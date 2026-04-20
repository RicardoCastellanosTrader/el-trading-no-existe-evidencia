#!/usr/bin/env python3
"""
validador_batch_v3.py — Mini-lab para validar gemas usando el motor del lab completo.

Importa funciones de lab_historico_numba_v8_3.py directamente.
Descarga datos una vez por preset, precalcula una vez, corre solo las configs gema.

Uso:
    python validador_batch_v3.py BTC/USDT gemas_BTCUSDT.csv
    python validador_batch_v3.py BNB/USDT gemas_BNBUSDT.csv --segments 3
    python validador_batch_v3.py BTC/USDT gemas_BTCUSDT.csv --max-configs 10

Requisitos:
    - lab_historico_numba_v8_3.py en el mismo directorio
    - gemas_SYMBOL.csv del extractor de gemas

Genera:
    validacion_gemas_SYMBOL.csv       — Resultados por config x ventana/segmento
    validacion_gemas_SYMBOL_pivot.csv — 1 fila por config, columnas por ventana
    validacion_gemas_SYMBOL.txt       — Resumen legible
"""

import os
import sys
import time
import argparse
import importlib.util

import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# 0. IMPORTAR LAB COMO MODULO
# -------------------------------------------------------------------

def import_lab(lab_filename="lab_historico_numba_v8_3.py"):
    """Importa el lab como modulo sin ejecutar main()."""
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

WINDOW_SIZE = 5000       # Tamano de cada segmento/ventana base
ACUM_WINDOWS = [5000, 7000, 10000]  # Ventanas acumulativas
DEFAULT_SEGMENTS = 3     # Segmentos aislados de 5k (seg0=reciente, seg1=offset 5k, seg2=offset 10k)
WARMUP_EXTRA = 500       # Margen extra para warmup de MAs largas


# -------------------------------------------------------------------
# 2. AGRUPACION DE GEMAS POR PRESET
# -------------------------------------------------------------------

def group_gems_by_preset(gems, symbol, lab):
    """Agrupa gemas por (preset_tuple, hyst) para minimizar precalculos."""
    
    registry = lab.SYMBOL_ZONE_PRESETS.get(symbol, [])
    if not registry:
        print(f"Error: sin presets para {symbol} en el lab")
        sys.exit(1)
    
    # Construir mapeo ma_info -> (preset_tuple, hyst_mult)
    # Necesitamos parsear ma_info del CSV y encontrar el preset correspondiente
    preset_map = {}
    for preset in registry:
        ft, fl, fp1, fp2 = preset[0], preset[1], preset[2], preset[3]
        st, sl, sp1, sp2 = preset[4], preset[5], preset[6], preset[7]
        # Generar la key como aparece en el CSV: "T3(20)/SMA(33)"
        key = f"{ft}({fl})/{st}({sl})"
        preset_map[key] = preset
    
    groups = {}  # (preset_key, hyst) -> list of (config_id, familia, ma_info)
    missing = set()
    
    for _, gem in gems.iterrows():
        ma_info = gem['ma_info']
        # Extraer key sin H00/H05
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
# 3. EJECUCION PRINCIPAL
# -------------------------------------------------------------------

def run_gem_validation(symbol, gems_csv, segments, max_configs, lab):
    """Ejecuta la validacion de gemas usando el motor del lab."""
    
    gems = pd.read_csv(gems_csv)
    gems_unique = gems.drop_duplicates(subset='config_id').copy()
    if max_configs > 0:
        gems_unique = gems_unique.head(max_configs)
    
    n_configs = len(gems_unique)
    print(f"\n  Configs: {n_configs}")
    
    groups = group_gems_by_preset(gems_unique, symbol, lab)
    print(f"  Grupos preset: {len(groups)}")
    for gk, gv in groups.items():
        print(f"    {gk[0]} H{gv['hyst']:.1f}: {len(gv['configs'])} configs")
    
    # Calcular candles necesarias
    max_offset = (segments - 1) * WINDOW_SIZE if segments > 1 else 0
    max_acum = max(ACUM_WINDOWS)
    total_candles_needed = max(max_acum, WINDOW_SIZE + max_offset) + WARMUP_EXTRA
    
    n_runs_per_config = len(ACUM_WINDOWS) + max(segments - 1, 0)  # seg0 = acum:5k
    total_runs = n_configs * n_runs_per_config
    print(f"\n  Total candles a descargar: {total_candles_needed}")
    print(f"  Runs por config: {n_runs_per_config} ({len(ACUM_WINDOWS)} acum + {max(segments-1,0)} seg)")
    print(f"  Total runs: {total_runs}")
    
    all_results = []
    t_global = time.time()

    # --- Descargar datos UNA VEZ para todos los grupos ---
    print(f"\n  Descargando {total_candles_needed} candles...")
    t0 = time.time()
    df = lab.fetch_all_candles(symbol, "1h", total_candles_needed)
    if df is None or len(df) < total_candles_needed * 0.9:
        print(f"  Error: datos insuficientes ({len(df) if df is not None else 0})")
        return pd.DataFrame()
    print(f"  Descarga: {time.time()-t0:.1f}s ({len(df)} candles)")

    for g_idx, (group_key, group) in enumerate(groups.items()):
        preset = group['preset']
        hyst = group['hyst']
        config_list = group['configs']
        preset_label = f"{group_key[0]} H{hyst:.1f}"

        print(f"\n  {'='*60}")
        print(f"  Grupo {g_idx+1}/{len(groups)}: {preset_label} ({len(config_list)} configs)")
        print(f"  {'='*60}")
        
        # --- Precalcular indicadores UNA VEZ ---
        print(f"  Precalculando indicadores...")
        t0 = time.time()
        data = lab.precalculate_all_data(df, preset=preset, hyst_mult=hyst, symbol=symbol)
        n_bars = len(data['close'])
        print(f"  Precalculo: {time.time()-t0:.1f}s ({n_bars} bars)")
        
        # --- Crear array de configs ---
        config_ids = np.array([c['config_id'] for c in config_list], dtype=np.uint32)
        config_meta = {c['config_id']: c for c in config_list}
        
        # --- Definir slices ---
        slices = []
        
        # Acumulativas: ultimas N bars
        for w in ACUM_WINDOWS:
            wk = w // 1000
            start = max(n_bars - w, 0)
            end = n_bars
            slices.append({
                'run_type': 'acum', 'run_label': f'{wk}k',
                'start': start, 'end': end, 'n_bars_slice': end - start
            })
        
        # Segmentos aislados (seg0 = acum:5k, no se repite)
        if segments > 1:
            for s in range(1, segments):
                offset = s * WINDOW_SIZE
                end = n_bars - offset
                start = end - WINDOW_SIZE
                if start < 0:
                    print(f"  AVISO: seg{s} requiere mas datos, saltando")
                    continue
                slices.append({
                    'run_type': 'seg', 'run_label': f'seg{s}',
                    'start': start, 'end': end, 'n_bars_slice': WINDOW_SIZE
                })
        
        # --- Ejecutar simulaciones ---
        for sl in slices:
            label = f"{sl['run_type']}:{sl['run_label']}"
            t0 = time.time()
            
            results = lab.run_on_slice(
                config_ids, data, sl['start'], sl['end'],
                lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT,
                lab.TS_PERCENT, lab.COOLDOWN_BARS,
                lab.COMMISSION_ROUND_TRIP
            )
            
            t_sim = time.time() - t0
            
            # results shape: (n_configs, 7) = [pnl, trades, wins, cancels, maxdd, gp, gl]
            pnl_arr = results[:, 0]
            trades_arr = results[:, 1]
            wins_arr = results[:, 2]
            cancels_arr = results[:, 3]
            maxdd_arr = results[:, 4]
            gp_arr = results[:, 5]
            gl_arr = results[:, 6]
            
            # Calcular metricas
            n_slice_bars = sl['n_bars_slice']
            score_arr, pnl_ann_arr, dd_f_arr, pf_arr, act_f_arr, cr_arr = \
                lab.calc_score_v63(pnl_arr, maxdd_arr, gp_arr, gl_arr,
                                   trades_arr, cancels_arr, n_slice_bars)
            wr_arr = np.where(trades_arr > 0, wins_arr / trades_arr * 100, 0.0)
            
            # Separar long/short PnL no esta disponible directamente del motor numba
            # (el motor solo devuelve agregados), pero podemos calcular PF y WR
            
            # Guardar resultados
            for i, cfg in enumerate(config_list):
                cid = cfg['config_id']
                pf_val = float(pf_arr[i]) if not np.isnan(pf_arr[i]) else 0.0
                
                row = {
                    'config_id': cid,
                    'familia': cfg['familia'],
                    'ma_info': cfg['ma_info'],
                    'run_type': sl['run_type'],
                    'run_label': sl['run_label'],
                    'n_bars': n_slice_bars,
                    'pnl': float(pnl_arr[i]),
                    'trades': int(trades_arr[i]),
                    'wins': int(wins_arr[i]),
                    'cancels': int(cancels_arr[i]),
                    'maxdd': float(maxdd_arr[i]),
                    'pf': pf_val,
                    'wr': float(wr_arr[i]),
                    'pnl_ann': float(pnl_ann_arr[i]),
                    'score': float(score_arr[i]),
                    'gross_profit': float(gp_arr[i]),
                    'gross_loss': float(gl_arr[i]),
                }
                all_results.append(row)
            
            # Resumen rapido
            n_pass = np.sum((pf_arr >= 2.0) & (maxdd_arr <= 10.0)) if sl['run_type'] == 'acum' and sl['n_bars_slice'] >= 7000 else 0
            n_toxic = np.sum(pnl_arr < 0)
            avg_pnl = np.mean(pnl_arr)
            best_pf = np.max(pf_arr)
            print(f"    {label:<10s} {n_slice_bars:>5d}bars  avgPnL:{avg_pnl:>+6.1f}%  "
                  f"bestPF:{best_pf:>5.2f}  toxic:{n_toxic}/{len(config_ids)}"
                  f"{'  PASS:'+str(n_pass) if n_pass > 0 else ''}  ({t_sim:.2f}s)")
    
    elapsed = time.time() - t_global
    print(f"\n  Total: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    
    return pd.DataFrame(all_results)


# -------------------------------------------------------------------
# 4. PIVOTEO
# -------------------------------------------------------------------

def build_pivot(df, segments):
    if len(df) == 0:
        return pd.DataFrame()
    
    pivot_rows = []
    for cid in df['config_id'].unique():
        cfg = df[df['config_id'] == cid]
        row = {'config_id': cid, 'familia': cfg.iloc[0]['familia'],
               'ma_info': cfg.iloc[0]['ma_info']}
        
        for _, r in cfg[cfg['run_type'] == 'acum'].iterrows():
            lb = r['run_label']
            for col in ['pnl','maxdd','pf','trades','wr','pnl_ann','score','gross_profit','gross_loss']:
                row[f'{col}_{lb}'] = r[col]
        
        # Segmentos: seg0 = copia de 5k
        if 'pnl_5k' in row:
            for col in ['pnl','maxdd','pf','trades','wr']:
                row[f'{col}_seg0'] = row.get(f'{col}_5k', np.nan)
        
        for _, r in cfg[cfg['run_type'] == 'seg'].iterrows():
            lb = r['run_label']
            for col in ['pnl','maxdd','pf','trades','wr']:
                row[f'{col}_{lb}'] = r[col]
        
        pivot_rows.append(row)
    
    pivot = pd.DataFrame(pivot_rows)
    
    # Metricas derivadas
    if 'pf_5k' in pivot.columns and 'pf_7k' in pivot.columns:
        pivot['delta_pf_57'] = pivot['pf_7k'] - pivot['pf_5k']
        pivot['delta_dd_57'] = pivot['maxdd_7k'] - pivot['maxdd_5k']
    
    if 'pf_7k' in pivot.columns:
        pivot['pasa_7k'] = (pivot['pf_7k'] >= 2.0) & (pivot['maxdd_7k'] <= 10.0)
    
    # Consistencia de segmentos
    seg_pnl_cols = sorted([c for c in pivot.columns if c.startswith('pnl_seg')])
    if seg_pnl_cols:
        pivot['n_seg_pos'] = pivot[seg_pnl_cols].apply(lambda x: (x > 0).sum(), axis=1)
        pivot['n_seg_total'] = len(seg_pnl_cols)
        pivot['seg_consistency'] = pivot['n_seg_pos'] / pivot['n_seg_total']
        pivot['seg_avg_pnl'] = pivot[seg_pnl_cols].mean(axis=1)
        pivot['seg_min_pnl'] = pivot[seg_pnl_cols].min(axis=1)
    
    return pivot


# -------------------------------------------------------------------
# 5. REPORTE
# -------------------------------------------------------------------

def decode_config_short(config_id):
    """Decodifica config_id a descripcion legible."""
    cfg = int(config_id)
    exit_mask = cfg & 0xF
    entry_mask = (cfg >> 4) & 0x1F
    div_entry_mode = (cfg >> 9) & 0x3
    div_exit = (cfg >> 11) & 0x1
    div_type = (cfg >> 12) & 0x3
    div_ind_mask = (cfg >> 14) & 0xFF
    cancel_tf = (cfg >> 22) & 0x1
    use_ts = (cfg >> 23) & 0x1
    reg_inv = (cfg >> 24) & 0x1
    hid_inv = (cfg >> 25) & 0x1

    entry_tfs = []
    for i, name in enumerate(["TF1","TF2","TF3","TF4","TF5"]):
        if entry_mask & (1 << i): entry_tfs.append(name)
    exit_tfs = []
    for i, name in enumerate(["TF1","TF2","TF3","TF4"]):
        if exit_mask & (1 << i): exit_tfs.append(name)
    if exit_mask == 0: exit_tfs.append("ZONA")

    inds = []
    for i, name in enumerate(["RSI","MACD_H","MACD_L","STOCH","VWMACD","CMF","CCI","MOM"]):
        if div_ind_mask & (1 << i): inds.append(name)

    div_mode = ["OFF","CONTEXTUAL","OR"][div_entry_mode]
    div_tp = ["NONE","REGULAR","HIDDEN","BOTH"][div_type]
    variant = {(0,0):"FIX",(0,1):"ORIGINAL",(1,1):"ALLINV",(1,0):"REGINV"}.get((reg_inv,hid_inv),"?")
    sl = "Trailing Stop" if use_ts else "Stop Loss Fijo"
    cancel = "ON (TF)" if cancel_tf else "OFF"

    entry_str = "+".join(entry_tfs) if entry_tfs else "ZONA"
    exit_str = "+".join(exit_tfs)
    inds_str = "+".join(inds) if inds else "NONE"

    ind_names = ["RSI","MACD_H","MACD_L","STOCH","VWMACD","CMF","CCI","MOM"]
    inds_dict = {name: bool(div_ind_mask & (1 << i)) for i, name in enumerate(ind_names)}

    return {
        'entry': entry_str, 'exit': exit_str,
        'div_entry': div_mode, 'div_exit': "ON" if div_exit else "OFF",
        'div_type': div_tp, 'variant': variant,
        'indicators': inds_str, 'indicators_dict': inds_dict,
        'sl': sl, 'cancel': cancel,
        'reg_str': "Invertida" if reg_inv else "Tradicional",
        'hid_str': "Invertida" if hid_inv else "Tradicional",
        'entry_mask': entry_mask, 'exit_mask': exit_mask,
    }


def format_preset_params(ma_info, symbol, lab):
    """Busca los parametros completos del preset en el lab."""
    if lab is None:
        return None
    registry = lab.SYMBOL_ZONE_PRESETS.get(symbol, [])
    # Parse ma_info: "KAMA(14)/ALMA(42) H00" -> key="KAMA(14)/ALMA(42)"
    key = ma_info.rsplit(' ', 1)[0].strip()
    for preset in registry:
        ft, fl, fp1, fp2 = preset[0], preset[1], preset[2], preset[3]
        st, sl, sp1, sp2 = preset[4], preset[5], preset[6], preset[7]
        tt, tl, tp1, tp2 = preset[8], preset[9], preset[10], preset[11]
        check_key = f"{ft}({fl})/{st}({sl})"
        if check_key == key:
            # Format fast
            fast_str = f"{ft}({fl}"
            if ft == "T3" and fp1 > 0: fast_str += f",v{fp1}"
            elif ft == "ALMA": fast_str += f",off={fp1},sig={fp2}"
            fast_str += ")"
            # Format slow
            slow_str = f"{st}({sl}"
            if st == "T3" and sp1 > 0: slow_str += f",v{sp1}"
            elif st == "ALMA": slow_str += f",off={sp1},sig={sp2}"
            slow_str += ")"
            # Format trend
            if tt != "NONE" and tl > 0:
                trend_str = f"{tt}({tl}"
                if tt == "T3" and tp1 > 0: trend_str += f",v{tp1}"
                elif tt == "ALMA": trend_str += f",off={tp1},sig={tp2}"
                trend_str += ")"
            else:
                trend_str = "NONE"
            hyst = "0.5" if "H05" in ma_info else "0.0"
            return f"Fast={fast_str} | Slow={slow_str} | Trend={trend_str} | Hyst={hyst}"
    return None


def format_config_block(config_id, prefix="     ", ma_info=None, symbol=None, lab=None):
    """Formatea bloque compacto de config decodificada (para top 5)."""
    d = decode_config_short(config_id)
    lines = []
    if ma_info and lab:
        preset_str = format_preset_params(ma_info, symbol, lab)
        if preset_str:
            lines.append(f"{prefix}MAs: {preset_str}")
    lines.append(f"{prefix}Entry: {d['entry']} | Exit: {d['exit']} | SL: {d['sl']} | Cancel: {d['cancel']}")
    lines.append(f"{prefix}Div: Entry={d['div_entry']}, Exit={d['div_exit']}, Type={d['div_type']}, Variant={d['variant']}")
    lines.append(f"{prefix}Indicadores: {d['indicators']}")
    return lines


def get_preset_detail(ma_info, symbol, lab):
    """Retorna dict con parametros completos del preset."""
    if lab is None:
        return None
    registry = lab.SYMBOL_ZONE_PRESETS.get(symbol, [])
    key = ma_info.rsplit(' ', 1)[0].strip()
    hyst = 0.5 if 'H05' in ma_info else 0.0
    for preset in registry:
        ft, fl, fp1, fp2 = preset[0], preset[1], preset[2], preset[3]
        st, sl, sp1, sp2 = preset[4], preset[5], preset[6], preset[7]
        tt, tl, tp1, tp2 = preset[8], preset[9], preset[10], preset[11]
        if f"{ft}({fl})/{st}({sl})" == key:
            return {
                'fast': {'type': ft, 'period': fl, 'p1': fp1, 'p2': fp2},
                'slow': {'type': st, 'period': sl, 'p1': sp1, 'p2': sp2},
                'trend': {'type': tt, 'period': tl, 'p1': tp1, 'p2': tp2},
                'hyst': hyst,
            }
    return None


def format_ma_detail(label, ma):
    """Formatea una MA con todos sus parametros secundarios."""
    lines = []
    lines.append(f"  {label+' MA:':<16s} {ma['type']}")
    lines.append(f"    Periodo:      {ma['period']}")
    t = ma['type']
    if t == 'T3' and ma['p1'] > 0:
        lines.append(f"    V-Factor:     {ma['p1']}")
    elif t == 'ALMA':
        lines.append(f"    Offset:       {ma['p1']}")
        lines.append(f"    Sigma:        {ma['p2']}")
    elif t == 'JMA' and ma['p1'] != 0:
        lines.append(f"    Phase:        {ma['p1']}")
        lines.append(f"    Power:        {ma['p2']}")
    return lines


def format_indicator_config(config_id, ma_info, symbol, lab, prefix="  "):
    """Genera bloque completo de configuracion para el indicador."""
    d = decode_config_short(config_id)
    preset = get_preset_detail(ma_info, symbol, lab)
    P = prefix
    L = []

    L.append(f"{P}CONFIGURACION INDICADOR")
    L.append(f"{P}{'─'*46}")

    # MAs
    L.append(f"{P}")
    L.append(f"{P}MEDIAS MOVILES (Zonas)")
    L.append(f"{P}{'─'*46}")
    if preset:
        for label, ma in [('Fast', preset['fast']), ('Slow', preset['slow']), ('Trend', preset['trend'])]:
            for line in format_ma_detail(label, ma):
                L.append(f"{P}{line[2:]}")  # strip leading 2 spaces, add prefix
        L.append(f"{P}Histeresis ATR: {preset['hyst']}")
    else:
        L.append(f"{P}Preset: {ma_info} (parametros no disponibles)")

    # Entry TFs
    L.append(f"{P}")
    L.append(f"{P}FILTROS DE ENTRADA (TF)")
    L.append(f"{P}{'─'*46}")
    for tf, bit in [("TF1",0),("TF2",1),("TF3",2),("TF4",3),("TF5",4)]:
        on = bool(d['entry_mask'] & (1 << bit))
        L.append(f"{P}{tf}:             {'ON' if on else 'OFF'}")

    # Exit TFs
    L.append(f"{P}")
    L.append(f"{P}FILTROS DE SALIDA (TF)")
    L.append(f"{P}{'─'*46}")
    if d['exit_mask'] == 0:
        L.append(f"{P}Salida:         ZONA (cambio de zona)")
    else:
        for tf, bit in [("TF1",0),("TF2",1),("TF3",2),("TF4",3)]:
            on = bool(d['exit_mask'] & (1 << bit))
            L.append(f"{P}{tf}:             {'ON' if on else 'OFF'}")

    # Divergencias
    L.append(f"{P}")
    L.append(f"{P}DIVERGENCIAS")
    L.append(f"{P}{'─'*46}")
    L.append(f"{P}Div Entry:      {d['div_entry']}")
    L.append(f"{P}Div Exit:       {d['div_exit']}")
    L.append(f"{P}Div Type:       {d['div_type']}")
    L.append(f"{P}Regular:        {d['reg_str']}")
    L.append(f"{P}Hidden:         {d['hid_str']}")

    # Indicadores
    L.append(f"{P}")
    L.append(f"{P}INDICADORES DE DIVERGENCIA")
    L.append(f"{P}{'─'*46}")
    for ind_name in ["RSI","MACD_H","MACD_L","STOCH","VWMACD","CMF","CCI","MOM"]:
        on = d['indicators_dict'][ind_name]
        L.append(f"{P}{ind_name:<16s} {'ON' if on else 'OFF'}")

    # Risk
    L.append(f"{P}")
    L.append(f"{P}GESTION DE RIESGO")
    L.append(f"{P}{'─'*46}")
    L.append(f"{P}Stop Loss:      {d['sl']}")
    L.append(f"{P}Cancelacion:    {d['cancel']}")

    return L


def fmt(val, f, default="    --"):
    if pd.isna(val): return default
    return f"{val:{f}}"


def generate_report(df, pivot, symbol, output_dir='.', lab=None):
    sc = symbol.replace('/', '')
    
    csv_f = os.path.join(output_dir, f'validacion_gemas_{sc}.csv')
    df.to_csv(csv_f, index=False)
    piv_f = os.path.join(output_dir, f'validacion_gemas_{sc}_pivot.csv')
    pivot.to_csv(piv_f, index=False)
    
    L = []
    L.append(f"{'='*130}")
    L.append(f"VALIDACION GEMAS (motor lab) -- {symbol} -- {len(pivot)} configs")
    L.append(f"{'='*130}\n")
    
    has_7k = 'pf_7k' in pivot.columns
    has_seg = 'seg_consistency' in pivot.columns
    seg_labels = sorted([c.replace('pnl_','') for c in pivot.columns if c.startswith('pnl_seg')])
    
    # --- PASAN 7k ---
    if has_7k:
        pasadas = pivot[pivot['pasa_7k'] == True].sort_values('pf_7k', ascending=False)
        L.append(f"PASAN CRITERIO 7k (PF>=2.0, DD<=10%): {len(pasadas)} de {len(pivot)}\n")
        if len(pasadas) > 0:
            for _, r in pasadas.iterrows():
                segs = ""
                if has_seg:
                    for sl in seg_labels:
                        v = r.get(f'pnl_{sl}', np.nan)
                        segs += f"  {sl}:{fmt(v,'>+5.1f')}%"
                    segs += f"  consist:{r['seg_consistency']:.0%}"
                L.append(f"  {int(r['config_id']):>12d} {r['familia']:>4s} {r['ma_info']:<22s}  "
                        f"PF:{r['pf_5k']:>5.2f}->{r['pf_7k']:>5.2f}->{fmt(r.get('pf_10k'),'>5.2f')}  "
                        f"DD:{r['maxdd_5k']:>4.1f}->{r['maxdd_7k']:>4.1f}%  "
                        f"Tr:{int(r['trades_5k']):>4d}->{int(r['trades_7k']):>4d}  "
                        f"PnL:{r['pnl_5k']:>+5.1f}->{r['pnl_7k']:>+5.1f}%{segs}")
        L.append("")
    
    # --- TOP 20 PF ---
    L.append(f"{'~'*130}")
    L.append(f"TOP 20 POR PF a 5k:")
    L.append(f"{'~'*130}")
    for _, r in pivot.sort_values('pf_5k', ascending=False).head(20).iterrows():
        p7 = "PASS" if r.get('pasa_7k', False) else "FAIL"
        seg_info = ""
        if has_seg:
            seg_info = f"  Consist:{r.get('seg_consistency',0):>4.0%} Worst:{fmt(r.get('seg_min_pnl'),'>+5.1f')}%"
        L.append(f"  {int(r['config_id']):>12d} {r['familia']:>4s} {r['ma_info']:<22s}  "
                f"PF:{r['pf_5k']:>5.2f}->{fmt(r.get('pf_7k'),'>5.2f')}  "
                f"DD:{r['maxdd_5k']:>4.1f}->{fmt(r.get('maxdd_7k'),'>4.1f')}%  "
                f"Tr:{int(r['trades_5k']):>4d}->{fmt(r.get('trades_7k'),'>4.0f')}  "
                f"PnL:{r['pnl_5k']:>+5.1f}->{fmt(r.get('pnl_7k'),'>+5.1f')}%{seg_info}  {p7}")
    
    # --- TOP 20 PnL ---
    L.append(f"\n{'~'*130}")
    L.append(f"TOP 20 POR PnL a 5k:")
    L.append(f"{'~'*130}")
    for _, r in pivot.sort_values('pnl_5k', ascending=False).head(20).iterrows():
        p7 = "PASS" if r.get('pasa_7k', False) else "FAIL"
        seg_info = ""
        if has_seg:
            seg_info = f"  Consist:{r.get('seg_consistency',0):>4.0%}"
        L.append(f"  {int(r['config_id']):>12d} {r['familia']:>4s} {r['ma_info']:<22s}  "
                f"PF:{r['pf_5k']:>5.2f}->{fmt(r.get('pf_7k'),'>5.2f')}  "
                f"PnL:{r['pnl_5k']:>+6.1f}->{fmt(r.get('pnl_7k'),'>+6.1f')}%{seg_info}  {p7}")
    
    # --- SEGMENTOS ---
    if has_seg:
        L.append(f"\n{'~'*130}")
        L.append(f"ANALISIS DE SEGMENTOS (5k cada uno):")
        L.append(f"{'~'*130}")
        L.append(f"  seg0=reciente  seg1=offset 5k (~208-416d atras)  seg2=offset 10k (~416-624d atras)\n")
        
        for sl in seg_labels:
            col = f'pnl_{sl}'
            avg = pivot[col].mean()
            pos = (pivot[col] > 0).sum()
            L.append(f"  {sl}: avg {avg:>+6.1f}% | {pos}/{len(pivot)} rentables ({100*pos/len(pivot):.0f}%)")
        
        L.append(f"\n  TOP 15 MAS CONSISTENTES (PF>1.5 en 5k):")
        consist = pivot[pivot['pf_5k'] > 1.5].sort_values(
            ['seg_consistency', 'seg_avg_pnl'], ascending=[False, False]).head(15)
        for _, r in consist.iterrows():
            p7 = "PASS" if r.get('pasa_7k', False) else "FAIL"
            segs = " ".join([f"{sl}:{r.get(f'pnl_{sl}',0):>+5.1f}%" for sl in seg_labels])
            L.append(f"    {int(r['config_id']):>12d} {r['familia']:>4s} {r['ma_info']:<22s}  "
                    f"PF:{r['pf_5k']:>5.2f} DD:{r['maxdd_5k']:>4.1f}% {int(r['trades_5k']):>4d}t  "
                    f"{segs}  Consist:{r['seg_consistency']:>4.0%}  {p7}")
        
        all_pos = pivot[pivot['seg_consistency'] == 1.0]
        L.append(f"\n  RENTABLES EN TODOS LOS SEGMENTOS: {len(all_pos)} configs")
        if len(all_pos) > 0:
            for _, r in all_pos.sort_values('pf_5k', ascending=False).head(20).iterrows():
                p7 = "PASS" if r.get('pasa_7k', False) else "FAIL"
                segs = " | ".join([f"{sl}:{r.get(f'pnl_{sl}',0):>+5.1f}%" for sl in seg_labels])
                L.append(f"    cfg={int(r['config_id']):<12d} Fam={r['familia']:<4s} "
                        f"PF5k={r['pf_5k']:.2f} DD={r['maxdd_5k']:.1f}% {int(r['trades_5k'])}t  "
                        f"{segs}  {p7}")
    
    # --- POR FAMILIA ---
    L.append(f"\n{'~'*130}")
    L.append(f"POR FAMILIA (mejor PF 7k):")
    L.append(f"{'~'*130}")
    scol = 'pf_7k' if has_7k else 'pf_5k'
    fb = pivot.sort_values(scol, ascending=False).drop_duplicates('familia')
    for _, r in fb.iterrows():
        p7 = "PASS" if r.get('pasa_7k', False) else "FAIL"
        line = f"  {r['familia']:<4s} {p7:>4s}  cfg={int(r['config_id']):<12d} {r['ma_info']:<22s}  "
        line += f"5k:PF={r['pf_5k']:.2f} DD={r['maxdd_5k']:.1f}% {int(r['trades_5k'])}t"
        if has_7k: line += f"  | 7k:PF={fmt(r.get('pf_7k'),'.2f')} DD={fmt(r.get('maxdd_7k'),'.1f')}%"
        if has_seg: line += f"  | Consist:{r.get('seg_consistency',0):.0%}"
        L.append(line)
    
    # --- DEGRADACION POR PRESET ---
    if has_7k and 'delta_pf_57' in pivot.columns:
        L.append(f"\n{'~'*130}")
        L.append(f"DEGRADACION POR PRESET (5k->7k):")
        L.append(f"{'~'*130}")
        for preset in sorted(pivot['ma_info'].unique()):
            sub = pivot[pivot['ma_info'] == preset]
            n = len(sub)
            dpf = sub['delta_pf_57'].mean()
            ddd = sub['delta_dd_57'].mean()
            np7 = sub['pasa_7k'].sum() if 'pasa_7k' in sub.columns else 0
            cs = sub['seg_consistency'].mean() if has_seg else 0
            L.append(f"  {preset:<28s}  {n:>3d} cfgs  dPF:{dpf:>+.2f}  dDD:{ddd:>+.1f}%  "
                    f"Pasan7k:{np7}/{n}" + (f"  Consist:{cs:.0%}" if has_seg else ""))
    
    # ═══ VEREDICTO AUTOMATICO ═══
    L.append(f"\n{'='*130}")
    L.append(f"VEREDICTO — SELECCION AUTOMATICA DE CANDIDATAS")
    L.append(f"{'='*130}")

    # Filtro minimo de trades: configs con <50 trades en 5k no son estadisticamente fiables
    MIN_TRADES_5K = 50
    pivot_filtered = pivot[pivot['trades_5k'] >= MIN_TRADES_5K]
    if len(pivot_filtered) == 0:
        L.append(f"\n  AVISO: Ninguna config tiene >= {MIN_TRADES_5K} trades en 5k. Usando todas sin filtro.")
        pivot_filtered = pivot
    else:
        n_dropped = len(pivot) - len(pivot_filtered)
        if n_dropped > 0:
            L.append(f"\n  Filtro: {n_dropped} configs descartadas por trades_5k < {MIN_TRADES_5K}")

    # Score compuesto: PF_7k * (1+consistencia) * log(trades) / (1 + DD/10)
    pivot_filtered = pivot_filtered.copy()
    pivot_filtered['composite'] = (
        pivot_filtered['pf_7k'].fillna(pivot_filtered['pf_5k']) *
        (1 + pivot_filtered['seg_consistency']) *
        np.log1p(pivot_filtered['trades_7k'].fillna(pivot_filtered['trades_5k'])) /
        (1 + pivot_filtered['maxdd_7k'].fillna(pivot_filtered['maxdd_5k']) / 10)
    )

    # Panorama (sobre pivot completo, sin filtrar)
    L.append(f"\n  Panorama general:")
    for sl in seg_labels:
        col = f'pnl_{sl}'
        avg = pivot[col].mean()
        pos = (pivot[col] > 0).sum()
        L.append(f"    {sl}: avg {avg:>+6.1f}% | {pos}/{len(pivot)} rentables ({100*pos/len(pivot):.0f}%)")

    n_pass_7k = pivot['pasa_7k'].sum() if 'pasa_7k' in pivot.columns else 0
    n_c100 = (pivot['seg_consistency'] == 1.0).sum() if has_seg else 0
    n_c67 = (pivot['seg_consistency'] >= 0.65).sum() if has_seg else 0
    L.append(f"    Pasan 7k: {n_pass_7k} | Consist 100%: {n_c100} | Consist 67%+: {n_c67}")

    # Calidad del activo
    quality = "EXCELENTE" if n_c100 >= 5 and n_pass_7k >= 5 else \
              "BUENO" if n_c67 >= 5 and n_pass_7k >= 3 else \
              "ACEPTABLE" if n_pass_7k >= 1 else \
              "POBRE"
    L.append(f"\n  Calidad del activo: {quality}")

    # Top 5 candidatas por score compuesto (filtradas por min trades)
    L.append(f"\n  TOP 5 CANDIDATAS (score = PF_7k * (1+consist) * log(trades) / (1+DD/10)):")
    L.append(f"  (filtro: trades_5k >= {MIN_TRADES_5K})\n")

    ranked = pivot_filtered.sort_values('composite', ascending=False).head(5)
    for i, (_, r) in enumerate(ranked.iterrows()):
        p7 = "SI" if r.get('pasa_7k', False) else "NO"
        segs = " | ".join([f"{sl}:{r.get(f'pnl_{sl}',0):+.1f}%" for sl in seg_labels])
        L.append(f"  #{i+1} cfg {int(r['config_id'])} (Fam {r['familia']}) — Score: {r['composite']:.1f}")
        L.append(f"     Preset: {r['ma_info']}")
        L.extend(format_config_block(r['config_id'], ma_info=r['ma_info'], symbol=symbol, lab=lab))
        L.append(f"     5k:  {int(r['trades_5k'])}t  PF {r['pf_5k']:.2f}  DD {r['maxdd_5k']:.1f}%  PnL {r['pnl_5k']:+.1f}%")
        L.append(f"     7k:  {int(r.get('trades_7k',0))}t  PF {r.get('pf_7k',0):.2f}  DD {r.get('maxdd_7k',0):.1f}%  PnL {r.get('pnl_7k',0):+.1f}%")
        L.append(f"     10k: {int(r.get('trades_10k',0))}t  PF {r.get('pf_10k',0):.2f}  DD {r.get('maxdd_10k',0):.1f}%  PnL {r.get('pnl_10k',0):+.1f}%")
        L.append(f"     Segmentos: {segs}")
        L.append(f"     Consistencia: {r['seg_consistency']:.0%}  |  Pasa 7k: {p7}")
        L.append("")

    # Elegida: la #1
    best = ranked.iloc[0]
    L.append(f"  {'*'*60}")
    L.append(f"  ELEGIDA: cfg {int(best['config_id'])} (Fam {best['familia']})")
    L.append(f"  Calidad activo: {quality}")
    L.append(f"  {'*'*60}")
    L.append("")

    # Metricas
    L.append(f"  METRICAS DE RENDIMIENTO")
    L.append(f"  {'─'*46}")
    L.append(f"  5k:  {int(best['trades_5k'])}t  PF {best['pf_5k']:.2f}  DD {best['maxdd_5k']:.1f}%  PnL {best['pnl_5k']:+.1f}%")
    L.append(f"  7k:  {int(best.get('trades_7k',0))}t  PF {best.get('pf_7k',0):.2f}  DD {best.get('maxdd_7k',0):.1f}%  PnL {best.get('pnl_7k',0):+.1f}%")
    L.append(f"  10k: {int(best.get('trades_10k',0))}t  PF {best.get('pf_10k',0):.2f}  DD {best.get('maxdd_10k',0):.1f}%  PnL {best.get('pnl_10k',0):+.1f}%")
    segs_best = " | ".join([f"{sl}:{best.get(f'pnl_{sl}',0):+.1f}%" for sl in seg_labels])
    L.append(f"  Segmentos: {segs_best}")
    L.append(f"  Consistencia: {best['seg_consistency']:.0%}  |  Pasa 7k: {'SI' if best.get('pasa_7k',False) else 'NO'}")
    L.append("")

    # Configuracion completa para el indicador
    L.extend(format_indicator_config(best['config_id'], best['ma_info'], symbol, lab, prefix="  "))

    # Razones
    reasons = []
    if best.get('pasa_7k', False):
        reasons.append(f"Pasa 7k con PF {best['pf_7k']:.2f} y DD {best['maxdd_7k']:.1f}%")
    if best['seg_consistency'] >= 1.0:
        reasons.append("Rentable en TODOS los segmentos temporales")
    elif best['seg_consistency'] >= 0.65:
        reasons.append(f"Rentable en {best['n_seg_pos']:.0f}/{best['n_seg_total']:.0f} segmentos")
    if best.get('trades_7k', 0) >= 100:
        reasons.append(f"{int(best['trades_7k'])} trades a 7k — confianza estadistica")
    elif best.get('trades_5k', 0) >= 80:
        reasons.append(f"{int(best['trades_5k'])} trades a 5k — confianza moderada")
    if best.get('maxdd_7k', 99) <= 7:
        reasons.append(f"DD muy bajo ({best['maxdd_7k']:.1f}%) — margen de seguridad amplio")
    for reason in reasons:
        L.append(f"    + {reason}")

    # Warning si no pasa 7k
    if not best.get('pasa_7k', False):
        L.append(f"\n  AVISO: La mejor candidata NO pasa criterio 7k.")
        L.append(f"  Operar solo con ventana 5k y reciclaje obligatorio.")

    L.append(f"  {'*'*60}")
    L.append(f"\n{'='*130}")
    
    txt = '\n'.join(L)
    rf = os.path.join(output_dir, f'validacion_gemas_{sc}.txt')
    with open(rf, 'w', encoding='utf-8') as f:
        f.write(txt)
    
    print(f"\n  CSV crudo:  {csv_f}")
    print(f"  CSV pivot:  {piv_f}")
    print(f"  Resumen:    {rf}")
    print(f"\n{txt}")


# -------------------------------------------------------------------
# 6. MAIN
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Validador de gemas v3 (motor lab)')
    parser.add_argument('symbol', help='Simbolo (ej: BTC/USDT)')
    parser.add_argument('gems_csv', help='CSV de gemas')
    parser.add_argument('--segments', type=int, default=DEFAULT_SEGMENTS,
                       help=f'Segmentos aislados de 5k (default: {DEFAULT_SEGMENTS}, 0=off)')
    parser.add_argument('--max-configs', type=int, default=0, help='Limitar configs (0=todas)')
    parser.add_argument('--lab', default='lab_historico_numba_v8_3.py', help='Archivo del lab')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  VALIDADOR DE GEMAS v3 (motor lab)")
    print(f"  {args.symbol}")
    print(f"  Ventanas acumulativas: {ACUM_WINDOWS}")
    print(f"  Segmentos: {args.segments} x {WINDOW_SIZE}")
    print(f"{'='*60}")
    
    # Importar lab
    print(f"\n  Importando {args.lab}...")
    t0 = time.time()
    lab = import_lab(args.lab)
    print(f"  Lab importado en {time.time()-t0:.1f}s (Numba compilando...)")
    
    # Ejecutar
    df = run_gem_validation(args.symbol, args.gems_csv, args.segments, args.max_configs, lab)
    
    if len(df) > 0:
        pivot = build_pivot(df, args.segments)
        generate_report(df, pivot, args.symbol, lab=lab)
    else:
        print("  Sin resultados")
    
    print(f"\n  Completado.\n")


if __name__ == '__main__':
    main()
