"""Tests analysis_aggregator module (Fase D.6 analytical aggregation).

Coverage:
- AA.1: _spearman_rank_corr basic + ties.
- AA.2: load_ccv_summary parses valid JSON correctly.
- AA.3: load_ccv_summary missing file returns error metric.
- AA.4: load_ccv_summary malformed JSON returns error metric.
- AA.5: load_baseline_metrics computes rho from top_configs.
- AA.6: load_baseline_metrics missing file returns error.
- AA.7: load_baseline_metrics no clusters returns error.
- AA.8: aggregate_cross_15_grupo aggregates 3 sources × N sym.
- AA.9: identify best source = argmax rho_mean.
- AA.10: prepare_deployment_package copies 5 JSONs + report.
- AA.11: prepare_deployment_package raises on missing best-source path.
- AA.12: grupo_summary counts correct.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import analysis_aggregator as aa


# -----------------------------------------------------------------------------
# AA.1: spearman basic
# -----------------------------------------------------------------------------

def test_aa_1_spearman_basic_monotonic():
    xs = [1, 2, 3, 4, 5]
    ys = [2, 4, 6, 8, 10]
    rho = aa._spearman_rank_corr(xs, ys)
    assert abs(rho - 1.0) < 1e-9


def test_aa_1_spearman_inverse():
    xs = [1, 2, 3, 4, 5]
    ys = [5, 4, 3, 2, 1]
    rho = aa._spearman_rank_corr(xs, ys)
    assert abs(rho - (-1.0)) < 1e-9


def test_aa_1_spearman_too_few_points():
    rho = aa._spearman_rank_corr([1, 2], [3, 4])
    import math
    assert math.isnan(rho)


# -----------------------------------------------------------------------------
# AA.2-4: load_ccv_summary
# -----------------------------------------------------------------------------

def _write_ccv_summary(path: Path, rho_mean=0.5, gate_a=False, gate_b=True, n_sp=2, n_sn=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "aggregated_per_cell": {
            "baseline": {
                "rho_mean": rho_mean,
                "rho_median": rho_mean,
                "rho_min": rho_mean - 0.1,
                "rho_max": rho_mean + 0.2,
                "n_evaluated": 3,
                "n_stable_positive": n_sp,
                "n_strong_negative": n_sn,
                "gate_a_pass": gate_a,
                "gate_b_pass": gate_b,
            }
        }
    }
    path.write_text(json.dumps(data))


def test_aa_2_load_ccv_summary_valid(tmp_path):
    path = tmp_path / "summary.json"
    _write_ccv_summary(path, rho_mean=0.45, gate_a=True, gate_b=True, n_sp=6, n_sn=0)
    m = aa.load_ccv_summary(path, "BNB", "BTC_SOURCE")
    assert m.error is None
    assert abs(m.rho_mean - 0.45) < 1e-9
    assert m.gate_a_pass is True
    assert m.gate_b_pass is True
    assert m.n_stable_positive == 6


def test_aa_3_load_ccv_summary_missing(tmp_path):
    m = aa.load_ccv_summary(tmp_path / "missing.json", "BNB", "BTC_SOURCE")
    assert m.error is not None
    assert "not found" in m.error.lower()


def test_aa_4_load_ccv_summary_malformed(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not valid json {{{")
    m = aa.load_ccv_summary(path, "BNB", "BTC_SOURCE")
    assert m.error is not None
    assert "parse failure" in m.error.lower()


# -----------------------------------------------------------------------------
# AA.5-7: load_baseline_metrics
# -----------------------------------------------------------------------------

def _write_regime_wf_json(path: Path, n_clusters=3, configs_per_cluster=5,
                            rho_target=0.7):
    """Write regime_wf JSON with top_configs designed to produce target rho.

    rho_target ~ correlation; for simplicity we make pf_fwd = rho * pf_tr + noise.
    """
    import math
    path.parent.mkdir(parents=True, exist_ok=True)
    clusters = {}
    for c in range(n_clusters):
        configs = []
        for i in range(configs_per_cluster):
            pf_tr = 1.0 + i * 0.5
            # Strong positive correlation
            pf_fwd = pf_tr * rho_target + 0.1
            configs.append({
                "config_id": i,
                "preset": f"P_{i}",
                "pf_tr": pf_tr,
                "pf_fwd": pf_fwd,
            })
        clusters[str(c)] = {"name": f"c_{c}", "top_configs": configs}
    data = {"symbol": "TEST/USDT", "n_clusters": n_clusters, "clusters": clusters}
    path.write_text(json.dumps(data))


def test_aa_5_load_baseline_metrics_computes_rho(tmp_path):
    path = tmp_path / "TEST_specialist_configs.json"
    _write_regime_wf_json(path, n_clusters=3, configs_per_cluster=10, rho_target=0.8)
    m = aa.load_baseline_metrics(path, "TEST")
    assert m.error is None
    assert m.source == "PER_SYM_BASELINE"
    # Perfect monotonic relation -> rho == 1.0 per cluster, mean ~ 1.0
    assert m.rho_mean > 0.99
    assert m.n_evaluated == 3
    assert m.n_stable_positive == 3
    assert m.n_strong_negative == 0


def test_aa_6_load_baseline_metrics_missing(tmp_path):
    m = aa.load_baseline_metrics(tmp_path / "missing.json", "TEST")
    assert m.error is not None
    assert "not found" in m.error.lower()


def test_aa_7_load_baseline_metrics_no_clusters(tmp_path):
    path = tmp_path / "empty_clusters.json"
    path.write_text(json.dumps({"clusters": {}}))
    m = aa.load_baseline_metrics(path, "TEST")
    assert m.error is not None
    assert "no cluster" in m.error.lower()


# -----------------------------------------------------------------------------
# AA.8: aggregate_cross_15_grupo
# -----------------------------------------------------------------------------

def test_aa_8_aggregate_cross_15_grupo(tmp_path):
    out_btc = tmp_path / "ccv_btc"
    out_eth = tmp_path / "ccv_eth"
    rwf = tmp_path / "rwf"

    symbols = ["BNBUSDT", "ETHUSDT"]
    # Write CCV summaries
    for sym in symbols:
        _write_ccv_summary(
            out_btc / f"{sym}_btc_classified" / "sub_frame_3a1_summary.json",
            rho_mean=0.4, gate_a=False, gate_b=True,
        )
        _write_ccv_summary(
            out_eth / f"{sym}_eth_classified" / "sub_frame_3a1_summary.json",
            rho_mean=0.25, gate_a=False, gate_b=True,
        )
        _write_regime_wf_json(rwf / f"{sym}_specialist_configs.json")

    analysis = aa.aggregate_cross_15_grupo(
        grupo_id=1, symbols=symbols,
        output_root_btc=str(out_btc),
        output_root_eth=str(out_eth),
        regime_wf_dir=str(rwf),
    )
    assert analysis.grupo_id == 1
    assert set(analysis.metrics_table.keys()) == set(symbols)
    for sym in symbols:
        assert set(analysis.metrics_table[sym].keys()) == set(aa.CROSS_SOURCES)
        for src in aa.CROSS_SOURCES:
            m = analysis.metrics_table[sym][src]
            assert m.error is None, f"{sym} {src}: {m.error}"


# -----------------------------------------------------------------------------
# AA.9: best source = argmax rho_mean
# -----------------------------------------------------------------------------

def test_aa_9_best_source_argmax(tmp_path):
    out_btc = tmp_path / "ccv_btc"
    out_eth = tmp_path / "ccv_eth"
    rwf = tmp_path / "rwf"
    sym = "BNBUSDT"

    # BTC rho_mean = 0.4, ETH = 0.6, baseline = ~1.0
    _write_ccv_summary(out_btc / f"{sym}_btc_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.4)
    _write_ccv_summary(out_eth / f"{sym}_eth_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.6)
    _write_regime_wf_json(rwf / f"{sym}_specialist_configs.json", rho_target=0.95)

    analysis = aa.aggregate_cross_15_grupo(
        grupo_id=1, symbols=[sym],
        output_root_btc=str(out_btc),
        output_root_eth=str(out_eth),
        regime_wf_dir=str(rwf),
    )
    # Baseline rho ~ 1.0 wins
    assert analysis.best_source_per_sym[sym] == "PER_SYM_BASELINE"


def test_aa_9_best_source_skips_error_metrics(tmp_path):
    out_btc = tmp_path / "ccv_btc"
    out_eth = tmp_path / "ccv_eth"
    rwf = tmp_path / "rwf"
    sym = "BNBUSDT"

    # BTC missing (error), ETH rho_mean = 0.6, baseline = ~1.0 winner
    _write_ccv_summary(out_eth / f"{sym}_eth_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.6)
    _write_regime_wf_json(rwf / f"{sym}_specialist_configs.json", rho_target=0.95)
    # BTC NOT written -> error

    analysis = aa.aggregate_cross_15_grupo(
        grupo_id=1, symbols=[sym],
        output_root_btc=str(out_btc),
        output_root_eth=str(out_eth),
        regime_wf_dir=str(rwf),
    )
    # BTC has error, skipped; baseline (~1.0) > ETH (0.6) -> baseline wins
    assert analysis.metrics_table[sym]["BTC_SOURCE"].error is not None
    assert analysis.best_source_per_sym[sym] == "PER_SYM_BASELINE"


# -----------------------------------------------------------------------------
# AA.10: prepare_deployment_package copies 5 JSONs + report
# -----------------------------------------------------------------------------

def test_aa_10_prepare_deployment_package(tmp_path):
    out_btc = tmp_path / "ccv_btc"
    out_eth = tmp_path / "ccv_eth"
    rwf = tmp_path / "rwf"
    deploy = tmp_path / "deploy"

    symbols = ["BNBUSDT", "ETHUSDT"]
    for sym in symbols:
        _write_ccv_summary(out_btc / f"{sym}_btc_classified" / "sub_frame_3a1_summary.json",
                            rho_mean=0.5)
        _write_ccv_summary(out_eth / f"{sym}_eth_classified" / "sub_frame_3a1_summary.json",
                            rho_mean=0.3)
        _write_regime_wf_json(rwf / f"{sym}_specialist_configs.json")
        # Create the cell_baseline path (best-source for BTC)
        cb_dir = out_btc / f"{sym}_btc_classified" / "cell_baseline" / sym
        cb_dir.mkdir(parents=True)
        (cb_dir / f"{sym}_specialist_configs.json").write_text('{"sym": "' + sym + '"}')

    analysis = aa.aggregate_cross_15_grupo(
        grupo_id=1, symbols=symbols,
        output_root_btc=str(out_btc),
        output_root_eth=str(out_eth),
        regime_wf_dir=str(rwf),
    )
    # Force best source to BTC for test (override baseline winning naturally)
    for sym in symbols:
        analysis.best_source_per_sym[sym] = "BTC_SOURCE"

    report_path, copied = aa.prepare_deployment_package(
        analysis, str(deploy),
        output_root_btc=str(out_btc),
        output_root_eth=str(out_eth),
        regime_wf_dir=str(rwf),
    )
    assert report_path.exists()
    assert len(copied) == 2
    for p in copied:
        assert p.exists()
    # Verify report content
    with open(report_path) as f:
        report = json.load(f)
    assert report["grupo_id"] == 1
    assert set(report["best_source_per_sym"].keys()) == set(symbols)


# -----------------------------------------------------------------------------
# AA.11: prepare_deployment_package raises on missing source path
# -----------------------------------------------------------------------------

def test_aa_11_deployment_pkg_missing_source_raises(tmp_path):
    out_btc = tmp_path / "ccv_btc"
    out_eth = tmp_path / "ccv_eth"
    rwf = tmp_path / "rwf"
    deploy = tmp_path / "deploy"

    sym = "BNBUSDT"
    _write_ccv_summary(out_btc / f"{sym}_btc_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.5)
    # PER_SYM_BASELINE has no rwf file -> baseline path missing
    # Force baseline as best source
    analysis = aa.GrupoCrossAnalysis(grupo_id=1, symbols=[sym])
    analysis.best_source_per_sym = {sym: "PER_SYM_BASELINE"}
    analysis.metrics_table = {sym: {"PER_SYM_BASELINE": aa.SourceMetrics(sym=sym, source="PER_SYM_BASELINE")}}

    with pytest.raises(FileNotFoundError):
        aa.prepare_deployment_package(
            analysis, str(deploy),
            output_root_btc=str(out_btc),
            output_root_eth=str(out_eth),
            regime_wf_dir=str(rwf),
        )


# -----------------------------------------------------------------------------
# AA.12: grupo_summary counts
# -----------------------------------------------------------------------------

def _write_regime_wf_low_rho(path: Path, n_clusters=3, configs_per_cluster=5):
    """Write regime_wf JSON with shuffled pf_fwd to break correlation -> low rho."""
    path.parent.mkdir(parents=True, exist_ok=True)
    clusters = {}
    # Fixed deterministic shuffle pattern to give low/zero rho
    shuffle_idx = [4, 2, 0, 3, 1]  # breaks monotonicity
    for c in range(n_clusters):
        configs = []
        pf_tr_vals = [1.0 + i * 0.5 for i in range(configs_per_cluster)]
        pf_fwd_vals = [pf_tr_vals[shuffle_idx[i % len(shuffle_idx)]]
                        for i in range(configs_per_cluster)]
        for i in range(configs_per_cluster):
            configs.append({
                "config_id": i,
                "preset": f"P_{i}",
                "pf_tr": pf_tr_vals[i],
                "pf_fwd": pf_fwd_vals[i],
            })
        clusters[str(c)] = {"name": f"c_{c}", "top_configs": configs}
    data = {"symbol": "TEST/USDT", "n_clusters": n_clusters, "clusters": clusters}
    path.write_text(json.dumps(data))


def test_aa_12_grupo_summary_counts(tmp_path):
    out_btc = tmp_path / "ccv_btc"
    out_eth = tmp_path / "ccv_eth"
    rwf = tmp_path / "rwf"

    symbols = ["BNBUSDT", "ETHUSDT", "XRPUSDT"]
    # BNB best=BTC (0.6), ETH best=ETH (0.8), XRP best=baseline (~1.0)
    _write_ccv_summary(out_btc / "BNBUSDT_btc_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.6, gate_a=True, gate_b=True)
    _write_ccv_summary(out_eth / "BNBUSDT_eth_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.3, gate_a=False, gate_b=True)
    _write_regime_wf_low_rho(rwf / "BNBUSDT_specialist_configs.json")  # rho ~ low/negative

    _write_ccv_summary(out_btc / "ETHUSDT_btc_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.3, gate_a=False, gate_b=True)
    _write_ccv_summary(out_eth / "ETHUSDT_eth_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.8, gate_a=True, gate_b=True)
    _write_regime_wf_low_rho(rwf / "ETHUSDT_specialist_configs.json")  # rho ~ low/negative

    _write_ccv_summary(out_btc / "XRPUSDT_btc_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.3, gate_a=False, gate_b=True)
    _write_ccv_summary(out_eth / "XRPUSDT_eth_classified" / "sub_frame_3a1_summary.json",
                        rho_mean=0.4, gate_a=False, gate_b=True)
    _write_regime_wf_json(rwf / "XRPUSDT_specialist_configs.json", rho_target=0.95)  # baseline ~ 1.0 wins

    analysis = aa.aggregate_cross_15_grupo(
        grupo_id=1, symbols=symbols,
        output_root_btc=str(out_btc),
        output_root_eth=str(out_eth),
        regime_wf_dir=str(rwf),
    )
    summary = analysis.grupo_summary
    assert summary["n_sym_total"] == 3
    assert summary["n_sym_with_best_source"] == 3
    assert summary["n_btc_source_best"] == 1  # BNB
    assert summary["n_eth_source_best"] == 1  # ETH
    assert summary["n_per_sym_baseline_best"] == 1  # XRP
