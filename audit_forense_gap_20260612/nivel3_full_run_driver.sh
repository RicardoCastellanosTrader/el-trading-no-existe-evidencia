#!/bin/bash
# Nivel 3 — RUN COMPLETO: 13 celdas, ancla 2025-05-01 (holdout capado 2026-05-16), fuente data_cache.
# Por celda: asof_run phase1(CPU)+phase2(GPU regime-wf canónico, leakage gate, chunk v18) + extensión D3/D4.
# Secuencial-estricto #14. Resume-safe (salta celdas con sealed json). Auto-cleanup parts (asof_run).
# NO mira veredicto (Δ/AUC) — la extensión solo sella trades + reporta gate/feasibility/recursos.
# El veredicto T3.2 se agrega aparte de los 13 sealed jsons.
cd /c/Users/rixip/combolab || exit 1
AD=audit_forense_gap_20260612
ANCHOR=2025-05-01
SYMS="ETH BNB XRP ATOM THETA ALGO DOT AVAX FET STX INJ IMX OP"
LOG=$AD/nivel3_full_run.log
MONLOG=$AD/nivel3_fullrun_vram_1s.log
LOCK=$AD/nivel3_run.lock
# Single-instance guard (sequential-strict #14): si otro driver está vivo, abortar.
# Evita que la auto-reanudación tras reboot lance un segundo driver en paralelo.
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "[ABORT] otro driver vivo PID=$(cat "$LOCK") — sequential-strict #14" | tee -a $LOG; exit 1
fi
echo $$ > "$LOCK"
# Monitor VRAM 1s+fsync atado al ciclo de vida del RUN (arranca con el run, trap EXIT lo mata).
# Fix tras TDR 2026-06-16: el monitor previo muestreaba cada 5 min y bufferizaba -> ceguera del crash.
python -u $AD/vram_monitor.py --log $MONLOG --interval 1 &
MONPID=$!
trap "kill $MONPID 2>/dev/null; rm -f $LOCK" EXIT
echo "==== NIVEL3 RUN COMPLETO START $(date -u) ancla=$ANCHOR fuente=data_cache monPID=$MONPID ====" | tee -a $LOG
for S in $SYMS; do
  SEAL=$AD/nivel3_resmoke_trades_${S}_${ANCHOR}_data_cache.json
  if [ -f "$SEAL" ]; then echo "[$S] SKIP (sealed existe) $(date -u)" | tee -a $LOG; continue; fi
  echo "===== [$S] CELL START $(date -u) =====" | tee -a $LOG
  PYTHONIOENCODING=utf-8 python -u $AD/asof_run.py --symbol $S --anchor $ANCHOR --phase 1 --source data_cache 2>&1 \
    | grep -viE "warning|Vela [0-9]" | grep -iE "prehistoria|cluster|Tiempo|Error|LEAK" | tee -a $LOG
  echo "----- [$S] PHASE2 GPU $(date -u) -----" | tee -a $LOG
  PYTHONIOENCODING=utf-8 python -u $AD/asof_run.py --symbol $S --anchor $ANCHOR --phase 2 --source data_cache 2>&1 \
    | grep -viE "warning|Vela [0-9]" | grep -iE "Tiempo|LEAKAGE|cluster|Limpieza|Error|JSONs finales" | tee -a $LOG
  if [ ! -f "$AD/asof_sandbox/${S}_${ANCHOR}/regime_wf/${S}USDT_specialist_configs.json" ]; then
    echo "[$S] FAIL phase2 (sin JSON) — continúo, retry en re-run $(date -u)" | tee -a $LOG; continue; fi
  echo "----- [$S] EXTENSION D3/D4 $(date -u) -----" | tee -a $LOG
  PYTHONIOENCODING=utf-8 python -u $AD/asof_d3d4_extension.py --symbol $S --anchor $ANCHOR --source data_cache 2>&1 \
    | grep -viE "warning" | grep -iE "leakage|GATE|C[0-9]:|D4|recursos|fuente" | tee -a $LOG
  echo "===== [$S] CELL DONE $(date -u) =====" | tee -a $LOG
done
echo "==== NIVEL3 RUN COMPLETO END $(date -u) ====" | tee -a $LOG
