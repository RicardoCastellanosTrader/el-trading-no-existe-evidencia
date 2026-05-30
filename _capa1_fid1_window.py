"""CAPA 1 PARTE A+B — Fidelidad 1 (indicadores) por entry-bar match-rate, a 500 vs 1500
window (live). READ-ONLY sobre productivo: importa _evaluate_bar/run_on_slice sin tocarlos.
Métrica PRIMARIA = entry-bar match-rate (alineado por barra REAL, no pairing secuencial)
→ robusta, independiente del modelo de ejecución (exits on-close vs intrabar = Fidelidad 2,
NO se mide aquí). Falsa la predicción window-sensitivity: ¿los FAILs de 500 recuperan a 1500?
"""
import io, re, json
from contextlib import redirect_stdout
import numpy as np, pandas as pd, os
from live.brain_engine import (_evaluate_bar, load_models, decode_config_bits,
                               SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT,
                               COOLDOWN_BARS, COMMISSION_ROUND_TRIP, _project_root,
                               _normalize_ohlcv, _load_preset_tuple)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice

SYMS = ["ETH/USDT", "ONDO/USDT", "TRX/USDT", "XRP/USDT"]  # los 4 FAILs Nivel B
WINDOWS = [500, 1500]
N = 4000
TOL = 1  # ±1 bar tolerancia de timing on-close

def setup(symbol):
    brain = load_models(regime_models_dir=os.path.join(_project_root, "regime_models"),
                        specialist_configs_dir=os.path.join(_project_root, "regime_wf"),
                        symbols=[symbol])
    cfg_data = brain.specialist_configs.get(symbol)
    test_cluster = next(int(k) for k, c in cfg_data["clusters"].items() if c.get("top_configs"))
    top = cfg_data["clusters"][str(test_cluster)]["top_configs"][0]
    cid, plabel = top["config_id"], top["preset"]
    ptuple = brain.preset_tuples.get(plabel) or _load_preset_tuple(symbol, plabel)[0]
    hm = re.search(r"_H(\d+)$", plabel)
    hyst = int(hm.group(1)) / 10.0 if hm else 0.0
    return brain, cfg_data, test_cluster, cid, plabel, ptuple, hyst

def brain_entries(symbol, df_test, warmup, brain, cfg_data, test_cluster, cid, plabel, ptuple):
    bits = decode_config_bits(cid)
    state = brain.get_state(symbol)
    state.current_cluster = test_cluster
    state.cluster_probs = np.ones(cfg_data["n_clusters"]) / cfg_data["n_clusters"]
    state.cluster_probs[test_cluster] = 0.9
    n_test = len(df_test)
    entries = []
    for i in range(warmup, n_test):
        window = df_test.iloc[max(0, i - warmup + 1):i + 1].reset_index(drop=True)
        cfg = {"config_id": cid, "preset": plabel, "preset_tuple": ptuple,
               "config_bits": bits, "cluster": test_cluster, "operable": True, "regime_changed": False}
        try:
            sig = _evaluate_bar(brain, symbol, window, cfg)
            if sig["action"] == "LONG":
                entries.append((i, 1))
            elif sig["action"] == "SHORT":
                entries.append((i, -1))
        except Exception:
            pass
    return entries

def kernel_entries(df_test, ptuple, hyst, symbol, cid, warmup):
    data = precalculate_all_data(df_test, preset=ptuple, hyst_mult=hyst, symbol=symbol)
    configs = np.array([cid], dtype=np.uint32)
    agg, pt = run_on_slice(configs, data, start_bar=warmup, end_bar=len(df_test),
                           sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT,
                           ts_pct=TS_PERCENT, cooldown_bars=COOLDOWN_BARS,
                           commission_pct=COMMISSION_ROUND_TRIP, warmup=100, return_per_trade=True)
    cnt = int(pt["count"][0])
    eb = pt["entry_bar"][0, :cnt].astype(int)
    # FIX: kernel entry_bar es relativo a actual_start = start_bar - kernel_warmup(100).
    # Convertir a índice ABSOLUTO en df_test para alinear con el bar 'i' del brain.
    eb_abs = eb + (warmup - 100)
    side = pt["side"][0, :cnt].astype(int) if "side" in pt else np.zeros(cnt, int)
    return list(zip(eb_abs.tolist(), side.tolist()))

def match_rate(brain_e, kern_e, tol=TOL):
    # greedy 1-1 match por barra ±tol
    kb = sorted(kern_e); used = [False] * len(kb)
    matched = 0
    for (b, _s) in sorted(brain_e):
        for j, (kbar, _ks) in enumerate(kb):
            if not used[j] and abs(kbar - b) <= tol:
                used[j] = True; matched += 1; break
    denom = max(len(brain_e), len(kern_e), 1)
    return matched, len(brain_e), len(kern_e), matched / denom * 100

results = []
for sym in SYMS:
    sc = sym.replace("/", "").replace("USDT", "")
    df_full = pd.read_parquet(os.path.join(_project_root, "data_cache", f"{sc}USDT_1h.parquet"))
    df_full = _normalize_ohlcv(df_full)
    df_test = df_full.tail(N).reset_index(drop=True)
    row = {"sym": sym}
    for W in WINDOWS:
        brain, cfg_data, tc, cid, plabel, ptuple, hyst = setup(sym)  # fresh state per window
        be = brain_entries(sym, df_test, W, brain, cfg_data, tc, cid, plabel, ptuple)
        ke = kernel_entries(df_test, ptuple, hyst, sym, cid, W)
        m, nb, nk, rate = match_rate(be, ke)
        row[f"W{W}"] = {"match_rate": round(rate, 2), "matched": m, "n_brain": nb, "n_kernel": nk}
        print(f"{sym:12} W={W:<4} entry-match={rate:6.2f}%  (matched {m}/max({nb},{nk}))", flush=True)
    results.append(row)
    print("", flush=True)

print("=== FALSACIÓN window-sensitivity: ¿FAILs(500) recuperan a 1500? ===")
for r in results:
    r500 = r["W500"]["match_rate"]; r1500 = r["W1500"]["match_rate"]
    verd = "RECUPERA (warmup confirmado)" if r1500 >= 98 else ("MEJORA parcial" if r1500 > r500 else "PERSISTE (no es solo warmup → escalar)")
    print(f"  {r['sym']:12} 500={r500:6.2f}% -> 1500={r1500:6.2f}%  {verd}")
json.dump(results, open("audit_capa1_fid1_window_results.json", "w"), indent=2)
print("\nNOTA: entry-match = Fidelidad 1 (indicadores). Exits/PnL (on-close vs intrabar) = Fidelidad 2, NO medido aquí.")
print("Saved: audit_capa1_fid1_window_results.json")
