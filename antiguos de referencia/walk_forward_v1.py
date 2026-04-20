#!/usr/bin/env python3
"""
walk_forward_v1.py — Walk-Forward Simulado para validar metricas predictivas.

Evalua configs candidatas en ventanas deslizantes de optimizacion + forward,
usando el mismo motor de simulacion del lab/validador.

Para cada posicion de ventana:
  - Corre configs en sub-ventana de 5k y 7k (como el validador)
  - Corre configs en ventana forward posterior (+ mitades h1/h2)
  - Registra metricas de ambas para cruzar y buscar correlaciones

Seleccion de candidatas:
  Grupo A: TODAS las configs con pasa_7k == True (del pivot del validador)
  Grupo B: configs frontera (pf_7k entre 1.5 y 2.0), hasta len(A) configs

Uso:
    python walk_forward_v1.py BNB/USDT output/test_bnb/BNBUSDT
    python walk_forward_v1.py BNB/USDT output/test_bnb/BNBUSDT --fwd-size 500 --step 500
    python walk_forward_v1.py BNB/USDT output/test_bnb/BNBUSDT --total-candles 16700

Requisitos:
    - lab_historico_numba_v8_3.py en el mismo directorio
    - validacion_gemas_SYMBOL_pivot.csv del validador (preferido)
    - gemas_SYMBOL.csv del extractor (fallback)
    - Datos en cache (data_cache/) o acceso a Binance

Genera:
    walkforward_SYMBOL.csv        — 1 fila por config x ventana (metricas opt + fwd + mitades)
    walkforward_SYMBOL_corr.txt   — Analisis de correlaciones y veredictos
"""

import os
import sys
import time
import argparse
import importlib.util

import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# 0. IMPORTAR LAB
# -------------------------------------------------------------------

def import_lab(lab_filename="lab_historico_numba_v8_3.py"):
    lab_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), lab_filename)
    if not os.path.exists(lab_path):
        print(f"Error: no se encuentra {lab_path}")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("lab", lab_path)
    lab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab)
    return lab


# -------------------------------------------------------------------
# 1. CONFIGURACION
# -------------------------------------------------------------------

OPT_5K = 5000        # Sub-ventana de optimizacion (como validador 5k)
OPT_7K = 7000        # Ventana de optimizacion completa (como validador 7k)
FWD_SIZE = 1000      # Ventana forward (1000 bars = ~42 dias)
STEP = 1000          # Paso entre posiciones (= FWD_SIZE para no solapar forward)
WARMUP = 500         # Bars extra para warmup de MAs
TOTAL_CANDLES = 16700  # Velas disponibles en cache


# -------------------------------------------------------------------
# 2. CARGAR CANDIDATAS DESDE PIVOT DEL VALIDADOR
# -------------------------------------------------------------------

def load_gems_and_metrics(sym_dir, sc):
    """Carga candidatas desde pivot del validador. Retorna (gems_df, pivot_df, wf_groups).

    Grupo A (obligatorio): TODAS las configs con pasa_7k == True.
    Grupo B (control): configs frontera (pf_7k entre 1.5 y 2.0), hasta len(A).
    Fallback: si el pivot no existe, usa gemas_SYMBOL.csv con warning.
    """
    pivot_csv = os.path.join(sym_dir, f"validacion_gemas_{sc}_pivot.csv")
    gems_csv = os.path.join(sym_dir, f"gemas_{sc}.csv")

    pivot = None
    wf_groups = {}  # config_id -> "A" o "B"

    if os.path.exists(pivot_csv):
        pivot = pd.read_csv(pivot_csv)
        print(f"  Pivot validador: {len(pivot)} configs de {pivot_csv}")

        # Grupo A: todas las que pasan 7k
        if 'pasa_7k' in pivot.columns:
            group_a = pivot[pivot['pasa_7k'] == True].copy()
        else:
            group_a = pd.DataFrame()

        # Grupo B: frontera (pf_7k entre 1.5 y 2.0, NO pasan 7k)
        if 'pf_7k' in pivot.columns and len(group_a) > 0:
            not_pass = pivot[~pivot['config_id'].isin(group_a['config_id'])]
            frontier = not_pass[(not_pass['pf_7k'] >= 1.5) & (not_pass['pf_7k'] < 2.0)].copy()
            frontier = frontier.sort_values('pf_7k', ascending=False).head(len(group_a))
        else:
            frontier = pd.DataFrame()

        # Asignar grupos
        for cid in group_a['config_id']:
            wf_groups[int(cid)] = 'A'
        for cid in frontier['config_id']:
            wf_groups[int(cid)] = 'B'

        # Combinar
        gems = pd.concat([group_a, frontier], ignore_index=True)
        gems = gems.drop_duplicates(subset='config_id')

        print(f"  Grupo A (pasa_7k): {len(group_a)} configs")
        print(f"  Grupo B (frontera): {len(frontier)} configs")
        print(f"  Total candidatas: {len(gems)}")

        if len(gems) == 0:
            print(f"  AVISO: sin configs que pasen 7k ni frontera en el pivot")
            # Fallback a gemas
            if os.path.exists(gems_csv):
                print(f"  Fallback a {gems_csv}")
                gems = pd.read_csv(gems_csv).drop_duplicates(subset='config_id').head(20)
                for cid in gems['config_id']:
                    wf_groups[int(cid)] = 'A'
            else:
                return pd.DataFrame(), pivot, {}

    elif os.path.exists(gems_csv):
        # Fallback: sin pivot, usar gemas con warning
        print(f"  AVISO: sin pivot del validador ({pivot_csv}), usando {gems_csv} como fallback")
        gems = pd.read_csv(gems_csv).drop_duplicates(subset='config_id').head(20)
        for cid in gems['config_id']:
            wf_groups[int(cid)] = 'A'
        print(f"  Configs cargadas (fallback): {len(gems)}")
    else:
        print(f"Error: no se encuentra ni {pivot_csv} ni {gems_csv}")
        sys.exit(1)

    return gems, pivot, wf_groups


def group_gems_by_preset(gems, symbol, lab):
    """Agrupa gemas por (preset_key, hyst) — reutiliza logica del validador."""
    registry = lab.SYMBOL_ZONE_PRESETS.get(symbol, [])
    if not registry:
        print(f"Error: sin presets para {symbol} en el lab")
        sys.exit(1)

    preset_map = {}
    for preset in registry:
        ft, fl = preset[0], preset[1]
        st, sl = preset[4], preset[5]
        key = f"{ft}({fl})/{st}({sl})"
        preset_map[key] = preset

    groups = {}
    missing = set()

    for _, gem in gems.iterrows():
        ma_info = gem['ma_info']
        parts = ma_info.rsplit(' ', 1)
        preset_key = parts[0].strip()
        hyst = 0.5 if 'H05' in ma_info else 0.0

        if preset_key not in preset_map:
            missing.add(preset_key)
            continue

        group_key = (preset_key, hyst)
        if group_key not in groups:
            groups[group_key] = {
                'preset': preset_map[preset_key],
                'hyst': hyst,
                'configs': []
            }
        groups[group_key]['configs'].append({
            'config_id': int(gem['config_id']),
            'familia': gem.get('familia', '?'),
            'ma_info': ma_info,
        })

    if missing:
        print(f"  AVISO: presets no encontrados: {missing}")

    return groups


# -------------------------------------------------------------------
# 3. EJECUCION WALK-FORWARD
# -------------------------------------------------------------------

def run_walk_forward(symbol, sym_dir, lab, opt_7k, opt_5k, fwd_size, step, total_candles):
    """Ejecuta walk-forward simulado. Retorna (results_df, timestamps_series)."""
    sc = symbol.replace('/', '')

    # Cargar candidatas desde pivot
    gems, pivot, wf_groups = load_gems_and_metrics(sym_dir, sc)
    if len(gems) == 0:
        print("  Sin configs para evaluar")
        return pd.DataFrame(), None

    # Cargar presets en el lab
    presets_csv = os.path.join(sym_dir, f"presets_{sc}.csv")
    if os.path.exists(presets_csv):
        from pipeline import load_presets_from_csv
        presets, cluster_ids = load_presets_from_csv(presets_csv)
        lab.SYMBOL_ZONE_PRESETS[symbol] = presets
        lab.PRESET_CLUSTER_IDS[symbol] = cluster_ids
    elif symbol not in lab.SYMBOL_ZONE_PRESETS:
        print(f"Error: sin presets para {symbol}")
        sys.exit(1)

    groups = group_gems_by_preset(gems, symbol, lab)
    print(f"  Grupos preset: {len(groups)}")

    # Descargar datos
    print(f"\n  Descargando {total_candles} candles...")
    t0 = time.time()
    df = lab.fetch_all_candles(symbol, "1h", total_candles)
    if df is None or len(df) < total_candles * 0.9:
        print(f"  Error: datos insuficientes ({len(df) if df is not None else 0})")
        return pd.DataFrame(), None
    print(f"  Datos: {len(df)} candles ({time.time()-t0:.1f}s)")

    # Extraer timestamps para contexto temporal (Mejora 5)
    timestamps = df['timestamp'] if 'timestamp' in df.columns else None

    # Calcular posiciones de ventana
    min_bars_needed = WARMUP + opt_7k + fwd_size
    n_positions = max(1, (len(df) - min_bars_needed) // step + 1)
    print(f"\n  Walk-Forward: opt_7k={opt_7k}, opt_5k={opt_5k}, fwd={fwd_size}, step={step}")
    print(f"  Posiciones: {n_positions} (datos={len(df)}, min_necesario={min_bars_needed})")

    all_results = []
    t_global = time.time()

    # Preparar metricas del validador para lookup rapido
    val_metrics = {}
    if pivot is not None:
        val_cols = ['pf_5k', 'pf_7k', 'maxdd_5k', 'maxdd_7k', 'trades_5k', 'trades_7k',
                    'pnl_5k', 'pnl_7k', 'delta_pf_57', 'delta_dd_57',
                    'seg_consistency', 'seg_avg_pnl', 'seg_min_pnl', 'pasa_7k',
                    'score_5k', 'score_7k']
        available_cols = [c for c in val_cols if c in pivot.columns]
        for _, r in pivot.iterrows():
            val_metrics[int(r['config_id'])] = {c: r[c] for c in available_cols}

    for g_idx, (group_key, group) in enumerate(groups.items()):
        preset = group['preset']
        hyst = group['hyst']
        config_list = group['configs']
        preset_label = f"{group_key[0]} H{hyst:.1f}"

        print(f"\n  {'='*60}")
        print(f"  Grupo {g_idx+1}/{len(groups)}: {preset_label} ({len(config_list)} configs)")

        # Precalcular indicadores UNA VEZ sobre TODOS los datos
        print(f"  Precalculando indicadores...")
        t0 = time.time()
        data = lab.precalculate_all_data(df, preset=preset, hyst_mult=hyst, symbol=symbol)
        n_bars = len(data['close'])
        print(f"  Precalculo: {time.time()-t0:.1f}s ({n_bars} bars)")

        config_ids = np.array([c['config_id'] for c in config_list], dtype=np.uint32)
        config_meta = {c['config_id']: c for c in config_list}

        # Iterar posiciones de ventana
        for pos_idx in range(n_positions):
            # Posiciones absolutas en el array de datos
            # Empezamos desde el final hacia atras para que pos_0 sea la mas reciente
            fwd_end = n_bars - pos_idx * step
            fwd_start = fwd_end - fwd_size
            opt_7k_start = fwd_start - opt_7k
            opt_5k_start = fwd_start - opt_5k

            if opt_7k_start < 0:
                break

            # --- Ejecutar simulacion en 5 slices ---
            t0 = time.time()

            # 1. Opt 7k
            res_7k = lab.run_on_slice(
                config_ids, data, opt_7k_start, fwd_start,
                lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
                lab.TS_PERCENT, lab.COOLDOWN_BARS,
                lab.COMMISSION_ROUND_TRIP
            )

            # 2. Opt 5k (sub-ventana de la 7k)
            res_5k = lab.run_on_slice(
                config_ids, data, opt_5k_start, fwd_start,
                lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
                lab.TS_PERCENT, lab.COOLDOWN_BARS,
                lab.COMMISSION_ROUND_TRIP
            )

            # 3. Forward completo
            res_fwd = lab.run_on_slice(
                config_ids, data, fwd_start, fwd_end,
                lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
                lab.TS_PERCENT, lab.COOLDOWN_BARS,
                lab.COMMISSION_ROUND_TRIP
            )

            # 4. Forward H1 (primera mitad) — Mejora 2
            fwd_mid = fwd_start + fwd_size // 2
            res_fwd_h1 = lab.run_on_slice(
                config_ids, data, fwd_start, fwd_mid,
                lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
                lab.TS_PERCENT, lab.COOLDOWN_BARS,
                lab.COMMISSION_ROUND_TRIP
            )

            # 5. Forward H2 (segunda mitad) — Mejora 2
            res_fwd_h2 = lab.run_on_slice(
                config_ids, data, fwd_mid, fwd_end,
                lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
                lab.TS_PERCENT, lab.COOLDOWN_BARS,
                lab.COMMISSION_ROUND_TRIP
            )

            t_sim = time.time() - t0

            # --- Calcular metricas derivadas ---
            # res shape: (n_configs, 7) = [pnl, trades, wins, cancels, maxdd, gp, gl]
            def extract_metrics(res, n_bars_slice, prefix):
                pnl = res[:, 0]
                trades = res[:, 1]
                wins = res[:, 2]
                cancels = res[:, 3]
                maxdd = res[:, 4]
                gp = res[:, 5]
                gl = res[:, 6]

                _, pnl_ann, _, pf, _, _ = lab.calc_score_v63(
                    pnl, maxdd, gp, gl, trades, cancels, n_bars_slice)

                wr = np.where(trades > 0, wins / trades * 100, 0.0)

                return {
                    f'{prefix}_pnl': pnl,
                    f'{prefix}_trades': trades,
                    f'{prefix}_maxdd': maxdd,
                    f'{prefix}_pf': pf,
                    f'{prefix}_wr': wr,
                    f'{prefix}_pnl_ann': pnl_ann,
                    f'{prefix}_gp': gp,
                    f'{prefix}_gl': gl,
                }

            m_7k = extract_metrics(res_7k, opt_7k, 'opt7k')
            m_5k = extract_metrics(res_5k, opt_5k, 'opt5k')
            m_fwd = extract_metrics(res_fwd, fwd_size, 'fwd')

            # Metricas de mitades (Mejora 2) — solo pnl, pf, trades
            h1_pnl = res_fwd_h1[:, 0]
            h1_trades = res_fwd_h1[:, 1]
            h1_gp = res_fwd_h1[:, 5]
            h1_gl = res_fwd_h1[:, 6]
            h1_maxdd = res_fwd_h1[:, 4]
            h1_cancels = res_fwd_h1[:, 3]
            _, _, _, h1_pf, _, _ = lab.calc_score_v63(
                h1_pnl, h1_maxdd, h1_gp, h1_gl, h1_trades, h1_cancels, fwd_size // 2)

            h2_pnl = res_fwd_h2[:, 0]
            h2_trades = res_fwd_h2[:, 1]
            h2_gp = res_fwd_h2[:, 5]
            h2_gl = res_fwd_h2[:, 6]
            h2_maxdd = res_fwd_h2[:, 4]
            h2_cancels = res_fwd_h2[:, 3]
            _, _, _, h2_pf, _, _ = lab.calc_score_v63(
                h2_pnl, h2_maxdd, h2_gp, h2_gl, h2_trades, h2_cancels, fwd_size - fwd_size // 2)

            # h2_ratio: proporcion del PnL total que viene de H2
            denom = np.abs(h1_pnl) + np.abs(h2_pnl)
            h2_ratio = np.where(denom > 0, h2_pnl / denom, 0.5)

            # Delta PF 5k -> 7k (la metrica clave a validar)
            delta_pf = m_7k['opt7k_pf'] - m_5k['opt5k_pf']
            delta_dd = m_7k['opt7k_maxdd'] - m_5k['opt5k_maxdd']

            # Fechas reales (Mejora 5)
            fwd_date_start_str = ""
            fwd_date_end_str = ""
            if timestamps is not None:
                try:
                    fwd_date_start_str = str(timestamps.iloc[fwd_start])[:10]
                    fwd_date_end_str = str(timestamps.iloc[min(fwd_end - 1, len(timestamps) - 1)])[:10]
                except (IndexError, KeyError):
                    pass

            # Guardar resultados
            for i, cfg in enumerate(config_list):
                cid = cfg['config_id']

                row = {
                    'config_id': cid,
                    'familia': cfg['familia'],
                    'ma_info': cfg['ma_info'],
                    'wf_group': wf_groups.get(cid, 'A'),
                    'pos_idx': pos_idx,
                    'opt7k_start': int(opt_7k_start),
                    'opt7k_end': int(fwd_start),
                    'opt5k_start': int(opt_5k_start),
                    'fwd_start': int(fwd_start),
                    'fwd_end': int(fwd_end),
                    'fwd_n_bars': fwd_size,
                    'fwd_date_start': fwd_date_start_str,
                    'fwd_date_end': fwd_date_end_str,
                }

                # Metricas de optimizacion
                for key in m_5k:
                    row[key] = float(m_5k[key][i])
                for key in m_7k:
                    row[key] = float(m_7k[key][i])

                # Delta (senal predictiva a evaluar)
                row['delta_pf_57'] = float(delta_pf[i])
                row['delta_dd_57'] = float(delta_dd[i])

                # Pasa 7k (criterio del validador)
                pf_7k_val = float(m_7k['opt7k_pf'][i])
                dd_7k_val = float(m_7k['opt7k_maxdd'][i])
                row['pasa_7k'] = bool(pf_7k_val >= 2.0 and dd_7k_val <= 10.0)

                # Metricas forward completo
                for key in m_fwd:
                    row[key] = float(m_fwd[key][i])

                # Metricas forward mitades (Mejora 2)
                row['fwd_h1_pnl'] = float(h1_pnl[i])
                row['fwd_h1_pf'] = float(h1_pf[i])
                row['fwd_h1_trades'] = int(h1_trades[i])
                row['fwd_h2_pnl'] = float(h2_pnl[i])
                row['fwd_h2_pf'] = float(h2_pf[i])
                row['fwd_h2_trades'] = int(h2_trades[i])
                row['fwd_h2_ratio'] = float(h2_ratio[i])

                # Flag de concentracion de riesgo (Mejora 4)
                fwd_trades_i = float(m_fwd['fwd_trades'][i])
                fwd_pnl_i = float(m_fwd['fwd_pnl'][i])
                fwd_gp_i = float(m_fwd['fwd_gp'][i])
                concentrated = False
                if fwd_trades_i <= 5 and fwd_pnl_i > 0 and fwd_gp_i > 0:
                    if fwd_pnl_i / fwd_gp_i > 0.5:
                        concentrated = True
                row['fwd_concentrated'] = concentrated

                # Metricas originales del validador (fijas por config)
                if cid in val_metrics:
                    for vk, vv in val_metrics[cid].items():
                        row[f'val_{vk}'] = vv

                all_results.append(row)

            # Resumen rapido con fechas reales (Mejora 5)
            avg_fwd_pnl = np.mean(m_fwd['fwd_pnl'])
            avg_opt_pf = np.mean(m_7k['opt7k_pf'])
            n_pf_up = np.sum(delta_pf > 0)
            date_info = f" [{fwd_date_start_str} -> {fwd_date_end_str}]" if fwd_date_start_str else ""
            print(f"    pos{pos_idx}: fwd[{fwd_start}:{fwd_end}]{date_info}  "
                  f"avgOptPF:{avg_opt_pf:.2f}  dPF+:{n_pf_up}/{len(config_ids)}  "
                  f"avgFwdPnL:{avg_fwd_pnl:+.2f}%  ({t_sim:.2f}s)")

    elapsed = time.time() - t_global
    print(f"\n  Total: {elapsed:.1f}s")

    return pd.DataFrame(all_results), timestamps


# -------------------------------------------------------------------
# 4. ANALISIS DE CORRELACIONES
# -------------------------------------------------------------------

def analyze_correlations(results_df, symbol, output_dir, timestamps=None):
    """Analiza correlaciones entre metricas de optimizacion y rendimiento forward."""
    sc = symbol.replace('/', '')
    L = []

    # Filtrar observaciones sin actividad forward (0 trades = metricas sin sentido)
    MIN_FWD_TRADES = 3
    n_total = len(results_df)
    results_df = results_df[results_df['fwd_trades'] >= MIN_FWD_TRADES].copy()
    n_filtered = n_total - len(results_df)

    # Cabecera con periodo total (Mejora 5)
    L.append(f"{'='*100}")
    L.append(f"WALK-FORWARD SIMULADO — {symbol}")
    L.append(f"{'='*100}")

    if timestamps is not None and len(timestamps) > 0:
        try:
            date_first = str(timestamps.iloc[0])[:10]
            date_last = str(timestamps.iloc[-1])[:10]
            L.append(f"Periodo datos: {date_first} a {date_last} ({len(timestamps)} bars)")
        except (IndexError, KeyError):
            pass

    L.append(f"Configs: {results_df['config_id'].nunique()}")
    L.append(f"Ventanas: {results_df['pos_idx'].nunique()}")
    L.append(f"Observaciones: {len(results_df)} (filtradas {n_filtered} con fwd_trades < {MIN_FWD_TRADES})")

    # Mostrar distribucion A/B si existe
    if 'wf_group' in results_df.columns:
        n_a = (results_df['wf_group'] == 'A').sum()
        n_b = (results_df['wf_group'] == 'B').sum()
        L.append(f"Grupo A (pasa_7k): {n_a} obs | Grupo B (frontera): {n_b} obs")
    L.append("")

    if len(results_df) < 10:
        L.append("AVISO: Muy pocas observaciones con trades forward suficientes.")
        L.append("Los resultados de correlacion no son fiables.")
        L.append(f"{'='*100}")
        return '\n'.join(L)

    # --- Correlaciones clave ---
    L.append(f"{'~'*100}")
    L.append(f"CORRELACIONES: Metricas de optimizacion vs Forward PnL")
    L.append(f"{'~'*100}")

    predictors = [
        ('delta_pf_57', 'Delta PF 5k->7k'),
        ('opt7k_pf', 'PF 7k (opt)'),
        ('opt5k_pf', 'PF 5k (opt)'),
        ('opt7k_maxdd', 'MaxDD 7k (opt)'),
        ('opt7k_pnl', 'PnL 7k (opt)'),
        ('opt5k_pnl', 'PnL 5k (opt)'),
        ('opt7k_trades', 'Trades 7k (opt)'),
        ('pasa_7k', 'Pasa criterio 7k'),
        ('delta_dd_57', 'Delta DD 5k->7k'),
    ]

    # Targets ampliados con mitades (Mejora 3)
    targets = [
        ('fwd_pnl', 'Forward PnL'),
        ('fwd_pf', 'Forward PF'),
        ('fwd_maxdd', 'Forward MaxDD'),
        ('fwd_h1_pnl', 'Fwd H1 PnL'),
        ('fwd_h2_pnl', 'Fwd H2 PnL'),
        ('fwd_h2_ratio', 'Fwd H2 Ratio'),
    ]

    # Tabla de correlaciones
    header_labels = [lbl for _, lbl in targets]
    L.append(f"\n  {'Predictor':<25s} | " + " | ".join(f"{lbl:>12s}" for lbl in header_labels))
    L.append(f"  {'-'*25}-+-" + "-+-".join(f"{'-'*12}" for _ in targets))

    for pred_col, pred_label in predictors:
        if pred_col not in results_df.columns:
            continue
        corrs = []
        for tgt_col, _ in targets:
            if tgt_col not in results_df.columns:
                corrs.append("      --")
                continue
            valid = results_df[[pred_col, tgt_col]].dropna()
            if len(valid) < 5:
                corrs.append("      --")
                continue
            c = valid[pred_col].corr(valid[tgt_col])
            star = " **" if abs(c) > 0.3 else " *" if abs(c) > 0.15 else ""
            corrs.append(f"{c:>+9.3f}{star}")
        L.append(f"  {pred_label:<25s} | " + " | ".join(f"{c:>12s}" for c in corrs))

    L.append(f"\n  (* = correlacion moderada |r|>0.15,  ** = correlacion fuerte |r|>0.30)")

    # --- Metricas del validador original vs forward ---
    val_predictors = [
        ('val_delta_pf_57', 'Val: Delta PF 5k->7k'),
        ('val_pf_7k', 'Val: PF 7k'),
        ('val_pf_5k', 'Val: PF 5k'),
        ('val_maxdd_7k', 'Val: MaxDD 7k'),
        ('val_seg_consistency', 'Val: Consistencia seg'),
        ('val_seg_min_pnl', 'Val: Min PnL seg'),
        ('val_pasa_7k', 'Val: Pasa 7k'),
    ]

    has_val = any(c in results_df.columns for c, _ in val_predictors)
    if has_val:
        L.append(f"\n  {'Metrica Validador':<25s} | " + " | ".join(f"{lbl:>12s}" for lbl in header_labels))
        L.append(f"  {'-'*25}-+-" + "-+-".join(f"{'-'*12}" for _ in targets))

        for pred_col, pred_label in val_predictors:
            if pred_col not in results_df.columns:
                continue
            corrs = []
            for tgt_col, _ in targets:
                if tgt_col not in results_df.columns:
                    corrs.append("      --")
                    continue
                valid = results_df[[pred_col, tgt_col]].dropna()
                if len(valid) < 5:
                    corrs.append("      --")
                    continue
                c = valid[pred_col].corr(valid[tgt_col])
                star = " **" if abs(c) > 0.3 else " *" if abs(c) > 0.15 else ""
                corrs.append(f"{c:>+9.3f}{star}")
            L.append(f"  {pred_label:<25s} | " + " | ".join(f"{c:>12s}" for c in corrs))

    # --- Correlacion especial: val_seg_consistency vs fwd_h2_ratio (Mejora 3) ---
    if 'val_seg_consistency' in results_df.columns and 'fwd_h2_ratio' in results_df.columns:
        valid = results_df[['val_seg_consistency', 'fwd_h2_ratio']].dropna()
        if len(valid) >= 5:
            c = valid['val_seg_consistency'].corr(valid['fwd_h2_ratio'])
            L.append(f"\n  Hipotesis clave: val_seg_consistency vs fwd_h2_ratio: r = {c:+.3f}")
            if abs(c) > 0.15:
                L.append(f"    -> Consistencia de segmentos {'SI' if c > 0 else 'NO'} correlaciona con distribucion equilibrada del forward")
            else:
                L.append(f"    -> Sin correlacion significativa entre consistencia y distribucion forward")

    # --- Analisis de distribucion forward (Mejora 3) ---
    if 'wf_group' in results_df.columns and 'fwd_h1_pnl' in results_df.columns:
        L.append(f"\n{'~'*100}")
        L.append(f"ANALISIS DE DISTRIBUCION FORWARD (H1/H2 por Grupo A vs B)")
        L.append(f"{'~'*100}")

        L.append(f"\n  {'Grupo':<20s} | {'N':>5s} | {'Avg H1 PnL':>11s} | {'Avg H2 PnL':>11s} | {'Avg H2 Ratio':>13s} | {'Avg Fwd PnL':>12s}")
        L.append(f"  {'-'*20}-+-{'-'*5}-+-{'-'*11}-+-{'-'*11}-+-{'-'*13}-+-{'-'*12}")

        for grp_label, grp_val in [('A (pasa_7k)', 'A'), ('B (frontera)', 'B')]:
            subset = results_df[results_df['wf_group'] == grp_val]
            if len(subset) == 0:
                continue
            avg_h1 = subset['fwd_h1_pnl'].mean()
            avg_h2 = subset['fwd_h2_pnl'].mean()
            avg_ratio = subset['fwd_h2_ratio'].mean()
            avg_total = subset['fwd_pnl'].mean()
            L.append(f"  {grp_label:<20s} | {len(subset):>5d} | {avg_h1:>+10.2f}% | {avg_h2:>+10.2f}% | {avg_ratio:>12.3f} | {avg_total:>+11.2f}%")

        # Interpretacion
        grp_a = results_df[results_df['wf_group'] == 'A']
        grp_b = results_df[results_df['wf_group'] == 'B']
        if len(grp_a) > 0 and len(grp_b) > 0:
            ratio_a = grp_a['fwd_h2_ratio'].mean()
            ratio_b = grp_b['fwd_h2_ratio'].mean()
            if abs(ratio_a - 0.5) < abs(ratio_b - 0.5):
                L.append(f"\n  -> Grupo A tiene forward mas equilibrado (ratio {ratio_a:.3f} vs {ratio_b:.3f})")
            else:
                L.append(f"\n  -> Grupo B tiene forward mas equilibrado (ratio {ratio_b:.3f} vs {ratio_a:.3f})")

    # --- Analisis por grupo: delta_pf positivo vs negativo ---
    L.append(f"\n{'~'*100}")
    L.append(f"ANALISIS GRUPAL: Delta PF ascendente vs descendente")
    L.append(f"{'~'*100}")

    if 'delta_pf_57' in results_df.columns:
        up = results_df[results_df['delta_pf_57'] > 0]
        down = results_df[results_df['delta_pf_57'] <= 0]

        L.append(f"\n  {'Grupo':<20s} | {'N':>5s} | {'Avg Fwd PnL':>12s} | {'Avg Fwd PF':>11s} | {'Avg Fwd DD':>11s} | {'%Fwd>0':>7s}")
        L.append(f"  {'-'*20}-+-{'-'*5}-+-{'-'*12}-+-{'-'*11}-+-{'-'*11}-+-{'-'*7}")

        for label, subset in [('dPF > 0 (ascend)', up), ('dPF <= 0 (descend)', down)]:
            if len(subset) == 0:
                continue
            avg_pnl = subset['fwd_pnl'].mean()
            avg_pf = subset['fwd_pf'].mean()
            avg_dd = subset['fwd_maxdd'].mean()
            pct_pos = (subset['fwd_pnl'] > 0).mean() * 100
            L.append(f"  {label:<20s} | {len(subset):>5d} | {avg_pnl:>+11.2f}% | {avg_pf:>10.2f} | {avg_dd:>10.2f}% | {pct_pos:>6.1f}%")

    # --- Analisis por grupo: pasa_7k si/no ---
    if 'pasa_7k' in results_df.columns:
        L.append(f"\n  {'Pasa 7k?':<20s} | {'N':>5s} | {'Avg Fwd PnL':>12s} | {'Avg Fwd PF':>11s} | {'Avg Fwd DD':>11s} | {'%Fwd>0':>7s}")
        L.append(f"  {'-'*20}-+-{'-'*5}-+-{'-'*12}-+-{'-'*11}-+-{'-'*11}-+-{'-'*7}")

        for label, subset in [('SI pasa 7k', results_df[results_df['pasa_7k'] == True]),
                              ('NO pasa 7k', results_df[results_df['pasa_7k'] == False])]:
            if len(subset) == 0:
                continue
            avg_pnl = subset['fwd_pnl'].mean()
            avg_pf = subset['fwd_pf'].mean()
            avg_dd = subset['fwd_maxdd'].mean()
            pct_pos = (subset['fwd_pnl'] > 0).mean() * 100
            L.append(f"  {label:<20s} | {len(subset):>5d} | {avg_pnl:>+11.2f}% | {avg_pf:>10.2f} | {avg_dd:>10.2f}% | {pct_pos:>6.1f}%")

    # --- Top configs por rendimiento forward promedio ---
    L.append(f"\n{'~'*100}")
    L.append(f"TOP CONFIGS POR RENDIMIENTO FORWARD PROMEDIO")
    L.append(f"{'~'*100}")

    agg_dict = {
        'familia': ('familia', 'first'),
        'ma_info': ('ma_info', 'first'),
        'n_windows': ('fwd_pnl', 'count'),
        'avg_fwd_pnl': ('fwd_pnl', 'mean'),
        'std_fwd_pnl': ('fwd_pnl', 'std'),
        'avg_fwd_pf': ('fwd_pf', 'mean'),
        'avg_fwd_dd': ('fwd_maxdd', 'mean'),
        'avg_fwd_trades': ('fwd_trades', 'mean'),
        'pct_fwd_pos': ('fwd_pnl', lambda x: (x > 0).mean() * 100),
        'avg_delta_pf': ('delta_pf_57', 'mean'),
        'avg_opt7k_pf': ('opt7k_pf', 'mean'),
    }
    if 'wf_group' in results_df.columns:
        agg_dict['wf_group'] = ('wf_group', 'first')

    cfg_summary = results_df.groupby('config_id').agg(**agg_dict).sort_values('avg_fwd_pnl', ascending=False)

    L.append(f"\n  {'Cfg':<12s} {'Fam':>4s} {'Grp':>3s} {'MA Info':<22s} {'AvgFwdPnL':>10s} {'StdPnL':>7s} "
             f"{'AvgFwdPF':>9s} {'AvgFwdDD':>9s} {'%Pos':>5s} {'AvgdPF':>7s} {'AvgOpt7kPF':>11s}")
    L.append(f"  {'-'*12} {'-'*4} {'-'*3} {'-'*22} {'-'*10} {'-'*7} {'-'*9} {'-'*9} {'-'*5} {'-'*7} {'-'*11}")

    for cid, r in cfg_summary.iterrows():
        grp = r.get('wf_group', '?') if 'wf_group' in cfg_summary.columns else '?'
        L.append(f"  {int(cid):<12d} {r['familia']:>4s} {grp:>3s} {r['ma_info']:<22s} "
                 f"{r['avg_fwd_pnl']:>+9.2f}% {r['std_fwd_pnl']:>6.2f} "
                 f"{r['avg_fwd_pf']:>8.2f} {r['avg_fwd_dd']:>8.2f}% "
                 f"{r['pct_fwd_pos']:>4.0f}% {r['avg_delta_pf']:>+6.2f} "
                 f"{r['avg_opt7k_pf']:>10.2f}")

    # --- Analisis temporal: forward PnL por posicion con fechas (Mejora 5) ---
    L.append(f"\n{'~'*100}")
    L.append(f"RENDIMIENTO FORWARD POR POSICION TEMPORAL")
    L.append(f"{'~'*100}")
    L.append(f"  (pos0 = mas reciente, posN = mas antiguo)\n")

    pos_agg = {
        'avg_fwd_pnl': ('fwd_pnl', 'mean'),
        'avg_opt7k_pf': ('opt7k_pf', 'mean'),
        'avg_delta_pf': ('delta_pf_57', 'mean'),
        'pct_fwd_pos': ('fwd_pnl', lambda x: (x > 0).mean() * 100),
        'fwd_start': ('fwd_start', 'first'),
        'fwd_end': ('fwd_end', 'first'),
    }
    if 'fwd_date_start' in results_df.columns:
        pos_agg['fwd_date_start'] = ('fwd_date_start', 'first')
        pos_agg['fwd_date_end'] = ('fwd_date_end', 'first')

    pos_summary = results_df.groupby('pos_idx').agg(**pos_agg)

    for pos, r in pos_summary.iterrows():
        date_str = ""
        if 'fwd_date_start' in pos_summary.columns and r.get('fwd_date_start', ''):
            date_str = f" [{r['fwd_date_start']} -> {r['fwd_date_end']}]"
        L.append(f"  pos{pos}: bars[{int(r['fwd_start'])}:{int(r['fwd_end'])}]{date_str}  "
                 f"avgFwdPnL:{r['avg_fwd_pnl']:>+6.2f}%  "
                 f"avgOptPF:{r['avg_opt7k_pf']:>5.2f}  "
                 f"avgdPF:{r['avg_delta_pf']:>+5.2f}  "
                 f"%pos:{r['pct_fwd_pos']:>4.0f}%")

    # --- Concentracion de riesgo (Mejora 4) ---
    if 'fwd_concentrated' in results_df.columns:
        n_concentrated = results_df['fwd_concentrated'].sum()
        if n_concentrated > 0:
            L.append(f"\n  AVISO: {n_concentrated} observaciones con flag fwd_concentrated=True")
            L.append(f"  (configs con <=5 trades y >50% del gross profit = PnL neto, posible dependencia de pocos trades grandes)")

    # --- Veredicto ---
    L.append(f"\n{'='*100}")
    L.append(f"VEREDICTO")
    L.append(f"{'='*100}")

    if 'delta_pf_57' in results_df.columns and len(results_df) >= 10:
        corr_dpf_fwd = results_df['delta_pf_57'].corr(results_df['fwd_pnl'])
        corr_pf7k_fwd = results_df['opt7k_pf'].corr(results_df['fwd_pnl'])
        corr_pasa7k_fwd = results_df['pasa_7k'].astype(float).corr(results_df['fwd_pnl'])

        L.append(f"\n  Correlaciones principales con Forward PnL:")
        L.append(f"    Delta PF 5k->7k:  r = {corr_dpf_fwd:+.3f}")
        L.append(f"    PF 7k (opt):      r = {corr_pf7k_fwd:+.3f}")
        L.append(f"    Pasa 7k:          r = {corr_pasa7k_fwd:+.3f}")

        # Interpretar
        signals = []
        if corr_dpf_fwd > 0.15:
            signals.append(f"Delta PF ASCENDENTE predice mejor forward (r={corr_dpf_fwd:+.3f})")
        elif corr_dpf_fwd < -0.15:
            signals.append(f"Delta PF ASCENDENTE NO predice mejor forward (r={corr_dpf_fwd:+.3f}, relacion inversa)")
        else:
            signals.append(f"Delta PF tiene correlacion debil con forward (r={corr_dpf_fwd:+.3f})")

        if corr_pf7k_fwd > 0.15:
            signals.append(f"PF 7k alto predice mejor forward (r={corr_pf7k_fwd:+.3f})")
        if corr_pasa7k_fwd > 0.15:
            signals.append(f"Pasar criterio 7k predice mejor forward (r={corr_pasa7k_fwd:+.3f})")

        for s in signals:
            L.append(f"    -> {s}")

        # Mejor metrica predictiva
        all_corrs = {}
        for pred_col, pred_label in predictors:
            if pred_col in results_df.columns:
                c = results_df[pred_col].corr(results_df['fwd_pnl'])
                if not np.isnan(c):
                    all_corrs[pred_label] = c

        if all_corrs:
            best_pred = max(all_corrs, key=lambda k: abs(all_corrs[k]))
            L.append(f"\n    Mejor predictor: {best_pred} (r={all_corrs[best_pred]:+.3f})")

    # --- Veredicto individual por config (Mejora 6) ---
    L.append(f"\n{'='*100}")
    L.append(f"VEREDICTO POR CONFIG")
    L.append(f"{'='*100}")

    # Obtener configs del grupo A promediadas por ventana
    if 'wf_group' in results_df.columns:
        group_a_cfgs = results_df[results_df['wf_group'] == 'A']['config_id'].unique()
    else:
        group_a_cfgs = results_df['config_id'].unique()

    if len(group_a_cfgs) > 0:
        L.append(f"\n  {'Cfg':<12s} {'Fam':>4s} {'Preset':<22s} {'FwdPnL':>7s} {'FwdPF':>6s} "
                 f"{'H1 PnL':>7s} {'H2 PnL':>7s} {'H2Rat':>6s} {'Conc':>4s} {'Veredicto':<10s}")
        L.append(f"  {'-'*12} {'-'*4} {'-'*22} {'-'*7} {'-'*6} {'-'*7} {'-'*7} {'-'*6} {'-'*4} {'-'*10}")

        for cid in group_a_cfgs:
            cfg_data = results_df[results_df['config_id'] == cid]
            if len(cfg_data) == 0:
                continue

            familia = cfg_data['familia'].iloc[0]
            ma_info = cfg_data['ma_info'].iloc[0]
            avg_pnl = cfg_data['fwd_pnl'].mean()
            avg_pf = cfg_data['fwd_pf'].mean()
            avg_h1 = cfg_data['fwd_h1_pnl'].mean() if 'fwd_h1_pnl' in cfg_data.columns else 0
            avg_h2 = cfg_data['fwd_h2_pnl'].mean() if 'fwd_h2_pnl' in cfg_data.columns else 0
            avg_h2r = cfg_data['fwd_h2_ratio'].mean() if 'fwd_h2_ratio' in cfg_data.columns else 0.5
            any_conc = cfg_data['fwd_concentrated'].any() if 'fwd_concentrated' in cfg_data.columns else False

            # Veredicto (Mejora 6)
            if avg_pnl <= 0:
                veredicto = "FALLA"
            elif avg_pf < 1.2:
                veredicto = "DEBIL"
            elif avg_h2r >= 0.75:
                veredicto = "CAUTELA"
            else:
                veredicto = "CONFIRMA"

            conc_flag = "SI" if any_conc else ""
            L.append(f"  {int(cid):<12d} {familia:>4s} {ma_info:<22s} {avg_pnl:>+6.1f}% {avg_pf:>5.2f} "
                     f"{avg_h1:>+6.1f}% {avg_h2:>+6.1f}% {avg_h2r:>5.3f} {conc_flag:>4s} {veredicto:<10s}")

        # Resumen de veredictos
        veredictos = {}
        for cid in group_a_cfgs:
            cfg_data = results_df[results_df['config_id'] == cid]
            if len(cfg_data) == 0:
                continue
            avg_pnl = cfg_data['fwd_pnl'].mean()
            avg_pf = cfg_data['fwd_pf'].mean()
            avg_h2r = cfg_data['fwd_h2_ratio'].mean() if 'fwd_h2_ratio' in cfg_data.columns else 0.5
            if avg_pnl <= 0:
                v = "FALLA"
            elif avg_pf < 1.2:
                v = "DEBIL"
            elif avg_h2r >= 0.75:
                v = "CAUTELA"
            else:
                v = "CONFIRMA"
            veredictos[v] = veredictos.get(v, 0) + 1

        L.append(f"\n  Resumen: " + " | ".join(f"{k}: {v}" for k, v in sorted(veredictos.items())))

    L.append(f"\n{'='*100}")

    return '\n'.join(L)


# -------------------------------------------------------------------
# 5. GUARDAR RESULTADOS
# -------------------------------------------------------------------

def save_results(results_df, analysis_txt, symbol, output_dir):
    """Guarda CSV y reporte de correlaciones."""
    sc = symbol.replace('/', '')

    csv_path = os.path.join(output_dir, f"walkforward_{sc}.csv")
    results_df.to_csv(csv_path, index=False)

    txt_path = os.path.join(output_dir, f"walkforward_{sc}_corr.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(analysis_txt)

    print(f"\n  CSV:      {csv_path}")
    print(f"  Analisis: {txt_path}")
    print(f"\n{analysis_txt}")


# -------------------------------------------------------------------
# 6. WF-OFFSET: VENTANA UNICA FORWARD
# -------------------------------------------------------------------

def run_wf_offset(symbol, sym_dir, lab, df_full, fwd_start, fwd_end, config):
    """Ejecuta walk-forward en modo offset: ventana unica forward sobre velas ocultas.

    Usa load_gems_and_metrics() para seleccion A/B desde pivot, y genera el mismo
    reporte enriquecido que el walk-forward simulado (correlaciones, h1/h2, veredictos).

    Args:
        symbol: par (ej. "BTC/USDT")
        sym_dir: directorio del simbolo con pivot/gemas/presets
        lab: modulo lab importado
        df_full: DataFrame COMPLETO (incluye velas ocultas), con timestamp
        fwd_start: indice inicio ventana forward (= n_total - offset)
        fwd_end: indice fin ventana forward (= n_total)
        config: dict con wf_opt_5k, wf_opt_7k (tamaños ventanas validacion)

    Returns:
        (results_df, timestamps) o (DataFrame vacio, None) si falla.
    """
    sc = symbol.replace('/', '')
    opt_5k = config.get("wf_opt_5k", OPT_5K)
    opt_7k = config.get("wf_opt_7k", OPT_7K)

    # --- Cargar candidatas desde pivot (grupo A + B) ---
    gems, pivot, wf_groups = load_gems_and_metrics(sym_dir, sc)
    if len(gems) == 0:
        print("  Sin configs para evaluar")
        return pd.DataFrame(), None

    # Cargar presets en el lab si no estan
    presets_csv = os.path.join(sym_dir, f"presets_{sc}.csv")
    if os.path.exists(presets_csv):
        try:
            from pipeline import load_presets_from_csv
            presets, cluster_ids = load_presets_from_csv(presets_csv)
            lab.SYMBOL_ZONE_PRESETS[symbol] = presets
            lab.PRESET_CLUSTER_IDS[symbol] = cluster_ids
        except ImportError:
            pass
    if symbol not in lab.SYMBOL_ZONE_PRESETS:
        print(f"Error: sin presets para {symbol}")
        return pd.DataFrame(), None

    groups = group_gems_by_preset(gems, symbol, lab)
    print(f"  Grupos preset: {len(groups)}")

    # Preparar metricas del validador para lookup rapido
    val_metrics = {}
    if pivot is not None:
        val_cols = ['pf_5k', 'pf_7k', 'maxdd_5k', 'maxdd_7k', 'trades_5k', 'trades_7k',
                    'pnl_5k', 'pnl_7k', 'delta_pf_57', 'delta_dd_57',
                    'seg_consistency', 'seg_avg_pnl', 'seg_min_pnl', 'pasa_7k',
                    'score_5k', 'score_7k']
        available_cols = [c for c in val_cols if c in pivot.columns]
        for _, r in pivot.iterrows():
            val_metrics[int(r['config_id'])] = {c: r[c] for c in available_cols}

    # --- Timestamps ---
    timestamps = df_full['timestamp'] if 'timestamp' in df_full.columns else None

    # --- Calcular indices de validacion (sobre datos recortados, sin forward) ---
    # opt_5k y opt_7k se calculan hacia atras desde fwd_start
    opt_5k_start = fwd_start - opt_5k
    opt_7k_start = fwd_start - opt_7k
    fwd_size = fwd_end - fwd_start
    fwd_mid = fwd_start + fwd_size // 2

    if opt_7k_start < 0:
        print(f"  AVISO: datos insuficientes para ventana 7k (necesita {opt_7k}, disponible {fwd_start})")
        opt_7k_start = 0
    if opt_5k_start < 0:
        opt_5k_start = 0

    print(f"\n  WF-Offset: opt_7k=[{opt_7k_start}:{fwd_start}], opt_5k=[{opt_5k_start}:{fwd_start}]")
    print(f"  Forward: [{fwd_start}:{fwd_end}] = {fwd_size} bars")
    print(f"  Forward H1: [{fwd_start}:{fwd_mid}], H2: [{fwd_mid}:{fwd_end}]")

    # Fechas reales
    fwd_date_start_str = ""
    fwd_date_end_str = ""
    if timestamps is not None:
        try:
            fwd_date_start_str = str(timestamps.iloc[fwd_start])[:10]
            fwd_date_end_str = str(timestamps.iloc[min(fwd_end - 1, len(timestamps) - 1)])[:10]
        except (IndexError, KeyError):
            pass
    if fwd_date_start_str:
        print(f"  Periodo forward: {fwd_date_start_str} -> {fwd_date_end_str}")

    all_results = []
    t_global = time.time()

    for g_idx, (group_key, group) in enumerate(groups.items()):
        preset = group['preset']
        hyst = group['hyst']
        config_list = group['configs']
        preset_label = f"{group_key[0]} H{hyst:.1f}"

        print(f"\n  {'='*60}")
        print(f"  Grupo {g_idx+1}/{len(groups)}: {preset_label} ({len(config_list)} configs)")

        # Precalcular indicadores sobre TODOS los datos (necesario para warmup)
        print(f"  Precalculando indicadores...")
        t0 = time.time()
        data = lab.precalculate_all_data(df_full, preset=preset, hyst_mult=hyst, symbol=symbol)
        n_bars = len(data['close'])
        print(f"  Precalculo: {time.time()-t0:.1f}s ({n_bars} bars)")

        config_ids = np.array([c['config_id'] for c in config_list], dtype=np.uint32)

        t0 = time.time()

        # 1. Opt 7k (sobre datos recortados)
        res_7k = lab.run_on_slice(
            config_ids, data, opt_7k_start, fwd_start,
            lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
            lab.TS_PERCENT, lab.COOLDOWN_BARS,
            lab.COMMISSION_ROUND_TRIP
        )

        # 2. Opt 5k (sobre datos recortados)
        res_5k = lab.run_on_slice(
            config_ids, data, opt_5k_start, fwd_start,
            lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
            lab.TS_PERCENT, lab.COOLDOWN_BARS,
            lab.COMMISSION_ROUND_TRIP
        )

        # 3. Forward completo
        res_fwd = lab.run_on_slice(
            config_ids, data, fwd_start, fwd_end,
            lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
            lab.TS_PERCENT, lab.COOLDOWN_BARS,
            lab.COMMISSION_ROUND_TRIP
        )

        # 4. Forward H1
        res_fwd_h1 = lab.run_on_slice(
            config_ids, data, fwd_start, fwd_mid,
            lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
            lab.TS_PERCENT, lab.COOLDOWN_BARS,
            lab.COMMISSION_ROUND_TRIP
        )

        # 5. Forward H2
        res_fwd_h2 = lab.run_on_slice(
            config_ids, data, fwd_mid, fwd_end,
            lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
            lab.TS_PERCENT, lab.COOLDOWN_BARS,
            lab.COMMISSION_ROUND_TRIP
        )

        t_sim = time.time() - t0

        # --- Metricas ---
        def extract_metrics(res, n_bars_slice, prefix):
            pnl = res[:, 0]
            trades = res[:, 1]
            wins = res[:, 2]
            cancels = res[:, 3]
            maxdd = res[:, 4]
            gp = res[:, 5]
            gl = res[:, 6]
            _, pnl_ann, _, pf, _, _ = lab.calc_score_v63(
                pnl, maxdd, gp, gl, trades, cancels, n_bars_slice)
            wr = np.where(trades > 0, wins / trades * 100, 0.0)
            return {
                f'{prefix}_pnl': pnl,
                f'{prefix}_trades': trades,
                f'{prefix}_maxdd': maxdd,
                f'{prefix}_pf': pf,
                f'{prefix}_wr': wr,
                f'{prefix}_pnl_ann': pnl_ann,
                f'{prefix}_gp': gp,
                f'{prefix}_gl': gl,
            }

        m_7k = extract_metrics(res_7k, fwd_start - opt_7k_start, 'opt7k')
        m_5k = extract_metrics(res_5k, fwd_start - opt_5k_start, 'opt5k')
        m_fwd = extract_metrics(res_fwd, fwd_size, 'fwd')

        # Mitades
        h1_pnl = res_fwd_h1[:, 0]
        h1_trades = res_fwd_h1[:, 1]
        h1_gp = res_fwd_h1[:, 5]
        h1_gl = res_fwd_h1[:, 6]
        h1_maxdd = res_fwd_h1[:, 4]
        h1_cancels = res_fwd_h1[:, 3]
        _, _, _, h1_pf, _, _ = lab.calc_score_v63(
            h1_pnl, h1_maxdd, h1_gp, h1_gl, h1_trades, h1_cancels, fwd_size // 2)

        h2_pnl = res_fwd_h2[:, 0]
        h2_trades = res_fwd_h2[:, 1]
        h2_gp = res_fwd_h2[:, 5]
        h2_gl = res_fwd_h2[:, 6]
        h2_maxdd = res_fwd_h2[:, 4]
        h2_cancels = res_fwd_h2[:, 3]
        _, _, _, h2_pf, _, _ = lab.calc_score_v63(
            h2_pnl, h2_maxdd, h2_gp, h2_gl, h2_trades, h2_cancels, fwd_size - fwd_size // 2)

        denom = np.abs(h1_pnl) + np.abs(h2_pnl)
        h2_ratio = np.where(denom > 0, h2_pnl / denom, 0.5)

        # Delta PF
        delta_pf = m_7k['opt7k_pf'] - m_5k['opt5k_pf']
        delta_dd = m_7k['opt7k_maxdd'] - m_5k['opt5k_maxdd']

        # Pasa 7k
        pasa_7k_arr = (m_7k['opt7k_pf'] >= 2.0) & (m_7k['opt7k_maxdd'] <= 10.0)

        for i, cfg in enumerate(config_list):
            cid = cfg['config_id']

            row = {
                'config_id': cid,
                'familia': cfg['familia'],
                'ma_info': cfg['ma_info'],
                'wf_group': wf_groups.get(cid, 'A'),
                'pos_idx': 0,  # Ventana unica
                'opt7k_start': int(opt_7k_start),
                'opt7k_end': int(fwd_start),
                'opt5k_start': int(opt_5k_start),
                'fwd_start': int(fwd_start),
                'fwd_end': int(fwd_end),
                'fwd_n_bars': fwd_size,
                'fwd_date_start': fwd_date_start_str,
                'fwd_date_end': fwd_date_end_str,
            }

            # Metricas de optimizacion (recalculadas in-situ)
            for key in m_5k:
                row[key] = float(m_5k[key][i])
            for key in m_7k:
                row[key] = float(m_7k[key][i])

            row['delta_pf_57'] = float(delta_pf[i])
            row['delta_dd_57'] = float(delta_dd[i])
            row['pasa_7k'] = bool(pasa_7k_arr[i])

            # Forward completo
            for key in m_fwd:
                row[key] = float(m_fwd[key][i])

            # Forward mitades
            row['fwd_h1_pnl'] = float(h1_pnl[i])
            row['fwd_h1_pf'] = float(h1_pf[i])
            row['fwd_h1_trades'] = int(h1_trades[i])
            row['fwd_h2_pnl'] = float(h2_pnl[i])
            row['fwd_h2_pf'] = float(h2_pf[i])
            row['fwd_h2_trades'] = int(h2_trades[i])
            row['fwd_h2_ratio'] = float(h2_ratio[i])

            # Flag de concentracion
            fwd_trades_i = float(m_fwd['fwd_trades'][i])
            fwd_pnl_i = float(m_fwd['fwd_pnl'][i])
            fwd_gp_i = float(m_fwd['fwd_gp'][i])
            concentrated = False
            if fwd_trades_i <= 5 and fwd_pnl_i > 0 and fwd_gp_i > 0:
                if fwd_pnl_i / fwd_gp_i > 0.5:
                    concentrated = True
            row['fwd_concentrated'] = concentrated

            # Metricas originales del validador (del pivot, fijas por config)
            if cid in val_metrics:
                for vk, vv in val_metrics[cid].items():
                    row[f'val_{vk}'] = vv

            all_results.append(row)

        # Resumen
        avg_fwd_pnl = np.mean(m_fwd['fwd_pnl'])
        avg_opt_pf = np.mean(m_7k['opt7k_pf'])
        n_pf_up = np.sum(delta_pf > 0)
        date_info = f" [{fwd_date_start_str} -> {fwd_date_end_str}]" if fwd_date_start_str else ""
        print(f"    fwd[{fwd_start}:{fwd_end}]{date_info}  "
              f"avgOptPF:{avg_opt_pf:.2f}  dPF+:{n_pf_up}/{len(config_ids)}  "
              f"avgFwdPnL:{avg_fwd_pnl:+.2f}%  ({t_sim:.2f}s)")

    elapsed = time.time() - t_global
    print(f"\n  Total: {elapsed:.1f}s")

    return pd.DataFrame(all_results), timestamps


# -------------------------------------------------------------------
# 7. MAIN
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Walk-Forward Simulado v1')
    parser.add_argument('symbol', help='Simbolo (ej: BNB/USDT)')
    parser.add_argument('sym_dir', help='Directorio del simbolo (con gemas, presets, etc.)')
    parser.add_argument('--opt-7k', type=int, default=OPT_7K,
                       help=f'Ventana de optimizacion 7k (default: {OPT_7K})')
    parser.add_argument('--opt-5k', type=int, default=OPT_5K,
                       help=f'Sub-ventana de optimizacion 5k (default: {OPT_5K})')
    parser.add_argument('--fwd-size', type=int, default=FWD_SIZE,
                       help=f'Ventana forward (default: {FWD_SIZE})')
    parser.add_argument('--step', type=int, default=STEP,
                       help=f'Paso entre posiciones (default: {STEP})')
    parser.add_argument('--total-candles', type=int, default=TOTAL_CANDLES,
                       help=f'Total de velas a usar (default: {TOTAL_CANDLES})')
    parser.add_argument('--lab', default='lab_historico_numba_v8_3.py',
                       help='Archivo del lab')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  WALK-FORWARD SIMULADO v1")
    print(f"  {args.symbol}")
    print(f"  opt_7k={args.opt_7k} | opt_5k={args.opt_5k} | fwd={args.fwd_size} | step={args.step}")
    print(f"  {args.total_candles} candles")
    print(f"{'='*60}")

    # Importar lab
    print(f"\n  Importando {args.lab}...")
    t0 = time.time()
    lab = import_lab(args.lab)
    print(f"  Lab importado en {time.time()-t0:.1f}s")

    # Ejecutar walk-forward
    results_df, timestamps = run_walk_forward(
        args.symbol, args.sym_dir, lab,
        args.opt_7k, args.opt_5k, args.fwd_size, args.step,
        args.total_candles
    )

    if len(results_df) > 0:
        analysis = analyze_correlations(results_df, args.symbol, args.sym_dir, timestamps)
        save_results(results_df, analysis, args.symbol, args.sym_dir)
    else:
        print("  Sin resultados")

    print(f"\n  Completado.\n")


if __name__ == '__main__':
    main()
