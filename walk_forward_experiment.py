#!/usr/bin/env python3
"""
walk_forward_experiment.py — Walk-Forward Multi-Punto: Ingenieria inversa de filtros optimos.

Genera dataset masivo (activos x puntos de anclaje x gemas) para descubrir que
metricas del periodo de validacion (7k) predicen rendimiento forward real.

Flujo:
  Fase 1: Para cada (simbolo, anclaje): lab historico -> extractor -> evaluar en 5 tramos
  Fase 2: Etiquetar dataset con alpha y clasificacion
  Fase 3: Analisis estadistico y descubrimiento de patrones

Uso:
    python walk_forward_experiment.py --symbols BTC/USDT,ETH/USDT --output-dir wf_experiment
    python walk_forward_experiment.py --all-symbols --output-dir wf_experiment
    python walk_forward_experiment.py --symbols BTC/USDT --step 2000 --fwd-size 2000 --opt-size 5000
    python walk_forward_experiment.py --analyze-only --output-dir wf_experiment
"""

import os
import sys
import io
import gc
import time
import json
import argparse
import importlib.util
import traceback
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool

import pandas as pd
import numpy as np


# ============================================
# CONFIGURACION
# ============================================

DEFAULT_SYMBOLS = [
    "BNB/USDT", "BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT",
    "TRX/USDT", "DOGE/USDT", "ADA/USDT", "BCH/USDT", "LINK/USDT",
    "XLM/USDT", "SUI/USDT", "LTC/USDT", "AVAX/USDT", "HBAR/USDT",
    "SHIB/USDT", "DOT/USDT", "UNI/USDT", "TAO/USDT",
    "AAVE/USDT", "NEAR/USDT", "ICP/USDT", "ETC/USDT",
    "ONDO/USDT", "ENA/USDT", "POL/USDT", "WLD/USDT", "APT/USDT",
    "ATOM/USDT", "ALGO/USDT", "RENDER/USDT", "ARB/USDT", "FIL/USDT",
    "QNT/USDT", "VET/USDT", "SEI/USDT", "OP/USDT",
    "IMX/USDT", "INJ/USDT", "FET/USDT", "STX/USDT", "SAND/USDT",
    "MANA/USDT", "GRT/USDT", "THETA/USDT",
]

DEFAULT_CONFIG = {
    # Ventanas
    "opt_size": 5000,
    "ext_size": 2000,
    "fwd_size": 2000,
    "step": 2000,
    "warmup": 500,

    # Lab Lite
    "lite_top_n": 5,
    "lite_diversity": True,

    # Lab
    "hyst_values": [0.0, 0.5],
    "sl_percent": 3.0,
    "sl_emergency_percent": 5.0,
    "ts_percent": 0.5,
    "cooldown_bars": 1,
    "commission": 0.10,

    # Extractor
    "extractor_top_n": 30,

    # Etiquetado
    "alpha_good": 2.0,
    "alpha_bad": -2.0,
    "pf_good": 1.2,
    "pf_bad": 0.8,
}

# Lab constants (matching lab_historico_numba_v8_3.py)
TRAIN_RATIO = 0.50
MIN_TRADES_TRAIN = 15
MIN_TRADES_TEST = 15
MIN_PF_TEST = 1.2
MAX_DD_TEST = 25.0
TOP_TRAIN = 20000
W_TRAIN = 0.35
W_TEST = 0.40
W_FULL = 0.25

# Checkpoint version: increment when checkpoint format changes
# v2 = lab_lite per anchor (presets discovered dynamically, not static)
CHECKPOINT_VERSION = 2


# ============================================
# CUDA DETECTION — lazy init to avoid BSOD with multiprocessing
# On Windows (spawn), workers re-import this module; top-level CUDA init
# would create competing GPU contexts across processes → BSOD.
# CUDA must only be initialized in the main process, after workers finish.
# ============================================

USE_CUDA = False
_cuda_sim = None
_cuda_initialized = False


def _init_cuda():
    """Initialize CUDA. Must only be called from the main process."""
    global USE_CUDA, _cuda_sim, _cuda_initialized
    if _cuda_initialized:
        return
    _cuda_initialized = True
    try:
        from lab_cuda import CUDASimulatorOptimized
        _cuda_sim = CUDASimulatorOptimized()
        USE_CUDA = _cuda_sim.gpu_available
        if USE_CUDA:
            _gpu_label = _cuda_sim.gpu_name.decode() if isinstance(_cuda_sim.gpu_name, bytes) else _cuda_sim.gpu_name
            print(f"[CUDA] GPU detectada: {_gpu_label}, usando aceleracion CUDA")
        else:
            print(f"[CUDA] GPU detectada pero no disponible, usando CPU")
            _cuda_sim = None
    except Exception as e:
        USE_CUDA = False
        _cuda_sim = None
        print(f"[CUDA] No disponible ({e}), usando CPU")


def run_slice(config_ids, data, start, end, sl, sl_e, ts, cool, comm,
              cuda_handle=None, lab=None):
    """Wrapper que ejecuta run_on_slice en GPU o CPU segun disponibilidad."""
    if USE_CUDA and _cuda_sim is not None and cuda_handle is not None:
        return _cuda_sim.run_on_slice(config_ids, cuda_handle, start, end,
                                       sl, sl_e, ts, cool, comm)
    else:
        return lab.run_on_slice(config_ids, data, start, end, sl, sl_e, ts, cool, comm)


# ============================================
# IMPORTACION DE MODULOS
# ============================================

_module_cache = {}

def _import_module(filename):
    if filename in _module_cache:
        return _module_cache[filename]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        print(f"ERROR: {path} no encontrado")
        sys.exit(1)
    name = os.path.splitext(filename)[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _module_cache[filename] = mod
    return mod


def import_lab():
    return _import_module("lab_historico_numba_v8_3.py")


def import_extractor():
    return _import_module("extractor_gemas.py")


def import_lite():
    return _import_module("lab_lite_zonas_v5d.py")


# ============================================
# PRECALC MULTIPROCESSING WORKERS
# ============================================

# Shared state set by worker initializer (one copy per worker process)
_worker_df = None
_worker_lab = None


def _precalc_worker_init(df_pickle_bytes):
    """Initializer for each worker process: deserializes the shared DataFrame
    and imports the lab module (triggers Numba JIT compilation once per worker)."""
    global _worker_df, _worker_lab
    # Fix Windows cp1252 encoding crash when lab prints emojis in workers
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    _worker_df = pd.read_pickle(io.BytesIO(df_pickle_bytes))
    # Each worker needs its own lab module instance (Numba JIT is per-process)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "lab_historico_numba_v8_3.py")
    spec = importlib.util.spec_from_file_location(
        f"lab_worker_{os.getpid()}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _worker_lab = mod


def _precalc_worker(args):
    """Worker function: precalculates indicators for one (preset, hyst) variant.
    Returns (preset_key, hyst, data_dict, preset_tuple, elapsed_seconds).
    CUDA is NOT used here — only CPU indicator computation."""
    preset, hyst, symbol = args
    t0 = time.time()
    data = _worker_lab.precalculate_all_data(
        _worker_df, preset=preset, hyst_mult=hyst, symbol=symbol)
    elapsed = time.time() - t0
    preset_key = f"{preset[0]}({preset[1]})/{preset[4]}({preset[5]})"
    print(f"    [worker-{os.getpid()}] {preset_key} H{hyst:.1f}: {elapsed:.1f}s", flush=True)
    return (preset_key, hyst, data, preset, elapsed)


# ============================================
# UTILIDADES
# ============================================

def sc(symbol):
    return symbol.replace("/", "")


def load_presets_from_csv(csv_path):
    """Carga presets desde CSV del lab lite. Retorna (presets, cluster_ids)."""
    df = pd.read_csv(csv_path)
    presets = []
    cluster_ids = []
    for _, row in df.iterrows():
        preset = (
            str(row['fast_type']), int(row['fast_period']),
            float(row['fast_p1']), float(row['fast_p2']),
            str(row['slow_type']), int(row['slow_period']),
            float(row['slow_p1']), float(row['slow_p2']),
            str(row['trend_type']), int(row['trend_period']),
            float(row['trend_p1']), float(row['trend_p2']),
        )
        presets.append(preset)
        cid = -1
        if 'cluster_id' in row.index:
            try:
                cid = int(row['cluster_id'])
            except (ValueError, TypeError):
                cid = -1
        cluster_ids.append(cid)
    return presets, cluster_ids


def compute_anchor_points(n_bars, opt_size, ext_size, fwd_size, step, warmup):
    """Calcula puntos de anclaje desde el mas reciente hacia atras.
    Retorna lista de dicts con indices de cada tramo.
    """
    min_per_anchor = warmup + ext_size + opt_size + fwd_size
    anchors = []
    idx = 0
    while True:
        fwd_end = n_bars - idx * step
        fwd_start = fwd_end - fwd_size
        opt_end = fwd_start
        opt_start = opt_end - opt_size
        ext_end = opt_start
        ext_start = ext_end - ext_size
        needed_start = ext_start - warmup

        if needed_start < 0:
            break

        anchors.append({
            "anchor_idx": idx,
            "ext_start": ext_start,
            "ext_end": ext_end,
            "opt_start": opt_start,
            "opt_end": opt_end,
            "fwd_start": fwd_start,
            "fwd_end": fwd_end,
            "fwd_h1_end": fwd_start + fwd_size // 2,
            "fwd_h2_start": fwd_start + fwd_size // 2,
        })
        idx += 1

    return anchors


def compute_asset_context(close_arr, start, end):
    """Calcula metricas de contexto del activo para un tramo."""
    if end <= start or start < 0 or end > len(close_arr):
        return {"return": 0.0, "volatility": 0.0, "maxdd": 0.0}

    prices = close_arr[start:end]
    if len(prices) < 2 or prices[0] == 0:
        return {"return": 0.0, "volatility": 0.0, "maxdd": 0.0}

    # Buy & hold return
    bh_return = (prices[-1] - prices[0]) / prices[0] * 100

    # Volatility (std of hourly returns)
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns) * 100 if len(returns) > 0 else 0.0

    # Max drawdown
    cummax = np.maximum.accumulate(prices)
    drawdowns = (cummax - prices) / cummax * 100
    maxdd = np.max(drawdowns) if len(drawdowns) > 0 else 0.0

    return {"return": float(bh_return), "volatility": float(volatility), "maxdd": float(maxdd)}


def compute_regime_columns(df, inplace=False):
    """Añade columnas de régimen de mercado a un DataFrame con columnas de contexto.

    Requiere: asset_return_opt, asset_return_fwd, asset_volatility_opt
    Genera:   regime_opt, regime_fwd, regime_match, regime_pair, chaos_opt

    Régimen: BULL si return > +5%, BEAR si return < -5%, NEUTRAL en medio.
    Chaos: volatilidad relativa al retorno neto.
    """
    BULL_THRESH =  5.0
    BEAR_THRESH = -5.0
    CHAOS_EPS   =  1.0

    if not inplace:
        df = df.copy()

    if 'asset_return_opt' in df.columns:
        df['regime_opt'] = 'NEUTRAL'
        df.loc[df['asset_return_opt'] >  BULL_THRESH, 'regime_opt'] = 'BULL'
        df.loc[df['asset_return_opt'] <  BEAR_THRESH, 'regime_opt'] = 'BEAR'

    if 'asset_return_fwd' in df.columns:
        df['regime_fwd'] = 'NEUTRAL'
        df.loc[df['asset_return_fwd'] >  BULL_THRESH, 'regime_fwd'] = 'BULL'
        df.loc[df['asset_return_fwd'] <  BEAR_THRESH, 'regime_fwd'] = 'BEAR'

    if 'regime_opt' in df.columns and 'regime_fwd' in df.columns:
        df['regime_match'] = df['regime_opt'] == df['regime_fwd']
        df['regime_pair']  = df['regime_opt'] + '->' + df['regime_fwd']

    if 'asset_volatility_opt' in df.columns and 'asset_return_opt' in df.columns:
        df['chaos_opt'] = (df['asset_volatility_opt'] /
                           (df['asset_return_opt'].abs() + CHAOS_EPS))

    return df


def make_ma_info_str(preset, hyst):
    """Construye string ma_info como aparece en los CSVs del lab."""
    ft, fl = preset[0], preset[1]
    st, sl_p = preset[4], preset[5]
    hyst_tag = "H00" if hyst == 0.0 else "H05"
    return f"{ft}({fl})/{st}({sl_p}) {hyst_tag}"


# ============================================
# FASE 1: SIMULACION LAB EN VENTANA
# ============================================

def run_lab_on_window(all_configs, data, opt_start, opt_end, lab, preset, hyst,
                      ma_info_str, variant_tag, cuda_handle=None, eval_all_train=False):
    """Replica la logica de _process_one_variant del lab para una ventana especifica.

    Retorna DataFrame con las columnas que el extractor necesita, o None si falla.
    """
    n_opt = opt_end - opt_start
    split_bar = opt_start + int(n_opt * TRAIN_RATIO)
    train_start = opt_start
    train_end = split_bar
    test_start = split_bar
    test_end = opt_end
    train_bars = train_end - train_start
    test_bars = test_end - test_start

    if train_bars < 500 or test_bars < 500:
        return None

    # B&H for reference
    close = data['close']
    bnh_train = (close[train_end - 1] - close[train_start + 50]) / close[train_start + 50] * 100 if close[train_start + 50] > 0 else 0
    bnh_test = (close[test_end - 1] - close[test_start]) / close[test_start] * 100 if close[test_start] > 0 else 0
    bnh_full = (close[opt_end - 1] - close[opt_start + 50]) / close[opt_start + 50] * 100 if close[opt_start + 50] > 0 else 0
    train_years = train_bars / 8760.0
    test_years = test_bars / 8760.0
    full_years = n_opt / 8760.0
    bnh_train_annual = bnh_train / train_years if train_years > 0.05 else 0
    bnh_test_annual = bnh_test / test_years if test_years > 0.05 else 0
    bnh_annual = bnh_full / full_years if full_years > 0.05 else 0

    sl = lab.SL_PERCENT
    sl_e = lab.SL_EMERGENCY_PERCENT
    ts = lab.TS_PERCENT
    cool = lab.COOLDOWN_BARS
    comm = lab.COMMISSION_ROUND_TRIP

    # --- TRAIN ---
    results_train = run_slice(all_configs, data, train_start, train_end,
                              sl, sl_e, ts, cool, comm, cuda_handle=cuda_handle, lab=lab)
    pnl_tr = results_train[:, 0]
    trades_tr = results_train[:, 1]
    wins_tr = results_train[:, 2]
    cancels_tr = results_train[:, 3]
    maxdd_tr = results_train[:, 4]
    gp_tr = results_train[:, 5]
    gl_tr = results_train[:, 6]

    score_tr, pnl_ann_tr, _, pf_tr, _, _ = lab.calc_score_v63(
        pnl_tr, maxdd_tr, gp_tr, gl_tr, trades_tr, cancels_tr, train_bars)
    wr_tr = np.where(trades_tr > 0, wins_tr / trades_tr * 100, 0.0)

    # Filter train
    if eval_all_train:
        valid_train = (trades_tr >= 5) & (pnl_tr > 0)
    else:
        valid_train = (trades_tr >= MIN_TRADES_TRAIN) & (pnl_tr > 0) & (pnl_ann_tr > 0)
    n_valid = int(np.sum(valid_train))
    if n_valid == 0:
        return None

    if eval_all_train:
        # Relaxed: all configs that pass minimum train filter
        top_train_indices = np.where(valid_train)[0]
        MAX_EVAL_ALL_CONFIGS = 250_000
        n_before_cap = len(top_train_indices)
        if n_before_cap > MAX_EVAL_ALL_CONFIGS:
            # Cap: keep top configs by score_tr to avoid blowup in bull periods
            top_scores = score_tr[top_train_indices]
            cap_order = np.argsort(-top_scores)[:MAX_EVAL_ALL_CONFIGS]
            top_train_indices = top_train_indices[cap_order]
            print(f"    [CAP] eval_all_train: {n_before_cap:,} passed filter -> capped to {MAX_EVAL_ALL_CONFIGS:,} by score_tr")
        else:
            print(f"    [CAP] eval_all_train: {n_before_cap:,} passed filter (under {MAX_EVAL_ALL_CONFIGS:,} cap, no trim)")
    else:
        valid_idx = np.where(valid_train)[0]
        sorted_by_score = valid_idx[np.argsort(-score_tr[valid_idx])]

        # PF quota (same as lab)
        pf_train_vals = np.where(gl_tr[valid_idx] > 0, gp_tr[valid_idx] / gl_tr[valid_idx],
                                 np.where(gp_tr[valid_idx] > 0, 5.0, 0.0))
        sorted_by_pf = valid_idx[np.argsort(-pf_train_vals)]
        PF_CUPO = min(2000, TOP_TRAIN // 3)
        top_by_score = set(sorted_by_score[:TOP_TRAIN].tolist())
        pf_extras = []
        for idx in sorted_by_pf:
            if idx not in top_by_score:
                pf_extras.append(idx)
                if len(pf_extras) >= PF_CUPO:
                    break

        top_train_indices = np.array(
            sorted_by_score[:TOP_TRAIN].tolist() + pf_extras, dtype=np.int64)

    # --- TEST ---
    top_configs = all_configs[top_train_indices]
    results_test = run_slice(top_configs, data, test_start, test_end,
                             sl, sl_e, ts, cool, comm, cuda_handle=cuda_handle, lab=lab)
    pnl_te = results_test[:, 0]
    trades_te = results_test[:, 1]
    wins_te = results_test[:, 2]
    cancels_te = results_test[:, 3]
    maxdd_te = results_test[:, 4]
    gp_te = results_test[:, 5]
    gl_te = results_test[:, 6]

    score_te, pnl_ann_te, _, pf_te, _, _ = lab.calc_score_v63(
        pnl_te, maxdd_te, gp_te, gl_te, trades_te, cancels_te, test_bars)
    wr_te = np.where(trades_te > 0, wins_te / trades_te * 100, 0.0)

    # --- FULL ---
    results_full = run_slice(top_configs, data, opt_start, opt_end,
                             sl, sl_e, ts, cool, comm, cuda_handle=cuda_handle, lab=lab)
    pnl_fu = results_full[:, 0]
    trades_fu = results_full[:, 1]
    wins_fu = results_full[:, 2]
    cancels_fu = results_full[:, 3]
    maxdd_fu = results_full[:, 4]
    gp_fu = results_full[:, 5]
    gl_fu = results_full[:, 6]

    score_fu, pnl_ann_fu, _, pf_fu, _, _ = lab.calc_score_v63(
        pnl_fu, maxdd_fu, gp_fu, gl_fu, trades_fu, cancels_fu, n_opt)
    wr_fu = np.where(trades_fu > 0, wins_fu / trades_fu * 100, 0.0)

    # --- SCORING (same as lab) ---
    min_pnl_annual_test = max(5.0, 20.0 + bnh_test_annual * 0.15)
    valid_test = (
        (trades_te >= MIN_TRADES_TEST) &
        (pnl_te > 0) &
        (pnl_ann_te >= min_pnl_annual_test) &
        (pf_te >= MIN_PF_TEST) &
        (maxdd_te <= MAX_DD_TEST)
    )
    if np.sum(valid_test) == 0:
        valid_test = (trades_te >= MIN_TRADES_TEST) & (pnl_te > 0) & (pf_te >= 1.1)
    if np.sum(valid_test) == 0:
        combined_score = score_tr[top_train_indices]
        robustness = np.zeros(len(top_train_indices))
    else:
        robustness = np.where(
            pnl_ann_tr[top_train_indices] > 0,
            np.minimum(pnl_ann_te / pnl_ann_tr[top_train_indices], 1.5),
            0.0
        )
        raw_combined = W_TRAIN * score_tr[top_train_indices] + W_TEST * score_te + W_FULL * score_fu
        both_profitable = (pnl_tr[top_train_indices] > 0) & (pnl_te > 0)
        consistency = np.where(both_profitable, 1.2, 0.3)
        beats_bnh_test = np.where(pnl_ann_te > bnh_test_annual, 1.3, 1.0)
        beats_bnh_train = np.where(pnl_ann_tr[top_train_indices] > bnh_train_annual, 1.2, 1.0)
        combined_score = raw_combined * np.sqrt(np.maximum(robustness, 0.01)) * consistency * beats_bnh_test * beats_bnh_train

    # --- BUILD DATAFRAME ---
    rows = []
    for i in range(len(top_train_indices)):
        gi = top_train_indices[i]
        cfg = int(all_configs[gi])
        decoded = lab.decode_config(cfg)

        entry_str = '+'.join(decoded['entry_tfs']) if decoded['entry_tfs'] else 'ZONA'
        exit_str = '+'.join(decoded['exit_tfs'])
        inds_str = '+'.join(decoded['div_indicators']) if decoded['div_indicators'] else '-'

        rows.append({
            'config_id': cfg,
            'preset': variant_tag,
            'ma_info': ma_info_str,
            'entry_tfs': entry_str,
            'n_entry_tfs': decoded['n_entry_tfs'],
            'exit_tfs': exit_str,
            'cancel': decoded['cancel_str'],
            'sl_type': decoded['ts_str'],
            'div_entry': decoded['div_entry_mode'],
            'div_exit': decoded['div_exit'],
            'div_type': decoded['div_type'],
            'variant': decoded['variant'],
            'indicators': inds_str,
            'pnl_tr': float(pnl_tr[gi]),
            'pnl_ann_tr': float(pnl_ann_tr[gi]),
            'trades_tr': int(trades_tr[gi]),
            'wr_tr': float(wr_tr[gi]),
            'maxdd_tr': float(maxdd_tr[gi]),
            'pf_tr': float(pf_tr[gi]),
            'score_tr': float(score_tr[gi]),
            'pnl_te': float(pnl_te[i]),
            'pnl_ann_te': float(pnl_ann_te[i]),
            'trades_te': int(trades_te[i]),
            'wr_te': float(wr_te[i]),
            'maxdd_te': float(maxdd_te[i]),
            'pf_te': float(pf_te[i]),
            'score_te': float(score_te[i]),
            'pnl_fu': float(pnl_fu[i]),
            'pnl_ann_fu': float(pnl_ann_fu[i]),
            'trades_fu': int(trades_fu[i]),
            'wr_fu': float(wr_fu[i]),
            'maxdd_fu': float(maxdd_fu[i]),
            'pf_fu': float(pf_fu[i]),
            'score_fu': float(score_fu[i]),
            'robustness': float(robustness[i]),
            'combined_score': float(combined_score[i]),
            'cancels_tr': int(cancels_tr[gi]),
            'cancels_te': int(cancels_te[i]),
            'cancels_fu': int(cancels_fu[i]),
            'preset_key': f"{preset[0]}({preset[1]})/{preset[4]}({preset[5]})",
            'hyst': hyst,
        })

    return pd.DataFrame(rows)


def extract_gems_for_anchor(variant_dfs, extractor, top_n):
    """Combina resultados de todas las variantes y extrae gemas.
    Retorna DataFrame de gemas o None.
    """
    combined = pd.concat(variant_dfs, ignore_index=True)
    if len(combined) == 0:
        return None

    valid = extractor.apply_validation_filter(combined)
    if len(valid) == 0:
        return None

    gem_ids, gem_criteria, config_presets = extractor.extract_gems(valid, top_n)
    if not gem_ids:
        return None

    gems = extractor.build_gem_table(valid, gem_ids, gem_criteria, config_presets)
    gems = extractor.assign_families(gems)
    return gems


# ============================================
# LAB LITE PER ANCHOR
# ============================================

def run_lab_lite_for_anchor(lite, df, anchor, symbol, config):
    """Run lab_lite on the optimization window of an anchor.

    Replicates the scoring/selection logic from lab_lite_zonas_v5d.process_symbol
    but operates on a DataFrame slice instead of downloading data.

    Returns list of preset tuples (12-element) for lab historico, or empty list.
    """
    opt_start = anchor["opt_start"]
    opt_end = anchor["opt_end"]

    # Calculate lab_lite warmup (same as lab_lite: max_period * 3)
    fast_cat_pre, slow_cat_pre, trend_cat_pre = lite.build_catalog()
    max_slow_period = max(p for _, p, _, _ in slow_cat_pre)
    max_trend_period = max((p for _, p, _, _ in trend_cat_pre if p > 0), default=0)
    max_period = max(max_slow_period, max_trend_period)
    lite_warmup = max_period * 3

    # Slice data: warmup + opt window
    data_start = max(0, opt_start - lite_warmup)
    actual_warmup = opt_start - data_start

    df_slice = df.iloc[data_start:opt_end].copy().reset_index(drop=True)

    if len(df_slice) < actual_warmup + 500:
        print(f"    [LITE] Datos insuficientes para lab_lite ({len(df_slice)} velas)")
        return []

    # Precalculate all MAs on slice
    close, fast_arr, slow_arr, trend_arr, fast_cat, slow_cat, trend_cat = lite.precalculate_all_mas(df_slice)
    n_fast, n_slow, n_trend = len(fast_cat), len(slow_cat), len(trend_cat)
    n_configs = n_fast * n_slow * n_trend

    # EMA reference (same constants as lab_lite)
    ema_f = lite.calc_ema(close, lite.EMA_FAST)
    ema_s = lite.calc_ema(close, lite.EMA_SLOW)
    ema_t = lite.calc_ema(close, lite.EMA_TREND)

    commission = config.get("commission", 0.10)

    # v5d: test_start = warmup (TRAIN_RATIO=0.0, measure everything after warmup)
    ema_pnl, ema_trades, ema_raw_crosses = lite.simulate_ema_pnl(
        close, ema_f, ema_s, ema_t, commission, actual_warmup, actual_warmup)

    # Run all candidates
    t0 = time.time()
    cand_pnl, cand_trades, cand_raw_crosses = lite.run_simulation_v5d(
        close, fast_arr, slow_arr, trend_arr,
        n_fast, n_slow, n_trend,
        commission, actual_warmup, actual_warmup)
    elapsed = time.time() - t0

    print(f"    [LITE] {n_configs:,} configs en {elapsed:.1f}s "
          f"(EMA ref: PnL={ema_pnl:+.2f}%, {ema_trades}t)")

    # Scoring (identical to lab_lite process_symbol)
    MIN_TRADES = 10
    valid = cand_trades >= MIN_TRADES

    excess_cross = np.where(ema_raw_crosses > 0,
                            np.maximum(0.0, (cand_raw_crosses.astype(np.float64) - ema_raw_crosses) / ema_raw_crosses),
                            0.0)
    excess_cross = np.minimum(excess_cross, 1.0)
    cross_penalty = 1.0 - 0.3 * excess_cross

    if ema_pnl > 0:
        pnl_ratio = cand_pnl / ema_pnl
    else:
        pnl_ratio = cand_pnl / 10.0

    score = pnl_ratio * cross_penalty
    score_valid = np.where(valid, score, -999.0)

    n_valid = int(np.sum(valid))
    if n_valid == 0:
        print(f"    [LITE] Sin configs validas (0 de {n_configs:,} con >={MIN_TRADES} trades)")
        return []

    sorted_idx = np.argsort(-score_valid)

    # Build top_results (same format as lab_lite)
    top_results = []
    count = 0
    TOP_SAVE = 5000
    for idx in sorted_idx:
        if not valid[idx]:
            continue
        if count >= TOP_SAVE:
            break
        fi = idx // (n_slow * n_trend)
        remainder = idx % (n_slow * n_trend)
        si = remainder // n_trend
        ti = remainder % n_trend
        top_results.append({
            'fast': fast_cat[fi], 'slow': slow_cat[si], 'trend': trend_cat[ti],
            'score': float(score[idx]), 'pnl': float(cand_pnl[idx]),
            'trades': int(cand_trades[idx]),
            'raw_crosses': int(cand_raw_crosses[idx]),
            'excess_cross': float(excess_cross[idx]),
        })
        count += 1

    if not top_results:
        print(f"    [LITE] Sin resultados validos")
        return []

    # Select top presets (same logic as lab_lite)
    top_n = config.get("lite_top_n", 5)
    diversity = config.get("lite_diversity", True)

    if diversity:
        selected = lite.select_top_diverse(top_results, top_n)
    else:
        selected = top_results[:top_n]

    # Convert to preset tuples for lab historico
    presets = [lite.result_to_preset_tuple(res) for res in selected]

    # Print summary
    families = set()
    for r, (res, preset) in enumerate(zip(selected, presets), 1):
        fam = f"{lite.ma_family(res['fast'])}/{lite.ma_family(res['slow'])}"
        families.add(fam)
        print(f"      #{r} Score={res['score']:.4f} PnL={res['pnl']:+.2f}% "
              f"{res['trades']}t | {preset[0]}({preset[1]})/{preset[4]}({preset[5]}) [{fam}]")
    print(f"    [LITE] {len(presets)} presets ({len(families)} familias)")

    return presets


# ============================================
# FASE 1: PROCESO POR SIMBOLO
# ============================================

def process_symbol(symbol, config, output_dir, lab, extractor, lite, presets_dir=None, n_workers=1):
    """Procesa un simbolo completo: todos los puntos de anclaje.
    Ejecuta lab_lite para cada anclaje para descubrir presets optimos del periodo.
    Retorna (gems_df, all_train_df) — all_train_df is None when eval_all_train is False.
    """
    eval_all_train = config.get("eval_all_train", False)
    symbol_clean = sc(symbol)
    checkpoint_path = os.path.join(output_dir, f"checkpoint_{symbol_clean}_v{CHECKPOINT_VERSION}.parquet")
    all_train_checkpoint_path = os.path.join(output_dir, f"checkpoint_{symbol_clean}_all_train_v{CHECKPOINT_VERSION}.parquet")

    # Resume (version-aware: old checkpoints without version suffix are ignored)
    # Only check file existence + read row counts from parquet metadata (zero RAM)
    if os.path.exists(checkpoint_path):
        import pyarrow.parquet as pq
        gem_rows = pq.read_metadata(checkpoint_path).num_rows
        all_train_rows = 0
        if eval_all_train and os.path.exists(all_train_checkpoint_path):
            all_train_rows = pq.read_metadata(all_train_checkpoint_path).num_rows
            print(f"  [RESUME] Checkpoints v{CHECKPOINT_VERSION} encontrados (gems: {gem_rows} + all_train: {all_train_rows:,})")
        else:
            print(f"  [RESUME] Checkpoint v{CHECKPOINT_VERSION} encontrado: {checkpoint_path} ({gem_rows} filas)")
        return (gem_rows, all_train_rows)

    hyst_values = config["hyst_values"]

    # Download/get data
    print(f"  Obteniendo datos...")
    total_needed = config["warmup"] + config["ext_size"] + config["opt_size"] + config["fwd_size"]
    # Need enough for all anchors
    max_needed = total_needed + 10 * config["step"]  # generous
    df = lab.fetch_all_candles(symbol, "1h", max_needed)
    if df is None or len(df) < total_needed:
        print(f"  [SKIP] Datos insuficientes ({len(df) if df is not None else 0} < {total_needed})")
        return None

    n_bars = len(df)
    print(f"  Datos: {n_bars} velas")

    # Compute anchor points
    anchors = compute_anchor_points(
        n_bars, config["opt_size"], config["ext_size"],
        config["fwd_size"], config["step"], config["warmup"])

    if not anchors:
        print(f"  [SKIP] Sin puntos de anclaje posibles")
        return None

    _max_anch = config.get("max_anchors")
    if _max_anch:
        anchors = anchors[:int(_max_anch)]
        print(f"  [SMOKE] max_anchors={_max_anch} -> usando {len(anchors)} anclajes (calibración de recursos)")

    print(f"  Puntos de anclaje: {len(anchors)}")
    for a in anchors:
        print(f"    anchor_{a['anchor_idx']}: ext[{a['ext_start']}:{a['ext_end']}] "
              f"opt[{a['opt_start']}:{a['opt_end']}] fwd[{a['fwd_start']}:{a['fwd_end']}]")

    # Get timestamps for date info
    timestamps = df['timestamp'] if 'timestamp' in df.columns else None

    # Generate all configs ONCE (same for all anchors)
    print(f"\n  Generando configs...")
    all_configs = lab.generate_valid_configs()
    print(f"  {len(all_configs):,} configuraciones")

    # Configure lab parameters
    lab.SL_PERCENT = config["sl_percent"]
    lab.SL_EMERGENCY_PERCENT = config["sl_emergency_percent"]
    lab.TS_PERCENT = config["ts_percent"]
    lab.COOLDOWN_BARS = config["cooldown_bars"]
    lab.COMMISSION_ROUND_TRIP = config["commission"]

    # Create worker pool for indicator precalculation (reused across all anchors)
    pool = None
    if n_workers > 1:
        buf = io.BytesIO()
        df.to_pickle(buf)
        df_pickle_bytes = buf.getvalue()
        buf.close()
        effective_workers = min(n_workers, 20)
        print(f"  Pool de {effective_workers} workers creado para precalculo de indicadores")
        pool = Pool(processes=effective_workers,
                    initializer=_precalc_worker_init,
                    initargs=(df_pickle_bytes,))

    all_symbol_rows = []
    all_train_written_rows = 0  # counter for incremental all_train parquet writes
    all_train_parts_dir = os.path.join(output_dir, f"_parts_all_train_{symbol_clean}")
    if eval_all_train:
        os.makedirs(all_train_parts_dir, exist_ok=True)

    try:
        for anchor in anchors:
            anchor_idx = anchor["anchor_idx"]
            t_anchor = time.time()

            # Date info
            date_opt_start = ""
            date_fwd_end = ""
            if timestamps is not None:
                try:
                    date_opt_start = str(timestamps.iloc[anchor["opt_start"]])[:10]
                    date_fwd_end = str(timestamps.iloc[min(anchor["fwd_end"] - 1, len(timestamps) - 1)])[:10]
                except (IndexError, KeyError):
                    pass

            print(f"\n  {'='*60}")
            print(f"  Anchor {anchor_idx}: opt[{anchor['opt_start']}:{anchor['opt_end']}] "
                  f"fwd[{anchor['fwd_start']}:{anchor['fwd_end']}]"
                  f"{' [' + date_opt_start + ' -> ' + date_fwd_end + ']' if date_opt_start else ''}")

            # ---- Step 1: Run lab_lite to discover presets for THIS anchor ----
            print(f"  Step 1: Lab Lite (descubriendo presets optimos para este anclaje)...")
            presets = run_lab_lite_for_anchor(lite, df, anchor, symbol, config)
            if not presets:
                print(f"  [SKIP] Lab lite sin presets para anchor {anchor_idx}")
                continue

            # ---- Step 2: Precalculate indicators for THESE presets ----
            n_variants = len(presets) * len(hyst_values)
            print(f"  Step 2: Precalculando indicadores ({len(presets)} presets x {len(hyst_values)} hyst = {n_variants} variantes)...")
            precomputed = {}  # (preset_key, hyst) -> (data_dict, preset_tuple, cuda_handle)

            if pool is not None and n_variants > 1:
                # Parallel precalculation using persistent pool
                tasks = [(preset, hyst, symbol)
                         for preset in presets for hyst in hyst_values]
                t_precalc = time.time()
                results = pool.map(_precalc_worker, tasks)
                print(f"    Precalculo paralelo: {time.time()-t_precalc:.1f}s")

                # Upload to GPU sequentially in main process
                for preset_key, hyst, data, preset_tuple, elapsed in results:
                    gk = (preset_key, hyst)
                    cuda_handle = None
                    if USE_CUDA and _cuda_sim is not None:
                        try:
                            cuda_handle = _cuda_sim.upload_data(data)
                        except Exception as e_gpu:
                            print(f"    {preset_key} H{hyst:.1f}: GPU upload failed: {e_gpu}")
                    precomputed[gk] = (data, preset_tuple, cuda_handle)
            else:
                # Sequential precalculation
                for preset in presets:
                    for hyst in hyst_values:
                        preset_key = f"{preset[0]}({preset[1]})/{preset[4]}({preset[5]})"
                        gk = (preset_key, hyst)
                        t0 = time.time()
                        data = lab.precalculate_all_data(df, preset=preset, hyst_mult=hyst, symbol=symbol)
                        cuda_handle = None
                        if USE_CUDA and _cuda_sim is not None:
                            try:
                                cuda_handle = _cuda_sim.upload_data(data)
                                print(f"    {preset_key} H{hyst:.1f}: {time.time()-t0:.1f}s [GPU]")
                            except Exception as e_gpu:
                                print(f"    {preset_key} H{hyst:.1f}: {time.time()-t0:.1f}s [GPU failed: {e_gpu}]")
                        else:
                            print(f"    {preset_key} H{hyst:.1f}: {time.time()-t0:.1f}s [CPU]")
                        precomputed[gk] = (data, preset, cuda_handle)

            # ---- Step 3: Run lab on 5k window for each variant ----
            # When eval_all_train, fwd evaluation + part-file writing is fused
            # into this loop so each variant is processed and freed before the next.
            # Peak RAM: ~1 variant (≤250K rows) instead of all 20 (≤5M rows).
            variant_dfs = []
            variant_idx = 0
            at_anchor_rows = 0
            part_variant_idx = 0
            for p_idx, preset in enumerate(presets):
                for hyst in hyst_values:
                    variant_idx += 1
                    preset_key = f"{preset[0]}({preset[1]})/{preset[4]}({preset[5]})"
                    hyst_tag = f"H{hyst:.1f}".replace(".", "")
                    ma_info_str = f"{preset_key} {hyst_tag}"
                    variant_tag = f"v{variant_idx:02d}_{hyst_tag}"

                    gk = (preset_key, hyst)
                    data_dict, _, cuda_h = precomputed[gk]

                    t0 = time.time()
                    vdf = run_lab_on_window(
                        all_configs, data_dict,
                        anchor["opt_start"], anchor["opt_end"],
                        lab, preset, hyst, ma_info_str, variant_tag,
                        cuda_handle=cuda_h, eval_all_train=eval_all_train)

                    if vdf is not None and len(vdf) > 0:
                        elapsed = time.time() - t0

                        if eval_all_train:
                            # Keep only top configs for gem extraction (Step 4)
                            gem_vdf = vdf.nlargest(TOP_TRAIN, 'combined_score')
                            variant_dfs.append(gem_vdf)

                            # Fused Step 3b: eval forward + write part-file immediately
                            n_written = _eval_one_variant_fwd(
                                vdf, gk, precomputed, lab, anchor, config,
                                all_train_parts_dir, anchor_idx, part_variant_idx)
                            at_anchor_rows += n_written
                            part_variant_idx += 1

                            del vdf
                            gc.collect()
                            print(f"    {ma_info_str}: {n_written} -> fwd+parquet, "
                                  f"{len(gem_vdf)} kept for gems ({elapsed:.1f}s)")
                        else:
                            variant_dfs.append(vdf)
                            print(f"    {ma_info_str}: {len(vdf)} configs ({elapsed:.1f}s)")
                    else:
                        print(f"    {ma_info_str}: sin configs validas")

            if eval_all_train and at_anchor_rows > 0:
                print(f"  Step 3 (fused): {at_anchor_rows:,} configs evaluadas en fwd")

            if not variant_dfs:
                print(f"  [SKIP] Sin variantes validas para anchor {anchor_idx}")
                continue

            # ---- Step 4: Extract gems ----
            print(f"\n  Step 4: Extrayendo gemas (top_n={config['extractor_top_n']})...")
            gems = extract_gems_for_anchor(variant_dfs, extractor, config["extractor_top_n"])
            if gems is None or len(gems) == 0:
                print(f"  [SKIP] Sin gemas para anchor {anchor_idx}")
                # Add id columns to existing part-files (no gem merge needed)
                if eval_all_train and at_anchor_rows > 0:
                    _patch_all_train_parts(all_train_parts_dir, anchor_idx,
                                           symbol, date_opt_start, date_fwd_end,
                                           gem_lookup=None)
                    all_train_written_rows += at_anchor_rows
                    print(f"  Anchor {anchor_idx}: {at_anchor_rows:,} all-train obs (sin gemas)")
                continue

            print(f"  {len(gems)} gemas extraidas")

            # ---- Step 5: Evaluate gems on all slices ----
            print(f"  Step 5: Evaluando gemas en tramos (opt/ext/fwd/h1/h2/7k/q1-q4)...")
            t0 = time.time()
            rows = evaluate_gems_on_slices_optimized(gems, precomputed, lab, anchor, config)
            print(f"  {len(rows)} observaciones ({time.time()-t0:.1f}s)")

            # Add identification columns
            for row in rows:
                row['symbol'] = symbol
                row['anchor_idx'] = anchor_idx
                row['date_opt_start'] = date_opt_start
                row['date_fwd_end'] = date_fwd_end

            all_symbol_rows.extend(rows)

            # ---- Merge gem info into all_train part-files ----
            if eval_all_train and at_anchor_rows > 0:
                # Build lookup of gem slice data by (config_id, ma_info)
                gem_lookup = {}
                for gem_row in rows:
                    key = (gem_row['config_id'], gem_row['ma_info'])
                    gem_lookup[key] = gem_row

                _patch_all_train_parts(all_train_parts_dir, anchor_idx,
                                       symbol, date_opt_start, date_fwd_end,
                                       gem_lookup=gem_lookup)
                all_train_written_rows += at_anchor_rows

            print(f"  Anchor {anchor_idx}: {len(rows)} gem obs"
                  + (f" + {all_train_written_rows:,} all-train obs (acum)" if eval_all_train else "")
                  + f" ({time.time()-t_anchor:.1f}s)")

    finally:
        if pool is not None:
            pool.close()
            pool.join()

    if not all_symbol_rows:
        print(f"  Sin observaciones (gems) para {symbol}")
        gems_df = None
    else:
        gems_df = pd.DataFrame(all_symbol_rows)
        gems_df = compute_regime_columns(gems_df, inplace=True)
        gems_df.to_parquet(checkpoint_path, index=False)
        print(f"\n  Checkpoint gems: {checkpoint_path} ({len(gems_df)} filas)")

    # Save all-train checkpoint — stream part files through ParquetWriter (one chunk in RAM at a time)
    at_rows = 0
    if eval_all_train and all_train_written_rows > 0:
        import glob as _glob
        import pyarrow as pa
        import pyarrow.parquet as pq
        part_files = sorted(_glob.glob(os.path.join(all_train_parts_dir, "part_*.parquet")))
        if part_files:
            writer = None
            for pf in part_files:
                chunk_df = pd.read_parquet(pf)
                chunk_df = compute_regime_columns(chunk_df, inplace=True)
                table = pa.Table.from_pandas(chunk_df, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(all_train_checkpoint_path, table.schema)
                writer.write_table(table)
                at_rows += len(chunk_df)
                del chunk_df, table
                gc.collect()
            if writer:
                writer.close()
            print(f"  Checkpoint all-train: {all_train_checkpoint_path} ({at_rows:,} filas)")
            # Cleanup part files
            for pf in part_files:
                os.remove(pf)
            try:
                os.rmdir(all_train_parts_dir)
            except OSError:
                pass
    elif eval_all_train:
        print(f"  Sin observaciones all-train para {symbol}")
        # Cleanup empty parts dir
        try:
            os.rmdir(all_train_parts_dir)
        except OSError:
            pass

    gem_rows = len(gems_df) if gems_df is not None else 0
    del gems_df
    return (gem_rows, at_rows)


# ============================================
# FASE 2: ETIQUETADO
# ============================================

def label_dataset(df, config):
    """Etiqueta cada gema por rendimiento forward relativo al contexto."""
    df = df.copy()

    # fwd_alpha: rendimiento config - rendimiento buy&hold
    df['fwd_alpha'] = df['fwd_pnl'] - df['asset_return_fwd']

    # fwd_label
    alpha_good = config.get("alpha_good", 2.0)
    alpha_bad = config.get("alpha_bad", -2.0)
    pf_good = config.get("pf_good", 1.2)
    pf_bad = config.get("pf_bad", 0.8)

    conditions_buena = (df['fwd_alpha'] > alpha_good) & (df['fwd_pf'] > pf_good)
    conditions_mala = (df['fwd_alpha'] < alpha_bad) | (df['fwd_pf'] < pf_bad)

    df['fwd_label'] = 'NEUTRA'
    df.loc[conditions_buena, 'fwd_label'] = 'BUENA'
    df.loc[conditions_mala, 'fwd_label'] = 'MALA'

    print(f"\n  Etiquetado:")
    for label in ['BUENA', 'NEUTRA', 'MALA']:
        n = (df['fwd_label'] == label).sum()
        print(f"    {label}: {n} ({100*n/len(df):.1f}%)")

    return df


# ============================================
# FASE 3: ANALISIS
# ============================================

def run_analysis(df, output_dir):
    """Ejecuta analisis completo sobre el dataset etiquetado."""
    L = []
    L.append(f"{'='*100}")
    L.append(f"WALK-FORWARD EXPERIMENT — ANALISIS DE PATRONES")
    L.append(f"{'='*100}")
    L.append(f"Observaciones: {len(df)}")
    L.append(f"Simbolos: {df['symbol'].nunique()}")
    L.append(f"Anchors por simbolo: {df.groupby('symbol')['anchor_idx'].nunique().to_dict()}")
    L.append(f"Gemas unicas: {df['config_id'].nunique()}")
    L.append(f"Distribucion labels: {df['fwd_label'].value_counts().to_dict()}")
    L.append("")

    # ---- 1. Correlaciones globales ----
    L.append(f"\n{'~'*100}")
    L.append(f"1. CORRELACIONES GLOBALES: Features vs Forward")
    L.append(f"{'~'*100}")

    features = [
        'opt_pnl', 'opt_pf', 'opt_trades', 'opt_maxdd', 'opt_wr', 'opt_pnl_ann',
        'ext_pnl', 'ext_pf', 'ext_trades', 'ext_maxdd', 'ext_wr',
        'combined_7k_pf', 'combined_7k_dd', 'combined_7k_pnl', 'combined_7k_trades',
        'delta_pf_opt_7k', 'delta_dd_opt_7k',
        'asset_return_ext', 'asset_volatility_ext', 'asset_maxdd_ext',
        'n_criterios',
    ]
    targets = ['fwd_pnl', 'fwd_pf', 'fwd_alpha', 'fwd_h1_pnl', 'fwd_h2_pnl',
               'fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl']

    # Build correlation table
    corr_rows = []
    for feat in features:
        if feat not in df.columns:
            continue
        row_data = {'feature': feat}
        for tgt in targets:
            if tgt not in df.columns:
                row_data[tgt] = np.nan
                continue
            valid = df[[feat, tgt]].dropna()
            if len(valid) < 10:
                row_data[tgt] = np.nan
            else:
                row_data[tgt] = valid[feat].corr(valid[tgt])
        corr_rows.append(row_data)

    corr_df = pd.DataFrame(corr_rows).set_index('feature')
    corr_df['max_abs_r'] = corr_df[targets].abs().max(axis=1)
    corr_df = corr_df.sort_values('max_abs_r', ascending=False)

    # Save CSV
    corr_csv = os.path.join(output_dir, "analysis_correlations.csv")
    corr_df.to_csv(corr_csv)

    # Print table
    L.append(f"\n  {'Feature':<30s} | " + " | ".join(f"{t:>12s}" for t in targets) + " | max|r|")
    L.append(f"  {'-'*30}-+-" + "-+-".join(f"{'-'*12}" for _ in targets) + "-+-------")
    for feat, row in corr_df.iterrows():
        vals = []
        for t in targets:
            v = row[t]
            if np.isnan(v):
                vals.append("          --")
            else:
                star = " **" if abs(v) > 0.3 else " *" if abs(v) > 0.15 else ""
                vals.append(f"{v:>+9.3f}{star}")
        L.append(f"  {feat:<30s} | " + " | ".join(f"{v:>12s}" for v in vals) +
                 f" | {row['max_abs_r']:.3f}")

    L.append(f"\n  (* |r|>0.15, ** |r|>0.30)")

    # ---- 2. Comparacion filtro actual vs realidad ----
    L.append(f"\n{'~'*100}")
    L.append(f"2. COMPARACION FILTRO ACTUAL (pasa_7k) VS REALIDAD")
    L.append(f"{'~'*100}")

    if 'pasa_7k' in df.columns and 'fwd_label' in df.columns:
        # Confusion matrix
        for pasa in [True, False]:
            subset = df[df['pasa_7k'] == pasa]
            n = len(subset)
            if n == 0:
                continue
            buenas = (subset['fwd_label'] == 'BUENA').sum()
            malas = (subset['fwd_label'] == 'MALA').sum()
            neutras = (subset['fwd_label'] == 'NEUTRA').sum()
            avg_alpha = subset['fwd_alpha'].mean()
            avg_fwd_pnl = subset['fwd_pnl'].mean()
            label = "PASAN 7k" if pasa else "NO pasan 7k"
            L.append(f"\n  {label}: {n} observaciones")
            L.append(f"    BUENA: {buenas} ({100*buenas/n:.1f}%) | NEUTRA: {neutras} ({100*neutras/n:.1f}%) | MALA: {malas} ({100*malas/n:.1f}%)")
            L.append(f"    Avg alpha: {avg_alpha:+.2f}% | Avg fwd_pnl: {avg_fwd_pnl:+.2f}%")

        # False negatives: BUENAS que no pasan
        buenas_total = (df['fwd_label'] == 'BUENA').sum()
        buenas_pasan = ((df['fwd_label'] == 'BUENA') & (df['pasa_7k'] == True)).sum()
        if buenas_total > 0:
            L.append(f"\n  Falsos negativos: {buenas_total - buenas_pasan}/{buenas_total} BUENAS no pasan 7k "
                     f"({100*(buenas_total - buenas_pasan)/buenas_total:.1f}%)")

        # Accuracy
        pasan = df[df['pasa_7k'] == True]
        if len(pasan) > 0:
            precision = (pasan['fwd_label'] == 'BUENA').sum() / len(pasan)
            L.append(f"  Precision filtro pasa_7k: {precision:.1%} de las que pasan son BUENA")

    # ---- 3. Analisis por preset/MA ----
    L.append(f"\n{'~'*100}")
    L.append(f"3. ANALISIS POR PRESET/MA")
    L.append(f"{'~'*100}")

    if 'ma_info' in df.columns:
        preset_stats = df.groupby('ma_info').agg(
            n=('fwd_pnl', 'count'),
            avg_fwd_pnl=('fwd_pnl', 'mean'),
            avg_fwd_alpha=('fwd_alpha', 'mean'),
            avg_fwd_pf=('fwd_pf', 'mean'),
            pct_buena=('fwd_label', lambda x: (x == 'BUENA').mean() * 100),
            pct_mala=('fwd_label', lambda x: (x == 'MALA').mean() * 100),
        ).sort_values('avg_fwd_alpha', ascending=False)

        L.append(f"\n  {'Preset':<35s} | {'N':>4s} | {'AvgAlpha':>9s} | {'AvgPnL':>8s} | {'AvgPF':>6s} | {'%Buena':>7s} | {'%Mala':>6s}")
        L.append(f"  {'-'*35}-+-{'-'*4}-+-{'-'*9}-+-{'-'*8}-+-{'-'*6}-+-{'-'*7}-+-{'-'*6}")
        for preset, row in preset_stats.iterrows():
            L.append(f"  {preset:<35s} | {int(row['n']):>4d} | {row['avg_fwd_alpha']:>+8.2f}% | "
                     f"{row['avg_fwd_pnl']:>+7.2f}% | {row['avg_fwd_pf']:>5.2f} | "
                     f"{row['pct_buena']:>6.1f}% | {row['pct_mala']:>5.1f}%")

    # ---- 4. Analisis por contexto de mercado ----
    L.append(f"\n{'~'*100}")
    L.append(f"4. ANALISIS POR CONTEXTO DE MERCADO")
    L.append(f"{'~'*100}")

    if 'asset_return_fwd' in df.columns and len(df) >= 30:
        terciles = df['asset_return_fwd'].quantile([0.33, 0.66])
        df_copy = df.copy()
        df_copy['market_regime'] = pd.cut(
            df_copy['asset_return_fwd'],
            bins=[-np.inf, terciles.iloc[0], terciles.iloc[1], np.inf],
            labels=['BEAR', 'NEUTRAL', 'BULL']
        )

        for regime in ['BEAR', 'NEUTRAL', 'BULL']:
            subset = df_copy[df_copy['market_regime'] == regime]
            if len(subset) < 5:
                continue
            L.append(f"\n  {regime} (N={len(subset)}, asset_return: "
                     f"{subset['asset_return_fwd'].min():.1f}% to {subset['asset_return_fwd'].max():.1f}%):")

            # Top correlated features in this regime
            regime_corrs = []
            for feat in features:
                if feat not in subset.columns:
                    continue
                valid = subset[['fwd_alpha', feat]].dropna()
                if len(valid) < 5:
                    continue
                r = valid[feat].corr(valid['fwd_alpha'])
                if not np.isnan(r):
                    regime_corrs.append((feat, r))

            regime_corrs.sort(key=lambda x: abs(x[1]), reverse=True)
            for feat, r in regime_corrs[:5]:
                star = "**" if abs(r) > 0.3 else "*" if abs(r) > 0.15 else ""
                L.append(f"    {feat:<30s} vs fwd_alpha: r={r:+.3f} {star}")

    # ---- 5. Feature importance (Decision Tree) ----
    L.append(f"\n{'~'*100}")
    L.append(f"5. FEATURE IMPORTANCE (Decision Tree)")
    L.append(f"{'~'*100}")

    tree_rules = ""
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.preprocessing import LabelEncoder

        feature_cols = [f for f in features if f in df.columns]
        X = df[feature_cols].copy()
        y = df['fwd_label'].copy()

        # Drop rows with NaN
        mask = X.notna().all(axis=1) & y.notna()
        X = X[mask]
        y = y[mask]

        if len(X) >= 100:
            le = LabelEncoder()
            y_enc = le.fit_transform(y)

            clf = DecisionTreeClassifier(max_depth=5, min_samples_leaf=max(10, len(X) // 50),
                                         class_weight='balanced', random_state=42)
            clf.fit(X, y_enc)

            # Feature importances
            importances = pd.Series(clf.feature_importances_, index=feature_cols)
            importances = importances.sort_values(ascending=False)

            L.append(f"\n  Feature importances (top 15):")
            for feat, imp in importances.head(15).items():
                if imp > 0.001:
                    L.append(f"    {feat:<30s}: {imp:.4f}")

            # Tree rules
            tree_rules = export_text(clf, feature_names=feature_cols,
                                     class_names=list(le.classes_))
            L.append(f"\n  Reglas del arbol (max_depth=5):")
            for line in tree_rules.split('\n')[:50]:
                L.append(f"    {line}")

            # Cross-validation accuracy estimate
            from sklearn.model_selection import cross_val_score
            scores = cross_val_score(clf, X, y_enc, cv=min(5, len(X) // 20), scoring='accuracy')
            L.append(f"\n  Accuracy (5-fold CV): {scores.mean():.3f} +/- {scores.std():.3f}")
            L.append(f"  Baseline (mayoria): {max(np.bincount(y_enc)) / len(y_enc):.3f}")
        else:
            L.append(f"\n  Insuficientes observaciones ({len(X)}) para arbol de decision (min 100)")
    except ImportError:
        L.append(f"\n  sklearn no instalado — saltando arbol de decision")
        L.append(f"  Instalar: pip install scikit-learn")

    # ---- 6. Propuesta de filtros alternativos ----
    L.append(f"\n{'~'*100}")
    L.append(f"6. PROPUESTA DE FILTROS ALTERNATIVOS")
    L.append(f"{'~'*100}")

    if len(df) >= 30:
        # Find features most correlated with fwd_alpha
        alpha_corrs = []
        for feat in features:
            if feat not in df.columns:
                continue
            valid = df[['fwd_alpha', feat]].dropna()
            if len(valid) < 10:
                continue
            r = valid[feat].corr(valid['fwd_alpha'])
            if not np.isnan(r) and abs(r) > 0.1:
                alpha_corrs.append((feat, r))

        alpha_corrs.sort(key=lambda x: abs(x[1]), reverse=True)

        # Candidate filter 1: Best single feature
        if alpha_corrs:
            best_feat, best_r = alpha_corrs[0]
            direction = "alto" if best_r > 0 else "bajo"
            # Find threshold that maximizes % BUENA
            feat_vals = df[best_feat].dropna()
            if len(feat_vals) > 0:
                median_val = feat_vals.median()
                if best_r > 0:
                    mask = df[best_feat] >= median_val
                else:
                    mask = df[best_feat] <= median_val
                subset = df[mask]
                pct_buena = (subset['fwd_label'] == 'BUENA').sum() / len(subset) * 100 if len(subset) > 0 else 0
                pct_mala = (subset['fwd_label'] == 'MALA').sum() / len(subset) * 100 if len(subset) > 0 else 0
                L.append(f"\n  Filtro 1: {best_feat} {'>' if best_r > 0 else '<'} {median_val:.2f}")
                L.append(f"    r={best_r:+.3f} | N={len(subset)} | %BUENA={pct_buena:.1f}% | %MALA={pct_mala:.1f}%")

        # Candidate filter 2: Combined with pasa_7k
        if 'pasa_7k' in df.columns and len(alpha_corrs) >= 2:
            feat2, r2 = alpha_corrs[1]
            feat_vals = df[feat2].dropna()
            if len(feat_vals) > 0:
                med2 = feat_vals.median()
                if r2 > 0:
                    mask = (df['pasa_7k'] == True) & (df[feat2] >= med2)
                else:
                    mask = (df['pasa_7k'] == True) & (df[feat2] <= med2)
                subset = df[mask]
                pct_buena = (subset['fwd_label'] == 'BUENA').sum() / len(subset) * 100 if len(subset) > 0 else 0
                pct_mala = (subset['fwd_label'] == 'MALA').sum() / len(subset) * 100 if len(subset) > 0 else 0
                L.append(f"\n  Filtro 2: pasa_7k AND {feat2} {'>' if r2 > 0 else '<'} {med2:.2f}")
                L.append(f"    r={r2:+.3f} | N={len(subset)} | %BUENA={pct_buena:.1f}% | %MALA={pct_mala:.1f}%")

        # Candidate filter 3: Relaxed 7k + multi-feature
        if len(alpha_corrs) >= 3:
            top3_feats = [(f, r) for f, r in alpha_corrs[:3]]
            conditions = []
            desc_parts = []
            for feat, r in top3_feats:
                if feat not in df.columns:
                    continue
                med = df[feat].dropna().median()
                if r > 0:
                    conditions.append(df[feat] >= med)
                    desc_parts.append(f"{feat}>={med:.2f}")
                else:
                    conditions.append(df[feat] <= med)
                    desc_parts.append(f"{feat}<={med:.2f}")

            if conditions:
                mask = conditions[0]
                for c in conditions[1:]:
                    mask = mask & c
                subset = df[mask]
                pct_buena = (subset['fwd_label'] == 'BUENA').sum() / len(subset) * 100 if len(subset) > 0 else 0
                pct_mala = (subset['fwd_label'] == 'MALA').sum() / len(subset) * 100 if len(subset) > 0 else 0
                L.append(f"\n  Filtro 3: {' AND '.join(desc_parts)}")
                L.append(f"    N={len(subset)} | %BUENA={pct_buena:.1f}% | %MALA={pct_mala:.1f}%")

        # Compare all filters
        L.append(f"\n  Comparacion con filtro actual (pasa_7k):")
        if 'pasa_7k' in df.columns:
            pasan = df[df['pasa_7k'] == True]
            if len(pasan) > 0:
                pct_b = (pasan['fwd_label'] == 'BUENA').sum() / len(pasan) * 100
                pct_m = (pasan['fwd_label'] == 'MALA').sum() / len(pasan) * 100
                L.append(f"    Filtro actual (pasa_7k): N={len(pasan)} | %BUENA={pct_b:.1f}% | %MALA={pct_m:.1f}%")
    else:
        L.append(f"\n  Insuficientes observaciones ({len(df)}) para propuesta de filtros")

    # ---- 7. Analisis de cuartos forward ----
    q_cols = ['fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl']
    has_quarters = all(c in df.columns for c in q_cols)

    if has_quarters:
        L.append(f"\n{'~'*100}")
        L.append(f"7. ANALISIS DE CUARTOS FORWARD (Q1-Q4)")
        L.append(f"{'~'*100}")

        # 7a. Promedio PnL por cuarto
        L.append(f"\n  7a. PROMEDIO PnL POR CUARTO")
        L.append(f"  {'-'*40}")
        for q in range(1, 5):
            col = f'fwd_q{q}_pnl'
            valid = df[col].dropna()
            if len(valid) > 0:
                L.append(f"    Q{q}: mean={valid.mean():.4f}  median={valid.median():.4f}  std={valid.std():.4f}")

        # By label
        L.append("")
        for label in ['BUENA', 'NEUTRA', 'MALA']:
            subset = df[df['fwd_label'] == label]
            if len(subset) == 0:
                continue
            L.append(f"    [{label}] (N={len(subset)})")
            for q in range(1, 5):
                col = f'fwd_q{q}_pnl'
                valid = subset[col].dropna()
                if len(valid) > 0:
                    L.append(f"      Q{q}: mean={valid.mean():.4f}  median={valid.median():.4f}")

        # 7b. % rentables por cuarto
        L.append(f"\n  7b. % OBSERVACIONES RENTABLES POR CUARTO")
        L.append(f"  {'-'*40}")
        for q in range(1, 5):
            col = f'fwd_q{q}_pnl'
            valid = df[col].dropna()
            if len(valid) > 0:
                pct = (valid > 0).mean() * 100
                L.append(f"    Q{q}: {pct:.1f}% rentables ({(valid > 0).sum()}/{len(valid)})")

        for label in ['BUENA', 'NEUTRA', 'MALA']:
            subset = df[df['fwd_label'] == label]
            if len(subset) == 0:
                continue
            L.append(f"    [{label}]")
            for q in range(1, 5):
                col = f'fwd_q{q}_pnl'
                valid = subset[col].dropna()
                pct = (valid > 0).mean() * 100 if len(valid) > 0 else 0
                L.append(f"      Q{q}: {pct:.1f}% rentables")

        # 7c. Patrones de degradacion
        has_all_q = df[q_cols].notna().all(axis=1)
        dv = df[has_all_q].copy()

        L.append(f"\n  7c. PATRONES DE DEGRADACION (N={len(dv)})")
        L.append(f"  {'-'*40}")

        if len(dv) > 0:
            q1_pos = dv['fwd_q1_pnl'] > 0
            q4_pos = dv['fwd_q4_pnl'] > 0
            q12_pos = (dv['fwd_q1_pnl'] + dv['fwd_q2_pnl']) > 0
            q34_pos = (dv['fwd_q3_pnl'] + dv['fwd_q4_pnl']) > 0

            L.append(f"    Rentables en Q1 pero no en Q4: {(q1_pos & ~q4_pos).sum()} ({(q1_pos & ~q4_pos).mean()*100:.1f}%)")
            L.append(f"    Rentables en Q4 pero no en Q1: {(~q1_pos & q4_pos).sum()} ({(~q1_pos & q4_pos).mean()*100:.1f}%)")
            L.append(f"    Rentables en Q1+Q2 pero no en Q3+Q4: {(q12_pos & ~q34_pos).sum()} ({(q12_pos & ~q34_pos).mean()*100:.1f}%)")
            L.append(f"    Rentables en Q3+Q4 pero no en Q1+Q2: {(~q12_pos & q34_pos).sum()} ({(~q12_pos & q34_pos).mean()*100:.1f}%)")
            L.append(f"    Rentables en todos los cuartos: {(q1_pos & q4_pos & (dv['fwd_q2_pnl']>0) & (dv['fwd_q3_pnl']>0)).sum()}")
            L.append(f"    No rentables en ningun cuarto: {(~q1_pos & ~q4_pos & (dv['fwd_q2_pnl']<=0) & (dv['fwd_q3_pnl']<=0)).sum()}")

        # 7d. Correlaciones entre cuartos
        L.append(f"\n  7d. CORRELACIONES ENTRE CUARTOS")
        L.append(f"  {'-'*40}")

        if len(dv) > 100:
            for q1 in range(1, 5):
                row_str = f"    Q{q1}:"
                for q2 in range(1, 5):
                    corr = dv[f'fwd_q{q1}_pnl'].corr(dv[f'fwd_q{q2}_pnl'])
                    row_str += f" Q{q2}={corr:+.3f}"
                L.append(row_str)

            means = [dv[f'fwd_q{q}_pnl'].mean() for q in range(1, 5)]
            monotonic_decay = all(means[i] >= means[i+1] for i in range(3))
            L.append(f"\n    Decae monotonicamente? {'SI' if monotonic_decay else 'NO'}")
            L.append(f"    Means: Q1={means[0]:.4f} Q2={means[1]:.4f} Q3={means[2]:.4f} Q4={means[3]:.4f}")

        # 7e. Re-etiquetado con Q1
        L.append(f"\n  7e. RE-ETIQUETADO USANDO SOLO Q1 COMO FORWARD")
        L.append(f"  {'-'*40}")

        if 'asset_return_fwd' in dv.columns and len(dv) > 0:
            q1_alpha = dv['fwd_q1_pnl'] - dv['asset_return_fwd'] / 4
            q1_pf_col = 'fwd_q1_pf' if 'fwd_q1_pf' in dv.columns else None

            if q1_pf_col:
                q1_buena = (q1_alpha > 2.0) & (dv[q1_pf_col] > 1.2)
                q1_mala = (q1_alpha < -2.0) | (dv[q1_pf_col] < 0.8)
            else:
                q1_buena = q1_alpha > 2.0
                q1_mala = q1_alpha < -2.0
            q1_neutra = ~q1_buena & ~q1_mala

            L.append(f"    Q1-only labels: BUENA={q1_buena.sum()} ({q1_buena.mean()*100:.1f}%)  "
                     f"NEUTRA={q1_neutra.sum()} ({q1_neutra.mean()*100:.1f}%)  "
                     f"MALA={q1_mala.sum()} ({q1_mala.mean()*100:.1f}%)")

            orig_buena = (dv['fwd_label'] == 'BUENA').sum()
            orig_mala = (dv['fwd_label'] == 'MALA').sum()
            L.append(f"    Original labels: BUENA={orig_buena} ({orig_buena/len(dv)*100:.1f}%)  "
                     f"MALA={orig_mala} ({orig_mala/len(dv)*100:.1f}%)")

        # 7f. Re-etiquetado con Q1+Q2
        L.append(f"\n  7f. RE-ETIQUETADO USANDO Q1+Q2 COMO FORWARD")
        L.append(f"  {'-'*40}")

        if 'asset_return_fwd' in dv.columns and len(dv) > 0:
            q12_pnl = dv['fwd_q1_pnl'] + dv['fwd_q2_pnl']
            q12_gp = dv[['fwd_q1_pnl', 'fwd_q2_pnl']].clip(lower=0).sum(axis=1)
            q12_gl = (-dv[['fwd_q1_pnl', 'fwd_q2_pnl']].clip(upper=0)).sum(axis=1)
            q12_pf = np.where(q12_gl > 0, q12_gp / q12_gl, np.where(q12_gp > 0, 5.0, 0.0))
            q12_alpha = q12_pnl - dv['asset_return_fwd'] / 2

            q12_buena = (q12_alpha > 2.0) & (q12_pf > 1.2)
            q12_mala = (q12_alpha < -2.0) | (q12_pf < 0.8)
            q12_neutra = ~q12_buena & ~q12_mala

            L.append(f"    Q1+Q2 labels: BUENA={q12_buena.sum()} ({q12_buena.mean()*100:.1f}%)  "
                     f"NEUTRA={q12_neutra.sum()} ({q12_neutra.mean()*100:.1f}%)  "
                     f"MALA={q12_mala.sum()} ({q12_mala.mean()*100:.1f}%)")

        # 7g. Presets mas durables
        L.append(f"\n  7g. PRESETS MAS DURABLES (edge en mas cuartos)")
        L.append(f"  {'-'*40}")

        if 'ma_info' in df.columns and len(dv) > 0:
            def get_preset_family(ma_info):
                parts = ma_info.rsplit(' ', 1)
                return parts[0].strip() if len(parts) > 1 else ma_info

            dv_a = dv.copy()
            dv_a['preset_family'] = dv_a['ma_info'].apply(get_preset_family)

            preset_stats_q = []
            for preset, group in dv_a.groupby('preset_family'):
                if len(group) < 10:
                    continue
                means = [group[f'fwd_q{q}_pnl'].mean() for q in range(1, 5)]
                pct_prof = [(group[f'fwd_q{q}_pnl'] > 0).mean() * 100 for q in range(1, 5)]
                n_prof_q = sum(1 for m in means if m > 0)
                preset_stats_q.append({
                    'preset': preset, 'n': len(group),
                    'q1_mean': means[0], 'q2_mean': means[1],
                    'q3_mean': means[2], 'q4_mean': means[3],
                    'n_profitable_q': n_prof_q,
                    'q1_pct': pct_prof[0], 'q4_pct': pct_prof[3],
                })

            preset_stats_q.sort(key=lambda x: x['n_profitable_q'], reverse=True)

            L.append(f"    {len(preset_stats_q)} presets con >= 10 observaciones")
            L.append("")
            L.append(f"    TOP 10 PRESETS MAS DURABLES:")
            for ps in preset_stats_q[:10]:
                L.append(f"      {ps['preset']} (N={ps['n']}) Q_rentables={ps['n_profitable_q']}")
                L.append(f"        means: Q1={ps['q1_mean']:+.3f} Q2={ps['q2_mean']:+.3f} Q3={ps['q3_mean']:+.3f} Q4={ps['q4_mean']:+.3f}")
                L.append(f"        %prof: Q1={ps['q1_pct']:.0f}% Q4={ps['q4_pct']:.0f}%")

            L.append("")
            L.append(f"    BOTTOM 10 PRESETS (edge decae rapido):")
            for ps in preset_stats_q[-10:]:
                L.append(f"      {ps['preset']} (N={ps['n']}) Q_rentables={ps['n_profitable_q']}")
                L.append(f"        means: Q1={ps['q1_mean']:+.3f} Q2={ps['q2_mean']:+.3f} Q3={ps['q3_mean']:+.3f} Q4={ps['q4_mean']:+.3f}")

        # 7h. Sanity check
        L.append(f"\n  7h. SANITY CHECK: SUM(Q1..Q4) vs FWD_PNL")
        L.append(f"  {'-'*40}")

        if 'fwd_pnl' in df.columns:
            valid_sc = df[has_all_q & df['fwd_pnl'].notna()].copy()
            if len(valid_sc) > 0:
                q_sum = valid_sc['fwd_q1_pnl'] + valid_sc['fwd_q2_pnl'] + valid_sc['fwd_q3_pnl'] + valid_sc['fwd_q4_pnl']
                diff = q_sum - valid_sc['fwd_pnl']
                L.append(f"    N observaciones: {len(valid_sc)}")
                L.append(f"    Diferencia (sum_quarters - fwd_pnl):")
                L.append(f"      mean: {diff.mean():.6f}")
                L.append(f"      std:  {diff.std():.6f}")
                L.append(f"      max abs: {diff.abs().max():.6f}")
                L.append(f"      corr(sum_q, fwd_pnl): {q_sum.corr(valid_sc['fwd_pnl']):.6f}")
                pct_close = (diff.abs() < 1.0).mean() * 100
                L.append(f"      % con diff < 1.0: {pct_close:.1f}%")

    # Save report
    report_text = '\n'.join(L)
    report_path = os.path.join(output_dir, "analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n  Reporte: {report_path}")

    # Save tree rules
    if tree_rules:
        tree_path = os.path.join(output_dir, "analysis_tree_rules.txt")
        with open(tree_path, 'w', encoding='utf-8') as f:
            f.write(tree_rules)
        print(f"  Reglas arbol: {tree_path}")

    print(f"\n{report_text}")


# ============================================
# OPTIMIZACION: EVALUAR 7k BATCH
# ============================================

def evaluate_gems_on_slices_optimized(gems, precomputed, lab, anchor, config):
    """Version optimizada que evalua 7k en batch por grupo.

    Misma logica que evaluate_gems_on_slices pero agrupa la evaluacion 7k
    para evitar llamadas individuales a run_on_slice.
    """
    sl = config["sl_percent"]
    sl_e = config["sl_emergency_percent"]
    ts = config["ts_percent"]
    cool = config["cooldown_bars"]
    comm = config["commission"]

    opt_start = anchor["opt_start"]
    opt_end = anchor["opt_end"]
    ext_start = anchor["ext_start"]
    ext_end = anchor["ext_end"]
    fwd_start = anchor["fwd_start"]
    fwd_end = anchor["fwd_end"]
    fwd_h1_end = anchor["fwd_h1_end"]
    fwd_h2_start = anchor["fwd_h2_start"]
    opt_size = config["opt_size"]
    ext_size = config["ext_size"]
    fwd_size = config["fwd_size"]

    # Group gems by (preset_key, hyst)
    groups = {}
    for _, gem in gems.iterrows():
        ma_info = gem['ma_info']
        parts = ma_info.rsplit(' ', 1)
        preset_key = parts[0].strip()
        hyst = 0.5 if 'H05' in ma_info else 0.0
        gk = (preset_key, hyst)
        if gk not in groups:
            groups[gk] = []
        groups[gk].append(gem)

    all_rows = []

    for gk, gem_list in groups.items():
        if gk not in precomputed:
            continue

        data, preset_tuple, cuda_handle = precomputed[gk]
        close = data['close']
        n_data = len(close)

        config_ids = np.array([int(g['config_id']) for g in gem_list], dtype=np.uint32)

        # 10 slices (opt, ext, fwd, fwd_h1, fwd_h2, combined_7k, fwd_q1-q4)
        ext_opt_start = ext_start
        ext_opt_end = opt_end
        ext_opt_size = ext_opt_end - ext_opt_start

        quarter_size = fwd_size // 4

        slices = [
            ("opt", opt_start, opt_end, opt_size),
            ("ext", ext_start, ext_end, ext_size),
            ("fwd", fwd_start, fwd_end, fwd_size),
            ("fwd_h1", fwd_start, fwd_h1_end, fwd_size // 2),
            ("fwd_h2", fwd_h2_start, fwd_end, fwd_size - fwd_size // 2),
            ("combined_7k", ext_opt_start, ext_opt_end, ext_opt_size),
            ("fwd_q1", fwd_start, fwd_start + quarter_size, quarter_size),
            ("fwd_q2", fwd_start + quarter_size, fwd_start + 2 * quarter_size, quarter_size),
            ("fwd_q3", fwd_start + 2 * quarter_size, fwd_start + 3 * quarter_size, quarter_size),
            ("fwd_q4", fwd_start + 3 * quarter_size, fwd_end, fwd_size - 3 * quarter_size),
        ]

        slice_results = {}
        for name, s, e, n_bars_slice in slices:
            if s < 0 or e > n_data or s >= e:
                slice_results[name] = None
                continue
            res = run_slice(config_ids, data, s, e, sl, sl_e, ts, cool, comm,
                           cuda_handle=cuda_handle, lab=lab)
            pnl = res[:, 0]
            trades = res[:, 1]
            wins = res[:, 2]
            cancels = res[:, 3]
            maxdd = res[:, 4]
            gp = res[:, 5]
            gl = res[:, 6]
            _, pnl_ann, _, pf, _, _ = lab.calc_score_v63(
                pnl, maxdd, gp, gl, trades, cancels, n_bars_slice)
            wr = np.where(trades > 0, wins / trades * 100, 0.0)
            slice_results[name] = {
                'pnl': pnl, 'pf': pf, 'trades': trades, 'wins': wins,
                'maxdd': maxdd, 'wr': wr, 'pnl_ann': pnl_ann,
                'gp': gp, 'gl': gl,
            }

        # Asset context
        ctx_ext = compute_asset_context(close, ext_start, ext_end)
        ctx_fwd = compute_asset_context(close, fwd_start, fwd_end)
        ctx_opt = compute_asset_context(close, opt_start, opt_end)

        # Build rows
        for i, gem in enumerate(gem_list):
            row = {
                'config_id': int(gem['config_id']),
                'familia': gem.get('familia', '?'),
                'ma_info': gem['ma_info'],
                'preset': gem.get('preset', ''),
                'n_criterios': gem.get('n_criterios', 0),
                'criterios': gem.get('criterios', ''),
            }

            # Lab train/test/full metrics from extractor
            for col in ['pnl_tr', 'pnl_ann_tr', 'trades_tr', 'wr_tr', 'maxdd_tr', 'pf_tr', 'score_tr',
                        'pnl_te', 'pnl_ann_te', 'trades_te', 'wr_te', 'maxdd_te', 'pf_te', 'score_te',
                        'pnl_fu', 'pnl_ann_fu', 'trades_fu', 'wr_fu', 'maxdd_fu', 'pf_fu', 'score_fu',
                        'robustness', 'combined_score', 'cancels_tr', 'cancels_te', 'cancels_fu']:
                row[col] = gem.get(col, np.nan)

            # Metrics for each standard slice
            for name, prefix in [("opt", "opt"), ("ext", "ext"),
                                 ("fwd", "fwd"), ("fwd_h1", "fwd_h1"), ("fwd_h2", "fwd_h2"),
                                 ("fwd_q1", "fwd_q1"), ("fwd_q2", "fwd_q2"),
                                 ("fwd_q3", "fwd_q3"), ("fwd_q4", "fwd_q4")]:
                sr = slice_results.get(name)
                if sr is None:
                    for col in ['pnl', 'pf', 'trades', 'maxdd', 'wr', 'pnl_ann', 'gp', 'gl']:
                        row[f'{prefix}_{col}'] = np.nan
                else:
                    for col in ['pnl', 'pf', 'trades', 'maxdd', 'wr', 'pnl_ann', 'gp', 'gl']:
                        row[f'{prefix}_{col}'] = float(sr[col][i])
                    row[f'{prefix}_trades'] = int(sr['trades'][i])

            # Combined 7k from batch
            sr_7k = slice_results.get("combined_7k")
            if sr_7k is not None:
                row['combined_7k_pf'] = float(sr_7k['pf'][i])
                row['combined_7k_dd'] = float(sr_7k['maxdd'][i])
                row['combined_7k_pnl'] = float(sr_7k['pnl'][i])
                row['combined_7k_trades'] = int(sr_7k['trades'][i])
                row['pasa_7k'] = bool(sr_7k['pf'][i] >= 2.0 and sr_7k['maxdd'][i] <= 10.0)
            else:
                row['combined_7k_pf'] = np.nan
                row['combined_7k_dd'] = np.nan
                row['combined_7k_pnl'] = np.nan
                row['combined_7k_trades'] = np.nan
                row['pasa_7k'] = False

            # Derived metrics
            opt_pf = row.get('opt_pf', np.nan)
            c7k_pf = row.get('combined_7k_pf', np.nan)
            opt_dd = row.get('opt_maxdd', np.nan)
            c7k_dd = row.get('combined_7k_dd', np.nan)

            row['delta_pf_opt_7k'] = c7k_pf - opt_pf if not (np.isnan(c7k_pf) or np.isnan(opt_pf)) else np.nan
            row['delta_dd_opt_7k'] = c7k_dd - opt_dd if not (np.isnan(c7k_dd) or np.isnan(opt_dd)) else np.nan

            # fwd_h2_ratio
            h1_pnl = row.get('fwd_h1_pnl', 0)
            h2_pnl = row.get('fwd_h2_pnl', 0)
            if np.isnan(h1_pnl):
                h1_pnl = 0
            if np.isnan(h2_pnl):
                h2_pnl = 0
            denom = abs(h1_pnl) + abs(h2_pnl)
            row['fwd_h2_ratio'] = h2_pnl / denom if denom > 0 else 0.5

            # Quarter sanity check: sum(Q1..Q4) vs fwd_pnl
            q_vals = [row.get(f'fwd_q{q}_pnl', np.nan) for q in range(1, 5)]
            fwd_pnl_val = row.get('fwd_pnl', np.nan)
            if all(not np.isnan(v) for v in q_vals) and not np.isnan(fwd_pnl_val):
                row['fwd_quarter_diff'] = sum(q_vals) - fwd_pnl_val
            else:
                row['fwd_quarter_diff'] = np.nan

            # Asset context
            row['asset_return_ext'] = ctx_ext['return']
            row['asset_volatility_ext'] = ctx_ext['volatility']
            row['asset_maxdd_ext'] = ctx_ext['maxdd']
            row['asset_return_fwd'] = ctx_fwd['return']
            row['asset_volatility_fwd'] = ctx_fwd['volatility']
            row['asset_maxdd_fwd'] = ctx_fwd['maxdd']
            row['asset_return_opt'] = ctx_opt['return']
            row['asset_volatility_opt'] = ctx_opt['volatility']
            row['asset_maxdd_opt'] = ctx_opt['maxdd']

            row['fwd_start'] = fwd_start
            row['fwd_end'] = fwd_end

            all_rows.append(row)

    return all_rows


def _patch_all_train_parts(parts_dir, anchor_idx, symbol, date_opt_start,
                           date_fwd_end, gem_lookup=None):
    """Read variant part-files for an anchor, add id columns + gem merge, rewrite.

    Processes one part-file at a time to keep memory low.
    """
    import glob as _glob
    pattern = os.path.join(parts_dir, f"part_{anchor_idx:04d}_v*.parquet")
    part_files = sorted(_glob.glob(pattern))

    gem_extra_cols = [
        'fwd_h1_pnl', 'fwd_h2_pnl',
        'fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl',
        'opt_pnl', 'opt_pf', 'opt_trades', 'opt_maxdd', 'opt_wr', 'opt_pnl_ann',
        'ext_pnl', 'ext_pf', 'ext_trades', 'ext_maxdd', 'ext_wr',
        'combined_7k_pf', 'combined_7k_dd', 'combined_7k_pnl', 'combined_7k_trades',
        'pasa_7k', 'delta_pf_opt_7k', 'delta_dd_opt_7k',
        'n_criterios', 'criterios', 'familia',
    ]

    for pf in part_files:
        df = pd.read_parquet(pf)
        df['symbol'] = symbol
        df['anchor_idx'] = anchor_idx
        df['date_opt_start'] = date_opt_start
        df['date_fwd_end'] = date_fwd_end

        if gem_lookup:
            for idx_row in range(len(df)):
                key = (df.iloc[idx_row]['config_id'], df.iloc[idx_row]['ma_info'])
                if key in gem_lookup:
                    gem_data = gem_lookup[key]
                    df.at[df.index[idx_row], 'is_gem'] = True
                    for col in gem_extra_cols:
                        if col in gem_data:
                            df.at[df.index[idx_row], col] = gem_data[col]

        df.to_parquet(pf, index=False)
        del df
        gc.collect()


def _eval_one_variant_fwd(vdf, gk, precomputed, lab, anchor, config,
                           parts_dir, anchor_idx, variant_idx):
    """Evaluate one variant's train-passing configs on forward, write part-file.

    Modifies *vdf* in-place (caller should del it after).
    Returns number of rows written, or 0 if skipped.
    """
    if gk not in precomputed:
        return 0

    sl = config["sl_percent"]
    sl_e = config["sl_emergency_percent"]
    ts = config["ts_percent"]
    cool = config["cooldown_bars"]
    comm = config["commission"]

    fwd_start = anchor["fwd_start"]
    fwd_end = anchor["fwd_end"]
    ext_start = anchor["ext_start"]
    ext_end = anchor["ext_end"]
    opt_start = anchor["opt_start"]
    opt_end = anchor["opt_end"]

    data_dict, preset_tuple, cuda_handle = precomputed[gk]
    close = data_dict['close']
    n_data = len(close)

    if fwd_start < 0 or fwd_end > n_data or fwd_start >= fwd_end:
        return 0

    config_ids = vdf['config_id'].values.astype(np.uint32)

    res_fwd = run_slice(config_ids, data_dict, fwd_start, fwd_end,
                        sl, sl_e, ts, cool, comm,
                        cuda_handle=cuda_handle, lab=lab)

    pnl_fwd = res_fwd[:, 0]
    trades_fwd = res_fwd[:, 1]
    wins_fwd = res_fwd[:, 2]
    maxdd_fwd = res_fwd[:, 4]
    gp_fwd = res_fwd[:, 5]
    gl_fwd = res_fwd[:, 6]
    pf_fwd = np.where(gl_fwd > 0, gp_fwd / gl_fwd, np.where(gp_fwd > 0, 5.0, 0.0))
    wr_fwd = np.where(trades_fwd > 0, wins_fwd / trades_fwd * 100, 0.0)

    ctx_ext = compute_asset_context(close, ext_start, ext_end)
    ctx_fwd = compute_asset_context(close, fwd_start, fwd_end)
    ctx_opt = compute_asset_context(close, opt_start, opt_end)

    # Add forward metrics in-place (caller will del vdf after)
    vdf['fwd_pnl'] = pnl_fwd
    vdf['fwd_pf'] = pf_fwd
    vdf['fwd_trades'] = trades_fwd.astype(int)
    vdf['fwd_maxdd'] = maxdd_fwd
    vdf['fwd_wr'] = wr_fwd
    for col in ['fwd_h1_pnl', 'fwd_h2_pnl',
                'fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl']:
        vdf[col] = np.nan
    vdf['ratio_pnl_te_tr'] = np.where(
        vdf['pnl_tr'].values != 0, vdf['pnl_te'].values / vdf['pnl_tr'].values, np.nan)
    vdf['delta_pf_opt_7k'] = np.nan
    vdf['delta_dd_opt_7k'] = np.nan
    vdf['asset_return_ext'] = ctx_ext['return']
    vdf['asset_volatility_ext'] = ctx_ext['volatility']
    vdf['asset_maxdd_ext'] = ctx_ext['maxdd']
    vdf['asset_return_fwd'] = ctx_fwd['return']
    vdf['asset_volatility_fwd'] = ctx_fwd['volatility']
    vdf['asset_maxdd_fwd'] = ctx_fwd['maxdd']
    vdf['asset_return_opt'] = ctx_opt['return']
    vdf['asset_volatility_opt'] = ctx_opt['volatility']
    vdf['asset_maxdd_opt'] = ctx_opt['maxdd']
    vdf['fwd_start'] = fwd_start
    vdf['fwd_end'] = fwd_end
    vdf['is_gem'] = False

    part_path = os.path.join(parts_dir,
                             f"part_{anchor_idx:04d}_v{variant_idx:04d}.parquet")
    vdf.to_parquet(part_path, index=False)
    n_written = len(vdf)
    del res_fwd
    gc.collect()
    return n_written


def evaluate_all_train_on_fwd(variant_dfs, precomputed, lab, anchor, config,
                              parts_dir, anchor_idx):
    """Evaluate ALL train-passing configs on the forward slice only.

    Writes results incrementally as parquet part-files (one per variant group)
    to *parts_dir*, freeing memory after each variant.
    Returns total number of rows written.
    """
    sl = config["sl_percent"]
    sl_e = config["sl_emergency_percent"]
    ts = config["ts_percent"]
    cool = config["cooldown_bars"]
    comm = config["commission"]

    fwd_start = anchor["fwd_start"]
    fwd_end = anchor["fwd_end"]
    ext_start = anchor["ext_start"]
    ext_end = anchor["ext_end"]

    # Group variant_dfs rows by (preset_key, hyst)
    groups = {}
    for vdf in variant_dfs:
        for _, row in vdf.iterrows():
            ma_info = row['ma_info']
            parts = ma_info.rsplit(' ', 1)
            preset_key = parts[0].strip()
            hyst_val = 0.5 if 'H05' in ma_info else 0.0
            gk = (preset_key, hyst_val)
            if gk not in groups:
                groups[gk] = []
            groups[gk].append(dict(row))

    total_written = 0
    variant_idx = 0

    for gk, rows_list in groups.items():
        if gk not in precomputed:
            continue

        data_dict, preset_tuple, cuda_handle = precomputed[gk]
        close = data_dict['close']
        n_data = len(close)

        if fwd_start < 0 or fwd_end > n_data or fwd_start >= fwd_end:
            continue

        config_ids = np.array([int(r['config_id']) for r in rows_list], dtype=np.uint32)

        # Run forward only
        res_fwd = run_slice(config_ids, data_dict, fwd_start, fwd_end,
                            sl, sl_e, ts, cool, comm,
                            cuda_handle=cuda_handle, lab=lab)

        pnl_fwd = res_fwd[:, 0]
        trades_fwd = res_fwd[:, 1]
        wins_fwd = res_fwd[:, 2]
        maxdd_fwd = res_fwd[:, 4]
        gp_fwd = res_fwd[:, 5]
        gl_fwd = res_fwd[:, 6]
        pf_fwd = np.where(gl_fwd > 0, gp_fwd / gl_fwd, np.where(gp_fwd > 0, 5.0, 0.0))
        wr_fwd = np.where(trades_fwd > 0, wins_fwd / trades_fwd * 100, 0.0)

        # Asset context
        ctx_ext = compute_asset_context(close, ext_start, ext_end)
        ctx_fwd = compute_asset_context(close, fwd_start, fwd_end)

        variant_rows = []
        for i, src_row in enumerate(rows_list):
            row = dict(src_row)

            # Forward metrics
            row['fwd_pnl'] = float(pnl_fwd[i])
            row['fwd_pf'] = float(pf_fwd[i])
            row['fwd_trades'] = int(trades_fwd[i])
            row['fwd_maxdd'] = float(maxdd_fwd[i])
            row['fwd_wr'] = float(wr_fwd[i])

            # H1/H2/Q1-Q4 = NaN (only computed for gems in Step 5)
            for col in ['fwd_h1_pnl', 'fwd_h2_pnl',
                        'fwd_q1_pnl', 'fwd_q2_pnl', 'fwd_q3_pnl', 'fwd_q4_pnl']:
                row[col] = np.nan

            # Derived
            row['ratio_pnl_te_tr'] = (row['pnl_te'] / row['pnl_tr']
                                      if row.get('pnl_tr', 0) != 0 else np.nan)
            # delta_pf_opt_7k not available for non-gems (no combined_7k eval)
            row['delta_pf_opt_7k'] = np.nan
            row['delta_dd_opt_7k'] = np.nan

            # Context
            row['asset_return_ext'] = ctx_ext['return']
            row['asset_volatility_ext'] = ctx_ext['volatility']
            row['asset_maxdd_ext'] = ctx_ext['maxdd']
            row['asset_return_fwd'] = ctx_fwd['return']
            row['asset_volatility_fwd'] = ctx_fwd['volatility']
            row['asset_maxdd_fwd'] = ctx_fwd['maxdd']

            row['fwd_start'] = fwd_start
            row['fwd_end'] = fwd_end
            row['is_gem'] = False

            variant_rows.append(row)

        # Flush variant to parquet part-file and free memory
        part_path = os.path.join(parts_dir,
                                 f"part_{anchor_idx:04d}_v{variant_idx:04d}.parquet")
        pd.DataFrame(variant_rows).to_parquet(part_path, index=False)
        total_written += len(variant_rows)
        del variant_rows, rows_list, res_fwd
        gc.collect()
        variant_idx += 1

    # Free the grouping dict
    del groups
    gc.collect()

    return total_written


def run_analysis_all_train(df, output_dir):
    """Analisis sobre el dataset expandido (todas las configs que pasan train)."""
    L = []
    L.append(f"{'='*100}")
    L.append(f"WALK-FORWARD EXPERIMENT — ANALISIS ALL-TRAIN DATASET")
    L.append(f"{'='*100}")
    L.append(f"Observaciones totales: {len(df)}")
    L.append(f"Gemas: {df['is_gem'].sum()} ({df['is_gem'].mean()*100:.1f}%)")
    L.append(f"No-gemas: {(~df['is_gem']).sum()} ({(~df['is_gem']).mean()*100:.1f}%)")
    L.append(f"Simbolos: {df['symbol'].nunique()}")
    L.append(f"Configs unicas: {df['config_id'].nunique()}")
    L.append("")

    # ---- 1. Correlaciones train/test features vs fwd_pnl ----
    L.append(f"\n{'~'*100}")
    L.append(f"1. CORRELACIONES TRAIN/TEST FEATURES VS FWD_PNL")
    L.append(f"{'~'*100}")

    features = [
        'pnl_tr', 'pf_tr', 'wr_tr', 'maxdd_tr', 'trades_tr', 'score_tr',
        'pnl_te', 'pf_te', 'wr_te', 'maxdd_te', 'trades_te', 'score_te',
        'pnl_fu', 'pf_fu', 'wr_fu', 'maxdd_fu', 'trades_fu', 'score_fu',
        'robustness', 'combined_score', 'ratio_pnl_te_tr',
        'pnl_ann_tr', 'pnl_ann_te', 'pnl_ann_fu',
    ]
    targets = ['fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_wr', 'fwd_maxdd']

    corr_rows = []
    for feat in features:
        if feat not in df.columns:
            continue
        row_data = {'feature': feat}
        for tgt in targets:
            if tgt not in df.columns:
                row_data[tgt] = np.nan
                continue
            valid = df[[feat, tgt]].dropna()
            if len(valid) < 10:
                row_data[tgt] = np.nan
            else:
                row_data[tgt] = valid[feat].corr(valid[tgt])
        corr_rows.append(row_data)

    corr_df = pd.DataFrame(corr_rows).set_index('feature')
    corr_df['max_abs_r'] = corr_df[targets].abs().max(axis=1)
    corr_df = corr_df.sort_values('max_abs_r', ascending=False)

    corr_csv = os.path.join(output_dir, "analysis_all_train_correlations.csv")
    corr_df.to_csv(corr_csv)

    L.append(f"\n  {'Feature':<25s} | " + " | ".join(f"{t:>12s}" for t in targets) + " | max|r|")
    L.append(f"  {'-'*25}-+-" + "-+-".join(f"{'-'*12}" for _ in targets) + "-+-------")
    for feat, row in corr_df.iterrows():
        vals = []
        for t in targets:
            v = row[t]
            if np.isnan(v):
                vals.append("          --")
            else:
                star = " **" if abs(v) > 0.3 else " *" if abs(v) > 0.15 else ""
                vals.append(f"{v:>+9.3f}{star}")
        L.append(f"  {feat:<25s} | " + " | ".join(f"{v:>12s}" for v in vals) +
                 f" | {row['max_abs_r']:.3f}")

    L.append(f"\n  (* |r|>0.15, ** |r|>0.30)")

    # ---- 2. Distribucion de fwd_pnl por buckets de metricas train/test ----
    L.append(f"\n{'~'*100}")
    L.append(f"2. DISTRIBUCION FWD_PNL POR BUCKETS DE METRICAS TRAIN/TEST")
    L.append(f"{'~'*100}")

    bucket_features = ['pnl_tr', 'pf_tr', 'score_tr', 'pnl_te', 'pf_te', 'score_te',
                       'robustness', 'combined_score', 'ratio_pnl_te_tr']
    for feat in bucket_features:
        if feat not in df.columns:
            continue
        valid = df[[feat, 'fwd_pnl']].dropna()
        if len(valid) < 50:
            continue

        try:
            valid['bucket'] = pd.qcut(valid[feat], q=5, duplicates='drop')
            bucket_stats = valid.groupby('bucket', observed=True)['fwd_pnl'].agg(
                ['mean', 'median', 'std', 'count',
                 lambda x: (x > 0).mean() * 100])
            bucket_stats.columns = ['mean', 'median', 'std', 'count', 'pct_positive']

            L.append(f"\n  {feat}:")
            L.append(f"    {'Bucket':<30s} | {'Mean':>8s} | {'Median':>8s} | {'Std':>8s} | {'N':>5s} | {'%Pos':>5s}")
            L.append(f"    {'-'*30}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*5}-+-{'-'*5}")
            for bucket, row in bucket_stats.iterrows():
                L.append(f"    {str(bucket):<30s} | {row['mean']:>+7.2f} | {row['median']:>+7.2f} | "
                         f"{row['std']:>7.2f} | {int(row['count']):>5d} | {row['pct_positive']:>4.1f}%")
        except Exception:
            continue

    # ---- 3. Gems vs Non-gems comparison ----
    L.append(f"\n{'~'*100}")
    L.append(f"3. COMPARACION GEMS VS NON-GEMS EN FORWARD")
    L.append(f"{'~'*100}")

    for is_gem_val, label in [(True, "GEMS"), (False, "NON-GEMS")]:
        subset = df[df['is_gem'] == is_gem_val]
        if len(subset) == 0:
            continue
        L.append(f"\n  {label} (N={len(subset)}):")
        for col in ['fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_maxdd', 'fwd_wr']:
            if col in subset.columns:
                vals = subset[col].dropna()
                if len(vals) > 0:
                    pct_pos = (vals > 0).mean() * 100 if col in ['fwd_pnl'] else np.nan
                    extra = f" | %pos={pct_pos:.1f}%" if not np.isnan(pct_pos) else ""
                    L.append(f"    {col:<15s}: mean={vals.mean():>+8.2f}  median={vals.median():>+8.2f}  "
                             f"std={vals.std():>7.2f}{extra}")

    # ---- 4. Decision Tree on full dataset ----
    L.append(f"\n{'~'*100}")
    L.append(f"4. DECISION TREE: PREDECIR FWD_PNL > 0")
    L.append(f"{'~'*100}")

    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.model_selection import cross_val_score

        feature_cols = [f for f in features if f in df.columns]
        X = df[feature_cols].copy()
        y = (df['fwd_pnl'] > 0).astype(int)

        mask = X.notna().all(axis=1) & y.notna()
        X = X[mask]
        y = y[mask]

        if len(X) >= 200:
            clf = DecisionTreeClassifier(max_depth=6, min_samples_leaf=max(20, len(X) // 100),
                                         class_weight='balanced', random_state=42)
            clf.fit(X, y)

            importances = pd.Series(clf.feature_importances_, index=feature_cols)
            importances = importances.sort_values(ascending=False)

            L.append(f"\n  Feature importances (top 15):")
            for feat, imp in importances.head(15).items():
                if imp > 0.001:
                    L.append(f"    {feat:<25s}: {imp:.4f}")

            tree_rules = export_text(clf, feature_names=feature_cols,
                                     class_names=['fwd_neg', 'fwd_pos'])
            L.append(f"\n  Reglas del arbol (max_depth=6):")
            for line in tree_rules.split('\n')[:60]:
                L.append(f"    {line}")

            scores = cross_val_score(clf, X, y, cv=min(5, len(X) // 50), scoring='accuracy')
            L.append(f"\n  Accuracy (5-fold CV): {scores.mean():.3f} +/- {scores.std():.3f}")
            L.append(f"  Baseline (mayoria): {max(y.mean(), 1-y.mean()):.3f}")

            # Save tree rules
            tree_path = os.path.join(output_dir, "analysis_all_train_tree.txt")
            with open(tree_path, 'w', encoding='utf-8') as f:
                f.write(tree_rules)
        else:
            L.append(f"\n  Insuficientes observaciones ({len(X)}) para arbol (min 200)")
    except ImportError:
        L.append(f"\n  sklearn no instalado — saltando arbol de decision")

    # Save report
    report_text = '\n'.join(L)
    report_path = os.path.join(output_dir, "analysis_all_train_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n  Reporte all-train: {report_path}")
    print(f"\n{report_text}")


def run_analysis_all_train_incremental(checkpoint_files, output_dir):
    """Analisis all-train leyendo row groups individuales via PyArrow.

    Nunca tiene mas de un row group (~100K filas) en memoria simultaneamente.
    Usa Chan's parallel algorithm (vectorizado con numpy) para correlaciones,
    medias y varianzas online.
    """
    import pyarrow.parquet as pq

    features = [
        'pnl_tr', 'pf_tr', 'wr_tr', 'maxdd_tr', 'trades_tr', 'score_tr',
        'pnl_te', 'pf_te', 'wr_te', 'maxdd_te', 'trades_te', 'score_te',
        'pnl_fu', 'pf_fu', 'wr_fu', 'maxdd_fu', 'trades_fu', 'score_fu',
        'robustness', 'combined_score', 'ratio_pnl_te_tr',
        'pnl_ann_tr', 'pnl_ann_te', 'pnl_ann_fu',
    ]
    targets = ['fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_wr', 'fwd_maxdd']
    bucket_features = ['pnl_tr', 'pf_tr', 'score_tr', 'pnl_te', 'pf_te', 'score_te',
                       'robustness', 'combined_score', 'ratio_pnl_te_tr']

    # -- Helper: Chan's parallel merge for (n, mean, M2) -----------------
    def _merge_welford(n_a, mean_a, m2_a, n_b, mean_b, m2_b):
        """Merge two Welford accumulators (Chan's parallel algorithm)."""
        if n_a == 0:
            return n_b, mean_b, m2_b
        if n_b == 0:
            return n_a, mean_a, m2_a
        n = n_a + n_b
        delta = mean_b - mean_a
        mean = (n_a * mean_a + n_b * mean_b) / n
        m2 = m2_a + m2_b + delta * delta * n_a * n_b / n
        return n, mean, m2

    def _merge_cov(n_a, mean_x_a, mean_y_a, m2_x_a, m2_y_a, c_a,
                   n_b, mean_x_b, mean_y_b, m2_x_b, m2_y_b, c_b):
        """Merge two online covariance accumulators (Chan's parallel)."""
        if n_a == 0:
            return n_b, mean_x_b, mean_y_b, m2_x_b, m2_y_b, c_b
        if n_b == 0:
            return n_a, mean_x_a, mean_y_a, m2_x_a, m2_y_a, c_a
        n = n_a + n_b
        dx = mean_x_b - mean_x_a
        dy = mean_y_b - mean_y_a
        mean_x = (n_a * mean_x_a + n_b * mean_x_b) / n
        mean_y = (n_a * mean_y_a + n_b * mean_y_b) / n
        m2_x = m2_x_a + m2_x_b + dx * dx * n_a * n_b / n
        m2_y = m2_y_a + m2_y_b + dy * dy * n_a * n_b / n
        c = c_a + c_b + dx * dy * n_a * n_b / n
        return n, mean_x, mean_y, m2_x, m2_y, c

    # -- Accumulators -----------------------------------------------------
    total_rows = 0
    total_gems = 0
    total_non_gems = 0
    all_symbols = set()
    all_configs = set()

    # Correlation accumulators: (feat, tgt) -> (n, mean_x, mean_y, M2_x, M2_y, C)
    corr_state = {}
    for feat in features:
        for tgt in targets:
            corr_state[(feat, tgt)] = (0, 0.0, 0.0, 0.0, 0.0, 0.0)

    # Per-symbol correlation accumulators: symbol -> {(feat, tgt) -> (n, mean_x, mean_y, M2_x, M2_y, C)}
    per_symbol_corr = {}
    per_symbol_n = {}  # symbol -> total rows

    # Gems vs non-gems: (is_gem, col) -> (n, mean, M2, pos_count)
    group_stats = {}
    for is_gem in [True, False]:
        for col in ['fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_maxdd', 'fwd_wr']:
            group_stats[(is_gem, col)] = {'n': 0, 'mean': 0.0, 'M2': 0.0, 'pos_count': 0}

    # Bucket accumulators: feat -> list of per-chunk summaries
    bucket_accum = {}

    # -- Count total row groups for progress ------------------------------
    total_rg = 0
    pq_files_info = []  # (path, num_row_groups, columns)
    for cp_path in checkpoint_files:
        try:
            pf = pq.ParquetFile(cp_path)
            nrg = pf.metadata.num_row_groups
            cols = [c.name for c in pf.schema_arrow]
            pq_files_info.append((cp_path, nrg, cols))
            total_rg += nrg
            del pf
        except Exception as e:
            print(f"  WARNING: No se pudo abrir {os.path.basename(cp_path)}: {e}")

    print(f"  Procesando {len(pq_files_info)} checkpoints, {total_rg} row groups en streaming...")

    rg_processed = 0

    for cp_path, num_rg, cp_columns in pq_files_info:
        try:
            pf = pq.ParquetFile(cp_path)
        except Exception as e:
            print(f"  WARNING: No se pudo abrir {os.path.basename(cp_path)}: {e}")
            continue

        # Extract symbol name from filename: checkpoint_{SYMBOL}_all_train_v2.parquet
        cp_basename = os.path.basename(cp_path)
        sym_name = cp_basename.replace("checkpoint_", "").replace(f"_all_train_v{CHECKPOINT_VERSION}.parquet", "")

        # Initialize per-symbol accumulators if needed
        if sym_name not in per_symbol_corr:
            per_symbol_corr[sym_name] = {}
            for feat in features:
                per_symbol_corr[sym_name][(feat, 'fwd_pnl')] = (0, 0.0, 0.0, 0.0, 0.0, 0.0)
            per_symbol_n[sym_name] = 0

        for rg_idx in range(num_rg):
            # Read single row group -> pandas, then release arrow table
            table = pf.read_row_group(rg_idx)
            df = table.to_pandas()
            del table

            n = len(df)
            if n == 0:
                del df
                continue

            total_rows += n

            # -- Basic counts --
            if 'is_gem' in df.columns:
                gem_mask = df['is_gem'].values
                total_gems += int(gem_mask.sum())
                total_non_gems += int((~gem_mask).sum())
            if 'symbol' in df.columns:
                all_symbols.update(df['symbol'].unique())
            if 'config_id' in df.columns:
                all_configs.update(df['config_id'].unique())

            # -- Correlations (vectorized Chan's parallel) --
            for feat in features:
                if feat not in df.columns:
                    continue
                feat_vals = df[feat].values
                for tgt in targets:
                    if tgt not in df.columns:
                        continue
                    tgt_vals = df[tgt].values
                    # Only valid (non-NaN) pairs
                    mask = ~(np.isnan(feat_vals) | np.isnan(tgt_vals))
                    n_valid = int(mask.sum())
                    if n_valid < 2:
                        continue
                    x = feat_vals[mask]
                    y = tgt_vals[mask]
                    # Batch stats for this chunk
                    n_b = n_valid
                    mean_x_b = float(x.mean())
                    mean_y_b = float(y.mean())
                    dx = x - mean_x_b
                    dy = y - mean_y_b
                    m2_x_b = float((dx * dx).sum())
                    m2_y_b = float((dy * dy).sum())
                    c_b = float((dx * dy).sum())
                    # Merge with existing accumulator
                    prev = corr_state[(feat, tgt)]
                    corr_state[(feat, tgt)] = _merge_cov(
                        prev[0], prev[1], prev[2], prev[3], prev[4], prev[5],
                        n_b, mean_x_b, mean_y_b, m2_x_b, m2_y_b, c_b)

                    # -- Per-symbol correlation (only for fwd_pnl) --
                    if tgt == 'fwd_pnl':
                        sym_prev = per_symbol_corr[sym_name][(feat, 'fwd_pnl')]
                        per_symbol_corr[sym_name][(feat, 'fwd_pnl')] = _merge_cov(
                            sym_prev[0], sym_prev[1], sym_prev[2], sym_prev[3], sym_prev[4], sym_prev[5],
                            n_b, mean_x_b, mean_y_b, m2_x_b, m2_y_b, c_b)

            per_symbol_n[sym_name] += n

            # -- Gems vs Non-gems (vectorized batch Welford) --
            if 'is_gem' in df.columns:
                gem_col = df['is_gem'].values
                for is_gem_val in [True, False]:
                    subset_mask = gem_col == is_gem_val
                    if not subset_mask.any():
                        continue
                    for col in ['fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_maxdd', 'fwd_wr']:
                        if col not in df.columns:
                            continue
                        raw = df[col].values[subset_mask]
                        valid_mask = ~np.isnan(raw)
                        vals = raw[valid_mask]
                        if len(vals) == 0:
                            continue
                        acc = group_stats[(is_gem_val, col)]
                        # Chan's parallel merge: batch stats
                        n_b = len(vals)
                        mean_b = float(vals.mean())
                        dx_b = vals - mean_b
                        m2_b = float((dx_b * dx_b).sum())
                        acc['n'], acc['mean'], acc['M2'] = _merge_welford(
                            acc['n'], acc['mean'], acc['M2'],
                            n_b, mean_b, m2_b)
                        if col == 'fwd_pnl':
                            acc['pos_count'] += int((vals > 0).sum())

            # -- Bucket distributions (per-chunk quintiles) --
            for feat in bucket_features:
                if feat not in df.columns or 'fwd_pnl' not in df.columns:
                    continue
                f_vals = df[feat].values
                t_vals = df['fwd_pnl'].values
                valid_mask = ~(np.isnan(f_vals) | np.isnan(t_vals))
                n_valid = int(valid_mask.sum())
                if n_valid < 50:
                    continue
                try:
                    chunk = pd.DataFrame({
                        'feat': f_vals[valid_mask],
                        'fwd_pnl': t_vals[valid_mask]
                    })
                    chunk['bucket'] = pd.qcut(chunk['feat'], q=5, duplicates='drop')
                    bstats = chunk.groupby('bucket', observed=True)['fwd_pnl'].agg(
                        ['mean', 'count', lambda x: (x > 0).sum()])
                    bstats.columns = ['mean', 'count', 'pos_count']
                    if feat not in bucket_accum:
                        bucket_accum[feat] = []
                    for bucket_label, row in bstats.iterrows():
                        bucket_accum[feat].append({
                            'bucket': str(bucket_label),
                            'count': int(row['count']),
                            'sum': row['mean'] * row['count'],
                            'pos_n': int(row['pos_count']),
                        })
                    del chunk
                except Exception:
                    pass

            del df
            gc.collect()

            rg_processed += 1
            if rg_processed % 20 == 0:
                print(f"    ... {rg_processed}/{total_rg} row groups ({total_rows:,} filas)")

        del pf

    if total_rows == 0:
        print("  Sin datos en checkpoints all-train.")
        return

    print(f"  Total: {total_rows:,} filas, {rg_processed} row groups de {len(pq_files_info)} checkpoints")

    # ---- Build report ----
    L = []
    L.append(f"{'='*100}")
    L.append(f"WALK-FORWARD EXPERIMENT — ANALISIS ALL-TRAIN DATASET (INCREMENTAL)")
    L.append(f"{'='*100}")
    L.append(f"Observaciones totales: {total_rows:,}")
    L.append(f"Gemas: {total_gems:,} ({total_gems/total_rows*100:.1f}%)")
    L.append(f"No-gemas: {total_non_gems:,} ({total_non_gems/total_rows*100:.1f}%)")
    L.append(f"Simbolos: {len(all_symbols)}")
    L.append(f"Configs unicas: {len(all_configs)}")
    L.append(f"Checkpoints: {len(pq_files_info)}  |  Row groups: {total_rg}")
    L.append("")

    # ---- 1. Correlations from online covariance ----
    L.append(f"\n{'~'*100}")
    L.append(f"1. CORRELACIONES TRAIN/TEST FEATURES VS FWD_PNL")
    L.append(f"{'~'*100}")

    corr_rows = []
    for feat in features:
        row_data = {'feature': feat}
        for tgt in targets:
            n, mx, my, m2x, m2y, c = corr_state[(feat, tgt)]
            if n < 10 or m2x <= 0 or m2y <= 0:
                row_data[tgt] = np.nan
            else:
                row_data[tgt] = c / (m2x * m2y) ** 0.5
        corr_rows.append(row_data)

    corr_df = pd.DataFrame(corr_rows).set_index('feature')
    corr_df['max_abs_r'] = corr_df[targets].abs().max(axis=1)
    corr_df = corr_df.sort_values('max_abs_r', ascending=False)

    corr_csv = os.path.join(output_dir, "analysis_all_train_correlations.csv")
    corr_df.to_csv(corr_csv)

    L.append(f"\n  {'Feature':<25s} | " + " | ".join(f"{t:>12s}" for t in targets) + " | max|r|")
    L.append(f"  {'-'*25}-+-" + "-+-".join(f"{'-'*12}" for _ in targets) + "-+-------")
    for feat, row in corr_df.iterrows():
        vals = []
        for t in targets:
            v = row[t]
            if np.isnan(v):
                vals.append("          --")
            else:
                star = " **" if abs(v) > 0.3 else " *" if abs(v) > 0.15 else ""
                vals.append(f"{v:>+9.3f}{star}")
        L.append(f"  {feat:<25s} | " + " | ".join(f"{v:>12s}" for v in vals) +
                 f" | {row['max_abs_r']:.3f}")

    L.append(f"\n  (* |r|>0.15, ** |r|>0.30)")
    L.append(f"  (correlaciones exactas via Chan's parallel online covariance)")

    # ---- 1b. Per-symbol correlations vs fwd_pnl ----
    L.append(f"\n{'~'*100}")
    L.append(f"1b. CORRELACIONES PER-SYMBOL: FEATURES VS FWD_PNL")
    L.append(f"{'~'*100}")

    # Compute per-symbol r values: symbol -> {feat -> r}
    per_symbol_r = {}
    for sym_name in sorted(per_symbol_corr.keys()):
        sym_corrs = {}
        for feat in features:
            key = (feat, 'fwd_pnl')
            if key not in per_symbol_corr[sym_name]:
                continue
            n, mx, my, m2x, m2y, c = per_symbol_corr[sym_name][key]
            if n < 10 or m2x <= 0 or m2y <= 0:
                continue
            sym_corrs[feat] = c / (m2x * m2y) ** 0.5
        per_symbol_r[sym_name] = sym_corrs

    for sym_name in sorted(per_symbol_r.keys()):
        sym_corrs = per_symbol_r[sym_name]
        sym_total = per_symbol_n.get(sym_name, 0)
        # Filter |r| > 0.10 and sort by |r| desc
        significant = [(f, r) for f, r in sym_corrs.items() if abs(r) > 0.10]
        significant.sort(key=lambda x: abs(x[1]), reverse=True)

        L.append(f"\n  {sym_name} (N={sym_total:,}):")
        if not significant:
            L.append(f"    (ninguna feature con |r| > 0.10)")
        else:
            L.append(f"    {'Feature':<25s} |   fwd_pnl")
            L.append(f"    {'-'*25}-+----------")
            for feat, r in significant:
                L.append(f"    {feat:<25s} |   {r:>+.4f}")

    # ---- Summary table: per-symbol r side by side ----
    L.append(f"\n  {'─'*100}")
    L.append(f"  RESUMEN: r POR SIMBOLO (features con |r|>0.10 en al menos un simbolo)")
    L.append(f"  {'─'*100}")

    # Collect all features that have |r| > 0.10 in at least one symbol
    symbols_sorted = sorted(per_symbol_r.keys())
    notable_feats = set()
    for sym_name in symbols_sorted:
        for feat, r in per_symbol_r[sym_name].items():
            if abs(r) > 0.10:
                notable_feats.add(feat)

    if notable_feats:
        # Sort features by max |r| across symbols
        def _max_abs_r(feat):
            return max((abs(per_symbol_r[s].get(feat, 0.0)) for s in symbols_sorted), default=0)
        notable_feats_sorted = sorted(notable_feats, key=_max_abs_r, reverse=True)

        # Header
        sym_width = max(8, max((len(s) for s in symbols_sorted), default=8))
        header = f"    {'Feature':<25s}"
        for s in symbols_sorted:
            header += f" | {s:>{sym_width}s}"
        L.append(header)
        sep = f"    {'-'*25}"
        for s in symbols_sorted:
            sep += f"-+-{'-'*sym_width}"
        L.append(sep)

        for feat in notable_feats_sorted:
            line = f"    {feat:<25s}"
            signs = set()
            for s in symbols_sorted:
                r = per_symbol_r[s].get(feat, np.nan)
                if np.isnan(r):
                    line += f" | {'--':>{sym_width}s}"
                else:
                    line += f" | {r:>+{sym_width}.4f}"
                    if r > 0.01:
                        signs.add('+')
                    elif r < -0.01:
                        signs.add('-')
            # Mark consistency
            if len(signs) == 1:
                line += "  CONSISTENTE"
            elif len(signs) == 2:
                line += "  CONTRADICTORIO"
            L.append(line)
    else:
        L.append(f"    (ninguna feature con |r| > 0.10 en ningun simbolo)")

    # Free per-symbol correlation memory
    del per_symbol_corr
    gc.collect()

    # ---- 2. Bucket distributions (aggregate across chunks) ----
    L.append(f"\n{'~'*100}")
    L.append(f"2. DISTRIBUCION FWD_PNL POR BUCKETS DE METRICAS TRAIN/TEST")
    L.append(f"{'~'*100}")

    for feat in bucket_features:
        if feat not in bucket_accum:
            continue
        merged = defaultdict(lambda: {'sum': 0.0, 'n': 0, 'pos_n': 0})
        for entry in bucket_accum[feat]:
            key = entry['bucket']
            merged[key]['sum'] += entry['sum']
            merged[key]['n'] += entry['count']
            merged[key]['pos_n'] += entry['pos_n']

        if not merged:
            continue

        L.append(f"\n  {feat}:")
        L.append(f"    {'Bucket':<30s} | {'Mean':>8s} | {'N':>5s} | {'%Pos':>5s}")
        L.append(f"    {'-'*30}-+-{'-'*8}-+-{'-'*5}-+-{'-'*5}")
        for bucket_label, agg in sorted(merged.items()):
            if agg['n'] == 0:
                continue
            mean_val = agg['sum'] / agg['n']
            pct_pos = agg['pos_n'] / agg['n'] * 100
            L.append(f"    {bucket_label:<30s} | {mean_val:>+7.2f} | {agg['n']:>5d} | {pct_pos:>4.1f}%")

    L.append(f"\n  (nota: buckets son quintiles per-row-group, pueden solaparse entre chunks)")

    # ---- 3. Gems vs Non-gems ----
    L.append(f"\n{'~'*100}")
    L.append(f"3. COMPARACION GEMS VS NON-GEMS EN FORWARD")
    L.append(f"{'~'*100}")

    for is_gem_val, label in [(True, "GEMS"), (False, "NON-GEMS")]:
        n_total = group_stats.get((is_gem_val, 'fwd_pnl'), {}).get('n', 0)
        if n_total == 0:
            continue
        L.append(f"\n  {label} (N={n_total:,}):")
        for col in ['fwd_pnl', 'fwd_pf', 'fwd_trades', 'fwd_maxdd', 'fwd_wr']:
            acc = group_stats[(is_gem_val, col)]
            if acc['n'] == 0:
                continue
            mean_val = acc['mean']
            std_val = (acc['M2'] / acc['n']) ** 0.5 if acc['n'] > 1 else 0.0
            extra = ""
            if col == 'fwd_pnl' and acc['n'] > 0:
                pct_pos = acc['pos_count'] / acc['n'] * 100
                extra = f" | %pos={pct_pos:.1f}%"
            L.append(f"    {col:<15s}: mean={mean_val:>+8.2f}  std={std_val:>7.2f}{extra}")

    # ---- 4. Decision tree per-symbol ----
    L.append(f"\n{'~'*100}")
    L.append(f"4. DECISION TREE PER-SYMBOL: PREDECIR FWD_PNL > 0")
    L.append(f"{'~'*100}")

    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.model_selection import cross_val_score

        all_importances = {}   # symbol -> (n_rows, Series of importances)
        all_accuracies = {}    # symbol -> (accuracy_mean, accuracy_std, n_rows)
        biggest_symbol = None
        biggest_n = 0
        biggest_tree_rules = ""

        for cp_path in checkpoint_files:
            # Extract symbol name from filename: checkpoint_{SYMBOL}_all_train_v2.parquet
            cp_basename = os.path.basename(cp_path)
            symbol_name = cp_basename.replace("checkpoint_", "").replace(f"_all_train_v{CHECKPOINT_VERSION}.parquet", "")

            # Discover feature columns from schema (no data loaded)
            schema_names = pq.read_schema(cp_path).names
            feat_cols = [c for c in schema_names
                         if ('_tr' in c or '_te' in c or '_fu' in c) and not c.startswith('fwd_')]
            for extra in ('combined_score', 'robustness', 'ratio_pnl_te_tr'):
                if extra in schema_names and extra not in feat_cols:
                    feat_cols.append(extra)

            if 'fwd_pnl' not in schema_names:
                L.append(f"\n  {symbol_name}: sin columna fwd_pnl — saltando")
                continue

            cols_to_read = feat_cols + ['fwd_pnl']
            try:
                df = pd.read_parquet(cp_path, columns=cols_to_read)
            except Exception as e:
                L.append(f"\n  {symbol_name}: error leyendo parquet — {e}")
                continue

            if len(df) < 200:
                L.append(f"\n  {symbol_name}: insuficientes filas ({len(df)}) — saltando")
                del df; gc.collect()
                continue

            # Sample if too large
            if len(df) > 2_000_000:
                df = df.sample(n=2_000_000, random_state=42)

            # Build X, y
            y = (df['fwd_pnl'] > 0).astype(int)
            X = df[feat_cols].fillna(0)
            mask = y.notna()
            X = X[mask]
            y = y[mask]

            n_rows = len(X)
            if n_rows < 200:
                L.append(f"\n  {symbol_name}: insuficientes filas ({n_rows}) — saltando")
                del df; gc.collect()
                continue

            clf = DecisionTreeClassifier(max_depth=5, min_samples_leaf=1000, random_state=42)
            clf.fit(X, y)

            importances = pd.Series(clf.feature_importances_, index=feat_cols)
            all_importances[symbol_name] = (n_rows, importances)

            scores = cross_val_score(clf, X, y, cv=3, scoring='accuracy')
            all_accuracies[symbol_name] = (scores.mean(), scores.std(), n_rows)

            tree_rules = export_text(clf, feature_names=feat_cols,
                                     class_names=['fwd_neg', 'fwd_pos'])
            if n_rows > biggest_n:
                biggest_n = n_rows
                biggest_symbol = symbol_name
                biggest_tree_rules = tree_rules

            print(f"    Decision tree {symbol_name}: N={n_rows:,}  acc={scores.mean():.3f}")
            del df; gc.collect()

        # -- Weighted-average feature importances --
        if all_importances:
            total_n = sum(n for n, _ in all_importances.values())
            avg_imp = None
            for symbol_name, (n_rows, imp) in all_importances.items():
                weighted = imp * (n_rows / total_n)
                if avg_imp is None:
                    avg_imp = weighted.copy()
                else:
                    avg_imp = avg_imp.add(weighted, fill_value=0.0)

            avg_imp = avg_imp.sort_values(ascending=False)
            L.append(f"\n  Feature importances promediadas (ponderadas por N, total={total_n:,}):")
            for feat, imp in avg_imp.head(15).items():
                if imp > 0.001:
                    L.append(f"    {feat:<30s}: {imp:.4f}")

            # -- Accuracy per symbol --
            L.append(f"\n  Accuracy por simbolo (3-fold CV):")
            for sym in sorted(all_accuracies, key=lambda s: all_accuracies[s][2], reverse=True):
                acc_mean, acc_std, n = all_accuracies[sym]
                L.append(f"    {sym:<20s}: acc={acc_mean:.3f} +/- {acc_std:.3f}  (N={n:,})")

            # -- Tree rules for biggest symbol --
            if biggest_symbol and biggest_tree_rules:
                L.append(f"\n  Reglas del arbol — {biggest_symbol} (N={biggest_n:,}, max_depth=5):")
                for line in biggest_tree_rules.split('\n')[:60]:
                    L.append(f"    {line}")

                tree_path = os.path.join(output_dir, "analysis_all_train_tree_persymbol.txt")
                with open(tree_path, 'w', encoding='utf-8') as f:
                    f.write(f"Symbol: {biggest_symbol} (N={biggest_n:,})\n\n")
                    f.write(biggest_tree_rules)
        else:
            L.append(f"\n  No se pudo entrenar arbol para ningun simbolo.")

    except ImportError:
        L.append(f"\n  sklearn no instalado — saltando arbol de decision")

    # Save report
    report_text = '\n'.join(L)
    report_path = os.path.join(output_dir, "analysis_all_train_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n  Reporte all-train (incremental): {report_path}")
    print(f"\n{report_text}")


# ============================================
# CLI
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Walk-Forward Experiment: ingenieria inversa de filtros optimos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python walk_forward_experiment.py --symbols BTC/USDT,ETH/USDT --output-dir wf_experiment
  python walk_forward_experiment.py --all-symbols --output-dir wf_experiment
  python walk_forward_experiment.py --symbols BTC/USDT --step 2000 --fwd-size 2000 --opt-size 5000
  python walk_forward_experiment.py --analyze-only --output-dir wf_experiment
        """
    )

    parser.add_argument('--symbols', type=str, default=None,
                       help='Simbolos separados por coma')
    parser.add_argument('--all-symbols', action='store_true',
                       help='Usar todos los ~48 simbolos')
    parser.add_argument('--output-dir', type=str, default='wf_experiment',
                       help='Directorio de salida (default: wf_experiment)')
    # Lab Lite
    parser.add_argument('--lite-top-n', type=int, default=None,
                       help=f'Top N presets de lab_lite por anclaje (default: {DEFAULT_CONFIG["lite_top_n"]})')
    parser.add_argument('--no-lite-diversity', action='store_true',
                       help='Desactivar diversidad de familias en lab lite')

    # Ventanas
    parser.add_argument('--opt-size', type=int, default=None,
                       help=f'Ventana de optimizacion (default: {DEFAULT_CONFIG["opt_size"]})')
    parser.add_argument('--ext-size', type=int, default=None,
                       help=f'Ventana ext anterior (default: {DEFAULT_CONFIG["ext_size"]})')
    parser.add_argument('--fwd-size', type=int, default=None,
                       help=f'Ventana forward (default: {DEFAULT_CONFIG["fwd_size"]})')
    parser.add_argument('--step', type=int, default=None,
                       help=f'Paso entre anclajes (default: {DEFAULT_CONFIG["step"]})')

    # Extractor
    parser.add_argument('--extractor-top', type=int, default=None,
                       help=f'Top N por criterio en extractor (default: {DEFAULT_CONFIG["extractor_top_n"]})')

    # Lab params
    parser.add_argument('--commission', type=float, default=None,
                       help=f'Comision round-trip %% (default: {DEFAULT_CONFIG["commission"]})')

    # Paralelismo
    parser.add_argument('--workers', type=int, default=max(1, os.cpu_count() - 2),
                       help=f'Workers para precalculo paralelo (default: {max(1, os.cpu_count() - 2)})')

    # Modos
    parser.add_argument('--analyze-only', action='store_true',
                       help='Solo fase 2+3 sobre datos existentes')
    parser.add_argument('--no-cache', action='store_true',
                       help='Desactivar cache local de datos')
    parser.add_argument('--eval-all-train', action='store_true',
                       help='Evaluar en forward TODAS las configs que pasan train (Step 3b)')
    parser.add_argument('--max-anchors', type=int, default=None,
                       help='Limitar nº de anclajes por símbolo (calibración/smoke; default sin límite)')

    return parser.parse_args()


def build_config(args):
    config = dict(DEFAULT_CONFIG)
    if args.lite_top_n is not None:
        config["lite_top_n"] = args.lite_top_n
    if args.no_lite_diversity:
        config["lite_diversity"] = False
    if args.opt_size is not None:
        config["opt_size"] = args.opt_size
    if args.ext_size is not None:
        config["ext_size"] = args.ext_size
    if args.fwd_size is not None:
        config["fwd_size"] = args.fwd_size
    if args.step is not None:
        config["step"] = args.step
    if args.extractor_top is not None:
        config["extractor_top_n"] = args.extractor_top
    if getattr(args, "max_anchors", None) is not None:
        config["max_anchors"] = args.max_anchors
    if args.commission is not None:
        config["commission"] = args.commission
    config["eval_all_train"] = args.eval_all_train
    return config


# ============================================
# MAIN
# ============================================

def main():
    args = parse_args()
    config = build_config(args)
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    elif args.all_symbols:
        symbols = list(DEFAULT_SYMBOLS)
    else:
        symbols = list(DEFAULT_SYMBOLS[:3])  # Default: primeros 3 para test

    # Initialize CUDA in main process only (BEFORE banner, BEFORE workers)
    _init_cuda()

    # Banner
    print("=" * 70)
    print("WALK-FORWARD EXPERIMENT — Ingenieria inversa de filtros")
    print("=" * 70)
    print(f"Simbolos:     {len(symbols)}")
    print(f"Opt size:     {config['opt_size']}")
    print(f"Ext size:     {config['ext_size']}")
    print(f"Fwd size:     {config['fwd_size']}")
    print(f"Step:         {config['step']}")
    print(f"Lab Lite:     top {config['lite_top_n']} presets, diversidad={'SI' if config['lite_diversity'] else 'NO'}")
    print(f"Extractor:    top {config['extractor_top_n']} por criterio")
    print(f"Output:       {output_dir}")
    print(f"Workers:      {args.workers}")
    print(f"Analyze only: {args.analyze_only}")
    print(f"Eval all:     {config.get('eval_all_train', False)}")
    _gpu_name = _cuda_sim.gpu_name.decode() if (USE_CUDA and _cuda_sim and isinstance(_cuda_sim.gpu_name, bytes)) else (_cuda_sim.gpu_name if USE_CUDA and _cuda_sim else None)
    print(f"CUDA:         {'ON (' + _gpu_name + ')' if _gpu_name else 'OFF (CPU)'}")
    print("=" * 70)

    # Save config
    config_path = os.path.join(output_dir, "experiment_config.json")
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    # ---- ANALYZE ONLY MODE ----
    if args.analyze_only:
        raw_path = os.path.join(output_dir, "dataset_raw.parquet")
        labeled_path = os.path.join(output_dir, "dataset_labeled.parquet")

        if os.path.exists(labeled_path):
            print(f"\nCargando dataset etiquetado: {labeled_path}")
            df = pd.read_parquet(labeled_path)
        elif os.path.exists(raw_path):
            print(f"\nCargando dataset raw: {raw_path}")
            df = pd.read_parquet(raw_path)
            print("\nFase 2: Etiquetado...")
            df = label_dataset(df, config)
            df.to_parquet(labeled_path, index=False)
        else:
            print(f"ERROR: No se encuentra {raw_path} ni {labeled_path}")
            sys.exit(1)

        print("\nFase 3: Analisis (gems)...")
        run_analysis(df, output_dir)

        # Also analyze all-train dataset if available
        all_train_path = os.path.join(output_dir, "dataset_all_train_raw.parquet")
        all_train_done = False
        if os.path.exists(all_train_path):
            print("\nFase 3b: Analisis (all-train)...")
            try:
                df_at = pd.read_parquet(all_train_path)
                run_analysis_all_train(df_at, output_dir)
                all_train_done = True
            except Exception as e:
                is_memory_error = ("ArrowMemoryError" in type(e).__name__ or
                                   "MemoryError" in type(e).__name__ or
                                   isinstance(e, MemoryError))
                if is_memory_error:
                    print(f"  WARNING: all-train parquet too large for memory ({type(e).__name__}), "
                          f"falling back to incremental analysis.")
                    gc.collect()
                else:
                    raise
        # Fallback / primary: incremental analysis from per-symbol checkpoints
        if not all_train_done:
            import glob as _glob
            checkpoint_files = sorted(_glob.glob(
                os.path.join(output_dir, f"checkpoint_*_all_train_v{CHECKPOINT_VERSION}.parquet")))
            if checkpoint_files:
                print("\nFase 3b: Analisis (all-train, incremental desde checkpoints)...")
                run_analysis_all_train_incremental(checkpoint_files, output_dir)
        return

    # ---- PHASE 1: DATA GENERATION ----
    print("\n" + "=" * 70)
    print("FASE 1: GENERACION DE DATOS")
    print("=" * 70)

    # Import modules
    print("\nImportando modulos...")
    t0 = time.time()
    lab = import_lab()
    extractor = import_extractor()
    lite = import_lite()
    print(f"Modulos importados ({time.time()-t0:.1f}s)")

    # Cache setup
    if not args.no_cache:
        import data_cache
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "data_cache")
        data_cache.CACHE_DIR = cache_dir

        # Calculate needed candles
        max_anchors = max(10, 20000 // config["step"])
        total_needed = (config["warmup"] + config["ext_size"] + config["opt_size"] +
                       config["fwd_size"] + max_anchors * config["step"] + 1000)
        print(f"\nPre-descargando datos ({total_needed} velas por simbolo)...")
        data_cache.prefetch_symbols(symbols, "1h", total_needed)
        data_cache.patch_modules(None, lab, 0, total_needed)
        data_cache.set_trim_tail(0)  # Asegurar que no hay trim residual de runs anteriores

    # Process each symbol
    eval_all_train = config.get("eval_all_train", False)
    t_global = time.time()
    symbols_ok = []

    for i, symbol in enumerate(symbols, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(symbols)}] {symbol}")
        print(f"{'='*70}")

        t_sym = time.time()
        try:
            gem_n, at_n = process_symbol(symbol, config, output_dir, lab, extractor, lite,
                                         n_workers=args.workers)
            if gem_n > 0:
                symbols_ok.append(symbol)
            parts = []
            if gem_n > 0:
                parts.append(f"{gem_n} gems")
            if at_n > 0:
                parts.append(f"{at_n:,} all-train")
            print(f"\n  {symbol}: {' + '.join(parts) if parts else 'sin observaciones'} ({time.time()-t_sym:.1f}s)")
        except Exception as e:
            print(f"\n  ERROR en {symbol}: {e}")
            traceback.print_exc()

    # Re-read checkpoints from disk and concatenate
    all_gem_dfs = []
    for symbol in symbols_ok:
        cp = os.path.join(output_dir, f"checkpoint_{sc(symbol)}_v{CHECKPOINT_VERSION}.parquet")
        if os.path.exists(cp):
            all_gem_dfs.append(pd.read_parquet(cp))

    if not all_gem_dfs:
        print("\nSin datos de gems generados. Abortando.")
        sys.exit(1)

    # Concatenate gems
    dataset_raw = pd.concat(all_gem_dfs, ignore_index=True)
    del all_gem_dfs
    gc.collect()
    raw_path = os.path.join(output_dir, "dataset_raw.parquet")
    dataset_raw.to_parquet(raw_path, index=False)
    print(f"\nDataset raw (gems): {raw_path} ({len(dataset_raw)} filas)")

    # Concatenate all-train from checkpoints (skip if too large for RAM)
    dataset_all_train = None
    all_train_raw_path = os.path.join(output_dir, "dataset_all_train_raw.parquet")
    all_train_concat_failed = False
    if eval_all_train:
        import pyarrow.parquet as pq
        total_all_rows = 0
        all_train_cps = []
        for symbol in symbols_ok:
            cp = os.path.join(output_dir, f"checkpoint_{sc(symbol)}_all_train_v{CHECKPOINT_VERSION}.parquet")
            if os.path.exists(cp):
                total_all_rows += pq.read_metadata(cp).num_rows
                all_train_cps.append(cp)

        if total_all_rows > 50_000_000:
            print(f"\n  Dataset all-train demasiado grande ({total_all_rows:,} filas) para consolidar en RAM.")
            print(f"  Usar analyze_train_test.py por checkpoint individual o por directorio.")
            all_train_concat_failed = True
        elif all_train_cps:
            try:
                all_train_dfs = [pd.read_parquet(cp) for cp in all_train_cps]
                dataset_all_train = pd.concat(all_train_dfs, ignore_index=True)
                del all_train_dfs
                gc.collect()
                dataset_all_train.to_parquet(all_train_raw_path, index=False)
                print(f"Dataset raw (all-train): {all_train_raw_path} ({len(dataset_all_train):,} filas)")
            except Exception as e:
                is_memory_error = ("ArrowMemoryError" in type(e).__name__ or
                                   "MemoryError" in type(e).__name__ or
                                   isinstance(e, MemoryError))
                if is_memory_error:
                    print(f"\n  WARNING: All-train dataset too large for memory ({type(e).__name__}), "
                          f"skipping concatenation.")
                    print(f"  Will use incremental per-checkpoint analysis instead.")
                    dataset_all_train = None
                    all_train_concat_failed = True
                    try:
                        del all_train_dfs
                    except NameError:
                        pass
                    gc.collect()
                else:
                    raise

    elapsed = time.time() - t_global
    print(f"Fase 1 completada: {elapsed:.1f}s ({elapsed/60:.1f}m)")

    # ---- PHASE 2: LABELING ----
    print("\n" + "=" * 70)
    print("FASE 2: ETIQUETADO")
    print("=" * 70)

    dataset_labeled = label_dataset(dataset_raw, config)
    labeled_path = os.path.join(output_dir, "dataset_labeled.parquet")
    dataset_labeled.to_parquet(labeled_path, index=False)
    print(f"Dataset etiquetado (gems): {labeled_path}")

    # ---- PHASE 3: ANALYSIS ----
    print("\n" + "=" * 70)
    print("FASE 3: ANALISIS DE PATRONES (GEMS)")
    print("=" * 70)

    run_analysis(dataset_labeled, output_dir)

    # ---- PHASE 3b: ALL-TRAIN ANALYSIS ----
    if dataset_all_train is not None and len(dataset_all_train) > 0:
        print("\n" + "=" * 70)
        print("FASE 3b: ANALISIS ALL-TRAIN DATASET")
        print("=" * 70)
        run_analysis_all_train(dataset_all_train, output_dir)
    elif all_train_concat_failed:
        print("\n" + "=" * 70)
        print("FASE 3b: ANALISIS ALL-TRAIN DATASET (INCREMENTAL)")
        print("=" * 70)
        checkpoint_files = []
        for symbol in symbols_ok:
            cp = os.path.join(output_dir, f"checkpoint_{sc(symbol)}_all_train_v{CHECKPOINT_VERSION}.parquet")
            if os.path.exists(cp):
                checkpoint_files.append(cp)
        if checkpoint_files:
            run_analysis_all_train_incremental(checkpoint_files, output_dir)

    # Summary
    print(f"\n{'='*70}")
    print(f"EXPERIMENTO COMPLETADO")
    print(f"{'='*70}")
    print(f"Total observaciones (gems): {len(dataset_labeled)}")
    if dataset_all_train is not None:
        print(f"Total observaciones (all-train): {len(dataset_all_train):,}")
    elif all_train_concat_failed:
        print(f"Total observaciones (all-train): concatenacion omitida (memoria), analisis incremental completado")
    print(f"Simbolos: {dataset_labeled['symbol'].nunique()}")
    print(f"Tiempo total: {time.time()-t_global:.0f}s ({(time.time()-t_global)/60:.1f}m)")
    print(f"Archivos:")
    print(f"  {raw_path}")
    print(f"  {labeled_path}")
    if dataset_all_train is not None:
        print(f"  {all_train_raw_path}")
    print(f"  {os.path.join(output_dir, 'analysis_report.txt')}")
    print(f"  {os.path.join(output_dir, 'analysis_correlations.csv')}")
    if dataset_all_train is not None or all_train_concat_failed:
        print(f"  {os.path.join(output_dir, 'analysis_all_train_report.txt')}")
        print(f"  {os.path.join(output_dir, 'analysis_all_train_correlations.csv')}")


if __name__ == "__main__":
    main()
