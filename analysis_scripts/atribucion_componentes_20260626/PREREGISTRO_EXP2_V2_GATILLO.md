# PRE-REGISTRO CONGELADO — Exp#2 v2: "Order Block" con el criterio REAL de Ricardo (gatillo-anclado)

**Fecha:** 2026-06-26 · **Estado:** FROZEN-PENDING-VALIDACIÓN (T3.1-Exp2: Ricardo valida la objetivación vía XRP + aprueba ANTES del barrido 45) · **Rama:** `atribucion-componentes`.

> **SUPERSEDE la v1** (`PREREGISTRO_EXP2_ORDERBLOCK.md`): la v1 formalizó SOLO "origen de explosión" (ICT) + 2R fijo + sin gatillo-ancla = subconjunto estrecho con sesgo geométrico (placebo floor 1.23). Su veredicto negativo es válido para ESA formalización, NO para la estrategia real. Esta v2 mide el criterio REAL (validado Q1-Q4 con capturas).

---

## 1. El componente (criterio real de Ricardo)

- **GATILLO (ancla, reúsa MR ya codificado, sin DOF nuevo):** cruce **Tenkan-9 / HA-diaria-forming** (`mean_reversion_features`, causal: el forming usa solo ≤t). Dispara la búsqueda + da dirección de reversión + ancla temporal. **No se buscan bloques sin gatillo.** (El gatillo solo dispara/ancla — Exp#1: el cruce solo no tiene edge; el edge tendría que venir del bloque.)
  - bull gatillo (flip a zona_bull) → LONG, busca SOPORTE debajo.
  - bear gatillo (flip a zona_bear) → SHORT, busca RESISTENCIA arriba.
- **BLOQUE (choque histórico, retroceso SIN límite):** el nivel anterior más reciente, FRESCO (no mitigado desde su formación) y dentro del 5% del precio, que el precio actual reencuentra. El precio se dirige al bloque a barrerlo; apuesta: el bloque RECHAZA → reversión.
- **ENTRADA:** orden límite pasiva en el borde proximal del bloque (no inmediata; se espera que el precio llegue).
- **STOP:** cierre fuera del bloque (invalidación por cierre — si cierra más allá, no hubo rechazo).
- **TAKE PROFIT (cardinal, corrección Q4):** el **siguiente CRUCE** (cambio de zona) tras la entrada — NO 2R fijo. El cruce delimita las zonas → un nuevo cruce señala cambio de zona = cierre natural. **Beneficio metodológico:** sale por un EVENTO ESTRUCTURAL, no una distancia fija → sin el sesgo geométrico del 2R (v1 PF_all 1.30 → v2 0.86). El random walk sigue siendo el juez.

## 2. Parámetros LÓGICOS FIJOS (congelados a priori)
- **Cercanía:** ≤ 5% del precio (Q3, Ricardo validó). Robustez: {3, 5, 7}%.
- **Retroceso:** sin límite histórico; primer soporte/resistencia FRESCO bajo/sobre el precio dentro del 5%.
- **Gatillo:** cruce MR Tenkan-9/HA-diaria-forming (existente). **STOP:** cierre fuera. **TP:** siguiente cruce. **Comisión:** 0.10%.
- **Unidad:** por-setup independiente (cada gatillo con bloque válido → un trade candidato).

## 3. [DOF FLAGGED — validación Ricardo vía XRP]
La objetivación de **"choque relevante / nivel donde el precio reencuentra una vela previa"** tiene un grado de libertad genuino. **Elección v1 (congelada-pendiente-validación):** bloque = la vela más reciente, hacia atrás, que es un extremo FRESCO (su low/high no mitigado desde que se formó) con borde proximal dentro del 5% del precio. **Ricardo valida vía su caso XRP** (marcó ~1.0485/1.0038): si el detector marca un bloque coincidente → la objetivación captura su criterio; si no → se corrige por JUICIO (su criterio), NO por rendimiento. Si la corrección abre mucho DOF → Tier 3, no tunear.

## 4. LOOK-AHEAD — cardinal, garantizado + test
Simulación **estrictamente barra-a-barra**: gatillo causal (forming ≤t); bloque usa solo j<t y la trayectoria [j,t]; la orden límite vive desde el gatillo y un CRUCE la cancela/cierra **cuando OCURRE** (no se pre-computa la ventana — fix tras FAIL de la v2.0 que pre-acotaba con el cruce futuro). Entrada/stop/TP estrictamente posteriores; el retest NO valida el bloque. **Gate: test prefix-invariance bit-exacta (re-precalc MR truncado) → PASS.**

## 5. Los 4 controles (congelados)
1. **Edge OOS:** pf_fwd GLOBAL (cross-cluster, forward holdout) neto 0.10%, CI bootstrap por-símbolo que excluya 1.0.
2. **Random walk (JUEZ decisivo):** 6 placebo (GBM/shuffle); el ruido no tiene liquidez que barrer → si "funciona" sobre ruido = geometría → debe caer a breakeven. El TP-por-cruce lo hace más limpio que el 2R. **El veredicto se lee de la BRECHA real-vs-placebo, no del PF absoluto.**
3. **Robustez:** cercanía {3,5,7}% + criterio de choque.
4. **As-of E2** + per-cluster diagnóstico (el setup de reversión debería vivir en régimen de reversión/lateral si la causa es real).

## 6. Criterio de éxito
Edge si: pf_fwd con CI por-símbolo que excluya 1.0 **Y supere el floor de placebo** **Y** caiga sobre random walk **Y** robusto **Y** coherente per-cluster. El edge se lee de la **brecha real-vs-placebo**.

## 7. Universo, métricas, harness
45 símbolos. Métricas como Exp#1 (PF + CI bootstrap, PnL, win-rate, neto 0.10%). Detector `ob_detector_v2.py` (gatillo MR reusado + bloque-por-choque). Smoke PASS (detección sensata + Gate B prefix-invariance PASS).

## 8. Tier-3 PAUSE
- **T3.1-Exp2 (AQUÍ):** detector v2 + smoke PASS + .md congelado + validación visual XRP → Ricardo valida la objetivación + aprueba ANTES del barrido 45.
- **T3.2-Exp2:** look-ahead irreducible (resuelto: PASS) / objetivación no captura el criterio de Ricardo → corregir por juicio.
- Barrido 45 SOLO con OK de Ricardo.

## 9. Invariantes
ULTRATHINK + §12 L38 (medir la estrategia REAL, no la aproximación ICT). Línea roja en el DISEÑO (params lógicos congelados; objetivación validada por juicio, no tuneada). Look-ahead fuera + test. brain/portfolio/kernel productivos INTACTOS (detector OB nuevo, separado). Migración Kraken en pausa. Bot Tokio stopped.
