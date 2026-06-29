# Logs históricos de operación en vivo — VPS Tokio (registro único, NO regenerable)

Copiados el **2026-06-29** desde el VPS de producción antes del cierre ordenado de
infraestructura (detención de instancias EC2). Este es el **registro irreemplazable**
de la operación real del bot: trades ejecutados reales en BingX, no reproducibles.

## Procedencia
- **Instancia origen:** `INSTANCE_ID_TOKIO_REDACTADO` (`trading-bot-tokyo`, ap-northeast-1)
- **Ruta origen:** `/home/trader/combolab/`
- **Método:** scp vía SSH, instancia arrancada brevemente solo-lectura y vuelta a `stopped`.
- **Integridad verificada:** MD5 `trade_history.csv` = `0f0e5e489a6b7a2254281a78c0c5abb8`
  (MATCH remoto↔local); 38/38 archivos de log (MATCH).

## Contenido
- `trade_history/trade_history.csv` — **736 trades reales ejecutados** (header + 736 filas),
  histórico completo de la operación en vivo hasta 2026-06-21. Bot v2.4.5 → v2.8.1.
- `trade_history/trade_history*.bak*` / `*.csv.bak-*` — backups de provenance de los fixes
  de integridad/migración/backfill (auditoría forense 2026-06-12, doge-backfill, etc.).
- `trade_history/trade_history_funding_obs.csv` — observabilidad de funding.
- `logs/engine.log` + `engine.log.N.gz` (30 días rotados) — registro operacional del engine
  (señales, fills, decisiones, reconciliaciones). Los registros tipo SIGNALS_RAW/EXECUTED
  viven embebidos aquí (no había CSV de señales separado).
- `logs/engine_error.log*` — errores del engine.

## Qué NO se copió (regenerable / ya versionado en el repo)
- `regime_wf/`, `regime_models/` (specialists + GMM): generados por el pipeline, en git.
- `output/production/` presets: regenerables.
- `.funding_cache/`: caché regenerable desde el exchange.
- Snapshots `*.bak-grupoN-*` de deployment: estado derivado.

## Límite cardinal
Estos son logs de cómputo/operación. **No contienen claves ni tocan fondos.** Los fondos
están en Kraken (MiCA), gestión de Ricardo, fuera del alcance de esta infraestructura.
