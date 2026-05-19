"""Tests Fase D.5.1 — AutomationOrchestrator real-compute hookup RECICLAJE.

Mock launcher + waiter to avoid actual subprocess spawning during tests.

Coverage:
- D51.1: per-sym launches subprocess + marks sym done on DONE_SUCCESS (primary-source verified).
- D51.2: requires fase_actual == RECICLAJE.
- D51.3: subprocess CRASHED -> Tier 3 PAUSE + Caveat #14 halt remaining sym.
- D51.4: subprocess BUGCHECK -> Tier 3 PAUSE.
- D51.5: subprocess DONE_PARTIAL -> Tier 3 PAUSE.
- D51.6: DONE_SUCCESS but primary-source MISSING -> Tier 3 PAUSE (Caveat #15).
- D51.7: sequential strict — launcher invoked exactly once per sym (not parallel).
- D51.8: state persisted with active_subprocess record + popped on success.
- D51.9: all 5 sym DONE -> Tier 2 announce.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pytest

import automation_orchestrator as ao


# Minimal stub mimicking compute_runner.RunHandle + CompletionStatus
@dataclass
class _StubHandle:
    pid: int
    cmd: List[str]
    log_path: Path
    err_path: Path
    expected_outputs: List[Path]
    start_time: float = 0.0
    initial_bugcheck_count: int = 0
    label: str = ""


class _StubStatus:
    """Enum-like stub matching compute_runner.CompletionStatus shape."""
    DONE_SUCCESS = "DONE_SUCCESS"
    DONE_PARTIAL = "DONE_PARTIAL"
    CRASHED = "CRASHED"
    BUGCHECK = "BUGCHECK"
    TIMEOUT = "TIMEOUT"
    RUNNING = "RUNNING"


def _stub_status(value: str):
    class _S:
        pass
    s = _S()
    s.value = value
    return s


def _make_launcher(captured_calls: list, pid_seq: Optional[List[int]] = None):
    """Launcher that records each call and returns a stub handle with predictable pid."""
    counter = {"i": 0}

    def _launch(*, symbol, chunk_size, log_path, err_path, from_step=None):
        captured_calls.append({
            "symbol": symbol,
            "chunk_size": chunk_size,
            "log_path": log_path,
            "err_path": err_path,
            "from_step": from_step,
        })
        pid = pid_seq[counter["i"]] if pid_seq and counter["i"] < len(pid_seq) else 1000 + counter["i"]
        counter["i"] += 1
        return _StubHandle(
            pid=pid,
            cmd=[],
            log_path=Path(log_path),
            err_path=Path(err_path),
            expected_outputs=[Path("regime_wf") / f"{symbol}_specialist_configs.json"],
        )
    return _launch


def _make_waiter(status_sequence: list):
    """Waiter that pops successive statuses from a list."""
    def _wait(handle, *, poll_interval, timeout, on_poll=None):
        next_val = status_sequence.pop(0)
        return _stub_status(next_val)
    return _wait


def _build_orch_at_reciclaje(tmp_path: Path, grupo_id: int = 2,
                              symbols=None) -> ao.AutomationOrchestrator:
    """Helper: build orchestrator advanced to RECICLAJE state for grupo_id."""
    if symbols is None:
        symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    orch.declare_grupo(grupo_id, symbols)
    orch.state["grupo_actual"] = grupo_id
    orch.transition(ao.STATE_RECICLAJE, note="test_start_reciclaje")
    return orch


def _create_primary_sources(tmp_path: Path, symbols: List[str]) -> None:
    """Create fake regime_wf/{sym}_specialist_configs.json for Caveat #15 verify."""
    rwf = tmp_path / "regime_wf"
    rwf.mkdir(exist_ok=True)
    for sym in symbols:
        (rwf / f"{sym}_specialist_configs.json").write_text("{}")


# -----------------------------------------------------------------------------
# D51.1: per-sym launches subprocess + marks sym done on DONE_SUCCESS
# -----------------------------------------------------------------------------

def test_d51_1_per_sym_launches_marks_done(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    captured = []
    launcher = _make_launcher(captured)
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 5)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    assert sorted(grupo["sym_done_grupo_N"]) == sorted(symbols)
    assert grupo["sym_pending_grupo_N"] == []
    assert len(captured) == 5
    # Verify per-sym launches received the right sym
    launched_syms = [c["symbol"] for c in captured]
    assert sorted(launched_syms) == sorted(symbols)


# -----------------------------------------------------------------------------
# D51.2: requires fase_actual == RECICLAJE
# -----------------------------------------------------------------------------

def test_d51_2_requires_fase_reciclaje(tmp_path):
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    orch.declare_grupo(2, symbols)
    # State == IDLE (not RECICLAJE)
    assert orch.state["fase_actual"] == ao.STATE_IDLE

    with pytest.raises(ao.OrchestratorError):
        orch.run_reciclaje_real_compute(
            2, launcher=_make_launcher([]), waiter=_make_waiter([])
        )


# -----------------------------------------------------------------------------
# D51.3: subprocess CRASHED -> Tier 3 PAUSE + Caveat #14 halt remaining sym
# -----------------------------------------------------------------------------

def test_d51_3_crashed_tier3_halt_remaining(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    captured = []
    launcher = _make_launcher(captured)
    # First sym succeeds, second crashes -> halt remaining
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS, _StubStatus.CRASHED])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    # First sym done, second NOT done
    assert "ONDOUSDT" in grupo["sym_done_grupo_N"]
    assert "RENDERUSDT" not in grupo["sym_done_grupo_N"]
    # Caveat #14: remaining 3 syms NOT launched
    assert len(captured) == 2, f"Expected exactly 2 launches (ONDO+RENDER), got {len(captured)}"
    # Tier 3 gate raised
    assert orch.state["tier3_gate_pending"] is True
    assert grupo["tier3_gate_pending"] is True
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert len(tier3) == 1
    assert tier3[0].context["status"] == "CRASHED"
    assert tier3[0].context["symbol"] == "RENDERUSDT"


# -----------------------------------------------------------------------------
# D51.4: subprocess BUGCHECK -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d51_4_bugcheck_tier3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    launcher = _make_launcher([])
    waiter = _make_waiter([_StubStatus.BUGCHECK])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert tier3[0].context["status"] == "BUGCHECK"
    assert orch.state["tier3_gate_pending"] is True


# -----------------------------------------------------------------------------
# D51.5: subprocess DONE_PARTIAL -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d51_5_partial_outputs_tier3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    launcher = _make_launcher([])
    waiter = _make_waiter([_StubStatus.DONE_PARTIAL])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    assert grupo["sym_done_grupo_N"] == []  # nothing marked done
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert tier3[0].context["status"] == "DONE_PARTIAL"


# -----------------------------------------------------------------------------
# D51.6: DONE_SUCCESS but primary-source MISSING -> Tier 3 PAUSE (Caveat #15)
# -----------------------------------------------------------------------------

def test_d51_6_done_success_primary_missing_tier3_caveat15(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    # NO primary sources created -> regime_wf/ doesn't exist
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    launcher = _make_launcher([])
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    assert grupo["sym_done_grupo_N"] == []  # primary-source missing -> NOT marked done
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert len(tier3) == 1
    assert "primary-source" in tier3[0].message.lower() or "missing" in tier3[0].message.lower()


# -----------------------------------------------------------------------------
# D51.7: sequential strict — launcher invoked exactly once per sym
# -----------------------------------------------------------------------------

def test_d51_7_sequential_strict_one_call_per_sym(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    captured = []
    launcher = _make_launcher(captured)
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 5)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    # Each sym launched exactly once
    syms_launched = [c["symbol"] for c in captured]
    assert len(syms_launched) == 5
    assert len(set(syms_launched)) == 5  # all unique
    assert sorted(syms_launched) == sorted(symbols)


# -----------------------------------------------------------------------------
# D51.8: state persisted with active_subprocess record + popped on success
# -----------------------------------------------------------------------------

def test_d51_8_active_subprocess_record_lifecycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    captured = []
    launcher = _make_launcher(captured, pid_seq=[2001, 2002, 2003, 2004, 2005])
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 5)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    # After all done, active_subprocess should be empty (each popped on success)
    active = grupo.get("active_subprocess", {})
    reciclaje_active = {k: v for k, v in active.items() if k.startswith("RECICLAJE_")}
    assert reciclaje_active == {}, f"active_subprocess RECICLAJE entries not cleaned: {reciclaje_active}"


# -----------------------------------------------------------------------------
# D51.9: all 5 sym DONE -> Tier 2 announce
# -----------------------------------------------------------------------------

def test_d51_9_all_sym_done_tier2_announce(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    launcher = _make_launcher([])
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 5)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    # Tier 2 final announce (RECICLAJE_GRUPO_N all 5 sym DONE)
    tier2_announce = [r for r in reports
                       if r.tier == ao.TIER_2
                       and "all 5 sym DONE" in r.message]
    assert len(tier2_announce) == 1
    assert orch.state["tier3_gate_pending"] is False

    # State should still be RECICLAJE — caller drives transition to CROSS_CLASS
    assert orch.state["fase_actual"] == ao.STATE_RECICLAJE
