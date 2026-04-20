#!/usr/bin/env python3
"""Fidelity test: CUDA vs Numba CPU on 1 preset, 5000 bars BTC with cluster labels.

Compares:
- 7 global results: pnl, trades, wins, cancels, maxdd, gp, gl
- 6 cluster arrays: cl_pnl, cl_trades, cl_wins, cl_maxdd, cl_gp, cl_gl
"""
import os
import sys
import time
import numpy as np

# Fix Windows cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
combolab_dir = os.path.join(os.path.dirname(base_dir), 'combolab')
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if combolab_dir not in sys.path:
    sys.path.insert(0, combolab_dir)

import lab_historico_numba_v8_3 as lab
from lab_cuda import CUDASimulatorOptimized
from regime_walk_forward import load_full_history, load_regime_model, compute_cluster_labels
from regime_walk_forward import identify_episodes, build_regime_labels

SYMBOL = "BTC/USDT"
N_BARS_TEST = 5000

print("=" * 70)
print("FIDELITY TEST: CUDA vs Numba CPU")
print("=" * 70)

# 1. Load data
print("\n[1] Loading BTC data...")
df = load_full_history(SYMBOL)
if df is None:
    print("ERROR: No BTC data found")
    sys.exit(1)
df = df.iloc[:N_BARS_TEST].copy().reset_index(drop=True)
print(f"    {len(df)} bars loaded")

# 2. Load model and compute cluster labels
print("[2] Computing cluster labels...")
model_data = load_regime_model(SYMBOL)
if model_data is None:
    print("ERROR: No regime model for BTC")
    sys.exit(1)

cluster_labels_raw, n_clusters = compute_cluster_labels(df, model_data)
episodes = identify_episodes(cluster_labels_raw, n_clusters, min_bars=50)
regime_labels, n_doubled, split_info = build_regime_labels(
    cluster_labels_raw, episodes, n_clusters, train_ratio=0.70)
print(f"    {n_clusters} clusters -> {n_doubled} doubled labels")

# 3. Generate configs and pick 1 preset
configs = lab.generate_valid_configs()
n_configs = len(configs)
print(f"[3] {n_configs:,} configs")

# Use first available preset
from regime_walk_forward import load_presets
presets = load_presets(SYMBOL, "output/")
if not presets:
    print("ERROR: No presets for BTC")
    sys.exit(1)
preset = presets[0]
hyst_mult = 0.0
print(f"    Preset: {preset[0]}({preset[1]})/{preset[4]}({preset[5]}), hyst={hyst_mult}")

# 4. Precalculate data
print("[4] Precalculating...")
data = lab.precalculate_all_data(df, preset=preset, hyst_mult=hyst_mult, symbol=SYMBOL)
n_data_bars = len(data['close'])

# 5. Run CPU (Numba)
print(f"\n[5] Running Numba CPU ({n_configs:,} configs x {n_data_bars} bars)...")
t0 = time.time()
cpu_result = lab.run_on_slice(
    configs, data, 0, n_data_bars,
    lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT, lab.TS_PERCENT,
    lab.COOLDOWN_BARS, lab.COMMISSION_ROUND_TRIP,
    cluster_labels=regime_labels, n_clusters=n_doubled)
t_cpu = time.time() - t0
cpu_results, cpu_cl_pnl, cpu_cl_trades, cpu_cl_wins, cpu_cl_maxdd, cpu_cl_gp, cpu_cl_gl = cpu_result
print(f"    CPU: {t_cpu:.2f}s ({n_configs/t_cpu:,.0f} configs/s)")

# 6. Run CUDA
print(f"\n[6] Running CUDA ({n_configs:,} configs x {n_data_bars} bars)...")
sim = CUDASimulatorOptimized()
if not sim.gpu_available:
    print("ERROR: No GPU available!")
    sys.exit(1)

handle = sim.upload_data(data)
t0 = time.time()
gpu_result = sim.run_on_slice(
    configs, handle, 0, n_data_bars,
    lab.SL_PERCENT, lab.SL_EMERGENCY_PERCENT, lab.TS_PERCENT,
    lab.COOLDOWN_BARS, lab.COMMISSION_ROUND_TRIP,
    cluster_labels=regime_labels, n_clusters=n_doubled)
t_gpu = time.time() - t0
gpu_results, gpu_cl_pnl, gpu_cl_trades, gpu_cl_wins, gpu_cl_maxdd, gpu_cl_gp, gpu_cl_gl = gpu_result
print(f"    CUDA: {t_gpu:.2f}s ({n_configs/t_gpu:,.0f} configs/s)")
print(f"    Speedup: {t_cpu/t_gpu:.1f}x")

# 7. Compare
print(f"\n{'=' * 70}")
print("COMPARISON")
print(f"{'=' * 70}")

all_ok = True

# Global results
names_global = ['pnl', 'trades', 'wins', 'cancels', 'maxdd', 'gp', 'gl']
print("\n--- Global results (7 columns) ---")
for i, name in enumerate(names_global):
    cpu_col = cpu_results[:, i]
    gpu_col = gpu_results[:, i]
    match = np.array_equal(cpu_col, gpu_col)
    max_diff = np.max(np.abs(cpu_col - gpu_col)) if not match else 0.0
    n_diff = int(np.sum(cpu_col != gpu_col))
    status = "OK" if match else f"DIFF (max={max_diff:.2e}, n={n_diff})"
    print(f"  {name:<10s}: {status}")
    if not match:
        all_ok = False

# Cluster arrays
print(f"\n--- Cluster arrays ({n_doubled} clusters) ---")
cluster_arrays = [
    ('cl_pnl', cpu_cl_pnl, gpu_cl_pnl),
    ('cl_trades', cpu_cl_trades, gpu_cl_trades),
    ('cl_wins', cpu_cl_wins, gpu_cl_wins),
    ('cl_maxdd', cpu_cl_maxdd, gpu_cl_maxdd),
    ('cl_gp', cpu_cl_gp, gpu_cl_gp),
    ('cl_gl', cpu_cl_gl, gpu_cl_gl),
]
for name, cpu_arr, gpu_arr in cluster_arrays:
    match = np.array_equal(cpu_arr, gpu_arr)
    max_diff = np.max(np.abs(cpu_arr - gpu_arr)) if not match else 0.0
    n_diff = int(np.sum(cpu_arr != gpu_arr))
    status = "OK" if match else f"DIFF (max={max_diff:.2e}, n={n_diff})"
    print(f"  {name:<12s}: {status}")
    if not match:
        all_ok = False

print(f"\n{'=' * 70}")
if all_ok:
    print("RESULT: BIT-IDENTICAL -- All 7 global + 6 cluster arrays match perfectly")
else:
    print("RESULT: DIFFERENCES FOUND -- See details above")
print(f"{'=' * 70}")
