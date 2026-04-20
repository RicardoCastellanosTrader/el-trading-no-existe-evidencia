#!/usr/bin/env python3
"""
regime_walk_forward.py — Walk-Forward por Régimen

Valida especialistas de cluster: para cada cluster K, los primeros episodios
son train y los últimos son forward. Mide si las métricas de train dentro de
un régimen predicen el rendimiento forward dentro del mismo régimen.

Uso:
    python regime_walk_forward.py
    python regime_walk_forward.py --symbols BTC/USDT,ETH/USDT
    python regime_walk_forward.py --train-ratio 0.7 --min-episode-bars 50
    python regime_walk_forward.py --output-dir regime_wf/
    python regime_walk_forward.py --presets-dir output/
"""

import gc
import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
import joblib
import pyarrow.parquet as pq
from datetime import datetime
from collections import defaultdict
from math import sqrt, log
import json

# Fix Windows cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from regime_features import compute_regime_features

# ============================================
# CUDA ACCELERATION (optional)
# ============================================
_cuda_sim = None
_USE_CUDA = False
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'combolab'))
    from lab_cuda import CUDASimulatorOptimized
    _cuda_sim = CUDASimulatorOptimized()
    if _cuda_sim.gpu_available:
        _USE_CUDA = True
        print(f"[CUDA] Aceleración GPU habilitada: {_cuda_sim.gpu_name}")
    else:
        print("[CUDA] GPU no disponible, usando Numba CPU")
        _cuda_sim = None
except ImportError as e:
    print(f"[CUDA] lab_cuda no disponible ({e}), usando Numba CPU")

# ============================================
# CONFIGURATION
# ============================================

SYMBOLS = [
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

TRAIN_RATIO = 0.70
MIN_EPISODE_BARS = 50
MIN_TRADES_CLUSTER = 30
MIN_EPISODES_VALIDATE = 5
TOP_TRAIN = 30000
OUTPUT_DIR = "regime_wf"
CACHE_DIR = "data_cache"
MODEL_DIR = "regime_models"
TIMEFRAME = "1h"
TOXIC_TAIL = 50


def sym_key(symbol):
    return symbol.replace("/USDT", "").replace("/", "")


def sym_clean(symbol):
    return symbol.replace("/", "")


# ============================================
# STEP 1: LOAD DATA & MODEL
# ============================================

def load_full_history(symbol):
    """Load full OHLCV history from data_cache."""
    sc = sym_clean(symbol)
    path = os.path.join(CACHE_DIR, f"{sc}_{TIMEFRAME}.parquet")
    if not os.path.exists(path):
        print(f"   ⚠️  No cache: {path}")
        return None
    df = pd.read_parquet(path)
    if len(df) == 0:
        return None
    result = df.copy()
    if 'timestamp_ms' in result.columns:
        result['timestamp'] = pd.to_datetime(result['timestamp_ms'], unit='ms')
    result = result[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    return result


def load_regime_model(symbol):
    """Load pre-trained regime model."""
    sk = sym_key(symbol)
    path = os.path.join(MODEL_DIR, f"{sk}_regime.joblib")
    if not os.path.exists(path):
        print(f"   ⚠️  No model: {path}")
        return None
    return joblib.load(path)


def compute_cluster_labels(df, model_data):
    """Apply pre-trained regime model to data."""
    features, valid_mask = compute_regime_features(df, lookback=model_data.get('lookback', 100))
    gmm = model_data['gmm']
    scaler = model_data['scaler']
    n_clusters = model_data['n_clusters']

    n_bars = len(df)
    labels = np.full(n_bars, -1, dtype=np.int64)
    valid_features = features[valid_mask]
    if len(valid_features) > 0:
        X = scaler.transform(valid_features)
        pred = gmm.predict(X)
        valid_indices = np.where(valid_mask)[0]
        for i, idx in enumerate(valid_indices):
            labels[idx] = pred[i]
    return labels, n_clusters


def compute_gmm_probs(df, model_data):
    """Pre-compute GMM probabilities for each bar.

    Returns full_probs: array (n_bars, n_clusters) where full_probs[t, k] is
    the probability that bar t belongs to cluster k according to the GMM.
    Bars without valid features (early lookback period) have all-zero probs.
    """
    features, valid_mask = compute_regime_features(
        df, lookback=model_data.get('lookback', 100))
    scaler = model_data['scaler']
    gmm = model_data['gmm']
    n_clusters = model_data['n_clusters']
    n_bars = len(df)

    full_probs = np.zeros((n_bars, n_clusters))
    valid_features = features[valid_mask]
    if len(valid_features) > 0:
        X = scaler.transform(valid_features)
        probs = gmm.predict_proba(X)
        valid_indices = np.where(valid_mask)[0]
        full_probs[valid_indices] = probs

    return full_probs


# ============================================
# STEP 2: IDENTIFY EPISODES
# ============================================

def identify_episodes(cluster_labels, n_clusters, min_bars=50):
    """Identify contiguous episodes per cluster.

    Returns: dict {cluster_id: [(start_bar, end_bar), ...]}
    Episodes shorter than min_bars are discarded.
    """
    n_bars = len(cluster_labels)
    episodes = defaultdict(list)

    current_label = cluster_labels[0]
    ep_start = 0

    for i in range(1, n_bars):
        if cluster_labels[i] != current_label:
            # Episode ended
            if current_label >= 0:
                ep_len = i - ep_start
                if ep_len >= min_bars:
                    episodes[current_label].append((ep_start, i))
            current_label = cluster_labels[i]
            ep_start = i

    # Last episode
    if current_label >= 0:
        ep_len = n_bars - ep_start
        if ep_len >= min_bars:
            episodes[current_label].append((ep_start, n_bars))

    return dict(episodes)


# ============================================
# STEP 3: BUILD DOUBLED REGIME LABELS
# ============================================

def build_regime_labels(cluster_labels, episodes, n_clusters, train_ratio=0.70,
                        toxic_tail=0, gmm_probs=None, confirm_threshold=0.75,
                        max_toxic_tail=100, min_toxic_tail=5):
    """Build doubled regime labels: train labels 0..K-1, forward labels K..2K-1.

    Toxic tail modes:
    - Fixed (toxic_tail > 0, gmm_probs is None): extend each forward episode
      by a fixed number of bars.
    - Dynamic (gmm_probs is not None): simulate GMM classifier bar-by-bar after
      each forward episode ends until P(new_regime) >= confirm_threshold.
      The number of bars until confirmation is the toxic tail for that episode.

    Returns:
        regime_labels: int64 array (n_bars,)
        n_clusters_doubled: 2 * n_clusters
        split_info: dict {cluster_id: {train_episodes, fwd_episodes, train_bars, fwd_bars, ...}}
    """
    n_bars = len(cluster_labels)
    regime_labels = np.full(n_bars, -1, dtype=np.int64)
    split_info = {}
    dynamic_mode = gmm_probs is not None

    for k in range(n_clusters):
        eps = episodes.get(k, [])
        n_eps = len(eps)

        if n_eps < MIN_EPISODES_VALIDATE:
            split_info[k] = {
                'total_episodes': n_eps,
                'train_episodes': 0, 'fwd_episodes': 0,
                'train_bars': 0, 'fwd_bars': 0,
                'toxic_tail_bars': 0,
                'toxic_tails': [],
                'valid': False, 'reason': f'insufficient episodes ({n_eps} < {MIN_EPISODES_VALIDATE})'
            }
            # Still label them as train (for global analysis)
            for start, end in eps:
                regime_labels[start:end] = k
            continue

        n_train = max(1, int(n_eps * train_ratio))
        n_fwd = n_eps - n_train

        train_eps = eps[:n_train]
        fwd_eps = eps[n_train:]

        train_bars = sum(e - s for s, e in train_eps)

        # Label train episodes as cluster K (no extension)
        for start, end in train_eps:
            regime_labels[start:end] = k

        # Label forward episodes as cluster K + n_clusters, with toxic tail
        fwd_label = k + n_clusters
        fwd_bars = 0
        toxic_bars = 0
        toxic_tails = []  # per-episode tail lengths

        for i, (start, end) in enumerate(fwd_eps):
            # Original episode
            regime_labels[start:end] = fwd_label
            fwd_bars += (end - start)

            # Compute tail length
            if dynamic_mode:
                # Dynamic: scan bars after episode end until another cluster
                # reaches confirm_threshold probability
                tail_length = max_toxic_tail  # default if never confirms
                scan_end = min(end + max_toxic_tail, n_bars)
                for t in range(end, scan_end):
                    # Check if any cluster different from K exceeds threshold
                    confirmed = False
                    for j in range(n_clusters):
                        if j != k and gmm_probs[t, j] >= confirm_threshold:
                            tail_length = max(t - end, min_toxic_tail)
                            confirmed = True
                            break
                    if confirmed:
                        break

                # Apply tail
                extended_end = min(end + tail_length, n_bars)
                # Don't overlap with next forward episode of same cluster
                if i + 1 < len(fwd_eps):
                    extended_end = min(extended_end, fwd_eps[i + 1][0])
                if extended_end > end:
                    regime_labels[end:extended_end] = fwd_label
                    actual_tail = extended_end - end
                    fwd_bars += actual_tail
                    toxic_bars += actual_tail
                    toxic_tails.append(actual_tail)
                else:
                    toxic_tails.append(0)

            elif toxic_tail > 0:
                # Fixed tail (backward compat)
                extended_end = min(end + toxic_tail, n_bars)
                # Don't overlap with next forward episode of same cluster
                if i + 1 < len(fwd_eps):
                    extended_end = min(extended_end, fwd_eps[i + 1][0])
                # Label the toxic tail bars as forward for cluster K
                if extended_end > end:
                    regime_labels[end:extended_end] = fwd_label
                    tail_len = extended_end - end
                    fwd_bars += tail_len
                    toxic_bars += tail_len

        info = {
            'total_episodes': n_eps,
            'train_episodes': n_train, 'fwd_episodes': n_fwd,
            'train_bars': train_bars, 'fwd_bars': fwd_bars,
            'toxic_tail_bars': toxic_bars,
            'toxic_tails': toxic_tails,
            'valid': True,
        }
        if dynamic_mode and toxic_tails:
            arr = np.array(toxic_tails)
            info['toxic_tail_mean'] = float(np.mean(arr))
            info['toxic_tail_median'] = float(np.median(arr))
            info['toxic_tail_min'] = int(np.min(arr))
            info['toxic_tail_max'] = int(np.max(arr))
        split_info[k] = info

    n_clusters_doubled = 2 * n_clusters
    return regime_labels, n_clusters_doubled, split_info


# ============================================
# STEP 4: LOAD PRESETS
# ============================================

def load_presets(symbol, presets_dir):
    """Load presets from presets_SYMBOL.csv or fallback to lab_historico hardcoded presets."""
    sc = sym_clean(symbol)

    # Search in presets_dir and subdirectories
    candidates = [
        os.path.join(presets_dir, sc, f"presets_{sc}.csv"),
        os.path.join(presets_dir, f"presets_{sc}.csv"),
        os.path.join(".", f"presets_{sc}.csv"),
    ]

    for path in candidates:
        if os.path.exists(path):
            df = pd.read_csv(path)
            presets = []
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
            print(f"   📋 Loaded {len(presets)} presets from {path}")
            return presets

    # Fallback: use hardcoded SYMBOL_ZONE_PRESETS from lab_historico
    try:
        lab = _import_lab()
        hardcoded = lab.SYMBOL_ZONE_PRESETS.get(symbol, [])
        if hardcoded:
            print(f"   📋 Loaded {len(hardcoded)} presets from lab_historico SYMBOL_ZONE_PRESETS")
            return hardcoded
    except Exception as e:
        print(f"   ⚠️  Error loading hardcoded presets: {e}")

    print(f"   ⚠️  No presets found for {symbol}")
    return None


# ============================================
# STEP 5: SIMULATION & ANALYSIS
# ============================================

def _import_lab():
    """Import lab_historico as a proper module (not dynamic) for Numba cache compat."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    import lab_historico_numba_v8_3 as lab
    return lab


def process_symbol(symbol, presets, df, model_data, args):
    """Run regime walk-forward for one symbol."""
    lab = _import_lab()

    sk = sym_key(symbol)
    sc = sym_clean(symbol)
    n_bars = len(df)

    print(f"\n   📊 {n_bars} barras: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")

    # Step 2: Cluster labels & episodes
    cluster_labels, n_clusters = compute_cluster_labels(df, model_data)
    n_labeled = int(np.sum(cluster_labels >= 0))
    print(f"   🔬 {n_clusters} clusters, {n_labeled}/{n_bars} barras etiquetadas")

    episodes = identify_episodes(cluster_labels, n_clusters, min_bars=args.min_episode_bars)
    for k in range(n_clusters):
        eps = episodes.get(k, [])
        total_bars_k = sum(e - s for s, e in eps)
        print(f"      C{k}: {len(eps)} episodios, {total_bars_k} barras")

    # Step 3: Build doubled labels (with optional toxic tail on forward episodes)
    toxic_tail = getattr(args, 'toxic_tail', 0)
    toxic_tail_mode = getattr(args, 'toxic_tail_mode', 'fixed')

    gmm_probs = None
    if toxic_tail_mode == 'dynamic':
        print(f"   🔮 Computing GMM probabilities for dynamic toxic tail...")
        gmm_probs = compute_gmm_probs(df, model_data)
        n_valid = int(np.sum(gmm_probs.sum(axis=1) > 0))
        print(f"      {n_valid}/{n_bars} bars with valid GMM probs")

    regime_labels, n_doubled, split_info = build_regime_labels(
        cluster_labels, episodes, n_clusters, train_ratio=args.train_ratio,
        toxic_tail=toxic_tail, gmm_probs=gmm_probs,
        confirm_threshold=getattr(args, 'confirm_threshold', 0.75),
        max_toxic_tail=getattr(args, 'max_toxic_tail', 100),
        min_toxic_tail=getattr(args, 'min_toxic_tail', 5))

    valid_clusters = [k for k in range(n_clusters) if split_info[k]['valid']]
    if not valid_clusters:
        print(f"   ⚠️  No cluster has enough episodes for validation")
        return None

    for k in valid_clusters:
        si = split_info[k]
        if toxic_tail_mode == 'dynamic' and 'toxic_tail_mean' in si:
            toxic_str = (f" [toxic: mean={si['toxic_tail_mean']:.0f} "
                         f"med={si['toxic_tail_median']:.0f} "
                         f"min={si['toxic_tail_min']} max={si['toxic_tail_max']}]")
        elif si.get('toxic_tail_bars', 0) > 0:
            toxic_str = f" [+{si['toxic_tail_bars']} toxic]"
        else:
            toxic_str = ""
        print(f"      C{k}: train={si['train_episodes']} eps ({si['train_bars']} bars)"
              f" | fwd={si['fwd_episodes']} eps ({si['fwd_bars']} bars){toxic_str}")

    # Step 4: Simulate each preset — INCREMENTAL: save to parquet, free RAM
    configs = lab.generate_valid_configs()
    n_configs = len(configs)
    print(f"   📋 {n_configs:,} configs × {len(presets)} presets")

    parts_dir = os.path.join(args.output_dir, f"_parts_{sc}")
    os.makedirs(parts_dir, exist_ok=True)

    variant_idx = 0
    total_written = 0
    skipped_variants = 0

    for p_idx, preset in enumerate(presets):
        for hyst_mult in [0.0, 0.5]:
            hyst_tag = f"H{hyst_mult:.1f}".replace(".", "")
            fast_type, fast_len = preset[0], preset[1]
            slow_type, slow_len = preset[4], preset[5]
            label = f"{fast_type}({fast_len})/{slow_type}({slow_len})_{hyst_tag}"

            # --- Resume logic: skip if all part files for this variant exist ---
            all_parts_exist = all(
                os.path.exists(os.path.join(parts_dir, f"part_{variant_idx:04d}_C{k}.parquet"))
                for k in valid_clusters
            )
            if all_parts_exist:
                skipped_variants += 1
                variant_idx += 1
                continue
            # -------------------------------------------------------------------

            print(f"\n   🔄 Preset {p_idx+1}/{len(presets)}: {label}")

            # Precalculate
            data = lab.precalculate_all_data(df, preset=preset, hyst_mult=hyst_mult, symbol=symbol)

            # Single simulation pass with doubled labels
            t0 = time.time()
            if _USE_CUDA and _cuda_sim is not None:
                handle = _cuda_sim.upload_data(data)
                results, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = \
                    _cuda_sim.run_on_slice(
                        configs, handle, 0, len(data['close']),
                        lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT, lab.TS_PERCENT,
                        lab.COOLDOWN_BARS, lab.COMMISSION_ROUND_TRIP,
                        cluster_labels=regime_labels, n_clusters=n_doubled)
                engine_tag = "CUDA"
            else:
                results, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = \
                    lab.run_on_slice(
                        configs, data, 0, len(data['close']),
                        lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT, lab.TS_PERCENT,
                        lab.COOLDOWN_BARS, lab.COMMISSION_ROUND_TRIP,
                        cluster_labels=regime_labels, n_clusters=n_doubled)
                engine_tag = "CPU"
            elapsed = time.time() - t0
            print(f"      ⏱️  {elapsed:.1f}s ({n_configs/elapsed:,.0f} configs/s) [{engine_tag}]")

            # Global metrics (computed once per variant)
            pnl_global = results[:, 0]
            trades_global = results[:, 1]
            gp_global = results[:, 5]
            gl_global = results[:, 6]
            pf_global = np.where(gl_global > 0, gp_global / gl_global,
                                 np.where(gp_global > 0, 5.0, 0.0))

            # For each valid cluster, extract metrics and flush to parquet
            for k in valid_clusters:
                k_train = k
                k_fwd = k + n_clusters
                si = split_info[k]

                # Train metrics
                pnl_tr = cl_pnl[:, k_train]
                trades_tr = cl_trades[:, k_train].astype(np.float64)
                wins_tr = cl_wins[:, k_train]
                maxdd_tr = cl_maxdd[:, k_train]
                gp_tr = cl_gp[:, k_train]
                gl_tr = cl_gl[:, k_train]

                # Forward metrics
                pnl_fwd = cl_pnl[:, k_fwd]
                trades_fwd = cl_trades[:, k_fwd].astype(np.float64)
                wins_fwd = cl_wins[:, k_fwd]
                maxdd_fwd = cl_maxdd[:, k_fwd]
                gp_fwd = cl_gp[:, k_fwd]
                gl_fwd = cl_gl[:, k_fwd]

                # PF
                pf_tr = np.where(gl_tr > 0, gp_tr / gl_tr, np.where(gp_tr > 0, 5.0, 0.0))
                pf_fwd = np.where(gl_fwd > 0, gp_fwd / gl_fwd, np.where(gp_fwd > 0, 5.0, 0.0))

                # Score
                cancels_zero = np.zeros_like(trades_tr)
                score_tr, pnl_ann_tr, _, _, _, _ = lab.calc_score_v63(
                    pnl_tr, maxdd_tr, gp_tr, gl_tr, trades_tr, cancels_zero, si['train_bars'])
                score_fwd, pnl_ann_fwd, _, _, _, _ = lab.calc_score_v63(
                    pnl_fwd, maxdd_fwd, gp_fwd, gl_fwd, trades_fwd, cancels_zero, si['fwd_bars'])

                # Save partial results to parquet (includes raw metrics for specialist extraction)
                part_df = pd.DataFrame({
                    'config_id': configs.astype(np.uint32),
                    'preset_label': label,
                    'cluster': np.int32(k),
                    'pf_tr': pf_tr.astype(np.float32),
                    'pf_fwd': pf_fwd.astype(np.float32),
                    'pnl_tr': pnl_tr.astype(np.float32),
                    'pnl_fwd': pnl_fwd.astype(np.float32),
                    'pnl_ann_tr': pnl_ann_tr.astype(np.float32),
                    'pnl_ann_fwd': pnl_ann_fwd.astype(np.float32),
                    'trades_tr': trades_tr.astype(np.float32),
                    'trades_fwd': trades_fwd.astype(np.float32),
                    'wins_tr': wins_tr.astype(np.float32),
                    'wins_fwd': wins_fwd.astype(np.float32),
                    'maxdd_tr': maxdd_tr.astype(np.float32),
                    'maxdd_fwd': maxdd_fwd.astype(np.float32),
                    'gp_tr': gp_tr.astype(np.float32),
                    'gp_fwd': gp_fwd.astype(np.float32),
                    'gl_tr': gl_tr.astype(np.float32),
                    'gl_fwd': gl_fwd.astype(np.float32),
                    'score_tr': score_tr.astype(np.float32),
                    'score_fwd': score_fwd.astype(np.float32),
                    'pf_global': pf_global.astype(np.float32),
                    'pnl_global': pnl_global.astype(np.float32),
                    'trades_global': trades_global.astype(np.float32),
                })
                part_path = os.path.join(parts_dir, f"part_{variant_idx:04d}_C{k}.parquet")
                part_df.to_parquet(part_path, index=False)
                total_written += len(part_df)
                del part_df, pnl_tr, trades_tr, wins_tr, maxdd_tr, gp_tr, gl_tr
                del pnl_fwd, trades_fwd, wins_fwd, maxdd_fwd, gp_fwd, gl_fwd
                del pf_tr, pf_fwd, score_tr, score_fwd, pnl_ann_tr, pnl_ann_fwd

            # Free heavy simulation arrays before next variant
            del results, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl
            del data, pnl_global, trades_global, gp_global, gl_global, pf_global
            gc.collect()
            variant_idx += 1

    if skipped_variants > 0:
        print(f"\n   ⏩ Resume: {skipped_variants} variantes ya existían, saltadas")

    if total_written == 0 and skipped_variants == 0:
        print(f"   ⚠️  No results")
        return None

    print(f"\n   💾 {total_written:,} rows nuevas en {variant_idx - skipped_variants} part files"
          f" ({skipped_variants} previas) → {parts_dir}")

    return {
        'symbol': symbol,
        'n_bars': n_bars,
        'n_clusters': n_clusters,
        'cluster_names': model_data['cluster_names'],
        'split_info': split_info,
        'episodes': episodes,
        'cluster_labels': cluster_labels,
        'parts_dir': parts_dir,
        'toxic_tail': toxic_tail,
        'toxic_tail_mode': toxic_tail_mode,
        'confirm_threshold': getattr(args, 'confirm_threshold', 0.75),
    }


# ============================================
# STEP 6: CORRELATION ANALYSIS
# ============================================

MAX_CORR_ROWS = 50_000_000  # safe_corr max rows before sampling


def safe_corr(x, y, min_n=20):
    """Pearson correlation with NaN/inf handling. Samples to MAX_CORR_ROWS if needed."""
    mask = np.isfinite(x) & np.isfinite(y)
    x_clean = x[mask]
    y_clean = y[mask]
    n = len(x_clean)
    if n < min_n:
        return np.nan
    if n > MAX_CORR_ROWS:
        rng = np.random.RandomState(42)
        idx = rng.choice(n, MAX_CORR_ROWS, replace=False)
        x_clean = x_clean[idx]
        y_clean = y_clean[idx]
    r = np.corrcoef(x_clean, y_clean)[0, 1]
    return r if np.isfinite(r) else np.nan


# --- Online Pearson helpers (O(1) RAM for global correlations) ---

def _init_pearson():
    return {'n': 0, 'sx': 0.0, 'sy': 0.0, 'sxy': 0.0, 'sx2': 0.0, 'sy2': 0.0}


def _update_pearson(state, x, y):
    """Accumulate sums for online Pearson. x, y are numpy arrays."""
    mask = np.isfinite(x) & np.isfinite(y)
    xc, yc = x[mask].astype(np.float64), y[mask].astype(np.float64)
    state['n'] += len(xc)
    state['sx'] += xc.sum()
    state['sy'] += yc.sum()
    state['sxy'] += (xc * yc).sum()
    state['sx2'] += (xc * xc).sum()
    state['sy2'] += (yc * yc).sum()


def _finalize_pearson(state, min_n=20):
    """Compute Pearson r from accumulated sums."""
    n = state['n']
    if n < min_n:
        return np.nan
    num = n * state['sxy'] - state['sx'] * state['sy']
    den2 = (n * state['sx2'] - state['sx'] ** 2) * (n * state['sy2'] - state['sy'] ** 2)
    if den2 <= 0:
        return np.nan
    r = num / np.sqrt(den2)
    return r if np.isfinite(r) else np.nan


def _load_cluster_data(parts_dir, cluster_id, columns, max_rows=50_000_000):
    """Load specific columns for one cluster from parquet part files.

    Loads incrementally. If total rows exceed max_rows, each file is
    proportionally sampled so the result fits in memory.
    """
    import glob as glob_mod
    pattern = os.path.join(parts_dir, f"part_*_C{cluster_id}.parquet")
    files = sorted(glob_mod.glob(pattern))
    if not files:
        return pd.DataFrame()

    # Count total rows from metadata (no data loaded)
    total_rows = 0
    file_rows = []
    for f in files:
        n = pq.ParquetFile(f).metadata.num_rows
        file_rows.append(n)
        total_rows += n

    frac = min(1.0, max_rows / max(total_rows, 1))

    chunks = []
    for f, nr in zip(files, file_rows):
        chunk = pd.read_parquet(f, columns=columns)
        if frac < 1.0:
            sample_n = max(1, int(nr * frac))
            if sample_n < len(chunk):
                chunk = chunk.sample(n=sample_n, random_state=42)
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    del chunks
    gc.collect()
    return df


def _list_cluster_files(parts_dir, cluster_id):
    """Return sorted list of part files for a cluster."""
    import glob as glob_mod
    return sorted(glob_mod.glob(os.path.join(parts_dir, f"part_*_C{cluster_id}.parquet")))


def analyze_correlations(sym_result, output_dir):
    """Analyze train→forward correlations per cluster, loading from parquet parts."""
    symbol = sym_result['symbol']
    sc = sym_clean(symbol)
    n_clusters = sym_result['n_clusters']
    cluster_names = sym_result['cluster_names']
    split_info = sym_result['split_info']
    parts_dir = sym_result['parts_dir']

    lines = []
    lines.append(f"{'='*100}")
    lines.append(f"REGIME WALK-FORWARD — {symbol}")
    lines.append(f"{'='*100}")
    lines.append(f"Bars: {sym_result['n_bars']} | Clusters: {n_clusters}")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Episode summary
    lines.append(f"\n{'='*80}")
    lines.append(f"EPISODES & SPLIT")
    lines.append(f"{'='*80}")
    for k in range(n_clusters):
        si = split_info[k]
        name = cluster_names[k]
        lines.append(f"\n  C{k} ({name}): {si['total_episodes']} episodes")
        if si['valid']:
            lines.append(f"    Train: {si['train_episodes']} eps, {si['train_bars']} bars")
            lines.append(f"    Forward: {si['fwd_episodes']} eps, {si['fwd_bars']} bars")
        else:
            lines.append(f"    ⚠️ {si.get('reason', 'invalid')}")

    # Per-cluster correlations
    cluster_corr_results = {}  # k -> {r_pf, r_pnl, n} for summary reuse
    lines.append(f"\n{'='*80}")
    lines.append(f"CORRELATIONS: TRAIN → FORWARD (by cluster)")
    lines.append(f"{'='*80}")

    corr_header = (f"  {'Metric':<25s} {'r(train,fwd)':>12s} {'N':>8s}"
                   f"  {'r(global)':>12s}")
    lines.append(f"\n{corr_header}")
    lines.append(f"  {'-'*60}")

    # Per-cluster analysis — load only needed columns for each cluster
    for k in range(n_clusters):
        si = split_info[k]
        if not si['valid']:
            lines.append(f"\n  C{k} ({cluster_names[k]}): skipped ({si.get('reason', '')})")
            continue

        # Load only columns needed for this cluster's analysis
        cl_df = _load_cluster_data(parts_dir, k, [
            'pf_tr', 'pf_fwd', 'pnl_tr', 'pnl_fwd', 'pnl_ann_tr', 'pnl_ann_fwd',
            'trades_tr', 'trades_fwd', 'score_tr', 'score_fwd', 'pf_global',
        ])
        if len(cl_df) == 0:
            continue

        n_variants = len(cl_df) // (cl_df['pf_tr'].notna().sum() // max(1, len(cl_df)))
        lines.append(f"\n  C{k} ({cluster_names[k]})"
                     f" — {len(cl_df):,} config-rows from part files")

        # Extract arrays
        pf_tr_all = cl_df['pf_tr'].values
        pf_fwd_all = cl_df['pf_fwd'].values
        pnl_tr_all = cl_df['pnl_tr'].values
        pnl_fwd_all = cl_df['pnl_fwd'].values
        trades_tr_all = cl_df['trades_tr'].values
        trades_fwd_all = cl_df['trades_fwd'].values
        score_tr_all = cl_df['score_tr'].values
        pf_global_all = cl_df['pf_global'].values

        # Filter to configs with enough trades
        valid = (trades_tr_all >= MIN_TRADES_CLUSTER) & (trades_fwd_all >= 5)
        n_valid = int(np.sum(valid))

        if n_valid < 20:
            lines.append(f"    ⚠️ Insufficient configs with enough trades ({n_valid})")
            del cl_df
            gc.collect()
            continue

        # Cluster correlations
        corrs = {
            'pf_tr → pf_fwd': (pf_tr_all[valid], pf_fwd_all[valid]),
            'pf_tr → pnl_fwd': (pf_tr_all[valid], pnl_fwd_all[valid]),
            'score_tr → pnl_fwd': (score_tr_all[valid], pnl_fwd_all[valid]),
            'pnl_tr → pnl_fwd': (pnl_tr_all[valid], pnl_fwd_all[valid]),
            'trades_tr → pnl_fwd': (trades_tr_all[valid], pnl_fwd_all[valid]),
        }

        # Global correlations (for comparison)
        global_valid = (trades_tr_all >= MIN_TRADES_CLUSTER)
        global_corrs = {
            'pf_tr → pf_fwd': safe_corr(pf_global_all[global_valid], pf_fwd_all[global_valid]),
        }

        for name, (x, y) in corrs.items():
            r = safe_corr(x, y)
            r_global = global_corrs.get(name, np.nan)
            r_str = f"{r:+.3f}" if np.isfinite(r) else "N/A"
            rg_str = f"{r_global:+.3f}" if np.isfinite(r_global) else "N/A"
            lines.append(f"    {name:<25s} {r_str:>12s} {n_valid:>8d}  {rg_str:>12s}")

        # Top 10 by PF in train and their forward performance
        lines.append(f"\n    Top 10 by pf_tr (cluster C{k}):")
        lines.append(f"    {'Rank':>4s}  {'pf_tr':>7s}  {'pf_fwd':>7s}  {'pnl_tr':>8s}  {'pnl_fwd':>8s}  {'tr_tr':>5s}  {'tr_fwd':>5s}")
        valid_idx = np.where(valid)[0]
        pf_sort = valid_idx[np.argsort(-pf_tr_all[valid_idx])]
        for rank, idx in enumerate(pf_sort[:10], 1):
            lines.append(f"    {rank:>4d}  {pf_tr_all[idx]:>7.2f}  {pf_fwd_all[idx]:>7.2f}"
                         f"  {pnl_tr_all[idx]:>+8.1f}  {pnl_fwd_all[idx]:>+8.1f}"
                         f"  {trades_tr_all[idx]:>5.0f}  {trades_fwd_all[idx]:>5.0f}")

        # Distribution of forward PF
        pf_fwd_valid = pf_fwd_all[valid]
        pf_fwd_valid = pf_fwd_valid[np.isfinite(pf_fwd_valid)]
        if len(pf_fwd_valid) > 0:
            lines.append(f"\n    PF forward distribution (C{k}):"
                         f" min={pf_fwd_valid.min():.2f}"
                         f" p25={np.percentile(pf_fwd_valid, 25):.2f}"
                         f" median={np.median(pf_fwd_valid):.2f}"
                         f" p75={np.percentile(pf_fwd_valid, 75):.2f}"
                         f" max={pf_fwd_valid.max():.2f}")

        # Save per-cluster correlation results for summary reuse
        cluster_corr_results[k] = {
            'r_pf': safe_corr(pf_tr_all[valid], pf_fwd_all[valid]),
            'r_pnl': safe_corr(pnl_tr_all[valid], pnl_fwd_all[valid]),
            'n': n_valid,
        }

        # Free cluster data before next iteration
        del cl_df
        gc.collect()

    # Summary comparison — incremental online Pearson (never loads all data)
    lines.append(f"\n{'='*80}")
    lines.append(f"SUMMARY: CLUSTER vs GLOBAL PREDICTABILITY")
    lines.append(f"{'='*80}")

    # Global correlations via online Pearson: one part file at a time
    import glob as glob_mod
    all_part_files = sorted(glob_mod.glob(os.path.join(parts_dir, "part_*.parquet")))
    # Sample every 10th file if >20 files (still >100M rows, enough for stable r)
    if len(all_part_files) > 20:
        all_part_files = all_part_files[::10]

    pf_state = _init_pearson()
    pnl_state = _init_pearson()
    n_global = 0

    for pf_path in all_part_files:
        chunk = pd.read_parquet(pf_path, columns=[
            'pf_tr', 'pf_fwd', 'pnl_tr', 'pnl_fwd', 'trades_tr', 'trades_fwd',
        ])
        tr = chunk['trades_tr'].values
        tf = chunk['trades_fwd'].values
        v = (tr >= MIN_TRADES_CLUSTER) & (tf >= 5)
        n_global += int(v.sum())
        _update_pearson(pf_state, chunk['pf_tr'].values[v], chunk['pf_fwd'].values[v])
        _update_pearson(pnl_state, chunk['pnl_tr'].values[v], chunk['pnl_fwd'].values[v])
        del chunk
        gc.collect()

    r_pf_global = _finalize_pearson(pf_state)
    r_pnl_global = _finalize_pearson(pnl_state)

    lines.append(f"\n  Global (all clusters mixed, {'sampled ' if len(all_part_files) < 58 else ''}{len(all_part_files)} part files):")
    lines.append(f"    r(pf_tr, pf_fwd)  = {r_pf_global:+.3f}  (N={n_global})" if np.isfinite(r_pf_global) else "    r(pf_tr, pf_fwd)  = N/A")
    lines.append(f"    r(pnl_tr, pnl_fwd) = {r_pnl_global:+.3f}" if np.isfinite(r_pnl_global) else "    r(pnl_tr, pnl_fwd) = N/A")

    # Per-cluster results reused from first pass (no reload needed)
    for k in range(n_clusters):
        if not split_info[k]['valid'] or k not in cluster_corr_results:
            continue
        cr = cluster_corr_results[k]
        r_pf = cr['r_pf']
        r_pnl = cr['r_pnl']
        n_v = cr['n']
        name = cluster_names[k]
        lines.append(f"\n  C{k} ({name}):")
        lines.append(f"    r(pf_tr, pf_fwd)  = {r_pf:+.3f}  (N={n_v})" if np.isfinite(r_pf) else f"    r(pf_tr, pf_fwd)  = N/A")
        lines.append(f"    r(pnl_tr, pnl_fwd) = {r_pnl:+.3f}" if np.isfinite(r_pnl) else f"    r(pnl_tr, pnl_fwd) = N/A")

        # Delta vs global
        if np.isfinite(r_pf) and np.isfinite(r_pf_global):
            delta = r_pf - r_pf_global
            indicator = "↑ BETTER" if delta > 0.02 else ("↓ WORSE" if delta < -0.02 else "≈ SAME")
            lines.append(f"    Δ vs global: {delta:+.3f} {indicator}")

    lines.append(f"\n{'='*100}")

    # Write standalone report
    report_path = os.path.join(output_dir, f"regime_wf_{sc}_analysis.txt")
    report_text = '\n'.join(lines)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n{report_text}")
    print(f"\n   📄 Correlation report: {report_path}")
    return report_text


# ============================================
# STEP 7: EXTRACT VALIDATED SPECIALISTS
# ============================================

# Thresholds for specialist extraction
_TRAIN_MIN_TRADES = 30
_TRAIN_MIN_PF = 1.2
_FWD_MIN_TRADES = 15
_FWD_MIN_PF = 1.0
_TOP_KEEP_RAM = 50000       # max validated configs to keep in RAM per cluster
_TOP_JSON = 100             # top configs per cluster in JSON output for bot


def _approx_sqn_vec(pnl, gp, gl, wins, trades):
    """Vectorized SQN approximation from aggregated metrics.

    SQN = mean(trade_returns) / std(trade_returns) * sqrt(n_trades)
    Variance approximated via two-point distribution (avg_win, avg_loss).
    """
    n = len(pnl)
    sqn = np.zeros(n, dtype=np.float64)

    valid = trades >= 2
    losses = trades - wins

    mean_trade = np.where(valid, pnl / np.maximum(trades, 1), 0.0)
    avg_win = np.where(wins > 0, gp / np.maximum(wins, 1), 0.0)
    avg_loss = np.where(losses > 0, gl / np.maximum(losses, 1), 0.0)  # gl is already positive (abs)

    p = np.where(valid, wins / np.maximum(trades, 1), 0.0)

    # Two-point variance: p*(avg_win - mean)^2 + (1-p)*(avg_loss - mean)^2
    # Note: avg_loss from gl (gross loss) is positive; actual loss return is -avg_loss
    variance = (p * (avg_win - mean_trade)**2
                + (1 - p) * (-avg_loss - mean_trade)**2)
    std_trade = np.where(variance > 0, np.sqrt(variance), 1e-10)

    sqn = np.where(valid, (mean_trade / std_trade) * np.sqrt(trades.astype(np.float64)), 0.0)
    return sqn.astype(np.float32)


# ============================================
# PARAMETRIC NEIGHBORHOOD (for SQN haircut)
# ============================================
# Estructura de bits del config_id (26 bits)
# Ref: lab_historico_numba_v8_3.py decode_config() / generate_valid_configs()
_PARAM_FIELDS = [
    #  (nombre,           shift, bits, is_bitmask)
    ('exit_mask',           0,    4,   True),
    ('entry_mask',          4,    5,   True),
    ('div_entry_mode',      9,    2,   False),
    ('div_exit',           11,    1,   False),
    ('div_type',           12,    2,   False),
    ('div_ind_mask',       14,    8,   True),
    ('cancel_tf',          22,    1,   False),
    ('use_ts',             23,    1,   False),
    ('reg_inv',            24,    1,   False),
    ('hid_inv',            25,    1,   False),
]


def _decode_config_id(config_id):
    """Descompone config_id en sus parámetros individuales."""
    params = {}
    for name, shift, n_bits, _ in _PARAM_FIELDS:
        params[name] = (config_id >> shift) & ((1 << n_bits) - 1)
    return params


def _encode_config_id(params):
    """Reconstruye config_id a partir de parámetros individuales."""
    cid = 0
    for name, shift, n_bits, _ in _PARAM_FIELDS:
        cid |= (params[name] & ((1 << n_bits) - 1)) << shift
    return cid


def _get_neighbors(config_id):
    """Genera vecinos paramétricos: configs que difieren en 1 parámetro por ±1 paso.

    Para campos bitmask (entry/exit/indicators): flip de cada bit individual.
    Para campos discretos/booleanos: ±1 dentro del rango válido.
    """
    params = _decode_config_id(config_id)
    neighbors = set()

    for name, shift, n_bits, is_bitmask in _PARAM_FIELDS:
        value = params[name]

        if is_bitmask:
            for bit in range(n_bits):
                new_params = params.copy()
                new_params[name] = value ^ (1 << bit)
                neighbors.add(_encode_config_id(new_params))
        else:
            max_val = (1 << n_bits) - 1
            if value > 0:
                new_params = params.copy()
                new_params[name] = value - 1
                neighbors.add(_encode_config_id(new_params))
            if value < max_val:
                new_params = params.copy()
                new_params[name] = value + 1
                neighbors.add(_encode_config_id(new_params))

    neighbors.discard(config_id)
    return neighbors


def _build_preset_file_map(parts_dir, cluster_id):
    """Build mapping from preset_label to part file paths for a cluster."""
    import glob as glob_mod
    files = sorted(glob_mod.glob(os.path.join(parts_dir, f"part_*_C{cluster_id}.parquet")))
    preset_map = defaultdict(list)
    for fpath in files:
        try:
            pf = pq.ParquetFile(fpath)
            batch = next(pf.iter_batches(batch_size=1, columns=['preset_label']))
            label = batch['preset_label'][0].as_py()
            preset_map[label].append(fpath)
        except Exception:
            continue
    return dict(preset_map)


def _compute_sqn_haircut(top_all, parts_dir, cluster_id):
    """Deflate SQN by parametric neighborhood.

    For each config in top_all, find ~25 neighbors in the SAME preset's
    part files (neighbors change filter bits, not MA params), compute their
    combined SQN, and set:
      sqn_p5 = percentile 5 of (neighbor SQNs + central SQN)
      If <5 neighbors found: sqn_p5 = sqn_combined * 0.5

    Then recompute specialist_score using sqn_p5 instead of sqn_combined.
    """
    if len(top_all) == 0:
        top_all['sqn_p5'] = np.float32(0)
        top_all['sqn_n_neighbors'] = np.int32(0)
        return top_all

    print(f"      SQN haircut: {len(top_all)} configs...")
    t0 = time.time()

    # Build preset → part file mapping (reads 1 row per file, fast)
    preset_file_map = _build_preset_file_map(parts_dir, cluster_id)

    sqn_cols = ['config_id', 'pnl_tr', 'pnl_fwd', 'gp_tr', 'gp_fwd',
                'gl_tr', 'gl_fwd', 'wins_tr', 'wins_fwd', 'trades_tr', 'trades_fwd']

    top_all = top_all.reset_index(drop=True)
    sqn_p5_arr = np.full(len(top_all), np.nan, dtype=np.float32)
    n_neighbors_arr = np.zeros(len(top_all), dtype=np.int32)

    for preset_label in top_all['preset_label'].unique():
        group_mask = top_all['preset_label'] == preset_label
        group_indices = np.where(group_mask)[0]
        config_ids = top_all.loc[group_mask, 'config_id'].astype(int).values
        sqn_combined_vals = top_all.loc[group_mask, 'sqn_combined'].values

        pfiles = preset_file_map.get(preset_label, [])

        # Generate all neighbors for configs in this preset
        neighbors_per_config = {}
        all_neighbor_ids = set()
        for cid in config_ids:
            nb = _get_neighbors(int(cid))
            neighbors_per_config[int(cid)] = nb
            all_neighbor_ids.update(nb)

        if not pfiles or not all_neighbor_ids:
            for i, idx in enumerate(group_indices):
                sqn_p5_arr[idx] = float(sqn_combined_vals[i]) * 0.5
            continue

        # Load part files (1-2 per preset) and get neighbor metrics
        neighbor_ids_arr = np.array(list(all_neighbor_ids), dtype=np.int64)
        neighbor_sqn = {}
        for pf_path in pfiles:
            chunk = pd.read_parquet(pf_path, columns=sqn_cols)
            chunk_cids = chunk['config_id'].values.astype(np.int64)
            mask = np.isin(chunk_cids, neighbor_ids_arr)
            n_match = mask.sum()
            if n_match == 0:
                del chunk
                continue

            matched = chunk.loc[mask]
            pnl_c = (matched['pnl_tr'].values + matched['pnl_fwd'].values).astype(np.float64)
            gp_c = (matched['gp_tr'].values + matched['gp_fwd'].values).astype(np.float64)
            gl_c = (matched['gl_tr'].values + matched['gl_fwd'].values).astype(np.float64)
            wins_c = (matched['wins_tr'].values + matched['wins_fwd'].values).astype(np.float64)
            trades_c = (matched['trades_tr'].values + matched['trades_fwd'].values).astype(np.float64)

            sqn_vals = _approx_sqn_vec(pnl_c, gp_c, gl_c, wins_c, trades_c)
            matched_ids = matched['config_id'].values.astype(int)
            for j in range(len(matched_ids)):
                neighbor_sqn[int(matched_ids[j])] = float(sqn_vals[j])

            del chunk, matched
        gc.collect()

        # Compute sqn_p5 for each config in this preset group
        for i, idx in enumerate(group_indices):
            cid = int(config_ids[i])
            nb_ids = neighbors_per_config[cid]
            nb_sqns = [neighbor_sqn[nid] for nid in nb_ids if nid in neighbor_sqn]
            n_found = len(nb_sqns)
            n_neighbors_arr[idx] = n_found

            if n_found >= 5:
                all_sqns = nb_sqns + [float(sqn_combined_vals[i])]
                sqn_p5_arr[idx] = float(np.percentile(all_sqns, 5))
            else:
                sqn_p5_arr[idx] = float(sqn_combined_vals[i]) * 0.5

    top_all['sqn_p5'] = sqn_p5_arr
    top_all['sqn_n_neighbors'] = n_neighbors_arr

    # Recompute specialist_score with sqn_p5
    sqn_factor = np.maximum(top_all['sqn_p5'].values / 3.0, 0.5)
    top_all['specialist_score'] = (
        top_all['pf_combined'].values
        * np.sqrt(np.maximum(top_all['pf_robustness'].values, 0.0))
        * np.log(1.0 + top_all['trades_total'].values / 50.0)
        * sqn_factor
    ).astype(np.float32)

    # Re-sort by deflated score
    top_all = top_all.sort_values('specialist_score', ascending=False).reset_index(drop=True)

    elapsed = time.time() - t0
    n_with_data = int(np.sum(n_neighbors_arr >= 5))
    print(f"      SQN haircut done: {n_with_data}/{len(top_all)} with >=5 neighbors"
          f" ({elapsed:.1f}s)")

    return top_all


def compute_transition_matrix(cluster_labels, n_clusters):
    """Compute P(cluster_next | cluster_current) from label sequence.

    Returns (prob_matrix, count_matrix).
    """
    transitions = np.zeros((n_clusters, n_clusters), dtype=np.int64)
    for t in range(len(cluster_labels) - 1):
        c_now = cluster_labels[t]
        c_next = cluster_labels[t + 1]
        if c_now >= 0 and c_next >= 0:
            transitions[c_now, c_next] += 1
    row_sums = transitions.sum(axis=1, keepdims=True)
    prob_matrix = transitions / np.maximum(row_sums, 1)
    return prob_matrix, transitions


def compute_episode_transition_matrix(cluster_labels, n_clusters):
    """Compute transition matrix between consecutive episodes (ignoring gaps with label=-1)."""
    transitions = np.zeros((n_clusters, n_clusters), dtype=np.int64)
    last_cluster = -1
    for t in range(len(cluster_labels)):
        c = cluster_labels[t]
        if c >= 0:
            if last_cluster >= 0 and c != last_cluster:
                transitions[last_cluster, c] += 1
            last_cluster = c
    row_sums = transitions.sum(axis=1, keepdims=True)
    prob_matrix = transitions / np.maximum(row_sums, 1)
    return prob_matrix, transitions


def _check_part_columns(parts_dir, cluster_id):
    """Check if part files have the columns needed for specialist extraction.
    Returns (ok: bool, missing: set, available: list).
    """
    files = _list_cluster_files(parts_dir, cluster_id)
    if not files:
        return False, set(), []
    cols = pq.ParquetFile(files[0]).schema.names
    required = {'config_id', 'preset_label', 'gp_tr', 'gl_tr', 'gp_fwd', 'gl_fwd',
                'wins_tr', 'wins_fwd', 'maxdd_tr', 'maxdd_fwd'}
    missing = required - set(cols)
    return len(missing) == 0, missing, cols


def _compute_specialist_metrics(df):
    """Vectorized computation of ranking metrics on a DataFrame of validated configs.
    Adds columns in-place: pf_combined, trades_total, maxdd_worst, wr_combined,
    pf_robustness, sqn_tr, sqn_fwd, sqn_combined, specialist_score.
    """
    gp_total = df['gp_tr'].values + df['gp_fwd'].values
    gl_total = df['gl_tr'].values + df['gl_fwd'].values
    pf_combined = np.where(gl_total > 0, gp_total / gl_total,
                           np.where(gp_total > 0, 5.0, 0.0))

    trades_total = df['trades_tr'].values + df['trades_fwd'].values
    maxdd_worst = np.maximum(df['maxdd_tr'].values, df['maxdd_fwd'].values)

    wins_total = df['wins_tr'].values + df['wins_fwd'].values
    wr_combined = np.where(trades_total > 0, wins_total / trades_total, 0.0)

    pf_tr_safe = np.where(df['pf_tr'].values > 0, df['pf_tr'].values, 1e-6)
    pf_robustness = np.minimum(df['pf_fwd'].values / pf_tr_safe, 1.5)

    # SQN approximation
    pnl_tr = df['pnl_tr'].values.astype(np.float64)
    pnl_fwd = df['pnl_fwd'].values.astype(np.float64)
    gp_tr = df['gp_tr'].values.astype(np.float64)
    gp_fwd = df['gp_fwd'].values.astype(np.float64)
    gl_tr = df['gl_tr'].values.astype(np.float64)
    gl_fwd = df['gl_fwd'].values.astype(np.float64)
    wins_tr = df['wins_tr'].values.astype(np.float64)
    wins_fwd = df['wins_fwd'].values.astype(np.float64)
    trades_tr = df['trades_tr'].values.astype(np.float64)
    trades_fwd = df['trades_fwd'].values.astype(np.float64)

    sqn_tr = _approx_sqn_vec(pnl_tr, gp_tr, gl_tr, wins_tr, trades_tr)
    sqn_fwd = _approx_sqn_vec(pnl_fwd, gp_fwd, gl_fwd, wins_fwd, trades_fwd)
    sqn_combined = _approx_sqn_vec(
        pnl_tr + pnl_fwd, gp_total.astype(np.float64), gl_total.astype(np.float64),
        wins_total.astype(np.float64), trades_total.astype(np.float64))

    # Score: PF * sqrt(robustness) * log(trade_count) * SQN_factor
    sqn_factor = np.maximum(sqn_combined / 3.0, 0.5)
    specialist_score = (pf_combined
                        * np.sqrt(np.maximum(pf_robustness, 0.0))
                        * np.log(1.0 + trades_total / 50.0)
                        * sqn_factor)

    df['pf_combined'] = pf_combined.astype(np.float32)
    df['trades_total'] = trades_total.astype(np.float32)
    df['maxdd_worst'] = maxdd_worst.astype(np.float32)
    df['wr_combined'] = wr_combined.astype(np.float32)
    df['pf_robustness'] = pf_robustness.astype(np.float32)
    df['sqn_tr'] = sqn_tr
    df['sqn_fwd'] = sqn_fwd
    df['sqn_combined'] = sqn_combined
    df['specialist_score'] = specialist_score.astype(np.float32)
    return df


def extract_validated_specialists(sym_result, output_dir):
    """Extract validated specialist configs per cluster from part files.

    Phases:
      1. Train filter (vectorized, per part file)
      2. Forward filter (same pass — both metrics live in same row)
      3. Ranking by specialist_score
      4. Plateau analysis (optional, on top N)
      5. Output: CSV + TXT report + JSON for bot

    Appends correlation analysis as secondary informative section.
    """
    symbol = sym_result['symbol']
    sc = sym_clean(symbol)
    n_clusters = sym_result['n_clusters']
    cluster_names = sym_result['cluster_names']
    split_info = sym_result['split_info']
    parts_dir = sym_result['parts_dir']

    # --- Pre-flight: check columns ---
    first_valid = next((k for k in range(n_clusters) if split_info[k]['valid']), None)
    if first_valid is None:
        print(f"   ⚠️  No valid clusters for specialist extraction")
        return None

    cols_ok, missing, available = _check_part_columns(parts_dir, first_valid)
    if not cols_ok:
        print(f"   ❌ Part files missing columns for specialist extraction: {missing}")
        print(f"      Available: {available}")
        print(f"      Re-run simulation (delete _parts_{sc}/) to include new columns.")
        # Fall back to correlation-only analysis
        corr_text = analyze_correlations(sym_result, output_dir)
        return corr_text
    print(f"   ✅ Part files have all required columns for specialist extraction")

    # --- Report header ---
    rpt = []
    rpt.append(f"{'='*100}")
    rpt.append(f"REGIME WALK-FORWARD — SPECIALIST EXTRACTION — {symbol}")
    rpt.append(f"{'='*100}")
    rpt.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    rpt.append(f"Bars: {sym_result['n_bars']} | Clusters: {n_clusters}")
    rpt.append(f"Train filters : trades >= {_TRAIN_MIN_TRADES}, pnl > 0, PF >= {_TRAIN_MIN_PF}")
    rpt.append(f"Forward filters: trades >= {_FWD_MIN_TRADES}, pnl > 0, PF >= {_FWD_MIN_PF}")
    toxic_tail_mode = sym_result.get('toxic_tail_mode', 'fixed')
    toxic_tail_val = sym_result.get('toxic_tail', 0)
    if toxic_tail_mode == 'dynamic':
        confirm_thresh = sym_result.get('confirm_threshold', 0.75)
        rpt.append(f"Toxic tail: DYNAMIC (threshold={confirm_thresh:.0%})")
    elif toxic_tail_val > 0:
        rpt.append(f"Toxic tail: {toxic_tail_val} bars (forward episodes extended into next regime)")

    # Episode summary
    rpt.append(f"\n{'='*80}")
    rpt.append(f"EPISODES & SPLIT")
    rpt.append(f"{'='*80}")
    for k in range(n_clusters):
        si = split_info[k]
        name = cluster_names[k]
        rpt.append(f"\n  C{k} ({name}): {si['total_episodes']} episodes")
        if si['valid']:
            rpt.append(f"    Train: {si['train_episodes']} eps, {si['train_bars']} bars")
            toxic_b = si.get('toxic_tail_bars', 0)
            toxic_info = f" [+{toxic_b} toxic tail]" if toxic_b > 0 else ""
            rpt.append(f"    Forward: {si['fwd_episodes']} eps, {si['fwd_bars']} bars{toxic_info}")
        else:
            rpt.append(f"    ⚠️ {si.get('reason', 'invalid')}")

    # Dynamic toxic tail distribution
    if toxic_tail_mode == 'dynamic':
        rpt.append(f"\n{'='*80}")
        rpt.append(f"TOXIC TAIL (dynamic, threshold={sym_result.get('confirm_threshold', 0.75):.0%})")
        rpt.append(f"{'='*80}")
        for k in range(n_clusters):
            si = split_info[k]
            name = cluster_names[k]
            if si['valid'] and 'toxic_tail_mean' in si:
                rpt.append(f"  C{k} ({name}): mean={si['toxic_tail_mean']:.0f} "
                           f"median={si['toxic_tail_median']:.0f} "
                           f"min={si['toxic_tail_min']} max={si['toxic_tail_max']} "
                           f"({si['fwd_episodes']} episodes)")
            elif si['valid']:
                rpt.append(f"  C{k} ({name}): no toxic tail data")

    # --- Transition matrix (Markov) ---
    cluster_labels = sym_result.get('cluster_labels')
    trans_prob = None
    trans_prob_ep = None
    if cluster_labels is not None:
        trans_prob, trans_counts = compute_transition_matrix(cluster_labels, n_clusters)
        trans_prob_ep, trans_counts_ep = compute_episode_transition_matrix(cluster_labels, n_clusters)

        rpt.append(f"\n{'='*80}")
        rpt.append(f"TRANSITION MATRIX (Markov — bar-level)")
        rpt.append(f"{'='*80}")
        hdr_cols = ''.join(f'  {"-> C"+str(j):>8s}' for j in range(n_clusters))
        rpt.append(f"  {'':>6s}{hdr_cols}")
        for i in range(n_clusters):
            row_str = ''.join(f'  {trans_prob[i,j]*100:>7.1f}%' for j in range(n_clusters))
            rpt.append(f"  {'C'+str(i):>6s}{row_str}")

        rpt.append(f"\n  TRANSITION MATRIX (Markov — episode-level)")
        rpt.append(f"  {'':>6s}{hdr_cols}")
        for i in range(n_clusters):
            row_str = ''.join(f'  {trans_prob_ep[i,j]*100:>7.1f}%' for j in range(n_clusters))
            rpt.append(f"  {'C'+str(i):>6s}{row_str}")

    # Columns to load per part file
    load_cols = [
        'config_id', 'preset_label',
        'pf_tr', 'pnl_tr', 'trades_tr', 'wins_tr', 'maxdd_tr', 'gp_tr', 'gl_tr',
        'pf_fwd', 'pnl_fwd', 'trades_fwd', 'wins_fwd', 'maxdd_fwd', 'gp_fwd', 'gl_fwd',
    ]

    json_output = {
        "symbol": symbol,
        "generated": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "n_clusters": n_clusters,
        "clusters": {},
    }
    if trans_prob is not None:
        json_output["transition_matrix_bar"] = [[round(float(v), 4) for v in row]
                                                 for row in trans_prob]
    if trans_prob_ep is not None:
        json_output["transition_matrix"] = [[round(float(v), 4) for v in row]
                                             for row in trans_prob_ep]

    # Track config_ids per cluster for cross-cluster generalista check
    validated_ids_per_cluster = {}
    # Store top_all DataFrames per cluster for cross-cluster survival
    top_all_per_cluster = {}
    n_validated_per_cluster = {}
    n_pass_train_per_cluster = {}

    # ========================================================
    # PROCESS EACH CLUSTER
    # ========================================================
    for k in range(n_clusters):
        si = split_info[k]
        if not si['valid']:
            rpt.append(f"\n{'='*80}")
            rpt.append(f"CLUSTER C{k} ({cluster_names[k]}): SKIPPED — {si.get('reason','')}")
            continue

        part_files = _list_cluster_files(parts_dir, k)
        if not part_files:
            rpt.append(f"\n{'='*80}")
            rpt.append(f"CLUSTER C{k} ({cluster_names[k]}): NO PART FILES")
            continue

        # Phase 1+2 combined: both train and forward metrics are in same row
        csv_path = os.path.join(output_dir, f"{sc}_cluster_{k}_specialists.csv")
        n_total = 0
        n_pass_train = 0
        n_validated = 0
        top_buffer = []  # small DataFrames of top candidates per part file

        for pf_path in part_files:
            chunk = pd.read_parquet(pf_path, columns=load_cols)
            n_total += len(chunk)

            # Phase 1: Train filter (vectorized)
            train_mask = (
                (chunk['trades_tr'] >= _TRAIN_MIN_TRADES) &
                (chunk['pnl_tr'] > 0) &
                (chunk['pf_tr'] >= _TRAIN_MIN_PF)
            )
            n_pass_train += int(train_mask.sum())

            # Phase 2: Forward filter on train-passed subset (vectorized)
            candidates = chunk.loc[train_mask]
            if len(candidates) == 0:
                del chunk
                gc.collect()
                continue

            fwd_mask = (
                (candidates['trades_fwd'] >= _FWD_MIN_TRADES) &
                (candidates['pnl_fwd'] > 0) &
                (candidates['pf_fwd'] >= _FWD_MIN_PF)
            )
            validated = candidates.loc[fwd_mask].copy()
            n_validated += len(validated)

            if len(validated) == 0:
                del chunk, candidates
                gc.collect()
                continue

            # Phase 3: Compute ranking metrics (vectorized)
            _compute_specialist_metrics(validated)

            # Keep top slice in RAM for JSON/report
            keep_n = min(1000, len(validated))
            top_buffer.append(
                validated.nlargest(keep_n, 'specialist_score').copy())

            del chunk, candidates, validated
            gc.collect()

        # --- Consolidate top buffer ---
        if top_buffer:
            top_all = pd.concat(top_buffer, ignore_index=True)
            top_all = top_all.nlargest(
                min(_TOP_KEEP_RAM, len(top_all)), 'specialist_score')
        else:
            top_all = pd.DataFrame()
        del top_buffer
        gc.collect()

        # --- SQN Haircut: deflate SQN by parametric neighborhood ---
        if len(top_all) > 0:
            top_all = _compute_sqn_haircut(top_all, parts_dir, k)

        # Track validated config_ids for cross-cluster check
        if len(top_all) > 0:
            validated_ids_per_cluster[k] = set(top_all['config_id'].astype(int).tolist())
        else:
            validated_ids_per_cluster[k] = set()

        survival_pct = (n_validated / max(n_pass_train, 1) * 100)
        train_pct = (n_pass_train / max(n_total, 1) * 100)

        # --- Report section for this cluster ---
        rpt.append(f"\n{'='*80}")
        rpt.append(f"CLUSTER C{k} ({cluster_names[k]})")
        rpt.append(f"{'='*80}")
        rpt.append(f"  Total config-rows evaluated: {n_total:,}")
        rpt.append(f"  Pass train filter:           {n_pass_train:,} ({train_pct:.1f}%)")
        rpt.append(f"  Pass forward (validated):    {n_validated:,}"
                    f" ({survival_pct:.1f}% survival train→fwd)")

        if len(top_all) > 0:
            # Top 20 — RANKING METRICS
            rpt.append(f"\n  RANKING METRICS — Top 20 specialists (score uses sqn_p5):")
            hdr = (f"  {'#':>3s}  {'config_id':>10s}  {'preset':>35s}"
                   f"  {'pf_comb':>7s}  {'sqn_comb':>8s}  {'sqn_p5':>7s}  {'nb':>3s}  {'trades':>6s}"
                   f"  {'maxdd':>7s}  {'robust':>6s}  {'plateau':>7s}"
                   f"  {'score':>7s}")
            rpt.append(hdr)
            rpt.append(f"  {'-'*len(hdr)}")

            for rank, (_, row) in enumerate(top_all.head(20).iterrows(), 1):
                plat_str = f"{row['plateau_ratio']:>7.2f}" if ('plateau_ratio' in row.index and np.isfinite(row.get('plateau_ratio', np.nan))) else f"{'—':>7s}"
                sqn_p5_val = row.get('sqn_p5', np.nan)
                sqn_p5_str = f"{sqn_p5_val:>7.2f}" if np.isfinite(sqn_p5_val) else f"{'—':>7s}"
                nb_val = int(row.get('sqn_n_neighbors', 0))
                rpt.append(
                    f"  {rank:>3d}  {int(row['config_id']):>10d}"
                    f"  {str(row['preset_label']):>35s}"
                    f"  {row['pf_combined']:>7.2f}  {row['sqn_combined']:>8.2f}"
                    f"  {sqn_p5_str}  {nb_val:>3d}  {int(row['trades_total']):>6d}"
                    f"  {row['maxdd_worst']:>7.4f}  {row['pf_robustness']:>6.2f}"
                    f"  {plat_str}  {row['specialist_score']:>7.2f}")

            # PF forward distribution among all validated (from top_all)
            pf_fwd_v = top_all['pf_fwd'].values
            pf_fwd_v = pf_fwd_v[np.isfinite(pf_fwd_v)]
            if len(pf_fwd_v) > 0:
                rpt.append(f"\n  PF forward distribution (validated, top {len(pf_fwd_v):,}):")
                rpt.append(f"    min={pf_fwd_v.min():.2f}"
                           f"  p25={np.percentile(pf_fwd_v, 25):.2f}"
                           f"  median={np.median(pf_fwd_v):.2f}"
                           f"  p75={np.percentile(pf_fwd_v, 75):.2f}"
                           f"  max={pf_fwd_v.max():.2f}")

            # PF combined distribution
            pf_comb_v = top_all['pf_combined'].values
            pf_comb_v = pf_comb_v[np.isfinite(pf_comb_v)]
            if len(pf_comb_v) > 0:
                rpt.append(f"  PF combined distribution:")
                rpt.append(f"    min={pf_comb_v.min():.2f}"
                           f"  p25={np.percentile(pf_comb_v, 25):.2f}"
                           f"  median={np.median(pf_comb_v):.2f}"
                           f"  p75={np.percentile(pf_comb_v, 75):.2f}"
                           f"  max={pf_comb_v.max():.2f}")

            # Write top 1000 to CSV (overwrite, not append)
            _CSV_TOP_N = 1000
            top_all.head(_CSV_TOP_N).to_csv(csv_path, index=False)
            rpt.append(f"\n  CSV: {csv_path} (top {min(_CSV_TOP_N, len(top_all))})")

            # --- Phase 4: Plateau analysis (on top 100) ---
            # Evaluate how many of the top config's parametric neighbors also
            # passed validation.  Build a lookup of validated config_ids from
            # this cluster's top_all, then for each top config shift its
            # bitfields by ±1 to generate neighbor IDs.
            if len(top_all) >= 20:
                rpt.append(f"\n  Plateau analysis (top 100):")
                validated_set = set(top_all['config_id'].astype(int).tolist())
                plateau_ratios = []
                top_for_plateau = top_all.head(100)
                for _, row in top_for_plateau.iterrows():
                    cid = int(row['config_id'])
                    # Generate parametric neighbors by flipping individual bits
                    # and shifting sub-fields ±1.  Quick heuristic: flip each of
                    # the 26 bits → 26 neighbors.
                    neighbors = set()
                    for bit in range(26):
                        neighbor = cid ^ (1 << bit)
                        neighbors.add(neighbor)
                    n_in = sum(1 for nb in neighbors if nb in validated_set)
                    ratio = n_in / max(len(neighbors), 1)
                    plateau_ratios.append(ratio)

                plateau_arr = np.array(plateau_ratios)
                rpt.append(f"    Avg plateau ratio: {plateau_arr.mean():.2f}"
                           f"  (median {np.median(plateau_arr):.2f},"
                           f" max {plateau_arr.max():.2f})")
                rpt.append(f"    Configs with ratio > 0.3: "
                           f"{int(np.sum(plateau_arr > 0.3))}/100")
                # Add plateau_ratio to top_all for the first 100
                top_all_plateau = np.full(len(top_all), np.nan, dtype=np.float32)
                top_all_plateau[:len(plateau_ratios)] = plateau_ratios
                top_all['plateau_ratio'] = top_all_plateau

        # Store for cross-cluster analysis (don't delete yet)
        top_all_per_cluster[k] = top_all
        n_validated_per_cluster[k] = n_validated
        n_pass_train_per_cluster[k] = n_pass_train

    # ========================================================
    # CROSS-CLUSTER SURVIVAL FILTER
    # ========================================================
    # For each config validated in cluster K, check its PF in adjacent clusters
    # (transition probability > 10%). Configs with PF < 0.7 in adjacent cluster
    # are penalized or discarded.

    valid_ks = [k for k in top_all_per_cluster if len(top_all_per_cluster[k]) > 0]

    # Build cross-cluster PF lookup: for top configs in each cluster, load their
    # metrics from other clusters' part files
    cross_cluster_pf = {}  # {(config_id, cluster_j): pf_fwd}
    if len(valid_ks) >= 2 and trans_prob_ep is not None:
        # Collect all config_ids we need cross-cluster data for
        all_target_ids = set()
        for k in valid_ks:
            # Only top configs (limit to keep load manageable)
            top_cids = set(top_all_per_cluster[k].head(5000)['config_id'].astype(int).tolist())
            all_target_ids.update(top_cids)

        # For each cluster, load part files and extract PF for target config_ids
        for j in valid_ks:
            pf_files = _list_cluster_files(parts_dir, j)
            for pf_path in pf_files:
                chunk = pd.read_parquet(pf_path, columns=['config_id', 'pf_fwd', 'pnl_fwd', 'trades_fwd'])
                chunk_ids = chunk['config_id'].astype(int)
                mask = chunk_ids.isin(all_target_ids)
                if mask.sum() > 0:
                    matched = chunk.loc[mask]
                    for _, row in matched.iterrows():
                        cid = int(row['config_id'])
                        cross_cluster_pf[(cid, j)] = float(row['pf_fwd'])
                del chunk
            gc.collect()

    # Apply survival filter and build final outputs per cluster
    _CROSS_CLUSTER_MIN_PF = 0.7
    _CROSS_CLUSTER_MIN_TRANS_PROB = 0.10

    rpt.append(f"\n{'='*80}")
    rpt.append(f"CROSS-CLUSTER SURVIVAL")
    rpt.append(f"{'='*80}")
    rpt.append(f"  Filter: PF_fwd < {_CROSS_CLUSTER_MIN_PF} in adjacent cluster"
               f" (P_transition > {_CROSS_CLUSTER_MIN_TRANS_PROB*100:.0f}%)")

    for k in range(n_clusters):
        if k not in top_all_per_cluster or len(top_all_per_cluster[k]) == 0:
            continue
        top_all = top_all_per_cluster[k]

        if trans_prob_ep is not None and len(valid_ks) >= 2:
            # Find adjacent clusters (episode-level transition prob > threshold)
            adjacent = [j for j in range(n_clusters)
                        if j != k and trans_prob_ep[k, j] >= _CROSS_CLUSTER_MIN_TRANS_PROB]

            if adjacent:
                # Check survival for each config
                survival_mask = np.ones(len(top_all), dtype=bool)
                worst_adj_pf = np.full(len(top_all), np.nan, dtype=np.float32)

                for idx, (_, row) in enumerate(top_all.iterrows()):
                    cid = int(row['config_id'])
                    min_adj_pf = float('inf')
                    for j in adjacent:
                        pf_j = cross_cluster_pf.get((cid, j), np.nan)
                        if np.isfinite(pf_j):
                            min_adj_pf = min(min_adj_pf, pf_j)
                            if pf_j < _CROSS_CLUSTER_MIN_PF:
                                survival_mask[idx] = False
                    if min_adj_pf < float('inf'):
                        worst_adj_pf[idx] = min_adj_pf

                top_all['cross_cluster_survival'] = survival_mask
                top_all['adjacent_worst_pf'] = worst_adj_pf

                n_before = len(top_all)
                n_survive = int(survival_mask.sum())
                surv_pct = n_survive / max(n_before, 1) * 100
                rpt.append(f"\n  C{k} specialists: {n_before:,} validated"
                           f" -> {n_survive:,} survive cross-cluster filter"
                           f" ({surv_pct:.1f}%)")
                adj_str = ', '.join(f"C{j}(P={trans_prob_ep[k,j]*100:.1f}%)" for j in adjacent)
                rpt.append(f"    Adjacent clusters: {adj_str}")
            else:
                top_all['cross_cluster_survival'] = True
                top_all['adjacent_worst_pf'] = np.nan
                rpt.append(f"\n  C{k}: no adjacent cluster with P > "
                           f"{_CROSS_CLUSTER_MIN_TRANS_PROB*100:.0f}%")
        else:
            top_all['cross_cluster_survival'] = True
            top_all['adjacent_worst_pf'] = np.nan
            rpt.append(f"\n  C{k}: cross-cluster filter not applicable"
                       f" (need >=2 clusters + transition matrix)")

        top_all_per_cluster[k] = top_all

    # ========================================================
    # CROSS-CLUSTER PROFILE (top 5 per cluster)
    # ========================================================
    rpt.append(f"\n{'='*80}")
    rpt.append(f"CROSS-CLUSTER PROFILE")
    rpt.append(f"{'='*80}")

    for k in valid_ks:
        top_all = top_all_per_cluster[k]
        # Show top 5 surviving configs and their performance in all clusters
        survivors = top_all[top_all['cross_cluster_survival'] == True] if 'cross_cluster_survival' in top_all.columns else top_all
        top5 = survivors.head(5)

        rpt.append(f"\n  C{k} ({cluster_names[k]}) — top 5 surviving specialists:")
        for _, row in top5.iterrows():
            cid = int(row['config_id'])
            rpt.append(f"    Config {cid} ({str(row['preset_label'])}):")
            for j in range(n_clusters):
                pf_j = cross_cluster_pf.get((cid, j), np.nan)
                is_specialist = (j == k)
                marker = " <- specialist cluster" if is_specialist else ""
                if is_specialist:
                    pf_j = float(row['pf_combined'])
                    rpt.append(f"      C{j}: PF={pf_j:.2f}"
                               f" {int(row['trades_total'])}t{marker}")
                elif np.isfinite(pf_j):
                    adj_status = ""
                    if trans_prob_ep is not None and trans_prob_ep[k, j] >= _CROSS_CLUSTER_MIN_TRANS_PROB:
                        adj_status = " SURVIVES" if pf_j >= _CROSS_CLUSTER_MIN_PF else " FAILS"
                        adj_status = f" (P={trans_prob_ep[k,j]*100:.1f}%) —{adj_status}"
                    rpt.append(f"      C{j}: PF={pf_j:.2f}{adj_status}")
                else:
                    rpt.append(f"      C{j}: no data")

    # ========================================================
    # CROSS-CLUSTER GENERALISTA CHECK
    # ========================================================
    rpt.append(f"\n{'='*80}")
    rpt.append(f"CROSS-CLUSTER ANALYSIS: GENERALISTAS")
    rpt.append(f"{'='*80}")

    if len(valid_ks) >= 2:
        from collections import Counter
        all_ids = Counter()
        for k in valid_ks:
            for cid in validated_ids_per_cluster[k]:
                all_ids[cid] += 1
        multi_cluster = {cid: cnt for cid, cnt in all_ids.items() if cnt > 1}
        rpt.append(f"\n  Configs validated in >1 cluster: {len(multi_cluster):,}")
        if multi_cluster:
            rpt.append(f"  (These are potential generalistas — work across regimes)")
            for cnt_val in sorted(set(multi_cluster.values()), reverse=True):
                n_with = sum(1 for c in multi_cluster.values() if c == cnt_val)
                rpt.append(f"    In {cnt_val} clusters: {n_with:,} configs")
        else:
            rpt.append(f"  (No generalistas found — all specialists are regime-specific)")
    else:
        rpt.append(f"\n  Only {len(valid_ks)} cluster(s) with validated configs — "
                    f"cross-cluster check not meaningful")

    # ========================================================
    # BUILD JSON PER CLUSTER (after survival filter applied)
    # ========================================================
    for k in valid_ks:
        top_all = top_all_per_cluster[k]
        n_validated = n_validated_per_cluster.get(k, 0)
        n_pass_train = n_pass_train_per_cluster.get(k, 0)
        survival_pct = (n_validated / max(n_pass_train, 1) * 100)

        # Prefer survivors; fall back to non-survivors only if < 10 survive
        _MIN_SURVIVORS = 10
        has_surv_col = 'cross_cluster_survival' in top_all.columns
        if has_surv_col:
            survivors = top_all[top_all['cross_cluster_survival'] == True]
            if len(survivors) >= _MIN_SURVIVORS:
                top_json = survivors.head(_TOP_JSON)
            else:
                # Not enough survivors: take all survivors + fill with non-survivors
                non_surv = top_all[top_all['cross_cluster_survival'] == False]
                top_json = pd.concat([
                    survivors.head(_TOP_JSON),
                    non_surv.head(_TOP_JSON - len(survivors))
                ], ignore_index=True)
        else:
            top_json = top_all.head(_TOP_JSON)

        cluster_json_configs = []
        for _, row in top_json.iterrows():
            entry = {
                "config_id": int(row['config_id']),
                "preset": str(row['preset_label']),
                "pf_combined": round(float(row['pf_combined']), 3),
                "sqn_combined": round(float(row['sqn_combined']), 3),
                "sqn_p5": round(float(row.get('sqn_p5', row['sqn_combined'])), 3),
                "sqn_n_neighbors": int(row.get('sqn_n_neighbors', 0)),
                "trades_total": int(row['trades_total']),
                "maxdd_worst": round(float(row['maxdd_worst']), 4),
                "pf_robustness": round(float(row['pf_robustness']), 3),
                "specialist_score": round(float(row['specialist_score']), 3),
                "pf_tr": round(float(row['pf_tr']), 3),
                "pf_fwd": round(float(row['pf_fwd']), 3),
                "trades_tr": int(row['trades_tr']),
                "trades_fwd": int(row['trades_fwd']),
                "pnl_tr": round(float(row['pnl_tr']), 3),
                "pnl_fwd": round(float(row['pnl_fwd']), 3),
            }
            if 'plateau_ratio' in row.index and np.isfinite(row.get('plateau_ratio', np.nan)):
                entry["plateau_ratio"] = round(float(row['plateau_ratio']), 3)
            if has_surv_col:
                entry["cross_cluster_survival"] = bool(row['cross_cluster_survival'])
            if 'adjacent_worst_pf' in row.index and np.isfinite(row.get('adjacent_worst_pf', np.nan)):
                entry["adjacent_worst_pf"] = round(float(row['adjacent_worst_pf']), 3)
            cluster_json_configs.append(entry)

        json_output["clusters"][str(k)] = {
            "name": cluster_names[k],
            "n_validated": n_validated,
            "survival_rate_pct": round(survival_pct, 1),
            "top_configs": cluster_json_configs,
        }

    # Free top_all DataFrames
    del top_all_per_cluster, cross_cluster_pf
    gc.collect()

    # ========================================================
    # SECONDARY: CORRELATION ANALYSIS
    # ========================================================
    rpt.append(f"\n\n{'='*100}")
    rpt.append(f"SECONDARY: CORRELATION ANALYSIS")
    rpt.append(f"{'='*100}")
    try:
        corr_text = analyze_correlations(sym_result, output_dir)
        if corr_text:
            rpt.append(corr_text)
    except Exception as e:
        rpt.append(f"\n  ⚠️ Correlation analysis failed: {e}")

    rpt.append(f"\n{'='*100}")

    # ========================================================
    # WRITE OUTPUTS
    # ========================================================

    # JSON for bot consumption
    json_path = os.path.join(output_dir, f"{sc}_specialist_configs.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)

    # Full specialist report
    report_path = os.path.join(output_dir, f"{sc}_specialists_report.txt")
    report_text = '\n'.join(rpt)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n{report_text}")
    print(f"\n   📄 Specialist report: {report_path}")
    print(f"   📄 Bot JSON: {json_path}")

    return report_path


# ============================================
# MAIN
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(description='Regime Walk-Forward Validation')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols (default: all 48)')
    parser.add_argument('--train-ratio', type=float, default=TRAIN_RATIO,
                        help=f'Fraction of episodes for train (default: {TRAIN_RATIO})')
    parser.add_argument('--min-episode-bars', type=int, default=MIN_EPISODE_BARS,
                        help=f'Min bars per episode (default: {MIN_EPISODE_BARS})')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help=f'Output directory (default: {OUTPUT_DIR})')
    parser.add_argument('--presets-dir', type=str, default='output',
                        help='Directory to search for presets_SYMBOL.csv (default: output)')
    parser.add_argument('--toxic-tail', type=str, default=str(TOXIC_TAIL),
                        help=f'Bars to extend forward episodes (int or "dynamic") (default: {TOXIC_TAIL})')
    parser.add_argument('--max-toxic-tail', type=int, default=100,
                        help='Max bars for dynamic toxic tail (default: 100)')
    parser.add_argument('--min-toxic-tail', type=int, default=5,
                        help='Min bars for dynamic toxic tail (default: 5)')
    parser.add_argument('--confirm-threshold', type=float, default=0.75,
                        help='GMM probability threshold for regime confirmation (default: 0.75)')
    args = parser.parse_args()

    # Parse toxic-tail: "dynamic" or integer
    if args.toxic_tail.lower() == 'dynamic':
        args.toxic_tail_mode = 'dynamic'
        args.toxic_tail = 0  # not used in dynamic mode
    else:
        try:
            args.toxic_tail = int(args.toxic_tail)
            args.toxic_tail_mode = 'fixed'
        except ValueError:
            parser.error(f"--toxic-tail must be 'dynamic' or an integer, got '{args.toxic_tail}'")

    return args


def main():
    args = parse_args()

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = SYMBOLS

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 70)
    print("🔬 REGIME WALK-FORWARD — Validation by Regime Episodes")
    print(f"   Symbols: {len(symbols)}")
    print(f"   Train ratio: {args.train_ratio}")
    print(f"   Min episode bars: {args.min_episode_bars}")
    if args.toxic_tail_mode == 'dynamic':
        print(f"   Toxic tail: DYNAMIC (threshold={args.confirm_threshold}, min={args.min_toxic_tail}, max={args.max_toxic_tail})")
    else:
        print(f"   Toxic tail: {args.toxic_tail} bars")
    print(f"   Output: {args.output_dir}/")
    print("=" * 70)

    # Warm up sklearn
    from sklearn.mixture import GaussianMixture
    GaussianMixture(n_components=2, n_init=1, max_iter=1, random_state=42).fit(
        np.random.randn(20, 3))

    completed = 0
    failed = []

    for i, symbol in enumerate(symbols, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(symbols)}] {symbol}")
        print(f"{'='*70}")

        try:
            # Load data
            df = load_full_history(symbol)
            if df is None or len(df) < 5000:
                print(f"   ⚠️  Insufficient data")
                failed.append(symbol)
                continue

            # Load model
            model_data = load_regime_model(symbol)
            if model_data is None:
                failed.append(symbol)
                continue

            # Load presets
            presets = load_presets(symbol, args.presets_dir)
            if presets is None or len(presets) == 0:
                failed.append(symbol)
                continue

            # Process (saves partial results to parquet, frees RAM per variant)
            result = process_symbol(symbol, presets, df, model_data, args)

            # Free heavy objects before analysis
            del df, model_data, presets
            gc.collect()

            if result is None:
                failed.append(symbol)
                continue

            # Extract validated specialists (includes correlation as secondary section)
            extract_validated_specialists(result, args.output_dir)

            # Cleanup: remove part files for this symbol to free disk
            _parts_dir = result.get('parts_dir')
            if _parts_dir and os.path.isdir(_parts_dir):
                import glob as _glob_cleanup
                _pfiles = _glob_cleanup.glob(os.path.join(_parts_dir, "*.parquet"))
                _n_files = len(_pfiles)
                _total_bytes = sum(os.path.getsize(f) for f in _pfiles)
                import shutil
                shutil.rmtree(_parts_dir)
                print(f"   🗑️ Limpieza: eliminados {_n_files} part files"
                      f" ({_total_bytes / 1e9:.2f} GB) de {os.path.basename(_parts_dir)}/")

            del result
            gc.collect()
            completed += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            failed.append(symbol)

    print(f"\n{'='*70}")
    print(f"✅ Completed: {completed}/{len(symbols)}")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
