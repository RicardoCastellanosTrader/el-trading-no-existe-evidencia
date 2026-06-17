#!/bin/bash
# Auto-reanudación HONESTA tras reboot del run Nivel 3 (TDR 0x116 estocástico Blackwell+WDDM).
# NO reinicia en silencio: CAPTURA evidencia forense + ALERTA + LÍMITE de reintentos ANTES de continuar.
# Distingue TDR estocástico (recurre en celdas distintas -> reanuda) de crash DETERMINISTA
# (misma celda repetida -> DETIENE, rompe el bucle infinito).
# Disparado por HKCU\...\Run "Nivel3AutoResume" (logon, sin admin).
# Condiciones de seguridad: resume-skip + single-instance(#14) + sanity toolchain + autodesactiva 13/13.
# Desactivar:   reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Nivel3AutoResume /f
# Reset contadores (al iniciar run limpio): rm -f crash_evidence/retry_state.txt crash_evidence/global_reboots.txt
# DRYRUN=1 -> valida la mecánica sin relanzar el driver ni tocar HKCU.
set -u
cd /c/Users/rixip/combolab || exit 1
AD=audit_forense_gap_20260612
ANCHOR=2025-05-01
SYMS="ETH BNB XRP ATOM THETA ALGO DOT AVAX FET STX INJ IMX OP"
LOG=$AD/nivel3_autoresume.log
EVID=$AD/crash_evidence
STATE=$EVID/retry_state.txt
GLOBAL=$EVID/global_reboots.txt
LOCK=$AD/nivel3_run.lock
RUNKEY='HKCU\Software\Microsoft\Windows\CurrentVersion\Run'
MAX_CELL=2; MAX_GLOBAL=5
DRY=${DRYRUN:-0}
mkdir -p "$EVID"
TS=$(date -u +%Y%m%dT%H%M%SZ)
echo "==== AUTORESUME logon $TS (DRY=$DRY) ====" >> "$LOG"

disable_autostart() {
  if [ "$DRY" = "1" ]; then echo "  [DRY] reg delete RunKey" >> "$LOG";
  else reg delete "$RUNKEY" //v Nivel3AutoResume //f >> "$LOG" 2>&1; fi
}

# 0) run completo (13/13) -> autodesactivar
N=0; for S in $SYMS; do [ -f "$AD/nivel3_resmoke_trades_${S}_${ANCHOR}_data_cache.json" ] && N=$((N+1)); done
echo "  sellados=$N/13" >> "$LOG"
if [ "$N" -ge 13 ]; then echo "  COMPLETO -> desactivo auto-arranque" >> "$LOG"; disable_autostart; exit 0; fi

# 1) driver ya vivo (#14) -> no relanzar
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "  driver vivo PID=$(cat "$LOCK") -> NO relanzo (#14)" >> "$LOG"; exit 0; fi

# 2) celda en curso = primera no sellada
NEXT=""; for S in $SYMS; do [ -f "$AD/nivel3_resmoke_trades_${S}_${ANCHOR}_data_cache.json" ] || { NEXT=$S; break; }; done
echo "  celda en curso/próxima=$NEXT" >> "$LOG"

# 3) ¿interrupción? lock stale (existe pero PID no vivo, ya descartado en paso 1) = driver matado sin exit limpio
if [ -f "$LOCK" ]; then
  STALEPID=$(cat "$LOCK" 2>/dev/null)
  echo "  INTERRUPCIÓN: lock stale PID=$STALEPID en celda $NEXT" >> "$LOG"
  DIR=$EVID/reboot_${TS}_${NEXT}; mkdir -p "$DIR"
  # 3a) EVIDENCIA forense
  powershell -NonInteractive -Command "Get-WinEvent -FilterHashtable @{LogName='System'; Id=41,1001,6008; StartTime=(Get-Date).AddHours(-12)} -ErrorAction SilentlyContinue | Select-Object TimeCreated,Id,ProviderName,Message | Format-List" > "$DIR/eventlog.txt" 2>&1
  tail -60 "$AD/nivel3_fullrun_vram_1s.log" > "$DIR/vram_tail.txt" 2>/dev/null
  grep '^2026' "$AD/nivel3_fullrun_vram_1s.log" 2>/dev/null | sed 's/,/ /g' | awk '{print $2}' | sort -n | tail -1 > "$DIR/vram_peak_MiB.txt" 2>/dev/null
  powershell -NonInteractive -Command "try { \$d = Get-ChildItem 'C:\Windows\Minidump\*.dmp' -ErrorAction Stop | Sort-Object LastWriteTime | Select-Object -Last 1; if (\$d){ Copy-Item \$d.FullName '$DIR\\' -ErrorAction Stop; 'copiado '+\$d.Name } else {'sin dmp'} } catch { 'minidump no accesible sin admin: '+\$_.Exception.Message }" > "$DIR/minidump_status.txt" 2>&1
  tail -30 "$AD/nivel3_full_run.log" > "$DIR/run_log_tail.txt" 2>/dev/null
  echo "celda=$NEXT ts=$TS sellados=$N/13 stale_pid=$STALEPID" > "$DIR/context.txt"
  echo "  evidencia -> $DIR" >> "$LOG"
  # 3b) CONTADORES (per-celda + global)
  CELLN=$(grep -E "^$NEXT " "$STATE" 2>/dev/null | awk '{print $2}'); CELLN=${CELLN:-0}; CELLN=$((CELLN+1))
  { grep -vE "^$NEXT " "$STATE" 2>/dev/null; echo "$NEXT $CELLN"; } > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  GN=$(cat "$GLOBAL" 2>/dev/null); GN=${GN:-0}; GN=$((GN+1)); echo "$GN" > "$GLOBAL"
  echo "  contador celda $NEXT=$CELLN/$MAX_CELL ; global=$GN/$MAX_GLOBAL" >> "$LOG"
  # 3c) ALERTA (local siempre; Telegram si hay token)
  MSG="NIVEL3 TDR/reboot: celda=$NEXT reboot#$GN (esta celda $CELLN/$MAX_CELL). Evidencia $DIR. Sellados $N/13. $TS"
  echo "$MSG" > "$EVID/ALERT_${TS}.txt"
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    curl -s --max-time 15 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$MSG" >> "$LOG" 2>&1 && echo "  alerta Telegram enviada" >> "$LOG"
  else echo "  [alerta] sin TELEGRAM_* -> alerta local $EVID/ALERT_${TS}.txt" >> "$LOG"; fi
  # 3d) LÍMITES -> STOP (no relanzar, rompe bucle determinista)
  if [ "$CELLN" -ge "$MAX_CELL" ]; then
    echo "  *** STOP T3.4-bis: celda $NEXT crashea $CELLN veces = DETERMINISTA. Intervención manual. ***" >> "$LOG"
    echo "STOP-DETERMINISTA celda=$NEXT $CELLN/$MAX_CELL" >> "$EVID/ALERT_${TS}.txt"; disable_autostart; exit 10; fi
  if [ "$GN" -ge "$MAX_GLOBAL" ]; then
    echo "  *** STOP T3.4-ter: $GN reboots totales = frecuencia anómala. Revisar. ***" >> "$LOG"
    echo "STOP-FRECUENCIA global=$GN/$MAX_GLOBAL" >> "$EVID/ALERT_${TS}.txt"; disable_autostart; exit 11; fi
  rm -f "$LOCK"
fi

# 4) sanity toolchain antes de confiar GPU (precedente is_available=False por paths post-reboot)
if ! python -c "import lab_cuda; lab_cuda._setup_cuda_paths(); from numba import cuda; import sys; sys.exit(0 if cuda.is_available() else 1)" >> "$LOG" 2>&1; then
  echo "  [WARN] cuda.is_available()=False tras reboot -> NO relanzo (diagnóstico Ricardo)" >> "$LOG"; exit 2; fi

# 5) relanzar (resume-skip continúa desde $N sellados; driver re-ata monitor 1s+fsync)
if [ "$DRY" = "1" ]; then echo "  [DRY] relanzaría: bash $AD/nivel3_full_run_driver.sh ($N/13, celda $NEXT)" >> "$LOG"; exit 0; fi
echo "  relanzo driver ($N/13 sellados, celda $NEXT) $TS" >> "$LOG"
bash "$AD/nivel3_full_run_driver.sh" >> "$LOG" 2>&1
echo "  driver terminó/murió rc=$? $(date -u)" >> "$LOG"
