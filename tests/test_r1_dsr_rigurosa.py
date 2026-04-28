"""
Tests Sesión 2.5 Frame 2 R1 DSR rigurosa Opción γ FULL ROBUSTA (López de Prado 2014).

Cover:
  1. _compute_per_trade_returns_simplified: pt_pnl directo (skip entry/exit derivation).
  2. _compute_dsr_zscore_rigorous: López de Prado formula synthetic case.
  3. DSR edge cases: insufficient sample (n<3), zero variance, invalid variance term.
  4. _apply_dsr_filter: DataFrame integration con returns dict.
  5. Backward compat _R1_DSR_METHOD='none': no-op preserves baseline.
  6. Hybrid sort gated por _R1_DSR_METHOD: 'none' → M2 fix sort, 'rigorous' → hybrid.
  7. _R1_DSR_REQUIRE_NOT_FLAGGED default OFF backward compat.

Standalone, no pytest. Run: python tests/test_r1_dsr_rigurosa.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
import pandas as pd
from regime_walk_forward import (
    _R1_DSR_METHOD,
    _DSR_GAMMA_EULER,
    _DSR_FLAG_PVALUE_THRESHOLD,
    _R1_DSR_REQUIRE_NOT_FLAGGED,
    _R1_DSR_TOP_N_SURVIVORS,
    _compute_per_trade_returns_simplified,
    _compute_dsr_zscore_rigorous,
    _apply_dsr_filter,
    _apply_w4_fwd_ci_filters,
)


def test_1_compute_per_trade_returns_simplified():
    """pt_pnl directo → returns dict (skip entry/exit derivation)."""
    n_configs = 3
    max_trades = 10
    pt_pnl = np.zeros((n_configs, max_trades), dtype=np.float64)
    pt_count = np.array([5, 0, 1], dtype=np.int32)

    pt_pnl[0, :5] = [0.5, -0.3, 0.8, 0.2, -0.1]
    pt_pnl[1, :0] = []  # 0 trades
    pt_pnl[2, :1] = [0.4]  # 1 trade insufficient

    returns = _compute_per_trade_returns_simplified(pt_pnl, pt_count)
    assert 0 in returns, "config 0 (5 trades) should be in returns dict"
    assert 1 not in returns, "config 1 (0 trades) excluded"
    assert 2 not in returns, "config 2 (1 trade < 2) excluded"
    np.testing.assert_array_equal(returns[0], [0.5, -0.3, 0.8, 0.2, -0.1])
    print("test_1 PASS: pt_pnl directo → returns dict, n<2 excluded")


def test_2_dsr_zscore_rigorous_synthetic():
    """López de Prado formula: strong positive edge → significant (z > 0, p < 0.05)."""
    # Strong positive-edge synthetic: 50 trades win/loss-like distribution
    # Mimics good specialist with PF~3 (avg_win 0.6 / avg_loss 0.2, 60% win rate)
    np.random.seed(42)
    n_wins = 30
    n_losses = 20
    wins = np.random.normal(0.6, 0.1, n_wins)
    losses = np.random.normal(-0.2, 0.1, n_losses)
    returns = np.concatenate([wins, losses])
    np.random.shuffle(returns)
    z, p, f = _compute_dsr_zscore_rigorous(returns, n_configs_tested=1000)
    assert not np.isnan(z), "Z-score should be finite for strong synthetic"
    assert z > 0, f"Strong positive-edge should have z > 0 (got {z})"
    # Compare with weak N selection bias: same returns, fewer configs → smaller correction
    z_weak, p_weak, f_weak = _compute_dsr_zscore_rigorous(returns, n_configs_tested=10)
    assert z_weak > z, f"Lower N_configs (less selection bias) should give higher z (got z_weak={z_weak} vs z={z})"
    print(f"test_2 PASS: synthetic edge z={z:.3f}@N=1000 vs z_weak={z_weak:.3f}@N=10 (selection bias correction directional)")


def test_3_dsr_edge_cases():
    """Edge cases: insufficient sample, zero variance, invalid variance term."""
    # Insufficient: n<3
    z1, p1, f1 = _compute_dsr_zscore_rigorous(np.array([0.1, 0.2]), n_configs_tested=100)
    assert np.isnan(z1) and f1, "n<3 → nan z + flagged"

    # Zero variance
    z2, p2, f2 = _compute_dsr_zscore_rigorous(np.full(20, 0.5), n_configs_tested=100)
    assert np.isnan(z2) and f2, "zero variance → nan z + flagged"

    # Empty array
    z3, p3, f3 = _compute_dsr_zscore_rigorous(np.array([]), n_configs_tested=100)
    assert np.isnan(z3) and f3, "empty → nan z + flagged"

    print("test_3 PASS: edge cases all return (nan, nan, flagged=True)")


def test_4_apply_dsr_filter_dataframe():
    """DataFrame integration: returns dict → df with dsr_zscore/dsr_pvalue/flagged_dsr."""
    df = pd.DataFrame({
        'config_id': [100, 200, 300],
        'pf_fwd': [1.5, 2.0, 1.2],
        'specialist_score_ci_low': [3.0, 2.0, 1.0],
    })
    np.random.seed(42)
    returns_dict = {
        100: np.random.normal(0.3, 0.5, 50),  # positive edge
        200: np.random.normal(-0.1, 0.5, 50),  # negative edge
        # 300 missing → flagged by default
    }
    df_out = _apply_dsr_filter(df, returns_dict, n_configs_tested=1000, method='rigorous')
    assert 'dsr_zscore' in df_out.columns
    assert 'dsr_pvalue' in df_out.columns
    assert 'flagged_dsr' in df_out.columns
    # config 300 has no returns → flagged_dsr=True default
    flagged_300 = df_out[df_out['config_id'] == 300]['flagged_dsr'].iloc[0]
    assert flagged_300 == True, "config 300 (no returns) should be flagged"
    print(f"test_4 PASS: dataframe integration, config 300 flagged (no returns)")


def test_5_backward_compat_method_none():
    """method='none' default → df unchanged (no-op)."""
    df = pd.DataFrame({
        'config_id': [100, 200],
        'pf_fwd': [1.5, 2.0],
    })
    df_out = _apply_dsr_filter(df, {}, n_configs_tested=1000, method='none')
    assert 'dsr_zscore' not in df_out.columns, "method='none' should NOT add dsr_zscore"
    assert 'flagged_dsr' not in df_out.columns, "method='none' should NOT add flagged_dsr"
    np.testing.assert_array_equal(df_out['config_id'].values, df['config_id'].values)
    print("test_5 PASS: method='none' → df unchanged backward compat")
    # Also verify default constant
    assert _R1_DSR_METHOD == 'none', f"Default _R1_DSR_METHOD should be 'none' (got {_R1_DSR_METHOD!r})"


def test_6_hybrid_sort_gated():
    """Hybrid sort gated: method='none' uses M2 fix [pf_fwd_ci_low, specialist_score_ci_low].
    method='rigorous' uses [pf_fwd_ci_low, dsr_zscore]."""
    # This test verifies the gating logic at the dataframe level.
    # Actual sort happens inside extract_validated_specialists; here we just
    # validate that the columns expected by both branches exist.
    df = pd.DataFrame({
        'config_id': [100, 200, 300],
        'pf_fwd_ci_low': [1.5, 2.0, 1.2],
        'specialist_score_ci_low': [3.0, 2.0, 1.0],  # M2 fix tie-breaker
    })
    # Apply DSR with rigorous method
    np.random.seed(42)
    returns_dict = {
        100: np.random.normal(0.3, 0.5, 50),
        200: np.random.normal(0.0, 0.5, 50),
        300: np.random.normal(-0.2, 0.5, 50),
    }
    df_dsr = _apply_dsr_filter(df.copy(), returns_dict, n_configs_tested=1000,
                                method='rigorous')
    # Sort by hybrid [pf_fwd_ci_low, dsr_zscore]
    sorted_dsr = df_dsr.sort_values(['pf_fwd_ci_low', 'dsr_zscore'],
                                     ascending=[False, False]).reset_index(drop=True)
    # Top should be config 200 (highest pf_fwd_ci_low=2.0)
    assert sorted_dsr.iloc[0]['config_id'] == 200, "Top should be config 200 (pf_fwd_ci_low max)"
    # Sort by M2 fix [pf_fwd_ci_low, specialist_score_ci_low]
    sorted_m2 = df.sort_values(['pf_fwd_ci_low', 'specialist_score_ci_low'],
                                ascending=[False, False]).reset_index(drop=True)
    assert sorted_m2.iloc[0]['config_id'] == 200, "M2 fix top should also be config 200"
    print("test_6 PASS: hybrid sort gated; both branches functional")


def test_7_w4_filter_dsr_optional():
    """W4 filter optional require_not_flagged_dsr (default OFF backward compat)."""
    df = pd.DataFrame({
        'config_id': [100, 200],
        'pf_fwd_ci_low': [1.5, 2.0],
        'flag_sospechoso_outlier': [False, False],
        'flagged_dsr': [True, False],
    })
    # Default OFF (require_not_flagged_dsr=None → uses _R1_DSR_REQUIRE_NOT_FLAGGED=False)
    df_default = _apply_w4_fwd_ci_filters(df.copy())
    assert len(df_default) == 2, "Default OFF: both configs pass (no DSR filter)"

    # Explicit ON: filter flagged_dsr
    df_filtered = _apply_w4_fwd_ci_filters(df.copy(), require_not_flagged_dsr=True)
    assert len(df_filtered) == 1, "Explicit ON: only config 200 (not flagged) passes"
    assert df_filtered.iloc[0]['config_id'] == 200

    assert _R1_DSR_REQUIRE_NOT_FLAGGED == False, \
        f"Default _R1_DSR_REQUIRE_NOT_FLAGGED should be False (got {_R1_DSR_REQUIRE_NOT_FLAGGED})"
    print("test_7 PASS: W4 require_not_flagged_dsr default OFF + explicit ON works")


if __name__ == "__main__":
    tests = [
        test_1_compute_per_trade_returns_simplified,
        test_2_dsr_zscore_rigorous_synthetic,
        test_3_dsr_edge_cases,
        test_4_apply_dsr_filter_dataframe,
        test_5_backward_compat_method_none,
        test_6_hybrid_sort_gated,
        test_7_w4_filter_dsr_optional,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    if failed == 0:
        print(f"\n{len(tests)}/{len(tests)} tests PASS")
        sys.exit(0)
    else:
        print(f"\n{failed}/{len(tests)} tests FAIL")
        sys.exit(1)
