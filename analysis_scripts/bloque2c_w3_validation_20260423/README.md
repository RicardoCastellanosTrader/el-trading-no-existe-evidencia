# Bloque 2c Opción Q1 — W3 divergencia validation — 2026-04-23

Stress-test W3 flag vs CANDIDATO EXCLUSION sobre kernel histórico Binance Futures 3y.

## Contexto

Sesión 2026-04-23: 6 refutaciones previas por stress-test §12 L34 aplicado a hipótesis
internas. Opción D cualitativa (commit b8bfcc5) reportó patrón DIVERGENTE W3 flag vs
evidencia operacional cross-sesión. Opción Q1 cuantitativa investiga edge histórico.

## Resultado

**CASO VALIDA CUANTITATIVAMENTE**: 10/10 configs flagged (6 W3 + 4 CANDIDATO EXCLUSION)
con PF_3y_binance < 1.5. 0/10 con PF≥2.0. 60% PF<1.0 (edge neto perdido).

Ratio PF_WF/PF_3y = 0.10-0.82 — §12 L29 (walk-forward N_fwd inflation) validada
masivamente, no caso aislado.

## Archivos

- `bloque2c_targets.pkl`: pickle con 10 target configs (symbol, cluster, flag_type, config_id, preset, pf_WF, pf_fwd).
- `bloque2c_w3_kernel.py`: script kernel runs sobre Binance 3y parquets → results CSV.
- `bloque2c_w3_results.csv`: resultados 10 configs con PF_3y_binance, trades, wins, PnL.

## Dataset ejecución

- Binance Futures OHLCV 1h 3y (2023-04-24 → 2026-04-23) fetched via VPS Tokio (geo-blocking §12.24).
- 9 unique symbols: ONDO, LTC, GRT, TRX, BTC, MANA, APT, SAND, SEI.
- ONDO listed 2024-01-20 (~2.3y), SEI listed 2023-08-17 (~2.7y), resto 3y completos.

## Uso como referencia

Para replicar o extender análisis:

1. Fetch Binance 3y desde VPS (script: `/tmp/fetch_binance_w3_csv.py` — sesión 2026-04-23).
2. CSV → parquet conversion local (pyarrow required).
3. `python bloque2c_w3_kernel.py` ejecuta kernel Numba sobre cada target config.
4. Output CSV contiene PF_3y_binance per cluster.

## Prerequisitos

- Tier 0 I2 commit (`53fe73a`) — `_run_verify_test --data-path` disponible.
- Parquets Binance 3y en `binance_w3_data/` (regenerable desde VPS).
- `regime_wf/*_specialist_configs.json` productivos (source configs).

## Limitaciones scope

- Kernel output aggregate-only (sin per-trade side/entry_ts/reason_exit).
- H1 short/long, H_funding aligned/contrarian, H_strategy strategy-logic NO testeables
  en este scope — requieren Tier 0 I1 kernel modification (item §13.3 post-reciclaje).
- Cross-exchange Binance ≠ BingX: direccionalidad PF<1.5 vs ≥2.0 preservada por
  naturaleza estructural del edge; magnitudes absolutas pueden diferir modestamente.

## Referencias

- §13.4 Bloque 2c Opción Q1 2026-04-23 (esta entrada — veredicto completo).
- §13.4 Opción D cualitativa 2026-04-23 (commit b8bfcc5).
- §13.4 Bloque 2b coverage Binance Futures 2026-04-23.
- §13.4 Tier 0 I2 commit 53fe73a 2026-04-23.
- §13.3 Tier 0 I1 + Bloque 2c H1+H_funding+H_strategy post-reciclaje.
- §12 L29 (walk-forward N_fwd inflation — validada masivamente).
- §12 L34 (9-10 aplicaciones sesión 2026-04-23).
