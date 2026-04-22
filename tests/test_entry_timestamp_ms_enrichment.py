"""Tests para fix entry_timestamp_ms enrichment en live_engine.

Verifica que _enrich_positions_with_entry_ms lee desde pre_signal_state
(snapshot pre-reset) y enriquece positions dict in-place.

Contexto: bug detectado 2026-04-22, 51/155 trades con entry_ms=0 en
trade_history.csv. Root cause: _reset_state_on_exit (v2.3.9 fix B1)
reseteaba state.entry_timestamp_ms=0 DURANTE generate_signals, antes
del call-site de enriquecimiento (live_engine.py L616). Trades via
_evaluate_bar CLOSE paths (div_exit, tf_exit, zone_exit, sl_hit,
cancel_*) post-v2.3.9 persistian 0 al CSV. v2.4.5 fix: usar
pre_signal_state (capturado pre-reset) como fuente canonica.

Run: python tests/test_entry_timestamp_ms_enrichment.py
"""
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from live.live_engine import _enrich_positions_with_entry_ms


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_enriches_from_pre_signal_state():
    """Happy path: pre_signal_state tiene entry_ms>0, pos enriquecido."""
    positions = {"BTC/USDT": {"side": "long", "size": 0.01}}
    pre_signal_state = {
        "BTC/USDT": {
            "entry_timestamp_ms": 1776621060000,
            "entry_price": 70000.0,
        }
    }
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert positions["BTC/USDT"]["entry_timestamp_ms"] == 1776621060000


def test_ignores_zero_pre_ts():
    """pre_ts=0 (bug sentinel) no enriquece; guard > 0 correcto."""
    positions = {"BTC/USDT": {"side": "long"}}
    pre_signal_state = {"BTC/USDT": {"entry_timestamp_ms": 0}}
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert "entry_timestamp_ms" not in positions["BTC/USDT"]


def test_ignores_missing_sym_in_pre_state():
    """Sym en positions pero no en pre_signal_state (ej. orphan BingX)."""
    positions = {"BTC/USDT": {"side": "long"}}
    pre_signal_state = {}
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert "entry_timestamp_ms" not in positions["BTC/USDT"]


def test_ignores_missing_entry_ms_key():
    """pre_signal_state entry sin campo entry_timestamp_ms."""
    positions = {"BTC/USDT": {"side": "long"}}
    pre_signal_state = {"BTC/USDT": {"entry_price": 70000.0}}
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert "entry_timestamp_ms" not in positions["BTC/USDT"]


def test_enriches_multiple_symbols_independently():
    """Varias posiciones, cada una enriquecida con su pre_ts respectivo."""
    positions = {
        "BTC/USDT": {"side": "long"},
        "ETH/USDT": {"side": "short"},
        "SOL/USDT": {"side": "long"},
    }
    pre_signal_state = {
        "BTC/USDT": {"entry_timestamp_ms": 1776621060000},
        "ETH/USDT": {"entry_timestamp_ms": 1776624660000},  # +1h
        "SOL/USDT": {"entry_timestamp_ms": 0},              # sentinel bug
    }
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert positions["BTC/USDT"]["entry_timestamp_ms"] == 1776621060000
    assert positions["ETH/USDT"]["entry_timestamp_ms"] == 1776624660000
    assert "entry_timestamp_ms" not in positions["SOL/USDT"]


def test_overrides_existing_entry_ms_in_pos():
    """Si pos ya tiene entry_timestamp_ms (improbable desde get_open_positions
    pero defensivo), el enriquecimiento sobreescribe con pre_ts."""
    positions = {
        "BTC/USDT": {"side": "long", "entry_timestamp_ms": 9999},  # stale
    }
    pre_signal_state = {
        "BTC/USDT": {"entry_timestamp_ms": 1776621060000},
    }
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert positions["BTC/USDT"]["entry_timestamp_ms"] == 1776621060000


def test_empty_positions_noop():
    """positions vacio: ningun error, no-op."""
    positions = {}
    pre_signal_state = {"BTC/USDT": {"entry_timestamp_ms": 1776621060000}}
    _enrich_positions_with_entry_ms(positions, pre_signal_state)
    assert positions == {}


def test_post_reset_scenario_regression():
    """
    Regresion directa del bug v2.3.9:

    Pre-v2.4.5 (roto): enrichment leia desde brain.symbol_state POST
    _reset_state_on_exit. state.entry_timestamp_ms=0 despues del reset.

    Post-v2.4.5 (fix): enrichment lee desde pre_signal_state, capturado
    ANTES de generate_signals. pre_ts preservado.

    Este test simula el escenario y verifica que el campo se preserva.
    """
    # Antes del cycle: brain state tiene entry_ms=1776621060000 (posicion abierta).
    # pre_signal_state capturado en L467-483:
    pre_signal_state = {
        "BTC/USDT": {
            "position": 1,
            "side": "long",
            "entry_price": 70000.0,
            "sl_level": 67900.0,
            "entry_bar_timestamp": 1776617460000,
            "entry_timestamp_ms": 1776621060000,
        }
    }

    # generate_signals invoca _evaluate_bar CLOSE -> _reset_state_on_exit
    # (simulado: brain state ahora seria entry_timestamp_ms=0, pero pre_signal_state
    # intacto).
    # (No necesitamos mockar el brain; el fix solo usa pre_signal_state.)

    # get_open_positions retorna positions sin entry_timestamp_ms
    # (BingX no provee este campo en fetch_positions).
    positions = {
        "BTC/USDT": {
            "side": "long",
            "size": 0.01,
            "entry_price": 70000.0,
        }
    }

    # Enrichment lee desde pre_signal_state (v2.4.5 fix).
    _enrich_positions_with_entry_ms(positions, pre_signal_state)

    # Post-fix: pos enriquecido, log_trade lo persistira correctamente al CSV.
    assert positions["BTC/USDT"]["entry_timestamp_ms"] == 1776621060000


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _main():
    tests = [
        test_enriches_from_pre_signal_state,
        test_ignores_zero_pre_ts,
        test_ignores_missing_sym_in_pre_state,
        test_ignores_missing_entry_ms_key,
        test_enriches_multiple_symbols_independently,
        test_overrides_existing_entry_ms_in_pos,
        test_empty_positions_noop,
        test_post_reset_scenario_regression,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    total = len(tests)
    print(f"\n{total - failed}/{total} tests PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_main())
