# RUNBOOK — Etapa 4 PAPER (Kraken Futures demo) — validación de fidelidad de EJECUCIÓN

**Rama:** `migracion-kraken` · **Instancia:** Irlanda `INSTANCE_ID_IRLANDA_REDACTADO` (`IP_VPS_IRLANDA_REDACTADA`, eu-west-1) · **Servicio:** `kraken-paper.service`
**Precondición de entrada:** demo API a 200 + `_verify_demo_safety.py` = `DEMO_SAFE_OK` sobre API viva + servicio arrancado (ver RUNBOOK DE REANUDACIÓN en `project_kraken_migration_viability_audit`).

> ⚠️ **ANTES de arrancar paper — re-scp obligatorio.** El deploy de Irlanda es una **copia scp**, NO un checkout git (la instancia no tiene git-auth). Cualquier cambio de código en la rama `migracion-kraken` posterior al último scp **NO está en la instancia**. Re-copiar los `.py` cambiados (al menos `live/` + raíz tocada) ANTES de `systemctl start`, o se arrancaría paper con **código viejo**. Verificar tras el scp: `ssh ... 'cd ~/combolab && git --version 2>/dev/null; md5sum live/data_feed.py'` y comparar con el local. (Cambios 2026-06-25 pendientes de re-scp: `live/data_feed.py` get_balance observabilidad.)

DRY_RUN-prod (lectura/cálculo: datos 20/20, clasificación, sizing DOGE 3003 entero) **YA validado**. Etapa 4 valida lo único que el demo aporta: **EJECUCIÓN real en libro ficticio** (fills, stops, balance, fee). `validate` NO existe en Futures (verificado primary-source 2026-06-25) → no hay escalón intermedio; el demo es el único validador de ejecución.

Duración esperada: unos días de operación paper (que entren/salgan posiciones reales en demo). Gate de salida: los 4 objetivos CONFIRMED + caminos críticos sin sorpresa → Tier 3 decisión Ricardo de escalar a live (clave producción separada).

---

## Cómo observar (común a todos)
```bash
ssh -i ~/.ssh/kraken_paper ec2-user@IP_VPS_IRLANDA_REDACTADA \
  'sudo journalctl -u kraken-paper.service --no-pager -n 200'
```
Marcadores de log relevantes: `[EXEC]`, `[S2_FLUSH]`, `[BALANCE]`, `[ORPHAN_FILL]`, `[ORPHAN_CLOSE]`, `[EMERGENCY_STOP_*]`.

---

## Objetivo 1 — ¿la protección 1% (IOC `mkt`) afecta a stops/cierres disparados?
**Qué se valida:** si el `mkt` IOC con price-protection 1% de Kraken llena PARCIAL en un gap >1%, dejando residual. Determina si el flush S2-lite (`_flush_residual`) es realmente necesario o redundante.
**Procedimiento:**
1. Observar cierres reales (CLOSE on-close del brain) y stops disparados (`stp` reduce-only) durante la operación paper.
2. Buscar en log `[S2_FLUSH] ... residual ... tras cierre` → significa que el cierre primario dejó residual (1% mordió).
3. Provocación opcional controlada: en un símbolo de baja liquidez/alta vol, observar si algún cierre deja residual.
**PASS si:** o bien (a) nunca aparece residual (la protección 1% no muerde en cierres reduce-only → flush es no-op defensivo, OK), o bien (b) aparece residual y el flush lo aplana en ≤3 intentos (`_flush_residual -> True`). 
**FAIL si:** `[S2_FLUSH] residual PERSISTE tras 3 intentos` recurrente → el `mkt` IOC no basta para cerrar; evaluar subir `max_attempts` o usar otra `orderType` de cierre. Documentar.

## Objetivo 2 — forming-bar de `charts/v1` = `iloc[-1]`
**Qué se valida:** que la última vela devuelta por el feed Kraken (`charts/v1`) es el bar EN CURSO (forming), igual que la convención que el brain/kernel asume (decide-y-entra con close[t] del bar en formación). Heredado de la Fidelidad 2 de BingX.
**Procedimiento:**
1. En dos ciclos consecutivos, comparar el timestamp de `iloc[-1]` de un símbolo con la hora del ciclo.
2. Confirmar que `iloc[-1].timestamp` == hora del bar actual (forming), no el último cerrado.
**PASS si:** `iloc[-1]` es el bar en curso de forma consistente (mismo contrato que kernel). 
**FAIL si:** `iloc[-1]` es el último bar CERRADO → habría desfase de 1h vs simulación; ajustar el feed (append/replace del forming, análogo a Fidelidad 2 BingX en `data_feed`).

## Objetivo 3 — `fetch_balance` multi-collateral (USD free)
**Qué se valida:** que `get_balance` devuelve el capital operable correcto en la cuenta demo (fondeada en USD). Multi-collateral PF_ puede anidar la estructura distinto.
**Procedimiento:**
1. Primer ciclo: revisar log `Balance USD — total: X, libre: Y`.
2. **Señal de alarma (hardening 2026-06-25):** si aparece `[BALANCE] colateral USD/USDT/USDC = 0. ¿Estructura multi-collateral distinta...? Monedas con entrada: [...]` → ccxt anida el balance bajo otra clave; el sizing NO abriría nada.
**PASS si:** `total`/`free` USD coinciden con el fondeo demo y el sizing usa `free` como capital. 
**FAIL si:** salta el warning all-zero → mapear la clave real que reporta el warning y ajustar la selección de wallet en `get_balance` (data_feed.py ~568).

## Objetivo 4 — fee real vs estimación ccxt
**Qué se valida:** el fee que registramos. Hoy `get_recent_closed_fill` usa `fee.cost` que ccxt SINTETIZA como `rate×cost` (estimación con tasa estática), NO el fee real cobrado. El fee real vive en un endpoint `account-log` separado.
**Procedimiento:**
1. Tras cierres reales, comparar `fee_usdt` registrado (estimación ccxt) con el fee real del account-log de la cuenta demo.
2. Medir la desviación.
**PASS si:** la desviación es tolerable para el análisis de fidelidad, o se documenta el sesgo conocido. 
**Mejora futura (no bloqueante paper):** alimentar el fee real desde account-log si la desviación es material.

---

## CAVEAT NUEVO (flag 2026-06-25, validar en paper antes de confiar en PnL de ORPHAN_CLOSE)
**`get_recent_closed_fill` devuelve SOLO el fill más reciente** (`max by timestamp`). Si un cierre exchange-side (SL trigger / liquidación / cierre manual) se llena en **múltiples tramos** (p.ej. protección 1% parcial → segundo fill del flush, o SL filled en tranches), el PnL/fee de ORPHAN_CLOSE quedaría **SUBESTIMADO** (solo cuenta el último tramo).
- **NO reescribir a ciegas** (necesita datos demo para validar la semántica de agregación — norma del proyecto: validación empírica antes de implementar).
- **Validar en Objetivo 1:** si los cierres reales son single-fill (lo esperado para `mkt` IOC que llena de golpe), el caveat es inerte. Si se observan cierres multi-fill → implementar agregación (sumar amount/cost/fee de todos los fills del cierre dentro de la ventana `since_ms`, no solo el último) y añadir test.

---

## Invariantes durante Etapa 4
- Tokio `INSTANCE_ID_TOKIO_REDACTADO` STOPPED = red de seguridad, NO eliminar hasta validar Irlanda + decisión operar.
- Clave demo = read+trade SIN retirada. Transferencias = mano de Ricardo.
- Cualquier cambio de código en la rama requiere **re-scp a Irlanda** antes de reiniciar el servicio (el deploy de Irlanda es copia scp, no git).
- Gate de salida = Tier 3 Ricardo (escalar a live con clave producción separada).
