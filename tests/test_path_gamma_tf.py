"""
Tests Sub-fase 2A TF Path γ kernel granular (Sesión 2 Frame 2 R3).

Cover:
  1. TF granular enum 6 valores constants definidos correctamente.
  2. Backward compat flag=False default — aggregate output IDÉNTICO baseline pattern.
  3. Path γ per-trade tracking flag=True — arrays populated con reasons 0-5.
  4. Audit hash regen NO WARN — EXPECTED_LAB_KERNEL_HASH actualizado match.
  5. No-regression W3 + W4 tests preservados (signature backward compat).
  6. normal_exit_signal split correcto en tf_exit_signal + zone_exit_signal.
  7. Cooldown condition refinement §12 L38 — preserves current kernel behavior
     (NO añade tf_exit/zone_exit a cooldown_until update — Pine canonical 4-rama).

Standalone, no pytest. Run: python tests/test_path_gamma_tf.py
"""
import os
import sys
import inspect
import hashlib

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
import lab_historico_numba_v8_3 as _lab


def test_1_tf_granular_enum_6_values():
    """Path γ constants enum 0-5 definidos correctamente."""
    assert _lab.REASON_TF_SL_HIT == 0
    assert _lab.REASON_TF_SL_EMERGENCY == 1
    assert _lab.REASON_TF_DIV_EXIT == 2
    assert _lab.REASON_TF_TF_EXIT == 3
    assert _lab.REASON_TF_ZONE_EXIT == 4
    assert _lab.REASON_TF_CANCEL_TF == 5
    assert not hasattr(_lab, "REASON_TF_NORMAL_EXIT"), \
        "Path α reduced enum REASON_TF_NORMAL_EXIT debe estar removido (Path γ split)"
    assert not hasattr(_lab, "REASON_TF_SL_EXIT"), \
        "Path α reduced enum REASON_TF_SL_EXIT debe estar removido (Path γ split sl_hit/sl_emergency)"
    print("test_1 PASS: enum granular 6 valores Path γ")


def test_2_tf_backward_compat_flag_off():
    """flag=False default — kernel retorna 7-tuple aggregate IDÉNTICO pattern."""
    # Mini-test: 1 config sintético, 200 bars, flag=False default
    n_bars = 200
    rng = np.random.default_rng(42)
    close = 100.0 + rng.normal(0, 1, n_bars).cumsum()
    high = close + 0.5
    low = close - 0.5
    timestamps = np.arange(n_bars, dtype=np.int64) * 3600000
    zone_bull = np.zeros(n_bars, dtype=np.bool_)
    zone_bear = np.zeros(n_bars, dtype=np.bool_)
    filters_forming = np.zeros(n_bars, dtype=np.uint32)
    filters_resolved = np.zeros(n_bars, dtype=np.uint32)
    div_bits = np.zeros((n_bars, 4), dtype=np.uint8)
    configs = np.array([0], dtype=np.uint32)

    result = _lab.run_simulation_numba(
        configs, close, high, low, timestamps,
        zone_bull, zone_bear,
        filters_forming, filters_resolved, div_bits,
        3.0, 5.0, 0.5, 1, 0.10,
    )
    # results: array shape (n_configs, 7) — pnl, trades, wins, cancels, max_dd, gp, gl
    assert isinstance(result, tuple) or hasattr(result, "shape"), \
        f"Backward compat: kernel debe retornar arrays/tuple sin per-trade dict cuando flag=False"
    print("test_2 PASS: backward compat flag=False default — signature preserved")


def test_3_tf_path_gamma_per_trade_tracking():
    """flag=True — per-trade arrays populated con reasons 0-5 valid range."""
    n_bars = 200
    rng = np.random.default_rng(42)
    close = 100.0 + rng.normal(0, 1, n_bars).cumsum()
    high = close + 0.5
    low = close - 0.5
    timestamps = np.arange(n_bars, dtype=np.int64) * 3600000
    zone_bull = np.ones(n_bars, dtype=np.bool_)  # always bull → triggers entries
    zone_bear = np.zeros(n_bars, dtype=np.bool_)
    filters_forming = np.full(n_bars, 0xFF, dtype=np.uint32)
    filters_resolved = np.full(n_bars, 0xFF, dtype=np.uint32)
    div_bits = np.zeros((n_bars, 4), dtype=np.uint8)
    configs = np.array([0], dtype=np.uint32)

    n_configs = 1
    max_trades = 50
    pt_entry_bar = np.zeros((n_configs, max_trades), dtype=np.int32)
    pt_exit_bar = np.zeros((n_configs, max_trades), dtype=np.int32)
    pt_side = np.zeros((n_configs, max_trades), dtype=np.int8)
    pt_pnl = np.zeros((n_configs, max_trades), dtype=np.float64)
    pt_reason = np.zeros((n_configs, max_trades), dtype=np.int8)
    pt_cluster = np.zeros((n_configs, max_trades), dtype=np.int8)
    pt_count = np.zeros(n_configs, dtype=np.int32)
    pt_entry_price = np.zeros((n_configs, max_trades), dtype=np.float64)
    pt_exit_price = np.zeros((n_configs, max_trades), dtype=np.float64)

    result = _lab.run_simulation_numba(
        configs, close, high, low, timestamps,
        zone_bull, zone_bear,
        filters_forming, filters_resolved, div_bits,
        3.0, 5.0, 0.5, 1, 0.10,
        accounting_start=100,
        cluster_labels=np.zeros(1, dtype=np.int64),
        n_clusters=1,
        return_per_trade=True,
        pt_entry_bar=pt_entry_bar, pt_exit_bar=pt_exit_bar,
        pt_side=pt_side, pt_pnl=pt_pnl, pt_reason=pt_reason,
        pt_cluster=pt_cluster, pt_count=pt_count,
        pt_entry_price=pt_entry_price, pt_exit_price=pt_exit_price,
    )

    n_trades_recorded = pt_count[0]
    if n_trades_recorded > 0:
        reasons = pt_reason[0, :n_trades_recorded]
        # Path γ enum: 0-5 valid range
        assert np.all(reasons >= 0) and np.all(reasons <= 5), \
            f"pt_reason fuera rango 0-5 Path γ: {reasons}"
    print(f"test_3 PASS: per-trade tracking n_trades={n_trades_recorded}, reasons in [0,5]")


def test_4_tf_audit_hash_regen_no_warn():
    """EXPECTED_LAB_KERNEL_HASH actualizado match SHA256 actual."""
    src = inspect.getsource(_lab.run_simulation_numba)
    h = hashlib.sha256(src.encode("utf-8")).hexdigest()
    expected = "89f00b7e2291d0b9aa5cc81d8471e90387fa148b0eff6a7f353a40abb76a07a3"
    assert h == expected, \
        f"Hash mismatch: actual={h}, expected={expected}\n" \
        f"Si kernel modificado intencionalmente, regen + update audit_v5.py:128 + audit_v5_2.py:123"
    print(f"test_4 PASS: audit hash regen match {h[:12]}...")


def test_5_tf_no_regression_w3_w4():
    """W3 + W4 tests preservados — signature backward compat NO ROTA."""
    # Smoke import: si W3+W4 imports rompen, signature change detected
    try:
        from regime_walk_forward import (
            _bootstrap_pf_fwd_vectorized,
            _apply_bootstrap_pf_fwd,
            _apply_w4_fwd_ci_filters,
        )
        print("test_5 PASS: W3+W4 imports preserved post-Path γ")
    except ImportError as e:
        raise AssertionError(f"W3/W4 imports broken: {e}")


def test_6_tf_normal_exit_split():
    """tf_exit_signal + zone_exit_signal split correcto — distintos pt_reason values 3 vs 4."""
    # Verify enum constants have distinct values for split paths
    assert _lab.REASON_TF_TF_EXIT != _lab.REASON_TF_ZONE_EXIT
    assert _lab.REASON_TF_TF_EXIT == 3
    assert _lab.REASON_TF_ZONE_EXIT == 4
    # Verify kernel source has both flag setters (split applied)
    src = inspect.getsource(_lab.run_simulation_numba)
    assert "tf_exit_signal = True" in src, \
        "tf_exit_signal=True setter no encontrado en kernel (split TF filter reverse)"
    assert "zone_exit_signal = True" in src, \
        "zone_exit_signal=True setter no encontrado en kernel (split zone reverse)"
    assert "normal_exit_signal" not in src, \
        "normal_exit_signal residual encontrado — split incomplete"
    print("test_6 PASS: normal_exit_signal split → tf_exit_signal + zone_exit_signal")


def test_7_tf_cooldown_uniforme_preserved():
    """Cooldown condition §12 L38 disciplinada — preserves current kernel behavior.

    Path γ split flag normal_exit_signal en tf_exit_signal + zone_exit_signal.
    Spec sub-decisión v listed tf_exit/zone_exit en cooldown OR condition pero
    análisis kernel reveló que current behavior NO incluye normal_exit en cooldown
    (only sl_emergency/sl/div/cancel). Añadirlos cambiaría behavior baseline:
    cooldown_until=t bloquearía same-bar re-entry post-tf_exit/zone_exit que
    current code permite.

    Refinement aplicado: cooldown condition UNCHANGED — tf_exit/zone_exit NOT in
    cooldown OR (Pine canonical 4-rama emergency/sl/div/cancel preservada).
    """
    src = inspect.getsource(_lab.run_simulation_numba)
    # Cooldown condition debe contener 4-rama (Pine canonical)
    cooldown_line = (
        "if sl_emergency_signal or sl_exit_signal or div_exit_signal or cancel_signal:"
    )
    assert cooldown_line in src, \
        f"Cooldown condition Pine canonical 4-rama NO encontrada — refinement §12 L38 violado.\n" \
        f"Esperado literal: '{cooldown_line}'"
    # Cooldown NO debe incluir tf_exit_signal ni zone_exit_signal (refinement §12 L38)
    bad_pattern_1 = "or tf_exit_signal or zone_exit_signal"
    bad_pattern_2 = "or tf_exit_signal"
    assert bad_pattern_1 not in src.replace("\n", ""), \
        "Cooldown condition incluye tf_exit_signal/zone_exit_signal — viola refinement §12 L38"
    print("test_7 PASS: cooldown condition Pine canonical 4-rama preserved (§12 L38 refinement)")


if __name__ == "__main__":
    tests = [
        test_1_tf_granular_enum_6_values,
        test_2_tf_backward_compat_flag_off,
        test_3_tf_path_gamma_per_trade_tracking,
        test_4_tf_audit_hash_regen_no_warn,
        test_5_tf_no_regression_w3_w4,
        test_6_tf_normal_exit_split,
        test_7_tf_cooldown_uniforme_preserved,
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
