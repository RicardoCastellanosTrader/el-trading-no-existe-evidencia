#!/usr/bin/env python3
"""C1 — N2 con potencia real: extender bloque2c de 60/9 a ~300/>=20 sym con CI.
Replica la metodologia smoke_c (doubled labels + split cronologico 67/33) pero sobre
>=20 sym (data_cache Binance 1h full history) x top1/mid/tail configs de los JSONs regime_wf.
CAVEAT (Tier-3, decision de diseno no pre-especificada): data_cache = mismos bars Binance que
la seleccion, con split CRONOLOGICO (!= split por episodios de produccion) -> testea la
ROBUSTEZ-AL-SPLIT de la persistencia pf_tr->pf_fwd (aproxima N2), NO es fully out-of-sample.
Decide: colapso total vs transferencia parcial de pf_tr, con CI symbol-clustered."""
import sys, os, re, json, glob, time
import numpy as np, pandas as pd, joblib
ROOT = r"c:\Users\rixip\combolab"; sys.path.insert(0, ROOT); os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "live"))
from brain_engine import (load_models, _normalize_ohlcv, _load_preset_tuple,
    COOLDOWN_BARS, SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT, COMMISSION_ROUND_TRIP)
from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice
from regime_features import compute_regime_features
from scipy.stats import spearmanr

TRAIN_FRAC = 2/3; NC = 3; GMM_DIR = os.path.join(ROOT, "regime_models"); WF = os.path.join(ROOT, "regime_wf")
SYMS = ("BTC ETH BNB XRP ADA SOL DOGE DOT LTC LINK BCH ATOM AVAX APT ARB OP NEAR FIL INJ SEI "
        "GRT MANA SAND ONDO STX IMX THETA").split()   # 27 candidatos

def doubled(df_p, sym):
    m = joblib.load(os.path.join(GMM_DIR, f"{sym}_regime.joblib"))
    feats, valid = compute_regime_features(df_p, lookback=m['lookback'])
    lab = np.zeros(len(df_p), dtype=np.int64); iv = np.where(valid)[0]
    if len(iv): lab[iv] = m['gmm'].predict_proba(m['scaler'].transform(feats[valid])).argmax(axis=1)
    split = int(len(df_p)*TRAIN_FRAC); d = lab.copy(); d[split:] += NC
    return d, split

def replay(sym, cl, cfg_id, preset):
    parq = os.path.join(ROOT, "data_cache", f"{sym}USDT_1h.parquet")
    df_p = _normalize_ohlcv(pd.read_parquet(parq)); n = len(df_p)
    brain = load_models(GMM_DIR, WF, [f"{sym}/USDT"])
    pt = brain.preset_tuples.get(preset)
    if pt is None: pt, _ = _load_preset_tuple(f"{sym}/USDT", preset)
    hm = re.search(r"_H(\d+)$", preset); hyst = int(hm.group(1))/10.0 if hm else 0.0
    dl, split = doubled(df_p, sym)
    data = precalculate_all_data(df_p, preset=pt, hyst_mult=hyst, symbol=f"{sym}/USDT")
    res, cl_pnl, cl_tr, cl_w, cl_dd, cl_gp, cl_gl = run_on_slice(
        np.array([cfg_id], dtype=np.uint32), data, start_bar=0, end_bar=n,
        sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT, ts_pct=TS_PERCENT,
        cooldown_bars=COOLDOWN_BARS, commission_pct=COMMISSION_ROUND_TRIP, warmup=100,
        cluster_labels=dl, n_clusters=NC*2)
    kt, kf = cl, cl+NC
    gp_t, gl_t = float(cl_gp[0,kt]), float(cl_gl[0,kt]); gp_f, gl_f = float(cl_gp[0,kf]), float(cl_gl[0,kf])
    pf_t = (gp_t/gl_t) if gl_t>0 else (np.inf if gp_t>0 else 0.0)
    pf_f = (gp_f/gl_f) if gl_f>0 else (np.inf if gp_f>0 else 0.0)
    return pf_t, int(cl_tr[0,kt]), pf_f, int(cl_tr[0,kf])

rows = []; t0 = time.time()
for si, sym in enumerate(SYMS):
    if not os.path.exists(os.path.join(ROOT,"data_cache",f"{sym}USDT_1h.parquet")): continue
    if not os.path.exists(os.path.join(GMM_DIR,f"{sym}_regime.joblib")): continue
    jf = os.path.join(WF, f"{sym}USDT_specialist_configs.json")
    if not os.path.exists(jf): continue
    J = json.load(open(jf)); cl_dict = J.get("clusters", {})
    for k, cinfo in cl_dict.items():
        tc = cinfo.get("top_configs", [])
        if len(tc) < 3: continue
        picks = [("top1", tc[0]), ("mid", tc[len(tc)//2]), ("tail", tc[-1])]
        for rank, cfg in picks:
            try:
                pf_t, n_t, pf_f, n_f = replay(sym, int(k), int(cfg["config_id"]), cfg["preset"])
                rows.append(dict(symbol=sym, cluster=int(k), rank=rank, config_id=cfg["config_id"],
                                 pf_tr=pf_t, n_tr=n_t, pf_fwd=pf_f, n_fwd=n_f, pf_json=cfg.get("pf_combined")))
            except Exception as e:
                print(f"[err] {sym} c{k} {rank}: {e}", flush=True)
    print(f"[{si+1}] {sym} rows={len(rows)} {(time.time()-t0)/60:.1f}min", flush=True)

df = pd.DataFrame(rows)
# limpiar inf/0 para spearman
d = df[np.isfinite(df.pf_tr) & np.isfinite(df.pf_fwd) & (df.n_tr>0) & (df.n_fwd>0)].copy()
rho = spearmanr(d.pf_tr, d.pf_fwd).correlation
syms = d.symbol.unique(); rng = np.random.default_rng(20260702); boot = []
for _ in range(10000):
    pick = rng.choice(syms, size=len(syms), replace=True)
    sub = pd.concat([d[d.symbol==s] for s in pick])
    if sub.pf_tr.nunique() > 2:
        r = spearmanr(sub.pf_tr, sub.pf_fwd).correlation
        if not np.isnan(r): boot.append(r)
lo, hi = np.percentile(boot, [2.5, 97.5])
out = {"n_configs": len(d), "n_symbols": int(d.symbol.nunique()),
       "spearman_pf_tr_vs_pf_fwd": round(float(rho), 4),
       "CI95_symbol_clustered": [round(float(lo),3), round(float(hi),3)],
       "incluye_+0.297_enslice": bool(lo <= 0.297 <= hi), "incluye_0": bool(lo <= 0 <= hi),
       "caveat": "data_cache mismos bars que seleccion, split cronologico 67/33 (!= episodios prod) -> robustez-al-split, no fully OOS"}
df.to_csv(os.path.join(ROOT,"cierre_definitivo_20260702","results_C1_extend.csv"), index=False)
open(os.path.join(ROOT,"cierre_definitivo_20260702","results_C1.json"),"w").write(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
