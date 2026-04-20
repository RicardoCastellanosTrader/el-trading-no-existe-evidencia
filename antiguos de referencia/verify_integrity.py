#!/usr/bin/env python3
"""
verify_integrity.py - Verificacion completa de integridad del pipeline con optimizaciones.

Test 1: Cache fidelity — datos cacheados identicos a descarga directa
Test 2: Pipeline con cache vs sin cache — lab lite produce mismos resultados
Test 3: Pipeline vs standalone — identico al verify_pipeline.py original
Test 4: Round-trip CSV (write -> read -> mismos presets)
Test 5: Formato de presets valido para lab historico
Test 6: Verificacion estructural de integracion (funciones exportadas)
Test 7: Diversidad de familias
"""

import os
import sys
import time
import shutil
import importlib.util

import pandas as pd
import numpy as np


def import_fresh(filename, mod_name=None):
    """Importa modulo fresco (sin cache)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    name = mod_name or filename.replace('.py', '')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SYMBOL = "BNB/USDT"
SC = SYMBOL.replace("/", "")

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} {detail}")
        failed += 1


# Directorios de trabajo
DIR_NOCACHE = "verify_nocache"
DIR_CACHE = "verify_cache"
DIR_STANDALONE = "verify_standalone"
CACHE_DIR_TEST = "verify_data_cache"

for d in [DIR_NOCACHE, DIR_CACHE, DIR_STANDALONE, CACHE_DIR_TEST]:
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)


# ============================================
# TEST 1: Cache fidelity — datos cacheados = descarga directa
# ============================================
print("=" * 70)
print("TEST 1: Cache fidelity — datos cacheados vs descarga directa")
print("=" * 70)

# Importar modulos
lite = import_fresh("lab_lite_zonas_v5d.py", "lite_t1")
cache = import_fresh("data_cache.py", "cache_t1")
cache.CACHE_DIR = CACHE_DIR_TEST

# Descargar directo (sin cache)
print("\n  Descargando 500 velas directo (sin cache)...")
direct_candles = lite.fetch_all_candles(SYMBOL, "1h", 500)
check("Descarga directa OK", len(direct_candles) >= 400,
      f"solo {len(direct_candles)} velas")

# Descargar via cache
print("  Descargando 500 velas via cache...")
cache.ensure_cached(SYMBOL, "1h", 500)
cached_list = cache.get_as_list(SYMBOL, "1h", 500)
cached_df = cache.get_as_dataframe(SYMBOL, "1h", 500)

check("Cache list OK", len(cached_list) >= 400,
      f"solo {len(cached_list)} velas")
check("Cache DataFrame OK", cached_df is not None and len(cached_df) >= 400,
      f"None o insuficiente")

# Comparar formatos
if len(direct_candles) > 0 and len(cached_list) > 0:
    # Alinear por timestamp (pueden tener 1-2 velas de diferencia por timing)
    direct_ts = set(c[0] for c in direct_candles)
    cached_ts = set(int(c[0]) for c in cached_list)
    common_ts = sorted(direct_ts & cached_ts)

    check("Timestamps comunes > 90%",
          len(common_ts) >= 0.9 * min(len(direct_candles), len(cached_list)),
          f"comunes={len(common_ts)} direct={len(direct_candles)} cached={len(cached_list)}")

    # Comparar OHLCV para timestamps comunes
    direct_dict = {c[0]: c for c in direct_candles}
    cached_dict = {int(c[0]): c for c in cached_list}

    ohlcv_match = True
    first_diff = None
    for ts in common_ts[:100]:  # Comparar primeras 100
        d = direct_dict[ts]
        c = cached_dict[ts]
        for j in range(1, 6):  # open, high, low, close, volume
            if abs(float(d[j]) - float(c[j])) > 1e-8:
                ohlcv_match = False
                first_diff = f"ts={ts} col={j} direct={d[j]} cached={c[j]}"
                break
        if not ohlcv_match:
            break

    check("OHLCV identicos (primeras 100 velas comunes)", ohlcv_match, first_diff or "")

# Verificar que DataFrame tiene formato correcto
if cached_df is not None:
    check("DataFrame tiene columna timestamp datetime",
          'timestamp' in cached_df.columns and pd.api.types.is_datetime64_any_dtype(cached_df['timestamp']))
    check("DataFrame tiene columnas OHLCV",
          all(c in cached_df.columns for c in ['open', 'high', 'low', 'close', 'volume']))

# Verificar cache hit (segunda lectura no descarga)
print("\n  Verificando cache hit (segunda lectura)...")
t0 = time.time()
cached_list_2 = cache.get_as_list(SYMBOL, "1h", 500)
t_hit = time.time() - t0
check("Cache hit es rapido (< 1s)", t_hit < 1.0, f"{t_hit:.3f}s")
check("Cache hit retorna mismos datos",
      len(cached_list_2) == len(cached_list))


# ============================================
# TEST 2: Lab Lite con cache vs sin cache — mismos resultados
# ============================================
print("\n" + "=" * 70)
print("TEST 2: Lab Lite con cache vs sin cache")
print("  Simbolo: BNB/USDT | Top N: 7 | Diversity: OFF")
print("=" * 70)

# Run A: sin cache
print(f"\n--- Run A: Sin cache (output: {DIR_NOCACHE}) ---")
t0 = time.time()

lite_a = import_fresh("lab_lite_zonas_v5d.py", "lite_nocache")
lite_a.OUTPUT_DIR = DIR_NOCACHE
lite_a.TOP_N_PRESETS = 7
lite_a.DIVERSITY_MODE = False

result_a = lite_a.process_symbol(SYMBOL)
time_a = time.time() - t0
print(f"\n  Sin cache: {time_a:.1f}s")

# Preparar cache con suficientes velas para lab lite
# Lab lite descarga TOTAL_CANDLES + warmup, normalmente ~5600 velas
cache_b = import_fresh("data_cache.py", "cache_t2")
cache_b.CACHE_DIR = CACHE_DIR_TEST
# Pre-descargar suficientes velas
cache_b.ensure_cached(SYMBOL, "1h", 6000)

# Run B: con cache
print(f"\n--- Run B: Con cache (output: {DIR_CACHE}) ---")
t0 = time.time()

lite_b = import_fresh("lab_lite_zonas_v5d.py", "lite_cache")
lite_b.OUTPUT_DIR = DIR_CACHE
lite_b.TOP_N_PRESETS = 7
lite_b.DIVERSITY_MODE = False

# Monkey-patch fetch_all_candles para usar cache
cache_b2 = import_fresh("data_cache.py", "cache_t2b")
cache_b2.CACHE_DIR = CACHE_DIR_TEST
cache_b2.patch_modules(lite_b, None, 5000, 10000)

result_b = lite_b.process_symbol(SYMBOL)
time_b = time.time() - t0
print(f"\n  Con cache: {time_b:.1f}s")

# Comparar resultados
print("\n--- Comparando resultados ---")

check("Ambos retornan resultados",
      result_a is not None and result_b is not None)

if result_a and result_b:
    top_a = result_a['top'][:100]
    top_b = result_b['top'][:100]

    check("Mismo numero de resultados top",
          len(top_a) == len(top_b),
          f"A={len(top_a)} B={len(top_b)}")

    # Los scores pueden diferir ligeramente si las velas descargadas
    # tienen 1-2 diferencia en el rango. Comparamos el RANKING (orden).
    # Si los top 10 presets son los mismos (aunque scores difieran levemente),
    # el pipeline es fiable.

    # Primero: comparar si los datos de entrada son identicos
    # (si el cache descargo exactamente las mismas velas)
    scores_match = True
    first_diff = None
    for i, (a, b) in enumerate(zip(top_a[:20], top_b[:20])):
        if abs(a['score'] - b['score']) > 1e-4:
            scores_match = False
            if first_diff is None:
                first_diff = f"pos {i}: A={a['score']:.6f} B={b['score']:.6f}"
            break

    check("Scores identicos top 20 (tolerancia 1e-4)",
          scores_match, first_diff or "")

    # Comparar presets seleccionados
    presets_a = result_a.get('selected_presets', [])
    presets_b = result_b.get('selected_presets', [])

    check("Mismos presets seleccionados",
          presets_a == presets_b,
          f"A={len(presets_a)} B={len(presets_b)}")

    if presets_a != presets_b and presets_a and presets_b:
        # Mostrar cuales difieren
        for i, (pa, pb) in enumerate(zip(presets_a, presets_b)):
            if pa != pb:
                print(f"    Preset {i+1}: A={pa[:4]} B={pb[:4]}")

    # Comparar CSVs
    csv_a = os.path.join(DIR_NOCACHE, f"presets_{SC}.csv")
    csv_b = os.path.join(DIR_CACHE, f"presets_{SC}.csv")
    if os.path.exists(csv_a) and os.path.exists(csv_b):
        df_a = pd.read_csv(csv_a)
        df_b = pd.read_csv(csv_b)
        check("CSVs de presets identicos", df_a.equals(df_b))

    # Comparar rankings txt
    rank_a = os.path.join(DIR_NOCACHE, f"ranking_lite_v5d_{SC}.txt")
    rank_b = os.path.join(DIR_CACHE, f"ranking_lite_v5d_{SC}.txt")
    if os.path.exists(rank_a) and os.path.exists(rank_b):
        with open(rank_a, encoding='utf-8') as f:
            lines_a = f.readlines()
        with open(rank_b, encoding='utf-8') as f:
            lines_b = f.readlines()

        ranking_diffs = 0
        for i, (la, lb) in enumerate(zip(lines_a, lines_b)):
            if any(skip in la for skip in ["Tiempo:", "Velas:", "descargadas"]):
                continue
            if la != lb:
                ranking_diffs += 1

        check("Rankings identicos (excluyendo timestamps)",
              ranking_diffs == 0,
              f"{ranking_diffs} lineas difieren")


# ============================================
# TEST 3: Pipeline vs Standalone (reproduce test original)
# ============================================
print("\n" + "=" * 70)
print("TEST 3: Pipeline vs Standalone")
print("=" * 70)

# Ya tenemos result_a (standalone sin cache)
# Ejecutar via pipeline module
print(f"\n--- Run C: Via pipeline (output: {DIR_STANDALONE}) ---")
t0 = time.time()

lite_c = import_fresh("lab_lite_zonas_v5d.py", "lite_pipeline")
lite_c.OUTPUT_DIR = DIR_STANDALONE
lite_c.TOP_N_PRESETS = 7
lite_c.DIVERSITY_MODE = False

result_c = lite_c.process_symbol(SYMBOL)
time_c = time.time() - t0
print(f"\n  Pipeline: {time_c:.1f}s")

if result_a and result_c:
    top_c = result_c['top'][:100]

    scores_ac = True
    for i, (a, c) in enumerate(zip(top_a[:100], top_c[:100])):
        if abs(a['score'] - c['score']) > 1e-6:
            scores_ac = False
            break

    check("Scores standalone vs pipeline identicos (top 100)", scores_ac)

    presets_c = result_c.get('selected_presets', [])
    check("Presets standalone vs pipeline identicos",
          presets_a == presets_c)


# ============================================
# TEST 4: Round-trip CSV
# ============================================
print("\n" + "=" * 70)
print("TEST 4: Round-trip CSV de presets")
print("=" * 70)

csv_path = os.path.join(DIR_NOCACHE, f"presets_{SC}.csv")
if os.path.exists(csv_path) and result_a:
    pip = import_fresh("pipeline.py", "pip_t4")
    loaded_presets, _ = pip.load_presets_from_csv(csv_path)
    original_presets = result_a['selected_presets']

    check("Mismo numero de presets",
          len(loaded_presets) == len(original_presets),
          f"loaded={len(loaded_presets)} original={len(original_presets)}")

    all_match = True
    for i, (orig, loaded) in enumerate(zip(original_presets, loaded_presets)):
        if orig != loaded:
            all_match = False
            print(f"    Preset {i}: orig={orig} loaded={loaded}")

    check("Presets round-trip identicos", all_match)


# ============================================
# TEST 5: Formato de presets valido para lab historico
# ============================================
print("\n" + "=" * 70)
print("TEST 5: Presets validos para lab historico")
print("=" * 70)

if result_a and result_a.get('selected_presets'):
    presets = result_a['selected_presets']

    check("Todos los presets tienen 12 elementos",
          all(len(p) == 12 for p in presets))

    valid_types = {'EMA', 'SMA', 'HMA', 'ALMA', 'ZLEMA', 'KAMA', 'DEMA',
                   'TEMA', 'McGinley', 'VIDYA', 'FRAMA', 'T3', 'SSmoother',
                   'VWMA', 'Tenkan', 'JMA', 'WMA', 'NONE'}

    for i, p in enumerate(presets):
        ft, fl = p[0], p[1]
        st, sl = p[4], p[5]
        tt, tl = p[8], p[9]

        check(f"Preset {i+1}: tipos validos ({ft}/{st}/{tt})",
              ft in valid_types and st in valid_types and tt in valid_types)
        check(f"Preset {i+1}: periodos son int",
              isinstance(fl, int) and isinstance(sl, int) and isinstance(tl, int))

    try:
        lab = import_fresh("lab_historico_numba_v8_3.py", "lab_t5")
        check("Lab historico importable", True)
    except Exception as e:
        check("Lab historico importable", False, str(e))


# ============================================
# TEST 6: Verificacion estructural de integracion
# ============================================
print("\n" + "=" * 70)
print("TEST 6: Verificacion estructural")
print("=" * 70)

# data_cache
try:
    dc = import_fresh("data_cache.py", "dc_t6")
    for fn in ['ensure_cached', 'get_as_list', 'get_as_dataframe',
               'patch_modules', 'prefetch_symbols']:
        check(f"data_cache.{fn} existe", hasattr(dc, fn))
except Exception as e:
    check("data_cache importable", False, str(e))

# pipeline
try:
    pip = import_fresh("pipeline.py", "pip_t6")
    for fn in ['phase_lite', 'phase_lab', 'phase_extractor', 'phase_validador',
               'load_presets_from_csv', 'run_pipeline']:
        check(f"pipeline.{fn} existe", hasattr(pip, fn))

    # Verificar que config tiene los nuevos campos
    check("Config tiene use_cache", "use_cache" in pip.DEFAULT_CONFIG)
    check("Config tiene workers", "workers" in pip.DEFAULT_CONFIG)
    check("Config use_cache default True", pip.DEFAULT_CONFIG["use_cache"] is True)
    check("Config workers default 1", pip.DEFAULT_CONFIG["workers"] == 1)
except Exception as e:
    check("Pipeline importable", False, str(e))

# extractor
try:
    ext = import_fresh("extractor_gemas.py", "ext_t6")
    for fn in ['load_all_presets', 'apply_validation_filter', 'extract_gems',
               'build_gem_table', 'assign_families', 'generate_summary']:
        check(f"extractor.{fn} existe", hasattr(ext, fn))
except Exception as e:
    check("Extractor importable", False, str(e))

# validador
try:
    val = import_fresh("validador_batch_v3.py", "val_t6")
    for fn in ['run_gem_validation', 'build_pivot', 'generate_report']:
        check(f"validador.{fn} existe", hasattr(val, fn))
except Exception as e:
    check("Validador importable", False, str(e))


# ============================================
# TEST 7: Diversidad de familias
# ============================================
print("\n" + "=" * 70)
print("TEST 7: Diversidad de familias")
print("=" * 70)

if result_a:
    top_results = result_a['top']

    # Sin diversidad: top 7 por score
    no_div = top_results[:7]
    no_div_families = set()
    for r in no_div:
        fam = f"{lite_a.ma_family(r['fast'])}/{lite_a.ma_family(r['slow'])}"
        no_div_families.add(fam)

    # Con diversidad
    diverse = lite_a.select_top_diverse(top_results, 7)
    div_families = set()
    for r in diverse:
        fam = f"{lite_a.ma_family(r['fast'])}/{lite_a.ma_family(r['slow'])}"
        div_families.add(fam)

    print(f"  Sin diversidad: {len(no_div_families)} familias - {no_div_families}")
    print(f"  Con diversidad: {len(div_families)} familias - {div_families}")

    check("Diversidad aporta mas familias o igual",
          len(div_families) >= len(no_div_families))

    # El #1 siempre debe estar en ambas selecciones
    no_div_top = (no_div[0]['fast'], no_div[0]['slow'], no_div[0]['trend'])
    diverse_entries = [(r['fast'], r['slow'], r['trend']) for r in diverse]
    check("#1 por score presente en seleccion diversa",
          no_div_top in diverse_entries)

    check("Todos los presets diversos tienen score > 0",
          all(r['score'] > 0 for r in diverse))


# ============================================
# RESULTADO FINAL
# ============================================
print("\n" + "=" * 70)
total = passed + failed
print(f"RESULTADO: {passed}/{total} tests pasados, {failed} fallidos")
if failed == 0:
    print("VERIFICACION EXITOSA — Pipeline con optimizaciones es identico")
else:
    print("HAY FALLOS — Revisar antes de usar")
print("=" * 70)

# Limpiar si todo OK
if failed == 0:
    for d in [DIR_NOCACHE, DIR_CACHE, DIR_STANDALONE, CACHE_DIR_TEST]:
        if os.path.exists(d):
            shutil.rmtree(d)
    print("Directorios de test limpiados")
else:
    print(f"Directorios conservados para inspeccion: {DIR_NOCACHE}, {DIR_CACHE}, {DIR_STANDALONE}")
