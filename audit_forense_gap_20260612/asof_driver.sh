#!/bin/bash
# E2-full driver: 4 símbolos base × 2 anclas = 8 runs as-of, secuencial estricto (#14).
# Cada run: Phase1 (CPU train+lite) → Phase2 (GPU regime-wf + leakage gate) → eval holdout.
# Lanzar SOLO tras E1 completo (sequential-strict GPU). ~36-64h.
cd /c/Users/rixip/combolab || exit 1
AD=audit_forense_gap_20260612
for A in 2025-10-01 2026-02-01; do
  for S in BTC SOL LINK LTC; do
    echo "===== $S @ $A — PHASE1 $(date -u) ====="
    python -u $AD/asof_run.py --symbol $S --anchor $A --phase 1 2>&1 | grep -viE 'warning|warn' | grep -iE 'prehistoria|Seleccion|Resultado|GLOBAL|Tiempo|Error' || true
    echo "===== $S @ $A — PHASE2 GPU $(date -u) ====="
    python -u $AD/asof_run.py --symbol $S --anchor $A --phase 2 2>&1 | grep -viE 'warning|warn|Vela [0-9]' | grep -iE 'PASO|CUDA|Preset|Resultado|JSONs|Tiempo|LEAKAGE|specialist|cluster' || true
    echo "===== $S @ $A — EVAL $(date -u) ====="
    python -u $AD/asof_eval.py --symbol $S --anchor $A 2>&1 | grep -iE 'holdout|PF_net|leakage|SIN specialist' || true
  done
done
echo "ASOF_DRIVER_DONE $(date -u)"
