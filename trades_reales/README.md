# Trades reales — 736 fills con dinero real (VPS Tokio, BingX perps)

**Archivo:** [`../logs_historicos_vps/trade_history/trade_history.csv`](../logs_historicos_vps/trade_history/trade_history.csv) — **736 operaciones** (737 líneas con cabecera), periodo **2026-04-13 → 2026-06-21**, 43 símbolos, ejecutadas por el bot en producción con cuenta real.

## Qué prueban
1. **Que el sistema medido es el sistema que operó.** Certificación de fidelidad señal-a-señal brain↔kernel (W1500): match-rate **98.24–100% por símbolo** (`cert_fidelity_gate_W1500.json`, p.ej. BTC 100% sobre 250 señales). Auditoría temprana contra fills del exchange: 10/11 = **91%**, con su tamaño de muestra declarado (**N=11, CI [62%, 98%]**).
2. **El resultado económico que los veredictos predicen.** PnL bruto registrado (mark-based, sin comisión): **+3.28 USDT** en 4.962 USDT de notional rotado; comisión estimada a 0.10% round-trip ≈ **−4.96 USDT** → neto ≈ **−1.7 USDT**. La formulación oficial del proyecto: *"no gané: los costes se llevaron el PnL"* — el precio dio ≈0 y las comisiones decidieron el signo, que es exactamente lo que el arco experimental (E01–E18) predice para esta familia a esta escala.

## Qué NO prueban
- No son una muestra estadísticamente potente por sí mismos (10 semanas, sizing mínimo): la evidencia del "sin edge" son los experimentos; esto es la verificación de que la ejecución real no esconde un resultado distinto.
- El capital inicial exacto no tiene artefacto en el repo (documental: ~296 USDT; balance final 288.71 USDT al cierre MiCA 2026-06-21).

## Columnas (se publican íntegras)
`timestamp, symbol, side, entry_price, exit_price, size_usdt, pnl_pct, pnl_usdt, funding_paid, reason_exit, flag, entry_timestamp_ms, cluster`

- **No contienen** order IDs, account IDs ni ningún identificador de cuenta del exchange (verificado columna a columna en la auditoría de publicabilidad).
- Los **importes absolutos en USDT se conservan deliberadamente**: la escala retail (~300 USDT) es parte de la evidencia de la tesis, no un dato sensible.
- `pnl_pct`/`pnl_usdt` son BRUTOS (mark-based, sin comisión ni funding no realizado) — verificado contra 736 fills reales en la corrección A9 de la meta-auditoría; `funding_paid` registra el funding realizado (~0.0023%/trade de media, negligible).

## Integridad y provenance
- Identificador canónico (independiente de plataforma): **blob git `f2da10ba117062011b7e1df84dc91b4372fe2363`** — verificable con `git rev-parse HEAD:logs_historicos_vps/trade_history/trade_history.csv`.
- SHA256 del contenido commiteado: `3862ca05fba90265eb597cd71e6b5fb2ea1b778bc9bd9a36ef2a4f47947dde72` (`git show HEAD:logs_historicos_vps/trade_history/trade_history.csv | sha256sum`).
- Nota sobre MD5: el MD5 del archivo en disco depende de la conversión de fin de línea del checkout (`core.autocrlf`); usa el blob/SHA256 de arriba, no el MD5 del working tree. El manifiesto MD5 del snapshot del VPS (`audit_forense_gap_20260612/vps_md5_manifest_20260612.txt`) corresponde al estado del 2026-06-12, cuando el archivo tenía menos filas (siguió creciendo hasta el 2026-06-21).
- Backups de provenance con las etapas intermedias del archivo: `logs_historicos_vps/trade_history/trade_history.bak-*.csv`.
