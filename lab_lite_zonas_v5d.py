# ============================================
# 🧪 LABORATORIO LITE v5d — PnL RELATIVO A EMAs
# ============================================
# Las EMAs EMA(10)/EMA(55)/EMA(200) son el baseline universal.
#
# ENFOQUE v5d:
#   Simular trades con zonas del candidato Y zonas EMA en test.
#   Comparar PnL neto directamente. El candidato reactivo que
#   captura correcciones intermedias tendrá más trades pero si
#   son legítimos, el PnL será superior (comisiones incluidas).
#
# Score = (PnL_candidato / PnL_ema) × (1 - 0.3 × ExcessCrossRate)
# Cuando EMA PnL <= 0: Score = (PnL / 10) × penalty (fallback absoluto)
#
# ExcessCrossRate = max(0, (rawX_cand - rawX_ema) / rawX_ema), cap 1.0
#   → penalización suave por exceso de cruces brutos
#
# v5d vs v5c:
#   - TOTAL_CANDLES = velas medidas (warmup se suma en descarga)
#   - Mide PnL sobre todo el período útil (sin split train/test)
#   - Warmup dinámico: max_period × 3
#   - Restaura fórmula ratio (PnL/PnL_ema) del v5c original que
#     demostró seleccionar MAs con mejor edge diferencial
# ============================================

# ============================================

import time
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import os
from numba import jit, prange
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN
# ============================================

SYMBOLS = [
    "BNB/USDT", "BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT",
    "TRX/USDT", "DOGE/USDT", "ADA/USDT", "BCH/USDT", "LINK/USDT",
    "XLM/USDT", "SUI/USDT", "LTC/USDT", "AVAX/USDT", "HBAR/USDT",
    "SHIB/USDT", "DOT/USDT", "UNI/USDT", "TAO/USDT",
    "AAVE/USDT", "NEAR/USDT", "ICP/USDT", "ETC/USDT",
    "ONDO/USDT", "ENA/USDT", "POL/USDT", "WLD/USDT", "APT/USDT",
    "ATOM/USDT", "ALGO/USDT", "RENDER/USDT", "ARB/USDT", "FIL/USDT",
    "QNT/USDT", "VET/USDT", "SEI/USDT", "OP/USDT",
    "IMX/USDT", "INJ/USDT", "FET/USDT", "STX/USDT", "SAND/USDT",
    "MANA/USDT", "GRT/USDT", "THETA/USDT",
]


TOTAL_CANDLES = 5000
TIMEFRAME = "1h"
TRAIN_RATIO = 0.0  # v5d: medir PnL sobre TODO el período (no solo test)
TOP_SAVE = 5000

# EMA reference periods
EMA_FAST = 10
EMA_SLOW = 55
EMA_TREND = 200
COMMISSION_ROUND_TRIP = 0.10  # 0.1% round-trip

TOP_N_PRESETS = 7        # Presets a seleccionar por simbolo
DIVERSITY_MODE = True    # Diversidad de familias en seleccion
OUTPUT_DIR = "."         # Directorio de salida (pipeline lo sobreescribe)

# ============================================
# EXCHANGE
# ============================================
exchange = ccxt.binance({'enableRateLimit': True})

def fetch_all_candles(symbol, timeframe, total_candles, max_retries=3):
    print(f"   📥 Descargando {total_candles} velas de {symbol}...")
    all_candles = []
    interval_ms = 3600000
    current_since = int(time.time() * 1000) - (total_candles + 200) * interval_ms
    while len(all_candles) < total_candles + 100:
        for attempt in range(max_retries):
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
                if not ohlcv:
                    return all_candles[-total_candles:] if len(all_candles) >= total_candles else all_candles
                all_candles.extend(ohlcv)
                current_since = ohlcv[-1][0] + interval_ms
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"   ❌ Error: {e}")
                    return all_candles[-total_candles:] if len(all_candles) >= total_candles else all_candles
                time.sleep(2)
    return all_candles[-total_candles:]

# ============================================
# MOVING AVERAGE CALCULATIONS (16 familias)
# ============================================

def calc_ema(close, period):
    """EMA — fiel a Pine Script ta.ema()"""
    n = len(close)
    ema = np.full(n, np.nan)
    if period > n: return ema
    k = 2.0 / (period + 1)
    ema[0] = close[0]
    for i in range(1, n):
        if np.isnan(ema[i-1]):
            ema[i] = close[i]
        else:
            ema[i] = close[i] * k + ema[i-1] * (1 - k)
    return ema

def calc_sma(close, period):
    n = len(close)
    sma = np.full(n, np.nan)
    if period > n: return sma
    cs = np.cumsum(close)
    sma[period-1] = cs[period-1] / period
    sma[period:] = (cs[period:] - cs[:-period]) / period
    return sma

def calc_hma(close, period):
    """HMA — fiel a Pine Script (usa WMA, no EMA)"""
    if period < 2: return calc_ema(close, max(period, 1))
    half_len = max(period // 2, 1)
    sqrt_len = max(round(np.sqrt(period)), 1)
    wma_half = calc_wma(close, half_len)
    wma_full = calc_wma(close, period)
    raw = 2 * wma_half - wma_full
    valid = ~np.isnan(raw)
    if not np.any(valid): return np.full(len(close), np.nan)
    first_valid = np.argmax(valid)
    result = np.full(len(close), np.nan)
    wma_result = calc_wma(raw[first_valid:], sqrt_len)
    result[first_valid:] = wma_result
    return result

def calc_wma(close, period):
    n = len(close)
    wma = np.full(n, np.nan)
    if period > n: return wma
    weights = np.arange(1, period + 1, dtype=np.float64)
    w_sum = weights.sum()
    for i in range(period - 1, n):
        wma[i] = np.dot(close[i-period+1:i+1], weights) / w_sum
    return wma

def calc_dema(close, period):
    """DEMA — fiel a Pine Script"""
    e1 = calc_ema(close, period)
    n = len(close)
    e2 = np.full(n, np.nan)
    k = 2.0 / (period + 1)
    for i in range(n):
        if not np.isnan(e1[i]):
            e2[i] = e1[i] if np.isnan(e2[i-1] if i > 0 else np.nan) else e1[i] * k + e2[i-1] * (1 - k)
    return 2 * e1 - e2

def calc_tema(close, period):
    """TEMA — fiel a Pine Script"""
    e1 = calc_ema(close, period)
    n = len(close)
    k = 2.0 / (period + 1)
    e2 = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(e1[i]):
            e2[i] = e1[i] if (i == 0 or np.isnan(e2[i-1])) else e1[i] * k + e2[i-1] * (1 - k)
    e3 = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(e2[i]):
            e3[i] = e2[i] if (i == 0 or np.isnan(e3[i-1])) else e2[i] * k + e3[i-1] * (1 - k)
    return 3 * e1 - 3 * e2 + e3

def calc_zlema(close, period):
    """ZLEMA — fiel a Pine Script"""
    n = len(close)
    lag = (period - 1) // 2
    zlema = np.full(n, np.nan)
    if period > n: return zlema
    adjusted = np.full(n, np.nan)
    for i in range(lag, n):
        adjusted[i] = 2.0 * close[i] - close[i - lag]
    start = lag
    end = start + period
    if end > n: return zlema
    zlema[end - 1] = np.mean(adjusted[start:end])
    k = 2.0 / (period + 1)
    for i in range(end, n):
        zlema[i] = adjusted[i] * k + zlema[i - 1] * (1 - k)
    return zlema

def calc_kama(close, period, fast_sc=2, slow_sc=30):
    """KAMA — fiel a Pine Script"""
    n = len(close)
    kama = np.full(n, np.nan)
    if period >= n: return kama
    kama[period - 1] = close[period - 1]
    fast_k = 2.0 / (fast_sc + 1)
    slow_k = 2.0 / (slow_sc + 1)
    for i in range(period, n):
        direction = abs(close[i] - close[i - period])
        volatility = np.sum(np.abs(np.diff(close[i - period:i + 1])))
        er = direction / volatility if volatility != 0 else 0.0
        sc = (er * (fast_k - slow_k) + slow_k) ** 2
        kama[i] = kama[i-1] + sc * (close[i] - kama[i-1])
    return kama

def calc_alma(close, period, offset=0.85, sigma=6):
    n = len(close)
    alma = np.full(n, np.nan)
    if period > n or period < 1: return alma
    m = offset * (period - 1)
    s = period / sigma
    weights = np.exp(-((np.arange(period) - m) ** 2) / (2 * s * s))
    w_sum = weights.sum()
    if w_sum == 0: return alma
    weights /= w_sum
    for i in range(period - 1, n):
        alma[i] = np.dot(close[i-period+1:i+1], weights)
    return alma

def calc_tenkan(high, low, period):
    n = len(high)
    tenkan = np.full(n, np.nan)
    if period > n: return tenkan
    for i in range(period - 1, n):
        tenkan[i] = (np.max(high[i-period+1:i+1]) + np.min(low[i-period+1:i+1])) / 2
    return tenkan

def calc_mcginley(close, period):
    """McGinley Dynamic — fiel a Pine Script (factor 0.6)"""
    n = len(close)
    mg = np.full(n, np.nan)
    if period > n: return mg
    mg[0] = close[0]
    for i in range(1, n):
        prev = mg[i-1] if not np.isnan(mg[i-1]) else close[i]
        ratio = close[i] / prev if prev != 0 else 1.0
        denom = 0.6 * period * (ratio ** 4)
        mg[i] = prev + (close[i] - prev) / denom if denom != 0 else prev
    return mg

def calc_vidya(close, period):
    """VIDYA — fiel a Pine Script (CMO real)"""
    n = len(close)
    vidya = np.full(n, np.nan)
    if period > n: return vidya
    sc = 2.0 / (period + 1)
    vidya[0] = close[0]
    for i in range(period, n):
        gains = np.sum(np.maximum(np.diff(close[i-period:i+1]), 0))
        losses = np.sum(np.maximum(-np.diff(close[i-period:i+1]), 0))
        total = gains + losses
        cmo = abs((gains - losses) / total) if total != 0 else 0.0
        prev = vidya[i-1] if not np.isnan(vidya[i-1]) else close[i]
        vidya[i] = close[i] * sc * cmo + prev * (1 - sc * cmo)
    return vidya

def calc_frama(close, high, low, period):
    """FRAMA — fiel a Pine Script (usa high/low)"""
    n = len(close)
    frama = np.full(n, np.nan)
    if period > n or period < 4: return frama
    half = period // 2
    frama[0] = close[0]
    for i in range(period, n):
        n1 = (np.max(high[i-half+1:i+1]) - np.min(low[i-half+1:i+1])) / half if half > 0 else 1
        n2 = (np.max(high[i-period+1:i-half+1]) - np.min(low[i-period+1:i-half+1])) / half if half > 0 else 1
        n3 = (np.max(high[i-period+1:i+1]) - np.min(low[i-period+1:i+1])) / period if period > 0 else 1
        d = (np.log(n1 + n2) - np.log(n3)) / np.log(2) if (n1+n2) > 0 and n3 > 0 else 1.0
        alpha_c = max(0.01, min(np.exp(-4.6 * (d - 1)), 1.0))
        prev = frama[i-1] if not np.isnan(frama[i-1]) else close[i]
        frama[i] = alpha_c * close[i] + (1 - alpha_c) * prev
    return frama

def calc_t3(close, period, vfactor=0.7):
    """T3 (Tillson) — fiel a Pine Script"""
    c1 = -(vfactor**3)
    c2 = 3*vfactor**2 + 3*vfactor**3
    c3 = -6*vfactor**2 - 3*vfactor - 3*vfactor**3
    c4 = 1 + 3*vfactor + vfactor**3 + 3*vfactor**2
    e1 = calc_ema(close, period)
    e2 = calc_ema(e1, period)
    e3 = calc_ema(e2, period)
    e4 = calc_ema(e3, period)
    e5 = calc_ema(e4, period)
    e6 = calc_ema(e5, period)
    return c1*e6 + c2*e5 + c3*e4 + c4*e3

def calc_ssmoother(close, period):
    """SuperSmoother (Ehlers) — fiel a Pine Script"""
    n = len(close)
    ss = np.full(n, np.nan)
    if period > n or period < 1: return ss
    a = np.exp(-np.sqrt(2) * np.pi / period)
    b = 2 * a * np.cos(np.sqrt(2) * np.pi / period)
    c2 = b; c3 = -(a * a); c1 = 1 - c2 - c3
    ss[0] = close[0]
    if n > 1: ss[1] = close[1]
    for i in range(2, n):
        ss[i] = c1 * (close[i] + close[i-1]) / 2 + c2 * ss[i-1] + c3 * ss[i-2]
    return ss

def calc_vwma(close, volume, period):
    n = len(close)
    vwma = np.full(n, np.nan)
    if period > n: return vwma
    cv = close * volume
    cum_cv = np.cumsum(cv); cum_v = np.cumsum(volume)
    vwma[period-1] = cum_cv[period-1] / cum_v[period-1] if cum_v[period-1] != 0 else close[period-1]
    for i in range(period, n):
        s_cv = cum_cv[i] - cum_cv[i-period]; s_v = cum_v[i] - cum_v[i-period]
        vwma[i] = s_cv / s_v if s_v != 0 else close[i]
    return vwma

def calc_jma(close, period, phase=0.0, power=2.0):
    """JMA (Jurik approximation) — fiel a Pine Script"""
    n = len(close)
    jma = np.full(n, np.nan)
    if period < 1 or period > n: return jma
    phase_ratio = 0.5 if phase < -100 else (2.5 if phase > 100 else phase / 100.0 + 1.5)
    beta = 0.45 * (period - 1) / (0.45 * (period - 1) + 2)
    alpha = beta ** power
    e0 = np.zeros(n); e1 = np.zeros(n); e2 = np.zeros(n)
    e0[0] = close[0]; jma[0] = close[0]
    for i in range(1, n):
        e0[i] = (1 - alpha) * close[i] + alpha * e0[i-1]
        e1[i] = (close[i] - e0[i]) * (1 - beta) + beta * e1[i-1]
        e2[i] = (e0[i] + phase_ratio * e1[i] - jma[i-1]) * (1 - alpha)**2 + alpha**2 * e2[i-1]
        jma[i] = jma[i-1] + e2[i]
    return jma

# ============================================
# MA TYPE INDICES & CATALOG
# ============================================
MA_NAMES = {
    0: 'EMA', 1: 'SMA', 2: 'HMA', 3: 'ALMA', 4: 'ZLEMA', 5: 'KAMA',
    6: 'DEMA', 7: 'TEMA', 8: 'McGinley', 9: 'VIDYA', 10: 'FRAMA',
    11: 'T3', 12: 'SSmoother', 13: 'VWMA', 14: 'Tenkan', 15: 'JMA',
}
NONE_TYPE = 99
SIMPLE_TYPES = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14]

def build_catalog():
    fast_periods = list(range(8, 25, 2))
    fast = []
    for p in fast_periods:
        for t in SIMPLE_TYPES: fast.append((t, p, 0, 0))
        for off in [0.5, 0.85]:
            for sig in [4, 6]: fast.append((3, p, off, sig))
        for vf in [0.7, 0.8]: fast.append((11, p, vf, 0))
        fast.append((15, p, 0, 2))
    slow_periods = sorted(set(list(range(30, 76, 3)) + [49]))
    slow = []
    for p in slow_periods:
        for t in SIMPLE_TYPES: slow.append((t, p, 0, 0))
        for off in [0.5, 0.85]:
            for sig in [4, 6]: slow.append((3, p, off, sig))
        for vf in [0.7, 0.8]: slow.append((11, p, vf, 0))
        slow.append((15, p, 0, 2))
    # Trend NO es variable libre en el lite.
    # Se deriva como slow×4 al exportar presets (ver result_to_preset_tuple).
    # Internamente el lite simula sin filtro de tendencia (NONE).
    trend = [(NONE_TYPE, 0, 0, 0)]
    return fast, slow, trend

def calc_ma(close, high, low, volume, ma_type, period, p1=0, p2=0):
    if ma_type == 0:  return calc_ema(close, period)
    elif ma_type == 1:  return calc_sma(close, period)
    elif ma_type == 2:  return calc_hma(close, period)
    elif ma_type == 3:  return calc_alma(close, period, p1, p2)
    elif ma_type == 4:  return calc_zlema(close, period)
    elif ma_type == 5:  return calc_kama(close, period)
    elif ma_type == 6:  return calc_dema(close, period)
    elif ma_type == 7:  return calc_tema(close, period)
    elif ma_type == 8:  return calc_mcginley(close, period)
    elif ma_type == 9:  return calc_vidya(close, period)
    elif ma_type == 10: return calc_frama(close, high, low, period)
    elif ma_type == 11: return calc_t3(close, period, p1)
    elif ma_type == 12: return calc_ssmoother(close, period)
    elif ma_type == 13: return calc_vwma(close, volume, period)
    elif ma_type == 14: return calc_tenkan(high, low, period)
    elif ma_type == 15: return calc_jma(close, period, int(p1), p2)
    else:               return np.full(len(close), np.nan)

def precalculate_all_mas(df):
    close = df['close'].values.astype(np.float64)
    high = df['high'].values.astype(np.float64)
    low = df['low'].values.astype(np.float64)
    volume = df['volume'].values.astype(np.float64)
    n = len(close)
    fast_cat, slow_cat, trend_cat = build_catalog()
    print(f"   🔧 Precalculando MAs: {len(fast_cat)}F + {len(slow_cat)}S + {len(trend_cat)}T...")
    fast_arr = np.full((len(fast_cat), n), np.nan, dtype=np.float64)
    for i, (t, p, p1, p2) in enumerate(fast_cat):
        fast_arr[i] = calc_ma(close, high, low, volume, t, p, p1, p2)
    slow_arr = np.full((len(slow_cat), n), np.nan, dtype=np.float64)
    for i, (t, p, p1, p2) in enumerate(slow_cat):
        slow_arr[i] = calc_ma(close, high, low, volume, t, p, p1, p2)
    trend_arr = np.full((len(trend_cat), n), np.nan, dtype=np.float64)
    for i, (t, p, p1, p2) in enumerate(trend_cat):
        if t == NONE_TYPE: trend_arr[i] = np.zeros(n)
        else: trend_arr[i] = calc_ma(close, high, low, volume, t, p, p1, p2)
    return close, fast_arr, slow_arr, trend_arr, fast_cat, slow_cat, trend_cat

def ma_name(cat_entry):
    t, p, p1, p2 = cat_entry
    if t == NONE_TYPE: return "NONE"
    name = MA_NAMES.get(t, f"T{t}")
    if t == 3: return f"{name}({p},{p1},{p2})"
    if t == 11: return f"{name}({p},v{p1})"
    return f"{name}({p})"

def ma_family(cat_entry):
    t = cat_entry[0]
    if t == NONE_TYPE: return "NONE"
    return MA_NAMES.get(t, f"T{t}")


def select_top_diverse(top_results, top_n=7, period_diff_min=3):
    """Selecciona top N presets con diversidad de familias + 1 variante por familia.

    Estrategia:
    1. Mejor de cada familia (fast_type/slow_type)
    2. Si hay mas familias que slots: top N familias por score
    3. Si hay menos: rellenar con siguientes mejores por score
    4. Post-seleccion: para cada familia seleccionada, buscar la siguiente
       mejor combo de esa misma familia con slow_period diff>=period_diff_min.
       Resultado: hasta top_n*2 presets (en practica 9-12).
    """
    if not top_results or top_n <= 0:
        return top_results[:top_n]

    # Agrupar por familia (primera aparicion = mejor por score)
    seen_families = {}
    for i, res in enumerate(top_results):
        fam = (ma_family(res['fast']), ma_family(res['slow']))
        if fam not in seen_families:
            seen_families[fam] = i

    # Mejores por familia, en orden de score
    family_best_indices = sorted(seen_families.values())

    if len(family_best_indices) >= top_n:
        base_indices = family_best_indices[:top_n]
    else:
        # Menos familias que slots: tomar todos los family bests + rellenar
        selected = set(family_best_indices)
        base_indices = list(family_best_indices)

        for i in range(len(top_results)):
            if len(base_indices) >= top_n:
                break
            if i not in selected:
                base_indices.append(i)
                selected.add(i)

        base_indices = sorted(base_indices[:top_n])

    # --- Variantes de periodo ---
    # Para cada familia seleccionada, registrar el slow_period usado
    selected_set = set(base_indices)
    family_periods = {}  # fam -> slow_period del seleccionado
    for i in base_indices:
        res = top_results[i]
        fam = (ma_family(res['fast']), ma_family(res['slow']))
        family_periods[fam] = res['slow'][1]

    variant_indices = []
    # Para cada familia seleccionada, buscar 1 variante con slow_period diferente
    families_with_variant = set()

    for i, res in enumerate(top_results):
        if i in selected_set:
            continue
        fam = (ma_family(res['fast']), ma_family(res['slow']))
        if fam not in family_periods or fam in families_with_variant:
            continue
        slow_p = res['slow'][1]
        if abs(slow_p - family_periods[fam]) >= period_diff_min:
            variant_indices.append(i)
            selected_set.add(i)
            families_with_variant.add(fam)

    result_indices = sorted(base_indices + variant_indices)
    return [top_results[i] for i in result_indices]


def result_to_preset_tuple(res):
    """Convierte resultado del lab lite a tupla de preset para lab historico.

    Trend se deriva siempre como slow×4: mismo tipo/params, periodo×4.
    Esto garantiza compatibilidad con el lab completo (TF5 necesita trend).

    Returns: (fast_type_str, fast_period, fast_p1, fast_p2,
              slow_type_str, slow_period, slow_p1, slow_p2,
              trend_type_str, trend_period, trend_p1, trend_p2)
    """
    def convert(entry):
        type_idx, period, p1, p2 = entry
        if type_idx == NONE_TYPE:
            return ("NONE", 0, 0.0, 0.0)
        return (MA_NAMES.get(type_idx, f"T{type_idx}"), int(period), float(p1), float(p2))

    f = convert(res['fast'])
    s = convert(res['slow'])
    # Trend = slow×4 (mismo tipo y params, periodo multiplicado)
    slow_type_idx, slow_period, slow_p1, slow_p2 = res['slow']
    t = convert((slow_type_idx, slow_period * 4, slow_p1, slow_p2))
    return (*f, *s, *t)


# ============================================
# ============================================
# NUMBA ENGINE v5d — PnL COMPARISON
# ============================================

@jit(nopython=True)
def simulate_ema_pnl(close, ema_fast, ema_slow, ema_trend, commission_pct, test_start, warmup):
    """Simulate trades using EMA zones in test period. Returns PnL%, n_trades, raw_crosses."""
    n_bars = len(close)
    position = 0
    entry_price = 0.0
    equity = 100.0
    n_trades = 0
    n_raw_crosses = 0
    prev_side = 0

    for t in range(warmup, n_bars):
        ef = ema_fast[t]
        es = ema_slow[t]
        et = ema_trend[t]
        if ef != ef or es != es or et != et:
            continue

        cross_bull = ef > es
        cross_bear = ef < es

        # Raw crosses
        curr_side = 1 if cross_bull else -1
        if prev_side != 0 and curr_side != prev_side:
            if t >= test_start:
                n_raw_crosses += 1
        prev_side = curr_side

        zone_bull = cross_bull and close[t] > et
        zone_bear = cross_bear and close[t] < et

        if t < test_start:
            # Track position for continuity but don't count trades
            if position == 0:
                if zone_bull: position = 1; entry_price = close[t]
                elif zone_bear: position = -1; entry_price = close[t]
            elif position == 1 and (zone_bear or (not zone_bull and not zone_bear)):
                if zone_bear: position = -1; entry_price = close[t]
                else: position = 0
            elif position == -1 and (zone_bull or (not zone_bull and not zone_bear)):
                if zone_bull: position = 1; entry_price = close[t]
                else: position = 0
            continue

        # Test period
        if position == 0:
            if zone_bull: position = 1; entry_price = close[t]
            elif zone_bear: position = -1; entry_price = close[t]
        elif position == 1:
            if zone_bear or (not zone_bull and not zone_bear):
                pnl = (close[t] - entry_price) / entry_price * 100.0 - commission_pct
                equity *= (1 + pnl / 100.0)
                n_trades += 1
                if zone_bear: position = -1; entry_price = close[t]
                else: position = 0
        elif position == -1:
            if zone_bull or (not zone_bull and not zone_bear):
                pnl = (entry_price - close[t]) / entry_price * 100.0 - commission_pct
                equity *= (1 + pnl / 100.0)
                n_trades += 1
                if zone_bull: position = 1; entry_price = close[t]
                else: position = 0

    total_pnl = equity - 100.0
    return total_pnl, n_trades, n_raw_crosses


@jit(nopython=True, parallel=True)
def run_simulation_v5d(close, fast_arr, slow_arr, trend_arr,
                       n_fast, n_slow, n_trend,
                       commission_pct, test_start, warmup):
    n_bars = len(close)
    n_configs = n_fast * n_slow * n_trend

    pnl_arr = np.zeros(n_configs, dtype=np.float64)
    trades_arr = np.zeros(n_configs, dtype=np.int32)
    raw_crosses_arr = np.zeros(n_configs, dtype=np.int32)

    for cfg_idx in prange(n_configs):
        fi = cfg_idx // (n_slow * n_trend)
        remainder = cfg_idx % (n_slow * n_trend)
        si = remainder // n_trend
        ti = remainder % n_trend

        position = 0
        entry_price = 0.0
        equity = 100.0
        n_trades = 0
        n_raw_crosses = 0
        prev_side = 0

        for t in range(warmup, n_bars):
            fv = fast_arr[fi, t]
            sv = slow_arr[si, t]
            if fv != fv or sv != sv:
                continue

            cross_bull = fv > sv
            cross_bear = fv < sv

            # Raw crosses (fast/slow without trend)
            curr_side = 0
            if cross_bull: curr_side = 1
            elif cross_bear: curr_side = -1
            if curr_side != 0 and prev_side != 0 and curr_side != prev_side:
                if t >= test_start:
                    n_raw_crosses += 1
            if curr_side != 0:
                prev_side = curr_side

            # Zone with trend filter
            if ti > 0:
                tv = trend_arr[ti, t]
                if tv != tv:
                    continue
                zone_bull = cross_bull and close[t] > tv
                zone_bear = cross_bear and close[t] < tv
            else:
                zone_bull = cross_bull
                zone_bear = cross_bear

            if t < test_start:
                if position == 0:
                    if zone_bull: position = 1; entry_price = close[t]
                    elif zone_bear: position = -1; entry_price = close[t]
                elif position == 1:
                    if zone_bear or (ti > 0 and not zone_bull and not zone_bear):
                        if zone_bear: position = -1; entry_price = close[t]
                        else: position = 0
                elif position == -1:
                    if zone_bull or (ti > 0 and not zone_bull and not zone_bear):
                        if zone_bull: position = 1; entry_price = close[t]
                        else: position = 0
                continue

            # Test period
            if position == 0:
                if zone_bull: position = 1; entry_price = close[t]
                elif zone_bear: position = -1; entry_price = close[t]
            elif position == 1:
                if zone_bear or (ti > 0 and not zone_bull and not zone_bear):
                    pnl = (close[t] - entry_price) / entry_price * 100.0 - commission_pct
                    equity *= (1 + pnl / 100.0)
                    n_trades += 1
                    if zone_bear: position = -1; entry_price = close[t]
                    else: position = 0
            elif position == -1:
                if zone_bull or (ti > 0 and not zone_bull and not zone_bear):
                    pnl = (entry_price - close[t]) / entry_price * 100.0 - commission_pct
                    equity *= (1 + pnl / 100.0)
                    n_trades += 1
                    if zone_bull: position = 1; entry_price = close[t]
                    else: position = 0

        pnl_arr[cfg_idx] = equity - 100.0
        trades_arr[cfg_idx] = n_trades
        raw_crosses_arr[cfg_idx] = n_raw_crosses

    return pnl_arr, trades_arr, raw_crosses_arr


# ============================================
# PROCESS SYMBOL
# ============================================
def process_symbol(symbol):
    # Calcular warmup antes de descargar para que TOTAL_CANDLES = velas medidas
    fast_cat_pre, slow_cat_pre, trend_cat_pre = build_catalog()
    max_slow_period = max(p for _, p, _, _ in slow_cat_pre)
    max_trend_period = max((p for _, p, _, _ in trend_cat_pre if p > 0), default=0)
    max_period = max(max_slow_period, max_trend_period)
    warmup = max_period * 3
    total_download = TOTAL_CANDLES + warmup

    candles = fetch_all_candles(symbol, TIMEFRAME, total_download)
    if len(candles) < TOTAL_CANDLES:
        print(f"   ❌ Solo {len(candles)} velas")
        return None

    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    print(f"   📊 {len(df)} velas descargadas: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")

    close, fast_arr, slow_arr, trend_arr, fast_cat, slow_cat, trend_cat = precalculate_all_mas(df)
    n_fast, n_slow, n_trend = len(fast_cat), len(slow_cat), len(trend_cat)
    n_configs = n_fast * n_slow * n_trend
    n_bars = len(close)
    n_measured = n_bars - warmup

    test_start = warmup
    print(f"   📐 Warmup={warmup} (max_period={max_period} × 3) | Velas medidas: {n_measured}")

    # EMA reference PnL
    print(f"   📏 Calculando referencia EMA({EMA_FAST}/{EMA_SLOW}/{EMA_TREND})...")
    ema_f = calc_ema(close, EMA_FAST)
    ema_s = calc_ema(close, EMA_SLOW)
    ema_t = calc_ema(close, EMA_TREND)
    ema_pnl, ema_trades, ema_raw_crosses = simulate_ema_pnl(
        close, ema_f, ema_s, ema_t, COMMISSION_ROUND_TRIP, test_start, warmup)
    print(f"   📏 EMA ref: PnL={ema_pnl:+.2f}% | {ema_trades} trades | {ema_raw_crosses} raw crosses")

    # Run all candidates
    print(f"   🚀 Simulando {n_configs:,} configs...")
    t0 = time.time()
    cand_pnl, cand_trades, cand_raw_crosses = run_simulation_v5d(
        close, fast_arr, slow_arr, trend_arr,
        n_fast, n_slow, n_trend,
        COMMISSION_ROUND_TRIP, test_start, warmup)
    elapsed = time.time() - t0
    print(f"   ⏱️  {elapsed:.1f}s ({n_configs/elapsed:,.0f} configs/s)")

    # Scoring
    # Score = (PnL_cand / PnL_ema) × (1 - 0.3 × ExcessCrossRate)
    # Ratio vs EMA premia edge diferencial sobre baseline, no PnL bruto.
    # Cuando EMA PnL <= 0, fallback a PnL absoluto / 10 (normalizado)
    MIN_TRADES = 10
    valid = cand_trades >= MIN_TRADES

    excess_cross = np.where(ema_raw_crosses > 0,
                            np.maximum(0.0, (cand_raw_crosses.astype(np.float64) - ema_raw_crosses) / ema_raw_crosses),
                            0.0)
    excess_cross = np.minimum(excess_cross, 1.0)
    cross_penalty = 1.0 - 0.3 * excess_cross

    if ema_pnl > 0:
        pnl_ratio = cand_pnl / ema_pnl
    else:
        pnl_ratio = cand_pnl / 10.0

    score = pnl_ratio * cross_penalty
    score_valid = np.where(valid, score, -999.0)

    n_valid = int(np.sum(valid))
    n_beating_ema = int(np.sum((cand_pnl > ema_pnl) & valid))
    print(f"   📊 Válidas (≥{MIN_TRADES}t): {n_valid:,} | Superan EMA: {n_beating_ema:,} ({n_beating_ema/max(n_valid,1)*100:.1f}%)")

    sorted_idx = np.argsort(-score_valid)
    bnh = (close[-1] - close[warmup]) / close[warmup] * 100
    test_years = (n_bars - warmup) / 8760.0

    # Ranking file
    sym_clean = symbol.replace("/", "")
    ranking_file = os.path.join(OUTPUT_DIR, f"ranking_lite_v5d_{sym_clean}.txt")
    with open(ranking_file, 'w', encoding='utf-8') as f:
        f.write(f"{'='*140}\n")
        f.write(f"RANKING LITE v5d — PnL RELATIVO A EMAs — {symbol}\n")
        f.write(f"Score = (PnL_cand/PnL_ema) × (1 - 0.3 × ExcessCrossRate)  [EMA<=0: PnL/10]\n")
        f.write(f"Referencia: EMA({EMA_FAST}/{EMA_SLOW}/{EMA_TREND}) → PnL={ema_pnl:+.2f}% | {ema_trades}t | {ema_raw_crosses} rawX\n")
        f.write(f"{'='*140}\n")
        f.write(f"Velas: {len(df)} | {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}\n")
        f.write(f"Warmup: {warmup} | Velas medidas: {n_bars - warmup} ({test_years:.2f}yr)\n")
        f.write(f"Configs: {n_configs:,} | Válidas (≥{MIN_TRADES}t): {n_valid:,} | Superan EMA: {n_beating_ema:,}\n")
        f.write(f"Comisiones: {COMMISSION_ROUND_TRIP}% | B&H: {bnh:+.1f}%\n")
        f.write(f"Tiempo: {elapsed:.1f}s\n")
        f.write(f"{'='*140}\n\n")

        count = 0
        for idx in sorted_idx:
            if not valid[idx]: continue
            if count >= TOP_SAVE: break
            fi = idx // (n_slow * n_trend)
            remainder = idx % (n_slow * n_trend)
            si = remainder // n_trend
            ti = remainder % n_trend
            rawX_ratio = cand_raw_crosses[idx] / ema_raw_crosses if ema_raw_crosses > 0 else 0
            tpy = cand_trades[idx] / test_years if test_years > 0 else 0
            pnl_vs = cand_pnl[idx] - ema_pnl
            if count < 200:
                f.write(f"#{count+1:4d} | Score={score[idx]:.4f}"
                        f" | PnL={cand_pnl[idx]:+.2f}% (vs EMA {pnl_vs:+.2f}%)"
                        f" | {int(cand_trades[idx])}t ({tpy:.0f}/yr)"
                        f" | RawX={int(cand_raw_crosses[idx])}({rawX_ratio:.2f}x)"
                        f" | XPen={excess_cross[idx]:.2f}\n")
                f.write(f"      Fast: {ma_name(fast_cat[fi])}"
                        f" | Slow: {ma_name(slow_cat[si])}"
                        f" | Trend: {ma_name(trend_cat[ti])}\n\n")
            count += 1
    print(f"   💾 {ranking_file}")

    # Top results
    top_results = []
    count = 0
    for idx in sorted_idx:
        if not valid[idx]: continue
        if count >= TOP_SAVE: break
        fi = idx // (n_slow * n_trend)
        remainder = idx % (n_slow * n_trend)
        si = remainder // n_trend
        ti = remainder % n_trend
        top_results.append({
            'fast': fast_cat[fi], 'slow': slow_cat[si], 'trend': trend_cat[ti],
            'score': float(score[idx]), 'pnl': float(cand_pnl[idx]),
            'trades': int(cand_trades[idx]),
            'raw_crosses': int(cand_raw_crosses[idx]),
            'excess_cross': float(excess_cross[idx]),
        })
        count += 1

    # Seleccion de presets (con o sin diversidad)
    if DIVERSITY_MODE:
        selected = select_top_diverse(top_results, TOP_N_PRESETS)
        mode_str = "DIVERSE"
    else:
        selected = top_results[:TOP_N_PRESETS]
        mode_str = "TOP"

    # CSV de presets seleccionados (formato estructurado para pipeline)
    csv_file = os.path.join(OUTPUT_DIR, f"presets_{sym_clean}.csv")
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("rank,fast_type,fast_period,fast_p1,fast_p2,"
                "slow_type,slow_period,slow_p1,slow_p2,"
                "trend_type,trend_period,trend_p1,trend_p2,"
                "score,pnl,trades,raw_crosses,excess_cross,family\n")
        for r, res in enumerate(selected, 1):
            pt = result_to_preset_tuple(res)
            fam = f"{ma_family(res['fast'])}/{ma_family(res['slow'])}"
            f.write(f"{r},{pt[0]},{pt[1]},{pt[2]},{pt[3]},"
                    f"{pt[4]},{pt[5]},{pt[6]},{pt[7]},"
                    f"{pt[8]},{pt[9]},{pt[10]},{pt[11]},"
                    f"{res['score']:.6f},{res['pnl']:.4f},{res['trades']},"
                    f"{res['raw_crosses']},{res['excess_cross']:.4f},{fam}\n")
    print(f"   💾 {csv_file}")

    # Preset tuples para lab historico
    selected_presets = [result_to_preset_tuple(res) for res in selected]

    # Familias seleccionadas
    families = set()
    for res in selected:
        families.add(f"{ma_family(res['fast'])}/{ma_family(res['slow'])}")

    print(f"\n   🏆 {mode_str} {len(selected)} PRESETS ({len(families)} familias)"
          f" (EMA ref: PnL={ema_pnl:+.2f}%, {ema_trades}t, {ema_raw_crosses}rawX):")
    for r, res in enumerate(selected, 1):
        pnl_vs = res['pnl'] - ema_pnl
        rx = res['raw_crosses'] / ema_raw_crosses if ema_raw_crosses > 0 else 0
        fam = f"{ma_family(res['fast'])}/{ma_family(res['slow'])}"
        print(f"      #{r} Score={res['score']:.4f} PnL={res['pnl']:+.2f}% ({pnl_vs:+.2f}vs)"
              f" {res['trades']}t RawX={res['raw_crosses']}({rx:.2f}x)"
              f" | {ma_name(res['fast'])} / {ma_name(res['slow'])} / {ma_name(res['trend'])}"
              f" [{fam}]")

    return {'symbol': symbol, 'top': top_results, 'bnh': bnh,
            'ema_pnl': ema_pnl, 'ema_trades': ema_trades, 'ema_raw_crosses': ema_raw_crosses,
            'selected': selected, 'selected_presets': selected_presets}


# ============================================
# CROSS-SYMBOL ANALYSIS v5d
# ============================================
def cross_symbol_analysis(all_results):
    print(f"\n{'='*140}")
    print(f"🔬 ANÁLISIS CROSS-SYMBOL v5d — PnL RELATIVO A EMAs")
    print(f"{'='*140}\n")
    from collections import Counter, defaultdict
    n_syms = len(all_results)
    TOP_N = TOP_SAVE

    outfile = "cross_symbol_v5d.txt"
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(f"{'='*140}\n")
        f.write(f"ANÁLISIS CROSS-SYMBOL v5d — PnL RELATIVO A EMAs\n")
        f.write(f"Símbolos: {n_syms} | Ref: EMA({EMA_FAST}/{EMA_SLOW}/{EMA_TREND})\n")
        f.write(f"{'='*140}\n\n")

        # EMA summary per symbol
        f.write(f"REFERENCIA EMA POR SÍMBOLO:\n")
        for result in sorted(all_results, key=lambda x: x['symbol']):
            sym = result['symbol'].replace('/USDT', '')
            f.write(f"  {sym:8s}: PnL={result['ema_pnl']:+.2f}% | {result['ema_trades']}t | {result['ema_raw_crosses']} rawX\n")

        # Familia por rol
        for label, role in [("FAST", "fast"), ("SLOW", "slow"), ("TREND", "trend")]:
            f.write(f"\n{'='*80}\n{label}\n{'='*80}\n")
            ts = Counter(); t_syms = defaultdict(set)
            t_pnls = defaultdict(list)
            for result in all_results:
                sym = result['symbol']
                for cfg in result['top'][:TOP_N]:
                    k = ma_family(cfg[role])
                    ts[k] += cfg['score']; t_syms[k].add(sym)
                    t_pnls[k].append(cfg['pnl'])
            total = sum(ts.values()) or 1
            for t, sc in ts.most_common(16):
                ns = len(t_syms[t]); pct = sc / total * 100
                f.write(f"    {t:12s}: Score={sc:10.2f} ({pct:5.1f}%) | {ns:2d}/{n_syms} syms"
                        f" | AvgPnL={np.mean(t_pnls[t]):+.2f}%\n")

        # Top 30 familias
        f.write(f"\n{'='*140}\nTOP 30 FAMILIAS\n{'='*140}\n\n")
        fam_scores = Counter(); fam_syms = defaultdict(set)
        fam_pnls = defaultdict(list); fam_rawx = defaultdict(list)
        for result in all_results:
            sym = result['symbol']
            for cfg in result['top'][:TOP_N]:
                fam = f"{ma_family(cfg['fast'])}/{ma_family(cfg['slow'])}/{ma_family(cfg['trend'])}"
                fam_scores[fam] += cfg['score']; fam_syms[fam].add(sym)
                fam_pnls[fam].append(cfg['pnl']); fam_rawx[fam].append(cfg['raw_crosses'])
        for rank, (fam, sc) in enumerate(fam_scores.most_common(30), 1):
            ns = len(fam_syms[fam])
            f.write(f"  #{rank:2d} | Score={sc:8.2f} | {ns:2d}/{n_syms} syms"
                    f" | AvgPnL={np.mean(fam_pnls[fam]):+.2f}%"
                    f" | AvgRawX={np.mean(fam_rawx[fam]):.0f} | {fam}\n")

        # Top 30 combos exactos
        f.write(f"\n{'='*140}\nTOP 30 COMBINACIONES EXACTAS\n{'='*140}\n\n")
        cs = Counter(); c_syms = defaultdict(set)
        c_pnls = defaultdict(list); c_trades = defaultdict(list); c_rawx = defaultdict(list)
        for result in all_results:
            sym = result['symbol']
            for cfg in result['top'][:TOP_N]:
                key = (cfg['fast'], cfg['slow'], cfg['trend'])
                cs[key] += cfg['score']; c_syms[key].add(sym)
                c_pnls[key].append(cfg['pnl']); c_trades[key].append(cfg['trades'])
                c_rawx[key].append(cfg['raw_crosses'])
        for rank, (key, sc) in enumerate(cs.most_common(30), 1):
            fast, slow, trend = key; ns = len(c_syms[key])
            f.write(f"  #{rank:2d} | Score={sc:8.4f} | {ns:2d}/{n_syms} syms"
                    f" | PnL={np.mean(c_pnls[key]):+.2f}% Trd={np.mean(c_trades[key]):.0f}"
                    f" RawX={np.mean(c_rawx[key]):.0f}"
                    f" | {ma_name(fast)} / {ma_name(slow)} / {ma_name(trend)}\n")
            if rank <= 5:
                syms_list = sorted(s.replace('/USDT', '') for s in c_syms[key])
                f.write(f"       Símbolos: {', '.join(syms_list)}\n")

        # Convergencia períodos top 5
        f.write(f"\n{'='*140}\nCONVERGENCIA DE PERÍODOS — Top 5 familias\n{'='*140}\n")
        fp = defaultdict(lambda: {'fast': Counter(), 'slow': Counter(), 'trend': Counter()})
        for result in all_results:
            for cfg in result['top'][:TOP_N]:
                fam = f"{ma_family(cfg['fast'])}/{ma_family(cfg['slow'])}/{ma_family(cfg['trend'])}"
                fp[fam]['fast'][cfg['fast'][1]] += cfg['score']
                fp[fam]['slow'][cfg['slow'][1]] += cfg['score']
                fp[fam]['trend'][cfg['trend'][1]] += cfg['score']
        for rank, (fam, sc) in enumerate(fam_scores.most_common(5), 1):
            ns = len(fam_syms[fam])
            f.write(f"\n  #{rank} {fam} ({ns}/{n_syms} syms, Score={sc:.2f})\n")
            for role in ['fast', 'slow', 'trend']:
                periods = fp[fam][role]; total_p = sum(periods.values()) or 1
                top_p = periods.most_common(5)
                parts = [f"{p}({s/total_p*100:.0f}%)" for p, s in top_p]
                conv = ""
                if top_p:
                    pct = top_p[0][1] / total_p * 100
                    if pct > 30: conv = f"  ✅ converge en {top_p[0][0]}"
                    elif pct > 20: conv = f"  ~ tendencia hacia {top_p[0][0]}"
                    else: conv = f"  ⚠️ disperso"
                f.write(f"    {role.upper()}: {' > '.join(parts)}{conv}\n")

        # #1 por símbolo
        f.write(f"\n{'='*140}\n#1 POR SÍMBOLO (vs EMA ref)\n{'='*140}\n\n")
        for result in sorted(all_results, key=lambda x: x['symbol']):
            if result['top']:
                cfg = result['top'][0]; sym = result['symbol'].replace('/USDT', '')
                pnl_vs = cfg['pnl'] - result['ema_pnl']
                rx = cfg['raw_crosses'] / result['ema_raw_crosses'] if result['ema_raw_crosses'] > 0 else 0
                f.write(f"  {sym:8s}: Score={cfg['score']:.4f}"
                        f" PnL={cfg['pnl']:+.2f}% ({pnl_vs:+.2f}vs EMA={result['ema_pnl']:+.2f}%)"
                        f" {cfg['trades']}t RawX({rx:.2f}x)"
                        f" | {ma_name(cfg['fast'])} / {ma_name(cfg['slow'])} / {ma_name(cfg['trend'])}\n")

    print(f"   💾 {outfile}")
    print(f"\n   🏆 TOP 10 FAMILIAS:")
    for rank, (fam, sc) in enumerate(fam_scores.most_common(10), 1):
        ns = len(fam_syms[fam])
        print(f"      #{rank} Score={sc:8.2f} ({ns:2d} syms) PnL={np.mean(fam_pnls[fam]):+.2f}% | {fam}")


# ============================================
# MAIN
# ============================================
def main():
    fast_cat, slow_cat, trend_cat = build_catalog()
    n_configs = len(fast_cat) * len(slow_cat) * len(trend_cat)
    print("="*70)
    print("🧪 LABORATORIO LITE v5d — PnL RELATIVO A EMAs")
    print(f"   Ref: EMA({EMA_FAST}/{EMA_SLOW}/{EMA_TREND})")
    print(f"   Score = PnL × (1 - 0.3×ExcessCrossRate)")
    print(f"   Total: {n_configs:,} configs × {len(SYMBOLS)} símbolos")
    print(f"   Comisiones: {COMMISSION_ROUND_TRIP}%")
    print("="*70)
    all_results = []
    failed = []
    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{i}/{len(SYMBOLS)}] {symbol}")
        try:
            result = process_symbol(symbol)
            if result: all_results.append(result)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback; traceback.print_exc()
            failed.append(symbol)
    if len(all_results) >= 3:
        cross_symbol_analysis(all_results)
    print(f"\n{'='*70}")
    print(f"✅ Completado: {len(all_results)}/{len(SYMBOLS)} símbolos")
    if failed: print(f"❌ Fallidos: {', '.join(failed)}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
