"""Tests A35 — cross_exchange_diff_pct tz-naive defensive.

Verifica:
  - tz-aware ambos: comportamiento preservado (bx/bn close identicos -> diff 0).
  - tz-naive target_ts: tz_localize('UTC') fallback evita TypeError.
  - None inputs retorna None (unchanged).
  - bx_close <= 0 retorna None (unchanged).

Run: python tests/test_a35_tz_naive_defensive.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _mk_df(ts_list, close_list, tz='UTC'):
    if tz is None:
        timestamps = [pd.Timestamp(t) for t in ts_list]
    else:
        timestamps = [pd.Timestamp(t, tz=tz) for t in ts_list]
    return pd.DataFrame({'timestamp': timestamps, 'close': close_list})


def _test_module(module_name, label):
    import importlib
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    mod = importlib.import_module(module_name)
    f = mod.cross_exchange_diff_pct

    # Test 1: tz-aware ambos, cierres identicos -> diff=0%
    bx = _mk_df(['2026-04-21 12:00', '2026-04-21 13:00'], [100.0, 101.0])
    bn = _mk_df(['2026-04-21 12:00', '2026-04-21 13:00'], [100.0, 101.0])
    ts_aware = pd.Timestamp('2026-04-21 12:00', tz='UTC')
    diff = f(bx, bn, ts_aware)
    assert diff == 0.0, f"[{label}] tz-aware identical: expected 0.0, got {diff}"
    print(f"OK [{label}] tz-aware identical -> diff=0.0")

    # Test 2: tz-aware con diff conocido (0.5%)
    bx2 = _mk_df(['2026-04-21 12:00'], [100.0])
    bn2 = _mk_df(['2026-04-21 12:00'], [100.5])
    diff2 = f(bx2, bn2, ts_aware)
    assert abs(diff2 - 0.5) < 1e-9, f"[{label}] tz-aware 0.5%: got {diff2}"
    print(f"OK [{label}] tz-aware diff=0.5% correcto")

    # Test 3: tz-naive target_ts (A35 core) — no TypeError, resultado consistente
    ts_naive = pd.Timestamp('2026-04-21 12:00')  # naive
    assert ts_naive.tzinfo is None
    try:
        diff3 = f(bx, bn, ts_naive)
    except TypeError as e:
        raise AssertionError(f"[{label}] tz-naive deberia ser localized, no TypeError: {e}")
    assert diff3 == 0.0, f"[{label}] tz-naive localized: expected 0.0, got {diff3}"
    print(f"OK [{label}] tz-naive -> tz_localize(UTC) fallback -> diff=0.0 (sin TypeError)")

    # Test 4: None inputs -> None (preservar)
    assert f(None, bn, ts_aware) is None, f"[{label}] None bingx deberia retornar None"
    assert f(bx, None, ts_aware) is None, f"[{label}] None binance deberia retornar None"
    print(f"OK [{label}] None inputs -> None (backward compat)")

    # Test 5: bx_close <= 0 -> None (preservar)
    bx_zero = _mk_df(['2026-04-21 12:00'], [0.0])
    assert f(bx_zero, bn, ts_aware) is None, f"[{label}] bx_close=0 deberia retornar None"
    bx_neg = _mk_df(['2026-04-21 12:00'], [-1.0])
    assert f(bx_neg, bn, ts_aware) is None, f"[{label}] bx_close<0 deberia retornar None"
    print(f"OK [{label}] bx_close<=0 -> None (backward compat)")

    # Test 6: target_ts no en ambos df -> None
    ts_missing = pd.Timestamp('2026-04-21 14:00', tz='UTC')
    assert f(bx, bn, ts_missing) is None, f"[{label}] ts no presente deberia retornar None"
    print(f"OK [{label}] ts fuera de ambos df -> None (backward compat)")


def test_audit_v51():
    _test_module("audit_fidelity_v5", "audit v5.1")


def test_audit_v52():
    _test_module("audit_fidelity_v5_2", "audit v5.2")


if __name__ == "__main__":
    tests = [test_audit_v51, test_audit_v52]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    total = len(tests)
    # Each test does 6 sub-checks
    print(f"\n{total - failed}/{total} test groups PASS ({(total-failed)*6}/12 sub-checks)")
    sys.exit(0 if failed == 0 else 1)
