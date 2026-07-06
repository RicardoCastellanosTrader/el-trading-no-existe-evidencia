# E08 — B1: funding-carry cross-sectional

**Hipótesis:** cobrar el funding sistemáticamente (largo los símbolos con funding más negativo, corto los más positivos) es rentable market-neutral.
**Nombre popular:** "cobrar el funding" — carry.

## Pre-registro — Nivel C (Lista de Cierre, commit único)
- `cierre_definitivo_20260702/B1_funding_carry_PREREGISTRO.md` — mini-pre-registro congelado antes de resultados según protocolo de la Lista de Cierre, pero todo (B1-B8, C1-C3, resultados y cierre) entró en el commit único `65b99c81` (2026-07-03). Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B124.py` sobre el harness común `xs_harness.py` (cluster-bootstrap cross-símbolo, gate beta, placebo GBM).
- Datos: klines 12h + funding de data.binance.vision ([`REGENERAR.md`](../../datos/REGENERAR.md)).
- Resultados: `cierre_definitivo_20260702/results_B124.json`.

## Veredicto
**NO DIGNA.** Sharpe del factor neutral: **−0.053, CI [−1.282, +1.261]**. El carry es genuino (ortogonal a momentum, ρ=0.022) y la **pata larga sola da +1.141** — pero la corta es un squeeze permanente (**−1.026**) que anula el factor, y la pata larga sola ni bate el buy-and-hold EW (1.443): es beta de bull, no edge.
