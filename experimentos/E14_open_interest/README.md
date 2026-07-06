# E14 — B7: open interest / positioning

**Hipótesis:** los cambios de open interest predicen retornos (factor −ΔOI cross-sectional: el des-apalancamiento anticipa rebote y viceversa).
**Nombre popular:** "sigue el posicionamiento / el OI manda".

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B7_open_interest_PREREGISTRO.md` — requirió dataset nuevo (~150 MB de métricas OI de data.binance.vision). Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B7.py` + `xs_harness.py`; datos OI ([`REGENERAR.md`](../../datos/REGENERAR.md)); resultados: `results_B7.json`.

## Veredicto
**NO DIGNA.** Sharpe **−0.42, CI [−1.85, +1.08]**; el residuo positivo de los primeros años no sobrevive 2024. El posicionamiento agregado no dio factor explotable en este universo/frecuencia.
