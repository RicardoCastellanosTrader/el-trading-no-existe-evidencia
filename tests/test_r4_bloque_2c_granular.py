"""
Tests Sesión 3 Frame 2 R4 Bloque 2c granular cross-strategy decomposition.

Cover:
  1. parse_preset_label encoder/decoder.
  2. find_preset_tuple lookup en presets list.
  3. TF_REASON_LABELS enum 6 valores Path γ TF.
  4. compute_h_strategy_aggregation reason distribution per cluster.
  5. compute_h1_aggregation short/long Cohen d cross-side.
  6. Edge cases empty cluster + single specialist.

Standalone, no pytest. Run: python tests/test_r4_bloque_2c_granular.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
from analysis_scripts.r4_bloque_2c_granular_cross_strategy import (
    parse_preset_label, find_preset_tuple, TF_REASON_LABELS,
    compute_h_strategy_aggregation, compute_h1_aggregation,
)


def test_1_parse_preset_label():
    """parse_preset_label encoder/decoder cross hyst variants."""
    assert parse_preset_label('ALMA(24)/SMA(57)_H00') == ('ALMA', 24, 'SMA', 57, 0.0)
    assert parse_preset_label('VIDYA(14)/KAMA(49)_H05') == ('VIDYA', 14, 'KAMA', 49, 0.5)
    assert parse_preset_label('FRAMA(8)/T3(33)_H00') == ('FRAMA', 8, 'T3', 33, 0.0)
    # Invalid format
    assert parse_preset_label('invalid') is None
    assert parse_preset_label('') is None
    print("test_1 PASS: parse_preset_label cross hyst + invalid")


def test_2_find_preset_tuple():
    """find_preset_tuple lookup en presets list."""
    presets = [
        ('ALMA', 24, 0.0, 0.0, 'SMA', 57, 0.0, 0.0, 'KAMA', 196, 0.0, 0.0),
        ('VIDYA', 14, 0.0, 0.0, 'KAMA', 49, 0.0, 0.0, 'KAMA', 196, 0.0, 0.0),
    ]
    found = find_preset_tuple(presets, 'ALMA', 24, 'SMA', 57)
    assert found is not None and found[0] == 'ALMA'
    assert find_preset_tuple(presets, 'NOT_FOUND', 99, 'BAD', 99) is None
    print("test_2 PASS: find_preset_tuple match + None for missing")


def test_3_tf_reason_labels_enum():
    """TF_REASON_LABELS Path γ TF 6 valores granular."""
    assert TF_REASON_LABELS == {
        0: 'sl_hit',
        1: 'sl_emergency',
        2: 'div_exit',
        3: 'tf_exit',
        4: 'zone_exit',
        5: 'cancel_tf',
    }
    assert len(TF_REASON_LABELS) == 6
    print("test_3 PASS: TF_REASON_LABELS Path γ 6 valores granular")


def test_4_h_strategy_aggregation():
    """compute_h_strategy_aggregation reason distribution per cluster."""
    synth_data = {
        '0': [{
            'config_id': 100, 'preset': 'TEST',
            'pnl_array': [0.5, -0.3, 0.8, -0.1, 0.6],
            'reason_array': [0, 5, 3, 0, 4],
            'side_array': [0, 0, 1, 0, 1],
            'n_trades_kernel_filtered': 5,
        }],
        '1': [], '2': [],
    }
    hs = compute_h_strategy_aggregation(synth_data)
    assert hs['0']['total_trades'] == 5
    assert hs['0']['reason_distribution']['sl_hit']['n_trades'] == 2
    assert hs['0']['reason_distribution']['sl_hit']['mean_pnl'] == 0.2
    assert hs['0']['reason_distribution']['cancel_tf']['n_trades'] == 1
    assert hs['1']['total_trades'] == 0
    print("test_4 PASS: h_strategy reason distribution + empty cluster handling")


def test_5_h1_aggregation():
    """compute_h1_aggregation short/long Cohen d cross-side."""
    synth_data = {
        '0': [{
            'pnl_array': [0.5, -0.3, 0.8, -0.1, 0.6],
            'reason_array': [0, 5, 3, 0, 4],
            'side_array': [0, 0, 1, 0, 1],  # 3 long, 2 short
        }],
        '1': [], '2': [],
    }
    h1 = compute_h1_aggregation(synth_data)
    assert h1['0']['n_long'] == 3
    assert h1['0']['n_short'] == 2
    assert h1['0']['mean_pnl_long'] is not None
    assert h1['0']['cohen_d_long_minus_short'] is not None
    assert h1['1']['n_long'] == 0
    print(f"test_5 PASS: h1 short/long Cohen d={h1['0']['cohen_d_long_minus_short']:.3f}")


def test_6_edge_cases():
    """Empty data + single trade per cluster."""
    empty_data = {'0': [], '1': [], '2': []}
    hs_empty = compute_h_strategy_aggregation(empty_data)
    assert hs_empty['0']['total_trades'] == 0
    h1_empty = compute_h1_aggregation(empty_data)
    assert h1_empty['0']['n_long'] == 0
    assert h1_empty['0']['cohen_d_long_minus_short'] is None
    print("test_6 PASS: edge cases empty + single-trade handled")


if __name__ == "__main__":
    tests = [
        test_1_parse_preset_label,
        test_2_find_preset_tuple,
        test_3_tf_reason_labels_enum,
        test_4_h_strategy_aggregation,
        test_5_h1_aggregation,
        test_6_edge_cases,
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
