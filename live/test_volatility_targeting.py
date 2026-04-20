"""
test_volatility_targeting.py -- Tests para volatility targeting en portfolio_manager.

Verifica:
1. ATR uniforme -> todos weights = 1.0
2. ATR diferente -> weights inversamente proporcionales
3. Clamp [0.3, 2.0]
4. Limites (5%/pos) se respetan con weight > 1.0
5. Regresion: DD circuit breaker y EWMA siguen funcionando
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from live.portfolio_manager import compute_volatility_weights, allocate_positions, PortfolioConfig


def _make_ohlcv(n_bars, base_price, atr_pct):
    """Genera OHLCV sintetico con ATR controlado."""
    np.random.seed(42)
    close = np.full(n_bars, base_price, dtype=float)
    # Variacion minima para que no sea todo constante
    close += np.random.randn(n_bars) * base_price * 0.001
    spread = base_price * atr_pct / 100.0
    high = close + spread / 2
    low = close - spread / 2
    return pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
        "open": close,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.ones(n_bars),
    })


def test_uniform_atr():
    """Con ATR uniforme, todos los weights deben ser ~1.0."""
    market_data = {
        "BTC/USDT": _make_ohlcv(200, 65000, 2.0),
        "ETH/USDT": _make_ohlcv(200, 3500, 2.0),
        "SOL/USDT": _make_ohlcv(200, 180, 2.0),
    }
    weights = compute_volatility_weights(market_data)

    for sym, w in weights.items():
        assert abs(w - 1.0) < 0.15, f"{sym} weight {w} should be ~1.0 with uniform ATR"

    print("PASS: test_uniform_atr")


def test_inverse_proportional():
    """BTC ATR=1%, WLD ATR=3% -> BTC weight ~1.5, WLD weight ~0.5."""
    market_data = {
        "BTC/USDT": _make_ohlcv(200, 65000, 1.0),  # low vol
        "ETH/USDT": _make_ohlcv(200, 3500, 2.0),   # median vol
        "WLD/USDT": _make_ohlcv(200, 2.5, 3.0),     # high vol
    }
    weights = compute_volatility_weights(market_data)

    print(f"  BTC weight: {weights.get('BTC/USDT', 0):.3f} (ATR=1%)")
    print(f"  ETH weight: {weights.get('ETH/USDT', 0):.3f} (ATR=2%)")
    print(f"  WLD weight: {weights.get('WLD/USDT', 0):.3f} (ATR=3%)")

    # Mediana ATR = 2%. BTC=1% -> w=2.0, ETH=2% -> w=1.0, WLD=3% -> w=0.67
    assert weights["BTC/USDT"] > 1.3, f"BTC should have high weight: {weights['BTC/USDT']}"
    assert abs(weights["ETH/USDT"] - 1.0) < 0.15, f"ETH should be ~1.0: {weights['ETH/USDT']}"
    assert weights["WLD/USDT"] < 0.8, f"WLD should have low weight: {weights['WLD/USDT']}"

    print("PASS: test_inverse_proportional")


def test_clamp():
    """Weights must be clamped to [0.3, 2.0]."""
    market_data = {
        "LOW/USDT": _make_ohlcv(200, 100, 0.1),    # very low vol -> raw weight very high
        "MED/USDT": _make_ohlcv(200, 100, 2.0),     # median
        "HIGH/USDT": _make_ohlcv(200, 100, 20.0),   # very high vol -> raw weight very low
    }
    weights = compute_volatility_weights(market_data)

    print(f"  LOW weight: {weights.get('LOW/USDT', 0):.3f}")
    print(f"  MED weight: {weights.get('MED/USDT', 0):.3f}")
    print(f"  HIGH weight: {weights.get('HIGH/USDT', 0):.3f}")

    assert weights["LOW/USDT"] <= 2.0, f"LOW should be clamped to 2.0: {weights['LOW/USDT']}"
    assert weights["HIGH/USDT"] >= 0.3, f"HIGH should be clamped to 0.3: {weights['HIGH/USDT']}"

    print("PASS: test_clamp")


def test_cap_respects_max_position():
    """vol_weight > 1.0 should not push sizing above max_single_position_pct."""
    config = PortfolioConfig(
        sector_map={},
        leverage_map={"BTC/USDT": 1},
        blending_enabled=False,
        max_single_position_pct=5.0,
    )

    balance = {"total": 1000.0, "free": 1000.0, "used": 0.0}
    positions = {}
    regime_info = {"BTC/USDT": {"cluster": 1, "confidence": 0.90, "operable": True}}
    signals = {
        "BTC/USDT": {
            "action": "LONG", "reason": "test", "entry_price": 65000.0,
            "sl_price": 63000.0, "confidence": 0.90, "operable": True,
        },
    }

    # BTC con ATR muy bajo -> vol_weight alto (~2.0)
    # Pero sizing should not exceed 5% of free_capital = 50 USDT
    market_data = {"BTC/USDT": _make_ohlcv(200, 65000, 0.5)}

    result = allocate_positions(
        signals, balance, positions, regime_info, market_data, config,
        dd_multiplier=1.0,
    )

    size = result["BTC/USDT"]["size_usdt"]
    max_allowed = 1000.0 * 5.0 / 100.0  # 50 USDT

    print(f"  size_usdt: {size:.2f}, max_allowed: {max_allowed:.2f}")
    assert size <= max_allowed + 0.01, f"Size {size} exceeds max {max_allowed}"

    print("PASS: test_cap_respects_max_position")


def test_regression_dd_and_ewma():
    """Verify previous tests still pass."""
    from live.test_dd_circuit_breaker import (
        test_dd_multiplier_bands,
        test_hysteresis,
        test_peak_update,
        test_portfolio_dd_multiplier_zero,
        test_portfolio_dd_multiplier_reduces_sizing,
    )
    from live.test_ewma_correlation import (
        test_ewma_vs_sma_reactivity,
        test_compute_correlation_matrix_ewma,
    )

    test_dd_multiplier_bands()
    test_hysteresis()
    test_peak_update()
    test_portfolio_dd_multiplier_zero()
    test_portfolio_dd_multiplier_reduces_sizing()
    test_ewma_vs_sma_reactivity()
    print()
    test_compute_correlation_matrix_ewma()

    print("PASS: test_regression_dd_and_ewma (all 7 sub-tests)")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S")

    test_uniform_atr()
    print()
    test_inverse_proportional()
    print()
    test_clamp()
    print()
    test_cap_respects_max_position()
    print()
    test_regression_dd_and_ewma()

    print("\n===== ALL TESTS PASSED =====")
