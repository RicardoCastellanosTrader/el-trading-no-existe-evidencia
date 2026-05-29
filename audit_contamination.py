"""Contamination sub-analysis — Ricardo cardinal directive 2026-05-26.

Tests whether A's pf_fwd advantage in AMPLIO sym is REAL edge or artifact of
lab_lite 5K-window overlapping the walk-forward fwd test zone.

For each sym × cluster:
  1. Apply GMM to FULL parquet → cluster_labels
  2. identify_episodes per cluster
  3. Compute train/fwd split (last 30% chronologically = fwd_eps)
  4. Get bar indices belonging to fwd_eps for each cluster
  5. Compute overlap with bars[-5000:] (lab_lite Mode A window)
  6. Report fwd_bars_INSIDE / fwd_bars_OUTSIDE per cluster

Read-only — no productive code modification.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

import regime_walk_forward as rwf
import lab_lite_zonas_v5e as ll


def analyze_overlap(symbol: str, parquet_dir: str = "data_cache",
                     model_dir: str = "regime_models") -> dict:
    sym_clean = symbol.replace("/", "").replace("USDT", "")
    p = Path(parquet_dir) / f"{sym_clean}USDT_1h.parquet"
    df = pd.read_parquet(p)
    if "timestamp" not in df.columns and "timestamp_ms" in df.columns:
        df = df.rename(columns={"timestamp_ms": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    n_bars = len(df)

    # Lab_lite Mode A window
    LL_WINDOW = 5000
    ll_start = max(0, n_bars - LL_WINDOW)
    ll_end = n_bars
    ll_start_ts = df["timestamp"].iloc[ll_start]
    ll_end_ts = df["timestamp"].iloc[ll_end - 1]

    # Apply GMM (same as productive)
    labels, cluster_info = ll.load_and_apply_regime_model(symbol, df, model_dir=model_dir)
    n_clusters = cluster_info["n_clusters"]
    cluster_names = cluster_info.get("cluster_names", [f"C{k}" for k in range(n_clusters)])

    # Identify episodes per cluster (chronological)
    episodes = rwf.identify_episodes(labels, n_clusters,
                                       min_bars=rwf.MIN_EPISODE_BARS)

    result = {
        "symbol": symbol,
        "n_bars": n_bars,
        "ll_window_start_bar": ll_start,
        "ll_window_end_bar": ll_end,
        "ll_window_start_ts": str(ll_start_ts),
        "ll_window_end_ts": str(ll_end_ts),
        "clusters": {},
    }

    train_ratio = rwf.TRAIN_RATIO  # 0.70
    for k in range(n_clusters):
        eps = episodes.get(k, [])
        n_eps = len(eps)
        if n_eps == 0:
            continue
        n_train = max(1, int(n_eps * train_ratio))
        n_fwd = n_eps - n_train
        train_eps = eps[:n_train]
        fwd_eps = eps[n_train:]

        # Build set of fwd bars (using boolean mask for efficiency)
        fwd_mask = np.zeros(n_bars, dtype=bool)
        for start, end in fwd_eps:
            fwd_mask[start:end] = True
        fwd_bars_total = int(fwd_mask.sum())

        # Overlap with lab_lite window
        in_window_mask = np.zeros(n_bars, dtype=bool)
        in_window_mask[ll_start:ll_end] = True
        fwd_inside = int((fwd_mask & in_window_mask).sum())
        fwd_outside = fwd_bars_total - fwd_inside
        pct_inside = (fwd_inside / fwd_bars_total * 100) if fwd_bars_total > 0 else 0.0

        # Fwd date range (first start bar of first fwd ep → last end bar of last fwd ep)
        if fwd_eps:
            fwd_first_bar = fwd_eps[0][0]
            fwd_last_bar = fwd_eps[-1][1] - 1
            fwd_ts_start = str(df["timestamp"].iloc[fwd_first_bar])
            fwd_ts_end = str(df["timestamp"].iloc[fwd_last_bar])
        else:
            fwd_ts_start = fwd_ts_end = "n/a"

        result["clusters"][str(k)] = {
            "name": cluster_names[k] if k < len(cluster_names) else f"C{k}",
            "n_eps_total": n_eps,
            "n_eps_train": n_train,
            "n_eps_fwd": n_fwd,
            "fwd_bars_total": fwd_bars_total,
            "fwd_bars_inside_5K": fwd_inside,
            "fwd_bars_outside_5K": fwd_outside,
            "pct_fwd_inside_5K": round(pct_inside, 1),
            "fwd_ts_start": fwd_ts_start,
            "fwd_ts_end": fwd_ts_end,
        }
    return result


def main():
    syms = sys.argv[1:] if len(sys.argv) > 1 else [
        "BTC/USDT", "ETH/USDT", "BNB/USDT",
        "SEI/USDT", "POL/USDT", "ONDO/USDT",
    ]
    print(f"\n{'='*100}")
    print(f"CONTAMINATION OVERLAP ANALYSIS — fwd_eps vs lab_lite 5K window")
    print(f"{'='*100}\n")
    print(f"{'SYM':<6} {'class':<7} {'n_bars':<8} {'5K range (bars)':<20} {'5K range (date)':<48}")
    print("-" * 100)
    all_results = {}
    for sym in syms:
        try:
            r = analyze_overlap(sym)
        except Exception as e:
            print(f"{sym}: ERROR {e}")
            continue
        all_results[sym] = r
        bars_range = f"[{r['ll_window_start_bar']:,}, {r['ll_window_end_bar']:,})"
        date_range = f"{r['ll_window_start_ts'][:10]} → {r['ll_window_end_ts'][:10]}"
        # Approx classification by bar count
        bc = r['n_bars']
        klass = "corto" if bc < 12000 else "medio" if bc < 50000 else "amplio"
        print(f"{sym.replace('/USDT',''):<6} {klass:<7} {bc:<8,} {bars_range:<20} {date_range:<48}")

    print(f"\n{'='*100}")
    print(f"PER-CLUSTER OVERLAP")
    print(f"{'='*100}\n")
    print(f"{'SYM':<6} {'k':<2} {'cluster_name':<28} {'fwd_eps':<8} {'fwd_bars':<10} {'inside_5K':<10} {'outside_5K':<10} {'%inside':<8} {'fwd_ts_range':<28}")
    print("-" * 130)
    for sym, r in all_results.items():
        for k, c in r["clusters"].items():
            ts_range = f"{c['fwd_ts_start'][:10]} → {c['fwd_ts_end'][:10]}"
            print(f"{sym.replace('/USDT',''):<6} {k:<2} {c['name']:<28} {c['n_eps_fwd']:<8} {c['fwd_bars_total']:<10,} {c['fwd_bars_inside_5K']:<10,} {c['fwd_bars_outside_5K']:<10,} {c['pct_fwd_inside_5K']:<8.1f} {ts_range:<28}")

    out_path = Path("audit_etapa2_20260522_213747") / "contamination_overlap.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
