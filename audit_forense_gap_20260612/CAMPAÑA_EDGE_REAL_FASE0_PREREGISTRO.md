# Campaña de Medición del Edge Real — FASE 0: Inventario + PRE-REGISTRO

**Fecha**: 2026-06-13 · **Estado**: T3.1 — pendiente de aprobación de Ricardo ANTES de generar datos.
**Regla meta**: este documento se fecha y se aprueba ANTES de correr E1/E2. Los umbrales NO se ajustan tras ver resultados. Una variante sugerida por un resultado es un experimento NUEVO con holdout NUEVO.

---

## PARTE 0.1 — INVENTARIO (read-only, hecho)

### A. Profundidad de histórico Binance por símbolo (define anclas as-of posibles)

| Banda | Símbolos | Años | Anclas as-of viables |
|---|---|---|---|
| Profundo (8+ y) | BTC, ETH, LTC | 8.5–8.7 | muchas; pre-historia sobra a cualquier ancla |
| Largo (6–8 y) | XRP, TRX, XLM, ETC, VET, DOGE, LINK, BCH, SOL, FET | 5.8–8.0 | anclas ≥2024 cómodas |
| Medio (2–3 y) | SEI (2.8), TAO (2.1) | 2.1–2.8 | anclas ~2025-Q4 dejan ~1.5–2y pre-historia (límite GMM) |
| Reciente (1–2 y) | RENDER (1.8), POL (1.7), ONDO (1.1) | 1.1–1.8 | anclas as-of INVIABLES (pre-historia <1y para GMM) → excluidos de E2-full |

**Consecuencia de diseño**: E2-full as-of solo sobre símbolos con ≥3y de historia (excluye ONDO/POL/RENDER/TAO/SEI según ancla). Símbolos candidatos a as-of: BTC, ETH, SOL, LINK, DOGE, BCH, XRP, TRX, LTC, XLM, ETC, VET, FET.

### B. Infraestructura de replay (E2 la REUSA, no se reconstruye)

`audit_forense_gap_20260612/replay_engine.py` — motor del audit, validado: replica ciclo-a-ciclo `classify_regimes` (GMM+histéresis 0.75) → `apply_btc_override` → `select_active_configs` → `generate_signals` + gate portfolio 0.60, contabilidad pnl_pct − 0.10pp fee RT. Sus salidas reprodujeron el live a nivel cartera (corr PnL 0.914 emparejados). **Reuso para E2-lite/E2-full**: parametrizar (a) fuente de velas → `binance_data/` en vez de `bingx_data/`, (b) ventana → post-selección completa / post-ancla, (c) set de artefactos → desplegados coherentes / as-of. Es parametrización del motor existente, NO reconstrucción.

### C. Coste GPU por run as-of completo (dimensiona E2-full a algo finito)

Medido del regen ADA (2-fases H_B, histórico 71.397 barras, 30 presets):
- **Fase 1** (download + GMM + lab_lite): **31 s** total (lab_lite 2.3s). Trivial.
- **Fase 2** (regime walk-forward): **9 h 05 m**. Kernel GPU ~118s/preset (~1h de GPU pura); el resto es **precompute CPU single-core** ("Vela N/71397") sobre el histórico completo — el cuello de botella escala con nº de barras.

**Dimensionamiento**: un run as-of ≈ 9h para histórico de 8 años; menos para histórico corto (escala ~lineal con barras). E2-full a 6–8 sym × 2–3 anclas = 12–24 runs × ~9h = **108–216h (4.5–9 días) — NO finito**. **Propuesta finita**: **4 símbolos × 2 anclas = 8 runs**, eligiendo símbolos de profundidad mixta y anclas que truncan historia → ~5–8h/run → **~40–64h (~2–3 días) secuencial estricto #14**. Expandible si el resultado lo amerita (Fase 2, holdout nuevo).

### D. Procedencia de los anclajes empíricos (umbrales NO inventados — §12 L38)

- **Smoke C 2026-04-24** (commit `431b5e1`, N=20 top-1 cross-símbolo, Binance, pipeline EXACTO doubled_labels + split 67/33): **pf_tr=1.53 → pf_fwd=1.13 (decay 26%)**, **Spearman ρ(JSON, binance)=+0.047** (nula), **1/20 top-1 pf_fwd≥2**, **11/20 pf_fwd<1**. → ancla del edge estructural: **pf_fwd ≈ 1.13 bruto** (~1.02 neto tras −0.11 fees). El ranking walk-forward NO predice el realizado.
- **Audit forense 2026-06-12**: live PF 0.859 [CI95 0.41–1.73], replay-corregido 0.640 [0.26–1.31], floor blended esperado 2.32. Δbug +0.03 PF. Consistente con Smoke C: realizado ~breakeven, floors son métrica interna.
- **CORRECCIÓN §12 L38**: el directive cita "survival 7.6%" — **NO existe en primary-source**. El documentado (LL2/A13) es **ratio supervivencia mean 36.7%, sano si ≥20%** (es ratio input→output de lab_lite, no una tasa de edge). Uso el 36.7% real; descarto el 7.6%.

### E. Staleness de datos (relevante para E2)

`data_cache` local de símbolos G1 (BTC/ETH/BNB/XRP/TRX) llega solo a **2026-05-08** (último reciclaje). E2-lite/E2-full requieren re-fetch Binance a fecha actual. El audit ya tiene `binance_data/` (20 sym → 2026-06-12) que cubre las ventanas live; E2-full as-of necesitará fetch Binance completo por símbolo as-of (truncado al ancla).

---

## PARTE 0.2 — PRE-REGISTRO (los 3 experimentos de FASE 1)

**Redefinición operativa de "notable" (por evidencia, NO floors 2+)**: criterio institucional = **expectativa NETA con CI95 que excluya 1.0 por arriba**. El número objetivo lo fija la evidencia.

---

### E1 — FÁBRICA SOBRE PLACEBO (noise floor)

**Pregunta única**: ¿cuánto "rendimiento simulado notable" acuña el pipeline de selección EXACTO desde datos SIN estructura explotable?

**Hipótesis**: H1 = los floors de producción (pf_fwd_ci_low) son artefactos de búsqueda — la fábrica los produce sobre ruido puro. H0_E1 = los gates filtran el ruido (0 notables sobre placebo).

**Datos (placebo, 6 series)**:
- 3× **random walk GBM** con σ horaria calibrada a la vol realizada de {BTC, SOL, SEI} (drift 0).
- 3× **block-shuffle** de retornos reales de {BTC, SOL, SEI}, bloque=168h (1 semana): rompe la autocorrelación que el MA-cross necesita, preserva el marginal (colas, vol-clustering intra-bloque).
- Longitud: ~25.000 barras (~2.85 a) cada una — suficiente para GMM + walk-forward, mantiene el run finito.
- Semilla fija registrada (reproducibilidad). Generación determinista, documentada.

**Pipeline**: EXACTO (lab_lite + walk_forward + gates + mesetas + diversity + trades_5k≥50). Sin tocar lógica — solo se sustituye la entrada de datos.

**Métrica primaria**: distribución de **top-1 pf_fwd_ci_low** por placebo-símbolo + **conteo de clusters que pasan TODOS los gates** con pf_fwd_ci_low≥2.0.
**Secundarias**: distribución de top-1 pf_fwd (forward realizado-proxy), survival ratio, nº notables vs producción.

**Regla de decisión (PRE-REGISTRADA, ambas direcciones)**:
- **Floors = artefacto** si la mediana de top-1 pf_fwd_ci_low sobre placebo **≥ 1.7** (extremo bajo del rango de producción 1.7–3.9) → demostración directa cuantificada de que el floor no porta edge.
- **Gates filtran ruido** si **0/6** placebo producen algún cluster con pf_fwd_ci_low≥1.5 → el floor porta señal.
- **Intermedio**: reportar el percentil de producción dentro de la distribución placebo (cuánto del floor es ruido vs señal). Sin reajuste.

**Coste**: ~6 × 3–4h ≈ **18–24h GPU**. **Holdout**: N/A (datos sintéticos, no consume holdout real).

---

### E2-LITE — REPLAY EXTENDIDO DE PICKS DESPLEGADOS (realizado, barato)

**Pregunta única**: ¿el PF NETO realizado de los specialists desplegados (post-fix, coherentes), agregado sobre TODA la ventana post-selección en Binance, supera el breakeven?

**Hipótesis**: H0 = edge neto ≤ breakeven (PF ≤ 1.0). Rechazable si CI95 pooled inferior > 1.0.

**Datos/holdout**: por generación, ventana deploy→2026-06-13 sobre velas **Binance** (evita ruido BingX), artefactos **coherentes post-fix**, contabilidad pnl_pct − 0.10pp fee RT.
| Gen | Deploy | Ventana OOS | N esperado |
|---|---|---|---|
| G1 | 2026-05-17 | ~27 d | ~40–55 |
| G2 | 2026-05-22 | ~22 d | ~15–25 |
| G3 | 2026-06-05 | ~8 d | ~5–12 |
| G4 | 2026-06-12 | ~1 d | ~0–2 (se reporta, no pondera) |

**HONESTIDAD del N (§12 L38)**: el sistema es JOVEN — las ventanas live suman **~70–90 trades**, NO "cientos". E2-lite mejora sobre el audit (N=56, BingX) por: Binance-limpio + artefactos coherentes + pooling 4 gen, pero **NO alcanza cientos**. Los cientos vienen de E2-full (holdouts as-of largos). Declarar esto evita sobre-vender E2-lite.

**Métrica primaria**: PF neto realizado pooled + CI95 bootstrap (10.000). Per-generación + per-(sym,cluster).
**Regla de decisión (PRE-REGISTRADA)**: rechazo H0 si CI95 inf > 1.0. Si CI95 contiene 1.0 → no se rechaza breakeven (consistente H2). Si CI95 sup < 1.0 → edge neto negativo.

**Coste**: replay, ~1h CPU, **sin GPU**. **Holdout consumido**: ventanas live G1–G4 (registradas como QUEMADAS para "realizado de picks desplegados"; ya medidas parcialmente por el audit — no tuneadas).

---

### E2-FULL — HOLDOUT RETROSPECTIVO as-of END-TO-END (decisivo)

**Pregunta única**: ¿el MÉTODO de selección, aplicado strict point-in-time as-of fechas históricas, produce picks cuyo PF neto realizado sobre el periodo post-ancla INTOCADO supera el breakeven?

**Hipótesis**: H0 = el método no generaliza (PF neto holdout ≤ 1.0). Falsable en AMBAS direcciones.

**Diseño (propuesta finita — Ricardo ajusta)**:
- **4 símbolos** de profundidad mixta: **BTC** (8.7y), **SOL** (5.8y), **LINK** (7.4y), **SEI** (2.8y).
- **2 anclas**:
  - **A1 = 2025-10-01** → holdout **2025-10→2026-01** (~3 m). **INDEPENDIENTE de E2-lite** (termina antes del deploy de mayo).
  - **A2 = 2026-02-01** → holdout **2026-02→2026-06** (~4 m). Solapa calendario con E2-lite (picks distintos; sin tuning cruzado).
- 8 runs full-pipeline as-of (truncados al ancla) → replay sobre post-ancla.
- **N esperado**: ~4 sym × ~100 d × ~0.4 trades/d × 2 anclas ≈ **250–350 trades** ("cientos" reales).

**ANTI-LEAKAGE (CARDINAL — el hallazgo más crítico de la fase; un leak invalida todo)**:
verificación primary-source de que el run as-of NO ve dato > ancla en NINGÚN paso:
1. **Download**: parquet truncado a ≤ ancla; el pipeline NO re-descarga a "now" (desactivar PASO 1 o pre-colocar parquet truncado + correr desde GMM).
2. **GMM**: training cutoff = ancla (verificar `training_date_range[1]` ≤ ancla en el joblib generado).
3. **lab_lite**: ventana 5000-barras debe terminar ≤ ancla (verificar última vela del slice).
4. **walk-forward**: train + forward AMBOS ≤ ancla (el forward es parte de la SELECCIÓN, no de la evaluación; la evaluación es el replay post-ancla separado).
- Gate de leakage codificado: script que afirma, por cada run, que el max(timestamp) de cada artefacto/intermedio ≤ ancla. FAIL → T3.3 inmediato, fase invalidada.

**Métrica primaria**: PF neto realizado sobre holdout, pooled (sym×ancla) + CI95 bootstrap. Per-celda.
**Regla de decisión (PRE-REGISTRADA, ambas direcciones)**:
- **Edge SOSTENIDO** si CI95 inf > 1.0 Y punto ≥ ~1.3 → revisa veredicto H2 del audit (**T3.4**), conversación → escala.
- **Frame 2 a escala** si CI95 contiene 1.0 (punto ~1.0–1.2) → breakeven establecido sobre roca, conversación estructural honesta.
- **Método net-negativo** si CI95 sup < 1.0.

**Coste**: 8 runs × ~5–8h ≈ **40–64h GPU** secuencial estricto #14. **Holdout consumido**: (BTC/SOL/LINK/SEI) × (A1, A2) post-ancla — QUEMADOS una vez. Variantes Fase 2 → anclas/símbolos NUEVOS.

---

## LIBRO MAYOR DE HOLDOUTS (presupuesto de datos)

| Holdout | Experimento | Estado |
|---|---|---|
| Sintético E1 (semilla fija) | E1 | no consume real |
| Live G1–G4 (deploy→2026-06-13) | E2-lite | se quema al correr E2-lite |
| BTC/SOL/LINK/SEI × {2025-10, 2026-02} post-ancla | E2-full | se quema al correr E2-full |
| **Reservado para Fase 2** | palancas | anclas/símbolos NO usados arriba (p.ej. 2025-07, 2025-04; ETH/DOGE/BCH/XLM) |

Solape E2-lite ↔ E2-full A2 (calendario 2026-02→06): picks DISTINTOS, ninguna decisión de tuning cruza entre experimentos. Documentado, no es violación (el holdout se quema por TUNING, no por medición independiente).

---

## ANDAMIAJE DE HARNESS REQUERIDO (y el invariante que preserva)

- **E1**: generador de placebo (GBM calibrado + block-shuffle, semilla fija) → inyecta parquet sintético; el pipeline corre desde GMM. 
- **E2-full**: truncador as-of (slice del parquet a ≤ ancla) + gate de leakage (asserts de max-timestamp por paso).
- **INVARIANTE**: los scripts del pipeline (`lab_lite`, `regime_walk_forward`, `master`) corren con su LÓGICA INTACTA — el harness solo controla la ENTRADA de datos y verifica cutoffs. **brain/portfolio/kernel/cancel_ghost NO se tocan**. Todo código de harness es test-only y se verifica que no altera el cómputo del pipeline. §13.3 upgrade stack intacto.

---

## PREGUNTAS PARA TU APROBACIÓN (T3.1) — antes de generar datos

1. **Presupuesto GPU E2-full**: ¿4 sym × 2 anclas (~40–64h) OK, o reducir/ampliar? (G5 diferido durante la campaña).
2. **Símbolos E2-full**: ¿BTC/SOL/LINK/SEI (profundidad mixta), u otra selección? SEI (2.8y) es el más arriesgado por pre-historia.
3. **Anclas E2-full**: ¿2025-10-01 + 2026-02-01? (la primera da holdout independiente de E2-lite).
4. **Orden de ejecución**: propongo **E2-lite primero** (barato, sin GPU, mata-objeción-N parcial) → **E1** (noise floor, ~20h) → **E2-full** (decisivo, ~40–64h). ¿OK?
5. **Umbral "edge sostenido"** E2-full: fijé punto ≥1.3 + CI95 inf >1.0. ¿Lo confirmas o ajustas AHORA (no después)?
6. **Andamiaje**: ¿autorizas el harness test-only (placebo injector + as-of truncator + leakage gate), entendido que NO toca lógica del pipeline ni código productivo?

**NO genero ningún dato de FASE 1 hasta tu aprobación de este pre-registro.**
