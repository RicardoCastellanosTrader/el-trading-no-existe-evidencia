# E03 — Nivel 3: confirmación de D3 (edge condicional a régimen)

**Hipótesis:** el régimen de mercado concurrente porta edge forward condicional — un specialist rinde mejor cuando opera en el régimen para el que fue seleccionado (MATCH) que fuera de él (MISMATCH).
**Nombre popular:** "opera según el régimen de mercado" — market regime filtering/clustering.

## Pre-registro — Nivel A (precedencia verificable en git)
- `audit_forense_gap_20260612/NIVEL3_CONFIRMACION_D3_DISENO_PREREGISTRO.md` — commit `fac92c01` (2026-06-16), **5 días antes** del veredicto (`68ecff2f`, 2026-06-21). Zonas CONFIRMADA/MATADA/NO CONCLUYENTE congeladas a priori. Ver [guía](../../prerregistros/README.md).

## Código y datos
- Extensión D3/D4 del harness as-of: `audit_forense_gap_20260612/asof_d3d4_extension.py` (reusa `asof_run.py`/`asof_eval.py`); drivers `nivel3_full_run_driver.sh`, `nivel3_autoresume.sh` (con telemetría VRAM 1s+fsync).
- Subset pre-registrado de 13 símbolos con frescura de anclas verificada: `nivel3_subset_freshness.py` + `.json`.
- Datos: velas 1h `data_cache/`.

## Resultados
- `audit_forense_gap_20260612/VEREDICTO_NIVEL3_D3.md` (run 13/13 celdas selladas, cero crashes, leakage 13/13 PASS).
- Trades del re-smoke por celda: `audit_forense_gap_20260612/nivel3_resmoke_trades_{SYM}_{ANCLA}*.json`.

## Veredicto
**D3 NO CONFIRMADO.** En neto, el Δ = PF_match − PF_mismatch agrupado es **+0.086**, indistinguible de un emparejamiento aleatorio (placebo wrong-match, p = 0.47), y la cartera régimen-condicional queda en **0.983 < 1** frente a 0.931 agnóstica (C2: `cierre_definitivo_20260702/C2_nivel3_patas_omitidas_VEREDICTO.md` L6-7, L11-12). *(v1.0.3: la versión anterior presentaba como veredicto que las 2 celdas de 3 regímenes «leanean negativo» — THETA Δ −0.535, OP Δ −0.094, en bruto —; la meta-auditoría (A6) retiró esa lectura como partición a posteriori, ver el matiz siguiente.)* La lectura L1 "confirmada" (solo celdas PASS) es un espejismo de baja varianza: p a nivel símbolo 0.011 pero **p a nivel trade 0.257** — no replica. El ε²=0.574 del Estudio (E02) era artefacto de relleno-independiente-por-clúster, no edge condicional forward.
**Matiz (A6):** la lectura degradada correcta es "**no contradice la convergencia**" (el Δ punto-estimado es positivo en 3/3 lecturas agregadas, con partición selectiva); la decisión "no construir el Frame 3 de regímenes" se sostiene porque la deployabilidad neta es < 1 en cualquier lectura.

## Reproducir
```
bash audit_forense_gap_20260612/nivel3_full_run_driver.sh   # requiere GPU; ~13 celdas
```
