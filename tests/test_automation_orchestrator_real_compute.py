"""Tests Fase D.5.2 — AutomationOrchestrator real-compute hookup CROSS_CLASS.

Mock launcher + waiter to avoid actual subprocess spawning during tests.

Coverage:
- D52.1: PER_SYM_BASELINE skips compute, marks done if primary-source exists.
- D52.2: PER_SYM_BASELINE missing primary-source -> Tier 3 PAUSE.
- D52.3: BTC_SOURCE launches subprocess + marks done on DONE_SUCCESS.
- D52.4: ETH_SOURCE launches subprocess + marks done on DONE_SUCCESS.
- D52.5: subprocess CRASHED -> Tier 3 PAUSE + state persisted.
- D52.6: subprocess BUGCHECK -> Tier 3 PAUSE.
- D52.7: subprocess DONE_PARTIAL -> Tier 3 PAUSE.
- D52.8: sequential strict — launcher called once per option, not parallel.
- D52.9: requires fase_actual == CROSS_CLASS.
- D52.10: state persisted with active_subprocess record during run.
- D52.11: targets exclude source symbol from grupo.
"""
from __future__ import annotations

import json
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
    """Return object with .value attribute (mimics enum)."""
    class _S:
        pass
    s = _S()
    s.value = value
    return s


def _make_launcher(captured_calls: list, return_handle: _StubHandle):
    def _launch(*, source, target, output_root, log_path, err_path):
        captured_calls.append({
            "source": source,
            "target": target,
            "output_root": output_root,
            "log_path": log_path,
            "err_path": err_path,
        })
        return return_handle
    return _launch


def _make_waiter(status_sequence: list):
    """Returns a waiter that pops successive statuses from a list."""
    def _wait(handle, *, poll_interval, timeout, on_poll=None):
        # Convert raw string to stub status object
        next_val = status_sequence.pop(0)
        return _stub_status(next_val)
    return _wait


def _build_orch_at_cross_class(tmp_path: Path, grupo_id: int = 1,
                                 symbols=None) -> ao.AutomationOrchestrator:
    """Helper: build orchestrator advanced to CROSS_CLASS state for grupo_id."""
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    orch.declare_grupo(grupo_id, symbols)
    orch.transition(ao.STATE_RECICLAJE, note="test_start")
    # Mark all syms done
    for sym in symbols:
        orch.mark_sym_done(grupo_id, sym)
    orch.transition(ao.STATE_CROSS_CLASS, note="test_to_cross_class")
    return orch


# -----------------------------------------------------------------------------
# D52.1: PER_SYM_BASELINE skips compute, marks done if primary-source exists
# -----------------------------------------------------------------------------

def test_d52_1_per_sym_baseline_skips_compute_marks_done(tmp_path, monkeypatch):
    # Create fake regime_wf/{sym}_specialist_configs.json for all 5 sym
    rwf = tmp_path / "regime_wf"
    rwf.mkdir()
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    for sym in symbols:
        (rwf / f"{sym}_specialist_configs.json").write_text("{}")
    monkeypatch.chdir(tmp_path)
    orch = _build_orch_at_cross_class(tmp_path)
    # Override pending to PER_SYM_BASELINE first only
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["PER_SYM_BASELINE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS])

    reports = orch.run_cross_class_real_compute(1, launcher=launcher, waiter=waiter)
    assert "PER_SYM_BASELINE" in orch.state["grupos"]["1"]["cross_options_done"]
    assert len(launcher_calls) == 0, "PER_SYM_BASELINE must NOT invoke launcher"


# -----------------------------------------------------------------------------
# D52.2: PER_SYM_BASELINE missing primary-source -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d52_2_per_sym_baseline_missing_primary_source_tier3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # No regime_wf files created -> all missing
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["PER_SYM_BASELINE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([])  # not invoked

    reports = orch.run_cross_class_real_compute(1, launcher=launcher, waiter=waiter)
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert len(tier3) == 1
    assert "missing_files" in tier3[0].context
    assert orch.state["tier3_gate_pending"] is True


# -----------------------------------------------------------------------------
# D52.3: BTC_SOURCE launches subprocess + marks done on DONE_SUCCESS
# -----------------------------------------------------------------------------

def test_d52_3_btc_source_launches_subprocess_marks_done(tmp_path):
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["BTC_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    handle = _StubHandle(12345, [], Path("log.txt"), Path("err.txt"), [tmp_path / "ETH_btc"])
    launcher = _make_launcher(launcher_calls, handle)
    # 4 targets (5 grupo sym minus BTC) -> 4 sequential subprocess
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 4)

    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    assert "BTC_SOURCE" in orch.state["grupos"]["1"]["cross_options_done"]
    # Per-target launches (CCV precedent): 4 calls, one per target
    assert len(launcher_calls) == 4
    assert all(c["source"] == "BTC" for c in launcher_calls)
    targets_called = [c["target"] for c in launcher_calls]
    assert "BTC" not in targets_called, "source must be excluded from targets"
    assert sorted(targets_called) == sorted(["ETH", "BNB", "XRP", "TRX"])


# -----------------------------------------------------------------------------
# D52.4: ETH_SOURCE launches subprocess + marks done
# -----------------------------------------------------------------------------

def test_d52_4_eth_source_launches_subprocess_marks_done(tmp_path):
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["ETH_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    handle = _StubHandle(54321, [], Path(), Path(), [])
    launcher = _make_launcher(launcher_calls, handle)
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 4)

    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    assert "ETH_SOURCE" in orch.state["grupos"]["1"]["cross_options_done"]
    assert len(launcher_calls) == 4
    assert all(c["source"] == "ETH" for c in launcher_calls)
    targets_called = [c["target"] for c in launcher_calls]
    assert "ETH" not in targets_called


# -----------------------------------------------------------------------------
# D52.5: subprocess CRASHED -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d52_5_subprocess_crashed_tier3(tmp_path):
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["BTC_SOURCE", "ETH_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([_StubStatus.CRASHED])

    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    assert "BTC_SOURCE" not in orch.state["grupos"]["1"]["cross_options_done"]
    assert orch.state["tier3_gate_pending"] is True
    assert orch.state["grupos"]["1"]["tier3_gate_pending"] is True
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert len(tier3) == 1
    assert tier3[0].context["status"] == "CRASHED"
    # ETH_SOURCE should NOT have been launched (Caveat #14 sequential strict halts on failure)
    assert len(launcher_calls) == 1


# -----------------------------------------------------------------------------
# D52.6: subprocess BUGCHECK -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d52_6_subprocess_bugcheck_tier3(tmp_path):
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["BTC_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([_StubStatus.BUGCHECK])

    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert tier3[0].context["status"] == "BUGCHECK"
    assert orch.state["tier3_gate_pending"] is True


# -----------------------------------------------------------------------------
# D52.7: subprocess DONE_PARTIAL -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d52_7_subprocess_partial_outputs_tier3(tmp_path):
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["BTC_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([_StubStatus.DONE_PARTIAL])

    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    assert "BTC_SOURCE" not in orch.state["grupos"]["1"]["cross_options_done"]
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert tier3[0].context["status"] == "DONE_PARTIAL"


# -----------------------------------------------------------------------------
# D52.8: sequential strict — launcher invoked once per option, not parallel
# -----------------------------------------------------------------------------

def test_d52_8_sequential_strict_launcher_once_per_option(tmp_path, monkeypatch):
    # Create regime_wf files for PER_SYM_BASELINE pass
    rwf = tmp_path / "regime_wf"
    rwf.mkdir()
    for sym in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]:
        (rwf / f"{sym}_specialist_configs.json").write_text("{}")
    monkeypatch.chdir(tmp_path)

    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = list(ao.CROSS_OPTIONS)  # all 3
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS, _StubStatus.DONE_SUCCESS,
                            _StubStatus.DONE_SUCCESS])

    # Per-target pattern: BTC_SOURCE = 4 targets, ETH_SOURCE = 4 targets,
    # PER_SYM_BASELINE = 0 launches = 8 total
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 8)
    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    assert len(launcher_calls) == 8
    sources_called = [c["source"] for c in launcher_calls]
    assert sources_called.count("BTC") == 4
    assert sources_called.count("ETH") == 4
    done = set(orch.state["grupos"]["1"]["cross_options_done"])
    assert done == set(ao.CROSS_OPTIONS)


# -----------------------------------------------------------------------------
# D52.9: requires fase_actual == CROSS_CLASS
# -----------------------------------------------------------------------------

def test_d52_9_requires_cross_class_state(tmp_path):
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    orch.declare_grupo(1, ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"])
    # state.fase_actual is still IDLE
    launcher = _make_launcher([], _StubHandle(99, [], Path(), Path(), []))
    waiter = _make_waiter([])
    with pytest.raises(ao.OrchestratorError, match="requires fase_actual == CROSS_CLASS"):
        orch.run_cross_class_real_compute(1, launcher=launcher, waiter=waiter)


# -----------------------------------------------------------------------------
# D52.10: state persisted with active_subprocess record during run
# -----------------------------------------------------------------------------

def test_d52_10_state_persisted_with_active_subprocess(tmp_path):
    orch = _build_orch_at_cross_class(tmp_path)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["BTC_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    state_path = orch.state_path

    captured = []
    def _waiter_inspect(handle, *, poll_interval, timeout, on_poll=None):
        with open(state_path) as f:
            st = json.load(f)
        captured.append(st["grupos"]["1"].get("active_subprocess", {}))
        return _stub_status(_StubStatus.DONE_SUCCESS)

    launcher = _make_launcher([], _StubHandle(7777, [], Path(), Path(), []))
    orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=_waiter_inspect, log_dir=str(tmp_path)
    )
    # 4 targets -> 4 waiter inspections
    assert len(captured) == 4
    # First target while waiting -> exactly 1 active record under "{option}_{target}" key
    first_keys = list(captured[0].keys())
    assert len(first_keys) == 1
    assert first_keys[0].startswith("BTC_SOURCE_")
    # After all completion, active_subprocess cleared
    assert not orch.state["grupos"]["1"].get("active_subprocess", {})


# -----------------------------------------------------------------------------
# D52.11: targets exclude source symbol from grupo
# -----------------------------------------------------------------------------

def test_d52_11_targets_exclude_source(tmp_path):
    # Test with custom grupo not containing BTC -> all 5 sym become targets
    symbols_no_btc = ["ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT", "ADAUSDT"]
    orch = _build_orch_at_cross_class(tmp_path, symbols=symbols_no_btc)
    grupo = orch.state["grupos"]["1"]
    grupo["cross_options_pending"] = ["BTC_SOURCE"]
    grupo["cross_options_done"] = []
    orch._save_state_internal(reason="setup")

    launcher_calls = []
    launcher = _make_launcher(launcher_calls, _StubHandle(99, [], Path(), Path(), []))
    # 5 targets -> 5 sequential subprocess
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 5)

    reports = orch.run_cross_class_real_compute(
        1, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )
    assert len(launcher_calls) == 5
    targets_called = sorted(c["target"] for c in launcher_calls)
    assert targets_called == sorted(["ETH", "BNB", "XRP", "TRX", "ADA"])
