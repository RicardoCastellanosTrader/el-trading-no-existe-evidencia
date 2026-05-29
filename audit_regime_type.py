"""Regime-TYPE re-analysis (Ricardo cardinal directive 2026-05-29).

Cardinal §0.0 test: does B2 (full-history preset selection) win SYSTEMATICALLY
in clusters whose regime is ABSENT from lab_lite Mode A's recent 5000-bar window
(where A is structurally blind), and tie/lose where the regime IS represented?

READ-ONLY. No new walk-forward, no productive modification. Reuses:
  - rwf.compute_cluster_labels  (EXACT productive GMM labeling path)
  - contamination_part_b.json   (G.3-validated pf_fwd + temporal INSIDE/OUTSIDE)
  - specialist JSONs            (A_deployed vs wf_B2_dyn) for pf_combined/trades

PARTE A — characterize each (sym,cluster) regime + % presence in 5K window.
PARTE B — partition 18 cells REPRESENTADO/AUSENTE, B2 vs A win rate + Δ.
PARTE C — refine with pf_fwd_OUTSIDE (double clean: regime-type + non-overlap).
PARTE D — assembled into stdout report + audit_regime_type_results.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from regime_walk_forward import compute_cluster_labels
from regime_features import FEATURE_NAMES

D = Path("audit_etapa2_20260522_213747")
SYMS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SEI/USDT", "POL/USDT", "ONDO/USDT"]
LL_WINDOW = 5000
REPR_THRESHOLD = 0.15   # cluster REPRESENTADO if >= 15% of recent 5K bars
MIN_TR_FWD = 15         # power floor per cell (matches productive _FWD_MIN_TRADES)


def load_full_parquet(symbol: str) -> pd.DataFrame:
    sym_clean = symbol.replace("/", "").replace("USDT", "")
    df = pd.read_parquet(Path("data_cache") / f"{sym_clean}USDT_1h.parquet")
    if "timestamp" not in df.columns and "timestamp_ms" in df.columns:
        df = df.rename(columns={"timestamp_ms": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["timestamp", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def load_spec_metrics(spec_path: Path):
    """Return {k: {pf_fwd, pf_combined, trades_fwd, pf_tr, config_id}} for top-1."""
    out = {}
    if not spec_path.exists():
        return out
    with open(spec_path) as f:
        d = json.load(f)
    for k, v in d.get("clusters", {}).items():
        tc = v.get("top_configs") or []
        if not tc:
            out[int(k)] = None
            continue
        t = tc[0]
        out[int(k)] = {
            "config_id": int(t["config_id"]),
            "pf_fwd": float(t.get("pf_fwd", 0)),
            "pf_combined": float(t.get("pf_combined", 0)),
            "pf_tr": float(t.get("pf_tr", 0)),
            "trades_fwd": int(t.get("trades_fwd", 0)),
        }
    return out


def main():
    # contamination_part_b: (sym,mode,k) -> pf_outside/n_inside/n_outside/pf_fwd
    with open(D / "contamination_part_b.json") as f:
        cb = {(c["sym"], c["mode"], c["k"]): c for c in json.load(f) if "error" not in c}

    rows = []         # one per (sym, cluster)
    partA_tables = []

    for sym in SYMS:
        sym_clean = sym.replace("/", "").replace("USDT", "")
        df = load_full_parquet(sym)
        n_bars = len(df)
        ll_start = max(0, n_bars - LL_WINDOW)

        md = joblib.load(Path("regime_models") / f"{sym_clean}_regime.joblib")
        gmm, scaler, n_clusters = md["gmm"], md["scaler"], md["n_clusters"]
        centroids_feat = scaler.inverse_transform(gmm.means_)
        cluster_names = md.get("cluster_names", {})

        labels, n_cl = compute_cluster_labels(df, md)
        assert n_cl == n_clusters
        valid_all = labels >= 0
        win_labels = labels[ll_start:]
        valid_win = win_labels >= 0
        n_valid_win = int(valid_win.sum())
        ts = df["timestamp"].values

        specA = load_spec_metrics(D / "baseline_A_deployed" / f"{sym_clean}USDT_specialist_configs.json")
        specB = load_spec_metrics(D / f"wf_B2_dyn_{sym_clean}" / f"{sym_clean}USDT_specialist_configs.json")

        win_start_ts = pd.Timestamp(ts[ll_start]) if n_bars > 0 else None
        hist_start_ts = pd.Timestamp(ts[np.where(valid_all)[0][0]]) if valid_all.any() else None
        hist_end_ts = pd.Timestamp(ts[-1])

        for k in range(n_clusters):
            pct_recent = float((win_labels[valid_win] == k).mean()) if n_valid_win else 0.0
            pct_full = float((labels[valid_all] == k).mean()) if valid_all.any() else 0.0
            # rolling-500 max share in recent window (secondary "dominant-in-stretch")
            recent_k = (win_labels == k).astype(float)
            if len(recent_k) >= 500:
                kern = np.ones(500) / 500.0
                roll = np.convolve(recent_k, kern, mode="valid")
                roll_max = float(roll.max())
            else:
                roll_max = pct_recent
            klass = "REPRESENTADO" if (pct_recent >= REPR_THRESHOLD or roll_max >= 0.50) else "AUSENTE"

            # regime span across history (first/last bar of this cluster)
            idx_k = np.where(labels == k)[0]
            span = None
            if len(idx_k):
                span = (str(pd.Timestamp(ts[idx_k[0]]).date()),
                        str(pd.Timestamp(ts[idx_k[-1]]).date()))

            a, b = specA.get(k), specB.get(k)
            cbA = cb.get((sym, "A", k)); cbB = cb.get((sym, "B2", k))
            row = {
                "sym": sym, "k": k,
                "centroid": {FEATURE_NAMES[j]: round(float(centroids_feat[k, j]), 3) for j in range(len(FEATURE_NAMES))},
                "cluster_name": cluster_names.get(str(k)) if isinstance(cluster_names, dict) else None,
                "pct_recent_5k": round(pct_recent, 4),
                "pct_full_hist": round(pct_full, 4),
                "roll500_max_recent": round(roll_max, 4),
                "regime_span": span,
                "klass": klass,
                "A_pf_fwd": a["pf_fwd"] if a else None,
                "B2_pf_fwd": b["pf_fwd"] if b else None,
                "A_pf_combined": a["pf_combined"] if a else None,
                "B2_pf_combined": b["pf_combined"] if b else None,
                "A_trades_fwd": a["trades_fwd"] if a else None,
                "B2_trades_fwd": b["trades_fwd"] if b else None,
                "A_pf_outside": (cbA.get("pf_outside") if cbA else None),
                "B2_pf_outside": (cbB.get("pf_outside") if cbB else None),
                "A_n_outside": (cbA.get("n_outside") if cbA else None),
                "B2_n_outside": (cbB.get("n_outside") if cbB else None),
            }
            rows.append(row)
            partA_tables.append(row)

        partA_meta = {
            "sym": sym, "n_bars": n_bars, "n_valid_win": n_valid_win,
            "win_start": str(win_start_ts.date()) if win_start_ts is not None else None,
            "hist_start": str(hist_start_ts.date()) if hist_start_ts is not None else None,
            "hist_end": str(hist_end_ts.date()),
            "training_date_range": md.get("training_date_range"),
        }
        partA_tables.append({"_meta": partA_meta})

    # ===== PARTE A report =====
    print("\n" + "=" * 110)
    print(f"PARTE A — Regime characterization + pct presence in recent 5K window  (threshold REPR>={REPR_THRESHOLD*100:.0f}pct or roll500>=50pct)")
    print("=" * 110)
    print(f"{'sym':10} {'k':2} {'Hurst':>6} {'Z_ATR':>6} {'ER':>6} {'pct5K':>7} {'pctFull':>7} {'roll500':>7} {'class':12} {'regime_span'}")
    for r in rows:
        c = r["centroid"]
        sp = f"{r['regime_span'][0]}..{r['regime_span'][1]}" if r["regime_span"] else "-"
        print(f"{r['sym']:10} {r['k']:<2} {c['Hurst']:>6.3f} {c['Z_ATR']:>6.3f} {c['ER']:>6.3f} "
              f"{r['pct_recent_5k']*100:>6.1f}% {r['pct_full_hist']*100:>6.1f}% {r['roll500_max_recent']*100:>6.1f}% "
              f"{r['klass']:12} {sp}")

    # ===== PARTE B test =====
    def safe(x):
        return x if (x is not None) else float("nan")

    def group_stats(cells, metric_a, metric_b, tr_floor=True):
        d = []
        for r in cells:
            va, vb = r[metric_a], r[metric_b]
            if va is None or vb is None:
                continue
            tr_ok = True
            if tr_floor:
                ta, tb = r["A_trades_fwd"], r["B2_trades_fwd"]
                tr_ok = (ta is not None and tb is not None and min(ta, tb) >= MIN_TR_FWD)
            d.append((vb - va, vb > va, tr_ok, va, vb, r))
        return d

    def summarize(label, cells, metric_a, metric_b):
        d = group_stats(cells, metric_a, metric_b)
        if not d:
            print(f"  [{label}] no cells")
            return None
        deltas = np.array([x[0] for x in d])
        wins = np.array([x[1] for x in d])
        powered = [x for x in d if x[2]]
        deltas_p = np.array([x[0] for x in powered]) if powered else np.array([])
        wins_p = np.array([x[1] for x in powered]) if powered else np.array([])
        # winsorized mean to tame degenerate pf outliers (e.g. pf=628)
        capped = np.clip(deltas, -10, 10)
        out = {
            "metric": f"{metric_b} vs {metric_a}",
            "n_cells": len(d),
            "n_powered": len(powered),
            "B2_win_rate": round(float(wins.mean()), 3),
            "B2_win_rate_powered": round(float(wins_p.mean()), 3) if len(wins_p) else None,
            "delta_mean": round(float(deltas.mean()), 3),
            "delta_median": round(float(np.median(deltas)), 3),
            "delta_mean_capped10": round(float(capped.mean()), 3),
            "delta_median_powered": round(float(np.median(deltas_p)), 3) if len(deltas_p) else None,
        }
        print(f"  [{label}] n={out['n_cells']} (powered≥{MIN_TR_FWD}tr={out['n_powered']}) | "
              f"B2 win={out['B2_win_rate']:.0%} (powered={out['B2_win_rate_powered']}) | "
              f"Δmedian={out['delta_median']:+.3f} Δmean_cap10={out['delta_mean_capped10']:+.3f} "
              f"Δmedian_powered={out['delta_median_powered']}")
        return out

    repres = [r for r in rows if r["klass"] == "REPRESENTADO"]
    ausente = [r for r in rows if r["klass"] == "AUSENTE"]

    print("\n" + "=" * 110)
    print(f"PARTE B — Cardinal test: B2 vs A by regime class  | REPRESENTADO={len(repres)} cells, AUSENTE={len(ausente)} cells")
    print("=" * 110)
    partB = {"counts": {"REPRESENTADO": len(repres), "AUSENTE": len(ausente)}, "results": {}}
    for metric_a, metric_b, name in [("A_pf_fwd", "B2_pf_fwd", "pf_fwd"),
                                      ("A_pf_combined", "B2_pf_combined", "pf_combined")]:
        print(f"\n  --- metric: {name} ---")
        partB["results"][name] = {
            "AUSENTE (A blind — §0.0 predicts B2 wins)": summarize("AUSENTE   ", ausente, metric_a, metric_b),
            "REPRESENTADO (A sees regime — predicts tie)": summarize("REPRESENT.", repres, metric_a, metric_b),
        }

    # ===== PARTE C — double clean (pf_outside by regime class) =====
    print("\n" + "=" * 110)
    print("PARTE C — pf_fwd_OUTSIDE (trades entered before recent 5K) by regime class — double clean")
    print("=" * 110)
    def outside_cells(cells):
        d = []
        for r in cells:
            a, b = r["A_pf_outside"], r["B2_pf_outside"]
            na, nb = r["A_n_outside"], r["B2_n_outside"]
            if a is None or b is None:
                continue
            if na is None or nb is None or min(na, nb) < MIN_TR_FWD:
                continue
            d.append((b - a, b > a, r))
        return d
    partC = {}
    for label, cells in [("AUSENTE", ausente), ("REPRESENTADO", repres)]:
        d = outside_cells(cells)
        if not d:
            print(f"  [{label}] 0 cells with ≥{MIN_TR_FWD} outside trades both modes — no temporal-clean power")
            partC[label] = {"n_cells": 0}
            continue
        deltas = np.array([x[0] for x in d]); wins = np.array([x[1] for x in d])
        partC[label] = {"n_cells": len(d), "B2_win_rate": round(float(wins.mean()), 3),
                        "delta_median": round(float(np.median(deltas)), 3)}
        print(f"  [{label}] n={len(d)} powered-outside cells | B2 win={wins.mean():.0%} | Δmedian={np.median(deltas):+.3f}")
        for _, _, r in d:
            print(f"      {r['sym']} C{r['k']} ({r['klass']}): A_pf_out={r['A_pf_outside']} B2_pf_out={r['B2_pf_outside']} "
                  f"(n_out A={r['A_n_outside']} B2={r['B2_n_outside']})")

    # ===== save =====
    out = {"part_a": partA_tables, "part_b": partB, "part_c": partC,
           "params": {"LL_WINDOW": LL_WINDOW, "REPR_THRESHOLD": REPR_THRESHOLD, "MIN_TR_FWD": MIN_TR_FWD}}
    with open("audit_regime_type_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nSaved: audit_regime_type_results.json")


if __name__ == "__main__":
    main()
