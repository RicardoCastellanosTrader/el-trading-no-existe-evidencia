"""
brain_engine.py — Motor de señales y clasificación de régimen (live)

Recibe DataFrames OHLCV de data_feed.py, clasifica el régimen de cada símbolo,
evalúa condiciones de entrada/salida según la config activa, y devuelve señales.
No ejecuta órdenes ni decide sizing — solo genera señales puras.

Replica en tiempo real la lógica del kernel Numba de lab_historico_numba_v8_3.py
para UNA sola barra (la actual), usando la config seleccionada del specialist_configs.json.
"""

import os
import sys
import re
import json
import time
import logging
import argparse
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

# Importar funciones existentes del proyecto (capa superior)
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from regime_features import compute_regime_features, LOOKBACK_SHORT, LOOKBACK_LONG, N_FEATURES

# A05 S3 (2026-04-23): single source of truth para zone_bull_mr/zone_bear_mr
# — elimina 6 inline comparisons fast<slow/fast>slow dispersos en MR cancel
# checks. Ver §13.4 entrada A05.
from mean_reversion_features import zone_bull_mr, zone_bear_mr

# Importar funciones de cálculo de MAs e indicadores de lab_historico
from lab_historico_numba_v8_3 import (
    calc_ema, calc_sma, calc_hma, calc_alma, calc_zlema, calc_kama,
    calc_dema, calc_tema, calc_mcginley, calc_vidya, calc_frama,
    calc_t3, calc_ssmoother, calc_vwma, calc_tenkan, calc_jma,
    calc_ma, calc_atr,
    calc_zone_with_hysteresis,
    calc_rsi, calc_macd, calc_stochastic, calc_vwmacd, calc_cmf, calc_cci, calc_momentum,
    calc_heikin_ashi, calc_ha_trend, resample_to_timeframe,
    precalculate_divergences_pine_faithful,
    decode_config,
)

logger = logging.getLogger("brain_engine")


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas OHLCV para que siempre exista 'timestamp' como pd.Timestamp UTC.

    Maneja:
      - Parquet con 'timestamp_ms' (int64 epoch millis) -> rename + convert
      - Index llamado 'timestamp' -> reset_index
      - 'timestamp' ya existente como int/str -> convert a pd.Timestamp
      - data_feed en producción que ya entrega 'timestamp' como Timestamp -> no-op
    """
    if 'timestamp' not in df.columns:
        if 'timestamp_ms' in df.columns:
            df = df.rename(columns={'timestamp_ms': 'timestamp'})
        elif df.index.name == 'timestamp':
            df = df.reset_index()
        else:
            # Último recurso: crear timestamp sintético (no debería ocurrir)
            logger.warning("DataFrame sin columna timestamp — generando índice sintético")
            df = df.copy()
            df['timestamp'] = pd.date_range('2020-01-01', periods=len(df), freq='1h', tz='UTC')
            return df

    # Convertir a pd.Timestamp UTC si es numérico (epoch ms)
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

    return df

# ---------------------------------------------------------------------------
# Constantes (idénticas a lab_historico / master.py CONFIG)
# ---------------------------------------------------------------------------
SL_PERCENT = 3.0
SL_EMERGENCY_PERCENT = 5.0
TS_PERCENT = 0.5
COOLDOWN_BARS = 1
COMMISSION_ROUND_TRIP = 0.10

HYST_ATR_LEN = 14
CONFIRM_THRESHOLD = 0.75  # histéresis de cambio de cluster

# Divergence indicator constants
DIV_RSI_LEN = 14
DIV_MACD_FAST = 12
DIV_MACD_SLOW = 26
DIV_MACD_SIGNAL = 9
DIV_STOCH_K = 14
DIV_STOCH_D = 3
DIV_STOCH_SMOOTH = 3
DIV_VWMACD_FAST = 12
DIV_VWMACD_SLOW = 26
DIV_CMF_LEN = 21
DIV_CCI_LEN = 10
DIV_MOM_LEN = 10
DIV_PIVOT_PERIOD = 5
DIV_MAX_PIVOTS = 10
DIV_MAX_BARS = 100


# ---------------------------------------------------------------------------
# State classes
# ---------------------------------------------------------------------------
@dataclass
class SymbolState:
    """Estado de trading de un símbolo entre ciclos."""
    current_cluster: int = -1
    cluster_probs: np.ndarray = None
    active_config_id: int = -1
    active_preset: str = ''

    # Estado de posición (sincronizado con exchange cada ciclo)
    position: int = 0               # 0=flat, 1=long, -1=short
    entry_price: float = 0.0
    entry_bar_timestamp: int = 0
    sl_level: float = 0.0
    entry_filters_forming: int = 0  # para cancel_tf
    stop_order_id: str = ''         # BingX order ID del stop-loss activo
    entry_timestamp_ms: int = 0     # v2.3.3: wall-clock ms de la confirmacion BingX del fill

    # Contexto de divergencias (persiste entre barras)
    div_ctx_bull: bool = False
    div_ctx_bear: bool = False
    prev_div_bull_now: bool = False
    prev_div_bear_now: bool = False

    # Historial de zonas para detección de cruces
    prev_zone_bull: bool = False
    prev_zone_bear: bool = False

    # Cooldown
    cooldown_until: int = 0  # timestamp ms hasta el cual no entrar
    bars_since_entry: int = 0

    # Mean-reversion specific state
    mr_entry_zone_bull: bool = False
    # A05 S2 DEPRECATED 2026-04-23: dead fields — asignados en entry MR path
    # (L2099-2100, L2119-2120) pero NUNCA leídos en el resto del código.
    # Residuos de iteración previa de diseño (cancel_zona snapshot-based)
    # abandonada al migrar a paridad kernel MR. Preservados con default 0/0.0
    # para back-compat de engine_state.json productivo (VPS + local).
    # Eliminación planificada en próxima versión mayor (v3.0 pre-reciclaje).
    mr_entry_filters_forming: int = 0
    mr_entry_slow_line: float = 0.0
    mr_zone_history: list = field(default_factory=list)


@dataclass
class BrainState:
    """Estado persistente del brain engine entre ciclos."""
    # Modelos GMM por símbolo
    gmm_models: dict = field(default_factory=dict)
    # Configs de especialistas por símbolo y cluster
    specialist_configs: dict = field(default_factory=dict)
    # Estado por símbolo (persiste entre ciclos horarios)
    symbol_state: dict = field(default_factory=dict)
    # Cache de preset label -> 12-tuple (con p1/p2 exactos)
    preset_tuples: dict = field(default_factory=dict)

    def get_state(self, symbol: str) -> SymbolState:
        if symbol not in self.symbol_state:
            self.symbol_state[symbol] = SymbolState()
        return self.symbol_state[symbol]


# ---------------------------------------------------------------------------
# Carga de modelos al inicio (una vez)
# ---------------------------------------------------------------------------
def load_models(
    regime_models_dir: str = "regime_models",
    specialist_configs_dir: str = "regime_wf",
    symbols: list | None = None,
) -> BrainState:
    """
    Carga modelos GMM y configs de especialistas para todos los símbolos.

    Args:
        regime_models_dir: directorio con archivos SYMBOL_regime.joblib
        specialist_configs_dir: directorio con archivos SYMBOL_specialist_configs.json
        symbols: lista de símbolos a cargar (formato master.py: 'BTC/USDT')

    Returns:
        BrainState con gmm_models y specialist_configs poblados.
    """
    brain = BrainState()

    if symbols is None:
        from live.data_feed import MASTER_SYMBOLS
        symbols = MASTER_SYMBOLS

    t0 = time.perf_counter()
    loaded_gmm = 0
    loaded_configs = 0

    for symbol in symbols:
        sym_key = symbol.replace("/USDT", "").replace("/", "")
        sym_clean = symbol.replace("/", "")

        # Cargar modelo GMM
        model_path = os.path.join(regime_models_dir, f"{sym_key}_regime.joblib")
        if os.path.exists(model_path):
            try:
                model_data = joblib.load(model_path)
                brain.gmm_models[symbol] = {
                    'gmm': model_data['gmm'],
                    'scaler': model_data['scaler'],
                    'n_clusters': model_data['n_clusters'],
                    'lookback': model_data['lookback'],
                    'centroids': model_data['centroids'],
                    'cluster_names': model_data['cluster_names'],
                    'feature_names': model_data['feature_names'],
                }
                loaded_gmm += 1
            except Exception as e:
                logger.error(f"{symbol}: Error cargando GMM {model_path}: {e}")
        else:
            logger.warning(f"{symbol}: modelo GMM no encontrado ({model_path})")

        # Cargar specialist configs
        config_path = os.path.join(specialist_configs_dir, f"{sym_clean}_specialist_configs.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    cfg = json.load(f)
                brain.specialist_configs[symbol] = cfg
                loaded_configs += 1
            except Exception as e:
                logger.error(f"{symbol}: Error cargando configs {config_path}: {e}")
        else:
            logger.warning(f"{symbol}: specialist_configs no encontrado ({config_path})")

    # Cargar presets CSV para obtener p1/p2 exactos de cada MA
    for symbol in symbols:
        sym_clean = symbol.replace("/", "")
        csv_path = os.path.join(_project_root, "output", "production", f"presets_{sym_clean}.csv")
        if os.path.exists(csv_path):
            try:
                df_p = pd.read_csv(csv_path)
                for _, row in df_p.iterrows():
                    ft, fp = str(row['fast_type']), int(row['fast_period'])
                    st, sp = str(row['slow_type']), int(row['slow_period'])
                    tt, tp = str(row['trend_type']), int(row['trend_period'])
                    for hv in [0.0, 0.5]:
                        htag = f"H{hv:.1f}".replace(".", "")
                        label = f"{ft}({fp})/{st}({sp})_{htag}"
                        brain.preset_tuples[label] = (
                            ft, fp, float(row['fast_p1']), float(row['fast_p2']),
                            st, sp, float(row['slow_p1']), float(row['slow_p2']),
                            tt, tp, float(row['trend_p1']), float(row['trend_p2']),
                        )
            except Exception as e:
                logger.warning(f"{symbol}: Error cargando presets CSV: {e}")

    elapsed = time.perf_counter() - t0
    logger.info(f"Modelos cargados: {loaded_gmm} GMM, {loaded_configs} specialist_configs "
                f"({len(symbols)} símbolos) en {elapsed:.2f}s")

    return brain


# ---------------------------------------------------------------------------
# Helper: reset state en exit de posicion
# ---------------------------------------------------------------------------
def _reset_state_on_exit(state: 'SymbolState', mr: bool = False) -> None:
    """
    v2.3.9 (fix B1): reset completo de state al cerrar posicion.
    Evita valores stale en campos que algunos consumers (log [SIGNALS_RAW],
    engine_state.json para audit/analyzer) leen tras el exit. Los campos
    de config (current_cluster, active_config_id, cluster_probs) NO se
    resetean aqui — mantienen el contexto de clasificacion. Los campos
    historicos (prev_zone, prev_div, div_ctx, cooldown_until) tampoco —
    mantienen contexto entre ciclos.

    Args:
        state: SymbolState a resetear.
        mr: si True, ademas resetea mr_zone_history (MR-specific).
    """
    state.position = 0
    state.entry_price = 0.0
    state.sl_level = 0.0
    state.bars_since_entry = 0
    state.entry_bar_timestamp = 0
    state.entry_filters_forming = 0
    state.stop_order_id = ''
    state.entry_timestamp_ms = 0
    if mr:
        state.mr_zone_history = []


# ---------------------------------------------------------------------------
# 1. classify_regimes
# ---------------------------------------------------------------------------
def classify_regimes(brain: BrainState, market_data: dict) -> dict:
    """
    Clasifica el régimen actual de cada símbolo.

    Args:
        brain: estado persistente
        market_data: {'BTC/USDT': DataFrame(500 barras)} de data_feed

    Returns:
        {'BTC/USDT': {
            'cluster': 1,
            'cluster_name': 'norm-vol/choppy',
            'probs': [0.12, 0.75, 0.13],
            'confidence': 0.75,
            'prev_cluster': 0,
            'transition': True,
            'operable': True,
        }, ...}
    """
    results = {}

    for symbol, df in market_data.items():
        if df is None or len(df) < LOOKBACK_SHORT + 10:
            logger.warning(f"{symbol}: datos insuficientes ({len(df) if df is not None else 0} barras)")
            continue

        state = brain.get_state(symbol)

        if symbol not in brain.gmm_models:
            # Fallback: cluster 0, siempre operable
            results[symbol] = {
                'cluster': 0,
                'cluster_name': 'all',
                'probs': [1.0],
                'confidence': 1.0,
                'prev_cluster': state.current_cluster,
                'transition': state.current_cluster != 0 and state.current_cluster != -1,
                'operable': True,
            }
            state.current_cluster = 0
            state.cluster_probs = np.array([1.0])
            continue

        model = brain.gmm_models[symbol]
        gmm = model['gmm']
        scaler = model['scaler']
        n_clusters = model['n_clusters']

        # Calcular features sobre las últimas barras
        features, valid_mask = compute_regime_features(df, lookback=model['lookback'])

        if not valid_mask.any():
            logger.warning(f"{symbol}: sin features válidas para clasificación")
            results[symbol] = {
                'cluster': state.current_cluster if state.current_cluster >= 0 else 0,
                'cluster_name': 'unknown',
                'probs': [1.0 / n_clusters] * n_clusters,
                'confidence': 0.0,
                'prev_cluster': state.current_cluster,
                'transition': False,
                'operable': False,
            }
            continue

        # Usar la última barra con features válidas
        last_valid_idx = np.where(valid_mask)[0][-1]
        feat_row = features[last_valid_idx:last_valid_idx + 1]  # (1, N_FEATURES)

        X = scaler.transform(feat_row)
        probs = gmm.predict_proba(X)[0]
        new_cluster = int(np.argmax(probs))
        confidence = float(probs[new_cluster])

        # Histéresis: solo cambiar si confianza > threshold
        prev_cluster = state.current_cluster
        if prev_cluster >= 0 and new_cluster != prev_cluster:
            if confidence < CONFIRM_THRESHOLD:
                new_cluster = prev_cluster
                confidence = float(probs[prev_cluster])

        transition = prev_cluster >= 0 and new_cluster != prev_cluster

        # Determinar si el cluster es operable (sqn_p5 > 0 del top config)
        operable = _is_cluster_operable(brain, symbol, new_cluster)

        cluster_names = model.get('cluster_names', [f'C{i}' for i in range(n_clusters)])
        cluster_name = cluster_names[new_cluster] if new_cluster < len(cluster_names) else f'C{new_cluster}'

        results[symbol] = {
            'cluster': new_cluster,
            'cluster_name': cluster_name,
            'probs': [float(p) for p in probs],
            'confidence': confidence,
            'prev_cluster': prev_cluster,
            'transition': transition,
            'operable': operable,
        }

        state.current_cluster = new_cluster
        state.cluster_probs = probs

    return results


def _is_cluster_operable(brain: BrainState, symbol: str, cluster: int) -> bool:
    """Verifica si un cluster es operable (sqn_p5 > 0 del top config, o MR present)."""
    cfg = brain.specialist_configs.get(symbol)
    if not cfg:
        return False
    cluster_data = cfg.get('clusters', {}).get(str(cluster))
    if not cluster_data:
        return False
    # MR clusters are operable if they have a config_id
    mr_block = cluster_data.get('mean_reversion')
    if mr_block and mr_block.get('strategy_type') == 'mean_reversion':
        return mr_block.get('config_id', 0) > 0
    # TF check
    top_configs = cluster_data.get('top_configs', [])
    if not top_configs:
        return False
    return top_configs[0].get('sqn_p5', 0) > 0


# ---------------------------------------------------------------------------
# 2. apply_btc_override
# ---------------------------------------------------------------------------
def apply_btc_override(brain: BrainState, regimes: dict) -> dict:
    """
    Si BTC está en pánico (cluster de high-vol), fuerza altcoins a su propio
    cluster equivalente (el de mayor Z_ATR en centroides).

    No modifica BTC. Solo aplica si confidence > 80%.
    """
    btc_regime = regimes.get('BTC/USDT')
    if not btc_regime:
        return regimes

    # Determinar si BTC está en cluster de high-vol
    btc_model = brain.gmm_models.get('BTC/USDT')
    if not btc_model or btc_model['centroids'] is None:
        return regimes

    centroids = btc_model['centroids']  # (n_clusters, n_features)
    # Z_ATR es feature index 1
    btc_highvol_cluster = int(np.argmax(centroids[:, 1]))

    if btc_regime['cluster'] != btc_highvol_cluster:
        return regimes
    if btc_regime['confidence'] < 0.80:
        return regimes

    logger.warning(f"BTC PANIC OVERRIDE: BTC en cluster high-vol (C{btc_highvol_cluster}, "
                   f"conf={btc_regime['confidence']:.2f})")

    for symbol in regimes:
        if symbol == 'BTC/USDT':
            continue

        model = brain.gmm_models.get(symbol)
        if not model or model['centroids'] is None:
            continue

        # Encontrar cluster equivalente de high-vol para esta altcoin
        sym_centroids = model['centroids']
        alt_highvol = int(np.argmax(sym_centroids[:, 1]))

        if regimes[symbol]['cluster'] != alt_highvol:
            prev = regimes[symbol]['cluster']
            regimes[symbol]['cluster'] = alt_highvol
            regimes[symbol]['transition'] = True
            regimes[symbol]['operable'] = _is_cluster_operable(brain, symbol, alt_highvol)

            cluster_names = model.get('cluster_names', [])
            regimes[symbol]['cluster_name'] = (
                cluster_names[alt_highvol] if alt_highvol < len(cluster_names) else f'C{alt_highvol}'
            )
            # v2.3.7 (fix S3): sincronizar state con override. Sin esto,
            # state.cluster_probs[state.current_cluster] reporta confidence
            # del cluster pre-override en _evaluate_bar.
            state = brain.get_state(symbol)
            state.current_cluster = alt_highvol
            logger.info(f"  {symbol}: forzado C{prev} -> C{alt_highvol} (BTC panic)")

    return regimes


# ---------------------------------------------------------------------------
# 3. select_active_configs
# ---------------------------------------------------------------------------
def select_active_configs(brain: BrainState, regimes: dict) -> dict:
    """
    Para cada símbolo, selecciona la config activa según el régimen detectado.

    Returns:
        {'BTC/USDT': {
            'config_id': 35566438,
            'preset': 'T3(18)/McGinley(36)_H05',
            'config_bits': {decoded bits...},
            'cluster': 1,
            'operable': True,
            'regime_changed': False,
        }, ...}
    """
    results = {}

    for symbol, regime in regimes.items():
        cluster = regime['cluster']
        operable = regime['operable']
        state = brain.get_state(symbol)

        cfg_data = brain.specialist_configs.get(symbol)
        if not cfg_data:
            results[symbol] = {
                'config_id': -1, 'preset': '', 'config_bits': {},
                'cluster': cluster, 'operable': False, 'regime_changed': False,
            }
            # v2.3.7 (fix S5): reset state para simbolos no-operables.
            state.active_config_id = -1
            state.active_preset = ''
            continue

        cluster_data = cfg_data.get('clusters', {}).get(str(cluster))
        if not cluster_data:
            results[symbol] = {
                'config_id': -1, 'preset': '', 'config_bits': {},
                'cluster': cluster, 'operable': False, 'regime_changed': False,
            }
            # v2.3.7 (fix S5): reset state para simbolos no-operables.
            state.active_config_id = -1
            state.active_preset = ''
            continue

        # Check for mean-reversion strategy in this cluster
        mr_block = cluster_data.get('mean_reversion')
        if mr_block and mr_block.get('strategy_type') == 'mean_reversion':
            mr_config_id = mr_block['config_id']
            regime_changed = regime['transition'] and state.position != 0
            results[symbol] = {
                'config_id': mr_config_id,
                'preset': '',
                'preset_tuple': None,
                'config_bits': {},
                'cluster': cluster,
                'operable': operable,
                'regime_changed': regime_changed,
                'strategy_type': 'mean_reversion',
                'mr_config': mr_block,
                'mr_bits': decode_mr_config_bits(mr_config_id),
            }
            state.active_config_id = mr_config_id
            state.active_preset = 'MR'
            continue

        top_configs = cluster_data.get('top_configs', [])

        # Seleccionar top-1 config con cross_cluster_survival: True
        selected = None
        for cfg in top_configs:
            if cfg.get('cross_cluster_survival', True):
                selected = cfg
                break
        if selected is None and top_configs:
            selected = top_configs[0]

        if selected is None:
            results[symbol] = {
                'config_id': -1, 'preset': '', 'config_bits': {},
                'cluster': cluster, 'operable': False, 'regime_changed': False,
            }
            # v2.3.7 (fix S5): reset state para simbolos no-operables.
            state.active_config_id = -1
            state.active_preset = ''
            continue

        config_id = selected['config_id']
        config_bits = decode_config_bits(config_id)

        # Detectar si el régimen cambió con posición abierta
        regime_changed = regime['transition'] and state.position != 0

        preset_str = selected.get('preset', '')
        results[symbol] = {
            'config_id': config_id,
            'preset': preset_str,
            'preset_tuple': brain.preset_tuples.get(preset_str),
            'config_bits': config_bits,
            'cluster': cluster,
            'operable': operable,
            'regime_changed': regime_changed,
        }

        state.active_config_id = config_id
        state.active_preset = selected.get('preset', '')

    return results


# ---------------------------------------------------------------------------
# 4. generate_signals
# ---------------------------------------------------------------------------
def generate_signals(
    brain: BrainState,
    market_data: dict,
    active_configs: dict,
) -> dict:
    """
    Evalúa condiciones de trading para cada símbolo.

    Returns:
        {'BTC/USDT': {
            'action': 'LONG',
            'reason': 'ma_cross',
            'entry_price': 65432.10,
            'sl_price': 63469.14,
            'use_ts': False,
            'confidence': 0.75,
            'operable': True,
        }, ...}
    """
    results = {}

    for symbol, cfg in active_configs.items():
        df = market_data.get(symbol)
        if df is None or len(df) < 50:
            results[symbol] = _flat_signal(symbol, 'no_data')
            continue

        if not cfg['operable'] or cfg['config_id'] < 0:
            results[symbol] = _flat_signal(symbol, 'not_operable', operable=False)
            continue

        state = brain.get_state(symbol)

        # Si el régimen cambió con posición abierta: cerrar inmediatamente
        if cfg.get('regime_changed', False):
            action = 'CLOSE_LONG' if state.position == 1 else 'CLOSE_SHORT'
            close_price = float(df['close'].iloc[-1])
            results[symbol] = {
                'action': action,
                'reason': 'regime_change',
                'entry_price': close_price,
                'sl_price': 0.0,
                'use_ts': False,
                'confidence': cfg.get('config_bits', {}).get('confidence', 0),
                'operable': True,
            }
            # Reset state
            state.position = 0
            state.entry_price = 0.0
            state.sl_level = 0.0
            continue

        try:
            if cfg.get('strategy_type') == 'mean_reversion':
                signal = _evaluate_bar_mr(brain, symbol, df, cfg)
            else:
                signal = _evaluate_bar(brain, symbol, df, cfg)
            results[symbol] = signal
        except Exception as e:
            logger.error(f"{symbol}: Error evaluando señal: {e}")
            results[symbol] = _flat_signal(symbol, f'error: {e}')

    return results


def _flat_signal(symbol: str, reason: str, operable: bool = True) -> dict:
    return {
        'action': 'FLAT',
        'reason': reason,
        'entry_price': 0.0,
        'sl_price': 0.0,
        'use_ts': False,
        'confidence': 0.0,
        'operable': operable,
    }


def _evaluate_bar(brain: BrainState, symbol: str, df: pd.DataFrame, cfg: dict) -> dict:
    """
    Evalúa la barra actual de un símbolo. Fiel al kernel Numba.
    """
    state = brain.get_state(symbol)
    # v2.3.7 (fix S2): incrementar contador de barras con posicion abierta.
    # Consumido por audit_fidelity/analyzer via engine_state.json (_save_state).
    # Reset a 0 en los 6 puntos de entry/exit mas abajo.
    if state.position != 0:
        state.bars_since_entry += 1
    bits = cfg['config_bits']
    preset_str = cfg['preset']

    # --- Precalcular indicadores sobre todas las barras ---
    close_arr = df['close'].values.astype(np.float64)
    high_arr = df['high'].values.astype(np.float64)
    low_arr = df['low'].values.astype(np.float64)
    volume_arr = df['volume'].values.astype(np.float64)
    n = len(close_arr)
    t = n - 1  # barra actual (última)

    # Parsear preset y calcular MAs (con p1/p2 exactos si disponible)
    ma_info = compute_mas(df, preset_str, preset_tuple=cfg.get('preset_tuple'))
    fast_ma = ma_info['fast_ma']
    slow_ma = ma_info['slow_ma']
    trend_ma = ma_info['trend_ma']
    hyst_mult = ma_info['hyst']

    # ATR para histéresis
    atr_arr = calc_atr(high_arr, low_arr, close_arr, HYST_ATR_LEN)

    # Zonas bull/bear
    zone_bull_arr, zone_bear_arr = calc_zone_with_hysteresis(fast_ma, slow_ma, atr_arr, hyst_mult)
    z_bull = bool(zone_bull_arr[t])
    z_bear = bool(zone_bear_arr[t])

    # Detectar cambio de zona
    if t > 0:
        prev_z_bull = bool(zone_bull_arr[t - 1])
        prev_z_bear = bool(zone_bear_arr[t - 1])
    else:
        prev_z_bull = state.prev_zone_bull
        prev_z_bear = state.prev_zone_bear

    # --- Filtros TF ---
    f_forming, f_resolved = compute_filters(df, slow_ma, trend_ma)

    # --- Divergencias ---
    div_bull_now, div_bear_now, div_ctx_bull, div_ctx_bear = compute_divergences(
        df, bits, state
    )

    # Guardar prev_div para entrada (entries use previous bar's div, Pine-faithful)
    prev_div_bull = state.prev_div_bull_now
    prev_div_bear = state.prev_div_bear_now

    # Actualizar div_ctx con cambio de zona
    if prev_z_bear and z_bull:
        div_ctx_bull = False  # reset
    if prev_z_bull and z_bear:
        div_ctx_bear = False  # reset

    # Actualizar div_ctx con prev bar's div
    if prev_div_bull:
        div_ctx_bull = True
        div_ctx_bear = False
    if prev_div_bear:
        div_ctx_bear = True
        div_ctx_bull = False

    # Snapshot entry div_ctx BEFORE current bar updates
    entry_div_ctx_bull = div_ctx_bull
    entry_div_ctx_bear = div_ctx_bear

    # Ahora actualizar con current bar's div (para future bars)
    if div_bull_now:
        div_ctx_bull = True
    if div_bear_now:
        div_ctx_bear = True

    # Extraer bits de config
    exit_mask = bits['exit_mask']
    entry_mask = bits['entry_mask']
    div_entry_mode = bits['div_entry_mode']
    div_exit = bits['div_exit']
    div_type = bits['div_type']
    cancel_tf = bits['cancel_tf']
    use_ts = bits['use_ts']

    close_p = close_arr[t]
    high_p = high_arr[t]
    low_p = low_arr[t]

    signal = {
        'action': 'HOLD' if state.position != 0 else 'FLAT',
        'reason': '',
        'entry_price': close_p,
        'sl_price': state.sl_level,
        'use_ts': bool(use_ts),
        'confidence': float(state.cluster_probs[state.current_cluster]) if state.cluster_probs is not None else 0.0,
        'operable': True,
    }

    # =====================================================
    # EXIT LOGIC (position != 0)
    # =====================================================
    if state.position != 0:
        exit_signal = False
        sl_exit_signal = False
        sl_emergency_signal = False
        div_exit_signal = False
        normal_exit_signal = False
        cancel_signal = False
        exit_price = close_p

        # 1. Trailing stop update
        if use_ts and t > 0:
            prev_low = low_arr[t - 1]
            prev_high = high_arr[t - 1]
            if state.position == 1:
                potential_stop = prev_low * (1 - TS_PERCENT / 100)
                if potential_stop > state.sl_level:
                    state.sl_level = potential_stop
            elif state.position == -1:
                potential_stop = prev_high * (1 + TS_PERCENT / 100)
                if state.sl_level == 0.0 or potential_stop < state.sl_level:
                    state.sl_level = potential_stop
            # Propagar nuevo SL al signal dict
            signal['sl_price'] = state.sl_level

        # 2. Emergency SL
        if state.position == 1:
            emerg_level = state.entry_price * (1 - SL_EMERGENCY_PERCENT / 100)
            if low_p <= emerg_level:
                exit_signal = True
                sl_exit_signal = True
                sl_emergency_signal = True
                exit_price = emerg_level
        elif state.position == -1:
            emerg_level = state.entry_price * (1 + SL_EMERGENCY_PERCENT / 100)
            if high_p >= emerg_level:
                exit_signal = True
                sl_exit_signal = True
                sl_emergency_signal = True
                exit_price = emerg_level

        # 3. Fixed SL
        if not exit_signal:
            if state.position == 1 and close_p < state.sl_level:
                exit_signal = True
                sl_exit_signal = True
            elif state.position == -1 and close_p > state.sl_level:
                exit_signal = True
                sl_exit_signal = True

        # 4. Divergence exit
        if not exit_signal and div_exit and div_type > 0:
            if state.position == 1 and div_bear_now:
                exit_signal = True
                div_exit_signal = True
            elif state.position == -1 and div_bull_now:
                exit_signal = True
                div_exit_signal = True

        # 5. TF filter exit
        if not exit_signal and exit_mask > 0:
            exit_count_active = 0
            exit_count_bull = 0
            for bit in range(4):
                if (exit_mask >> bit) & 1:
                    exit_count_active += 1
                    if (f_forming >> bit) & 1:
                        exit_count_bull += 1
            if exit_count_active > 0:
                if state.position == 1 and exit_count_bull == 0:
                    exit_signal = True
                    normal_exit_signal = True
                elif state.position == -1 and exit_count_bull == exit_count_active:
                    exit_signal = True
                    normal_exit_signal = True

        # 6. Zone exit
        if not exit_signal:
            if state.position == 1 and z_bear:
                exit_signal = True
                normal_exit_signal = True
            elif state.position == -1 and z_bull:
                exit_signal = True
                normal_exit_signal = True

        # 7. Cancel TF
        if not exit_signal and cancel_tf:
            cancel_signal = _check_cancel_tf(
                state, entry_mask, f_forming, f_resolved, df, t
            )

        # Process exit
        if exit_signal or cancel_signal:
            if state.position == 1:
                action = 'CLOSE_LONG'
            else:
                action = 'CLOSE_SHORT'

            if sl_emergency_signal:
                reason = 'sl_emergency'
            elif sl_exit_signal:
                reason = 'sl_hit'
            elif div_exit_signal:
                reason = 'div_exit'
            elif cancel_signal:
                reason = 'cancel_tf'
            elif normal_exit_signal:
                reason = 'zone_exit' if (
                    (state.position == 1 and z_bear) or (state.position == -1 and z_bull)
                ) else 'tf_exit'
            else:
                reason = 'exit'

            signal = {
                'action': action,
                'reason': reason,
                'entry_price': exit_price,
                'sl_price': 0.0,
                'use_ts': bool(use_ts),
                'confidence': signal['confidence'],
                'operable': True,
            }

            # Determine cooldown (using bar index as proxy)
            if sl_emergency_signal or cancel_signal:
                state.cooldown_until = 0  # immediate
            elif sl_exit_signal or div_exit_signal:
                state.cooldown_until = COOLDOWN_BARS  # bars to wait
            else:
                state.cooldown_until = 0  # no cooldown for normal exit

            # v2.3.9 (fix B1): reset completo (incluye campos antes stale).
            _reset_state_on_exit(state, mr=False)

            # Reset div_ctx for exited direction (local var, persisted at end)
            if action == 'CLOSE_LONG':
                div_ctx_bull = False
            else:
                div_ctx_bear = False

    # Zone-based div_ctx cleanup (kernel lines 1659-1662, every bar)
    if z_bear:
        div_ctx_bull = False
    if z_bull:
        div_ctx_bear = False

    # =====================================================
    # ENTRY LOGIC (position == 0)
    # =====================================================
    if state.position == 0:
        # Decrement cooldown counter
        if state.cooldown_until > 0:
            state.cooldown_until -= 1
            # Still in cooldown
        else:
            # Build entry TF flags
            entry_tf_count = bin(entry_mask).count('1')
            exit_tf_count = bin(exit_mask).count('1')

            tf_entry_ok_bull = True
            tf_entry_ok_bear = True

            for bit in range(5):
                if (entry_mask >> bit) & 1:
                    if bit < 3:
                        if not ((f_forming >> bit) & 1):
                            tf_entry_ok_bull = False
                        if (f_forming >> bit) & 1:
                            tf_entry_ok_bear = False
                    elif bit == 3:  # TF4
                        if not ((f_forming >> 3) & 1):
                            tf_entry_ok_bull = False
                        if not ((f_forming >> 11) & 1):
                            tf_entry_ok_bear = False
                    elif bit == 4:  # TF5
                        if not ((f_forming >> 4) & 1):
                            tf_entry_ok_bull = False
                        if not ((f_forming >> 12) & 1):
                            tf_entry_ok_bear = False

            # Effective div context
            effective_ctx_bull = entry_div_ctx_bull or prev_div_bull
            effective_ctx_bear = entry_div_ctx_bear or prev_div_bear

            # Entry conditions by div_entry_mode
            long_cond = False
            short_cond = False

            if div_entry_mode == 0:  # OFF
                if z_bull:
                    long_cond = tf_entry_ok_bull if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = tf_entry_ok_bear if entry_tf_count > 0 else True

            elif div_entry_mode == 1:  # CONTEXTUAL
                if z_bull:
                    if entry_tf_count > 0:
                        long_cond = tf_entry_ok_bull and effective_ctx_bull
                    elif exit_tf_count > 0:
                        long_cond = effective_ctx_bull
                    else:
                        long_cond = prev_div_bull
                if z_bear:
                    if entry_tf_count > 0:
                        short_cond = tf_entry_ok_bear and effective_ctx_bear
                    elif exit_tf_count > 0:
                        short_cond = effective_ctx_bear
                    else:
                        short_cond = prev_div_bear

            elif div_entry_mode == 2:  # OR
                if z_bull:
                    if entry_tf_count > 0:
                        long_cond = tf_entry_ok_bull or prev_div_bull
                    else:
                        long_cond = True
                if z_bear:
                    if entry_tf_count > 0:
                        short_cond = tf_entry_ok_bear or prev_div_bear
                    else:
                        short_cond = True

            # Exit filter conflict check
            if long_cond and exit_mask > 0:
                exit_count_bull = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        if (f_forming >> bit) & 1:
                            exit_count_bull += 1
                if exit_count_bull == 0:
                    long_cond = False

            if short_cond and exit_mask > 0:
                exit_count_bull = 0
                exit_count_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        exit_count_active += 1
                        if (f_forming >> bit) & 1:
                            exit_count_bull += 1
                if exit_count_active > 0 and exit_count_bull == exit_count_active:
                    short_cond = False

            # Execute entry
            if long_cond:
                state.position = 1
                state.entry_price = close_p
                state.sl_level = low_p * (1 - SL_PERCENT / 100)
                state.entry_filters_forming = f_forming
                state.entry_bar_timestamp = int(df['timestamp'].iloc[t].timestamp() * 1000) if hasattr(df['timestamp'].iloc[t], 'timestamp') else 0
                state.bars_since_entry = 0
                signal = {
                    'action': 'LONG',
                    'reason': 'ma_cross',
                    'entry_price': close_p,
                    'sl_price': state.sl_level,
                    'use_ts': bool(use_ts),
                    'confidence': signal['confidence'],
                    'operable': True,
                }
            elif short_cond:
                state.position = -1
                state.entry_price = close_p
                state.sl_level = high_p * (1 + SL_PERCENT / 100)
                state.entry_filters_forming = f_forming
                state.entry_bar_timestamp = int(df['timestamp'].iloc[t].timestamp() * 1000) if hasattr(df['timestamp'].iloc[t], 'timestamp') else 0
                state.bars_since_entry = 0
                signal = {
                    'action': 'SHORT',
                    'reason': 'ma_cross',
                    'entry_price': close_p,
                    'sl_price': state.sl_level,
                    'use_ts': bool(use_ts),
                    'confidence': signal['confidence'],
                    'operable': True,
                }

    # Update persistent state
    state.prev_zone_bull = z_bull
    state.prev_zone_bear = z_bear
    state.prev_div_bull_now = div_bull_now
    state.prev_div_bear_now = div_bear_now
    state.div_ctx_bull = div_ctx_bull
    state.div_ctx_bear = div_ctx_bear

    return signal


# ---------------------------------------------------------------------------
# 5. decode_config_bits
# ---------------------------------------------------------------------------
def decode_config_bits(config_id: int) -> dict:
    """
    Decodifica los 26 bits del config_id en parámetros legibles.
    Idéntico a decode_config de lab_historico_numba_v8_3.py.
    """
    return {
        'exit_mask': config_id & 0xF,
        'entry_mask': (config_id >> 4) & 0x1F,
        'div_entry_mode': (config_id >> 9) & 0x3,
        'div_exit': (config_id >> 11) & 0x1,
        'div_type': (config_id >> 12) & 0x3,
        'div_ind_mask': (config_id >> 14) & 0xFF,
        'cancel_tf': (config_id >> 22) & 0x1,
        'use_ts': (config_id >> 23) & 0x1,
        'reg_inv': (config_id >> 24) & 0x1,
        'hid_inv': (config_id >> 25) & 0x1,
    }


# ---------------------------------------------------------------------------
# 6. compute_mas
# ---------------------------------------------------------------------------
def compute_mas(df: pd.DataFrame, preset: str, preset_tuple: tuple = None) -> dict:
    """
    Parsea el preset y calcula fast_ma, slow_ma, trend_ma.

    Args:
        df: DataFrame OHLCV
        preset: string label del preset (e.g. 'ALMA(24)/SMA(57)_H05')
        preset_tuple: opcional, 12-tuple con p1/p2 exactos del presets CSV.
                      Si se proporciona, usa los p1/p2 del tuple en vez de defaults.

    Returns:
        {'fast_ma': array, 'slow_ma': array, 'trend_ma': array, 'hyst': float}
    """
    close_arr = df['close'].values.astype(np.float64)
    high_arr = df['high'].values.astype(np.float64)
    low_arr = df['low'].values.astype(np.float64)
    volume_arr = df['volume'].values.astype(np.float64)

    if preset_tuple is not None:
        # Usar tuple con p1/p2 exactos
        ft, fp, fp1, fp2, st, sp, sp1, sp2, tt, tp, tp1, tp2 = preset_tuple
        hyst_match = re.search(r'_H(\d+)$', preset)
        hyst = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0
        fast_ma = calc_ma(ft, close_arr, high_arr, low_arr, volume_arr, fp, fp1, fp2)
        slow_ma = calc_ma(st, close_arr, high_arr, low_arr, volume_arr, sp, sp1, sp2)
        trend_ma = calc_ma(tt, close_arr, high_arr, low_arr, volume_arr, tp, tp1, tp2)
    else:
        # Fallback: sin p1/p2 (usará defaults de calc_ma)
        fast_type, fast_period, slow_type, slow_period, trend_type, trend_period, hyst = parse_preset(preset)
        fast_ma = calc_ma(fast_type, close_arr, high_arr, low_arr, volume_arr, fast_period)
        slow_ma = calc_ma(slow_type, close_arr, high_arr, low_arr, volume_arr, slow_period)
        trend_ma = calc_ma(trend_type, close_arr, high_arr, low_arr, volume_arr, trend_period)

    return {
        'fast_ma': fast_ma,
        'slow_ma': slow_ma,
        'trend_ma': trend_ma,
        'hyst': hyst,
    }


def parse_preset(preset: str) -> tuple:
    """
    Parsea el string del preset a parámetros.

    Format: 'FastType(FastLen)/SlowType(SlowLen)/TrendType_HXX'
    Trend period = slow_period × 4 (convención del sistema).

    Returns:
        (fast_type, fast_period, slow_type, slow_period, trend_type, trend_period, hyst_mult)
    """
    # Extraer histéresis del final: _H00 o _H05
    hyst_match = re.search(r'_H(\d+)$', preset)
    hyst_mult = 0.0
    if hyst_match:
        hyst_str = hyst_match.group(1)
        # H00 -> 0.0, H05 -> 0.5, H10 -> 1.0
        hyst_mult = int(hyst_str) / 10.0
        preset_core = preset[:hyst_match.start()]
    else:
        preset_core = preset

    # Split por '/'
    parts = preset_core.split('/')
    if len(parts) == 3:
        fast_str, slow_str, trend_str = parts
    elif len(parts) == 2:
        fast_str, slow_str = parts
        trend_str = slow_str  # trend = slow type, period × 4
    else:
        raise ValueError(f"Preset format inválido: {preset}")

    def _parse_ma_part(s: str) -> tuple:
        """Parsea 'Type(Period)' o 'Type(Period,vX.X)' a (type_str, period)."""
        m = re.match(r'(\w+)\((\d+)(?:,.*?)?\)', s.strip())
        if not m:
            raise ValueError(f"No se pudo parsear MA: '{s}'")
        return m.group(1), int(m.group(2))

    fast_type, fast_period = _parse_ma_part(fast_str)
    slow_type, slow_period = _parse_ma_part(slow_str)

    # Trend: puede tener período explícito o derivado
    try:
        trend_type, trend_period = _parse_ma_part(trend_str)
    except ValueError:
        # Si no tiene período, usar slow_period × 4
        trend_type = trend_str.strip()
        trend_period = slow_period * 4

    # Si trend_period parece ser igual a slow_period, usar convención ×4
    if trend_period == slow_period:
        trend_period = slow_period * 4

    return fast_type, fast_period, slow_type, slow_period, trend_type, trend_period, hyst_mult


# ---------------------------------------------------------------------------
# 7. compute_divergences
# ---------------------------------------------------------------------------
def compute_divergences(
    df: pd.DataFrame,
    config_bits: dict,
    state: SymbolState,
) -> tuple:
    """
    Calcula divergencias para la barra actual.

    Returns:
        (div_bull_now, div_bear_now, div_ctx_bull, div_ctx_bear)
    """
    div_type = config_bits.get('div_type', 0)
    div_ind_mask = config_bits.get('div_ind_mask', 0)
    reg_inv = config_bits.get('reg_inv', 0)
    hid_inv = config_bits.get('hid_inv', 0)

    if div_type == 0 or div_ind_mask == 0:
        return False, False, state.div_ctx_bull, state.div_ctx_bear

    close_s = df['close']
    high_s = df['high']
    low_s = df['low']
    volume_s = df['volume']

    # Calcular los 8 indicadores
    rsi = calc_rsi(close_s, DIV_RSI_LEN).values
    macd_line, macd_hist = calc_macd(close_s, DIV_MACD_FAST, DIV_MACD_SLOW, DIV_MACD_SIGNAL)
    macd_line = macd_line.values
    macd_hist = macd_hist.values
    stoch = calc_stochastic(high_s, low_s, close_s, DIV_STOCH_K, DIV_STOCH_D, DIV_STOCH_SMOOTH).values
    vwmacd = calc_vwmacd(close_s, volume_s, DIV_VWMACD_FAST, DIV_VWMACD_SLOW).values
    cmf = calc_cmf(high_s, low_s, close_s, volume_s, DIV_CMF_LEN).values
    cci = calc_cci(high_s, low_s, close_s, DIV_CCI_LEN).values
    mom = calc_momentum(close_s, DIV_MOM_LEN).values

    indicators = {
        'rsi': rsi, 'macd_hist': macd_hist, 'macd_line': macd_line,
        'stoch': stoch, 'vwmacd': vwmacd, 'cmf': cmf, 'cci': cci, 'mom': mom,
    }

    close_arr = df['close'].values.astype(np.float64)
    high_arr = df['high'].values.astype(np.float64)
    low_arr = df['low'].values.astype(np.float64)
    n = len(close_arr)

    # Calcular div_bits para todas las barras (necesario por los pivots)
    div_bits_arr = precalculate_divergences_pine_faithful(
        close_arr, high_arr, low_arr, indicators,
        n, DIV_PIVOT_PERIOD, DIV_MAX_PIVOTS, DIV_MAX_BARS
    )

    # Evaluar divergencia en la barra actual
    t = n - 1
    net_div_score = 0

    for ind in range(8):
        if not (div_ind_mask & (1 << ind)):
            continue

        bits = int(div_bits_arr[t, ind])

        ind_bull = False
        ind_bear = False

        if div_type == 1:  # REGULAR only
            if reg_inv == 0:
                ind_bull = (bits & 1) > 0
                ind_bear = (bits & 4) > 0
            else:
                ind_bull = (bits & 4) > 0
                ind_bear = (bits & 1) > 0
        elif div_type == 2:  # HIDDEN only
            if hid_inv == 0:
                ind_bull = (bits & 8) > 0
                ind_bear = (bits & 2) > 0
            else:
                ind_bull = (bits & 2) > 0
                ind_bear = (bits & 8) > 0
        elif div_type == 3:  # BOTH
            if reg_inv == 0:
                reg_bull = (bits & 1) > 0
                reg_bear = (bits & 4) > 0
            else:
                reg_bull = (bits & 4) > 0
                reg_bear = (bits & 1) > 0

            if hid_inv == 0:
                hid_bull = (bits & 8) > 0
                hid_bear = (bits & 2) > 0
            else:
                hid_bull = (bits & 2) > 0
                hid_bear = (bits & 8) > 0

            ind_bull = reg_bull or hid_bull
            ind_bear = reg_bear or hid_bear

        if ind_bull:
            net_div_score += 1
        if ind_bear:
            net_div_score -= 1

    div_bull_now = net_div_score >= 1
    div_bear_now = net_div_score <= -1

    return div_bull_now, div_bear_now, state.div_ctx_bull, state.div_ctx_bear


# ---------------------------------------------------------------------------
# 8. compute_filters
# ---------------------------------------------------------------------------
def compute_filters(df: pd.DataFrame, slow_ma: np.ndarray, trend_ma: np.ndarray) -> tuple:
    """
    Calcula filtros TF forming y resolved para la barra actual.

    Returns:
        (f_forming, f_resolved) como uint32 con los bits de TF1-TF5.
    """
    n = len(df)
    t = n - 1

    close_arr = df['close'].values.astype(np.float64)

    # Ensure timestamp is the index for resampling
    if 'timestamp' in df.columns:
        df_ts = df.copy()
        if not isinstance(df_ts['timestamp'].iloc[0], pd.Timestamp):
            df_ts['timestamp'] = pd.to_datetime(df_ts['timestamp'], utc=True)
    else:
        df_ts = df.copy()

    # TF1: HA trend 1h (forming = current bar)
    tf1_bull = bool(calc_ha_trend(df_ts).iloc[-1]) if len(df_ts) > 1 else True

    # TF2: HA trend 4h (forming = incomplete current 4h bar)
    df_4h = resample_to_timeframe(df_ts, "4h")
    tf2_trend = calc_ha_trend(df_4h)
    tf2_bull_forming = bool(tf2_trend.iloc[-1]) if len(tf2_trend) > 0 else True

    # TF2 resolved: previous completed 4h bar
    tf2_bull_resolved = bool(tf2_trend.iloc[-2]) if len(tf2_trend) > 1 else True

    # TF3: HA trend 1d (forming = incomplete current daily bar)
    df_1d = resample_to_timeframe(df_ts, "1d")
    tf3_trend = calc_ha_trend(df_1d)
    tf3_bull_forming = bool(tf3_trend.iloc[-1]) if len(tf3_trend) > 0 else True

    # TF3 resolved: previous completed daily bar
    tf3_bull_resolved = bool(tf3_trend.iloc[-2]) if len(tf3_trend) > 1 else True

    # TF4: close vs slow MA
    tf4_bull = bool(close_arr[t] > slow_ma[t]) if not np.isnan(slow_ma[t]) else True
    tf4_bear = bool(close_arr[t] < slow_ma[t]) if not np.isnan(slow_ma[t]) else False

    # TF5: close vs trend MA
    tf5_bull = bool(close_arr[t] > trend_ma[t]) if not np.isnan(trend_ma[t]) else True
    tf5_bear = bool(close_arr[t] < trend_ma[t]) if not np.isnan(trend_ma[t]) else False

    # Build forming bitmask
    f_forming = 0
    if tf1_bull:          f_forming |= (1 << 0)
    if tf2_bull_forming:  f_forming |= (1 << 1)
    if tf3_bull_forming:  f_forming |= (1 << 2)
    if tf4_bull:          f_forming |= (1 << 3)
    if tf5_bull:          f_forming |= (1 << 4)
    if tf4_bear:          f_forming |= (1 << 11)
    if tf5_bear:          f_forming |= (1 << 12)

    # Build resolved bitmask
    f_resolved = 0
    if tf1_bull:           f_resolved |= (1 << 0)
    if tf2_bull_resolved:  f_resolved |= (1 << 1)
    if tf3_bull_resolved:  f_resolved |= (1 << 2)
    if tf4_bull:           f_resolved |= (1 << 3)
    if tf5_bull:           f_resolved |= (1 << 4)
    if tf4_bear:           f_resolved |= (1 << 11)
    if tf5_bear:           f_resolved |= (1 << 12)

    return f_forming, f_resolved


# ---------------------------------------------------------------------------
# Cancel TF helper
# ---------------------------------------------------------------------------
def _check_cancel_tf(
    state: SymbolState,
    entry_mask: int,
    f_forming: int,
    f_resolved: int,
    df: pd.DataFrame,
    t: int,
) -> bool:
    """
    Helper compartido entre ramas TF y MR del brain_engine.
    Verifica si los filtros HTF (TF2/TF3) que estaban activos al
    entrar han cambiado.

    Semántica:
    - Mismo bloque HTF que entry: compara
      state.entry_filters_forming (snapshot-at-entry) vs
      f_forming[t] (forming actual del bar).
    - Bloque HTF cruzado: compara state.entry_filters_forming
      vs f_resolved[t] (resolved del último bloque HTF cerrado
      observable desde t).

    Fiel al kernel Numba (lab_historico_numba_v8_3.py l.1550-1580
    para TF, mean_reversion_kernel.py l.315-345 para MR) que
    implementa el mismo patrón snapshot-vs-current.

    Ver §0.6 CONTEXTO_PROYECTO_TRADING.md sobre Kernel como verdad
    operacional: el "Fix fidelidad" del kernel TF l.1560-1562
    (resolved[t] vs resolved[entry_bar]) está replicado fielmente
    en este helper.
    """
    cancel = False

    # TF2 check (4h)
    if (entry_mask >> 1) & 1:
        ts_now = df['timestamp'].iloc[t]
        ts_entry = pd.Timestamp(state.entry_bar_timestamp, unit='ms', tz='UTC') if state.entry_bar_timestamp > 0 else ts_now

        if hasattr(ts_now, 'timestamp'):
            now_4h = int(ts_now.timestamp()) // (3600 * 4)
            entry_4h = int(ts_entry.timestamp()) // (3600 * 4)
        else:
            now_4h = 0
            entry_4h = 0

        if entry_4h == now_4h:
            # Same 4h block: compare forming
            if ((state.entry_filters_forming >> 1) & 1) != ((f_forming >> 1) & 1):
                cancel = True
        else:
            # Different 4h block: compare resolved
            if ((state.entry_filters_forming >> 1) & 1) != ((f_resolved >> 1) & 1):
                cancel = True

    # TF3 check (1d)
    if not cancel and (entry_mask >> 2) & 1:
        ts_now = df['timestamp'].iloc[t]
        ts_entry = pd.Timestamp(state.entry_bar_timestamp, unit='ms', tz='UTC') if state.entry_bar_timestamp > 0 else ts_now

        if hasattr(ts_now, 'timestamp'):
            now_day = int(ts_now.timestamp()) // 86400
            entry_day = int(ts_entry.timestamp()) // 86400
        else:
            now_day = 0
            entry_day = 0

        if entry_day == now_day:
            if ((state.entry_filters_forming >> 2) & 1) != ((f_forming >> 2) & 1):
                cancel = True
        else:
            if ((state.entry_filters_forming >> 2) & 1) != ((f_resolved >> 2) & 1):
                cancel = True

    return cancel


# ===========================================================================
# Mean-Reversion Mode
# ===========================================================================

# ---------------------------------------------------------------------------
# MR: decode config bits (17-bit layout from mean_reversion_kernel.py)
# ---------------------------------------------------------------------------
def decode_mr_config_bits(config_id: int) -> dict:
    """Decode 17-bit MR config_id into parameter dict."""
    return {
        'exit_mask': config_id & 0xF,
        'entry_mask': (config_id >> 4) & 0x1F,
        'div_entry_mode': (config_id >> 9) & 0x3,
        'div_exit': (config_id >> 11) & 0x1,
        'div_type': (config_id >> 12) & 0x3,
        'cancel_zona': (config_id >> 14) & 0x1,
        'cancel_tf': (config_id >> 15) & 0x1,
        'cancel_ghost': (config_id >> 16) & 0x1,
    }


# ---------------------------------------------------------------------------
# MR: slow line (HA daily forming/resolved) and fast line (Tenkan 9)
# ---------------------------------------------------------------------------
def _calc_slow_line_forming_mr(df_1h):
    """
    Slow line forming: HA diaria repintable (parcial para dia actual).
    Replica calc_slow_line_forming de mean_reversion_features.py.
    Retorna array completo alineado a barras 1h.
    """
    n = len(df_1h)
    result = np.full(n, np.nan)

    timestamps = pd.to_datetime(df_1h['timestamp'])
    # Strip timezone for resampling compatibility
    if timestamps.dt.tz is not None:
        timestamps_naive = timestamps.dt.tz_localize(None)
    else:
        timestamps_naive = timestamps

    o = df_1h['open'].values.astype(np.float64)
    h = df_1h['high'].values.astype(np.float64)
    l = df_1h['low'].values.astype(np.float64)
    c = df_1h['close'].values.astype(np.float64)

    # Pre-compute resolved daily HA for base state per day
    df_indexed = df_1h[['open', 'high', 'low', 'close']].copy()
    df_indexed.index = timestamps_naive
    df_daily = df_indexed.resample('1D', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
    }).dropna()

    ha_daily = calc_heikin_ashi(df_daily)
    ha_open_d = ha_daily['open'].values
    ha_close_d = ha_daily['close'].values
    daily_ts = ha_daily.index.values.astype('datetime64[D]')
    date_to_idx = {daily_ts[k]: k for k in range(len(daily_ts))}

    bar_days = timestamps_naive.values.astype('datetime64[D]')

    current_day = None
    day_o = day_h = day_l = 0.0
    prev_ha_open = np.nan
    prev_ha_close = np.nan

    for i in range(n):
        bd = bar_days[i]

        if bd != current_day:
            if current_day is not None and current_day in date_to_idx:
                didx = date_to_idx[current_day]
                prev_ha_open = ha_open_d[didx]
                prev_ha_close = ha_close_d[didx]
            current_day = bd
            day_o = o[i]
            day_h = h[i]
            day_l = l[i]
        else:
            if h[i] > day_h:
                day_h = h[i]
            if l[i] < day_l:
                day_l = l[i]

        day_c = c[i]

        fha_close = (day_o + day_h + day_l + day_c) / 4.0
        if np.isnan(prev_ha_open):
            fha_open = (day_o + day_c) / 2.0
        else:
            fha_open = (prev_ha_open + prev_ha_close) / 2.0

        fha_high = max(day_h, fha_open, fha_close)
        fha_low = min(day_l, fha_open, fha_close)
        result[i] = (fha_high + fha_low + fha_close) / 3.0

    return result


def _calc_slow_line_resolved_mr(df_1h):
    """
    Slow line resolved: HA diaria hlc3, solo dias cerrados, ffill a 1h.
    Replica calc_slow_line_resolved de mean_reversion_features.py.
    """
    timestamps = pd.to_datetime(df_1h['timestamp'])
    if timestamps.dt.tz is not None:
        timestamps_naive = timestamps.dt.tz_localize(None)
    else:
        timestamps_naive = timestamps

    df_indexed = df_1h[['open', 'high', 'low', 'close']].copy()
    df_indexed.index = timestamps_naive
    df_daily = df_indexed.resample('1D', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
    }).dropna()

    ha = calc_heikin_ashi(df_daily)
    hlc3 = (ha['high'] + ha['low'] + ha['close']) / 3

    resolved = hlc3.shift(1).reindex(df_indexed.index).ffill().values
    return resolved


def _calc_fast_line_mr(df_1h, tenkan_len=9):
    """Fast line: Tenkan-sen (highest(high,9) + lowest(low,9)) / 2 on 1h bars."""
    h_series = pd.Series(df_1h['high'].values, dtype=np.float64)
    l_series = pd.Series(df_1h['low'].values, dtype=np.float64)
    highest = h_series.rolling(window=tenkan_len, min_periods=tenkan_len).max()
    lowest = l_series.rolling(window=tenkan_len, min_periods=tenkan_len).min()
    return ((highest + lowest) / 2.0).values


# ---------------------------------------------------------------------------
# MR: TF filters (TF1-TF3 only, HA-based, no MAs)
# ---------------------------------------------------------------------------
def _compute_filters_mr(df):
    """
    Compute TF1-TF3 forming/resolved filters for mean-reversion.
    Only HA-based filters (no MA filters TF4/TF5).
    Returns (f_forming, f_resolved) as uint32 with bits 0-2.
    """
    df_ts = df.copy()
    if 'timestamp' in df_ts.columns:
        if not isinstance(df_ts['timestamp'].iloc[0], pd.Timestamp):
            df_ts['timestamp'] = pd.to_datetime(df_ts['timestamp'], utc=True)

    # TF1: HA trend 1h
    tf1_bull = bool(calc_ha_trend(df_ts).iloc[-1]) if len(df_ts) > 1 else True

    # TF2: HA trend 4h (forming + resolved)
    df_4h = resample_to_timeframe(df_ts, "4h")
    tf2_trend = calc_ha_trend(df_4h)
    tf2_forming = bool(tf2_trend.iloc[-1]) if len(tf2_trend) > 0 else True
    tf2_resolved = bool(tf2_trend.iloc[-2]) if len(tf2_trend) > 1 else True

    # TF3: HA trend 1D (forming + resolved)
    df_1d = resample_to_timeframe(df_ts, "1d")
    tf3_trend = calc_ha_trend(df_1d)
    tf3_forming = bool(tf3_trend.iloc[-1]) if len(tf3_trend) > 0 else True
    tf3_resolved = bool(tf3_trend.iloc[-2]) if len(tf3_trend) > 1 else True

    f_forming = 0
    if tf1_bull:     f_forming |= (1 << 0)
    if tf2_forming:  f_forming |= (1 << 1)
    if tf3_forming:  f_forming |= (1 << 2)

    f_resolved = 0
    if tf1_bull:      f_resolved |= (1 << 0)
    if tf2_resolved:  f_resolved |= (1 << 1)
    if tf3_resolved:  f_resolved |= (1 << 2)

    return f_forming, f_resolved


# ---------------------------------------------------------------------------
# MR: divergences (with hidden div correction)
# ---------------------------------------------------------------------------
def _compute_div_current_bar_mr(df, mr_bits):
    """
    Compute divergences for current bar using MR semantics.
    Applies hidden div bug fix (swap bits 1 and 3) before evaluation.
    Returns (div_bull_now, div_bear_now).
    """
    div_type = mr_bits['div_type']
    if div_type == 0:
        return False, False

    close_s = df['close']
    high_s = df['high']
    low_s = df['low']
    volume_s = df['volume']

    rsi = calc_rsi(close_s, DIV_RSI_LEN).values
    macd_line, macd_hist = calc_macd(close_s, DIV_MACD_FAST, DIV_MACD_SLOW, DIV_MACD_SIGNAL)
    stoch = calc_stochastic(high_s, low_s, close_s, DIV_STOCH_K, DIV_STOCH_D, DIV_STOCH_SMOOTH).values
    vwmacd = calc_vwmacd(close_s, volume_s, DIV_VWMACD_FAST, DIV_VWMACD_SLOW).values
    cmf = calc_cmf(high_s, low_s, close_s, volume_s, DIV_CMF_LEN).values
    cci = calc_cci(high_s, low_s, close_s, DIV_CCI_LEN).values
    mom = calc_momentum(close_s, DIV_MOM_LEN).values

    indicators = {
        'rsi': rsi, 'macd_hist': macd_hist.values, 'macd_line': macd_line.values,
        'stoch': stoch, 'vwmacd': vwmacd, 'cmf': cmf, 'cci': cci, 'mom': mom,
    }

    close_arr = df['close'].values.astype(np.float64)
    high_arr = df['high'].values.astype(np.float64)
    low_arr = df['low'].values.astype(np.float64)
    n = len(close_arr)

    div_bits_arr = precalculate_divergences_pine_faithful(
        close_arr, high_arr, low_arr, indicators,
        n, DIV_PIVOT_PERIOD, DIV_MAX_PIVOTS, DIV_MAX_BARS
    )

    # Apply hidden div correction (swap bits 1 and 3) — same as mean_reversion_features.py
    bit1 = (div_bits_arr >> 1) & np.uint8(1)
    bit3 = (div_bits_arr >> 3) & np.uint8(1)
    div_bits_arr = (
        (div_bits_arr & np.uint8(0x05))
        | (bit3 << 1).astype(np.uint8)
        | (bit1 << 3).astype(np.uint8)
    )

    # Evaluate at last bar (RSI only = mask 1, default for MR)
    t = n - 1
    div_ind_mask = 1
    net_div_score = 0

    for ind in range(8):
        if not (div_ind_mask & (1 << ind)):
            continue
        bits = int(div_bits_arr[t, ind])
        ind_bull = False
        ind_bear = False

        if div_type == 1:  # Regular only
            ind_bull = (bits & 1) > 0
            ind_bear = (bits & 4) > 0
        elif div_type == 2:  # Hidden (corrected)
            ind_bull = (bits & 2) > 0
            ind_bear = (bits & 8) > 0
        elif div_type == 3:  # Both
            ind_bull = (bits & 1) > 0 or (bits & 2) > 0
            ind_bear = (bits & 4) > 0 or (bits & 8) > 0

        if ind_bull:
            net_div_score += 1
        if ind_bear:
            net_div_score -= 1

    return net_div_score >= 1, net_div_score <= -1


# ---------------------------------------------------------------------------
# MR: cancel helpers
# ---------------------------------------------------------------------------
def _find_bar_by_timestamp(df, timestamp_ms):
    """Find bar positional index matching timestamp_ms. Returns None if not found."""
    if timestamp_ms <= 0:
        return None
    target = pd.Timestamp(timestamp_ms, unit='ms', tz='UTC')
    ts_col = df['timestamp']
    # Ensure comparable
    if not isinstance(ts_col.iloc[0], pd.Timestamp):
        return None
    diffs = (ts_col - target).abs()
    min_pos = int(diffs.values.argmin())
    if diffs.iloc[min_pos] <= pd.Timedelta(hours=1):
        return min_pos
    return None


def _check_cancel_zona_mr(state, df, fast_line, slow_forming, slow_resolved, t):
    """Cancel zona MR: detecta si la zona de entry fue invalidada.

    Dos modos según si el día entry sigue abierto (repintable) o cerrado:
      - Same day (entry_day == current_day): compara zona_bull/bear MR en
        el bar actual `t` usando `slow_forming` (HA daily smoothed
        repintable). Si la dirección de posición NO coincide con la zona
        actual → cancel.
      - Day closed (entry_day < current_day): compara zona_bull/bear MR en
        el entry_bar usando `slow_resolved` (HA daily smoothed cerrada).
        Si la zona resolved del día entry contradice la dirección
        original → cancel.

    Fidelidad a `mean_reversion_kernel.py` cancel_zona logic. Semántica MR
    invertida via `zone_bull_mr` / `zone_bear_mr` (§0.5): zone_bull = fast
    < slow (precio bajo la media → reversion al alza esperada).

    Docstring preciso A05 S1 (2026-04-23) reemplaza versión previa que
    decía "forming zone at entry repainted" — descripción conceptual pero
    imprecisa. La implementación NO compara "forming en entry_bar" sino
    "zona actual (same-day)" o "resolved en entry_bar (day-closed)".

    Args:
        state: SymbolState del símbolo.
        df: DataFrame 1h con columna 'timestamp'.
        fast_line: array Tenkan 1h.
        slow_forming: array HA daily smoothed forming (repintable).
        slow_resolved: array HA daily smoothed resolved (cerrada).
        t: índice del bar actual.

    Returns:
        bool: True si cancel zona activo, False otherwise.
    """
    ts_now = df['timestamp'].iloc[t]
    ts_entry = pd.Timestamp(state.entry_bar_timestamp, unit='ms', tz='UTC') if state.entry_bar_timestamp > 0 else ts_now

    now_day = ts_now.normalize()
    entry_day = ts_entry.normalize()

    if entry_day == now_day:
        # Same day: check if forming zone still matches entry direction
        ft = fast_line[t]
        sf = slow_forming[t]
        if np.isnan(ft) or np.isnan(sf):
            return False
        if state.position == 1 and not zone_bull_mr(ft, sf):
            return True
        if state.position == -1 and not zone_bear_mr(ft, sf):
            return True
    else:
        # Day closed: check resolved zone at entry bar
        entry_idx = _find_bar_by_timestamp(df, state.entry_bar_timestamp)
        if entry_idx is not None and entry_idx < len(slow_resolved):
            ft = fast_line[entry_idx]
            sr = slow_resolved[entry_idx]
            if np.isnan(ft) or np.isnan(sr):
                return False
            if state.position == 1 and not zone_bull_mr(ft, sr):
                return True
            if state.position == -1 and not zone_bear_mr(ft, sr):
                return True

    return False


def _check_cancel_ghost_mr(state, df, fast_line, slow_forming, slow_resolved, t):
    """
    Cancel ghost: zone invalidated and recovered during trajectory from entry to now.
    Faithful to mean_reversion_kernel.py cancel_ghost logic.
    """
    entry_idx = _find_bar_by_timestamp(df, state.entry_bar_timestamp)
    if entry_idx is None:
        return False

    entry_was_bull = state.mr_entry_zone_bull
    ts_now = df['timestamp'].iloc[t]
    current_day = ts_now.normalize()

    for traj_bar in range(entry_idx + 1, t):
        traj_day = df['timestamp'].iloc[traj_bar].normalize()

        if traj_day == current_day:
            # Today: use current forming slow line (repaintable)
            fl = fast_line[traj_bar]
            sf = slow_forming[t]  # current bar's forming value
            if np.isnan(fl) or np.isnan(sf):
                continue
            traj_zone_bull = zone_bull_mr(fl, sf)
        else:
            # Closed day: use resolved
            fl = fast_line[traj_bar]
            sr = slow_resolved[traj_bar]
            if np.isnan(fl) or np.isnan(sr):
                continue
            traj_zone_bull = zone_bull_mr(fl, sr)

        if entry_was_bull and not traj_zone_bull:
            return True
        if not entry_was_bull and traj_zone_bull:
            return True

    return False


# ---------------------------------------------------------------------------
# MR: main signal evaluation
# ---------------------------------------------------------------------------
def _evaluate_bar_mr(brain: BrainState, symbol: str, df: pd.DataFrame, cfg: dict) -> dict:
    """
    Evaluate current bar for a mean-reversion cluster.
    Faithful to mean_reversion_kernel.py bar loop logic.
    """
    state = brain.get_state(symbol)
    # v2.3.7 (fix S2): incrementar contador de barras con posicion abierta.
    # Consumido por audit_fidelity/analyzer via engine_state.json (_save_state).
    # Reset a 0 en los 6 puntos de entry/exit mas abajo.
    if state.position != 0:
        state.bars_since_entry += 1
    mr_bits = cfg['mr_bits']

    close_arr = df['close'].values.astype(np.float64)
    high_arr = df['high'].values.astype(np.float64)
    low_arr = df['low'].values.astype(np.float64)
    n = len(close_arr)
    t = n - 1

    # --- Compute MR arrays ---
    slow_forming = _calc_slow_line_forming_mr(df)
    slow_resolved = _calc_slow_line_resolved_mr(df)
    fast_line = _calc_fast_line_mr(df)

    # --- Zone (INVERTED for mean-reversion) ---
    fast_t = fast_line[t]
    slow_f_t = slow_forming[t]
    z_bull = False
    z_bear = False
    if not (np.isnan(fast_t) or np.isnan(slow_f_t)):
        z_bull = bool(fast_t < slow_f_t)  # INVERTED
        z_bear = bool(fast_t > slow_f_t)

    # Previous zone for div_ctx resets
    prev_z_bull = state.prev_zone_bull

    # --- TF filters (TF1-TF3 only) ---
    f_forming, f_resolved = _compute_filters_mr(df)

    # --- Divergences ---
    div_bull_now, div_bear_now = _compute_div_current_bar_mr(df, mr_bits)

    # --- Pine-faithful div_ctx management ---
    prev_div_bull = state.prev_div_bull_now
    prev_div_bear = state.prev_div_bear_now

    # Zone change resets
    zone_changed_to_bear = z_bear and prev_z_bull
    zone_changed_to_bull = z_bull and not prev_z_bull
    if zone_changed_to_bear:
        state.div_ctx_bull = False
    if zone_changed_to_bull:
        state.div_ctx_bear = False

    # Update div_ctx with prev bar's div
    if prev_div_bull:
        state.div_ctx_bull = True
        state.div_ctx_bear = False
    if prev_div_bear:
        state.div_ctx_bear = True
        state.div_ctx_bull = False

    # Snapshot for entry evaluation
    entry_div_ctx_bull = state.div_ctx_bull
    entry_div_ctx_bear = state.div_ctx_bear

    # Update with current bar's div (for future bars)
    if div_bull_now:
        state.div_ctx_bull = True
    if div_bear_now:
        state.div_ctx_bear = True

    # --- Extract config bits ---
    exit_mask = mr_bits['exit_mask']
    entry_mask = mr_bits['entry_mask']
    div_entry_mode = mr_bits['div_entry_mode']
    div_exit = mr_bits['div_exit']
    div_type = mr_bits['div_type']
    cancel_zona = mr_bits['cancel_zona']
    cancel_tf_bit = mr_bits['cancel_tf']
    cancel_ghost = mr_bits['cancel_ghost']

    close_p = close_arr[t]
    high_p = high_arr[t]
    low_p = low_arr[t]

    signal = {
        'action': 'HOLD' if state.position != 0 else 'FLAT',
        'reason': '',
        'entry_price': close_p,
        'sl_price': state.sl_level,
        'use_ts': False,
        'confidence': float(state.cluster_probs[state.current_cluster]) if state.cluster_probs is not None else 0.0,
        'operable': True,
    }

    # =================================================================
    # EXIT LOGIC (position != 0)
    # =================================================================
    if state.position != 0:
        exit_signal = False
        sl_exit_signal = False
        sl_emergency_signal = False
        div_exit_signal = False
        cancel_signal = False
        exit_price = close_p

        # 1. Trailing stop update
        if t > 0:
            if state.position == 1:
                potential_stop = low_arr[t - 1] * (1 - TS_PERCENT / 100)
                if potential_stop > state.sl_level:
                    state.sl_level = potential_stop
            elif state.position == -1:
                potential_stop = high_arr[t - 1] * (1 + TS_PERCENT / 100)
                if state.sl_level == 0.0 or potential_stop < state.sl_level:
                    state.sl_level = potential_stop
            signal['sl_price'] = state.sl_level

        # 2. Emergency SL
        if state.position == 1:
            emerg = state.entry_price * (1 - SL_EMERGENCY_PERCENT / 100)
            if low_p <= emerg:
                exit_signal = True
                sl_exit_signal = True
                sl_emergency_signal = True
                exit_price = emerg
        elif state.position == -1:
            emerg = state.entry_price * (1 + SL_EMERGENCY_PERCENT / 100)
            if high_p >= emerg:
                exit_signal = True
                sl_exit_signal = True
                sl_emergency_signal = True
                exit_price = emerg

        # 3. Fixed SL
        if not exit_signal:
            if state.position == 1 and close_p < state.sl_level:
                exit_signal = True
                sl_exit_signal = True
            elif state.position == -1 and close_p > state.sl_level:
                exit_signal = True
                sl_exit_signal = True

        # 4. Div exit
        if not exit_signal and div_exit and div_type > 0:
            if state.position == 1 and div_bear_now:
                exit_signal = True
                div_exit_signal = True
            elif state.position == -1 and div_bull_now:
                exit_signal = True
                div_exit_signal = True

        # 5. TF exit (exit_mask)
        if not exit_signal and exit_mask > 0:
            exit_count_active = 0
            exit_count_bull = 0
            for bit in range(4):
                if (exit_mask >> bit) & 1:
                    exit_count_active += 1
                    if (f_forming >> bit) & 1:
                        exit_count_bull += 1
            if exit_count_active > 0:
                if state.position == 1 and exit_count_bull == 0:
                    exit_signal = True
                elif state.position == -1 and exit_count_bull == exit_count_active:
                    exit_signal = True

        # 6. Zone exit (inverted)
        if not exit_signal:
            if state.position == 1 and z_bear:
                exit_signal = True
            elif state.position == -1 and z_bull:
                exit_signal = True

        # 7. Cancel checks (only if no regular exit)
        if not exit_signal:
            if cancel_zona and not cancel_signal:
                cancel_signal = _check_cancel_zona_mr(
                    state, df, fast_line, slow_forming, slow_resolved, t
                )
            if cancel_tf_bit and not cancel_signal:
                cancel_signal = _check_cancel_tf(
                    state, entry_mask, f_forming, f_resolved, df, t
                )
            if cancel_ghost and not cancel_signal:
                cancel_signal = _check_cancel_ghost_mr(
                    state, df, fast_line, slow_forming, slow_resolved, t
                )

        # Process exit/cancel
        if exit_signal or cancel_signal:
            action = 'CLOSE_LONG' if state.position == 1 else 'CLOSE_SHORT'

            if sl_emergency_signal:
                reason = 'sl_emergency'
            elif sl_exit_signal:
                reason = 'sl_hit'
            elif div_exit_signal:
                reason = 'div_exit'
            elif cancel_signal:
                reason = 'cancel_mr'
            else:
                reason = 'zone_exit_mr' if (
                    (state.position == 1 and z_bear) or (state.position == -1 and z_bull)
                ) else 'tf_exit'

            signal = {
                'action': action,
                'reason': reason,
                'entry_price': exit_price,
                'sl_price': 0.0,
                'use_ts': False,
                'confidence': signal['confidence'],
                'operable': True,
            }

            if sl_emergency_signal or cancel_signal:
                state.cooldown_until = 0
            elif sl_exit_signal or div_exit_signal:
                state.cooldown_until = COOLDOWN_BARS
            else:
                state.cooldown_until = 0

            # v2.3.9 (fix B1): reset completo (incluye campos antes stale).
            _reset_state_on_exit(state, mr=True)

            if action == 'CLOSE_LONG':
                state.div_ctx_bull = False
            else:
                state.div_ctx_bear = False

    # Zone-based div_ctx cleanup (every bar)
    if z_bear:
        state.div_ctx_bull = False
    if z_bull:
        state.div_ctx_bear = False

    # =================================================================
    # ENTRY LOGIC (position == 0)
    # =================================================================
    if state.position == 0:
        if state.cooldown_until > 0:
            state.cooldown_until -= 1
        else:
            entry_tf_count = bin(entry_mask & 0x7).count('1')  # bits 0-2 only for MR
            exit_tf_count = bin(exit_mask & 0x7).count('1')

            tf_entry_ok_bull = True
            tf_entry_ok_bear = True

            for bit in range(3):  # MR uses TF1-TF3 only
                if (entry_mask >> bit) & 1:
                    if not ((f_forming >> bit) & 1):
                        tf_entry_ok_bull = False
                    if (f_forming >> bit) & 1:
                        tf_entry_ok_bear = False

            effective_ctx_bull = entry_div_ctx_bull or prev_div_bull
            effective_ctx_bear = entry_div_ctx_bear or prev_div_bear

            long_cond = False
            short_cond = False

            if div_entry_mode == 0:  # OFF
                if z_bull:
                    long_cond = tf_entry_ok_bull if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = tf_entry_ok_bear if entry_tf_count > 0 else True

            elif div_entry_mode == 1:  # AND
                if z_bull:
                    if entry_tf_count > 0:
                        long_cond = tf_entry_ok_bull and effective_ctx_bull
                    elif exit_tf_count > 0:
                        long_cond = effective_ctx_bull
                    else:
                        long_cond = prev_div_bull
                if z_bear:
                    if entry_tf_count > 0:
                        short_cond = tf_entry_ok_bear and effective_ctx_bear
                    elif exit_tf_count > 0:
                        short_cond = effective_ctx_bear
                    else:
                        short_cond = prev_div_bear

            elif div_entry_mode == 2:  # OR
                if z_bull:
                    long_cond = (tf_entry_ok_bull or prev_div_bull) if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = (tf_entry_ok_bear or prev_div_bear) if entry_tf_count > 0 else True

            # Exit filter conflict check
            if long_cond and exit_mask > 0:
                ec = sum(1 for bit in range(4) if (exit_mask >> bit) & 1 and (f_forming >> bit) & 1)
                if ec == 0:
                    long_cond = False

            if short_cond and exit_mask > 0:
                ec_bull = 0
                ec_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        ec_active += 1
                        if (f_forming >> bit) & 1:
                            ec_bull += 1
                if ec_active > 0 and ec_bull == ec_active:
                    short_cond = False

            # Execute entry
            if long_cond:
                state.position = 1
                state.entry_price = close_p
                state.sl_level = low_p * (1 - SL_PERCENT / 100)
                state.entry_filters_forming = f_forming
                state.entry_bar_timestamp = int(df['timestamp'].iloc[t].timestamp() * 1000) if hasattr(df['timestamp'].iloc[t], 'timestamp') else 0
                state.bars_since_entry = 0
                state.mr_entry_zone_bull = True
                state.mr_entry_filters_forming = f_forming
                state.mr_entry_slow_line = float(slow_forming[t])
                state.mr_zone_history = [True]
                signal = {
                    'action': 'LONG',
                    'reason': 'mr_entry',
                    'entry_price': close_p,
                    'sl_price': state.sl_level,
                    'use_ts': False,
                    'confidence': signal['confidence'],
                    'operable': True,
                }
            elif short_cond:
                state.position = -1
                state.entry_price = close_p
                state.sl_level = high_p * (1 + SL_PERCENT / 100)
                state.entry_filters_forming = f_forming
                state.entry_bar_timestamp = int(df['timestamp'].iloc[t].timestamp() * 1000) if hasattr(df['timestamp'].iloc[t], 'timestamp') else 0
                state.bars_since_entry = 0
                state.mr_entry_zone_bull = False
                state.mr_entry_filters_forming = f_forming
                state.mr_entry_slow_line = float(slow_forming[t])
                state.mr_zone_history = [False]
                signal = {
                    'action': 'SHORT',
                    'reason': 'mr_entry',
                    'entry_price': close_p,
                    'sl_price': state.sl_level,
                    'use_ts': False,
                    'confidence': signal['confidence'],
                    'operable': True,
                }

    # Update persistent state
    state.prev_zone_bull = z_bull
    state.prev_zone_bear = z_bear
    state.prev_div_bull_now = div_bull_now
    state.prev_div_bear_now = div_bear_now

    # Track zone history for cancel_ghost
    if state.position != 0:
        state.mr_zone_history.append(z_bull)

    return signal


# ---------------------------------------------------------------------------
# Orquestador: run_cycle (conveniencia para live_engine)
# ---------------------------------------------------------------------------
def run_cycle(brain: BrainState, market_data: dict) -> dict:
    """
    Ejecuta un ciclo completo: classify -> btc_override -> select_configs -> generate_signals.

    Returns:
        {'BTC/USDT': {signal_dict}, ...}
    """
    t0 = time.perf_counter()

    # Normalizar columnas (parquet usa timestamp_ms, data_feed usa timestamp)
    market_data = {sym: _normalize_ohlcv(df) for sym, df in market_data.items()}

    regimes = classify_regimes(brain, market_data)
    regimes = apply_btc_override(brain, regimes)
    active_configs = select_active_configs(brain, regimes)
    signals = generate_signals(brain, market_data, active_configs)

    elapsed = time.perf_counter() - t0
    actions = {s: sig['action'] for s, sig in signals.items() if sig['action'] not in ('FLAT', 'HOLD')}
    logger.info(f"Ciclo brain completado en {elapsed:.2f}s — {len(actions)} señales activas: {actions}")

    return signals


# ---------------------------------------------------------------------------
# CLI / Tests
# ---------------------------------------------------------------------------
def _run_quick_test(symbol: str = 'BTC/USDT'):
    """Test rápido con datos de data_cache."""
    import asyncio
    print("=" * 60)
    print("BRAIN ENGINE — Test rápido")
    print("=" * 60)

    # Intentar cargar datos locales
    sym_key = symbol.replace("/USDT", "").replace("/", "")
    cache_path = os.path.join(_project_root, "data_cache", f"{sym_key}USDT_1h.parquet")
    if not os.path.exists(cache_path):
        print(f"  No se encontró {cache_path}")
        print(f"  Intentando descargar de BingX...")
        from live.data_feed import download_all_ohlcv
        data = asyncio.run(download_all_ohlcv([symbol], limit=500))
        df = data.get(symbol)
    else:
        df = pd.read_parquet(cache_path)
        df = _normalize_ohlcv(df)
        # Usar las últimas 500 barras
        df = df.tail(500).reset_index(drop=True)

    if df is None or len(df) == 0:
        print("  Sin datos. Abortando.")
        return

    print(f"\n[1] Cargando modelos...")
    brain = load_models(
        regime_models_dir=os.path.join(_project_root, "regime_models"),
        specialist_configs_dir=os.path.join(_project_root, "regime_wf"),
        symbols=[symbol],
    )

    print(f"\n[2] Ejecutando ciclo para {symbol} ({len(df)} barras)...")
    signals = run_cycle(brain, {symbol: df})

    print(f"\n[3] Resultado:")
    for sym, sig in signals.items():
        print(f"    {sym}: {sig['action']} ({sig['reason']})")
        if sig['action'] in ('LONG', 'SHORT'):
            print(f"      Entry: {sig['entry_price']:.2f}, SL: {sig['sl_price']:.2f}, TS: {sig['use_ts']}")
        print(f"      Confidence: {sig['confidence']:.4f}, Operable: {sig['operable']}")

    state = brain.get_state(symbol)
    print(f"\n    State: cluster={state.current_cluster}, position={state.position}")


def _load_preset_tuple(symbol: str, preset_label: str):
    """
    Reconstruye el tuple de 12 elementos del preset desde presets CSV o parse_preset.

    Returns:
        (preset_tuple_12, hyst_mult)  o  (None, None) si no se puede resolver.
    """
    sym_clean = symbol.replace("/", "")
    csv_path = os.path.join(_project_root, "output", "production", f"presets_{sym_clean}.csv")

    # Parsear label para extraer fast/slow type+period y hyst
    fast_type, fast_period, slow_type, slow_period, trend_type, trend_period, hyst_mult = parse_preset(preset_label)

    if os.path.exists(csv_path):
        try:
            df_presets = pd.read_csv(csv_path)
            match = df_presets[
                (df_presets['fast_type'] == fast_type) &
                (df_presets['fast_period'] == fast_period) &
                (df_presets['slow_type'] == slow_type) &
                (df_presets['slow_period'] == slow_period)
            ]
            if len(match) > 0:
                row = match.iloc[0]
                preset_tuple = (
                    str(row['fast_type']), int(row['fast_period']),
                    float(row['fast_p1']), float(row['fast_p2']),
                    str(row['slow_type']), int(row['slow_period']),
                    float(row['slow_p1']), float(row['slow_p2']),
                    str(row['trend_type']), int(row['trend_period']),
                    float(row['trend_p1']), float(row['trend_p2']),
                )
                return preset_tuple, hyst_mult
        except Exception as e:
            logger.warning(f"Error leyendo presets CSV: {e}")

    # Fallback: construir con p1=0, p2=0 (usará defaults de calc_ma)
    logger.warning(f"Usando preset sin p1/p2 (defaults) — presets CSV no encontrado")
    preset_tuple = (
        fast_type, fast_period, 0.0, 0.0,
        slow_type, slow_period, 0.0, 0.0,
        trend_type, trend_period, 0.0, 0.0,
    )
    return preset_tuple, hyst_mult


_VERIFY_LEVEL_B_THRESHOLD = 2000
_VERIFY_TOLERANCE_PNL_A_PP = 0.1
_VERIFY_TOLERANCE_PNL_B_PCT = 15.0
_VERIFY_TOLERANCE_PNL_B_FLOOR_PP = 0.1


def _run_verify_test(symbol: str = 'BTC/USDT', n_bars: int = 1000, data_path: str = None) -> int:
    """Test de fidelidad brain↔kernel sobre N barras del símbolo (§0.8 protocolo).

    N<2000 → Nivel A (benchmark rápido, gate obligatorio todo deploy).
              Tolerance PnL 0.1pp absoluto; trades exacto.
    N≥2000 → Nivel B (deep smoke, gate cambios brain/kernel/data_feed).
              Tolerance PnL 15% relativo con floor 0.1pp (drift arquitectónico
              baseline 7-9% documentado §12 L30); trades max(1, 0.5% N_trades).

    Args:
        symbol: símbolo a testear.
        n_bars: número de bars a procesar. Default 1000 (Nivel A baseline §0.8).
        data_path: parquet path override (default data_cache productivo).
                   Permite cargar data alternativa (ej. Binance Futures
                   histórico) sin modificar data_cache/{SYMBOL}USDT_1h.parquet
                   productivo. Tier 0 I2 Bloque 2c 2026-04-23.

    Returns:
        Exit code 0 si PASS, 1 si FAIL o datos insuficientes.
    """
    if n_bars < 1:
        raise ValueError(f"n_bars debe ser >= 1 (recibido {n_bars})")

    level = "B" if n_bars >= _VERIFY_LEVEL_B_THRESHOLD else "A"

    print("=" * 60)
    print(f"BRAIN ENGINE — Test de fidelidad vs kernel Numba [NIVEL {level}]")
    print("=" * 60)

    if data_path:
        cache_path = data_path
        print(f"  Data source: CUSTOM {cache_path}")
    else:
        sym_key = symbol.replace("/USDT", "").replace("/", "")
        cache_path = os.path.join(_project_root, "data_cache", f"{sym_key}USDT_1h.parquet")
    if not os.path.exists(cache_path):
        print(f"  No se encontro {cache_path}. Necesitas datos en data_cache/ o pasar --data-path.")
        return 1

    df_full = pd.read_parquet(cache_path)
    df_full = _normalize_ohlcv(df_full)

    print(f"  Datos: {len(df_full)} barras totales (solicitado n_bars={n_bars})")

    # Cargar modelos
    brain = load_models(
        regime_models_dir=os.path.join(_project_root, "regime_models"),
        specialist_configs_dir=os.path.join(_project_root, "regime_wf"),
        symbols=[symbol],
    )

    cfg_data = brain.specialist_configs.get(symbol)
    if not cfg_data:
        print(f"  Sin specialist_configs para {symbol}.")
        return 1

    # Usar cluster 0 o el primer cluster con configs
    test_cluster = None
    for k_str, cdata in cfg_data.get('clusters', {}).items():
        if cdata.get('top_configs'):
            test_cluster = int(k_str)
            break

    if test_cluster is None:
        print("  Sin configs disponibles.")
        return 1

    top_cfg = cfg_data['clusters'][str(test_cluster)]['top_configs'][0]
    config_id = top_cfg['config_id']
    preset_label = top_cfg['preset']
    print(f"  Config: {config_id} ({preset_label}) de cluster {test_cluster}")

    # Tomar las últimas n_bars barras (acotado por len del parquet)
    n_test = min(n_bars, len(df_full))
    if n_test < n_bars:
        print(f"  WARN: parquet solo tiene {len(df_full)} bars, procesando N={n_test} (solicitado {n_bars})")
    df_test = df_full.tail(n_test).reset_index(drop=True)
    print(f"  Simulando {n_test} barras (nivel efectivo: {'B' if n_test >= _VERIFY_LEVEL_B_THRESHOLD else 'A'})")

    # =====================================================================
    # PARTE 1: Brain engine barra a barra
    # =====================================================================
    print(f"\n  [1/2] Brain engine barra a barra...")
    bits = decode_config_bits(config_id)
    trades_brain = []
    state = brain.get_state(symbol)
    state.current_cluster = test_cluster
    state.cluster_probs = np.ones(cfg_data['n_clusters']) / cfg_data['n_clusters']
    state.cluster_probs[test_cluster] = 0.9

    warmup = 500
    for i in range(warmup, n_test):
        window = df_test.iloc[max(0, i - warmup + 1):i + 1].reset_index(drop=True)

        cfg = {
            'config_id': config_id,
            'preset': preset_label,
            'preset_tuple': brain.preset_tuples.get(preset_label),
            'config_bits': bits,
            'cluster': test_cluster,
            'operable': True,
            'regime_changed': False,
        }

        try:
            sig = _evaluate_bar(brain, symbol, window, cfg)
            if sig['action'] in ('LONG', 'SHORT', 'CLOSE_LONG', 'CLOSE_SHORT'):
                trades_brain.append({
                    'bar': i,
                    'action': sig['action'],
                    'price': sig['entry_price'],
                    'reason': sig['reason'],
                })
        except Exception as e:
            logger.error(f"Bar {i}: {e}")

    # Calcular PnL de brain_engine trades
    brain_pnl = 0.0
    brain_trades_count = 0
    brain_wins = 0
    brain_gross_profit = 0.0
    brain_gross_loss = 0.0
    i = 0
    while i < len(trades_brain) - 1:
        entry = trades_brain[i]
        exit_t = trades_brain[i + 1]
        if entry['action'] in ('LONG', 'SHORT') and exit_t['action'] in ('CLOSE_LONG', 'CLOSE_SHORT'):
            if entry['action'] == 'LONG':
                pnl_pct = (exit_t['price'] - entry['price']) / entry['price'] * 100
            else:
                pnl_pct = (entry['price'] - exit_t['price']) / entry['price'] * 100
            pnl_net = pnl_pct - COMMISSION_ROUND_TRIP
            brain_pnl += pnl_net
            brain_trades_count += 1
            if pnl_net > 0:
                brain_wins += 1
                brain_gross_profit += pnl_net
            else:
                brain_gross_loss += abs(pnl_net)
            i += 2
        else:
            i += 1

    print(f"    Senales: {len(trades_brain)}")
    print(f"    Trades completos: {brain_trades_count}")
    print(f"    PnL neto: {brain_pnl:.4f}%")
    print(f"    Wins: {brain_wins}, Losses: {brain_trades_count - brain_wins}")
    print(f"    Gross profit: {brain_gross_profit:.4f}%, Gross loss: {brain_gross_loss:.4f}%")
    for t in trades_brain[:20]:
        print(f"      Bar {t['bar']}: {t['action']} @ {t['price']:.2f} ({t['reason']})")
    if len(trades_brain) > 20:
        print(f"      ... y {len(trades_brain) - 20} mas")

    # =====================================================================
    # PARTE 2: Kernel Numba via run_on_slice
    # =====================================================================
    print(f"\n  [2/2] Kernel Numba (run_on_slice)...")

    preset_tuple = brain.preset_tuples.get(preset_label)
    if preset_tuple is None:
        # Fallback a CSV directo
        preset_tuple, _ = _load_preset_tuple(symbol, preset_label)
    if preset_tuple is None:
        print("    ERROR: No se pudo resolver el preset tuple.")
        return 1
    _, _, _, _, _, _, _, _, _, _, _, _ = preset_tuple  # validate 12-tuple
    hyst_match = re.search(r'_H(\d+)$', preset_label)
    hyst_mult = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0

    print(f"    Preset tuple: {preset_tuple}")
    print(f"    Hyst mult: {hyst_mult}")

    try:
        from lab_historico_numba_v8_3 import precalculate_all_data, run_on_slice
    except ImportError as e:
        print(f"    ERROR importando lab_historico: {e}")
        return 1

    # precalculate_all_data espera df con columna 'timestamp'
    data = precalculate_all_data(df_test, preset=preset_tuple, hyst_mult=hyst_mult, symbol=symbol)

    configs = np.array([config_id], dtype=np.uint32)
    # El kernel opera sobre el rango [start_bar, end_bar) con warmup interno
    # Para comparar con brain_engine (que empieza en bar warmup), usamos:
    #   start_bar = warmup, end_bar = n_test
    #   warmup del kernel = 100 (bars antes de start_bar para construir estado)
    results, cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl = run_on_slice(
        configs, data,
        start_bar=warmup,
        end_bar=n_test,
        sl_pct=SL_PERCENT,
        sl_emergency_pct=SL_EMERGENCY_PERCENT,
        ts_pct=TS_PERCENT,
        cooldown_bars=COOLDOWN_BARS,
        commission_pct=COMMISSION_ROUND_TRIP,
        warmup=100,
    )

    kernel_pnl = results[0, 0]
    kernel_trades = int(results[0, 1])
    kernel_wins = int(results[0, 2])
    kernel_cancels = int(results[0, 3])
    kernel_maxdd = results[0, 4]
    kernel_gp = results[0, 5]
    kernel_gl = results[0, 6]

    print(f"    Trades: {kernel_trades}")
    print(f"    PnL neto: {kernel_pnl:.4f}%")
    print(f"    Wins: {kernel_wins}, Losses: {kernel_trades - kernel_wins}")
    print(f"    Cancels: {kernel_cancels}")
    print(f"    MaxDD: {kernel_maxdd:.4f}%")
    print(f"    Gross profit: {kernel_gp:.4f}%, Gross loss: {kernel_gl:.4f}%")

    # =====================================================================
    # PARTE 3: Comparacion (tolerance escalada según nivel §0.8)
    # =====================================================================
    effective_level = "B" if n_test >= _VERIFY_LEVEL_B_THRESHOLD else "A"
    print(f"\n  {'='*60}")
    print(f"  COMPARACION DE FIDELIDAD [NIVEL {effective_level}]")
    print(f"  {'='*60}")

    pnl_diff_abs = abs(brain_pnl - kernel_pnl)
    pnl_diff_rel_pct = pnl_diff_abs / max(abs(kernel_pnl), 0.01) * 100
    trade_diff_abs = brain_trades_count - kernel_trades

    if effective_level == "A":
        pnl_tolerance_desc = f"{_VERIFY_TOLERANCE_PNL_A_PP}pp absoluto"
        pnl_close = pnl_diff_abs < _VERIFY_TOLERANCE_PNL_A_PP
        trade_tolerance_max = 0
        trade_tolerance_desc = "exacto"
    else:
        pnl_tolerance_desc = f"{_VERIFY_TOLERANCE_PNL_B_PCT} pct relativo (floor {_VERIFY_TOLERANCE_PNL_B_FLOOR_PP}pp)"
        pnl_close = (pnl_diff_abs < _VERIFY_TOLERANCE_PNL_B_FLOOR_PP) or (pnl_diff_rel_pct < _VERIFY_TOLERANCE_PNL_B_PCT)
        # Nivel B trades: criterio §0.8 "match count brain<->kernel > 95 pct" = 5 pct divergence permitida
        trade_tolerance_max = max(1, int(0.05 * max(brain_trades_count, kernel_trades)))
        trade_tolerance_desc = f"max(1, 5 pct N)=+/-{trade_tolerance_max} (match >=95 pct §0.8)"
    trades_match = abs(trade_diff_abs) <= trade_tolerance_max
    match_pct = (min(brain_trades_count, kernel_trades) / max(brain_trades_count, kernel_trades, 1)) * 100

    print(f"  Tolerance PnL:     {pnl_tolerance_desc}")
    print(f"  Tolerance trades:  {trade_tolerance_desc}")
    print(f"  {'Metrica':<25} {'Brain':>12} {'Kernel':>12} {'Diff':>12} {'OK?':>5}")
    print(f"  {'-'*66}")
    print(f"  {'Trades':<25} {brain_trades_count:>12} {kernel_trades:>12} {trade_diff_abs:>12} {'YES' if trades_match else 'NO':>5}")
    print(f"  {'Wins':<25} {brain_wins:>12} {kernel_wins:>12} {brain_wins - kernel_wins:>12} {'YES' if brain_wins == kernel_wins else 'NO':>5}")
    print(f"  {'PnL neto %':<25} {brain_pnl:>12.4f} {kernel_pnl:>12.4f} {brain_pnl - kernel_pnl:>12.4f} {'YES' if pnl_close else 'NO':>5}")
    if effective_level == "B":
        print(f"  {'PnL diff relativo':<25} {'':>12} {'':>12} {pnl_diff_rel_pct:>11.2f}{'pct':>3}")
        print(f"  {'Match count trades':<25} {'':>12} {'':>12} {match_pct:>11.2f}{'pct':>3}")
    print(f"  {'Gross profit %':<25} {brain_gross_profit:>12.4f} {kernel_gp:>12.4f} {brain_gross_profit - kernel_gp:>12.4f}")
    print(f"  {'Gross loss %':<25} {brain_gross_loss:>12.4f} {kernel_gl:>12.4f} {brain_gross_loss - kernel_gl:>12.4f}")

    passed = trades_match and pnl_close
    if passed:
        print(f"\n  RESULTADO: FIDELIDAD CONFIRMADA [NIVEL {effective_level} PASS]")
        return 0
    else:
        print(f"\n  RESULTADO: DIVERGENCIA DETECTADA [NIVEL {effective_level} FAIL]")
        if not trades_match:
            print(f"    Trades diff={trade_diff_abs} (tolerance ±{trade_tolerance_max})")
        if not pnl_close:
            print(f"    PnL diff_abs={pnl_diff_abs:.4f}pp  diff_rel={pnl_diff_rel_pct:.2f}%  (tolerance: {pnl_tolerance_desc})")
        return 1


def _run_classify(symbol: str = 'BTC/USDT'):
    """Clasifica régimen actual de un símbolo."""
    import asyncio
    print(f"Clasificando régimen de {symbol}...")

    brain = load_models(
        regime_models_dir=os.path.join(_project_root, "regime_models"),
        specialist_configs_dir=os.path.join(_project_root, "regime_wf"),
        symbols=[symbol],
    )

    # Intentar datos locales primero
    sym_key = symbol.replace("/USDT", "").replace("/", "")
    cache_path = os.path.join(_project_root, "data_cache", f"{sym_key}USDT_1h.parquet")
    if os.path.exists(cache_path):
        df = pd.read_parquet(cache_path)
        df = _normalize_ohlcv(df)
        df = df.tail(1100).reset_index(drop=True)
    else:
        from live.data_feed import download_all_ohlcv
        data = asyncio.run(download_all_ohlcv([symbol], limit=500))
        df = data.get(symbol)

    if df is None:
        print("Sin datos.")
        return

    regimes = classify_regimes(brain, {symbol: df})
    r = regimes.get(symbol, {})
    print(f"\n  Cluster: {r.get('cluster')} ({r.get('cluster_name')})")
    print(f"  Probs: {r.get('probs')}")
    print(f"  Confidence: {r.get('confidence', 0):.4f}")
    print(f"  Operable: {r.get('operable')}")

    # Show active config (TF or MR)
    active_configs = select_active_configs(brain, regimes)
    ac = active_configs.get(symbol, {})
    if ac.get('strategy_type') == 'mean_reversion':
        mr_bits = ac.get('mr_bits', {})
        tf_names = ["TF1", "TF2", "TF3"]
        entry_tfs = "+".join(tf_names[b] for b in range(3) if (mr_bits.get('entry_mask', 0) >> b) & 1) or "-"
        exit_tfs = "+".join(tf_names[b] for b in range(3) if (mr_bits.get('exit_mask', 0) >> b) & 1) or "ZONA"
        div_mode = ["OFF", "AND", "OR"][mr_bits.get('div_entry_mode', 0)]
        div_type = ["NONE", "REGULAR", "HIDDEN", "BOTH"][mr_bits.get('div_type', 0)]
        cancels = []
        if mr_bits.get('cancel_zona'): cancels.append("ZONA")
        if mr_bits.get('cancel_tf'): cancels.append("TF")
        if mr_bits.get('cancel_ghost'): cancels.append("GHOST")
        print(f"\n  Strategy: MEAN-REVERSION")
        print(f"  Config ID: {ac.get('config_id')}")
        print(f"  Entry: {entry_tfs} | Exit: {exit_tfs}")
        print(f"  Div: {div_type}/{div_mode} | Cancel: {'+'.join(cancels) if cancels else 'OFF'}")
    else:
        print(f"\n  Strategy: TREND-FOLLOWING")
        print(f"  Config ID: {ac.get('config_id')} ({ac.get('preset')})")

    # Run signal generation
    signals = generate_signals(brain, {symbol: df}, active_configs)
    sig = signals.get(symbol, {})
    print(f"\n  Signal: {sig.get('action')} ({sig.get('reason')})")
    if sig.get('action') in ('LONG', 'SHORT'):
        print(f"    Entry: {sig.get('entry_price', 0):.6f}, SL: {sig.get('sl_price', 0):.6f}")

    if symbol in brain.gmm_models:
        model = brain.gmm_models[symbol]
        print(f"\n  Centroides ({model['feature_names']}):")
        for i, row in enumerate(model['centroids']):
            names = model['cluster_names']
            name = names[i] if i < len(names) else f'C{i}'
            print(f"    C{i} ({name}): {[f'{v:.3f}' for v in row]}")


def main():
    parser = argparse.ArgumentParser(description="Brain Engine — Signal Generation")
    parser.add_argument("--verify", action="store_true", help="Test de fidelidad vs kernel Numba")
    parser.add_argument("--classify", type=str, default=None, help="Clasificar régimen de un símbolo")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Símbolo para tests")
    parser.add_argument(
        "--n-bars",
        type=int,
        default=1000,
        help="Bars a procesar en --verify. Menor que 2000: Nivel A benchmark rapido. "
             "Mayor o igual que 2000: Nivel B deep smoke (drift baseline 7-9 pct esperable). Default 1000.",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Parquet path override para --verify (default data_cache productivo). "
             "Uso: cargar data alternativa (ej. Binance Futures histórico) sin "
             "modificar parquet productivo. Tier 0 I2 Bloque 2c.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.verify:
        exit_code = _run_verify_test(args.symbol, n_bars=args.n_bars, data_path=args.data_path)
        sys.exit(exit_code if exit_code is not None else 0)
    elif args.classify:
        _run_classify(args.classify)
    else:
        _run_quick_test(args.symbol)


if __name__ == "__main__":
    main()
