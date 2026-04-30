"""
Tests greenfield para custom Numba HMM Gaussian.
Frame 3.A meta-redesign Eje 1 paradigm shift cardinal — split A core algoritmos.

References: Rabiner 1989 IEEE Tutorial + Bishop PRML Ch. 13.
"""

import os
import sys
import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from hmm_gaussian_numba import (
    GaussianHMM,
    _logsumexp_1d,
    _logaddexp,
    _gaussian_log_emissions_full,
    _forward_log,
    _backward_log,
    _smoother_gamma_sumxi,
    _forward_step_online,
)


# ============================================================
# Synthetic data generators
# ============================================================

def _generate_2state_sequence(n_bars=500, seed=42):
    """Synthetic 2-state Gaussian HMM sequence: state 0 means [0,0], state 1 means [3,3]."""
    rng = np.random.default_rng(seed)
    transmat_true = np.array([[0.9, 0.1], [0.15, 0.85]])
    means_true = np.array([[0.0, 0.0], [3.0, 3.0]])
    covars_true = np.array([[[0.5, 0.0], [0.0, 0.5]], [[0.5, 0.0], [0.0, 0.5]]])

    states = np.zeros(n_bars, dtype=np.int64)
    states[0] = 0
    for t in range(1, n_bars):
        states[t] = rng.choice(2, p=transmat_true[states[t - 1]])

    X = np.zeros((n_bars, 2))
    for t in range(n_bars):
        X[t] = rng.multivariate_normal(means_true[states[t]], covars_true[states[t]])

    return X, states, transmat_true, means_true, covars_true


def _generate_3state_sequence(n_bars=600, seed=42):
    """Synthetic 3-state Gaussian sequence."""
    rng = np.random.default_rng(seed)
    transmat_true = np.array([
        [0.85, 0.10, 0.05],
        [0.10, 0.85, 0.05],
        [0.05, 0.05, 0.90],
    ])
    means_true = np.array([
        [0.0, 0.0, 0.0],
        [4.0, 4.0, 4.0],
        [-3.0, 3.0, -3.0],
    ])
    covars_true = np.array([np.eye(3) * 0.5 for _ in range(3)])

    states = np.zeros(n_bars, dtype=np.int64)
    states[0] = 0
    for t in range(1, n_bars):
        states[t] = rng.choice(3, p=transmat_true[states[t - 1]])

    X = np.zeros((n_bars, 3))
    for t in range(n_bars):
        X[t] = rng.multivariate_normal(means_true[states[t]], covars_true[states[t]])

    return X, states, transmat_true, means_true, covars_true


# ============================================================
# Tests
# ============================================================

class TestForwardBackwardCore:
    """Test 1+2+3 forward + backward + smoother core algorithms."""

    def test_1_forward_algorithm_synthetic_2state(self):
        """Forward algorithm produces log_alpha shape correcto + log_likelihood finite."""
        X, _, transmat, means, covars = _generate_2state_sequence(n_bars=200, seed=42)
        startprob = np.array([0.5, 0.5])
        log_emissions = _gaussian_log_emissions_full(X, means, covars)
        log_alpha, log_likelihood = _forward_log(log_emissions, np.log(transmat), np.log(startprob))

        assert log_alpha.shape == (200, 2), f"log_alpha shape {log_alpha.shape} != (200, 2)"
        assert np.isfinite(log_likelihood), "log_likelihood NOT finite"
        assert log_likelihood < 0, f"log_likelihood {log_likelihood} should be negative"

    def test_2_backward_algorithm_synthetic_2state(self):
        """Backward algorithm produces log_beta shape correcto + log_beta[N-1] = 0."""
        X, _, transmat, means, covars = _generate_2state_sequence(n_bars=200, seed=42)
        log_emissions = _gaussian_log_emissions_full(X, means, covars)
        log_beta = _backward_log(log_emissions, np.log(transmat))

        assert log_beta.shape == (200, 2)
        assert np.allclose(log_beta[-1, :], 0.0), f"log_beta[N-1] = {log_beta[-1]} should be all zeros"
        assert np.all(np.isfinite(log_beta))

    def test_3_forward_backward_smoother_consistency(self):
        """log_gamma rows exp sum to 1.0 (probabilities normalized) cross-N timesteps."""
        X, _, transmat, means, covars = _generate_2state_sequence(n_bars=200, seed=42)
        startprob = np.array([0.5, 0.5])
        log_emissions = _gaussian_log_emissions_full(X, means, covars)
        log_alpha, log_likelihood = _forward_log(log_emissions, np.log(transmat), np.log(startprob))
        log_beta = _backward_log(log_emissions, np.log(transmat))
        log_gamma, sum_xi = _smoother_gamma_sumxi(
            log_alpha, log_beta, log_emissions, np.log(transmat), log_likelihood)

        gamma = np.exp(log_gamma)
        row_sums = gamma.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6), \
            f"log_gamma rows sum to {row_sums} not 1.0 (max diff: {np.abs(row_sums - 1.0).max()})"


class TestBaumWelchEM:
    """Test 4+5+9 Baum-Welch EM convergence + n_init random restarts."""

    def test_4_baum_welch_convergence_2state(self):
        """Baum-Welch fits 2-state synthetic + converges + recovers approximate transmat + means."""
        X, _, transmat_true, means_true, _ = _generate_2state_sequence(n_bars=1000, seed=42)
        hmm = GaussianHMM(n_components=2, n_iter=200, tol=1e-4,
                          random_state=42, reg_covar=1e-3, n_init=3)
        hmm.fit(X)

        assert hmm.converged_, f"NOT converged after {hmm.n_iter_} iterations"
        # Recovered means should be close to true means (modulo cluster permutation)
        # Match by closest mean
        recovered = hmm.means_
        distances = np.linalg.norm(recovered[:, None] - means_true[None, :], axis=2)
        # Each true mean has at least one recovered close (distance < 1.5)
        for i in range(2):
            min_dist = distances[:, i].min()
            assert min_dist < 1.5, f"True mean {means_true[i]} no close recovered (min dist {min_dist:.3f})"

    def test_5_baum_welch_convergence_3state(self):
        """Baum-Welch fits 3-state synthetic + converges."""
        X, _, _, means_true, _ = _generate_3state_sequence(n_bars=1000, seed=42)
        hmm = GaussianHMM(n_components=3, n_iter=300, tol=1e-4,
                          random_state=42, reg_covar=1e-3, n_init=5)
        hmm.fit(X)
        assert hmm.converged_, f"NOT converged after {hmm.n_iter_} iterations"

        recovered = hmm.means_
        distances = np.linalg.norm(recovered[:, None] - means_true[None, :], axis=2)
        for i in range(3):
            min_dist = distances[:, i].min()
            assert min_dist < 2.0, f"True mean {means_true[i]} no close recovered (min dist {min_dist:.3f})"

    def test_9_n_init_random_starts(self):
        """fit con n_init=5 selects best log_likelihood vs n_init=1 single."""
        X, _, _, _, _ = _generate_2state_sequence(n_bars=500, seed=42)

        hmm_single = GaussianHMM(n_components=2, n_iter=100, random_state=1, n_init=1)
        hmm_single.fit(X)
        ll_single = hmm_single.score(X)

        hmm_multi = GaussianHMM(n_components=2, n_iter=100, random_state=1, n_init=5)
        hmm_multi.fit(X)
        ll_multi = hmm_multi.score(X)

        # n_init=5 selects best so log_likelihood should be >= n_init=1
        assert ll_multi >= ll_single - 1e-6, \
            f"n_init=5 ll {ll_multi:.4f} < n_init=1 ll {ll_single:.4f}"


class TestEmissionsBIC:
    """Test 6+7 Gaussian emissions correctness + BIC formula."""

    def test_6_gaussian_log_emissions_consistency_with_scipy(self):
        """Custom _gaussian_log_emissions_full matches scipy multivariate_normal.logpdf."""
        from scipy.stats import multivariate_normal as mvn

        rng = np.random.default_rng(42)
        N, D, K = 50, 3, 2
        X = rng.standard_normal((N, D))
        means = rng.standard_normal((K, D))
        covars = np.empty((K, D, D))
        for k in range(K):
            A = rng.standard_normal((D, D))
            covars[k] = A @ A.T + 0.1 * np.eye(D)

        log_emissions = _gaussian_log_emissions_full(X, means, covars)

        for k in range(K):
            ref = mvn.logpdf(X, mean=means[k], cov=covars[k])
            assert np.allclose(log_emissions[:, k], ref, atol=1e-8), \
                f"k={k} max diff {np.abs(log_emissions[:, k] - ref).max():.2e} vs scipy"

    def test_7_bic_computation_correctness(self):
        """BIC formula manual computation matches implementation."""
        X, _, _, _, _ = _generate_2state_sequence(n_bars=500, seed=42)
        hmm = GaussianHMM(n_components=3, n_iter=50, random_state=42, n_init=2, reg_covar=1e-3)
        hmm.fit(X)
        ll = hmm.score(X)
        K, D = 3, 2
        N = X.shape[0]
        n_params_expected = (K - 1) + K * (K - 1) + K * D + K * (D * (D + 1) // 2)
        # = 2 + 6 + 6 + 9 = 23
        bic_expected = -2.0 * ll + n_params_expected * np.log(N)
        bic_actual = hmm.bic(X)
        assert np.isclose(bic_actual, bic_expected, atol=1e-6), \
            f"BIC actual {bic_actual:.4f} != expected {bic_expected:.4f}"


class TestPredictAPI:
    """Test 8+10+14 predict / predict_proba / score / forward_step API."""

    def test_8_predict_predict_proba_consistency(self):
        """predict argmax matches argmax of predict_proba."""
        X, _, _, _, _ = _generate_2state_sequence(n_bars=500, seed=42)
        hmm = GaussianHMM(n_components=2, n_iter=100, random_state=42, n_init=3, reg_covar=1e-3)
        hmm.fit(X)
        labels = hmm.predict(X)
        proba = hmm.predict_proba(X)
        labels_from_proba = np.argmax(proba, axis=1)
        assert np.array_equal(labels, labels_from_proba)
        # Each row sums to 1
        row_sums = proba.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)

    def test_10_forward_step_online_vs_batch(self):
        """forward_step iterative cross-bars produces log_alpha matching batch _forward_log."""
        X, _, _, _, _ = _generate_2state_sequence(n_bars=200, seed=42)
        hmm = GaussianHMM(n_components=2, n_iter=100, random_state=42, n_init=3, reg_covar=1e-3)
        hmm.fit(X)

        # Batch
        log_emissions = _gaussian_log_emissions_full(X, hmm.means_, hmm.covars_)
        log_transmat = np.log(hmm.transmat_ + 1e-300)
        log_startprob = np.log(hmm.startprob_ + 1e-300)
        log_alpha_batch, _ = _forward_log(log_emissions, log_transmat, log_startprob)

        # Online iterative
        log_alpha_online = np.empty_like(log_alpha_batch)
        log_alpha_online[0] = hmm.forward_step(X[0])
        for t in range(1, X.shape[0]):
            log_alpha_online[t] = hmm.forward_step(X[t], log_alpha_prev=log_alpha_online[t - 1])

        assert np.allclose(log_alpha_batch, log_alpha_online, atol=1e-8), \
            f"batch vs online max diff {np.abs(log_alpha_batch - log_alpha_online).max():.2e}"

    def test_14_score_log_likelihood_consistency(self):
        """score(X) matches log_likelihood from forward algorithm directly."""
        X, _, _, _, _ = _generate_2state_sequence(n_bars=300, seed=42)
        hmm = GaussianHMM(n_components=2, n_iter=100, random_state=42, n_init=3, reg_covar=1e-3)
        hmm.fit(X)
        score = hmm.score(X)

        log_emissions = _gaussian_log_emissions_full(X, hmm.means_, hmm.covars_)
        log_transmat = np.log(hmm.transmat_ + 1e-300)
        log_startprob = np.log(hmm.startprob_ + 1e-300)
        _, ll_direct = _forward_log(log_emissions, log_transmat, log_startprob)

        assert np.isclose(score, ll_direct, atol=1e-8), \
            f"score {score:.6f} vs direct ll {ll_direct:.6f}"


class TestStability:
    """Test 11+12 numerical stability + edge cases."""

    def test_11_logsumexp_numerical_stability(self):
        """_logsumexp_1d con extreme values NO NaN/Inf."""
        # Very large values
        arr_large = np.array([1000.0, 1001.0, 999.5])
        result = _logsumexp_1d(arr_large)
        assert np.isfinite(result)
        # Reference: max + log(exp(0) + exp(1) + exp(-0.5)) ≈ 1001 + log(1+e+e^-0.5)
        expected = 1001.0 + np.log(np.exp(0) + np.exp(-1) + np.exp(-1.5))
        assert np.isclose(result, expected, atol=1e-8)

        # Very negative values
        arr_neg = np.array([-1000.0, -1001.0, -999.5])
        result = _logsumexp_1d(arr_neg)
        assert np.isfinite(result)

        # All -inf
        arr_neginf = np.array([-np.inf, -np.inf, -np.inf])
        result = _logsumexp_1d(arr_neginf)
        assert result == -np.inf

    def test_12_logaddexp_consistency(self):
        """_logaddexp matches np.logaddexp."""
        for a, b in [(0.0, 0.0), (1.0, 2.0), (-100.0, 100.0), (-np.inf, 5.0), (5.0, -np.inf)]:
            result = _logaddexp(a, b)
            ref = np.logaddexp(a, b)
            if np.isinf(ref):
                assert np.isinf(result) and np.sign(result) == np.sign(ref)
            else:
                assert np.isclose(result, ref, atol=1e-10), f"({a}, {b}): got {result}, ref {ref}"


class TestSerialization:
    """Test 13 joblib serialize + deserialize roundtrip."""

    def test_13_joblib_serialize_roundtrip(self):
        """Fit + dump/load + predict produces identical results."""
        import joblib
        import tempfile

        X, _, _, _, _ = _generate_2state_sequence(n_bars=300, seed=42)
        hmm = GaussianHMM(n_components=2, n_iter=100, random_state=42, n_init=3, reg_covar=1e-3)
        hmm.fit(X)

        labels_orig = hmm.predict(X)
        proba_orig = hmm.predict_proba(X)
        ll_orig = hmm.score(X)

        with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as f:
            path = f.name
        try:
            joblib.dump(hmm.get_params(), path)
            params_loaded = joblib.load(path)
            hmm_restored = GaussianHMM(n_components=2)
            hmm_restored.set_params(params_loaded)

            labels_restored = hmm_restored.predict(X)
            proba_restored = hmm_restored.predict_proba(X)
            ll_restored = hmm_restored.score(X)

            assert np.array_equal(labels_orig, labels_restored)
            assert np.allclose(proba_orig, proba_restored, atol=1e-12)
            assert np.isclose(ll_orig, ll_restored, atol=1e-12)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestRealData:
    """Test 15 fit + predict on real BTC features (Hurst+Z_ATR+ER subset)."""

    def test_15_fit_predict_real_btc_features_subset(self):
        """Fit GaussianHMM on real BTC features Hurst+Z_ATR+ER subset (1000 bars). NO crash + NO NaN."""
        import pandas as pd

        cache_path = os.path.join(_ROOT, 'data_cache', 'BTCUSDT_1h.parquet')
        if not os.path.exists(cache_path):
            pytest.skip(f"BTC parquet not available at {cache_path}")

        from regime_features import compute_regime_features
        df = pd.read_parquet(cache_path)
        if 'timestamp_ms' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        # Take first 2000 bars for speed
        df_subset = df.iloc[:3000]
        features, valid_mask = compute_regime_features(df_subset, lookback=100)
        valid_features = features[valid_mask]
        # Take first 1000 valid
        X = valid_features[:1000]

        hmm = GaussianHMM(n_components=3, n_iter=100, random_state=42, n_init=3, reg_covar=1e-3)
        hmm.fit(X)

        assert hmm.transmat_ is not None
        assert hmm.means_.shape == (3, 3), f"means_ shape {hmm.means_.shape} != (3, 3)"
        assert np.all(np.isfinite(hmm.means_)), "means_ contains NaN/Inf"
        assert np.all(np.isfinite(hmm.covars_)), "covars_ contains NaN/Inf"
        assert np.all(np.isfinite(hmm.transmat_)), "transmat_ contains NaN/Inf"

        # transmat_ row-stochastic
        row_sums = hmm.transmat_.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)

        # predict_proba sums to 1
        proba = hmm.predict_proba(X)
        assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-6)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
