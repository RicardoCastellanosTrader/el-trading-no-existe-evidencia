# E12 — B5: lead-lag BTC→alts

**Hipótesis:** los movimientos de BTC predicen los de las altcoins con retardo explotable.
**Nombre popular:** "BTC manda y las alts siguen".

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B5_lead_lag_PREREGISTRO.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B5.py` + `xs_harness.py` (barrido de lags con FDR); datos horarios ([`REGENERAR.md`](../../datos/REGENERAR.md)); resultados: `results_B5.json`.

## Veredicto
**CERRADO.** El único lag que sobrevive la corrección por múltiples comparaciones (1-2h) es **NEGATIVO (−0.016)** y de magnitud muy inferior al umbral pre-registrado (0.03): no hay retardo explotable, y el signo va en contra de la intuición popular.
