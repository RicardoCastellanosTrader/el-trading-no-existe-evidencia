"""Tests v2.3.6 H1 + H4. Ejecutar:  python -m live.test_v236_h1_h4"""
import json
import os
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from live.health_monitor import (
    HealthConfig,
    _compute_portfolio_dd,
    _days_since_recycle,
)


def test_h1_dd_10pct():
    """H1: peak=300, current=270 -> DD=10.0%."""
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "engine_state.json"
        state_path.write_text(json.dumps({
            "peak_balance": 300.0,
            "current_balance": 270.0,
        }))
        cfg = HealthConfig(engine_state_path=str(state_path))
        dd = _compute_portfolio_dd(cfg)
        assert abs(dd - 10.0) < 1e-6, f"Expected 10.0, got {dd}"
        print(f"[PASS] H1 DD 10%: {dd:.4f}")


def test_h1_current_above_peak():
    """H1: current>peak -> DD=0."""
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "engine_state.json"
        state_path.write_text(json.dumps({
            "peak_balance": 300.0,
            "current_balance": 310.0,
        }))
        cfg = HealthConfig(engine_state_path=str(state_path))
        dd = _compute_portfolio_dd(cfg)
        assert dd == 0.0, f"Expected 0.0, got {dd}"
        print(f"[PASS] H1 current>peak: {dd}")


def test_h1_missing_file():
    """H1: archivo inexistente -> DD=0."""
    cfg = HealthConfig(engine_state_path="/tmp/nonexistent_xyz_12345.json")
    dd = _compute_portfolio_dd(cfg)
    assert dd == 0.0, f"Expected 0.0, got {dd}"
    print(f"[PASS] H1 missing file: {dd}")


def test_h1_current_zero_post_restart():
    """H1: current=0 (post-restart antes de primer ciclo) -> DD=0 (no 100%)."""
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "engine_state.json"
        state_path.write_text(json.dumps({
            "peak_balance": 298.39,
            "current_balance": 0.0,
        }))
        cfg = HealthConfig(engine_state_path=str(state_path))
        dd = _compute_portfolio_dd(cfg)
        assert dd == 0.0, f"Expected 0.0 (not 100%), got {dd}"
        print(f"[PASS] H1 current=0 post-restart: {dd}")


def test_h1_peak_zero():
    """H1: peak=0 (arranque fresco) -> DD=0."""
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "engine_state.json"
        state_path.write_text(json.dumps({
            "peak_balance": 0.0,
            "current_balance": 0.0,
        }))
        cfg = HealthConfig(engine_state_path=str(state_path))
        dd = _compute_portfolio_dd(cfg)
        assert dd == 0.0, f"Expected 0.0, got {dd}"
        print(f"[PASS] H1 peak=0: {dd}")


def test_h1_real_vps_snapshot():
    """H1: valores reales del VPS (peak=298.39, current=297.69) -> DD~0.23%."""
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "engine_state.json"
        state_path.write_text(json.dumps({
            "peak_balance": 298.3853,
            "current_balance": 297.69,
        }))
        cfg = HealthConfig(engine_state_path=str(state_path))
        dd = _compute_portfolio_dd(cfg)
        expected = (298.3853 - 297.69) / 298.3853 * 100.0
        assert abs(dd - expected) < 1e-4, f"Expected {expected}, got {dd}"
        print(f"[PASS] H1 real VPS snapshot: DD={dd:.4f}% (expected ~{expected:.4f}%)")


def test_h4_missing_file():
    """H4: last_recycle.txt inexistente -> 0 (no 9999)."""
    cfg = HealthConfig(last_recycle_file="/tmp/nonexistent_recycle_xyz.txt")
    days = _days_since_recycle(cfg)
    assert days == 0, f"Expected 0, got {days}"
    print(f"[PASS] H4 missing file: {days}")


def test_h4_valid_file():
    """H4: archivo valido con fecha reciente -> dias correctos."""
    from datetime import datetime, timezone, timedelta
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "last_recycle.txt"
        past = datetime.now(timezone.utc) - timedelta(days=5)
        path.write_text(past.strftime("%Y-%m-%dT%H:%M:%S+00:00"))
        cfg = HealthConfig(last_recycle_file=str(path))
        days = _days_since_recycle(cfg)
        assert days == 5, f"Expected 5, got {days}"
        print(f"[PASS] H4 valid file: {days} days")


def test_h4_corrupt_file():
    """H4: archivo corrupto -> 0 (fallback seguro)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "last_recycle.txt"
        path.write_text("not-a-valid-date")
        cfg = HealthConfig(last_recycle_file=str(path))
        days = _days_since_recycle(cfg)
        assert days == 0, f"Expected 0, got {days}"
        print(f"[PASS] H4 corrupt file: {days}")


if __name__ == "__main__":
    test_h1_dd_10pct()
    test_h1_current_above_peak()
    test_h1_missing_file()
    test_h1_current_zero_post_restart()
    test_h1_peak_zero()
    test_h1_real_vps_snapshot()
    test_h4_missing_file()
    test_h4_valid_file()
    test_h4_corrupt_file()
    print("\n[OK] Todos los tests v2.3.6 pasaron (9/9)")
