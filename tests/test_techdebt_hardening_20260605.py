"""Tests greenfield — tanda tech-debt post-cert Grupo 3 (2026-06-05).

Cubre los 3 items remediados (robustez/error-handling, NO lógica de cómputo):
  A.1 master resume JSON-read: JSON corrupto -> skip_read_error (no skip silencioso).
  A.2 rwf integrity check: parts corruptos -> quarantine (.corrupt-bak), no unlink ciego.
  A.3 orchestrator resume-skip: specialist válido en disco -> mark done + skip (anti-re-run).
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------- A.3 _reciclaje_specialist_valid ----------
def _make_specialist(path, n_clusters=3, full=True):
    clusters = {}
    for k in range(n_clusters):
        clusters[str(k)] = {"top_configs": [{"config_id": 123, "pf_fwd": 2.0}] if full else []}
    path.write_text(json.dumps({"n_clusters": n_clusters, "clusters": clusters}), encoding="utf-8")


def test_a3_specialist_valid_complete(tmp_path):
    import automation_orchestrator as ao
    p = tmp_path / "ADAUSDT_specialist_configs.json"
    _make_specialist(p, 3, full=True)
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(p) is True


def test_a3_specialist_valid_partial_is_false(tmp_path):
    import automation_orchestrator as ao
    p = tmp_path / "X_specialist_configs.json"
    # 3 clusters declarados pero 1 sin top_configs -> parcial -> NO válido
    clusters = {"0": {"top_configs": [{"config_id": 1}]},
                "1": {"top_configs": [{"config_id": 2}]},
                "2": {"top_configs": []}}
    p.write_text(json.dumps({"n_clusters": 3, "clusters": clusters}), encoding="utf-8")
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(p) is False


def test_a3_specialist_valid_missing_is_false(tmp_path):
    import automation_orchestrator as ao
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(tmp_path / "nope.json") is False


def test_a3_specialist_valid_corrupt_json_is_false(tmp_path):
    import automation_orchestrator as ao
    p = tmp_path / "corrupt_specialist_configs.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(p) is False


# ---------- ancla de recencia resume-skip (2026-06-06, caso origen G4 launch) ----------
def test_a3_specialist_valid_stale_mtime_is_false(tmp_path):
    """JSON estructuralmente válido pero LEGACY (mtime < ancla) -> NO válido (re-compute)."""
    import time
    import automation_orchestrator as ao
    p = tmp_path / "LTCUSDT_specialist_configs.json"
    _make_specialist(p, 3, full=True)
    legacy = time.time() - 30 * 86400  # 30 días atrás (reciclaje marzo/abril)
    os.utime(p, (legacy, legacy))
    anchor = time.time() - 60  # ancla = launch hace 1 min
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(p, min_mtime=anchor) is False


def test_a3_specialist_valid_fresh_mtime_is_true(tmp_path):
    """JSON válido escrito DESPUÉS del ancla (relaunch mid-grupo) -> skip preservado."""
    import time
    import automation_orchestrator as ao
    p = tmp_path / "LTCUSDT_specialist_configs.json"
    _make_specialist(p, 3, full=True)  # mtime = ahora
    anchor = time.time() - 3600  # ancla = launch hace 1h
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(p, min_mtime=anchor) is True


def test_a3_specialist_valid_no_anchor_backward_compat(tmp_path):
    """Sin min_mtime el comportamiento original se preserva (validez estructural sola)."""
    import time
    import automation_orchestrator as ao
    p = tmp_path / "X_specialist_configs.json"
    _make_specialist(p, 3, full=True)
    legacy = time.time() - 30 * 86400
    os.utime(p, (legacy, legacy))
    assert ao.AutomationOrchestrator._reciclaje_specialist_valid(p) is True


# ---------- A.2 rwf integrity check quarantine ----------
def test_a2_corrupted_part_quarantined_not_deleted(tmp_path):
    import regime_walk_forward as rwf
    # part "corrupto" = no es parquet válido
    good = tmp_path / "part_0000_C0.parquet"
    bad = tmp_path / "part_0000_C1.parquet"
    # crear un parquet válido para 'good'
    import pandas as pd
    pd.DataFrame({"a": [1, 2, 3]}).to_parquet(good)
    bad.write_text("CORRUPT-NOT-PARQUET", encoding="utf-8")
    result = rwf._all_parts_valid_or_clean([str(good), str(bad)])
    assert result is False  # integridad falla
    # el corrupto debe estar en cuarentena (.corrupt-bak), NO borrado sin rastro
    assert (tmp_path / "part_0000_C1.parquet.corrupt-bak").exists(), "corrupted part debe quedar en .corrupt-bak (rollback safety)"
    assert not bad.exists(), "el part corrupto original se renombra (ya no en path original)"
    assert good.exists(), "el part válido NO se toca"


def test_a2_all_valid_returns_true(tmp_path):
    import regime_walk_forward as rwf
    import pandas as pd
    paths = []
    for k in range(3):
        p = tmp_path / f"part_0000_C{k}.parquet"
        pd.DataFrame({"a": [1]}).to_parquet(p)
        paths.append(str(p))
    assert rwf._all_parts_valid_or_clean(paths) is True


def test_a2_missing_part_returns_false(tmp_path):
    import regime_walk_forward as rwf
    assert rwf._all_parts_valid_or_clean([str(tmp_path / "missing.parquet")]) is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
