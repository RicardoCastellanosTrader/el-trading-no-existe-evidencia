"""Tests for audit_lab_lite_window.py (Caveat #21 §13.2 audit script)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import audit_lab_lite_window as audit


def test_preset_signature_canonical():
    """Signature ignores p1/p2 — clusters similar variants under fast/slow type+period."""
    e1 = (0, 20, 0, 0)  # EMA(20) — type 0
    e2 = (1, 50, 0, 0)  # SMA(50) — type 1
    sig = audit.preset_signature(e1, e2)
    assert sig == "EMA(20)/SMA(50)"


def test_preset_signature_alma_with_p1p2_ignored():
    e1 = (3, 12, 0.85, 4.0)  # ALMA(12, 0.85, 4)
    e2 = (10, 60, 0, 0)  # FRAMA(60)
    sig = audit.preset_signature(e1, e2)
    assert sig == "ALMA(12)/FRAMA(60)"


def test_jaccard_identical_sets():
    a = {"EMA(20)/SMA(50)", "VIDYA(18)/FRAMA(60)"}
    assert audit.jaccard(a, a) == 1.0


def test_jaccard_disjoint_sets():
    a = {"EMA(20)/SMA(50)"}
    b = {"VIDYA(18)/FRAMA(60)"}
    assert audit.jaccard(a, b) == 0.0


def test_jaccard_partial_overlap():
    a = {"X", "Y", "Z"}
    b = {"Y", "Z", "W"}
    # intersection=2, union=4 → 0.5
    assert audit.jaccard(a, b) == 0.5


def test_jaccard_empty_sets():
    assert audit.jaccard(set(), set()) == 1.0


def test_overlap_report_structure():
    pools = {
        "A": {"X", "Y"},
        "B": {"Y", "Z"},
    }
    r = audit.overlap_report(pools)
    assert "jaccard" in r
    assert "sizes" in r
    assert r["sizes"]["A"] == 2
    assert r["sizes"]["B"] == 2
    assert r["jaccard"]["A_vs_B"] == round(1 / 3, 4)
    assert "X" in r["only_in"]["A_not_B"]
    assert "Z" in r["only_in"]["B_not_A"]
    assert r["intersection"]["A_vs_B"] == ["Y"]


def test_load_full_parquet_btc_exists():
    """BTC parquet should load with full history (~76K bars expected)."""
    df = audit.load_full_parquet("BTC/USDT")
    assert len(df) > 50000, f"BTC parquet only has {len(df)} bars"
    assert {"timestamp", "open", "high", "low", "close", "volume"}.issubset(df.columns)


def test_load_full_parquet_missing_raises():
    with pytest.raises(FileNotFoundError):
        audit.load_full_parquet("NONEXISTENT/USDT")


def test_extract_mode_a_signatures_btc():
    """Mode A reads existing presets CSV — BTC should have 28-32 unique signatures."""
    try:
        sigs = audit.extract_mode_a_signatures("BTC/USDT")
    except FileNotFoundError:
        pytest.skip("BTC presets CSV not present")
    assert 10 < len(sigs) < 40, f"unexpected sigs count {len(sigs)}"
    # Each sig follows canonical format
    for s in sigs:
        assert "/" in s
        assert "(" in s and ")" in s


def test_overlap_report_jaccard_value_range():
    """All Jaccard values must lie in [0,1]."""
    pools = {
        "A": {"X", "Y", "Z"},
        "B": {"Y", "Z", "W", "V"},
        "C": set(),
    }
    r = audit.overlap_report(pools)
    for k, v in r["jaccard"].items():
        assert 0.0 <= v <= 1.0, f"{k} Jaccard out of range: {v}"
