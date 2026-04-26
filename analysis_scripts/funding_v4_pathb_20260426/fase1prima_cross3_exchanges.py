"""Fase 1' — Cross-3-exchanges funding coherence + threshold X identification.

Path B-institutional. Reformulación marco: rasgo agregado mercado vs noise local.

Hipótesis principal: existe X tal que rates ≥X muestran direccionalidad
unanimous cross-3 exchanges (Binance + BingX + OKX). X define
"desequilibrio significativo" empírico.

Subset 15 símbolos cross-cap-tier:
  Tier 1 mega-cap (4): BTC, ETH, BNB, SOL.
  Tier 2 large-cap (4): XRP, DOGE, ADA, LINK.
  Tier 3 mid-cap (4): AVAX, DOT, LTC, NEAR.
  Tier 4 small/recientes (3): ONDO, SEI, ENA.

Ventana: 180 días.

Metodología:
  - Fetch funding rates cross-3 exchanges via ccxt (funding_context.fetch_funding_rates).
  - Alinear timestamps cross-3 con tolerance 30 min.
  - Threshold sweep X ∈ {1e-5, 5e-5, 1e-4, 5e-4, 1e-3}.
  - Para cada X: % bars donde sign(r_b)==sign(r_x)==sign(r_o) AND |r_binance|≥X.
  - Cross-régimen breakdown: 3 sub-ventanas 60d.
  - Identificar X crítico: minimum X con unanimidad ≥95% AND N≥50.

Veredicto:
  - CONFIRMA RASGO: X≤1e-4 con ≥95% unanimidad + estable cross-3-subwindows.
  - EXTREMO RARO: X requerido ≥5e-4, N bars ≥X bajo.
  - REFUTA RASGO: ningún X razonable con unanimidad ≥95%.

Ejecutar VPS Tokyo (geo Binance):
  ssh trader@vps "cd combolab && /home/trader/venv/bin/python \\
    analysis_scripts/funding_v4_pathb_20260426/fase1prima_cross3_exchanges.py \\
    --since-days 180 \\
    --out analysis_scripts/funding_v4_pathb_20260426/fase1prima_results.json \\
    --cache-base /tmp/fc_pathb_fase1"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
COMBOLAB_ROOT = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, COMBOLAB_ROOT)

import pandas as pd
import numpy as np

from funding_context import fetch_funding_rates, FundingCache

ALIGN_TOLERANCE_MS = 30 * 60 * 1000  # 30 min cross-exchange timing drift

SYMBOLS_DEFAULT = [
    # Tier 1 mega-cap
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT",
    # Tier 2 large-cap
    "XRP/USDT", "DOGE/USDT", "ADA/USDT", "LINK/USDT",
    # Tier 3 mid-cap
    "AVAX/USDT", "DOT/USDT", "LTC/USDT", "NEAR/USDT",
    # Tier 4 small/recientes
    "ONDO/USDT", "SEI/USDT", "ENA/USDT",
]

THRESHOLDS = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3]


async def fetch_with_cache(symbol: str, since_ms: int, until_ms: int,
                           exchange_id: str, cache: FundingCache) -> pd.DataFrame:
    """Fetch funding rates con cache local. Si cache cubre rango, retorna cached.
    Si gap, fetch incremental."""
    cmin, cmax = cache.coverage(symbol)
    if cmin is not None and cmin <= since_ms and cmax >= until_ms:
        return cache.load(symbol).query(
            f"{since_ms} <= timestamp <= {until_ms}"
        ).reset_index(drop=True)
    # Gap: fetch missing
    fetch_since = since_ms if cmax is None else min(since_ms, cmax + 1)
    try:
        new = await fetch_funding_rates(symbol, fetch_since, until_ms, exchange_id=exchange_id)
    except Exception as e:
        return pd.DataFrame(columns=["timestamp", "rate", "datetime"])
    existing = cache.load(symbol)
    if new.empty and existing.empty:
        return new
    merged = pd.concat([existing, new], ignore_index=True) if not existing.empty else new
    merged = merged.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    cache.save(symbol, merged)
    return merged.query(f"{since_ms} <= timestamp <= {until_ms}").reset_index(drop=True)


def align_3way(df_b: pd.DataFrame, df_x: pd.DataFrame, df_o: pd.DataFrame,
               tol_ms: int = ALIGN_TOLERANCE_MS):
    """Alinea 3 exchanges por timestamp. Retorna 3 arrays alineados."""
    if df_b.empty or df_x.empty or df_o.empty:
        return None
    # Anchor = exchange con menor n (típico Binance 8h vs BingX 4h)
    candidates = [(len(df_b), "binance", df_b), (len(df_x), "bingx", df_x), (len(df_o), "okx", df_o)]
    candidates.sort()
    anchor_n, anchor_id, anchor = candidates[0]
    others = [(c[1], c[2]) for c in candidates[1:]]

    # Build timestamp-indexed series for "other" exchanges
    other_ts = {oid: o["timestamp"].values for oid, o in others}
    other_rate = {oid: o["rate"].values for oid, o in others}

    aligned = {"binance": [], "bingx": [], "okx": []}
    aligned[anchor_id] = []
    for _, row in anchor.iterrows():
        ts_a = row["timestamp"]
        match_all = True
        matches = {}
        for oid, ts_arr in other_ts.items():
            idx = int(np.searchsorted(ts_arr, ts_a))
            best_idx, best_diff = None, tol_ms + 1
            for c in [idx - 1, idx]:
                if 0 <= c < len(ts_arr):
                    d = abs(int(ts_arr[c]) - int(ts_a))
                    if d < best_diff:
                        best_diff, best_idx = d, c
            if best_idx is None:
                match_all = False
                break
            matches[oid] = float(other_rate[oid][best_idx])
        if match_all:
            aligned[anchor_id].append(float(row["rate"]))
            for oid, r in matches.items():
                aligned[oid].append(r)

    n = len(aligned["binance"])
    if n == 0:
        return None
    return {
        "n_aligned": n,
        "rates_binance": np.array(aligned["binance"]),
        "rates_bingx": np.array(aligned["bingx"]),
        "rates_okx": np.array(aligned["okx"]),
    }


def threshold_sweep(rates_b, rates_x, rates_o, thresholds=THRESHOLDS):
    """Para cada threshold X: filtrar bars |r_binance|≥X, computar unanimidad cross-3."""
    out = {}
    sig_b = np.sign(rates_b)
    sig_x = np.sign(rates_x)
    sig_o = np.sign(rates_o)
    n_total = len(rates_b)
    for X in thresholds:
        # Filter por |r_binance| >= X (Binance como anchor "verdad mayor cap").
        mask_b = np.abs(rates_b) >= X
        n_X = int(mask_b.sum())
        if n_X == 0:
            out[f"thr_{X:.0e}"] = {
                "n_bars_geq_X": 0,
                "unanimidad_3way_pct": None,
                "pair_BX_pct": None,
                "pair_BO_pct": None,
                "pair_XO_pct": None,
            }
            continue
        sb = sig_b[mask_b]
        sx = sig_x[mask_b]
        so = sig_o[mask_b]
        # Unanimidad cross-3: bingx & okx también claros (no zero)
        nontrivial = (sx != 0) & (so != 0)
        n_unanimous = int(((sb == sx) & (sb == so) & nontrivial).sum())
        # Use n_X as denominator (Binance ≥X bars), pair-wise también
        unan_pct = n_unanimous / n_X * 100.0
        bx_pct = int(((sb == sx) & (sx != 0)).sum()) / n_X * 100.0
        bo_pct = int(((sb == so) & (so != 0)).sum()) / n_X * 100.0
        xo_pct = int(((sx == so) & (sx != 0) & (so != 0)).sum()) / n_X * 100.0
        out[f"thr_{X:.0e}"] = {
            "n_bars_geq_X": n_X,
            "n_total_aligned": n_total,
            "frac_geq_X": n_X / n_total,
            "unanimidad_3way_pct": unan_pct,
            "pair_BX_pct": bx_pct,
            "pair_BO_pct": bo_pct,
            "pair_XO_pct": xo_pct,
        }
    return out


def find_critical_X(per_threshold: dict, min_unanimous=95.0, min_n=50):
    """Identifica X crítico: minimum X con unanimidad≥95% AND N≥min_n bars."""
    sorted_thrs = sorted(THRESHOLDS)
    for X in sorted_thrs:
        key = f"thr_{X:.0e}"
        d = per_threshold.get(key, {})
        n_bars = d.get("n_bars_geq_X", 0) or 0
        unan = d.get("unanimidad_3way_pct")
        if unan is not None and unan >= min_unanimous and n_bars >= min_n:
            return X, d
    return None, None


async def fetch_one_symbol(symbol: str, since_ms: int, until_ms: int, cache_base: str):
    """Fetch cross-3 exchanges con caches separados. Retorna 3 DataFrames."""
    cache_b = FundingCache(f"{cache_base}_binance")
    cache_x = FundingCache(f"{cache_base}_bingx")
    cache_o = FundingCache(f"{cache_base}_okx")

    df_b = await fetch_with_cache(symbol, since_ms, until_ms, "binance", cache_b)
    df_x = await fetch_with_cache(symbol, since_ms, until_ms, "bingx", cache_x)
    df_o = await fetch_with_cache(symbol, since_ms, until_ms, "okx", cache_o)
    return df_b, df_x, df_o


async def analyze_symbol(symbol: str, since_ms: int, until_ms: int, cache_base: str,
                         subwindows: list[tuple[int, int]] = None):
    """Analiza 1 símbolo: fetch + alineación + threshold sweep (full + sub-windows)."""
    print(f"  {symbol}: fetch cross-3...", flush=True)
    df_b, df_x, df_o = await fetch_one_symbol(symbol, since_ms, until_ms, cache_base)
    print(f"    n_b={len(df_b)} n_x={len(df_x)} n_o={len(df_o)}", flush=True)
    if df_b.empty or df_x.empty or df_o.empty:
        return {
            "symbol": symbol, "error": "empty_one_or_more_exchanges",
            "n_binance": len(df_b), "n_bingx": len(df_x), "n_okx": len(df_o),
        }
    aligned = align_3way(df_b, df_x, df_o)
    if aligned is None or aligned["n_aligned"] < 10:
        return {
            "symbol": symbol, "error": "align_failed",
            "n_binance": len(df_b), "n_bingx": len(df_x), "n_okx": len(df_o),
            "n_aligned": aligned["n_aligned"] if aligned else 0,
        }
    rb = aligned["rates_binance"]; rx = aligned["rates_bingx"]; ro = aligned["rates_okx"]
    full_sweep = threshold_sweep(rb, rx, ro)

    # Sub-window timestamps (filter rates_xx by ts; need to track ts — re-derive from anchor)
    # Reconstruct timestamp arrays per anchor (anchor_id was determined inside align). We don't
    # have ts arrays after align. Simplification: re-align per sub-window from raw dfs.
    sub_results = {}
    if subwindows:
        for i, (ws, we) in enumerate(subwindows):
            df_b_w = df_b[(df_b["timestamp"] >= ws) & (df_b["timestamp"] <= we)].reset_index(drop=True)
            df_x_w = df_x[(df_x["timestamp"] >= ws) & (df_x["timestamp"] <= we)].reset_index(drop=True)
            df_o_w = df_o[(df_o["timestamp"] >= ws) & (df_o["timestamp"] <= we)].reset_index(drop=True)
            a_w = align_3way(df_b_w, df_x_w, df_o_w)
            if a_w is None:
                sub_results[f"sw_{i}"] = {"error": "no_aligned"}
                continue
            sub_results[f"sw_{i}"] = {
                "ws_iso": pd.Timestamp(ws, unit="ms", tz="UTC").isoformat(),
                "we_iso": pd.Timestamp(we, unit="ms", tz="UTC").isoformat(),
                "n_aligned": a_w["n_aligned"],
                "sweep": threshold_sweep(a_w["rates_binance"], a_w["rates_bingx"], a_w["rates_okx"]),
            }

    return {
        "symbol": symbol,
        "n_binance": len(df_b),
        "n_bingx": len(df_x),
        "n_okx": len(df_o),
        "n_aligned": aligned["n_aligned"],
        "earliest": int(df_b["timestamp"].min()),
        "latest": int(df_b["timestamp"].max()),
        "rate_b_mean_abs": float(np.abs(rb).mean()),
        "rate_x_mean_abs": float(np.abs(rx).mean()),
        "rate_o_mean_abs": float(np.abs(ro).mean()),
        "rate_b_p95_abs": float(np.quantile(np.abs(rb), 0.95)),
        "rate_b_p99_abs": float(np.quantile(np.abs(rb), 0.99)),
        "sweep_full": full_sweep,
        "sweep_subwindows": sub_results,
    }


def aggregate_pooled(per_symbol_results: list[dict]) -> dict:
    """Pool todos los rates cross-symbols + threshold sweep agregado."""
    valid = [r for r in per_symbol_results if "error" not in r and r.get("n_aligned", 0) >= 10]
    if not valid:
        return {"error": "no_valid_symbols"}
    # Pool aligned rates from each symbol — re-fetch from cache or recompute alignment from cached files.
    # Simpler approach: aggregate sweep stats per threshold WEIGHTED by n_bars_geq_X.
    pooled = {}
    for X in THRESHOLDS:
        key = f"thr_{X:.0e}"
        n_total = 0
        n_unanimous = 0
        n_bx = 0; n_bo = 0; n_xo = 0
        for r in valid:
            d = r["sweep_full"].get(key, {})
            n_X = d.get("n_bars_geq_X", 0) or 0
            unan = d.get("unanimidad_3way_pct")
            if unan is None or n_X == 0:
                continue
            n_total += n_X
            n_unanimous += int(round(unan / 100.0 * n_X))
            n_bx += int(round((d.get("pair_BX_pct") or 0) / 100.0 * n_X))
            n_bo += int(round((d.get("pair_BO_pct") or 0) / 100.0 * n_X))
            n_xo += int(round((d.get("pair_XO_pct") or 0) / 100.0 * n_X))
        pooled[key] = {
            "n_bars_geq_X_pool": n_total,
            "unanimidad_3way_pct": (n_unanimous / n_total * 100.0) if n_total > 0 else None,
            "pair_BX_pct": (n_bx / n_total * 100.0) if n_total > 0 else None,
            "pair_BO_pct": (n_bo / n_total * 100.0) if n_total > 0 else None,
            "pair_XO_pct": (n_xo / n_total * 100.0) if n_total > 0 else None,
        }
    return pooled


async def main(args):
    until_ts = pd.Timestamp.now(tz="UTC")
    since_ts = until_ts - pd.Timedelta(days=args.since_days)
    since_ms = int(since_ts.timestamp() * 1000)
    until_ms = int(until_ts.timestamp() * 1000)
    symbols = args.symbols.split(",") if args.symbols else SYMBOLS_DEFAULT

    # Sub-windows: 3 chunks de since_days/3 cada uno
    sw_size = args.since_days // 3
    sub_ms = sw_size * 24 * 3600 * 1000
    subwindows = [
        (since_ms, since_ms + sub_ms),
        (since_ms + sub_ms, since_ms + 2 * sub_ms),
        (since_ms + 2 * sub_ms, until_ms),
    ]

    print(f"=== Fase 1' cross-3-exchanges (Path B-institutional) ===")
    print(f"Window: {since_ts.isoformat()} -> {until_ts.isoformat()} ({args.since_days}d)")
    print(f"Subwindows: {sw_size}d × 3")
    print(f"Symbols ({len(symbols)}): {symbols}")
    print(f"Thresholds: {THRESHOLDS}")
    print(f"Cache base: {args.cache_base}")
    print()

    results = []
    for sym in symbols:
        try:
            r = await analyze_symbol(sym, since_ms, until_ms, args.cache_base, subwindows)
        except Exception as e:
            r = {"symbol": sym, "error": f"exception: {type(e).__name__}: {e}"}
        results.append(r)
        if "error" in r:
            print(f"    -> ERROR {r['error']}")
        else:
            f5 = r["sweep_full"].get("thr_5e-05", {})
            f4 = r["sweep_full"].get("thr_1e-04", {})
            f3 = r["sweep_full"].get("thr_5e-04", {})
            print(f"    -> n_aligned={r['n_aligned']} "
                  f"thr5e-5: n={f5.get('n_bars_geq_X', 0)} unan={f5.get('unanimidad_3way_pct') or float('nan'):.1f}% | "
                  f"thr1e-4: n={f4.get('n_bars_geq_X', 0)} unan={f4.get('unanimidad_3way_pct') or float('nan'):.1f}% | "
                  f"thr5e-4: n={f3.get('n_bars_geq_X', 0)} unan={f3.get('unanimidad_3way_pct') or float('nan'):.1f}%")

    # Aggregate across symbols
    pooled = aggregate_pooled(results)
    if "error" not in pooled:
        X_crit, X_data = find_critical_X(pooled, min_unanimous=95.0, min_n=50)
    else:
        X_crit = None; X_data = None

    print()
    print("=== POOLED CROSS-15-SYMBOLS ===")
    print(f"{'thr':<10}{'n_bars≥X':>10}{'unan_3way':>11}{'pair_BX':>9}{'pair_BO':>9}{'pair_XO':>9}")
    for X in THRESHOLDS:
        key = f"thr_{X:.0e}"
        d = pooled.get(key, {})
        if d and d.get("unanimidad_3way_pct") is not None:
            print(f"{X:<10.0e}{d['n_bars_geq_X_pool']:>10}{d['unanimidad_3way_pct']:>10.1f}%"
                  f"{d['pair_BX_pct']:>8.1f}%{d['pair_BO_pct']:>8.1f}%{d['pair_XO_pct']:>8.1f}%")
        else:
            print(f"{X:<10.0e}{'-':>10}{'-':>11}{'-':>9}{'-':>9}{'-':>9}")

    if X_crit is not None:
        print(f"\nThreshold X CRÍTICO: {X_crit:.0e} (unanimidad {X_data['unanimidad_3way_pct']:.1f}% N={X_data['n_bars_geq_X_pool']})")
        if X_crit <= 1e-4:
            verdict = "CONFIRMA RASGO ESTRUCTURAL"
        elif X_crit <= 5e-4:
            verdict = "EXTREMO RARO (X medio-alto)"
        else:
            verdict = "EXTREMO RARO (X muy alto)"
    else:
        verdict = "REFUTA RASGO ESTRUCTURAL (ningún X≤1e-3 con unanimidad≥95% N≥50)"
    print(f"VEREDICTO: {verdict}")

    out = {
        "meta": {
            "since": since_ts.isoformat(),
            "until": until_ts.isoformat(),
            "since_days": args.since_days,
            "subwindow_days": sw_size,
            "thresholds_tested": THRESHOLDS,
            "tolerance_ms_align": ALIGN_TOLERANCE_MS,
            "min_unanimous_pct": 95.0,
            "min_n_bars": 50,
        },
        "symbols": symbols,
        "per_symbol": results,
        "pooled": pooled,
        "critical_X": X_crit,
        "critical_X_data": X_data,
        "verdict": verdict,
    }
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"\nSaved: {args.out}")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="", help="Comma-sep list. Default 15 cross-cap-tier.")
    p.add_argument("--since-days", type=int, default=180)
    p.add_argument("--out", default="")
    p.add_argument("--cache-base", default="/tmp/fc_pathb_fase1",
                   help="Base path for caches. Adds _binance, _bingx, _okx suffixes.")
    args = p.parse_args()
    asyncio.run(main(args))
