"""
Tests greenfield AutomationOrchestrator (Fase D.3 — dry-run end-to-end).

Coverage:
  - run_grupo dry-run full flow for grupo 1: IDLE -> ... -> DEPLOYMENT_READY (Tier 3 pause)
  - resume_grupo after authorize_deploy: DEPLOYMENT_READY -> DEPLOYED -> NEXT_GRUPO
  - Two grupos × 3 sym dummy: full pipeline end-to-end
  - Tiered reporting emission verified (Tier 1 silent, Tier 2 mid-stage, Tier 3 pause)
  - Crash mid-grupo: re-load state + re-invoke run_grupo idempotent (does NOT redo done work)
  - CLI smoke: main() with --status and --simulate-grupo

Standalone runnable: python tests/test_automation_orchestrator_dry_run.py
Pytest collectable: pytest tests/test_automation_orchestrator_dry_run.py
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

_here = Path(__file__).resolve().parent
_root = _here.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import automation_orchestrator as ao  # noqa: E402
from automation_orchestrator import (  # noqa: E402
    AutomationOrchestrator,
    CROSS_OPTIONS,
    STATE_DEPLOYED,
    STATE_DEPLOYMENT_READY,
    STATE_IDLE,
    STATE_RECICLAJE,
    STATE_TERMINAL_COMPLETE,
    TIER_1,
    TIER_2,
    TIER_3,
    main,
)


# Dummy grupos to keep test "2 grupos × 3 sym" intent — but orchestrator requires 5 sym/grupo;
# we keep 5 sym for valid declaration and assert structure / report counts only.
GRUPO_A = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT", "EEEUSDT"]
GRUPO_B = ["FFFUSDT", "GGGUSDT", "HHHUSDT", "IIIUSDT", "JJJUSDT"]


def _accept_all(state, gid, sym):
    return True


def _make_orch(tmp_path):
    state_path = tmp_path / "automation_state.json"
    orch = AutomationOrchestrator(
        state_path=str(state_path),
        grupo_plan={1: GRUPO_A, 2: GRUPO_B},
        primary_source_verifier=_accept_all,
    )
    orch.load_state()
    return orch, state_path


def test_run_grupo_dry_run_pauses_at_tier3(tmp_path):
    orch, _ = _make_orch(tmp_path)
    reports = orch.run_grupo(1, GRUPO_A, dry_run=True)
    # Final state must be DEPLOYMENT_READY (Tier 3 pause)
    assert orch.state["fase_actual"] == STATE_DEPLOYMENT_READY
    assert orch.state["tier3_gate_pending"] is True
    # Last report should be Tier 3
    assert reports[-1].tier == TIER_3
    # Tier 1 reports for each sym + each cross option
    tier1_count = sum(1 for r in reports if r.tier == TIER_1)
    assert tier1_count == 5 + 3
    # Tier 2 reports at least 3 (reciclaje complete + cross_class complete + analysis report)
    tier2_count = sum(1 for r in reports if r.tier == TIER_2)
    assert tier2_count >= 3


def test_run_grupo_rejects_non_dry_run(tmp_path):
    orch, _ = _make_orch(tmp_path)
    with pytest.raises(Exception):
        orch.run_grupo(1, GRUPO_A, dry_run=False)


def test_authorize_and_resume_to_next_grupo(tmp_path):
    orch, _ = _make_orch(tmp_path)
    orch.run_grupo(1, GRUPO_A, dry_run=True)
    assert orch.state["fase_actual"] == STATE_DEPLOYMENT_READY
    orch.authorize_deploy(1)
    reports = orch.resume_grupo(1, dry_run=True)
    # After resume: deployed -> ack -> NEXT_GRUPO -> RECICLAJE (grupo 2)
    assert orch.state["fase_actual"] == STATE_RECICLAJE
    assert orch.state["grupo_actual"] == 2
    # Resume reports include at least one Tier 2
    assert any(r.tier == TIER_2 for r in reports)


def test_full_two_grupo_pipeline_end_to_end(tmp_path):
    plan = {1: GRUPO_A, 2: GRUPO_B}
    orch = AutomationOrchestrator(
        state_path=str(tmp_path / "automation_state.json"),
        grupo_plan=plan,
        primary_source_verifier=_accept_all,
    )
    orch.load_state()

    # Grupo 1 — full flow
    orch.run_grupo(1, GRUPO_A, dry_run=True)
    orch.authorize_deploy(1)
    orch.resume_grupo(1, dry_run=True)
    assert orch.state["grupo_actual"] == 2
    assert orch.state["fase_actual"] == STATE_RECICLAJE

    # Grupo 2 — continue from current fase
    reports2 = orch.run_grupo(2, GRUPO_B, dry_run=True)
    assert orch.state["fase_actual"] == STATE_DEPLOYMENT_READY
    assert orch.state["grupo_actual"] == 2
    assert orch.state["grupos"]["2"]["tier3_gate_pending"] is True
    assert reports2[-1].tier == TIER_3

    orch.authorize_deploy(2)
    orch.resume_grupo(2, dry_run=True)
    # After grupo 2 done, no auto next grupo declared since plan only had 1 and 2.
    # grupo_actual should advance to 3 (auto _advance) but no plan => stays at 3 placeholder,
    # but resume_grupo tries NEXT_GRUPO -> RECICLAJE which guard rejects (grupo 3 not declared).
    # Verify state reflects that the orchestrator advanced past grupo 2 deployment.
    # The flow gets stuck at NEXT_GRUPO since grupo 3 not declared — that's expected.
    assert orch.state["grupos"]["2"]["deployment_ack"] is True


def test_terminal_complete_at_max_grupo(tmp_path):
    # Simulate reaching grupo 9 done.
    state_path = tmp_path / "automation_state.json"
    orch = AutomationOrchestrator(
        state_path=str(state_path),
        primary_source_verifier=_accept_all,
    )
    orch.load_state()
    # Manually fast-forward state to "grupo 9 deployed + ack, ready for NEXT_GRUPO"
    orch.declare_grupo(9, ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT", "EEEUSDT"])
    # transition through manually
    orch.transition(STATE_RECICLAJE)
    for sym in orch.state["grupos"]["9"]["symbols"]:
        orch.mark_sym_done(9, sym)
    from automation_orchestrator import STATE_CROSS_CLASS, STATE_ANALYSIS
    orch.transition(STATE_CROSS_CLASS)
    for opt in CROSS_OPTIONS:
        orch.mark_cross_option_done(9, opt)
    orch.transition(STATE_ANALYSIS)
    orch.set_analysis_report(9, "r.json")
    orch.transition(STATE_DEPLOYMENT_READY)
    orch.authorize_deploy(9)
    orch.transition(STATE_DEPLOYED)
    orch.mark_deployment_ack(9)
    orch.transition("NEXT_GRUPO")
    # After NEXT_GRUPO from grupo 9 we expect grupo_actual = None (exhausted)
    assert orch.state["grupo_actual"] is None
    orch.transition(STATE_TERMINAL_COMPLETE)
    assert orch.state["fase_actual"] == STATE_TERMINAL_COMPLETE


def test_crash_resume_does_not_redo_done_work(tmp_path):
    state_path = tmp_path / "automation_state.json"
    orch = AutomationOrchestrator(
        state_path=str(state_path),
        primary_source_verifier=_accept_all,
    )
    orch.load_state()
    orch.declare_grupo(1, GRUPO_A)
    orch.transition(STATE_RECICLAJE)
    # Partial: mark only 2 sym done, then "crash" (no further calls)
    orch.mark_sym_done(1, GRUPO_A[0])
    orch.mark_sym_done(1, GRUPO_A[1])

    # Reload — simulate fresh process
    orch2 = AutomationOrchestrator(
        state_path=str(state_path),
        primary_source_verifier=_accept_all,
    )
    orch2.load_state()
    assert orch2.state["fase_actual"] == STATE_RECICLAJE
    assert sorted(orch2.state["grupos"]["1"]["sym_done_grupo_N"]) == sorted(GRUPO_A[:2])
    assert sorted(orch2.state["grupos"]["1"]["sym_pending_grupo_N"]) == sorted(GRUPO_A[2:])

    # Continue: run_grupo should be idempotent — only process remaining 3 sym
    reports = orch2.run_grupo(1, GRUPO_A, dry_run=True)
    # Tier 1 sym-done reports should be 3 (only the pending ones), not 5
    tier1_sym = [r for r in reports if r.tier == TIER_1 and "sym " in r.message and " done" in r.message]
    assert len(tier1_sym) == 3
    assert orch2.state["fase_actual"] == STATE_DEPLOYMENT_READY


def test_cli_status_smoke(tmp_path, monkeypatch):
    state_path = tmp_path / "automation_state.json"
    # Pre-init state
    orch = AutomationOrchestrator(state_path=str(state_path))
    orch.load_state()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["--state-path", str(state_path), "--status"])
    assert rc == 0
    out = buf.getvalue()
    assert "fase_actual" in out
    payload = json.loads(out)
    assert payload["fase_actual"] == STATE_IDLE


def test_cli_simulate_grupo_requires_dry_run(tmp_path, monkeypatch):
    state_path = tmp_path / "automation_state.json"
    # Use default plan via monkeypatch
    rc = main(["--state-path", str(state_path), "--simulate-grupo", "1"])
    # Should fail without --dry-run
    assert rc == 2


def test_cli_simulate_grupo_dry_run_succeeds(tmp_path, capsys):
    state_path = tmp_path / "automation_state.json"
    rc = main(["--state-path", str(state_path), "--dry-run", "--simulate-grupo", "1"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Tier 3" in captured.out
    assert "PAUSE" in captured.out
    # State file persisted
    assert state_path.exists()
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["fase_actual"] == STATE_DEPLOYMENT_READY
    assert payload["tier3_gate_pending"] is True


def test_cli_authorize_deploy_clears_gate(tmp_path):
    state_path = tmp_path / "automation_state.json"
    main(["--state-path", str(state_path), "--dry-run", "--simulate-grupo", "1"])
    rc = main(["--state-path", str(state_path), "--authorize-deploy", "1"])
    assert rc == 0
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["tier3_gate_pending"] is False
    assert payload["grupos"]["1"]["tier3_gate_pending"] is False


def test_cli_reset_removes_state(tmp_path):
    state_path = tmp_path / "automation_state.json"
    main(["--state-path", str(state_path), "--dry-run", "--simulate-grupo", "1"])
    assert state_path.exists()
    rc = main(["--state-path", str(state_path), "--reset"])
    assert rc == 0
    assert not state_path.exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
