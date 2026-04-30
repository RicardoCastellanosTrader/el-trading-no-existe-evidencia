#!/usr/bin/env python3
"""
HMM init diagnostic — discriminate init divergence vs implementation bug for FAIL_SUBSTANTIAL cases.

Test synthetic 3-state + BTC k=3 con identical initial params injected directly:
  - Both libraries seed con SAME startprob, transmat, means, covars
  - Run Baum-Welch from same starting point
  - Compare convergence trajectory + final log_likelihood

If both converge to identical params from same init → implementation correct, divergence was init.
If diverge despite same init → bug in one of them.
"""

import os
import sys
import time
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from hmm_gaussian_numba import GaussianHMM as CustomHMM
from hmmlearn.hmm import GaussianHMM as RefHMM


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


def fit_custom_with_explicit_init(X, K, startprob_init, transmat_init, means_init, covars_init, n_iter=200, tol=1e-3):
    """Run custom HMM con explicit initial params (bypass internal init)."""
    from hmm_gaussian_numba import (_gaussian_log_emissions_full, _forward_log,
                                     _backward_log, _smoother_gamma_sumxi, _m_step_update)

    startprob = startprob_init.copy()
    transmat = transmat_init.copy()
    means = means_init.copy()
    covars = covars_init.copy()
    log_likelihood_prev = -np.inf
    history = []

    for iter_ in range(n_iter):
        log_emissions = _gaussian_log_emissions_full(X, means, covars)
        log_transmat = np.log(transmat + 1e-300)
        log_startprob = np.log(startprob + 1e-300)
        log_alpha, log_likelihood = _forward_log(log_emissions, log_transmat, log_startprob)
        history.append(log_likelihood)
        if iter_ > 0:
            delta = log_likelihood - log_likelihood_prev
            if delta < tol:
                break
        log_likelihood_prev = log_likelihood
        log_beta = _backward_log(log_emissions, log_transmat)
        log_gamma, sum_xi = _smoother_gamma_sumxi(log_alpha, log_beta, log_emissions, log_transmat, log_likelihood)
        startprob, transmat, means, covars = _m_step_update(X, log_gamma, sum_xi, 1e-6)

    return {
        'startprob': startprob, 'transmat': transmat, 'means': means, 'covars': covars,
        'log_likelihood': float(log_likelihood), 'n_iter': iter_ + 1, 'history': history,
    }


def fit_ref_with_explicit_init(X, K, startprob_init, transmat_init, means_init, covars_init, n_iter=200, tol=1e-3):
    """Run hmmlearn HMM con explicit initial params via init_params=''."""
    ref = RefHMM(n_components=K, covariance_type='full', n_iter=n_iter, tol=tol,
                 init_params='', params='stmc', implementation='log')
    ref.startprob_ = startprob_init.copy()
    ref.transmat_ = transmat_init.copy()
    ref.means_ = means_init.copy()
    ref.covars_ = covars_init.copy()
    ref.fit(X)
    return {
        'startprob': ref.startprob_, 'transmat': ref.transmat_, 'means': ref.means_, 'covars': ref.covars_,
        'log_likelihood': float(ref.score(X)), 'n_iter': ref.monitor_.iter,
        'history': list(ref.monitor_.history),
    }


def main():
    print(f"=== HMM init diagnostic — discriminate init vs implementation bug ===\n")

    # Test 1: synthetic 3-state with explicit init injected
    X = gen_3state(1000, 42)
    K, D = 3, 3

    # Build identical init params for both libraries
    rng = np.random.default_rng(42)
    indices = rng.choice(X.shape[0], size=K, replace=False)
    startprob_init = np.full(K, 1.0 / K)
    # uniform transmat to match hmmlearn default
    transmat_init = np.full((K, K), 1.0 / K)
    means_init = X[indices].copy()
    cov_data = np.cov(X.T)
    covars_init = np.array([cov_data + 1e-3 * np.eye(D) for _ in range(K)])

    print("Test 1: synthetic 3-state, EXPLICIT IDENTICAL INIT (uniform transmat + random sample means + data cov):")
    print(f"  X shape: {X.shape}")
    print(f"  startprob_init: {startprob_init}")
    print(f"  transmat_init (row 0): {transmat_init[0]}")
    print(f"  means_init: {means_init.tolist()}")

    r_custom = fit_custom_with_explicit_init(X, K, startprob_init, transmat_init, means_init, covars_init)
    r_ref = fit_ref_with_explicit_init(X, K, startprob_init, transmat_init, means_init, covars_init)

    print(f"\n  Custom result: ll={r_custom['log_likelihood']:.4f}, n_iter={r_custom['n_iter']}")
    print(f"  Ref result:    ll={r_ref['log_likelihood']:.4f}, n_iter={r_ref['n_iter']}")
    print(f"  ll_diff_relative: {abs(r_custom['log_likelihood'] - r_ref['log_likelihood']) / abs(r_ref['log_likelihood']):.2e}")

    # Compare final params (same cluster ordering since same init)
    means_diff = np.linalg.norm(r_custom['means'] - r_ref['means'])
    transmat_diff = np.linalg.norm(r_custom['transmat'] - r_ref['transmat'])
    print(f"  means Frobenius diff: {means_diff:.6f}")
    print(f"  transmat Frobenius diff: {transmat_diff:.6f}")
    print(f"\n  Custom convergence trajectory (last 10): {[f'{x:.2f}' for x in r_custom['history'][-10:]]}")
    print(f"  Ref convergence trajectory (last 10):    {[f'{x:.2f}' for x in r_ref['history'][-10:]]}")

    # Test 2: BTC k=3 EXPLICIT IDENTICAL INIT
    print("\n" + "=" * 70)
    print("Test 2: BTC features k=3, EXPLICIT IDENTICAL INIT:")

    import pandas as pd
    sys.path.insert(0, _ROOT)
    from regime_features import compute_regime_features
    df = pd.read_parquet(os.path.join(_ROOT, 'data_cache', 'BTCUSDT_1h.parquet'))
    if 'timestamp_ms' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    features, valid_mask = compute_regime_features(df, lookback=100)
    X_btc = features[valid_mask]
    K, D = 3, 3

    rng = np.random.default_rng(42)
    indices = rng.choice(X_btc.shape[0], size=K, replace=False)
    startprob_init_btc = np.full(K, 1.0 / K)
    transmat_init_btc = np.full((K, K), 1.0 / K)
    means_init_btc = X_btc[indices].copy()
    cov_data_btc = np.cov(X_btc.T)
    covars_init_btc = np.array([cov_data_btc + 1e-3 * np.eye(D) for _ in range(K)])

    print(f"  X shape: {X_btc.shape}")

    t0 = time.time()
    r_custom_btc = fit_custom_with_explicit_init(X_btc, K, startprob_init_btc, transmat_init_btc, means_init_btc, covars_init_btc)
    t_custom = time.time() - t0
    t1 = time.time()
    r_ref_btc = fit_ref_with_explicit_init(X_btc, K, startprob_init_btc, transmat_init_btc, means_init_btc, covars_init_btc)
    t_ref = time.time() - t1

    print(f"\n  Custom result: ll={r_custom_btc['log_likelihood']:.4f}, n_iter={r_custom_btc['n_iter']}, time={t_custom:.1f}s")
    print(f"  Ref result:    ll={r_ref_btc['log_likelihood']:.4f}, n_iter={r_ref_btc['n_iter']}, time={t_ref:.1f}s")
    rel_diff = abs(r_custom_btc['log_likelihood'] - r_ref_btc['log_likelihood']) / abs(r_ref_btc['log_likelihood'])
    print(f"  ll_diff_relative: {rel_diff:.2e}")
    means_diff_btc = np.linalg.norm(r_custom_btc['means'] - r_ref_btc['means'])
    transmat_diff_btc = np.linalg.norm(r_custom_btc['transmat'] - r_ref_btc['transmat'])
    print(f"  means Frobenius diff: {means_diff_btc:.6f}")
    print(f"  transmat Frobenius diff: {transmat_diff_btc:.6f}")

    # Diagnostic conclusion
    print("\n" + "=" * 70)
    print("=== DIAGNOSTIC CONCLUSION ===")
    if rel_diff < 1e-3 and means_diff_btc < 0.01:
        print("✓ IMPLEMENTATION CORRECT: with identical init both libraries converge to identical params")
        print("  → FAIL_SUBSTANTIAL outcome was due to DIFFERENT default init strategies, NOT implementation bug")
    else:
        print("✗ DIVERGENCE PERSISTS even with identical init — investigate algorithm bug")
        print(f"  rel_diff = {rel_diff:.2e}, means_diff = {means_diff_btc:.4f}")


if __name__ == "__main__":
    main()
