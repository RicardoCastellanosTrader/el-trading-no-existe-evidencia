# Tabla de respaldo de afirmaciones (puente entre las afirmaciones públicas y su evidencia)

**Fecha:** 2026-07-06. **Regla:** todo número público debe salir de esta tabla; cada número aquí sale de un artefacto PRIMARIO (JSON/CSV/log/código) de este repositorio, no de resúmenes. Lo no verificable va en ROJO y no se usa públicamente.
**Método:** recomputo directo con pandas/json sobre los artefactos citados (2026-07-06). Donde el número solo existe en un documento de registro (no recomputable), se marca **[documental]**.

Leyenda de estado: ✅ VERIFICADO (recomputado desde artefacto primario) · 🟡 PARCIAL/documental · 🔴 ROJO (no verificado — NO usar públicamente).

La transparencia de los números ROJOS es parte del método: esta tabla existe para que cualquier lector compruebe que ninguno de ellos aparece en el paper ni en ningún texto público.

---

## REDACCIÓN OFICIAL APROBADA (2026-07-06)

Estas son las formulaciones públicas canónicas. Todo texto público (paper, README, divulgación) usa EXCLUSIVAMENTE estas versiones; las cifras en ROJO quedan prohibidas.

1. **Configuraciones**: "espacio de **20.891.648 configuraciones** válidas, cruzado con los **28–32 presets** de cada símbolo; **138.000 configuraciones retenidas** con métricas walk-forward completas". Versión popular: "**decenas de millones de combinaciones**". ELIMINADO todo "~4M".
2. **Brecha in/out**: "optimizado **3,317** vs lógico **0,917** (bajo breakeven)". ELIMINADO todo "3.3 vs 1.16". (El 1,164 del mejor-lógico puede citarse solo como robustez adicional, nunca como la cifra principal.)
3. **Señales genuinas**: "**Ninguna señal genuina superó el listón fijado para ella**: magnitud inferior a costes (cascadas ≈+1pb; estacionalidad <10pb) o por debajo del benchmark trivial (Curva C 0,541 < EW 1,443; carry pata larga ≈ beta)." Sustituye a "todas < comisiones".
4. **Producción**: evidencia fuerte = **certificación W1500 (98,24-100% por símbolo)**; la auditoría 91% se declara siempre con su **N=11 (CI 62-98%)**; resultado real: **neto ≈ −1,7 USDT** — "no gané: los costes se llevaron el PnL".
5. **"Cuanto mejor lo haces, peor"**: los 2 ejemplos ROJOS quedan sustituidos por los 4 verificados: (a) ρ +0,598 → −0,054 (C1); (b) floor esperado 2,32 → replay (PF bruto, antes de comisión) 0,640; (c) noise floor 2,35 acuñado sobre placebos de ruido (mediana de 1 GBM y 2 block-shuffles de 168 h; el GBM solo, 2,14, ya supera el umbral pre-registrado de 1,7); (d) optimizado 3,32 vs lógico 0,92.
6. **Transferencia a otra fuente de datos**: siempre "≈ nula / indistinguible de cero" (CI [−0,31,+0,39] incluye 0 y también +0,30: test infrapotenciado, ni colapso ni transferencia demostrados), nunca "colapso demostrado"; y nunca "datos independientes", "fuera de muestra" ni "apartados de antemano": el −0,054 se recalculó sobre velas de futuros de Binance de la **misma ventana** cuyo tercio forward la selección ya había visto como velas al contado (forward solo "Parcial" intocado). "0/45" siempre con la coletilla "con intervalo de confianza" (en punto-estimado son 6/45).
7. **Pre-registros**: taxonomía A/B/C obligatoria (ver `prerregistros/README.md`): Nivel A verificable en git = E01/E03/E05; Nivel B documental; Nivel C commit único. Con declaración de asimetría: los veredictos son negativos → el sesgo auto-interesado iría en la dirección contraria. Anclaje público = OTS 2026-07-06 + DOI Zenodo al publicar.

---

## Afirmación 1 — "Probé todo lo que la industria vende y un retail puede comprobar"

**Estado: ✅ VERIFICADO** (enumeración 7+8+3 = 18 familias; tabla B y C recomputadas contra `cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md` §D1 y los results_*.json).

| # | Familia | Nombre popular (lo que "vende la industria") | Qué cubre | Veredicto | Artefacto primario |
|---|---------|----------------------------------------------|-----------|-----------|--------------------|
| L1 | Campaña Edge Real (E1 placebos + E2 as-of) | "Mi sistema optimizado gana" (backtesting + walk-forward) | ¿El sistema completo optimizado tiene edge neto en holdout intocado? | Sin edge neto demostrado; mejor estimación **PF ~0.70–0.85** (E2-full global 0.702 [0.439,1.066] N=163; noise floor E1 **2.35** ≈ floor producción 2.32) | `audit_forense_gap_20260612/VEREDICTO_FASE1.md` L13,32,47 |
| L2 | Estudio de Capacidad de Información | "Selecciona los mejores del pasado" (ranking por PF/score) | ¿Alguna dimensión del rendimiento pasado predice el forward? | Re-selección muerta para re-rankear dentro de la shortlist y no concluyente sobre capacidad en rango completo (A2); `specialist_score`→fwd ρ **+0.054** [−0.010,+0.117]; canónico ρ(fwd_JSON,fwd_bin) **+0.0465** | `audit_forense_gap_20260612/estudio_capacidad_fase1_results.json` (D6, repro_rho_0047) |
| L3 | Nivel 3 — D3 régimen | "Opera según el régimen de mercado" (market regimes) | ¿El régimen concurrente porta edge forward condicional? (MATCH/MISMATCH) | **NO CONFIRMADO**; en NETO PF_match pooled <1.0 | `audit_forense_gap_20260612/VEREDICTO_NIVEL3_D3.md` |
| L4 | Exp#1 — cruce de medias | "Cruces de medias móviles" (golden cross, 14 tipos de MA) | Componente cruce-de-zona aislado, params lógicos vs ruido | TF **0.917** vs panel placebo **0.928** (GBM 0.909, block-shuffles 0.969: contra el GBM solo, el real queda ligeramente encima, A3); MR **0.742** vs **0.853** (panel de 3 GBM + 3 block-shuffles); 0/14 tipos de MA con mediana>1 | `analysis_scripts/atribucion_componentes_20260626/results_*.csv` (recomputado) |
| L5 | Exp#2 — order block | "Order blocks / SMC / acción del precio" (ICT, S/R, pools de liquidez) | La hipótesis causal real del autor, objetivada y verificada en su ejemplo | Real **0.800** (pf_all de la serie completa; forward 0.739) vs floor placebo **0.989** (mediana de 3 GBM + 3 block-shuffles); CI_low>floor **0/45** | `results_obv3_real.csv`+`results_obv3_placebo.csv` (recomputado) |
| L6 | MFE — cascadas de liquidación | "Liquidation cascades / stop hunts" (microestructura seg-min) | Exhaustión post-cascada, 2 años tick BTC+ETH | Señal de supervivencia real pero neto ≈ −0.2%/trade; bruto ≈ +1pb | `mfe_sandbox/results/edge_summary.json` + FASE_A §A5 |
| L7 | CS-MOM | "Momentum" (Jegadeesh-Titman) | Momentum cross-sectional L/S market-neutral 12h | **NO DIGNO** — C neutral real Sharpe **0.541** < listón; A 1.163 < EW 1.443 | `cs_mom_sandbox/results/curves.json`+`benchmark.json` (recomputado) |
| B1 | Funding-carry | "Cobra el funding" (carry) | Carry cross-sectional neutral | NO DIGNA — Sharpe **−0.053** [−1.282,+1.261]; pata larga **+1.141**, corta **−1.026** | `cierre_definitivo_20260702/results_B124.json` (recomputado) |
| B2 | Reversal corto | "Compra el dip" (reversión 3d) | Reversión cross-sectional corto plazo | NO DIGNA — Sharpe **−0.121**, turnover 2.9 | `results_B124.json` |
| B3 | TSMOM diario | "Sigue la tendencia" (trend-following time-series) | Momentum time-series diario, 8 años incl. bear 2022 | NO DIGNA — Sharpe 0.749 < EW 0.779 | `results_B3.json` + FASE_D |
| B4 | Low-vol / BAB | "Betting against beta" (factor low-vol) | Factor low-vol cross-sectional | NO DIGNA — Sharpe **−0.633**, β **−0.494** (short-beta encubierto) | `results_B124.json` (recomputado) |
| B5 | Lead-lag BTC→alts | "BTC manda, las alts siguen" | Predictibilidad cruzada con FDR | CERRADO — único lag sig. 1-2h y NEGATIVO (−0.016) ≪ umbral | `results_B5.json` + FASE_D |
| B6 | Estacionalidad reloj | "Los mejores horarios para operar" | 37 buckets hora/día con FDR-BH | EFECTO REAL NO TRADEABLE — máx **5.97 pb** < 10 pb coste | `results_B6.json` (recomputado) |
| B7 | Open interest | "Sigue el posicionamiento" (OI) | Factor −ΔOI cross-sectional | NO DIGNA — Sharpe −0.42, no sobrevive 2024 | `results_B7.json` + FASE_D |
| B8 | MFE squeeze | "Short/long squeeze" (cascadas alcistas) | Retest MFE con control vol-matched | MUERE — net diff **CI excluye 0 en NEGATIVO** (BTC 3m: −0.00039 [−0.00062,−0.00017]) | `results_B8.json` (recomputado) |
| C1 | N2 potencia real | (retest de L2) | ¿−0.05 en la otra fuente es colapso o infra-potencia? | ρ within **+0.5984** [0.451,0.713] vs otra fuente (futuros, misma ventana) **−0.0545** [−0.305,+0.389] | `results_C1.json` (recomputado) + `C1_N2_potencia_VEREDICTO.md` L7; ventana: `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18 |
| C2 | Nivel3 patas omitidas | (retest de L3) | Placebo wrong-match + cartera condicional | p_perm **0.4735**; condicional **0.9828** vs agnóstica 0.9308, ambas <1 | `results_C2.json` (recomputado) |
| C3 | Exp#2 ablación | (retest de L5) | ¿La regla "más profundo = más liquidez" hace algo? | INERTE — deepest 0.8002 ≈ shallowest 0.8109 ≈ random 0.8099, todos < floor 0.9891 | `results_C3.json` (recomputado) |

**Matiz obligatorio (A7, meta-auditoría):** las 18 familias NO son 18 líneas independientes — son **~3 clusters efectivos** (L1-L5 comparten kernel/datos/placebos parcialmente; L6 y L7 ortogonales; B1-B8 cada una con instrumento propio). Decir "18 familias" es correcto como conteo de experimentos; decir "18 evidencias independientes" NO. Fuente: `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A7.

**Matiz de alcance (A8):** Binance top-45 — velas 1h del mercado al contado para la búsqueda principal y 11 de las 18 familias, perpetuos USDT-M para las otras 7, y ejecución real en perpetuos USDT-M de BingX — 1s/1h/12h/diario, 2018-2026, costes taker 0.10-0.20% RT — no atemporal, no otros venues/maker/institucional. *(La redacción de la v1.0.0, «perps Binance top-45», era inexacta: ver el reparto siguiente.)*

**Reparto comprobado en el código (v1.0.1):** la búsqueda principal (`lab_historico_numba_v8_3.py`, `data_cache.py`: `ccxt.binance(...)` con el mercado por defecto, es decir, contado; la caché empieza en 2017, antes de que existieran los perpetuos USDT-M) y las familias E01–E05, E10, E12, E13, E16, E17 y E18 usaron velas de 1h de Binance **al contado** (`data_cache/*.parquet`; runners `audit_forense_gap_20260612/asof_run.py`, `analysis_scripts/atribucion_componentes_20260626/exp*`, `cierre_definitivo_20260702/run_B3.py`, `run_B5.py`, `run_B6.py`, `run_C1_extend.py`, `run_C2.py`, `run_C3.py`); E06, E07, E08, E09, E11, E14 y E15 usaron **perpetuos USDT-M** de data.binance.vision (`mfe_sandbox/sandbox_mfe.py`, `cs_mom_sandbox/cs_mom.py` L31-32 `futures/um`, `cierre_definitivo_20260702/run_B124.py` y `run_B7.py` L12, `run_B8.py`); la ejecución real fue en **perpetuos USDT-M de BingX** (`trades_reales/README.md`). Razón registrada para el contado: los endpoints de futuros de Binance estaban geobloqueados (CONTEXTO §2.6, «Binance Futures geo-bloqueado → Spot»; §1.1, «Dual exchange»). El salto entre exchanges se midió en ~0,113 % en precios OHLC (CONTEXTO §0.6.1 y §1.1) y el funding, ausente en los backtests al contado, fue negligible en el registro real (~0,0023 %/operación, A9).

---

## Afirmación 2 — "Millones de combinaciones"

**Estado: 🟡 PARCIAL — "millones" se sostiene sobradamente; la cifra "~4M" es 🔴 ROJO (no localizada en ningún artefacto).**

Números verificados:

| Concepto | Número exacto | Artefacto primario |
|---|---|---|
| Espacio de configuraciones TF válidas (26 bits) | **20.891.648** (= 2.048 sin divergencias + 20.889.600 con divergencias, por enumeración) | `lab_historico_numba_v8_3.py:1153-1205` (`generate_valid_configs`) y `:1207-1217` (`decode_config`, bits 0-25); el log de reciclaje que lo imprime («📋 20,891,648 configs × 31 presets», `reciclaje_ONDOUSDT_grupo2_phase2_gpu_20260519_123048.log` L45) **no está en el archivo** [documental] |
| Evaluación GPU real de ese espacio | **~20,9M configs evaluadas por preset-pasada** (≈21-22 s a **~0,94-1,04M configs/s**, verificado en timing del log: 22.1s × 944.167/s ≈ 20,9M) | mismo log (líneas de timing por fase) |
| Por símbolo-pasada de reciclaje | 20.891.648 × 28–32 presets (los del símbolo); en la pasada de ONDO del log, 31 presets ≈ **6,48×10⁸** evaluaciones | `output/production/presets_*.csv` (28–32 por símbolo; ONDO, 31); log de ONDO [documental, no está en el archivo] |
| Acumulado cartera (45 símbolos, 1 pasada reciclaje) | ≈ **2,9×10¹⁰** evaluaciones config×preset (orden de magnitud; extrapola los 31 presets de ONDO a los 45 símbolos) | extrapolación aritmética de lo anterior; logs de reciclaje existen para los 20 símbolos reciclados + baseline v17 previo |
| Configuraciones retenidas con métricas walk-forward completas (producción final) | **138.000** filas (138 CSVs × 1.000: 45 sym × 3 clústeres, +ficheros extra) | `regime_wf/*_cluster_*_specialists.csv` (recomputado: 138 ficheros, 138.000 filas) |
| Población N1 del Estudio de Capacidad | **13.500** (45×3×100) | `audit_forense_gap_20260612/estudio_capacidad_fase1_results.json` (`n1_configs: 13500`) |

**Redacción oficial:** "un espacio de **20,9 millones de combinaciones válidas**, evaluado exhaustivamente en GPU (del orden de **decenas de miles de millones** de evaluaciones configuración×preset acumuladas)". La cifra "~4M" no aparece en ningún artefacto localizado: como cifra específica es indefendible; como orden de magnitud es una **infra**-estimación (dirección segura, pero se usa la verificada).

---

## Afirmación 3 — "La ventaja del gráfico desaparece fuera de muestra"

**Estado: ✅ VERIFICADO (ambas patas).**

**(a) ρ in-sample vs otra fuente de datos:**
- Within-data (27 sym / 243 configs, split cronológico 67/33, mismos bars): ρ = **+0.5984**, CI [0.451, 0.713] → `cierre_definitivo_20260702/results_C1.json` (recomputado).
- Otra fuente (binance_w3_data: velas 1h de futuros de Binance, 2023-04-24 → 2026-04-23, partidas 67/33; 9 sym / 60 configs): ρ = **−0.0545**, CI [−0.305, +0.389] → `estudio_capacidad_fase1_results.json` (`rho_pf_tr_fwd_b2 = −0.0545`) + `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md` L6-7. **No es un holdout apartado de antemano**: su tercio forward (para BTC, 2025-04-23 → 2026-04-23) cubre meses que la selección ya había visto como velas al contado (hasta 2026-03-24), y el pre-registro del Estudio lo marca como solo "Parcial" intocado (`audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18).
- **Matiz obligatorio:** el CI sobre la otra fuente incluye 0 Y +0.297 → lo defendible es "**indistinguible de cero / transferencia ≈ nula**", NO "colapso demostrado" (corrección A2 + veredicto C1: infra-potenciado a 9 símbolos). La formulación congelada del Escudo ("transferencia ≈ nula") es exactamente la correcta.

**(b) Brecha lógico-vs-optimizado (Exp#1):**
- Optimizado por activo: median opt_pf_fwd_global = **3.3167** → `results_optimized.csv` (recomputado, N=45).
- Lógico (params lógicos fijados en su pre-registro, nivel B; config primaria 10/55 H0): median pf_fwd = **0.9167** (N=630; sobre las 3.780 celdas todos-los-configs: 0.9266) → `results_tf_logical.csv` (recomputado).
- Lógico "mejor caso": median lógico EMA = 0.913; median lógico BEST (mejor config lógica por símbolo) = **1.164** → `ATRIBUCION_T3_2_RESULTADOS.md` §6.
- **Redacción oficial: "optimizado 3,317 vs lógico 0,917 (bajo breakeven)".** El 1,164 del mejor-lógico solo como robustez adicional. **Caveat del propio artefacto:** el 3,3 está CONTAMINADO por selección — no es edge, es la medida del sobreajuste. Ese es precisamente el punto.

---

## Afirmación 4 — "Las señales reales existen y todas quedaron por debajo del listón fijado para ellas"

**Estado: 🟡 PARCIAL — cierta para las señales por-trade; la formulación literal "todas < comisiones" tiene contraejemplos netos positivos tras costes (CS-MOM Curva C, la única market-neutral; y tres exposiciones largas por debajo de comprar y mantener: momentum solo largo, pata larga del carry y TSMOM diario) y queda sustituida por la redacción oficial §3 de arriba.**

Señales genuinas detectadas (todas verificadas):

| Señal | Magnitud verificada | Coste relevante | Artefacto |
|---|---|---|---|
| Gap de supervivencia post-cascada (MFE/B8) | surv_3m diff: BTC **+13.24pp** [11.1,15.5], ETH **+13.33pp** [11.5,15.2] (control vol-matched); neto **NEGATIVO** con CI excluyendo 0 (BTC −0.039pp [−0.062,−0.017]) | stack de costes por-trade lo mata; bruto ≈ **+1pb/trade** [documental FASE_A §A5, estimación de la meta-auditoría] | `results_B8.json` (recomputado); `FASE_A_correcciones_documentales.md` §A5 |
| Estacionalidad horaria | hour_22 **+5.97 pb** [2.82,9.28], hour_21 +5.37 [1.95,8.79], vie +2.93, sáb +2.16 (FDR-BH, 2017-2026) | < **10 pb** de coste RT → no tradeable; valor solo como timing de ejecución | `results_B6.json` (recomputado) |
| Carry de funding, pata larga | Sharpe **+1.141** (long-only del factor carry); genuino (ortogonal a momentum ρ=0.022) | no bate buy&hold EW **1.443** y el market-neutral se anula (C = −0.053) por el squeeze de la corta (−1.026) | `results_B124.json` + `benchmark.json` (recomputados) |
| CS-MOM Curva C (L/S neutral) | Sharpe **0.541**, ret 2a **+29.56%** NETO de costes de rotación, β vs EW **−0.043**, β vs BTC **−0.041**, maxDD −27.4%, 2023: 0.028 | **ES NETO-POSITIVA tras costes** — pero no cumple los criterios escritos en su código (nivel B: código, documento y resultados en un solo commit): `cs_mom.py` L332-335 exige |β| ≤ 0,15 (vs EW y vs BTC), Sharpe ≥ 1,00, maxDD mejor que −25 % y Sharpe 2024 > 0; falló Sharpe (0,541) y drawdown (−27,4 %). El límite de drawdown no es coherente en el registro: el documento (L118, L122 de sus bytes sellados) y un comentario del código (L334) dan un objetivo de −15 a −20 %, el test aplicó −25 %, y el −27,4 % falla los dos. *(v1.0.1: el 1,94 ≈ EW + 0,5 que citaba la v1.0.0 es el listón de la curva A, `cs_mom.py` L329, no el de la C.)* | `cs_mom_sandbox/results/curves.json` (recomputado); criterios: `cs_mom_sandbox/cs_mom.py` (bloque marcado CONGELADO; nivel B) |

**Barrido de contraejemplos (todos los veredictos B1-B8, C1-C3, L1-L7 revisados; cifras: `cs_mom_sandbox/results/curves.json` y `benchmark.json`, `cierre_definitivo_20260702/results_B124.json` y `results_B3.json`):** ninguna señal por-trade supera su coste. La única estrategia market-neutral neta positiva tras costes del proyecto es **CS-MOM Curva C** (y con sesgo de supervivencia a favor declarado como techo); el momentum solo largo (curva A, Sharpe 1,163), la pata larga del carry (+1,141) y el TSMOM diario (0,749) son positivos pero quedan por debajo de comprar y mantener (EW 1,443 los dos primeros; 0,779 el TSMOM diario en su periodo de ocho años). Por eso la redacción oficial es: *"Ninguna señal genuina superó el listón fijado para ella: magnitud inferior a costes o por debajo del benchmark trivial"* — la frase literal "TODAS menores que las comisiones" es falsable con `curves.json` en mano y NO se usa.

---

## Afirmación 5 — "Mi robot ejecutó con ~91% de fidelidad, con dinero real, y no gané"

**Estado: 🟡 PARCIAL — cada pieza es real pero las tres necesitan su matiz exacto (incorporado a la redacción oficial §4).**

**(a) El 91%:** auditoría v4 (kernel stateless vs BingX): **10/11 trades match = 91%**, CI ~[62%, 98%] → `audit_v5_2_report_20260426_1106_utf8.txt` L30 (+ CONTEXTO §2.5). *(v1.0.1: la ruta anterior, `…20260427_1844…`, no existe en el archivo; el script de esa auditoría v4, `audit_fidelity_v4.py`, tampoco está en el archivo público — solo existe copia local; en el archivo están `audit_fidelity_v5.py` y `audit_fidelity_v5_2.py`.)* **Matiz: N=11.** Evidencia posterior MÁS fuerte: certificación señal-a-señal brain↔kernel W1500 con match-rate **98.24-100% por símbolo** (p.ej. BTC 100% sobre 250 señales, ONDO 100% sobre 498; el mínimo es TRX, 98,24 % = 167/170) → `cert_fidelity_gate_W1500.json` (recomputado). *(v1.0.1, TRX:* el 97,06 % de TRX que aparece en el diario es de otra medición: la certificación de la Capa 1 del 2026-05-30, re-medida a ventana operacional 1500 y aceptada como drift benigno — CONTEXTO, entrada «[CERTIFICACIÓN CAPA 1] … 2026-05-30» [documental]; el 98,24 % es el del JSON del archivo, recalculado después, y es el que sostiene esta afirmación.)*; shadow-equivalence VPS-stack↔HEAD-stack: acciones **99.46%** sobre 6.470 ciclos [documental, CONTEXTO L1690]. La redacción oficial lidera con la certificación 98-100% y declara el 91% con su N.

**(b) Los 736 fills:** **736 filas** exactas, periodo **2026-04-13 → 2026-06-21**, 43 símbolos, 591 con size>0 → `logs_historicos_vps/trade_history/trade_history.csv` (recomputado).

**(c) "No gané":** PnL bruto registrado (mark-based, SIN comisión — A9): **+3.28 USDT** suma de pnl_usdt; notional total 4.962 USDT → comisión estimada 0.10% RT ≈ **−4.96 USDT** → neto estimado ≈ **−1.7 USDT**. **Es la cota más generosa (v1.0.1):** 145 de las 736 filas no registran tamaño (`size_usdt` = 0: las 48 primeras, 93 de abril y las líneas 533, 548, 712 y 736 del CSV), así que la comisión estimada no las cobra; y 7 de esas 145 (líneas 86, 97, 115, 533, 548, 712 y 736), cierres por stop reconstruidos o estimados después, registran su pérdida en `pnl_pct` (de −0,97 % a −6,16 %) pero 0 en `pnl_usdt`, de modo que esa pérdida no entra en la suma de +3.28 (recomputado 2026-10-13 sobre `trade_history.csv`). El −1,7 no se recalcula: se presenta como la cota más generosa, al lado del balance documental. Balance documental: capital ~296-298 USDT (CONTEXTO §13, múltiples entradas) → final **288.71 USDT** (CONTEXTO, cierre MiCA 2026-06-21) ≈ **−7 a −9 USDT (−2.4 a −3%)** en ~10 semanas. **Redacción oficial:** "tras 736 operaciones reales el precio me dio +3 USDT y las comisiones me quitaron ~5: exactamente lo que predice el veredicto — no gané: los costes se llevaron el PnL". **Funding realizado (`funding_paid`), filtro declarado (v1.0.1):** la suma depende del filtro: **+0,118 USDT sobre las 591 filas con `size_usdt > 0`** (filtro de la corrección A9, `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A9: es el que se usa, porque la comisión estimada y el ~0,0023 % por operación se calculan sobre esas mismas 591 filas con nominal), y **−0,0188 USDT sobre las 736 filas** (recomputado 2026-10-13 sobre el CSV). Ninguna de las dos cambia el neto. 🔴 El capital inicial exacto no tiene artefacto primario localizado (no hay registro de depósito en el repo); usar "~296 USDT" como documental.

---

## Afirmación 6 — "Mi propio sistema, el que me dio dinero, tampoco sobrevivió"

**Estado: ✅ VERIFICADO (con los dos matices de registro).**

Exp#2 v3 (criterio REAL del autor, verificado en su ejemplo XRP antes del barrido):
- Real: median pf_all (45 sym, config primaria near=0.05/frac=0.75/P=10) = **0.8002**; forward median 0.739.
- Placebo floor (mediana de 6 series de ruido) = **0.9891** (por serie: 0.90/1.66/1.04/1.27/0.94/0.89).
- Brecha = **−0.189** (el real queda DEBAJO del ruido); robusta cross-config (7/7 configs con brecha negativa, recomputado: −0.34 a −0.15).
- **0/45 símbolos con CI_low > floor** (y 0/45 con CI_low>1.0). **Matiz de redacción:** en punto-estimado 6/45 quedan sobre el floor; el "0/45" exacto es con el CI — no intercambiar.
- Ablación C3: deepest 0.8002 ≈ shallowest 0.8109 ≈ random 0.8099 → la regla causal es INERTE.
- Fuentes: `results_obv3_real.csv` + `results_obv3_placebo.csv` (recomputados), `ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md`, `results_C3.json` (recomputado).
- **Matiz A4 (meta-auditoría, obligatorio):** "negativa con **signo robusto** (P(brecha≥0)≤3.2%) pero **magnitud no ganada estadísticamente**" + la certificación no-look-ahead del smoke commiteado es irreproducible (aunque la inspección del código por la auditoría no halló fuga, y una fuga sería simétrica real/placebo). Fuente: `FASE_A_correcciones_documentales.md` §A4.
- **Matiz de identidad:** lo refutado es el criterio del autor **fielmente objetivado y verificado en su ejemplo exacto** — puede decirse "mi sistema, tal y como yo lo defino, objetivado" (la v1 estrecha ICT fue retractada y re-formalizada; es la v3 la que porta el veredicto).

---

## Afirmación 7 — "Cuanto mejor lo haces, peores salen los resultados"

**Estado: 🟡 PARCIAL — 4 ejemplos verificados fuertes (redacción oficial §5); los 2 ejemplos inicialmente propuestos están en ROJO y NO se usan.**

Ejemplos VERIFICADOS del patrón (optimización/selección más intensa → forward peor):

| Ejemplo | Números | Artefacto |
|---|---|---|
| La firma del sobreajuste (C1) | mismo ranking: ρ **+0.5984** sobre los mismos bars → **−0.0545** sobre otra fuente (futuros) de la misma ventana | `results_C1.json` + `estudio_capacidad_fase1_results.json` (recomputados) |
| El floor de producción vs lo realizado | floor esperado de los picks desplegados **2.32** (media ponderada por trades en vivo) → replay del mes real con emparejamiento correcto: PF **bruto** (antes de comisión) **0.640** [0.26, 1.31] (techo del CI ≪ floor) | `audit_forense_gap_20260612/INFORME_AUDITORIA_FORENSE_GAP.md` (tabla atribución; replay A/B) |
| La búsqueda acuña floors sobre RUIDO | noise floor E1 = **2.35** (mediana de 3 placebos: 1 GBM, 2.14, y 2 block-shuffles de 168 h, 3.03 y 2.35; 9/9 clústeres "notables", pf_fwd hasta 633 sobre ruido) ≈ floor producción 2.32 (comparación descriptiva: no hay contraste) | `audit_forense_gap_20260612/VEREDICTO_FASE1.md` L13,43; `e1_noise_floor/RESULTADO_E1.md` L7-13 |
| Optimizado deslumbra, lógico no | optimizado 3.32 vs lógico 0.92 (misma señal, mismos datos) — la diferencia ES el sobreajuste | `results_optimized.csv` + `results_tf_logical.csv` (recomputados) |
| N pequeño selecciona ruido amplificado | ONDO C0 pf_fwd=**7.945** con N=17 → observado en real PF **1.08** | 🟡 [documental, CONTEXTO §13.4/W3 2026-04-23; el JSON original fue superseded por reciclajes] |

- 🔴 **"~89% de gemas descartadas por la meseta"**: NO localizado en ningún artefacto ni doc del repo (grep exhaustivo por plateau/meseta/gemas+porcentajes). NO usar.
- 🔴 **"Corrección del TP: 1.30→0.86"**: NO localizado (grep por 1.30/0.86/take-profit en todo el repo). NO usar. (Nota: el par 2.32→0.86 "live bruto" del informe forense es OTRA cosa — no confundir.)

---

## Afirmación 8 — Cerradas POR ACCESO ("lo único que no probé es dejar de ser retail")

**Estado: ✅ VERIFICADO** — lista y razones exactas de `cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md` §D2:

| Puerta | Razón exacta registrada |
|---|---|
| Carry delta-neutral spot-perp | "edge casi seguro real (cash-and-carry, base de Ethena) pero **irrelevante a 289 USDT** (5-15%/año sobre 289 = 15-45 USDT/año menos fees de 2 patas). Test barato pero negocio inviable a esta escala." |
| VRP opciones Deribit | "el respaldo académico más fuerte, pero exige margen ≫ 289 USDT + acceso EU/MiCA dudoso + riesgo de cola de vender vol sin colchón = ruina. Edge probablemente real, INVIABLE para este operador." |
| Market-making / liquidez | "no falsable en backtest sin L2 completo (Tardis ~500 USD/mes o grabar meses); latencia doméstica = adverse selection; 289 USDT no alcanza tier maker. INVIABLE, cerrada por argumento." |
| Arbitraje cross-exchange | "spread comprimido a bps; con 289 USDT fragmentados = céntimos/evento vs fees de retirada; killer = capital fragmentado + latencia. INVIABLE." |
| On-chain flows | "literatura marginal post-2021 + riesgo de look-ahead del vendor (métricas revisadas retroactivamente) + suscripción 100-1200 USD. No digno." |

**Matiz:** el propio doc distingue "edge probablemente real" (carry delta-neutral, VRP) de "no digno" (on-chain) — puede decirse honestamente que las dos primeras son las puertas donde el edge probablemente existe y lo que falta es capital/acceso. Eso ES la evidencia de la tesis "dejar de ser retail".

---

## NÚMEROS EN ROJO (no usar públicamente)

1. **"~4M configuraciones"** — no existe en ningún artefacto; sustituido por 20.891.648 (espacio) × 28–32 presets por símbolo / ~2,9×10¹⁰ acumulado como orden de magnitud (afirmación 2).
2. **"~89% de gemas descartadas por la meseta"** — no localizado.
3. **"Corrección del TP: 1.30→0.86"** — no localizado.
4. **Capital inicial exacto** — solo documental (~296-298 USDT); no hay artefacto de depósito en el repo.
5. **"+6-8pp → ≈+1pb" (MFE corregido)** — es la estimación de la meta-auditoría registrada en FASE_A §A5; el recomputo del confound-vol no tiene artefacto propio en el repo (los JSONs de B8 con control vol-matched dan la versión verificable: gap +13pp / neto negativo CI excl. 0 — usar ESOS).
6. **"Shadow-equivalence 99.46% / 6470 ciclos"** — documental (CONTEXTO L1690); usable como registro, no como recomputo. La alternativa recomputable es `cert_fidelity_gate_W1500.json` (98.24-100%).

## DISCREPANCIAS (afirmación decía X, artefacto dice Y — todas resueltas en la redacción oficial)

1. **"~4M configuraciones"** → los artefactos sostienen 2,09×10⁷ (espacio) y ≥10¹⁰ (evaluaciones). La cifra 4M infra-vendía y era inverificable: cambiada.
2. **"TODAS las señales < comisiones"** → CS-MOM Curva C es neta-positiva tras costes (Sharpe 0.541, +29.6%/2a). Reformulada a "ninguna supera el listón fijado para ella".
3. **"0/45 baten el floor" (Exp#2)** → exacto solo con CI (CI_low>floor 0/45); en punto-estimado 6/45. Se especifica siempre "con intervalo de confianza".
4. **"ρ −0.05 independiente"** → la cifra es correcta, pero CI [−0.31,+0.39] incluye 0 y +0.30: se dice "≈ nula / indistinguible de cero", nunca "colapso demostrado"; y no es "independiente" en el tiempo: otra fuente (futuros), misma ventana (v1.0.3).
5. **"TF 0.917"** → es la config primaria 10/55 (N=630); sobre las 3.780 celdas es 0.927. Misma conclusión; se cita la definición.
6. **"91% de fidelidad"** → real pero N=11 y CI [62%,98%]; la evidencia fuerte es la certificación posterior 98-100% (W1500, N=125-498 por símbolo). Se citan ambas, liderando con la fuerte.
7. **"Perdí igual"** → la pérdida neta es pequeña (−1.7 USDT estimada / −7..−9 USDT en balance), no sustancial: la formulación oficial es "no gané: el precio me dio ~+3 USDT y los costes se los llevaron".
8. **"18 familias"** → correcto como conteo; como evidencia independiente son ~3 clusters + ejes ortogonales (A7). Declarado en portada.

---

## Correcciones v1.0.4 (2026-10-20)

Propagación que faltaba en la v1.0.3: dos líneas de esta tabla conservaban texto que la v1.0.3 ya había corregido (REDACCIÓN OFICIAL §3; criterio de H1). La REDACCIÓN OFICIAL no cambia. Cada fila guarda el texto anterior **literal** y su fuente.

| # | Texto anterior (literal) | Fuente de la corrección |
|---|---|---|
| A4e | Por eso la redacción oficial es: *"Ninguna señal genuina superó el listón honesto: magnitud inferior a costes o por debajo del benchmark trivial"* | REDACCIÓN OFICIAL §3 (R3, v1.0.3) |
| A6a | (aunque la inspección independiente no halló fuga, y una fuga sería simétrica real/placebo) | «independiente» sin respaldo [V], con el mismo criterio que H1: la inspección la hizo la propia meta-auditoría (`cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` L30) |

## Correcciones v1.0.3 (2026-10-20)

Primera versión en que cambia la REDACCIÓN OFICIAL de arriba (§1, §5 y §6): contenía tres de las afirmaciones corregidas. Regla del programa: el canon primero; nada se borra en silencio. Cada fila guarda el texto anterior **literal** y su fuente. Las cifras e intervalos no cambian; cambia lo que se dice de ellos (qué placebos, qué mide cada cifra, qué puede probar cada pre-registro). Detalle y commits en [`CHANGELOG.md`](CHANGELOG.md).

| # | Texto anterior (literal) | Fuente de la corrección |
|---|---|---|
| R1 | 1. **Configuraciones**: "espacio de **20.891.648 configuraciones** válidas × 31 presets; ~**6,5×10⁸ evaluaciones** por símbolo-pasada; **138.000 configuraciones retenidas** con métricas walk-forward completas". | `output/production/presets_*.csv` (48 archivos: 3×28, 4×29, 16×30, 13×31, 12×32); el «31» y el «~6,5×10⁸» salen de una pasada de ONDO cuyo log no está en el archivo (afirmación 2) |
| R5 | (b) floor esperado 2,32 → replay real 0,640; (c) noise floor 2,35 acuñado sobre GBM puro; | `audit_forense_gap_20260612/e1_noise_floor/RESULTADO_E1.md` L7-15; `INFORME_AUDITORIA_FORENSE_GAP.md` L44-48; `fase1_compare.py` L95 |
| R6 | 6. **Transferencia fuera de muestra**: siempre "≈ nula / indistinguible de cero" (CI [−0,31,+0,39] incluye 0), nunca "colapso demostrado". | `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md` L7-8, L16-23 |
| L2 | \| Re-selección muerta/mecánica; `specialist_score`→fwd ρ **+0.054** [−0.010,+0.117]; | `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A2 (L15) |
| L4 | \| TF **0.917** vs placebo **0.928**; MR **0.742** vs **0.853**; | `analysis_scripts/atribucion_componentes_20260626/ATRIBUCION_T3_2_RESULTADOS.md` L40-41, L54; `FASE_A…` §A3 |
| L5 | \| Real **0.800** vs floor placebo **0.989**; CI_low>floor **0/45** \| | `ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md` L6-7, L12 |
| A2a | \| Espacio de configuraciones TF válidas (26 bits) \| **20.891.648** \| `lab_historico_numba_v8_3.py:1207-1217` (`decode_config`, bits 0-25) + log reciclaje: "📋 20,891,648 configs × 31 presets" (`reciclaje_ONDOUSDT_grupo2_phase2_gpu_20260519_123048.log` L45) \| | `lab_historico_numba_v8_3.py` L1153-1205; `git ls-files` (el log no está) |
| A2b | \| Por símbolo-pasada de reciclaje \| 20.891.648 × 31 presets ≈ **6,48×10⁸** evaluaciones \| mismo log L45 \| | `output/production/presets_*.csv` |
| A2c | \| Acumulado cartera (45 símbolos, 1 pasada reciclaje) \| ≈ **2,9×10¹⁰** evaluaciones config×preset (orden de magnitud) \| extrapolación aritmética de lo anterior; | ídem |
| A3b | - Lógico (params fijos a priori, config primaria 10/55 H0): | `prerregistros/README.md` L43 |
| A4 | **ES NETO-POSITIVA tras costes** — pero no cumple sus criterios congelados: `cs_mom.py` L332-335 exige \|β\| ≤ 0,15 (vs EW y vs BTC), Sharpe ≥ 1,00, maxDD mejor que −25 % y Sharpe 2024 > 0; falló Sharpe (0,541) y drawdown (−27,4 %). | `prerregistros/README.md` L38, L45; `cs_mom_sandbox/cs_mom.py` L334; `CS_MOM_PREREGISTRO.md` L118, L122 |
| A7a | \| El floor de producción vs lo realizado \| floor esperado de los picks desplegados **2.32** → replay correcto del mes real: PF **0.640** [0.26, 1.31] (techo del CI ≪ floor) \| | `INFORME_AUDITORIA_FORENSE_GAP.md` L23, L44-48; `fase0_pf_live.py` L127-134; `fase1_compare.py` L95 |
| A7b | \| noise floor E1 = **2.35** (3 placebos GBM, 9/9 clústeres "notables", pf_fwd hasta 633 sobre nada) ≈ floor producción 2.32 \| `audit_forense_gap_20260612/VEREDICTO_FASE1.md` L13,43 \| | `RESULTADO_E1.md` L7-13 |
| ROJO1 | sustituido por 20.891.648 (espacio) / ~6,5×10⁸ por símbolo-pasada / ~2,9×10¹⁰ acumulado (afirmación 2). | ídem R1 |
| R3 | 3. **Señales genuinas**: "**Ninguna señal genuina superó el listón honesto**: | decisión del director, título del caso (DF-3b, 20-X-2026): «the bar set for it» |
| R6b | 6. **Transferencia fuera de muestra**: siempre "≈ nula / indistinguible de cero" (CI [−0,31,+0,39] incluye 0 y también +0,30: test infrapotenciado, ni colapso ni transferencia demostrados), nunca "colapso demostrado". | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18 |
| L7 | \| L7 \| CS-MOM \| "Momentum" (Jegadeesh-Titman, el de mayor respaldo académico) \| | superlativo sin fuente bibliográfica en el archivo (DF-3b) |
| C1 | \| ¿−0.05 independiente es colapso o infra-potencia? \| ρ within **+0.5984** [0.451,0.713] vs independiente **−0.0545** [−0.305,+0.389] \| `results_C1.json` (recomputado) + `C1_N2_potencia_VEREDICTO.md` \| | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18 |
| A3a | **(a) ρ in-sample vs independiente:** / - Independiente (binance_w3_data, 9 sym / 60 configs): ρ = **−0.0545**, CI [−0.305, +0.389] → `results_C1.json` + `estudio_capacidad_fase1_results.json` (`rho_pf_tr_fwd_b2 = −0.0545`). / - **Matiz obligatorio:** el CI independiente incluye 0 Y +0.297 | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18; `C1_N2_potencia_VEREDICTO.md` L6-7 |
| A4b | ETH **+13.33pp** [11.5,15.3] (control vol-matched) | `cierre_definitivo_20260702/results_B8.json` (ETHUSDT surv_3m CI = [0.1147, 0.1525] → [11,5; 15,2] pp) |
| A4t | ## Afirmación 4 — "Las señales reales existen y todas quedaron por debajo del listón honesto" | ídem R3 |
| A4c | \| `cs_mom_sandbox/results/curves.json` (recomputado); criterios: `cs_mom_sandbox/cs_mom.py` (bloque CONGELADO) \| | `prerregistros/README.md` L45 (nivel B) |
| A4d | **Barrido de contraejemplos (todos los veredictos B1-B8, C1-C3, L1-L7 revisados):** | fuentes que faltaban en la línea |
| A7c | \| mismo ranking: ρ **+0.5984** sobre los mismos bars → **−0.0545** en datos independientes \| | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18 |
| D2 | Reformulada a "ninguna supera el listón honesto". | ídem R3 |
| D4 | 4. **"ρ −0.05 independiente"** → correcto, pero CI [−0.31,+0.39] incluye 0 y +0.30: se dice "≈ nula / indistinguible de cero", nunca "colapso demostrado". | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18 |
| H1 | \| **39 agentes de IA en 2 pasadas independientes**, mandato de refutar; | «independientes» sin respaldo [V]: CONTEXTO solo registra «39 agentes ×2» |

## Correcciones v1.0.2 (2026-10-14)

Alineación con el manuscrito del caso enviado a PLOS ONE. **Ninguna cifra, intervalo ni veredicto cambia**; la REDACCIÓN OFICIAL de arriba sigue idéntica, carácter a carácter, a la de la v1.0.0. Detalle y commits en [`CHANGELOG.md`](CHANGELOG.md).

| # | Qué cambia | Dónde |
|---|---|---|
| 1a | «El único retorno neto positivo tras costes del proyecto es CS-MOM Curva C» pasa a «la única estrategia market-neutral neta positiva tras costes»; el momentum solo largo (1,163), la pata larga del carry (+1,141) y el TSMOM diario (0,749) son positivos pero por debajo de comprar y mantener. | Afirmación 4 (barrido de contraejemplos); `HOW_TO_AUDIT.md` y `COMO_AUDITAR_ESTO.md` §2.6 |
| 1b | Las guías de auditoría (§2.6) aplicaban el 1,94 a la curva C; ahora la juzgan por sus criterios congelados (`cs_mom.py` L332-335), como esta tabla (§8(b) de la v1.0.1). Los dos working papers v1.0.0 se conservan como documento fechado. | `HOW_TO_AUDIT.md`; `COMO_AUDITAR_ESTO.md` |
| 1c | La línea «Estado» de la afirmación 4 decía «UN contraejemplo (CS-MOM Curva C)»; ahora nombra los contraejemplos netos positivos tras costes (la curva C, única market-neutral, y las tres exposiciones largas por debajo de comprar y mantener). Los dos working papers v1.0.0 llevan una nota de una línea bajo su sello de versión que remite a esta tabla y al CHANGELOG; su texto y su sello no cambian. | Afirmación 4 («Estado»); `paper/working_paper_ES.md`; `paper/working_paper_EN.md` |

## Correcciones v1.0.1 (2026-10-13)

Erratas y desajustes de la v1.0.0 corregidos en esta versión. **Ninguna cifra, intervalo ni veredicto cambia**: entran matices, rutas corregidas, descripciones corregidas y hechos que faltaban. Cada corrección se aplicó con su artefacto primario delante; el texto de la REDACCIÓN OFICIAL de arriba es idéntico, carácter a carácter, al de la v1.0.0. La lista completa, con el commit de cada cambio, está en [`CHANGELOG.md`](CHANGELOG.md).

| # | Qué cambia | Dónde |
|---|---|---|
| 1 | La fila del 91 % citaba `audit_v5_2_report_20260427_1844_utf8.txt` L28-29, un informe que no existe en el archivo. La cifra (v4 BingX: N=11, 10 matches, 91 %, CI ~[62 %, 98 %]) está en `audit_v5_2_report_20260426_1106_utf8.txt` L30. Se declara además que el script de la auditoría v4, `audit_fidelity_v4.py`, no está en el archivo público. | Afirmación 5(a) |
| 2 | La suma de `funding_paid` da −0,0188 USDT sobre 736 filas y +0,118 USDT sobre las 591 con tamaño. La tabla declara que usa el filtro de las 591 (el de A9, el mismo de la comisión) y por qué. | Afirmación 5(c) |
| 3 | **No aplica.** La tabla no cita la alarma del 26-IV (51,1 % = 48/94 para todo el periodo posterior a la v2.3.11, `audit_v5_2_report_20260426_1106_utf8.txt` L31; 48,1 % con N=52 para el segmento desde la v2.4.5, L49): no se añade. | — |
| 4 | TRX tiene dos cifras de fidelidad: 97,06 % (certificación Capa 1 del 30-V, documental, CONTEXTO) y 98,24 % (`cert_fidelity_gate_W1500.json`, recalculado). La tabla dice de qué medición sale cada una y que la del JSON es la que sostiene el 98,24–100 %. | Afirmación 5(a) |
| 5 | **No aplica.** Ninguna fila cita el 7–9 % del forense A10 del 22-IV: no se añade. | — |
| 6 | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md` conserva la cabecera «BORRADOR v0, PENDIENTE FREEZE». Una nota bajo el título, y otra en la guía de E07, dicen que lo congelado es el código (`cs_mom.py`, «CONGELADO 2026-06-29») y que es un pre-registro de Nivel B. | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md`, `experimentos/E07_cs_momentum/README.md` |
| 7 | **No es del archivo** (es del libro): no se toca nada. | — |
| 8 | El neto estimado de −1,7 USDT no cobra comisión a 145 filas sin `size_usdt` y no suma la pérdida de 7 de ellas (registrada solo en `pnl_pct`). Se declara en 5(c) y en A9, y el −1,7 se presenta como la cota más generosa junto al balance documental (~296–298 → 288,71 USDT). La cifra no se recalcula ni se sustituye. | Afirmación 5(c); `auditoria_adversarial/README.md` (A9) |
| 9 | La guía de E17 decía «prereg embebido» en el veredicto C2; ese veredicto (L3) dice que su pre-registro es el del Nivel 3 original (`NIVEL3_CONFIRMACION_D3_DISENO_PREREGISTRO.md` L61–L62). La guía lo dice ahora igual. | `experimentos/E17_nivel3_patas/README.md` |
| 10 | Ni el registro de Zenodo ni el README enlazaban el repositorio de GitHub (la dirección solo estaba en `CITATION.cff`). El README lo enlaza ahora en las dos lenguas y dice que el historial `git` solo está allí. La relación en el registro de Zenodo se añade al publicar la v1.0.1. | `README.md` |
| §8(a) | El archivo decía «perps Binance top-45» para todo. Comprobado en cada runner: la búsqueda principal y 11 familias (E01–E05, E10, E12, E13, E16, E17, E18) usaron velas 1h de Binance al contado; 7 (E06, E07, E08, E09, E11, E14, E15), perpetuos USDT-M de data.binance.vision; la ejecución real, perpetuos USDT-M de BingX. La guía de E10 decía «datos diarios de data.binance.vision» y su runner (`run_B3.py`) lee `data_cache` 1h y agrega a diario: corregida. | Afirmación 1 (A8); `README.md` (formulación congelada y limitación 3, es/en); `datos/REGENERAR.md` §1 y §3; `experimentos/E10_tsmom_diario/README.md`; `CITATION.cff` (abstract) |
| §8(b) | El 1,94 (≈ EW + 0,5) es el listón de la curva A (long-only), `cs_mom.py` L329; la v1.0.0 lo aplicaba a la curva C. La curva C se juzga con sus criterios congelados (L332-335): |β| ≤ 0,15, Sharpe ≥ 1,00, maxDD > −25 %, Sharpe 2024 > 0; falló Sharpe y drawdown. El veredicto no cambia. En la guía de E07, «protocolo declarado en el propio doc» pasa a referirse al código. | Afirmación 4; `experimentos/E07_cs_momentum/README.md` |
| §8(c) | Entran en la tabla, con artefacto: los 39 auditores (dos pasadas), la diferencia de precios entre exchanges (0,113 %), el funding realizado (~0,0023 %/operación) y la Sharpe deflactada implementada pero no aplicada. | Esta sección, tabla «Hechos añadidos» |

**Hechos añadidos a la tabla en v1.0.1 (§8 del encuadre del paper del caso):**

| Hecho | Cifra | Artefacto | Estado |
|---|---|---|---|
| Auditores de la meta-auditoría adversarial | **39 agentes de IA en 2 pasadas**, mandato de refutar; 7/7 veredictos «correcto con matices» | `auditoria_adversarial/README.md` L3 (y su nota: los transcripts no se conservaron); CONTEXTO, entrada «[META-AUDITORÍA DE LOS 7 VEREDICTOS …] 2026-07-01/02» («39 agentes ×2»); `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` (las correcciones aplicadas) | 🟡 documental: auditoría interna documentada, no reproducible |
| Diferencia de precios entre exchanges (Binance, datos; BingX, ejecución) | **≈ 0,113 %** en valores OHLC absolutos | CONTEXTO §0.6.1 («Diferencia esperada cross-exchange: ~0.113%») y §1.1 («validado: 0.113% diff cross-exchange») | 🟡 documental |
| Funding realizado en las 736 operaciones reales | **≈ +0,0023 % del nominal por operación** (media +0,00020 USDT; suma +0,118 USDT sobre las 591 filas con tamaño, de 4.962 USDT de nominal) | `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A9; `cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md` (Fase A, A9); `trades_reales/README.md`; `logs_historicos_vps/trade_history/trade_history.csv` (columna `funding_paid`) | ✅ recomputable (recomputado 2026-10-13: +0,1181 USDT / 4.962 USDT = 0,0024 %) |
| Sharpe deflactada (López de Prado 2014) | Implementada y probada en seco, **no aplicada a los veredictos**: `_R1_DSR_METHOD = 'none'` por defecto (infraestructura inactiva); ensayo cross-3 (BTC, ONDO, SEI): 1/9 cambios de top-1 y 88,9 % de clústeres marcados | `regime_walk_forward.py` L1120 (`_R1_DSR_METHOD = 'none'`) y L1377; `analysis_scripts/dsr_dry_run_cross_3.py`; `tests/test_r1_dsr_rigurosa.py`; `ROADMAP_PRE_RECICLAJE.md`, «Sesión 2.5 Frame 2 — R1 DSR rigurosa» | ✅ código en el archivo; el ensayo es documental (ROADMAP) |
