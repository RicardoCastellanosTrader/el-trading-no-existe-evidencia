"""
Tests symbol-aware min_order pre-check (migración Kraken Futures PF_).
markets_info keyed por símbolo ccxt Kraken ('ETH/USD:USD'); el caller pasa el
símbolo master ('ETH/USDT') y compute_min_order_usdt_for resuelve vía
to_kraken_symbol. Standalone (no pytest). Run: python tests/test_min_order_precheck.py
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
    """ETH precision 0.01 at $2310 -> min=23.1 USD."""
    m = {"ETH/USD:USD": _mk_market(precision_amount=0.01, amount_min=0.01, cost_min=2.0)}
    r = compute_min_order_usdt_for("ETH/USDT", 2310.0, m)
    assert abs(r - 23.1) < 0.01, f"expected 23.1, got {r}"
    print(f"  [OK] eth_high_price: {r:.2f} USD")


def test_compute_min_order_uni_normal():
    """UNI precision 1.0 at $3.25 -> raw 3.25, floor 5.0."""
    m = {"UNI/USD:USD": _mk_market(precision_amount=1.0, amount_min=1.0, cost_min=2.0)}
    r = compute_min_order_usdt_for("UNI/USDT", 3.25, m)
    assert abs(r - 5.0) < 0.01, f"expected 5.0 (floor), got {r}"
    print(f"  [OK] uni_normal: {r:.2f} USD (floor aplicado)")


def test_compute_min_order_algo():
    """ALGO amount_min 17.4 at $0.10 -> raw 1.74, floor 5.0."""
    m = {"ALGO/USD:USD": _mk_market(precision_amount=0.1, amount_min=17.4, cost_min=2.0)}
    r = compute_min_order_usdt_for("ALGO/USDT", 0.10, m)
    assert abs(r - 5.0) < 0.01, f"expected 5.0 (floor), got {r}"
    print(f"  [OK] algo: {r:.2f} USD (floor aplicado)")


def test_compute_min_order_fallback_no_markets():
    """markets_info None o {} -> 5.0 default."""
    assert compute_min_order_usdt_for("ETH/USDT", 2310.0, None) == 5.0
    assert compute_min_order_usdt_for("ETH/USDT", 2310.0, {}) == 5.0
    print("  [OK] fallback_no_markets: 5.0 USD")


def test_compute_min_order_fallback_invalid_price():
    """price <= 0 o no numerico -> 5.0 default."""
    m = {"ETH/USD:USD": _mk_market(precision_amount=0.01, cost_min=2.0)}
    assert compute_min_order_usdt_for("ETH/USDT", 0.0, m) == 5.0
    assert compute_min_order_usdt_for("ETH/USDT", -100, m) == 5.0
    assert compute_min_order_usdt_for("ETH/USDT", "no_number", m) == 5.0
    print("  [OK] fallback_invalid_price: 5.0 USD")


def test_compute_min_order_missing_symbol():
    """Symbol no en markets_info -> 5.0 default."""
    m = {"ETH/USD:USD": _mk_market(precision_amount=0.01)}
    assert compute_min_order_usdt_for("BTC/USDT", 50000, m) == 5.0
    print("  [OK] missing_symbol: 5.0 USD")


def test_eth_hypothetical_with_bigger_balance():
    """ETH con price 3000, precision 0.01 -> min threshold 30 USD."""
    m = {"ETH/USD:USD": _mk_market(precision_amount=0.01, amount_min=0.01, cost_min=2.0)}
    r = compute_min_order_usdt_for("ETH/USDT", 3000.0, m)
    assert abs(r - 30.0) < 0.01, f"expected 30.0, got {r}"
    print(f"  [OK] eth_price_3000: min threshold {r:.2f} USD")


def test_btc_high_precision():
    """BTC precision 0.0001 at 50000 -> 5.0 USD (raw 5.0, equals floor)."""
    m = {"BTC/USD:USD": _mk_market(precision_amount=0.0001, amount_min=0.0001, cost_min=2.0)}
    r = compute_min_order_usdt_for("BTC/USDT", 50000.0, m)
    assert abs(r - 5.0) < 0.01, f"expected 5.0 (floor), got {r}"
    print(f"  [OK] btc_high_precision: {r:.2f} USD")


def test_master_format_resolves_to_ccxt():
    """symbol 'ETH/USDT' (master format) debe resolver a
    markets_info['ETH/USD:USD'] (ccxt Kraken Futures PF_ format) vía
    to_kraken_symbol. Sin esto, compute devolvia 5.0 floor por no encontrar
    la key y ETH llegaba a execution para ser rechazado por el exchange."""
    m = {"ETH/USD:USD": _mk_market(precision_amount=0.01, amount_min=0.01, cost_min=2.0)}
    r = compute_min_order_usdt_for("ETH/USDT", 2310.0, m)
    assert abs(r - 23.1) < 0.01, f"expected 23.1 from master format, got {r}"
    print(f"  [OK] master_format_resolves_to_ccxt: {r:.2f} USD")


if __name__ == "__main__":
    print("=== Tests compute_min_order_usdt_for (Kraken Futures) ===")
    test_compute_min_order_eth_high_price()
    test_compute_min_order_uni_normal()
    test_compute_min_order_algo()
    test_compute_min_order_fallback_no_markets()
    test_compute_min_order_fallback_invalid_price()
    test_compute_min_order_missing_symbol()
    test_eth_hypothetical_with_bigger_balance()
    test_btc_high_precision()
    test_master_format_resolves_to_ccxt()
    print("=== 9/9 PASS ===")
