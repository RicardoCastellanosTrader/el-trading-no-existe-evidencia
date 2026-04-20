#!/usr/bin/env python3
"""
generate_reference_dataset.py - Genera dataset de referencia CPU para verificar
ports a GPU (CUDA) u otras implementaciones.

Ejecuta run_on_slice + calc_score_v63 con configuraciones diversas sobre
distintos tramos de datos BTC/USDT 1h, guarda resultados y auto-verifica.
"""

import os
import sys
import json
import time
import numpy as np

# Importar lab y data_cache
import lab_historico_numba_v8_3 as lab
import data_cache

# ============================================
# CONFIGURACION
# ============================================
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
N_CANDLES = 10000
N_CONFIGS = 1000

OUTPUT_DIR = "reference_dataset"

# Parametros de riesgo (mismos que el lab)
SL_PCT = lab.SL_PERCENT               # 3.0
SL_EMERGENCY_PCT = lab.SL_EMERGENCY_PERCENT  # 5.0
TS_PCT = lab.TS_PERCENT                # 0.5
COOLDOWN_BARS = lab.COOLDOWN_BARS      # 1
COMMISSION_PCT = lab.COMMISSION_ROUND_TRIP    # 0.10

# Tramos
SLICES = {
    'A': (1000, 4000),   # 3000 bars
    'B': (4000, 7000),   # 3000 bars
    'C': (1000, 7000),   # 6000 bars
}

# Hysteresis values
HYST_VALUES = [0.0, 0.5]
HYST_TAGS = {0.0: 'h00', 0.5: 'h05'}


def select_diverse_configs(n_target=1000):
    """Genera un subset diverso de config_ids del espacio completo.
    Toma las primeras 200, las ultimas 200, y 600 uniformemente distribuidas.
    """
    print(f"Generando configs validas...")
    all_configs = lab.generate_valid_configs()
    total = len(all_configs)
    print(f"  Total configs validas: {total:,}")

    if total <= n_target:
        print(f"  Usando todas ({total})")
        return all_configs

    # Primeras 200
    first_200 = all_configs[:200]
    # Ultimas 200
    last_200 = all_configs[-200:]
    # 600 uniformemente distribuidas del medio
    middle_indices = np.linspace(200, total - 201, 600, dtype=int)
    middle_600 = all_configs[middle_indices]

    selected = np.concatenate([first_200, middle_600, last_200])
    # Eliminar duplicados manteniendo orden
    _, unique_idx = np.unique(selected, return_index=True)
    selected = selected[np.sort(unique_idx)]

    print(f"  Seleccionadas: {len(selected)} configs diversas")
    return selected


def get_btc_preset():
    """Obtiene el primer preset de BTC/USDT del lab."""
    presets = lab.SYMBOL_ZONE_PRESETS.get(SYMBOL, [])
    if not presets:
        raise RuntimeError(f"No hay presets para {SYMBOL} en SYMBOL_ZONE_PRESETS")
    preset = presets[0]
    print(f"  Preset BTC: {preset[0]}({preset[1]})/{preset[4]}({preset[5]})/{preset[8]}({preset[9]})")
    return preset


def run_and_score(configs, data, start, end, label):
    """Ejecuta run_on_slice y calc_score_v63, retorna resultados y scores."""
    n_bars_period = end - start
    print(f"  [{label}] Ejecutando run_on_slice bars [{start}, {end}] ({n_bars_period} bars, {len(configs)} configs)...")
    t0 = time.time()
    results = lab.run_on_slice(
        configs, data, start, end,
        SL_PCT, SL_EMERGENCY_PCT, TS_PCT, COOLDOWN_BARS, COMMISSION_PCT
    )
    elapsed = time.time() - t0
    print(f"  [{label}] Completado en {elapsed:.1f}s")

    # calc_score_v63 espera arrays columna
    pnl = results[:, 0]
    trades = results[:, 1]
    wins = results[:, 2]
    cancels = results[:, 3]
    maxdd = results[:, 4]
    gp = results[:, 5]
    gl = results[:, 6]

    score, pnl_ann, dd_f, pf, act_f, cr = lab.calc_score_v63(
        pnl, maxdd, gp, gl, trades, cancels, n_bars_period
    )

    # Apilar scores en (N, 6)
    scores = np.column_stack([score, pnl_ann, dd_f, pf, act_f, cr])

    return results, scores


def print_summary(results, scores, label):
    """Imprime resumen de rangos de valores."""
    pnl = results[:, 0]
    trades = results[:, 1]
    wins = results[:, 2]
    cancels = results[:, 3]
    maxdd = results[:, 4]
    gp = results[:, 5]
    gl = results[:, 6]

    print(f"    {label} resumen:")
    print(f"      PnL:    min={pnl.min():.4f}  max={pnl.max():.4f}  mean={pnl.mean():.4f}")
    print(f"      Trades: min={trades.min():.0f}  max={trades.max():.0f}  mean={trades.mean():.1f}")
    print(f"      Wins:   min={wins.min():.0f}  max={wins.max():.0f}")
    print(f"      Cancel: min={cancels.min():.0f}  max={cancels.max():.0f}")
    print(f"      MaxDD:  min={maxdd.min():.4f}  max={maxdd.max():.4f}")
    print(f"      GP:     min={gp.min():.4f}  max={gp.max():.4f}")
    print(f"      GL:     min={gl.min():.4f}  max={gl.max():.4f}")
    print(f"      Score:  min={scores[:,0].min():.4f}  max={scores[:,0].max():.4f}")

    n_zero_trades = int(np.sum(trades == 0))
    n_positive_pnl = int(np.sum(pnl > 0))
    print(f"      Configs con 0 trades: {n_zero_trades}/{len(trades)}")
    print(f"      Configs con PnL>0:    {n_positive_pnl}/{len(pnl)}")


def verify_results(configs, data, all_results, all_scores):
    """Re-ejecuta y verifica bit a bit contra los datos guardados/cargados."""
    print("\n" + "="*60)
    print("AUTO-VERIFICACION: Re-ejecutando y comparando bit a bit...")
    print("="*60)

    errors = 0
    for hyst_val in HYST_VALUES:
        hyst_tag = HYST_TAGS[hyst_val]
        for slice_name, (start, end) in SLICES.items():
            key_r = f"{slice_name}_{hyst_tag}"
            key_s = f"scores_{slice_name}_{hyst_tag}"

            saved_results = all_results[key_r]
            saved_scores = all_scores[key_s]

            # Re-ejecutar
            results2, scores2 = run_and_score(
                configs, data[hyst_val], start, end, f"verify_{key_r}"
            )

            # Comparar bit a bit
            if not np.array_equal(results2, saved_results):
                diff_count = int(np.sum(results2 != saved_results))
                max_diff = float(np.max(np.abs(results2 - saved_results)))
                print(f"  ERROR: {key_r} results difieren! {diff_count} valores, max_diff={max_diff}")
                errors += 1
            else:
                print(f"  OK: {key_r} results identicos bit a bit")

            if not np.array_equal(scores2, saved_scores):
                diff_count = int(np.sum(scores2 != saved_scores))
                max_diff = float(np.max(np.abs(scores2 - saved_scores)))
                print(f"  ERROR: {key_s} scores difieren! {diff_count} valores, max_diff={max_diff}")
                errors += 1
            else:
                print(f"  OK: {key_s} scores identicos bit a bit")

    if errors > 0:
        print(f"\nFAILED: {errors} verificaciones fallaron!")
        sys.exit(1)
    else:
        print(f"\nPASSED: Todas las verificaciones OK - guardado/carga es correcto")


def main():
    print("="*70)
    print("GENERADOR DE DATASET DE REFERENCIA CPU")
    print("="*70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Obtener datos
    print(f"\n[1/6] Descargando/cargando datos {SYMBOL} {TIMEFRAME}...")
    data_cache.ensure_cached(SYMBOL, TIMEFRAME, N_CANDLES)
    df = data_cache.get_as_dataframe(SYMBOL, TIMEFRAME, N_CANDLES)
    if df is None or len(df) < N_CANDLES:
        print(f"ERROR: No se pudieron obtener {N_CANDLES} velas (got {len(df) if df is not None else 0})")
        sys.exit(1)
    print(f"  Datos cargados: {len(df)} velas")

    # 2. Obtener preset BTC
    print(f"\n[2/6] Cargando preset BTC...")
    preset = get_btc_preset()

    # 3. Generar configs diversas
    print(f"\n[3/6] Generando {N_CONFIGS} config_ids diversas...")
    configs = select_diverse_configs(N_CONFIGS)

    # 4. Precalcular datos para cada hyst value
    print(f"\n[4/6] Precalculando datos (2 valores de hysteresis)...")
    data_by_hyst = {}
    for hyst_val in HYST_VALUES:
        print(f"\n  --- Hysteresis = {hyst_val} ---")
        data_by_hyst[hyst_val] = lab.precalculate_all_data(
            df, preset=preset, hyst_mult=hyst_val, symbol=SYMBOL
        )

    # 5. Ejecutar simulaciones
    print(f"\n[5/6] Ejecutando simulaciones...")
    all_results = {}
    all_scores = {}

    for hyst_val in HYST_VALUES:
        hyst_tag = HYST_TAGS[hyst_val]
        data = data_by_hyst[hyst_val]

        for slice_name, (start, end) in SLICES.items():
            key_r = f"{slice_name}_{hyst_tag}"
            key_s = f"scores_{slice_name}_{hyst_tag}"

            results, scores = run_and_score(
                configs, data, start, end, f"{slice_name}_{hyst_tag}"
            )

            all_results[key_r] = results
            all_scores[key_s] = scores

            print_summary(results, scores, f"{slice_name}_{hyst_tag}")

    # 6. Guardar
    print(f"\n[6/6] Guardando en {OUTPUT_DIR}/...")

    # Config IDs
    np.save(os.path.join(OUTPUT_DIR, "reference_config_ids.npy"), configs)

    # Parametros
    params = {
        'symbol': SYMBOL,
        'timeframe': TIMEFRAME,
        'n_bars': int(len(df)),
        'n_configs': int(len(configs)),
        'preset': list(preset),  # tuple -> list for JSON
        'hyst_values': HYST_VALUES,
        'sl_pct': SL_PCT,
        'sl_emergency_pct': SL_EMERGENCY_PCT,
        'ts_pct': TS_PCT,
        'cooldown_bars': COOLDOWN_BARS,
        'commission_pct': COMMISSION_PCT,
        'slices': {k: list(v) for k, v in SLICES.items()},
    }
    with open(os.path.join(OUTPUT_DIR, "reference_data_params.json"), 'w') as f:
        json.dump(params, f, indent=2)

    # Resultados y scores
    for key, arr in all_results.items():
        np.save(os.path.join(OUTPUT_DIR, f"reference_slice_{key}.npy"), arr)
    for key, arr in all_scores.items():
        np.save(os.path.join(OUTPUT_DIR, f"reference_{key}.npy"), arr)

    print(f"  Guardados {len(all_results)} archivos de resultados + {len(all_scores)} de scores")

    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  Configs:  {len(configs)}")
    print(f"  Tramos:   {len(SLICES)}")
    print(f"  Hyst:     {HYST_VALUES}")
    print(f"  Archivos: {2 + 2*len(SLICES)*len(HYST_VALUES)} (config_ids + params + results + scores)")

    # Auto-verificacion: cargar y re-ejecutar
    print(f"\n[VERIFY] Cargando archivos guardados y re-verificando...")
    loaded_configs = np.load(os.path.join(OUTPUT_DIR, "reference_config_ids.npy"))
    assert np.array_equal(loaded_configs, configs), "Config IDs no coinciden!"

    loaded_results = {}
    loaded_scores = {}
    for key in all_results:
        loaded_results[key] = np.load(os.path.join(OUTPUT_DIR, f"reference_slice_{key}.npy"))
        assert np.array_equal(loaded_results[key], all_results[key]), f"Results {key} no coinciden tras carga!"

    for key in all_scores:
        loaded_scores[key] = np.load(os.path.join(OUTPUT_DIR, f"reference_{key}.npy"))
        assert np.array_equal(loaded_scores[key], all_scores[key]), f"Scores {key} no coinciden tras carga!"

    print(f"  Carga/guardado verificado OK")

    # Re-ejecutar y comparar bit a bit
    verify_results(configs, data_by_hyst, loaded_results, loaded_scores)


if __name__ == "__main__":
    main()
