"""Tests greenfield resume integrity check — H_B sub-fix 2026-05-19 cumulative cross-Sub-Sesiones precedent absoluto.

Validates `_all_parts_valid_or_clean` helper que verify exists + integrity (pyarrow
metadata readable) per part file. Corrupted parts get deleted as side effect.

Origen empírico cardinal: Crash 12 cumulative 2026-05-19 left 2 corrupted parquet parts
mid-write en regime_wf/_parts_ONDOUSDT/ (part_0003_C2 + part_0004_C2). Old resume logic
cumulative skipped variants 0-4 sin verify integrity → ONDO standalone PID 5932 ran
1h51m compute (H_B confirmed cumulative) THEN FAILED at extract_validated_specialists
trying to read corrupted parts cumulative. Integrity check cheap (~1ms metadata) vs cost
regenerate 1 variant ~30s vs cost FAIL extract end ~1-2h compute loss.

Coverage:
- RI.1: all parts exist + valid → True (skip variant)
- RI.2: any part missing → False (regenerate, no deletion needed)
- RI.3: all exist + 1 corrupted → False (corrupted deleted as side effect)
- RI.4: all exist + multiple corrupted → False + all corrupted deleted
- RI.5: empty list edge case → True (vacuously, all 0 valid)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

# Project root import
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from regime_walk_forward import _all_parts_valid_or_clean


def _write_valid_parquet(path: Path, n_rows: int = 10) -> None:
    """Create a valid small parquet file at path."""
    df = pd.DataFrame({"a": range(n_rows), "b": np.random.rand(n_rows)})
    df.to_parquet(path, engine="pyarrow")


def _write_corrupted_parquet(path: Path, sz_bytes: int = 1024) -> None:
    """Create a corrupted file at path (random bytes — no valid parquet magic)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"NOT_A_PARQUET_FILE" + b"\x00" * (sz_bytes - 18))


# -----------------------------------------------------------------------------
# RI.1: all parts exist + valid → True (skip)
# -----------------------------------------------------------------------------

def test_ri_1_all_valid_returns_true(tmp_path):
    paths = [tmp_path / f"part_0000_C{k}.parquet" for k in range(3)]
    for p in paths:
        _write_valid_parquet(p)
    assert _all_parts_valid_or_clean([str(p) for p in paths]) is True
    # All files preserved (not deleted)
    for p in paths:
        assert p.exists(), f"{p} should be preserved"


# -----------------------------------------------------------------------------
# RI.2: any part missing → False (regenerate)
# -----------------------------------------------------------------------------

def test_ri_2_missing_part_returns_false(tmp_path):
    paths = [tmp_path / f"part_0000_C{k}.parquet" for k in range(3)]
    # Create only 2 of 3
    _write_valid_parquet(paths[0])
    _write_valid_parquet(paths[1])
    # paths[2] does NOT exist
    assert _all_parts_valid_or_clean([str(p) for p in paths]) is False
    # Existing files preserved
    assert paths[0].exists()
    assert paths[1].exists()


# -----------------------------------------------------------------------------
# RI.3: 1 corrupted → False + corrupted deleted (cardinal H_B sub-fix case)
# -----------------------------------------------------------------------------

def test_ri_3_one_corrupted_returns_false_deletes_corrupted(tmp_path):
    paths = [tmp_path / f"part_0000_C{k}.parquet" for k in range(3)]
    _write_valid_parquet(paths[0])
    _write_valid_parquet(paths[1])
    _write_corrupted_parquet(paths[2])  # corrupted!
    assert _all_parts_valid_or_clean([str(p) for p in paths]) is False
    # Valid parts preserved
    assert paths[0].exists() and paths[1].exists()
    # Corrupted DELETED (side effect for regeneration)
    assert not paths[2].exists(), \
        f"{paths[2]} should be deleted by integrity check"


# -----------------------------------------------------------------------------
# RI.4: multiple corrupted → False + all corrupted deleted
# -----------------------------------------------------------------------------

def test_ri_4_multiple_corrupted_all_deleted(tmp_path):
    paths = [tmp_path / f"part_0000_C{k}.parquet" for k in range(5)]
    _write_valid_parquet(paths[0])
    _write_corrupted_parquet(paths[1])
    _write_valid_parquet(paths[2])
    _write_corrupted_parquet(paths[3])
    _write_corrupted_parquet(paths[4])
    assert _all_parts_valid_or_clean([str(p) for p in paths]) is False
    assert paths[0].exists() and paths[2].exists(), "valid parts preserved"
    assert not paths[1].exists() and not paths[3].exists() and not paths[4].exists(), \
        "corrupted parts deleted"


# -----------------------------------------------------------------------------
# RI.5: empty list edge case → True (vacuously)
# -----------------------------------------------------------------------------

def test_ri_5_empty_list_returns_true(tmp_path):
    """Edge case: no parts expected (e.g., zero clusters) — vacuously valid."""
    assert _all_parts_valid_or_clean([]) is True
