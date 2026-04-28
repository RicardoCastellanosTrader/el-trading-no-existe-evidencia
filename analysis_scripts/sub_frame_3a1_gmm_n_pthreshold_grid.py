"""
Sub-Frame 3.A.1 GMM cluster N adaptive + P_threshold adaptive grid sweep
ablation matrix mandatory standalone retrain script Frame 3.A — 2026-04-29.

Per Sub-Frame 3.A.1 spec (Sesión 1 Frame 3.A análisis arquitectónica fundamental
commit 4d622e9 + decisiones Ricardo Sub-fase 3.A.1.0 Parte 0 escalación):

Ablation matrix mandatory 4 condiciones (Ricardo confirmed):
  · Baseline (N=3, P=0.75) — Sesión 4.5 Gate C rigorous baseline FAIL.
  · γ.1 only (N∈{4,5,6}, P=0.75 fixed).
  · γ.2 only (N=3, P∈{0.55..0.85} grid 7 values).
  · Joint (N∈{4,5,6}, P grid 7 values).
Total 32 unique cells × 3 sym (BTC + ONDO + SEI) = 96 walk-forward runs.

Architectural pattern Opción α (Ricardo confirmed Sub-fase 3.A.1.0):
  - Productive train_regime_model.py + regime_walk_forward.py UNCHANGED.
  - Standalone GMM fit + in-process call to regime_walk_forward.process_symbol
    with model_data dict pasado directly (NO disk I/O regime_models hack).
  - process_symbol(symbol, presets, df, model_data, args) accepts model_data
    parameter directly — NO monkey-patch MODEL_DIR needed.
  - Per-cell output to output/sub_frame_3a1/cell_<label>/<symbol>/...

Variant 4 P_threshold global sweep (Ricardo confirmed Sub-fase 3.A.1.0):
  - Single global confirm_threshold per cell (uses existing CLI semantics).
  - toxic_tail_mode='dynamic' all cells — P_threshold only takes effect
    via dynamic mode (toxic_tail fixed=0 makes confirm_threshold dead param
    per regime_walk_forward.build_regime_labels logic L346-371).

Determinismo Opción ε (Ricardo confirmed Sub-fase 3.A.1.0):
  - max_iter=300 default + monitor gmm.converged_ flag.
  - Adaptive escalate to 1000 IF non-convergence detected.
  - random_state=42 fijado preserva reproducibility 1:1 productive Sesión 4.5.

§12 L37 V2 calibrated honest: ~12-48h cumulative compute background substantial
cross-multiple sesiones acceptable per Ricardo Sub-fase 3.A.1.0 confirmation.

Validation gates per cell (Sub-fase 3.A.1.4 stricter criterion):
  - Gate 3.A.1.A: ≥6/9 stable+POSITIVE (NOT just |ρ|≥0.3 sign consistent).
  - Gate 3.A.1.B: 0/9 STRONG NEGATIVE (vs Sesión 4.5 baseline 2/9).
  - Gate 3.A.1.C: PF empírica cross-9 ≥1.2 baseline (computed downstream).

Decision rule Opción γ gated-marginal post-cell:
  - STRONG signal (ρ_mean cross-9 > 0.4): early-exit considered.
  - Marginal PASS (ρ_mean ∈ [0.3, 0.4]): proceed Sub-Frame 3.A.2 + 3.A.3.
  - FAIL: Sub-Frame 3.A.4 conditional activation last-resort defer Frame 3.D.

Resume logic: cells with cell_metadata.json status='completed' are skipped.

Usage:
  # Single cell smoke test
  python -m analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid \\
      --cells baseline --symbols BTC

  # Full ablation matrix (32 cells × 3 sym = 96 runs ~12-48h cumulative)
  python -m analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid

  # Analysis-only post-cells (skip execution; aggregate gates from existing)
  python -m analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid --analysis-only
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# Fix Windows cp1252 encoding (preserve unicode in stdout)
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
from scipy.stats import spearmanr
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from regime_features import compute_regime_features
import regime_walk_forward as rwf


# --------------------------------------------------------------------------
# Constants — ablation matrix specification
# --------------------------------------------------------------------------

SYMBOLS_DEFAULT = ['BTC/USDT', 'ONDO/USDT', 'SEI/USDT']

GAMMA_1_N_VALUES = [4, 5, 6]
GAMMA_2_P_GRID = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

OUTPUT_ROOT_DEFAULT = os.path.join(_ROOT, 'output', 'sub_frame_3a1')

# GMM fit constants (preserved 1:1 from train_regime_model.py L196-208)
GMM_N_INIT = 10
GMM_RANDOM_STATE = 42
GMM_MAX_ITER_DEFAULT = 300
GMM_MAX_ITER_ESCALATED = 1000
GMM_COVARIANCE_TYPE = 'full'

# Walk-forward constants (regime_walk_forward.py defaults)
TRAIN_RATIO = 0.70
MIN_EPISODE_BARS = 50
TOXIC_TAIL_MODE = 'dynamic'  # γ.2 P_threshold only effects via dynamic mode
MAX_TOXIC_TAIL = 100
MIN_TOXIC_TAIL = 5
LOOKBACK = 100  # train_regime_model.py default

# Validation gates thresholds (stricter criterion vs Frame 2 Gate C)
GATE_A_THRESHOLD_RHO_POSITIVE = 0.30  # ρ ≥ +0.30 with p<0.05 = stable+POSITIVE
GATE_A_REQUIRED_COUNT = 6  # ≥6/9 stable+positive
GATE_B_THRESHOLD_RHO_NEGATIVE = -0.30  # ρ ≤ -0.30 with p<0.05 = STRONG NEGATIVE
GATE_B_MAX_COUNT = 0  # 0/9 STRONG NEGATIVE
PVALUE_SIG_THRESHOLD = 0.05

# Decision rule Opción γ thresholds
RHO_MEAN_STRONG_PASS = 0.40
RHO_MEAN_MARGINAL_LOW = 0.30


# --------------------------------------------------------------------------
# Ablation matrix construction
# --------------------------------------------------------------------------

def build_ablation_matrix():
    """Build ablation matrix per Ricardo Sub-fase 3.A.1.0 spec — HONEST CORRECTION.

    Returns:
        list of (n_clusters, p_threshold, label) tuples.
        Total 28 unique (N,P) cells:
          - 1 baseline (N=3 P=0.75)
          - 3 γ.1 only (N∈{4,5,6} P=0.75 fixed)
          - 6 γ.2 only (N=3 × P grid 6 values, excluding P=0.75=baseline duplicate)
          - 18 joint (N∈{4,5,6} × P grid 6 values, excluding P=0.75=γ.1 duplicate)
          Total = 1 + 3 + 6 + 18 = 28 unique cells

    HONEST CORRECTION vs Ricardo Sub-fase 3.A.1.0 spec (32→31→28):
      - spec original 32 cells included γ.2 only P=0.75 = baseline duplicate (-1).
      - spec implicit 31 cells included Joint N∈{4,5,6} P=0.75 = γ.1 only
        duplicates 3× (Joint at P=0.75 produces identical (N,P) experimental
        condition as γ.1 only N=N P=0.75) (-3).
      - True unique (N,P) count = 28 cells.
      - 28 cells × 3 sym = 84 walk-forward runs (vs spec 96 → saves ~2-6h compute).

    Ablation interpretation orthogonal:
      - Baseline = neither γ.1 nor γ.2 active.
      - γ.1 only = γ.1 active (N>3), γ.2 inactive (P=0.75 default).
      - γ.2 only = γ.2 active (P≠0.75), γ.1 inactive (N=3).
      - Joint = both γ.1 + γ.2 active (N>3 AND P≠0.75).

    §12 L34 cross-24ª aplicación recursiva al own ablation matrix: deduplication
    honest applied al own spec when (N,P) redundancy detected during implementation.
    """
    cells = []
    # Baseline cell (Sesión 4.5 FAIL replicate)
    cells.append((3, 0.75, 'baseline'))
    # γ.1 only: N ∈ {4,5,6} P=0.75 fixed (γ.2 inactive)
    for n in GAMMA_1_N_VALUES:
        cells.append((n, 0.75, f'gamma1_only_N{n}'))
    # γ.2 only: N=3 P≠0.75 grid (γ.1 inactive — skip P=0.75 = baseline duplicate)
    for p in GAMMA_2_P_GRID:
        if abs(p - 0.75) < 1e-9:
            continue
        cells.append((3, p, f'gamma2_only_P{p:.2f}'))
    # Joint: N ∈ {4,5,6} × P ≠ 0.75 grid (both γ.1 + γ.2 active)
    # Skip P=0.75 — covered by γ.1 only at corresponding N (identical (N,P) cell).
    for n in GAMMA_1_N_VALUES:
        for p in GAMMA_2_P_GRID:
            if abs(p - 0.75) < 1e-9:
                continue
            cells.append((n, p, f'joint_N{n}_P{p:.2f}'))
    return cells


# --------------------------------------------------------------------------
# GMM fit with convergence monitoring (Opción ε §12 L26)
# --------------------------------------------------------------------------

def fit_gmm_with_convergence_monitoring(features, n_clusters,
                                         max_iter=GMM_MAX_ITER_DEFAULT):
    """Fit GMM with convergence monitoring + adaptive escalation.

    Replicates train_regime_model.py:196-208 GMM fit logic exactly +
    adds convergence monitoring per Sub-fase 3.A.1.0 sub-decisión 4 Opción ε.

    Args:
        features: (n_valid_bars, n_features) feature matrix (NOT scaled).
        n_clusters: int — N for GMM components.
        max_iter: int — initial max iter (default 300).

    Returns:
        dict with keys: gmm, scaler, converged, n_iter_actual, max_iter_used, bic.
    """
    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    gmm = GaussianMixture(
        n_components=n_clusters,
        covariance_type=GMM_COVARIANCE_TYPE,
        n_init=GMM_N_INIT,
        random_state=GMM_RANDOM_STATE,
        max_iter=max_iter,
    )
    gmm.fit(X)

    # M-F1 §12 L26: monitor convergence flag + escalate IF non-convergence
    if not gmm.converged_:
        print(f"      ⚠ GMM N={n_clusters} max_iter={max_iter} NOT converged "
              f"(n_iter={gmm.n_iter_}) — escalating to {GMM_MAX_ITER_ESCALATED}")
        gmm = GaussianMixture(
            n_components=n_clusters,
            covariance_type=GMM_COVARIANCE_TYPE,
            n_init=GMM_N_INIT,
            random_state=GMM_RANDOM_STATE,
            max_iter=GMM_MAX_ITER_ESCALATED,
        )
        gmm.fit(X)
        max_iter_used = GMM_MAX_ITER_ESCALATED
    else:
        max_iter_used = max_iter

    return {
        'gmm': gmm,
        'scaler': scaler,
        'converged': bool(gmm.converged_),
        'n_iter_actual': int(gmm.n_iter_),
        'max_iter_used': int(max_iter_used),
        'bic': float(gmm.bic(X)),
    }


def build_model_data_dict(gmm_result, n_clusters):
    """Build model_data dict compatible with regime_walk_forward.process_symbol.

    Replicates structure produced by train_regime_model.py output via
    load_regime_model (regime_walk_forward.py:189-196 + train_regime_model
    output structure):
      - gmm: GaussianMixture instance
      - scaler: StandardScaler instance
      - n_clusters: int
      - lookback: int
      - centroids: (n_clusters, n_features) original-scale centroids
      - cluster_names: list[str] auto-generated per high-vol pattern
    """
    centroids_scaled = gmm_result['gmm'].means_
    centroids_original = gmm_result['scaler'].inverse_transform(centroids_scaled)

    # Auto-generate cluster names (replicate train_regime_model.py L222-256)
    cluster_names = []
    for k in range(n_clusters):
        c = centroids_original[k]
        h, z_atr, er = c[0], c[1], c[2]
        parts = []
        if h > 0.55:
            parts.append('trending')
        elif h < 0.45:
            parts.append('mean-rev')
        else:
            parts.append('neutral')
        if z_atr > 0.5:
            parts.append('high-vol')
        elif z_atr < -0.5:
            parts.append('low-vol')
        else:
            parts.append('mid-vol')
        if er > 0.4:
            parts.append('efficient')
        elif er < 0.2:
            parts.append('choppy')
        else:
            parts.append('mixed')
        cluster_names.append('_'.join(parts))

    return {
        'gmm': gmm_result['gmm'],
        'scaler': gmm_result['scaler'],
        'n_clusters': n_clusters,
        'lookback': LOOKBACK,
        'centroids': centroids_original,
        'cluster_names': cluster_names,
    }


# --------------------------------------------------------------------------
# Cell driver
# --------------------------------------------------------------------------

def run_cell(symbol, n_clusters, p_threshold, label, output_root,
             features_cache=None):
    """Execute single ablation matrix cell.

    Resume logic: skip cell if cell_metadata.json status='completed' exists.

    Args:
        symbol: 'BTC/USDT' format.
        n_clusters: int (3, 4, 5, or 6).
        p_threshold: float ∈ [0.55, 0.85].
        label: str cell label (e.g., 'baseline', 'joint_N5_P0.65').
        output_root: str root output directory.
        features_cache: optional dict {symbol: (features, valid_mask)} cross-cells.

    Returns:
        cell_meta dict, or None if failed.
    """
    sym_key = rwf.sym_clean(symbol)
    cell_dir = os.path.join(output_root, f'cell_{label}', sym_key)
    os.makedirs(cell_dir, exist_ok=True)

    metadata_path = os.path.join(cell_dir, 'cell_metadata.json')
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path) as f:
                meta = json.load(f)
            if meta.get('status') == 'completed':
                print(f"   ⏭  Skip (resume): {label} {symbol}")
                return meta
        except (json.JSONDecodeError, OSError):
            pass  # corrupt metadata → re-run

    print(f"\n   🔧 Cell {label} {symbol}: N={n_clusters} P={p_threshold:.2f}")
    t0 = time.time()

    # Load full history (via regime_walk_forward.load_full_history)
    df = rwf.load_full_history(symbol)
    if df is None or len(df) < 5000:
        print(f"   ⚠ Insufficient data {symbol}")
        return None

    # Compute features (cached cross-cells per symbol — reusable since
    # features depend only on symbol+lookback, NOT N or P)
    if features_cache is not None and symbol in features_cache:
        features, valid_mask = features_cache[symbol]
    else:
        features, valid_mask = compute_regime_features(df, lookback=LOOKBACK)
        if features_cache is not None:
            features_cache[symbol] = (features, valid_mask)

    valid_features = features[valid_mask]
    if len(valid_features) < n_clusters * 50:
        print(f"   ⚠ Insufficient valid features ({len(valid_features)} "
              f"< {n_clusters * 50})")
        return None

    # Fit GMM with convergence monitoring (Opción ε)
    gmm_result = fit_gmm_with_convergence_monitoring(valid_features, n_clusters)
    print(f"   ✅ GMM N={n_clusters} BIC={gmm_result['bic']:.1f} "
          f"converged={gmm_result['converged']} n_iter={gmm_result['n_iter_actual']} "
          f"max_iter_used={gmm_result['max_iter_used']}")

    model_data = build_model_data_dict(gmm_result, n_clusters)

    # Build args namespace for regime_walk_forward.process_symbol
    args = argparse.Namespace(
        symbols=symbol,
        train_ratio=TRAIN_RATIO,
        min_episode_bars=MIN_EPISODE_BARS,
        output_dir=cell_dir,
        presets_dir=os.path.join(_ROOT, 'output'),
        toxic_tail=0,  # not used in dynamic mode (kept for backward compat)
        toxic_tail_mode=TOXIC_TAIL_MODE,
        max_toxic_tail=MAX_TOXIC_TAIL,
        min_toxic_tail=MIN_TOXIC_TAIL,
        confirm_threshold=p_threshold,
    )

    # Load presets (via regime_walk_forward.load_presets)
    presets = rwf.load_presets(symbol, args.presets_dir)
    if presets is None or len(presets) == 0:
        print(f"   ⚠ No presets {symbol}")
        return None

    # Run walk-forward (heavy compute step ~10-30 min per cell)
    try:
        result = rwf.process_symbol(symbol, presets, df, model_data, args)
    except Exception as e:
        print(f"   ❌ process_symbol error: {e}")
        import traceback
        traceback.print_exc()
        return None

    if result is None:
        print(f"   ⚠ process_symbol returned None")
        return None

    # Extract validated specialists per cluster (writes specialist_configs.json)
    rwf.extract_validated_specialists(result, args.output_dir)

    # Cleanup parts files (free disk)
    parts_dir = result.get('parts_dir')
    if parts_dir and os.path.isdir(parts_dir):
        import shutil
        shutil.rmtree(parts_dir)
        print(f"   🗑 Cleaned parts dir: {os.path.basename(parts_dir)}")

    elapsed = time.time() - t0
    cell_meta = {
        'status': 'completed',
        'cell_label': label,
        'symbol': symbol,
        'n_clusters': n_clusters,
        'p_threshold': p_threshold,
        'gmm_bic': gmm_result['bic'],
        'gmm_converged': gmm_result['converged'],
        'gmm_n_iter': gmm_result['n_iter_actual'],
        'gmm_max_iter_used': gmm_result['max_iter_used'],
        'elapsed_seconds': elapsed,
        'timestamp': datetime.now().isoformat(),
    }
    with open(metadata_path, 'w') as f:
        json.dump(cell_meta, f, indent=2)

    print(f"   ✅ Cell {label} {symbol} DONE ({elapsed:.0f}s)")
    return cell_meta


# --------------------------------------------------------------------------
# Spearman ρ analysis post-cell (Gate C rigorous methodology)
# --------------------------------------------------------------------------

def compute_spearman_per_cluster_post_cell(cell_dir):
    """Compute Spearman ρ(pf_tr, pf_fwd) per cluster from cell specialist_configs JSON.

    Mirrors gate_c_rigorous_analytical.py methodology applied per-cell.

    Returns:
        dict {cluster_id_str: {rho, p_value, n}} or None if JSON missing.
    """
    sym_key = os.path.basename(cell_dir)
    json_path = os.path.join(cell_dir, f'{sym_key}_specialist_configs.json')
    if not os.path.exists(json_path):
        return None
    with open(json_path) as f:
        d = json.load(f)
    n_clusters = d.get('n_clusters', 0)
    per_cluster = {}
    for k in range(n_clusters):
        cluster_data = d.get('clusters', {}).get(str(k), {})
        top_configs = cluster_data.get('top_configs', [])
        if len(top_configs) < 5:
            per_cluster[str(k)] = {'rho': None, 'p_value': None,
                                   'n': len(top_configs)}
            continue
        pf_tr = np.array([cfg.get('pf_tr', np.nan) for cfg in top_configs])
        pf_fwd = np.array([cfg.get('pf_fwd', np.nan) for cfg in top_configs])
        valid = ~(np.isnan(pf_tr) | np.isnan(pf_fwd))
        if valid.sum() < 5:
            per_cluster[str(k)] = {'rho': None, 'p_value': None,
                                   'n': int(valid.sum())}
            continue
        rho, pval = spearmanr(pf_tr[valid], pf_fwd[valid])
        per_cluster[str(k)] = {
            'rho': float(rho),
            'p_value': float(pval),
            'n': int(valid.sum()),
        }
    return per_cluster


def aggregate_cells_cross_n(all_cell_results):
    """Aggregate Spearman ρ per cell across all (sym, cluster) pairs.

    Note: cells with N=4,5,6 produce 4/5/6 clusters per symbol (not always 3).
    Aggregation total clusters = 3 sym × N_clusters per cell.

    Returns:
        dict {cell_label: {rho_mean, n_evaluated, n_stable_positive,
                           n_strong_negative, gate_a_pass, gate_b_pass, ...}}.
    """
    aggregated = {}
    for cell_label, sym_results in all_cell_results.items():
        rhos = []
        rhos_signed_pvals = []
        n_strong_negative = 0
        n_stable_positive = 0
        for sym, per_cluster in sym_results.items():
            if per_cluster is None:
                continue
            for k, m in per_cluster.items():
                if m['rho'] is None:
                    continue
                rhos.append(m['rho'])
                rhos_signed_pvals.append((m['rho'], m['p_value']))
                if (m['rho'] <= GATE_B_THRESHOLD_RHO_NEGATIVE
                        and m['p_value'] < PVALUE_SIG_THRESHOLD):
                    n_strong_negative += 1
                if (m['rho'] >= GATE_A_THRESHOLD_RHO_POSITIVE
                        and m['p_value'] < PVALUE_SIG_THRESHOLD):
                    n_stable_positive += 1
        n_eval = len(rhos)
        aggregated[cell_label] = {
            'n_evaluated': n_eval,
            'rho_mean': float(np.mean(rhos)) if rhos else None,
            'rho_median': float(np.median(rhos)) if rhos else None,
            'rho_min': float(np.min(rhos)) if rhos else None,
            'rho_max': float(np.max(rhos)) if rhos else None,
            'n_stable_positive': n_stable_positive,
            'n_strong_negative': n_strong_negative,
            'gate_a_pass': n_stable_positive >= GATE_A_REQUIRED_COUNT,
            'gate_b_pass': n_strong_negative <= GATE_B_MAX_COUNT,
        }
    return aggregated


def apply_decision_rule_opcion_gamma(aggregated):
    """Apply Opción γ gated-marginal decision rule per cell.

    - STRONG signal (ρ_mean > 0.4): early-exit considered.
    - Marginal PASS (ρ_mean ∈ [0.3, 0.4]): proceed Sub-Frame 3.A.2 + 3.A.3.
    - WEAK (ρ_mean < 0.3): below threshold → FAIL.
    - FAIL_GATES: gates A or B fail regardless of ρ_mean.
    """
    decisions = {}
    for cell_label, m in aggregated.items():
        if m.get('rho_mean') is None:
            decisions[cell_label] = 'NO_DATA'
            continue
        gates_pass = m['gate_a_pass'] and m['gate_b_pass']
        if not gates_pass:
            decisions[cell_label] = 'FAIL_GATES'
        elif m['rho_mean'] > RHO_MEAN_STRONG_PASS:
            decisions[cell_label] = 'STRONG_PASS_early_exit_considered'
        elif m['rho_mean'] >= RHO_MEAN_MARGINAL_LOW:
            decisions[cell_label] = 'MARGINAL_PASS_proceed_3a2_3a3_reinforcement'
        else:
            decisions[cell_label] = 'WEAK_below_threshold_FAIL'
    return decisions


# --------------------------------------------------------------------------
# Main CLI driver
# --------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Sub-Frame 3.A.1 GMM N + P_threshold ablation matrix grid sweep')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols (default: BTC,ONDO,SEI). '
                             'Accepts BTC or BTC/USDT.')
    parser.add_argument('--cells', type=str, default=None,
                        help='Comma-separated cell labels (default: all 31 cells).')
    parser.add_argument('--output-root', type=str, default=OUTPUT_ROOT_DEFAULT,
                        help=f'Output root dir (default: {OUTPUT_ROOT_DEFAULT})')
    parser.add_argument('--analysis-only', action='store_true',
                        help='Skip cell execution; only aggregate Spearman ρ + gates '
                             'from existing cell outputs.')
    return parser.parse_args()


def normalize_symbol(s):
    s = s.strip()
    return s if '/USDT' in s else f'{s}/USDT'


def main():
    args = parse_args()

    if args.symbols:
        symbols = [normalize_symbol(s) for s in args.symbols.split(',')]
    else:
        symbols = SYMBOLS_DEFAULT

    cells = build_ablation_matrix()
    if args.cells:
        wanted = set(c.strip() for c in args.cells.split(','))
        cells = [c for c in cells if c[2] in wanted]
        if not cells:
            print(f"ERROR: --cells filter matched zero cells. Available: "
                  f"{[c[2] for c in build_ablation_matrix()]}")
            return 1

    print('=' * 70)
    print('🔬 SUB-FRAME 3.A.1 GMM N + P_threshold ablation matrix grid sweep')
    print(f'   Symbols: {symbols}')
    print(f'   Cells: {len(cells)}')
    print(f'   Total runs: {len(cells) * len(symbols)}')
    print(f'   Output root: {args.output_root}')
    print(f'   GMM: random_state={GMM_RANDOM_STATE} n_init={GMM_N_INIT} '
          f'max_iter={GMM_MAX_ITER_DEFAULT} (escalate {GMM_MAX_ITER_ESCALATED} '
          f'if non-conv)')
    print(f'   Walk-forward: train_ratio={TRAIN_RATIO} '
          f'toxic_tail_mode={TOXIC_TAIL_MODE}')
    print(f'   Gates: A=≥{GATE_A_REQUIRED_COUNT}/N stable+POSITIVE | '
          f'B=≤{GATE_B_MAX_COUNT}/N STRONG NEGATIVE')
    print(f'   Decision rule: Opción γ gated-marginal '
          f'(strong={RHO_MEAN_STRONG_PASS} marginal=[{RHO_MEAN_MARGINAL_LOW},'
          f'{RHO_MEAN_STRONG_PASS}])')
    print('=' * 70)

    os.makedirs(args.output_root, exist_ok=True)

    # Phase A: cell execution (skipped with --analysis-only)
    if not args.analysis_only:
        features_cache = {}  # cache features per symbol cross-cells (saves work)
        total_runs = len(cells) * len(symbols)
        run_idx = 0
        for cell_idx, (n, p, label) in enumerate(cells, 1):
            for sym_idx, symbol in enumerate(symbols, 1):
                run_idx += 1
                print(f"\n[{run_idx}/{total_runs} | cell {cell_idx}/{len(cells)} "
                      f"× sym {sym_idx}/{len(symbols)}]")
                run_cell(symbol, n, p, label, args.output_root,
                         features_cache=features_cache)

    # Phase B: post-cell analysis (Spearman ρ + gates + decision)
    print(f"\n{'=' * 70}\n🔬 POST-CELL ANALYSIS — "
          f"Spearman ρ + validation gates + Opción γ decision rule\n{'=' * 70}")
    all_cell_results = {}
    for n, p, label in cells:
        sym_results = {}
        for symbol in symbols:
            cell_dir = os.path.join(args.output_root, f'cell_{label}',
                                    rwf.sym_clean(symbol))
            if os.path.isdir(cell_dir):
                sym_results[symbol] = compute_spearman_per_cluster_post_cell(cell_dir)
        all_cell_results[label] = sym_results

    aggregated = aggregate_cells_cross_n(all_cell_results)
    decisions = apply_decision_rule_opcion_gamma(aggregated)

    summary = {
        'cells': [{'n_clusters': n, 'p_threshold': p, 'label': label}
                  for n, p, label in cells],
        'symbols': symbols,
        'aggregated_per_cell': aggregated,
        'decisions_opcion_gamma': decisions,
        'thresholds': {
            'gate_a_rho_positive_min': GATE_A_THRESHOLD_RHO_POSITIVE,
            'gate_a_required_count': GATE_A_REQUIRED_COUNT,
            'gate_b_rho_negative_max': GATE_B_THRESHOLD_RHO_NEGATIVE,
            'gate_b_max_count': GATE_B_MAX_COUNT,
            'rho_mean_strong_pass': RHO_MEAN_STRONG_PASS,
            'rho_mean_marginal_low': RHO_MEAN_MARGINAL_LOW,
        },
        'timestamp': datetime.now().isoformat(),
    }
    summary_path = os.path.join(args.output_root, 'sub_frame_3a1_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n=== SUMMARY (validation gates per cell + Opción γ decision) ===")
    print(f"  {'cell':32s}  {'N':>2s}  {'P':>5s}  {'n':>3s}  "
          f"{'rho̅':>7s}  {'A':>2s}  {'B':>2s}  decision")
    for n, p, label in cells:
        m = aggregated.get(label, {})
        if not m or m.get('rho_mean') is None:
            print(f"  {label:32s}  {n:>2d}  {p:>5.2f}  N/A  N/A   N/A  N/A  "
                  f"{decisions.get(label, 'N/A')}")
            continue
        gate_a = '✓' if m['gate_a_pass'] else '✗'
        gate_b = '✓' if m['gate_b_pass'] else '✗'
        rho_mean = f"{m['rho_mean']:+.3f}"
        print(f"  {label:32s}  {n:>2d}  {p:>5.2f}  {m['n_evaluated']:>3d}  "
              f"{rho_mean:>7s}  {gate_a:>2s}  {gate_b:>2s}  "
              f"{decisions.get(label, 'N/A')}")

    print(f"\n  Output summary: {summary_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
