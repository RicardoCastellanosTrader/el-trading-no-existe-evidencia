"""Test unit de _run_verify_test parametrización n_bars + tolerance escalada.

Cubre validación input + detección de nivel A/B + backward compat.
Smokes integración (ejecución real) validados aparte en §0.8:
- Nivel A BTC/USDT N=1000: diff 0.0000 exacto.
- Nivel B BTC/USDT N=5000: diff 0.0000 (BTC converge).
- Nivel B ONDO/USDT N=8000: match 99.38%, PnL diff_rel 9.80%.
"""
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from live.brain_engine import (
    _run_verify_test,
    _VERIFY_LEVEL_B_THRESHOLD,
    _VERIFY_TOLERANCE_PNL_A_PP,
    _VERIFY_TOLERANCE_PNL_B_PCT,
    _VERIFY_TOLERANCE_PNL_B_FLOOR_PP,
)


def test_n_bars_zero_raises():
    with pytest.raises(ValueError, match="n_bars debe ser >= 1"):
        _run_verify_test("BTC/USDT", n_bars=0)


def test_n_bars_negative_raises():
    with pytest.raises(ValueError, match="n_bars debe ser >= 1"):
        _run_verify_test("BTC/USDT", n_bars=-100)


def test_level_constants_match_protocol():
    """Constantes alineadas con §0.8 protocolo smoke test."""
    # Nivel B threshold: N>=2000 según item §13.3 original.
    assert _VERIFY_LEVEL_B_THRESHOLD == 2000
    # Nivel A PnL tolerance: 0.1pp (preserva comportamiento pre-refactor).
    assert _VERIFY_TOLERANCE_PNL_A_PP == 0.1
    # Nivel B PnL tolerance: 15% relativo con floor 0.1pp (margen sobre drift 7-9% §12 L30).
    assert _VERIFY_TOLERANCE_PNL_B_PCT == 15.0
    assert _VERIFY_TOLERANCE_PNL_B_FLOOR_PP == 0.1


def test_missing_parquet_returns_failure(capsys):
    """Símbolo sin parquet retorna exit code != 0 + mensaje informativo."""
    exit_code = _run_verify_test("NONEXISTENT/USDT", n_bars=100)
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "No se encontro" in captured.out


def test_default_n_bars_backward_compat():
    """Signature default n_bars=1000 preserva gate Nivel A §0.8."""
    import inspect
    sig = inspect.signature(_run_verify_test)
    assert sig.parameters["n_bars"].default == 1000
    assert sig.parameters["symbol"].default == "BTC/USDT"
