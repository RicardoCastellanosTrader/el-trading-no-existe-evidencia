# B5 — LEAD-LAG BTC→ALTS (horario) — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Datos `data_cache/*_1h.parquet` (BTC + 44 alts, 2018-2026). $0, sandbox aislado.

## Hipótesis
Los shocks de BTC se propagan a las alts menos líquidas con retraso (atención/liquidez escalonadas; Hou 2007; papers cripto 2018-2021 con BTC liderando alts minutos-horas). ¿El retorno de BTC en t predice el cross-section de alts en t+k?

## Diseño (medición primero, cartera solo si hay señal)
- **Estadístico primario por lag k:** media sobre las 44 alts de `corr(BTC_ret_t, alt_i_ret_{t+k})` (BTC contemporáneo vs alt futura a lag k), sobre todo el histórico solapado. Control de autocorrelación propia: se reporta también el parcial controlando `alt_i_ret_t` (regresión `alt_{t+k} ~ BTC_t + alt_t`, coef de BTC pooled).
- **CI:** moving-block bootstrap sobre el tiempo (bloque 24 barras = 1 día, respeta co-movimiento cross-alt y serial).
- **Multiplicidad:** FDR-Benjamini-Hochberg sobre k ∈ **{1, 2, 4, 8, 12}h** (los 5 declarados a priori; q=0.10).

## Criterios de veredicto (CONGELADOS)
- **"SEÑAL"** si algún k tiene coef/corr **FDR-significativo Y |magnitud| ≥ 0.03** (mínimo económico; por debajo no es tradeable a 0.10% RT). 
- Si SEÑAL → construir la cartera mínima (largo las alts tras un up-move de BTC en t, hold k horas, costes 0.10% RT + slippage) y juzgar con criterios estándar: Sharpe_neto ≥ 1.0 Y CI(Sharpe) excluye 0.
- Si NINGÚN k sobrevive FDR con magnitud ≥ 0.03 → **CERRADO** (sin predictibilidad tradeable). 

## Riesgo honesto pre-registrado
Evidencia cripto de lead-lag mayormente pre-2022; en 2024-26 los MMs arbitran el co-movimiento en segundos → a cierre de hora lo esperable es ~nada. Las alts más ilíquidas (donde podría quedar residuo) son las de peor slippage real → el 0.10% es optimista ahí. Prior de muerte alto; el valor es cerrar la pregunta.

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa. Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## VEREDICTO B5 (2026-07-02) — **CERRADO (sin predictibilidad tradeable)**
Ventana 2017-08→2026-06, 44 alts, ew pooled, moving-block bootstrap (bloque 24h, 1000 reps), FDR-BH q=0.10.
- k=1h: mean_corr **−0.0161** [−0.025,−0.007] FDR-sig (p=0.002) pero |0.016| < 0.03 → NO señal. **Negativo** (leve reversión, no continuación).
- k=2h: **−0.0187** [−0.027,−0.011] FDR-sig pero < 0.03. Negativo.
- k=4h/8h/12h: ~0, no significativos.
- **VEREDICTO: CERRADO.** No hay predictibilidad direccional BTC→alts tradeable a horizonte horario; lo que sobrevive FDR es una micro-reversión (signo opuesto a la hipótesis) de magnitud ≪ coste. Confirma el prior (co-movimiento arbitrado en segundos). Versión sub-1h no perseguida (base horario ya CERRADO).
