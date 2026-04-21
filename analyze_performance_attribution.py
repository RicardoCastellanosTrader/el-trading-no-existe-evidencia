#!/usr/bin/env python3
"""
analyze_performance_attribution.py -- Atribucion de PnL por trade (offline).

Descompone el PnL real de cada trade en:

    pnl_real = alpha_esperado_nominal
             + factor_portfolio      (suma de 4 capas: vw, bf, br, dd)
             + slippage_total        (entry + exit)
             + funding               (= funding_paid_csv, convencion ccxt: +recibido/-pagado)
             + alpha_residual

CONVENCION DE SIGNOS:
    - slippage, factor_portfolio, funding, alpha_residual:
        + = favorable, - = coste
    - pnl_real y alpha_esperado_*: valores absolutos en USDT
      (sin convencion comparativa)
    La ecuacion DEBE cerrar numericamente con tolerancia 0.01 USDT por trade.

INPUTS:
    --trades trade_history.csv  (default ./trade_history.csv)
    --logs engine.log           (default: engine.log o vps_engine_latest.log)
    --json-dir regime_wf/       (default $COMBOLAB_DIR/regime_wf/)
    --combolab-dir PATH         (CLI > env COMBOLAB_DIR > ../combolab)
    --since YYYY-MM-DDTHH:MM:SSZ  (default 2026-04-16T17:00:00Z)
    --until YYYY-MM-DDTHH:MM:SSZ  (default: ahora)
    --log-start-date YYYY-MM-DD   (default: fecha de --since)
    --n-saturation 8              (umbral de saturacion, default 8)
    --no-plots                    (skip matplotlib)
    --exclude-reconstructed       (default True) / --include-reconstructed

OUTPUTS (en ./):
    attribution_per_trade_YYYYMMDD_HHMM.csv (26 columnas)
    attribution_summary_YYYYMMDD_HHMM.txt    (ASCII, cp1252-safe)
    attribution_summary_YYYYMMDD_HHMM_utf8.txt (con emojis de alerts)
    attribution_timeline_YYYYMMDD_HHMM.png   (opcional, si matplotlib)

Este script NO modifica ningun input. Solo lee.

FIXES v2.4.1 (ultra review):
  C1  entry_candle inferido (csv entry_timestamp_ms > log SIGNALS_EXECUTED).
  C2  consistency check por reconstruccion de precios (no tautologica).
  C3  COMBOLAB_DIR via CLI/env/default.
  C4  date rollover con ENGINE_STATE.t como ancla (resistente a gaps).
  S1  classify usa multipliers (admite proxy).
  S2  balance_req sin double-count de br.
  S3  --exclude-reconstructed default True.
  S4  split counters: n_pnl_recon_checked, n_pnl_recon_not_closing, n_components_missing.
  S5  unit validator de pnl_tr/pnl_fwd.
  S6  active_config_source='heuristic' trackeado (pendiente v2.3.4 logs).
  S7  CAPITALIZE safeguards: N>=20, |pnl|>=5 USDT.
  M9  DD breaker alert con umbral minimo.

LIMITACION (Q6): si entre la ventana analizada y el momento de correr este
analyzer hubo reciclajes del GMM, la reclasificacion (fallback b) podria
diferir del cluster real del ciclo original. Revisar si se corre el analyzer
despues de un reciclaje.

LIMITACION (Q7): Los multiplicadores vw/bf/br/dd NO se loguean hoy para
senales descartadas (solo para SIGNALS_EXECUTED). Usamos proxy de 5 ciclos
previos si el ciclo de un descarte no tiene ejecuciones. TODO: instrumentar
v2.3.4 para loguear vw/bf/br/dd dentro de [SIGNALS_DISCARDED].
"""

import argparse
import json
import os
import re
import sys
import time
import math
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timezone

# A36: log rotation tolerance — spec acepta archivo, glob, CSV.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
from log_file_resolver import resolve_engine_log_paths, read_log_files

# COMBOLAB_DIR resolution (CLI > env > default relative to __file__)
# La resolucion final ocurre en run() segun args.combolab_dir
_DEFAULT_COMBOLAB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'combolab'
)
COMBOLAB_DIR = os.environ.get('COMBOLAB_DIR', _DEFAULT_COMBOLAB)
if COMBOLAB_DIR not in sys.path:
    sys.path.insert(0, COMBOLAB_DIR)

try:
    from regime_features import compute_regime_features
    HAVE_REGIME_FEATURES = True
except Exception:
    HAVE_REGIME_FEATURES = False

# ---------------------------------------------------------------------------
# Constantes (sincronizadas con portfolio_manager.py)
# ---------------------------------------------------------------------------
MIN_ORDER_USDT = 5.0            # portfolio_manager.py:535
GLOBAL_CAP_PCT = 25.0           # max_portfolio_risk_pct, usado como global cap (L511-519)
NOMINAL_CAP_PCT = 5.0           # max_single_position_pct
GLOBAL_CAP_FRAC = GLOBAL_CAP_PCT / 100.0
NOMINAL_CAP_FRAC = NOMINAL_CAP_PCT / 100.0
COMMISSION_RATE = 0.001          # 0.10% round-trip approx (entry+exit)

# Umbrales del analyzer (configurables por CLI)
DEFAULT_N_SATURATION = 8
DEFAULT_MIN_N_CLUSTER_ALERTS = 5
DEFAULT_MIN_N_EDGE_EROSION = 3

# Alerts
SLIPPAGE_BP_ALERT = 15.0
BLENDING_PCT_ALERT = 20.0
FUNDING_PCT_ALERT = 10.0
EDGE_EROSION_RATIO_ALERT = 0.5
NO_ESTIMABLE_PCT_ALERT = 20.0
EDGE_EROSION_LAST_N = 20
EDGE_EROSION_DROP = 0.10

# S7: CAPITALIZAR safeguards
MIN_TRADES_FOR_CAPITALIZE_ALERT = 20
MIN_PNL_ABS_FOR_CAPITALIZE_ALERT = 5.0   # USDT
CAPITALIZE_PCT_THRESHOLD = 30.0

# M9: DD breaker alert minimum cost
MIN_DD_BREAKER_COST_FOR_ALERT = 1.0      # USDT
MIN_DD_BREAKER_N_TRADES = 3

# S4: balance consistency ratio threshold
BALANCE_NOT_CLOSING_RATIO_ALERT = 0.05

# S5: Expected unit for pnl_tr/pnl_fwd in walk-forward JSONs
EXPECTED_PNL_UNIT = "percent"            # "percent" o "fraction"
PNL_SAMPLE_RANGE_PERCENT = (0.01, 500.0)
PNL_SAMPLE_RANGE_FRACTION = (0.0001, 5.0)

# Consistency check
BALANCE_EQN_TOLERANCE_USDT = 0.01

# Proxy para multiplicadores (Q7)
PROXY_MIN_PREV_CYCLES = 5
PROXY_WINDOW_HOURS = 48

# Cluster classification thresholds (Q5)
SAT_FACTOR_ACTIVE = 0.90       # sat_factor < 0.90 para saturar
DD_FACTOR_ACTIVE = 1.00        # dd_factor < 1.00 para activar DD
BAL_BAJO_EPSILON = 0.05        # factores ~ 1.0 (+/- 0.05) = balance_bajo_absoluto

# Default ventana
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

def _resolve_paths():
    """Devuelve (default_json_dir, regime_models_dir) basado en COMBOLAB_DIR actual."""
    return (
        os.path.join(COMBOLAB_DIR, "regime_wf"),
        os.path.join(COMBOLAB_DIR, "regime_models"),
    )

DEFAULT_JSON_DIR, REGIME_MODELS_DIR = _resolve_paths()

# v2.3.3: trade_history.csv anade columna entry_timestamp_ms (12a columna).
# Trades pre-v2.3.3 no tienen la columna -> padded a ''/NaN por tolerancia.
CSV_COLUMNS = ['timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
               'size_usdt', 'pnl_pct', 'pnl_usdt', 'funding_paid',
               'reason_exit', 'flag', 'entry_timestamp_ms']
CSV_N_COLS = len(CSV_COLUMNS)


# ============================================================================
# 1. TRADE CSV LOADER
# ============================================================================

def load_trades(csv_path, since_ts, until_ts):
    """CSV tolerante a 10/11/12 columnas.

    v2.3.1- : 10 columnas (sin 'flag')
    v2.3.2  : 11 columnas (anade 'flag')
    v2.3.3+ : 12 columnas (anade 'entry_timestamp_ms', wall-clock ms del fill)

    Derivacion de entry_candle: ver infer_entry_candle(). Aqui solo preparamos
    exit_cycle = floor(timestamp, 'h'). entry_candle se computa por trade en
    attribute_trade (C1 Part B) usando entry_timestamp_ms si disponible, o
    busqueda en log.
    """
    rows = []
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        _ = f.readline()  # header variable; lo ignoramos, usamos posicional
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
    df['exit_cycle'] = df['timestamp'].dt.floor('h')

    mask = df['timestamp'] >= since_ts
    if until_ts is not None:
        mask &= df['timestamp'] <= until_ts
    return df[mask].reset_index(drop=True)


def infer_entry_candle(trade_row, log_events):
    """Devuelve (entry_candle_ts | None, source_str).

    source_str in {'csv', 'log', 'none'}.

    Prioridad:
    1. trade_row['entry_timestamp_ms'] presente y > 0 -> floor('h') a UTC.
    2. log: ultimo SIGNALS_EXECUTED del mismo simbolo con action=LONG|SHORT
       antes (estrictamente) de exit_cycle. Filtra CLOSE_* y HOLD.
    3. None con source='none' si ninguna via funciona -> trade excluido de
       atribucion per-trade; listado aparte en reporte.
    """
    ets = trade_row.get('entry_timestamp_ms')
    if ets is not None and not (isinstance(ets, float) and math.isnan(ets)) and ets > 0:
        try:
            return (pd.Timestamp(int(ets), unit='ms', tz='UTC').floor('h'), 'csv')
        except (TypeError, ValueError, OverflowError):
            pass

    sym = trade_row['symbol']
    exit_cycle = trade_row['exit_cycle']

    candidates = []
    for (cycle_ts, s), info in log_events['signals_executed'].items():
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
# 2. LOG PARSER
# ============================================================================

LOG_TS_RE = re.compile(r'^(\d{2}):(\d{2}):(\d{2})\s')
ENGINE_STATE_RE = re.compile(r'\[ENGINE_STATE\]\s+(\{.+\})')
SIGNALS_RAW_RE = re.compile(r'\[SIGNALS_RAW\]\s+(\{.+\})')
SIGNALS_DISCARDED_RE = re.compile(r'\[SIGNALS_DISCARDED\]\s+(\{.+\})')
SIGNALS_EXECUTED_RE = re.compile(r'\[SIGNALS_EXECUTED\]\s+(\{.+\})')
BRAIN_RECONCILE_RE = re.compile(r'\[BRAIN_RECONCILE\]\s+(\S+)')
ORPHAN_CLOSE_RE = re.compile(r'\[ORPHAN_CLOSE\]\s+(\S+)')


def parse_engine_log(log_path, log_start_date):
    """Parsea engine.log. C4 fix: usa [ENGINE_STATE].t (unix seconds) como
    ancla de fecha. Si el log tiene gaps (bot caido varias horas), la siguiente
    [ENGINE_STATE] re-sincroniza la fecha. Fallback: rollover 23->00 entre
    anclas.

    A36: log_path acepta archivo unico, glob pattern o CSV (ver
    log_file_resolver.resolve_engine_log_paths). Archivos se procesan en orden
    cronologico ascendente (mas antiguo primero). Soporte transparente .gz.
    """
    result = {
        'engine_states': {},
        'signals_raw': {},
        'signals_discarded': {},
        'signals_executed': {},
        'brain_reconciles': {},     # {(cycle_ts, sym): True}
        'orphan_closes': {},
        'brain_reconciles_per_day': {},   # {date: count}
        'log_start_ts': None,
        'log_end_ts': None,
        'log_date_sync_anchors': 0,   # debug: n_veces que ENGINE_STATE.t re-sincronizo
        'log_date_gap_warnings': 0,
    }

    if not log_path:
        return result
    try:
        paths = resolve_engine_log_paths(log_path)
    except (FileNotFoundError, ValueError):
        return result

    current_date = log_start_date
    last_hour = None

    # A36: bloque antes envuelto en `with open(log_path) as f`. Sustituido por
    # read_log_files sobre paths resueltos. Indentacion preservada via sentinela
    # para minimizar diff y facilitar auditoria literal antes/despues.
    if True:  # A36 sentinela: preserva nivel de indentacion del `with` original
        for line in read_log_files(paths):
            m = LOG_TS_RE.match(line)
            if not m:
                continue
            hh = int(m.group(1))
            mm = int(m.group(2))
            ss = int(m.group(3))

            # C4: si la linea es ENGINE_STATE con 't', re-sincronizar fecha.
            em = ENGINE_STATE_RE.search(line)
            anchor_ts = None
            if em:
                try:
                    es_payload = json.loads(em.group(1))
                    t_unix = es_payload.get('t')
                    if t_unix is not None:
                        anchor_ts = pd.Timestamp(int(t_unix), unit='s', tz='UTC')
                        # Validar que hh:mm:ss coincide con anchor (sanity)
                        if anchor_ts.hour == hh:
                            prev_date = current_date
                            current_date = pd.Timestamp(anchor_ts.date())
                            if prev_date != current_date:
                                result['log_date_sync_anchors'] += 1
                        else:
                            # Desajuste entre timestamp log y t unix; usar t
                            current_date = pd.Timestamp(anchor_ts.date())
                            result['log_date_sync_anchors'] += 1
                            hh = anchor_ts.hour
                            mm = anchor_ts.minute
                            ss = anchor_ts.second
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

            # Rollover fallback para lineas sin anchor
            if anchor_ts is None:
                if last_hour is not None:
                    if hh == 0 and last_hour == 23:
                        current_date = current_date + pd.Timedelta(days=1)
                    elif hh < last_hour and (last_hour - hh) >= 2:
                        # Gap sospechoso (ej. last=22, ahora=02 sin anchor)
                        # No podemos inferir con seguridad; contamos warning.
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
                    result['engine_states'][cycle_ts] = json.loads(em.group(1))
                except json.JSONDecodeError:
                    pass
                continue

            bm = BRAIN_RECONCILE_RE.search(line)
            if bm:
                sym = bm.group(1)
                result['brain_reconciles'][(cycle_ts, sym)] = True
                d = line_ts.date()
                result['brain_reconciles_per_day'][d] = \
                    result['brain_reconciles_per_day'].get(d, 0) + 1
                continue

            om = ORPHAN_CLOSE_RE.search(line)
            if om:
                result['orphan_closes'][(cycle_ts, om.group(1))] = True
                continue

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

            sdm = SIGNALS_DISCARDED_RE.search(line)
            if sdm:
                try:
                    payload = json.loads(sdm.group(1))
                    if isinstance(payload, dict):
                        for sym, info in payload.items():
                            result['signals_discarded'][(cycle_ts, sym)] = info
                except json.JSONDecodeError:
                    pass
                continue

            srm = SIGNALS_RAW_RE.search(line)
            if srm:
                try:
                    payload = json.loads(srm.group(1))
                    if isinstance(payload, dict):
                        for sym, info in payload.items():
                            result['signals_raw'][(cycle_ts, sym)] = info
                except json.JSONDecodeError:
                    pass

    return result


# ============================================================================
# 3. JSON LOADER + EXPECTANCY
# ============================================================================

def load_all_specialist_configs(json_dir):
    """Carga todos los *_specialist_configs.json. Key por symbol canonico 'BTC/USDT'."""
    out = {}
    if not os.path.isdir(json_dir):
        return out
    for fn in os.listdir(json_dir):
        if not fn.endswith('_specialist_configs.json'):
            continue
        sym_clean = fn.replace('_specialist_configs.json', '')
        sym = sym_clean[:-4] + '/USDT' if sym_clean.endswith('USDT') else sym_clean
        try:
            with open(os.path.join(json_dir, fn), 'r') as f:
                out[sym] = json.load(f)
        except Exception as e:
            print(f"[WARN] No se pudo cargar {fn}: {e}", file=sys.stderr)
    return out


def validate_pnl_units(specialist_cfgs):
    """S5: verificar empiricamente que pnl_tr/pnl_fwd estan en las unidades asumidas.

    Toma una muestra de top_configs y chequea que pnl_tr / trades_tr (media
    por trade) cae en el rango esperado. Si EXPECTED_PNL_UNIT='percent', esperamos
    valores como 0.5 - 5.0 (% por trade). Si 'fraction', 0.005 - 0.05.

    Devuelve (ok: bool, rango_observado: tuple, n_samples: int, messages: list).
    """
    samples = []
    messages = []
    for sym, cfg in specialist_cfgs.items():
        for cl_id, cl_data in cfg.get('clusters', {}).items():
            tcfg = (cl_data.get('top_configs') or [])
            if not tcfg:
                continue
            c = tcfg[0]
            tr = c.get('trades_tr', 0) or 0
            pnl_tr = c.get('pnl_tr', 0.0) or 0.0
            if tr > 0:
                samples.append(abs(pnl_tr / tr))

    if not samples:
        return (False, (None, None), 0, ["No se pudo extraer muestra de pnl_tr"])

    mn, mx = min(samples), max(samples)
    rng = PNL_SAMPLE_RANGE_PERCENT if EXPECTED_PNL_UNIT == 'percent' else PNL_SAMPLE_RANGE_FRACTION
    rng_lo, rng_hi = rng

    # La media por trade deberia caer dentro del rango;
    # una pequena fraccion de outliers (p.ej. clusters con muy pocos trades
    # cuya media es extrema) es tolerable.
    p5 = float(np.percentile(samples, 5))
    p95 = float(np.percentile(samples, 95))
    ok = (p5 >= rng_lo * 0.5) and (p95 <= rng_hi * 2.0)
    messages.append(
        f"[UNITS] pnl_tr/trades_tr N={len(samples)} p5={p5:.4f} p95={p95:.4f} "
        f"min={mn:.4f} max={mx:.4f} (esperado unidad='{EXPECTED_PNL_UNIT}', rango {rng_lo}-{rng_hi})"
    )
    if not ok:
        messages.append(
            f"[UNITS][WARN] Distribucion de pnl_tr/trades_tr fuera del rango esperado "
            f"para unidad='{EXPECTED_PNL_UNIT}'. Posible mismatch de unidades; revisar "
            f"regime_walk_forward.py o lab_historico_numba_v8_3.py."
        )
    return (ok, (mn, mx), len(samples), messages)


def compute_expectancy(cfg, cluster_id):
    """Devuelve (expectancy_pool_pct, expectancy_oos_pct, strategy, config_meta).

    expectancy_pool = (pnl_tr + pnl_fwd) / (trades_tr + trades_fwd)
    expectancy_oos  = pnl_fwd / trades_fwd  (si trades_fwd > 0)

    Units: % PnL por trade (tal como vienen en el JSON).
    """
    if cfg is None or cluster_id is None or cluster_id < 0:
        return (None, None, None, None)

    cluster_data = cfg.get('clusters', {}).get(str(cluster_id))
    if not cluster_data:
        return (None, None, None, None)

    mr_block = cluster_data.get('mean_reversion')
    if mr_block and mr_block.get('strategy_type') == 'mean_reversion':
        tr = mr_block.get('trades_tr', 0) or 0
        fw = mr_block.get('trades_fwd', 0) or 0
        pnl_tr = mr_block.get('pnl_tr', 0.0) or 0.0
        pnl_fwd = mr_block.get('pnl_fwd', 0.0) or 0.0
        pool = (pnl_tr + pnl_fwd) / (tr + fw) if (tr + fw) > 0 else None
        oos = pnl_fwd / fw if fw > 0 else None
        meta = {
            'config_id': mr_block.get('config_id'),
            'pf_combined': mr_block.get('pf_combined'),
            'trades_tr': tr, 'trades_fwd': fw,
            'pnl_tr': pnl_tr, 'pnl_fwd': pnl_fwd,
        }
        return (pool, oos, 'MR', meta)

    top_configs = cluster_data.get('top_configs', [])
    if not top_configs:
        return (None, None, None, None)
    selected = None
    for c in top_configs:
        if c.get('cross_cluster_survival', True):
            selected = c
            break
    if selected is None:
        selected = top_configs[0]
    if selected.get('sqn_p5', 0) <= 0:
        return (None, None, None, None)

    tr = selected.get('trades_tr', 0) or 0
    fw = selected.get('trades_fwd', 0) or 0
    pnl_tr = selected.get('pnl_tr', 0.0) or 0.0
    pnl_fwd = selected.get('pnl_fwd', 0.0) or 0.0
    pool = (pnl_tr + pnl_fwd) / (tr + fw) if (tr + fw) > 0 else None
    oos = pnl_fwd / fw if fw > 0 else None
    meta = {
        'config_id': selected.get('config_id'),
        'pf_combined': selected.get('pf_combined'),
        'trades_tr': tr, 'trades_fwd': fw,
        'pnl_tr': pnl_tr, 'pnl_fwd': pnl_fwd,
    }
    return (pool, oos, 'TF', meta)


# ============================================================================
# 4. GMM CLASSIFIER FALLBACK (para cluster de descartes sin 'k')
# ============================================================================

_GMM_CACHE = {}


def classify_cluster_at_ts(symbol, ts, bingx_data_cache):
    """Fallback (b) de Q6. Devuelve cluster_id o None si falla.

    bingx_data_cache: {sym: df} con columnas open/high/low/close/volume/timestamp (tz-aware UTC).
    Si no hay df o no se puede clasificar, devuelve None.
    """
    if not HAVE_REGIME_FEATURES:
        return None
    df = bingx_data_cache.get(symbol)
    if df is None or len(df) == 0:
        return None

    sym_key = symbol.replace("/USDT", "").replace("/", "")
    model_path = os.path.join(REGIME_MODELS_DIR, f"{sym_key}_regime.joblib")
    if not os.path.exists(model_path):
        return None

    if symbol not in _GMM_CACHE:
        try:
            _GMM_CACHE[symbol] = joblib.load(model_path)
        except Exception:
            return None

    model_data = _GMM_CACHE[symbol]
    gmm = model_data['gmm']
    scaler = model_data['scaler']
    lookback = model_data.get('lookback', 100)

    target_ts = pd.Timestamp(ts)
    if target_ts.tzinfo is None:
        target_ts = target_ts.tz_localize('UTC')
    df_ts = df['timestamp']
    if df_ts.dt.tz is None:
        df_ts = df_ts.dt.tz_localize('UTC')
    mask = df_ts <= target_ts
    if not mask.any():
        return None
    idx = mask.values.nonzero()[0][-1]
    if idx < lookback:
        return None

    subset = df.iloc[max(0, idx - lookback - 10):idx + 1]
    feat_df = pd.DataFrame({
        'close': subset['close'].values,
        'high': subset['high'].values,
        'low': subset['low'].values,
        'open': subset['open'].values,
        'volume': subset['volume'].values,
    })
    try:
        features, valid_mask = compute_regime_features(feat_df, lookback=lookback)
        if not valid_mask.any():
            return None
        last_valid_idx = valid_mask.nonzero()[0][-1]
        X = scaler.transform(features[last_valid_idx:last_valid_idx + 1])
        return int(gmm.predict(X)[0])
    except Exception:
        return None


# ============================================================================
# 5. SATURACION HELPERS
# ============================================================================

def new_entries_in_cycle(log_events, cycle_ts):
    """Devuelve lista de (symbol, info) para senales LONG/SHORT del ciclo (no CLOSE, no HOLD)."""
    out = []
    for (ts, sym), info in log_events['signals_raw'].items():
        if ts != cycle_ts:
            continue
        a = (info or {}).get('a', '')
        if a in ('LONG', 'SHORT'):
            out.append((sym, info))
    return out


def executed_in_cycle(log_events, cycle_ts):
    """Devuelve {sym: info} de SIGNALS_EXECUTED del ciclo."""
    out = {}
    for (ts, sym), info in log_events['signals_executed'].items():
        if ts == cycle_ts:
            out[sym] = info
    return out


def _normalize_discard_info(info):
    """Normaliza info de SIGNALS_DISCARDED: puede venir como str (legacy) o dict."""
    if isinstance(info, dict):
        return info
    if isinstance(info, str):
        return {'d': info}
    return {}


def discarded_in_cycle(log_events, cycle_ts):
    """Devuelve {sym: info_dict} de SIGNALS_DISCARDED del ciclo."""
    out = {}
    for (ts, sym), info in log_events['signals_discarded'].items():
        if ts == cycle_ts:
            out[sym] = _normalize_discard_info(info)
    return out


def cycle_multipliers_empirical(log_events, cycle_ts):
    """Mean de (vw, bf, br, dd) sobre SIGNALS_EXECUTED del ciclo. None si no hay."""
    execs = executed_in_cycle(log_events, cycle_ts)
    if not execs:
        return None
    vws = [float(info.get('vw', 1.0)) for info in execs.values()]
    bfs = [float(info.get('bf', 1.0)) for info in execs.values()]
    brs = [float(info.get('br', 1.0)) for info in execs.values()]
    dds = [float(info.get('dd', 1.0)) for info in execs.values()]
    return {
        'vw': float(np.mean(vws)),
        'bf': float(np.mean(bfs)),
        'br': float(np.mean(brs)),
        'dd': float(np.mean(dds)),
        'combined': float(np.mean(vws) * np.mean(bfs) * np.mean(brs) * np.mean(dds)),
        'n_exec': len(execs),
    }


def proxy_multipliers_from_prev_cycles(log_events, cycle_ts,
                                        min_cycles=PROXY_MIN_PREV_CYCLES,
                                        window_hours=PROXY_WINDOW_HOURS):
    """Q7. Mean de (vw, bf, br, dd) sobre los ultimos N ciclos previos con ejecuciones.

    Devuelve (multipliers_dict | None, n_cycles_usados).
    None si no se encuentran >= min_cycles en la ventana.
    """
    earliest = cycle_ts - pd.Timedelta(hours=window_hours)
    prev_cycles = sorted({ts for ts, _ in log_events['signals_executed'].keys()
                          if earliest <= ts < cycle_ts}, reverse=True)
    picked = []
    for pc in prev_cycles:
        m = cycle_multipliers_empirical(log_events, pc)
        if m is not None:
            picked.append(m)
            if len(picked) >= min_cycles:
                break
    if len(picked) < min_cycles:
        return (None, len(picked))
    return ({
        'vw': float(np.mean([m['vw'] for m in picked])),
        'bf': float(np.mean([m['bf'] for m in picked])),
        'br': float(np.mean([m['br'] for m in picked])),
        'dd': float(np.mean([m['dd'] for m in picked])),
        'combined': float(np.mean([m['combined'] for m in picked])),
        'n_exec': int(np.mean([m['n_exec'] for m in picked])),
    }, len(picked))


def classify_below_min_order_root_cause(n_signals, multipliers, dd_mult,
                                        n_sat_threshold=DEFAULT_N_SATURATION):
    """Q5 tie-break. Devuelve (category, sat_factor, dd_factor, rationale).

    S1 fix: acepta 'multipliers' (dict con 'br') provenientes del ciclo actual
    O del proxy (ver compute_saturation_analysis). Si multipliers es None,
    devuelve categoria 'multiplicadores_no_estimables' (distinta de
    'balance_bajo_absoluto').

    Categorias posibles:
      - saturacion_N_signals
      - dd_breaker_active
      - balance_bajo_absoluto
      - multiplicadores_no_estimables (nuevo, S1)
    """
    if multipliers is None:
        return ('multiplicadores_no_estimables', None,
                float(dd_mult) if dd_mult is not None else 1.0,
                'sin multiplicadores empiricos ni proxy')

    sat_factor = float(multipliers['br'])
    dd_factor = float(dd_mult) if dd_mult is not None else 1.0

    # Saturacion: umbral de N senales Y br significativamente < 1
    sat_candidate = (n_signals >= n_sat_threshold and
                     sat_factor < SAT_FACTOR_ACTIVE)
    dd_candidate = dd_factor < DD_FACTOR_ACTIVE

    if sat_candidate and dd_candidate:
        if sat_factor < dd_factor:
            return ('saturacion_N_signals', sat_factor, dd_factor,
                    f'sat({sat_factor:.3f}) < dd({dd_factor:.3f})')
        else:
            return ('dd_breaker_active', sat_factor, dd_factor,
                    f'dd({dd_factor:.3f}) <= sat({sat_factor:.3f})')
    if sat_candidate:
        return ('saturacion_N_signals', sat_factor, dd_factor,
                f'sat_factor={sat_factor:.3f}, n={n_signals}')
    if dd_candidate:
        return ('dd_breaker_active', sat_factor, dd_factor,
                f'dd_factor={dd_factor:.3f}')
    # Balance bajo absoluto: ningun factor comprime
    sat_near_one = abs(sat_factor - 1.0) <= BAL_BAJO_EPSILON
    dd_near_one = abs(dd_factor - 1.0) <= BAL_BAJO_EPSILON
    if sat_near_one and dd_near_one:
        return ('balance_bajo_absoluto', sat_factor, dd_factor,
                'no compression active')
    return ('balance_bajo_absoluto', sat_factor, dd_factor, 'other')


# ============================================================================
# 6. ATRIBUCION POR TRADE
# ============================================================================

# CONVENCION DE SIGNOS:
# - slippage, factor_portfolio, funding, alpha_residual: + = favorable, - = coste
# - pnl_real y alpha_esperado_*: valores absolutos en USDT (sin convencion comparativa)
# Verificar: pnl_real ~= alpha_esperado_nominal + factor_portfolio + slippage_total + funding + alpha_residual

def side_sign(side):
    s = (side or '').lower()
    if s in ('long', 'buy'):
        return 1.0
    if s in ('short', 'sell'):
        return -1.0
    return 0.0


def attribute_trade(trade_row, log_events, specialist_cfgs, bingx_cache):
    """Descompone PnL de un trade.

    Devuelve dict con todos los componentes. Usa NaN (no 0) para campos no
    disponibles. Setea 'analyzable' en {'full', 'partial', 'no'}.

    C1 Part B: entry_candle se infiere por infer_entry_candle():
      1. trade_row.entry_timestamp_ms (v2.3.3+)
      2. log: ultimo SIGNALS_EXECUTED LONG/SHORT del simbolo
      3. None -> entry_candle_no_inferible (trade excluido)

    C2: balance consistency check reemplazado por reconstruccion desde precios.
    """
    # Inferir entry_candle (C1 Part B)
    entry_candle, entry_src = infer_entry_candle(trade_row, log_events)

    flag_str = str(trade_row.get('flag') or '').strip().lower()
    out = {
        'ts': trade_row['timestamp'],
        'exit_cycle': trade_row['exit_cycle'],
        'entry_candle': entry_candle,
        'entry_candle_source': entry_src,     # 'csv' | 'log' | 'none'
        'symbol': trade_row['symbol'],
        'side': trade_row['side'],
        'size_usdt': float(trade_row['size_usdt']) if pd.notna(trade_row['size_usdt']) else np.nan,
        'entry_price_csv': float(trade_row['entry_price']) if pd.notna(trade_row['entry_price']) else np.nan,
        'exit_price_csv': float(trade_row['exit_price']) if pd.notna(trade_row['exit_price']) else np.nan,
        'pnl_real': float(trade_row['pnl_usdt']) if pd.notna(trade_row['pnl_usdt']) else np.nan,
        'pnl_pct': float(trade_row['pnl_pct']) if pd.notna(trade_row['pnl_pct']) else np.nan,
        'reason_exit': trade_row['reason_exit'],
        'flag': trade_row.get('flag', ''),
        'flag_reconstructed': flag_str in ('reconstructed_post_hoc', 'reconstructed'),
        'funding_paid_csv': float(trade_row['funding_paid']) if pd.notna(trade_row['funding_paid']) else np.nan,
        'cluster': None,
        'strategy': None,
        'active_config_id': None,
        'active_config_source': None,       # 'engine_state' | 'heuristic'
        'expectancy_pool_pct': np.nan,
        'expectancy_oos_pct': np.nan,
        'alpha_esperado_nominal': np.nan,
        'alpha_esperado_sized': np.nan,
        'coste_vol_targeting': np.nan,
        'coste_blending': np.nan,
        'coste_block_reduct': np.nan,
        'coste_dd_breaker': np.nan,
        'factor_portfolio': np.nan,
        'slippage_entry': np.nan,
        'slippage_exit': np.nan,
        'slippage_total': np.nan,
        'funding': np.nan,
        'alpha_residual': np.nan,
        'n_simultaneous_signals_in_cycle': np.nan,
        'analyzable': 'no',
        'missing_fields': [],
        'pnl_recon_gap': np.nan,      # C2: abs(pnl_csv - pnl_reconstruido)
        'pnl_recon_closes': False,    # C2: True si gap <= tolerance
    }

    # Caso entry_candle_no_inferible: trade excluido de atribucion
    if entry_candle is None:
        out['missing_fields'].append('entry_candle_no_inferible')
        out['analyzable'] = 'no'
        return out

    ss = side_sign(out['side'])
    if ss == 0.0:
        out['missing_fields'].append('side')
        return out

    # Timestamps
    sym = out['symbol']
    entry_cycle_key = entry_candle
    exit_cycle_key = out['exit_cycle']

    # 1. SIGNALS_RAW entry + cluster
    sr_entry = log_events['signals_raw'].get((entry_cycle_key, sym))
    cluster_id = None
    strategy = None
    if sr_entry:
        cluster_id = sr_entry.get('k')
        strategy = sr_entry.get('s')
    if cluster_id is None:
        # Fallback (b): GMM en el entry_candle
        cluster_id = classify_cluster_at_ts(sym, entry_cycle_key, bingx_cache)
    out['cluster'] = cluster_id

    # 2. Expectancy desde JSON (S6: heuristic por ahora, no hay active_config_id en logs)
    cfg = specialist_cfgs.get(sym)
    exp_pool, exp_oos, strat_from_cfg, cfg_meta = compute_expectancy(cfg, cluster_id)
    if strategy is None:
        strategy = strat_from_cfg
    out['strategy'] = strategy
    out['expectancy_pool_pct'] = exp_pool
    out['expectancy_oos_pct'] = exp_oos
    if cfg_meta:
        out['active_config_id'] = cfg_meta.get('config_id')
        out['active_config_source'] = 'heuristic'   # TODO v2.3.4: inyectar en SIGNALS_RAW

    if exp_pool is None:
        out['missing_fields'].append('expectancy')
        # No podemos computar alpha; sin embargo slippage/funding si podemos

    # 3. SIGNALS_EXECUTED del ciclo de entrada (multipliers y size)
    se_entry = log_events['signals_executed'].get((entry_cycle_key, sym))
    vw = bf = br = dd = None
    if se_entry:
        vw = float(se_entry.get('vw', 1.0))
        bf = float(se_entry.get('bf', 1.0))
        br = float(se_entry.get('br', 1.0))
        dd = float(se_entry.get('dd', 1.0))
    else:
        out['missing_fields'].append('signals_executed_entry')

    # 4. ENGINE_STATE del ciclo (balance, dd_mult)
    es = log_events['engine_states'].get(entry_cycle_key)
    balance_at_entry = None
    if es:
        balance_at_entry = float(es.get('bal', es.get('balance', 0.0)))
        if dd is None:
            dd = float(es.get('dd_mult', es.get('dd_multiplier', 1.0)))
    else:
        out['missing_fields'].append('engine_state_entry')

    # 5. nominal_cap (5% del balance al momento del trade)
    nominal_cap_usdt = None
    if balance_at_entry is not None and balance_at_entry > 0:
        nominal_cap_usdt = balance_at_entry * NOMINAL_CAP_FRAC

    # 6. Alpha nominal + capas de portfolio
    if exp_pool is not None and nominal_cap_usdt is not None:
        # expectancy es % por trade; alpha en USDT = exp_pct/100 * size_usdt
        exp_frac = exp_pool / 100.0
        alpha_nominal = exp_frac * nominal_cap_usdt
        out['alpha_esperado_nominal'] = alpha_nominal

        if vw is not None and bf is not None and br is not None and dd is not None:
            # Descomposicion telescopica
            out['coste_vol_targeting'] = alpha_nominal * (vw - 1.0)
            out['coste_blending']      = alpha_nominal * vw * (bf - 1.0)
            out['coste_block_reduct']  = alpha_nominal * vw * bf * (br - 1.0)
            out['coste_dd_breaker']    = alpha_nominal * vw * bf * br * (dd - 1.0)
            out['factor_portfolio'] = (out['coste_vol_targeting']
                                        + out['coste_blending']
                                        + out['coste_block_reduct']
                                        + out['coste_dd_breaker'])
            # alpha_esperado_sized = alpha_nominal + factor_portfolio = exp_frac * size_real
            out['alpha_esperado_sized'] = alpha_nominal + out['factor_portfolio']
        else:
            # Sin multipliers -> sized = nominal como aproximacion pobre
            out['factor_portfolio'] = 0.0
            out['alpha_esperado_sized'] = alpha_nominal
            if 'signals_executed_entry' not in out['missing_fields']:
                out['missing_fields'].append('multipliers')

    # 7. Slippage
    # Signal prices desde SIGNALS_RAW.p (entry) y SIGNALS_RAW.p del exit_cycle
    signal_entry_p = (sr_entry or {}).get('p')
    sr_exit = log_events['signals_raw'].get((exit_cycle_key, sym))
    signal_exit_p = (sr_exit or {}).get('p')

    entry_price_exec = float(trade_row['entry_price']) if pd.notna(trade_row['entry_price']) else None
    exit_price_exec = float(trade_row['exit_price']) if pd.notna(trade_row['exit_price']) else None

    contracts = None
    if out['size_usdt'] and not math.isnan(out['size_usdt']) and entry_price_exec and entry_price_exec > 0:
        contracts = out['size_usdt'] / entry_price_exec

    # slippage_entry = (signal_close - exec) * contracts * side_sign  (Q8 final)
    if signal_entry_p is not None and entry_price_exec is not None and contracts is not None:
        try:
            sep = float(signal_entry_p)
            out['slippage_entry'] = (sep - entry_price_exec) * contracts * ss
        except (TypeError, ValueError):
            out['missing_fields'].append('signal_entry_price')
    else:
        out['missing_fields'].append('signal_entry_price')

    # slippage_exit = (exec - signal_exit) * contracts * side_sign
    if signal_exit_p is not None and exit_price_exec is not None and contracts is not None:
        try:
            sxp = float(signal_exit_p)
            out['slippage_exit'] = (exit_price_exec - sxp) * contracts * ss
        except (TypeError, ValueError):
            out['missing_fields'].append('signal_exit_price')
    else:
        out['missing_fields'].append('signal_exit_price')

    se_filled = [s for s in (out['slippage_entry'], out['slippage_exit']) if not (s is None or (isinstance(s, float) and math.isnan(s)))]
    if len(se_filled) == 2:
        out['slippage_total'] = float(out['slippage_entry']) + float(out['slippage_exit'])
    else:
        # Si una pata falta, dejamos NaN en total (no asumir 0)
        pass

    # 8. Funding
    # FUNDING SIGN CONVENTION:
    # trade_history.csv column 'funding_paid' stores the ccxt `amount` tal cual
    # (execution_manager.py:164), donde la convencion ccxt es:
    #   amount < 0: trader PAGO funding (coste)
    #   amount > 0: trader RECIBIO funding (favorable)
    # Esto coincide exactamente con la convencion del analyzer (+ favorable,
    # - coste), por lo que el valor se usa DIRECTAMENTE sin invertir.
    if not (out['funding_paid_csv'] is None or math.isnan(out['funding_paid_csv'])):
        out['funding'] = out['funding_paid_csv']

    # 9. n_simultaneous_signals_in_cycle (nuevas aperturas)
    new_entries = new_entries_in_cycle(log_events, entry_cycle_key)
    out['n_simultaneous_signals_in_cycle'] = len(new_entries) if new_entries or (entry_cycle_key in {ts for ts, _ in log_events['signals_raw']}) else np.nan

    # 10. Alpha residual (definicion: lo que queda tras descontar componentes)
    nan_safe = lambda x: 0.0 if (x is None or (isinstance(x, float) and math.isnan(x))) else float(x)
    if not math.isnan(out['pnl_real']):
        residual = (out['pnl_real']
                    - nan_safe(out['alpha_esperado_nominal'])
                    - nan_safe(out['factor_portfolio'])
                    - nan_safe(out['slippage_total'])
                    - nan_safe(out['funding']))
        out['alpha_residual'] = residual

    # C2: consistency check por reconstruccion de precios (no tautologica).
    # pnl_reconstruido = (exit - entry) * contracts * side_sign - fees
    # Verifica que el pnl_usdt del CSV es coherente con los precios y tamanio
    # declarados, capturando errores de escritura, fees mal contabilizadas,
    # o desajuste contracts vs size_usdt.
    if (contracts is not None and contracts > 0
            and not math.isnan(out['entry_price_csv'])
            and not math.isnan(out['exit_price_csv'])
            and not math.isnan(out['pnl_real'])):
        notional_entry = contracts * out['entry_price_csv']
        est_fees = COMMISSION_RATE * notional_entry * 2.0  # round-trip
        pnl_recon = ((out['exit_price_csv'] - out['entry_price_csv'])
                     * contracts * ss) - est_fees
        # Tolerancia: 0.01 USDT absoluto o 10% del pnl, lo mayor de los dos
        tolerance = max(BALANCE_EQN_TOLERANCE_USDT, 0.1 * abs(out['pnl_real']))
        out['pnl_recon_gap'] = abs(pnl_recon - out['pnl_real'])
        out['pnl_recon_closes'] = out['pnl_recon_gap'] <= tolerance

    # 11. Analyzable level
    critical_missing = {'expectancy', 'signal_entry_price', 'signal_exit_price',
                        'signals_executed_entry', 'engine_state_entry', 'multipliers'}
    missed = critical_missing.intersection(out['missing_fields'])
    if not out['missing_fields']:
        out['analyzable'] = 'full'
    elif len(missed) >= 3:
        out['analyzable'] = 'no'
    else:
        out['analyzable'] = 'partial'

    return out


# ============================================================================
# 7. SATURACION COMPUTO (seccion f)
# ============================================================================

def compute_saturation_analysis(log_events, specialist_cfgs, bingx_cache,
                                 since_ts, until_ts,
                                 n_sat_threshold=DEFAULT_N_SATURATION):
    """Devuelve dict con f1 y f2 agregados + balance_req stats."""
    result = {
        'n_saturated_cycles': 0,
        'n_below_min_order_total': 0,
        'f1_alpha_perdido_total_usdt': 0.0,
        'f1_per_discard': [],   # lista de dicts
        'f2_counts': {'saturacion_N_signals': 0, 'dd_breaker_active': 0,
                      'balance_bajo_absoluto': 0, 'multiplicadores_no_estimables': 0},
        'f2_alpha_por_categoria': {'saturacion_N_signals': 0.0, 'dd_breaker_active': 0.0,
                                    'balance_bajo_absoluto': 0.0, 'multiplicadores_no_estimables': 0.0},
        'balance_req_cycles': [],   # list of (cycle_ts, balance_req_usdt)
        'cycles_sat_with_empirical_mult': 0,
        'cycles_sat_with_proxy_mult': 0,
        'cycles_sat_excluded_no_proxy': 0,
        'not_classifiable_discards': 0,
    }

    # Cubrir todos los ciclos con SIGNALS_DISCARDED o SIGNALS_RAW en ventana
    all_cycles = set()
    for (ts, _sym) in log_events['signals_discarded'].keys():
        if since_ts <= ts <= (until_ts or ts):
            all_cycles.add(ts)
    for (ts, _sym) in log_events['signals_raw'].keys():
        if since_ts <= ts <= (until_ts or ts):
            all_cycles.add(ts)

    for cycle_ts in sorted(all_cycles):
        entries = new_entries_in_cycle(log_events, cycle_ts)
        n_signals = len(entries)
        discards = discarded_in_cycle(log_events, cycle_ts)
        bmo = {s: i for s, i in discards.items()
               if i.get('d') == 'below_min_order'}

        is_saturated = n_signals >= n_sat_threshold
        if is_saturated:
            result['n_saturated_cycles'] += 1

        if not bmo:
            continue

        result['n_below_min_order_total'] += len(bmo)

        # Multipliers del ciclo
        mult_emp = cycle_multipliers_empirical(log_events, cycle_ts)
        if mult_emp is not None:
            result['cycles_sat_with_empirical_mult'] += 1 if is_saturated else 0
            multipliers = mult_emp
            mult_source = 'empirical'
        else:
            proxy, n_prev = proxy_multipliers_from_prev_cycles(log_events, cycle_ts)
            if proxy is not None:
                result['cycles_sat_with_proxy_mult'] += 1 if is_saturated else 0
                multipliers = proxy
                mult_source = f'proxy_{n_prev}_prev'
            else:
                result['cycles_sat_excluded_no_proxy'] += 1 if is_saturated else 0
                multipliers = None
                mult_source = 'excluded'

        # DD mult
        es = log_events['engine_states'].get(cycle_ts)
        dd_mult = float(es.get('dd_mult', es.get('dd_multiplier', 1.0))) if es else 1.0
        balance_at_cycle = float(es.get('bal', es.get('balance', 0.0))) if es else 0.0
        nominal_cap_usdt = balance_at_cycle * NOMINAL_CAP_FRAC if balance_at_cycle > 0 else None

        # Para cada below_min_order
        for sym, info in bmo.items():
            # Cluster del descarte (Q6 chain)
            sr_info = log_events['signals_raw'].get((cycle_ts, sym)) or {}
            cluster_id = sr_info.get('k')
            if cluster_id is None:
                cluster_id = classify_cluster_at_ts(sym, cycle_ts, bingx_cache)

            cfg = specialist_cfgs.get(sym)
            exp_pool, _exp_oos, strategy, _meta = compute_expectancy(cfg, cluster_id)

            if exp_pool is None or multipliers is None or nominal_cap_usdt is None:
                result['not_classifiable_discards'] += 1
                continue

            # f1 alpha_hubiera_sido
            exp_frac = exp_pool / 100.0
            alpha_hubiera = (exp_frac * nominal_cap_usdt
                             * multipliers['vw'] * multipliers['bf']
                             * multipliers['br'] * multipliers['dd'])
            result['f1_alpha_perdido_total_usdt'] += alpha_hubiera

            # S1: classify con multipliers (ya contempla proxy), no mult_emp
            category, sat_factor, dd_factor, rationale = classify_below_min_order_root_cause(
                n_signals, multipliers, dd_mult, n_sat_threshold)
            result['f2_counts'][category] += 1
            result['f2_alpha_por_categoria'][category] += alpha_hubiera

            result['f1_per_discard'].append({
                'cycle_ts': cycle_ts, 'symbol': sym,
                'cluster': cluster_id, 'strategy': strategy,
                'expectancy_pool_pct': exp_pool,
                'n_signals': n_signals,
                'alpha_hubiera_sido_usdt': alpha_hubiera,
                'mult_source': mult_source,
                'vw': multipliers['vw'], 'bf': multipliers['bf'],
                'br': multipliers['br'], 'dd': multipliers['dd'],
                'category': category, 'sat_factor': sat_factor, 'dd_factor': dd_factor,
                'rationale': rationale,
            })

        # S2: balance_req sin double-count de br.
        # Derivacion:
        #   Con balance B, cada senal recibe hasta (GLOBAL_CAP x B / n_signals) x vw x bf x dd.
        #   Queremos que esto >= MIN_ORDER_USDT.
        #   Despejando: B >= MIN_ORDER_USDT x n_signals / (GLOBAL_CAP x vw x bf x dd).
        #   br ya representa la reduccion 1/n_signals implicita en el global cap;
        #   incluirlo duplicaria el efecto de n_signals en el denominador.
        if is_saturated and multipliers is not None:
            vw = multipliers.get('vw', 1.0)
            bf = multipliers.get('bf', 1.0)
            dd = multipliers.get('dd', 1.0)
            mult_c_for_req = vw * bf * dd
            if mult_c_for_req > 0:
                balance_req = (MIN_ORDER_USDT * n_signals) / (GLOBAL_CAP_FRAC * mult_c_for_req)
                result['balance_req_cycles'].append((cycle_ts, balance_req))

    # Agregados balance_req
    if result['balance_req_cycles']:
        arr = np.array([b for _, b in result['balance_req_cycles']])
        result['balance_req_p50'] = float(np.percentile(arr, 50))
        result['balance_req_p95'] = float(np.percentile(arr, 95))
        result['balance_req_max'] = float(np.max(arr))
    else:
        result['balance_req_p50'] = None
        result['balance_req_p95'] = None
        result['balance_req_max'] = None

    return result


# ============================================================================
# 8. REPORTE
# ============================================================================

def _fmt(x, fmt="{:.4f}", na="N/A"):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return na
        return fmt.format(x)
    except Exception:
        return str(x)


def _fmt_ts(ts, na="N/A"):
    if ts is None:
        return na
    try:
        return pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M UTC')
    except Exception:
        return str(ts)


def write_report(report_path, ctx, alerts):
    lines = []

    def out(s=""):
        lines.append(s)

    def hr(c='='):
        out(c * 80)

    hr()
    out("ATRIBUCION DE PERFORMANCE -- REPORTE")
    hr()
    out(f"Generado:             {ctx['now_str']}")
    out(f"Ventana:              {_fmt_ts(ctx['since_ts'])} -> {_fmt_ts(ctx['until_ts'])}")
    out(f"Trades totales:       {ctx['n_total']}")
    out(f"Trades analizables:   {ctx['n_full']}+{ctx['n_partial']} (full+partial)")
    out(f"Trades no_analizables:{ctx['n_no']}")
    out()
    out("CONVENCION DE SIGNOS:")
    out("  slippage / factor_portfolio / funding / alpha_residual:")
    out("      + = favorable, - = coste")
    out("  pnl_real y alpha_esperado_*: valores absolutos en USDT")
    out()
    out("FORMULAS CLAVE:")
    out("  expectancy_pool = (pnl_tr + pnl_fwd) / (trades_tr + trades_fwd)  [%/trade]")
    out("  expectancy_oos  = pnl_fwd / trades_fwd                            [%/trade]")
    out("  alpha_nominal   = (expectancy_pool/100) * 0.05 * balance_at_entry")
    out("  alpha_sized     = alpha_nominal + factor_portfolio                 [= exp * size_real]")
    out()

    # ==== a) AGREGADO GLOBAL ====
    hr()
    out("(a) AGREGADO GLOBAL")
    hr()
    agg = ctx['aggregate']
    pnl_abs = abs(agg['pnl_total']) if agg['pnl_total'] != 0 else 1.0
    out(f"PnL total realizado:                         {_fmt(agg['pnl_total'], '{:+.2f}')} USDT")
    out(f"Alpha esperado nominal (suma):               {_fmt(agg['alpha_nominal_sum'], '{:+.2f}')} USDT "
        f"({_fmt(100*agg['alpha_nominal_sum']/pnl_abs, '{:+.1f}')}% de |PnL|)")
    out(f"Alpha esperado sized (suma):                 {_fmt(agg['alpha_sized_sum'], '{:+.2f}')} USDT")
    out()
    out("Descomposicion (todos en USDT y % de |PnL total|):")
    out(f"  Slippage entry:                            {_fmt(agg['slippage_entry'], '{:+.2f}')} "
        f"({_fmt(100*agg['slippage_entry']/pnl_abs, '{:+.1f}')}%)")
    out(f"  Slippage exit:                             {_fmt(agg['slippage_exit'], '{:+.2f}')} "
        f"({_fmt(100*agg['slippage_exit']/pnl_abs, '{:+.1f}')}%)")
    out(f"  Slippage TOTAL:                            {_fmt(agg['slippage_total'], '{:+.2f}')} "
        f"({_fmt(100*agg['slippage_total']/pnl_abs, '{:+.1f}')}%)")
    out(f"  Factor portfolio -- 4 capas:")
    out(f"    coste_vol_targeting:                     {_fmt(agg['coste_vol_targeting'], '{:+.2f}')}")
    out(f"    coste_blending:                          {_fmt(agg['coste_blending'], '{:+.2f}')}")
    out(f"    coste_block_reduct (incl. global cap):   {_fmt(agg['coste_block_reduct'], '{:+.2f}')}")
    out(f"    coste_dd_breaker:                        {_fmt(agg['coste_dd_breaker'], '{:+.2f}')}")
    out(f"    Factor portfolio TOTAL:                  {_fmt(agg['factor_portfolio'], '{:+.2f}')} "
        f"({_fmt(100*agg['factor_portfolio']/pnl_abs, '{:+.1f}')}%)")
    out(f"  Funding:                                   {_fmt(agg['funding'], '{:+.2f}')} "
        f"({_fmt(100*agg['funding']/pnl_abs, '{:+.1f}')}%)")
    out(f"  Alpha residual:                            {_fmt(agg['alpha_residual'], '{:+.2f}')} "
        f"({_fmt(100*agg['alpha_residual']/pnl_abs, '{:+.1f}')}%)")
    out()
    if agg['alpha_nominal_sum'] and agg['alpha_nominal_sum'] != 0:
        ratio = agg['alpha_residual'] / agg['alpha_nominal_sum']
        out(f"Ratio alpha_residual / alpha_nominal: {_fmt(ratio, '{:+.3f}')}  "
            "(~0 si modelo calibrado)")
    out()
    # C2 + S4: reporte de consistencia de precios separado de datos missing
    n_chk = agg.get('n_pnl_recon_checked', 0)
    n_bad = agg.get('n_pnl_recon_not_closing', 0)
    n_miss = agg.get('n_components_missing', 0)
    ratio_bad = (n_bad / max(n_chk, 1)) if n_chk > 0 else 0.0
    out(f"Consistencia de precios (C2): {n_bad}/{n_chk} trades con gap > tolerancia "
        f"({ratio_bad*100:.1f}%)")
    out(f"Datos de modelo incompletos: {n_miss} trades (excluidos del check)")
    out()

    # ==== b) POR SIMBOLO ====
    hr()
    out("(b) POR SIMBOLO  (ordenado por alpha_residual descendente)")
    hr()
    out(f"{'symbol':<12} {'N':>4} {'pnl':>10} {'alpha_nom':>10} {'alpha_res':>10} "
        f"{'res/nom':>10} {'flag':<15}")
    for row in ctx['per_symbol']:
        warn = ""
        if row['alpha_nominal'] and row['alpha_nominal'] != 0:
            ratio = row['alpha_residual'] / row['alpha_nominal']
            if ratio < -0.20:
                warn = "WARN_neg_res"
        out(f"{row['symbol']:<12} {row['n']:>4} "
            f"{_fmt(row['pnl'], '{:+.2f}'):>10} "
            f"{_fmt(row['alpha_nominal'], '{:+.2f}'):>10} "
            f"{_fmt(row['alpha_residual'], '{:+.2f}'):>10} "
            f"{_fmt(100*row['alpha_residual']/row['alpha_nominal'] if row['alpha_nominal'] else 0, '{:+.0f}%'):>10} "
            f"{warn:<15}")
    out()

    # ==== c) POR CLUSTER ====
    hr()
    out("(c) POR SIMBOLO x CLUSTER")
    hr()
    out(f"{'symbol':<12} {'cl':>3} {'N':>4} {'pnl':>10} {'alpha_nom':>10} {'alpha_res':>10} "
        f"{'res/nom':>10} {'exp_pool':>10} {'exp_oos':>10} {'ratio_oos':>10} {'flag':<25}")
    for row in ctx['per_cluster']:
        flag = ""
        if (row['alpha_nominal'] and row['alpha_nominal'] != 0 and
                row['n'] >= DEFAULT_MIN_N_CLUSTER_ALERTS):
            r = row['alpha_residual'] / row['alpha_nominal']
            if r < -0.20:
                flag = "candidato_exclusion"
        if (row['exp_pool'] and row['exp_oos'] is not None
                and row['n'] >= DEFAULT_MIN_N_EDGE_EROSION):
            ratio_oos = row['exp_oos'] / row['exp_pool'] if row['exp_pool'] else None
            if ratio_oos is not None and ratio_oos < EDGE_EROSION_RATIO_ALERT:
                flag = (flag + ", " if flag else "") + "edge_erosion"
        out(f"{row['symbol']:<12} {row['cluster'] if row['cluster'] is not None else '-':>3} "
            f"{row['n']:>4} "
            f"{_fmt(row['pnl'], '{:+.2f}'):>10} "
            f"{_fmt(row['alpha_nominal'], '{:+.2f}'):>10} "
            f"{_fmt(row['alpha_residual'], '{:+.2f}'):>10} "
            f"{_fmt(100*row['alpha_residual']/row['alpha_nominal'] if row['alpha_nominal'] else 0, '{:+.0f}%'):>10} "
            f"{_fmt(row['exp_pool'], '{:+.3f}'):>10} "
            f"{_fmt(row['exp_oos'], '{:+.3f}'):>10} "
            f"{_fmt(row['exp_oos']/row['exp_pool'] if (row['exp_pool'] and row['exp_oos'] is not None) else None, '{:.2f}'):>10} "
            f"{flag:<25}")
    out()

    # ==== d) COSTES DE EJECUCION ====
    hr()
    out("(d) COSTES DE EJECUCION -- Slippage por simbolo")
    hr()
    out(f"{'symbol':<12} {'N':>4} {'slip_entry_bp':>15} {'slip_exit_bp':>15} {'total_bp':>15} {'flag':<15}")
    for row in ctx['slippage_per_symbol']:
        flag = "alerta_slippage" if abs(row['total_bp']) > SLIPPAGE_BP_ALERT else ""
        out(f"{row['symbol']:<12} {row['n']:>4} "
            f"{_fmt(row['entry_bp'], '{:+.2f}'):>15} "
            f"{_fmt(row['exit_bp'], '{:+.2f}'):>15} "
            f"{_fmt(row['total_bp'], '{:+.2f}'):>15} "
            f"{flag:<15}")
    out()

    # ==== e) COSTES DE PORTFOLIO ====
    hr()
    out("(e) COSTES DE PORTFOLIO -- Desglose 4 capas")
    hr()
    out(f"  coste_vol_targeting:   {_fmt(agg['coste_vol_targeting'], '{:+.2f}')} USDT")
    out(f"  coste_blending:        {_fmt(agg['coste_blending'], '{:+.2f}')} USDT")
    out(f"  coste_block_reduct:    {_fmt(agg['coste_block_reduct'], '{:+.2f}')} USDT")
    out(f"  coste_dd_breaker:      {_fmt(agg['coste_dd_breaker'], '{:+.2f}')} USDT")
    # Capa mas costosa
    costs = {
        'vol_targeting': agg['coste_vol_targeting'],
        'blending': agg['coste_blending'],
        'block_reduct': agg['coste_block_reduct'],
        'dd_breaker': agg['coste_dd_breaker'],
    }
    neg_costs = [(k, v) for k, v in costs.items() if v is not None and v < 0]
    if neg_costs:
        worst = min(neg_costs, key=lambda kv: kv[1])
        out(f"  Capa mas costosa: {worst[0]} ({_fmt(worst[1], '{:+.2f}')} USDT)")
    # Blending check
    if (agg['alpha_nominal_sum'] and agg['alpha_nominal_sum'] > 0 and
            agg['coste_blending'] is not None):
        pct_blending = -agg['coste_blending'] / agg['alpha_nominal_sum'] * 100.0
        out(f"  coste_blending / alpha_nominal = {pct_blending:+.1f}% "
            f"(umbral alerta: {BLENDING_PCT_ALERT}%)")
    if agg['coste_dd_breaker'] is not None and agg['coste_dd_breaker'] < 0:
        out(f"  Alpha diferido/perdido por DD breaker: {_fmt(-agg['coste_dd_breaker'], '{:.2f}')} USDT")
    out()

    # ==== f) SATURACION ====
    hr()
    out("(f) SATURACION DE PORTFOLIO")
    hr()
    sat = ctx['saturation']
    out(f"Umbral N_threshold (aperturas simultaneas):        {ctx['n_sat_threshold']}")
    out(f"Ciclos con saturacion (N >= umbral):               {sat['n_saturated_cycles']}")
    out(f"Descartes below_min_order totales en ventana:      {sat['n_below_min_order_total']}")
    out()
    out("(f1) Alpha perdido especifico por below_min_order:")
    out(f"  Total USDT:                                      {_fmt(sat['f1_alpha_perdido_total_usdt'], '{:+.2f}')}")
    if agg['pnl_total'] and agg['pnl_total'] != 0:
        out(f"  Como % de |PnL realizado|:                       "
            f"{_fmt(100*sat['f1_alpha_perdido_total_usdt']/pnl_abs, '{:.1f}')}%")
    out(f"  Descartes no clasificables por cluster:          {sat['not_classifiable_discards']}")
    out()
    out("(f2) Desglose por categoria de causa raiz:")
    for cat in ('saturacion_N_signals', 'dd_breaker_active', 'balance_bajo_absoluto'):
        n = sat['f2_counts'][cat]
        a = sat['f2_alpha_por_categoria'][cat]
        out(f"  {cat:<30} N={n:>4}  alpha_perdido={_fmt(a, '{:+.2f}')} USDT")
    out()
    out("Proxy de multiplicadores en ciclos saturados:")
    out(f"  Con multipliers empiricos:                       {sat['cycles_sat_with_empirical_mult']}")
    out(f"  Con proxy de 5 ciclos previos:                   {sat['cycles_sat_with_proxy_mult']}")
    out(f"  Excluidos por falta de proxy:                    {sat['cycles_sat_excluded_no_proxy']}")
    total_cls = (sat['cycles_sat_with_empirical_mult']
                 + sat['cycles_sat_with_proxy_mult']
                 + sat['cycles_sat_excluded_no_proxy'])
    if total_cls > 0:
        pct_excluded = 100.0 * sat['cycles_sat_excluded_no_proxy'] / total_cls
        out(f"  % excluidos:                                     {pct_excluded:.1f}% "
            f"(umbral alerta: {NO_ESTIMABLE_PCT_ALERT}%)")
    out()
    out("Balance requerido para evitar saturacion (por ciclo):")
    out(f"  p50: {_fmt(sat['balance_req_p50'], '{:.0f}')} USDT")
    out(f"  p95: {_fmt(sat['balance_req_p95'], '{:.0f}')} USDT")
    out(f"  max: {_fmt(sat['balance_req_max'], '{:.0f}')} USDT")
    out()

    # ==== g) FUNDING ====
    hr()
    out("(g) COSTES DE FUNDING")
    hr()
    out(f"Funding total (signed):   {_fmt(agg['funding'], '{:+.2f}')} USDT")
    if agg['pnl_total'] and agg['pnl_total'] != 0:
        out(f"Funding / PnL neto:       {_fmt(100*agg['funding']/agg['pnl_total'], '{:+.1f}')}%")
    out()
    out(f"{'symbol':<12} {'funding':>10} {'pnl':>10} {'%_of_pnl':>10} {'flag':<15}")
    for row in ctx['funding_per_symbol']:
        pct = 100 * row['funding'] / row['pnl'] if row['pnl'] else None
        flag = "alerta_funding" if pct is not None and abs(pct) > FUNDING_PCT_ALERT else ""
        out(f"{row['symbol']:<12} "
            f"{_fmt(row['funding'], '{:+.2f}'):>10} "
            f"{_fmt(row['pnl'], '{:+.2f}'):>10} "
            f"{_fmt(pct, '{:+.1f}%'):>10} "
            f"{flag:<15}")
    out()

    # ==== h) BRAIN_RECONCILE ====
    hr()
    out("(h) FRECUENCIA DE [BRAIN_RECONCILE]")
    hr()
    out(f"{'fecha':<12} {'count':>6}")
    dates_sorted = sorted(ctx['brain_reconciles_per_day'].items())
    for d, n in dates_sorted:
        out(f"{str(d):<12} {n:>6}")
    if len(dates_sorted) >= 3:
        first_half = dates_sorted[:len(dates_sorted)//2]
        second_half = dates_sorted[len(dates_sorted)//2:]
        a1 = np.mean([n for _, n in first_half])
        a2 = np.mean([n for _, n in second_half])
        if a1 > 0:
            change = (a2 - a1) / a1 * 100.0
            trend = "CRECIENTE" if change > 10 else ("DECRECIENTE" if change < -10 else "ESTABLE")
            out(f"Tendencia (segunda mitad vs primera): {change:+.1f}% ({trend})")
            out("Interpretacion: alto y estable es esperable con balance bajo; "
                "si aumenta post-capitalizacion, investigar.")
    out()

    # ==== i) TRADES RECONSTRUIDOS ====
    hr()
    out("(i) TRADES RECONSTRUIDOS + ORPHAN_CLOSE")
    hr()
    out(f"Trades con flag=reconstructed_post_hoc: {ctx['n_reconstructed']}")
    for r in ctx['reconstructed_list']:
        out(f"    {_fmt_ts(r['ts']):<20} {r['symbol']:<12} {r['side']:<6} "
            f"pnl={_fmt(r['pnl_real'], '{:+.2f}')} reason={r['reason_exit']}")
    out(f"Eventos [ORPHAN_CLOSE] en log: {ctx['n_orphan_close']}")
    out()

    # ==== NEXT STEPS ====
    hr()
    out("NEXT STEPS -- CHECKS AUTOMATICOS")
    hr()
    for a in alerts['ascii']:
        out(f"  {a}")
    if not alerts['ascii']:
        out("  (Ninguna alerta disparada.)")
    out()
    hr()

    # Escribir ASCII
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    # Escribir UTF-8 con emojis (reemplazar alerts ASCII por UTF-8)
    utf8_path = report_path.replace('.txt', '_utf8.txt')
    with open(utf8_path, 'w', encoding='utf-8') as f:
        content = '\n'.join(lines)
        for a_ascii, a_utf in zip(alerts['ascii'], alerts['utf8']):
            content = content.replace(a_ascii, a_utf)
        f.write(content + '\n')

    return report_path, utf8_path


# ============================================================================
# 9. ALERTS (NEXT STEPS)
# ============================================================================

def build_alerts(ctx):
    alerts_ascii = []
    alerts_utf = []
    agg = ctx['aggregate']
    sat = ctx['saturation']

    def add(ascii_text, utf_text):
        alerts_ascii.append(ascii_text)
        alerts_utf.append(utf_text)

    # 1. Slippage
    pnl_bruto = agg.get('alpha_nominal_sum', 0.0) or 0.0
    slippage_abs = abs(agg.get('slippage_total', 0.0) or 0.0)
    if pnl_bruto != 0 and slippage_abs / max(abs(pnl_bruto), 1e-9) > 0.15:
        add(f"[EXEC] INVESTIGAR EJECUCION. Slippage total {_fmt(agg['slippage_total'], '{:+.2f}')} USDT "
            f"= {_fmt(100*slippage_abs/abs(pnl_bruto), '{:.1f}')}% del PnL bruto. Posible problema "
            "con ordenes a mercado en volatilidad alta.",
            f"\U0001f527 INVESTIGAR EJECUCION. Slippage total {_fmt(agg['slippage_total'], '{:+.2f}')} USDT "
            f"= {_fmt(100*slippage_abs/abs(pnl_bruto), '{:.1f}')}% del PnL bruto.")

    # 2. Blending
    if agg.get('alpha_nominal_sum') and agg['alpha_nominal_sum'] > 0 and agg.get('coste_blending'):
        pct = -agg['coste_blending'] / agg['alpha_nominal_sum'] * 100.0
        if pct > BLENDING_PCT_ALERT:
            add(f"[CFG] BLENDING DEMASIADO AGRESIVO. coste_blending = {pct:.1f}% del alpha nominal. "
                "Considerar subir thresholds de confianza en portfolio_manager.",
                f"\U0001f527 BLENDING DEMASIADO AGRESIVO. coste_blending = {pct:.1f}% del alpha nominal.")

    # 3. DD breaker (M9: umbral minimo para evitar ruido)
    dd_cost = agg.get('coste_dd_breaker')
    n_dd = agg.get('n_trades_with_dd_reduction', 0)
    if (dd_cost is not None and dd_cost < 0 and
            (abs(dd_cost) > MIN_DD_BREAKER_COST_FOR_ALERT or n_dd >= MIN_DD_BREAKER_N_TRADES)):
        add(f"[STAT] CIRCUIT BREAKER ACTIVO. Impacto: "
            f"{_fmt(-dd_cost, '{:.2f}')} USDT de alpha diferido/perdido en {n_dd} trades.",
            f"\U0001f4ca CIRCUIT BREAKER ACTIVO. {_fmt(-dd_cost, '{:.2f}')} USDT de alpha diferido ({n_dd} trades).")

    # 4. Saturacion -> capitalizar (S7: safeguards de muestra y PnL)
    alpha_lost_sat = sat['f2_alpha_por_categoria']['saturacion_N_signals']
    n_trades = agg.get('n_trades_analyzed', 0)
    pnl_total = agg.get('pnl_total', 0.0) or 0.0
    if alpha_lost_sat > 0 and agg.get('alpha_nominal_sum') and agg['alpha_nominal_sum'] > 0:
        if n_trades < MIN_TRADES_FOR_CAPITALIZE_ALERT:
            pass  # muestra insuficiente, no disparar
        elif abs(pnl_total) < MIN_PNL_ABS_FOR_CAPITALIZE_ALERT:
            pass  # pnl cercano a 0, ratio seria ruidoso
        else:
            pct_of_realized = 100.0 * alpha_lost_sat / abs(pnl_total)
            if pct_of_realized > CAPITALIZE_PCT_THRESHOLD:
                p95 = sat.get('balance_req_p95') or 0
                add(f"[$$$] CAPITALIZAR CUENTA. Saturacion del portfolio impidiendo capturar "
                    f"{_fmt(alpha_lost_sat, '{:.2f}')} USDT de alpha "
                    f"({pct_of_realized:.1f}% del PnL realizado, N={n_trades}). "
                    f"Balance optimo minimo estimado (p95): {p95:.0f} USDT. "
                    "Supone distribucion futura de senales simultaneas similar a la ventana observada.",
                    f"\U0001f4b0 CAPITALIZAR CUENTA. Saturacion impidiendo {_fmt(alpha_lost_sat, '{:.2f}')} USDT. "
                    f"Balance p95 sugerido: {p95:.0f} USDT.")

    # 5. Cluster candidato exclusion
    candidatos = []
    for row in ctx['per_cluster']:
        if (row['alpha_nominal'] and row['alpha_nominal'] != 0 and
                row['n'] >= DEFAULT_MIN_N_CLUSTER_ALERTS):
            r = row['alpha_residual'] / row['alpha_nominal']
            if r < -0.20:
                candidatos.append(f"{row['symbol']} C{row['cluster']}")
    if candidatos:
        add(f"[ALERT] CANDIDATO EXCLUSION RECICLAJE: {', '.join(candidatos)}",
            f"\U0001f6a8 CANDIDATO EXCLUSION RECICLAJE: {', '.join(candidatos)}")

    # 6. Funding
    if agg.get('funding') is not None and agg.get('pnl_total'):
        pct = 100.0 * agg['funding'] / agg['pnl_total'] if agg['pnl_total'] != 0 else 0.0
        if abs(pct) > FUNDING_PCT_ALERT:
            add(f"[CFG] ACELERAR v2.6 FILTRO FUNDING. funding / pnl_neto = {pct:+.1f}%",
                f"\U0001f527 ACELERAR v2.6 FILTRO FUNDING. funding / pnl_neto = {pct:+.1f}%")

    # 7. Edge erosion temporal
    if ctx.get('edge_erosion_flag'):
        add("[WARN] EDGE EROSIONANDOSE. Alpha residual cae > 10% en los ultimos 20 trades "
            "vs los 20 previos. Considerar reciclaje anticipado.",
            "\u26a0\ufe0f  EDGE EROSIONANDOSE. Alpha residual cae > 10% en los ultimos 20 trades.")

    # 8. Edge erosion por cluster
    erosion_clusters = []
    for row in ctx['per_cluster']:
        if (row['exp_pool'] and row['exp_oos'] is not None
                and row['n'] >= DEFAULT_MIN_N_EDGE_EROSION):
            ratio_oos = row['exp_oos'] / row['exp_pool'] if row['exp_pool'] else None
            if ratio_oos is not None and ratio_oos < EDGE_EROSION_RATIO_ALERT:
                erosion_clusters.append(f"{row['symbol']} C{row['cluster']}")
    if erosion_clusters:
        add(f"[WARN] EDGE EROSION en clusters: {', '.join(erosion_clusters)}",
            f"\u26a0\ufe0f  EDGE EROSION en clusters: {', '.join(erosion_clusters)}")

    # 9. Proxy no estimable
    total_cls = (sat['cycles_sat_with_empirical_mult']
                 + sat['cycles_sat_with_proxy_mult']
                 + sat['cycles_sat_excluded_no_proxy'])
    if total_cls > 0:
        pct_excluded = 100.0 * sat['cycles_sat_excluded_no_proxy'] / total_cls
        if pct_excluded > NO_ESTIMABLE_PCT_ALERT:
            add(f"[WARN] NO_ESTIMABLE_RATIO_ALTO: {pct_excluded:.1f}% de ciclos saturados sin "
                "multiplicadores estimables. Instrumentar v2.3.3 para loguear vw/bf/br/dd en "
                "[SIGNALS_DISCARDED].",
                f"\u26a0\ufe0f  NO_ESTIMABLE_RATIO_ALTO: {pct_excluded:.1f}%. Instrumentar v2.3.3.")

    return {'ascii': alerts_ascii, 'utf8': alerts_utf}


# ============================================================================
# 10. AGREGACION
# ============================================================================

def aggregate_trades(per_trade):
    """Devuelve dict 'aggregate' con sumas globales + listas per_symbol/per_cluster."""
    def sum_ns(key):
        vals = [r[key] for r in per_trade if r.get(key) is not None
                and not (isinstance(r[key], float) and math.isnan(r[key]))]
        return float(sum(vals)) if vals else 0.0

    agg = {
        'pnl_total': sum_ns('pnl_real'),
        'alpha_nominal_sum': sum_ns('alpha_esperado_nominal'),
        'alpha_sized_sum': sum_ns('alpha_esperado_sized'),
        'slippage_entry': sum_ns('slippage_entry'),
        'slippage_exit': sum_ns('slippage_exit'),
        'slippage_total': sum_ns('slippage_total'),
        'coste_vol_targeting': sum_ns('coste_vol_targeting'),
        'coste_blending': sum_ns('coste_blending'),
        'coste_block_reduct': sum_ns('coste_block_reduct'),
        'coste_dd_breaker': sum_ns('coste_dd_breaker'),
        'factor_portfolio': sum_ns('factor_portfolio'),
        'funding': sum_ns('funding'),
        'alpha_residual': sum_ns('alpha_residual'),
        # S4: split counters. pnl_recon_closes se setea solo si tenemos precios
        # y pnl (no requiere componentes del modelo). Un NaN en pnl_recon_gap
        # significa "no chequeable" (missing prices), no "gap".
        'n_pnl_recon_checked': sum(
            1 for r in per_trade if r.get('pnl_recon_gap') is not None
            and not (isinstance(r.get('pnl_recon_gap'), float) and math.isnan(r['pnl_recon_gap']))
        ),
        'n_pnl_recon_not_closing': sum(
            1 for r in per_trade
            if r.get('pnl_recon_gap') is not None
            and not (isinstance(r.get('pnl_recon_gap'), float) and math.isnan(r['pnl_recon_gap']))
            and not r.get('pnl_recon_closes', False)
        ),
        'n_components_missing': sum(
            1 for r in per_trade if r.get('analyzable') != 'full'
        ),
        'n_trades_with_dd_reduction': sum(
            1 for r in per_trade
            if r.get('coste_dd_breaker') is not None
            and not (isinstance(r['coste_dd_breaker'], float) and math.isnan(r['coste_dd_breaker']))
            and r['coste_dd_breaker'] < 0
        ),
        'n_trades_analyzed': len([r for r in per_trade if r.get('analyzable') in ('full', 'partial')]),
    }

    # Per-symbol
    per_symbol = {}
    for r in per_trade:
        s = r['symbol']
        rec = per_symbol.setdefault(s, {'symbol': s, 'n': 0, 'pnl': 0.0,
                                         'alpha_nominal': 0.0, 'alpha_residual': 0.0,
                                         'slippage_entry_bp_num': 0.0, 'slippage_entry_bp_den': 0.0,
                                         'slippage_exit_bp_num': 0.0, 'slippage_exit_bp_den': 0.0,
                                         'funding': 0.0})
        rec['n'] += 1
        if r.get('pnl_real') is not None and not math.isnan(r['pnl_real']):
            rec['pnl'] += r['pnl_real']
        if r.get('alpha_esperado_nominal') is not None and not math.isnan(r['alpha_esperado_nominal']):
            rec['alpha_nominal'] += r['alpha_esperado_nominal']
        if r.get('alpha_residual') is not None and not math.isnan(r['alpha_residual']):
            rec['alpha_residual'] += r['alpha_residual']
        if r.get('funding') is not None and not math.isnan(r['funding']):
            rec['funding'] += r['funding']
        # Slippage en bp sobre size_usdt
        if (r.get('slippage_entry') is not None and not math.isnan(r['slippage_entry'])
                and r.get('size_usdt') and not math.isnan(r['size_usdt']) and r['size_usdt'] > 0):
            rec['slippage_entry_bp_num'] += r['slippage_entry'] * 10000.0
            rec['slippage_entry_bp_den'] += r['size_usdt']
        if (r.get('slippage_exit') is not None and not math.isnan(r['slippage_exit'])
                and r.get('size_usdt') and not math.isnan(r['size_usdt']) and r['size_usdt'] > 0):
            rec['slippage_exit_bp_num'] += r['slippage_exit'] * 10000.0
            rec['slippage_exit_bp_den'] += r['size_usdt']

    per_symbol_list = []
    for s, rec in per_symbol.items():
        rec['entry_bp'] = (rec['slippage_entry_bp_num'] / rec['slippage_entry_bp_den']
                           if rec['slippage_entry_bp_den'] > 0 else None)
        rec['exit_bp'] = (rec['slippage_exit_bp_num'] / rec['slippage_exit_bp_den']
                          if rec['slippage_exit_bp_den'] > 0 else None)
        rec['total_bp'] = ((rec['entry_bp'] or 0.0) + (rec['exit_bp'] or 0.0)
                           if (rec['entry_bp'] is not None and rec['exit_bp'] is not None) else None)
        per_symbol_list.append(rec)
    per_symbol_list.sort(key=lambda x: (x['alpha_residual'] or 0.0), reverse=True)

    # Per-cluster (symbol, cluster)
    per_cluster = {}
    for r in per_trade:
        key = (r['symbol'], r.get('cluster'))
        rec = per_cluster.setdefault(key, {'symbol': r['symbol'], 'cluster': r.get('cluster'),
                                            'n': 0, 'pnl': 0.0,
                                            'alpha_nominal': 0.0, 'alpha_residual': 0.0,
                                            'exp_pool_sum': 0.0, 'exp_oos_sum': 0.0,
                                            'exp_pool_n': 0, 'exp_oos_n': 0})
        rec['n'] += 1
        if r.get('pnl_real') is not None and not math.isnan(r['pnl_real']):
            rec['pnl'] += r['pnl_real']
        if r.get('alpha_esperado_nominal') is not None and not math.isnan(r['alpha_esperado_nominal']):
            rec['alpha_nominal'] += r['alpha_esperado_nominal']
        if r.get('alpha_residual') is not None and not math.isnan(r['alpha_residual']):
            rec['alpha_residual'] += r['alpha_residual']
        if r.get('expectancy_pool_pct') is not None and not math.isnan(r['expectancy_pool_pct']):
            rec['exp_pool_sum'] += r['expectancy_pool_pct']
            rec['exp_pool_n'] += 1
        if r.get('expectancy_oos_pct') is not None and not math.isnan(r['expectancy_oos_pct']):
            rec['exp_oos_sum'] += r['expectancy_oos_pct']
            rec['exp_oos_n'] += 1
    per_cluster_list = []
    for key, rec in per_cluster.items():
        rec['exp_pool'] = rec['exp_pool_sum'] / rec['exp_pool_n'] if rec['exp_pool_n'] > 0 else None
        rec['exp_oos'] = rec['exp_oos_sum'] / rec['exp_oos_n'] if rec['exp_oos_n'] > 0 else None
        per_cluster_list.append(rec)
    per_cluster_list.sort(key=lambda x: (x['symbol'], x['cluster'] if x['cluster'] is not None else -1))

    # Funding per symbol
    funding_per_symbol = [{'symbol': s, 'funding': rec['funding'], 'pnl': rec['pnl']}
                          for s, rec in per_symbol.items()]
    funding_per_symbol.sort(key=lambda x: abs(x['funding'] or 0.0), reverse=True)

    # Slippage per symbol (subset de per_symbol_list)
    slippage_per_symbol = []
    for s, rec in per_symbol.items():
        if rec.get('total_bp') is None:
            continue
        slippage_per_symbol.append({
            'symbol': s, 'n': rec['n'],
            'entry_bp': rec['entry_bp'], 'exit_bp': rec['exit_bp'],
            'total_bp': rec['total_bp'],
        })
    slippage_per_symbol.sort(key=lambda x: abs(x['total_bp']), reverse=True)

    return agg, per_symbol_list, per_cluster_list, funding_per_symbol, slippage_per_symbol


# ============================================================================
# 11. EDGE EROSION TEMPORAL
# ============================================================================

def detect_edge_erosion(per_trade, last_n=EDGE_EROSION_LAST_N, drop=EDGE_EROSION_DROP):
    """Devuelve True si alpha_residual promedio de ultimos N cae > drop vs N previos."""
    sorted_trades = sorted(per_trade, key=lambda r: r['ts'])
    vals = [r['alpha_residual'] for r in sorted_trades
            if r.get('alpha_residual') is not None and not math.isnan(r['alpha_residual'])]
    if len(vals) < 2 * last_n:
        return False
    recent = np.mean(vals[-last_n:])
    prev = np.mean(vals[-2*last_n:-last_n])
    if prev == 0:
        return False
    return (recent - prev) / abs(prev) < -drop


# ============================================================================
# 12. PLOT
# ============================================================================

def plot_timeline(per_trade, path):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"[PLOT] matplotlib no disponible ({e}), saltando grafico")
        return False

    sorted_trades = sorted(per_trade, key=lambda r: r['ts'])
    ts = [r['ts'] for r in sorted_trades]
    pnl_cum = np.cumsum([r['pnl_real'] if r.get('pnl_real') is not None
                         and not math.isnan(r['pnl_real']) else 0.0 for r in sorted_trades])
    alpha_cum = np.cumsum([r['alpha_esperado_nominal'] if r.get('alpha_esperado_nominal') is not None
                            and not math.isnan(r['alpha_esperado_nominal']) else 0.0
                            for r in sorted_trades])
    res_cum = np.cumsum([r['alpha_residual'] if r.get('alpha_residual') is not None
                          and not math.isnan(r['alpha_residual']) else 0.0
                          for r in sorted_trades])

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(ts, pnl_cum, label='PnL realizado (cum)', color='black', linewidth=2)
    ax.plot(ts, alpha_cum, label='Alpha nominal esperado (cum)', color='blue', linestyle='--')
    ax.plot(ts, res_cum, label='Alpha residual (cum)', color='red', linewidth=1)
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.set_xlabel('Trade ts')
    ax.set_ylabel('USDT (cumulative)')
    ax.set_title('Performance Attribution -- Timeline Cumulativo')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    return True


# ============================================================================
# 13. MAIN
# ============================================================================

def parse_iso_ts(s):
    if s is None:
        return None
    ts = pd.Timestamp(s)
    if ts.tzinfo is None:
        ts = ts.tz_localize('UTC')
    return ts


def run(args):
    global COMBOLAB_DIR, DEFAULT_JSON_DIR, REGIME_MODELS_DIR
    print("=" * 70)
    print("ANALYZER DE PERFORMANCE ATTRIBUTION")
    print("=" * 70)

    # C3: Resolver COMBOLAB_DIR prioridad CLI > env > default
    if args.combolab_dir:
        COMBOLAB_DIR = os.path.abspath(args.combolab_dir)
        if COMBOLAB_DIR not in sys.path:
            sys.path.insert(0, COMBOLAB_DIR)
        DEFAULT_JSON_DIR, REGIME_MODELS_DIR = _resolve_paths()
    if not os.path.isdir(COMBOLAB_DIR):
        print(f"ERROR: COMBOLAB_DIR no existe: {COMBOLAB_DIR}", file=sys.stderr)
        print("  Opciones para configurar:", file=sys.stderr)
        print("  1. --combolab-dir PATH", file=sys.stderr)
        print("  2. export COMBOLAB_DIR=PATH", file=sys.stderr)
        print(f"  3. Default: {_DEFAULT_COMBOLAB} (no existe)", file=sys.stderr)
        sys.exit(2)
    print(f"COMBOLAB_DIR: {COMBOLAB_DIR}")

    since_ts = parse_iso_ts(args.since) or parse_iso_ts(DEFAULT_SINCE_ISO)
    until_ts = parse_iso_ts(args.until) if args.until else None

    # 1. Log
    log_path = args.logs
    if not log_path:
        for p in DEFAULT_ENGINE_LOG_CANDIDATES:
            if os.path.exists(p):
                log_path = p
                break
    log_start_date = (pd.Timestamp(args.log_start_date) if args.log_start_date
                      else pd.Timestamp(since_ts.date()))
    print(f"\nEngine log: {log_path or '(ninguno)'}")
    log_events = parse_engine_log(log_path, log_start_date)
    print(f"  engine_states={len(log_events['engine_states'])}  "
          f"signals_raw={len(log_events['signals_raw'])}  "
          f"signals_discarded={len(log_events['signals_discarded'])}  "
          f"signals_executed={len(log_events['signals_executed'])}  "
          f"brain_reconciles={len(log_events['brain_reconciles'])}  "
          f"orphan_closes={len(log_events['orphan_closes'])}")

    # 2. Trades
    trades = load_trades(args.trades or DEFAULT_TRADE_CSV, since_ts, until_ts)
    print(f"\nTrades en ventana: {len(trades)}")

    # 3. Specialist configs
    specialist_cfgs = load_all_specialist_configs(args.json_dir or DEFAULT_JSON_DIR)
    print(f"Specialist configs cargados: {len(specialist_cfgs)}")

    # S5: verificar unidades empiricamente antes de interpretar resultados
    units_ok, units_range, units_n, units_msgs = validate_pnl_units(specialist_cfgs)
    for msg in units_msgs:
        print(msg)
    if not units_ok and units_n > 0:
        print("[UNITS][ERROR] Unidades fuera de rango. Abortar para evitar reportes sesgados.",
              file=sys.stderr)
        # No abortamos por defecto; solo warn. El usuario decide.

    # 4. BingX cache (para fallback GMM). Si hay regime_cache local, usarlo.
    # Por simplicidad: no descargar, solo usar si hay parquet local.
    bingx_cache = {}
    cache_dir = os.path.join(COMBOLAB_DIR, 'data_cache')
    if os.path.isdir(cache_dir):
        for sym in trades['symbol'].unique():
            sym_clean = sym.replace('/', '')
            parquet_path = os.path.join(cache_dir, f"{sym_clean}_1h.parquet")
            if os.path.exists(parquet_path):
                try:
                    df = pd.read_parquet(parquet_path)
                    if 'timestamp' not in df.columns and 'ts' in df.columns:
                        df = df.rename(columns={'ts': 'timestamp'})
                    if df['timestamp'].dt.tz is None:
                        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
                    bingx_cache[sym] = df
                except Exception:
                    pass
    print(f"Data cache GMM fallback: {len(bingx_cache)} simbolos")

    # 5. Atribucion por trade
    print("\nAtribuyendo trades...")
    per_trade_all = []
    for _, row in trades.iterrows():
        attr = attribute_trade(row, log_events, specialist_cfgs, bingx_cache)
        per_trade_all.append(attr)

    # S3: excluir reconstructed_post_hoc de agregados si --exclude-reconstructed
    reconstructed_excluded = []
    if args.exclude_reconstructed:
        per_trade = []
        for r in per_trade_all:
            if r.get('flag_reconstructed'):
                reconstructed_excluded.append(r)
            else:
                per_trade.append(r)
        print(f"  Excluidos por flag=reconstructed_post_hoc: {len(reconstructed_excluded)}")
    else:
        per_trade = per_trade_all

    # Stats entry_candle source
    n_csv = sum(1 for r in per_trade if r.get('entry_candle_source') == 'csv')
    n_log = sum(1 for r in per_trade if r.get('entry_candle_source') == 'log')
    n_none = sum(1 for r in per_trade if r.get('entry_candle_source') == 'none')
    print(f"  entry_candle source: csv={n_csv} log={n_log} none={n_none}")

    n_full = sum(1 for r in per_trade if r['analyzable'] == 'full')
    n_partial = sum(1 for r in per_trade if r['analyzable'] == 'partial')
    n_no = sum(1 for r in per_trade if r['analyzable'] == 'no')
    print(f"  full={n_full}  partial={n_partial}  no={n_no}")

    # 6. Saturacion
    print("Analizando saturacion...")
    saturation = compute_saturation_analysis(
        log_events, specialist_cfgs, bingx_cache,
        since_ts, until_ts, args.n_saturation
    )
    print(f"  ciclos saturados={saturation['n_saturated_cycles']}  "
          f"below_min_order={saturation['n_below_min_order_total']}")

    # 7. Agregacion
    agg, per_symbol, per_cluster, funding_per_symbol, slippage_per_symbol = aggregate_trades(per_trade)

    # 8. Edge erosion
    edge_erosion_flag = detect_edge_erosion(per_trade)

    # 9. Reconstruidos: listar desde todos los trades (incluyendo excluidos) para trazabilidad
    source_for_recon = per_trade_all if args.exclude_reconstructed else per_trade
    reconstructed_list = [{'ts': r['ts'], 'symbol': r['symbol'], 'side': r['side'],
                           'pnl_real': r['pnl_real'], 'reason_exit': r['reason_exit']}
                          for r in source_for_recon if r.get('flag_reconstructed')]
    n_orphan_close = len(log_events['orphan_closes'])

    # 10. Brain reconciles by day
    brain_reconciles_per_day = dict(log_events['brain_reconciles_per_day'])

    # 11. Contexto reporte
    now = datetime.now(timezone.utc)
    ctx = {
        'now_str': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'since_ts': since_ts,
        'until_ts': until_ts,
        'n_total': len(per_trade),
        'n_full': n_full, 'n_partial': n_partial, 'n_no': n_no,
        'aggregate': agg,
        'per_symbol': per_symbol,
        'per_cluster': per_cluster,
        'funding_per_symbol': funding_per_symbol,
        'slippage_per_symbol': slippage_per_symbol,
        'saturation': saturation,
        'n_sat_threshold': args.n_saturation,
        'edge_erosion_flag': edge_erosion_flag,
        'brain_reconciles_per_day': brain_reconciles_per_day,
        'n_reconstructed': len(reconstructed_list),
        'reconstructed_list': reconstructed_list,
        'n_orphan_close': n_orphan_close,
    }

    # 12. Alerts
    alerts = build_alerts(ctx)

    # 13. Escribir CSV y reporte
    ts_stamp = now.strftime('%Y%m%d_%H%M')
    csv_path = os.path.join(THIS_DIR, f"attribution_per_trade_{ts_stamp}.csv")
    # CSV per_trade: 26 columnas (23 antes + entry_candle_source +
    # active_config_source + pnl_recon_* reemplazando balance_*).
    df_out = pd.DataFrame([{
        'ts': r['ts'], 'symbol': r['symbol'], 'side': r['side'],
        'cluster': r['cluster'], 'strategy': r['strategy'],
        'active_config_id': r.get('active_config_id'),
        'active_config_source': r.get('active_config_source'),
        'entry_candle': r.get('entry_candle'),
        'entry_candle_source': r.get('entry_candle_source'),
        'size_usdt': r['size_usdt'], 'pnl_real': r['pnl_real'],
        'alpha_esperado_nominal': r['alpha_esperado_nominal'],
        'alpha_esperado_sized': r['alpha_esperado_sized'],
        'slippage_entry': r['slippage_entry'],
        'slippage_exit': r['slippage_exit'],
        'coste_vol_targeting': r['coste_vol_targeting'],
        'coste_blending': r['coste_blending'],
        'coste_block_reduct': r['coste_block_reduct'],
        'coste_dd_breaker': r['coste_dd_breaker'],
        'factor_portfolio': r['factor_portfolio'],
        'funding': r['funding'],
        'alpha_residual': r['alpha_residual'],
        'flag_reconstructed': r['flag_reconstructed'],
        'n_simultaneous_signals_in_cycle': r['n_simultaneous_signals_in_cycle'],
        'analyzable': r['analyzable'],
        'pnl_recon_closes': r.get('pnl_recon_closes', False),
        'pnl_recon_gap': r.get('pnl_recon_gap'),
        'missing_fields': ';'.join(r['missing_fields']),
    } for r in per_trade])
    df_out.to_csv(csv_path, index=False)
    print(f"\nCSV: {csv_path}")

    report_path = os.path.join(THIS_DIR, f"attribution_summary_{ts_stamp}.txt")
    ascii_path, utf8_path = write_report(report_path, ctx, alerts)
    print(f"Report ASCII: {ascii_path}")
    print(f"Report UTF-8: {utf8_path}")

    if not args.no_plots:
        plot_path = os.path.join(THIS_DIR, f"attribution_timeline_{ts_stamp}.png")
        ok = plot_timeline(per_trade, plot_path)
        if ok:
            print(f"Plot: {plot_path}")

    # 14. Consistency check warning (C2: reconstruccion por precios)
    n_chk = agg.get('n_pnl_recon_checked', 0)
    n_bad = agg.get('n_pnl_recon_not_closing', 0)
    ratio_bad = (n_bad / max(n_chk, 1)) if n_chk > 0 else 0.0
    if ratio_bad > BALANCE_NOT_CLOSING_RATIO_ALERT:
        print(f"\nWARN: {n_bad}/{n_chk} trades ({ratio_bad*100:.1f}%) con pnl_recon_gap "
              f"> tolerancia. Posible problema en precios/fees del CSV.")
    elif n_bad > 0:
        print(f"\nNOTA: {n_bad}/{n_chk} trades con pnl_recon_gap > tolerancia (ratio OK).")

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"PnL total: {_fmt(agg['pnl_total'], '{:+.2f}')} USDT")
    print(f"Alpha nominal: {_fmt(agg['alpha_nominal_sum'], '{:+.2f}')}")
    print(f"Factor portfolio: {_fmt(agg['factor_portfolio'], '{:+.2f}')}")
    print(f"Slippage total: {_fmt(agg['slippage_total'], '{:+.2f}')}")
    print(f"Funding: {_fmt(agg['funding'], '{:+.2f}')}")
    print(f"Alpha residual: {_fmt(agg['alpha_residual'], '{:+.2f}')}")
    print(f"\nAlerts: {len(alerts['ascii'])}")
    for a in alerts['ascii']:
        print(f"  {a}")


def main():
    p = argparse.ArgumentParser(description="Performance attribution analyzer (offline)")
    p.add_argument('--trades', default=None, help="path a trade_history.csv")
    p.add_argument('--logs', default=None,
                   help="path a engine.log. A36: acepta archivo unico, glob "
                        "pattern (ej. 'logs/engine.log*') o CSV "
                        "('logs/engine.log.1,logs/engine.log'). Rotados .gz "
                        "transparentes. Orden cronologico ASC automatico.")
    p.add_argument('--json-dir', default=None, help="directorio con specialist_configs JSONs")
    p.add_argument('--combolab-dir', default=None,
                   help="path a combolab (default: $COMBOLAB_DIR o ../combolab)")
    p.add_argument('--since', default=DEFAULT_SINCE_ISO, help=f"ventana inicio ISO8601 (default {DEFAULT_SINCE_ISO})")
    p.add_argument('--until', default=None, help="ventana fin ISO8601 (default: ahora)")
    p.add_argument('--log-start-date', default=None, help="fecha del primer timestamp del log (YYYY-MM-DD)")
    p.add_argument('--n-saturation', type=int, default=DEFAULT_N_SATURATION,
                   help=f"umbral de saturacion (default {DEFAULT_N_SATURATION})")
    p.add_argument('--no-plots', action='store_true', help="saltar generacion de .png")
    p.add_argument('--exclude-reconstructed', dest='exclude_reconstructed',
                   action='store_true', default=True,
                   help="excluir trades flag=reconstructed_post_hoc de agregados (default True)")
    p.add_argument('--include-reconstructed', dest='exclude_reconstructed',
                   action='store_false',
                   help="incluir trades reconstruidos en agregados (no recomendado)")
    args = p.parse_args()
    run(args)


if __name__ == '__main__':
    main()
