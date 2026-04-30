#!/usr/bin/env python3
"""
Eje 1 Smoke MANDATORY Phase 1 — Cluster label agreement HMM vs GMM ONDO N=3 productive.

Cardinal H_meta_3 sanity check pragmatic: if HMM-classified labels match GMM-classified labels
substantially (>=90%), ranking selectivity within survivor pool will be NEAR-IDENTICAL post-HMM
→ HMM_NEUTRAL likely sin full walk-forward needed.

If substantially differ (<70%), Phase 2 full walk-forward MANDATORY.

Output: agreement %, episode distribution per cluster, HMM_NEUTRAL early-exit decision.

Run: python -m analysis_scripts.eje1_smoke_phase1_cluster_agreement
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from collections import defaultdict
from sklearn.preprocessing import StandardScaler

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_features import compute_regime_features
from hmm_gaussian_numba import GaussianHMM as CustomHMM

CACHE_DIR = os.path.join(_ROOT, "data_cache")
MODEL_DIR = os.path.join(_ROOT, "regime_models")
TIMEFRAME = "1h"

LOOKBACK = 100
MIN_EPISODE_BARS = 50
MIN_EPISODES_VALIDATE = 5

# HMM training params (matching productive GMM productive train_regime_model.py)
N_INIT = 10
N_ITER = 300
RANDOM_STATE = 42
REG_COVAR = 1e-6


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


def hungarian_match(means_a, means_b):
    from scipy.optimize import linear_sum_assignment
    cost = np.linalg.norm(means_a[:, None] - means_b[None, :], axis=2)
    _, col_ind = linear_sum_assignment(cost)
    return col_ind


def main():
    print(f"=== Eje 1 Smoke MANDATORY Phase 1 — Cluster agreement HMM vs GMM ONDO ===")
    print(f"Start: {datetime.now().isoformat()}")

    # 1. Load ONDO features
    sym = "ONDO/USDT"
    sc = sym.replace("/", "")
    parquet_path = os.path.join(CACHE_DIR, f"{sc}_{TIMEFRAME}.parquet")
    df = pd.read_parquet(parquet_path)
    if 'timestamp_ms' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    print(f"\nONDO bars: {len(df)}")

    features, valid_mask = compute_regime_features(df, lookback=LOOKBACK)
    valid_features = features[valid_mask]
    valid_indices = np.where(valid_mask)[0]
    print(f"Valid features: {len(valid_features)} (post-LOOKBACK_LONG=1000)")

    # 2. Load productive GMM model
    model_path = os.path.join(MODEL_DIR, "ONDO_regime.joblib")
    model_data_gmm = joblib.load(model_path)
    gmm = model_data_gmm['gmm']
    scaler_gmm = model_data_gmm['scaler']
    n_clusters_gmm = model_data_gmm['n_clusters']
    print(f"\nProductive GMM ONDO: k={n_clusters_gmm}, BIC={model_data_gmm.get('bic_values', {}).get(n_clusters_gmm, 'N/A')}")

    X_gmm = scaler_gmm.transform(valid_features)
    labels_gmm = gmm.predict(X_gmm)

    # 3. Train custom HMM ONDO with same K as productive GMM (apple-to-apples)
    print(f"\nTraining custom HMM ONDO with K={n_clusters_gmm} (matching productive GMM)...")
    t0 = time.time()
    scaler_hmm = StandardScaler()
    X_hmm = scaler_hmm.fit_transform(valid_features)
    hmm = CustomHMM(
        n_components=n_clusters_gmm, covariance_type='full',
        n_iter=N_ITER, random_state=RANDOM_STATE, n_init=N_INIT, reg_covar=REG_COVAR
    )
    hmm.fit(X_hmm)
    hmm_time = time.time() - t0
    labels_hmm = hmm.predict(X_hmm)
    print(f"HMM fit: converged={hmm.converged_}, n_iter={hmm.n_iter_}, time={hmm_time:.1f}s")
    print(f"HMM BIC: {hmm.bic(X_hmm):.1f}")

    # 4. Hungarian match HMM cluster labels to GMM cluster labels (cluster IDs are arbitrary)
    matching_h2g = hungarian_match(hmm.means_, gmm.means_)
    labels_hmm_remapped = matching_h2g[labels_hmm]
    print(f"\nHungarian matching HMM->GMM: {matching_h2g.tolist()}")

    # 5. Compute agreement
    agreement_pct = float(np.mean(labels_hmm_remapped == labels_gmm))
    print(f"\nCluster label agreement HMM vs GMM: {agreement_pct:.2%}")

    # 6. Episode distribution per (model, cluster)
    eps_gmm = identify_episodes(labels_gmm, min_bars=MIN_EPISODE_BARS)
    eps_hmm = identify_episodes(labels_hmm_remapped, min_bars=MIN_EPISODE_BARS)
    print(f"\nEpisode distribution (GMM remapped to GMM cluster IDs):")
    for k in range(n_clusters_gmm):
        n_eps_g = len(eps_gmm.get(k, []))
        n_bars_g = sum(e - s for s, e in eps_gmm.get(k, []))
        valid_g = "VALID" if n_eps_g >= MIN_EPISODES_VALIDATE else "INFEASIBLE"
        n_eps_h = len(eps_hmm.get(k, []))
        n_bars_h = sum(e - s for s, e in eps_hmm.get(k, []))
        valid_h = "VALID" if n_eps_h >= MIN_EPISODES_VALIDATE else "INFEASIBLE"
        print(f"  C{k}: GMM={n_eps_g} eps/{n_bars_g} bars [{valid_g}]  |  HMM={n_eps_h} eps/{n_bars_h} bars [{valid_h}]")

    # 7. Outcome categorization Phase 1
    if agreement_pct >= 0.90:
        outcome = "HMM_NEUTRAL_LIKELY"
        outcome_desc = (f"Cluster labels HMM vs GMM agreement {agreement_pct:.2%} >= 90% → ranking selectivity "
                        f"within survivor pool NEAR-IDENTICAL post-HMM (no substantial classification change). "
                        f"Phase 2 full walk-forward likely confirms HMM_NEUTRAL. Ricardo escalación strategic.")
    elif agreement_pct < 0.70:
        outcome = "PHASE2_MANDATORY"
        outcome_desc = (f"Cluster labels HMM vs GMM agreement {agreement_pct:.2%} < 70% → substantial classification "
                        f"divergence → top-100 specialists per cluster differ → ranking selectivity may differ "
                        f"empirically. Phase 2 full walk-forward MANDATORY for HMM_PASS/HMM_FAIL discrimination.")
    else:
        outcome = "PHASE2_RECOMMENDED"
        outcome_desc = (f"Cluster labels HMM vs GMM agreement {agreement_pct:.2%} en [70%, 90%) borderline → "
                        f"Ricardo decisión strategic Phase 2 full walk-forward OR HMM_NEUTRAL acceptance.")

    print(f"\nOutcome Phase 1: {outcome}")
    print(f"  {outcome_desc}")

    # Save JSON
    output_dir = os.path.join(_ROOT, "n2_pre_parte3_results")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"eje1_smoke_phase1_cluster_agreement_{timestamp}.json")
    summary = {
        'timestamp': timestamp,
        'symbol': sym,
        'n_clusters': int(n_clusters_gmm),
        'n_bars_total': int(len(df)),
        'n_valid_features': int(len(valid_features)),
        'gmm_bic_productive': model_data_gmm.get('bic_values', {}).get(n_clusters_gmm),
        'hmm_bic': float(hmm.bic(X_hmm)),
        'hmm_fit_seconds': hmm_time,
        'hungarian_matching_hmm_to_gmm': matching_h2g.tolist(),
        'cluster_label_agreement_pct': agreement_pct,
        'episodes_per_cluster_gmm': {str(k): len(eps_gmm.get(k, [])) for k in range(n_clusters_gmm)},
        'episodes_per_cluster_hmm': {str(k): len(eps_hmm.get(k, [])) for k in range(n_clusters_gmm)},
        'outcome': outcome,
        'outcome_desc': outcome_desc,
    }
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OUTPUT] {out_path}")


if __name__ == "__main__":
    main()
