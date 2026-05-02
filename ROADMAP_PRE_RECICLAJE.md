# Roadmap pre-reciclaje — consolidado 2026-04-24 (FRAME 2 SUPERSEDE 2026-04-28 sesión noche)

**Criterio institucional Ricardo 2026-04-24**: todas las mejoras (A+B+C) implementadas antes de lanzar reciclaje completo 45 sym. Categorías D+E esperan datos operacionales temporales. Reciclaje se lanza cuando A+B+C done + D+E validados/archivados.

**FRAME 2 UPDATE 2026-04-28 sesión noche** (SUPERSEDE AGGRESSIVE pura recalibrada): walk-forward methodology refinements (Deflated SR + k-fold CV) reformulados **PRE-RECICLAJE** post-cuestionamiento Ricardo "patada hacia delante" + Sesión 1A.2 Path β3 EMPIRICAL FAIL evidence (2.7% match rate vs gate 80%). Tier 0 I1 Path γ kernel granular sustituye Path α reduced enum. Cierre criterio empírico Gates A+B+C cross-9 N=9 (no calendarico). 5 sesiones Frame 2 cross-1.5-2 semanas calendario, ~12-19h CC real §12 L37. Ver sección "Pre-reciclaje Frame 2" infra + §13.4 entrada Sesión 0 Frame 2 2026-04-28 sesión noche.

**FRAME 2 REFORMULADO 2026-04-28 sesión noche-2** (Sesión 1 análisis arquitectónico): R2 k-fold CV **DESCARTADO** pre-reciclaje (H2 mal-formulada vs realidad episode-based per cluster chronological + cross-9 ONDO 0/3 R2-eligible orphan). R6 audit refactor **DIFERIDO POST-RECICLAJE** (R6_γ — state evolution divergence Path β3 fail validó Path γ alone NO replica audit pre-refactor entries-filter). R3 Path γ enum **ASIMÉTRICO TF (6) + MR (8)** — spec Sesión 0 invertida, regime_change/cancel_mr spurious. **R5 Reduced parameter space + ensemble** promovido pre-reciclaje combinado R4. Calendar reciclaje launch ~2026-05-03 invariante. Ver sección "Pre-reciclaje Frame 2 REFORMULADO" infra + §13.4 entrada Sesión 1 análisis arquitectónico 2026-04-28 sesión noche-2.

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

### Categoría D — ARCHIVED_EMPIRICAL 2026-04-27 (pre-flight refutación)

**v2.6-inv momentum filter archivado empíricamente**: pre-flight enrichment N=72 trades post-v2.4.5 reveló **subset trades `|rate|≥5e-4` = 0/72** (cobertura cache 95% N=76). Path B Sesión 3 caveat "rasgo extremo raro régimen actual" validado operacionalmente cross-arquitectura limpia. Filter NUNCA se activaría régimen actual. Extrapolación lineal N=100 disparador D ~mañana 2026-04-28: subset esperado ~0 trades. Disparador NO cambia conclusión.

Reactivable solo con cambio régimen mercado significativo (bear extremo, eventos macro, shock funding). Path B framework cross-3-exchanges metodológicamente disponible para re-validación. §13.3 L2342 ARCHIVED_EMPIRICAL_2026-04-27. Ver §13.4 entrada 2026-04-27 sesión mañana.

### Categoría E — ARCHIVED_EMPIRICAL 2026-04-27 (pre-flight refutación)

**v2.6-exit filter archivado empíricamente**: pre-flight Spearman ρ(n_bars_contrarian, pnl_pct) post-v2.4.5 N=72 = **+0.020 p=0.87** — signo OPUESTO + magnitud nula vs Bloque 2 N=50 ρ=-0.32. Triple-refutación cross-régimen confirmó Bloque 2 era artefacto contaminación pre-v2.4.4 (size_usdt=0) + pre-v2.4.5 (entry_ms=0) + ventana temporal estrecha + clusters S2+S3 sub-window concentración. Hipótesis "más tiempo contrarian = peor PnL" NO sostenida cross-arquitectura limpia.

Reactivable post-reciclaje 45 sym + k-fold CV proyecto dedicado podría re-evaluar correlación n_bars_contrarian vs PnL sobre specialists nuevos régimen mercado distinto. §13.3 L2399 ARCHIVED_EMPIRICAL_2026-04-27. Ver §13.4 entrada 2026-04-27 sesión mañana.

### Post-reciclaje
- Tier 0 I1 kernel reason_exit + Bloque 2c H1+H_funding+H_strategy (proyecto dedicado ~20-30h).
- ~~Multi-testing correction formal (Bonferroni/BH/Deflated SR)~~ — **CASO B ARCHIVADO empíricamente 2026-04-26** (Holm/BH no mejoran ranking M2 fix; residual 2.41× confirmed estructural). Selection-bias-specific tools (Deflated SR López de Prado ~15-25h, k-fold CV ~20-30h, sample splitting) permanecen como proyectos dedicados separados — refinamiento mayor post-reciclaje.
- k-fold CV vs train/fwd split único — proyecto dedicado ~20-30h post-reciclaje.
- `_FWD_MIN_PF` óptimo calibrado — refinamiento menor.
- **P1 leverage 1x feature oficial documentado lab** (proyecto post-reciclaje ~2-4h): fix bug `*100.0` `compute_leverage_map` → setear `lev=1` always con docstring explicativo. Análisis cuantitativo Fase 2 sesión 2026-04-27 tarde confirmó opción (b) empíricamente (cap 3x amplifica decay 1.61×, asimetría arquitectónica clusters ganadores maxdd alto / perdedores maxdd bajo). Reactivable solo post-reciclaje con condiciones (i)-(v) explícitas (ver §13.4 entrada P1 quantitative 2026-04-27 tarde).

## Reciclaje completo 45 símbolos

Trigger: A+B+C done + D+E validados o archivados. **Estado 2026-04-27 Sesión 2 D MADURO INSTITUCIONAL FINAL+P1+TRIAJE+AUDIT-RESCATE+AGGRESSIVE-PRE-RECICLAJE**: A done_archived + B done merged + C 7/7 done + Path B archive 2026-04-26 + D+E ARCHIVED_EMPIRICAL 2026-04-27 mañana + P1 ARCHIVED_EMPIRICAL 2026-04-27 tarde + triaje §13.3 sistemático cross-20-items 2026-04-27 tarde-noche + auditoría rescate archived 2026-04-27 cierre día + **auditoría exhaustiva pre-reciclaje + decisión Ricardo AGGRESSIVE pura recalibrada 2026-04-27 Sesión 2 D**. **Pre-reciclaje recalibrado**: 14 items pre-reciclaje confirmados cross-4-5 sesiones Claude Code (~18-26h). Trigger reciclaje 45 sym launch ~2026-05-06 a 12 cuando Sesiones 1A+1B+2+3+4 done. Reciclaje completo ~2026-05-22 a 06-05.

## Pre-reciclaje Frame 2 REFORMULADO — 2026-04-28 Sesión 1 análisis arquitectónico (SUPERSEDE Sesión 0 Frame 2 inicial)

**Estado**: PLANIFICACIÓN INSTITUCIONAL PERMANENTE post-Sesión 1 análisis arquitectónico exhaustivo + decisiones Ricardo (C) descartar R2 + R6_γ defer post-reciclaje + spec R3 Path γ TF (6) + MR (8) ASIMÉTRICO refinada.

**Origen reformulación**: §12 L38 disciplinada cross-Sesión 0+1 produciría refinamientos honestos sucesivos:
1. Sesión 0: R1 DSR approximation matemática cuestionable + cuestionamiento "patada hacia delante".
2. Sesión 1 R2 Parte 0: 6/5 mismatches arquitectónicos.
3. Sesión 1 análisis Parte 1+2+3: H2 hipótesis Sesión 0 mal-formulada + asimetría TF/MR enum + R6 specification original incompleta.
4. ~12-18h CC futile prevenido cumulative + reformulación honesta alcance Frame 2.

**Total**: 4 items pre-reciclaje (R1 + R3 + R4 + R5) cross-5 sesiones Frame 2 cross-1-2 semanas calendario, **~10-15h CC real** §12 L37.

### Sesión 1 Frame 2 — Análisis arquitectónico [DONE 2026-04-28 sesión noche-2]

- [x] **Mapeo arquitectónico** `regime_walk_forward.py` exhaustivo (2366 líneas, 36 funciones, parts files architecture, CLI args).
- [x] **Mapeo `build_regime_labels`** semantics (episode-based per-cluster chronological + toxic_tail dynamic + train_ratio default 0.70).
- [x] **Spec R3 Path γ** refinada — enum asimétrico TF (6 valores) + MR (8 valores) + 5+ sub-decisiones técnicas (m+n+o+p+P1+q) + 6 operacionales (r+s+t+u+v).
- [x] **3 escenarios Sesión 4 Gates** evaluation 3-way documentados + math sostenibilidad capital allocation.
- [x] **Decisiones Ricardo**: (C) descartar R2 + R6_γ defer post-reciclaje + R5 promovido pre-reciclaje + P1 Path γ sustituye Path α (no amend).
- [x] **Commit institucional consolidado** §13.4 + §13.3 + §13.2 + ROADMAP + Header L3 + MD5 sync.

### Sesión 2 Frame 2 — R3 Path γ kernel granular TF+MR ambos standalone (~5-6h CC, 2026-04-29) ✅ DONE

**2 sub-fases §12 L25 segmentación arquitectónica**:

**Sub-fase 2A — TF kernel Path γ** (~1.5-2h CC) ✅ DONE 2026-04-29:
- [x] **Parte 0 verificación pre-implementación** §12 L38: 2/8 mismatches detectados (D audit_mr hash check + H run_on_slice MR signature) — ambos partial, NO blocker.
- [x] Module-level constants `lab_historico_numba_v8_3.py:1272-1285` reemplazadas: Path α reduced 4 valores → Path γ granular 6 valores TF (`REASON_TF_SL_HIT/SL_EMERGENCY/DIV_EXIT/TF_EXIT/ZONE_EXIT/CANCEL_TF`).
- [x] Add 2 nuevos flags `tf_exit_signal` + `zone_exit_signal` en run_simulation_numba L1562-1585 (split de `normal_exit_signal`).
- [x] Update trade closure block L1675-1697 con 6-valor enum (sl_hit/sl_emergency split + tf_exit/zone_exit split).
- [x] Existing flags PRESERVED (sl_emergency_signal, sl_exit_signal, div_exit_signal, cancel_signal).
- [x] Per-trade arrays preserved Path α' supplement Sesión 1B amendment (9 fields incl pt_cluster).
- [x] Backward compat `return_per_trade=False` default invariante.
- [x] **Refinement §12 L38** cooldown condition Pine canonical 4-rama PRESERVED (NO add tf_exit/zone_exit a cooldown OR — análisis L1391+L1712+L1725 reveló behavior change si añadido). Smoke A diff 0.0000 valida refinement.
- [x] EXPECTED_LAB_KERNEL_HASH TF regen `02f9c480...` → `89f00b7e2291...` + audit_fidelity_v5.py:128 + audit_v5_2.py:123 updated.
- [x] Smokes §0.8 BTC Nivel A diff 0.0000 + ONDO Nivel B 22.70% IDÉNTICO baseline + APT Nivel B 1.51% IDÉNTICO baseline.
- [x] verify_test BTC ground truth 11/11 trades 5 métricas diff 0.0000 EXACTO PASS (intermedio post-2A).

**Sub-fase 2B — MR kernel Path γ** (~3-4h CC) ✅ DONE 2026-04-29:
- [x] **Parte 0 verificación**: `audit_mr_fidelity_sei.py` hash check NO existía → agregado per decisión Ricardo D-i.
- [x] Add `return_per_trade` flag-driven MR (PRIMERA VEZ MR — Sesión 1B fue TF-only) + 4 sentinel arrays MR + dispatch logic run_on_slice extension análogo Path α' supplement.
- [x] Add 5 nuevos flags MR: `tf_exit_signal_mr`, `zone_exit_signal_mr`, `cancel_zona_signal`, `cancel_tf_signal_mr`, `cancel_ghost_signal` (general `exit_signal` + `cancel_signal` PRESERVED para cooldown invariante).
- [x] Add per-trade tracking arrays MR — 8 fields (entry_bar, exit_bar, side, pnl, reason granular 8 valores, entry_price, exit_price, count) — **NO pt_cluster per decisión Ricardo H-ii** (asimetría arquitectónica honesta TF (9) ≠ MR (8) refleja MR sin cluster accounting).
- [x] Module-level Path γ MR enum constants 8 valores (sl_hit, sl_emergency, div_exit, tf_exit, zone_exit_mr, cancel_zona, cancel_tf_mr, cancel_ghost).
- [x] `run_mean_reversion_numba` signature extension: 9 nuevos kwargs.
- [x] Trade closure 8-branch decision block (priority emergency > sl_hit > div > tf_exit > zone_exit > cancel_zona > cancel_tf_mr > cancel_ghost).
- [x] **Refinement §12 L38 análogo TF**: cooldown MR Pine canonical 4-rama PRESERVED. Smoke C diff 0.0000 valida.
- [x] EXPECTED_LAB_KERNEL_HASH_MR NEW `371551bdebe328ff...` + audit_mr_fidelity_sei.py hash check agregado (D-i, ~10 min CC).
- [x] Smoke §0.8 SEI MR Nivel C diff **0.0000 EXACTO en 7 métricas** (PnL, Trades, Wins, Cancels, MaxDD, GrossProfit, GrossLoss).
- [x] verify_test cross-3-símbolos final post-2B: BTC 11/11 + ONDO 425/423 baseline + SEI 66/66 diff 0.0000.

**Tests greenfield Sesión 2** (14/14 PASS):
- [x] tests/test_path_gamma_tf.py: 7 tests TF (enum + backward compat + per-trade tracking + audit hash + W3/W4 no-regression + normal_exit split + cooldown refinement).
- [x] tests/test_path_gamma_mr.py: 7 tests MR (enum 8 valores asimétrico + backward compat + per-trade 8 fields NO cluster + audit_mr hash + cancel split + exit split + PRIMERA VEZ MR signature).

**Asimetría arquitectónica honesta documented**:
- Enum granular: TF (6) ≠ MR (8) refleja realidad cancel paths (TF 1 cancel + tf/zone splits vs MR 3 cancel + tf/zone splits).
- Per-trade arrays: TF (9 fields incl pt_cluster) ≠ MR (8 fields sin pt_cluster) refleja MR kernel intrínsecamente sin cluster accounting.

- [x] **Commit consolidado Sesión 2 Frame 2 R3 Path γ TF+MR**.

### Sesión 2.5 Frame 2 — R1 DSR rigurosa post-Path γ Opción γ→C standalone script (2026-04-29) ✅ DONE

**Decisión arquitectónica refinada §12 L37 V2** post-Parte 0 escalación: spec compute estimate "1.5-4.5h" → realidad full pipeline ~30-45h cross-3 sym + kernel re-run survivors. Pragmatic approach: Opción C standalone script synthetic returns from JSON aggregates (Multi-testing Caso B precedent + W3 bootstrap caveat) → ~5 segundos compute viable.

- [x] **R1 Deflated SR rigurosa** López de Prado 2014 implementado en `regime_walk_forward.py` (~280 líneas): scipy.stats imports + 5 funciones DSR core + orchestrator `_orchestrate_dsr_kernel_rerun` + W4 filter extension `require_not_flagged_dsr` + extract_validated_specialists DSR integration + hybrid sort gated.
- [x] Backward compat absoluto: `_R1_DSR_METHOD='none'` default → infrastructure inactive (verify_test BTC diff 0.0000 EXACTO PASS).
- [x] **§12 L38 12ª aplicación recursiva fix DSR formula one-tailed**: inicial two-tailed `2.0 × (1 - norm.cdf(|z|))` test sintético reveló bug NOISE z=-2.377 NOT flagged. Fix one-tailed right-tail per López de Prado 2014: `dsr_pvalue = 1.0 - norm.cdf(dsr_zscore)`.
- [x] Tests greenfield 7/7 PASS (`tests/test_r1_dsr_rigurosa.py`).
- [x] No-regression 27/27 PASS (W3 8/8 + W4 8/8 + M2 fix 3/3 + A14 4/4 + A15 4/4).
- [x] Standalone script `analysis_scripts/dsr_dry_run_cross_3.py` synthetic returns approach (Multi-testing Caso B precedent reusable).
- [x] Empirical dry-run cross-3 BTC+ONDO+SEI ~5 segundos compute: **1/9 top-1 changes DSR vs M2 fix (11.1%) + 88.9% flagged_dsr cross-clusters**. ONDO C0 §12 L29 canonical case detected (z_median=-1.72 + 100% flagged cluster-level — selection bias structural confirmed).
- [x] **Veredicto**: VALIDACIÓN PARCIAL H1 (NOT refutación pura análoga Caso B BH 0/9). DSR provee diagnostic value `flagged_dsr` beyond top-1 ranking; M2 fix `pf_fwd_ci_low` ya captura mayoría DSR-favored configs (8/9 top-1 alineados). R1 NOT archived — preserva methodology refinement con caveat synthetic returns documentado.
- [x] **§12 L37 V2 captura permanente**: spec compute estimates Frame 2 deben distinguir implementation pure compute vs full pipeline upstream cost.
- [x] Commit consolidado Sesión 2.5 Frame 2 R1.

### Sesión 3 Frame 2 — R4 Bloque 2c granular cross-strategy + R5 DEFERRED Opción δ (2026-04-29) ✅ DONE PARCIAL

**Decisión Ricardo Parte 0 escalación 3/6 mismatches sustantivos R5 spec ambiguity ROADMAP L162 (architectural changes) vs L219 (hypothesis testing condicional)**: Sub-fase 3A R4 PROCEDE clean + Sub-fase 3B R5 Opción δ DEFERRED post-Sesión 4 Gates condicional (preserva original Frame 2 spec L1296 design + disciplina aspirar-a-lo-mejor literal).

- [x] **R4 Bloque 2c granular cross-strategy** standalone script `analysis_scripts/r4_bloque_2c_granular_cross_strategy.py` (~390 líneas):
  - Pattern Sesión 2.5 Opción C reusable: JSONs-based + kernel re-run Path γ flag=True.
  - Hipótesis testables: H_strategy (TF cancel_tf vs MR cancel_zona/cancel_tf/cancel_ghost) + H1 (short/long Cohen d cross-cluster).
  - **H_funding DEFERRED**: funding cache cobertura ~2 meses (2026-03-01 → 2026-04-26) vs kernel runs full historical range (~2-3 años) → statistical power LOW. Reactivable post-reciclaje con extended funding cache.
  - Top-3 per cluster sorted por `pf_fwd_ci_low` (M2 fix order) + group por preset variant + per-trade arrays granular extraction (pt_pnl + pt_reason + pt_side).
- [x] Tests greenfield 6/6 PASS (`tests/test_r4_bloque_2c_granular.py`).
- [x] **§12 L37 V2 captura recurrente**: empirical compute reveal `precalculate_all_data` ~10-15 min × ~3-5 unique variants × 3 sym = **~90-225 min cumulative** full pipeline cost. Empirical R4 dry-run cross-3 BTC+ONDO+SEI **DEFERRED Ricardo manual invocation** cuando compute resources available. Pattern análogo Sesión 2.5 Opción γ original full pipeline cost trap.

- [x] **R5 DEFERRED Opción δ post-Sesión 4 Gates condicional**:
  - **L162 R5 architectural changes** (Reduced parameter space hyper-grid + ensemble cross-top-N specialists deployment): DIFERIDOS post-reciclaje proyecto dedicado análogo R6 audit refactor (NO pre-reciclaje validation viable).
  - **L219 R5 hypothesis testing condicional** (H_M3 selection bias cross-cluster + H_M4 régimen-temporal + H_M5 GMM noise + H_M6 cross-exchange): reactivable post-Sesión 4 IF Gate A FAIL Escenario 2 (~40-50% probabilidad).
  - Original Frame 2 spec L1296 design "R5 condicional Gate A FAIL" preserved. NO scope expansion sin evidence necessity.

- [x] **§12 L34 19ª aplicación recursiva**: hipótesis emergente "R5 implementable Sesión 3 pre-reciclaje" refutada vía análisis arquitectónico Parte 0 → roadmap reformulado disciplinadamente.
- [x] **§12 L38 13ª aplicación recursiva validated**: lectura disciplinada ROADMAP cross-references reveló spec internal conflict → corrección pre-implementación previno scope creep R5 architectural changes.
- [x] **§12 L36 22ª aplicación retrospectiva**: predicción "10-30 min compute" → realidad ~90-225 min ❌ refutada factor 6-8× (similar pattern Sesión 2.5).
- [x] Commit consolidado Sesión 3 Frame 2 R4 done + R5 DEFERRED.

### Sesión 3.5 Frame 2 — R4 dry-run cross-3 launched background + CLI args added (2026-04-29) ✅ DONE PARCIAL

- [x] CLI args added to `analysis_scripts/r4_bloque_2c_granular_cross_strategy.py` (`--symbols`, `--clusters`, `--top-n`, `--output`).
- [x] R4 dry-run cross-3 launched background bg `bno9hiw92`.
- [x] **§12 L37 V2 captura recurrente**: smoke BTC C2 top-1 timeout 10 min (precalculate_all_data ~10 min para 76k bars). Full cross-3 compute estimate ~90-225 min cumulative — exceeded session capacity. **Empirical R4 results DEFERRED Ricardo manual analysis post-compute**.

### Sesión 4 Frame 2 — Gates A+B+C cross-9 evaluation → Escenario 1 RECICLAJE LAUNCH VIABLE (2026-04-29) ✅ DONE

- [x] Standalone script `analysis_scripts/sesion_4_gates_evaluation.py` Gates A+B+C analytical evaluation con M2 fix baseline + R1 DSR + R3 Path γ + R4 analytical proxy.
- [x] **Gate A**: mean ratio J/B post-R1+R3+R4 cross-9 = **2.408 ≤ 3.62** (1.5× baseline 2.41) → **PASS**.
- [x] **Gate B**: 0/9 colapso fuerte cross-9 (max ratio 4.093 BTC C2 < 5.0 threshold) → **PASS**.
- [x] **Gate C**: cross-9 Spearman ρ = -0.17 NS p=0.65 (analytical proxy via cross-9 ρ stability indicator) → **PARTIAL** (per-cluster ρ requires kernel re-run Binance 3y top-100, unavailable).
- [x] **ESCENARIO 1 PASS+PASS+PASS|PARTIAL** determined → **RECICLAJE LAUNCH ~2026-05-03 VIABLE**. R5 NOT NEEDED per Frame 2 spec L1296 design preserved.
- [x] Frame 2 escenarios documented preserved (Escenario 2 R5 L219 NO needed; Escenario 3 Frame 3 NO needed).
- [x] **§12 L36 23ª aplicación retrospectiva**: predicción Sesión 1 análisis "Escenario 1 ~30-40%" → outcome confirmed.
- [x] Commit consolidado Sesión 3.5 + Sesión 4 monolítico.

### Frame 3 redesign mandatory — sequential focused (γ) → (β) → (δ) priority order (Sesión 0 Frame 3 metodológica fundamental 2026-04-29) ✅ DONE

**Decisión Ricardo Opción E sequential focused** post-Sesión 4.5 Frame 2 CONCLUSION + Gate C rigorous FAIL Escenario 3 detected empirically robust. Frame 3 alcance fundamental edge mejora real architectural changes — NO walk-forward methodology refinement scope (Frame 2 alcance).

**4 hipótesis arquitectónicas Frame 3 candidatas evaluadas**:
- α: Edge fundamental marginal limit estructural strategy actual.
- β: Strategy architectural refinements potential capture mayor edge.
- γ: Régimen detection methodology current limita capture.
- δ: Methodology selection (walk-forward + parameter sweep + reciclaje calendar) limita capture.

#### Frame 3.A focused (γ) régimen detection methodology refinement (foundation primary)

- [x] **Sesión 1 Frame 3.A análisis arquitectónica fundamental** ✅ DONE 2026-04-29: 6 candidatos γ.1-γ.6 evaluation comprehensive + scoring refined + Sub-Frame 3.A roadmap detailed (3 Sub-Frames + 1 conditional). Decision rule Opción γ gated-marginal + ablation matrix mandatory + drift threshold tiered.

- [⚠] **Sub-Frame 3.A.1 ARCHIVED_EMPIRICAL 2026-04-28** post-Sub-fase 3.A.1.2 smoke empirical reality catastrophic refuted spec methodology factor 20-30× (smoke single cell BTC ~10.7h compute + ~307 GB transient disk; full grid 84 runs ~900h ≈ 37.5 días + ~25 TB cumulative I/O). Decisión Ricardo strategic Opción F: Sub-Frame 3.A.1 archive empírico + Frame 3.A methodology fundamental redesign mandatory.
  - Sub-fases ejecutadas pre-archive: 3.A.1.0 Parte 0 (6 sustantivos + 5 sub-decisiones Ricardo) + 3.A.1.1 standalone script 664 LOC commit `4eea4ec` + 3.A.1.2 smoke launched bg `b1euswpru` killed SIGTERM PID 1791 + 3.A.1.3 tests greenfield 12/12 PASS commit `9d3f156` preserved branch.
  - Branch `sesion-1-frame-3a1-2-ablation-matrix-background-launch` preserved git history trazabilidad — NO merged main intencionalmente.
  - Sub-Frame 3.A.2 (γ.4 toxic_tail dynamic default) STATUS: pending Frame 3.A methodology redesign — re-evaluable post-Sesión 2 Frame 3.A redesign.
  - Sub-Frame 3.A.3 (γ.3+γ.5 H2 sequential coupled) STATUS: pending Frame 3.A methodology redesign.
  - Sub-Frame 3.A.4 (γ.6 HMM CONDITIONAL Frame 3.D defer) STATUS: conditional preserved.
  - Frame 2 methodology refinements infrastructure DEPLOYABLE preserved post-Frame 3.A redesign integrate.
  - **Caveat permanente Frame 3 methodology compute estimates**: empirical smoke + 5-10× safety factor over JSONs-based projections + storage/compute constraints NOT ilimitados (cognitive + tiempo ilimitados, hardware finitos).

- [⚠] **Sub-Frame 3.A.1 SUCCESSOR ARCHIVED_EMPIRICAL 2026-04-29** sesión continuación post-Sesión 2 Frame 3.A redesign methodology — methodology fundamentally REFUTED empíricamente cumulative Sub-fase B:
  - **ETAPA 1 N=6 ONDO**: 1/6 clusters valid (16.7% rate) — Cluster 0 16 episodes VALID, C1-C5 0-4 episodes INSUFFICIENT (<5 MIN_EPISODES_VALIDATE threshold). Cluster 0 top-100 Spearman ρ = -0.032 (≈ 0). Decision FAIL_GATES (Gate A FAIL ρ̅<+0.30, Gate B PASS).
  - **ETAPA 2 N=8 ONDO**: 0/8 clusters valid (0% rate CATASTROPHIC) — total 11 episodes/983 bars labeled across 8 clusters. process_symbol returned None. Decision NO_DATA. Differential signaling N=8 worse than N=6 (ONDO BIC priori knee N=8 analytical-vs-operational gap).
  - **G.0 cluster orphan investigation root cause**: Hypothesis C cluster sparsity inherent ONDO bar distribution VALIDATED EMPIRICAL. Hypothesis A (top-K too small) + B (W4 thresholds) REFUTED.
  - **5 fundamental constraints methodology Sub-Frame 3.A.1 successor identified empíricamente**:
    1. Single-symbol single-N effective sample 0-1 cluster (vs 6-8 expected).
    2. ONDO BIC priori N=8 analytical-vs-operational gap (analytical knee N=8 → operational 0/8 valid).
    3. Validation gates Gate A ≥2/3 stable+POSITIVE inherently FAIL with ≤1/3 max clusters available.
    4. Cross-symbol generalization claim impossible within single-sym scope (BTC/SEI similar bar limits).
    5. Pattern reproduces Frame 2 Gate C FAIL ranking selectivity within survivor pool unchanged.
  - **Compute estimates refuted catastrophic**: Total cumulative 31.5 min (~25 min N=6 + ~6 min N=8) vs spec ~36.75h = **factor 70× overestimated empíricamente**.
  - **Pattern match Sesión 4.5 Gate C FAIL reproducción robust**: Cluster 0 top-100 ρ=-0.032 ≈ cross-9 ρ_mean=-0.026.
  - **Sub-fase B.0 4 spec violations resolved** (commit `35a1d36`): GAMMA_1_N_VALUES extension + load_top_k_presets + run_cell signature + CLI flags + presets_dir bug fix `output/'` → `output/production/'` §12 L38 22ª + tests greenfield 5/5 PASS.
  - **Parte 0_v2 ONDO BIC sweep N=2..12** (~12s analytical zero compute): ONDO knee N=8 detected (vs BTC knee N=6) — H_AUX_1 UNFAVORABLE detected.
  - **Decisión Ricardo strategic**: Opción (δ) Hybrid commit cumulative empirical evidence + Frame 3.A meta-redesign trigger documented + defer next sesión.
  - Branch `sesion-2-frame3a-smoke-ondo-comparative-n6-n8` preserved git history trazabilidad — code potentially reusable Frame 3.A meta-redesign IF refined approach compatible.
  - **Frame 3.A meta-redesign trigger validated robust empíricamente** (D.β BOTH FAIL + D.δ Cluster orphan fundamental issue cross-N). Sub-Frame 3.A.1 ARCHIVED_EMPIRICAL precedent applied recursively al successor.

- [x] **Frame 3.A meta-redesign sesión PRIMER FOCUS DONE 2026-04-30** cumulative empirical-evidence-driven (Parte 1+2+3 + N.2 pre-requisitos empíricos foundational + commit monolítico) — análoga Sesión 2 Frame 3.A redesign methodology precedent respeted estructural recursivamente. **4 ejes Opción C Hybrid balanced reformuladas empirical-evidence-driven**: Eje 1 HMM CONDITIONAL γ.6 paradigm shift CARDINAL (smoke MANDATORY ONDO C0 ~3-5h pre-investment) + Eje 2 Cluster aggregation Outcome_C-refined intra-sym + Eje 3 Validation gates redesign per-sym proportional al k_max_op derivative + Eje 4 Cross-symbol concurrent post-HMM consensus pool. **Outcome_C per-sym adaptive MAX_K decisión productivo deferred post-Eje 1 smoke** (iii.A re-deploy bot v2.4.5→v2.5.0 vs iii.B survivor pool only). **Caveats permanentes §13.2 cumulative post-Parte 3**: BIC overfitting beyond operability (89% sym), operability cap natural < 20 cross-amplio, cluster sparsity tradeoff GENÉRICO, reproducción robusta independent ONDO, Outcome_C paradigm justificable. Ver §13.4 entrada Frame 3.A meta-redesign DONE 2026-04-30 cumulative.

- [x] **Sub-Sesión Eje 1 Opción α splits A+B+C cumulative DONE 2026-04-30 segunda sesión cross-conversación SAME calendar día** — cardinal H_meta_3 paradigm shift HMM CONDITIONAL γ.6 VALIDATED EMPIRICAL ROBUST. Splits resumen: split A `63a5ae8` custom Numba HMM 370 LOC + 15/15 tests greenfield + T6 scipy atol 1e-8; split B `c3e119b` reference comparison hmmlearn 0.3.3 venv Python 3.11 + identical-init diagnostic atol 1e-7 cross-libraries → caveat permanente §13.2 #7; split C `700cedb` Phase 1 cluster agreement 89% borderline + Phase 2A GMM baseline ρ_mean=-0.336 / HMM smoke ρ_mean=-0.0354 = **+0.301 substantial improvement** cross-3 ONDO clusters HMM_PASS_DOMINANT outcome + Gate B PASS post-HMM + C2 over-fit reversal -0.621→-0.165 + ρ_max negative→POSITIVE +0.149 + caveat permanente §13.2 #8. Caveat honest persistente: Gate A FAIL still post-HMM ρ_max +0.149 < +0.30 strict — HMM CONDITIONAL paradigm shift necesario PERO NOT sufficient → Eje 2+3+4 cumulative mandatory antes reciclaje launch foundational. Sub-fase Z.0 cierre cumulative Caveat #8 §13.2 refined generalización ONDO categoría histórico extremadamente bajo ~5K-15K bars universo 45 sym productive (NOT solo ONDO específicamente). 4 commits substantive cumulative single calendar día (`2a0e8bc` + `63a5ae8` + `c3e119b` + `700cedb`) + Z.0 cierre commit pendiente. ~6h compute background + ~7-8h CC cumulative segunda sesión.

- [x] **Sub-Sesión Eje 1 EXTENSION BTC HMM smoke pre-check Caveat #8 cross-categoría histórico validation foundational DONE 2026-05-01/02** (Opción δ Ricardo recursos ilimitados máximas garantías) — BTC full 76,018 bars sequential cumulative (~21.7h compute factor 5.45× ONDO Phase 2A) + outcome BTC_HMM_NEUTRAL_PARTIAL_CAVEAT8 con refinamiento gradient effect foundational: GMM baseline ρ_mean +0.157 → HMM smoke +0.335 = Δ +0.178 (vs ONDO Δ +0.301 attenuated 59% ceiling effect) + ρ_min +0.233 (primer all positive cross-cluster cumulative cross-Sesiones) + ρ_max +0.473 (primer approaching strong +0.40). **Caveat #8 hypothesis VALIDATED CON refinamiento gradient effect** — paradigm shift HMM γ.6 generaliza cross-categoría histórico magnitud baseline-dependent. BTC GMM baseline +0.157 vs ONDO GMM −0.336 = +0.493 diferencia ranking selectivity baseline pre-paradigm-shift directly validates Caveat #8. Caveat #9 §13.2 nueva §0.7 sync convención desactivada empírico documental (post-Sub-fase O.0 verificación primary source 2026-05-01 comboclaude/ contiene solo .claude/ + .gitignore). Strategic implications: Eje 4 cross-symbol concurrent empirically PRIORITIZED vs Eje 2 ceiling effect refined — decisión Ricardo strategic deferred post-commit escalación.

- [ ] **Sub-Sesión Eje 2 Cluster aggregation próxima Sub-Sesión Claude Code futura** cuando Ricardo confirme disponibilidad — natural next step closing remaining gap ranking selectivity (ONDO HMM ρ_mean -0.0354 + BTC HMM ρ_mean +0.335 cumulative cross-categoría) toward Gate A target. Smoke MANDATORY ONDO post-aggregation ranking selectivity vs Phase 2A HMM-only baseline. Compute estimate ~2-4h (similar Phase 2A pattern ~120 min × 2 walks). **Strategic re-prioritization post-Sub-Sesión Eje 1 extension Caveat #8 cross-categoría validation cumulative**: Eje 4 cross-symbol concurrent empirically prioritized vs Eje 2 ceiling effect refined — decisión Ricardo deferred.

- [ ] **Sub-Sesión Eje 4 Cross-symbol concurrent post-Eje 2 outcomes** pooled BTC+ONDO+SEI same-cluster post-HMM consensus régimen pool effective ≥3-4× single-sym. Mitigates histórico corto sparsity vía sample size aggregation cross-sym + caveat 2 anexo L.0 estabilidad regímenes. Compute estimate ~2-4h.

- [ ] **Sub-Sesión Eje 3 Validation gates redesign derivative ratificar empirical post-Eje 1+2+4 outcomes** — criterio per-sym proportional al k_max_op (amplio ≥6/12, medio ≥5/11, corto ≥3/8) + pool-level cross-sym AND per-sym intra-sym aggregated supercluster two-tier criterion.

- [ ] **Sub-decisión Outcome_C productivo decisión strategic Ricardo (iii.A re-deploy bot v2.5.0 vs iii.B survivor pool methodology only)** post-cumulative empirical evidence Eje 1+2+3+4 complete.

- [ ] **Phase 2B N=k_max_op deferred Sub-Sesión Eje 1 split D dedicated post-Eje 2 outcomes** — validation cross-N adaptive MAX_K productivo (ONDO N=4 k_max_op vs N=3 productive HMM impact cross-N).
  - **VALIDATED ROBUST EMPÍRICAMENTE** post-Sub-Frame 3.A.1 successor ARCHIVED_EMPIRICAL (5 fundamental constraints) + Sub-fase H.0 §12 L38 26ª aplicación recursiva 3/3 cross-conversation pendientes legacy framework REFUTED 100% systematic pattern (perfil de extremos + walk-forward `--opt-size`/`--fwd-size` + Market Regime Clustering 457 metrics ALL legacy March 15-20 pre-Frame 2/3 reformulation April 22+).
  - **§12 L38 verification primary source MANDATORY pattern institutional permanente**: cualquier pendiente cross-conversation memory claim Ricardo futuro requiere verificación primary source antes spec investment — pattern §12 L38 cross-26ª aplicaciones recursivas cumulative validated robust 6 applications cross-conversación 2026-04-29.
  - **§12 L34 cross-44ª aplicación recursiva al own pendientes memoria persistente**: mi memoria persistente cross-conversaciones systemic limitation acknowledged honest disciplinada — NOT reliable source pendientes scope actual current methodology cualquier pendiente.

  **Parte 0 preliminary sub-decisiones Ricardo cumulative substantive 2026-04-29 cross-conversación nueva hoy DONE Sub-fase J.0** (pattern Sesión 2 Frame 3.A redesign methodology precedent respeted estructural — NO standalone memory file ephemeral, persistente Header L3 + ROADMAP + §13.4 appendix):

  - **Sub-decisión 1: re-evaluación 6 candidatos γ.1-γ.6 cumulative empirical evidence honest disciplinada**:
    - **γ.1 GMM cluster N adaptive**: ❌ DEPRECATED standalone (BIC priori transferred ONDO UNFAVORABLE H_AUX_1 + cluster sparsity inherent ONDO N=6 1/6 + N=8 0/8 catastrophic).
    - **γ.2 P_threshold adaptive**: ❌ DEPRECATED standalone (FAIL_GATES + cluster sparsity inherent makes P_threshold tuning futile).
    - **γ.5 Z_ATR_BTC cross-symbol feature**: ❌ DEPRECATED standalone (depends γ.3 + γ.1 framework superseded; cluster aggregation prerequisite).
    - **γ.3 Cross-exchange Binance↔BingX consistency H_M6**: ⚠️ ARCHIVED ROBUSTLY (cluster sparsity inherent makes irrelevante primary methodology refinement; re-evaluable post-meta-redesign).
    - **γ.4 Régimen transition handling toxic_tail dynamic default activate**: ⚠️ SUBJECT cluster sparsity resolution (toxic_tail dynamic ya implementado ETAPA 1+2 verified pero cluster sparsity precludes effective regime transition handling until cluster aggregation strategy resuelve).
    - **γ.6 HMM/regime-switching**: ✅ **PROMOTED PRIORITY HIGH paradigm shift architectural fundamental** (addresses cluster sparsity inherent via probabilistic regime persistence + smoother transitions vs hard GMM hard-classification; aligns Sub-Frame 3.A.4 conditional Frame 3.D originally documented; Markov regime persistence paradigm fundamentally different current methodology).

  - **Sub-decisión 2: approach preliminary Frame 3.A meta-redesign Opción (C) Hybrid balanced architectural rethink integrated**:
    - (A) Single-issue refinement validation gates only — REJECTED insufficient.
    - (B) Full architectural rethink HMM + everything redesigned standalone — REJECTED scope catastrophic.
    - **(C) Hybrid balanced architectural rethink integrated** — SELECTED preliminary:
      - Cluster aggregation strategy: pool sparse clusters cross-N OR cross-sym recover validation power.
      - HMM CONDITIONAL paradigm shift: probabilistic regime persistence vs hard GMM clustering.
      - Validation gates redesign: criterio empirical adapted cluster sparsity inherent.
      - Cross-symbol concurrent validation: alternative single-symbol single-N.

  - **Sub-decisión 3 refined: Header L3 + ROADMAP + §13.4 appendix update sub-decisiones persistente cross-conversation memory mandatory pre-Frame 3.A meta-redesign sesión PRIMER FOCUS PRÓXIMA** (pattern Sesión 2 Frame 3.A redesign methodology precedent respeted estructural — memory file ephemeral REMOVED post-Parte 3 commit pattern preserved).

  **Frame 3.A meta-redesign sesión PRIMER FOCUS scope refined Parte 1+2+3**:
  - **Prerequisito de lectura mandatory pre-Parte 1 (Sub-fase K.0 refinamiento canónico 2026-04-29 + Sub-fase L.0 anexo estabilidad regímenes 2026-04-29)**: §0.0 CONTEXTO_PROYECTO_TRADING.md "Objetivo del proyecto: identificación honesta de configuraciones notables dentro del universo de candidatas" **incluyendo el sub-bloque "Estabilidad estructural de regímenes y horizonte foundational del reciclaje"** + §13.2 bloque "REFINAMIENTO CANÓNICO 2026-04-29 — Objetivo del proyecto correctamente formulado" **incluyendo el anexo Sub-fase L.0** + `memory/objetivo_proyecto_identificacion_honesta.md` **incluyendo sección homónima estabilidad regímenes**. Las cuatro mejoras Opción (C) Hybrid balanced son **mejoras a la capacidad de identificación dentro del universo de candidatas (~10¹⁰ configuraciones)**, NO intentos de mejorar el sistema en abstracto. Cuantificación verificada empíricamente: 26 bits / 20.9M combos válidas / ~30 presets media / 45 símbolos primary source. Origen Ricardo conversación 2026-04-29 sesión continuación post-Sub-fase J.0.
  - **Contexto adicional para eje cross-symbol concurrent validation (Sub-fase L.0)**: el anexo §0.0 estabilidad regímenes articula explícitamente que la estacionariedad aplica robustamente a símbolos con histórico amplio (BTC ~9 años a 1h) pero menos directamente a símbolos con histórico corto (ONDO ~1 año, SEI ~2 años, APT ~3 años) — los clusters detectados sobre histórico corto pueden capturar patrones idiosincráticos del período disponible, no estructura estacionaria genuina. **Esto justifica directamente el eje cross-symbol concurrent validation de la Opción (C) Hybrid balanced**: extraer estructura compartida entre símbolos para aumentar el sample size efectivo más allá del límite single-symbol histórico y mitigar overfitting a particularidades de períodos cortos. Adicionalmente la distinción cierre foundational vs ciclo operacional posterior (con re-evaluación periódica + monitoreo assignment + detección outliers + re-clustering condicional vigentes) precisa el alcance del "reciclaje definitivo" para evitar interpretaciones erróneas de inmutabilidad operacional perpetua cross-Sesiones futuras.
  - **Parte 1**: análisis código real cumulative empirical evidence ETAPA 1 + ETAPA 2 + G.0 + 3/3 pattern + HMM CONDITIONAL theoretical foundation Markov regime persistence (~1-2h CC).
  - **Parte 2**: hipótesis emergentes integrated cluster aggregation strategy + HMM CONDITIONAL paradigm shift + validation gates redesign + cross-symbol concurrent validation alternative (~30-45 min CC).
  - **Parte 3**: reformulación spec Frame 3.A meta-redesign integrated + commit monolítico merged main (~30-45 min CC).

  - **§12 L34 cross-45ª aplicación recursiva al own 6 candidatos γ.1-γ.6 cumulative empirical evidence** honest disciplinada applied — re-evaluation grounded cumulative empirical evidence Sub-Frame 3.A.1 successor ARCHIVED + 3/3 pattern + cluster sparsity Hypothesis C VALIDATED.
  - **§12 L36 42ª aplicación prophilactic predicción** Frame 3.A meta-redesign sesión PRIMER FOCUS approach preliminary Opción (C) Hybrid balanced more promising standalone — calibration retrospective post-sesión pendiente.

  Sub-Frames 3.A.2 (γ.4 toxic_tail) + 3.A.3 (γ.3+γ.5) + 3.A.4 (γ.6 HMM CONDITIONAL) STATUS pending Frame 3.A meta-redesign — re-evaluable post-meta-redesign sesión. **γ.6 HMM PROMOTED PRIORITY HIGH paradigm shift integrated Opción (C) Hybrid balanced** — Sub-Frame 3.A.4 originalmente conditional Frame 3.D defer ahora foundation Frame 3.A meta-redesign primer focus.

  Reciclaje launch new calendar TBD post-Frame 3.A meta-redesign sesión + validation gates evaluation methodology refined.

- [⚠] **Pendientes memoria persistente cross-conversaciones DEPRECATED honest disciplinada** — 3/3 cases REFUTED legacy framework pre-Frame 2/3 reformulation (Sub-fase H.0 §12 L38 26ª aplicación recursiva 2026-04-29):
  - **"Perfil de extremos" en `analyze_train_test.py`** (§12 L38 24ª REFUTED Sub-fase E.0) — script archived `antiguos de referencia/` March 20 + data `wf_full/dataset_labeled.parquet` does NOT exist + multi-anchor methodology legacy.
  - **Walk-forward second experiment `--opt-size 8000 --fwd-size 2000`** (§12 L38 26ª-A REFUTED Sub-fase H.0.1) — flags exist `walk_forward_experiment.py:16` + `walk_forward_v1.py:1185` archived; current `regime_walk_forward.py` Frame 2/3 uses `--train-ratio` single train/fwd split.
  - **Market Regime Clustering ~457 metrics** (§12 L38 26ª-B REFUTED Sub-fase H.0.2) — "457" only matches `config_id` literals; methodology + data NOT FOUND current Frame 3.A.
  - Pattern systematic 100% rate detected empíricamente cross-3-cases — cross-conversation memory cross-temporal framework changes invalidates references unless re-validated. Ver `memory/feedback_cross_conversation_memory_verification.md` para detalle institutional consolidated robust.

- [⚠] **Sesión 2 Frame 3.A redesign methodology DONE 2026-04-29** (commit `c6ad5ce` HISTÓRICO) post-Sub-Frame 3.A.1 ARCHIVED_EMPIRICAL — Parte 0 ayer cumulative 7 sub-decisiones + BIC sweep N=2..12 BTC empirical (knee N=6 defensible) + Parte 1 substantive análisis arquitectónica fundamental cross-5 refinements integrados (4-axis decomposition Refinements OVERLAP non-orthogonal §12 L38 19ª aplicación) + Parte 2 hipótesis emergentes + 4 H_AUX flagged + 5 sub-decisiones cumulative (a)-(e) + Parte 3 commit monolítico. **Sub-Frame 3.A.1 successor scope refined consolidated** (HISTÓRICO superseded by Sub-Frame 3.A.1 SUCCESSOR ARCHIVED_EMPIRICAL above):
  - **Axis A γ.1 N**: Priori N=6 BIC (DONE Parte 0 BTC + Parte 0_v2 ONDO BIC ~70s pendiente sub-decisión b).
  - **Axis B γ.2 P**: Targeted grid 7 values {0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85} (NOT Bayesian — O4).
  - **Axis C Symbol**: ONDO single-symbol (NOT BTC — O1 better signal detection STRONG NEG C2 + sig C0).
  - **Axis D Presets**: Top-10 pf_fwd_ci_low M2 fix ranking (caveat O2 + H_AUX_4).
  - **Compute estimate refined**: 7 cells × 1 sym × ~3.75-5.25h N=6 ≈ ~26-37h baseline + safety 5-10× = ~130-370h cumulative cross-multiple sesiones (vs ~900h original 2.4-6.9× reduction; storage ~1 TB vs ~25 TB 24-37× reduction).
  - **8 caveats explícitos documentados honest** (O1 generalization ONDO → cross-symbol limited / O2 top-10 selection-bias regression to mean / O3 H1 architectural coupling indirect validation / O4 1D grid simpler reproducible / H_AUX_1 ONDO BIC NOT validated → resuelto Parte 0_v2 / H_AUX_2 toxic_tail × P_threshold interaction track usable_bars per cell / H_AUX_3 ONDO C2 STRONG NEG deeper mechanism ~50-65% persists / H_AUX_4 top-10 cross-baseline mismatch).
  - **§12 L36 31ª prophilactic predicción** registered explícitamente pre-execution: STRONG ρ_mean > +0.40 5-10% / MARGINAL [+0.30, +0.40] 10-15% / WEAK [+0.10, +0.30] 15-25% / FAIL Gate A 30-40% / FAIL Gate B 25-40% / Combined FAIL_GATES ~55-80% most likely outcome.
  - **Validation gates adapted single-sym ONDO 3 clusters**: ≥2/3 stable+POSITIVE primary + 3/3 sign positive secondary, ρ_mean cross-3 deprecated NOT robust single outlier 3× weight inflation.
  - **Decision rule Opción γ gated-marginal preserved adapted**: STRONG cross-3 ONDO > +0.40 + Primary criterion → early-exit reciclaje launch. MARGINAL [+0.30, +0.40] + Primary → Sub-Frame 3.A.2+3.A.3. WEAK <+0.30 → Sub-Frame 3.A.4 Frame 3.D HMM defer. FAIL_GATES → Frame 3.A meta-redesign mandatory (Sub-Frame 3.A.1 ARCHIVED_EMPIRICAL precedent).

- [ ] **Parte 0_v2 ONDO BIC sweep N=2..12 ~70s zero compute analytical** PRÓXIMA cuando Ricardo confirme (resuelve H_AUX_1 ONDO N_optimo NOT validated transferred BTC asumed).

- [ ] **Smoke minimal 1 cell ONDO N=6 P=0.75 baseline ~3-5h compute MANDATORY** post-Parte 0_v2 (sub-decisión e — pattern Sub-Frame 3.A.1 ARCHIVED_EMPIRICAL precedent applied: ~5h cost vs ~130-370h full investment savings IF infeasibility detected pre-emptive).

- [ ] **Full execution Sub-Frame 3.A.1 successor 7 cells × ONDO × N=6 × top-10 ~130-370h cumulative cross-multiple sesiones** CONDITIONAL Parte 0_v2 + smoke PASS — ELSE scope re-evaluation Frame 3.A meta-redesign pre-investment savings.

**Sub-Frame 3.A roadmap detailed (Sesión 1 Frame 3.A output)**:

##### Sub-Frame 3.A.1 ORIGINAL (γ.1 + γ.2 H1 architectural coupling combined exhaustive grid) — ARCHIVED_EMPIRICAL 2026-04-28
- [⚠] Sub-Frame 3.A.1 ORIGINAL spec ARCHIVED_EMPIRICAL post-smoke catastrophic factor 20-30× refutación (~900h compute + ~25 TB I/O cumulative). Branch `sesion-1-frame-3a1-2-ablation-matrix-background-launch` preserved trazabilidad NO merged main. Sub-Frame 3.A.1 SUCCESSOR scope refined Sesión 2 Frame 3.A redesign methodology (4-axis decomposition + 8 caveats + minimal smoke pre-execution validation MANDATORY) — ver sección "Sesión 2 Frame 3.A redesign methodology DONE 2026-04-29" arriba para scope refined consolidated.

##### Sub-Frame 3.A.2 (γ.4 toxic_tail dynamic default) — POST-Sub-Frame 3.A.1 conditional Opción γ
- [ ] **Sub-fase 3.A.2.0 Parte 0** verify toxic_tail dynamic implementation Frame 2 baseline (regime_walk_forward.py:282-406).
- [ ] **Sub-fase 3.A.2.1 activation default mode**: change default `--toxic-tail` arg fixed → dynamic. Defaults `confirm_threshold=0.75, min_toxic_tail=5, max_toxic_tail=100`. Backward compat `--toxic-tail 0` disable.
- [ ] **Sub-fase 3.A.2.2** walk-forward ablation tests 3 condiciones (fixed=0 baseline + fixed=50 + dynamic) + Spearman ρ stability + empirical edge comparison.
- [ ] **Sub-fase 3.A.2.3** validation gates Frame 3.A.2.A/B/C stricter.
- [ ] **Sub-fase 3.A.2.4** commit monolítico.
- **Scope**: ~1-2 sesiones cumulative ~4-8h CC + ~5-10h compute ablation.

##### Sub-Frame 3.A.3 (γ.3 + γ.5 H2 sequential coupled) — POST-Sub-Frame 3.A.1 + 3.A.2 conditional Opción γ
- [ ] **Sub-fase 3.A.3.0 Parte 0** verify Z_ATR_BTC = 0 hits source actual + precompute_btc_features.pyc origen.
- [ ] **Sub-fase 3.A.3.1 γ.3 cross-exchange consistency validation**: download BingX BTC histórico ≥1y + recompute Hurst + Z_ATR + ER cross-exchange Binance vs BingX + quantify drift mean/median/p95 absolute deviation per feature. **Bifurcación crítica gate γ.3 tiered** (Ricardo confirmed): <1% drift confident proceed γ.5 / 1-5% caveat documented proceed γ.5 / ≥5% γ.5 honest-abandoned o restructured BingX-only training.
- [ ] **Sub-fase 3.A.3.2 γ.5 Z_ATR_BTC implementation CONDITIONAL** (post-γ.3 validation): implement `regime_features.py` USE_4TH_FEATURE redefine (Z_ATR_BTC vs Z_Vol) + decode `precompute_btc_features.pyc` o reimplement source clean + retrain GMM 3-symbols + BIC comparison + Spearman cross-symbol contribution.
- [ ] **Sub-fase 3.A.3.3** tests + validation gates Frame 3.A.3.A/B/C stricter.
- [ ] **Sub-fase 3.A.3.4** commit monolítico (incluye γ.3-only outcome si γ.5 abandoned).
- **Scope**: ~3-4 sesiones cumulative ~12-18h CC + ~15-30h compute moderado.

##### Sub-Frame 3.A.4 (γ.6 HMM CONDITIONAL Frame 3.D defer) — LAST-RESORT IF Sub-Frames 3.A.1 + 3.A.2 + 3.A.3 cumulative FAIL
- **Activation criterion**: Sub-Frame 3.A.1 + 3.A.2 + 3.A.3 cumulative FAIL Gate C rigorous re-evaluation.
- **Defer Frame 3.D dedicated session** — NOT within Frame 3.A scope.
- **Scope**: ~5-8 sesiones cumulative ~25-40h CC + +substantial compute.

##### Decision rule Opción γ gated-marginal documented explícito (Ricardo confirmed Sesión 1 Parte 2)
- Sub-Frame 3.A.1 ejecuta primero + Gate C rigurous re-evaluation.
- IF Gate C PASS + STRONG signal (ρ_mean cross-9 > 0.4): early-exit considered + reciclaje launch.
- ELIF marginal PASS (ρ_mean ∈ [0.3, 0.4]): proceed 3.A.2 + 3.A.3 reinforcement.
- ELIF FAIL: Sub-Frame 3.A.4 conditional activation last-resort defer Frame 3.D.

##### Validation gates analogía Frame 2 stricter criterion (per Sub-Frame 3.A.X)
- **Gate Frame 3.A.X.A**: ≥6/9 stable+POSITIVE (NOT just |ρ|≥0.3 sign consistent — stricter than Frame 2 Gate C original).
- **Gate Frame 3.A.X.B**: 0/9 STRONG NEGATIVE over-fit (vs Sesión 4.5 baseline 2/9).
- **Gate Frame 3.A.X.C**: PF empírica cross-9 ≥1.2 baseline real edge (§13.2 framing).

- **Frame 3.A cumulative scope total refined**: Sub-Frames 3.A.1 + 3.A.2 + 3.A.3 = ~7-10 sesiones cumulative ~28-44h CC + ~50-100h compute background. Sub-Frame 3.A.4 conditional = +5-8 sesiones cumulative IF needed.

#### Frame 3.B focused (β) strategy architectural refinements (post-Frame 3.A conclusion)

- [ ] Cross-strategy ensemble combinaciones (R5 L162 architectural):
  - [ ] Reduced parameter space hyper-grid (preset families × hyst) ~50% reducción configs sweep.
  - [ ] Ensemble cross-top-N specialists per cluster brain/portfolio_manager deployment.
- [ ] Indicator selection criteria architectural refinement.
- [ ] Multi-timeframe filter refinement architectural per régimen.
- [ ] Funding-aware strategy selection (H_funding architectural).
- **Scope estimated**: 3-4 sesiones cumulative (~15-25h CC + compute background substantial).

#### Frame 3.C focused (δ) methodology selection redesign (post-Frame 3.A + 3.B)

- [ ] Walk-forward methodology fundamental redesign:
  - [ ] Train/fwd ratio refinement architectural (current 0.70 default).
  - [ ] Multi-window walk-forward (rolling vs static fwd window).
  - [ ] Cross-validation methodology integrated (k-fold CV reformulado post-Frame 3.A + 3.B).
- [ ] Parameter sweep architectural redesign:
  - [ ] Reduced parameter space + smart sampling (Frame 3.B integration).
  - [ ] Bayesian optimization vs exhaustive search ~4M combinations.
- [ ] Reciclaje calendar architectural refinement:
  - [ ] Adaptive reciclaje trigger per pair drift detection.
  - [ ] Continuous learning architectural changes.
- **Scope estimated**: 3-5 sesiones cumulative (~15-30h CC + compute background substantial).

#### Frame 3 conclusion outcomes posibles documented

| Escenario | Outcome | Decisión |
|-----------|---------|----------|
| F3.1 | Edge mejora real validated robust cross-Sub-Frames | Reciclaje launch new methodology + bot reproduces edge mejora |
| F3.2 | Edge mejora real validated parcial | Frame 3 deployable + decisión Ricardo strategic capital scale-up vs continued refinement |
| F3.3 | Edge mejora real refutado robust cross-Sub-Frames | Hipótesis α validated + decisión Ricardo strategic + reciclaje launch Frame 2 refinements deployable |

#### Frame 2 methodology refinements infrastructure DEPLOYABLE post-Frame 3 OR independent reciclaje (escenario F3.3 confirmation)

- M2 fix sort + W3 bootstrap CI + W4 thresholds.
- R3 Path γ kernel granular ASIMÉTRICO TF (6) + MR (8).
- R1 DSR rigurosa diagnostic flagged_dsr column + filter optional `_R1_DSR_REQUIRE_NOT_FLAGGED=True` activable.
- R4 standalone analytical cross-strategy decomposition.

#### Reciclaje launch new calendar TBD post-Frame 3 redesign architectural deployment + validation gates analogous Frame 2 Gates A+B+C cross-9 evaluation rigorous

### Sesión 5 Frame 2 — Reciclaje launch (~2026-05-03) — **SUSPENDED post-Sesión 4.5 Gate C rigorous FAIL** → Frame 3 redesign mandatory

### Sesión 4.5 Frame 2 — Gate C rigorous analytical FAIL → Escenario 3 → Frame 3 redesign trigger (2026-04-29) ✅ DONE

**Decisión Ricardo Opción A**: Frame 3 redesign mandatory + reciclaje launch DEFERRED. Disciplina aspirar-a-lo-mejor literal applied al own Frame 2 conclusion.

- [x] Standalone script `analysis_scripts/gate_c_rigorous_analytical.py` per-cluster Spearman ρ(pf_tr, pf_fwd) cross-9 BTC+ONDO+SEI × C0+C1+C2 from JSONs metadata directly (zero compute cost).
- [x] **Per-cluster Spearman ρ table cross-9**:
  - BTC C0/C1/C2: ρ=+0.185 NS / -0.004 NS / +0.013 NS (all noise).
  - ONDO C0/C1/C2: ρ=+0.221 * / +0.044 NS / **-0.502 *** STRONG NEGATIVE over-fit**.
  - SEI C0/C1/C2: ρ=+0.127 NS / **-0.363 *** STRONG NEGATIVE over-fit** / +0.046 NS.
- [x] **Cross-9 aggregates**: mean ρ -0.026 (~null); 2/9 stable ambos NEGATIVE over-fit; 0/9 stable+positive (Gate C strict ≥+0.30 sig FAIL); 3/9 sign reversals.
- [x] **Gate C verdict**: **FAIL** strict criterion (0/9 ρ≥+0.30 sig).
- [x] **Frame 2 escenarios re-evaluation rigorous**:
  - Escenario 1 (PASS+PASS+PASS, ~30-40%) → **REFUTED empirically**.
  - Escenario 3 (Gate B/C FAIL, ~15-25%) → **DETECTED EMPIRICALLY ROBUST** ✓
- [x] **§12 L34 cross-20ª aplicación recursiva al own Frame 2 conclusion**: Sesión 4 analytical proxy gave optimistic PARTIAL → Sesión 4.5 rigorous reveals empirical FAIL strict criterion. Honest scrutiny prevents Frame 2 launch on flawed Gate C foundation.
- [x] R4 empirical Sesión 3.5 dry-run DEFERRED §12 L37 V2 cumulative refutado cross-3 intentos previos (Sesión 2.5 + Sesión 3 + Sesión 3.5): precalculate_all_data upstream cost dominante NO escapable bg mode.

### Frame 3 redesign session subsequent (calendar TBD post-Frame 3 análisis arquitectónica fundamental)

**Scope**: arquitectura análisis fundamental edge mejora real architectural changes (NO walk-forward methodology refinement scope).
- Cross-strategy ensemble combinaciones R5 L162 (Reduced parameter space + ensemble cross-top-N specialists).
- Revisión fundamental régimen detection methodology.
- Edge mejora real architectural changes scope ~10-30h CC + compute background substantial estimated.
- Calendar TBD post-Frame 3 análisis arquitectónica fundamental.

### Frame 2 methodology refinements infrastructure DEPLOYABLE post-Frame 3 redesign integrate

- M2 fix sort `pf_fwd_ci_low` primary + `specialist_score_ci_low` tie-breaker.
- W3 bootstrap CI (`_apply_bootstrap_pf_fwd` + `flag_sospechoso_outlier`).
- W4 thresholds (`_FWD_MIN_TRADES=25`, `_FWD_MIN_PF=1.1`, `_FWD_REQUIRE_NOT_SOSPECHOSO=True`).
- R3 Path γ kernel granular ASIMÉTRICO TF (6) + MR (8) per-trade arrays.
- R1 DSR rigurosa diagnostic flagged_dsr column.
- R4 standalone analytical cross-strategy decomposition.

Walk-forward ranking selectivity within survivor pool unchanged empíricamente — Frame 3 redesign requires architectural changes fundamental.

### Sesión 4 Frame 2 — Gates A+B+C cross-9/cross-15 + decisión Ricardo strategic (~1-2h CC + ~30-60 min compute, ~2026-05-01 a 02)

**Gates evaluation criterio empírico cierre Frame 2**:
- [ ] **Gate A — Predictive correlation**: Spearman ρ(pf_fwd_JSON_top1, pf_operational_post-reciclaje) ≥ +0.30 sig p<0.05 cross-9.
- [ ] **Gate B — Magnitud sobrestimación**: mean ratio J/B ≤ 1.5× cross-9 (vs baseline M2 fix 2.41×).
- [ ] **Gate C — Edge real revelado**: top-1 pf_fwd JSON mean ≥ 1.5 + ≥6/9 sym pf_fwd > 1.5.
- [ ] Cross-15 expansión opcional: BTC+ETH+ADA+SOL+ONDO+SEI × C0+C1+C2 = 18 cluster-sym pairs.

**3 escenarios decisión Ricardo strategic**:
- [ ] **Escenario 1 PASS+PASS+PASS** (~30-40%): reciclaje launch confidence alta.
- [ ] **Escenario 2 PASS+PASS+FAIL_C** (~40-50% most likely): reciclaje methodology honest + decisión capital scale-up vs Frame 3 pivot.
- [ ] **Escenario 3 FAIL_A** (~15-25%): Frame 3 redesign mandatory + reciclaje pospuesto ≥3 meses.

### Sesión 5 Frame 2 — Reciclaje 45 sym launch (~30 min preparation + ~15 días background lab local, ~2026-05-03)

- [ ] Validation gates: bot v2.4.5 invariante + Gates A+B+C decision Ricardo + Smoke Nivel B sistemático done.
- [ ] Reciclaje 45 sym launch.
- [ ] Reciclaje ejecución background lab local (~15 días compute).

### Post-reciclaje proyecto dedicado — R6 audit refactor (~6-10h CC)

- [ ] R6 audit refactor Path β1 entries-filter (preserva audit stateless property pre-refactor) — proyecto dedicado L1721 disparador original.

**R2 k-fold CV — DESCARTADO pre-reciclaje** (H2 mal-formulada vs realidad arquitectónica episode-based per cluster chronological + cross-9 ONDO 0/3 R2-eligible orphan).

---

## Pre-reciclaje Frame 2 — 2026-04-28 Sesión 0 metodológica fundamental (SUPERSEDED por Sesión 1 análisis arquitectónico 2026-04-28 sesión noche-2)

**Estado**: PLANIFICACIÓN INSTITUCIONAL PERMANENTE bajo enfoque Ricardo "al margen de lo que cueste, aspirar a lo mejor reciclaje" + **walk-forward methodology completa pre-reciclaje** (no diferida post como AGGRESSIVE).

**Origen reformulación**: cuestionamiento Ricardo "patada hacia delante" (refinamientos pospuestos repetidamente L1721 audit + L2336 multi-testing + L2621 Tier 0 I1) + Sesión 1A.2 Path β3 EMPIRICAL FAIL (2.7% match rate vs gate 80%, ROLLBACK clean main `f8205fa`). Frame 2 ataca walk-forward methodology completa ANTES no DESPUÉS reciclaje.

**Total**: 6 items pre-reciclaje (R1-R6) cross-5 sesiones Frame 2 cross-1.5-2 semanas calendario, **~12-19h CC real §12 L37** (vs estimación humana naive ~50-100h).

### Sesión 1 Frame 2 — R1 Deflated SR + R2 k-fold CV walk-forward (~2-4h CC, ~2026-04-28 noche)

- [ ] **R1 Deflated SR** (López de Prado 2014): rama `sesion-1-frame2-r1-deflated-sr`. Implementar `_compute_expected_max_sr` + `_compute_deflated_sr_vectorized` + `_apply_deflated_sr` en `regime_walk_forward.py`. Integration post-W3 bootstrap pre-W4 thresholds. Re-sort hybrid `pf_fwd_ci_low + dsr_zscore` tie-breaker. Tests greenfield (7 tests). Dry-run cross-9 over JSONs smoke 2026-04-24.
- [ ] **R2 k-fold CV walk-forward**: continuar misma rama (R1+R2 commit juntos). Implementar `_compute_kfold_cluster_labels` + `_compute_kfold_specialist_score` + `extract_validated_specialists_kfold`. 5-fold rolling preservación temporal order (no shuffle puro). Backward-compat flag `_R2_USE_KFOLD=False` default. Tests greenfield (5 tests).
- [ ] Smoke §0.8 obligatorio cross-cuatro símbolos invariante baselines pre-merge.
- [ ] Commit consolidado Sesión 1 Frame 2 R1+R2.

### Sesión 2 Frame 2 — R3 Tier 0 I1 Path γ kernel granular + R6 audit refactor Opción A clean post-Path γ (~4-7h CC, ~2026-04-29)

- [ ] **R3 Tier 0 I1 Path γ kernel granular** (sustituye Sesión 1B Path α reduced enum): enum extendido sl_emergency/sl_hit + cancel_zone/cancel_ghost + tf_exit/zone_exit separados + regime_change brain-side propagación. Preserva state evolution per-cluster (mitigación causa raíz Path β3 FAIL). Tests greenfield diff 0.0000 cross-3-símbolos pre-merge gate empírico mandatory.
- [ ] **R6 audit refactor Opción A clean post-Path γ**: callers `audit_fidelity_v5*.py` + `audit_mr_fidelity_sei.py` + analyzers actualizados para usar `run_on_slice(..., return_per_trade=True)` cluster-by-cluster (preserva state evolution). Eliminate copia python `extract_trades_tf` audit (audit ahora wraps kernel productivo directamente cluster-by-cluster).
- [ ] Tests greenfield audit pre/post refactor diff 0.0000 cross-3-símbolos + cross-check `_run_verify_test` ground truth (76 trades 380 mediciones diff 0.0000 baseline 2026-04-26) **gate empírico antes merge**.
- [ ] Smoke §0.8 obligatorio cross-cuatro símbolos.
- [ ] EXPECTED_LAB_KERNEL_HASH regenerated post-Path γ.
- [ ] Commit consolidado Sesión 2 Frame 2 R3+R6.

### Sesión 3 Frame 2 — R4 Bloque 2c granular cross-régimen + R5 condicional (~2-5h CC, ~2026-04-30 a 05-01)

- [ ] **R4 Bloque 2c granular cross-régimen** (con kernel Path γ): H1+H_funding+H_strategy cross-régimen 44 sym × 3 clusters × top-5 cross-régimen 3y BTC macro. Granularidad H_strategy real cross-strategy disponible vía Path γ enum extendido.
- [ ] **R5 condicional** (solo si Gate A FAIL Sesión 4): H_M3 selection bias cross-cluster + H_M4 régimen-temporal bias + H_M5 GMM regime classification noise + H_M6 cross-exchange Binance↔BingX residual.
- [ ] Commit consolidado Sesión 3 Frame 2.

### Sesión 4 Frame 2 — Gates evaluation cross-9 N=9 (~1-2h CC, ~2026-05-02 a 03)

**Gates criterio empírico cierre Frame 2** (cross-9 N=9 BTC+ONDO+SEI × C0+C1+C2):
- [ ] **Gate A — Magnitud**: mean ratio J/B post-R1+R2 ≤ 1.5× baseline M2 fix 2.41× (target reducción >40% vs baseline single-fold).
- [ ] **Gate B — Resilencia**: 0/9 colapso fuerte cross-symbol (preservar M2 fix invariante).
- [ ] **Gate C — Estabilidad cross-cluster**: Spearman ρ stable cross-cluster sin volteos signo (proxy noise ranking).
- [ ] **PASS Gates A+B+C**: reciclaje launch Sesión 5 Frame 2.
- [ ] **FAIL Gate A único** (B+C PASS): escalar Sesión 3 R5 condicional adicional.
- [ ] **FAIL Gate B/C**: pause + diagnóstico arquitectónico §12 L34 (no escalada compute ciega).

### Sesión 5 Frame 2 — Reciclaje 45 sym launch (~30 min preparation + ~10-15 días compute autónomo VPS, ~2026-05-03 a 05)

- [ ] Validation gates: bot v2.4.5 invariante + audit refactored R6 done + Smoke Nivel B sistemático done + Gates A+B+C PASS.
- [ ] Reciclaje 45 sym launch.
- [ ] Reciclaje ejecución autónoma VPS (~10-15 días compute).
- [ ] Reciclaje completo: ~2026-05-15 a 05-22.

**§12 L37 recalibración temporal Frame 2**:
- Estimación humana naive: ~50-100h cross-3-4 semanas calendario.
- **Tiempo Claude Code real**: **~12-19h cross-1.5-2 semanas calendario** (factor 5-7× más rápido — patrón cross-Sesiones 1A+1B+1B amendment validated).
- Bot obsoleto adicional Frame 2 vs AGGRESSIVE pura recalibrada: **+0-2 días** (negligible vs valor refinamientos pre-reciclaje).
- Trade-off: invertir 2-4 días CC real adicional Frame 2 evita rotación 45 specialists post-reciclaje con methodology defectuosa = ahorro ~10-15 días calendario futuro.

**Riesgos + mitigaciones cross-items**: ver §13.4 entrada Sesión 0 Frame 2 2026-04-28 sesión noche + §13.4 entrada Path β3 ROLLBACK 2026-04-28 sesión noche (lección §12 L34 + L38 captura).

---

## Pre-reciclaje AGGRESSIVE pura recalibrada — 2026-04-27 Sesión 2 D (SUPERSEDED 2026-04-28 sesión noche por Frame 2)

**Estado**: PLANIFICACIÓN INSTITUCIONAL PERMANENTE bajo enfoque Ricardo "al margen de lo que cueste, aspirar a lo mejor reciclaje". **Sesiones 1A+1A.2 Path β3 mantenidas como historial done/failed** (Sesión 1A 2/3 implementadas + Sesión 1B Path α + amendment done; Sesión 1A.2 Path β3 ROLLBACK clean). Sesiones 1B+2+3+4+5 redefinidas Frame 2 supra.

**Total**: 14 items pre-reciclaje cross-4-5 sesiones Claude Code cross-1.5-2 semanas calendario.

**Recalibración temporal §12 L37**: estimaciones humanas (89-135h cross-3-semanas) → tiempo Claude Code real (20-35h cross-1.5-2 semanas calendario). Bot obsoleto adicional ~1-2 semanas vs ~5-6 semanas estimación original. Diferencia categórica trade-offs.

### Sesión 1A — Setup base parcial DONE 2026-04-28 (2/3 implemented + 1/3 BLOQUEADO mismatch revealed)

- [x] **G1.3 Lab compute_leverage_map fix** → `lev=1` always + docstring P1 opción (b) caveats (i)-(v) explícitos (`live/portfolio_manager.py:641-728`, 45 sym verificado lev=1).
- [x] **G5.11 portfolio correlación min_len** arquitectónica simple (`live/portfolio_manager.py:89-122` threshold 60 + tests no-regression PASS).
- [⚠] **G2.1 Refactor audit_v5.x Opción A** → BLOQUEADO mismatch revealed (`extract_trades_tf` audit retorna per-trade vs `run_simulation_numba` kernel retorna agregados). Path A reorder confirmed Ricardo: **Sesión 1A.2 nueva post-G1.1**.
- [x] **G2.2 Smoke §0.8 Nivel B baseline** pre-cambios cross-3-símbolos: BTC N=1000 diff 0.0000 + ONDO N=8000 diff_rel 22.70% (specialist working tree NEW, NO regresión brain/kernel — §12 L25 sub-refinamiento) + APT N=10000 diff_rel 1.51% PASS (specialist HEAD baseline). Cross-symbol triangulación §12 L26 valida diagnóstico.
- [x] **G2.2 Smoke §0.8 Nivel B post-cambios validation**: BTC N=1000 diff 0.0000 IDÉNTICO baseline (predicción §12 L36 (3) confirmed: G1.3+G5.11 NO tocan brain path). ONDO+APT post equivalencia lógica.
- [x] Commit consolidado Sesión 1A parcial.

**Hallazgos institucionales Sesión 1A**:
- §12 L36 9ª aplicación profiláctica funcionó: G2.1 dependency mismatch detectado pre-implementación (~1-2h CC ahorrados redirección Path A) + ONDO baseline context revealed (~30-60 min ahorro).
- §12 L25 sub-refinamiento inline aplicado: smoke baselines + specialist version context.
- Cross-10-aplicaciones §12 L36 consolidada (~52-90h ahorro acumulado paths infeasibles ciegamente).
- Ver §13.4 entrada Sesión 1A parcial 2026-04-28.

### Sesión 1A.2 — G2.1 Refactor audit_v5.x Opción A clean post-G1.1 (NUEVA reorder Path A, ~1-2h Claude Code, ~2026-04-30)

- [ ] **G2.1 Refactor audit_v5.x Opción A** (importar kernel directo, preservar stateless property) post-G1.1 (per-trade arrays disponibles)
- [ ] Tests greenfield audit pre/post refactor diff 0.0000 cross-3-símbolos
- [ ] Cross-check `_run_verify_test` ground truth (76 trades 380 mediciones diff 0.0000 baseline 2026-04-26)
- [ ] Smoke audit cross-3-símbolos validación
- [ ] Commit consolidado Sesión 1A.2.

### Sesión 1B Amendment — Path α' supplement entry_price + exit_price arrays DONE 2026-04-28 sesión noche

- [x] **Path α' supplement**: kernel `run_simulation_numba` extended con 2 arrays adicionales (`pt_entry_price` + `pt_exit_price`, float64) — corrige oversight Sesión 1B planning original (reduced enum colapsa sl_emergency vs sl_hit → exit_price NO derivable post-call).
- [x] **EXPECTED_LAB_KERNEL_HASH regenerated**: `fec1725e...` → `02f9c480...` en `audit_fidelity_v5*.py`.
- [x] **Re-Smoke §0.8 obligatorio post-amendment**: 5/5 PASS (BTC Nivel A diff 0.0000 + ONDO Nivel B 22.70% IDÉNTICO + APT Nivel B 1.51% IDÉNTICO + SEI MR Nivel C diff 0.0000 + audit hash parity NO WARN). Backward compat 100% empíricamente validated.
- [x] Tests greenfield Test 1 backward compat + Test 2 Path α + amendment (10 keys per_trade_dict) PASS.
- [x] Commit consolidado Sesión 1B amendment.

**Hallazgo**: Sesión 1A.2 Parte 0 verificación §12 L38 detectó gap arquitectónico Sesión 1B planning (reduced enum collapse decisión deliberada NO necessity técnica → reversible vía supplement). Path α' corrige ANTES audit refactor invertir compute futile. Aplicación recursiva §12 L38 cross-2-aplicaciones cross-2-sesiones.

### Sesión 1B — G1.1 Tier 0 I1 Path α flag-driven DONE 2026-04-28 sesión tarde

- [x] **G1.1 Tier 0 I1 kernel return_per_trade flag-driven** (Path α): TF kernel modify (`lab_historico_numba_v8_3.py:1268-1297` constants + signature + `:1685-1715` per-trade tracking + `:1911-1990` `run_on_slice` dispatch). Backward compat 100% production callers preserved + memory acotada audit/analyzers (~5 KB small config sets) + reduced enum 4 valores TF (sl_exit, div_exit, normal_exit, cancel_tf) matching kernel current logic.
- [x] **Verificación pre-implementación Parte 0** (4/5 mismatch detectados, decision Path α vs Path γ original): signature parallel prange + 25 callers + reason_exit collapsed + memory blowup 4.8 GB inviable.
- [x] **EXPECTED_LAB_KERNEL_HASH regenerated**: old `165b2357...` → new `fec1725e...` en `audit_fidelity_v5*.py`.
- [x] **Tests greenfield**: Test 1 backward compat 7-tuple PASS + Test 2 Path α 2-tuple (aggregates + per_trade dict) PASS + Numba JIT compila signature extendida.
- [x] **Smoke §0.8 obligatorio cross-cuatro símbolos**: BTC Nivel A diff 0.0000 EXACTO + ONDO Nivel B 22.70% IDÉNTICO baseline + APT Nivel B 1.51% IDÉNTICO baseline + SEI MR Nivel C diff 0.0000 en 7 métricas (MR kernel UNCHANGED) + audit hash parity NO WARN.
- [x] **Commit consolidado Sesión 1B Path α**.

**Hallazgos institucionales Sesión 1B**:
- §12 L38 nueva captura formal sexto pilar institucional: verificación supuestos técnicos pre-implementación cross-fuentes primarias. Aplicación recursiva 2-niveles (Claude redactor + Claude Code verificador). Caso origen 2026-04-28 cross-2-sesiones consecutivas (Sesión 1A G2.1 + Sesión 1B G1.1 Parte 0). Total ahorro temporal ~4-7h CC paths infeasibles ciegamente.
- §12 L36 cross-13-aplicaciones consolidada: 12ª pre-impl + 13ª Smokes = 10/10 acertadas Sesión 1B. Cross-13 ahorro acumulado ~52-90h.
- MR kernel UNCHANGED Sesión 1B (preserva §12 L25 segmentación). Expansión MR kernel diferida Sesión 2 si Bloque 2c granular emerge necesidad H_strategy análisis cross-strategy.
- Ver §13.4 entrada Sesión 1B Path α 2026-04-28.

### Sesión 1A.2 — G2.1 Refactor audit_v5.x Opción A clean post-Path α PRIORITARIA próxima (~1-2h Claude Code, ~2026-04-29)

- [ ] **G2.1 Refactor audit_v5.x Opción A** post-Path α: callers `audit_fidelity_v5*.py` + `audit_mr_fidelity_sei.py` + analyzers actualizados para usar `run_on_slice(..., return_per_trade=True)` cuando per-trade tracing necesario. Stateless property preservada por construcción (kernel funciones puras). Eliminate copia python `extract_trades_tf` audit (audit ahora wraps kernel productivo directamente).
- [ ] Tests greenfield audit pre/post refactor diff 0.0000 cross-3-símbolos
- [ ] Cross-check `_run_verify_test` ground truth (76 trades 380 mediciones diff 0.0000 baseline 2026-04-26)
- [ ] Smoke audit cross-3-símbolos validación
- [ ] Commit consolidado Sesión 1A.2.

- [ ] Análisis profundo callers `run_simulation_numba` (grep + ag-search)
- [ ] **G1.1 Tier 0 I1 kernel modify**: arrays per-trade + reason_exit enum + signature extension
- [ ] Update 10+ callers: `_run_verify_test`, `regime_walk_forward.py`, `lab_lite_zonas_v5e.py`, `audit_fidelity_v5.py` + `audit_fidelity_v5_2.py`, `master.py`, `audit_mr_fidelity_sei.py`
- [ ] Update `EXPECTED_LAB_KERNEL_HASH` audit + checksum regen
- [ ] Tests greenfield per-trade tracing
- [ ] **Smoke §0.8 Nivel A+B+C obligatorio** (BTC N=1000 + ONDO N=8000 + APT N=10000 + SEI MR)
- [ ] Cross-check `_run_verify_test` baseline (76 trades 380 mediciones diff 0.0000 baseline 2026-04-26)
- [ ] Commit consolidado Sesión 1B.

### Sesión 2 — G1.2 Bloque 2c + Hipótesis Mec 3+4 (~4-6h Claude Code, ~2026-05-01 a 02)

- [ ] **G1.2 Bloque 2c granular** H1+H_funding+H_strategy cross-régimen (44 sym × 3 clusters × top-5 cross-régimen 3y BTC macro)
- [ ] **H_M3 Selection bias cross-cluster** (matriz correlation MA preset families top-1 cross-44-sym)
- [ ] **H_M4 Régimen-temporal bias** subset+full (segmentación régimen GMM BTC × top-1 specialist)
- [ ] **H_M5 GMM regime classification noise** (sensitivity sweep P_threshold ∈ {0.50, 0.65, 0.80, 0.95})
- [ ] **H_M6 Cross-exchange Binance↔BingX residual** (kernel runs 9 specialists top-1 cross-exchange)
- [ ] Calibración §12 L36 9ª aplicación retrospectiva
- [ ] Commit consolidado Sesión 2.

### Sesión 3 — Selection-bias-specific tools subsets (~5-6h Claude Code, ~2026-05-03 a 04)

- [ ] **G3.2 Deflated SR core formula** + validación numérica + cross-9 cross-symbol M2 fix baseline (Q1+W1 2026-04-23)
- [ ] **G3.3 k-fold CV walk-forward subset** + validación tests
- [ ] Aplicación al ranking selection (input para Sesión 4 reciclaje preparation)
- [ ] Commit consolidado Sesión 3.

### Sesión 4 — G5.3 brain refactors + cierre pre-reciclaje (~3-5h Claude Code, ~2026-05-05 a 06)

- [ ] Análisis profundo lecciones v2.3.9 prev_zone B2 + TF locals B3 (subtarea explícita pre-implementar). Output: documento decisión arquitectónica (a/b/c) prev_zone.
- [ ] **G5.3 prev_zone B2 + TF locals B3** implementación (~3-5h Claude Code)
- [ ] **Smoke §0.8 Nivel A+B+C obligatorio** cross-cambios brain camino crítico
- [ ] **G5.1 Deploy L1892+L1904** (procedure standard 8 pasos)
- [ ] **G2.2 Smoke §0.8 Nivel B sistemático final** pre-launch
- [ ] Documentación final pre-reciclaje
- [ ] Commit consolidado Sesión 4.

### Sesión 5 — Reciclaje 45 sym launch (~30 min preparation + ~10-15 días compute autónomo VPS, ~2026-05-07 a 22)

- [ ] Validation gates: bot v2.4.5 invariante + audit refactored + Smoke Nivel B sistemático done + Deploy L1892+L1904 done
- [ ] Reciclaje 45 sym launch
- [ ] Reciclaje ejecución autónoma VPS (~10-15 días compute)
- [ ] Reciclaje completo: ~2026-05-22 a 06-05

**Trigger reciclaje launch**: cuando Sesiones 1A+1B+1A.2+2+3+4 done todas. Estimación temporal: ~2026-05-07 a 13.

**Bot obsoleto adicional bajo AGGRESSIVE pura recalibrada**: ~1-2 semanas vs plan minimalista sesión 1 Fase 5 (~3-4 días). Trade-off aceptable bajo enfoque Ricardo "al margen de lo que cueste, aspirar a lo mejor reciclaje".

**Riesgos + mitigaciones cross-items**: ver §13.4 entrada Sesión 2 D + `docs/audit_pre_reciclaje_calendar_20260427_sesion2.md`.

**Reciclaje "aspirar a lo mejor" empíricamente sustentado**:
- Gaps F1 resueltos: G1.1 + G1.2 + G1.3.
- Gaps F2 resueltos: G2.1 + G2.2 + G5.1.
- Gaps F3 caracterizados: 4 hipótesis Walk-forward Mec 3+4 + Deflated SR + k-fold CV.
- Operacionales cleanup: G5.3 + G5.11.

## Próximas sesiones — pendientes operacionales

**Disparadores temporales próximos**:
- Deploy L1892 active_config_id + L1904 multipliers SIGNALS_DISCARDED (commit `3727366`): fecha límite ~2026-05-05 a 05-10 aislado pre-reciclaje. Procedure standard validada v2.4.4/v2.4.5 (~20-47s downtime + Smoke §0.8 Nivel A único requerido). Item L2869 scope refinado Fase 3 2026-04-27.
- **Refactor audit_v5.x pre-reciclaje** (~4-12h sesión dedicada agrupada con deploy L1892+L1904 ~2026-05-05 a 05-10): único candidato rescatable identificado por auditoría rescate items archived 2026-04-27 cierre día (Fase 5). Output: auditor limpio + tests greenfield + cross-check `_run_verify_test` ground truth (76 trades 380 mediciones diff 0.0000 baseline). Beneficio: validación 45 JSONs nuevos post-reciclaje sin bottleneck refactor concurrent. Ver §13.4 entrada "AUDITORÍA RESCATE ARCHIVED" 2026-04-27 cierre día.
- Reciclaje completo 45 sym ETA ~2026-05-12 a 05-22 (~180-225h compute VPS, 8-10 días).

**Reactivación condicional items archivados** (no requieren acción pre-reciclaje):
- v2.6-inv re-evaluable solo si régimen mercado cambia drásticamente (bear extremo, eventos macro, shock funding) → re-evaluar threshold X empírico + frecuencia subset operacional.
- v2.6-exit re-evaluable post-reciclaje + k-fold CV proyecto dedicado.
- P1 leverage re-evaluable post-reciclaje SOLO con condiciones (i)-(v) explícitas (edge restored N≥50 nuevo + capital >1000 USDT + isolated mantenido + re-simulación cross-12-escenarios mejora vs baseline 2026-04-27 + asimetría arquitectónica clusters resuelta).

**Items §13.3 EN_ESPERA finales (24 totales)**: 8 categóricos skip post-reciclaje (audit_v5.x, git+GitHub, walk-forward bias, Tier 0 I1, Análisis B edge decay, orphan reconstruction triage, funding fallback triage) + 16 refinados scope/disparador 2026-04-27 (brain_engine 8 items reciclaje julio, portfolio 3 disparadores empíricos no cumplidos, data_feed/execution 2 post-reciclaje cleanup, operacionales 3 cosmético/permanente/inminente reciclaje).
Scope compute: ~180-225h VPS (8-10 días).
Estimación fecha: ~2026-05-12 a 05-22.

**Pre-reciclaje deploy pendiente** (item §13.3 EN_ESPERA 2026-04-26 sesión 2): L1892 active_config_id + L1904 multipliers SIGNALS_DISCARDED observability extensions (commit `3727366`) — agrupar con próximo deploy operacional Fase D/E si emerge, o aislado fecha límite ~2026-05-10 inmediato pre-reciclaje. Disparador temporal explícito conscientemente prevenido §12 L27 (item NO debe sobrevivir reciclaje sin cierre). Procedure standard validada v2.4.4/v2.4.5 (~20-47s downtime, Smoke §0.8 Nivel A único requerido).

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

## Variante 4 caracterización funding pre-reciclaje — ARCHIVED 2026-04-26 sesión 4 (Path B.4)

Investigación cross-régimen rasgo agregado mercado funding rates archivada por retornos decrecientes vs disparador operacional D inminente. Hallazgos institucionales permanentes preservados:

1. **Threshold X=5e-4 empírico cross-3-exchanges** (Binance+BingX+OKX × 15 sym × 180d, 96.5% unanimidad pooled, 100% sw2 60d) confirmado como magnitud donde rasgo agregado mercado es genuino.
2. **Rasgo EXTREMO RARO régimen actual**: 11/15 sym 0 eventos cross-180d. Concentración 4 sym primary (SEI 14% + DOT 8.4% + SOL 1.4% + NEAR 0.3% ~24% combined). Mega/large-caps 0 eventos cross-180d.
3. **OKX funding history retention API ≈95d** caveat permanente cross-exchange retrospective. Binance + BingX retention >180d.
4. Items §13.3 v2.6-inv L2340 + v2.6-exit L2385 actualizados con threshold empírico X=5e-4 vs §9.3 arbitrario `|rate| > 0.001`.

Disparador operacional D ~2026-05-01 N≥100 BingX-native sigue método correcto para decisión filter productivo. Threshold X=5e-4 identificado hoy = input empírico al diseño análisis Welch post-N≥100. Ver §13.4 entrada Path B archive 2026-04-26 sesión 4 + `docs/funding_pathb_sesion3_archived_20260426.md`.

§12 L36 validada profilácticamente cross-3 sesiones consecutivas funding research (ahorro compute ~30-45h paths infeasibles ciegamente).

## Historia

- **2026-04-28 Sesión 1 Frame 2 análisis arquitectónico completo** (sesión noche-2): Opción γ' confirmada Ricardo — análisis arquitectónico exhaustivo `regime_walk_forward.py` (2366 líneas, 36 funciones) + `lab_historico_numba_v8_3.py` TF kernel + `mean_reversion_kernel.py` MR kernel post-Sesión 1 R2 Parte 0 detected 6/5 mismatches sustanciales spec R2 original. **Decisiones Ricardo confirmadas**: (C) descartar R2 k-fold CV pre-reciclaje (H2 hipótesis Sesión 0 mal-formulada vs realidad episode-based per cluster CHRONOLOGICAL + cross-9 ONDO 0/3 R2-eligible orphan) + R6_γ defer post-reciclaje (state evolution divergence audit pre-refactor entries-filter NO replicable Path γ alone — Path β3 fail empírica 2.7% match rate validó) + R5 Reduced parameter space + ensemble promovido pre-reciclaje combinado R4 + (P1) Path γ SUSTITUYE Path α + α' supplement Sesión 1B (no amend, decisión arquitectónica honesta). **Spec R3 Path γ refinada ASIMÉTRICO TF (6 valores) + MR (8 valores)** — spec Sesión 0 invertida (`regime_change` brain-side + `cancel_mr` no aplica TF spurious paths). MR kernel UNCHANGED Sesión 1B → Path γ Sesión 2 introduce per-trade tracking PRIMERA VEZ MR (~3-4h CC) replicando Path α' supplement pattern + TF scope ~1.5-2h CC = TOTAL ~5-6h CC ambos kernels Sesión 2. **5 sub-decisiones técnicas (m+n+o+p+P1+q) + 6 operacionales (r+s+t+u+v) explicitadas Sesión 2 Parte 0 verificación pre-implementación obligatoria**. **3 escenarios Sesión 4 Gates evaluation 3-way honestos**: Escenario 1 PASS+PASS+PASS ~30-40% reciclaje confidence alta + Escenario 2 PASS+PASS+FAIL_C ~40-50% (most likely) reciclaje methodology honest + decisión Ricardo strategic capital scale-up (10K USDT × edge ~1.2-1.6 PF ≈ +$240-1200/año conservative o +$450-900/año selective comparable ETF/bonds baseline) vs Frame 3 pivot (ensemble adaptive + Bayesian regime-conditional + online learning) + Escenario 3 FAIL_A ~15-25% Frame 3 redesign mandatory. **Frame 2 alcance honesto explícito**: refinements pre-reciclaje (R1+R3+R4+R5) NO mejoran edge real disponible mercado — atacan sobrestimación métricas walk-forward para selección honesta configs reciclaje. **§12 L34+L36+L37+L38 aplicadas disciplinadamente cross-Sesión 0+1 = ~12-18h CC futile prevenido cumulative + reformulación honesta alcance Frame 2 cross-evidencia disponible**. §12 L34 aplicación recursiva al roadmap Frame 2 propio (hipótesis emergentes refutadas → roadmap reformulado disciplinadamente). §12 L36 cross-18-aplicaciones consolidada. §12 L37 calibración temporal ~3-4h CC total Sesión 1 vs ~30-50h estimación humana. §12 L38 disciplinada lectura código real cross-fuentes-primarias completas. Frame 2 reformulado calendar reciclaje launch ~2026-05-03 invariante. Bot v2.4.5 invariante uptime ~5d 11h+ VPS Tokio. Sin tocar live/* productivo (Sesión 1 read-only análisis + documentación institucional). Fidelidad 2 invariante por construcción.

- **2026-04-28 Sesión 0 Frame 2 metodológica fundamental + Sesión 1A.2 Path β3 ROLLBACK** (sesión noche): post-Sesión 1A.2 Path β3 EMPIRICAL FAIL 2.7% match rate vs gate 80% (kernel cross-cluster + post-filter brain-side NO preserva state evolution equivalence con audit pre-refactor cluster-by-cluster — causa raíz cooldown/sl_level/div_ctx evolution cross-trade). ROLLBACK clean: branch `feature-audit-refactor-path-beta3` deleted + audit_fidelity_v5_2.py restaurado main `f8205fa` + EXPECTED_LAB_KERNEL_HASH revertido `02f9c480...` (Sesión 1B amendment baseline preservado). **Cuestionamiento Ricardo "patada hacia delante"**: refinamientos pospuestos repetidamente L1721 audit + L2336 multi-testing + L2621 Tier 0 I1 — AGGRESSIVE pura recalibrada heredó patrón al diferir Deflated SR + k-fold CV post-reciclaje. **Frame 2 redesign SUPERSEDE**: walk-forward methodology completa pre-reciclaje (R1 Deflated SR + R2 k-fold CV Sesión 1 + R3 Path γ kernel granular sustituye Path α reduced enum + R6 audit refactor Opción A clean post-Path γ Sesión 2 + R4 Bloque 2c granular cross-régimen + R5 condicional Sesión 3 + Gates A+B+C cross-9 N=9 cierre empírico Sesión 4 + reciclaje launch Sesión 5). Total 5 sesiones cross-1.5-2 semanas calendario, ~12-19h CC real §12 L37 (vs estimación humana naive ~50-100h, factor 5-7× más rápido). Bot obsoleto adicional vs AGGRESSIVE: +0-2 días negligible. **§12 L36 16ª aplicación retrospectiva refutada**: predicción Path β3 by-construction equivalent → real 2.7% REFUTADA. **§12 L34 captura**: hipótesis "semánticamente equivalente por construcción" sin validación empírica ANTES = costo evitable ~3-4h CC. **§12 L38 10ª aplicación recursiva**: state evolution divergence categoría riesgo distinta a output equivalence. Estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1+TRIAJE+AUDIT-RESCATE+FRAME-2-WALK-FORWARD-COMPLETO invariante. Bot v2.4.5 operacional VPS Tokio uptime ~5d 11h+ invariante.

- **2026-04-28 Sesión 1B Path α** (G1.1 Tier 0 I1 kernel return_per_trade flag-driven DONE post-Path A reorder Sesión 1A): bajo plan AGGRESSIVE pura recalibrada commit `8d837af` + reorder Sesión 1A G2.1 mismatch (commit `2270b67`). Implementación Path α flag-driven post-Parte 0 verificación 4/5 mismatch detectados (signature parallel prange + 25 callers + reason_exit collapsed + memory blowup 4.8 GB inviable Path γ original). **Path α adoptado**: `return_per_trade: bool = False` flag default backward compat 100% + reduced enum 4 valores TF kernel-current granularidad sin refactor invasivo + MR kernel UNCHANGED preserva §12 L25 segmentación (expansión MR diferida Sesión 2 si Bloque 2c emerge necesidad). Tests greenfield + Smokes §0.8 obligatorios cross-cuatro símbolos PASS (BTC Nivel A diff 0.0000 EXACTO + ONDO Nivel B 22.70% IDÉNTICO + APT Nivel B 1.51% IDÉNTICO + SEI MR Nivel C diff 0.0000 + audit hash parity NO WARN post fec1725e). **§12 L38 nueva captura formal sexto pilar institucional** (verificación supuestos técnicos pre-implementación cross-fuentes primarias, aplicación recursiva Claude redactor + Claude Code verificador). §12 L36 cross-13-aplicaciones consolidada (10/10 acertadas Sesión 1B). Items §13.3 IMPLEMENTED: L2910 Path α; L1781 READY post-Sesión 1B. Calendario AGGRESSIVE pura recalibrada inalterado: Sesión 1A.2 G2.1 Opción A clean post-Path α próxima (~1-2h CC). Trigger reciclaje launch ~2026-05-06 a 21. Bot v2.4.5 invariante uptime ~5d 7h+ (sin tocar live/* productivo, kernel modify lab-only).

- **2026-04-28 Sesión 1A parcial** (setup base independiente DONE 2/3 + 1/3 BLOQUEADO mismatch revealed): bajo plan AGGRESSIVE pura recalibrada commit `8d837af` 2026-04-27 Sesión 2 D, ejecución Sesión 1A primer dedicada. **Items implementados clean**: G1.3 Lab compute_leverage_map fix → lev=1 always + docstring P1 (b) caveats (i)-(v) (45 sym verificado); G5.11 portfolio correlación min_len threshold 60 + tests no-regression PASS. **Item BLOQUEADO**: G2.1 Refactor audit_v5.x Opción A — investigación pre-cambio reveló dependency mismatch (audit `extract_trades_tf` retorna per-trade vs kernel `run_simulation_numba` retorna agregados; Opción A inherente requiere G1.1 Tier 0 I1 prereq). Decisión Ricardo Path A reorder: Sesión 1A.2 nueva post-G1.1. **Validación cross-cambios**: BTC pre/post N=1000 diff 0.0000 IDÉNTICO (G1.3+G5.11 NO tocan brain path); ONDO pre N=8000 diff_rel 22.70% explicable specialist working tree NEW vs HEAD baseline (no regresión brain/kernel — §12 L25 sub-refinamiento inline aplicado); APT pre N=10000 diff_rel 1.51% PASS triangulación cross-símbolo §12 L26 confirmando JSON HEAD baseline preserved. **§12 L36 9ª aplicación profiláctica funcionó**: G2.1 mismatch detectado pre-implementación (~1-2h CC ahorrados redirección Path A) + ONDO baseline context revealed. Cross-10-aplicaciones consolidada (~52-90h ahorro acumulado). Items §13.3 actualizados: L2370 + L2393 → IMPLEMENTED 2026-04-28; L1781 → BLOQUEADO scope refinado Sesión 1A.2. Calendario refinado 5-6 sesiones cross-1.5-2.5 semanas (vs 4-5 original). Trigger reciclaje launch ~2026-05-07 a 13. Reciclaje completo ~2026-05-22 a 06-05. Bot v2.4.5 invariante uptime 5d 4h+ (sin tocar live/* productivo, G1.3+G5.11 cambios offline preservados).

- **2026-04-27 Sesión 2 D** (auditoría exhaustiva pre-reciclaje + decisión Ricardo AGGRESSIVE pura recalibrada): bajo enfoque Ricardo "al margen de lo que cueste, aspirar a lo mejor reciclaje", auditoría 4-fase exhaustiva (Parte 0 inventario gaps F1/F2/F3 cross-25-items + Parte 1 re-evaluación individual + Parte 2 mapping dependencias + Parte 3 calendarios A/M/F + Parte 4 riesgos+mitigaciones específicas). Reformulaciones timing categóricas reveladas: G1.1 Tier 0 I1 + G1.3 Lab compute_leverage_map + G2.1 Refactor audit_v5.x conceptualmente PRE-RECICLAJE (sesión 1 Fase 5 timing inversión). Recalibración temporal §12 L37 capturado: estimaciones humanas (89-135h cross-3-semanas) → tiempo Claude Code real (20-35h cross-1.5-2 semanas calendario). Decisión Ricardo confirmada AGGRESSIVE pura recalibrada: 14 items pre-reciclaje cross-Sesiones 1A+1B+2+3+4 (~18-26h Claude Code). Bot obsoleto adicional ~1-2 semanas vs ~5-6 semanas plan original. §12 L36 9ª aplicación cross-9-aplicaciones consolidada (~52-90h ahorro acumulado). 4 hipótesis Walk-forward Mec 3+4 §12 L34 compatible formuladas (H_M3+H_M4+H_M5+H_M6). 5 commits acumulados día + 1 Sesión 2 D = 6 commits día completo. Estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1+TRIAJE+AUDIT-RESCATE+AGGRESSIVE-PRE-RECICLAJE invariante.

- **2026-04-27 cierre día Fase 5** (auditoría rescate archived items): bajo enfoque institucional Ricardo "aspirar a lo mejor" + recursos ilimitados, auditoría sistemática cross-14-archived items con análisis crítico ultrathink top-5 candidatos. **7/7 predicciones acertadas** Claude Code pre-auditoría: solo 1/5 rescatable (B Refactor audit_v5.x bajo argumento independiente timing eficiente) + 4/5 refutados (A Path B refutación reforzada hoy + C Tier 0 I1 ya cumplido + D Walk-forward scope abierto §12 L34 + E Subset §13.3 contradice triaje Fase 3 propio). Aplicación recursiva §12 L27 V1 al meta-nivel produjo §12 L27 refinamiento V2 permanente: items archivados con razones empíricas sólidas son resilientes a rescate (turnover ~7-15% análogo items §13.3 disciplinados V1). Candidato B diferido sesión dedicada deploy L1892+L1904 ~2026-05-05 a 05-10 (evita momentum institucional sesgo + agrupa eficientemente). §12 L36 cross-7-aplicaciones consolidada (~52-82h ahorro acumulado).

- **2026-04-27 cierre día consolidado** (Fase 4 administrativa): §12 L27 refinamiento permanente capturado (distinción items susceptibles vs resilientes, predicción turnover diferenciada, valor institucional update sistemático ≠ exclusivamente turnover). Header L3 entrada SESIÓN COMPLETA DÍA cierre. ROADMAP final post-archive D+E+P1+triaje. Único pendiente pre-reciclaje: deploy L1892+L1904 fecha límite ~2026-05-05 a 05-10. 4 commits día completo (3eb937c + 06e30fb + d1d2859 + Fase 4). Estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1+TRIAJE invariante.

- **2026-04-27 sesión tarde-noche** (Fase 3): triaje sistemático §13.3 §12 L27 cross-20-items. Categorización: 2 ARCHIVED (L1961 R1 dependencia obsoleta + L2295 compute_leverage_map bajo P1) + 18 EN_ESPERA refinados scope/disparador marcador 2026-04-27 + 0 RESUELTO + 0 consolidados. §12 L34 metodológico: predicción turnover backlog 50-65% REFUTADA (real 10%) — items §13.3 son robustos, disparadores válidos pero no cumplidos. §13.3 EN_ESPERA reducido 28 → 24 (todos items refinados marcador hoy). §12 L36 cross-6-aplicaciones consolidada (~50-80h ahorro acumulado). Estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1+TRIAJE.

- **2026-04-27 sesión tarde**: P1 leverage ARCHIVED_EMPIRICAL bajo opción (b) 1x feature oficial. Fase 2 análisis cuantitativo full robusto isolated cluster-específico cross-12-escenarios + cluster top/bottom 10 + leverage selectivo + sanity cross-segmento §12 L25. Margin mode `isolated` VERIFIED empírico VPS BingX. Cluster_id mapping 100% coverage post-v2.4.5 N=76 vía SIGNALS_RAW logs parse. Hallazgos: cap 3x amplifica decay 1.61× (-0.0246 vs -0.0153 baseline); 0 liquidaciones cross-12-escenarios; cluster selectivo top-10 PEOR que baseline (-1.92 vs -1.17 USDT); asimetría arquitectónica clusters ganadores maxdd alto / perdedores maxdd bajo. §13.3 L1849 P1 + L2152 E3 + L1861 setLeverage altos → ARCHIVED. §12 L36 cross-5-sesiones consolidada (3/7 acertadas + 3/7 refutadas + 1/7 parcial; ~40-65h ahorro acumulado). Baseline cuantitativo preservado para reactivación post-reciclaje con condiciones (i)-(v) explícitas. Estado pre-reciclaje MADURO INSTITUCIONAL FINAL+P1.

- **2026-04-27 sesión mañana**: D+E ARCHIVED_EMPIRICAL pre-disparadores. Pre-flight enrichment N=72 trades post-v2.4.5 (~17s compute local) reveló refutación masiva: v2.6-inv subset `|rate|≥5e-4` = 0/72 (Path B caveat "extremo raro régimen actual" validado operacionalmente cross-arquitectura limpia); v2.6-exit Spearman ρ=+0.020 p=0.87 signo OPUESTO triple-refutado vs Bloque 2 -0.32. Aplicación §12 L36 prophilactic ahorró ~6-10h compute + 2 días tiempo (validación mínima vs framework completo + Welch + esperar disparadores). §13.3 L2342 + L2399 → ARCHIVED_EMPIRICAL. §12 L36 cross-4-sesiones funding research consolidada (ahorro acumulado ~36-55h). Estado pre-reciclaje MADURO INSTITUCIONAL FINAL — A+B+C+D+E completo, trigger reciclaje 45 sym aguarda solo fecha calendario.

- **2026-04-22** (`roadmap_2026-04-22.md.archived-20260424`): roadmap original categorización §13.3 N/R/C (29 items). Sustituido por criterio institucional 2026-04-24 "todas mejoras A+B+C pre-reciclaje".
- **2026-04-24**: roadmap consolidado A+B+C+D+E post-smoke reciclaje Bloque 5 + refinamiento §13.2 marco mecánico canónico.
- **2026-04-25**: Fase B DONE (M2 fix validado empíricamente cross-symbol N=9, mejora 3.42× vs W3b baseline, hallazgo metodológico `_FWD_MIN_PF` no eficaz documentado). Avanzar Fase A (Z_BTC).
- **2026-04-26**: Fase C COMPLETA 7/7 DONE — audit Fid2 + investigación pnl_recon causa raíz + fix v1 + L1892/L1904 logs + triaje 4 micro-items + Fase 2 secundaria Opción C (causa raíz convenciones BingX vs analyzer identificada por code review). Multi-testing correction Holm/BH CASO B archivado empíricamente paralelo. **Fase A DONE_ARCHIVED mismo día** (Z_BTC refutado empíricamente cross-5 altcoins BIC sweep, commit `63de84c`).
- **2026-04-26 cierre estado pre-reciclaje maduro institucional**: Fase A DONE_ARCHIVED + Fase B DONE merged + Fase C 7/7 DONE + D+E ESPERA disparadores temporales (D N≥100 ~2026-05-01, E N≥150 ~2026-05-10). Refinamiento metodológico walk-forward: Multi-testing correction CASO B archivado empírico; tools selection-bias-specific (Deflated SR, k-fold CV) pendientes proyectos dedicados separados post-reciclaje. Próximo natural: esperar disparadores temporales D+E madurando o continuación sesión institucional según oportunidad.
- **2026-04-26 sesión 2**: Cache funding refresh forward + cierre §13.3 L2317 §12 L27. Predicción ultrathink §12 L36 5ª aplicación validada profilácticamente cross-3 puntos (service mismatch trading-bot vs combolab-bot + cache parcialmente cubre + cobertura 100% por construcción). Operación efectiva: refresh forward gap real 2026-04-23 → 2026-04-26T16:00 (~42s VPS, ~306 entradas, 35 símbolos, apareció THETAUSDT.csv nuevo). Coverage 78/78 trades duration>1h con entry_ms válido 100%. Item §13.3 L2317 RESUELTO con caveat parcialmente obsoleto pre-operación. Stress-tests v2.6-inv N≥100 disparador (~2026-05-01) NO bloqueados por gap cache. Bot v2.4.5 invariante.

- **2026-04-26 sesión 4 (Path B archive)**: Variante 4 caracterización rasgo agregado mercado funding rates ARCHIVED bajo decisión Ricardo Path B.4 (retornos decrecientes vs disparador D inminente). Captura institucional 3 hallazgos permanentes preservados: (1) Threshold X=5e-4 empírico cross-3-exchanges identificado; (2) rasgo EXTREMO RARO régimen actual concentración 4 sym; (3) OKX retention 95d caveat permanente. Items §13.3 L2340 v2.6-inv + L2385 v2.6-exit actualizados con threshold empírico vs §9.3 arbitrario. §12 L36 validada cross-3 sesiones funding research (ahorro compute ~30-45h paths infeasibles ciegamente). funding_context.py extendido OKX support. Disparador D ~2026-05-01 N≥100 sigue método correcto para decisión filter productivo. Bot v2.4.5 invariante uptime 4d 12h+. Sin tocar `live/*`. Sin deploy.
