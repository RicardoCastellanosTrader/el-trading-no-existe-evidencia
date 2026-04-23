"""Bloque 2c Opción Q1 — W3 divergencia validation cuantitativa.

Ejecuta kernel Numba run_on_slice sobre 10 (symbol, cluster) × Binance
Futures 3y data. Aggregates PF/trades/wins sin per-trade output
(limitación kernel aggregate-only, sin Tier 0 I1).
"""
import sys, os, re
import numpy as np
import pandas as pd
import pickle
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "live"))

from brain_engine import (
    load_models, _normalize_ohlcv, _load_preset_tuple,
    COOLDOWN_BARS, SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT, COMMISSION_ROUND_TRIP,
)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice

DATA_DIR = os.path.join(ROOT, "binance_w3_data")

with open(os.path.join(ROOT, "bloque2c_targets.pkl"), "rb") as f:
    TARGETS = pickle.load(f)

print(f"Targets: {len(TARGETS)}")
print(f"{'sym':<6}{'cl':<4}{'flag':<22}{'cfg_id':<12}{'preset':<38}{'PF_kern':<10}{'trades':<8}{'wins':<6}{'pnl':<8}{'elapsed':<8}")

results = []
warmup = 500

for sym, cl, ftype, cfg_id, preset, pf_c_wf, pf_f_wf in TARGETS:
    t0 = time.time()
    parq = os.path.join(DATA_DIR, f"{sym}USDT_1h.parquet")
    if not os.path.exists(parq):
        print(f"{sym} C{cl}: MISSING PARQUET")
        continue

    df = pd.read_parquet(parq)
    df = _normalize_ohlcv(df)
    n_bars = len(df)
    if n_bars < 2000:
        print(f"{sym} C{cl}: insufficient bars {n_bars}")
        continue

    # Load brain models (incluye preset_tuples)
    brain = load_models(
        regime_models_dir=os.path.join(ROOT, "regime_models"),
        specialist_configs_dir=os.path.join(ROOT, "regime_wf"),
        symbols=[f"{sym}/USDT"],
    )

    preset_tuple = brain.preset_tuples.get(preset)
    if preset_tuple is None:
        preset_tuple, _ = _load_preset_tuple(f"{sym}/USDT", preset)
    if preset_tuple is None:
        print(f"{sym} C{cl}: preset_tuple unresolvable")
        continue

    hyst_match = re.search(r"_H(\d+)$", preset)
    hyst_mult = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0

    try:
        data = precalculate_all_data(df, preset=preset_tuple, hyst_mult=hyst_mult, symbol=f"{sym}/USDT")
    except Exception as e:
        print(f"{sym} C{cl}: precalc ERROR {type(e).__name__}: {e}")
        continue

    configs = np.array([cfg_id], dtype=np.uint32)
    try:
        res, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = run_on_slice(
            configs, data,
            start_bar=warmup, end_bar=n_bars,
            sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT,
            ts_pct=TS_PERCENT, cooldown_bars=COOLDOWN_BARS,
            commission_pct=COMMISSION_ROUND_TRIP,
            warmup=100,
        )
    except Exception as e:
        print(f"{sym} C{cl}: kernel ERROR {type(e).__name__}: {e}")
        continue

    kernel_pnl = float(res[0, 0])
    kernel_trades = int(res[0, 1])
    kernel_wins = int(res[0, 2])
    kernel_gp = float(res[0, 5])
    kernel_gl = float(res[0, 6])
    pf_3y = (kernel_gp / kernel_gl) if kernel_gl > 0 else float('inf') if kernel_gp > 0 else 0.0
    el = time.time() - t0

    results.append({
        "symbol": sym, "cluster": cl, "flag_type": ftype,
        "config_id": cfg_id, "preset": preset,
        "pf_combined_WF": pf_c_wf, "pf_fwd_WF": pf_f_wf,
        "pf_3y_binance": pf_3y, "trades_3y": kernel_trades,
        "wins_3y": kernel_wins, "pnl_3y": kernel_pnl,
        "gp_3y": kernel_gp, "gl_3y": kernel_gl,
        "n_bars_data": n_bars, "elapsed_s": el,
    })
    print(f"{sym:<6}{cl:<4}{ftype:<22}{cfg_id:<12}{preset:<38}{pf_3y:<10.3f}{kernel_trades:<8}{kernel_wins:<6}{kernel_pnl:<8.2f}{el:<7.1f}s")

# Save results
df_res = pd.DataFrame(results)
df_res.to_csv(os.path.join(ROOT, "bloque2c_w3_results.csv"), index=False)
print(f"\nResults saved to bloque2c_w3_results.csv ({len(results)} rows)")

# Veredicto W3 validation cuantitativa
print("\n=== AGREGADOS POR FLAG TYPE ===")
for ftype in ["W3", "CANDIDATO_EXCLUSION"]:
    subset = [r for r in results if r["flag_type"] == ftype]
    if not subset: continue
    pfs = [r["pf_3y_binance"] for r in subset]
    n_under_15 = sum(1 for x in pfs if x < 1.5)
    n_under_10 = sum(1 for x in pfs if x < 1.0)
    n_above_20 = sum(1 for x in pfs if x >= 2.0)
    mean_pf = sum(pfs)/len(pfs)
    print(f"  {ftype:<22} N={len(subset)}  mean_PF={mean_pf:.3f}  PF<1.5={n_under_15}/{len(subset)}  PF<1.0={n_under_10}/{len(subset)}  PF>=2.0={n_above_20}/{len(subset)}")

print("\n=== PER-CLUSTER DETAIL ===")
for r in results:
    n_trades = r["trades_3y"]
    pf = r["pf_3y_binance"]
    pf_wf = r["pf_combined_WF"]
    ratio = pf / pf_wf if pf_wf and pf_wf > 0 else float('nan')
    label = ""
    if pf < 1.0: label = "EDGE PERDIDO"
    elif pf < 1.5: label = "EDGE DEBIL"
    elif pf < 2.0: label = "EDGE MODERADO"
    else: label = "EDGE ROBUSTO"
    print(f"  {r['symbol']:<6}C{r['cluster']:<2}{r['flag_type']:<22}PF_WF={pf_wf:<7}PF_3y={pf:<8.3f}ratio={ratio:<6.3f}N_trades={n_trades:<5}{label}")
