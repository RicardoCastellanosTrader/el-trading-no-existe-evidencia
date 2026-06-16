"""Nivel 3 — selección de subset (cobertura de régimen) + frescura exacta. READ-ONLY, sin GPU.
No toca live/* ni el kernel. Solo clasifica barras con la GMM productiva (CPU) y mapea ventanas."""
import os, sys, glob, json
import numpy as np, pandas as pd, joblib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "live"))
from regime_features import compute_regime_features

# ventanas (mismas que α: opt5000/ext2000/fwd2000/step2000/warmup500)
OPT, EXT, FWD, STEP, WARM = 5000, 2000, 2000, 2000, 500
DEPLOYED = {"BNB","BTC","ETH","TRX","XRP","ONDO","RENDER","POL","SEI","TAO",
            "SOL","ADA","BCH","LINK","DOGE","LTC","XLM","ETC","VET","FET"}
E2FULL = {"BTC","SOL","LINK","LTC"}
# categorías DIAG (memory): extr.bajo, medio; resto amplio
EXTR_BAJO = {"ONDO","POL","RENDER"}
MEDIO = {"SEI","TAO","APT","ENA","WLD","ARB","SUI","INJ","FET","OP","STX","IMX"}
def categoria(s): return "extr.bajo" if s in EXTR_BAJO else ("medio" if s in MEDIO else "amplio")

MS_2025_10_01 = pd.Timestamp("2025-10-01", tz="UTC").value // 10**6
MS_2026_05_17 = pd.Timestamp("2026-05-17", tz="UTC").value // 10**6
MS_NOW        = pd.Timestamp("2026-06-16", tz="UTC").value // 10**6

def cluster_counts(sym, df):
    gp = os.path.join(ROOT, "regime_models", f"{sym}_regime.joblib")
    if not os.path.exists(gp): return None, None
    m = joblib.load(gp)
    feats, valid = compute_regime_features(df, lookback=m['lookback'])
    lab = np.full(len(df), -1, dtype=int)
    iv = np.where(valid)[0]
    if len(iv):
        Xs = m['scaler'].transform(feats[valid])
        lab[iv] = m['gmm'].predict_proba(Xs).argmax(axis=1)
    n = m.get('n_clusters', 3)
    counts = [int((lab==k).sum()) for k in range(n)]
    return counts, m

def cluster_names(sym):
    p = os.path.join(ROOT, "regime_wf", f"{sym}USDT_specialist_configs.json")
    if not os.path.exists(p): return {}
    d = json.load(open(p, encoding="utf-8"))
    return {int(k): c.get("name","?") for k,c in d.get("clusters",{}).items()}

def fresh_anchors(sym, ts):
    """Cuenta anclajes cuya ventana fwd NO intersecta holdouts quemados (frescura exacta)."""
    n = len(ts)
    burned = []
    if sym in E2FULL: burned.append((MS_2025_10_01, MS_2026_05_17))
    if sym in DEPLOYED: burned.append((MS_2026_05_17, MS_NOW))
    total = fresh = 0; fresh_spans=[]
    idx = 0
    while True:
        fwd_end_i = n - idx*STEP
        fwd_start_i = fwd_end_i - FWD
        needed = fwd_start_i - OPT - EXT - WARM
        if needed < 0: break
        total += 1
        fs, fe = int(ts[fwd_start_i]), int(ts[fwd_end_i-1])
        clash = any(not (fe < b0 or fs >= b1) for (b0,b1) in burned)
        if not clash:
            fresh += 1
            if len(fresh_spans) < 3 or idx >= 0:
                fresh_spans.append((str(pd.Timestamp(fs,unit='ms'))[:10], str(pd.Timestamp(fe,unit='ms'))[:10]))
        idx += 1
    return total, fresh, fresh_spans

def main():
    rows=[]
    for p in sorted(glob.glob(os.path.join(ROOT,"data_cache","*USDT_1h.parquet"))):
        sym = os.path.basename(p).replace("USDT_1h.parquet","")
        df = pd.read_parquet(p)
        if "timestamp_ms" not in df.columns or len(df) < (OPT+EXT+FWD+WARM):
            continue
        df = df.rename(columns=str.lower)
        ts = df["timestamp_ms"].values
        counts, m = cluster_counts(sym, df)
        if counts is None: continue
        tot, fr, spans = fresh_anchors(sym, ts)
        names = cluster_names(sym)
        rows.append(dict(sym=sym, n=len(df),
                         first=str(pd.Timestamp(int(ts[0]),unit='ms'))[:10],
                         last=str(pd.Timestamp(int(ts[-1]),unit='ms'))[:10],
                         cat=categoria(sym), deployed=sym in DEPLOYED,
                         counts=counts, names=names, anchors=tot, fresh=fr))
    # min cluster fraction (cobertura régimen)
    for r in rows:
        tot=sum(r["counts"]); r["minfrac"]=min(r["counts"])/tot if tot else 0
    rows.sort(key=lambda r:-r["fresh"])
    print(f"{'sym':<7}{'cat':<10}{'dep':<4}{'n_bars':>7}{'first':>12}{'last':>12}{'anch':>5}{'fresh':>6}{'minClu%':>8}  clusters(bars)")
    for r in rows:
        c=r["counts"]; mf=r["minfrac"]*100
        print(f"{r['sym']:<7}{r['cat']:<10}{('Y' if r['deployed'] else '-'):<4}{r['n']:>7}{r['first']:>12}{r['last']:>12}{r['anchors']:>5}{r['fresh']:>6}{mf:>7.1f}%  {c}")
    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"nivel3_subset_freshness.json"),"w"), indent=1, default=str)
    print("\nguardado nivel3_subset_freshness.json")

if __name__=="__main__": main()
