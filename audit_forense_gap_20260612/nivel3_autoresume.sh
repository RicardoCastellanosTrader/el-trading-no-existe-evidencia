#!/bin/bash
# Auto-reanudación tras reboot del run Nivel 3 (red de seguridad para el TDR estocástico
# arquitectural Blackwell: un reboot mata la sesión; sin esto el run espera a Ricardo a mano).
# Disparado por la clave HKCU\...\Run "Nivel3AutoResume" (logon, sin admin). CONDICIONES DE SEGURIDAD:
#  - IDEMPOTENTE + resume-skip: el driver salta celdas SELLADAS, nunca re-corre completas.
#  - SINGLE-INSTANCE (#14): no relanza si ya hay un driver vivo (lock con PID vivo).
#  - AUTODESACTIVABLE: a 13/13 sellados borra su propia clave de auto-arranque.
# Desactivación manual: reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Nivel3AutoResume /f
set -u
cd /c/Users/rixip/combolab || exit 1
AD=audit_forense_gap_20260612
ANCHOR=2025-05-01
SYMS="ETH BNB XRP ATOM THETA ALGO DOT AVAX FET STX INJ IMX OP"
LOG=$AD/nivel3_autoresume.log
echo "==== AUTORESUME logon $(date -u) ====" >> "$LOG"

# 1) ¿run completo? (13/13 sellados) -> autodesactivar, no relanzar.
N=0; for S in $SYMS; do [ -f "$AD/nivel3_resmoke_trades_${S}_${ANCHOR}_data_cache.json" ] && N=$((N+1)); done
echo "  sellados=$N/13" >> "$LOG"
if [ "$N" -ge 13 ]; then
  echo "  COMPLETO -> borro clave de auto-arranque HKCU\\...\\Run\\Nivel3AutoResume" >> "$LOG"
  reg delete 'HKCU\Software\Microsoft\Windows\CurrentVersion\Run' //v Nivel3AutoResume //f >> "$LOG" 2>&1
  exit 0
fi

# 2) ¿driver ya vivo? -> no relanzar (#14). El driver también tiene su propio guard.
LOCK=$AD/nivel3_run.lock
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "  driver ya vivo PID=$(cat "$LOCK") -> NO relanzo" >> "$LOG"; exit 0
fi
[ -f "$LOCK" ] && { echo "  lock stale (reboot, PID=$(cat "$LOCK") muerto) -> limpio" >> "$LOG"; rm -f "$LOCK"; }

# 3) sanity toolchain antes de confiar GPU (precedente is_available=False por paths).
if ! python -c "import lab_cuda; lab_cuda._setup_cuda_paths(); from numba import cuda; import sys; sys.exit(0 if cuda.is_available() else 1)" >> "$LOG" 2>&1; then
  echo "  [WARN] cuda.is_available()=False tras reboot -> NO relanzo auto (requiere diagnóstico Ricardo)" >> "$LOG"; exit 2
fi

# 4) relanzar driver (resume-skip continúa desde $N sellados; driver re-ata su monitor 1s+fsync).
echo "  relanzo driver ($N/13 sellados) $(date -u)" >> "$LOG"
bash "$AD/nivel3_full_run_driver.sh" >> "$LOG" 2>&1
echo "  driver terminó/murió rc=$? $(date -u)" >> "$LOG"
