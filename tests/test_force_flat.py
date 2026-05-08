"""
Tests greenfield admin script live/force_flat.py.

Cover:
  1. Dry-run sin --confirm: 0 ejecuciones close/cancel + state listado correcto.
  2. --confirm con 0 posiciones + 0 órdenes: idempotente exit 0 sin acciones.
  3. --confirm con N=3 posiciones mock: N close_position calls + verificación post-close empty.
  4. Individual close fail: continúa procesando otros sym + reporta failure + exit 1.

Standalone runnable: python tests/test_force_flat.py
Pytest collectable: pytest tests/test_force_flat.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_root = _here.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Setear creds dummy para que _create_bingx_exchange (parcheado) no falle
# si por algun motivo se llamara a la version real durante import.
os.environ.setdefault("BINGX_API_KEY", "TEST_KEY")
os.environ.setdefault("BINGX_API_SECRET", "TEST_SECRET")

from live import force_flat as ff  # noqa: E402


class _FakeExchange:
    """Exchange placeholder con close() async para satisfacer finally clause."""

    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


class _Stub:
    """Container de fixtures + counters mutables compartidos cross async calls."""

    def __init__(self, positions, orders):
        # Estado simulado del exchange. Las llamadas a close_position/cancel_order
        # mutan estos diccionarios para reflejar lo que pasa post-acción.
        self.positions = dict(positions)
        self.orders = list(orders)
        self.fetch_pos_calls = 0
        self.fetch_ord_calls = 0
        self.close_calls = []
        self.cancel_calls = []
        self.close_force_fail_for: set[str] = set()

    async def get_open_positions(self, exchange=None):
        self.fetch_pos_calls += 1
        return dict(self.positions)

    async def get_open_orders(self, exchange=None, symbol=None):
        self.fetch_ord_calls += 1
        return list(self.orders)

    async def close_position(self, symbol, position, exchange):
        self.close_calls.append(symbol)
        if symbol in self.close_force_fail_for:
            return {"symbol": symbol, "action": "close_failed", "error": "mocked failure"}
        # Éxito: eliminar de posiciones simuladas + remover stop_order vinculado
        self.positions.pop(symbol, None)
        stop_id = position.get("stop_order_id")
        if stop_id:
            self.orders = [o for o in self.orders if o.get("id") != stop_id]
        return {"symbol": symbol, "action": "closed", "side": position.get("side")}

    async def cancel_order(self, order_id, symbol, exchange):
        self.cancel_calls.append((symbol, order_id))
        self.orders = [o for o in self.orders if o.get("id") != order_id]
        return True


def _install_stub(stub: _Stub):
    """Patch module-level imports en live.force_flat con stub y _FakeExchange."""
    fake_exchange = _FakeExchange()
    ff._create_bingx_exchange = lambda: fake_exchange
    ff.get_open_positions = stub.get_open_positions
    ff.get_open_orders = stub.get_open_orders
    ff.close_position = stub.close_position
    ff.cancel_order = stub.cancel_order
    return fake_exchange


def _run(coro):
    return asyncio.run(coro)


def test_1_dry_run_no_execution():
    """Dry-run sin --confirm: lista state pero NO llama close/cancel."""
    positions = {
        "BTC/USDT": {
            "side": "long", "size": 0.01, "entry_price": 65000.0,
            "size_usdt": 650.0, "unrealized_pnl": 12.5, "leverage": 1,
            "stop_order_id": "stop_btc",
        },
    }
    orders = [
        {"id": "stop_btc", "symbol": "BTC/USDT", "type": "stop_market",
         "side": "sell", "amount": 0.01, "price": 63000.0},
    ]
    stub = _Stub(positions, orders)
    fake_ex = _install_stub(stub)

    rc = _run(ff.main_async(confirm=False))

    assert rc == 0, f"dry-run exit_code esperado=0 got={rc}"
    assert stub.close_calls == [], f"dry-run NO debe llamar close_position, got={stub.close_calls}"
    assert stub.cancel_calls == [], f"dry-run NO debe llamar cancel_order, got={stub.cancel_calls}"
    assert stub.fetch_pos_calls == 1, "dry-run debe leer positions una vez"
    assert stub.fetch_ord_calls == 1, "dry-run debe leer orders una vez"
    assert fake_ex.closed, "exchange.close() debe ejecutarse en finally"
    print("[PASS] Test 1 dry-run: no execution + state listed")


def test_2_confirm_idempotent_zero_state():
    """--confirm con 0 posiciones + 0 órdenes: idempotente exit 0 sin acciones."""
    stub = _Stub({}, [])
    fake_ex = _install_stub(stub)

    rc = _run(ff.main_async(confirm=True))

    assert rc == 0, f"idempotente exit_code esperado=0 got={rc}"
    assert stub.close_calls == [], f"NO close calls esperado, got={stub.close_calls}"
    assert stub.cancel_calls == [], f"NO cancel calls esperado, got={stub.cancel_calls}"
    # Solo 1 fetch (early return tras detectar empty state)
    assert stub.fetch_pos_calls == 1, f"1 fetch_positions esperado, got={stub.fetch_pos_calls}"
    assert stub.fetch_ord_calls == 1, f"1 fetch_orders esperado, got={stub.fetch_ord_calls}"
    assert fake_ex.closed, "exchange.close() debe ejecutarse"
    print("[PASS] Test 2 idempotente: 0 state -> 0 actions, exit 0")


def test_3_confirm_n_positions_close_all_ok():
    """--confirm con N=3 posiciones mock: 3 close_position calls + verification flat post."""
    positions = {
        "BTC/USDT": {
            "side": "long", "size": 0.01, "entry_price": 65000.0,
            "size_usdt": 650.0, "unrealized_pnl": 5.0, "leverage": 1,
            "stop_order_id": "stop_btc",
        },
        "ETH/USDT": {
            "side": "short", "size": 0.5, "entry_price": 3500.0,
            "size_usdt": 1750.0, "unrealized_pnl": -2.0, "leverage": 1,
            "stop_order_id": "stop_eth",
        },
        "SOL/USDT": {
            "side": "long", "size": 5.0, "entry_price": 180.0,
            "size_usdt": 900.0, "unrealized_pnl": 0.0, "leverage": 1,
            "stop_order_id": None,
        },
    }
    orders = [
        {"id": "stop_btc", "symbol": "BTC/USDT", "type": "stop_market",
         "side": "sell", "amount": 0.01, "price": 63000.0},
        {"id": "stop_eth", "symbol": "ETH/USDT", "type": "stop_market",
         "side": "buy", "amount": 0.5, "price": 3600.0},
    ]
    stub = _Stub(positions, orders)
    fake_ex = _install_stub(stub)

    rc = _run(ff.main_async(confirm=True))

    assert rc == 0, f"close_all_ok exit_code esperado=0 got={rc}"
    assert sorted(stub.close_calls) == ["BTC/USDT", "ETH/USDT", "SOL/USDT"], \
        f"3 close_position calls esperado, got={stub.close_calls}"
    # Stops linked se eliminan via close_position (mutación stub.orders).
    # Sweep phase encuentra orders_remaining vacío, 0 cancel calls.
    assert stub.cancel_calls == [], \
        f"sweep cancel calls esperado=0 (linked stops removed by close), got={stub.cancel_calls}"
    # Final verification: positions y orders empty
    assert stub.positions == {}, f"positions final empty esperado, got={stub.positions}"
    assert stub.orders == [], f"orders final empty esperado, got={stub.orders}"
    assert fake_ex.closed, "exchange.close() debe ejecutarse"
    print("[PASS] Test 3 close N=3 ok: 3 closes + flat final")


def test_4_individual_close_fail_continues_and_reports():
    """Individual close fail: continúa procesando otros + reporta failure + exit 1."""
    positions = {
        "BTC/USDT": {
            "side": "long", "size": 0.01, "entry_price": 65000.0,
            "size_usdt": 650.0, "unrealized_pnl": 5.0, "leverage": 1,
            "stop_order_id": "stop_btc",
        },
        "ETH/USDT": {
            "side": "short", "size": 0.5, "entry_price": 3500.0,
            "size_usdt": 1750.0, "unrealized_pnl": -2.0, "leverage": 1,
            "stop_order_id": "stop_eth",
        },
    }
    orders = [
        {"id": "stop_btc", "symbol": "BTC/USDT", "type": "stop_market",
         "side": "sell", "amount": 0.01, "price": 63000.0},
        {"id": "stop_eth", "symbol": "ETH/USDT", "type": "stop_market",
         "side": "buy", "amount": 0.5, "price": 3600.0},
    ]
    stub = _Stub(positions, orders)
    stub.close_force_fail_for = {"BTC/USDT"}  # BTC close falla, ETH OK
    fake_ex = _install_stub(stub)

    rc = _run(ff.main_async(confirm=True))

    # ETH cerrado OK, BTC falló → residual 1 position + 1 stop → exit 1
    assert rc == 1, f"con failure residual exit_code esperado=1 got={rc}"
    # AMBOS sym intentados (continúa tras fail)
    assert sorted(stub.close_calls) == ["BTC/USDT", "ETH/USDT"], \
        f"continuación tras fail: ambos sym intentados, got={stub.close_calls}"
    # Sweep: stop_btc residual → cancel intentado
    assert ("BTC/USDT", "stop_btc") in stub.cancel_calls, \
        f"sweep cancela stop_btc residual, got={stub.cancel_calls}"
    # ETH cerrada limpia → no en positions final; BTC residual permanece
    assert "ETH/USDT" not in stub.positions, "ETH cerrada"
    assert "BTC/USDT" in stub.positions, "BTC residual (close failed)"
    assert fake_ex.closed, "exchange.close() debe ejecutarse"
    print("[PASS] Test 4 partial fail: continúa + reporta + exit 1")


if __name__ == "__main__":
    tests = [
        test_1_dry_run_no_execution,
        test_2_confirm_idempotent_zero_state,
        test_3_confirm_n_positions_close_all_ok,
        test_4_individual_close_fail_continues_and_reports,
    ]
    print("=" * 60)
    print("Running tests/test_force_flat.py")
    print("=" * 60)
    for t in tests:
        t()
    print("=" * 60)
    print(f"[OK] {len(tests)}/{len(tests)} tests PASS")
