# B7 — OPEN INTEREST / POSITIONING — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Datos NUEVOS: dataset `metrics` de data.binance.vision (`futures/um/daily/metrics/{sym}/{sym}-metrics-{date}.zip`, 5-min, `sum_open_interest`). Cobertura verificada (200 OK 2021-2024 BTC+ONDO, §12 L38). $0. Sandbox aislado.

## Hipótesis
El OI mide POSICIONAMIENTO real, no precio. Dos usos pre-registrados:
- **(a) Condicionador del gap MFE:** ¿la purga de apalancamiento fue completa? (ΔOI en la cascada) — el condicionador que la firma precio/volumen de MFE solo aproximaba.
- **(b) Predictor cross-sectional standalone:** OI subiendo = acumulación crowded → fragilidad. **Factor primario = −(ΔOI over lookback)** → LARGO los de OI cayendo (desapalancados, menos crowded), CORTO los de OI subiendo (crowded), market-neutral. Dirección de fragilidad congelada; la inversa solo se reporta descriptiva.

## Parámetros a priori (CONGELADOS)
- Universo = 44 sym cs_mom, ventana **2023-2024** (comparable a B1-B4). OI agregado a 12h (último OI del bar).
- `lookback_OI` = 6 barras (3 días). ΔOI = (OI_t − OI_{t−6})/OI_{t−6}. Solo pasado.
- Resto (rebal 10, quintiles 20/33, vol-target, costes, funding bilateral, corto pesimista, warmup 56): idéntico a B1-B4.

## Métrica CARDINAL (a priori, sin pivote)
(b) Sharpe NETO Curva C (neutral, fragilidad ΔOI), full 2023-24, CI block-bootstrap. Criterios = los 5 de B1.
(a) Gap de supervivencia MFE condicionado por decil de ΔOI-flush en la cascada (BTC+ETH), CI cluster-8h; **con control matched en slippage** (lección auditoría).

## Criterios de veredicto (CONGELADOS)
(b) "DIGNA" iff los 5 de B1 (neutral gate-arreglado + Sharpe≥1 + CI>0 + maxDD>−25 + sobrevive 2023 Y 2024).
(a) "CONDICIONADOR ÚTIL" iff el gap de supervivencia crece monótono con el ΔOI-flush Y la expectativa neta del decil-alto supera breakeven con ejecución justa (si no → el OI no rescata MFE).

## Riesgo honesto pre-registrado
Rescate condicional post-hoc de una línea muerta (MFE) = el sesgo que el proyecto aprendió a evitar → el condicionador (a) se pre-registra ANTES de re-mirar. La granularidad 5-min puede ser gruesa para cascadas de segundos. Prior negativo (B1-B4 cross-sectional todas muertas; el slippage pesimista de MFE persiste).

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa (eje posicionamiento, nunca descargado). Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## VEREDICTO B7 (2026-07-02) — **NO DIGNA**
OI descargado 45/45 sym (32895 ficheros metrics), ventana 2023-24, factor fragilidad −ΔOI(6 barras).
- **(b) cross-sectional standalone (pata decisiva):** Sharpe C = **−0.419**, CI[−1.85,1.08] incluye 0; neutral (β_EW −0.001, β_BTC 0.05); maxDD −46%; no sobrevive (2023 −0.001, 2024 −0.727); turnover 2.8. A_long 0.93 / B_short −1.12. **NO DIGNA.** Otro factor cross-sectional muerto (consistente con B1-B4).
- **(a) condicionador del gap MFE:** NO perseguida deliberadamente. Razón honesta (consistente con el ethos anti-rescate del propio pre-registro): es un rescate condicional de una línea que la auditoría halló MÁS muerta (gap inflado ~3-4× por confound de vol, bruto ≈+1bp/trade), y la pata decisiva standalone (b) ya es NO DIGNA. Computable (OI 5-min BTC+ETH + join a edge_cascades) si alguna vez se quisiera, pero no cambiaría un veredicto ya negativo. Documentada como cerrada por decisión, no por omisión.
- **VEREDICTO B7: NO DIGNA.** El posicionamiento (OI) como fuente de edge cross-sectional no bate breakeven.
