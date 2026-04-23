"""Bloque 2c Fase B.1 — cluster filter post-hoc sobre 60 configs Fase A.

Kernel Numba expone per-cluster aggregates via cluster_labels parameter.
Re-ejecutamos los 60 configs con GMM cluster classification per-bar
(regime_models/{SYMBOL}_regime.joblib aplicado a parquet Binance 3y).

Para cada config, PF_filtered = cl_gp / cl_gl DEL CLUSTER PRODUCTIVO
(donde specialist debería operar). Compara vs PF_full de Fase A
(aggregate sin filter).
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
OUT_CSV = os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_fase_b1_results.csv")

# Load Fase A configs
df_fa = pd.read_csv(FASE_A_CSV)
print(f"Fase A configs: {len(df_fa)}")
print(f"Groups: {df_fa['rank_group'].value_counts().to_dict()}")

# Pre-compute cluster_labels per symbol (cache)
cluster_cache = {}
print(f"\nComputing GMM cluster_labels per symbol...")
symbols = df_fa['symbol'].unique()
for sym in symbols:
    parq = os.path.join(DATA_DIR, f"{sym}USDT_1h.parquet")
    gmm_path = os.path.join(GMM_DIR, f"{sym}_regime.joblib")
    if not os.path.exists(gmm_path):
        print(f"  {sym}: MISSING GMM {gmm_path}")
        continue
    df = pd.read_parquet(parq)
    df = _normalize_ohlcv(df)
    m = joblib.load(gmm_path)
    feats, valid = compute_regime_features(df, lookback=m['lookback'])
    cluster_ids = np.full(len(df), -1, dtype=np.int64)
    idx_valid = np.where(valid)[0]
    if len(idx_valid):
        Xs = m['scaler'].transform(feats[valid])
        lbl = m['gmm'].predict_proba(Xs).argmax(axis=1)
        cluster_ids[idx_valid] = lbl
    # For -1 bars (insufficient warmup), assign to cluster 0 fallback (they're excluded via filter anyway)
    cluster_ids[cluster_ids == -1] = 0
    cluster_cache[sym] = cluster_ids
    vc = pd.Series(lbl if len(idx_valid) else []).value_counts().to_dict() if len(idx_valid) else {}
    print(f"  {sym}: {len(df)} bars valid={valid.sum()} distribution={vc}")

print(f"\nCluster caches: {len(cluster_cache)}")

# Kernel runs per config with cluster_labels
results = []
warmup = 500
N_CLUSTERS = 3  # k=3 GMM productivos

print(f"\n{'sym':<6}{'cl':<3}{'grp':<6}{'cfg_id':<12}{'PF_full':<9}{'PF_filt':<9}{'N_full':<8}{'N_filt':<8}{'el':<6}")

for idx, row in df_fa.iterrows():
    sym = row['symbol']; cl_prod = int(row['cluster'])
    cfg_id = int(row['config_id']); preset = row['preset']
    t0 = time.time()

    if sym not in cluster_cache:
        print(f"{sym} C{cl_prod}: no cluster_cache")
        continue

    parq = os.path.join(DATA_DIR, f"{sym}USDT_1h.parquet")
    df_p = pd.read_parquet(parq)
    df_p = _normalize_ohlcv(df_p)
    n_bars = len(df_p)

    brain = load_models(
        regime_models_dir=GMM_DIR,
        specialist_configs_dir=os.path.join(ROOT, "regime_wf"),
        symbols=[f"{sym}/USDT"],
    )

    preset_tuple = brain.preset_tuples.get(preset)
    if preset_tuple is None:
        preset_tuple, _ = _load_preset_tuple(f"{sym}/USDT", preset)
    if preset_tuple is None:
        print(f"{sym} C{cl_prod}: preset unresolvable {preset}")
        continue

    hyst_match = re.search(r"_H(\d+)$", preset)
    hyst_mult = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0

    try:
        data = precalculate_all_data(df_p, preset=preset_tuple, hyst_mult=hyst_mult, symbol=f"{sym}/USDT")
    except Exception as e:
        print(f"{sym} C{cl_prod}: precalc ERROR {e}")
        continue

    configs = np.array([cfg_id], dtype=np.uint32)
    cluster_labels = cluster_cache[sym].astype(np.int64)
    assert len(cluster_labels) == n_bars, f"cluster_labels len mismatch: {len(cluster_labels)} vs {n_bars}"

    try:
        res, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = run_on_slice(
            configs, data,
            start_bar=warmup, end_bar=n_bars,
            sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT,
            ts_pct=TS_PERCENT, cooldown_bars=COOLDOWN_BARS,
            commission_pct=COMMISSION_ROUND_TRIP,
            warmup=100,
            cluster_labels=cluster_labels,
            n_clusters=N_CLUSTERS,
        )
    except Exception as e:
        print(f"{sym} C{cl_prod}: kernel ERROR {type(e).__name__}: {e}")
        continue

    # FULL aggregates
    pnl_full = float(res[0, 0]); trades_full = int(res[0, 1])
    gp_full = float(res[0, 5]); gl_full = float(res[0, 6])
    PF_full = (gp_full/gl_full) if gl_full > 0 else (float('inf') if gp_full > 0 else 0.0)

    # PER-CLUSTER aggregates — cluster productivo
    pnl_cl = float(cl_pnl[0, cl_prod]); trades_cl = int(cl_trades[0, cl_prod])
    gp_cl = float(cl_gp[0, cl_prod]); gl_cl = float(cl_gl[0, cl_prod])
    PF_cl = (gp_cl/gl_cl) if gl_cl > 0 else (float('inf') if gp_cl > 0 else 0.0)

    el = time.time()-t0

    results.append({
        "symbol": sym, "cluster_productive": cl_prod, "rank_group": row['rank_group'],
        "config_id": cfg_id, "preset": preset,
        "pf_fwd_WF": row['pf_fwd_WF'],
        "PF_3y_full": PF_full, "N_trades_full": trades_full,
        "PF_3y_filtered": PF_cl, "N_trades_filtered": trades_cl,
        "ratio_filt_full": trades_cl/trades_full if trades_full > 0 else 0,
        "pnl_cluster": pnl_cl, "pnl_full": pnl_full,
        "elapsed_s": el,
    })
    print(f"{sym:<6}{cl_prod:<3}{row['rank_group']:<6}{cfg_id:<12}{PF_full:<9.3f}{PF_cl:<9.3f}{trades_full:<8}{trades_cl:<8}{el:<5.1f}s")

df_out = pd.DataFrame(results)
df_out.to_csv(OUT_CSV, index=False)
print(f"\nSaved {OUT_CSV} ({len(df_out)} rows)")

# === ANÁLISIS B.1.4 ===
from math import sqrt, erf
def welch(a,b):
    na,nb=len(a),len(b)
    if na<2 or nb<2: return (float('nan'), float('nan'))
    ma=sum(a)/na; mb=sum(b)/nb
    va=sum((x-ma)**2 for x in a)/(na-1)
    vb=sum((x-mb)**2 for x in b)/(nb-1)
    se=sqrt(va/na+vb/nb) if (va+vb)>0 else 1e-20
    t=(ma-mb)/se
    p=2*(1-0.5*(1+erf(abs(t)/sqrt(2))))
    return t,p
def mw(a,b):
    na,nb=len(a),len(b)
    combined=[(v,'a') for v in a]+[(v,'b') for v in b]
    combined.sort()
    ranks={}; i=0
    while i<len(combined):
        j=i
        while j+1<len(combined) and combined[j+1][0]==combined[i][0]: j+=1
        avg=(i+j)/2+1
        for k in range(i,j+1): ranks[k]=avg
        i=j+1
    ra=sum(ranks[i] for i,(_,tg) in enumerate(combined) if tg=='a')
    U=ra-na*(na+1)/2; mu=na*nb/2
    sig=sqrt(na*nb*(na+nb+1)/12)
    z=(U-mu)/sig if sig>0 else 0
    return 2*(1-0.5*(1+erf(abs(z)/sqrt(2))))
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

print("\n=== FASE B.1.4 — DISTRIBUCIONES PF_FILTERED por GROUP ===")
print(f"{'group':<8}{'N':<4}{'mean_full':>10}{'mean_filt':>10}{'delta':>8}{'median_f':>10}{'PF_f>=2':>8}{'PF_f<1':>8}{'N_cl_mean':>10}")
for grp in ["top1","mid","tail"]:
    sub_full = df_out[df_out['rank_group']==grp]['PF_3y_full'].tolist()
    sub_filt = df_out[df_out['rank_group']==grp]['PF_3y_filtered'].tolist()
    n_cls = df_out[df_out['rank_group']==grp]['N_trades_filtered'].tolist()
    if not sub_full: continue
    mf = sum(sub_full)/len(sub_full)
    mfilt = sum(sub_filt)/len(sub_filt)
    median_filt = sorted(sub_filt)[len(sub_filt)//2]
    pf_ge2 = sum(1 for x in sub_filt if x>=2.0)
    pf_lt1 = sum(1 for x in sub_filt if x<1.0)
    n_cl_mean = sum(n_cls)/len(n_cls)
    print(f"{grp:<8}{len(sub_full):<4}{mf:>10.3f}{mfilt:>10.3f}{mfilt-mf:>+8.3f}{median_filt:>10.3f}{pf_ge2:>7}/{len(sub_filt)} {pf_lt1:>6}/{len(sub_filt)} {n_cl_mean:>10.1f}")

# Spearman PF_WF vs PF_filtered
all_wf = df_out['pf_fwd_WF'].tolist()
all_filt = df_out['PF_3y_filtered'].tolist()
rho, p = spearman(all_wf, all_filt)
print(f"\n=== SPEARMAN (PF_WF, PF_filtered) all = {rho:+.4f}  p={p:.4f} (Fase A all PF_full = +0.229 p=0.074) ===")

# Welch top-1 vs tail PF_filtered
s1 = df_out[df_out['rank_group']=='top1']['PF_3y_filtered'].tolist()
s3 = df_out[df_out['rank_group']=='tail']['PF_3y_filtered'].tolist()
t, p = welch(s1, s3)
pm = mw(s1, s3)
print(f"\n=== WELCH top-1 vs tail PF_filtered: t={t:+.3f} p={p:.4f}  MW p={pm:.4f} (Fase A p=0.751) ===")

# Veredicto
mean_top_filt = sum(s1)/len(s1) if s1 else 0
mean_tail_filt = sum(s3)/len(s3) if s3 else 0
print(f"\n  Top-1 mean PF_filtered: {mean_top_filt:.3f}")
print(f"  Tail  mean PF_filtered: {mean_tail_filt:.3f}")

if mean_top_filt >= 1.5 and p < 0.05:
    case = "RESTAURADO — régimen filter restaura edge, Fase A explicable por caveat"
elif mean_top_filt >= 1.2 and p < 0.10:
    case = "PARCIAL — régimen filter restaura parcialmente, continuar B.2"
else:
    case = "CONFIRMADO — hallazgo Fase A robusto dentro régimen diseñado, escalar B.2"
print(f"\n  VEREDICTO FASE B.1: {case}")
