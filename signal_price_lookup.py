"""
signal_price_lookup.py — Helper compartido para derivar signal_entry_price /
signal_exit_price desde SIGNALS_RAW del engine.log (post-hoc, zero-touch al bot).

Contexto: live_engine.py:520 loguea `p` (= close_p del bar que dispara signal)
en SIGNALS_RAW per (cycle_ts, symbol) desde v2.3.1. Parser engine.log del
analyzer y audit ya indexan signals_raw[(cycle_ts, sym)]["p"]. Este modulo
provee lookup + computo de slippage reutilizable.

Retroactivo desde v2.3.1. Para trades pre-v2.3.1 o con logs rotados, retorna
None sin error (consumer decide que hacer con missing).

Uso: analyzer v2.4.1+, audit v5.2+, cualquier script offline que necesite
slippage directo (fill_price - signal_price).

Referencia: §13.3 MEJORA "Logger enriquecer signal_entry_price" 2026-04-21
(A02 resuelto via Opcion 2 post-hoc). live_engine.py:517-540 genera SIGNALS_RAW.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_signal_price(
    signals_raw_by_cycle: dict,
    cycle_ts,
    symbol: str,
    action_hint: Optional[str] = None,
) -> Optional[float]:
    """Extrae signal_price del bar del cycle especificado para symbol.

    signals_raw_by_cycle: dict {(cycle_ts, symbol): {a, r, p, sl, c, s, k, t}}
        tal como lo retorna parse_engine_log de analyzer v2.4.1 y audit v5.x.
    cycle_ts: pd.Timestamp (idealmente UTC-aware) del bar de la senal.
    symbol: "BTC/USDT" etc.
    action_hint: opcional, "LONG"/"SHORT" para entry o "CLOSE_LONG"/"CLOSE_SHORT"
        para exit. Solo para sanity check; lookup es permisivo (si el hint
        no coincide con event["a"], loggea WARNING pero retorna el price).

    Returns: float con signal_price, o None si:
      - No hay entry en signals_raw para ese (cycle_ts, sym).
      - El entry existe pero "p" es None o 0.0 (brain_engine:517-523 solo
        loguea "p" si ep truthy).
      - cycle_ts es None.
    """
    if cycle_ts is None:
        return None
    event = signals_raw_by_cycle.get((cycle_ts, symbol))
    if event is None:
        return None
    p = event.get("p")
    if p is None:
        return None
    try:
        p_float = float(p)
    except (TypeError, ValueError):
        return None
    if p_float == 0.0:
        return None
    if action_hint is not None:
        actual_action = str(event.get("a", "")).upper()
        hint = action_hint.upper()
        hint_is_close = hint.startswith("CLOSE")
        actual_is_close = actual_action.startswith("CLOSE")
        if hint_is_close != actual_is_close:
            logger.warning(
                "signal_price action mismatch at %s %s: hint=%s actual=%s",
                cycle_ts, symbol, action_hint, actual_action,
            )
    return p_float


def compute_slippage_usdt(
    fill_price: float,
    signal_price: float,
    side: str,
    size_contracts: float,
) -> float:
    """Slippage en USDT sobre contratos. Convencion de signo:
      positivo = favorable al trader (fill mejor que signal).
      negativo = adverso.

    LONG: fill < signal = favorable -> (signal - fill) * size.
    SHORT: fill > signal = favorable -> (fill - signal) * size.

    Raises ValueError si side no es 'long'/'short'.
    """
    s = side.lower().strip()
    if s == "long":
        return (signal_price - fill_price) * size_contracts
    if s == "short":
        return (fill_price - signal_price) * size_contracts
    raise ValueError(f"Invalid side: {side!r} (expected 'long' or 'short')")


def compute_slippage_pct(
    fill_price: float,
    signal_price: float,
    side: str,
) -> float:
    """Slippage en porcentaje. Mismo signo que compute_slippage_usdt.
    Retorna 0.0 si signal_price == 0 (division defensiva)."""
    if signal_price == 0:
        return 0.0
    s = side.lower().strip()
    if s == "long":
        return (signal_price - fill_price) / signal_price * 100.0
    if s == "short":
        return (fill_price - signal_price) / signal_price * 100.0
    raise ValueError(f"Invalid side: {side!r}")


def attribute_slippage_per_trade(
    fill_entry: float,
    fill_exit: float,
    signal_entry: Optional[float],
    signal_exit: Optional[float],
    side: str,
    size_contracts: float,
) -> dict:
    """Agrega slippage_entry + slippage_exit + total en USDT y % para un trade.

    Si algun signal_* es None, el componente respectivo es None (no 0.0, para
    distinguir 'no pude medir' de 'medi y fue cero').
    """
    out = {
        "slippage_entry_usdt": None,
        "slippage_exit_usdt": None,
        "slippage_total_usdt": None,
        "slippage_entry_pct": None,
        "slippage_exit_pct": None,
        "slippage_missing_entry": signal_entry is None,
        "slippage_missing_exit": signal_exit is None,
    }
    if signal_entry is not None:
        out["slippage_entry_usdt"] = compute_slippage_usdt(
            fill_entry, signal_entry, side, size_contracts
        )
        out["slippage_entry_pct"] = compute_slippage_pct(
            fill_entry, signal_entry, side
        )
    if signal_exit is not None:
        # Convencion: exit es el lado opuesto del entry.
        # Para LONG trade, exit es un SELL (cierre venta): fill > signal =
        # favorable (vendemos mas caro de lo que senal indicaba).
        # Para SHORT trade, exit es un BUY (cierre compra): fill < signal =
        # favorable (compramos mas barato).
        # Side invertido para formula:
        exit_side = "short" if side.lower() == "long" else "long"
        out["slippage_exit_usdt"] = compute_slippage_usdt(
            fill_exit, signal_exit, exit_side, size_contracts
        )
        out["slippage_exit_pct"] = compute_slippage_pct(
            fill_exit, signal_exit, exit_side
        )
    if out["slippage_entry_usdt"] is not None and out["slippage_exit_usdt"] is not None:
        out["slippage_total_usdt"] = (
            out["slippage_entry_usdt"] + out["slippage_exit_usdt"]
        )
    return out
