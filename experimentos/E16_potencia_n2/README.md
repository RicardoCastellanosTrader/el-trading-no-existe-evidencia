# E16 — C1: potencia real de N2 (retest de blindaje de E02)

**Pregunta:** el ρ ≈ −0.05 de [E02](../E02_estudio_capacidad/README.md) en datos independientes, ¿es colapso real de la transferencia o simple falta de potencia estadística (N=9 símbolos)?

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- Prereg embebido en `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_C1_extend.py`; extensión within-data a 27 símbolos / 243 configs con split cronológico 67/33; resultados: `results_C1.json` + `results_C1_extend.csv`. (El log de ejecución `c1_run.log` citado en el veredicto no está incluido en el repo.)

## Veredicto
**La firma del sobreajuste-a-los-bars, cuantificada.** El MISMO procedimiento de ranking da:
- **ρ = +0.5984, CI [0.451, 0.713]** cuando training y forward comparten los mismos bars (within-data, 27 sym) —
- **ρ = −0.0545, CI [−0.305, +0.389]** cuando el forward viene de datos verdaderamente independientes (9 sym).
El CI independiente incluye 0 (y también +0.30): la lectura correcta es "**transferencia indistinguible de cero**", no "colapso demostrado" — con la potencia disponible, lo que queda excluido es la transferencia FUERTE que el within-data aparenta. El gap +0.60 → −0.05 es la medida directa de cuánto de la "predictividad del histórico" era memoria de los propios datos.
