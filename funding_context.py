"""
funding_context.py — observabilidad funding bar-a-bar + exit context.

Reemplaza `funding_observability.py` (Bloque 2, entry-only) con solución
definitiva permanente: 11 columnas enriquecimiento + 9-pattern trajectory,
cache parquet por símbolo, ejecutable como librería (importado por el
analyzer) o CLI standalone.

Data model (añadido a cada trade):

Entry context:
  - funding_rate_at_entry         (decimal per 8h)
  - funding_crowd_direction_entry ('long_crowd' | 'short_crowd' | 'neutral')
  - signal_vs_entry_crowd         ('aligned' | 'contrarian' | 'neutral')

Exit context:
  - funding_rate_at_exit
  - funding_crowd_direction_exit
  - position_vs_exit_crowd

Evolution during trade (significativo solo cruzando funding boundaries 8h):
  - funding_rate_min_during
  - funding_rate_max_during
  - funding_rate_mean_during
  - funding_crowd_flipped  (bool: crowd cambió sign entre entry y exit)
  - n_bars_contrarian       (bars con position contra el crowd vigente)
  - max_consecutive_bars_contrarian

Derived:
  - entry_exit_pattern (9 combos: e.g. "aligned->aligned", "aligned->contrarian", ...)

Convención:
  rate > +5e-5 → long_crowd (longs pagan / shorts reciben).
  rate < -5e-5 → short_crowd.
  |rate| < 5e-5 → neutral.

Fetch via ccxt BingX. Geo-bloqueo España (§12.24) obliga ejecutar
`refresh-cache` desde VPS Tokyo; cache parquet rsync a local para analyzer.

CLI:
  # VPS Tokyo (fetch):
  python funding_context.py refresh-cache --symbols BTC/USDT,... \
    --since 2026-04-01 --cache-dir .funding_cache/

  # Local Spain (enrich CSV standalone):
  python funding_context.py enrich /path/to/trade_history.csv \
    --cache-dir .funding_cache/ --output enriched.csv --output-report report.txt

Uso como librería (analyzer integration):
  from funding_context import enrich_trades, FundingCache
  cache = FundingCache(".funding_cache/")
  enrich_trades(trades_list, cache)  # muta in-place, añade columnas.

Sustituye funding_observability.py (Bloque 2 entry-only, refutó §9.3 v2.6
contrarian hipótesis). Ver §13.4 entrada 2026-04-22 para contexto.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import math
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import ccxt.async_support as ccxt_async
except ImportError:
    ccxt_async = None

# Thresholds / constants.
NEUTRAL_THRESHOLD = 5e-5
V2_3_11_TS = pd.Timestamp("2026-04-19 17:51:00", tz="UTC")
FUNDING_PERIOD_HOURS = 8

# ==============================================================
# Cache
# ==============================================================

class FundingCache:
    """Cache funding rate history as CSV per symbol in a directory.

    File layout: cache_dir/<SYM_KEY>.csv with columns:
      timestamp (int64 ms UTC), rate (float64), datetime (str ISO).

    symbol 'BTC/USDT' → key 'BTCUSDT'.

    Formato CSV elegido sobre parquet para evitar dependencia pyarrow
    no disponible en VPS sin instalación adicional. Volumen pequeño
    (100-500 rates por símbolo × 45 símbolos ≈ <100 KB total).
    """

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, symbol: str) -> str:
        key = symbol.replace("/", "").replace(":USDT", "")
        return os.path.join(self.cache_dir, f"{key}.csv")

    def load(self, symbol: str) -> pd.DataFrame:
        p = self._path(symbol)
        if not os.path.exists(p):
            return pd.DataFrame(columns=["timestamp", "rate", "datetime"]).astype(
                {"timestamp": "int64", "rate": "float64", "datetime": "object"})
        df = pd.read_csv(p)
        if not df.empty:
            df["timestamp"] = df["timestamp"].astype("int64")
            df["rate"] = df["rate"].astype("float64")
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def save(self, symbol: str, df: pd.DataFrame) -> None:
        p = self._path(symbol)
        df2 = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
        df2.to_csv(p, index=False)

    def coverage(self, symbol: str) -> tuple[int | None, int | None]:
        df = self.load(symbol)
        if df.empty:
            return None, None
        return int(df["timestamp"].min()), int(df["timestamp"].max())

    def symbols_cached(self) -> list[str]:
        if not os.path.isdir(self.cache_dir):
            return []
        out = []
        for f in os.listdir(self.cache_dir):
            if f.endswith(".csv"):
                out.append(f[:-len(".csv")])
        return out


# ==============================================================
# Fetch (BingX via ccxt)
# ==============================================================

async def fetch_funding_rates(
    symbol: str,
    since_ms: int,
    until_ms: int,
    exchange_id: str = "bingx",
) -> pd.DataFrame:
    """Fetch funding rate history via ccxt.

    Returns DataFrame with columns [timestamp, rate, datetime] ordered by ts.
    Symbol 'BTC/USDT' resolved to 'BTC/USDT:USDT' (BingX swap / Binance perp).
    """
    if ccxt_async is None:
        raise RuntimeError("ccxt.async_support no disponible (pip install ccxt)")

    if exchange_id == "bingx":
        ex = ccxt_async.bingx({"options": {"defaultType": "swap"}, "enableRateLimit": True})
    elif exchange_id == "binance":
        ex = ccxt_async.binance({"options": {"defaultType": "future"}, "enableRateLimit": True})
    else:
        raise ValueError(f"Unsupported exchange: {exchange_id}")

    fetch_sym = f"{symbol}:USDT" if ":USDT" not in symbol else symbol

    rates: list[dict] = []
    offset_since = since_ms
    attempt = 0
    try:
        while True:
            try:
                batch = await ex.fetch_funding_rate_history(fetch_sym, since=offset_since, limit=1000)
            except Exception as e:
                attempt += 1
                if attempt >= 3:
                    raise RuntimeError(f"fetch {symbol} failed after 3 retries: {type(e).__name__}: {e}")
                await asyncio.sleep(1.0 * attempt)
                continue
            if not batch:
                break
            for b in batch:
                ts = int(b.get("timestamp") or 0)
                if ts <= 0:
                    continue
                rates.append({
                    "timestamp": ts,
                    "rate": float(b.get("fundingRate") or 0.0),
                    "datetime": b.get("datetime") or pd.Timestamp(ts, unit="ms", tz="UTC").isoformat(),
                })
            last_ts = batch[-1].get("timestamp")
            if last_ts is None or len(batch) < 1000 or last_ts >= until_ms:
                break
            offset_since = last_ts + 1
            attempt = 0
            await asyncio.sleep(0.2)
    finally:
        await ex.close()

    df = pd.DataFrame(rates)
    if not df.empty:
        df = df[df["timestamp"] <= until_ms + FUNDING_PERIOD_HOURS * 3600 * 1000]
        df = df.sort_values("timestamp").reset_index(drop=True)
    return df


async def refresh_cache(
    symbols: Iterable[str],
    since_ts: pd.Timestamp,
    until_ts: pd.Timestamp,
    cache: FundingCache,
    exchange_id: str = "bingx",
    force_refresh: bool = False,
) -> dict[str, int]:
    """For each symbol, fetch funding rates in [since, until] and merge into cache.

    If force_refresh=False, only fetch gap between cache_max and until_ts.
    Returns dict {symbol: n_rates_total_in_cache}.
    """
    since_ms = int(since_ts.timestamp() * 1000)
    until_ms = int(until_ts.timestamp() * 1000)
    counts: dict[str, int] = {}
    for sym in sorted(set(symbols)):
        cache_min, cache_max = cache.coverage(sym)
        if not force_refresh and cache_min is not None and cache_min <= since_ms and cache_max >= until_ms:
            counts[sym] = len(cache.load(sym))
            continue
        fetch_since = since_ms if (force_refresh or cache_max is None) else cache_max + 1
        new = await fetch_funding_rates(sym, fetch_since, until_ms, exchange_id=exchange_id)
        existing = cache.load(sym)
        if new.empty and existing.empty:
            counts[sym] = 0
            continue
        merged = pd.concat([existing, new], ignore_index=True) if not existing.empty else new
        merged = merged.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        cache.save(sym, merged)
        counts[sym] = len(merged)
    return counts


# ==============================================================
# Lookup / evolution
# ==============================================================

def lookup_rate_at(rates: pd.DataFrame, ts_ms: int) -> float | None:
    """Most recent settled rate with timestamp <= ts_ms."""
    if rates is None or rates.empty:
        return None
    ts_arr = rates["timestamp"].values
    idx = int(np.searchsorted(ts_arr, ts_ms, side="right")) - 1
    if idx < 0:
        return None
    return float(rates["rate"].iloc[idx])


def classify_crowd(rate: float | None) -> str:
    if rate is None or (isinstance(rate, float) and math.isnan(rate)):
        return "unknown"
    if abs(rate) < NEUTRAL_THRESHOLD:
        return "neutral"
    return "long_crowd" if rate > 0 else "short_crowd"


def classify_position_vs_crowd(side: str, crowd: str) -> str:
    if crowd in ("neutral", "unknown"):
        return "neutral" if crowd == "neutral" else "unknown"
    if side == "long" and crowd == "long_crowd":
        return "aligned"
    if side == "short" and crowd == "short_crowd":
        return "aligned"
    return "contrarian"


def compute_bar_level_evolution(
    rates: pd.DataFrame,
    entry_ts_ms: int,
    exit_ts_ms: int,
    side: str,
) -> dict[str, Any]:
    """Walk each hourly bar from entry to exit; at each hour, the applicable
    funding rate is `lookup_rate_at(t)` (most recent settled ≤ t).

    Returns 6 evolution stats:
      funding_rate_min/max/mean_during (floats or NaN),
      funding_crowd_flipped (bool),
      n_bars_contrarian, max_consecutive_bars_contrarian (ints).

    Assumes 1h bars. If exit_ts <= entry_ts+1h, evolution is trivial (1 bar).
    """
    out = {
        "funding_rate_min_during": None,
        "funding_rate_max_during": None,
        "funding_rate_mean_during": None,
        "funding_crowd_flipped": False,
        "n_bars_contrarian": 0,
        "max_consecutive_bars_contrarian": 0,
    }
    if rates is None or rates.empty:
        return out
    if exit_ts_ms <= entry_ts_ms:
        exit_ts_ms = entry_ts_ms + 3600 * 1000  # mínimo 1 bar.

    bars: list[int] = []
    t = entry_ts_ms
    while t <= exit_ts_ms:
        bars.append(t)
        t += 3600 * 1000
    if not bars:
        return out

    bar_rates: list[float] = []
    bar_crowds: list[str] = []
    bar_contrarian: list[bool] = []
    for ts in bars:
        r = lookup_rate_at(rates, ts)
        if r is None:
            continue
        bar_rates.append(r)
        crowd = classify_crowd(r)
        bar_crowds.append(crowd)
        status = classify_position_vs_crowd(side, crowd)
        bar_contrarian.append(status == "contrarian")

    if not bar_rates:
        return out

    out["funding_rate_min_during"] = float(min(bar_rates))
    out["funding_rate_max_during"] = float(max(bar_rates))
    out["funding_rate_mean_during"] = float(sum(bar_rates) / len(bar_rates))

    # crowd flipped: ¿cambió entre non-neutral entry crowd y non-neutral exit crowd?
    non_neutral = [c for c in bar_crowds if c in ("long_crowd", "short_crowd")]
    if non_neutral and len(set(non_neutral)) > 1:
        out["funding_crowd_flipped"] = True

    out["n_bars_contrarian"] = sum(bar_contrarian)
    max_run = 0
    cur_run = 0
    for c in bar_contrarian:
        if c:
            cur_run += 1
            if cur_run > max_run:
                max_run = cur_run
        else:
            cur_run = 0
    out["max_consecutive_bars_contrarian"] = max_run
    return out


def compute_pattern(entry_status: str, exit_status: str) -> str:
    """9-combo trajectory label. Uses unknown as sentinel."""
    if entry_status == "unknown" or exit_status == "unknown":
        return "unknown"
    return f"{entry_status}->{exit_status}"


# ==============================================================
# Enrichment
# ==============================================================

@dataclass
class EnrichedTrade:
    # Input fields (assumed populated by caller):
    timestamp: pd.Timestamp   # exit cycle timestamp (from CSV col 0).
    symbol: str
    side: str                 # 'long' | 'short'.
    entry_price: float
    exit_price: float
    size_usdt: float
    pnl_pct: float
    pnl_usdt: float
    funding_paid: float
    reason_exit: str
    flag: str
    entry_timestamp_ms: int   # 0 if not valid.
    entry_ts_ms: int          # resolved entry ms (via entry_timestamp_ms or infer).
    exit_ts_ms: int           # resolved exit ms (timestamp col).
    # Enriched fields (populated by enrich_trade):
    funding_rate_at_entry: float | None = None
    funding_crowd_direction_entry: str | None = None
    signal_vs_entry_crowd: str | None = None
    funding_rate_at_exit: float | None = None
    funding_crowd_direction_exit: str | None = None
    position_vs_exit_crowd: str | None = None
    funding_rate_min_during: float | None = None
    funding_rate_max_during: float | None = None
    funding_rate_mean_during: float | None = None
    funding_crowd_flipped: bool = False
    n_bars_contrarian: int = 0
    max_consecutive_bars_contrarian: int = 0
    entry_exit_pattern: str | None = None


def enrich_trade(tr: EnrichedTrade, rates: pd.DataFrame) -> None:
    """Muta tr in-place con 11 columnas + pattern."""
    r_entry = lookup_rate_at(rates, tr.entry_ts_ms)
    tr.funding_rate_at_entry = r_entry
    entry_crowd = classify_crowd(r_entry)
    tr.funding_crowd_direction_entry = entry_crowd
    tr.signal_vs_entry_crowd = classify_position_vs_crowd(tr.side, entry_crowd)

    r_exit = lookup_rate_at(rates, tr.exit_ts_ms)
    tr.funding_rate_at_exit = r_exit
    exit_crowd = classify_crowd(r_exit)
    tr.funding_crowd_direction_exit = exit_crowd
    tr.position_vs_exit_crowd = classify_position_vs_crowd(tr.side, exit_crowd)

    evo = compute_bar_level_evolution(rates, tr.entry_ts_ms, tr.exit_ts_ms, tr.side)
    tr.funding_rate_min_during = evo["funding_rate_min_during"]
    tr.funding_rate_max_during = evo["funding_rate_max_during"]
    tr.funding_rate_mean_during = evo["funding_rate_mean_during"]
    tr.funding_crowd_flipped = evo["funding_crowd_flipped"]
    tr.n_bars_contrarian = evo["n_bars_contrarian"]
    tr.max_consecutive_bars_contrarian = evo["max_consecutive_bars_contrarian"]

    tr.entry_exit_pattern = compute_pattern(tr.signal_vs_entry_crowd, tr.position_vs_exit_crowd)


def enrich_trades(trades: list[EnrichedTrade], cache: FundingCache) -> None:
    """Enriquecer batch; carga rates por símbolo una vez."""
    by_sym: dict[str, list[EnrichedTrade]] = {}
    for t in trades:
        by_sym.setdefault(t.symbol, []).append(t)
    for sym, tr_list in by_sym.items():
        rates = cache.load(sym)
        for tr in tr_list:
            enrich_trade(tr, rates)


# ==============================================================
# CSV I/O
# ==============================================================

def parse_trade_row(row: list[str]) -> EnrichedTrade | None:
    try:
        ts_str = row[0]
        ts = pd.Timestamp(ts_str)
        if ts.tz is None:
            ts = ts.tz_localize("UTC")
        flag = row[10] if len(row) >= 11 else ""
        etm_raw = row[11] if len(row) >= 12 else "0"
        etm = int(etm_raw) if etm_raw and etm_raw.strip() else 0
        exit_ts_ms = int(ts.timestamp() * 1000)
        # Si entry_timestamp_ms válido → úsalo; else fallback a exit_ts_ms (imperfecto pero
        # operacional para trades con hold times <8h donde rate suele ser idéntico).
        # Analyzer integration puede mejorar con infer_entry_candle del log.
        entry_ts_ms = etm if etm > 0 else exit_ts_ms - 3600 * 1000  # estima 1h hold.
        return EnrichedTrade(
            timestamp=ts, symbol=row[1], side=row[2].lower(),
            entry_price=float(row[3]), exit_price=float(row[4]),
            size_usdt=float(row[5]) if row[5] else 0.0,
            pnl_pct=float(row[6]), pnl_usdt=float(row[7]),
            funding_paid=float(row[8]) if row[8] else 0.0,
            reason_exit=row[9], flag=flag, entry_timestamp_ms=etm,
            entry_ts_ms=entry_ts_ms, exit_ts_ms=exit_ts_ms,
        )
    except Exception as e:
        print(f"  [WARN] parse row failed: {row[:3]}... ({type(e).__name__}: {e})")
        return None


def write_enriched_csv(path: str, trades: list[EnrichedTrade]) -> None:
    header = ["timestamp", "symbol", "side", "entry_price", "exit_price", "size_usdt",
              "pnl_pct", "pnl_usdt", "funding_paid", "reason_exit", "flag", "entry_timestamp_ms",
              "funding_rate_at_entry", "funding_crowd_direction_entry", "signal_vs_entry_crowd",
              "funding_rate_at_exit", "funding_crowd_direction_exit", "position_vs_exit_crowd",
              "funding_rate_min_during", "funding_rate_max_during", "funding_rate_mean_during",
              "funding_crowd_flipped", "n_bars_contrarian", "max_consecutive_bars_contrarian",
              "entry_exit_pattern"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for t in trades:
            w.writerow([t.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], t.symbol, t.side,
                        t.entry_price, t.exit_price, t.size_usdt, t.pnl_pct, t.pnl_usdt,
                        t.funding_paid, t.reason_exit, t.flag, t.entry_timestamp_ms,
                        t.funding_rate_at_entry if t.funding_rate_at_entry is not None else "",
                        t.funding_crowd_direction_entry or "",
                        t.signal_vs_entry_crowd or "",
                        t.funding_rate_at_exit if t.funding_rate_at_exit is not None else "",
                        t.funding_crowd_direction_exit or "",
                        t.position_vs_exit_crowd or "",
                        t.funding_rate_min_during if t.funding_rate_min_during is not None else "",
                        t.funding_rate_max_during if t.funding_rate_max_during is not None else "",
                        t.funding_rate_mean_during if t.funding_rate_mean_during is not None else "",
                        "true" if t.funding_crowd_flipped else "false",
                        t.n_bars_contrarian, t.max_consecutive_bars_contrarian,
                        t.entry_exit_pattern or ""])


# ==============================================================
# Stats helpers
# ==============================================================

def welch_t_test(xs: list[float], ys: list[float]) -> tuple[float, float]:
    if len(xs) < 2 or len(ys) < 2:
        return (0.0, 1.0)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    vx, vy = statistics.variance(xs), statistics.variance(ys)
    se = math.sqrt(vx / len(xs) + vy / len(ys))
    if se == 0:
        return (0.0, 1.0)
    t = (mx - my) / se
    from math import erf, sqrt
    z = abs(t)
    p = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
    return (t, p)


def mann_whitney_u(xs: list[float], ys: list[float]) -> tuple[float, float]:
    if not xs or not ys:
        return (0.0, 1.0)
    combined = [(v, "x") for v in xs] + [(v, "y") for v in ys]
    combined.sort(key=lambda t: t[0])
    ranks: list[float] = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    rx = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == "x")
    nx, ny = len(xs), len(ys)
    u = rx - nx * (nx + 1) / 2.0
    mu = nx * ny / 2.0
    sigma = math.sqrt(nx * ny * (nx + ny + 1) / 12.0)
    if sigma == 0:
        return (u, 1.0)
    z = (u - mu) / sigma
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return (u, p)


def spearman_rho(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Spearman rank correlation with approximate p-value (normal approx)."""
    n = len(xs)
    if n < 3 or n != len(ys):
        return (0.0, 1.0)

    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    mx = statistics.mean(rx)
    my = statistics.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if dx == 0 or dy == 0:
        return (0.0, 1.0)
    rho = num / (dx * dy)
    if abs(rho) >= 1:
        return (rho, 0.0)
    t = rho * math.sqrt((n - 2) / (1 - rho * rho))
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
    return (rho, p)


# ==============================================================
# Report
# ==============================================================

def build_report(trades: list[EnrichedTrade]) -> str:
    lines: list[str] = []
    out = lines.append

    enriched = [t for t in trades if t.signal_vs_entry_crowd and t.signal_vs_entry_crowd != "unknown"]
    N = len(enriched)
    out("=" * 72)
    out("FUNDING CONTEXT REPORT — bar-a-bar trajectory + exit context")
    out("=" * 72)
    out(f"Trades enriched: {N} (unknown entry rate: {len(trades) - N})")
    out(f"Convención: |rate| < {NEUTRAL_THRESHOLD:.0e} → neutral; rate > 0 → long_crowd; rate < 0 → short_crowd.")
    out("")

    if N == 0:
        out("Sin trades enriched; terminar.")
        return "\n".join(lines)

    # ===== Section 1: Entry context (preserved from Bloque 2) =====
    out("-" * 72)
    out("SECTION 1 — Entry crowd (signal_vs_entry_crowd)")
    out("-" * 72)
    by_entry: dict[str, list[EnrichedTrade]] = {}
    for t in enriched:
        by_entry.setdefault(t.signal_vs_entry_crowd, []).append(t)
    out(f"{'group':<12} {'N':>4} {'%':>5} {'mean_pnl_%':>12} {'sum_usdt':>12} {'win_rate':>9}")
    for g in ("aligned", "contrarian", "neutral"):
        trs = by_entry.get(g, [])
        n = len(trs)
        if n == 0:
            out(f"{g:<12} {n:>4} {'-':>5} {'-':>12} {'-':>12} {'-':>9}")
            continue
        pnls = [t.pnl_pct for t in trs]
        u = sum(t.pnl_usdt for t in trs)
        wr = 100 * sum(1 for p in pnls if p > 0) / n
        out(f"{g:<12} {n:>4} {100*n/N:>4.1f}% {statistics.mean(pnls):>+12.4f} {u:>+12.4f} {wr:>8.1f}%")

    al = [t.pnl_pct for t in by_entry.get("aligned", [])]
    co = [t.pnl_pct for t in by_entry.get("contrarian", [])]
    if al and co:
        t_s, t_p = welch_t_test(al, co)
        _, u_p = mann_whitney_u(al, co)
        out(f"  Welch aligned-vs-contrarian: t={t_s:+.3f} p={t_p:.4f}  Mann-Whitney p={u_p:.4f}")
    out("")

    # ===== Section 2: Exit context =====
    out("-" * 72)
    out("SECTION 2 — Exit crowd (position_vs_exit_crowd at close)")
    out("-" * 72)
    by_exit: dict[str, list[EnrichedTrade]] = {}
    for t in enriched:
        g = t.position_vs_exit_crowd or "unknown"
        by_exit.setdefault(g, []).append(t)
    out(f"{'group':<12} {'N':>4} {'%':>5} {'mean_pnl_%':>12} {'sum_usdt':>12} {'win_rate':>9}")
    for g in ("aligned", "contrarian", "neutral", "unknown"):
        trs = by_exit.get(g, [])
        n = len(trs)
        if n == 0:
            continue
        pnls = [t.pnl_pct for t in trs]
        u = sum(t.pnl_usdt for t in trs)
        wr = 100 * sum(1 for p in pnls if p > 0) / n
        out(f"{g:<12} {n:>4} {100*n/N:>4.1f}% {statistics.mean(pnls):>+12.4f} {u:>+12.4f} {wr:>8.1f}%")

    al_e = [t.pnl_pct for t in by_exit.get("aligned", [])]
    co_e = [t.pnl_pct for t in by_exit.get("contrarian", [])]
    if al_e and co_e:
        t_s, t_p = welch_t_test(al_e, co_e)
        _, u_p = mann_whitney_u(al_e, co_e)
        out(f"  Welch exit aligned-vs-contrarian: t={t_s:+.3f} p={t_p:.4f}  Mann-Whitney p={u_p:.4f}")
    out("")

    # ===== Section 3: Trajectory pattern (entry -> exit) =====
    out("-" * 72)
    out("SECTION 3 — Trajectory pattern (entry -> exit), 9 combos")
    out("-" * 72)
    pattern_labels = [f"{a}->{b}" for a in ("aligned", "contrarian", "neutral")
                                  for b in ("aligned", "contrarian", "neutral")]
    by_pat: dict[str, list[EnrichedTrade]] = {}
    for t in enriched:
        by_pat.setdefault(t.entry_exit_pattern or "unknown", []).append(t)
    out(f"{'pattern':<24} {'N':>4} {'%':>5} {'mean_pnl_%':>12} {'sum_usdt':>12} {'win_rate':>9}")
    for pat in pattern_labels:
        trs = by_pat.get(pat, [])
        n = len(trs)
        if n == 0:
            out(f"{pat:<24} {n:>4} {'-':>5} {'-':>12} {'-':>12} {'-':>9}")
            continue
        pnls = [t.pnl_pct for t in trs]
        u = sum(t.pnl_usdt for t in trs)
        wr = 100 * sum(1 for p in pnls if p > 0) / n
        out(f"{pat:<24} {n:>4} {100*n/N:>4.1f}% {statistics.mean(pnls):>+12.4f} {u:>+12.4f} {wr:>8.1f}%")
    out("  CAVEAT: 9 subgrupos con N<50 → CI muy ancho. Descriptivo, no inferencial.")
    out("")

    # ===== Section 4: Crowd flip / duration analysis =====
    out("-" * 72)
    out("SECTION 4 — Crowd flip + contrarian duration")
    out("-" * 72)
    flipped = [t for t in enriched if t.funding_crowd_flipped]
    nonflipped = [t for t in enriched if not t.funding_crowd_flipped]
    out(f"Crowd flipped during trade: {len(flipped)} / {N} ({100*len(flipped)/N:.1f}%)")
    if flipped:
        pnls_f = [t.pnl_pct for t in flipped]
        out(f"  Flipped: mean PnL {statistics.mean(pnls_f):+.4f}% median {statistics.median(pnls_f):+.4f}%"
            f" sum {sum(t.pnl_usdt for t in flipped):+.4f} USDT")
    if nonflipped:
        pnls_nf = [t.pnl_pct for t in nonflipped]
        out(f"  Non-flipped: mean PnL {statistics.mean(pnls_nf):+.4f}% median {statistics.median(pnls_nf):+.4f}%"
            f" sum {sum(t.pnl_usdt for t in nonflipped):+.4f} USDT")
    if flipped and nonflipped:
        t_s, t_p = welch_t_test([t.pnl_pct for t in flipped], [t.pnl_pct for t in nonflipped])
        out(f"  Welch flipped-vs-nonflipped: t={t_s:+.3f} p={t_p:.4f}")

    out("")
    # n_bars_contrarian vs PnL correlation.
    xs = [t.n_bars_contrarian for t in enriched]
    ys = [t.pnl_pct for t in enriched]
    rho, p = spearman_rho([float(x) for x in xs], ys)
    out(f"Spearman ρ(n_bars_contrarian, pnl_pct) = {rho:+.4f}  p={p:.4f}  (N={N})")
    out(f"  Interpretación: ρ negativo = más bars contrarian → peor PnL.")

    xs2 = [t.max_consecutive_bars_contrarian for t in enriched]
    rho2, p2 = spearman_rho([float(x) for x in xs2], ys)
    out(f"Spearman ρ(max_consecutive_contrarian, pnl_pct) = {rho2:+.4f}  p={p2:.4f}  (N={N})")
    out("  CAVEAT: hold times típicos <8h → bars_contrarian a menudo 0; correlación informativa solo si hay trades largos.")
    out("")

    # Hold time summary.
    holds_ms = [t.exit_ts_ms - t.entry_ts_ms for t in enriched]
    holds_hours = [h / 3600000 for h in holds_ms if h > 0]
    if holds_hours:
        out(f"Hold time distribution (h): min={min(holds_hours):.2f} median={statistics.median(holds_hours):.2f} "
            f"max={max(holds_hours):.2f} mean={statistics.mean(holds_hours):.2f}")
        crossed8 = sum(1 for h in holds_hours if h >= 8)
        out(f"Trades crossing >=8h boundary (funding period): {crossed8} / {len(holds_hours)}"
            f" ({100*crossed8/len(holds_hours):.1f}%)")

    out("")
    out("=" * 72)
    out("VEREDICTO descriptivo (caveats N pequeño):")
    if al and co:
        t_s, t_p = welch_t_test(al, co)
        mean_a = statistics.mean(al)
        mean_c = statistics.mean(co)
        if t_p < 0.05 and mean_a > mean_c:
            out(f"  Entry: aligned outperform contrarian (p={t_p:.4f}, diff {mean_a-mean_c:+.4f}%). "
                "Refuta v2.6 contrarian §9.3; soporta candidato v2.6-inv pendiente N>=100.")
        elif t_p < 0.05:
            out(f"  Entry: contrarian outperform aligned (p={t_p:.4f}). Soporta v2.6 contrarian original §9.3.")
        else:
            out(f"  Entry: no diff significativa (p={t_p:.4f}). Acumular N.")
    if al_e and co_e:
        t_s, t_p = welch_t_test(al_e, co_e)
        mean_a = statistics.mean(al_e)
        mean_c = statistics.mean(co_e)
        if t_p < 0.05 and mean_c < mean_a:
            out(f"  Exit: position_vs_exit contrarian pierde (p={t_p:.4f}, diff exit_a-exit_c {mean_a-mean_c:+.4f}%). "
                "Soporta candidato v2.6-exit filter (cerrar contrarian losing).")
        else:
            out(f"  Exit: sin diff significativa (p={t_p:.4f}). Observar con N mayor.")
    out("=" * 72)
    return "\n".join(lines)


# ==============================================================
# CLI
# ==============================================================

async def cmd_refresh_cache(args) -> int:
    cache = FundingCache(args.cache_dir)
    since_ts = pd.Timestamp(args.since).tz_localize("UTC") if args.since else V2_3_11_TS
    until_ts = pd.Timestamp(args.until).tz_localize("UTC") if args.until else pd.Timestamp.now(tz="UTC")
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    elif args.csv:
        with open(args.csv) as f:
            r = csv.reader(f); next(r)
            symbols = sorted({row[1] for row in r if row})
    else:
        print("Error: --symbols o --csv requerido.")
        return 1
    print(f"Refreshing cache {len(symbols)} symbols, {since_ts} .. {until_ts}, exchange={args.exchange}")
    t0 = time.time()
    counts = await refresh_cache(symbols, since_ts, until_ts, cache, exchange_id=args.exchange,
                                   force_refresh=args.force)
    print(f"Done in {time.time()-t0:.1f}s. Cache counts: {sum(counts.values())} total rates across {len(counts)} symbols.")
    for s, n in sorted(counts.items()):
        print(f"  {s}: {n}")
    return 0


def cmd_enrich(args) -> int:
    cache = FundingCache(args.cache_dir)
    with open(args.csv) as f:
        r = csv.reader(f)
        next(r)
        trades: list[EnrichedTrade] = []
        for row in r:
            if not row:
                continue
            t = parse_trade_row(row)
            if t is not None:
                trades.append(t)
    print(f"Loaded {len(trades)} trades from {args.csv}")

    since_ts = pd.Timestamp(args.since).tz_localize("UTC") if args.since else V2_3_11_TS
    filt = [t for t in trades if t.timestamp >= since_ts
            and t.flag not in ("reconstructed", "reconstructed_post_hoc")]
    print(f"Filtered post-{since_ts} + clean: {len(filt)} trades")

    enrich_trades(filt, cache)

    out_csv = args.output or args.csv.replace(".csv", "_funding_enriched.csv")
    write_enriched_csv(out_csv, filt)
    print(f"Enriched CSV -> {out_csv}")

    report = build_report(filt)
    print("\n" + report)
    if args.output_report:
        with open(args.output_report, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Report -> {args.output_report}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="funding_context.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    rp = sub.add_parser("refresh-cache", help="Fetch funding rate history a cache parquet.")
    rp.add_argument("--cache-dir", default=".funding_cache/")
    rp.add_argument("--symbols", default=None, help="Comma list. E.g. 'BTC/USDT,ETH/USDT'.")
    rp.add_argument("--csv", default=None, help="Alternativa: extraer símbolos del CSV.")
    rp.add_argument("--since", default=None, help="ISO date UTC. Default v2.3.11 deploy.")
    rp.add_argument("--until", default=None, help="ISO date UTC. Default now.")
    rp.add_argument("--exchange", default="bingx", choices=["bingx", "binance"])
    rp.add_argument("--force", action="store_true", help="Ignora cache existente.")

    ep = sub.add_parser("enrich", help="Enriquece trade_history CSV usando cache.")
    ep.add_argument("csv")
    ep.add_argument("--cache-dir", default=".funding_cache/")
    ep.add_argument("--since", default=None, help="Filter trades desde ts UTC.")
    ep.add_argument("--output", default=None, help="Enriched CSV path.")
    ep.add_argument("--output-report", default=None)

    args = p.parse_args()

    if args.cmd == "refresh-cache":
        if ccxt_async is None:
            print("Error: ccxt.async_support no disponible.")
            return 1
        return asyncio.run(cmd_refresh_cache(args))
    elif args.cmd == "enrich":
        return cmd_enrich(args)
    else:
        p.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
