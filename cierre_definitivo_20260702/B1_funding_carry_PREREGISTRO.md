# B1 — FUNDING-CARRY CROSS-SECTIONAL — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de mirar resultados. Sandbox aislado, producción intacta, $0, VPS stopped.
**Harness:** `xs_harness.run_xs` (valida bit-exacto CS-MOM A/B/C=1.163/−0.832/0.541; gate de beta ARREGLADO y verificado con serie sintética: recupera beta_true; el roto colapsa a ~0).

## Hipótesis
El funding como **FUENTE de retorno** (nunca probado — solo fue filtro refutado v2.6 y covariable en MFE). El funding es un pago observable de apalancados, no una predicción de precio. Cartera cross-sectional market-neutral que **cosecha el carry**: LARGO los que COBRAN funding estando largo (funding negativo), CORTO los que COBRAN funding estando corto (funding positivo alto).

## Dirección (verificada contra la contabilidad del harness)
- Funding>0 → largos pagan, cortos cobran → **CORTO el quintil de funding más ALTO** (short_ret += sw·fund).
- Funding<0 → largos cobran → **LARGO el quintil de funding más BAJO/negativo** (long_ret −= lw·fund, con fund<0 suma).
- Factor para run_xs (mayor = largo) = **−(funding trailing)**.

## Parámetros lógicos a priori (CONGELADOS, no tuneados)
- `lookback_funding` = **6 barras (3 días)** — el funding es persistente a escala de días; media trailing solo con pasado (sin look-ahead). PRIMARIO único.
- `rebal_bars` = 10 (5 días) — idéntico a CS-MOM.
- Quintiles: enter 20% / exit 33% (histéresis simétrica) — idéntico a CS-MOM.
- Vol-target ATR-inverse, costes 0.10%/lado taker + slippage por iliquidez, funding bilateral, corto pesimista — todo idéntico a CS-MOM.
- `warmup` = 56 barras (paridad con CS-MOM; conservador).

## Métrica CARDINAL (fijada a priori, SIN pivote)
**Sharpe NETO de la Curva C (neutral L/S carry), full 2023-2024**, con su **CI por block-bootstrap** (bloques de 10 barras).
Reporto además Sortino, maxDD, dur peor DD, turnover, y las betas con el gate ARREGLADO.

## Criterios de veredicto (CONGELADOS — "DIGNA" exige TODOS)
1. **Neutral (gate arreglado):** |beta_C_vs_EW| ≤ 0.15 **y** |beta_C_vs_BTC| ≤ 0.15.
2. **Rentabilidad:** Sharpe_neto_full ≥ 1.00.
3. **CI del Sharpe excluye 0** (límite inferior del CI block-bootstrap > 0). [además anoto si excluye 1.0]
4. **Protección:** maxDD_full > −25% (objetivo −15/−20).
5. **Supervivencia:** Sharpe > 0 en 2023 **Y** 2024.
- Cualquiera que falle → **NO DIGNA**.

## Chequeo de colapso en CS-MOM disfrazado (CONGELADO, diagnóstico)
Spearman medio por rebalanceo entre el ranking de funding y el ranking de momentum (N=28). Si |ρ| medio > 0.5 → anotar "carry ≈ momentum disfrazado". Además reporto correlación de la serie de retorno C-carry vs C-momentum.

## Riesgo honesto pre-registrado
- La pata corta = shortear el funding más alto = típicamente coins crowded-long/pumpeadas → **exposición a squeeze** (heredada del corto pesimista bar-HIGH). 
- El carry post-2024 puede estar comprimido por desks de basis-trade/Ethena → el edge 2020-22 de la literatura probablemente ya no existe.
- Puede colapsar en un CS-MOM disfrazado.

## Expectativa CALIBRADA (CONGELADA)
Incluso un positivo es **modesto y limitado por capital** (auditoría: irrelevante a 289 USDT). El propósito es COMPLETAR EL MAPA, no resucitar el objetivo. Un positivo modesto se documenta como hallazgo limitado-por-capital; un negativo suma al mapa. Ningún resultado reabre la búsqueda.

## Alcance (heredado, honesto)
Perps Binance top-45 point-in-time (survivorship = techo optimista), 12h, 2023-2024 (sin bear 2022). No es negativo atemporal.

---
*VEREDICTO abajo, añadido tras el run (sección separada, sin tocar lo anterior).*

---
## VEREDICTO B1 (2026-07-02) — **NO DIGNA**
- Sharpe_neto C (carry neutral) full = **−0.053**, CI block-bootstrap [−1.282, 1.261] → **incluye 0** (criterios 2,3 FALLAN).
- Neutral: **SÍ** (beta_EW −0.067, beta_BTC −0.070, gate arreglado) — la carry ES market-neutral.
- maxDD −65.5% → protección FALLA. No sobrevive (2023 −0.20 / 2024 +0.09).
- **Descomposición reveladora:** A (largo cobra-funding en funding-negativo) Sharpe **+1.141**; B (corto cobra-funding en funding-alto) **−1.026** → se cancelan. La pata corta = shortear coins de funding alto = crowded-long/pumpeadas → **squeeze** (mismo veneno que CS-MOM Curva B, riesgo pre-registrado confirmado).
- **NO es CS-MOM disfrazado:** spearman medio ranking funding-vs-momentum = **0.022** (ortogonal); corr serie C-carry vs C-momentum −0.116. La carry es un factor genuinamente distinto — y aun así sin edge neto market-neutral en 2023-24.
- **VEREDICTO: NO DIGNA.** El carry existe en la pata larga pero el market-neutral lo anula vía el squeeze de la pata corta. Robustez OMITIDA (base muerto).
