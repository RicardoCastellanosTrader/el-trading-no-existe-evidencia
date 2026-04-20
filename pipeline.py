#!/usr/bin/env python3
"""
pipeline.py - Pipeline unificado de optimizacion de trading

Automatiza el flujo completo:
  Lab Lite -> Lab Historico -> Extractor Gemas -> Validador Batch -> Walk-Forward

Uso:
    python pipeline.py
    python pipeline.py --symbols BNB/USDT,BTC/USDT,ETH/USDT
    python pipeline.py --symbols BNB/USDT --top-n 7 --diversity
    python pipeline.py --output-dir output/run_20260306
    python pipeline.py --phase lite          # Solo fase 1
    python pipeline.py --phase lab           # Fases 1-2
    python pipeline.py --phase extractor     # Fases 1-3
    python pipeline.py --resume              # Retomar ejecucion previa

Resume automatico: detecta archivos existentes y salta fases completadas.
"""

import os
import sys
import time
import glob
import argparse
import importlib.util
import multiprocessing
from datetime import datetime

import pandas as pd
import numpy as np


# ============================================
# CONFIGURACION POR DEFECTO
# ============================================

DEFAULT_SYMBOLS = [
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

DEFAULT_CONFIG = {
    # Lab Lite
    "lite_total_candles": 5000,
    "lite_top_n": 7,
    "lite_diversity": True,

    # Lab Historico
    "lab_total_candles": 5000,
    "hyst_values": [0.0, 0.5],

    # Risk (fijos, configurables)
    "sl_percent": 3.0,
    "sl_emergency_percent": 5.0,
    "ts_percent": 0.5,
    "cooldown_bars": 1,
    "commission": 0.10,

    # Extractor
    "extractor_top": 15,

    # Validador
    "val_segments": 3,
    "val_acum_windows": [5000, 7000, 10000],

    # Walk-Forward
    "wf_opt_7k": 7000,
    "wf_opt_5k": 5000,
    "wf_fwd_size": 1000,
    "wf_step": 1000,
    "wf_total_candles": 16700,

    # Optimizaciones
    "use_cache": True,
    "workers": 1,
}

# Fases disponibles y su orden
PHASE_ORDER = ["lite", "lab", "extractor", "validador", "walkforward"]


# ============================================
# IMPORTACION DE MODULOS
# ============================================

_module_cache = {}

def _import_module(filename):
    """Importa un archivo Python como modulo sin ejecutar __main__."""
    if filename in _module_cache:
        return _module_cache[filename]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        print(f"ERROR: {path} no encontrado")
        sys.exit(1)

    name = os.path.splitext(filename)[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _module_cache[filename] = mod
    return mod


def import_lite():
    return _import_module("lab_lite_zonas_v5e.py")


def import_lab():
    return _import_module("lab_historico_numba_v8_3.py")


def import_extractor():
    return _import_module("extractor_gemas.py")


def import_validador():
    return _import_module("validador_batch_v3.py")


def import_walkforward():
    return _import_module("walk_forward_v1.py")


# ============================================
# UTILIDADES
# ============================================

def load_presets_from_csv(csv_path):
    """Carga presets desde CSV del lab lite. Retorna lista de tuplas y lista de cluster_ids."""
    df = pd.read_csv(csv_path)
    presets = []
    cluster_ids = []
    for _, row in df.iterrows():
        preset = (
            str(row['fast_type']), int(row['fast_period']),
            float(row['fast_p1']), float(row['fast_p2']),
            str(row['slow_type']), int(row['slow_period']),
            float(row['slow_p1']), float(row['slow_p2']),
            str(row['trend_type']), int(row['trend_period']),
            float(row['trend_p1']), float(row['trend_p2']),
        )
        presets.append(preset)
        # cluster_id: -1 = global, 0/1/2 = cluster specialist
        cid = -1
        if 'cluster_id' in row.index:
            try:
                cid = int(row['cluster_id'])
            except (ValueError, TypeError):
                cid = -1
        cluster_ids.append(cid)
    return presets, cluster_ids


def count_variant_csvs(sym_dir, sym_clean):
    """Cuenta CSVs de variantes del lab historico existentes."""
    # Nuevo patrón con cluster_id
    pattern_new = os.path.join(sym_dir, f"full_{sym_clean}_v*_H*_C*.csv")
    n = len(glob.glob(pattern_new))
    if n > 0:
        return n
    # Fallback: patrón legacy sin cluster_id
    pattern_legacy = os.path.join(sym_dir, f"full_{sym_clean}_v*_H*.csv")
    return len(glob.glob(pattern_legacy))


def sym_clean(symbol):
    return symbol.replace("/", "")


# ============================================
# FASE 1: LAB LITE
# ============================================

def phase_lite(symbol, config, sym_dir, lite):
    """Ejecuta Lab Lite para un simbolo. Retorna (presets, cluster_ids) o (None, None)."""
    sc = sym_clean(symbol)
    csv_path = os.path.join(sym_dir, f"presets_{sc}.csv")

    # Resume
    if os.path.exists(csv_path):
        presets, cluster_ids = load_presets_from_csv(csv_path)
        print(f"  [LITE] Resume -> {len(presets)} presets de {csv_path}")
        return presets, cluster_ids

    # Configurar modulo
    lite.TOTAL_CANDLES = config["lite_total_candles"]
    lite.OUTPUT_DIR = sym_dir
    lite.TOP_N_PRESETS = config["lite_top_n"]
    lite.DIVERSITY_MODE = config["lite_diversity"]
    lite.COMMISSION_ROUND_TRIP = config["commission"]

    # Ejecutar
    result = lite.process_symbol(symbol)
    if not result or not result.get('selected_presets'):
        print(f"  [LITE] Sin resultados para {symbol}")
        return None, None

    presets = result['selected_presets']
    # Leer cluster_ids del CSV generado (process_symbol ya lo escribió)
    cluster_ids = [-1] * len(presets)
    if os.path.exists(csv_path):
        _, cluster_ids = load_presets_from_csv(csv_path)
    print(f"  [LITE] OK -> {len(presets)} presets seleccionados")
    return presets, cluster_ids


# ============================================
# FASE 2: LAB HISTORICO
# ============================================

def phase_lab(symbol, presets, cluster_ids, config, sym_dir, lab):
    """Ejecuta Lab Historico para un simbolo con presets dados. Retorna True/False."""
    sc = sym_clean(symbol)
    n_expected = len(presets) * len(config["hyst_values"])

    # Resume: si todos los CSVs existen, saltar
    n_existing = count_variant_csvs(sym_dir, sc)
    if n_existing >= n_expected:
        print(f"  [LAB] Resume -> {n_existing}/{n_expected} variantes completas")
        return True

    if n_existing > 0:
        print(f"  [LAB] Resume parcial -> {n_existing}/{n_expected} completas, continuando...")

    # Configurar modulo
    lab.SYMBOL_ZONE_PRESETS[symbol] = presets
    lab.PRESET_CLUSTER_IDS[symbol] = cluster_ids
    lab.OUTPUT_DIR = sym_dir
    lab.TOTAL_CANDLES = config["lab_total_candles"]
    lab.HYST_VALUES = config["hyst_values"]
    lab.SL_PERCENT = config["sl_percent"]
    lab.SL_EMERGENCY_PERCENT = config["sl_emergency_percent"]
    lab.TS_PERCENT = config["ts_percent"]
    lab.COOLDOWN_BARS = config["cooldown_bars"]
    lab.COMMISSION_ROUND_TRIP = config["commission"]

    # Ejecutar (el resume por variante lo hace _process_one_variant)
    try:
        result = lab.process_symbol(symbol)
        if result:
            print(f"  [LAB] OK -> {n_expected} variantes procesadas")
            return True
        else:
            print(f"  [LAB] Sin resultados para {symbol}")
            return False
    except Exception as e:
        print(f"  [LAB] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# FASE 3: EXTRACTOR DE GEMAS
# ============================================

def phase_extractor(symbol, config, sym_dir, extractor):
    """Ejecuta Extractor de Gemas. Retorna path al CSV de gemas o None."""
    sc = sym_clean(symbol)
    gems_csv = os.path.join(sym_dir, f"gemas_{sc}.csv")

    # Resume
    if os.path.exists(gems_csv):
        n_gems = len(pd.read_csv(gems_csv))
        print(f"  [GEMAS] Resume -> {n_gems} gemas en {gems_csv}")
        return gems_csv

    # Verificar que hay CSVs del lab (nuevo patrón con _C*, fallback a legacy)
    csv_pattern = os.path.join(sym_dir, f"full_{sc}_v*_H*_C*.csv")
    lab_csvs = sorted(glob.glob(csv_pattern))
    if not lab_csvs:
        csv_pattern = os.path.join(sym_dir, f"full_{sc}_v*_H*.csv")
        lab_csvs = sorted(glob.glob(csv_pattern))
    if not lab_csvs:
        print(f"  [GEMAS] Sin CSVs del lab en {sym_dir}")
        return None

    rank_pattern = os.path.join(sym_dir, f"ranking_{sc}_v*_H*_C*.txt")
    lab_ranks = sorted(glob.glob(rank_pattern))
    if not lab_ranks:
        rank_pattern = os.path.join(sym_dir, f"ranking_{sc}_v*_H*.txt")
        lab_ranks = sorted(glob.glob(rank_pattern))

    print(f"  [GEMAS] Procesando {len(lab_csvs)} CSVs...")

    # Cargar datos
    combined = extractor.load_all_presets(lab_csvs, lab_ranks)
    if len(combined) == 0:
        print(f"  [GEMAS] Sin datos en CSVs")
        return None

    # Filtro de validacion
    valid = extractor.apply_validation_filter(combined)
    if len(valid) == 0:
        print(f"  [GEMAS] Ninguna config pasa filtro de validacion")
        return None

    # Calcular structural_score
    valid = extractor.compute_structural_score(valid)

    # Extraer gemas
    top_n = config["extractor_top"]
    gem_ids, gem_criteria, config_presets = extractor.extract_gems(valid, top_n)
    if not gem_ids:
        print(f"  [GEMAS] Sin gemas extraidas")
        return None

    # Construir tabla
    gems_best = extractor.build_gem_table(valid, gem_ids, gem_criteria, config_presets)

    # Filtro de meseta (robustez paramétrica)
    print(f"  [GEMAS] Aplicando filtro de meseta...")
    gems_best = extractor.apply_plateau_filter(gems_best, combined)

    gems_best = extractor.assign_families(gems_best)

    # Guardar CSV
    gems_best.to_csv(gems_csv, index=False)
    print(f"  [GEMAS] {len(gems_best)} gemas -> {gems_csv}")

    # Generar resumen
    extractor.generate_summary(gems_best, sc, sym_dir)

    return gems_csv


# ============================================
# FASE 4: VALIDADOR BATCH
# ============================================

def phase_validador(symbol, gems_csv, config, sym_dir, validador, lab):
    """Ejecuta Validador Batch. Retorna True/False."""
    sc = sym_clean(symbol)
    report_path = os.path.join(sym_dir, f"validacion_gemas_{sc}.txt")

    # Resume
    if os.path.exists(report_path):
        print(f"  [VALID] Resume -> reporte existe en {report_path}")
        return True

    # Verificar que hay gemas
    if not os.path.exists(gems_csv):
        print(f"  [VALID] Sin CSV de gemas")
        return False

    gems = pd.read_csv(gems_csv)
    if len(gems) == 0:
        print(f"  [VALID] CSV de gemas vacio")
        return False

    print(f"  [VALID] Validando {len(gems)} gemas...")

    # Configurar ventanas del validador
    validador.ACUM_WINDOWS = config["val_acum_windows"]

    # El lab ya tiene los presets seteados (de phase_lab)
    # Pero si estamos en resume, necesitamos cargarlos
    presets_csv = os.path.join(sym_dir, f"presets_{sc}.csv")
    if os.path.exists(presets_csv):
        presets, cluster_ids = load_presets_from_csv(presets_csv)
        lab.SYMBOL_ZONE_PRESETS[symbol] = presets
        lab.PRESET_CLUSTER_IDS[symbol] = cluster_ids

    # Ejecutar validacion
    try:
        segments = config["val_segments"]
        df = validador.run_gem_validation(symbol, gems_csv, segments, 0, lab)

        if len(df) == 0:
            print(f"  [VALID] Sin resultados")
            return False

        pivot = validador.build_pivot(df, segments)
        validador.generate_report(df, pivot, symbol, output_dir=sym_dir, lab=lab)

        print(f"  [VALID] OK -> reporte en {report_path}")
        return True

    except Exception as e:
        print(f"  [VALID] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# FASE 5: WALK-FORWARD SIMULADO
# ============================================

def phase_walkforward(symbol, config, sym_dir, walkforward, lab):
    """Ejecuta Walk-Forward Simulado. Retorna True/False."""
    sc = sym_clean(symbol)
    csv_path = os.path.join(sym_dir, f"walkforward_{sc}.csv")

    # Resume
    if os.path.exists(csv_path):
        print(f"  [WF] Resume -> resultados en {csv_path}")
        return True

    # Verificar que hay gemas
    gems_csv = os.path.join(sym_dir, f"gemas_{sc}.csv")
    if not os.path.exists(gems_csv):
        print(f"  [WF] Sin CSV de gemas")
        return False

    # Cargar presets en el lab
    presets_csv = os.path.join(sym_dir, f"presets_{sc}.csv")
    if os.path.exists(presets_csv):
        presets, cluster_ids = load_presets_from_csv(presets_csv)
        lab.SYMBOL_ZONE_PRESETS[symbol] = presets
        lab.PRESET_CLUSTER_IDS[symbol] = cluster_ids

    print(f"  [WF] Ejecutando walk-forward...")

    try:
        results_df, timestamps = walkforward.run_walk_forward(
            symbol, sym_dir, lab,
            config["wf_opt_7k"], config["wf_opt_5k"],
            config["wf_fwd_size"], config["wf_step"],
            config["wf_total_candles"]
        )

        if len(results_df) == 0:
            print(f"  [WF] Sin resultados")
            return False

        analysis = walkforward.analyze_correlations(results_df, symbol, sym_dir, timestamps)
        walkforward.save_results(results_df, analysis, symbol, sym_dir)

        print(f"  [WF] OK -> {csv_path}")
        return True

    except Exception as e:
        print(f"  [WF] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# FASE WF-OFFSET: EVALUACION FORWARD
# ============================================

def phase_wf_offset_forward(symbol, config, sym_dir, lab, walkforward):
    """Evalua configs candidatas en las N velas ocultas por wf-offset.
    Delega a walk_forward_v1.run_wf_offset() para reutilizar toda la logica
    de seleccion A/B, metricas h1/h2, correlaciones y veredictos.
    Retorna True/False."""
    import data_cache

    sc = sym_clean(symbol)
    wf_csv = os.path.join(sym_dir, f"walkforward_{sc}.csv")

    # Resume
    if os.path.exists(wf_csv):
        print(f"  [WF-OFFSET] Resume -> {wf_csv}")
        return True

    offset_n = config["wf_offset"]

    # Cargar presets en el lab
    presets_csv = os.path.join(sym_dir, f"presets_{sc}.csv")
    if os.path.exists(presets_csv):
        presets, cluster_ids = load_presets_from_csv(presets_csv)
        lab.SYMBOL_ZONE_PRESETS[symbol] = presets
        lab.PRESET_CLUSTER_IDS[symbol] = cluster_ids

    # Obtener datos COMPLETOS (sin trim) — necesitamos las velas forward
    val_candles = max(10000, 5000 * config["val_segments"]) + 500
    max_candles = max(config["lite_total_candles"], config["lab_total_candles"], val_candles) + 1000 + offset_n
    df_full = data_cache.get_full_dataframe(symbol, "1h", max_candles)
    if df_full is None or len(df_full) < offset_n + 1000:
        print(f"  [WF-OFFSET] Datos insuficientes ({len(df_full) if df_full is not None else 0})")
        return False

    n_total = len(df_full)
    fwd_start = n_total - offset_n
    fwd_end = n_total

    print(f"  [WF-OFFSET] Datos: {n_total} velas totales, forward: [{fwd_start}:{fwd_end}] = {offset_n} velas")
    print(f"  [WF-OFFSET] Delegando a walk_forward_v1.run_wf_offset()...")

    try:
        results_df, timestamps = walkforward.run_wf_offset(
            symbol, sym_dir, lab, df_full, fwd_start, fwd_end, config
        )

        if len(results_df) == 0:
            print(f"  [WF-OFFSET] Sin resultados forward")
            return False

        analysis = walkforward.analyze_correlations(results_df, symbol, sym_dir, timestamps)
        walkforward.save_results(results_df, analysis, symbol, sym_dir)

        print(f"  [WF-OFFSET] OK -> {wf_csv}")
        return True

    except Exception as e:
        print(f"  [WF-OFFSET] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# PIPELINE PRINCIPAL
# ============================================

def _process_single_symbol(symbol, idx, total, config, output_dir, phases_to_run):
    """Procesa un simbolo completo (todas las fases). Usado por workers."""
    # Cada worker importa sus propios modulos (necesario para multiprocessing)
    lite = _import_module("lab_lite_zonas_v5e.py") if "lite" in phases_to_run else None
    lab = _import_module("lab_historico_numba_v8_3.py") if any(p in phases_to_run for p in ["lab", "validador", "walkforward"]) or config.get("wf_offset") else None
    extractor = _import_module("extractor_gemas.py") if "extractor" in phases_to_run else None
    validador = _import_module("validador_batch_v3.py") if "validador" in phases_to_run else None
    walkforward = _import_module("walk_forward_v1.py") if ("walkforward" in phases_to_run or config.get("wf_offset")) else None

    # Aplicar cache si esta activado
    if config.get("use_cache", True):
        import data_cache
        data_cache.CACHE_DIR = config.get("_cache_dir", "data_cache")
        val_candles = max(10000, 5000 * config["val_segments"]) + 500 if "validador" in phases_to_run else 0
        max_candles = max(config["lite_total_candles"], config["lab_total_candles"], val_candles) + 1000
        data_cache.patch_modules(lite, lab, config["lite_total_candles"], config["lab_total_candles"])
        # Propagar trim para wf-offset
        if config.get("wf_offset"):
            data_cache.set_trim_tail(config["wf_offset"])

    sc = sym_clean(symbol)
    sym_dir = os.path.join(output_dir, sc)
    os.makedirs(sym_dir, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"[{idx}/{total}] {symbol}")
    print(f"{'='*70}")

    sym_result = {"symbol": symbol, "phases": {}}
    t_sym = time.time()

    # Fase 1: Lab Lite
    presets = None
    cluster_ids = None
    if "lite" in phases_to_run:
        t_phase = time.time()
        presets, cluster_ids = phase_lite(symbol, config, sym_dir, lite)
        sym_result["phases"]["lite"] = {
            "ok": presets is not None,
            "n_presets": len(presets) if presets else 0,
            "time": time.time() - t_phase,
        }
        if not presets:
            print(f"  SKIP -> sin presets, saltando simbolo")
            sym_result["total_time"] = time.time() - t_sym
            return symbol, sym_result
    else:
        presets_csv = os.path.join(sym_dir, f"presets_{sc}.csv")
        if os.path.exists(presets_csv):
            presets, cluster_ids = load_presets_from_csv(presets_csv)

    # Fase 2: Lab Historico
    if "lab" in phases_to_run:
        if not presets:
            print(f"  SKIP -> sin presets para lab historico")
            sym_result["total_time"] = time.time() - t_sym
            return symbol, sym_result
        if cluster_ids is None:
            cluster_ids = [-1] * len(presets)
        t_phase = time.time()
        lab_ok = phase_lab(symbol, presets, cluster_ids, config, sym_dir, lab)
        sym_result["phases"]["lab"] = {
            "ok": lab_ok,
            "time": time.time() - t_phase,
        }
        if not lab_ok:
            print(f"  SKIP -> lab historico fallo")
            sym_result["total_time"] = time.time() - t_sym
            return symbol, sym_result

    # Fase 3: Extractor
    gems_csv = None
    if "extractor" in phases_to_run:
        t_phase = time.time()
        gems_csv = phase_extractor(symbol, config, sym_dir, extractor)
        sym_result["phases"]["extractor"] = {
            "ok": gems_csv is not None,
            "time": time.time() - t_phase,
        }
        if not gems_csv:
            print(f"  SKIP -> extractor sin gemas")
            sym_result["total_time"] = time.time() - t_sym
            return symbol, sym_result
    else:
        gems_csv = os.path.join(sym_dir, f"gemas_{sc}.csv")
        if not os.path.exists(gems_csv):
            gems_csv = None

    # Fase 4: Validador
    if "validador" in phases_to_run:
        if not gems_csv:
            print(f"  SKIP -> sin gemas para validador")
            sym_result["total_time"] = time.time() - t_sym
            return symbol, sym_result
        t_phase = time.time()
        val_ok = phase_validador(symbol, gems_csv, config, sym_dir, validador, lab)
        sym_result["phases"]["validador"] = {
            "ok": val_ok,
            "time": time.time() - t_phase,
        }

    # Fase 5: Walk-Forward
    if "walkforward" in phases_to_run:
        if config.get("wf_offset"):
            # Modo offset: ejecutar walk-forward sobre velas ocultas
            t_phase = time.time()
            wfo_ok = phase_wf_offset_forward(symbol, config, sym_dir, lab, walkforward)
            sym_result["phases"]["walkforward"] = {
                "ok": wfo_ok,
                "time": time.time() - t_phase,
            }
        else:
            # Modo normal: ventanas deslizantes
            gems_csv_wf = gems_csv or os.path.join(sym_dir, f"gemas_{sc}.csv")
            if not os.path.exists(gems_csv_wf):
                print(f"  SKIP -> sin gemas para walk-forward")
                sym_result["total_time"] = time.time() - t_sym
                return symbol, sym_result
            t_phase = time.time()
            wf_ok = phase_walkforward(symbol, config, sym_dir, walkforward, lab)
            sym_result["phases"]["walkforward"] = {
                "ok": wf_ok,
                "time": time.time() - t_phase,
            }

    sym_result["total_time"] = time.time() - t_sym

    # Resumen del simbolo
    status = " | ".join(
        f"{p}:{'OK' if d['ok'] else 'FAIL'}"
        for p, d in sym_result["phases"].items()
    )
    print(f"  >> {symbol} [{status}] ({sym_result['total_time']:.1f}s)")

    return symbol, sym_result


def _worker_init(config, output_dir, phases_to_run):
    """Inicializador para workers de multiprocessing."""
    global _worker_config, _worker_output_dir, _worker_phases
    _worker_config = config
    _worker_output_dir = output_dir
    _worker_phases = phases_to_run


def _worker_task(args):
    """Tarea para un worker de multiprocessing."""
    symbol, idx, total = args
    try:
        return _process_single_symbol(
            symbol, idx, total, _worker_config, _worker_output_dir, _worker_phases)
    except Exception as e:
        import traceback
        print(f"  ERROR en {symbol}: {e}")
        traceback.print_exc()
        return symbol, {"symbol": symbol, "phases": {}, "error": str(e), "total_time": 0}


def run_pipeline(symbols, config, output_dir, last_phase="validador"):
    """Ejecuta el pipeline completo para los simbolos dados."""

    os.makedirs(output_dir, exist_ok=True)

    # Determinar fases a ejecutar
    phase_idx = PHASE_ORDER.index(last_phase)
    phases_to_run = PHASE_ORDER[:phase_idx + 1]
    print(f"Fases: {' -> '.join(phases_to_run)}")

    # Guardar config
    _save_config(config, output_dir)

    # Cache: pre-descargar datos para todos los simbolos
    wf_offset = config.get("wf_offset", 0)
    if wf_offset and not config.get("use_cache", True):
        print("AVISO: --wf-offset requiere cache. Activando cache automaticamente.")
        config["use_cache"] = True
    use_cache = config.get("use_cache", True)
    if use_cache:
        import data_cache
        # Cache compartido entre runs (al nivel del proyecto, no dentro de output)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "data_cache")
        data_cache.CACHE_DIR = cache_dir
        config["_cache_dir"] = cache_dir

        # Incluir necesidades del validador y walk-forward
        val_candles = max(10000, 5000 * config["val_segments"]) + 500 if "validador" in phases_to_run else 0
        wf_candles = config["wf_total_candles"] if "walkforward" in phases_to_run else 0
        # Si wf-offset activo, necesitamos N velas extra en el prefetch
        offset_extra = wf_offset if wf_offset else 0
        max_candles = max(config["lite_total_candles"], config["lab_total_candles"], val_candles, wf_candles) + 1000 + offset_extra
        data_cache.prefetch_symbols(symbols, "1h", max_candles)

        # Activar trim si wf-offset
        if wf_offset:
            data_cache.set_trim_tail(wf_offset)

    workers = config.get("workers", 1)
    t_global = time.time()

    if workers > 1 and len(symbols) > 1:
        # Multiprocessing
        print(f"\nMultiprocessing: {workers} workers para {len(symbols)} simbolos")
        tasks = [(s, i, len(symbols)) for i, s in enumerate(symbols, 1)]

        # Limpiar cache de modulos para que cada worker importe fresco
        global _module_cache
        _module_cache = {}

        with multiprocessing.Pool(
            processes=workers,
            initializer=_worker_init,
            initargs=(config, output_dir, phases_to_run)
        ) as pool:
            result_list = pool.map(_worker_task, tasks)

        results = dict(result_list)
    else:
        # Secuencial: importar una vez y procesar todos
        results = {}
        for i, symbol in enumerate(symbols, 1):
            sym, sym_result = _process_single_symbol(
                symbol, i, len(symbols), config, output_dir, phases_to_run)
            results[sym] = sym_result

    # Resumen global
    elapsed = time.time() - t_global
    _print_summary(results, symbols, elapsed, output_dir)

    return results


def _save_config(config, output_dir):
    """Guarda configuracion usada en el directorio de salida."""
    import json
    config_path = os.path.join(output_dir, "pipeline_config.json")
    # Solo guardar si no existe (no sobreescribir config de ejecucion previa)
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"Config guardada: {config_path}")


def _print_summary(results, symbols, elapsed, output_dir):
    """Imprime resumen global del pipeline."""
    print(f"\n{'='*70}")
    print(f"PIPELINE COMPLETADO")
    print(f"{'='*70}")
    print(f"Tiempo total: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    print(f"Directorio: {output_dir}")
    print(f"Simbolos: {len(symbols)}")

    # Contadores por fase
    all_phases = list(PHASE_ORDER)
    for phase in all_phases:
        ok = sum(1 for r in results.values()
                 if r["phases"].get(phase, {}).get("ok", False))
        total = sum(1 for r in results.values()
                    if phase in r["phases"])
        if total > 0:
            print(f"  {phase:<12s}: {ok}/{total} OK")

    # Simbolos fallidos
    failed = [s for s, r in results.items()
              if any(not d.get("ok", True) for d in r["phases"].values())]
    if failed:
        print(f"\nFallidos:")
        for s in failed:
            phases = results[s]["phases"]
            fails = [p for p, d in phases.items() if not d.get("ok", True)]
            print(f"  {s}: {', '.join(fails)}")

    # Simbolos completados (todas las fases OK)
    completed = [s for s, r in results.items()
                 if all(d.get("ok", True) for d in r["phases"].values())
                 and len(r["phases"]) > 0]
    if completed:
        print(f"\nCompletados ({len(completed)}/{len(symbols)}):")
        for s in completed:
            t = results[s].get("total_time", 0)
            print(f"  {s} ({t:.1f}s)")


# ============================================
# CLI
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Pipeline unificado de optimizacion de trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python pipeline.py                                    # Todos los simbolos, pipeline completo
  python pipeline.py --symbols BNB/USDT,BTC/USDT       # Solo estos simbolos
  python pipeline.py --phase lite                       # Solo lab lite
  python pipeline.py --phase lab                        # Hasta lab historico
  python pipeline.py --top-n 5 --no-diversity           # Top 5 sin diversidad
  python pipeline.py --output-dir output/test           # Directorio custom
  python pipeline.py --workers 4                        # 4 simbolos en paralelo
  python pipeline.py --no-cache                         # Sin cache local
        """
    )

    parser.add_argument('--symbols', type=str, default=None,
                       help='Simbolos separados por coma (default: 48 principales)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Directorio de salida (default: output/YYYYMMDD_HHMMSS)')
    parser.add_argument('--phase', type=str, default='validador',
                       choices=PHASE_ORDER,
                       help='Ultima fase a ejecutar (default: validador = pipeline completo)')

    # Lab Lite
    parser.add_argument('--top-n', type=int, default=None,
                       help=f'Presets a seleccionar por simbolo (default: {DEFAULT_CONFIG["lite_top_n"]})')
    parser.add_argument('--no-diversity', action='store_true',
                       help='Desactivar diversidad de familias en lab lite')
    parser.add_argument('--lite-candles', type=int, default=None,
                       help=f'Velas para lab lite (default: {DEFAULT_CONFIG["lite_total_candles"]})')

    # Lab Historico
    parser.add_argument('--lab-candles', type=int, default=None,
                       help=f'Velas para lab historico (default: {DEFAULT_CONFIG["lab_total_candles"]})')
    parser.add_argument('--hyst', type=str, default=None,
                       help='Valores de histeresis separados por coma (default: 0.0,0.5)')

    # Risk
    parser.add_argument('--sl', type=float, default=None,
                       help=f'SL fijo %% (default: {DEFAULT_CONFIG["sl_percent"]})')
    parser.add_argument('--sl-emergency', type=float, default=None,
                       help=f'SL emergencia %% (default: {DEFAULT_CONFIG["sl_emergency_percent"]})')
    parser.add_argument('--ts', type=float, default=None,
                       help=f'Trailing stop %% (default: {DEFAULT_CONFIG["ts_percent"]})')
    parser.add_argument('--commission', type=float, default=None,
                       help=f'Comision round-trip %% (default: {DEFAULT_CONFIG["commission"]})')

    # Extractor
    parser.add_argument('--extractor-top', type=int, default=None,
                       help=f'Top N por criterio en extractor (default: {DEFAULT_CONFIG["extractor_top"]})')

    # Validador
    parser.add_argument('--val-segments', type=int, default=None,
                       help=f'Segmentos de validacion (default: {DEFAULT_CONFIG["val_segments"]})')

    # Walk-Forward
    parser.add_argument('--wf-fwd-size', type=int, default=None,
                       help=f'Ventana forward en bars (default: {DEFAULT_CONFIG["wf_fwd_size"]})')
    parser.add_argument('--wf-total-candles', type=int, default=None,
                       help=f'Total candles para WF (default: {DEFAULT_CONFIG["wf_total_candles"]})')

    # WF-Offset (modo experimental)
    parser.add_argument('--wf-offset', type=int, default=None,
                       help='Offset temporal: recortar N velas del final, pipeline sobre datos recortados, '
                            'evaluar forward en las N velas ocultas. Experimental.')

    # Optimizaciones
    parser.add_argument('--workers', type=int, default=None,
                       help='Workers paralelos para simbolos (default: 1, secuencial)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Desactivar cache local de datos de Binance')

    return parser.parse_args()


def build_config(args):
    """Construye config desde argumentos CLI + defaults."""
    config = dict(DEFAULT_CONFIG)

    if args.top_n is not None:
        config["lite_top_n"] = args.top_n
    if args.no_diversity:
        config["lite_diversity"] = False
    if args.lite_candles is not None:
        config["lite_total_candles"] = args.lite_candles
    if args.lab_candles is not None:
        config["lab_total_candles"] = args.lab_candles
    if args.hyst is not None:
        config["hyst_values"] = [float(x) for x in args.hyst.split(",")]
    if args.sl is not None:
        config["sl_percent"] = args.sl
    if args.sl_emergency is not None:
        config["sl_emergency_percent"] = args.sl_emergency
    if args.ts is not None:
        config["ts_percent"] = args.ts
    if args.commission is not None:
        config["commission"] = args.commission
    if args.extractor_top is not None:
        config["extractor_top"] = args.extractor_top
    if args.val_segments is not None:
        config["val_segments"] = args.val_segments
    if args.workers is not None:
        config["workers"] = args.workers
    if args.no_cache:
        config["use_cache"] = False
    if args.wf_fwd_size is not None:
        config["wf_fwd_size"] = args.wf_fwd_size
        config["wf_step"] = args.wf_fwd_size  # step = fwd_size por defecto
    if args.wf_total_candles is not None:
        config["wf_total_candles"] = args.wf_total_candles

    if args.wf_offset is not None:
        config["wf_offset"] = args.wf_offset

    return config


def main():
    args = parse_args()
    config = build_config(args)

    # Simbolos
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    else:
        symbols = list(DEFAULT_SYMBOLS)

    # Output dir
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", timestamp)

    # Banner
    n_variants = config["lite_top_n"] * len(config["hyst_values"])
    print("=" * 70)
    print("PIPELINE DE OPTIMIZACION DE TRADING")
    print("=" * 70)
    print(f"Simbolos:     {len(symbols)}")
    print(f"Top N:        {config['lite_top_n']} presets × {len(config['hyst_values'])} hyst = {n_variants} variantes")
    print(f"Diversidad:   {'SI' if config['lite_diversity'] else 'NO'}")
    print(f"Fases:        hasta {args.phase}")
    print(f"Output:       {output_dir}")
    print(f"SL: {config['sl_percent']}% | SL Emerg: {config['sl_emergency_percent']}% "
          f"| TS: {config['ts_percent']}% | Comision: {config['commission']}%")
    print(f"Cache:        {'SI' if config.get('use_cache', True) else 'NO'}")
    print(f"Workers:      {config.get('workers', 1)}")
    if config.get('wf_offset'):
        print(f"WF-Offset:    {config['wf_offset']} velas ({config['wf_offset']/24:.0f} dias) — MODO EXPERIMENTAL")
    print("=" * 70)

    run_pipeline(symbols, config, output_dir, last_phase=args.phase)


if __name__ == "__main__":
    main()
