# Alpha Residual — Caracterización Descriptiva N=60 post-v2.4.5

**Fecha**: 2026-04-26 sesión 2
**Scope**: ventana operacional bot v2.4.5 desde deploy 2026-04-22 09:46:10 UTC hasta 2026-04-26 09:00 UTC (~3.9 días, 60 trades).
**Status**: **DESCRIPTIVA NO CONCLUYENTE — N=60 borderline §12 L34 + análisis Welch correcto pendiente N≥100**.

## 0. Caveat metodológico institucional

Esta caracterización es **EXPLORATORIA CUALITATIVA** sobre una ventana N=60 cuyo poder estadístico es insuficiente para conclusiones formales. Se aplica explícitamente **§12 L34** (hipótesis emergentes con N<50 — aquí N=60 borderline — requieren validación multi-segmento N≥100 antes de elevar a §13.3 activo) y **§12 L36** (predicción ultrathink registrada explícitamente pre-análisis).

**NO se crean items §13.3 nuevos a partir de esta caracterización**. Output: framework pre-listo para análisis Welch correcto cuando llegue N≥100 (~2026-05-01) coincidente con disparador v2.6-inv.

Base referencial: audit C1 sesión 1 2026-04-26 (commit `aa8bb2d`) reportó alpha_residual N=60 = -5.76 USDT (-0.096/trade), EMPEORA vs A.1 N=26 (-0.066/trade) — degradación +45%. Datos crudos reproducidos: `attribution_per_trade_20260426_1324.csv`.

## 1. Predicciones ultrathink pre-análisis (§12 L36)

Registradas ANTES de descomposición:

| Hipótesis | Mecanismo | Predicción cuantitativa |
|---|---|---|
| (a) Edge real estructural marginal | sistema sin reciclar genera edge ~1.0-1.1 PF cross-universe | gini < 0.4, distribución uniforme |
| (b) Régimen mercado adverso ventana específica | post-v2.4.5 régimen distinto a A.1 | sub-ventana 3 / sub-ventana 1 > 1.5× |
| (c) Símbolos drift específicos | 4 clusters CANDIDATO EXCLUSION concentran degradación | top-4 clusters acumulan >70% alpha negativo |
| (d) Mix a+b+c | combinación factores | múltiples factores pero magnitudes moderadas |

**Predicción Claude pre-análisis**: (c) dominante (60-80% concentración) + (b) secundario, gini esperado 0.55-0.70.

**Predicción Ricardo (spec)**: similar, (c) dominante + (b) secundario.

## 2. Descomposición multi-dimensional

### 2.1 Per (símbolo, cluster)

23 unidades (sym, cluster). Top-5 contribuidores negativos:

| Sym/Cl | N | α total | α/trade | PnL | WR% | CANDIDATO |
|---|---:|---:|---:|---:|---:|:---:|
| RENDER/USDT C1 | 7 | -1.169 | -0.167 | -0.368 | 29% | **Y** |
| TAO/USDT C0 | 3 | -0.629 | -0.210 | -0.090 | 33% | . |
| GRT/USDT C0 | 4 | -0.572 | -0.143 | -0.192 | 25% | . |
| ONDO/USDT C2 | 8 | -0.570 | -0.071 | -0.140 | 25% | **Y** |
| BNB/USDT C0 | 5 | -0.458 | -0.092 | -0.051 | 20% | **Y** |

5 unidades con α positivo (suma +0.642). 18 unidades con α negativo (suma -6.406).

**Concentración 4 CANDIDATO EXCLUSION**:
- N=25/60 trades (41.7% volumen).
- α=−2.575 USDT (**44.7% del α total**).
- α/trade CANDIDATO −0.103 vs resto −0.091 (diferencia solo 0.012 USDT/trade).

**Hallazgo crítico**: TAO_C0 (-0.629) y GRT_C0 (-0.572) son **top contributors NO documentados como CANDIDATO EXCLUSION**. Si la lógica fuera "concentrate-on-outliers", emergerían en cualquier filtro de exclusión. Su presencia indica que el problema NO se limita a clusters CANDIDATO actuales.

### 2.2 Per símbolo (agregado cross-clusters)

Top-3 negativos: RENDER (-1.17, 7t), TAO (-0.63, 3t), GRT (-0.57, 4t). Top-3 positivos: MANA (+0.14), APT (+0.05), BTC (+0.01, 1t).

### 2.3 Sub-ventanas temporales

| Bucket | Range | N | α total | α/trade | PnL | WR% |
|---|---|---:|---:|---:|---:|---:|
| B1 (early) | 04-22 12:00 → 04-23 20:00 | 20 | -1.339 | -0.067 | -0.049 | 35% |
| B2 (mid) | 04-23 20:00 → 04-25 08:00 | 20 | -1.986 | -0.099 | -0.219 | 30% |
| B3 (late) | 04-25 09:00 → 04-26 09:00 | 20 | -2.438 | -0.122 | -0.467 | 30% |

**Pattern degradación monotónica creciente confirmado**. Ratio B3/B1 = 1.82× α/trade. WR% caída 35→30%. PnL acelera de -0.049 a -0.467 USDT (×9.5).

### 2.4 Strategy: TF vs MR

**60/60 trades TF** (TODOS). 0 trades MR en N=60. Caracterización aplica solo al edge TF (~39 specialists activos del universo). Specialists MR rescues (SEI C2, STX C2, UNI C0, LTC C2, DOT C1, BCH C0) NO produjeron trades en esta ventana.

### 2.5 Side: LONG vs SHORT

| Side | N | α total | α/trade | PnL | WR% |
|---|---:|---:|---:|---:|---:|
| long | 34 | -2.322 | -0.068 | -0.349 | 26% |
| short | 26 | -3.441 | -0.132 | -0.387 | 38% |

**Paradoja asymmetric magnitude**: SHORTS ganan más frecuentemente (38% vs 26%, +12pp) PERO α/trade peor (1.94×). Cuando los shorts pierden, pierden grande. Cross-session validation: matches audit C1 sesión 1 H1 ratio 1.48-1.94 (aquí 1.94, upper bound).

### 2.6 Hold duration buckets

| Bucket | N | α total | α/trade | PnL | WR% |
|---|---:|---:|---:|---:|---:|
| <1h | 0 | — | — | — | — |
| 1-4h | 22 | -2.444 | -0.111 | -0.867 | 14% |
| 4-12h | 22 | -2.440 | -0.111 | -0.169 | 41% |
| 12-24h | 13 | -0.973 | -0.075 | +0.011 | 38% |
| >24h | 3 | +0.093 | +0.031 | +0.290 | 67% |

**Contraintuitivo**: trades MÁS LARGOS tienen MEJOR α (refuta predicción Claude "trades >12h peor"). Trades 1-12h dominan α negativo (84.6% del total). Trades >24h marginalmente positivos (3 trades, sample insuficiente).

Insight: exits prematuros (1-4h con WR 14%) son problemáticos. Posible mecanismo: cancelaciones tempranas (cancel_tf, cancel_zona, div_exit) capturan ruido sin alpha real; trades que sobreviven a hold largo capturan edge tendencia.

## 3. Concentration metrics

### 3.1 Heatmap símbolo × sub-ventana

(α en USDT, N entre paréntesis, símbolos ordenados por α total ascendente)

| Symbol | B1 (early) | B2 (mid) | B3 (late) | Total |
|---|---|---|---|---:|
| RENDER/USDT | -0.283 (2) | -0.664 (3) | -0.221 (2) | -1.168 |
| TAO/USDT | -0.078 (1) | — | -0.551 (2) | -0.629 |
| GRT/USDT | — | -0.423 (2) | -0.149 (2) | -0.572 |
| ONDO/USDT | +0.045 (2) | -0.150 (3) | -0.466 (3) | -0.570 |
| DOGE/USDT | -0.414 (1) | -0.143 (1) | — | -0.557 |
| BNB/USDT | -0.182 (2) | -0.276 (3) | — | -0.458 |
| SEI/USDT | -0.304 (4) | -0.073 (1) | — | -0.377 |
| ENA/USDT | +0.238 (1) | — | -0.391 (4) | -0.152 |
| SAND/USDT | -0.254 (2) | +0.248 (2) | — | -0.006 |
| MANA/USDT | +0.189 (1) | -0.051 (2) | — | +0.138 |
| **TOTAL** | **-1.339 (20)** | **-1.986 (20)** | **-2.438 (20)** | **-5.764 (60)** |

(Solo símbolos con N≥3 mostrados; lista completa en CSV crudo.)

**Patterns observados**:
- **RENDER**: degradación sostenida B1+B2+B3 (concentrada B2 -0.66).
- **ONDO**: degradación monotónica creciente +0.05→-0.15→-0.47 (deteriorating clear).
- **TAO**: pattern bipolar B1+B3, sin trades B2 (concentración B3 -0.55).
- **GRT**: concentrado mid-late (0→-0.42→-0.15).
- **ENA**: flip dramático B1+0.24 → B3-0.39 (regime change suspect).
- **SEI**: concentrado early (-0.30+−0.07 luego silencioso).

### 3.2 Gini coefficient

Aplicado a contribuciones α negativas:

| Métrica | Valor | Interpretación |
|---|---:|---|
| Gini per-trade (52 trades α<0) | **0.3642** | Concentración MODERADA-BAJA |
| Gini per (sym,cluster) (18 unidades α<0) | **0.3670** | Similar |
| Top 10% trades → % α negativo | 23.7% | Distribución relativamente plana |
| Top 20% trades → % α negativo | **41.1%** | (predicción Claude: 70%+) |
| Top 30% trades → % α negativo | 54.0% | |
| Top 5 (sym,cluster) → % α negativo | **53.0%** | (predicción Claude: top-4 >70%) |

**Predicción Claude REFUTADA en magnitud**: distribución MUCHO más uniforme que esperado. No es pattern outlier-dominated.

### 3.3 Cross-correlation temporal

| Test | ρ | Interpretación |
|---|---:|---|
| Spearman(trade_idx, α_cumulative) | -0.998 | Monotonic decrease (autocorrelated, esperado) |
| Spearman(trade_idx, α_per_trade) | -0.176 | Débil pero direccionalmente correcto (degradación creciente per-trade) |

ρ=-0.176 con N=60 está por debajo del threshold de significancia (~|ρ|>0.25 para p<0.05). **No conclusivo individualmente**, consistente con "degradación temporal real pero magnitud per-trade noisy". Power requiere N≥100.

## 4. Validación predicciones (§12 L36)

| Hipótesis | Predicción cuantitativa | Resultado | Veredicto |
|---|---|---|---|
| (a) Edge estructural uniforme | Gini < 0.4 | **Gini 0.36** | **STRONG SUPPORT** |
| (b) Régimen adverso temporal | B3/B1 > 1.5× | **1.82×** + monotónica | **PARTIAL SUPPORT** (sostenido, no ventana específica) |
| (c) 4 CANDIDATO concentran >70% α | **44.7%** observed | **REFUTADA cuantitativamente** |
| (d) MIX (a)+(b)+(c residual) | combinación moderada | best-fit observed | **BEST-FIT HYPOTHESIS** |

**Predicción Claude pre-análisis**: (c) dominante 60-80% + (b) secundario, gini 0.55-0.70.
**Realidad**: (a)+(b) dominantes, (c) residual modesto, gini 0.36.

**Refutación cuantitativa Claude** (§12 L36 caso "predicción refutada redirige antes invertir compute"): la concentración es ~50% menor de lo predicho, gini ~50% menor de lo predicho. La predicción "drift-on-outliers" surgida de leer "4 clusters CANDIDATO EXCLUSION" en audit C1 fue **prematura** — el dataset N=60 muestra pattern más distribuido cross-universe.

## 5. Implicaciones operacionales (DESCRIPTIVAS, no concluyentes)

### 5.1 Si patrón (a)+(b) sostenido en N≥100 (mismo perfil)

- **Reciclaje completo necesario**, no surgical de specialists CANDIDATO EXCLUSION.
- Edge real estructural ~1.0-1.1 PF distribuido cross-universe.
- Reciclaje julio (calendario actual ~2026-05-12 a 05-22) consistente con esta lectura.
- Decisión Ricardo institucional 2026-04-24 "todas mejoras A+B+C antes de reciclaje" sigue siendo correcta.

### 5.2 Si (c) emerge dominante en N≥100 (cambio perfil)

- Surgical exclusion específica de 4 (o más) clusters CANDIDATO podría recuperar edge.
- Re-evaluar política política adelantar reciclaje §13.3 L1398.

### 5.3 Si (b) profundiza en N≥100 (degradación acelera)

- Régimen mercado adverso global; reciclaje con misma methodology podría no resolver.
- Re-considerar W3+W4+M2 fix coverage cross-régimen.

### 5.4 Caveats institucionales

- Caracterización TF-only (0 MR trades en N=60). MR rescues no caracterizados.
- N=60 ventana 3.9 días; régimen mercado puede ser específico abril 2026 lateral-alcista.
- audit_residual depende analyzer v2.4.1 attribution; sujeto §12 L26 (ecuación cierra ≠ atribución correcta per-componente).

## 6. Framework pre-listo para análisis Welch correcto N≥100

Cuando llegue N≥100 (~2026-05-01 disparador v2.6-inv):

### 6.1 Tests específicos a ejecutar

1. **Welch t-test α/trade B1+B2+B3 vs B4+B5** (cuando N≥100 permite 5 sub-ventanas N=20):
   - H0: α/trade temporal-uniforme.
   - H1: degradación temporal sostenida.
   - Threshold significancia: p<0.05 con Cohen d>0.5.

2. **Welch α/trade CANDIDATO EXCLUSION clusters vs resto universo** (con N CANDIDATO ≥30, N resto ≥50):
   - H0: α/trade equivalente cross-classification.
   - H1: CANDIDATO peor.
   - Validar concentración cuantitativamente.

3. **Spearman ρ(trade_idx, α_per_trade)** con N≥100:
   - Significancia esperada |ρ|>0.20 con p<0.05.
   - Confirmar pattern monotónico real vs noise.

4. **Bootstrap CI95 α/trade ventana móvil 25 trades**:
   - Detectar puntos de degradación brusca vs sostenida.
   - Cross-check estructural vs régimen-específico.

5. **Welch α/trade LONG vs SHORT** (cross-session continuity):
   - audit C1 sesión 1 reportó ratio 1.48-1.94. N=60 sesión 2 ratio 1.94. Validar persistencia.

6. **Cross-correlation α/trade vs ATR/régimen GMM markers** per-cluster:
   - Identificar si la degradación correlaciona con régimen volatility BTC macro.

### 6.2 Disparadores escalación a §13.3 (CRITERIOS estrictos §12 L34)

Solo crear items §13.3 nuevos si **N≥100 valida**:
- Welch p<0.05 + Cohen d>0.5 cross-segmento sostenido.
- Magnitud no degrada en cross-segmento (no es artefacto S4 Aug-Sept 2026 ventana específica).
- Pattern persiste post-validación bootstrap (no es outliers).

Si N≥100 NO produce significancia o produce signo distinto → **archivar como caracterización descriptiva permanente sin item §13.3** (consistente §12 L34 protocolo).

### 6.3 Outputs esperados análisis N≥100

- Tabla cross-5-buckets temporales con CI bootstrap.
- Veredicto formal Hipótesis (a)/(b)/(c)/(d) con magnitudes.
- Decisión Ricardo: adelantar reciclaje (criterio empírico §13.3 L1398) o mantener calendario julio.

## 7. Hallazgos colaterales / aprendizajes meta

1. **Predicción ultrathink Claude refutada en magnitud (§12 L36 caso "refutada")**: la lectura de "4 clusters CANDIDATO EXCLUSION + alpha cae 45%" generó pattern mental "outlier-dominated" que no aplica. Distribución es más uniforme. Este es un caso clásico §12 L36 donde predicción refutada **redirige** antes de invertir compute en hipótesis errónea. Ahorra elevación prematura de items §13.3 surgical-exclusion específicos.

2. **§12 L34 profilácticamente aplicada**: aunque hay temptation hipótesis emergentes (TAO_C0, GRT_C0 nuevos contribuidores, paradoja LONG/SHORT magnitude, hold duration anti-intuición), NINGUNA elevada a §13.3. Validación N≥100 obligatoria.

3. **Cross-session validation H1 short/long ratio**: audit C1 sesión 1 reportó 1.48-1.94. Sesión 2 N=60 reproduce 1.94 (upper bound). Pattern direccional sostenido cross-session pero sigue refutado como hipótesis estructural por audit sesión 1 stress-test cross-segmento.

4. **TF-only caracterización**: hallazgo metodológico — N=60 carece de trades MR para análisis cross-strategy. Cualquier conclusión strategy-related limitada a TF universe.

5. **Hold duration anti-intuición**: trades MÁS LARGOS mejor alpha. Sugiere que cancelaciones tempranas (cancel_tf, div_exit, zone_exit dentro 1-12h) pueden capturar ruido sin alpha real. Mecanismo plausible para investigación post-reciclaje (no §13.3 ahora).

6. **Concentración relativa moderada**: top 5 (sym,cluster) units = 53% α negativo. NO outlier-dominated NO completamente uniforme. Pattern mixto consistente con sistema operacional real (algunos contribuidores estructurales + ruido cross-universe).

## 8. Caveats permanentes

- N=60 borderline §12 L34. Validación N≥100 obligatoria pre-decisión.
- Caracterización TF-only.
- Régimen mercado abril 2026 lateral-alcista ~3.9 días — NO representa bearish/tail-risk.
- Analyzer v2.4.1 attribution sujeto §12 L26 (validación per-componente periódica).
- Predicciones Claude refutadas en magnitud — calibración retrospectiva metodológica.
- 0 items §13.3 nuevos creados. Disparadores existentes (v2.6-inv N≥100, v2.6-exit N≥150, política adelantar reciclaje §13.3 L1398) cubren escalación natural.

---

**Reproducibilidad**: data crudo `attribution_per_trade_20260426_1324.csv` (N=60 post-v2.4.5, audit C1 sesión 1 commit `aa8bb2d`). Scripts Python ad-hoc inline en commit `<placeholder-commit>`. Cualquier sesión futura puede regenerar tablas con descomposición idéntica.

**Status final**: caracterización descriptiva DONE. Ningún item §13.3 nuevo. Framework pre-listo análisis Welch N≥100 (~2026-05-01).
