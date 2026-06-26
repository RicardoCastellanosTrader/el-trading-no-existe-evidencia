# -*- coding: utf-8 -*-
"""
Atribucion por Componentes — Experimento #1 — RUNNER MR.
Capa MR (Tenkan-9 / HA-diario) YA fija-logica por diseno -> el test mas limpio.
config_id=0 = zona pura. Lectura PRIMARIA = global (forward, agregado cross-cluster
via episodios). Desglose per-cluster = diagnostico. Random walk (6 placebo) = global.
Reusa mean_reversion_walk_forward._run_cluster_simulation (acumulacion por episodios).
NO muta kernel.
"""
import sys, os, time, traceback
import numpy as np
import pandas as pd

ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import regime_walk_forward as rwf
import mean_reversion_features as mrf
import mean_reversion_walk_forward as mrwf
import mean_reversion_kernel as mrk

OUTDIR = os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626")
CONFIGS = np.array([0], dtype=np.uint32)


def pf_of(gp, gl):
    return gp / gl if gl > 0 else (5.0 if gp > 0 else 0.0)


def boot_ci(tr, w, gp, gl):
    b = rwf._bootstrap_pf_fwd_vectorized(np.array([tr]), np.array([w]), np.array([gp]), np.array([gl]))
    return float(b['pf_fwd_ci_low'][0]), float(b['pf_fwd_ci_high'][0])


def sim_eps(mr_data, episodes):
    """Acumula config=0 sobre lista de episodios -> (gp, gl, trades, wins)."""
    if not episodes:
        return 0.0, 0.0, 0.0, 0.0
    r = mrwf._run_cluster_simulation(CONFIGS, mr_data, episodes)
    gp = float(np.asarray(r['gross_profit'])[0])
    gl = float(np.asarray(r['gross_loss'])[0])
    tr = float(np.asarray(r['trades'])[0])
    w = float(np.asarray(r['wins'])[0])
    return gp, gl, tr, w


def run_mr_logical():
    rows = []
    t0 = time.time()
    for si, sym in enumerate(rwf.SYMBOLS):
        try:
            df = rwf.load_full_history(sym)
            model = rwf.load_regime_model(sym)
            if df is None or model is None:
                print(f"[SKIP] {sym}"); continue
            mr_data = mrf.precalculate_mean_reversion(sym, df)
            cl_labels, ncl = rwf.compute_cluster_labels(df, model)
            gmm_probs = rwf.compute_gmm_probs(df, model)
            episodes = rwf.identify_episodes(cl_labels, ncl, min_bars=rwf.MIN_EPISODE_BARS)
            reg, ndob, split = rwf.build_regime_labels(
                cl_labels, episodes, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=0,
                gmm_probs=gmm_probs, confirm_threshold=0.75, max_toxic_tail=100, min_toxic_tail=5)
            valid = [k for k in range(ncl) if split[k]['valid']]
            if not valid:
                print(f"[SKIP] {sym}: sin clusters validos"); continue

            glob_fwd, glob_tr = [], []
            per = {}
            for k in valid:
                all_eps = episodes.get(k, [])
                n_train = split[k]['train_episodes']
                tr_eps = all_eps[:n_train]
                fwd_eps = all_eps[n_train:]
                glob_tr += tr_eps; glob_fwd += fwd_eps
                gpk, glk, trk, wk = sim_eps(mr_data, fwd_eps)
                per[f'pf_fwd_c{k}'] = round(pf_of(gpk, glk), 4)
                per[f'trades_fwd_c{k}'] = int(trk)
            gp_f, gl_f, tr_f, w_f = sim_eps(mr_data, glob_fwd)
            gp_t, gl_t, tr_t, w_t = sim_eps(mr_data, glob_tr)
            cil, cih = boot_ci(tr_f, w_f, gp_f, gl_f)
            row = dict(symbol=rwf.sym_key(sym), n_clusters=ncl,
                       pf_tr=round(pf_of(gp_t, gl_t), 4), pf_fwd=round(pf_of(gp_f, gl_f), 4),
                       ci_low=round(cil, 4), ci_high=round(cih, 4),
                       trades_fwd=int(tr_f), wins_fwd=int(w_f), trades_tr=int(tr_t))
            for k in range(3):
                row[f'pf_fwd_c{k}'] = per.get(f'pf_fwd_c{k}', np.nan)
                row[f'trades_fwd_c{k}'] = per.get(f'trades_fwd_c{k}', 0)
            rows.append(row)
            print(f"[{si+1}/45] {rwf.sym_key(sym):8s} MR pf_fwd={row['pf_fwd']} CI[{cil:.2f},{cih:.2f}] "
                  f"trades={int(tr_f)} | {(time.time()-t0)/60:.1f}min", flush=True)
        except Exception as e:
            print(f"[ERR] {sym}: {e}"); traceback.print_exc()
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTDIR, "results_mr_logical.csv"), index=False)
    print(f"[SAVED] results_mr_logical.csv ({len(out)} rows)")
    return out


PLACEBO = ["PLBGB1", "PLBSH1", "PLBGB2", "PLBSH2", "PLBGB3", "PLBSH3"]
def run_mr_placebo():
    rows = []
    for series in PLACEBO:
        df = rwf.load_full_history(series + "/USDT")
        if df is None:
            print(f"[SKIP placebo] {series}"); continue
        mr_data = mrf.precalculate_mean_reversion(series + "/USDT", df)
        n = len(mr_data['close'])
        res = mrk.run_on_slice(CONFIGS, mr_data, 100, n)
        gp, gl, tr, w = float(res[0, 5]), float(res[0, 6]), float(res[0, 1]), float(res[0, 2])
        cil, cih = boot_ci(tr, w, gp, gl)
        rows.append(dict(series=series, kind="GBM" if "GB" in series else "SHUF",
                         pf=round(pf_of(gp, gl), 4), ci_low=round(cil, 4), ci_high=round(cih, 4),
                         trades=int(tr)))
        print(f"[placebo MR] {series} pf={pf_of(gp,gl):.4f} trades={int(tr)}", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTDIR, "results_mr_placebo.csv"), index=False)
    print(f"[SAVED] results_mr_placebo.csv ({len(out)} rows)")
    return out


if __name__ == "__main__":
    print("===== EXPERIMENTO #1 — RUNNER MR (Tenkan-9/HA-diario fija-logica) =====")
    t0 = time.time()
    run_mr_placebo()
    run_mr_logical()
    print(f"\n[DONE MR] total {(time.time()-t0)/60:.1f} min")
