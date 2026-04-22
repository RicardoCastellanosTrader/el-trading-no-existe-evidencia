# Runbook reciclaje productivo — post-sesión 2026-04-23

Guía operacional para ejecutar `master.py --recycle` con el pipeline mejorado tras la sesión 2026-04-23 (9 items §13.3 RESUELTOS). Escrita para ser auto-contenida: desde estado requerido hasta deploy de nuevos specialists al VPS.

---

## 0. Scope del reciclaje — DECISIÓN PREVIA

Antes de ejecutar reciclaje, decidir qué mejoras se incluyen. Tres opciones según §9.3 y §9.4 del CONTEXTO:

### Opción α — Reciclaje con pipeline de hoy

**Scope**:
- Mejoras sesión 2026-04-23: W3 + W4 + A12 + A13 + A14 + A15 + A04 + A04b + A05.
- Sin features nuevas. Sin v2.5 Walk-Forward Continuo. Sin v2.6 Funding Rate Filter. Sin Z_ATR GMM.

**Tiempo**:
- Preparación: sistema ya listo post-sesión 2026-04-23.
- Compute: ~15 días walk-forward estándar.
- Total hasta deploy: ~15-20 días desde activación.

**Ventaja**:
- Ejecutable inmediatamente.
- Valida mejoras de sesión 2026-04-23 en producción.
- Genera datos empíricos que informarán siguiente reciclaje.

**Desventaja**:
- Reciclaje "incompleto" respecto a roadmap v3.0 original.
- Requiere reciclaje posterior para features restantes.

### Opción β — Reciclaje completo v3.0

**Scope**:
- Todo α + mejoras §9.3 + §9.4:
  - v2.5 Walk-Forward Continuo (infraestructura monitoring semanal).
  - v2.6 Funding Rate Filter (brain bloquea entradas funding extremos).
  - v3.0 Z_ATR como feature GMM (añade feature training + subsume "cortafuegos BTC").
  - BTC Override evolución binario → BIC → Bayesiano según §9.4.

**Tiempo**:
- Implementación adicional: 5-10 sesiones dedicadas.
- Validación empírica multicolinealidad Z_ATR (BIC test).
- Compute walk-forward: +15 días tras implementación.
- Total hasta deploy: 6-10 semanas desde activación.

**Ventaja**: reciclaje único con todas las mejoras del roadmap.

**Desventaja**:
- Bundle grande. Si falla alguna feature, debug complejo.
- Timeline largo contradice "cuanto antes".
- Z_ATR GMM feature crítica sin datos empíricos previos sobre sistema α → arriesgado calibrar a ciegas.

### Opción γ — Híbrida recomendada

**Scope**:
- α ahora (reciclaje con pipeline de hoy).
- Entre α y β: implementar v2.6 Funding Filter (NO requiere reciclaje, es filtro runtime brain + precondición analyzer observabilidad funding).
- β posterior con v2.5 + Z_ATR GMM + BTC override.

**Timeline**:
1. Ejecutar α: ~15-20 días hasta deploy.
2. Monitoreo α + implementación v2.6 funding filter paralelo.
3. Monitoreo N≥50 trades post-α para datos empíricos.
4. Implementación v2.5 + Z_ATR + BTC override (calibrados con datos α).
5. Ejecutar β: calibración más robusta basada en α.

**Ventaja**:
- Balance entre "cuanto antes" y "con mejoras".
- Datos empíricos de α informan diseño β.
- v2.6 funding se beneficia sin esperar reciclaje.
- Evita bundle monolítico arriesgado.

**Desventaja**:
- Dos reciclajes en lugar de uno.
- Mayor compute total.

### Criterio recomendado

| Prioridad | Opción |
|---|---|
| "Validar mejoras de hoy cuanto antes" | **α** |
| "Todo junto no importa tiempo" | **β** |
| "Balance pragmático con calibración empírica" | **γ** |

**Decisión Ricardo pre-ejecución**. Inventario mejoras pendientes §9.3 y §9.4:

| Mejora | Ubicación CONTEXTO | Estado | Scope |
|---|---|---|---|
| v2.4 Performance Attribution | §9.3 | ✅ Implementado (analyzer v2.4.1) | α |
| v2.5 Walk-Forward Continuo | §9.3 | ❌ Pendiente | β |
| v2.6 Funding Rate Filter | §9.3 | ❌ Pendiente (§13.3 observabilidad + filtro runtime 2026-04-23) | β (o intercalado γ) |
| v3.0 Z_ATR GMM | §9.4 | ❌ Pendiente | β |
| BTC Override evolución | §9.4 | ❌ v1 binario actual | β |

Tras decisión α/β/γ, continuar con Sección 1.

---

## 1. Estado requerido pre-reciclaje

**Sistema**:
- Bot v2.4.5 operacional en VPS Tokio (INSTANCE_ID_TOKIO_REDACTADO, IP_VPS_TOKIO_REDACTADA).
- `trading-bot.service` Restart=on-failure activo, no procesos duplicados.
- Kernel host 6.17.0-1012-aws, APT window xx:15-xx:45 UTC.
- Balance/posiciones estables (consultar con `ssh trader@IP_VPS_TOKIO_REDACTADA 'tail -n 50 /home/trader/combolab/logs/engine.log'`).

**Repositorio**:
- Rama main con últimos commits mergeados. Hoy 2026-04-23 último commit esperado: `09b01f6` (docs A04b) o posterior al commit cierre de sesión.
- Regresión 34/34 tests PASS (`tests/test_*.py`).
- Smoke test §0.8 los 3 niveles PASS pre-reciclaje (ver Sección 10).

**Items §13.3 activos que afectan reciclaje**:
- W3 bootstrap pf_fwd + flag_sospechoso → activo en `regime_walk_forward.py`.
- W4 thresholds _FWD (25/1.1 + NOT sospechoso) → activo.
- A14 plateau_ratio consistency con `_get_neighbors` → activo (metadata informativa).
- A15 engine tag en parquet → activo (telemetría + resume check).
- A12 MAs dedup lab_lite ↔ lab_historico → activo.
- A13 LL2 ratio supervivencia saludable (36.7% mean) → validado sin fix.
- A05 MR zone_bull_mr helpers + docstring + dead fields deprecated → activo.
- A04 + A04b Fidelidad 1 TF + MR auditorías completadas → documentales.

---

## 2. Precondiciones hardware y compute

- **Hardware local**: RTX 5070 Laptop GPU (CUDA 12.0, Compute 12.0, 256 threads/block). Confirmar GPU visible: `nvidia-smi` o boot de `regime_walk_forward.py` que imprime `[CUDA] Aceleración GPU habilitada: NVIDIA GeForce RTX 5070 Laptop GPU`.
- **Fallback CPU**: Numba CPU si CUDA no disponible. A15 engine tag persiste en parquet — verificar `engine_name="cuda"` o `"cpu_numba"` tras primer part file generado.
- **Compute esperado**: walk-forward completo 45 símbolos × 3 clusters × miles de variants ~ días (según runs históricos). Dependiente de presets × n_bars × configs.
- **Ventana temporal recomendada**: iniciar por la noche o fin de semana para permitir ejecución desatendida con monitoreo diario de progreso.
- **Espacio disco**: `regime_wf/_parts_*/` genera parquets intermedios ~cientos MB total. `data_cache/*_1h.parquet` ya descargado, ~100MB total 45 símbolos.

---

## 3. Variables clave a decidir pre-ejecución

| Variable | Default actual | Decisión reciclaje |
|---|---|---|
| Símbolos | 45 según `master.py CONFIG` | Revisar si alguno a archivar/añadir |
| Data ventana training | ~2 años histórico BingX | Considerar ventana hasta ~día reciclaje |
| Seed bootstrap W3 | `_BOOTSTRAP_SEED = 42` | Fijar para reproducibilidad (ya hardcoded) |
| W4 thresholds | trades≥25, pf≥1.1, NOT sospechoso | Mantener (empíricamente validado 134/138 operable) |
| W4 hooks opcionales | `_FWD_MIN_CI_LOW=0.0`, `_FWD_MAX_CI_WIDTH=inf` (OFF) | Dejar OFF (redundante con NOT sospechoso) |
| Toxic tail | Modo dinámico, confirm=0.75 | Mantener |
| TOP_N_PRESETS lab_lite | 7 globales + 3 per-cluster | Mantener (A13 ratio supervivencia 36.7% saludable) |
| Engine | Autodetect CUDA con fallback CPU | Usar CUDA si disponible |

---

## 4. Comandos de ejecución

### Opción A — Reciclaje completo orquestado por master.py

```bash
cd c:/Users/rixip/combolab
python master.py --recycle
```

Flag `--recycle` fuerza re-generación de todo el pipeline: download → train_regime → lab_lite → regime_walk_forward.

### Opción B — Ejecución por pasos con resume capability

```bash
# Step 1 — Download (solo si se cambia ventana data)
python master.py --step download

# Step 2 — Entrenar GMMs
python master.py --step regime

# Step 3 — Generar presets (lab_lite)
python master.py --step lite

# Step 4 — Walk-forward con W3+W4 activos
python master.py --step regime-wf
```

Resume automático si `regime_wf/_parts_*/part_XXXX_CK.parquet` ya existen — engine consistency check A15 emitirá WARN loud si parquets previos fueron generados con engine distinto al actual.

### Opción C — Subset único símbolo (test)

```bash
python master.py --symbols ONDO/USDT --recycle
```

Útil para validar pipeline tras cambios antes de correr los 45.

---

## 5. Criterios aceptación post-reciclaje

Antes de deploy de nuevos specialists al VPS:

- [ ] Walk-forward completó sin crashes (exit 0 en todos los símbolos).
- [ ] 45/45 JSONs generados en `regime_wf/*_specialist_configs.json`.
- [ ] 40+ símbolos con specialists operables en los 3 clusters (baseline actual 42/45 según A13 simulación).
- [ ] 0 símbolos con 0 clusters operables.
- [ ] W3 bootstrap aplicado: campos `pf_fwd_ci_low, pf_fwd_ci_high, ci_width, flag_sospechoso_outlier` presentes en top_configs.
- [ ] W4 filtros: top_configs seleccionados reflejan `NOT sospechoso` (ningún top-1 productivo con `flag_sospechoso_outlier=True`).
- [ ] Ratio `flag_sospechoso/total` per cluster <30% (baseline walk-forward saludable).
- [ ] Selección por `specialist_score_ci_low` (W3b sort) vs point estimate — verificar en reporte text.
- [ ] A15 engine tag presente en parquets: `engine_name` ∈ {"cuda", "cpu_numba"}, `timestamp_run` ISO reciente.
- [ ] Smoke test §0.8 3 niveles PASS con nuevos specialists cargados:
  - Nivel A BTC N=1000 diff 0.0000 exacto 5 métricas.
  - Nivel B ONDO+APT N≥8000 match >95%, ratio bar-level <5% o dentro baseline ~7-9%.
  - Nivel C SEI MR diff 0.0000 en 7 métricas.
- [ ] Analyzer dry-run sobre nuevos specialists + última ventana data del bot: alpha esperado coherente, sin WARNs inesperados.

---

## 6. Plan contingencia si falla

### Fallo 1 — Walk-forward crash parcial
- Recovery: `python master.py --step regime-wf` sin `--recycle` (usa resume).
- A15 emitirá WARN `A15 RESUME ENGINE MISMATCH` si el engine difiere. Decidir:
  - Continuar con mixto (heterogeneidad silenciosa): NO recomendado.
  - Restart clean: eliminar `regime_wf/_parts_*/` y re-correr desde cero con engine consistente.

### Fallo 2 — <35 símbolos operables post-W4
- Causa probable: régimen de mercado muy distinto a ventana training → W4 filtros demasiado estrictos para data actual.
- Acción: revisar distribución `flag_sospechoso` por cluster. Si >50% flagged globalmente, considerar:
  - Acortar ventana training (última ~1 año en lugar de ~2).
  - Relajar hooks W4 manualmente (`_FWD_REQUIRE_NOT_SOSPECHOSO=False`) — pero esto introduce ruido ci_width>5.
- Si persiste: aceptar operación reducida y monitorear con bot post-deploy.

### Fallo 3 — Ratio flag_sospechoso >50% global
- Problema metodológico: el bootstrap binomial es lower bound de CI real (caveat §12 Lección 29). Si >50% de top-1000 configs per cluster quedan flagged, el problema es de data (N_fwd pequeño sistemáticamente) no de W3.
- Acción: investigar si ventana training produce N_fwd>50 típico. Si no, extender data training.

### Fallo 4 — Smoke test Nivel B ratio muy fuera baseline (>15-20%)
- Regresión brain/kernel introducida por cambio en pipeline.
- Acción: rollback a specialists v2.4.5 actuales.
- Investigar cambios en `lab_historico_numba_v8_3.py` o `live/brain_engine.py` que pudieran afectar path brain↔kernel.
- NO deploy hasta reconciliación.

### Fallo 5 — Crash inesperado Numba compile
- Numba 0.64.0 es versión actual (L_NUMBA_VERSION en A15). Si actualización Numba rompe jit:
  - Revisar @jit(nopython=True, parallel=True) compatibility con nueva versión.
  - Rollback `pip install numba==0.64.0` y re-correr.

---

## 7. Items pendientes post-reciclaje (para próximos ciclos)

De los items §13.3 que quedaron EN_ESPERA tras sesión 2026-04-23:

- **Cooldown asimétrico TF+MR** (POT INVOLUNTARIA única detectada en A04+A04b). Pre-reciclaje NO urgente (impacto bajo con `cooldown_bars=1`). Considerar pre-v3.0 reciclaje: investigar intención diseño, unificar o documentar asimetría.
- **A30 hidden divergence asimetría TF vs MR**: diferido a v3.0 por scope arquitectónico mayor (67/138 configs afectados, requiere test diferencial pre/post con simulador swap TF↔MR).
- **B2 prev_zone asimetría TF vs MR** + **B3 TF locals vs MR state directo div_ctx**: §13.3 difdridos a v3.0.
- **P1 portfolio leverage**: proyecto separado, balance >1000 USDT.
- **Otros §13.3 EN_ESPERA dormidos**: revisar inventario antes próximo ciclo.

---

## 8. Deploy nuevos specialists al bot productivo

**Protocolo (referencia §0.7 CONTEXTO sync combolab ↔ VPS)**:

1. **Backup specialists actuales en VPS**:
   ```bash
   ssh ubuntu@IP_VPS_TOKIO_REDACTADA
   sudo cp -r /home/trader/combolab/regime_wf /home/trader/combolab/regime_wf.bak-$(date +%Y%m%d)
   ```

2. **scp nuevos JSONs**:
   ```bash
   scp combolab/regime_wf/*.json trader@IP_VPS_TOKIO_REDACTADA:/home/trader/combolab/regime_wf/
   ```

3. **Restart trading-bot.service**:
   ```bash
   ssh ubuntu@IP_VPS_TOKIO_REDACTADA
   sudo systemctl restart trading-bot.service
   sudo systemctl status trading-bot.service
   ```

4. **Smoke-A** (boot limpio + N posiciones sincronizadas):
   ```bash
   tail -f /home/trader/combolab/logs/engine.log | head -50
   # Verificar: [ENGINE_STATE] con n_open = posiciones esperadas.
   # Verificar: no CRITICAL en primer minuto post-boot.
   ```

5. **Smoke-B** (primer cycle post-deploy):
   - Esperar a próximo xx:00 UTC.
   - Verificar ciclo completo sin crash + BRAIN_RECONCILE esperados (§13.2).
   - Cycle duration <30s.

6. **Monitoreo 24-48h primer cycles reales con nuevos specialists**:
   - Telegram alerts activas (§7.5).
   - Daily summary 00:00 UTC confirma PF real vs esperado.
   - `health_monitor` debe mostrar `days_since_recycle=0` tras update de `last_recycle.txt`.

---

## 9. Referencias

- **§0.8 CONTEXTO**: protocolo smoke test pre-deploy 3 niveles.
- **§13.4 2026-04-23**: 9 items RESUELTOS en sesión previa al reciclaje.
- **A15 engine tag**: `regime_walk_forward.py:56-128` para reproducibilidad cross-machine.
- **W3 bootstrap**: `regime_walk_forward.py:930-1030` para CI pf_fwd.
- **W4 filtros**: `regime_walk_forward.py:923-932` (thresholds) + `_apply_w4_fwd_ci_filters`.
- **A12 MAs dedup**: `lab_lite_zonas_v5e.py:112-132` importa desde `lab_historico`.
- **A05 zone helpers**: `mean_reversion_features.py:213-282` single source of truth zonas MR.

---

## 10. Cuándo ejecutar reciclaje

**Criterio calendario §13.3 política**: `last_recycle.txt` + 90 días triggers reciclaje calendario automático. Actual `last_recycle.txt = 2026-04-08` → trigger calendario 2026-07-07.

**Criterio empírico §13.3 política adelantar reciclaje**:
- 5+ clusters cruzando ratio_oos/pool < 0.5 con N≥3.
- O alpha residual <-50% del alpha nominal en ventana 30d con N≥30.
- O PnL cumulativo turn negativo en ventana 30d con N≥30.
- O 3+ clusters flagged candidato_exclusion sostenido en 2+ reportes consecutivos.

**Estado actual 2026-04-23**: 3 clusters flagged en §13.4 Fase II.C (ONDO C0, ONDO C2, SAND C1). Alpha residual -68% del nominal (cerca trigger -50%). PnL aún positivo. Veredicto: NO disparar reciclaje todavía, monitorear 7-14 días.

**Recomendación Ricardo 2026-04-23**: "cuanto antes posible". Acciones:
1. Acumular N≥50 trades post-v2.4.5 (~2026-04-26 a 2026-05-01).
2. Ejecutar analyzer + audit v5.2 sobre ventana fresca con nuevos data.
3. Evaluar si triggers empíricos se cruzan.
4. Si sí: adelantar reciclaje aprovechando pipeline mejorado (W3+W4+A12+A13+A14+A15+A04+A04b+A05).
5. Si no: mantener calendario julio 2026.

**Decisión previa obligatoria**: scope α/β/γ según Sección 0. Recomendación técnica default: **γ híbrida** (α inmediato + v2.6 funding filter intercalado + β posterior con calibración empírica). Sujeto a decisión Ricardo.

**Ventana ejecución óptima**: fin de semana con Ricardo monitoreando primeras ~4-6h para detección temprana de fallos.

---

## Checklist mental pre-ejecutar

- [ ] Estado sistema verificado (Sección 1).
- [ ] Hardware/compute disponible (Sección 2).
- [ ] Variables decisión confirmadas (Sección 3).
- [ ] Smoke test §0.8 3 niveles PASS pre-reciclaje.
- [ ] Backup specialists actuales VPS listo para rollback.
- [ ] Ventana ejecución suficiente (24-48h monitoreo).
- [ ] Criterios aceptación claros (Sección 5).
- [ ] Plan contingencia comprendido (Sección 6).

Si todo ✅: ejecutar `python master.py --recycle`. Monitorear logs cada 1-2h primeras 12h.
