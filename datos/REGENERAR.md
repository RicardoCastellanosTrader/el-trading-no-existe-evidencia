# Datos: qué hay en el repo, qué no, y cómo regenerarlo todo

Política del repo: **los datos crudos no se redistribuyen** (fuentes públicas: la API pública de klines de Binance, mercado al contado, para las velas 1h; y <https://data.binance.vision>, perpetuos USDT-M, para los datos de 12h/tick/OI); se publican los scripts de descarga y los manifiestos de verificación. Excepción declarada: `data_cache/` (82 MB de parquets de velas 1h) SÍ está incluido como conveniencia para reproducir los experimentos sin descarga previa — su manifiesto es [`MANIFEST.sha256`](MANIFEST.sha256).

## 1. Velas 1h, 45 símbolos (`data_cache/*.parquet`) — INCLUIDO
- **Usado por:** la búsqueda principal y todo el pipeline de laboratorio; E01, E03, E04, E05, E10 (`run_B3.py` agrega 1h → diario), E12, E13, E16 (más `binance_w3_data`, §4), E17 (sobre los trades sellados del run Nivel 3) y E18. E02 trabaja sobre los resultados del pipeline (`regime_wf/`) y `binance_w3_data`. *(v1.0.1: lista corregida contra la cabecera de cada runner.)*
- **Regeneración:** `python download_full_history.py` (descarga) + `data_cache.py` (módulo de acceso/normalización). Fuente: velas 1h del **mercado al contado** de Binance (`ccxt.binance(...)` con el mercado por defecto; la caché empieza en 2017, antes de que existieran los perpetuos USDT-M de Binance). *(v1.0.1: la v1.0.0 decía «Binance USDT-M»; el código descarga contado.)*
- **Verificación:** `sha256sum -c` contra `datos/MANIFEST.sha256` (48 parquets; sha256 + bytes + ruta).
- Nota: `data_cache/stress_test/` contiene CSVs 1h de FTTUSDT (activo deslistado) usados para tests de robustez del feed.

## 2. aggTrades tick, BTC+ETH, 2 años (~4.4 GB) — NO INCLUIDO
- **Usado por:** E06 (MFE) y E15 (B8).
- **Regeneración:** los scripts de `mfe_sandbox/` (`sandbox_mfe.py`; ver cabecera) descargan los zips mensuales/diarios de aggTrades de data.binance.vision y construyen el dataset de cascadas. El funding (mensual, 8h) se descarga de la misma fuente.
- **Hallazgo de fuente primaria (declarado en el pre-registro de E06):** el stream `forceOrder` (liquidaciones) NO existe en el histórico público — solo en vivo. La firma de cascada se define por velocidad+volumen; es una limitación de diseño declarada, no un descuido.

## 3. Klines 12h + funding, universo point-in-time (~9 MB) — NO INCLUIDO
- **Usado por:** E07 (CS-MOM), E08, E09 y E11 (harness cross-sectional sobre `cs_mom.build_panels`) y E14 (que añade las métricas OI). Son datos de **perpetuos USDT-M** (`futures/um`). *(v1.0.1: E10, E12 y E13 no usan estos datos sino las velas 1h al contado de §1.)*
- **Regeneración:** `cs_mom_sandbox/cs_mom.py` descarga y construye el universo. Detalles point-in-time que importan para reproducir: universo 35→45 símbolos según fecha de listado, stitch de renombrados **MATIC→POL** y **RNDR→RENDER**, **SHIB = 1000SHIBUSDT**. El sesgo de supervivencia restante se asume y se declara como techo optimista en los veredictos.
- E14 (open interest) usa además las métricas OI públicas de data.binance.vision (~150 MB, no incluidas; el runner `cierre_definitivo_20260702/run_B7.py` documenta la descarga).

## 4. Datos W3 de otra fuente (`binance_w3_data/`) — NO INCLUIDO (no tracked)
- **Usado por:** E02/E16 como ancla de **otra fuente** (9 símbolos) — es el dataset que produce el ρ −0.0545. Regenerable con los mismos scripts de descarga. *(v1.0.3: la versión anterior decía «ventana distinta de la de data_cache; la independencia es el punto». No es así: son velas de futuros de Binance (2023-04-24 → 2026-04-23) que se solapan en el tiempo con `data_cache`; su tercio forward cubre meses que la selección ya había visto como velas al contado, y el pre-registro del Estudio lo marca como solo «Parcial» intocado: `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` L30; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18.)*

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
