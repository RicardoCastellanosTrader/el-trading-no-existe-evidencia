# C3 — Exp#2 ablación deepest/shallowest/random — VEREDICTO (2026-07-02)
Config primaria (0.05,0.75,10), 45 sym, misma banda/detector, solo cambia el pick del bloque:
- deepest (original) pf_all_median = **0.8002** (reproduce el Exp#2 congelado EXACTO → harness fiel)
- shallowest = 0.8109 | random-en-banda = 0.8099
- Los tres ≈ 0.80-0.81 (Δ<0.011), TODOS bajo el floor placebo 0.9891.
**VEREDICTO: REGLA CAUSAL SIN SEÑAL.** "Bloque más profundo = pool de liquidez mayor" NO porta señal — shallowest y random dan el mismo PF que deepest. Es geometría de banda, no profundidad-liquidez. El negativo de Exp#2 es ROBUSTO a la regla de selección del bloque, y la dimensión causal "profundidad" queda aislada e INERTE (cierra el "(b) algo del criterio no capturado" para el eje profundidad).
