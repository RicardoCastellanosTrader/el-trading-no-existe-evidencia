#!/usr/bin/env python3
"""
audit_fidelity_v5.py -- Auditoria de fidelidad v5 (post-v2.3.2)

Evolucion de audit_fidelity_v4.py con:
  1. Ventana temporal desde el despliegue de v2.3.2 (default 2026-04-16T17:00:00Z).
  2. Criterios de exclusion formalizados:
       - excluido_ruido_cross_exchange (|diff BingX-Binance| > 0.3% en barra entrada)
       - excluido_reconstruido (flag=='reconstructed_post_hoc' en CSV o reason_exit 'orphan_close')
       - excluido_dd_breaker (dd_multiplier < 1.0 en el [ENGINE_STATE] del ciclo)
       - excluido_reconcile_intervino (linea [BRAIN_RECONCILE] para el simbolo en el ciclo)
       - excluido_mr_kernel_no_implementado (trades MR, kernel MR pendiente)
  3. Wilson 95% CI para match rate (scipy.stats.binomtest).
  4. Veredicto automatico con umbrales (88/80/70%).
  5. Analisis detallado caso a caso de no-match (5 hipotesis).
  6. Reporte .txt en 5 secciones: audit_v5_report_YYYYMMDD_HHMM.txt.

Kernel stateless: IDENTICO a v4 (extract_trades_tf + regime transitions).
Datos OHLCV: BingX (ejecucion real) con Binance solo para diff cross-exchange.

Ejecutar:
  cd c:\\Users\\rixip\\comboclaude
  set PYTHONIOENCODING=utf-8
  python audit_fidelity_v5.py --since 2026-04-16T17:00:00Z

Opciones:
  --since YYYY-MM-DDTHH:MM:SSZ    Inicio de la ventana (default 2026-04-16T17:00:00Z)
  --until YYYY-MM-DDTHH:MM:SSZ    Fin (default: ultimo trade en CSV)
  --log-start-date YYYY-MM-DD     Fecha del primer timestamp en engine.log
  --engine-log PATH               engine.log path (default: engine.log o vps_engine_latest.log)
  --trade-csv PATH                trade_history.csv path
  --dry-run                       No descarga BingX/Binance, solo ejercita parsing/reporte
  --skip-binance                  Saltar diff cross-exchange (acepta Exclusion 1 como 0)
  --min-n 30                      N minimo para veredicto robusto
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timezone
from pathlib import Path

# M6: scipy version check
try:
    import scipy
    _MIN_SCIPY = (1, 7, 0)
    _scipy_ver = tuple(int(x) for x in scipy.__version__.split('.')[:3])
    if _scipy_ver < _MIN_SCIPY:
        raise ImportError(
            f"audit_fidelity_v5 requires scipy >= {'.'.join(map(str, _MIN_SCIPY))}, "
            f"found {scipy.__version__}"
        )
except ImportError as _e:
    print(f"[SCIPY] {_e}", file=sys.stderr)

# C6: COMBOLAB_DIR via CLI > env > default relative (resolucion final en run())
_DEFAULT_COMBOLAB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'combolab'
)
COMBOLAB_DIR = os.environ.get('COMBOLAB_DIR', _DEFAULT_COMBOLAB)
if COMBOLAB_DIR not in sys.path:
    sys.path.insert(0, COMBOLAB_DIR)

# lab_historico_numba_v8_3 y regime_features se importan lazy despues de
# resolver COMBOLAB_DIR (ver _lazy_import_combolab_modules() en run_audit).
lab = None
compute_regime_features = None


def _lazy_import_combolab_modules():
    """Importa modulos del combolab despues de resolver COMBOLAB_DIR.
    Permite que --combolab-dir tenga efecto completo, no solo sobre paths."""
    global lab, compute_regime_features
    if COMBOLAB_DIR not in sys.path:
        sys.path.insert(0, COMBOLAB_DIR)
    import lab_historico_numba_v8_3 as _lab
    import regime_features as _rf
    lab = _lab
    compute_regime_features = _rf.compute_regime_features
    return lab, compute_regime_features

# ---------------------------------------------------------------------------
# Constantes del kernel (mismas que lab y live)
# ---------------------------------------------------------------------------
SL_PCT = 3.0
SL_EMERGENCY_PCT = 5.0
TS_PCT = 0.5
COOLDOWN_BARS = 1
COMMISSION_PCT = 0.10

WARMUP_BARS = 200
N_DOWNLOAD = 2000
# C8: tolerancia en horas (= 1 vela 1h). Antes era 2 (inconsistente con docstring "±1 vela")
ENTRY_CANDLE_TOLERANCE = 1
EXIT_CANDLE_TOLERANCE = 1

# C2: Kernel parity checksum (opcion C del triaje).
# Lab solo tiene Numba run_simulation_numba (sin python puro); el audit
# reimplementa la semantica en python estatico. Para detectar drift:
# - Audit hash: fija el codigo actual de extract_trades_tf. Si alguien
#   modifica el kernel del audit, hash difiere -> forzar revision explicita.
# - Lab hash: fija la firma del Numba run_simulation_numba. Si el lab
#   cambia, el audit podria quedar desalineado -> warning.
# Flujo para actualizar: tras cambio intencional y revision de parity,
# recomputar hash con `python -c "import hashlib,inspect; import ..."`
# y actualizar constante.
EXPECTED_AUDIT_KERNEL_HASH = "a93310e41213967bfe57bc7e94942178589ac2802a3a071f786eb5a7d3ba4167"
EXPECTED_LAB_KERNEL_HASH = "165b235786306a1d2753274f09b91968aaacf44d90bc272613cf8d39b4b5028a"

# Umbrales v5
CROSS_EXCHANGE_DIFF_PCT_THRESHOLD = 0.3
CROSS_EXCHANGE_HYPOTHESIS_PCT = 0.1
VERDICT_GREEN_RATE = 0.88
VERDICT_GREEN_CI_LOW = 0.80
VERDICT_AMBER_RATE = 0.80
VERDICT_AMBER_CI_LOW = 0.70
MIN_N_FOR_ROBUST_VERDICT = 30

# Default deploy timestamp v2.3.2 (16 abril 2026, ~17:00 UTC)
DEFAULT_SINCE_ISO = "2026-04-16T17:00:00Z"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRADE_CSV = os.path.join(THIS_DIR, "trade_history.csv")
DEFAULT_ENGINE_LOG_CANDIDATES = [
    os.path.join(THIS_DIR, "engine.log"),
    os.path.join(THIS_DIR, "vps_engine_latest.log"),
]

def _resolve_combolab_paths():
    return (
        os.path.join(COMBOLAB_DIR, "regime_models"),
        os.path.join(COMBOLAB_DIR, "regime_wf"),
        os.path.join(COMBOLAB_DIR, "output", "production"),
    )

REGIME_MODELS_DIR, SPECIALIST_CONFIGS_DIR, PRESETS_DIR = _resolve_combolab_paths()


# ============================================================================
# 1. CARGA DE TRADES REALES (VPS)
# ============================================================================

# v2.3.3+ anade entry_timestamp_ms como columna 12
CSV_COLUMNS = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
               'size_usdt', 'pnl_pct', 'pnl_usdt', 'funding_paid',
               'reason_exit', 'flag', 'entry_timestamp_ms']
CSV_N_COLS = len(CSV_COLUMNS)


def load_vps_trades(csv_path, since_ts, until_ts):
    """Carga trade_history.csv, normaliza timestamps y filtra por ventana.

    Tolerante a 10/11/12 columnas:
      v2.3.1-: 10 columnas (sin flag)
      v2.3.2 : 11 columnas (anade flag)
      v2.3.3+: 12 columnas (anade entry_timestamp_ms)

    cycle_ts = exit cycle (floor('h') del timestamp de cierre).
    entry_candle se infiere en infer_entry_candle() por trade (C1 fix).
    """
    rows = []
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        _header_line = f.readline().rstrip('\n')  # header, ignorado (parseo posicional)
        for line in f:
            parts = line.rstrip('\n').split(',')
            while len(parts) < CSV_N_COLS:
                parts.append('')
            rows.append(parts[:CSV_N_COLS])
    df = pd.DataFrame(rows, columns=CSV_COLUMNS)

    for col in ('entry_price', 'exit_price', 'size_usdt', 'pnl_pct',
                'pnl_usdt', 'funding_paid', 'entry_timestamp_ms'):
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['timestamp']).reset_index(drop=True)

    df['cycle_ts'] = df['timestamp'].dt.floor('h')

    mask = df['timestamp'] >= since_ts
    if until_ts is not None:
        mask &= df['timestamp'] <= until_ts
    filtered = df[mask].reset_index(drop=True)

    return filtered, df


def infer_entry_candle(vps_row, log_events):
    """C1 fix. Devuelve (entry_candle_ts | None, source_str).

    Prioridad:
      1. entry_timestamp_ms del CSV (v2.3.3+) -> floor('h') UTC.
      2. Log: ultimo [SIGNALS_EXECUTED] con a='LONG'|'SHORT' del mismo
         simbolo antes (estrictamente) del cycle_ts (exit cycle).
      3. None -> entry_not_inferrable. Trade excluido del match.
    """
    ets = vps_row.get('entry_timestamp_ms')
    if ets is not None and not (isinstance(ets, float) and pd.isna(ets)) and ets > 0:
        try:
            return (pd.Timestamp(int(ets), unit='ms', tz='UTC').floor('h'), 'csv')
        except (TypeError, ValueError, OverflowError):
            pass

    sym = vps_row['symbol']
    exit_cycle = vps_row['cycle_ts']

    candidates = []
    for (cycle_ts, s), info in log_events.get('signals_executed', {}).items():
        if s != sym:
            continue
        if cycle_ts >= exit_cycle:
            continue
        a = (info or {}).get('a', '')
        if a in ('LONG', 'SHORT'):
            candidates.append(cycle_ts)
    if candidates:
        return (max(candidates), 'log')

    return (None, 'none')


# ============================================================================
# 2. PARSER DE ENGINE LOG (ENGINE_STATE, BRAIN_RECONCILE, SIGNALS_EXECUTED)
# ============================================================================

LOG_TS_RE = re.compile(r'^(\d{2}):(\d{2}):(\d{2})\s')
ENGINE_STATE_RE = re.compile(r'\[ENGINE_STATE\]\s+(\{.+\})')
SIGNALS_RAW_RE = re.compile(r'\[SIGNALS_RAW\]\s+(\{.+\})')
SIGNALS_DISCARDED_RE = re.compile(r'\[SIGNALS_DISCARDED\]\s+(\{.+\})')
SIGNALS_EXECUTED_RE = re.compile(r'\[SIGNALS_EXECUTED\]\s+(\{.+\})')
BRAIN_RECONCILE_RE = re.compile(r'\[BRAIN_RECONCILE\]\s+(\S+)')
ORPHAN_CLOSE_RE = re.compile(r'\[ORPHAN_CLOSE\]\s+(\S+)')


def parse_engine_log(log_path, log_start_date):
    """Parsea engine.log y devuelve eventos por ciclo horario.

    C5 fix: usa [ENGINE_STATE].t (unix seconds, v2.3.1+) como ancla de fecha.
    Si hay gaps (bot caido multi-hora), la siguiente [ENGINE_STATE] re-sincroniza.
    Fallback rollover 23->00 solo para lineas sin anchor disponible.

    Returns dict con:
      engine_states: {cycle_ts_utc: {bal, peak, dd_pct, dd_mult, cb_active, n_open, t}}
      brain_reconciles: {(cycle_ts_utc, symbol): True}
      orphan_closes: {(cycle_ts_utc, symbol): True}
      signals_executed: {(cycle_ts_utc, symbol): {sz, lv, bf, br, dd, a}}
      signals_raw: {(cycle_ts_utc, symbol): {a, r, p, sl, c, s, k, t}}
    """
    result = {
        'engine_states': {},
        'brain_reconciles': {},
        'orphan_closes': {},
        'signals_executed': {},
        'signals_raw': {},
        'log_start_ts': None,
        'log_end_ts': None,
        'log_date_sync_anchors': 0,
        'log_date_gap_warnings': 0,
    }

    if not log_path or not os.path.exists(log_path):
        return result

    current_date = log_start_date
    last_hour = None

    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = LOG_TS_RE.match(line)
            if not m:
                continue
            hh = int(m.group(1))
            mm = int(m.group(2))
            ss = int(m.group(3))

            # C5: ENGINE_STATE.t como ancla de fecha
            em = ENGINE_STATE_RE.search(line)
            anchor_ts = None
            if em:
                try:
                    es_payload = json.loads(em.group(1))
                    t_unix = es_payload.get('t')
                    if t_unix is not None:
                        anchor_ts = pd.Timestamp(int(t_unix), unit='s', tz='UTC')
                        if anchor_ts.hour == hh:
                            prev_date = current_date
                            current_date = pd.Timestamp(anchor_ts.date())
                            if prev_date != current_date:
                                result['log_date_sync_anchors'] += 1
                        else:
                            current_date = pd.Timestamp(anchor_ts.date())
                            result['log_date_sync_anchors'] += 1
                            hh = anchor_ts.hour
                            mm = anchor_ts.minute
                            ss = anchor_ts.second
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

            if anchor_ts is None:
                if last_hour is not None:
                    if hh == 0 and last_hour == 23:
                        current_date = current_date + pd.Timedelta(days=1)
                    elif hh < last_hour and (last_hour - hh) >= 2:
                        result['log_date_gap_warnings'] += 1
            last_hour = hh

            line_ts = pd.Timestamp(
                year=current_date.year, month=current_date.month, day=current_date.day,
                hour=hh, minute=mm, second=ss, tz='UTC'
            )
            cycle_ts = line_ts.floor('h')

            if result['log_start_ts'] is None:
                result['log_start_ts'] = line_ts
            result['log_end_ts'] = line_ts

            if em:
                try:
                    state = json.loads(em.group(1))
                    result['engine_states'][cycle_ts] = state
                except json.JSONDecodeError:
                    pass
                continue

            # BRAIN_RECONCILE
            bm = BRAIN_RECONCILE_RE.search(line)
            if bm:
                sym = bm.group(1)
                result['brain_reconciles'][(cycle_ts, sym)] = True
                continue

            # ORPHAN_CLOSE
            om = ORPHAN_CLOSE_RE.search(line)
            if om:
                sym = om.group(1)
                result['orphan_closes'][(cycle_ts, sym)] = True
                continue

            # SIGNALS_EXECUTED
            sxm = SIGNALS_EXECUTED_RE.search(line)
            if sxm:
                try:
                    payload = json.loads(sxm.group(1))
                    if isinstance(payload, dict):
                        for sym, info in payload.items():
                            result['signals_executed'][(cycle_ts, sym)] = info
                except json.JSONDecodeError:
                    pass
                continue

            # SIGNALS_RAW
            srm = SIGNALS_RAW_RE.search(line)
            if srm:
                try:
                    payload = json.loads(srm.group(1))
                    if isinstance(payload, dict):
                        for sym, info in payload.items():
                            result['signals_raw'][(cycle_ts, sym)] = info
                except json.JSONDecodeError:
                    pass
                continue

    return result


def find_v232_deploy_ts(log_events, hint_ts=None):
    """Encuentra el primer [ENGINE_STATE] del arranque post-v2.3.2.

    Heuristica: primer ENGINE_STATE >= hint_ts con n_open consistente (>=0).
    Si no hay ENGINE_STATE (log antiguo sin v2.3.1+), devuelve hint_ts.
    """
    if not log_events['engine_states']:
        return hint_ts
    candidates = sorted(log_events['engine_states'].keys())
    if hint_ts is not None:
        candidates = [c for c in candidates if c >= hint_ts - pd.Timedelta(hours=1)]
    if not candidates:
        return hint_ts
    return candidates[0]


# ============================================================================
# 3. EXCHANGE (BingX + Binance Spot para diff cross-exchange)
# ============================================================================

def create_bingx_exchange():
    import ccxt
    ex = ccxt.bingx({'options': {'defaultType': 'swap'}, 'enableRateLimit': True})
    ex.load_markets()
    return ex


def create_binance_exchange():
    """Binance Spot (Futures esta geo-bloqueado, per bug log)."""
    import ccxt
    ex = ccxt.binance({'options': {'defaultType': 'spot'}, 'enableRateLimit': True})
    ex.load_markets()
    return ex


def to_bingx_symbol(symbol):
    return f"{symbol}:USDT"


def _download_ohlcv(symbol, exchange, bingx=True):
    """Descarga N_DOWNLOAD barras 1h de BingX o Binance Spot."""
    sym = symbol.replace("/", "")
    label = "BingX" if bingx else "Binance"
    ex_sym = to_bingx_symbol(symbol) if bingx else symbol
    print(f"  [{sym}] Descargando {N_DOWNLOAD} barras 1h de {label}...")

    all_candles = []
    interval_ms = 3600000
    limit_per_request = 1000
    current_since = int(time.time() * 1000) - (N_DOWNLOAD + 200) * interval_ms

    while len(all_candles) < N_DOWNLOAD + 100:
        try:
            ohlcv = exchange.fetch_ohlcv(ex_sym, '1h', since=current_since,
                                          limit=limit_per_request)
            if not ohlcv:
                break
            all_candles.extend(ohlcv)
            current_since = ohlcv[-1][0] + interval_ms
            time.sleep(0.15)
        except Exception as e:
            print(f"    ERROR descargando {symbol} ({label}): {e}")
            return None

    if len(all_candles) < 100:
        print(f"    ERROR: solo {len(all_candles)} barras {label}")
        return None

    seen = set()
    deduped = []
    for c in all_candles:
        if c[0] not in seen:
            seen.add(c[0])
            deduped.append(c)
    deduped.sort(key=lambda x: x[0])

    df = pd.DataFrame(deduped,
                       columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    if len(df) > N_DOWNLOAD:
        df = df.tail(N_DOWNLOAD).reset_index(drop=True)

    print(f"    {label}: {len(df)} barras: {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")
    return df


def download_bingx(symbol, exchange):
    return _download_ohlcv(symbol, exchange, bingx=True)


def download_binance(symbol, exchange):
    return _download_ohlcv(symbol, exchange, bingx=False)


def cross_exchange_diff_pct(df_bingx, df_binance, target_ts):
    """Calcula |close_BingX - close_Binance| / close_BingX * 100 en barra target_ts."""
    if df_bingx is None or df_binance is None:
        return None
    target_ts = pd.Timestamp(target_ts).tz_convert('UTC')

    bx_mask = df_bingx['timestamp'] == target_ts
    bn_mask = df_binance['timestamp'] == target_ts
    if not bx_mask.any() or not bn_mask.any():
        return None

    bx_close = float(df_bingx.loc[bx_mask, 'close'].iloc[0])
    bn_close = float(df_binance.loc[bn_mask, 'close'].iloc[0])
    if bx_close <= 0:
        return None
    return abs(bx_close - bn_close) / bx_close * 100.0


# ============================================================================
# 4. CLASIFICACION DE REGIMEN (copia verbatim de v4)
# ============================================================================

def classify_bars_gmm(symbol, df):
    sym_key = symbol.replace("/USDT", "").replace("/", "")
    model_path = os.path.join(REGIME_MODELS_DIR, f"{sym_key}_regime.joblib")

    if not os.path.exists(model_path):
        print(f"    WARN: No regime model for {symbol}")
        return None, 1

    model_data = joblib.load(model_path)
    gmm = model_data['gmm']
    scaler = model_data['scaler']
    lookback = model_data.get('lookback', 100)
    n_clusters = model_data['n_clusters']
    cluster_names = model_data.get('cluster_names', [f'C{i}' for i in range(n_clusters)])

    feat_df = pd.DataFrame({
        'close': df['close'].values,
        'high': df['high'].values,
        'low': df['low'].values,
        'open': df['open'].values,
        'volume': df['volume'].values,
    })
    features, valid_mask = compute_regime_features(feat_df, lookback=lookback)

    n_bars = len(df)
    labels = np.full(n_bars, -1, dtype=np.int64)
    valid_features = features[valid_mask]
    if len(valid_features) > 0:
        X = scaler.transform(valid_features)
        pred = gmm.predict(X)
        valid_indices = np.where(valid_mask)[0]
        for i, idx in enumerate(valid_indices):
            labels[idx] = pred[i]

    n_valid = int(np.sum(labels >= 0))
    print(f"    Regime: k={n_clusters}, {n_valid}/{n_bars} barras clasificadas")
    for ci in range(n_clusters):
        name = cluster_names[ci] if ci < len(cluster_names) else f'C{ci}'
        cnt = int(np.sum(labels == ci))
        print(f"      C{ci} ({name}): {cnt} barras")

    return labels, n_clusters


# ============================================================================
# 5. SPECIALIST CONFIGS + PRESETS (copia verbatim de v4)
# ============================================================================

def load_specialist_config(symbol):
    sym_clean = symbol.replace("/", "")
    path = os.path.join(SPECIALIST_CONFIGS_DIR, f"{sym_clean}_specialist_configs.json")
    if not os.path.exists(path):
        print(f"    WARN: No specialist config for {symbol}")
        return None
    with open(path) as f:
        return json.load(f)


def get_cluster_config(specialist_cfg, cluster_id):
    cluster_data = specialist_cfg.get('clusters', {}).get(str(cluster_id))
    if not cluster_data:
        return None

    mr_block = cluster_data.get('mean_reversion')
    if mr_block and mr_block.get('strategy_type') == 'mean_reversion':
        return {
            'config_id': mr_block['config_id'],
            'preset': None,
            'strategy_type': 'mean_reversion',
        }

    top_configs = cluster_data.get('top_configs', [])
    if not top_configs:
        return None

    selected = None
    for cfg in top_configs:
        if cfg.get('cross_cluster_survival', True):
            selected = cfg
            break
    if selected is None:
        selected = top_configs[0]

    if selected.get('sqn_p5', 0) <= 0:
        return None

    return {
        'config_id': selected['config_id'],
        'preset': selected.get('preset', ''),
        'strategy_type': 'trend_following',
    }


def find_preset_in_symbol_presets(symbol, preset_str):
    hyst_match = re.search(r'_H(\d+)$', preset_str)
    hyst = int(hyst_match.group(1)) / 10.0 if hyst_match else 0.0

    core = re.sub(r'_H\d+$', '', preset_str)
    parts = core.split('/')
    if len(parts) != 2:
        return None, hyst

    m1 = re.match(r'(\w+)\((\d+)(?:,[\d.]+)*\)', parts[0])
    m2 = re.match(r'(\w+)\((\d+)(?:,[\d.]+)*\)', parts[1])
    if not m1 or not m2:
        return None, hyst

    fast_type, fast_period = m1.group(1), int(m1.group(2))
    slow_type, slow_period = m2.group(1), int(m2.group(2))

    presets_list = lab.SYMBOL_ZONE_PRESETS.get(symbol, [])
    for preset_tuple in presets_list:
        pt_ft, pt_fp = preset_tuple[0], preset_tuple[1]
        pt_st, pt_sp = preset_tuple[4], preset_tuple[5]
        if pt_ft == fast_type and pt_fp == fast_period and pt_st == slow_type and pt_sp == slow_period:
            return preset_tuple, hyst

    sym_clean = symbol.replace("/", "")
    csv_path = os.path.join(PRESETS_DIR, f"presets_{sym_clean}.csv")
    if os.path.exists(csv_path):
        df_p = pd.read_csv(csv_path)
        for _, row in df_p.iterrows():
            if (str(row['fast_type']) == fast_type and int(row['fast_period']) == fast_period and
                    str(row['slow_type']) == slow_type and int(row['slow_period']) == slow_period):
                return (
                    str(row['fast_type']), int(row['fast_period']),
                    float(row['fast_p1']), float(row['fast_p2']),
                    str(row['slow_type']), int(row['slow_period']),
                    float(row['slow_p1']), float(row['slow_p2']),
                    str(row['trend_type']), int(row['trend_period']),
                    float(row['trend_p1']), float(row['trend_p2']),
                ), hyst

    trend_period = slow_period * 4
    fallback = (fast_type, fast_period, 0.0, 0.0,
                slow_type, slow_period, 0.0, 0.0,
                slow_type, trend_period, 0.0, 0.0)
    print(f"    WARN: preset '{preset_str}' no encontrado, usando fallback")
    return fallback, hyst


# ============================================================================
# 6. DECODE CONFIG BITS (verbatim v4)
# ============================================================================

def decode_tf_config(config_id):
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


# ============================================================================
# 7. KERNEL STATELESS TF (verbatim v4)
# ============================================================================

def extract_trades_tf(data, config_id, cluster_labels, target_cluster,
                      start_bar=0, end_bar=None):
    bits = decode_tf_config(config_id)
    exit_mask = bits['exit_mask']
    entry_mask = bits['entry_mask']
    div_entry_mode = bits['div_entry_mode']
    div_exit = bits['div_exit']
    div_type = bits['div_type']
    div_ind_mask = bits['div_ind_mask']
    cancel_tf_bit = bits['cancel_tf']
    use_ts = bits['use_ts']
    reg_inv = bits['reg_inv']
    hid_inv = bits['hid_inv']

    close_arr = data['close']
    high_arr = data['high']
    low_arr = data['low']
    timestamps = data['timestamps']
    zone_bull = data['zone_bull']
    zone_bear = data['zone_bear']
    filters_forming = data['filters_forming']
    filters_resolved = data['filters_resolved']
    div_bits = data['div_bits']

    n_bars = len(close_arr) if end_bar is None else end_bar
    if end_bar is None:
        end_bar = n_bars

    ts_i64 = timestamps.astype('datetime64[ms]').astype(np.int64)

    entry_tf_count = bin(entry_mask).count('1')
    exit_tf_count = bin(exit_mask & 0xF).count('1')

    position = 0
    entry_price = 0.0
    entry_bar = 0
    entry_filters_forming = 0
    sl_level = 0.0
    cooldown_until = 0

    div_ctx_bull = False
    div_ctx_bear = False
    last_zone_bull = False
    prev_div_bull_now = False
    prev_div_bear_now = False
    div_bull_now_saved = False
    div_bear_now_saved = False

    trades = []
    acct_start = start_bar

    for t in range(1, end_bar):
        z_bull = bool(zone_bull[t])
        z_bear = bool(zone_bear[t])
        f_forming = int(filters_forming[t])
        f_resolved = int(filters_resolved[t])
        close_p = float(close_arr[t])
        high_p = float(high_arr[t])
        low_p = float(low_arr[t])

        prev_div_bull_now = div_bull_now_saved
        prev_div_bear_now = div_bear_now_saved

        zone_changed_to_bear = z_bear and last_zone_bull
        zone_changed_to_bull = z_bull and not last_zone_bull

        if zone_changed_to_bear:
            div_ctx_bull = False
        if zone_changed_to_bull:
            div_ctx_bear = False

        if prev_div_bull_now:
            div_ctx_bull = True
            div_ctx_bear = False
        if prev_div_bear_now:
            div_ctx_bear = True
            div_ctx_bull = False

        entry_div_ctx_bull = div_ctx_bull
        entry_div_ctx_bear = div_ctx_bear

        last_zone_bull = z_bull

        div_bull_now = False
        div_bear_now = False
        if div_type > 0 and div_ind_mask > 0:
            net_div_score = 0
            for ind in range(8):
                if not (div_ind_mask & (1 << ind)):
                    continue
                b = int(div_bits[t, ind])
                ind_bull = False
                ind_bear = False
                if div_type == 1:
                    if reg_inv == 0:
                        ind_bull = (b & 1) > 0
                        ind_bear = (b & 4) > 0
                    else:
                        ind_bull = (b & 4) > 0
                        ind_bear = (b & 1) > 0
                elif div_type == 2:
                    if hid_inv == 0:
                        ind_bull = (b & 8) > 0
                        ind_bear = (b & 2) > 0
                    else:
                        ind_bull = (b & 2) > 0
                        ind_bear = (b & 8) > 0
                elif div_type == 3:
                    if reg_inv == 0:
                        reg_bull = (b & 1) > 0
                        reg_bear = (b & 4) > 0
                    else:
                        reg_bull = (b & 4) > 0
                        reg_bear = (b & 1) > 0
                    if hid_inv == 0:
                        h_bull = (b & 8) > 0
                        h_bear = (b & 2) > 0
                    else:
                        h_bull = (b & 2) > 0
                        h_bear = (b & 8) > 0
                    ind_bull = reg_bull or h_bull
                    ind_bear = reg_bear or h_bear
                if ind_bull:
                    net_div_score += 1
                if ind_bear:
                    net_div_score -= 1
            div_bull_now = net_div_score >= 1
            div_bear_now = net_div_score <= -1

        div_bull_now_saved = div_bull_now
        div_bear_now_saved = div_bear_now

        if div_bull_now:
            div_ctx_bull = True
        if div_bear_now:
            div_ctx_bear = True

        # EXITS
        if position != 0 and t >= acct_start:
            exit_signal = False
            cancel_signal = False
            div_exit_signal = False
            sl_exit_signal = False
            sl_emergency_signal = False
            exit_price = close_p
            exit_reason = ""

            if use_ts == 1 and t > entry_bar:
                if position == 1:
                    pot = low_arr[t - 1] * (1.0 - TS_PCT / 100.0)
                    if pot > sl_level:
                        sl_level = pot
                elif position == -1:
                    pot = high_arr[t - 1] * (1.0 + TS_PCT / 100.0)
                    if sl_level == 0.0 or pot < sl_level:
                        sl_level = pot

            if position == 1:
                emerg = entry_price * (1.0 - SL_EMERGENCY_PCT / 100.0)
                if low_p <= emerg:
                    exit_signal = True
                    sl_exit_signal = True
                    sl_emergency_signal = True
                    exit_price = emerg
                    exit_reason = "sl_emergency"
            elif position == -1:
                emerg = entry_price * (1.0 + SL_EMERGENCY_PCT / 100.0)
                if high_p >= emerg:
                    exit_signal = True
                    sl_exit_signal = True
                    sl_emergency_signal = True
                    exit_price = emerg
                    exit_reason = "sl_emergency"

            if not exit_signal and sl_level > 0:
                if position == 1 and close_p < sl_level:
                    exit_signal = True
                    sl_exit_signal = True
                    exit_reason = "sl_hit"
                elif position == -1 and close_p > sl_level:
                    exit_signal = True
                    sl_exit_signal = True
                    exit_reason = "sl_hit"

            if not exit_signal and div_exit == 1 and div_type > 0:
                if position == 1 and div_bear_now:
                    exit_signal = True
                    div_exit_signal = True
                    exit_reason = "div_exit"
                elif position == -1 and div_bull_now:
                    exit_signal = True
                    div_exit_signal = True
                    exit_reason = "div_exit"

            if not exit_signal and exit_mask > 0:
                ex_bull = 0
                ex_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        ex_active += 1
                        if (f_forming >> bit) & 1:
                            ex_bull += 1
                if position == 1 and ex_active > 0 and ex_bull == 0:
                    exit_signal = True
                    exit_reason = "tf_exit"
                elif position == -1 and ex_active > 0 and ex_bull == ex_active:
                    exit_signal = True
                    exit_reason = "tf_exit"

            if not exit_signal:
                if position == 1 and z_bear:
                    exit_signal = True
                    exit_reason = "zone_exit"
                elif position == -1 and z_bull:
                    exit_signal = True
                    exit_reason = "zone_exit"

            if not exit_signal and cancel_tf_bit == 1:
                ts_entry_i = ts_i64[entry_bar]
                ts_now_i = ts_i64[t]
                entry_day = ts_entry_i // 86400000
                current_day = ts_now_i // 86400000
                same_daily = (entry_day == current_day)

                eff = entry_filters_forming
                f_now = f_forming
                efr = f_resolved

                if (entry_mask >> 1) & 1:
                    entry_4h = (ts_entry_i // 3600000) // 4
                    now_4h = (ts_now_i // 3600000) // 4
                    if entry_4h == now_4h:
                        if ((eff >> 1) & 1) != ((f_now >> 1) & 1):
                            cancel_signal = True
                    else:
                        if ((eff >> 1) & 1) != ((efr >> 1) & 1):
                            cancel_signal = True

                if not cancel_signal and (entry_mask >> 2) & 1:
                    if same_daily:
                        if ((eff >> 2) & 1) != ((f_now >> 2) & 1):
                            cancel_signal = True
                    else:
                        if ((eff >> 2) & 1) != ((efr >> 2) & 1):
                            cancel_signal = True

                if cancel_signal:
                    exit_reason = "cancel_tf"

            if exit_signal or cancel_signal:
                side = "long" if position == 1 else "short"
                if position == 1:
                    trade_pnl = (exit_price - entry_price) / entry_price * 100.0
                else:
                    trade_pnl = (entry_price - exit_price) / entry_price * 100.0
                trade_pnl -= COMMISSION_PCT

                entry_cluster = int(cluster_labels[entry_bar]) if cluster_labels is not None else -1

                trades.append({
                    'entry_bar': entry_bar,
                    'exit_bar': t,
                    'entry_ts': timestamps[entry_bar],
                    'exit_ts': timestamps[t],
                    'side': side,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl_pct': trade_pnl,
                    'reason': exit_reason if not cancel_signal else "cancel_tf",
                    'cluster': entry_cluster,
                })

                if position == 1:
                    div_ctx_bull = False
                else:
                    div_ctx_bear = False

                if sl_emergency_signal:
                    cooldown_until = t
                elif sl_exit_signal:
                    cooldown_until = t + COOLDOWN_BARS - 1
                elif div_exit_signal:
                    cooldown_until = t + COOLDOWN_BARS - 1
                elif cancel_signal:
                    cooldown_until = t

                position = 0
                entry_price = 0.0
                sl_level = 0.0
                entry_filters_forming = 0

        if z_bear:
            div_ctx_bull = False
        if z_bull:
            div_ctx_bear = False

        # ENTRIES
        if position == 0 and t >= acct_start:
            if t <= cooldown_until:
                continue

            if cluster_labels is not None and int(cluster_labels[t]) != target_cluster:
                continue

            long_cond = False
            short_cond = False
            tf_entry_ok_bull = True
            tf_entry_ok_bear = True

            if (entry_mask >> 0) & 1:
                if not ((f_forming >> 0) & 1):
                    tf_entry_ok_bull = False
                if ((f_forming >> 0) & 1):
                    tf_entry_ok_bear = False
            if (entry_mask >> 1) & 1:
                if not ((f_forming >> 1) & 1):
                    tf_entry_ok_bull = False
                if ((f_forming >> 1) & 1):
                    tf_entry_ok_bear = False
            if (entry_mask >> 2) & 1:
                if not ((f_forming >> 2) & 1):
                    tf_entry_ok_bull = False
                if ((f_forming >> 2) & 1):
                    tf_entry_ok_bear = False
            if (entry_mask >> 3) & 1:
                if not ((f_forming >> 3) & 1):
                    tf_entry_ok_bull = False
                if not ((f_forming >> 11) & 1):
                    tf_entry_ok_bear = False
            if (entry_mask >> 4) & 1:
                if not ((f_forming >> 4) & 1):
                    tf_entry_ok_bull = False
                if not ((f_forming >> 12) & 1):
                    tf_entry_ok_bear = False

            effective_ctx_bull = entry_div_ctx_bull or prev_div_bull_now
            effective_ctx_bear = entry_div_ctx_bear or prev_div_bear_now

            if div_entry_mode == 0:
                if z_bull:
                    long_cond = tf_entry_ok_bull if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = tf_entry_ok_bear if entry_tf_count > 0 else True
            elif div_entry_mode == 1:
                if z_bull:
                    if entry_tf_count > 0:
                        long_cond = tf_entry_ok_bull and effective_ctx_bull
                    elif exit_tf_count > 0:
                        long_cond = effective_ctx_bull
                    else:
                        long_cond = prev_div_bull_now
                if z_bear:
                    if entry_tf_count > 0:
                        short_cond = tf_entry_ok_bear and effective_ctx_bear
                    elif exit_tf_count > 0:
                        short_cond = effective_ctx_bear
                    else:
                        short_cond = prev_div_bear_now
            elif div_entry_mode == 2:
                if z_bull:
                    long_cond = (tf_entry_ok_bull or prev_div_bull_now) if entry_tf_count > 0 else True
                if z_bear:
                    short_cond = (tf_entry_ok_bear or prev_div_bear_now) if entry_tf_count > 0 else True

            if long_cond and exit_mask > 0:
                ex_bull = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1 and (f_forming >> bit) & 1:
                        ex_bull += 1
                if ex_bull == 0:
                    long_cond = False

            if short_cond and exit_mask > 0:
                ex_bull = 0
                ex_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        ex_active += 1
                        if (f_forming >> bit) & 1:
                            ex_bull += 1
                if ex_bull == ex_active:
                    short_cond = False

            if long_cond:
                position = 1
                entry_price = close_p
                entry_bar = t
                entry_filters_forming = f_forming
                sl_level = low_p * (1.0 - SL_PCT / 100.0)
            elif short_cond:
                position = -1
                entry_price = close_p
                entry_bar = t
                entry_filters_forming = f_forming
                sl_level = high_p * (1.0 + SL_PCT / 100.0)

    return trades


# ============================================================================
# 8. REGIME TRANSITIONS (verbatim v4)
# ============================================================================

def detect_regime_changes(cluster_labels):
    changes = []
    prev_cluster = -1
    for t in range(len(cluster_labels)):
        cl = int(cluster_labels[t])
        if cl < 0:
            continue
        if prev_cluster >= 0 and cl != prev_cluster:
            changes.append((t, prev_cluster, cl))
        prev_cluster = cl
    return changes


def apply_regime_transitions(kernel_trades, regime_changes, data):
    if not regime_changes:
        return kernel_trades

    result = []
    for trade in kernel_trades:
        entry_bar = trade['entry_bar']
        exit_bar = trade['exit_bar']
        entry_cluster = trade['cluster']

        first_change = None
        for bar_idx, from_cl, to_cl in regime_changes:
            if entry_bar < bar_idx < exit_bar and from_cl == entry_cluster:
                first_change = (bar_idx, from_cl, to_cl)
                break

        if first_change is not None:
            change_bar, from_cl, to_cl = first_change
            truncated = dict(trade)
            truncated['exit_bar'] = change_bar
            truncated['exit_ts'] = data['timestamps'][change_bar]
            truncated['exit_price'] = float(data['close'][change_bar])
            truncated['reason'] = 'regime_change'
            if truncated['side'] == 'long':
                pnl = (truncated['exit_price'] - truncated['entry_price']) / truncated['entry_price'] * 100.0
            else:
                pnl = (truncated['entry_price'] - truncated['exit_price']) / truncated['entry_price'] * 100.0
            truncated['pnl_pct'] = pnl - COMMISSION_PCT
            truncated['regime_change_detail'] = f"C{from_cl}->C{to_cl}"
            result.append(truncated)
        else:
            result.append(trade)

    return result


# ============================================================================
# 9. REASON COMPAT (verbatim v4)
# ============================================================================

def _reason_compatible(vps_reason, kernel_reason):
    """M4 fix: sl_hit y sus variantes (sl_trigger_*, sl_emergency) son equivalentes."""
    vps_r = (vps_reason or '').lower().strip()
    kernel_r = (kernel_reason or '').lower().strip()

    if vps_r == kernel_r:
        return True

    SL_ALIASES = {
        'sl_hit', 'sl_exit', 'sl_emergency',
        'sl_trigger_hit', 'sl_trigger_reconstructed',
        'sl_trigger_orphan_reconstructed', 'sl_trigger_hit_reconstructed',
    }
    if vps_r in SL_ALIASES and kernel_r in SL_ALIASES:
        return True

    aliases = {
        'tf_exit': ['tf_exit', 'normal_exit'],
        'zone_exit': ['zone_exit', 'normal_exit'],
        'div_exit': ['div_exit'],
        'cancel_tf': ['cancel_tf'],
        'regime_change': ['regime_change'],
    }
    vps_group = aliases.get(vps_r, [vps_r])
    return kernel_r in vps_group


# ============================================================================
# 10. EXCLUSIONES (nuevas en v5)
# ============================================================================

EXCL_CROSS = 'excluido_ruido_cross_exchange'
EXCL_RECON = 'excluido_reconstruido'
EXCL_DD = 'excluido_dd_breaker'
EXCL_BRAIN_RC = 'excluido_reconcile_intervino'
EXCL_MR = 'excluido_mr_kernel_no_implementado'

# S4: orden canonico (primer match gana). Actualizar docstring del modulo si cambia.
EXCL_LABELS = {
    EXCL_RECON: 'Trade reconstruido post-hoc (orphan_close / flag reconstructed)',
    EXCL_MR: 'Trade mean-reversion (kernel MR no implementado en auditor)',
    EXCL_DD: 'Ciclo con DD breaker activo (dd_multiplier < 1.0)',
    EXCL_BRAIN_RC: 'Brain reconcile intervino en el ciclo de entrada',
    EXCL_CROSS: 'Ruido cross-exchange BingX/Binance > 0.3%',
}


def is_mr_trade(symbol, cluster_hint, specialist_cfg_cache):
    """Devuelve True si el specialist activo del simbolo/cluster es MR."""
    cfg = specialist_cfg_cache.get(symbol)
    if cfg is None:
        return False
    if cluster_hint is None or cluster_hint < 0:
        clusters = cfg.get('clusters', {})
        for cl_str, cl_data in clusters.items():
            mr = cl_data.get('mean_reversion')
            if mr and mr.get('strategy_type') == 'mean_reversion':
                return True
        return False
    cl_data = cfg.get('clusters', {}).get(str(cluster_hint), {})
    mr = cl_data.get('mean_reversion')
    return bool(mr and mr.get('strategy_type') == 'mean_reversion')


def is_reconstructed(vps_row):
    """C3 fix: acepta 'reconstructed_post_hoc' (legacy manual) y 'reconstructed'
    (live_engine.py:872 organic orphan close)."""
    flag = str(vps_row.get('flag') or '').strip().lower()
    if flag in ('reconstructed_post_hoc', 'reconstructed'):
        return True
    reason = str(vps_row.get('reason_exit') or '').strip().lower()
    if reason in ('orphan_close', 'reconstructed', 'sl_trigger_reconstructed',
                  'sl_trigger_hit_reconstructed', 'sl_trigger_orphan_reconstructed'):
        return True
    return False


def cluster_hint_from_log_or_gmm(sym, entry_candle, log_events, bingx_cache):
    """C4 fix: obtiene cluster_id para decidir is_mr_trade.

    Prioridad:
      1. log_events['signals_raw'][(entry_candle, sym)].get('k')
      2. GMM fallback usando bingx_cache[sym] en entry_candle
      3. None -> NO aplicar is_mr_trade automaticamente
    """
    if entry_candle is None:
        return None, 'no_entry_candle'
    sr = log_events.get('signals_raw', {}).get((entry_candle, sym))
    if sr:
        k = sr.get('k')
        if k is not None:
            try:
                return int(k), 'signals_raw'
            except (TypeError, ValueError):
                pass
    # GMM fallback
    df = bingx_cache.get(sym)
    if df is None or len(df) == 0:
        return None, 'gmm_unavailable'
    sym_key = sym.replace("/USDT", "").replace("/", "")
    model_path = os.path.join(REGIME_MODELS_DIR, f"{sym_key}_regime.joblib")
    if not os.path.exists(model_path):
        return None, 'gmm_no_model'
    try:
        model_data = joblib.load(model_path)
        gmm = model_data['gmm']
        scaler = model_data['scaler']
        lookback = model_data.get('lookback', 100)

        target = pd.Timestamp(entry_candle)
        if target.tzinfo is None:
            target = target.tz_localize('UTC')
        df_ts = df['timestamp']
        if df_ts.dt.tz is None:
            df_ts = df_ts.dt.tz_localize('UTC')
        mask = df_ts <= target
        if not mask.any():
            return None, 'gmm_no_bars_before'
        idx = mask.values.nonzero()[0][-1]
        if idx < lookback:
            return None, 'gmm_insufficient_warmup'

        subset = df.iloc[max(0, idx - lookback - 10):idx + 1]
        feat_df = pd.DataFrame({
            'close': subset['close'].values,
            'high': subset['high'].values,
            'low': subset['low'].values,
            'open': subset['open'].values,
            'volume': subset['volume'].values,
        })
        features, valid_mask = compute_regime_features(feat_df, lookback=lookback)
        if not valid_mask.any():
            return None, 'gmm_no_valid_features'
        last_valid = valid_mask.nonzero()[0][-1]
        X = scaler.transform(features[last_valid:last_valid + 1])
        return int(gmm.predict(X)[0]), 'gmm'
    except Exception as e:
        return None, f'gmm_error:{e}'


def all_clusters_are_mr(sym, specialist_cache):
    """Devuelve True si TODOS los clusters operables del simbolo son MR."""
    cfg = specialist_cache.get(sym)
    if cfg is None:
        return False
    clusters = cfg.get('clusters', {})
    if not clusters:
        return False
    any_tf = False
    any_operable = False
    for cl_str, cl_data in clusters.items():
        mr = cl_data.get('mean_reversion')
        is_mr = bool(mr and mr.get('strategy_type') == 'mean_reversion')
        top = cl_data.get('top_configs', [])
        has_tf = bool(top) and any(c.get('sqn_p5', 0) > 0 for c in top)
        if has_tf:
            any_operable = True
            if not is_mr:
                any_tf = True
    return any_operable and not any_tf


def classify_exclusion(vps_row, entry_candle, log_events,
                        bingx_cache, binance_cache,
                        specialist_cache, skip_binance=False):
    """Devuelve (excl_code, detail_dict) o (None, None) si no se excluye.

    S4 orden canonico (primer match gana, documentado):
      1. reconstructed  (precios estimados, no son medida real)
      2. mr_kernel_no_implementado (audit v5 no soporta kernel MR)
      3. dd_breaker_activo (sizing modulado, no kernel puro)
      4. brain_reconcile_intervino (estado turbulento en el ciclo)
      5. cross_exchange_noise (senal borderline por micro-diff precio)
    """
    sym = vps_row['symbol']
    cycle_ts = vps_row['cycle_ts']  # exit cycle

    # 1. Reconstruido (siempre primero: precios estimados invalidan todo lo demas)
    if is_reconstructed(vps_row):
        return EXCL_RECON, {'flag': vps_row.get('flag', ''),
                            'reason_exit': vps_row.get('reason_exit', '')}

    # 2. MR (solo si podemos determinar cluster con precision)
    cluster_hint, cluster_src = cluster_hint_from_log_or_gmm(
        sym, entry_candle, log_events, bingx_cache
    )
    if cluster_hint is not None:
        if is_mr_trade(sym, cluster_hint, specialist_cache):
            return EXCL_MR, {'symbol': sym, 'cluster': cluster_hint,
                              'cluster_src': cluster_src}
    else:
        # Sin cluster_hint: solo excluir si TODOS los clusters son MR
        if all_clusters_are_mr(sym, specialist_cache):
            return EXCL_MR, {'symbol': sym, 'cluster': None,
                              'cluster_src': cluster_src,
                              'note': 'all_clusters_MR'}

    # 3. DD breaker (usar entry_candle, no exit cycle)
    probe_ts = entry_candle if entry_candle is not None else cycle_ts
    state = log_events['engine_states'].get(probe_ts)
    if state is None:
        for delta in (-1, 1):
            state = log_events['engine_states'].get(probe_ts + pd.Timedelta(hours=delta))
            if state:
                break
    if state is not None:
        dd_mult = state.get('dd_mult', state.get('dd_multiplier', 1.0))
        try:
            dd_mult = float(dd_mult)
        except (TypeError, ValueError):
            dd_mult = 1.0
        if dd_mult < 1.0:
            return EXCL_DD, {'dd_mult': dd_mult,
                             'dd_pct': state.get('dd_pct'),
                             'cb_active': state.get('cb_active'),
                             'probe_ts': str(probe_ts)}

    # 4. Brain reconcile intervino (usar entry_candle)
    if entry_candle is not None:
        for probe in (entry_candle, entry_candle - pd.Timedelta(hours=1)):
            if (probe, sym) in log_events['brain_reconciles']:
                return EXCL_BRAIN_RC, {'reconcile_cycle': str(probe)}

    # 5. Cross-exchange noise (usar entry_candle)
    if not skip_binance and entry_candle is not None:
        df_bx = bingx_cache.get(sym)
        df_bn = binance_cache.get(sym)
        diff = cross_exchange_diff_pct(df_bx, df_bn, entry_candle)
        if diff is not None and diff > CROSS_EXCHANGE_DIFF_PCT_THRESHOLD:
            return EXCL_CROSS, {'diff_pct': diff,
                                'entry_candle': str(entry_candle)}

    return None, None


# ============================================================================
# 11. WILSON CI + VEREDICTO
# ============================================================================

def wilson_ci_95(matches, denominator):
    if denominator == 0:
        return (0.0, 1.0)
    try:
        from scipy.stats import binomtest
        r = binomtest(matches, denominator)
        ci = r.proportion_ci(confidence_level=0.95, method='wilson')
        return (float(ci.low), float(ci.high))
    except Exception:
        p = matches / denominator if denominator > 0 else 0.0
        z = 1.96
        n = denominator
        center = (p + z*z/(2*n)) / (1 + z*z/n)
        margin = z * ((p*(1-p)/n + z*z/(4*n*n))**0.5) / (1 + z*z/n)
        return (max(0.0, center - margin), min(1.0, center + margin))


def build_verdict(matches, denominator, min_n=MIN_N_FOR_ROBUST_VERDICT):
    """Devuelve (tag_utf8, tag_ascii, msg, notes[]).

    S5 fix: si denominator < min_n, el veredicto NUNCA puede ser GREEN.
    Se fuerza AMBER con tag explicito [N_INSUFICIENTE_SIN_VEREDICTO_VALIDO]
    para evitar mensajes contradictorios GREEN + N_INSUFICIENTE.
    """
    if denominator == 0:
        return ("[N/A]", "[N/A]",
                "Sin trades en denominador tras exclusiones.",
                ["N efectivo = 0, no hay base para evaluar."])
    rate = matches / denominator
    ci_low, ci_high = wilson_ci_95(matches, denominator)

    notes = [f"match_rate = {rate*100:.1f}% ({matches}/{denominator})",
             f"CI95% Wilson = [{ci_low*100:.1f}%, {ci_high*100:.1f}%]"]

    insufficient = denominator < min_n

    # Computar veredicto sin N_insuficiente primero
    if rate >= VERDICT_GREEN_RATE and ci_low >= VERDICT_GREEN_CI_LOW:
        raw_color = 'GREEN'
    elif rate >= VERDICT_AMBER_RATE or ci_low >= VERDICT_AMBER_CI_LOW:
        raw_color = 'AMBER'
    else:
        raw_color = 'RED'

    # S5: override GREEN si N insuficiente
    if insufficient and raw_color == 'GREEN':
        raw_color = 'AMBER_NINS'

    if raw_color == 'GREEN':
        tag_u = "\u2705 CONSISTENTE CON V4, FIDELIDAD DEL KERNEL CONFIRMADA"
        tag_a = "[OK] CONSISTENTE CON V4, FIDELIDAD DEL KERNEL CONFIRMADA"
    elif raw_color == 'AMBER_NINS':
        tag_u = "\u26a0\ufe0f  [N_INSUFICIENTE_SIN_VEREDICTO_VALIDO]"
        tag_a = "[N_INSUF] SIN VEREDICTO VALIDO"
        notes.append(
            f"N={denominator} < {min_n} minimo. Match rate observado "
            f"{rate*100:.1f}% con CI [{ci_low*100:.1f}%, {ci_high*100:.1f}%]. "
            f"Esperar >={min_n} trades antes de emitir veredicto."
        )
    elif raw_color == 'AMBER':
        tag_u = "\u26a0\ufe0f  REGRESION MENOR, REVISAR CASOS SIN MATCH UNO A UNO"
        tag_a = "[WARN] REGRESION MENOR, REVISAR CASOS SIN MATCH UNO A UNO"
        if insufficient:
            notes.append(f"Ademas N={denominator} < {min_n}: acumular mas trades.")
    else:
        tag_u = "\U0001f6a8 REGRESION GRAVE, POSIBLE BUG ACUMULATIVO"
        tag_a = "[ALERT] REGRESION GRAVE, POSIBLE BUG ACUMULATIVO"
        if insufficient:
            notes.append(f"Ademas N={denominator} < {min_n}: acumular mas trades.")

    return (tag_u, tag_a, "", notes)


# ============================================================================
# 12. MATCHING + ANALISIS DE NO-MATCH
# ============================================================================

def match_vps_to_kernel(vps_trades, kernel_trades, regime_change_events,
                        entry_tol=ENTRY_CANDLE_TOLERANCE,
                        exit_tol=EXIT_CANDLE_TOLERANCE):
    """C1 + S8 fix. Match VPS trade vs kernel trade con semantica correcta:
      - kernel ENTRY vs vps entry_candle (tolerancia entry_tol horas)
      - kernel EXIT vs vps exit_cycle (tolerancia exit_tol horas)
      - mismo simbolo + mismo side
      - razon de salida compatible via _reason_compatible (SAME vs DIFF)

    S8: kernel_idx se guarda en el match, sin segunda pasada aliasing.
    """
    matches = []
    no_match_vps = []
    matched_kernel_ids = set()

    for idx, vps_row in vps_trades.iterrows():
        if vps_row.get('_excluded'):
            continue
        if vps_row.get('_entry_candle') is None:
            # C1: trade sin entry_candle inferible -> no matcheable
            continue

        vps_sym = vps_row['symbol']
        vps_side = vps_row['side']
        vps_entry_candle = vps_row['_entry_candle']
        vps_exit_cycle = vps_row['cycle_ts']
        vps_entry_price = float(vps_row['entry_price'])
        vps_reason = vps_row['reason_exit']

        if vps_reason == 'regime_change':
            sym_changes = regime_change_events.get(vps_sym, [])
            matched_rc = False
            for ev in sym_changes:
                ev_ts = pd.Timestamp(ev['timestamp'])
                diff = abs((ev_ts - vps_exit_cycle).total_seconds()) / 3600.0
                if diff <= exit_tol:
                    matches.append({
                        'vps_idx': idx, 'vps_sym': vps_sym, 'vps_side': vps_side,
                        'vps_entry_candle': vps_entry_candle,
                        'vps_exit_cycle': vps_exit_cycle,
                        'vps_reason': vps_reason,
                        'match_type': 'regime_change',
                        'kernel_reason': 'regime_change',
                        'reason_match': 'SAME',
                        'detail': f"C{ev['from_cluster']}->C{ev['to_cluster']}",
                        'entry_price_vps': vps_entry_price,
                        'entry_price_kernel': None,
                        'kernel_idx': None,
                    })
                    matched_rc = True
                    break
            if not matched_rc:
                no_match_vps.append({
                    'idx': idx, 'symbol': vps_sym, 'side': vps_side,
                    'entry_candle': vps_entry_candle,
                    'exit_cycle': vps_exit_cycle,
                    'reason': vps_reason,
                    'entry_price': vps_entry_price,
                    'detail': 'regime_change sin transicion detectada',
                })
            continue

        best_match = None
        best_dist = float('inf')
        best_ki = None
        for ki, kt in enumerate(kernel_trades):
            if ki in matched_kernel_ids:
                continue
            if kt['symbol'] != vps_sym or kt['side'] != vps_side:
                continue
            kt_entry_ts = pd.Timestamp(kt['entry_ts'])
            if kt_entry_ts.tzinfo is None:
                kt_entry_ts = kt_entry_ts.tz_localize('UTC')
            kt_entry_candle = kt_entry_ts.floor('h')
            kt_exit_ts = pd.Timestamp(kt['exit_ts'])
            if kt_exit_ts.tzinfo is None:
                kt_exit_ts = kt_exit_ts.tz_localize('UTC')
            kt_exit_cycle = kt_exit_ts.floor('h')

            entry_diff_h = abs((kt_entry_candle - vps_entry_candle).total_seconds()) / 3600.0
            exit_diff_h = abs((kt_exit_cycle - vps_exit_cycle).total_seconds()) / 3600.0

            if entry_diff_h <= entry_tol and exit_diff_h <= exit_tol:
                price_diff = abs(kt['entry_price'] - vps_entry_price) / max(vps_entry_price, 1e-9) * 100.0
                dist = entry_diff_h + exit_diff_h + price_diff
                if dist < best_dist:
                    best_dist = dist
                    best_match = kt
                    best_ki = ki

        if best_match is not None and best_ki is not None:
            reason_match = "SAME" if _reason_compatible(vps_reason, best_match['reason']) else "DIFF"
            matched_kernel_ids.add(best_ki)
            kt_entry_candle_ts = pd.Timestamp(best_match['entry_ts'])
            if kt_entry_candle_ts.tzinfo is None:
                kt_entry_candle_ts = kt_entry_candle_ts.tz_localize('UTC')
            kt_exit_ts_m = pd.Timestamp(best_match['exit_ts'])
            if kt_exit_ts_m.tzinfo is None:
                kt_exit_ts_m = kt_exit_ts_m.tz_localize('UTC')
            matches.append({
                'vps_idx': idx, 'vps_sym': vps_sym, 'vps_side': vps_side,
                'vps_entry_candle': vps_entry_candle,
                'vps_exit_cycle': vps_exit_cycle,
                'vps_reason': vps_reason,
                'match_type': 'kernel_match',
                'kernel_reason': best_match['reason'],
                'kernel_entry_candle': kt_entry_candle_ts.floor('h'),
                'kernel_exit_cycle': kt_exit_ts_m.floor('h'),
                'entry_price_vps': vps_entry_price,
                'entry_price_kernel': best_match['entry_price'],
                'reason_match': reason_match,
                'kernel_idx': best_ki,
                'detail': f"price_diff={abs(best_match['entry_price']-vps_entry_price)/max(vps_entry_price,1e-9)*100:.3f}%",
            })
        else:
            no_match_vps.append({
                'idx': idx, 'symbol': vps_sym, 'side': vps_side,
                'entry_candle': vps_entry_candle,
                'exit_cycle': vps_exit_cycle,
                'reason': vps_reason,
                'entry_price': vps_entry_price,
                'detail': 'no kernel trade within entry_tol+exit_tol',
            })

    # S8: kernel sin match = todos los no en matched_kernel_ids
    no_match_kernel = [kt for ki, kt in enumerate(kernel_trades) if ki not in matched_kernel_ids]

    return matches, no_match_vps, no_match_kernel


def hypothesis_for_no_match(entry, kind, bingx_cache, binance_cache):
    """kind in {'vps_no_kernel', 'kernel_no_vps', 'diff_reason'}.
    Devuelve codigo de hipotesis (string)."""
    sym = entry.get('symbol') or entry.get('vps_sym')
    if kind == 'diff_reason':
        return "razon_salida_distinta"

    if kind == 'kernel_no_vps':
        return "no_match_bot"

    # kind == 'vps_no_kernel'
    exit_ts = entry.get('exit_ts')
    df_bx = bingx_cache.get(sym)
    df_bn = binance_cache.get(sym)
    diff = cross_exchange_diff_pct(df_bx, df_bn, exit_ts)
    if diff is not None and diff > CROSS_EXCHANGE_HYPOTHESIS_PCT:
        return "micro_precio_BingX_vs_Binance"
    return "no_match_kernel"


# ============================================================================
# 13. REPORTE 5 SECCIONES
# ============================================================================

V3_STATS = {'N': 11, 'matches': 9, 'rate': 0.82, 'ci_low': 0.52, 'ci_high': 0.95}
V4_STATS = {'N': 11, 'matches': 10, 'rate': 0.91, 'ci_low': 0.62, 'ci_high': 0.98}


def _fmt_ts(ts):
    if ts is None:
        return "N/A"
    try:
        return pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M UTC')
    except Exception:
        return str(ts)


def write_report(out_path, ctx):
    """ctx es un dict con todo lo que necesita el reporte."""
    lines = []
    def out(s=""):
        lines.append(s)

    def hr(char='='):
        out(char * 78)

    # ==== SECCION 1: RESUMEN EJECUTIVO ====
    hr()
    out("AUDITORIA DE FIDELIDAD v5 -- KERNEL STATELESS BingX (post-v2.3.2)")
    hr()
    out(f"Generado: {ctx['now_str']}")
    out(f"Ventana analizada: {_fmt_ts(ctx['since_ts'])} -> {_fmt_ts(ctx['until_ts'])}")
    out(f"v2.3.2 deploy detectado: {_fmt_ts(ctx['deploy_ts'])}")
    out()
    out("--- RESUMEN EJECUTIVO ---")
    out(f"N trades VPS en ventana bruta:           {ctx['n_window']}")
    out(f"N entry_candle no inferible:             {ctx.get('n_entry_not_inferrable', 0)}")
    out(f"N excluidos (5 categorias):              {ctx['n_excluded']}")
    for code, n in ctx['exclusion_counts'].items():
        out(f"    {code:<45s}: {n}  ({EXCL_LABELS.get(code, '')})")
    out(f"N efectivo (denominador):                {ctx['n_effective']}")
    out(f"Matches:                                 {ctx['n_matches']}")
    out(f"  Mismo entry+side+razon (OK):           {ctx['n_same_reason']}")
    out(f"  Mismo entry+side, razon distinta:      {ctx['n_diff_reason']}")
    out(f"  Regime change match:                   {ctx['n_regime']}")
    out(f"Sin match (VPS sin kernel equivalente):  {ctx['n_no_match_vps']}")
    out(f"Extras del kernel (no ejecutados en bot):{ctx['n_no_match_kernel']}")
    out()

    denom = ctx['n_effective']
    if denom > 0:
        rate = ctx['n_matches'] / denom
        out(f"Match rate efectivo: {rate*100:.1f}%   "
            f"CI95% Wilson = [{ctx['ci_low']*100:.1f}%, {ctx['ci_high']*100:.1f}%]")
    else:
        out("Match rate efectivo: N/A (denominador = 0)")

    out()
    out("Comparativa numerica:")
    out(f"  v3 (Binance):  N={V3_STATS['N']:>3}  matches={V3_STATS['matches']}  "
        f"rate={V3_STATS['rate']*100:.0f}%   CI~[{V3_STATS['ci_low']*100:.0f}%, {V3_STATS['ci_high']*100:.0f}%]")
    out(f"  v4 (BingX):    N={V4_STATS['N']:>3}  matches={V4_STATS['matches']}  "
        f"rate={V4_STATS['rate']*100:.0f}%   CI~[{V4_STATS['ci_low']*100:.0f}%, {V4_STATS['ci_high']*100:.0f}%]")
    out(f"  v5 (BingX+exc):N={denom:>3}  matches={ctx['n_matches']}  "
        f"rate={(rate*100 if denom > 0 else 0):.1f}%   "
        f"CI [{ctx['ci_low']*100:.1f}%, {ctx['ci_high']*100:.1f}%]")
    out()
    out("VEREDICTO:")
    out(f"  {ctx['verdict_ascii']}")
    for n in ctx['verdict_notes']:
        out(f"    - {n}")
    out()

    # ==== SECCION 2: TABLA TRADE-A-TRADE ====
    hr()
    out("SECCION 2: TABLA TRADE-A-TRADE")
    hr()
    out(f"{'ts_entry':<20} {'symbol':<12} {'side':<6} "
        f"{'entry_vps':>10} {'entry_ker':>10} "
        f"{'exit_vps':<15} {'exit_ker':<15} {'match':<8} {'exclusion':<45}")
    out("-" * 78)

    for row in ctx['trade_rows']:
        out(f"{_fmt_ts(row['entry_ts']):<20} "
            f"{row['symbol']:<12} {row['side']:<6} "
            f"{(f'{row['entry_real']:.4f}' if row['entry_real'] is not None else '-'):>10} "
            f"{(f'{row['entry_kernel']:.4f}' if row['entry_kernel'] is not None else '-'):>10} "
            f"{(row['exit_reason_real'] or '-'):<15} "
            f"{(row['exit_reason_kernel'] or '-'):<15} "
            f"{row['match_type']:<8} "
            f"{(row['exclusion'] or '-'):<45}")
    out()

    # ==== SECCION 3: CASOS SIN MATCH -- analisis detallado ====
    hr()
    out("SECCION 3: CASOS SIN MATCH -- ANALISIS DETALLADO")
    hr()
    if not ctx['no_match_detail']:
        out("(Sin casos sin match en el denominador efectivo.)")
    else:
        for i, d in enumerate(ctx['no_match_detail'], 1):
            out(f"[{i}] {d['symbol']:<10} side={d['side']}  entry={_fmt_ts(d['entry_ts'])}")
            out(f"    entry_price_real   = {d.get('entry_real', 'N/A')}")
            out(f"    entry_price_kernel = {d.get('entry_kernel', 'N/A')}")
            out(f"    exit_reason_real   = {d.get('exit_reason_real', 'N/A')}")
            out(f"    exit_reason_kernel = {d.get('exit_reason_kernel', 'N/A')}")
            out(f"    cross_exchange_diff= {d.get('cross_diff_pct', 'N/A')}")
            out(f"    hipotesis          = {d.get('hypothesis', 'N/A')}")
            out()
    out()

    # ==== SECCION 4: EXCLUSIONES ====
    hr()
    out("SECCION 4: EXCLUSIONES -- DESGLOSE POR MOTIVO")
    hr()
    for code, label in EXCL_LABELS.items():
        items = ctx['exclusion_items'].get(code, [])
        out(f"[{code}] -- {label}  ({len(items)})")
        for it in items:
            extra_bits = []
            for k in ('diff_pct', 'dd_mult', 'reconcile_cycle', 'cluster', 'reason_exit', 'flag'):
                if k in it['detail']:
                    extra_bits.append(f"{k}={it['detail'][k]}")
            extra = " ".join(extra_bits)
            out(f"    {_fmt_ts(it['ts']):<20} {it['symbol']:<12} {it['side']:<6} {extra}")
        out()
    out()

    # ==== SECCION 5: COMPARATIVA VS v4 ====
    hr()
    out("SECCION 5: COMPARATIVA v3 / v4 / v5")
    hr()
    out(f"{'version':<10} {'N':>5} {'matches':>10} {'rate':>8} {'CI_low':>10} {'CI_high':>10}")
    out(f"{'v3':<10} {V3_STATS['N']:>5} {V3_STATS['matches']:>10} "
        f"{V3_STATS['rate']*100:>7.1f}% {V3_STATS['ci_low']*100:>9.1f}% {V3_STATS['ci_high']*100:>9.1f}%")
    out(f"{'v4':<10} {V4_STATS['N']:>5} {V4_STATS['matches']:>10} "
        f"{V4_STATS['rate']*100:>7.1f}% {V4_STATS['ci_low']*100:>9.1f}% {V4_STATS['ci_high']*100:>9.1f}%")
    v5_rate = ctx['n_matches'] / denom if denom > 0 else 0.0
    out(f"{'v5':<10} {denom:>5} {ctx['n_matches']:>10} "
        f"{v5_rate*100:>7.1f}% {ctx['ci_low']*100:>9.1f}% {ctx['ci_high']*100:>9.1f}%")
    out()
    out("Comentario sobre convergencia/divergencia (S10 fix: CI overlap formal):")
    if denom == 0:
        out("  Insuficientes trades en denominador. Repetir cuando N >= 50.")
    else:
        v5_lo, v5_hi = ctx['ci_low'], ctx['ci_high']
        v4_lo, v4_hi = V4_STATS['ci_low'], V4_STATS['ci_high']
        if v5_hi < v4_lo:
            out(f"  v5 DIVERGE A LA BAJA: CI v5 [{v5_lo*100:.1f}, {v5_hi*100:.1f}]% "
                f"no solapa con CI v4 [{v4_lo*100:.0f}, {v4_hi*100:.0f}]%.")
        elif v5_lo > v4_hi:
            out(f"  v5 DIVERGE AL ALZA: CI v5 [{v5_lo*100:.1f}, {v5_hi*100:.1f}]% "
                f"supera CI v4 [{v4_lo*100:.0f}, {v4_hi*100:.0f}]%.")
        elif abs(v5_rate - V4_STATS['rate']) > 0.10:
            out(f"  v5 difiere de v4 en >10pp pero CIs SE SOLAPAN -> no significativo "
                f"con N disponible.")
        else:
            out(f"  v5 compatible con v4 dentro de CI (no hay evidencia de divergencia).")
    out()
    out("CAVEAT IMPORTANTE: v3 y v4 tienen bugs de matching identificados en el")
    out("ultra review del 17/04/2026 (entry/exit semantics, kernel copy, tolerancia")
    out("laxa, rollover frágil). Sus match rate son REFERENCIALES, no ground truth.")
    out("No extrapolar a la baja directamente si v5 da menos del 91% de v4.")
    out()
    hr()

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    # Tambien volcar version UTF-8 con emojis en veredicto (si el terminal lo soporta)
    utf8_path = out_path.replace('.txt', '_utf8.txt')
    with open(utf8_path, 'w', encoding='utf-8') as f:
        content = '\n'.join(lines)
        content = content.replace(ctx['verdict_ascii'], ctx['verdict_utf8'])
        f.write(content + '\n')

    return out_path, utf8_path


# ============================================================================
# 14. MAIN ORCHESTRATOR
# ============================================================================

def parse_iso_ts(s):
    if s is None:
        return None
    ts = pd.Timestamp(s)
    if ts.tzinfo is None:
        ts = ts.tz_localize('UTC')
    return ts


def verify_kernel_parity():
    """C2: compara SHA256 del codigo kernel actual vs expected.

    Returns (ok_audit, ok_lab, messages).
    """
    import inspect
    msgs = []
    # Audit kernel
    try:
        src_audit = inspect.getsource(extract_trades_tf)
        h_audit = hashlib.sha256(src_audit.encode()).hexdigest()
    except Exception as e:
        msgs.append(f"[KERNEL_PARITY] No se pudo hashear extract_trades_tf: {e}")
        return (False, False, msgs)
    ok_audit = h_audit == EXPECTED_AUDIT_KERNEL_HASH
    msgs.append(f"[KERNEL_PARITY] audit.extract_trades_tf: {h_audit[:12]}... "
                f"{'OK' if ok_audit else 'MISMATCH'}")
    if not ok_audit:
        msgs.append(f"[KERNEL_PARITY][WARN] Expected {EXPECTED_AUDIT_KERNEL_HASH[:12]}... "
                    "Kernel del audit modificado desde la revision. "
                    "Revisar cambio vs brain_engine.generate_signals y actualizar EXPECTED_AUDIT_KERNEL_HASH.")

    # Lab kernel (referencia; el audit reimplementa pero lab es la referencia semantica)
    ok_lab = False
    try:
        import lab_historico_numba_v8_3 as _lab
        src_lab = inspect.getsource(_lab.run_simulation_numba)
        h_lab = hashlib.sha256(src_lab.encode()).hexdigest()
        ok_lab = h_lab == EXPECTED_LAB_KERNEL_HASH
        msgs.append(f"[KERNEL_PARITY] lab.run_simulation_numba: {h_lab[:12]}... "
                    f"{'OK' if ok_lab else 'MISMATCH'}")
        if not ok_lab:
            msgs.append(f"[KERNEL_PARITY][WARN] Expected {EXPECTED_LAB_KERNEL_HASH[:12]}... "
                        "Lab cambio; verificar si audit sigue semanticamente alineado.")
    except Exception as e:
        msgs.append(f"[KERNEL_PARITY] No se pudo importar/hashear lab: {e}")

    return (ok_audit, ok_lab, msgs)


def run_audit(args):
    global COMBOLAB_DIR, REGIME_MODELS_DIR, SPECIALIST_CONFIGS_DIR, PRESETS_DIR
    print("=" * 70)
    print("AUDITORIA DE FIDELIDAD v5 (post-v2.3.2, BingX + exclusiones)")
    print("=" * 70)

    # C6: resolver COMBOLAB_DIR prioridad CLI > env > default
    if getattr(args, 'combolab_dir', None):
        COMBOLAB_DIR = os.path.abspath(args.combolab_dir)
        if COMBOLAB_DIR not in sys.path:
            sys.path.insert(0, COMBOLAB_DIR)
        REGIME_MODELS_DIR, SPECIALIST_CONFIGS_DIR, PRESETS_DIR = _resolve_combolab_paths()
    if not os.path.isdir(COMBOLAB_DIR):
        print(f"ERROR: COMBOLAB_DIR no existe: {COMBOLAB_DIR}", file=sys.stderr)
        print("  Opciones: --combolab-dir PATH | export COMBOLAB_DIR=PATH", file=sys.stderr)
        sys.exit(2)
    print(f"COMBOLAB_DIR: {COMBOLAB_DIR}")
    try:
        _lazy_import_combolab_modules()
    except ImportError as e:
        print(f"ERROR: no se pudo importar modulos de combolab: {e}", file=sys.stderr)
        sys.exit(2)

    # C2: kernel parity check
    ok_audit, ok_lab, msgs = verify_kernel_parity()
    for m in msgs:
        print(m)
    if not ok_audit:
        print("[KERNEL_PARITY] Continuando con warning; revisar el cambio del kernel.",
              file=sys.stderr)

    since_ts = parse_iso_ts(args.since) or parse_iso_ts(DEFAULT_SINCE_ISO)
    until_ts = parse_iso_ts(args.until) if args.until else None

    # 1. Log
    log_path = args.engine_log
    if not log_path:
        for p in DEFAULT_ENGINE_LOG_CANDIDATES:
            if os.path.exists(p):
                log_path = p
                break
    log_start_date = pd.Timestamp(args.log_start_date) if args.log_start_date else pd.Timestamp(since_ts.date())
    print(f"\nEngine log: {log_path or '(ninguno)'}")
    print(f"Log start date: {log_start_date.date()}")
    log_events = parse_engine_log(log_path, log_start_date)
    print(f"  [ENGINE_STATE]: {len(log_events['engine_states'])} ciclos")
    print(f"  [BRAIN_RECONCILE]: {len(log_events['brain_reconciles'])} eventos")
    print(f"  [ORPHAN_CLOSE]: {len(log_events['orphan_closes'])} eventos")
    print(f"  [SIGNALS_EXECUTED]: {len(log_events['signals_executed'])} eventos")
    if log_events['log_start_ts']:
        print(f"  Log span: {log_events['log_start_ts']} -> {log_events['log_end_ts']}")

    deploy_ts = find_v232_deploy_ts(log_events, since_ts)
    print(f"v2.3.2 deploy_ts (usado como inicio de ventana): {deploy_ts}")

    # 2. Trades
    csv_path = args.trade_csv or DEFAULT_TRADE_CSV
    vps_window, vps_all = load_vps_trades(csv_path, since_ts, until_ts)
    print(f"\nTrades CSV: {len(vps_all)} totales, {len(vps_window)} en ventana desde {since_ts}")
    if len(vps_window) == 0:
        print("Sin trades en ventana. Escribiendo reporte vacio.")

    # 3. Specialist configs cache
    symbols = list(vps_window['symbol'].unique()) if len(vps_window) > 0 else []
    specialist_cache = {}
    for sym in symbols:
        specialist_cache[sym] = load_specialist_config(sym)

    # 4. Data download (BingX + Binance) salvo dry-run
    bingx_cache = {}
    binance_cache = {}

    if args.dry_run:
        print("\n[DRY RUN] Saltando descarga de BingX/Binance y kernel.")
    else:
        bingx_ex = create_bingx_exchange()
        print("BingX OK")
        binance_ex = None
        if not args.skip_binance:
            try:
                binance_ex = create_binance_exchange()
                print("Binance OK")
            except Exception as e:
                print(f"WARN: Binance no disponible ({e}), diff cross-exchange se omitira")
                binance_ex = None

        for sym in symbols:
            print(f"\n--- Descargando {sym} ---")
            bingx_cache[sym] = download_bingx(sym, bingx_ex)
            if binance_ex is not None:
                try:
                    binance_cache[sym] = download_binance(sym, binance_ex)
                except Exception as e:
                    print(f"    WARN Binance {sym}: {e}")
                    binance_cache[sym] = None

    # 5. Kernel (solo si no dry-run)
    all_kernel_trades = []
    regime_change_events = {}

    if not args.dry_run:
        audit_start_ts = since_ts - pd.Timedelta(hours=48)
        audit_end_ts = (until_ts or pd.Timestamp(datetime.now(timezone.utc)))

        for symbol in symbols:
            sym_clean = symbol.replace("/", "")
            print(f"\n{'='*60}")
            print(f"Procesando {symbol}")
            print(f"{'='*60}")

            df = bingx_cache.get(symbol)
            if df is None:
                print(f"  SKIP: no BingX data")
                continue
            df_naive = df.copy()
            df_naive['timestamp'] = df_naive['timestamp'].dt.tz_convert('UTC').dt.tz_localize(None)

            cluster_labels, n_clusters = classify_bars_gmm(symbol, df_naive)
            if cluster_labels is None:
                print(f"  SKIP: no regime model")
                continue

            spec_cfg = specialist_cache.get(symbol)
            if spec_cfg is None:
                print(f"  SKIP: no specialist config")
                continue

            changes = detect_regime_changes(cluster_labels)
            for bar_idx, from_cl, to_cl in changes:
                ts = df_naive['timestamp'].iloc[bar_idx]
                ts_aware = pd.Timestamp(ts).tz_localize('UTC') if pd.Timestamp(ts).tzinfo is None else pd.Timestamp(ts)
                if audit_start_ts <= ts_aware <= audit_end_ts:
                    regime_change_events.setdefault(symbol, []).append({
                        'bar_idx': bar_idx, 'timestamp': ts_aware,
                        'from_cluster': from_cl, 'to_cluster': to_cl,
                    })

            data = None
            for cl_id in range(n_clusters):
                cl_cfg = get_cluster_config(spec_cfg, cl_id)
                if cl_cfg is None:
                    print(f"  Cluster {cl_id}: no operable, skip")
                    continue

                config_id = cl_cfg['config_id']
                strategy = cl_cfg['strategy_type']
                preset_str = cl_cfg.get('preset', '') or ''
                print(f"  Cluster {cl_id}: {strategy}, config_id={config_id}, preset={preset_str}")

                if strategy == 'mean_reversion':
                    print(f"    MR kernel no implementado en v5; trades MR se excluyen del denominador")
                    continue

                preset_tuple, hyst = find_preset_in_symbol_presets(symbol, preset_str)
                if preset_tuple is None:
                    print(f"    WARN: preset sin resolver, skip")
                    continue

                print(f"    Precalculando indicadores (hyst={hyst})...")
                t0 = time.time()
                data = lab.precalculate_all_data(df_naive, preset=preset_tuple, hyst_mult=hyst,
                                                  symbol=symbol)
                print(f"    Precalc: {time.time()-t0:.1f}s")

                bar_ts = pd.to_datetime(data['timestamps'])
                start_bar = max(0, np.searchsorted(bar_ts, audit_start_ts.tz_convert(None) if audit_start_ts.tzinfo else audit_start_ts) - WARMUP_BARS)

                print(f"    Extracting trades (start_bar={start_bar})...")
                t0 = time.time()
                kernel_trades = extract_trades_tf(
                    data, config_id, cluster_labels, cl_id,
                    start_bar=start_bar, end_bar=len(data['close'])
                )
                print(f"    {len(kernel_trades)} trades en {time.time()-t0:.1f}s")

                for kt in kernel_trades:
                    kt_exit_ts = pd.Timestamp(kt['exit_ts'])
                    if kt_exit_ts.tzinfo is None:
                        kt_exit_ts = kt_exit_ts.tz_localize('UTC')
                    if audit_start_ts <= kt_exit_ts <= audit_end_ts:
                        kt['symbol'] = symbol
                        kt['exit_ts'] = kt_exit_ts
                        kt['entry_ts'] = pd.Timestamp(kt['entry_ts']).tz_localize('UTC') \
                            if pd.Timestamp(kt['entry_ts']).tzinfo is None else pd.Timestamp(kt['entry_ts'])
                        all_kernel_trades.append(kt)

            if data is not None and symbol in regime_change_events:
                rc_list = [(ev['bar_idx'], ev['from_cluster'], ev['to_cluster'])
                           for ev in regime_change_events[symbol]]
                sym_trades = [kt for kt in all_kernel_trades if kt.get('symbol') == symbol]
                other_trades = [kt for kt in all_kernel_trades if kt.get('symbol') != symbol]
                sym_trades = apply_regime_transitions(sym_trades, rc_list, data)
                all_kernel_trades = other_trades + sym_trades

    # 6. Inferir entry_candle (C1) y clasificar exclusiones
    excl_codes = list(EXCL_LABELS.keys())  # S4: orden canonico desde EXCL_LABELS
    exclusion_counts = {c: 0 for c in excl_codes}
    exclusion_items = {c: [] for c in excl_codes}

    vps_window['_entry_candle'] = None
    vps_window['_entry_src'] = ''
    vps_window['_excluded'] = False
    vps_window['_excl_code'] = ''
    vps_window['_excl_detail'] = None

    for idx, row in vps_window.iterrows():
        entry_candle, entry_src = infer_entry_candle(row, log_events)
        vps_window.at[idx, '_entry_candle'] = entry_candle
        vps_window.at[idx, '_entry_src'] = entry_src

        # Pasar entry_candle a classify_exclusion
        code, detail = classify_exclusion(
            row, entry_candle, log_events, bingx_cache, binance_cache,
            specialist_cache, skip_binance=args.skip_binance or args.dry_run,
        )
        if code is not None:
            vps_window.at[idx, '_excluded'] = True
            vps_window.at[idx, '_excl_code'] = code
            vps_window.at[idx, '_excl_detail'] = detail
            exclusion_counts[code] += 1
            exclusion_items[code].append({
                'ts': entry_candle if entry_candle is not None else row['cycle_ts'],
                'symbol': row['symbol'],
                'side': row['side'],
                'detail': detail,
            })

    n_window = len(vps_window)
    n_excluded = int(vps_window['_excluded'].sum())
    # Contadores separados y no solapados:
    # - n_excluded: por las 5 categorias formales (RECON/MR/DD/BRAIN_RC/CROSS)
    # - n_entry_not_inferrable: sobre no-excluidos, sin entry_candle determinable
    # - n_effective (= matchable): no-excluido Y con entry_candle
    n_entry_not_inferrable = int(sum(
        1 for _, r in vps_window.iterrows()
        if not r['_excluded'] and r['_entry_candle'] is None
    ))
    n_effective = n_window - n_excluded - n_entry_not_inferrable

    # 7. Match (solo trades NO excluidos)
    matches, no_match_vps, no_match_kernel = match_vps_to_kernel(
        vps_window, all_kernel_trades, regime_change_events
    )

    n_matches = len(matches)
    n_same = sum(1 for m in matches if m.get('reason_match') == 'SAME')
    n_diff = sum(1 for m in matches if m.get('reason_match') == 'DIFF')
    n_regime = sum(1 for m in matches if m['match_type'] == 'regime_change')

    # 8. Wilson CI + veredicto
    ci_low, ci_high = wilson_ci_95(n_matches, n_effective)
    tag_u, tag_a, _, notes = build_verdict(n_matches, n_effective, args.min_n)

    # 9. Construir filas trade-a-trade
    trade_rows = []
    matches_by_idx = {m['vps_idx']: m for m in matches}
    for idx, row in vps_window.iterrows():
        m = matches_by_idx.get(idx)
        ec = row.get('_entry_candle')
        if row['_excluded']:
            match_type = 'EXCL'
            entry_kernel = None
            exit_kernel = None
        elif ec is None:
            match_type = 'NO_EC'   # entry_candle no inferible
            entry_kernel = None
            exit_kernel = None
        elif m is None:
            match_type = 'NONE'
            entry_kernel = None
            exit_kernel = None
        else:
            match_type = 'OK' if m.get('reason_match') == 'SAME' else 'DIFF'
            entry_kernel = m.get('entry_price_kernel')
            exit_kernel = m.get('kernel_reason')

        trade_rows.append({
            'entry_ts': ec if ec is not None else row['cycle_ts'],
            'symbol': row['symbol'],
            'side': row['side'],
            'entry_real': float(row['entry_price']),
            'entry_kernel': entry_kernel,
            'exit_reason_real': row['reason_exit'],
            'exit_reason_kernel': exit_kernel,
            'match_type': match_type,
            'exclusion': row['_excl_code'] or '',
        })

    # 10. No-match detail
    no_match_detail = []
    for nm in no_match_vps:
        probe = nm.get('entry_candle') or nm.get('exit_cycle')
        hyp = hypothesis_for_no_match(nm, 'vps_no_kernel', bingx_cache, binance_cache)
        diff = cross_exchange_diff_pct(bingx_cache.get(nm['symbol']),
                                        binance_cache.get(nm['symbol']),
                                        probe)
        no_match_detail.append({
            'symbol': nm['symbol'], 'side': nm['side'],
            'entry_ts': probe,
            'entry_real': nm['entry_price'],
            'entry_kernel': None,
            'exit_reason_real': nm['reason'],
            'exit_reason_kernel': None,
            'cross_diff_pct': (f"{diff:.3f}%" if diff is not None else "N/A"),
            'hypothesis': hyp,
        })
    for kt in no_match_kernel:
        kt_entry = pd.Timestamp(kt['entry_ts'])
        if kt_entry.tzinfo is None:
            kt_entry = kt_entry.tz_localize('UTC')
        hyp = hypothesis_for_no_match(
            {'symbol': kt['symbol'], 'exit_ts': kt['exit_ts']},
            'kernel_no_vps', bingx_cache, binance_cache
        )
        no_match_detail.append({
            'symbol': kt['symbol'], 'side': kt['side'],
            'entry_ts': kt_entry.floor('h'),
            'entry_real': None,
            'entry_kernel': kt['entry_price'],
            'exit_reason_real': None,
            'exit_reason_kernel': kt['reason'],
            'cross_diff_pct': "N/A",
            'hypothesis': hyp,
        })
    for m in matches:
        if m.get('reason_match') == 'DIFF':
            diff = cross_exchange_diff_pct(bingx_cache.get(m['vps_sym']),
                                            binance_cache.get(m['vps_sym']),
                                            m.get('vps_entry_candle'))
            no_match_detail.append({
                'symbol': m['vps_sym'], 'side': m['vps_side'],
                'entry_ts': m.get('vps_entry_candle'),
                'entry_real': m['entry_price_vps'],
                'entry_kernel': m.get('entry_price_kernel'),
                'exit_reason_real': m['vps_reason'],
                'exit_reason_kernel': m['kernel_reason'],
                'cross_diff_pct': (f"{diff:.3f}%" if diff is not None else "N/A"),
                'hypothesis': "razon_salida_distinta",
            })

    # 11. Construir contexto para reporte
    now = datetime.now(timezone.utc)
    ctx = {
        'now_str': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'since_ts': since_ts,
        'until_ts': until_ts,
        'deploy_ts': deploy_ts,
        'n_window': n_window,
        'n_excluded': n_excluded,
        'n_entry_not_inferrable': n_entry_not_inferrable,
        'n_effective': n_effective,
        'n_matches': n_matches,
        'n_same_reason': n_same,
        'n_diff_reason': n_diff,
        'n_regime': n_regime,
        'n_no_match_vps': len(no_match_vps),
        'n_no_match_kernel': len(no_match_kernel),
        'ci_low': ci_low,
        'ci_high': ci_high,
        'verdict_utf8': tag_u,
        'verdict_ascii': tag_a,
        'verdict_notes': notes,
        'exclusion_counts': exclusion_counts,
        'exclusion_items': exclusion_items,
        'trade_rows': trade_rows,
        'no_match_detail': no_match_detail,
    }

    # 12. Escribir reporte
    ts_stamp = now.strftime('%Y%m%d_%H%M')
    report_path = os.path.join(THIS_DIR, f"audit_v5_report_{ts_stamp}.txt")
    ascii_path, utf8_path = write_report(report_path, ctx)

    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Ventana: {since_ts} -> {until_ts or 'ahora'}")
    print(f"N ventana: {n_window}  N excluidos: {n_excluded}  N efectivo: {n_effective}")
    print(f"Matches: {n_matches} (SAME={n_same}, DIFF={n_diff}, regime={n_regime})")
    print(f"No-match VPS: {len(no_match_vps)}  No-match kernel: {len(no_match_kernel)}")
    if n_effective > 0:
        rate = n_matches / n_effective
        print(f"Rate: {rate*100:.1f}%  CI95=[{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
    print(f"Veredicto: {tag_a}")
    print()
    print(f"Reporte (ASCII):  {ascii_path}")
    print(f"Reporte (UTF-8):  {utf8_path}")
    return ctx


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="audit_fidelity_v5 (post-v2.3.2)")
    parser.add_argument('--since', type=str, default=DEFAULT_SINCE_ISO,
                        help=f"Inicio de ventana ISO8601 (default {DEFAULT_SINCE_ISO})")
    parser.add_argument('--until', type=str, default=None,
                        help="Fin de ventana ISO8601 (default: ahora)")
    parser.add_argument('--log-start-date', type=str, default=None,
                        help="Fecha del primer timestamp del engine.log (YYYY-MM-DD). "
                             "Default: fecha de --since")
    parser.add_argument('--engine-log', type=str, default=None,
                        help="Path a engine.log (default: engine.log o vps_engine_latest.log)")
    parser.add_argument('--trade-csv', type=str, default=None,
                        help="Path a trade_history.csv (default: ./trade_history.csv)")
    parser.add_argument('--dry-run', action='store_true',
                        help="No descarga BingX/Binance ni ejecuta kernel. Solo parsing/reporte.")
    parser.add_argument('--skip-binance', action='store_true',
                        help="Saltar diff cross-exchange (trata Exclusion 1 como no aplicable)")
    parser.add_argument('--min-n', type=int, default=MIN_N_FOR_ROBUST_VERDICT,
                        help=f"N minimo para veredicto robusto (default {MIN_N_FOR_ROBUST_VERDICT})")
    parser.add_argument('--combolab-dir', type=str, default=None,
                        help="Path a combolab (default: $COMBOLAB_DIR o ../combolab)")
    args = parser.parse_args()
    run_audit(args)


if __name__ == '__main__':
    main()
