"""
Tests del gate de sincronización horaria (live/clock_sync.py).

Mockea la salida de chronyc/timedatectl (vía clock_sync._run) para cubrir:
sincronizado OK, no-sincronizado, offset alto, fallback timesyncd, sin NTP tool,
y la semántica del gate de arranque (DRY_RUN avisa / órdenes reales abortan).

Standalone: python tests/test_clock_sync.py   |   Pytest: pytest tests/test_clock_sync.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import live.clock_sync as cs


CHRONY_OK = """Reference ID    : 0A0A0A0A
Stratum         : 3
System time     : 0.000012 seconds slow of NTP time
Last offset     : -0.000001 seconds
RMS offset      : 0.000005 seconds
Leap status     : Normal
"""

CHRONY_UNSYNCED = """Reference ID    : 00000000
Stratum         : 0
System time     : 0.000000 seconds slow of NTP time
Last offset     : +0.000000 seconds
Leap status     : Not synchronised
"""

CHRONY_HIGH_OFFSET = """Reference ID    : 0A0A0A0A
Stratum         : 3
System time     : 0.500000 seconds slow of NTP time
Last offset     : +0.480000 seconds
Leap status     : Normal
"""


def _install(mapping):
    """Patch clock_sync._run para devolver stdout canónico por subcomando."""
    def _fake(cmd, timeout=5.0):
        s = " ".join(cmd)
        for key, val in mapping.items():
            if key in s:
                return val
        return None
    _saved = cs._run
    cs._run = _fake
    return _saved


def test_chrony_synced_ok():
    saved = _install({"chronyc": CHRONY_OK})
    try:
        ok, d = cs.check_clock_sync(max_offset_ms=250)
    finally:
        cs._run = saved
    assert ok is True, d
    assert d["tool"] == "chrony" and d["offset_ms"] is not None
    print(f"  [OK] chrony synced: offset {d['offset_ms']}ms")


def test_chrony_not_synchronised():
    saved = _install({"chronyc": CHRONY_UNSYNCED})
    try:
        ok, d = cs.check_clock_sync()
    finally:
        cs._run = saved
    assert ok is False and "Normal" in d["reason"] or "leap" in d["reason"].lower()
    print(f"  [OK] chrony not synchronised -> ok=False ({d['reason']})")


def test_chrony_high_offset():
    saved = _install({"chronyc": CHRONY_HIGH_OFFSET})
    try:
        ok, d = cs.check_clock_sync(max_offset_ms=250)
    finally:
        cs._run = saved
    assert ok is False and "offset" in d["reason"]
    print(f"  [OK] chrony high offset -> ok=False ({d['reason']})")


def test_timesyncd_fallback_ok():
    # chronyc ausente -> cae a timedatectl
    saved = _install({"NTPSynchronized": "yes\n",
                      "timesync-status": "       Server: 1.2.3.4\n       Offset: +0.5ms\n"})
    try:
        ok, d = cs.check_clock_sync(max_offset_ms=250)
    finally:
        cs._run = saved
    assert ok is True, d
    assert d["tool"] == "timesyncd"
    print(f"  [OK] timesyncd synced fallback: {d.get('offset_ms')}ms")


def test_no_ntp_tool():
    saved = _install({})  # ningún comando disponible
    try:
        ok, d = cs.check_clock_sync()
    finally:
        cs._run = saved
    assert ok is False and d["tool"] is None
    print(f"  [OK] sin NTP tool -> ok=False ({d['reason']})")


def test_gate_dry_run_warns_real_aborts():
    saved = _install({})  # no sincronizado
    try:
        # DRY_RUN: avisa pero continúa (sin órdenes reales)
        assert cs.assert_clock_synced_for_trading(dry_run=True) is True
        # Órdenes reales: aborta (False -> caller raise)
        assert cs.assert_clock_synced_for_trading(dry_run=False) is False
        # Sincronizado: True en ambos
        cs._run = lambda cmd, timeout=5.0: CHRONY_OK if "chronyc" in " ".join(cmd) else None
        assert cs.assert_clock_synced_for_trading(dry_run=False) is True
    finally:
        cs._run = saved
    print("  [OK] gate: DRY_RUN avisa / órdenes reales abortan / synced pasa")


if __name__ == "__main__":
    tests = [
        test_chrony_synced_ok,
        test_chrony_not_synchronised,
        test_chrony_high_offset,
        test_timesyncd_fallback_ok,
        test_no_ntp_tool,
        test_gate_dry_run_warns_real_aborts,
    ]
    print("=" * 60)
    print("Running tests/test_clock_sync.py")
    print("=" * 60)
    for t in tests:
        t()
    print("=" * 60)
    print(f"[OK] {len(tests)}/{len(tests)} tests PASS")
