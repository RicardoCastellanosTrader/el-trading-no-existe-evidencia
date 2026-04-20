"""
execution_manager.py — Ejecución de órdenes en BingX.

Recibe allocaciones del portfolio_manager y las ejecuta en BingX vía ccxt.
Gestiona bracket orders (entry + stop vinculado), trailing stops, cierres,
y cancelación de órdenes obsoletas. Único módulo que ESCRIBE en el exchange.
"""

import asyncio
import csv
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import ccxt.async_support as ccxt_async
import ccxt as ccxt_sync

from live.data_feed import (
    _create_bingx_exchange,
    to_bingx_symbol,
    from_bingx_symbol,
    get_open_positions,
    get_open_orders,
    get_balance,
    get_funding_rate,
    get_funding_history,
)

logger = logging.getLogger("live.execution_manager")

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
DRY_RUN = True  # DEBE arrancar en True durante ≥1 semana antes de operar real

MAX_RETRIES = 3
RETRY_BACKOFF = [1.0, 2.0, 4.0]   # segundos entre reintentos
ORDER_DELAY = 0.1                   # 100ms entre órdenes secuenciales
SL_EMERGENCY_PCT = 5.0              # SL de emergencia si no hay nivel calculado

TRADE_LOG_PATH = Path(__file__).parent.parent / "trade_history.csv"

# ---------------------------------------------------------------------------
# Dry-run position tracking
# ---------------------------------------------------------------------------
_dry_run_positions: dict[str, dict] = {}


def get_dry_run_positions() -> dict[str, dict]:
    """Retorna copia de las posiciones DRY_RUN simuladas."""
    return {sym: pos.copy() for sym, pos in _dry_run_positions.items()}


def save_dry_run_positions() -> dict:
    """Serializa dry_run_positions para engine_state.json."""
    return {sym: pos.copy() for sym, pos in _dry_run_positions.items()}


def load_dry_run_positions(data: dict):
    """Restaura dry_run_positions desde engine_state.json."""
    global _dry_run_positions
    _dry_run_positions = data or {}


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------

class ExecutionError(Exception):
    """Error no recuperable en ejecución."""
    pass


class OrderRejected(Exception):
    """Exchange rechazó la orden (insufficient margin, invalid size, etc.)."""
    pass


# ---------------------------------------------------------------------------
# ExecutionReport
# ---------------------------------------------------------------------------

@dataclass
class ExecutionReport:
    timestamp: str = ""
    orders_sent: list = field(default_factory=list)
    orders_failed: list = field(default_factory=list)
    positions_closed: list = field(default_factory=list)
    stops_updated: list = field(default_factory=list)
    stops_placed: list = field(default_factory=list)
    errors: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _ts_ms() -> float:
    return time.perf_counter()


async def _retry_async(coro_fn, description: str):
    """Ejecuta una coroutine con retry y backoff exponencial."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_fn()
        except (ccxt_sync.NetworkError, ccxt_sync.RequestTimeout) as e:
            last_err = e
            delay = RETRY_BACKOFF[attempt] if attempt < len(RETRY_BACKOFF) else RETRY_BACKOFF[-1]
            logger.warning(
                f"[EXEC] {description}: retry {attempt+1}/{MAX_RETRIES} "
                f"({type(e).__name__}), waiting {delay}s"
            )
            await asyncio.sleep(delay)
        except ccxt_sync.ExchangeNotAvailable as e:
            logger.critical(f"[EXEC] Exchange no disponible: {e}")
            raise ExecutionError(f"Exchange down: {e}") from e
        except ccxt_sync.InsufficientFunds as e:
            logger.warning(f"[EXEC] {description}: margen insuficiente — {e}")
            raise OrderRejected(f"Insufficient margin: {e}") from e
        except ccxt_sync.OrderNotFound:
            raise  # Propagar a cancel_order, no reintentar
        except ccxt_sync.InvalidOrder as e:
            logger.warning(f"[EXEC] {description}: orden invalida -- {e}")
            raise OrderRejected(f"Invalid order: {e}") from e

    logger.critical(f"[EXEC] {description}: FALLIDO tras {MAX_RETRIES} intentos — {last_err}")
    raise ExecutionError(f"{description} failed after {MAX_RETRIES} retries: {last_err}")


# ---------------------------------------------------------------------------
# Funding helpers
# ---------------------------------------------------------------------------

async def _get_position_funding(
    symbol: str,
    entry_timestamp_ms: int | None,
    position_size_usdt: float,
    exchange: ccxt_async.bingx,
) -> float:
    """
    Obtiene el funding total pagado/recibido durante la vida de una posición.

    Intenta fetch_funding_history primero. Si no disponible, estima con el
    funding rate actual × size × períodos de 8h transcurridos.

    Returns:
        funding total en USDT (negativo = pagado, positivo = recibido)
    """
    # Intento 1: historial real
    try:
        history = await get_funding_history(
            symbol, since=entry_timestamp_ms, limit=100, exchange=exchange,
        )
        if history:
            return sum(entry["amount"] for entry in history)
    except Exception as e:
        logger.debug(f"Funding history {symbol} no disponible: {e}")

    # Intento 2: estimación con rate actual × períodos
    if entry_timestamp_ms and position_size_usdt > 0:
        try:
            fr = await get_funding_rate(symbol, exchange=exchange)
            rate = fr.get("rate", 0.0)
            if rate != 0:
                import time as _time
                elapsed_ms = int(_time.time() * 1000) - entry_timestamp_ms
                periods_8h = max(1, elapsed_ms // (8 * 3600 * 1000))
                estimated = rate * position_size_usdt * periods_8h
                logger.debug(
                    f"Funding {symbol}: estimado {estimated:.4f} USDT "
                    f"({rate:.6f} × {position_size_usdt:.0f} × {periods_8h} períodos)"
                )
                return round(estimated, 4)
        except Exception as e:
            logger.debug(f"Funding rate {symbol} no disponible: {e}")

    return 0.0


# ---------------------------------------------------------------------------
# 5. set_leverage
# ---------------------------------------------------------------------------

async def set_leverage(symbol: str, leverage: int, exchange: ccxt_async.bingx) -> bool:
    """
    Configura leverage para el símbolo en BingX.
    Se llama antes de abrir posición.
    """
    bingx_sym = to_bingx_symbol(symbol)

    if DRY_RUN:
        logger.info(f"[DRY_RUN] set_leverage {symbol} -> {leverage}x")
        return True

    try:
        async def _do():
            return await exchange.set_leverage(leverage, bingx_sym, params={'side': 'BOTH'})
        await _retry_async(_do, f"set_leverage {symbol} {leverage}x")
        logger.info(f"[EXEC] Leverage {symbol} -> {leverage}x")
        return True
    except (ExecutionError, OrderRejected) as e:
        logger.error(f"[EXEC] set_leverage {symbol} falló: {e}")
        return False


# ---------------------------------------------------------------------------
# 6. cancel_order
# ---------------------------------------------------------------------------

async def cancel_order(order_id: str, symbol: str, exchange: ccxt_async.bingx) -> bool:
    """
    Cancela una orden pendiente. Retry hasta MAX_RETRIES veces.
    Returns True si se canceló o ya no existía.
    """
    bingx_sym = to_bingx_symbol(symbol)

    if DRY_RUN:
        logger.info(f"[DRY_RUN] cancel_order {symbol} id={order_id}")
        return True

    try:
        async def _do():
            return await exchange.cancel_order(order_id, bingx_sym)
        await _retry_async(_do, f"cancel_order {symbol} {order_id}")
        logger.info(f"[EXEC] Orden cancelada: {symbol} id={order_id}")
        return True
    except ccxt_sync.OrderNotFound:
        logger.info(f"[EXEC] Orden {order_id} ({symbol}) ya no existe")
        return True
    except (ExecutionError, OrderRejected) as e:
        logger.error(f"[EXEC] cancel_order {symbol} {order_id} falló: {e}")
        return False


# ---------------------------------------------------------------------------
# 2. close_position
# ---------------------------------------------------------------------------

async def close_position(
    symbol: str,
    position: dict,
    exchange: ccxt_async.bingx,
) -> dict:
    """
    Cierra una posición abierta con Market contraria + cancela stop vinculado.
    """
    side = position.get("side", "")
    size = position.get("size", 0.0)
    stop_order_id = position.get("stop_order_id")
    bingx_sym = to_bingx_symbol(symbol)

    close_side = "sell" if side == "long" else "buy"

    t0 = _ts_ms()

    if DRY_RUN:
        # Recuperar datos de la posición simulada
        dry_pos = _dry_run_positions.get(symbol, {})
        entry_price = dry_pos.get("entry_price", 0.0) or position.get("entry_price", 0.0)

        # Obtener precio actual del exchange para calcular PnL real
        close_price = 0.0
        try:
            bingx_sym_ticker = to_bingx_symbol(symbol)
            ticker = await exchange.fetch_ticker(bingx_sym_ticker)
            close_price = float(ticker.get("last", 0) or 0)
        except Exception as e:
            logger.warning(f"[DRY_RUN] No se pudo obtener precio de cierre para {symbol}: {e}")

        # Calcular PnL simulado
        pnl = 0.0
        if entry_price > 0 and close_price > 0:
            if side == "long":
                pnl = (close_price - entry_price) * size
            else:
                pnl = (entry_price - close_price) * size

        # Eliminar de posiciones simuladas
        _dry_run_positions.pop(symbol, None)

        logger.info(
            f"[DRY_RUN] CLOSE {side.upper()} {symbol} size={size} @ {close_price:.4f} "
            f"entry={entry_price:.4f} PnL={pnl:+.4f}"
        )
        if stop_order_id:
            logger.info(f"[DRY_RUN] cancel stop {stop_order_id}")
        return {
            "symbol": symbol, "action": "closed_dry", "side": side,
            "close_price": close_price, "pnl": pnl,
            "entry_order_id": None, "stop_cancelled": stop_order_id,
        }

    # Verificar que la posicion existe en BingX antes de enviar cierre
    if not DRY_RUN:
        try:
            live_positions = await get_open_positions(exchange=exchange)
            if symbol not in live_positions:
                logger.warning(
                    f"[EXEC] CLOSE {symbol}: posicion no encontrada en exchange "
                    f"-- cerrada por SL trigger intrabar"
                )
                if stop_order_id:
                    try:
                        await cancel_order(stop_order_id, symbol, exchange)
                    except Exception:
                        pass
                return {
                    "symbol": symbol, "action": "already_closed_by_sl",
                    "side": side, "close_price": 0.0, "pnl": 0.0,
                    "reason": "sl_trigger_detected",
                }
        except Exception as e:
            logger.warning(
                f"[EXEC] No se pudo verificar posicion {symbol}: {e} "
                f"-- continuando con cierre"
            )

    # Enviar orden Market de cierre
    close_order = None
    try:
        async def _do():
            return await exchange.create_order(
                bingx_sym, "market", close_side, size,
                params={"reduceOnly": True},
            )
        close_order = await _retry_async(_do, f"close {side} {symbol}")
    except (ExecutionError, OrderRejected) as e:
        logger.critical(f"[EXEC] CLOSE {symbol} FALLIDO: {e}")
        return {
            "symbol": symbol, "action": "close_failed", "side": side,
            "error": str(e),
        }
    except Exception as e:
        # Fallback: capturar error 101290 "Reduce Only" si la verificacion
        # previa no lo detecto (race condition entre fetch y orden)
        if "101290" in str(e) or "Reduce Only" in str(e):
            logger.warning(
                f"[EXEC] CLOSE {symbol}: Reduce Only error -- "
                f"posicion cerrada por SL trigger o proceso concurrente"
            )
            return {
                "symbol": symbol, "action": "already_closed_by_sl",
                "side": side, "close_price": 0.0, "pnl": 0.0,
                "reason": "sl_trigger_detected",
            }
        raise

    latency = (_ts_ms() - t0) * 1000
    fill_price = float(close_order.get("average", 0) or close_order.get("price", 0) or 0)
    logger.info(
        f"[EXEC] {_now_str()} CLOSE {side.upper()} {symbol} {size} @ market, "
        f"fill={fill_price}, latency={latency:.0f}ms"
    )

    # Cancelar stop vinculado
    stop_cancelled = None
    if stop_order_id:
        await asyncio.sleep(ORDER_DELAY)
        ok = await cancel_order(stop_order_id, symbol, exchange)
        stop_cancelled = stop_order_id if ok else None
        if not ok:
            logger.warning(
                f"[EXEC] Stop {stop_order_id} de {symbol} no se canceló "
                f"(la posición ya está cerrada, stop sin efecto)"
            )

    return {
        "symbol": symbol, "action": "closed", "side": side,
        "close_price": fill_price, "pnl": position.get("unrealized_pnl", 0.0),
        "entry_order_id": close_order.get("id"),
        "stop_cancelled": stop_cancelled,
    }


# ---------------------------------------------------------------------------
# 3. open_position
# ---------------------------------------------------------------------------

async def open_position(
    symbol: str,
    allocation: dict,
    exchange: ccxt_async.bingx,
) -> dict:
    """
    Abre posición con bracket: configura leverage -> Market entry -> Stop Market SL.

    ATOMICIDAD: si la entrada OK pero el stop falla, cierra la posición inmediatamente.
    """
    action = allocation.get("action", "LONG")
    size = allocation.get("size_contracts", 0.0)
    leverage = allocation.get("leverage", 1)
    sl_price = allocation.get("sl_price", 0.0)
    bingx_sym = to_bingx_symbol(symbol)

    entry_side = "buy" if action == "LONG" else "sell"
    stop_side = "sell" if action == "LONG" else "buy"

    if DRY_RUN:
        entry_price = allocation.get("entry_price", 0.0)
        if not entry_price:
            try:
                ticker = await exchange.fetch_ticker(bingx_sym)
                entry_price = float(ticker.get("last", 0) or 0)
            except Exception as e:
                logger.warning(f"[DRY_RUN] fetch_ticker failed for {symbol}: {e}")
        pos_side = "long" if action == "LONG" else "short"
        logger.info(
            f"[DRY_RUN] OPEN {action} {symbol} size={size} lev={leverage}x "
            f"sl={sl_price} entry={entry_price}"
        )
        _dry_run_positions[symbol] = {
            "side": pos_side,
            "size": size,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "leverage": leverage,
            "timestamp": _now_str(),
            "entry_timestamp_ms": int(time.time() * 1000),
            "size_usdt": allocation.get("size_usdt", 0.0),
        }
        return {
            "symbol": symbol, "action": "opened_dry", "side": entry_side,
            "entry_price": entry_price,
            "size": size, "entry_order_id": "dry_entry",
            "stop_order_id": "dry_stop", "sl_price": sl_price,
            "entry_timestamp_ms": _dry_run_positions[symbol]["entry_timestamp_ms"],
        }

    # Paso 1: Leverage
    lev_ok = await set_leverage(symbol, leverage, exchange)
    if not lev_ok:
        return {
            "symbol": symbol, "action": "open_failed",
            "error": "set_leverage failed",
        }

    await asyncio.sleep(ORDER_DELAY)

    # Paso 2: Orden Market de entrada
    t0 = _ts_ms()
    entry_order = None
    try:
        async def _do_entry():
            return await exchange.create_order(
                bingx_sym, "market", entry_side, size,
            )
        entry_order = await _retry_async(_do_entry, f"open {action} {symbol}")
    except (ExecutionError, OrderRejected) as e:
        logger.critical(f"[EXEC] OPEN {action} {symbol} FALLIDO: {e}")
        return {
            "symbol": symbol, "action": "open_failed", "error": str(e),
        }

    entry_latency = (_ts_ms() - t0) * 1000
    fill_price = float(entry_order.get("average", 0) or entry_order.get("price", 0) or 0)
    entry_id = entry_order.get("id", "")

    # v2.3.7 (fix E5): abortar si fill_price invalido. Sin esto,
    # stop_price_bingx = 0 * (1 - SL/100) = 0, BingX rechaza con
    # mensaje oscuro.
    if fill_price <= 0:
        logger.critical(
            f"[EXEC] OPEN {action} {symbol}: fill_price={fill_price} invalido "
            f"(entry_order_id={entry_id}). Abortando creacion de stop."
        )
        return {
            "symbol": symbol, "action": "open_failed",
            "error": f"Invalid fill_price={fill_price}",
            "entry_order_id": entry_id,
        }

    # v2.3.8 (fix B7): usar filled real del entry_order para el stop,
    # no el requested. Si BingX ejecuta parcialmente (raro pero posible
    # al escalar capital cerca de limite de liquidez), stop debe
    # dimensionarse al filled real para evitar sobredimension + rechazo
    # reduceOnly.
    filled_size = float(entry_order.get("filled", 0) or 0)
    if filled_size <= 0:
        logger.warning(
            f"[EXEC] OPEN {action} {symbol}: entry_order sin campo 'filled' "
            f"o 0 (ccxt version antigua?). Usando requested={size} como fallback."
        )
        filled_size = size
    elif filled_size < size:
        logger.warning(
            f"[EXEC] OPEN {action} {symbol}: partial fill detectado "
            f"filled={filled_size} < requested={size}. Stop dimensionado a filled."
        )

    # Compute BingX stop at emergency level (5%) — triggers intrabar on touch.
    # Brain's 3% SL is checked by software each hour against close.
    if action == "LONG":
        stop_price_bingx = fill_price * (1 - SL_EMERGENCY_PCT / 100)
    else:
        stop_price_bingx = fill_price * (1 + SL_EMERGENCY_PCT / 100)

    logger.info(
        f"[EXEC] {_now_str()} OPEN {action} {symbol} {filled_size} @ market, "
        f"SL_brain={sl_price} SL_bingx={stop_price_bingx:.6g} "
        f"[lev={leverage}x, size={allocation.get('size_usdt', 0):.0f} USDT]"
    )

    await asyncio.sleep(ORDER_DELAY)

    # Paso 3: Stop Market vinculado (emergency level, 5% from fill_price)
    stop_order = None
    try:
        async def _do_stop():
            return await exchange.create_order(
                bingx_sym, "market", stop_side, filled_size,
                params={
                    "stopPrice": stop_price_bingx,
                    "reduceOnly": True,
                    "triggerType": "MARK_PRICE",
                },
            )
        stop_order = await _retry_async(_do_stop, f"stop {symbol} @ {stop_price_bingx}")
    except (ExecutionError, OrderRejected) as e:
        # ATOMICIDAD: stop falló, cerrar posición inmediatamente
        logger.critical(
            f"[EXEC] STOP para {symbol} FALLIDO: {e} — "
            f"cerrando posición de emergencia"
        )
        try:
            async def _do_emergency_close():
                # v2.3.8 (fix B7): emergency close sobre filled real.
                return await exchange.create_order(
                    bingx_sym, "market", stop_side, filled_size,
                    params={"reduceOnly": True},
                )
            await _retry_async(_do_emergency_close, f"emergency close {symbol}")
            logger.critical(f"[EXEC] Posición {symbol} cerrada de emergencia (stop no colocado)")
        except Exception as e2:
            logger.critical(
                f"[EXEC] EMERGENCIA: ni stop ni cierre para {symbol} — "
                f"INTERVENCIÓN MANUAL REQUERIDA: {e2}"
            )
        return {
            "symbol": symbol, "action": "open_failed",
            "error": f"Stop placement failed, position emergency-closed: {e}",
        }

    stop_id = stop_order.get("id", "")
    total_latency = (_ts_ms() - t0) * 1000

    logger.info(
        f"[EXEC] {_now_str()} -> entry_id={entry_id}, stop_id={stop_id}, "
        f"fill_price={fill_price}, latency={total_latency:.0f}ms"
    )

    return {
        "symbol": symbol, "action": "opened",
        "side": "long" if action == "LONG" else "short",
        "entry_price": fill_price, "size": filled_size,
        "entry_order_id": entry_id, "stop_order_id": stop_id,
        "sl_price": stop_price_bingx,
        "entry_timestamp_ms": int(time.time() * 1000),
    }


# ---------------------------------------------------------------------------
# 4. update_trailing_stop
# ---------------------------------------------------------------------------

async def update_trailing_stop(
    symbol: str,
    position: dict,
    new_sl_price: float,
    current_orders: list,
    exchange: ccxt_async.bingx,
) -> dict:
    """
    Actualiza trailing stop: cancela viejo, coloca nuevo si mejora.
    Para longs el SL solo sube; para shorts solo baja.

    BingX stop = max(brain_sl, emergency_5%) para longs.
    El stop nunca esta mas lejos del 5% del entry price.
    """
    side = position.get("side", "")
    size = position.get("size", 0.0)
    entry_price = position.get("entry_price", 0.0)
    bingx_sym = to_bingx_symbol(symbol)

    # Enforce emergency floor/ceiling (5% from entry)
    if side == "long" and entry_price > 0:
        emergency_floor = entry_price * (1 - SL_EMERGENCY_PCT / 100)
        effective_sl = max(new_sl_price, emergency_floor)
    elif side == "short" and entry_price > 0:
        emergency_ceiling = entry_price * (1 + SL_EMERGENCY_PCT / 100)
        effective_sl = min(new_sl_price, emergency_ceiling)
    else:
        effective_sl = new_sl_price

    # Buscar stop existente
    existing_stop = None
    for order in current_orders:
        if (order["symbol"] == symbol
                and order["type"] in ("stop_market", "stop", "stop_limit")):
            existing_stop = order
            break

    old_sl = existing_stop["price"] if existing_stop else 0.0

    # Verificar que el nuevo SL mejora (sube para long, baja para short)
    if side == "long" and effective_sl <= old_sl and existing_stop:
        return {
            "symbol": symbol, "action": "stop_unchanged",
            "reason": f"new_sl {effective_sl} <= current_sl {old_sl}",
        }
    if side == "short" and effective_sl >= old_sl and existing_stop and old_sl > 0:
        return {
            "symbol": symbol, "action": "stop_unchanged",
            "reason": f"new_sl {effective_sl} >= current_sl {old_sl}",
        }

    if DRY_RUN:
        # Actualizar SL en posición simulada
        if symbol in _dry_run_positions:
            _dry_run_positions[symbol]["sl_price"] = new_sl_price
        logger.info(
            f"[DRY_RUN] UPDATE_TS {symbol} SL {old_sl}->{new_sl_price}"
        )
        return {
            "symbol": symbol, "action": "stop_updated_dry",
            "old_sl": old_sl, "new_sl": new_sl_price,
            "old_order_id": existing_stop["id"] if existing_stop else None,
            "new_order_id": "dry_stop",
        }

    # Cancelar stop viejo
    old_order_id = None
    if existing_stop:
        old_order_id = existing_stop["id"]
        ok = await cancel_order(old_order_id, symbol, exchange)
        if not ok:
            # Stop no cancelable -- verificar si posicion sigue abierta
            try:
                live_positions = await get_open_positions(exchange=exchange)
            except Exception as e:
                logger.error(f"[EXEC] {symbol} cancel stop failed and can't verify position: {e}")
                return {
                    "symbol": symbol, "action": "stop_update_failed",
                    "error": f"cancel old stop failed and position check failed: {e}",
                }
            if symbol not in live_positions:
                # Posicion cerrada (SL se ejecuto)
                logger.warning(
                    f"[EXEC] {symbol} stop {old_order_id} gone and position closed -- sl_trigger_hit"
                )
                return {
                    "symbol": symbol, "action": "sl_trigger_hit",
                    "old_sl": old_sl, "old_order_id": old_order_id,
                }
            # Posicion sigue abierta, stop desaparecio -- continuar a colocar nuevo
            logger.warning(
                f"[EXEC] {symbol} old stop {old_order_id} gone but position open -- placing new stop"
            )
        await asyncio.sleep(ORDER_DELAY)

    # Colocar stop nuevo (con emergency floor/ceiling aplicado)
    stop_side = "sell" if side == "long" else "buy"
    try:
        async def _do_stop():
            return await exchange.create_order(
                bingx_sym, "market", stop_side, size,
                params={
                    "stopPrice": effective_sl,
                    "reduceOnly": True,
                    "triggerType": "MARK_PRICE",
                },
            )
        new_stop = await _retry_async(_do_stop, f"trailing stop {symbol} @ {effective_sl}")
    except (ExecutionError, OrderRejected) as e:
        logger.critical(
            f"[EXEC] Trailing stop {symbol} FALLIDO: {e} — "
            f"posición SIN STOP, colocando SL de emergencia"
        )
        # Intentar poner un SL de emergencia
        entry_price = position.get("entry_price", 0.0)
        emergency_sl = (
            entry_price * (1 - SL_EMERGENCY_PCT / 100) if side == "long"
            else entry_price * (1 + SL_EMERGENCY_PCT / 100)
        )
        try:
            async def _do_emergency():
                return await exchange.create_order(
                    bingx_sym, "market", stop_side, size,
                    params={
                        "stopPrice": emergency_sl,
                        "reduceOnly": True,
                        "triggerType": "MARK_PRICE",
                    },
                )
            emg = await _retry_async(_do_emergency, f"emergency stop {symbol}")
            logger.warning(
                f"[EXEC] SL emergencia colocado para {symbol} @ {emergency_sl} "
                f"(id={emg.get('id')})"
            )
            return {
                "symbol": symbol, "action": "stop_emergency",
                "old_sl": old_sl, "new_sl": emergency_sl,
                "old_order_id": old_order_id,
                "new_order_id": emg.get("id"),
                "error": str(e),
            }
        except Exception as e2:
            logger.critical(
                f"[EXEC] EMERGENCIA: {symbol} SIN STOP — "
                f"INTERVENCIÓN MANUAL REQUERIDA: {e2}"
            )
            return {
                "symbol": symbol, "action": "stop_update_failed",
                "error": f"Both trailing and emergency stop failed: {e2}",
            }

    new_stop_id = new_stop.get("id", "")
    logger.info(
        f"[EXEC] {_now_str()} UPDATE_TS {symbol} SL {old_sl}->{effective_sl} "
        f"[{old_order_id}->{new_stop_id}]"
    )

    return {
        "symbol": symbol, "action": "stop_updated",
        "old_sl": old_sl, "new_sl": effective_sl,
        "old_order_id": old_order_id, "new_order_id": new_stop_id,
    }


# ---------------------------------------------------------------------------
# 7. reconcile_state
# ---------------------------------------------------------------------------

def reconcile_state(
    allocations: dict,
    positions: dict,
    orders: list,
) -> list[dict]:
    """
    Compara estado deseado vs real y genera lista de acciones ordenadas.

    Orden de ejecución:
        1. emergency_stop (posiciones sin stop)
        2. close (cierres de posiciones)
        3. update_stop (actualización de trailing stops)
        4. open (nuevas entradas)
    """
    # En DRY_RUN, combinar posiciones reales (vacías) con simuladas
    if DRY_RUN and _dry_run_positions:
        positions = dict(positions)  # copia para no mutar el original
        for sym, dry_pos in _dry_run_positions.items():
            if sym not in positions:
                positions[sym] = dry_pos

    actions = []

    # Detectar posiciones sin stop -> EMERGENCIA (skip dry_run positions)
    order_syms_with_stop = set()
    for o in orders:
        if o["type"] in ("stop_market", "stop", "stop_limit"):
            order_syms_with_stop.add(o["symbol"])

    for sym, pos in positions.items():
        # En DRY_RUN, las posiciones simuladas no tienen stops reales en el exchange
        if DRY_RUN and sym in _dry_run_positions:
            continue
        if pos.get("side", "") in ("long", "short") and sym not in order_syms_with_stop:
            # Posición sin stop -> emergencia
            entry_price = pos.get("entry_price", 0.0)
            side = pos["side"]
            emergency_sl = (
                entry_price * (1 - SL_EMERGENCY_PCT / 100) if side == "long"
                else entry_price * (1 + SL_EMERGENCY_PCT / 100)
            )
            actions.append({
                "type": "emergency_stop",
                "symbol": sym,
                "position": pos,
                "sl_price": emergency_sl,
                "reason": "missing stop order",
            })

    # Procesar allocations
    for sym, alloc in allocations.items():
        action = alloc.get("action", "")

        if action in ("CLOSE_LONG", "CLOSE_SHORT"):
            if sym in positions:
                actions.append({
                    "type": "close",
                    "symbol": sym,
                    "position": positions[sym],
                    "reason": alloc.get("reason", "signal_close"),
                })

        elif action == "FLAT":
            # Cluster no operable / low confidence -> cerrar si existe posición
            if sym in positions and positions[sym].get("side", "") in ("long", "short"):
                actions.append({
                    "type": "close",
                    "symbol": sym,
                    "position": positions[sym],
                    "reason": alloc.get("reason", "flat_signal"),
                })

        elif action == "HOLD":
            # Posición mantenida -> actualizar trailing stop si procede
            if sym in positions and positions[sym].get("side", "") in ("long", "short"):
                sl = alloc.get("sl_price", 0.0)
                if sl > 0:
                    actions.append({
                        "type": "update_stop",
                        "symbol": sym,
                        "position": positions[sym],
                        "new_sl": sl,
                    })

        elif action in ("LONG", "SHORT"):
            has_position = (
                sym in positions
                and positions[sym].get("side", "") in ("long", "short")
            )

            if not has_position:
                # Nueva entrada
                actions.append({
                    "type": "open",
                    "symbol": sym,
                    "allocation": alloc,
                })
            else:
                # Ya existe posición -> solo actualizar trailing stop si procede
                pos = positions[sym]
                pos_side = pos["side"]
                alloc_side = "long" if action == "LONG" else "short"

                if pos_side == alloc_side:
                    # Misma dirección -> actualizar TS
                    sl = alloc.get("sl_price", 0.0)
                    if sl > 0:
                        actions.append({
                            "type": "update_stop",
                            "symbol": sym,
                            "position": pos,
                            "new_sl": sl,
                        })
                else:
                    # Dirección opuesta -> cerrar y reabrir
                    actions.append({
                        "type": "close",
                        "symbol": sym,
                        "position": pos,
                        "reason": "direction_reversal",
                    })
                    actions.append({
                        "type": "open",
                        "symbol": sym,
                        "allocation": alloc,
                    })

        # HOLD: no hacer nada
        # Posiciones sin allocation: mantener (de ciclo anterior)

    # Ordenar: emergency_stop -> close -> update_stop -> open
    priority = {"emergency_stop": 0, "close": 1, "update_stop": 2, "open": 3}
    actions.sort(key=lambda a: priority.get(a["type"], 99))

    return actions


# ---------------------------------------------------------------------------
# 1. execute_cycle
# ---------------------------------------------------------------------------

async def execute_cycle(
    allocations: dict,
    current_positions: dict,
    current_orders: list,
    exchange: ccxt_async.bingx | None = None,
) -> ExecutionReport:
    """
    Procesa todas las allocaciones de un ciclo:
    1. Reconcilia estado deseado vs real
    2. Ejecuta acciones en orden: emergencias -> cierres -> stops -> entradas
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_bingx_exchange()

    report = ExecutionReport(timestamp=_now_str())
    actions = reconcile_state(allocations, current_positions, current_orders)

    n_emergency = sum(1 for a in actions if a["type"] == "emergency_stop")
    n_close = sum(1 for a in actions if a["type"] == "close")
    n_update = sum(1 for a in actions if a["type"] == "update_stop")
    n_open = sum(1 for a in actions if a["type"] == "open")
    logger.info(
        f"[EXEC] Ciclo: {n_emergency} emergencias, {n_close} cierres, "
        f"{n_update} TS updates, {n_open} aperturas"
    )

    for action in actions:
        atype = action["type"]
        sym = action["symbol"]

        try:
            if atype == "emergency_stop":
                logger.critical(
                    f"[EXEC] EMERGENCIA: {sym} sin stop — "
                    f"colocando SL @ {action['sl_price']}"
                )
                result = await update_trailing_stop(
                    sym, action["position"], action["sl_price"],
                    current_orders, exchange,
                )
                if result.get("action", "").startswith("stop"):
                    report.stops_placed.append(result)
                else:
                    report.errors.append(result)

            elif atype == "close":
                result = await close_position(sym, action["position"], exchange)
                if result.get("action") in ("closed", "closed_dry"):
                    # Obtener funding acumulado durante la vida de la posicion
                    pos = action["position"]
                    funding_paid = await _get_position_funding(
                        sym,
                        entry_timestamp_ms=pos.get("entry_timestamp_ms"),
                        position_size_usdt=pos.get("notional", 0) or pos.get("size", 0) * pos.get("entry_price", 0),
                        exchange=exchange,
                    )
                    result["funding_paid"] = funding_paid

                    report.positions_closed.append(result)
                    # Log del trade
                    log_trade({
                        "symbol": sym,
                        "side": pos.get("side", ""),
                        "entry_price": pos.get("entry_price", 0.0),
                        "exit_price": result.get("close_price", 0.0),
                        "size_usdt": pos.get("size_usdt", 0.0),
                        "pnl_usdt": result.get("pnl", 0.0),
                        "reason_exit": action.get("reason", ""),
                        "funding_paid": funding_paid,
                        "entry_timestamp_ms": pos.get("entry_timestamp_ms", 0),
                    })
                elif result.get("action") == "already_closed_by_sl":
                    # Posicion cerrada por SL trigger de BingX intrabar
                    pos = action["position"]
                    sl_price = pos.get("sl_price", 0.0)
                    entry_price = pos.get("entry_price", 0.0)
                    side = pos.get("side", "")
                    # Estimar PnL usando el precio de SL como exit
                    pnl_est = 0.0
                    if entry_price > 0 and sl_price > 0:
                        if side == "long":
                            pnl_est = (sl_price - entry_price) / entry_price * pos.get("size_usdt", 0.0)
                        else:
                            pnl_est = (entry_price - sl_price) / entry_price * pos.get("size_usdt", 0.0)
                    result["close_price"] = sl_price
                    result["pnl"] = round(pnl_est, 4)
                    result["funding_paid"] = 0.0
                    report.positions_closed.append(result)
                    log_trade({
                        "symbol": sym,
                        "side": side,
                        "entry_price": entry_price,
                        "exit_price": sl_price,
                        "size_usdt": pos.get("size_usdt", 0.0),
                        "pnl_usdt": round(pnl_est, 4),
                        "reason_exit": "sl_trigger_hit",
                        "funding_paid": 0.0,
                        "entry_timestamp_ms": pos.get("entry_timestamp_ms", 0),
                    })
                    logger.info(
                        f"[EXEC] {sym} registrado como sl_trigger_hit: "
                        f"entry={entry_price} exit~={sl_price} PnL~={pnl_est:+.4f}"
                    )
                else:
                    report.orders_failed.append(result)

            elif atype == "update_stop":
                result = await update_trailing_stop(
                    sym, action["position"], action["new_sl"],
                    current_orders, exchange,
                )
                if "updated" in result.get("action", ""):
                    report.stops_updated.append(result)
                # stop_unchanged es OK, no es error

            elif atype == "open":
                alloc = action["allocation"]
                result = await open_position(sym, alloc, exchange)
                if result.get("action") in ("opened", "opened_dry"):
                    report.orders_sent.append(result)
                    report.stops_placed.append({
                        "symbol": sym,
                        "stop_order_id": result.get("stop_order_id"),
                        "sl_price": result.get("sl_price"),
                    })
                else:
                    report.orders_failed.append(result)

        except ExecutionError as e:
            logger.critical(f"[EXEC] Error crítico en {atype} {sym}: {e}")
            report.errors.append({"symbol": sym, "type": atype, "error": str(e)})
        except Exception as e:
            logger.error(f"[EXEC] Error inesperado en {atype} {sym}: {e}")
            report.errors.append({"symbol": sym, "type": atype, "error": str(e)})

        # Delay entre órdenes
        await asyncio.sleep(ORDER_DELAY)

    if own_exchange:
        await exchange.close()

    # Resumen
    logger.info(
        f"[EXEC] Ciclo completado: {len(report.orders_sent)} enviadas, "
        f"{len(report.positions_closed)} cerradas, "
        f"{len(report.stops_updated)} TS actualizados, "
        f"{len(report.errors)} errores"
    )

    return report


# ---------------------------------------------------------------------------
# Trade log (CSV append-only)
# ---------------------------------------------------------------------------

def log_trade(trade: dict, filepath: str | Path | None = None):
    """
    Appends trade al CSV de historial.

    Columnas: timestamp, symbol, side, entry_price, exit_price, size_usdt,
              pnl_pct, pnl_usdt, reason_exit
    """
    filepath = Path(filepath) if filepath else TRADE_LOG_PATH

    row = {
        "timestamp": _now_str(),
        "symbol": trade.get("symbol", ""),
        "side": trade.get("side", ""),
        "entry_price": trade.get("entry_price", 0.0),
        "exit_price": trade.get("exit_price", 0.0),
        "size_usdt": trade.get("size_usdt", 0.0),
        "pnl_usdt": trade.get("pnl_usdt", 0.0),
        "funding_paid": trade.get("funding_paid", 0.0),
        "reason_exit": trade.get("reason_exit", ""),
        "flag": trade.get("flag", ""),
        "entry_timestamp_ms": trade.get("entry_timestamp_ms", 0),
    }

    # Calcular pnl_pct
    entry = row["entry_price"]
    exit_ = row["exit_price"]
    if entry and entry > 0 and exit_ and exit_ > 0:
        if row["side"] == "long":
            row["pnl_pct"] = round((exit_ / entry - 1) * 100, 4)
        elif row["side"] == "short":
            row["pnl_pct"] = round((1 - exit_ / entry) * 100, 4)
        else:
            row["pnl_pct"] = 0.0
    else:
        row["pnl_pct"] = 0.0

    fieldnames = [
        "timestamp", "symbol", "side", "entry_price", "exit_price",
        "size_usdt", "pnl_pct", "pnl_usdt", "funding_paid", "reason_exit",
        "flag", "entry_timestamp_ms",
    ]

    file_exists = filepath.exists()
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# __main__ — Tests
# ---------------------------------------------------------------------------

def _test_reconcile():
    """Muestra reconciliación con datos mock."""
    print("=" * 60)
    print("EXECUTION MANAGER — Test reconcile")
    print("=" * 60)

    allocations = {
        "BTC/USDT": {
            "action": "LONG", "size_usdt": 500, "size_contracts": 0.0077,
            "leverage": 1, "sl_price": 63469.14, "reason": "ma_cross",
        },
        "ETH/USDT": {
            "action": "CLOSE_LONG", "reason": "sl_exit",
        },
        "SOL/USDT": {
            "action": "LONG", "size_usdt": 300, "size_contracts": 1.67,
            "leverage": 3, "sl_price": 174.6, "reason": "zone_entry",
        },
        "DOGE/USDT": {
            "action": "FLAT", "reason": "low_confidence",
        },
    }

    positions = {
        "ETH/USDT": {
            "side": "long", "size": 0.1, "entry_price": 3500.0,
            "unrealized_pnl": 50.0, "leverage": 2, "stop_order_id": "stop_eth",
        },
        "DOGE/USDT": {
            "side": "long", "size": 1000.0, "entry_price": 0.15,
            "unrealized_pnl": -5.0, "leverage": 1, "stop_order_id": "stop_doge",
        },
        "LINK/USDT": {
            "side": "long", "size": 10.0, "entry_price": 15.0,
            "unrealized_pnl": 3.0, "leverage": 2, "stop_order_id": None,
        },
    }

    orders = [
        {"id": "stop_eth", "symbol": "ETH/USDT", "type": "stop_market",
         "side": "sell", "price": 3395.0, "amount": 0.1},
        {"id": "stop_doge", "symbol": "DOGE/USDT", "type": "stop_market",
         "side": "sell", "price": 0.1455, "amount": 1000.0},
    ]

    actions = reconcile_state(allocations, positions, orders)

    print(f"\nAcciones generadas ({len(actions)}):")
    for i, a in enumerate(actions):
        print(f"  {i+1}. [{a['type'].upper()}] {a['symbol']}", end="")
        if a["type"] == "open":
            alloc = a["allocation"]
            print(f" -> {alloc['action']} {alloc.get('size_usdt', 0)} USDT "
                  f"sl={alloc.get('sl_price', 0)}")
        elif a["type"] == "close":
            print(f" -> reason={a.get('reason', '')}")
        elif a["type"] == "emergency_stop":
            print(f" -> SL @ {a['sl_price']:.4f} (EMERGENCY)")
        elif a["type"] == "update_stop":
            print(f" -> new SL={a['new_sl']}")
        else:
            print()


async def _test_dry_run():
    """Simula un ciclo completo en DRY_RUN."""
    print("=" * 60)
    print("EXECUTION MANAGER — Dry-run cycle")
    print("=" * 60)

    global DRY_RUN
    DRY_RUN = True

    allocations = {
        "BTC/USDT": {
            "action": "LONG", "size_usdt": 500, "size_contracts": 0.0077,
            "leverage": 1, "sl_price": 63469.14, "entry_price": 65000.0,
            "reason": "ma_cross",
        },
        "ETH/USDT": {
            "action": "CLOSE_LONG", "reason": "sl_exit",
        },
        "SOL/USDT": {
            "action": "SHORT", "size_usdt": 300, "size_contracts": 1.67,
            "leverage": 3, "sl_price": 185.4, "entry_price": 180.0,
            "reason": "zone_entry",
        },
    }

    positions = {
        "ETH/USDT": {
            "side": "long", "size": 0.1, "entry_price": 3500.0,
            "unrealized_pnl": 50.0, "leverage": 2, "stop_order_id": "stop_eth",
        },
    }

    orders = [
        {"id": "stop_eth", "symbol": "ETH/USDT", "type": "stop_market",
         "side": "sell", "price": 3395.0, "amount": 0.1},
    ]

    # No necesitamos exchange real en DRY_RUN, pero execute_cycle crea uno
    # Mock mínimo para evitar error de credenciales
    class MockExchange:
        async def close(self):
            pass

    report = await execute_cycle(
        allocations, positions, orders, exchange=MockExchange()
    )

    print(f"\n--- ExecutionReport ---")
    print(f"Timestamp: {report.timestamp}")
    print(f"Orders sent:     {len(report.orders_sent)}")
    print(f"Positions closed: {len(report.positions_closed)}")
    print(f"Stops updated:   {len(report.stops_updated)}")
    print(f"Stops placed:    {len(report.stops_placed)}")
    print(f"Errors:          {len(report.errors)}")

    for item in report.orders_sent:
        print(f"  SENT: {item['symbol']} {item['action']} size={item.get('size', 0)}")
    for item in report.positions_closed:
        print(f"  CLOSED: {item['symbol']} {item['side']} pnl={item.get('pnl', 0)}")
    for item in report.errors:
        print(f"  ERROR: {item}")


async def _test_connection():
    """Test de conexión real a BingX (solo lectura)."""
    print("=" * 60)
    print("EXECUTION MANAGER — Test conexión BingX")
    print("=" * 60)

    try:
        exchange = _create_bingx_exchange()
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    try:
        bal = await get_balance(exchange=exchange)
        print(f"\nBalance: {bal['total']:.2f} USDT (libre: {bal['free']:.2f})")

        positions = await get_open_positions(exchange=exchange)
        if positions:
            print(f"\nPosiciones ({len(positions)}):")
            for sym, pos in positions.items():
                print(f"  {sym}: {pos['side']} x{pos['size']} @ {pos['entry_price']:.2f} "
                      f"stop_id={pos.get('stop_order_id')}")
        else:
            print("\nSin posiciones abiertas")

        orders = await get_open_orders(exchange=exchange)
        if orders:
            print(f"\nÓrdenes ({len(orders)}):")
            for o in orders:
                print(f"  {o['symbol']}: {o['type']} {o['side']} @ {o['price']} x{o['amount']}")
        else:
            print("\nSin órdenes abiertas")

    finally:
        await exchange.close()

    print("\nTest conexión completado.")


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if "--dry-run" in sys.argv:
        asyncio.run(_test_dry_run())
    elif "--reconcile" in sys.argv:
        _test_reconcile()
    else:
        asyncio.run(_test_connection())
