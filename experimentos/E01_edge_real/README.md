# E01 — Campaña Edge Real (as-of, holdout intocado)

**Hipótesis:** el sistema completo optimizado (familia SmartDiv TF+MR, selección walk-forward por régimen sobre 45 símbolos) tiene edge neto cuando se re-ejecuta su selección *as-of* (solo con información disponible en la fecha ancla) y se evalúa sobre holdout intocado.
**Nombre popular:** "mi backtest/walk-forward gana" — la promesa base de todo sistema optimizado.

## Pre-registro — Nivel A (precedencia verificable en git)
- `audit_forense_gap_20260612/CAMPAÑA_EDGE_REAL_FASE0_PREREGISTRO.md` — commit `d94123d` (2026-06-13), **3 días antes** del veredicto (`6b396ac`, 2026-06-16). Ver [guía de verificación](../../prerregistros/README.md).

## Código
- Harness as-of anti-leakage bidireccional: `audit_forense_gap_20260612/asof_run.py` (selección) + `asof_eval.py` (replay) + `asof_driver.sh`.
- Placebos sintéticos (GBM y block-shuffle de 168 h): `audit_forense_gap_20260612/placebo_gen.py` + `placebo_manifest.json` (símbolos `PLB*`).
- Kernel bajo test: `lab_historico_numba_v8_3.py` (TF) + `mean_reversion_kernel.py` (MR); pipeline `regime_walk_forward.py`.

## Datos
Velas 1h de `data_cache/` (incluidas en el repo; regenerables — ver [`../../datos/REGENERAR.md`](../../datos/REGENERAR.md)).

## Resultados
- Veredicto: `audit_forense_gap_20260612/VEREDICTO_FASE1.md`.
- Per-celda: `audit_forense_gap_20260612/asof_result_{SYM}_{ANCLA}.json` + `asof_trades_{SYM}_{ANCLA}.csv` (BTC/SOL/LINK/LTC × 2025-10-01 / 2026-02-01).

## Veredicto
**Sin edge neto demostrado.** PF neto real global (E2-full as-of): **0.702, CI95 [0.439, 1.066], N=163 trades**; E2-lite 0.737. La búsqueda acuña "floors" espectaculares sobre nada: noise floor E1 = **2.35 sobre placebos de ruido** — mediana de 1 GBM (2.14) y 2 block-shuffles de 168 h (3.03 y 2.35), `e1_noise_floor/RESULTADO_E1.md` L7-13; el GBM solo ya supera el umbral pre-registrado de 1.7 — (9/9 clústeres "notables" sobre ruido), cercano al floor de producción 2.32 (comparación descriptiva: no hay contraste entre las dos cifras).
**Matiz (meta-auditoría A1):** el holdout más reciente es "no concluyente lean-negativo" (CI iid superior 0.96 < 1.0), no "ausencia demostrada": el bootstrap por celdas [0.452, 2.392] cruza 1.0 y la regla de 3 zonas pre-registrada se aplica al agregado, no a cada ancla (`FASE_A_correcciones_documentales.md` §A1) — el CI global cruza 1.

## Reproducir
```
bash audit_forense_gap_20260612/asof_driver.sh   # por símbolo/ancla; ver cabecera del script
```
El gate de leakage es bidireccional: la selección no ve el holdout y el replay reproduce las señales del orchestrator (13/13 PASS en el run sellado).
