"""Tests Fase D.5.1 — AutomationOrchestrator real-compute hookup RECICLAJE.

Mock launcher + waiter to avoid actual subprocess spawning during tests.

H_B isolation fix 2026-05-19 cardinal cross-Sub-Sesiones precedent absoluto —
2-phase pattern per sym: Phase 1 CPU steps 1-3 + Phase 2 GPU step 4 isolated
(replicates Grupo 1 success pattern; refutes full-pipeline Crashes 12+13).

Coverage:
- D51.1: per-sym 2-phase launches + marks sym done on both DONE_SUCCESS.
- D51.2: requires fase_actual == RECICLAJE.
- D51.3: Phase 2 CRASHED on sym 1 -> Tier 3 + Caveat #14 halt remaining sym.
- D51.4: Phase 1 BUGCHECK -> Tier 3 (steps 1-3 also crash-able).
- D51.5: Phase 2 DONE_PARTIAL -> Tier 3.
- D51.6: Phase 2 DONE_SUCCESS but specialist_configs missing -> Tier 3 (Caveat #15).
- D51.7: sequential strict — 2 calls per sym, no parallel.
- D51.8: state persisted active_subprocess phase1 + phase2 records + popped on success.
- D51.9: all 5 sym 2-phase DONE -> Tier 2 announce.
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
    """Launcher that records each call and returns a stub handle with predictable pid.

    2-phase pattern: caller invokes once per phase per sym. to_step="lite" → Phase 1,
    from_step="regime-wf" → Phase 2.
    """
    counter = {"i": 0}

    def _launch(*, symbol, chunk_size, log_path, err_path,
                 from_step=None, to_step=None, recycle=True):
        captured_calls.append({
            "symbol": symbol,
            "chunk_size": chunk_size,
            "log_path": log_path,
            "err_path": err_path,
            "from_step": from_step,
            "to_step": to_step,
            "recycle": recycle,
        })
        pid = pid_seq[counter["i"]] if pid_seq and counter["i"] < len(pid_seq) else 1000 + counter["i"]
        counter["i"] += 1
        # Phase 2 expected = regime_wf JSON; Phase 1 expected = presets CSV
        if to_step == "lite":
            base = symbol.replace("/USDT", "").replace("USDT", "")
            expected = [Path("output/production") / f"presets_{base}USDT.csv"]
        else:
            expected = [Path("regime_wf") / f"{symbol}_specialist_configs.json"]
        return _StubHandle(
            pid=pid,
            cmd=[],
            log_path=Path(log_path),
            err_path=Path(err_path),
            expected_outputs=expected,
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
    """Create fake Phase 1 + Phase 2 primary-source files for Caveat #15 verify.

    Phase 1 expected: output/production/presets_{SYM}USDT.csv
    Phase 2 expected: regime_wf/{SYM}USDT_specialist_configs.json
    """
    rwf = tmp_path / "regime_wf"
    rwf.mkdir(exist_ok=True)
    presets_dir = tmp_path / "output" / "production"
    presets_dir.mkdir(parents=True, exist_ok=True)
    for sym in symbols:
        (rwf / f"{sym}_specialist_configs.json").write_text("{}")
        (presets_dir / f"presets_{sym}.csv").write_text("dummy")


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
    # 2-phase: 5 sym × 2 phases = 10 DONE_SUCCESS
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 10)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    assert sorted(grupo["sym_done_grupo_N"]) == sorted(symbols)
    assert grupo["sym_pending_grupo_N"] == []
    assert len(captured) == 10, f"Expected 10 launches (5 sym × 2 phases), got {len(captured)}"
    # Phase 1 + Phase 2 per sym
    phase1_calls = [c for c in captured if c["to_step"] == "lite"]
    phase2_calls = [c for c in captured if c["from_step"] == "regime-wf"]
    assert len(phase1_calls) == 5 and len(phase2_calls) == 5
    assert sorted(c["symbol"] for c in phase1_calls) == sorted(symbols)
    assert sorted(c["symbol"] for c in phase2_calls) == sorted(symbols)


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
    # Sym 1 Phase 1+2 SUCCESS, Sym 2 Phase 1 SUCCESS Phase 2 CRASHED -> halt
    # 2-phase: ONDO p1=SUCCESS, ONDO p2=SUCCESS, RENDER p1=SUCCESS, RENDER p2=CRASHED
    waiter = _make_waiter([
        _StubStatus.DONE_SUCCESS,  # ONDO phase1
        _StubStatus.DONE_SUCCESS,  # ONDO phase2
        _StubStatus.DONE_SUCCESS,  # RENDER phase1
        _StubStatus.CRASHED,        # RENDER phase2 — CRASH
    ])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    # ONDO done (both phases OK), RENDER NOT done (phase2 crashed)
    assert "ONDOUSDT" in grupo["sym_done_grupo_N"]
    assert "RENDERUSDT" not in grupo["sym_done_grupo_N"]
    # Caveat #14: remaining sym (POL/SEI/TAO) NOT launched at all
    assert len(captured) == 4, f"Expected 4 launches (ONDO 2 + RENDER 2), got {len(captured)}"
    # Tier 3 gate raised
    assert orch.state["tier3_gate_pending"] is True
    assert grupo["tier3_gate_pending"] is True
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert len(tier3) == 1
    assert tier3[0].context["status"] == "CRASHED"
    assert tier3[0].context["symbol"] == "RENDERUSDT"
    assert tier3[0].context["phase"] == "phase2_gpu"


# -----------------------------------------------------------------------------
# D51.4: subprocess BUGCHECK -> Tier 3 PAUSE
# -----------------------------------------------------------------------------

def test_d51_4_bugcheck_tier3(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    launcher = _make_launcher([])
    # BUGCHECK on first phase (Phase 1) of first sym
    waiter = _make_waiter([_StubStatus.BUGCHECK])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert tier3[0].context["status"] == "BUGCHECK"
    assert tier3[0].context["phase"] == "phase1_cpu"
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
    # Phase 1 SUCCESS, Phase 2 PARTIAL -> Tier 3 on Phase 2
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS, _StubStatus.DONE_PARTIAL])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    assert grupo["sym_done_grupo_N"] == []  # nothing marked done
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert tier3[0].context["status"] == "DONE_PARTIAL"
    assert tier3[0].context["phase"] == "phase2_gpu"


# -----------------------------------------------------------------------------
# D51.6: DONE_SUCCESS but primary-source MISSING -> Tier 3 PAUSE (Caveat #15)
# -----------------------------------------------------------------------------

def test_d51_6_done_success_primary_missing_tier3_caveat15(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    # NO primary sources created -> Phase 1 expected presets MISSING → Tier 3 immediately
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    launcher = _make_launcher([])
    # Phase 1 reports DONE_SUCCESS but presets file doesn't exist → Tier 3
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS])

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    assert grupo["sym_done_grupo_N"] == []
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
    # 2-phase: 5 sym × 2 phases = 10 DONE_SUCCESS
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 10)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    # Each sym launched exactly twice (phase1 + phase2)
    syms_launched = [c["symbol"] for c in captured]
    assert len(syms_launched) == 10
    sym_counts = {sym: syms_launched.count(sym) for sym in symbols}
    assert all(c == 2 for c in sym_counts.values()), \
        f"Each sym must be launched 2x (phase1+phase2), got {sym_counts}"


# -----------------------------------------------------------------------------
# D51.8: state persisted with active_subprocess record + popped on success
# -----------------------------------------------------------------------------

def test_d51_8_active_subprocess_record_lifecycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    symbols = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, symbols=symbols)

    captured = []
    launcher = _make_launcher(captured,
                                pid_seq=[2001, 2002, 2003, 2004, 2005,
                                         2011, 2012, 2013, 2014, 2015])
    # 2-phase: 5 sym × 2 phases = 10 DONE_SUCCESS
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 10)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    grupo = orch.state["grupos"]["2"]
    # After all done, active_subprocess should be empty (phase1+phase2 each popped on success)
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
    # 2-phase: 5 sym × 2 phases = 10 DONE_SUCCESS
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 10)

    reports = orch.run_reciclaje_real_compute(
        2, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    # Tier 2 final announce (RECICLAJE_GRUPO_N all sym DONE 2-phase H_B isolation)
    tier2_announce = [r for r in reports
                       if r.tier == ao.TIER_2
                       and "all 5 sym DONE" in r.message
                       and "2-phase" in r.message]
    assert len(tier2_announce) == 1
    assert orch.state["tier3_gate_pending"] is False

    # State should still be RECICLAJE — caller drives transition to CROSS_CLASS
    assert orch.state["fase_actual"] == ao.STATE_RECICLAJE


# -----------------------------------------------------------------------------
# D51.10/11/12: ancla de recencia resume-skip (2026-06-06, caso origen G4 launch
# — JSONs legacy reciclaje cartera-completa marzo/abril aceptados como DONE)
# -----------------------------------------------------------------------------

def _write_valid_specialist(path: Path, mtime: float = None) -> None:
    import json as _json
    import os as _os
    clusters = {str(k): {"top_configs": [{"config_id": 1, "pf_fwd": 2.0}]}
                for k in range(3)}
    path.write_text(_json.dumps({"n_clusters": 3, "clusters": clusters}),
                    encoding="utf-8")
    if mtime is not None:
        _os.utime(path, (mtime, mtime))


def test_d51_10_legacy_specialist_not_skipped(tmp_path, monkeypatch):
    """Specialist VÁLIDO pero legacy (mtime << launch) -> NO resume-skip, re-computa."""
    import time
    monkeypatch.chdir(tmp_path)
    symbols = ["LTCUSDT", "XLMUSDT", "ETCUSDT", "VETUSDT", "FETUSDT"]
    _create_primary_sources(tmp_path, symbols)
    # Sobrescribir con specialists VÁLIDOS pero legacy (30 días atrás)
    legacy = time.time() - 30 * 86400
    for sym in symbols:
        _write_valid_specialist(tmp_path / "regime_wf" / f"{sym}_specialist_configs.json",
                                mtime=legacy)
    orch = _build_orch_at_reciclaje(tmp_path, grupo_id=4, symbols=symbols)

    captured = []
    launcher = _make_launcher(captured)
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 10)

    orch.run_reciclaje_real_compute(
        4, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    # Los 5 sym DEBEN computarse (10 launches) — el legacy NO satisface el ancla
    assert len(captured) == 10, \
        f"Legacy specialists deben re-computarse, got {len(captured)} launches"
    # Ancla persistida en estado
    assert orch.state["grupos"]["4"].get("reciclaje_started_at") is not None


def test_d51_11_fresh_specialist_skipped_after_relaunch(tmp_path, monkeypatch):
    """Specialist escrito DESPUÉS del ancla (relaunch mid-grupo, Caveat #20 secuela)
    -> resume-skip preservado para ese sym."""
    import time
    monkeypatch.chdir(tmp_path)
    symbols = ["LTCUSDT", "XLMUSDT", "ETCUSDT", "VETUSDT", "FETUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, grupo_id=4, symbols=symbols)
    # Simular relaunch: ancla fijada hace 1h + LTC completado DESPUÉS del ancla
    from datetime import datetime, timezone, timedelta
    anchor_dt = datetime.now(timezone.utc) - timedelta(hours=1)
    orch.state["grupos"]["4"]["reciclaje_started_at"] = \
        anchor_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_valid_specialist(tmp_path / "regime_wf" / "LTCUSDT_specialist_configs.json")

    captured = []
    launcher = _make_launcher(captured)
    # 4 sym restantes × 2 phases = 8 (LTC skipped)
    waiter = _make_waiter([_StubStatus.DONE_SUCCESS] * 8)

    reports = orch.run_reciclaje_real_compute(
        4, launcher=launcher, waiter=waiter, log_dir=str(tmp_path)
    )

    assert len(captured) == 8, f"LTC fresh debe skipearse, got {len(captured)} launches"
    assert "LTCUSDT" not in [c["symbol"] for c in captured]
    assert "LTCUSDT" in orch.state["grupos"]["4"]["sym_done_grupo_N"]
    skip_reports = [r for r in reports if "resume-skip" in r.message]
    assert len(skip_reports) == 1 and skip_reports[0].context["symbol"] == "LTCUSDT"


def test_d51_12_anchor_stable_across_relaunches(tmp_path, monkeypatch):
    """El ancla se fija UNA vez (primer arranque) y NO se re-fija en relaunches."""
    monkeypatch.chdir(tmp_path)
    symbols = ["LTCUSDT", "XLMUSDT", "ETCUSDT", "VETUSDT", "FETUSDT"]
    _create_primary_sources(tmp_path, symbols)
    orch = _build_orch_at_reciclaje(tmp_path, grupo_id=4, symbols=symbols)
    sentinel = "2026-06-06T00:00:00Z"
    orch.state["grupos"]["4"]["reciclaje_started_at"] = sentinel

    orch.run_reciclaje_real_compute(
        4, launcher=_make_launcher([]),
        waiter=_make_waiter([_StubStatus.DONE_SUCCESS] * 10),
        log_dir=str(tmp_path),
    )

    assert orch.state["grupos"]["4"]["reciclaje_started_at"] == sentinel
