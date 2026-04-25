# M2 fix validation — Smoke C exact replica (2026-04-25)

Validación empírica cross-symbol N=9 del M2 fix (commit 7162369, Fase B
ROADMAP_PRE_RECICLAJE).

## Propósito

Discriminar empíricamente entre Interpretación 1 (M2 fix funciona como
diseñado) vs Interpretación 2 (M2 fix selecciona configs lucky en fwd
window) ejecutando 9 configs M2 fix top-1 (BTC+ONDO+SEI × C0/C1/C2)
sobre Binance Futures 3y con setup Smoke C exacto.

## Archivos

- `m2_fix_smoke_test.py` — adapter, clon literal de
  `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py`
  con 4 cambios mínimos documentados en docstring.
- `m2_fix_smoke_results.csv` — output 10 rows (9 M2 fix + 1 W3b baseline).
- `_gmm_head_baseline/` — GMM HEAD baseline (binarios joblib NO commitados;
  regenerar con `setup_gmm_baseline.sh` o git show).

## Cómo regenerar GMM HEAD baseline

```bash
mkdir -p analysis_scripts/m2_fix_validation_20260424/_gmm_head_baseline
git show HEAD:regime_models/BTC_regime.joblib  > _gmm_head_baseline/BTC_regime.joblib
git show HEAD:regime_models/ONDO_regime.joblib > _gmm_head_baseline/ONDO_regime.joblib
git show HEAD:regime_models/SEI_regime.joblib  > _gmm_head_baseline/SEI_regime.joblib
```

El baseline es necesario porque smokes posteriores (reciclaje Bloque 5
2026-04-24, smoke BTC M2 fix 2026-04-25) regeneraron el GMM BTC working
tree. La paridad con Smoke C original requiere el GMM HEAD.

## Ejecutar

```bash
python -u analysis_scripts/m2_fix_validation_20260424/m2_fix_smoke_test.py
```

Tiempo: ~3-5 min (10 configs Numba JIT).

## Resultados clave (2026-04-25)

- Mean ratio J/B cross-9: **2.408** (vs W3b baseline 8.235, **3.42× reducción**).
- 0/9 colapso fuerte cross-symbol; 9/9 edge real positivo (Binance pf_fwd>1.0).
- Spearman ρ cross-9: −0.17 p=0.65 NO sig.
- Sanity determinismo W3b cfg 20607806 = 0.7722 desviación 0.00%.

Veredicto: M2 fix VALIDADO empíricamente como mejora parcial.
Avanzar Fase A (Z_BTC).

Ver §13.4 entrada "M2 fix VALIDACIÓN POST-IMPLEMENTACIÓN cross-symbol N=9
— 2026-04-25" en CONTEXTO_PROYECTO_TRADING.md para análisis completo.
