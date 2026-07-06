# E18 — C3: ablación del order block (retest de blindaje de E05)

**Pregunta:** en el criterio real de [E05](../E05_order_blocks/README.md), la regla causal central ("el bloque MÁS PROFUNDO = pool de liquidez mayor") ¿aporta algo? Ablación: sustituirla por "el más superficial" y por elección aleatoria, todo lo demás igual.

## Pre-registro — Nivel C (Lista de Cierre, commit único `65b99c81`, 2026-07-03)
- `cierre_definitivo_20260702/B_C3_note.md`. Ver [taxonomía](../../prerregistros/README.md).

## Código, datos, resultados
- Runner: `cierre_definitivo_20260702/run_C3.py` reusando `analysis_scripts/atribucion_componentes_20260626/ob_detector_v3.py`; datos: velas 1h `data_cache/`; resultados: `results_C3.json`.

## Veredicto
**La regla causal es INERTE.** deepest **0.8002** ≈ shallowest **0.8109** ≈ random **0.8099** — las tres variantes son indistinguibles entre sí y todas quedan bajo el floor placebo (0.9891). La pieza del criterio que portaba la hipótesis de liquidez no mueve el resultado en absoluto: lo que queda es la geometría del setup, y la geometría no bate al ruido.
