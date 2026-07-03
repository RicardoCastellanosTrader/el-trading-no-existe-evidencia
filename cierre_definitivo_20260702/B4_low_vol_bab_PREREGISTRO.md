# B4 — LOW-VOL / BETTING-AGAINST-BETA CROSS-SECTIONAL — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Harness `xs_harness.run_xs` (validado). $0, sandbox aislado.

## Hipótesis
Demanda de lotería + restricciones de apalancamiento → los activos de alta vol están sobrecomprados y rinden peor ajustado por riesgo (Frazzini-Pedersen BAB 2014; lottery effect cripto). LARGO baja-vol, CORTO alta-vol, market-neutral vol-targeted.

## Factor
BAB = **−(vol realizada)** sobre `lookback`. Mayor factor (menor vol) = LARGO. Vol realizada = std de retornos 12h sobre `lookback`, solo pasado.

## Parámetros lógicos a priori (CONGELADOS)
- `lookback_vol` = **28 barras (14 días)** PRIMARIO único.
- Resto (rebal 10, quintiles 20/33, vol-target, costes, funding bilateral, corto pesimista, warmup 56): idéntico a CS-MOM/B1.
- **Confound declarado a priori:** el harness ya usa inv-vol (price/ATR) para el SIZING; usar vol también como factor de RANKING solapa (los low-vol se seleccionan Y pesan más). Es inherente a BAB; se declara y no se corrige (pre-registrado).

## Métrica CARDINAL (a priori, sin pivote)
Sharpe NETO de la Curva C (neutral L/S BAB), full 2023-2024, con CI block-bootstrap. + Sortino/maxDD/turnover/betas(gate arreglado).

## Criterios de veredicto (CONGELADOS — 5 idénticos a B1)
1. Neutral: |beta_EW|≤0.15 y |beta_BTC|≤0.15. 2. Sharpe_neto_full≥1.00. 3. CI excluye 0. 4. maxDD>−25%. 5. Sharpe>0 en 2023 Y 2024.

## Riesgo honesto pre-registrado
La pata larga low-vol ≈ majors ≈ beta BTC con menos upside (difícil batir); la corta high-vol = short de memes en euforia = squeeze (aunque cobra funding típico alto → sinergia con B1); vol correlaciona con iliquidez donde el coste real supera el modelado.

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa. Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## VEREDICTO B4 (2026-07-02) — **NO DIGNA**
- Sharpe_neto C full = **−0.633**, CI [−1.924, 0.717] → incluye 0.
- **NO NEUTRAL: beta_EW −0.494, beta_BTC −0.528** (gate ARREGLADO). El gate roto lo habría ocultado (~0). BAB aquí = apuesta short-beta encubierta (largo low-vol/majors, corto high-vol/alts → pierde cuando el mercado sube).
- maxDD −75%. No sobrevive (2023 −0.89 / 2024 −0.43). A_long 1.18 / B_short −1.08.
- **VEREDICTO: NO DIGNA** (ni neutral ni rentable). Valida la utilidad del gate de beta arreglado. Robustez OMITIDA (base muerto).
