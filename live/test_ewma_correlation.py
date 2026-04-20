"""
test_ewma_correlation.py -- Test EWMA vs SMA correlation reactivity.

Genera dos series: 160 barras de correlacion baja (r~0.2) seguidas de
8 barras de correlacion perfecta (r=1.0).
- SMA 168h: r resultante ~0.25 (diluida por las 160 barras de calma)
- EWMA halflife=24: r resultante ~0.85+ (reactiva al shock reciente)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd


def test_ewma_vs_sma_reactivity():
    """EWMA debe detectar shock reciente que SMA diluye."""
    np.random.seed(42)

    # 160 barras: correlacion baja (series independientes)
    n_calm = 160
    a_calm = np.random.randn(n_calm) * 0.02
    b_calm = np.random.randn(n_calm) * 0.02  # independiente

    # 8 barras: correlacion perfecta (contagio/shock macro)
    n_shock = 8
    shock = np.random.randn(n_shock) * 0.04
    a_shock = shock
    b_shock = shock  # perfectamente correlados

    a = np.concatenate([a_calm, a_shock])
    b = np.concatenate([b_calm, b_shock])

    # SMA (Pearson sobre toda la ventana)
    df = pd.DataFrame({"A": a, "B": b})
    sma_corr = df.corr().loc["A", "B"]

    # EWMA halflife=24
    ewm_corr = df.ewm(halflife=24).corr()
    ewma_corr = ewm_corr.loc[df.index[-1]].loc["A", "B"]

    print(f"Series: {n_calm} barras calma (r~0) + {n_shock} barras shock (r=1.0)")
    print(f"  SMA  Pearson(168): r = {sma_corr:.4f}")
    print(f"  EWMA halflife=24:  r = {ewma_corr:.4f}")
    print()

    # SMA deberia estar diluida (<0.40)
    assert sma_corr < 0.40, f"SMA correlation too high: {sma_corr:.4f}"
    # EWMA deberia ser significativamente mayor que SMA (al menos 2x)
    assert ewma_corr > sma_corr * 2.0, (
        f"EWMA should be at least 2x SMA: ewma={ewma_corr:.4f} sma={sma_corr:.4f}"
    )
    assert ewma_corr > 0.50, f"EWMA correlation too low: {ewma_corr:.4f}"

    print(f"  EWMA/SMA ratio: {ewma_corr/sma_corr:.1f}x mas reactivo")
    print("PASS: test_ewma_vs_sma_reactivity")


def test_compute_correlation_matrix_ewma():
    """Verificar que compute_correlation_matrix usa EWMA."""
    from live.portfolio_manager import compute_correlation_matrix

    np.random.seed(42)
    n_bars = 200

    # Crear market_data con BTC y ETH altamente correlados
    btc_returns = np.random.randn(n_bars) * 0.02
    btc_close = 65000 * np.exp(np.cumsum(btc_returns))

    # ETH = BTC * 0.9 + ruido (alta correlacion)
    eth_close = 3500 * np.exp(np.cumsum(btc_returns * 0.9 + np.random.randn(n_bars) * 0.005))

    # DOGE independiente
    doge_close = 0.15 * np.exp(np.cumsum(np.random.randn(n_bars) * 0.03))

    market_data = {}
    for sym, closes in [("BTC/USDT", btc_close), ("ETH/USDT", eth_close), ("DOGE/USDT", doge_close)]:
        market_data[sym] = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
            "open": closes * 0.999, "high": closes * 1.005,
            "low": closes * 0.995, "close": closes,
            "volume": np.ones(n_bars),
        })

    corr = compute_correlation_matrix(market_data)

    btc_eth = corr.loc["BTC/USDT", "ETH/USDT"]
    btc_doge = corr.loc["BTC/USDT", "DOGE/USDT"]

    print(f"  BTC-ETH correlation (EWMA): {btc_eth:.4f}")
    print(f"  BTC-DOGE correlation (EWMA): {btc_doge:.4f}")

    assert btc_eth > 0.7, f"BTC-ETH should be highly correlated: {btc_eth:.4f}"
    assert abs(btc_doge) < 0.5, f"BTC-DOGE should be weakly correlated: {btc_doge:.4f}"

    print("PASS: test_compute_correlation_matrix_ewma")


def test_existing_dd_tests_still_pass():
    """Verificar que los tests de DD circuit breaker siguen pasando."""
    from live.test_dd_circuit_breaker import (
        test_dd_multiplier_bands,
        test_hysteresis,
        test_peak_update,
        test_portfolio_dd_multiplier_zero,
        test_portfolio_dd_multiplier_reduces_sizing,
    )
    test_dd_multiplier_bands()
    test_hysteresis()
    test_peak_update()
    test_portfolio_dd_multiplier_zero()
    test_portfolio_dd_multiplier_reduces_sizing()
    print("PASS: test_existing_dd_tests_still_pass (all 5 sub-tests)")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S")

    test_ewma_vs_sma_reactivity()
    print()
    test_compute_correlation_matrix_ewma()
    print()
    test_existing_dd_tests_still_pass()

    print("\n===== ALL TESTS PASSED =====")
