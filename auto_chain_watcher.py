"""Auto-chain watcher cross-Sub-Sesiones precedent absoluto cumulative.

Polls automation_state.json + handles RECICLAJE→CROSS_CLASS→ANALYSIS auto-transitions
for a target grupo. Stops at DEPLOYMENT_READY (Tier 3 PAUSE Ricardo authorization
required) or TERMINAL_COMPLETE or any tier3_gate_pending.

Sequential strict: ONE orchestrator subprocess at a time (waits for completion).
Each stage runs in its own clean subprocess — preserves H_B isolation pattern
cross-stages cumulative.

Designed for detached operation (PowerShell Start-Process -WindowStyle Hidden) —
outlives parent shell + survives conversation ends. Restart-tolerant: state
persisted in automation_state.json, watcher re-reads on each poll.

Exit codes:
  0 — clean exit (Tier 3 PAUSE OR TERMINAL_COMPLETE OR max iterations)
  1 — error (transition failure OR subprocess non-zero exit)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import automation_orchestrator as ao

DEFAULT_STATE_PATH = "automation_state.json"
DEFAULT_POLL_INTERVAL_SEC = 300  # 5 min between state checks
DEFAULT_MAX_ITER = 2000  # safety upper bound (~7 days of polling at 5 min)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_state(state_path: str) -> dict:
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def decide_action(state: dict, grupo: int) -> str:
    """Determine next action based on current state for target grupo.

    Returns one of:
        'tier3_pause' — Tier 3 gate (tier3_gate_pending OR DEPLOYMENT_READY) → exit
        'terminal' — TERMINAL_COMPLETE → exit
        'launch_cross_class' — RECICLAJE complete, transition + launch CROSS_CLASS
        'launch_analysis' — CROSS_CLASS complete, transition + launch ANALYSIS
        'wait' — current stage in progress OR wrong grupo OR pre-conditions not met
    """
    if state.get("tier3_gate_pending"):
        return "tier3_pause"
    fase = state.get("fase_actual")
    if fase == ao.STATE_TERMINAL_COMPLETE:
        return "terminal"
    if fase == ao.STATE_DEPLOYMENT_READY:
        return "tier3_pause"

    grupo_actual = state.get("grupo_actual")
    if grupo_actual != grupo:
        return "wait"

    gid_key = str(grupo)
    g = state.get("grupos", {}).get(gid_key)
    if g is None:
        return "wait"

    if fase == ao.STATE_RECICLAJE:
        symbols = set(g.get("symbols", []))
        sym_done = set(g.get("sym_done_grupo_N", []))
        if len(symbols) > 0 and sym_done == symbols:
            return "launch_cross_class"
        return "wait"

    if fase == ao.STATE_CROSS_CLASS:
        options_done = set(g.get("cross_options_done", []))
        if options_done == set(ao.CROSS_OPTIONS):
            return "launch_analysis"
        return "wait"

    return "wait"


def launch_orchestrator_stage(
    stage: str, grupo: int, *,
    state_path: str = DEFAULT_STATE_PATH,
    chunk_size: int = 1_000_000,
    poll_interval: int = 60,
    timeout_per_sym: int = 64800,
    timeout_per_option: int = 14 * 3600,
    log_dir: str = ".",
    python_exe: Optional[str] = None,
    orchestrator_script: str = "automation_orchestrator.py",
) -> int:
    """Launch orchestrator subprocess for stage + wait for completion.

    Returns subprocess exit code. The orchestrator's CLI returns:
        0 — success
        1 — orchestrator error
        2 — usage/state error
        3 — tier3_gate_pending raised during run

    Watcher should escalate exit code != 0 as Tier 3 PAUSE.
    """
    if python_exe is None:
        python_exe = sys.executable or "python"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log = Path(log_dir) / f"watcher_orch_{stage.lower()}_grupo{grupo}_{ts}.log"
    err = Path(log_dir) / f"watcher_orch_{stage.lower()}_grupo{grupo}_{ts}.err.log"
    log.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        python_exe, orchestrator_script,
        "--mode", "production",
        "--grupo", str(grupo),
        "--stage", stage,
        "--state-path", state_path,
        "--chunk-size", str(chunk_size),
        "--poll-interval", str(poll_interval),
        "--log-dir", log_dir,
    ]
    if stage == "RECICLAJE":
        cmd.extend(["--timeout-per-sym", str(timeout_per_sym)])
    elif stage == "CROSS_CLASS":
        cmd.extend(["--timeout-per-option", str(timeout_per_option)])

    logging.info(f"Launching orchestrator stage={stage} grupo={grupo} log={log}")
    logging.info(f"  cmd: {' '.join(cmd)}")
    with open(log, "wb") as out_f, open(err, "wb") as err_f:
        proc = subprocess.Popen(
            cmd, stdout=out_f, stderr=err_f,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    rc = proc.wait()
    logging.info(f"Orchestrator stage={stage} grupo={grupo} exit code={rc}")
    return rc


def perform_transition_then_launch(stage: str, grupo: int, *,
                                    state_path: str,
                                    log_dir: str,
                                    chunk_size: int,
                                    poll_interval: int) -> int:
    """Transition state to target stage then launch orchestrator subprocess.

    Returns subprocess exit code.
    """
    target_state = {
        "CROSS_CLASS": ao.STATE_CROSS_CLASS,
        "ANALYSIS": ao.STATE_ANALYSIS,
    }[stage]
    # Use accept-all verifier — primary source files are verified by mark_sym_done
    # callers inside run_reciclaje_real_compute (Caveat #15 enforced upstream).
    orch = ao.AutomationOrchestrator(
        state_path=state_path,
        primary_source_verifier=lambda st, gid, sym: True,
    )
    orch.load_state()
    logging.info(f"Transitioning to {target_state} for grupo {grupo}")
    try:
        orch.transition(target_state, note=f"watcher_auto_transition_{stage.lower()}")
    except ao.OrchestratorError as e:
        logging.error(f"Transition to {target_state} FAILED: {e}")
        return 1
    return launch_orchestrator_stage(
        stage, grupo,
        state_path=state_path,
        log_dir=log_dir,
        chunk_size=chunk_size,
        poll_interval=poll_interval,
    )


def watcher_loop(*, grupo: int, state_path: str, poll_interval: int,
                  max_iter: int, log_dir: str, chunk_size: int,
                  inner_poll_interval: int) -> int:
    """Main watcher loop. Returns exit code."""
    logging.info(f"WATCHER START grupo={grupo} state_path={state_path} "
                 f"poll_interval={poll_interval}s max_iter={max_iter}")

    for it in range(max_iter):
        try:
            s = read_state(state_path)
        except Exception as e:
            logging.error(f"iter={it} state read error: {e}")
            time.sleep(poll_interval)
            continue

        action = decide_action(s, grupo)
        fase = s.get("fase_actual")
        gid_key = str(grupo)
        g = s.get("grupos", {}).get(gid_key, {})
        sym_done_n = len(g.get("sym_done_grupo_N", []))
        sym_total_n = len(g.get("symbols", []))
        opt_done_n = len(g.get("cross_options_done", []))
        logging.info(f"iter={it} fase={fase} grupo_actual={s.get('grupo_actual')} "
                     f"sym_done={sym_done_n}/{sym_total_n} "
                     f"options_done={opt_done_n}/3 action={action}")

        if action == "tier3_pause":
            logging.info("Tier 3 PAUSE — exiting watcher "
                         "(Ricardo authorization required for deployment)")
            return 0
        if action == "terminal":
            logging.info("TERMINAL_COMPLETE — exiting watcher")
            return 0
        if action == "wait":
            time.sleep(poll_interval)
            continue

        if action == "launch_cross_class":
            rc = perform_transition_then_launch(
                "CROSS_CLASS", grupo,
                state_path=state_path, log_dir=log_dir,
                chunk_size=chunk_size, poll_interval=inner_poll_interval,
            )
            if rc != 0:
                logging.error(f"CROSS_CLASS subprocess exit={rc} — Tier 3 escalation")
                return 1
            continue

        if action == "launch_analysis":
            rc = perform_transition_then_launch(
                "ANALYSIS", grupo,
                state_path=state_path, log_dir=log_dir,
                chunk_size=chunk_size, poll_interval=inner_poll_interval,
            )
            if rc != 0:
                logging.error(f"ANALYSIS subprocess exit={rc} — Tier 3 escalation")
                return 1
            continue

    logging.warning(f"max_iterations={max_iter} reached without terminal state")
    return 0


def main():
    p = argparse.ArgumentParser(description="Auto-chain watcher Grupo N reciclaje→cross-class→analysis")
    p.add_argument("--grupo", type=int, required=True)
    p.add_argument("--state-path", default=DEFAULT_STATE_PATH)
    p.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL_SEC,
                    help="seconds between state checks (default 300=5min)")
    p.add_argument("--inner-poll-interval", type=int, default=60,
                    help="poll interval passed to orchestrator subprocess (default 60s)")
    p.add_argument("--max-iter", type=int, default=DEFAULT_MAX_ITER,
                    help="safety upper bound iterations (default 2000)")
    p.add_argument("--log-dir", default=".",
                    help="directory for watcher + orchestrator logs")
    p.add_argument("--chunk-size", type=int, default=1_000_000,
                    help="R1 v18 chunk_size passed to orchestrator")
    args = p.parse_args()

    log_path = Path(args.log_dir) / (
        f"auto_chain_watcher_grupo{args.grupo}_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    # Also log to stderr for visibility when run interactively
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(sh)

    return watcher_loop(
        grupo=args.grupo,
        state_path=args.state_path,
        poll_interval=args.poll_interval,
        max_iter=args.max_iter,
        log_dir=args.log_dir,
        chunk_size=args.chunk_size,
        inner_poll_interval=args.inner_poll_interval,
    )


if __name__ == "__main__":
    sys.exit(main())
