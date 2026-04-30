#!/usr/bin/env python3
"""
HMM reference comparison custom Numba HMM (combolab/hmm_gaussian_numba.py) vs hmmlearn GaussianHMM
cross-multiple synthetic + real datasets reales.

Sub-Sesión Eje 1 Opción α split B mandatory rigor methodology completo independiente.
Run from venv hmm_reference_env Python 3.11:
    hmm_reference_env/Scripts/python -m analysis_scripts.hmm_reference_comparison

Outputs JSON estructurado + cumulative outcome categorization.
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import linear_sum_assignment

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from hmm_gaussian_numba import GaussianHMM as CustomHMM
from hmmlearn.hmm import GaussianHMM as RefHMM
from regime_features import compute_regime_features

CACHE_DIR = os.path.join(_ROOT, "data_cache")
TIMEFRAME = "1h"

LOOKBACK = 100
N_INIT = 5
N_ITER = 200
TOL = 1e-3
RANDOM_STATE = 42
REG_COVAR = 1e-3


def hungarian_match(means_custom, means_ref):
    """Hungarian assignment custom→ref clusters by closest mean."""
    cost = np.linalg.norm(means_custom[:, None] - means_ref[None, :], axis=2)
    _, col_ind = linear_sum_assignment(cost)
    return col_ind


def load_features(symbol):
    sc = symbol.replace("/", "")
    path = os.path.join(CACHE_DIR, f"{sc}_{TIMEFRAME}.parquet")
    if not os.path.exists(path):
        return None
    df = pd.read_parquet(path)
    if 'timestamp_ms' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    features, valid_mask = compute_regime_features(df, lookback=LOOKBACK)
    return features[valid_mask]


def gen_2state(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    transmat = np.array([[0.9, 0.1], [0.1, 0.9]])
    means = np.array([[-2.0, 0.0], [2.0, 0.0]])
    covars = np.array([[[0.5, 0.0], [0.0, 0.5]], [[0.5, 0.0], [0.0, 0.5]]])
    states = np.zeros(n, dtype=np.int64)
    for t in range(1, n):
        states[t] = rng.choice(2, p=transmat[states[t-1]])
    X = np.zeros((n, 2))
    for t in range(n):
        X[t] = rng.multivariate_normal(means[states[t]], covars[states[t]])
    return X


def gen_3state(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    transmat = np.array([[0.85, 0.10, 0.05], [0.10, 0.85, 0.05], [0.05, 0.05, 0.90]])
    means = np.array([[0.0, 0.0, 0.0], [4.0, 4.0, 4.0], [-3.0, 3.0, -3.0]])
    covars = np.array([np.eye(3) * 0.5 for _ in range(3)])
    states = np.zeros(n, dtype=np.int64)
    for t in range(1, n):
        states[t] = rng.choice(3, p=transmat[states[t-1]])
    X = np.zeros((n, 3))
    for t in range(n):
        X[t] = rng.multivariate_normal(means[states[t]], covars[states[t]])
    return X


def gen_4state_5dim(n=1500, seed=42):
    rng = np.random.default_rng(seed)
    K, D = 4, 5
    transmat = np.full((K, K), 0.05)
    np.fill_diagonal(transmat, 0.85)
    for k in range(K):
        transmat[k] /= transmat[k].sum()
    means = rng.standard_normal((K, D)) * 3.0
    covars = np.array([np.eye(D) * 0.5 for _ in range(K)])
    states = np.zeros(n, dtype=np.int64)
    for t in range(1, n):
        states[t] = rng.choice(K, p=transmat[states[t-1]])
    X = np.zeros((n, D))
    for t in range(n):
        X[t] = rng.multivariate_normal(means[states[t]], covars[states[t]])
    return X


def fit_both_libraries(X, K, label):
    print(f"\n=== {label} (X shape {X.shape}, K={K}) ===")

    t0 = time.time()
    custom = CustomHMM(n_components=K, n_iter=N_ITER, tol=TOL,
                       random_state=RANDOM_STATE, n_init=N_INIT, reg_covar=REG_COVAR)
    custom.fit(X)
    custom_time = time.time() - t0
    custom_ll = float(custom.score(X))
    custom_pred = custom.predict(X)

    t1 = time.time()
    ref = RefHMM(n_components=K, covariance_type='full', n_iter=N_ITER, tol=TOL,
                 random_state=RANDOM_STATE, init_params='stmc', params='stmc',
                 implementation='log')
    ref.fit(X)
    ref_time = time.time() - t1
    ref_ll = float(ref.score(X))
    ref_pred = ref.predict(X)

    matching = hungarian_match(custom.means_, ref.means_)
    inv_matching = np.argsort(matching)
    custom_means_perm = custom.means_[inv_matching]
    custom_transmat_perm = custom.transmat_[inv_matching][:, inv_matching]

    means_max_diff = float(np.max(np.linalg.norm(custom_means_perm - ref.means_, axis=1)))
    transmat_frobenius = float(np.linalg.norm(custom_transmat_perm - ref.transmat_))
    ll_relative_diff = float(abs(custom_ll - ref_ll) / max(abs(ref_ll), 1e-9))

    custom_pred_remapped = matching[custom_pred]
    pred_agreement = float(np.mean(custom_pred_remapped == ref_pred))

    print(f"  custom: converged={custom.converged_} iter={custom.n_iter_} ll={custom_ll:.2f} time={custom_time:.1f}s")
    print(f"  ref:    converged={ref.monitor_.converged} iter={ref.monitor_.iter} ll={ref_ll:.2f} time={ref_time:.1f}s")
    print(f"  Hungarian matching custom→ref: {matching.tolist()}")
    print(f"  means_max_diff={means_max_diff:.4f}, transmat_frobenius={transmat_frobenius:.4f}")
    print(f"  ll_relative_diff={ll_relative_diff:.2e}, predict_agreement={pred_agreement:.2%}")

    return {
        'label': label,
        'X_shape': list(X.shape),
        'K': K,
        'custom_converged': bool(custom.converged_),
        'custom_n_iter': int(custom.n_iter_),
        'custom_log_likelihood': custom_ll,
        'custom_fit_time_seconds': custom_time,
        'ref_converged': bool(ref.monitor_.converged),
        'ref_n_iter': int(ref.monitor_.iter),
        'ref_log_likelihood': ref_ll,
        'ref_fit_time_seconds': ref_time,
        'matching': matching.tolist(),
        'means_max_diff': means_max_diff,
        'transmat_frobenius_norm': transmat_frobenius,
        'log_likelihood_relative_diff': ll_relative_diff,
        'predict_agreement_pct': pred_agreement,
    }


def main():
    output_dir = os.path.join(_ROOT, "n2_pre_parte3_results")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t_total = time.time()

    print(f"=== HMM reference comparison custom vs hmmlearn — start {datetime.now().isoformat()} ===")

    results = []

    print("\n[Synthetic datasets]")
    results.append(fit_both_libraries(gen_2state(1000, 42), K=2, label='T_REF_1_synthetic_2state'))
    results.append(fit_both_libraries(gen_3state(1000, 42), K=3, label='T_REF_2_synthetic_3state'))
    results.append(fit_both_libraries(gen_4state_5dim(1500, 42), K=4, label='T_REF_3_synthetic_4state_5dim'))

    print("\n[Real datasets]")
    btc = load_features("BTC/USDT")
    if btc is not None:
        results.append(fit_both_libraries(btc, K=3, label='T_REF_4_BTC_k3_productive_baseline'))
        results.append(fit_both_libraries(btc, K=6, label='T_REF_5_BTC_k6_subframe3a1_methodology'))

    ondo = load_features("ONDO/USDT")
    if ondo is not None:
        results.append(fit_both_libraries(ondo, K=4, label='T_REF_6_ONDO_k4_kmaxop_n2extended'))

    eth = load_features("ETH/USDT")
    if eth is not None:
        results.append(fit_both_libraries(eth, K=12, label='T_REF_7_ETH_k12_kmaxop_n2extended_amplio'))

    elapsed = time.time() - t_total

    print(f"\n{'='*70}")
    print("=== AGGREGATE ANALYSIS ===")
    n_pass_strict = 0
    n_pass_marginal = 0
    n_fail = 0
    for r in results:
        ll_diff = r['log_likelihood_relative_diff']
        means_diff = r['means_max_diff']
        pred_agree = r['predict_agreement_pct']
        strict = (ll_diff < 1e-3 and pred_agree > 0.95 and means_diff < 0.5)
        marginal = (ll_diff < 1e-2 and pred_agree > 0.80 and means_diff < 1.5)
        if strict:
            n_pass_strict += 1
            outcome = "PASS_STRICT"
        elif marginal:
            n_pass_marginal += 1
            outcome = "PASS_MARGINAL"
        else:
            n_fail += 1
            outcome = "FAIL"
        r['outcome'] = outcome
        print(f"  {r['label']}: {outcome}  ll_diff={ll_diff:.2e}  pred_agree={pred_agree:.2%}  means_diff={means_diff:.3f}")

    n_total = len(results)
    print(f"\nTotals: PASS_STRICT={n_pass_strict}/{n_total}, PASS_MARGINAL={n_pass_marginal}/{n_total}, FAIL={n_fail}/{n_total}")
    print(f"Total elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")

    if n_fail == 0:
        cumulative = "PASS_ALL_REFERENCE_STRICT" if n_pass_strict == n_total else "PASS_ALL_REFERENCE_MARGINAL_OK"
    elif n_fail <= max(1, n_total // 3):
        cumulative = "PASS_MAJORITY_MARGINAL_DIFFS"
    else:
        cumulative = "FAIL_SUBSTANTIAL"
    print(f"Cumulative outcome: {cumulative}")

    summary = {
        'timestamp': timestamp,
        'n_tests': n_total,
        'n_pass_strict': n_pass_strict,
        'n_pass_marginal': n_pass_marginal,
        'n_fail': n_fail,
        'cumulative_outcome': cumulative,
        'elapsed_seconds': elapsed,
        'tests': results,
    }
    out_path = os.path.join(output_dir, f"hmm_reference_comparison_{timestamp}.json")
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OUTPUT] {out_path}")


if __name__ == "__main__":
    main()
