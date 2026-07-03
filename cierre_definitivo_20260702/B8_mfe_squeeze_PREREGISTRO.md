# B8 — MFE DIRECCIÓN SQUEEZE (cascadas alcistas) — PRE-REGISTRO CONGELADO

**Congelado:** 2026-07-02, ANTES de resultados. Sandbox `mfe_sandbox/` (pipeline existente). Datos: re-descarga aggTrades BTC+ETH 2023-2024 (~37GB transfer, pico disco <2GB, cleanup por-día Caveat #13). $0.

## Hipótesis
MFE §6.4 dejó explícitamente FUERA la dirección squeeze (cascadas ALCISTAS = liquidación de cortos) — nunca corrida. Firma espejo: subida ≥0.3%/15s + volumen COMPRADOR z≥3.0 (el grid original solo guardó sell_vol → se reconstruye con buy_vol). Entrada: exhaustión CORTO (1er seg tras disparo con ret15≤0, máx 60s).

## Falsador (idéntico rigor a MFE, con la LECCIÓN de la auditoría)
- Slippage worst-3s para CORTO = entrada al **precio MÁS BAJO** de los siguientes 3s (low3s). Stop +2% (MAE de un corto = el precio sube). FEE 0.20% RT. PnL corto = entry/exit − 1 − fee.
- **CONTROL CON SLIPPAGE MATCHED (lección auditoría A5):** control estratificado por decil de volatilidad (bstd) de las entradas-cascada, y medido con el MISMO mecanismo worst-3s (low3s) → el diferencial de slippage NO puede fabricar el resultado. CI cluster-8h.

## Métrica CARDINAL (a priori, CONJUNTA, SIN pivote — lección MFE)
**AMBAS pre-registradas conjuntas:** (1) media neta por trade Y (2) tasa de supervivencia, con CI cluster-8h. NO se pivota a una si la otra falla.

## Criterio de veredicto (CONGELADO)
- **"DIGNO"** iff: media neta > 0 con CI cluster-8h que excluye 0 **Y** gap de supervivencia cascada>control con CI que excluye 0 (matched por vol). AMBAS.
- Si media neta ≤ 0 (como el lado largo) → **MUERE** (el stack de costes que mató el long lo paga el short igual).

## Parámetros a priori (CONGELADOS, heredados de MFE)
DROP_PCT 0.003, VOL_Z 3.0, VEL_WIN 15s, BASE_WIN 3600s, COOLDOWN 300s, MAX_WAIT 60s, SLIP_WIN 3s, FEE_RT 0.20%, HARD_STOP +2% (short), HORIZONS 60/180/300s, N_CTRL 10/casc, SEED 20260629. Smoke 1 mes (2024-03) → run 2 años si smoke sano.

## Riesgo honesto pre-registrado (prior MODESTO)
La muerte del lado long fue por el stack de costes (−0.2%/trade ≈ fees+slippage) que el short paga IGUAL. Los cortos liquidados compran contra un libro típicamente más fino arriba (asimetría posible) y el régimen de funding en squeezes es opuesto — pero el prior es que muere por costes. Se corre solo porque el coste marginal es bajo y cierra la mitad no medida del dominio.

## Expectativa CALIBRADA (CONGELADA)
Modesto y limitado por capital. Completar el mapa (mitad no medida de MFE). Ningún resultado reabre la búsqueda.

---
*VEREDICTO abajo tras el run.*

---
## SMOKE B8 (2024-03, validación del mirror) — 2026-07-02
Mirror validado (detecta cascadas alcistas, control VOL-MATCHED, CI cluster-8h). Señal temprana:
- BTC (74 casc): net_3m casc **−0.0026** vs ctrl −0.0022 (diff −0.0004, CI[−0.0013,+0.0004]) → **MUERE**. Gap supervivencia 3m 25.7% vs 12.6% (CI excluye 0) = señal microestructural REAL (con control vol-matched → NO artefacto slippage), pero net negativo.
- ETH (101 casc): net_3m casc **−0.0034** vs ctrl −0.0022 (diff −0.0012, CI[−0.0022,−0.0002]) → **MUERE** (casc PEOR que control). Gap supervivencia 21.8% vs 11.2%.
- **Patrón idéntico al lado largo MFE:** gap de supervivencia real y positivo, anulado por perdedores mayores → expectativa neta negativa. El stack de costes que mató el long lo paga el short igual (riesgo pre-registrado confirmado). Full 2-años en curso para el veredicto con N pre-registrado.

---
## VEREDICTO B8 FULL (2023-2024, 2026-07-02) — **MUERE (BTC+ETH)**
Run completo 2 años (BTC 45min/12GB, ETH 44min/10GB), control VOL-MATCHED, CI cluster-8h.
- BTC (1378 casc / 13780 ctrl): net_3m casc **−0.00250** vs ctrl −0.00210 → diff **−0.00039, CI[−0.00062,−0.00017] EXCLUYE 0 (negativo)**. Supervivencia gap positivo pero net negativo.
- ETH (1757 casc / 17570 ctrl): net_3m casc **−0.00251** vs ctrl −0.00208 → diff **−0.00043, CI[−0.00064,−0.00023] EXCLUYE 0 (negativo)**.
- **VEREDICTO: MUERE (ambos).** Criterio conjunto (media neta>0 con CI>0 Y gap supervivencia>0): la media neta es NEGATIVA → falla. Y con el control vol-matched (confound de slippage eliminado, lección auditoría), la cascada es **significativamente PEOR que una entrada aleatoria vol-matched** — negativa selección, no solo coste. Idéntico al lado largo: el stack de costes (~−0.25%/trade) mata el short. La mitad no medida de MFE queda cerrada NEGATIVA. Prior pre-registrado (MODESTO→muere por costes) confirmado.
