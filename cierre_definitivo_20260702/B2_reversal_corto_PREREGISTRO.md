# B2 — REVERSAL CROSS-SECTIONAL CORTO — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Harness `xs_harness.run_xs` (validado bit-exacto). $0, sandbox aislado.

## Hipótesis
El turnover 83%/pata de CS-MOM insinúa que los rankings de momentum se deshacen en días → el ranking **INVERTIDO** (comprar perdedores recientes, vender ganadores recientes) a horizonte corto podría capturar la reversión de corto plazo (Jegadeesh 1990; en cripto convive reversal 1-3d con momentum 2-4 sem).

## Factor
Reversal = **−(retorno reciente)** sobre `lookback`. Mayor factor (mayor perdedor reciente) = LARGO. Retorno reciente = (C − C.shift(lookback))/C.shift(lookback), solo pasado.

## Parámetros lógicos a priori (CONGELADOS)
- `lookback` = **6 barras (3 días)** PRIMARIO único (robustez {2,10}=1d/5d SOLO si el base sobrevive — no se rescata un base muerto).
- Resto (rebal 10, quintiles 20/33, vol-target, costes 0.10%/lado+slip, funding bilateral, corto pesimista, warmup 56): idéntico a CS-MOM/B1.

## Métrica CARDINAL (a priori, sin pivote)
Sharpe NETO de la Curva C (neutral L/S reversal), full 2023-2024, con CI block-bootstrap. + Sortino/maxDD/turnover/betas(gate arreglado).

## Criterios de veredicto (CONGELADOS — "DIGNA" exige TODOS los 5, idénticos a B1)
1. Neutral (gate arreglado): |beta_EW|≤0.15 y |beta_BTC|≤0.15.
2. Sharpe_neto_full ≥ 1.00.
3. CI del Sharpe excluye 0.
4. maxDD_full > −25%.
5. Sharpe>0 en 2023 Y 2024.

## Riesgo honesto pre-registrado
Reversal comprando perdedores = comprar coins en caída (posible continuación bajista / delistings); costes altos por turnover alto (heredado); la pata corta de ganadores hereda el squeeze.

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa. Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## VEREDICTO B2 (2026-07-02) — **NO DIGNA**
- Sharpe_neto C full = **−0.121**, CI [−1.541, 1.277] → incluye 0. Neutral SÍ (beta_EW 0.055). maxDD −58.4%. No sobrevive (2023 −0.47 / 2024 +0.16).
- Turnover **2.903** (el más alto de todos) → los costes por rotación entierran cualquier reversión. A_long 0.93 / B_short −1.03.
- **VEREDICTO: NO DIGNA.** El reversal corto no captura edge neto; el turnover altísimo lo hace inviable a 0.10%/lado. Robustez {1d,5d} OMITIDA (base muerto).
