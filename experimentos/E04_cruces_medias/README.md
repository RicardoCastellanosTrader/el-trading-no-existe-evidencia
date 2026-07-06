# E04 — Exp#1: el cruce de medias aislado, con parámetros lógicos

**Hipótesis:** el componente "cruce de zona de medias" porta edge por sí mismo, con parámetros LÓGICOS fijados a priori (sin optimizar), frente a un random walk.
**Nombre popular:** "cruces de medias móviles" — golden cross y variantes; se prueban 14 tipos de media.

## Pre-registro — Nivel B (documental, commit conjunto)
- `analysis_scripts/atribucion_componentes_20260626/PREREGISTRO_EXP1_MEDIAS.md` — params lógicos y contraste congelados por escrito; commit conjunto con resultados (`d5ae6c81`, 2026-06-26). Ver [taxonomía](../../prerregistros/README.md).

## Código y datos
- Runners: `analysis_scripts/atribucion_componentes_20260626/exp1_runner_tf.py` + `exp1_runner_mr.py` + `exp1_analyze.py`; gate de humo `exp1_smoke.py`.
- Datos: velas 1h `data_cache/` (45 símbolos) + placebos GBM.

## Resultados
- `analysis_scripts/atribucion_componentes_20260626/ATRIBUCION_T3_2_RESULTADOS.md` + `results_tf_logical.csv`, `results_mr_logical.csv`, `results_placebo.csv`, `results_optimized.csv`.

## Veredicto
**NEGATIVO — el cruce no porta edge.**
- TF: median pf_fwd **0.917** (config primaria 10/55, N=630 celdas; 0.927 sobre las 3.780 celdas) vs placebo random-walk **0.928**.
- MR: **0.742** vs placebo **0.853**.
- **0/14 tipos de media** con mediana > 1. Robusto cross-parámetro.
- La brecha que sí existe es la del sobreajuste: optimizado-por-activo **3.317** vs lógico **0.917** — la diferencia no es edge, es la medida de la contaminación por selección.
**Matiz (A3):** la lectura correcta es "indistinguible del ruido **y** sub-breakeven", no "peor que el ruido" (el floor del placebo estaba inflado por una serie sintética, PLBSH3).
