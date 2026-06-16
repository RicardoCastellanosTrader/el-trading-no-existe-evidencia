# Nivel 3 — Confirmación de D3 (régimen/contexto) — DISEÑO + PRE-REGISTRO

**Fecha**: 2026-06-16 · **Estado**: 🟡 **DISEÑO + PRE-REGISTRO — PENDIENTE T3.1 (Ricardo) + elección α/β. NO ejecutar GPU hasta aprobación.** Mismo patrón que funcionó 2× (Campaña Edge Real, Estudio de Capacidad): diseñar+pre-registrar → Tier 3 → ejecutar.

**Contexto**: el Estudio de Capacidad (`VEREDICTO_ESTUDIO_CAPACIDAD.md`) cerró que la re-selección por el eje del **rendimiento pasado** está muerta o es mecánica, y que **D3 (régimen/contexto, ε²=0.574) es la única señal viva, limpia, no mecánica — y es el eje exacto de Frame 3**. Pero D3 es **CANDIDATA**: medida sobre N1 (en-selección, sesgos a favor) y con una **explicación alternativa viva** que debe aislarse antes de justificar la construcción de Frame 3.

---

## B.1 — LA EXPLICACIÓN ALTERNATIVA A AISLAR (cardinal — sin esto el Nivel 3 no confirma nada)

ε²=0.574 ⇒ el clúster (régimen) explica ~57% de la varianza de rango de `pf_fwd` entre configs (within símbolo). Dos lecturas mutuamente excluyentes:

- **H_real (señal)**: el contexto/régimen en la selección PREDICE qué config rinde forward. Desplegar el specialist correcto en el régimen correcto bate al despliegue régimen-agnóstico sobre datos futuros intocados.
- **H_artefacto (relleno)**: cada clúster se rellena con selección INDEPENDIENTE (top-100 de las configs validadas DE ESE clúster). Las configs difieren entre clústeres **por construcción**; el ε² mide *qué configs entraron*, no que el régimen prediga rendimiento. Algunos régimenes simplemente rinden más PF para sus propias top picks — propiedad de los datos del régimen, no relación explotable.

**El discriminante (directive Ricardo)**: la señal REAL implica **condicionalidad forward** que el artefacto NO: *¿una config seleccionada para el contexto X rinde forward MEJOR en periodos futuros de contexto X que en periodos de contexto Y?*

### Test que aísla — MATCH vs MISMATCH forward (sobre datos intocados)
Para cada specialist `c` con régimen-hogar `h(c)`, ejecutado **régimen-agnóstico sobre TODO el holdout** (no solo cuando su régimen está activo) y tagueando cada trade por el régimen concurrente `r` (clasificado as-of):
- `PF_match(c)` = PF de trades con `r = h(c)`.
- `PF_mismatch(c)` = PF de trades con `r ≠ h(c)`.
- **Δ(c) = PF_match(c) − PF_mismatch(c)**.

- **H_real**: Δ pooled > 0 robusto (el match porta edge forward).
- **H_artefacto**: Δ ≈ 0 (la config rinde igual haya o no match → el régimen no porta info forward → ε² fue relleno).

Esto separa limpiamente las dos hipótesis porque el artefacto NO predice condicionalidad forward, solo niveles de relleno. **Es además exactamente lo que Frame 3 NECESITA que sea cierto** para ser desplegable.

**Por qué NO se puede hacer barato (verificado primary-source)**: el único cross-cluster forward PF almacenado es `adjacent_worst_pf` (el mínimo), y es EN-selección (la config se eligió por su `pf_fwd`-hogar alto → home>adjacent es parcialmente mecánico por selección). El contraste limpio exige forward INTOCADO. Además **`asof_sandbox/` fue limpiado** → los specialists/GMM as-of de E2-full NO están en disco → regenerar la selección as-of = GPU. (La réplica de condicionalidad en sí es CPU; el coste GPU es solo la *selección* as-of.)

---

## B.2 — DOS OPCIONES DE DATASET

| | **α — walk-forward población-COMPLETA** | **β — holdout as-of régimen-condicional (reusa gate E2)** |
|---|---|---|
| Qué es | Regenerar `walk_forward_experiment.py` (36 anclajes, borrado Caveat #13): población completa de configs, forward fuera de selección | Regenerar selección as-of por celda (sym×ancla) + clasificar holdout intocado por régimen + replay MATCH/MISMATCH (B.1) |
| Aísla B.1 | NO de forma nativa — da ρ(dimensión,forward) limpio pero requiere instrumentar el split por régimen igualmente | **SÍ nativamente** — el test MATCH/MISMATCH sobre holdout intocado es el corazón del diseño |
| Anti-leakage | forward-fuera-de-selección por anclaje (limpio) | **gate E2 validado BIDIRECCIONAL** (honesto pasa / envenenado caza) ya probado 8/8 |
| Beneficio extra | rescata D4 (con fracasos) + D2/D5 limpios (métricas train-only) | enfocado solo a D3 |
| Coste GPU | población completa cross-N-sym = **días de GPU** (177M obs precedent; el mayor del proyecto) | regen selección as-of ~5–8h/celda × celdas (mismo orden que E2-full ~40–80h) |
| Estructura para condicionalidad | hay que añadirla | ya la produce |

**RECOMENDACIÓN: β.** Aísla B.1 nativamente sobre datos intocados con el gate anti-leakage ya validado, al menor coste, y entrega justo la afirmación desplegable de Frame 3 (specialist-correcto-en-régimen-correcto bate agnóstico). α es más caro y NO aísla mejor el artefacto; α solo es preferible si Ricardo además quiere resucitar D4 + D2/D5 limpios (pregunta separada, mucho más cara) — en ese caso α es un pase complementario posterior, no el confirmador de D3.

---

## B.3 — PRE-REGISTRO (congelar ANTES de ejecutar; Tier 3 aprobación)

### Hipótesis falsable
**H0**: el régimen/contexto NO porta edge forward condicional (Δ ≤ 0 y/o régimen-conditional NO bate régimen-agnóstico) → D3 fue artefacto de relleno → re-selección por régimen también muerta.
**H1**: seleccionar config por contexto produce rendimiento forward CONDICIONAL al contexto que la selección por PF no produce (Δ > 0 robusto **y** `PF_match` net > breakeven).

### Métricas (todas: pnl_pct − 0.10pp fee RT, idéntica a E2/audit)
- **Primaria — condicionalidad**: Δ = PF_match − PF_mismatch, pooled cross-celda, **CI95 bootstrap por-símbolo**.
- **Primaria — deployabilidad**: `PF_match` net pooled + CI95 (el match debe ser RENTABLE, no solo "pierde menos").
- **Secundaria — valor Frame 3 directo**: PF de cartera régimen-CONDICIONAL (despliega specialist de `r` en cada bar `r`) vs PF régimen-AGNÓSTICO (mejor config único ignorando régimen) sobre el mismo holdout.
- **Placebo de control**: specialist-para-Y sobre bars-X vs bars-Y (el wrong-match no debe mostrar el patrón si la señal es real y específica).

### Criterio de decisión — 3 ZONAS (congelado, igual que Campaña Edge Real)
- **D3 CONFIRMADA (→ construir Frame 3)**: Δ CI95 inf > 0 **Y** `PF_match` CI95 inf > 1.0 **Y** cartera condicional > agnóstica (punto). El régimen porta edge forward desplegable.
- **D3 MATADA (→ cierra la familia / pivota)**: Δ CI95 cruza/≤ 0 **o** `PF_match` CI95 sup < 1.0. El régimen no porta edge forward → ε² fue relleno → re-selección por régimen muerta como la del PF.
- **NO CONCLUYENTE**: Δ > 0 pero `PF_match` CI cruza 1.0, o CIs anchos → regla = **más anclas/símbolos ANTES de conclusión estructural** (NO forzar sí/no). "No demostrado" ≠ "no hay edge".

### Anti-leakage (reusa gate E2, validado BIDIRECCIONAL — ajuste #6 campaña)
- Selección as-of strict point-in-time: GMM training cutoff ≤ ancla, lab_lite + walk-forward ≤ ancla; holdout post-ancla intocado.
- **Clasificación del holdout por la GMM as-of** (entrenada ≤ ancla): legítima (es lo que hace live — clasificar futuro con modelo pasado), NO leakage.
- Gate de leakage por celda (max-timestamp por artefacto ≤ ancla) + validación honesto-pasa / envenenado-caza ANTES de correr. FAIL → fase invalidada.

### Anti-artefacto (B.1) — integrado
El test MATCH/MISMATCH ES el aislador. Sin un Δ>0 robusto, NO se declara confirmación aunque la cartera condicional parezca buena (podría ser nivel, no condicionalidad).

### Presupuesto GPU (finito, dimensionado)
β: **5 símbolos × 2 anclas = 10 celdas × ~5–8h = ~50–80h GPU** secuencial estricto (#14). Réplica condicionalidad CPU (~trivial). Expandible si NO CONCLUYENTE.

### Libro mayor de holdouts (sin doble-dipping)
- **Primario sobre anclas RESERVADAS Fase 2** (ledger campaña: 2025-07, 2025-04; símbolos ETH/DOGE/BCH/XLM + 1 profundo) → holdouts FRESCOS, ledger-limpio.
- Re-análisis de las celdas E2-full QUEMADAS (BTC/SOL/LINK/LTC × A1/A2) = SECUNDARIO de robustez (re-análisis, NO re-selección sobre ellas) — admisible porque no se re-tunea sobre el holdout.

---

## B.4 — NO EJECUTAR. Entregable = este doc. Tier 3 para aprobación + elección α/β.

**INVARIANTES**: ULTRATHINK + §12 L35/L38 (la auditoría de contaminación desenmascaró 3 espejismos mecánicos — misma disciplina al confirmar D3: aislar el artefacto de relleno antes de creer) + §0.0 Frame 2 + §0.3. Pre-registro + holdout sagrado + aislar la alternativa = no repetir el espejismo a nivel meta. **D3 es CANDIDATA hasta Nivel 3.** Harness E2 as-of = gate permanente. `brain/portfolio/kernel/cancel_ghost` INTACTOS. §13.3 upgrade stack intacto. Caveats §13.2 #1–#22 (Caveat #13 = dataset ideal limpiado; α lo regeneraría). Bot v2.8.1 operacional 20/20, G5 PAUSADO.

## RESOLUCIÓN T3.1 — PENDIENTE (Ricardo)
1. **Aprobar el pre-registro** (hipótesis, 3 zonas, test MATCH/MISMATCH como aislador, anti-leakage bidireccional, presupuesto).
2. **Elegir α o β** (recomendado **β**; α solo si además quieres resucitar D4 + D2/D5 limpios — pase separado más caro).
3. **Confirmar anclas/símbolos** (reservadas frescas vs re-análisis de E2-full quemadas).

**Umbrales se CONGELAN al aprobar. NO GPU hasta T3.1.** Tras ejecución (pase posterior): T3.2 = veredicto de confirmación/refutación D3.
