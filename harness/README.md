# Harness — el instrumental anti-autoengaño

Este directorio documenta las herramientas de validación que sostienen los veredictos. La regla del proyecto: **ningún resultado cuenta si no pasó por su gate**. Cada pieza vive en su ruta histórica; aquí se explica qué garantiza, cómo se invoca y quién la usa.

## 1. Harness E2 as-of — anti-leakage bidireccional ("el gate permanente")
**Rutas:** `audit_forense_gap_20260612/asof_run.py` (selección as-of) + `asof_eval.py` (replay de evaluación) + `asof_driver.sh`.
**Qué garantiza:** la SELECCIÓN de configuraciones se re-ejecuta usando exclusivamente información disponible en la fecha ancla (ningún dato del holdout entra en la selección), y la EVALUACIÓN reproduce fielmente las señales del orchestrator de producción (gate de fidelidad: el replay debe reproducir los trades MATCH del orchestrator). Bidireccional: ni el pasado ve el futuro, ni la evaluación reinventa la ejecución.
**Lo usan:** E01 (Campaña Edge Real), E03 (Nivel 3, vía `asof_d3d4_extension.py`), E17.

## 2. Gates de no-look-ahead (prefix-invariance)
**Rutas:** `analysis_scripts/atribucion_componentes_20260626/exp2_smoke.py`, `exp2_v2_smoke.py`, `exp2_v3_validate_smoke.py`; `mfe_sandbox/run_edge.py` (integrado); `analysis_scripts/atribucion_componentes_20260626/exp1_smoke.py`.
**Qué garantizan:** que la señal calculada en la barra *t* es idéntica si se recalcula con la serie truncada en *t* (prefix-invariance) — es decir, que ningún indicador "ve" barras futuras. Es el test que convierte "confía en mí, no hay look-ahead" en una propiedad verificable mecánicamente.
**Lo usan:** E04, E05, E06, E18.

## 3. Placebos — la vara de medir contra el ruido
**Rutas:** `audit_forense_gap_20260612/placebo_gen.py` + `placebo_manifest.json` (series GBM sintéticas, símbolos `PLB*`).
**Qué garantizan:** todo pipeline de búsqueda se ejecuta TAMBIÉN sobre ruido puro con la misma maquinaria. Si el procedimiento "encuentra" lo mismo sobre GBM que sobre datos reales, lo encontrado es un artefacto del procedimiento (el hallazgo cardinal de E01: noise floor 2.35 ≈ floor de producción 2.32; el floor placebo 0.989 de E05). Regla de la Lista de Cierre: placebo = **GBM puro**, no block-shuffle (que preserva estructura explotable).
**Lo usan:** E01, E04, E05, E18 y todos los B vía harness común.

## 4. Harness cross-sectional B/C — cluster-bootstrap + gate beta
**Ruta:** `cierre_definitivo_20260702/xs_harness.py` + runners `run_B124.py`, `run_B3.py`, `run_B5.py`, `run_B6.py`, `run_B7.py`, `run_B8.py`, `run_C1_extend.py`, `run_C2.py`, `run_C3.py`.
**Qué garantiza:** (a) **cluster-bootstrap cross-símbolo** — los CIs respetan que los 45 símbolos co-mueven (un bootstrap ingenuo por observación fabricaría significancia); (b) **gate beta** — todo factor "neutral" se regresa contra el mercado; si su retorno es beta disfrazada, se declara (así cayó E11: β −0.494); (c) métrica cardinal fijada a priori en el pre-registro, sin pivote post-hoc; (d) CI en el número que decide.
**Lo usan:** E08–E15, E16–E18.

## 5. Certificación de fidelidad sim↔live
**Rutas:** `cert_fidelity_gate.py` + `cert_fidelity_gate_W1500.json` (raíz); auditoría forense completa en `audit_forense_gap_20260612/INFORME_AUDITORIA_FORENSE_GAP.md` + `replay_engine.py`.
**Qué garantiza:** que el sistema que se mide en laboratorio es el que operó con dinero real — certificación señal-a-señal brain↔kernel con match-rate **98.24–100% por símbolo** (p.ej. BTC 100% sobre 250 señales), más la auditoría temprana contra fills reales de BingX (10/11 = 91%, N=11, CI [62%, 98%]). Sin esto, cualquier gap sim-vs-real invalidaría la extrapolación de los veredictos al mundo real.
**Lo usan:** los 736 fills de [`../trades_reales/README.md`](../trades_reales/README.md); E01 (vía replay).

## Cómo atacar esto (invitación)
1. Busca look-ahead: rompe la prefix-invariance de cualquier señal (los smokes son ejecutables).
2. Recomputa los CIs con tu propio bootstrap sobre los results_*.json.
3. Ejecuta los pipelines sobre TUS placebos y compara floors.
4. Audita la selección as-of: `asof_run.py` no debe tocar ningún archivo con datos posteriores al ancla.
