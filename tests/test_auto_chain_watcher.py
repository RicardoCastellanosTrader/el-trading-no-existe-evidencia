"""Tests greenfield auto_chain_watcher.decide_action state dispatch cumulative.

Covers state machine dispatch logic for cross-stage auto-chain Grupo N reciclaje
→ CROSS_CLASS → ANALYSIS with Tier 3 PAUSE at DEPLOYMENT_READY.

Coverage:
- W.1: RECICLAJE in-progress (sym_done < symbols) → wait
- W.2: RECICLAJE complete (sym_done == symbols) → launch_cross_class
- W.3: CROSS_CLASS in-progress (options_done < 3) → wait
- W.4: CROSS_CLASS complete (options_done == 3) → launch_analysis
- W.5: tier3_gate_pending → tier3_pause
- W.6: DEPLOYMENT_READY → tier3_pause (Ricardo authorization required)
- W.7: TERMINAL_COMPLETE → terminal
- W.8: grupo_actual mismatch → wait
- W.9: grupo not in state.grupos → wait
- W.10: ANALYSIS state in progress → wait (orchestrator handles auto-transition)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import automation_orchestrator as ao
from auto_chain_watcher import decide_action


def _make_state(*, fase, grupo_actual=2, grupo_data=None, tier3=False):
    s = {
        "fase_actual": fase,
        "grupo_actual": grupo_actual,
        "tier3_gate_pending": tier3,
        "grupos": {},
    }
    if grupo_data is not None:
        s["grupos"][str(grupo_actual)] = grupo_data
    return s


def test_w_1_reciclaje_in_progress_wait():
    s = _make_state(
        fase=ao.STATE_RECICLAJE,
        grupo_data={
            "symbols": ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"],
            "sym_done_grupo_N": ["ONDOUSDT", "RENDERUSDT"],
            "sym_pending_grupo_N": ["POLUSDT", "SEIUSDT", "TAOUSDT"],
        },
    )
    assert decide_action(s, grupo=2) == "wait"


def test_w_2_reciclaje_complete_launch_cross_class():
    syms = ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"]
    s = _make_state(
        fase=ao.STATE_RECICLAJE,
        grupo_data={
            "symbols": syms,
            "sym_done_grupo_N": list(syms),
            "sym_pending_grupo_N": [],
        },
    )
    assert decide_action(s, grupo=2) == "launch_cross_class"


def test_w_3_cross_class_in_progress_wait():
    s = _make_state(
        fase=ao.STATE_CROSS_CLASS,
        grupo_data={
            "symbols": ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"],
            "cross_options_done": ["BTC_SOURCE"],
            "cross_options_pending": ["ETH_SOURCE", "PER_SYM_BASELINE"],
        },
    )
    assert decide_action(s, grupo=2) == "wait"


def test_w_4_cross_class_complete_launch_analysis():
    s = _make_state(
        fase=ao.STATE_CROSS_CLASS,
        grupo_data={
            "symbols": ["ONDOUSDT", "RENDERUSDT", "POLUSDT", "SEIUSDT", "TAOUSDT"],
            "cross_options_done": list(ao.CROSS_OPTIONS),
            "cross_options_pending": [],
        },
    )
    assert decide_action(s, grupo=2) == "launch_analysis"


def test_w_5_tier3_gate_pending():
    s = _make_state(
        fase=ao.STATE_RECICLAJE,
        grupo_data={"symbols": [], "sym_done_grupo_N": []},
        tier3=True,
    )
    assert decide_action(s, grupo=2) == "tier3_pause"


def test_w_6_deployment_ready_tier3_pause():
    s = _make_state(
        fase=ao.STATE_DEPLOYMENT_READY,
        grupo_data={"symbols": [], "sym_done_grupo_N": []},
    )
    assert decide_action(s, grupo=2) == "tier3_pause"


def test_w_7_terminal_complete():
    s = _make_state(
        fase=ao.STATE_TERMINAL_COMPLETE,
        grupo_data={"symbols": [], "sym_done_grupo_N": []},
    )
    assert decide_action(s, grupo=2) == "terminal"


def test_w_8_grupo_actual_mismatch_wait():
    s = _make_state(
        fase=ao.STATE_RECICLAJE,
        grupo_actual=3,  # different from target
        grupo_data={"symbols": ["X"], "sym_done_grupo_N": ["X"]},
    )
    assert decide_action(s, grupo=2) == "wait"


def test_w_9_grupo_not_in_state_wait():
    s = {
        "fase_actual": ao.STATE_RECICLAJE,
        "grupo_actual": 2,
        "tier3_gate_pending": False,
        "grupos": {},  # empty
    }
    assert decide_action(s, grupo=2) == "wait"


def test_w_10_analysis_state_wait():
    """ANALYSIS state: orchestrator handles auto-transition to DEPLOYMENT_READY itself.
    Watcher should just wait until DEPLOYMENT_READY surfaces."""
    s = _make_state(
        fase=ao.STATE_ANALYSIS,
        grupo_data={"symbols": ["X"], "sym_done_grupo_N": ["X"]},
    )
    assert decide_action(s, grupo=2) == "wait"


def test_w_11_zero_symbols_no_action():
    """Edge case: grupo declared but symbols empty (shouldn't happen but safe)."""
    s = _make_state(
        fase=ao.STATE_RECICLAJE,
        grupo_data={
            "symbols": [],
            "sym_done_grupo_N": [],
        },
    )
    # Empty symbols → wait (don't launch with 0 sym)
    assert decide_action(s, grupo=2) == "wait"
