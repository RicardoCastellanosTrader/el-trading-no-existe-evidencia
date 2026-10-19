# E05 — Exp#2: el order block (el sistema propio del autor, objetivado)

**Hipótesis:** la hipótesis causal del operador — el "order block" como huella de liquidez institucional: gatillo anclado en zona, bloque más profundo = pool de liquidez mayor, entrada en el borde lejano, stop al cierre fuera — porta edge. Es el criterio REAL del autor, objetivado fielmente y **verificado sobre su propio ejemplo histórico (XRP) antes del barrido**.
**Nombre popular:** "order blocks / Smart Money Concepts / acción del precio" (ICT y derivados).

## Pre-registro — Nivel A (precedencia verificable en git, con intervalos cortos)
Tres iteraciones el 2026-06-26, cada una commiteada ANTES de sus resultados:
- v1 (ICT estrecho): `PREREGISTRO_EXP2_ORDERBLOCK.md` (`76a09db4`, 12:01) → resultados `8c72516a` (12:08).
- v2 (gatillo anclado): `PREREGISTRO_EXP2_V2_GATILLO.md` (`2b0f96b1`).
- v3 (criterio real final): `PREREGISTRO_EXP2_V3_FINAL.md` (`25b50930`, 17:19) → resultados `8b9bf2a0` (17:37).
Rutas bajo `analysis_scripts/atribucion_componentes_20260626/`. **Honestidad:** el orden es demostrable; con 7–18 minutos de intervalo, la "congelación previa" descansa en ese intervalo, no en días. La v1 fue retractada y re-formalizada (v3 es la que porta el veredicto). Ver [taxonomía](../../prerregistros/README.md).

## Código y datos
- Detectores: `ob_detector.py` / `ob_detector_v2.py` / `ob_detector_v3.py`; barrido `exp2_v3_barrido.py`; análisis `exp2_v3_analyze.py`.
- Gates no-look-ahead (prefix-invariance): `exp2_smoke.py`, `exp2_v2_smoke.py`, `exp2_v3_validate_smoke.py`.
- Datos: velas 1h `data_cache/` (45 símbolos) + 6 series placebo.

## Resultados
- `ATRIBUCION_T3_2_EXP2_RESULTADOS.md` (v1) + `ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md` (v3, veredicto) + `results_obv3_real.csv`, `results_obv3_placebo.csv`.

## Veredicto
**NEGATIVO ROBUSTO por brecha real-vs-placebo.** El setup geométrico da PF sobre ruido (el "floor" placebo): mediana **0.9891** de 6 series, 3 GBM (0.90, 1.04, 0.94) y 3 block-shuffles (1.66, 1.27, 0.89) (`ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md` L6). El criterio real sobre datos reales: **0.8002** (pf_all de la serie completa; mediana forward 0.739, L12) — QUEDA POR DEBAJO del ruido (brecha **−0.189**, negativa en 7/7 configuraciones). **0/45 símbolos baten el floor con intervalo de confianza** (en punto-estimado, 6/45 — no intercambiar las dos cifras). La trampa evitada: en la v1 del detector, 15/45 símbolos «pasaban» breakeven=1.0 con intervalo de confianza y solo 1/45 batía el floor (`ATRIBUCION_T3_2_EXP2_RESULTADOS.md` L13-14) — el placebo revela que eso es geometría, no liquidez. *(v1.0.3: la versión anterior mezclaba el 15/45 de la v1 con el 0/45 de la v3.)*
**Matiz (A4):** negativa con **signo robusto** (P(brecha≥0) ≤ 3.2%) pero **magnitud no ganada estadísticamente**; la certificación no-look-ahead del smoke original es irreproducible bit-a-bit, aunque la inspección independiente no halló fuga (y una fuga sería simétrica real/placebo). La ablación posterior ([E18](../E18_ablacion_orderblock/README.md)) mostró la regla causal INERTE.
