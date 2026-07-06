# Datos: qué hay en el repo, qué no, y cómo regenerarlo todo

Política del repo: **los datos crudos no se redistribuyen** (fuente pública: <https://data.binance.vision> y la API pública de klines de Binance); se publican los scripts de descarga y los manifiestos de verificación. Excepción declarada: `data_cache/` (82 MB de parquets de velas 1h) SÍ está incluido como conveniencia para reproducir los experimentos sin descarga previa — su manifiesto es [`MANIFEST.sha256`](MANIFEST.sha256).

## 1. Velas 1h, 45 símbolos (`data_cache/*.parquet`) — INCLUIDO
- **Usado por:** E01, E03, E04, E05, E18 y todo el pipeline de laboratorio.
- **Regeneración:** `python download_full_history.py` (descarga) + `data_cache.py` (módulo de acceso/normalización). Fuente: klines públicos de Binance USDT-M.
- **Verificación:** `sha256sum -c` contra `datos/MANIFEST.sha256` (48 parquets; sha256 + bytes + ruta).
- Nota: `data_cache/stress_test/` contiene CSVs 1h de FTTUSDT (activo deslistado) usados para tests de robustez del feed.

## 2. aggTrades tick, BTC+ETH, 2 años (~4.4 GB) — NO INCLUIDO
- **Usado por:** E06 (MFE) y E15 (B8).
- **Regeneración:** los scripts de `mfe_sandbox/` (`sandbox_mfe.py`; ver cabecera) descargan los zips mensuales/diarios de aggTrades de data.binance.vision y construyen el dataset de cascadas. El funding (mensual, 8h) se descarga de la misma fuente.
- **Hallazgo de fuente primaria (declarado en el pre-registro de E06):** el stream `forceOrder` (liquidaciones) NO existe en el histórico público — solo en vivo. La firma de cascada se define por velocidad+volumen; es una limitación de diseño declarada, no un descuido.

## 3. Klines 12h + funding, universo point-in-time (~9 MB) — NO INCLUIDO
- **Usado por:** E07 (CS-MOM) y E08–E14 (harness cross-sectional).
- **Regeneración:** `cs_mom_sandbox/cs_mom.py` descarga y construye el universo. Detalles point-in-time que importan para reproducir: universo 35→45 símbolos según fecha de listado, stitch de renombrados **MATIC→POL** y **RNDR→RENDER**, **SHIB = 1000SHIBUSDT**. El sesgo de supervivencia restante se asume y se declara como techo optimista en los veredictos.
- E14 (open interest) usa además las métricas OI públicas de data.binance.vision (~150 MB, no incluidas; el runner `cierre_definitivo_20260702/run_B7.py` documenta la descarga).

## 4. Datos independientes W3 (`binance_w3_data/`) — NO INCLUIDO (no tracked)
- **Usado por:** E02/E16 como ancla INDEPENDIENTE (9 símbolos) — es el dataset que produce el ρ −0.0545. Regenerable con los mismos scripts de descarga (ventana distinta de la de data_cache; la independencia es el punto).

## 5. Resultados (SÍ incluidos)
Los `results_*.json` / `*.csv` pequeños de cada experimento están en sus rutas (ver README de cada E) y son la base de verificación directa. `regime_wf/` (63 MB de CSVs de specialists con métricas walk-forward, 138.000 filas) y `output/` (presets) son RESULTADOS del pipeline, no datos crudos, y se publican para auditoría.

## Verificación rápida
```bash
# manifiesto de data_cache
cd datos && python -c "
import hashlib,sys
for line in open('MANIFEST.sha256'):
    if line.startswith('#'): continue
    h,b,p=line.split(maxsplit=2); p=p.strip()
    d=hashlib.sha256(open('../'+p,'rb').read()).hexdigest()
    assert d==h, p
print('OK')"
```
