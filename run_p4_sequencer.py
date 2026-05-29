"""Sequencer P4 — re-run B2 walk-forwards vía wrapper master.py (CONFIG productiva COMPLETE).

Sequential strict (Caveat #14). Each invocation goes through audit_wrapper_master.py
which uses master.step_regime_wf — guarantees apples-to-apples vs deployed A.

Smallest-first risk mitigation order: ONDO → POL → SEI → BNB → ETH → BTC.

Output: audit_etapa2_20260522_213747/wf_B2_dyn_<SYM>/{SYM}USDT_specialist_configs.json
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# Order: smallest first for risk mitigation
SEQUENCE = [
    "ONDO/USDT",   # ~2h (10K bars)
    "POL/USDT",    # ~4-5h (15K bars)
    "SEI/USDT",    # ~5-6h (24K bars)
    "BNB/USDT",    # ~11-13h (74K bars)
    "ETH/USDT",    # ~12-14h (76K bars)
    "BTC/USDT",    # ~12-14h (76K bars) — gate already done but rerun for consistency
]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_one(symbol: str, audit_dir: Path) -> int:
    sym_clean = symbol.replace("/", "").replace("USDT", "")
    presets_dir = audit_dir / "B2"
    output_dir = audit_dir / f"wf_B2_dyn_{sym_clean}"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = audit_dir / f"p4_seq_{sym_clean}_{ts}.log"
    err_path = audit_dir / f"p4_seq_{sym_clean}_{ts}.err.log"

    cmd = [
        sys.executable, "audit_wrapper_master.py",
        "--symbol", symbol,
        "--presets-dir", str(presets_dir),
        "--output-dir", str(output_dir),
        "--chunk-size", "1000000",
    ]
    print(f"\n[{utcnow()}] LAUNCH {symbol} -> {output_dir}")
    print(f"  cmd: {' '.join(cmd)}")

    t0 = time.time()
    with open(log_path, "wb") as out_f, open(err_path, "wb") as err_f:
        proc = subprocess.Popen(
            cmd, stdout=out_f, stderr=err_f,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    rc = proc.wait()
    elapsed = time.time() - t0
    print(f"[{utcnow()}] EXIT {symbol} rc={rc} elapsed={elapsed/3600:.2f}h")
    return rc


def main():
    p = argparse.ArgumentParser(description="P4 sequencer (vía master.py wrapper)")
    p.add_argument("--audit-dir", required=True)
    p.add_argument("--start-from", type=int, default=0)
    p.add_argument("--only", type=int, default=None)
    args = p.parse_args()

    audit_dir = Path(args.audit_dir)
    progress_path = audit_dir / "p4_progress.json"
    progress = []
    if progress_path.exists():
        try: progress = json.loads(progress_path.read_text())
        except Exception: pass

    indices = [args.only] if args.only is not None else list(range(args.start_from, len(SEQUENCE)))
    print(f"[{utcnow()}] P4 SEQUENCER START audit_dir={audit_dir} indices={indices}")
    for i in indices:
        sym = SEQUENCE[i]
        entry = {"index": i, "symbol": sym, "started_at": utcnow()}
        rc = run_one(sym, audit_dir)
        entry["finished_at"] = utcnow()
        entry["exit_code"] = rc
        progress.append(entry)
        progress_path.write_text(json.dumps(progress, indent=2))
        if rc != 0:
            print(f"[{utcnow()}] STOP rc={rc} on index {i} ({sym}) — Tier 3 escalation")
            return rc
    print(f"[{utcnow()}] P4 COMPLETE — all {len(indices)} runs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
