"""
Tests v2.4.3 symbol-aware min_order pre-check.
Standalone (no pytest). Run: python tests/test_min_order_precheck.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

from live.portfolio_manager import compute_min_order_usdt_for


def _mk_market(precision_amount=None, amount_min=None, cost_min=None):
    m = {}
    if precision_amount is not None:
        m["precision"] = {"amount": precision_amount}
    if amount_min is not None or cost_min is not None:
        limits = {}
        if amount_min is not None:
            limits["amount"] = {"min": amount_min}
        if cost_min is not None:
            limits["cost"] = {"min": cost_min}
        m["limits"] = limits
    return m


def test_compute_min_order_eth_high_price():
    """ETH precision 0.01 at $2310 -> min=23.1 USDT."""
    m = {"ETH/USDT:USDT": _mk_market(precision_amount=0.01, amount_min=0.01, cost_min=2.0)}
    r = compute_min_order_usdt_for("ETH/USDT:USDT", 2310.0, m)
    assert abs(r - 23.1) < 0.01, f"expected 23.1, got {r}"
    print(f"  [OK] eth_high_price: {r:.2f} USDT")


def test_compute_min_order_uni_normal():
    """UNI precision 1.0 at $3.25 -> raw 3.25, floor 5.0."""
    m = {"UNI/USDT:USDT": _mk_market(precision_amount=1.0, amount_min=1.0, cost_min=2.0)}
    r = compute_min_order_usdt_for("UNI/USDT:USDT", 3.25, m)
    assert abs(r - 5.0) < 0.01, f"expected 5.0 (floor), got {r}"
    print(f"  [OK] uni_normal: {r:.2f} USDT (floor aplicado)")


def test_compute_min_order_algo():
    """ALGO amount_min 17.4 at $0.10 -> raw 1.74, floor 5.0."""
    m = {"ALGO/USDT:USDT": _mk_market(precision_amount=0.1, amount_min=17.4, cost_min=2.0)}
    r = compute_min_order_usdt_for("ALGO/USDT:USDT", 0.10, m)
    assert abs(r - 5.0) < 0.01, f"expected 5.0 (floor), got {r}"
    print(f"  [OK] algo: {r:.2f} USDT (floor aplicado)")


def test_compute_min_order_fallback_no_markets():
    """markets_info None o {} -> 5.0 default."""
    assert compute_min_order_usdt_for("ETH/USDT:USDT", 2310.0, None) == 5.0
    assert compute_min_order_usdt_for("ETH/USDT:USDT", 2310.0, {}) == 5.0
    print("  [OK] fallback_no_markets: 5.0 USDT")


def test_compute_min_order_fallback_invalid_price():
    """price <= 0 o no numerico -> 5.0 default."""
    m = {"ETH/USDT:USDT": _mk_market(precision_amount=0.01, cost_min=2.0)}
    assert compute_min_order_usdt_for("ETH/USDT:USDT", 0.0, m) == 5.0
    assert compute_min_order_usdt_for("ETH/USDT:USDT", -100, m) == 5.0
    assert compute_min_order_usdt_for("ETH/USDT:USDT", "no_number", m) == 5.0
    print("  [OK] fallback_invalid_price: 5.0 USDT")


def test_compute_min_order_missing_symbol():
    """Symbol no en markets_info -> 5.0 default."""
    m = {"ETH/USDT:USDT": _mk_market(precision_amount=0.01)}
    assert compute_min_order_usdt_for("BTC/USDT:USDT", 50000, m) == 5.0
    print("  [OK] missing_symbol: 5.0 USDT")


def test_eth_hypothetical_with_bigger_balance():
    """ETH con price 3000, size 25 USDT -> 25 USDT >= 30 min? No, falla por precision.
    Verifica que compute devuelve 30 (el threshold correcto)."""
    m = {"ETH/USDT:USDT": _mk_market(precision_amount=0.01, amount_min=0.01, cost_min=2.0)}
    r = compute_min_order_usdt_for("ETH/USDT:USDT", 3000.0, m)
    assert abs(r - 30.0) < 0.01, f"expected 30.0, got {r}"
    print(f"  [OK] eth_price_3000: min threshold {r:.2f} USDT")


def test_btc_high_precision():
    """BTC precision 0.0001 at 50000 -> 5.0 USDT (raw 5.0, equals floor)."""
    m = {"BTC/USDT:USDT": _mk_market(precision_amount=0.0001, amount_min=0.0001, cost_min=2.0)}
    r = compute_min_order_usdt_for("BTC/USDT:USDT", 50000.0, m)
    assert abs(r - 5.0) < 0.01, f"expected 5.0 (floor), got {r}"
    print(f"  [OK] btc_high_precision: {r:.2f} USDT")


if __name__ == "__main__":
    print("=== Tests v2.4.3 compute_min_order_usdt_for ===")
    test_compute_min_order_eth_high_price()
    test_compute_min_order_uni_normal()
    test_compute_min_order_algo()
    test_compute_min_order_fallback_no_markets()
    test_compute_min_order_fallback_invalid_price()
    test_compute_min_order_missing_symbol()
    test_eth_hypothetical_with_bigger_balance()
    test_btc_high_precision()
    print("=== 8/8 PASS ===")
