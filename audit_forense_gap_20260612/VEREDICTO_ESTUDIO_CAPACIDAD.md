# VEREDICTO — Estudio de Capacidad de Información (FASE 2 / T3.2) — 2026-06-16

**Pregunta** (Ricardo): ¿qué dimensiones del pasado (si alguna) predicen el rendimiento forward, ANTES de construir Frame 3? Read-only, sin GPU, sobre datos ya generados.

**Disciplina**: pre-registro CONGELADO T3.1 (D1–D6, m=6, FDR-BH q=0.10 + Bonferroni α=0.0100, bootstrap por-símbolo, interpretación N1 asimétrica). Resultados en `estudio_capacidad_fase1_results.json`; harness read-only `estudio_capacidad_fase1.py`.

**Encuadre de alcance (congelado)**: el Nivel 1 (screen, N=13.500) MATA (ρ≈0 en caso fácil-sesgado-a-favor = muerta) pero NUNCA confirma (señal = candidata). El Nivel 2 (bloque2c N=60) es el único contrapeso barato con datos independientes. La confirmación de edge real es Nivel 3 (GPU, T3.3, NO este pase). **Este pase entrega "muertas vs candidatas", NO "edge demostrado".**

---

## 1. Tabla de capacidad — tests primarios congelados (tal cual corridos)

| Dim | Dimensión (métrica primaria) | stat | est | CI95 (boot por-símbolo) | p | FDR | Veredicto literal |
|---|---|---|---|---|---|---|---|
| D1 | PF histórico (`pf_combined`, bloque2c N=60) | ρ | 0.263 | [+0.007, +0.516] | 0.043 | ✔ | SEÑAL† |
| D2 | Estab. cross-régimen (`pf_robustness`) | ρ | 0.393 | [+0.305, +0.472] | ~0 | ✔ | SEÑAL† |
| **D3** | **Contexto/régimen (ε² del clúster)** | ε² | **0.574** | [+0.510, +0.630] | ~0 | ✔ | **SEÑAL (limpia)** |
| D4 | Perfil de fracaso (`plateau→fracaso` AUC) | AUC | — | — | — | — | **NO EVALUABLE** |
| D5 | Dispersión (`ci_width`) | ρ | 0.234 | [+0.097, +0.370] | 0.0004 | ✔ | SEÑAL† |
| D6 | Score compuesto (`specialist_score`) | ρ | 0.054 | [−0.010, +0.117] | 0.092 | ✔ | **MUERTA** |

**† = SEÑAL MECÁNICA (inválida como dimensión-pasado).** Auditoría de contaminación verificada en `regime_walk_forward.py`:
- `pf_combined` = blend ponderado que **contiene `pf_fwd`** → D1 es auto-correlación.
- `pf_robustness = min(pf_fwd / pf_tr, 1.5)` (L2055) → D2 **lleva `pf_fwd` en el numerador**.
- `ci_width = pf_fwd_ci_high − pf_fwd_ci_low` (L1239) → D5 derivado del CI del forward, escala con la magnitud del PF.
- `cross_cluster_survival` / `adjacent_worst_pf` = función del `pf_fwd` en clústeres adyacentes → contaminados.

**D4 NO EVALUABLE por construcción**: los `top_configs` productivos filtran TODO fracaso forward — **base rate de `pf_fwd<1` = 0.00%** (95.1% tienen `pf_fwd≥1.5`; rango winsorizado [1.24, 9.40]). No hay fracasos que predecir en N1. (Hallazgo que FASE 0 no anticipó; el primario congelado se declara inadmisible, NO se sustituye para cazar resultado.)

---

## 2. Panel limpio — dimensiones NO contaminadas por `pf_fwd` (within-cell N1, bootstrap por-símbolo)

| Dimensión (pura-pasado) | ρ con `pf_fwd` (N1) | CI95 | N | ¿transfiere a datos independientes (N2)? |
|---|---|---|---|---|
| `pf_tr` (PF train puro = D1 limpio) | **+0.297** | [+0.243, +0.352] | 13.500 | **NO** → en bloque2c ρ(`pf_tr_bin`,`pf_fwd_bin`) = **−0.05** |
| `plateau_ratio` (robustez param-espacio = D2/D5 limpio) | +0.134 | [+0.060, +0.210] | 5.859 | no comprobable barato (bloque2c no lo tiene) → N3-GPU |
| `trades_tr` (nº trades train) | **−0.591** | [−0.646, −0.537] | 13.500 | inconsistente → bloque2c AUC(trades→fracaso)=0.43 (signo opuesto) |
| `pnl_tr` (PnL train) | −0.222 | [−0.283, −0.159] | 13.500 | no comprobable barato |
| `maxdd_worst` (drawdown) | −0.268 | [−0.323, −0.212] | 13.500 | no comprobable barato |

**Ancla Nivel 2 (bloque2c N=60, datos Binance independientes)**: ρ(`pf_fwd_JSON`,`pf_fwd_bin`) = **+0.0465 ≈ +0.047** (el nulo canónico, REPRODUCIDO exactamente). ρ(`pf_tr_bin`,`pf_fwd_bin`) = **−0.05**.

**Lectura cardinal del panel**: existen relaciones no-nulas DENTRO de la rebanada de selección (hasta \|ρ\|≈0.59), es decir el pasado SÍ ordena el forward **en-muestra**. PERO la única dimensión pura-pasado que se puede cruzar contra datos independientes (`pf_tr`) **colapsa de +0.30 a −0.05** fuera de la rebanada. La persistencia es **específica de la rebanada de datos, no un edge transferible** — exactamente lo que la selección ya explota y que Frame 2 demostró que no llega a live (ρ=0.047).

---

## 3. VEREDICTO (muertas vs candidatas — honesto en ambas direcciones)

**NO es "nada predice"** (sería sobregeneralizar, §12 L38): within-slice varias dimensiones ordenan el forward, y **el régimen/contexto (D3) porta una señal grande y NO mecánica** (ε²≈0.57). El eje de Frame 3 está VIVO a nivel screen.

**NO es "encontramos edge"** (sería pescar, §12 L35): toda dimensión PF/calidad/estabilidad que se pudo cruzar contra datos independientes colapsó (`pf_tr` +0.30→−0.05; canónico +0.047) o es mecánica (`pf_combined`/`pf_robustness`/`ci_width`). **El `specialist_score` — la métrica que el pipeline realmente usa para rankear — tiene ρ≈+0.05 con CI que cruza 0 = MUERTA** incluso within-slice. La hipótesis de Ricardo del **perfil de fracaso (D4)** NO es evaluable barato (selección elimina los fracasos) y, en datos independientes, los predictores de fracaso son moneda al aire (AUC 0.43–0.57).

### Conclusión dirigida
1. **Re-seleccionar por PF/calidad/estabilidad está muerto o es mecánico** — confirmado a nivel config, consistente con H2 y con el VEREDICTO FASE 1. Refinar la selección sobre estas dimensiones NO rescata la familia.
2. **El único eje con señal limpia es el régimen/contexto (D3)** — y es precisamente el paradigma de Frame 3 (Market Regime Clustering de contexto) que Ricardo ya concibió. **Es una CANDIDATA, no una confirmación**: la señal es N1 en-selección y admite explicación alternativa (cada clúster se rellena con selección independiente → diferencias de nivel entre régimenes). **Requiere confirmación Nivel 3 (GPU) ANTES de construir Frame 3.**

---

## 4. Qué iría a Nivel 3 (GPU, T3.3 — decisión Ricardo, NO este pase)

Confirmación de D3 como edge real, no artefacto de selección. Dos vías (ambas GPU):
- **(a) Regenerar el walk-forward masivo población-completa** (`walk_forward_experiment.py`, 36 anclajes — borrado por espacio): da ρ(dimensión, forward) sobre la población COMPLETA (sin range-restriction ni colisionador) y con forward fuera de la ventana de selección. Permitiría además rescatar D4 (con fracasos) y los D2/D5 limpios (recomputando métricas train-only).
- **(b) Holdout as-of estilo E2-full pero régimen-condicional**: ¿el régimen identificado point-in-time predice qué specialist rinde sobre el holdout intocado? Reusa el harness E2 (gate permanente) + truncador as-of ya validados.

**Costo estimado** (calibrado §13.2): (a) ~población-completa cross-N-sym, días de GPU; (b) reusa infra E2-full (~5–8h/celda). Decisión de si vale el cómputo = T3.3.

---

## 5. Caveats de honestidad (§12 L38)
- **Todo N1 es en-selección + range-restricted** (top-100 de 29M, sin fracasos): infla la predictibilidad aparente y atenúa por restricción de rango simultáneamente. Por eso la lectura decisiva es el cruce N1→N2, no el valor N1 absoluto.
- **N2 es N=60** (CI anchos); su valor es la DIRECCIÓN (colapso de la persistencia), no la magnitud precisa.
- **D3 ε² no distingue** "régimen porta edge explotable" de "la selección per-clúster rellena clústeres con niveles distintos de PF". Solo N3 (untouched, régimen-by-trade) lo dirime.
- **D4 quedó sin test limpio**: la familia productiva no contiene fracasos forward; afirmar algo sobre el perfil de fracaso exige población completa (N3-GPU).
- Sin tocar `live/*`. Bot v2.8.1 operacional 20/20, G5 PAUSADO. Harness E2 as-of = gate de cualquier Frame 3.

---

## 6. Pendiente Ricardo (T3.2 → decisión estructural)
**Opciones** (no técnicas):
1. **Autorizar Nivel 3-GPU para confirmar D3** (régimen/contexto) antes de construir Frame 3 — la vía dirigida que este estudio respalda. (T3.3)
2. **Construir Frame 3 directamente sobre el eje régimen/contexto** asumiendo el riesgo de no-confirmación previa (más rápido, menos riguroso — contra la disciplina E2-gate).
3. **Cerrar la familia**: aceptar que la re-selección está muerta y el único eje vivo (D3) no justifica el cómputo → operar/monitorizar como está (breakeven esperado) o pivotar de paradigma.
4. **Otra** refinación que el resultado sugiera.

**CONGELADO**: m=6, umbrales, interpretación asimétrica N1 — no se reajustan. Tier 3 en T3.3 si autorizas Nivel 3.
