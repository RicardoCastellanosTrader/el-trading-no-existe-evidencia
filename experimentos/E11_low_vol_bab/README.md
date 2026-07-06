# E11 — B4: low-volatility / betting-against-beta

**Hipótesis:** los activos de baja volatilidad/beta rinden más por unidad de riesgo (el factor BAB de Frazzini-Pedersen) también en perps cripto.
**Nombre popular:** "betting against beta / factor de baja volatilidad".

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B4_low_vol_bab_PREREGISTRO.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B124.py` + `xs_harness.py` (el **gate beta** del harness es protagonista aquí); datos 12h ([`REGENERAR.md`](../../datos/REGENERAR.md)); resultados: `results_B124.json`.

## Veredicto
**NO DIGNA.** Sharpe **−0.633** con **β = −0.494**: el "factor low-vol" era un short-beta encubierto — precisamente el tipo de espejismo que el gate beta del harness existe para revelar (la versión con el gate roto parecía funcionar; arreglar el gate lo desenmascaró).
