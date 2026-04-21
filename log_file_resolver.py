"""Helper compartido para resolver paths de engine.log aceptando rotation.

A36 (2026-04-23): analyzer v2.4.1 + audit v5.1 + audit v5.2 compartian logica de
`open(log_path)` sobre un archivo unico. Cuando logrotate rote orgánicamente en
VPS, una ventana de analisis cruzando rotation perderia la primera parte. Este
helper resuelve spec a lista ordenada cronologicamente y provee iterador
transparente sobre archivos planos o gzipped.

Convención logrotate detectada en VPS (verificada en audit_run_20260421/):
  engine.log.current       age=0 (mas reciente)
  engine.log.1.gz          age=1
  engine.log.2.gz          age=2
  ...
  engine.log.N.gz          age=N (mas antiguo)

Estrategia ordenamiento: N mayor = mas antiguo → posicion 0 en lista ordenada.
Sin sufijo numerico → age=0 → posicion final (mas reciente). Empate por mtime.

Uso tipico en consumidores:
    paths = resolve_engine_log_paths(args.engine_log)
    for line in read_log_files(paths):
        # ... parsing incremental
"""
from __future__ import annotations

import glob as _glob
import gzip
import os
import re
from pathlib import Path
from typing import Iterator, List


_LOGROTATE_NUMERIC_RE = re.compile(r'\.(\d+)(?:\.gz)?$')
_DATE_SUFFIX_RE = re.compile(r'-(\d{8})(?:\.gz)?$')


def _rotation_age(path: Path) -> tuple:
    """Devuelve tupla ordenable (age, mtime) para un path.

    age = int del sufijo .N o .N.gz si existe, 0 si no hay sufijo numerico.
    mtime = modification time fallback.

    Convención logrotate: N mayor = mas antiguo.
    Para ordenar del mas antiguo al mas reciente, usar key=-age primary,
    mtime asc secondary.
    """
    name = path.name
    m = _LOGROTATE_NUMERIC_RE.search(name)
    if m:
        return (int(m.group(1)), path.stat().st_mtime if path.exists() else 0.0)
    # Fallback: buscar date suffix estilo engine.log-20260421.gz
    dm = _DATE_SUFFIX_RE.search(name)
    if dm:
        # Convertir YYYYMMDD a int: valor mayor = fecha posterior = mas reciente
        # Para unificar con age logrotate: negative para que mayor date = age menor
        # (mas reciente). Compensado en sort.
        return (-int(dm.group(1)), path.stat().st_mtime if path.exists() else 0.0)
    # Archivo activo sin sufijo numerico (engine.log, engine.log.current): age=0
    return (0, path.stat().st_mtime if path.exists() else 0.0)


def _sort_paths_chronological(paths: List[Path]) -> List[Path]:
    """Ordena paths del mas antiguo al mas reciente.

    Primary key: age descendente (N mayor primero = mas antiguo primero).
    Secondary: mtime ascendente (para desempate).

    Archivos sin sufijo numerico quedan al final (age=0).
    """
    def sort_key(p: Path):
        age, mtime = _rotation_age(p)
        # age descending: usar -age
        # mtime ascending: usar mtime directo
        return (-age, mtime)
    return sorted(paths, key=sort_key)


def resolve_engine_log_paths(spec: str) -> List[Path]:
    """Resuelve spec a lista de Paths ordenados del mas antiguo al mas reciente.

    spec acepta:
      - Archivo unico: "logs/engine.log"
      - Glob pattern: "logs/engine.log*"
      - Lista CSV: "logs/engine.log.1,logs/engine.log"

    Ordenamiento cronologico:
      - Sufijo logrotate .N o .N.gz: N mayor = mas antiguo.
      - Sufijo date -YYYYMMDD: fecha menor = mas antiguo.
      - Fallback mtime ascendente.

    Raises:
      FileNotFoundError: si spec resuelve a 0 archivos.
      ValueError: si spec es None o vacio.
    """
    if not spec:
        raise ValueError("resolve_engine_log_paths: spec vacio")

    # Detectar forma CSV primero (separador explicito)
    if ',' in spec:
        candidates = [s.strip() for s in spec.split(',') if s.strip()]
        paths = []
        for c in candidates:
            p = Path(c)
            if not p.exists():
                raise FileNotFoundError(f"CSV spec: archivo no existe: {c}")
            paths.append(p)
    elif any(ch in spec for ch in ['*', '?', '[']):
        # Glob pattern
        matches = _glob.glob(spec)
        if not matches:
            raise FileNotFoundError(f"Glob spec: 0 matches para: {spec}")
        paths = [Path(m) for m in matches]
    else:
        # Archivo unico
        p = Path(spec)
        if not p.exists():
            raise FileNotFoundError(f"Archivo unico no existe: {spec}")
        paths = [p]

    return _sort_paths_chronological(paths)


def read_log_files(paths: List[Path]) -> Iterator[str]:
    """Iterador lazy linea a linea sobre lista de archivos en orden.

    Soporta .gz transparentemente (gzip.open si path.suffix == '.gz').
    Encoding utf-8 con errors='replace' (consistencia con consumidores actuales).

    paths se espera ya ordenado (mas antiguo primero) — usar
    resolve_engine_log_paths previamente.
    """
    for p in paths:
        if p.suffix == '.gz':
            f = gzip.open(p, 'rt', encoding='utf-8', errors='replace')
        else:
            f = open(p, 'r', encoding='utf-8', errors='replace')
        with f:
            for line in f:
                yield line
