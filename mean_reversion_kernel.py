#!/usr/bin/env python
"""
mean_reversion_kernel.py -- Kernel de simulacion Mean-Reversion con cancelaciones

Config: 17 bits
  bits 0-3:   exit_mask   (TF1..TF4)
  bits 4-8:   entry_mask  (TF1..TF5)
  bits 9-10:  div_entry_mode (0=OFF, 1=AND, 2=OR)
  bit 11:     div_exit
  bits 12-13: div_type (0=none, 1=Regular, 2=Hidden corregida, 3=Both corregida)
  bit 14:     cancel_zona
  bit 15:     cancel_tf
  bit 16:     cancel_ghost

Uso:
    python mean_reversion_kernel.py --test BTC/USDT
"""

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
from numba import jit, prange

from master import CONFIG

# ---------------------------------------------------------------------------
# Constants (same as existing pipeline)
# ---------------------------------------------------------------------------
DATA_CACHE_DIR = CONFIG['data_cache_dir']
SYMBOLS = CONFIG['symbols']

SL_PERCENT = 3.0
SL_EMERGENCY_PERCENT = 5.0
TS_PERCENT = 0.5
COOLDOWN_BARS = 1
COMMISSION_ROUND_TRIP = 0.10

# Default: RSI only (bit 0)
DEFAULT_DIV_IND_MASK = 1


# ============================================
# KERNEL NUMBA
# ============================================

@jit(nopython=True, parallel=True, cache=True)
def run_mean_reversion_numba(
    configs,
    close_arr, high_arr, low_arr,
    timestamps_i64,
    zone_bull_forming, zone_bear_forming,
    zone_bull_resolved, zone_bear_resolved,
    filters_forming, filters_resolved,
    fast_line_arr, slow_line_forming_arr,
    div_bits_arr,
    div_ind_mask,
    sl_pct, sl_emergency_pct, ts_pct,
    cooldown_bars, commission_pct,
    accounting_start=100
):
    n_configs = len(configs)
    n_bars = len(close_arr)
    results = np.zeros((n_configs, 7), dtype=np.float64)

    for c in prange(n_configs):
        cfg = configs[c]

        # --- Decode config ---
        exit_mask       = cfg & 0xF
        entry_mask      = (cfg >> 4) & 0x1F
        div_entry_mode  = (cfg >> 9) & 0x3
        div_exit        = (cfg >> 11) & 0x1
        div_type        = (cfg >> 12) & 0x3
        cancel_zona_bit = (cfg >> 14) & 0x1
        cancel_tf_bit   = (cfg >> 15) & 0x1
        cancel_ghost_bit = (cfg >> 16) & 0x1

        # --- State ---
        position = 0
        entry_price = 0.0
        entry_bar = 0
        entry_filters_forming = 0

        pnl = 0.0
        trades = 0
        wins = 0
        cancels = 0
        peak_pnl = 0.0
        max_dd = 0.0
        gross_profit = 0.0
        gross_loss = 0.0

        div_ctx_bull = False
        div_ctx_bear = False
        last_zone_bull = False

        # Pine-faithful delay: entries use div from PREVIOUS bar
        prev_div_bull_now = False
        prev_div_bear_now = False
        div_bull_now_saved = False
        div_bear_now_saved = False

        cooldown_until = 0
        sl_level = 0.0

        entry_tf_count = 0
        for bit in range(5):
            if (entry_mask >> bit) & 1:
                entry_tf_count += 1

        exit_tf_count = 0
        for bit in range(4):
            if (exit_mask >> bit) & 1:
                exit_tf_count += 1

        acct_start = accounting_start

        # =============================================
        # BAR LOOP
        # =============================================
        for t in range(1, n_bars):
            z_bull = zone_bull_forming[t]
            z_bear = zone_bear_forming[t]
            f_forming = filters_forming[t]
            f_resolved = filters_resolved[t]

            close_p = close_arr[t]
            high_p = high_arr[t]
            low_p = low_arr[t]

            # --- Pine-faithful: save previous bar's div state ---
            prev_div_bull_now = div_bull_now_saved
            prev_div_bear_now = div_bear_now_saved

            # Phase 1: Zone change resets
            zone_changed_to_bear = z_bear and last_zone_bull
            zone_changed_to_bull = z_bull and not last_zone_bull

            if zone_changed_to_bear:
                div_ctx_bull = False
            if zone_changed_to_bull:
                div_ctx_bear = False

            # Phase 2: div_ctx update from PREVIOUS bar
            if prev_div_bull_now:
                div_ctx_bull = True
                div_ctx_bear = False
            if prev_div_bear_now:
                div_ctx_bear = True
                div_ctx_bull = False

            # Snapshot for entry evaluation
            entry_div_ctx_bull = div_ctx_bull
            entry_div_ctx_bear = div_ctx_bear

            last_zone_bull = z_bull

            # Phase 3: Divergence for CURRENT bar
            div_bull_now = False
            div_bear_now = False

            if div_type > 0 and div_ind_mask > 0:
                net_div_score = 0
                for ind in range(8):
                    if not (div_ind_mask & (1 << ind)):
                        continue
                    bits = div_bits_arr[t, ind]
                    ind_bull = False
                    ind_bear = False

                    if div_type == 1:
                        # Regular only
                        ind_bull = (bits & 1) > 0   # bit0 = Regular Bull
                        ind_bear = (bits & 4) > 0   # bit2 = Regular Bear

                    elif div_type == 2:
                        # Hidden only (bits already corrected in precalc)
                        ind_bull = (bits & 2) > 0   # bit1 = Hidden Bull
                        ind_bear = (bits & 8) > 0   # bit3 = Hidden Bear

                    elif div_type == 3:
                        # Both: Regular + Hidden
                        reg_bull = (bits & 1) > 0
                        reg_bear = (bits & 4) > 0
                        hid_bull = (bits & 2) > 0   # bit1 = Hidden Bull
                        hid_bear = (bits & 8) > 0   # bit3 = Hidden Bear
                        ind_bull = reg_bull or hid_bull
                        ind_bear = reg_bear or hid_bear

                    if ind_bull:
                        net_div_score += 1
                    if ind_bear:
                        net_div_score -= 1

                div_bull_now = net_div_score >= 1
                div_bear_now = net_div_score <= -1

            # Save for next bar's entry
            div_bull_now_saved = div_bull_now
            div_bear_now_saved = div_bear_now

            # Phase 4: Update div_ctx with CURRENT bar (after entry evaluated)
            if div_bull_now:
                div_ctx_bull = True
            if div_bear_now:
                div_ctx_bear = True

            # =============================================
            # EXIT CHECKS
            # =============================================
            if position != 0 and t >= acct_start:
                exit_signal = False
                cancel_signal = False
                div_exit_signal = False
                sl_exit_signal = False
                sl_emergency_signal = False
                exit_price = close_p

                # --- Trailing stop update ---
                if t > entry_bar:
                    if position == 1:
                        potential_stop = low_arr[t - 1] * (1.0 - ts_pct / 100.0)
                        if potential_stop > sl_level:
                            sl_level = potential_stop
                    elif position == -1:
                        potential_stop = high_arr[t - 1] * (1.0 + ts_pct / 100.0)
                        if sl_level == 0.0 or potential_stop < sl_level:
                            sl_level = potential_stop

                # --- Emergency SL ---
                if position == 1:
                    emerg_level = entry_price * (1.0 - sl_emergency_pct / 100.0)
                    if low_p <= emerg_level:
                        exit_signal = True
                        sl_exit_signal = True
                        sl_emergency_signal = True
                        exit_price = emerg_level
                elif position == -1:
                    emerg_level = entry_price * (1.0 + sl_emergency_pct / 100.0)
                    if high_p >= emerg_level:
                        exit_signal = True
                        sl_exit_signal = True
                        sl_emergency_signal = True
                        exit_price = emerg_level

                # --- Regular SL ---
                if not exit_signal and sl_level > 0.0:
                    if position == 1 and close_p < sl_level:
                        exit_signal = True
                        sl_exit_signal = True
                    elif position == -1 and close_p > sl_level:
                        exit_signal = True
                        sl_exit_signal = True

                # --- Div exit ---
                if not exit_signal and div_exit == 1 and div_type > 0:
                    if position == 1 and div_bear_now:
                        exit_signal = True
                        div_exit_signal = True
                    elif position == -1 and div_bull_now:
                        exit_signal = True
                        div_exit_signal = True

                # --- TF exit (exit_mask) ---
                if not exit_signal and exit_mask > 0:
                    exit_count_bull = 0
                    exit_count_active = 0
                    for bit in range(4):
                        if (exit_mask >> bit) & 1:
                            exit_count_active += 1
                            if (f_forming >> bit) & 1:
                                exit_count_bull += 1
                    if position == 1 and exit_count_active > 0 and exit_count_bull == 0:
                        exit_signal = True
                    elif position == -1 and exit_count_active > 0 and exit_count_bull == exit_count_active:
                        exit_signal = True

                # --- Zone exit (forming) ---
                if not exit_signal:
                    if position == 1 and z_bear:
                        exit_signal = True
                    elif position == -1 and z_bull:
                        exit_signal = True

                # =============================================
                # CANCEL CHECKS (only if no regular exit)
                # =============================================
                if not exit_signal:

                    # --- Cancel zona (bit 14) ---
                    # Anti-repainting: forming zone at entry vs best-available zone now
                    if cancel_zona_bit == 1 and not cancel_signal:
                        ts_entry_i = timestamps_i64[entry_bar]
                        ts_now_i = timestamps_i64[t]
                        entry_day = ts_entry_i // 86400000
                        current_day = ts_now_i // 86400000

                        if entry_day == current_day:
                            # Same day: check if forming zone still matches entry direction
                            if position == 1 and not zone_bull_forming[t]:
                                cancel_signal = True
                            elif position == -1 and not zone_bear_forming[t]:
                                cancel_signal = True
                        else:
                            # Day closed: check resolved zone at entry_bar
                            # If resolved disagrees with forming at entry -> entry was repainted
                            if position == 1 and not zone_bull_resolved[entry_bar]:
                                cancel_signal = True
                            elif position == -1 and not zone_bear_resolved[entry_bar]:
                                cancel_signal = True

                    # --- Cancel TF (bit 15) ---
                    # Forming vs resolved TF filter comparison
                    if cancel_tf_bit == 1 and not cancel_signal:
                        ts_entry_i = timestamps_i64[entry_bar]
                        ts_now_i = timestamps_i64[t]
                        entry_day_tf = ts_entry_i // 86400000
                        current_day_tf = ts_now_i // 86400000

                        eff = entry_filters_forming
                        f_now = filters_forming[t]
                        efr = filters_resolved[t]

                        # TF2 (bit 1): compare within 4h block
                        if (entry_mask >> 1) & 1:
                            entry_4h = (ts_entry_i // 3600000) // 4
                            now_4h = (ts_now_i // 3600000) // 4
                            if entry_4h == now_4h:
                                if ((eff >> 1) & 1) != ((f_now >> 1) & 1):
                                    cancel_signal = True
                            else:
                                if ((eff >> 1) & 1) != ((efr >> 1) & 1):
                                    cancel_signal = True

                        # TF3 (bit 2): compare within daily block
                        if not cancel_signal and (entry_mask >> 2) & 1:
                            if entry_day_tf == current_day_tf:
                                if ((eff >> 2) & 1) != ((f_now >> 2) & 1):
                                    cancel_signal = True
                            else:
                                if ((eff >> 2) & 1) != ((efr >> 2) & 1):
                                    cancel_signal = True

                    # --- Cancel ghost (bit 16) ---
                    # Ghost cross: zone invalidated and recovered during trajectory
                    if cancel_ghost_bit == 1 and not cancel_signal:
                        entry_was_bull = (position == 1)
                        current_day_g = timestamps_i64[t] // 86400000

                        for traj_bar in range(entry_bar + 1, t):
                            traj_day = timestamps_i64[traj_bar] // 86400000

                            if traj_day == current_day_g:
                                # Today: recalculate zone using current forming slow line
                                fl = fast_line_arr[traj_bar]
                                sf = slow_line_forming_arr[t]
                                if np.isnan(fl) or np.isnan(sf):
                                    continue
                                traj_zone_bull = fl < sf
                            else:
                                # Closed day: use precomputed resolved zone
                                traj_zone_bull = zone_bull_resolved[traj_bar]

                            if entry_was_bull and not traj_zone_bull:
                                cancel_signal = True
                                break
                            elif not entry_was_bull and traj_zone_bull:
                                cancel_signal = True
                                break

                # =============================================
                # PROCESS EXIT / CANCEL
                # =============================================
                if exit_signal or cancel_signal:
                    if position == 1:
                        trade_pnl = (exit_price - entry_price) / entry_price * 100.0
                    else:
                        trade_pnl = (entry_price - exit_price) / entry_price * 100.0

                    trade_pnl -= commission_pct

                    pnl += trade_pnl
                    trades += 1
                    if trade_pnl > 0:
                        wins += 1
                        gross_profit += trade_pnl
                    else:
                        gross_loss += abs(trade_pnl)
                    if cancel_signal:
                        cancels += 1

                    if pnl > peak_pnl:
                        peak_pnl = pnl
                    dd = peak_pnl - pnl
                    if dd > max_dd:
                        max_dd = dd

                    # Reset div_ctx for closed direction
                    if position == 1:
                        div_ctx_bull = False
                    else:
                        div_ctx_bear = False

                    # Cooldown uniforme (convención Pine canónica i_cooldown_bars).
                    # Las 4 ramas del switch original (emergency/sl/div/cancel) colapsaban
                    # matemáticamente a `t` con cooldown_bars=1 (valor productivo único).
                    # Unificado 2026-04-22 tras confirmación Opción A: cooldown=1 siempre operacional
                    # en Pine histórico, la diferenciación por tipo exit era código muerto.
                    # Ver §13.3 "Cooldown asimétrico" RESUELTO + §13.4 entrada 2026-04-22.
                    if sl_emergency_signal or sl_exit_signal or div_exit_signal or cancel_signal:
                        cooldown_until = t + cooldown_bars - 1

                    position = 0
                    entry_price = 0.0
                    sl_level = 0.0
                    entry_filters_forming = 0

            # Clear div_ctx on zone boundaries
            if z_bear:
                div_ctx_bull = False
            if z_bull:
                div_ctx_bear = False

            # =============================================
            # ENTRY CHECKS
            # =============================================
            if position == 0 and t >= acct_start:
                if t <= cooldown_until:
                    continue

                long_cond = False
                short_cond = False

                tf_entry_ok_bull = True
                tf_entry_ok_bear = True

                # TF entry checks (bits 0-2 for MR: TF1, TF2, TF3)
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

                # Effective div context (Pine-faithful: from PREVIOUS bar)
                effective_ctx_bull = entry_div_ctx_bull or prev_div_bull_now
                effective_ctx_bear = entry_div_ctx_bear or prev_div_bear_now

                if div_entry_mode == 0:
                    if z_bull:
                        if entry_tf_count > 0:
                            long_cond = tf_entry_ok_bull
                        else:
                            long_cond = True
                    if z_bear:
                        if entry_tf_count > 0:
                            short_cond = tf_entry_ok_bear
                        else:
                            short_cond = True

                elif div_entry_mode == 1:  # AND
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

                elif div_entry_mode == 2:  # OR
                    if z_bull:
                        if entry_tf_count > 0:
                            long_cond = tf_entry_ok_bull or prev_div_bull_now
                        else:
                            long_cond = True
                    if z_bear:
                        if entry_tf_count > 0:
                            short_cond = tf_entry_ok_bear or prev_div_bear_now
                        else:
                            short_cond = True

                # Prevent entering into immediate exit
                if long_cond and exit_mask > 0:
                    exit_count_bull = 0
                    for bit in range(4):
                        if (exit_mask >> bit) & 1 and (f_forming >> bit) & 1:
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
                    if exit_count_bull == exit_count_active:
                        short_cond = False

                # --- Open position ---
                if long_cond:
                    position = 1
                    entry_price = close_p
                    entry_bar = t
                    entry_filters_forming = f_forming
                    sl_level = low_p * (1.0 - sl_pct / 100.0)
                elif short_cond:
                    position = -1
                    entry_price = close_p
                    entry_bar = t
                    entry_filters_forming = f_forming
                    sl_level = high_p * (1.0 + sl_pct / 100.0)

        # --- Store results ---
        results[c, 0] = pnl
        results[c, 1] = trades
        results[c, 2] = wins
        results[c, 3] = cancels
        results[c, 4] = max_dd
        results[c, 5] = gross_profit
        results[c, 6] = gross_loss

    return results


# ============================================
# CONFIG GENERATION
# ============================================

def generate_mean_reversion_configs():
    """
    Genera todas las combinaciones validas de los 17 bits.

    Filtros:
      - div_type=0 -> div_entry_mode=0 y div_exit=0
      - div_entry_mode=0 y div_exit=0 -> div_type=0
      - entry/exit masks solo bits 0-2 (TF1-TF3, unicos TFs en MR)
    """
    configs = []

    for cancel_ghost in range(2):
        for cancel_tf in range(2):
            for cancel_zona in range(2):
                # --- Sin divergencias ---
                for entry_bits in range(8):   # bits 0-2
                    for exit_bits in range(8):
                        config_id = (
                            exit_bits
                            | (entry_bits << 4)
                            # div_entry_mode=0, div_exit=0, div_type=0
                            | (cancel_zona << 14)
                            | (cancel_tf << 15)
                            | (cancel_ghost << 16)
                        )
                        configs.append(config_id)

                # --- Con divergencias ---
                for div_type in range(1, 4):
                    for div_entry_mode in range(3):
                        for div_exit in range(2):
                            if div_entry_mode == 0 and div_exit == 0:
                                continue  # must use divs if div_type > 0
                            for entry_bits in range(8):
                                for exit_bits in range(8):
                                    config_id = (
                                        exit_bits
                                        | (entry_bits << 4)
                                        | (div_entry_mode << 9)
                                        | (div_exit << 11)
                                        | (div_type << 12)
                                        | (cancel_zona << 14)
                                        | (cancel_tf << 15)
                                        | (cancel_ghost << 16)
                                    )
                                    configs.append(config_id)

    return np.array(configs, dtype=np.uint32)


# ============================================
# CONFIG DECODE
# ============================================

def decode_mean_reversion_config(config_id):
    """Decodifica un config_id de 17 bits en un dict legible."""
    exit_mask       = config_id & 0xF
    entry_mask      = (config_id >> 4) & 0x1F
    div_entry_mode  = (config_id >> 9) & 0x3
    div_exit        = (config_id >> 11) & 0x1
    div_type        = (config_id >> 12) & 0x3
    cancel_zona     = (config_id >> 14) & 0x1
    cancel_tf       = (config_id >> 15) & 0x1
    cancel_ghost    = (config_id >> 16) & 0x1

    tf_names = ["TF1", "TF2", "TF3", "TF4", "TF5"]

    entry_tfs = [tf_names[b] for b in range(5) if (entry_mask >> b) & 1]
    exit_tfs = [tf_names[b] for b in range(4) if (exit_mask >> b) & 1]
    if not exit_tfs:
        exit_tfs = ["ZONA"]

    div_mode_str = ["OFF", "AND", "OR"][div_entry_mode]
    div_type_str = ["NONE", "REGULAR", "HIDDEN", "BOTH"][div_type]

    cancel_parts = []
    if cancel_zona:
        cancel_parts.append("ZONA")
    if cancel_tf:
        cancel_parts.append("TF")
    if cancel_ghost:
        cancel_parts.append("GHOST")
    cancel_str = "+".join(cancel_parts) if cancel_parts else "OFF"

    return {
        'exit_mask': exit_mask,
        'entry_mask': entry_mask,
        'entry_tfs': entry_tfs,
        'exit_tfs': exit_tfs,
        'div_entry_mode': div_mode_str,
        'div_exit': "ON" if div_exit else "OFF",
        'div_type': div_type_str,
        'cancel_zona': cancel_zona,
        'cancel_tf': cancel_tf,
        'cancel_ghost': cancel_ghost,
        'cancel_str': cancel_str,
        'n_entry_tfs': bin(entry_mask).count('1'),
    }


# ============================================
# RUN ON SLICE
# ============================================

def run_on_slice(configs, data, start_bar, end_bar,
                 sl_pct=SL_PERCENT, sl_emergency_pct=SL_EMERGENCY_PERCENT,
                 ts_pct=TS_PERCENT, cooldown_bars=COOLDOWN_BARS,
                 commission_pct=COMMISSION_ROUND_TRIP,
                 div_ind_mask=DEFAULT_DIV_IND_MASK, warmup=100):
    """
    Ejecuta simulacion sobre un slice de datos precalculados.

    warmup: barras antes de start_bar para construir estado (div_ctx, etc.)
    sin abrir trades ni acumular stats.
    """
    n_data = len(data['close'])
    actual_start = max(0, start_bar - warmup)
    accounting_start = start_bar - actual_start
    s, e = actual_start, end_bar

    ts_raw = data['timestamps'][s:e]
    ts_i64 = ts_raw.astype('datetime64[ms]').astype(np.int64)

    return run_mean_reversion_numba(
        configs,
        np.ascontiguousarray(data['close'][s:e]),
        np.ascontiguousarray(data['high'][s:e]),
        np.ascontiguousarray(data['low'][s:e]),
        ts_i64,
        np.ascontiguousarray(data['zone_bull_forming'][s:e]),
        np.ascontiguousarray(data['zone_bear_forming'][s:e]),
        np.ascontiguousarray(data['zone_bull_resolved'][s:e]),
        np.ascontiguousarray(data['zone_bear_resolved'][s:e]),
        np.ascontiguousarray(data['filters_forming'][s:e].astype(np.uint32)),
        np.ascontiguousarray(data['filters_resolved'][s:e].astype(np.uint32)),
        np.ascontiguousarray(data['fast_line'][s:e]),
        np.ascontiguousarray(data['slow_line_forming'][s:e]),
        np.ascontiguousarray(data['div_bits'][s:e]),
        div_ind_mask,
        sl_pct, sl_emergency_pct, ts_pct,
        cooldown_bars, commission_pct,
        accounting_start
    )


# ============================================
# CLI TEST
# ============================================

def main():
    parser = argparse.ArgumentParser(description='Mean-Reversion Kernel Test')
    parser.add_argument('--test', type=str, default='BTC/USDT',
                        help='Simbolo para test (default: BTC/USDT)')
    parser.add_argument('--div-ind-mask', type=int, default=DEFAULT_DIV_IND_MASK,
                        help='Mascara de indicadores de divergencia (default: 1 = RSI)')
    args = parser.parse_args()

    symbol = args.test
    sym = symbol.replace("/", "")

    # Load precalculated data
    npz_path = os.path.join(DATA_CACHE_DIR, f"{sym}_mean_reversion.npz")
    if not os.path.exists(npz_path):
        print(f"ERROR: No existe {npz_path}. Ejecutar mean_reversion_features.py primero.")
        sys.exit(1)

    print(f"=== Mean-Reversion Kernel Test: {symbol} ===")
    print(f"Cargando {npz_path}...")
    data = dict(np.load(npz_path, allow_pickle=True))

    n_bars = len(data['close'])
    print(f"Barras: {n_bars}")

    # Generate configs
    print("Generando configs...")
    configs = generate_mean_reversion_configs()
    print(f"Configs: {len(configs)}")

    # JIT warmup
    print("Compilando kernel (primera vez puede tardar ~30s)...")
    t0 = time.time()

    # Run simulation
    results = run_on_slice(
        configs, data,
        start_bar=100, end_bar=n_bars,
        div_ind_mask=args.div_ind_mask,
        warmup=100
    )
    elapsed = time.time() - t0
    print(f"Simulacion completada en {elapsed:.1f}s")

    # Extract results
    pnl_arr = results[:, 0]
    trades_arr = results[:, 1]
    wins_arr = results[:, 2]
    cancels_arr = results[:, 3]
    maxdd_arr = results[:, 4]
    gp_arr = results[:, 5]
    gl_arr = results[:, 6]

    # Filter configs with trades
    has_trades = trades_arr > 0
    n_with_trades = int(np.sum(has_trades))
    print(f"\nConfigs con trades: {n_with_trades}/{len(configs)}")

    if n_with_trades == 0:
        print("No hay configs con trades. Verificar datos.")
        return

    # Top 20 by PnL
    sort_idx = np.argsort(-pnl_arr)

    print(f"\n{'Rank':>4} {'PnL':>8} {'Trades':>6} {'WR%':>6} {'PF':>6} {'MaxDD':>7} "
          f"{'Cancel':>6} {'Entry':>12} {'Exit':>10} {'Div':>10} {'Cancel':>12}")
    print("-" * 105)

    for rank, idx in enumerate(sort_idx[:20]):
        p = pnl_arr[idx]
        tr = int(trades_arr[idx])
        w = int(wins_arr[idx])
        ca = int(cancels_arr[idx])
        md = maxdd_arr[idx]
        gp = gp_arr[idx]
        gl = gl_arr[idx]

        wr = 100.0 * w / tr if tr > 0 else 0.0
        pf = gp / gl if gl > 0 else (99.9 if gp > 0 else 0.0)

        d = decode_mean_reversion_config(int(configs[idx]))

        entry_str = "+".join(d['entry_tfs']) if d['entry_tfs'] else "-"
        exit_str = "+".join(d['exit_tfs'])
        div_str = f"{d['div_type']}/{d['div_entry_mode']}"
        if d['div_type'] == "NONE":
            div_str = "-"

        print(f"{rank+1:>4} {p:>8.1f} {tr:>6} {wr:>5.1f}% {pf:>5.1f}x {md:>6.1f}% "
              f"{ca:>6} {entry_str:>12} {exit_str:>10} {div_str:>10} {d['cancel_str']:>12}")

    # Summary stats
    print(f"\n--- Resumen ---")
    print(f"Mejor PnL: {pnl_arr[sort_idx[0]]:.1f}%")
    print(f"PnL mediana (con trades): {np.median(pnl_arr[has_trades]):.1f}%")
    print(f"Configs rentables: {int(np.sum(pnl_arr > 0))}/{n_with_trades}")

    # Cancel impact analysis
    no_cancel = np.array([
        (configs[i] >> 14) & 0x7 == 0
        for i in range(len(configs))
    ])
    has_cancel = ~no_cancel
    if np.sum(has_trades & no_cancel) > 0 and np.sum(has_trades & has_cancel) > 0:
        avg_pnl_no_cancel = np.mean(pnl_arr[has_trades & no_cancel])
        avg_pnl_with_cancel = np.mean(pnl_arr[has_trades & has_cancel])
        print(f"\nPnL medio sin cancels: {avg_pnl_no_cancel:.1f}%")
        print(f"PnL medio con cancels: {avg_pnl_with_cancel:.1f}%")
        print(f"Mejora por cancels: {avg_pnl_with_cancel - avg_pnl_no_cancel:+.1f}%")


if __name__ == '__main__':
    main()
