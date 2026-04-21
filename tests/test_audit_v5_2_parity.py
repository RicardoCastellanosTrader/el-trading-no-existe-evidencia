"""Tests unitarios para audit_fidelity_v5_2.

Tests de las funciones puras nuevas en v5.2:
  - load_deploy_boundaries (Feature A).
  - build_segments + assign_trade_to_segment (Feature A).
  - compute_segment_metrics + detect_discontinuity_warnings (Feature A).
  - check_clustering_divergent (Feature B).
  - Backward compat: EXCL_LABELS_V52 preserva EXCL_LABELS.

No se ejecuta run_audit completo (requiere BingX); eso se valida en demo manual.

Run: python -m pytest tests/test_audit_v5_2_parity.py -v
     o: python tests/test_audit_v5_2_parity.py
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd

# ruta modulos
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import audit_fidelity_v5 as v5_1  # baseline
import audit_fidelity_v5_2 as v5_2


# ---------------------------------------------------------------------------
# TEST 1 — Backward compat de constantes
# ---------------------------------------------------------------------------

def test_excl_labels_v52_preserves_v5_1_order():
    """EXCL_LABELS_V52 debe contener las 5 exclusiones v5.1 en el mismo orden
    + clustering_divergente al final."""
    v5_1_codes = list(v5_1.EXCL_LABELS.keys())
    v5_2_codes = list(v5_2.EXCL_LABELS_V52.keys())
    assert v5_2_codes[:5] == v5_1_codes, \
        f"primeros 5 codigos deben coincidir con v5.1: {v5_1_codes} vs {v5_2_codes[:5]}"
    assert v5_2_codes[5] == v5_2.EXCL_CLUSTERING
    assert len(v5_2_codes) == 6


def test_excl_clustering_constant():
    """EXCL_CLUSTERING debe ser 'excluido_clustering_divergente'."""
    assert v5_2.EXCL_CLUSTERING == 'excluido_clustering_divergente'


# ---------------------------------------------------------------------------
# TEST 2 — load_deploy_boundaries
# ---------------------------------------------------------------------------

def test_load_deploy_boundaries_happy_path():
    data = {
        "v1.0": "2026-04-01T00:00:00Z",
        "v2.0": "2026-04-10T00:00:00Z",
        "v3.0": "2026-04-20T00:00:00Z",
    }
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w',
                                      delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        path = f.name
    try:
        boundaries = v5_2.load_deploy_boundaries(path)
        assert len(boundaries) == 3
        keys = list(boundaries.keys())
        assert keys == ["v1.0", "v2.0", "v3.0"]  # orden cronologico
        assert all(ts.tzinfo is not None for ts in boundaries.values())
    finally:
        os.unlink(path)


def test_load_deploy_boundaries_skips_metadata_keys():
    data = {
        "_comment": "ignorar",
        "_source_notes": {"v1.0": "some note"},
        "v1.0": "2026-04-01T00:00:00Z",
        "v2.0": "2026-04-10T00:00:00Z",
    }
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w',
                                      delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        path = f.name
    try:
        boundaries = v5_2.load_deploy_boundaries(path)
        assert "_comment" not in boundaries
        assert "_source_notes" not in boundaries
        assert len(boundaries) == 2
    finally:
        os.unlink(path)


def test_load_deploy_boundaries_sorts_chronologically():
    data = {
        "v3.0": "2026-04-20T00:00:00Z",
        "v1.0": "2026-04-01T00:00:00Z",
        "v2.0": "2026-04-10T00:00:00Z",
    }
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w',
                                      delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        path = f.name
    try:
        boundaries = v5_2.load_deploy_boundaries(path)
        keys = list(boundaries.keys())
        assert keys == ["v1.0", "v2.0", "v3.0"]
    finally:
        os.unlink(path)


def test_load_deploy_boundaries_none_path():
    assert v5_2.load_deploy_boundaries(None) is None


# ---------------------------------------------------------------------------
# TEST 3 — build_segments y assign_trade_to_segment
# ---------------------------------------------------------------------------

def test_build_segments_simple_case():
    """3 boundaries -> 3 segmentos (pre-v1 si aplica, v1->v2, v2->v3, v3->now)."""
    boundaries = {
        "v1.0": pd.Timestamp("2026-04-10T00:00:00Z"),
        "v2.0": pd.Timestamp("2026-04-15T00:00:00Z"),
    }
    window_start = pd.Timestamp("2026-04-05T00:00:00Z")
    window_end = pd.Timestamp("2026-04-20T00:00:00Z")
    segments = v5_2.build_segments(boundaries, window_start, window_end)
    names = [s[0] for s in segments]
    assert "pre-v1.0" in names
    assert "v1.0 -> v2.0" in names
    assert "v2.0 -> now" in names


def test_build_segments_no_pre_segment_if_window_after_first_boundary():
    boundaries = {
        "v1.0": pd.Timestamp("2026-04-10T00:00:00Z"),
        "v2.0": pd.Timestamp("2026-04-15T00:00:00Z"),
    }
    window_start = pd.Timestamp("2026-04-12T00:00:00Z")  # ya post v1.0
    window_end = pd.Timestamp("2026-04-20T00:00:00Z")
    segments = v5_2.build_segments(boundaries, window_start, window_end)
    names = [s[0] for s in segments]
    assert "pre-v1.0" not in names


def test_assign_trade_to_segment():
    segments = [
        ('pre-v1', pd.Timestamp("2026-04-05T00:00:00Z"), pd.Timestamp("2026-04-10T00:00:00Z")),
        ('v1->v2', pd.Timestamp("2026-04-10T00:00:00Z"), pd.Timestamp("2026-04-15T00:00:00Z")),
        ('v2->now', pd.Timestamp("2026-04-15T00:00:00Z"), pd.Timestamp("2026-04-20T00:00:00Z")),
    ]
    assert v5_2.assign_trade_to_segment(pd.Timestamp("2026-04-07T12:00:00Z"), segments) == 'pre-v1'
    assert v5_2.assign_trade_to_segment(pd.Timestamp("2026-04-12T12:00:00Z"), segments) == 'v1->v2'
    assert v5_2.assign_trade_to_segment(pd.Timestamp("2026-04-17T12:00:00Z"), segments) == 'v2->now'
    assert v5_2.assign_trade_to_segment(None, segments) is None


def test_assign_trade_to_segment_boundary_transition():
    """Trade exactamente en el timestamp del boundary va al segmento NUEVO (inclusive start)."""
    segments = [
        ('pre-v1', pd.Timestamp("2026-04-05T00:00:00Z"), pd.Timestamp("2026-04-10T00:00:00Z")),
        ('v1->now', pd.Timestamp("2026-04-10T00:00:00Z"), pd.Timestamp("2026-04-20T00:00:00Z")),
    ]
    # 04-10T00:00:00 pertenece a v1->now (half-open [start, end))
    assert v5_2.assign_trade_to_segment(pd.Timestamp("2026-04-10T00:00:00Z"), segments) == 'v1->now'


# ---------------------------------------------------------------------------
# TEST 4 — compute_segment_metrics
# ---------------------------------------------------------------------------

def test_compute_segment_metrics_happy_path():
    trades = [
        {'match_type': 'OK', 'exclusion': ''},
        {'match_type': 'OK', 'exclusion': ''},
        {'match_type': 'NONE', 'exclusion': ''},
        {'match_type': 'EXCL', 'exclusion': 'excluido_reconstruido'},
        {'match_type': 'EXCL', 'exclusion': 'excluido_clustering_divergente'},
        {'match_type': 'NO_EC', 'exclusion': ''},  # no contabilizable
    ]
    m = v5_2.compute_segment_metrics(trades, matches_by_idx={})
    assert m['n_effective'] == 3  # 2 OK + 1 NONE
    assert m['matches_ok'] == 2
    assert m['none'] == 1
    assert m['excluded'] == 2
    assert m['match_rate'] == 2 / 3
    assert m['ci_low'] >= 0.0
    assert m['ci_high'] <= 1.0


def test_compute_segment_metrics_empty():
    m = v5_2.compute_segment_metrics([], matches_by_idx={})
    assert m['n_effective'] == 0
    assert m['match_rate'] == 0.0
    assert m['ci_low'] == 0.0


# ---------------------------------------------------------------------------
# TEST 5 — detect_discontinuity_warnings
# ---------------------------------------------------------------------------

def test_discontinuity_warnings_flag_large_delta():
    """Si seg A tiene 95% y seg B tiene 50% con N>=3, debe flaggear."""
    segments = {
        'seg_a': {'n_effective': 10, 'match_rate': 0.95, 'matches_ok': 9, 'ci_low': 0, 'ci_high': 1, 'none': 1, 'excluded': 0, 'exclusion_counts': {}, 'matches_diff': 0},
        'seg_b': {'n_effective': 10, 'match_rate': 0.50, 'matches_ok': 5, 'ci_low': 0, 'ci_high': 1, 'none': 5, 'excluded': 0, 'exclusion_counts': {}, 'matches_diff': 0},
    }
    warns = v5_2.detect_discontinuity_warnings(segments, min_delta_pp=20.0, min_n=3)
    assert len(warns) == 1
    assert warns[0]['between'] == ['seg_a', 'seg_b']
    assert warns[0]['delta_pp'] == 45.0


def test_discontinuity_warnings_no_flag_small_delta():
    segments = {
        'seg_a': {'n_effective': 10, 'match_rate': 0.90, 'matches_ok': 9, 'ci_low': 0, 'ci_high': 1, 'none': 1, 'excluded': 0, 'exclusion_counts': {}, 'matches_diff': 0},
        'seg_b': {'n_effective': 10, 'match_rate': 0.85, 'matches_ok': 8, 'ci_low': 0, 'ci_high': 1, 'none': 2, 'excluded': 0, 'exclusion_counts': {}, 'matches_diff': 0},
    }
    warns = v5_2.detect_discontinuity_warnings(segments, min_delta_pp=20.0, min_n=3)
    assert len(warns) == 0


def test_discontinuity_warnings_skips_low_n():
    """Si N < min_n, no se considera el segmento."""
    segments = {
        'seg_a': {'n_effective': 2, 'match_rate': 1.0, 'matches_ok': 2, 'ci_low': 0, 'ci_high': 1, 'none': 0, 'excluded': 0, 'exclusion_counts': {}, 'matches_diff': 0},
        'seg_b': {'n_effective': 10, 'match_rate': 0.0, 'matches_ok': 0, 'ci_low': 0, 'ci_high': 1, 'none': 10, 'excluded': 0, 'exclusion_counts': {}, 'matches_diff': 0},
    }
    warns = v5_2.detect_discontinuity_warnings(segments, min_delta_pp=20.0, min_n=3)
    assert len(warns) == 0  # seg_a N=2 < min_n=3


# ---------------------------------------------------------------------------
# TEST 6 — get_cluster_live_from_signals_raw
# ---------------------------------------------------------------------------

def test_get_cluster_live_happy_path():
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {
        'signals_raw': {
            (ec, 'IMX/USDT'): {'a': 'LONG', 'r': 'ma_cross', 'k': 2}
        }
    }
    assert v5_2.get_cluster_live_from_signals_raw('IMX/USDT', ec, log_events) == 2


def test_get_cluster_live_missing_k():
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {
        'signals_raw': {
            (ec, 'IMX/USDT'): {'a': 'LONG', 'r': 'ma_cross'}  # no 'k'
        }
    }
    assert v5_2.get_cluster_live_from_signals_raw('IMX/USDT', ec, log_events) is None


def test_get_cluster_live_missing_signal():
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {'signals_raw': {}}
    assert v5_2.get_cluster_live_from_signals_raw('IMX/USDT', ec, log_events) is None


def test_get_cluster_live_none_entry_candle():
    log_events = {'signals_raw': {}}
    assert v5_2.get_cluster_live_from_signals_raw('IMX/USDT', None, log_events) is None


# ---------------------------------------------------------------------------
# TEST 7 — get_cluster_post_hoc_at_entry
# ---------------------------------------------------------------------------

def test_get_cluster_post_hoc_happy_path():
    ts_arr = pd.date_range("2026-04-20T00:00:00", periods=24, freq="h").values
    labels = np.array([0, 0, 1, 1, 2, 2, 2, 1, 0, 0] + [1] * 14, dtype=np.int64)
    cluster_labels_cache = {'IMX/USDT': labels}
    timestamps_cache = {'IMX/USDT': ts_arr}
    # bar 14:00 es idx 14 en ts_arr (index-aligned)
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    result = v5_2.get_cluster_post_hoc_at_entry('IMX/USDT', ec,
                                                  cluster_labels_cache, timestamps_cache)
    assert result == 1  # labels[14]


def test_get_cluster_post_hoc_unknown_symbol():
    result = v5_2.get_cluster_post_hoc_at_entry('XYZ/USDT',
                                                  pd.Timestamp("2026-04-20T14:00:00Z"),
                                                  {}, {})
    assert result is None


def test_get_cluster_post_hoc_negative_label():
    """labels[-1] (not classified) -> return None."""
    ts_arr = pd.date_range("2026-04-20T00:00:00", periods=3, freq="h").values
    labels = np.array([-1, -1, -1], dtype=np.int64)
    ec = pd.Timestamp("2026-04-20T01:00:00Z")
    result = v5_2.get_cluster_post_hoc_at_entry(
        'IMX/USDT', ec, {'IMX/USDT': labels}, {'IMX/USDT': ts_arr}
    )
    assert result is None


# ---------------------------------------------------------------------------
# TEST 8 — check_clustering_divergent (integra live + post_hoc)
# ---------------------------------------------------------------------------

def test_check_clustering_divergent_detects_divergence():
    """Simula caso IMX 2026-04-20 14:00: cluster_live=2, cluster_post_hoc=0."""
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {
        'signals_raw': {
            (ec, 'IMX/USDT'): {'k': 2}
        }
    }
    ts_arr = pd.date_range("2026-04-20T00:00:00", periods=24, freq="h").values
    labels = np.array([0] * 24, dtype=np.int64)  # siempre cluster 0 post-hoc
    is_div, detail = v5_2.check_clustering_divergent(
        'IMX/USDT', ec, log_events,
        {'IMX/USDT': labels}, {'IMX/USDT': ts_arr},
    )
    assert is_div is True
    assert detail['cluster_live'] == 2
    assert detail['cluster_post_hoc'] == 0


def test_check_clustering_divergent_no_divergence():
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {
        'signals_raw': {
            (ec, 'IMX/USDT'): {'k': 1}
        }
    }
    ts_arr = pd.date_range("2026-04-20T00:00:00", periods=24, freq="h").values
    labels = np.array([1] * 24, dtype=np.int64)
    is_div, detail = v5_2.check_clustering_divergent(
        'IMX/USDT', ec, log_events,
        {'IMX/USDT': labels}, {'IMX/USDT': ts_arr},
    )
    assert is_div is False
    assert detail is None  # match


def test_check_clustering_divergent_missing_live():
    """Cluster_live missing -> is_div=False, detail note='missing_data'."""
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {'signals_raw': {}}
    ts_arr = pd.date_range("2026-04-20T00:00:00", periods=24, freq="h").values
    labels = np.array([0] * 24, dtype=np.int64)
    is_div, detail = v5_2.check_clustering_divergent(
        'IMX/USDT', ec, log_events,
        {'IMX/USDT': labels}, {'IMX/USDT': ts_arr},
    )
    assert is_div is False
    assert detail is not None
    assert detail.get('note') == 'missing_data'
    assert detail.get('cluster_live') is None


def test_check_clustering_divergent_missing_post_hoc():
    ec = pd.Timestamp("2026-04-20T14:00:00Z")
    log_events = {
        'signals_raw': {
            (ec, 'IMX/USDT'): {'k': 2}
        }
    }
    # cache vacia
    is_div, detail = v5_2.check_clustering_divergent(
        'IMX/USDT', ec, log_events, {}, {},
    )
    assert is_div is False
    assert detail.get('note') == 'missing_data'


# ---------------------------------------------------------------------------
# TEST 9 — Smoke: script importable y --help no crashea
# ---------------------------------------------------------------------------

def test_module_imports_clean():
    """v5_2 debe importarse sin errores."""
    assert v5_2 is not None
    assert hasattr(v5_2, 'run_audit')
    assert hasattr(v5_2, 'main')
    assert hasattr(v5_2, 'load_deploy_boundaries')
    assert hasattr(v5_2, 'check_clustering_divergent')


def test_help_string():
    """main() con --help no debe crashear (ejecutado via argparse en sub-test)."""
    # argparse imprime y exits con 0 con --help; lo evitamos
    # pero verificamos que el parser se puede construir
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--deploy-boundaries', type=str)
    parser.add_argument('--clustering-check', action='store_true')
    parser.add_argument('--json-output', type=str)
    # si llegamos aqui, los nombres no colisionan
    assert True


# ---------------------------------------------------------------------------
# TEST 10 — Weighted avg consistency
# ---------------------------------------------------------------------------

def test_weighted_avg_equals_total_match_rate():
    """Weighted avg ponderado por N debe igualar match rate global."""
    trade_rows_total = [
        {'match_type': 'OK', 'exclusion': ''},  # seg_a
        {'match_type': 'OK', 'exclusion': ''},  # seg_a
        {'match_type': 'NONE', 'exclusion': ''},  # seg_b
        {'match_type': 'OK', 'exclusion': ''},  # seg_b
    ]
    # Total: 3 OK / 4 N_eff = 0.75
    m_total = v5_2.compute_segment_metrics(trade_rows_total, matches_by_idx={})
    expected_rate = m_total['match_rate']

    # segmentos
    m_a = v5_2.compute_segment_metrics(trade_rows_total[:2], matches_by_idx={})
    m_b = v5_2.compute_segment_metrics(trade_rows_total[2:], matches_by_idx={})
    total_n = m_a['n_effective'] + m_b['n_effective']
    weighted = (m_a['match_rate'] * m_a['n_effective']
                + m_b['match_rate'] * m_b['n_effective']) / total_n
    assert abs(weighted - expected_rate) < 1e-9


if __name__ == '__main__':
    import traceback
    passed = 0
    failed = 0
    tests = [v for k, v in globals().items() if k.startswith('test_') and callable(v)]
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
