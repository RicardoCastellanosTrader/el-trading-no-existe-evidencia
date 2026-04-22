"""
Tests A15 (W2) — CUDA/CPU engine tag en parquets walk-forward.

Pre-fix: bifurcación CUDA vs CPU en runtime sin tag persistido →
resume con engine distinto producía specialists heterogéneos
silenciosamente (§13.3 W2).

Post-fix 2026-04-23: parquet carga 4 columnas nuevas (engine_name,
engine_version, machine_id, timestamp_run). Resume check WARN si
mismatch. Legacy parquets tolerados con WARN.

Standalone. Run: python tests/test_a15_engine_tag.py
"""
import os
import sys
import tempfile

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import pandas as pd
import numpy as np

import regime_walk_forward as wf


def test_1_get_engine_tag_fields():
    """_get_engine_tag() returns 4 required fields with valid content."""
    tag = wf._get_engine_tag()
    assert set(tag.keys()) == {'engine_name', 'engine_version', 'machine_id', 'timestamp_run'}
    assert tag['engine_name'] in ('cuda', 'cpu_numba'), f"unexpected engine_name: {tag['engine_name']}"
    assert tag['engine_version'].startswith('numba='), f"engine_version malformed: {tag['engine_version']}"
    assert isinstance(tag['machine_id'], str) and tag['machine_id'], "machine_id empty"
    # timestamp_run should be ISO 8601 ending with Z
    assert tag['timestamp_run'].endswith('Z'), f"timestamp_run not ISO: {tag['timestamp_run']}"
    # And parseable
    import datetime as _dt
    _dt.datetime.fromisoformat(tag['timestamp_run'].rstrip('Z'))
    print(f"  test_1 PASS: tag={tag}")


def test_2_parquet_has_engine_columns_after_fix():
    """After writing a parquet with the A15 pattern, the 4 engine columns
    are present. Simulates the production flow minimally."""
    with tempfile.TemporaryDirectory() as tmp:
        # Synthetic small DataFrame matching parquet schema
        df = pd.DataFrame({
            'config_id': np.array([1, 2, 3], dtype=np.uint32),
            'preset_label': ['EMA(14)', 'EMA(14)', 'EMA(14)'],
            'pf_fwd': [1.5, 2.0, 1.2],
        })
        # Apply A15 pattern
        tag = wf._get_engine_tag()
        df['engine_name'] = tag['engine_name']
        df['engine_version'] = tag['engine_version']
        df['machine_id'] = tag['machine_id']
        df['timestamp_run'] = tag['timestamp_run']
        pth = os.path.join(tmp, 'part_0000_C0.parquet')
        df.to_parquet(pth, index=False)
        # Verify
        read_back = pd.read_parquet(pth)
        for col in ('engine_name', 'engine_version', 'machine_id', 'timestamp_run'):
            assert col in read_back.columns, f"{col} missing after round-trip"
        assert read_back['engine_name'].iloc[0] == tag['engine_name']
        assert (read_back['engine_name'] == tag['engine_name']).all(), "engine_name not broadcast to all rows"
    print(f"  test_2 PASS: 4 engine columns present + broadcast correctly")


def test_3_resume_consistency_check_match():
    """Resume check with parquet carrying the current engine → no WARN."""
    with tempfile.TemporaryDirectory() as tmp:
        # Create a part file with the current engine tag
        tag = wf._get_engine_tag()
        df = pd.DataFrame({
            'config_id': np.array([1], dtype=np.uint32),
            'engine_name': [tag['engine_name']],
            'engine_version': [tag['engine_version']],
            'machine_id': [tag['machine_id']],
            'timestamp_run': [tag['timestamp_run']],
        })
        pth = os.path.join(tmp, 'part_0000_C0.parquet')
        df.to_parquet(pth, index=False)
        # Capture stdout during check
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            wf._check_resume_engine_consistency(tmp)
        out = buf.getvalue()
        assert 'consistency OK' in out or '[A15]' in out, \
            f"expected consistency-OK message, got: {out}"
        assert 'MISMATCH' not in out, f"unexpected MISMATCH in OK path: {out}"
    print(f"  test_3 PASS: resume check same engine → OK message, no WARN")


def test_4_resume_consistency_check_legacy_parquet():
    """Legacy parquet without engine_name column → WARN 'unknown'
    but no abort."""
    with tempfile.TemporaryDirectory() as tmp:
        # Create legacy parquet (no engine columns)
        df = pd.DataFrame({
            'config_id': np.array([1, 2], dtype=np.uint32),
            'pf_fwd': [1.5, 1.2],
        })
        pth = os.path.join(tmp, 'part_0000_C0.parquet')
        df.to_parquet(pth, index=False)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            wf._check_resume_engine_consistency(tmp)
        out = buf.getvalue()
        assert 'pre-A15' in out and 'unknown' in out, \
            f"expected legacy WARN with 'pre-A15' + 'unknown', got: {out}"
        # Should not raise
    print(f"  test_4 PASS: legacy parquet → WARN 'pre-A15 unknown', no abort")


def _run_all():
    print("=" * 68)
    print("A15 (W2) engine tag test suite")
    print("=" * 68)
    tests = [
        test_1_get_engine_tag_fields,
        test_2_parquet_has_engine_columns_after_fix,
        test_3_resume_consistency_check_match,
        test_4_resume_consistency_check_legacy_parquet,
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
