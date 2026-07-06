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
**D3 NO CONFIRMADO.** Las 2 únicas celdas que ejercen de verdad el contraste (3 regímenes con trades) leanean **negativo**: THETA Δ = PF_match − PF_mismatch = **−0.535** (el specialist rinde PEOR en su propio régimen) y OP Δ = **−0.094**. La lectura L1 "confirmada" (solo celdas PASS) es un espejismo de baja varianza: p a nivel símbolo 0.011 pero **p a nivel trade 0.257** — no replica. El ε²=0.574 del Estudio (E02) era artefacto de relleno-independiente-por-clúster, no edge condicional forward.
**Matiz (A6):** la lectura degradada correcta es "**no contradice la convergencia**" (el Δ punto-estimado es positivo en 3/3 lecturas agregadas, con partición selectiva); la decisión "no construir el Frame 3 de regímenes" se sostiene porque la deployabilidad neta es < 1 en cualquier lectura.

## Reproducir
```
bash audit_forense_gap_20260612/nivel3_full_run_driver.sh   # requiere GPU; ~13 celdas
```
