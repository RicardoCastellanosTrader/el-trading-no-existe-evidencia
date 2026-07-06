# E06 — MFE: exhaustión post-cascada de liquidaciones (microestructura)

**Hipótesis:** tras una cascada de liquidaciones (detectada por velocidad+volumen en tick data), el precio exhibe exhaustión explotable en segundos-minutos.
**Nombre popular:** "liquidation hunting / cazar cascadas de liquidaciones / stop hunts".

## Pre-registro — Nivel B (documental, commit conjunto)
- `mfe_sandbox/MFE_FASE_EDGE_PREREGISTRO.md` (§13 = veredicto añadido al cierre) — sandbox completo commiteado en `3b57151f` (2026-06-29). Ver [taxonomía](../../prerregistros/README.md).
- Hallazgo de fuente primaria declarado en el prereg: el stream `forceOrder` de Binance **no existe histórico** en data.binance.vision — la firma cascada se define por velocidad+volumen sobre aggTrades.

## Código y datos
- `mfe_sandbox/sandbox_mfe.py` (construcción del dataset) + `run_edge.py` (run del edge con falsador duro: peor-precio-3s, stop −2%, control simétrico estratificado, CI cluster-8h) + `smoke_calibration.py`.
- Datos: aggTrades tick BTC+ETH 2 años (~4.4 GB, NO incluidos; regenerables de data.binance.vision — [`REGENERAR.md`](../../datos/REGENERAR.md)) + funding mensual.

## Resultados
- `mfe_sandbox/results/edge_summary.json` (+ `smoke_summary_2024-03.json`, ejemplo por-símbolo).

## Veredicto
**NEGATIVO ROBUSTO bajo falsador duro.** Expectativa neta ≈ **−0.2%/trade** — igual o peor que entrar aleatoriamente con los mismos costes. La señal microestructural EXISTE (gap de supervivencia post-cascada real) pero los perdedores mayores anulan el edge en la media, y el funding NO estratifica el resultado (celda aislada — "no confirmado", corrección A5).
**Matiz (A5, obligatorio):** el gap bruto reportado originalmente (23% vs 3%) estaba **inflado ~3-4× por el confound de volatilidad**; la versión corregida es ~+6-8 pp ≈ **+1 bp bruto por trade** [estimación documental de la meta-auditoría]. La versión VERIFICABLE con control vol-matched es el retest [E15](../E15_mfe_squeeze/README.md): surv diff +13.2/+13.3 pp con neto negativo (CI excluye 0). "Peor que aleatorio" tampoco es exacto: el control no tenía el slippage matched (corregido en E15).
