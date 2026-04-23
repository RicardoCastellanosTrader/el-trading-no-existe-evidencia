"""Bloque 2c Fase A — caracterización sesgo walk-forward.

Sampling 3 groups × 20 configs:
- Top-1 (reuso 10 Q1 flagged + 10 W1 control = 20 testados).
- Mid-rank (rank 10 de 20 clusters cross-parquets disponibles).
- Tail-rank (rank 95 de 20 clusters cross-parquets disponibles).

Objetivo: determinar si top-1 correlaciona con PF_3y real (Caso α
noise aditivo) o si sesgo es universal multi-testing sin signal
(Caso β noise puro) o combinado (Caso γ).
"""
import sys, os, re, json
import numpy as np
import pandas as pd
import time
import random

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "live"))

from brain_engine import (
    load_models, _normalize_ohlcv, _load_preset_tuple,
    COOLDOWN_BARS, SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT, COMMISSION_ROUND_TRIP,
)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice

DATA_DIR = os.path.join(ROOT, "binance_w3_data")
JSON_DIR = os.path.join(ROOT, "regime_wf")
OUT_CSV = os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_fase_a_results.csv")

# Symbols disponibles en parquets Q1+W1
PARQ_SYMS = ["ONDO","LTC","GRT","TRX","BTC","MANA","APT","SAND","SEI"]

random.seed(42)

def load_top_configs(sym, cluster_id):
    path = os.path.join(JSON_DIR, f"{sym}USDT_specialist_configs.json")
    with open(path) as f:
        d = json.load(f)
    return d.get("clusters", {}).get(str(cluster_id), {}).get("top_configs", [])

# Mid-rank + Tail-rank sampling: 20 configs cada uno cross-parquets+clusters
MID_RANK = 10    # index 10 = rank 11
TAIL_RANK = 95   # index 95 = rank 96 (de top-100)

mid_sample = []
tail_sample = []

# Iterar cross-symbol+cluster con parquets disponibles
cluster_candidates = []
for sym in PARQ_SYMS:
    for cl in ["0","1","2"]:
        tops = load_top_configs(sym, cl)
        if len(tops) > max(MID_RANK, TAIL_RANK):
            cluster_candidates.append((sym, cl, tops))

print(f"Cluster candidates with ≥100 configs: {len(cluster_candidates)}")

# Sample 20 cluster_candidates random (para cada group independiente)
# Evitar sesgo: mismo 20 para mid + tail (same sym-cluster, different ranks)
random.shuffle(cluster_candidates)
selected_clusters = cluster_candidates[:20]

for sym, cl, tops in selected_clusters:
    mid_cfg = tops[MID_RANK]
    tail_cfg = tops[TAIL_RANK]
    mid_sample.append({
        "symbol": sym, "cluster": cl, "rank_group": "mid",
        "config_id": mid_cfg["config_id"], "preset": mid_cfg["preset"],
        "pf_combined_WF": mid_cfg.get("pf_combined", 0),
        "pf_fwd_WF": mid_cfg.get("pf_fwd", 0),
        "n_fwd_WF": mid_cfg.get("trades_fwd", 0),
    })
    tail_sample.append({
        "symbol": sym, "cluster": cl, "rank_group": "tail",
        "config_id": tail_cfg["config_id"], "preset": tail_cfg["preset"],
        "pf_combined_WF": tail_cfg.get("pf_combined", 0),
        "pf_fwd_WF": tail_cfg.get("pf_fwd", 0),
        "n_fwd_WF": tail_cfg.get("trades_fwd", 0),
    })

print(f"Mid-rank sample: {len(mid_sample)}")
print(f"Tail-rank sample: {len(tail_sample)}")

# Ejecución kernel
all_to_run = mid_sample + tail_sample
results = []
warmup = 500

print(f"\nRunning {len(all_to_run)} kernel configs (40 nuevos)...")
print(f"{'sym':<6}{'cl':<3}{'grp':<6}{'cfg_id':<12}{'pf_fwd':<9}{'n_fwd':<7}{'PF_3y':<9}{'trades':<8}{'pnl':<9}{'el':<6}")

for item in all_to_run:
    sym = item["symbol"]; cl = item["cluster"]
    cfg_id = item["config_id"]; preset = item["preset"]
    t0 = time.time()
    parq = os.path.join(DATA_DIR, f"{sym}USDT_1h.parquet")
    if not os.path.exists(parq):
        print(f"{sym} C{cl}: MISSING PARQUET")
        continue

    df = pd.read_parquet(parq)
    df = _normalize_ohlcv(df)
    n_bars = len(df)

    brain = load_models(
        regime_models_dir=os.path.join(ROOT, "regime_models"),
        specialist_configs_dir=JSON_DIR,
        symbols=[f"{sym}/USDT"],
    )

    preset_tuple = brain.preset_tuples.get(preset)
    if preset_tuple is None:
        preset_tuple, _ = _load_preset_tuple(f"{sym}/USDT", preset)
    if preset_tuple is None:
        print(f"{sym} C{cl}: preset unresolvable {preset}")
        continue

    hyst_match = re.search(r"_H(\d+)$", preset)
    hyst_mult = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0

    try:
        data = precalculate_all_data(df, preset=preset_tuple, hyst_mult=hyst_mult, symbol=f"{sym}/USDT")
    except Exception as e:
        print(f"{sym} C{cl}: precalc ERROR {e}")
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
        print(f"{sym} C{cl}: kernel ERROR {e}")
        continue

    kernel_pnl = float(res[0, 0])
    kernel_trades = int(res[0, 1])
    kernel_gp = float(res[0, 5])
    kernel_gl = float(res[0, 6])
    pf_3y = (kernel_gp/kernel_gl) if kernel_gl > 0 else (float('inf') if kernel_gp > 0 else 0.0)
    el = time.time()-t0
    ratio = pf_3y/item["pf_fwd_WF"] if item["pf_fwd_WF"] > 0 else 0

    r = {**item, "PF_3y": pf_3y, "trades_3y": kernel_trades, "pnl_3y": kernel_pnl, "ratio_wf_3y": ratio, "elapsed_s": el}
    results.append(r)
    print(f"{sym:<6}{cl:<3}{item['rank_group']:<6}{cfg_id:<12}{item['pf_fwd_WF']:<9.3f}{item['n_fwd_WF']:<7}{pf_3y:<9.3f}{kernel_trades:<8}{kernel_pnl:<9.2f}{el:<5.1f}s")

# Add top-1 group (reuse Q1+W1 existing results)
print(f"\nAggregating top-1 group (reuso Q1+W1 = 20 configs existing):")
for csv_path in [
    os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_w3_results.csv"),
    os.path.join(ROOT, "analysis_scripts", "bloque2c_w3_validation_20260423", "bloque2c_w1_control_results.csv"),
]:
    prev = pd.read_csv(csv_path)
    for _, row in prev.iterrows():
        r = {
            "symbol": row["symbol"], "cluster": str(row["cluster"]),
            "rank_group": "top1",
            "config_id": row["config_id"], "preset": row.get("preset",""),
            "pf_combined_WF": row.get("pf_combined_WF", row.get("pf_combined",0)),
            "pf_fwd_WF": row.get("pf_fwd_WF", row.get("pf_fwd",0)),
            "n_fwd_WF": row.get("n_fwd_WF", 0),
            "PF_3y": row["pf_3y_binance"], "trades_3y": row["trades_3y"],
            "pnl_3y": row["pnl_3y"], "ratio_wf_3y": row.get("ratio_wf_3y", row["pf_3y_binance"]/row.get("pf_fwd_WF", row.get("pf_fwd",1)) if row.get("pf_fwd_WF", row.get("pf_fwd",0))>0 else 0),
            "elapsed_s": row.get("elapsed_s", 0),
        }
        results.append(r)
    print(f"  loaded {csv_path.split(os.sep)[-1]}")

df_all = pd.DataFrame(results)
df_all.to_csv(OUT_CSV, index=False)
print(f"\nTotal results: {len(df_all)}  saved {OUT_CSV}")

# === ANÁLISIS A.3 ===
from math import sqrt, erf
def welch(a,b):
    na,nb=len(a),len(b)
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

print("\n=== FASE A.3.1 — DISTRIBUCIONES por GROUP ===")
print(f"{'group':<8}{'N':<4}{'mean':>9}{'median':>9}{'std':>9}{'P25':>9}{'P75':>9}{'pf>=2':>8}{'pf<1':>8}")
for grp in ["top1","mid","tail"]:
    sub = df_all[df_all["rank_group"]==grp]["PF_3y"].tolist()
    if not sub: continue
    n = len(sub)
    mean = sum(sub)/n
    sorted_s = sorted(sub)
    median = sorted_s[n//2]
    var = sum((x-mean)**2 for x in sub)/max(n-1,1)
    std = sqrt(var)
    p25 = sorted_s[int(0.25*n)]
    p75 = sorted_s[int(0.75*n)]
    pf_ge2 = sum(1 for x in sub if x>=2.0)
    pf_lt1 = sum(1 for x in sub if x<1.0)
    print(f"{grp:<8}{n:<4}{mean:>9.3f}{median:>9.3f}{std:>9.3f}{p25:>9.3f}{p75:>9.3f}{pf_ge2:>7}/{n} {pf_lt1:>7}/{n}")

print("\n=== FASE A.3.2 — CORRELACIÓN PF_WF vs PF_3y (ALL GROUPS) ===")
all_pfs_wf = df_all["pf_fwd_WF"].tolist()
all_pfs_3y = df_all["PF_3y"].tolist()
rho, p_rho = spearman(all_pfs_wf, all_pfs_3y)
print(f"  Spearman rho = {rho:+.4f}  p = {p_rho:.4f}  N = {len(all_pfs_wf)}")
print(f"  Interpretación:")
if rho > 0.3:
    print(f"    rho > 0.3 → PF_WF tiene INFORMACIÓN sobre PF_real (Caso α)")
elif abs(rho) < 0.1:
    print(f"    rho ≈ 0 → PF_WF NO informa PF_real (Caso β noise puro)")
elif rho < -0.1:
    print(f"    rho < 0 → PF_WF anti-correlaciona (overfitting crítico)")
else:
    print(f"    rho ∈ [0.1, 0.3] → ambiguo (Caso γ)")

# Per-group correlación
for grp in ["top1","mid","tail"]:
    sub = df_all[df_all["rank_group"]==grp]
    if len(sub) >= 4:
        rho_g, p_g = spearman(sub["pf_fwd_WF"].tolist(), sub["PF_3y"].tolist())
        print(f"  {grp}: rho = {rho_g:+.4f}  p = {p_g:.4f}  N = {len(sub)}")

print("\n=== FASE A.3.3 — PAIRWISE TESTS PF_3y ===")
for g1, g2 in [("top1","mid"), ("top1","tail"), ("mid","tail")]:
    s1 = df_all[df_all["rank_group"]==g1]["PF_3y"].tolist()
    s2 = df_all[df_all["rank_group"]==g2]["PF_3y"].tolist()
    if len(s1)>=2 and len(s2)>=2:
        t,p = welch(s1,s2); pm = mw(s1,s2)
        print(f"  {g1} vs {g2}: mean {sum(s1)/len(s1):+.3f} vs {sum(s2)/len(s2):+.3f}  Welch p={p:.4f}  MW p={pm:.4f}")

print("\n=== FASE A.3.4 — RATIO PF_WF/PF_3y por GROUP ===")
for grp in ["top1","mid","tail"]:
    sub = df_all[df_all["rank_group"]==grp]["ratio_wf_3y"].tolist()
    if sub:
        mean_r = sum(sub)/len(sub)
        sorted_r = sorted(sub)
        median_r = sorted_r[len(sub)//2]
        print(f"  {grp}: mean ratio = {mean_r:.3f}  median = {median_r:.3f}")

# === VEREDICTO ===
print("\n=== VEREDICTO CASO α/β/γ ===")
mean_top1 = df_all[df_all["rank_group"]=="top1"]["PF_3y"].mean()
mean_tail = df_all[df_all["rank_group"]=="tail"]["PF_3y"].mean()
rho_all, p_all = spearman(all_pfs_wf, all_pfs_3y)
s1 = df_all[df_all["rank_group"]=="top1"]["PF_3y"].tolist()
s2 = df_all[df_all["rank_group"]=="tail"]["PF_3y"].tolist()
_, p_top_tail = welch(s1, s2)

print(f"  Spearman all: rho={rho_all:+.3f} p={p_all:.4f}")
print(f"  Top-1 vs tail mean: {mean_top1:.3f} vs {mean_tail:.3f}")
print(f"  Top-1 vs tail Welch p: {p_top_tail:.4f}")

if rho_all > 0.3 and mean_top1 > mean_tail + 0.3 and p_top_tail < 0.1:
    case = "α DOMINANTE — walk-forward tiene noise + signal"
elif abs(rho_all) < 0.15 and abs(mean_top1 - mean_tail) < 0.2 and p_top_tail > 0.3:
    case = "β DOMINANTE — inflación universal, top-1 noise puro"
elif rho_all < -0.1:
    case = "α CRÍTICO — overfitting detectable (PF_WF anti-correlaciona)"
else:
    case = "γ INTERMEDIO — ambos factores contribuyen"
print(f"\n  CASO: {case}")
