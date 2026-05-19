"""Tests Fase D.6 — AutomationOrchestrator.run_analysis_real_compute.

Mock aggregator + package_preparer to avoid touching filesystem CCV/baseline outputs.

Coverage:
- D6.1: run_analysis_real_compute requires fase_actual == ANALYSIS.
- D6.2: happy path -> transitions to DEPLOYMENT_READY + Tier 3 PAUSE.
- D6.3: missing best source -> Tier 3 PAUSE no transition.
- D6.4: deployment package FileNotFoundError -> Tier 3 PAUSE.
- D6.5: analysis_report_path set after success.
- D6.6: tier3_gate_pending after success (DEPLOYMENT_READY auto-pauses).
- D6.7: grupo summary captured in TierReport context.
- D6.8: undeclared grupo raises.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import automation_orchestrator as ao
import analysis_aggregator as aa


def _build_orch_at_analysis(tmp_path: Path, grupo_id: int = 1,
                              symbols=None) -> ao.AutomationOrchestrator:
    """Helper: drive orchestrator state machine to ANALYSIS for grupo_id."""
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    orch.declare_grupo(grupo_id, symbols)
    orch.transition(ao.STATE_RECICLAJE, note="t")
    for sym in symbols:
        orch.mark_sym_done(grupo_id, sym)
    orch.transition(ao.STATE_CROSS_CLASS, note="t")
    for opt in list(orch.state["grupos"][str(grupo_id)]["cross_options_pending"]):
        orch.mark_cross_option_done(grupo_id, opt)
    orch.transition(ao.STATE_ANALYSIS, note="t")
    return orch


def _stub_analysis_object(symbols, best_sources):
    """Build a stub aa.GrupoCrossAnalysis-like object."""
    analysis = aa.GrupoCrossAnalysis(grupo_id=1, symbols=list(symbols))
    for sym in symbols:
        analysis.metrics_table[sym] = {
            "BTC_SOURCE": aa.SourceMetrics(sym=sym, source="BTC_SOURCE", rho_mean=0.5),
            "ETH_SOURCE": aa.SourceMetrics(sym=sym, source="ETH_SOURCE", rho_mean=0.3),
            "PER_SYM_BASELINE": aa.SourceMetrics(sym=sym, source="PER_SYM_BASELINE",
                                                  rho_mean=0.4),
        }
    analysis.best_source_per_sym = dict(best_sources)
    analysis.grupo_summary = {
        "n_sym_total": len(symbols),
        "n_sym_with_best_source": len(best_sources),
        "n_btc_source_best": sum(1 for v in best_sources.values() if v == "BTC_SOURCE"),
        "n_eth_source_best": sum(1 for v in best_sources.values() if v == "ETH_SOURCE"),
        "n_per_sym_baseline_best": sum(1 for v in best_sources.values()
                                        if v == "PER_SYM_BASELINE"),
        "n_gate_a_pass_total": 0,
        "n_gate_b_violations_total": 0,
    }
    return analysis


# -----------------------------------------------------------------------------
# D6.1: requires fase_actual == ANALYSIS
# -----------------------------------------------------------------------------

def test_d6_1_requires_analysis_state(tmp_path):
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    orch.declare_grupo(1, ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"])
    # state.fase_actual is IDLE
    with pytest.raises(ao.OrchestratorError, match="requires fase_actual == ANALYSIS"):
        orch.run_analysis_real_compute(1, aggregator=lambda **kw: None, package_preparer=lambda **kw: (None, []))


# -----------------------------------------------------------------------------
# D6.2: happy path transitions to DEPLOYMENT_READY + Tier 3
# -----------------------------------------------------------------------------

def test_d6_2_happy_path_deployment_ready(tmp_path):
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = _build_orch_at_analysis(tmp_path, symbols=symbols)

    best = {s: "BTC_SOURCE" for s in symbols}
    stub_analysis = _stub_analysis_object(symbols, best)

    def _stub_agg(**kw):
        return stub_analysis

    def _stub_pkg(**kw):
        out_dir = Path(kw["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        report = out_dir / "deployment_report.json"
        report.write_text("{}")
        return (report, [out_dir / f"{s}_specialist_configs.json" for s in symbols])

    reports = orch.run_analysis_real_compute(
        1,
        deployment_package_dir=str(tmp_path / "deploy"),
        aggregator=_stub_agg,
        package_preparer=_stub_pkg,
    )
    # Should transition to DEPLOYMENT_READY
    assert orch.state["fase_actual"] == ao.STATE_DEPLOYMENT_READY
    # Should set Tier 3 gate
    assert orch.state["tier3_gate_pending"] is True
    # Should have Tier 3 report
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert len(tier3) == 1
    assert "PAUSE awaiting Ricardo authorization" in tier3[0].message


# -----------------------------------------------------------------------------
# D6.3: missing best source -> Tier 3 no transition
# -----------------------------------------------------------------------------

def test_d6_3_missing_best_source_tier3_no_transition(tmp_path):
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = _build_orch_at_analysis(tmp_path, symbols=symbols)

    # Only 3 of 5 have best source
    best = {symbols[0]: "BTC_SOURCE", symbols[1]: "ETH_SOURCE", symbols[2]: "PER_SYM_BASELINE"}
    stub_analysis = _stub_analysis_object(symbols, best)

    reports = orch.run_analysis_real_compute(
        1,
        aggregator=lambda **kw: stub_analysis,
        package_preparer=lambda **kw: (None, []),
    )
    # Should NOT transition out of ANALYSIS
    assert orch.state["fase_actual"] == ao.STATE_ANALYSIS
    assert orch.state["tier3_gate_pending"] is True
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert any("missing best source" in r.message for r in tier3)


# -----------------------------------------------------------------------------
# D6.4: deployment package FileNotFoundError -> Tier 3
# -----------------------------------------------------------------------------

def test_d6_4_deployment_pkg_filenotfound_tier3(tmp_path):
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = _build_orch_at_analysis(tmp_path, symbols=symbols)

    best = {s: "BTC_SOURCE" for s in symbols}
    stub_analysis = _stub_analysis_object(symbols, best)

    def _stub_pkg_raises(**kw):
        raise FileNotFoundError("simulated missing best-source path for BNB")

    reports = orch.run_analysis_real_compute(
        1,
        aggregator=lambda **kw: stub_analysis,
        package_preparer=_stub_pkg_raises,
    )
    assert orch.state["fase_actual"] == ao.STATE_ANALYSIS  # no transition
    assert orch.state["tier3_gate_pending"] is True
    tier3 = [r for r in reports if r.tier == ao.TIER_3]
    assert any("deployment package failure" in r.message for r in tier3)


# -----------------------------------------------------------------------------
# D6.5: analysis_report_path set after success
# -----------------------------------------------------------------------------

def test_d6_5_analysis_report_path_set(tmp_path):
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = _build_orch_at_analysis(tmp_path, symbols=symbols)

    best = {s: "BTC_SOURCE" for s in symbols}
    stub_analysis = _stub_analysis_object(symbols, best)

    captured_report_path = Path("captured_path.json")

    def _stub_pkg(**kw):
        out_dir = Path(kw["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        rp = out_dir / "report.json"
        rp.write_text("{}")
        return (rp, [])

    orch.run_analysis_real_compute(
        1,
        deployment_package_dir=str(tmp_path / "deploy"),
        aggregator=lambda **kw: stub_analysis,
        package_preparer=_stub_pkg,
    )
    grupo = orch.state["grupos"]["1"]
    assert grupo["analysis_report_path"] is not None
    assert "report.json" in grupo["analysis_report_path"]


# -----------------------------------------------------------------------------
# D6.6: tier3_gate_pending after success (DEPLOYMENT_READY auto-pauses)
# -----------------------------------------------------------------------------

def test_d6_6_tier3_gate_after_success(tmp_path):
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = _build_orch_at_analysis(tmp_path, symbols=symbols)

    best = {s: "BTC_SOURCE" for s in symbols}
    stub_analysis = _stub_analysis_object(symbols, best)

    def _stub_pkg(**kw):
        out_dir = Path(kw["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        rp = out_dir / "r.json"
        rp.write_text("{}")
        return (rp, [])

    orch.run_analysis_real_compute(
        1,
        deployment_package_dir=str(tmp_path / "deploy"),
        aggregator=lambda **kw: stub_analysis,
        package_preparer=_stub_pkg,
    )
    # Top-level Tier 3 gate pending
    assert orch.state["tier3_gate_pending"] is True
    # Per-grupo gate also pending (set on DEPLOYMENT_READY transition)
    assert orch.state["grupos"]["1"]["tier3_gate_pending"] is True


# -----------------------------------------------------------------------------
# D6.7: grupo summary captured in TierReport context
# -----------------------------------------------------------------------------

def test_d6_7_grupo_summary_in_tier_report(tmp_path):
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "TRXUSDT"]
    orch = _build_orch_at_analysis(tmp_path, symbols=symbols)

    best = {symbols[0]: "BTC_SOURCE", symbols[1]: "ETH_SOURCE",
            symbols[2]: "BTC_SOURCE", symbols[3]: "ETH_SOURCE",
            symbols[4]: "PER_SYM_BASELINE"}
    stub_analysis = _stub_analysis_object(symbols, best)

    def _stub_pkg(**kw):
        out_dir = Path(kw["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        rp = out_dir / "r.json"
        rp.write_text("{}")
        return (rp, [])

    reports = orch.run_analysis_real_compute(
        1,
        deployment_package_dir=str(tmp_path / "deploy"),
        aggregator=lambda **kw: stub_analysis,
        package_preparer=_stub_pkg,
    )
    tier2 = [r for r in reports if r.tier == ao.TIER_2]
    aggregated_report = next(r for r in tier2 if "aggregated cross-15" in r.message)
    assert "grupo_summary" in aggregated_report.context
    summary = aggregated_report.context["grupo_summary"]
    assert summary["n_btc_source_best"] == 2
    assert summary["n_eth_source_best"] == 2
    assert summary["n_per_sym_baseline_best"] == 1


# -----------------------------------------------------------------------------
# D6.8: undeclared grupo raises
# -----------------------------------------------------------------------------

def test_d6_8_undeclared_grupo_raises(tmp_path):
    orch = ao.AutomationOrchestrator(
        state_path=str(tmp_path / "state.json"),
        primary_source_verifier=lambda s, g, sy: True,
    )
    orch.load_state()
    # Force fase_actual=ANALYSIS without declaring grupo
    orch.state["fase_actual"] = ao.STATE_ANALYSIS
    orch._save_state_internal(reason="setup")
    with pytest.raises(ao.OrchestratorError, match="grupo 99 not declared"):
        orch.run_analysis_real_compute(
            99,
            aggregator=lambda **kw: None,
            package_preparer=lambda **kw: (None, []),
        )
