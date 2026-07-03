# B3 — TIME-SERIES MOMENTUM DIARIO (lookback largo) — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Sandbox aislado, $0. Datos: `data_cache/*_1h.parquet` (45+ sym, BTC 2017→2026, **incluye bear 2022** → cubre parcialmente la laguna temporal del cierre).

## Hipótesis
Exp#1 refutó cruces a 1h donde fee×rotación domina; a **diario** con ~5-15 operaciones/año/símbolo el ratio señal/coste cambia un orden de magnitud. Es donde vive el TSMOM académico (Moskowitz-Ooi-Pedersen 2012; Liu-Tsyvinski 2021 en cripto). **Prior PARCIALMENTE EN CONTRA** pre-registrado: CS-MOM Curva A (tilt direccional) no batió al EW.

## Diseño
- Resample 1h→1d (close diario). Universo point-in-time (símbolo activo cuando tiene datos).
- Señal por símbolo en cada rebalanceo: `signal = +1 si retorno_trailing(L) > 0, si no FLAT` (**largo/flat**, dado el corto-veneno documentado B/CS-MOM). Retorno trailing solo con pasado (sin look-ahead).
- Cartera: peso vol-target (inverse vol realizada) sobre los símbolos en largo, normalizado a suma 1. Inercia entre rebalanceos.
- Rebalanceo semanal (5 días de trading). Costes: **0.10%/lado taker sobre el turnover** de pesos (idéntico esquema a CS-MOM). Sin funding (largo/flat; funding de largos es coste menor, medido negligible en A9 ~0.0023%/trade → se omite, declarado).

## Parámetros lógicos a priori (CONGELADOS)
- `L` (lookback señal) = **56 días (8 semanas)** PRIMARIO único. Robustez {28, 84}d SOLO si el base sobrevive.
- Rebalanceo = 5 días. Vol realizada para sizing = std de retornos diarios sobre 28 días.
- Ventana = máx. disponible por símbolo (point-in-time), full 2018-2026. Sub-períodos reportados por año.

## Métrica CARDINAL (a priori, sin pivote)
Sharpe NETO de la cartera TSMOM largo/flat, full, con CI block-bootstrap (bloques 5d). + Sortino/maxDD/Calmar/turnover.

## Benchmark
EW buy-and-hold (siempre largo todos los listados, reweight semanal a igual peso) sobre la MISMA ventana + buy-and-hold por símbolo (media). Es la comparación justa para una estrategia direccional largo/flat (el timing es la única diferencia vs holdear).

## Criterios de veredicto (CONGELADOS — "DIGNA" exige TODOS)
1. Sharpe_TSMOM_neto ≥ **1.00** (listón tradeable absoluto).
2. Sharpe_TSMOM > Sharpe_EW-buy&hold (el **timing añade valor** sobre holdear).
3. maxDD_TSMOM > maxDD_EW-buy&hold (**mejor protección** — la promesa del TSMOM largo/flat).
4. CI(Sharpe_TSMOM) excluye 0.
- Cualquiera que falle → **NO DIGNA**. Reporto además la diferencia de Sharpe TSMOM−EW.

## Riesgo honesto pre-registrado
La pata larga TSMOM ≈ beta larga cronometrada; el EW buy-and-hold es un listón brutal (Sharpe cripto 2023-24 fue alto). Decay post-2021 del TSMOM cripto documentado (crowding CTAs). Señales de tendencia a horizonte corto ya lean-negativo (Exp#1).

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa (cierra formalmente la rama time-series que CS-MOM dejó abierta). Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## VEREDICTO B3 (2026-07-02) — **NO DIGNA**
Ventana full 2017-08→2026-06 (3222 días, incluye bear 2022).
- Sharpe_TSMOM_neto = **0.749** < 1.00 → criterio 1 FALLA.
- Sharpe EW buy&hold = 0.779 → TSMOM **NO bate holdear** (diff −0.03) → criterio 2 FALLA.
- maxDD TSMOM −84.99% vs EW −87.57% → mejor por 2.6pp (criterio 3 pasa, pero **protección ilusoria**: un largo/flat que aún cae 85% no protege).
- CI(Sharpe) [0.131, 1.403] → excluye 0 (criterio 4 pasa) pero **incluye 1.0** (rentabilidad no establecida).
- Sub-períodos: 2022 −1.04 (vs EW −1.25), 2023 +2.33 (vs 2.11), 2024 +1.24 (vs 1.01), **2025 −1.36 (vs EW −0.76, PEOR)**.
- **VEREDICTO: NO DIGNA** (2/4 criterios). El timing NO añade valor sobre holdear, net de costes, sobre 8 años. Confirma y extiende el prior (CS-MOM Curva A no batió EW) a la rama time-series diaria de horizonte largo. **Cierra formalmente la rama time-series.** Nada que rescatar; robustez {28,84}d OMITIDA (base muerto).
