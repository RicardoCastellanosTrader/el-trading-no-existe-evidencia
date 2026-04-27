# Roadmap pre-reciclaje — consolidado 2026-04-24 (FRAME 2 SUPERSEDE 2026-04-28 sesión noche)

**Criterio institucional Ricardo 2026-04-24**: todas las mejoras (A+B+C) implementadas antes de lanzar reciclaje completo 45 sym. Categorías D+E esperan datos operacionales temporales. Reciclaje se lanza cuando A+B+C done + D+E validados/archivados.

**FRAME 2 UPDATE 2026-04-28 sesión noche** (SUPERSEDE AGGRESSIVE pura recalibrada): walk-forward methodology refinements (Deflated SR + k-fold CV) reformulados **PRE-RECICLAJE** post-cuestionamiento Ricardo "patada hacia delante" + Sesión 1A.2 Path β3 EMPIRICAL FAIL evidence (2.7% match rate vs gate 80%). Tier 0 I1 Path γ kernel granular sustituye Path α reduced enum. Cierre criterio empírico Gates A+B+C cross-9 N=9 (no calendarico). 5 sesiones Frame 2 cross-1.5-2 semanas calendario, ~12-19h CC real §12 L37. Ver sección "Pre-reciclaje Frame 2" infra + §13.4 entrada Sesión 0 Frame 2 2026-04-28 sesión noche.

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

## Pre-reciclaje Frame 2 — 2026-04-28 Sesión 0 metodológica fundamental (SUPERSEDE AGGRESSIVE pura recalibrada)

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
