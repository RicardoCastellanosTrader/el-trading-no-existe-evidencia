# -*- coding: utf-8 -*-
"""
Exp#2 v3 FINAL — BARRIDO 45 + robustez (una-a-la-vez) + 6 placebo + per-cluster.
Detector congelado ob_detector_v3 (gatillo en-zona + bloque más-profundo + entrada borde-lejano
+ cancel_zona + TP-cruce). Veredicto = BRECHA real-vs-placebo.
"""
import sys, os, time, traceback
import numpy as np, pandas as pd
ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT); os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626"))
import regime_walk_forward as rwf, mean_reversion_features as mrf, ob_detector_v3 as ob

OUT = os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626")
# robustez una-a-la-vez sobre primario (near=0.05, frac=0.75, P=10)
CONFIGS = [(0.05, 0.75, 10), (0.03, 0.75, 10), (0.07, 0.75, 10),
           (0.05, 0.90, 10), (0.05, 1.00, 10), (0.05, 0.75, 30), (0.05, 0.75, 50)]
PRIMARY = (0.05, 0.75, 10)
PLACEBO = ["PLBGB1", "PLBSH1", "PLBGB2", "PLBSH2", "PLBGB3", "PLBSH3"]


def zones(df, sym):
    cp = 'data_cache/' + sym.replace('/', '') + '_mean_reversion.npz'
    if os.path.exists(cp): os.remove(cp)
    d = mrf.precalculate_mean_reversion(sym, df)
    if os.path.exists(cp): os.remove(cp)
    return d


def arrs(df):
    return [df[x].values.astype(float) for x in ['open', 'high', 'low', 'close']]


def run_one(o, h, l, c, d, tsms, near, frac, P):
    ob.P_PIVOT = P
    return ob.detect_ob_v3(o, h, l, c, d['zone_bull_forming'], d['zone_bull_resolved'],
                           d['zone_bear_forming'], d['zone_bear_resolved'], tsms,
                           near_pct=near, entry_frac=frac)


def boot_ci(tr, w, gp, gl):
    b = rwf._bootstrap_pf_fwd_vectorized(np.array([tr]), np.array([w]), np.array([gp]), np.array([gl]))
    return float(b['pf_fwd_ci_low'][0]), float(b['pf_fwd_ci_high'][0])


def run_real():
    rows = []; t0 = time.time()
    for si, sym in enumerate(rwf.SYMBOLS):
        try:
            df = rwf.load_full_history(sym); model = rwf.load_regime_model(sym)
            if df is None or model is None:
                print(f"[SKIP] {sym}"); continue
            o, h, l, c = arrs(df); tsms = (pd.to_datetime(df['timestamp']).astype('int64') // 10**6).values
            d = zones(df, sym)
            cl, ncl = rwf.compute_cluster_labels(df, model)
            eps = rwf.identify_episodes(cl, ncl, min_bars=rwf.MIN_EPISODE_BARS)
            reg, ndob, split = rwf.build_regime_labels(cl, eps, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
            valid = [k for k in range(ncl) if split[k]['valid']]
            if not valid:
                print(f"[SKIP] {sym}: sin clusters"); continue
            for (near, frac, P) in CONFIGS:
                tr = run_one(o, h, l, c, d, tsms, near, frac, P)
                allp = [x['pnl'] for x in tr]
                fwd = []; per = {k: [] for k in valid}
                for x in tr:
                    le = reg[x['entry_bar']] if 0 <= x['entry_bar'] < len(reg) else -1
                    if le < 0: continue
                    if le >= ncl and (le - ncl) in per:
                        fwd.append(x['pnl']); per[le - ncl].append(x['pnl'])
                pf_all, _, _ = ob.pf_from_pnls(allp)
                pf_f, gpf, glf = ob.pf_from_pnls(fwd)
                trf = len(fwd); wf = int((np.array(fwd) > 0).sum()) if fwd else 0
                cil, cih = boot_ci(trf, wf, gpf, glf)
                row = dict(symbol=rwf.sym_key(sym), near=near, frac=frac, P=P,
                           pf_all=round(pf_all, 4), trades_all=len(allp),
                           pf_fwd=round(pf_f, 4), ci_low=round(cil, 4), ci_high=round(cih, 4),
                           trades_fwd=trf, wins_fwd=wf)
                for k in range(3):
                    if k in valid:
                        pk, _, _ = ob.pf_from_pnls(per[k]); row[f'pf_fwd_c{k}'] = round(pk, 4); row[f'n_c{k}'] = len(per[k])
                    else:
                        row[f'pf_fwd_c{k}'] = np.nan; row[f'n_c{k}'] = 0
                rows.append(row)
            print(f"[{si+1}/45] {rwf.sym_key(sym):8s} | {len(rows)} rows | {(time.time()-t0)/60:.1f}min", flush=True)
        except Exception as e:
            print(f"[ERR] {sym}: {e}"); traceback.print_exc()
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "results_obv3_real.csv"), index=False)
    print(f"[SAVED] results_obv3_real.csv ({len(rows)})")


def run_placebo():
    rows = []
    for series in PLACEBO:
        df = rwf.load_full_history(series + "/USDT")
        if df is None: continue
        o, h, l, c = arrs(df); tsms = (pd.to_datetime(df['timestamp']).astype('int64') // 10**6).values
        d = zones(df, series + "/USDT")
        for (near, frac, P) in CONFIGS:
            tr = run_one(o, h, l, c, d, tsms, near, frac, P)
            pn = [x['pnl'] for x in tr]; pf, gp, gl = ob.pf_from_pnls(pn)
            t_, w_ = len(pn), int((np.array(pn) > 0).sum()) if pn else 0
            cil, cih = boot_ci(t_, w_, gp, gl)
            rows.append(dict(series=series, kind="GBM" if "GB" in series else "SHUF", near=near, frac=frac, P=P,
                             pf_all=round(pf, 4), ci_low=round(cil, 4), ci_high=round(cih, 4), trades_all=t_))
        print(f"[placebo] {series} done", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "results_obv3_placebo.csv"), index=False)
    print(f"[SAVED] results_obv3_placebo.csv ({len(rows)})")


if __name__ == "__main__":
    print(f"===== EXP#2 v3 BARRIDO (7 configs robustez, primario {PRIMARY}) =====")
    t0 = time.time(); run_placebo(); run_real()
    print(f"[DONE] {(time.time()-t0)/60:.1f} min")
