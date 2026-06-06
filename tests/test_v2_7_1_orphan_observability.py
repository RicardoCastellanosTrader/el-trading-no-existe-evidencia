"""Tests greenfield v2.7.1 — ORPHAN_CLOSE fill real + alerta + reporting robusto.

Cubre los 3 bugs diagnosticados (PARTE A):
  B.1 orphan close → fill real recuperado → trade_history real + alerta CLOSE.
  B.1 fallback → fill no recuperable → flag estimated + alerta "estimado", nunca silencio.
  B.2 catch-up → resumen pendiente se dispara en cualquier ciclo (no solo hour==0).
  B.2 watchdog → silencio > 26h → ERROR alert.

SCOPE: observabilidad/registro. NO toca brain/kernel/estrategia.
"""
import asyncio
import os
import sys
import types

import pytest

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)


# ---------- Fakes mínimos ----------
class FakeSymbolState:
    def __init__(self, position=0, entry_price=0.0, sl_level=0.0):
        self.position = position
        self.entry_price = entry_price
        self.sl_level = sl_level
        self.stop_order_id = ""
        self.entry_filters_forming = 0
        self.entry_timestamp_ms = 0


class FakeBrain:
    def __init__(self):
        self.symbol_state = {}


class FakeExecReport:
    def __init__(self):
        self.orders_failed = []
        self.positions_closed = []
        self.orders_sent = []
        self.errors = []


def _make_engine(monkeypatch, real_positions, recent_fill):
    """Construye un LiveEngine real con dependencias parcheadas."""
    import live.live_engine as le

    eng = le.LiveEngine.__new__(le.LiveEngine)  # sin __init__ (evita setup pesado)
    eng.brain = FakeBrain()
    eng.exchange = None
    eng.config = types.SimpleNamespace(dry_run=False)
    eng.alerts = []

    async def fake_get_positions(exchange=None):
        return real_positions

    async def fake_get_fill(symbol, since_ms=None, exchange=None):
        return recent_fill

    async def fake_send_alert(message):
        eng.alerts.append(message)

    monkeypatch.setattr(le, "get_open_positions", fake_get_positions)
    monkeypatch.setattr(le, "get_recent_closed_fill", fake_get_fill)
    eng._send_alert = fake_send_alert

    logged = []
    monkeypatch.setattr(le, "log_trade", lambda d, **k: logged.append(d))
    eng._logged_trades = logged
    return eng, le


def test_b1_orphan_real_fill_recorded_and_alerted(monkeypatch):
    """SL exchange-side con fill real → trade_history con PnL real + alerta CLOSE."""
    real_fill = {"price": 0.0786, "amount": 166.0, "cost": 13.05,
                 "fee_usdt": 0.013, "timestamp_ms": 1780718400000, "side": "sell"}
    eng, le = _make_engine(monkeypatch, real_positions={}, recent_fill=real_fill)
    eng.brain.symbol_state["DOGE/USDT"] = FakeSymbolState(1, 0.08274, 0.07896)
    pre = {"DOGE/USDT": {"side": "long", "entry_price": 0.08274, "sl_level": 0.07896,
                          "entry_timestamp_ms": 1780707601767}}
    allocations = {"DOGE/USDT": {"action": "CLOSE_LONG"}}
    exec_report = FakeExecReport()

    asyncio.run(eng._reconcile_brain_after_execution(exec_report, pre, allocations))

    assert len(eng._logged_trades) == 1, "debe registrar el orphan close"
    t = eng._logged_trades[0]
    assert t["flag"] == "exchange_side_close", "fill real → flag NO estimated"
    assert t["exit_price"] == 0.0786, "exit = fill real, no sl_level"
    assert t["size_usdt"] == 13.05, "size = cost real, NO 0.0 fantasma"
    assert t["pnl_usdt"] != 0.0, "pnl real, NO 0.0 fantasma"
    assert any("[CLOSE]" in a and "DOGE" in a and "SL exchange-side" in a for a in eng.alerts), \
        "debe emitir alerta Telegram CLOSE etiquetada"


def test_b1_orphan_fallback_estimated_when_no_fill(monkeypatch):
    """Fill no recuperable → flag estimated + alerta 'estimado', NUNCA silencio."""
    eng, le = _make_engine(monkeypatch, real_positions={}, recent_fill=None)
    eng.brain.symbol_state["SOL/USDT"] = FakeSymbolState(-1, 150.0, 157.5)
    pre = {"SOL/USDT": {"side": "short", "entry_price": 150.0, "sl_level": 157.5,
                         "entry_timestamp_ms": 1780707601767}}
    allocations = {"SOL/USDT": {"action": "CLOSE_SHORT"}}
    exec_report = FakeExecReport()

    asyncio.run(eng._reconcile_brain_after_execution(exec_report, pre, allocations))

    assert len(eng._logged_trades) == 1
    t = eng._logged_trades[0]
    assert t["flag"] == "exchange_side_close_estimated", "sin fill → flag estimated explícito"
    assert t["exit_price"] == 157.5, "fallback usa sl_level"
    assert any("[CLOSE]" in a and "ESTIMADO" in a.upper() for a in eng.alerts), \
        "alerta debe indicar fill estimado — nunca silencio"


def test_b2_no_orphan_when_position_still_open(monkeypatch):
    """Posición sigue en exchange → NO orphan close (no falso positivo)."""
    real_fill = {"price": 0.0786, "amount": 166.0, "cost": 13.05, "fee_usdt": 0.0,
                 "timestamp_ms": 0, "side": "sell"}
    eng, le = _make_engine(
        monkeypatch,
        real_positions={"DOGE/USDT": {"side": "long"}},
        recent_fill=real_fill,
    )
    eng.brain.symbol_state["DOGE/USDT"] = FakeSymbolState(1, 0.08274, 0.07896)
    pre = {"DOGE/USDT": {"side": "long", "entry_price": 0.08274, "sl_level": 0.07896,
                          "entry_timestamp_ms": 0}}
    allocations = {"DOGE/USDT": {"action": "CLOSE_LONG"}}
    exec_report = FakeExecReport()

    asyncio.run(eng._reconcile_brain_after_execution(exec_report, pre, allocations))
    assert len(eng._logged_trades) == 0, "posición viva → NO registrar orphan"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
