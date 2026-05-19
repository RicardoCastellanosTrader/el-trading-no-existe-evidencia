"""
Tests greenfield AutomationOrchestrator (Fase D.3 — state machine).

Coverage:
  - state machine transitions valid + invalid rejected
  - guards (RECICLAJE -> CROSS_CLASS requires sym_done complete AND primary source verified — Caveat #15)
  - load_state / save_state atomic
  - crash recovery resume: state JSON inspection + primary-source re-check
  - Tier 3 gate blocks DEPLOYMENT_READY -> DEPLOYED until authorize_deploy

Standalone runnable: python tests/test_automation_orchestrator_state.py
Pytest collectable: pytest tests/test_automation_orchestrator_state.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_here = Path(__file__).resolve().parent
_root = _here.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from automation_orchestrator import (  # noqa: E402
    AutomationOrchestrator,
    CROSS_OPTIONS,
    GuardFailedError,
    InvalidTransitionError,
    STATE_ANALYSIS,
    STATE_CROSS_CLASS,
    STATE_DEPLOYED,
    STATE_DEPLOYMENT_READY,
    STATE_IDLE,
    STATE_NEXT_GRUPO,
    STATE_RECICLAJE,
    STATE_TERMINAL_COMPLETE,
    SCHEMA_VERSION,
)


GRUPO1 = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
GRUPO2 = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]


def _accept_all_primary_source(state, gid, sym):
    return True


def _reject_all_primary_source(state, gid, sym):
    return False


def _make_orch(tmp_path, plan=None, verifier=_accept_all_primary_source):
    state_path = tmp_path / "automation_state.json"
    orch = AutomationOrchestrator(
        state_path=str(state_path),
        grupo_plan=plan,
        primary_source_verifier=verifier,
    )
    orch.load_state()
    return orch, state_path


def test_fresh_state_schema(tmp_path):
    orch, state_path = _make_orch(tmp_path)
    assert state_path.exists()
    with open(state_path, "r", encoding="utf-8") as f:
        s = json.load(f)
    assert s["schema_version"] == SCHEMA_VERSION
    assert s["fase_actual"] == STATE_IDLE
    assert s["grupo_actual"] is None
    assert s["grupos"] == {}
    assert s["tier3_gate_pending"] is False


def test_declare_grupo_basic(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    assert orch.state["grupo_actual"] == 1
    g = orch.state["grupos"]["1"]
    assert g["symbols"] == GRUPO1
    assert g["sym_pending_grupo_N"] == GRUPO1
    assert g["sym_done_grupo_N"] == []
    assert sorted(g["cross_options_pending"]) == sorted(CROSS_OPTIONS)


def test_declare_grupo_rejects_wrong_size(tmp_path):
    orch, _ = _make_orch(tmp_path)
    with pytest.raises(Exception):
        orch.declare_grupo(1, ["BTCUSDT", "ETHUSDT"])


def test_declare_grupo_rejects_out_of_range(tmp_path):
    orch, _ = _make_orch(tmp_path)
    with pytest.raises(Exception):
        orch.declare_grupo(99, GRUPO1)


def test_transition_invalid_target_rejected(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    # IDLE -> ANALYSIS is not valid
    with pytest.raises(InvalidTransitionError):
        orch.transition(STATE_ANALYSIS)


def test_transition_unknown_state_rejected(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    with pytest.raises(InvalidTransitionError):
        orch.transition("NONEXISTENT_STATE")


def test_idle_to_reciclaje_ok(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    assert orch.state["fase_actual"] == STATE_RECICLAJE
    # history appended
    assert any(h["to"] == STATE_RECICLAJE for h in orch.state["history"])


def test_idle_to_reciclaje_rejected_without_grupo(tmp_path):
    orch, _ = _make_orch(tmp_path)
    # No declare_grupo
    with pytest.raises(GuardFailedError):
        orch.transition(STATE_RECICLAJE)


def test_reciclaje_to_cross_class_requires_all_sym_done(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    # Mark only 4/5 done
    for sym in GRUPO1[:4]:
        orch.mark_sym_done(1, sym)
    with pytest.raises(GuardFailedError):
        orch.transition(STATE_CROSS_CLASS)
    # Mark last one
    orch.mark_sym_done(1, GRUPO1[4])
    orch.transition(STATE_CROSS_CLASS)
    assert orch.state["fase_actual"] == STATE_CROSS_CLASS


def test_reciclaje_to_cross_class_primary_source_failure(tmp_path):
    # Caveat #15: even if sym_done complete, primary source check must pass
    orch, _ = _make_orch(tmp_path, verifier=_reject_all_primary_source)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    with pytest.raises(GuardFailedError) as exc_info:
        orch.transition(STATE_CROSS_CLASS)
    assert "primary-source" in str(exc_info.value).lower()


def test_cross_class_to_analysis_requires_all_options(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    orch.transition(STATE_CROSS_CLASS)
    # Only 2/3 options
    orch.mark_cross_option_done(1, "BTC_SOURCE")
    orch.mark_cross_option_done(1, "ETH_SOURCE")
    with pytest.raises(GuardFailedError):
        orch.transition(STATE_ANALYSIS)
    orch.mark_cross_option_done(1, "PER_SYM_BASELINE")
    orch.transition(STATE_ANALYSIS)
    assert orch.state["fase_actual"] == STATE_ANALYSIS


def test_analysis_to_deployment_ready_requires_report_path(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    orch.transition(STATE_CROSS_CLASS)
    for opt in CROSS_OPTIONS:
        orch.mark_cross_option_done(1, opt)
    orch.transition(STATE_ANALYSIS)
    with pytest.raises(GuardFailedError):
        orch.transition(STATE_DEPLOYMENT_READY)
    orch.set_analysis_report(1, "report.json")
    orch.transition(STATE_DEPLOYMENT_READY)
    # Tier 3 gate should now be pending
    assert orch.state["tier3_gate_pending"] is True
    assert orch.state["grupos"]["1"]["tier3_gate_pending"] is True


def test_tier3_gate_blocks_deployment(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    orch.transition(STATE_CROSS_CLASS)
    for opt in CROSS_OPTIONS:
        orch.mark_cross_option_done(1, opt)
    orch.transition(STATE_ANALYSIS)
    orch.set_analysis_report(1, "report.json")
    orch.transition(STATE_DEPLOYMENT_READY)
    # Block: tier3 gate pending
    with pytest.raises(GuardFailedError):
        orch.transition(STATE_DEPLOYED)
    # Authorize
    orch.authorize_deploy(1)
    assert orch.state["tier3_gate_pending"] is False
    orch.transition(STATE_DEPLOYED)
    assert orch.state["fase_actual"] == STATE_DEPLOYED


def test_deployed_requires_ack(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    orch.transition(STATE_CROSS_CLASS)
    for opt in CROSS_OPTIONS:
        orch.mark_cross_option_done(1, opt)
    orch.transition(STATE_ANALYSIS)
    orch.set_analysis_report(1, "report.json")
    orch.transition(STATE_DEPLOYMENT_READY)
    orch.authorize_deploy(1)
    orch.transition(STATE_DEPLOYED)
    with pytest.raises(GuardFailedError):
        orch.transition(STATE_NEXT_GRUPO)
    orch.mark_deployment_ack(1)
    orch.transition(STATE_NEXT_GRUPO)
    assert orch.state["grupo_actual"] == 2  # auto-advance


def test_next_grupo_auto_declares_from_plan(tmp_path):
    plan = {1: GRUPO1, 2: GRUPO2}
    orch, _ = _make_orch(tmp_path, plan=plan)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    orch.transition(STATE_CROSS_CLASS)
    for opt in CROSS_OPTIONS:
        orch.mark_cross_option_done(1, opt)
    orch.transition(STATE_ANALYSIS)
    orch.set_analysis_report(1, "r.json")
    orch.transition(STATE_DEPLOYMENT_READY)
    orch.authorize_deploy(1)
    orch.transition(STATE_DEPLOYED)
    orch.mark_deployment_ack(1)
    orch.transition(STATE_NEXT_GRUPO)
    assert "2" in orch.state["grupos"]
    assert orch.state["grupos"]["2"]["symbols"] == GRUPO2
    orch.transition(STATE_RECICLAJE)
    assert orch.state["fase_actual"] == STATE_RECICLAJE
    assert orch.state["grupo_actual"] == 2


def test_save_and_load_roundtrip(tmp_path):
    orch, state_path = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    orch.mark_sym_done(1, GRUPO1[0])
    orch.save_state()

    # Reload in a fresh instance
    orch2 = AutomationOrchestrator(
        state_path=str(state_path),
        primary_source_verifier=_accept_all_primary_source,
    )
    orch2.load_state()
    assert orch2.state["fase_actual"] == STATE_RECICLAJE
    assert orch2.state["grupo_actual"] == 1
    assert GRUPO1[0] in orch2.state["grupos"]["1"]["sym_done_grupo_N"]
    assert len(orch2.state["grupos"]["1"]["sym_pending_grupo_N"]) == 4


def test_crash_recovery_resume_point_updated(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    snap = orch.state["crash_recovery_resume_point"]
    assert snap["state"] == STATE_IDLE
    assert snap["context"]["target"] == STATE_RECICLAJE


def test_atomic_write_no_partial_on_simulated_failure(tmp_path):
    orch, state_path = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.save_state()
    # Ensure no tmp leftovers
    leftovers = list(state_path.parent.glob(".automation_state.json.*.tmp"))
    assert leftovers == []


def test_schema_version_mismatch_rejected(tmp_path):
    state_path = tmp_path / "automation_state.json"
    state_path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
    orch = AutomationOrchestrator(state_path=str(state_path))
    with pytest.raises(Exception) as exc_info:
        orch.load_state()
    assert "Schema version" in str(exc_info.value)


def test_history_append_order(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.declare_grupo(1, GRUPO1)
    orch.transition(STATE_RECICLAJE)
    for sym in GRUPO1:
        orch.mark_sym_done(1, sym)
    orch.transition(STATE_CROSS_CLASS)
    transitions = [(h["from"], h["to"]) for h in orch.state["history"]]
    assert transitions == [(STATE_IDLE, STATE_RECICLAJE), (STATE_RECICLAJE, STATE_CROSS_CLASS)]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
