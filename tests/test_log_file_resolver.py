"""Tests unitarios para log_file_resolver (A36 — log rotation tolerance).

Run: python tests/test_log_file_resolver.py
     o: python -m pytest tests/test_log_file_resolver.py -v
"""
from __future__ import annotations

import gzip
import os
import sys
import tempfile
from pathlib import Path

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from log_file_resolver import (
    resolve_engine_log_paths,
    read_log_files,
    _rotation_age,
    _sort_paths_chronological,
)


def _mk(tmp: Path, name: str, content: str = "") -> Path:
    p = tmp / name
    p.write_text(content, encoding='utf-8')
    return p


def _mk_gz(tmp: Path, name: str, content: str = "") -> Path:
    p = tmp / name
    with gzip.open(p, 'wt', encoding='utf-8') as f:
        f.write(content)
    return p


def test_single_file_path():
    """Test 1 — Single file (backward compat)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p = _mk(tmp, "engine.log", "line\n")
        result = resolve_engine_log_paths(str(p))
        assert len(result) == 1
        assert result[0].name == "engine.log"
    print("OK test_single_file_path")


def test_glob_pattern_logrotate_ordering():
    """Test 2 — Glob pattern con logrotate numeric.

    N mayor = mas antiguo → posicion 0.
    Sin sufijo numerico (activo) → posicion final.
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _mk(tmp, "engine.log", "newest\n")
        _mk(tmp, "engine.log.1", "mid\n")
        _mk(tmp, "engine.log.2", "oldest\n")
        result = resolve_engine_log_paths(str(tmp / "engine.log*"))
        names = [p.name for p in result]
        assert names == ["engine.log.2", "engine.log.1", "engine.log"], \
            f"Orden incorrecto: {names}"
    print("OK test_glob_pattern_logrotate_ordering")


def test_glob_pattern_logrotate_gzip_ordering():
    """Test 2b — Glob pattern con .N.gz (convención VPS real)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _mk(tmp, "engine.log.current", "newest\n")
        _mk_gz(tmp, "engine.log.1.gz", "age1\n")
        _mk_gz(tmp, "engine.log.2.gz", "age2\n")
        _mk_gz(tmp, "engine.log.3.gz", "age3\n")
        _mk_gz(tmp, "engine.log.4.gz", "age4\n")
        result = resolve_engine_log_paths(str(tmp / "engine.log*"))
        names = [p.name for p in result]
        assert names == [
            "engine.log.4.gz",
            "engine.log.3.gz",
            "engine.log.2.gz",
            "engine.log.1.gz",
            "engine.log.current",
        ], f"Orden incorrecto: {names}"
    print("OK test_glob_pattern_logrotate_gzip_ordering")


def test_csv_list():
    """Test 3 — CSV list (orden preservado en spec, pero re-ordenado por rotation)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = _mk(tmp, "engine.log.1", "old\n")
        b = _mk(tmp, "engine.log", "new\n")
        # User pasa en orden arbitrario; resolver ordena cronologicamente
        spec = f"{b},{a}"
        result = resolve_engine_log_paths(spec)
        names = [p.name for p in result]
        assert names == ["engine.log.1", "engine.log"], f"CSV no re-ordenado: {names}"
    print("OK test_csv_list")


def test_csv_list_missing_file_raises():
    """Test 3b — CSV con archivo inexistente levanta FileNotFoundError."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _mk(tmp, "engine.log", "x\n")
        spec = f"{tmp/'engine.log'},{tmp/'nonexistent.log'}"
        try:
            resolve_engine_log_paths(spec)
            assert False, "Deberia haber lanzado FileNotFoundError"
        except FileNotFoundError:
            pass
    print("OK test_csv_list_missing_file_raises")


def test_empty_glob_raises():
    """Test 4 — Glob sin matches levanta FileNotFoundError."""
    try:
        resolve_engine_log_paths("/nonexistent_dir_xyzzy/engine.log*")
        assert False, "Deberia haber lanzado FileNotFoundError"
    except FileNotFoundError:
        pass
    print("OK test_empty_glob_raises")


def test_single_file_missing_raises():
    """Test 4b — Archivo unico inexistente levanta FileNotFoundError."""
    try:
        resolve_engine_log_paths("/nonexistent_dir_xyzzy/engine.log")
        assert False, "Deberia haber lanzado FileNotFoundError"
    except FileNotFoundError:
        pass
    print("OK test_single_file_missing_raises")


def test_empty_spec_raises():
    """Test 4c — spec vacio levanta ValueError."""
    try:
        resolve_engine_log_paths("")
        assert False, "Deberia haber lanzado ValueError"
    except ValueError:
        pass
    try:
        resolve_engine_log_paths(None)
        assert False, "Deberia haber lanzado ValueError"
    except ValueError:
        pass
    print("OK test_empty_spec_raises")


def test_read_log_files_preserves_order():
    """Test 5 — read_log_files concatena en orden de lista."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = _mk(tmp, "a", "line1\nline2\n")
        b = _mk(tmp, "b", "line3\nline4\n")
        lines = list(read_log_files([a, b]))
        assert lines == ["line1\n", "line2\n", "line3\n", "line4\n"], \
            f"Orden lineas incorrecto: {lines}"
    print("OK test_read_log_files_preserves_order")


def test_gzip_transparent():
    """Test 6 — read_log_files soporta .gz transparentemente."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = _mk(tmp, "a.log", "plain\n")
        b = _mk_gz(tmp, "b.log.gz", "compressed\n")
        lines = list(read_log_files([a, b]))
        assert "plain\n" in lines
        assert "compressed\n" in lines
        # Orden preservado (a antes que b)
        assert lines == ["plain\n", "compressed\n"], f"Orden incorrecto: {lines}"
    print("OK test_gzip_transparent")


def test_read_log_files_empty_list():
    """Test 6b — read_log_files con lista vacia retorna iterador vacio."""
    lines = list(read_log_files([]))
    assert lines == []
    print("OK test_read_log_files_empty_list")


def test_rotation_age_helper():
    """Test 7 — _rotation_age clasifica correctamente sufijos."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p_active = _mk(tmp, "engine.log", "")
        p_current = _mk(tmp, "engine.log.current", "")
        p_n1 = _mk(tmp, "engine.log.1", "")
        p_n4_gz = _mk_gz(tmp, "engine.log.4.gz", "")

        age_active, _ = _rotation_age(p_active)
        age_current, _ = _rotation_age(p_current)
        age_n1, _ = _rotation_age(p_n1)
        age_n4, _ = _rotation_age(p_n4_gz)

        assert age_active == 0, f"engine.log age={age_active}, expected 0"
        assert age_current == 0, f"engine.log.current age={age_current}, expected 0"
        assert age_n1 == 1, f"engine.log.1 age={age_n1}, expected 1"
        assert age_n4 == 4, f"engine.log.4.gz age={age_n4}, expected 4"
    print("OK test_rotation_age_helper")


def test_integration_with_audit_run_fixture():
    """Test 8 — Integracion con fixture estilo audit_run_20260421/ del repo."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _mk(tmp, "engine.log.current", "CYCLE_N\n")
        _mk_gz(tmp, "engine.log.1.gz", "CYCLE_N-1\n")
        _mk_gz(tmp, "engine.log.2.gz", "CYCLE_N-2\n")
        _mk_gz(tmp, "engine.log.3.gz", "CYCLE_N-3\n")
        _mk_gz(tmp, "engine.log.4.gz", "CYCLE_N-4\n")

        paths = resolve_engine_log_paths(str(tmp / "engine.log*"))
        lines = list(read_log_files(paths))
        # Orden cronologico: mas antiguo primero
        assert lines == [
            "CYCLE_N-4\n",
            "CYCLE_N-3\n",
            "CYCLE_N-2\n",
            "CYCLE_N-1\n",
            "CYCLE_N\n",
        ], f"Orden eventos no cronologico: {lines}"
    print("OK test_integration_with_audit_run_fixture")


if __name__ == "__main__":
    tests = [
        test_single_file_path,
        test_glob_pattern_logrotate_ordering,
        test_glob_pattern_logrotate_gzip_ordering,
        test_csv_list,
        test_csv_list_missing_file_raises,
        test_empty_glob_raises,
        test_single_file_missing_raises,
        test_empty_spec_raises,
        test_read_log_files_preserves_order,
        test_gzip_transparent,
        test_read_log_files_empty_list,
        test_rotation_age_helper,
        test_integration_with_audit_run_fixture,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    total = len(tests)
    print(f"\n{total - failed}/{total} tests PASS")
    sys.exit(0 if failed == 0 else 1)
