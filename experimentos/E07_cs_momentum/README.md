# E07 — CS-MOM: momentum cross-sectional market-neutral

**Hipótesis:** el momentum relativo (Jegadeesh-Titman) es explotable market-neutral en perps cripto: largo el quintil más fuerte, corto el más débil.
**Nombre popular:** "momentum — compra los más fuertes, vende los más débiles".

## Pre-registro — Nivel B (documental, commit conjunto) — con protocolo benchmark-primero
- `cs_mom_sandbox/CS_MOM_PREREGISTRO.md` (§10 = veredicto) — commit `3b57151f` (2026-06-29). El `.md` conserva su cabecera de borrador («BORRADOR v0, PENDIENTE FREEZE») y sus bytes sellados (la nota de la v1.0.1 está aparte, en `cs_mom_sandbox/NOTA_v1.0.1_CS_MOM.md`); lo congelado es el código, `cs_mom_sandbox/cs_mom.py` («CONGELADO 2026-06-29»), que es donde viven el protocolo y los criterios de veredicto. **El protocolo escrito en el código manda computar el benchmark EW (Sharpe 1.443) antes de fijar el listón y de ver ninguna curva CS-MOM** (Nivel B: código, documento y resultados entraron en el mismo commit, así que el orden no es verificable en git; `cs_mom.py`, cabecera «PROTOCOLO: --benchmark PRIMERO … --curves DESPUÉS (con X congelado)»). Criterios escritos en `cs_mom.py` (bloque marcado CONGELADO, L329-335; Nivel B): curva A (long-only), Sharpe ≥ 1,94 (≈ EW + 0,5) y Sharpe 2024 > 0; curva C (L/S neutral), |β| ≤ 0,15 vs EW y vs BTC, Sharpe ≥ 1,00, maxDD mejor que −25 % y Sharpe 2024 > 0. *(v1.0.1: la v1.0.0 citaba el 1,94 como listón único; es el de la curva A.)*

## Código y datos
- `cs_mom_sandbox/cs_mom.py` (universo point-in-time 35→45, stitch MATIC→POL / RNDR→RENDER, SHIB=1000SHIBUSDT; klines 12h + funding bilateral; corto pesimista; costes en rotación).
- Datos: NO incluidos (~9 MB zips); regenerables — [`REGENERAR.md`](../../datos/REGENERAR.md).

## Resultados
- `cs_mom_sandbox/results/benchmark.json` (EW, computado primero) + `curves.json` (curvas A/B/C).

## Veredicto
**NO DIGNO — y es la única línea del proyecto con retorno neto positivo real.**
- Curva A (Long-Only): Sharpe **1.163** — ni siquiera bate el comprar-y-mantener EW (**1.443**).
- Curva B (Short-Only): **−0.83** — veneno (funding bilateral + squeezes refutan "la basura colapsa = ganancia fácil").
- Curva C (L/S market-neutral): **neutralidad real lograda** (β vs EW −0.043, β vs BTC −0.041) y **neta-positiva tras costes**: Sharpe **0.541**, +29.56% en 2 años, maxDD −27.4% (vs −59% del benchmark) — pero **no cumple los criterios escritos en su código** (Sharpe 0,541 < 1,00; maxDD −27,4 % peor que −25 %; el 1,94 es el listón de la curva A, no de la C). El límite de drawdown no es coherente en el registro: la sección de veredicto del documento (L118 y L122 de sus bytes sellados) y un comentario del código (`cs_mom.py` L334) dan un objetivo de −15 a −20 %, mientras que el test del código aplicó −25 %, el más permisivo; el resultado (−27,4 %) falla los dos, con 2023 plano (0.028) y turnover 1.657/rebalanceo.
**Declaración obligatoria:** esta Curva C es el contraejemplo a cualquier frase tipo "todas las señales < costes" — la formulación oficial del proyecto es "ninguna señal genuina superó el listón fijado para ella: magnitud inferior a costes o por debajo del benchmark trivial". El sesgo de supervivencia del universo juega A FAVOR de la estrategia y aun así no llega.
