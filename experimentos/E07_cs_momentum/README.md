# E07 — CS-MOM: momentum cross-sectional market-neutral

**Hipótesis:** el momentum relativo (Jegadeesh-Titman, la anomalía con MAYOR respaldo académico) es explotable market-neutral en perps cripto: largo el quintil más fuerte, corto el más débil.
**Nombre popular:** "momentum — compra los más fuertes, vende los más débiles".

## Pre-registro — Nivel B (documental, commit conjunto) — con protocolo de listón honesto
- `cs_mom_sandbox/CS_MOM_PREREGISTRO.md` (§10 = veredicto) — commit `3b57151f` (2026-06-29). **El benchmark EW (Sharpe 1.443) se computó y reportó ANTES de fijar el listón y antes de ver ninguna curva CS-MOM** (protocolo declarado en el propio doc). Listón pre-registrado: 1.94 (≈ EW + 0.5).

## Código y datos
- `cs_mom_sandbox/cs_mom.py` (universo point-in-time 35→45, stitch MATIC→POL / RNDR→RENDER, SHIB=1000SHIBUSDT; klines 12h + funding bilateral; corto pesimista; costes en rotación).
- Datos: NO incluidos (~9 MB zips); regenerables — [`REGENERAR.md`](../../datos/REGENERAR.md).

## Resultados
- `cs_mom_sandbox/results/benchmark.json` (EW, computado primero) + `curves.json` (curvas A/B/C).

## Veredicto
**NO DIGNO — y es la única línea del proyecto con retorno neto positivo real.**
- Curva A (Long-Only): Sharpe **1.163** — ni siquiera bate el comprar-y-mantener EW (**1.443**).
- Curva B (Short-Only): **−0.83** — veneno (funding bilateral + squeezes refutan "la basura colapsa = ganancia fácil").
- Curva C (L/S market-neutral): **neutralidad real lograda** (β vs EW −0.043, β vs BTC −0.041) y **neta-positiva tras costes**: Sharpe **0.541**, +29.56% en 2 años, maxDD −27.4% (vs −59% del benchmark) — pero **sub-listón** (0.541 < 1.0 de mínimo y ≪ 1.94 pre-registrado), con 2023 plano (0.028) y turnover 1.657/rebalanceo.
**Declaración obligatoria:** esta Curva C es el contraejemplo a cualquier frase tipo "todas las señales < costes" — la formulación oficial del proyecto es "ninguna señal genuina superó el listón honesto: magnitud inferior a costes o por debajo del benchmark trivial". El sesgo de supervivencia del universo juega A FAVOR de la estrategia y aun así no llega.
