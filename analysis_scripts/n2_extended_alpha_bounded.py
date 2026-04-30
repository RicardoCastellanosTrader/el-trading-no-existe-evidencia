#!/usr/bin/env python3
"""
N.2 extended Opción α-bounded — single combined pass cross-45 sym k=2..15.

Per (sym, k):
  - GMM fit (n_init=10 fidelity productiva train_regime_model.py:199).
  - Compute BIC.
  - Predict labels.
  - identify_episodes (MIN_EPISODE_BARS=50, regime_walk_forward.py:149).
  - Count n_clusters_valid (≥5 episodes per cluster, regime_walk_forward.py:151).

Output:
  - Extended BIC sweep k=2..15 cross-45 sym → k_optimal_extended distribution.
  - Operability sweep cross-45 sym k=2..15 → k_max_operable distribution per sym.
  - Gap analysis BIC k_optimal vs k_max_operable per sym.
  - Outcome_C per-symbol adaptive MAX_K viability evaluation.

Compute estimate ~1-2h cumulative (single combined pass, fits reused).
NO toca live/* productivo. Read-only analytical.

Usage: python -m analysis_scripts.n2_extended_alpha_bounded
"""

import json
import os
import sys
import time
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from collections import defaultdict

# Fix Windows cp1252 encoding (preserve unicode in output)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*did not converge.*')

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_features import compute_regime_features

CACHE_DIR = os.path.join(_ROOT, "data_cache")
TIMEFRAME = "1h"

# 45 sym primary source train_regime_model.py:37-48
SYMBOLS = [
    "BNB/USDT", "BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT",
    "TRX/USDT", "DOGE/USDT", "ADA/USDT", "BCH/USDT", "LINK/USDT",
    "XLM/USDT", "SUI/USDT", "LTC/USDT", "AVAX/USDT", "HBAR/USDT",
    "SHIB/USDT", "DOT/USDT", "UNI/USDT", "TAO/USDT",
    "AAVE/USDT", "NEAR/USDT", "ICP/USDT", "ETC/USDT",
    "ONDO/USDT", "ENA/USDT", "POL/USDT", "WLD/USDT", "APT/USDT",
    "ATOM/USDT", "ALGO/USDT", "RENDER/USDT", "ARB/USDT", "FIL/USDT",
    "QNT/USDT", "VET/USDT", "SEI/USDT", "OP/USDT",
    "IMX/USDT", "INJ/USDT", "FET/USDT", "STX/USDT", "SAND/USDT",
    "MANA/USDT", "GRT/USDT", "THETA/USDT",
]
assert len(SYMBOLS) == 45, f"Expected 45 sym, got {len(SYMBOLS)}"

LOOKBACK = 100  # SHORT (regime_features.py LOOKBACK_SHORT=100)
N_INIT = 10  # spec productivo train_regime_model.py:199
MAX_ITER = 300
RANDOM_STATE = 42

MIN_EPISODE_BARS = 50  # regime_walk_forward.py:149
MIN_EPISODES_VALIDATE = 5  # regime_walk_forward.py:151

K_RANGE = list(range(2, 16))  # k=2..15


def load_features(symbol):
    sc = symbol.replace("/", "")
    path = os.path.join(CACHE_DIR, f"{sc}_{TIMEFRAME}.parquet")
    if not os.path.exists(path):
        return None, 0
    df = pd.read_parquet(path)
    if len(df) == 0:
        return None, 0
    if 'timestamp_ms' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    n_total = len(df)
    features, valid_mask = compute_regime_features(df, lookback=LOOKBACK)
    valid_features = features[valid_mask]
    return valid_features, n_total


def identify_episodes(cluster_labels, min_bars=MIN_EPISODE_BARS):
    n_bars = len(cluster_labels)
    episodes = defaultdict(list)
    if n_bars == 0:
        return dict(episodes)
    current_label = cluster_labels[0]
    ep_start = 0
    for i in range(1, n_bars):
        if cluster_labels[i] != current_label:
            if current_label >= 0:
                ep_len = i - ep_start
                if ep_len >= min_bars:
                    episodes[current_label].append((int(ep_start), int(i)))
            current_label = cluster_labels[i]
            ep_start = i
    if current_label >= 0:
        ep_len = n_bars - ep_start
        if ep_len >= min_bars:
            episodes[current_label].append((int(ep_start), int(n_bars)))
    return dict(episodes)


def categorize_history(n_valid):
    """Categorize symbol by history length (n_valid features post-LOOKBACK_LONG=1000)."""
    if n_valid >= 40000:
        return "amplio"  # BTC ETH BNB XRP-like ≥4.5y
    elif n_valid >= 15000:
        return "medio"   # 1.7-4.5y
    else:
        return "corto"   # <1.7y ONDO ENA-like


def main():
    output_dir = os.path.join(_ROOT, "n2_pre_parte3_results")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    incremental_path = os.path.join(output_dir, "n2_extended_alpha_bounded_INCREMENTAL.json")

    print(f"=== N.2 extended α-bounded — start {datetime.now().isoformat()} ===")
    print(f"K range: {K_RANGE[0]}..{K_RANGE[-1]} ({len(K_RANGE)} k values)")
    print(f"Symbols: {len(SYMBOLS)} (n_init={N_INIT}, max_iter={MAX_ITER})")
    print(f"Total fits: {len(SYMBOLS)} sym × {len(K_RANGE)} k = {len(SYMBOLS) * len(K_RANGE)}")

    t0 = time.time()
    per_sym_results = {}
    n_completed = 0
    n_skipped = 0

    for idx, sym in enumerate(SYMBOLS, 1):
        sym_t0 = time.time()
        print(f"\n[{idx}/{len(SYMBOLS)}] {sym} ...")

        valid_features, n_total = load_features(sym)
        if valid_features is None:
            print(f"[{idx}/{len(SYMBOLS)}] {sym}: SKIPPED (no parquet)")
            n_skipped += 1
            continue

        n_valid = len(valid_features)
        if n_valid < 15 * 50:  # need at least 750 valid bars for k=15
            print(f"[{idx}/{len(SYMBOLS)}] {sym}: SKIPPED (insufficient valid bars: {n_valid} < 750)")
            n_skipped += 1
            continue

        scaler = StandardScaler()
        X = scaler.fit_transform(valid_features)

        history_cat = categorize_history(n_valid)

        bic_values = {}
        n_clusters_valid_per_k = {}
        n_episodes_per_k = {}
        converged_per_k = {}

        for k in K_RANGE:
            try:
                gmm = GaussianMixture(
                    n_components=k, covariance_type='full',
                    n_init=N_INIT, random_state=RANDOM_STATE, max_iter=MAX_ITER
                )
                gmm.fit(X)
                bic = float(gmm.bic(X))
                bic_values[k] = bic
                converged_per_k[k] = bool(gmm.converged_)

                # Operability metrics
                labels = gmm.predict(X)
                episodes = identify_episodes(labels, min_bars=MIN_EPISODE_BARS)
                # Count clusters with ≥ MIN_EPISODES_VALIDATE episodes
                n_valid_clusters = sum(1 for c in range(k) if len(episodes.get(c, [])) >= MIN_EPISODES_VALIDATE)
                episodes_per_cluster = {c: len(episodes.get(c, [])) for c in range(k)}
                n_clusters_valid_per_k[k] = n_valid_clusters
                n_episodes_per_k[k] = episodes_per_cluster
            except Exception as e:
                bic_values[k] = None
                converged_per_k[k] = False
                n_clusters_valid_per_k[k] = None
                n_episodes_per_k[k] = None
                print(f"[{idx}/{len(SYMBOLS)}] {sym} k={k}: ERROR {type(e).__name__}: {e}")

        # k_optimal_BIC_extended
        valid_bics = {k: v for k, v in bic_values.items() if v is not None}
        if valid_bics:
            k_optimal_bic = min(valid_bics, key=valid_bics.get)
            best_bic = valid_bics[k_optimal_bic]
            second_best = min((v for k, v in valid_bics.items() if k != k_optimal_bic), default=None)
            bic_margin = (second_best - best_bic) if second_best is not None else None
        else:
            k_optimal_bic = None
            best_bic = None
            bic_margin = None

        # k_max_operable: max k where n_valid_clusters >= k * 0.5 (mayoría válidos)
        operability_classification = {}
        k_max_operable = None
        for k in K_RANGE:
            n_v = n_clusters_valid_per_k.get(k)
            if n_v is None:
                operability_classification[k] = None
                continue
            ratio = n_v / k
            if ratio >= 0.5:
                op_class = "VIABLE"
                k_max_operable = k
            elif ratio >= 0.3:
                op_class = "MARGINAL"
            else:
                op_class = "INFEASIBLE"
            operability_classification[k] = {"n_valid": n_v, "ratio": ratio, "class": op_class}

        # Gap analysis
        bic_vs_op_gap = (k_optimal_bic - k_max_operable) if (k_optimal_bic is not None and k_max_operable is not None) else None

        sym_elapsed = time.time() - sym_t0
        per_sym_results[sym] = {
            'n_bars_total': int(n_total),
            'n_valid_features': int(n_valid),
            'history_cat': history_cat,
            'bic_values': {str(k): v for k, v in bic_values.items()},
            'converged_per_k': {str(k): v for k, v in converged_per_k.items()},
            'n_clusters_valid_per_k': {str(k): v for k, v in n_clusters_valid_per_k.items()},
            'n_episodes_per_k': {str(k): v for k, v in n_episodes_per_k.items()},
            'operability_classification': {str(k): v for k, v in operability_classification.items()},
            'k_optimal_bic': k_optimal_bic,
            'best_bic': best_bic,
            'bic_margin_vs_second': bic_margin,
            'k_max_operable': k_max_operable,
            'bic_vs_op_gap': bic_vs_op_gap,
            'elapsed_seconds': sym_elapsed,
        }
        n_completed += 1
        bic_str = f"{best_bic:.1f}" if best_bic is not None else "N/A"
        margin_str = f"{bic_margin:.1f}" if bic_margin is not None else "N/A"
        op_str = f"k_max_op={k_max_operable}" if k_max_operable is not None else "k_max_op=NONE"
        print(f"[{idx}/{len(SYMBOLS)}] {sym} [{history_cat}, n_valid={n_valid}]: k_opt_bic={k_optimal_bic} BIC={bic_str} margin={margin_str} {op_str} gap={bic_vs_op_gap} elapsed={sym_elapsed:.1f}s")

        # Save incremental progress
        with open(incremental_path, 'w') as f:
            json.dump({
                'progress': f"{idx}/{len(SYMBOLS)}",
                'n_completed': n_completed,
                'n_skipped': n_skipped,
                'elapsed_seconds_so_far': time.time() - t0,
                'per_symbol': per_sym_results,
            }, f, indent=2)

    # ====================================================================
    # AGGREGATE ANALYSIS
    # ====================================================================
    elapsed_total = time.time() - t0

    # BIC k_optimal_extended distribution
    k_opt_bic_list = [r['k_optimal_bic'] for r in per_sym_results.values() if r['k_optimal_bic'] is not None]
    bic_distribution = {str(k): sum(1 for ki in k_opt_bic_list if ki == k) for k in K_RANGE}

    n_in_2_10 = sum(1 for k in k_opt_bic_list if 2 <= k <= 10)
    n_in_11_14 = sum(1 for k in k_opt_bic_list if 11 <= k <= 14)
    n_at_15 = sum(1 for k in k_opt_bic_list if k == 15)

    # Outcome categorization extended
    n_total_ko = len(k_opt_bic_list)
    if n_at_15 / n_total_ko > 0.5 if n_total_ko > 0 else False:
        bic_outcome = "Outcome_overfit_ALERT"
        bic_outcome_desc = f"{n_at_15}/{n_total_ko} sym k_opt=15 (>50% truncation persistente) — RED FLAG potential overfitting OR pre-pass adicional k=16..20 escalación Ricardo"
    elif n_in_2_10 == n_total_ko:
        bic_outcome = "Outcome_B_refined_within_original"
        bic_outcome_desc = f"{n_in_2_10}/{n_total_ko} sym k_opt en [2..10] — knee genuino dentro original sweep, N.2.2 robust"
    elif n_in_11_14 + n_in_2_10 == n_total_ko:
        bic_outcome = "Outcome_B_refined_extended"
        bic_outcome_desc = f"{n_in_2_10} en [2..10] + {n_in_11_14} en [11..14] — knee genuino emerge upper extension"
    else:
        bic_outcome = "Outcome_mixed"
        bic_outcome_desc = f"{n_in_2_10} en [2..10] + {n_in_11_14} en [11..14] + {n_at_15} at k=15 — mixed truncation"

    # Operability k_max_operable distribution
    k_max_op_list = [r['k_max_operable'] for r in per_sym_results.values() if r['k_max_operable'] is not None]
    op_distribution = {str(k): sum(1 for ki in k_max_op_list if ki == k) for k in K_RANGE}

    # By history category
    by_history = {"amplio": [], "medio": [], "corto": []}
    for sym, r in per_sym_results.items():
        cat = r['history_cat']
        by_history[cat].append({
            'sym': sym,
            'n_valid': r['n_valid_features'],
            'k_opt_bic': r['k_optimal_bic'],
            'k_max_operable': r['k_max_operable'],
            'gap': r['bic_vs_op_gap'],
        })

    # Outcome_C per-symbol adaptive viability
    # Coherent: histórico amplio sustains higher k_max_operable than histórico corto
    amplio_max_ops = [s['k_max_operable'] for s in by_history['amplio'] if s['k_max_operable'] is not None]
    corto_max_ops = [s['k_max_operable'] for s in by_history['corto'] if s['k_max_operable'] is not None]
    medio_max_ops = [s['k_max_operable'] for s in by_history['medio'] if s['k_max_operable'] is not None]

    if amplio_max_ops and corto_max_ops:
        amplio_median_op = np.median(amplio_max_ops)
        corto_median_op = np.median(corto_max_ops)
        op_gap_amplio_corto = amplio_median_op - corto_median_op
        outcome_c_viable = (op_gap_amplio_corto >= 2)  # ≥2 cluster gap = substantial
    else:
        amplio_median_op = None
        corto_median_op = None
        op_gap_amplio_corto = None
        outcome_c_viable = False

    print(f"\n{'='*70}")
    print(f"=== N.2 extended α-bounded — DONE elapsed={elapsed_total:.1f}s ({elapsed_total/60:.1f} min) ===")
    print(f"n_completed={n_completed}/{len(SYMBOLS)} (skipped={n_skipped})")
    print(f"\nBIC outcome: {bic_outcome}")
    print(f"  {bic_outcome_desc}")
    print(f"\nBIC k_optimal_extended distribution: {bic_distribution}")
    print(f"  in [2..10]: {n_in_2_10}/{n_total_ko}")
    print(f"  in [11..14]: {n_in_11_14}/{n_total_ko}")
    print(f"  at k=15: {n_at_15}/{n_total_ko}")
    print(f"\nOperability k_max_operable distribution: {op_distribution}")
    print(f"  amplio (n_valid≥40K): median k_max_op = {amplio_median_op}")
    print(f"  medio (15K≤n_valid<40K): median k_max_op = {np.median(medio_max_ops) if medio_max_ops else None}")
    print(f"  corto (n_valid<15K): median k_max_op = {corto_median_op}")
    print(f"\nOutcome_C per-symbol adaptive viable: {outcome_c_viable}")
    print(f"  amplio↔corto operability gap: {op_gap_amplio_corto}")

    # Save full results
    bic_path = os.path.join(output_dir, f"n2_extended_alpha_bounded_{timestamp}.json")
    summary = {
        'timestamp': timestamp,
        'k_range': K_RANGE,
        'n_init': N_INIT,
        'symbols_total': len(SYMBOLS),
        'n_completed': n_completed,
        'n_skipped': n_skipped,
        'elapsed_seconds': elapsed_total,
        'bic_outcome': bic_outcome,
        'bic_outcome_desc': bic_outcome_desc,
        'bic_distribution': bic_distribution,
        'bic_k_opt_in_2_10': n_in_2_10,
        'bic_k_opt_in_11_14': n_in_11_14,
        'bic_k_opt_at_15': n_at_15,
        'operability_distribution': op_distribution,
        'amplio_median_k_max_op': float(amplio_median_op) if amplio_median_op is not None else None,
        'corto_median_k_max_op': float(corto_median_op) if corto_median_op is not None else None,
        'medio_median_k_max_op': float(np.median(medio_max_ops)) if medio_max_ops else None,
        'op_gap_amplio_corto': float(op_gap_amplio_corto) if op_gap_amplio_corto is not None else None,
        'outcome_c_per_sym_adaptive_viable': bool(outcome_c_viable),
        'by_history': by_history,
        'per_symbol': per_sym_results,
    }
    with open(bic_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OUTPUT] {bic_path}")

    # Pointer file
    latest_path = os.path.join(output_dir, "LATEST_EXTENDED.json")
    with open(latest_path, 'w') as f:
        json.dump({'timestamp': timestamp, 'path': bic_path,
                   'bic_outcome': bic_outcome, 'outcome_c_viable': bool(outcome_c_viable)}, f, indent=2)


if __name__ == "__main__":
    main()
