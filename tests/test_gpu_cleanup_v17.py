"""Tests mitigations GPU cleanup v17 post-DIAG.11 cross-2-crashes
TDR 0x116 STATUS_INSUFFICIENT_RESOURCES (2026-05-08 + 2026-05-10).

Cubre:
- T1: del + deallocations.clear() ejecuta sin error en clustered run_on_slice
- T2: API cuda.current_context().deallocations.clear() existe en Numba instalada
- T3: Fidelidad invariante — results bit-a-bit identical cross-invocations
- T4: GPU memory free estable cross-10-iterations cumulative (no degradación
      monotónica >10% que indicaría leak persistent post-mitigations)
"""
import gc
import numpy as np
import pytest

try:
    from numba import cuda
    cuda.current_context()
    _GPU_AVAILABLE = True
except Exception:
    _GPU_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _GPU_AVAILABLE, reason="Numba CUDA not available")


def _make_synthetic_data(n_bars=2000, seed=42):
    """Dataset sintético mínimo compatible con CUDASimulatorOptimized.upload_data."""
    rng = np.random.default_rng(seed)
    start = np.datetime64('2024-01-01T00', 'h')
    timestamps = start + np.arange(n_bars).astype('timedelta64[h]')
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n_bars)))
    high = close * (1.0 + np.abs(rng.normal(0, 0.005, n_bars)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.005, n_bars)))
    return {
        'close': close,
        'high': high,
        'low': low,
        'timestamps': timestamps,
        'zone_bull': rng.random(n_bars) > 0.7,
        'zone_bear': rng.random(n_bars) > 0.7,
        'filters_forming': rng.integers(0, 256, n_bars, dtype=np.uint32),
        'filters_resolved': rng.integers(0, 256, n_bars, dtype=np.uint32),
        'div_bits': rng.integers(0, 16, (n_bars, 8), dtype=np.uint8),
    }


def _run_clustered_smoke(sim, configs, data, n_clusters=2):
    """Smoke run clustered path con configs sintéticas + cluster_labels."""
    handle = sim.upload_data(data)
    n_bars = len(data['close'])
    cluster_labels = np.zeros(n_bars, dtype=np.int64)
    cluster_labels[n_bars // 2:] = 1
    return sim.run_on_slice(
        configs, handle, 100, n_bars - 100,
        sl_pct=0.03, sl_emergency_pct=0.05, ts_pct=0.005,
        cooldown_bars=2, commission_pct=0.001,
        cluster_labels=cluster_labels, n_clusters=n_clusters,
    )


def test_t1_clustered_path_runs_without_error():
    """T1: del explícito + deallocations.clear() ejecuta sin error en clustered path."""
    from lab_cuda import CUDASimulatorOptimized
    sim = CUDASimulatorOptimized()
    if not sim.gpu_available:
        pytest.skip("GPU not available")

    data = _make_synthetic_data(2000)
    configs = np.array([0, 1, 2, 100, 1000], dtype=np.uint32)

    results, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = \
        _run_clustered_smoke(sim, configs, data, n_clusters=2)

    assert results.shape == (5, 7)
    assert cl_pnl.shape == (5, 2)
    assert np.isfinite(results).all(), "results contains NaN/Inf post-cleanup"


def test_t2_deallocations_clear_api_exists():
    """T2: cuda.current_context().deallocations.clear() existe en Numba instalada."""
    ctx = cuda.current_context()
    assert hasattr(ctx, 'deallocations'), "ctx.deallocations missing"
    assert hasattr(ctx.deallocations, 'clear'), "ctx.deallocations.clear() missing"
    ctx.deallocations.clear()


def test_t3_fidelidad_invariante_post_cleanup():
    """T3: results bit-a-bit identical cross-invocations (Fidelidad cardinal).

    Cualquier diferencia → mitigations rompen el output del kernel → REGRESSION.
    """
    from lab_cuda import CUDASimulatorOptimized
    sim = CUDASimulatorOptimized()
    if not sim.gpu_available:
        pytest.skip("GPU not available")

    data = _make_synthetic_data(2000, seed=42)
    configs = np.array([42, 100, 1000, 5000], dtype=np.uint32)

    results1, cl_pnl1, _, _, _, _, _ = _run_clustered_smoke(sim, configs, data)
    results2, cl_pnl2, _, _, _, _, _ = _run_clustered_smoke(sim, configs, data)

    np.testing.assert_array_equal(
        results1, results2,
        err_msg="Fidelidad break: results differ between invocations post-cleanup")
    np.testing.assert_array_equal(
        cl_pnl1, cl_pnl2,
        err_msg="Fidelidad break: cl_pnl differs between invocations post-cleanup")


def test_t4_gpu_memory_stable_cross_10_iterations():
    """T4: GPU memory free no degrada monotónicamente >10% cross-10-iter.

    Pre-mitigations v17, cumulative ~3328 device array allocations dejaban
    pending dealloc queue creciente → STATUS_INSUFFICIENT_RESOURCES eventual.
    Post-mitigations, free debe permanecer dentro de ±10% del initial.
    """
    from lab_cuda import CUDASimulatorOptimized
    sim = CUDASimulatorOptimized()
    if not sim.gpu_available:
        pytest.skip("GPU not available")

    data = _make_synthetic_data(2000)
    configs = np.array([0, 1, 2, 100, 1000], dtype=np.uint32)

    free_history = []
    for _ in range(10):
        _run_clustered_smoke(sim, configs, data)
        gc.collect()
        cuda.current_context().deallocations.clear()
        free_history.append(cuda.current_context().get_memory_info().free)

    initial_free = free_history[0]
    final_free = free_history[-1]
    degradation = (initial_free - final_free) / initial_free
    assert degradation < 0.10, (
        f"GPU memory free degradó {degradation*100:.1f}% cross-10-iter "
        f"(initial={initial_free:,}, final={final_free:,}, "
        f"history={free_history})"
    )
