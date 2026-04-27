"""P1 leverage cuantitativo full robusto — isolated cluster-específico.

Mitigaciones T1-T9 explícitas:
T1 cluster_id mapping via SIGNALS_RAW log parse.
T2 fees+funding escalan lineal con notional (matemáticamente correcta isolated).
T3 liquidación criterio worst-case observado |pnl_pct_real| × L >= 0.99.
T4 confounding portfolio_manager allocation = caveat documentado (no acción).
T5 liquidación trunca trade = pnl_final = -margin_assigned.
T6 §0.3 Fidelidad break = caveat operacional (informe).
T7 isolated margin operacional VERIFIED empírico VPS.
T8 selection bias top clusters N>=3 + caveat.
T9 segmentación arquitectural §12 L25: principal N=76 limpio + sanity N=215 segmentado.
"""
from __future__ import annotations
import csv, gzip, json, math, re
from collections import defaultdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent
COMBOLAB = ROOT.parent.parent
LOGS_DIR = ROOT / "logs_vps"

CSV_PATH = COMBOLAB / "trade_history.csv"  # synced via scp
REGIME_WF = COMBOLAB / "regime_wf"

# Boundaries arquitecturales §12 L25
V245_DEPLOY = "2026-04-22 09:46:17"
V244_DEPLOY = "2026-04-22 00:00:00"  # approx, conservative
V2311_DEPLOY = "2026-04-19 00:00:00"  # day boundary

COMMISSION_RATE = 0.001  # round-trip 0.10% canonical §11 (T2)
LIQUIDATION_THRESHOLD = 0.99  # 99% margin loss isolated (T3)
TARGET_MAX_DD_PCT = 25.0  # 25% (compute_leverage_map default, sin bug *100.0)
# Sanity alternativo: TARGET_MAX_DD_PCT = 5.0 (conservador safety) → colapsa 1x

CAPITAL_LEVELS = [296.0, 500.0, 1000.0]
CAP_LEVELS = ["1x", "3x", "5x", "unr"]


# ==============================================================
# T1 — Cluster_id mapping via SIGNALS_RAW logs
# ==============================================================

SIGNALS_RAW_RE = re.compile(r"\[SIGNALS_RAW\]\s+(\{.+\})")
TIMESTAMP_LINE_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})")  # HH:MM:SS at start of line


def parse_logs_for_cluster_map(logs_dir: Path) -> dict[tuple[str, int], int]:
    """Build mapping (symbol, hour_floor_ms) -> cluster_id from SIGNALS_RAW.

    Heurística: el SIGNALS_RAW del cycle xx:59:50 procesa señales para barra
    cerrada en xx:00:00 (anterior). Trade abierto en hour H tiene cluster
    desde el SIGNALS_RAW del cycle de hour H-1 (procesando bar H-1 cerrado).
    Field `t` en JSON contiene candle_ts (bar timestamp).
    """
    mapping: dict[tuple[str, int], int] = {}

    files = sorted(logs_dir.glob("engine.log*"))
    for fpath in files:
        opener = gzip.open if fpath.suffix == ".gz" else open
        try:
            with opener(fpath, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = SIGNALS_RAW_RE.search(line)
                    if not m:
                        continue
                    try:
                        sigs = json.loads(m.group(1))
                    except json.JSONDecodeError:
                        continue
                    for sym, payload in sigs.items():
                        if not isinstance(payload, dict):
                            continue
                        k = payload.get("k")
                        t = payload.get("t")
                        if k is None or t is None:
                            continue
                        # `t` es bar candle_ts (segundos UTC). Trade abierto en
                        # bar siguiente hereda este cluster.
                        candle_ms = int(t) * 1000
                        next_bar_ms = candle_ms + 3600 * 1000
                        mapping[(sym, next_bar_ms)] = int(k)
        except Exception as e:
            print(f"  [WARN] parse {fpath.name}: {e}")
    return mapping


# ==============================================================
# JSON regime_wf — maxdd_worst per (symbol, cluster)
# ==============================================================

def load_maxdd_per_cluster(regime_wf: Path) -> dict[tuple[str, int], float]:
    """Per (symbol, cluster_id) -> maxdd_worst del top-1 specialist activo.

    JSON guarda maxdd_worst en porcentaje (e.g. 14.777 = 14.777%).
    """
    out: dict[tuple[str, int], float] = {}
    for jp in regime_wf.glob("*_specialist_configs.json"):
        try:
            data = json.loads(jp.read_text())
        except Exception:
            continue
        # Symbol key: "BTC/USDT" del JSON
        sym = data.get("symbol", "")
        clusters = data.get("clusters", {})
        for cid_str, cdata in clusters.items():
            try:
                cid = int(cid_str)
            except Exception:
                continue
            top_configs = cdata.get("top_configs", [])
            if not top_configs:
                # Try mean_reversion as fallback
                mr = cdata.get("mean_reversion") or {}
                maxdd = mr.get("maxdd_worst", 0.0)
                if maxdd > 0:
                    out[(sym, cid)] = float(maxdd)
                continue
            top1 = top_configs[0]
            maxdd = top1.get("maxdd_worst", 0.0)
            if maxdd > 0:
                out[(sym, cid)] = float(maxdd)
    return out


def compute_l_target(maxdd_worst_pct: float, cap_lev: float) -> float:
    """L_target = TARGET_MAX_DD / maxdd_worst, clamped [1, cap]."""
    if maxdd_worst_pct <= 0:
        return 1.0
    raw = TARGET_MAX_DD_PCT / maxdd_worst_pct
    return max(1.0, min(raw, cap_lev))


# ==============================================================
# Trade parsing + segmentation
# ==============================================================

def parse_trades(csv_path: Path) -> list[dict]:
    trades: list[dict] = []
    with open(csv_path, encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)  # header
        for row in r:
            if len(row) < 10:
                continue
            try:
                tr = {
                    "timestamp": row[0],
                    "symbol": row[1],
                    "side": row[2].lower(),
                    "entry_price": float(row[3]),
                    "exit_price": float(row[4]),
                    "size_usdt": float(row[5]) if row[5] else 0.0,
                    "pnl_pct": float(row[6]),
                    "pnl_usdt": float(row[7]),
                    "funding_paid": float(row[8]) if row[8] else 0.0,
                    "reason_exit": row[9],
                    "flag": row[10] if len(row) > 10 else "",
                    "entry_ms": int(row[11]) if len(row) > 11 and row[11] and row[11].strip() else 0,
                }
                trades.append(tr)
            except Exception:
                continue
    return trades


def segment_trades(trades: list[dict]) -> dict[str, list[dict]]:
    """T9 — segmentación arquitectural §12 L25."""
    out = {"pre_v244": [], "post_v244_pre_v245": [], "post_v245": [], "all": []}
    for t in trades:
        ts = t["timestamp"]
        out["all"].append(t)
        if ts >= V245_DEPLOY:
            out["post_v245"].append(t)
        elif ts >= V244_DEPLOY:
            out["post_v244_pre_v245"].append(t)
        else:
            out["pre_v244"].append(t)
    return out


def attach_cluster(trades: list[dict], cluster_map: dict[tuple[str, int], int]) -> tuple[int, int]:
    """T1 mitigation — match por (symbol, entry_hour_floor)."""
    matched, total = 0, 0
    for t in trades:
        total += 1
        if t["entry_ms"] <= 0:
            t["cluster_id"] = -1
            continue
        # Floor a hora exacta (entry_ms - entry_ms % 3600000)
        hour_ms = (t["entry_ms"] // (3600 * 1000)) * 3600 * 1000
        cid = cluster_map.get((t["symbol"], hour_ms))
        if cid is None:
            # Try +/- 1 hour fallback
            cid = cluster_map.get((t["symbol"], hour_ms - 3600 * 1000))
            if cid is None:
                cid = cluster_map.get((t["symbol"], hour_ms + 3600 * 1000))
        t["cluster_id"] = cid if cid is not None else -1
        if cid is not None:
            matched += 1
    return matched, total


# ==============================================================
# Simulation core
# ==============================================================

def simulate_scenario(
    trades: list[dict],
    capital: float,
    cap_lev_str: str,
    maxdd_per_cluster: dict[tuple[str, int], float],
) -> dict:
    """Simulate isolated leverage scenario.

    T2 fees+funding escalan lineal con notional -> pnl_neto = L × pnl_real.
    T3 liquidación: |pnl_pct_real| × L ≥ 0.99 -> pnl_final = -size_usdt (margin).
    """
    cap_num = {"1x": 1.0, "3x": 3.0, "5x": 5.0, "unr": 50.0}[cap_lev_str]

    pnl_running = 0.0
    pnl_per_trade: list[float] = []
    drawdown_peak = 0.0
    drawdown_running = 0.0
    n_liq = 0
    n_saturated = 0  # L_actual == cap

    for t in trades:
        sym = t["symbol"]
        cid = t.get("cluster_id", -1)
        size = t["size_usdt"]
        pnl_real = t["pnl_usdt"]
        pnl_pct_real = t["pnl_pct"] / 100.0  # CSV pct in % units -> fraction

        # L_target per (sym, cluster); fallback worst-case if cluster unknown
        if cid >= 0 and (sym, cid) in maxdd_per_cluster:
            maxdd = maxdd_per_cluster[(sym, cid)]
        else:
            # Fallback: avg maxdd across clusters of symbol
            sym_dds = [v for (s, _), v in maxdd_per_cluster.items() if s == sym]
            maxdd = sum(sym_dds) / len(sym_dds) if sym_dds else 5.0

        l_target = compute_l_target(maxdd, cap_num)
        l_actual = min(l_target, cap_num)
        if abs(l_actual - cap_num) < 0.05:
            n_saturated += 1

        # Liquidación check (T3 worst-case observed)
        liquidated = abs(pnl_pct_real) * l_actual >= LIQUIDATION_THRESHOLD
        if liquidated:
            pnl_final = -size  # full margin assigned lost
            n_liq += 1
        else:
            pnl_final = pnl_real * l_actual  # T2 lineal correcto

        pnl_running += pnl_final
        pnl_per_trade.append(pnl_final)

        # Track drawdown
        if pnl_running > drawdown_peak:
            drawdown_peak = pnl_running
        dd_now = drawdown_peak - pnl_running
        if dd_now > drawdown_running:
            drawdown_running = dd_now

    n = len(pnl_per_trade)
    mean_pnl = pnl_running / n if n else 0.0
    if n > 1:
        var = sum((x - mean_pnl) ** 2 for x in pnl_per_trade) / (n - 1)
        std = math.sqrt(var)
        sharpe = (mean_pnl / std) * math.sqrt(n) if std > 0 else 0.0
    else:
        std = 0.0
        sharpe = 0.0

    dd_pct_capital = (drawdown_running / capital) * 100.0 if capital else 0.0

    return {
        "capital": capital,
        "cap_lev": cap_lev_str,
        "n_trades": n,
        "pnl_total": pnl_running,
        "pnl_per_trade": mean_pnl,
        "n_liquidaciones": n_liq,
        "max_drawdown_usdt": drawdown_running,
        "max_drawdown_pct_capital": dd_pct_capital,
        "sharpe": sharpe,
        "n_saturated": n_saturated,
        "pct_saturated": (n_saturated / n * 100.0) if n else 0.0,
    }


# ==============================================================
# Cluster top/bottom analysis
# ==============================================================

def cluster_performance(trades: list[dict]) -> list[dict]:
    by_cluster: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for t in trades:
        cid = t.get("cluster_id", -1)
        if cid < 0:
            continue
        by_cluster[(t["symbol"], cid)].append(t)
    rows = []
    for (sym, cid), trs in by_cluster.items():
        n = len(trs)
        if n < 3:
            continue
        pnl_sum = sum(x["pnl_usdt"] for x in trs)
        pnl_avg = pnl_sum / n
        wins = sum(1 for x in trs if x["pnl_usdt"] > 0)
        wr = wins / n * 100
        rows.append({
            "symbol": sym, "cluster": cid, "n": n,
            "pnl_total": pnl_sum, "pnl_per_trade": pnl_avg,
            "win_rate": wr,
        })
    rows.sort(key=lambda r: r["pnl_per_trade"], reverse=True)
    return rows


# ==============================================================
# Main
# ==============================================================

def main() -> None:
    print("=" * 72)
    print("P1 LEVERAGE — Análisis cuantitativo isolated cluster-específico")
    print("=" * 72)

    print(f"\n[1] Parsing logs from {LOGS_DIR}...")
    cluster_map = parse_logs_for_cluster_map(LOGS_DIR)
    print(f"  Total (symbol, hour_ms) -> cluster mappings: {len(cluster_map)}")

    print(f"\n[2] Loading regime_wf JSONs from {REGIME_WF}...")
    maxdd_map = load_maxdd_per_cluster(REGIME_WF)
    print(f"  Total (symbol, cluster) -> maxdd_worst entries: {len(maxdd_map)}")
    if maxdd_map:
        vals = sorted(maxdd_map.values())
        n = len(vals)
        print(f"  maxdd_worst distribution: min={vals[0]:.3f}% p25={vals[n//4]:.3f}% p50={vals[n//2]:.3f}% p75={vals[3*n//4]:.3f}% max={vals[-1]:.3f}%")

    print(f"\n[3] Loading trades from {CSV_PATH}...")
    trades_all = parse_trades(CSV_PATH)
    print(f"  Total trades parsed: {len(trades_all)}")

    segs = segment_trades(trades_all)
    for k, v in segs.items():
        print(f"  Segment {k}: N={len(v)}")

    # Filter: valid (size_usdt > 0 + entry_ms valid + not orphan_close)
    def is_valid(t):
        if t["size_usdt"] <= 0:
            return False
        if t["reason_exit"] in ("orphan_close",):
            return False
        return True

    print(f"\n[4] Attaching cluster_id (T1 mitigation)...")
    for k in ["all", "post_v245", "post_v244_pre_v245", "pre_v244"]:
        m, tot = attach_cluster(segs[k], cluster_map)
        print(f"  Segment {k}: matched cluster_id {m}/{tot} ({m/tot*100:.1f}%)" if tot else f"  Segment {k}: empty")

    # Apply validity filter
    clean = [t for t in segs["post_v245"] if is_valid(t) and t["entry_ms"] > 0]
    print(f"\n  Clean post-v2.4.5 (size>0 + entry_ms>0 + not orphan): N={len(clean)}")

    full_clean = [t for t in segs["all"] if is_valid(t)]
    pre244_clean = [t for t in segs["pre_v244"] if is_valid(t)]
    post244_clean = [t for t in segs["post_v244_pre_v245"] if is_valid(t)]

    print(f"  Clean pre-v2.4.4 (size>0 + not orphan): N={len(pre244_clean)} (caveat size_usdt may be 0 in raw)")
    print(f"  Clean post-v2.4.4 pre-v2.4.5: N={len(post244_clean)}")
    print(f"  Clean all: N={len(full_clean)}")

    # ============================================================
    # 12 escenarios principal sobre N=76 clean
    # ============================================================
    print("\n" + "=" * 72)
    print("[5] 12 ESCENARIOS — N=76 limpio post-v2.4.5 (análisis principal)")
    print("=" * 72)
    print(f"\n{'Cap':<6}{'Capital':<10}{'PnL_total':<14}{'PnL/trade':<14}"
          f"{'N_liq':<8}{'MaxDD_USD':<12}{'MaxDD%cap':<12}{'Sharpe':<10}{'%saturated':<12}")
    print("-" * 100)

    results_principal = []
    for cap_lev in CAP_LEVELS:
        for capital in CAPITAL_LEVELS:
            r = simulate_scenario(clean, capital, cap_lev, maxdd_map)
            results_principal.append(r)
            print(f"{cap_lev:<6}{capital:<10.0f}{r['pnl_total']:<14.4f}{r['pnl_per_trade']:<14.4f}"
                  f"{r['n_liquidaciones']:<8}{r['max_drawdown_usdt']:<12.4f}{r['max_drawdown_pct_capital']:<12.2f}"
                  f"{r['sharpe']:<10.3f}{r['pct_saturated']:<12.1f}")

    # ============================================================
    # Sanity cross-segment T9 (capital 296, cap 3x)
    # ============================================================
    print("\n" + "=" * 72)
    print("[6] T9 SANITY — Cross-segmento capital 296 cap 3x")
    print("=" * 72)
    print(f"\n{'Segment':<28}{'N':<6}{'PnL_total':<14}{'PnL/trade':<14}{'N_liq':<8}{'MaxDD_USD':<12}")
    print("-" * 90)
    for label, segdata in [
        ("pre_v2.4.4 (contaminado)", pre244_clean),
        ("post_v2.4.4 pre_v2.4.5", post244_clean),
        ("post_v2.4.5 (limpio)", clean),
    ]:
        if not segdata:
            continue
        r = simulate_scenario(segdata, 296.0, "3x", maxdd_map)
        print(f"{label:<28}{r['n_trades']:<6}{r['pnl_total']:<14.4f}{r['pnl_per_trade']:<14.4f}"
              f"{r['n_liquidaciones']:<8}{r['max_drawdown_usdt']:<12.4f}")

    # ============================================================
    # Cluster top/bottom (N=76 clean)
    # ============================================================
    print("\n" + "=" * 72)
    print("[7] CLUSTER TOP/BOTTOM 10 — N=76 limpio (T8 caveat selection bias)")
    print("=" * 72)
    cperf = cluster_performance(clean)
    print(f"\nClusters with N>=3 trades: {len(cperf)}")
    print(f"\n--- TOP 10 by PnL/trade ---")
    print(f"{'Symbol':<14}{'Cluster':<8}{'N':<5}{'PnL_total':<12}{'PnL/trade':<12}{'WinRate%':<10}{'maxdd%':<10}{'L_target_unr':<14}")
    print("-" * 100)
    for r in cperf[:10]:
        sym, cid = r["symbol"], r["cluster"]
        maxdd = maxdd_map.get((sym, cid), 0.0)
        l_target = compute_l_target(maxdd, 50.0) if maxdd > 0 else 1.0
        print(f"{sym:<14}{cid:<8}{r['n']:<5}{r['pnl_total']:<12.4f}{r['pnl_per_trade']:<12.4f}"
              f"{r['win_rate']:<10.1f}{maxdd:<10.3f}{l_target:<14.2f}")

    print(f"\n--- BOTTOM 10 by PnL/trade ---")
    print(f"{'Symbol':<14}{'Cluster':<8}{'N':<5}{'PnL_total':<12}{'PnL/trade':<12}{'WinRate%':<10}{'maxdd%':<10}{'L_target_unr':<14}")
    print("-" * 100)
    for r in cperf[-10:]:
        sym, cid = r["symbol"], r["cluster"]
        maxdd = maxdd_map.get((sym, cid), 0.0)
        l_target = compute_l_target(maxdd, 50.0) if maxdd > 0 else 1.0
        print(f"{sym:<14}{cid:<8}{r['n']:<5}{r['pnl_total']:<12.4f}{r['pnl_per_trade']:<12.4f}"
              f"{r['win_rate']:<10.1f}{maxdd:<10.3f}{l_target:<14.2f}")

    # Selectivo: aplicar leverage 3x ONLY top-10 clusters, 1x resto
    print(f"\n--- LEVERAGE SELECTIVO TOP-10 (cap 3x top, 1x resto) ---")
    top_keys = {(r["symbol"], r["cluster"]) for r in cperf[:10]}
    pnl_selective = 0.0
    n_liq_sel = 0
    n_top_trades = 0
    for t in clean:
        sym, cid = t["symbol"], t.get("cluster_id", -1)
        if (sym, cid) in top_keys:
            n_top_trades += 1
            maxdd = maxdd_map.get((sym, cid), 5.0)
            l_actual = min(compute_l_target(maxdd, 3.0), 3.0)
            if abs(t["pnl_pct"] / 100.0) * l_actual >= LIQUIDATION_THRESHOLD:
                pnl_selective += -t["size_usdt"]
                n_liq_sel += 1
            else:
                pnl_selective += t["pnl_usdt"] * l_actual
        else:
            pnl_selective += t["pnl_usdt"]  # 1x for non-top
    print(f"  N_top trades: {n_top_trades}/{len(clean)}")
    print(f"  PnL selectivo: {pnl_selective:.4f} USDT")
    print(f"  Liquidaciones: {n_liq_sel}")
    print(f"  Baseline 1x universal: {sum(t['pnl_usdt'] for t in clean):.4f} USDT")

    # Save CSV
    out_csv = ROOT / "scenario_results.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cap_lev", "capital", "n_trades", "pnl_total", "pnl_per_trade",
                    "n_liquidaciones", "max_drawdown_usdt", "max_drawdown_pct_capital",
                    "sharpe", "pct_saturated"])
        for r in results_principal:
            w.writerow([r["cap_lev"], r["capital"], r["n_trades"], r["pnl_total"],
                        r["pnl_per_trade"], r["n_liquidaciones"], r["max_drawdown_usdt"],
                        r["max_drawdown_pct_capital"], r["sharpe"], r["pct_saturated"]])
    print(f"\n[8] Output -> {out_csv}")

    out_cluster_csv = ROOT / "cluster_performance.csv"
    with open(out_cluster_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "cluster", "n", "pnl_total", "pnl_per_trade", "win_rate", "maxdd_worst", "L_target_unr"])
        for r in cperf:
            sym, cid = r["symbol"], r["cluster"]
            maxdd = maxdd_map.get((sym, cid), 0.0)
            l_target = compute_l_target(maxdd, 50.0) if maxdd > 0 else 1.0
            w.writerow([sym, cid, r["n"], r["pnl_total"], r["pnl_per_trade"],
                        r["win_rate"], maxdd, l_target])
    print(f"  Cluster perf -> {out_cluster_csv}")


if __name__ == "__main__":
    main()
