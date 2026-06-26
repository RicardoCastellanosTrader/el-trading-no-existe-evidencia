# PRE-REGISTRO CONGELADO — Atribución por Componentes, Experimento #1: "Medias aisladas"

**Fecha congelación:** 2026-06-26 · **Estado:** FROZEN (T3.1 aprobado por Ricardo con ajustes) · **Rama de trabajo:** `migracion-kraken` (artefactos en `analysis_scripts/`; recomendado branch dedicado antes de commit — esta investigación NO toca Kraken).

> **Este documento se congela ANTES de mirar datos.** Cualquier cambio posterior al criterio de éxito, controles, métricas o universo invalida el pre-registro. Los resultados se reportan contra ESTE documento, no contra una versión revisada a posteriori.

---

## 0. Principio rector y línea roja

Nueva dirección post-veredicto Nivel 3 (re-selección sobre el pasado MUERTA — 3 líneas convergentes: Edge Campaign, capacidad ρ≈0.047, D3 NO CONFIRMADO). En vez de re-seleccionar, **aislar componentes que el sistema YA tiene y medir cuáles tienen edge POR SÍ SOLOS**, con parámetros fijados POR LÓGICA (no optimizados), validación out-of-sample intocada, y control contra random walk.

**LÍNEA ROJA (corregida por Ricardo 2026-06-26):** la línea roja NO es "una media vs varias" — es **"parámetros lógicos vs optimizados"**. Se pueden probar VARIAS medias y seguir siendo limpio, mientras cada una use su config ESTÁNDAR (no optimizada al activo). Medir un componente con parámetros lógicos fijos = diagnóstico válido; OPTIMIZAR sus parámetros = el espejismo (specialist_score era un componente y dio ρ+0.05 al optimizarse).

**El edge se LEE del panel LÓGICO, NUNCA de las optimizadas.** Las optimizadas son solo contraste de sobreajuste.

---

## 1. Hallazgos primary-source que fundan el experimento (§12 L38)

**3 supuestos del brief original REFUTADOS** al recorrer el código:
1. **No existe ADX** en el código. Los filtros TF son Heikin-Ashi de tendencia (TF1-3) y precio-vs-MA (TF4-5).
2. **No existe "10/55" literal.** Periodos optimizados por símbolo (fast 8-24, slow 30-75, trend=slow×4) y tipo de media también optimizado. "10/55" es una PROPUESTA de set lógico.
3. **"Momentum" no es filtro TF** — solo es 1 de los 8 indicadores de divergencia (MOM-10).

**Hallazgo estructural cardinal — DOS capas de "medias que definen zonas", no una:**

| Capa | Medias de la zona | ¿Optimizadas? | Regla zona | Kernel |
|---|---|---|---|---|
| **TF (tendencial)** | `fast/slow` triple, tipo+periodo **por símbolo** | **SÍ** ← blanco a medir lógico | `z_bull = fast > slow` | `lab_historico_numba_v8_3.py` (26-bit config) |
| **MR (reversión)** | **Tenkan-9 (1h) vs Heikin-Ashi-Diario-HLC3**, **fijas en código** | **NO** (ya fijas-lógicas) | `z_bull = fast < slow` (invertido) | `mean_reversion_kernel.py` (17-bit config) |

**Aislamiento verificado primary-source:** `config_id = 0` (los 26 bits apagados) ES las medias aisladas:
- Entrada (`lab_historico_numba_v8_3.py:1772-1782`): `div_entry_mode=0` + `entry_tf_count=0` → `if z_bull: long_cond = True` (sin TF, sin divergencias).
- Salida (`:1588-1594`): flip de zona hardwired + SL 3% / emergencia 5% + comisión 0.10% round-trip + cooldown 1 barra.
- Sin order blocks (lab_lite_zonas NO está en el path productivo), sin momentum, sin divergencias, sin filtros, sin cancels, sin trailing. **No requiere editar kernel.**

**Infraestructura reusada (no se construye):**
- **E2 (as-of)** = `regime_walk_forward.py`: split train/forward por episodio de régimen + toxic-tail anti-lookahead; corre el kernel y emite `pf_tr`/`pf_fwd` por config y clúster. Se reusa la MAQUINARIA (precalc + split + kernel), evaluando SOLO `config_id=0` — NO la selección de specialist (eso es la optimización).
- **E1 (random walk)** = `audit_forense_gap_20260612/placebo_gen.py`: pre-registrado, SEED 20260613, 6 series (PLBGB1-3 GBM σ-real drift-0 + PLBSH1-3 block-shuffle 168h). Su docstring: el block-shuffle "DESTRUYE la estructura multi-semana que el MA-cross (~75-340 barras) necesita". Se escriben como `data_cache/*.parquet` → el mismo E2 las corre sin cambios.
- Kernel de 1 config = `lab.run_on_slice(configs=[0], ...)` (numba **CPU**; sin path CUDA para 1 config → **sin riesgo VRAM/TDR**, Caveats #17-19 no aplican).

---

## 2. El componente (B.1)

Estrategia long/short **solo de cruce de medias**: entra long en `fast > slow` (TF) ó `fast < slow` (MR), estando flat; sale por flip de zona o SL 3% (emergencia 5%); comisión 0.10% round-trip; cooldown 1 barra. Implementación: `config_id = 0` + un preset de medias. Cumple B.1 exactamente.

---

## 3. DECISIÓN 1 — Parámetros (panel lógico + contraste optimizado)

### 3.1 PRIMARIO (medición limpia del edge) — PANEL de tipos de media, periodos estándar fijos
- **Panel de tipos** (los estándar-definibles del set de Ricardo, soportados por el kernel): **SMA, EMA, KAMA, VIDYA** (mínimo exigido) + **FRAMA, TEMA, DEMA, T3, Tenkan, ALMA, McGinley, VWMA** (los que el kernel soporte con config estándar). *(panel exacto confirmado contra `lab.calc_ma` en §Implementación).*
- **Periodos fijos, IGUALES para todos los símbolos:** primario `fast=10 / slow=55`, histéresis 0. (El `trend` NO interviene en la zona aislada — fuera.)
- **Params estándar por tipo** (no optimizados): T3 vfactor=0.7; ALMA offset=0.85/sigma=6; resto p1=p2=0.
- **Decisión de diseño:** periodos UNIFORMES (10/55) a través de tipos en el primario → aísla la variable TIPO (¿importa la familia de media?) controlando el periodo. La sensibilidad al periodo la cubre el Control 3.
- **NO se busca qué tipo+periodo gana.** Eso sería el espejismo. Se mide el cruce-de-medias-como-concepto a través de la familia.

### 3.2 SECUNDARIO (diagnóstico de sobreajuste — NO la medida del edge)
- Correr TAMBIÉN las configuraciones **optimizadas por símbolo** que el sistema ya tiene (top-1 de `regime_wf/{SYM}_specialist_configs.json`: su preset + su `config_id`), por la MISMA maquinaria as-of.
- **Comparar** contra el panel lógico:
  - `lógico ≈ optimizado` → edge robusto real.
  - `optimizado ≫ lógico` → la **brecha ES el sobreajuste cuantificado** (specialist_score ρ+0.05 reencarnado, ahora en números). T3.3.
- Esta comparación detecta el **sobreajuste-AL-ACTIVO** que el random walk NO puede detectar (el random walk usa ruido, no los activos reales; solo la brecha lógico-vs-optimizado revela si el edge era el eco de la optimización).

### 3.3 Señal de causa: consistencia entre tipos
Si el cruce tiene edge real, debería aparecer (siquiera modesto) a través de VARIOS tipos de media, no solo en uno. **Consistencia entre tipos = señal de causa real** (análogo a la robustez al periodo). Se reporta.

---

## 4. DECISIÓN 2 — Universo: 45 símbolos (cartera completa)
Coste es minutos igual; 45 da más evidencia independiente. Lista = los 45 `data_cache/{SYM}_1h.parquet` productivos.

---

## 5. DECISIÓN 3 — Alcance: TF + MR en el MISMO pase
- **TF (tendencial):** blanco original — cruce optimizado→panel lógico. Capa optimizada → se mide lógica (primario) + contraste optimizado (secundario).
- **MR (reversión):** INCLUIR. La capa MR (Tenkan-9 / HA-diario) YA es fija-lógica por diseño (no optimizada) → es el test MÁS LIMPIO de los dos SIN esfuerzo extra (no hay que imponerle params lógicos, ya los tiene). Y es el lado donde vive la hipótesis causal real de Ricardo (**barrido de liquidez = reversión, no tendencia**). Medir la capa fundacional del lado que más importa, en su forma ya-limpia.
  - MR primario = `config_id=0` MR (Tenkan-9/HA-diario) tal cual, 45 símbolos.
  - MR no tiene "contraste optimizado" (sus medias no se optimizan) — su valor es ser el baseline limpio.
  - MR Control 3 (robustez al periodo): requiere exponer el periodo Tenkan como argumento a nivel de features (NO muta la lógica de zona). Si exige cambio de feature, se reporta en §Implementación; si no es trivial en pase 1, se documenta como pendiente, no se omite silenciosamente.

---

## 5bis. TRATAMIENTO DE CLUSTERS / REGÍMENES (ajuste Ricardo 2026-06-26)

**Principio:** distinguir **cluster-como-DESCRIPCIÓN** (válido) de **cluster-como-SELECTOR** (el riesgo) — misma distinción que medir-vs-optimizar. El régimen/cluster fue lo que D3 (Nivel 3) midió y NO confirmó → medir "edge por cluster" como criterio repetiría, en miniatura, la pregunta ya refutada. Desglosar por cluster multiplica combinaciones (3 clusters × tipos × periodos) → reintroduce grados de libertad. Por eso el cluster es **DIAGNÓSTICO, no criterio**.

1. **LECTURA PRIMARIA = GLOBAL**, sin condicionar al cluster. La pregunta fundamental ("¿el cruce de medias tiene edge como concepto, por sí solo?") se responde sobre TODOS los regímenes mezclados — concretamente **`pf_fwd` GLOBAL = agregado cross-cluster del forward holdout** (`Σ_k gp_fwd_k / Σ_k gl_fwd_k` sobre clusters válidos; sigue siendo as-of, solo no condiciona al régimen). Un edge real y robusto debería verse globalmente (aunque modesto). El criterio de éxito (§7) se evalúa sobre el GLOBAL. Esta es la lectura que decide si el componente es candidato.
2. **DESGLOSE POR CLUSTER = DIAGNÓSTICO SECUNDARIO, NO criterio de éxito.** Tras la lectura global, desglosar `pf_fwd` por cluster para ENTENDER la señal: ¿el edge global (si lo hay) se concentra en un régimen? ¿el cruce gana en tendencial y pierde en lateral (coherente causalmente — el cruce es señal tendencial)? **El cluster DESCRIBE dónde está la señal; NO la RESCATA si el global es breakeven.**
3. **PROHIBIDO (cluster como selector):** NO elegir parámetros distintos por cluster. NO concluir "hay edge" porque funcione en ALGÚN cluster. Eso es seleccionar-por-régimen = lo que D3 refutó + reintroduce grados de libertad.

**Valor del desglose para la fase siguiente:** si el cruce tiene edge en régimen tendencial pero no en lateral/reversión → indica que el lado de reversión (donde vive el barrido de liquidez) NO se captura con el cruce solo → necesita el componente de order blocks. El cluster-como-lente ayuda a decidir QUÉ componente enriquecer con QUÉ causa.

**Aplica igual a TF y MR** (MR usa los mismos clusters GMM). Métrica primaria = `pf_fwd` GLOBAL; desglose per-cluster = secundario, descriptivo.

**INVARIANTE:** cluster-como-descripción (¿dónde está la señal?) válido; cluster-como-selector (¿qué config/régimen elijo?) = el espejismo que D3 midió muerto. **El edge se declara sobre el global; el cluster solo lo caracteriza.**

---

## 6. LOS 4 CONTROLES (congelados antes de mirar datos)

1. **Edge OOS:** `pf_fwd` neto de costes (0.10% round-trip) sobre holdout forward intocado; **CI bootstrap por-símbolo que excluya 1.0** (breakeven). Benchmark de referencia: el sistema completo as-of dio **0.702 [0.44, 1.07]**.
2. **Random walk** (placebo_gen, SEED 20260613, 6 series GBM+block-shuffle): `config=0`+preset **debe caer a PF≈breakeven**. Si funciona sobre ruido → geometría, causa refutada por construcción. *(NOTA: el random walk detecta sobreajuste-DE-FORMA, NO sobreajuste-AL-ACTIVO — para eso está la comparación lógico-vs-optimizado de §3.2.)*
3. **Robustez al parámetro:** `{8/40, 10/55, 12/60}` × tipos de media (+ histéresis 0 vs 0.5×ATR). Señal real = estable en el vecindario; si solo brilla en un valor exacto = sobreajuste de un grado de libertad.
4. **As-of (E2, `regime_walk_forward`):** preset fijo, `config_id=0` a priori ⇒ sin leakage por construcción. Se reporta `pf_tr` vs `pf_fwd`.

---

## 7. CRITERIO DE ÉXITO (pre-registrado)

Un tipo de media (o el concepto a través de tipos) **tiene edge** si, **evaluado sobre el GLOBAL** (`pf_fwd` agregado cross-cluster, forward holdout — §5bis, NO sobre un cluster individual):
- `pf_fwd` GLOBAL neto con **CI bootstrap que excluye 1.0** sobre el panel **LÓGICO** (no las optimizadas), **Y**
- se **cae** sobre random walk (PF≈breakeven en placebo), **Y**
- es **robusto al parámetro** (estable en {8/40,10/55,12/60} × histéresis), **Y**
- es **consistente a través de tipos** de media.

- Componentes con edge → **candidatos a enriquecer con razonamiento de mercado** (barrido de liquidez en el lado MR).
- Componentes sin edge → **descartados**.
- **El edge se lee del panel LÓGICO. Las optimizadas son solo contraste; su pf_fwd NO se interpreta como edge.**

---

## 8. Métricas, ventanas, coste

- **Métricas:** PF (primaria) + CI bootstrap por-símbolo; PnL neto, nº trades, maxDD, win-rate. Todo neto de 0.10% round-trip.
- **Ventanas:** convención E2 (`--train-ratio 0.70`, forward = resto + toxic-tail). Se reporta `tr` y `fwd`.
- **Coste:** 1 config × 1 preset × ~25-50K barras = segundos por celda (numba CPU). Orden de magnitud: 45 sym × (~8 tipos × 3 periodos × 2 hyst) reales + 6 placebo × panel + 45 optimizadas ≈ miles de celdas × segundos = **~minutos a ~1-1.5h**, sin GPU. **Smoke obligatorio de 1 celda** antes del barrido (norma Frame 3 + factor seguridad 2-3×) para calibrar tiempo real y validar PF sano.

---

## 9. Tier 3 PAUSE Ricardo MANDATORY

- **T3.2** — resultados del Experimento #1: tabla de atribución (qué medias/capas tienen edge en el panel lógico, brecha vs optimizadas, caída en ruido, robustez, consistencia entre tipos) → decisión de qué componente enriquecer con causa.
- **T3.3** — si la brecha lógico-vs-optimizado es grande (optimizado≫lógico) → confirma sobreajuste-al-activo, hallazgo central a documentar.

---

## 10. Invariantes preservados

- ULTRATHINK + §12 L38. Medir-no-asumir aplicado al propio inventario (3 supuestos refutados + 2 capas descubiertas).
- Re-selección sobre el pasado MUERTA (3 líneas). E2 as-of + E1 random walk = controles reusables.
- Migración Kraken en PAUSA (demo 503, Ricardo monitorea manual). Bot Tokio STOPPED (red de seguridad).
- **brain / kernel-simulación INTACTOS** — se LEEN y EJECUTAN, NO se mutan. El runner es un script nuevo en `analysis_scripts/` que importa y reusa, sin tocar `live/*` ni la lógica del kernel.
- NO martingala. Frame 3 cerrado. Harness E2 as-of = gate permanente.

---

## 11. Plan de ejecución autorizado

`congelar este .md` (DONE) → `smoke 1 celda` (BTC, EMA 10/55, real; verificar pf sano + tiempo) → `Experimento #1` (TF panel-lógico + contraste-optimizado, MR fija-lógica, 45 símbolos, 4 controles) → `T3.2 tabla de atribución`. **El edge se lee del panel lógico.**
