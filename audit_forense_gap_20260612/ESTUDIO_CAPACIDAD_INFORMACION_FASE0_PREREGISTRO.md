# Estudio de Capacidad de Información — FASE 0 (Inventario) + PRE-REGISTRO

**Fecha**: 2026-06-16 · **Estado**: ✅ **PRE-REGISTRO APROBADO — T3.1 (Ricardo) 2026-06-16. UMBRALES CONGELADOS** — no se reajustan tras ver resultados (misma disciplina que la Campaña Edge Real). Read-only, sin GPU.

**Decisiones T3.1 congeladas (Ricardo 2026-06-16)**: (1) **Lista cerrada D1–D6 tal cual → m=6 tests primarios**; (2) **Nivel 1 = solo 45 JSONs productivos** (procedencia limpia; campaña ccv/eje como robustez secundaria reportada aparte, NO en test primario); (3) **decisor de SEÑAL = FDR Benjamini-Hochberg q=0.10 + Bonferroni α=0.0083 de referencia + CI95 bootstrap (por-símbolo) que excluya 0** (ambos requeridos).

**Métrica primaria fijada por dimensión (una por D, para m=6)**: D1=ρ(`pf_combined_bin`,`pf_fwd_bin`) sobre bloque2c N=60; D2=ρ(`pf_robustness`,`pf_fwd`) JSON; D3=ε² (tamaño de efecto del clúster sobre `pf_fwd`, Kruskal-Wallis per-símbolo); D4=AUC(`plateau_ratio` → fracaso `pf_fwd<1`) JSON; D5=ρ(`ci_width`,`pf_fwd`) JSON; D6=ρ(`specialist_score`,`pf_fwd`) JSON. Las demás métricas de cada dimensión = secundarias (se reportan, NO cuentan para m). **Unidad de análisis primaria**: ρ de Spearman WITHIN (símbolo,clúster) → media de los ~135 ρ; CI95 por **bootstrap remuestreando símbolos** (45, 10.000 reps). Pooled = diagnóstico secundario.

**Directive (Ricardo, 2026-06-16)**: mapear sistemáticamente qué dimensiones del pasado (si alguna) predicen el rendimiento forward, ANTES de construir Frame 3. Cimiento para la decisión estructural: o dirige Frame 3 a un eje con señal, o establece con rigor que ninguna dimensión disponible discrimina.

---

## ENCUADRE EPISTÉMICO (cardinal — gobierna las dos salidas)

- **PROBADO**: la métrica de selección ACTUAL (`pf_combined`, PF walk-forward → realizado) tiene **ρ≈+0.047** (Smoke C, N=60, commit `431b5e1`) y el edge realizado es ~0.70–0.85 PF neto (VEREDICTO FASE 1 campaña edge real, 2026-06-16). Una proyección del PF agregado del pasado falla.
- **NO PROBADO**: que NINGUNA dimensión del pasado prediga el futuro. El pasado tiene muchas dimensiones además del PF agregado. Este estudio las mapea.
- **Ambas salidas son producto válido**: señal detectada (tras corrección por multiplicidad) → dirige Frame 3 a ese eje; ninguna señal → implicación crítica establecida con rigor, ahorra meses sobre eje muerto.
- **§12 L35/L38 en ambas direcciones**: ni pescar una correlación espuria entre muchas para justificar esperanza, ni declarar "nada predice" por pereza. **Corrección por multiplicidad OBLIGATORIA**. Zona débil-pero-no-cero se reporta como "sugestivo, no demostrado" (igual que E2-full respetó la zona no-concluyente).

---

## PARTE 0.1 — INVENTARIO (read-only, hecho — primary-source verificado)

### A. Qué datos YA computados emparejan comportamiento-de-selección ↔ rendimiento-forward

| # | Dataset | Unidad | N | Dimensiones-pasado disponibles | Forward disponible | ¿Forward intocado por la selección? | GPU |
|---|---|---|---|---|---|---|---|
| **1** | `regime_wf/*_specialist_configs.json` (productivos) | config × clúster × símbolo | **13.500** (45 sym × 3 clúster × ~100 top) | `pf_tr, trades_tr, pnl_tr, sqn_combined, sqn_p5, sqn_n_neighbors, pf_robustness, plateau_ratio, cross_cluster_survival, adjacent_worst_pf, maxdd_worst, ci_width, specialist_score` | `pf_fwd, pf_fwd_ci_low/high, pnl_fwd, trades_fwd` (split doubled-labels 67/33) | **NO** — el forward (33%) entra en `pf_combined`→`specialist_score`→selección. Además **solo top-100 de 29M validados** (range restriction + collider) | no |
| **2** | JSONs de campaña (`ccv_phase1-4`, `eje*`, `para_smoke`) | idem | ~65 JSONs adicionales | idem #1 | idem #1 | idem #1 (variantes cross-class) | no |
| **3** | `bloque2c_smoke_c_results.csv` | config (top1/mid/tail) | **60** | `pf_tr_bin, trades_tr` | `pf_fwd_bin` **RE-COMPUTADO sobre velas Binance independientes** + `pf_combined_bin` | **Parcial** — re-cómputo en fuente de datos distinta (más cerca de "independiente"), pero misma ventana temporal 33%. **Muestreo estratificado** top1/mid/tail (mejor rango que top-100) | no |
| **3b** | `bloque2c_fase_a_results.csv` | config | 60 | `pf_combined_WF, trades_3y` | `pf_fwd_WF, PF_3y` (re-evaluación a 3 años), `ratio_wf_3y` (decay) | idem #3 + horizonte 3y más largo | no |
| **4** | E2-full as-of (`asof_result_*.json`, `asof_trades_*.csv`) | celda (sym×ancla) | **8 celdas / 163 trades** | config seleccionada as-of + prehistoria | PF neto realizado sobre **holdout estrictamente intocado** (anti-leakage 8/8 PASS) | **SÍ — el único verdaderamente intocado** | ya hecho (sin GPU adicional) |
| **5** | E2-lite (`replay_trades_*.csv`) | generación | **4 gen / 93 trades** | picks desplegados | PF neto realizado live Binance | SÍ (realizado live) | no |

### B. Dato IDEAL que NO está disponible (notado por 0.2 del directive)

- **`wf_experiment` (walk-forward masivo, 36 anclajes / "177M obs")** — `walk_forward_experiment.py` genera precisamente el dataset óptimo: **población COMPLETA de configs** (no solo top-100) × **múltiples anclajes rodantes** × forward evaluado **fuera de la ventana de selección** (selección solo sobre `opt_window`), con `analysis_correlations.csv` ya cableado. **Sus salidas (`checkpoint_*.parquet`) NO están en disco** (limpiadas por gestión de espacio, Caveat #13). Regenerarlo **requiere GPU** → **fuera de alcance de este pase (T3.3 si Ricardo lo decide)**. Es la única vía a un test per-config, gran-N, con población completa y forward limpio.

### C. HALLAZGO CARDINAL DE FASE 0 (gobierna el diseño y el alcance de las conclusiones)

> **Sin GPU, NO existe un dataset per-config de gran-N con forward verdaderamente intocado.** Lo que hay se parte en dos: (1) gran-N pero con forward EN-selección y rango restringido (JSONs, #1-2); (2) forward (semi-)independiente pero N pequeño (#3, N=60) o grueso a nivel-método (#4-5, 8 celdas / 4 gen).

**Consecuencia para el diseño — estudio de DOS NIVELES, honesto sobre lo que cada uno puede concluir:**

- **NIVEL 1 — SCREEN (barato, sin GPU, N≈13.500 sobre #1-2).** Mide ρ(dimensión-pasado, `pf_fwd`) dentro de los JSONs. **Sesgos conocidos — TODOS inflan la predictibilidad aparente** (forward en-selección + filtro top-100). Por tanto el screen es **conservador para MATAR, no para CONFIRMAR**:
  - Dimensión con ρ≈0 (CI cruza 0 tras corrección) **incluso en este caso fácil y sesgado-a-favor** → **muerta** (no predice ni el caso trivial). Resultado negativo fuerte y barato.
  - Dimensión con señal aquí → **CANDIDATA, NO confirmada** (el sesgo puede haberla fabricado). Pasa a Nivel 2 / T3.3.
  - **Sesgo de colisionador (cardinal)**: condicionar a top-100 (seleccionados por `specialist_score` ∝ `pf_combined` que incluye `pf_fwd`) induce asociación espuria entre `pf_tr` y `pf_fwd` (típicamente **negativa**). Por eso las dimensiones **PF-basadas** (D1) se miden con instrumento #3 (estratificado), y el screen JSON se reserva para dimensiones **ortogonales al score** (estabilidad, fracaso, dispersión), donde el colisionador es más débil (aunque persiste range-restriction sobre el outcome).

- **NIVEL 2 — ANCLA INDEPENDIENTE (barato, sin GPU, N=60 sobre #3/#3b).** Reproduce ρ=0.047 (sanity D1) y permite comprobar si una dimensión PF-basada sobrevive al re-cómputo sobre datos Binance independientes y al horizonte 3y. **El único contrapeso barato al sesgo del Nivel 1.**

- **NIVEL 3 — CONFIRMACIÓN VERDADERA (GPU, T3.3, NO este pase).** Cualquier candidata superviviente solo se confirma como edge real con holdout as-of intocado (estilo E2-full). Se **marca**, no se ejecuta.

**INTERPRETACIÓN OFICIAL DEL NIVEL 1 (congelada T3.1 — gobierna la lectura del veredicto)**: como los tres sesgos juegan A FAVOR de detectar señal, el Nivel 1 es **asimétrico por construcción**:
- **ρ≈0 en el caso fácil-y-sesgado-a-favor ⇒ dimensión MUERTA, sin ambigüedad** (no predice ni el caso trivial). Resultado negativo válido y barato.
- **Señal en el caso fácil ⇒ CANDIDATA, NUNCA confirmada** (el sesgo puede haberla fabricado). Solo Nivel 3 (GPU) confirma.

**Honestidad de alcance pre-registrada**: este pase entrega con rigor (a) **qué dimensiones están muertas** y (b) **qué dimensiones son candidatas** a confirmar con GPU. **NO puede, por sí solo, DEMOSTRAR edge real** (eso es Nivel 3). La salida "ninguna señal ni en el caso fácil" es, sin embargo, una **implicación crítica plena**: si nada predice ni el forward en-selección, la familia no es rescatable por re-selección sobre estas dimensiones.

---

## PARTE 0.2 — PRE-REGISTRO (lista CERRADA de dimensiones + reglas, CONGELADAS al aprobar)

### Unidad de análisis y CIs (anti-falso-positivo por no-independencia)

Las 13.500 filas **no son independientes** (45 símbolos × 3 clústeres). Tratarlas como iid daría CIs espuriamente estrechos. **Regla pre-registrada**:
- **ρ de Spearman calculado por (símbolo) y agregado** (mediana cross-símbolo + IQR), **Y** ρ pooled con **bootstrap por CLÚSTER de símbolo** (se remuestrean símbolos enteros, no filas; 10.000 réplicas). Se reporta el CI del bootstrap por-símbolo (el conservador).
- Se descarta `±inf`/`NaN` de PF (gl=0 → regla Smoke C), se winsoriza PF al p1/p99 antes de ρ (Spearman es rank-based, robusto, pero se documenta el recorte).

### Señal detectada — definición (PRE-REGISTRADA)

- **m = nº de tests primarios** (uno por dimensión D1–D6 = **6 tests primarios**; los secundarios por-dimensión NO cuentan para multiplicidad pero se reportan).
- **Corrección por multiplicidad**: **Benjamini-Hochberg FDR a q=0.10** sobre los 6 p-valores primarios (control de tasa de falsos descubrimientos, más potente que Bonferroni para un screen exploratorio) **Y** se reporta también el umbral Bonferroni (α=0.05/6=0.0083) como referencia conservadora.
- **"SEÑAL"** ≡ ρ con **CI95 bootstrap (por-símbolo) que excluye 0** **Y** p-valor que sobrevive FDR q=0.10. Ambos requeridos.
- **"SUGESTIVO, no demostrado"** ≡ |ρ| material (≥0.10) pero CI roza/cruza 0 o no sobrevive FDR. Se reporta como tal, sin redondear.
- **"MUERTA"** ≡ CI cruza 0 y |ρ| < 0.10.
- **Magnitud mínima de interés**: dado que el caso es fácil-y-sesgado-a-favor, se pre-registra que una señal de Nivel 1 con |ρ|<0.15 es **débil aun siendo significativa** (N grande infla significancia) — se reporta el tamaño del efecto, no solo el p.

### Lista CERRADA de dimensiones candidatas (fijada ANTES de computar)

| Dim | Hipótesis (qué dimensión-pasado) | Instrumento primario | Test primario | Outcome forward | Notas de sesgo |
|---|---|---|---|---|---|
| **D1** | **PF histórico** (`pf_combined`/`pf_tr`) — BASELINE | #3 estratificado (N=60) | ρ(`pf_combined_bin`, `pf_fwd_bin`) **+ reproducir ρ(`pf_fwd_JSON`,`pf_fwd_bin`)≈0.047** | `pf_fwd_bin` (recomputado Binance) | sanity del método + línea base. JSON como secundario (colisionador) |
| **D2** | **Estabilidad cross-régimen / vecindario** | #1-2 JSON (N≈13.5k) | ρ(`cross_cluster_survival`∈{0,1} → point-biserial; `pf_robustness`; `sqn_n_neighbors`; `adjacent_worst_pf`) vs `pf_fwd` | `pf_fwd` (en-selección) | dim ortogonal al score → colisionador débil. Range-restriction persiste |
| **D3** | **Contexto/régimen en la selección** (núcleo Frame 3, versión barata) | #1-2 JSON | Kruskal-Wallis de `pf_fwd` entre clústeres (¿el régimen explica varianza forward?) + ρ(estacionariedad `transition_matrix` diag, `pf_fwd`) | `pf_fwd` | pre-test barato de Frame 3; versión intocada (régimen-por-trade) es GPU (T3.3) |
| **D4** | **Perfil de fracaso** (asimetría éxito vs fracaso; hipótesis Ricardo) | #1-2 JSON | AUC/point-biserial de predictores (`trades_tr>150`, \|`pnl_tr`\| extremo, `maxdd_worst`, `flag_sospechoso_outlier`, `plateau_ratio` bajo) sobre **fracaso forward** (`pf_fwd<1`) **vs** sobre **éxito** (`pf_fwd≥1.5`) | binario `pf_fwd<1` | mide si **predecir quién FALLA** es más robusto que predecir quién gana |
| **D5** | **Dispersión/forma del rendimiento** | #1-2 JSON | ρ(`ci_width`, `pf_fwd_ci_high−pf_fwd_ci_low`, `sqn_p5`) vs `pf_fwd` | `pf_fwd` | proxy de varianza inter-vecino; verdadera varianza inter-subperíodo sería GPU |
| **D6** | **Score de selección compuesto + decay** | #1-2 JSON + #3b | ρ(`specialist_score`, `pf_fwd`) [score completo] + ρ(`ratio_wf_3y`/`PF_3y`, forward) [decay/horizonte largo] | `pf_fwd` / `PF_3y` | D6 = "¿el blend completo añade sobre `pf_combined`?" + única mirada a horizonte 3y |

> **D6 está propuesto, no fijado.** Si Ricardo quiere añadir/quitar una dimensión de la lista cerrada, debe hacerlo **en T3.1, antes de computar** — añadir una dimensión después de ver resultados la convierte en un experimento nuevo y rompe la honestidad de la multiplicidad. m se recalcula con la lista final.

### Datasets y procedencia (congelado)

- Nivel 1: `regime_wf/*_specialist_configs.json` (45 productivos, `generated` 2026-04→05) + opcionalmente campaña (se decide en T3.1 si se incluyen; por defecto **solo productivos** para limpieza de procedencia, campaña como robustez secundaria).
- Nivel 2: `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c_results.csv` (N=60) + `bloque2c_fase_a_results.csv` (N=60).
- Ancla de verdad (no se re-mide, se cita): E2-full 163 trades / 8 celdas + E2-lite 93 / Smoke C ρ=0.047.

---

## PARTE 0.3 — FASE 1+2 (lo que se ejecutará TRAS aprobación T3.1)

- **FASE 1**: batería D1–D6, cada una con ρ + CI bootstrap por-símbolo, point-biserial/AUC donde aplique, sobre el instrumento primario pre-registrado. Script read-only puro (parsea JSON/CSV; **no toca** `live/*`, ni pipeline, ni GPU).
- **FASE 2 — Tabla de capacidad + veredicto (T3.2 PAUSE)**:
  - 2.1 Tabla D1–D6: ρ, CI corregido, p (FDR + Bonferroni), veredicto individual (SEÑAL / SUGESTIVO / MUERTA).
  - 2.2 Veredicto global:
    - **Alguna SEÑAL** (sobrevive Nivel 1 y, si PF-basada, Nivel 2) → identifica el eje; **recomendación**: diseñar Frame 3 explotando ESE eje, con su pre-registro y **confirmación Nivel 3 (GPU, T3.3) ANTES de construir**.
    - **Ninguna SEÑAL ni en el caso fácil** → implicación crítica: la familia no es rescatable por re-selección sobre ninguna dimensión disponible. Decisión estructural honesta, sin GPU en Frame 3 sobre eje muerto.
  - 2.3 Honestidad de zona: débil-pero-no-cero → "sugestivo, no demostrado". Siempre se reporta el tamaño del efecto junto al p (N grande infla significancia).

---

## AUTORIZACIONES Y TIER 3 (del directive)

- **FASE 0 + este pre-registro**: AUTO-execute, read-only ✅ (hecho). **T3.1 = tu aprobación de la lista cerrada + umbral corregido ANTES de computar Fase 1.**
- **FASE 1+2**: AUTO-execute tras aprobación T3.1. **SIN GPU.**
- **T3.2** = tabla de capacidad + veredicto (dirige Frame 3 / implicación crítica).
- **T3.3** = si una candidata exige confirmación con GPU (regenerar `wf_experiment` población-completa, o as-of holdout estilo E2-full) → decisión de si vale el cómputo. **No se ejecuta en este pase.**
- **NINGÚN** cambio productivo, deploy, G5, ni construcción de Frame 3 sin Tier 3. Bot v2.8.1 operacional 20/20, G5 PAUSADO. `brain/portfolio/kernel/cancel_ghost` INTACTOS. Harness E2 as-of = gate permanente de cualquier Frame 3 resultante.

---

## RESOLUCIÓN T3.1 — PENDIENTE (Ricardo)

Decisiones a congelar antes de Fase 1:
1. **Lista cerrada de dimensiones**: ¿D1–D6 tal cual, o ajustar/añadir D6+? (afecta m de la multiplicidad).
2. **Inclusión de JSONs de campaña** en Nivel 1: ¿solo 45 productivos (procedencia limpia) o + campaña como robustez?
3. **Umbral de multiplicidad**: ¿FDR q=0.10 (propuesto) + Bonferroni de referencia, o exiges Bonferroni estricto como decisor?
4. **Confirmación del encuadre de DOS NIVELES**: aceptas que este pase MATA o NOMINA candidatas, pero la confirmación de edge real es Nivel 3 (GPU, T3.3).

**Umbrales se CONGELAN al aprobar. Fase 1 NO ejecuta hasta T3.1.**

---

## ESTADO — FASE 1+2 EJECUTADAS (2026-06-16, read-only, sin GPU) → T3.2 PAUSE

Harness `estudio_capacidad_fase1.py` + resultados `estudio_capacidad_fase1_results.json`. **Veredicto completo en `VEREDICTO_ESTUDIO_CAPACIDAD.md`**. Resumen: D1/D2/D5 = SEÑAL MECÁNICA (contaminadas por `pf_fwd`: `pf_combined`⊃`pf_fwd`, `pf_robustness=pf_fwd/pf_tr`, `ci_width` del CI forward); D4 = NO EVALUABLE (0% fracasos en top_configs); D6 `specialist_score` = MUERTA (ρ+0.05, CI cruza 0); **D3 régimen/contexto ε²=0.574 = única señal limpia (CANDIDATA, requiere N3-GPU)**. Panel limpio: `pf_tr→pf_fwd` +0.30 en-slice → **−0.05 en datos independientes** (persistencia no transferible); canónico ρ=+0.0465 reproducido. **PAUSA T3.2 — decisión estructural Ricardo.**
