"""Bloque 2c Parte B — Smoke C replicating pipeline productivo doubled_labels.

Setup matching regime_walk_forward.py L571-575:
- cluster_labels doubled: bars train (primeros 67%) → labels 0-2 (cluster k);
  bars fwd (últimos 33%) → labels 3-5 (cluster k+3).
- n_clusters=6 (doubled).
- Kernel extract cl_gp[cfg, k] (train) + cl_gp[cfg, k+3] (fwd) → pf_tr + pf_fwd.
- pf_combined = weighted_mean ponderado por trades.

Scope: sanity pilot 3 configs (BTC C2, ONDO C0, GRT C2) + 60 configs
Fase A full si sanity pasa.
"""
import sys, os, re, json
import numpy as np
import pandas as pd
import joblib
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "live"))

from brain_engine import (
    load_models, _normalize_ohlcv, _load_preset_tuple,
    COOLDOWN_BARS, SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT, COMMISSION_ROUND_TRIP,
)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice
from regime_features import compute_regime_features

DATA_DIR = os.path.join(ROOT, "binance_w3_data")
GMM_DIR = os.path.join(ROOT, "regime_models")
FASE_A_CSV = os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_fase_a_results.csv")
OUT_CSV = os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_smoke_c_results.csv")

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

# ----- SANITY PILOT 3 configs -----
SANITY = [
    ("BTC", 2, 20607806, "Tenkan(16)/EMA(42)_H05", 6.359),
    ("ONDO", 0, 2457036, "VIDYA(18)/KAMA(54)_H00", 7.945),
    ("GRT", 2, 58457547, "TEMA(10)/VIDYA(49)_H00", 1.272),
]

print("=== SANITY PILOT (3 configs W3 flagged) — doubled_labels + train/fwd split ===")
print(f"Split train/fwd: {TRAIN_FRAC:.0%} / {1-TRAIN_FRAC:.0%}")
print(f"{'sym':<6}{'cl':<4}{'cfg_id':<12}{'pf_fwd_JSON':<14}{'pf_tr_bin':<11}{'pf_fwd_bin':<12}{'pf_comb_bin':<12}{'N_tr':<7}{'N_fwd':<7}{'el':<7}")

sanity_results = []
for sym, cl, cfg, preset, pf_fwd_json in SANITY:
    r = run_config(sym, cl, cfg, preset, pf_fwd_json)
    sanity_results.append(r)
    print(f"{r['symbol']:<6}{r['cluster_productive']:<4}{r['config_id']:<12}{r['pf_fwd_JSON']:<14.3f}{r['pf_tr_bin']:<11.3f}{r['pf_fwd_bin']:<12.3f}{r['pf_combined_bin']:<12.3f}{r['trades_tr']:<7}{r['trades_fwd']:<7}{r['elapsed_s']:<6.1f}s")

# Decisión sanity: si pf_fwd_bin top-1 W3 flagged > 1.5 en ≥1/3 → proceed full 60
threshold_pass = sum(1 for r in sanity_results if r['pf_fwd_bin'] >= 1.5)
print(f"\nSanity threshold (pf_fwd_bin ≥ 1.5): {threshold_pass}/3 pass")
if threshold_pass >= 1:
    print("PROCEED full 60 configs")
else:
    print("CAVEAT: sanity muestra pf_fwd_bin aún bajo con setup productivo — finding robust potential")
    print("Proceeding anyway para evidencia completa")

# ----- FULL 60 CONFIGS Fase A -----
print(f"\n=== FULL 60 CONFIGS (Fase A universe) ===")
df_fa = pd.read_csv(FASE_A_CSV)
# Filter out top1 que ya están en sanity (evitar duplicados) o incluir todos
all_results = list(sanity_results)  # start with sanity

seen = {(r['symbol'], r['cluster_productive'], r['config_id']) for r in sanity_results}

print(f"{'sym':<6}{'cl':<4}{'grp':<6}{'cfg_id':<12}{'pf_tr':<9}{'pf_fwd':<9}{'pf_comb':<9}{'el':<6}", flush=True)

for idx, row in df_fa.iterrows():
    sym = row['symbol']; cl_prod = int(row['cluster'])
    cfg_id = int(row['config_id'])
    preset = row['preset']
    pf_fwd_wf = float(row['pf_fwd_WF']) if 'pf_fwd_WF' in row else 0.0
    if (sym, cl_prod, cfg_id) in seen:
        continue
    try:
        r = run_config(sym, cl_prod, cfg_id, preset, pf_fwd_wf)
        r['rank_group'] = row['rank_group']
        all_results.append(r)
        print(f"{sym:<6}{cl_prod:<4}{row['rank_group']:<6}{cfg_id:<12}{r['pf_tr_bin']:<9.3f}{r['pf_fwd_bin']:<9.3f}{r['pf_combined_bin']:<9.3f}{r['elapsed_s']:<5.1f}s", flush=True)
    except Exception as e:
        print(f"{sym} C{cl_prod} ERROR: {e}", flush=True)

df_all = pd.DataFrame(all_results)
# Add rank_group to sanity rows
for i, r in enumerate(sanity_results):
    df_all.loc[df_all['config_id'] == r['config_id'], 'rank_group'] = 'top1'

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

print("\n=== DISTRIBUCIONES pf_fwd_bin por group ===")
print(f"{'group':<8}{'N':<4}{'mean_pf_tr':>12}{'mean_pf_fwd':>12}{'mean_pf_comb':>13}{'pf_fwd>=2':>11}{'pf_fwd<1':>10}")
for grp in ["top1","mid","tail"]:
    sub = df_all[df_all['rank_group']==grp]
    if len(sub)==0: continue
    mtr = sub['pf_tr_bin'].mean()
    mfwd = sub['pf_fwd_bin'].mean()
    mcomb = sub['pf_combined_bin'].mean()
    p_ge2 = (sub['pf_fwd_bin']>=2.0).sum()
    p_lt1 = (sub['pf_fwd_bin']<1.0).sum()
    print(f"{grp:<8}{len(sub):<4}{mtr:>12.3f}{mfwd:>12.3f}{mcomb:>13.3f}{p_ge2:>10}/{len(sub)} {p_lt1:>8}/{len(sub)}")

# Spearman pf_fwd_JSON vs pf_fwd_bin
all_j = df_all['pf_fwd_JSON'].tolist()
all_b = df_all['pf_fwd_bin'].tolist()
rho, p = spearman(all_j, all_b)
print(f"\nSpearman ρ(pf_fwd_JSON, pf_fwd_bin) all: {rho:+.4f}  p={p:.4f}  N={len(all_j)}")

# Welch top1 vs tail pf_fwd_bin
s1 = df_all[df_all['rank_group']=='top1']['pf_fwd_bin'].tolist()
s3 = df_all[df_all['rank_group']=='tail']['pf_fwd_bin'].tolist()
if len(s1)>=2 and len(s3)>=2:
    t, p = welch(s1, s3)
    print(f"Welch top1 vs tail pf_fwd_bin: t={t:+.3f} p={p:.4f}  (mean {sum(s1)/len(s1):.3f} vs {sum(s3)/len(s3):.3f})")

# Veredicto
mean_top_fwd = sum(s1)/len(s1) if s1 else 0
print(f"\n=== VEREDICTO SMOKE C ===")
if mean_top_fwd >= 1.5 and rho > 0.4:
    case = "EDGE PRODUCTIVO CONFIRMADO — setup productivo preserva edge, Q1+W1+A+B.1 eran sobre-generalización"
elif mean_top_fwd >= 1.2 and rho > 0.2:
    case = "EDGE MODERADO — setup productivo revela edge modesto, mejor que sin filter pero no robusto"
else:
    case = "SESGO REAL CONFIRMADO — incluso con setup productivo correcto, edge ausente en Binance 3y"
print(f"  Top-1 mean pf_fwd_bin: {mean_top_fwd:.3f}")
print(f"  Spearman ρ(JSON, binance): {rho:+.3f}")
print(f"  VEREDICTO: {case}")
