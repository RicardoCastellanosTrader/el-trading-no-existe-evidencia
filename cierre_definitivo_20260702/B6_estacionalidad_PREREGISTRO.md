# B6 — ESTACIONALIDAD RELOJ / FUNDING-CLOCK — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Datos `data_cache/*_1h.parquet` (timestamp UTC exacto, 45 sym, 2017-2026). $0.
**REGLA DURA:** solo se corre CON FDR pre-registrado sobre el conjunto COMPLETO de hipótesis declarado a priori. Sin FDR sería data-mining y NO se corre.

## Hipótesis
Anomalías de calendario cripto (sesiones US/Asia; efecto fin de semana; drift alrededor del cobro de funding 00/08/16 UTC — el perp tiende hacia el índice antes del fixing). Eje ortogonal: ninguna de las 7 líneas condiciona por reloj.

## Conjunto COMPLETO de hipótesis declarado a priori (para FDR-BH, q=0.10)
- 24 buckets hora-del-día UTC (retorno horario medio pooled cross-símbolo vs 0).
- 7 buckets día-de-semana (retorno diario medio pooled vs 0).
- 6 buckets funding-clock: las 3 horas de funding {0,8,16} UTC y las 3 horas previas {23,7,15} (ventana pre-fixing).
- **Total = 37 buckets.** Primarias con hipótesis causal a priori: sesión US (13-21 UTC), fin de semana (sáb+dom), pre-funding (23,7,15). El resto = descriptivas dentro del mismo FDR.

## Estadístico
Por bucket: media del retorno pooled cross-símbolo, CI + p por moving-block bootstrap (bloque 24h, respeta co-movimiento). FDR-BH sobre los 37 p-values, q=0.10.

## Criterios de veredicto (CONGELADOS)
- **"SEÑAL TRADEABLE"** iff algún bucket sobrevive FDR **Y** |retorno medio del bucket| ≥ **10 bps** (coste RT taker) → construir overlay mínimo y juzgar con Sharpe_neto≥1 + CI>0.
- **"EFECTO REAL NO TRADEABLE"** iff algún bucket sobrevive FDR pero < 10 bps → documentar como valor de TIMING DE EJECUCIÓN (no estrategia standalone), sin claim de tradeable.
- **"CERRADO"** iff ningún bucket sobrevive FDR.

## Riesgo honesto pre-registrado
Los tamaños documentados son bps/hora contra ~10bps RT → como estrategia standalone casi seguro muerta; el resultado más probable es "real pero no tradeable". Multiplicidad = el riesgo dominante, mitigado por FDR sobre el conjunto completo declarado.

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa (eje reloj, nunca medido). Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## VEREDICTO B6 (2026-07-02) — **EFECTO REAL NO TRADEABLE**
Ventana 2017-08→2026-06, 77188 horas, 44 sym, ew pooled horario, 37 buckets, FDR-BH q=0.10.
- **Sobreviven FDR (4):** hour_21 (UTC), hour_22, dow_4 (viernes), dow_5 (sábado) — efectos de calendario REALES (cierre US ~16-17 ET; fin de semana).
- **Máximo |efecto| = 5.97 bps** < 10 bps (coste RT taker) → **NINGÚN bucket es tradeable como estrategia standalone**.
- **VEREDICTO: EFECTO REAL NO TRADEABLE** — valor solo como TIMING DE EJECUCIÓN (ejecutar rebalanceos de otra estrategia en las horas favorables), NO como estrategia autónoma. Outcome pre-registrado ("real pero no tradeable") confirmado. Eje reloj CERRADO como fuente de edge; anotado como overlay de timing para eventual uso.
