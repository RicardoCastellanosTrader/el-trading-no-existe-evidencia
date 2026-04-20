"""
portfolio_manager.py — Gestión de cartera, sizing y control de riesgo.

Recibe señales de brain_engine y estado del portfolio, decide CUÁNTO asignar
a cada operación. Controla correlación inter-símbolo, límites de exposición,
soft blending en transiciones, y position sizing global.
No ejecuta órdenes — solo devuelve sizing.
"""

import json
import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("live.portfolio_manager")

# ---------------------------------------------------------------------------
# PortfolioConfig
# ---------------------------------------------------------------------------

@dataclass
class PortfolioConfig:
    # Capital y riesgo
    max_portfolio_risk_pct: float = 25.0       # máximo DD aceptable del portfolio total
    max_single_position_pct: float = 5.0       # máximo % del capital en una posición
    max_correlated_block_pct: float = 20.0     # máximo % del capital en un bloque correlado

    # Correlación
    correlation_lookback: int = 168            # 168 barras = 1 semana de 1h para rolling corr
    correlation_threshold: float = 0.7          # por encima = mismo bloque

    # Soft blending
    blending_enabled: bool = True
    min_confidence_to_trade: float = 0.60      # P(cluster) mínima para operar
    full_confidence_threshold: float = 0.85    # P(cluster) al 100%

    # Sectores
    sector_map: dict = None   # {'BTC/USDT': 'L1_major', ...}
    max_sector_exposure_pct: float = 30.0      # máximo % por sector

    # Leverage por símbolo
    leverage_map: dict = None  # {'BTC/USDT': 5, ...} calculado post-JSONs


def load_portfolio_config(
    specialist_configs_dir: str | None = None,
    target_max_dd: float = 25.0,
) -> PortfolioConfig:
    """Carga config con sector_map y leverage_map pre-calculados."""
    sector_map = get_sector_map()
    leverage_map = {}
    if specialist_configs_dir and os.path.isdir(specialist_configs_dir):
        leverage_map = compute_leverage_map(specialist_configs_dir, target_max_dd)

    return PortfolioConfig(
        sector_map=sector_map,
        leverage_map=leverage_map,
    )


# ---------------------------------------------------------------------------
# 1. compute_correlation_matrix
# ---------------------------------------------------------------------------

def compute_correlation_matrix(
    market_data: dict,
    lookback: int = 168,
    ewma_halflife: int = 24,
) -> pd.DataFrame:
    """
    Correlacion EWMA de log-returns 1h entre simbolos relevantes.

    Usa EWMA con halflife=24h para que shocks recientes dominen el calculo.
    Las ultimas 24 barras pesan el 50% de la correlacion.

    Args:
        market_data: {symbol: DataFrame(OHLCV)} de data_feed.
        lookback: barras de historia a usar.
        ewma_halflife: halflife en barras para EWMA (default 24 = 1 dia).

    Returns:
        DataFrame NxN con correlaciones EWMA.
    """
    returns = {}
    for sym, df in market_data.items():
        if df is None or len(df) < 2:
            continue
        close = df["close"].values.astype(float)
        # log-returns, usar las ultimas `lookback` barras
        lr = np.diff(np.log(close))
        lr = lr[-lookback:] if len(lr) > lookback else lr
        if len(lr) >= 20:  # minimo razonable para correlacion
            returns[sym] = lr

    if not returns:
        return pd.DataFrame()

    # Alinear longitudes (usar el minimo comun)
    min_len = min(len(v) for v in returns.values())
    df_ret = pd.DataFrame({sym: arr[-min_len:] for sym, arr in returns.items()})

    # EWMA correlation: tomar la ultima fila (correlacion mas reciente)
    ewm_corr = df_ret.ewm(halflife=ewma_halflife).corr()
    return ewm_corr.loc[df_ret.index[-1]]


# ---------------------------------------------------------------------------
# 1b. compute_volatility_weights
# ---------------------------------------------------------------------------

def compute_volatility_weights(
    market_data: dict,
    atr_period: int = 14,
    lookback: int = 100,
    clamp_lo: float = 0.3,
    clamp_hi: float = 2.0,
) -> dict[str, float]:
    """
    Peso inversamente proporcional a la volatilidad (ATR normalizado).

    ATR_pct = ATR(14) / close * 100  (ATR como % del precio)
    weight = median_ATR_pct / ATR_pct  (normalizado a la mediana)

    Simbolo con volatilidad mediana tiene weight=1.0,
    mas volatiles weight<1.0, menos volatiles weight>1.0.
    Clamped a [clamp_lo, clamp_hi].
    """
    atr_pcts = {}
    for sym, df in market_data.items():
        if df is None or len(df) < atr_period + 2:
            continue
        # Usar las ultimas `lookback` barras
        d = df.iloc[-lookback:] if len(df) > lookback else df
        high = d["high"].values.astype(float)
        low = d["low"].values.astype(float)
        close = d["close"].values.astype(float)

        # True Range
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]
        tr = np.maximum(
            high - low,
            np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
        )

        # ATR = SMA de TR sobre las ultimas atr_period barras
        if len(tr) < atr_period:
            continue
        atr = np.mean(tr[-atr_period:])
        last_close = close[-1]
        if last_close > 0:
            atr_pcts[sym] = (atr / last_close) * 100.0

    if not atr_pcts:
        return {}

    # Mediana para normalizar
    median_atr = float(np.median(list(atr_pcts.values())))
    if median_atr <= 0:
        return {}

    weights = {}
    for sym, atr_pct in atr_pcts.items():
        if atr_pct <= 0:
            weights[sym] = 1.0
            continue
        raw_w = median_atr / atr_pct
        weights[sym] = max(clamp_lo, min(clamp_hi, raw_w))

    return weights


# ---------------------------------------------------------------------------
# 2. identify_correlated_blocks
# ---------------------------------------------------------------------------

def identify_correlated_blocks(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.7,
) -> list[set]:
    """
    Agrupa símbolos correlados en bloques (union-find transitivo).

    Returns:
        [{'BTC/USDT', 'ETH/USDT', 'SOL/USDT'}, {'DOGE/USDT', 'SHIB/USDT'}, ...]
    """
    if corr_matrix.empty:
        return []

    symbols = list(corr_matrix.columns)
    n = len(symbols)

    # Union-Find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            # v2.3.7 (fix S2 portfolio): correlacion solo positiva. abs()
            # agrupaba anticorrelacionados como concentracion de riesgo,
            # cuando en realidad son diversificacion.
            if corr_matrix.iloc[i, j] > threshold:
                union(i, j)

    # Agrupar
    blocks_map: dict[int, set] = {}
    for i in range(n):
        root = find(i)
        blocks_map.setdefault(root, set()).add(symbols[i])

    return list(blocks_map.values())


# ---------------------------------------------------------------------------
# 3. compute_soft_blending
# ---------------------------------------------------------------------------

def compute_soft_blending(
    regime_info: dict,
    config: PortfolioConfig,
) -> dict[str, float]:
    """
    Multiplicador de sizing basado en confianza del GMM.

    Returns:
        {symbol: float 0.0-1.0}
    """
    result = {}
    lo = config.min_confidence_to_trade
    hi = config.full_confidence_threshold

    for sym, info in regime_info.items():
        # Cluster no operable -> 0
        if not info.get("operable", False):
            result[sym] = 0.0
            continue

        conf = info.get("confidence", 0.0)
        if conf < lo:
            result[sym] = 0.0
        elif conf >= hi:
            result[sym] = 1.0
        else:
            # Interpolación lineal de 0 a 1 entre [lo, hi)
            result[sym] = (conf - lo) / (hi - lo)

    return result


# ---------------------------------------------------------------------------
# 4. allocate_positions  (función principal)
# ---------------------------------------------------------------------------

def allocate_positions(
    signals: dict,
    balance: dict,
    positions: dict,
    regime_info: dict,
    market_data: dict,
    config: PortfolioConfig,
    dd_multiplier: float = 1.0,
) -> dict:
    """
    Recibe señales puras y decide sizing para cada símbolo.

    Returns:
        {symbol: {action, size_usdt, size_contracts, leverage, sl_price,
                  blending_factor, block_reduction, reason}}
    """
    free_capital = balance.get("free", 0.0)
    total_capital = balance.get("total", 0.0)
    if total_capital <= 0:
        logger.warning("[PORTFOLIO] Balance total <= 0, no se puede asignar")
        return {}

    leverage_map = config.leverage_map or {}
    sector_map = config.sector_map or {}
    allocations = {}

    # ------------------------------------------------------------------
    # Paso 1: Filtrar señales operables
    # ------------------------------------------------------------------
    entry_signals = {}   # señales de entrada (LONG/SHORT)
    close_signals = {}   # señales de cierre (CLOSE_LONG/CLOSE_SHORT)

    for sym, sig in signals.items():
        action = sig.get("action", "HOLD")

        if action in ("CLOSE_LONG", "CLOSE_SHORT"):
            # Cierres siempre pasan
            close_signals[sym] = sig
            continue

        if action in ("HOLD", "FLAT"):
            alloc = {"action": action, "reason": sig.get("reason", action.lower())}
            if action == "HOLD" and sig.get("sl_price", 0.0) > 0:
                alloc["sl_price"] = sig["sl_price"]
            allocations[sym] = alloc
            continue

        if not sig.get("operable", False):
            allocations[sym] = {"action": "FLAT", "reason": "not_operable"}
            continue

        # LONG o SHORT
        entry_signals[sym] = sig

    # Procesar cierres directamente (sin sizing)
    for sym, sig in close_signals.items():
        allocations[sym] = {
            "action": sig["action"],
            "size_usdt": 0.0,
            "size_contracts": 0.0,
            "leverage": leverage_map.get(sym, 1),
            "sl_price": 0.0,
            "blending_factor": 1.0,
            "block_reduction": 1.0,
            "reason": sig.get("reason", "close_signal"),
        }

    # DD circuit breaker: bloquear entradas si multiplier = 0.0
    if dd_multiplier <= 0.0:
        for sym in list(entry_signals.keys()):
            allocations[sym] = {"action": "FLAT", "reason": "circuit_breaker_paused"}
        entry_signals.clear()

    n_entry = len(entry_signals)
    n_close = len(close_signals)
    if dd_multiplier < 1.0:
        logger.info(
            f"[PORTFOLIO] {n_entry} senales de entrada, {n_close} de cierre "
            f"(dd_multiplier={dd_multiplier})"
        )
    else:
        logger.info(f"[PORTFOLIO] {n_entry} senales de entrada, {n_close} de cierre")

    if not entry_signals:
        return allocations

    # ------------------------------------------------------------------
    # Paso 2: Soft blending
    # ------------------------------------------------------------------
    blending = compute_soft_blending(regime_info, config) if config.blending_enabled else {}
    blending_log_parts = []

    for sym in list(entry_signals.keys()):
        bf = blending.get(sym, 1.0)
        if bf <= 0.0:
            allocations[sym] = {"action": "FLAT", "reason": "low_confidence"}
            del entry_signals[sym]
            blending_log_parts.append(f"{sym.split('/')[0]} 0%")
        else:
            blending_log_parts.append(f"{sym.split('/')[0]} {bf*100:.0f}%")

    if blending_log_parts:
        logger.info(f"[PORTFOLIO] Soft blending: {', '.join(blending_log_parts)}")

    if not entry_signals:
        return allocations

    # ------------------------------------------------------------------
    # Paso 3: Volatility targeting + Sizing base
    # ------------------------------------------------------------------
    vol_weights = compute_volatility_weights(market_data)
    vol_log_parts = []
    for sym in entry_signals:
        vw = vol_weights.get(sym, 1.0)
        if vw < 0.7 or vw > 1.3:
            tag = "low vol" if vw > 1.0 else "high vol"
            vol_log_parts.append(f"{sym.split('/')[0]} w={vw:.2f} ({tag})")
    if vol_log_parts:
        logger.info(f"[PORTFOLIO] Vol targeting: {', '.join(vol_log_parts)}")

    sizing = {}  # sym -> size_usdt (antes de reducciones por bloque/sector/global)
    effective_max_pos_pct = config.max_single_position_pct * dd_multiplier
    for sym, sig in entry_signals.items():
        lev = leverage_map.get(sym, 1)
        bf = blending.get(sym, 1.0)
        vw = vol_weights.get(sym, 1.0)
        base_size = free_capital * effective_max_pos_pct / 100.0
        adjusted = base_size * bf * vw
        # Cap: vol_weight puede empujar por encima del max_single_position_pct
        max_allowed = free_capital * config.max_single_position_pct / 100.0
        adjusted = min(adjusted, max_allowed)
        sizing[sym] = {
            "base_usdt": adjusted,
            "leverage": lev,
            "position_value": adjusted * lev,
            "blending_factor": bf,
            "vol_weight": vw,
            "sl_price": sig.get("sl_price", 0.0),
            "entry_price": sig.get("entry_price", 0.0),
            "action": sig["action"],
            "reason": sig.get("reason", ""),
        }

    # ------------------------------------------------------------------
    # Paso 4: Correlación y bloques
    # ------------------------------------------------------------------
    entry_syms = list(sizing.keys())
    # Solo calcular correlación con datos de los símbolos relevantes
    relevant_data = {s: market_data[s] for s in entry_syms if s in market_data}
    corr_matrix = compute_correlation_matrix(relevant_data, config.correlation_lookback)
    blocks = identify_correlated_blocks(corr_matrix, config.correlation_threshold)

    block_reductions = {sym: 1.0 for sym in entry_syms}

    for block in blocks:
        if len(block) < 2:
            continue
        block_syms = [s for s in block if s in sizing]
        if not block_syms:
            continue

        # Calcular exposición total del bloque como % del total_capital
        block_exposure_pct = sum(
            sizing[s]["base_usdt"] / total_capital * 100.0 for s in block_syms
        )
        limit = config.max_correlated_block_pct
        if block_exposure_pct > limit:
            reduction = limit / block_exposure_pct
            for s in block_syms:
                block_reductions[s] = reduction
                sizing[s]["base_usdt"] *= reduction
                sizing[s]["position_value"] = sizing[s]["base_usdt"] * sizing[s]["leverage"]

        # Log de bloques con correlación media
        block_names = [s.split("/")[0] for s in block_syms]
        # Calcular correlación media del bloque
        avg_corr = 0.0
        n_pairs = 0
        for i, s1 in enumerate(block_syms):
            for s2 in block_syms[i + 1:]:
                if s1 in corr_matrix.columns and s2 in corr_matrix.columns:
                    avg_corr += abs(corr_matrix.loc[s1, s2])
                    n_pairs += 1
        avg_corr = avg_corr / n_pairs if n_pairs > 0 else 0.0

        logger.info(
            f"[PORTFOLIO] Bloque {{{','.join(block_names)}}}: "
            f"{block_exposure_pct:.1f}% -> "
            f"{'OK' if block_exposure_pct <= limit else f'reducido a {limit:.0f}%'} "
            f"(r={avg_corr:.2f}, límite {limit:.0f}%)"
        )

    # ------------------------------------------------------------------
    # Paso 5: Límites por sector
    # ------------------------------------------------------------------
    if sector_map:
        # Calcular exposición existente por sector
        existing_sector_exp: dict[str, float] = {}
        for sym, pos in positions.items():
            if pos.get("side", "") in ("long", "short"):
                sec = sector_map.get(sym, "Unknown")
                pos_value = pos.get("size", 0.0) * pos.get("entry_price", 0.0)
                pct = pos_value / total_capital * 100.0 if total_capital > 0 else 0.0
                existing_sector_exp[sec] = existing_sector_exp.get(sec, 0.0) + pct

        # Calcular nuevas por sector
        new_sector_exp: dict[str, list[str]] = {}
        for sym in sizing:
            sec = sector_map.get(sym, "Unknown")
            new_sector_exp.setdefault(sec, []).append(sym)

        for sec, syms in new_sector_exp.items():
            existing = existing_sector_exp.get(sec, 0.0)
            new_total = sum(sizing[s]["base_usdt"] / total_capital * 100.0 for s in syms)
            combined = existing + new_total
            limit = config.max_sector_exposure_pct

            logger.info(
                f"[PORTFOLIO] Sector {sec}: {combined:.1f}% exposición "
                f"(límite {limit:.0f}%) "
                f"{'OK' if combined <= limit else 'WARN recortando'}"
            )

            if combined > limit and new_total > 0:
                # Solo recortar las nuevas, proporcional
                allowed_new = max(0.0, limit - existing)
                reduction = allowed_new / new_total if new_total > 0 else 0.0
                for s in syms:
                    sizing[s]["base_usdt"] *= reduction
                    sizing[s]["position_value"] = sizing[s]["base_usdt"] * sizing[s]["leverage"]
                    block_reductions[s] *= reduction

    # ------------------------------------------------------------------
    # Paso 6: Límite global
    # ------------------------------------------------------------------
    # Exposición existente
    existing_exposure_pct = 0.0
    for sym, pos in positions.items():
        if pos.get("side", "") in ("long", "short"):
            pos_value = pos.get("size", 0.0) * pos.get("entry_price", 0.0)
            existing_exposure_pct += pos_value / total_capital * 100.0 if total_capital > 0 else 0.0

    new_total_pct = sum(sizing[s]["base_usdt"] / total_capital * 100.0 for s in sizing)
    combined_pct = existing_exposure_pct + new_total_pct

    if combined_pct > config.max_portfolio_risk_pct and new_total_pct > 0:
        allowed = max(0.0, config.max_portfolio_risk_pct - existing_exposure_pct)
        global_reduction = allowed / new_total_pct if new_total_pct > 0 else 0.0
        logger.info(
            f"[PORTFOLIO] Exposición global {combined_pct:.1f}% > "
            f"{config.max_portfolio_risk_pct:.0f}% -> reducción global {global_reduction:.2f}"
        )
        for s in sizing:
            sizing[s]["base_usdt"] *= global_reduction
            sizing[s]["position_value"] = sizing[s]["base_usdt"] * sizing[s]["leverage"]
            block_reductions[s] *= global_reduction

    # No exceder capital disponible total
    total_new_usdt = sum(sizing[s]["base_usdt"] for s in sizing)
    if total_new_usdt > free_capital and total_new_usdt > 0:
        cap_reduction = free_capital / total_new_usdt
        for s in sizing:
            sizing[s]["base_usdt"] *= cap_reduction
            sizing[s]["position_value"] = sizing[s]["base_usdt"] * sizing[s]["leverage"]

    # ------------------------------------------------------------------
    # Paso 7: Redondeo y mínimos del exchange
    # ------------------------------------------------------------------
    # Mínimos típicos de BingX (en USDT notional)
    MIN_ORDER_USDT = 5.0  # mínimo práctico para la mayoría de pares

    alloc_log_parts = []
    for sym, info in sizing.items():
        size_usdt = info["base_usdt"]

        if size_usdt < MIN_ORDER_USDT:
            allocations[sym] = {"action": "FLAT", "reason": "below_min_order"}
            continue

        # Calcular tamaño en contratos
        price = info["entry_price"]
        size_contracts = size_usdt / price if price > 0 else 0.0

        # Redondeo a precisión razonable
        if price >= 10000:
            size_contracts = round(size_contracts, 5)  # BTC
        elif price >= 100:
            size_contracts = round(size_contracts, 4)  # ETH, SOL
        else:
            size_contracts = round(size_contracts, 2)  # altcoins

        allocations[sym] = {
            "action": info["action"],
            "size_usdt": round(size_usdt, 2),
            "size_contracts": size_contracts,
            "leverage": info["leverage"],
            "sl_price": info["sl_price"],
            "blending_factor": info["blending_factor"],
            "vol_weight": round(info.get("vol_weight", 1.0), 4),
            "block_reduction": round(block_reductions.get(sym, 1.0), 4),
            "reason": info["reason"],
        }

        side_str = "long" if info["action"] == "LONG" else "short"
        alloc_log_parts.append(
            f"{sym.split('/')[0]} {size_usdt:.0f} USDT {side_str} {info['leverage']}x"
        )

    if alloc_log_parts:
        logger.info(f"[PORTFOLIO] Allocations: {', '.join(alloc_log_parts)}")

    return allocations


# ---------------------------------------------------------------------------
# 5. compute_leverage_map
# ---------------------------------------------------------------------------

def compute_leverage_map(
    specialist_configs_dir: str,
    target_max_dd: float = 25.0,
) -> dict[str, int]:
    """
    Calcula leverage por símbolo basado en maxDD del top-1 specialist.

    leverage = target_max_dd / maxdd_worst (del top-1 config del mejor cluster operable)
    Capped: min 1x, max 10x.
    """
    leverage_map = {}
    configs_path = Path(specialist_configs_dir)

    for json_file in configs_path.glob("*_specialist_configs.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"[PORTFOLIO] Error leyendo {json_file.name}: {e}")
            continue

        symbol = data.get("symbol")
        if not symbol:
            continue

        # Buscar el mejor cluster operable (top-1 con sqn_p5 > 0)
        best_maxdd = None
        clusters = data.get("clusters", {})

        for cluster_id, cluster_data in clusters.items():
            top_configs = cluster_data.get("top_configs", [])
            if not top_configs:
                continue
            top1 = top_configs[0]
            if top1.get("sqn_p5", 0.0) <= 0:
                continue
            maxdd = top1.get("maxdd_worst", 0.0)
            if maxdd > 0:
                # Tomar el que tenga mayor specialist_score entre los operables
                if best_maxdd is None:
                    best_maxdd = maxdd
                else:
                    # Prefiero el cluster con mejor score
                    best_maxdd = maxdd  # simplificación: último operable gana

        if best_maxdd and best_maxdd > 0:
            raw_lev = target_max_dd / (best_maxdd * 100.0)  # maxdd_worst está en fracción
            lev = max(1, min(10, int(raw_lev)))
            leverage_map[symbol] = lev
        else:
            # MR-only symbols (no TF operable cluster) default to 1x
            for cluster_id, cluster_data in clusters.items():
                mr = cluster_data.get("mean_reversion")
                if mr and mr.get("strategy_type") == "mean_reversion" and mr.get("config_id", 0) > 0:
                    leverage_map[symbol] = 1
                    break

    logger.info(
        f"[PORTFOLIO] Leverage map: {len(leverage_map)} símbolos calculados"
    )
    return leverage_map


# ---------------------------------------------------------------------------
# 6. get_sector_map
# ---------------------------------------------------------------------------

def get_sector_map() -> dict[str, str]:
    """Clasificación manual de los 48 símbolos por sector."""
    return {
        # L1 major
        "BTC/USDT": "L1_major",
        "ETH/USDT": "L1_major",
        "BNB/USDT": "L1_major",

        # L1 alt
        "SOL/USDT": "L1_alt",
        "AVAX/USDT": "L1_alt",
        "NEAR/USDT": "L1_alt",
        "SUI/USDT": "L1_alt",
        "APT/USDT": "L1_alt",
        "SEI/USDT": "L1_alt",
        "ICP/USDT": "L1_alt",
        "ADA/USDT": "L1_alt",
        "DOT/USDT": "L1_alt",
        "ATOM/USDT": "L1_alt",
        "ALGO/USDT": "L1_alt",
        "TRX/USDT": "L1_alt",
        "XRP/USDT": "L1_alt",
        "XLM/USDT": "L1_alt",
        "HBAR/USDT": "L1_alt",

        # Legacy / Forks
        "BCH/USDT": "Legacy",
        "LTC/USDT": "Legacy",
        "ETC/USDT": "Legacy",

        # DeFi
        "UNI/USDT": "DeFi",
        "AAVE/USDT": "DeFi",
        "ENA/USDT": "DeFi",
        "ONDO/USDT": "DeFi",

        # L2 / Scaling
        "ARB/USDT": "L2",
        "OP/USDT": "L2",
        "IMX/USDT": "L2",
        "POL/USDT": "L2",
        "STX/USDT": "L2",

        # Meme
        "DOGE/USDT": "Meme",
        "SHIB/USDT": "Meme",

        # Oracle / Infra
        "LINK/USDT": "Oracle",
        "GRT/USDT": "Infra",
        "FIL/USDT": "Infra",
        "RENDER/USDT": "Infra",
        "QNT/USDT": "Infra",
        "THETA/USDT": "Infra",
        "FET/USDT": "Infra",

        # Metaverse / Gaming
        "SAND/USDT": "Metaverse",
        "MANA/USDT": "Metaverse",

        # AI / Misc
        "TAO/USDT": "AI",
        "INJ/USDT": "DeFi",
        "WLD/USDT": "AI",
        "VET/USDT": "Infra",
    }


# ---------------------------------------------------------------------------
# __main__ — Tests
# ---------------------------------------------------------------------------

def _test_basic():
    """Test con datos de ejemplo estáticos."""
    print("=" * 60)
    print("PORTFOLIO MANAGER — Test básico")
    print("=" * 60)

    config = PortfolioConfig(
        sector_map=get_sector_map(),
        leverage_map={"BTC/USDT": 1, "ETH/USDT": 2, "SOL/USDT": 3, "DOGE/USDT": 1, "SHIB/USDT": 1},
    )

    # Mock balance
    balance = {"total": 10000.0, "free": 7500.0, "used": 2500.0, "currency": "USDT"}

    # Mock positions (una posición existente)
    positions = {
        "LINK/USDT": {
            "side": "long", "size": 10.0, "entry_price": 15.0,
            "unrealized_pnl": 5.0, "leverage": 2, "stop_order_id": None,
        }
    }

    # Mock regime_info
    regime_info = {
        "BTC/USDT": {"cluster": 1, "confidence": 0.82, "operable": True},
        "ETH/USDT": {"cluster": 1, "confidence": 0.90, "operable": True},
        "SOL/USDT": {"cluster": 2, "confidence": 0.75, "operable": True},
        "DOGE/USDT": {"cluster": 0, "confidence": 0.55, "operable": True},   # below min
        "SHIB/USDT": {"cluster": 0, "confidence": 0.70, "operable": True},
        "DOT/USDT": {"cluster": 1, "confidence": 0.80, "operable": False},   # not operable
    }

    # Mock signals
    signals = {
        "BTC/USDT": {"action": "LONG", "reason": "ma_cross", "entry_price": 65000.0,
                     "sl_price": 63469.14, "confidence": 0.82, "operable": True},
        "ETH/USDT": {"action": "LONG", "reason": "zone_entry", "entry_price": 3500.0,
                     "sl_price": 3395.0, "confidence": 0.90, "operable": True},
        "SOL/USDT": {"action": "LONG", "reason": "zone_entry", "entry_price": 180.0,
                     "sl_price": 174.6, "confidence": 0.75, "operable": True},
        "DOGE/USDT": {"action": "LONG", "reason": "zone_entry", "entry_price": 0.15,
                      "sl_price": 0.1455, "confidence": 0.55, "operable": True},
        "SHIB/USDT": {"action": "SHORT", "reason": "divergence", "entry_price": 0.000025,
                      "sl_price": 0.0000258, "confidence": 0.70, "operable": True},
        "DOT/USDT": {"action": "LONG", "reason": "zone_entry", "entry_price": 7.5,
                     "sl_price": 7.275, "confidence": 0.80, "operable": False},
        "LINK/USDT": {"action": "CLOSE_LONG", "reason": "sl_exit", "entry_price": 15.5,
                      "sl_price": 0.0, "confidence": 0.70, "operable": True},
    }

    # Mock market_data (con precios sintéticos para correlación)
    np.random.seed(42)
    n_bars = 200

    def _make_ohlcv(base_price, vol=0.02):
        closes = base_price * np.exp(np.cumsum(np.random.randn(n_bars) * vol))
        df = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
            "open": closes * 0.999,
            "high": closes * 1.005,
            "low": closes * 0.995,
            "close": closes,
            "volume": np.random.rand(n_bars) * 1e6,
        })
        return df

    # BTC y ETH correlados, SOL parcialmente, DOGE/SHIB correlados entre sí
    btc_returns = np.random.randn(n_bars) * 0.02
    market_data = {}
    market_data["BTC/USDT"] = _make_ohlcv(65000)
    # ETH correlado con BTC
    eth_close = 3500 * np.exp(np.cumsum(btc_returns * 0.8 + np.random.randn(n_bars) * 0.01))
    market_data["ETH/USDT"] = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
        "open": eth_close * 0.999, "high": eth_close * 1.005,
        "low": eth_close * 0.995, "close": eth_close,
        "volume": np.random.rand(n_bars) * 1e6,
    })
    market_data["SOL/USDT"] = _make_ohlcv(180)
    # DOGE y SHIB altamente correlados
    doge_ret = np.random.randn(n_bars) * 0.04
    doge_close = 0.15 * np.exp(np.cumsum(doge_ret))
    shib_close = 0.000025 * np.exp(np.cumsum(doge_ret * 0.9 + np.random.randn(n_bars) * 0.01))
    market_data["DOGE/USDT"] = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
        "open": doge_close * 0.999, "high": doge_close * 1.005,
        "low": doge_close * 0.995, "close": doge_close,
        "volume": np.random.rand(n_bars) * 1e6,
    })
    market_data["SHIB/USDT"] = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
        "open": shib_close * 0.999, "high": shib_close * 1.005,
        "low": shib_close * 0.995, "close": shib_close,
        "volume": np.random.rand(n_bars) * 1e6,
    })
    market_data["DOT/USDT"] = _make_ohlcv(7.5)

    print(f"\nBalance: {balance}")
    print(f"Posiciones existentes: {list(positions.keys())}")
    print(f"Señales: {list(signals.keys())}")
    print()

    result = allocate_positions(signals, balance, positions, regime_info, market_data, config)

    print("\n--- Allocations ---")
    for sym, alloc in sorted(result.items()):
        if alloc.get("size_usdt", 0) > 0:
            print(f"  {sym}: {alloc['action']} {alloc['size_usdt']:.2f} USDT "
                  f"({alloc['size_contracts']} contracts) "
                  f"lev={alloc['leverage']}x blend={alloc['blending_factor']:.2f} "
                  f"block_red={alloc['block_reduction']:.4f} [{alloc['reason']}]")
        else:
            print(f"  {sym}: {alloc['action']} [{alloc.get('reason', '')}]")

    print("\nTest básico completado.")


def _test_simulate():
    """Simula allocación con señales mock más extensas."""
    print("=" * 60)
    print("PORTFOLIO MANAGER — Simulación")
    print("=" * 60)

    config = PortfolioConfig(
        sector_map=get_sector_map(),
        leverage_map={
            "BTC/USDT": 1, "ETH/USDT": 2, "SOL/USDT": 3,
            "AVAX/USDT": 2, "NEAR/USDT": 3, "DOGE/USDT": 1,
            "SHIB/USDT": 1, "UNI/USDT": 2, "AAVE/USDT": 2,
            "LINK/USDT": 2, "ARB/USDT": 3, "OP/USDT": 3,
        },
    )

    balance = {"total": 50000.0, "free": 40000.0, "used": 10000.0, "currency": "USDT"}
    positions = {
        "BTC/USDT": {
            "side": "long", "size": 0.01, "entry_price": 64000.0,
            "unrealized_pnl": 200.0, "leverage": 1, "stop_order_id": None,
        },
    }

    # 12 señales de entrada + 3 cierres
    symbols_entry = [
        ("ETH/USDT", "LONG", 3500.0, 0.88),
        ("SOL/USDT", "LONG", 180.0, 0.76),
        ("AVAX/USDT", "LONG", 35.0, 0.92),
        ("NEAR/USDT", "LONG", 6.5, 0.65),
        ("DOGE/USDT", "SHORT", 0.15, 0.71),
        ("SHIB/USDT", "SHORT", 0.000025, 0.55),  # below threshold
        ("UNI/USDT", "LONG", 12.0, 0.83),
        ("AAVE/USDT", "LONG", 280.0, 0.90),
        ("LINK/USDT", "LONG", 18.0, 0.78),
        ("ARB/USDT", "LONG", 1.2, 0.62),
        ("OP/USDT", "LONG", 2.5, 0.88),
        ("SUI/USDT", "LONG", 1.8, 0.70),
    ]

    signals = {}
    regime_info = {}
    for sym, action, price, conf in symbols_entry:
        signals[sym] = {
            "action": action, "reason": "zone_entry", "entry_price": price,
            "sl_price": price * 0.97, "confidence": conf, "operable": True,
        }
        regime_info[sym] = {"cluster": 1, "confidence": conf, "operable": True}

    # Cierres
    for sym in ["BCH/USDT", "LTC/USDT", "XRP/USDT"]:
        signals[sym] = {
            "action": "CLOSE_LONG", "reason": "sl_exit", "entry_price": 100.0,
            "sl_price": 0.0, "confidence": 0.80, "operable": True,
        }
        regime_info[sym] = {"cluster": 1, "confidence": 0.80, "operable": True}

    # Market data sintético
    np.random.seed(123)
    n_bars = 200
    market_data = {}
    base_prices = {
        "ETH/USDT": 3500, "SOL/USDT": 180, "AVAX/USDT": 35, "NEAR/USDT": 6.5,
        "DOGE/USDT": 0.15, "SHIB/USDT": 0.000025, "UNI/USDT": 12, "AAVE/USDT": 280,
        "LINK/USDT": 18, "ARB/USDT": 1.2, "OP/USDT": 2.5, "SUI/USDT": 1.8,
    }
    for sym, bp in base_prices.items():
        closes = bp * np.exp(np.cumsum(np.random.randn(n_bars) * 0.02))
        market_data[sym] = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=n_bars, freq="1h"),
            "open": closes * 0.999, "high": closes * 1.005,
            "low": closes * 0.995, "close": closes,
            "volume": np.random.rand(n_bars) * 1e6,
        })

    result = allocate_positions(signals, balance, positions, regime_info, market_data, config)

    print("\n--- Allocations ---")
    entries = 0
    total_usdt = 0.0
    for sym, alloc in sorted(result.items()):
        action = alloc.get("action", "")
        if alloc.get("size_usdt", 0) > 0:
            entries += 1
            total_usdt += alloc["size_usdt"]
            print(f"  {sym}: {action} {alloc['size_usdt']:.2f} USDT "
                  f"lev={alloc['leverage']}x blend={alloc['blending_factor']:.2f} "
                  f"[{alloc['reason']}]")
        else:
            print(f"  {sym}: {action} [{alloc.get('reason', '')}]")

    print(f"\nResumen: {entries} entradas, {total_usdt:.2f} USDT total")
    print("Simulación completada.")


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if "--simulate" in sys.argv:
        _test_simulate()
    else:
        _test_basic()
