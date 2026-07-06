# E15 — B8: MFE squeeze (retest de E06 con controles corregidos)

**Hipótesis:** retest del edge post-cascada de [E06](../E06_cascadas_liquidacion/README.md) corrigiendo las dos objeciones de la meta-auditoría: control **vol-matched** (el gap original estaba inflado por el confound de volatilidad) y **slippage matched** en el control (la comparación "peor que aleatorio" original no lo tenía).
**Nombre popular:** "cazar el short/long-squeeze".

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B8_mfe_squeeze_PREREGISTRO.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B8.py` + `xs_harness.py`; 2 años de datos tick agregados ([`REGENERAR.md`](../../datos/REGENERAR.md)); resultados: `results_B8.json` (+ `results_B8_smoke.json`).

## Veredicto
**MUERE — y ratifica E06 con el control correcto.** El gap de supervivencia post-cascada es real incluso vol-matched (BTC **+13.24 pp** [11.1, 15.5], ETH **+13.33 pp** [11.5, 15.3]) — pero el resultado NETO por operación es peor que el control equivalente: BTC 3m net diff **−0.00039 [−0.00062, −0.00017]** — **el CI excluye 0 por el lado negativo**. La señal microestructural existe; su explotación con costes retail destruye valor de forma estadísticamente concluyente.
