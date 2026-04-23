"""Bloque 2c Opción W1 — control group unflagged matched-by-pf_fwd.

Ejecuta kernel sobre 10 top-1 configs NO flagged (matching distribución
pf_fwd del grupo flagged Q1) para discriminar entre:
(A) filter W3+CANDIDATO discrimina edge decay — control unflagged PF_3y ≥ 2.0.
(B) inflación universal walk-forward — control unflagged PF_3y similar a flagged.
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

CONTROL_GROUP = [
    ("MANA", "1", 35173823, "ALMA(20)/ZLEMA(39)_H05", 1.377, 232),
    ("TRX",  "0", 3156128,  "SMA(18)/TEMA(54)_H05",    1.472, 380),
    ("MANA", "2", 53443118, "ALMA(24)/VIDYA(66)_H05",  1.789, 99),
    ("APT",  "2", 52477067, "McGinley(20)/FRAMA(75)_H05", 1.829, 178),
    ("BTC",  "1", 1118752,  "T3(18)/ALMA(57)_H05",     3.997, 59),
    ("APT",  "1", 31447907, "ALMA(18)/ALMA(54)_H05",   4.780, 25),
    ("SEI",  "1", 40002182, "McGinley(24)/EMA(30)_H00", 5.208, 24),
    ("BTC",  "0", 38007639, "ALMA(24)/SMA(57)_H05",    5.490, 19),
    ("SAND", "0", 20075296, "VIDYA(24)/FRAMA(51)_H00", 9.512, 18),
    ("SAND", "2", 16987014, "VIDYA(14)/KAMA(42)_H05",  18.963, 19),
]

print(f"Control group: {len(CONTROL_GROUP)} configs (unflagged, matched pf_fwd distribution)")
print(f"{'sym':<6}{'cl':<4}{'cfg_id':<12}{'preset':<38}{'pf_fwd':<10}{'PF_3y':<10}{'trades':<8}{'pnl':<10}{'elapsed':<8}")

results = []
warmup = 500

for sym, cl, cfg_id, preset, pf_fwd_wf, n_fwd_wf in CONTROL_GROUP:
    t0 = time.time()
    parq = os.path.join(DATA_DIR, f"{sym}USDT_1h.parquet")
    if not os.path.exists(parq):
        print(f"{sym} C{cl}: MISSING PARQUET (skipping)")
        continue

    df = pd.read_parquet(parq)
    df = _normalize_ohlcv(df)
    n_bars = len(df)

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
    pf_3y = (kernel_gp / kernel_gl) if kernel_gl > 0 else (float('inf') if kernel_gp > 0 else 0.0)
    el = time.time() - t0
    ratio = pf_3y / pf_fwd_wf if pf_fwd_wf > 0 else 0

    results.append({
        "symbol": sym, "cluster": cl, "flag_type": "UNFLAGGED_CONTROL",
        "config_id": cfg_id, "preset": preset,
        "pf_fwd_WF": pf_fwd_wf, "n_fwd_WF": n_fwd_wf,
        "pf_3y_binance": pf_3y, "trades_3y": kernel_trades,
        "wins_3y": kernel_wins, "pnl_3y": kernel_pnl,
        "gp_3y": kernel_gp, "gl_3y": kernel_gl,
        "n_bars_data": n_bars, "elapsed_s": el,
        "ratio_wf_3y": ratio,
    })
    print(f"{sym:<6}{cl:<4}{cfg_id:<12}{preset:<38}{pf_fwd_wf:<10.3f}{pf_3y:<10.3f}{kernel_trades:<8}{kernel_pnl:<10.2f}{el:<7.1f}s")

df_res = pd.DataFrame(results)
df_res.to_csv(os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_w1_control_results.csv"), index=False)
print(f"\nResults saved to analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_w1_control_results.csv ({len(results)} rows)")

# Estadísticas control group
pfs = [r["pf_3y_binance"] for r in results]
n_under_15 = sum(1 for x in pfs if x < 1.5)
n_under_10 = sum(1 for x in pfs if x < 1.0)
n_above_20 = sum(1 for x in pfs if x >= 2.0)
mean_pf = sum(pfs)/len(pfs)
ratios = [r["ratio_wf_3y"] for r in results]
mean_ratio = sum(ratios)/len(ratios)

print(f"\n=== CONTROL GROUP AGGREGATES (N={len(results)}) ===")
print(f"  mean PF_3y:     {mean_pf:.3f}")
print(f"  median PF_3y:   {sorted(pfs)[len(pfs)//2]:.3f}")
print(f"  PF<1.5: {n_under_15}/{len(results)}")
print(f"  PF<1.0: {n_under_10}/{len(results)}")
print(f"  PF>=2.0: {n_above_20}/{len(results)}")
print(f"  mean ratio WF/3y: {mean_ratio:.3f}")

# Comparación con Q1 flagged
print(f"\n=== COMPARACION FLAGGED Q1 vs CONTROL W1 ===")
Q1_PFS = [0.894, 1.045, 1.004, 1.227, 0.952, 0.855, 0.825, 0.870, 1.030, 0.917]
Q1_RATIOS = [0.16, 0.30, 0.82, 0.10, 0.20, 0.24, 0.51, 0.27, 0.68, 0.51]
q1_mean = sum(Q1_PFS)/len(Q1_PFS)

from math import sqrt, erf
def welch(a, b):
    na, nb = len(a), len(b)
    ma = sum(a)/na; mb = sum(b)/nb
    va = sum((x-ma)**2 for x in a)/(na-1)
    vb = sum((x-mb)**2 for x in b)/(nb-1)
    se = sqrt(va/na + vb/nb)
    t = (ma - mb) / se if se > 0 else 0
    p = 2*(1-0.5*(1+erf(abs(t)/sqrt(2))))
    return t, p

def cohen_d(a, b):
    na, nb = len(a), len(b)
    ma = sum(a)/na; mb = sum(b)/nb
    va = sum((x-ma)**2 for x in a)/(na-1)
    vb = sum((x-mb)**2 for x in b)/(nb-1)
    sp = sqrt(((na-1)*va + (nb-1)*vb)/(na+nb-2))
    return (ma-mb)/sp if sp > 0 else 0

def mw(a, b):
    na, nb = len(a), len(b)
    combined = [(v,'a') for v in a] + [(v,'b') for v in b]
    combined.sort()
    ranks = {}
    i = 0
    while i < len(combined):
        j = i
        while j+1 < len(combined) and combined[j+1][0] == combined[i][0]: j += 1
        avg = (i+j)/2 + 1
        for k in range(i, j+1): ranks[k] = avg
        i = j+1
    ra = sum(ranks[i] for i,(_,tg) in enumerate(combined) if tg=='a')
    U = ra - na*(na+1)/2
    mu = na*nb/2
    sig = sqrt(na*nb*(na+nb+1)/12)
    z = (U-mu)/sig if sig > 0 else 0
    p = 2*(1-0.5*(1+erf(abs(z)/sqrt(2))))
    return p

t, p_welch = welch(Q1_PFS, pfs)
d = cohen_d(Q1_PFS, pfs)
p_mw = mw(Q1_PFS, pfs)

print(f"  Flagged Q1 mean: {q1_mean:.3f}  (N=10)")
print(f"  Control W1 mean: {mean_pf:.3f}  (N={len(pfs)})")
print(f"  Delta:           {mean_pf - q1_mean:+.3f}")
print(f"  Welch t:         {t:+.3f}")
print(f"  Welch p:         {p_welch:.4f}")
print(f"  Mann-Whitney p:  {p_mw:.4f}")
print(f"  Cohen d:         {d:+.3f}")

# Veredicto
if mean_pf >= 1.5 and p_welch < 0.05:
    vered = "FILTER DISCRIMINA (control significativamente mayor)"
elif mean_pf < 1.3 and p_welch > 0.1:
    vered = "INFLACION UNIVERSAL (control similar a flagged)"
else:
    vered = "INTERMEDIO"
print(f"\n  VEREDICTO: {vered}")
