# -*- coding: utf-8 -*-
"""
Atribucion por Componentes — Experimento #1 — RUNNER TF.
  - Panel logico de tipos de media x periodos x histeresis, config_id=0, as-of E2.
  - Random walk (6 placebo) mismo panel, global.
  - Contraste optimizado (top-1 por cluster desde JSON produccion).
Lectura PRIMARIA = global (pf_fwd agregado cross-cluster). Desglose per-cluster = diagnostico.
NO muta kernel/brain. Gate de fidelidad fast-path PASS (ver exp1_smoke).
"""
import sys, os, time, json, traceback
import numpy as np
import pandas as pd

ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import regime_walk_forward as rwf
import lab_historico_numba_v8_3 as lab

OUTDIR = os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626")

# ---- Panel logico (tipos soportados por lab.calc_ma, params estandar) ----
MA_TYPES = ["SMA", "EMA", "HMA", "ZLEMA", "KAMA", "VIDYA", "FRAMA",
            "TEMA", "DEMA", "T3", "Tenkan", "ALMA", "McGinley", "VWMA"]
PERIODS = [(8, 40), (10, 55), (12, 60)]   # (fast, slow); 10/55 = primario
HYSTS = [0.0, 0.5]
PRIMARY = (10, 55, 0.0)

CONFIGS = np.array([0], dtype=np.uint32)
SL, SLE, TS = lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT, lab.TS_PERCENT
CD, COMM = lab.COOLDOWN_BARS, lab.COMMISSION_ROUND_TRIP
DIV_DTYPE = np.uint8  # validado en smoke (div_bits uint8 (n,8))


def fast_precalc(df, fast_type, fast_p, slow_type, slow_p, hyst):
    n = len(df)
    close = df['close'].values.astype(np.float64)
    high = df['high'].values.astype(np.float64)
    low = df['low'].values.astype(np.float64)
    vol = df['volume'].values.astype(np.float64)
    ma_f = lab.calc_ma(fast_type, close, high, low, vol, fast_p, 0.0, 0.0)
    ma_s = lab.calc_ma(slow_type, close, high, low, vol, slow_p, 0.0, 0.0)
    atr = lab.calc_atr(high, low, close, lab.HYST_ATR_LEN)
    zb, zr = lab.calc_zone_with_hysteresis(ma_f, ma_s, atr, hyst)
    return {
        'close': close, 'high': high, 'low': low,
        'timestamps': df['timestamp'].values,
        'zone_bull': zb, 'zone_bear': zr,
        'filters_forming': np.zeros(n, dtype=np.uint32),
        'filters_resolved': np.zeros(n, dtype=np.uint32),
        'div_bits': np.zeros((n, 8), dtype=DIV_DTYPE),
    }


def pf_of(gp, gl):
    return gp / gl if gl > 0 else (5.0 if gp > 0 else 0.0)


def boot_ci(tr, w, gp, gl):
    b = rwf._bootstrap_pf_fwd_vectorized(np.array([tr]), np.array([w]), np.array([gp]), np.array([gl]))
    return float(b['pf_fwd_ci_low'][0]), float(b['pf_fwd_ci_high'][0])


# ============================================================
# 1) TF PANEL LOGICO (45 sym, as-of split)
# ============================================================
def run_logical():
    rows = []
    t_start = time.time()
    for si, sym in enumerate(rwf.SYMBOLS):
        try:
            df = rwf.load_full_history(sym)
            model = rwf.load_regime_model(sym)
            if df is None or model is None:
                print(f"[SKIP] {sym}: sin datos/modelo"); continue
            cl_labels, ncl = rwf.compute_cluster_labels(df, model)
            episodes = rwf.identify_episodes(cl_labels, ncl, min_bars=rwf.MIN_EPISODE_BARS)
            reg, ndob, split = rwf.build_regime_labels(
                cl_labels, episodes, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
            valid = [k for k in range(ncl) if split[k]['valid']]
            if not valid:
                print(f"[SKIP] {sym}: sin clusters validos"); continue
            for mt in MA_TYPES:
                for (fp, sp) in PERIODS:
                    for hy in HYSTS:
                        data = fast_precalc(df, mt, fp, mt, sp, hy)
                        res, cl_pnl, cl_tr, cl_w, cl_dd, cl_gp, cl_gl = lab.run_on_slice(
                            CONFIGS, data, 0, len(df), SL, SLE, TS, CD, COMM,
                            cluster_labels=reg, n_clusters=ndob)
                        gp_f = float(sum(cl_gp[0, k + ncl] for k in valid))
                        gl_f = float(sum(cl_gl[0, k + ncl] for k in valid))
                        tr_f = float(sum(cl_tr[0, k + ncl] for k in valid))
                        w_f = float(sum(cl_w[0, k + ncl] for k in valid))
                        gp_t = float(sum(cl_gp[0, k] for k in valid))
                        gl_t = float(sum(cl_gl[0, k] for k in valid))
                        pf_f = pf_of(gp_f, gl_f)
                        cil, cih = boot_ci(tr_f, w_f, gp_f, gl_f)
                        row = dict(symbol=rwf.sym_key(sym), ma_type=mt, fast=fp, slow=sp, hyst=hy,
                                   n_clusters=ncl, pf_tr=round(pf_of(gp_t, gl_t), 4),
                                   pf_fwd=round(pf_f, 4), ci_low=round(cil, 4), ci_high=round(cih, 4),
                                   trades_fwd=int(tr_f), wins_fwd=int(w_f))
                        for k in range(3):
                            if k in valid:
                                row[f'pf_fwd_c{k}'] = round(pf_of(float(cl_gp[0, k + ncl]), float(cl_gl[0, k + ncl])), 4)
                                row[f'trades_fwd_c{k}'] = int(cl_tr[0, k + ncl])
                            else:
                                row[f'pf_fwd_c{k}'] = np.nan; row[f'trades_fwd_c{k}'] = 0
                        rows.append(row)
            el = time.time() - t_start
            print(f"[{si+1}/45] {rwf.sym_key(sym):8s} done | {len(rows)} rows | {el/60:.1f} min", flush=True)
        except Exception as e:
            print(f"[ERR] {sym}: {e}"); traceback.print_exc()
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTDIR, "results_tf_logical.csv"), index=False)
    print(f"\n[SAVED] results_tf_logical.csv ({len(out)} rows)")
    return out


# ============================================================
# 2) RANDOM WALK (placebo) — global, mismo panel
# ============================================================
PLACEBO = ["PLBGB1", "PLBSH1", "PLBGB2", "PLBSH2", "PLBGB3", "PLBSH3"]
def run_placebo():
    rows = []
    for series in PLACEBO:
        df = rwf.load_full_history(series + "/USDT")
        if df is None:
            print(f"[SKIP placebo] {series}"); continue
        kind = "GBM" if "GB" in series else "SHUF"
        for mt in MA_TYPES:
            for (fp, sp) in PERIODS:
                for hy in HYSTS:
                    data = fast_precalc(df, mt, fp, mt, sp, hy)
                    res, *_ = lab.run_on_slice(CONFIGS, data, 0, len(df), SL, SLE, TS, CD, COMM)
                    gp, gl = float(res[0, 5]), float(res[0, 6])
                    tr, w = float(res[0, 1]), 0.0  # wins not in global tuple; approx via pnl sign not needed
                    # reconstruct wins from results? results[:,2]=wins
                    w = float(res[0, 2])
                    cil, cih = boot_ci(tr, w, gp, gl)
                    rows.append(dict(series=series, kind=kind, ma_type=mt, fast=fp, slow=sp, hyst=hy,
                                     pf=round(pf_of(gp, gl), 4), ci_low=round(cil, 4), ci_high=round(cih, 4),
                                     trades=int(tr)))
        print(f"[placebo] {series} done", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTDIR, "results_placebo.csv"), index=False)
    print(f"[SAVED] results_placebo.csv ({len(out)} rows)")
    return out


# ============================================================
# 3) CONTRASTE OPTIMIZADO (desde JSON produccion, top-1 por cluster)
#    CAVEAT: pf_fwd optimizado esta CONTAMINADO por seleccion (la produccion
#    eligio con el forward CI). Por eso es CONTRASTE, no edge. La brecha
#    logico-vs-optimizado = sobreajuste-al-activo cuantificado.
# ============================================================
def reconstruct_gp_gl(pf, pnl):
    if pf is None or pnl is None: return None, None
    if abs(pf - 1.0) < 1e-6: return None, None
    gl = pnl / (pf - 1.0)
    gp = pf * gl
    if gl <= 0 or gp < 0: return None, None
    return gp, gl

def run_optimized():
    rows = []
    for sym in rwf.SYMBOLS:
        sc = rwf.sym_clean(sym)
        path = os.path.join(ROOT, "regime_wf", f"{sc}_specialist_configs.json")
        if not os.path.exists(path):
            print(f"[SKIP opt] {sym}: no JSON"); continue
        d = json.load(open(path))
        clusters = d.get('clusters', {})
        gp_sum = gl_sum = 0.0; per = {}
        for k, cl in clusters.items():
            tc = cl.get('top_configs', [])
            if not tc: continue
            s = tc[0]
            per[f'opt_pf_fwd_c{k}'] = s.get('pf_fwd')
            per[f'opt_preset_c{k}'] = s.get('preset')
            gp, gl = reconstruct_gp_gl(s.get('pf_fwd'), s.get('pnl_fwd'))
            if gp is not None:
                gp_sum += gp; gl_sum += gl
        row = dict(symbol=rwf.sym_key(sym),
                   opt_pf_fwd_global=round(pf_of(gp_sum, gl_sum), 4) if gl_sum > 0 else np.nan)
        row.update(per)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTDIR, "results_optimized.csv"), index=False)
    print(f"[SAVED] results_optimized.csv ({len(out)} rows)")
    return out


if __name__ == "__main__":
    print("===== EXPERIMENTO #1 — RUNNER TF =====")
    print(f"Panel: {len(MA_TYPES)} tipos x {len(PERIODS)} periodos x {len(HYSTS)} hyst = "
          f"{len(MA_TYPES)*len(PERIODS)*len(HYSTS)} variantes/sym")
    t0 = time.time()
    run_optimized()
    run_placebo()
    run_logical()
    print(f"\n[DONE TF] total {(time.time()-t0)/60:.1f} min")
