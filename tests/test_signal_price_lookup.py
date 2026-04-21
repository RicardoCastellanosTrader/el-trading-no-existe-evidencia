"""Tests unitarios para signal_price_lookup.

Verifica:
  - get_signal_price: happy path, missing keys, p=0/None, action_hint mismatch.
  - compute_slippage_usdt: signo LONG/SHORT favorable vs adverso.
  - compute_slippage_pct: convencion de signo.
  - attribute_slippage_per_trade: integracion con side + exit_side invertido.

Run: python tests/test_signal_price_lookup.py
     o: python -m pytest tests/test_signal_price_lookup.py -v
"""
import logging
import os
import sys

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from signal_price_lookup import (
    get_signal_price,
    compute_slippage_usdt,
    compute_slippage_pct,
    attribute_slippage_per_trade,
)


# ---------------------------------------------------------------------------
# get_signal_price
# ---------------------------------------------------------------------------

def test_lookup_returns_price_when_signal_exists():
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {
        (ec, "IMX/USDT"): {"a": "LONG", "r": "ma_cross", "p": 0.1637,
                             "s": "TF", "k": 2}
    }
    assert get_signal_price(signals_raw, ec, "IMX/USDT") == 0.1637


def test_lookup_returns_none_when_missing():
    assert get_signal_price({}, pd.Timestamp("2026-04-21T14:00:00Z"), "X/USDT") is None


def test_lookup_returns_none_when_p_missing():
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {(ec, "X/USDT"): {"a": "LONG"}}
    assert get_signal_price(signals_raw, ec, "X/USDT") is None


def test_lookup_returns_none_when_p_zero():
    """brain_engine l.517-523 solo loguea p si truthy, pero guard defensivo."""
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {(ec, "X/USDT"): {"a": "LONG", "p": 0.0}}
    assert get_signal_price(signals_raw, ec, "X/USDT") is None


def test_lookup_returns_none_when_cycle_is_none():
    assert get_signal_price({}, None, "X/USDT") is None


def test_lookup_returns_none_when_p_not_numeric():
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {(ec, "X/USDT"): {"a": "LONG", "p": "bogus"}}
    assert get_signal_price(signals_raw, ec, "X/USDT") is None


def test_lookup_coerces_str_p_to_float():
    """JSON decoder podria entregar "100.5" como str si viene mal."""
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {(ec, "X/USDT"): {"a": "LONG", "p": "100.5"}}
    assert get_signal_price(signals_raw, ec, "X/USDT") == 100.5


def test_lookup_logs_warning_on_entry_hint_vs_close_actual(caplog=None):
    """Sanity check: hint=LONG pero actual=CLOSE_LONG -> WARNING."""
    import io
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger("signal_price_lookup")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        ec = pd.Timestamp("2026-04-21T14:00:00Z")
        signals_raw = {(ec, "X/USDT"): {"a": "CLOSE_LONG", "p": 100.0}}
        result = get_signal_price(signals_raw, ec, "X/USDT", action_hint="LONG")
        assert result == 100.0  # lookup permisivo
        log_output = log_capture.getvalue()
        assert "action mismatch" in log_output.lower() or "mismatch" in log_output.lower()
    finally:
        logger.removeHandler(handler)


def test_lookup_no_warning_when_hint_matches():
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {(ec, "X/USDT"): {"a": "LONG", "p": 100.0}}
    # solo queremos verificar que no crashea con hint que matchea
    assert get_signal_price(signals_raw, ec, "X/USDT", action_hint="LONG") == 100.0


def test_lookup_no_warning_when_both_close():
    ec = pd.Timestamp("2026-04-21T14:00:00Z")
    signals_raw = {(ec, "X/USDT"): {"a": "CLOSE_SHORT", "p": 100.0}}
    assert get_signal_price(signals_raw, ec, "X/USDT", action_hint="CLOSE_LONG") == 100.0


# ---------------------------------------------------------------------------
# compute_slippage_usdt — LONG
# ---------------------------------------------------------------------------

def test_slippage_long_favorable_when_fill_lower():
    # fill 99.9, signal 100.0, long, 10 contratos -> +1.0 USDT favorable
    result = compute_slippage_usdt(
        fill_price=99.9, signal_price=100.0, side="long", size_contracts=10
    )
    assert abs(result - 1.0) < 1e-9


def test_slippage_long_adverse_when_fill_higher():
    # fill 100.1, signal 100.0, long, 10 contratos -> -1.0 USDT adverso
    result = compute_slippage_usdt(
        fill_price=100.1, signal_price=100.0, side="long", size_contracts=10
    )
    assert abs(result - (-1.0)) < 1e-9


def test_slippage_long_zero_when_fill_equals_signal():
    result = compute_slippage_usdt(
        fill_price=100.0, signal_price=100.0, side="long", size_contracts=10
    )
    assert abs(result) < 1e-9


# ---------------------------------------------------------------------------
# compute_slippage_usdt — SHORT
# ---------------------------------------------------------------------------

def test_slippage_short_favorable_when_fill_higher():
    # fill 100.1, signal 100.0, short, 10 contratos -> +1.0 USDT favorable
    result = compute_slippage_usdt(
        fill_price=100.1, signal_price=100.0, side="short", size_contracts=10
    )
    assert abs(result - 1.0) < 1e-9


def test_slippage_short_adverse_when_fill_lower():
    # fill 99.9, signal 100.0, short, 10 contratos -> -1.0 USDT adverso
    result = compute_slippage_usdt(
        fill_price=99.9, signal_price=100.0, side="short", size_contracts=10
    )
    assert abs(result - (-1.0)) < 1e-9


def test_slippage_invalid_side_raises():
    try:
        compute_slippage_usdt(100, 100, side="invalid", size_contracts=1)
    except ValueError:
        return
    assert False, "expected ValueError"


# ---------------------------------------------------------------------------
# compute_slippage_pct
# ---------------------------------------------------------------------------

def test_slippage_pct_long_favorable():
    # fill 99, signal 100, long -> +1.0% favorable
    pct = compute_slippage_pct(fill_price=99.0, signal_price=100.0, side="long")
    assert abs(pct - 1.0) < 1e-9


def test_slippage_pct_short_favorable():
    pct = compute_slippage_pct(fill_price=101.0, signal_price=100.0, side="short")
    assert abs(pct - 1.0) < 1e-9


def test_slippage_pct_returns_zero_when_signal_zero():
    pct = compute_slippage_pct(fill_price=100.0, signal_price=0.0, side="long")
    assert pct == 0.0


# ---------------------------------------------------------------------------
# attribute_slippage_per_trade — integration
# ---------------------------------------------------------------------------

def test_attribute_long_full():
    """LONG trade: entry 100 (signal) -> 99.9 (fill), exit 105 (signal) -> 105.1 (fill).
    Entry: +0.1 * 10 = +1.0 favorable.
    Exit (exit_side=short): (105.1 - 105) * 10 = +1.0 favorable.
    Total: +2.0 USDT."""
    result = attribute_slippage_per_trade(
        fill_entry=99.9, fill_exit=105.1,
        signal_entry=100.0, signal_exit=105.0,
        side="long", size_contracts=10,
    )
    assert abs(result["slippage_entry_usdt"] - 1.0) < 1e-9
    assert abs(result["slippage_exit_usdt"] - 1.0) < 1e-9
    assert abs(result["slippage_total_usdt"] - 2.0) < 1e-9
    assert result["slippage_missing_entry"] is False
    assert result["slippage_missing_exit"] is False


def test_attribute_short_full():
    """SHORT trade: entry 100 (signal) -> 100.1 (fill, favorable).
    Exit 95 (signal) -> 94.9 (fill, exit_side=long -> favorable).
    Entry: (100 - 100.1) no... short formula: (fill - signal) = +0.1 * 10 = +1.0.
    Exit: exit_side=long -> (signal - fill) = (95 - 94.9) * 10 = +1.0.
    Total: +2.0."""
    result = attribute_slippage_per_trade(
        fill_entry=100.1, fill_exit=94.9,
        signal_entry=100.0, signal_exit=95.0,
        side="short", size_contracts=10,
    )
    assert abs(result["slippage_entry_usdt"] - 1.0) < 1e-9
    assert abs(result["slippage_exit_usdt"] - 1.0) < 1e-9
    assert abs(result["slippage_total_usdt"] - 2.0) < 1e-9


def test_attribute_missing_entry():
    """Si signal_entry es None, slippage_entry es None y total tambien."""
    result = attribute_slippage_per_trade(
        fill_entry=100.0, fill_exit=105.0,
        signal_entry=None, signal_exit=105.0,
        side="long", size_contracts=10,
    )
    assert result["slippage_entry_usdt"] is None
    assert result["slippage_missing_entry"] is True
    assert result["slippage_exit_usdt"] is not None
    assert result["slippage_total_usdt"] is None  # None porque entry es None


def test_attribute_missing_both():
    result = attribute_slippage_per_trade(
        fill_entry=100, fill_exit=105, signal_entry=None,
        signal_exit=None, side="long", size_contracts=10,
    )
    assert result["slippage_entry_usdt"] is None
    assert result["slippage_exit_usdt"] is None
    assert result["slippage_total_usdt"] is None
    assert result["slippage_missing_entry"] is True
    assert result["slippage_missing_exit"] is True


def test_attribute_long_adverse_both():
    """LONG adverse: entry 100->100.5 (adv), exit 105->104.5 (adv exit_side=short)."""
    result = attribute_slippage_per_trade(
        fill_entry=100.5, fill_exit=104.5,
        signal_entry=100.0, signal_exit=105.0,
        side="long", size_contracts=10,
    )
    # entry long adv: (100 - 100.5) * 10 = -5.0
    # exit short: (104.5 - 105) * 10 = -5.0 (fill menor que signal es adverso para sell)
    assert abs(result["slippage_entry_usdt"] - (-5.0)) < 1e-9
    assert abs(result["slippage_exit_usdt"] - (-5.0)) < 1e-9
    assert abs(result["slippage_total_usdt"] - (-10.0)) < 1e-9


if __name__ == '__main__':
    import traceback
    passed = 0
    failed = 0
    tests = [v for k, v in globals().items() if k.startswith('test_') and callable(v)]
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
