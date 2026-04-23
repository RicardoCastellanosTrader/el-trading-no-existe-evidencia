# H1 Stress Test — 2026-04-23

Scripts ad-hoc de la sesión 2026-04-23 A.1 deep-dive + Fase 2 + Fase 3.
Primera aplicación empírica de §12 Lección 34 (validación multi-segmento
de hipótesis emergentes N<50).

## Contexto

A.1 N=26 post-v2.4.4 generó 3 hipótesis emergentes (H1 short/long 12:1,
H_strategy exits 3.4×, H_new_3 residual contrarian 24×). Stress-test
cross-segmento (S1-S4) + cross-régimen (BTC GMM) refutó las 3 como
artefactos S4-específicos. Los scripts capturan el protocolo ejecutable.

## Archivos

- `h1_phase2.py`: H1 (short/long asimetría) validación multi-régimen +
  multi-segmento sobre N=98. Merge trade_history.csv +
  regime_models/BTC_regime.joblib + deploy_boundaries.json. OLS
  side + BTC_delta_pct. Veredicto Caso E2.
- `h1_phase3.py`: H_strategy (strategy-logic exits vs estructurales)
  cross-segmento N=98. Welch + MW + Cohen d per segmento + per reason.
  Incluye W3-flagged cross-check scaffold (0 trades flagged en dataset
  actual). Veredicto Caso F3.
- `h1_phase3b.py`: H_funding (aligned/contrarian) + H_new_3 (pattern
  residual) sobre N=98 (N=49 funding cache-limited). Comparación triple
  Bloque 2 N=50 / A.1 N=26 / Fase 3 N=49. Spearman correlation residual
  vs n_bars_contrarian. Veredictos Caso G2 atenuado + M2.

## Uso como referencia

Para replicar el patrón stress-test sobre futuras hipótesis emergentes:

1. Identificar ventana de origen de la hipótesis (típicamente N<50 S4
   homogéneo post-fixes recientes).
2. Expandir a dataset completo N≥80 con entry_ts recuperable.
3. Segmentar por deploy boundaries (deploy_boundaries.json).
4. Análisis cross-segmento + cross-régimen con tests estadísticos
   apropiados (Welch + MW + Cohen d; OLS si ≥2 covariables).
5. Aplicar criterio L34 (§12): persiste ≥2 segmentos N≥20 sin
   inversión → elevar §13.3. Si no → refutar como artefacto.

## Prerequisitos ejecución

- `trade_history.csv` snapshot desde VPS (scp).
- `logs/engine.log*` desde VPS (scp).
- Analyzer `analyze_performance_attribution.py` ejecutado previamente
  con `--since 2026-04-01T00:00:00Z` para producir
  `attribution_per_trade_<TS>.csv`.
- `data_cache/BTCUSDT_1h_fresh.parquet` (2100+ bars para warmup
  LOOKBACK_LONG=1000 de `regime_features.py`).
- `.funding_cache/` sincronizada desde VPS (geo-bloqueo España §12.24).
- `regime_models/BTC_regime.joblib` (GMM productivo k=3).
- `deploy_boundaries.json` (boundaries arquitectónicas).

## Limitaciones conocidas

- Funding cache arranca 2026-04-15 (gap vs origen dataset 2026-04-13).
  Refresh cache a origen si stress-test funding necesario — ver §13.3
  [MEJORA] cache funding extender 2026-04-23.
- BTC parquet local puede requerir refresh si stress-test cubre ventanas
  antiguas; verificar cobertura con `len(parquet)` antes de ejecutar.
- Scripts usan paths hardcoded absolutos Windows (`C:\Users\rixip\...`).
  Parametrizar si se reusan en otro entorno.
- Entry_ts recuperability ≤100% por bug histórico pre-v2.4.5; scripts
  usan fallback `exit−1h` para trades con `entry_timestamp_ms=0`.

## Referencias

- §12 Lección 34 (caso origen sesión 2026-04-23).
- §13.4 entrada "Sesión 2026-04-23 — A.1 deep-dive Criterio B + 3
  refutaciones cross-segmento + L34".
- §13.3 updates v2.6-inv + v2.6-exit (aplicación del protocolo).
- §13.3 [MEJORA] cache funding context extender a origen (prerequisito
  para S1 retrospectivo en stress-tests futuros).
