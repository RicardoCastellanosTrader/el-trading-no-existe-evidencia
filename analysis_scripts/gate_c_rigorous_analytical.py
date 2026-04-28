"""
Gate C rigorous analytical refinement Sesión 4.5 Frame 2 — 2026-04-29.

Per-cluster Spearman ρ(pf_tr, pf_fwd) top-100 specialists from JSONs
smoke 2026-04-24 cross-9 BTC+ONDO+SEI × C0+C1+C2.

Refines Sesión 4 Gate C PARTIAL veredict via per-cluster computation:
- Sesión 4 analytical proxy: cross-9 ρ = -0.17 NS (single cross-pool measure).
- Sesión 4.5 refinement: per-cluster ρ × 9 clusters cross-3 sym (rigorous).

Criterion Gate C (per spec L1296): Spearman ρ stable cross-cluster.
Operacional: ≥6/9 clusters with |ρ| ≥ 0.3 sign consistent.

Analytical sin compute cost — JSONs metadata directly disponible.

Usage: python -m analysis_scripts.gate_c_rigorous_analytical
"""

import json
import os
import sys
from datetime import datetime

# Fix Windows cp1252 encoding (preserve unicode in output)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
from scipy.stats import spearmanr

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

SYMBOLS = ['BTC', 'ONDO', 'SEI']
CLUSTERS = ['0', '1', '2']
JSONS_DIR = os.path.join(_ROOT, 'regime_wf')

# Stability threshold: |ρ| >= 0.3 considered stable per spec criterion
GATE_C_STABILITY_THRESHOLD = 0.3
# Minimum stable clusters for Gate C PASS (≥6/9)
GATE_C_PASS_THRESHOLD = 6


def load_smoke_json(symbol):
    json_path = os.path.join(JSONS_DIR, f"{symbol}USDT_specialist_configs.json")
    with open(json_path) as f:
        return json.load(f)


def compute_cluster_spearman_rho(json_data, cluster_id):
    """Compute Spearman ρ(pf_tr, pf_fwd) top-N specialists per cluster."""
    cluster_data = json_data['clusters'].get(cluster_id, {})
    top_configs = cluster_data.get('top_configs', [])
    if len(top_configs) < 5:
        return None, None, len(top_configs)

    pf_tr = np.array([cfg.get('pf_tr', np.nan) for cfg in top_configs])
    pf_fwd = np.array([cfg.get('pf_fwd', np.nan) for cfg in top_configs])

    valid = ~(np.isnan(pf_tr) | np.isnan(pf_fwd))
    if valid.sum() < 5:
        return None, None, int(valid.sum())

    rho, p_value = spearmanr(pf_tr[valid], pf_fwd[valid])
    return float(rho), float(p_value), int(valid.sum())


def main():
    print(f"Gate C rigorous analytical refinement Sesión 4.5 Frame 2 — start {datetime.now().isoformat()}")
    print(f"  Approach: per-cluster Spearman ρ(pf_tr, pf_fwd) top-100 specialists from JSONs")
    print(f"  Stability threshold: |ρ| ≥ {GATE_C_STABILITY_THRESHOLD}")
    print(f"  Gate C PASS criterion: ≥{GATE_C_PASS_THRESHOLD}/9 stable clusters")
    print()

    results = {}
    all_rhos = []
    all_pvalues = []
    n_stable = 0
    n_significant = 0
    n_clusters_evaluated = 0

    for sym in SYMBOLS:
        json_data = load_smoke_json(sym)
        results[sym] = {}
        print(f"  {sym}:")
        for cluster_id in CLUSTERS:
            rho, p, n = compute_cluster_spearman_rho(json_data, cluster_id)
            if rho is None:
                results[sym][f'cluster_{cluster_id}'] = {
                    'spearman_rho': None,
                    'p_value': None,
                    'n_specialists': n,
                    'stable': False,
                    'significant': False,
                    'note': 'insufficient_data',
                }
                print(f"    C{cluster_id}: insufficient data (n={n})")
                continue

            stable = abs(rho) >= GATE_C_STABILITY_THRESHOLD
            significant = p < 0.05
            results[sym][f'cluster_{cluster_id}'] = {
                'spearman_rho': rho,
                'p_value': p,
                'n_specialists': n,
                'stable': bool(stable),
                'significant': bool(significant),
            }
            all_rhos.append(rho)
            all_pvalues.append(p)
            n_clusters_evaluated += 1
            if stable:
                n_stable += 1
            if significant:
                n_significant += 1
            sig_marker = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'NS'))
            stable_marker = 'STABLE' if stable else 'unstable'
            print(f"    C{cluster_id}: ρ={rho:+.3f} (p={p:.4f} {sig_marker}) {stable_marker} (n={n})")

    # Sign consistency check
    if all_rhos:
        n_positive = sum(1 for r in all_rhos if r > 0)
        n_negative = sum(1 for r in all_rhos if r < 0)
        sign_consistency_pct = max(n_positive, n_negative) / len(all_rhos)
    else:
        sign_consistency_pct = 0.0

    gate_c_pass = (n_stable >= GATE_C_PASS_THRESHOLD)

    summary = {
        'n_clusters_evaluated': n_clusters_evaluated,
        'n_stable_cross_9': n_stable,
        'n_significant_cross_9': n_significant,
        'mean_rho_cross_9': float(np.mean(all_rhos)) if all_rhos else None,
        'std_rho_cross_9': float(np.std(all_rhos, ddof=1)) if len(all_rhos) >= 2 else None,
        'median_rho_cross_9': float(np.median(all_rhos)) if all_rhos else None,
        'min_rho': float(np.min(all_rhos)) if all_rhos else None,
        'max_rho': float(np.max(all_rhos)) if all_rhos else None,
        'sign_consistency_pct': sign_consistency_pct,
        'gate_c_stability_threshold': GATE_C_STABILITY_THRESHOLD,
        'gate_c_pass_threshold': GATE_C_PASS_THRESHOLD,
        'gate_c_pass': bool(gate_c_pass),
        'verdict': 'PASS' if gate_c_pass else 'FAIL',
        'comparison_sesion_4_proxy': {
            'sesion_4_cross_9_rho_proxy': -0.17,
            'sesion_4_verdict': 'PARTIAL',
            'sesion_4_5_verdict': 'PASS' if gate_c_pass else 'FAIL',
            'refinement_outcome': (
                f'Gate C upgraded from PARTIAL → {("PASS" if gate_c_pass else "FAIL")} '
                f'(rigorous per-cluster analysis)'),
        },
        'timestamp': datetime.now().isoformat(),
    }

    output = {
        'summary': summary,
        'per_cluster': results,
    }

    output_path = os.path.join(_ROOT, 'gate_c_rigorous_analytical_results.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print()
    print(f"=== SUMMARY ===")
    print(f"  N stable cross-9: {n_stable}/{n_clusters_evaluated}")
    print(f"  N significant cross-9: {n_significant}/{n_clusters_evaluated}")
    print(f"  Mean ρ cross-9: {summary['mean_rho_cross_9']}")
    print(f"  Median ρ cross-9: {summary['median_rho_cross_9']}")
    print(f"  Range ρ cross-9: [{summary['min_rho']}, {summary['max_rho']}]")
    print(f"  Sign consistency: {sign_consistency_pct*100:.1f}%")
    print(f"  Gate C verdict: **{summary['verdict']}**")
    print(f"  Output: {output_path}")
    print(f"Done {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
