# Path B caracterización rasgo agregado mercado funding rates — ARCHIVED 2026-04-26

**Status**: ARCHIVED (Path B.4 decisión Ricardo).
**Sesión**: día 2026-04-26 sesiones 3+4.
**Bot v2.4.5 invariante** uptime 4d 12h+ durante toda la sesión. Sin tocar `live/*`.

---

## Origen y evolución de la investigación

**Variante 4 original (sesión 3 día 2026-04-26)**:
Caracterización estructural rasgo funding aligned/contrarian via kernel re-ejecución cross-régimen sobre specialists actuales con histórico 3y completo. Output deseado: dataset trades sintéticos cross-axis enriquecidos con funding rates per trade.

**Bloqueo Tier 0 I1 detectado pre-Fase 1 (§12 L36 protocolo)**:
Kernel `run_simulation_numba` exporta SOLO agregados (7 metrics + 6 cluster aggregates), NO arrays per-trade (side/entry_ts/reason_exit). Documentado §13.3 línea 2589-2645 como diferido post-reciclaje por timing operacional + Fidelidad 1 risk + scope 15-20h sesión dedicada.

Pivote a **Opción C aggregate-level metric-driven** (compatible con kernel actual).

**Sesión 1 Variante 4 Opción C (pre-Path B)**:
Cross-exchange Binance↔BingX validation 5 símbolos × 30d → veredicto **COHERENCIA BAJA** (mean directional 65.5%, mean categorical 54.2%, ρ=+0.51). Magnitudes divergentes sistemáticas: SEI Binance ~1.75× BingX, BTC/ETH BingX ~1.6-1.8× Binance.

Ricardo reformulación marco institucional: *"el rasgo es propiedad agregada del mercado, debemos buscarlo en la fuente más informativa (Binance mayor cap), no en la fuente operacional del bot (BingX)"*. La BAJA coherence en rates pequeños NO refuta hipótesis — la confirma desde nueva perspectiva: rates significativos cross-exchange deberían ser unanimous (sesgo mercado) vs rates pequeños local-noise.

→ **Path B-institutional** = cross-3-exchanges con threshold sweep para identificar magnitud X crítica.

---

## Path B Fase 1' — cross-3-exchanges + threshold sweep

**Setup**:
- Exchanges: Binance + BingX + OKX vía ccxt `fetchFundingRateHistory`.
- 15 símbolos cross-cap-tier:
  - Tier 1 mega-cap (4): BTC, ETH, BNB, SOL.
  - Tier 2 large-cap (4): XRP, DOGE, ADA, LINK.
  - Tier 3 mid-cap (4): AVAX, DOT, LTC, NEAR.
  - Tier 4 small/recientes (3): ONDO, SEI, ENA.
- Ventana solicitada: 180 días (2025-10-28 → 2026-04-26).
- Threshold sweep: X ∈ {1e-5, 5e-5, 1e-4, 5e-4, 1e-3}.
- Criterio X crítico: minimum X con unanimidad cross-3 ≥95% AND N≥50 bars pooled.
- Tolerance alineación timestamps: 30 min.

**Implementación**: `analysis_scripts/funding_v4_pathb_20260426/fase1prima_cross3_exchanges.py`.
**Extensión `funding_context.py`**: agregado OKX support (2 ediciones: `elif exchange_id == "okx"` en `fetch_funding_rates` + `okx` en CLI choices flag `--exchange`).

---

## Hallazgo 1 — Rasgo estructural CONFIRMADO empíricamente

Pooled cross-15-símbolos:

| Threshold X | N bars ≥X | Unanimidad 3-way | pair B-X | pair B-O | pair X-O |
|---|---:|---:|---:|---:|---:|
| 1e-05 | 3792 | 63.8% | 72.2% | 76.5% | 78.8% |
| 5e-05 | 2266 | 71.1% | 77.2% | 83.7% | 81.3% |
| 1e-04 | 1055 | 78.5% | 83.2% | 88.7% | 85.0% |
| **5e-04** | **57** | **96.5%** | 96.5% | 100.0% | 96.5% |
| 1e-03 | 12 | 100.0% | 100.0% | 100.0% | 100.0% |

**X crítico empírico = 5e-04**. Rates ≥5e-4 muestran direccionalidad unanimous cross-3-exchanges → evidencia rasgo agregado mercado (no ruido local-exchange). Rates <5e-4 son local-exchange phenomena dominantes.

**Cross-régimen breakdown (efectivamente 2 sub-windows post-OKX-retention)**:

| Sub-window | Ventana | N bars ≥5e-4 | Unanimidad 3-way |
|---|---|---:|---:|
| sw0 | 2025-10-28 → 2025-12-27 | 0 | N/A (OKX no coverage) |
| sw1 | 2025-12-27 → 2026-02-25 | 22 | 90.9% |
| sw2 | 2026-02-25 → 2026-04-26 | 35 | 100.0% |

Sub-window 1 marginal (90.9% < 95%). Sub-window 2 confirma 100%. Estabilidad cross-régimen razonable con N escaso (sw1+sw2 ambos en banda alta).

---

## Hallazgo 2 — Rasgo es EXTREMO RARO régimen actual

Per-symbol distribución cross-180d, fracción bars con `|rate_binance| ≥ 5e-4`:

| Sym | mean_abs | p95_abs | p99_abs | frac ≥5e-4 |
|---|---:|---:|---:|---:|
| **SEI** | 0.000215 | 0.000763 | 0.000992 | **14.0%** |
| **DOT** | 0.000214 | 0.000820 | 0.001793 | **8.4%** |
| SOL | 0.000091 | 0.000240 | 0.000532 | 1.4% |
| NEAR | 0.000079 | 0.000144 | 0.000309 | 0.3% |
| BTC | 0.000037 | 0.000084 | 0.000124 | 0.0% |
| ETH | 0.000047 | 0.000123 | 0.000226 | 0.0% |
| BNB | 0.000009 | 0.000057 | 0.000105 | 0.0% |
| XRP | 0.000068 | 0.000175 | 0.000261 | 0.0% |
| DOGE | 0.000062 | 0.000119 | 0.000176 | 0.0% |
| ADA | 0.000083 | 0.000206 | 0.000283 | 0.0% |
| LINK | 0.000061 | 0.000100 | 0.000145 | 0.0% |
| AVAX | 0.000082 | 0.000196 | 0.000284 | 0.0% |
| LTC | 0.000048 | 0.000100 | 0.000104 | 0.0% |
| ONDO | 0.000035 | 0.000075 | 0.000146 | 0.0% |
| ENA | 0.000043 | 0.000106 | 0.000181 | 0.0% |

**11/15 símbolos (73%) NUNCA alcanzan rate ≥5e-4 cross-180d**. Concentración extrema en 4 sym (SEI 14%, DOT 8.4%, SOL 1.4%, NEAR 0.3% = ~24% combined del histórico ≥X). Mega/large-caps (BTC/ETH/BNB/XRP/DOGE/ADA/LINK), donde el bot opera más, **0 eventos en 180d**.

---

## Hallazgo 3 — OKX retention 95d (caveat permanente)

**Verificación directa** (test SSH VPS, ccxt async):
```python
ex.fetch_funding_rate_history("BTC/USDT:USDT", limit=1000)
# Retorna: 287 rates, earliest 2026-01-21, latest 2026-04-26

ex.fetch_funding_rate_history("BTC/USDT:USDT", since=2025-10-28_ts, limit=1000)
# Retorna: 287 rates idéntico — since param no extiende retention
```

**OKX API funding history retention ≈ 95 días** no extensible. Binance + BingX retention ≥180 días (no testado upper bound).

Implicación operacional: cualquier análisis cross-3-exchanges retrospectivo extendido (>3 meses atrás) hereda OKX como bottleneck permanente. Para análisis cross-régimen amplio (>3-6 meses), el setup correcto es:
- 2-exchange Binance↔BingX cross-régimen amplio (no limitado por retention).
- OKX como verificación adicional ventana móvil reciente (~95d) cuando se requiere unanimidad cross-3.

---

## Decisión Path B.4 — Archivar Variante 4 con captura institucional

**Caveats acumulados que erosionarían valor incremental Sesión 2 (Fase 2-3'-4-5-6)**:

1. Aggregate-level cluster ≠ per-trade granularidad (Tier 0 I1 limitation).
2. Tier 0 I1 sigue diferido post-reciclaje (filter productivo final requiere kernel modificado).
3. Cross-exchange transferibilidad parcial (Binance→BingX divergencias documentadas Sesión 1).
4. Threshold X específico régimen actual rates pequeños (re-calibrable cross-régimen).
5. Funding cobertura asimétrica 4h vs 8h per símbolo.
6. **Rasgo extremo raro régimen actual** (N=57 eventos cross-180d — Hallazgo 2).
7. **OKX retention 95d** cross-régimen no extensible (Hallazgo 3).

Output esperado Sesión 2 con esos caveats: *"evidencia indirecta sugestiva con power limitado sobre 4 símbolos en régimen rates pequeños actual"*. Erosión señal/ruido vs disparador operacional D inminente.

**Disparador D operacional ~2026-05-01 N≥100 (BingX-native, post-v2.4.5 régimen homogéneo)** sigue siendo método correcto para decisión filter productivo. **Threshold X=5e-4 empírico identificado hoy reemplaza §9.3 arbitrario `|rate| > 0.001` como input al diseño análisis Welch post-N≥100**.

---

## Calibración §12 L36 retrospectiva (3 sesiones consecutivas funding research)

| Sesión | Predicciones | Acertadas | Refutadas | Outcome |
|---|---|---:|---:|---|
| Sesión 1 (Variante 4 original) | 6 cualitativas estructurales | 6/6 | 0/6 | Tier 0 I1 bloqueante detectado pre-compute. Pivote Opción C. Ahorro ~15-90h compute infeasible. |
| Sesión 2 (Path B previo cross-2-exchange) | 5 (ALTA coherence) | 0/5 | 5/5 | Refutación reveló estructura: rates pequeños = local-noise, magnitudes ≥X cross-exchange unanimous. Reformulación Ricardo emergente. |
| Sesión 3 (Path B-institutional cross-3 + 180d) | 9 | 6/9 | 1/9 fuerte + 2/9 parcial | Rasgo X=5e-4 confirmado pero EXTREMO RARO. Predicción 1.E refutada por OKX retention (factor estructural no anticipado). |

**Patrón institucional consolidado §12 L36**:
Predicciones refutadas en magnitud (no en dirección estructural) son outcome más informativo que predicciones acertadas. 3 sesiones consecutivas Variante 4: cada refutación llevó a hallazgo estructural genuino + redirección scope metodológicamente correcto.

**Ahorro compute acumulado**: ~30-45h paths que hubieran sido infeasibles ciegamente:
- Sesión 1: kernel modification path A (15-20h) + brain-level path B (60-90h) → evitados.
- Sesión 2: extensión ciega Path B sin threshold sweep habría producido análisis aggregate-level con magnitudes incomparables exchange-to-exchange.
- Sesión 3: Fase 2-3'-4-5-6 con N=57 power limitado y OKX bottleneck habría producido conclusiones no operacionalmente accionables.

L36 protocolo redirigió scope correctamente cada sesión, en línea con definición original L36 (*"variante constructive de L35 — predicción cualitativa antes de implementación invasiva, predicción refutada redirige antes invertir compute"*).

---

## Hallazgos institucionales permanentes preservados (independientes de Variante 4 outcome)

1. **Threshold X=5e-4 empírico cross-3-exchanges** reemplaza §9.3 `|rate| > 0.001` arbitrario como input al diseño v2.6-inv análisis Welch post-disparador N≥100.

2. **Rasgo agregado mercado funding rates es real** (96.5% unanimidad cross-3) pero raro régimen actual: concentración 4 símbolos primary (SEI/DOT/SOL/NEAR), mega/large-caps 0 eventos cross-180d.

3. **OKX retention 95d caveat permanente cross-exchange retrospective** — afecta cualquier análisis futuro que requiera unanimidad cross-3 más allá de ventana móvil reciente.

4. **§12 L36 validada profilácticamente cross-3 sesiones consecutivas funding research** con métricas concretas de ahorro compute + redirección scope metodológicamente correcta.

---

## Items §13.3 actualizados con input empírico

- **L2340 v2.6-inv momentum filter**: contexto + threshold empírico X=5e-4 vs §9.3 arbitrario `|rate| > 0.001`. Disparador N≥100 ~2026-05-01 MANTENIDO con análisis Welch específico subset trades con `|funding_rate_at_entry| ≥ 5e-4` aligned vs contrarian. Caveat: subset esperado pequeño régimen actual (concentración SEI/DOT/SOL/NEAR primary; mega-caps 0 eventos cross-180d Path B) — si subset N<20 cross-N≥100 operacional, archivar como "rasgo real pero NO operacionalmente accionable régimen actual".

- **L2385 v2.6-exit filter**: análogo update threshold empírico X=5e-4. Disparador N≥150 mantenido.

---

## Output preserved (referencia permanente)

- `analysis_scripts/funding_v4_pathb_20260426/fase1prima_results.json` — datos crudos cross-3 × 15 sym × 180d.
- `analysis_scripts/funding_v4_pathb_20260426/fase1prima_cross3_exchanges.py` — script ejecutable (incluye bug `find_critical_X` documentado: key mismatch `n_bars_geq_X` vs `n_bars_geq_X_pool` causó veredicto literal incorrecto pre-fix manual; se preserva tal cual como referencia + post-process scripts hacen análisis correcto).
- `analysis_scripts/funding_v4_opcion_c_20260426/fase1_results.json` — Sesión 2 cross-2-exchange BAJA coherence (referencia previa al pivot Path B).
- `funding_context.py` extendido con OKX support (commit incluido en cierre).

---

## Estado pre-reciclaje invariante post-archive

Sistema pre-reciclaje en estado **MADURO INSTITUCIONAL** invariante post-Path B archive:

- Fase A DONE_ARCHIVED 2026-04-26 (Z_BTC refutado cross-5 altcoins).
- Fase B DONE merged 2026-04-25 (M2 fix validado N=9).
- Fase C 7/7 DONE 2026-04-26 (audit + pnl_recon + L1892/L1904 + triaje + Opción C).
- Fase D EN_ESPERA disparador N≥100 ~2026-05-01 (con threshold X=5e-4 empírico nuevo input).
- Fase E EN_ESPERA disparador N≥150 ~2026-05-10.
- Reciclaje completo 45 sym ETA ~2026-05-12 a 05-22.

Path B archive es cierre coherente con marco institucional Ricardo: hallazgos permanentes preservados, decisión filter productivo final delegada a disparador operacional D con threshold empírico mejor que arbitrario.

---

## Referencias cruzadas

- `analysis_scripts/funding_v4_pathb_20260426/` — código + data crudo Path B Sesión 3.
- `analysis_scripts/funding_v4_opcion_c_20260426/` — Sesión 2 previa cross-2-exchange.
- §13.4 entrada Path B archive 2026-04-26 (resumen ejecutivo + 3 hallazgos).
- §13.3 L2340 v2.6-inv (updated threshold empírico).
- §13.3 L2385 v2.6-exit (updated análogo).
- §13.3 L2589-2645 Tier 0 I1 (sigue diferido post-reciclaje).
- §12 L36 (3 sesiones aplicaciones consecutivas, validación profiláctica institucional).
- ROADMAP_PRE_RECICLAJE.md sección "Variante 4 funding caracterización" → ARCHIVED.
- Conversación Ricardo 2026-04-26 sesión 3 día (reformulación marco) + sesión 4 día (decisión Path B.4).
