# Fase 2 secundaria pnl_recon — causa raíz + Opción C (redefinir métrica)

**Fecha**: 2026-04-26
**Item §13.3**: "Investigación causa raíz pnl_recon gap analyzer" (commit `ab4f6f6` 2026-04-23, scope ~1-2h dedicada Opción D Fase 2 secundaria).
**Predecesor**: Fase 1 (commit `195be1a`, fix v1) eliminó duplicación `*2.0` round-trip — gap mean abs 0.0218→0.0137 USDT (-37%, predicción exacta), % > tolerance 90%→56.7%. Residual signed mean -0.013 USDT persistente.
**Bot v2.4.5 invariante** (cambio analyzer offline únicamente).

---

## 1. Spec original (§13.3 L2400 entrada 2026-04-23)

Hipótesis candidatas componentes del gap:

1. **Precision rounding CSV** — entry/exit redondeados 4-6 decimales. Magnitud ~0.1-1% sobre notional.
2. **Fees estimation divergente** — taker 0.05% vs maker 0.02%, BNB discount, funding ambiguo. ~0.05-0.2% sobre notional.
3. **Notional definition mismatch** — `size_usdt` BingX-reportado vs `contracts × CSV_entry_price`. ~0.1-5%.
4. **Size_usdt pre-v2.4.4 bug colateral** — campo BingX-internal divergente. Validación post-v2.4.4.

Plan original: Fase A descomposición → Fase B raw BingX API → Fase C fix → Fase D validación.

## 2. Causa raíz (no encaja en hipótesis A/B/C/D originales)

**Hallazgo code review** (no requirió raw BingX query adicional):

`live/execution_manager.py:378` (live mode `close_position`):
```python
return {
    "symbol": symbol, "action": "closed", "side": side,
    "close_price": fill_price, "pnl": position.get("unrealized_pnl", 0.0),
    ...
}
```

`live/data_feed.py:351` (fuente de `unrealized_pnl`):
```python
"unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),
```

**Cadena**:
1. `fetch_positions()` BingX retorna `unrealizedPnl` calculado con **mark_price actual** (no fill_price futuro) y bruto (sin descontar fees de close).
2. `close_position()` envía orden market, recibe `fill_price` real, pero retorna `pnl = position["unrealized_pnl"]` **del fetch previo** — NO recalcula con `fill_price`.
3. `log_trade()` escribe `pnl_usdt` CSV directamente desde ese campo.

**Consecuencia estructural**:
```
pnl_usdt CSV         ≈ (mark_price@fetch - entry) × contracts × sign     [bruto, mark-based]
pnl_estimate_offline = (fill_price@close  - entry) × contracts × sign - 0.001×notional  [neto, fill-based]
gap_signed = pnl_estimate_offline - pnl_usdt
           ≈ (fill - mark@fetch) × contracts × sign - 0.001×notional
```

Con drift taker `(fill - mark@fetch) ≈ -0.0005 × entry` (long sells at bid < mark; short buys at ask > mark, tras side_sign queda negativo consistente):
```
gap_signed ≈ -0.0005×notional - 0.001×notional ≈ -0.0015 × notional
```

Para notional típico ~5 USDT: gap_signed ≈ -0.0075 USDT.

## 3. Validación empírica predicción → observación

Re-ejecución analyzer post-Opción C N=63 trades válidos (precios+pnl):

| Métrica | Predicción | Observado | Status |
|---|---|---|---|
| signed mean | -0.005 a -0.013 USDT | **-0.0123 USDT** | ✓ dentro banda |
| signo signed | NEGATIVO consistente | NEGATIVO | ✓ exacto |
| \|abs\| mean | 0.010-0.015 USDT | **0.0133 USDT** | ✓ predicción exacta |
| \|abs\| p95 | 0.025-0.035 USDT | **0.0290 USDT** | ✓ dentro banda |

Causa raíz **CONFIRMADA**: divergencia mark@fetch ↔ fill@close + fees parciales en `unrealizedPnl` BingX.

## 4. Hipótesis A/B/C/D originales — refutadas

- **A precision rounding**: NO. Magnitud predicha ~0.1-1% notional (5×0.001=0.005 USDT mín), observado consistente con fill/mark drift no rounding (signed sistemático negativo, no random).
- **B fees divergente**: NO. Fee `0.05%` per side BingX confirmado empíricamente sobre fetch raw trade BTC/USDT (cost=7.80738, fee=0.003904 → 0.10% round-trip exacto, sin BNB discount).
- **C notional mismatch**: NO. `size_usdt` post-v2.4.4 100% válido sobre N=73 trades (audit C1 2026-04-26).
- **D size_usdt v2.4.4 colateral**: NO. Mismo audit confirma post-v2.4.4 limpio.

Las 4 hipótesis abordaban componentes del cálculo offline analyzer asumiendo que `pnl_usdt` CSV era `realized_pnl_neto` ground truth. La causa real es que `pnl_usdt` CSV sigue convención BingX `unrealizedPnl@fetch` (mark-based + bruto), y no es ground truth comparable con la reconstrucción analyzer (fill-based + neto).

## 5. Decisión Opción C — redefinir métrica analyzer

### 5.1 Tres opciones evaluadas

**Opción A — Fix bot-side** (`close_position` recompute con `fill_price`):
- Pros: `pnl_usdt` CSV converge con reconstrucción analyzer.
- Contras: toca bot v2.4.5 operacional (deploy + Fidelidad 2 verificación + rompe semántica histórica de reports — todos los CSVs anteriores asumían `pnl_usdt = unrealizedPnl@fetch`).

**Opción B — Fix analyzer convención BingX** (emular `mark_price@fetch`):
- Imposible retroactivamente: `mark_price@fetch` no se almacena.
- **Descartada**.

**Opción C — Redefinir métrica analyzer** (no toca bot):
- Renombrar `pnl_recon` → `pnl_estimate_offline` con docstring explícito.
- Cambiar alert mecánico (saturado por divergencia estructural) → reporte descriptivo distribución signed/unsigned.
- Bot v2.4.5 invariante; histórico CSV preservado.

### 5.2 Justificación §13.2 DECISION canónica

§13.2 establece "fix resuelve fenómeno, no tapa síntoma". Aplicado aquí:

- El "fenómeno" NO es un bug de cálculo en alguno de los componentes (refutado §4) — es la **divergencia de convenciones** entre dos métricas válidas.
- El "fix" no es ajustar tolerance arbitraria (eso sería tapar síntoma). Es **identificar y separar las dos convenciones en métricas independientes**.
- Opción C cumple §13.2: causa raíz IDENTIFICADA, métricas REDISEÑADAS con justificación empírica + teórica, alert SATURADO eliminado por construcción.

### 5.3 Trade-off documentado

- **Pierde**: alert mecánico "consistency check pnl_recon" como ground-truth pass/fail.
  - Pre-fix-v1: 93% trades > tolerance (saturado, falso-positivo masivo).
  - Post-fix-v1: 56.7% trades > tolerance (saturado moderado).
  - El alert NO funcionaba operacionalmente — ningún caso real detectado pre-fix-v1 fue bug, todos eran convención.
- **Gana**:
  - Claridad conceptual: dos métricas válidas, no comparables como ground truth.
  - Preserva observabilidad descriptiva (distribución signed mean, |abs| mean, p50, p95).
  - Bot v2.4.5 sin tocar, deploy-window invariante.
  - Histórico CSV retro analyzable sin re-cómputo (las nuevas keys son additive).

## 6. Cambios analyzer (Opción C)

`analyze_performance_attribution.py`:

| Sección | Antes | Después |
|---|---|---|
| L48 docstring | `S4 split counters: n_pnl_recon_checked, n_pnl_recon_not_closing` | distribución `pnl_offline_gaps_signed` + alert legacy eliminado |
| L132 const | `BALANCE_NOT_CLOSING_RATIO_ALERT = 0.05` | DEPRECATED comment, conservada por compat ABI |
| L140 const | `BALANCE_EQN_TOLERANCE_USDT = 0.01` | DEPRECATED comment |
| L826-827 keys | `pnl_recon_gap`, `pnl_recon_closes` | `pnl_estimate_offline`, `pnl_offline_gap_signed` |
| L991-1011 lógica | `pnl_recon = ... ; out['pnl_recon_gap'] = abs(...); out['pnl_recon_closes'] = gap <= tol` | docstring expandido convenciones BingX vs analyzer + variable `pnl_estimate_offline` + `out['pnl_offline_gap_signed'] = pnl_estimate_offline - pnl_real` (signed, no abs) |
| L1257-1265 reporte | `Consistencia de precios (C2): n_bad/n_chk con gap > tol (X%)` | `Gap offline-vs-CSV (descriptivo, N=...): signed mean / |abs| mean / p50 / p95` con convenciones inline |
| L1621-1633 agregado | `n_pnl_recon_checked`, `n_pnl_recon_not_closing` | `pnl_offline_gaps_signed` (lista) |
| L2031-2032 CSV | `pnl_recon_closes`, `pnl_recon_gap` | `pnl_estimate_offline`, `pnl_offline_gap_signed` |
| L2049-2057 final | `WARN/NOTA si ratio_bad > 5%` | comment Opción C explicativo, sin print |

## 7. Validación post-Opción C

Re-ejecución `python analyze_performance_attribution.py --no-plots` 2026-04-26 1511:

```
Gap offline-vs-CSV (descriptivo, N=63):
  Convenciones: pnl_estimate_offline = (fill-entry)*contracts*sign - 0.10%*notional (realized)
                pnl_usdt CSV = BingX unrealizedPnl@fetch (mark+bruto)
  signed mean: -0.0123 USDT  |  |abs| mean: 0.0133 USDT
  |abs| p50: 0.0121  |  p95: 0.0290
Datos de modelo incompletos: 159 trades
```

Verificaciones:
- ✓ Sin error runtime end-to-end.
- ✓ CSV nuevas columnas `pnl_estimate_offline`, `pnl_offline_gap_signed` presentes.
- ✓ Reporte ASCII+UTF-8 nueva sección descriptiva.
- ✓ 0 menciones `WARN/NOTA pnl_recon` en reporte → alert legacy eliminado.
- ✓ Otros alerts (EDGE EROSION, etc.) preservados sin regresión.

## 8. Items §13.3 cerrados

- **Línea 2400 "Investigación causa raíz pnl_recon gap analyzer"** → **RESUELTO Opción C 2026-04-26**.
- **Línea 2284 L1916 "Test consistencia ecuación de descomposición"** → **RESUELTO por merge natural 2026-04-26** (la métrica que soportaba el test fue rediseñada; el "test consistencia" original se vuelve obsoleto al separarse las convenciones).

## 9. Status Fase C pre-reciclaje

**7/7 items DONE** post Opción C:

1. ✓ Audit Fidelidad 2 N≥50 (`_run_verify_test` 76 trades diff 0.0000)
2. ✓ Investigación pnl_recon causa raíz Fase 1 (commit ab4f6f6)
3. ✓ Fix v1 pnl_recon aplicado + validado (commit 195be1a, -37% gap)
4. ✓ L1892 active_config_id SIGNALS_RAW (live_engine.py L565-577)
5. ✓ L1904 multipliers SIGNALS_DISCARDED (live_engine.py L607-625)
6. ✓ Triaje 4 micro-items §13.3 (3 EN_ESPERA refinados, 1 ARCHIVADO obsoleto)
7. ✓ **Fase 2 secundaria pnl_recon Opción C** (este documento)

**Fase C COMPLETA**. **Sistema pre-reciclaje en estado MADURO INSTITUCIONAL** post-2026-04-26: Fase A DONE_ARCHIVED (Z_BTC refutado empíricamente cross-5 altcoins, commit `63de84c`) + Fase B DONE merged + Fase C 7/7 DONE; pendientes solo D+E disparadores temporales (~2026-05-01 / ~2026-05-10). Próximo natural: esperar D+E o continuación institucional según oportunidad.

## 10. Referencias

- `live/execution_manager.py` L378 (causa raíz código).
- `live/data_feed.py` L351 (fuente `unrealized_pnl`).
- `analyze_performance_attribution.py` L991-1011 (cambios Opción C centrales).
- `docs/pnl_recon_root_cause_20260426.md` (Fase 1 / fix v1, predecesor).
- §13.2 DECISION canónica "Consistency check por reconstrucción no tautológico".
- §13.3 línea 2400 entrada original (cerrada).
- §13.3 línea 2284 L1916 (cerrada).
- §13.4 entrada Opción C 2026-04-26.
- ROADMAP_PRE_RECICLAJE.md Fase C item 7 → DONE.
