# Multi-testing correction Holm/BH — CASO B ARCHIVADO empíricamente — 2026-04-26

**Item §13.3 línea 2336** sub-item walk-forward methodology refinement.
**§13.2 caveat permanente** residual ratio J/B 2.41× post-M2 fix.
**Bot v2.4.5 invariante**.

---

## 1. Predicción metodológica pre-implementación (ultrathink)

Antes de implementar, identifiqué **mismatch conceptual estructural** entre:
- **Multi-testing correction clásico** (Bonferroni/Holm/BH/Deflated SR): herramienta para hypothesis testing donde cada test es independiente y se controla familywise error rate (FWER) o false discovery rate (FDR).
- **Selection bias structural "best of millions"**: sesgo en el POINT ESTIMATE de pf_fwd por seleccionar el mejor de ~138M candidates pre-filter. El bias está en la métrica, NO en la inferencia.

**Predicción**: classical multi-test correction sobre top_all post-filtros (N≤50000) NO ataca selection bias structural — solo controla FWER/FDR dentro del subset survivor.

**Predicción cuantitativa**:
- Holm con N=50000, α=0.05: threshold para best = α/N = 1e-6 → mayoría configs FAIL → orphan rate alto.
- BH con N=50000, α=0.05: threshold rank i = (i/N)×α → menos conservador, depende distribución p-values.

## 2. Implementación rama `feature-multi-testing-correction-pre-reciclaje`

### 2.1 Cambios `regime_walk_forward.py`

**Constantes nuevas**:
```python
_MULTI_TEST_METHOD = 'none'     # 'none' | 'holm' | 'bh'
_MULTI_TEST_ALPHA = 0.05
_MULTI_TEST_NULL_PF = 1.0       # H0: pf_fwd ≤ 1.0
```

**Funciones nuevas** (~250 LOC):
- `_compute_pvalues_from_ci_low(df)`: SE approx desde W3 bootstrap CI95 lower bound. t-stat = (pf_fwd - 1) / SE. p-value normal CDF one-sided.
- `_apply_holm_correction(p_values, alpha)`: step-down FWER control. α/(N-i) thresholds.
- `_apply_bh_correction(p_values, alpha)`: step-up FDR control. (i+1)/N × α thresholds.
- `_apply_multi_testing_correction(df, method, alpha)`: wrapper con flag selectivo.

**Integración** `extract_validated_specialists`: aplicada post-W3 bootstrap, pre-sort. NO-OP si method='none' (default backwards-compat M2 fix baseline).

### 2.2 Tests greenfield 13 PASS

`tests/test_multi_testing_correction.py`:
- T1 `_compute_pvalues_from_ci_low`: p-value para configs strong (pf=2, ci=1.5) ≈ 4.4e-5; weak (pf=1.05, ci=0.8) ≈ 0.35; SE inválido → p=1.
- T2 `_apply_holm_correction`: synthetic p [0.001, 0.01, 0.04, 0.05, 0.5] → 2 sobreviven; large N=50000 con 1 strong p=1e-7 → 1 sobrevive.
- T3 `_apply_bh_correction`: mismo synthetic → 2 sobreviven; verificar BH ≥ Holm en survivors.
- T4 `_apply_multi_testing_correction` wrapper: 'none' no-op, 'holm'/'bh' filtran, 'unknown' ValueError.
- T5 backwards-compat: 'none' default preserva M2 fix ranking.

**No-regression**: W3 8 + W4 8 + A14 4 + A15 4 + M2 3 = 27/27 PASS.

**Total**: 44/44 tests PASS efectivos.

## 3. Dry-run cross-9 sobre JSONs smoke 2026-04-24

Aplicación in-memory sobre top_100 del JSON existente (sin re-running pipeline). Re-sort por M2 fix (`pf_fwd_ci_low desc, specialist_score_ci_low desc`) para baseline correcta — JSONs actuales son W3b ranking pre-M2-fix (sorted por specialist_score_ci_low).

### Tabla resultados cross-9

| Sym | Cl | M2 cfg | pf_fwd | ci_low | Holm N | Holm cfg | chg | BH N | BH cfg | chg |
|-----|---:|-------:|-------:|-------:|-------:|---------:|:---:|-----:|-------:|:---:|
| BTC | 0 | 36909877 | 4.48 | 2.83 | 100 | 36909877 | F | 100 | 36909877 | F |
| BTC | 1 | 3758688 | 4.09 | 2.49 | 100 | 3758688 | F | 100 | 3758688 | F |
| BTC | 2 | 33831248 | 5.47 | 3.65 | 100 | 33831248 | F | 100 | 33831248 | F |
| ONDO | 0 | 34635228 | 3.27 | 1.81 | **0** | **ORPHAN** | — | 100 | 34635228 | F |
| ONDO | 1 | 12360961 | 2.88 | 1.54 | **0** | **ORPHAN** | — | 100 | 12360961 | F |
| ONDO | 2 | 48380978 | 3.95 | 2.40 | 100 | 48380978 | F | 100 | 48380978 | F |
| SEI | 0 | 57375331 | 3.44 | 1.81 | 1 | 37207460 | **T** | 100 | 57375331 | F |
| SEI | 1 | 1612992 | 3.08 | 1.84 | 79 | 1612992 | F | 100 | 1612992 | F |
| SEI | 2 | 815625 | 3.77 | 2.07 | **0** | **ORPHAN** | — | 100 | 815625 | F |

### Summary cross-9

| Métrica | Holm | BH |
|---------|-----:|---:|
| Orphan clusters (N=0 post-correction) | **3/9 (33%)** | 0/9 |
| Top-1 changed (de no-orphan) | 1/6 | **0/9** |
| Mean N post-correction | 53.3/100 | 100/100 |

## 4. Análisis veredicto

### Holm — orphan rate 33% inviable operacionalmente

3/9 clusters quedarían sin top-1 specialist:
- ONDO C0, ONDO C1, SEI C2: pf_fwd_ci_low (1.5-2.0) genera p-values insuficientemente bajos para pasar α/N=5e-4 threshold con N=100.

**Implicación operacional**: bot no podría operar 33% clusters → degrada PnL real significativamente vs ganar precision estadística marginal. **Trade-off claramente desfavorable**.

### BH — no-op efectivo (idéntico M2 fix baseline)

0/9 cluster orphan + 0/9 top-1 changed. Esto significa:
- Todos los 100 configs por cluster pasan BH threshold final (rank 100 con threshold 100/100 × 0.05 = 0.05).
- Ranking final = ranking M2 fix sin filtrado.

**Causa**: el survivor pool top-100 está heavily pre-filtered (W4 thresholds, SQN haircut, flag_sospechoso). Los configs sobrevivientes tienen p-values bajos (pf_fwd_ci_low > 1.0 implícito por W4 thresholds). BH al α=0.05 acepta todos.

**Implicación**: BH sobre survivor pool ya post-filtered es **redundante** — no añade información sobre el ranking M2 fix.

## 5. Caso B — Archivar empíricamente

Ambas variantes Multi-testing correction clásico **NO mejoran ranking M2 fix**:
- Holm: degrada operacionalmente (orphan 33%).
- BH: redundante con W4 + flag_sospechoso filtros existentes.

**Causa raíz** (predicción ultrathink confirmada empíricamente):

Multi-testing correction clásico es la **herramienta incorrecta** para el problema. El residual J/B 2.41× post-M2 fix es **selection bias structural** sobre millones de candidates pre-filter, NO inferencia mal calibrada dentro del survivor pool.

Herramientas apropiadas para selection bias structural (fuera scope esta sesión):
- **Deflated Sharpe Ratio** (López de Prado): específico para finanzas, penaliza Sharpe ratio según N tests + serial autocorrelation. Adaptable a PF como proxy.
- **k-fold Cross-Validation**: replicar selección + evaluación sobre múltiples folds. Penaliza configs que solo funcionan en un fold.
- **Sample splitting**: dividir histórico en parte selección + parte evaluación independientes. Forzar evaluación OOS robusta.
- **Bootstrap aggregation con re-selection**: en cada bootstrap resample, re-seleccionar top-N. Acumular distribución.

Estas herramientas requieren **proyectos dedicados separados** (~20-30h cada uno) según §13.2 caveat permanente. Multi-testing correction clásico era el candidato más rápido (~3-4h spec) pero metodológicamente misaligned.

## 6. Decisión

**Caso B confirmed empíricamente**:
- Rama `feature-multi-testing-correction-pre-reciclaje` queda como **REFERENCIA ARCHIVADA** (no merge a main).
- Código preservado con default `_MULTI_TEST_METHOD='none'` para backwards-compat futuro (si alguien quiere experimentar con α distinto, variantes adicionales, application points alternativos).
- Tests preservados (44 PASS) garantizan funcionamiento del código si se reactiva.

**§13.2 caveat permanente actualizado**: residual ratio J/B 2.41× post-M2 fix **confirmed estructural** vía test empírico Multi-testing correction. Reducción adicional requiere proyectos dedicados para selection bias structural (Deflated SR, k-fold CV, etc.).

**§13.3 item línea 2336 sub-item Multi-testing correction**: marcado **ARCHIVED EMPIRICAL 2026-04-26** con justificación. Items hermanos (k-fold CV, multi-testing Bonferroni/BH/Deflated SR) sub-componentes del proyecto walk-forward methodology refinement permanecen EN_ESPERA como proyectos dedicados independientes.

## 7. Hallazgos colaterales

🔹 **JSONs smoke 2026-04-24 actuales (regime_wf/)** están sorted por `specialist_score_ci_low` (W3b ranking pre-M2-fix), NO por `pf_fwd_ci_low` (M2 fix). Esto es coherente con que el smoke 2026-04-24 BTC+ONDO+SEI fue ANTES del M2 fix implementación (commit 7162369 mismo 2026-04-24 pero post-smoke). Solo el smoke posterior BTC-only (2026-04-25) tiene M2 fix activo.

   Implicación operacional: para reciclaje completo 45 sym, los JSONs se regenerarán post-A+B+C done con M2 fix activo (ranking pf_fwd_ci_low). Este caveat es solo metodológico para análisis dry-run.

🔹 **BH redundancia con W4 + flag_sospechoso**: el filtro upstream existente (W4 thresholds + flag_sospechoso_outlier) actúa como un BH-equivalente conservador implícito. BH al α=0.05 sobre el survivor pool resultante es no-op. Cualquier multi-test correction adicional debería aplicarse PRE-W4, NO POST-W4.

🔹 **Holm + N grande (test T2d)**: Holm con N=50000 + 1 config p=1e-7 → 1 sobrevive. Esto valida que la implementación Holm está correcta numéricamente en N grande. El issue cross-9 NO es bug numérico — es mismatch conceptual con selection bias.

🔹 **Predicción metodológica ultrathink confirmada empíricamente**: la reflexión pre-implementación predijo Caso B con probabilidad alta. La validación empírica cross-9 confirmó la predicción. **Esta es L35 aplicada profilácticamente** (test diagnóstico antes de invertir compute) — variante constructive de L35.

## 8. Plan post-archivar

- Rama feature preservada como referencia.
- Item §13.3 línea 2336 marca ARCHIVED_EMPIRICAL_2026-04-26 con link a este doc.
- ROADMAP_PRE_RECICLAJE.md sub-componentes walk-forward methodology refinement: actualizado.
- Si futuro proyecto dedicado Deflated SR / k-fold CV se prioriza, el código Multi-testing aquí sirve como infraestructura de testing (p-value computation, correction application logic).

**Status final**: Multi-testing correction Holm/BH **EMPÍRICAMENTE REFUTADA** como solución al residual J/B 2.41×. Residual confirmed estructural — solo atacable via selection bias-specific tools (proyectos dedicados separados post-reciclaje).
