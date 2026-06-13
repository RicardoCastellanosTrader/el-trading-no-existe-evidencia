# E1 — Resultado del NOISE FLOOR (fábrica sobre placebo) — 2026-06-13

**Pregunta**: ¿cuánto "rendimiento simulado notable" acuña el pipeline de selección EXACTO desde datos SIN estructura explotable?

**Diseño** (enmienda 1: 3 placebos): pipeline producción completo (lab_lite + walk-forward + gates + mesetas + diversity + trades_5k≥50) sobre 3 series placebo. Semilla 20260613.

| Placebo | Tipo | top-1 pf_fwd_ci_low por cluster | mediana | notables (≥2) |
|---|---|---|---|---|
| PLBGB1 | GBM~BTC (ruido puro iid) | [100.0, 2.08, 2.14] | **2.14** | 3/3 |
| PLBSH1 | SHUF~BTC (block-shuffle 168h) | [3.03, 100.0, 2.30] | **3.03** | 3/3 |
| PLBSH2 | SHUF~SOL (block-shuffle 168h) | [2.95, 2.35, 2.02] | **2.35** | 3/3 |

**NOISE FLOOR = 2.35** (mediana de las 3 medianas).

**Regla pre-registrada** (mediana top-1 pf_fwd_ci_low ≥1.7 → floors artefacto): **2.35 ≥ 1.7 → FLOORS = ARTEFACTO DE BÚSQUEDA**, cuantificado.

**Condición #4 (robustez cross-modo/cross-fuente)**: las 3 medianas [2.14, 3.03, 2.35] **COINCIDEN direccionalmente** (todas ≥1.7, 9/9 clusters notables). GBM (ruido puro) y block-shuffle (marginales reales) concuerdan; el shuffle da floors algo mayores (más survivors espurios por su vol-clustering). **Noise floor SÓLIDO** — sin discrepancia que reportar.

**Hallazgo cardinal**: el noise floor **2.35 ≈ floor de producción blended 2.32** (match casi exacto). Los floors pf_fwd_ci_low 2+ de los specialists desplegados son **estadísticamente indistinguibles de lo que la búsqueda acuña sobre ruido puro**. Señales extremas sobre ruido: pf_fwd=633 (PLBGB1 C0), pf_fwd=**32775** (PLBSH1 C1) — la búsqueda encuentra configs "perfectos" donde no hay nada que encontrar.

**Implicación**: el forward-PF del walk-forward (y su CI-low) es un **artefacto de selección, no un pronóstico**. Refuerza H2 del audit (los floors no portan edge real). NO revisa H2 al alza (no dispara T3.4). Contextualiza E2-lite (realizado neto 0.737, NO CONCLUYENTE) y prepara la lectura de E2-full (as-of, decisivo).

**Coste**: 3 placebos × ~3.5-5h = ~13h GPU + ~200-250GB parts transitorios/placebo (cleanup per-símbolo OK). Evidencia: los 3 specialist JSONs placebo preservados en este directorio.
