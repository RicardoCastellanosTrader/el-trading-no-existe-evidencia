# E13 — B6: estacionalidad de reloj (hora del día / día de la semana)

**Hipótesis:** existen horas/días sistemáticamente mejores para operar (efectos de reloj ligados a sesiones y al ciclo de funding).
**Nombre popular:** "las mejores horas para operar".

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B6_estacionalidad_PREREGISTRO.md` — con exigencia FDR pre-registrada (37 buckets → corrección obligatoria). Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_B6.py` + `xs_harness.py`; datos horarios 2017-2026 ([`REGENERAR.md`](../../datos/REGENERAR.md)); resultados: `results_B6.json`.

## Veredicto
**EFECTO REAL, NO TRADEABLE.** 4 buckets sobreviven FDR-BH: hour_22 UTC **+5.97 bps** [2.82, 9.28], hour_21 +5.37 [1.95, 8.79], viernes +2.93, sábado +2.16. Es de las pocas señales estadísticamente genuinas del proyecto — y su magnitud máxima (**5.97 bps**) es inferior al coste round-trip taker (~10 bps): no financia ni su propia ejecución. Valor residual honesto: timing de ejecución para órdenes que se iban a hacer de todos modos.
