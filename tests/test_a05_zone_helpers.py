"""
Tests A05 S3 — zone_bull_mr + zone_bear_mr single source of truth.

Pre-fix: brain_engine recomputaba `fast < slow` inline en 6 sitios
dispersos; mean_reversion_features.calc_zones computaba arrays
independientemente → drift potencial silencioso.

Post-fix 2026-04-23: `zone_bull_mr(fast, slow)` + `zone_bear_mr(fast, slow)`
module-level en mean_reversion_features.py. calc_zones delega. brain
importa y reemplaza 6 inlines.

Standalone. Run: python tests/test_a05_zone_helpers.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
from mean_reversion_features import zone_bull_mr, zone_bear_mr, calc_zones


def test_1_scalar_basic():
    """Escalar fast<slow → zone_bull_mr True, fast>slow → zone_bear_mr True."""
    assert zone_bull_mr(1.0, 2.0) is True, "fast<slow should yield zone_bull"
    assert zone_bull_mr(2.0, 1.0) is False, "fast>slow should NOT yield zone_bull"
    assert zone_bull_mr(1.0, 1.0) is False, "fast==slow should NOT yield zone_bull (strict <)"
    assert zone_bear_mr(2.0, 1.0) is True
    assert zone_bear_mr(1.0, 2.0) is False
    assert zone_bear_mr(1.0, 1.0) is False
    print(f"  test_1 PASS: scalar bull/bear basic")


def test_2_scalar_nan_defensive():
    """NaN en input → False (never crash, never True)."""
    assert zone_bull_mr(float('nan'), 1.0) is False
    assert zone_bull_mr(1.0, float('nan')) is False
    assert zone_bull_mr(float('nan'), float('nan')) is False
    assert zone_bear_mr(float('nan'), 1.0) is False
    print(f"  test_2 PASS: NaN inputs → False")


def test_3_array_vectorized():
    """Array inputs → vectorized np.bool_ result."""
    f = np.array([1.0, 3.0, 2.0, float('nan'), 1.5])
    s = np.array([2.0, 1.0, 2.0, 1.0, float('nan')])
    bull = zone_bull_mr(f, s)
    bear = zone_bear_mr(f, s)
    assert isinstance(bull, np.ndarray) and bull.dtype == np.bool_
    # Expected: fast<slow? [T, F, F(equal), F(nan), F(nan)]
    np.testing.assert_array_equal(bull, np.array([True, False, False, False, False]))
    np.testing.assert_array_equal(bear, np.array([False, True, False, False, False]))
    print(f"  test_3 PASS: array vectorized + NaN propagation to False")


def test_4_calc_zones_delegation():
    """calc_zones retorna mismo resultado que zone_bull/bear_mr aplicados
    a forming/resolved arrays."""
    np.random.seed(42)
    N = 100
    fast = np.random.randn(N) + 100
    slow_f = np.random.randn(N) + 100
    slow_r = np.random.randn(N) + 100
    # Inject NaN
    fast[5] = np.nan
    slow_f[10] = np.nan
    slow_r[15] = np.nan
    zones = calc_zones(fast, slow_f, slow_r)
    expected_bull_f = zone_bull_mr(fast, slow_f)
    expected_bear_f = zone_bear_mr(fast, slow_f)
    expected_bull_r = zone_bull_mr(fast, slow_r)
    expected_bear_r = zone_bear_mr(fast, slow_r)
    np.testing.assert_array_equal(zones['zone_bull_forming'], expected_bull_f)
    np.testing.assert_array_equal(zones['zone_bear_forming'], expected_bear_f)
    np.testing.assert_array_equal(zones['zone_bull_resolved'], expected_bull_r)
    np.testing.assert_array_equal(zones['zone_bear_resolved'], expected_bear_r)
    print(f"  test_4 PASS: calc_zones delegates correctly (N={N})")


def test_5_inline_equivalence_parity():
    """
    Equivalence con el inline comparison eliminado de brain_engine.
    Reproduce el patrón original: `fl < sf` escalar. Zone_bull_mr escalar
    debe coincidir.
    """
    np.random.seed(7)
    pairs = [(np.random.randn() + 100, np.random.randn() + 100) for _ in range(100)]
    for fl, sf in pairs:
        inline_bull = (fl < sf)  # Old brain_engine inline pattern
        helper_bull = zone_bull_mr(float(fl), float(sf))
        assert helper_bull == inline_bull, f"parity broken at fl={fl}, sf={sf}"
    # Include NaN edge cases
    assert zone_bull_mr(float('nan'), 1.0) is False
    # Note: (NaN < 1.0) == False in Python too, so parity also holds for NaN comparison
    # but zone_bull_mr is defensive (explicit False) while inline relies on IEEE semantics
    print(f"  test_5 PASS: scalar helper ≡ inline fl<sf (100 random pairs)")


def test_6_brain_imports_helpers():
    """Verify brain_engine.py imports the helpers (post-refactor)."""
    brain_path = os.path.join(_root, 'live', 'brain_engine.py')
    with open(brain_path, encoding='utf-8') as f:
        src = f.read()
    assert 'from mean_reversion_features import zone_bull_mr, zone_bear_mr' in src, \
        "brain_engine.py missing zone_bull_mr/zone_bear_mr import"
    # Verify inline patterns are gone from MR cancel functions
    # (_check_cancel_zona_mr and _check_cancel_ghost_mr)
    # Extract relevant blocks
    idx_start = src.find('def _check_cancel_zona_mr')
    idx_end = src.find('def _check_cancel_ghost_mr')
    idx_end2 = src.find('\ndef ', idx_end + 1)
    cancel_block = src[idx_start:idx_end2]
    # Should NOT contain the old inline patterns
    assert 'ft < sf' not in cancel_block, "old inline 'ft < sf' still present"
    assert 'ft > sf' not in cancel_block, "old inline 'ft > sf' still present"
    assert 'fl < sf' not in cancel_block, "old inline 'fl < sf' still present"
    assert 'fl < sr' not in cancel_block, "old inline 'fl < sr' still present"
    # Should contain the helper calls
    assert 'zone_bull_mr(ft, sf)' in cancel_block
    assert 'zone_bear_mr(ft, sf)' in cancel_block
    assert 'zone_bull_mr(ft, sr)' in cancel_block
    assert 'zone_bear_mr(ft, sr)' in cancel_block
    assert 'zone_bull_mr(fl, sf)' in cancel_block
    assert 'zone_bull_mr(fl, sr)' in cancel_block
    print(f"  test_6 PASS: brain_engine uses helpers, no inline 'ft<sf' remnants")


def _run_all():
    print("=" * 68)
    print("A05 S3 zone_bull/bear_mr helpers test suite")
    print("=" * 68)
    tests = [
        test_1_scalar_basic,
        test_2_scalar_nan_defensive,
        test_3_array_vectorized,
        test_4_calc_zones_delegation,
        test_5_inline_equivalence_parity,
        test_6_brain_imports_helpers,
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
