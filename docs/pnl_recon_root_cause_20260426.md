# Investigación causa raíz pnl_recon_gap — Fase C item 2 Opción D

**Fecha**: 2026-04-26
**Item §13.3**: "Investigación causa raíz pnl_recon gap analyzer" (commit ab4f6f6, scope ~1-2h dedicada Opción D).
**Síntoma persistente**: pnl_recon_gap > tolerance en 92% N=26 (A.1 sesión 2026-04-23) → 93% N=60 (audit C1 institucional 2026-04-26).
**Bot v2.4.5 invariante**.

---

## 1. Spec item §13.3 + componentes

### 1.1 Fórmula pnl_recon en analyzer (analyze_performance_attribution.py L996-1007)

```python
# C2: consistency check por reconstruccion de precios.
if (contracts is not None and contracts > 0
        and not math.isnan(out['entry_price_csv'])
        and not math.isnan(out['exit_price_csv'])
        and not math.isnan(out['pnl_real'])):
    notional_entry = contracts * out['entry_price_csv']
    est_fees = COMMISSION_RATE * notional_entry * 2.0  # round-trip
    pnl_recon = ((out['exit_price_csv'] - out['entry_price_csv'])
                 * contracts * ss) - est_fees
    tolerance = max(BALANCE_EQN_TOLERANCE_USDT, 0.1 * abs(out['pnl_real']))
    out['pnl_recon_gap'] = abs(pnl_recon - out['pnl_real'])
    out['pnl_recon_closes'] = out['pnl_recon_gap'] <= tolerance
```

### 1.2 Constantes y definiciones

- `COMMISSION_RATE = 0.001` con comment **"0.10% round-trip approx (entry+exit)"** (L106).
- `BALANCE_EQN_TOLERANCE_USDT = 0.01` (floor tolerance).
- `contracts = size_usdt / entry_price_exec` (L935-937).
- `pnl_real = pnl_usdt` del CSV (sin funding incluido — `funding_paid` es columna separada).

### 1.3 Datos para investigación

Dataset post-v2.4.5 N=60 (de audit C1 institucional 2026-04-26):
- 100% size_usdt > 0 (post-v2.4.4 fix).
- 100% entry_timestamp_ms > 0 (post-v2.4.5 fix).
- 100% funding_paid != 0 (cobertura completa).
- entry_price + exit_price + pnl_usdt + funding_paid disponibles para todos.

## 2. Distribución pnl_recon_gap actual

| Métrica | Valor |
|---------|------:|
| count | 60 |
| mean | 0.0218 USDT |
| median | 0.0201 USDT |
| std | 0.0091 USDT |
| min | 0.0044 USDT |
| max | 0.0439 USDT |
| p25 | 0.0150 USDT |
| p75 | 0.0274 USDT |
| p90 | 0.0331 USDT |
| p99 | 0.0433 USDT |

Gap como fracción de \|pnl_real\|: p50 = 34%, p75 = 81%, p90 = 172%, p99 = 1452% (trade pnl ~0).

% trades con gap > tolerance: **93.3%**.

## 3. Hipótesis candidatas + tests discriminatorios

### H_fees: double-counting en `est_fees`

Comment dice "0.10% round-trip approx (entry+exit)". Pero código aplica `COMMISSION_RATE * notional * 2.0`:
- `est_fees = 0.001 × notional × 2.0 = 0.20% × notional` (round-trip).
- BingX taker real: 0.05% per side = **0.10% round-trip**.
- Analyzer over-estima fees por **factor 2×**.

**Test discriminatorio**: comparar gap empírico vs predicted by 2× fee over-estimate.

```
predicted_gap_H_fees = (0.20% - 0.10%) × notional = 0.10% × notional = 0.001 × size_usdt
```

Resultado:
- corr(gap_real, gap_predicted_H_fees) = **+0.674** (strong correlation).
- corr(gap_signed_analyzer, size_usdt) = **−0.564** (gap más negativo con notional grande, consistente con fee over-estimate proporcional a notional).
- Mean ratio gap_real / gap_predicted_H_fees = **2.40-2.59**.

**Veredicto H_fees**: **CONFIRMADA como causa primaria** — explica ~38-40% del gap (predicted_gap es ~40% del observed).

### H_funding: pnl_real CSV incluye funding implícito

Si `pnl_usdt` CSV tuviera funding embebido (no solo en columna separada), gap = pnl_recon (sin funding) − pnl_usdt (con funding implícito) sería distinto.

**Test discriminatorio**: comparar pnl_recon + funding_paid vs pnl_usdt.

Resultado:
- pnl_recon (con bingx taker rate 0.10% round-trip) gap mean abs: 0.0137.
- pnl_recon (con bingx taker) + funding_paid: gap mean abs 0.0132 (apenas mejora -3.6%).
- corr(gap_signed, funding_paid) = **−0.244** (correlación débil).
- Funding mean per trade: +0.0004 USDT (irrelevante en magnitud vs gap).

**Veredicto H_funding**: **REFUTADA como causa primaria**. pnl_usdt CSV NO incluye funding embebido. funding_paid es columna independiente. Magnitud funding insignificante vs gap residual.

### H_decimal / H_price_precision: precision rounding entry/exit prices CSV

Prices CSV redondeados a 4-6 decimales. Para notional 10 USDT y entry_price 0.1 USDT:
- contracts = 100.
- Precision 4 decimal en entry_price: error ±0.00005 USDT.
- PnL error: 0.00005 × 100 = 0.005 USDT (~10% del gap residual post-fix).

**Test discriminatorio**: residual post H_fees fix correlaciona con contracts × precision.

Resultado:
- Residual signed post fix v1 (eliminar `*2.0`): **−0.0127 mean** consistentemente NEGATIVO.
- corr(residual_signed, contracts) = +0.145 (débil).
- corr(residual_signed, naive_pnl) = +0.434 (correlación con magnitud PnL).

**Veredicto H_decimal**: **PARCIAL** — explica algo del residual post-H_fees fix pero no es la causa dominante secundaria.

### H_real_fees_below_taker: BingX aplica fees < 0.10% (BNB discount, VIP tier)

Si BingX real fees son menores que el taker estándar 0.10% round-trip (BNB discount → 0.045-0.09% range), el bot recibe PnL real algo mayor que pnl_recon estima.

**Test discriminatorio**: residual_signed post-fix consistentemente NEGATIVO sugiere bot real PnL > pnl_recon (el bot pagó MENOS fees que asume el analyzer post-fix v1).

Resultado: residual signed mean = **−0.013 USDT** (consistentemente negativo). Compatible con BingX real fees ~0.06-0.08% round-trip vs 0.10% asumido.

**Veredicto H_real_fees_below_taker**: **PROBABLE causa secundaria**. residual signed negativo + correlación con notional sugiere fees reales menores.

### H_size_usdt_drift: size_usdt BingX-reported vs computed

Bot reporta `size_usdt = filled_notional from BingX`. analyzer calcula `contracts = size_usdt / entry_price_csv`. Si size_usdt BingX usa entry_price MEJOR que CSV (precisión BingX > CSV), contracts calculados desvían.

**Test discriminatorio**: para los top 5 residual_abs post-fix, inspeccionar drift contracts.

Resultado: top 5 residuals van −0.033 a +0.029 (mix signs). NO sistemáticos. Drift contracts es minoritario.

**Veredicto H_size_usdt_drift**: **MENOR contribución**.

## 4. Modelos de fee discriminados

| Modelo fee | Mean abs gap | Median | %>0.01 | %>tolerance |
|-----------|------------:|-------:|-------:|------------:|
| Current (0.001 × 2.0 = 0.20%) | 0.0218 | 0.0201 | 93.3% | 90.0% |
| **Fix v1 (0.001 × 1.0 = 0.10%)** | **0.0137** | **0.0127** | **65.0%** | **56.7%** |
| Fix v2 (0.0005 × 2.0 = 0.10%) | 0.0137 | 0.0127 | 65.0% | 56.7% |
| Maker (0.0002 × 2.0 = 0.04%) | 0.0091 | 0.0074 | 31.7% | 23.3% |

**Fix v1** (eliminar `*2.0`) y **Fix v2** (cambiar COMMISSION_RATE a 0.0005 mantener `*2.0`) son matemáticamente equivalentes. **Fix v1 más conservador** (1 línea, comment ya consistente). Reduce gap mean en 37%, % over tolerance de 90% a 57%.

## 5. Causa raíz identificada

**CAUSA RAÍZ PRIMARIA**: **double-counting de round-trip** en línea 1001 de `analyze_performance_attribution.py`:

```python
# CURRENT (BUG):
est_fees = COMMISSION_RATE * notional_entry * 2.0  # round-trip
# COMMISSION_RATE = 0.001 — comment dice "0.10% round-trip approx (entry+exit)"
# El * 2.0 DUPLICA el round-trip ya implícito en la constante.
```

Comment del COMMISSION_RATE explícitamente dice "round-trip" (entry+exit combined). El operador `* 2.0` aplica un round-trip ADICIONAL, resultando en 0.20% notional fees vs los 0.10% intended.

**Magnitud impacto**: +0.001 × notional USDT extra por trade en fees subestimados. Para notional típico ~10 USDT: 0.010 USDT/trade. Sobre N=60: 0.60 USDT acumulado de "fees fantasma" en pnl_recon vs pnl_real.

**CAUSA RAÍZ SECUNDARIA** (residual post-fix v1): mix de:
- H_real_fees_below_taker: BingX real fees probablemente <0.10% round-trip (BNB discount, taker rate < 0.05% per side, etc.). Magnitud ~0.005-0.013 USDT/trade.
- H_decimal: precision rounding entry/exit prices CSV crea drift sub-bp. Magnitud ~0.001-0.005 USDT/trade.

Estas causas secundarias **suman ~0.013 USDT residual post-fix v1**, suficiente para que ~57% trades aún violen tolerance 0.01 floor pero ya dentro del rango aceptable.

## 6. Fix sugerido + scope

### 6.1 Fix v1 (1 línea, recomendado)

```python
# analyze_performance_attribution.py línea 1001
# BEFORE:
est_fees = COMMISSION_RATE * notional_entry * 2.0  # round-trip

# AFTER:
est_fees = COMMISSION_RATE * notional_entry  # round-trip (already includes entry+exit)
```

Scope: 1 línea código + actualización comment opcional. Test diferencial: re-ejecutar analyzer sobre attribution_per_trade_20260426_1113.csv y verificar gap mean abs ~0.0137 (esperado).

### 6.2 Predicción post-fix v1

| Métrica | Pre-fix | Post-fix v1 |
|---------|--------:|------------:|
| gap mean abs | 0.0218 | 0.0137 |
| gap median | 0.0201 | 0.0127 |
| % trades >0.01 absoluto | 93% | 65% |
| % trades >tolerance | 90% | 57% |

### 6.3 Spec Fase D criterio: gap típico <5%, <10% p95

Fix v1 NO alcanza spec Fase D criterio (57% > tolerance, target <5%). Mejora sustancial (de 90% a 57%) pero residual ~0.013 USDT/trade indica causas secundarias adicionales requieren investigación Fase 2 dedicada.

**Plan recomendado**:

1. **Fix v1 inmediato** (1 línea): elimina la causa primaria identificada. Reduce gap 37%.
2. **Investigación adicional Fase 2** (~30-45 min, item §13.3 nuevo opcional):
   - Verificar BingX taker fees reales para cuenta del bot (con BNB discount aplicado, VIP tier).
   - Inspeccionar precision drift `size_usdt` BingX-reported vs CSV-recorded.
   - Posiblemente añadir `funding_paid` al pnl_recon si pnl_usdt CSV implícitamente lo incluye (validar con un trade específico).
3. **Tolerance ajuste opcional** (~5 min): si residual ~0.013 USDT inevitable, considerar floor tolerance de 0.01 → 0.015 USDT (1.5×) para que ratio 5% sea alcanzable.

## 7. Status item §13.3 actualizado

- **Causa raíz primaria identificada**: double-counting `*2.0` en COMMISSION_RATE round-trip.
- **Fix v1 sugerido**: 1 línea código, predicción gap mean -37%.
- **Causas secundarias**: H_real_fees_below_taker + H_decimal residual ~0.013 USDT/trade. Investigación Fase 2 ~30-45 min sesión adicional.
- **Spec Fase D criterio**: NO alcanzado solo con fix v1 (57% > target 5%). Requiere combinación fix v1 + investigación secundaria + posible tolerance ajuste.

**Item §13.3 sigue ABIERTO post-Fase 1 investigación** (causa raíz primaria identificada, fix dispuesto). Cierre se completará tras:
- Fix v1 implementado en analyze_performance_attribution.py.
- Re-ejecución analyzer sobre N=60 demuestra gap mean ~0.0137 confirmado.
- Investigación Fase 2 secundaria si se decide invertir scope adicional.

## 8. Hallazgos inesperados

🔹 **Comment vs código mismatch confirmado**: comment "0.10% round-trip approx" pero código aplica como per-side con `*2.0`. Bug de copy-paste o legacy refactor incompleto.

🔹 **gap residual post-fix consistentemente NEGATIVO** (mean −0.013 USDT): bot reporta PnL real **mayor** que reconstrucción analyzer. Compatible con BingX fees reales <0.10% round-trip (BNB discount, taker rate menor).

🔹 **§12 Lección 26 aplicada empíricamente**: H_funding refutada por correlación débil (−0.244) y magnitud insignificante. Sin validación per-componente, hipótesis "ecuación cierre OK significa no hay bug" hubiera ocultado el bug `*2.0` (la ecuación cierre matemático SÍ pasa para alpha residual, pero pnl_recon es check separado per-componente).

🔹 **Item §13.3 "Investigación causa raíz pnl_recon gap"** evolucionó por aplicación recursiva §12 L34: refutación L2018 (floor) → refutación "ratio 25%" (prerequisite inviable) → "Investigación causa raíz" Opción D (este análisis). Tres iteraciones para llegar al fix de 1 línea.

## 9. Referencias

- §13.3 "Investigación causa raíz pnl_recon gap" (commit ab4f6f6 2026-04-23).
- §13.4 entrada nueva "pnl_recon causa raíz Fase C item 2 — 2026-04-26" (esta sesión).
- §13.2 "Consistency check por reconstrucción no tautológico" 2026-04-17 (preservada — fix resuelve fenómeno, no tapa síntoma).
- §13.4 audit C1 institucional 2026-04-26 (pnl_recon_gap 93% N=60 confirmado).
- `analyze_performance_attribution.py` L996-1007 (función pnl_recon).
- `attribution_per_trade_20260426_1113.csv` (dataset N=60 investigado).
- §12 L26 (validación per-componente) + L34 (refutaciones recursivas) + L35 (test discriminatorio antes investigar causa).

**Status**: causa raíz primaria identificada, fix dispuesto. Item §13.3 sigue ABIERTO hasta fix implementado + verificación empírica post-fix.
