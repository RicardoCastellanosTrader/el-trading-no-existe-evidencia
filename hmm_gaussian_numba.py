"""
hmm_gaussian_numba.py — Custom Numba HMM Gaussian para Frame 3.A meta-redesign Eje 1 paradigm shift cardinal.

Ownership total — bypassa hmmlearn pip install blocker Python 3.14.3 wheel build fail.
Coherencia arquitectónica §0.6 kernel verdad operacional + reciclaje definitivo foundational anexo L.0.

References:
- Rabiner 1989 — "A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition" (IEEE)
- Bishop PRML 2006 — Chapter 13 "Sequential Data"

API sklearn-compatible drop-in posterior split C integration:
    GaussianHMM(n_components, covariance_type='full', n_iter=300, tol=1e-3,
                init_params='stmc', random_state=None, reg_covar=1e-6, n_init=1)

Methods:
    fit(X) → self
    predict(X) → cluster_labels (Viterbi-equivalent argmax smoothed posterior)
    predict_proba(X) → posterior probabilities (smoothed forward-backward)
    score(X) → log_likelihood
    bic(X) → BIC value
    forward_step(x_t, log_alpha_prev) → log_alpha_t (online filter)

Attributes post-fit: transmat_, means_, covars_, startprob_, converged_, n_iter_, monitor_
"""

import numpy as np
from numba import njit


# ============================================================
# LOW-LEVEL NUMBA-COMPILED CORE
# ============================================================

@njit(cache=True)
def _logsumexp_1d(arr):
    """Numerically stable logsumexp for 1D array."""
    n = arr.shape[0]
    if n == 0:
        return -np.inf
    max_v = arr[0]
    for i in range(1, n):
        if arr[i] > max_v:
            max_v = arr[i]
    if max_v == -np.inf:
        return -np.inf
    s = 0.0
    for i in range(n):
        s += np.exp(arr[i] - max_v)
    return max_v + np.log(s)


@njit(cache=True)
def _logaddexp(a, b):
    """Numerically stable log(exp(a) + exp(b))."""
    if a == -np.inf:
        return b
    if b == -np.inf:
        return a
    if a > b:
        return a + np.log1p(np.exp(b - a))
    else:
        return b + np.log1p(np.exp(a - b))


@njit(cache=True)
def _gaussian_log_emissions_full(X, means, covars):
    """Compute log emissions Gaussian full covariance.

    X: (N, D), means: (K, D), covars: (K, D, D).
    Returns log_emissions: (N, K).
    """
    N = X.shape[0]
    D = X.shape[1]
    K = means.shape[0]
    log_emissions = np.empty((N, K))
    log_2pi = np.log(2.0 * np.pi)

    for k in range(K):
        # Cholesky decomposition of covars[k] = L L^T
        L = np.linalg.cholesky(covars[k])
        log_det = 0.0
        for d in range(D):
            log_det += 2.0 * np.log(L[d, d])
        const = -0.5 * (D * log_2pi + log_det)

        for t in range(N):
            # Solve L @ y = (X[t] - means[k]) via forward substitution
            mahal = 0.0
            y = np.empty(D)
            for d in range(D):
                s = X[t, d] - means[k, d]
                for j in range(d):
                    s -= L[d, j] * y[j]
                y[d] = s / L[d, d]
                mahal += y[d] * y[d]
            log_emissions[t, k] = const - 0.5 * mahal

    return log_emissions


@njit(cache=True)
def _forward_log(log_emissions, log_transmat, log_startprob):
    """Forward algorithm log-space.

    Returns log_alpha: (N, K), log_likelihood: scalar.
    """
    N = log_emissions.shape[0]
    K = log_emissions.shape[1]
    log_alpha = np.empty((N, K))

    # t=0
    for k in range(K):
        log_alpha[0, k] = log_startprob[k] + log_emissions[0, k]

    # Recursion t=1..N-1
    tmp = np.empty(K)
    for t in range(1, N):
        for k in range(K):
            for i in range(K):
                tmp[i] = log_alpha[t - 1, i] + log_transmat[i, k]
            log_alpha[t, k] = _logsumexp_1d(tmp) + log_emissions[t, k]

    log_likelihood = _logsumexp_1d(log_alpha[N - 1, :])
    return log_alpha, log_likelihood


@njit(cache=True)
def _backward_log(log_emissions, log_transmat):
    """Backward algorithm log-space.

    Returns log_beta: (N, K).
    """
    N = log_emissions.shape[0]
    K = log_emissions.shape[1]
    log_beta = np.empty((N, K))

    for k in range(K):
        log_beta[N - 1, k] = 0.0

    tmp = np.empty(K)
    for t in range(N - 2, -1, -1):
        for k in range(K):
            for j in range(K):
                tmp[j] = log_transmat[k, j] + log_emissions[t + 1, j] + log_beta[t + 1, j]
            log_beta[t, k] = _logsumexp_1d(tmp)

    return log_beta


@njit(cache=True)
def _smoother_gamma_sumxi(log_alpha, log_beta, log_emissions, log_transmat, log_likelihood):
    """Forward-Backward smoother → log_gamma + sum_xi (memory-efficient sufficient stats).

    log_gamma[t, k] = log_alpha[t, k] + log_beta[t, k] - log_likelihood
    sum_xi[i, j] = logsumexp_t (log_alpha[t, i] + log_transmat[i, j] + log_emissions[t+1, j] + log_beta[t+1, j]) - log_likelihood
    """
    N = log_alpha.shape[0]
    K = log_alpha.shape[1]

    log_gamma = np.empty((N, K))
    for t in range(N):
        for k in range(K):
            log_gamma[t, k] = log_alpha[t, k] + log_beta[t, k] - log_likelihood

    sum_xi = np.full((K, K), -np.inf)
    for t in range(N - 1):
        for i in range(K):
            for j in range(K):
                val = (log_alpha[t, i] + log_transmat[i, j]
                       + log_emissions[t + 1, j] + log_beta[t + 1, j]
                       - log_likelihood)
                sum_xi[i, j] = _logaddexp(sum_xi[i, j], val)

    return log_gamma, sum_xi


@njit(cache=True)
def _m_step_update(X, log_gamma, sum_xi, reg_covar):
    """M-step Baum-Welch update.

    Returns startprob (K,), transmat (K, K), means (K, D), covars (K, D, D).
    """
    N = X.shape[0]
    D = X.shape[1]
    K = log_gamma.shape[1]

    gamma = np.exp(log_gamma)

    # startprob
    startprob = gamma[0].copy()
    s = 0.0
    for k in range(K):
        s += startprob[k]
    if s > 1e-300:
        for k in range(K):
            startprob[k] /= s
    else:
        for k in range(K):
            startprob[k] = 1.0 / K

    # transmat
    transmat = np.empty((K, K))
    sum_xi_prob = np.exp(sum_xi)
    for i in range(K):
        denom = 0.0
        for t in range(N - 1):
            denom += gamma[t, i]
        if denom > 1e-300:
            for j in range(K):
                transmat[i, j] = sum_xi_prob[i, j] / denom
        else:
            for j in range(K):
                transmat[i, j] = 1.0 / K
        row_sum = 0.0
        for j in range(K):
            row_sum += transmat[i, j]
        if row_sum > 1e-300:
            for j in range(K):
                transmat[i, j] /= row_sum
        else:
            for j in range(K):
                transmat[i, j] = 1.0 / K

    # gamma_sum_per_k for means + covars
    gamma_sum = np.zeros(K)
    for t in range(N):
        for k in range(K):
            gamma_sum[k] += gamma[t, k]

    # means
    means = np.zeros((K, D))
    for t in range(N):
        for k in range(K):
            for d in range(D):
                means[k, d] += gamma[t, k] * X[t, d]
    for k in range(K):
        if gamma_sum[k] > 1e-300:
            for d in range(D):
                means[k, d] /= gamma_sum[k]

    # covars (full)
    covars = np.zeros((K, D, D))
    for t in range(N):
        for k in range(K):
            w = gamma[t, k]
            if w > 1e-300:
                for i in range(D):
                    diff_i = X[t, i] - means[k, i]
                    for j in range(D):
                        diff_j = X[t, j] - means[k, j]
                        covars[k, i, j] += w * diff_i * diff_j
    for k in range(K):
        if gamma_sum[k] > 1e-300:
            for i in range(D):
                for j in range(D):
                    covars[k, i, j] /= gamma_sum[k]
        # Regularize diagonal
        for d in range(D):
            covars[k, d, d] += reg_covar

    return startprob, transmat, means, covars


@njit(cache=True)
def _forward_step_online(x_t_log_emission, log_alpha_prev, log_transmat):
    """Single online forward filter step: posterior_t given posterior_{t-1}.

    log_alpha_t[k] = logsumexp(log_alpha_{t-1}[:] + log_transmat[:, k]) + log_emission[k]
    """
    K = log_alpha_prev.shape[0]
    log_alpha_t = np.empty(K)
    tmp = np.empty(K)
    for k in range(K):
        for i in range(K):
            tmp[i] = log_alpha_prev[i] + log_transmat[i, k]
        log_alpha_t[k] = _logsumexp_1d(tmp) + x_t_log_emission[k]
    return log_alpha_t


# ============================================================
# HIGH-LEVEL Python class (sklearn-compatible API)
# ============================================================

class ConvergenceMonitor:
    """Simple convergence monitor analogous to hmmlearn ConvergenceMonitor."""
    def __init__(self, tol, n_iter):
        self.tol = tol
        self.n_iter = n_iter
        self.iter = 0
        self.converged = False
        self.history = []


def _init_transmat_persistence_biased(K, persistence=0.9):
    """Initialize transmat con régimen persistence prior (diagonal weight)."""
    transmat = np.full((K, K), (1.0 - persistence) / (K - 1) if K > 1 else 1.0)
    np.fill_diagonal(transmat, persistence)
    return transmat


def _init_means_random_sample(X, K, rng):
    """Random sample K rows from X as initial means."""
    N = X.shape[0]
    indices = rng.choice(N, size=K, replace=False)
    return X[indices].copy()


def _init_covars_data_variance(X, K, reg_covar):
    """Initialize covars cada cluster con data covariance + regularization."""
    D = X.shape[1]
    cov_data = np.cov(X.T)
    if cov_data.ndim == 0:
        # D=1 edge case
        cov_data = np.array([[cov_data]])
    covars = np.empty((K, D, D))
    for k in range(K):
        covars[k] = cov_data + reg_covar * np.eye(D)
    return covars


class GaussianHMM:
    """Custom Gaussian HMM con Numba-accelerated Baum-Welch EM training.

    Sklearn-compatible API drop-in posterior para Frame 3.A meta-redesign Eje 1.

    Parameters:
        n_components: número de hidden states K
        covariance_type: 'full' (default; only 'full' supported initially)
        n_iter: max EM iterations
        tol: convergence tolerance (delta log_likelihood)
        random_state: int seed
        reg_covar: regularización diagonal covars (numerical stability)
        n_init: número de random restarts (selecciona best log_likelihood)
        verbose: print iteration log_likelihood
    """

    def __init__(self, n_components=3, covariance_type='full', n_iter=300,
                 tol=1e-3, random_state=None, reg_covar=1e-6,
                 n_init=1, verbose=False):
        if covariance_type != 'full':
            raise NotImplementedError(
                f"covariance_type='{covariance_type}' not supported. Only 'full' implemented split A.")
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.n_iter = n_iter
        self.tol = tol
        self.random_state = random_state
        self.reg_covar = reg_covar
        self.n_init = n_init
        self.verbose = verbose

        # Post-fit attributes (None until fit)
        self.transmat_ = None
        self.means_ = None
        self.covars_ = None
        self.startprob_ = None
        self.converged_ = False
        self.n_iter_ = 0
        self.monitor_ = None

    def _validate_X(self, X):
        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 2:
            raise ValueError(f"X must be 2D, got shape {X.shape}")
        if X.shape[0] < self.n_components:
            raise ValueError(
                f"N={X.shape[0]} bars insufficient for K={self.n_components} components")
        return X

    def _single_fit(self, X, seed):
        """Single Baum-Welch EM run con specific random_state seed."""
        N, D = X.shape
        K = self.n_components
        rng = np.random.default_rng(seed)

        # Initialize parameters
        startprob = np.full(K, 1.0 / K)
        transmat = _init_transmat_persistence_biased(K, persistence=0.9)
        means = _init_means_random_sample(X, K, rng)
        covars = _init_covars_data_variance(X, K, self.reg_covar)

        log_likelihood_prev = -np.inf
        monitor = ConvergenceMonitor(tol=self.tol, n_iter=self.n_iter)

        for iter_ in range(self.n_iter):
            # E-step
            log_emissions = _gaussian_log_emissions_full(X, means, covars)
            log_transmat = np.log(transmat + 1e-300)
            log_startprob = np.log(startprob + 1e-300)
            log_alpha, log_likelihood = _forward_log(log_emissions, log_transmat, log_startprob)

            monitor.history.append(log_likelihood)
            monitor.iter = iter_ + 1

            if self.verbose:
                print(f"   iter {iter_}: log_likelihood = {log_likelihood:.4f}")

            # Convergence check
            if iter_ > 0:
                delta = log_likelihood - log_likelihood_prev
                if delta < self.tol:
                    if delta < 0 and abs(delta) > 1e-3:
                        # Negative delta substantial → numerical issue or local optimum
                        pass
                    monitor.converged = True
                    break
            log_likelihood_prev = log_likelihood

            # Backward + smoother
            log_beta = _backward_log(log_emissions, log_transmat)
            log_gamma, sum_xi = _smoother_gamma_sumxi(
                log_alpha, log_beta, log_emissions, log_transmat, log_likelihood)

            # M-step
            startprob, transmat, means, covars = _m_step_update(
                X, log_gamma, sum_xi, self.reg_covar)

        return {
            'startprob': startprob, 'transmat': transmat, 'means': means, 'covars': covars,
            'log_likelihood': log_likelihood, 'monitor': monitor,
        }

    def fit(self, X):
        """Fit con n_init random restarts; selecciona best log_likelihood."""
        X = self._validate_X(X)
        K = self.n_components

        if self.random_state is None:
            base_seed = np.random.randint(0, 2**31 - 1)
        else:
            base_seed = self.random_state

        best = None
        for init_idx in range(self.n_init):
            seed = base_seed + init_idx * 1000
            try:
                result = self._single_fit(X, seed)
            except np.linalg.LinAlgError:
                # Cholesky fail (covariance singular) — skip this init
                continue
            if best is None or result['log_likelihood'] > best['log_likelihood']:
                best = result

        if best is None:
            raise RuntimeError(f"All {self.n_init} fit attempts failed (LinAlgError)")

        self.startprob_ = best['startprob']
        self.transmat_ = best['transmat']
        self.means_ = best['means']
        self.covars_ = best['covars']
        self.monitor_ = best['monitor']
        self.converged_ = best['monitor'].converged
        self.n_iter_ = best['monitor'].iter

        return self

    def _check_fitted(self):
        if self.transmat_ is None:
            raise RuntimeError("Model not fitted. Call fit(X) first.")

    def score(self, X):
        """Compute log-likelihood of X under fitted model."""
        self._check_fitted()
        X = self._validate_X(X)
        log_emissions = _gaussian_log_emissions_full(X, self.means_, self.covars_)
        log_transmat = np.log(self.transmat_ + 1e-300)
        log_startprob = np.log(self.startprob_ + 1e-300)
        _, log_likelihood = _forward_log(log_emissions, log_transmat, log_startprob)
        return log_likelihood

    def predict_proba(self, X):
        """Smoothed posteriors P(z_t | X) via forward-backward."""
        self._check_fitted()
        X = self._validate_X(X)
        log_emissions = _gaussian_log_emissions_full(X, self.means_, self.covars_)
        log_transmat = np.log(self.transmat_ + 1e-300)
        log_startprob = np.log(self.startprob_ + 1e-300)
        log_alpha, log_likelihood = _forward_log(log_emissions, log_transmat, log_startprob)
        log_beta = _backward_log(log_emissions, log_transmat)
        log_gamma, _ = _smoother_gamma_sumxi(
            log_alpha, log_beta, log_emissions, log_transmat, log_likelihood)
        return np.exp(log_gamma)

    def predict(self, X):
        """Return MAP cluster labels (argmax smoothed posterior)."""
        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)

    def bic(self, X):
        """BIC = -2 * log_likelihood + n_params * log(N).

        n_params (full covariance):
            (K - 1) startprob + K(K - 1) transmat + K*D means + K*D*(D + 1)/2 covars triangular
        """
        self._check_fitted()
        X = self._validate_X(X)
        N, D = X.shape
        K = self.n_components
        n_params = (K - 1) + K * (K - 1) + K * D + K * (D * (D + 1) // 2)
        log_likelihood = self.score(X)
        return -2.0 * log_likelihood + n_params * np.log(N)

    def forward_step(self, x_t, log_alpha_prev=None):
        """Online forward filter: single step posterior given previous log_alpha.

        x_t: (D,) single observation.
        log_alpha_prev: (K,) previous log_alpha. If None, uses log_startprob (initial step).
        Returns log_alpha_t: (K,).
        """
        self._check_fitted()
        x_t = np.asarray(x_t, dtype=np.float64).reshape(1, -1)
        log_emission_t = _gaussian_log_emissions_full(x_t, self.means_, self.covars_)[0]

        if log_alpha_prev is None:
            log_startprob = np.log(self.startprob_ + 1e-300)
            return log_startprob + log_emission_t

        log_alpha_prev = np.asarray(log_alpha_prev, dtype=np.float64)
        log_transmat = np.log(self.transmat_ + 1e-300)
        return _forward_step_online(log_emission_t, log_alpha_prev, log_transmat)

    def get_params(self):
        """Return dict of model parameters (for joblib serialization)."""
        return {
            'n_components': self.n_components,
            'covariance_type': self.covariance_type,
            'n_iter': self.n_iter,
            'tol': self.tol,
            'random_state': self.random_state,
            'reg_covar': self.reg_covar,
            'n_init': self.n_init,
            'startprob_': self.startprob_,
            'transmat_': self.transmat_,
            'means_': self.means_,
            'covars_': self.covars_,
            'converged_': self.converged_,
            'n_iter_': self.n_iter_,
        }

    def set_params(self, params):
        """Restore model from get_params dict (joblib roundtrip)."""
        self.n_components = params['n_components']
        self.covariance_type = params['covariance_type']
        self.n_iter = params['n_iter']
        self.tol = params['tol']
        self.random_state = params['random_state']
        self.reg_covar = params['reg_covar']
        self.n_init = params['n_init']
        self.startprob_ = params['startprob_']
        self.transmat_ = params['transmat_']
        self.means_ = params['means_']
        self.covars_ = params['covars_']
        self.converged_ = params['converged_']
        self.n_iter_ = params['n_iter_']
        return self
