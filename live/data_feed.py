"""
data_feed.py — Módulo de datos en tiempo real (Kraken Futures)

Única misión: obtener datos OHLCV limpios de Kraken Futures y estado de cuenta/posiciones.
Es el único módulo que habla con el exchange. Todos los demás reciben DataFrames ya procesados.

Migración BingX→Kraken Futures (Etapa 1, fase PAPER demo-futures.kraken.com):
producto = PF_ linear (USD-margined, multi-collateral, contractSize=1, size en
unidades base). Símbolo ccxt unificado = 'BASE/USD:USD' (ccxt normaliza XBT→BTC).
Demo vs live se controla con env KRAKEN_DEMO (set_sandbox_mode). Ver
project_kraken_migration_viability_audit + reporte T3.1-Et1.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path

import re

import aiohttp
import ccxt.async_support as ccxt_async
import ccxt as ccxt_sync
import pandas as pd

logger = logging.getLogger("data_feed")


def _sanitize_error(error: Exception) -> str:
    """Elimina parámetros sensibles (signature, timestamp, apiKey) de mensajes de error ccxt."""
    msg = str(error)
    # Eliminar parámetros sensibles de URLs en el mensaje (Kraken usa Nonce/Authent)
    msg = re.sub(
        r'(signature|apiKey|timestamp|secretKey|nonce|Authent|APIKey)=[^&\s\'")\]]+',
        r'\1=***', msg,
    )
    return msg


async def _retry_async(coro_factory, name: str, max_retries: int = 3,
                       base_delay: float = 0.5):
    """
    v2.3.8 (fix B4): wrapper de retry con backoff exponencial para
    llamadas async a BingX. coro_factory es callable sin args que
    retorna coroutine (necesario porque no se puede re-await un
    coroutine ya agotado).

    AuthenticationError se re-lanza sin retry — reintentar con
    credenciales invalidas es inutil y ruidoso.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except ccxt_sync.AuthenticationError:
            raise
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"{name} intento {attempt+1}/{max_retries} "
                    f"fallo ({_sanitize_error(e)}), retry en {delay}s"
                )
                await asyncio.sleep(delay)
    logger.error(f"{name} agoto retries tras {max_retries} intentos")
    raise last_exc

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
KRAKEN_API_KEY = os.environ.get("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.environ.get("KRAKEN_API_SECRET")
# Demo (paper) vs live: demo-futures.kraken.com requiere claves DEMO separadas.
# La clave la crea Ricardo en el momento del despliegue (Etapa 3) y la pega
# directo en la instancia como env var — NUNCA en chat/local.
KRAKEN_DEMO = os.environ.get("KRAKEN_DEMO", "").strip().lower() in ("1", "true", "yes", "on")

# Intentar leer de credentials.json si no hay env vars
_creds_path = Path(__file__).parent.parent / "credentials.json"
if not KRAKEN_API_KEY and _creds_path.exists():
    with open(_creds_path) as f:
        _creds = json.load(f)
    KRAKEN_API_KEY = _creds.get("KRAKEN_API_KEY", "")
    KRAKEN_API_SECRET = _creds.get("KRAKEN_API_SECRET", "")

OHLCV_LIMIT = 1500          # velas 1h (~62 días), suficiente para Z_ATR(1000) + warmup
KRAKEN_MAX_CANDLES = 1000   # máximo conservador por petición (charts/v1 ~1000 recientes)
TIMEFRAME = "1h"
MAX_RETRIES = 3
RETRY_DELAY = 0.5           # segundos
REQUEST_TIMEOUT = 10000      # ms

# ---------------------------------------------------------------------------
# Universo de símbolos — fuente única en master.py CONFIG['symbols']
# ---------------------------------------------------------------------------
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from master import CONFIG as _MASTER_CONFIG
MASTER_SYMBOLS = _MASTER_CONFIG['symbols']

# ---------------------------------------------------------------------------
# Mapping de símbolos: master.py format <-> Kraken Futures ccxt format
# ---------------------------------------------------------------------------
# Verificado primary-source (ccxt krakenfutures.fetch_markets + instruments
# endpoint): el perp PF_ linear se expone como símbolo unificado 'BASE/USD:USD'
# (USD-quoted, USD-settled, linear=true). ccxt normaliza XBT→BTC vía
# commonCurrencies, y POL/RENDER coinciden con el master, así que la regla es
# determinista: 'X/USDT' (master) → 'X/USD:USD' (Kraken ccxt). Se valida
# fail-loud contra exchange.markets en el arranque (validate_symbol_map).


def to_kraken_symbol(master_symbol: str) -> str:
    """Convierte 'BTC/USDT' (master.py) a 'BTC/USD:USD' (Kraken Futures PF_ linear ccxt)."""
    base = master_symbol.split("/")[0]
    return f"{base}/USD:USD"


def from_kraken_symbol(kraken_symbol: str) -> str:
    """Convierte 'BTC/USD:USD' (Kraken ccxt) a 'BTC/USDT' (formato master.py)."""
    base = kraken_symbol.split("/")[0]
    return f"{base}/USDT"


SYMBOL_MAP = {s: to_kraken_symbol(s) for s in MASTER_SYMBOLS}
SYMBOL_MAP_INV = {v: k for k, v in SYMBOL_MAP.items()}


def validate_symbol_map(exchange) -> list[str]:
    """Verifica fail-loud que cada símbolo Kraken mapeado existe en
    exchange.markets (tras load_markets). Retorna lista de símbolos master
    NO encontrados (vacía = todo OK). Llamado por live_engine post-load_markets.

    §12 L38: no se asume que el mapeo determinista 'X/USD:USD' resuelve a un
    mercado real — se mide contra el exchange. Un símbolo ausente (delisted,
    base distinta) se reporta, no se traga silenciosamente.
    """
    markets = getattr(exchange, "markets", None) or {}
    if not markets:
        return []  # markets no cargados (mock/test) — sin validación posible
    missing = []
    for master, kraken_sym in SYMBOL_MAP.items():
        if kraken_sym not in markets:
            missing.append(master)
    return missing


# ---------------------------------------------------------------------------
# Factory del exchange
# ---------------------------------------------------------------------------
def _create_aiohttp_session() -> aiohttp.ClientSession:
    """Crea sesión aiohttp con ThreadedResolver (evita aiodns DNS failures en Windows)."""
    resolver = aiohttp.resolver.ThreadedResolver()
    connector = aiohttp.TCPConnector(resolver=resolver)
    return aiohttp.ClientSession(connector=connector)


def _create_kraken_exchange(api_key=None, api_secret=None) -> ccxt_async.krakenfutures:
    key = api_key or KRAKEN_API_KEY
    secret = api_secret or KRAKEN_API_SECRET
    if not key or not secret:
        raise RuntimeError(
            "Credenciales Kraken Futures no encontradas. "
            "Setear KRAKEN_API_KEY/KRAKEN_API_SECRET como env vars o en credentials.json"
        )
    ex = ccxt_async.krakenfutures({
        "apiKey": key,
        "secret": secret,
        # Kraken tolera nonces fuera de orden solo "brevemente" → mantener
        # rate-limit ON para serializar y evitar bursts que desordenen el nonce.
        "enableRateLimit": True,
        "timeout": REQUEST_TIMEOUT,
        "session": _create_aiohttp_session(),
    })
    if KRAKEN_DEMO:
        # demo-futures.kraken.com — sandbox oficial (paper). Idéntico a prod
        # salvo la base URL. Requiere claves DEMO separadas (no las de prod).
        ex.set_sandbox_mode(True)
    return ex


# ---------------------------------------------------------------------------
# 1. download_all_ohlcv
# ---------------------------------------------------------------------------
async def download_all_ohlcv(
    symbols: list | None = None,
    limit: int = OHLCV_LIMIT,
    exchange: ccxt_async.krakenfutures | None = None,
) -> dict[str, pd.DataFrame | None]:
    """
    Descarga OHLCV de BingX Futures para todos los símbolos en paralelo.

    Args:
        symbols: lista en formato master.py ('BTC/USDT'). Default = MASTER_SYMBOLS.
        limit: cantidad de velas 1h a descargar (default 500).
        exchange: instancia ccxt reutilizable (se crea una si no se pasa).

    Returns:
        {'BTC/USDT': DataFrame(timestamp, open, high, low, close, volume), ...}
        Si un símbolo falla tras MAX_RETRIES, su valor es None.
    """
    symbols = symbols or MASTER_SYMBOLS
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    t0 = time.perf_counter()

    async def _fetch_paged(kraken_sym: str) -> list:
        """Descarga `limit` velas 1h de Kraken charts/v1. Para limit grande,
        pagina hacia atrás con `since` (Kraken ~KRAKEN_MAX_CANDLES por petición).
        Retorna lista ccxt [[ts,o,h,l,c,v],...] ascendente, últimas `limit`."""
        if limit <= KRAKEN_MAX_CANDLES:
            return await exchange.fetch_ohlcv(kraken_sym, TIMEFRAME, limit=limit)
        now_ms = int(time.time() * 1000)
        cursor = now_ms - limit * 3_600_000  # 1h por vela
        collected: dict[int, list] = {}
        while len(collected) < limit:
            page = await exchange.fetch_ohlcv(
                kraken_sym, TIMEFRAME, since=cursor, limit=KRAKEN_MAX_CANDLES
            )
            if not page:
                break
            for row in page:
                collected[int(row[0])] = row
            last_ts = int(page[-1][0])
            if last_ts < cursor:  # sin progreso → cortar
                break
            cursor = last_ts + 3_600_000
            if cursor >= now_ms:
                break
        rows = [collected[k] for k in sorted(collected)]
        return rows[-limit:]

    async def _fetch_one(sym: str) -> tuple[str, pd.DataFrame | None]:
        kraken_sym = to_kraken_symbol(sym)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                ohlcv = await _fetch_paged(kraken_sym)
                # Lista vacia sin excepcion dejaba el simbolo con DataFrame
                # vacio silenciosamente y brain saltaba evaluacion. Levantar
                # explicitamente activa el retry del outer for attempt.
                if not ohlcv:
                    raise ValueError(
                        f"fetch_ohlcv retorno lista vacia para {kraken_sym}"
                    )
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
                df = (
                    df.drop_duplicates(subset=["timestamp"])
                    .sort_values("timestamp")
                    .reset_index(drop=True)
                )
                # NOTA fidelidad (objetivo Etapa 4 paper): el hack forming-bar
                # de BingX se eliminó. charts/v1 de Kraken devuelve la vela en
                # curso como último elemento — verificar empíricamente en demo
                # que iloc[-1] es el bar forming (convención del brain on-close).
                return sym, df
            except Exception as e:
                logger.warning(f"{sym}: retry {attempt}/{MAX_RETRIES}, error: {_sanitize_error(e)}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
        logger.warning(f"{sym}: FALLIDO tras {MAX_RETRIES} intentos")
        return sym, None

    results = await asyncio.gather(*[_fetch_one(s) for s in symbols])

    if own_exchange:
        await exchange.close()

    elapsed = time.perf_counter() - t0
    ok = sum(1 for _, df in results if df is not None)
    fail = len(results) - ok
    logger.info(f"{ok}/{len(symbols)} símbolos descargados en {elapsed:.2f}s" +
                (f" ({fail} fallidos)" if fail else ""))

    return {sym: df for sym, df in results}


# ---------------------------------------------------------------------------
# 2. get_open_positions
# ---------------------------------------------------------------------------
async def get_open_positions(
    exchange: ccxt_async.krakenfutures | None = None,
) -> dict[str, dict]:
    """
    Consulta posiciones abiertas en BingX Futures.

    Returns:
        {'BTC/USDT': {
            'side': 'long',
            'size': 0.01,
            'entry_price': 65000.0,
            'unrealized_pnl': 120.5,
            'leverage': 10,
            'stop_order_id': None
        }, ...}
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    t0 = time.perf_counter()
    try:
        # v2.3.8 (fix B4): retry con backoff para hiccups transitorios.
        positions = await _retry_async(
            lambda: exchange.fetch_positions(),
            name="fetch_positions",
        )
    except ccxt_sync.AuthenticationError:
        logger.critical("Credenciales Kraken Futures inválidas — deteniendo.")
        if own_exchange:
            await exchange.close()
        raise
    except Exception as e:
        logger.critical(f"Error obteniendo posiciones: {_sanitize_error(e)}")
        if own_exchange:
            await exchange.close()
        raise

    result = {}
    for pos in positions:
        size = float(pos.get("contracts", 0) or 0)
        if size == 0:
            continue
        master_sym = from_kraken_symbol(pos["symbol"])
        side = pos.get("side", "").lower()
        entry_px = float(pos.get("entryPrice", 0) or 0)
        # BingX via ccxt a veces provee "notional" directo (valor USDT de
        # la posicion). Si esta, usarlo. Si no, fallback a size*entry_price.
        # Edge case entry_price=0 (posicion huerfana rara) -> size_usdt=0
        # con WARNING. Fix del bug historico trade_history.csv size_usdt=0
        # (134/135 trades pre-fix).
        notional = float(pos.get("notional", 0) or 0)
        size_usdt = notional if notional > 0 else (size * entry_px)
        if size_usdt == 0 and size > 0:
            logger.warning(
                f"[get_open_positions] {master_sym} size_usdt=0 "
                f"with size={size}, entry_price={entry_px}"
            )
        result[master_sym] = {
            "side": side,
            "size": size,
            "entry_price": entry_px,
            "size_usdt": size_usdt,
            "unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),
            "leverage": int(pos.get("leverage", 1) or 1),
            "stop_order_id": None,  # se enlaza desde execution_manager
        }

    elapsed = time.perf_counter() - t0
    if result:
        summary = ", ".join(f"{s} {v['side']}" for s, v in result.items())
        logger.info(f"{len(result)} posiciones abiertas: {summary} ({elapsed:.2f}s)")
    else:
        logger.info(f"Sin posiciones abiertas ({elapsed:.2f}s)")

    # Vincular stops pendientes a posiciones
    if result:
        try:
            orders = await get_open_orders(exchange=exchange)
            for order in orders:
                sym = order["symbol"]
                if sym in result and order["type"] in ("stop_market", "stop", "stop_limit"):
                    result[sym]["stop_order_id"] = order["id"]
        except Exception as e:
            logger.warning(f"No se pudieron vincular stops a posiciones: {_sanitize_error(e)}")

    if own_exchange:
        await exchange.close()

    return result


# ---------------------------------------------------------------------------
# 3. get_open_orders
# ---------------------------------------------------------------------------
async def get_open_orders(
    symbol: str | None = None,
    exchange: ccxt_async.krakenfutures | None = None,
) -> list[dict]:
    """
    Consulta órdenes abiertas (stops pendientes, límites, etc.).

    Args:
        symbol: formato master.py ('BTC/USDT'). None = todas.

    Returns:
        [{'id': 'ord_123', 'symbol': 'BTC/USDT', 'type': 'stop_market',
          'side': 'sell', 'price': 62000.0, 'amount': 0.01}, ...]
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    kraken_sym = to_kraken_symbol(symbol) if symbol else None
    try:
        # v2.3.8 (fix B4): retry con backoff para hiccups transitorios.
        raw_orders = await _retry_async(
            lambda: exchange.fetch_open_orders(kraken_sym),
            name="fetch_open_orders",
        )
    except Exception as e:
        logger.error(f"Error obteniendo órdenes abiertas: {_sanitize_error(e)}")
        if own_exchange:
            await exchange.close()
        raise

    result = []
    for o in raw_orders:
        # Kraken Futures stop orders (orderType='stp'/'take_profit') llegan vía
        # ccxt con triggerPrice/stopLossPrice/stopPrice y/o info.orderType.
        # Normalizar a "stop_market" para que reconcile_state los reconozca
        # como stops (el SL server-side reduce-only que coloca open_position).
        order_type = o.get("type", "")
        info = o.get("info", {}) or {}
        raw_ot = str(info.get("orderType", "")).lower()
        trigger_px = (
            o.get("triggerPrice")
            or o.get("stopLossPrice")
            or o.get("stopPrice")
            or info.get("stopPrice")
        )
        if trigger_px or raw_ot in ("stp", "take_profit", "stop"):
            order_type = "stop_market"
        result.append({
            "id": o["id"],
            "symbol": from_kraken_symbol(o["symbol"]),
            "type": order_type,
            "side": o.get("side", ""),
            "price": float(trigger_px or o.get("price") or 0),
            "amount": float(o.get("amount", 0) or o.get("remaining", 0) or 0),
        })

    if own_exchange:
        await exchange.close()

    return result


# ---------------------------------------------------------------------------
# 3b. get_recent_closed_fill (v2.7.1 — recuperar fill REAL de cierre exchange-side)
# ---------------------------------------------------------------------------
async def get_recent_closed_fill(
    symbol: str,
    since_ms: int | None = None,
    exchange: ccxt_async.krakenfutures | None = None,
) -> dict | None:
    """Recupera el fill REAL del cierre exchange-side (SL trigger / liquidación /
    cierre manual) de un símbolo, vía fetch_my_trades. v2.7.1 — alimenta ORPHAN_CLOSE
    para registrar PnL real (no estimado) + alerta Telegram.

    Args:
        symbol: formato master.py ('DOGE/USDT').
        since_ms: epoch ms desde el que buscar trades (típicamente entry_timestamp_ms
            de la posición huérfana). None = última hora.

    Returns:
        {'price': fill_price, 'amount': base_amount, 'cost': quote_usdt,
         'fee_usdt': fee, 'timestamp_ms': ts, 'side': 'buy'/'sell'} del trade de
         cierre más reciente, o None si el exchange no devuelve fills (retención/API).
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    kraken_sym = to_kraken_symbol(symbol)
    if since_ms is None:
        since_ms = int(time.time() * 1000) - 3_600_000  # última hora

    try:
        trades = await _retry_async(
            lambda: exchange.fetch_my_trades(kraken_sym, since=since_ms, limit=50),
            name="fetch_my_trades",
        )
    except Exception as e:
        logger.warning(f"[ORPHAN_FILL] {symbol}: fetch_my_trades falló: {_sanitize_error(e)}")
        if own_exchange:
            await exchange.close()
        return None
    finally:
        if own_exchange and exchange:
            try:
                await exchange.close()
            except Exception:
                pass

    if not trades:
        return None

    # El trade de cierre es el más reciente (mayor timestamp).
    last = max(trades, key=lambda t: t.get("timestamp", 0) or 0)

    # Kraken Futures (migración): a diferencia de BingX, ccxt mapea BIEN los
    # campos de un fill PF_ linear (contractSize=1) — NO hay hazard "25×".
    # Verificado primary-source (ccxt krakenfutures.parseTrade): para mercado
    # linear, `amount` = size base y `cost = stringMul(amount, price)` en USD.
    # El raw fill de Kraken (/fills) trae size/price pero NO volume/amount/
    # commission (los keys de BingX) → se usa la ruta ccxt-unified limpia.
    price = float(last.get("price", 0) or 0)
    base_amount = float(last.get("amount", 0) or 0)        # size base (PF_ contractSize=1)
    quote_cost = float(last.get("cost", 0) or 0)           # USD = price × size (ccxt-computed)
    if quote_cost <= 0 and price > 0 and base_amount > 0:
        quote_cost = price * base_amount                    # gate ortogonal: cost ≈ price×amount

    # Fee: el /fills de Kraken NO trae fee; ccxt SINTETIZA fee.cost = rate×cost
    # (estimación con la tasa estática del mercado, NO el fee real cobrado).
    # Se usa como estimación; el fee real vive en un endpoint account-log
    # separado (refinamiento futuro / objetivo de fidelidad Etapa 4 paper).
    fee_cost = 0.0
    fee = last.get("fee") or {}
    if isinstance(fee, dict):
        fee_cost = abs(float(fee.get("cost", 0) or 0))

    return {
        "price": price,
        "amount": base_amount,          # base units (ccxt size — PF_ linear contractSize=1)
        "cost": quote_cost,             # USD notional (ccxt price×amount; gate cost≈price×amount)
        "fee_usdt": fee_cost,           # ESTIMACIÓN ccxt (rate×cost); fee real = account-log
        "timestamp_ms": int(last.get("timestamp", 0) or 0),
        "side": last.get("side", ""),
    }


# ---------------------------------------------------------------------------
# 4. get_balance
# ---------------------------------------------------------------------------
async def get_balance(
    exchange: ccxt_async.krakenfutures | None = None,
) -> dict:
    """
    Returns:
        {'total': 10000.0, 'free': 7500.0, 'used': 2500.0, 'currency': 'USDT'}
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    try:
        # v2.3.8 (fix B4): retry con backoff para hiccups transitorios.
        bal = await _retry_async(
            lambda: exchange.fetch_balance(),
            name="fetch_balance",
        )
    except ccxt_sync.AuthenticationError:
        logger.critical("Credenciales Kraken Futures inválidas — deteniendo.")
        if own_exchange:
            await exchange.close()
        raise
    except Exception as e:
        logger.error(f"Error obteniendo balance: {_sanitize_error(e)}")
        if own_exchange:
            await exchange.close()
        raise

    # Kraken Futures PF_ = multi-collateral USD-margined. El colateral puede
    # ser USD/USDT/USDC (con haircut). Se prefiere el wallet USD (moneda de
    # settle); fallback a USDT/USDC. OBJETIVO PAPER (Etapa 4): confirmar contra
    # demo qué moneda/estructura devuelve ccxt fetch_balance (free/total) — la
    # cuenta demo se fondea en USD y el sizing usa 'free' como capital operable.
    wallet, currency = {}, "USD"
    for ccy in ("USD", "USDT", "USDC"):
        w = bal.get(ccy) or {}
        if isinstance(w, dict) and (float(w.get("total", 0) or 0) > 0):
            wallet, currency = w, ccy
            break
    result = {
        "total": float(wallet.get("total", 0) or 0),
        "free": float(wallet.get("free", 0) or 0),
        "used": float(wallet.get("used", 0) or 0),
        "currency": currency,
    }

    # Observabilidad multi-collateral (OBJETIVO PAPER Etapa 4, UNCONFIRMED): si ccxt
    # anida el balance bajo otra estructura/clave en Kraken demo, los wallets
    # USD/USDT/USDC saldrían a 0 y el sizing no abriría NADA en silencio. No cambia
    # lógica (sigue devolviendo 0); solo vuelca las monedas presentes para diagnóstico
    # rápido en el primer ciclo de paper.
    if result["total"] == 0 and result["free"] == 0:
        _ccys = [
            k for k in bal.keys()
            if k not in ("info", "free", "used", "total", "timestamp", "datetime")
        ]
        logger.warning(
            "[BALANCE] colateral USD/USDT/USDC = 0. ¿Estructura multi-collateral "
            f"distinta en Kraken? Monedas con entrada en fetch_balance: {_ccys}"
        )

    if own_exchange:
        await exchange.close()

    logger.info(
        f"Balance {result['currency']} — total: {result['total']:.2f}, "
        f"libre: {result['free']:.2f}"
    )
    return result


# ---------------------------------------------------------------------------
# 5. Funding rate
# ---------------------------------------------------------------------------

async def get_funding_rate(
    symbol: str,
    exchange: ccxt_async.krakenfutures | None = None,
) -> dict:
    """
    Consulta el funding rate actual de un símbolo.

    Returns:
        {'symbol': symbol, 'rate': 0.0001, 'next_funding_time': datetime|None,
         'interval': '1h'}

    Kraken Futures PF_ multi-collateral: funding HORARIO (cap ±0.5%/h,
    fundingRateCoefficient=8), acumulación continua — NO el 8h de BingX.
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    kraken_sym = to_kraken_symbol(symbol)
    result = {
        "symbol": symbol, "rate": 0.0, "next_funding_time": None, "interval": "1h",
    }

    try:
        fr = await exchange.fetch_funding_rate(kraken_sym)
        result["rate"] = float(fr.get("fundingRate", 0) or 0)
        next_ts = fr.get("fundingTimestamp") or fr.get("nextFundingTimestamp")
        if next_ts:
            result["next_funding_time"] = pd.Timestamp(next_ts, unit="ms", tz="UTC")
    except Exception as e:
        logger.warning(f"get_funding_rate {symbol}: {_sanitize_error(e)}")

    if own_exchange:
        await exchange.close()

    return result


async def get_funding_history(
    symbol: str,
    since: int | None = None,
    limit: int = 10,
    exchange: ccxt_async.krakenfutures | None = None,
) -> list[dict]:
    """
    Consulta el historial de funding cobrado/pagado por una posición.

    Args:
        symbol: formato master.py ('BTC/USDT')
        since: timestamp ms desde el cual buscar (None = últimos N)
        limit: número de registros a obtener

    Returns:
        [{'timestamp': datetime, 'symbol': symbol, 'amount': -0.05,
          'rate': 0.0001, 'position_size': 500.0}, ...]
        Lista vacía si el exchange no soporta el endpoint.
    """
    own_exchange = exchange is None
    if own_exchange:
        exchange = _create_kraken_exchange()

    kraken_sym = to_kraken_symbol(symbol)
    results = []

    try:
        # ccxt unified: fetchFundingHistory (income type = FUNDING_FEE)
        raw = await exchange.fetch_funding_history(kraken_sym, since=since, limit=limit)
        for entry in raw:
            results.append({
                "timestamp": pd.Timestamp(entry.get("timestamp", 0), unit="ms", tz="UTC"),
                "symbol": symbol,
                "amount": float(entry.get("amount", 0) or 0),
                "rate": float(entry.get("info", {}).get("fundingRate", 0) or 0),
            })
    except (AttributeError, ccxt_sync.NotSupported):
        # Exchange no soporta funding history — caller debe estimar
        logger.debug(f"get_funding_history {symbol}: no soportado por exchange")
    except Exception as e:
        logger.warning(f"get_funding_history {symbol}: {_sanitize_error(e)}")

    if own_exchange:
        await exchange.close()

    return results


# ---------------------------------------------------------------------------
# 6. cross_exchange_fidelity_test
# ---------------------------------------------------------------------------
async def cross_exchange_fidelity_test(
    symbols: list | None = None,
    n_bars: int = 1000,
) -> pd.DataFrame:
    """
    Descarga n_bars de Binance (spot) y Kraken Futures para cada símbolo y
    compara close prices bar a bar. Mide la brecha de fidelidad sim(Binance)
    vs venue de ejecución (Kraken) — la motivación de la migración.

    Returns:
        DataFrame: symbol, mean_diff_pct, max_diff_pct, median_diff_pct,
                   n_bars_compared, n_missing_kraken, n_missing_binance
    """
    symbols = symbols or MASTER_SYMBOLS
    logger.info(f"Fidelity test: {len(symbols)} símbolos, {n_bars} barras cada uno")

    # Crear exchanges (solo datos públicos — sin API keys)
    kraken = ccxt_async.krakenfutures({
        "enableRateLimit": True,
        "timeout": REQUEST_TIMEOUT,
        "session": _create_aiohttp_session(),
    })
    binance = ccxt_async.binance({
        "enableRateLimit": True,
        "timeout": REQUEST_TIMEOUT,
        "session": _create_aiohttp_session(),
    })

    # Pre-cargar mercados una sola vez (evita race condition de load_markets paralelos)
    print("  Cargando mercados Kraken Futures...")
    try:
        await kraken.load_markets()
        print(f"    Kraken: {len(kraken.markets)} mercados")
    except Exception as e:
        logger.error(f"  Kraken load_markets falló: {_sanitize_error(e)}")
        await kraken.close()
        await binance.close()
        return pd.DataFrame()

    print("  Cargando mercados Binance (spot)...")
    try:
        await binance.load_markets()
        print(f"    Binance: {len(binance.markets)} mercados")
    except Exception as e:
        logger.error(f"  Binance load_markets falló: {_sanitize_error(e)}")
        await kraken.close()
        await binance.close()
        return pd.DataFrame()

    async def _fetch_pair(sym: str) -> dict:
        kraken_sym = to_kraken_symbol(sym)
        binance_sym = sym  # Binance spot usa 'BTC/USDT' directamente

        kraken_data, binance_data = None, None

        # Kraken Futures
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                kraken_data = await kraken.fetch_ohlcv(kraken_sym, TIMEFRAME, limit=n_bars)
                break
            except Exception as e:
                logger.warning(f"Fidelity Kraken {sym}: retry {attempt}/{MAX_RETRIES}: {_sanitize_error(e)}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)

        # Binance
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                binance_data = await binance.fetch_ohlcv(binance_sym, TIMEFRAME, limit=n_bars)
                break
            except Exception as e:
                logger.warning(f"Fidelity Binance {sym}: retry {attempt}/{MAX_RETRIES}: {_sanitize_error(e)}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)

        if kraken_data is None or binance_data is None:
            return {
                "symbol": sym,
                "mean_diff_pct": None,
                "max_diff_pct": None,
                "median_diff_pct": None,
                "n_bars_compared": 0,
                "n_missing_kraken": n_bars if kraken_data is None else 0,
                "n_missing_binance": n_bars if binance_data is None else 0,
            }

        # Convertir a DataFrames y alinear por timestamp
        df_kraken = pd.DataFrame(kraken_data, columns=["ts", "o", "h", "l", "c", "v"]).set_index("ts")
        df_binance = pd.DataFrame(binance_data, columns=["ts", "o", "h", "l", "c", "v"]).set_index("ts")

        merged = df_kraken[["c"]].join(df_binance[["c"]], lsuffix="_kraken", rsuffix="_binance", how="outer")
        n_missing_kraken = int(merged["c_kraken"].isna().sum())
        n_missing_binance = int(merged["c_binance"].isna().sum())

        both = merged.dropna()
        if len(both) == 0:
            return {
                "symbol": sym, "mean_diff_pct": None, "max_diff_pct": None,
                "median_diff_pct": None, "n_bars_compared": 0,
                "n_missing_kraken": n_missing_kraken, "n_missing_binance": n_missing_binance,
            }

        diff_pct = ((both["c_kraken"] - both["c_binance"]).abs() / both["c_binance"] * 100)

        return {
            "symbol": sym,
            "mean_diff_pct": round(diff_pct.mean(), 6),
            "max_diff_pct": round(diff_pct.max(), 6),
            "median_diff_pct": round(diff_pct.median(), 6),
            "n_bars_compared": len(both),
            "n_missing_kraken": n_missing_kraken,
            "n_missing_binance": n_missing_binance,
        }

    # Ejecutar en paralelo (con semáforo para no saturar el rate limit)
    sem = asyncio.Semaphore(10)

    async def _guarded(sym):
        async with sem:
            return await _fetch_pair(sym)

    t0 = time.perf_counter()
    results = await asyncio.gather(*[_guarded(s) for s in symbols])
    elapsed = time.perf_counter() - t0

    # Cerrar exchanges y sus sesiones aiohttp
    kraken_session = kraken.session
    binance_session = binance.session
    await kraken.close()
    await binance.close()
    if kraken_session and not kraken_session.closed:
        await kraken_session.close()
    if binance_session and not binance_session.closed:
        await binance_session.close()

    df = pd.DataFrame(results)
    logger.info(f"Fidelity test completado en {elapsed:.1f}s")

    # Alertas
    major = {"BTC/USDT", "ETH/USDT"}
    for _, row in df.iterrows():
        if row["mean_diff_pct"] is None:
            logger.warning(f"  {row['symbol']}: SIN DATOS para comparar")
            continue

        threshold = 0.05 if row["symbol"] in major else 0.20
        if row["mean_diff_pct"] > threshold:
            logger.warning(
                f"  {row['symbol']}: mean_diff={row['mean_diff_pct']:.4f}% "
                f"(threshold={threshold}%)"
            )

        total_bars = row["n_bars_compared"] + row["n_missing_kraken"] + row["n_missing_binance"]
        if total_bars > 0:
            missing_pct = (row["n_missing_kraken"] + row["n_missing_binance"]) / total_bars * 100
            if missing_pct > 1.0:
                logger.warning(
                    f"  {row['symbol']}: {missing_pct:.1f}% barras faltantes "
                    f"(kraken={row['n_missing_kraken']}, binance={row['n_missing_binance']})"
                )

    return df


# ---------------------------------------------------------------------------
# CLI / Tests
# ---------------------------------------------------------------------------
async def _run_quick_test():
    print("=" * 60)
    print("DATA FEED — Test rápido")
    print("=" * 60)

    # 1. Descargar OHLCV
    exchange = _create_kraken_exchange()

    print(f"\n[1] Descargando {len(MASTER_SYMBOLS)} símbolos ({OHLCV_LIMIT} velas 1h)...")
    data = await download_all_ohlcv(exchange=exchange)
    ok = sum(1 for v in data.values() if v is not None)
    fail = len(data) - ok
    print(f"    OK: {ok}, fallidos: {fail}")

    # Muestra una sample
    for sym, df in data.items():
        if df is not None:
            print(f"    Sample {sym}: {len(df)} barras, "
                  f"última={df['timestamp'].iloc[-1]}, close={df['close'].iloc[-1]}")
            break

    # 2. Balance
    print("\n[2] Consultando balance...")
    try:
        bal = await get_balance(exchange=exchange)
        print(f"    Total: {bal['total']:.2f} USDT, Libre: {bal['free']:.2f} USDT")
    except Exception as e:
        print(f"    Error: {e}")

    # 3. Posiciones
    print("\n[3] Consultando posiciones abiertas...")
    try:
        positions = await get_open_positions(exchange=exchange)
        if positions:
            for sym, pos in positions.items():
                print(f"    {sym}: {pos['side']} x{pos['size']} @ {pos['entry_price']:.2f} "
                      f"(PnL: {pos['unrealized_pnl']:.2f})")
        else:
            print("    Sin posiciones abiertas")
    except Exception as e:
        print(f"    Error: {e}")

    await exchange.close()
    print("\nTest completado.")


async def _run_fidelity_test():
    print("=" * 60)
    print("DATA FEED — Test de fidelidad cross-exchange")
    print("=" * 60)

    df = await cross_exchange_fidelity_test()
    if df.empty:
        print("\n  Sin resultados — ambos exchanges fallaron.")
        return

    print(f"\nResultados ({len(df)} simbolos):\n")
    with pd.option_context("display.max_rows", None, "display.float_format", "{:.6f}".format):
        print(df.to_string(index=False))

    # Resumen
    valid = df.dropna(subset=["mean_diff_pct"])
    if len(valid) > 0:
        print(f"\nResumen global:")
        print(f"  Mean diff promedio: {valid['mean_diff_pct'].mean():.6f}%")
        print(f"  Max diff máximo:    {valid['max_diff_pct'].max():.6f}%")
        print(f"  Símbolos sin datos: {len(df) - len(valid)}")


def main():
    parser = argparse.ArgumentParser(description="Data Feed — Kraken Futures OHLCV + Account")
    parser.add_argument("--fidelity-test", action="store_true",
                        help="Ejecutar test de fidelidad cross-exchange (Binance vs Kraken)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.fidelity_test:
        asyncio.run(_run_fidelity_test())
    else:
        asyncio.run(_run_quick_test())


if __name__ == "__main__":
    main()
