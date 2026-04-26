# Roadmap pre-reciclaje — consolidado 2026-04-24

**Criterio institucional Ricardo 2026-04-24**: todas las mejoras (A+B+C) implementadas antes de lanzar reciclaje completo 45 sym. Categorías D+E esperan datos operacionales temporales. Reciclaje se lanza cuando A+B+C done + D+E validados/archivados.

## Categorías

### Categoría A — Z_BTC como feature GMM altcoins — **DONE_ARCHIVED 2026-04-26 (refutado empíricamente cross-5 altcoins)**
Scope original: ~8-12h sesión dedicada. Modificaba `regime_features.py` para añadir Z_ATR BTC como feature cross-símbolo del GMM de altcoins.

**Cierre 2026-04-26**: ARCHIVED por refutación empírica. Sub-fase A.1 V1 implementada (commit `20b5773`) + Sub-fase A.2 BIC sweep multi-criterio cross-5 altcoins (commit `63de84c`) → **ESCENARIO A — UNANIMIDAD V0**: ΔBIC = V1_best_bic - V0_best_bic positivo cross-5 (ONDO +14610, SEI +53193, ETH +121194, AAVE/DOGE strong V0 también). 5/5 altcoins prefieren V0 (sin Z_ATR_BTC) sobre V1 (con Z_ATR_BTC) por criterio BIC + discriminación + multicolinealidad. Z_BTC no aporta información incremental al GMM altcoins; complejidad cross-exchange Binance↔BingX (caveat §0.6.1) injustificada empíricamente. Adapter preservado: `analysis_scripts/fase_a_a2_bic_sweep_20260426/`.

Referencias: §9.4 v3.0 (contexto conceptual), §13.3 Z_ATR BTC 2026-04-23, commits `db55617` + `20b5773` + `63de84c`, §0.6.1 caveat cross-exchange dependency.

### Categoría B — Metodología walk-forward Mecanismo 2 fix (refinamiento ranking) — **DONE 2026-04-25**
Scope: ~4-6h sesión dedicada. Implementado commit 7162369 + validado empíricamente cross-symbol N=9 commit pendiente.
Re-ordena selección specialists por `pf_fwd_ci_low` directo en lugar de `specialist_score_ci_low` (que embebe pf_combined con dilución train/fwd). Elimina sesgo Mecanismo 2 identificado por Ricardo 2026-04-24.

**Validación empírica cross-symbol N=9 (2026-04-25)**:
- Mean ratio J/B cross-9 (BTC+ONDO+SEI top-1 M2 fix sobre Binance 3y): **2.408** (vs W3b baseline 8.235, **3.42× reducción**).
- 0/9 colapso fuerte cross-symbol; 9/9 edge real positivo Binance pf_fwd>1.0.
- Spearman ρ cross-9: −0.17 (p=0.65, NO significativo).
- Veredicto: **VALIDADO EMPÍRICAMENTE como mejora parcial**.

**Hallazgo metodológico**: `_FWD_MIN_PF` estricto **NO es palanca eficaz** (validado empíricamente cross-9 con thresholds 1.1-3.0; min pf_fwd top-100 actual = 1.665 > threshold candidatos 1.3-1.5). Atacar Mecanismo 2 vía cambio criterio ranking era la palanca correcta.

**Caveat permanente §13.2**: residual ratio 2.41× requiere proyectos dedicados separados (multi-testing correction, k-fold CV) — fuera del scope Mecanismo 2 fix.

Referencias: §13.2 bloque REFINAMIENTO canónico 2026-04-24 + sub-sección "Validación M2 fix 2026-04-25", §13.3 W3 implementation 2026-04-23, §13.4 entrada "M2 fix VALIDACIÓN POST-IMPLEMENTACIÓN cross-symbol N=9 — 2026-04-25".

### Categoría C — Operacionales menores (micro-fixes + audit) — **COMPLETA 2026-04-26 (7/7 DONE)**
Scope: ~4-6h total distribuido. Estado actualizado:
- ✓ **Audit Fidelidad 2 N≥50 post-v2.3.11** **DONE 2026-04-26** — Fidelidad 2 CONFIRMADA via `_run_verify_test` 76 trades diff 0.0000.
- ✓ **Opción D pnl_recon causa raíz** **investigación DONE 2026-04-26** — double-counting `*2.0` identificado.
- ✓ **Fix v1 pnl_recon aplicado + validado** **DONE 2026-04-26** — 1 línea analyze_performance_attribution.py L1001. Validación empírica: gap mean abs 0.0218→0.0137 (-37%, predicción EXACTA), % > tolerance 90%→56.7% (-33pp).
- ✓ **L1892 active_config_id en SIGNALS_RAW** **DONE 2026-04-26** — campo `cfg` añadido en live_engine.py L565-577. Smoke §0.8 Nivel A PASS 0.0000.
- ✓ **L1904 multipliers en SIGNALS_DISCARDED** **DONE 2026-04-26** — campos vw/bf/br/dd añadidos en live_engine.py L607-625. Smoke §0.8 Nivel A PASS 0.0000.
- ✓ **Triaje 4 micro-items §13.3 (L1999, L2005, L2011, L2017)** **DONE 2026-04-26** — §12 L27 protocolo aplicado individual. Resultado: 3 mantenidos EN_ESPERA con disparadores empíricos refinados (L1999 ratio reconstructed >5% sobre N≥50, L2005 funding fallback >1% cycles, L2011 bloqueado P1 leverage); 1 ARCHIVADO obsoleto (L2017 E4 — update_trailing_stop NO-OP desde v2.4.0 elimina cancel-then-place). Hallazgo metodológico: 4/4 items quedaron stale en 9 días post-ultra-review.
- ✓ **Fase 2 secundaria pnl_recon RESUELTA Opción C** **DONE 2026-04-26** — Causa raíz IDENTIFICADA por code review: divergencia estructural de convenciones BingX `unrealizedPnl@fetch` (mark+bruto, capturado en `live/execution_manager.py:378` desde `live/data_feed.py:351`) vs analyzer reconstrucción `realized@fill` (neto con fees). Hipótesis A/B/C/D (precision/fees/notional/size_usdt) refutadas individualmente — caso instructivo causa conceptual no numérica. Decisión Opción C per §13.2: rename `pnl_recon` → `pnl_estimate_offline` + docstring convenciones expandido + gap signed preservando dirección drift + alert mecánico saturado eliminado + reporte descriptivo distribución. Validación empírica N=63: signed mean -0.0123 USDT (predicción NEGATIVO ✓), \|abs\| mean 0.0133 USDT (predicción 0.010-0.015 ✓ exacta), p95 0.0290 USDT (predicción 0.025-0.035 ✓). Bot v2.4.5 invariante. Items §13.3 L2400 + L1916 cerrados. Doc: `docs/pnl_recon_phase2_root_cause_20260426.md`.

**Items §13.3 actualizados post-Fase C 2026-04-26**:
1. ✓ "Refactor audit_v5.x herramienta auditor + reconciliación con kernel productivo Numba" — proyecto dedicado post-reciclaje, NO bloqueante. CREADO.
2. ✓ "Aplicar fix v1 pnl_recon" → **FIX_V1_APLICADO + VALIDADO 2026-04-26**. Fase 2 secundaria sigue EN_ESPERA scope ~30-45 min.

**Cambios live/live_engine.py NO deployed VPS**: cambios L1892/L1904 son observability extensions con backwards-compat. Bot v2.4.5 sigue invariante hasta próximo restart. Deploy puede esperar ventana mantenimiento o agruparse con próximo deploy operacional.

## Orden de ejecución

**Secuencial estricto** (Ricardo 2026-04-24): un hilo Claude Code activo por vez. Sin paralelización.

1. ~~**Fase B primero**: Mecanismo 2 fix.~~ **DONE 2026-04-25** (M2 fix VALIDADO empíricamente cross-symbol N=9; mean ratio 2.41×, mejora 3.42× vs W3b baseline; merge a main).
2. ~~**Fase A**: Z_BTC implementación + re-entrenamiento GMMs altcoins.~~ **DONE_ARCHIVED 2026-04-26** (Z_BTC refutado empíricamente cross-5 altcoins, BIC sweep ESCENARIO A unanimidad V0; commit `63de84c`).
3. ~~**Fase C en paralelo**~~ **DONE 7/7 2026-04-26** (audit Fid2 + investigación pnl_recon causa raíz + fix v1 + L1892/L1904 logs + triaje 4 micro-items + Fase 2 secundaria Opción C). Multi-testing correction CASO B archivado empíricamente paralelo (commit `0eb843c`, NO merge feature branch).

## Dependencias y post-reciclaje

### Categoría D — Espera datos operacionales N≥100 (~2026-05-01)
- v2.6-inv entry filter candidato — validación Welch p<0.05 S4 homogéneo obligatorio (§13.3 actualizado Fase 3 stress-test).
- ~~Cache funding extender a origen dataset (prerequisito VPS ~30 min).~~ **DONE 2026-04-26 sesión 2 §12 L27** — cache local ya cubría 2026-03-01 → 2026-04-23 08:00 desde refresh previo no documentado; sesión 2 ejecutó refresh forward gap real 2026-04-23 → 2026-04-26T16:00 (~42s VPS, 78/78 trades duration>1h cobertura 100%). Stress-tests v2.6-inv NO bloqueados por gap cache. Ver §13.4 entrada cache funding refresh 2026-04-26 sesión 2.

### Categoría E — Espera datos operacionales N≥150 (~2026-05-10)
- v2.6-exit filter candidato (cerrar contrarian losing trades).

### Post-reciclaje
- Tier 0 I1 kernel reason_exit + Bloque 2c H1+H_funding+H_strategy (proyecto dedicado ~20-30h).
- ~~Multi-testing correction formal (Bonferroni/BH/Deflated SR)~~ — **CASO B ARCHIVADO empíricamente 2026-04-26** (Holm/BH no mejoran ranking M2 fix; residual 2.41× confirmed estructural). Selection-bias-specific tools (Deflated SR López de Prado ~15-25h, k-fold CV ~20-30h, sample splitting) permanecen como proyectos dedicados separados — refinamiento mayor post-reciclaje.
- k-fold CV vs train/fwd split único — proyecto dedicado ~20-30h post-reciclaje.
- `_FWD_MIN_PF` óptimo calibrado — refinamiento menor.

## Reciclaje completo 45 símbolos

Trigger: A+B+C done + D+E validados o archivados. **Estado 2026-04-26**: A done (DONE_ARCHIVED refutado empírico) + B done (merged) + C done (7/7) — A+B+C completo. Pendiente solo D+E disparadores temporales (~2026-05-01 / ~2026-05-10).
Scope compute: ~180-225h VPS (8-10 días).
Estimación fecha: ~2026-05-12 a 05-22.

## Invariantes durante A+B+C

- Fidelidad 2 invariante (bot v2.4.5 operacional continuo).
- Sin deploy nuevos durante A+B+C salvo micro-fixes operacionales C que lo requieran explícitamente.
- Smokes pre-deploy §0.8 mandatory para cualquier cambio lab-side que genere JSONs nuevos.

## Referencias cruzadas

- §13.2 HALLAZGO ESTRUCTURAL + bloque REFINAMIENTO canónico 2026-04-24.
- §13.3 Categorías A (Z_BTC 2026-04-23), D+E (v2.6-inv/exit, cache funding), operacionales varios.
- §13.4 W3 IMPLEMENTADO 2026-04-23, W4 IMPLEMENTADO 2026-04-23, A14+A15 2026-04-23, Smoke reciclaje Bloque 5 PASS 2026-04-24, Smoke C 2026-04-24.
- §9.4 v3.0 roadmap técnico (Z_BTC contexto conceptual).
- Conversación Ricardo 2026-04-24 post-smoke (marco mecánico consolidado + criterio institucional orden).

## Actualización de este roadmap

Documento vivo. Se actualiza con:
- Mejoras adicionales identificadas durante ejecución A+B+C.
- Cambios de orden justificados.
- Cierre individual categorías (marcar DONE o ARCHIVADO con fecha).
- Re-trigger post-ejecución (reciclaje → roadmap post-reciclaje separado).

## Historia

- **2026-04-22** (`roadmap_2026-04-22.md.archived-20260424`): roadmap original categorización §13.3 N/R/C (29 items). Sustituido por criterio institucional 2026-04-24 "todas mejoras A+B+C pre-reciclaje".
- **2026-04-24**: roadmap consolidado A+B+C+D+E post-smoke reciclaje Bloque 5 + refinamiento §13.2 marco mecánico canónico.
- **2026-04-25**: Fase B DONE (M2 fix validado empíricamente cross-symbol N=9, mejora 3.42× vs W3b baseline, hallazgo metodológico `_FWD_MIN_PF` no eficaz documentado). Avanzar Fase A (Z_BTC).
- **2026-04-26**: Fase C COMPLETA 7/7 DONE — audit Fid2 + investigación pnl_recon causa raíz + fix v1 + L1892/L1904 logs + triaje 4 micro-items + Fase 2 secundaria Opción C (causa raíz convenciones BingX vs analyzer identificada por code review). Multi-testing correction Holm/BH CASO B archivado empíricamente paralelo. **Fase A DONE_ARCHIVED mismo día** (Z_BTC refutado empíricamente cross-5 altcoins BIC sweep, commit `63de84c`).
- **2026-04-26 cierre estado pre-reciclaje maduro institucional**: Fase A DONE_ARCHIVED + Fase B DONE merged + Fase C 7/7 DONE + D+E ESPERA disparadores temporales (D N≥100 ~2026-05-01, E N≥150 ~2026-05-10). Refinamiento metodológico walk-forward: Multi-testing correction CASO B archivado empírico; tools selection-bias-specific (Deflated SR, k-fold CV) pendientes proyectos dedicados separados post-reciclaje. Próximo natural: esperar disparadores temporales D+E madurando o continuación sesión institucional según oportunidad.
- **2026-04-26 sesión 2**: Cache funding refresh forward + cierre §13.3 L2317 §12 L27. Predicción ultrathink §12 L36 5ª aplicación validada profilácticamente cross-3 puntos (service mismatch trading-bot vs combolab-bot + cache parcialmente cubre + cobertura 100% por construcción). Operación efectiva: refresh forward gap real 2026-04-23 → 2026-04-26T16:00 (~42s VPS, ~306 entradas, 35 símbolos, apareció THETAUSDT.csv nuevo). Coverage 78/78 trades duration>1h con entry_ms válido 100%. Item §13.3 L2317 RESUELTO con caveat parcialmente obsoleto pre-operación. Stress-tests v2.6-inv N≥100 disparador (~2026-05-01) NO bloqueados por gap cache. Bot v2.4.5 invariante.
