"""
Tests v2.4.2 silent reconcile.
Valida que _reconcile_brain_after_execution:
- Dispara DEBUG [BRAIN_ROLLBACK_EXPECTED] para alloc FLAT.
- Dispara DEBUG [BRAIN_ROLLBACK_EXPECTED] para exec orders_failed.
- Dispara INFO [BRAIN_RECONCILE] para desincs reales (BingX cerro).
- Reset de 6 campos identico a v2.4.1.

Standalone (no pytest). Uso captura de logs via caplog-like pattern.
Run: python tests/test_silent_reconcile.py
"""
import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "live"))

# Capture logger records via custom handler
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []
    def emit(self, record):
        self.records.append((record.levelname, record.getMessage()))


@dataclass
class FakeSymbolState:
    position: int = 0
    entry_price: float = 0.0
    sl_level: float = 0.0
    stop_order_id: str = ""
    entry_filters_forming: int = 0
    entry_timestamp_ms: int = 0


@dataclass
class FakeBrain:
    symbol_state: dict = field(default_factory=dict)


@dataclass
class FakeExecReport:
    orders_failed: list = field(default_factory=list)
    positions_closed: list = field(default_factory=list)


class FakeEngine:
    """Minimal stand-in para LiveEngine que permite llamar al metodo
    _reconcile_brain_after_execution con mocks. Re-usa la impl real."""
    def __init__(self, brain, real_positions, dry_run=False):
        self.brain = brain
        self._real_positions = real_positions
        self.config = type("C", (), {"dry_run": dry_run})()
        self.exchange = None  # no usado por el patch


async def _run_reconcile(engine, exec_report, allocations):
    """Invoca la funcion real de live_engine con patches."""
    import live.live_engine as le

    _captured = {}

    async def _fake_get_open_positions(**kwargs):
        return engine._real_positions

    # Patch get_open_positions a nivel de modulo
    orig = le.get_open_positions
    le.get_open_positions = _fake_get_open_positions
    try:
        method = le.LiveEngine._reconcile_brain_after_execution
        await method(engine, exec_report, {}, allocations)
    finally:
        le.get_open_positions = orig


def _assert_reset(state, label):
    assert state.position == 0, f"{label}: position not reset ({state.position})"
    assert state.entry_price == 0.0, f"{label}: entry_price not reset"
    assert state.sl_level == 0.0, f"{label}: sl_level not reset"
    assert state.stop_order_id == "", f"{label}: stop_order_id not reset"
    assert state.entry_filters_forming == 0, f"{label}: filters not reset"
    assert state.entry_timestamp_ms == 0, f"{label}: ts_ms not reset"


def _setup_handler():
    logger = logging.getLogger("live.live_engine")
    logger.setLevel(logging.DEBUG)
    h = ListHandler()
    logger.addHandler(h)
    return h, logger


def _cleanup_handler(logger, h):
    logger.removeHandler(h)


def test_rollback_esperado_portfolio_flat():
    """Portfolio descarta con action=FLAT -> DEBUG [BRAIN_ROLLBACK_EXPECTED]."""
    brain = FakeBrain(symbol_state={
        "UNI/USDT": FakeSymbolState(
            position=-1, entry_price=3.25, sl_level=3.38,
            stop_order_id="stopid", entry_filters_forming=7,
            entry_timestamp_ms=1234567890,
        )
    })
    real_positions = {}  # BingX no tiene
    allocations = {"UNI/USDT": {"action": "FLAT", "reason": "low_confidence"}}
    exec_report = FakeExecReport()
    engine = FakeEngine(brain, real_positions)
    h, logger = _setup_handler()
    try:
        asyncio.run(_run_reconcile(engine, exec_report, allocations))
        levels = [lvl for lvl, _ in h.records]
        msgs = [m for _, m in h.records]
        debug_rollback = any(
            lvl == "DEBUG" and "BRAIN_ROLLBACK_EXPECTED" in m
            for lvl, m in h.records
        )
        info_reconcile = any(
            lvl == "INFO" and "BRAIN_RECONCILE" in m and "UNI/USDT" in m
            for lvl, m in h.records
        )
        assert debug_rollback, f"no DEBUG BRAIN_ROLLBACK_EXPECTED; records={h.records}"
        assert not info_reconcile, f"unexpected INFO BRAIN_RECONCILE; records={h.records}"
        _assert_reset(brain.symbol_state["UNI/USDT"], "flat_rollback")
        print("  [OK] rollback_esperado_portfolio_flat")
    finally:
        _cleanup_handler(logger, h)


def test_rollback_esperado_execution_failed():
    """Execution falla con orders_failed -> DEBUG [BRAIN_ROLLBACK_EXPECTED]."""
    brain = FakeBrain(symbol_state={
        "ETH/USDT": FakeSymbolState(
            position=1, entry_price=2310.0, sl_level=2240.0,
            stop_order_id="stopid", entry_filters_forming=5,
            entry_timestamp_ms=1234567890,
        )
    })
    real_positions = {}
    allocations = {"ETH/USDT": {"action": "LONG"}}  # paso filter
    exec_report = FakeExecReport(orders_failed=[{"symbol": "ETH/USDT", "error": "below min"}])
    engine = FakeEngine(brain, real_positions)
    h, logger = _setup_handler()
    try:
        asyncio.run(_run_reconcile(engine, exec_report, allocations))
        debug_rollback = any(
            lvl == "DEBUG" and "BRAIN_ROLLBACK_EXPECTED" in m and "ETH/USDT" in m
            for lvl, m in h.records
        )
        info_reconcile = any(
            lvl == "INFO" and "BRAIN_RECONCILE" in m and "ETH/USDT" in m
            for lvl, m in h.records
        )
        assert debug_rollback, f"no DEBUG rollback; records={h.records}"
        assert not info_reconcile, f"unexpected INFO reconcile; records={h.records}"
        _assert_reset(brain.symbol_state["ETH/USDT"], "exec_failed_rollback")
        print("  [OK] rollback_esperado_execution_failed")
    finally:
        _cleanup_handler(logger, h)


def test_desync_real_log_info():
    """BingX cerro entre ciclos (no en FLAT ni failed) -> INFO [BRAIN_RECONCILE]."""
    brain = FakeBrain(symbol_state={
        "OP/USDT": FakeSymbolState(
            position=1, entry_price=0.123, sl_level=0.117,
            stop_order_id="stopid", entry_filters_forming=3,
            entry_timestamp_ms=1234567890,
        )
    })
    real_positions = {}  # BingX no tiene (cerro por SL intrabar)
    allocations = {}  # ni FLAT ni activo, no aparece
    exec_report = FakeExecReport()
    engine = FakeEngine(brain, real_positions)
    h, logger = _setup_handler()
    try:
        asyncio.run(_run_reconcile(engine, exec_report, allocations))
        info_reconcile = any(
            lvl == "INFO" and "BRAIN_RECONCILE" in m and "OP/USDT" in m
            for lvl, m in h.records
        )
        debug_rollback = any(
            lvl == "DEBUG" and "BRAIN_ROLLBACK_EXPECTED" in m and "OP/USDT" in m
            for lvl, m in h.records
        )
        assert info_reconcile, f"no INFO reconcile; records={h.records}"
        assert not debug_rollback, f"unexpected DEBUG; records={h.records}"
        _assert_reset(brain.symbol_state["OP/USDT"], "real_desync")
        print("  [OK] desync_real_log_info")
    finally:
        _cleanup_handler(logger, h)


def test_reset_fields_identical_v241():
    """Los 6 campos reseteados post-reconcile deben coincidir con v2.4.1."""
    brain = FakeBrain(symbol_state={
        "SEI/USDT": FakeSymbolState(
            position=-1, entry_price=0.25, sl_level=0.26,
            stop_order_id="abc", entry_filters_forming=15,
            entry_timestamp_ms=9999,
        )
    })
    real_positions = {}
    allocations = {"SEI/USDT": {"action": "FLAT", "reason": "low_confidence"}}
    exec_report = FakeExecReport()
    engine = FakeEngine(brain, real_positions)
    h, logger = _setup_handler()
    try:
        asyncio.run(_run_reconcile(engine, exec_report, allocations))
        s = brain.symbol_state["SEI/USDT"]
        # Exactos 6 campos del v2.4.1 reset:
        assert s.position == 0
        assert s.entry_price == 0.0
        assert s.sl_level == 0.0
        assert s.stop_order_id == ""
        assert s.entry_filters_forming == 0
        assert s.entry_timestamp_ms == 0
        print("  [OK] reset_fields_identical_v241")
    finally:
        _cleanup_handler(logger, h)


if __name__ == "__main__":
    print("=== Tests v2.4.2 silent reconcile ===")
    test_rollback_esperado_portfolio_flat()
    test_rollback_esperado_execution_failed()
    test_desync_real_log_info()
    test_reset_fields_identical_v241()
    print("=== 4/4 PASS ===")
