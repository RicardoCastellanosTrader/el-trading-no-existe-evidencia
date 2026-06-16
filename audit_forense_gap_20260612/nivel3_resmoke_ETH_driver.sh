#!/bin/bash
# Nivel 3 — RE-SMOKE de la celda que crasheó: ETH @2025-05-01, chunk 1M (idéntico al run original),
# fuente data_cache. PROPÓSITO: discriminar TDR transitorio-vs-determinista CON telemetría VRAM 1s.
# NO baja chunk (eso solo si el monitor muestra presión de VRAM determinista, Tier 3).
# Monitor VRAM atado al ciclo de vida (arranca con el run, trap EXIT lo mata).
# Riesgo = otro reinicio: INOFENSIVO (read-only + resume-skip + 0 selladas que perder).
set -u
cd /c/Users/rixip/combolab || exit 1
AD=audit_forense_gap_20260612
SYM=ETH; ANCHOR=2025-05-01
MONLOG=$AD/vram_resmoke_ETH_1M.log
RUNLOG=$AD/nivel3_resmoke_ETH_1M_run.log
SEAL=$AD/asof_sandbox/${SYM}_${ANCHOR}/regime_wf/${SYM}USDT_specialist_configs.json

# --- monitor VRAM 1s+fsync como hijo, muere con este script ---
python -u $AD/vram_monitor.py --log $MONLOG --interval 1 &
MONPID=$!
trap "kill $MONPID 2>/dev/null" EXIT

echo "==== ETH RE-SMOKE @1M START $(date -u) monPID=$MONPID ====" | tee -a $RUNLOG
echo "----- PHASE1 CPU $(date -u) -----" | tee -a $RUNLOG
PYTHONIOENCODING=utf-8 python -u $AD/asof_run.py --symbol $SYM --anchor $ANCHOR --phase 1 --source data_cache 2>&1 \
  | grep -viE "warning|Vela [0-9]" | grep -iE "prehistoria|cluster|Tiempo|Error|LEAK" | tee -a $RUNLOG

echo "----- PHASE2 GPU @1M $(date -u) (kernel canónico — punto del TDR) -----" | tee -a $RUNLOG
PYTHONIOENCODING=utf-8 python -u $AD/asof_run.py --symbol $SYM --anchor $ANCHOR --phase 2 --source data_cache 2>&1 \
  | grep -viE "warning|Vela [0-9]" | grep -iE "Tiempo|LEAKAGE|cluster|Limpieza|Error|JSONs finales" | tee -a $RUNLOG

if [ -f "$SEAL" ]; then
  echo "----- PHASE2 COMPLETÓ (sin TDR) — EXTENSION D3/D4 sella celda $(date -u) -----" | tee -a $RUNLOG
  PYTHONIOENCODING=utf-8 python -u $AD/asof_d3d4_extension.py --symbol $SYM --anchor $ANCHOR --source data_cache 2>&1 \
    | grep -viE "warning" | grep -iE "leakage|GATE|C[0-9]:|D4|recursos|fuente" | tee -a $RUNLOG
  echo "==== ETH RE-SMOKE @1M DONE OK $(date -u) ====" | tee -a $RUNLOG
else
  echo "==== ETH RE-SMOKE @1M: PHASE2 SIN JSON (TDR o fallo) $(date -u) ====" | tee -a $RUNLOG
fi