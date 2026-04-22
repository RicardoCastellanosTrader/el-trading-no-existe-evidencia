"""
Tests W4 thresholds (feature-w3-bootstrap-pf-fwd; W4 layered on W3).

Cover:
  1. _FWD_MIN_TRADES=25 constant value.
  2. _FWD_MIN_PF=1.1 constant value.
  3. _FWD_REQUIRE_NOT_SOSPECHOSO default True.
  4. NOT sospechoso filter blocks flagged config.
  5. NOT sospechoso lets through non-flagged config.
  6. Optional ci_low hook blocks config with ci_low below threshold.
  7. Optional ci_width hook blocks config with wide CI.
  8. Retroactive check on real data: ONDO C0 cfg 2457036 blocked by W4.

Standalone, no pytest. Run: python tests/test_w4_thresholds.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
import pandas as pd
from regime_walk_forward import (
    _apply_bootstrap_pf_fwd,
    _apply_w4_fwd_ci_filters,
    _FWD_MIN_TRADES,
    _FWD_MIN_PF,
    _FWD_REQUIRE_NOT_SOSPECHOSO,
    _FWD_MIN_CI_LOW,
    _FWD_MAX_CI_WIDTH,
)


def test_1_min_trades_constant():
    """_FWD_MIN_TRADES upgraded to 25 per W4."""
    assert _FWD_MIN_TRADES == 25, f"expected 25, got {_FWD_MIN_TRADES}"
    print(f"  test_1 PASS: _FWD_MIN_TRADES={_FWD_MIN_TRADES}")


def test_2_min_pf_constant():
    """_FWD_MIN_PF upgraded to 1.1 per W4."""
    assert _FWD_MIN_PF == 1.1, f"expected 1.1, got {_FWD_MIN_PF}"
    print(f"  test_2 PASS: _FWD_MIN_PF={_FWD_MIN_PF}")


def test_3_require_not_sospechoso_default():
    """_FWD_REQUIRE_NOT_SOSPECHOSO default True per W4 (dominant filter)."""
    assert _FWD_REQUIRE_NOT_SOSPECHOSO is True
    # Hooks default off (redundant with NOT sospechoso)
    assert _FWD_MIN_CI_LOW == 0.0
    assert _FWD_MAX_CI_WIDTH == float('inf')
    print(f"  test_3 PASS: NOT_SOSPECHOSO=True, ci_low hook={_FWD_MIN_CI_LOW},"
          f" ci_width hook={_FWD_MAX_CI_WIDTH}")


def _mk_df(rows):
    """Build a DataFrame with W3 columns populated synthetically."""
    return pd.DataFrame(rows)


def test_4_not_sospechoso_blocks_flagged():
    """Config flagged by W3 is filtered out by NOT_SOSPECHOSO guard."""
    df = _mk_df([
        {'config_id': 1, 'pf_fwd_ci_low': 2.5, 'ci_width': 36.0,
         'flag_sospechoso_outlier': True},
    ])
    out = _apply_w4_fwd_ci_filters(df)
    assert len(out) == 0, f"flagged config should be filtered, got {len(out)}"
    print(f"  test_4 PASS: flagged config blocked")


def test_5_not_sospechoso_passes_clean():
    """Config NOT flagged passes the guard."""
    df = _mk_df([
        {'config_id': 2, 'pf_fwd_ci_low': 1.5, 'ci_width': 2.0,
         'flag_sospechoso_outlier': False},
    ])
    out = _apply_w4_fwd_ci_filters(df)
    assert len(out) == 1, f"clean config should pass, got {len(out)}"
    assert int(out.iloc[0]['config_id']) == 2
    print(f"  test_5 PASS: clean config passes")


def test_6_ci_low_hook_blocks():
    """Optional min_ci_low hook blocks config below threshold even if not flagged."""
    df = _mk_df([
        {'config_id': 3, 'pf_fwd_ci_low': 1.1, 'ci_width': 2.0,
         'flag_sospechoso_outlier': False},
        {'config_id': 4, 'pf_fwd_ci_low': 2.0, 'ci_width': 2.0,
         'flag_sospechoso_outlier': False},
    ])
    # Hook ON: min_ci_low=1.5 filters config 3 (ci_low=1.1 < 1.5)
    out = _apply_w4_fwd_ci_filters(df, min_ci_low=1.5)
    ids = sorted(out['config_id'].tolist())
    assert ids == [4], f"expected only cfg 4 (ci_low>=1.5), got {ids}"
    # Default hook OFF: both pass
    out_default = _apply_w4_fwd_ci_filters(df)
    assert len(out_default) == 2, "with hook OFF both configs pass"
    print(f"  test_6 PASS: ci_low hook ON blocks 1.1, OFF lets through")


def test_7_ci_width_hook_blocks():
    """Optional max_ci_width hook blocks config above threshold."""
    df = _mk_df([
        {'config_id': 5, 'pf_fwd_ci_low': 1.5, 'ci_width': 4.5,
         'flag_sospechoso_outlier': False},
        {'config_id': 6, 'pf_fwd_ci_low': 1.5, 'ci_width': 2.0,
         'flag_sospechoso_outlier': False},
    ])
    # Hook ON: max_ci_width=3.0 filters config 5 (ci_width=4.5 > 3.0)
    out = _apply_w4_fwd_ci_filters(df, max_ci_width=3.0)
    ids = sorted(out['config_id'].tolist())
    assert ids == [6], f"expected only cfg 6 (ci_width<=3.0), got {ids}"
    print(f"  test_7 PASS: ci_width hook ON blocks wide-CI config")


def test_8_real_data_ondo_c0_blocked():
    """
    Retroactive: ONDO C0 cfg 2457036 (production top-1, §13.4 Fase II.B
    real PF 1.08 vs expected 5.5) must be blocked by W4 default filters.
    """
    csv_path = os.path.join(_root, 'regime_wf', 'ONDOUSDT_cluster_0_specialists.csv')
    if not os.path.exists(csv_path):
        print(f"  test_8 SKIP (CSV not found)")
        return
    df = pd.read_csv(csv_path)
    _apply_bootstrap_pf_fwd(df)
    # Pre-filter base: trades>=25 & pf_fwd>=1.1 (as _FWD_MIN_*)
    base_mask = (df['trades_fwd'] >= _FWD_MIN_TRADES) & (df['pf_fwd'] >= _FWD_MIN_PF)
    df_base = df.loc[base_mask]
    # ONDO C0 cfg 2457036 has trades_fwd=17 < 25 → already blocked at base
    cfg_row = df_base[df_base['config_id'] == 2457036]
    assert len(cfg_row) == 0, \
        f"ONDO cfg 2457036 should be blocked by _FWD_MIN_TRADES=25 (N=17<25), got {len(cfg_row)}"
    # And if by any chance it passed base, it would be flagged by NOT sospechoso
    full_row = df[df['config_id'] == 2457036]
    assert bool(full_row.iloc[0]['flag_sospechoso_outlier']) is True, \
        "ONDO cfg 2457036 must be flagged (ci_width~36)"
    print(f"  test_8 PASS: ONDO C0 cfg 2457036 blocked by W4 (base N<25 + flag_sospechoso)")


def _run_all():
    print("=" * 68)
    print("W4 thresholds test suite (layered on W3 commit 4e54c8d)")
    print("=" * 68)
    tests = [
        test_1_min_trades_constant,
        test_2_min_pf_constant,
        test_3_require_not_sospechoso_default,
        test_4_not_sospechoso_blocks_flagged,
        test_5_not_sospechoso_passes_clean,
        test_6_ci_low_hook_blocks,
        test_7_ci_width_hook_blocks,
        test_8_real_data_ondo_c0_blocked,
    ]
    n_pass = 0
    n_fail = 0
    for t in tests:
        try:
            t()
            n_pass += 1
        except AssertionError as e:
            print(f"  {t.__name__} FAIL: {e}")
            n_fail += 1
        except Exception as e:
            print(f"  {t.__name__} ERROR: {type(e).__name__}: {e}")
            n_fail += 1
    print("=" * 68)
    print(f"Result: {n_pass}/{len(tests)} PASS, {n_fail} FAIL")
    print("=" * 68)
    return n_fail == 0


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)
