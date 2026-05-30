"""[DEPRECATED 2026-05-30 — Caveat #22 §13.2] NO USAR. Invoca regime_walk_forward.py
por CLI SIN la CONFIG metodológica productiva (no expone --fwd-min-trades/--fwd-min-pf;
corre defaults divergentes _FWD_MIN_TRADES=25/_FWD_MIN_PF=1.1 vs productivo 15/1.0 +
toxic_tail fijo). CASO ORIGEN de Caveat #22 (contaminación 3-mismatch, 58h invalidadas).
SUPERSEDED por run_p4_sequencer.py + audit_wrapper_master.py (patrón master.step_regime_wf,
bit-exact P4). Para comparación metodológica vs productivo usar el wrapper master.py.

Sequencer for ETAPA 2 walk-forward audit (Caveat #21 §13.2).

Runs sequentially (Caveat #14 sequential strict, NO parallel):
  1. ONDO/USDT × B2 (per-cluster full-history pool)
  2. ONDO/USDT × B1 (agnostic full-history pool)
  3. BTC/USDT  × B1
  4. BTC/USDT  × B2

Each invocation: regime_walk_forward.py with custom --presets-dir + --output-dir.

Designed for detached operation (Start-Process Hidden). One subprocess at a
time. On any non-zero exit code, sequencer stops (Tier 3 escalation pattern).

Each walk-forward is GPU-isolated (separate fresh process) preserving H_B
isolation fix (commit 779bef0) cumulative cross-Sub-Sesiones precedent absoluto.

NOT productive — uses audit_etapa2_<TS>/ directory tree. Productive
regime_wf/ untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Sequence: (symbol, mode_label, presets_subdir)
# ETAPA 2 (indices 0-3): ONDO+BTC × {B1, B2} — completed 2026-05-22/24
# ETAPA 2-EXT (indices 4-7): SEI→POL→BNB→ETH × B2 only — smallest first risk mitigation
SEQUENCE = [
    ("ONDO/USDT", "B2", "B2"),
    ("ONDO/USDT", "B1", "B1"),
    ("BTC/USDT",  "B1", "B1"),
    ("BTC/USDT",  "B2", "B2"),
    ("SEI/USDT",  "B2", "B2"),   # ~3-5h (24K bars)
    ("POL/USDT",  "B2", "B2"),   # ~5-7h (15K bars)
    ("BNB/USDT",  "B2", "B2"),   # ~9-10h (74K bars)
    ("ETH/USDT",  "B2", "B2"),   # ~9-11h (76K bars)
]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_one(symbol: str, mode_label: str, audit_dir: Path,
            presets_subdir: str) -> int:
    """Launch one regime_walk_forward.py subprocess + wait for completion.

    Returns subprocess exit code.
    """
    sym_clean = symbol.replace("/", "").replace("USDT", "")
    presets_dir = audit_dir / presets_subdir
    output_dir = audit_dir / f"wf_{mode_label}_{sym_clean}"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = audit_dir / f"sequencer_{sym_clean}_{mode_label}_{ts}.log"
    err_path = audit_dir / f"sequencer_{sym_clean}_{mode_label}_{ts}.err.log"

    cmd = [
        sys.executable, "regime_walk_forward.py",
        "--symbols", symbol,
        "--presets-dir", str(presets_dir),
        "--output-dir", str(output_dir),
    ]
    print(f"\n[{utcnow_iso()}] LAUNCH {symbol} × {mode_label}")
    print(f"  cmd: {' '.join(cmd)}")
    print(f"  log: {log_path}")

    t0 = time.time()
    with open(log_path, "wb") as out_f, open(err_path, "wb") as err_f:
        proc = subprocess.Popen(
            cmd, stdout=out_f, stderr=err_f,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    rc = proc.wait()
    elapsed = time.time() - t0
    print(f"[{utcnow_iso()}] EXIT {symbol} × {mode_label} rc={rc} elapsed={elapsed/60:.1f}min")
    return rc


def main():
    p = argparse.ArgumentParser(description="ETAPA 2 walk-forward sequencer")
    p.add_argument("--audit-dir", required=True,
                    help="Audit base dir with B1/ and B2/ subdirs containing presets CSVs")
    p.add_argument("--start-from", type=int, default=0,
                    help="Index in SEQUENCE to start from (default 0 = all 4)")
    p.add_argument("--only", type=int, default=None,
                    help="Run only this single index from SEQUENCE")
    args = p.parse_args()

    audit_dir = Path(args.audit_dir)
    if not audit_dir.exists():
        print(f"ERROR: audit dir not found: {audit_dir}", file=sys.stderr)
        return 1

    progress_path = audit_dir / "sequencer_progress.json"
    progress = []
    if progress_path.exists():
        try:
            progress = json.loads(progress_path.read_text())
        except Exception:
            progress = []

    indices_to_run = (
        [args.only] if args.only is not None
        else list(range(args.start_from, len(SEQUENCE)))
    )

    print(f"[{utcnow_iso()}] SEQUENCER START audit_dir={audit_dir} indices={indices_to_run}")
    for i in indices_to_run:
        sym, mode_label, sub = SEQUENCE[i]
        entry = {
            "index": i, "symbol": sym, "mode": mode_label,
            "started_at": utcnow_iso(),
        }
        rc = run_one(sym, mode_label, audit_dir, sub)
        entry["finished_at"] = utcnow_iso()
        entry["exit_code"] = rc
        progress.append(entry)
        progress_path.write_text(json.dumps(progress, indent=2))
        if rc != 0:
            print(f"[{utcnow_iso()}] STOP — exit code {rc} on index {i} ({sym} × {mode_label}). "
                  f"Tier 3 escalation.")
            return rc
    print(f"[{utcnow_iso()}] SEQUENCER COMPLETE — all {len(indices_to_run)} runs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
