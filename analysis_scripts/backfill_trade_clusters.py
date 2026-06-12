"""backfill_trade_clusters.py — Backfill de la columna 'cluster' en trade_history.csv
desde los logs SIGNALS_RAW del bot (v2.8.1, PARTE E).

Fuente ÚNICA = logs (SIGNALS_RAW lleva "k"=cluster + "t"=timestamp de barra por
símbolo/ciclo). FIEL a lo que el bot realmente clasificó (incluida la hysteresis
path-dependent). NO re-clasificación offline (produciría etiquetas que el bot
nunca vio — decisión Ricardo 4).

Matcher: para un trade con entry_timestamp_ms + símbolo, toma el registro
SIGNALS_RAW del MISMO símbolo con el "t" más reciente <= entrada (el ciclo que
disparó la apertura; caso ambiguo k cambió intra-barra → registro inmediatamente
anterior a la entrada). Sin registro dentro de la tolerancia → None (NULL,
excluido de la evaluación per-par; la ventana rolling 30d se autocura).

Uso:
    python analysis_scripts/backfill_trade_clusters.py \
        --trade-log trade_history.csv --logs-glob 'logs/engine.log*' [--apply]
Sin --apply: dry-run (reporta matched/unmatched + distribución + spot-check).
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path
from typing import Optional

# t (segundos) de SIGNALS_RAW es el cierre de la barra horaria; entry_timestamp_ms
# es la ejecución (ms, justo después). El registro válido está dentro de ~2h.
DEFAULT_MAX_GAP_MS = 2 * 3600 * 1000

_SIGNALS_RAW_RE = re.compile(r"SIGNALS_RAW\]\s*(\{.*\})\s*$")


def parse_signals_raw_line(line: str) -> Optional[dict]:
    """Extrae el JSON de una línea [SIGNALS_RAW]. None si no aplica/parse falla."""
    m = _SIGNALS_RAW_RE.search(line)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except (json.JSONDecodeError, ValueError):
        return None


def build_signal_index(log_paths: list) -> dict:
    """Construye {symbol: [(t_ms, k), ...]} ordenado asc por t_ms desde los logs.

    Soporta .log y .gz. Dedup por (symbol, t_ms) — un mismo ciclo puede repetirse
    en logs solapados; se conserva el último k visto para ese t.
    """
    tmp: dict = {}  # symbol -> {t_ms: k}
    for p in log_paths:
        path = Path(p)
        if not path.exists():
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "SIGNALS_RAW" not in line:
                        continue
                    payload = parse_signals_raw_line(line)
                    if not payload:
                        continue
                    for sym, entry in payload.items():
                        if not isinstance(entry, dict):
                            continue
                        k = entry.get("k")
                        t = entry.get("t")
                        if k is None or t is None:
                            continue
                        t_ms = int(t) * 1000
                        tmp.setdefault(sym, {})[t_ms] = int(k)
        except OSError:
            continue
    index = {}
    for sym, d in tmp.items():
        index[sym] = sorted(d.items())  # list[(t_ms, k)] asc
    return index


def match_cluster(index: dict, symbol: str, entry_ts_ms: int,
                  max_gap_ms: int = DEFAULT_MAX_GAP_MS) -> Optional[int]:
    """Cluster del registro con t_ms más reciente <= entry_ts_ms (dentro de max_gap).

    None si no hay registro previo dentro de la tolerancia (hueco de log o trade
    fuera del horizonte de retención).
    """
    if not entry_ts_ms or entry_ts_ms <= 0:
        return None
    recs = index.get(symbol)
    if not recs:
        return None
    best_t, best_k = None, None
    for t_ms, k in recs:  # asc
        if t_ms <= entry_ts_ms:
            best_t, best_k = t_ms, k
        else:
            break
    if best_t is None:
        return None
    if entry_ts_ms - best_t > max_gap_ms:
        return None
    return best_k


# --- I/O de trade_history (mismo esquema posicional tolerante que health_monitor) ---
CSV_COLUMNS = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
               'size_usdt', 'pnl_pct', 'pnl_usdt', 'funding_paid',
               'reason_exit', 'flag', 'entry_timestamp_ms', 'cluster']


def _read_rows(path: Path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        rows = []
        for line in f:
            parts = line.rstrip("\n").split(",")
            while len(parts) < len(CSV_COLUMNS):
                parts.append("")
            rows.append(parts[:len(CSV_COLUMNS)])
    return header, rows


def main():
    ap = argparse.ArgumentParser(description="Backfill cluster en trade_history desde SIGNALS_RAW")
    ap.add_argument("--trade-log", default="trade_history.csv")
    ap.add_argument("--logs-glob", default="logs/engine.log*",
                    help="glob de logs (engine.log + rotados .gz)")
    ap.add_argument("--apply", action="store_true", help="escribir (default dry-run)")
    ap.add_argument("--max-gap-hours", type=float, default=2.0)
    args = ap.parse_args()

    import glob
    log_paths = sorted(glob.glob(args.logs_glob))
    index = build_signal_index(log_paths)
    max_gap_ms = int(args.max_gap_hours * 3600 * 1000)

    path = Path(args.trade_log)
    header, rows = _read_rows(path)
    i_sym = CSV_COLUMNS.index("symbol")
    i_ets = CSV_COLUMNS.index("entry_timestamp_ms")
    i_clu = CSV_COLUMNS.index("cluster")

    matched = unmatched = already = 0
    dist: dict = {}
    spot = []
    for r in rows:
        if r[i_clu].strip():  # ya etiquetado
            already += 1
            continue
        try:
            ets = int(r[i_ets]) if r[i_ets].strip() else 0
        except ValueError:
            ets = 0
        k = match_cluster(index, r[i_sym], ets, max_gap_ms)
        if k is None:
            unmatched += 1
        else:
            r[i_clu] = str(k)
            matched += 1
            dist[k] = dist.get(k, 0) + 1
            if len(spot) < 5:
                spot.append((r[0], r[i_sym], ets, k))

    print(f"Logs: {len(log_paths)} archivos, {sum(len(v) for v in index.values())} registros SIGNALS_RAW")
    print(f"Trades: {len(rows)} | ya etiquetados: {already} | matched: {matched} | unmatched (NULL): {unmatched}")
    print(f"Distribución cluster: {dict(sorted(dist.items()))}")
    print("Spot-check (timestamp, símbolo, entry_ms, k):")
    for s in spot:
        print(f"  {s}")

    if args.apply and matched > 0:
        bak = path.with_suffix(path.suffix + ".bak-pre-backfill")
        bak.write_bytes(path.read_bytes())
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(header if header.endswith("\n") else header + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")
        print(f"APLICADO. Backup: {bak.name}")
    else:
        print("DRY-RUN (sin --apply o 0 matches).")


if __name__ == "__main__":
    main()
