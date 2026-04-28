"""
R1 DSR rigurosa Sesión 2.5 Frame 2 — dry-run cross-3 standalone script.

Carga JSONs smoke 2026-04-24 cross-3 BTC+ONDO+SEI + aplica DSR sobre
synthetic returns reconstruidos desde aggregates per config (pattern
Multi-testing Caso B archive precedent 2026-04-26 — in-memory dry-run
sin kernel re-run).

Synthetic returns reconstruction:
  Para cada config con pf_fwd + trades_fwd + wins_fwd + pnl_fwd:
    gl = pnl_fwd / (pf_fwd - 1) si pf_fwd != 1
    gp = pnl_fwd × pf_fwd / (pf_fwd - 1)
    avg_win = gp / wins_fwd
    avg_loss = -gl / (trades_fwd - wins_fwd)
    returns = [avg_win] × wins + [avg_loss] × losses

Caveat: synthetic distribution uniforme (todos wins = avg_win, todos losses
= avg_loss). NO captura dispersión intra-grupo. Skew/kurt computed son
SIMPLISTAS vs real per-trade distribution. Pattern análogo W3 bootstrap
caveat — same trade-off (Multi-testing Caso B precedent acceptable for
empirical validation H1 magnitude top-1 changes).

Output: dsr_dry_run_cross_3_results.json con per-cluster:
- top-1 W3b JSON original (specialist_score_ci_low — current JSON order).
- top-1 M2 fix re-ranked (pf_fwd_ci_low).
- top-1 DSR hybrid (pf_fwd_ci_low + dsr_zscore tie-breaker).
- DSR distribution stats per cluster.
- ONDO C0 canonical §12 L29 case detection.
- Cross-9 summary: total top-1 changes DSR vs M2.

Usage: python -m analysis_scripts.dsr_dry_run_cross_3
"""

import json
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_walk_forward import (
    _compute_dsr_zscore_rigorous,
    _DSR_FLAG_PVALUE_THRESHOLD,
)


SYMBOLS = ['BTC', 'ONDO', 'SEI']
JSONS_DIR = os.path.join(_ROOT, 'regime_wf')
TOP_N = 100  # survivors per cluster from JSON

# Conservative N upstream estimate per cluster (~kernel sweep cost).
# JSON not contain n_configs_evaluated_upstream directly — use conservative.
# Per kernel sweep typically ~1-4M configs × variants ÷ clusters. Use 1M default.
N_CONFIGS_TESTED_UPSTREAM = 1_000_000


def synthetic_returns_from_aggregates(pf_fwd, trades_fwd, pnl_fwd, wins_fwd=None):
    """Reconstruct synthetic per-trade returns from JSON aggregates.

    JSON smoke 2026-04-24 NO incluye wins_fwd directamente. Estimación:
        wins ≈ round(trades × pf / (1 + pf)) (assuming avg_win ≈ |avg_loss|).

    Once wins/losses split estimated:
        gp = pnl × pf / (pf - 1)  (derived from pf = gp/gl, pnl = gp - gl)
        gl = pnl / (pf - 1)
        avg_win = gp / wins (positive)
        avg_loss = -gl / losses (negative)

    Returns synthetic returns array (uniform avg_win × N_wins +
    avg_loss × N_losses). Caveat: skew/kurt simplistas (uniform binary
    distribution).

    Pattern Multi-testing Caso B precedent + W3 bootstrap caveat.
    """
    if pf_fwd is None or trades_fwd is None or pnl_fwd is None:
        return np.array([])
    if trades_fwd < 3:
        return np.array([])
    if pf_fwd <= 0 or abs(pf_fwd - 1.0) < 1e-6:
        # PF <= 0 invalid; PF = 1 → gp = gl, pnl = 0, can't determine magnitudes
        return np.array([])

    # Estimate wins from pf assuming avg_win ≈ |avg_loss| magnitude
    if wins_fwd is None:
        wins_estimate = int(round(trades_fwd * pf_fwd / (1.0 + pf_fwd)))
        # Bound wins to [1, trades_fwd - 1] (need at least 1 win and 1 loss)
        wins_estimate = max(1, min(trades_fwd - 1, wins_estimate))
    else:
        wins_estimate = int(wins_fwd)
        if wins_estimate <= 0 or wins_estimate >= trades_fwd:
            return np.array([])

    losses_n = trades_fwd - wins_estimate
    # gl = pnl / (pf - 1), gp = gl × pf
    if pf_fwd > 1.0:
        gl = pnl_fwd / (pf_fwd - 1.0)
    else:
        # pf < 1 → losing strategy, pnl_fwd should be negative
        # gl = -pnl / (1 - pf), gp = gl × pf
        gl = -pnl_fwd / (1.0 - pf_fwd)
    gp = gl * pf_fwd
    if gp <= 0 or gl <= 0:
        return np.array([])

    avg_win = gp / wins_estimate
    avg_loss = -gl / losses_n
    returns = np.concatenate([
        np.full(wins_estimate, avg_win),
        np.full(losses_n, avg_loss),
    ])
    return returns


def load_smoke_json(symbol):
    """Load smoke 2026-04-24 specialist_configs.json for symbol."""
    json_path = os.path.join(JSONS_DIR, f"{symbol}USDT_specialist_configs.json")
    with open(json_path) as f:
        return json.load(f)


def compute_dsr_per_cluster(json_data, symbol, n_upstream):
    """Apply DSR to top-N configs per cluster.

    Returns dict {cluster_id_str: DataFrame}.
    """
    out = {}
    for cluster_id_str, cluster_data in json_data['clusters'].items():
        top_configs = cluster_data.get('top_configs', [])[:TOP_N]
        if not top_configs:
            out[cluster_id_str] = pd.DataFrame()
            continue

        df = pd.DataFrame(top_configs)
        # Add JSON original order as 'rank_w3b' (1-indexed)
        df['rank_w3b'] = np.arange(1, len(df) + 1)

        # Synthesize returns + compute DSR per row
        dsr_z = np.full(len(df), np.nan, dtype=np.float64)
        dsr_p = np.full(len(df), np.nan, dtype=np.float64)
        flagged = np.ones(len(df), dtype=bool)

        for i, row in df.iterrows():
            returns = synthetic_returns_from_aggregates(
                pf_fwd=row.get('pf_fwd'),
                trades_fwd=row.get('trades_fwd'),
                pnl_fwd=row.get('pnl_fwd'),
                wins_fwd=row.get('wins_fwd'),  # may be None (JSON smoke)
            )
            if len(returns) >= 3:
                z, p, f = _compute_dsr_zscore_rigorous(returns, n_upstream)
                dsr_z[i] = z
                dsr_p[i] = p
                flagged[i] = f

        df['dsr_zscore'] = dsr_z
        df['dsr_pvalue'] = dsr_p
        df['flagged_dsr'] = flagged
        out[cluster_id_str] = df

    return out


def compare_top_1(df_cluster):
    """Compare top-1 across W3b JSON / M2 fix / DSR hybrid sorts."""
    if len(df_cluster) == 0:
        return None
    # W3b JSON original (current order, top index 0)
    top_1_w3b = int(df_cluster.iloc[0]['config_id'])

    # M2 fix baseline: re-sort by pf_fwd_ci_low (descending)
    df_m2 = df_cluster.sort_values('pf_fwd_ci_low', ascending=False)
    top_1_m2 = int(df_m2.iloc[0]['config_id'])

    # DSR hybrid: re-sort by [pf_fwd_ci_low, dsr_zscore]
    df_dsr = df_cluster.sort_values(
        ['pf_fwd_ci_low', 'dsr_zscore'], ascending=[False, False]
    )
    top_1_dsr = int(df_dsr.iloc[0]['config_id'])

    return {
        'w3b_top_1': top_1_w3b,
        'm2_top_1': top_1_m2,
        'dsr_top_1': top_1_dsr,
        'm2_changed_vs_w3b': top_1_m2 != top_1_w3b,
        'dsr_changed_vs_m2': top_1_dsr != top_1_m2,
        'dsr_changed_vs_w3b': top_1_dsr != top_1_w3b,
    }


def cluster_stats(df_cluster):
    if len(df_cluster) == 0:
        return {}
    valid_mask = ~df_cluster['dsr_zscore'].isna()
    n_valid = int(valid_mask.sum())
    n_total = len(df_cluster)
    return {
        'n_total': n_total,
        'n_dsr_valid': n_valid,
        'flagged_dsr_count': int(df_cluster['flagged_dsr'].sum()),
        'flagged_dsr_pct': float(df_cluster['flagged_dsr'].mean()),
        'dsr_zscore_mean': (float(df_cluster.loc[valid_mask, 'dsr_zscore'].mean())
                            if n_valid > 0 else None),
        'dsr_zscore_std': (float(df_cluster.loc[valid_mask, 'dsr_zscore'].std())
                           if n_valid > 1 else None),
        'dsr_zscore_median': (float(df_cluster.loc[valid_mask, 'dsr_zscore'].median())
                              if n_valid > 0 else None),
        'dsr_pvalue_median': (float(df_cluster.loc[valid_mask, 'dsr_pvalue'].median())
                              if n_valid > 0 else None),
    }


def main():
    print(f"R1 DSR dry-run cross-3 BTC+ONDO+SEI start {datetime.now().isoformat()}")
    print(f"  Approach: synthetic returns from JSON aggregates (Multi-testing Caso B pattern)")
    print(f"  N_upstream conservative: {N_CONFIGS_TESTED_UPSTREAM}")
    print(f"  TOP_N per cluster: {TOP_N}")

    all_results = {}

    for symbol in SYMBOLS:
        print(f"\nProcessing {symbol}...")
        json_data = load_smoke_json(symbol)
        clusters = compute_dsr_per_cluster(json_data, symbol,
                                             N_CONFIGS_TESTED_UPSTREAM)

        all_results[symbol] = {}
        for cluster_id_str, df in clusters.items():
            comp = compare_top_1(df)
            stats = cluster_stats(df)
            all_results[symbol][f'cluster_{cluster_id_str}'] = {
                'comparison': comp,
                'stats': stats,
            }
            if comp:
                print(f"  C{cluster_id_str}: w3b={comp['w3b_top_1']}, "
                      f"m2={comp['m2_top_1']}, dsr={comp['dsr_top_1']}; "
                      f"flagged={stats['flagged_dsr_count']}/{stats['n_total']} "
                      f"({stats['flagged_dsr_pct']*100:.1f}%); "
                      f"z_median={stats.get('dsr_zscore_median')}")

    # Aggregate cross-9 summary
    total_dsr_vs_m2 = 0
    total_dsr_vs_w3b = 0
    total_m2_vs_w3b = 0
    flagged_pcts = []
    n_clusters_with_data = 0

    for sym in SYMBOLS:
        for c in ['0', '1', '2']:
            entry = all_results[sym].get(f'cluster_{c}', {})
            comp = entry.get('comparison')
            stats = entry.get('stats', {})
            if comp:
                total_dsr_vs_m2 += int(comp['dsr_changed_vs_m2'])
                total_dsr_vs_w3b += int(comp['dsr_changed_vs_w3b'])
                total_m2_vs_w3b += int(comp['m2_changed_vs_w3b'])
                n_clusters_with_data += 1
                flagged_pcts.append(stats.get('flagged_dsr_pct', 0.0))

    summary = {
        'n_clusters_evaluated': n_clusters_with_data,
        'total_top_1_changes_dsr_vs_m2': total_dsr_vs_m2,
        'total_top_1_changes_dsr_vs_w3b': total_dsr_vs_w3b,
        'total_top_1_changes_m2_vs_w3b': total_m2_vs_w3b,
        'pct_changes_dsr_vs_m2': (
            total_dsr_vs_m2 / n_clusters_with_data
            if n_clusters_with_data else 0.0),
        'mean_flagged_dsr_pct_cross_clusters': (
            float(np.mean(flagged_pcts)) if flagged_pcts else 0.0),
        'timestamp': datetime.now().isoformat(),
        'methodology': {
            'approach': 'synthetic_returns_from_json_aggregates',
            'precedent': 'Multi-testing Caso B archive 2026-04-26',
            'top_n_per_cluster': TOP_N,
            'n_configs_tested_upstream_conservative': N_CONFIGS_TESTED_UPSTREAM,
            'caveat': ('synthetic uniform avg_win/avg_loss → skew/kurt simplistas; '
                        'rigorous per-trade returns kernel re-run deferred to reciclaje real'),
        },
    }

    output = {
        'summary': summary,
        'per_cluster': all_results,
    }

    output_path = os.path.join(_ROOT, 'dsr_dry_run_cross_3_results.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n=== SUMMARY ===")
    print(f"  Clusters evaluated: {n_clusters_with_data}/9")
    print(f"  Top-1 changes DSR vs M2 fix: {total_dsr_vs_m2}/{n_clusters_with_data} "
          f"({summary['pct_changes_dsr_vs_m2']*100:.1f}%)")
    print(f"  Top-1 changes M2 fix vs W3b JSON: {total_m2_vs_w3b}/{n_clusters_with_data}")
    print(f"  Top-1 changes DSR vs W3b JSON: {total_dsr_vs_w3b}/{n_clusters_with_data}")
    print(f"  Mean flagged_dsr cross-clusters: {summary['mean_flagged_dsr_pct_cross_clusters']*100:.1f}%")

    # ONDO C0 canonical §12 L29 case
    ondo_c0 = all_results.get('ONDO', {}).get('cluster_0', {})
    if ondo_c0:
        print(f"\n  ONDO C0 canonical case (§12 L29):")
        print(f"    comparison: {ondo_c0['comparison']}")
        print(f"    stats: {ondo_c0['stats']}")

    print(f"\n  Output: {output_path}")
    print(f"Done {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
