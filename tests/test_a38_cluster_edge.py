"""Tests A38 — _classify_cluster_edge guard contra exp_pool/exp_oos negativos.

Verifica:
  - exp_pool>0, exp_oos>0, ratio bajo  -> 'edge_erosion'
  - exp_pool>0, exp_oos>0, ratio alto  -> None (cluster sano)
  - exp_pool<=0                         -> 'cluster_estructuralmente_perdedor'
  - exp_oos<0 con exp_pool>0            -> 'cluster_estructuralmente_perdedor'
  - None inputs                          -> None (datos insuficientes)
  - n < min_n                            -> None (datos insuficientes)

Sin guard A38 (pre-fix), ratio_oos/exp_pool con numerador o denominador
negativo cruzaba threshold 0.5 espuriamente (ej. -0.4 < 0.5 disparaba
edge_erosion falso para cluster con exp_pool<0).

Run: python tests/test_a38_cluster_edge.py
"""
from __future__ import annotations

import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from analyze_performance_attribution import (
    _classify_cluster_edge,
    DEFAULT_MIN_N_EDGE_EROSION,
    EDGE_EROSION_RATIO_ALERT,
)


MIN_N = DEFAULT_MIN_N_EDGE_EROSION  # default 3
RATIO = EDGE_EROSION_RATIO_ALERT    # default 0.5


def test_edge_erosion_happy_path():
    """exp_pool>0, exp_oos>0, ratio < 0.5 -> edge_erosion."""
    # exp_pool=1.0, exp_oos=0.3 -> ratio=0.3 < 0.5 -> edge_erosion
    label = _classify_cluster_edge(1.0, 0.3, 10)
    assert label == 'edge_erosion', f"expected edge_erosion, got {label}"
    print("OK edge_erosion happy path")


def test_cluster_sano():
    """exp_pool>0, exp_oos>0, ratio >= 0.5 -> None (sin flag)."""
    # exp_pool=1.0, exp_oos=0.7 -> ratio=0.7 >= 0.5 -> None
    label = _classify_cluster_edge(1.0, 0.7, 10)
    assert label is None, f"expected None, got {label}"
    print("OK cluster sano ratio>=0.5 -> None")


def test_exp_pool_negative_guard():
    """A38 core: exp_pool<0 -> cluster_estructuralmente_perdedor.

    Pre-fix: exp_pool=-2.5, exp_oos=-1.0 -> ratio=0.4 (positivo!) < 0.5 ->
    flag edge_erosion falso. Post-fix: clasificado correctamente como
    cluster perdedor.
    """
    label = _classify_cluster_edge(-2.5, -1.0, 10)
    assert label == 'cluster_estructuralmente_perdedor', \
        f"expected cluster_estructuralmente_perdedor, got {label}"
    print("OK exp_pool<0, exp_oos<0 -> cluster_estructuralmente_perdedor")


def test_exp_pool_zero_guard():
    """exp_pool=0 -> cluster_estructuralmente_perdedor (no dividir por cero)."""
    label = _classify_cluster_edge(0.0, 0.5, 10)
    assert label == 'cluster_estructuralmente_perdedor', \
        f"expected cluster_estructuralmente_perdedor, got {label}"
    print("OK exp_pool=0 -> cluster_estructuralmente_perdedor")


def test_exp_pool_positive_exp_oos_negative():
    """exp_pool>0 pero exp_oos<0 -> cluster_estructuralmente_perdedor.

    Pre-fix: exp_pool=2.0, exp_oos=-0.5 -> ratio=-0.25 < 0.5 -> edge_erosion
    falso. Post-fix: flag correcto (exp_oos negativo indica pérdida OOS).
    """
    label = _classify_cluster_edge(2.0, -0.5, 10)
    assert label == 'cluster_estructuralmente_perdedor', \
        f"expected cluster_estructuralmente_perdedor, got {label}"
    print("OK exp_pool>0, exp_oos<0 -> cluster_estructuralmente_perdedor")


def test_none_inputs():
    """None en exp_pool o exp_oos -> None (datos insuficientes)."""
    assert _classify_cluster_edge(None, 0.5, 10) is None
    assert _classify_cluster_edge(1.0, None, 10) is None
    assert _classify_cluster_edge(None, None, 10) is None
    print("OK None inputs -> None")


def test_n_below_min():
    """n < min_n -> None (datos insuficientes aunque ratio cruce threshold)."""
    assert MIN_N >= 2, "Test asume MIN_N >= 2"
    label = _classify_cluster_edge(1.0, 0.3, MIN_N - 1)
    assert label is None, f"n<min_n deberia retornar None, got {label}"
    print(f"OK n<min_n={MIN_N} -> None")


def test_custom_min_n_and_ratio():
    """min_n y ratio_alert custom aplican correctamente."""
    # custom min_n=100, con n=10 -> None
    label = _classify_cluster_edge(1.0, 0.3, 10, min_n=100)
    assert label is None, f"custom min_n=100 con n=10 deberia ser None, got {label}"
    # custom ratio_alert=0.1 (más estricto), con ratio=0.3 -> None (0.3 >= 0.1)
    label2 = _classify_cluster_edge(1.0, 0.3, 10, ratio_alert=0.1)
    assert label2 is None, f"custom ratio_alert=0.1 con ratio=0.3 deberia ser None, got {label2}"
    # mismo input pero ratio_alert=0.5 default -> edge_erosion (0.3 < 0.5)
    label3 = _classify_cluster_edge(1.0, 0.3, 10, ratio_alert=0.5)
    assert label3 == 'edge_erosion', f"ratio_alert=0.5 con ratio=0.3 deberia ser edge_erosion, got {label3}"
    print("OK custom min_n y ratio_alert")


def test_ratio_boundary():
    """ratio exactamente == ratio_alert -> None (strictly less than)."""
    # ratio=0.5 exactamente, ratio_alert=0.5 -> None
    label = _classify_cluster_edge(1.0, 0.5, 10)
    assert label is None, f"ratio=0.5 == ratio_alert deberia ser None (< strictly), got {label}"
    print("OK ratio boundary == ratio_alert -> None (strict less)")


if __name__ == "__main__":
    tests = [
        test_edge_erosion_happy_path,
        test_cluster_sano,
        test_exp_pool_negative_guard,
        test_exp_pool_zero_guard,
        test_exp_pool_positive_exp_oos_negative,
        test_none_inputs,
        test_n_below_min,
        test_custom_min_n_and_ratio,
        test_ratio_boundary,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    total = len(tests)
    print(f"\n{total - failed}/{total} tests PASS")
    sys.exit(0 if failed == 0 else 1)
