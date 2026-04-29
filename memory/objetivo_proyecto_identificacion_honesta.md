# Objetivo del proyecto: identificación honesta de configuraciones notables dentro del universo de candidatas

**Fecha origen**: 2026-04-29 (sesión continuación post-Sub-fase J.0).
**Carácter**: foundational — referencia rápida cross-conversation memory cuando la lectura completa de §0.0 + §13.2 del CONTEXTO_PROYECTO_TRADING.md no ocurra.

## Cuantificación verificada empíricamente 2026-04-29

- **Bits config_id TF kernel**: 26 bits ocupados (`decode_config` en `lab_historico_numba_v8_3.py:1202-1212`, bits 0-25).
- **Combinaciones válidas/preset**: **20,891,648** tras filtros (`generate_valid_configs()`; Path 1 sin div = 2,048; Path 2 con div = 20,889,600).
- **Presets/símbolo (CSVs producción `output/production/presets_*.csv`)**: media 30.5, rango 28-32, sobre 48 CSVs.
- **Símbolos operacionales bot productivo**: **45** (primary source autoritativo: `master.py CONFIG['symbols']` + `regime_wf/*_specialist_configs.json`). Divergencias 47 (lab `SYMBOLS` list) y 48 (CSVs/parquets/joblibs) son artefactos lab/legacy pendientes cleanup post-reciclaje.
- **Regímenes clasificables**: 3-8 clusters según GMM N priori cross-símbolo.
- **Orden de magnitud foundational**: 20.9M × ~30 × 45 × ~5 ≈ **1.4 × 10¹⁰ configuraciones**.

## Marco correcto

El propósito del proyecto NO es mejorar el rendimiento del sistema en abstracto. El sistema —la lógica SmartDiv replicada en Python con fidelidad bidireccional preservada— tiene edge promedio limitado en el régimen actual (~1.2 PF para configuración típica seleccionada del universo con fidelidad 1+2 preservadas). Eso es propiedad estructural del régimen, NO techo de lo identificable.

El propósito real es **identificar dentro del universo (~10¹⁰ configuraciones) las configuraciones específicas cuyo edge real es notablemente superior al promedio**. Por la magnitud del espacio, existen necesariamente. La cuestión NO es si existen sino si la metodología puede identificarlas honestamente sin confundirlas con configuraciones que parecen buenas por sobrestimación walk-forward, selection bias o overfitting al período de training.

## Implicaciones operacionales

Bajo este marco, todo el aparato metodológico toma su sentido completo:

- **Filtros de mesetas y robustez paramétrica** (extractor_gemas, ≥60% vecinos rentables): distinguen edge estructural de picos de ruido aislados.
- **M2 fix + W3 bootstrap + W4 thresholds**: corrigen mecanismos de sobrestimación walk-forward (M1 muestra fwd pequeña, M2 dilución pf_combined media ponderada).
- **Z_BTC archivado empíricamente** (Sub-fase A 2026-04-26): candidato architectural change refutado — la metodología no requería este factor.
- **Frame 3.A meta-redesign Opción C Hybrid balanced** (4 ejes: HMM CONDITIONAL γ.6 + cluster aggregation + cross-symbol concurrent + validation gates redesign): mejoras a la **capacidad de identificación dentro del universo**, NO intentos de mejorar el sistema en abstracto.

## Caveat honesto persistente

Methodology refinement máximo es condición **necesaria pero no suficiente**. Si la metodología identifica una configuración notable con edge real ≈2.0 PF, el bot operacional reproduce ese edge con fidelidad bidireccional preservada. Si la metodología no logra identificarlas —por constraints estructurales como cluster sparsity inherente detectados empíricamente Sub-Frame 3.A.1 successor ARCHIVED— el reciclaje produce specialists típicos del promedio aunque las configuraciones notables existan. Frame 3.A meta-redesign es la respuesta arquitectónica a esas constraints.

La pregunta operacionalmente relevante: **¿cuán bueno es el mejor edge real identificable por la metodología actual dentro del universo de candidatas?** Depende del aparato metodológico, del universo existente y de los regímenes presentes — no del sistema en abstracto ni del régimen en abstracto.

## Principio operativo verificación primary source

La verificación primary source contra el código y los datos reales es **prerequisito de cualquier afirmación numérica, framing o referencia cross-Sesiones**. La memoria persistente cross-conversaciones puede arrastrar valores desactualizados o framings mal formulados; la lectura primary source antes de propagar es disciplina foundational, no lección operacional opcional. Formalizado en §12 Lección 38 con aplicaciones cumulative documentadas.

Caso emblemático K.0.0 (2026-04-29): valores claimed pre-flight (23 bits / ~8M combos / 31 presets / 45 símbolos) vs empíricos (26 bits / 20.9M combos / mean 30.5 presets / 45 confirmado pero 47/48 en otras fuentes). Detección antes de propagar al bloque canónico previno error perpetuado cross-Sesiones.

## Sesiones futuras: lectura obligatoria antes de

- Re-interpretar el rendimiento ~1.2 PF del bot operacional.
- Proponer scope reformulations a Frame 3.A / 3.B / 3.C.
- Articular caveats sobre edge real estructural mercado.
- Citar cuantitativos del universo de candidatas sin re-verificar primary source.

## Origen documental

Conversación Ricardo 2026-04-29 sesión continuación post-Sub-fase J.0. Caveat mal formulado en respuestas previas ("edge real estructural marginal mercado potentially independiente methodology refinement") corregido por Ricardo articulando: "el problema es encontrar aquellas configuraciones que arrojan resultados notables, lo cual pasa porque lo simulado no sobrestime el rendimiento, y estas configuraciones existen por fuerza ya que tenemos millones de candidatas, y de ahí el filtro de mesetas, vecindad, etc.".

## Referencias

- **§0.0** CONTEXTO_PROYECTO_TRADING.md — formulación foundational completa con cuantificación verificada empíricamente.
- **§13.2** CONTEXTO_PROYECTO_TRADING.md — bloque "REFINAMIENTO CANÓNICO 2026-04-29 — Objetivo del proyecto correctamente formulado".
- **§12 Lección 38** CONTEXTO_PROYECTO_TRADING.md — verificación supuestos técnicos pre-implementación cross-fuentes primarias.
- Sub-Frame 3.A.1 successor ARCHIVED_EMPIRICAL §13.4 entrada 2026-04-29.
