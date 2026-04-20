"""
test_dd_circuit_breaker.py -- Tests para el drawdown circuit breaker.

Verifica:
1. Multiplier correcto segun bandas de DD
2. Histeresis en la recuperacion
3. Integracion con portfolio_manager (dd_multiplier bloquea entradas)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live.live_engine import LiveEngine, EngineConfig


def test_dd_multiplier_bands():
    """Verificar bandas de DD -> multiplier."""
    engine = LiveEngine(EngineConfig())
    engine._peak_balance = 304.0  # pico fijado

    # DD 0% -> 1.0
    m = engine._calc_dd_multiplier(304.0)
    assert m == 1.0, f"Expected 1.0 got {m}"

    # DD 4.6% (balance=290) -> 1.0 (< 5%)
    m = engine._calc_dd_multiplier(290.0)
    assert m == 1.0, f"Expected 1.0 got {m}"

    # DD 7.9% (balance=280) -> 0.75
    engine._prev_dd_multiplier = 1.0
    m = engine._calc_dd_multiplier(280.0)
    assert m == 0.75, f"Expected 0.75 got {m}"

    # DD 10.5% (balance=272) -> 0.50
    engine._prev_dd_multiplier = 0.75
    m = engine._calc_dd_multiplier(272.0)
    assert m == 0.50, f"Expected 0.50 got {m}"

    # DD 15.1% (balance=258) -> 0.0
    engine._prev_dd_multiplier = 0.50
    m = engine._calc_dd_multiplier(258.0)
    assert m == 0.0, f"Expected 0.0 got {m}"
    assert engine._circuit_breaker_active is True

    print("PASS: test_dd_multiplier_bands")


def test_hysteresis():
    """Verificar histeresis: DD baja de 12% antes de reanudar."""
    engine = LiveEngine(EngineConfig())
    engine._peak_balance = 304.0

    # Activar circuit breaker (DD >15%)
    engine._prev_dd_multiplier = 0.50
    m = engine._calc_dd_multiplier(258.0)  # DD=15.1%
    assert m == 0.0
    assert engine._circuit_breaker_active is True

    # DD baja a 14% -> sigue pausado (histeresis, umbral es 12%)
    engine._prev_dd_multiplier = 0.0
    m = engine._calc_dd_multiplier(261.4)  # DD~14%
    assert m == 0.0, f"Expected 0.0 (hysteresis) got {m}"

    # DD baja a 13% -> sigue pausado
    engine._prev_dd_multiplier = 0.0
    m = engine._calc_dd_multiplier(264.5)  # DD~13%
    assert m == 0.0, f"Expected 0.0 (hysteresis) got {m}"

    # DD baja a 11.5% (< 12%) -> reanuda con 0.50
    engine._prev_dd_multiplier = 0.0
    m = engine._calc_dd_multiplier(269.5)  # DD~11.3%
    assert m == 0.50, f"Expected 0.50 (recovery) got {m}"
    assert engine._circuit_breaker_active is False

    # Sigue bajando DD a 8% -> 0.75 (banda normal)
    engine._prev_dd_multiplier = 0.50
    m = engine._calc_dd_multiplier(279.7)  # DD~8%
    assert m == 0.75, f"Expected 0.75 got {m}"

    print("PASS: test_hysteresis")


def test_peak_update():
    """Verificar que peak_balance se actualiza con nuevos maximos."""
    engine = LiveEngine(EngineConfig())

    m = engine._calc_dd_multiplier(300.0)
    assert engine._peak_balance == 300.0
    assert m == 1.0

    m = engine._calc_dd_multiplier(310.0)
    assert engine._peak_balance == 310.0
    assert m == 1.0

    # Baja -> peak se mantiene
    m = engine._calc_dd_multiplier(305.0)
    assert engine._peak_balance == 310.0
    assert m == 1.0  # DD=1.6%, < 5%

    print("PASS: test_peak_update")


def test_portfolio_dd_multiplier_zero():
    """Verificar que dd_multiplier=0 bloquea entradas pero permite cierres."""
    from live.portfolio_manager import allocate_positions, PortfolioConfig
    import numpy as np
    import pandas as pd

    config = PortfolioConfig(
        sector_map={},
        leverage_map={"BTC/USDT": 1, "ETH/USDT": 2},
    )

    balance = {"total": 1000.0, "free": 800.0, "used": 200.0}
    positions = {"ETH/USDT": {"side": "long", "size": 0.1, "entry_price": 3500.0}}

    regime_info = {
        "BTC/USDT": {"cluster": 1, "confidence": 0.90, "operable": True},
        "ETH/USDT": {"cluster": 1, "confidence": 0.90, "operable": True},
    }

    signals = {
        "BTC/USDT": {
            "action": "LONG", "reason": "test", "entry_price": 65000.0,
            "sl_price": 63000.0, "confidence": 0.90, "operable": True,
        },
        "ETH/USDT": {
            "action": "CLOSE_LONG", "reason": "sl_exit", "entry_price": 3500.0,
            "sl_price": 0.0, "confidence": 0.90, "operable": True,
        },
    }

    n_bars = 200
    np.random.seed(42)
    market_data = {}
    for sym, bp in [("BTC/USDT", 65000), ("ETH/USDT", 3500)]:
        closes = bp * np.exp(np.cumsum(np.random.randn(n_bars) * 0.02))
        market_data[sym] = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
            "open": closes, "high": closes, "low": closes, "close": closes,
            "volume": np.ones(n_bars),
        })

    # Con dd_multiplier=0.0: BTC entry bloqueada, ETH close permitido
    result = allocate_positions(
        signals, balance, positions, regime_info, market_data, config,
        dd_multiplier=0.0,
    )

    assert result["BTC/USDT"]["action"] == "FLAT", f"Expected FLAT got {result['BTC/USDT']['action']}"
    assert result["BTC/USDT"]["reason"] == "circuit_breaker_paused"
    assert result["ETH/USDT"]["action"] == "CLOSE_LONG", f"Expected CLOSE_LONG got {result['ETH/USDT']['action']}"

    print("PASS: test_portfolio_dd_multiplier_zero")


def test_portfolio_dd_multiplier_reduces_sizing():
    """Verificar que dd_multiplier=0.75 reduce sizing en 25%."""
    from live.portfolio_manager import allocate_positions, PortfolioConfig
    import numpy as np
    import pandas as pd

    config = PortfolioConfig(
        sector_map={},
        leverage_map={"BTC/USDT": 1},
        blending_enabled=False,
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

    n_bars = 200
    np.random.seed(42)
    closes = 65000 * np.exp(np.cumsum(np.random.randn(n_bars) * 0.02))
    market_data = {"BTC/USDT": pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
        "open": closes, "high": closes, "low": closes, "close": closes,
        "volume": np.ones(n_bars),
    })}

    # Normal (dd_multiplier=1.0)
    r1 = allocate_positions(
        signals, balance, positions, regime_info, market_data, config,
        dd_multiplier=1.0,
    )
    size_normal = r1["BTC/USDT"]["size_usdt"]

    # Reduced (dd_multiplier=0.75)
    r2 = allocate_positions(
        signals, balance, positions, regime_info, market_data, config,
        dd_multiplier=0.75,
    )
    size_reduced = r2["BTC/USDT"]["size_usdt"]

    ratio = size_reduced / size_normal
    assert abs(ratio - 0.75) < 0.01, f"Expected ratio ~0.75 got {ratio}"

    print("PASS: test_portfolio_dd_multiplier_reduces_sizing")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S")

    test_dd_multiplier_bands()
    test_hysteresis()
    test_peak_update()
    test_portfolio_dd_multiplier_zero()
    test_portfolio_dd_multiplier_reduces_sizing()

    print("\n===== ALL TESTS PASSED =====")
