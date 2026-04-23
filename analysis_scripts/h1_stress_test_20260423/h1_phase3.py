import csv, json, sys
sys.path.insert(0, r"C:\Users\rixip\combolab")
import pandas as pd, numpy as np
from datetime import datetime, timezone
from math import sqrt, erf
from collections import Counter, defaultdict

ENR = r"C:\Users\rixip\combolab\a1_h1_enriched.csv"
ATTR = r"C:\Users\rixip\combolab\attribution_per_trade_20260423_0856.csv"
SRC_CSV = r"C:\Users\rixip\combolab\audit_run_20260421\trade_history_2026-04-23.csv"

# reason_exit map
reason_map = {}
with open(SRC_CSV, encoding='utf-8', errors='replace') as f:
    f.readline()
    for raw in f:
        p = raw.rstrip('\n').split(',')
        if len(p) >= 10:
            reason_map[(p[0][:19], p[1])] = p[9]

# Load enriched N=98
rows = []
with open(ENR, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        r = dict(row)
        key = (r['ts'][:19], r['symbol'])
        r['reason_exit'] = reason_map.get(key, 'unknown')
        r['_ar'] = float(r['alpha_res'] or 0)
        r['_pnl'] = float(r['pnl'] or 0)
        rows.append(r)
print(f"N=98 rows loaded, reasons: {Counter(r['reason_exit'] for r in rows)}")

# Classification:
# strategy-logic: tf_exit, div_exit, cancel_tf, cancel_mr, zone_exit_mr, sl_hit
# structural: zone_exit (TF), not_operable, regime_change, sl_trigger_reconstructed
STRATEGY = {"tf_exit","div_exit","cancel_tf","cancel_mr","zone_exit_mr","sl_hit","sl_hit_mr"}
STRUCTURAL = {"zone_exit","not_operable","regime_change","sl_trigger_reconstructed"}

def cat(rz):
    if rz in STRATEGY: return "strategy"
    if rz in STRUCTURAL: return "structural"
    return "other"

for r in rows:
    r['_cat'] = cat(r['reason_exit'])

# Welch / MW / Cohen helpers
def welch(a, b):
    na,nb=len(a),len(b)
    if na<2 or nb<2: return (float('nan'), float('nan'))
    ma=sum(a)/na; mb=sum(b)/nb
    va=sum((x-ma)**2 for x in a)/(na-1)
    vb=sum((x-mb)**2 for x in b)/(nb-1)
    se=sqrt(va/na+vb/nb) if (va+vb)>0 else 1e-20
    t=(ma-mb)/se
    p = 2*(1-0.5*(1+erf(abs(t)/sqrt(2))))
    return t,p

def mw(a,b):
    na,nb=len(a),len(b)
    if na<2 or nb<2: return float('nan')
    combined=[(v,'a') for v in a]+[(v,'b') for v in b]
    combined.sort()
    ranks={}
    i=0
    while i<len(combined):
        j=i
        while j+1<len(combined) and combined[j+1][0]==combined[i][0]: j+=1
        avg=(i+j)/2+1
        for k in range(i,j+1): ranks[k]=avg
        i=j+1
    ra=sum(ranks[i] for i,(_,tg) in enumerate(combined) if tg=='a')
    U=ra-na*(na+1)/2
    mu=na*nb/2
    sig=sqrt(na*nb*(na+nb+1)/12)
    z=(U-mu)/sig if sig>0 else 0
    p = 2*(1-0.5*(1+erf(abs(z)/sqrt(2))))
    return p

def cohen_d(a,b):
    na,nb=len(a),len(b)
    if na<2 or nb<2: return float('nan')
    ma=sum(a)/na; mb=sum(b)/nb
    va=sum((x-ma)**2 for x in a)/(na-1)
    vb=sum((x-mb)**2 for x in b)/(nb-1)
    sp=sqrt(((na-1)*va+(nb-1)*vb)/(na+nb-2)) if (va+vb)>0 else 1e-20
    return (ma-mb)/sp

print(f"\n=== 3.1.3 STRATEGY vs STRUCTURAL — GLOBAL N=98 ===")
for cat_name in ["strategy","structural","other"]:
    s = [r for r in rows if r['_cat']==cat_name]
    if not s:
        print(f"  {cat_name}: N=0")
        continue
    ar=[r['_ar'] for r in s]
    pn=[r['_pnl'] for r in s]
    mean_ar = sum(ar)/len(ar); mean_pn=sum(pn)/len(pn)
    var = sum((x-mean_ar)**2 for x in ar)/max(len(ar)-1,1)
    sd = sqrt(var)
    print(f"  {cat_name:<12} N={len(s):3d}  sumAR={sum(ar):+7.3f}  mean={mean_ar:+.4f}  sd={sd:.4f}  sumPnL={sum(pn):+7.3f} mean={mean_pn:+.4f}")

# Welch strategy vs structural
strat_ar=[r['_ar'] for r in rows if r['_cat']=='strategy']
struct_ar=[r['_ar'] for r in rows if r['_cat']=='structural']
if len(strat_ar)>=2 and len(struct_ar)>=2:
    t,p = welch(strat_ar, struct_ar)
    pmw = mw(strat_ar, struct_ar)
    d = cohen_d(strat_ar, struct_ar)
    print(f"\n  Welch strategy vs structural α_res: t={t:+.3f}  p={p:.4f}  MW p={pmw:.4f}  Cohen_d={d:+.3f}")
    sg = sum(strat_ar)/len(strat_ar)
    xg = sum(struct_ar)/len(struct_ar)
    print(f"  mean strategy {sg:+.4f}  mean structural {xg:+.4f}  gap {abs(sg-xg):.4f}  ratio {sg/xg if abs(xg)>1e-9 else 'inf':.3f}" if abs(xg)>1e-9 else f"  mean strategy {sg:+.4f}  mean structural {xg:+.4f}")

# Per segment
print(f"\n=== 3.1.4 STRATEGY vs STRUCTURAL — PER SEGMENT ===")
segs = defaultdict(list)
for r in rows: segs[r['seg']].append(r)

print(f"{'seg':<22} {'Ns':>3} {'AR_str':>8} {'mean':>8}  {'Nx':>3} {'AR_sct':>8} {'mean':>8}  {'ratio':>8}  {'W_p':>7}")
for s in ["S1_pre_v2311","S2_v2311_v240","S3_v240_v244","S4_post_v244"]:
    trs = segs.get(s, [])
    st = [r['_ar'] for r in trs if r['_cat']=='strategy']
    sc = [r['_ar'] for r in trs if r['_cat']=='structural']
    ar_s = sum(st); ar_c=sum(sc)
    ms = ar_s/len(st) if st else 0.0
    mc = ar_c/len(sc) if sc else 0.0
    ratio = f"{ms/mc:+7.2f}" if abs(mc)>1e-9 else "  nan"
    wp = f"{welch(st,sc)[1]:.3f}" if (len(st)>=2 and len(sc)>=2) else "  -"
    print(f"{s:<22} {len(st):>3} {ar_s:>+8.3f} {ms:>+8.4f}  {len(sc):>3} {ar_c:>+8.3f} {mc:>+8.4f}  {ratio:>8}  {wp:>7}")

# Per reason individual
print(f"\n=== 3.1.6 PER REASON INDIVIDUAL (N=98) ===")
per_r = defaultdict(list)
for r in rows: per_r[r['reason_exit']].append(r)
total_ar = sum(r['_ar'] for r in rows)
print(f"{'reason':<25} {'cat':<10} {'N':>3} {'sumAR':>8} {'mean':>8}  {'% of total':>10}")
for rz, lst in sorted(per_r.items(), key=lambda x: sum(r['_ar'] for r in x[1])):
    n=len(lst); sar=sum(r['_ar'] for r in lst)
    mar=sar/n if n else 0
    pct=100*sar/total_ar if abs(total_ar)>1e-9 else 0
    print(f"{rz:<25} {cat(rz):<10} {n:>3} {sar:>+8.3f} {mar:>+8.4f}  {pct:>+9.1f}%")

# W3-flagged cross-check. W3-flagged: ONDO C0, LTC C2, GRT C2, TRX C2, BTC C2, MANA C0
# Load attribution for cluster info
flagged = {("ONDO/USDT","0"), ("LTC/USDT","2"), ("GRT/USDT","2"),
           ("TRX/USDT","2"), ("BTC/USDT","2"), ("MANA/USDT","0")}

# Need cluster per trade — from attribution CSV directly
cluster_map = {}
with open(ATTR, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cluster_map[(r['ts'][:19], r['symbol'])] = r.get('cluster','')
for r in rows:
    r['_cluster'] = cluster_map.get((r['ts'][:19], r['symbol']), '')
    r['_flagged'] = (r['symbol'], r['_cluster']) in flagged

print(f"\n=== 3.1.7 W3-FLAGGED CROSS-CHECK ===")
flg_rows = [r for r in rows if r['_flagged']]
unf_rows = [r for r in rows if not r['_flagged']]
print(f"W3-flagged trades: {len(flg_rows)}  non-flagged: {len(unf_rows)}")
print(f"Flagged: {Counter((r['symbol'], r['_cluster']) for r in flg_rows)}")

print(f"\n{'bucket':<28}  {'N':>3}  {'sumAR':>8}  {'meanAR':>8}")
for lbl, grp in [("Flagged × strategy",   [r for r in flg_rows if r['_cat']=='strategy']),
                 ("Flagged × structural", [r for r in flg_rows if r['_cat']=='structural']),
                 ("Non-flagged × strategy",   [r for r in unf_rows if r['_cat']=='strategy']),
                 ("Non-flagged × structural", [r for r in unf_rows if r['_cat']=='structural'])]:
    n=len(grp); s=sum(r['_ar'] for r in grp); m=s/n if n else 0
    print(f"{lbl:<28}  {n:>3}  {s:>+8.3f}  {m:>+8.4f}")

# Save trades for funding enrich — write raw CSV row for each of N=98
with open(SRC_CSV, encoding='utf-8', errors='replace') as f:
    header = f.readline()
    raw_map = {}
    for raw in f:
        p = raw.rstrip('\n').split(',')
        if len(p) >= 2:
            raw_map[(p[0][:19], p[1])] = raw

out_csv = r"C:\Users\rixip\combolab\trades_N98_filtered.csv"
with open(out_csv, 'w', encoding='utf-8', newline='') as fo:
    fo.write(header)
    for r in rows:
        key = (r['ts'][:19], r['symbol'])
        if key in raw_map:
            fo.write(raw_map[key])
print(f"\nWrote {out_csv} for funding enrich")
