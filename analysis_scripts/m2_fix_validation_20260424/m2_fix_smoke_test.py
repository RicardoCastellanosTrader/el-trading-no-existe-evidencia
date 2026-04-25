"""M2 fix validation - CLON LITERAL de bloque2c_smoke_c.py (Smoke C original).

Solo 4 cambios sobre el original:
  (1) SANITY -> 3 M2 fix BTC top-1 configs (C0, C1, C2) + W3b BTC C2 baseline
      como sanity de determinismo (esperado pf_fwd_bin ~= 0.7722 segun
      bloque2c_smoke_c_results.csv).
  (2) Seccion "FULL 60 CONFIGS" eliminada (scope BTC-only por TAREA).
  (3) GMM_DIR override -> _gmm_head_baseline/ (GMM HEAD restaurado, identico
      al que Smoke C original uso; working tree GMM fue regenerado por
      smokes posteriores 2026-04-24/25 -> preservar paridad estricta).
  (4) OUT_CSV path -> directorio del adapter.

Setup matching regime_walk_forward.py L571-575 INVARIANTE:
- cluster_labels doubled (n_clusters=6), train/fwd 67%/33%.
- Kernel productivo run_on_slice, start_bar=0, warmup=100.
- Parquet Binance Futures 3y BTCUSDT.
"""
import sys, os, re, json
import numpy as np
import pandas as pd
import joblib
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
# Cambio (necesario): adapter vive en analysis_scripts/m2_fix_validation_20260424/
# y debe apuntar a combolab/ root (2 niveles arriba) para parquet + regime_models.
# Smoke C original asumia CWD=combolab/; este adapter resuelve paths absolutos.
COMBOLAB_ROOT = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, COMBOLAB_ROOT)
sys.path.insert(0, os.path.join(COMBOLAB_ROOT, "live"))

from brain_engine import (
    load_models, _normalize_ohlcv, _load_preset_tuple,
    COOLDOWN_BARS, SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT, COMMISSION_ROUND_TRIP,
)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice
from regime_features import compute_regime_features

DATA_DIR = os.path.join(COMBOLAB_ROOT, "binance_w3_data")
# GMM override -> _gmm_head_baseline/ (GMM HEAD restaurado, identico al usado
# por Smoke C original commit 431b5e1; working tree GMM fue regenerado por
# smokes posteriores 2026-04-24/25 -> paridad estricta requiere HEAD).
GMM_DIR = os.path.join(ROOT, "_gmm_head_baseline")
OUT_CSV = os.path.join(ROOT, "m2_fix_smoke_results.csv")

TRAIN_FRAC = 2/3  # 67% train, 33% fwd
N_CLUSTERS = 3   # base (doubled = 6)

def compute_doubled_labels(df_p, sym):
    """Compute doubled labels: train bars → cluster k (0-2), fwd bars → cluster k+3 (3-5)."""
    gmm_path = os.path.join(GMM_DIR, f"{sym}_regime.joblib")
    m = joblib.load(gmm_path)
    feats, valid = compute_regime_features(df_p, lookback=m['lookback'])
    base_labels = np.zeros(len(df_p), dtype=np.int64)
    idx_valid = np.where(valid)[0]
    if len(idx_valid):
        Xs = m['scaler'].transform(feats[valid])
        base_labels[idx_valid] = m['gmm'].predict_proba(Xs).argmax(axis=1)
    # Doubled: train bars = cluster k; fwd bars = cluster k + n_clusters
    n_bars = len(df_p)
    split_idx = int(n_bars * TRAIN_FRAC)
    doubled = base_labels.copy()
    doubled[split_idx:] = doubled[split_idx:] + N_CLUSTERS
    return doubled, split_idx, n_bars

def run_config(sym, cl_prod, cfg_id, preset, pf_fwd_json):
    parq = os.path.join(DATA_DIR, f"{sym}USDT_1h.parquet")
    df_p = pd.read_parquet(parq); df_p = _normalize_ohlcv(df_p)
    n_bars = len(df_p)

    brain = load_models(GMM_DIR, os.path.join(ROOT, "regime_wf"), [f"{sym}/USDT"])
    preset_tuple = brain.preset_tuples.get(preset)
    if preset_tuple is None:
        preset_tuple, _ = _load_preset_tuple(f"{sym}/USDT", preset)
    hyst_match = re.search(r"_H(\d+)$", preset)
    hyst_mult = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0

    doubled_labels, split_idx, _ = compute_doubled_labels(df_p, sym)

    data = precalculate_all_data(df_p, preset=preset_tuple, hyst_mult=hyst_mult, symbol=f"{sym}/USDT")
    configs = np.array([cfg_id], dtype=np.uint32)

    t0 = time.time()
    res, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = run_on_slice(
        configs, data, start_bar=0, end_bar=n_bars,
        sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT,
        ts_pct=TS_PERCENT, cooldown_bars=COOLDOWN_BARS,
        commission_pct=COMMISSION_ROUND_TRIP, warmup=100,
        cluster_labels=doubled_labels, n_clusters=N_CLUSTERS*2,
    )
    el = time.time() - t0

    # Extract train + fwd cluster k y k+3
    k_tr = cl_prod
    k_fwd = cl_prod + N_CLUSTERS

    trades_tr = int(cl_trades[0, k_tr])
    gp_tr = float(cl_gp[0, k_tr]); gl_tr = float(cl_gl[0, k_tr])
    pf_tr = (gp_tr/gl_tr) if gl_tr > 0 else (float('inf') if gp_tr > 0 else 0.0)

    trades_fwd = int(cl_trades[0, k_fwd])
    gp_fwd = float(cl_gp[0, k_fwd]); gl_fwd = float(cl_gl[0, k_fwd])
    pf_fwd = (gp_fwd/gl_fwd) if gl_fwd > 0 else (float('inf') if gp_fwd > 0 else 0.0)

    # pf_combined weighted mean (pondera por trades)
    total_tr = trades_tr + trades_fwd
    if total_tr > 0:
        pf_combined = (pf_tr * trades_tr + pf_fwd * trades_fwd) / total_tr
    else:
        pf_combined = 0.0

    return {
        "symbol": sym, "cluster_productive": cl_prod, "config_id": cfg_id,
        "preset": preset, "pf_fwd_JSON": pf_fwd_json,
        "pf_tr_bin": pf_tr, "trades_tr": trades_tr,
        "pf_fwd_bin": pf_fwd, "trades_fwd": trades_fwd,
        "pf_combined_bin": pf_combined,
        "split_idx": split_idx, "n_bars": n_bars,
        "elapsed_s": el,
    }

# ----- M2 fix BTC top-1 + W3b BTC C2 baseline (sanity determinismo) -----
# Cambios respecto al original:
# (1a) SANITY -> 3 M2 fix BTC top-1 (cfg_ids actuales rama
#      feature-m2-fix-pffwd-cilow-ranking, pf_fwd_JSON desde JSON activo).
# (1b) Append W3b BTC C2 baseline (cfg 20607806) para sanity check
#      determinismo numerico vs bloque2c_smoke_c_results.csv (esperado
#      pf_fwd_bin ~= 0.7722).
# (2) Seccion "FULL 60 CONFIGS" eliminada (scope BTC-only).
SANITY = [
    # M2 fix BTC top-1 (rama feature-m2-fix-pffwd-cilow-ranking commit 7162369)
    ("BTC", 0, 36909877, "ALMA(24)/SMA(57)_H00", 4.480),
    ("BTC", 1, 3758688, "VIDYA(14)/KAMA(49)_H05", 4.089),
    ("BTC", 2, 33831248, "T3(18)/T3(45)_H05", 5.468),
    # M2 fix ONDO top-1 (re-sort en memoria sobre JSONs smoke W3b 2026-04-24,
    # numericamente equivalente a pipeline M2 fix activo - W3+W4 filters
    # invariantes pre-sort).
    ("ONDO", 0, 34635228, "T3(22)/KAMA(57)_H00", 3.268),
    ("ONDO", 1, 12360961, "ALMA(20)/TEMA(51)_H00", 2.879),
    ("ONDO", 2, 48380978, "SMA(14)/TEMA(69)_H00", 3.953),
    # M2 fix SEI top-1 (re-sort en memoria, idem ONDO).
    ("SEI", 0, 57375331, "VWMA(14)/FRAMA(66)_H05", 3.436),
    ("SEI", 1, 1612992, "McGinley(24)/EMA(30)_H00", 3.083),
    ("SEI", 2, 815625, "T3(12)/HMA(54)_H00", 3.769),
    # W3b baseline BTC C2 (sanity determinismo - debe reproducir 0.7722)
    ("BTC", 2, 20607806, "Tenkan(16)/EMA(42)_H05", 6.359),
]

print("=== M2 FIX VALIDATION — Smoke C exact replica ===")
print(f"Split train/fwd: {TRAIN_FRAC:.0%} / {1-TRAIN_FRAC:.0%}")
print(f"GMM_DIR: {GMM_DIR}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"{'sym':<6}{'cl':<4}{'cfg_id':<12}{'pf_fwd_JSON':<14}{'pf_tr_bin':<11}{'pf_fwd_bin':<12}{'pf_comb_bin':<12}{'N_tr':<7}{'N_fwd':<7}{'el':<7}")

sanity_results = []
for sym, cl, cfg, preset, pf_fwd_json in SANITY:
    r = run_config(sym, cl, cfg, preset, pf_fwd_json)
    sanity_results.append(r)
    print(f"{r['symbol']:<6}{r['cluster_productive']:<4}{r['config_id']:<12}{r['pf_fwd_JSON']:<14.3f}{r['pf_tr_bin']:<11.3f}{r['pf_fwd_bin']:<12.3f}{r['pf_combined_bin']:<12.3f}{r['trades_tr']:<7}{r['trades_fwd']:<7}{r['elapsed_s']:<6.1f}s")

# Sanity determinismo: cfg 20607806 debe reproducir pf_fwd_bin ~= 0.7722
baseline = next((r for r in sanity_results if r['config_id'] == 20607806), None)
if baseline is not None:
    expected = 0.7722
    actual = baseline['pf_fwd_bin']
    deviation = abs(actual - expected) / expected if expected > 0 else float('inf')
    print(f"\nSANITY DETERMINISMO W3b BTC C2 cfg 20607806:")
    print(f"  Esperado pf_fwd_bin (CSV original): {expected:.4f}")
    print(f"  Actual pf_fwd_bin:                  {actual:.4f}")
    print(f"  Desviacion relativa: {deviation*100:.2f}%")
    if deviation < 0.01:
        print(f"  -> PASS (paridad GMM Smoke C original confirmada)")
    else:
        print(f"  -> FAIL (GMM/setup divergente vs Smoke C original; resultados M2 fix NO comparables 1:1)")

df_all = pd.DataFrame(sanity_results)
df_all.to_csv(OUT_CSV, index=False)
print(f"\nSaved {OUT_CSV} ({len(df_all)} rows)")

# Análisis final
from math import sqrt, erf
def welch(a,b):
    na,nb=len(a),len(b)
    if na<2 or nb<2: return (float('nan'), float('nan'))
    ma=sum(a)/na; mb=sum(b)/nb
    va=sum((x-ma)**2 for x in a)/(na-1)
    vb=sum((x-mb)**2 for x in b)/(nb-1)
    se=sqrt(va/na+vb/nb) if (va+vb)>0 else 1e-20
    t=(ma-mb)/se; p=2*(1-0.5*(1+erf(abs(t)/sqrt(2))))
    return t,p

def spearman(xs, ys):
    def ranks(lst):
        pairs=sorted(enumerate(lst), key=lambda x:x[1])
        r=[0]*len(lst); i=0
        while i<len(pairs):
            j=i
            while j+1<len(pairs) and pairs[j+1][1]==pairs[i][1]: j+=1
            avg=(i+j)/2+1
            for k in range(i,j+1): r[pairs[k][0]]=avg
            i=j+1
        return r
    rx=ranks(xs); ry=ranks(ys); n=len(xs)
    mx=sum(rx)/n; my=sum(ry)/n
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    dx=sqrt(sum((r-mx)**2 for r in rx))
    dy=sqrt(sum((r-my)**2 for r in ry))
    rho=num/(dx*dy) if dx*dy>0 else 0
    t=rho*sqrt((n-2)/(1-rho**2)) if abs(rho)<0.999 else float('inf')
    p=2*(1-0.5*(1+erf(abs(t)/sqrt(2))))
    return rho, p

# ===== TABLA COMPARATIVA + INTERPRETACION (T4-T6) =====
# Mapping cfg_id -> label
LABEL_MAP = {
    36909877: "M2_BTC_C0", 3758688: "M2_BTC_C1", 33831248: "M2_BTC_C2",
    34635228: "M2_ONDO_C0", 12360961: "M2_ONDO_C1", 48380978: "M2_ONDO_C2",
    57375331: "M2_SEI_C0", 1612992: "M2_SEI_C1", 815625: "M2_SEI_C2",
    20607806: "W3b_BTC_C2_baseline",
}

print("\n=== TABLA COMPARATIVA T4 (9 combos M2 fix + 1 W3b baseline) ===")
print(f"{'label':<26}{'cfg':<11}{'pf_fwd_JSON':>13}{'pf_fwd_bin':>13}{'ratio J/B':>11}{'N_fwd_bin':>11}")
all_labeled = []
for r in sanity_results:
    label = LABEL_MAP.get(r['config_id'], f"unknown_{r['config_id']}")
    ratio = (r['pf_fwd_JSON'] / r['pf_fwd_bin']) if r['pf_fwd_bin'] > 0 else float('inf')
    print(f"{label:<26}{r['config_id']:<11}{r['pf_fwd_JSON']:>13.3f}{r['pf_fwd_bin']:>13.3f}{ratio:>11.3f}{r['trades_fwd']:>11}")
    all_labeled.append((label, r, ratio))

# Per-symbol breakdown
print("\n=== T5a Per-symbol breakdown M2 fix (3 configs c/u) ===")
print(f"{'symbol':<8}{'mean_ratio_JB':>14}{'mean_pf_fwd_bin':>17}{'mean_pf_fwd_JSON':>17}{'N_fwd_bin_mean':>16}")
sym_stats = {}
for sym in ["BTC", "ONDO", "SEI"]:
    sym_rows = [(label, r, ratio) for label, r, ratio in all_labeled
                if label.startswith(f"M2_{sym}_")]
    ratios = [ratio for _, _, ratio in sym_rows if not (ratio != ratio or ratio == float('inf'))]
    bins = [r['pf_fwd_bin'] for _, r, _ in sym_rows]
    jsons = [r['pf_fwd_JSON'] for _, r, _ in sym_rows]
    n_fwds = [r['trades_fwd'] for _, r, _ in sym_rows]
    sym_stats[sym] = {
        'mean_ratio': sum(ratios)/len(ratios) if ratios else float('nan'),
        'mean_pf_fwd_bin': sum(bins)/len(bins) if bins else 0,
        'mean_pf_fwd_json': sum(jsons)/len(jsons) if jsons else 0,
        'mean_n_fwd': sum(n_fwds)/len(n_fwds) if n_fwds else 0,
    }
    s = sym_stats[sym]
    print(f"{sym:<8}{s['mean_ratio']:>14.3f}{s['mean_pf_fwd_bin']:>17.3f}{s['mean_pf_fwd_json']:>17.3f}{s['mean_n_fwd']:>16.1f}")

# Cross-9 aggregates
m2_rows_only = [(label, r, ratio) for label, r, ratio in all_labeled
                if label.startswith("M2_")]
ratios_only = [ratio for _, _, ratio in m2_rows_only
               if not (ratio != ratio or ratio == float('inf'))]
ratios_sorted = sorted(ratios_only)
n = len(ratios_sorted)
median_r = ratios_sorted[n//2] if n % 2 == 1 else (ratios_sorted[n//2-1]+ratios_sorted[n//2])/2
q1 = ratios_sorted[n//4]
q3 = ratios_sorted[3*n//4]
mean_r = sum(ratios_sorted)/n
print(f"\nCross-9 ratio J/B: mean={mean_r:.3f} median={median_r:.3f} IQR=[{q1:.3f}, {q3:.3f}]")

# T5 Interpretacion bands
print("\n=== INTERPRETACION T5 ===")
n_in_band = sum(1 for x in ratios_only if 0.5 <= x <= 1.5)
n_partial = sum(1 for x in ratios_only if 1.5 < x <= 3.33)
n_collapsed = sum(1 for x in ratios_only if 3.33 < x <= 5.0)
n_strong = sum(1 for x in ratios_only if x > 5.0)
print(f"  In band [0.5, 1.5] (Interpretacion 1): {n_in_band}/9")
print(f"  Moderado (1.5, 3.33]: {n_partial}/9")
print(f"  Colapso parcial (3.33, 5.0]: {n_collapsed}/9")
print(f"  Colapso fuerte (>5.0, Interpretacion 2): {n_strong}/9")

# T6 Ranking interno cross-9
print("\n=== RANKING INTERNO T6 (cross-9) ===")
rank_json = sorted(m2_rows_only, key=lambda x: x[1]['pf_fwd_JSON'], reverse=True)
rank_bin = sorted(m2_rows_only, key=lambda x: x[1]['pf_fwd_bin'], reverse=True)
print(f"  Top-3 JSON:    {[label for label, _, _ in rank_json[:3]]}")
print(f"  Top-3 Binance: {[label for label, _, _ in rank_bin[:3]]}")
overlap_top3 = len(set(label for label,_,_ in rank_json[:3]) & set(label for label,_,_ in rank_bin[:3]))
print(f"  Top-3 overlap: {overlap_top3}/3")
print(f"  Top-1 same?: {rank_json[0][0] == rank_bin[0][0]}")

js = [r['pf_fwd_JSON'] for _, r, _ in m2_rows_only]
bs = [r['pf_fwd_bin'] for _, r, _ in m2_rows_only]
rho, p_rho = spearman(js, bs)
print(f"  Spearman rho(JSON, Binance) cross-9: {rho:+.4f}  p={p_rho:.4f}")

# Veredicto final segun criterios prompt
print("\n=== VEREDICTO REFINADO (criterios prompt cross-9) ===")
if mean_r <= 2.0 and rho > 0.3:
    verdict = ("M2 FIX CONSOLIDADO - mean ratio<=2.0 + Spearman>0.3, "
               "avanzar Fase A (Z_BTC)")
elif 2.0 < mean_r <= 3.5:
    verdict = ("M2 FIX MEJORA PARCIAL - mean ratio 2.0-3.5, "
               "evaluar Opcion (b) combinar con _FWD_MIN_PF estricto")
else:  # mean_r > 3.5 or rho < 0
    verdict = ("M2 FIX NO RESUELVE GAP - mean ratio>3.5 o Spearman<0, "
               "revisar enfoque alternativo (subir _FWD_MIN_PF, "
               "posiblemente revertir M2 fix)")

if rho < 0 and mean_r <= 3.5:
    verdict += " [WARN: Spearman<0 fuerza re-evaluacion incluso si magnitud aceptable]"

print(f"\n  Mean ratio: {mean_r:.3f}")
print(f"  Spearman rho: {rho:+.4f}")
print(f"  Top-3 overlap: {overlap_top3}/3")
print(f"\n  VEREDICTO: {verdict}")

# Baseline comparison
baseline_row = next((r for label, r, ratio in all_labeled
                     if label == "W3b_BTC_C2_baseline"), None)
if baseline_row is not None:
    b_ratio = (baseline_row['pf_fwd_JSON'] / baseline_row['pf_fwd_bin']
               if baseline_row['pf_fwd_bin'] > 0 else float('inf'))
    print(f"\n  W3b baseline ratio: {b_ratio:.3f} (esperado ~8.24 - sanity OK si actual=0.7722)")
    print(f"  M2 fix mean ratio cross-9: {mean_r:.3f}")
    print(f"  Improvement vs baseline magnitude: {b_ratio/mean_r:.2f}x reduction")

print(f"\nFINAL VEREDICTO: {verdict}")
