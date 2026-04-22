"""
funding_observability.py — §13.3 "Observabilidad funding extremo per-trade".

Enriquece el trade_history.csv con 3 columnas para análisis crowd-direction:
  - funding_rate_at_entry: tasa vigente (más reciente settled <= entry_ts) en decimal por período 8h.
  - funding_crowd_direction: 'long_crowd' (rate > +5e-5) | 'short_crowd' (rate < -5e-5) | 'neutral'.
  - signal_vs_crowd: 'aligned' | 'contrarian' | 'neutral'.

Convención BingX / ccxt (confirmada vía data_feed.get_funding_rate):
  fundingRate = tasa decimal por período de 8h.
  Positivo → longs PAGAN / shorts RECIBEN (crowd long dominante).
  Negativo → longs RECIBEN / shorts PAGAN (crowd short dominante).

Fetch bypassa el bug §13.3 E1 (execution_manager._get_position_funding fallback
con signo invertido) usando ccxt.fetch_funding_rate_history directo.

Uso:
    python funding_observability.py <trade_history.csv> [--since-ts YYYY-MM-DD]
        [--output-csv OUT.csv] [--output-report REPORT.txt]

Escribe CSV enriquecido + reporte aligned/contrarian con stats.

Generado 2026-04-22 como parte del prerequisito §13.3 a v2.6 Funding Filter.
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

# Windows console default cp1252 rompe caracteres UTF-8 (§, ±, —) en print.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np
import pandas as pd

try:
    import ccxt.async_support as ccxt_async
except ImportError:
    import ccxt as _ccxt_sync  # fallback si async no disponible
    ccxt_async = None

NEUTRAL_THRESHOLD = 5e-5                 # |rate| < 0.005% per 8h → neutral.
V2_3_11_TS = pd.Timestamp("2026-04-19 17:51:00", tz="UTC")
THEORETIC_EXTREME = 1e-3                 # §9.3 "+0.1%/8h = crowding extremo".


@dataclass
class Trade:
    timestamp: pd.Timestamp
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size_usdt: float
    pnl_pct: float
    pnl_usdt: float
    funding_paid: float
    reason_exit: str
    flag: str
    entry_timestamp_ms: int  # 0 si legacy.
    # Campos enriquecidos:
    funding_rate_at_entry: float | None = None
    funding_crowd_direction: str | None = None
    signal_vs_crowd: str | None = None


def parse_trade_row(row: list[str]) -> Trade | None:
    try:
        ts = pd.Timestamp(row[0]).tz_localize("UTC") if pd.Timestamp(row[0]).tz is None else pd.Timestamp(row[0])
        flag = row[10] if len(row) >= 11 else ""
        etm_raw = row[11] if len(row) >= 12 else "0"
        etm = int(etm_raw) if etm_raw and etm_raw.strip() else 0
        return Trade(
            timestamp=ts,
            symbol=row[1],
            side=row[2].lower(),
            entry_price=float(row[3]),
            exit_price=float(row[4]),
            size_usdt=float(row[5]) if row[5] else 0.0,
            pnl_pct=float(row[6]),
            pnl_usdt=float(row[7]),
            funding_paid=float(row[8]) if row[8] else 0.0,
            reason_exit=row[9],
            flag=flag,
            entry_timestamp_ms=etm,
        )
    except Exception as e:
        print(f"  [WARN] parse failed for row: {row[:3]}... ({type(e).__name__}: {e})")
        return None


def effective_entry_ts(tr: Trade) -> pd.Timestamp:
    """Timestamp más preciso para lookup del rate."""
    if tr.entry_timestamp_ms > 0:
        return pd.Timestamp(tr.entry_timestamp_ms, unit="ms", tz="UTC")
    return tr.timestamp


async def fetch_all_funding_rates(
    symbols: Iterable[str],
    since_ts: pd.Timestamp,
    until_ts: pd.Timestamp,
    exchange_id: str = "binance",
) -> dict[str, list[dict]]:
    """
    Por cada símbolo, fetch completo de funding rate history entre since y until.
    Retorna dict {symbol: [{'timestamp': ms, 'rate': float, 'datetime': iso}, ...]}.

    Exchange default Binance: (a) accesible global (BingX geo-bloquea endpoint
    /quote/contracts desde clientes fuera de Asia, incluido Windows local);
    (b) funding rates Binance y BingX correlacionan >95% para majors (instrumentos
    perpetuos competitivos tienden a converger en arbitraje). Proxy aceptable
    para análisis direccional aligned vs contrarian.

    Caveat: magnitudes absolutas pueden diverger; para decisión de threshold
    operacional final habría que re-fetch desde BingX (ejecutable en VPS).
    """
    if ccxt_async is None:
        raise RuntimeError("ccxt.async_support no disponible")

    if exchange_id == "bingx":
        exchange = ccxt_async.bingx({"options": {"defaultType": "swap"}, "enableRateLimit": True})
    else:
        exchange = ccxt_async.binance({"options": {"defaultType": "future"}, "enableRateLimit": True})

    since_ms = int(since_ts.timestamp() * 1000)
    # Some exchanges require "until"; ccxt BingX ignora y retorna secuencia desde since.
    result: dict[str, list[dict]] = {}
    try:
        for sym in sorted(set(symbols)):
            # Binance perpetual futures y BingX swap usan formato ccxt "BTC/USDT:USDT";
            # pasar "BTC/USDT" devuelve 0 rates silently (no error). Patrón Lección §12.24.
            fetch_sym = f"{sym}:USDT" if exchange_id in ("binance", "bingx") else sym
            rates: list[dict] = []
            offset_since = since_ms
            attempt = 0
            while True:
                try:
                    batch = await exchange.fetch_funding_rate_history(fetch_sym, since=offset_since, limit=1000)
                except Exception as e:
                    attempt += 1
                    if attempt >= 3:
                        print(f"  [ERROR] {sym}: fetch failed after 3 retries: {type(e).__name__}: {e}")
                        break
                    await asyncio.sleep(1.0 * attempt)
                    continue
                if not batch:
                    break
                rates.extend([{
                    "timestamp": int(b.get("timestamp") or 0),
                    "rate": float(b.get("fundingRate") or 0.0),
                    "datetime": b.get("datetime"),
                } for b in batch if b.get("timestamp")])
                last_ts = batch[-1].get("timestamp")
                if last_ts is None or len(batch) < 1000 or last_ts >= int(until_ts.timestamp() * 1000):
                    break
                offset_since = last_ts + 1
                attempt = 0
                await asyncio.sleep(0.2)  # cortesía rate limit.

            rates = [r for r in rates if r["timestamp"] <= int(until_ts.timestamp() * 1000) + 8 * 3600 * 1000]
            rates.sort(key=lambda r: r["timestamp"])
            result[sym] = rates
            print(f"  [FETCH] {sym}: {len(rates)} rates ({rates[0]['datetime'] if rates else 'empty'} .. {rates[-1]['datetime'] if rates else '-'})")
    finally:
        await exchange.close()
    return result


def lookup_rate_at(rates: list[dict], entry_ms: int) -> float | None:
    """Retorna el rate settled más reciente con timestamp <= entry_ms."""
    if not rates:
        return None
    # Binary search.
    lo, hi = 0, len(rates) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if rates[mid]["timestamp"] <= entry_ms:
            best = rates[mid]["rate"]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def classify(tr: Trade) -> None:
    r = tr.funding_rate_at_entry
    if r is None or math.isnan(r):
        tr.funding_crowd_direction = "unknown"
        tr.signal_vs_crowd = "unknown"
        return
    if abs(r) < NEUTRAL_THRESHOLD:
        tr.funding_crowd_direction = "neutral"
        tr.signal_vs_crowd = "neutral"
        return
    crowd = "long_crowd" if r > 0 else "short_crowd"
    tr.funding_crowd_direction = crowd
    if tr.side == "long" and crowd == "long_crowd":
        tr.signal_vs_crowd = "aligned"
    elif tr.side == "short" and crowd == "short_crowd":
        tr.signal_vs_crowd = "aligned"
    else:
        tr.signal_vs_crowd = "contrarian"


def welch_t_test(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Welch t-test, retorna (t, p aproximada 2-sided por normal approx)."""
    if len(xs) < 2 or len(ys) < 2:
        return (0.0, 1.0)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    vx, vy = statistics.variance(xs), statistics.variance(ys)
    se = math.sqrt(vx / len(xs) + vy / len(ys))
    if se == 0:
        return (0.0, 1.0)
    t = (mx - my) / se
    # Aproximación 2-sided con normal (N>20 adecuado).
    from math import erf, sqrt
    z = abs(t)
    p = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
    return (t, p)


def mann_whitney_u(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Mann-Whitney U con aproximación normal."""
    if not xs or not ys:
        return (0.0, 1.0)
    combined = [(v, "x") for v in xs] + [(v, "y") for v in ys]
    combined.sort(key=lambda t: t[0])
    # Rank con ties medios.
    ranks: list[float] = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 2) / 2.0  # ranks base-1.
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


def percentiles(xs: list[float]) -> dict[str, float]:
    if not xs:
        return {"p25": float("nan"), "p50": float("nan"), "p75": float("nan"),
                "p95": float("nan"), "p99": float("nan")}
    arr = np.asarray(xs, dtype=float)
    return {
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
    }


def build_report(trades: list[Trade]) -> str:
    lines: list[str] = []
    out = lines.append

    enriched = [t for t in trades if t.signal_vs_crowd and t.signal_vs_crowd != "unknown"]
    unknown = [t for t in trades if t.signal_vs_crowd == "unknown" or t.signal_vs_crowd is None]
    by_cat: dict[str, list[Trade]] = {"aligned": [], "contrarian": [], "neutral": []}
    for t in enriched:
        by_cat.setdefault(t.signal_vs_crowd, []).append(t)

    N = len(enriched)
    out("=" * 70)
    out("FUNDING CROWD OBSERVABILITY REPORT — §13.3 prerequisito v2.6 filter")
    out("=" * 70)
    out(f"Trades enriquecidos: {N}  (unknown funding rate: {len(unknown)})")
    out(f"Convención: rate > +{NEUTRAL_THRESHOLD:.0e} → long_crowd (longs PAGAN);")
    out(f"            rate < -{NEUTRAL_THRESHOLD:.0e} → short_crowd (shorts PAGAN);")
    out(f"            |rate| < threshold → neutral.")
    out(f"Threshold §9.3 extremo: |rate| > {THEORETIC_EXTREME:.0e} (0.1% per 8h).")
    out("")

    if N == 0:
        out("Sin trades enriquecidos. No hay análisis.")
        return "\n".join(lines)

    # Tabla distribución + PnL por grupo.
    out("Distribución y PnL por grupo:")
    out(f"{'group':<12} {'N':>5} {'%':>6} {'mean_pnl_%':>12} {'median_pnl_%':>14} {'std_pnl_%':>12} {'sum_pnl_USDT':>14} {'mean_fr_%':>12}")
    out("-" * 100)
    for cat in ("aligned", "contrarian", "neutral"):
        tr = by_cat.get(cat, [])
        n = len(tr)
        pct = 100 * n / N if N else 0
        if n == 0:
            out(f"{cat:<12} {n:>5} {pct:>5.1f}% {'-':>12} {'-':>14} {'-':>12} {'-':>14} {'-':>12}")
            continue
        pnls = [t.pnl_pct for t in tr]
        pnls_usdt = [t.pnl_usdt for t in tr]
        rates = [t.funding_rate_at_entry for t in tr if t.funding_rate_at_entry is not None]
        mean_p = statistics.mean(pnls)
        med_p = statistics.median(pnls)
        std_p = statistics.stdev(pnls) if n > 1 else 0.0
        sum_u = sum(pnls_usdt)
        mean_r = statistics.mean(rates) * 100 if rates else float("nan")  # como %.
        out(f"{cat:<12} {n:>5} {pct:>5.1f}% {mean_p:>+12.4f} {med_p:>+14.4f} {std_p:>12.4f} {sum_u:>+14.4f} {mean_r:>+12.5f}")

    out("")

    # Tests estadísticos aligned vs contrarian.
    aligned_pnls = [t.pnl_pct for t in by_cat.get("aligned", [])]
    contrarian_pnls = [t.pnl_pct for t in by_cat.get("contrarian", [])]
    if aligned_pnls and contrarian_pnls:
        t_stat, t_p = welch_t_test(aligned_pnls, contrarian_pnls)
        u_stat, u_p = mann_whitney_u(aligned_pnls, contrarian_pnls)
        out("Tests estadísticos aligned vs contrarian (PnL %):")
        out(f"  Welch t-test:   t={t_stat:+.4f}  p={t_p:.4f}  (N_a={len(aligned_pnls)}, N_c={len(contrarian_pnls)})")
        out(f"  Mann-Whitney U: U={u_stat:.1f}  p={u_p:.4f}")
        if t_p < 0.05:
            out(f"  -> p < 0.05: diferencia estadísticamente significativa.")
        else:
            out(f"  -> p >= 0.05: no se rechaza H0 (no evidencia de diff). N posiblemente insuficiente.")
        out("")

    # Funding rate distribution.
    all_rates = [t.funding_rate_at_entry for t in enriched if t.funding_rate_at_entry is not None]
    pct = percentiles(all_rates)
    abs_pct = percentiles([abs(r) for r in all_rates])
    out("Funding rate at entry — distribución absoluta (decimal per 8h):")
    out(f"  p25 = {pct['p25']:+.6f}  p50 = {pct['p50']:+.6f}  p75 = {pct['p75']:+.6f}")
    out(f"  p95 = {pct['p95']:+.6f}  p99 = {pct['p99']:+.6f}")
    out(f"  |rate|: p75 = {abs_pct['p75']:.6f}  p95 = {abs_pct['p95']:.6f}  p99 = {abs_pct['p99']:.6f}")
    out(f"  Trades con |rate| > {THEORETIC_EXTREME} (§9.3 extremo): "
        f"{sum(1 for r in all_rates if abs(r) > THEORETIC_EXTREME)} / {len(all_rates)}")
    out("")

    # Threshold analysis §9.3.
    threshold = THEORETIC_EXTREME
    blocked = [t for t in enriched if (t.funding_rate_at_entry is not None
                                        and abs(t.funding_rate_at_entry) > threshold
                                        and t.signal_vs_crowd == "aligned")]
    permitted = [t for t in enriched if t not in blocked]
    out(f"Simulación filtro §9.3 threshold |rate| > {threshold}:")
    out(f"  Trades BLOCKED (aligned + extremo): {len(blocked)} / {N} ({100*len(blocked)/N:.1f}%)")
    if blocked:
        b_mean = statistics.mean(t.pnl_pct for t in blocked)
        b_sum_usdt = sum(t.pnl_usdt for t in blocked)
        out(f"    PnL mean de blocked (lo que se 'habría ahorrado'): {b_mean:+.4f}% / sum {b_sum_usdt:+.4f} USDT")
    if permitted:
        p_mean = statistics.mean(t.pnl_pct for t in permitted)
        p_sum_usdt = sum(t.pnl_usdt for t in permitted)
        out(f"    PnL mean de permitted: {p_mean:+.4f}% / sum {p_sum_usdt:+.4f} USDT")
    out("")

    # Symbol breakdown.
    sym_map: dict[str, dict[str, Any]] = {}
    for t in enriched:
        sr = sym_map.setdefault(t.symbol, {"N": 0, "aligned": 0, "contrarian": 0, "neutral": 0,
                                             "pnl": 0.0, "rates": []})
        sr["N"] += 1
        sr[t.signal_vs_crowd] = sr.get(t.signal_vs_crowd, 0) + 1
        sr["pnl"] += t.pnl_usdt
        if t.funding_rate_at_entry is not None:
            sr["rates"].append(t.funding_rate_at_entry)
    out("Breakdown por símbolo (top 10 por N):")
    out(f"{'symbol':<15} {'N':>4} {'aligned':>8} {'contrarian':>11} {'neutral':>8} {'sum_pnl':>10} {'mean_rate':>12}")
    out("-" * 80)
    for sym in sorted(sym_map, key=lambda s: -sym_map[s]["N"])[:10]:
        sr = sym_map[sym]
        mr = statistics.mean(sr["rates"]) if sr["rates"] else float("nan")
        out(f"{sym:<15} {sr['N']:>4} {sr.get('aligned', 0):>8} {sr.get('contrarian', 0):>11} "
            f"{sr.get('neutral', 0):>8} {sr['pnl']:>+10.4f} {mr:>+12.6f}")

    out("")
    out("=" * 70)

    # Interpretación final — 4 casos.
    if aligned_pnls and contrarian_pnls:
        t_stat, t_p = welch_t_test(aligned_pnls, contrarian_pnls)
        mean_a = statistics.mean(aligned_pnls)
        mean_c = statistics.mean(contrarian_pnls)
        if t_p < 0.05 and mean_a < mean_c:
            verdict = ("CASO MATERIAL (hipótesis v2.6 CONFIRMADA): aligned PnL signif. peor que contrarian "
                       f"(p={t_p:.4f}, diff {mean_a-mean_c:+.4f}%). Justificaría v2.6 filter que bloquee aligned.")
        elif t_p < 0.05 and mean_a > mean_c:
            verdict = ("CASO MATERIAL INVERSO (hipótesis v2.6 REFUTADA): aligned PnL signif. MEJOR que contrarian "
                       f"(p={t_p:.4f}, diff {mean_a-mean_c:+.4f}%). Recomendar ARCHIVAR v2.6 contrarian filter; "
                       "considerar 'momentum' filter (bloquear contrarian) como item separado pendiente N>100.")
        elif abs(mean_a - mean_c) < 0.1 and t_p >= 0.5:
            verdict = "CASO NULL: sin evidencia diff (p>=0.5, magnitud <0.1%). Recomendar archivar v2.6 o esperar N>>50."
        else:
            verdict = f"CASO MARGINAL: p={t_p:.3f}, diff means {mean_a-mean_c:+.4f}%. Insuficiente; acumular más data."
    else:
        verdict = "Sin ambos grupos aligned+contrarian. Recomendar acumular más trades."
    out(f"VEREDICTO: {verdict}")
    out("=" * 70)

    return "\n".join(lines)


async def main_async(args: argparse.Namespace) -> int:
    # Load CSV.
    trades: list[Trade] = []
    with open(args.csv) as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if not row:
                continue
            t = parse_trade_row(row)
            if t is not None:
                trades.append(t)

    print(f"Loaded {len(trades)} trades from {args.csv}")

    # Filter post-v2.3.11 by default + exclude reconstructed.
    since_ts = pd.Timestamp(args.since_ts).tz_localize("UTC") if args.since_ts else V2_3_11_TS
    filt = [t for t in trades if t.timestamp >= since_ts and t.flag not in ("reconstructed", "reconstructed_post_hoc")]
    print(f"Filtered post-{since_ts} excluding reconstructed: {len(filt)} trades")

    if not filt:
        print("No trades to analyze.")
        return 1

    # Fetch funding rate histories.
    symbols = [t.symbol for t in filt]
    min_ts = min(effective_entry_ts(t) for t in filt) - pd.Timedelta(hours=16)
    max_ts = max(effective_entry_ts(t) for t in filt) + pd.Timedelta(hours=16)
    print(f"Fetching funding rates for {len(set(symbols))} symbols from {min_ts} to {max_ts} via {args.exchange}")
    t_fetch = time.time()
    rates_by_sym = await fetch_all_funding_rates(symbols, min_ts, max_ts, exchange_id=args.exchange)
    print(f"Fetch complete in {time.time()-t_fetch:.1f}s")

    # Enrich.
    for t in filt:
        entry_ms = int(effective_entry_ts(t).timestamp() * 1000)
        rates = rates_by_sym.get(t.symbol, [])
        t.funding_rate_at_entry = lookup_rate_at(rates, entry_ms)
        classify(t)

    # Write enriched CSV.
    out_csv = args.output_csv or args.csv.replace(".csv", "_funding_obs.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "symbol", "side", "entry_price", "exit_price", "size_usdt",
                    "pnl_pct", "pnl_usdt", "funding_paid", "reason_exit", "flag", "entry_timestamp_ms",
                    "funding_rate_at_entry", "funding_crowd_direction", "signal_vs_crowd"])
        for t in filt:
            w.writerow([t.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], t.symbol, t.side,
                        t.entry_price, t.exit_price, t.size_usdt, t.pnl_pct, t.pnl_usdt,
                        t.funding_paid, t.reason_exit, t.flag, t.entry_timestamp_ms,
                        t.funding_rate_at_entry if t.funding_rate_at_entry is not None else "",
                        t.funding_crowd_direction or "",
                        t.signal_vs_crowd or ""])
    print(f"Wrote enriched CSV -> {out_csv}")

    # Build + print + write report.
    report = build_report(filt)
    print("\n" + report)

    if args.output_report:
        with open(args.output_report, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nReport saved -> {args.output_report}")

    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Path a trade_history.csv")
    p.add_argument("--since-ts", default=None, help="Filtro timestamp desde (UTC). Default: v2.3.11 deploy 2026-04-19 17:51.")
    p.add_argument("--output-csv", default=None)
    p.add_argument("--output-report", default=None)
    p.add_argument("--exchange", default="binance", choices=["binance", "bingx"],
                   help="Exchange proxy para funding rates. Default binance (accesible global).")
    args = p.parse_args()

    if ccxt_async is None:
        print("ERROR: ccxt.async_support no disponible. Instala con `pip install ccxt`.")
        return 1

    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
