"""
Tests A12 (LL1) — parity MAs lab_lite_zonas_v5e vs lab_historico_numba_v8_3.

Post-refactor 2026-04-23: lab_lite importa las 16 MAs desde
lab_historico. Tests verifican:
  1. Las 16 MAs son literal mismas funciones (`is` True).
  2. calc_wma fue eliminado de lab_lite (era único local).
  3. Dispatcher de lab_lite (L385-400) sigue operativo con las
     MAs importadas.
  4. Output numérico sobre serie sintética es idéntico (trivial
     dado que son same objects).

Standalone. Run: python tests/test_a12_ma_parity.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
import lab_lite_zonas_v5e as lite
import lab_historico_numba_v8_3 as lab

MA_NAMES = [
    'calc_ema', 'calc_sma', 'calc_hma', 'calc_alma', 'calc_zlema',
    'calc_kama', 'calc_dema', 'calc_tema', 'calc_mcginley',
    'calc_vidya', 'calc_frama', 'calc_t3', 'calc_ssmoother',
    'calc_vwma', 'calc_tenkan', 'calc_jma',
]


def test_1_ma_objects_identical():
    """Las 16 MAs en lab_lite son literal mismas funciones que lab_historico."""
    for name in MA_NAMES:
        a = getattr(lite, name)
        b = getattr(lab, name)
        assert a is b, f"{name}: lite object {id(a)} != lab object {id(b)}"
    print(f"  test_1 PASS: 16/16 MA functions are identical (is True)")


def test_2_calc_wma_removed_from_lite():
    """calc_wma era local único de lab_lite (usado solo por calc_hma local).
    Post-refactor debe estar eliminado ya que lab_historico.calc_hma tiene
    wma interno."""
    assert not hasattr(lite, 'calc_wma'), "calc_wma should be removed from lab_lite"
    # Y lab_historico tampoco lo expone públicamente (wma es closure en calc_hma)
    assert not hasattr(lab, 'calc_wma'), "lab_historico also should not expose calc_wma"
    print(f"  test_2 PASS: calc_wma removed from lab_lite (was only caller)")


def test_3_dispatcher_returns_numeric():
    """El dispatcher interno (L385-400) delega a calc_X. Verificar que
    sigue funcionando con funciones importadas (no quedó referencia dangling)."""
    np.random.seed(42)
    N = 200
    close = np.cumsum(np.random.randn(N)) + 100
    high = close + np.random.rand(N) * 0.5
    low = close - np.random.rand(N) * 0.5
    volume = np.random.rand(N) * 1000 + 100
    # Dispatcher real: calc_ma(close, high, low, volume, ma_type, period, p1, p2)
    ema = lite.calc_ma(close, high, low, volume, 0, 14, 0.85, 6.0)
    assert ema is not None and np.any(np.isfinite(ema)), "EMA dispatch failed"
    jma = lite.calc_ma(close, high, low, volume, 15, 14, 0.0, 2.0)
    assert jma is not None and np.any(np.isfinite(jma)), "JMA dispatch failed"
    vwma = lite.calc_ma(close, high, low, volume, 13, 14, 0.0, 0.0)
    assert vwma is not None and np.any(np.isfinite(vwma)), "VWMA dispatch failed"
    frama = lite.calc_ma(close, high, low, volume, 10, 14, 0.0, 0.0)
    assert frama is not None and np.any(np.isfinite(frama)), "FRAMA dispatch failed"
    print(f"  test_3 PASS: dispatcher responds to MA types 0,10,13,15 with finite output")


def test_4_numerical_equivalence_sanity():
    """Sanity: porque lite.calc_X IS lab.calc_X, output debe ser
    literalmente idéntico. Test trivial pero útil como guard futuro
    si alguien re-introduce definiciones locales."""
    np.random.seed(123)
    N = 500
    close = np.cumsum(np.random.randn(N)) + 100
    for name in MA_NAMES:
        if name in ('calc_frama', 'calc_tenkan', 'calc_vwma'):
            continue  # need extra args
        fn = getattr(lite, name)
        a = fn(close, 14)
        b = getattr(lab, name)(close, 14)
        assert np.array_equal(a, b, equal_nan=True), f"{name} output differs"
    print(f"  test_4 PASS: numerical equivalence trivially holds (same obj)")


def _run_all():
    print("=" * 68)
    print("A12 (LL1) MA parity test suite")
    print("=" * 68)
    tests = [
        test_1_ma_objects_identical,
        test_2_calc_wma_removed_from_lite,
        test_3_dispatcher_returns_numeric,
        test_4_numerical_equivalence_sanity,
    ]
    n_pass = 0
    n_fail = 0
    for t in tests:
        try:
            t()
            n_pass += 1
        except AssertionError as e:
            print(f"  {t.__name__} FAIL: {e}")
            n_fail += 1
        except Exception as e:
            print(f"  {t.__name__} ERROR: {type(e).__name__}: {e}")
            n_fail += 1
    print("=" * 68)
    print(f"Result: {n_pass}/{len(tests)} PASS, {n_fail} FAIL")
    print("=" * 68)
    return n_fail == 0


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)
