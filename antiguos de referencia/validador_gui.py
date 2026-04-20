# ============================================
# Validador v8.2 — GUI Streamlit (Self-Contained)
# ============================================
# Run: streamlit run validador_gui.py
# Requires: pip install streamlit plotly ccxt pandas numpy
# NO dependency on validador_v8_2.py — motor embedded.
# ============================================

import streamlit as st
import sys
import os
import time
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
import ccxt

# =====================================================================
# ENGINE — Copied verbatim from validador_v8_2.py (absolute fidelity)
# =====================================================================

# ---------------------------------------------------------------------------
# Globals (defaults — GUI injects actual values before each run)
# ---------------------------------------------------------------------------
SL_PERCENT = 3.0
SL_EMERGENCY_PERCENT = 5.0
TS_PERCENT = 0.5
COOLDOWN_BARS = 1
COMMISSION_ROUND_TRIP = 0.10
HYST_ATR_LEN = 14
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
# Exchange instance (overridden by GUI before download)
# ---------------------------------------------------------------------------
exchange = ccxt.binance({'enableRateLimit': True})

# ---------------------------------------------------------------------------
# Data download
# ---------------------------------------------------------------------------
def fetch_all_candles(symbol, timeframe, total_candles, max_retries=3,
                      since_ms=None, until_ms=None):
    """Download candles. If since_ms/until_ms given, download that date range instead of total_candles from now."""
    all_candles = []
    tf_ms = {'1h': 3600000, '4h': 14400000, '1d': 86400000}
    interval_ms = tf_ms.get(timeframe, 3600000)
    if since_ms is not None:
        current_since = since_ms
    else:
        current_since = int(time.time() * 1000) - (total_candles + 200) * interval_ms
    requests_made = 0
    consecutive_errors = 0
    while True:
        if until_ms is not None:
            if current_since >= until_ms:
                break
        elif len(all_candles) >= total_candles + 100:
            break
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
            if not ohlcv: break
            all_candles.extend(ohlcv)
            current_since = ohlcv[-1][0] + interval_ms
            requests_made += 1
            consecutive_errors = 0
            time.sleep(0.1)
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= max_retries:
                return None
            time.sleep(2 * consecutive_errors)
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    if until_ms is not None:
        df = df[df['timestamp'] <= pd.Timestamp(until_ms, unit='ms')].reset_index(drop=True)
    elif len(df) > total_candles:
        df = df.tail(total_candles).reset_index(drop=True)
    return df

# ---------------------------------------------------------------------------
# Indicators (verbatim from lab v6.2)
# ---------------------------------------------------------------------------
def calc_ha_trend(df):
    avg_price = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    avg_oc = (df['open'] + df['close'].shift(1)) / 2
    return avg_price > avg_oc

def resample_to_timeframe(df, target_tf):
    df_indexed = df.set_index('timestamp')
    if target_tf == "4h": rule = '4h'
    elif target_tf == "1d": rule = '1D'
    else: return df_indexed
    return df_indexed.resample(rule, closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()

def calc_rsi(close, length=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.ewm(alpha=1.0/length, adjust=False, min_periods=1).mean()
    avg_loss = loss.ewm(alpha=1.0/length, adjust=False, min_periods=1).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=1).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=1).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=1).mean()
    return macd_line, macd_line - signal_line

def calc_stochastic(high, low, close, k=14, d=3, smooth=3):
    lowest_low = low.rolling(window=k, min_periods=1).min()
    highest_high = high.rolling(window=k, min_periods=1).max()
    stoch_range = highest_high - lowest_low
    stoch_raw = np.where(stoch_range > 0, 100 * (close - lowest_low) / stoch_range, 0.0)
    return pd.Series(stoch_raw, index=close.index).rolling(window=smooth, min_periods=1).mean()

def calc_vwmacd(close, volume, fast=12, slow=26):
    def vwma(price, vol, length):
        return (price * vol).rolling(window=length, min_periods=1).sum() / vol.rolling(window=length, min_periods=1).sum()
    return vwma(close, volume, fast) - vwma(close, volume, slow)

def calc_cmf(high, low, close, volume, length=21):
    h_l = high - low
    ad = ((close - low) - (high - close)) / h_l.replace(0, np.nan) * volume
    ad = ad.fillna(0.0)
    sma_ad = ad.rolling(window=length, min_periods=1).mean()
    sma_vol = volume.rolling(window=length, min_periods=1).mean()
    result = sma_ad / sma_vol.replace(0, np.nan)
    return result.fillna(0.0)

def calc_cci(high, low, close, length=10):
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=length, min_periods=1).mean()
    mad = tp.rolling(window=length, min_periods=1).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma_tp) / (0.015 * mad)

def calc_momentum(close, length=10):
    return close - close.shift(length)

# ---------------------------------------------------------------------------
# Divergences (Pine-faithful, verbatim)
# ---------------------------------------------------------------------------
def precalculate_divergences_pine_faithful(close_arr, high_arr, low_arr, indicators_dict,
                                            n_bars, period=5, max_pivots=10, max_bars=100):
    n_indicators = len(indicators_dict)
    div_bits_arr = np.zeros((n_bars, n_indicators), dtype=np.uint8)
    pl_positions = []; pl_vals = []
    ph_positions = []; ph_vals = []
    indicator_arrays = list(indicators_dict.values())
    startpoint = 1
    for t in range(period, n_bars):
        pivot_bar = t - period
        if pivot_bar >= period:
            is_pivot_low = True
            for j in range(1, period + 1):
                if close_arr[pivot_bar] > close_arr[pivot_bar - j] or close_arr[pivot_bar] > close_arr[pivot_bar + j]:
                    is_pivot_low = False; break
            if is_pivot_low:
                pl_positions.insert(0, t); pl_vals.insert(0, close_arr[pivot_bar])
                if len(pl_positions) > 20: pl_positions.pop(); pl_vals.pop()
            is_pivot_high = True
            for j in range(1, period + 1):
                if close_arr[pivot_bar] < close_arr[pivot_bar - j] or close_arr[pivot_bar] < close_arr[pivot_bar + j]:
                    is_pivot_high = False; break
            if is_pivot_high:
                ph_positions.insert(0, t); ph_vals.insert(0, close_arr[pivot_bar])
                if len(ph_positions) > 20: ph_positions.pop(); ph_vals.pop()
        if t < 1: continue
        for ind_idx in range(n_indicators):
            src = indicator_arrays[ind_idx]
            if np.isnan(src[t]): continue
            bull_reg = False; bull_hid = False; bear_reg = False; bear_hid = False
            can_check_pos = t >= 1 and ((src[t] > src[t-1]) or (close_arr[t] > close_arr[t-1]))
            if can_check_pos and len(pl_positions) > 0:
                for x in range(min(max_pivots, len(pl_positions))):
                    pos = pl_positions[x]
                    if pos == 0: break
                    length = t - pos + period
                    if length > max_bars: break
                    if length > 5 and t >= length:
                        ss = src[t - startpoint]; se = src[t - length] if (t - length) >= 0 else np.nan
                        ps = close_arr[t - startpoint]; pe = pl_vals[x]
                        if np.isnan(ss) or np.isnan(se): continue
                        is_reg = (ss > se) and (ps < pe)
                        is_hid = (ss < se) and (ps > pe)
                        if is_reg or is_hid:
                            span = length - startpoint
                            if span <= 0: continue
                            sl_s = (ss - se) / span; sl_p = (ps - pe) / span
                            vs = ss - sl_s; vp = ps - sl_p
                            ok = True
                            for y in range(1 + startpoint, length):
                                bb = t - y
                                if bb < 0 or src[bb] < vs or close_arr[bb] < vp: ok = False; break
                                vs -= sl_s; vp -= sl_p
                            if ok:
                                if is_reg: bull_reg = True
                                if is_hid: bear_hid = True
                                break
            can_check_neg = t >= 1 and ((src[t] < src[t-1]) or (close_arr[t] < close_arr[t-1]))
            if can_check_neg and len(ph_positions) > 0:
                for x in range(min(max_pivots, len(ph_positions))):
                    pos = ph_positions[x]
                    if pos == 0: break
                    length = t - pos + period
                    if length > max_bars: break
                    if length > 5 and t >= length:
                        ss = src[t - startpoint]; se = src[t - length] if (t - length) >= 0 else np.nan
                        ps = close_arr[t - startpoint]; pe = ph_vals[x]
                        if np.isnan(ss) or np.isnan(se): continue
                        is_reg = (ss < se) and (ps > pe)
                        is_hid = (ss > se) and (ps < pe)
                        if is_reg or is_hid:
                            span = length - startpoint
                            if span <= 0: continue
                            sl_s = (ss - se) / span; sl_p = (ps - pe) / span
                            vs = ss - sl_s; vp = ps - sl_p
                            ok = True
                            for y in range(1 + startpoint, length):
                                bb = t - y
                                if bb < 0 or src[bb] > vs or close_arr[bb] > vp: ok = False; break
                                vs -= sl_s; vp -= sl_p
                            if ok:
                                if is_reg: bear_reg = True
                                if is_hid: bull_hid = True
                                break
            bits = 0
            if bull_reg: bits |= 1
            if bull_hid: bits |= 2
            if bear_reg: bits |= 4
            if bear_hid: bits |= 8
            div_bits_arr[t, ind_idx] = bits
    return div_bits_arr

# ---------------------------------------------------------------------------
# Moving Averages — 16 families (Pine-faithful, verbatim)
# ---------------------------------------------------------------------------
def calc_ema(src, period):
    n = len(src); result = np.full(n, np.nan); k = 2.0 / (period + 1)
    result[0] = src[0]
    for i in range(1, n):
        result[i] = src[i] if np.isnan(result[i-1]) else src[i] * k + result[i-1] * (1 - k)
    return result

def calc_sma(src, period):
    n = len(src); result = np.full(n, np.nan)
    for i in range(period - 1, n): result[i] = np.mean(src[i - period + 1:i + 1])
    return result

def calc_kama(close_arr, period, fast_sc=2, slow_sc=30):
    n = len(close_arr); result = np.full(n, np.nan)
    if period >= n: return result
    result[period - 1] = close_arr[period - 1]
    fast_k = 2.0 / (fast_sc + 1); slow_k = 2.0 / (slow_sc + 1)
    for i in range(period, n):
        direction = abs(close_arr[i] - close_arr[i - period])
        volatility = np.sum(np.abs(np.diff(close_arr[i - period:i + 1])))
        er = direction / volatility if volatility != 0 else 0.0
        sc = (er * (fast_k - slow_k) + slow_k) ** 2
        result[i] = result[i - 1] + sc * (close_arr[i] - result[i - 1])
    return result

def calc_zlema(close_arr, period):
    n = len(close_arr); lag = (period - 1) // 2
    adjusted = np.full(n, np.nan)
    for i in range(lag, n): adjusted[i] = 2.0 * close_arr[i] - close_arr[i - lag]
    result = np.full(n, np.nan); k = 2.0 / (period + 1)
    start = lag; end = start + period
    if end > n: return result
    result[end - 1] = np.mean(adjusted[start:end])
    for i in range(end, n): result[i] = adjusted[i] * k + result[i - 1] * (1 - k)
    return result

def calc_alma(close_arr, period, offset=0.85, sigma=6):
    n = len(close_arr); result = np.full(n, np.nan)
    if period < 1: return result
    m = offset * (period - 1); s = period / sigma
    weights = np.array([np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(period)])
    w_sum = np.sum(weights)
    if w_sum == 0: return result
    weights = weights / w_sum
    for i in range(period - 1, n): result[i] = np.sum(close_arr[i - period + 1:i + 1] * weights)
    return result

def calc_dema(src, period):
    e1 = calc_ema(src, period); n = len(src)
    e2 = np.full(n, np.nan); k = 2.0 / (period + 1)
    for i in range(n):
        if not np.isnan(e1[i]):
            e2[i] = e1[i] if np.isnan(e2[i-1] if i > 0 else np.nan) else e1[i] * k + e2[i-1] * (1 - k)
    return 2 * e1 - e2

def calc_tema(src, period):
    e1 = calc_ema(src, period); n = len(src); k = 2.0 / (period + 1)
    e2 = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(e1[i]):
            e2[i] = e1[i] if (i == 0 or np.isnan(e2[i-1])) else e1[i] * k + e2[i-1] * (1 - k)
    e3 = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(e2[i]):
            e3[i] = e2[i] if (i == 0 or np.isnan(e3[i-1])) else e2[i] * k + e3[i-1] * (1 - k)
    return 3 * e1 - 3 * e2 + e3

def calc_jma(src, period, phase=0.0, power=2.0):
    n = len(src)
    phase_ratio = 0.5 if phase < -100 else (2.5 if phase > 100 else phase / 100.0 + 1.5)
    beta = 0.45 * (period - 1) / (0.45 * (period - 1) + 2)
    alpha = beta ** power
    e0 = np.zeros(n); e1 = np.zeros(n); e2 = np.zeros(n)
    result = np.full(n, np.nan); e0[0] = src[0]; result[0] = src[0]
    for i in range(1, n):
        e0[i] = (1 - alpha) * src[i] + alpha * e0[i-1]
        e1[i] = (src[i] - e0[i]) * (1 - beta) + beta * e1[i-1]
        e2[i] = (e0[i] + phase_ratio * e1[i] - result[i-1]) * (1 - alpha)**2 + alpha**2 * e2[i-1]
        result[i] = result[i-1] + e2[i]
    return result

def calc_mcginley(src, period):
    n = len(src); result = np.full(n, np.nan); result[0] = src[0]
    for i in range(1, n):
        prev = result[i-1] if not np.isnan(result[i-1]) else src[i]
        ratio = src[i] / prev if prev != 0 else 1.0
        denom = 0.6 * period * (ratio ** 4)
        result[i] = prev + (src[i] - prev) / denom if denom != 0 else prev
    return result

def calc_vidya(src, period):
    n = len(src); sc = 2.0 / (period + 1)
    result = np.full(n, np.nan); result[0] = src[0]
    for i in range(period, n):
        gains = np.sum(np.maximum(np.diff(src[i-period:i+1]), 0))
        losses = np.sum(np.maximum(-np.diff(src[i-period:i+1]), 0))
        total = gains + losses
        cmo = abs((gains - losses) / total) if total != 0 else 0.0
        prev = result[i-1] if not np.isnan(result[i-1]) else src[i]
        result[i] = src[i] * sc * cmo + prev * (1 - sc * cmo)
    return result

def calc_frama(src, high_arr, low_arr, period):
    n = len(src); half = period // 2
    result = np.full(n, np.nan); result[0] = src[0]
    for i in range(period, n):
        n1 = (np.max(high_arr[i-half+1:i+1]) - np.min(low_arr[i-half+1:i+1])) / half if half > 0 else 1
        n2 = (np.max(high_arr[i-period+1:i-half+1]) - np.min(low_arr[i-period+1:i-half+1])) / half if half > 0 else 1
        n3 = (np.max(high_arr[i-period+1:i+1]) - np.min(low_arr[i-period+1:i+1])) / period if period > 0 else 1
        d = (np.log(n1 + n2) - np.log(n3)) / np.log(2) if (n1+n2) > 0 and n3 > 0 else 1.0
        alpha_c = max(0.01, min(np.exp(-4.6 * (d - 1)), 1.0))
        prev = result[i-1] if not np.isnan(result[i-1]) else src[i]
        result[i] = alpha_c * src[i] + (1 - alpha_c) * prev
    return result

def calc_t3(src, period, v=0.7):
    c1 = -(v**3); c2 = 3*v**2 + 3*v**3; c3 = -6*v**2 - 3*v - 3*v**3; c4 = 1 + 3*v + v**3 + 3*v**2
    e1 = calc_ema(src, period); e2 = calc_ema(e1, period); e3 = calc_ema(e2, period)
    e4 = calc_ema(e3, period); e5 = calc_ema(e4, period); e6 = calc_ema(e5, period)
    return c1*e6 + c2*e5 + c3*e4 + c4*e3

def calc_ssmoother(src, period):
    n = len(src)
    a = np.exp(-np.sqrt(2) * np.pi / period)
    b = 2 * a * np.cos(np.sqrt(2) * np.pi / period)
    c2 = b; c3 = -(a * a); c1 = 1 - c2 - c3
    result = np.full(n, np.nan); result[0] = src[0]
    if n > 1: result[1] = src[1]
    for i in range(2, n): result[i] = c1 * (src[i] + src[i-1]) / 2 + c2 * result[i-1] + c3 * result[i-2]
    return result

def calc_hma(src, period):
    half_len = max(period // 2, 1); sqrt_len = max(round(np.sqrt(period)), 1)
    def wma(x, p):
        s = pd.Series(x)
        return s.rolling(p).apply(lambda x: np.sum(x * np.arange(1,len(x)+1)) / np.sum(np.arange(1,len(x)+1)), raw=True).values
    diff = 2 * wma(src, half_len) - wma(src, period)
    return wma(diff, sqrt_len)

def calc_vwma(src, volume, period):
    n = len(src); result = np.full(n, np.nan)
    for i in range(period - 1, n):
        sv = np.sum(src[i-period+1:i+1] * volume[i-period+1:i+1])
        v = np.sum(volume[i-period+1:i+1])
        result[i] = sv / v if v != 0 else src[i]
    return result

def calc_tenkan(high_arr, low_arr, period):
    n = len(high_arr); result = np.full(n, np.nan)
    for i in range(period - 1, n):
        result[i] = (np.max(high_arr[i-period+1:i+1]) + np.min(low_arr[i-period+1:i+1])) / 2
    return result

def calc_atr(high_arr, low_arr, close_arr, period):
    n = len(close_arr); tr = np.zeros(n)
    tr[0] = high_arr[0] - low_arr[0]
    for i in range(1, n):
        tr[i] = max(high_arr[i]-low_arr[i], abs(high_arr[i]-close_arr[i-1]), abs(low_arr[i]-close_arr[i-1]))
    atr = np.full(n, np.nan); atr[period-1] = np.mean(tr[:period])
    for i in range(period, n): atr[i] = atr[i-1] + (tr[i] - atr[i-1]) / period
    return atr

# ---------------------------------------------------------------------------
# MA dispatcher (identical to Pine v10.0 f_calc_ma)
# ---------------------------------------------------------------------------
def calc_ma(ma_type, close_arr, high_arr, low_arr, volume_arr, period, p1=0.0, p2=0.0):
    if ma_type == "NONE": return np.full(len(close_arr), np.nan)
    elif ma_type == "EMA": return calc_ema(close_arr, period)
    elif ma_type == "SMA": return calc_sma(close_arr, period)
    elif ma_type == "HMA": return calc_hma(close_arr, period)
    elif ma_type == "ALMA": return calc_alma(close_arr, period, offset=p1 if p1>0 else 0.85, sigma=p2 if p2>0 else 6)
    elif ma_type == "KAMA": return calc_kama(close_arr, period)
    elif ma_type == "ZLEMA": return calc_zlema(close_arr, period)
    elif ma_type == "DEMA": return calc_dema(close_arr, period)
    elif ma_type == "TEMA": return calc_tema(close_arr, period)
    elif ma_type == "JMA": return calc_jma(close_arr, period)
    elif ma_type == "McGinley": return calc_mcginley(close_arr, period)
    elif ma_type == "VIDYA": return calc_vidya(close_arr, period)
    elif ma_type == "FRAMA": return calc_frama(close_arr, high_arr, low_arr, period)
    elif ma_type == "T3": return calc_t3(close_arr, period, v=p1 if p1>0 else 0.7)
    elif ma_type in ("SuperSmoother", "SSmoother"): return calc_ssmoother(close_arr, period)
    elif ma_type == "VWMA": return calc_vwma(close_arr, volume_arr, period)
    elif ma_type == "Tenkan": return calc_tenkan(high_arr, low_arr, period)
    else: return calc_ema(close_arr, period)

# ---------------------------------------------------------------------------
# Hysteresis ATR (identical to Pine v10.0)
# ---------------------------------------------------------------------------
def calc_zone_with_hysteresis(ma_fast_arr, ma_slow_arr, atr_arr, hyst_mult):
    n = len(ma_fast_arr)
    zone_bull = np.zeros(n, dtype=np.bool_)
    zone_bear = np.zeros(n, dtype=np.bool_)
    hyst_zone = 0
    for i in range(n):
        if np.isnan(ma_fast_arr[i]) or np.isnan(ma_slow_arr[i]): continue
        hyst_band = hyst_mult * atr_arr[i] if not np.isnan(atr_arr[i]) else 0.0
        if hyst_mult == 0.0:
            hyst_zone = 1 if ma_fast_arr[i] > ma_slow_arr[i] else (-1 if ma_fast_arr[i] < ma_slow_arr[i] else hyst_zone)
        else:
            if hyst_zone <= 0 and ma_fast_arr[i] > ma_slow_arr[i] + hyst_band: hyst_zone = 1
            if hyst_zone >= 0 and ma_fast_arr[i] < ma_slow_arr[i] - hyst_band: hyst_zone = -1
            if hyst_zone == 0:
                hyst_zone = 1 if ma_fast_arr[i] > ma_slow_arr[i] + hyst_band else (-1 if ma_fast_arr[i] < ma_slow_arr[i] - hyst_band else 0)
        zone_bull[i] = (hyst_zone == 1)
        zone_bear[i] = (hyst_zone == -1)
    return zone_bull, zone_bear

# ---------------------------------------------------------------------------
# Pre-calculate all data (v8.1: Multi-MA + Hysteresis)
# ---------------------------------------------------------------------------
def precalculate_all_data(df_1h, preset=None, hyst_mult=0.0, symbol=None):
    n = len(df_1h)
    fast_type, fast_len, fast_p1, fast_p2 = preset[0], preset[1], preset[2], preset[3]
    slow_type, slow_len, slow_p1, slow_p2 = preset[4], preset[5], preset[6], preset[7]
    trend_type, trend_len, trend_p1, trend_p2 = preset[8], preset[9], preset[10], preset[11]

    df_1h_indexed = df_1h.set_index('timestamp')
    df_4h_full = df_1h_indexed.resample('4h', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    df_1d_full = df_1h_indexed.resample('1D', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()

    tf2_trend_resolved = calc_ha_trend(df_4h_full)
    tf2_bull_resolved = tf2_trend_resolved.shift(1).reindex(df_1h_indexed.index).ffill().fillna(True).values
    tf3_trend_resolved = calc_ha_trend(df_1d_full)
    tf3_bull_resolved = tf3_trend_resolved.shift(1).reindex(df_1h_indexed.index).ffill().fillna(True).values

    close_arr = df_1h['close'].values.astype(np.float64)
    high_arr = df_1h['high'].values.astype(np.float64)
    low_arr = df_1h['low'].values.astype(np.float64)
    volume_arr = df_1h['volume'].values.astype(np.float64)

    ma_fast_arr = calc_ma(fast_type, close_arr, high_arr, low_arr, volume_arr, fast_len, fast_p1, fast_p2)
    ma_slow_arr = calc_ma(slow_type, close_arr, high_arr, low_arr, volume_arr, slow_len, slow_p1, slow_p2)

    atr_arr = calc_atr(high_arr, low_arr, close_arr, HYST_ATR_LEN)
    zone_bull_arr, zone_bear_arr = calc_zone_with_hysteresis(ma_fast_arr, ma_slow_arr, atr_arr, hyst_mult)

    tf4_bull_arr = close_arr > ma_slow_arr
    tf4_bear_arr = close_arr < ma_slow_arr

    ma_trend_arr = calc_ma(trend_type, close_arr, high_arr, low_arr, volume_arr, trend_len, trend_p1, trend_p2)
    tf5_bull_resolved = np.where(np.isnan(ma_trend_arr), False, close_arr > ma_trend_arr)
    tf5_bear_resolved = np.where(np.isnan(ma_trend_arr), False, close_arr < ma_trend_arr)

    filters_forming_arr = np.zeros(n, dtype=np.uint32)
    filters_resolved_arr = np.zeros(n, dtype=np.uint32)

    for bar_idx in range(100, n):
        df_until_now = df_1h.iloc[:bar_idx+1].copy()
        df_4h = resample_to_timeframe(df_until_now, "4h")
        df_1d = resample_to_timeframe(df_until_now, "1d")
        tf1_bull = calc_ha_trend(df_until_now).iloc[-1] if len(df_until_now) > 1 else True
        tf2_trend = calc_ha_trend(df_4h)
        tf2_bull_forming = tf2_trend.iloc[-1] if len(tf2_trend) > 0 else True
        tf3_trend = calc_ha_trend(df_1d)
        tf3_bull_forming = tf3_trend.iloc[-1] if len(tf3_trend) > 0 else True

        tf4_bull = tf4_bull_arr[bar_idx]; tf4_bear = tf4_bear_arr[bar_idx]
        tf5_bull = tf5_bull_resolved[bar_idx]; tf5_bear = tf5_bear_resolved[bar_idx]

        f_forming = 0
        if tf1_bull: f_forming |= (1 << 0)
        if tf2_bull_forming: f_forming |= (1 << 1)
        if tf3_bull_forming: f_forming |= (1 << 2)
        if tf4_bull: f_forming |= (1 << 3)
        if tf5_bull: f_forming |= (1 << 4)
        if tf4_bear: f_forming |= (1 << 11)
        if tf5_bear: f_forming |= (1 << 12)
        filters_forming_arr[bar_idx] = f_forming

        f_resolved = 0
        if tf1_bull: f_resolved |= (1 << 0)
        if tf2_bull_resolved[bar_idx]: f_resolved |= (1 << 1)
        if tf3_bull_resolved[bar_idx]: f_resolved |= (1 << 2)
        if tf4_bull: f_resolved |= (1 << 3)
        if tf5_bull: f_resolved |= (1 << 4)
        if tf4_bear: f_resolved |= (1 << 11)
        if tf5_bear: f_resolved |= (1 << 12)
        filters_resolved_arr[bar_idx] = f_resolved

    rsi_full = calc_rsi(df_1h['close'], DIV_RSI_LEN).values
    macd_line_full, macd_hist_full = calc_macd(df_1h['close'], DIV_MACD_FAST, DIV_MACD_SLOW, DIV_MACD_SIGNAL)
    macd_line_full = macd_line_full.values; macd_hist_full = macd_hist_full.values
    stoch_full = calc_stochastic(df_1h['high'], df_1h['low'], df_1h['close'], DIV_STOCH_K, DIV_STOCH_D, DIV_STOCH_SMOOTH).values
    vwmacd_full = calc_vwmacd(df_1h['close'], df_1h['volume'], DIV_VWMACD_FAST, DIV_VWMACD_SLOW).values
    cmf_full = calc_cmf(df_1h['high'], df_1h['low'], df_1h['close'], df_1h['volume'], DIV_CMF_LEN).values
    cci_full = calc_cci(df_1h['high'], df_1h['low'], df_1h['close'], DIV_CCI_LEN).values
    mom_full = calc_momentum(df_1h['close'], DIV_MOM_LEN).values

    indicators = {
        'rsi': rsi_full, 'macd_hist': macd_hist_full, 'macd_line': macd_line_full,
        'stoch': stoch_full, 'vwmacd': vwmacd_full, 'cmf': cmf_full,
        'cci': cci_full, 'mom': mom_full
    }
    div_bits_arr = precalculate_divergences_pine_faithful(
        close_arr, high_arr, low_arr, indicators,
        n, DIV_PIVOT_PERIOD, DIV_MAX_PIVOTS, DIV_MAX_BARS
    )

    return {
        'close': close_arr, 'high': high_arr, 'low': low_arr,
        'open': df_1h['open'].values.astype(np.float64),
        'volume': volume_arr,
        'ma_trend': ma_trend_arr,
        'timestamps': df_1h['timestamp'].values,
        'zone_bull': zone_bull_arr, 'zone_bear': zone_bear_arr,
        'ema_fast': ma_fast_arr, 'ema_slow': ma_slow_arr,
        'filters_forming': filters_forming_arr, 'filters_resolved': filters_resolved_arr,
        'div_bits': div_bits_arr,
    }

# ---------------------------------------------------------------------------
# Decode / Encode config (identical to lab)
# ---------------------------------------------------------------------------
def decode_config(config_id):
    exit_mask = config_id & 0xF
    entry_mask = (config_id >> 4) & 0x1F
    div_entry_mode = (config_id >> 9) & 0x3
    div_exit = (config_id >> 11) & 0x1
    div_type = (config_id >> 12) & 0x3
    div_ind_mask = (config_id >> 14) & 0xFF
    cancel_tf = (config_id >> 22) & 0x1
    use_ts = (config_id >> 23) & 0x1
    reg_inv = (config_id >> 24) & 0x1
    hid_inv = (config_id >> 25) & 0x1
    entry_tfs = []
    if entry_mask & 1: entry_tfs.append("TF1")
    if entry_mask & 2: entry_tfs.append("TF2")
    if entry_mask & 4: entry_tfs.append("TF3")
    if entry_mask & 8: entry_tfs.append("TF4")
    if entry_mask & 16: entry_tfs.append("TF5")
    exit_tfs = []
    if exit_mask & 1: exit_tfs.append("TF1")
    if exit_mask & 2: exit_tfs.append("TF2")
    if exit_mask & 4: exit_tfs.append("TF3")
    if exit_mask & 8: exit_tfs.append("TF4")
    if exit_mask == 0: exit_tfs.append("ZONA")
    ind_names = ["RSI", "MACD_H", "MACD_L", "STOCH", "VWMACD", "CMF", "CCI", "MOM"]
    indicators = [ind_names[i] for i in range(8) if (div_ind_mask >> i) & 1]
    variant_map = {(0,0): "FIX", (0,1): "ORIGINAL", (1,1): "ALLINV", (1,0): "REGINV"}
    variant_str = variant_map.get((reg_inv, hid_inv), "?")
    return {
        'exit_mask': exit_mask, 'entry_mask': entry_mask,
        'div_entry_mode': div_entry_mode, 'div_exit': div_exit,
        'div_type': div_type, 'div_ind_mask': div_ind_mask,
        'cancel_tf': cancel_tf, 'use_ts': use_ts,
        'reg_inv': reg_inv, 'hid_inv': hid_inv,
        'entry_tfs': entry_tfs, 'exit_tfs': exit_tfs,
        'div_indicators': indicators,
        'div_mode_str': ["OFF", "CONTEXTUAL", "OR"][div_entry_mode],
        'div_type_str': ["NONE", "REGULAR", "HIDDEN", "BOTH"][div_type],
        'cancel_str': "TF" if cancel_tf else "OFF",
        'ts_str': "TS" if use_ts else "SL_FIJO",
        'n_entry_tfs': bin(entry_mask).count('1'),
        'variant': variant_str,
    }

def encode_config_id(entry_mask, exit_mask, div_entry_mode, div_exit,
                     div_type, div_ind_mask, cancel_tf, use_ts, reg_inv, hid_inv):
    cfg = (exit_mask & 0xF)
    cfg |= (entry_mask & 0x1F) << 4
    cfg |= (div_entry_mode & 0x3) << 9
    cfg |= (div_exit & 0x1) << 11
    cfg |= (div_type & 0x3) << 12
    cfg |= (div_ind_mask & 0xFF) << 14
    cfg |= (cancel_tf & 0x1) << 22
    cfg |= (use_ts & 0x1) << 23
    cfg |= (reg_inv & 0x1) << 24
    cfg |= (hid_inv & 0x1) << 25
    return cfg

# ---------------------------------------------------------------------------
# ENGINE — Literal translation of Numba engine with trade-by-trade logging
# ---------------------------------------------------------------------------
def run_single_config(data, cfg_id):
    cfg = decode_config(cfg_id)
    exit_mask = cfg['exit_mask']; entry_mask = cfg['entry_mask']
    div_entry_mode = cfg['div_entry_mode']; div_exit = cfg['div_exit']
    div_type = cfg['div_type']; div_ind_mask = cfg['div_ind_mask']
    cancel_tf = cfg['cancel_tf']; use_ts = cfg['use_ts']
    reg_inv = cfg['reg_inv']; hid_inv = cfg['hid_inv']

    close_arr = data['close']; high_arr = data['high']; low_arr = data['low']
    timestamps = data['timestamps']
    zone_bull_arr = data['zone_bull']; zone_bear_arr = data['zone_bear']
    filters_forming_arr = data['filters_forming']; filters_resolved_arr = data['filters_resolved']
    div_bits_arr = data['div_bits']

    n_bars = len(close_arr)
    timestamps_i64 = timestamps.astype('datetime64[ms]').astype(np.int64)

    position = 0; entry_price = 0.0; entry_bar = 0; entry_filters_forming = 0; sl_level = 0.0
    pnl = 0.0; peak_pnl = 0.0; max_dd = 0.0; gross_profit = 0.0; gross_loss = 0.0
    div_ctx_bull = False; div_ctx_bear = False; last_zone_bull = False; last_zone_bear = False
    div_bull_now_saved = False; div_bear_now_saved = False
    cooldown_until = 0

    entry_tf_count = 0
    for bit in range(5):
        if (entry_mask >> bit) & 1: entry_tf_count += 1
    exit_tf_count = 0
    for bit in range(4):
        if (exit_mask >> bit) & 1: exit_tf_count += 1

    trades = []; entry_div_ctx_str = ""

    for t in range(100, n_bars):
        z_bull = zone_bull_arr[t]; z_bear = zone_bear_arr[t]
        f_forming = int(filters_forming_arr[t])
        f_resolved = int(filters_resolved_arr[t])
        close_p = close_arr[t]; high_p = high_arr[t]; low_p = low_arr[t]

        prev_div_bull_now = div_bull_now_saved
        prev_div_bear_now = div_bear_now_saved

        # Phase 1: Zone change resets (Pine: not zonaBajista[1] / not zonaAlcista[1])
        zone_changed_to_bear = z_bear and not last_zone_bear
        zone_changed_to_bull = z_bull and not last_zone_bull
        if zone_changed_to_bear: div_ctx_bull = False
        if zone_changed_to_bull: div_ctx_bear = False

        # Phase 2: div_ctx update from PREVIOUS bar's div_raw (Pine L.447-452)
        if prev_div_bull_now:
            div_ctx_bull = True
            div_ctx_bear = False
        if prev_div_bear_now:
            div_ctx_bear = True
            div_ctx_bull = False

        # Snapshot div_ctx for entry evaluation
        entry_div_ctx_bull = div_ctx_bull
        entry_div_ctx_bear = div_ctx_bear

        last_zone_bull = z_bull
        last_zone_bear = z_bear

        # Phase 3: Calculate divergence for CURRENT bar
        div_bull_now = False; div_bear_now = False
        if div_type > 0 and div_ind_mask > 0:
            net_div_score = 0
            for ind in range(8):
                if not (div_ind_mask & (1 << ind)): continue
                bits = div_bits_arr[t, ind]
                ind_bull = False; ind_bear = False
                if div_type == 1:
                    if reg_inv == 0: ind_bull = (bits & 1) > 0; ind_bear = (bits & 4) > 0
                    else: ind_bull = (bits & 4) > 0; ind_bear = (bits & 1) > 0
                elif div_type == 2:
                    if hid_inv == 0: ind_bull = (bits & 8) > 0; ind_bear = (bits & 2) > 0
                    else: ind_bull = (bits & 2) > 0; ind_bear = (bits & 8) > 0
                elif div_type == 3:
                    if reg_inv == 0: reg_bull = (bits & 1) > 0; reg_bear = (bits & 4) > 0
                    else: reg_bull = (bits & 4) > 0; reg_bear = (bits & 1) > 0
                    if hid_inv == 0: hid_bull = (bits & 8) > 0; hid_bear = (bits & 2) > 0
                    else: hid_bull = (bits & 2) > 0; hid_bear = (bits & 8) > 0
                    ind_bull = reg_bull or hid_bull; ind_bear = reg_bear or hid_bear
                if ind_bull: net_div_score += 1
                if ind_bear: net_div_score -= 1
            # Umbral consenso = 1 (matches Pine i_div_showlimit default)
            div_bull_now = net_div_score >= 1; div_bear_now = net_div_score <= -1

        div_bull_now_saved = div_bull_now; div_bear_now_saved = div_bear_now

        # Phase 4: Update div_ctx
        if div_bull_now: div_ctx_bull = True
        if div_bear_now: div_ctx_bear = True

        # ===== POSITION MANAGEMENT =====
        if position != 0:
            exit_signal = False; cancel_signal = False; div_exit_signal = False
            sl_exit_signal = False; sl_emergency_signal = False; normal_exit_signal = False
            exit_price = close_p

            # Trailing Stop update
            if use_ts == 1 and t > entry_bar:
                if position == 1:
                    potential_stop = low_arr[t - 1] * (1 - TS_PERCENT / 100)
                    if potential_stop > sl_level: sl_level = potential_stop
                elif position == -1:
                    potential_stop = high_arr[t - 1] * (1 + TS_PERCENT / 100)
                    if sl_level == 0.0 or potential_stop < sl_level: sl_level = potential_stop

            # P1: SL Emergency
            if position == 1:
                emerg_level = entry_price * (1 - SL_EMERGENCY_PERCENT / 100)
                if low_p <= emerg_level:
                    exit_signal = True; sl_exit_signal = True; sl_emergency_signal = True; exit_price = emerg_level
            elif position == -1:
                emerg_level = entry_price * (1 + SL_EMERGENCY_PERCENT / 100)
                if high_p >= emerg_level:
                    exit_signal = True; sl_exit_signal = True; sl_emergency_signal = True; exit_price = emerg_level

            # P2: SL/TS Normal
            if not exit_signal and sl_level > 0:
                if position == 1 and close_p < sl_level: exit_signal = True; sl_exit_signal = True
                elif position == -1 and close_p > sl_level: exit_signal = True; sl_exit_signal = True

            # P3: TF exit (Pine priority: normal > div)
            if not exit_signal and exit_mask > 0:
                exit_count_bull = 0; exit_count_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        exit_count_active += 1
                        if (f_forming >> bit) & 1: exit_count_bull += 1
                if position == 1 and exit_count_active > 0 and exit_count_bull == 0:
                    exit_signal = True; normal_exit_signal = True
                elif position == -1 and exit_count_active > 0 and exit_count_bull == exit_count_active:
                    exit_signal = True; normal_exit_signal = True

            # P4: Zone exit (Pine priority: normal > div)
            if not exit_signal:
                if position == 1 and z_bear: exit_signal = True; normal_exit_signal = True
                elif position == -1 and z_bull: exit_signal = True; normal_exit_signal = True

            # P5: Div exit (only if no normal exit triggered — matches Pine)
            if not exit_signal and div_exit == 1 and div_type > 0:
                if position == 1 and div_bear_now: exit_signal = True; div_exit_signal = True
                elif position == -1 and div_bull_now: exit_signal = True; div_exit_signal = True

            # P6: Cancel TF
            if not exit_signal and cancel_tf == 1:
                cancel_signal = False
                ts_entry_i = timestamps_i64[entry_bar]; ts_now_i = timestamps_i64[t]
                entry_day = ts_entry_i // 86400000; current_day = ts_now_i // 86400000
                same_daily = (entry_day == current_day)
                eff = entry_filters_forming; f_now = f_forming
                # Fix fidelidad: usar resolved[t] (barra HTF actual finalizada)
                efr = int(filters_resolved_arr[t])
                if (entry_mask >> 1) & 1:
                    entry_4h = (ts_entry_i // 3600000) // 4; now_4h = (ts_now_i // 3600000) // 4
                    if entry_4h == now_4h:
                        if ((eff >> 1) & 1) != ((f_now >> 1) & 1): cancel_signal = True
                    else:
                        if ((eff >> 1) & 1) != ((efr >> 1) & 1): cancel_signal = True
                if not cancel_signal and (entry_mask >> 2) & 1:
                    if same_daily:
                        if ((eff >> 2) & 1) != ((f_now >> 2) & 1): cancel_signal = True
                    else:
                        if ((eff >> 2) & 1) != ((efr >> 2) & 1): cancel_signal = True

            # EXECUTE EXIT
            if exit_signal or cancel_signal:
                if position == 1: trade_pnl = (exit_price - entry_price) / entry_price * 100
                else: trade_pnl = (entry_price - exit_price) / entry_price * 100
                trade_pnl -= COMMISSION_ROUND_TRIP
                pnl += trade_pnl
                if trade_pnl > 0: gross_profit += trade_pnl
                else: gross_loss += abs(trade_pnl)
                if pnl > peak_pnl: peak_pnl = pnl
                dd = peak_pnl - pnl
                if dd > max_dd: max_dd = dd

                if sl_emergency_signal: exit_reason = "SL_EMERG"
                elif sl_exit_signal: exit_reason = "SL_TS" if use_ts else "SL_FIJO"
                elif div_exit_signal: exit_reason = "DIV_EXIT"
                elif cancel_signal: exit_reason = "CANCEL_TF"
                elif normal_exit_signal:
                    if exit_mask > 0:
                        ecb = 0; eca = 0
                        for bit in range(4):
                            if (exit_mask >> bit) & 1:
                                eca += 1
                                if (f_forming >> bit) & 1: ecb += 1
                        if (position == 1 and ecb == 0) or (position == -1 and ecb == eca): exit_reason = "TF_EXIT"
                        else: exit_reason = "ZONA_EXIT"
                    else: exit_reason = "ZONA_EXIT"
                else: exit_reason = "UNKNOWN"

                dur = t - entry_bar
                tf_names = ["TF1","TF2","TF3","TF4","TF5"]
                fs = ""
                for b in range(5):
                    if (entry_mask >> b) & 1:
                        v = "B" if (filters_forming_arr[entry_bar] >> b) & 1 else "b"
                        fs += f"{tf_names[b]}={v} "

                trades.append({
                    'num': len(trades) + 1,
                    'side': 'L' if position == 1 else 'S',
                    'entry_date': str(pd.Timestamp(timestamps[entry_bar]))[:16],
                    'exit_date': str(pd.Timestamp(timestamps[t]))[:16],
                    'entry_price': round(entry_price, 4),
                    'exit_price': round(exit_price, 4),
                    'pnl': round(trade_pnl, 4),
                    'cumul': round(pnl, 4),
                    'bars': dur,
                    'reason': exit_reason,
                    'sl_at_exit': round(sl_level, 4),
                    'entry_filters': fs.strip(),
                    'entry_ctx': entry_div_ctx_str,
                    'zone_exit': 'B' if z_bull else 'b',
                    'div_bull': div_bull_now,
                    'div_bear': div_bear_now,
                    'max_dd': round(max_dd, 4),
                })

                if position == 1: div_ctx_bull = False
                else: div_ctx_bear = False

                if sl_emergency_signal: cooldown_until = t
                elif sl_exit_signal: cooldown_until = t + COOLDOWN_BARS - 1
                elif div_exit_signal: cooldown_until = t + COOLDOWN_BARS - 1
                elif cancel_signal: cooldown_until = t

                position = 0; entry_price = 0.0; sl_level = 0.0; entry_filters_forming = 0

        # Post-exit zone context reset
        if z_bear: div_ctx_bull = False
        if z_bull: div_ctx_bear = False

        # ===== ENTRY =====
        if position == 0:
            if t <= cooldown_until: continue
            long_cond = False; short_cond = False
            tf_entry_ok_bull = True; tf_entry_ok_bear = True

            if (entry_mask >> 0) & 1:
                if not ((f_forming >> 0) & 1): tf_entry_ok_bull = False
                if ((f_forming >> 0) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 1) & 1:
                if not ((f_forming >> 1) & 1): tf_entry_ok_bull = False
                if ((f_forming >> 1) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 2) & 1:
                if not ((f_forming >> 2) & 1): tf_entry_ok_bull = False
                if ((f_forming >> 2) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 3) & 1:
                if not ((f_forming >> 3) & 1): tf_entry_ok_bull = False
                if not ((f_forming >> 11) & 1): tf_entry_ok_bear = False
            if (entry_mask >> 4) & 1:
                if not ((f_forming >> 4) & 1): tf_entry_ok_bull = False
                if not ((f_forming >> 12) & 1): tf_entry_ok_bear = False

            effective_ctx_bull = entry_div_ctx_bull or prev_div_bull_now
            effective_ctx_bear = entry_div_ctx_bear or prev_div_bear_now

            if div_entry_mode == 0:
                if z_bull: long_cond = tf_entry_ok_bull if entry_tf_count > 0 else True
                if z_bear: short_cond = tf_entry_ok_bear if entry_tf_count > 0 else True
            elif div_entry_mode == 1:
                if z_bull:
                    if entry_tf_count > 0: long_cond = tf_entry_ok_bull and effective_ctx_bull
                    elif exit_tf_count > 0: long_cond = effective_ctx_bull
                    else: long_cond = prev_div_bull_now
                if z_bear:
                    if entry_tf_count > 0: short_cond = tf_entry_ok_bear and effective_ctx_bear
                    elif exit_tf_count > 0: short_cond = effective_ctx_bear
                    else: short_cond = prev_div_bear_now
            elif div_entry_mode == 2:
                if z_bull: long_cond = (tf_entry_ok_bull or prev_div_bull_now) if entry_tf_count > 0 else True
                if z_bear: short_cond = (tf_entry_ok_bear or prev_div_bear_now) if entry_tf_count > 0 else True

            # Gatekeeper
            if long_cond and exit_mask > 0:
                exit_count_bull = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1 and (f_forming >> bit) & 1: exit_count_bull += 1
                if exit_count_bull == 0: long_cond = False

            if short_cond and exit_mask > 0:
                exit_count_bull = 0; exit_count_active = 0
                for bit in range(4):
                    if (exit_mask >> bit) & 1:
                        exit_count_active += 1
                        if (f_forming >> bit) & 1: exit_count_bull += 1
                if exit_count_bull == exit_count_active: short_cond = False

            if long_cond:
                position = 1; entry_price = close_p; entry_bar = t
                entry_filters_forming = f_forming
                sl_level = low_p * (1 - SL_PERCENT / 100)
                entry_div_ctx_str = f"ctx_b={div_ctx_bull} now={div_bull_now}"
            elif short_cond:
                position = -1; entry_price = close_p; entry_bar = t
                entry_filters_forming = f_forming
                sl_level = high_p * (1 + SL_PERCENT / 100)
                entry_div_ctx_str = f"ctx_s={div_ctx_bear} now={div_bear_now}"

    return trades, pnl, max_dd, gross_profit, gross_loss


# =====================================================================
# GUI
# =====================================================================

MA_TYPES = [
    "EMA", "SMA", "HMA", "ALMA", "KAMA", "ZLEMA", "DEMA", "TEMA",
    "JMA", "McGinley", "VIDYA", "FRAMA", "T3", "SSmoother", "VWMA", "Tenkan",
]
NEEDS_P1 = {"ALMA", "T3"}
NEEDS_P2 = {"ALMA"}

EXCHANGES = {
    "Binance": lambda: ccxt.binance({'enableRateLimit': True}),
    "Binance US": lambda: ccxt.binanceus({'enableRateLimit': True}),
    "Bybit": lambda: ccxt.bybit({'enableRateLimit': True}),
    "OKX": lambda: ccxt.okx({'enableRateLimit': True}),
    "Bitget": lambda: ccxt.bitget({'enableRateLimit': True}),
    "Gate.io": lambda: ccxt.gateio({'enableRateLimit': True}),
    "KuCoin": lambda: ccxt.kucoin({'enableRateLimit': True}),
    "MEXC": lambda: ccxt.mexc({'enableRateLimit': True}),
    "HTX (Huobi)": lambda: ccxt.htx({'enableRateLimit': True}),
    "Coinbase": lambda: ccxt.coinbase({'enableRateLimit': True}),
    "Kraken": lambda: ccxt.kraken({'enableRateLimit': True}),
    "Bitfinex": lambda: ccxt.bitfinex2({'enableRateLimit': True}),
    "BingX": lambda: ccxt.bingx({'enableRateLimit': True}),
    "Phemex": lambda: ccxt.phemex({'enableRateLimit': True}),
    "WOO X": lambda: ccxt.woo({'enableRateLimit': True}),
    "Crypto.com": lambda: ccxt.cryptocom({'enableRateLimit': True}),
    "Bitstamp": lambda: ccxt.bitstamp({'enableRateLimit': True}),
    "Gemini": lambda: ccxt.gemini({'enableRateLimit': True}),
    "Poloniex": lambda: ccxt.poloniex({'enableRateLimit': True}),
    "BitMart": lambda: ccxt.bitmart({'enableRateLimit': True}),
    "AscendEX": lambda: ccxt.ascendex({'enableRateLimit': True}),
    "LBank": lambda: ccxt.lbank({'enableRateLimit': True}),
    "ProBit": lambda: ccxt.probit({'enableRateLimit': True}),
    "Deribit": lambda: ccxt.deribit({'enableRateLimit': True}),
    "Exmo": lambda: ccxt.exmo({'enableRateLimit': True}),
    "WhiteBit": lambda: ccxt.whitebit({'enableRateLimit': True}),
    "XT.com": lambda: ccxt.xt({'enableRateLimit': True}),
    "CoinEx": lambda: ccxt.coinex({'enableRateLimit': True}),
    "Toobit": lambda: ccxt.toobit({'enableRateLimit': True}),
    "Hyperliquid": lambda: ccxt.hyperliquid({'enableRateLimit': True}),
    "Bitvavo": lambda: ccxt.bitvavo({'enableRateLimit': True}),
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Validador v8.2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helper: set module-level globals before running
# ---------------------------------------------------------------------------
def inject_globals(params):
    global SL_PERCENT, SL_EMERGENCY_PERCENT, TS_PERCENT, COOLDOWN_BARS, COMMISSION_ROUND_TRIP
    global HYST_ATR_LEN, DIV_RSI_LEN, DIV_MACD_FAST, DIV_MACD_SLOW, DIV_MACD_SIGNAL
    global DIV_STOCH_K, DIV_STOCH_D, DIV_STOCH_SMOOTH, DIV_VWMACD_FAST, DIV_VWMACD_SLOW
    global DIV_CMF_LEN, DIV_CCI_LEN, DIV_MOM_LEN, DIV_PIVOT_PERIOD, DIV_MAX_PIVOTS, DIV_MAX_BARS
    SL_PERCENT = params['sl_percent']
    SL_EMERGENCY_PERCENT = params['sl_emergency_percent']
    TS_PERCENT = params['ts_percent']
    COOLDOWN_BARS = params['cooldown_bars']
    COMMISSION_ROUND_TRIP = params['commission']
    HYST_ATR_LEN = params['hyst_atr_len']
    DIV_RSI_LEN = params['div_rsi_len']
    DIV_MACD_FAST = params['div_macd_fast']
    DIV_MACD_SLOW = params['div_macd_slow']
    DIV_MACD_SIGNAL = params['div_macd_signal']
    DIV_STOCH_K = params['div_stoch_k']
    DIV_STOCH_D = params['div_stoch_d']
    DIV_STOCH_SMOOTH = params['div_stoch_smooth']
    DIV_VWMACD_FAST = params['div_vwmacd_fast']
    DIV_VWMACD_SLOW = params['div_vwmacd_slow']
    DIV_CMF_LEN = params['div_cmf_len']
    DIV_CCI_LEN = params['div_cci_len']
    DIV_MOM_LEN = params['div_mom_len']
    DIV_PIVOT_PERIOD = params['div_pivot_period']
    DIV_MAX_PIVOTS = params['div_max_pivots']
    DIV_MAX_BARS = params['div_max_bars']

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Validador v8.2")

    # --- 1. Data Source ---
    st.header("1. Data Source")
    exchange_name = st.selectbox("Exchange", list(EXCHANGES.keys()), index=0)
    symbol = st.text_input("Symbol (e.g. BTC/USDT)", value="ETH/USDT", key="sym_custom").strip().upper()
    if not symbol:
        st.warning("Enter a valid symbol pair.")
    timeframe = st.selectbox("Timeframe", ["1h"], index=0)
    period_mode = st.radio("Period selection", ["By candles", "By date range"], horizontal=True, key="period_mode")
    if period_mode == "By candles":
        total_candles = st.number_input("Total Candles", min_value=1000, max_value=50000, value=20000, step=1000)
        date_since_ms = None
        date_until_ms = None
    else:
        default_start = date.today() - timedelta(days=365)
        dc1, dc2 = st.columns(2)
        with dc1:
            start_date = st.date_input("Start date", value=default_start, key="start_date")
            start_time = st.text_input("Start time (HH:MM)", value="00:00", key="start_time")
        with dc2:
            end_date = st.date_input("End date", value=date.today(), key="end_date")
            end_time = st.text_input("End time (HH:MM)", value="00:00", key="end_time")
        try:
            sh, sm = [int(x) for x in start_time.split(":")]
            eh, em = [int(x) for x in end_time.split(":")]
            dt_start = datetime(start_date.year, start_date.month, start_date.day, sh, sm)
            dt_end = datetime(end_date.year, end_date.month, end_date.day, eh, em)
            date_since_ms = int(dt_start.timestamp() * 1000)
            date_until_ms = int(dt_end.timestamp() * 1000)
            if date_since_ms >= date_until_ms:
                st.warning("Start date must be before end date.")
            tf_ms_map = {'1h': 3600000, '4h': 14400000, '1d': 86400000}
            estimated_candles = (date_until_ms - date_since_ms) // tf_ms_map.get(timeframe, 3600000)
            st.caption(f"~{estimated_candles:,} candles estimated")
        except (ValueError, IndexError):
            st.warning("Invalid time format. Use HH:MM (e.g. 14:30)")
            date_since_ms = None
            date_until_ms = None
        total_candles = 50000  # fallback max, date range controls actual download

    # --- Config ID (auto-fill) ---
    st.header("Config ID (optional)")
    def _apply_config_id():
        """Callback: decode config_id and set all dependent widget values."""
        cid = st.session_state.get('input_config_id', 0)
        if cid <= 0:
            return
        d = decode_config(int(cid))
        # Entry TFs
        st.session_state['e_tf1'] = bool(d['entry_mask'] & 1)
        st.session_state['e_tf2'] = bool(d['entry_mask'] & 2)
        st.session_state['e_tf3'] = bool(d['entry_mask'] & 4)
        st.session_state['e_tf4'] = bool(d['entry_mask'] & 8)
        st.session_state['e_tf5'] = bool(d['entry_mask'] & 16)
        # Exit TFs
        st.session_state['x_tf1'] = bool(d['exit_mask'] & 1)
        st.session_state['x_tf2'] = bool(d['exit_mask'] & 2)
        st.session_state['x_tf3'] = bool(d['exit_mask'] & 4)
        st.session_state['x_tf4'] = bool(d['exit_mask'] & 8)
        # Divergencias
        st.session_state['div_entry_mode_sel'] = ["OFF", "Contextual", "Direct (OR)"][d['div_entry_mode']]
        st.session_state['div_exit'] = bool(d['div_exit'])
        st.session_state['div_type_sel'] = ["None", "Regular", "Hidden", "Both"][d['div_type']]
        # Indicators
        for i in range(8):
            st.session_state[f'ind{i}'] = bool((d['div_ind_mask'] >> i) & 1)
        # Variant / flags
        st.session_state['reg_inv'] = bool(d['reg_inv'])
        st.session_state['hid_inv'] = bool(d['hid_inv'])
        st.session_state['cancel_tf'] = bool(d['cancel_tf'])
        st.session_state['use_ts'] = bool(d['use_ts'])

    st.number_input("Config ID", min_value=0, max_value=2**26-1, value=0,
                     step=1, key="input_config_id", on_change=_apply_config_id,
                     help="Enter a config_id to auto-fill Entry/Exit TFs, Divergences, and flags below.")
    if st.session_state.get('input_config_id', 0) > 0:
        st.caption(f"Config {st.session_state['input_config_id']} applied")

    # --- 2. Config ---
    st.header("2. Entry TFs")
    mcols = st.columns(5)
    entry_tf1 = mcols[0].checkbox("TF1", value=True, key="e_tf1")
    entry_tf2 = mcols[1].checkbox("TF2", value=False, key="e_tf2")
    entry_tf3 = mcols[2].checkbox("TF3", value=False, key="e_tf3")
    entry_tf4 = mcols[3].checkbox("TF4", value=True, key="e_tf4")
    entry_tf5 = mcols[4].checkbox("TF5", value=True, key="e_tf5")
    entry_mask = (entry_tf1 * 1) | (entry_tf2 * 2) | (entry_tf3 * 4) | (entry_tf4 * 8) | (entry_tf5 * 16)

    st.header("3. Exit TFs")
    xcols = st.columns(4)
    exit_tf1 = xcols[0].checkbox("TF1", value=True, key="x_tf1")
    exit_tf2 = xcols[1].checkbox("TF2", value=False, key="x_tf2")
    exit_tf3 = xcols[2].checkbox("TF3", value=False, key="x_tf3")
    exit_tf4 = xcols[3].checkbox("TF4", value=False, key="x_tf4")
    exit_mask = (exit_tf1 * 1) | (exit_tf2 * 2) | (exit_tf3 * 4) | (exit_tf4 * 8)
    if exit_mask == 0:
        st.caption("Exit mode: ZONA")

    # --- 4. Zones (MAs) ---
    st.header("4. Zones (MAs)")
    st.subheader("Fast MA")
    fast_type = st.selectbox("Type", MA_TYPES, index=MA_TYPES.index("McGinley"), key="fast_type")
    fast_len = st.number_input("Length", min_value=2, max_value=100, value=20, key="fast_len")
    fast_p1 = st.number_input("p1", min_value=0.0, max_value=10.0, value=0.0, step=0.1, key="fast_p1") if fast_type in NEEDS_P1 else 0.0
    fast_p2 = st.number_input("p2", min_value=0.0, max_value=10.0, value=0.0, step=0.1, key="fast_p2") if fast_type in NEEDS_P2 else 0.0

    st.subheader("Slow MA")
    slow_type = st.selectbox("Type", MA_TYPES, index=MA_TYPES.index("KAMA"), key="slow_type")
    slow_len = st.number_input("Length", min_value=2, max_value=300, value=48, key="slow_len")
    slow_p1 = st.number_input("p1", min_value=0.0, max_value=10.0, value=0.0, step=0.1, key="slow_p1") if slow_type in NEEDS_P1 else 0.0
    slow_p2 = st.number_input("p2", min_value=0.0, max_value=10.0, value=0.0, step=0.1, key="slow_p2") if slow_type in NEEDS_P2 else 0.0

    st.subheader("Trend MA")
    use_trend_ma = st.checkbox("Enable Trend MA", value=True, key="use_trend")
    if use_trend_ma:
        trend_type = st.selectbox("Type", MA_TYPES, index=MA_TYPES.index("KAMA"), key="trend_type")
        trend_len = st.number_input("Length", min_value=2, max_value=500, value=192, key="trend_len")
        trend_p1 = st.number_input("p1", min_value=0.0, max_value=10.0, value=0.0, step=0.1, key="trend_p1") if trend_type in NEEDS_P1 else 0.0
        trend_p2 = st.number_input("p2", min_value=0.0, max_value=10.0, value=0.0, step=0.1, key="trend_p2") if trend_type in NEEDS_P2 else 0.0
    else:
        trend_type = "NONE"; trend_len = 1; trend_p1 = 0.0; trend_p2 = 0.0

    selected_preset = (fast_type, fast_len, fast_p1, fast_p2,
                       slow_type, slow_len, slow_p1, slow_p2,
                       trend_type, trend_len, trend_p1, trend_p2)

    # --- 5. Hysteresis ---
    st.header("5. Hysteresis ATR")
    hyst_mult = st.slider("Hyst Multiplier", 0.0, 1.0, 0.0, 0.05, key="hyst_mult")
    hyst_atr_len = st.number_input("ATR Period", min_value=1, max_value=50, value=14, key="hyst_atr_len")

    # --- 6. Exit Management ---
    st.header("6. Exit Management")
    sl_percent = st.number_input("SL %", min_value=0.5, max_value=20.0, value=3.0, step=0.5, key="sl_pct")
    ts_percent = st.number_input("TS %", min_value=0.1, max_value=10.0, value=0.5, step=0.1, key="ts_pct")
    cooldown_bars = st.number_input("Cooldown Bars", min_value=0, max_value=10, value=1, step=1, key="cooldown")
    commission = st.number_input("Commission % (RT)", min_value=0.0, max_value=1.0, value=0.10, step=0.01, key="comm")

    # --- 7. Emergency SL ---
    st.header("7. Emergency SL")
    sl_emergency = st.number_input("Emergency SL %", min_value=1.0, max_value=30.0, value=5.0, step=0.5, key="sl_emerg")

    # --- 8. Divergencias ---
    st.header("8. Divergencias")
    div_entry_mode = st.selectbox("Entry Mode", ["OFF", "Contextual", "Direct (OR)"], index=1, key="div_entry_mode_sel")
    div_entry_mode_val = ["OFF", "Contextual", "Direct (OR)"].index(div_entry_mode)
    div_exit = st.checkbox("Div Exit", value=True, key="div_exit")
    div_type = st.selectbox("Div Type", ["None", "Regular", "Hidden", "Both"], index=3, key="div_type_sel")
    div_type_val = ["None", "Regular", "Hidden", "Both"].index(div_type)

    st.subheader("Oscillators")
    icols1 = st.columns(4)
    icols2 = st.columns(4)
    ind_rsi = icols1[0].checkbox("RSI", value=True, key="ind0")
    ind_macdh = icols1[1].checkbox("MACD_H", value=True, key="ind1")
    ind_macdl = icols1[2].checkbox("MACD_L", value=True, key="ind2")
    ind_stoch = icols1[3].checkbox("STOCH", value=True, key="ind3")
    ind_vwmacd = icols2[0].checkbox("VWMACD", value=True, key="ind4")
    ind_cmf = icols2[1].checkbox("CMF", value=True, key="ind5")
    ind_cci = icols2[2].checkbox("CCI", value=True, key="ind6")
    ind_mom = icols2[3].checkbox("MOM", value=True, key="ind7")
    div_ind_mask = (ind_rsi*1 | ind_macdh*2 | ind_macdl*4 | ind_stoch*8 |
                    ind_vwmacd*16 | ind_cmf*32 | ind_cci*64 | ind_mom*128)

    reg_inv = st.checkbox("Reg Inverted", value=False, key="reg_inv")
    hid_inv = st.checkbox("Hid Inverted", value=True, key="hid_inv")

    cancel_tf = st.checkbox("Cancel TF", value=True, key="cancel_tf")
    use_ts = st.checkbox("Trailing Stop", value=False, key="use_ts")

    # --- 9. Oscillator Params (advanced) ---
    with st.expander("9. Oscillator Params (Advanced)"):
        div_rsi_len = st.number_input("RSI Length", 2, 50, 14, key="osc_rsi")
        c1, c2, c3 = st.columns(3)
        div_macd_fast = c1.number_input("MACD Fast", 2, 50, 12, key="osc_mf")
        div_macd_slow = c2.number_input("MACD Slow", 2, 100, 26, key="osc_ms")
        div_macd_signal = c3.number_input("MACD Signal", 2, 50, 9, key="osc_msig")
        c4, c5, c6 = st.columns(3)
        div_stoch_k = c4.number_input("Stoch K", 2, 50, 14, key="osc_sk")
        div_stoch_d = c5.number_input("Stoch D", 1, 20, 3, key="osc_sd")
        div_stoch_smooth = c6.number_input("Stoch Smooth", 1, 20, 3, key="osc_ss")
        c7, c8 = st.columns(2)
        div_vwmacd_fast = c7.number_input("VW-MACD Fast", 2, 50, 12, key="osc_vf")
        div_vwmacd_slow = c8.number_input("VW-MACD Slow", 2, 100, 26, key="osc_vs")
        div_cmf_len = st.number_input("CMF Length", 2, 100, 21, key="osc_cmf")
        div_cci_len = st.number_input("CCI Length", 2, 100, 10, key="osc_cci")
        div_mom_len = st.number_input("MOM Length", 2, 100, 10, key="osc_mom")
        div_pivot_period = st.number_input("Pivot Period", 1, 20, 5, key="osc_pp")
        div_max_pivots = st.number_input("Max Pivots", 1, 50, 10, key="osc_mp")
        div_max_bars = st.number_input("Max Bars", 10, 500, 100, key="osc_mb")

    # --- RUN button ---
    st.divider()
    run_clicked = st.button("Run Validation", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Compute config_id from manual params
# ---------------------------------------------------------------------------
final_config_id = encode_config_id(
    entry_mask, exit_mask, div_entry_mode_val, int(div_exit),
    div_type_val, div_ind_mask, int(cancel_tf), int(use_ts),
    int(reg_inv), int(hid_inv)
)

# ---------------------------------------------------------------------------
# Build params dict
# ---------------------------------------------------------------------------
params = dict(
    sl_percent=sl_percent,
    sl_emergency_percent=sl_emergency,
    ts_percent=ts_percent,
    cooldown_bars=cooldown_bars,
    commission=commission,
    hyst_atr_len=hyst_atr_len,
    div_rsi_len=div_rsi_len,
    div_macd_fast=div_macd_fast,
    div_macd_slow=div_macd_slow,
    div_macd_signal=div_macd_signal,
    div_stoch_k=div_stoch_k,
    div_stoch_d=div_stoch_d,
    div_stoch_smooth=div_stoch_smooth,
    div_vwmacd_fast=div_vwmacd_fast,
    div_vwmacd_slow=div_vwmacd_slow,
    div_cmf_len=div_cmf_len,
    div_cci_len=div_cci_len,
    div_mom_len=div_mom_len,
    div_pivot_period=div_pivot_period,
    div_max_pivots=div_max_pivots,
    div_max_bars=div_max_bars,
)

# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------
if run_clicked:
    inject_globals(params)

    # Inject selected exchange
    try:
        exchange = EXCHANGES[exchange_name]()
    except Exception as exc:
        st.error(f"Failed to create exchange {exchange_name}: {exc}")
        st.stop()

    if date_since_ms is not None and date_until_ms is not None:
        dl_label = f"Downloading candles from {exchange_name} (date range)..."
        cache_key_dl = (exchange_name, symbol, timeframe, date_since_ms, date_until_ms)
    else:
        dl_label = f"Downloading {total_candles} candles from {exchange_name}..."
        cache_key_dl = (exchange_name, symbol, timeframe, total_candles)

    with st.spinner(dl_label):
        if 'dl_cache_key' not in st.session_state or st.session_state['dl_cache_key'] != cache_key_dl:
            df_raw = fetch_all_candles(symbol, timeframe, total_candles,
                                       since_ms=date_since_ms, until_ms=date_until_ms)
            if df_raw is None or len(df_raw) == 0:
                st.error(f"Failed to download {symbol} from {exchange_name}. Check the pair exists on this exchange.")
                st.stop()
            st.session_state['dl_cache_key'] = cache_key_dl
            st.session_state['df_raw'] = df_raw
        else:
            df_raw = st.session_state['df_raw']

    with st.spinner("Pre-calculating indicators (this may take several minutes for 20K candles)..."):
        data = precalculate_all_data(df_raw, preset=selected_preset, hyst_mult=hyst_mult, symbol=symbol)

    with st.spinner("Running simulation..."):
        t0 = time.time()
        trades, total_pnl, max_dd, gp, gl = run_single_config(data, final_config_id)
        elapsed = time.time() - t0

    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    pf = gp / gl if gl > 0 else 999.0
    cfg = decode_config(final_config_id)

    st.session_state['results'] = {
        'trades_df': trades_df, 'total_pnl': total_pnl, 'max_dd': max_dd,
        'gross_profit': gp, 'gross_loss': gl, 'profit_factor': pf,
        'data': data, 'config_decoded': cfg, 'elapsed': elapsed,
    }
    st.session_state['run_symbol'] = symbol
    st.session_state['run_config_id'] = final_config_id

# ---------------------------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------------------------
if 'results' not in st.session_state:
    st.info("Configure parameters in the sidebar and click **Run Validation**.")
    st.stop()

result = st.session_state['results']
tdf = result['trades_df']
data = result['data']
cfg = result['config_decoded']
total_pnl = result['total_pnl']
max_dd = result['max_dd']
gp = result['gross_profit']
gl = result['gross_loss']
pf = result['profit_factor']
elapsed = result['elapsed']

st.title(f"{st.session_state.get('run_symbol', '')} | Config {st.session_state.get('run_config_id', '')}")

tab_summary, tab_chart, tab_trades, tab_equity = st.tabs(
    ["Summary", "Price Chart", "Trade List", "Equity & Drawdown"]
)

# ========================= TAB 1: SUMMARY =========================
with tab_summary:
    n_trades = len(tdf)
    if n_trades > 0:
        w = tdf[tdf['pnl'] > 0]
        l = tdf[tdf['pnl'] <= 0]
        wr = len(w) / n_trades * 100
        avg_win = w['pnl'].mean() if len(w) > 0 else 0
        avg_loss = l['pnl'].mean() if len(l) > 0 else 0

        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
        mc1.metric("Total PnL", f"{total_pnl:+.2f}%")
        mc2.metric("Max DD", f"{max_dd:.2f}%")
        mc3.metric("Profit Factor", f"{pf:.2f}")
        mc4.metric("Win Rate", f"{wr:.1f}%")
        mc5.metric("Trades", n_trades)
        mc6.metric("Time", f"{elapsed:.1f}s")

        mc7, mc8, mc9, mc10 = st.columns(4)
        mc7.metric("Avg Win", f"{avg_win:+.2f}%")
        mc8.metric("Avg Loss", f"{avg_loss:+.2f}%")
        mc9.metric("Gross Profit", f"{gp:.2f}%")
        mc10.metric("Gross Loss", f"{gl:.2f}%")

        st.subheader("Config Details")
        st.code(
            f"Entry: {'+'.join(cfg['entry_tfs']) or 'ZONA'} | Exit: {'+'.join(cfg['exit_tfs'])}\n"
            f"Div Entry: {cfg['div_mode_str']} | Div Exit: {'ON' if cfg['div_exit'] else 'OFF'} | Type: {cfg['div_type_str']}\n"
            f"Inds: {'+'.join(cfg['div_indicators'])}\n"
            f"Cancel: {cfg['cancel_str']} | SL: {cfg['ts_str']} | Variant: {cfg['variant']}",
            language=None
        )

        st.subheader("Exit Reasons")
        reason_stats = []
        for r, cnt in tdf['reason'].value_counts().items():
            sub = tdf[tdf['reason'] == r]
            reason_stats.append({
                'Reason': r, 'Count': cnt, '%': f"{cnt/n_trades*100:.0f}%",
                'Avg PnL': f"{sub['pnl'].mean():+.2f}%",
                'Total PnL': f"{sub['pnl'].sum():+.2f}%",
            })
        st.dataframe(pd.DataFrame(reason_stats), use_container_width=True, hide_index=True)

        st.subheader("Long vs Short")
        side_stats = []
        for s in ['L', 'S']:
            sub = tdf[tdf['side'] == s]
            if len(sub) > 0:
                sw = sub[sub['pnl'] > 0]
                side_stats.append({
                    'Side': 'Long' if s == 'L' else 'Short', 'Trades': len(sub),
                    'PnL': f"{sub['pnl'].sum():+.2f}%", 'WR': f"{len(sw)/len(sub)*100:.0f}%",
                    'Avg PnL': f"{sub['pnl'].mean():+.2f}%",
                })
        st.dataframe(pd.DataFrame(side_stats), use_container_width=True, hide_index=True)

        st.subheader("Train/Test Split (75/25)")
        n_bars = len(data['close'])
        train_end = int(n_bars * 0.75)
        train_date = str(pd.Timestamp(data['timestamps'][train_end]))[:16]
        train_trades = tdf[tdf['entry_date'] <= train_date]
        test_trades = tdf[tdf['entry_date'] > train_date]
        tc1, tc2 = st.columns(2)
        tc1.metric("Train", f"{len(train_trades)} trades | {train_trades['pnl'].sum():+.2f}%")
        tc2.metric("Test", f"{len(test_trades)} trades | {test_trades['pnl'].sum():+.2f}%")

        st.subheader("Duration Breakdown")
        dur_stats = []
        for lb, lo, hi in [("1 bar", 1, 1), ("2-5 bars", 2, 5), ("6-24 bars", 6, 24),
                           ("1-7 days", 25, 168), (">7 days", 169, 99999)]:
            sub = tdf[(tdf['bars'] >= lo) & (tdf['bars'] <= hi)]
            if len(sub) > 0:
                dur_stats.append({'Duration': lb, 'Count': len(sub),
                    'Avg PnL': f"{sub['pnl'].mean():+.2f}%", 'Total PnL': f"{sub['pnl'].sum():+.2f}%"})
        if dur_stats:
            st.dataframe(pd.DataFrame(dur_stats), use_container_width=True, hide_index=True)
    else:
        st.warning("No trades generated with this configuration.")

# ========================= TAB 2: PRICE CHART =========================
with tab_chart:
    if n_trades > 0:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        timestamps = pd.to_datetime(data['timestamps'])
        chart_window = st.slider("Visible candles (from end)", 500, len(timestamps), min(2000, len(timestamps)), 100)
        start_idx = max(0, len(timestamps) - chart_window)

        ts_slice = timestamps[start_idx:]
        o_slice = data['open'][start_idx:]
        h_slice = data['high'][start_idx:]
        l_slice = data['low'][start_idx:]
        c_slice = data['close'][start_idx:]
        v_slice = data['volume'][start_idx:]
        zb_slice = data['zone_bull'][start_idx:]
        zbr_slice = data['zone_bear'][start_idx:]
        fast_slice = data['ema_fast'][start_idx:]
        slow_slice = data['ema_slow'][start_idx:]
        trend_slice = data['ma_trend'][start_idx:]

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.8, 0.2], vertical_spacing=0.03)

        fig.add_trace(go.Candlestick(
            x=ts_slice, open=o_slice, high=h_slice, low=l_slice, close=c_slice,
            name="OHLC", increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
        ), row=1, col=1)

        # Zone backgrounds
        zone_changes = []; current_zone = None
        for i in range(len(ts_slice)):
            z = 'bull' if zb_slice[i] else ('bear' if zbr_slice[i] else None)
            if z != current_zone:
                if current_zone is not None: zone_changes.append((zone_start, i - 1, current_zone))
                zone_start = i; current_zone = z
        if current_zone is not None: zone_changes.append((zone_start, len(ts_slice) - 1, current_zone))
        for s, e, z in zone_changes:
            color = "rgba(38, 166, 154, 0.07)" if z == 'bull' else "rgba(239, 83, 80, 0.07)"
            fig.add_vrect(x0=ts_slice[s], x1=ts_slice[e], fillcolor=color, layer="below", line_width=0, row=1, col=1)

        fig.add_trace(go.Scatter(x=ts_slice, y=fast_slice, name="Fast MA", line=dict(width=1, color='#42a5f5')), row=1, col=1)
        fig.add_trace(go.Scatter(x=ts_slice, y=slow_slice, name="Slow MA", line=dict(width=1, color='#ffa726')), row=1, col=1)
        if not np.all(np.isnan(trend_slice)):
            fig.add_trace(go.Scatter(x=ts_slice, y=trend_slice, name="Trend MA", line=dict(width=1, color='#ab47bc', dash='dot')), row=1, col=1)

        # Trade markers — positioned above/below candles
        ts_str_index = pd.Series(range(len(ts_slice)), index=pd.to_datetime(ts_slice).strftime('%Y-%m-%d %H:%M'))
        price_range = np.nanmax(h_slice) - np.nanmin(l_slice)
        offset_pct = 0.012

        def get_candle_y(date_str, arr, direction):
            idx = ts_str_index.get(date_str[:16])
            if idx is not None: return arr[idx] + direction * price_range * offset_pct
            return None

        min_date = str(ts_slice.min())[:16]; max_date = str(ts_slice.max())[:16]

        # Long entries below low
        visible_long = tdf[(tdf['side'] == 'L') & (tdf['entry_date'] >= min_date) & (tdf['entry_date'] <= max_date)]
        if len(visible_long) > 0:
            y_vals = [get_candle_y(d, l_slice, -1) or p for d, p in zip(visible_long['entry_date'], visible_long['entry_price'])]
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(visible_long['entry_date']), y=y_vals, mode='markers', name='Long Entry',
                marker=dict(symbol='triangle-up', size=14, color='#26a69a', line=dict(width=1, color='white')),
                hovertext=[f"L entry #{n} @ {p:.2f}" for n, p in zip(visible_long['num'], visible_long['entry_price'])],
                hoverinfo='text',
            ), row=1, col=1)

        # Short entries above high
        visible_short = tdf[(tdf['side'] == 'S') & (tdf['entry_date'] >= min_date) & (tdf['entry_date'] <= max_date)]
        if len(visible_short) > 0:
            y_vals = [get_candle_y(d, h_slice, 1) or p for d, p in zip(visible_short['entry_date'], visible_short['entry_price'])]
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(visible_short['entry_date']), y=y_vals, mode='markers', name='Short Entry',
                marker=dict(symbol='triangle-down', size=14, color='#ef5350', line=dict(width=1, color='white')),
                hovertext=[f"S entry #{n} @ {p:.2f}" for n, p in zip(visible_short['num'], visible_short['entry_price'])],
                hoverinfo='text',
            ), row=1, col=1)

        # Exits
        exits_visible = tdf[(tdf['exit_date'] >= min_date) & (tdf['exit_date'] <= max_date)]
        if len(exits_visible) > 0:
            exit_colors = ['#26a69a' if p > 0 else '#ef5350' for p in exits_visible['pnl']]
            y_vals = []
            for _, row in exits_visible.iterrows():
                if row['pnl'] > 0: y = get_candle_y(row['exit_date'], h_slice, 1.5) or row['exit_price']
                else: y = get_candle_y(row['exit_date'], l_slice, -1.5) or row['exit_price']
                y_vals.append(y)
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(exits_visible['exit_date']), y=y_vals, mode='markers', name='Exit',
                marker=dict(symbol='x', size=12, color=exit_colors, line=dict(width=2)),
                hovertext=[f"Exit #{n} {r} PnL:{p:+.2f}%" for n, r, p in
                           zip(exits_visible['num'], exits_visible['reason'], exits_visible['pnl'])],
                hoverinfo='text',
            ), row=1, col=1)

        # Volume
        vol_colors = ['#26a69a' if c_slice[i] >= o_slice[i] else '#ef5350' for i in range(len(v_slice))]
        fig.add_trace(go.Bar(x=ts_slice, y=v_slice, name="Volume", marker_color=vol_colors, opacity=0.5), row=2, col=1)

        fig.update_layout(height=700, xaxis_rangeslider_visible=False, template="plotly_dark", showlegend=True,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No trades to display on chart.")

# ========================= TAB 3: TRADE LIST =========================
with tab_trades:
    if n_trades > 0:
        display_cols = ['num', 'side', 'entry_date', 'exit_date', 'entry_price', 'exit_price',
                        'pnl', 'cumul', 'bars', 'reason', 'entry_filters']
        available_cols = [c for c in display_cols if c in tdf.columns]

        def color_pnl(val):
            if isinstance(val, (int, float)):
                color = '#26a69a' if val > 0 else '#ef5350' if val < 0 else '#888'
                return f'color: {color}'
            return ''

        styled = tdf[available_cols].style.applymap(color_pnl, subset=['pnl', 'cumul'])
        st.dataframe(styled, use_container_width=True, height=600, hide_index=True)

        csv_data = tdf.to_csv(index=False)
        st.download_button("Download CSV", csv_data,
            file_name=f"trades_{st.session_state.get('run_symbol','').replace('/','')}_cfg{st.session_state.get('run_config_id','')}.csv",
            mime="text/csv")
    else:
        st.warning("No trades.")

# ========================= TAB 4: EQUITY & DRAWDOWN =========================
with tab_equity:
    if n_trades > 0:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        equity = tdf['cumul'].values
        peak = np.maximum.accumulate(equity)
        dd = peak - equity

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.65, 0.35], vertical_spacing=0.05)

        fig.add_trace(go.Scatter(
            x=pd.to_datetime(tdf['exit_date']), y=equity, name="Equity",
            line=dict(color='#42a5f5', width=2), fill='tozeroy', fillcolor='rgba(66,165,245,0.1)',
        ), row=1, col=1)

        # Train/Test split line
        n_bars = len(data['close'])
        train_end = int(n_bars * 0.75)
        train_dt = pd.Timestamp(data['timestamps'][train_end])
        fig.add_shape(type="line", x0=train_dt, x1=train_dt, y0=0, y1=1,
                      yref="y domain", line=dict(dash="dash", color="yellow", width=1), row=1, col=1)
        fig.add_annotation(x=train_dt, y=1, yref="y domain", text="Train/Test",
                           showarrow=False, font=dict(color="yellow", size=10), yanchor="bottom", row=1, col=1)

        fig.add_trace(go.Scatter(
            x=pd.to_datetime(tdf['exit_date']), y=-dd, name="Drawdown",
            line=dict(color='#ef5350', width=1), fill='tozeroy', fillcolor='rgba(239,83,80,0.2)',
        ), row=2, col=1)

        fig.update_layout(height=550, template="plotly_dark", showlegend=True,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="Cumulative PnL %", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No trades to display equity curve.")
