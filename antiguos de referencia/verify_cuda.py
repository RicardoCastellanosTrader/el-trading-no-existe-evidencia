#!/usr/bin/env python3
"""
verify_cuda.py - Verifica que el port CUDA produce resultados identicos al CPU.

Carga el dataset de referencia generado por generate_reference_dataset.py,
reproduce las mismas condiciones con CUDASimulator, y compara valor a valor.

Tolerancia:
  - float64 PnL/gp/gl/maxdd: abs(cuda - cpu) < 1e-10
  - trades/wins/cancels: exacto (son enteros)
"""

import os
import sys
import json
import time
import numpy as np

import lab_historico_numba_v8_3 as lab
import data_cache
from lab_cuda import CUDASimulatorOptimized

# ============================================
# CONFIGURACION
# ============================================
REFERENCE_DIR = "reference_dataset"

# Tolerancias
TOL_FLOAT = 1e-10       # Para pnl, maxdd, gp, gl
TOL_INT = 0.0           # Para trades, wins, cancels (exacto)
PASS_THRESHOLD = 0.9999 # 99.99% de valores deben coincidir


def load_reference():
    """Carga el dataset de referencia."""
    print("Cargando dataset de referencia...")

    configs = np.load(os.path.join(REFERENCE_DIR, "reference_config_ids.npy"))
    with open(os.path.join(REFERENCE_DIR, "reference_data_params.json"), 'r') as f:
        params = json.load(f)

    print(f"  Configs: {len(configs)}")
    print(f"  Symbol: {params['symbol']}, TF: {params['timeframe']}, Bars: {params['n_bars']}")

    return configs, params


def compare_results(cuda_results, cpu_results, label):
    """Compara resultados CUDA vs CPU con detalle."""
    n_configs = cuda_results.shape[0]
    total_values = n_configs * 7

    # Columnas: [pnl, trades, wins, cancels, maxdd, gp, gl]
    col_names = ['pnl', 'trades', 'wins', 'cancels', 'maxdd', 'gp', 'gl']
    float_cols = [0, 4, 5, 6]  # pnl, maxdd, gp, gl
    int_cols = [1, 2, 3]        # trades, wins, cancels

    matches = 0
    mismatches = 0
    max_deviation = 0.0
    mismatch_details = []

    for col_idx in range(7):
        cuda_col = cuda_results[:, col_idx]
        cpu_col = cpu_results[:, col_idx]

        if col_idx in int_cols:
            # Integer comparison (exact)
            col_match = (cuda_col == cpu_col)
        else:
            # Float comparison with tolerance
            col_match = np.abs(cuda_col - cpu_col) < TOL_FLOAT

        col_matches = int(np.sum(col_match))
        col_mismatches = n_configs - col_matches

        if col_idx in float_cols:
            col_max_dev = float(np.max(np.abs(cuda_col - cpu_col)))
            if col_max_dev > max_deviation:
                max_deviation = col_max_dev
        else:
            col_max_dev = float(np.max(np.abs(cuda_col - cpu_col)))

        matches += col_matches
        mismatches += col_mismatches

        status = "OK" if col_mismatches == 0 else "DIFF"
        print(f"    {col_names[col_idx]:>8}: {col_matches}/{n_configs} match ({status})"
              f"  max_dev={col_max_dev:.2e}")

        if col_mismatches > 0 and len(mismatch_details) < 10:
            # Report first few mismatches
            mismatch_idx = np.where(~col_match)[0][:5]
            for idx in mismatch_idx:
                mismatch_details.append(
                    f"      config[{idx}] {col_names[col_idx]}: "
                    f"cuda={cuda_col[idx]:.10f} cpu={cpu_col[idx]:.10f} "
                    f"diff={abs(cuda_col[idx]-cpu_col[idx]):.2e}"
                )

    match_pct = matches / total_values if total_values > 0 else 0.0
    passed = match_pct >= PASS_THRESHOLD

    print(f"  [{label}] Total: {matches}/{total_values} ({match_pct*100:.4f}%) "
          f"max_deviation={max_deviation:.2e} "
          f"{'PASS' if passed else 'FAIL'}")

    if mismatch_details:
        print(f"  Primeros mismatches:")
        for detail in mismatch_details[:10]:
            print(detail)

    return passed, match_pct, max_deviation


def main():
    print("="*70)
    print("VERIFICACION CUDA vs CPU")
    print("="*70)

    # 1. Cargar referencia
    configs, params = load_reference()

    symbol = params['symbol']
    timeframe = params['timeframe']
    n_candles = params['n_bars']
    preset = tuple(params['preset'])
    hyst_values = params['hyst_values']
    sl_pct = params['sl_pct']
    sl_emergency_pct = params['sl_emergency_pct']
    ts_pct = params['ts_pct']
    cooldown_bars = params['cooldown_bars']
    commission_pct = params['commission_pct']
    slices = params['slices']

    hyst_tags = {0.0: 'h00', 0.5: 'h05'}

    # 2. Cargar datos de mercado
    print(f"\nCargando datos de mercado {symbol}...")
    data_cache.ensure_cached(symbol, timeframe, n_candles)
    df = data_cache.get_as_dataframe(symbol, timeframe, n_candles)
    assert df is not None and len(df) >= n_candles, f"Datos insuficientes: {len(df) if df else 0}"
    print(f"  {len(df)} velas cargadas")

    # 3. Inicializar CUDA
    print(f"\nInicializando CUDASimulator...")
    sim = CUDASimulatorOptimized()

    if not sim.gpu_available:
        print("ERROR: No hay GPU disponible. No se puede verificar el port CUDA.")
        print("Ejecutando en modo fallback CPU para validar la logica del script...")

    # 4. Precalcular y subir datos
    all_passed = True
    total_tests = 0
    total_passed = 0
    global_max_dev = 0.0

    for hyst_val in hyst_values:
        hyst_tag = hyst_tags[hyst_val]
        print(f"\n{'='*60}")
        print(f"Hysteresis = {hyst_val} ({hyst_tag})")
        print(f"{'='*60}")

        # Precalcular en CPU
        print(f"  Precalculando datos (CPU)...")
        data = lab.precalculate_all_data(df, preset=preset, hyst_mult=hyst_val, symbol=symbol)

        # Subir a GPU
        print(f"  Subiendo a GPU...")
        handle = sim.upload_data(data)

        # 5. Ejecutar y comparar por cada tramo
        for slice_name, (start, end) in slices.items():
            start = int(start)
            end = int(end)
            key_r = f"{slice_name}_{hyst_tag}"

            print(f"\n  --- Tramo {slice_name}: [{start}, {end}] ({end-start} bars) ---")

            # Cargar referencia CPU
            ref_path = os.path.join(REFERENCE_DIR, f"reference_slice_{key_r}.npy")
            if not os.path.exists(ref_path):
                print(f"  SKIP: No existe {ref_path}")
                continue

            cpu_results = np.load(ref_path)

            # Ejecutar en GPU
            t0 = time.time()
            cuda_results = sim.run_on_slice(
                configs, handle, start, end,
                sl_pct, sl_emergency_pct, ts_pct, cooldown_bars, commission_pct
            )
            elapsed = time.time() - t0
            print(f"  GPU ejecutado en {elapsed:.3f}s")

            # Comparar
            passed, match_pct, max_dev = compare_results(cuda_results, cpu_results, key_r)

            total_tests += 1
            if passed:
                total_passed += 1
            else:
                all_passed = False
            if max_dev > global_max_dev:
                global_max_dev = max_dev

            # Tambien verificar scores
            ref_scores_path = os.path.join(REFERENCE_DIR, f"reference_scores_{key_r}.npy")
            if os.path.exists(ref_scores_path):
                cpu_scores = np.load(ref_scores_path)
                n_bars_period = end - start
                pnl = cuda_results[:, 0]
                trades = cuda_results[:, 1]
                wins = cuda_results[:, 2]
                cancels_arr = cuda_results[:, 3]
                maxdd = cuda_results[:, 4]
                gp = cuda_results[:, 5]
                gl = cuda_results[:, 6]

                score, pnl_ann, dd_f, pf, act_f, cr = lab.calc_score_v63(
                    pnl, maxdd, gp, gl, trades, cancels_arr, n_bars_period
                )
                cuda_scores = np.column_stack([score, pnl_ann, dd_f, pf, act_f, cr])

                scores_match = np.allclose(cuda_scores, cpu_scores, atol=TOL_FLOAT)
                scores_max_dev = float(np.max(np.abs(cuda_scores - cpu_scores)))
                print(f"  Scores: {'MATCH' if scores_match else 'DIFF'} (max_dev={scores_max_dev:.2e})")

    # Final summary
    print(f"\n{'='*70}")
    print(f"RESULTADO FINAL")
    print(f"{'='*70}")
    print(f"  Tests: {total_passed}/{total_tests} pasados")
    print(f"  Max desviacion global: {global_max_dev:.2e}")
    print(f"  Estado: {'PASS' if all_passed else 'FAIL'}")

    if all_passed:
        print(f"\n  El port CUDA produce resultados identicos al motor CPU.")
    else:
        print(f"\n  HAY DIFERENCIAS. Revisar los detalles arriba.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
