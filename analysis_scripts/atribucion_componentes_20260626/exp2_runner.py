# -*- coding: utf-8 -*-
"""
Exp#2 ORDER BLOCK — RUNNER barrido completo: 45 sym x grid{k,W,R} + 6 placebo + per-cluster.
Veredicto = BRECHA real-vs-placebo (no PF absoluto). Reporta pf_all (geometrico) + pf_fwd (as-of).
Detector look-ahead-free (gate PASS). brain/kernel productivos INTACTOS.
"""
import sys, os, time, traceback
import numpy as np
import pandas as pd

ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626"))
import regime_walk_forward as rwf
import lab_historico_numba_v8_3 as lab
import ob_detector as ob

OUTDIR = os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626")
KS = [1.5, 2.0, 2.5]; WS = [30, 50, 80]; RS = [1.5, 2.0, 3.0]
PRIMARY = (2.0, 50, 2.0)
GRID = [(k, w, r) for k in KS for w in WS for r in RS]  # 27
PLACEBO = ["PLBGB1", "PLBSH1", "PLBGB2", "PLBSH2", "PLBGB3", "PLBSH3"]


def boot_ci(tr, w, gp, gl):
    b = rwf._bootstrap_pf_fwd_vectorized(np.array([tr]), np.array([w]), np.array([gp]), np.array([gl]))
    return float(b['pf_fwd_ci_low'][0]), float(b['pf_fwd_ci_high'][0])


def run_real():
    rows = []
    t0 = time.time()
    for si, sym in enumerate(rwf.SYMBOLS):
        try:
            df = rwf.load_full_history(sym); model = rwf.load_regime_model(sym)
            if df is None or model is None:
                print(f"[SKIP] {sym}"); continue
            o = df['open'].values.astype(float); h = df['high'].values.astype(float)
            l = df['low'].values.astype(float); c = df['close'].values.astype(float)
            atr = lab.calc_atr(h, l, c, lab.HYST_ATR_LEN)
            cl_labels, ncl = rwf.compute_cluster_labels(df, model)
            episodes = rwf.identify_episodes(cl_labels, ncl, min_bars=rwf.MIN_EPISODE_BARS)
            reg, ndob, split = rwf.build_regime_labels(cl_labels, episodes, ncl,
                                                       train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
            valid = [k for k in range(ncl) if split[k]['valid']]
            if not valid:
                print(f"[SKIP] {sym}: sin clusters validos"); continue
            for (k, W, R) in GRID:
                trades = ob.detect_order_block_trades(o, h, l, c, atr, k=k, W=W, R_mult=R)
                all_pnls = [x['pnl'] for x in trades]
                fwd, trn = [], []; per = {q: [] for q in valid}
                for x in trades:
                    le = reg[x['entry_bar']]
                    if le < 0: continue
                    if le >= ncl:
                        q = le - ncl
                        if q in per: fwd.append(x['pnl']); per[q].append(x['pnl'])
                    else:
                        trn.append(x['pnl'])
                pf_all, _, _ = ob.pf_from_pnls(all_pnls)
                pf_t, _, _ = ob.pf_from_pnls(trn)
                pf_f, gpf, glf = ob.pf_from_pnls(fwd)
                trf = len(fwd); wf = int((np.array(fwd) > 0).sum()) if fwd else 0
                cil, cih = boot_ci(trf, wf, gpf, glf)
                row = dict(symbol=rwf.sym_key(sym), k=k, W=W, R=R,
                           pf_all=round(pf_all, 4), trades_all=len(all_pnls),
                           pf_tr=round(pf_t, 4), pf_fwd=round(pf_f, 4),
                           ci_low=round(cil, 4), ci_high=round(cih, 4),
                           trades_fwd=trf, wins_fwd=wf)
                for q in range(3):
                    if q in valid:
                        pq, _, _ = ob.pf_from_pnls(per[q])
                        row[f'pf_fwd_c{q}'] = round(pq, 4); row[f'trades_fwd_c{q}'] = len(per[q])
                    else:
                        row[f'pf_fwd_c{q}'] = np.nan; row[f'trades_fwd_c{q}'] = 0
                rows.append(row)
            print(f"[{si+1}/45] {rwf.sym_key(sym):8s} done | {len(rows)} rows | {(time.time()-t0)/60:.1f}min", flush=True)
        except Exception as e:
            print(f"[ERR] {sym}: {e}"); traceback.print_exc()
    pd.DataFrame(rows).to_csv(os.path.join(OUTDIR, "results_ob_real.csv"), index=False)
    print(f"[SAVED] results_ob_real.csv ({len(rows)} rows)")


def run_placebo():
    rows = []
    for series in PLACEBO:
        df = rwf.load_full_history(series + "/USDT")
        if df is None:
            print(f"[SKIP placebo] {series}"); continue
        o = df['open'].values.astype(float); h = df['high'].values.astype(float)
        l = df['low'].values.astype(float); c = df['close'].values.astype(float)
        atr = lab.calc_atr(h, l, c, lab.HYST_ATR_LEN)
        for (k, W, R) in GRID:
            trades = ob.detect_order_block_trades(o, h, l, c, atr, k=k, W=W, R_mult=R)
            pnls = [x['pnl'] for x in trades]
            pf, gp, gl = ob.pf_from_pnls(pnls)
            tr = len(pnls); w = int((np.array(pnls) > 0).sum()) if pnls else 0
            cil, cih = boot_ci(tr, w, gp, gl)
            rows.append(dict(series=series, kind="GBM" if "GB" in series else "SHUF", k=k, W=W, R=R,
                             pf_all=round(pf, 4), ci_low=round(cil, 4), ci_high=round(cih, 4), trades_all=tr))
        print(f"[placebo] {series} done", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUTDIR, "results_ob_placebo.csv"), index=False)
    print(f"[SAVED] results_ob_placebo.csv ({len(rows)} rows)")


if __name__ == "__main__":
    print(f"===== EXP#2 RUNNER (grid {len(GRID)} combos, primary {PRIMARY}) =====")
    t0 = time.time()
    run_placebo()
    run_real()
    print(f"[DONE EXP2] {(time.time()-t0)/60:.1f} min")
