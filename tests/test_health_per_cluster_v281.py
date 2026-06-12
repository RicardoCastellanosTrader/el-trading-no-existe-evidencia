"""Tests greenfield v2.8.1 — health report per-par (símbolo, cluster) + registro
de cluster en trades + backfill desde logs.

Cubre (decisión Ricardo):
  (i)   apertura en cluster k → log_trade lo registra en la columna CSV.
  (ii)  cierre ORPHAN_CLOSE conserva el cluster de apertura (enrich + log_trade).
  (iii) evaluación per-par con trades multi-cluster → PF por par + gates N correctos.
  (iv)  REGRESIÓN del agravante: cluster actual ≠ clusters de los trades →
        status sale de la comparación per-par, NUNCA de mezcla vs baseline actual.
  (v)   render con 0 / 1 / varios degradados (exception-based, escalable).
  (vi)  matcher de backfill (timestamp+símbolo → k; intra-barra → registro ≤ entrada).
"""
import csv
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live import execution_manager as em
from live import health_monitor as hm
from live.live_engine import _enrich_positions_with_entry_ms
import analysis_scripts.backfill_trade_clusters as bf


# ───────────────────────── (i) log_trade escribe cluster ─────────────────────────
def test_i_log_trade_writes_cluster_column(tmp_path):
    p = tmp_path / "trade_history.csv"
    em.log_trade({"symbol": "BTC/USDT", "side": "long", "entry_price": 100.0,
                  "exit_price": 105.0, "size_usdt": 10.0, "pnl_usdt": 0.5,
                  "reason_exit": "tf_exit", "entry_timestamp_ms": 1781000000000,
                  "cluster": 2}, filepath=p)
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert rows[0]["cluster"] == "2"
    # columna es la última (13ª)
    assert list(rows[0].keys())[-1] == "cluster"


def test_i_log_trade_cluster_empty_when_absent(tmp_path):
    p = tmp_path / "trade_history.csv"
    em.log_trade({"symbol": "ETH/USDT", "side": "short", "entry_price": 50.0,
                  "exit_price": 49.0, "size_usdt": 10.0, "pnl_usdt": 0.2,
                  "reason_exit": "sl_hit"}, filepath=p)  # sin cluster
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert rows[0]["cluster"] == ""  # NULL, no crashea


def test_i_log_trade_cluster_none_becomes_empty(tmp_path):
    p = tmp_path / "trade_history.csv"
    em.log_trade({"symbol": "ETH/USDT", "side": "long", "entry_price": 50.0,
                  "exit_price": 51.0, "size_usdt": 10.0, "pnl_usdt": 0.2,
                  "reason_exit": "tf_exit", "cluster": None}, filepath=p)
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert rows[0]["cluster"] == ""


# ───────────────────────── (ii) ORPHAN_CLOSE conserva cluster ─────────────────────
def test_ii_enrich_positions_carries_open_cluster():
    positions = {"BTC/USDT": {"side": "long", "entry_price": 100.0}}
    pre = {"BTC/USDT": {"entry_timestamp_ms": 1781000000000, "open_cluster": 1}}
    _enrich_positions_with_entry_ms(positions, pre)
    assert positions["BTC/USDT"]["cluster"] == 1
    assert positions["BTC/USDT"]["entry_timestamp_ms"] == 1781000000000


def test_ii_orphan_close_trade_dict_writes_pre_cluster(tmp_path):
    # Simula el trade dict que construye el path ORPHAN_CLOSE: cluster = pre.open_cluster
    p = tmp_path / "trade_history.csv"
    pre = {"open_cluster": 0, "entry_timestamp_ms": 1781000000000}
    em.log_trade({"symbol": "SOL/USDT", "side": "long", "entry_price": 1.0,
                  "exit_price": 0.95, "size_usdt": 10.0, "pnl_usdt": -0.5,
                  "reason_exit": "sl_trigger_exchange_side",
                  "flag": "exchange_side_close",
                  "entry_timestamp_ms": pre["entry_timestamp_ms"],
                  "cluster": pre.get("open_cluster")}, filepath=p)
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert rows[0]["cluster"] == "0"  # cluster 0 preservado (no vacío)
    assert rows[0]["flag"] == "exchange_side_close"


def test_ii_enrich_no_cluster_when_pre_none():
    positions = {"X/USDT": {"side": "long"}}
    pre = {"X/USDT": {"entry_timestamp_ms": 123, "open_cluster": None}}
    _enrich_positions_with_entry_ms(positions, pre)
    assert "cluster" not in positions["X/USDT"]  # None → no se enriquece → NULL


# ───────────────────────── helpers para health tests ─────────────────────────
def _write_history(path: Path, rows):
    """rows = list de dicts; escribe CSV 13-col con header."""
    cols = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
            'size_usdt', 'pnl_pct', 'pnl_usdt', 'funding_paid',
            'reason_exit', 'flag', 'entry_timestamp_ms', 'cluster']
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            full = {c: r.get(c, "") for c in cols}
            w.writerow(full)


def _specialist_json(path: Path, symbol, pf_by_cluster):
    import json
    clusters = {str(k): {"name": f"c{k}", "n_validated": 50,
                         "top_configs": [{"config_id": 1, "pf_combined": pf}]}
                for k, pf in pf_by_cluster.items()}
    path.write_text(json.dumps({"symbol": symbol, "n_clusters": len(pf_by_cluster),
                                "clusters": clusters}), encoding="utf-8")


def _mk_trades(symbol, cluster, n, pnl, ts0=1781000000000):
    out = []
    for i in range(n):
        out.append({"timestamp": "2026-06-10 12:00:00.000", "symbol": symbol,
                    "side": "long", "entry_price": "100", "exit_price": "101",
                    "size_usdt": "10", "pnl_pct": "1.0", "pnl_usdt": str(pnl),
                    "funding_paid": "0", "reason_exit": "tf_exit", "flag": "",
                    "entry_timestamp_ms": str(ts0 + i), "cluster": str(cluster)})
    return out


def _cfg(tmp_path):
    return hm.HealthConfig(
        trade_log_path=str(tmp_path / "trade_history.csv"),
        specialist_configs_dir=str(tmp_path / "regime_wf"),
        last_recycle_file=str(tmp_path / "nope.txt"),
        engine_state_path=str(tmp_path / "nostate.json"),
    )


# ───────────────────────── (iii) per-par PF + gates N ─────────────────────────
def test_iii_per_pair_pf_and_n_gates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "regime_wf").mkdir()
    _specialist_json(tmp_path / "regime_wf" / "BTCUSDT_specialist_configs.json",
                     "BTC/USDT", {0: 3.0, 1: 3.0, 2: 3.0})
    # C0: 20 trades sanos (PF alto); C1: 20 trades perdedores (PF bajo); C2: 5 trades (insuf)
    rows = (_mk_trades("BTC/USDT", 0, 20, +1.0)
            + _mk_trades("BTC/USDT", 1, 18, -1.0)  # net loss → PF bajo
            + _mk_trades("BTC/USDT", 2, 5, +1.0))
    # C1 necesita mezcla de wins/losses para PF>0 finito; ponemos 6 win 12 loss
    rows_c1 = _mk_trades("BTC/USDT", 1, 6, +1.0) + _mk_trades("BTC/USDT", 1, 12, -1.0)
    rows = _mk_trades("BTC/USDT", 0, 20, +1.0) + rows_c1 + _mk_trades("BTC/USDT", 2, 5, +1.0)
    _write_history(tmp_path / "trade_history.csv", rows)

    rep = hm.evaluate_health(_cfg(tmp_path))
    pairs = {(p.symbol, p.cluster): p for p in rep.pairs}
    assert pairs[("BTC/USDT", 0)].status == "HEALTHY"
    assert pairs[("BTC/USDT", 0)].trades_real == 20
    # C1: PF = 6/12 = 0.5, ratio 0.5/3 = 0.17 → CRITICAL
    assert pairs[("BTC/USDT", 1)].status == "CRITICAL"
    # C2: 5 < 15 → INSUFFICIENT
    assert pairs[("BTC/USDT", 2)].status == "INSUFFICIENT_DATA"
    assert pairs[("BTC/USDT", 2)].trades_real == 5


# ───────────────────────── (iv) REGRESIÓN del agravante ─────────────────────────
def test_iv_status_from_per_pair_not_current_cluster_mix(tmp_path, monkeypatch):
    """Trades en C0 (sanos) y C1 (degradado); cluster ACTUAL del símbolo = C2.
    La lógica vieja comparaba pf_real(mezcla C0+C1) vs pf_expected(C2) → inválido.
    La nueva: cada par vs su propio esperado; C2 actual NO contamina la atribución."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "regime_wf").mkdir()
    _specialist_json(tmp_path / "regime_wf" / "ETHUSDT_specialist_configs.json",
                     "ETH/USDT", {0: 3.0, 1: 3.0, 2: 3.0})
    # engine_state dice cluster actual = 2 (sin trades en C2)
    import json
    (tmp_path / "engine_state.json").write_text(json.dumps(
        {"symbols": {"ETHUSDT": {"current_cluster": 2}}}))
    cfg = hm.HealthConfig(
        trade_log_path=str(tmp_path / "trade_history.csv"),
        specialist_configs_dir=str(tmp_path / "regime_wf"),
        last_recycle_file=str(tmp_path / "nope.txt"),
        engine_state_path=str(tmp_path / "engine_state.json"),
    )
    rows = (_mk_trades("ETH/USDT", 0, 20, +1.0)
            + _mk_trades("ETH/USDT", 1, 6, +1.0) + _mk_trades("ETH/USDT", 1, 14, -1.0))
    _write_history(tmp_path / "trade_history.csv", rows)

    rep = hm.evaluate_health(cfg)
    pairs = {(p.symbol, p.cluster): p for p in rep.pairs}
    # C0 sano evaluado por su propio esperado (no mezclado con C1)
    assert pairs[("ETH/USDT", 0)].status == "HEALTHY"
    # C1 degradado detectado per-par (no diluido por C0)
    assert pairs[("ETH/USDT", 1)].status == "CRITICAL"
    # NO existe par C2 (sin trades) — el cluster actual no inventa un par
    assert ("ETH/USDT", 2) not in pairs
    # current_cluster registrado como CONTEXTO, distinto de la atribución
    assert pairs[("ETH/USDT", 0)].current_cluster == 2
    assert pairs[("ETH/USDT", 0)].cluster == 0
    # símbolo flagged (algún par degradado)
    assert "ETH/USDT" in rep.flagged_symbols()


def test_iv_dilution_would_have_hidden_it(tmp_path, monkeypatch):
    """Prueba positiva de la dilución: el agregado símbolo (C0+C1 mezclado) sería
    HEALTHY, escondiendo el C1 degradado que la nueva lógica SÍ caza."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "regime_wf").mkdir()
    _specialist_json(tmp_path / "regime_wf" / "ADAUSDT_specialist_configs.json",
                     "ADA/USDT", {0: 3.0, 1: 3.0})
    cfg = _cfg(tmp_path)
    # C0: 30 wins (PF 99); C1: 5 win 15 loss (PF 0.33). Mezcla: 35 win 15 loss → PF alto.
    rows = (_mk_trades("ADA/USDT", 0, 30, +1.0)
            + _mk_trades("ADA/USDT", 1, 5, +1.0) + _mk_trades("ADA/USDT", 1, 15, -1.0))
    _write_history(tmp_path / "trade_history.csv", rows)
    rep = hm.evaluate_health(cfg)
    pairs = {(p.symbol, p.cluster): p for p in rep.pairs}
    # mezcla daría PF≈ (35)/(15)=2.33 ratio 0.78 → HEALTHY (escondería C1)
    # per-par: C1 PF=5/15=0.33 ratio 0.11 → CRITICAL detectado
    assert pairs[("ADA/USDT", 1)].status == "CRITICAL"
    assert pairs[("ADA/USDT", 0)].status == "HEALTHY"


# ───────────────────────── (v) render exception-based ─────────────────────────
def test_v_render_zero_degraded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "regime_wf").mkdir()
    _specialist_json(tmp_path / "regime_wf" / "BTCUSDT_specialist_configs.json",
                     "BTC/USDT", {0: 3.0})
    _write_history(tmp_path / "trade_history.csv", _mk_trades("BTC/USDT", 0, 20, +1.0))
    out = hm.generate_daily_health_summary(_cfg(tmp_path))
    assert "1 healthy" in out
    assert "CRITICAL" not in out  # sin degradados, no detalle
    assert "No recycle needed" in out


def test_v_render_multiple_degraded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "regime_wf").mkdir()
    for s in ("BTC", "ETH", "SOL"):
        _specialist_json(tmp_path / "regime_wf" / f"{s}USDT_specialist_configs.json",
                         f"{s}/USDT", {0: 3.0})
    rows = []
    for s in ("BTC", "ETH", "SOL"):
        rows += _mk_trades(f"{s}/USDT", 0, 6, +1.0) + _mk_trades(f"{s}/USDT", 0, 14, -1.0)
    _write_history(tmp_path / "trade_history.csv", rows)
    rep = hm.evaluate_health(_cfg(tmp_path))
    out = hm.generate_daily_health_summary(_cfg(tmp_path))
    # 3 símbolos con par degradado → recycle recomendado
    assert len(rep.flagged_symbols()) == 3
    assert "RECYCLE RECOMENDADO" in out
    assert "CRITICAL" in out


def test_v_render_unlabeled_note(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "regime_wf").mkdir()
    _specialist_json(tmp_path / "regime_wf" / "BTCUSDT_specialist_configs.json",
                     "BTC/USDT", {0: 3.0})
    rows = _mk_trades("BTC/USDT", 0, 16, +1.0)
    rows += [{**r, "cluster": ""} for r in _mk_trades("BTC/USDT", 0, 4, +1.0)]  # 4 NULL
    _write_history(tmp_path / "trade_history.csv", rows)
    out = hm.generate_daily_health_summary(_cfg(tmp_path))
    assert "4 trades sin cluster" in out


# ───────────────────────── (vi) matcher de backfill ─────────────────────────
def test_vi_match_cluster_basic():
    index = {"BTC/USDT": [(1000_000, 0), (1003600_000, 1), (1007200_000, 2)]}
    # entrada justo después de la barra t=1003600 → k=1
    assert bf.match_cluster(index, "BTC/USDT", 1003600_500) == 1


def test_vi_match_cluster_intrabar_takes_preceding():
    # Dos barras horarias ADYACENTES: bar0 t=1_000_000s (k=0), bar1 +3600s (k=1).
    bar0_ms = 1_000_000 * 1000
    bar1_ms = (1_000_000 + 3600) * 1000
    index = {"BTC/USDT": [(bar0_ms, 0), (bar1_ms, 1)]}
    # entrada 0.5s tras el cierre de bar0 (dentro de la hora, antes de bar1) → k=0
    assert bf.match_cluster(index, "BTC/USDT", bar0_ms + 500) == 0
    # entrada 0.5s tras bar1 → k=1
    assert bf.match_cluster(index, "BTC/USDT", bar1_ms + 500) == 1


def test_vi_match_cluster_no_record_before():
    index = {"BTC/USDT": [(1007200_000, 2)]}
    # entrada anterior a todo registro → None
    assert bf.match_cluster(index, "BTC/USDT", 1000_000) is None


def test_vi_match_cluster_gap_exceeds_tolerance():
    index = {"BTC/USDT": [(1000_000, 0)]}
    # entrada >2h después del único registro → None (hueco de log)
    assert bf.match_cluster(index, "BTC/USDT", 1000_000 + 3 * 3600 * 1000) is None


def test_vi_match_cluster_unknown_symbol():
    index = {"BTC/USDT": [(1000_000, 0)]}
    assert bf.match_cluster(index, "ETH/USDT", 1000_500) is None


def test_vi_parse_signals_raw_line():
    line = ('11:00 live.live_engine [SIGNALS_RAW] '
            '{"XRP/USDT":{"a":"LONG","k":0,"cfg":57424768,"t":1781258400}}')
    payload = bf.parse_signals_raw_line(line)
    assert payload["XRP/USDT"]["k"] == 0
    assert payload["XRP/USDT"]["t"] == 1781258400


def test_vi_build_index_and_match_end_to_end(tmp_path):
    log = tmp_path / "engine.log"
    log.write_text(
        '10:00 [SIGNALS_RAW] {"BTC/USDT":{"a":"LONG","k":1,"t":1000}}\n'
        '11:00 [SIGNALS_RAW] {"BTC/USDT":{"a":"FLAT","k":2,"t":4600}}\n',
        encoding="utf-8")
    idx = bf.build_signal_index([str(log)])
    assert idx["BTC/USDT"] == [(1000_000, 1), (4600_000, 2)]
    # entrada tras t=4600 → k=2
    assert bf.match_cluster(idx, "BTC/USDT", 4600_500) == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
