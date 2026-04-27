# Auditoría exhaustiva pre-reciclaje + decisión AGGRESSIVE pura recalibrada — 2026-04-27 Sesión 2 D

**Estado**: PLANIFICACIÓN INSTITUCIONAL PERMANENTE.

**Contexto sesión**: Sesión 2 día 2026-04-27 reformuló timing categórico items "post-reciclaje" bajo enfoque Ricardo "al margen de lo que cueste, aspirar a lo mejor reciclaje". Sesión 1 día cerró con 5 commits + estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1+TRIAJE+AUDIT-RESCATE. Plan original Sesión 1 Fase 5: deploy L1892+L1904 + Refactor audit_v5.x ~2026-05-05 a 05-10 + reciclaje 45 sym ~2026-05-12 a 05-22 (~10 días total pre-reciclaje minimalista).

Pregunta crítica Ricardo Sesión 2: reciclaje cuesta 15 días + bot opera JSONs obsoletos + reciclaje oportunidad única → pre-reciclaje debe resolver gaps simulado↔operacional ANTES de regenerar specialists, no después. Items "post-reciclaje" categóricos pueden ser pre-reciclaje bajo este enfoque.

Decisión Ricardo confirmada: opción A "aspirar a lo mejor reciclaje" con D auditoría exhaustiva PREVIA como prerequisito metodológico.

**Bot v2.4.5 invariante uptime 5d 3h+ durante Sesión 2 D**. Sin tocar `live/*`. Sin compute productivo. Read+write sobre CONTEXTO + ROADMAP + docs.

---

## 1. Inventario gaps simulado↔operacional G1-G5 (Parte 0)

### Categorización gaps

**G1 — Gaps Fidelidad 1** (lab simula ≠ bot haría):
- G1.1 Tier 0 I1 kernel reason_exit per-trade arrays (L2910)
- G1.2 Bloque 2c granular H1+H_funding+H_strategy cross-régimen (L2910 sub)
- G1.3 Lab compute_leverage_map fix → lev=1 always docstring (L2370 + ROADMAP)
- G1.4 Hidden divergence asimetría TF↔MR 67/138 configs (L2434)
- G1.5 Análisis B edge decay cross-cluster JSON WF→kernel-actual (L2967)

**G2 — Gaps Fidelidad 2** (bot replica ≠ lab simuló):
- G2.1 Refactor audit_v5.x herramienta auditor (L1781) — ya rescatado sesión 1 Fase 5
- G2.2 Test diferencial brain↔kernel histórico Smoke Nivel B sistemático (L2476)

Ya RESUELTOS previo a Sesión 2 D: size_usdt v2.4.4 + entry_timestamp_ms v2.4.5 + TS divergence v2.4.0 + R1 cooldown 2026-04-22 + lag estructural v2.3.11.

**G3 — Gaps Selección Specialists** (walk-forward bias):
- G3.1 Walk-forward Mecanismos 3+4 hipotético-driven (L2847+L2865)
- G3.2 Deflated SR core formula + validación cross-9 (post-reciclaje archivado, subset rescatable)
- G3.3 k-fold CV walk-forward subset (post-reciclaje archivado, subset rescatable)

Ya resueltos: M1 W3+W4 + M2 fix ranking pf_fwd_ci_low directo. Multi-testing classical CASO B archivado empírico.

**G4 — Gaps Régimen Mercado**:
- G4.1 Edge erosion descriptivo N=60 — caracterización no accionable

**G5 — Gaps Operacionales**:
- G5.1 Deploy L1892+L1904 multipliers SIGNALS_DISCARDED (L3003)
- G5.3 brain prev_zone B2 + TF locals B3 (L2403+L2416)
- G5.4 brain _evaluate_bar duplicación (L2466)
- G5.6 data_feed attach stops redundante (L2274)
- G5.7 execution funding fallback signo invertido (L2302)
- G5.8 execution ejecución parcial reconcile (L2510)
- G5.9 portfolio vol_weight neutraliza dd_multiplier (L2360)
- G5.10 portfolio block_reduction 3 factores (L2383)
- G5.11 portfolio correlación min_len bajo silencioso (L2393)

### Tabla principal gaps

| # | Cat | Item | Estado | Pre-reciclaje viable? | Scope | Riesgo |
|---|-----|------|--------|----------------------|-------|--------|
| G1.1 | F1 | Tier 0 I1 kernel reason_exit | EN_ESPERA "post-reciclaje" | **SÍ candidato fuerte** | 15-20h humano / 2-4h CC | Medio |
| G1.2 | F1 | Bloque 2c granular cross-régimen | EN_ESPERA "post-reciclaje" | **SÍ condicional G1.1** | 5-10h humano / 1-2h CC | Bajo |
| G1.3 | F1 | Lab compute_leverage_map fix | ARCHIVED bajo P1 (b) | **SÍ ESENCIAL** | 2-4h humano / 30-45min CC | Bajo |
| G1.4 | F1 | Hidden divergence asimetría TF↔MR | EN_ESPERA v3.0 | **NO viable** | >20h | Alto |
| G1.5 | F1 | Análisis B edge decay | EN_ESPERA viability blocker | **NO viable** (post-training ≥60d) | 1-2h ejec | Bajo |
| G2.1 | F2 | Refactor audit_v5.x Op A | EN_ESPERA — RESCATADO | **SÍ confirmado** | 4-12h humano / 1-2h CC | Medio |
| G2.2 | F2 | Smoke §0.8 Nivel B sistemático | EN_ESPERA | **SÍ obligatorio** | 1-2h humano / 15-30min CC | Bajo |
| G3.1 | F3 | Walk-forward Mec 3+4 hipotético | EN_ESPERA scope abierto | **CONDICIONAL** hipótesis | varía | Bajo |
| G3.2 | F3 | Deflated SR core subset | post-reciclaje archivado | **SUBSET** ~10-15h humano / 2-3h CC | Bajo |
| G3.3 | F3 | k-fold CV subset | post-reciclaje archivado | **SUBSET** ~10-15h humano / 2-3h CC | Bajo |
| G4.1 | Régimen | Edge erosion descriptivo | NO accionable | **NO directo** | N/A | N/A |
| G5.1 | Op | Deploy L1892+L1904 | EN_ESPERA fecha límite | **SÍ confirmado** | 0.5-1h humano / 10min CC | Bajo |
| G5.3 | Op | brain prev_zone B2 + TF locals B3 | EN_ESPERA reciclaje julio | **CONDICIONAL aggressive** | 14-20h humano / 3-5h CC | Medio |
| G5.4 | Op | _evaluate_bar duplicación | EN_ESPERA disparador 1/2 | **DIFERIR post** | 8-12h | Medio |
| G5.11 | Op | portfolio correlación min_len | EN_ESPERA inminente reciclaje | **OPCIONAL** | 0.5-1h humano / 10-20min CC | Bajo |

---

## 2. Re-evaluación items individual + análisis discriminatorio H_M3-M6 (Parte 1)

### Items core confirmados (6 items)

#### G1.1 Tier 0 I1 kernel reason_exit per-trade arrays — CONFIRMADO FUERTE

**Veredicto**: PRE-RECICLAJE CONFIRMADO FUERTE.

**Scope refinado**: 20-25h humano / **2-4h Claude Code interacción + Smoke compute batch** (~3-5h total CC).

**Componentes**:
- Kernel modify `run_simulation_numba`: arrays pre-alloc per trade — entry_bar[N], exit_bar[N], side[N], pnl[N], reason_exit[N], cluster_at_entry[N]
- Enum reason_exit: 0=tf_exit, 1=div_exit, 2=sl_hit, 3=zone_exit, 4=regime_change, 5=cancel_tf, 6=cancel_mr, 7=sl_emergency
- Signature extension output tuple
- Update 10+ callers
- Update EXPECTED_LAB_KERNEL_HASH audit + checksum regen
- Tests greenfield per-trade tracing
- Smoke §0.8 A+B+C cross-2-3 ciclos debugging esperado

**Riesgos**: F1 transitorio + update callers incompleto + memory overflow arrays per-trade.

**Mitigaciones**: M1.1 tests greenfield ANTES merge. M1.2 grep exhaustivo callers. M1.3 chunked allocation. M1.4 Smoke §0.8 A+B+C obligatorio. M1.5 cross-check verify_test baseline. M1.6 git branch + commits granulares + revert.

**Dependencias**: ninguna. PRECEDE G1.2.

**Valor permanente**: per-trade tracing arquitectónico permanente para audits + analyzer per-reason granular + walk-forward diagnostics + cualquier stress-test arquitectónico futuro con trade-level data.

#### G1.2 Bloque 2c granular H1+H_funding+H_strategy cross-régimen — CONFIRMADO cond G1.1

**Veredicto**: PRE-RECICLAJE CONFIRMADO (condicional G1.1 done).

**Scope refinado**: 5-10h humano / **1-2h Claude Code + ~1-2h compute kernel runs**.

**Componentes**: Fetch Binance 44 sym × 3y OHLCV + funding (cached) + Kernel runs 44 × 3 clusters × top-5 = 660 configs cross-régimen + H1+H_funding+H_strategy per régimen + descomposición BTC macro.

**Riesgos**: none-emergente (replicación refutaciones N masivo) + emergencia hipótesis Mec 3+4 (HIGH-VALUE byproduct >50% probabilidad).

**Mitigaciones**: M2.1 chunked execution + memory monitor. M2.2 hipótesis emergentes documentadas explícitamente input H_M3-M6.

**Dependencias**: G1.1 done obligatorio. NO paralelizable.

**Valor permanente**: caracterización cross-régimen masivo H1+H_funding+H_strategy.

#### G1.3 Lab compute_leverage_map fix — ESENCIAL

**Veredicto**: PRE-RECICLAJE ESENCIAL (timing crítico bajo opción b confirmed 2026-04-27).

**Scope refinado**: 2-4h humano / **30-45 min Claude Code**.

**Componentes**: setear `lev=1` always con docstring P1 opción (b) confirmed 2026-04-27 + caveats reactivación (i)-(v) + tests no-regression walk-forward 1 sym.

**Riesgos**: NULO bot productivo. F1 mejora — sin fix → reciclaje regenera con bug *100.0 + bot 1x = F1 break silencioso permanente.

**Mitigaciones**: M3.1 walk-forward 1 sym smoke validar specialists scores invariantes. M3.2 docstring explícito caveats reactivación.

**Dependencias**: ninguna. INDEPENDIENTE.

**Valor permanente**: F1 invariante post-reciclaje + documentación lab opción (b) consistente.

#### G2.1 Refactor audit_v5.x Opción A — CONFIRMADO

**Veredicto**: PRE-RECICLAJE CONFIRMADO (rescatado sesión 1 Fase 5).

**Scope refinado**: 4-12h humano / **1-2h Claude Code** (Opción A importar kernel directo).

**Riesgos**: regresión audit silenciosa + Opción A breaking stateless property.

**Mitigaciones**: MA.1 tests greenfield pre/post refactor. MA.2 cross-check verify_test ground truth (76 trades 380 mediciones diff 0.0000 baseline 2026-04-26). MA.3 importar kernel funciones puras parametrizadas. MA.4 smoke audit cross-3-símbolos pre/post.

**Dependencias**: ninguna. INDEPENDIENTE.

**Valor permanente**: audit consolidado validable cross-45 JSONs nuevos post-reciclaje.

#### G2.2 Smoke §0.8 Nivel B sistemático — OBLIGATORIO

**Veredicto**: PRE-RECICLAJE OBLIGATORIO (gate inmediato pre-launch).

**Scope refinado**: 1-2h humano / **15-30 min Claude Code ejecución**.

**Comando**: `python -m live.brain_engine --verify --symbol ONDO/USDT --n-bars 8000` + `--symbol APT/USDT --n-bars 10000`

**Dependencias**: post-G1.1 + post-G1.3. Ejecutable múltiples veces.

#### G5.1 Deploy L1892+L1904 — CONFIRMADO

**Veredicto**: PRE-RECICLAJE CONFIRMADO (procedure validada).

**Scope refinado**: 0.5-1h humano / **~10 min Claude Code + procedure VPS**.

**Procedure**: 8 pasos §13.3 L3003 (Smoke Nivel A → systemctl stop → scp → backup mv chown → MD5 3-way → systemctl start → Smoke-A boot → Smoke-B cycle).

### Análisis discriminatorio Walk-forward Mec 3+4 (4 hipótesis)

#### H_M3 Selection bias cross-cluster

**Hipótesis**: top-1 cluster A (config X) y top-1 cluster B (config Y) mismo símbolo usan presets MA correlated. Multi-testing efectivo cross-cluster supera intra-cluster. Inflación pf_fwd cluster-level systematic.

**§12 L34 compatible**: SÍ. Hipótesis específica + testeable + falsifiable.

**Test**: cross-44-sym × C0/C1/C2 top-1 → matriz correlation MA preset families. Si correlación ≥0.5 sistemática → confirmada. Si <0.3 → refutada.

**Pre-requisito**: G1.1 NO requerido. G1.2 cross-régimen N masivo refuerza.

**Scope**: 5-8h humano / **~1h Claude Code + 30 min análisis**.

**Recomendación**: EJECUTAR pre-reciclaje.

#### H_M4 Régimen-temporal bias

**Hipótesis**: top-1 selected sub-window específico régimen GMM BTC no generaliza cross-régimen. Walk-forward fwd window dominado por mismo régimen → pf_fwd inflated localmente.

**§12 L34 compatible**: SÍ.

**Test**: top-1 specialist sobre 9 sym × cross-régimen segmentación BTC macro (3-5 régimenes). PF per régimen distintivo. Si concentración >70% PF en 1 régimen → confirmada.

**Pre-requisito**: G1.1 RECOMENDADO (per-trade reason_exit + segmentación régimen × reason_exit). Sin G1.1 ejecutable subset aggregate-level.

**Scope**: 8-12h humano / **~1h Claude Code + 30 min análisis**.

**Recomendación**: EJECUTAR subset aggregate-level pre-reciclaje. Full granular post-G1.1.

#### H_M5 GMM regime classification noise P_threshold sensitivity

**Hipótesis**: histéresis P≥0.75 GMM cluster threshold borderline. Bars con P~0.75-0.80 misclassified into adjacent cluster K' instead of K real. PF_fwd cluster K inflated por bars borderline mal-clasificados.

**§12 L34 compatible**: SÍ DIRECTAMENTE.

**Test**: re-classify bars con P_threshold ∈ {0.50, 0.65, 0.80, 0.95} sobre 9 sym × 3 clusters × top-1 specialist. PF per threshold. Si PF_fwd cae sustancialmente con threshold más estricto → confirmada.

**Pre-requisito**: NINGUNA. Directamente testeable JSONs actuales + GMM joblib + parquets Binance 3y.

**Scope**: 5-8h humano / **~1h Claude Code + 30-60 min sweep**.

**Recomendación**: EJECUTAR pre-reciclaje DIRECTAMENTE.

#### H_M6 Cross-exchange Binance↔BingX residual

**Hipótesis**: §12 L29 ya identificó contribuidor secundario. Ratio JSON pf_fwd / Binance 3y pf_fwd 4-30× cross-9. Cross-exchange residual contribution medible: kernel runs sobre BingX 3y vs Binance 3y mismo specialist → diff cuantifica cross-exchange.

**§12 L34 compatible**: SÍ DIRECTAMENTE.

**Test**: 9 specialists top-1 (BTC/ONDO/SEI × C0/C1/C2 M2 fix) → kernel runs BingX 3y + Binance 3y. PF per exchange. Diff quantifies cross-exchange residual.

**Pre-requisito**: NINGUNA. Datos disponibles.

**Scope**: 5-10h humano / **~1-2h Claude Code + 30-60 min kernel runs**.

**Recomendación**: EJECUTAR pre-reciclaje DIRECTAMENTE.

### Items subset operacionales

#### G5.3 brain prev_zone B2 + TF locals B3 — CONDICIONAL aggressive

**Veredicto**: CONDICIONAL pre-reciclaje (análisis profundo lecciones v2.3.9 requerido).

**Scope refinado**: 14-20h humano / **3-5h Claude Code total**.

**Lecciones v2.3.9 documentadas** refresh:
- B2 prev_zone: ultra review premise INCORRECTA — TF SÍ lee state.prev_zone_bull en fallback t==0. Semántica DISTINTA TF (computed `fast/slow/trend`) vs MR (`fast<slow` invertida). Cross-strategy swaps (GRT TF→MR 2026-04-17) dejan stale state.
- B3 TF locals vs MR state: cambiar TF estilo MR requiere modificar `compute_divergences` signature + 14+ lecturas div_ctx locales. Refactor quirúrgico API interna camino crítico TF.

**Riesgos**: regresión brain TF + MR + decisión arquitectónica subóptima.

**Mitigaciones**: MS.1 análisis profundo lecciones v2.3.9 ANTES implementar (subtarea explícita). MS.2 Smoke §0.8 A+B+C obligatorio. MS.3 tests TF+MR cross-strategy swap. MS.4 rollback strategy git branch + revert.

**Recomendación**: CONDICIONAL — solo si AGGRESSIVE confirmed. Si MODERATE/FOCUSED: diferir v3.0.

#### G5.4 brain _evaluate_bar duplicación — DIFERIR post

**Veredicto**: DIFERIR post-reciclaje. Refactor sin valor F1/F2 directo. Disparador 1/2 cumplido (R1 cooldown único bug del mismo tipo replicado, RESUELTO via cooldown_unify).

#### G5.11 portfolio correlación min_len — OPCIONAL

**Veredicto**: PRE-RECICLAJE OPCIONAL.

**Scope refinado**: 0.5-1h humano / **10-20 min Claude Code**.

**Decisión**: cambiar excluir símbolos N<60 vs truncar. Recomendar excluir threshold 60 samples.

### Items NO rescatables (~14 items §13.3 EN_ESPERA) — confirmaciones

| Item | Línea | Categoría | Refutación |
|------|-------|-----------|------------|
| G5.6 data_feed attach stops | L2274 | post-reciclaje cleanup | DIFERIR scope coordinated refactor |
| G5.7 execution funding fallback signo | L2302 | bug latente 0% path activo | DIFERIR sin disparador |
| G5.8 execution ejecución parcial reconcile | L2510 | mitigada parcial v2.3.8 B7 | DIFERIR escalar capital >1000 USDT |
| G5.9 portfolio vol_weight neutraliza dd | L2360 | DD no activo (DD 1.32%) | DIFERIR disparador no cumplido |
| G5.10 portfolio block_reduction 3 factores | L2383 | post-reciclaje refactor analyzer | DIFERIR scope analyzer |
| L1894 v2.3.11 Opción B2 forming fetch | L1894 | virtualmente improbable | DIFERIR |
| L2486 Multiples eventos mismo-ciclo | L2486 | 0/231 trades histórico | DIFERIR edge case raro |
| L2446 brain símbolo datos insuficientes | L2446 | 0 incidentes 5+ días | DIFERIR disparador no cumplido |
| L2456 brain comments forming/resolved | L2456 | puro cosmético | DIFERIR post-reciclaje |
| L2632 engine_state nomenclature | L2632 | cosmético consolidado | mantener trazabilidad |
| L1904 git+GitHub setup | L1904 | política /ultrareview v3 deprecated | mantener EN_ESPERA antiguo |
| L1707 política adelantar reciclaje | L1707 | subsumida calendario inminente | EN_ESPERA hasta reciclaje ejecutado |
| L2721 funding NO feature GMM | L2721 | decisión permanente | mantener referencia |
| G1.4 Hidden divergence asimetría | L2434 | refactor brain+kernel simultáneo riesgo F1+F2 alto | DIFERIR v3.0 |
| G1.5 Análisis B edge decay | L2967 | viability blocker post-training ≥60d | DIFERIR post-reciclaje julio |
| G4.1 Edge erosion descriptivo N=60 | (caracterización) | NO accionable directo | caracterización permanente |

### Tabla resumen final Parte 1

| # | Item | Veredicto | Scope CC | Pre-req | Riesgo |
|---|------|-----------|----------|---------|--------|
| G1.1 | Tier 0 I1 kernel | **CONFIRMADO** | 2-4h CC + Smoke | Smoke A+B+C oblig | Medio |
| G1.2 | Bloque 2c granular | **CONFIRMADO cond G1.1** | 1-2h CC | G1.1 done | Bajo |
| G1.3 | Lab compute_leverage_map fix | **ESENCIAL** | 30-45 min CC | None | Bajo |
| G2.1 | Refactor audit_v5.x Op A | **CONFIRMADO** | 1-2h CC | None | Medio |
| G2.2 | Smoke §0.8 Nivel B | **OBLIGATORIO** | 15-30 min CC | Post-G1.1+G1.3 | Bajo |
| G5.1 | Deploy L1892+L1904 | **CONFIRMADO** | 10 min CC | None | Bajo |
| H_M3 | Selection bias cross-cluster | **EJECUTAR** | 1h CC | None | Bajo |
| H_M4 | Régimen-temporal bias | **EJECUTAR subset** | 1h CC | None | Bajo |
| H_M5 | GMM classification noise | **EJECUTAR** | 1h CC | None | Bajo |
| H_M6 | Cross-exchange residual | **EJECUTAR** | 1-2h CC | None | Bajo |
| G3.2 | Deflated SR core subset | **CONDICIONAL** | 2-3h CC | None | Bajo |
| G3.3 | k-fold CV subset | **CONDICIONAL** | 2-3h CC | None | Bajo |
| G5.3 | brain prev_zone B2 + TF locals B3 | **CONDICIONAL aggressive** | 3-5h CC | Análisis profundo v2.3.9 | Medio |
| G5.4 | _evaluate_bar duplicación | **DIFERIR post** | — | None | Medio |
| G5.11 | portfolio correlación min_len | **OPCIONAL** | 10-20 min CC | None | Bajo |

**Scope totales refinados Claude Code**:
- CORE confirmados (6 items): **~5-10h CC**
- HIPÓTESIS Mec 3+4 todas 4: **~4-6h CC**
- DEFLATED SR + k-fold subsets: **~4-6h CC**
- OPERACIONALES rescatables (G5.3+G5.11): **~3-5h CC**
- **TOTAL AGGRESSIVE pura recalibrada**: **~16-27h CC** cross-4-5 sesiones

---

## 3. Mapping dependencias secuenciales (Parte 2)

### Análisis dependencias finas

```
DEPENDENCIA CONCEPTUAL ESTRICTA (precede obligatorio):
  G1.1 Tier 0 I1 kernel ─────────────────► G1.2 Bloque 2c granular
       (per-trade arrays salida)              (consume reason_exit + side)

DEPENDENCIA RECOMENDADA (refuerza poder estadístico):
  G1.1 Tier 0 I1 ──recomienda──► H_M4 Régimen-temporal bias full
       (per-trade granular)            (subset aggregate viable sin G1.1)
  G1.2 Bloque 2c ──refuerza──► H_M3 Selection bias cross-cluster
       (cross-régimen N masivo)        (subset cross-cluster viable directamente)

DEPENDENCIA VALIDACIÓN (post-cambio):
  G1.1 done ──obligatorio──► G2.2 Smoke §0.8 Nivel B re-run
  G1.3 done ──obligatorio──► G2.2 Smoke §0.8 Nivel B re-run
  G5.3 done ──obligatorio──► G2.2 Smoke §0.8 Nivel A+B+C cross-cambio

INDEPENDIENTES (ejecución paralela posible):
  G1.3 Lab fix          ┐
  G2.1 Refactor audit   │  Independientes G1.1 + G1.2 + Mec hipótesis
  G5.1 Deploy obs       │
  H_M5 GMM threshold    │
  H_M6 Cross-exchange   │
  G3.2 Deflated SR      │
  G3.3 k-fold CV        │
  G5.11 portfolio min_len ┘

DEPENDENCIA OPERACIONAL FINAL (precede reciclaje launch):
  Todos cambios pipeline lab ──► reciclaje launch
  G2.1 audit refactor done ──► validación 45 JSONs nuevos post-reciclaje
  G2.2 Smoke Nivel B sistemático ──► gate inmediato pre-launch
  G5.1 Deploy observability ──► fecha límite ~2026-05-05 a 05-10
```

### Cadena crítica (critical path)

**AGGRESSIVE pura recalibrada cadena crítica**:
G1.1 (2-4h CC) → G1.2 (1-2h CC) → H_M3+H_M4 full (2h CC) = **~5-8h CC secuencial obligatorio**

Resto items independientes ejecutables paralelo cross-sesiones distintas → reduce calendario.

---

## 4. Calendarios alternativos + AGGRESSIVE pura recalibrada (Parte 3)

### 3 calendarios alternativos

#### Calendario AGGRESSIVE (humano original)
- Total scope: ~89-135h cross-aggressive humano
- Duración: ~3 semanas pre-reciclaje + 2 semanas reciclaje = **5 semanas total**
- Bot obsoleto adicional: ~3 semanas

#### Calendario MODERATE (humano original)
- Total scope: ~45-70h humano
- Duración: ~1.5-2 semanas pre-reciclaje + 2 semanas reciclaje = **3.5-4 semanas total**
- Bot obsoleto adicional: ~2 semanas

#### Calendario FOCUSED (humano original)
- Total scope: ~25-40h humano
- Duración: ~1 semana pre-reciclaje + 2 semanas reciclaje = **3 semanas total**
- Bot obsoleto adicional: ~1 semana

### Recomendación inicial Sesión 2 D Parte 3 (PRE-RECALIBRACIÓN)

Mi recomendación inicial: **Calendario MODERATE** bajo "aspirar a lo mejor reciclaje" pragmático.

**Razones MODERATE**:
1. CORE confirmados cubren reformulaciones timing categóricas reveladas Parte 0.
2. H_M5+H_M6 directamente testeable sin G1.1 dependencia.
3. G1.1+G1.2 done → infrastructure permanente para H_M3+H_M4 post-reciclaje.
4. Deflated SR + k-fold CV proyectos dedicados ~30-55h cada → diferir post-reciclaje.
5. G5.3 brain refactors riesgo medio + valor F1/F2 indirecto.
6. Stress humano sostenible cross-2 semanas vs cross-3.

### Decisión Ricardo Sesión 2 D + recalibración temporal §12 L37

**Cuestionamiento honesto Ricardo**: estimaciones temporales basadas en patrones humanos NO aplican a Claude Code. Aplicación errónea infla scope ~3-5× y produce decisiones calendario conservadoras subóptimas bajo recursos ilimitados.

**Recalibración temporal cross-tareas**:

| Tarea | Estimación humana | Estimación Claude Code |
|-------|-------------------|------------------------|
| G1.1 Tier 0 I1 kernel | 15-20h cross-4-5 días | 2-4h CC + Smoke compute |
| G1.2 Bloque 2c granular | 5-10h cross-2 días | 1-2h CC + 1-2h kernel runs |
| G1.3 Lab fix | 2-4h cross-1 día | 30-45 min CC |
| G2.1 Refactor audit | 4-12h cross-1-2 días | 1-2h CC |
| G2.2 Smoke sistemático | 1-2h cross-0.5 día | 15-30 min CC ejecución |
| G5.1 Deploy | 0.5-1h cross-0.5 día | 10 min CC + procedure VPS |
| H_M3-M6 todos 4 | 20-34h cross-4-5 días | 4-6h CC + 1-2h compute |
| G3.2+G3.3 subsets | 20-30h cross-4-5 días | 4-6h CC |
| G5.3 prev_zone B2+B3 | 14-20h cross-3-4 días | 3-5h CC |
| G5.11 portfolio min_len | 0.5-1h cross-0.5 día | 10-20 min CC |
| **TOTAL** | **~89-135h cross-3-semanas humano** | **~16-27h CC cross-4-5 sesiones cross-1.5-2 semanas calendario** |

**Diferencia categórica**: ~3-5× temporal cross-tareas. Bot obsoleto adicional reducido de ~3 semanas a ~1-2 semanas.

**Decisión Ricardo CONFIRMADA**: **AGGRESSIVE PURA RECALIBRADA** bajo "al margen de lo que cueste, aspirar a lo mejor reciclaje".

### Calendario AGGRESSIVE pura recalibrada cross-Claude-Code-sesiones

| Sesión | Días calendario | Sub-fases | Scope CC |
|--------|-----------------|-----------|----------|
| 1A | ~2026-04-28 | G1.3 + G2.1 + G5.11 + G2.2 baseline | ~3-4h |
| 1B | ~2026-04-29 | G1.1 Tier 0 I1 kernel + Smoke A+B+C | ~3-5h |
| 2 | ~2026-04-30 a 05-01 | G1.2 + H_M3 + H_M4 + H_M5 + H_M6 | ~4-6h |
| 3 | ~2026-05-02 a 03 | G3.2 + G3.3 selection-bias-specific | ~5-6h |
| 4 | ~2026-05-04 a 05 | G5.3 + G5.1 + G2.2 final pre-launch | ~3-5h |
| 5 | ~2026-05-06 a 12 | Reciclaje 45 sym launch + ejecución VPS autónomo | 30 min preparation + 10-15 días compute |

**Total pre-reciclaje cross-Claude-Code-sesiones**: **~18-26h CC cross-1.5-2 semanas calendario** + reciclaje 10-15 días = **~3-4 semanas total**.

**Bot obsoleto adicional**: ~1-2 semanas vs plan minimalista sesión 1 Fase 5 (~3-4 días). Trade-off aceptable bajo enfoque Ricardo.

---

## 5. Riesgos + mitigaciones específicas cross-items (Parte 4)

### Riesgos cross-items con mitigaciones acotadas

#### G1.1 Tier 0 I1 kernel — riesgo medio

**Riesgos**:
- F1 transitorio: kernel modify cambia output signature
- Update callers incompleto → fallo runtime regime_walk_forward
- Memory overflow arrays per-trade (~5GB peak posible)

**Mitigaciones**:
- M1.1: tests greenfield con per-trade tracing ANTES merge
- M1.2: grep exhaustivo callers list completa pre-cambio
- M1.3: chunked allocation arrays (chunks 10K trades) + memory monitor
- M1.4: Smoke §0.8 A+B+C obligatorio cross-cambio
- M1.5: cross-check verify_test baseline (BTC N=1000 diff 0.0000 + cross-3-símbolos N=1000 380 mediciones)
- M1.6: rollback strategy explícita — git branch pre-G1.1 + commits granulares + revert si Smoke falla

#### G1.2 Bloque 2c granular — riesgo bajo

**Riesgos**: memory durante kernel runs masivos.

**Mitigaciones**:
- M2.1: chunked execution + validation memory
- M2.2: hipótesis emergentes Mec 3+4 documentadas explícitamente

#### G1.3 Lab compute_leverage_map fix — riesgo NULO bot productivo

**Mitigaciones**:
- M3.1: walk-forward 1 sym smoke validar specialists scores invariantes
- M3.2: docstring explícito P1 opción (b) confirmed 2026-04-27 + caveats reactivación (i)-(v)

#### G2.1 Refactor audit_v5.x Opción A — riesgo medio

**Riesgos**:
- Audit produce match rate distinto post-refactor (falsa alarma o falsa tranquilidad)
- Opción A breaking stateless property

**Mitigaciones**:
- MA.1: tests greenfield audit pre-refactor + post-refactor
- MA.2: cross-check verify_test ground truth (76 trades 380 mediciones diff 0.0000 baseline)
- MA.3: importar kernel funciones puras parametrizadas
- MA.4: smoke audit cross-3-símbolos pre/post

#### G3.2 Deflated SR core subset — riesgo bajo

**Mitigaciones**:
- MD.1: validación numérica vs paper formula + tests synthetic
- MD.2: validación cross-9 cross-symbol M2 fix baseline (Q1+W1 2026-04-23)
- MD.3: comparación expected vs computed Sharpe deflation

#### G3.3 k-fold CV subset — riesgo bajo

**Mitigaciones**:
- ME.1: validación tests + comparación baseline walk-forward

#### G5.3 prev_zone B2 + TF locals B3 — riesgo medio

**Riesgos**:
- Regresión brain TF + MR (cambia API interna camino crítico)
- Decisión arquitectónica subóptima si lecciones v2.3.9 no bien aplicadas

**Mitigaciones**:
- MS.1: análisis profundo lecciones v2.3.9 ANTES implementar (subtarea explícita). Output documento decisión arquitectónica prev_zone.
- MS.2: Smoke §0.8 A+B+C obligatorio cross-cambios
- MS.3: tests TF+MR cross-strategy swap (caso GRT TF→MR 2026-04-17)
- MS.4: rollback strategy git branch + revert si Smoke falla

#### H_M3-M6 hipótesis Walk-forward — riesgo bajo

**Mitigaciones**:
- MH.1: cada hipótesis aplicar §12 L36 prophilactic (predicción registrada pre-test + falsifiable)
- MH.2: §12 L25 segmentación + §12 L26 validación per-componente
- MH.3: hipótesis emergentes durante G1.2 Bloque 2c → input directo H_M3-M6

#### G5.1 Deploy L1892+L1904 — riesgo bajo

**Mitigaciones**:
- MQ.1: procedure standard 8 pasos §13.3 L3003
- MQ.2: agrupar con G5.11 + G2.2 final pre-launch

#### G5.11 portfolio correlación min_len — riesgo bajo

**Mitigaciones**:
- MR.1: tests no-regression matriz correlación pre/post fix

### Riesgos cross-AGGRESSIVE acumulado

**Riesgo regresión multi-cambios acumulada**:
- §12 L25 segmentación arquitectónica obligatoria — sesiones dedicadas aisladas (Sesión 1A independiente + 1B G1.1 dedicada + 2 G1.2+hipótesis + 3 selection-bias + 4 G5.3+cierre)
- Gates Smoke §0.8 cross-sesiones: A+B+C obligatorio post-G1.1 + post-G1.3 + post-G5.3
- Commits granulares per item (no merges grandes)

**Riesgo bot productivo durante pre-reciclaje**:
- Bot v2.4.5 invariante todo pre-reciclaje (cero deploys productivos hasta deploy final reciclaje launch)
- Modificaciones offline (lab/, post-hoc analyzers, audit refactor, scripts hipótesis testing)
- live/ NO tocar excepto G5.1 deploy operacional acotado

---

## 6. Decisión Ricardo AGGRESSIVE pura recalibrada confirmada + plan Sesiones 1A+1B+2+3+4+5

Ver detalles en ROADMAP_PRE_RECICLAJE.md sección "Pre-reciclaje AGGRESSIVE pura recalibrada — 2026-04-27 Sesión 2 D".

**Plan Sesión 1A próxima dedicada ~mañana 2026-04-28**: G1.3 + G2.1 + G5.11 + G2.2 baseline (~3-4h Claude Code).

Spec detallado redactado en sesión próxima cuando confirmada disponibilidad Ricardo.

---

## 7. Caveats temporales + recalibración §12 L37

**§12 L37 nuevo refinamiento permanente capturado**:

> "Estimaciones temporales para tareas Claude Code calibrar contra procesamiento+ejecución técnica, NO patrones humanos. Aplicación errónea infla scope 3-5× y produce decisiones calendario conservadoras subóptimas bajo recursos ilimitados."

Caso origen: Sesión 2 día 2026-04-27 D recalibración 89-135h humanas → 20-35h Claude Code real.

**Mitigación protocolaria**: pre-redacción spec o calendario, separar explícitamente:
- (a) Tiempo Claude Code interacción (lectura + escritura + análisis token-bound)
- (b) Tiempo compute batch (kernel runs, smokes, sweeps autónomos)
- (c) Tiempo calendario humano (tomar decisiones intermedias, validar reportes, supervisión Ricardo)

NO sumarlos en una métrica única "Xh".

**Quinto pilar metodológico institucional** (extiende cuádruple guardrail L25+L26+L35+L36 + nuevo L37):
- L25: segmentación arquitectónica obligatoria sobre ventanas con deploys heterogéneos.
- L26: validación per-componente además de ecuación global de cierre.
- L35: test diferencial contra ground truth productivo ANTES de investigar causa raíz por hipótesis (reactivo).
- L36: predicción cualitativa explícita ANTES de implementación o investigación de scope significativo (proactivo).
- L37: recalibrar estimaciones temporales contra tiempo Claude Code real, NO humano (planning).

---

## 8. §12 L36 9ª aplicación calibración retrospectiva + cross-9-aplicaciones consolidada

### Calibración retrospectiva Parte 0 (8ª aplicación)

| # | Predicción | Realidad | Status |
|---|------------|----------|--------|
| 1 | Bot v2.4.5 invariante uptime ~5d | confirmed 5d 1h+ | ✓ |
| 2 | Sync local OK 5 commits | confirmed | ✓ |
| 3 | Tier 0 I1 + Lab fix conceptualmente PRE-RECICLAJE | confirmed reformulación timing | ✓ |
| 4 | Bloque 2c depende Tier 0 I1 | confirmed | ✓ |
| 5 | Walk-forward Mec 3+4 §12 L34 estricto sin hipótesis | parcialmente — 4 hipótesis emergentes formuladas | ⚠️ refinada |
| 6 | Deflated SR full post-reciclaje, subset viable | confirmed | ✓ |
| 7 | Riesgos overengineering + stress humano + superficie | confirmados | ✓ |

6/7 acertadas + 1 refinada. §12 L36 cross-8-aplicaciones consolidada.

### Calibración retrospectiva Parte 1 (9ª aplicación)

| # | Predicción | Realidad | Status |
|---|------------|----------|--------|
| 1 | G1.1 Tier 0 I1 scope realista 20-25h subestimado original | confirmed | ✓ |
| 2 | G1.2 Bloque 2c probable produce hipótesis Mec 3+4 emergentes >50% | byproduct identificado | ✓ |
| 3 | G2.1 Refactor audit Opción A bajo "aspirar a lo mejor" | confirmed | ✓ |
| 4 | H_M5 + H_M6 directamente testeable sin G1.1 prereq | confirmed | ✓ |
| 5 | H_M3 + H_M4 dependen G1.1 ejecutables solo post | parcialmente — H_M4 subset aggregate viable directamente | ⚠️ refinada |
| 6 | G5.3 prev_zone B2 + TF locals B3 con análisis profundo | confirmado viable | ✓ |
| 7 | Recalibración temporal categórica produce reformulación trade-offs | **MASIVAMENTE confirmada** | ✓ MAYOR |

5/7 acertadas + 1 refinada + 1 mayor (recalibración temporal §12 L37).

### Cross-9-aplicaciones consolidada

| Sesión/Aplicación | Predicciones | Acertadas | Refutadas | Outcome |
|---|---:|---:|---:|---|
| 1. Variante 4 funding 2026-04-25 | 6 | 6/6 | 0/6 | Tier 0 I1 bloqueante |
| 2. Path B previo 2026-04-26 | 5 | 0/5 | 5/5 | Reformulación marco |
| 3. Path B-institutional 2026-04-26 | 9 | 6/9 | 3/9 | OKX retention factor |
| 4. Pre-flight v2.6-inv/exit 2026-04-27 mañana | 7 | 2/7 | 4/7 | Refutación masiva opción α |
| 5. P1 leverage Fase 2 2026-04-27 tarde | 7 | 3/7 | 3/7 | Asimetría arquitectónica clusters |
| 6. Triaje §13.3 Fase 3 2026-04-27 tarde-noche | 10 | 3/10 | 5/10 | Items disciplinados resilientes |
| 7. Auditoría rescate Fase 5 2026-04-27 cierre | 7 | 7/7 | 0/7 | Análisis crítico individual reemplaza auditoría sistemática 6-8× eficiencia |
| **8. Sesión 2 D Parte 0 2026-04-27** | **7** | **6/7** | **0/7 (1 refinada)** | **Reformulación timing categórico revelada** |
| **9. Sesión 2 D Parte 1 2026-04-27** | **7** | **5/7** | **0/7 (1 refinada + 1 mayor §12 L37)** | **Recalibración temporal §12 L37 capturado** |

Cross-9-aplicaciones ahorro acumulado compute estimado **~52-90h** (extends cross-7 sesión 1 cierre día + Parte 0 + Parte 1).

### Patrón institucional consolidado §12 L36 cross-9

Predicciones refutadas en magnitud son outcome más informativo cuando ocurren. Cross-9-sesiones consecutivas cada refutación llevó a hallazgo estructural genuino + redirección scope metodológicamente correcto. Predicciones acertadas validan profilácticamente decisiones eficientemente.

§12 L36 prophilactic + §12 L27 V1+V2 refinamientos + §12 L37 nuevo (recalibración temporal Claude Code) constituyen marco metodológico institucional permanente para sesiones futuras.

---

## Cierre

**Estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1+TRIAJE+AUDIT-RESCATE+AGGRESSIVE-PRE-RECICLAJE invariante**.

**Plan Sesión 1A próxima dedicada ~mañana 2026-04-28**: G1.3 + G2.1 + G5.11 + G2.2 baseline (~3-4h Claude Code).

**Bot v2.4.5 operacional VPS Tokio uptime 5d 3h+ invariante**. Sin tocar `live/*` hasta Sesión 4 G5.1 deploy + Sesión 5 reciclaje launch. Fidelidad 2 invariante por construcción.

**6 commits acumulados día 2026-04-27**: 3eb937c (Fase 1) + 06e30fb (Fase 2) + d1d2859 (Fase 3) + 8aa0db1 (Fase 4) + c1cc474 (Fase 5) + Sesión 2 D hash final.
