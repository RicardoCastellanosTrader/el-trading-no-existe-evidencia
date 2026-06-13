#!/bin/bash
# E1 driver: 6 placebos × (Phase1 CPU train+lite | Phase2 GPU regime-wf), secuencial,
# procesos separados (H_B isolation). Cada placebo ~1.5h GPU → ~9h total.
cd /c/Users/rixip/combolab || exit 1
SYMS="PLBGB1 PLBGB2 PLBGB3 PLBSH1 PLBSH2 PLBSH3"
for S in $SYMS; do
  echo "=== $S PHASE1 (train+lite) $(date -u) ==="
  python -u audit_forense_gap_20260612/e1_run.py --from-step train --to-step lite --recycle --symbols $S/USDT --chunk-size 1000000 2>&1 | grep -viE 'warning|warn:|userwarn' | grep -iE 'PASO|Seleccion|presets|Resultado|GLOBAL|Tiempo' || true
  echo "=== $S PHASE2 (regime-wf GPU) $(date -u) ==="
  python -u audit_forense_gap_20260612/e1_run.py --from-step regime-wf --recycle --symbols $S/USDT --chunk-size 1000000 2>&1 | grep -viE 'warning|warn:|userwarn|Vela [0-9]' | grep -iE 'PASO|CUDA|Preset|Resultado|JSONs|Tiempo|cluster|OK\]|specialist' || true
  echo "=== $S DONE $(date -u) ==="
done
echo "E1_DRIVER_DONE $(date -u)"
