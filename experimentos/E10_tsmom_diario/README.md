# E10 — B3: momentum time-series (TSMOM) diario

**Hipótesis:** seguir la tendencia propia de cada activo (posición según el signo del retorno de las últimas 8 semanas) bate al mercado — el trend-following clásico.
**Nombre popular:** "sigue la tendencia / trend following".

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B3_tsmom_diario_PREREGISTRO.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B3.py` + `xs_harness.py`; datos diarios de data.binance.vision ([`REGENERAR.md`](../../datos/REGENERAR.md)); resultados: `results_B3.json`.

## Veredicto
**NO DIGNA.** Sharpe **0.749 < EW 0.779** sobre 8 años que INCLUYEN el bear de 2022 (el escenario donde TSMOM debería brillar), con maxDD −85%. Seguir la tendencia rindió menos que mantener el índice equiponderado.
