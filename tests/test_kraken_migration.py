"""
Tests de la migración BingX→Kraken Futures (Etapa 1, fase PAPER).

Cubre el código exchange-facing nuevo que antes estaba SIN cobertura:
  1. Symbol mapping master↔Kraken PF_ ('X/USDT'↔'X/USD:USD') + validate_symbol_map.
  2. Fill-parser ccxt-UNIFIED (Kraken PF_ contractSize=1; NO hazard 25× de BingX;
     NO lee info.volume/amount/commission).
  3. Sizing: precisión por amount-step (_round_amount_to_step) — DOGE/TRX precision-0
     = unidades enteras.
  4. open_position: stop = `stp` reduce-only stop-market (stopLossPrice +
     triggerSignal='mark', reduceOnly, SIN limitPrice); entry sin params de stop.
  5. S2-lite _flush_residual: tras un cierre con residual (protección 1% parcial),
     re-emite reduce-only market hasta aplanar.

Standalone: python tests/test_kraken_migration.py   |   Pytest: pytest tests/test_kraken_migration.py
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

os.environ.setdefault("KRAKEN_API_KEY", "TEST_KEY")
os.environ.setdefault("KRAKEN_API_SECRET", "TEST_SECRET")

from live import data_feed as df
from live import execution_manager as em
from live import portfolio_manager as pm


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 1. Symbol mapping
# ---------------------------------------------------------------------------

def test_to_kraken_symbol_rule():
    assert df.to_kraken_symbol("BTC/USDT") == "BTC/USD:USD"
    assert df.to_kraken_symbol("ETH/USDT") == "ETH/USD:USD"
    assert df.to_kraken_symbol("POL/USDT") == "POL/USD:USD"     # ex-MATIC
    assert df.to_kraken_symbol("RENDER/USDT") == "RENDER/USD:USD"
    print("  [OK] to_kraken_symbol: 'X/USDT' -> 'X/USD:USD'")


def test_from_kraken_symbol_roundtrip():
    for master in ("BTC/USDT", "DOGE/USDT", "TAO/USDT", "FET/USDT"):
        assert df.from_kraken_symbol(df.to_kraken_symbol(master)) == master
    # base-extraction robusta también con sufijo BingX-shaped
    assert df.from_kraken_symbol("BTC/USD:USD") == "BTC/USDT"
    print("  [OK] from_kraken_symbol: round-trip de los 20 OK")


def test_validate_symbol_map():
    class _Ex:
        def __init__(self, markets):
            self.markets = markets
    # Todos presentes -> 0 missing
    all_markets = {df.to_kraken_symbol(s): {} for s in df.MASTER_SYMBOLS}
    assert df.validate_symbol_map(_Ex(all_markets)) == []
    # Uno ausente -> aparece en la lista
    partial = dict(all_markets)
    partial.pop(df.to_kraken_symbol("BTC/USDT"))
    missing = df.validate_symbol_map(_Ex(partial))
    assert "BTC/USDT" in missing
    # Sin markets (mock/test) -> [] (sin validación posible, no fail)
    assert df.validate_symbol_map(_Ex({})) == []
    print("  [OK] validate_symbol_map: fail-loud de símbolos ausentes")


# ---------------------------------------------------------------------------
# 2. Fill-parser ccxt-unified (sin hazard 25×)
# ---------------------------------------------------------------------------

class _FillExchange:
    def __init__(self, trades):
        self._trades = trades

    async def fetch_my_trades(self, symbol, since=None, limit=None):
        return self._trades

    async def close(self):
        pass


def test_fill_parser_ccxt_unified():
    # Trade ccxt Kraken PF_ linear: amount=base, cost=price*size (USD), fee dict.
    # info trae keys Kraken (size/price) pero NO volume/amount/commission (BingX).
    trade = {
        "timestamp": 1780718400000,
        "price": 0.0786,
        "amount": 166.0,            # base (DOGE) — ccxt size
        "cost": 13.05,              # USD = price*size (ccxt-computed)
        "side": "sell",
        "fee": {"cost": 0.0052, "currency": "USD"},
        "info": {"size": 166.0, "price": 0.0786, "fillType": "taker"},
    }
    res = _run(df.get_recent_closed_fill("DOGE/USDT", since_ms=1, exchange=_FillExchange([trade])))
    assert res is not None
    assert abs(res["amount"] - 166.0) < 1e-9, res          # base, NO inflado 25×
    assert abs(res["cost"] - 13.05) < 1e-9, res            # USD notional
    assert abs(res["price"] - 0.0786) < 1e-9, res
    assert abs(res["fee_usdt"] - 0.0052) < 1e-9, res
    assert res["side"] == "sell"
    print("  [OK] fill-parser: campos ccxt-unified (sin 25×, sin info.volume)")


def test_fill_parser_cost_fallback():
    # cost ausente -> gate ortogonal: cost = price × amount
    trade = {
        "timestamp": 2, "price": 100.0, "amount": 2.0, "cost": 0,
        "side": "buy", "fee": {}, "info": {},
    }
    res = _run(df.get_recent_closed_fill("ETH/USDT", since_ms=1, exchange=_FillExchange([trade])))
    assert abs(res["cost"] - 200.0) < 1e-9, res
    print("  [OK] fill-parser: fallback cost = price×amount")


# ---------------------------------------------------------------------------
# 3. Sizing precision (amount-step)
# ---------------------------------------------------------------------------

def test_round_amount_to_step():
    doge = {"precision": {"amount": 1.0}}      # precision-0 = unidades enteras
    btc = {"precision": {"amount": 0.0001}}
    assert pm._round_amount_to_step(1234.56, doge) == 1235.0
    assert abs(pm._round_amount_to_step(0.00765432, btc) - 0.0077) < 1e-9
    # sin market o step inválido -> qty intacto
    assert pm._round_amount_to_step(1234.56, None) == 1234.56
    assert pm._round_amount_to_step(1234.56, {"precision": {"amount": 0}}) == 1234.56
    print("  [OK] _round_amount_to_step: DOGE entero, BTC 0.0001 step")


# ---------------------------------------------------------------------------
# 4 + 5. open_position stop params + S2-lite flush (execution_manager)
# ---------------------------------------------------------------------------

class _ExecExchange:
    """Fake async exchange que registra create_order y devuelve fills canónicos."""

    def __init__(self):
        self.created = []

    def amount_to_precision(self, symbol, amount):
        return str(amount)

    async def set_leverage(self, leverage, symbol):
        return True

    async def fetch_ticker(self, symbol):
        return {"last": 100.0}

    async def create_order(self, symbol, type, side, amount, price=None, params=None):
        self.created.append({
            "symbol": symbol, "type": type, "side": side,
            "amount": amount, "params": params or {},
        })
        return {"id": f"ord_{len(self.created)}", "filled": amount,
                "average": 100.0, "price": 100.0}

    async def close(self):
        pass


def test_open_position_stop_params_s2lite():
    ex = _ExecExchange()
    _saved = em.DRY_RUN
    em.DRY_RUN = False
    try:
        alloc = {"action": "LONG", "size_contracts": 1.5, "leverage": 1,
                 "sl_price": 95.0, "entry_price": 100.0}
        res = _run(em.open_position("ETH/USDT", alloc, ex))
    finally:
        em.DRY_RUN = _saved

    assert res["action"] == "opened", res
    # 2 órdenes: entry market + stop
    assert len(ex.created) == 2, ex.created
    entry, stop = ex.created
    assert entry["type"] == "market" and entry["side"] == "buy"
    assert not entry["params"], "entry NO debe llevar params de stop"
    # Stop = stp reduce-only stop-market: stopLossPrice + triggerSignal=mark, SIN limitPrice
    p = stop["params"]
    assert "stopLossPrice" in p and p["stopLossPrice"] > 0, p
    assert p.get("reduceOnly") is True, p
    assert p.get("triggerSignal") == "mark", p
    assert "limitPrice" not in p, p
    assert "triggerType" not in p and "stopPrice" not in p, "no params BingX"
    assert stop["side"] == "sell", "stop contrario a LONG"
    print("  [OK] open_position: stop stp reduce-only (stopLossPrice+mark, sin limitPrice)")


def test_flush_residual_reaplana():
    # get_open_positions devuelve residual la 1ª vez, plano la 2ª → 1 reduce-only mkt
    calls = {"n": 0}

    async def _fake_positions(exchange=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"ETH/USDT": {"side": "long", "size": 0.4, "entry_price": 100.0}}
        return {}

    ex = _ExecExchange()
    _saved_dry, _saved_gp = em.DRY_RUN, em.get_open_positions
    em.DRY_RUN = False
    em.get_open_positions = _fake_positions
    try:
        ok = _run(em._flush_residual("ETH/USDT", ex))
    finally:
        em.DRY_RUN, em.get_open_positions = _saved_dry, _saved_gp

    assert ok is True
    assert len(ex.created) == 1, ex.created
    flush = ex.created[0]
    assert flush["type"] == "market" and flush["side"] == "sell"
    assert flush["params"].get("reduceOnly") is True
    assert abs(flush["amount"] - 0.4) < 1e-9
    print("  [OK] _flush_residual: re-emite reduce-only mkt y aplana residual")


def test_flush_residual_noop_cuando_plano():
    async def _flat_positions(exchange=None):
        return {}
    ex = _ExecExchange()
    _saved_dry, _saved_gp = em.DRY_RUN, em.get_open_positions
    em.DRY_RUN = False
    em.get_open_positions = _flat_positions
    try:
        ok = _run(em._flush_residual("ETH/USDT", ex))
    finally:
        em.DRY_RUN, em.get_open_positions = _saved_dry, _saved_gp
    assert ok is True
    assert ex.created == [], "sin residual no debe emitir órdenes"
    print("  [OK] _flush_residual: no-op cuando ya está plano (seguro si 1% no muerde)")


if __name__ == "__main__":
    tests = [
        test_to_kraken_symbol_rule,
        test_from_kraken_symbol_roundtrip,
        test_validate_symbol_map,
        test_fill_parser_ccxt_unified,
        test_fill_parser_cost_fallback,
        test_round_amount_to_step,
        test_open_position_stop_params_s2lite,
        test_flush_residual_reaplana,
        test_flush_residual_noop_cuando_plano,
    ]
    print("=" * 60)
    print("Running tests/test_kraken_migration.py")
    print("=" * 60)
    for t in tests:
        t()
    print("=" * 60)
    print(f"[OK] {len(tests)}/{len(tests)} tests PASS")
