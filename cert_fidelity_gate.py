"""cert_fidelity_gate.py — Gate de certificación de fidelidad brain<->kernel REMEDIADO (2026-05-30).

Reemplaza el uso directo de live.brain_engine._run_verify_test como gate de certificación,
corrigiendo los 3 hallazgos de instrumento de la Capa 1. NO modifica productivo: importa
y llama _evaluate_bar / run_on_slice sin tocarlos.

  B1.1 Multi-símbolo (CERT_SET ejercita TODAS las clases de MA, incl. adaptativas de período
       largo VIDYA/KAMA/FRAMA/McGinley/T3 en slow/trend, no solo BTC drift-free).
  B1.2 Ventana OPERACIONAL WINDOW=1500 (OHLCV_LIMIT del bot), NO 500 (=diagnóstico warmup).
  B1.3 Métrica PRIMARIA (Fidelidad 1): entry-bar match-rate alineando entry_bar del kernel
       (relativo a actual_start = start_bar - kernel_warmup) al índice absoluto del brain.
       Independiente del modelo de ejecución. Fidelidad 2 (exits on-close vs intrabar) = por
       diseño §13.4 v2.4.0, NO objeto de esta certificación.

Criterio: entry-bar match-rate >= 98% a WINDOW=1500 cross-sym (drift residual ranking-invariante
§12.30 aceptable; TRX VIDYA-276 = 97.06% drift benigno). Lógica validada en Capa 1 2026-05-30
(offset-400 del kernel cazado + corregido).
Uso: python cert_fidelity_gate.py [--window 1500] [--n 8000] [--symbols BTC/USDT,...]
"""
from __future__ import annotations
import argparse, re, os, json
import numpy as np, pandas as pd
from live.brain_engine import (_evaluate_bar, load_models, decode_config_bits,
                               SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT,
                               COOLDOWN_BARS, COMMISSION_ROUND_TRIP, _project_root,
                               _normalize_ohlcv, _load_preset_tuple)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice

KERNEL_WARMUP = 100
CERT_THRESHOLD = 98.0
TOL = 1
DEFAULT_CERT_SET = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SEI/USDT", "POL/USDT",
                    "ONDO/USDT", "TRX/USDT", "XRP/USDT", "RENDER/USDT"]


def _setup(symbol):
    brain = load_models(regime_models_dir=os.path.join(_project_root, "regime_models"),
                        specialist_configs_dir=os.path.join(_project_root, "regime_wf"),
                        symbols=[symbol])
    cfg_data = brain.specialist_configs.get(symbol)
    tc = next(int(k) for k, c in cfg_data["clusters"].items() if c.get("top_configs"))
    top = cfg_data["clusters"][str(tc)]["top_configs"][0]
    cid, plabel = top["config_id"], top["preset"]
    ptuple = brain.preset_tuples.get(plabel) or _load_preset_tuple(symbol, plabel)[0]
    hm = re.search(r"_H(\d+)$", plabel)
    hyst = int(hm.group(1)) / 10.0 if hm else 0.0
    return brain, cfg_data, tc, cid, plabel, ptuple, hyst


def _brain_entries(symbol, df_test, W, brain, cfg_data, tc, cid, plabel, ptuple):
    bits = decode_config_bits(cid)
    st = brain.get_state(symbol)
    st.current_cluster = tc
    st.cluster_probs = np.ones(cfg_data["n_clusters"]) / cfg_data["n_clusters"]
    st.cluster_probs[tc] = 0.9
    out = []
    for i in range(W, len(df_test)):
        window = df_test.iloc[max(0, i - W + 1):i + 1].reset_index(drop=True)
        cfg = {"config_id": cid, "preset": plabel, "preset_tuple": ptuple, "config_bits": bits,
               "cluster": tc, "operable": True, "regime_changed": False}
        try:
            sig = _evaluate_bar(brain, symbol, window, cfg)
            if sig["action"] == "LONG":
                out.append((i, 1))
            elif sig["action"] == "SHORT":
                out.append((i, -1))
        except Exception:
            pass
    return out


def _kernel_entries(df_test, ptuple, hyst, symbol, cid, W):
    data = precalculate_all_data(df_test, preset=ptuple, hyst_mult=hyst, symbol=symbol)
    configs = np.array([cid], dtype=np.uint32)
    _agg, pt = run_on_slice(configs, data, start_bar=W, end_bar=len(df_test),
                            sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT,
                            ts_pct=TS_PERCENT, cooldown_bars=COOLDOWN_BARS,
                            commission_pct=COMMISSION_ROUND_TRIP, warmup=KERNEL_WARMUP,
                            return_per_trade=True)
    cnt = int(pt["count"][0])
    eb_abs = pt["entry_bar"][0, :cnt].astype(int) + (W - KERNEL_WARMUP)  # B1.3 a absoluto
    side = pt["side"][0, :cnt].astype(int) if "side" in pt else np.zeros(cnt, int)
    return list(zip(eb_abs.tolist(), side.tolist()))


def _match_rate(brain_e, kern_e, tol=TOL):
    kb = sorted(kern_e); used = [False] * len(kb); matched = 0
    for (b, _s) in sorted(brain_e):
        for j, (kbar, _ks) in enumerate(kb):
            if not used[j] and abs(kbar - b) <= tol:
                used[j] = True; matched += 1; break
    return matched, len(brain_e), len(kern_e), matched / max(len(brain_e), len(kern_e), 1) * 100


def run_gate(symbols, window, n):
    rows = []
    for sym in symbols:
        sc = sym.replace("/", "").replace("USDT", "")
        df = _normalize_ohlcv(pd.read_parquet(os.path.join(_project_root, "data_cache", f"{sc}USDT_1h.parquet")))
        df_test = df.tail(n).reset_index(drop=True)
        brain, cfg_data, tc, cid, plabel, ptuple, hyst = _setup(sym)
        be = _brain_entries(sym, df_test, window, brain, cfg_data, tc, cid, plabel, ptuple)
        ke = _kernel_entries(df_test, ptuple, hyst, sym, cid, window)
        m, nb, nk, rate = _match_rate(be, ke)
        cert = rate >= CERT_THRESHOLD
        rows.append({"sym": sym, "match_rate": round(rate, 2), "matched": m,
                     "n_brain": nb, "n_kernel": nk, "certified": cert})
        print(f"{sym:12} entry-match={rate:6.2f}%  ({'CERT' if cert else 'BELOW'})  "
              f"matched {m}/max({nb},{nk})  [Fidelidad 1]", flush=True)
    n_cert = sum(r["certified"] for r in rows)
    print(f"\n=> Fidelidad 1 @ W={window}: {n_cert}/{len(rows)} sym >= {CERT_THRESHOLD}%")
    print("   (Fidelidad 2 exits on-close vs intrabar = por diseño §13.4 v2.4.0, NO certificada aquí)")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=1500, help="1500=cert operacional, 500=diagnóstico")
    ap.add_argument("--n", type=int, default=8000)
    ap.add_argument("--symbols", type=str, default=None)
    a = ap.parse_args()
    syms = a.symbols.split(",") if a.symbols else DEFAULT_CERT_SET
    res = run_gate(syms, a.window, a.n)
    json.dump(res, open(f"cert_fidelity_gate_W{a.window}.json", "w"), indent=2)
    print(f"Saved cert_fidelity_gate_W{a.window}.json")
