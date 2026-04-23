import csv, json, sys
sys.path.insert(0, r"C:\Users\rixip\combolab")
import pandas as pd, numpy as np, joblib
from datetime import datetime, timezone
from math import sqrt, erf
from regime_features import compute_regime_features

ATTR = r"C:\Users\rixip\combolab\attribution_per_trade_20260423_0856.csv"
BTC  = r"C:\Users\rixip\combolab\data_cache\BTCUSDT_1h_fresh.parquet"
CSV_SRC = r"C:\Users\rixip\combolab\audit_run_20260421\trade_history_2026-04-23.csv"

btc = pd.read_parquet(BTC).sort_values('timestamp_ms').reset_index(drop=True)
btc['ts_utc'] = pd.to_datetime(btc['timestamp_ms'], unit='ms', utc=True)
model = joblib.load(r"C:\Users\rixip\combolab\regime_models\BTC_regime.joblib")
gmm, scaler = model['gmm'], model['scaler']
feats, valid = compute_regime_features(btc, lookback=model['lookback'])
print(f"BTC features valid: {valid.sum()} / {len(valid)}")
clusters = np.full(len(btc), -1, dtype=int)
valid_idx = np.where(valid)[0]
if len(valid_idx):
    Xs = scaler.transform(feats[valid])
    clusters[valid_idx] = gmm.predict_proba(Xs).argmax(axis=1)
btc['cluster'] = clusters

def btc_row(ts):
    t = ts.floor('h')
    sel = btc[btc['ts_utc']==t]
    if len(sel)==0:
        sel = btc[btc['ts_utc']<=t]
        if len(sel)==0: return None
        return sel.iloc[-1]
    return sel.iloc[0]

entry_ms_map = {}
with open(CSV_SRC, encoding='utf-8', errors='replace') as f:
    f.readline()
    for raw in f:
        p=raw.rstrip('\n').split(',')
        if len(p)>=12:
            try: ms=int(p[11])
            except: ms=0
            if ms>0: entry_ms_map[(p[0][:19],p[1])] = ms

V2311 = datetime(2026,4,19,17,51,tzinfo=timezone.utc)
V240  = datetime(2026,4,20,14,8,tzinfo=timezone.utc)
V244  = datetime(2026,4,21,18,22,2,tzinfo=timezone.utc)

def seg_of(ts):
    if ts < V2311: return "S1_pre_v2311"
    if ts < V240:  return "S2_v2311_v240"
    if ts < V244:  return "S3_v240_v244"
    return "S4_post_v244"

with open(ATTR, encoding='utf-8') as f:
    rows=list(csv.DictReader(f))

enriched=[]
excl_cross=0; excl_btc=0; excl_unan=0
for r in rows:
    if r.get('analyzable')=='no':
        excl_unan+=1
        continue
    ts = pd.to_datetime(r['ts'], utc=True)
    key=(r['ts'][:19], r['symbol'])
    ems = entry_ms_map.get(key, 0)
    if ems>0:
        entry_ts = pd.to_datetime(ems, unit='ms', utc=True)
    else:
        entry_ts = ts - pd.Timedelta(hours=1)
    seg_entry = seg_of(entry_ts.to_pydatetime())
    seg_exit  = seg_of(ts.to_pydatetime())
    if seg_entry != seg_exit:
        excl_cross+=1
        continue
    be = btc_row(entry_ts); bx = btc_row(ts)
    if be is None or bx is None:
        excl_btc+=1
        continue
    btc_delta = 100*(bx['close']/be['close'] - 1)
    if btc_delta > 1.0: mov="alcista"
    elif btc_delta < -1.0: mov="bajista"
    else: mov="lateral"
    r['_seg']=seg_entry
    r['_entry_ts']=entry_ts
    r['_btc_delta']=btc_delta
    r['_btc_mov']=mov
    r['_btc_cluster_entry']=int(be['cluster']) if be['cluster']>=0 else -1
    r['_hold_h']=max(1, int((ts-entry_ts).total_seconds()/3600))
    r['_ar']=float(r.get('alpha_residual',0) or 0)
    r['_slip']=float(r.get('slippage_entry',0) or 0)+float(r.get('slippage_exit',0) or 0)
    r['_factor']=float(r.get('factor_portfolio',0) or 0)
    r['_funding']=float(r.get('funding',0) or 0)
    r['_pnl']=float(r.get('pnl_real',0) or 0)
    r['_alpha_nom']=float(r.get('alpha_esperado_nominal',0) or 0)
    enriched.append(r)

print(f"Enriched: {len(enriched)}  excl_unan={excl_unan} excl_cross={excl_cross} excl_btc_data={excl_btc}")

# Segment summary
segs = {}
for r in enriched:
    segs.setdefault(r['_seg'], []).append(r)

print("\n=== 1. N POR SEGMENTO ===")
for s in ["S1_pre_v2311","S2_v2311_v240","S3_v240_v244","S4_post_v244"]:
    trs = segs.get(s,[])
    n_s=sum(1 for t in trs if t['side']=='short')
    n_l=sum(1 for t in trs if t['side']=='long')
    print(f"  {s}: N={len(trs)} (short={n_s}, long={n_l})")

def table(buckets, label):
    print(f"\n=== {label} ===")
    print(f"{'bucket':<24} {'N_s':>4} {'SαR_s':>9} {'N_l':>4} {'SαR_l':>9}  {'mean_s':>8} {'mean_l':>8}  {'ratio':>8}")
    for k in sorted(buckets):
        ts = buckets[k]
        shorts=[t for t in ts if t['side']=='short']
        longs =[t for t in ts if t['side']=='long']
        if len(shorts)+len(longs)==0: continue
        ar_s = sum(t['_ar'] for t in shorts)
        ar_l = sum(t['_ar'] for t in longs)
        ms = ar_s/len(shorts) if shorts else 0
        ml = ar_l/len(longs) if longs else 0
        if abs(ar_l)>1e-6:
            ratio=f"{ar_s/ar_l:+7.2f}"
        else:
            ratio=" inf"
        print(f"{k:<24} {len(shorts):>4} {ar_s:>+9.3f} {len(longs):>4} {ar_l:>+9.3f}  {ms:>+8.4f} {ml:>+8.4f}  {ratio}")

table(segs, "2.2.1 PER SEGMENT")

mov_buckets={}
for r in enriched: mov_buckets.setdefault(r['_btc_mov'],[]).append(r)
table(mov_buckets, "2.2.2 PER BTC MOVIMIENTO (durante hold)")

bi2={}
for r in enriched: bi2.setdefault(f"{r['_seg'][:2]}_{r['_btc_mov']}",[]).append(r)
table(bi2, "2.2.3 2D SEGMENTO x MOVIMIENTO")

cl_buckets={}
for r in enriched: cl_buckets.setdefault(f"C{r['_btc_cluster_entry']}",[]).append(r)
table(cl_buckets, "2.2.4 PER BTC GMM CLUSTER (entry)")

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

print("\n=== 2.3 WELCH / MW / COHEN_D (short vs long alpha_residual) ===")
for s in ["S1_pre_v2311","S2_v2311_v240","S3_v240_v244","S4_post_v244"]:
    trs=segs.get(s,[])
    sh=[t['_ar'] for t in trs if t['side']=='short']
    lg=[t['_ar'] for t in trs if t['side']=='long']
    if len(sh)>=2 and len(lg)>=2:
        t,p = welch(sh,lg); pmw = mw(sh,lg); d=cohen_d(sh,lg)
        print(f"  {s:<22} Ns={len(sh):>3} Nl={len(lg):>3}  Welch t={t:+.3f} p={p:.4f}  MW p={pmw:.4f}  Cohen_d={d:+.3f}")
    else:
        print(f"  {s:<22} insufficient (Ns={len(sh)} Nl={len(lg)})")

for m in ["alcista","lateral","bajista"]:
    trs=mov_buckets.get(m,[])
    sh=[t['_ar'] for t in trs if t['side']=='short']
    lg=[t['_ar'] for t in trs if t['side']=='long']
    if len(sh)>=2 and len(lg)>=2:
        t,p = welch(sh,lg); pmw = mw(sh,lg); d=cohen_d(sh,lg)
        print(f"  BTC_{m:<10} Ns={len(sh):>3} Nl={len(lg):>3}  Welch t={t:+.3f} p={p:.4f}  MW p={pmw:.4f}  Cohen_d={d:+.3f}")

print(f"\n=== 2.4 COMPONENTES PER SIDE (N={len(enriched)}) ===")
sh_all=[t for t in enriched if t['side']=='short']
lg_all=[t for t in enriched if t['side']=='long']
print(f"N shorts={len(sh_all)}  N longs={len(lg_all)}")
for name, field in [("alpha_residual","_ar"),("slippage","_slip"),("factor_port","_factor"),("funding","_funding"),("alpha_nominal","_alpha_nom"),("pnl_real","_pnl"),("hold_h","_hold_h")]:
    sh_vals=[t[field] for t in sh_all]
    lg_vals=[t[field] for t in lg_all]
    ms=sum(sh_vals)/len(sh_vals); ml=sum(lg_vals)/len(lg_vals)
    if len(sh_vals)>=2 and len(lg_vals)>=2:
        t,p = welch(sh_vals, lg_vals)
        print(f"  {name:<14} mean_s={ms:+7.4f} mean_l={ml:+7.4f}  Welch p={p:.4f}")

# OLS manual: alpha_residual ~ side_short_dummy + btc_delta
xs = np.array([[1.0 if t['side']=='short' else 0.0, t['_btc_delta']] for t in enriched])
ys = np.array([t['_ar'] for t in enriched])
# add intercept
X = np.column_stack([np.ones(len(xs)), xs])
# OLS: beta = (X'X)^-1 X'y
try:
    beta = np.linalg.lstsq(X, ys, rcond=None)[0]
    resid = ys - X @ beta
    rss = float((resid**2).sum())
    n,p = X.shape
    dfr = n - p
    sigma2 = rss/dfr
    cov = sigma2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    tstat = beta/se
    from math import erf
    pv = [2*(1-0.5*(1+erf(abs(ti)/sqrt(2)))) for ti in tstat]
    print(f"\n=== 2.3.3 OLS: alpha_residual ~ side_short + btc_delta ===")
    print(f"  intercept:     coef={beta[0]:+.4f}  se={se[0]:.4f}  t={tstat[0]:+.3f}  p={pv[0]:.4f}")
    print(f"  side_short:    coef={beta[1]:+.4f}  se={se[1]:.4f}  t={tstat[1]:+.3f}  p={pv[1]:.4f}")
    print(f"  btc_delta_pct: coef={beta[2]:+.4f}  se={se[2]:.4f}  t={tstat[2]:+.3f}  p={pv[2]:.4f}")
except Exception as e:
    print(f"OLS error: {e}")

with open(r"C:\Users\rixip\combolab\a1_h1_enriched.csv",'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['ts','symbol','side','seg','pnl','alpha_nom','alpha_res','slip','factor','funding','hold_h','btc_delta_pct','btc_mov','btc_cluster_entry'])
    for r in enriched:
        w.writerow([r['ts'][:19],r['symbol'],r['side'],r['_seg'],r['_pnl'],r['_alpha_nom'],r['_ar'],r['_slip'],r['_factor'],r['_funding'],r['_hold_h'],r['_btc_delta'],r['_btc_mov'],r['_btc_cluster_entry']])
print(f"\nwrote a1_h1_enriched.csv ({len(enriched)} rows)")
