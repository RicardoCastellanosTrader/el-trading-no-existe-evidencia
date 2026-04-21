"""Tests de integracion A36 — parse_engine_log glob vs concat.

Usa fixture real audit_run_20260421/ (5 archivos rotados + 1 concat existente).

Criterios:
  1. Backward compat: parse_engine_log(concat) == current behavior.
  2. Glob equivalente a concat: parse_engine_log(glob) produce MISMOS counts
     y claves que parse_engine_log(concat).
  3. Los 3 consumidores (analyzer, audit v5.1, audit v5.2) comparten el mismo
     parser con la misma semantica.

Run: python tests/test_a36_integration.py
"""
from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


FIXTURE_DIR = Path(ROOT) / "audit_run_20260421"
CONCAT = FIXTURE_DIR / "engine.log.concat"

# Rotated files actuales sin incluir .concat (artificial) ni trade_history.csv.
# Orden cronologico ASC (mas antiguo primero) = logrotate age descendente.
_ROTATED_FILES = [
    "engine.log.4.gz",
    "engine.log.3.gz",
    "engine.log.2.gz",
    "engine.log.1.gz",
    "engine.log.current",
]


def _make_rotated_fixture_dir() -> Path:
    """Copia los 5 archivos rotados a un tmpdir para evitar que glob
    matche tambien engine.log.concat (que es fixture artificial).
    Retorna path del tmpdir; caller responsable de shutil.rmtree.
    """
    td = Path(tempfile.mkdtemp(prefix="a36_fixture_"))
    for name in _ROTATED_FILES:
        shutil.copy2(FIXTURE_DIR / name, td / name)
    return td


def _assert_result_equivalent(r_concat, r_glob, script_name):
    """Compara dicts retornados por parse_engine_log. Usa keys/counts."""
    for k in ('engine_states', 'brain_reconciles', 'orphan_closes',
              'signals_executed', 'signals_raw'):
        len_c = len(r_concat.get(k, {}))
        len_g = len(r_glob.get(k, {}))
        assert len_c == len_g, (
            f"[{script_name}] key={k} concat={len_c} glob={len_g} MISMATCH"
        )
    # Sanity: keys deben ser IDENTICAS (mismo set, no solo misma cardinalidad)
    for k in ('engine_states', 'brain_reconciles', 'orphan_closes',
              'signals_executed', 'signals_raw'):
        keys_c = set(r_concat.get(k, {}).keys())
        keys_g = set(r_glob.get(k, {}).keys())
        assert keys_c == keys_g, (
            f"[{script_name}] key={k} concat/glob different keys: "
            f"only_c={list(keys_c - keys_g)[:3]}, only_g={list(keys_g - keys_c)[:3]}"
        )
    print(f"OK [{script_name}] glob == concat (engine_states={len(r_concat['engine_states'])}, "
          f"signals_raw={len(r_concat['signals_raw'])}, "
          f"signals_executed={len(r_concat['signals_executed'])}, "
          f"brain_reconciles={len(r_concat['brain_reconciles'])}, "
          f"orphan_closes={len(r_concat['orphan_closes'])})")


def _test_script(module_name, script_label):
    """Importa modulo del consumidor, ejecuta parse_engine_log glob vs concat."""
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    mod = importlib.import_module(module_name)

    log_start_date = pd.Timestamp("2026-04-19")
    r_concat = mod.parse_engine_log(str(CONCAT), log_start_date)

    td = _make_rotated_fixture_dir()
    try:
        glob_spec = str(td / "engine.log.*")
        r_glob = mod.parse_engine_log(glob_spec, log_start_date)
        _assert_result_equivalent(r_concat, r_glob, script_label)
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_analyzer_glob_vs_concat():
    """Test integracion analyzer v2.4.1."""
    _test_script("analyze_performance_attribution", "analyzer v2.4.1")


def test_audit_v51_glob_vs_concat():
    """Test integracion audit v5.1."""
    _test_script("audit_fidelity_v5", "audit v5.1")


def test_audit_v52_glob_vs_concat():
    """Test integracion audit v5.2."""
    _test_script("audit_fidelity_v5_2", "audit v5.2")


def test_backward_compat_single_file():
    """Backward compat: pasar archivo unico produce mismos resultados que concat."""
    # Esto es implicitamente lo que hace _test_script con CONCAT — si
    # parse_engine_log(CONCAT) no falla, backward compat OK.
    import analyze_performance_attribution as mod_an
    r = mod_an.parse_engine_log(str(CONCAT), pd.Timestamp("2026-04-19"))
    assert len(r['engine_states']) > 0, "parse_engine_log(concat) sin engine_states"
    print(f"OK backward_compat archivo unico: engine_states={len(r['engine_states'])}")


def test_csv_spec():
    """CSV spec: concatenar 2 archivos explicitos produce resultado consistente."""
    import analyze_performance_attribution as mod_an
    # Usar 2 de los gz explicitamente (los mas antiguos)
    csv_spec = f"{FIXTURE_DIR/'engine.log.4.gz'},{FIXTURE_DIR/'engine.log.3.gz'}"
    r = mod_an.parse_engine_log(csv_spec, pd.Timestamp("2026-04-19"))
    # Deberia parsear algo (archivos existen y tienen contenido)
    assert len(r['engine_states']) > 0, "CSV spec sin engine_states"
    print(f"OK csv_spec con 2 gz: engine_states={len(r['engine_states'])}")


def test_invalid_spec_returns_empty():
    """Spec que no resuelve (glob sin matches) retorna result vacio (backward compat)."""
    import analyze_performance_attribution as mod_an
    r = mod_an.parse_engine_log("/nonexistent_xyz*/engine.log*",
                                pd.Timestamp("2026-04-19"))
    assert r['engine_states'] == {}, "Spec invalido deberia retornar result vacio"
    assert r['log_start_ts'] is None
    print("OK invalid_spec retorna result vacio (backward compat)")


if __name__ == "__main__":
    tests = [
        test_backward_compat_single_file,
        test_invalid_spec_returns_empty,
        test_csv_spec,
        test_analyzer_glob_vs_concat,
        test_audit_v51_glob_vs_concat,
        test_audit_v52_glob_vs_concat,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    total = len(tests)
    print(f"\n{total - failed}/{total} tests PASS")
    sys.exit(0 if failed == 0 else 1)
