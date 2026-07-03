#!/usr/bin/env python3
"""C3 — Exp#2 ablacion: deepest (original) vs shallowest vs random-en-banda.
Aisla la regla causal 'bloque mas profundo = pool de liquidez mayor', preservando
tendencias/vol/colas reales (mismo detector, misma banda, solo cambia el pick).
Config primaria (0.05,0.75,10), 45 sym. Reusa el pipeline del barrido congelado."""
import sys, os, json, time
import numpy as np, pandas as pd
ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT); os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626"))
import regime_walk_forward as rwf, mean_reversion_features as mrf, ob_detector_v3 as ob

NEAR, FRAC, P = 0.05, 0.75, 10
RNG = np.random.default_rng(20260702)
_orig_find = ob._find_block

def _find_block_mode(mode):
    def fb(t, side, l, h, c, is_low, is_high, near_pct, out_thresh, scan_cap):
        ct = c[t]; PP = ob.P_PIVOT; cands = []
        if side == +1:
            run = l[t]
            for j in range(t - PP - 1, max(PP, t - scan_cap) - 1, -1):
                if l[j] < run:
                    run = l[j]
                    if not is_low[j]: continue
                    L = l[j]
                    if L > ct: continue
                    if (ct - L) / ct > near_pct: break
                    cl = c[j + 1:t]
                    if len(cl) and np.mean((cl < L * 0.95) | (cl > L * 1.05)) >= out_thresh:
                        cands.append((j, L))
            if not cands: return -1
            if mode == "deepest":   return min(cands, key=lambda x: x[1])[0]
            if mode == "shallowest":return max(cands, key=lambda x: x[1])[0]
            return cands[int(RNG.integers(len(cands)))][0]
        else:
            run = h[t]
            for j in range(t - PP - 1, max(PP, t - scan_cap) - 1, -1):
                if h[j] > run:
                    run = h[j]
                    if not is_high[j]: continue
                    L = h[j]
                    if L < ct: continue
                    if (L - ct) / ct > near_pct: break
                    cl = c[j + 1:t]
                    if len(cl) and np.mean((cl < L * 0.95) | (cl > L * 1.05)) >= out_thresh:
                        cands.append((j, L))
            if not cands: return -1
            if mode == "deepest":   return max(cands, key=lambda x: x[1])[0]
            if mode == "shallowest":return min(cands, key=lambda x: x[1])[0]
            return cands[int(RNG.integers(len(cands)))][0]
    return fb

def arrs(df): return [df[x].values.astype(float) for x in ['open','high','low','close']]
def zones(df, sym):
    cp = 'data_cache/'+sym.replace('/','')+'_mean_reversion.npz'
    if os.path.exists(cp): os.remove(cp)
    d = mrf.precalculate_mean_reversion(sym, df)
    if os.path.exists(cp): os.remove(cp)
    return d

modes = ["deepest", "shallowest", "random"]
acc = {m: {"pf_all": [], "pf_fwd": []} for m in modes}
t0 = time.time()
for si, sym in enumerate(rwf.SYMBOLS):
    try:
        df = rwf.load_full_history(sym); model = rwf.load_regime_model(sym)
        if df is None or model is None: continue
        o, h, l, c = arrs(df); tsms = (pd.to_datetime(df['timestamp']).astype('int64')//10**6).values
        d = zones(df, sym)
        cl, ncl = rwf.compute_cluster_labels(df, model)
        eps = rwf.identify_episodes(cl, ncl, min_bars=rwf.MIN_EPISODE_BARS)
        reg, ndob, split = rwf.build_regime_labels(cl, eps, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
        valid = [k for k in range(ncl) if split[k]['valid']]
        if not valid: continue
        ob.P_PIVOT = P
        for m in modes:
            ob._find_block = _find_block_mode(m)
            tr = ob.detect_ob_v3(o, h, l, c, d['zone_bull_forming'], d['zone_bull_resolved'],
                                 d['zone_bear_forming'], d['zone_bear_resolved'], tsms,
                                 near_pct=NEAR, entry_frac=FRAC)
            allp = [x['pnl'] for x in tr]
            fwd = []
            for x in tr:
                le = reg[x['entry_bar']] if 0 <= x['entry_bar'] < len(reg) else -1
                if le < 0: continue
                if le >= ncl and (le - ncl) in valid: fwd.append(x['pnl'])
            pf_all,_,_ = ob.pf_from_pnls(allp)
            pf_f,_,_ = ob.pf_from_pnls(fwd)
            acc[m]["pf_all"].append(pf_all); acc[m]["pf_fwd"].append(pf_f)
        print(f"[{si+1}/45] {rwf.sym_key(sym):8s} {(time.time()-t0)/60:.1f}min", flush=True)
    except Exception as e:
        print(f"[ERR] {sym}: {e}", flush=True)
ob._find_block = _orig_find

res = {"config_primaria": [NEAR, FRAC, P]}
for m in modes:
    a = np.array(acc[m]["pf_all"]); f = np.array(acc[m]["pf_fwd"])
    res[m] = {"n_sym": len(a), "pf_all_median": round(float(np.median(a)),4),
              "pf_fwd_median": round(float(np.median(f)),4),
              "pf_all_mean": round(float(np.mean(a)),4)}
# floor placebo primario (referencia)
try:
    pl = pd.read_csv(os.path.join(ROOT,"analysis_scripts","atribucion_componentes_20260626","results_obv3_placebo.csv"))
    plp = pl[(pl.near==NEAR)&(pl.frac==FRAC)&(pl.P==P)]
    res["placebo_floor_pf_all_median"] = round(float(plp.pf_all.median()),4)
except Exception as e:
    res["placebo_floor_pf_all_median"] = None
d_dp = res["deepest"]["pf_all_median"]; d_sh = res["shallowest"]["pf_all_median"]; d_rn = res["random"]["pf_all_median"]
res["VEREDICTO"] = ("REGLA CAUSAL SIN SEÑAL (deepest ~ shallowest ~ random -> geometria de banda, no profundidad-liquidez)"
                    if (abs(d_dp-d_sh) < 0.10 and abs(d_dp-d_rn) < 0.10)
                    else "deepest se separa de shallowest/random -> la profundidad porta algo")
open(os.path.join(ROOT,"cierre_definitivo_20260702","results_C3.json"),"w").write(json.dumps(res,indent=2))
print(json.dumps(res, indent=2))
