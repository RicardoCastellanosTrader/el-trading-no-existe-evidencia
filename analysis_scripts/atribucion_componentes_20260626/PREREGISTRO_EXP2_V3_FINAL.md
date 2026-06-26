# PRE-REGISTRO CONGELADO — Exp#2 v3 FINAL: Order Block (criterio real de Ricardo, gatillo-anclado)

**Fecha:** 2026-06-26 · **Estado:** FROZEN (validado en el ejemplo exacto de Ricardo; barrido autorizado) · **Rama:** `atribucion-componentes`. SUPERSEDE v1 (ICT estrecho) y v2 (choque reciente).

> Congelado tras verificación primary-source en el ejemplo XRP de Ricardo. La línea roja vive en el DISEÑO: todos los parámetros y reglas se fijan por LÓGICA/CAUSA a priori. La regla de selección "más profundo" es **causal (Ruta 2)**, no ajuste a un ejemplo.

## 1. El componente (criterio real, validado)
- **GATILLO EN-ZONA** (reúsa MR, sin DOF): entra mientras `z_bull`/`z_bear` (forming) estando flat — replica `mean_reversion_kernel.py:542-583` (NO solo el flip). **Dirección = zona MR invertida** (`fast<slow=bull=LARGO`; verificado CONTEXTO 297/308 + kernel:574).
- **BLOQUE = nivel de reacción / swing pivot (±P)**, FRESCO (extremo no mitigado) + REENCUENTRO (≥90% del tiempo fuera de la banda ±5% = nivel dormido reencontrado), por el lado correcto (debajo en alcista), retroceso s/tope (cap 25000). **SELECCIÓN = el MÁS PROFUNDO dentro del 5%** (= pool de liquidez mayor hacia donde barre el institucional; CAUSAL, no el más cercano). Verificado: en la barra exacta de Ricardo (2026-06-25 21:00, flat) devuelve su bloque [1.0026–1.0480].
- **ENTRADA** = orden límite en el **borde LEJANO al 75%** (donde barre la mecha de liquidación), no el proximal.
- **STOP** = cierre por debajo del borde **inferior** (extremo lejano; mecha perfora sin cerrar = barrido/entrada, cierre perfora = ruptura/invalidación). **TP** = nuevo cruce (zona opuesta). **cancel_zona** anti-repintado (forming repinta mismo-día / resolved discrepa al cierre; `kernel:353-377`).

## 2. Verificación primary-source (completada)
- NO bug de dirección: 0/218 trades alcistas con bloque por encima de la entrada. ✓
- Stop = cierre bajo el borde inferior (no el superior). ✓
- Barra exacta de Ricardo (flat) → `_find_block` devuelve [1.0026–1.0480] (el más profundo de los candidatos por-debajo dentro del 5%). ✓
- **NO-LOOK-AHEAD PASS** (prefix-invariance bit-exacta, BTC full=trunc; cancel_zona usa forming[t]+resolved[entry], causal). ✓

## 3. Parámetros lógicos congelados
P_pivote=10 · reencuentro out_thresh=0.90 · cercanía/banda=5% · entry_frac=0.75 (75% hacia borde lejano) · selección=**deepest** · stop=cierre-fuera-borde-inferior · TP=nuevo-cruce · comisión 0.10% · cooldown 1.

## 4. CAVEATS documentados (honestidad)
1. **Swing-pivot + "más profundo"** = objetivación CAUSAL del criterio de Ricardo (verificada en su ejemplo), no proxy ni sobreajuste (el principio vino de la tesis del barrido; el ejemplo lo confirmó).
2. **Preempción**: backtest secuencial de UNA posición; algunas entradas que el ojo vería quedan preempidas por operaciones abiertas (mecánica de backtest, no del criterio).
3. **Refinamientos NO incluidos** (medir por separado SI la base muestra señal): ángulo del cruce, cancel_ghost, cancel_tf.
4. **Exp#1 MR fue ingenuo** (config=0 sin cancel_zona); Exp#2 incluye cancel_zona.
5. **Bifurcación de interpretación** (pre-registrada): si edge (real>placebo robusto) → el concepto del barrido de liquidez carga señal; si no → (a) sin edge o (b) algo del criterio no capturado → refinamiento UNA condición a la vez.

## 5. Los 4 controles
1. Edge OOS: `pf_fwd` GLOBAL (cross-cluster, forward holdout) neto 0.10%, CI bootstrap por-símbolo.
2. **Random walk (JUEZ)**: 6 placebo (GBM/shuffle) — el ruido no tiene niveles de reacción con liquidez real → debe caer a breakeven. **El veredicto se lee de la BRECHA real-vs-placebo, no del PF absoluto** (el TP-por-cruce ya quitó el sesgo del 2R, PF 1.30→0.86 cumple).
3. Robustez: cercanía {3,5,7}%, entry_frac {75,90,100}%, P {10,30,50} (una-a-la-vez sobre el primario 5%/75%/P10).
4. As-of E2 (split GMM) + per-cluster diagnóstico (la reversión debería vivir en régimen reversión/lateral si la causa es real).

## 6. Criterio de éxito / VEREDICTO
Edge si: `pf_fwd` real con CI por-símbolo que excluya 1.0 **Y supere el floor de placebo** **Y** caiga sobre random walk **Y** robusto **Y** coherente per-cluster. **Se lee de la BRECHA real-vs-placebo.** Universo 45, métricas como Exp#1. Detector `ob_detector_v3.py` congelado.
