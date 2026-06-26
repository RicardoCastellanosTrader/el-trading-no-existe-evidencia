# -*- coding: utf-8 -*-
"""
Atribucion por Componentes — Experimento #1 — SMOKE (1 celda + gate de fidelidad).

Objetivos:
  (A) FIDELIDAD: precalc zone-only (rapido) == precalc full (lento) para config_id=0.
      Si identico -> autorizado usar el path rapido en el barrido (evita el loop O(n)
      de filtros forming, ~300s/variante, que config=0 NO lee).
  (B) 1 CELDA real: BTC, EMA 10/55, full df, split as-of E2, config_id=0 ->
      pf_tr / pf_fwd GLOBAL (agregado cross-cluster) + CI bootstrap + desglose per-cluster.
  (C) TIMING: proyectar coste del barrido.

NO muta kernel/brain. Solo importa y ejecuta. Lee del panel logico (config=0).
"""
import sys, os, time
import numpy as np
import pandas as pd

ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import regime_walk_forward as rwf
import lab_historico_numba_v8_3 as lab

SYMBOL = "BTC/USDT"
PRESET = ('EMA', 10, 0.0, 0.0, 'EMA', 55, 0.0, 0.0, 'EMA', 220, 0.0, 0.0)  # trend no usado en zona aislada
HYST = 0.0
CONFIGS = np.array([0], dtype=np.uint32)

SL = lab.SL_PERCENT
SLE = lab.SL_EMERGENCY_PERCENT
TS = lab.TS_PERCENT
CD = lab.COOLDOWN_BARS
COMM = lab.COMMISSION_ROUND_TRIP
print(f"[CONST] SL={SL} SLE={SLE} TS={TS} cooldown={CD} commission={COMM}")


def fast_precalc(df, preset, hyst_mult, div_dtype=np.uint8):
    """Phase-1-only precalc: MAs + ATR + zona; filtros/div = ceros (config=0 no los lee)."""
    n = len(df)
    close = df['close'].values.astype(np.float64)
    high = df['high'].values.astype(np.float64)
    low = df['low'].values.astype(np.float64)
    vol = df['volume'].values.astype(np.float64)
    ma_fast = lab.calc_ma(preset[0], close, high, low, vol, preset[1], preset[2], preset[3])
    ma_slow = lab.calc_ma(preset[4], close, high, low, vol, preset[5], preset[6], preset[7])
    atr = lab.calc_atr(high, low, close, lab.HYST_ATR_LEN)
    zb, zr = lab.calc_zone_with_hysteresis(ma_fast, ma_slow, atr, hyst_mult)
    return {
        'close': close, 'high': high, 'low': low,
        'timestamps': df['timestamp'].values,
        'zone_bull': zb, 'zone_bear': zr,
        'filters_forming': np.zeros(n, dtype=np.uint32),
        'filters_resolved': np.zeros(n, dtype=np.uint32),
        'div_bits': np.zeros((n, 8), dtype=div_dtype),
    }


def sim_global(data):
    return lab.run_on_slice(CONFIGS, data, 0, len(data['close']), SL, SLE, TS, CD, COMM)


def pf_of(gp, gl):
    if gl > 0:
        return gp / gl
    return 5.0 if gp > 0 else 0.0


df = rwf.load_full_history(SYMBOL)
print(f"\n[DATA] {SYMBOL}: {len(df)} barras | {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")

# ======================================================================
# (A) GATE DE FIDELIDAD sobre tail 8000 (full precalc lento pero acotado)
# ======================================================================
print("\n===== (A) GATE DE FIDELIDAD (tail 8000) =====")
dft = df.tail(8000).reset_index(drop=True)
t0 = time.time()
data_full = lab.precalculate_all_data(dft, preset=PRESET, hyst_mult=HYST, symbol=SYMBOL)
t_full = time.time() - t0
print(f"[TIME] full precalc (8000 barras): {t_full:.1f}s")
print(f"[INFO] div_bits dtype={data_full['div_bits'].dtype} shape={data_full['div_bits'].shape}")
print(f"[INFO] filters_forming dtype={data_full['filters_forming'].dtype}")

data_fast = fast_precalc(dft, PRESET, HYST, div_dtype=data_full['div_bits'].dtype)

zb_eq = np.array_equal(data_full['zone_bull'], data_fast['zone_bull'])
zr_eq = np.array_equal(data_full['zone_bear'], data_fast['zone_bear'])
print(f"[CHECK A1] zone_bull identico: {zb_eq} | zone_bear identico: {zr_eq}")

rf = sim_global(data_full)
ra = sim_global(data_fast)
res_full, res_fast = rf[0], ra[0]
res_eq = np.array_equal(res_full, res_fast)
print(f"[CHECK A2] results[config=0] identico full-vs-fast: {res_eq}")
print(f"           full:  pnl={res_full[0,0]:.4f} trades={res_full[0,1]:.0f} gp={res_full[0,5]:.4f} gl={res_full[0,6]:.4f} pf={pf_of(res_full[0,5],res_full[0,6]):.4f}")
print(f"           fast:  pnl={res_fast[0,0]:.4f} trades={res_fast[0,1]:.0f} gp={res_fast[0,5]:.4f} gl={res_fast[0,6]:.4f} pf={pf_of(res_fast[0,5],res_fast[0,6]):.4f}")
FIDELITY_OK = zb_eq and zr_eq and res_eq
print(f"[GATE A] FIDELIDAD {'PASS' if FIDELITY_OK else 'FAIL'} -> fast path {'autorizado' if FIDELITY_OK else 'NO autorizado'}")

# ======================================================================
# (B) 1 CELDA real: BTC full df, split as-of, config=0, global-fwd + CI
# ======================================================================
print("\n===== (B) 1 CELDA real (BTC, EMA 10/55, as-of) =====")
model = rwf.load_regime_model(SYMBOL)
cl_labels, ncl = rwf.compute_cluster_labels(df, model)
print(f"[REGIME] {ncl} clusters, {int(np.sum(cl_labels>=0))}/{len(df)} barras etiquetadas")
episodes = rwf.identify_episodes(cl_labels, ncl, min_bars=rwf.MIN_EPISODE_BARS)
reg_labels, ndob, split_info = rwf.build_regime_labels(
    cl_labels, episodes, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
valid = [k for k in range(ncl) if split_info[k]['valid']]
print(f"[SPLIT] n_doubled={ndob} valid_clusters={valid}")

t0 = time.time()
data = fast_precalc(df, PRESET, HYST, div_dtype=data_full['div_bits'].dtype)
t_fast_full = time.time() - t0
print(f"[TIME] fast precalc (full {len(df)} barras): {t_fast_full:.2f}s")

t0 = time.time()
results, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = lab.run_on_slice(
    CONFIGS, data, 0, len(df), SL, SLE, TS, CD, COMM,
    cluster_labels=reg_labels, n_clusters=ndob)
t_sim = time.time() - t0
print(f"[TIME] run_on_slice (1 config, as-of): {t_sim:.2f}s")

# Agregados GLOBAL (cross-cluster) sobre forward holdout
gp_fwd = float(sum(cl_gp[0, k + ncl] for k in valid))
gl_fwd = float(sum(cl_gl[0, k + ncl] for k in valid))
tr_fwd = float(sum(cl_trades[0, k + ncl] for k in valid))
w_fwd = float(sum(cl_wins[0, k + ncl] for k in valid))
gp_tr = float(sum(cl_gp[0, k] for k in valid))
gl_tr = float(sum(cl_gl[0, k] for k in valid))
tr_tr = float(sum(cl_trades[0, k] for k in valid))

pf_fwd = pf_of(gp_fwd, gl_fwd)
pf_tr = pf_of(gp_tr, gl_tr)

boot = rwf._bootstrap_pf_fwd_vectorized(
    np.array([tr_fwd]), np.array([w_fwd]), np.array([gp_fwd]), np.array([gl_fwd]))
ci_low = float(boot['pf_fwd_ci_low'][0])
ci_high = float(boot['pf_fwd_ci_high'][0])

print(f"\n[RESULT GLOBAL] pf_tr={pf_tr:.4f} (trades_tr={tr_tr:.0f}) | "
      f"pf_fwd={pf_fwd:.4f} CI=[{ci_low:.3f}, {ci_high:.3f}] (trades_fwd={tr_fwd:.0f}, wins_fwd={w_fwd:.0f})")
print(f"[CRITERIO] CI excluye 1.0 (breakeven)? {'SI (edge)' if ci_low > 1.0 else 'NO'}")
print(f"[BENCHMARK] sistema completo as-of GLOBAL = 0.702 [0.44, 1.07]")

print("\n[DESGLOSE per-cluster (DIAGNOSTICO, no criterio)]:")
names = model.get('cluster_names', {}) if isinstance(model, dict) else {}
for k in valid:
    cgp, cgl = float(cl_gp[0, k + ncl]), float(cl_gl[0, k + ncl])
    ctr = float(cl_trades[0, k + ncl])
    print(f"   C{k} ({names.get(k, '?')}): pf_fwd={pf_of(cgp,cgl):.4f} trades_fwd={ctr:.0f}")

# ======================================================================
# (C) PROYECCION DE COSTE
# ======================================================================
print("\n===== (C) PROYECCION COSTE BARRIDO =====")
per_cell = t_fast_full + t_sim
print(f"[COST] por celda (fast precalc + sim) ~= {per_cell:.2f}s")
print(f"[COST] panel TF logico estimado: 45 sym x ~8 tipos x 3 periodos x 2 hyst = ~2160 celdas")
print(f"       -> ~{2160*per_cell/60:.0f} min  (+ placebo 6 series x panel)")
print(f"[NOTE] (numba CPU, sin GPU); full precalc evitado por gate A")
print("\n[SMOKE DONE]")
