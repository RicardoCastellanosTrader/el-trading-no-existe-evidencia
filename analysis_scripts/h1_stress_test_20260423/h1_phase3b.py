import csv, sys
sys.path.insert(0, r"C:\Users\rixip\combolab")
from math import sqrt, erf
from collections import defaultdict

ENR = r"C:\Users\rixip\combolab\a1_h1_enriched.csv"
FC  = r"C:\Users\rixip\AppData\Local\Temp\funding_context_N98.csv"

rows=[]
with open(ENR, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        r['_ar']=float(r['alpha_res'] or 0)
        r['_pnl']=float(r['pnl'] or 0)
        r['_pnl_pct']=0.0  # fill below
        rows.append(r)

# Key: ts[:19] + symbol
fc_map={}
with open(FC, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        fc_map[(r['timestamp'][:19], r['symbol'])]=r

# Get pnl_pct from source CSV
SRC_CSV = r"C:\Users\rixip\combolab\audit_run_20260421\trade_history_2026-04-23.csv"
pnl_pct_map={}
with open(SRC_CSV, encoding='utf-8', errors='replace') as f:
    f.readline()
    for raw in f:
        p=raw.rstrip('\n').split(',')
        if len(p)>=8:
            try: pnl_pct_map[(p[0][:19],p[1])]=float(p[6])
            except: pass

# Enrich rows with funding
for r in rows:
    key=(r['ts'][:19], r['symbol'])
    fc=fc_map.get(key)
    if fc:
        r['_crowd']=fc.get('signal_vs_entry_crowd','')
        r['_exit_crowd']=fc.get('position_vs_exit_crowd','')
        r['_pattern']=fc.get('entry_exit_pattern','')
        try: r['_nbars']=float(fc.get('n_bars_contrarian','') or 0)
        except: r['_nbars']=0
    else:
        r['_crowd']=''
        r['_pattern']=''
        r['_nbars']=None
    r['_pnl_pct']=pnl_pct_map.get(key, 0.0)

with_fc=[r for r in rows if r['_crowd']]
print(f"N with funding context: {len(with_fc)} / {len(rows)}")

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

# Distribution of with_fc across segments
print(f"\nWith-fc per segment:")
seg_cnt=defaultdict(int)
for r in with_fc: seg_cnt[r['seg']]+=1
for s in ["S1_pre_v2311","S2_v2311_v240","S3_v240_v244","S4_post_v244"]:
    print(f"  {s}: {seg_cnt[s]}")

# 3.2.3 Per segment: aligned vs contrarian entry
print(f"\n=== 3.2.3 Per segmento Aligned vs Contrarian (PnL%) ===")
print(f"{'seg':<22} {'Na':>3} {'mean_a%':>9} {'Nc':>3} {'mean_c%':>9} {'gap_pp':>8} {'Welch_p':>8} {'MW_p':>6}")
segs=defaultdict(list)
for r in with_fc: segs[r['seg']].append(r)
for s in ["S1_pre_v2311","S2_v2311_v240","S3_v240_v244","S4_post_v244"]:
    lst=segs.get(s,[])
    a=[r['_pnl_pct'] for r in lst if r['_crowd']=='aligned']
    c=[r['_pnl_pct'] for r in lst if r['_crowd']=='contrarian']
    if len(a)>=2 and len(c)>=2:
        t,p=welch(a,c); pm=mw(a,c)
        ma=sum(a)/len(a); mc=sum(c)/len(c)
        print(f"{s:<22} {len(a):>3} {ma:>+9.4f} {len(c):>3} {mc:>+9.4f} {ma-mc:>+8.3f} {p:>8.4f} {pm:>6.4f}")
    else:
        na=len(a); nc=len(c)
        print(f"{s:<22} {na:>3} {sum(a)/na if a else 0:>+9.4f} {nc:>3} {sum(c)/nc if c else 0:>+9.4f}   -insuff")

# 3.2.5 Pattern x alpha_residual
print(f"\n=== 3.2.5 Pattern x alpha_residual (N={len(with_fc)}) ===")
pat=defaultdict(list)
for r in with_fc: pat[r['_pattern']].append(r)
print(f"{'pattern':<24} {'N':>3} {'ΣαR':>8} {'mean_αR':>10}  {'meanPnL%':>10}")
for p_k, lst in sorted(pat.items(), key=lambda x: -len(x[1])):
    n=len(lst); ar=sum(r['_ar'] for r in lst); mar=ar/n; mpl=sum(r['_pnl_pct'] for r in lst)/n
    print(f"{p_k:<24} {n:>3} {ar:>+8.3f} {mar:>+10.4f}  {mpl:>+10.4f}")

# Comparison al→al vs contra→contra
aa=[r['_ar'] for r in with_fc if r['_pattern']=='aligned->aligned']
cc=[r['_ar'] for r in with_fc if r['_pattern']=='contrarian->contrarian']
if len(aa)>=2 and len(cc)>=2:
    ma=sum(aa)/len(aa); mc=sum(cc)/len(cc)
    t,p=welch(aa,cc); pm=mw(aa,cc)
    print(f"\naligned->aligned vs contrarian->contrarian α_res:")
    print(f"  al->al mean={ma:+.4f} (N={len(aa)})  con->con mean={mc:+.4f} (N={len(cc)})")
    gap_ratio = mc/ma if abs(ma)>1e-9 else float('inf')
    print(f"  ratio mean con/al: {gap_ratio:+.2f}x    Welch p={p:.4f}  MW p={pm:.4f}")

# Spearman ρ(n_bars_contrarian, pnl_pct) for N=49
nb=[(r['_nbars'], r['_pnl_pct']) for r in with_fc if r['_nbars'] is not None]
if len(nb)>=4:
    # Spearman manual
    def ranks(vals):
        pairs=sorted(enumerate(vals), key=lambda x: x[1])
        r=[0]*len(vals)
        i=0
        while i<len(pairs):
            j=i
            while j+1<len(pairs) and pairs[j+1][1]==pairs[i][1]: j+=1
            avg=(i+j)/2+1
            for k in range(i,j+1): r[pairs[k][0]]=avg
            i=j+1
        return r
    x=[p[0] for p in nb]; y=[p[1] for p in nb]
    rx=ranks(x); ry=ranks(y); nn=len(nb)
    mx=sum(rx)/nn; my=sum(ry)/nn
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(nn))
    dx=sqrt(sum((r-mx)**2 for r in rx))
    dy=sqrt(sum((r-my)**2 for r in ry))
    rho = num/(dx*dy) if dx*dy>0 else 0
    t_stat = rho*sqrt((nn-2)/(1-rho**2)) if abs(rho)<0.999 else float('inf')
    from math import erf
    p_approx = 2*(1-0.5*(1+erf(abs(t_stat)/sqrt(2))))
    print(f"\nSpearman ρ(n_bars_contrarian, pnl_pct) = {rho:+.4f}  t={t_stat:+.3f}  p={p_approx:.4f}  N={nn}")

# Spearman α_res
nb2=[(r['_nbars'], r['_ar']) for r in with_fc if r['_nbars'] is not None]
if len(nb2)>=4:
    x=[p[0] for p in nb2]; y=[p[1] for p in nb2]
    rx=ranks(x); ry=ranks(y); nn=len(nb2)
    mx=sum(rx)/nn; my=sum(ry)/nn
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(nn))
    dx=sqrt(sum((r-mx)**2 for r in rx))
    dy=sqrt(sum((r-my)**2 for r in ry))
    rho = num/(dx*dy) if dx*dy>0 else 0
    t_stat = rho*sqrt((nn-2)/(1-rho**2)) if abs(rho)<0.999 else float('inf')
    p_approx = 2*(1-0.5*(1+erf(abs(t_stat)/sqrt(2))))
    print(f"Spearman ρ(n_bars_contrarian, α_res) = {rho:+.4f}  t={t_stat:+.3f}  p={p_approx:.4f}  N={nn}")
