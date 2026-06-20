# VEREDICTO NIVEL 3 — D3 (eje régimen) NO CONFIRMADO

**Fecha:** 2026-06-21 · **Run:** 13 celdas as-of, ancla 2025-05-01, holdout capado 2026-05-16, fuente data_cache.
**Disciplina:** pre-registro congelado (T3.1), holdout intocado, anti-leakage, chequeo de robustez. NO se miró Δ/AUC hasta cerrar la validez de las celdas.

## Resultado del run (operacional)
- **13/13 celdas selladas, CERO crashes en ~4 días.** El TDR 0x116 original fue transitorio (re-smoke ETH 8h32m @1M sin TDR; ver `project_nivel3_tdr_transitorio`). Infra de auto-reanudación armada — nunca tuvo que actuar.
- **Leakage gate 13/13 PASS.** Integridad anti-fuga sólida.

## Gate de fidelidad: mixto, diagnosticado BENIGNO
- 7 PASS (Jaccard 1.000) / 2 NO CONCLUYENTE / 4 FAIL (Jaccard 0.62–0.78), **divergentes(señal)=0 en 13/13**.
- **Diagnóstico (medido, no asumido):** drift path-dependent §12.30 BENIGNO — señal idéntica, conteos preservados, atribución del propio gate `state-path-dep(config idéntico)`.
- **Hipótesis MA-composition REFUTADA** (los MAs iterativos VIDYA/KAMA/ALMA/T3/FRAMA/McGinley son ubicuos: XRP PASS usa 100%). **Driver real = nº de régimenes con trades:** 1→PASS (drift mueve ±1-2 barras *dentro* del régimen, tag intacto) / 2→FAIL / 3→NO CONCLUYENTE (más trades en fronteras → flip de tag).
- Ruido PF_match (orch canónico vs agn): <5% (DOT/THETA/AVAX/OP), 8.7% ATOM, 17.5% INJ (cruza 1.0).

## Tensión cardinal: fidelidad ↔ cobertura ANTI-correlacionadas
Las celdas de fidelidad perfecta (PASS) son **single-régimen** → apenas ejercen el MATCH/MISMATCH que D3 pregunta. Las celdas que SÍ ejercen D3 (multi-régimen) son las ruidosas. El veredicto se resuelve con tres lecturas:

| Lectura | n | Δ_pooled | p_sym | p_trade | zona |
|---|---|---|---|---|---|
| L1 solo-PASS (single-régimen) | 6 | +0.099 | 0.011 ✓ | 0.257 ✗ | "CONFIRMADA"* |
| L2 +secundario (multi-rég) | 12 | +0.091 | 0.043 ✗ | 0.182 ✗ | NO CONCL. |
| L3 sin-INJ | 11 | +0.098 | 0.037 ✗ | 0.166 ✗ | NO CONCL. |

*(Bonferroni α=0.025, m=2 primarios; H1 una cola Δ>0)*

## VEREDICTO D3: **NO CONFIRMADO** (NO CONCLUYENTE, lean negativo en las celdas informativas)
- La "CONFIRMADA" de L1 es **espejismo de baja varianza** de 6 celdas single-régimen homogéneas: no replica a nivel trade (p=0.257), no sobrevive añadir celdas informativas (L2/L3 p_sym>0.025), y NO es ruido (L3 sin la celda más ruidosa ≈ L2).
- **Decisivo:** las 2 celdas **3-régimen** (las que más ejercen MATCH/MISMATCH) **leanean NEGATIVO** — **THETA Δ=−0.535** (PF_match **0.53** vs PF_mis **1.07**: el specialist rinde *mucho peor* en su propio régimen) + OP Δ=−0.094. El signo positivo viene de celdas 2-régimen (ATOM +1.01, AVAX +0.69) y del set single-régimen de baja varianza — los menos informativos.
- **Interpretación:** el ε²=0.574 del Estudio de Capacidad (el único candidato vivo) era **H_artefacto** (relleno independiente por clúster), NO edge forward régimen-condicional real. El test MATCH/MISMATCH, diseñado para separarlos, lean hacia el artefacto.

## VEREDICTO D4: **NO EVALUABLE**
0/2100 fracasos (pf_fwd<1) en el set de supervivientes — la selección embebe el forward, filtra los fracasos. Una AUC requiere fracasos. Rigurosa necesitaría replay holdout de población failure-inclusive (no hecho). Mismo resultado que el Estudio de Capacidad.

## CONCLUSIÓN CENTRAL — la CONVERGENCIA (el arco completo de medición de edge)
Tres líneas **independientes** convergen:
1. **Campaña Edge Real** (E1/E2 as-of): noise floor 2.35 ≈ floor producción → floors pf_fwd 2+ son artefacto de búsqueda; E2-full GLOBAL 0.702 [0.44,1.07] → **sin edge neto demostrado** (~0.70–0.85 PF).
2. **Estudio de Capacidad**: re-selección por PF/calidad/estabilidad MUERTA o mecánica (3 de 4 "señales" = auto-correlación; specialist_score→fwd ρ+0.05 cruza 0; ρ(pf_fwd_JSON,pf_fwd_bin)=+0.047).
3. **Nivel 3** (este doc): D3 régimen NO confirmado, adverso donde se ejerce.

→ **Re-seleccionar sobre el RENDIMIENTO PASADO (cualquier dimensión medible: PF, calidad, estabilidad, régimen) NO produce edge robusto explotable** en esta familia de estrategia, estos mercados, estos costes. Establecido con holdouts intocados, anti-leakage 13/13 PASS, pre-registro congelado, chequeo de robustez que cazó el último espejismo single-régimen.

## QUÉ QUEDA REIVINDICADO (no malinterpretar el veredicto)
El veredicto es sobre la **familia de estrategia + la forma de selección**, NO sobre la calidad de la construcción:
- **La ingeniería es sólida:** fidelidad certificada (kernel↔brain diff 0.0000), ejecución fiel, datos limpios (bug de asignación cerrado, provenance gate), instrumento institucional (master.py pipeline, gates).
- **El harness E2 as-of queda como GATE PERMANENTE** para cualquier estrategia futura: ninguna mejora se acepta sin pasar el holdout intocado anti-leakage.
- La disciplina §12 L38 / chequeo de robustez protegió tanto del falso negativo como del falso positivo (el espejismo L1).

## Decisiones derivadas
- **NO construir Frame 3** sobre el eje régimen (no hay edge régimen-condicional que arquitecturar).
- **NO expandir a 2 anclas** (el veredicto converge desde 3 ángulos, no es ambiguo-por-N; es adverso).
- **Migración Kraken / MiCA:** decisión aparte (estaba condicionada a un veredicto que justificara reciclar; no lo justifica).
- **Bot v2.8.1** sigue operando 20/20 (breakeven esperado) — decisión estratégica sobre el bot = conversación aparte, NO acción de este cierre.

Cross-ref: `VEREDICTO_FASE1.md` (Campaña Edge Real) + `VEREDICTO_ESTUDIO_CAPACIDAD.md` (Estudio) + `NIVEL3_CONFIRMACION_D3_DISENO_PREREGISTRO.md` (diseño) + sealed trades `nivel3_resmoke_trades_*_2025-05-01_data_cache.json` (evidencia).
