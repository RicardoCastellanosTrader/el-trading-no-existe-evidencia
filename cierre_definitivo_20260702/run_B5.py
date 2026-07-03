#!/usr/bin/env python3
"""B5 — Lead-lag BTC->alts horario. Params CONGELADOS. data_cache 1h."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
np.seterr(all="ignore")
SYMS = ("AAVE ADA ALGO APT ARB ATOM AVAX BCH BNB DOGE DOT ENA ETC ETH FET FIL GRT HBAR ICP "
        "IMX INJ LINK LTC MANA NEAR ONDO OP POL QNT RENDER SAND SEI SOL STX SUI THETA TAO "
        "TRX UNI VET WLD XLM XRP").split()   # 44 alts (BTC aparte)
LAGS = [1, 2, 4, 8, 12]
BLOCK = 24; NBOOT = 1000; SEED = 20260702; QFDR = 0.10; MAG_MIN = 0.03

def load_ret(sym):
    for cand in ([f"{sym}USDT"] if sym not in ("POL","RENDER","SHIB") else
                 {"POL":["POLUSDT","MATICUSDT"],"RENDER":["RENDERUSDT","RNDRUSDT"],"SHIB":["1000SHIBUSDT"]}[sym]):
        p = ROOT/"data_cache"/f"{cand}_1h.parquet"
        if p.exists():
            d = pd.read_parquet(p); d["ts"]=pd.to_datetime(d["timestamp_ms"],unit="ms",utc=True)
            return d.set_index("ts")["close"].pct_change()
    return None

btc = load_ret("BTC")
alts = {s: load_ret(s) for s in SYMS}
alts = {s: r for s, r in alts.items() if r is not None}
idx = btc.index
A = pd.DataFrame(alts).reindex(idx)
x_full = btc.values
print(f"BTC {len(idx)} h | {A.shape[1]} alts | ventana {idx.min().date()}->{idx.max().date()}")

def mean_corr(xrows, Ymat):
    # corr de x contra cada columna de Ymat, promedio (ignora nan por columna)
    xs = xrows - np.nanmean(xrows)
    out = []
    for j in range(Ymat.shape[1]):
        y = Ymat[:, j]; m = ~(np.isnan(xs) | np.isnan(y))
        if m.sum() < 100: continue
        xc = xs[m] - xs[m].mean(); yc = y[m] - y[m].mean()
        den = np.sqrt((xc**2).sum()*(yc**2).sum())
        if den > 0: out.append(float((xc*yc).sum()/den))
    return float(np.mean(out)) if out else np.nan

rng = np.random.default_rng(SEED)
T = len(idx); nb = int(np.ceil(T/BLOCK)); starts = np.arange(0, T-BLOCK+1)
res = {"params":{"lags_h":LAGS,"block":BLOCK,"nboot":NBOOT,"q_fdr":QFDR,"mag_min":MAG_MIN,
       "ventana":f"{idx.min().date()}->{idx.max().date()}","n_alts":A.shape[1]},"por_lag":{}}
pvals = {}
for k in LAGS:
    Yk = A.shift(-k).values                       # alt_{t+k}
    obs = mean_corr(x_full, Yk)
    boot = np.empty(NBOOT)
    for b in range(NBOOT):
        st = rng.choice(starts, size=nb); ridx = (st[:,None]+np.arange(BLOCK)[None,:]).ravel()[:T]
        boot[b] = mean_corr(x_full[ridx], Yk[ridx])
    lo, hi = np.nanpercentile(boot,2.5), np.nanpercentile(boot,97.5)
    frac_pos = np.mean(boot > 0); p = 2*min(frac_pos, 1-frac_pos)
    pvals[k] = p
    res["por_lag"][f"k={k}h"] = {"mean_corr": round(obs,4), "CI":[round(lo,4),round(hi,4)],
                                 "p_boot": round(p,4), "excede_mag_min": abs(obs)>=MAG_MIN}
# FDR-BH sobre los 5 lags
items = sorted(pvals.items(), key=lambda kv: kv[1]); m = len(items); sig = {}
for rank,(k,p) in enumerate(items, start=1):
    sig[k] = p <= (rank/m)*QFDR
for k in LAGS:
    res["por_lag"][f"k={k}h"]["fdr_significativo"] = bool(sig[k])
    res["por_lag"][f"k={k}h"]["SENAL"] = bool(sig[k] and res["por_lag"][f"k={k}h"]["excede_mag_min"])
any_signal = any(res["por_lag"][f"k={k}h"]["SENAL"] for k in LAGS)
res["VEREDICTO"] = "SENAL (construir cartera)" if any_signal else "CERRADO (sin predictibilidad tradeable)"
(HERE/"results_B5.json").write_text(json.dumps(res,indent=2,default=str))
print(json.dumps(res,indent=2,default=str))
