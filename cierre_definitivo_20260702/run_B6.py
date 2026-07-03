#!/usr/bin/env python3
"""B6 — Estacionalidad reloj/funding-clock. FDR-BH pre-registrado. data_cache 1h."""
import json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
np.seterr(all="ignore")
SYMS = ("AAVE ADA ALGO APT ARB ATOM AVAX BCH BNB BTC DOGE DOT ENA ETC ETH FET FIL GRT HBAR ICP "
        "IMX INJ LINK LTC MANA NEAR ONDO OP POL QNT RENDER SAND SEI SOL STX SUI THETA TAO "
        "TRX UNI VET WLD XLM XRP").split()
BLOCK=24; NBOOT=2000; SEED=20260702; QFDR=0.10; MAG_MIN_BPS=10.0

def load_ret(s):
    for cand in ([f"{s}USDT"] if s not in ("POL","RENDER","SHIB") else
                 {"POL":["POLUSDT","MATICUSDT"],"RENDER":["RENDERUSDT","RNDRUSDT"],"SHIB":["1000SHIBUSDT"]}[s]):
        p=ROOT/"data_cache"/f"{cand}_1h.parquet"
        if p.exists():
            d=pd.read_parquet(p); d["ts"]=pd.to_datetime(d["timestamp_ms"],unit="ms",utc=True)
            return d.set_index("ts")["close"].pct_change()
    return None
R = pd.DataFrame({s:load_ret(s) for s in SYMS})
R = R.dropna(how="all")
ew = R.mean(axis=1, skipna=True)                 # retorno pooled cross-simbolo por hora
ew = ew.dropna()
hod = ew.index.hour; dow = ew.index.dayofweek
print(f"ew hourly {len(ew)} h | {R.shape[1]} sym | {ew.index.min().date()}->{ew.index.max().date()}")

# buckets declarados
buckets = {}
for h in range(24): buckets[f"hour_{h:02d}"] = (hod==h)
for d in range(7): buckets[f"dow_{d}"] = (dow==d)          # 0=lunes
for h in (0,8,16): buckets[f"fund_{h:02d}"] = (hod==h)
for h in (23,7,15): buckets[f"prefund_{h:02d}"] = (hod==h)

vals = ew.values; T=len(vals)
rng=np.random.default_rng(SEED); nb=int(np.ceil(T/BLOCK)); starts=np.arange(0,T-BLOCK+1)
# precompute bootstrap index sets once (compartidos entre buckets)
boot_idx = [ (lambda st: (st[:,None]+np.arange(BLOCK)[None,:]).ravel()[:T])(rng.choice(starts,size=nb)) for _ in range(NBOOT) ]
res={"params":{"block":BLOCK,"nboot":NBOOT,"q_fdr":QFDR,"mag_min_bps":MAG_MIN_BPS,
     "ventana":f"{ew.index.min().date()}->{ew.index.max().date()}","n_buckets":len(buckets)},"buckets":{}}
pv={}
for name,mask in buckets.items():
    m = mask
    obs = float(vals[m].mean())*1e4   # bps
    bs = np.empty(NBOOT)
    hb = hod  # hour labels
    for b,ix in enumerate(boot_idx):
        vv=vals[ix]; mm=m[ix]
        bs[b]= vv[mm].mean()*1e4 if mm.any() else 0.0
    lo,hi=np.percentile(bs,2.5),np.percentile(bs,97.5)
    fp=np.mean(bs>0); p=2*min(fp,1-fp)
    pv[name]=p
    res["buckets"][name]={"mean_bps":round(obs,3),"CI_bps":[round(lo,3),round(hi,3)],"p":round(p,4)}
items=sorted(pv.items(),key=lambda kv:kv[1]); m=len(items); sig={}
for rank,(k,p) in enumerate(items,1): sig[k]= p <= (rank/m)*QFDR
tradeable=[]; real_not=[]
for name in buckets:
    s=bool(sig[name]); mag=abs(res["buckets"][name]["mean_bps"])>=MAG_MIN_BPS
    res["buckets"][name]["fdr_sig"]=s; res["buckets"][name]["tradeable"]=bool(s and mag)
    if s and mag: tradeable.append(name)
    elif s: real_not.append(name)
res["fdr_significativos"]=[k for k in buckets if sig[k]]
res["VEREDICTO"]=("SENAL TRADEABLE: "+",".join(tradeable)) if tradeable else \
    ("EFECTO REAL NO TRADEABLE (solo timing ejecucion): "+",".join(real_not)) if real_not else \
    "CERRADO (ningun bucket sobrevive FDR)"
(HERE/"results_B6.json").write_text(json.dumps(res,indent=2,default=str))
print("FDR-significativos:",res["fdr_significativos"])
print("max |mean_bps|:",round(max(abs(res['buckets'][k]['mean_bps']) for k in buckets),2))
print("VEREDICTO:",res["VEREDICTO"])
