#!/usr/bin/env python3
"""B3 — TSMOM diario largo/flat, params CONGELADOS. Datos data_cache 1h -> diario."""
import json, glob, os
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
np.seterr(all="ignore")

SYMS = ("AAVE ADA ALGO APT ARB ATOM AVAX BCH BNB BTC DOGE DOT ENA ETC ETH FET FIL GRT HBAR ICP "
        "IMX INJ LINK LTC MANA NEAR ONDO OP POL QNT RENDER SAND SEI SHIB SOL STX SUI THETA TAO "
        "TRX UNI VET WLD XLM XRP").split()

L = 56          # lookback dias (8 sem) PRIMARIO
REBAL = 5       # semanal
VOL_BARS = 28
FEE_SIDE = 0.0010
WARMUP = L + VOL_BARS
DPY = 365

def load_daily():
    closes = {}
    for s in SYMS:
        for cand in ([f"{s}USDT"] if s not in ("POL","RENDER","SHIB") else
                     {"POL":["POLUSDT","MATICUSDT"],"RENDER":["RENDERUSDT","RNDRUSDT"],"SHIB":["1000SHIBUSDT","SHIBUSDT"]}[s]):
            p = ROOT / "data_cache" / f"{cand}_1h.parquet"
            if p.exists():
                d = pd.read_parquet(p)
                d["ts"] = pd.to_datetime(d["timestamp_ms"], unit="ms", utc=True)
                dc = d.set_index("ts")["close"].resample("1D").last()
                closes[s] = dc
                break
    C = pd.DataFrame(closes).sort_index()
    return C

def sharpe(ret):
    ret = pd.Series(ret).dropna()
    if len(ret) < 2 or ret.std() == 0: return None
    return float(ret.mean()/ret.std()*np.sqrt(DPY))

def maxdd(ret):
    eq = (1+pd.Series(ret).dropna()).cumprod()
    return float((eq/eq.cummax()-1).min()*100)

def block_ci(ret, block=5, n=5000, seed=20260702):
    r = pd.Series(ret).dropna().values; T=len(r)
    if T < block+2: return None,None
    rng=np.random.default_rng(seed); nb=int(np.ceil(T/block)); starts=np.arange(0,T-block+1); sh=np.empty(n)
    for k in range(n):
        st=rng.choice(starts,size=nb); idx=(st[:,None]+np.arange(block)[None,:]).ravel()[:T]; s=r[idx]
        sh[k]=(s.mean()/s.std()*np.sqrt(DPY)) if s.std()>0 else 0.0
    return float(np.percentile(sh,2.5)), float(np.percentile(sh,97.5))

C = load_daily()
print(f"panel diario: {C.shape[1]} sym x {C.shape[0]} dias  ({C.index.min().date()} -> {C.index.max().date()})")
rets = C.pct_change()
fwd = rets.shift(-1)
trail = C / C.shift(L) - 1.0
vol = rets.rolling(VOL_BARS, min_periods=VOL_BARS//2).std()
invv = 1.0 / vol
cols = C.columns
n = len(C.index)
w = pd.DataFrame(0.0, index=C.index, columns=cols)
last = pd.Series(0.0, index=cols)
cost = pd.Series(0.0, index=C.index)
rebal = set(range(WARMUP, n, REBAL))
for i in range(n):
    if i in rebal:
        sig = (trail.iloc[i] > 0)                       # largo/flat
        longs = [s for s in cols if sig.get(s, False) and not pd.isna(invv.iloc[i][s])]
        wt = pd.Series(0.0, index=cols)
        if longs:
            iv = invv.iloc[i].reindex(longs).replace([np.inf,-np.inf],np.nan).dropna()
            if len(iv) and iv.sum()>0:
                wt.loc[iv.index] = (iv/iv.sum()).values
        d = (wt-last).abs()
        cost.iloc[i] = float((d*FEE_SIDE).sum())
        last = wt
    w.iloc[i] = last.values
tsmom = (w*fwd).sum(axis=1) - cost
# EW buy&hold point-in-time
ew = rets.mean(axis=1, skipna=True)

def sub(ret, tag):
    r = pd.Series(ret)
    return {"sharpe": sharpe(r), "maxdd_pct": round(maxdd(r),2),
            "ret_total_pct": round(float((1+r.dropna()).prod()-1)*100,1)}

res = {"params":{"L":L,"rebal":REBAL,"window":f"{C.index.min().date()}->{C.index.max().date()}","n_dias":n},
       "TSMOM_full": sub(tsmom,"ts"), "EW_bh_full": sub(ew,"ew")}
lo,hi = block_ci(tsmom); res["TSMOM_sharpe_CI"]=[round(lo,3) if lo else None, round(hi,3) if hi else None]
res["TSMOM_turnover_medio"]= round(float(cost[cost>0].mean()/FEE_SIDE),3) if (cost>0).any() else None
for y in (2022,2023,2024,2025):
    m = tsmom.index.year==y
    res[f"TSMOM_{y}"]={"sharpe":sharpe(tsmom[m])}; res[f"EW_{y}"]={"sharpe":sharpe(ew[m])}

sh_ts=res["TSMOM_full"]["sharpe"]; sh_ew=res["EW_bh_full"]["sharpe"]
dd_ts=res["TSMOM_full"]["maxdd_pct"]; dd_ew=res["EW_bh_full"]["maxdd_pct"]
c1= sh_ts is not None and sh_ts>=1.0
c2= sh_ts is not None and sh_ew is not None and sh_ts>sh_ew
c3= dd_ts is not None and dd_ew is not None and dd_ts>dd_ew
c4= lo is not None and lo>0
res["criterios"]={"sharpe>=1":c1,"bate_EW_sharpe":c2,"mejor_maxDD":c3,"CI_excluye_0":c4}
res["VEREDICTO"]="DIGNA" if (c1 and c2 and c3 and c4) else "NO DIGNA"
res["sharpe_diff_TSMOM_menos_EW"]=round(sh_ts-sh_ew,3) if (sh_ts and sh_ew) else None
(HERE/"results_B3.json").write_text(json.dumps(res,indent=2,default=str))
print(json.dumps(res,indent=2,default=str))
