"""Tests para fix size_usdt en data_feed.get_open_positions.

Verifica que el dict retornado por get_open_positions incluye size_usdt
poblado desde notional (si BingX lo provee) o calculado desde
contracts * entry_price como fallback.

Contexto: bug historico detectado 2026-04-22, 134/135 trades con
size_usdt=0 en trade_history.csv porque el dict de posiciones no
incluia el campo.

Run: python tests/test_get_open_positions_size_usdt.py
"""
import asyncio
import logging
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Mock ccxt import antes de importar data_feed (data_feed importa ccxt)
# No necesitamos ccxt real, solo el namespace.
from live.data_feed import get_open_positions


class FakeExchange:
    """Mock minimo de ccxt exchange para test."""
    def __init__(self, positions_response, orders_response=None):
        self._positions = positions_response
        self._orders = orders_response or []

    async def fetch_positions(self):
        return self._positions

    async def fetch_open_orders(self, *a, **kw):
        return self._orders

    async def close(self):
        pass


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_size_usdt_from_notional_when_present():
    """BingX provee notional directo -> size_usdt = notional."""
    ex = FakeExchange([
        {
            "symbol": "BTC/USDT:USDT",
            "contracts": 0.1,
            "side": "long",
            "entryPrice": 50000.0,
            "notional": 5000.0,
            "unrealizedPnl": 100.0,
            "leverage": 2,
        }
    ])
    result = _run(get_open_positions(exchange=ex))
    assert "BTC/USDT" in result, f"BTC/USDT missing from result: {list(result.keys())}"
    assert result["BTC/USDT"]["size_usdt"] == 5000.0
    assert result["BTC/USDT"]["entry_price"] == 50000.0
    assert result["BTC/USDT"]["size"] == 0.1


def test_size_usdt_fallback_without_notional():
    """Sin notional -> size_usdt = contracts * entry_price."""
    ex = FakeExchange([
        {
            "symbol": "ETH/USDT:USDT",
            "contracts": 1.0,
            "side": "short",
            "entryPrice": 2300.0,
            # sin notional
            "unrealizedPnl": 0.0,
            "leverage": 1,
        }
    ])
    result = _run(get_open_positions(exchange=ex))
    assert result["ETH/USDT"]["size_usdt"] == 2300.0


def test_size_usdt_notional_zero_falls_back():
    """notional=0 -> fallback a size*entry (no respeta notional=0)."""
    ex = FakeExchange([
        {
            "symbol": "SOL/USDT:USDT",
            "contracts": 2.0,
            "side": "long",
            "entryPrice": 150.0,
            "notional": 0,
        }
    ])
    result = _run(get_open_positions(exchange=ex))
    assert result["SOL/USDT"]["size_usdt"] == 300.0


def test_size_usdt_notional_none_falls_back():
    """notional=None -> fallback."""
    ex = FakeExchange([
        {
            "symbol": "SOL/USDT:USDT",
            "contracts": 2.0,
            "side": "long",
            "entryPrice": 150.0,
            "notional": None,
        }
    ])
    result = _run(get_open_positions(exchange=ex))
    assert result["SOL/USDT"]["size_usdt"] == 300.0


def test_size_usdt_warning_when_entry_price_zero():
    """Edge case entry_price=0 sin notional -> size_usdt=0 + WARNING."""
    import io
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    df_logger = logging.getLogger("data_feed")
    df_logger.addHandler(handler)
    df_logger.setLevel(logging.WARNING)
    try:
        ex = FakeExchange([
            {
                "symbol": "X/USDT:USDT",
                "contracts": 5.0,
                "side": "long",
                "entryPrice": 0.0,
                "unrealizedPnl": 0.0,
            }
        ])
        result = _run(get_open_positions(exchange=ex))
        assert result["X/USDT"]["size_usdt"] == 0.0
        log_output = log_capture.getvalue()
        assert "size_usdt=0" in log_output, f"WARNING no emitido: {log_output!r}"
    finally:
        df_logger.removeHandler(handler)


def test_empty_positions_list():
    """fetch_positions retorna [] -> result vacio, sin crash."""
    ex = FakeExchange([])
    result = _run(get_open_positions(exchange=ex))
    assert result == {}


def test_contracts_zero_skipped():
    """Position con contracts=0 skipped (linea 329)."""
    ex = FakeExchange([
        {
            "symbol": "SKIP/USDT:USDT",
            "contracts": 0,
            "side": "long",
            "entryPrice": 100.0,
        },
        {
            "symbol": "KEEP/USDT:USDT",
            "contracts": 1.0,
            "side": "long",
            "entryPrice": 200.0,
            "notional": 200.0,
        },
    ])
    result = _run(get_open_positions(exchange=ex))
    assert "SKIP/USDT" not in result
    assert "KEEP/USDT" in result
    assert result["KEEP/USDT"]["size_usdt"] == 200.0


def test_multiple_positions_each_gets_size_usdt():
    """3 posiciones, cada una con size_usdt correcto (notional vs fallback)."""
    ex = FakeExchange([
        {"symbol": "A/USDT:USDT", "contracts": 1.0, "side": "long",
         "entryPrice": 100.0, "notional": 100.0},
        {"symbol": "B/USDT:USDT", "contracts": 2.0, "side": "short",
         "entryPrice": 50.0},  # fallback
        {"symbol": "C/USDT:USDT", "contracts": 0.5, "side": "long",
         "entryPrice": 1000.0, "notional": 500.0},
    ])
    result = _run(get_open_positions(exchange=ex))
    assert result["A/USDT"]["size_usdt"] == 100.0
    assert result["B/USDT"]["size_usdt"] == 100.0
    assert result["C/USDT"]["size_usdt"] == 500.0


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
