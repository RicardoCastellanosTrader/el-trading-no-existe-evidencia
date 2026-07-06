# E17 — C2: patas omitidas del Nivel 3 (retest de blindaje de E03)

**Pregunta:** el veredicto NO CONFIRMADO de [E03](../E03_regimen_d3/README.md), ¿resiste las dos patas que el run original no ejerció? (a) placebo de especificidad (¿un MATCH con régimen EQUIVOCADO rinde igual?); (b) la cartera condicional completa vs la agnóstica.

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- Prereg embebido en `cierre_definitivo_20260702/C2_nivel3_patas_omitidas_VEREDICTO.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_C2.py` sobre los trades sellados del run Nivel 3 (`audit_forense_gap_20260612/nivel3_resmoke_trades_*.json`); resultados: `results_C2.json`.

## Veredicto
**Refuerza el NO CONFIRMADO.** (a) El placebo wrong-match da **p_perm = 0.4735** — el "acierto" de régimen no tiene especificidad alguna (etiquetas equivocadas rinden estadísticamente igual). (b) La cartera condicional-a-régimen: PF **0.9828** vs agnóstica 0.9308 — la condicionalidad añade una mejora marginal pero **ambas quedan bajo 1.0 neto**: no hay nada deployable que rescatar.
