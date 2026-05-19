"""
Automation Orchestrator — Path C reformulado incremental rolling (Fase D.2 stub).

Scope (stub, 2026-05-11):
  - State machine over grupos of 5 sym × cross-3-options PIPELINED.
  - Persistent state JSON `automation_state.json` (schema v1 — see fase_d_automation_orchestrator_design_20260511.md).
  - Dry-run flow simulation. NO real compute. NO Numba/CUDA imports. NO writes outside the state file.
  - Pause / resume / crash-recovery via primary-source verification pattern (Caveat #15).

NOT in scope this stub (deferred Fase D.5+):
  - Real subprocess launch of master.py / lab_cuda.py / regime_walk_forward.py.
  - Real watchers on filesystem (here: simulated via dry-run flow).
  - Real bot v2.5.0 deployment hook.

Standalone runnable:
    python automation_orchestrator.py --dry-run --simulate-grupo 1
    python automation_orchestrator.py --status
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------------------------------------------------------
# Schema constants
# -----------------------------------------------------------------------------

SCHEMA_VERSION = 1
DEFAULT_STATE_PATH = "automation_state.json"

STATE_IDLE = "IDLE"
STATE_RECICLAJE = "RECICLAJE_GRUPO_N"
STATE_CROSS_CLASS = "CROSS_CLASS_GRUPO_N"
STATE_ANALYSIS = "ANALYSIS_GRUPO_N"
STATE_DEPLOYMENT_READY = "DEPLOYMENT_READY_GRUPO_N"
STATE_DEPLOYED = "DEPLOYED_GRUPO_N"
STATE_NEXT_GRUPO = "NEXT_GRUPO"
STATE_TERMINAL_COMPLETE = "TERMINAL_COMPLETE"

VALID_STATES = {
    STATE_IDLE, STATE_RECICLAJE, STATE_CROSS_CLASS, STATE_ANALYSIS,
    STATE_DEPLOYMENT_READY, STATE_DEPLOYED, STATE_NEXT_GRUPO,
    STATE_TERMINAL_COMPLETE,
}

# Explicit transition table — (from, to). Anything else REJECTED.
VALID_TRANSITIONS: Dict[str, set] = {
    STATE_IDLE: {STATE_RECICLAJE},
    STATE_RECICLAJE: {STATE_CROSS_CLASS},
    STATE_CROSS_CLASS: {STATE_ANALYSIS},
    STATE_ANALYSIS: {STATE_DEPLOYMENT_READY},
    STATE_DEPLOYMENT_READY: {STATE_DEPLOYED},
    STATE_DEPLOYED: {STATE_NEXT_GRUPO},
    STATE_NEXT_GRUPO: {STATE_RECICLAJE, STATE_TERMINAL_COMPLETE},
    STATE_TERMINAL_COMPLETE: set(),
}

CROSS_OPTIONS = ("BTC_SOURCE", "ETH_SOURCE", "PER_SYM_BASELINE")
MAX_GRUPO = 9  # 45 sym / 5 per grupo

# Default plan (Path C reformulated 2026-05-10 spec — Grupo 1 documented; others placeholder
# until Sub-Sesión refines per-grupo composition). Tests inject their own plan.
DEFAULT_GRUPO_PLAN: Dict[int, List[str]] = {
    1: ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"],
    2: ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"],
}


# -----------------------------------------------------------------------------
# Reporting tiers
# -----------------------------------------------------------------------------

TIER_1 = 1  # silent
TIER_2 = 2  # brief log line
TIER_3 = 3  # PAUSE + report Ricardo


@dataclass
class TierReport:
    tier: int
    message: str
    grupo_id: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class OrchestratorError(Exception):
    pass


class InvalidTransitionError(OrchestratorError):
    pass


class GuardFailedError(OrchestratorError):
    pass


class Tier3PauseError(OrchestratorError):
    """Raised internally to signal a Tier 3 gate; caller persists state and exits."""
    pass


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON atomically: temp file in same dir + os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# -----------------------------------------------------------------------------
# AutomationOrchestrator
# -----------------------------------------------------------------------------

class AutomationOrchestrator:
    """State machine + persistent JSON state for Path C reformulado.

    Caveat #14 sequential strict: only one transition at a time per process.
    Caveat #15 verificación primary source: guards verify file existence when
    `verify_primary_source=True` (default for real flows; tests inject stubs).
    """

    def __init__(
        self,
        state_path: str = DEFAULT_STATE_PATH,
        grupo_plan: Optional[Dict[int, List[str]]] = None,
        primary_source_verifier=None,
        clock=None,
    ):
        self.state_path = Path(state_path)
        self.grupo_plan = dict(grupo_plan) if grupo_plan is not None else dict(DEFAULT_GRUPO_PLAN)
        # primary_source_verifier(state_dict, grupo_id, sym) -> bool. None => filesystem check.
        self.primary_source_verifier = primary_source_verifier
        self.clock = clock if clock is not None else _utcnow_iso
        self.state: Dict[str, Any] = {}
        self.reports: List[TierReport] = []

    # ------------------------------------------------------------------
    # state load/save
    # ------------------------------------------------------------------

    def load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            self.state = self._fresh_state()
            self._save_state_internal(reason="init")
            return self.state
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        if self.state.get("schema_version") != SCHEMA_VERSION:
            raise OrchestratorError(
                f"Schema version mismatch: expected {SCHEMA_VERSION}, got {self.state.get('schema_version')}"
            )
        return self.state

    def save_state(self) -> None:
        self._save_state_internal(reason="explicit_save")

    def _save_state_internal(self, reason: str) -> None:
        self.state["updated_at"] = self.clock()
        _atomic_write_json(self.state_path, self.state)

    def _fresh_state(self) -> Dict[str, Any]:
        ts = self.clock()
        return {
            "schema_version": SCHEMA_VERSION,
            "created_at": ts,
            "updated_at": ts,
            "grupo_actual": None,
            "fase_actual": STATE_IDLE,
            "grupos": {},
            "last_completed": {"state": None, "grupo_id": None, "timestamp": None},
            "crash_recovery_resume_point": {
                "state": STATE_IDLE, "grupo_id": None, "context": {}, "timestamp": ts,
            },
            "tier3_gate_pending": False,
            "history": [],
        }

    # ------------------------------------------------------------------
    # grupo declaration
    # ------------------------------------------------------------------

    def declare_grupo(self, grupo_id: int, symbols: List[str]) -> None:
        if grupo_id < 1 or grupo_id > MAX_GRUPO:
            raise OrchestratorError(f"grupo_id {grupo_id} out of range [1, {MAX_GRUPO}]")
        if not symbols or len(symbols) != 5:
            raise OrchestratorError(f"grupo_id {grupo_id} expects 5 symbols, got {len(symbols)}")
        key = str(grupo_id)
        if key in self.state.get("grupos", {}):
            raise OrchestratorError(f"grupo_id {grupo_id} already declared")
        self.state.setdefault("grupos", {})[key] = {
            "symbols": list(symbols),
            "sym_done_grupo_N": [],
            "sym_pending_grupo_N": list(symbols),
            "cross_options_done": [],
            "cross_options_pending": list(CROSS_OPTIONS),
            "analysis_report_path": None,
            "deployment_ack": False,
            "tier3_gate_pending": False,
        }
        if self.state.get("grupo_actual") is None:
            self.state["grupo_actual"] = grupo_id

    # ------------------------------------------------------------------
    # transition
    # ------------------------------------------------------------------

    def transition(self, new_state: str, *, note: str = "") -> None:
        """Atomic transition with guard validation. Raises on invalid transition."""
        if new_state not in VALID_STATES:
            raise InvalidTransitionError(f"unknown state '{new_state}'")
        current = self.state.get("fase_actual", STATE_IDLE)
        if new_state not in VALID_TRANSITIONS.get(current, set()):
            raise InvalidTransitionError(
                f"transition {current} -> {new_state} not in valid table"
            )
        # Snapshot pre-write to crash recovery
        self.state["crash_recovery_resume_point"] = {
            "state": current,
            "grupo_id": self.state.get("grupo_actual"),
            "context": {"target": new_state},
            "timestamp": self.clock(),
        }
        # Evaluate guard for the transition
        self._evaluate_guard(current, new_state)
        # Commit
        self.state["fase_actual"] = new_state
        self.state["last_completed"] = {
            "state": current,
            "grupo_id": self.state.get("grupo_actual"),
            "timestamp": self.clock(),
        }
        self.state.setdefault("history", []).append({
            "ts": self.clock(),
            "from": current,
            "to": new_state,
            "grupo_id": self.state.get("grupo_actual"),
            "note": note,
        })
        # If transitioning into DEPLOYMENT_READY, set tier3 gate
        if new_state == STATE_DEPLOYMENT_READY:
            self.state["tier3_gate_pending"] = True
            gid = str(self.state.get("grupo_actual"))
            if gid in self.state.get("grupos", {}):
                self.state["grupos"][gid]["tier3_gate_pending"] = True
        # If transitioning into NEXT_GRUPO -> increment grupo_actual
        if new_state == STATE_NEXT_GRUPO:
            self._advance_grupo_actual()
        self._save_state_internal(reason=f"transition_{current}_to_{new_state}")

    def _evaluate_guard(self, current: str, target: str) -> None:
        gid = self.state.get("grupo_actual")
        gid_key = str(gid) if gid is not None else None
        grupo = self.state.get("grupos", {}).get(gid_key) if gid_key else None

        if current == STATE_IDLE and target == STATE_RECICLAJE:
            if grupo is None:
                raise GuardFailedError("IDLE->RECICLAJE: no grupo declared / grupo_actual unset")
            if len(grupo["sym_pending_grupo_N"]) != 5:
                raise GuardFailedError("IDLE->RECICLAJE: sym_pending must contain all 5 sym")
            return

        if current == STATE_RECICLAJE and target == STATE_CROSS_CLASS:
            if grupo is None:
                raise GuardFailedError("RECICLAJE->CROSS_CLASS: no active grupo")
            if set(grupo["sym_done_grupo_N"]) != set(grupo["symbols"]):
                raise GuardFailedError(
                    f"RECICLAJE->CROSS_CLASS: sym_done {grupo['sym_done_grupo_N']} != symbols {grupo['symbols']}"
                )
            # Caveat #15 primary source verification
            for sym in grupo["symbols"]:
                if not self._verify_primary_source_for_reciclaje(gid, sym):
                    raise GuardFailedError(
                        f"RECICLAJE->CROSS_CLASS: primary-source verification FAILED for {sym}"
                    )
            return

        if current == STATE_CROSS_CLASS and target == STATE_ANALYSIS:
            if grupo is None:
                raise GuardFailedError("CROSS_CLASS->ANALYSIS: no active grupo")
            if set(grupo["cross_options_done"]) != set(CROSS_OPTIONS):
                raise GuardFailedError(
                    f"CROSS_CLASS->ANALYSIS: cross_options_done {grupo['cross_options_done']} incomplete"
                )
            return

        if current == STATE_ANALYSIS and target == STATE_DEPLOYMENT_READY:
            if grupo is None or not grupo.get("analysis_report_path"):
                raise GuardFailedError("ANALYSIS->DEPLOYMENT_READY: analysis_report_path missing")
            return

        if current == STATE_DEPLOYMENT_READY and target == STATE_DEPLOYED:
            if self.state.get("tier3_gate_pending", True):
                raise GuardFailedError(
                    "DEPLOYMENT_READY->DEPLOYED: tier3_gate_pending == True (awaiting Ricardo authorization)"
                )
            return

        if current == STATE_DEPLOYED and target == STATE_NEXT_GRUPO:
            if grupo is None or not grupo.get("deployment_ack"):
                raise GuardFailedError("DEPLOYED->NEXT_GRUPO: deployment_ack == False")
            return

        if current == STATE_NEXT_GRUPO and target == STATE_RECICLAJE:
            # grupo_actual was already advanced when entering NEXT_GRUPO; verify the new grupo
            # is declared.
            next_gid = self.state.get("grupo_actual")
            if next_gid is None or str(next_gid) not in self.state.get("grupos", {}):
                raise GuardFailedError(
                    f"NEXT_GRUPO->RECICLAJE: next grupo {next_gid} not declared"
                )
            return

        if current == STATE_NEXT_GRUPO and target == STATE_TERMINAL_COMPLETE:
            if self.state.get("grupo_actual") is not None:
                raise GuardFailedError(
                    "NEXT_GRUPO->TERMINAL_COMPLETE: grupo_actual must be None (exhausted)"
                )
            return

        # Default: no guard => allow
        return

    def _advance_grupo_actual(self) -> None:
        current = self.state.get("grupo_actual")
        if current is None:
            return
        next_id = current + 1
        if next_id > MAX_GRUPO:
            self.state["grupo_actual"] = None
            return
        # Auto-declare from default plan if available
        if str(next_id) not in self.state.get("grupos", {}):
            if next_id in self.grupo_plan:
                self.declare_grupo(next_id, self.grupo_plan[next_id])
        self.state["grupo_actual"] = next_id

    # ------------------------------------------------------------------
    # primary source verification (Caveat #15)
    # ------------------------------------------------------------------

    def _verify_primary_source_for_reciclaje(self, grupo_id: int, sym: str) -> bool:
        """Caveat #15: file `regime_wf/{sym}_specialist_configs.json` must exist."""
        if self.primary_source_verifier is not None:
            return bool(self.primary_source_verifier(self.state, grupo_id, sym))
        # Default filesystem check
        candidate = Path("regime_wf") / f"{sym}_specialist_configs.json"
        return candidate.exists()

    # ------------------------------------------------------------------
    # simulated work helpers (DRY-RUN ONLY)
    # ------------------------------------------------------------------

    def mark_sym_done(self, grupo_id: int, sym: str) -> None:
        gid_key = str(grupo_id)
        grupo = self.state["grupos"][gid_key]
        if sym not in grupo["sym_pending_grupo_N"]:
            raise OrchestratorError(f"{sym} not in pending for grupo {grupo_id}")
        grupo["sym_pending_grupo_N"].remove(sym)
        if sym not in grupo["sym_done_grupo_N"]:
            grupo["sym_done_grupo_N"].append(sym)
        self._save_state_internal(reason=f"sym_done_{sym}")

    def mark_cross_option_done(self, grupo_id: int, option: str) -> None:
        if option not in CROSS_OPTIONS:
            raise OrchestratorError(f"unknown cross option {option}")
        gid_key = str(grupo_id)
        grupo = self.state["grupos"][gid_key]
        if option in grupo["cross_options_pending"]:
            grupo["cross_options_pending"].remove(option)
        if option not in grupo["cross_options_done"]:
            grupo["cross_options_done"].append(option)
        self._save_state_internal(reason=f"cross_option_done_{option}")

    def set_analysis_report(self, grupo_id: int, report_path: str) -> None:
        gid_key = str(grupo_id)
        self.state["grupos"][gid_key]["analysis_report_path"] = report_path
        self._save_state_internal(reason="analysis_report_set")

    def authorize_deploy(self, grupo_id: int) -> None:
        gid_key = str(grupo_id)
        grupo = self.state["grupos"][gid_key]
        if not grupo.get("tier3_gate_pending"):
            raise OrchestratorError(f"grupo {grupo_id} has no pending Tier 3 gate")
        grupo["tier3_gate_pending"] = False
        # Top-level gate cleared only when ALL pending grupos clear
        any_pending = any(
            g.get("tier3_gate_pending") for g in self.state.get("grupos", {}).values()
        )
        self.state["tier3_gate_pending"] = any_pending
        self._save_state_internal(reason=f"authorize_deploy_grupo_{grupo_id}")

    def mark_deployment_ack(self, grupo_id: int) -> None:
        gid_key = str(grupo_id)
        self.state["grupos"][gid_key]["deployment_ack"] = True
        self._save_state_internal(reason=f"deployment_ack_grupo_{grupo_id}")

    # ------------------------------------------------------------------
    # dry-run flow
    # ------------------------------------------------------------------

    def run_grupo(self, grupo_id: int, symbols: List[str], *, dry_run: bool = True) -> List[TierReport]:
        """Simulate full grupo flow. Dry-run only in this stub.

        Returns list of TierReport entries emitted. Tier 3 gate pauses the flow
        at DEPLOYMENT_READY — caller must invoke `authorize_deploy(grupo_id)` then
        `resume_grupo(grupo_id)` to continue.
        """
        if not dry_run:
            raise OrchestratorError(
                "run_grupo: real-compute path not implemented in stub (use --dry-run)"
            )
        reports: List[TierReport] = []
        gid_key = str(grupo_id)
        if gid_key not in self.state.get("grupos", {}):
            self.declare_grupo(grupo_id, symbols)
        if self.state.get("grupo_actual") != grupo_id:
            self.state["grupo_actual"] = grupo_id
            self._save_state_internal(reason="set_grupo_actual")

        # IDLE -> RECICLAJE
        if self.state["fase_actual"] == STATE_IDLE:
            self.transition(STATE_RECICLAJE, note=f"start_grupo_{grupo_id}_dry_run")

        # RECICLAJE: simulate 5 sym sequential (Caveat #14)
        if self.state["fase_actual"] == STATE_RECICLAJE:
            grupo = self.state["grupos"][gid_key]
            for sym in list(grupo["sym_pending_grupo_N"]):
                # Tier 1 silent — each sym done
                self.mark_sym_done(grupo_id, sym)
                reports.append(TierReport(tier=TIER_1, message=f"sym {sym} done (dry-run)", grupo_id=grupo_id))
            reports.append(TierReport(tier=TIER_2, message=f"RECICLAJE_GRUPO_{grupo_id} complete (5/5)", grupo_id=grupo_id))
            self.transition(STATE_CROSS_CLASS, note="reciclaje_complete_dry_run")

        # CROSS_CLASS: 3 options sequential strict
        if self.state["fase_actual"] == STATE_CROSS_CLASS:
            grupo = self.state["grupos"][gid_key]
            for opt in list(grupo["cross_options_pending"]):
                self.mark_cross_option_done(grupo_id, opt)
                reports.append(TierReport(tier=TIER_1, message=f"cross option {opt} done (dry-run)", grupo_id=grupo_id))
            reports.append(TierReport(tier=TIER_2, message=f"CROSS_CLASS_GRUPO_{grupo_id} complete (3/3)", grupo_id=grupo_id))
            self.transition(STATE_ANALYSIS, note="cross_class_complete_dry_run")

        # ANALYSIS: emit report
        if self.state["fase_actual"] == STATE_ANALYSIS:
            simulated_report = f"analysis_grupo_{grupo_id}_report_dry_run.json"
            self.set_analysis_report(grupo_id, simulated_report)
            reports.append(TierReport(tier=TIER_2, message=f"ANALYSIS_GRUPO_{grupo_id} report at {simulated_report}", grupo_id=grupo_id))
            self.transition(STATE_DEPLOYMENT_READY, note="analysis_complete_dry_run")

        # DEPLOYMENT_READY -> Tier 3 PAUSE
        if self.state["fase_actual"] == STATE_DEPLOYMENT_READY:
            reports.append(TierReport(
                tier=TIER_3,
                message=f"DEPLOYMENT_READY_GRUPO_{grupo_id} — PAUSE awaiting Ricardo authorization",
                grupo_id=grupo_id,
                context={"tier3_gate_pending": True},
            ))
            self.reports.extend(reports)
            return reports

        self.reports.extend(reports)
        return reports

    def resume_grupo(self, grupo_id: int, *, dry_run: bool = True) -> List[TierReport]:
        """Resume after Tier 3 authorization. Drives DEPLOYED -> NEXT_GRUPO."""
        if not dry_run:
            raise OrchestratorError("resume_grupo: real-compute path not implemented in stub")
        reports: List[TierReport] = []
        gid_key = str(grupo_id)

        # DEPLOYMENT_READY -> DEPLOYED (requires authorize_deploy called)
        if self.state["fase_actual"] == STATE_DEPLOYMENT_READY:
            self.transition(STATE_DEPLOYED, note="ricardo_authorized_dry_run")
            reports.append(TierReport(tier=TIER_2, message=f"DEPLOYED_GRUPO_{grupo_id} hook invoked (dry-run)", grupo_id=grupo_id))
            # Simulate deployment ack
            self.mark_deployment_ack(grupo_id)
            reports.append(TierReport(tier=TIER_2, message=f"deployment_ack received grupo {grupo_id} (dry-run)", grupo_id=grupo_id))

        # DEPLOYED -> NEXT_GRUPO
        if self.state["fase_actual"] == STATE_DEPLOYED:
            self.transition(STATE_NEXT_GRUPO, note="advance_grupo_dry_run")
            new_gid = self.state.get("grupo_actual")
            if new_gid is None:
                self.transition(STATE_TERMINAL_COMPLETE, note="all_grupos_done_dry_run")
                reports.append(TierReport(tier=TIER_3, message="TERMINAL_COMPLETE — cross-cartera 45 deployed (dry-run)", grupo_id=None))
            elif str(new_gid) in self.state.get("grupos", {}):
                # Next grupo declared (auto from plan or pre-declared) — enter its RECICLAJE
                self.transition(STATE_RECICLAJE, note=f"enter_reciclaje_grupo_{new_gid}_dry_run")
                reports.append(TierReport(tier=TIER_2, message=f"entered RECICLAJE_GRUPO_{new_gid}", grupo_id=new_gid))
            else:
                # Next grupo not yet declared — stay at NEXT_GRUPO awaiting external declaration
                reports.append(TierReport(
                    tier=TIER_2,
                    message=f"NEXT_GRUPO reached — grupo {new_gid} not yet declared (awaiting plan)",
                    grupo_id=new_gid,
                ))

        self.reports.extend(reports)
        return reports

    # ------------------------------------------------------------------
    # real-compute path RECICLAJE (Fase D.5.1)
    # ------------------------------------------------------------------

    def run_reciclaje_real_compute(
        self,
        grupo_id: int,
        *,
        chunk_size: int = 1_000_000,
        log_dir: str = ".",
        poll_interval: int = 120,
        timeout_per_sym: int = 18 * 3600,
        from_step: Optional[str] = None,
        recycle: bool = True,
        on_poll: Optional[Any] = None,
        launcher=None,
        waiter=None,
    ) -> List[TierReport]:
        """Real subprocess hookup for RECICLAJE step (Fase D.5.1).

        Iterates `sym_pending_grupo_N` for grupo, launches master.py per-sym
        sequentially (Caveat #14 sequential strict mandatory — paralelización
        REFUTED CATASTROPHIC cross-Sub-Sesiones precedent absoluto), polls until
        each subprocess completes, verifies primary-source output, marks each
        sym done on success (mark_sym_done), escalates Tier 3 on crash/bugcheck/
        partial/timeout.

        Requires state.fase_actual == STATE_RECICLAJE before invocation. After
        all 5 sym done, caller drives transition to CROSS_CLASS (guard verifies
        sym_done_grupo_N == symbols + primary_source_verifier).

        R1 v18 chunk_size=1M empirical-evidence-driven (cross-2-sym XRP+TRX
        validated 2026-05-12 — TDR 0x116 fix robust).

        Args:
            grupo_id: target grupo (1..MAX_GRUPO).
            chunk_size: R1 v18 max configs per kernel call.
            log_dir: dir for per-sym {log,err} files.
            poll_interval: seconds between completion polls.
            timeout_per_sym: max seconds before TIMEOUT (default 18h —
                empirical pace ~7K bars/h, large-bar sym BTC/ETH ~10-13h
                margin x1.5; small-bar Grupo 2 sym ~2-6h margin x3-x9).
            from_step: optional `--from-step VALUE` master.py CLI passthrough.
            launcher / waiter: injection points for tests. Default to
                compute_runner module.
        """
        if launcher is None or waiter is None:
            import compute_runner as _cr
            if launcher is None:
                launcher = _cr.launch_reciclaje_per_sym
            if waiter is None:
                waiter = _cr.wait_for_completion

        if self.state.get("fase_actual") != STATE_RECICLAJE:
            raise OrchestratorError(
                f"run_reciclaje_real_compute: requires fase_actual == RECICLAJE, "
                f"got {self.state.get('fase_actual')}"
            )

        gid_key = str(grupo_id)
        grupo = self.state.get("grupos", {}).get(gid_key)
        if grupo is None:
            raise OrchestratorError(f"grupo {grupo_id} not declared")

        reports: List[TierReport] = []

        # Snapshot pending list (mutation during iteration via mark_sym_done)
        pending_snapshot = list(grupo["sym_pending_grupo_N"])

        def _run_phase(sym, phase_label, from_step_arg, to_step_arg,
                       expected_file: Path):
            """Launch one master.py phase subprocess + wait + verify.

            Returns (success: bool, reports: List[TierReport]).
            """
            phase_reports: List[TierReport] = []
            ts_inner = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            log_p = str(Path(log_dir) /
                         f"reciclaje_{sym}_grupo{grupo_id}_{phase_label}_{ts_inner}.log")
            err_p = str(Path(log_dir) /
                         f"reciclaje_{sym}_grupo{grupo_id}_{phase_label}_{ts_inner}.err.log")

            handle_p = launcher(
                symbol=sym,
                chunk_size=chunk_size,
                log_path=log_p,
                err_path=err_p,
                from_step=from_step_arg,
                to_step=to_step_arg,
                recycle=recycle,
            )
            phase_reports.append(TierReport(
                tier=TIER_2,
                message=f"RECICLAJE {sym} {phase_label}: subprocess launched pid={handle_p.pid}",
                grupo_id=grupo_id,
                context={"pid": handle_p.pid, "symbol": sym, "phase": phase_label,
                         "log_path": log_p, "err_path": err_p,
                         "from_step": from_step_arg, "to_step": to_step_arg,
                         "expected_outputs": [str(p) for p in handle_p.expected_outputs]},
            ))

            # Persist active_subprocess record
            grupo.setdefault("active_subprocess", {})[f"RECICLAJE_{sym}_{phase_label}"] = {
                "pid": handle_p.pid, "symbol": sym, "phase": phase_label,
                "log_path": log_p, "err_path": err_p,
                "start_time": handle_p.start_time,
            }
            self._save_state_internal(
                reason=f"subprocess_launched_reciclaje_{sym}_{phase_label}")

            status_p = waiter(handle_p, poll_interval=poll_interval,
                               timeout=timeout_per_sym, on_poll=on_poll)
            status_str_p = status_p.value if hasattr(status_p, "value") else str(status_p)

            if status_str_p == "DONE_SUCCESS":
                grupo.get("active_subprocess", {}).pop(
                    f"RECICLAJE_{sym}_{phase_label}", None)
                # Caveat #15 primary-source verification
                if not expected_file.exists():
                    self.state["tier3_gate_pending"] = True
                    grupo["tier3_gate_pending"] = True
                    self._save_state_internal(
                        reason=f"tier3_reciclaje_{phase_label}_primary_source_missing_{sym}")
                    phase_reports.append(TierReport(
                        tier=TIER_3,
                        message=f"RECICLAJE {sym} {phase_label}: DONE_SUCCESS but "
                                f"primary-source {expected_file} MISSING (Caveat #15)",
                        grupo_id=grupo_id,
                        context={"symbol": sym, "phase": phase_label,
                                 "expected": str(expected_file), "status": status_str_p},
                    ))
                    return False, phase_reports
                phase_reports.append(TierReport(
                    tier=TIER_1,
                    message=f"RECICLAJE {sym} {phase_label}: DONE_SUCCESS pid={handle_p.pid}",
                    grupo_id=grupo_id,
                ))
                self._save_state_internal(reason=f"subprocess_done_reciclaje_{sym}_{phase_label}")
                return True, phase_reports

            # Phase failure -> Tier 3 PAUSE
            self.state["tier3_gate_pending"] = True
            grupo["tier3_gate_pending"] = True
            self._save_state_internal(
                reason=f"tier3_subprocess_failure_reciclaje_{sym}_{phase_label}")
            phase_reports.append(TierReport(
                tier=TIER_3,
                message=f"RECICLAJE {sym} {phase_label}: subprocess FAILED "
                        f"status={status_str_p} pid={handle_p.pid}",
                grupo_id=grupo_id,
                context={"status": status_str_p, "pid": handle_p.pid, "symbol": sym,
                         "phase": phase_label, "log_path": log_p, "err_path": err_p},
            ))
            return False, phase_reports

        # H_B isolation fix 2026-05-19 cardinal cross-Sub-Sesiones precedent absoluto:
        # Grupo 1 ZERO crashes 42h con `--from-step regime-wf` (step 4 isolated process)
        # vs Grupo 2 Crashes 12+13 con full pipeline same process refuted.
        # Per-sym 2-phase pattern: Phase 1 CPU steps 1-3 + Phase 2 GPU step 4 isolated.
        for sym in pending_snapshot:
            # Phase 1: CPU steps 1-3 (download + train + lite) — recycle=True forces refresh
            base_sym = sym.replace("/USDT", "").replace("USDT", "")
            phase1_expected = Path("output/production") / f"presets_{base_sym}USDT.csv"
            ok1, p1_reports = _run_phase(
                sym=sym, phase_label="phase1_cpu",
                from_step_arg=from_step,  # None=download / "lite" allowed for resume
                to_step_arg="lite",
                expected_file=phase1_expected,
            )
            reports.extend(p1_reports)
            if not ok1:
                self.reports.extend(reports)
                return reports  # Caveat #14 halt remaining sym

            # Phase 2: GPU step 4 isolated (regime-wf only in fresh process) — recycle
            # not needed since step 4 itself always re-computes specialists.
            phase2_expected = Path("regime_wf") / f"{base_sym}USDT_specialist_configs.json"
            ok2, p2_reports = _run_phase(
                sym=sym, phase_label="phase2_gpu",
                from_step_arg="regime-wf",
                to_step_arg="regime-wf",
                expected_file=phase2_expected,
            )
            reports.extend(p2_reports)
            if not ok2:
                self.reports.extend(reports)
                return reports

            # Both phases succeeded → mark sym done (canonical sym_done update)
            self.mark_sym_done(grupo_id, sym)
            self._save_state_internal(reason=f"sym_done_2phase_{sym}")

        # All sym done -> Tier 2 announce + caller drives transition to CROSS_CLASS
        reports.append(TierReport(
            tier=TIER_2,
            message=f"RECICLAJE_GRUPO_{grupo_id} all {len(pending_snapshot)} sym DONE "
                    f"(real-compute 2-phase H_B isolation pattern)",
            grupo_id=grupo_id,
        ))
        self.reports.extend(reports)
        return reports

    # ------------------------------------------------------------------
    # real-compute path (Fase D.5.2 CROSS_CLASS)
    # ------------------------------------------------------------------

    def run_cross_class_real_compute(
        self,
        grupo_id: int,
        *,
        output_root_prefix: str = "ccv_phase4",
        log_dir: str = ".",
        poll_interval: int = 120,
        timeout_per_option: int = 14 * 3600,
        on_poll: Optional[Any] = None,
        launcher=None,
        waiter=None,
    ) -> List[TierReport]:
        """Real subprocess hookup for CROSS_CLASS step (Fase D.5.2).

        Iterates `cross_options_pending` for grupo, launches sub_frame_3a1
        cross-classify subprocess sequentially (Caveat #14), polls until done,
        marks each option done on success, escalates Tier 3 on crash/bugcheck.

        Requires state.fase_actual == STATE_CROSS_CLASS before invocation.

        `launcher` / `waiter`: injection points for tests. Default to
        compute_runner module.
        """
        if launcher is None or waiter is None:
            import compute_runner as _cr
            if launcher is None:
                launcher = _cr.launch_cross_classification
            if waiter is None:
                waiter = _cr.wait_for_completion

        if self.state.get("fase_actual") != STATE_CROSS_CLASS:
            raise OrchestratorError(
                f"run_cross_class_real_compute: requires fase_actual == CROSS_CLASS, "
                f"got {self.state.get('fase_actual')}"
            )

        gid_key = str(grupo_id)
        grupo = self.state.get("grupos", {}).get(gid_key)
        if grupo is None:
            raise OrchestratorError(f"grupo {grupo_id} not declared")

        reports: List[TierReport] = []
        symbols = grupo["symbols"]

        # Strip USDT suffix for source identification
        def _strip_usdt(s: str) -> str:
            return s.replace("USDT", "").replace("/USDT", "")

        for option in list(grupo["cross_options_pending"]):
            if option == "PER_SYM_BASELINE":
                # NO compute — reuse existing regime_wf/{sym}_specialist_configs.json.
                # Caveat #15 primary source verification.
                missing = []
                for sym in symbols:
                    sym_clean = sym if sym.endswith("USDT") else f"{sym}USDT"
                    candidate = Path("regime_wf") / f"{sym_clean}_specialist_configs.json"
                    if not candidate.exists():
                        missing.append(str(candidate))
                if missing:
                    self.state["tier3_gate_pending"] = True
                    self._save_state_internal(reason=f"tier3_per_sym_baseline_missing")
                    reports.append(TierReport(
                        tier=TIER_3,
                        message=f"PER_SYM_BASELINE: missing primary-source files {missing}",
                        grupo_id=grupo_id,
                        context={"missing_files": missing, "option": option},
                    ))
                    self.reports.extend(reports)
                    return reports
                self.mark_cross_option_done(grupo_id, option)
                reports.append(TierReport(
                    tier=TIER_1,
                    message=f"PER_SYM_BASELINE marked done (primary-source verified, no compute)",
                    grupo_id=grupo_id,
                ))
                continue

            # BTC_SOURCE or ETH_SOURCE — launch 1 subprocess per target (Caveat #14)
            source_sym = "BTC" if option == "BTC_SOURCE" else "ETH"
            # Targets: all grupo symbols MINUS the source itself
            targets = [_strip_usdt(s) for s in symbols if _strip_usdt(s) != source_sym]
            if not targets:
                raise OrchestratorError(
                    f"option {option}: source {source_sym} not removable from grupo {symbols}"
                )

            output_root_base = f"{output_root_prefix}_{source_sym.lower()}_results"

            # Sequential strict per-target launch (CCV Phase 1+2+3 precedent +
            # smoke 2026-05-13 confirmed: 1 subprocess per (sym, source) — single
            # launch with multi-target mixes aggregated_per_cell metrics).
            option_failed = False
            for target in targets:
                target_clean = target if target.endswith("USDT") else f"{target}USDT"
                # Per-target output_root: {base}/{TARGET}USDT_{source_lower}_classified/
                # Matches CCV Phase 3 precedent naming.
                per_target_output_root = str(
                    Path(output_root_base) / f"{target_clean}_{source_sym.lower()}_classified"
                )
                ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                log_path = str(Path(log_dir) /
                                 f"cross_class_{option.lower()}_{target}_grupo{grupo_id}_{ts}.log")
                err_path = str(Path(log_dir) /
                                 f"cross_class_{option.lower()}_{target}_grupo{grupo_id}_{ts}.err.log")

                handle = launcher(
                    source=source_sym,
                    target=target,
                    output_root=per_target_output_root,
                    log_path=log_path,
                    err_path=err_path,
                )
                reports.append(TierReport(
                    tier=TIER_2,
                    message=f"{option}/{target}: subprocess launched pid={handle.pid}",
                    grupo_id=grupo_id,
                    context={"pid": handle.pid, "target": target,
                             "output_root": per_target_output_root,
                             "log_path": log_path, "err_path": err_path,
                             "expected_outputs": [str(p) for p in handle.expected_outputs]},
                ))

                # Persist intermediate state with active subprocess record
                grupo.setdefault("active_subprocess", {})[f"{option}_{target}"] = {
                    "pid": handle.pid,
                    "target": target,
                    "output_root": per_target_output_root,
                    "log_path": log_path,
                    "err_path": err_path,
                    "start_time": handle.start_time,
                }
                self._save_state_internal(reason=f"subprocess_launched_{option}_{target}")

                status = waiter(handle, poll_interval=poll_interval,
                                 timeout=timeout_per_option, on_poll=on_poll)
                status_str = status.value if hasattr(status, "value") else str(status)

                if status_str == "DONE_SUCCESS":
                    grupo.get("active_subprocess", {}).pop(f"{option}_{target}", None)
                    reports.append(TierReport(
                        tier=TIER_1,
                        message=f"{option}/{target}: DONE_SUCCESS pid={handle.pid}",
                        grupo_id=grupo_id,
                    ))
                    self._save_state_internal(reason=f"subprocess_done_{option}_{target}")
                    continue

                # Per-target failure -> Tier 3 PAUSE (Caveat #14 halt remaining)
                self.state["tier3_gate_pending"] = True
                grupo["tier3_gate_pending"] = True
                self._save_state_internal(reason=f"tier3_subprocess_failure_{option}_{target}")
                reports.append(TierReport(
                    tier=TIER_3,
                    message=f"{option}/{target}: subprocess FAILED status={status_str} pid={handle.pid}",
                    grupo_id=grupo_id,
                    context={"status": status_str, "pid": handle.pid, "target": target,
                             "log_path": log_path, "err_path": err_path, "option": option},
                ))
                option_failed = True
                break

            if option_failed:
                self.reports.extend(reports)
                return reports

            # All targets for this option succeeded -> mark option done
            self.mark_cross_option_done(grupo_id, option)
            reports.append(TierReport(
                tier=TIER_2,
                message=f"{option}: all {len(targets)} targets DONE",
                grupo_id=grupo_id,
                context={"targets": targets},
            ))

        # All options done -> Tier 2 announce + caller drives transition
        reports.append(TierReport(
            tier=TIER_2,
            message=f"CROSS_CLASS_GRUPO_{grupo_id} all 3 options DONE (real-compute)",
            grupo_id=grupo_id,
        ))
        self.reports.extend(reports)
        return reports

    # ------------------------------------------------------------------
    # real-compute analytical path (Fase D.6 — STAGE 2 analytical)
    # ------------------------------------------------------------------

    def run_analysis_real_compute(
        self,
        grupo_id: int,
        *,
        output_root_btc: str = "ccv_phase4_btc_results",
        output_root_eth: str = "ccv_phase4_eth_results",
        regime_wf_dir: str = "regime_wf",
        deployment_package_dir: Optional[str] = None,
        aggregator=None,
        package_preparer=None,
    ) -> List[TierReport]:
        """Real analytical aggregation for ANALYSIS step (Fase D.6).

        Reads cross-15 cross-classification outputs + per-sym baseline + identifies
        best source per sym + prepares deployment package + Tier 3 PAUSE Ricardo.

        Requires fase_actual == STATE_ANALYSIS before invocation.

        `aggregator` / `package_preparer`: injection points for tests. Default to
        analysis_aggregator module.
        """
        if aggregator is None or package_preparer is None:
            import analysis_aggregator as _aa
            if aggregator is None:
                aggregator = _aa.aggregate_cross_15_grupo
            if package_preparer is None:
                package_preparer = _aa.prepare_deployment_package

        if self.state.get("fase_actual") != STATE_ANALYSIS:
            raise OrchestratorError(
                f"run_analysis_real_compute: requires fase_actual == ANALYSIS, "
                f"got {self.state.get('fase_actual')}"
            )

        gid_key = str(grupo_id)
        grupo = self.state.get("grupos", {}).get(gid_key)
        if grupo is None:
            raise OrchestratorError(f"grupo {grupo_id} not declared")

        reports: List[TierReport] = []
        symbols = grupo["symbols"]

        # Step 1: Aggregate metrics cross-15
        analysis = aggregator(
            grupo_id=grupo_id,
            symbols=symbols,
            output_root_btc=output_root_btc,
            output_root_eth=output_root_eth,
            regime_wf_dir=regime_wf_dir,
        )
        reports.append(TierReport(
            tier=TIER_2,
            message=f"ANALYSIS_GRUPO_{grupo_id}: aggregated cross-15 metrics",
            grupo_id=grupo_id,
            context={"best_source_per_sym": dict(analysis.best_source_per_sym),
                     "grupo_summary": dict(analysis.grupo_summary)},
        ))

        # Step 2: Verify all sym have best source identified (Caveat #15)
        missing_best = [s for s in symbols if s not in analysis.best_source_per_sym]
        if missing_best:
            self.state["tier3_gate_pending"] = True
            grupo["tier3_gate_pending"] = True
            self._save_state_internal(reason="tier3_analysis_missing_best_source")
            reports.append(TierReport(
                tier=TIER_3,
                message=f"ANALYSIS_GRUPO_{grupo_id}: missing best source for syms {missing_best}",
                grupo_id=grupo_id,
                context={"missing_best": missing_best,
                         "metrics_errors": {
                             sym: {src: analysis.metrics_table[sym][src].error
                                    for src in analysis.metrics_table[sym]}
                             for sym in missing_best
                         }},
            ))
            self.reports.extend(reports)
            return reports

        # Step 3: Prepare deployment package
        if deployment_package_dir is None:
            deployment_package_dir = f"deployment_package_grupo_{grupo_id}"
        try:
            report_path, copied = package_preparer(
                analysis=analysis,
                output_dir=deployment_package_dir,
                output_root_btc=output_root_btc,
                output_root_eth=output_root_eth,
                regime_wf_dir=regime_wf_dir,
            )
        except FileNotFoundError as e:
            self.state["tier3_gate_pending"] = True
            grupo["tier3_gate_pending"] = True
            self._save_state_internal(reason="tier3_analysis_deployment_pkg_failure")
            reports.append(TierReport(
                tier=TIER_3,
                message=f"ANALYSIS_GRUPO_{grupo_id}: deployment package failure: {e}",
                grupo_id=grupo_id,
                context={"error": str(e)},
            ))
            self.reports.extend(reports)
            return reports

        # Step 4: Record analysis report path + transition to DEPLOYMENT_READY
        self.set_analysis_report(grupo_id, str(report_path))
        reports.append(TierReport(
            tier=TIER_2,
            message=f"ANALYSIS_GRUPO_{grupo_id}: deployment package at {report_path}",
            grupo_id=grupo_id,
            context={"report_path": str(report_path), "copied_files": [str(p) for p in copied]},
        ))
        self.transition(STATE_DEPLOYMENT_READY, note="analysis_complete_real_compute")

        # Step 5: Tier 3 PAUSE Ricardo deployment authorization MANDATORY
        reports.append(TierReport(
            tier=TIER_3,
            message=f"DEPLOYMENT_READY_GRUPO_{grupo_id} — PAUSE awaiting Ricardo authorization (Fase D.6 complete)",
            grupo_id=grupo_id,
            context={"tier3_gate_pending": True,
                     "deployment_package_dir": deployment_package_dir,
                     "report_path": str(report_path)},
        ))
        self.reports.extend(reports)
        return reports

    # ------------------------------------------------------------------
    # status summary
    # ------------------------------------------------------------------

    def status_summary(self) -> Dict[str, Any]:
        return {
            "fase_actual": self.state.get("fase_actual"),
            "grupo_actual": self.state.get("grupo_actual"),
            "tier3_gate_pending": self.state.get("tier3_gate_pending"),
            "grupos_count": len(self.state.get("grupos", {})),
            "last_completed": self.state.get("last_completed"),
        }


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Automation orchestrator for Path C reformulado (Fase D.2 + D.5.2)."
    )
    p.add_argument("--state-path", default=DEFAULT_STATE_PATH, help="path to automation_state.json")
    p.add_argument("--dry-run", action="store_true", help="MANDATORY for state-mutating ops in dry-run mode")
    p.add_argument("--mode", choices=["dry_run", "production"], default="dry_run",
                    help="dry_run (default) or production (Fase D.5.2 real-compute CROSS_CLASS)")
    p.add_argument("--grupo", type=int, default=None,
                    help="grupo id (required with --mode production)")
    p.add_argument("--stage", choices=["RECICLAJE", "CROSS_CLASS", "ANALYSIS"], default=None,
                    help="stage to run in --mode production (RECICLAJE Fase D.5.1 + "
                         "CROSS_CLASS Fase D.5.2 + ANALYSIS Fase D.6)")
    p.add_argument("--output-root-prefix", default="ccv_phase4",
                    help="output root prefix for cross-classification results (default: ccv_phase4)")
    p.add_argument("--log-dir", default=".",
                    help="dir for cross_class log/err files (default: cwd)")
    p.add_argument("--poll-interval", type=int, default=120,
                    help="seconds between poll cycles (default: 120)")
    p.add_argument("--timeout-per-option", type=int, default=14 * 3600,
                    help="hard timeout per cross option in seconds (default: 14h)")
    p.add_argument("--timeout-per-sym", type=int, default=18 * 3600,
                    help="hard timeout per RECICLAJE sym in seconds (default: 18h)")
    p.add_argument("--chunk-size", type=int, default=1_000_000,
                    help="R1 v18 chunk_size for RECICLAJE (default 1M empirical-validated)")
    p.add_argument("--from-step", default=None,
                    help="master.py --from-step passthrough for RECICLAJE (default: full pipeline)")
    p.add_argument("--no-recycle", action="store_true",
                    help="Skip --recycle for master.py — Phase 1 effectively no-op si "
                         "artifacts existen. Use for sub-test bit-exact comparison cumulative "
                         "vs manual --from-step regime-wf reference cumulative H_B validation.")
    p.add_argument("--simulate-grupo", type=int, default=None, help="simulate full flow for grupo N (1..9)")
    p.add_argument("--status", action="store_true", help="print status and exit (read-only)")
    p.add_argument("--authorize-deploy", type=int, default=None, help="clear Tier 3 gate for grupo N")
    p.add_argument("--reset", action="store_true", help="erase state file (use with care)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_argparser().parse_args(argv)
    # In dry-run mode the primary-source files do not need to exist (stub uses
    # simulated work). Inject an accept-all verifier so guards pass.
    verifier = None
    if args.dry_run:
        verifier = lambda state, gid, sym: True  # noqa: E731
    orch = AutomationOrchestrator(state_path=args.state_path, primary_source_verifier=verifier)

    if args.reset:
        if Path(args.state_path).exists():
            os.unlink(args.state_path)
        print(f"[reset] state file removed: {args.state_path}")
        return 0

    orch.load_state()

    if args.status:
        summary = orch.status_summary()
        print(json.dumps(summary, indent=2))
        return 0

    if args.authorize_deploy is not None:
        try:
            orch.authorize_deploy(args.authorize_deploy)
            print(f"[authorize_deploy] grupo {args.authorize_deploy} gate cleared")
            return 0
        except OrchestratorError as e:
            print(f"[authorize_deploy] ERROR: {e}", file=sys.stderr)
            return 1

    if args.simulate_grupo is not None:
        if not args.dry_run:
            print("ERROR: --simulate-grupo requires --dry-run in this stub", file=sys.stderr)
            return 2
        symbols = DEFAULT_GRUPO_PLAN.get(args.simulate_grupo)
        if symbols is None:
            print(f"ERROR: no default plan for grupo {args.simulate_grupo}", file=sys.stderr)
            return 2
        reports = orch.run_grupo(args.simulate_grupo, symbols, dry_run=True)
        for r in reports:
            print(f"[Tier {r.tier}] grupo={r.grupo_id} :: {r.message}")
        return 0

    # Fase D.5.2 + D.6 production path
    if args.mode == "production":
        if args.grupo is None:
            print("ERROR: --mode production requires --grupo N", file=sys.stderr)
            return 2
        if args.stage not in ("RECICLAJE", "CROSS_CLASS", "ANALYSIS"):
            print("ERROR: --mode production requires --stage RECICLAJE (D.5.1) "
                  "or CROSS_CLASS (D.5.2) or ANALYSIS (D.6).",
                  file=sys.stderr)
            return 2
        gid_key = str(args.grupo)
        if gid_key not in orch.state.get("grupos", {}):
            plan = DEFAULT_GRUPO_PLAN.get(args.grupo)
            if plan is None:
                print(f"ERROR: grupo {args.grupo} not declared and no default plan",
                      file=sys.stderr)
                return 2
            orch.declare_grupo(args.grupo, plan)
            orch.state["grupo_actual"] = args.grupo
            orch._save_state_internal(reason=f"auto_declare_grupo_{args.grupo}")

        if args.stage == "RECICLAJE":
            # Auto-transition IDLE -> RECICLAJE (Grupo 1 first launch) or
            # NEXT_GRUPO -> RECICLAJE (post-DEPLOYED prior grupo, advancing).
            current_fase = orch.state.get("fase_actual")
            if current_fase in (STATE_IDLE, STATE_NEXT_GRUPO):
                orch.transition(STATE_RECICLAJE,
                                note=f"production_launch_grupo_{args.grupo}")
            if orch.state.get("fase_actual") != STATE_RECICLAJE:
                print(f"ERROR: fase_actual must be RECICLAJE (got {orch.state.get('fase_actual')})",
                      file=sys.stderr)
                return 2
            try:
                reports = orch.run_reciclaje_real_compute(
                    args.grupo,
                    chunk_size=args.chunk_size,
                    log_dir=args.log_dir,
                    poll_interval=args.poll_interval,
                    timeout_per_sym=args.timeout_per_sym,
                    from_step=args.from_step,
                    recycle=not args.no_recycle,
                )
            except OrchestratorError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                return 1
        elif args.stage == "CROSS_CLASS":
            if orch.state.get("fase_actual") != STATE_CROSS_CLASS:
                print(f"ERROR: fase_actual must be CROSS_CLASS (got {orch.state.get('fase_actual')})",
                      file=sys.stderr)
                return 2
            try:
                reports = orch.run_cross_class_real_compute(
                    args.grupo,
                    output_root_prefix=args.output_root_prefix,
                    log_dir=args.log_dir,
                    poll_interval=args.poll_interval,
                    timeout_per_option=args.timeout_per_option,
                )
            except OrchestratorError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                return 1
        else:  # ANALYSIS
            if orch.state.get("fase_actual") != STATE_ANALYSIS:
                print(f"ERROR: fase_actual must be ANALYSIS (got {orch.state.get('fase_actual')})",
                      file=sys.stderr)
                return 2
            try:
                reports = orch.run_analysis_real_compute(
                    args.grupo,
                    output_root_btc=f"{args.output_root_prefix}_btc_results",
                    output_root_eth=f"{args.output_root_prefix}_eth_results",
                )
            except OrchestratorError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                return 1

        for r in reports:
            print(f"[Tier {r.tier}] grupo={r.grupo_id} :: {r.message}")
        if orch.state.get("tier3_gate_pending"):
            return 3
        return 0

    print("no-op (try --status or --dry-run --simulate-grupo N or --mode production --grupo N --stage CROSS_CLASS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
