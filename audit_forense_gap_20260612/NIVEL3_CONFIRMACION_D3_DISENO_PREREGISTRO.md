# Nivel 3 — Confirmación de D3 + D4 (+ D2/D5) — DISEÑO + PRE-REGISTRO CONSOLIDADO

**Fecha**: 2026-06-16 · **Estado**: 🟡 **PRE-REGISTRO CONSOLIDADO — PENDIENTE T3.1 (Ricardo): aprobación final + presupuesto GPU ANTES de lanzar. NO ejecutar GPU en este pase.** Dataset = **α (población-completa)** APROBADO por Ricardo (habilita D3+D4+D2/D5 en un cómputo vs β solo-D3 + regen futura cara). Mismo patrón que funcionó 2× (Campaña Edge Real, Estudio de Capacidad): diseñar+pre-registrar → Tier 3 → ejecutar.

> **DISTINCIÓN CARDINAL (la lección de la sesión, explícita y gobernante)**: mirar el pasado para **TESTEAR una regla estructural fijada de antemano** sobre holdout intocado = VÁLIDO (D3, D4). Mirar el pasado para **DESTILAR qué config/firma habría ganado y construir una regla que la elija** = INGENIERÍA INVERSA = sobreajuste garantizado (E1 lo probó: sobre ruido puro SIEMPRE existe un "ganador"). El script `walk_forward_experiment.py` se titula "ingeniería inversa" — uso LEGADO; aquí solo **genera el dataset emparejado**; las reglas D3/D4 se **fijan ANTES** y se testean sobre tramos FRESCOS. Prohibido derivar la firma de los perdedores del holdout; obligado fijarla a priori y luego medir.

**Sección original (B.1–B.4)** = lógica del aislador D3, preservada abajo. **La VERSIÓN CONSOLIDADA al final supersede la recomendación α/β** (α elegido) y añade D4 con rigor completo + D2/D5 secundario + m de multiplicidad + presupuesto.

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

---
---

# VERSIÓN CONSOLIDADA — D3 (primario) + D4 (primario) + D2/D5 (secundario) sobre α — 2026-06-16

*(Supersede la recomendación α/β: Ricardo eligió α. D3 confirmado tal cual + D4 con rigor completo + D2/D5 como oportunidad barata del mismo dataset.)*

## 1. Dataset α — qué es, qué habilita, qué hay que INSTRUMENTAR

**α = regenerar el walk-forward población-COMPLETA** (`walk_forward_experiment.py`, borrado Caveat #13). Estructura verificada primary-source: 45 símbolos (`DEFAULT_SYMBOLS`), ventanas `opt=5000 / ext=2000 / fwd=2000 / step=2000 / warmup=500`, anclajes rodando desde lo más reciente hacia atrás (`compute_anchor_points` L253 — deep-history → ~35 anclajes, alinea con "36 anchors"), forward dividido en h1/h2 (dispersión nativa), etiquetado `alpha_good/bad ±2.0`, `pf_good 1.2 / pf_bad 0.8`. **Población COMPLETA con FRACASOS** (no el top-100 que los borraba) + forward FUERA de la ventana de selección por anclaje (untouched per-anchor).

**Habilita en UN cómputo**: D3 (régimen-conditionality), D4 (firma de fracaso, ahora hay fracasos), D2/D5 limpios (estabilidad/dispersión train-only sobre población completa).

**INSTRUMENTACIÓN REQUERIDA (harness test-only, NO toca `live/*` ni la lógica del kernel)** — porque `walk_forward_experiment.py` es **régimen-AGNÓSTICO** (descubre gems vía lab_lite sin split por régimen):
1. Clasificar el régimen de cada barra con la GMM as-of (entrenada ≤ `opt_end` del anclaje — point-in-time, sin leakage).
2. Selección PER-RÉGIMEN sobre la ventana opt (specialist por clúster, como producción).
3. Evaluar cada specialist sobre la ventana fwd (intocada), **split por el régimen concurrente** → produce MATCH/MISMATCH (D3) + el forward con fracasos (D4) + dispersión h1/h2 (D5).
El harness se verifica output-neutral respecto al kernel (solo controla entrada/clasificación/split), igual que el harness E2.

## 2. Anclas FRESCAS (holdout sagrado — el primario no reusa holdouts quemados)

Quemados: **E2-full** = BTC/SOL/LINK/LTC × [2025-10-01, 2026-05-17); **E2-lite** = 20 símbolos desplegados × [2026-05-17, ahora).
- **PRIMARIO = anclajes cuya ventana fwd NO intersecta ningún holdout quemado** (regla precisa, N-eficiente): conserva todo fwd pre-2025-10-01 para los 45 símbolos + post-2025-10 para los 41 no-E2-full (salvo su ventana live). Regla simple alternativa = fwd entera < 2025-10-01 (universalmente fresca) si Ricardo prefiere máxima limpieza sobre N.
- **SECUNDARIO/robustez** = anclajes que intersectan holdouts quemados → reportados APARTE, nunca en el veredicto primario.
- Confirmación de frescura codificada por anclaje (timestamp de fwd vs windows quemadas), análoga al gate E2.

## 3. D3 — PRIMARIO (test MATCH/MISMATCH, ya aprobado A.1)
Sin cambios respecto a B.1–B.3. Δ = PF_match − PF_mismatch sobre fwd intocado per-anchor, CI95 bootstrap por-símbolo. 3 zonas: **CONFIRMADA** (Δ CI inf>0 ∧ PF_match net CI inf>1.0 ∧ cartera condicional>agnóstica) / **MATADA** (Δ≤0 o PF_match sup<1.0) / **NO CONCLUYENTE** (más anclas/símbolos). Aísla H_real vs H_artefacto (relleno por clúster).

## 4. D4 — PRIMARIO (firma de fracaso como REGLA DE EXCLUSIÓN, rigor completo)

**B.1 Hipótesis falsable (fijada ANTES de ver resultados)**: existe una **firma de fracaso —definida SOLO sobre la ventana de selección— que predice qué configs FALLAN forward, estable a través de tiempo/regímenes**. La regla **EXCLUYE** configs con la firma; NO selecciona ganadoras (caracterizar el fracaso, hipótesis Ricardo).

**B.2 ANTI-INGENIERÍA-INVERSA (cardinal)**: la firma se define **a priori** desde campos estructurales nombrados, NUNCA buscándola sobre los fracasos del holdout. **Firma candidata CONGELADA** (campos de la ventana de selección, todos pre-nombrados):
  - `trades_tr` extremo (overtrading; umbral pre-fijado: > p90 within-celda **o** absoluto >150);
  - `maxdd_tr` extremo (drawdown selección);
  - `pnl_tr` outlier alto (sobreajuste; |z|>2 within-celda);
  - `flag_sospechoso_outlier` (flag propio del pipeline);
  - baja robustez param-espacio (`plateau_ratio` < 0.2).
  - **Composite primario** = z-score equal-weight de estos 5 campos (sin libertad de pesos post-hoc); "tiene firma" = composite en el cuartil superior (cutoff pre-fijado).

**B.3 Test sobre holdout intocado** (mismos tramos FRESCOS de D3): ¿las configs con firma fallan forward (`pf_fwd<1` o `alpha<alpha_bad`) con AUC/separación significativa vs las que no? AUC del composite, CI95 bootstrap por-símbolo. Univariante por campo = secundario/diagnóstico (reportado, no decisor).

**B.4 — 3 zonas (congeladas)**: **PREDICTIVA** (AUC CI95 inf > 0.5 → regla de exclusión viable; cuantificar cuántas configs excluiría y el lift) / **NO PREDICTIVA** (AUC CI95 incluye/≤0.5 → moneda al aire, D4 cerrada) / **NO CONCLUYENTE** (CI cruza 0.5 con AUC material → más datos).

## 5. D2/D5 — SECUNDARIO (oportunidad del mismo dataset, NO foco, NO decisor)
- **D2 limpio**: `pf_tr`-train estabilidad cross-anclaje + cross-régimen (recomputada train-only, sin la contaminación `pf_fwd/pf_tr`).
- **D5 limpio**: dispersión real entre los 5 tramos fwd (y h1 vs h2) como predictor.
- ρ + CI bootstrap por-símbolo, **reportados como exploratorios** — el screen los dejó débiles/mecánicos; α los limpia barato porque el dataset se genera igual. **NO entran en la multiplicidad ni en ningún veredicto estructural.**

## 6. Multiplicidad — m FIJADO ANTES de computar
**m = 2 tests PRIMARIOS decisores**: D3 (Δ conditionality; PF_match>1 es condición de la MISMA hipótesis, no test aparte) + D4 (composite firma-fracaso AUC). **Corrección: Bonferroni α = 0.025 por test + FDR-BH q=0.10 de referencia**; "señal" exige además CI95 bootstrap por-símbolo excluyendo el nulo (0 para Δ, 0.5 para AUC). D2/D5 + univariantes D4 = secundarios, NO cuentan para m, reportados con tamaño de efecto. Si Ricardo decide elevar D2/D5 a decisores → m=4 (recalcular antes de computar).

## 7. Presupuesto GPU (C.2 — dimensionado, con disciplina de safety-factor)
α regenera población-completa multi-anclaje: **el cómputo más grande del proyecto** ("177M obs" precedente). D3+D4+D2/D5 salen del MISMO dataset (coste ≈ generar la población, NO ×4).
- **Proyección** (sin smoke, por tanto con 5–10× incertidumbre mandatoria — `feedback_compute_estimates_frame3`): 45 sym × ~20–35 anclajes × selección per-régimen ≈ **orden de varios días a ~2 semanas GPU** secuencial estricto (#14). **Subset representativo fresco (12–15 símbolos cross-categoría, anclajes pre-2025-10)** ≈ **~1–3 días** y basta para el test con bootstrap por-símbolo (no se necesitan los 45 para potencia).
- **Riesgo de DISCO (Caveat #13/#3)**: parts dirs ~200–300 GB/run precedente E1 → auto-cleanup por símbolo/anclaje OBLIGATORIO en el harness (patrón `shutil.rmtree _parts_*` ya validado).
- **EJECUCIÓN PASO 0 = SMOKE de calibración** (2 símbolos, pocos anclajes) ANTES del run completo → recalibra horas + disco reales → reconfirmar presupuesto. El smoke es GPU → pertenece al pase de ejecución (T3.2), NO a este.

## 8. RESOLUCIÓN T3.1 CONSOLIDADA — PENDIENTE (Ricardo)
1. **Aprobar el pre-registro consolidado** (D3 primario + D4 primario rigor completo + D2/D5 secundario, m=2, zonas congeladas, firma de fracaso congelada a priori).
2. **Confirmar subset de símbolos** (45 completo ~días-semanas vs subset fresco 12–15 ~1–3 días — recomendado el subset, expandible si NO CONCLUYENTE).
3. **Confirmar regla de frescura** (intersección precisa N-eficiente — recomendada — vs fwd<2025-10 máxima limpieza).
4. **Aprobar el presupuesto** sabiendo que la ejecución empieza por un smoke de calibración que lo reconfirma.

**Umbrales/firma/zonas se CONGELAN al aprobar. NO GPU hasta T3.1.** Ejecución (pase siguiente): smoke → reconfirmar presupuesto → run → T3.2 veredicto D3 (CONFIRMADA/MATADA/NO CONCLUYENTE) + D4 (firma predictiva/no) + D2/D5.

---
---

# PREPARACIÓN T3.1-bis — Subset + Frescura (decisiones 2 y 3) + Protocolo de smoke — 2026-06-16

*(Read-only ejecutado: `nivel3_subset_freshness.py` + `nivel3_subset_freshness.json`. APROBADO subset 12-15 + frescura exacta + smoke-primero por Ricardo.)*

## Decisión 2 — SUBSET (13 símbolos) con cobertura de régimen VERIFICADA

| sym | cat | anclajes FRESCOS | minClu% | clusters (tipos de régimen) |
|---|---|---|---|---|
| ETH | amplio | 34 | 31.7 | low/norm-vol × choppy/efficient |
| BNB | amplio | 33 | 27.5 | norm/high/low-vol choppy |
| XRP | amplio | 31 | 24.8 | norm/high-vol choppy |
| ATOM | amplio | 27 | 28.5 | norm/high/low-vol choppy |
| THETA | amplio | 27 | 27.0 | high/low/norm-vol choppy |
| ALGO | amplio | 26 | 28.6 | norm/high/low-vol choppy |
| DOT | amplio | 21 | 29.0 | low/norm/high-vol choppy |
| AVAX | amplio | 20 | 29.1 | norm-vol efficient + choppy + low-vol |
| FET | medio | 27 | 23.5 | low/norm-vol choppy + high-vol efficient |
| STX | medio | 24 | 27.4 | low-vol efficient + norm/high-vol choppy |
| INJ | medio | 20 | 25.6 | norm-vol choppy/efficient + low-vol |
| IMX | medio | 15 | 28.7 | low-vol choppy + norm-vol efficient/choppy |
| OP | medio | 13 | 27.9 | high/low-vol choppy + norm-vol efficient |

- **Cobertura de régimen verificada**: cada símbolo tiene **3 clústeres poblados** (minClu% 23.5–31.7%, sin celdas vacías → MATCH/MISMATCH de D3 tendrá N por celda). Colectivamente cubren los arquetipos low/norm/high-vol × choppy/efficient. **Bootstrap por-símbolo sobre 13 símbolos**.
- **Cross-categoría**: 8 amplio + 5 medio. **extr.bajo (ONDO/POL/RENDER) NO representable** en α: 0/2/3 anclajes frescos (historia <1.8y) — limitación de cobertura honesta, censada (DIAG: extr.bajo = 3 sym/7% cartera).
- **318 anclaje-evaluaciones** totales (Σ frescos) × ~30 gems × 3 clústeres forward → miles de observaciones config×régimen para los tests.

## Decisión 3 — FRESCURA EXACTA (holdout sagrado, verificable)

Holdouts quemados: **E2-full** = {BTC, SOL, LINK, LTC} × [2025-10-01, 2026-05-17); **E2-lite** = 20 desplegados × [2026-05-17, 2026-06-16).

**El subset es fresco por DOBLE garantía exacta y verificable**:
1. **Ningún símbolo del subset es E2-full** (BTC/SOL/LINK/LTC excluidos a propósito) → la exclusión [2025-10-01, 2026-05-17) NO aplica a ningún símbolo elegido.
2. **`data_cache` de los 13 termina ≤ 2026-05-08** (último reciclaje) **< 2026-05-17 (inicio E2-lite)** → ninguna ventana forward puede tocar la ventana live E2-lite (no existe en los datos).
→ **0 intersección con holdouts quemados, por construcción.** (`nivel3_subset_freshness.py:fresh_anchors` codifica el cálculo exacto barra-a-barra; para el subset, fresh==total en los no-E2-full.)

## Protocolo de SMOKE (calibración de RECURSOS — NO se mira veredicto D3/D4)

- **2 símbolos que acotan el coste**: **ETH** (76.349 barras / 34 anclajes = techo) + **OP** (34.496 / 13 = piso).
- **Modo `--eval-all-train`** (población-completa = el modo con fracasos para D4 y el de mayor disco/`_parts_all_train_*`).
- **Acotado**: `--max-anchors 2-3` por símbolo + auto-cleanup `_parts_*` por anclaje (Caveat #13) + monitor de disco y VRAM (8 GB).
- **Mide**: wall-time/anclaje + GB-parts/anclaje → extrapola a 13 sym × Σanclajes. **Prohibido inspeccionar el MATCH/MISMATCH o el AUC de los 2 símbolos** (sesgaría; el veredicto sale SOLO del run completo de 13).

## ⚠️ HALLAZGO DE ENTORNO — el smoke NO puede ejecutarse fielmente en esta sesión

- `numba.cuda.is_available() = False` en este entorno (aunque `cuda.detect()` ve la **RTX 5070 Laptop, cc12.0, [SUPPORTED]**; el linkage del runtime CUDA que usó el reciclaje productivo NO está expuesto aquí). El kernel lab usa `numba.jit/prange` (CPU) + `_cuda_sim` (acelerador GPU opcional, =None sin CUDA).
- Correr α **CPU-only aquí daría tiempos MIS-calibrados** (el GPU es el componente a medir) → viola el propósito del smoke (§12 L38). Además los runs GPU locales son frágiles (TDR 0x116, Caveats #17-19, VRAM 8 GB).
- **Decisión honesta**: NO se ejecuta un smoke con números falsos. El smoke debe correr en el **entorno GPU probado del reciclaje** (driver 596.02, chunking v18).

## RESOLUCIÓN T3.1-bis — PENDIENTE (Ricardo)
1. **Confirmar subset 13 + frescura** (arriba) — o ajustar símbolos.
2. **Ejecutar el smoke (ETH+OP, eval-all-train, max-anchors≈2-3) en el host GPU del reciclaje** → recalibrar horas/disco reales.
3. **Aprobar el presupuesto recalibrado** → entonces run completo de los 13 → T3.2 veredicto.
- Hasta tener números reales del smoke, el presupuesto sigue siendo PROYECCIÓN (subset 13 ~1–3 días GPU, 5-10× incertidumbre, disco ~200-300 GB/run-completo con cleanup). **NO run completo sin T3.1-bis.**
