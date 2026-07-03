# FASE A — Correcciones documentales del registro (honestidad post-auditoría)

**Fecha:** 2026-07-02. **Coste:** ~0 (documental) + A9 análisis de datos reales (~minutos).
**Origen:** meta-auditoría multi-agente de los 7 veredictos (2026-07-01, `project_auditoria_veredictos_7_lineas_2026_07_01`).
**Naturaleza:** registro honesto. Ningún veredicto se voltea; se rebajan sub-claims sobre-afirmados y se corrigen 2 bugs de número. Producción intacta, VPS stopped, $0.

---

## A1 — Edge Real, ancla A2
- **Antes:** "A2 = EDGE AUSENTE (demuestra edge bajo breakeven)".
- **Ahora:** "A2 = NO-CONCLUYENTE lean-negativo". El único rótulo de evidencia-de-ausencia formal de la campaña es frágil: CI iid [0.264, 0.972] a ~0.04 de la frontera; bajo bootstrap por celdas (3 celdas, LINK N=5 outlier) [0.452, 2.392] cruza 1.0; regla de 3 zonas pre-registrada para el POOLED, no por ancla; multiplicidad k=2 sin corregir.
- **Invariante:** el GLOBAL E2-full ya era NO CONCLUYENTE y la conclusión titular ("sin edge neto demostrado; mejor estimación ~0.70-0.85") no depende de A2. El pilar E1 (floors 2+ = artefacto) es evidencia positiva activa y se mantiene sólido (GBM puro solo ≥ umbral congelado 1.7).

## A2 — Estudio de Capacidad
- **D6 (specialist_score):** "MUERTA sin ambigüedad" → **"MUERTA para re-rankear DENTRO de la shortlist; NO-CONCLUYENTE sobre capacidad en rango completo"** (restricción de rango u=0.13 atenúa un ρ real 0.2-0.4 hasta la banda observada 0.03-0.09; la premisa congelada "todos los sesgos juegan a favor" es cuantitativamente falsa para el score).
- **D4 (perfil de fracaso):** "moneda al aire" → **"UNTESTED"** (0.00% fracasos en N1 = inadmisible; AUC N2 0.43-0.57 sin CI ~±0.15). La hipótesis de Ricardo quedó sin test limpio, no refutada.
- **D5 (ci_width) — BUG NUMÉRICO:** ρ publicado **+0.2345 es ERRÓNEO**. 25/45 símbolos carecen de ci_width (7.500/13.500 NaN) y el `_rankdata` del harness rankea NaN silenciosamente. Valor verdadero sobre las 60 celdas finitas = **+0.7465**. Dirección inocua (refuerza "mecánica"), pero el número primario publicado estaba corrupto.
- **Eslabón cardinal N2 ("pf_tr +0.30 en-slice → −0.05 independiente"):** sin CI; recomputado por-símbolo el CI es [−0.31, +0.40] e INCLUYE +0.297 → es NO-CONCLUYENTE infra-potenciado, no "colapso confirmado a nivel config". (→ retest C1.)
- **Invariante:** la pata dura del veredicto (D1/D2/D5 = auto-correlación mecánica) es un hecho del código, verificada línea a línea; el veredicto de línea no descansa en los eslabones débiles.

## A3 — Exp#1 (medias / cruce de zona)
- **Antes:** "TF real 0.917 ≤ ruido 0.928".
- **Ahora:** **"TF indistinguible del ruido y sub-breakeven neto"**. El "≤" era artefacto de composición: los 43/504 placebo-cells con edge eran TODOS de una serie medio-viva (PLBSH3, block-shuffle 168h inválido a escala 10/55); contra el GBM puro (0.909) el real (0.917) queda ligeramente ENCIMA.
- **Nota adicional:** el brazo MR no era "zona pura" (trailing stop 0.5% hardwired sin bit de config, no descrito en el pre-registro) — la lectura relativa sobrevive porque el placebo comparte la mecánica, pero la atribución al COMPONENTE está confundida con el stop.
- **Invariante:** MR es activamente peor que el ruido (45/45 pf<1, bajo las 6 realizaciones del nulo); TF es empate-con-ruido sub-breakeven. "El cruce no porta edge neto explotable" se sostiene.

## A4 — Exp#2 (order block)
- **Antes:** "la 5ª línea, la MÁS FUERTE".
- **Ahora:** **"negativa con brecha de signo robusto (P(brecha≥0)≤3.2% incluso a N_eff=5) pero magnitud NO ganada estadísticamente"** (el floor es mediana de 6 series ruidosas 0.89-1.66 sin CI; el real solo queda bajo el MÍNIMO placebo en 1/7 configs).
- **Certificación no-look-ahead:** el smoke commiteado crashea contra el detector del MISMO commit (6 vs 9 args; el PASS corrió contra una versión intermedia no commiteada). La inspección independiente del código congelado NO halló fuga, y cualquier fuga sería simétrica real/placebo → defecto de reproducibilidad, no vector de flip. (→ retest C3.)
- **Invariante:** el detector congelado rinde bajo breakeven absoluto (0/45 ci_low>1, costes laxos a favor) — el criterio de ÉXITO congelado falló por su propia regla.

## A5 — MFE (liquidation exhaustion)
- **Antes:** "IGUAL O PEOR que aleatorio" + "gap supervivencia 23-27% vs 3-7% = señal microestructural real".
- **Ahora:**
  - "PEOR que aleatorio" → **"diferencial de slippage worst-3s NO matched en el control"** (el diferencial de coste de entrada ~0.035pp ≈ TODO el Δ de medias; a ejecución neutral el Δ ≈ 0).
  - "gap = señal real 23% vs 3%" → **"~+6-8pp sobre coin-flip tras corregir el confound de volatilidad del control (no matched por vol); bruto condicional a ejecución justa ≈ +1bp/trade, un orden de magnitud bajo cualquier coste"**. La línea queda MÁS muerta, no menos.
  - "funding NO estratifica: REFUTADO" → **"NO CONFIRMADO"** (N_hi=38/40 al borde del mínimo, CIs ±0.15-0.19; lo soportado es el fallo de monotonía pre-registrado + 1 celda activa en contra).
- **Desviación procesal anotada:** pivote de métrica post-hoc. La métrica cardinal CONGELADA (tasa de supervivencia) PASÓ (CI cluster-8h excluye 0, 6/6 horizontes); la que mató la línea (media neta) fue explícitamente EXCLUIDA en el freeze. Económicamente correcto (bruto ≈ +1bp no paga costes), procesalmente asimétrico — lección para B8 (fijar métrica cardinal a priori, sin pivote).
- **Invariante:** sin edge tradeable (potencia sobrada N=1391/1835; robusto cross-ejecución y cross-umbral). NO paper-trading.

## A6 — Nivel 3 D3 (régimen)
- **Antes (formal):** "D3 NO CONFIRMADO" — **se mantiene, correcto**.
- **Antes (interpretativo):** "ε²=0.574 era H_artefacto / es adverso, no ambiguo-por-N".
- **Ahora:** **"NO CONTRADICE la convergencia"** (no es 3ª pata adversa). El Δ MATCH−MISMATCH punto-estimado es POSITIVO en las 3 lecturas (+0.09 a +0.19); el "lean negativo en las celdas informativas" era partición selectiva post-hoc (6 celdas multi-régimen pooled Δ=+0.133 POSITIVO; solo el subset de 2 celdas 3-régimen, con OP del orden del ruido, da negativo); potencia ~20-25% sobre 1 ancla/1 ventana; se violó la regla congelada de la zona NO CONCLUYENTE ("más anclas ANTES de conclusión estructural"); veredicto computado en GROSS vs NETO congelado.
- **Invariante:** en NETO la deployabilidad falla igual (PF_match pooled 0.910/0.983/0.982 < 1.0) → **"no construir Frame 3" se sostiene**; el gate "divergentes=0" era teorema del código (rama FAIL muerta), no medición. (→ retest C2 para calibrar potencia del instrumento.)

## A7 — Convergencia
- **Antes:** "7 líneas independientes convergen en negativo".
- **Ahora:** **"~3 clusters efectivos"**: {L1-L3 encadenadas: mismos JSONs, kernel regime_walk_forward+GMM, fee 0.10pp, velas 1h, holdout 2025-26, con circularidad — Nivel 3 rechazó su expansión pre-registrada citando a L1-L2} + {L4-L5 comparten placebos seed 20260613 y kernel con L1} + {L6 ortogonal} + {L7 ortogonal}. La dirección converge igualmente porque L6 (aggTrades 1s, supervivencia) y L7 (12h, Sharpe, benchmark pre-fijado), con instrumentos propios, también dieron negativo/no-digno.

## A8 — Alcance del cierre
- **Reformulado:** el cierre vale para **"esta clase de estrategias (familia SmartDiv + los ejes medidos), en perps Binance top-45, a 1h/12h/1s, en 2023-2026, a costes taker"** — NO es un negativo atemporal (ningún bear testeado; 2022 excluido en CS-MOM contra su pre-registro).
- **Laguna declarada:** no se separó completamente "edge bruto nulo" vs "edge bruto < costes" (Exp#1 TF sin lectura pre-comisión; A1 bruto E2-full = 0.998 ≈ moneda al aire exacta).

## A9 — Fee flat 0.10% RT contrastado con 736 fills reales (BingX, `logs_historicos_vps/`)
**Hecho empírico (medido, no asumido):**
- El trade_history registra PnL BRUTO de precio: `pnl_pct` == retorno de precio side-adjusted **exacto** (corr 1.0, max |diff| = 0.0000 sobre 591 trades con size válido).
- `pnl_usdt` es mark-based bruto de BingX: residual `pnl_usdt − size·pnl_pct` = **+0.0247% del notional de media** (+0.0228% mediana), POSITIVO → es drift mark-vs-fill, **NO comisión** (una comisión sería negativa). Confirma la nota del auditor sobre `unrealizedPnl`.
- **La comisión y el slippage NO están registrados** en los fills ni en engine.log (grep: 0 líneas de commission/slippage/intended-price; los 45 gz sin registro de fee).
- **Funding realizado** (`funding_paid`, columna real): media +0.00020 USDT/trade, mediana +0.00040, suma **+0.118 USDT** sobre 585/591 trades no-cero → **~0.0023% del notional por trade = NEGLIGIBLE** (y neto ligeramente a favor).

**Conclusión A9:** el 0.10% RT modelado = taker nominal de BingX (0.05%/lado) — un supuesto **fiel a conservador**, no inflado. Lo que el 0.10% NO captura: (i) slippage — embebido en los fills reales pero no separable sin el precio-intención (no logueado); (ii) funding — medido aquí como **negligible** (~0.0023%/trade), lo que **valida empíricamente que ignorar funding en las líneas 1-5 fue inmaterial**. Ningún componente de coste recuperable es lo bastante grande para voltear un veredicto. La comisión efectiva no es recuperable de estos fills (mark-based), así que el 0.10% no puede afinarse hacia abajo/arriba empíricamente — pero equivale al taker publicado, luego es un floor honesto.

**Caveat residual permanente:** con fills mark-based no se puede medir la comisión realizada ni el slippage; para ello haría falta loguear precio-intención vs fill (no existe en el histórico). El supuesto de coste queda **contrastado en lo recuperable (funding negligible, PnL bruto exacto) y declarado fiel-a-conservador en la comisión (= taker nominal)**.

---

**Estado FASE A: COMPLETA.** Aplicado a memoria persistente + este documento de registro. Siguiente: FASE B (B1 funding-carry) con el gate de beta ARREGLADO y re-verificado con serie sintética.
