# E02 — Estudio de Capacidad de Información (¿el pasado predice el forward?)

**Hipótesis:** alguna dimensión del rendimiento pasado (PF, score compuesto, estabilidad, régimen) predice el rendimiento forward de una configuración.
**Nombre popular:** "elige la config/estrategia con mejor histórico" — el ranking por rendimiento pasado, la operación central de toda optimización.

## Pre-registro — Nivel B (documental, commit conjunto)
- `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` — pre-registro congelado (D1–D6, m=6, FDR-BH q=0.10 + Bonferroni, bootstrap por símbolo) pero commiteado junto al veredicto (`06091df3`, 2026-06-16). Ver [taxonomía](../../prerregistros/README.md).

## Código y datos
- Harness: `audit_forense_gap_20260612/estudio_capacidad_fase1.py`.
- Población N1: 13.500 configs (45 sym × 3 clústeres × top-100, `regime_wf/*_specialist_configs.json`); ancla N2 independiente: `binance_w3_data` (no tracked; regenerable — [`REGENERAR.md`](../../datos/REGENERAR.md)).

## Resultados
- `audit_forense_gap_20260612/estudio_capacidad_fase1_results.json` + `VEREDICTO_ESTUDIO_CAPACIDAD.md`.

## Veredicto
**Re-selección por rendimiento pasado: muerta o mecánica.**
- `specialist_score` (la métrica que el pipeline usa para rankear) → forward: **ρ = +0.054, CI [−0.010, +0.117]** — cruza 0 incluso en su propia slice.
- `pf_tr` puro: +0.297 en-slice → **−0.05 en datos independientes** (canónico ρ(fwd_JSON, fwd_bin) = +0.0465, reproducido exacto).
- 3 de 4 "señales" congeladas resultaron ser **auto-correlación mecánica** (D1/D2/D5 promedian o acotan el propio forward — desenmascaradas por auditoría de contaminación en fuente primaria).
- La única candidata viva (D3 régimen, ε²=0.574) pasó a confirmación en [E03](../E03_regimen_d3/README.md) — y no confirmó.
**Matiz (A2):** D6 "muerta within-shortlist"; D4 (perfil de fracaso) quedó *untested* en N1 (base rate de fracasos 0.00% en supervivientes); el bug NaN de D5 corregido cambia +0.2345→+0.7465 (más mecánica aún).
