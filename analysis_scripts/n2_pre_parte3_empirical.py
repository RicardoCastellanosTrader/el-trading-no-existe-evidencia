#!/usr/bin/env python3
"""
N.2 pre-requisitos empíricos foundational pre-Parte 3 Frame 3.A meta-redesign.

N.2.1 — H_meta_1 BTC validation ANALYTICAL-ONLY:
  GMM N=6 BTC fit + identify_episodes + count n_episodes per cluster.
  Outcomes: 1 (5-6/6 valid → tradeoff genérico), 2 (<3/6 → propiedad profunda), 3 (3-4/6 mixto).

N.2.2 — BIC sweep cross-45 sym k=2..10:
  Per-sym GMM fit features Hurst+Z_ATR+ER cross k=2..10 con n_init=10 max_iter=300.
  Outcomes: A (45/45 k≤3 robust), B (45/45 k>3 sub-óptimo), C (mixto per-sym adaptive).

Scope: pre-Parte 3 spec reformulación foundational empirical. NO toca live/* productivo.

Usage: python -m analysis_scripts.n2_pre_parte3_empirical
"""

import json
import os
import sys
import time
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from collections import defaultdict

# Fix Windows cp1252 encoding (preserve unicode in output)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Suppress sklearn ConvergenceWarning (esperable con max_iter=300 en algunos sym)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*did not converge.*')

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_features import compute_regime_features

CACHE_DIR = os.path.join(_ROOT, "data_cache")
TIMEFRAME = "1h"

# 45 sym primary source train_regime_model.py:37-48 SYMBOLS list
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
assert len(SYMBOLS) == 45, f"Expected 45 sym, got {len(SYMBOLS)}"

LOOKBACK = 100  # SHORT (regime_features.py LOOKBACK_SHORT=100)
N_INIT = 10  # spec productivo train_regime_model.py:199
MAX_ITER = 300  # spec productivo
RANDOM_STATE = 42

# H_meta_1 BTC analytical params (spec regime_walk_forward.py)
BTC_N_TARGET = 6
MIN_EPISODE_BARS = 50  # regime_walk_forward.py:149
MIN_EPISODES_VALIDATE = 5  # regime_walk_forward.py:151

# BIC sweep params
K_RANGE = list(range(2, 11))  # k=2..10


def load_features(symbol):
    """Load OHLCV parquet + compute features stationary. Returns valid_features (n_valid, 3)."""
    sc = symbol.replace("/", "")
    path = os.path.join(CACHE_DIR, f"{sc}_{TIMEFRAME}.parquet")
    if not os.path.exists(path):
        return None, 0
    df = pd.read_parquet(path)
    if len(df) == 0:
        return None, 0
    if 'timestamp_ms' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    n_total = len(df)
    features, valid_mask = compute_regime_features(df, lookback=LOOKBACK)
    valid_features = features[valid_mask]
    return valid_features, n_total


def identify_episodes(cluster_labels, min_bars=MIN_EPISODE_BARS):
    """Replica regime_walk_forward.py:247 identify_episodes."""
    n_bars = len(cluster_labels)
    episodes = defaultdict(list)
    if n_bars == 0:
        return dict(episodes)

    current_label = cluster_labels[0]
    ep_start = 0
    for i in range(1, n_bars):
        if cluster_labels[i] != current_label:
            if current_label >= 0:
                ep_len = i - ep_start
                if ep_len >= min_bars:
                    episodes[current_label].append((int(ep_start), int(i)))
            current_label = cluster_labels[i]
            ep_start = i
    if current_label >= 0:
        ep_len = n_bars - ep_start
        if ep_len >= min_bars:
            episodes[current_label].append((int(ep_start), int(n_bars)))
    return dict(episodes)


def n2_1_btc_analytical():
    """H_meta_1 BTC validation ANALYTICAL-ONLY."""
    t0 = time.time()
    print(f"\n=== N.2.1 BTC analytical-only — start {datetime.now().isoformat()} ===")

    valid_features, n_total = load_features("BTC/USDT")
    if valid_features is None:
        return {"error": "BTC parquet not found"}

    n_valid = len(valid_features)
    print(f"[N.2.1] BTC bars total={n_total}, valid features (post-LOOKBACK_LONG=1000)={n_valid}")

    scaler = StandardScaler()
    X = scaler.fit_transform(valid_features)

    print(f"[N.2.1] Fitting GMM N={BTC_N_TARGET} (n_init={N_INIT}, max_iter={MAX_ITER})...")
    t1 = time.time()
    gmm = GaussianMixture(
        n_components=BTC_N_TARGET, covariance_type='full',
        n_init=N_INIT, random_state=RANDOM_STATE, max_iter=MAX_ITER
    )
    gmm.fit(X)
    fit_time = time.time() - t1
    bic = gmm.bic(X)
    print(f"[N.2.1] GMM fit done in {fit_time:.1f}s — converged={gmm.converged_}, n_iter={gmm.n_iter_}, BIC={bic:.1f}")

    cluster_labels = gmm.predict(X)

    # Identify episodes (NO toxic_tail extension — analytical only)
    episodes = identify_episodes(cluster_labels, min_bars=MIN_EPISODE_BARS)

    # Distribution per cluster
    cluster_distribution = {}
    n_valid_clusters = 0
    for k in range(BTC_N_TARGET):
        eps = episodes.get(k, [])
        n_eps = len(eps)
        n_bars_k = sum(end - start for start, end in eps)
        valid = n_eps >= MIN_EPISODES_VALIDATE
        if valid:
            n_valid_clusters += 1
        cluster_distribution[k] = {
            'n_episodes': n_eps,
            'n_bars_in_episodes': int(n_bars_k),
            'pct_bars': float(100 * n_bars_k / n_valid) if n_valid > 0 else 0,
            'valid': valid,
            'reason': 'OK' if valid else f'insufficient episodes ({n_eps} < {MIN_EPISODES_VALIDATE})',
        }

    # Outcome categorization
    if n_valid_clusters >= 5:
        outcome = "Outcome_1"
        outcome_desc = f"cluster sparsity = tradeoff genérico N×bar_count×MIN_EPISODES ({n_valid_clusters}/{BTC_N_TARGET} valid ≥5)"
    elif n_valid_clusters < 3:
        outcome = "Outcome_2"
        outcome_desc = f"cluster sparsity propiedad más profunda ({n_valid_clusters}/{BTC_N_TARGET} valid <3)"
    else:
        outcome = "Outcome_3"
        outcome_desc = f"cluster sparsity gradient sym-dependent ({n_valid_clusters}/{BTC_N_TARGET} valid mixto)"

    elapsed = time.time() - t0
    print(f"[N.2.1] DONE elapsed={elapsed:.1f}s ({elapsed/60:.1f} min) — n_valid_clusters={n_valid_clusters}/{BTC_N_TARGET} → {outcome}")
    print(f"[N.2.1] {outcome_desc}")

    return {
        'symbol': 'BTC/USDT',
        'n_target_clusters': BTC_N_TARGET,
        'n_bars_total': int(n_total),
        'n_valid_features': int(n_valid),
        'gmm_bic': float(bic),
        'gmm_converged': bool(gmm.converged_),
        'gmm_n_iter': int(gmm.n_iter_),
        'gmm_fit_seconds': fit_time,
        'cluster_distribution': cluster_distribution,
        'n_valid_clusters': int(n_valid_clusters),
        'outcome': outcome,
        'outcome_desc': outcome_desc,
        'elapsed_seconds': elapsed,
        'timestamp': datetime.now().isoformat(),
    }


def n2_2_bic_sweep_cross_45(output_dir):
    """BIC sweep cross-45 sym k=2..10. Saves incremental progress per sym."""
    print(f"\n=== N.2.2 BIC sweep cross-45 sym k=2..10 — start {datetime.now().isoformat()} ===")
    t0 = time.time()

    results = {}
    n_completed = 0
    n_skipped = 0
    incremental_path = os.path.join(output_dir, "n2_2_bic_sweep_INCREMENTAL.json")

    for idx, sym in enumerate(SYMBOLS, 1):
        sym_t0 = time.time()
        print(f"\n[N.2.2 {idx}/{len(SYMBOLS)}] {sym} ...")

        valid_features, n_total = load_features(sym)
        if valid_features is None:
            print(f"[N.2.2] {sym}: SKIPPED (no parquet)")
            n_skipped += 1
            continue

        n_valid = len(valid_features)
        if n_valid < 10 * 50:  # need at least 500 valid bars for k=10
            print(f"[N.2.2] {sym}: SKIPPED (insufficient valid bars: {n_valid} < 500)")
            n_skipped += 1
            continue

        scaler = StandardScaler()
        X = scaler.fit_transform(valid_features)

        bic_values = {}
        converged_per_k = {}
        for k in K_RANGE:
            try:
                gmm = GaussianMixture(
                    n_components=k, covariance_type='full',
                    n_init=N_INIT, random_state=RANDOM_STATE, max_iter=MAX_ITER
                )
                gmm.fit(X)
                bic = gmm.bic(X)
                bic_values[k] = float(bic)
                converged_per_k[k] = bool(gmm.converged_)
            except Exception as e:
                bic_values[k] = None
                converged_per_k[k] = False
                print(f"[N.2.2] {sym} k={k}: ERROR {type(e).__name__}: {e}")

        valid_bics = {k: v for k, v in bic_values.items() if v is not None}
        if valid_bics:
            k_optimal = min(valid_bics, key=valid_bics.get)
            best_bic = valid_bics[k_optimal]
            # Substantial margin: best vs second-best
            second_best = min((v for k, v in valid_bics.items() if k != k_optimal), default=None)
            margin = (second_best - best_bic) if second_best is not None else None
        else:
            k_optimal = None
            best_bic = None
            margin = None

        sym_elapsed = time.time() - sym_t0
        results[sym] = {
            'n_bars_total': int(n_total),
            'n_valid_features': int(n_valid),
            'bic_values': {str(k): v for k, v in bic_values.items()},
            'converged_per_k': {str(k): v for k, v in converged_per_k.items()},
            'k_optimal': int(k_optimal) if k_optimal else None,
            'best_bic': float(best_bic) if best_bic is not None else None,
            'bic_margin_vs_second': float(margin) if margin is not None else None,
            'elapsed_seconds': sym_elapsed,
        }
        n_completed += 1
        bic_str = f"{best_bic:.1f}" if best_bic is not None else "N/A"
        margin_str = f"{margin:.1f}" if margin is not None else "N/A"
        print(f"[N.2.2 {idx}/{len(SYMBOLS)}] {sym}: k_optimal={k_optimal} BIC={bic_str} margin={margin_str} elapsed={sym_elapsed:.1f}s")

        # Save incremental progress (resume-friendly + monitorable)
        with open(incremental_path, 'w') as f:
            json.dump({
                'progress': f"{idx}/{len(SYMBOLS)}",
                'n_completed': n_completed,
                'n_skipped': n_skipped,
                'elapsed_seconds_so_far': time.time() - t0,
                'per_symbol': results,
            }, f, indent=2)

    # Categorization Outcome A/B/C
    k_optimals = [r['k_optimal'] for r in results.values() if r['k_optimal'] is not None]
    if not k_optimals:
        outcome = "ERROR"
        outcome_desc = "No valid k_optimals"
    else:
        n_le3 = sum(1 for k in k_optimals if k <= 3)
        n_gt3 = sum(1 for k in k_optimals if k > 3)
        n_total_ko = len(k_optimals)
        if n_le3 == n_total_ko:
            outcome = "Outcome_A"
            outcome_desc = f"{n_le3}/{n_total_ko} sym k_optimal≤3 — MAX_K=3 robust empíricamente"
        elif n_gt3 == n_total_ko:
            outcome = "Outcome_B"
            outcome_desc = f"{n_gt3}/{n_total_ko} sym k_optimal>3 — MAX_K=3 sub-óptimo sistemáticamente"
        else:
            outcome = "Outcome_C"
            outcome_desc = f"{n_le3}/{n_total_ko} k≤3 + {n_gt3}/{n_total_ko} k>3 — per-sym adaptive MAX_K"

    elapsed = time.time() - t0
    print(f"\n[N.2.2] DONE elapsed={elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"[N.2.2] n_completed={n_completed}/{len(SYMBOLS)} (skipped={n_skipped}) → {outcome}")
    print(f"[N.2.2] {outcome_desc}")

    distribution = {str(k): sum(1 for ki in k_optimals if ki == k) for k in K_RANGE}

    return {
        'symbols_total': len(SYMBOLS),
        'n_completed': n_completed,
        'n_skipped': n_skipped,
        'k_range': K_RANGE,
        'per_symbol': results,
        'k_optimal_distribution': distribution,
        'outcome': outcome,
        'outcome_desc': outcome_desc,
        'elapsed_seconds': elapsed,
        'timestamp': datetime.now().isoformat(),
    }


def main():
    output_dir = os.path.join(_ROOT, "n2_pre_parte3_results")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # N.2.1 BTC analytical (fast first ~5-15 min)
    btc_result = n2_1_btc_analytical()
    btc_path = os.path.join(output_dir, f"n2_1_btc_analytical_{timestamp}.json")
    with open(btc_path, 'w') as f:
        json.dump(btc_result, f, indent=2)
    print(f"\n[OUTPUT] N.2.1 BTC analytical → {btc_path}")

    # N.2.2 BIC sweep cross-45 sym (slow ~1-3h)
    bic_result = n2_2_bic_sweep_cross_45(output_dir)
    bic_path = os.path.join(output_dir, f"n2_2_bic_sweep_cross_45_{timestamp}.json")
    with open(bic_path, 'w') as f:
        json.dump(bic_result, f, indent=2)
    print(f"\n[OUTPUT] N.2.2 BIC sweep cross-45 → {bic_path}")

    # Aggregated summary
    summary = {
        'timestamp': timestamp,
        'n2_1_btc_analytical': {
            'outcome': btc_result.get('outcome'),
            'outcome_desc': btc_result.get('outcome_desc'),
            'n_valid_clusters': btc_result.get('n_valid_clusters'),
            'elapsed_seconds': btc_result.get('elapsed_seconds'),
        },
        'n2_2_bic_sweep_cross_45': {
            'outcome': bic_result.get('outcome'),
            'outcome_desc': bic_result.get('outcome_desc'),
            'k_optimal_distribution': bic_result.get('k_optimal_distribution'),
            'n_completed': bic_result.get('n_completed'),
            'elapsed_seconds': bic_result.get('elapsed_seconds'),
        },
    }
    summary_path = os.path.join(output_dir, f"n2_summary_{timestamp}.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OUTPUT] Summary → {summary_path}")

    # Pointer file (latest)
    latest_path = os.path.join(output_dir, "LATEST.json")
    with open(latest_path, 'w') as f:
        json.dump({'timestamp': timestamp, 'summary_path': summary_path,
                   'btc_path': btc_path, 'bic_path': bic_path}, f, indent=2)


if __name__ == "__main__":
    main()
