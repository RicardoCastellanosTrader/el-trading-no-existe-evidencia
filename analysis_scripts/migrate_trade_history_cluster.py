"""migrate_trade_history_cluster.py — Migración idempotente de esquema (v2.8.1).

Añade la columna 'cluster' (13ª, vacía) a trade_history.csv: reescribe header +
filas con cluster='' donde falte. Idempotente: si ya tiene 13 cols con 'cluster'
al final, reescribe idéntico (sin daño). Backup pre-migración SIEMPRE.

NO rellena el cluster (eso es el backfill desde logs, PARTE E) — solo normaliza
el esquema para que el bot v2.8.1 escriba/lea contra un header consistente.

Uso: python analysis_scripts/migrate_trade_history_cluster.py --trade-log trade_history.csv [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

CSV_COLUMNS = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
               'size_usdt', 'pnl_pct', 'pnl_usdt', 'funding_paid',
               'reason_exit', 'flag', 'entry_timestamp_ms', 'cluster']
N = len(CSV_COLUMNS)


def migrate(path: Path, apply: bool) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {"status": "empty_or_absent", "rows": 0}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        old_header = f.readline().rstrip("\n")
        rows = []
        for line in f:
            parts = line.rstrip("\n").split(",")
            while len(parts) < N:
                parts.append("")        # filas viejas → cluster='' (y cualquier col faltante)
            rows.append(parts[:N])

    header_cols = [c.strip() for c in old_header.split(",")]
    already = (len(header_cols) == N and header_cols[-1] == "cluster")

    if apply:
        bak = path.with_suffix(path.suffix + ".bak-pre-migration")
        bak.write_bytes(path.read_bytes())
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(CSV_COLUMNS) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")
        # verificación: recuento de filas preservado + header correcto
        with open(path, "r", encoding="utf-8") as f:
            new_header = f.readline().rstrip("\n")
            n_new = sum(1 for _ in f)
        ok = (new_header == ",".join(CSV_COLUMNS) and n_new == len(rows))
        return {"status": "applied" if ok else "VERIFY_FAILED",
                "rows": len(rows), "already_migrated": already,
                "backup": bak.name, "verify_ok": ok}
    return {"status": "dry_run", "rows": len(rows), "already_migrated": already,
            "old_header_cols": len(header_cols)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trade-log", default="trade_history.csv")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    res = migrate(Path(args.trade_log), args.apply)
    print(res)


if __name__ == "__main__":
    main()
