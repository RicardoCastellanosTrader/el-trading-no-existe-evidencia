"""Wrapper master.py for audit walk-forward re-generation.

Caveat #22 §13.2 cumulative: comparison/audit methodológicas DEBEN invocarse
vía master.py (NO replicar CONFIG a mano). This wrapper:

1. Imports master + override CONFIG paths to audit dir (separate from productive)
2. Invokes step_regime_wf() which applies ALL CONFIG productive overrides
   automatically (toxic_tail dynamic, _FWD_MIN_TRADES=15, _FWD_MIN_PF=1.0, etc.)
3. Output specialist_configs.json appears in audit dir, productive regime_wf/
   intacto

Usage:
    python audit_wrapper_master.py --symbol BTC/USDT --presets-dir output/production --output-dir audit_etapa2_*/wf_bitex_gate/

Mock cli_args for chunk_size=1M (R1 v18 productive).
"""
from __future__ import annotations

import argparse
import sys
import shutil
from pathlib import Path


class MockCliArgs:
    """Mock argparse Namespace for master.step_regime_wf cli_args param."""
    def __init__(self, chunk_size=1_000_000, recycle=True):
        self.chunk_size = chunk_size
        self.recycle = recycle
        self.presets_per_subprocess = 0
        self.internal_subprocess_mode = False
        self.preset_idx_start = 0
        self.preset_idx_end = None


def run_wrapper(symbol: str, presets_dir: str, output_dir: str,
                 chunk_size: int = 1_000_000) -> int:
    """Re-run walk-forward step for one symbol with productive CONFIG complete.

    Args:
        symbol: e.g. "BTC/USDT"
        presets_dir: directory with presets_<SYM>USDT.csv
        output_dir: where to write specialist_configs.json (separate from productive)
        chunk_size: R1 v18 chunk size (default 1M productive)

    Returns: 0 on success, 1 on failure.
    """
    import master

    # CRITICAL: override paths to audit dir BEFORE step_regime_wf to keep
    # productive regime_wf/ intact. master.py reads/writes via CONFIG dict.
    print(f"[wrapper] Pre-override CONFIG['regime_wf_dir']: {master.CONFIG['regime_wf_dir']}")
    print(f"[wrapper] Pre-override CONFIG['output_dir']:   {master.CONFIG['output_dir']}")
    master.CONFIG['regime_wf_dir'] = output_dir
    master.CONFIG['output_dir'] = presets_dir
    print(f"[wrapper] Post-override CONFIG['regime_wf_dir']: {master.CONFIG['regime_wf_dir']}")
    print(f"[wrapper] Post-override CONFIG['output_dir']:   {master.CONFIG['output_dir']}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cli_args = MockCliArgs(chunk_size=chunk_size, recycle=True)

    print(f"[wrapper] Invoking master.step_regime_wf([{symbol!r}], recycle=True, cli_args=...)")
    try:
        failed = master.step_regime_wf([symbol], recycle=True, cli_args=cli_args)
        # step_regime_wf returns either a list of failed symbols OR (failed, results_summary) tuple
        if isinstance(failed, tuple):
            failed_list = failed[0]
        else:
            failed_list = failed
        if failed_list:
            print(f"[wrapper] FAILED symbols: {failed_list}", file=sys.stderr)
            return 1
        print(f"[wrapper] DONE — output at {output_dir}")
        return 0
    except Exception as e:
        print(f"[wrapper] EXCEPTION: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    p = argparse.ArgumentParser(description="Wrapper for productive master.py step_regime_wf")
    p.add_argument("--symbol", required=True, help="e.g. BTC/USDT")
    p.add_argument("--presets-dir", required=True, help="dir with presets_*USDT.csv")
    p.add_argument("--output-dir", required=True, help="output dir (NOT productive regime_wf/)")
    p.add_argument("--chunk-size", type=int, default=1_000_000)
    args = p.parse_args()
    sys.exit(run_wrapper(args.symbol, args.presets_dir, args.output_dir, args.chunk_size))


if __name__ == "__main__":
    main()
