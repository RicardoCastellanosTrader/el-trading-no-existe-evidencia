"""Fase 1 — Cross-exchange funding coherence Binance vs BingX.

Variante 4 Opción C (Sesión 1 / 2026-04-26 sesión 3 día). Reusa
funding_context.fetch_funding_rates con exchange_id ∈ {bingx, binance}.

Subset 5 símbolos: BTC, ETH, ONDO, DOGE, SEI (cobertura larga + corta + 4h).
Ventana: últimos 30 días.

Métricas computadas:
  - Direccional coincidence: % bars sign(rate_b) == sign(rate_x).
  - Categorical coincidence: % bars same {long_crowd|short_crowd|neutral}
    con threshold ±5e-5.
  - Spearman ρ(rate_binance, rate_bingx) sobre rates alineados.

Para 4h vs 8h asimétrico (ONDO BingX 4h, Binance probable 8h):
alinear sub-sample timestamps Binance, restringir comparación a esos.

Ejecutar desde VPS Tokyo:
  ssh trader@vps "cd combolab && /home/trader/venv/bin/python \\
    analysis_scripts/funding_v4_opcion_c_20260426/fase1_cross_exchange.py \\
    --symbols BTC/USDT,ETH/USDT,ONDO/USDT,DOGE/USDT,SEI/USDT \\
    --since-days 30 \\
    --out analysis_scripts/funding_v4_opcion_c_20260426/fase1_results.json"

Output JSON con per-symbol metrics + raw rates (para auditoría).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
COMBOLAB_ROOT = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, COMBOLAB_ROOT)

import pandas as pd
import numpy as np

from funding_context import fetch_funding_rates, NEUTRAL_THRESHOLD

NEUTRAL_TS_TOLERANCE_MS = 30 * 60 * 1000  # 30 min — tolerar drift timing


def classify(rate: float) -> str:
    if rate is None or math.isnan(rate):
        return "unknown"
    if abs(rate) < NEUTRAL_THRESHOLD:
        return "neutral"
    return "long_crowd" if rate > 0 else "short_crowd"


def spearman(xs, ys) -> tuple[float, float]:
    """Spearman ρ + p-value approx normal."""
    n = len(xs)
    if n < 3:
        return float("nan"), float("nan")
    rx = pd.Series(xs).rank().values
    ry = pd.Series(ys).rank().values
    mx, my = rx.mean(), ry.mean()
    num = ((rx - mx) * (ry - my)).sum()
    dx = math.sqrt(((rx - mx) ** 2).sum())
    dy = math.sqrt(((ry - my) ** 2).sum())
    rho = num / (dx * dy) if dx * dy > 0 else 0.0
    if abs(rho) >= 0.999:
        return rho, 0.0
    t = rho * math.sqrt((n - 2) / max(1 - rho * rho, 1e-12))
    # 2-sided p approx normal
    from math import erf
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / math.sqrt(2))))
    return rho, p


def align_timestamps(df_b: pd.DataFrame, df_x: pd.DataFrame, tol_ms: int = NEUTRAL_TS_TOLERANCE_MS):
    """Alinea rates Binance y BingX por timestamp con tolerance. Retorna 2 arrays alineados."""
    if df_b.empty or df_x.empty:
        return np.array([]), np.array([]), 0
    # Para cada timestamp Binance, busca el más cercano BingX dentro de tol_ms.
    # Binance suele tener menos rates (8h) que BingX (4h o 8h).
    # Usa el lado con menos rates como "anchor".
    if len(df_b) <= len(df_x):
        anchor, other = df_b, df_x
        anchor_label = "binance"
    else:
        anchor, other = df_x, df_b
        anchor_label = "bingx"
    other_ts = other["timestamp"].values
    aligned_anchor, aligned_other = [], []
    for _, row in anchor.iterrows():
        ts_a = row["timestamp"]
        idx = int(np.searchsorted(other_ts, ts_a))
        # Check candidates idx-1 y idx
        candidates = []
        if idx > 0:
            candidates.append(idx - 1)
        if idx < len(other_ts):
            candidates.append(idx)
        best_idx, best_diff = None, tol_ms + 1
        for c in candidates:
            d = abs(int(other_ts[c]) - int(ts_a))
            if d < best_diff:
                best_diff, best_idx = d, c
        if best_idx is not None:
            aligned_anchor.append(row["rate"])
            aligned_other.append(float(other["rate"].iloc[best_idx]))
    if anchor_label == "binance":
        return np.array(aligned_anchor), np.array(aligned_other), len(aligned_anchor)
    else:
        return np.array(aligned_other), np.array(aligned_anchor), len(aligned_anchor)


async def fetch_pair(symbol: str, since_ms: int, until_ms: int) -> dict:
    """Fetch ambos exchanges para un símbolo + computa métricas."""
    print(f"  {symbol}: fetch BingX...", flush=True)
    df_x = await fetch_funding_rates(symbol, since_ms, until_ms, exchange_id="bingx")
    print(f"  {symbol}: fetch Binance...", flush=True)
    try:
        df_b = await fetch_funding_rates(symbol, since_ms, until_ms, exchange_id="binance")
    except Exception as e:
        return {"symbol": symbol, "error": f"binance_fetch_failed: {type(e).__name__}: {e}",
                "n_bingx": int(len(df_x)), "n_binance": 0}

    n_b, n_x = len(df_b), len(df_x)
    if n_b == 0 or n_x == 0:
        return {"symbol": symbol, "error": "empty_history", "n_bingx": n_x, "n_binance": n_b,
                "n_aligned": 0, "directional_pct": None, "categorical_pct": None,
                "spearman_rho": None, "spearman_p": None}

    rates_b, rates_x, n_aligned = align_timestamps(df_b, df_x)
    if n_aligned < 3:
        return {"symbol": symbol, "error": "aligned_too_few",
                "n_bingx": n_x, "n_binance": n_b, "n_aligned": n_aligned,
                "directional_pct": None, "categorical_pct": None,
                "spearman_rho": None, "spearman_p": None}

    # Direccional: excluir muy cerca de cero ambos
    sig_b = np.sign(rates_b)
    sig_x = np.sign(rates_x)
    nontrivial = (np.abs(rates_b) > NEUTRAL_THRESHOLD) & (np.abs(rates_x) > NEUTRAL_THRESHOLD)
    if nontrivial.sum() > 0:
        directional_pct = float(((sig_b == sig_x) & nontrivial).sum()) / float(nontrivial.sum()) * 100.0
        n_directional = int(nontrivial.sum())
    else:
        directional_pct = None
        n_directional = 0

    # Categorical (multi-threshold sensitivity)
    THRESHOLDS = [1e-5, 5e-5, 1e-4, 5e-4]
    categorical_pct_by_thr = {}
    for thr in THRESHOLDS:
        def cls(r):
            if abs(r) < thr:
                return "neutral"
            return "long" if r > 0 else "short"
        cats_b = [cls(float(r)) for r in rates_b]
        cats_x = [cls(float(r)) for r in rates_x]
        match = sum(1 for cb, cx in zip(cats_b, cats_x) if cb == cx)
        categorical_pct_by_thr[f"thr_{thr:.0e}"] = match / n_aligned * 100.0

    categorical_pct = categorical_pct_by_thr["thr_5e-05"]

    rho, p = spearman(list(rates_b), list(rates_x))

    # Magnitude descriptive
    # Magnitude diff per-bar
    diff = rates_b - rates_x
    return {
        "symbol": symbol,
        "n_bingx": n_x,
        "n_binance": n_b,
        "n_aligned": n_aligned,
        "n_directional_nontrivial": n_directional,
        "directional_pct": directional_pct,
        "categorical_pct": categorical_pct,
        "categorical_pct_by_thr": categorical_pct_by_thr,
        "spearman_rho": rho,
        "spearman_p": p,
        "rate_binance_mean_abs": float(np.abs(rates_b).mean()),
        "rate_bingx_mean_abs": float(np.abs(rates_x).mean()),
        "rate_binance_signed_mean": float(rates_b.mean()),
        "rate_bingx_signed_mean": float(rates_x.mean()),
        "diff_mean": float(diff.mean()),
        "diff_abs_mean": float(np.abs(diff).mean()),
        "diff_p95": float(np.quantile(np.abs(diff), 0.95)),
        "earliest_binance": int(df_b["timestamp"].min()),
        "latest_binance": int(df_b["timestamp"].max()),
        "earliest_bingx": int(df_x["timestamp"].min()),
        "latest_bingx": int(df_x["timestamp"].max()),
    }


async def main(args):
    until_ts = pd.Timestamp.now(tz="UTC")
    since_ts = until_ts - pd.Timedelta(days=args.since_days)
    since_ms = int(since_ts.timestamp() * 1000)
    until_ms = int(until_ts.timestamp() * 1000)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    print(f"=== Fase 1 cross-exchange Binance vs BingX ===")
    print(f"Window: {since_ts.isoformat()} -> {until_ts.isoformat()} ({args.since_days}d)")
    print(f"Symbols: {symbols}")
    print(f"Threshold neutral: {NEUTRAL_THRESHOLD}")
    print()

    results = []
    for sym in symbols:
        r = await fetch_pair(sym, since_ms, until_ms)
        results.append(r)
        if "error" in r:
            print(f"  {sym}: ERROR {r['error']} (n_bingx={r.get('n_bingx', '?')} "
                  f"n_binance={r.get('n_binance', '?')} n_aligned={r.get('n_aligned', '?')})")
        else:
            dir_s = f"{r['directional_pct']:.1f}%" if r.get('directional_pct') is not None else "n/a"
            cat_s = f"{r['categorical_pct']:.1f}%" if r.get('categorical_pct') is not None else "n/a"
            rho_s = f"{r['spearman_rho']:+.4f}" if r.get('spearman_rho') is not None else "n/a"
            p_s = f"{r['spearman_p']:.4f}" if r.get('spearman_p') is not None else "n/a"
            print(f"  {sym}: n_bingx={r['n_bingx']} n_binance={r['n_binance']} "
                  f"n_aligned={r['n_aligned']} directional={dir_s} "
                  f"categorical={cat_s} rho={rho_s} p={p_s}")

    # Aggregate
    valid = [r for r in results if "error" not in r and r.get("n_aligned", 0) >= 3]
    if valid:
        mean_dir = sum(r["directional_pct"] or 0 for r in valid) / len(valid)
        mean_cat = sum(r["categorical_pct"] or 0 for r in valid) / len(valid)
        rhos = [r["spearman_rho"] for r in valid if r.get("spearman_rho") is not None
                and not math.isnan(r["spearman_rho"])]
        mean_rho = sum(rhos) / len(rhos) if rhos else float("nan")
        print()
        print(f"=== AGGREGATE Fase 1 ({len(valid)} símbolos válidos) ===")
        print(f"  Mean directional: {mean_dir:.1f}%")
        print(f"  Mean categorical: {mean_cat:.1f}%")
        print(f"  Mean Spearman ρ: {mean_rho:+.4f}")

        # Veredicto
        if mean_dir >= 95.0 and mean_cat >= 95.0:
            verdict = "ALTA"
        elif mean_dir >= 80.0 and mean_cat >= 80.0:
            verdict = "MEDIA"
        else:
            verdict = "BAJA"
        print(f"  VEREDICTO: COHERENCIA {verdict}")
        agg = {"mean_directional_pct": mean_dir, "mean_categorical_pct": mean_cat,
               "mean_spearman_rho": mean_rho, "verdict": verdict, "n_valid": len(valid)}
    else:
        agg = {"verdict": "NO_DATA", "n_valid": 0}
        print("  VEREDICTO: NO_DATA (todos símbolos fallaron)")

    out = {
        "meta": {
            "since": since_ts.isoformat(),
            "until": until_ts.isoformat(),
            "since_days": args.since_days,
            "neutral_threshold": NEUTRAL_THRESHOLD,
            "tolerance_ms_align": NEUTRAL_TS_TOLERANCE_MS,
        },
        "per_symbol": results,
        "aggregate": agg,
    }
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"\nSaved: {args.out}")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="BTC/USDT,ETH/USDT,ONDO/USDT,DOGE/USDT,SEI/USDT")
    p.add_argument("--since-days", type=int, default=30)
    p.add_argument("--out", default="")
    args = p.parse_args()
    asyncio.run(main(args))
