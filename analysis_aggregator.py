"""Cross-classification analytical aggregator (Fase D.6 minimum viable).

Reads per-sym cross-class outputs (BTC source + ETH source + PER_SYM_BASELINE)
and aggregates into cumulative cross-15 metrics table + per-sym best-source
identification + Gate A/B verification + deployment package preparation.

Scope minimum viable:
- 3 sources per sym: BTC_SOURCE, ETH_SOURCE, PER_SYM_BASELINE.
- For BTC/ETH sources: read pre-aggregated `sub_frame_3a1_summary.json`.
- For PER_SYM_BASELINE: compute rho_mean from top_configs en regime_wf JSON
  (lightweight on-the-fly aggregation cumulative).
- Best source = argmax rho_mean cross-3-sources cumulative.
- Gate A: ≥ N_REQUIRED stable+POSITIVE clusters cumulative.
- Gate B: ≤ N_MAX STRONG NEGATIVE clusters cumulative.
- Deployment package: 5 JSONs selected from best-source path + cumulative report.

DEFERRED (Ricardo manual review post-Tier-3-PAUSE cumulative):
- Pattern A/B/C classification (per memoria precedent — contextual cumulative).
- Cluster sparsity refined penalty.
- STRONG NEGATIVE forensics detailed.

Caveat #15 primary source verification mandatory cumulative cross-input-paths.
"""
from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# -----------------------------------------------------------------------------
# Gate thresholds (mirror sub_frame_3a1_gmm_n_pthreshold_grid.py cumulative)
# -----------------------------------------------------------------------------

GATE_A_RHO_POSITIVE_MIN = 0.3
GATE_A_REQUIRED_COUNT = 6
GATE_B_RHO_NEGATIVE_MAX = -0.3
GATE_B_MAX_COUNT = 0
RHO_MEAN_STRONG_PASS = 0.4
RHO_MEAN_MARGINAL_LOW = 0.3

CROSS_SOURCES = ("BTC_SOURCE", "ETH_SOURCE", "PER_SYM_BASELINE")


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------

@dataclass
class SourceMetrics:
    """Aggregated metrics for one (sym, source) combination."""
    sym: str
    source: str  # "BTC_SOURCE", "ETH_SOURCE", "PER_SYM_BASELINE"
    rho_mean: float = float("nan")
    rho_median: float = float("nan")
    rho_min: float = float("nan")
    rho_max: float = float("nan")
    n_evaluated: int = 0
    n_stable_positive: int = 0
    n_strong_negative: int = 0
    gate_a_pass: bool = False
    gate_b_pass: bool = False
    source_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class GrupoCrossAnalysis:
    """Cross-grupo analytical aggregation result."""
    grupo_id: int
    symbols: List[str]
    metrics_table: Dict[str, Dict[str, SourceMetrics]] = field(default_factory=dict)
    best_source_per_sym: Dict[str, str] = field(default_factory=dict)
    grupo_summary: Dict[str, int] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# CCV summary loader
# -----------------------------------------------------------------------------

def load_ccv_summary(summary_json_path: Path, sym: str, source: str) -> SourceMetrics:
    """Load pre-aggregated CCV summary JSON.

    Schema expected: keys aggregated_per_cell.baseline.{rho_mean, n_evaluated,
    n_stable_positive, n_strong_negative, gate_a_pass, gate_b_pass, ...}.
    """
    if not summary_json_path.exists():
        return SourceMetrics(
            sym=sym, source=source, source_path=str(summary_json_path),
            error=f"CCV summary not found: {summary_json_path}",
        )
    try:
        with open(summary_json_path, encoding="utf-8") as f:
            data = json.load(f)
        baseline = data.get("aggregated_per_cell", {}).get("baseline", {})
        return SourceMetrics(
            sym=sym,
            source=source,
            rho_mean=float(baseline.get("rho_mean", float("nan"))),
            rho_median=float(baseline.get("rho_median", float("nan"))),
            rho_min=float(baseline.get("rho_min", float("nan"))),
            rho_max=float(baseline.get("rho_max", float("nan"))),
            n_evaluated=int(baseline.get("n_evaluated", 0)),
            n_stable_positive=int(baseline.get("n_stable_positive", 0)),
            n_strong_negative=int(baseline.get("n_strong_negative", 0)),
            gate_a_pass=bool(baseline.get("gate_a_pass", False)),
            gate_b_pass=bool(baseline.get("gate_b_pass", False)),
            source_path=str(summary_json_path),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return SourceMetrics(
            sym=sym, source=source, source_path=str(summary_json_path),
            error=f"Parse failure: {e}",
        )


# -----------------------------------------------------------------------------
# PER_SYM_BASELINE on-the-fly aggregator from top_configs
# -----------------------------------------------------------------------------

def _spearman_rank_corr(xs: List[float], ys: List[float]) -> float:
    """Spearman rank correlation (manual, NumPy-free). Returns NaN if too few points."""
    n = len(xs)
    if n != len(ys) or n < 3:
        return float("nan")
    # Rank x and y
    def _ranks(vs):
        sorted_idx = sorted(range(n), key=lambda i: vs[i])
        ranks = [0.0] * n
        # Average ranks for ties
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vs[sorted_idx[j + 1]] == vs[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[sorted_idx[k]] = avg_rank
            i = j + 1
        return ranks
    rx = _ranks(xs)
    ry = _ranks(ys)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((rx[i] - mean_x) * (ry[i] - mean_y) for i in range(n))
    den_x = math.sqrt(sum((rx[i] - mean_x) ** 2 for i in range(n)))
    den_y = math.sqrt(sum((ry[i] - mean_y) ** 2 for i in range(n)))
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def load_baseline_metrics(regime_wf_json_path: Path, sym: str) -> SourceMetrics:
    """Compute PER_SYM_BASELINE metrics from regime_wf/{sym}_specialist_configs.json.

    Iterates clusters, computes Spearman pf_tr vs pf_fwd per cluster, aggregates
    rho_mean = mean of per-cluster Spearman, gates per CCV criteria cumulative.
    """
    if not regime_wf_json_path.exists():
        return SourceMetrics(
            sym=sym, source="PER_SYM_BASELINE", source_path=str(regime_wf_json_path),
            error=f"Regime WF JSON not found: {regime_wf_json_path}",
        )
    try:
        with open(regime_wf_json_path, encoding="utf-8") as f:
            data = json.load(f)
        clusters = data.get("clusters", {})
        cluster_rhos: List[float] = []
        for cluster_key in sorted(clusters.keys()):
            configs = clusters[cluster_key].get("top_configs", [])
            if not configs:
                continue
            pf_tr = [c.get("pf_tr", float("nan")) for c in configs]
            pf_fwd = [c.get("pf_fwd", float("nan")) for c in configs]
            # Filter NaN pairs
            valid = [(x, y) for x, y in zip(pf_tr, pf_fwd)
                     if isinstance(x, (int, float)) and isinstance(y, (int, float))
                     and not (math.isnan(x) or math.isnan(y))]
            if len(valid) < 3:
                continue
            xs, ys = zip(*valid)
            rho = _spearman_rank_corr(list(xs), list(ys))
            if not math.isnan(rho):
                cluster_rhos.append(rho)

        n_eval = len(cluster_rhos)
        if n_eval == 0:
            return SourceMetrics(
                sym=sym, source="PER_SYM_BASELINE", source_path=str(regime_wf_json_path),
                error="No cluster Spearman could be computed (insufficient configs)",
            )
        rho_mean = sum(cluster_rhos) / n_eval
        rho_sorted = sorted(cluster_rhos)
        rho_median = rho_sorted[n_eval // 2] if n_eval % 2 == 1 else \
            (rho_sorted[n_eval // 2 - 1] + rho_sorted[n_eval // 2]) / 2.0
        rho_min = rho_sorted[0]
        rho_max = rho_sorted[-1]
        n_stable_positive = sum(1 for r in cluster_rhos if r >= GATE_A_RHO_POSITIVE_MIN)
        n_strong_negative = sum(1 for r in cluster_rhos if r <= GATE_B_RHO_NEGATIVE_MAX)
        gate_a_pass = n_stable_positive >= GATE_A_REQUIRED_COUNT
        gate_b_pass = n_strong_negative <= GATE_B_MAX_COUNT
        return SourceMetrics(
            sym=sym, source="PER_SYM_BASELINE",
            rho_mean=rho_mean, rho_median=rho_median, rho_min=rho_min, rho_max=rho_max,
            n_evaluated=n_eval, n_stable_positive=n_stable_positive,
            n_strong_negative=n_strong_negative,
            gate_a_pass=gate_a_pass, gate_b_pass=gate_b_pass,
            source_path=str(regime_wf_json_path),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return SourceMetrics(
            sym=sym, source="PER_SYM_BASELINE", source_path=str(regime_wf_json_path),
            error=f"Parse failure: {e}",
        )


# -----------------------------------------------------------------------------
# Grupo-level aggregation
# -----------------------------------------------------------------------------

def _ccv_summary_path(output_root: str, sym: str, source_lower: str) -> Path:
    """Path to ccv_phaseN_results/{sym}_{source}_classified/sub_frame_3a1_summary.json."""
    sym_clean = sym if sym.endswith("USDT") else f"{sym}USDT"
    return Path(output_root) / f"{sym_clean}_{source_lower}_classified" / "sub_frame_3a1_summary.json"


def _baseline_path(regime_wf_dir: str, sym: str) -> Path:
    sym_clean = sym if sym.endswith("USDT") else f"{sym}USDT"
    return Path(regime_wf_dir) / f"{sym_clean}_specialist_configs.json"


def aggregate_cross_15_grupo(
    grupo_id: int,
    symbols: List[str],
    output_root_btc: str = "ccv_phase4_btc_results",
    output_root_eth: str = "ccv_phase4_eth_results",
    regime_wf_dir: str = "regime_wf",
) -> GrupoCrossAnalysis:
    """Aggregate cumulative cross-{N_sym × 3 sources} metrics for one grupo."""
    analysis = GrupoCrossAnalysis(grupo_id=grupo_id, symbols=list(symbols))
    for sym in symbols:
        sym_metrics: Dict[str, SourceMetrics] = {}
        # BTC_SOURCE
        btc_path = _ccv_summary_path(output_root_btc, sym, "btc")
        sym_metrics["BTC_SOURCE"] = load_ccv_summary(btc_path, sym, "BTC_SOURCE")
        # ETH_SOURCE
        eth_path = _ccv_summary_path(output_root_eth, sym, "eth")
        sym_metrics["ETH_SOURCE"] = load_ccv_summary(eth_path, sym, "ETH_SOURCE")
        # PER_SYM_BASELINE
        baseline_path = _baseline_path(regime_wf_dir, sym)
        sym_metrics["PER_SYM_BASELINE"] = load_baseline_metrics(baseline_path, sym)
        analysis.metrics_table[sym] = sym_metrics

    # Identify best source per sym (argmax rho_mean across non-error metrics)
    for sym in symbols:
        best_rho = float("-inf")
        best_source = None
        for source in CROSS_SOURCES:
            m = analysis.metrics_table[sym][source]
            if m.error is not None:
                continue
            if math.isnan(m.rho_mean):
                continue
            if m.rho_mean > best_rho:
                best_rho = m.rho_mean
                best_source = source
        if best_source is not None:
            analysis.best_source_per_sym[sym] = best_source

    # Grupo summary counts
    analysis.grupo_summary = {
        "n_sym_with_best_source": len(analysis.best_source_per_sym),
        "n_sym_total": len(symbols),
        "n_btc_source_best": sum(1 for v in analysis.best_source_per_sym.values()
                                  if v == "BTC_SOURCE"),
        "n_eth_source_best": sum(1 for v in analysis.best_source_per_sym.values()
                                  if v == "ETH_SOURCE"),
        "n_per_sym_baseline_best": sum(1 for v in analysis.best_source_per_sym.values()
                                        if v == "PER_SYM_BASELINE"),
        "n_gate_a_pass_total": sum(1 for sym in symbols
                                    for source in CROSS_SOURCES
                                    if analysis.metrics_table[sym][source].gate_a_pass),
        "n_gate_b_violations_total": sum(1 for sym in symbols
                                          for source in CROSS_SOURCES
                                          if not analysis.metrics_table[sym][source].gate_b_pass
                                          and analysis.metrics_table[sym][source].error is None),
    }
    return analysis


# -----------------------------------------------------------------------------
# Deployment package preparation
# -----------------------------------------------------------------------------

def _best_source_config_path(sym: str, source: str,
                              output_root_btc: str, output_root_eth: str,
                              regime_wf_dir: str) -> Path:
    """Resolve path to specialist_configs.json for the best-source decision."""
    sym_clean = sym if sym.endswith("USDT") else f"{sym}USDT"
    if source == "BTC_SOURCE":
        # Expected: ccv_phase4_btc_results/{sym}_btc_classified/cell_baseline/{sym}/{sym}_specialist_configs.json
        return Path(output_root_btc) / f"{sym_clean}_btc_classified" / "cell_baseline" / sym_clean / f"{sym_clean}_specialist_configs.json"
    if source == "ETH_SOURCE":
        return Path(output_root_eth) / f"{sym_clean}_eth_classified" / "cell_baseline" / sym_clean / f"{sym_clean}_specialist_configs.json"
    # PER_SYM_BASELINE
    return Path(regime_wf_dir) / f"{sym_clean}_specialist_configs.json"


def prepare_deployment_package(
    analysis: GrupoCrossAnalysis,
    output_dir: str,
    output_root_btc: str = "ccv_phase4_btc_results",
    output_root_eth: str = "ccv_phase4_eth_results",
    regime_wf_dir: str = "regime_wf",
) -> Tuple[Path, List[Path]]:
    """Copy 5 JSONs selected from best-source paths into output_dir.

    Returns (report_path, list_of_copied_json_paths).

    Caveat #15 primary source verification: missing best-source JSON for any sym
    raises FileNotFoundError. Caller should escalate Tier 3.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    copied: List[Path] = []
    missing: List[str] = []
    for sym in analysis.symbols:
        source = analysis.best_source_per_sym.get(sym)
        if source is None:
            missing.append(f"{sym}: no best source identified")
            continue
        src_path = _best_source_config_path(
            sym, source, output_root_btc, output_root_eth, regime_wf_dir
        )
        if not src_path.exists():
            missing.append(f"{sym} ({source}): source path missing {src_path}")
            continue
        sym_clean = sym if sym.endswith("USDT") else f"{sym}USDT"
        dst = out / f"{sym_clean}_specialist_configs.json"
        shutil.copy2(src_path, dst)
        copied.append(dst)
    if missing:
        raise FileNotFoundError(f"Deployment package incomplete: {missing}")

    # Build report
    report_path = out / f"deployment_report_grupo_{analysis.grupo_id}.json"
    report = {
        "grupo_id": analysis.grupo_id,
        "symbols": analysis.symbols,
        "best_source_per_sym": analysis.best_source_per_sym,
        "grupo_summary": analysis.grupo_summary,
        "metrics_table": {
            sym: {
                source: {
                    "rho_mean": m.rho_mean,
                    "rho_median": m.rho_median,
                    "rho_min": m.rho_min,
                    "rho_max": m.rho_max,
                    "n_evaluated": m.n_evaluated,
                    "n_stable_positive": m.n_stable_positive,
                    "n_strong_negative": m.n_strong_negative,
                    "gate_a_pass": m.gate_a_pass,
                    "gate_b_pass": m.gate_b_pass,
                    "source_path": m.source_path,
                    "error": m.error,
                }
                for source, m in sym_metrics.items()
            }
            for sym, sym_metrics in analysis.metrics_table.items()
        },
        "copied_files": [str(p) for p in copied],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return (report_path, copied)
