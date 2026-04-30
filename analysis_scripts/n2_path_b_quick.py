#!/usr/bin/env python3
"""
N.2 Path B — Quick BIC + operability sweep k=2..20 cross-3 sym k_max_op=15 truncated.

Sym targeted (from N.2 extended outcomes empíricos):
  XRP/USDT (n_valid=68,070), TRX/USDT (n_valid=67,155), GRT/USDT (n_valid=45,135).

Verifies operability cap natural < 20 cross-amplio. Spec ~5-10 min compute.
Permanent §13.2 caveat documentation BIC overfitting beyond operability.

Usage: python -m analysis_scripts.n2_path_b_quick
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

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*did not converge.*')

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_features import compute_regime_features

CACHE_DIR = os.path.join(_ROOT, "data_cache")
TIMEFRAME = "1h"

SYMBOLS = ["XRP/USDT", "TRX/USDT", "GRT/USDT"]

LOOKBACK = 100
N_INIT = 10
MAX_ITER = 300
RANDOM_STATE = 42

MIN_EPISODE_BARS = 50
MIN_EPISODES_VALIDATE = 5

K_RANGE = list(range(2, 21))  # k=2..20


def load_features(symbol):
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
    return features[valid_mask], n_total


def identify_episodes(cluster_labels, min_bars=MIN_EPISODE_BARS):
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
    if current_label >= 0 and (n_bars - ep_start) >= min_bars:
        episodes[current_label].append((int(ep_start), int(n_bars)))
    return dict(episodes)


def main():
    output_dir = os.path.join(_ROOT, "n2_pre_parte3_results")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"=== N.2 Path B quick — start {datetime.now().isoformat()} ===")
    print(f"Symbols: {SYMBOLS}, k range {K_RANGE[0]}..{K_RANGE[-1]} ({len(K_RANGE)} k values)")
    print(f"Total fits: {len(SYMBOLS)} sym x {len(K_RANGE)} k = {len(SYMBOLS) * len(K_RANGE)}")

    t0 = time.time()
    per_sym_results = {}

    for sym in SYMBOLS:
        sym_t0 = time.time()
        print(f"\n[{sym}] ...")

        valid_features, n_total = load_features(sym)
        if valid_features is None:
            print(f"[{sym}]: SKIPPED (no parquet)")
            continue
        n_valid = len(valid_features)

        scaler = StandardScaler()
        X = scaler.fit_transform(valid_features)

        bic_values = {}
        n_clusters_valid_per_k = {}
        operability_classification = {}

        for k in K_RANGE:
            try:
                gmm = GaussianMixture(
                    n_components=k, covariance_type='full',
                    n_init=N_INIT, random_state=RANDOM_STATE, max_iter=MAX_ITER
                )
                gmm.fit(X)
                bic = float(gmm.bic(X))
                bic_values[k] = bic

                labels = gmm.predict(X)
                episodes = identify_episodes(labels, min_bars=MIN_EPISODE_BARS)
                n_valid_clusters = sum(1 for c in range(k) if len(episodes.get(c, [])) >= MIN_EPISODES_VALIDATE)
                n_clusters_valid_per_k[k] = n_valid_clusters
                ratio = n_valid_clusters / k
                if ratio >= 0.5:
                    op_class = "VIABLE"
                elif ratio >= 0.3:
                    op_class = "MARGINAL"
                else:
                    op_class = "INFEASIBLE"
                operability_classification[k] = {"n_valid": n_valid_clusters, "ratio": ratio, "class": op_class}
            except Exception as e:
                print(f"[{sym}] k={k}: ERROR {e}")

        valid_bics = {k: v for k, v in bic_values.items() if v is not None}
        k_optimal_bic = min(valid_bics, key=valid_bics.get) if valid_bics else None
        best_bic = valid_bics.get(k_optimal_bic) if k_optimal_bic else None

        # k_max_operable: max k where VIABLE
        k_max_operable = None
        for k in K_RANGE:
            op = operability_classification.get(k, {})
            if op.get("class") == "VIABLE":
                k_max_operable = k

        # k_first_INFEASIBLE: first k where INFEASIBLE (operability cliff)
        k_first_infeasible = None
        for k in K_RANGE:
            op = operability_classification.get(k, {})
            if op.get("class") == "INFEASIBLE":
                k_first_infeasible = k
                break

        sym_elapsed = time.time() - sym_t0
        per_sym_results[sym] = {
            'n_bars_total': int(n_total),
            'n_valid_features': int(n_valid),
            'bic_values': {str(k): v for k, v in bic_values.items()},
            'n_clusters_valid_per_k': {str(k): v for k, v in n_clusters_valid_per_k.items()},
            'operability_classification': {str(k): v for k, v in operability_classification.items()},
            'k_optimal_bic': k_optimal_bic,
            'best_bic': best_bic,
            'k_max_operable': k_max_operable,
            'k_first_INFEASIBLE': k_first_infeasible,
            'elapsed_seconds': sym_elapsed,
        }
        print(f"[{sym}] n_valid={n_valid}: k_opt_BIC={k_optimal_bic} BIC={best_bic:.1f} k_max_op={k_max_operable} k_first_INFEASIBLE={k_first_infeasible} elapsed={sym_elapsed:.1f}s")

    elapsed_total = time.time() - t0

    # Aggregate analysis
    k_max_ops = [r['k_max_operable'] for r in per_sym_results.values() if r['k_max_operable'] is not None]
    k_first_infs = [r['k_first_INFEASIBLE'] for r in per_sym_results.values() if r['k_first_INFEASIBLE'] is not None]
    k_opt_bics = [r['k_optimal_bic'] for r in per_sym_results.values() if r['k_optimal_bic'] is not None]

    if k_max_ops:
        k_max_op_max = max(k_max_ops)
        k_max_op_at_20 = sum(1 for k in k_max_ops if k == 20)
    else:
        k_max_op_max = None
        k_max_op_at_20 = 0

    if k_max_op_at_20 == 0:
        outcome = "Outcome_op_cap_natural_below_20"
        outcome_desc = f"All 3 sym operability cap natural < 20 (max k_max_op = {k_max_op_max}). Operability binding constraint < 20 cross-amplio confirmed empirically."
    else:
        outcome = "Outcome_op_cap_at_20"
        outcome_desc = f"{k_max_op_at_20}/3 sym k_max_op=20 (truncation persists upper bound). Operability cap natural may extend ≥20 cross-amplio."

    print(f"\n{'='*70}")
    print(f"=== N.2 Path B DONE elapsed={elapsed_total:.1f}s ({elapsed_total/60:.1f} min) ===")
    print(f"\nOutcome: {outcome}")
    print(f"  {outcome_desc}")
    print(f"\nk_max_operable cross-3 sym: {k_max_ops}")
    print(f"k_first_INFEASIBLE cross-3 sym: {k_first_infs}")
    print(f"k_optimal_BIC cross-3 sym: {k_opt_bics}")

    summary = {
        'timestamp': timestamp,
        'symbols': SYMBOLS,
        'k_range': K_RANGE,
        'n_init': N_INIT,
        'elapsed_seconds': elapsed_total,
        'outcome': outcome,
        'outcome_desc': outcome_desc,
        'k_max_operable_cross_3': k_max_ops,
        'k_first_INFEASIBLE_cross_3': k_first_infs,
        'k_optimal_BIC_cross_3': k_opt_bics,
        'per_symbol': per_sym_results,
    }
    out_path = os.path.join(output_dir, f"n2_path_b_quick_{timestamp}.json")
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OUTPUT] {out_path}")


if __name__ == "__main__":
    main()
