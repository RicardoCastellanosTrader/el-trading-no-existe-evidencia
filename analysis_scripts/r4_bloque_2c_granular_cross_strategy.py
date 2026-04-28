"""
R4 Bloque 2c granular cross-strategy decomposition Sesión 3 Frame 2 — 2026-04-29.

Standalone script JSONs-based + kernel re-run Path γ flag=True (Sesión 2.5
Opción C precedent reusable). Hipótesis testables R4:

H_strategy granular cross-strategy:
  TF cancel_tf vs MR cancel_zona/cancel_tf/cancel_ghost per-trade reasons
  distribution. Hipótesis: TF strategy-logic cancellations diferentes
  distribución performance vs MR cross-pair structural cancellations.

H1 short/long asimetría granular:
  pt_side per-trade. Hipótesis: short/long performance asimetría cross-cluster.

H_funding aligned/contrarian — DEFERRED Sesión 3 R4 (funding cache cobertura
2026-03-01 → 2026-04-26 ~2 meses vs kernel runs sobre historical full range
~2-3 años → statistical power LOW). Documented caveat. Reactivable post-
reciclaje con extended funding cache.

Approach:
  1. Load JSONs cross-3 BTC+ONDO+SEI smoke 2026-04-24.
  2. Top-3 per cluster sorted by pf_fwd_ci_low (post-M2-fix order).
  3. Group configs by preset variant (lookup preset CSV by name).
  4. Per (sym, preset_variant): precalculate_all_data + kernel re-run
     Path γ flag=True con subset configs.
  5. Extract per-trade arrays granular (pt_pnl, pt_reason, pt_side).
  6. Aggregate per cluster + per hypothesis.
  7. Output r4_dry_run_cross_3_results.json.

Pattern Sesión 2.5 Opción C reusable + Path γ Sesión 2 enabled per-trade
arrays granular (TF 6 valores + MR 8 valores asimétrico).

Usage: python -m analysis_scripts.r4_bloque_2c_granular_cross_strategy
"""

import json
import os
import re
import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_walk_forward import (
    load_full_history, load_regime_model, compute_cluster_labels,
    compute_gmm_probs, identify_episodes, build_regime_labels,
    load_presets,
)

import lab_historico_numba_v8_3 as _lab


SYMBOLS = ['BTC', 'ONDO', 'SEI']
JSONS_DIR = os.path.join(_ROOT, 'regime_wf')
PRESETS_DIR = os.path.join(_ROOT, 'output', 'production')
TOP_N_PER_CLUSTER = 3  # top-3 by pf_fwd_ci_low (M2 fix order)
MAX_TRADES_PER_CONFIG = 1000
TRAIN_RATIO = 0.70
MIN_EPISODE_BARS = 50

# Path γ TF reason_exit enum (lab_historico_numba_v8_3.py)
TF_REASON_LABELS = {
    0: 'sl_hit',
    1: 'sl_emergency',
    2: 'div_exit',
    3: 'tf_exit',
    4: 'zone_exit',
    5: 'cancel_tf',
}


def parse_preset_label(label):
    """Parse preset_label 'ALMA(24)/SMA(57)_H00' → (fast_type, fast_p, slow_type, slow_p, hyst_mult)."""
    m = re.match(r'(\w+)\((\d+)\)/(\w+)\((\d+)\)_H(\d+)', label)
    if not m:
        return None
    fast_type, fast_p, slow_type, slow_p, hyst_str = m.groups()
    hyst_mult = float(hyst_str) / 10.0  # 'H00' → 0.0, 'H05' → 0.5
    return (fast_type, int(fast_p), slow_type, int(slow_p), hyst_mult)


def find_preset_tuple(presets_list, fast_type, fast_p, slow_type, slow_p):
    """Find preset tuple matching (fast_type, fast_p, slow_type, slow_p) from presets CSV list."""
    for p in presets_list:
        if (p[0] == fast_type and int(p[1]) == fast_p
            and p[4] == slow_type and int(p[5]) == slow_p):
            return p
    return None


def load_smoke_json(symbol):
    json_path = os.path.join(JSONS_DIR, f"{symbol}USDT_specialist_configs.json")
    with open(json_path) as f:
        return json.load(f)


def gather_top_n_per_cluster(json_data, n=TOP_N_PER_CLUSTER):
    """Top-N configs per cluster sorted by pf_fwd_ci_low (M2 fix order).

    Returns list of (cluster_id_str, config_dict) tuples.
    """
    out = []
    for cluster_id_str, cluster_data in json_data['clusters'].items():
        top_configs = cluster_data.get('top_configs', [])
        if not top_configs:
            continue
        df = pd.DataFrame(top_configs)
        df_sorted = df.sort_values('pf_fwd_ci_low', ascending=False).head(n)
        for _, row in df_sorted.iterrows():
            out.append((cluster_id_str, row.to_dict()))
    return out


def kernel_rerun_per_variant(symbol, preset_tuple, hyst_mult, configs_subset,
                              df_ohlcv, regime_labels, n_doubled, max_trades):
    """Run kernel TF Path γ flag=True con subset configs over preset+hyst variant.

    Returns per_trade dict {config_idx_local: {pnl, reason, side, entry_bar, exit_bar}}.
    """
    data = _lab.precalculate_all_data(df_ohlcv, preset=preset_tuple,
                                        hyst_mult=hyst_mult, symbol=f"{symbol}/USDT")

    n_configs = len(configs_subset)
    pt_entry_bar = np.zeros((n_configs, max_trades), dtype=np.int32)
    pt_exit_bar = np.zeros((n_configs, max_trades), dtype=np.int32)
    pt_side = np.zeros((n_configs, max_trades), dtype=np.int8)
    pt_pnl = np.zeros((n_configs, max_trades), dtype=np.float64)
    pt_reason = np.zeros((n_configs, max_trades), dtype=np.int8)
    pt_cluster = np.zeros((n_configs, max_trades), dtype=np.int8)
    pt_entry_price = np.zeros((n_configs, max_trades), dtype=np.float64)
    pt_exit_price = np.zeros((n_configs, max_trades), dtype=np.float64)
    pt_count = np.zeros(n_configs, dtype=np.int32)

    _lab.run_on_slice(
        np.asarray(configs_subset, dtype=np.uint32),
        data, 0, len(data['close']),
        _lab.SL_PERCENT, _lab.SL_EMERGENCY_PERCENT, _lab.TS_PERCENT,
        _lab.COOLDOWN_BARS, _lab.COMMISSION_ROUND_TRIP,
        cluster_labels=regime_labels, n_clusters=n_doubled,
        return_per_trade=True,
        pt_entry_bar=pt_entry_bar, pt_exit_bar=pt_exit_bar,
        pt_side=pt_side, pt_pnl=pt_pnl, pt_reason=pt_reason,
        pt_cluster=pt_cluster,
        pt_count=pt_count,
        pt_entry_price=pt_entry_price, pt_exit_price=pt_exit_price,
    )

    per_trade_data = {}
    for c in range(n_configs):
        n_t = int(pt_count[c])
        if n_t < 1:
            continue
        per_trade_data[c] = {
            'pnl': pt_pnl[c, :n_t].copy(),
            'reason': pt_reason[c, :n_t].copy(),
            'side': pt_side[c, :n_t].copy(),
            'entry_bar': pt_entry_bar[c, :n_t].copy(),
            'exit_bar': pt_exit_bar[c, :n_t].copy(),
            'cluster': pt_cluster[c, :n_t].copy(),
        }
    return per_trade_data


def aggregate_per_cluster_per_specialist(symbol, top_n_data, df_ohlcv,
                                          regime_labels, n_doubled, presets_list):
    """Group top-N configs by preset variant + run kernel re-run + extract per-trade.

    top_n_data: list of (cluster_id_str, config_dict) tuples.
    Returns dict {cluster_id_str: list of per-trade dicts per specialist}.
    """
    # Group by preset variant
    variants = {}  # {(preset_label, hyst_mult): [(cluster_id_str, config_dict), ...]}
    for cid, cfg in top_n_data:
        label = cfg.get('preset')
        parsed = parse_preset_label(label)
        if parsed is None:
            print(f"  ⚠️  Could not parse preset_label: {label}")
            continue
        fast_type, fast_p, slow_type, slow_p, hyst_mult = parsed
        preset_tuple = find_preset_tuple(presets_list, fast_type, fast_p,
                                          slow_type, slow_p)
        if preset_tuple is None:
            print(f"  ⚠️  Preset {label} NOT in CSV — skipping config {cfg.get('config_id')}")
            continue
        key = (label, hyst_mult, preset_tuple)
        if key not in variants:
            variants[key] = []
        variants[key].append((cid, cfg))

    print(f"  {symbol}: {len(top_n_data)} top-N configs grouped into {len(variants)} unique variants")

    # Run kernel per variant + aggregate per specialist
    per_cluster = {'0': [], '1': [], '2': []}
    for (label, hyst_mult, preset_tuple), config_list in variants.items():
        config_ids = [int(c[1]['config_id']) for c in config_list]
        print(f"    variant '{label}' (hyst={hyst_mult}): {len(config_ids)} configs kernel re-run...")
        t0 = time.time()
        per_trade = kernel_rerun_per_variant(
            symbol, preset_tuple, hyst_mult, config_ids,
            df_ohlcv, regime_labels, n_doubled, MAX_TRADES_PER_CONFIG,
        )
        print(f"      done in {time.time() - t0:.1f}s")

        # Map back per-trade data to cluster_id
        for local_idx, (cid, cfg) in enumerate(config_list):
            if local_idx in per_trade:
                pt = per_trade[local_idx]
                # Filter to trades where pt_cluster matches cid (train k or fwd k+K)
                target_cluster_train = int(cid)
                target_cluster_fwd = int(cid) + 3  # n_clusters_base = 3
                cluster_arr = pt['cluster']
                mask = (cluster_arr == target_cluster_train) | (cluster_arr == target_cluster_fwd)
                n_filtered = int(mask.sum())
                if n_filtered < 1:
                    continue
                specialist_data = {
                    'config_id': int(cfg['config_id']),
                    'preset': label,
                    'pf_fwd': cfg.get('pf_fwd'),
                    'pf_fwd_ci_low': cfg.get('pf_fwd_ci_low'),
                    'trades_fwd_json': cfg.get('trades_fwd'),
                    'pnl_array': pt['pnl'][mask].tolist(),
                    'reason_array': pt['reason'][mask].tolist(),
                    'side_array': pt['side'][mask].tolist(),
                    'n_trades_kernel_filtered': n_filtered,
                }
                per_cluster[cid].append(specialist_data)

    return per_cluster


def compute_h_strategy_aggregation(per_cluster_data):
    """H_strategy: distribution pt_reason per cluster + PnL per reason category.

    Returns dict {cluster_id: {reason_label: {n_trades, mean_pnl, std_pnl}}}.
    """
    out = {}
    for cid, specialists in per_cluster_data.items():
        reason_pnls = {label: [] for label in TF_REASON_LABELS.values()}
        total_trades = 0
        for spec in specialists:
            reasons = np.asarray(spec['reason_array'], dtype=np.int8)
            pnls = np.asarray(spec['pnl_array'], dtype=np.float64)
            for r_int, r_label in TF_REASON_LABELS.items():
                mask = reasons == r_int
                reason_pnls[r_label].extend(pnls[mask].tolist())
            total_trades += len(reasons)

        cluster_summary = {
            'total_trades': total_trades,
            'reason_distribution': {},
        }
        for r_label, pnl_list in reason_pnls.items():
            n_t = len(pnl_list)
            if n_t == 0:
                cluster_summary['reason_distribution'][r_label] = {
                    'n_trades': 0, 'mean_pnl': None, 'std_pnl': None, 'pct_of_total': 0.0
                }
            else:
                arr = np.asarray(pnl_list)
                cluster_summary['reason_distribution'][r_label] = {
                    'n_trades': n_t,
                    'mean_pnl': float(arr.mean()),
                    'std_pnl': float(arr.std(ddof=1)) if n_t >= 2 else None,
                    'pct_of_total': n_t / max(total_trades, 1),
                }
        out[cid] = cluster_summary
    return out


def compute_h1_aggregation(per_cluster_data):
    """H1 short/long asymmetry: distribution pt_side per cluster + PnL per side."""
    out = {}
    for cid, specialists in per_cluster_data.items():
        long_pnls = []
        short_pnls = []
        for spec in specialists:
            sides = np.asarray(spec['side_array'], dtype=np.int8)
            pnls = np.asarray(spec['pnl_array'], dtype=np.float64)
            # pt_side: 0=long, 1=short (per kernel L1673)
            long_mask = sides == 0
            short_mask = sides == 1
            long_pnls.extend(pnls[long_mask].tolist())
            short_pnls.extend(pnls[short_mask].tolist())

        long_arr = np.asarray(long_pnls)
        short_arr = np.asarray(short_pnls)

        # Cohen's d: (mean1 - mean2) / pooled_std
        cohen_d = None
        if len(long_arr) >= 2 and len(short_arr) >= 2:
            pooled_std = np.sqrt(
                ((len(long_arr) - 1) * long_arr.var(ddof=1)
                 + (len(short_arr) - 1) * short_arr.var(ddof=1))
                / (len(long_arr) + len(short_arr) - 2)
            )
            if pooled_std > 0:
                cohen_d = float((long_arr.mean() - short_arr.mean()) / pooled_std)

        out[cid] = {
            'n_long': len(long_arr),
            'n_short': len(short_arr),
            'mean_pnl_long': float(long_arr.mean()) if len(long_arr) > 0 else None,
            'mean_pnl_short': float(short_arr.mean()) if len(short_arr) > 0 else None,
            'std_pnl_long': float(long_arr.std(ddof=1)) if len(long_arr) >= 2 else None,
            'std_pnl_short': float(short_arr.std(ddof=1)) if len(short_arr) >= 2 else None,
            'cohen_d_long_minus_short': cohen_d,
            'long_short_ratio': (len(long_arr) / max(len(short_arr), 1)),
        }
    return out


def main():
    print(f"R4 Bloque 2c granular cross-strategy dry-run start {datetime.now().isoformat()}")
    print(f"  Approach: JSONs-based + kernel re-run Path γ flag=True (Opción C precedent)")
    print(f"  TOP_N per cluster: {TOP_N_PER_CLUSTER}")
    print(f"  Hipótesis: H_strategy + H1 (H_funding DEFERRED — funding cache cobertura insuficiente)")

    all_results = {}

    for symbol in SYMBOLS:
        sym_full = f"{symbol}/USDT"
        print(f"\nProcessing {symbol}...")
        json_data = load_smoke_json(symbol)
        top_n_data = gather_top_n_per_cluster(json_data, TOP_N_PER_CLUSTER)
        if not top_n_data:
            print(f"  ⚠️  No top configs for {symbol}, skipping")
            continue

        # Load OHLCV + regime model + episodes for kernel re-run
        df_ohlcv = load_full_history(sym_full)
        if df_ohlcv is None:
            print(f"  ⚠️  No data for {symbol}, skipping")
            continue
        model_data = load_regime_model(sym_full)
        if model_data is None:
            print(f"  ⚠️  No regime model for {symbol}, skipping")
            continue
        cluster_labels, n_clusters = compute_cluster_labels(df_ohlcv, model_data)
        episodes = identify_episodes(cluster_labels, n_clusters, min_bars=MIN_EPISODE_BARS)
        regime_labels, n_doubled, _ = build_regime_labels(
            cluster_labels, episodes, n_clusters, train_ratio=TRAIN_RATIO,
            toxic_tail=50, gmm_probs=None, confirm_threshold=0.75,
            max_toxic_tail=100, min_toxic_tail=5,
        )
        presets_list = load_presets(sym_full, PRESETS_DIR)
        if presets_list is None or len(presets_list) == 0:
            print(f"  ⚠️  No presets for {symbol}, skipping")
            continue

        per_cluster_data = aggregate_per_cluster_per_specialist(
            symbol, top_n_data, df_ohlcv, regime_labels, n_doubled, presets_list
        )

        h_strategy = compute_h_strategy_aggregation(per_cluster_data)
        h1 = compute_h1_aggregation(per_cluster_data)

        all_results[symbol] = {
            'h_strategy': h_strategy,
            'h1_short_long': h1,
            'per_cluster_specialist_count': {
                cid: len(specs) for cid, specs in per_cluster_data.items()
            },
        }

        print(f"  {symbol} summary:")
        for cid in ['0', '1', '2']:
            h_s = h_strategy.get(cid, {})
            h1_c = h1.get(cid, {})
            print(f"    C{cid}: total_trades={h_s.get('total_trades', 0)}, "
                  f"long={h1_c.get('n_long', 0)}/short={h1_c.get('n_short', 0)}, "
                  f"cohen_d={h1_c.get('cohen_d_long_minus_short')}")

    # Cross-9 summary
    summary = {
        'methodology': {
            'approach': 'JSONs-based + kernel re-run Path γ flag=True',
            'top_n_per_cluster': TOP_N_PER_CLUSTER,
            'hipotesis_evaluadas': ['H_strategy', 'H1'],
            'hipotesis_deferred': ['H_funding (funding cache cobertura insuficiente)'],
            'precedent': 'Sesión 2.5 Opción C standalone script',
        },
        'timestamp': datetime.now().isoformat(),
        'per_symbol': all_results,
    }

    # Aggregate H1 cross-9 (Cohen d cross-clusters)
    cohen_ds = []
    for sym, sym_data in all_results.items():
        for cid, h1_c in sym_data.get('h1_short_long', {}).items():
            if h1_c.get('cohen_d_long_minus_short') is not None:
                cohen_ds.append(h1_c['cohen_d_long_minus_south' if False else 'cohen_d_long_minus_short'])
    summary['h1_cohen_d_cross_clusters'] = {
        'n_clusters_with_data': len(cohen_ds),
        'cohen_d_values': [float(c) for c in cohen_ds],
        'mean_cohen_d': float(np.mean(cohen_ds)) if cohen_ds else None,
        'std_cohen_d': float(np.std(cohen_ds, ddof=1)) if len(cohen_ds) >= 2 else None,
    }

    # Aggregate H_strategy cross-9 (reason distribution dominance)
    cancel_tf_pcts = []
    for sym, sym_data in all_results.items():
        for cid, h_s in sym_data.get('h_strategy', {}).items():
            cancel_tf_dist = h_s.get('reason_distribution', {}).get('cancel_tf', {})
            cancel_tf_pcts.append(cancel_tf_dist.get('pct_of_total', 0.0))
    summary['h_strategy_cancel_tf_pct_cross_clusters'] = {
        'mean_pct': float(np.mean(cancel_tf_pcts)) if cancel_tf_pcts else None,
        'values': cancel_tf_pcts,
    }

    output_path = os.path.join(_ROOT, 'r4_dry_run_cross_3_results.json')
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n=== SUMMARY ===")
    print(f"  Symbols processed: {list(all_results.keys())}")
    print(f"  H1 mean Cohen d cross-clusters: {summary['h1_cohen_d_cross_clusters']['mean_cohen_d']}")
    print(f"  H_strategy cancel_tf mean pct cross-clusters: {summary['h_strategy_cancel_tf_pct_cross_clusters']['mean_pct']}")
    print(f"  Output: {output_path}")
    print(f"Done {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
