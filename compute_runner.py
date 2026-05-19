"""Compute runner for AutomationOrchestrator real-compute hookup (Fase D.5.2).

Scope this module:
- Subprocess launch for cross-classification (sub_frame_3a1_gmm_n_pthreshold_grid.py
  --cross-classify-source SOURCE --symbols TARGETS).
- Subprocess wrapper for reciclaje master.py (Fase D.5.1 future use).
- Polling for completion via PID alive + output files exist + Event Log 1001 bugcheck.
- Tier 3 escalation on subprocess crash or TDR bugcheck.

NOT in scope:
- Analysis logic (cross-15-classifications matrix, Gate B evaluation) — Fase D.6.
- Bot v2.5.0 deployment hook — Fase D.7.
- Real watchdog filesystem events (uses polling instead — simpler, sufficient).

Caveat #14 sequential strict: callers must serialize launches (one at a time per
process). compute_runner does NOT enforce this — that's orchestrator's job.

Caveat #15 primary source verification: callers MUST verify expected_outputs paths
exist post-completion (compute_runner provides verify_outputs helper).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


# -----------------------------------------------------------------------------
# Status enum
# -----------------------------------------------------------------------------

class CompletionStatus(str, Enum):
    RUNNING = "RUNNING"
    DONE_SUCCESS = "DONE_SUCCESS"
    DONE_PARTIAL = "DONE_PARTIAL"
    CRASHED = "CRASHED"
    BUGCHECK = "BUGCHECK"
    TIMEOUT = "TIMEOUT"


# -----------------------------------------------------------------------------
# RunHandle dataclass
# -----------------------------------------------------------------------------

@dataclass
class RunHandle:
    """Handle to a launched subprocess + its expected outputs."""
    pid: int
    cmd: List[str]
    log_path: Path
    err_path: Path
    expected_outputs: List[Path]
    start_time: float
    initial_bugcheck_count: int = 0
    label: str = ""
    exit_code: Optional[int] = None


# -----------------------------------------------------------------------------
# Platform-specific helpers (Windows-only; tests can monkey-patch)
# -----------------------------------------------------------------------------

def _pid_alive_default(pid: int) -> bool:
    """Check if PID is alive via PowerShell Get-Process. Returns True if alive."""
    if pid <= 0:
        return False
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"if (Get-Process -Id {pid} -EA SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}"],
            capture_output=True, timeout=15,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _bugcheck_count_default(hours: int = 4) -> int:
    """Query Event Log for bugcheck 1001 count last N hours."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-WinEvent -FilterHashtable @{{LogName='System'; ID=1001;"
             f" StartTime=(Get-Date).AddHours(-{hours})}} -EA SilentlyContinue |"
             f" Measure-Object).Count"],
            capture_output=True, text=True, timeout=15,
        )
        try:
            return int(r.stdout.strip() or "0")
        except ValueError:
            return 0
    except (subprocess.TimeoutExpired, OSError):
        return 0


def _get_pid_exit_code_default(pid: int) -> Optional[int]:
    """Get exit code of a (presumably dead) PID. Returns None if alive/unknown."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"$p = Get-Process -Id {pid} -EA SilentlyContinue; "
             f"if ($p) {{ Write-Output 'ALIVE' }} else {{ Write-Output 'GONE' }}"],
            capture_output=True, text=True, timeout=15,
        )
        # PowerShell doesn't expose exit codes for exited processes via Get-Process.
        # Return None as "unknown" — caller must rely on outputs + bugcheck.
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


# Module-level injection points for tests
pid_alive: Callable[[int], bool] = _pid_alive_default
bugcheck_count: Callable[[int], int] = _bugcheck_count_default
get_pid_exit_code: Callable[[int], Optional[int]] = _get_pid_exit_code_default


# -----------------------------------------------------------------------------
# Subprocess launch helpers
# -----------------------------------------------------------------------------

def launch_subprocess(cmd: List[str], log_path: str, err_path: str,
                       expected_outputs: List[str],
                       label: str = "",
                       cwd: Optional[str] = None) -> RunHandle:
    """Launch a Python subprocess with stdout/stderr redirected to files.

    Returns RunHandle immediately. Caller must poll for completion.
    """
    log_p = Path(log_path)
    err_p = Path(err_path)
    log_p.parent.mkdir(parents=True, exist_ok=True)
    err_p.parent.mkdir(parents=True, exist_ok=True)
    out_f = open(log_p, "wb")
    err_f = open(err_p, "wb")
    proc = subprocess.Popen(
        cmd,
        stdout=out_f,
        stderr=err_f,
        cwd=cwd,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    out_f.close()  # Popen inherits descriptors via OS handles on Windows
    err_f.close()
    initial_bc = bugcheck_count(2)
    return RunHandle(
        pid=proc.pid,
        cmd=list(cmd),
        log_path=log_p,
        err_path=err_p,
        expected_outputs=[Path(p) for p in expected_outputs],
        start_time=time.time(),
        initial_bugcheck_count=initial_bc,
        label=label,
    )


def launch_cross_classification(
    source: str,
    target: str,
    output_root: str,
    log_path: str,
    err_path: str,
    script_path: str = "analysis_scripts/sub_frame_3a1_gmm_n_pthreshold_grid.py",
    python_exe: Optional[str] = None,
    cells: str = "baseline",
) -> RunHandle:
    """Launch sub_frame_3a1 cross-classify subprocess for ONE target.

    CCV Phase 1+2+3 precedent (confirmed empirically by smoke 2026-05-13):
    one subprocess per (sym, source) pair — aggregated_per_cell metrics are
    per-symbol; passing multiple targets in one launch mixes metrics across
    symbols incorrectly.

    Args:
        source: source symbol for GMM joblib reuse (e.g. "BTC").
        target: target symbol (e.g. "ETH"). Single symbol per launch.
        output_root: dir for THIS cross-classification's results (typically
            named e.g. ccv_phase4_btc_results/ETHUSDT_btc_classified/ per
            CCV precedent — caller composes the path).
        log_path / err_path: stdout / stderr redirect.
        cells: cells filter (default "baseline" — without this filter the
            script runs all 31 cells = catastrophic compute cost).

    Returns RunHandle with expected_outputs = [output_root/sub_frame_3a1_summary.json].
    """
    if python_exe is None:
        python_exe = sys.executable or "python"
    cmd = [
        python_exe,
        script_path,
        "--cross-classify-source", source,
        "--symbols", target,
        "--output-root", output_root,
        "--cells", cells,
    ]
    # Expected outputs (empirically confirmed by smoke 2026-05-13):
    # - output_root/sub_frame_3a1_summary.json (aggregated metrics for this target)
    # - output_root/cell_baseline/{target}USDT/{target}USDT_specialist_configs.json
    target_clean = target if target.endswith("USDT") else f"{target}USDT"
    expected = [
        Path(output_root) / "sub_frame_3a1_summary.json",
        Path(output_root) / "cell_baseline" / target_clean / f"{target_clean}_specialist_configs.json",
    ]
    return launch_subprocess(
        cmd=cmd,
        log_path=log_path,
        err_path=err_path,
        expected_outputs=[str(p) for p in expected],
        label=f"cross_classify_{source}_x_{target}",
    )


def launch_reciclaje_per_sym(
    symbol: str,
    *,
    chunk_size: int = 1_000_000,
    log_path: str = "reciclaje.log",
    err_path: str = "reciclaje.err.log",
    master_path: str = "master.py",
    python_exe: Optional[str] = None,
    from_step: Optional[str] = None,
    to_step: Optional[str] = None,
    recycle: bool = True,
    extra_args: Optional[List[str]] = None,
) -> RunHandle:
    """Launch master.py reciclaje subprocess for a SINGLE symbol (Fase D.5.1).

    Caveat #14 sequential strict pattern — caller invokes once per sym in grupo,
    serializing launches. Each subprocess runs master.py pipeline producing the
    canonical specialist config JSON in regime_wf/ (when step 4 included).

    H_B isolation fix 2026-05-19 cross-Crash-12+13 cumulative cross-Sub-Sesiones
    precedent absoluto refuted full-pipeline pattern (steps 1-4 same process).
    Grupo 1 ZERO crashes 42h con `--from-step regime-wf` aislado vs Grupo 2 crashed.
    Caller must split per-sym into 2 phases: (Phase 1) from_step=None +
    to_step="lite" → steps 1-3 CPU only; (Phase 2) from_step="regime-wf" → step 4
    GPU isolated fresh process. Expected output (regime_wf JSON) only available
    after Phase 2.

    R1 v18 chunk_size=1M empirical-evidence-driven (XRP+TRX cross-2-sym 16h51m
    cumulative + ONDO step 4 isolated 2026-05-19 cumulative cross-Sub-Sesiones).

    Args:
        symbol: e.g. "ONDO", "ONDO/USDT", or "ONDOUSDT" (normalized internally).
        chunk_size: R1 v18 max configs per kernel call (default 1_000_000).
        from_step: optional `--from-step VALUE` to skip earlier steps.
        to_step: optional `--to-step VALUE` to stop after this step (inclusive).
            H_B isolation pattern: Phase 1 to_step="lite", Phase 2 from_step="regime-wf".
        recycle: pass `--recycle` to master.py. Default True for canonical
            reciclaje semantics (force re-download + re-train + re-generate).
        extra_args: additional CLI args appended after the standard set.

    Expected output: regime_wf/{SYM}USDT_specialist_configs.json (only if step 4
        included, i.e. to_step is None or to_step="regime-wf").
    """
    if python_exe is None:
        python_exe = sys.executable or "python"
    cmd = [python_exe, master_path]
    if from_step:
        cmd.extend(["--from-step", from_step])
    if to_step:
        cmd.extend(["--to-step", to_step])
    if recycle:
        cmd.append("--recycle")
    cmd.extend(["--symbols", _normalize_symbol(symbol)])
    cmd.extend(["--chunk-size", str(chunk_size)])
    if extra_args:
        cmd.extend(extra_args)
    base = symbol.replace("/USDT", "").replace("USDT", "")
    # Expected output depends on whether step 4 (regime-wf) is included
    step_4_included = (to_step is None or to_step == "regime-wf")
    if step_4_included:
        expected = [Path("regime_wf") / f"{base}USDT_specialist_configs.json"]
    else:
        # Phase 1 stops at lite → presets file is the canonical output marker
        expected = [Path("output/production") / f"presets_{base}USDT.csv"]
    return launch_subprocess(
        cmd=cmd,
        log_path=log_path,
        err_path=err_path,
        expected_outputs=[str(p) for p in expected],
        label=f"reciclaje_{base}",
    )


def _normalize_symbol(s: str) -> str:
    s = s.strip()
    if "/USDT" in s:
        return s
    if s.endswith("USDT"):
        return s[:-4] + "/USDT"
    return f"{s}/USDT"


def _strip_slash(s: str) -> str:
    return s.replace("/USDT", "")


# -----------------------------------------------------------------------------
# Polling + completion detection
# -----------------------------------------------------------------------------

def verify_outputs(handle: RunHandle) -> Tuple[bool, List[Path]]:
    """Return (all_present, present_list)."""
    present = [p for p in handle.expected_outputs if p.exists()]
    return (len(present) == len(handle.expected_outputs), present)


def poll_completion(handle: RunHandle, *, bugcheck_lookback_hours: int = 4) -> CompletionStatus:
    """Single poll cycle. Returns current status.

    Order:
    1. Check bugcheck count > initial -> BUGCHECK (TDR escalation)
    2. Check PID alive
       - alive -> RUNNING
       - dead + all outputs present -> DONE_SUCCESS
       - dead + partial outputs -> DONE_PARTIAL
       - dead + no outputs -> CRASHED
    """
    new_bc = bugcheck_count(bugcheck_lookback_hours)
    if new_bc > handle.initial_bugcheck_count:
        return CompletionStatus.BUGCHECK

    if pid_alive(handle.pid):
        return CompletionStatus.RUNNING

    # PID dead — assess outputs
    all_present, present = verify_outputs(handle)
    if all_present:
        return CompletionStatus.DONE_SUCCESS
    if present:
        return CompletionStatus.DONE_PARTIAL
    return CompletionStatus.CRASHED


def wait_for_completion(
    handle: RunHandle,
    *,
    poll_interval: int = 120,
    timeout: int = 14 * 3600,
    on_poll: Optional[Callable[[RunHandle, CompletionStatus, int], None]] = None,
) -> CompletionStatus:
    """Block until handle completes. Polls every poll_interval seconds.

    Returns final CompletionStatus. RUNNING/TIMEOUT only if timeout hit before completion.

    on_poll(handle, status, elapsed_seconds) optional callback at each poll.
    """
    deadline = handle.start_time + timeout
    while time.time() < deadline:
        elapsed = int(time.time() - handle.start_time)
        status = poll_completion(handle)
        if on_poll is not None:
            on_poll(handle, status, elapsed)
        if status in (CompletionStatus.DONE_SUCCESS, CompletionStatus.DONE_PARTIAL,
                       CompletionStatus.CRASHED, CompletionStatus.BUGCHECK):
            return status
        time.sleep(poll_interval)
    return CompletionStatus.TIMEOUT
