# VEREDICTO FASE 1 — Campaña de Medición del Edge Real (T3.2) — 2026-06-16

**Pregunta** (Ricardo): ¿la clase de estrategia (specialists por régimen) tiene expectativa NETA positiva sostenida sobre datos que ningún proceso de selección tocó — y de cuánto?

**Umbrales CONGELADOS** en el pre-registro aprobado (2026-06-13). Sin reajuste post-resultado. 3 zonas: DEMOSTRADO (punto≥1.3 & CI95 inf>1.0) / AUSENTE (CI95 sup<1.0) / NO CONCLUYENTE (cruza 1.0).

---

## Los tres ejes (todos con contabilidad idéntica: pnl_pct − 0.10pp fee RT)

| Experimento | Qué mide | Resultado |
|---|---|---|
| **E1 — fábrica sobre placebo** | qué floors acuña la búsqueda sobre RUIDO puro | **NOISE FLOOR = 2.35** (3 placebos, 9/9 clusters "notables", pf_fwd hasta 633 y 32775 sobre nada) → **los floors 2+ son ARTEFACTO de búsqueda** |
| **E2-lite — realizado desplegados** | PF neto de los picks LIVE post-fix sobre Binance | **0.737** CI95 [0.37, 1.30] N=93 → **NO CONCLUYENTE** |
| **E2-full — as-of holdout** | el MÉTODO aplicado point-in-time, evaluado sobre holdout intocado | **ver abajo** |

## E2-full — 8 celdas (4 símbolos × 2 anclas, anti-leakage 8/8 PASS + gate validado bidireccional)

| celda | N | PF neto | prehistoria | zona celda |
|---|---|---|---|---|
| BTC@2025-10-01 | 49 | 0.80 | 71.076 | bajo |
| BTC@2026-02-01 | 28 | 0.50 | 74.028 | bajo |
| SOL@2025-10-01 | 19 | 1.26 | 45.022 | breakeven |
| SOL@2026-02-01 | 48 | 0.45 | 47.974 | bajo |
| LINK@2025-10-01 | 14 | 0.39 | 58.730 | bajo |
| LINK@2026-02-01 | 5 | 2.39 | 61.682 | bajo→alto (N=5, ruidoso) |
| LTC@2025-10-01 | 0 | — | 68.251 | sin trades |
| LTC@2026-02-01 | 0 | — | 71.203 | sin trades |

| Conjunto | N | PF neto | CI95 | **ZONA** |
|---|---|---|---|---|
| **GLOBAL pooled** | 163 | **0.702** | **[0.439, 1.066]** | **NO CONCLUYENTE** (techo roza 1.0) |
| **A1 [2025-10,2026-02) independiente** | 82 | 0.848 | [0.444, 1.520] | NO CONCLUYENTE |
| **A2 [2026-02,2026-05-17)** | 81 | **0.534** | **[0.264, 0.960]** | **EDGE AUSENTE** |

---

## VEREDICTO (estricto + preponderancia)

**Por la regla estricta congelada**: el GLOBAL es **NO CONCLUYENTE** — el punto 0.70 está claramente bajo breakeven, pero el techo del CI95 (1.066) roza el 1.0, así que no se *demuestra* formalmente "edge ausente" sobre el pooled completo con este N.

**Por preponderancia de evidencia (las tres direcciones convergen, H2 CONFIRMADO)**:
1. **E1**: el noise floor (2.35) **iguala el floor de producción (2.32)** → los floors pf_fwd_ci_low 2+ no portan NINGUNA información de edge. Cuantificado, robusto cross-3-placebos.
2. **E2-lite**: realizado 0.737 (bajo breakeven, NO CONCLUYENTE).
3. **E2-full**: realizado global 0.702 (punto muy bajo), **A2 EDGE AUSENTE** (el holdout más reciente, CI95 sup 0.96 < 1.0, demuestra edge bajo breakeven), A1 0.848 no concluyente.

**Conclusión**: **NO hay edge neto DEMOSTRADO por encima del breakeven en ninguno de los tres ejes; la mejor estimación del edge real neto es ~0.70–0.85 PF (bajo breakeven)**, consistente con el ancla Frame 2 (Smoke C: pf_fwd 1.13 bruto ≈ 1.0 neto, ρ=+0.047). Los floors simulados 2+ son artefactos de selección sin valor predictivo. **El veredicto H2 del audit forense queda CONFIRMADO a escala.** NO se dispara T3.4 (no hay señal de edge fuerte que revise H2 al alza — al contrario).

**Disciplina de la zona NO CONCLUYENTE (global)**: la regla pre-registrada para NO CONCLUYENTE es "más datos antes de conclusión estructural". Honesto: el GLOBAL no alcanza EDGE AUSENTE estricto por el techo del CI. PERO el A2 (anclaje reciente) SÍ es AUSENTE, y los 3 ejes coinciden. Si Ricardo exige el estándar estricto sobre el pooled global, se requeriría más holdout (más anclas/símbolos) para estrechar el CI — pero la dirección (negativa) es robusta y poco probable de invertirse.

## Caveats de honestidad (§12 L38)
- **N modesto**: 163 trades pooled, CIs anchos (sistema joven + holdouts de 3.5-4 meses). La magnitud (~0.7) es más fiable que su CI.
- **LTC N=0 en ambas anclas**: la config as-of de LTC nunca clasificó/operó en sus holdouts → no contribuye. Heterogeneidad de cobertura (ajuste #1: prehistoria registrada, todas ≥45k barras sólidas).
- **LINK@A2 N=5** (PF 2.39): outlier de N minúsculo; el pooled lo pondera apropiadamente (peso 5/163).
- **Replay path-dependence**: el evaluador replica el stack live (drift arquitectónico documentado §12.30); lectura válida a nivel pooled, no per-trade.
- **Anti-leakage**: 8/8 runs PASS + gate validado bidireccionalmente (honesto pasa / envenenado caza) → los holdouts son estrictamente intocados; A2 corta en 2026-05-16 (excluye el mes que el bot operó en vivo).

## Opciones estructurales (decisión Ricardo — NO técnica)
1. **Frame 3 — atacar el edge real** (Market Regime Clustering de contexto, el paradigma que ya concebiste): el ρ=+0.047 dice que el ranking no predice; un edge real requiere cambio arquitectónico, no refinamiento de selección.
2. **Recalibrar expectativas/floors**: `pf_fwd_ci_low` NO es un forecast — dejar de usarlo como tal en reportes/health; la expectativa honesta del realizado es ~0.7–1.0 neto.
3. **Costes vs balance**: fees 0.10pp/trade sobre edge ~1.1 bruto = la mitad del edge. Palanca de alto ROI (maker entries, símbolos menos costosos) SI el edge bruto fuera positivo — pero E2-full sugiere que ni el bruto despega claramente.
4. **Aceptar + monitorizar**: operar como está (breakeven esperado, exposición mínima, instrumento íntegro) y acumular N real hasta que el CI live decida.

**Harness E2 = GATE PERMANENTE**: toda mejora futura (Fase 2 palancas) debe pasar por este harness as-of (holdout nuevo, anti-leakage) para llamarse mejora — como verify_test es el gate de fidelidad.

**Pendiente Ricardo**: elegir dirección estructural. G5 sigue PAUSADO. Bot operacional 20 sym (breakeven esperado, DD breaker activo). Sin cambios sin Tier 3.
