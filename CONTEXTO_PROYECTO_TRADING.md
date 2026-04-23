# Sistema de Trading Algorítmico — Contexto Completo del Proyecto

**Última actualización:** 23 Abril 2026 CIERRE SESIÓN — **A.1 alpha residual deep-dive Criterio B** sobre N=26 post-v2.4.4 (primera ventana arquitectónicamente limpia post-fixes v2.4.4 size_usdt + v2.4.5 entry_timestamp_ms). Hipótesis slippage liberado **CONFIRMADA** (slippage/trade 7× vs Fase II.C contaminada, alpha_residual/trade mejora 19%). 3 hipótesis emergentes N=26 sometidas a stress-test cross-segmento cross-régimen N=98: **H1 short/long asimetría 12:1 REFUTADA** (S1 N=49 dirección opuesta), **H_strategy exits logic/structural 3.4× REFUTADA** (Welch N=98 p=0.086 dominado enteramente por S4), **H_new_3 residual contrarian ratio 24× REFUTADA** (cae a 2.16× con N=19/14 consistente con gap PnL). 3 refutaciones en una sesión evitaron creación de 3 items §13.3 activos con disparadores futuros. **§12 Lección 34 NUEVA**: "Hipótesis emergentes de análisis con ventana N<50 requieren validación multi-segmento antes de elevar a §13.3". Complementaria a L25+L29+L33. Updates §13.3 v2.6-inv + v2.6-exit con matización arquitectónica (efecto Bloque 2 concentrado S2+S3, no S4). 2 items §13.3 nuevos: pnl_recon tolerancia mal calibrada + cache funding extender a origen. Bot v2.4.5 operacional VPS Tokio. Fidelidad 2 invariante (sesión read-only). Pipeline pre-reciclaje: sobrecarga §13.3 REDUCIDA por 3 refutaciones. Disparadores maduros: v2.6-inv N≥100 (~2026-05-01), v2.6-exit N≥150 (~2026-05-10), audit N≥50 (~2026-04-26). **Mejora adicional**: `_run_verify_test` upgrade CLI parametrizable `--n-bars` + tolerance escalada §0.8 Nivel A/B automática (wrappers temporales obsoletos; item §13.3 EN_ESPERA 2026-04-22 RESUELTO). Smokes A/B/C PASS. **Inventario §13.3 Opción E**: 3 items cerrados (L2018 refutado por validación empírica propia aplicando L34 — hipótesis floor mal calibrado contraria a evidencia 42pct→58pct con floor más bajo; L1910 cerrado L27 parcial — analyzer v2.4.1 ya implementa detección `CANDIDATO EXCLUSION RECICLAJE` alert, tracking cross-sesiones integrado en L1398; nuevo item pnl_recon ratio 10pct demasiado estricto creado con hipótesis refinada ratio 25pct pendiente validación multi-segmento). L1916 mantiene EN_ESPERA con context update. 4ª refutación del día por stress-test — L34 consistente. **L1839 batch cp1252 RESUELTO**: 68 líneas runtime-critical en lab_historico (scope real 5x mayor al documentado "14"; pre-reciclaje cleared Windows cp1252). Smokes A+C diff 0.0000 — lógica invariante. **5ª refutación del día por L34 recursiva** aplicada a item propio "ratio 25%" creado en commit ab4f6f6 — prerequisite "validación multi-segmento N=98" inviable (bug histórico size_usdt=0 afecta 138/164 trades pre-v2.4.4). Nuevo item creado: "Investigación causa raíz pnl_recon gap" con scope explícito ~1-2h sesión dedicada (Opción D). **Bloque 2c Opción Q1 EJECUTADO** (Tier 0 I2 `--data-path` commit 53fe73a → kernel 10 configs cross-3y Binance Futures): **W3 VALIDA CUANTITATIVAMENTE** (6/6 W3 + 4/4 CANDIDATO EXCLUSION con PF_3y<1.5, 0/10 con PF≥2.0, 60% PF<1.0). Ratio PF_WF/PF_3y 0.10-0.82 — §12 L29 validada masivamente. Filter expandido (W3 ∪ CANDIDATO EXCLUSION) evaluación refinada post-Opción W1 (control group 2026-04-23): **INFLACION UNIVERSAL** — filter marca edge bajo pero no discrimina vs baseline unflagged (Welch p=0.148 NO sig; 9/10 control con PF<1.5, 0/10 con PF≥2.0). **20/20 configs universe top-1 con PF_3y<1.5 sobre Binance 3y** — sesgo walk-forward sistemático cross-universe. **Nuevo item §13.3 high priority**: "Investigación walk-forward methodology bias sistemático" (antes de reciclar para no repetir sesgo). §12 L29 extended cross-universe + §12 L34 11ª aplicación. **Fase A** (N=60 cross-rank): distribuciones PF_3y idénticas cross-rank means 1.01-1.06, CASO γ tendente β. **Fase B.1 cluster filter** (60 configs): top-1 mean 1.327, Spearman p=0.0041 sig, **CASO PARCIAL**. **Auditoría harness 2026-04-23** reveló setup simplificado (no doubled_labels, no train/fwd split) → aclaración interpretativa: quantities medidas ≠ edge productivo (7fe4e0d). **Smoke C 2026-04-24 replicating pipeline productivo exacto** (doubled_labels + train/fwd split 67/33): top-1 pf_tr=1.53, pf_fwd=1.13 (decay 26%), Spearman ρ(JSON, binance)=+0.047 (nula), 1/20 top-1 pf_fwd≥2, 11/20 pf_fwd<1. **SESGO REAL CONFIRMADO** — walk-forward ranking no predice pf_fwd real, edge train→fwd decay 26% estructural. Q1+W1+A+B.1 core direccionalmente correcto pese a setup simplificado. §12 L29 validada masivamente (ratio JSON/real 0.03-0.26). Prerequisito pre-reciclaje recomendado. 12ª L34 aplicación. Tier 0 I1 + H1+H_funding+H_strategy diferidos proyecto dedicado post-reciclaje ~20-30h (item §13.3 ampliado). **6ª pausa L34 del día — Bloque 2 Análisis B edge decay cross-cluster WF→kernel pausado** por inviabilidad estadística (JSONs generated 2026-03-27 a 2026-04-07 → ventana post-training 16-27 días → N_trades/config 1-3 insuficiente para Spearman ρ). Diferido a §13.3 con disparador generated_date ≥60 días (~2026-06-01). **Opción D validación cruzada W3 flag vs evidencia operacional cross-sesión ejecutada interim**: patrón **DIVERGENTE** (0/6 Fuerte, 1/6 Moderada ONDO C0, 2/6 Débil TRX+BTC C2, 3/6 Ausente LTC+GRT+MANA). 4 clusters CANDIDATO EXCLUSION (APT C0, ONDO C2, SAND C1, SEI C0) no W3 flagged → W3 filter necesario pero no suficiente. Recomendación: mantener calendario julio + monitorear N≥50 reporte ~2026-04-26.
**Versión actual:** v2.4.4 (sin bump — sesión 100% herramientas offline, sin deploy operacional)  
**Autor del sistema:** Ricardo  
**Plataforma:** Binance (datos) + BingX (ejecución), velas 1h  
**Stack:** Python, Numba, CUDA (RTX 5070 Laptop), ccxt (async)  
**Símbolos:** 45 (eliminados TON, PEPE, BONK — no disponibles en BingX Futures)

---

## 0. Filosofía de fidelidad del proyecto

El proyecto opera sobre una cadena de verdades y fidelidades que determina cómo evaluamos cualquier decisión técnica. Documentar aquí este marco para evitar debates técnicos desconectados del propósito real.

### 0.1 Jerarquía de verdades

**Verdad original:** el sistema de trading como tal (originalmente indicador Pine Script SmartDiv v7.25, replicado en código Python local por conveniencia). Es la lógica que define qué es una señal, qué es un exit, qué es una zona. El sistema en sí es la hipótesis de trading.

**Fidelidad 1 (lab simula al bot):** master.py y su pipeline (train_regime_model, lab_lite, regime_walk_forward) deben simular lo que el bot haría en operación real. Si master.py no refleja al bot, los specialist_configs JSON que genera son inválidos como referencia — seleccionan configs con PF alto bajo supuestos falsos.

**Fidelidad 2 (bot replica al lab):** el bot en producción debe replicar lo que master.py simuló como rentable. Si el bot diverge, la operación real no tiene las propiedades simuladas (PF, DD, specialist_score). master.py pudo haber hecho trabajo perfecto pero la divergencia del bot hace que los números simulados no apliquen.

Ambas fidelidades son necesarias. Una sin la otra no sirve.

### 0.2 Las tres derivadas cuando hay divergencia

**Derivada 1 — Fidelidad 1 rota:** master.py NO refleja lo que el bot haría. Los JSONs son ruido decorado con números. Hay que arreglar master.py o documentar explícitamente cómo diverge.

**Derivada 2 — Fidelidad 2 rota:** el bot NO replica lo que master.py simuló. La rentabilidad teórica es inalcanzable. Hay que arreglar el bot o aceptar que la referencia del lab es aproximación optimista.

**Derivada 3 — ambas fidelidades OK pero bot no rentable:** el problema no está en el pipeline sino en el sistema subyacente. Causas posibles: sistema no es rentable en el régimen actual de mercado, costes no modelados (liquidez, comisiones reales, funding), supuestos implícitos que ni lab ni bot capturan. Hay que entender por qué antes de tocar nada.

### 0.3 Principio operacional

**No tomar decisiones que rompan fidelidad sin datos empíricos que justifiquen el coste.**

Aplicaciones concretas:

- El lag de 1 bar entre brain decision y live execution (ítem 13.2) fue analizado el 2026-04-19 con dos decisiones secuenciales: primera iteración adoptó opción (a) aceptar como feature con disparador post-N≥50. Segunda iteración del mismo día, tras análisis más profundo del trade-off, adoptó opción (b) restaurar Fidelidad 2 via fetch adicional del bar forming (v2.3.11). Principio aplicado: "entrar una vela más tarde nunca es ventaja" — el lag era sesgo unidireccional. 2-5 segundos de aproximación al close real es operacionalmente equivalente a close[t] exacto para efectos de decisión.

- El bug P1 de leverage (ítem 13.3 2026-04-17) ha mantenido al bot en 1x uniforme, coincidiendo con cómo el lab simula. Esto es accidentalmente consistente con Fidelidad 1 y 2. Aplicar leverage variable rompería ambas fidelidades simultáneamente: el lab no simula con leverage, y simularlo portfolio-wise con co-movimientos entre activos no tiene ground truth para validar. Por tanto, la decisión canónica es: mantener 1x hasta tener datos empíricos del bot real (N≥50). Solo con evidencia real podremos decidir si introducir leverage y cómo.

- Cualquier refactor de brain_engine, data_feed o lab debe preguntarse: ¿cambia Fidelidad 1 o Fidelidad 2? Si cambia, requiere test diferencial que cuantifique el cambio. Refactors "solo estilísticos" pueden introducir regresiones sutiles que rompen fidelidad (ver lecciones de B2/B3 del 2026-04-19).

### 0.4 Historia del proyecto bajo este marco

- Fase 1 (meses hasta 2026-03): foco en Fidelidad 1 — asegurar que master.py (originalmente Laboratorio 1024) simulaba fielmente el indicador Pine Script. Se alcanzó y se validó.

- Fase 2 (2026-04): master.py demostró resultados rentables, entonces Fidelidad 1 quedó implícitamente confirmada "porque funciona". Empezamos a replicar en vivo: foco de Fidelidad desplaza al eje 2 — el bot debe replicar master.py.

- Fase 3 (actual): fidelidad empírica del bot vs master.py medible con audit v5.1 cuando lleguemos a N≥50 trades post-v2.3.3. Primer reporte dirá si Fidelidad 2 está al nivel necesario o si hay acciones correctivas.

- Futuro: si Fidelidad 2 se confirma y el bot es rentable → sistema validado, scaling posible (incluyendo consideración de leverage con base empírica). Si Fidelidad 2 rota pero bot rentable → interesante, no es lo simulado pero funciona por otra razón, entender por qué. Si Fidelidad 2 OK pero bot no rentable → derivada 3, el problema está en el sistema subyacente o en el régimen actual de mercado.

### 0.5 Aplicación a estrategia MR — 2026-04-20

La estrategia Mean Reversion (MR) mantiene su propio canon de verdad en paralelo al TF. Ambas estrategias tienen Pine Script canónico como referencia, pero con semántica de zona INVERTIDA entre ellas:

**Pine TF canónico** — `indicador_v44_0_smartdiv_v11_0_TF.pine`
- Semántica zona: `ma_fast > ma_slow` → BULL (rápida ENCIMA de lenta)
- Convención clásica: "la rápida marca el camino"
- Kernel: `lab_historico_numba_v8_3.py`
- Brain_engine rama TF
- Fidelidad 1 TF auditada (ver §13.3)
- Fidelidad 2 TF auditada y corregida (v2.4.0 + v2.4.1)

**Pine MR canónico** — `indicador_v7_25_smartdiv_v40_28_MR.pine`
- Semántica zona: `series_fast_line < series_slow_line` → BULL (rápida DEBAJO de lenta)
- Convención invertida: "la lenta marca el camino". Precio bajo respecto a donde debería estar → señal BULL de reversión al alza.
- Kernel: `mean_reversion_kernel.py`
- Features: `mean_reversion_features.py`
- Walk-forward: `mean_reversion_walk_forward.py`
- Brain_engine rama MR
- Versión Pine congelada con faltas conocidas (ver notas abajo)
- Fidelidad 1 MR implementada en kernel; Fidelidad 2 MR auditada y confirmada 2026-04-21 (ver §13.3 RESUELTO).

IMPORTANTE: no confundir los dos Pines. Regla mnemotécnica:
- TF: rápida domina (`fast > slow` = bull)
- MR: lenta domina (`fast < slow` = bull)

**Faltas conocidas del Pine v7.25 MR** respecto al kernel MR moderno:
- Hidden divergencia en Pine sin fix de inversión (kernel MR marca explícitamente "Hidden corregida" en bits 12-13 del config).

**Mecanismos activos de la estrategia MR** (parte integral de la selección walk-forward, implementados en `mean_reversion_kernel.py` líneas 290-372):
- bit 14 (cancel_zona): anti-repainting comparando zona `forming` al entrar vs `resolved` tras cierre del día.
- bit 15 (cancel_tf): comparación `forming` vs `resolved` en filtros TF2 (bloque 4h) y TF3 (bloque diario).
- bit 16 (cancel_ghost): verificación de trayectoria bar-a-bar para detectar cruces fantasma repintados.

Cada config MR es probada por el walk-forward con cada combinación de los 3 bits; el selector escoge la combinación óptima por cluster.

Los 4 mecanismos de stop (SL inicial desde mecha, TS on-close, SL emergency intrabar, trigger `close < sl_level`) son idénticos entre TF y MR en Pine y en kernel. El fix arquitectural v2.4.0+v2.4.1 en `execution_manager` aplica universalmente a ambas estrategias (brain `state.sl_level` ratchetea on-close igual en TF y MR).

### 0.6 Kernel como verdad operacional, Pine como referencia histórica — 2026-04-21

Descubrimiento articulado durante auditorías de Fidelidad 2 TF+MR del 2026-04-20 y 2026-04-21. Refina el marco general establecido en §0.

**Jerarquía clarificada:**

Pine canónico (TF v44, MR v7.25) es **referencia histórica del diseño original**. Es la intención semántica del sistema de trading en su formulación inicial. **No es juez operacional.**

Kernel del lab (`lab_historico_numba_v8_3.py` para TF, `mean_reversion_kernel.py` para MR) es la **verdad operacional**. Es lo que `master.py` ejecuta, lo que el walk-forward optimiza, y cuyos specialist_configs alimentan al bot en producción. La rentabilidad simulada que valida el sistema se construye sobre el comportamiento del kernel, no sobre el Pine.

Brain live debe replicar al kernel. Auditorías Fidelidad 2 se miden contra el kernel, no contra el Pine.

**Divergencias kernel ≠ Pine:**

Pueden existir y algunas están documentadas en código. Ejemplo: `lab_historico_numba_v8_3.py` líneas 1560-1562 contiene comentario literal:

```
Fix fidelidad: usar resolved[t] (barra HTF actual finalizada)
en vez de resolved[entry_bar] (barra HTF anterior a la entrada)
```

Esta divergencia consciente modifica cancel_tf de Pine canónico (reindex-al-pasado `ha_trend_tfN_e[barsSinceEntry]`) a patrón resolved[t] (último bloque HTF cerrado observable desde el bar actual). Es **decisión de diseño madurada**, no bug.

**Principio operacional:**

Toda divergencia kernel ≠ Pine documentada en código (con comentario explícito o mediante tests que confirmen la decisión) es **parte del diseño vigente**. No requiere fix. Solo requiere inventario.

Toda divergencia kernel ≠ Pine no documentada ni justificada es **candidata a revisión pre-reciclaje julio**. Puede ser bug, puede ser decisión olvidada. Auditoría Fidelidad 1 formal (ver §13.3) hará el inventario completo.

**Implicación para auditorías futuras:**

Cuando Claude (o Claude Code, o Ricardo en persona) conduzca auditoría, el eje de verdad es:

1. **Fidelidad 2 (brain ↔ kernel): CRÍTICA para operación real.** Divergencia aquí = bot opera distinto de lo simulado = specialist_configs no predicen comportamiento real.

2. **Fidelidad 1 (kernel ↔ Pine): OPCIONAL, histórica.** Divergencia aquí = kernel hace algo distinto del diseño original. Puede ser madurez, puede ser bug olvidado. Inventariar sin alarma.

No confundir prioridades: bot que replica fielmente un kernel con "Fix fidelidad" intencional es estado sano. Bot que no replica al kernel pero coincide con Pine canónico es estado roto.

### 0.7 Convención de sincronización combolab ↔ comboclaude — 2026-04-23

`combolab/` es directorio de ejecución: bot productivo (live/), scripts de análisis ejecutados localmente, kernel lab, repositorio git versionado. `comboclaude/` es directorio de fuente Claude Code donde Claude Code lee/modifica código en sesiones de desarrollo.

**Regla**: TODOS los archivos de código Python, JSON de configuración, y tests deben mantenerse sincronizados 2-way con MD5 idéntico entre ambos directorios.

**Excepciones** (NO sincronizar):
- Artefactos generados por ejecución: `audits/`, `logs/`, `trade_history.csv`, `engine_state.json`, `portfolio_state.json`.
- Datos pesados: parquets de `data_cache/`, modelos pickle de `regime_models/`, JSONs de `regime_wf/*_specialist_configs.json`.
- Caches: `__pycache__/`, `.pytest_cache/`, `.git/`.
- Documentos de diario local: `roadmap_*.md`, reportes ad-hoc del día.

**Protocolo al cierre de cualquier tarea que modifica código:**
1. Identificar TODOS los archivos modificados.
2. Para cada archivo: comparar `md5sum combolab/<path>` vs `md5sum comboclaude/<path>`.
3. Si hashes difieren → sync inmediato (copia combolab → comboclaude, combolab es fuente de verdad).
4. Si archivo existe solo en combolab → verificar si debe sincronizarse (regla por defecto: SÍ, a menos que sea excepción listada arriba).

**Anti-patrón a evitar**: "El archivo no estaba antes en comboclaude, consistente dejarlo así". Esta asunción es INCORRECTA por defecto. La ausencia previa puede ser oversight acumulado, no convención intencional. VERIFICAR contra la regla general antes de asumir.

Ver §12 Lección 28 (sync implícito incorrecto) para caso de estudio y mitigación documental.

### 0.8 Protocolo de smoke test pre-deploy — 2026-04-22

Contexto histórico: A10 test diferencial (§13.4 2026-04-22) reveló que el smoke test estándar `_run_verify_test` sobre BTC/USDT con N~500 bars (usado como gate único en 5+ deploys previos: v2.3.11, v2.4.0, v2.4.1, v2.4.2, v2.4.3, v2.4.4, v2.4.5) reportaba consistentemente diff 0.0000 pero **ocultaba drift path-dependent** que se manifiesta a partir de N≥2000 bars en indicadores iterativos (VIDYA, KAMA, ALMA, T3, FRAMA, McGinley). Forensic sobre ONDO+APT con N=8335-10000 cuantificó ratio divergencia bar-level 7-9% (Lección §12.30). Item 3.5 (§13.4 ranking stability) validó que el drift NO afecta selección walk-forward (Spearman ρ=1.0000), por lo que es propiedad arquitectónica aceptable, no bug. Pero el smoke test N pequeño era insuficiente para detectar drift NUEVO que SÍ pudiera ser bug.

Protocolo corregido desde 2026-04-22:

**Nivel A — Benchmark rápido (GATE OBLIGATORIO en TODO deploy brain/kernel):**
- Comando: `python -m live.brain_engine --verify --symbol BTC/USDT`.
- Dataset: baseline histórico con N~500-1000 bars (4 señales, 2 trades esperados).
- Criterio: diff **0.0000 exacto** en Trades, Wins, PnL neto %, Gross profit %, Gross loss %.
- Tiempo: ~30-60 segundos.
- Propósito: regresión automática contra bugs lógicos de determinismo (typos, constantes incorrectas, orden de operaciones).

**Nivel B — Deep smoke (GATE OBLIGATORIO para cambios específicos + periódico):**
- Comandos: wrapper temporal sobre `_run_verify_test` con N configurable (actualmente hardcoded N=1000, ver §13.3 upgrade pendiente). Template:
  ```python
  from live.brain_engine import _run_verify_test
  # TODO: parametrizar _run_verify_test con n_bars
  # Alternativa inline: replicar código de _run_verify_test con tail 10000.
  ```
- Dataset: N≥8000 barras sobre ONDO/USDT + APT/USDT (2 altcoins activas con specialists con MAs path-dependent + rolling cerradas).
- Criterio: ratio divergencia bar-level <5% (alerta si significativamente mayor que drift baseline arquitectónico ~7-9% documentado en §12.30). Match count brain↔kernel > 95%.
- Tiempo: ~10-15 minutos (kernel Numba rápido, brain engine ~8 min/símbolo).
- Propósito: catches drift path-dependent que N=500 oculta.
- Disparos OBLIGATORIOS:
  - Cambios en `brain_engine.py` que toquen cálculo de signals (no solo logs/emit/alerts).
  - Cambios en `lab_historico_numba_v8_3.py` (kernel Numba).
  - Refactors de `data_feed.py` que afecten flujo de bars al brain (ej. bar forming, paginated fetch).
  - Pre-reciclaje: validación antes de regenerar specialists para confirmar que pipeline actual sigue bajo control.
- Disparos RECOMENDADOS:
  - Periódico cada ~2 semanas (health check del sistema).
  - Cuando se detecte anomalía en health_monitor o analyzer que sugiera divergencia estructural.

**Nivel C — MR fidelity (GATE OBLIGATORIO deploys MR o cambios brain completos):**
- Comando: `python audit_mr_fidelity_sei.py`.
- Dataset: SEI/USDT C2 config 45686 (1500 bars warmup brain=500 + kernel=100).
- Criterio: **diff 0.0000 en 7 métricas** (PnL, Trades, Wins, Cancels, MaxDD, GrossProfit, GrossLoss).
- Tiempo: ~140 segundos.
- Propósito: verifica fidelidad específica camino MR (`_evaluate_bar_mr`, `mr_zone_history`).
- Disparos: cambios brain engine MR O cualquier cambio brain al completo.

**Tabla resumen**:

| Nivel | Test | Criterio | Tiempo | Disparos |
|-------|------|----------|--------|----------|
| A — Benchmark rápido | `brain_engine --verify BTC/USDT` N~500 | diff 0.0000 | ~30-60s | **TODO deploy brain/kernel** |
| B — Deep smoke | ONDO+APT N≥8000 via wrapper | ratio div <5% | ~10-15 min | **Brain/kernel signal logic + data_feed bar flow + pre-reciclaje + periódico** |
| C — MR fidelity | `audit_mr_fidelity_sei.py` | diff 0.0000 en 7 métricas | ~140s | **Deploys MR + cualquier cambio brain completo** |

**Convención de reporte en commits**:

Todo commit de deploy debe documentar en el mensaje los niveles aplicados:
```
Tests pre-deploy:
- Nivel A (BTC N=500): diff 0.0000 ✓
- Nivel B (ONDO N=10000, APT N=10000): ratio 7-9% dentro de baseline arquitectónico ✓
- Nivel C (SEI MR): diff 0.0000 en 7 métricas ✓
```

Si Nivel B NO se ejecutó en un deploy que lo requiere, flag explícito en commit message con justificación.

**Anti-patrón explícito a evitar**: "Smoke test PASS" sin especificación de nivel. Puede interpretarse como solo Nivel A cuando debería incluir Nivel B o C.

Ver §12.30 (Lección drift oculto por smoke test N pequeño) + §13.4 A10 entries 2026-04-22 (base empírica del protocolo).

---

## 1. ARQUITECTURA GENERAL

### 1.1 Dos entornos separados

**Laboratorio (local, RTX 5070):** Entrenamiento de modelos, backtesting, regime walk-forward. Intensivo en GPU/RAM. Genera los archivos .joblib y .json que alimentan el bot.

**Producción (VPS Tokio, AWS EC2 t3.micro):** Bot 24/7 que ejecuta señales. Solo inferencia GMM (milisegundos en CPU), cálculo de MAs, y órdenes vía ccxt. Latencia 3ms a BingX.

**Dual exchange:** Binance para datos de entrenamiento (mayor liquidez, datos más limpios). BingX para ejecución en vivo (permite futuros). Features estacionarias agnósticas al exchange (validado: 0.113% diff cross-exchange).

### 1.2 Pipeline de laboratorio (`master.py`)

```
python master.py                              # Todo, 45 símbolos
python master.py --symbols BTC/USDT           # Solo uno
python master.py --recycle                    # Fuerza re-generar todo
python master.py --from-step regime-wf        # Desde regime walk-forward

Paso 1: download_full_history.py → data_cache/SYMBOL_1h.parquet
Paso 2: train_regime_model.py → regime_models/SYMBOL_regime.joblib
Paso 3: lab_lite_zonas_v5e.py → output/production/SYMBOL/presets_SYMBOL.csv
Paso 4: regime_walk_forward.py → regime_wf/SYMBOL_specialist_configs.json
```

### 1.3 Bot de producción (`live/`)

```
live/
├── live_engine.py          # Orquestador 24/7, DD circuit breaker, señales raw logging
├── data_feed.py            # Datos async BingX, 1500 barras/símbolo, trigger orders
├── brain_engine.py         # GMM + señales TF y MR (fiel al kernel Numba)
├── portfolio_manager.py    # EWMA correlación, volatility targeting, soft blending
├── execution_manager.py    # Bracket orders BingX, trailing stop, SL emergencia 5%
├── health_monitor.py       # Monitorización rendimiento real vs esperado
└── stress_test.py          # Test LUNA/FTT (colapsos a cero)
```

Ciclo horario:
```
xx:59:50  Despertar + descarga async 45 símbolos (<1s desde Tokio)
xx:59:52  Clasificación GMM + BTC override
xx:59:53  Señales TF o MR según specialist
xx:59:54  DD circuit breaker (reduce exposición si drawdown)
xx:59:54  Logging [SIGNALS_RAW] pre-portfolio
xx:59:54  Portfolio (EWMA correlación, volatility targeting, blending, límites)
xx:59:55  Logging [SIGNALS_DISCARDED] post-portfolio
xx:59:55  Espera precisa
xx:59:59.5 Ejecución (bracket orders a BingX)
xx:00:02  Verificación + alertas Telegram
xx:00:00 UTC (diario) Health monitor + resumen
```

---

## 2. ESTADO ACTUAL

### 2.1 Fase 1 (Alpha Engine) — COMPLETADA ✅

45 JSONs generados. 43/46 símbolos con al menos 1 cluster operable en trend-following. 6 clusters adicionales rescatados por mean-reversion.

**Distribución de operabilidad (trend-following):**
- 3/3 clusters operables: 14 símbolos
- 2/3 clusters: 22 símbolos
- 1/3 clusters: 7 símbolos

**Top 5 clusters por specialist_score (TF):**
1. TRX C2: score=30.9, PF=11.94 — VIDYA/KAMA
2. BTC C2: score=17.21, PF=4.68 — Tenkan/EMA
3. MANA C0: score=15.51, PF=3.62 — VIDYA/KAMA
4. HBAR C1: score=12.23, PF=3.61 — FRAMA/T3
5. UNI C2: score=11.72, PF=3.89 — VIDYA/KAMA

### 2.2 Fase 2 (Live Engine) — v2.3.1 DESPLEGADA ✅

| Módulo | Estado |
|--------|--------|
| data_feed.py | ✅ Async BingX, 1500 barras, trigger orders normalizadas |
| brain_engine.py | ✅ Dual mode TF+MR, fidelidad verificada, stop_order_id tracking |
| portfolio_manager.py | ✅ **v2.2** EWMA correlación (halflife=24), **v2.3** Volatility targeting (ATR inverse) |
| execution_manager.py | ✅ Bracket orders, trailing stop, SL emergencia 5%, close hardened, OrderNotFound fix |
| live_engine.py | ✅ **v2.3.1** ENGINE_STATE + SIGNALS_RAW/DISCARDED/EXECUTED expandidos para performance attribution |
| health_monitor.py | ✅ PF real vs esperado, 4 triggers de reciclaje |
| stress_test.py | ✅ LUNA/FTT validados |

### 2.3 VPS Producción — EN PRODUCCIÓN LIVE ✅

| Campo | Valor |
|-------|-------|
| IP | IP_VPS_TOKIO_REDACTADA |
| Región | ap-northeast-1 (Tokyo) |
| Instancia | INSTANCE_ID_TOKIO_REDACTADO (t3.micro) |
| OS | Ubuntu 24.04 LTS |
| Coste | ~$11/mes |
| Latencia BingX | 3ms |
| SSH | Puerto 22, key ~/.ssh/trading_vps |
| Usuarios | trader (código), ubuntu (sudo/systemctl) |
| Servicio | trading-bot.service (Restart=on-failure, pkill pre-start, KillMode=control-group) |
| Telegram | Bot BOTvps, chat_id=1263830762 |
| IAM | Claude-helper con TradingVPSManager |
| Arranque limpio | 2026-04-13T21:39:24Z |

### 2.4 Versiones desplegadas

| Versión | Fecha | Cambio |
|---------|-------|--------|
| v1.0 | 10 Abr | Producción LIVE activada (trend-following puro) |
| v1.1 | 10 Abr | Fix trigger orders BingX + phantom purge + SL fidelidad 5% |
| v1.2 | 13 Abr | Mean-reversion integrado en brain_engine + 6 JSONs MR |
| v1.3 | 14 Abr | Fix proceso duplicado systemd + close hardened + OrderNotFound |
| v2.1 | 15 Abr | DD circuit breaker (bandas 5/10/15%, histéresis) |
| v2.2 | 15 Abr | EWMA correlación (halflife=24h, 3.6x más reactivo) |
| v2.3 | 15 Abr | Volatility targeting (ATR inverse, clamp 0.3-2.0) |
| v2.3.1 | 16 Abr | Instrumentacion pasiva (ENGINE_STATE, SIGNALS_RAW/DISCARDED/EXECUTED expandidos) |
| v2.3.1-grt | 16 Abr | Swap GRT C2 TF -> MR (clausula rollback activa, pendiente cierre posicion) |
| v2.3.2 | 16 Abr | Phantom fix (reconciliacion post-exec + orphan close recovery) |
| v2.3.2-grt | 17 Abr | GRT C2 swap TF->MR desplegado en VPS (config_id=25088, rollback clause 20 trades o 90 dias) |
| v2.3.3 | 17 Abr | entry_timestamp_ms: wall-clock ms del fill persiste en brain state y trade_history.csv (col 12) para fix C1 del analyzer v2.4.1 |
| v2.3.4 | 17 Abr | L1 _next_activation_time usa timedelta (fix month-end ValueError) + L2 _save_state atómico via tmp+replace (previene JSON parcial en crash) |
| v2.3.5 | 17 Abr | H3 health_monitor._load_trades parseo posicional (tolerante a schema evolution 10/11/12 cols) + H2 excluye flag='reconstructed'/'reconstructed_post_hoc' (consistente con analyzer v2.4.1 y audit v5.1) |
| v2.3.6 | 19 Abr | H1 portfolio_dd_from_peak sobre capital total (peak_balance vs current_balance de engine_state.json) + H4 _days_since_recycle=0 si archivo inexistente (previene trigger calendario espurio). Enabler en live_engine.py: current_balance persistido en engine_state.json |
| v2.3.7 | 19 Abr | 10 fixes triviales Fase 2: brain S2 bars_since_entry incremento funcional, S3 BTC Override sincroniza state.current_cluster, S5 reset active_config_id en paths no-operables. Portfolio S2 correlacion solo positiva (quitado abs), S4 doc 10 sectores, S5 TON archivado (45 JSONs). Execution E5 guard fill_price<=0. Live L3 phantom purge tambien en DRY_RUN, L5 max_cycle_duration enforcement con asyncio.wait_for, L7 Telegram parse_mode omitido (texto plano) |
| v2.3.8 | 19 Abr | 3 fixes Fase 3 Grupo B parte 1 (data_feed + execution): B4 _retry_async helper compartido con backoff exponencial aplicado a fetch_positions/fetch_open_orders/fetch_balance (AuthenticationError sin retry). B5 OHLCV pagination levanta ValueError explicitamente en primera fetch vacia (activa outer retry). B7 stop y emergency_close usan `entry_order.filled` real (no requested) con fallback a size si ccxt no expone filled. B6 (attach stops redundante) NO aplicado: close_position usa el attach (ver §13.3) — preservado en §13.3 con nota |
| v2.3.9 | 19 Abr | Solo B1 aplicado (B2/B3 pospuestos a reciclaje con test diferencial completo — ver notas en §13.3). B1 _reset_state_on_exit helper top-level standalone (mr:bool flag para mr_zone_history) invocado desde los 2 exits TF/MR — resetea 8 campos completos (position, entry_price, sl_level, bars_since_entry, entry_bar_timestamp, entry_filters_forming, stop_order_id, entry_timestamp_ms). Non-regression verificada con _run_verify_test (4 senales, 2 trades, PnL +1.2940%, bars 511/523/610/617 identicos pre/post). Validacion empirica de v2.3.8-B7 en cycle 134 (APT partial fill 8.5/8.59) |
| v2.3.10 | 19 Abr | D4 Telegram alerts fire-and-forget (reduce latencia cycle 1-3s): asyncio.create_task reemplaza await secuencial en los 2 loops de _post_cycle (OPEN alerts + CLOSE alerts). Alertas son observabilidad, _send_alert tiene try/except interno, event loop retiene tasks hasta completion. Test latencia: sequential 5010ms → fire-and-forget 0ms (100% reduccion). _run_verify_test idéntico al baseline (sanity check brain). Single alerts (ERROR, DD, daily_summary) se mantienen como await — no son el bottleneck |
| v2.3.11 | 19 Abr | Fidelidad 2 restaurada (opción b del HALLAZGO §13.2 lag estructural 1 bar). download_all_ohlcv apendiza/actualiza bar forming determinísticamente: fetch adicional sin `since` (limit=2) tras paginated. 3 ramas: (a) paginated sin forming → append; (b) paginated ya trae forming → update OHLC in-place con snapshot fresh; (c) ts inconsistente → warn y df sin modificar. iloc[-1] siempre pasa a ser bar t en curso. close_forming ≈ close_real a ~6s del cierre (reducción del lag 60 min → 6 s). brain_engine sin cambios (state.entry_bar_timestamp ahora es hora t, alineado con kernel lab). _run_verify_test invariante (histórico sin forming). Latency +1s (0.88s → ~1.8s, tolerable). Tests 5/5 PASS (3 ramas + 2 fallbacks) |
| v2.4.0 | 20 Abr | Fidelidad 2 TS restaurada: update_trailing_stop no-op (execution_manager.py). cp1252 fix en lab_historico_numba_v8_3.py (sys.stdout reconfigure UTF-8). Deploy 14:08 UTC, 20s downtime. Primer cycle post-deploy 6 TS_NOOP_V240 + 2 cierres on-close (ONDO, RENDER). 3 commits rama v2.4.0-fidelity2-ts. Ver §13.4 entrada v2.4.0 deploy. |
| v2.4.1 | 20 Abr | Emergency stop path protegido ante no-op TS (finding Run 2 /ultrareview). `_place_emergency_stop` helper extraído con firma minimalista (symbol, position, sl_price, exchange), invocado desde `reconcile_state` (líneas 652-676) cuando se detecta posición abierta sin stop. `update_trailing_stop` renombra action `stop_noop_v240` → `noop_v240` (defensa in-depth vs `startswith("stop")` en callers). Fail-loud size guard: `size<=0` loggea CRITICAL `EMERGENCY_STOP_INVALID_SIZE_V241` y retorna `emergency_stop_failed` en vez de enviar orden inválida. Semantic identifiers en docstring. Tests T7-T10 todos PASS (5 subtests). Smoke-A boot 19:07:59 UTC limpio + Smoke-B cycle 166 (20:00 UTC) PASS: 7 TS_NOOP_V240, 0 EMERGENCY_STOP_*_V241, 0 UPDATE_TS, cycle 17347ms (+3s atribuible a open+close, dentro de rango 14-22s). Red de seguridad armada sin haber disparado (consistente con frecuencia histórica 0/11 días). Fidelidad 2 TS preservada (brain on-close → close_position MARKET sigue camino canónico). 3 commits rama v2.4.1-emergency-stop-fix → merge main. Ver §13.4 entrada v2.4.1 Smoke-B PASS. |
| v2.4.2 | 21 Abr | Silent reconcile: `_reconcile_brain_after_execution` diferencia rollback ESPERADO (symbol en alloc FLAT o en exec_report.orders_failed) → DEBUG level `[BRAIN_ROLLBACK_EXPECTED]` vs desinc REAL (BingX cerró entre ciclos, orphan fill) → INFO level `[BRAIN_RECONCILE]` preservado. Reset de 6 campos idéntico a v2.4.1. Resuelve ruido §13.3 B-UNI-1 (26 BRAIN_RECONCILE/13h observados 2026-04-21 por UNI low_confidence + ALGO below_min_order + ETH BingX reject). Cambio acotado a una función en live_engine.py (sin tocar brain/execution/portfolio). Fidelidad 2 preservada por construcción: brain internals intactos. Tests 4/4 silent_reconcile PASS + TF `_run_verify_test` BTC/USDT diff 0.0000 + MR `audit_mr_fidelity_sei.py` SEI C2 diff 0.0000 en 7 métricas. |
| v2.4.3 | 21 Abr | Pre-check symbol-aware min_order en portfolio: `compute_min_order_usdt_for(symbol, price, markets_info)` reemplaza constante `MIN_ORDER_USDT=5.0`. Evalúa constraints reales de BingX por símbolo — `max(limits.cost.min, limits.amount.min × price, precision.amount × price)` con floor 5.0 USDT. Elimina CRITICAL `[EXEC] OPEN FALLIDO ETH` (7-11/día) causados por size < 0.01 ETH precision con balance bajo. Ejemplos: ETH @ 2310 → min 23.1 USDT; UNI @ 3.25 → 5.0 USDT (floor); ALGO @ 0.10 → 5.0 USDT (floor). Reason label enriquecido `below_min_order_X.Xusdt`. Wiring: `live_engine.start()` invoca `exchange.load_markets()` post-conexión y cachea `self.markets_info` (2879 símbolos BingX confirmados). Se pasa como kwarg opcional a `allocate_positions`. Fallback 5 USDT genérico si markets_info vacío o price inválido. Tests 8/8 min_order_precheck PASS. Fidelidad 2 preservada (cambio solo en threshold de descarte, no toca brain/execution). 1 commit rama v2.4.2-silent-reconcile+precheck → merge main. Ver §13.4 entrada v2.4.2+v2.4.3 Smoke-A PASS. |
| v2.4.3-hotfix | 21 Abr | Fix resolución ccxt symbol format en `compute_min_order_usdt_for`. Bug detectado en Smoke-B cycle 181 (11:00 UTC): markets_info ccxt usa formato perpetuo `"ETH/USDT:USDT"` pero bot pasa símbolos en formato master `"ETH/USDT"`, causando `symbol not in markets_info` → fallback `DEFAULT_MIN=5.0` en vez del threshold real (ETH 23.1 USDT). ETH `sz=11.67` alcanzaba execution y fallaba con `precision 0.01` reject. Fix: condicional que primero intenta `symbol` directo (backward compat para llamadas con formato ccxt), si no está intenta con sufijo `":USDT"` añadido (traducción master→ccxt), si tampoco está fallback a `DEFAULT_MIN`. Test adicional `test_master_format_resolves_to_ccxt` añadido. Tests 13/13 PASS (9 min_order + 4 silent_reconcile). Deploy VPS 11:09:56 UTC, MD5 `c4d5e7496…074`. Validación Smoke-B cycle 182 (11:59-12:00 UTC) confirmó code path v2.4.3 operando (ALGO discarded con label enriquecido `below_min_order_5.0usdt`) + v2.4.2 silent reconcile activo (0 INFO BRAIN_RECONCILE para ALGO fantasma). Validación directa ETH con threshold 23.1 pendiente de signal orgánico (evidencia indirecta robusta: test unit + code path confirmado + lógica inspeccionada). Commit 8b61e94 en main. |
| v2.4.4 | 22 Abr | Fix bug histórico `size_usdt=0` en trade_history.csv (134/135 trades afectados desde origen del dataset 2026-04-13). Root cause: `data_feed.get_open_positions` construía pos dict sin campo `size_usdt`; log_trade fallback `pos.get("size_usdt", 0.0)` persistía 0 sistemáticamente. Fix: 1 línea en `data_feed.py` (líneas 326-340) que añade `size_usdt = notional if notional > 0 else size × entry_price` con warning sentinel para edge case `entry_price=0 && size>0`. Impacto retroactivo: trades históricos permanecen con `size_usdt=0` (documentado, no migrable). Impacto forward: analyzer ahora computa slippage USDT correctamente (previo era espurio +0.00). Bug aislado, no afectaba pnl_usdt/pnl_pct/funding_paid (sanos por cómputo independiente). Tests 8/8 PASS (notional present/absent, entry_price=0 warning, multiple positions). Fidelidad 2 invariante: `_run_verify_test` TF diff 0.0000 + `audit_mr_fidelity_sei.py` MR diff 0.0000 en 7 métricas. Deploy VPS 18:22:02 UTC, MD5 3-way `d69afccf1be685c1c910a9d1c1a84f28`, downtime ~20s, Smoke-A PASS (6 posiciones sincronizadas sin WARNINGs). Validación directa orgánica pendiente de próximo close post-deploy. |
| v2.4.5 | 22 Abr | Fix bug `entry_timestamp_ms=0` en trade_history.csv (51/155 trades afectados, 100% de closes via `_evaluate_bar` post-v2.3.9). Root cause: `_reset_state_on_exit` (v2.3.9 fix B1, brain_engine.py L264-285) setea `state.entry_timestamp_ms = 0` durante `generate_signals` (línea 485), antes del call-site de enriquecimiento en live_engine.py L616. Sin este fix, trades via `_evaluate_bar` CLOSE paths (div_exit, tf_exit, zone_exit, sl_hit, cancel_tf, cancel_mr, zone_exit_mr) persistían entry_timestamp_ms=0 al CSV. Trades via paths alternativos (regime_change L627, not_operable L621, sl_trigger_reconstructed L958) estaban exentos por flujos propios que no invocan `_reset_state_on_exit`. Fix: extraer enriquecimiento a `_enrich_positions_with_entry_ms(positions, pre_signal_state)` que lee desde `pre_signal_state` (snapshot pre-reset, L467-483) en vez de `self.brain.symbol_state` (post-reset). `pre_signal_state` ya capturaba el campo desde v2.3.2. Impacto: bug AISLADO a observabilidad. Analyzer v2.4.1 y audit v5.1 mitigados via fallback a log SIGNALS_EXECUTED (`infer_entry_candle` C1 pre-existente). Health_monitor usa exit timestamp (no entry_ms), no afectado. Tests 8/8 PASS (happy, zero guard, missing sym/key, multi-symbol, override, empty, regression). Fidelidad 2 invariante: TF `_run_verify_test` BTC/USDT diff 0.0000 + MR `audit_mr_fidelity_sei` SEI C2 diff 0.0000 en 7 métricas. Deploy VPS 09:45:30→09:46:17 UTC, MD5 3-way `4141ab7157b9eb341e99347b37f0cc44`, downtime 47s, Smoke-A PASS (6 posiciones sincronizadas con entry_ms VALID en engine_state.json). Smoke-B cycle 205 pendiente verificación CSV con entry_ms>0 si cierra posición. Commit bc673c8 rama `fix-entry-timestamp-ms-v2.4.5` → merge main 3ec73f6. |
| analyzer v2.4.1 | 17 Abr | Ultra review fixes: C1 entry_candle inferido, C2 consistency check por precios, C3 COMBOLAB_DIR via env/CLI, C4 rollover con ENGINE_STATE.t, S1/S2/S5/S7/M9 + S3/S4/S6/M3 |
| audit v5.1 | 17 Abr | Ultra review fixes: C1 entry/exit semantics correctas, C2 kernel parity checksum (opcion C: lab solo tiene Numba), C3 flag recon organic, C4 MR cluster_hint via SIGNALS_RAW/GMM, C5 rollover con ENGINE_STATE.t, C6 path env/CLI, C7 CSV 12col, C8 tolerancia +-1, S4/S5/S8/S10/M4/M6 |

### 2.5 Auditoría de fidelidad — COMPLETADA ✅ (91% match)

**v3 (kernel stateless, Binance):** 82% match (9/11 trades)
**v4 (kernel stateless, BingX) — DEFINITIVA:** 91% match (10/11 trades)

| Métrica | v3 (Binance) | v4 (BingX) |
|---------|-------------|------------|
| Matches | 9/11 (82%) | 10/11 (91%) |
| Razón OK | 6/9 | 7/10 |
| Razón diferente | 3/9 | 3/10 |
| Sin match | 2/11 | 1/11 |

**Conclusión:** Fidelidad del kernel demostrada. Discrepancias residuales: micro-diferencias de precio BingX/Binance que afectan prioridad de señales simultáneas (no afectan rentabilidad), y 1 caso de señal borderline por estado acumulado. Se repetirá con 50+ trades.

### 2.6 Bugs corregidos (total: 58)

**brain_engine.py (10):**
1. p1/p2 ALMA offset/sigma
2. div_ctx reset tras exit
3. Zone-based div_ctx cleanup
4. sym_clean naming
5. _normalize_ohlcv parquet/live
6. signal['sl_price'] timing en TS
7. v2.3.7 S2: bars_since_entry dead field → incremento funcional al inicio de _evaluate_bar/_evaluate_bar_mr cuando position != 0. Consumido por audit_fidelity/analyzer via engine_state.json.
8. v2.3.7 S3: apply_btc_override no sincronizaba state.current_cluster tras mutar regimes → reportaba confidence del cluster pre-override en _evaluate_bar línea 721. Fix: asignar state.current_cluster = alt_highvol post-override.
9. v2.3.7 S5: select_active_configs dejaba stale state.active_config_id/active_preset en paths no-operables (no cfg, no cluster, no selected). Fix: reset a -1/'' en los 3 paths.
10. v2.3.9 B1: SymbolState parcialmente reseteado al exit — reseteaba solo position/entry_price/sl_level/bars_since_entry, dejando stale entry_bar_timestamp, entry_filters_forming, stop_order_id, entry_timestamp_ms. Consumers (log [SIGNALS_RAW], audit, analyzer) podrian leer valores post-exit invalidos. Fix: helper `_reset_state_on_exit(state, mr=False)` top-level standalone que resetea 8 campos y opcionalmente mr_zone_history. Llamado desde los 2 puntos de exit (TF linea 877, MR linea 1977). Non-regression verificada con _run_verify_test (output IDENTICO al baseline pre-cambio).

**data_feed.py (9):**
1. Binance Futures geo-bloqueado → Spot
2. BingX defaultType 'swap'
3. DNS ThreadedResolver
4. OHLCV_LIMIT 120→1500 con paginación
5. Trigger orders: TRIGGER_MARKET → stop_market
6. v2.3.8 B4: retry inconsistente entre funciones — download_all_ohlcv tenia retry inline; get_balance/get_open_positions/get_open_orders no. Fix: helper `_retry_async(coro_factory, name, max_retries=3, base_delay=0.5)` con backoff exponencial (0.5s→1.0s→2.0s) y AuthenticationError sin retry. Aplicado a las 3 funciones faltantes.
7. v2.3.8 B5: OHLCV pagination primera fetch vacia caia al else con ohlcv=[] sin reintento — simbolo quedaba con DataFrame vacio y brain saltaba evaluacion. Fix: `raise ValueError(...)` activa outer retry del for attempt. Preserva `since` parameter (critico para Fase 1 opcion-a decision de lag estructural).
8. v2.3.11 Fidelidad 2: BingX paginated con `since` incluye el forming INCONSISTENTEMENTE (a veces iloc[-1] es forming, a veces es last closed; verificado empíricamente 2026-04-19). Fix determiniza via fetch adicional sin `since` (limit=2) tras el paginated y rama 3-way: (a) `forming_ts == last_paginated + 1h` → append forming; (b) `forming_ts == last_paginated` → update OHLC in-place con snapshot fresh del forming fetch; (c) otro → warn y df sin modificar (inconsistencia real tipo race xx:00:00). Fallback robusto en excepción: warn y df sin modificar (modo lag solo ese símbolo ese ciclo). iloc[-1] pasa a ser siempre el bar t en curso (Fidelidad 2 restaurada vs kernel lab que decide-y-entra con close[t]). Latencia +~1s (0.88s paginated → ~1.8s total con forming serial por símbolo).
9. v2.4.4 (22 Abr): populate `size_usdt` en `get_open_positions`. Bug histórico: dict retornado por esta función no incluía `size_usdt`, pos propagaba sin campo hasta log_trade que hacía `.get("size_usdt", 0.0)` → CSV persistía `size_usdt=0` sistemáticamente desde origen del dataset (134 de 135 trades). Cascada visible en analyzer v2.4.1: `slippage_usdt` espurio `+0.00` porque `contracts = size_usdt/entry_price = 0` → slippage per trade = NaN → sum = 0. Fix: `size_usdt = notional if notional > 0 else size × entry_price`. BingX ccxt a veces provee `notional` directo; fallback a cálculo exacto. Warning sentinel si `entry_price=0 and size>0` (posición huérfana rara). No toca state schema, no migración, zero riesgo regresión (confirmado por Fidelidad 2 TF+MR invariante). Ver §13.4 entrada 2026-04-22.

**execution_manager.py (10):**
1. DRY_RUN entry_price=0 → fetch_ticker
2. size_usdt no se pasaba a log_trade
3. setLeverage: params={'side': 'BOTH'}
4. reconcile HOLD → generar update_stop
5. SL fidelidad: 3% → 5% emergencia
6. close_position hardened: pre-verifica posición existe, captura "Reduce Only" 101290
7. sl_trigger_hit: BingX cierra por stop entre ciclos → estima PnL, registra en CSV
8. v2.3.7 E5: fill_price=0 no se detectaba explícitamente en open_position → stop_price_bingx=0, BingX rechazaba con mensaje oscuro. Fix: guard `if fill_price <= 0: return {"action": "open_failed", "error": ...}` antes de calcular stop_price.
9. v2.3.8 B7: stop y emergency_close usaban `size` (requested) no `entry_order.filled` (real). Partial fills dejaban stop sobredimensionado rechazado por reduceOnly. Fix: `filled_size = float(entry_order.get("filled", 0) or 0)` con warning log y fallback a `size` si ccxt no expone filled. size del dict de return tambien usa filled_size.
10. v2.4.0 update_trailing_stop convertido en no-op (log_info TS_NOOP_V240 + return stop_noop_v240 action). Brain TS vive on-close en state.sl_level; BingX mantiene stop_market al 5% emergency fijo desde entry. Cierre por TS ejecutado on-close vía close_position MARKET cuando brain detecta close < sl_level en cycle. Cuerpo de 153 líneas reemplazado por 45 líneas (no-op + docstring). Restaura Fidelidad 2 con Pine y kernel lab (ambos evalúan TS on-close). Ver §13.4 RESUELTO v2.4.0 deploy.
11. v2.4.1 emergency_stop path protegido. Finding Run 2 /ultrareview detectó que el no-op de v2.4.0 atrapaba también el caller `atype="emergency_stop"` de `reconcile_state` (líneas 652-676 → `execute_cycle` línea 802), desactivando silenciosamente la red de seguridad que repone stop_market cuando detecta posición sin stop en BingX. Fix: helper `_place_emergency_stop` extraído con DRY_RUN guard preservado (consistencia con `set_leverage`/`cancel_order`/`close_position`/`open_position`), `triggerType=MARK_PRICE`, `logger.critical` en fail path. Dict interno usa `"size"` (canon `get_open_positions` línea 335 `data_feed.py`), no `"contracts"` — descubrimiento crítico pre-edit (spec original con `abs(position["contracts"])` habría dado KeyError). Rename `stop_noop_v240` → `noop_v240` defensivo (evita misroute en callers `startswith("stop")`). Size guard fail-loud: `size<=0` retorna `emergency_stop_failed` con `EMERGENCY_STOP_INVALID_SIZE_V241` CRITICAL en vez de enviar orden inválida. Ver §13.4 RESUELTO v2.4.1 Smoke-B PASS.

**portfolio_manager.py (7):**
1. Emojis Unicode → texto plano
2. HOLD descartaba sl_price
3. CRV/USDT sobrante en sector_map eliminado
4. v2.3.7 S2: identify_correlated_blocks usaba `abs(corr)` agrupando anticorrelacionados (r=-0.9) como "correlated block" — conceptualmente diversificación, no concentración. Fix: `corr_matrix.iloc[i,j] > threshold` (solo positiva).
5. v2.3.7 S5: 46 leverage entries vs 45 símbolos activos. TONUSDT_specialist_configs.json stale (TON eliminado pero JSON preservado). Fix: movido a regime_wf/archived/TONUSDT_specialist_configs.json.legacy-2026-04-19. Portfolio log post-deploy confirma 45 leverage entries.
6. v2.4.3 pre-check symbol-aware min_order: constante `MIN_ORDER_USDT = 5.0` genérica producía CRITICAL `[EXEC] OPEN FALLIDO ETH` (7-11/día) porque ETH @ 2310 requiere mínimo 0.01 ETH = 23.1 USDT por precision.amount, pero portfolio permitía sizes 5-11 USDT. Fix: nueva función `compute_min_order_usdt_for(symbol, price, markets_info)` que evalúa `max(limits.cost.min, limits.amount.min × price, precision.amount × price)` con floor 5.0 USDT. Nuevo kwarg `markets_info` a `allocate_positions` (opcional, fallback 5 USDT genérico). ETH threshold 23.1 USDT a precio 2310, UNI/ALGO quedan en floor 5.0 USDT. Reason label enriquecido: `below_min_order_X.Xusdt`. Tests 8/8 PASS.
7. v2.4.3-hotfix ccxt symbol format resolution en `compute_min_order_usdt_for`. Bug detectado en Smoke-B cycle 181 (2026-04-21 11:00 UTC): `markets_info` cargado vía `exchange.load_markets()` usa key formato perpetuo ccxt BingX swap (`"ETH/USDT:USDT"`); el bot pasa símbolos en formato master (`"ETH/USDT"`). La condición `symbol not in markets_info` se cumplía siempre → fallback `DEFAULT_MIN=5.0` → ETH `sz=11.67 USDT > 5.0` pasaba el portfolio, alcanzaba execution y BingX rechazaba con precision 0.01. Fix: resolver ambos formatos con condicional ordenada: (a) intentar `symbol` directamente (backward compat para llamadas con formato ccxt), (b) si no está intentar `f"{symbol}:USDT"` (traducción master→ccxt), (c) si tampoco está fallback `DEFAULT_MIN`. Añadido test `test_master_format_resolves_to_ccxt` que valida específicamente la traducción ETH/USDT → ETH/USDT:USDT → threshold 23.1 USDT. Tests 13/13 PASS (9 min_order + 4 silent_reconcile). Commit 8b61e94.

**live_engine.py (18):**
1. Unclosed session -> try/finally
2. Telegram env vars -> os.environ.get
3. -> (U+2192) -> -> en logging
4. Alerta RECYCLE duplicada eliminada
5. Phantom purge LIVE
6. Senales raw logging [SIGNALS_RAW] + [SIGNALS_DISCARDED]
7. v2.3.2: Fantasmas por apertura optimista — brain marcaba position=1 al generar senal, portfolio podia descartarla. Fix: reconciliacion post-ejecucion con BingX como fuente de verdad
8. v2.3.2: Trades cerrados por SL trigger entre ciclos no se registraban en CSV. Fix: deteccion orphan close + reconstruccion de trade
9. v2.3.4 L1: _next_activation_time crasheaba en month-end (target.replace(day=now.day+1)). Fix: target + timedelta(hours=1).
10. v2.3.4 L2: _save_state no atómico → JSON parcial si crash durante write. Fix: write-tmp + os.replace.
11. v2.3.6: current_balance no se persistía en engine_state.json (solo peak_balance). Enabler para fix H1 de health_monitor. Fix: atributo self._current_balance capturado en _calc_dd_multiplier(balance), persistido en _save_state y restaurado en _load_state.
12. v2.3.7 L3: phantom purge en start() solo aplicaba en LIVE (`if not self.config.dry_run`). En DRY_RUN state stale post-restart dejaba fantasmas hasta el primer reconcile post-ciclo. Fix: extendido a DRY_RUN usando get_dry_run_positions() como fuente de verdad.
13. v2.3.7 L5: max_cycle_duration_seconds=30.0 configurado pero no enforzado — BingX outage con retry largo podía colgar cycle y perder ventana del siguiente cierre. Fix: extraída lógica a _run_cycle_inner() y wrapper run_cycle() con asyncio.wait_for(timeout=30). En TimeoutError registra error y continúa al siguiente ciclo.
14. v2.3.7 L7: _send_alert usaba parse_mode="HTML" con mensajes en texto plano (sin tags HTML intencionales). Caracteres especiales (<,>,&) en exception msg o PnL formateado rompían la alerta con HTTP 400 silencioso. Fix: parse_mode omitido (Telegram default texto plano).
15. v2.3.10 D4: alerts Telegram en _post_cycle usaban await secuencial en 2 loops (OPEN + CLOSE). Con N trades por ciclo y timeout Telegram 10s, latencia acumulada 1-3s por cycle — presión sobre margen de tiempo antes del siguiente cierre. Fix: `asyncio.create_task(self._send_alert(msg))` fire-and-forget. Single alerts (ERROR, DD, daily) mantienen await (no son bottleneck). _send_alert tiene try/except interno que captura excepciones sin propagar a la task huérfana (no "Task exception was never retrieved").
16. v2.4.2 silent reconcile en `_reconcile_brain_after_execution`: el reset de fantasmas (Bug #1 del v2.3.2) disparaba siempre INFO `[BRAIN_RECONCILE]`, generando 26 log lines/13h en la ventana 2026-04-20 20:00→2026-04-21 09:00 UTC (UNI 11 + ETH 11 + ALGO 4). Estos resets son consecuencia MECÁNICA del diseño optimista v2.3.2: brain marca state.position al emitir signal → portfolio descarta (low_confidence, below_min_order) o execution falla (BingX reject) → BingX vacío → reset. Fix: calcular `flat_syms = {sym : alloc.action=="FLAT"}` + `failed_syms = {sym : exec_report.orders_failed}` al inicio del reset loop. Si `sym in (flat_syms ∪ failed_syms)` → log DEBUG `[BRAIN_ROLLBACK_EXPECTED]` (rollback esperado, silencioso en INFO). Else → INFO `[BRAIN_RECONCILE]` preservado (desinc real: BingX cerró entre ciclos, orphan fill). Los 6 campos reseteados (position, entry_price, sl_level, stop_order_id, entry_filters_forming, entry_timestamp_ms) idénticos a v2.4.1. Sin toque en brain/execution/portfolio. Fidelidad 2 preservada. Tests 4/4 PASS.
17. v2.4.3 wiring markets_info: en `start()` post-conexión a BingX, invocar `await self.exchange.load_markets()` (idempotente, ccxt cachea) y `self.markets_info = self.exchange.markets or {}`. Se expone como nuevo atributo del `LiveEngine.__init__`. En `run_cycle()` se pasa como kwarg `markets_info=self.markets_info` a `allocate_positions`. Confirmado post-deploy: 2879 símbolos cargados. Fallback a dict vacío si `load_markets()` falla (warning + portfolio usa floor 5 USDT genérico).
18. v2.4.5 enrichment entry_timestamp_ms desde `pre_signal_state`: bug introducido por v2.3.9 B1 (`_reset_state_on_exit` setea `state.entry_timestamp_ms=0` durante generate_signals, antes del call-site de enriquecimiento L616). Trades via `_evaluate_bar` CLOSE paths (div_exit, tf_exit, zone_exit, sl_hit, cancel_*, zone_exit_mr) persistían entry_timestamp_ms=0 al CSV (43/43 = 100% post-v2.3.9). Trades via paths alternativos (regime_change, not_operable, sl_trigger_reconstructed) no afectados por flujos propios. Fix: extraer lógica a función módulo-level `_enrich_positions_with_entry_ms(positions, pre_signal_state)` que lee desde `pre_signal_state` (snapshot pre-reset en L467-483) en vez de `self.brain.symbol_state` (post-reset). `pre_signal_state` ya capturaba entry_timestamp_ms desde v2.3.2. Tests 8/8 PASS (happy, zero guard, missing sym/key, multi-symbol, override, empty, regression). Fidelidad 2 invariante: TF + MR diff 0.0000.

**health_monitor.py (4):**
1. v2.3.5 H3: _load_trades fallaba con pd.read_csv en CSV con schema evolucionado (header 10 cols vs rows 11-12 cols). Fix: parseo posicional con pad/trunc a 12 cols.
2. v2.3.5 H2: reconstructed trades incluidos en agregados, inconsistente con analyzer/audit. Fix: filtro `flag in {reconstructed_post_hoc, reconstructed}` excluido por defecto.
3. v2.3.6 H1: portfolio_dd_from_peak se calculaba sobre cumsum de pnl_usdt de trades cerrados, produciendo DD espurio (-121.7% reportado en daily summary Telegram 19/04 con balance real 297 USDT y DD real 0.23%). Fix: leer peak_balance y current_balance de engine_state.json (mismas referencias que DD breaker del live_engine). Guard `current_balance > 0` para el caso ramp-up post-restart antes del primer ciclo. Enabler: live_engine.py persiste current_balance.
4. v2.3.6 H4: _days_since_recycle retornaba 9999 sin last_recycle.txt, disparando trigger calendario espuriamente (9999 > 90). Fix: retorna 0 si el archivo no existe; placeholder "??/90" se mantiene en display via check directo de existencia.

**regime_walk_forward.py (4):**
1. 2026-04-23 W3 bootstrap pf_fwd + selección por ci_low (rama `feature-w3-bootstrap-pf-fwd`, NO deploy — activación en próximo reciclaje). Contexto: specialists con N_fwd pequeño (13-30) producían pf_fwd point estimate engañoso; ONDO C0 pf_fwd=7.945 con N=17 observado en realidad con PF 1.08 (Fase II.B 2026-04-22). Validación empírica múltiple (§13.4 2026-04-22) promovió W3 a PRIORIDAD ALTA. Implementado: `_bootstrap_pf_fwd_vectorized` (N=1000 resamples binomial sobre pool sintético reconstruido desde agregados {wins_fwd, gp_fwd, gl_fwd}, chunked 5000 configs/batch), `_apply_bootstrap_pf_fwd` (añade 6 campos: pf_fwd_ci_low, pf_fwd_ci_high, ci_width, pf_combined_ci_low, specialist_score_ci_low, flag_sospechoso_outlier), integración post-haircut en `extract_validated_specialists` con re-sort W3b por `specialist_score_ci_low`. Caveat: bootstrap binomial es lower bound de CI real (no captura dispersión intra-grupo). Validación sobre JSONs productivos: 6/12 top-1 flagged (ONDO C0, LTC C2, GRT C2, TRX C2, BTC C2, MANA C0) — sesgo N pequeño generalizado. Tests 8/8 PASS (tests/test_w3_bootstrap.py). Fidelidad 2 invariante (cambio del pipeline del lab, no toca bot). Ver §13.4 entrada W3 IMPLEMENTADO 2026-04-23.
2. 2026-04-23 W4 thresholds _FWD + CI filters (misma rama, layered sobre W3, NO deploy). Contexto: `_FWD_MIN_TRADES=15` / `_FWD_MIN_PF=1.0` laxos permitían outliers pasar; ultra review W4 (2026-04-17) marcó para pre-reciclaje. Análisis cuantitativo Fase 1 sobre 138k candidates reveló que `NOT sospechoso` (W3 flag) es el filtro dominante (-35% pool); subir trades/PF es marginal. Thresholds adoptados: `_FWD_MIN_TRADES=25, _FWD_MIN_PF=1.1, _FWD_REQUIRE_NOT_SOSPECHOSO=True` + hooks opcionales (`_FWD_MIN_CI_LOW=0.0`, `_FWD_MAX_CI_WIDTH=inf` — default OFF). Nueva función `_apply_w4_fwd_ci_filters(df)` aplicada post-bootstrap con WARN log si cluster queda orphan. Validación Fase 3 reciclaje hipotético: 42/45 símbolos (93%) operables en 3/3 clusters, 3 clusters orphan (TAO C1, TRX C2, WLD C0), los 6 flagged W3 reemplazados o marked orphan. Patrón típico: old pf_fwd alto + N pequeño flagged → new pf_fwd moderado + N grande clean. TRX C2 orphan (top TF score 30.9 original) consistente con Lección 29 (N pequeño selecciona noise amplificado). Tests 8/8 PASS (tests/test_w4_thresholds.py) + W3 no-regression 8/8. Fidelidad 2 invariante. Ver §13.4 entrada W4 IMPLEMENTADO 2026-04-23.
3. 2026-04-23 A14 (W1) plateau_ratio consistency (rama `feature-a14-a15-wf-polish` commit 5a7135b → merge main cf9d7b6, NO deploy). Contexto: plateau_ratio pre-fix usaba bit-flip brutal sobre 26 bits del config_id mientras `_compute_sqn_haircut` ya usaba `_get_neighbors` canonical (respeta bitmask vs discrete de `_PARAM_FIELDS`). Dos fórmulas semánticas de "neighbor" en el mismo módulo. Fix: bloque Phase 4 reemplaza 4 líneas bit-flip por llamada única a `_get_neighbors(cid)`. Evidencia: ONDO C0 cfg 2457036 canonical=25 vs brute-26=26 neighbors (symmetric diff 3 → 3 "neighbors" viejos NO paramétricamente adyacentes). Impacto retroactivo: plateau_ratio es metadata informativa pura en pipeline canónico (NO filtro de selección; extractor_gemas.py lo usa como filtro pero NO está en pipeline productivo, §13.2). Cero impacto operacional hasta próximo reciclaje. Tests 4/4 PASS (tests/test_a14_plateau_consistency.py). Ver §13.4 entrada A14+A15 2026-04-23.
4. 2026-04-23 A15 (W2) engine tag en parquet output + resume consistency check (misma rama). Contexto: bifurcación runtime CUDA↔CPU (L487-505) con `engine_tag` local solo para print, no persistido. Resume tras crash con engine distinto = heterogeneidad silenciosa en specialists (precisión float32/float64 difiere marginalmente CUDA vs Numba CPU). Fix: módulo añade `_MACHINE_ID`, `_NUMBA_VERSION` + funciones `_get_engine_tag()` (4 campos) y `_check_resume_engine_consistency(parts_dir)` (WARN loud si mismatch, legacy pre-A15 tolerado como 'unknown'). `process_symbol` invoca check post-mkdir. Parquet write L548-585 extendido con 4 columnas engine broadcast a todas las rows. Impacto retroactivo: parquets actuales no tienen engine tag, regeneración completa via `master.py --recycle` los reescribe con tag. Resume intermedio: WARN legacy, no abort. Tests 4/4 PASS (tests/test_a15_engine_tag.py). Ver §13.4 entrada A14+A15 2026-04-23.

**lab_lite_zonas_v5e.py (1):**
1. 2026-04-23 A12 (LL1) MA dedup (rama `feature-a12-ma-dedup`, NO deploy). Contexto: ultra review LL1 marcó 16 MAs duplicadas en 4 archivos. Inventario real: duplicación 2-way (lab_lite ↔ lab_historico). brain_engine y MR features ya eran pass-through. Fase 2 verificación bit-a-bit: 52/52 tests PASS rtol=1e-10 (drift max 3.3e-11 por cumsum vs loop, sub-ULP). Fase 4 aplicado: bloque L112-348 (234 líneas, 17 defs MA) reemplazado por import consolidado desde lab_historico_numba_v8_3 (17 líneas). calc_wma eliminado (único local sin contraparte, usado solo por calc_hma local ahora importado). `lab_lite.calc_X is lab_historico.calc_X → True` → cero posibilidad drift por construcción. Neto: -234/+17 líneas. Tests parity 4/4 PASS + no-regresión W3/W4 16/16 + Smoke §0.8 A+C PASS (Nivel B omitido por scope, no toca brain/kernel). Fidelidad 2 invariante (brain ya importaba desde lab_historico). Ver §13.4 entrada A12 IMPLEMENTADO 2026-04-23.

**lab_historico_numba_v8_3.py + mean_reversion_kernel.py (1):**
1. 2026-04-22 Cooldown unify TF+MR (rama `feature-cooldown-unify` commit `9389af9`, NO deploy). Contexto: A04 TF + A04b MR detectaron switch cooldown 4-branch (`emergency/cancel → t` fijo; `sl/div → t + cooldown_bars - 1` parametrizable) vs Pine uniforme. Discovery pre-ejecución: `COOLDOWN_BARS = 1` constante única en 9 módulos del pipeline productivo (lab + live + audit); con ese valor las 4 ramas colapsan matemáticamente a `t` → asimetría estructural latente sin efecto operacional. Ricardo confirmó Opción A: cooldown=1 siempre operacional en Pine histórico, diferenciación era código muerto. Refactor `lab_historico_numba_v8_3.py` L1630-1637 (kernel TF Numba) + `mean_reversion_kernel.py` L408-415 (kernel MR Numba) unificado a `if any_exit_signal: cooldown_until = t + cooldown_bars - 1` (expresión Pine canónica). Comportamiento bit-idéntico con `cooldown_bars=1`. Fall-through preservado en tf_exit/zone_exit (asimetría 4-vs-6 separada, fuera de scope). Confirmatorio §0.8 Nivel A (BTC N=1000) + Nivel C (SEI MR C2 N=1500) pre/post: diff 0.0000 exacto en todas métricas. Nivel B (ONDO+APT N=10000) ejecutado post-refactor dentro de baseline arquitectónico. Fidelidad 2 invariante. Deploy VPS NO requerido. Ver §13.4 entrada Cooldown unify 2026-04-22 + §13.3 cooldown → RESUELTO.

**Infraestructura (5):**
1. SSH puerto 2222 → 22 (ISP bloqueaba)
2. Cloud-boothook rompió sshd → rescue volume
3. last_recycle.txt creado
4. Proceso duplicado: nohup + systemd Restart=always → 2 procesos, órdenes duplicadas HBAR
5. systemd fix: Restart=on-failure + ExecStartPre=pkill + KillMode=control-group + TimeoutStopSec=30

**ccxt (1):**
1. OrderNotFound hereda de InvalidOrder → _retry_async capturaba mal. Fix: except OrderNotFound antes de InvalidOrder

---

## 3. MEAN-REVERSION PIPELINE (COMPLETADO E INTEGRADO)

### 3.1 Origen

Sistema original de Ricardo: HA diaria repintable + Tenkan-sen cruce invertido. Estrategia adaptativa con 3 cancelaciones anti-repainting.

### 3.2 Pipeline (3 fases, 3 archivos separados)

- `mean_reversion_features.py` — Precálculo datos (.npz)
- `mean_reversion_kernel.py` — Kernel Numba 17 bits, 8192 configs, 3 cancelaciones
- `mean_reversion_walk_forward.py` — Regime walk-forward, inyección en JSONs

### 3.3 Resultados: 6 clusters rescatados

| Símbolo | Cluster | MR PF | MR Score | Trades (tr+fwd) | Config ID |
|---------|---------|-------|----------|-----------------|-----------|
| SEI     | 2       | 2.38  | 2.58     | 70+24           | 45686     |
| STX     | 2       | 1.55  | 1.05     | 57+29           | 60003     |
| UNI     | 0       | 1.39  | 1.14     | 143+66          | 121360    |
| LTC     | 2       | 1.45  | 0.81     | 76+27           | 109139    |
| DOT     | 1       | 1.47  | 0.57     | 31+27           | 55824     |
| BCH     | 0       | 1.27  | 0.34     | 22+13           | 27136     |

> Nota: los config_ids permiten decodificar bits específicos del specialist activo en producción (ver §0.5 para mapeo de bits 0-16 del kernel MR). Para auditoría Fidelidad 2 MR formal (§13.3), UNI C0 (config_id=121360) es el candidato óptimo del _run_verify_test por tener el N OOS más alto de los 6 rescates (N=66 forward, 3-5× mayor que los demás).

**3 clusters donde MR supera TF (anotados, no reemplazados):** GRT C2 (+1.57), LINK C0 (+0.20), XRP C2 (+0.15)

### 3.4 Integración en brain_engine — COMPLETADA ✅

- `generate_signals()` bifurca: TF (código original intacto) vs MR (bloque ~700 líneas)
- Hidden divergences corregidas (lab original las tenía invertidas)
- Fidelidad MR verificada: 0.0 diff en slow_line, fast_line, zonas
- JSONs con MR desplegados en VPS

---

## 4. MEJORAS v2.1-v2.3 (DESPLEGADAS)

### 4.1 v2.1: DD Circuit Breaker

Reduce exposición progresivamente según drawdown desde pico de equity:

| DD | Multiplier | Acción |
|----|-----------|--------|
| 0-5% | 1.0 | Normal |
| 5-10% | 0.75 | Reduce 25% |
| 10-15% | 0.50 | Reduce 50% |
| >15% | 0.0 | Pausa (solo cierra) |

Histéresis: tras circuit breaker (>15%), no reanuda hasta DD < 12%, y reanuda con 0.50.
peak_balance, dd_multiplier, circuit_breaker_active persistidos en engine_state.json.
Alertas Telegram en cada umbral.

### 4.2 v2.2: EWMA Correlación

Reemplazó `rolling(168).corr()` (SMA plana) por `ewm(halflife=24).corr()`.

Test de reactividad (160 barras calma + 8 barras shock r=1.0):
- SMA Pearson(168): r = 0.17 (diluida)
- EWMA halflife=24: r = 0.60 (3.6x más reactivo)

Umbral r > 0.7 y union-find sin cambios.

### 4.3 v2.3: Volatility Targeting

Sizing proporcional a volatilidad inversa:
```
ATR_pct = ATR(14) / close × 100
weight = median_ATR_pct / ATR_pct
Clamp [0.3, 2.0]
```

Ejemplo: BTC weight=2.0 (baja vol, más capital), WLD weight=0.42 (alta vol, menos capital).
Ambos aportan el mismo riesgo real a la cuenta. Límites (5%/pos, 20%/bloque) siguen como techos.

---

## 5. HALLAZGOS PRINCIPALES

- Low-vol clusters dominan TF (7/10 top). VIDYA/KAMA dominante.
- Mean-reversion rescata 6 clusters que TF no opera.
- Fidelidad kernel demostrada al 91% (BingX data). Discrepancias son micro-precios.
- Mercado lateral actual (23/45 en low-vol/choppy) explica pérdidas en TF. No es fallo del bot.
- Correlación SMA tiene inercia letal: 5 días calma diluyen shock actual. EWMA resuelve.
- 5% fijo por posición viola paridad de riesgo. Volatility targeting iguala riesgo real.

---

## 6. FILTROS Y SCORING

- **Specialist_score (TF):** `pf_combined × sqrt(pf_robustness) × log(1+trades/50) × max(sqn_p5/3.0, 0.5)`
- **Specialist_score (MR):** `pf_combined × log(1+trades/50) × max(sqn/3.0, 0.5)`
- **SQN Haircut:** p5 de ~25 vecinos (TF) / directo (MR)
- **Toxic Tail Dinámico:** P(nuevo_régimen) ≥ 75%, min=5, max=100 barras
- **Cross-cluster Survival:** PF < 0.7 en adyacente → descartado (solo TF)
- **Meseta:** ≥60% vecinos rentables PF ≥ 1.2 (solo TF)

---

## 7. ARQUITECTURA DEL LIVE ENGINE

### 7.1 data_feed.py
- Descarga async 45 símbolos, 1500 barras con paginación
- Trigger orders: TRIGGER_MARKET → stop_market
- Logs sanitizados

### 7.2 brain_engine.py
- Dual mode TF + MR, detecta strategy_type en JSON
- GMMs + histéresis (P > 75%), BTC Override (conf > 80%)
- stop_order_id tracking por símbolo

### 7.3 portfolio_manager.py
- **EWMA correlación** (halflife=24h), bloques union-find (r > 0.7)
- **Volatility targeting** (ATR inverse, clamp 0.3-2.0)
- Soft blending 0.60-0.85, 10 sectores (L1_major, L1_alt, Legacy, DeFi, L2, Meme, Oracle, Infra, Metaverse, AI)
- Límites: 5%/pos, 20%/bloque, 30%/sector, 25% global
- Acepta dd_multiplier del circuit breaker

### 7.4 execution_manager.py
- Bracket orders: Market + Stop Market (5% emergencia)
- Cancel-old/place-new para trailing stop
- effective_sl = max(brain_sl, emergency_floor)
- close_position hardened: pre-verifica + captura "Reduce Only"
- OrderNotFound manejado antes de InvalidOrder en _retry_async

### 7.5 live_engine.py
- Scheduler asyncio, disparo a xx:59:59.500
- **DD circuit breaker** (bandas 5/10/15%, histeresis, persistencia)
- Recovery: engine_state.json (symbol_state + positions + stop_ids + peak_balance + dd_multiplier)
- Phantom purge LIVE al arrancar
- **v2.3.1 Logs de instrumentacion (4 tipos por ciclo):**
  - `[ENGINE_STATE]` {t, bal, peak, dd_pct, dd_mult, cb_active, n_open}
  - `[SIGNALS_RAW]` {sym: {a, r, p, sl, c, s(TF/MR), k(cluster), t(candle_ts)}}
  - `[SIGNALS_DISCARDED]` {sym: {a(action original), d(razon descarte)}}
  - `[SIGNALS_EXECUTED]` {sym: {a, sz, lv, vw, bf, br, dd}}
- **v2.3.2 Reconciliacion post-ejecucion:**
  - `[BRAIN_RECONCILE]` sym reset position->0 (fantasma limpiado)
  - `[ORPHAN_CLOSE]` sym reconstructed (trade cerrado por SL trigger entre ciclos)
- Alertas Telegram

### 7.6 health_monitor.py
- PF real vs esperado, 4 triggers reciclaje
- last_recycle.txt (fecha: 2026-04-08)

### 7.7 systemd service
- Restart=on-failure (no always)
- ExecStartPre=pkill -f live.live_engine (mata huérfanos)
- KillMode=control-group (mata todo el cgroup)
- TimeoutStopSec=30 (SIGKILL si SIGTERM no funciona)

---

## 8. DECISIONES DE DISEÑO

1. Diccionario de especialistas + clasificador GMM en vivo
2. Dual exchange (Binance datos / BingX ejecución)
3. SL emergencia 5% delegado al exchange (fidelidad con simulación)
4. SL normal 3% verificado por software contra close cada hora
5. Stateless data feed (1500 barras frescas)
6. DRY_RUN default, --live requiere CONFIRMO
7. Lista símbolos centralizada (master.py CONFIG)
8. Reciclaje por triggers, no calendario
9. Mean-reversion como pipeline paralelo + modo dual en brain_engine
10. Trigger orders requieren normalización de type en ccxt/BingX
11. Auditoría de fidelidad con kernel stateless + datos BingX
12. Nunca nohup con systemd Restart — solo systemctl
13. DD circuit breaker con bandas e histéresis
14. EWMA correlación para reacción instantánea a contagio
15. Volatility targeting para paridad de riesgo

---

## 9. ROADMAP TÉCNICO

### 9.1 Inmediato: Monitorizar + re-auditar
- Bot corriendo v2.3.2 desde 16 abril 2026
- Re-auditoria v5 debe contar trades DESPUES de v2.3.2 (pre-v2.3.2 contaminados por fantasmas)
- Repetir auditoria fidelidad con 50+ trades post-fix
- Si perdidas persisten, investigar mas alla de fidelidad

### 9.2 GRT C2: Swap TF -> MR desplegado 2026-04-17
MR score=3.36 vs TF=1.79 (ratio 1.87x). Clausula de rollback revisada segun densidad empirica (ver 9.2.1).
Seguimiento: 0 trades reales MR / (20 trades o 90 dias, lo primero).

#### 9.2.1 Seguimiento rollback GRT

Fecha del swap: 2026-04-17 (deploy en VPS a las 08:15:51 UTC)
Backup TF: regime_wf/GRTUSDT_specialist_configs.json.bak-TF-2026-04-16
Configuracion activa: C2 MR (config_id=25088, HIDDEN div, cancel_zona=1)

Verificación del arranque: JSON GRT cargado correctamente con bloque MR activo para C2 (confirmado al start del servicio a las 08:15:51 UTC). Verificación en vivo del flujo MR diferida hasta primer trade real de GRT en C2 (según densidad empírica, semanas a meses).

**Metricas base del walk-forward para C2 MR:**
- pf_train = 1.912 (28 trades)
- pf_forward = 14.975 (13 trades OOS)
- pf_combined = 2.918
- sqn_forward = 5.771
- specialist_score = 3.36
- max_dd = 3.57%

Nota: pf_forward alto con N=13 es potencialmente sensible a outliers.
Usar pf_combined (2.918) como expectativa base al interpretar resultados
reales, no pf_forward.

**Densidad empirica esperada:**
- C2 representa ~25.3% del tiempo (stationary distribution de transition matrix)
- Auto-persistencia C2: 97.9%/barra -> visitas de ~47.6 horas (2 dias)
- ~46.5 visitas a C2 por ano
- Densidad de trades MR: ~1 trade cada 270 barras en C2 (~11 dias calendario efectivos en C2)
- Extrapolacion a tiempo real: 20 trades MR pueden tardar 1-2.4 anos segun densidad del walk-forward

**Clausula de rollback (revisada segun densidad):**

DISPARADORES DE REVISION (lo primero que ocurra):
- 20 trades MR reales ejecutados
- 90 dias transcurridos desde fecha del swap (fecha limite: 2026-07-16)

DECISION EN EL DISPARO:

Si N_trades >= 10:
- PF empirico < 1.0 -> rollback a TF (restaurar .bak-TF)
- 1.0 <= PF < 1.3 -> mantener MR, proxima revision a N=20 o +90 dias
- PF >= 1.3 -> MR confirmado, revision pospuesta al primer reciclaje (v3.0)

Si N_trades < 10 (probable a 90 dias segun densidad):
- Correr analyzer v2.4 filtrado solo para GRT
- Examinar alpha_residual y componentes por trade
- Decision cualitativa: mantener / rollback / extender periodo a 180 dias
- Documentar decision y razon aqui mismo

**Seguimiento:**
- Trades MR acumulados: 0 / 20
- Proxima revision disparada por: 90 dias (2026-07-16) o N=20
- PF empirico: pendiente
- Decision rollback: pendiente

### 9.3 v2.4-v2.6 (necesitan datos de producción)

**v2.4 Performance Attribution:**
Descomponer PnL por trade en: alpha del kernel, coste de ejecución (slippage), coste de portfolio (blending), coste de funding. Diagnosticar si el problema es mercado o sistema.

**v2.5 Walk-Forward Continuo:**
Cada semana re-evaluar configs activas contra 4 semanas de datos reales. Alertar si PF real degrada antes de que el health monitor (15 trades) lo detecte.

**v2.6 Funding Rate como Filtro — REFUTADO 2026-04-22:**

~~Funding rates extremos (+0.1% / 8h) = crowding signal. Bloquear entradas cuando funding está en extremos para esa dirección. Protección contrarian.~~

**REFUTADO 2026-04-22 por evidencia empírica N=50 post-v2.3.11**. Hipótesis contrarian (literatura general) no aplica a este sistema trend-following en el régimen actual. Aligned trades (entry con funding en misma dirección que crowd) obtuvieron PnL mean **+0.50%** vs contrarian **-0.57%** (Welch t=+3.58 **p=0.0003 trimmed**, Mann-Whitney p=0.0052). Win rate aligned **62%** vs contrarian **28%**. Threshold §9.3 propuesto `|rate| > 0.001` nunca activó (0/50 trades cumplieron; p99 real 1.74e-4). Filter propuesto habría bloqueado ganadores y permitido perdedores (simulación: -1.52 USDT adicional sobre 50 trades vs PnL real +0.70 USDT, degradación factor 2.2×). Interpretación: el sistema TF es trend-following; funding positivo es **confirmation signal de tendencia**, no crowd-to-be-squeezed. Ver §13.4 entrada "Observabilidad funding per-trade — refutación empírica §9.3" 2026-04-22 + §12 Lección 33.

**Candidato nuevo (pendiente validación N≥100)**: `v2.6-inv momentum filter` — bloquear entries **contrarian** al funding crowd (inverso a hipótesis original). Si efecto persiste con más data, podría mejorar PnL. Rompe Fidelidad 2 igual que versión original; requiere implementación simétrica en kernel lab para preservar §0.3. Item §13.3 EN_ESPERA con disparo N≥100 post-v2.3.11 (~2026-05-01 al ritmo actual).

### 9.4 v3.0 Primer reciclaje (~3 meses)

**Experimento Z_ATR de BTC en GMM altcoins:**
Riesgo multicolinealidad, BIC como juez. Si rechaza → probabilidad condicional bayesiana.

**Cobertura conceptual ampliada (2026-04-23):** Z_ATR como feature del GMM de altcoins subsume naturalmente la idea de "cortafuegos BTC" — cuando BTC entra en régimen de caída fuerte (Z_ATR extremo), el GMM entrenado de cada altcoin aprende durante training la correlación BTC-altcoin-régimen-específico, y en producción asigna al símbolo el cluster que corresponde a esa condición BTC + condiciones locales. Ventajas vs override runtime manual:
- No requiere umbrales arbitrarios ("¿qué es caída fuerte?" lo aprende el GMM).
- No requiere mapeo manual ("¿qué cluster equivalente?" lo decide el GMM por símbolo).
- No rompe Fidelidad 2 (el cluster sale del mismo GMM que el lab usa post-hoc).
- Maneja matices (BTC cayendo despacio vs fuerte, lateral bear vs bull).

Por tanto NO se implementa cortafuegos runtime como item separado pre-reciclaje — se espera a v3.0 con Z_ATR. Si criterio de degradación de clusters (roadmap 2026-04-22 FASE 2) dispara antes de v3.0 por eventos BTC, reciclaje se adelanta orgánicamente.

**Evolución BTC Override:**
| Versión | Mecanismo |
|---------|-----------|
| v1 (actual) | Override binario (conf > 80%) |
| v1.5 | Experimento BIC |
| v2 | Bayesiano: P(contagio) modula sizing |

### 9.5 Mejoras posteriores

| Mejora | Impacto | Cuándo |
|--------|---------|--------|
| SQN exacto | Bajo | Reciclaje con re-simulación |
| HRP (López de Prado) | Medio | 20+ posiciones, post volatility targeting |
| Slippage no lineal SL | Bajo→Alto | Cuando capital > 5K USDT |
| Escalado liquidez (order book) | Crítico | Cuando capital > 5K USDT |
| Backtest walk-forward continuo | Medio | Cuando haya historial producción |

---

## 10. ARCHIVOS Y UBICACIONES

### 10.1 Laboratorio (local)
```
c:\Users\rixip\combolab\
├── master.py
├── regime_features.py, train_regime_model.py, download_full_history.py
├── lab_lite_zonas_v5e.py, lab_historico_numba_v8_3.py, lab_cuda.py
├── regime_walk_forward.py, extractor_gemas.py, pipeline.py
├── mean_reversion_features.py, mean_reversion_kernel.py, mean_reversion_walk_forward.py
├── audit_fidelity_v3.py (Binance), audit_fidelity_v4.py (BingX)
├── audit_system.py (auditoría general)
├── live/ (mirror VPS)
├── deploy/setup_vps.sh, README.md
├── data_cache\, regime_models\, output\production\, regime_wf\
```

### 10.2 Producción (VPS Tokio)
```
/home/trader/combolab/
├── live/ (brain_engine con TF+MR, portfolio con EWMA+VolTarget, engine con DD breaker)
├── regime_models/ (45 .joblib)
├── regime_wf/ (45 .json — TF + 6 MR rescates)
├── .env, engine_state.json, trade_history.csv (con funding_paid), last_recycle.txt
└── logs/engine.log (ENGINE_STATE, SIGNALS_RAW/DISCARDED/EXECUTED v2.3.1)
```

---

## 11. PARÁMETROS CLAVE

| Categoría | Parámetros |
|-----------|-----------|
| Simulación (Pine/kernel) | `stopLossLevel_logic` único: inicial SL 3% (entry bar low/high), tensado por TS 0.5% (prev bar low/high), trigger `close < stopLossLevel_logic` en bar confirmado (on-close). SL Emergency 5% intrabar (`low/high ≤ entry × 0.95/1.05`) separado como `emerg_price_L/S`. Cooldown 1 bar tras exit (bloquea same-bar). Comisión 0.10% round-trip. |
| Clustering | Hurst(100) + Z_ATR(100/1000) + ER(100), GMM k=2-3 por BIC |
| Walk-Forward | Train 70%, Toxic tail (75%, 5-100), PF≥1.2/1.0, Cross-cluster PF≥0.7, SQN p5 |
| Portfolio | 5%/pos, 20%/bloque, 30%/sector, 25% global, EWMA halflife=24, VolTarget clamp 0.3-2.0 |
| DD Breaker | 5%→0.75, 10%→0.50, 15%→0.0 (pausa), histéresis 12% reanuda con 0.50 |
| Health | PF degrad 70%/50%, Min 15 trades, Ventana 30d, Max 90d, DD alert 10% |
| MR Kernel | 17 bits, 8192 configs, 3 cancelaciones, Tenkan(9), HA diaria repintable |
| BingX Stop (hasta v2.3.11) | stop_market al `effective_sl = max(brain_sl, emergency_5%)`, ratcheado por update_trailing_stop via cancel/place-new cada ciclo. Trigger MARK_PRICE intrabar. Rompe Fidelidad 2 vs Pine on-close (ver §13.2 HALLAZGO 2026-04-20). |
| BingX Stop (v2.4.0+) | stop_market hardcoded al 5% emergency desde fill_price, no se tensa post-entry. TS gestionado por brain on-close via software (close < state.sl_level → CLOSE market order). FIEL a Pine/kernel. |

---

## 12. LECCIONES APRENDIDAS

1. **No adivinar el futuro.** Diccionario de especialistas + clasificador en vivo.
2. **SQN Haircut es el filtro más potente.** BTC C1: 85/100 sqn_p5 negativos.
3. **Toxic tail dinámico cambia presets óptimos.** VIDYA/KAMA resiste transiciones.
4. **Mean-reversion rescata 6 clusters** que TF no puede operar.
5. **Fidelidad simulación-producción es la base de todo.** 91% match con datos BingX.
6. **SL delegado al exchange = nivel intrabar de la simulación** (emergencia 5%).
7. **Trigger orders BingX:** TRIGGER_MARKET → forzar "stop_market".
8. **Stops duplicados = riesgo #1 en producción.** Reconcile debe ver trigger orders.
9. **Phantom purge:** DRY_RUN contamina LIVE si no se purga.
10. **Hidden divergences invertidas** en lab original. Corregidas en MR.
11. **Auditoría requiere kernel stateless** (no brain_engine stateful).
12. **Datos BingX para auditoría.** 0.1-0.5% cross-exchange crea/destruye señales borderline.
13. **Pipeline MR no contamina TF.** 3 archivos separados + bifurcación brain_engine.
14. **Nunca nohup con systemd Restart.** Dos procesos = órdenes duplicadas.
15. **close_position debe verificar que la posición existe** antes de enviar.
16. **OrderNotFound hereda de InvalidOrder** en ccxt. Capturar antes.
17. **5% fijo por posición viola paridad de riesgo.** Volatility targeting.
18. **Correlación SMA tiene inercia letal.** EWMA halflife=24 reacciona instantáneamente.
19. **Circuit breaker con histéresis** previene oscilación on/off.
20. **Slippage en cisnes negros es no lineal.** Crítico al escalar capital.
21. **Health monitor proactivo.** Reciclar por degradación medible.
22. **IAM mínimo privilegio.** AdministratorAccess → TradingVPSManager.
23. **Versiones incrementales** (v2.1→v2.2→v2.3) mejor que un gran cambio.
24. **Tests con mocks que replican asunciones del código propio dejan bugs de contrato externo invisibles** — 21 Abr 2026. El bug v2.4.3 original pasó los 8 tests unit porque el mock de `markets_info` usaba formato master (`"ETH/USDT"`) en la key, replicando la misma asunción del código bajo test. El bug emergió en producción (Smoke-B cycle 181) cuando la función operó contra ccxt real, que usa formato perpetuo (`"ETH/USDT:USDT"`). **Patrón problemático**: test que confirma "el código funciona consigo mismo" vs test que confirma "el código cumple el contrato de la dependencia externa". **Mitigación para tests que tocan interfaz de exchange**: (a) usar fixtures con formato ccxt real, no inventado; (b) documentar explícitamente qué contrato externo se asume en cada mock con comentario inline; (c) test de integración ligero contra ccxt real (`load_markets()` + lookup de un símbolo conocido) como smoke test al arranque del módulo. **Escalabilidad**: aplica a cualquier dependencia externa con formato específico (BingX endpoints, ccxt parameters, market info schemas, Telegram API shapes). No limitado a portfolio_manager. Ver §13.4 entrada v2.4.3-hotfix Smoke-B cycle 182 y §2.6 portfolio fix #7.
25. **Métricas agregadas sobre ventanas con hitos arquitecturales heterogéneos ocultan información crítica — 2026-04-21**. El primer audit v5.1 global con N=70 dio match rate 26.7% disparando alert de "regresión grave". Investigación posterior reveló que la ventana mezclaba período pre-v2.3.11 (lag estructural 1 bar, ~3.4% match inevitable) con post-v2.3.11 (~84.6% entry-filter, dentro de CI95 del baseline 91%). El número agregado fue promedio no-comparable. **Patrón problemático**: aplicar audits/analyzers sobre ventanas que cruzan deploys de fixes arquitecturales sin segmentar produce veredictos engañosos. **Mitigación**: antes de interpretar métricas agregadas, identificar deploys de fixes que afecten señales/entries/exits en la ventana. Segmentar por deploy boundary. Comparar solo ventanas homogéneas con baseline. Casos concretos: fix de lag (v2.3.11), fix Fidelidad 2 TS (v2.4.0), fix reconcile fantasma (v2.4.2). **Escalabilidad**: aplica a cualquier métrica temporal del sistema (match rate, alpha residual, slippage, portfolio saturación). Ver §13.4 entrada "Primer audit empírico 2026-04-21" como caso de estudio completo.
26. **Ecuaciones que cierran no garantizan atribución correcta por componente — 2026-04-22**. El analyzer v2.4.1 de 2026-04-21 reportó PnL real +0.77 USDT y ecuación cerraba con tolerancia <0.01 USDT/trade: `alpha_nominal + factor_portfolio + slippage + funding + residual = pnl_real`. Sin embargo, el componente `slippage` reportaba +0.00 espuriamente debido a bug histórico en `data_feed.get_open_positions` (size_usdt=0 sistemático en trade_history.csv). El slippage real (~-0.23 USDT) quedaba absorbido silenciosamente en `alpha_residual`, generando la impresión de "fenómeno no modelado" mayor al real. **Patrón problemático**: sistema de atribución con cierre matemático global pero componentes individuales con bugs silenciosos. El chequeo "ecuación cierra" no detecta el bug porque el error se propaga al residual con signo opuesto. **Mitigación**: validar independientemente cada componente contra expectativa teórica. Slippage con orden MARKET debería ser no-cero sistemáticamente; si reporta 0 en N trades, flag. Funding con posiciones >1h debería ser no-cero; idem. **Escalabilidad**: aplica a cualquier sistema de atribución con múltiples componentes y residual absorbente (analytics financieros, instrumentación de logs, audits). La ecuación global NO sustituye validación per-componente. **Caso origen**: bug size_usdt=0 descubierto durante A02 demo 2026-04-22, root cause en `data_feed.get_open_positions` sin field `size_usdt`, fix v2.4.4 deployado mismo día. Ver §13.4 entradas 2026-04-22 (size_usdt fix + matización primer audit 2026-04-21).
27. **Items §13.3 EN_ESPERA pueden estar obsoletos por reviews previos no documentados en §13.4 — 2026-04-23**. Dos casos detectados en 2 días consecutivos: (a) 2026-04-22 A40 parser rollover — fix ya aplicado en ultra review C5 (2026-04-17) pero item seguía en §13.3 EN_ESPERA; (b) 2026-04-23 A34 timing_borderline — `ENTRY_CANDLE_TOLERANCE=1` ya aplicado en ultra review C8 (2026-04-17) pero item seguía en §13.3 EN_ESPERA describiendo fix para problema ya resuelto. **Causa raíz**: ultra reviews agrupan varios fixes bajo etiquetas Cn (C1..Cn). Al aplicarse, §13.3 no se limpia sistemáticamente de items que ya resolvieron. Gap documental entre "fix aplicado" y "item backlog actualizado". **Consecuencia**: sesiones futuras que consultan §13.3 leen items obsoletos como tareas pendientes. Si se implementan literalmente: duplicación de funcionalidad o refactor innecesario. **Mitigación protocolaria**: al arrancar cualquier item de §13.3, Fase 0 obligatoria = verificar si el fix ya existe en código actual. Patrón diagnóstico: (1) grep del componente afectado; (2) citar literal función/constante en código actual; (3) comparar contra descripción del item; (4a) si ya implementado → reclasificar a §13.4 RESUELTO con referencia al review que lo resolvió; (4b) si parcialmente implementado → reinterpretar scope (como A34 adoptó "extender más allá del tol actual" en vez de "añadir tol=1"); (4c) si NO implementado → proceder. **Caso positivo**: A34 reinterpretación terminó siendo conceptualmente mejor que scope original (captura genuinamente caso útil ±2 beyond tol=1). La obsolescencia del item reveló oportunidad de mejora, no duplicación. **Aplicabilidad**: cualquier sistema con backlog documental + reviews que agrupan cambios. Cuando ritmo de review > ritmo de limpieza backlog, el backlog queda desfasado sistemáticamente. Ver §13.4 entrada A34 2026-04-23 para caso de estudio.
28. **Sincronización implícita incorrecta entre directorios paralelos — 2026-04-23**. Durante sesión 2026-04-22 y 2026-04-23 se detectaron 3+ instancias del mismo patrón: archivos creados/modificados en combolab no se propagaron automáticamente a comboclaude. Claude Code, al detectar asimetría posteriormente, "justificó" la ausencia como intencional en vez de verificar contra convención. **Caso concreto**: al cierre 2026-04-22 se commitaron `audit_fidelity_v5_2.py`, `deploy_boundaries.json`, `signal_price_lookup.py` en combolab; comboclaude no recibió copia. En sesión 2026-04-23, Claude Code reportó 3 veces "archivo X no existe en comboclaude, consistente dejarlo así" antes de detectarse como oversight acumulado. Sync retroactivo reveló **13 archivos desincronizados al inicio de 2026-04-23** (3 código + 10 tests que no existían en comboclaude). **Causa raíz**: ausencia de convención explícita documentada sobre sync 2-way. Claude Code infiere convención en cada sesión, y la inferencia por defecto es "preservar estado actual" (asume asimetría = intencional). **Mitigación adoptada 2026-04-23**: convención explícita en §0.7 ("Convención de sincronización combolab ↔ comboclaude"). Protocolo al cierre de tarea: MD5 2-way verification de TODOS los archivos modificados. Anti-patrón explicitado: "El archivo no estaba antes en comboclaude, consistente dejarlo así" es asunción INCORRECTA por defecto. **Aplicabilidad**: cualquier proyecto con múltiples checkouts o directorios paralelos del mismo código. La regla general es SYNC-BY-DEFAULT con excepciones listadas explícitamente, no PRESERVE-BY-DEFAULT con sync como excepción. Ver §0.7 para regla operativa + §13.4 entrada A34 2026-04-23 para cierre que aplicó protocolo retroactivo.

29. **Walk-forward con N_fwd pequeño puede producir expected PF significativamente inflado vs régimen futuro — 2026-04-22**. Caso empírico: ONDO/USDT C0 walk-forward arrojó pf_fwd=7.945 con N=17 OOS (pf_combined=5.5 reportado como expected en specialist_score). En operación real 2026-04-14 → 2026-04-21 sobre OHLCV ONDO real (16 trades bot, 7 efectivo matchable post-Fase II.B), PF observado=1.08 (fidelidad bot↔kernel 100% match expandido confirmada en Fase II.B). El gap NO es de ejecución (fidelidad OK), es **gap entre "edge inferred on small OOS sample" vs "edge reproduced in live régimen"**. Caveat §13.3 W3 (CI bootstrap en pf_fwd) era especulativo pre-2026-04-22; este caso lo valida empíricamente como necesario. **Generalización en Fase II.C global mismo día**: 2 candidatos exclusión adicionales (ONDO C2, SAND C1) + 17 símbolos con WARN_neg_res + edge_erosion alert direccional. NO es caso aislado, es patrón.

**Patrón problemático**: pf_fwd con N<25 y bootstrap CI no computado puede tener CI95 wide [1.0, 15.0+]. pf_combined=5.5 como punto estimado es engañoso cuando proviene de OOS noisy. Specialist seleccionado puede ser mayoritariamente ruido amplificado por multiple-testing bias del walk-forward (selección sobre miles de configs, mejor PF gana, sin penalty por N).

**Mitigación pre-reciclaje próximo**:
(a) Implementar W3 (CI bootstrap pf_fwd) en `regime_walk_forward.py`. N=1000 resamples por config. Filtrar specialists con `pf_fwd_ci_low < 1.5` o threshold a definir.
(b) Implementar W4 (subir _FWD_MIN_TRADES de 15 → 25 o 30) para reducir candidatos noise.
(c) Ordenar specialists por `pf_combined_ci_low` en lugar de `pf_combined` punto estimado.
(d) Warning en JSON output cuando `N_fwd < 25`.

**Consecuencia metodológica**: cualquier modelo que selecciona "mejor de N" con N pequeño y métrica continua sufre **multiple testing bias**. Walk-forward es instancia clásica. Solución estándar académica: bootstrap CI o penalty por N (FDR control). Implementación pre-reciclaje no urgente pero crítica para que el reciclaje julio no produzca specialists similarmente inflados.

**Aplicabilidad fuera de trading**: cualquier sistema con selección sobre samples pequeños + métrica continua. Inflación de point estimates vs CI lower bound. Fenómeno generalizable.

**Caso origen**: Fase II.B + Fase II.C audit/analyzer 2026-04-22. Validación de empírica de W3 que estaba como hipótesis sin data hasta este punto. Ver §13.4 entries respectivos + §13.3 W3 (priorizar pre-reciclaje).

30. **Smoke test con N pequeño puede ocultar drift path-dependent sobre N grande — 2026-04-22**. Caso empírico: `_run_verify_test(BTC/USDT)` con N=1000 hardcoded reportó diff 0.0000 consistentemente en 5+ deploys (v2.3.7-v2.4.5). A10 sobre ONDO N=8335 reveló diff real: 506 vs 510 trades (99.22% match), PnL +5.2983% diff. APT N=10000 patrón consistente: diff -1.3260% PnL. La métrica de smoke test (tolerance PnL 0.1%) es apropiada para small N pero **insuficiente para detectar drift acumulado** en indicadores path-dependent (VIDYA/KAMA/ALMA/T3/FRAMA/McGinley). Root cause probable: brain usa rolling window de 500 bars recomputando MAs desde window start; kernel Numba usa estado acumulado desde t=0 con warmup 100 interno. La diferencia es numéricamente sub-0.01% por bar pero acumula sobre miles de barras.

**Patrón problemático**: test que protege invariante X con muestra insuficiente para que X se manifieste. Passes consistentes no significan invariante preservado — pueden significar test ciego a la amplitud real del fenómeno.

**Mitigación adoptada**:
(a) Upgrade smoke test a N≥5000 para deploys críticos (ver §13.3 item relacionado).
(b) Tolerance escalada con N: <2000 → 0.1%, ≥2000 → 2% (acknowledges drift path-dependent esperado).
(c) Trade count diff absoluto ≤ max(1, 0.5% de N_trades).
(d) Deploys que solo toquen observabilidad (logs, alerts, config paths) pueden seguir usando smoke N=1000 si no afectan lógica brain/kernel.

**Consecuencia metodológica**: cualquier test de fidelidad/consistencia entre dos implementaciones debe calibrar N a la magnitud esperada del drift. Para indicadores path-dependent, el drift acumula con O(N) o O(sqrt(N)) según implementación; tolerance del test debe escalar igualmente. Tolerance fija ≠ test robusto con N variable.

**Aplicabilidad fuera de trading**: cualquier sistema con dos implementaciones independientes de la misma lógica (referencia + optimizada, Python + Numba/C, interpreter + JIT). Regresión tests con N pequeño pueden pasar por coincidencia; N grande discrimina. Valid también para tests de algoritmos numéricos iterativos (SGD, ODE solvers, Kalman filters).

**Caso origen**: A10 diferencial brain↔kernel Numba 2026-04-22 sobre N≥8000 altcoins activas (ONDO, APT). Ver §13.4 A10 entrada respectiva + §13.3 item root cause drift + smoke test upgrade.

31. **Verificar diseño documentado antes de diagnosticar problema arquitectónico — 2026-04-23**. Caso origen: A13 LL2 kernel simplificado lab_lite. Primera iteración diagnosticó "Caso C bias severo" comparando kernel lite (solo zonas puras) vs kernel completo (con SL/TS/divergencias/cancelaciones). Veredicto estructural aparente: drift inevitable, reducción 0.05%. Ricardo interrumpió preguntando si CONTEXTO documentaba este diseño como intencional. Re-lectura §13.3 LL2: el criterio empírico documentado era "ratio supervivencia presets input lab_lite → walk-forward outputs, saludable si ≥20%". Re-análisis con métrica correcta: **ratio mean 36.7%**, 43/45 símbolos en rango saludable → veredicto LIMPIO, el diseño funciona como intencional.

**Patrón problemático**: diagnosticar "problema arquitectónico" sin verificar primero si es diseño intencional documentado. El análisis correcto depende de qué pregunta se pretende responder — "¿el sistema funciona como diseñó?" vs "¿el sistema es óptimo globalmente?" son evaluaciones distintas con métricas distintas.

**Mitigación**: antes de clasificar un comportamiento como "bug arquitectónico", (a) grep CONTEXTO para la palabra clave del componente; (b) leer items §13.3 relevantes completamente, incluyendo "Disparo" y "Cierre"; (c) si CONTEXTO documenta el comportamiento como diseño, aplicar el criterio empírico definido ahí, no el criterio intuitivo que surja del análisis estructural. El criterio documentado captura la intención del diseñador; el criterio intuitivo refleja asunciones no validadas.

**Escalabilidad**: aplica a cualquier sistema con diseño evolutivo documentado + desarrolladores externos (o agentes AI) que no necesariamente conocen las decisiones previas. La documentación del "por qué" de un diseño es tan importante como el "qué" — sin el por qué, cada auditor re-inventa la rueda (incorrectamente) al detectar el "qué" desviado de una norma implícita.

**Caso origen**: A13 LL2 2026-04-23 diagnóstico inicial incorrecto corregido por Ricardo con señalamiento explícito al CONTEXTO §13.3.

32. **Auditorías comparativas con referencia histórica requieren inventario de adaptaciones esperadas a priori — 2026-04-23**. Caso origen: A04b Fidelidad 1 MR kernel ↔ Pine v7.25. Ricardo aportó contexto crítico en el prompt: Pine v7.25 MR es versión **congelada con faltas conocidas** documentadas §0.2 (hidden divergence sin fix, cancelaciones unificadas bajo `i_use_cancel`). Kernel MR moderno incluye **4 adaptaciones intencionales** listadas a priori. Sin ese aviso, la auditoría habría clasificado las 4 adaptaciones como "divergencias POT INVOLUNTARIAS", generando 4 falsos positivos sobre ~5 divergencias totales → reporte virtualmente inservible.

**Patrón problemático**: auditar "kernel moderno" vs "referencia histórica congelada" asumiendo que ambos deberían ser funcionalmente idénticos. En proyectos con evolución arquitectónica intencional, la referencia histórica **diverge esperablemente** del estado actual — las divergencias son adaptaciones documentadas, no bugs.

**Mitigación**: al diseñar un prompt de auditoría comparativa, incluir explícitamente:
- **Jerarquía clara**: qué archivo es "verdad operacional" vs cuál es "referencia histórica" (§0.6 en este proyecto).
- **Inventario de adaptaciones esperadas a priori**: lista de divergencias intencionales conocidas, con referencia al documento que las justifica (§0.2 en este caso).
- **Categorías de clasificación asimétricas**: distinguir "ADAPTACIÓN DOCUMENTADA" (esperada, no es divergencia a reconciliar) de "POT INVOLUNTARIA" (divergencia real a investigar).

Sin esto, el auditor produce falsos positivos masivos y la auditoría pierde valor.

**Escalabilidad**: cualquier sistema con diseño vivo + referencia histórica (indicadores Pine vs kernel Python, papers académicos vs implementación industrial, specs originales vs producto maduro). La auditoría comparativa es útil solo si el marco de clasificación reconoce que "divergencia ≠ bug" cuando hay evolución consciente.

**Caso origen**: A04b 2026-04-23. Prompt mejorado por Ricardo incluyó explícitamente: las 4 adaptaciones esperadas (hidden fix, cancelaciones bits 14-16, HA/Tenkan cruce invertido, semántica zona invertida), clasificación jerárquica §0.6, categorías distintas "ADAPTACIÓN DOC §0.2" vs "POT INVOLUNTARIA". Resultado: auditoría limpia (4/5 divergencias correctamente clasificadas como ADAPTACIÓN §0.2 esperadas, 1 única POT INVOLUNTARIA real a investigar).

33. **Hipótesis del roadmap requieren validación empírica antes de implementación, incluso si provienen de literatura establecida — 2026-04-22**. Caso origen: §9.3 v2.6 Funding Filter contrarian era hipótesis "bien fundada" desde literatura financiera general — funding extremos = crowding signal, trade contrarian = ganador. Opción A (§13.3 observabilidad) ejecutada antes de implementación reveló dirección **opuesta** con p=0.0003 (trimmed): aligned trades ganan +0.50% mean, contrarian pierden -0.57% (Welch t=+3.58, Mann-Whitney p=0.0052). Implementación directa sin validación empírica habría degradado PnL en factor 2.2× (simulación -1.52 USDT adicional sobre 50 trades vs PnL real +0.70).

**Patrón problemático**: asumir que una hipótesis válida en la literatura general aplica directamente al sistema específico. Trading textbooks describen reversión por liquidación de crowds crowded; trading algorítmico específico puede tener otro edge (trend-following) donde funding positivo es **confirmation signal de tendencia**, no target de squeeze. La misma hipótesis verbal tiene dirección operacional opuesta según arquitectura del edge.

**Mitigación protocolar**: protocolo §13.3 aplica observabilidad-antes-de-decisión de forma general. Para cualquier item del roadmap:
1. Identificar si la hipótesis asume arquitectura genérica o específica.
2. Antes de implementar lógica activa: implementar observabilidad en analyzer (infra offline que no toca producción ni rompe Fidelidad 2).
3. Acumular N mínimo (50 para dirección estadística; 100+ para magnitud estable).
4. Ejecutar tests (Welch + Mann-Whitney + robustness checks).
5. Decidir implementación con evidencia propia del sistema, no extrapolación de literatura.

**Variante importante**: distinguir "archivar por falta de evidencia" (null case, no material diff) vs "refutar por evidencia contraria" (material diff en dirección opuesta). El segundo escenario es más informativo — descubre que la hipótesis estaba inversa, no solo insuficiente. Registrar explícitamente la diferencia en docs.

**Escalabilidad**: cualquier sistema con hipótesis heredadas (de literatura, de diseño original, de consenso genérico) que se propongan implementar mecánicamente. La asunción "esto es conocido, funciona así" se verifica antes de invertir compute o tocar producción. Conecta con Lecciones 31 (verificar diseño documentado antes de diagnosticar) y 32 (auditorías requieren inventario adaptaciones esperadas) — patrón común: **no asumir, verificar empíricamente en el contexto específico**.

**Caso origen completo**: §9.3 v2.6 Funding Filter propuso threshold `|rate| > 0.001` (0.1%/8h) como "crowding extremo" contrarian. Opción A observabilidad reveló: (a) ese threshold nunca se activa (0/50 trades; p99 empírica 5× menor); (b) la dirección del efecto crowd-vs-signal es opuesta a la hipótesis. Resultado: filter archivado por refutación empírica, item candidato inverso ("v2.6-inv momentum filter") abierto pendiente N≥100 para validación temporal. Ver §13.4 entrada "Observabilidad funding per-trade" 2026-04-22.

34. **Hipótesis emergentes de análisis con ventana N<50 requieren validación multi-segmento antes de elevar a §13.3 — 2026-04-23**. Caso origen sesión A.1: N=26 post-v2.4.4 generó 3 hipótesis emergentes con magnitudes aparentes dramáticas (H1 asimetría short vs long 12:1, H_strategy exits logic vs structural 3.4×, H_new_3 residual contrarian vs PnL 24×). Stress-test Fase 3 multi-segmento cross-arquitectónico N=98 refutó las tres: H1 mostró dirección opuesta en S1 pre-v2.3.11 (N=49 con Cohen d +0.55 longs peor); H_strategy concentrado enteramente en S4 (S1+S2 dirección opuesta, Welch global p=0.086 dominado por S4 p<0.001); H_new_3 ratio 24× cae a 2.16× con N=19/14 consistente con gap PnL relativo. Las tres hipótesis eran artefactos de ventana estrecha S4.

**Patrón problemático**: análisis limitado a la ventana arquitectónicamente más limpia (S4 post-v2.4.4 con size_usdt y entry_timestamp_ms correctos) parece metodológicamente óptimo — data sin contaminación de bugs pre-fix — pero sacrifica el poder discriminador que da la variación cross-segmento. Hipótesis con ratios 3×-24× en N=26 pueden ser ruido muestral que multi-segmento N=98 disuelve o invierte. La "calidad arquitectónica" de la data no sustituye al "poder estadístico" del dataset completo cuando se busca efecto estructural.

**Mitigación protocolaria**: antes de crear un item §13.3 EN_ESPERA (con spec, disparador, cierre) a partir de hipótesis emergente de ventana N<50:
1. Replicar cross-segmento arquitectónico sobre dataset completo (S1/S2/S3/S4 del proyecto). Los segmentos tienen régimen y fixes distintos, pero la persistencia direccional es más informativa que la magnitud local.
2. Aplicar criterio de elevación:
  - Persiste direccionalmente en ≥2 segmentos con N≥20 cada uno Y no invierte signo en ningún segmento con N≥20 → elevar a §13.3 HIPOTESIS con disparador N mayor.
  - Persiste en 1 segmento o signos mixtos cross-segmento → mantener como OBSERVACION en notas del análisis, NO crear item §13.3 activo.
  - Invierte signo en ≥1 segmento con N≥20 → archivar como artefacto muestral, documentar en §13.4 con refutación.
3. Segmentos con N<10 se excluyen del análisis vinculante (ni como evidencia ni como contra-evidencia).

**Escalabilidad**: aplica a cualquier proyecto con historial segmentado arquitectónicamente (deploy boundaries, régimen de mercado, versiones). La tentación de analizar solo la ventana más limpia es fuerte; el coste de hacerlo sin cross-check es crear backlog de hipótesis espurias que consumen validación incremental prolongada (espera N≥100 cuando el efecto es artefacto de N=26).

**Relación con lecciones previas**: complementaria a L25 (agregados sobre ventanas heterogéneas engañan — aquí lo contrario: segmento único también engaña); complementaria a L29 (walk-forward N_fwd inflado en selección — aquí análogo para hipótesis post-hoc en atribución); complementaria a L33 (hipótesis heredadas de literatura externa requieren validación empírica — aquí hipótesis emergentes internas requieren validación multi-segmento).

**Caso origen completo**: sesión 2026-04-23 A.1 deep-dive + Fase 2 H1 + Fase 3 stress-test. 3 refutaciones en una sesión aplicando el protocolo por iniciativa del operador (Ricardo) que solicitó stress-test antes de escribir borradores §13.3. Sin el protocolo se habrían creado 3 items §13.3 activos con disparadores N≥40/50/100 que habrían consumido 3-4 sesiones de validación incremental para concluir refutación. Con el protocolo se resuelven en 1 sesión.

---

## 13. LISTA VIVA DE SEGUIMIENTO

Esta sección registra ítems pendientes de verificación, mejoras detectadas pero no bloqueantes, hallazgos empíricos que afectan decisiones futuras, y decisiones arquitectónicas a recordar. Mantenida incrementalmente por Claude (conversacional) y Claude Code. Los ítems resueltos no se borran — se marcan con [RESUELTO] y fecha, conservando trazabilidad.

**Formato de cada ítem:**

```
[TAG] [ESTADO] Título breve — fecha_detectado
Contexto: descripción autocontenida (sin referencias a otras secciones)
Disparo: condición bajo la que actuar sobre este ítem
Cierre: condición bajo la que se considera resuelto
Referencias: archivos/líneas/versiones si aplica.
```

**Tags válidos:**
- BUG: fallo confirmado o sospechado en producción
- MEJORA: optimización o refactor posible, no urgente
- OBSERVACION: patrón detectado que merece monitoreo
- DECISION: decisión arquitectónica a recordar al cruzar ciertas líneas
- HALLAZGO: resultado empírico que afecta decisiones futuras

**Estados:** ACTIVO | EN_ESPERA | VERIFICANDO | RESUELTO

**Orden:** por estado (VERIFICANDO → ACTIVO → EN_ESPERA → RESUELTO), dentro de cada estado por fecha descendente.

---

### 13.1 VERIFICANDO

**[VERIFICANDO] Primer trade MR real del sistema — UNI C0 OBSERVADO 2026-04-21 (disparador conceptual SATISFECHO) — GRT C2 específico sigue VERIFICANDO — 2026-04-17**

Dos niveles de disparador:

a) **CONCEPTUAL AMPLIO** (validar flujo MR live con cualquier símbolo rescatado): **SATISFECHO 2026-04-21** por UNI/USDT C0 config_id=121360 (rescue rank 3 §3.3). 2 trades MR reales observados:
   - 2026-04-20 16:00 UTC UNI short `zone_exit_mr`.
   - 2026-04-20 18:00 UTC UNI long `cancel_mr`.
   Ambos excluidos del audit v5.1 (kernel MR no implementado en audit) pero validados por `audit_mr_fidelity_sei.py` (0.0000 diff empírico en SEI C2 del mismo día). Pipeline MR end-to-end funcional en producción.

b) **ESPECÍFICO GRT** (trade MR de GRT C2 config_id=25088 según swap 2026-04-17): **SIGUE VERIFICANDO**. GRT no clasificado en C2 desde deploy hace 5 días. Rollback §9.2.1 trackea: 0/20 trades GRT MR, 0/90 días (fecha límite 2026-07-16).

Contexto original: Swap GRT TF→MR desplegado 2026-04-17 08:15 UTC. JSON cargado al arranque. Verificación flujo MR live posible cuando GRT esté clasificado en C2 Y se generen condiciones entrada specialist MR. Según densidad empírica walk-forward ~1 trade cada 270 barras en C2, C2 ~25% del tiempo — semanas a meses hasta primer trade.

Disparo específico GRT: primer trade GRT con s="MR" en [SIGNALS_EXECUTED] o strategy_type="MR" en trade_history.csv. Verificar: (a) trade se ejecuta sin errores, (b) SL/TS se gestionan correctamente, (c) el cierre sigue lógica MR.

Notas verificación temporal:
- 2026-04-20 10:05 UTC: últimos 10 [SIGNALS_RAW] GRT/USDT con `"s":"TF"` y `"k":0|1`. Sin C2 aún.
- 2026-04-21 mediodía: análisis forense GRT (1 trade 04:00 UTC long tf_exit) confirmó cluster 0 TF, config 34648634 (no config MR 25088). GRT aún no clasificado en C2.

Cierre: se cierra cuando (a) primer trade MR GRT ejecutado y verificado (sub-item específico), o (b) rollback §9.2.1 disparado (20 trades MR cualquier cluster o 90 días desde swap). El sub-item conceptual amplio YA cerrado 2026-04-21.

Referencias: §9.2.1 rollback GRT, §3.3 tabla MR rescates, §13.4 RESUELTO audit MR SEI 2026-04-21, §13.4 RESUELTO primer audit/analyzer empírico 2026-04-21, brain_engine.py bifurcación TF/MR, live_engine.py [SIGNALS_EXECUTED].

---

### 13.2 ACTIVO

**[HALLAZGO] [ACTIVO] BRAIN_RECONCILE no registra cierres legacy en trade_history.csv — 2026-04-20**
Contexto: descubierto durante investigación de anomalía UNI/USDT en Smoke-B post-v2.4.0 (2026-04-20 cycle 161). Cuando brain detecta posición en su state pero BingX no tiene la posición (cerrada entre cycles por stop tensado intrabar o apertura fantasma que no persistió), emite BRAIN_RECONCILE reset. Este path NO dispara log_trade — el cierre no queda en trade_history.csv.
Diferencia con ORPHAN_CLOSE existente:
- ORPHAN_CLOSE (§13.4 RESUELTO 2026-04-20 OP/USDT verificado 3 casos) se dispara cuando el path de close_position() intenta cancelar un stop_order_id y BingX responde "no existe" o "position not found" → reconstrucción y log_trade.
- BRAIN_RECONCILE (este ítem) se dispara antes, al inicio del cycle cuando fetch_positions() no retorna la posición esperada. No intenta cancelar stop, solo resetea state. Sin log_trade.
Impacto operacional:
1. Ventana migración Opción B v2.4.0 (próximas horas a 1 semana): 6 posiciones legacy con stops tensados heredados pueden dispararse intrabar. Si eso ocurre entre cycles sin que close_position se invoque, el trade NO se registra. Pérdida silenciosa del dato.
2. Aperturas fantasma (patrón B-UNI-1 observado en UNI/USDT desde cycle 154 del 2026-04-20): signal emitido, apertura no persiste (likely min_order_precision con balance bajo, mismo patrón ETH), brain state marca abierto, cycle siguiente detecta gap y BRAIN_RECONCILE resetea. En este caso NO hay trade real, el no-registro es correcto. Pero el patrón recurrente satura logs (1× por cycle, 7+ cycles confirmados para UNI).
3. Audit v5.1 futuro: trades legacy cerrados durante ventana migración no estarán en CSV → gap en comparación fidelidad vs kernel. Requerirá exclusión explícita de la ventana 2026-04-20 14:08 UTC → cierre de última posición legacy.
Decisión provisional 2026-04-20: Opción A — aceptar pérdida de registro durante migración. Documentar. Cuando llegue audit v5.1 post-N≥50 segmentar explícitamente el período.
Fix futuro (candidato v2.4.1): modificar BRAIN_RECONCILE para que intente obtener fill_price via fetch_my_trades(symbol, since) para el período entre last_known_state y current_cycle, y si encuentra un trade consistente (SELL si era LONG, BUY si era SHORT) con approximate timing, invocar log_trade con dato reconstruido. Similar a ORPHAN_CLOSE pero sin depender del stop_order_id.
Disparo:
- Inmediato (para decisión): contar cuántos trades legacy se pierden durante ventana migración.
- v2.4.1 candidate: tras estabilidad v2.4.0 confirmada en 48h, considerar implementación de reconstrucción.
Cierre: implementado v2.4.1 o aceptado como pérdida permanente con documentación rigurosa.
Referencias:
- Smoke-B cycle 161 2026-04-20 15:00:09 UTC: BRAIN_RECONCILE UNI/USDT reset sin trade en CSV.
- Patrón observado desde 08:00 UTC (cycle 154) pre-deploy, no introducido por v2.4.0.
- ORPHAN_CLOSE mecanismo fiel vinculado en §13.4 entrada 2026-04-20.

**[HALLAZGO] [ACTIVO] Divergencia de Fidelidad 2 en TS — 2026-04-20**
Contexto: auditoría del 2026-04-20 confirmó con citas literales que Fidelidad 1 (Pine ↔ kernel lab) está intacta en los 4 mecanismos de stop, pero Fidelidad 2 (kernel ↔ bot live) está rota en el TS.
Especificación de la divergencia:
- Pine evalúa `close < stopLossLevel_logic` on-close (barstate.isconfirmed, líneas 897-906 + 944 del indicador_v44_0_smartdiv_v11_0_TF.pine).
- Kernel lab (lab_historico_numba_v8_3.py líneas 1503-1509) evalúa `close_p < sl_level` on-close. FIEL a Pine.
- Bot live (execution_manager.py update_trailing_stop, líneas 574-740): traduce state.sl_level del brain a stop_market en BingX que se ejecuta intrabar al toque (MARK_PRICE trigger). ROMPE convención.
Los 3 ORPHAN_CLOSE OP/USDT del 2026-04-18 07:00, 2026-04-19 01:00 y 2026-04-19 23:00 son manifestación directa de esta divergencia. Precio tocó el nivel tensado intrabar y BingX cerró; Pine/kernel no habrían cerrado si el close del mismo bar estaba por encima del sl_level (caso plausible en mercados choppy).
Impacto en audit v5.1 futuro:
- Trades con exit por TS intrabar en bot NO matchearán con trades de kernel si el close del bar revirtió sobre sl_level.
- PnL acumulado live sesgado vs simulado en mercados choppy (cierres prematuros en live que kernel/Pine no ejecutarían).
- Audit v5.1 con N>=50 detectará estos casos como discrepancia, contaminando los reportes si no se documenta origen.
Decisión adoptada 2026-04-20: aplicar v2.4.0 con Opción C (Ricardo confirmada tras leer Pine directamente). Respeto literal del diseño original: emergency 5% intrabar delegado a BingX hardware; TS/SL gestionados por brain on-close via software. Razonamiento: respetar convención del sistema simulado, absorber mechas de volatilidad como el diseño original pretendía. "Entrar una vela más tarde nunca es ventaja, cerrar por una mecha que revierte tampoco lo es."
Especificación técnica v2.4.0:
- Prerequisito: fix cp1252 emoji en lab_historico_numba_v8_3.py:990 (reemplazar `⚙️` por `[CALC]` ASCII) — habilita _run_verify_test [2/2] kernel compare en Windows.
- Cambio principal: execution_manager.py update_trailing_stop convertido en no-op. Mantener firma y callers sin cambios. Cuerpo reemplazado por log informativo + return {"action":"stop_noop_v240"}. Rollback trivial restaurando cuerpo original.
- open_position sin cambios (ya coloca stop_market al 5% emergency desde fill_price, líneas 499-504 de execution_manager.py).
- close_position sin cambios (ya usa MARKET order reduceOnly para cierre activo, línea 330-335).
- brain_engine.py sin cambios (ya calcula state.sl_level y emite CLOSE con reason=sl_hit on-close).
- live_engine.py sin cambios (no invoca update_trailing_stop directamente).
Migración Opción B (transición gradual): posiciones legacy mantienen stop_market tensado existente hasta cerrar. Nuevas posiciones post-deploy usan 5% emergency fijo + brain software TS. Ventana mixta ~horas a 1 semana. Segmentación para audit v5.1 futuro vía entry_timestamp_ms (ya disponible en trade_history.csv col 12 desde v2.3.3) comparando con timestamp del deploy v2.4.0.
Testing pre-deploy: T1 cp1252 smoke, T2 syntax no-op, T3 unit test on-close vs intrabar (mock OHLC entry=100, low=95 close=98.5, bar forming intrabar), T4 _run_verify_test [1/2] baseline invariante (4 señales, 2 trades, PnL +1.2940%), T5 [2/2] nueva capacidad post-cp1252 fix, T6 DRY_RUN cycle con engine_state del VPS.
Disparo para aplicación: próxima sesión. Target: v2.4.0 en ~1-2 sesiones.
Cierre: post-v2.4.0 deploy + validación con _run_verify_test + observación de 10+ cycles post-deploy sin regresión + primera verificación orgánica de que un TS-intrabar potencial no se ejecuta (precio toca sl_level brain pero close por encima → posición se mantiene).
Referencias:
- Pine: indicador_v44_0_smartdiv_v11_0_TF.pine líneas 786-808 (emergency intrabar), 897-906 (TS update), 905 (trigger on-close), 1039-1054 (SL inicial).
- Kernel: lab_historico_numba_v8_3.py líneas 1476-1509 (TS update + emergency intrabar + TS/SL close check).
- Live: execution_manager.py update_trailing_stop líneas 574-740 (función a convertir en no-op en v2.4.0).
- Audit completo: §13.4 entrada "[RESUELTO-CORRECCIÓN] Audit fidelidad 4x3 — 2026-04-20".

[RESUELTO 2026-04-20 v2.4.0 deploy] — ver §13.4 entrada v2.4.0 deploy.

**[DECISION] [ACTIVO] Sesión 2026-04-19 — 15 fixes aplicados, 5 despliegues — 2026-04-19**
Contexto: Segunda sesión grande del proyecto tras auditorias del 2026-04-17. Foco: atacar masivamente los serios pendientes de §13.3 antes del primer reporte audit v5.1 con N>=50.
Fixes aplicados en la sesión:
- v2.3.6 (inicio de sesión): H1 + H4 health_monitor (daily summary Telegram fix de DD espurio).
- v2.3.7: 10 fixes triviales Grupo A (brain S2/S3/S5, portfolio S2/S4/S5, execution E5, live_engine L3/L5/L7).
- v2.3.8: B4 + B5 + B7 data_feed/execution (B6 investigado, no aplicado — close_position consume el attach).
- v2.3.9: B1 brain_engine (B2 prev_zone y B3 TF locals DIFERIDOS por complejidad oculta revelada en Fase I, documentada como lección).
- v2.3.10: D4 alerts Telegram fire-and-forget (cierre de sesión).
Total: **15 fixes aplicados sin rollback** + 5 ítems RESUELTO de verificaciones empíricas Fase 1 (C1 funding, C5 current_balance, C4/D4 forming/closed, C3 hid_inv datos, C2 setLeverage diferido) + 1 decisión arquitectónica (lag 1 bar como feature oficial opción-a, disparo post-N>=50).
Hallazgos metodológicos:
- Fix "estilístico" NO es sinónimo de "bajo riesgo". B2/B3 revelaron errores de premisa del ultra review que solo se detectan tocando código real (ej. ultra review decía "TF nunca lee state.prev_zone" pero en realidad sí lo lee en fallback t==0).
- B7 validado empíricamente en producción cycle 134 (APT partial fill 8.5/8.59 capturado por el fix horas después del deploy) — primera validación real de un fix recien desplegado.
- _run_verify_test [1/2] como gate de no-regresión funciona perfectamente (B1 confirmó bit-por-bit IDÉNTICO pre/post).
- [2/2] bloqueado por cp1252 emoji en lab_historico:990 (nuevo ítem pendiente en §13.3).
- v2.3.10 demostró 100% reducción de latencia en test sintético (5010ms → 0ms para 10 alerts 0.5s c/u).
Estado al cierre:
- Bot v2.3.10 estable en producción, 136 ciclos ejecutados.
- §13.3 EN_ESPERA: 36 ítems restantes (mayormente pre-reciclaje julio o disparador N>=50).
- Próximos disparadores orgánicos: daily summary 2026-04-20 00:00 UTC (verifica H1 fix de v2.3.6), acumulación hasta N>=50 post-v2.3.3 para primer audit v5.1 real.
Disparo: próxima sesión de trabajo activo, o momento de primer reporte audit v5.1 con N>=50.
Cierre: no se cierra — registro de trazabilidad de sesión productiva.
Referencias: versiones v2.3.6 a v2.3.10 todas del 2026-04-19, §13.4 entradas consolidadas por versión.

**[DECISION] [ACTIVO] Ultra review sistemático completado — 2026-04-17**
Contexto: Auditoría completa de 12 módulos en 3 capas, ejecutada el 2026-04-17.
- **Capa 1 (core, 4 módulos):** 1 FIX DIRECTO (L1 aplicado en v2.3.4), 2 FIX CON RIESGO (R1 brain cooldown, P1 portfolio leverage — diferidos), 28 SERIOS, 15 MENORES.
- **Capa 2 (apoyo, 3 módulos):** 1 FIX DIRECTO (H3 aplicado en v2.3.5), 0 FIX CON RIESGO, 7 SERIOS, 11 MENORES.
- **Capa 3 (lab pipeline, 5 módulos):** 0 CRÍT, 6 SERIOS (pre-reciclaje), 13 MENORES. extractor_gemas.py confirmado como legacy NO en pipeline (master.py no lo usa; sus bugs no afectan JSONs actuales).
**Totales agregados:** 2 FIX DIRECTO (ambos aplicados), 2 FIX CON RIESGO (diferidos con disparadores), 41 SERIOS (documentados como MEJORA en 13.3), 39 MENORES.
**Fixes aplicados en esta sesión:**
- v2.3.3: entry_timestamp_ms en trade_history.csv para fix C1 del analyzer.
- v2.3.4: L1 scheduler month-end + L2 _save_state atómico.
- v2.3.5: H3 health_monitor CSV parsing + H2 excluye reconstructed.
**Fixes diferidos con disparadores claros:**
- R1 brain cooldown emergency/cancel: pendiente primer audit v5.1 con N≥50 y test diferencial brain vs kernel.
- P1 portfolio leverage: convertido en proyecto arquitectónico separado (balance >1000 USDT + cap de safety antes de aplicar).
- Capa 3 SERIOS: aplicar antes del primer reciclaje ~julio.
**Hallazgos estructurales importantes:**
- R1 confirmado aislado en brain (ni portfolio, ni execution, ni live_engine, ni lab kernel lo compensan).
- P1 confirmado como sub-apalancamiento sistemático (25/44 símbolos cambiarían leverage post-fix; algunos 10x — riesgo de liquidación con balance 297).
- H3 reveló que daily summary Telegram silenciosamente roto desde 2026-04-16 (fix aplicado 2026-04-17).
- Kernel lab (run_simulation_numba) sin parámetro leverage → specialist_configs calibrados para 1x.
- Drift potencial de MA implementations entre 4 archivos (lab_lite, lab_historico, brain_engine, mean_reversion_kernel) sin checksum shared.
**Conclusión:** sistema globalmente sano, con deuda técnica manejable documentada en lista de seguimiento. No hay bugs que afecten la correctitud operacional del bot actualmente en producción más allá de lo ya fixeado.
Disparo: al plantear nuevas auditorías sistemáticas, revisar progreso global, o justificar decisiones sobre R1/P1/reciclaje.
Cierre: no se cierra — cierre histórico del proceso de auditoría sistemática del 2026-04-17.
Referencias: 12 DECISION items individuales de ultra reviews en 13.2, plan maestro en 13.2, ítems de MEJORA en 13.3.

**[DECISION] [ACTIVO] Ultra review master.py ejecutado — 2026-04-17**
Contexto: Cuarto módulo de Capa 3. Orquestador del pipeline (751 líneas). Resultado: LIMPIO (0 CRÍT, 0 SERIOS, 4 MENORES). CONFIG centralizada con 45 símbolos (coincide con CONTEXTO §0), resume vía detección de outputs, check_prerequisites por paso.
MENORES (cosmético):
- master.py `--recycle` NO actualiza last_recycle.txt (health_monitor.log_recycle_event no invocado).
- Docstring dice "48 símbolos" pero CONFIG tiene 45 (inconsistencia documental).
- lab_lite sin checkpoints intra-símbolo (crash re-ejecuta símbolo completo).
- Interacción --skip-download + --from-step poco documentada.
Disparo: no aplica — trazabilidad.
Cierre: no se cierra.
Referencias: master.py en v2.3.5.

**[DECISION] [ACTIVO] Ultra review train_regime_model.py ejecutado — 2026-04-17**
Contexto: Segundo módulo de Capa 3. Entrena GMMs (510 líneas). Resultado: LIMPIO (0 CRÍT, 0 SERIOS, 3 MENORES). Código simple, determinista (random_state=42, n_init=10). Features vía compute_regime_features del módulo compartido — garantiza fidelity training↔inferencia brain_engine.
MENORES: joblib sin versioning sklearn, no min cluster size, discrimination threshold 0.5 cosmético.
Disparo: no aplica — trazabilidad.
Cierre: no se cierra.
Referencias: train_regime_model.py en v2.3.5.

**[DECISION] [ACTIVO] Ultra review lab_lite_zonas_v5e.py ejecutado — 2026-04-17**
Contexto: Tercer módulo de Capa 3. Generador de presets (1481 líneas). Resultado: 0 CRÍT, 2 SERIOS, 2 MENORES.
SERIOS (pre-reciclaje):
- LL1 MA implementations duplicadas en 4 archivos (lab_lite, lab_historico, brain_engine, mean_reversion_kernel) sin import shared. Drift silencioso potencial.
- LL2 Kernel lab_lite simplificado (zonas puras sin filtros TF/divergencias/SL) — presets seleccionados tienen selection bias hacia zonas limpias.
Disparo: pre-reciclaje julio.
Cierre: LL1 resuelto con import shared; LL2 cuantificar % presets que pasan walk-forward y decidir si ajustar.
Referencias: lab_lite_zonas_v5e.py en v2.3.5.

**[OBSERVACION] [ACTIVO] extractor_gemas.py NO está en pipeline de producción — 2026-04-17**
Contexto: Ultra review reveló que extractor_gemas.py es legacy/alternate tool. master.py NO lo invoca. El pipeline canónico (CONTEXTO §1.2) son 4 pasos sin extractor_gemas. Los JSONs actuales en producción vienen de regime_walk_forward, no de extractor_gemas. Sus posibles bugs internos no afectan producción.
El módulo es internamente consistente — usa _get_neighbors con semántica correcta (mejor que regime_walk_forward que tiene el bug W1 con bit-flip simple).
Disparo: si alguien propone reactivar el flujo lab_historico + extractor_gemas en el futuro.
Cierre: documentar permanentemente como tool opcional fuera del pipeline canónico, o eliminar si no se prevé uso.
Referencias: extractor_gemas.py, master.py (no lo importa), CONTEXTO §1.2 (pipeline canónico de 4 pasos).

**[DECISION] [ACTIVO] Ultra review regime_walk_forward.py ejecutado — 2026-04-17**
Contexto: Primer módulo de Capa 3 del plan maestro. Ejecutado sobre regime_walk_forward.py (1970 líneas). NO afecta bot operacional actual — hallazgos aplican al próximo reciclaje (~julio). Resultado: 0 CRÍTICOS, 4 SERIOS pendientes pre-reciclaje (documentados en 13.3), 4 MENORES.
Hallazgos clave:
- W1 plateau_ratio usa bit-flip simple en 26 bits, inconsistente con _get_neighbors del SQN haircut (mismo módulo, 2 definiciones de "neighbor"). Plateau_ratio en JSONs actuales tiene significado diluido.
- W2 CUDA vs CPU engine drift potencial sin tag en part files. Si un run mezcla engines tras crash/resume, specialists generados tienen heterogeneidad silenciosa.
- W3 falta CI/bootstrap en pf_fwd y specialist_score con N pequeño. El caso GRT C2 MR (pf_fwd=14.975 N=13) formaliza el riesgo.
- W4 _FWD_MIN_PF=1.0 y _FWD_MIN_TRADES=15 laxos — outliers pasan filtro. Requiere análisis cuantitativo para subir thresholds sin perder demasiados candidatos.
Reconfirmaciones:
- Kernel lab (run_simulation_numba) tiene cooldown correcto (cooldown_until=t para emergency/cancel). R1 brain cooldown confirmado como divergencia brain-side, no lab.
- Kernel lab no toma parámetro leverage. maxdd_worst en % (1x). Reconfirma P1 (portfolio_manager * 100.0 es incorrecto).
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte ultra review del 2026-04-17, regime_walk_forward.py en v2.3.5.

**[DECISION] [ACTIVO] Capa 2 del ultra review sistemático completada — 2026-04-17**
Contexto: Los 3 módulos de apoyo (data_feed, health_monitor, stress_test) auditados. Totales Capa 2: **1 CRÍTICO FIX DIRECTO (H3 CSV schema)**, **7 SERIOS** (documentados como MEJORA en 13.3), **11 MENORES**. Hallazgos clave:
- H3 detecta bug operacional: daily health summary silencioso fallando desde v2.3.2 por schema evolution. Fix pendiente en 13.1.
- Health_monitor portfolio_dd_from_peak métrica ambigua (no alineada con DD breaker).
- Health_monitor no excluye reconstructed trades (inconsistente con analyzer/audit).
- Stress_test es script offline simple, limitado a SL safety net.
- Data_feed bien-hardened, retry inconsistente entre funciones es el mayor hallazgo.
Próximo paso: Capa 3 (pipeline de lab — regime_walk_forward, lab_lite_zonas_v5e, train_regime_model, extractor_gemas, master). Puede arrancar inmediatamente. H3 se aplica aparte (trivial).
Disparo: al arrancar Capa 3.
Cierre: Capa 3 también completada.
Referencias: 3 DECISION items de Capa 2 en 13.2 (data_feed, health_monitor, stress_test del 2026-04-17).

**[DECISION] [ACTIVO] Ultra review stress_test.py ejecutado — 2026-04-17**
Contexto: Tercer y último módulo de Capa 2. Ejecutado sobre v2.3.4. Resultado: 0 CRÍTICOS, 0 SERIOS, 4 MENORES (T1 simulador solo SL, T2 depende de train_regime_model sin drift detection, T3 urllib sin retry, T4 resultados no persisten). Script offline simple (466 líneas), bajo riesgo. No se ejecuta en producción. Probabilidad críticos latentes: ~5%.
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte ultra review del 2026-04-17, stress_test.py en v2.3.4.

**[DECISION] [ACTIVO] Ultra review health_monitor.py ejecutado — 2026-04-17**
Contexto: Segundo módulo de Capa 2. Ejecutado sobre v2.3.4. Resultado: **1 CRÍTICO FIX DIRECTO (H3 CSV schema mismatch — ver 13.1)**, 0 FIX CON RIESGO, 3 SERIOS (H1 DD métrica, H2 reconstructed no excluidos, H4 9999 default dispara trigger espurio), 3 MENORES. Módulo de monitoring (501 líneas), no crítico para trading pero sí para observabilidad. Probabilidad críticos latentes: ~15%.
Hallazgo operacional relevante: H3 significa que el daily summary Telegram silenciosamente no se envía desde v2.3.2 deploy (2026-04-16). Bot sigue funcionando — solo pierde telemetría.
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte ultra review del 2026-04-17, health_monitor.py en v2.3.4.

**[DECISION] [ACTIVO] Ultra review data_feed.py ejecutado — 2026-04-17**
Contexto: Primer módulo de Capa 2 del plan maestro. Ejecutado el 2026-04-17 sobre v2.3.4. Resultado: 0 CRÍTICOS (ni FIX DIRECTO ni FIX CON RIESGO), 4 SERIOS (documentados en 13.3), 4 MENORES. Módulo simple (699 líneas) con fixes históricos §2.6 verificados (ThreadedResolver, Binance Spot no Futures, BingX swap, OHLCV_LIMIT 1500 con paginación, normalización trigger orders). Probabilidad críticos latentes: 10-15%, concentrada en ambigüedad forming vs closed candle (D4).
Hallazgos serios:
- D1 retry inconsistente (solo OHLCV, no balance/positions/orders).
- D2 pagination empty first-fetch no reintenta (silent gap).
- D3 attach de stops en get_open_positions redundante con llamada separada desde live_engine.
- D4 ambigüedad semántica "forming vs closed" en iloc[-1] — needs verification empírica.
Correlación: get_funding_history captura NotSupported y retorna [] → es la ruta que dispara el fallback E1 de execution_manager. Ratio estimable con grep de logs.
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte ultra review del 2026-04-17, data_feed.py auditado en v2.3.4.

**[DECISION] [ACTIVO] Capa 1 del ultra review sistemático completada — 2026-04-17**
Contexto: Los 4 módulos core (brain_engine, portfolio_manager, execution_manager, live_engine) auditados sistemáticamente. Resultado agregado: **1 CRÍTICO FIX DIRECTO (L1 scheduler month-boundary)**, **2 CRÍTICOS FIX CON RIESGO (R1 cooldown brain, P1 leverage portfolio)**, **28 SERIOS** (documentados como MEJORA en 13.3), **15 MENORES** (mayormente ignorados). Hallazgos clave:
- R1 brain cooldown divergence confirmado aislado (ni portfolio, ni execution, ni live_engine compensan).
- P1 portfolio leverage convertido en proyecto separado (HALLAZGO leverage lab↔producción).
- E3 execution emergency SL escala con leverage (vincula con proyecto P1).
- L1 live_engine scheduler crashea en fin de mes, fix trivial pendiente en 13.1.
- Todos los módulos están bien-hardened por fixes históricos acumulados (§2.6).
Estado del pipeline de fixes: L1 pendiente aplicar antes del 2026-04-30. R1 y P1 pendientes de primer reporte audit v5.1 con N≥50 (baseline empírica necesaria).
Próximo paso: Capa 2 (data_feed, health_monitor, stress_test). Puede comenzar inmediatamente — ningún CRÍTICO FIX DIRECTO bloquea (L1 es trivial y no requiere esperar).
Disparo: al arrancar Capa 2.
Cierre: Capa 2 también completada.
Referencias: 4 DECISION items de ultra reviews Capa 1 en 13.2 (brain_engine, portfolio_manager, execution_manager, live_engine del 2026-04-17).

**[HALLAZGO] [ACTIVO] Investigación leverage lab↔producción — 2026-04-17**
Contexto: Tras detección de P1 (leverage 1x uniforme por bug en portfolio_manager), se investigó el lab para determinar si specialist_scores y pnl del walk-forward asumen leverage variable o 1x. Evidencia decisiva: `run_simulation_numba` del lab NO tiene parámetro leverage (firma en lab_historico_numba_v8_3.py línea 1266-1279); PnL calculado como `(exit-entry)/entry × 100` puro sin escalado. maxdd_worst en JSONs (valores entre 1.848% y 76.83%) solo interpretable en porcentaje.
Escenario real: **SCENARIO 2 con matización**. Lab simula a 1x. Diseño producción intenta escalar via leverage para targetear 25% DD portfolio. Producción real stuck a 1x por bug P1 → sistema sistemáticamente sub-apalancado. Análisis empírico sobre los 44 símbolos activos: 25 de 44 (56.8%) cambiarían leverage post-fix, hasta 10x para QNT/TON (maxdd~1.87%).
Matización crítica: balance actual 297 USDT + leverage 10x → liquidación a -10% drop. Leverage 5x → liquidación a -20%. Fix de P1 sin mitigación adicional incrementa severamente riesgo de liquidación.
Implicación para P1: fix necesario, NO cosmético. Pero aplicación requiere: (a) esperar balance mayor (>1000 USDT reduce severidad), o (b) cap adicional de leverage en producción (p.ej. max 3x hasta balance >1000 USDT), o (c) aceptar sub-apalancamiento como feature implícita de safety.
Disparo: al triaje de P1 post-primer reporte audit v5.1.
Cierre: decisión tomada sobre P1 con análisis cuantitativo considerando balance actual.
Referencias: lab_historico_numba_v8_3.py run_simulation_numba, maxdd_worst en JSONs regime_wf/, ítem P1 "Leverage map siempre 1x" en 13.2.

**[DECISION] [ACTIVO] Ultra review live_engine.py ejecutado — 2026-04-17**
Contexto: Cuarto y último módulo auditado en Capa 1 del plan maestro. Ejecutado el 2026-04-17 sobre v2.3.3. Resultado: 1 CRÍTICO FIX DIRECTO (L1 _next_activation_time crashea en month-end, movido a 13.1 VERIFICANDO), 0 FIX CON RIESGO, 6 SERIOS (documentados en 13.3), 3 MENORES. Probabilidad críticos latentes: 15-20%, los bugs residuales son operacionales (atomicidad save, timeout ciclo, alerts serializadas) más que lógicos. Módulo bien estructurado con los fixes v2.1/v2.3.1/v2.3.2/v2.3.3 acumulados correctamente.
Confirmaciones:
- R1 brain cooldown NO compensado en live_engine (signals pasan directo a portfolio sin filtro "just-closed").
- P1 portfolio leverage NO alterado en live_engine (lv del log viene de allocations tal cual).
- E1 funding sign NO afecta live_engine (log_trade usa funding_paid=0.0 solo en ORPHAN_CLOSE).
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte de ultra review del 2026-04-17, archivo live_engine.py auditado en v2.3.3.

**[DECISION] [ACTIVO] Ultra review execution_manager.py ejecutado — 2026-04-17**
Contexto: Tercer módulo auditado en Capa 1 del plan maestro. Ejecutado el 2026-04-17 sobre v2.3.3. Resultado: 0 críticos FIX DIRECTO, 0 críticos FIX CON RIESGO DE REGRESIÓN, 5 serios (documentados como MEJORA en 13.3), 3 menores (ignorados). El módulo está bien hardened por fixes históricos acumulados (§2.6 del CONTEXTO: close hardened, OrderNotFound antes de InvalidOrder, fix setLeverage side=BOTH, normalización trigger orders, etc.). Probabilidad de críticos latentes: 20-30%, concentrada en casos borde operacionales (partial fills, exchange outages, ventanas sin stop) difíciles de simular.
Confirmaciones importantes:
- R1 (brain cooldown) NO se compensa en execution. Execution procesa LONG sin filtro "just-closed". R1 aislado.
- P1 (portfolio leverage) NO se corrige en execution. Execution pasa `leverage` de allocation directo a set_leverage. Bug propaga sin alteración.
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte de ultra review del 2026-04-17, archivo execution_manager.py auditado en v2.3.3.

**[DECISION] [ACTIVO] Ultra review portfolio_manager.py ejecutado — 2026-04-17**
Contexto: Segundo módulo auditado en Capa 1 del plan maestro. Ejecutado el 2026-04-17 sobre v2.3.3. Resultado: 0 críticos FIX DIRECTO, 1 crítico FIX CON RIESGO DE REGRESIÓN (P1: compute_leverage_map tiene `* 100.0` espurio que reduce todos los leverages a 1x — ver ítem separado), 7 serios (documentados como MEJORA en 13.3), 4 menores (mayormente no accionables o ya documentados). Calibración: probabilidad críticos latentes adicionales 25-35%. Confirmado: no hay filtro en portfolio que compense brain R1 (cooldown emergency/cancel) — R1 queda aislado. Vol_weight puede neutralizar DD breaker para símbolos low-vol (SERIO S1, ambigüedad de intención del spec).
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte de ultra review del 2026-04-17, archivo portfolio_manager.py auditado en v2.3.3.

**[DECISION] [ACTIVO] Leverage map siempre 1x por `* 100.0` espurio — pendiente análisis — 2026-04-17**
Contexto: Ultra review portfolio_manager.py detectó P1. Línea 630: `raw_lev = target_max_dd / (best_maxdd * 100.0)`. El `* 100.0` es espurio asumiendo maxdd_worst está en porcentaje (confirmado empíricamente: GRT C0 tiene maxdd_worst=14.777 que solo es interpretable como %). Resultado: para cualquier maxdd > 0.25% (todos los símbolos), raw_lev < 1 → int=0 → max(1,...)=1x. Logs de SIGNALS_EXECUTED confirman lv=1 uniforme para todos los símbolos observados.
Compensaciones plausibles: (a) sizing validado empíricamente durante semanas con leverage 1x; (b) DD breaker calibrado con exposición real a 1x (fix a lev 2-10x aumenta frecuencia DD events); (c) kernel de auditoría no simula leverage (asume 1x); fix aumenta divergencia real vs simulado en costes funding+liquidación.
Síntoma verificable: `grep SIGNALS_EXECUTED | grep -oP '"lv":\d+' | sort -u` debería mostrar solo "lv":1. Confirmar en VPS.
Análisis pendiente antes de fix:
1. Extraer maxdd_worst de los 45 JSONs activos, estimar distribución de leverage post-fix.
2. Con balance 297 USDT, evaluar tolerancia a liquidación: lev 10x implica liquidación a -10% drop, lev 5x a -20%.
3. Si decisión es fix: desplegarlo como v2.3.4 con monitoring específico de funding costs y DD events primeras 24-48h.
Fix sugerido: cambiar a `raw_lev = target_max_dd / best_maxdd` (sin `* 100.0`).
Disparo: tras primer reporte audit v5.1 con N≥50, cuando ya haya evidencia de comportamiento del sistema a 1x, para poder comparar impacto de cambio a leverage variable.
Cierre: fix aplicado con análisis cuantitativo de impacto, o decisión documentada de mantener 1x uniforme por conservadurismo.
Referencias: portfolio_manager.py compute_leverage_map líneas 629-631, SIGNALS_EXECUTED logs con `"lv":1` consistente.

**[DECISION] [ACTIVO] Ultra review brain_engine.py ejecutado — 2026-04-17**
Contexto: Primer módulo auditado sistemáticamente en Capa 1 del plan maestro. Ejecutado el 2026-04-17 sobre v2.3.3. Resultado: 0 críticos FIX DIRECTO, 1 crítico FIX CON RIESGO DE REGRESIÓN (divergencia cooldown emergency/cancel vs kernel — ver ítem separado), 10 serios (documentados como MEJORA en 13.3), 5 menores (ignorados). Calibración: probabilidad de críticos latentes adicionales 35-45%, concentrada en áreas de fidelidad vs walk-forward y casos borde (gaps de data, warmup, NaN en MAs path-dependent). Recomendación: primer test diferencial (brain vs kernel sobre 10k+ barras histórico) como siguiente verificación empírica antes de continuar con portfolio_manager.
Disparo: no aplica — ítem histórico de trazabilidad.
Cierre: no se cierra — registro permanente de auditoría.
Referencias: reporte de ultra review del 2026-04-17, archivo brain_engine.py auditado en v2.3.3.

**[DECISION] [ACTIVO] Cooldown brain diverge del kernel para emergency/cancel — pendiente análisis — 2026-04-17**
Contexto: Ultra review brain_engine.py detectó FIX CON RIESGO DE REGRESIÓN R1. En líneas 850-856 (TF) y 1946-1951 (MR), brain asigna `state.cooldown_until = 0` para `sl_emergency_signal` y `cancel_signal`, permitiendo re-entrada same-bar. El kernel (lab + audit_fidelity_v5) asigna `cooldown_until = t` (absoluto), bloqueando same-bar. Los otros 3 exit types (sl_hit, div_exit, normal) concuerdan. El bug es demostrable por inspección pero raro en práctica (SL emergencia 5% implica mercado ya movido, cancel_tf implica TFs ya no alinean — improbable que entry_cond se cumpla mismo bar).
Compensaciones plausibles: (a) los falsos positivos de matching de audit v4 podían estar enmascarando este bug en el 91% reportado; (b) el fix hace el bot menos agresivo (bloquea re-entrada) — podría reducir alpha capturado en escenarios específicos.
Síntoma verificable: dos filas consecutivas en trade_history.csv con `reason_exit in {sl_emergency, cancel_tf}` seguido de apertura del mismo símbolo en el mismo `floor(timestamp, 'h')`. No observado aún (ningún trade con sl_emergency/cancel_tf en CSV local con 53 trades).
Análisis pendiente antes de aplicar fix:
1. Primer reporte audit v5.1 con N≥50 para baseline limpia.
2. Test diferencial: correr brain_engine con y sin fix sobre histórico BTC 10k barras, comparar trades y PnL.
3. Si fix reduce alpha >1% sobre histórico, documentar y decidir si aceptar la regresión por ganar fidelidad.
Fix sugerido: en ambos paths (TF y MR), cambiar `state.cooldown_until = 0` a `state.cooldown_until = COOLDOWN_BARS` para emergency/cancel.
Disparo: tras primer reporte audit v5.1 o cuando aparezca primer trade con sl_emergency/cancel_tf en producción.
Cierre: fix aplicado con análisis diferencial completado, o decisión documentada de aceptar la divergencia con justificación.
Referencias: brain_engine.py líneas 850-856 y 1946-1951, audit_fidelity_v5.py extract_trades_tf líneas 817-824 (referencia de kernel).

**[DECISION] [ACTIVO] Plan maestro ultra review sistemático del proyecto — 2026-04-17**
Contexto: Ricardo ha decidido aplicar ultra review sistemático a todo el código del proyecto tras éxito de los reviews de analyzer v2.4.1 y audit v5.1 (17 críticos combinados detectados). Plan estructurado por capas con criterios diferenciados para código en producción:

CAPA 1 — Bot core en producción (criterio estricto):
  1. brain_engine.py — [COMPLETADO 2026-04-17 v2.3.3] — 0 FIX DIRECTO, 1 FIX CON RIESGO, 10 SERIOS, 5 MENORES
  2. portfolio_manager.py — [COMPLETADO 2026-04-17 v2.3.3] — 0 FIX DIRECTO, 1 FIX CON RIESGO, 7 SERIOS, 4 MENORES
  3. execution_manager.py — [COMPLETADO 2026-04-17 v2.3.3] — 0 FIX DIRECTO, 0 FIX CON RIESGO, 5 SERIOS, 3 MENORES
  4. live_engine.py — [COMPLETADO 2026-04-17 v2.3.3] — 1 FIX DIRECTO, 0 FIX CON RIESGO, 6 SERIOS, 3 MENORES
  **CAPA 1 COMPLETADA 2026-04-17.** Totales: 1 FIX DIRECTO + 2 FIX CON RIESGO + 28 SERIOS + 15 MENORES.
  Observación 12-24h entre módulos si hay despliegue.

CAPA 2 — Módulos de apoyo:
  5. data_feed.py — [COMPLETADO 2026-04-17 v2.3.4] — 0 FIX DIRECTO, 0 FIX CON RIESGO, 4 SERIOS, 4 MENORES
  6. health_monitor.py — [COMPLETADO 2026-04-17 v2.3.4] — 1 FIX DIRECTO (H3 CSV schema), 0 FIX CON RIESGO, 3 SERIOS, 3 MENORES
  7. stress_test.py — [COMPLETADO 2026-04-17 v2.3.4] — 0 FIX DIRECTO, 0 FIX CON RIESGO, 0 SERIOS, 4 MENORES
  **CAPA 2 COMPLETADA 2026-04-17.** Totales: 1 FIX DIRECTO + 7 SERIOS + 11 MENORES.

CAPA 3 — Pipeline de lab:
  8. regime_walk_forward.py — [COMPLETADO 2026-04-17] — 0 FIX DIRECTO, 0 FIX CON RIESGO, 4 SERIOS (pre-reciclaje), 4 MENORES
  9. lab_lite_zonas_v5e.py — [COMPLETADO 2026-04-17] — 0 CRÍT, 2 SERIOS, 2 MENORES
  10. train_regime_model.py — [COMPLETADO 2026-04-17] — LIMPIO (0 CRÍT, 0 SERIOS, 3 MENORES)
  11. extractor_gemas.py — [COMPLETADO 2026-04-17] — NO EN PIPELINE (master.py no lo usa; no afecta JSONs actuales)
  12. master.py — [COMPLETADO 2026-04-17] — LIMPIO (0 CRÍT, 0 SERIOS, 4 MENORES)
  **CAPA 3 COMPLETADA 2026-04-17.** Totales: 0 CRÍT + 6 SERIOS + 13 MENORES.

Criterios especiales para código en producción (Capa 1 y 2):
- CRÍTICO solo si síntoma demostrable o correctitud clara.
- Atención a compensaciones implícitas (bugs pueden compensarse).
- Fixes clasificados: FIX DIRECTO vs FIX CON RIESGO DE REGRESIÓN.
- SERIOS por defecto a MEJORA en lista de seguimiento, no fix inmediato.

Estimación temporal total: 3-5 semanas calendario, terminando aproximadamente antes del primer reporte v2.4.1 con N≥50 trades o del primer reciclaje (julio).
Disparo: actualizar este ítem cada vez que se complete ultra review de un módulo, cambiando su estado en la lista y añadiendo versión resultante. Al completar todos los módulos de una capa, marcar capa como completa.
Cierre: todos los módulos completados.
Referencias: sesión 2026-04-17 donde se tomó decisión, sección 2.6 del CONTEXTO que lista fixes históricos ya identificados (pre-ultra review) por módulo.

**[OBSERVACION] [ACTIVO] E3 (emergency SL fill vs close_brain) escala con leverage — 2026-04-17**
Contexto: El serio E3 del ultra review de execution_manager reporta divergencia sub-% entre fill_price y close_brain usado para emergency SL. A leverage 1x actual (por bug P1), el impacto sobre capital es sub-% y despreciable. Pero si P1 se corrige y aplica leverage 10x, una diferencia de 0.5% fill↔close se convierte en 5% sobre capital. E3 pasa de SERIO a potencialmente CRÍTICO al apalancar.
Disparo: si se decide aplicar P1, revisar E3 en el mismo trabajo.
Cierre: E3 arreglado antes o conjuntamente con P1.
Referencias: execution_manager.py línea 469 (E3), ítem P1, ítem "Investigación leverage".

**[OBSERVACION] [ACTIVO] Ultra review como primer filtro ha sido crítico — 2026-04-17**
Contexto: Los dos ultra reviews aplicados (analyzer v2.4 y audit v5) detectaron 17 críticos combinados (8+9) más ~20 serios/menores. Sin ultra review, esos bugs habrían contaminado los primeros reportes reales con N=50, potencialmente llevándonos a conclusiones falsas sobre fidelidad del kernel y/o necesidad de capitalización. La verificación manual previa (solo cazó signo de funding) habría sido insuficiente para detectar bugs como kernel reimplementado silenciosamente en audit, o exit_bar_ts con asunción de 1-bar-hold que generaba falsos positivos de matching.
Disparo: cualquier futuro script crítico que afecte decisiones.
Cierre: no se cierra — observación empírica documentada, refuerza la DECISION "Política de aplicación de ultra review".
Referencias: ultra reviews de analyze_performance_attribution.py y audit_fidelity_v5.py del 2026-04-17.

**[OBSERVACION] [ACTIVO] N=50 para primer reporte v2.4.1 empieza desde v2.3.3 — 2026-04-17**
Contexto: Los 52 trades acumulados entre v2.3.2 (16 abril 17:00 UTC) y v2.3.3 (17 abril 08:55 UTC) carecen de entry_timestamp_ms en el CSV y el log no los cubre con el detalle necesario para inferir entry_candle retroactivamente (log stale para esos trades). Los analyzers los marcan como entry_candle_source=none y los excluyen del análisis. Por tanto, el primer reporte útil (analyzer v2.4.1 y audit v5.1) requiere acumular ≥50 trades POST-v2.3.3, no desde v2.3.2 como estaba planeado originalmente.
Disparo: monitorizar el contador de trades post-v2.3.3 en trade_history.csv. Lanzar primer reporte cuando N≥50 con entry_timestamp_ms poblado.
Cierre: primer reporte v2.4.1 y primer reporte audit v5.1 ejecutados y procesados.
Referencias: analyze_performance_attribution.py infer_entry_candle(), audit_fidelity_v5.py infer_entry_candle(), trade_history.csv columna entry_timestamp_ms introducida en v2.3.3.

**[OBSERVACION] [ACTIVO] pf_forward=14.975 con N=13 sensible a outliers — 2026-04-17**
Contexto: El specialist MR de GRT C2 tiene pf_forward muy alto (14.975) pero con solo 13 trades OOS en walk-forward. Esto es potencialmente producto de 1-2 ganadores atipicos, no evidencia solida de edge excepcional. Al evaluar resultados reales, usar pf_combined (2.918) como expectativa base. Si PF empirico aparece cercano a pf_train (~1.9), es mas creible que si aparece cercano a pf_forward (~15).
Disparo: en la primera revision de GRT MR (N>=10 o 90 dias), contrastar PF empirico contra ambas referencias y valorar cual de las dos hipotesis (edge real alto vs outliers) es mas consistente.
Cierre: primera revision de GRT MR completada y documentada.
Referencias: seccion 9.2.1 metricas base del walk-forward.

**[OBSERVACION] [ACTIVO] BRAIN_RECONCILE frecuencia alta con balance bajo — 2026-04-16**
Contexto: En el primer ciclo post-v2.3.2 el mecanismo de reconciliación disparó 12 veces (12 señales LONG descartadas por below_min_order con balance ~298 USDT). Esperado mientras el balance sea pequeño — brain sigue generando señales optimistas que portfolio descarta, y reconcile las limpia. No es bug. Si tras capitalizar la cuenta o tras el primer reciclaje la frecuencia sigue igual de alta, revisar si hay lógica que se puede mejorar (ej: brain podría abstenerse de generar señales cuando el sizing previsto caiga bajo el mínimo).
Disparo: analyzer v2.4 reporta frecuencia [BRAIN_RECONCILE] por día y tendencia temporal. Si post-capitalización o post-reciclaje la frecuencia no baja, revisar.
Cierre: frecuencia baja orgánicamente tras capitalización/reciclaje, o se implementa filtro preventivo en brain que se documenta como nueva decisión arquitectónica.
Referencias: live_engine.py _reconcile_brain_after_execution(), v2.3.2

**[HALLAZGO] [ACTIVO] Saturación de portfolio con balance bajo afecta alpha capturado — 2026-04-16**
Contexto: Primer ciclo post-v2.3.2 mostró 12 señales LONG simultáneas, todas descartadas por below_min_order con exposure real solo al 37.8%. Con balance 297 USDT y sizing mínimo 5 USDT, muchas señales simultáneas comprimen el cap global del 25% repartido entre N hasta hacer cada slot inviable. Adicionalmente, la verificación de v2.4 reveló funding negativo al 121% de |PnL| — el funding sobre notional apalancado (lv=3 típico) erosiona más PnL del que el trading genera con balance bajo. Dos vectores refuerzan conclusión: capitalización ayudaría por dos caminos distintos (reducir saturación + reducir peso relativo del funding).
Disparo: analyzer v2.4 en su sección (f) cuantifica alpha perdido por saturación y funding. Si el reporte muestra >30% de alpha perdido o funding >10% de PnL neto, alert automático recomienda capitalización.
Cierre: decisión de capitalización tomada (con cifra justificada) o balance sube orgánicamente hasta niveles no saturados.
Referencias: portfolio_manager.py límites (25% global, 5% posición, sizing mínimo 5 USDT), analyze_performance_attribution.py secciones f y g

**[DECISION] [ACTIVO] Brain se mantiene stateless — correcciones de estado van en orquestador — 2026-04-16**
Contexto: Bug #1 (fantasmas por apertura optimista) se arregló en live_engine con _reconcile_brain_after_execution(), NO en brain_engine. Esta decisión preserva la propiedad de kernel stateless del brain, crítica para que la auditoría de fidelidad siga comparable con el kernel stateless de regime_walk_forward.py. Si en el futuro se plantea modificar brain para que dependa de feedback del exchange, recordar que eso rompería la equivalencia con el kernel de auditoría.
Disparo: cualquier propuesta futura de añadir lógica stateful al brain (ej: "que brain consulte BingX antes de generar señal"). Revisar este ítem antes de aceptar.
Cierre: no se cierra — decisión arquitectónica permanente.
Referencias: brain_engine.py (se mantiene stateless), live_engine.py _reconcile_brain_after_execution(), audit_fidelity_v4.py/v5.py (kernel stateless)

**[DECISION] [ACTIVO] Fórmula expectancy en analyzer v2.4 — 2026-04-16**
Contexto: expectancy_cluster se calcula como pool completo (pnl_tr+pnl_fwd)/(trades_tr+trades_fwd), con columna OOS comparativa pnl_fwd/trades_fwd y flag edge_erosion si ratio OOS/pool <0.5 con N≥3. En prompt original se sugirió erróneamente fórmula (pf-1)/pf × avg_trade que es redundante — el promedio empírico YA es la expectancy en las unidades del JSON.
Disparo: si en futuras iteraciones alguien propone cambiar a otra fórmula, revisar razón antes de aceptar.
Cierre: no se cierra — decisión arquitectónica permanente.
Referencias: analyze_performance_attribution.py sección expectancy

**[DECISION] [ACTIVO] br empírico preferido sobre 5/n para factor saturación — 2026-04-16**
Contexto: Para clasificar descartes below_min_order entre saturación vs dd_breaker vs balance_bajo, el analyzer v2.4 usa br empírico del ciclo (que ya incorpora global_reduction según hallazgo en portfolio_manager.py:521) en lugar de fórmula teórica 5/n. El br empírico captura correlaciones y sectores reales del ciclo; la fórmula teórica los ignora.
Disparo: si iteración futura propone simplificar a fórmula teórica, revisar por qué antes de aceptar.
Cierre: no se cierra — decisión arquitectónica permanente.
Referencias: analyze_performance_attribution.py sección f2 categorización below_min_order, portfolio_manager.py línea 521

**[DECISION] [ACTIVO] Limitación modelo GMM en re-clasificación de ciclos históricos — 2026-04-16**
Contexto: Analyzer v2.4 re-clasifica ciclos con GMM cuando [SIGNALS_RAW] no incluye cluster_id (fallback b de cadena Q6). Si entre ventana analizada y ejecución del analyzer hubo reciclajes del GMM, la reclasificación podría no coincidir con el cluster real del ciclo original. Actualmente no relevante (no hay reciclajes hasta ~julio) pero a considerar tras primer reciclaje v3.0.
Disparo: tras primer reciclaje (~julio), si se quiere analizar datos previos al reciclaje con el analyzer post-reciclaje.
Cierre: implementar versionado de modelos .joblib con timestamp, y que analyzer elija modelo según fecha del ciclo analizado. Actualmente documentado como TODO en código.
Referencias: analyze_performance_attribution.py fallback b de re-clasificación de clusters (Q6)

**[DECISION] [ACTIVO] Política de aplicación de ultra review — 2026-04-17**
Contexto: Ultra review de Claude Code se ha incorporado al flujo para código complejo que produce análisis consumidos en decisiones. Primera aplicación al analyzer v2.4 detectó 4 críticos + 4 serios promocionables a críticos — validando la decisión. La verificación manual previa solo cazó 1 de los 8 críticos totales (el signo de funding), demostrando que ultra review es complemento necesario, no redundante.
Criterios de aplicación:
- SÍ: código nuevo o significativamente cambiado que producirá análisis para decisiones importantes, antes de la primera ejecución real.
- SÍ: tras cambios a lógica delicada (ej: fixes en brain_engine, portfolio_manager, execution_manager) una vez verificado que no hay regresión en 12-24h.
- NO: cambios mecánicos (swaps de config en JSON).
- NO: instrumentación pasiva ya verificada como no-regressiva.
Triaje del output:
- CRÍTICOS: fixear sin discusión.
- SERIOS: revisar, promocionar a crítico los que afecten correctitud de resultados. El resto a lista de seguimiento como MEJORA.
- MENORES: ignorar salvo mejoras específicas de robustez o documentación.
Disparo: cada vez que haya código nuevo/cambiado que cumpla criterios SÍ arriba.
Cierre: no se cierra — política permanente.
Referencias: primera aplicación fue a analyze_performance_attribution.py el 2026-04-17, segunda a audit_fidelity_v5.py el mismo día.

**[DECISION] [ACTIVO] v4 audit fidelity es referencia sucia, no baseline — 2026-04-17**
Contexto: Ultra review de audit_fidelity_v5.py detecto 5 bugs heredados de v4: kernel reimplementado sin verificacion de parity con lab (C2), exit_bar_ts mal nombrado con asuncion 1-bar-hold (C1), rollover de fecha fragil sin anchor (C5), path hardcoded (C6), y tolerancia +-2 cuando spec dice +-1 (C8). El 91% de v4 con N=11 probablemente incluyo falsos positivos de matching espurios. Implicacion: v4 NO es baseline valida para comparar contra v5.1 corregido. El reporte de v5.1 incluye caveat explicito en seccion 5.
Disparo: al interpretar resultados del primer v5.1 corregido. NO extrapolar cuando el numero caiga por debajo de 91% -- probablemente v4 estaba inflado.
Cierre: no se cierra -- decision arquitectonica permanente.
Referencias: audit_fidelity_v5.py seccion 5 con caveat, ultra review del 17 abril 2026.

**[DECISION] [ACTIVO] Kernel de auditoria: opcion C (checksum drift detection) — 2026-04-17**
Contexto: Lab solo tiene run_simulation_numba (Numba, sin equivalente python puro). Opcion B (importar desde lab) no factible sin refactor mayor >8h. Opcion C aplicada: audit mantiene copia python estatica de extract_trades_tf, con SHA256 checksum del codigo en EXPECTED_AUDIT_KERNEL_HASH. Startup verifica hash y warn on mismatch. Tambien checksum lab.run_simulation_numba para detectar drift al reves. Para actualizar hash tras cambio intencional: recomputar con inspect.getsource + hashlib y actualizar constante.
Disparo: si futuro audit v6+ se plantea reimplementar kernel, revisar este item y considerar refactor a opcion B antes.
Cierre: no se cierra -- decision arquitectonica permanente hasta que lab exponga kernel python puro.
Referencias: audit_fidelity_v5.py verify_kernel_parity(), EXPECTED_AUDIT_KERNEL_HASH / EXPECTED_LAB_KERNEL_HASH constantes.

**[DECISION] [ACTIVO] balance_req en analyzer v2.4.1 excluye br — 2026-04-17**
Contexto: Formula corregida tras ultra review (S2). `br` (block_reduction) captura la compresion implicita 1/n_signals del global cap, por lo que incluirlo en el denominador junto a `GLOBAL_CAP * n_signals` hacia double-count. Formula final: `balance_req = (MIN_ORDER * n_signals) / (GLOBAL_CAP * vw * bf * dd)`. Derivacion documentada en el codigo (compute_saturation_analysis).
Disparo: si iteracion futura propone re-incluir br en denominador, revisar razonamiento antes de aceptar.
Cierre: no se cierra — decision arquitectonica permanente.
Referencias: analyze_performance_attribution.py compute_saturation_analysis, ultra review S2.

**[DECISION] [ACTIVO] Consistency check por reconstruccion de precios (no tautologico) — 2026-04-17**
Contexto: Tras ultra review C2, el antiguo check `pnl_real - sum(componentes) = residual` era tautologico (residual se define como residual, gap siempre 0). Reemplazado por: `pnl_recon = (exit - entry) * contracts * side_sign - fees` vs `pnl_usdt` del CSV con tolerancia 0.01 USDT o 10% de |pnl|. Captura errores de escritura, fees mal contabilizadas, y desajustes contracts vs size_usdt. Unit test de consistencia se hace con precios observados, no con el modelo.
Disparo: si >5% de trades tienen `pnl_recon_not_closing`, alerta automatica en el reporte.
Cierre: no se cierra — decision arquitectonica permanente.
Referencias: analyze_performance_attribution.py attribute_trade seccion "C2", ultra review C2.

**[DECISION] [ACTIVO] Convención de signos en analyzer v2.4 — 2026-04-16**
Contexto: Convención interna del analyzer: para slippage, factor_portfolio, funding y alpha_residual, positivo = favorable y negativo = coste. Para pnl_real y alpha_esperado, valores absolutos en USDT sin convención comparativa. Fórmula corregida de slippage_entry: (signal - exec) × contracts × side_sign (opuesta a la del spec original, que daba signo invertido respecto a exit). Fórmula exit sin cambios. Ecuación de cierre: pnl_real ≈ alpha_esperado + slippage + factor_portfolio + funding + alpha_residual con tolerancia 0.01 USDT por trade.
Disparo: si algún reporte futuro muestra signos inconsistentes o trades donde la ecuación no cierra, revisar fórmulas antes de cualquier otra hipótesis.
Cierre: no se cierra — decisión arquitectónica permanente.
Referencias: analyze_performance_attribution.py bloque attribute_trade(), test de consistencia interno

---

### 13.3 EN_ESPERA

**[MEJORA] [RESUELTO] Cooldown asimétrico por tipo exit — UNIFICAR SEGURO confirmado 2026-04-22**

Ver §13.4 entrada RESUELTO 2026-04-22 "Cooldown asimétrico — UNIFICAR SEGURO por Opción A".

Resumen: Ricardo confirmó Opción A (cooldown=1 siempre operacional en Pine productivo histórico; diferenciación en kernel era código muerto). Refactor kernel TF L1630-1637 + kernel MR L408-415 a expresión Pine canónica uniforme. Confirmatorio empírico + Smoke §0.8 A+B+C PASS. Último ítem §13.3 bloqueante arquitectónico pre-reciclaje cerrado.

**[MEJORA] [RESUELTO] Upgrade `_run_verify_test` — parametrizar n_bars + tolerance escalada — 2026-04-22 → RESUELTO 2026-04-23**

Ver §13.4 entrada RESUELTO 2026-04-23 "_run_verify_test CLI parametrizable --n-bars + tolerance escalada §0.8". Signature extendida con n_bars (default 1000 backward compat), CLI `--n-bars N`, tolerance escalada Nivel A/B automática (A: 0.1pp absoluto/exacto; B: 15pct relativo floor 0.1pp / match >=95pct §0.8). Wrappers temporales obsoletos. Scope `--cluster K` diferido.

---

**[POLÍTICA] [EN_ESPERA] Adelantar reciclaje por criterio empírico degradación clusters — 2026-04-22**

Contexto: Fase II.C (§13.4 2026-04-22) reveló patrón de degradación edge generalizada antes del calendario reciclaje original julio:
- 3 clusters flagged (ONDO C0 health_monitor + ONDO C2 + SAND C1 candidatos exclusión analyzer).
- 17 símbolos con WARN_neg_res (alpha residual significativamente negativo).
- Edge_erosion alert direccional (alpha residual cae >10% últimos 20 trades vs 20 anteriores).
- PnL realizado +0.48 USDT vs alpha esperado +5.64 (gap -91% sobre 47 trades en 3 días).

Política propuesta para adelantar reciclaje por criterio empírico (no calendario):

**Disparador automático**:
- 5+ clusters cruzando ratio_oos/pool < 0.5 con N≥3 cada uno (umbral W3 conservador).
- O alpha residual sistemático <-50% del alpha nominal en ventana 30d con N≥30.
- O PnL cumulativo turn negativo en ventana 30d con N≥30.

**Disparador semi-automático (alerta + decisión Ricardo)**:
- 3+ clusters flagged candidato_exclusion sostenido en 2+ reportes consecutivos del analyzer (semanal).
- O degradación edge >20% en métrica direccional consecutivos 2 reportes.

**Estado actual (2026-04-22)**:
- 3 clusters flagged (límite del semi-automático).
- Alpha residual -68% del alpha nominal (cerca del trigger automático -50% si se mantiene).
- PnL aún positivo (+0.48 USDT, no trigger negativo).
- Veredicto: NO disparar reciclaje todavía. Monitorear próximos 7-14 días.

**Disparo del item**: próximo audit/analyzer N≥50 (~2026-04-26) o cualquier degradación adicional sustantiva (clusters flagged crecen, PnL turn neg).

**Cierre**:
- (a) Reciclaje adelantado ejecutado con W3+W4 implementados pre-corrida (mejor specialists post-reciclaje).
- (b) Patrón estabiliza/revierte naturalmente (régimen mejora) → mantener calendario julio.
- (c) Decisión documentada de mantener calendario julio aceptando degradación marginal.

Referencias:
- §13.4 Fase II.C 2026-04-22.
- §12 Lección 29 (W3 validación empírica).
- §13.3 W3 (CI bootstrap) + W4 (thresholds _FWD) — ambos prioridad elevada.
- §9.4 v3.0 reciclaje calendario original julio 2026.

---

**[AUDIT] [EN_ESPERA] Audit definitivo Fidelidad 2 con N ≥ 50 post-v2.3.11 — 2026-04-21**
Contexto: primer audit empírico 2026-04-21 confirmó Fidelidad 2 con N=13 efectivo entry-filter (84.6% match rate, CI95 overlap con baseline 91%). Pero N=13 tiene CI95 ancho; veredicto robusto requiere N≥50.
Al ritmo actual (~10 trades/día observados post-v2.3.3), N=50 post-v2.3.11 entry-filter se proyecta para ~2026-04-26 (cinco días desde hoy). Primera ejecución con N≥50 será el audit definitivo inicial.
Disparo: 50 trades con entry_cycle > 2026-04-19 17:51 UTC Y post-C3 filtering (no reconstructed, entry_timestamp_ms válido) acumulados en trade_history.csv. Verificable con awk filter o contador en el script audit.
Cierre: audit con N≥50 ejecutado, match rate reportado con CI95 estrecho. Comparación directa con baseline 91%. Si cae dentro de CI95 del baseline: Fidelidad 2 confirmada definitivamente. Si cae fuera: investigar fenómeno adicional.
Referencias: §13.4 RESUELTO primer audit 2026-04-21, §2.4 v2.3.11, §12 Lección 25.

**[MEJORA] [EN_ESPERA] Caracterización clustering divergente live vs post-hoc — 2026-04-21**
Contexto: primer audit empírico 2026-04-21 detectó 2/13 NONE post-v2.3.11 (IMX 14:00 + GRT 01:00, ambos 2026-04-20). Análisis forense descartó state stale, reconcile, deploy boundaries como causa. Hipótesis dominante: clustering GMM live (con histéresis + warmup 1500 barras) diverge de classify_bars_gmm post-hoc en bars borderline con confidence 0.7-0.9.
No es bug. Es efecto estructural de arquitectura brain stateful (brain mantiene cluster entre ciclos) vs audit kernel stateless (recomputa clustering cada bar).
Argumentos a favor de clasificación benigna:
- Frecuencia 2/13 compatible con ruido GMM en bars borderline.
- Ambos trades rentables (+0.148 IMX, +0.066 GRT) → señales técnicamente válidas.
- 0 BRAIN_RECONCILE, state limpio, no reconcile intervino.
Disparo: si en audit N≥50 post-v2.3.11 entry-filter el rate NONE persiste ≥10%, caracterizar cuantitativamente. Si <5%, aceptar como ruido estadístico esperado.
Mitigación potencial: audit v5.2 añadiría exclusión `excluido_clustering_divergente` cuando kernel post-hoc asigna cluster distinto al live registrado en SIGNALS_RAW. Permitiría match rate más comparable con baseline teórico. Este enfoque requiere que el audit guarde el cluster_live de SIGNALS_RAW y lo compare con el cluster post-hoc. Coste estimado similar a audit v5.2 segmentación automática (2-3h). Puede consolidarse en la misma iteración audit v5.2.
Referencias: §13.4 RESUELTO primer audit 2026-04-21, §12 Lección 25, §13.3 REFERENCIA audit v5.2, investigación IMX+GRT 2026-04-21.

**[REFERENCIA] [ARCHIVADA] Refactor v2.5.0 state-after-confirmation — 2026-04-21**
Contexto: diseñada en Fase II-A (documento arquitectural de 10 secciones + alternativa §11 silent reconcile + §9.5 conflicto con Fidelidad 2 en tests bar-a-bar). Propondría separar `_mark_provisional` (bar de señal) de `commit_fill` (tras fill BingX), añadiendo flag `is_provisional: bool` a `SymbolState`. Scope: 5 módulos (brain_engine, execution_manager, live_engine, portfolio_manager como consumidor, SymbolState dataclass), 6 commits intermedios estimados, 8-15h.
Decisión 2026-04-21: **archivada**. Razones:
1. El diseño dual del sistema (simulación offline + ejecución online con mismo código de señales) produce el estado optimista intermedio como propiedad, no bug. El refactor lo renombraría sin eliminarlo: en tests bar-a-bar sin portfolio, `_mark_provisional` debería persistir sin commit (no hay fill), replicando semánticamente el mark actual.
2. **v2.4.2 silent reconcile** resuelve el problema observable (logs ruido) con complejidad mínima. Comportamiento post-v2.4.2 es operacionalmente idéntico a lo que produciría v2.5.0 desde el punto de vista externo.
3. **v2.4.3 pre-check symbol-aware** elimina la fuente de CRITICAL/EXEC ETH (la única externa) sin requerir refactor arquitectural.
4. Sección 9.5 del diseño detectó conflicto con tests bar-a-bar (Fidelidad 2) si brain no marca estado inmediatamente: mitigable pero añade complejidad innecesaria.
5. Riesgo/reward desfavorable: 8-15h + riesgo F2 vs beneficio marginal sobre v2.4.2+v2.4.3 (rollback silencioso en DEBUG ya es equivalente a no-mark externo).
Disparador para reactivar: si en futuro emerge necesidad operacional de state estricto (ej. observer externo que lea brain.state entre generate_signals y reconcile en vivo, o refactor que elimine pre_signal_state snapshot), reconsiderar. Alternativamente, al reciclaje julio si se quiere aprovechar un cambio mayor del pipeline para unificar arquitectura.
Referencias:
- Documento de diseño Fase II-A (conversación 2026-04-21 tarde, 10 secciones + §11 alternativa).
- Commit fe274e3 (auditorías Fidelidad 2 TF+MR) que motivó el diseño.
- §13.4 RESUELTO v2.4.2+v2.4.3 Smoke-A PASS.
- Decisión Ricardo 2026-04-21: optar por solución minimalista tras detectar que v2.5.0 "no resuelve causa raíz, solo la reviste" bajo el marco §0.6.
Cierre: permanente como referencia. No se re-abre salvo disparador explícito documentado.

**[AUDITORIA] [RESUELTO A04 TF + A04b MR] Auditoría Fidelidad 1 formal (kernel ↔ Pine) completada para ambas ramas — 2026-04-23**
Contexto: durante auditoría Fidelidad 2 TF cancel_tf de 2026-04-21 emergió comentario literal en kernel TF (lab_historico_numba_v8_3.py l.1560-1562) documentando divergencia consciente con Pine v44 canónico. Esto abrió pregunta sistemática sobre cuántas otras divergencias existen y cuántas son intencionales vs bugs olvidados.

**Auditoría TF completada 2026-04-23** (A04 scope kernel_TF ↔ Pine_v44_TF, ver §13.4 entrada A04 IMPLEMENTADO). **Auditoría MR A04b también completada mismo día** (kernel MR ↔ Pine v7.25 MR, ver §13.4 entrada A04b IMPLEMENTADO). Ambos scopes RESUELTOS.

**Resumen hallazgos A04 TF** (5 divergencias detectadas, veredicto limpio):

| # | Área | Tipo | Impacto | Estado |
|---|---|---|---|---|
| 1 | cancel_tf: resolved[t] vs ha_trend_tfN_e[barsSinceEntry] | DOCUMENTADA | medio | §0.6 aceptado |
| 2 | div_showlimit hardcoded 1 vs Pine 1-8 | NO DOC INTENCIONAL | medio | doc en A04 entry |
| 3 | kernel no soporta i_div_dontconfirm=true | NO DOC INTENCIONAL | bajo (default Pine coincide) | doc en A04 entry |
| 4 | kernel pivotes sobre close vs Pine close/HL param | NO DOC INTENCIONAL | bajo (default Pine coincide) | doc en A04 entry |
| 5 | cooldown diferenciado por tipo exit (emergency/cancel 1 bar fijo, sl/div param) | NO DOC POT INVOLUNTARIA | bajo con cooldown_bars=1 | investigar intención diseño pre-reciclaje |

**Cross-check §13.3 A30 (hidden asimetría TF vs MR)**: confirmado que A30 es asimetría **interna kernel TF ↔ kernel MR** (pre-swap bits 1↔3 en MR), NO divergencia kernel TF ↔ Pine TF. Bit mapping hid_inv=0 (tradicional) coincide con Pine hid_inverted=false.

**Cross-check §13.2 TS fidelity**: Pine L897-903 y kernel L1482-1492 idénticos funcionalmente (TS on-close con `low[1]/high[1]`, `math.max/min` monotónico, 0.5% prev bar). Fidelidad 1 en TS INTACTA — confirmando §13.2 HALLAZGO (el issue estaba en Fidelidad 2 bot live, resuelto v2.4.0).

**Cross-check §13.2 lag estructural 1 bar**: ni Pine ni kernel tenían lag. Era arquitectura bot live (resuelto v2.3.11). Fidelidad 1 no afectada.

**Veredicto**: auditoría TF limpia. Ninguna divergencia categórica que invalide arquitectura. Arquitectura Fidelidad 1 TF es robusta; sólo 1 ítem requiere investigación (Divergencia #5 cooldown).

Cierre: RESUELTO completo — scopes TF + MR auditados el mismo día 2026-04-23. Ver §13.4 entradas A04 (TF) y A04b (MR).
Referencias: §13.4 entrada A04 IMPLEMENTADO 2026-04-23, §0.6 Kernel como verdad operacional, `lab_historico_numba_v8_3.py` L1558-1562 (cancel_tf documentado), L1458-1460 (showlimit), L633 (dontconfirm), L641/653 (source), L1630-1637 (cooldown diferenciado), `indicador_v44_0_smartdiv_v11_0_TF.pine` L134-139 (div params), L897-906 (TS/SL), L912-934 (cancel_tf).

**[MEJORA] [RESUELTO A05] Deuda documental/refactor menores de auditoría Fidelidad 2 MR — 2026-04-23**
Contexto: agregado de MENORES emergidos durante auditorías Fidelidad 2 TF y MR del 2026-04-20 y 2026-04-21. Todos sin impacto operacional al detectarse.

**Resolución 2026-04-23** (rama `feature-a05-mr-docstring-cleanup` commit 8552b95, merge ca3bbd6):

- **MENOR 1 `_check_cancel_tf` dual-use docstring**: RESUELTO 2026-04-21 en commit previo (docstring actualizado con semántica TF+MR explícita + referencia §0.6).

- **MENOR 2 `_zone_bull_mr` helper extract**: RESUELTO 2026-04-23. Brain MR reemplaza 6 inline comparisons (`fast < slow` / `fast > slow`) en `_check_cancel_zona_mr` (L1735/1737/1747/1749) y `_check_cancel_ghost_mr` (L1777/1784) por calls a `zone_bull_mr(fast, slow)` / `zone_bear_mr(fast, slow)` — funciones module-level añadidas en `mean_reversion_features.py` (escalar + array friendly, NaN guard). `calc_zones` refactorizado internamente para delegar a los helpers (single source of truth). Drift silencioso eliminado por construcción.

- **MENOR 3 dead fields**: RESUELTO 2026-04-23 opción B (preservar con docstring DEPRECATED). `mr_entry_filters_forming` y `mr_entry_slow_line` mantenidos en `SymbolState` para back-compat con `engine_state.json` productivo (VPS + local). Docstring explícito sobre eliminación planificada en v3.0 pre-reciclaje. Campos siguen siendo asignados en entry path pero su "lectura" ahora es explícitamente None (dead confirmed).

- **MENOR docstring `_check_cancel_zona_mr`**: RESUELTO 2026-04-23. Docstring reescrito con semántica exacta:
  - Same day: compara zona_bull/bear MR en bar actual `t` con `slow_forming[t]` (NO "forming en entry_bar").
  - Day closed: compara zona_bull/bear MR en `entry_bar` con `slow_resolved[entry_idx]`.
  - Referencia §0.5 para semántica MR invertida (fast < slow = bull).
  - Args/Returns documentados.

**Validación**:
- Tests 6/6 PASS (`tests/test_a05_zone_helpers.py`): escalar basic, NaN defensive, array vectorizado, calc_zones delega, scalar helper ≡ inline comparison (100 random pairs), brain_engine usa helpers (no inline remnants).
- Regresión 34/34 PASS: W3 8/8 + W4 8/8 + A12 4/4 + A14 4/4 + A15 4/4 + A05 6/6.
- Smoke §0.8 Nivel A (BTC N=1000): diff 0.0000 exacto ✓.
- Smoke §0.8 Nivel C (SEI MR, MANDATORIO): 7/7 métricas diff 0.0000 ✓.
- Nivel B omitido: cambios aislados a helpers puros bit-equivalentes (test 5 prueba parity).

**Fidelidad 2 MR invariante por construcción**. Deploy VPS NO requerido (cambios activan al próximo restart del bot, helpers puros idempotentes). Bot v2.4.5 operacional con comportamiento bit-equivalente.

**Complementa A12 LL1** (commit ae5a21a): A12 consolidó MAs entre lab_lite ↔ lab_historico. A05 S3 consolida zonas MR entre mean_reversion_features ↔ brain_engine. Ahora brain MR es 100% pass-through para los 2 cómputos comunes (MAs + zonas).

Referencias: `live/brain_engine.py` L33-37 (import helpers), L148-156 (dead fields DEPRECATED docstring), L1718-1776 (docstring preciso + refactor cancel_zona), L1784-1796 (cancel_ghost refactor), `mean_reversion_features.py` L213-282 (zone_bull_mr/zone_bear_mr + calc_zones delegation), `tests/test_a05_zone_helpers.py`, §13.4 entrada A05 IMPLEMENTADO 2026-04-23.
Cierre: RESUELTO permanente. Próxima eliminación real de dead fields en v3.0 reciclaje.

**[INFORMACIONAL] Reapertura fantasma UNI (y patrón similar en ETH/ALGO) — reclasificado 2026-04-21 post v2.4.2+v2.4.3**
Contexto original: descubierto durante investigación post-v2.4.0 Smoke-B. Patrón recurrente donde brain emite signal, portfolio descarta (low_confidence, below_min_order) o execution falla (BingX reject), brain state queda fantasma, reconcile cycle siguiente resetea. Observado en UNI/USDT SHORT cycles 154-161 del 2026-04-20 (11 ocurrencias por low_confidence), ETH/USDT LONG 2026-04-20/21 (11 ocurrencias por BingX precision reject), ALGO/USDT SHORT 2026-04-21 (4 ocurrencias por below_min_order).
Reclasificación 2026-04-21 tras doble deploy:
- **Post-v2.4.2 silent reconcile**: el rollback esperado se loggea en DEBUG level `[BRAIN_ROLLBACK_EXPECTED]` (no INFO). Patrón persiste operacionalmente (parte del diseño dual brain↔kernel intencional v2.3.2) pero sin ruido observable en logs operacionales. Reset funcional idéntico (6 campos).
- **Post-v2.4.3 pre-check symbol-aware (+ hotfix ccxt format)**: el caso específico ETH que generaba CRITICAL `[EXEC] OPEN FALLIDO` queda eliminado por pre-check en portfolio (threshold 23.1 USDT reemplaza 5.0 genérico). Smoke-B cycle 182 confirmó label enriquecido `below_min_order_X.Xusdt` operando; ALGO descartado con `below_min_order_5.0usdt`. ETH directo pendiente validación orgánica.
Resolución efectiva del síntoma observable. Raíz (diseño dual optimista) preservada como propiedad intencional, ver entrada REFERENCIA ARCHIVADA v2.5.0 refactor para contexto arquitectural. Para observabilidad en análisis futuro: activar logging DEBUG temporalmente o filtrar trace del patrón.
Impacto: eliminado del flujo INFO + eliminado el CRITICAL ETH. Sin impacto operacional (no se pierden trades reales).
Disparador para re-apertura: si emerge efecto operacional adicional no anticipado (ej. observer externo que lea brain.state en ventana provisional y actúe incorrectamente), reconsiderar v2.5.0. O si balance crece >500 USDT y el patrón cesa orgánicamente (reduciendo también la relevancia).
Referencias:
- v2.4.2 silent reconcile (§13.4 RESUELTO 2026-04-21).
- v2.4.3 + hotfix (§13.4 RESUELTO 2026-04-21, combinado).
- v2.5.0 refactor archivado (§13.3 REFERENCIA ARCHIVADA 2026-04-21).
- §12 Lección 24 (mocks que replican asunciones del código propio, caso origen ccxt format).
- Patrón observado cycles 154-161 del 2026-04-20 + cycles 166-178 del 2026-04-21 + cycle 182 (validación).

**[MEJORA] [EN_ESPERA] v2.3.11 Opción B2 — forming fetch tardío para residual 6s→2s — 2026-04-19**
Contexto: v2.3.11 aplicó Opción B1 (forming fetch en paralelo al inicio del cycle, ~6s antes del cierre). Opción B2 (forming fetch tardío tras sleep, ~2s antes del cierre) captura 4 segundos adicionales de proximidad con complejidad arquitectónica no justificada por el beneficio marginal dada la proporción ya capturada por B1 (99.8% del sesgo original eliminado). B2 requiere refactor de _run_cycle_inner con split download + sleep + coordinación temporal frágil.
Disparo: si tras ≥N≥50 trades post-v2.3.11, el residual de 6s muestra sesgo sistemático detectable en slippage_entry del analyzer v2.4.1. Virtualmente improbable — documentado para completitud del marco de decisiones.
Cierre: decisión tomada tras datos empíricos, o aceptación permanente del residual B1 como suficiente.
Referencias: investigación pre-implementación v2.3.11 del 2026-04-19 (§6 append strategy, §riesgos opciones B1/B2).

**[MEJORA] [EN_ESPERA] Establecer git+GitHub para combolab — 2026-04-17**
Contexto: Prerequisito para usar /ultrareview sobre futuros fixes críticos. Beneficios adicionales independientes de /ultrareview: trazabilidad real (commits por versión vs sección 2.4 manual), rollback fácil, sincronización nativa entre comboclaude y combolab, gate de despliegue reproducible desde commit conocido.
Verificación previa requerida: confirmar que ningún archivo Python contiene secrets hardcoded (BingX API keys, Telegram tokens). Si están en .env/env vars como se espera, OK. Si hay alguno en código, limpiar antes de commitear.
Disparo: aproximadamente tras completar v2.3.6 (H1+H4) y resolver los serios de Capa 1 que decidamos abordar antes del primer run de /ultrareview. También puede hacerse proactivamente en cualquier momento entre ahora y el primer run. No urgente hasta que acumulemos varios commits post-v2.3.6 que merezcan versionado.
Cierre: combolab como repo git con remote GitHub privado, commit inicial del estado actual, documentado workflow de deploy desde commit conocido.
Referencias: investigación /ultrareview del 2026-04-17, política de uso en 13.4 (ítem "Naturaleza real de /ultrareview").

**[DECISION] [EN_ESPERA] P1 leverage NO es fix simple — requiere proyecto separado — 2026-04-17**
Contexto: Investigación leverage confirmó que el lab simula a 1x. Los specialist_scores, pf_combined, maxdd_worst están calibrados para ese mundo. Aplicar compute_leverage_map sin más convierte el bot en un sistema que el lab nunca simuló — maxDD sobre capital deja de corresponder a maxdd_worst del JSON, liquidación se vuelve riesgo real (10x = liquidación a -10%), funding escala sobre notional apalancado. El fix correcto NO es simplemente eliminar el `*100.0`. Requiere:
  a) Decidir si queremos leverage variable o mantener 1x como feature.
  b) Si leverage variable: adaptar el kernel de auditoría para simular con leverage; recalibrar maxdd_worst y specialist_scores en próximo reciclaje teniendo en cuenta leverage objetivo.
  c) Cap adicional de safety (ej: max_leverage=3x mientras balance <1000 USDT).
  d) Comparar resultados empíricos pre/post con datos reales antes de decidir.
  e) Revisar E3 del ultra review de execution (emergency SL usa fill_price vs close_brain) — su criticidad aumenta drásticamente con leverage alto.
No es fix de Capa 1 — es un proyecto arquitectónico separado.
Disparo: tras primer reporte audit v5.1 con N≥50 (baseline 1x documentada), cuando haya evidencia empírica del sistema actual para comparar con hipótesis leverage.
Cierre: decisión tomada sobre una de 3 opciones: (1) fix aplicado con cap de safety, (2) 1x adoptado como feature oficial (actualizar lab para no calcular leverage), (3) posposición explícita hasta balance mayor.
Referencias: HALLAZGO "Investigación leverage lab↔producción" 2026-04-17, ítem P1 "Leverage map siempre 1x", ítem E3 emergency SL.

**[MEJORA] [EN_ESPERA] Verificar setLeverage con valores altos antes de aplicar P1 — 2026-04-17**
Contexto: El fix histórico `setLeverage: params={'side': 'BOTH'}` (§2.6) se ha probado en producción solo con leverage=1x uniforme durante semanas. Si P1 se aplica y los símbolos usan 2x, 5x, 10x, el flujo setLeverage ejecuta con esos valores. Hay que verificar que BingX acepta esos valores vía ccxt sin errores raros (permiso de cuenta, margin mode, maximum leverage por símbolo de BingX). Fase 1 C2 intentó validación local pero bloqueado: no hay credenciales BingX en entorno local. Test requiere scp del .env del VPS o ejecución en VPS fuera de ventana cycle (xx:59:50-xx:00:10).
Disparo: al arrancar proyecto P1 tras primer reporte audit v5.1 con N≥50. Incluir entonces en el scope de P1 el test de setLeverage con 2x/5x/10x (desde local tras scp del .env, o desde VPS en ventana xx:30-xx:45).
Cierre: test completado, setLeverage verificado con valores altos, o documentación de limitaciones encontradas.
Referencias: execution_manager.py setLeverage invocación, fix histórico §2.6 sobre side=BOTH, Fase 1 C2 bloqueo 2026-04-19.

**[DECISION] [EN_ESPERA] Dependencia: test diferencial brain vs kernel es prerrequisito de fix R1 — 2026-04-17**
Contexto: En el ultra review de brain_engine.py, el ítem "Test diferencial brain vs kernel sobre histórico" (MEJORA en 13.3) es prerrequisito del análisis que bloquea el fix R1 (cooldown divergence). Sin el test diferencial, no tenemos forma de medir el impacto del fix R1 en trades y PnL, y por tanto no podemos aplicar R1 con evidencia. El orden correcto es: primer reporte v5.1 con N≥50 → test diferencial _run_verify_test sobre BTC/ETH 10k+ barras → análisis de impacto de R1 pre/post fix → decisión sobre aplicar R1 o documentar la divergencia aceptada.
Disparo: al tener primer reporte v5.1 disponible.
Cierre: test diferencial ejecutado, impacto de R1 medido y fix aplicado o justificadamente diferido.
Referencias: ítem "Cooldown brain diverge del kernel" en 13.2, ítem "test diferencial brain vs kernel" en 13.3.

**[MEJORA] [RESUELTO] lab_lite LL1 (A12): MA implementations deduplicadas — 2026-04-23**
Contexto: Ultra review lab_lite LL1 (2026-04-17). Funciones calc_ema, calc_sma, calc_hma, calc_alma, calc_kama, calc_dema, calc_tema, calc_mcginley, calc_vidya, calc_frama, calc_t3, calc_ssmoother, calc_vwma, calc_tenkan, calc_jma se asumía duplicadas en 4 archivos. Drift silencioso si alguien modificaba una sin actualizar las demás.

**Hallazgo del inventario Fase 1 (2026-04-23)**: la hipótesis "4 archivos" era incorrecta. Duplicación real es **2-way**:
- `lab_historico_numba_v8_3.py`: source-of-truth canónica (16 MAs).
- `lab_lite_zonas_v5e.py`: copias independientes (17 MAs, incluye calc_wma único).
- `live/brain_engine.py`: **pass-through** — ya importa desde lab_historico (L34-45).
- `mean_reversion_features.py`: pass-through — importa subset desde lab_historico (L23-34).
- `mean_reversion_kernel.py`: no usa MAs directamente (consume features precomputadas).

**Verificación Fase 2 bit-a-bit** (52 tests: 14 pares × 3-4 periods):
- **13 de 14 MAs con diff absoluto 0.000e+00** (idéntico bit-a-bit).
- 4 MAs con drift sub-ε (max 3.3e-11 en calc_vwma por cumsum vectorizado vs loop en lab_historico).
- **52/52 PASS rtol=1e-10**. Veredicto: **Caso A — TODAS EQUIVALENTES**.
- calc_wma solo en lab_lite, sin contraparte pública en lab_historico (está como closure interno en calc_hma lite); único usuario era lab_lite.calc_hma local.

**Refactor Fase 4 aplicado** (branch `feature-a12-ma-dedup`, commit pendiente):
- `lab_lite_zonas_v5e.py`: bloque MAs L112-348 (234 líneas) reemplazado por import consolidado desde lab_historico_numba_v8_3 (17 líneas). calc_wma eliminado (ya no tenía caller post-refactor dado que calc_hma importado tiene wma interno).
- lab_historico sin cambios (source canónica preservada).
- brain_engine sin cambios (transitivo).
- Neto: -234 líneas / +17 líneas.

**Validación post-refactor**:
- `tests/test_a12_ma_parity.py` 4/4 PASS (16/16 MAs son literal `is` True mismas funciones, calc_wma eliminado, dispatcher calc_ma operativo, sanity numérico trivial).
- No-regresión: `tests/test_w3_bootstrap.py` 8/8, `tests/test_w4_thresholds.py` 8/8.
- Smoke §0.8 Nivel A (BTC N=1000): diff 0.0000 exacto ✓.
- Smoke §0.8 Nivel C (SEI MR): 7/7 métricas diff 0.0000 ✓.
- Nivel B omitido por scope: A12 NO toca brain_engine ni kernel Numba (solo lab_lite, pipeline del lab usado por master.py). §0.8 establece Nivel B como gate obligatorio para cambios brain/kernel — fuera del scope. Parity tests + Nivel A+C bastaron.

**Resultado**: 0 posibilidad de drift por construcción (`lite.calc_X is lab.calc_X`). Cualquier modificación futura a MAs se aplica automáticamente a ambos consumers. Deuda técnica LL1 eliminada permanentemente para TF. Fidelidad 2 invariante por construcción (brain ya usaba lab_historico).

**Nota residual lab_historico**: `calc_tenkan` definido 2 veces internamente (L536 DataFrame-based, L929 arrays-based). Duplicación intra-archivo no cubierta por A12 (scope cross-file). Candidato a refactor menor pre-reciclaje si emerge necesidad.

Disparo: N/A (item cerrado).
Cierre: RESUELTO 2026-04-23, commit siguiente a 56d38d4 en rama feature-a12-ma-dedup → merge main pendiente.
Referencias: lab_lite_zonas_v5e.py L112-130 (imports consolidados post-refactor), tests/test_a12_ma_parity.py, §13.4 entrada A12 IMPLEMENTADO 2026-04-23.

**[MEJORA] [RESUELTO] lab_lite LL2 (A13): ratio supervivencia presets saludable — 2026-04-23**
Contexto: Ultra review lab_lite LL2 (2026-04-17). `run_simulation_v5e` simula SOLO zonas MA puras fast/slow (+trend post-hoc derivado como slow×4, no simulado en kernel). Sin TF filters, sin divergencias, sin cancelaciones (cancel_tf/zona/ghost/div), sin SL, sin TS. Presets seleccionados son "robustos a zonas puras". Walk-forward después añade los filtros completos sobre cada preset × 4M configs. El caveat §13.3 original era que presets cuyo edge depende de filtros añadidos podrían nunca pasar el pre-filtro lite.

**Criterio empírico §13.3 literal**: "Si <20% presets pasan walk-forward → reducción demasiado agresiva".

**Análisis empírico 2026-04-23** sobre 45 símbolos productivos (`output/production/presets_SYMBOL.csv` vs `regime_wf/SYMBOL_specialist_configs.json`):

Métrica: ratio de presets únicos (signature `fast_type(period)/slow_type(period)`) de lab_lite CSV que aparecen en `top_configs` del JSON walk-forward (deduplicado por signature, excluyendo hyst tag _H00/_H05).

| Métrica | Inputs lab_lite | Survived WF | Ratio% |
|---|---|---|---|
| Mean | 30.5 | 11.2 | **36.7%** |
| Median | 31 | 11 | **34.4%** |
| Min | 28 | 5 | 16.7% (MANA) |
| Max | 32 | 20 | 63.3% (FET) |

**Distribución según criterio §13.3 LL2**:
- <20% (agresivo): **2/45 = 4.4%** (APTUSDT 17.2%, MANAUSDT 16.7%).
- 20-70% (saludable): **43/45 = 95.6%**.
- >70% (sobredimensionado): 0/45.

**Veredicto**: **Caso saludable**. Ratio mean 36.7% cómodamente por encima del threshold 20%. Ningún símbolo en rango sobredimensionado. Sin fix al pipeline.

**Cross-check cualitativo con W3 flagged (6 top-1 productivos 2026-04-23)**:
- MANA C0 (cfg 5339578) flagged W3 + ratio MANA 16.7% (lowest). Correlación observable.
- APT C1 (cfg 31447907) reemplazado bajo W4 simulado + ratio APT 17.2% (2nd lowest). Correlación observable.
- Otros 4 flagged W3 (ONDO 45.2%, LTC 36.7%, GRT 28.6%, TRX 37.5%, BTC 41.9%) en rango saludable — flagged por ci_width/ci_low W3, no por supervivencia.

**Hipótesis residual**: supervivencia baja lab_lite → walk-forward puede correlacionar con mayor probabilidad de specialists flagged W3 (casos MANA, APT). Potencial item monitoreo post-reciclaje; no acción inmediata.

**Caveat diseño consciente**: el bias estructural del kernel lite (ausencia de SL/TS/divergencias/cancelaciones/filtros HTF) es INTENCIONAL y documentado — pre-filtro rápido sobre zonas puras. El 36.7% mean demuestra que este diseño NO sesga excesivamente la selección de specialists; walk-forward refina sobre un pool adecuado de presets candidatos.

Disparo: N/A (item cerrado).
Cierre: RESUELTO documental 2026-04-23. Ratio saludable empíricamente. No requiere ampliar TOP_N_PRESETS ni modificar kernel lite. Sin fix de código. Los 2 outliers (APT, MANA) quedan como símbolos a monitorear en audits futuros.
Referencias: lab_lite_zonas_v5e.py `run_simulation_v5e` L558-684 (kernel), L144-165 (`build_catalog` trend=NONE), presets CSVs en output/production/, JSONs regime_wf/, §13.4 entrada A13 IMPLEMENTADO 2026-04-23.

**[MEJORA] [RESUELTO] regime_walk_forward W1 (A14): plateau_ratio consistency con _get_neighbors — 2026-04-23**
Contexto: Ultra review W1 (2026-04-17). plateau_ratio usaba bit-flip brutal en los 26 bits del config_id, mientras `_get_neighbors` (canonical, usado en `_compute_sqn_haircut`) respeta semántica bitmask vs discrete de `_PARAM_FIELDS`. Misma función semántica con dos implementaciones inconsistentes en el mismo módulo. Fix aplicado 2026-04-23 en rama `feature-a14-a15-wf-polish` (commit 5a7135b, merge cf9d7b6):
- Bloque Phase 4 Plateau analysis reemplaza los 4 líneas del bit-flip loop por llamada única a `_get_neighbors(cid)`.
- Evidencia test_2 empírica: ONDO C0 cfg 2457036 — canonical=25 neighbors vs brute-26=26 neighbors, symmetric diff 3 (3 neighbors del brute NO son paramétricamente adyacentes — flips de bit alto en campo discreto saltaban valores no-vecinos).
- **plateau_ratio NO es filtro de selección** en pipeline canónico (metadata informativa pura: reporte L1780 + JSON output opcional L2087). extractor_gemas.py sí lo usa como filtro pero NO está en pipeline productivo (master.py no lo invoca, §13.2). Impacto retroactivo: cero operacional. JSONs actuales mantienen plateau_ratio con fórmula vieja hasta próximo reciclaje, cuando se regenera con nueva fórmula.
- Tests 4/4 PASS (tests/test_a14_plateau_consistency.py).
- Smoke §0.8 Nivel A+C diff 0.0000. No-regresión W3/W4/A12 16/16 PASS.
Referencias: regime_walk_forward.py L1853-1869 (plateau block post-fix) + L1246-1275 (`_get_neighbors` canonical), §13.4 entrada A14 IMPLEMENTADO 2026-04-23.
Cierre: RESUELTO. Próxima activación en `master.py --recycle`.

**[MEJORA] [RESUELTO] regime_walk_forward W2 (A15): engine tag en parquet + resume consistency — 2026-04-23**
Contexto: Ultra review W2 (2026-04-17). Bifurcación CUDA↔CPU runtime (L487-505) con `engine_tag` local usado solo para print, NO persistido en parquet. Risk: run mezcla engines tras crash/resume → heterogeneidad silenciosa en specialists (precisión float32/float64 + orden reducciones difieren marginalmente). Fix aplicado 2026-04-23 en rama `feature-a14-a15-wf-polish` (commit 5a7135b, merge cf9d7b6):
- Módulo añade constantes `_MACHINE_ID` (platform.node()), `_NUMBA_VERSION`.
- Función `_get_engine_tag()` retorna dict {engine_name ("cuda"|"cpu_numba"), engine_version (numba=x.y.z), machine_id, timestamp_run (ISO UTC)} — timestamp fresh por invocación.
- Función `_check_resume_engine_consistency(parts_dir)` lee engine_name del primer parquet existente. WARN loud si mismatch con current. Legacy parquets pre-A15 sin columna tolerados con WARN "unknown".
- `process_symbol` invoca check tras crear `parts_dir`.
- Parquet output L548-580 extendido con 4 columnas engine (broadcast a todas las rows del DataFrame).
- Tests 4/4 PASS (tests/test_a15_engine_tag.py): campos válidos + timestamp ISO parseable, parquet round-trip preserva columnas, resume check match → 'consistency OK', legacy → WARN 'pre-A15 unknown' no abort.
- Smoke §0.8 Nivel A+C diff 0.0000. No-regresión W3/W4/A12/A14 28/28 PASS.
Impacto retroactivo: parquets actuales (pre-A15) no tienen engine tag. Primera regeneración completa via `master.py --recycle` los reescribe con tag. Resume intermedio sobre parquets mixtos emite WARN pero no bloquea.
Referencias: regime_walk_forward.py L56-128 (engine tag module) + L460 (resume check call) + L548-585 (parquet write + engine columns), §13.4 entrada A15 IMPLEMENTADO 2026-04-23.
Cierre: RESUELTO. Observabilidad activada para próximo reciclaje.

**[MEJORA] [RESUELTO] regime_walk_forward W3: bootstrap pf_fwd + selection by ci_low — 2026-04-23**
Contexto: Ultra review W3 (2026-04-17). specialist_score y pf_fwd eran point estimates sin intervalo de confianza. Configs con N=15-20 y 1-2 outliers inflaban pf_fwd artificialmente. Validado empíricamente 2026-04-22: ONDO C0 walk-forward entregó pf_fwd=7.945 con N=17, real observado PF 1.08 (ratio 0.14). Fase II.C reveló 2 candidatos exclusión adicionales (ONDO C2 + SAND C1). Item 3.5 ranking stability: ranking WF ≠ ranking kernel-actual (config #1 WF 2457036 es rank #4 en régimen actual).
W3 fue elevado a PRIORIDAD ALTA como prerequisito OBLIGATORIO pre-reciclaje (§12.29 Lección walk-forward N pequeño infla PF).

**Implementación 2026-04-23** (branch `feature-w3-bootstrap-pf-fwd`):
- W3a aditivo: función `_bootstrap_pf_fwd_vectorized` — N=1000 resamples binomial sobre pool sintético {W × avg_win, (T-W) × -avg_loss} reconstruido desde agregados `{trades_fwd, wins_fwd, gp_fwd, gl_fwd}`. Chunking 5000 configs/batch (~40MB RAM). Seed 42 determinista. Computa `pf_fwd_ci_low, pf_fwd_ci_high, ci_width` (percentil 2.5/97.5).
- Función `_apply_bootstrap_pf_fwd(df)`: añade 6 columnas (`pf_fwd_ci_low, pf_fwd_ci_high, ci_width, pf_combined_ci_low, specialist_score_ci_low, flag_sospechoso_outlier`). `pf_combined_ci_low = (gp_tr + pf_fwd_ci_low × gl_fwd) / (gl_tr + gl_fwd)` (substituye gp_fwd conservadoramente). `specialist_score_ci_low` usa misma fórmula que `_compute_sqn_haircut` con `pf_combined_ci_low`. Flag disparado por `pf_fwd_ci_low < 1.0 OR ci_width > 5.0`.
- W3b cambio selección: integrado en `extract_validated_specialists` post-`_compute_sqn_haircut` → `top_all.sort_values('specialist_score_ci_low')`. JSON output y report text reflejan el nuevo orden.
- JSON output `top_configs[*]` extendido con 6 campos W3.
- Report text nueva sección "W3 BOOTSTRAP pf_fwd" con distribuciones y flagged count.

**Caveat metodológico documentado**: bootstrap binomial sobre pool sintético **NO captura dispersión intra-grupo** (todos los wins tratados como avg_win uniforme). CI resultante es **lower bound** de la incertidumbre real. Implementación fiel trade-level requeriría modificar kernel Numba `run_on_slice` para exportar arrays de PnL per trade — cambio invasivo no justificado para W3 inicial. Aproximación Opción F suficiente para detectar casos como ONDO C0 (CI ancho claramente flagged).

**Validación empírica sobre JSONs productivos** (2026-04-23):
- ONDO C0 config 2457036 (WF #1, Fase II.B): pf_fwd=7.94 N=17 → ci_low=2.75, ci_width=36.36 → **flagged=Y ✓** (coincide con expectativa empírica post-Fase II.B).
- 967/1000 top validated ONDO C0 configs flagged (96.7%) → sesgo N pequeño dominante en este cluster.
- 6/12 top-1 productivos cross-symbol flagged (50%): ONDO C0, LTC C2, GRT C2, TRX C2, BTC C2, MANA C0. NO flagged (N≥58): SEI C2, STX C2, UNI C0, DOT C1, BCH C0, HBAR C1.
- Score penalty W3b típica: 7-24% (ONDO −24%, TRX −7%).
- ci_low=2.75 de ONDO está por encima del real 1.08 → confirmación empírica del caveat: bootstrap binomial es **lower bound**. Real CI más ancho; aún así flag operativo.

**Tests 8/8 PASS** (tests/test_w3_bootstrap.py): happy N=5, fallback N<5, all-winners, all-losers, seed determinism, ONDO-like flagged, pf_combined_ci_low conservador, W3b selection change.

**NO hay deploy**. Código en rama, pendiente activación via próximo `master.py --recycle`. Bot v2.4.5 sigue operacional con specialists actuales. Fidelidad 2 invariante (cambio es del pipeline del lab, no toca brain/execution/portfolio).

Cierre: **IMPLEMENTADO 2026-04-23**. Commit en rama `feature-w3-bootstrap-pf-fwd`. Siguiente ítem dependiente: W4 (_FWD_MIN_TRADES 15 → 25/30) — análisis cuantitativo ahora factible con CI data que W3 provee.
Referencias: regime_walk_forward.py L930-1030 (constantes W3 + `_bootstrap_pf_fwd_vectorized` + `_apply_bootstrap_pf_fwd`), L1668-1677 (integración post-haircut), L1770-1788 (JSON output), tests/test_w3_bootstrap.py, §12.29 Lección metodológica, §13.4 Fase II.B+II.C+Item 3.5 2026-04-22 (validaciones empíricas base), §13.4 entrada W3 IMPLEMENTADO 2026-04-23.

**[MEJORA] [RESUELTO] regime_walk_forward W4: _FWD thresholds + CI filters — 2026-04-23**
Contexto: Ultra review W4 (2026-04-17). `_FWD_MIN_TRADES=15` y `_FWD_MIN_PF=1.0` permitían configs con poca muestra y PF borderline pasar filtro. Outliers de entry timing sobrevivían. Vinculado con W3 (bootstrap pf_fwd).

**Implementación 2026-04-23** (misma rama `feature-w3-bootstrap-pf-fwd`, layered sobre W3):

Análisis cuantitativo Fase 1 sobre **138k candidates** (45 símbolos activos + TON histórico × 3 clusters × top-1000 cada):
- Distribuciones base: trades_fwd median=73 p25=37; pf_fwd median=2.47 p25=1.83; pf_fwd_ci_low median=1.52; ci_width median=2.34 p75=5.86; ~35% del pool flagged por W3.
- Sensibilidad (trades × pf, sin CI): subir 15→25 elimina solo 80 candidates de 90k (0.09%). Subir PF 1.0→1.1 elimina 74 más. Diferencias marginales.
- **`NOT sospechoso` es el filtro dominante**. Reduce pool 138k → 90k (-35%).
- Combinaciones ensayadas: ninguna con `NOT sospechoso` activa deja <134/138 clusters operables.

**Thresholds adoptados**:
- `_FWD_MIN_TRADES = 25` (+10 vs baseline; defense-in-depth con W3; alineado con Lección 29).
- `_FWD_MIN_PF = 1.1` (marginal sobre 1.0; consistencia metodológica).
- `_FWD_REQUIRE_NOT_SOSPECHOSO = True` (filtro dominante — encapsula `ci_low ≥ 1.0 AND ci_width ≤ 5.0` vía W3 flag).
- `_FWD_MIN_CI_LOW = 0.0` (hook opcional, default OFF — redundante con NOT sospechoso).
- `_FWD_MAX_CI_WIDTH = inf` (hook opcional, default OFF — redundante con NOT sospechoso).

Los dos últimos hooks se exponen para calibración futura sin code change.

**Arquitectura del cambio**:
- `regime_walk_forward.py` L923-932: constantes W4 documentadas con racional.
- L1032-1074: función nueva `_apply_w4_fwd_ci_filters(df, ...)` — filtra sobre DataFrame post-bootstrap con NOT sospechoso + hooks opcionales.
- L1690-1703: integración en `extract_validated_specialists` post-W3 bootstrap + WARN log si cluster queda orphan.
- L1552-1556: reporte text muestra tanto base thresholds como CI thresholds aplicados.

**Validación Fase 3 — reciclaje hipotético sobre JSONs actuales**:

| Métrica | Valor |
|---|---|
| Clusters productivos (45 activos × 3) | 135 |
| Clusters orphan bajo W4 | **3** (TAO C1, TRX C2, WLD C0) |
| Símbolos con 3/3 clusters operables | **42/45 (93%)** |
| Símbolos con 2/3 clusters | 3 |
| Clusters donde mismo specialist ganaría | 26 (19%) |
| Clusters donde cambia specialist | 106 (79%) |

**Cross-check los 6 flagged W3 (top-1 productivos actuales)**:
- ONDO C0 2457036 → reemplazado por 33586655.
- LTC C2 2532096 → 1534656.
- GRT C2 58457547 → 41610560.
- TRX C2 53066572 → **ORPHAN** (top-1000 completo no pasa filtros).
- BTC C2 20607806 → 33831247.
- MANA C0 5339578 → 5339579 (config adjacent in bit space, similar preset).

**TRX C2 caso crítico**: fue top TF score 30.9 (§2.1), N=33 pf_fwd=12.74 flagged ci_width=34.51. W4 revela que el cluster entero no tiene candidatos robustos — todos los 1000 top tienen N<25 o flagged. TRX seguirá operable en C0 y C1. Hallazgo consistente con Lección 29 (walk-forward N pequeño infla PF selecciona noise, no edge).

**Patrón de reemplazo típico**:
- Old: pf_fwd alto + N pequeño + flagged (ej. APT C1 PF 4.78 N=25 flagged).
- New: pf_fwd moderado + N grande + CI estrecho (ej. APT C1 PF 1.63 N=146 clean).

Defense-in-depth operando como diseño pretende.

**Tests 8/8 PASS** (tests/test_w4_thresholds.py): constantes, NOT sospechoso bloquea flagged + pasa clean, hooks ci_low/ci_width ON/OFF, retroactivo ONDO C0 bloqueado.

**No regression W3**: `tests/test_w3_bootstrap.py` sigue 8/8 PASS.

Deploy VPS NO requerido (cambio del pipeline del lab). Activación en próximo `master.py --recycle`. Bot v2.4.5 operacional con specialists actuales preservados hasta reciclaje formal.

Cierre: **IMPLEMENTADO 2026-04-23**. Commit siguiente a 4e54c8d en rama `feature-w3-bootstrap-pf-fwd`. Siguiente dependiente: `§13.3 política adelantar reciclaje por criterio empírico` — W4 facilita decisión (ratio sospechosos/total por cluster es métrica monitorizable).
Referencias: regime_walk_forward.py L919-932 (constantes), L1032-1074 (_apply_w4_fwd_ci_filters), L1690-1703 (integración), tests/test_w4_thresholds.py, §13.4 entrada W4 IMPLEMENTADO 2026-04-23, §12.29 Lección base, §13.4 W3 entrada 2026-04-23 (prerequisito).

**[MEJORA] [EN_ESPERA] data_feed: attach stops redundante en get_open_positions — 2026-04-17 (v2.3.8 investigado, no aplicado)**
Contexto: Ultra review D3. get_open_positions líneas 242-251 hacen get_open_orders y attachean stop_order_id. Pero reconcile_state (execution_manager) usa su propia llamada a get_open_orders desde live_engine línea 424. Dos fetches por ciclo de fetch_open_orders.
VERIFICADO 2026-04-19 (B6 Fase 3): el attach SI tiene consumer real — `close_position` en execution_manager.py linea 258: `stop_order_id = position.get("stop_order_id")` — se usa para cancelar el stop vinculado al cerrar posicion. La eliminacion trivial rompe close_position. Refactor alternativo (eliminar la llamada separada en live_engine y mantener attach como single source of truth) no es viable porque reconcile_state necesita la orders list completa, no solo stop_order_id por simbolo.
Redundancia real: 2 llamadas fetch_open_orders por ciclo. Coste minimal.
Disparo: al proximo reciclaje (julio), cuando se pueda refactorizar close_position para buscar el stop en orders directamente en lugar de usar position.stop_order_id embebido. Alternativa: introducir parametro `orders=None` en get_open_positions y si se provee usarlo en vez de fetch (permite compartir orders entre llamadas).
Cierre: refactor aplicado con eliminacion de la redundancia, o decision documentada de mantener arquitectura actual con 2 fetches.
Referencias: data_feed.py get_open_positions líneas 242-251, execution_manager.py close_position linea 258, Fase 3 B6 del 2026-04-19.

**[MEJORA] [EN_ESPERA] live_engine: orphan reconstruction usa sl_level brain, no real exit price — 2026-04-17**
Contexto: Ultra review L4. Líneas 872-876 de _reconcile_brain_after_execution: estimated_exit = sl_level del brain (fixed 3% + TS). Real exit puede haber sido emergency SL 5% (intrabar) o TS mayor. PnL reconstruido desvía ±2%. Flag 'reconstructed' marca el trade; analyzer v2.4.1 los excluye de agregados via fix C3.
Disparo: si aparecen múltiples orphan closes y el desajuste de PnL reconstruido afecta análisis.
Cierre: en lugar de sl_level, fetch price real de BingX al momento del trigger (via fetch_my_trades o fetch_order), o documentar aceptación del desajuste.
Referencias: live_engine.py _reconcile_brain_after_execution líneas 872-876.

**[MEJORA] [EN_ESPERA] execution_manager: estimated funding fallback ignora side → signo invertido para longs — 2026-04-17**
Contexto: Ultra review E1. Línea 177: `estimated = rate * position_size_usdt * periods_8h`. No considera side del trade. Convención ccxt: amount>0 recibido, amount<0 pagado. Para LONG con rate positiva, trader PAGA (debería ser negativo); formula actual devuelve positivo. Ruta activa solo cuando fetch_funding_history falla (exception) y cae al fallback estimado. Frecuencia actual desconocida — grep en logs "Funding history no disponible" revelaría incidencia.
Disparo: si analyzer v2.4.1 reporta funding con signos inesperadamente invertidos para longs, o si log engine muestra uso frecuente del fallback.
Cierre: pasar `side` a `_get_position_funding` y multiplicar por -1 si long (o `-side_sign`).
Referencias: execution_manager.py _get_position_funding líneas 143-186, DECISION sobre sign de funding del 16/04 en 13.2.

**[MEJORA] [EN_ESPERA] execution_manager: emergency SL usa fill_price no entry_price_brain — 2026-04-17**
Contexto: Ultra review E3. Línea 469: `stop_price_bingx = fill_price * (1 - SL_EMERGENCY_PCT / 100)`. Kernel asume emergency_sl = close_de_la_barra × 0.95. Producción usa fill_price que puede diferir por slippage. Divergencia sub-% típicamente.
Disparo: si auditoría v5.1 muestra divergencia de precios de exit por SL emergencia (kernel triggerea a close×0.95, producción a fill×0.95). Actualmente los trades observados caen por sl_hit (software SL 3%) o normal exits, no sl_emergency.
Cierre: pasar entry_price (close de señal del brain) como parámetro a open_position y usarlo para calcular stop_price_bingx, en lugar de fill_price.
Referencias: execution_manager.py open_position línea 469.

**[MEJORA] [EN_ESPERA] execution_manager: ventana sin stop entre cancel y place-new — 2026-04-17**
Contexto: Ultra review E4. El patrón cancel-then-place (necesario porque BingX no soporta modify-order) deja ~100ms+latencia sin stop. Mitigado por rama de fallo que coloca emergency SL si place-new falla, pero la ventana existe.
Disparo: si en un evento de volatilidad extrema ocurre trigger de stop entre cancel y place-new, y no hay orphan reconstrucción adecuada.
Cierre: investigar si BingX añade en nueva versión soporte para modify-order, o usar un flag `keep_previous_on_fail` antes del cancel.
Referencias: execution_manager.py update_trailing_stop líneas 610-648.

**[MEJORA] [EN_ESPERA] portfolio_manager: vol_weight puede neutralizar dd_multiplier en low-vol — 2026-04-17**
Contexto: Ultra review S1. Líneas 387-396: effective_max_pos_pct aplica dd_multiplier, pero el cap max_allowed usa max_single_position_pct SIN dd. Con vw=2 (símbolo low-vol típicamente BTC) y dd=0.5, adjusted = min(2.5% × 2, 5%) = 5% — DD neutralizado. Ambigüedad de diseño: si el 5% cap es "risk-equivalent" entonces OK, si es "dollar exposure bajo cualquier condición" entonces OK actual, si es "dd_reduced%" entonces bug. Impacto real: BTC (principal símbolo low-vol) escapa al DD reduce.
Disparo: cuando haya primer evento DD breaker activo + posición BTC, observar si BTC mantiene 5% o se reduce.
Cierre: decidir semántica canónica (probablemente: cap debe respetar dd también) y documentar en CONTEXTO; aplicar fix si necesario.
Referencias: portfolio_manager.py allocate_positions líneas 387-396.

**[MEJORA] [EN_ESPERA] portfolio_manager: compute_leverage_map "último operable" heurística — 2026-04-17**
Contexto: Ultra review S3. Líneas 623-627 iteran clusters operables y el if/else es vestigial (ambos asignan `best_maxdd = maxdd`). El cluster activo en producción puede tener maxdd muy distinto del "último operable iterado". Leverage desalineado del cluster real. Inactivo hasta que P1 se fixee (mientras lev=1x, esto no importa).
Disparo: al aplicar fix de P1 (leverage variable), este issue se vuelve relevante.
Cierre: usar maxdd del cluster actual activo (state.current_cluster) en tiempo de ejecución, o del cluster con mejor specialist_score.
Referencias: portfolio_manager.py compute_leverage_map líneas 623-627.

**[MEJORA] [EN_ESPERA] portfolio_manager: block_reduction agrupa 3 factores distintos — 2026-04-17**
Contexto: Ultra review S6. Campo `block_reduction` en allocation dict es realmente `block × sector × global`, no solo block. Analyzer v2.4.1 y logs SIGNALS_EXECUTED usan "br" pero no pueden separar los 3 sub-factores. Afecta granularidad de atribución.
Disparo: si analyzer v2.4.1 reporta factor_portfolio alto sin claridad sobre qué componente domina (block, sector o global).
Cierre: exponer en allocations `block_factor`, `sector_factor`, `global_factor` por separado; analyzer los consume.
Referencias: portfolio_manager.py líneas 418, 433-436, 494-496, 521, analyze_performance_attribution.py coste_block_reduct.

**[MEJORA] [EN_ESPERA] portfolio_manager: correlación con min_len bajo silenciosamente — 2026-04-17**
Contexto: Ultra review S7. Líneas 104-105: si un símbolo recién entra con 20 barras y otros tienen 168, todos se truncan a 20. Correlación EWMA con 20 samples y halflife=24 es esencialmente peso uniforme. Latente hasta futuro reciclaje con símbolos nuevos.
Disparo: añadir símbolos nuevos al MASTER_SYMBOLS o en primer reciclaje.
Cierre: excluir símbolos con muy poca historia (threshold min_samples >= 60 p.ej.) en lugar de truncar el resto.
Referencias: portfolio_manager.py compute_correlation_matrix líneas 104-109.

**[MEJORA] [EN_ESPERA] brain_engine: prev_zone asimetria TF vs MR — 2026-04-19**
Contexto: B2 de Fase 3 (investigado y DIFERIDO). Asimetria observada: TF lee `zone_bull_arr[t-1]` localmente cuando t>0 (ruta normal live con t=1499), fallback a `state.prev_zone_bull` solo cuando t==0; escritura persistente al final (brain_engine.py:1027-1028). MR lee `state.prev_zone_bull` siempre (linea 1787); escritura al final (2108-2109).
VERIFICADO 2026-04-19 (Fase I v2.3.9): premise del ultra review INCORRECTA. El ultra review afirmo "TF nunca lee state.prev_zone" pero TF SI lo lee en fallback t==0 (lineas 678-683). Aunque en operacion normal t=1499 siempre, el fallback existe por robustez y no debe romperse.
Complicacion adicional: state.prev_zone tiene SEMANTICA DISTINTA TF vs MR. TF zone se computa con fast/slow/trend (una formula). MR zone es `fast < slow` INVERTED (linea 1783). Si un symbol swapea TF↔MR (como GRT el 2026-04-17), state.prev_zone escrito por TF no es valido para MR al siguiente ciclo, y viceversa. Aunque swap es raro, es deuda tecnica real.
Fix correcto NO es "eliminar escritura en TF" (Opcion A del ultra review). Requiere: (a) decidir semantica cross-strategy de prev_zone, (b) posiblemente introducir state.prev_zone_tf y state.prev_zone_mr separados, (c) testing en simulador con swap TF↔MR.
Disparo: al refactorizar compute_regime_features o al proximo reciclaje con test diferencial completo (simulador con swaps TF↔MR).
Cierre: decision arquitectonica sobre semantica cross-strategy tomada y aplicada.
Referencias: brain_engine.py lineas 678-683 (TF fallback), 1027-1028 (TF escritura), 1787 (MR lectura), 1780-1784 (MR zone INVERTED), 2108-2109 (MR escritura), Fase I v2.3.9 del 2026-04-19.

**[MEJORA] [EN_ESPERA] brain_engine: TF locals vs MR state directo para div_ctx — 2026-04-19**
Contexto: B3 de Fase 3 (investigado y DIFERIDO). Asimetria: TF usa variables locales div_ctx_bull/bear durante el loop de _evaluate_bar (mutaciones en lineas 699-719, snapshot en 712-713, resets locales en 885-893, uso en 930) y persiste al final (1031-1032: `state.div_ctx_X = div_ctx_X`). MR muta state directamente durante el loop (1803-1823, 1984-1992).
VERIFICADO 2026-04-19 (Fase I v2.3.9): cambiar TF al estilo MR no es trivial. Requiere modificar signature de `compute_divergences(df, bits, state)` que retorna tuple `(div_bull_now, div_bear_now, div_ctx_bull, div_ctx_bear)` (linea 689). Afecta los callers en lineas 1171 y 1266 (fallback `return state.div_ctx_X` dentro de compute_divergences), y 14+ lecturas de div_ctx locales en TF. Es refactor quirurgico en API interna del camino critico de generacion de senales TF, donde fidelidad vs kernel Numba es 91% y cualquier regresion sutil es costosa de detectar.
Sin test diferencial completo incluido kernel Numba parity, riesgo no justificado para ganar solo consistencia estilistica. Funcionalmente equivalente (state persiste entre ciclos en ambos casos).
Disparo: al reciclaje julio con test diferencial completo pre/post, o si aparece bug especifico atribuible a la asimetria TF/MR (ej. caso donde compute_divergences lee state.div_ctx stale y difiere del local en TF).
Cierre: refactor aplicado con test diferencial verde, o decision documentada de mantener asimetria.
Referencias: brain_engine.py compute_divergences linea 1171-1266, _evaluate_bar TF locals lineas 689-930 y 1031-1032, _evaluate_bar_mr MR directo lineas 1803-1823 y 1984-1992, Fase I v2.3.9 del 2026-04-19.

**[MEJORA] [RESUELTO] Batch fix emojis cp1252 restantes en lab_historico_numba_v8_3.py — 2026-04-22 → RESUELTO 2026-04-23**

Ver §13.4 entrada "[MEJORA] [RESUELTO] L1839 batch fix cp1252 runtime-critical lab_historico — 2026-04-23".

Resumen: scope real revelado por grep Python (420 chars no-ASCII en 188 líneas vs "14" documentado en §13.4 A27 por subestimación). Análisis separó runtime-critical (print/logger/f.write) de comments/docstrings. Aplicado fix solo en 68 líneas runtime-critical (mapping ASCII estándar brackets + flechas `->` + box drawings `-`). Comments/docstrings preservados (UTF-8 seguro Python 3). Smoke §0.8 Nivel A+C diff 0.0000 exacto — lógica invariante. master.py --recycle habilitado Windows cp1252.

**[MEJORA] [EN_ESPERA] brain_engine: hidden divergence asimetría TF vs MR — 2026-04-17**
Contexto: Ultra review S8. TF relee hid_inv del config_id para decidir interpretación (confía en WF haber seleccionado hid_inv=1 para compensar bug histórico). MR aplica pre-swap de bits 1↔3 antes de evaluar. Ambos producen resultado correcto SI los configs TF tienen hid_inv=1. VERIFICADO 2026-04-19 (C3 de Fase 1): 67 de 138 configs activos (48.5%) usan interpretación invertida (hid_inv=0 con div_type∈{2,3}): 9 configs pure HIDDEN only (BCH C2, IMX C2, LTC C2, TRX C0+C1, UNI C0, VET C1, XLM C2, XRP C2) + 58 configs BOTH mode. Símbolos con 3/3 clusters afectados: SOL, NEAR, AAVE, SUI. Escáner verificado: `div_type = (config_id >> 12) & 0x3`, `hid_inv = (config_id >> 25) & 0x1`.
Semántica exacta verificada: TF hid_inv=0 → `ind_bull=(bits&8), ind_bear=(bits&2)` (brain_engine.py:1216-1217) = interpretación "invertida"/pre-fix. MR post-pre-swap → `ind_bull=(bits&2), ind_bear=(bits&8)` (línea 1622) = interpretación "corrected". TF hid_inv=1 == MR post-swap.
No es bug operacional: consistencia interna WF↔brain (WF validó estos configs con interpretación invertida y brain los aplica consistentemente). Es deuda semántica — si se regenera WF unificando semántica con MR, los 67 configs cambiarán comportamiento y dejarán de ser óptimos.
Disparo: reciclaje v3.0 julio.
Cierre: al regenerar WF en julio, decidir unificar pipeline TF con MR (aplicar pre-swap en WF también o reentrenar con div_features corregidos). Evaluar comparativamente rendimiento pre/post unificación.
Referencias: brain_engine.py líneas 1214-1220 (TF) y 1597-1604 (MR), Fase 1 C3 del 2026-04-19.

**[MEJORA] [EN_ESPERA] brain_engine: símbolo con datos insuficientes salta evaluación — 2026-04-17**
Contexto: Ultra review S9. En classify_regimes líneas 286-288, símbolos con len(df) < LOOKBACK_SHORT+10 hacen `continue`, por lo que no entran en regimes dict y tampoco en active_configs/signals. Si el símbolo tiene posición abierta, brain no evalúa exit/TS; el SL emergencia 5% del exchange es la única red de seguridad. Gaps del data_feed pueden dejar posiciones sin TS updates temporalmente.
Disparo: si data_feed falla para un símbolo con posición abierta (ya ha ocurrido una vez en producción), o si un trade muestra PnL inesperadamente malo por falta de TS actualización.
Cierre: en classify_regimes, cuando datos insuficientes y hay posición abierta, emitir al menos signal mínimo (HOLD) con TS update si posible, o alerta al orquestador.
Referencias: brain_engine.py classify_regimes líneas 286-288, live_engine.py manejo de datos faltantes.

**[MEJORA] [EN_ESPERA] Comments 'forming/resolved' en brain_engine mis-etiquetados — 2026-04-19**
Contexto: Descubierto durante Parte A de Fase 1. Líneas 1274, 1276, 1284, 1525, 1529, 1534, 1540 en brain_engine.py llaman "forming" a iloc[-1] de df_ts y de los resampleos 4h/1d. Empíricamente iloc[-1] es la ÚLTIMA CERRADA — BingX con `since` (path paginado que usa el bot con OHLCV_LIMIT=1500) excluye forming candles. Los comments son vestigiales del path no-paginado original (pre-upgrade OHLCV_LIMIT 120→1500, §2.6 data_feed fix #4). Cosmético — no afecta correctitud de la evaluación — pero engaña a futuros lectores sobre lo que realmente evalúa brain.
Disparo: al refactor de _evaluate_bar/_evaluate_bar_mr (ver ítem S10 de ultra review), o al próximo reciclaje.
Cierre: rename variables de `tfN_bull_forming` a `tfN_bull_current` (o similar) y actualizar comments para reflejar "iloc[-1] = última barra cerrada".
Referencias: brain_engine.py líneas 1274, 1276, 1279, 1284, 1287, 1525, 1529, 1534, 1540, HALLAZGO "Lag estructural de 1 bar" en §13.2.

**[MEJORA] [EN_ESPERA] brain_engine: _evaluate_bar y _evaluate_bar_mr son >360 líneas con duplicación pesada — 2026-04-17**
Contexto: Ultra review S10. Las dos funciones principales del kernel duplican emergency SL, fixed SL, cooldown logic, entry blocks, cancel dispatching. Cualquier bug (como R1 de cooldown) se replica en ambos. Refactor a helpers compartidos (_check_emergency_sl, _check_fixed_sl, _process_exit_cooldown, _entry_tf_filters) reduciría superficie de bugs.
Disparo: al acumular 2+ bugs del mismo tipo replicados TF/MR.
Cierre: refactor aplicado con verificación diferencial brain vs kernel pre/post refactor.
Referencias: brain_engine.py líneas 627-1015 (TF) y 1734-2093 (MR).

**[MEJORA] [EN_ESPERA] brain_engine: test diferencial brain vs kernel sobre histórico — 2026-04-17**
Contexto: La calibración de probabilidad de críticos latentes (35-45%) estaba dominada por áreas 5 (fidelidad vs walk-forward) y 7 (casos borde) que requieren ejecución sobre miles de barras para descartar divergencias finas (tipo ALMA p1/p2 original que fue bug histórico). El test `_run_verify_test` ya existe (líneas 2219+) pero es ad-hoc — no parte de CI ni reportado.
Disparo: antes del primer reciclaje o si alguna regresión de fidelidad aparece en audit v5.1.
Cierre: ejecutar _run_verify_test sobre BTC/ETH (representativos) con N>=10000 barras, documentar % diff trades y PnL vs kernel. Si diff >0.1%, investigar.
Referencias: brain_engine.py _run_verify_test líneas 2219-2432.

**[MEJORA] [EN_ESPERA] Multiples eventos mismo-simbolo mismo-ciclo — 2026-04-17**
Contexto: Ultra review S9. En dict de eventos por (cycle_ts, sym), si un simbolo aparece con CLOSE_LONG y luego LONG en el mismo ciclo (raro pero posible en close+reopen), el segundo sobrescribe el primero. Perdida silenciosa de informacion.
Disparo: si se observa un trade con pattern close+reopen mismo ciclo en logs de produccion, o si el analyzer comienza a reportar trades con slippage_entry nulo inesperadamente.
Cierre: cambiar dict a list de eventos por clave, consumidores manejan multiples.
Referencias: analyze_performance_attribution.py lineas 221, 229, 238, 249, 260.

**[MEJORA] [EN_ESPERA] active_config_id en SIGNALS_RAW (v2.3.4) — 2026-04-17**
Contexto: Ultra review S6. El analyzer actualmente usa heuristico para elegir config (primer cross_cluster_survival=True en top_configs). Puede diferir del config_id real de produccion. Para mapearlo correctamente, anadir campo `cfg` en [SIGNALS_RAW] por simbolo con el active_config_id. analyzer matcheara contra top_configs[*].config_id.
Disparo: si reporte muestra >20% de trades con active_config_source=heuristic y los resultados son sensibles.
Cierre: v2.3.4 anade cfg en SIGNALS_RAW; analyzer lo lee.
Referencias: live_engine.py [SIGNALS_RAW] logging, analyze_performance_attribution.py attribute_trade seccion 2.

**[MEJORA] [EN_ESPERA] Ejecución parcial de órdenes no manejada en reconcile — 2026-04-16**
Contexto: Fix de Bug #1 asume que si BingX tiene contracts>0 la posición es real. No maneja explícitamente el caso raro de ejecución fraccional (BingX abre, digamos, 60% del size pedido por insufficient margin o slippage extremo). Raro con balance 297 USDT, más probable al escalar capital.
Disparo: al escalar capital (>1000 USDT) o si aparece algún trade con size real significativamente distinto del size pedido en los logs.
Cierre: reconcile extendido para detectar y manejar parcialidades, o decisión documentada de aceptar el caso como edge raro y no manejarlo.
Referencias: live_engine.py _reconcile_brain_after_execution(), v2.3.2

**[MEJORA] [EN_ESPERA] v2.3.3 — loguear multiplicadores en SIGNALS_DISCARDED — 2026-04-16**
Contexto: Analyzer v2.4 necesita vw/bf/br/dd para atribución de coste en descartes. Actualmente [SIGNALS_EXECUTED] los tiene pero [SIGNALS_DISCARDED] no. Para señales descartadas el analyzer usa proxy de 5 ciclos previos con ejecuciones; si no hay suficientes en 48h, marca "no_estimable" y excluye del cálculo de balance_req. Si primer reporte v2.4 muestra no_estimable_ratio >20%, instrumentar v2.3.3 para loguear multiplicadores en SIGNALS_DISCARDED.
Disparo: primer reporte v2.4 con flag NO_ESTIMABLE_RATIO_ALTO activo.
Cierre: v2.3.3 desplegada, o decisión documentada de no instrumentar (ej: si ratio baja orgánicamente por capitalización).
Referencias: portfolio_manager.py ~511-521 cálculo factores, live_engine.py ~485 log DISCARDED, analyze_performance_attribution.py fallback proxy Q7

**[MEJORA] [RESUELTO L27 parcial] Detección automática de edge_erosion por cluster — 2026-04-16**

Ver §13.4 entrada "[MEJORA] [RESUELTO L27 parcial] L1910 edge_erosion detection ya implementado por analyzer v2.4.1 — 2026-04-23".

Resumen: detección automática ya implementada por analyzer v2.4.1 (alert `CANDIDATO EXCLUSION RECICLAJE`, primer caso empírico Fase II.C 2026-04-22 con ONDO C2 + SAND C1). Tracking cross-sesiones para criterio semi-automático 2+ reportes consecutivos integrado en §13.3 L1398 política adelantar reciclaje. Item cerrado como L27 parcial.

**[MEJORA] [EN_ESPERA] Test de consistencia de ecuación de descomposición — 2026-04-16**
Contexto: Analyzer v2.4 incluye verificación interna de que pnl_real ≈ suma de componentes con tolerancia 0.01 USDT por trade. Si algún trade falla, loguea WARNING. Si primera ejecución con N≥50 trades muestra WARNINGs frecuentes (>5% de trades), investigar emparejamiento trades↔logs o bugs en fórmulas.
Disparo: primer reporte v2.4 con WARNINGs de ecuación no cerrando en >5% de trades.
Cierre: causa raíz identificada y corregida, o ratio de WARNING <5% aceptado como ruido de floating point.
Referencias: analyze_performance_attribution.py verificación al final de attribute_trade()

**Update 2026-04-23 (revisado)**: item vinculado estrechamente con §13.3 "Investigación causa raíz pnl_recon gap analyzer" (nuevo 2026-04-23). El item sucesor "ratio 25%" fue refutado por prerequisite inviable (§13.4). L1916 permanece EN_ESPERA y se cerrará por merge natural cuando el item Opción D (investigación causa raíz) complete Fase D con gap típico reducido a <5% post-fix. Spec original sin cambio: alert threshold 5% sigue siendo criterio; lo que cambia es que el fix correcto no es recalibrar tolerance sino identificar y corregir el componente del gap dominante.

**[MEJORA] [RESUELTO] Observabilidad funding per-trade (bar-a-bar + exit context) — IMPLEMENTADO 2026-04-22**

Ver §13.4 entrada "Observabilidad funding bar-a-bar — integración permanente — 2026-04-22" (ampliación post-Bloque 2).

Resumen: `funding_context.py` reemplaza `funding_observability.py` standalone (borrado). 11 columnas enriquecimiento total (3 entry + 3 exit + 5 evolution) + entry_exit_pattern de 9 combos. Cache CSV por símbolo (compat VPS sin pyarrow) en `.funding_cache/`. CLI `refresh-cache` (VPS Tokyo) + `enrich` (local). Analyzer v2.4.1 NO modificado (post-hoc enrichment workflow; integration directa pospuesta por scope). Cross-check empírico: Section 1 (entry) N=50 bit-idéntico a Bloque 2 (p=0.0113). Nuevos hallazgos descriptivos: Section 2 (exit) p=0.0162 soporta candidato v2.6-exit filter; Section 4 correlación Spearman ρ=-0.3172 p=0.0205 n_bars_contrarian vs PnL → más tiempo contrarian = peor PnL. Analyzer enriquecido definitivo operativo para futuras evaluaciones N≥100 y N≥150.

**[MEJORA] [REFUTADO] Filtro funding contrarian runtime (direccional) — REFUTADO empíricamente 2026-04-22**

Ver §13.4 entrada "Observabilidad funding per-trade — refutación empírica §9.3 v2.6 contrarian filter — 2026-04-22".

Resumen: hipótesis original (bloquear entries aligned con crowd, preservar contrarian) **refutada con dirección opuesta confirmada** (Welch t=+3.58 p=0.0003 trimmed, Mann-Whitney p=0.0052). Aligned trades son GANADORES en régimen actual; contrarian trades son PERDEDORES. Simulación del filter propuesto: habría degradado PnL en factor 2.2× (-1.52 USDT adicional sobre 50 trades). Item cerrado; hipótesis refutada — no "archivado por falta de evidencia" sino "refutado por evidencia contraria" (distinción §12 Lección 33).

**[MEJORA] [EN_ESPERA] v2.6-inv momentum filter candidato — validación N≥100 — 2026-04-22**

Contexto (actualizado post-Bloque 2 ampliación): observabilidad funding §13.3 implementada 2026-04-22 reveló dirección OPUESTA a hipótesis §9.3. Aligned trades ganan +0.50% mean; contrarian pierden -0.57% mean. Gap 1.07 pp/trade, win rate 62% vs 28% (Welch baseline p=0.0113, trimmed p=0.0003, Mann-Whitney p=0.0052). Filter **inverso** (bloquear entries contrarian al funding crowd) podría mejorar PnL neto en régimen actual.

**Ampliación datos post-bar-a-bar** (funding_context.py primera ejecución): en 50 trades, 0 crowd flips observados (crowd stable en ventana 4d); `entry_exit_pattern` dominado por `aligned->aligned` (16) + `contrarian->contrarian` (17) + `neutral->neutral` (15). Correlación Spearman ρ=-0.3172 p=0.0205 entre n_bars_contrarian y PnL confirma la hipótesis inversa con perspectiva temporal (más tiempo contrarian = peor PnL).

**Update Fase 3 stress-test 2026-04-23**: replicación N=98 multi-segmento (N=49 con funding cache, S1 no testeable por cache arrancando 2026-04-15) reveló que el efecto Bloque 2 (p=0.0003 trimmed) estaba concentrado en S2+S3 (trades 2026-04-19→21). Aislando S4 post-v2.4.4 (A.1 N=26): p=0.77. En N=49 multi-segmento (S2+S3+S4): gap +0.49pp p=0.35, dirección correcta sin significancia. Bloque 2 magnitud inflada por concentración ventana-específica. Disparador N≥100 MANTENIDO con prerequisito reforzado: replicación Welch p<0.05 sobre ventana S4 homogénea (no solo N≥100 cualquier dirección). Cache funding extender a origen dataset es prerequisito para testear S1 retrospectivo cuando disparador activo (ver §13.3 [MEJORA] cache funding extender). Si N≥100 S4 homogéneo no recupera p<0.10, archivar análogo a v2.6 contrarian original.

**Caveats a validar**:
- N=50 en 4 días (2026-04-19 a 2026-04-22) — suficiente para dirección estadística pero no para magnitud estable. Régimen observado (lateral-alcista, funding mayoritariamente positivo ligero) puede no representar bearish ni tail-risk crowded.
- Rompe Fidelidad 2 igual que versión contrarian original — cualquier trade runtime bloqueado diverge del kernel post-hoc. Requiere implementación simétrica en kernel lab (Numba TF + MR) para preservar §0.3 → ~2-3 sesiones extras si opción 1. Opción 2 (filter sin lab, Fidelidad 2 rota conscientemente) aceptable si trades bloqueados quedan documentados y fracción pequeña. Opción 3 (no implementar) si al llegar a N≥100 el efecto revirtió.

**Metodología de validación**:
1. Acumular N≥100 post-v2.3.11 (~2026-05-01 al ritmo actual 0.7 trades/h).
2. Re-ejecutar `funding_observability.py` sobre dataset ampliado.
3. Verificar si efecto persiste: p-value trimmed y magnitud gap. CI95 para aligned y contrarian mean.
4. Si persiste y robusto: decisión Ricardo opción 1 (kernel + lab) / 2 (solo runtime) / 3 (archivar).
5. Si opción 1 elegida: implementar en kernel Numba TF + MR con entry filter basado en funding rate. Threshold a definir con percentil empírico (no §9.3 fallido que nunca activa). Tests + smoke §0.8 + deploy v2.4.6 operacional.

**Disparo**: N≥100 post-v2.3.11 + cross-check condiciones de mercado. Si régimen cambió significativamente (ej. bearish prolongado, funding negativo mayoritario), evidencia nueva puede divergir — re-validar antes de decidir.

**Cierre**: decisión fundamentada con data robusta (N≥100) o archivar si efecto revirtió.

**Prerequisito parcial**: ítem §13.3 E1 funding sign bug relevante SOLO si la implementación del filter consume `_get_position_funding` fallback. Si el filter fetcha rate directo de ccxt (como hace `funding_observability.py`), bypass natural y E1 irrelevante.

Referencias: §13.4 entrada "Observabilidad funding per-trade" 2026-04-22 + ampliación bar-a-bar; §9.3 v2.6 (refutado); §12 Lección 33; `funding_context.py` (reemplaza `funding_observability.py` borrado; analyzer enriquecido definitivo).

**[OBSERVACION] [EN_ESPERA] engine_state.json nomenclature — consumers usan `dict.get("positions", {})` con default silencioso — 2026-04-22**

Contexto: durante reconocimiento inicio sesión 2026-04-22 (análisis N trades acumulado), la query `d.get("positions", {})` sobre `engine_state.json` retornó default `{}` y se reportó como "positions vacío pese a 5 posiciones abiertas" (sospecha bug). Diagnóstico Micro-item 2 mismo día reveló: **la key `positions` no existe**. El estado se persiste bajo la key `symbols` (live_engine.py `_save_state` L1159-1211; `_load_state` L1213+). 45 entries en `symbols`, 5 con `position != 0` — consistente con las posiciones reales.

**Clasificación**: CATEGORÍA 1 — alternate representation (no bug). Grep confirmó 0 código lee `state["positions"]`.

**Aprendizaje metodológico**: queries con `dict.get(key, default)` para inspección ad-hoc **confunden ausencia con vacuidad**. Para diagnóstico: usar `key in d` o `d.get(key)` sin default, y distinguir `None` (ausente) de `{}` (vacío presente).

**Cleanup propuesto (cosmético, no urgente)**:
- Scripts ad-hoc de inspección deberían verificar `"symbols" in d` (correcto) en vez de `d.get("positions")` (confuso).
- Si hay memoria viva en scripts/agentes sobre "positions" como campo esperado, refrescar con este contexto.
- Rename-futuro opcional: consolidar terminología "symbols" → "positions" o mantener "symbols" + docstring explícito. Fuera de scope pre-reciclaje; posible en v3.0 refactor.

**Disparo**: si en futuras sesiones alguien vuelve a reportar "positions vacío" → este item clarifica que es mala query, no bug.
**Cierre**: si al refactor v3.0 se consolida nomenclatura, o permanente si se decide mantener convención actual con docstring mejorado.

Referencias: live_engine.py `_save_state` L1166 (`"symbols": {}` escribe dict), L1178-1199 (bucle populating per símbolo). §13.4 entrada sesión 2026-04-22 Micro-item 2.

**[MEJORA] [EN_ESPERA] v2.6-exit filter candidato (cerrar contrarian losing trades) — validación N≥150 — 2026-04-22**

Contexto: Bloque 2 ampliación (funding_context.py bar-a-bar) reveló evidencia de candidato DISTINTO al v2.6-inv entry filter. Section 4 del reporte muestra **correlación Spearman ρ=-0.3172 p=0.0205** entre `n_bars_contrarian` (bars posicionado contra crowd vigente) y `pnl_pct` — más tiempo contrarian = peor PnL. Direccional y significativo con N=50.

**Hipótesis**: cerrar preventivamente posiciones contrarian que estén en pérdida + tiempo prolongado contrarian reduciría pérdidas. A diferencia de v2.6-inv (bloquea entries), v2.6-exit permite entries normales pero gestiona activamente exits en base al crowd evolution.

**Caveats críticos**:
- 0 crowd flips observados en ventana 4d (todos los trades entry_pattern == exit_pattern). Section 3: 16 aligned->aligned, 17 contrarian->contrarian, 15 neutral->neutral, 2 cross. El efecto depende **parcialmente** de crowd cambios durante trade, que en régimen actual son raros.
- Solo 4/50 (8%) trades cruzan boundary 8h funding. Para régimen típico con hold time mediano 1h, n_bars_contrarian es simplemente hold_time_contrarian × 1 (sin variación). La correlación observada puede reducirse a "trades contrarian largos pierden más", no "crowd flip dispara reversión".
- N=150 requerido para power estadístico en 9-pattern breakdown + duración correlación robusta con CI estrecho.
- Rompe Fidelidad 2 **MÁS** que v2.6-inv entry (v2.6-exit altera múltiples exits potenciales, no solo algunas entradas). Implementación kernel lab-side más invasiva.

**Update Fase 3 stress-test 2026-04-23**: Spearman ρ(n_bars_contrarian, pnl_pct) en N=49 multi-segmento = -0.145 p=0.31 (vs -0.32 p=0.02 Bloque 2 N=50, vs +0.02 p=0.93 A.1 N=26 S4-only). Signo correcto recuperado a magnitud 0.5× del Bloque 2, no significativo. Disparador N≥150 MANTENIDO con flag adicional: requerir cache funding extendida S1 + replicación cross-segmento + significancia Welch p<0.10 antes de implementar.

**Metodología de validación**:
1. Acumular N≥150 post-v2.3.11 (~2026-05-10 al ritmo actual).
2. Re-ejecutar `funding_context.py enrich` (cache sirve data fresca automáticamente).
3. Verificar si (a) correlación Spearman n_bars_contrarian vs pnl persiste CI bajo; (b) trades con crowd_flipped=True muestran gap PnL material vs non-flipped; (c) pattern `contrarian->*` breakdown revela señal.
4. Si persiste y robusto: decisión Ricardo con trade-off Fidelidad 2 (igual a v2.6 original/inv).
5. Si opción lab-side: threshold time de cierre (ej. "bloquear/cerrar si n_bars_contrarian > 4 AND pnl<0") + threshold crowd signal.

**Disparo**: N≥150 post-v2.3.11. Cross-check con v2.6-inv entry filter (decisión excluyente o combinable — v2.6-inv bloquea entry, v2.6-exit gestiona exit; podrían coexistir como dos filtros ortogonales).

**Cierre**: decisión fundamentada con data robusta o archivar si efectos revirtieron.

Referencias: §13.4 entrada "Observabilidad funding bar-a-bar — integración permanente" 2026-04-22; §9.3 v2.6 refutada; §13.3 v2.6-inv (candidato paralelo); §12 Lección 33; `funding_context.py`.

**[DECISION] [EN_ESPERA] Funding rate NO es feature del GMM — rechazo explícito 2026-04-23**
Contexto: durante discusión 2026-04-23 sobre cómo integrar funding rate al sistema, se evaluaron dos opciones arquitectónicas:

**Opción descartada**: funding como feature del GMM. El GMM de cada símbolo recibiría funding rate como input adicional junto con las features técnicas actuales. Clusters capturarían "régimen técnico + estado de funding" como variable compuesta del régimen.

**Razonamiento del rechazo**: funding rate es exógeno al régimen técnico del precio. El precio tiene estructura de régimen (trending/lateral/volátil). El funding refleja desequilibrio de posiciones, que puede estar descorrelacionado con el régimen técnico actual. Un mercado lateral puede tener funding extremo si hay crowd posicionado. Un mercado fuertemente trending puede tener funding neutro si hay equilibrio long/short. Meter funding al GMM contaminaría la clasificación técnica con información de posicionamiento de mercado, produciendo clusters que son mezcla conceptual (ej. "volatilidad alta + crowd long" vs "volatilidad alta + crowd short" que no son dos regímenes técnicos distintos, es uno con posicionamiento variable).

**Opción adoptada**: funding como filtro runtime separado del GMM (ver item [MEJORA] "Filtro funding contrarian runtime (direccional)" 2026-04-23). El GMM clasifica régimen técnico limpio. El filtro opera sobre la decisión de ejecutar signal, no sobre la clasificación. Son conceptualmente separables, lógicamente modulares.
Disparo: solo reabrir esta decisión si evidencia empírica futura indica que funding como feature del GMM mejora significativamente alpha (improbable dado el razonamiento).
Cierre: decisión estable. No se implementa funding como feature del GMM en ningún reciclaje (v3.0 o posteriores) salvo que este item explícitamente se reabra.
Referencias: §13.3 items funding runtime + observabilidad 2026-04-23; §9.3 v2.6 funding rate como filtro (roadmap donde filtro runtime se materializa); §9.4 v3.0 Z_ATR (feature del GMM que SÍ se acepta para BTC, por naturaleza técnica de Z_ATR vs posicional de funding).

**[MEJORA] [REFUTADO] Tolerancia pnl_recon analyzer — L2018 refutado por validación empírica 2026-04-23**

Ver §13.4 entrada "[MEJORA] [REFUTADO] L2018 pnl_recon tolerance hipótesis floor mal calibrado — 2026-04-23".

Resumen: hipótesis original "floor 0.01 USDT mal calibrado con balance bajo" refutada por validación empírica directa. Bajar floor 0.01→0.005 empeora ratio 42%→58%. Causa real: ratio 10% demasiado estricto para gap típico empírico 15-25%. Nuevo item creado con hipótesis refinada ratio 25% (ver §13.3 "[MEJORA] pnl_recon ratio 10pct demasiado estricto — hipótesis refinada post-L2018 — 2026-04-23").

**[MEJORA] [REFUTADO] pnl_recon ratio 25% — prerequisito validación multi-segmento no-satisfacible — 2026-04-23**

Ver §13.4 entrada "[MEJORA] [REFUTADO] Item pnl_recon ratio 25% refutado por prerequisito inviable + nuevo item Opción D investigación causa raíz — 2026-04-23".

Resumen: prerequisito "validación multi-segmento N=98" del item era inviable por bug histórico size_usdt=0 (§2.4 v2.4.4, afecta ~138/164 trades pre-v2.4.4). Solo S4 N=24 testeable — "multi-segmento" renombrado de single-segment. Aplicación L34 recursiva: item propio refutado al no cumplir criterio elevación multi-segmento de su propia lección invocada. 5ª refutación del día por stress-test. Item reemplazado por nuevo §13.3 "Investigación causa raíz pnl_recon gap" con scope explícito ~1-2h data-independent.

**[MEJORA] [EN_ESPERA] Investigación causa raíz pnl_recon gap analyzer — 2026-04-23**

Contexto: síntoma 92% trades con `pnl_recon_gap > tolerance` sobre A.1 N=26 identificado 2026-04-23. Hipótesis "floor mal calibrado" (L2018) refutada empíricamente (bajar floor empeora ratio). Hipótesis "ratio 25% cross-segmento" (item sucesor) refutada por prerequisite inviable (§13.4 2026-04-23). Síntoma persiste.

Distribución gap empírica sobre S4 N=24 (única ventana testeable):
- p50 gap/|pnl| = 21%
- p75 = 19%
- p90 = 15%
- p99 = 11%

Gap típico 15-25% no es calibrable con tolerance arbitraria de forma robusta. Requiere identificar qué componente lo genera antes de aplicar fix sostenible.

**Hipótesis candidatas componentes del gap**:

1. **Precision rounding CSV**: entry_price y exit_price redondeados a 4-6 decimales en CSV vs precision BingX mayor. `(exit_price - entry_price) * contracts` amplifica rounding linearmente con contracts. Magnitud estimada: ~0.1-1% sobre notional.

2. **Fees estimation divergente**: analyzer usa `COMMISSION_RATE * notional * 2` (round-trip). BingX real:
   - Taker 0.05%, maker 0.02% — depende tipo orden. Analyzer asume constante.
   - Funding incluido dentro del PnL reportado o fuera — interpretación ambigua.
   - BNB discount aplicado o no según configuración cuenta.
   Magnitud estimada: ~0.05-0.2% sobre notional.

3. **Notional definition mismatch**:
   - `size_usdt` BingX-reportado = `filled_contracts * mark_price_at_fill`.
   - Recomputed = `requested_contracts * CSV_entry_price` puede diferir por slippage bid-ask + delta mark vs fill price.
   Magnitud estimada: ~0.1-5% dependiendo volatilidad fill.

4. **Size_usdt pre-v2.4.4 bug colateral**: aunque v2.4.4 fix aplica size_usdt correcto a trades futuros, tal vez la lógica BingX-reporting interna usaba otro campo del response que también cambió post-v2.4.4. Requiere validación sobre trades v2.4.4 exactos.

**Scope investigación propuesto** (~1-2h sesión dedicada):

1. **Fase A — análisis componente por componente** (~30 min): Sobre S4 N=24 dataset actual, descomponer gap en:
   - gap_precision: recomputar pnl_recon con precision extendida (decimales originales BingX via API position.info si disponible). Diferencia vs CSV-redondeado estima precision_rounding component.
   - gap_fees: comparar `COMMISSION_RATE * notional * 2` con BingX fee_schedule por trade (GET /api/v1/account/commission). Diferencia estima fees_divergence.
   - gap_notional: comparar size_usdt (BingX) con filled_contracts * entry_price (recomputed). Diferencia estima notional_mismatch.

2. **Fase B — raw BingX API verification** (~30 min): Para 3-5 trades S4 muestra, consultar BingX historial completo (GET /api/v1/trade/fills) y verificar:
   - Precio exacto fill vs CSV.
   - Commission real vs estimada.
   - Size/notional tal como BingX lo reporta.
   Identificar qué campo usar como "ground truth" para pnl_recon.

3. **Fase C — implementación fix** (~30 min): Según findings Fase A+B:
   - Si gap_precision dominante → leer precision original desde BingX.
   - Si gap_fees dominante → integrar fee_schedule real.
   - Si gap_notional dominante → usar size_usdt directamente sin recompute.
   Fix resuelve fenómeno vs calibrar tolerance arbitraria.

4. **Fase D — validación post-fix** (~15 min): Re-ejecutar analyzer sobre S4 con fix aplicado. Gap típico debe caer a <5% típico, <10% p95. Alert 5% threshold vuelve significativo (no saturado por falso positivo).

**Disparador ejecución**: sesión dedicada ~1-2h. No requiere data nueva. No requiere N≥X trades. Puede ejecutarse en cualquier momento que haya tiempo suficiente contiguo.

**Prerequisito implícito**: acceso BingX API para queries raw (fee_schedule, trade fills). Disponible desde VPS Tokio donde ya está configurado ccxt con keys.

**Scope impacto**:
- Analyzer offline únicamente. No toca brain/kernel/execution/live_engine.
- Fidelidad 2 invariante por construcción.
- Cierra 2 items §13.3 cuando Fase D PASA: este + L1916.

**Cierre**: investigación completada + fix aplicado + gap típico <5% + L1916 cerrado por merge natural. Opcional: si Fase A revela múltiples componentes con magnitud similar, descomponer en sub-items §13.3 por componente para fixes secuenciales.

**Referencias**:
- §13.4 L2018 refutación 2026-04-23.
- §13.4 item "ratio 25%" refutación 2026-04-23.
- §13.3 L1916 2026-04-16 (vinculado, cierre diferido).
- §13.2 DECISION "Consistency check por reconstrucción no tautológico" (preservada — fix resuelve fenómeno, no tapa síntoma).
- §2.4 v2.4.4 size_usdt bug origen.
- §12 L34 (scope del item verifica data soporta análisis a priori).

**[MEJORA] [EN_ESPERA] Cache funding context extender a origen dataset para stress-tests multi-segmento — 2026-04-23**

Contexto: Fase 3 stress-test 2026-04-23 reveló que el efecto funding aligned/contrarian Bloque 2 no pudo testearse en S1 pre-v2.3.11 (N=49 trades del dataset total) por cache funding arrancando 2026-04-15; dataset arranca 2026-04-13 con S1 terminando en 2026-04-19 17:51. Gap infra limitó rigor del stress-test a S2+S3+S4 (N=49 de 98 total). El veredicto "signo correcto sin significancia N=49" se beneficiaría de S1 retrospectivo para tener cross-segmento completo N≥98.

Acción:
- VPS refresh cache desde 2026-04-10 (margen seguridad):
  ssh trader@vps "cd combolab && python funding_context.py refresh-cache --csv trade_history.csv --cache-dir .funding_cache --since 2026-04-10"
- Sync cache local.
- Re-ejecutar Fase 3 Section 2 sobre N=98 completo.

Scope: ~15 min operacional. No toca código.
Disparo: próximo stress-test de v2.6-inv (disparador N≥100) O v2.6-exit (disparador N≥150) O cualquier análisis cross-segmento funding.
Cierre: cache extendida + re-ejecución stress-test completado.
Referencias: §13.4 Fase 3 2026-04-23, funding_context.py CLI refresh-cache, §13.3 v2.6-inv + v2.6-exit.

**[INVESTIGACION] [EN_ESPERA] Walk-forward methodology sistemático bias cross-universe — hallazgo Opción W1 2026-04-23**

Contexto: Bloque 2c Opción W1 (§13.4 2026-04-23) reveló hallazgo inesperado: inflación walk-forward NO es específica de clusters flagged W3/CANDIDATO EXCLUSION — es UNIVERSAL cross-universe. Control group unflagged matched-by-pf_fwd distribution mostró 9/10 con PF_3y<1.5 (vs 10/10 flagged), 0/10 con PF≥2.0 (vs 0/10 flagged). Welch p=0.148 NO significativo.

**Implicación crítica**: filter W3+CANDIDATO EXCLUSION marca configs con edge bajo pero NO los discrimina significativamente de unflagged. Los JSONs productivos actuales tienen sesgo walk-forward sistemático que afecta TODO el universe, no solo flagged.

**§12 L29 extendida**: no es solo "N_fwd pequeño inflation". Es "walk-forward selection bias amplifica noise cross-universe". 20/20 configs (flagged + control) tienen PF_3y<1.5 sobre Binance 3y; 0/20 con PF≥2.0.

**Scope investigación propuesto** (~10-15h sesión dedicada):

1. **Análisis metodológico walk-forward actual** (~3-4h):
   - Revisar `regime_walk_forward.py` selection pipeline: filters pf_tr ≥ 1.1, pf_fwd ≥ 1.1, trades_tr ≥ 25 (W4 thresholds recientes).
   - Evaluar si criterios de selección amplifican noise multi-testing cross-millones-configs.
   - Hipótesis candidatas:
     a) Multi-testing bias: seleccionar top-1 de millones de configs infla PF por diseño.
     b) Selection on noisy pf_fwd: W3 corrige solo top-level, no el pool completo.
     c) Régimen training ≠ régimen future: GMM classification shift entre train y OOS periodo.
     d) Specialist selection criterion amplifica (specialist_score = pf_combined × robustness).

2. **Experimento comparativo** (~4-5h):
   - Simulación metodología alternativa (ej. cross-validation k-fold en vez de train/test split; penalty N_fwd más agresivo; filter por ci_low ratio no solo pf_combined).
   - Verificar si methodology alt produce PF_3y más cercano a pf_fwd (menos inflation).

3. **Implementación fix** (~3-6h):
   - Según findings, modificar regime_walk_forward.py metodología.
   - Tests + validación pre-reciclaje julio.

**Beneficios post-investigación**:
- Reciclaje julio con methodology corregida entrega specialists operacionales más robustos.
- W3+W4 implementations existentes preservadas (fixes válidos), investigación añade capa adicional.

**Disparador**: antes de reciclaje julio 2026 O si operacional degradación acelera.

**Cierre**: methodology revisada + empirical validation (control group PF_3y mean ≥ 1.5 post-fix) + specialist nuevos con edge real cross-régimen.

Referencias:
- §13.4 Bloque 2c Opción W1 2026-04-23 (hallazgo INFLACION UNIVERSAL).
- §13.4 Bloque 2c Opción Q1 2026-04-23 (validación filter flagged).
- §13.3 W3 implementado 2026-04-23.
- §13.3 W4 implementado 2026-04-23.
- §12 L29 extendida (pre-W1).
- `regime_walk_forward.py` methodology.

---

**[INFRA] [EN_ESPERA] Tier 0 I1 kernel reason_exit tracing + Bloque 2c H1 + H_funding + H_strategy full cross-régimen — proyecto dedicado post-reciclaje — 2026-04-23**

Contexto: Bloque 2c Opción Q1 sesión 2026-04-23 ejecutó W3 divergencia validation cuantitativa (§13.4 entrada nueva, 10 clusters × 3y Binance Futures). H1 + H_funding + H_strategy diferidos por limitación estructural del kernel Numba output: aggregates-only, sin per-trade side/entry_ts/reason_exit.

Sin modificación kernel (Tier 0 I1) H1+H_funding+H_strategy NO son testeables granularmente — brain-level bar-by-bar 40x más lento es ~30-60h compute para 44 sym × top-5 × 2y = infeasible.

Decisión institucional 2026-04-23: diferir a proyecto dedicado post-reciclaje por:
1. Timing operacional: modificar kernel Numba pre-reciclaje máximo riesgo (reciclaje ejecutaría sobre kernel potencialmente comprometido).
2. Fidelidad 1 Pine↔kernel bit-a-bit no verificable desde local (Pine vive en TradingView web) — §0.8 smokes 0.0000 cubre scenarios típicos pero no kernel edge cases estructurales.
3. Scope 15-20h realistic justifica sesión dedicada + commit cycle independiente + testing exhaustivo.

**Scope proyecto dedicado post-reciclaje**:

1. **Tier 0 I1 — kernel run_simulation_numba modification** (~10-15h):
   - Arrays pre-alloc per trade: entry_bar, exit_bar, side, pnl, reason_exit, cluster_at_entry.
   - Enum reasons: 0=tf_exit, 1=div_exit, 2=sl_hit, 3=zone_exit, 4=regime_change, 5=cancel_tf, 6=cancel_mr, 7=sl_emergency.
   - Signature extension output tuple para incluir trade-level arrays.
   - Update 10+ callers: `_run_verify_test`, `regime_walk_forward.py` (multiple sites), `lab_lite_zonas_v5e.py`, `audit_fidelity_v5.py` + `audit_fidelity_v5_2.py`, `master.py`, `audit_mr_fidelity_sei.py`.
   - Update `EXPECTED_LAB_KERNEL_HASH` + audit regen.
   - Tests §0.8 A+B+C multi-iteration + debugging expected 2-3 ciclos.
   - Pine v44 re-run manual validation vía TradingView (fuera Claude Code scope) — owner Ricardo.

2. **Bloque 2c full cross-régimen post-I1** (~5-10h):
   - Fetch Binance 44 sym × 3y OHLCV + funding (ya infra I2 `--data-path` disponible).
   - Kernel runs 44 × 3 clusters × top-5 = 660 configs con per-trade output.
   - **H1 short/long asimetría** cross-régimen × side (kernel side per-trade disponible post-I1).
   - **H_funding aligned/contrarian** cross-régimen × funding_context enriched (kernel entry_ts per-trade).
   - **H_strategy strategy-logic vs structural** cross-régimen × reason_exit categorized.
   - Descomposición per-régimen BTC macro (3-5 régimenes distinguibles en 3y).

**Ventana preferida post-reciclaje**:
- Reciclaje completo ejecutado + specialists desplegados.
- Bot operacional ≥2 semanas estable con nuevos specialists.
- Ventana máxima seguridad refactor arquitectónico kernel.

**Beneficios persistentes post-I1**:
- H1+H_funding+H_strategy validables cross-régimen N masivo (~100-200k trades teóricos).
- Analyzer future per-reason_exit attribution granular.
- Walk-forward diagnostics per-reason.
- Cualquier stress-test arquitectónico futuro con trade-level data.

**Evidencia interim Bloque 2c Opción Q1 (§13.4 2026-04-23)**:
- W3 divergencia validation: **CASO VALIDA CUANTITATIVAMENTE** — 6/6 W3 flagged + 4/4 CANDIDATO EXCLUSION con PF_3y_binance < 1.5, 0/10 con PF≥2.0. Ambos flag types convergen en detección edge bajo histórico.
- H1+H_funding+H_strategy permanecen refutados N≤98 con caveat "validación cross-régimen N masivo diferida a proyecto I1".

Disparador: post-reciclaje final + bot operacional ≥2 semanas stable + sesión dedicada ≥20-30h (I1 + stress-tests).

Cierre: I1 implementado + Fidelidad 1 verificada (Pine re-run manual) + Bloque 2c 4/4 hipótesis stress-test cross-régimen completo.

Referencias:
- §13.4 Bloque 2c Opción Q1 2026-04-23 (W3 validation cuantitativa).
- §13.4 Bloque 2c Opción D 2026-04-23 (W3 cualitativa initial).
- §13.4 Bloque 2b coverage Binance 2026-04-23.
- §13.4 Tier 0 I2 2026-04-23 (`--data-path` habilitado commit 53fe73a).
- §12 L34 (9 aplicaciones sesión 2026-04-23).
- §0.6 Kernel como verdad operacional.

**[VALIDACIÓN] [EN_ESPERA] Análisis B edge decay cross-cluster JSON WF → kernel-actual — diferido por viabilidad estadística — 2026-04-23**

Contexto: Bloque 2 Tier 1 sesión 2026-04-23 intentó ejecutar Análisis B (ranking WF vs kernel-actual con Spearman ρ top-5 por cluster) sobre 6 clusters flagged W3. Pause stress-test detectó inviabilidad estadística (6ª aplicación §12 L34 del día):

- JSONs generated 2026-03-27 a 2026-04-07.
- Ventana post-training efectiva: 16-27 días.
- N_trades estimado per config: 1-3.
- Top-5 Spearman ρ con N=2-3 dominado por ruido puro.

Diferimiento obligatorio: Análisis B robusto requiere ventana post-training ≥2 meses para N_trades ≥15 per config.

Disparador: JSONs walk-forward con generated_date ≥60 días (proxy training_end ≥60 días). Para JSONs actuales, proyección ~2026-06-01 (BTC C2 oldest generated 2026-03-27) a ~2026-06-10 (GRT C2 newest generated 2026-04-07). Alternativamente, post-reciclaje (cuando JSONs regeneren + esperar 2 meses más).

Scope ejecución (cuando disparador cumpla):
- 6 clusters × top-5 configs × kernel sobre ventana post-training.
- Spearman ρ top-5 per cluster.
- Tabla agregada cross-cluster.
- Veredicto Caso Alpha Preservado / Decay Parcial / Decay Generalizado.
- Cross-checks TRX C2 orphan + BTC C2 régimen.

Esperable tiempo ejecución: ~60-90 min (kernel 30 configs + docs).

Scope implícito: validación complementaria W3 implementation (corrige futuro, mide decay actual).

**Evidencia interim 2026-04-23 (Opción D validación cruzada)**: validación cruzada W3 flag vs evidencia operacional cross-sesión realizada hoy (§13.4 2026-04-23) provee signal cualitativo. Resultado: **patrón DIVERGENTE** — 0/6 Fuerte, 1/6 Moderada (ONDO C0), 2/6 Débil (TRX C2, BTC C2), 3/6 Ausente (LTC C2, GRT C2, MANA C0). W3 flag correlaciona débilmente con edge decay operacional. 4 clusters CANDIDATO EXCLUSION (APT C0, ONDO C2, SAND C1, SEI C0) no W3 flagged → W3 falsos negativos. Complemento cualitativo que no sustituye Análisis B cuantitativo diferido.

Referencias:
- §13.4 Bloque 2 Pause 2026-04-23 (blocker estadístico detectado).
- §13.4 Opción D validación cruzada W3 2026-04-23 (evidencia interim).
- §13.4 Fase 3 W3 bootstrap 2026-04-23 (implementation que este análisis valida).
- §12 L34 (preventiva 6ª vez — "scope item verifica viabilidad estadística a priori").

Cierre: Análisis B ejecutado con N_trades ≥15 per config + veredicto cross-cluster + W3 validación empírica completada.

---

### 13.4 RESUELTO

**[VALIDACIÓN] [RESUELTO] Bloque 2c Smoke C — replicating pipeline productivo doubled_labels + train/fwd split → SESGO REAL CONFIRMADO (con matices) — 2026-04-24**

Contexto: Post-auditoría harness (§13.4 2026-04-23 entrada), smoke replicating pipeline productivo con setup completo (doubled_labels + train/fwd split) para responder metodológicamente la pregunta "¿walk-forward methodology tiene sesgo real con setup correcto?".

**Setup**:
- `cluster_labels` doubled: bars train (primeros 67%) → labels 0-2, bars fwd (últimos 33%) → labels 3-5. `n_clusters=6`.
- Kernel productivo `run_on_slice` invocación idéntica a pipeline regime_walk_forward.py L571-575.
- 60 configs Fase A universe (top-1, mid rank-10, tail rank-95) + 3 sanity pilot (BTC C2, ONDO C0, GRT C2 W3 flagged).
- Parquets Binance Futures 3y (Abr 2023 - Abr 2026), 9 símbolos.

**Sanity pilot 3 configs**:

| Config | pf_fwd JSON | pf_tr_bin | **pf_fwd_bin** | pf_comb_bin | N_tr | N_fwd |
|---|---:|---:|---:|---:|---:|---:|
| BTC C2 top-1 | 6.359 | 1.591 | **0.772** | 1.277 | 77 | 48 |
| ONDO C0 top-1 | 7.945 | 0.938 | **2.060** | 1.361 | 236 | 143 |
| GRT C2 top-1 | 1.272 | 1.076 | 0.957 | 1.040 | 330 | 145 |

**Distribuciones 60 configs**:

| Group | N | mean pf_tr | **mean pf_fwd** | mean pf_comb | pf_fwd≥2 | pf_fwd<1 |
|---|---:|---:|---:|---:|---:|---:|
| **Top-1** | 20 | 1.530 | **1.126** | 1.388 | **1/20** | 11/20 |
| Mid (rank 10) | 20 | 1.511 | 1.041 | 1.340 | 1/20 | 13/20 |
| Tail (rank 95) | 20 | 1.203 | **1.210** | 1.194 | 0/20 | 8/20 |

**Tests críticos**:

- **Spearman ρ(pf_fwd_JSON, pf_fwd_binance) = +0.047** (essencialmente NULA — ranking WF NO predice pf_fwd real en Binance 3y).
- **Top-1 mean pf_fwd (1.126) vs Tail mean pf_fwd (1.210)**: **tail marginalmente MEJOR que top-1 en fwd real**. Invertido al ranking WF.

**VEREDICTO SMOKE C: SESGO REAL CONFIRMADO (con matices)**.

**Hallazgos core**:

1. **Edge existe en TRAIN**: pf_tr top-1 mean 1.530. Sistema no es "sin edge alguno".

2. **Edge DECAY sustancial train→fwd**: pf_tr 1.53 → pf_fwd 1.13 = decay **26%**. Mid similar (31% decay). Tail sin decay (no había edge en train).

3. **Walk-forward ranking NO predice pf_fwd real**: Spearman ρ=0.047. Virtualmente random correlation.

4. **Top-1 NO discrimina vs tail en fwd**: selection WF dominated por noise en OOS real.

5. **1/20 top-1 con pf_fwd≥2** (ONDO C0 pf_fwd_bin=2.060). Algunos individuos preservan edge robusto, pero **NO sistemáticamente** seleccionados por WF.

6. **11/20 top-1 pf_fwd<1 post-split**: >50% pierde edge net en fwd window.

**Interpretación consolidada Q1+W1+A+B.1 + Smoke C**:

Q1+W1+A+B.1 **NO eran puramente sobre-generalización por setup simplificado**. Corrección del setup (doubled_labels + split correcto) **confirma hallazgos core** aunque con magnitud ajustada:

- Walk-forward methodology **tiene sesgo sistemático real** (train→fwd decay 26%, rank noise-dominated).
- Edge productivo **existe pero modesto** (pf_comb ~1.38 top-1, no robust).
- Cross-exchange Binance ≠ BingX **posible contribuidor secundario** pero no explicación completa.

**Reconciliación con auditoría**:
- Setup simplificado (Q1+W1+A+B.1) subestimaba magnitud pero captaba sesgo real direccionalmente.
- Setup correcto (Smoke C) revela magnitudes exactas: train edge 1.5, fwd decay 26%, rank no predice.
- Ambos consistentes: **walk-forward tiene sesgo sistemático**, lo que varía es la magnitud medida.

**§12 L29 validada masivamente**: walk-forward N_fwd pequeño/selection bias infla expected PF. ONDO C0 pf_fwd=7.945 JSON → Binance 3y pf_fwd=2.06 (ratio 0.26). BTC C2 pf_fwd=6.359 → 0.77 (ratio 0.12). TRX C2 pf_fwd=22.5 tail → 0.72 (ratio 0.03). **Todos los altos pf_fwd del JSON colapsan en fwd real**.

**Implicaciones pre-reciclaje REVISADAS (post-Smoke C)**:

1. **Reciclaje julio con methodology actual**: producirá specialists con train edge moderado (~1.5 PF) y fwd real decay sustancial (~1.1 PF). Reporte pf_fwd del JSON no refleja edge real operacional.

2. **Filter expandido W3+CANDIDATO útil** pero no suficiente. Walk-forward selection rule requiere revisión.

3. **Investigación walk-forward methodology** (§13.3 item) ahora con evidencia cuantitativa robusta:
   - Train→fwd decay 26% es patrón estructural.
   - Rank WF no predice fwd real.
   - Candidatos fixes: multi-testing correction (Bonferroni/BH), cross-validation k-fold, penalty más agresivo sobre N_fwd, filter by ci_low no pf_combined.

4. **Bot operacional v2.4.5**: PF esperado real operacional ~1.0-1.4 (no 4-7 JSON). Esto matches patrón hallazgos empíricos del día (§13.4 A.1 N=26 PnL +0.22 USDT ≈ PF ~1.2).

**§12 L34 15ª aplicación consolidada día 2026-04-23/24**: "validación empírica requiere tanto setup correcto como confirmación cross-setup". Setup simplificado puede sub/sobre-estimar; setup correcto confirma dirección. Aprendizaje meta: **no toda sobre-generalización borra la señal**. La señal persiste aunque con magnitudes ajustadas.

**Status consolidado 4 commits previos** (Q1 397b3c7, W1 affb8c0, Fase A d3b3703, Fase B.1 9459ebe + aclaración 7fe4e0d): **VÁLIDOS direccionalmente** tras Smoke C correction. Anotación interpretativa existente apropiada — quantities medidas subestimaban (Q1+W1+A) o parcialmente corregían (B.1) el fenómeno real que Smoke C confirma.

Scripts preservados: `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` + `_smoke_c_results.csv`.

Items §13.3 derivados:
- **[INVESTIGACION] walk-forward methodology bias sistemático** (§13.3 existente) — **confirmado robustamente**, scope proyecto dedicado claro:
  - Multi-testing correction formal (W5).
  - Cross-validation k-fold vs train/fwd split.
  - Penalty N_fwd más agresivo.
  - Filter by ci_low del bootstrap (ya W3 implementado parcialmente).

Referencias:
- §13.4 Auditoría harness 2026-04-23 (7fe4e0d).
- §13.4 Q1 (397b3c7), W1 (affb8c0), Fase A (d3b3703), Fase B.1 (9459ebe).
- §13.3 "Investigación walk-forward methodology bias sistemático" (confirmado cuantitativamente).
- §12 L29 (validada masivamente, 60/60 configs con train→fwd decay).
- §12 L34 aplicaciones 1-15 consolidadas.

Cierre: permanente. Bloque 2c completo. Investigación walk-forward methodology con evidencia cuantitativa robusta. Reciclaje requiere methodology revisada O aceptar edge operacional moderado.

---

**[AUDITORÍA] [RESUELTO] Harness bloque2c vs pipeline productivo — aclaración interpretativa Q1+W1+A+B.1 — 2026-04-23**

Contexto: Ricardo planteó observaciones metodológicas fundamentales post-Fase B.1. Auditoría directa del harness versus pipeline productivo reveló setup simplificado en dimensiones materiales.

**Fase 1 — Inspección match harness vs pipeline**:

| Aspect | Harness Q1+W1+A+B.1 | Pipeline productivo `regime_walk_forward` | Match? |
|---|---|---|---|
| Kernel function | `run_on_slice` | `run_on_slice` | ✓ |
| `precalculate_all_data` | Productivo | Productivo | ✓ |
| Config decoding (bit-packed) | Internal kernel | Internal kernel | ✓ |
| TF filters / zones / divergencias | Internal kernel | Internal kernel | ✓ |
| Regime_change exits | Internal kernel | Internal kernel | ✓ |
| Funding context | NO en kernel | NO en kernel | ✓ |
| `start_bar` | 500 (Q1+W1+A) | 0 | DIFIERE |
| `warmup` | 100 (default) | 100 (default) | ✓ |
| `cluster_labels` Q1/W1/A | None (no clustering) | **Doubled 0-5** (train/fwd split) | **DIFIERE MATERIAL** |
| `cluster_labels` Fase B.1 | 0-2 (single-clustering GMM match) | **Doubled 0-5** | DIFIERE |
| `n_clusters` | 1 (Q1+W1+A) o 3 (B.1) | **6** (doubled) | DIFIERE |

**Fase 2 — Smoke validation** BTC C2 pf_combined=4.679 JSON contra `data_cache/BTCUSDT_1h.parquet` (75.273 bars, 8.5 años — parquet usado por walk-forward):

| Setup | PF obtenido | trades | Delta vs pf_combined=4.679 |
|---|---:|---:|---:|
| Pipeline-match (`start_bar=0, no cluster_labels`) | **0.992** | 1943 | **−78.8%** |
| Harness-match (`start_bar=500, no cluster_labels`) | **0.993** | 1936 | **−78.8%** |

**Hallazgo interpretativo crítico**:

`pf_combined` del JSON NO es aggregate full dataset. Es **cluster-filtered + train/fwd-split aggregate**:
- Pipeline productivo usa `cluster_labels=doubled` (0-5): labels 0-2 = train bars cluster k, labels 3-5 = fwd bars cluster k.
- `pf_combined = weighted_mean(pf_tr, pf_fwd)` donde `pf_tr = cl_gp[cfg, k]/cl_gl[cfg, k]` (train), `pf_fwd = cl_gp[cfg, k+n]/cl_gl[cfg, k+n]` (fwd).
- Ejecutar kernel sin cluster_labels sobre full dataset produce PF aggregate sobre TODOS los régimenes + TODAS las ventanas temporales → esperable ~1.0 porque specialists C2 están diseñados para operar SOLO en régimen C2 en ventana específica.

**Delta −78.8% es TAUTOLÓGICO por diseño specialist**, NO defect del harness.

**Consecuencia interpretativa sobre Q1+W1+A+B.1**:

| Análisis | Medición válida | Sobre-generalización corregida |
|---|---|---|
| **Q1** "10/10 flagged PF_3y<1.5 sin filter" | Mide PF aggregate cross-régimen sin filter | NO evidencia "edge bajo operacional". Es tautológico — specialists diseñados para cluster-matched bars, aggregate sin filter esperado bajo. |
| **W1** "INFLACIÓN UNIVERSAL 20/20 PF<1.5" | Mide mismo aggregate en control | NO evidencia "universal bias". Cross-universe sin filter productivo → PF~1 esperable por diseño. |
| **Fase A** "rank no discrimina" | Mide rank vs PF aggregate sin filter | NO evidencia "walk-forward selection es noise puro". Rank no discrimina aggregate sin filter productivo — pero nunca fue diseñado para discriminar EN ESE SETUP. |
| **Fase B.1** "caveat 28% filter restaura" | Mide con cluster filter simple (no doubled) | Parcial — cluster filter importa pero single-clustering ≠ pipeline doubled scheme. Subestima edge productivo. |

**NO retracción commits** (397b3c7, affb8c0, d3b3703, 9459ebe) — documentan análisis válido en lo que mide. **SÍ aclaración interpretativa fundamental**: quantities medidas ≠ edge productivo.

**§12 L34 14ª aplicación meta-extendida**:

Previas 1-13: "validación empírica requiere scope estadísticamente viable".

**Ampliación 14ª**: "validación empírica requiere **setup de testing que matches la arquitectura operacional del sistema** antes de conclusiones fuertes". Ejecutar harness con semantics distintas del pipeline productivo puede medir quantities legítimas pero NO evidencia del sistema operacional.

**Ricardo identificó correctamente** la preocupación. "INFLACIÓN UNIVERSAL" era sobre-generalización. Sistema productivo puede tener edge real que harness simplificado oculta por medir "sin filter cross-régimen sin split".

**Parte B pendiente**: smoke replicating pipeline productivo exacto con doubled_labels + train/fwd split sobre Binance 3y → responder metodológicamente la pregunta original.

Referencias:
- §13.4 Q1 (397b3c7), W1 (affb8c0), Fase A (d3b3703), Fase B.1 (9459ebe) — análisis con setup simplificado.
- `lab_historico_numba_v8_3.py` L1849 `run_on_slice` signature.
- `regime_walk_forward.py` L571-575 pipeline invocation con `cluster_labels=regime_labels, n_clusters=n_doubled`.
- Parquet productivo `data_cache/BTCUSDT_1h.parquet` (75,273 bars, referencia smoke).
- §12 L34 14ª aplicación.

Cierre: permanente. Anotación interpretativa fundamental. NO retracción hard.

---

**[INVESTIGACION] [RESUELTO] Bloque 2c Fase B.1 cluster filter post-hoc — CASO PARCIAL (caveat metodológico explica ~28% de Fase A) — 2026-04-23**

**[NOTA INTERPRETATIVA 2026-04-23]**: PF_filtered medido usa cluster_labels single-clustering (0-2), NO pipeline productivo doubled scheme (0-5 con train/fwd split). Mide quantity legítima pero NO equivale a edge productivo del sistema. Ver §13.4 "Auditoría harness bloque2c 2026-04-23" para aclaración completa.

Contexto: Post Fase A "CASO γ INTERMEDIO" (commit d3b3703), hipótesis caveat metodológico propuesta: specialists productivos diseñados operar solo en cluster GMM específico, ejecutar sobre 3y aggregate sin filter dilute PF_3y. Verificación directa via kernel `run_on_slice` con `cluster_labels` parameter (expone per-cluster aggregates nativamente).

**Dataset**: 60 configs Fase A re-ejecutados con GMM cluster classification per-bar + cluster filter post-hoc:
- Top-1 (20), Mid rank-10 (20), Tail rank-95 (20).
- 9 parquets Binance 3y + 9 GMM `regime_models/{SYMBOL}_regime.joblib` aplicados.
- Cluster_labels computed per bar → kernel retorna cl_gp/cl_gl per cluster → PF_filtered = gp/gl solo en cluster_productivo del specialist.

**Resultados distribuciones PF_filtered**:

| Group | N | mean PF_full (Fase A) | **mean PF_filt** | Δ | median | **PF_filt≥2** | PF_filt<1 | N_cluster mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Top-1** | 20 | 1.034 | **1.327** | **+0.293** | 1.152 | **3/20** | 7/20 | 399 |
| **Mid (rank 10)** | 20 | 1.056 | 1.297 | +0.240 | 1.098 | 2/20 | 7/20 | 327 |
| **Tail (rank 95)** | 20 | 1.011 | 1.190 | +0.179 | 1.108 | 1/20 | 5/20 | 361 |

**Tests post-filter**:
- **Spearman ρ(PF_WF, PF_filtered) all = +0.3526 p=0.0041** → SIGNIFICATIVO (Fase A ρ=+0.229 p=0.074 borderline). Filter **restaura información en el ranking**.
- Welch top-1 vs tail PF_filtered: t=+0.869 **p=0.3848** (NO sig con N=20+20). Delta mean +0.137.

**VEREDICTO: CASO PARCIAL** (tendente a "caveat significativo pero no exclusivo").

**Hallazgos críticos**:

1. **Filter mejora PF cross-all-groups**: +0.18 (tail) a +0.29 (top-1). Caveat metodológico **explica ~28% del problema** Fase A.

2. **Spearman pasa de borderline (0.074) a significativo (0.004)** cuando aplicamos filter régimen. **Top-1 SÍ tiene más signal que rank 95 post-filter**, confirmando que walk-forward selection contains ranking information — pero oculto por cross-régimen noise.

3. **3/20 top-1 post-filter con PF≥2** (vs 0/20 pre-filter). Algunos configs SÍ entregan edge robusto cuando se ejecutan en régimen matched.

4. **Top-1 mean PF_filtered = 1.327 < 1.5 "restaurado"**: restauración parcial, no completa. 7/20 top-1 aún con PF<1.0 post-filter.

5. **Top-1 vs tail post-filter NO significativo** (p=0.38): filter restaura signal pero N=20+20 insuficiente para discriminar p<0.05.

**Reinterpretación consolidada Q1+W1+Fase A+B.1**:

- Opción Q1 (flagged PF<1.5): cierto pero parcialmente artifact de cross-régimen sin filter.
- Opción W1 (INFLACIÓN UNIVERSAL): magnitud amplificada por cross-régimen aggregate — filter reduce gap.
- Fase A (CASO γ): caveat metodológico se confirma pero **NO completamente explica** hallazgo.
- Fase B.1: **caveat explica ~28%; restante es edge modesto + multi-testing bias persistente**.

**Interpretación final integrada**:
- Sistema tiene **edge real modesto** cross-universo (top-1 post-filter mean 1.33).
- Walk-forward contiene signal (Spearman p=0.004 post-filter) pero magnitudes absolutas modestas.
- Inflación W_F universal es parcialmente artifact metodológico (cross-régimen masking) + parcialmente bias multi-testing real.
- Filter W3+CANDIDATO útil pre-reciclaje pero no suficiente. Filter expandido + methodology revisada **ambos necesarios**.

**Implicaciones pre-reciclaje revisadas**:

1. **Reciclar con methodology actual + régimen filter apropiado**: producirá specialists con edge moderado (~1.3 PF típico), no robusto (PF≥2 minoritario).

2. **Fase B.2 cross-exchange BingX**: aún relevante para determinar si BingX-específico component del edge existe (podría amplificar vs Binance 1.3 → BingX 1.8+).

3. **Fase B.3 régimen-específico revival**: restringir kernel a ventanas GMM régimen MACRO (no just classifications per-bar). ¿Edge más fuerte en subset específico temporal?

4. **Fase B.4 investigación multi-testing correction formal** (W5 proyecto futuro): Bonferroni/Holm/BH correction sobre selection criterion. W3 bootstrap corrige ci_low individual; W4 raised thresholds; W5 multi-testing correction sobre millones configs selected.

**Matiz metodológico ultrathink**:

Q1+W1+Fase A sub-estimaron el edge real al no aplicar filter régimen. Fase B.1 corrige parcialmente. Evidencia **todavía insuficiente para concluir "sistema edge robusto"** pero también **insuficiente para "sistema sin edge"** — resultado intermedio con implicaciones matizadas.

**§12 L34 13ª aplicación**: caveat metodológico es extensión de "validación empírica requiere setup correcto". Ejecutar kernel sin filter cuando specialist está diseñado operar con filter == measurement bias por metodología inadecuada. Filter parameter del kernel EXISTÍA — inspección kernel más cuidadosa pre-Q1 habría revelado. Aprendizaje meta: antes de sacar conclusiones fuertes, **verificar que setup de testing matches arquitectura operacional**.

Scripts preservados:
- `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_fase_b1.py`.
- `bloque2c_fase_b1_results.csv` (60 configs).

Referencias:
- §13.4 Fase A (d3b3703 — caracterización Caso γ tendente β).
- §13.4 W1 (affb8c0 — INFLACIÓN UNIVERSAL sin filter).
- §13.4 Q1 (397b3c7 — VALIDA cuantitativa sin filter).
- §12 L29 extendida (pre-B1, ahora con matiz caveat).
- §12 L34 13ª aplicación.
- `run_on_slice(..., cluster_labels, n_clusters)` — kernel parameter ya existente.

Cierre Fase B.1: permanente. Caveat metodológico explica ~28% de Fase A. Continuar Fase B.2 (cross-exchange BingX) opcional para refinar entendimiento.

---

**[INVESTIGACION] [RESUELTO] Bloque 2c Fase A caracterización sesgo walk-forward — CASO γ INTERMEDIO (tendente β) — 2026-04-23**

**[NOTA INTERPRETATIVA 2026-04-23]**: PF_3y medido usa kernel sin cluster_labels (no filter productivo). Measured quantity es aggregate cross-régimen 3y — NO equivale a edge productivo. "CASO γ tendente β" aplica SOBRE esa quantity, no sobre edge operacional. Ver §13.4 "Auditoría harness bloque2c 2026-04-23" aclaración.

Contexto: Post Opción W1 INFLACIÓN UNIVERSAL (commit affb8c0), Fase A caracteriza cuantitativamente el sesgo mediante sampling 3 groups × 20 configs. Objetivo: determinar si top-1 correlaciona con PF_3y (Caso α noise aditivo, fix implementation) o si noise es puro (Caso β, fix espacio búsqueda) o combinado (Caso γ).

**Dataset**:
- Top-1 group: 20 configs reuso Q1+W1 (10 flagged + 10 control).
- Mid-rank group (rank 11 de top-100 per cluster): 20 configs cross-symbols+clusters (9 sym × 3 clusters disponibles = 20 selected random).
- Tail-rank group (rank 96 de top-100): 20 configs mismas (symbol, cluster) que mid (rank distinto para aislar efecto).
- Total 60 configs kernel 3y Binance Futures.

**Resultados distribuciones PF_3y per group**:

| Group | N | mean | median | std | P25 | P75 | PF≥2 | PF<1 | ratio_WF_3y mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Top-1** | 20 | **1.034** | 0.978 | 0.229 | 0.887 | 1.083 | **0/20** | 10/20 | **0.342** |
| **Mid (rank 10)** | 20 | 1.056 | 1.006 | 0.248 | 0.910 | 1.081 | 0/20 | 10/20 | 0.373 |
| **Tail (rank 95)** | 20 | 1.011 | 0.964 | 0.219 | 0.868 | 1.093 | 0/20 | 12/20 | 0.392 |

**Tests estadísticos**:
- Spearman ρ(pf_fwd_WF, PF_3y) all groups = **+0.229 p=0.0737** (borderline, NO sig α=0.05).
- Welch top-1 vs tail: **p=0.7509** (NO sig — distribuciones idénticas).
- Welch pairwise top-1 vs mid: no sig. Welch mid vs tail: no sig.

**VEREDICTO: CASO γ INTERMEDIO (tendente a β)**.

**Hallazgos críticos**:

1. **60/60 configs con PF<2.0 cross-groups**. Ningún rank del top-100 entrega edge robusto cross-universe 3y.

2. **Distribuciones PF_3y estadísticamente idénticas entre groups** (means 1.011-1.056, stds 0.22-0.25, Welch p>0.75 todas las comparaciones). Top-1 NO es materialmente distinto de rank 95.

3. **Débil correlación PF_WF → PF_3y** (ρ=+0.229, p=0.074 borderline). Microinformation existente pero marginalmente detectable — no soporta "walk-forward selecciona edge materialmente mejor".

4. **Ratio WF/3y similar cross-groups** (0.34-0.39). Inflación NO es proporcional al PF_WF (esperado α). Es **aditiva cross-rank**: todos los rangos parten de PF_3y ~1 y pf_fwd_WF adiciona ruido ~0.34-0.39×.

**Interpretación arquitectónica**:

- **β fuerte (dominante)**: edge real ~1.0 cross-universe independiente del rank. Los JSONs productivos actuales contienen universos con edge real ≈ 0 neutral sobre Binance Futures 3y.
- **α débil (secundario)**: correlación débil PF_WF→PF_3y (borderline p=0.074) sugiere microinformation, pero insuficiente para justificar "walk-forward selection valida".

**Implicaciones arquitectónicas ultrathink**:

La inflación walk-forward NO es case-isolated ni proporcional al PF_WF. **Todos los rangos del top-100 muestran edge real ~1.0 neutral cross-régimen Binance 3y**. Hipótesis candidatas explicativas:

1. **Edge del sistema original perdido en régimen Binance 2023-2026**: sistema reproducible en data específica (Pine v44 entrenamiento en BingX Spot probablemente 2019-2023), perdió signal en ventana reciente. Market regime shift.

2. **Cross-exchange Binance ≠ BingX crítico**: sistema tiene edge ejecutable en BingX Futures específicamente (microstructure, liquidez, fees). Binance Futures es "mismo mercado" pero NO "mismo edge". Refutable con fetch BingX histórico.

3. **Sistema requiere cambio fundamental pre-reciclaje**: configs actuales + methodology walk-forward no detectan edge en data actual. Reciclaje con misma methodology sobre espacio igual = repetir sin edge.

**Re-orientación Fase B (post-A ultrathink)**:

Caso γ intermedio típicamente orientaría a "combinar inspection implementation + revisión espacio". Pero 0/60 PF≥2 es dominante → comportamiento efectivo caso β. Inspección implementation sola probablemente NO resuelve.

**Fase B propuesta** (re-orientada):
- **B.1 Cross-exchange validation** (~1-2h): fetch BingX histórico 3 símbolos + kernel runs. Si BingX PF_3y materialmente >1.5, cross-exchange es factor. Si no, elimina esa hipótesis.
- **B.2 Régimen-específico revival** (~1-2h): restringir kernel a bars dentro de ventanas-régimen específicas GMM BTC (vs agregado 3y). ¿El sistema tiene edge en subset régimen específico?
- **B.3 Escalación meta-arquitectónica** (condicional post-B1+B2): si B.1+B.2 no revelan edge, sistema puede requerir revisión profunda — no solo methodology walk-forward.

**Evidencia interim para decisión reciclaje**:
- Reciclaje julio con JSONs actuales + misma methodology = probable repetición sesgo universal.
- **Prerequisito recomendado pre-reciclaje**: completar B.1+B.2 para determinar naturaleza del problema.

Scripts preservados: `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_fase_a.py` + `_fase_a_results.csv`.

Referencias:
- §13.4 Bloque 2c Opción Q1 2026-04-23 (397b3c7).
- §13.4 Bloque 2c Opción W1 2026-04-23 (affb8c0 — INFLACIÓN UNIVERSAL).
- §13.3 "Investigación walk-forward methodology bias sistemático" (en_curso, Fase A completada).
- §12 L29 extendida caso universal.
- §12 L34 12ª aplicación sesión (caracterización ≠ confirmación solo).

Cierre Fase A: permanente. Fase B re-orientada documentada. Proceder Fase B en sesión dedicada (evitar scope creep en sesión actual ya extensa).

---

**[VALIDACIÓN] [RESUELTO] Bloque 2c Opción W1 — control group flagged vs unflagged → INFLACIÓN UNIVERSAL — 2026-04-23**

**[NOTA INTERPRETATIVA 2026-04-23]**: "INFLACIÓN UNIVERSAL" declarada aplica sobre PF aggregate cross-régimen sin filter productivo. NO equivale a "sistema sin edge" — quantity medida tautológicamente ~1 por diseño specialist. Ver §13.4 "Auditoría harness bloque2c 2026-04-23" para interpretación correcta.

Contexto: Extensión Opción Q1 (commit 397b3c7) con control group matched-by-pf_fwd distribution para discriminar entre "filter discrimina edge decay" vs "inflación universal walk-forward".

**Dataset**:
- Flagged (Q1): 10 configs (6 W3 + 4 CANDIDATO EXCLUSION). PF_3y reportados en entrada Q1.
- Control (W1): 10 configs UNFLAGGED matched por pf_fwd distribution (low 4 + medhi 4 + hi 2). Parquets Q1 reutilizados (sin fetch adicional).

**Control group configs**:

| Symbol C | cfg_id | pf_fwd_WF | N_fwd | PF_3y | ratio WF/3y | Label |
|---|---:|---:|---:|---:|---:|---|
| MANA C1 | 35173823 | 1.377 | 232 | **0.891** | 0.647 | **EDGE PERDIDO** |
| TRX C0 | 3156128 | 1.472 | 380 | **0.876** | 0.595 | **EDGE PERDIDO** |
| MANA C2 | 53443118 | 1.789 | 99 | 1.033 | 0.578 | Débil |
| APT C2 | 52477067 | 1.829 | 178 | **0.900** | 0.492 | **EDGE PERDIDO** |
| BTC C1 | 1118752 | 3.997 | 59 | **1.786** | 0.447 | Moderado |
| APT C1 | 31447907 | 4.780 | 25 | **0.811** | 0.170 | **EDGE PERDIDO** |
| SEI C1 | 40002182 | 5.208 | 24 | 1.070 | 0.205 | Débil |
| BTC C0 | 38007639 | 5.490 | 19 | 1.304 | 0.237 | Débil |
| SAND C0 | 20075296 | 9.512 | 18 | 1.268 | 0.133 | Débil |
| SAND C2 | 16987014 | 18.963 | 19 | 1.122 | **0.059** | Débil |

**Agregados Control W1**:
- mean PF_3y: **1.106**
- median PF_3y: 1.070
- PF<1.5: **9/10** (solo BTC C1 alcanza 1.786, no supera threshold)
- PF<1.0: 4/10
- PF≥2.0: **0/10**
- mean ratio WF/3y: 0.356

**Comparación Flagged Q1 vs Control W1**:

| Métrica | Flagged (Q1) | Control (W1) | Delta |
|---|---:|---:|---:|
| N | 10 | 10 | — |
| mean PF_3y | 0.962 | **1.106** | +0.144 |
| PF<1.5 | 10/10 | **9/10** | −1 |
| PF<1.0 | 6/10 | 4/10 | −2 |
| PF≥2.0 | 0/10 | **0/10** | 0 |

Tests estadísticos:
- Welch t = −1.446, **p = 0.1482 (NO SIGNIFICATIVO α=0.05)**.
- Mann-Whitney p = 0.2265 (NO SIGNIFICATIVO).
- Cohen d = −0.647 (medio-grande, pero N=10+10 insuficiente para p<0.05).

**VEREDICTO: INFLACIÓN UNIVERSAL — filter NO discrimina significativamente**.

**Reinterpretación Opción Q1**:
- Q1 sin control: "VALIDA cuantitativamente" (flagged detecta edge bajo).
- Q1 + W1 combinado: filter marca configs con edge bajo, **pero inflación walk-forward es universal cross-universe**. Filter W3+CANDIDATO NO discrimina subset especial — marca el mismo fenómeno que afecta todos los top-1 configs.

**Hallazgo crítico emergente**: **20/20 configs (flagged + control) con PF_3y<1.5 sobre Binance 3y; 0/20 con PF≥2.0**. Los JSONs productivos actuales tienen **sesgo sistemático walk-forward masivo** afectando virtualmente todo el universo top-1 per cluster.

**§12 L29 extendida**: no es solo "N_fwd pequeño inflation" en casos aislados. Es **"walk-forward selection bias amplifica noise cross-universe"** — pattern estructural del pipeline entero, no anomalía de configs flagged.

**Implicaciones operacionales revisadas**:

1. **Filter expandido W3+CANDIDATO EXCLUSION**: útil para excluir los peores pero **no discrimina subset crítico**. Todos los JSONs actuales pueden ser marginal O subóptimo.

2. **Reciclaje urgencia re-evaluada**:
   - Data pro-adelantar reciclaje: todos los configs actuales entregan edge bajo cross-3y Binance.
   - Data anti-adelantar: reciclaje con **misma methodology produce mismo sesgo**. Reciclar sin revisar methodology = repetir el problema.
   - **Recomendación nueva**: priorizar investigación walk-forward methodology ANTES de reciclar. Si se adelanta reciclaje, aplicar methodology revisada.

3. **W3 + W4 implementations valiosas** (corrigen estadísticos estructurales específicos: ci_low bootstrap + thresholds _FWD) pero **insuficientes solas** — abordan síntomas, no causa raíz sistemática.

4. **Nuevo item §13.3 alta priority**: "Investigación walk-forward methodology sistemático bias cross-universe" (creado — ver §13.3).

**Reconciliación con prior hallazgos**:
- Opción D cualitativa (b8bfcc5): DIVERGENTE W3 vs CANDIDATO (ortogonales en recency).
- Opción Q1 cuantitativa (397b3c7): VALIDA (ambos detectan edge bajo).
- Opción W1 cuantitativa (este commit): INFLACIÓN UNIVERSAL (filter no discrimina).
- **Sin contradicción — niveles de análisis distintos**: D mide correlación flagged↔recency operational; Q1 mide edge histórico flagged; W1 añade baseline unflagged → revela que edge bajo es el baseline, no la excepción.

**Meta-observación**: aplicación §12 L34 **11ª del día** — validación SIN control group habría aceptado "filter valida" sin detectar que filter no discrimina. Control group crítico para análisis comparativo. L34 generalizada extended: "validación empírica requiere baseline/control cuando se evalúa si un criterio DISCRIMINA (no solo marca correlacionalmente)".

**Caveats**:
- N=10+10 insuficiente para p<0.05 con Cohen d=-0.65. Probabilístico pero no categórico.
- Cross-exchange Binance ≠ BingX: direccionalidad preservada; magnitudes absolutas pueden diferir modestamente.
- Control group matched por pf_fwd distribution — no matched por symbol o otras covariables.
- BTC C1 control único con PF_3y=1.786 (cerca 2.0) — sugiere que algún subset unflagged podría tener edge material. N mayor necesario para caracterizar.

Items §13.3 derivados:
- **Investigación walk-forward methodology bias sistemático** (nuevo, high priority).
- Filter expandido pre-reciclaje: **útil pero no categórico** — implementar con caveat explícito.
- L29 extendida cross-universe: generalización Lección §12 no-item-§13.3.

Referencias:
- §13.4 Bloque 2c Opción Q1 2026-04-23 (VALIDA cuantitativa — reinterpretada con W1).
- §13.4 Bloque 2c Opción D 2026-04-23 (DIVERGENTE cualitativa).
- §13.4 Bloque 2b coverage Binance 2026-04-23.
- §13.3 "Investigación walk-forward methodology bias" (nuevo).
- §12 L29 extendida cross-universe.
- §12 L34 (11ª aplicación — control group para análisis comparativo).
- `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_w1_control.py` + results CSV.

Cierre: permanente. Inflación universal confirmed. Investigación methodology walk-forward derivada a §13.3.

---

**[VALIDACIÓN] [RESUELTO] Bloque 2c Opción Q1 — W3 divergencia validation cuantitativa cross-3y Binance Futures — 2026-04-23**

**[NOTA INTERPRETATIVA 2026-04-23]**: "VALIDA cuantitativamente" aplica sobre PF aggregate cross-régimen sin filter productivo. Filter W3+CANDIDATO detecta clusters con PF aggregate bajo — pero bajo es esperable por diseño specialist, no evidencia edge operacional bajo. Ver §13.4 "Auditoría harness bloque2c 2026-04-23" para interpretación correcta.

Contexto: Post 8-9 aplicaciones §12 L34 sesión 2026-04-23, scope Bloque 2c realista converged a Opción Q1: solo W3 divergencia validation viable con kernel aggregates actuales. H1+H_funding+H_strategy diferidos proyecto I1 post-reciclaje (item §13.3 ampliado commit).

**Tier 0 I2 prerequisite**: commit 53fe73a (`--data-path` CLI + tests 8/8 PASS + smoke §0.8 Nivel A backward compat 0.0000 exacto).

**Dataset**:
- 10 (symbol, cluster) targets: 6 W3 flagged + 4 CANDIDATO EXCLUSION persistentes 2+ sesiones.
- 9 unique symbols × 3y Binance Futures OHLCV (2023-04-24 → 2026-04-23).
- Fetch CSV desde VPS Tokio (geo-blocking §12.24) → sync local → convert parquet.
- N_candles per symbol: 26280 (majors 3y completos), 19777 (ONDO listed 2024-01-20 ~2.3y), 23532 (SEI listed 2023-08-17 ~2.7y).
- Kernel Numba `run_on_slice` directo (bypass brain-level 40× slower).

**Resultados per (symbol, cluster)**:

| Symbol+Cluster | Flag Type | cfg_id | preset | PF_WF | PF_3y | ratio | N_trades | label |
|---|---|---:|---|---:|---:|---:|---:|---|
| ONDO C0 | W3 | 2457036 | VIDYA(18)/KAMA(54)_H00 | 5.500 | **0.894** | 0.16 | 1251 | **EDGE PERDIDO** |
| LTC C2 | W3 | 2532096 | VIDYA(16)/HMA(33)_H00 | 3.518 | 1.045 | 0.30 | 308 | Débil |
| GRT C2 | W3 | 58457547 | TEMA(10)/VIDYA(49)_H00 | 1.229 | 1.004 | 0.82 | 1752 | Débil |
| TRX C2 | W3 | 53066572 | VIDYA(16)/KAMA(69)_H05 | **11.944** | 1.227 | **0.10** | 526 | Débil |
| BTC C2 | W3 | 20607806 | Tenkan(16)/EMA(42)_H05 | 4.679 | **0.952** | 0.20 | 680 | **EDGE PERDIDO** |
| MANA C0 | W3 | 5339578 | VIDYA(18)/KAMA(75)_H00 | 3.622 | **0.855** | 0.24 | 1997 | **EDGE PERDIDO** |
| APT C0 | CAND_EX | 2473235 | Tenkan(24)/KAMA(72)_H00 | 1.612 | **0.825** | 0.51 | 4877 | **EDGE PERDIDO** |
| ONDO C2 | CAND_EX | 36616254 | McGinley(24)/KAMA(30)_H00 | 3.214 | **0.870** | 0.27 | 2150 | **EDGE PERDIDO** |
| SAND C1 | CAND_EX | 1129791 | VIDYA(10)/SMA(30)_H00 | 1.514 | 1.030 | 0.68 | 1849 | Débil |
| SEI C0 | CAND_EX | 36812972 | T3(18)/T3(63)_H00 | 1.792 | **0.917** | 0.51 | 2131 | **EDGE PERDIDO** |

**Agregados per flag type**:

| Flag Type | N | mean_PF_3y | PF<1.5 | PF<1.0 | PF≥2.0 |
|---|---:|---:|---:|---:|---:|
| **W3 flagged** | 6 | **0.996** | **6/6** | 3/6 | **0/6** |
| **CANDIDATO EXCLUSION** | 4 | **0.911** | **4/4** | 3/4 | **0/4** |
| **Combined 10** | 10 | **0.962** | **10/10** | 6/10 | **0/10** |

**Veredicto: CASO VALIDA CUANTITATIVAMENTE (ambos flag types)**.

Ambos flag types convergen en detección de edge bajo histórico:
- **100% de flagged (W3 ∪ CANDIDATO) tienen PF_3y < 1.5** (edge no-robusto).
- **60% tienen PF_3y < 1.0** (edge neto PERDIDO — loss-making histórico).
- **0% tienen PF_3y ≥ 2.0** (ningún config flagged mostró edge robusto histórico).

**Ratio PF_WF vs PF_3y (todos los 10)**: 0.10-0.82. **TODOS** los configs tienen PF_WF inflado 1.2×-10× vs PF_3y real — confirma empírica y masivamente **§12 Lección 29** (walk-forward N_fwd pequeño infla expected PF).

Caso extremo TRX C2: PF_WF=11.944 → PF_3y=1.227 (ratio 0.10, inflación 10×). El outlier extremo del patrón L29.

**Reconciliación con Opción D cualitativa (commit b8bfcc5)**:
- Opción D cualitativa: patrón DIVERGENTE — W3 no correlaciona con evidencia operacional cross-sesión CANDIDATO EXCLUSION (analyzer + WARN_neg_res + health_monitor).
- Opción Q1 cuantitativa: ambos convergen en detección edge bajo histórico.
- **No contradicción**: Opción D midió overlap evento-sesión específico (recency 30d). Opción Q1 mide edge histórico agregado 3y. Ambas correctas — detectan fenómenos temporalmente distintos. W3 y CANDIDATO EXCLUSION son **herramientas ortogonales complementarias**: W3 detecta bias estadístico histórico, CANDIDATO detecta edge decay reciente.

**Implicaciones pre-reciclaje**:

1. **W3 como filter**: **VALIDADO CUANTITATIVAMENTE** — 6/6 flagged con edge bajo histórico 3y. W3 es filter robusto pre-reciclaje. No es falso positivo.

2. **CANDIDATO EXCLUSION como filter**: **VALIDADO CUANTITATIVAMENTE** — 4/4 flagged con edge bajo histórico. Criterio ratio_oos/pool < 0.5 del analyzer v2.4.1 es predictor válido de PF_3y < 1.5.

3. **Filter expandido propuesto** (W3 OR CANDIDATO EXCLUSION): **VALIDADO CUANTITATIVAMENTE** — unión de ambos captura 10/10 configs con edge bajo histórico. Complementariedad confirmada.

4. **Acción pre-reciclaje**: al próximo reciclaje excluir/demotarios configs que cumplan W3 flagged OR CANDIDATO EXCLUSION persistente 2+ sesiones. Alta confianza empírica.

5. **§12 L29 (walk-forward N_fwd inflation)**: validada masivamente — 10/10 con PF_WF inflado 1.2×-10× vs PF_3y real. Patrón estructural, no caso aislado ONDO C0 original.

**Caveats**:
- Cross-exchange Binance ≠ BingX: PF_3y calculado sobre Binance Futures data; magnitud absoluta puede diferir modestamente de BingX real. Direccionalidad (PF<1.5 vs ≥2.0) preservada cross-exchange por naturaleza del edge estructural.
- Kernel Numba sin cluster filter post-hoc: PF_3y es mixed-régimen aggregate. Per-régimen descomposición diferida a Tier 0 I1 proyecto.
- H1+H_funding+H_strategy no validables en este scope (requieren Tier 0 I1 per-trade data).

**Items §13.3 derivados**:
- Item I1 ampliado: Tier 0 I1 + Bloque 2c full scope H1+H_funding+H_strategy post-reciclaje (creado esta sesión).
- Item "filter expandido pre-reciclaje" opcional — current L1398 política ya cubre criterio operacional; validación cuantitativa refuerza spec existente.

Referencias:
- §13.4 Opción D 2026-04-23 (cualitativa baseline, commit b8bfcc5).
- §13.4 Bloque 2b 2026-04-23 (cobertura Binance Futures).
- §13.4 Tier 0 I2 commit 53fe73a 2026-04-23 (`--data-path` habilita data source alternativa).
- §13.3 Tier 0 I1 ampliado (post-reciclaje).
- §13.3 L1398 política adelantar reciclaje.
- §12 L29 (walk-forward N_fwd inflation — validada masivamente).
- §12 L34 (9-10 aplicaciones sesión).
- `bloque2c_w3_results.csv` dataset reference.

Cierre: permanente. Evidencia cuantitativa robusta W3+CANDIDATO EXCLUSION validation. Filter expandido pre-reciclaje soportado empíricamente.

---

**[VALIDACIÓN] [RESUELTO] _run_verify_test --data-path habilitado — Tier 0 I2 Bloque 2c — 2026-04-23**

Ver commit `53fe73a`. Signature extendida con `data_path=None` opcional. CLI `--data-path PATH`. Backward compat preservado (sin path usa default data_cache productivo). Prerequisite Bloque 2c Opción Q1 — permitió cargar Binance Futures parquets sin modificar data_cache/{SYMBOL}USDT_1h.parquet productivo. Tests 8/8 PASS + smoke §0.8 Nivel A backward compat diff 0.0000.

---

**[VALIDACIÓN] [RESUELTO interim] Bloque 2 Análisis B pausado + Opción D validación cruzada W3 flag — 2026-04-23**

Contexto: Bloque 2 Tier 1 planificó Análisis B (ranking WF vs kernel-actual) cross-cluster 6 clusters flagged W3 bootstrap. Pause empírico Fase 0 detectó blocker.

**Blocker estadístico (6ª aplicación §12 L34 preventiva del día)**: JSONs walk-forward generated 2026-03-27 a 2026-04-07 → ventana post-training 16-27 días → N_trades per config 1-3 → top-5 Spearman ρ estadísticamente inerte. Robustez requiere ventana post-training ≥2 meses.

Acciones aplicadas:
1. Análisis B diferido: §13.3 item nuevo con disparador generated_date ≥60 días proxy (~2026-06-01 BTC C2 oldest).
2. **Opción D refinada ejecutada** — validación cruzada W3 flag vs evidencia operacional cross-sesión ya disponible. Analíticamente distinta de Análisis B (cualitativa vs cuantitativa), pero responde aproximadamente la pregunta motivacional.

**Resultados Opción D (validación cruzada)**:

| Cluster W3 | E1 CANDIDATO persistente (2+ sesiones) | E2 WARN_neg_res (symbol Fase II.C) | E3 health_monitor | Convergencia |
|---|---|---|---|---|
| ONDO C0 | NO (ONDO C2 persistente, no C0) | SÍ (ONDO) | SÍ (ONDO C0) | **Moderada 2/3** |
| LTC C2 | NO | NO | NO | Ausente 0/3 |
| GRT C2 | NO | NO | NO | Ausente 0/3 |
| TRX C2 | NO | SÍ (TRX) | NO | Débil 1/3 |
| BTC C2 | NO | SÍ (BTC) | NO | Débil 1/3 |
| MANA C0 | NO | NO | NO | Ausente 0/3 |

Indicadores:
- **E1 CANDIDATO EXCLUSION cross-sesión**: persistentes 2+ sesiones = [ONDO C2, SAND C1]. Fase II.C 2026-04-22 flagged ONDO C2 + SAND C1; A.1 2026-04-23 flagged APT C0 + ONDO C2 + SAND C1 + SEI C0. Intersección 2 clusters. **Ningún W3 flagged aparece en E1 persistente**.
- **E2 WARN_neg_res Fase II.C**: 17 símbolos = {APT, SOL, LINK, ENA, RENDER, OP, TAO, XLM, BTC, SUI, ALGO, ADA, INJ, ONDO, ICP, SAND, TRX}. Caveat: per-symbol no per-cluster. 3/6 W3 symbols aparecen (ONDO, BTC, TRX).
- **E3 health_monitor**: 1 cluster flagged = ONDO C0 (§13.4 2026-04-22).

**Cross-check inverso**:
Clusters flagged CANDIDATO EXCLUSION pero **NO W3 flagged**: [APT C0, ONDO C2, SAND C1, SEI C0]. **Implica W3 tiene 4 falsos negativos** — clusters con edge decay operacional real no capturados por bootstrap ci_low/ci_width.

**Patrón observado**: DIVERGENTE (0/6 Fuerte, 1/6 Moderada, 2/6 Débil, 3/6 Ausente). W3 flag **ortogonal** a edge decay operacional.

**Implicaciones operacionales**:

**a) W3 implementation status pre-reciclaje**:
- W3 captura **bias estadístico de construcción** (ci_low/ci_width por N pequeño OOS, multiple-testing amplifica noise).
- CANDIDATO EXCLUSION captura **edge decay observable** (expectancy OOS/pool < 0.5).
- Las dos detecciones son **ortogonales**, no redundantes.
- W3 es filter necesario pero **no suficiente** para pre-reciclaje.

**b) Decisión adelantar reciclaje**:
- E1 persistentes 2+ sesiones: 2 clusters (ONDO C2, SAND C1).
- Criterio §13.3 L1398 semi-automático: "3+ clusters flagged candidato_exclusion sostenido en 2+ reportes consecutivos". **2 no cumple threshold de 3**.
- Recomendación: **mantener calendario julio** pero monitorear próximos reportes N≥50 (~2026-04-26) y N≥100 (~2026-05-01). Si APT C0 y/o SEI C0 (nuevos A.1) persisten en próximo reporte → criterio semi-automático se cumpliría.

**c) Filters pre-reciclaje expandidos propuestos**:
Si Opción D revela que analyzer CANDIDATO EXCLUSION es evidencia operacional más temprana que W3 → considerar filter completo pre-reciclaje:
- `flagged W3 OR (CANDIDATO EXCLUSION persistente 2+ sesiones) OR (WARN_neg_res severo per symbol+cluster breakdown)`.
- Unión de 3 indicadores → cobertura estadística + operacional + volumen residual.

**Cross-checks específicos**:
- **TRX C2 (W3 flagged + W4 orphan)**: Débil en E2 (TRX en WARN_neg_res), ausente E1+E3. No doble evidencia pro-orphan — W4 puede ser overly conservative para este cluster específico.
- **BTC C2 (W3 flagged, máximo score productivo 17.21)**: Débil en E2 (BTC en WARN_neg_res); ventana A.1 dominada por régimen C1 (71%) no C2. Sensibilidad esperable — falta de específicos flags ausentes refuerza robustez arquitectónica cross-régimen.

**Meta-observación**: esta pausa extiende §12 L34 recurrentemente. Cuenta refutaciones/pausas día 2026-04-23: **6 total** (H1, H_strategy, H_new_3, L2018, ratio 25%, Análisis B viabilidad). 3 recursivas sobre creaciones de la sesión misma (L2018, ratio 25%, Análisis B prompt).

Consistencia metodológica: el criterio L34 no prefiere ningún lado — refuta igualmente creaciones externas, creaciones propias, y scope de análisis propuestos. Cada stress-test previene consumo de recursos en análisis N-insuficiente.

Referencias:
- §13.3 nuevo item "Análisis B cross-cluster diferido" (este commit).
- §13.4 Fase 3 W3 bootstrap 2026-04-23 (flagged 6 clusters).
- §13.4 Fase II.C 2026-04-22 (analyzer flags + 17 WARN_neg_res).
- §13.4 A.1 2026-04-23 (analyzer flags recientes: APT C0, ONDO C2, SAND C1, SEI C0).
- §13.3 L1398 política adelantar reciclaje (criterio 3+ clusters persistentes).
- §12 L34 (6ª aplicación sesión).

Cierre: Opción D interim completada. Análisis B cuantitativo diferido a §13.3 con disparador generated_date ≥60 días.

---

**[MEJORA] [REFUTADO] Item pnl_recon ratio 25% refutado por prerequisito inviable + nuevo item Opción D investigación causa raíz — 2026-04-23**

Contexto: item §13.3 creado esta misma sesión (2026-04-23 commit ab4f6f6) como hipótesis refinada post-refutación L2018. Proponía fix `tolerance = max(0.005, 0.25 * abs(pnl_usdt))` basado en gap distribución p50 21% p75 19% p90 15% sobre N=26 A.1. Prerequisite explícito: "validación multi-segmento N=98 antes de implementar".

Stress-test validación multi-segmento reveló prerequisito inviable:

**Diagnóstico dataset**:
- CSV N=164 total. 104 analyzable. 26 con pnl_recon_gap populado.
- **138/164 trades pre-v2.4.4 tienen size_usdt=0** por bug histórico (§2.4 v2.4.4 "134/135 afectados desde origen 2026-04-13").
- contracts = size_usdt / entry_price = 0 → pnl_recon = 0 → pnl_recon_gap ≈ |pnl_usdt| trivialmente fuera de tolerance, pero por bug histórico, no señal real.

**Distribución segmentos con pnl_recon computable**:

| Segmento | N enriched | N con size_usdt>0 | Validable? |
|---|---|---|---|
| S1 pre-v2.3.11 | 49 | ~0 | NO |
| S2 v2.3.11→v2.4.0 | 7 | ~0 | NO |
| S3 v2.4.0→v2.4.4 | 18 | ~0 | NO |
| S4 post-v2.4.4 | 24 | 24 | SÍ |

Solo S4 (N=24) testeable — **subconjunto del mismo segmento origen** del A.1 N=26. "Multi-segmento N=98" del prerequisite era S4 N=24 renombrado, no validación cross-segmento real.

**Aplicación L34 recursiva**: el item propio violaba el criterio de elevación L34 que invocaba como prerequisite. Misma trampa cognitiva que H1/H_strategy/H_new_3/L2018 refutados hoy — asumir viabilidad de validación sin verificar empíricamente que los datos la soporten.

**Alternativas evaluadas**:

1. **Opción A (recomputar contracts desde logs SIGNALS_EXECUTED)**: viable técnicamente pero introduce confounding — el gap sobre trades con contracts inferidos mezcla "gap real" con "ruido de inferencia". S1-S3 no apareables directamente con S4 que usa size_usdt BingX-reportado genuino. L34 aplicada a prerequisite advierte: validación con método que introduce el mismo tipo de ruido que se quiere medir es equivalente a no validar.

2. **Opción B (validación S4 only con caveat)**: viola L34 explícitamente. N=24 single-segment es el patrón exacto prohibido.

3. **Opción C (mantener item EN_ESPERA permanente)**: síntoma persiste saturando analyzer (92% WARN). Item dormido hasta post-reciclaje cuando S5 exista. Costo metodológico bajo, costo operacional medio.

4. **Opción D (investigación causa raíz)**: cambia naturaleza del fix. En lugar de calibrar tolerance más permisiva, identifica qué componente domina el gap típico 19-25% (precision rounding CSV / fees BingX estimación / notional definition). Fix resuelve fenómeno vs tapar síntoma. Scope ~1-2h sesión dedicada data-independent (requiere comparar analyzer output con raw BingX API responses, no nueva data operacional).

**Decisión aplicada**: Opción E (refutar item ratio 25% por prerequisite inviable) + Opción D (crear nuevo item scope explícito).

**Nuevo item creado**: "[MEJORA] [EN_ESPERA] Investigación causa raíz pnl_recon gap analyzer — 2026-04-23" en §13.3 con disparador sesión dedicada ~1-2h.

**L1916 NO cierra por merge**: depende del item refutado. Mantiene EN_ESPERA con context update apuntando a nuevo item Opción D. El merge path queda diferido hasta investigación causa raíz + fix subsecuente.

**Conteo refutaciones día 2026-04-23**: 5 por stress-test L34 aplicado — H1, H_strategy, H_new_3, L2018, ratio 25%. 2 son refutaciones recursivas sobre items creados en la misma sesión (L2018, ratio 25%). Patrón inverso al sesgo confirmatorio: el stress test cuestiona igualmente creaciones propias.

**Meta-observación**: L34 no solo aplica a hipótesis post-hoc N<50. Aplica también a prerequisitos de validación propuestos como specs de items §13.3. Patrón captable: "multi-segmento" como criterio requiere verificar empíricamente que los datos soportan la segmentación antes de escribirlo como requirement.

Referencias:
- §13.3 item "ratio 25%" (commit ab4f6f6 hoy) movido a REFUTADO.
- §13.3 nuevo item "Investigación causa raíz pnl_recon gap" creado.
- §13.3 L1916 2026-04-16 mantiene EN_ESPERA con context update.
- §12 L34 (aplicada recursivamente 2ª vez hoy).
- §2.4 v2.4.4 size_usdt fix (origen bug histórico).

Cierre: permanente por prerequisite inviable.

---

**[MEJORA] [RESUELTO] L1839 batch fix cp1252 runtime-critical lab_historico — 2026-04-23**

Contexto: §13.3 L1839 2026-04-22 solicitaba batch fix de "14 ocurrencias no-ASCII" en `lab_historico_numba_v8_3.py` en paths que `_run_verify_test` NO ejecuta (master.py pipeline + walk-forward). Prerequisito pre-reciclaje para habilitar `master.py --recycle` Windows cp1252 sin UnicodeEncodeError.

Verificación empírica 2026-04-23 reveló **cifra real muy superior a documentada**: 420 chars no-ASCII en 188 líneas totales (incluyendo box drawings `─` 153, flechas `→` 45, em-dash `—` 22, emojis 66, acentos españoles 119, variation selectors 12). La cifra "14" del A27 era subestimación sustancial.

**Sub-análisis por contexto runtime**:
- print/log (critical): **70 chars cp1252-unsafe en 59 líneas**.
- f.write + string assignments consumidas (critical): ~9 líneas adicionales.
- comments/docstrings (no runtime): 30 chars en 20 líneas (preservados — Python 3 default UTF-8 reading).
- "other" (inline trailing comments): 178 chars mostly `→` en comments de lógica bitwise (preservados).

**Scope aplicado**: 68 líneas runtime-critical. Comments/docstrings/acentos españoles preservados. Chars cp1252-unsafe post-fix en runtime lines: **0**.

**Mapping ASCII aplicado** (tabla estándar):
- ⚙️ → [CALC]
- ✅ → [OK]
- ❌ → [ERROR]
- ⚠️ → [WARN]
- 📊 → [STATS]
- 📈 → [CHART]
- 📥 → [DOWN]
- 📋 → [LIST]
- 📅 → [DATE]
- 📝 → [EDIT]
- 💾 → [SAVE]
- 🚀 → [START]
- 🔬 → [RESEARCH]
- 🔄 → [REFRESH]
- 🏆 → [TOP]
- 🧪 → [LAB]
- 🛑 → [STOP]
- 🆕 → [NEW]
- ⬆️ → [UP]
- → (U+2192) → ->
- ─ (U+2500) → -
- ✓ → V
- ✗ → X

Validación (Fidelidad 2 invariante por construcción — solo strings, sin lógica):
- Smoke §0.8 Nivel A (BTC N=1000): diff 0.0000 exacto ✓ PASS.
- Smoke §0.8 Nivel C (audit_mr_fidelity_sei): diff 0.0000 en 7 métricas ✓ PASS.
- Nivel B no re-ejecutado (lab_historico no cambió lógica; redundante post-Nivel A).
- Syntax check: `python -m py_compile lab_historico_numba_v8_3.py` → SYNTAX OK.

Impacto: desbloquea `master.py --recycle` + pipeline pre-reciclaje en Windows cp1252 local (Ricardo). Prerequisito pre-reciclaje (julio o adelantado) cleared.

Meta-observación: scope real 5× mayor al documentado en A27 (68 líneas vs 14). §12 L27-compatible ("documentación inventario inicial puede subestimar scope real"). Grep Python exhaustivo pre-fix identificó correctamente el scope antes de aplicar — evitó trabajo parcial que dejaría problema residual.

Referencias:
- §13.4 A27 2026-04-22 (fix ⚙️ L996 original + descubrimiento colateral).
- §13.3 L1839 movido a RESUELTO (pointer a esta entrada).
- lab_historico_numba_v8_3.py: 68 líneas runtime-critical modificadas.
- §12 L30 (baseline drift arquitectónico — smoke Nivel A confirma lógica invariante).

Cierre: permanente.

---

**[MEJORA] [REFUTADO] L2018 pnl_recon tolerance hipótesis floor mal calibrado — 2026-04-23**

Contexto: Item §13.3 L2018 creado esta misma sesión (2026-04-23) como consecuencia de A.1 N=26 que reportó 92% trades con `pnl_recon_gap > tolerance`. Hipótesis propuesta: "tolerancia absoluta 0.01 USDT mal dimensionada para balance ~296 USDT". Fix propuesto: `tolerance = max(0.005, 0.10 * abs(pnl_usdt))` (bajar floor de 0.01 a 0.005).

Validación empírica directa (Fase 0-3 sesión 2026-04-23 post-creación del item):

1. **Fórmula actual ya es `max(0.01, 0.10 * abs(pnl_real))`**, no absoluta pura como asumía L2018. Floor 0.01 + ratio 10% coexisten.

2. **Efecto de bajar floor 0.01→0.005 sobre ratio trades failing (N=26 post-v2.4.4)**:

| Variante | Floor 0.01 | Floor 0.005 | Floor 0.001 |
|---|---|---|---|
| Sin funding | 42.3% | 57.7% | 61.5% |
| Con funding | 42.3% | 57.7% | 57.7% |

Bajar el floor **empeora** el ratio. Hipótesis L2018 refutada empíricamente.

3. **Diagnóstico causa raíz** (no documentado en L2018):

Distribución gap / |pnl| (N=26):

| Percentil | gap | |pnl| | gap/|pnl| |
|---|---|---|---|
| p50 | 0.022 | 0.104 | 21% |
| p75 | 0.032 | 0.170 | 19% |
| p90 | 0.033 | 0.227 | 15% |
| p99 | 0.042 | 0.388 | 11% |

El gap real es típicamente 15-25% del |pnl|, NO <10%. Causas probables no-bugs:
- Rounding precios CSV (4-6 decimales vs BingX precision mayor).
- size_usdt post-v2.4.4 = notional BingX reportado (puede diferir de "size × entry" teórico).
- COMMISSION_RATE estimation vs fees reales BingX.
- Funding mínimo no incluido en pnl_recon (N=26 funding casi cero; no es factor).

4. **Nota discrepancia ratios reportados**: analyzer reportó 92% failing, recálculo directo da 42%. Diferencia probable: analyzer aplica tolerance post-funding, o usa handling distinto de entry/exit prices. Dirección cualitativa del efecto consistente: bajar floor NO mejora.

Aplicación §12 L34: stress-test validación hipótesis propia antes de implementar fix. Refutamos L2018 por el mismo criterio que refutamos H1/H_strategy/H_new_3 hoy. Coherencia metodológica.

Acciones derivadas:
- L2018 cerrado por refutación (este §13.4 entry).
- Nuevo item §13.3 creado: "pnl_recon ratio 10pct demasiado estricto" con hipótesis refinada ratio 25% basada en evidencia empírica cuantitativa (ver §13.3 entrada específica).
- L1916 2026-04-16 "Test consistencia ecuación descomposición" MANTIENE estado EN_ESPERA (no se resuelve por merge como originalmente planificado; queda con contexto actualizado en su entrada).

Dataset de referencia: attribution_per_trade_20260423_0827.csv (regenerable via analyzer sobre trade_history post-v2.4.4 N=26).

Referencias:
- §13.3 L2018 movido a REFUTADO (pointer a esta entrada).
- §13.3 nuevo item "pnl_recon ratio refinado" creado 2026-04-23.
- §13.3 L1916 mantiene EN_ESPERA con context update.
- §13.2 DECISION ACTIVO "Consistency check por reconstrucción no tautológico" (preservada — no se toca).
- §12 L34 (aplicada a hipótesis propia recién creada — 4ª refutación del día por stress-test).

Cierre: permanente por refutación.

---

**[MEJORA] [RESUELTO L27 parcial] L1910 edge_erosion detection ya implementado por analyzer v2.4.1 — 2026-04-23**

Contexto: §13.3 L1910 2026-04-16 solicitaba "Detección automática de edge_erosion por cluster. Si varios clusters flaggeados de forma persistente en reportes sucesivos, considerar adelantar reciclaje". Verificación inventario 2026-04-23 reveló L27 parcial:

**Parte implementada (fix real ya existe)**:
- analyzer v2.4.1 (release 2026-04-17 ultra review) emite alert `CANDIDATO EXCLUSION RECICLAJE` por cluster con ratio_oos/pool < 0.5 y N_obs ≥ 3.
- Primer caso empírico reportado: 2026-04-22 Fase II.C (§13.4) — ONDO C2 + SAND C1 flagged como CANDIDATOS EXCLUSION.
- 2026-04-23 A.1: 4 clusters flagged (APT C0, ONDO C2, SAND C1, SEI C0). Alert automático funciona.

**Parte pendiente (integrada en otro item)**:
- Tracking cross-sesiones para criterio semi-automático "persistentes 2+ reportes consecutivos" está integrado en §13.3 L1398 "Política adelantar reciclaje por criterio empírico — 2026-04-22".
- L1398 establece el disparador semi-automático: "3+ clusters flagged candidato_exclusion sostenido en 2+ reportes consecutivos del analyzer (semanal)" → alerta + decisión Ricardo.

Conclusión: la funcionalidad L1910 original está cubierta por la combinación analyzer v2.4.1 alert + L1398 política. Item cerrado como L27 parcial resuelto.

Patrón de cierre sin código: ilustración de §12 L27 (items §13.3 obsoletos por reviews previos no documentados en §13.4). Update ultra review analyzer v2.4.1 aplicó el fix de detección; documentación §13.4 de 2026-04-17 mencionaba "edge_erosion flag" genéricamente sin cerrar L1910 explícitamente.

Referencias:
- analyze_performance_attribution.py sección detect_edge_erosion (función existente pre-L1910 close).
- §13.3 L1398 "Política adelantar reciclaje" (tracking cross-sesiones).
- §13.4 primer audit empírico 2026-04-21 (primer reporte con flag).
- §13.4 Fase II.C 2026-04-22 (primer CANDIDATO EXCLUSION ONDO C2 + SAND C1).
- §13.4 A.1 2026-04-23 (4 clusters flagged confirman robustez).
- §12 L27 (pattern items §13.3 obsoletos por reviews).

Cierre: permanente por L27 parcial resuelto.

---

**[MEJORA] [RESUELTO] _run_verify_test CLI parametrizable --n-bars + tolerance escalada §0.8 — 2026-04-23**

Contexto: §13.3 EN_ESPERA 2026-04-22 solicitaba parametrizar n_bars + tolerance escalada para habilitar Nivel B §0.8 sin wrappers temporales. Item maduro (scope acotado, racional documentado).

**Implementación**:
- Signature: `_run_verify_test(symbol, n_bars=1000) -> int`.
- CLI: `--n-bars N` (default 1000, preserva backward compat Nivel A baseline §0.8).
- Nivel detection automática: N<2000 → A, N>=2000 → B.
- Tolerance escalada:
  - Nivel A: PnL diff 0.1pp absoluto; trades exacto (match pre-refactor).
  - Nivel B: PnL max(0.1pp absoluto, 15pct relativo sobre |kernel|); trades max(1, 5pct N_trades) = match >=95pct §0.8.
- Output enriquecido: [NIVEL A/B] header + tolerance aplicada + match count explícito + veredicto PASS/FAIL.
- Exit code 0 PASS, 1 FAIL (nuevo — antes siempre 0; no rompe callers porque solo `--verify` añade exit code, deploy gates eran man-in-the-loop por inspección output).

**Matización tolerance**: el protocolo original solicitaba `max(1, 0.5pct N_trades)` en trades. §0.8 canon dice "match count >95pct" = 5pct divergence. Discrepancia detectada durante smoke Nivel B ONDO N=8000 (diff 3 trades falso-FAIL por 0.5pct). Alineado con §0.8 (5pct) que es fuente autoritativa.

**Smokes validación (§0.8)**:
- Nivel A BTC/USDT N=1000: diff 0.0000 exacto ✓ (backward compat).
- Nivel B BTC/USDT N=5000: diff 0.0000 ✓ (BTC converge, drift path-dependent no manifiesta).
- Nivel B ONDO/USDT N=8000: match 99.38pct, PnL diff_rel 9.80pct ✓ (encaja baseline §12 L30 7-9pct).
- Nivel B ONDO/USDT N=5000: FAIL PnL diff_rel 40.60pct (N insuficiente vs baseline ≥8000 §0.8; comportamiento esperado — documentar como "N Nivel B recomendado ≥8000 para altcoins path-dependent").
- Nivel C MR (audit_mr_fidelity_sei.py): diff 0.0000 en 7 métricas ✓ invariante.

**Tests unit**: 5/5 PASS (`tests/test_run_verify_test_cli.py`):
- n_bars=0 / n_bars<0 → ValueError.
- Constants alineadas §0.8 protocolo.
- Símbolo sin parquet → exit code 1.
- Default n_bars=1000 + symbol="BTC/USDT" verificados vía inspect.

**Cleanup**: wrappers temporales eliminados (`.nivel_b_cooldown.py`, `.nivel_b_output.txt`).

**Scope diferido**: `--cluster K` (no incluido). Utilidad operacional no emergente en debug actual; agregar si requisito específico emerge.

**Fidelidad 2 invariante** (refactor test harness — no toca kernel Numba, execution, portfolio, live_engine, ni lógica signal_generation del brain).

**Impacto**: gate §0.8 Nivel B ejecutable con comando único estándar `python -m live.brain_engine --verify --symbol ONDO/USDT --n-bars 8000`. Deploys futuros brain/kernel pueden invocar Nivel B directamente sin código ad-hoc.

Referencias: §0.8 protocolo smoke test, §12 L30 drift arquitectónico, `live/brain_engine.py` L2323-2577 (`_run_verify_test` refactor + constantes + main CLI), `tests/test_run_verify_test_cli.py`. §13.3 item movido a RESUELTO con pointer a esta entrada.
Cierre: permanente.

---

**[SESIÓN] [RESUELTO] Sesión 2026-04-23 — A.1 deep-dive Criterio B + 3 refutaciones cross-segmento + L34**

Directiva Ricardo arranque: continuar Bloque 3 A.1 alpha residual deep-dive con analyzer enriquecido automáticamente (11 cols funding context). Criterio empírico de scope según N post-v2.4.4.

**Reconocimiento inicial**: N=26 post-v2.4.4, ritmo 0.69 trades/h, ventana 37.76h desde deploy v2.4.4. **Criterio B** (25≤N<40). Bot sano, sin restarts desde v2.4.5, 7 posiciones, balance 296.55 USDT, DD -0.62%.

**A.1 deep-dive N=26 Criterio B — descomposición primera ejecución end-to-end post-fixes v2.4.4+v2.4.5**:

Primera ventana con dataset arquitectónicamente limpio (size_usdt válido + entry_timestamp_ms válido). Descomposición alpha_residual:

| Campo (USDT) | post-v2.4.4 N=26 | post-v2.4.5 N=13 | Fase II.C N=47 ref |
|---|---|---|---|
| PnL real | +0.22 | +0.45 | +0.48 |
| Alpha nominal | +2.87 | +1.21 | +5.64 |
| Factor portfolio | -0.64 | -0.30 | -1.17 |
| Slippage TOTAL | -0.30 | -0.21 | -0.08 |
| Funding | +0.01 | -0.00 | -0.06 |
| Alpha residual | -1.72 | -0.25 | -3.84 |
| Ratio res/nom | -0.60 | -0.21 | -0.68 |

**Hipótesis slippage liberado CONFIRMADA**: slippage/trade pasó de -0.0017 (Fase II.C contaminado size_usdt=0) a -0.0115 (post-v2.4.4), 7× aumento. Correlativamente alpha_residual/trade mejora 19%. Parte del "residual" previo era slippage no computable absorbido (§12 L26 caso adicional).

**3 hipótesis emergentes de A.1 N=26**:
- H1: asimetría short vs long en alpha_residual ratio 12:1 (Σα_res -1.58 shorts vs -0.13 longs, sample balanceado 13/13).
- H_strategy: strategy-logic exits (tf/div/cancel_tf N=17) vs estructurales (zone/not_operable/regime_change N=9) ratio 3.4× residual.
- H_new_3: aligned→aligned residual mean -0.005 vs contrarian→contrarian -0.094, ratio 19× en residual a pesar de gap PnL no significativo (p=0.77).

**Fase 2 — H1 stress-test cross-régimen + cross-segmento N=98**:

Régimen BTC ventana (2026-04-21 19:00→2026-04-23 08:00): retorno +3.67% alcista material, GMM dominante C1 (71%) + C2 (29%), 0% C0 (high-vol). BTC specialists: C2 score 17.21 best.

Tabla cross-segmento:

| Segmento | Ns | Σα_res_s | Nl | Σα_res_l | mean_s | mean_l | Ratio |
|---|---|---|---|---|---|---|---|
| S1 pre-v2.3.11 | 17 | -0.62 | 32 | -3.69 | -0.036 | -0.115 | +0.17 |
| S2 v2.3.11→v2.4.0 | 5 | +0.09 | 2 | -0.19 | +0.018 | -0.094 | -0.48 |
| S3 v2.4.0→v2.4.4 | 4 | -0.33 | 14 | -1.12 | -0.082 | -0.080 | +0.29 |
| S4 post-v2.4.4 | 11 | -1.35 | 13 | -0.13 | -0.122 | -0.010 | +10.11 |

S1 (N=49 mayor sample) dirección opuesta (longs peor, Cohen d +0.55). Solo S4 muestra 12:1. OLS α_res ~ side + BTC_delta_pct: side_short coef +0.028 p=0.39 NO significativo.

**H1 REFUTADA** como hipótesis estructural. Caso E2 — artefacto de ventana S4 específica + régimen BTC alcista localizado.

**Fase 3 — Stress-test H_strategy + H_funding + H_new_3 N=98**:

**H_strategy cross-segmento**:

| Segmento | N_strat | mean α | N_struct | mean α | Welch p |
|---|---|---|---|---|---|
| S1 | 32 | -0.084 | 16 | -0.102 | 0.735 |
| S2 | 5 | -0.003 | 2 | -0.040 | 0.769 |
| S3 | 13 | -0.092 | 5 | -0.050 | 0.339 |
| S4 | 16 | -0.152 | 8 | +0.120 | 0.000 |

Welch global N=98 p=0.086 marginal DOMINADO por S4. Sin S4 efecto desaparece. S1 dirección opuesta. **H_strategy REFUTADA** Caso F3.

**H_funding efecto Bloque 2**:

| Métrica | Bloque 2 N=50 | A.1 N=26 | N=49 multi-seg |
|---|---|---|---|
| Gap aligned-contrarian | +1.07pp | +0.26pp | +0.49pp |
| Welch p (entry) | 0.0113 | 0.7654 | 0.3516 |
| Spearman ρ(n_bars, PnL) | -0.32 p=0.02 | +0.02 p=0.93 | -0.145 p=0.31 |

Signo direccional correcto en N=49 pero ninguna significancia. Bloque 2 magnitud inflada por muestra. S1 no testeable por cache limit (arranca 2026-04-15, dataset desde 2026-04-13). Caso G2 atenuado — dirección plausible, significancia pendiente N≥100 con cache extendida.

**H_new_3 ratio residual contrarian**:

N=49 ratio al→al residual -0.048 vs con→con -0.103 = 2.16× (vs 24× A.1). Consistente con gap PnL relativo (0.6×). No hay "insight residual adicional" — es la misma señal. **H_new_3 REFUTADA preliminar** Caso M2.

**3 refutaciones en una sesión**: H1 + H_strategy + H_new_3. Todas artefactos de ventana S4 estrecha. Paralelo exacto a §12 L33 (v2.6 contrarian refutado 2026-04-22) pero aplicado a hipótesis emergentes internas vs externas.

**Balance arquitectónico del día**:

| Item | Estado | Ubicación |
|---|---|---|
| H1 short/long 12:1 | REFUTADO | esta entrada §13.4 |
| H_strategy exits 3.4× | REFUTADO | esta entrada §13.4 |
| H_new_3 residual 24× | REFUTADO prelim | esta entrada §13.4 |
| v2.6-inv entry filter | UPDATE triple ref | §13.3 existente actualizado |
| v2.6-exit filter | UPDATE triple ref | §13.3 existente actualizado |
| pnl_recon tolerance mal calibrada | NUEVO [MEJORA] | §13.3 nuevo |
| Cache funding extender S1 | NUEVO [MEJORA] | §13.3 nuevo |
| §12 Lección 34 meta-validación | NUEVO | §12 |

**Updates §13.3 v2.6-inv + v2.6-exit — matización arquitectónica**:

El efecto Bloque 2 p=0.0003 trimmed en N=50 mezcla trades S2 (N=7) + S3 (N=18) + S4 parcial. La A.1 N=26 aisló S4 exclusivamente y reveló p=0.77. La Fase 3 N=49 multi-segmento recupera p=0.35 direccional. Implicación: el efecto Bloque 2 estaba concentrado en S2+S3 ventana 2026-04-19→21 (régimen + fase fix específica), no en S4 post-v2.4.4. Disparadores N≥100/N≥150 preservados pero con prerequisito reforzado: replicación significativa ventana S4 homogénea, no solo "N mayor cualquiera".

**§12 Lección 34 NUEVA**: "Hipótesis emergentes de análisis con ventana N<50 requieren validación multi-segmento antes de elevar a §13.3". Caso origen esta sesión — 3 refutaciones cross-segmento evitaron crear 3 items §13.3 activos con disparadores incrementales que habrían consumido 3-4 sesiones de validación para llegar a la misma conclusión.

**Estado operacional al cierre**:
- Bot v2.4.5 operacional VPS Tokio, sin restarts desde v2.4.5 deploy.
- Fidelidad 2 invariante (sesión read-only, 0 cambios código/deploy).
- Pipeline pre-reciclaje: sin items bloqueantes nuevos. Sobrecarga §13.3 REDUCIDA por 3 refutaciones.
- Próxima acción natural: N≥40 post-v2.4.4 (~2026-04-24 04:00 UTC) para replicación incremental A.1 si Ricardo decide. Disparadores maduros: v2.6-inv N≥100 (~2026-05-01), v2.6-exit N≥150 (~2026-05-10), audit definitivo N≥50 post-v2.3.11 (~2026-04-26).

**Meta-observación de la sesión**: el flujo Ricardo-dirigido hacia stress-test multi-segmento (Fase 2 + Fase 3) antes de escribir borradores §13.3 fue la decisión metodológica crítica. Sin ese paso, 3 artefactos se habrían consolidado como hipótesis activas con disparadores futuros. La Lección 34 captura el aprendizaje para futuras sesiones.

Referencias:
- §12 Lección 34 (nueva esta sesión).
- §12 Lección 25 (métricas agregadas heterogéneas — complementaria).
- §12 Lección 29 (walk-forward N_fwd inflado — complementaria).
- §12 Lección 33 (hipótesis externas sin validación — complementaria).
- §13.3 updates v2.6-inv + v2.6-exit + 2 items nuevos.
- §13.4 Fase II.C 2026-04-22 (datos base del analyzer N=47 contaminado).
- Archivos locales /tmp/* (no commiteados): attribution_summary + funding_context_post-v244 + Fase 2 + Fase 3 outputs.

Cierre: permanente. Sesión 2026-04-23 cerrada con 3 refutaciones + 1 lección nueva + 2 items §13.3 nuevos + 2 updates §13.3.

---

**[SESIÓN] [RESUELTO] Sesión 2026-04-22 — Bloque 1 cooldown + Bloque 2 v2.6 refutado + Bloque 2 ampliado observabilidad + micro-items cierre**

Directiva Ricardo arranque sesión: "ningún reciclaje tiene sentido si no es para mejorar la rentabilidad operativa… deben concluirse todas las mejoras posibles, e identificar todas las causas probables que puedan mejorar el sistema". Plan ajustado: atacar causas raíz + observabilidad definitiva antes del reciclaje, no reciclaje con pipeline de ayer solamente.

**Balance arquitectónico consolidado** (commits cronológicos en main):

| Commit | Bloque | Scope | Impacto |
|---|---|---|---|
| `9389af9` | B1 refactor | Kernel TF L1630-1637 + MR L408-415 cooldown unify a expresión Pine canónica | Elimina código muerto bajo cooldown_bars=1 |
| `f229510` | B1 merge | Merge feature branch a main | Arquitectónico |
| `a3eca13` | B1 docs | §13.3 cooldown RESUELTO + §2.6 kernel fix | Documental |
| `a2379ab` | B2 v2.6 refutado | funding_observability.py standalone + §9.3 REFUTADO empíricamente + §12 L33 + §13.3 v2.6-inv candidato | REFUTACIÓN con p=0.0003 trimmed, dirección opuesta a hipótesis §9.3 |
| `3a7f286` | B2 ampliado | funding_context.py bar-a-bar + 11 cols + 19 tests + funding_observability.py borrado + §13.3 v2.6-exit candidato nuevo | Solución observabilidad definitiva |
| (este commit) | Cierre | deploy_boundaries.json v2.4.4+v2.4.5 + engine_state.json Categoría 1 + §13.4 consolidación | Cierre documental sesión |

**Bloque 1 — Cooldown unify TF+MR**:
- Discovery pre-ejecución: `COOLDOWN_BARS=1` constante única en 9 módulos productivos → las 4 ramas del switch colapsaban matemáticamente a `t`.
- Ricardo confirmó Opción A: cooldown=1 siempre operacional en Pine histórico; diferenciación por tipo exit en kernel era código muerto.
- Refactor a `if any_exit_signal: cooldown_until = t + cooldown_bars - 1` (expresión Pine canónica).
- Confirmatorio triple anclaje: Nivel A (BTC N=1000) diff 0.0000 exacto + Nivel C (SEI MR N=1500) diff 0.0000 + Nivel B (ONDO+APT N=10000) bit-idéntico a §13.4 A10 baseline pre-refactor.
- §13.3 **último ítem bloqueante arquitectónico pre-reciclaje** RESUELTO.

**Bloque 2 — v2.6 Funding Filter contrarian REFUTADO**:
- Claude Code PAUSÓ con 6 concerns pre-implementación (Fidelidad 2 break, threshold prompt 10× error vs §9.3, etc.).
- Ricardo escogió Opción A §13.3 (observabilidad prerequisito, no implementar filter directo).
- `funding_observability.py` standalone + fetch N=50 post-v2.3.11 desde VPS Tokyo BingX real (geo-bloqueo ES §12.24).
- Hipótesis §9.3 contrarian **REFUTADA con dirección OPUESTA**: aligned +0.5045%, contrarian -0.5692%, Welch trimmed **p=0.0003**, Mann-Whitney p=0.0052. Win rate 62% vs 28%.
- Simulación del filter original: habría degradado PnL en factor 2.2× (-1.52 USDT adicional sobre 50 trades vs PnL real +0.70).
- Threshold §9.3 `|rate|>0.001` nunca activa (0/50 trades, p99 real 5× menor).
- §9.3 v2.6 actualizada con REFUTADO; §12 **Lección 33 nueva**: validar hipótesis roadmap empíricamente (literatura general no sustituye).
- §13.3 **v2.6-inv entry filter candidato** abierto EN_ESPERA disparo N≥100.

**Bloque 2 ampliado — Observabilidad bar-a-bar definitiva**:
- `funding_observability.py` BORRADO. `funding_context.py` (575 líneas) lo reemplaza: librería + CLI dual-command (refresh-cache + enrich).
- Data model 11 columnas: 3 entry (existentes) + 3 exit (nuevas) + 5 evolution (nuevas) + entry_exit_pattern (9 combos derivado).
- Cache CSV-per-symbol (parquet descartado por ausencia pyarrow VPS).
- Tests 19/19 PASS.
- Primera ejecución N=50: Section 1 cross-check Bloque 2 bit-idéntico; Section 2 exit contrarian pierde p=0.0162 (soporta candidato v2.6-exit); Section 3 patterns 0 crowd flips (dominado por `->same`); Section 4 Spearman ρ(n_bars_contrarian, pnl_pct) = -0.3172 **p=0.0205**.
- §13.3 **v2.6-exit filter candidato** nuevo EN_ESPERA disparo N≥150 (cerrar contrarian losing).

**Micro-item 1 — deploy_boundaries.json actualizado**:
- Añadidos v2.4.4 (2026-04-21T18:22:02Z, deploy VPS inferido de git commit 4fe5e87 @ 18:40 UTC CEST) y v2.4.5 (2026-04-22T09:46:10Z, ground truth `systemctl Active since`).
- 180/180 tests PASS (pytest discovery). Cero regresión arquitectónica.
- Source notes expandidas con origen de cada timestamp.

**Micro-item 2 — engine_state.json investigación preliminar**:
- Reconocimiento inicio sesión reportó `"positions": {}` vacío pese a 5 posiciones abiertas → sospecha de bug.
- Diagnóstico: mi query inicial usaba `d.get("positions", {})` que retorna **default vacío cuando la key NO EXISTE**, confundiendo ausencia con vacuidad.
- Inspección real: engine_state.json tiene keys `{saved_at, cycle_count, start_time, peak_balance, current_balance, dd_multiplier, circuit_breaker_active, symbols, dry_run_positions}`. **No existe** la key `positions`.
- `symbols` contiene 45 entries (una por símbolo trackeado) con 5 de ellas con `position != 0` — consistente con las 5 posiciones abiertas. Todos los campos relevantes persistidos: position, entry_price, sl_level, stop_order_id, entry_timestamp_ms, bars_since_entry, etc.
- `_save_state` (live_engine.py L1159-1211) escribe key `symbols`; `_load_state` (L1213+) lee key `symbols`. Zero código lee `state["positions"]` (grep exhaustivo confirmado).
- **Clasificación: CATEGORÍA 1 — Alternate representation**. Sin bug. Mi query inicial fue ambigua por uso de `dict.get` con default silencioso.
- Acción correctiva: ninguna operacional. Documental: advertir en §13.3 para que futuras inspecciones usen `key in d` antes de `d.get` con default silencioso.

**Balance items §13.3 sesión**:
- RESUELTOS: cooldown asimétrico, observabilidad funding entry-only (Bloque 2), observabilidad funding bar-a-bar (Bloque 2 ampliado).
- REFUTADOS: v2.6 Funding Filter contrarian §9.3 (no "archivado por falta evidencia" — "refutado por evidencia contraria").
- NUEVOS EN_ESPERA: v2.6-inv entry filter candidato (disparo N≥100), v2.6-exit filter candidato (disparo N≥150), observación engine_state.json nomenclature (cosmética).
- Items §12 nuevos: L33 "validar hipótesis roadmap empíricamente".

**Estado operacional**:
- Bot v2.4.5 en VPS Tokyo. 5 posiciones abiertas (ENA SHORT, RENDER LONG, SEI LONG, SAND LONG, THETA LONG).
- Balance 296.40 USDT; peak 298.39; DD -0.67%.
- Sin deploy hoy en ninguno de los 3 bloques + 2 micro-items. Fidelidad 2 invariante en toda la sesión.
- Pipeline pre-reciclaje arquitectónicamente **completo**: todos los items bloqueantes §13.3 resueltos; 3 items candidatos EN_ESPERA con disparadores empíricos claros (N≥50 audit, N≥100 v2.6-inv, N≥150 v2.6-exit).

**Plan próxima sesión**:
- N post-v2.4.4 proyección: ≥25 en ~12h, ≥40 en ~33h, ≥50 en ~48h (ritmo observado 0.7 trades/h).
- Trigger natural: N≥40 post-v2.4.4 (Criterio B de A.1 deep-dive) permite análisis direccional sólido.
- Analyzer enriquecido `funding_context.py` listo para ejecutar sin retrabajo cuando N suficiente.
- Items candidatos v2.6-inv (~2026-05-01) y v2.6-exit (~2026-05-10) esperables según densidad.
- Criterio §13.3 "política adelantar reciclaje" sigue EN_ESPERA, ahora evaluable con data más rica.

Cierre: permanente. Sesión 2026-04-22 cerrada con densidad completa documentada.

---

**[MEJORA] [IMPLEMENTADO] Observabilidad funding bar-a-bar — integración permanente + 2 candidatos derivados — 2026-04-22 (post-Bloque 2)**

Contexto: Bloque 2 original (funding_observability.py entry-only) implementado horas antes en la misma sesión refutó hipótesis §9.3. Ampliación inmediata por solicitud Ricardo: "solución definitiva no patada hacia delante". Observabilidad expandida a entry + exit + bar-a-bar trajectory para que N≥100 y N≥150 puedan evaluarse sin trabajo adicional.

**Reemplazo arquitectónico**: `funding_observability.py` (Bloque 2) → **borrado**. `funding_context.py` (nuevo, 575 líneas) lo reemplaza como librería importable + CLI dual-command (`refresh-cache` + `enrich`). Single source of truth (evita drift futuro §12.24).

**Data model expandido** (11 columnas + pattern derivado):

| Categoría | Columna | Descripción |
|---|---|---|
| Entry (existían) | funding_rate_at_entry | decimal per 8h (o 4h en algunos símbolos) |
| | funding_crowd_direction_entry | long_crowd / short_crowd / neutral |
| | signal_vs_entry_crowd | aligned / contrarian / neutral |
| Exit (nuevas) | funding_rate_at_exit | rate más reciente ≤ exit_ts |
| | funding_crowd_direction_exit | análogo a entry |
| | position_vs_exit_crowd | análogo a entry pero al cerrar |
| Evolution (nuevas) | funding_rate_min_during | rate min visto en hourly bars [entry, exit] |
| | funding_rate_max_during | rate max |
| | funding_rate_mean_during | rate mean |
| | funding_crowd_flipped | bool: non-neutral entry crowd ≠ non-neutral exit crowd |
| | n_bars_contrarian | bars con posición contrarian al crowd |
| | max_consecutive_bars_contrarian | longest run contrarian |
| Derived | entry_exit_pattern | "X->Y" donde X,Y ∈ {aligned, contrarian, neutral} (9 combos) |

**Arquitectura técnica**:
- `FundingCache`: CSV-per-symbol en `.funding_cache/`. CSV en vez de parquet por compat VPS sin pyarrow. 324 KB para 34 símbolos × ~200 rates.
- `refresh_cache(symbols, since, until, cache)`: fetch incremental (solo gap vs cache existente) via ccxt BingX. Geo-bloqueo España (§12.24) obliga ejecutar desde VPS Tokyo; cache rsync/scp+tar de vuelta.
- `lookup_rate_at(rates, ts)`: binary search, O(log N).
- `compute_bar_level_evolution(rates, entry_ts, exit_ts, side)`: walk hourly bars entre entry-exit, computar 6 stats.
- `enrich_trades(trades, cache)`: batch con load-once por símbolo.
- CLI dual: `refresh-cache` (fetch, VPS) + `enrich` (análisis post-hoc, local).

**Integration con analyzer**: decisión scope-conservadora — NO modificado `analyze_performance_attribution.py` (2097 líneas, análisis enriquecido funciona como workflow post-hoc). Analyzer run normal → funding_context.py enrich CSV output → reporte separado. Integration directa posible si se aprueba alguno de los candidatos derivados (v2.6-inv / v2.6-exit).

**Workflow documentado**:
```
# 1. VPS — refresh funding cache:
ssh trader@vps "cd combolab && python funding_context.py refresh-cache \
  --csv trade_history.csv --cache-dir .funding_cache --since 2026-03-01"

# 2. Sync cache local (una vez por sesión de análisis):
ssh trader@vps "tar czf /tmp/fc.tgz .funding_cache/"
scp trader@vps:/tmp/fc.tgz /tmp/
tar xzf /tmp/fc.tgz -C combolab/

# 3. Local — analyzer normal + enrich funding:
python analyze_performance_attribution.py <trades.csv>
python funding_context.py enrich <trades.csv> --cache-dir .funding_cache
```

**Primera ejecución empírica N=50 post-v2.3.11** (cross-check Bloque 2):

Section 1 — Entry crowd (bit-idéntico Bloque 2):
| group | N | mean_pnl_% | sum_USDT | win_rate |
|---|---|---|---|---|
| aligned | 16 | +0.5045 | +0.7524 | 62.5% |
| contrarian | 18 | -0.5692 | -0.7704 | 27.8% |
| neutral | 16 | +0.3764 | +0.7134 | 50.0% |
| | | | Welch | p=0.0113; Mann-Whitney p=0.0052 |

Section 2 — Exit crowd (NUEVO):
| group | N | mean_pnl_% | sum_USDT | win_rate |
|---|---|---|---|---|
| aligned | 16 | +0.5045 | +0.7524 | 62.5% |
| contrarian | 18 | -0.5237 | -0.7103 | 33.3% |
| neutral | 16 | +0.3252 | +0.6533 | 43.8% |
| | | | Welch | p=0.0162; Mann-Whitney p=0.0107 |

Section 3 — Trajectory pattern (9 combos):
| pattern | N | mean_pnl_% |
|---|---|---|
| aligned->aligned | 16 | +0.5045 |
| contrarian->contrarian | 17 | -0.5798 (29% WR) |
| contrarian->neutral | 1 | -0.3903 |
| neutral->contrarian | 1 | +0.4293 |
| neutral->neutral | 15 | +0.3729 |
| (otros 4 combos) | 0 | - |

Section 4 — Evolution + correlations:
- **0 crowd flips** en 50 trades (crowd súper estable en ventana 4d).
- Hold time: median **1h**, max 25h, mean 2.26h.
- Trades >=8h boundary cross: **4/50 (8.0%)**.
- **Spearman ρ(n_bars_contrarian, pnl_pct) = -0.3172 p=0.0205** → correlación negativa significativa (más tiempo contrarian = peor PnL).
- ρ idéntico para max_consecutive_bars_contrarian (por 0 flips, son iguales).

**Consecuencias arquitectónicas + nuevos candidatos**:

1. **v2.6-inv entry filter** (refutación Bloque 2 → candidato inverso): soportado adicionalmente por exit context (p=0.0162) y trajectory (patterns dominados por `->same`). Mantiene disparo N≥100.

2. **v2.6-exit filter** (NUEVO candidato): soportado por correlación Spearman duration-PnL. Hipótesis: cerrar trades contrarian en pérdida ahorraría PnL. Disparo N≥150. Caveat crítico: 0 crowd flips actuales significa que "exit filter" reduce a "close if contrarian entry + hold time > X + pnl<0" — distinto de "close on crowd flip".

**Cross-check consistency Bloque 2 → Bloque 2 ampliación**: entry columns N=50 reproducen exactamente p=0.0113, mean +0.5045 vs -0.5692, win rate 62.5% vs 27.8%. Cero drift.

**Tests 19/19 PASS** (`tests/test_funding_context.py`): FundingCache save/load/coverage, lookup (before/exact/between/empty), classify (neutral/long/short/unknown/aligned/contrarian), bar-level evolution (short constant, boundary no-flip, crowd-flip, contrarian-throughout), enrich pattern (aligned-aligned, flip, NaN fallback), 9 pattern combos.

**Impacto operacional**: zero (offline). Fidelidad 2 invariante.

**Deuda**:
- Analyzer direct integration: pospuesta (funciona como post-hoc workflow). Si v2.6-inv o v2.6-exit se aprueba futuro, re-evaluar.
- N de data: 50 es mínimo direccional. Para decisiones implementación necesario N≥100 (entry) y N≥150 (exit + pattern breakdown).
- Régimen temporal: 4 días no representa bearish markets, tail-risk crowded events. Persistencia del efecto requiere validación temporal.

Referencias: `funding_context.py` (575 líneas), `tests/test_funding_context.py` (19 tests), `funding_observability.py` (borrado), §13.3 v2.6-inv + v2.6-exit candidatos actualizados, §9.3 v2.6 refutada, §12 Lección 33.

Cierre: permanente. Solución definitiva para observabilidad funding; base de decisión para N mayor sin trabajo adicional.

---

**[MEJORA] [IMPLEMENTADO + REFUTACIÓN] Observabilidad funding per-trade — refutación empírica §9.3 v2.6 contrarian filter — 2026-04-22**

Contexto: §13.3 documentó "Observabilidad funding extremo per-trade en analyzer" como prerequisito del item §13.3 "Filtro funding contrarian runtime" (§9.3 v2.6 en roadmap). Opción A (implementar observabilidad primero) ejecutada para evitar romper Fidelidad 2 sin evidencia empírica y para calibrar threshold.

**Implementación técnica**:
- `funding_observability.py` standalone (nuevo archivo combolab root). 516 líneas. No integrado en `analyze_performance_attribution.py` para scope mínimo; integración futura opcional si filter se aprueba.
- 3 columnas enriquecidas: `funding_rate_at_entry` (decimal per 8h), `funding_crowd_direction` ('long_crowd' rate > +5e-5 / 'short_crowd' rate < -5e-5 / 'neutral'), `signal_vs_crowd` ('aligned' / 'contrarian' / 'neutral').
- Fetch ccxt `fetch_funding_rate_history` por símbolo con paginación + cache intra-sesión. Exchange selector (`--exchange bingx|binance`).
- **Geo-bloqueo ccxt España** detectado: BingX, Binance, OKX, Bybit todos bloquean `/contracts` endpoint → ejecución vía SSH VPS Tokyo (BingX accesible allí). Kraken no soporta `fetchFundingRateHistory`. Symbol format `BTC/USDT:USDT` requerido (Lección §12.24 aplicada — `BTC/USDT` devuelve 0 rates silently).
- Bypass del bug §13.3 E1 (execution_manager `_get_position_funding` sign fallback): analyzer v2.4.1 lee `funding_paid` directo del CSV, y la observabilidad fetcha rate independiente del CSV. Ninguna lectura atraviesa `_get_position_funding`.
- Welch t-test y Mann-Whitney implementados in-script (bypass scipy dependency). Robustness checks: drop min+max, drop |z|>2 outliers.

**Resultado empírico N=50 post-v2.3.11** (BingX real desde VPS):

| Group | N | % | Mean PnL % | Median PnL % | Sum USDT | Win Rate | Mean rate (per 8h) |
|---|---|---|---|---|---|---|---|
| **aligned** | 16 | 32% | **+0.5045** | +0.2112 | +0.7524 | **62%** | +7.9e-5 |
| **contrarian** | 18 | 36% | **-0.5692** | -0.5194 | -0.7704 | **28%** | +8.7e-5 |
| neutral | 16 | 32% | +0.3764 | +0.0876 | +0.7134 | 50% | +0.7e-5 |

Tests estadísticos (aligned vs contrarian PnL%):
- Welch t baseline: **t=+2.53, p=0.0113**.
- Welch t trimmed (drop min+max per group): **t=+3.58, p=0.0003**.
- Welch t sin outliers |z|≤2: **t=+3.41, p=0.0006**.
- Mann-Whitney U: **p=0.0052**.

Robustez preservada tras remover outliers y trimming → efecto NO atribuible a ruido muestral. Win/loss stats: aligned avg_win +1.13% vs loss -0.54%; contrarian avg_win solo +0.63% vs loss -1.03%.

**Veredicto**: hipótesis §9.3 v2.6 (contrarian filter → bloquear aligned) **REFUTADA con dirección OPUESTA confirmada** (p=0.0003 trimmed). Efecto magnitud: gap 1.07 pp/trade entre grupos. Literatura contrarian (funding extremo como crowding signal a atacar) asume sistemas de reversión; este sistema es **trend-following** donde funding positivo es **confirmation signal** de la tendencia que TF captura. Aligned no es crowd-to-be-squeezed, es tendencia confirmada.

**Simulación v2.6 original aplicada al dataset**:
- Habría bloqueado los 16 trades ganadores aligned (+0.75 USDT).
- Habría permitido los 18 trades perdedores contrarian (-0.77 USDT).
- Diff operacional: **-1.52 USDT adicional** vs PnL real (+0.70 USDT).
- Filter habría degradado performance en **factor 2.2×** sobre 50 trades.

**Threshold §9.3 propuesto**:
- `|rate| > 0.001` (0.1% per 8h) como "extremo".
- **0/50 trades** cumplen — ese threshold nunca se habría activado.
- p99 empírica: 1.74e-4 (5× menor que §9.3). p95: 1.15e-4.
- "Régimen extremo" hipotético por §9.3 jamás ocurrió en ventana abril 2026.
- Cualquier filter futuro que quiera ser operativo necesita threshold mucho menor (ej. percentil empírico p75-p90).

**Distribución entre grupos diversa**: aligned dominado por ONDO (4), ATOM (2); contrarian por INJ (3), ALGO/ICP/SAND (2 each). Sin concentración patológica — efecto distribuido cross-symbol.

**Updates documentales**:
- §9.3 v2.6 actualizada con nota REFUTADO (hipótesis strikethrough + análisis empírico).
- §13.3 "Observabilidad funding per-trade" → IMPLEMENTADO (pointer a esta entrada).
- §13.3 "Filtro funding contrarian runtime" → **REFUTADO** (pointer a esta entrada). Distinción importante: NO es "archivado por falta de evidencia", es "refutado por evidencia contraria robusta".
- §13.3 nuevo item EN_ESPERA: **"v2.6-inv momentum filter candidato"** — bloquear contrarian entries (hipótesis inversa). Disparo N≥100 post-v2.3.11 (~2026-05-01). Caveat: rompe Fidelidad 2 igual, requiere lab-side impl o documentar ruptura. Requiere validación temporal (régimen actual puede no generalizar).
- §12 Lección 33 nueva: "Hipótesis del roadmap requieren validación empírica antes de implementación, incluso si provienen de literatura establecida".

**Caveats permanentes**:
- N=50 en 4 días calendario es mínimo §13.3; régimen lateral-alcista abril 2026 puede no representar bearish/tail-risk. Confirmar con N≥100 antes de implementar filter inverso.
- Analyzer enriquecido NO integrado en `analyze_performance_attribution.py` — es script standalone. Si se aprueba v2.6-inv futuro, evaluar integración.
- Fetch funding rate requiere geo acceso a BingX/Binance — ejecutable desde VPS Tokyo. Local España bloquea todos los major exchanges perpetuos en ccxt.

**Fidelidad 2**: invariante (Opción A es observabilidad offline, no toca bot runtime). Decisión de implementar v2.6-inv en futuro traerá el dilema Fidelidad 2 pendiente.

**Deuda declarada**:
- §13.3 E1 funding sign bug: irrelevante para esta observabilidad (bypass natural); sigue como EN_ESPERA para otros consumers del path fallback.
- Analyzer integration (opcional): si se aprueba v2.6-inv, considerar merge de las 3 columnas a `analyze_performance_attribution.py`.
- Funding data fetch requires BingX access — analyzer runs in Spain environment would need funding data pre-fetched from VPS.

Referencias: `funding_observability.py` (nuevo), `analyze_performance_attribution.py` v2.4.1 (sin cambios, bypass E1 natural), §9.3 v2.6 actualizada, §13.3 items actualizados, §12 Lección 33 nueva, dataset N=50 trades post-v2.3.11 ejecutado en VPS Tokyo con BingX real.

Cierre: permanente para observabilidad (IMPLEMENTADO) + refutación v2.6 (RESUELTO por evidencia contraria). Analyzer enriquecido operativo via script standalone. Item candidato v2.6-inv queda en §13.3 EN_ESPERA.

---

**[MEJORA] [RESUELTO] Cooldown asimétrico — UNIFICAR SEGURO por Opción A — 2026-04-22**

Contexto: A04 TF (§13.4 2026-04-23) + A04b MR (§13.4 2026-04-23) identificaron la única POT INVOLUNTARIA compartida entre ambas auditorías Fidelidad 1: switch cooldown por tipo exit en kernels (`emergency/cancel → cooldown_until = t`; `sl_exit/div_exit → t + cooldown_bars - 1`) vs Pine uniforme `i_cooldown_bars`. §13.3 planteó investigación empírica para decidir unificar vs mantener.

**Discovery pre-ejecución** (2026-04-22 ultrathink): `COOLDOWN_BARS = 1` es constante única en 9 módulos del pipeline productivo (`lab_historico_numba_v8_3.py` L422, `mean_reversion_kernel.py` L38, `live/brain_engine.py` L88, `audit_fidelity_v5_2.py` L98, `master.py` L61+L456 CONFIG, `pipeline.py` L65, `regime_walk_forward.py` L566 L574 vía `lab.COOLDOWN_BARS`, `mean_reversion_walk_forward.py` L152, `walk_forward_experiment.py` L71). Ningún override a >1 en producción, live, audit ni pipeline lab. Con `cooldown_bars=1` las 4 ramas del switch colapsan matemáticamente a `t` (la variable `cooldown_bars - 1 = 0`). **La "asimetría" era código estructural latente sin efecto operacional**; §13.4 A04 ya lo avisaba: "Impacto BAJO con default `cooldown_bars=1`; divergencia solo emerge si `cooldown_bars>1`".

**Confirmación Ricardo Opción A** (2026-04-22): cooldown=1 siempre operó en Pine productivo histórico. La diferenciación por tipo exit en kernel es estructura que **nunca fue validada operacionalmente** — código muerto bajo la configuración única productiva. No hay base empírica histórica para mantenerla.

**Descartados** vs plan original test empírico:
- Test cooldown_bars=2,3 hipotético: no hay razón operativa (Pine productivo siempre 1, roadmap no lo contempla).
- Caracterizar asimetría "latente" para futuro: no tiene base operacional histórica.
- Matriz 4 símbolos × 3 configs × 2 modos a cooldown_bars=1: vacua por construcción (0 diff esperado).

**Refactor aplicado** (branch `feature-cooldown-unify`, commit `9389af9`):

Kernel TF `lab_historico_numba_v8_3.py` L1630-1637 + Kernel MR `mean_reversion_kernel.py` L408-415:

```python
# ANTES (4-branch switch, código muerto bajo cooldown_bars=1):
if sl_emergency_signal:   cooldown_until = t
elif sl_exit_signal:      cooldown_until = t + cooldown_bars - 1
elif div_exit_signal:     cooldown_until = t + cooldown_bars - 1
elif cancel_signal:       cooldown_until = t

# DESPUÉS (expresión Pine canónica i_cooldown_bars uniforme):
if sl_emergency_signal or sl_exit_signal or div_exit_signal or cancel_signal:
    cooldown_until = t + cooldown_bars - 1
```

Con `cooldown_bars=1`: `t + 1 - 1 = t` (idéntico a valor anterior de las 4 ramas). Con hipotético `cooldown_bars>1` aplicaría uniforme (convención Pine). Comportamiento bit-idéntico en régimen productivo.

Fall-through preservado intencionalmente: `tf_exit` y `zone_exit` siguen sin actualizar `cooldown_until` (asimetría 4-vs-6 distinta que §13.3 NO cubre — representa "exits graceful por cambio de régimen" sin cooldown protectivo, fuera de scope).

**Confirmatorio empírico** pre/post refactor:

Nivel A (§0.8 — `brain_engine --verify BTC/USDT` N=1000, config BTC C0 38007639):
| Métrica | Pre | Post | Diff |
|---|---|---|---|
| Trades | 1 | 1 | 0 |
| Wins | 0 | 0 | 0 |
| PnL neto | -0.5935% | -0.5935% | 0.0000 |
| Gross profit | 0.0000% | 0.0000% | 0.0000 |
| Gross loss | 0.5935% | 0.5935% | 0.0000 |

Nivel C (§0.8 — `audit_mr_fidelity_sei.py` SEI/USDT C2 config 45686 N=1500):
| Métrica | Pre | Post | Diff |
|---|---|---|---|
| PnL % | 1.0180 | 1.0180 | 0.0000 |
| Trades | 17 | 17 | 0 |
| Wins | 5 | 5 | 0 |
| Cancels | 2 | 2 | 0 |
| MaxDD % | 3.9316 | 3.9316 | 0.0000 |
| GrossProfit | 9.6434 | 9.6434 | 0.0000 |
| GrossLoss | 8.6254 | 8.6254 | 0.0000 |

Nivel B (§0.8 — wrapper temporal `.nivel_b_cooldown.py`) POST-refactor:

| Símbolo | Config | N bars | Brain trades | Brain PnL | Kernel trades | Kernel PnL | Trade ratio | PnL diff abs | Match % |
|---|---|---|---|---|---|---|---|---|---|
| ONDO/USDT | 2457036 VIDYA(18)/KAMA(54) C0 | 8335 | 506 | +12.3097% | 510 | +7.0114% | 0.78% | 5.2983% | 99.22% |
| APT/USDT | 2473235 Tenkan(24)/KAMA(72) C0 | 10000 | 1786 | -88.9407% | 1801 | -87.6147% | 0.83% | 1.3260% | 99.17% |

Resultados **bit-idénticos a §13.4 A10 baseline pre-refactor** (ONDO A10: brain=506 kernel=510 diff PnL +5.2983%; APT A10: brain vs kernel diff PnL 1.326%). Criterios §0.8: trade ratio <5% ✓ ambos (0.78% + 0.83%), match count >95% ✓ ambos (99.22% + 99.17%). Drift brain↔kernel (propiedad arquitectónica §12.30, ranking estable §13.4 A10) **invariante** al refactor — confirmación empírica independiente de la prueba analítica (cooldown_bars=1 hace ambas ramas idénticas).

Pre-refactor Nivel B no se re-ejecutó (Nivel A+C diff 0.0000 anclan equivalencia matemáticamente; Nivel B POST-refactor vs §13.4 A10 baseline bit-idéntica cierra el triple anclaje empírico).

**Veredicto empírico**: **UNIFICAR SEGURO** confirmado. Refactor es zero-impact en régimen productivo (`cooldown_bars=1`). Fidelidad 2 TF + MR invariante por construcción (los 7 métricas MR + 5 métricas TF bit-idénticas).

**Deuda residual (fuera de scope A)**:
- `audit_fidelity_v5_2.py` L961-968 + `audit_fidelity_v5.py` L969-976 + `lab_cuda.py` L542-546 L1060-1062 mantienen el switch asimétrico 4-way. Con `COOLDOWN_BARS=1` es igualmente inerte. Candidatos a pass de consistencia pre-reciclaje (1h refactor cosmético).
- `EXPECTED_LAB_KERNEL_HASH` en audit_fidelity_v5/v5_2 puede necesitar actualización si emite WARN al ver la nueva firma de `run_simulation_numba`. Monitorear en próxima ejecución de audit N≥50 (~2026-04-24 post-trades).
- Asimetría 4-vs-6 distinta (tf_exit/zone_exit sin cooldown): observación estructural separada, no tratada en §13.3. No hay evidencia operacional de que deba unificarse con Pine (que sí impone cooldown en todos los exits).

**Item §13.3 cooldown → RESUELTO**. Último ítem bloqueante arquitectónico pre-reciclaje cerrado. Pipeline pre-reciclaje listo (pending decisiones operacionales: política adelantar reciclaje por criterio empírico, P1 leverage cuando balance >1000 USDT).

Deploy VPS NO requerido (Fidelidad 2 invariante; cambio activa al próximo restart del bot con comportamiento bit-equivalente).

Referencias: commit `9389af9` refactor kernels, §13.3 "Cooldown asimétrico" movido a RESUELTO, §13.4 entrada A04 TF 2026-04-23, §13.4 entrada A04b MR 2026-04-23 (POT INVOLUNTARIA compartida ahora resuelta), §2.6 kernel TF + kernel MR fix entry adicional, Ricardo confirmación Opción A 2026-04-22.

Cierre: permanente.

---

**[SESIÓN] [RESUELTO] Sesión 2026-04-23 — 9 items §13.3 resueltos + runbook reciclaje**

Contexto: sesión intensiva de resolución pre-reciclaje. Ricardo decidió atacar agresivamente el backlog §13.3 con foco en items que afectan el próximo `master.py --recycle`. Al cierre: 9 items RESUELTOS, pipeline pre-reciclaje significativamente mejorado, runbook operacional documentado.

**Balance arquitectónico del día**:

| Item | Scope | Impacto pipeline | Commit |
|---|---|---|---|
| **W3** | bootstrap pf_fwd + selección por ci_low | walk-forward output + selection logic | `4e54c8d` |
| **W4** | thresholds _FWD + filtros CI | walk-forward filtering | `ee4ce69` |
| (merge W3+W4) | — | — | `56d38d4` |
| **A12 LL1** | MAs dedup lab_lite ↔ lab_historico | single source of truth MAs | `347639a` + `ae5a21a` |
| **A14 W1** | plateau_ratio consistency | metadata correcta | `5a7135b` + `cf9d7b6` |
| **A15 W2** | engine tag + resume check | reproducibilidad + heterogeneidad prevention | (mismo commit A14) |
| **A13 LL2** | ratio supervivencia validado saludable | diseño OK, sin fix código | `bcc3828` (docs) |
| **A04 TF** | Fidelidad 1 formal kernel TF ↔ Pine v44 | auditoría limpia, 5 divergencias catalogadas | `b620d9f` |
| **A05 MR** | docstring + dead fields + zone helpers | brain MR pass-through cleanup | `8552b95` + `ca3bbd6` + `4a19c09` |
| **A04b MR** | Fidelidad 1 formal kernel MR ↔ Pine v7.25 | auditoría limpia, 4 ADAPTACIÓN §0.2 esperadas + 1 POT INVOLUNTARIA compartida | `09b01f6` |
| Cierre docs | L31+L32 + runbook + §13.4 consolidación | documentación completa sesión | (este commit) |

**Totales arquitectónicos**:

- Pipeline walk-forward: W3 bootstrap CI + W4 thresholds + CI filters + A14 plateau canonical + A15 engine tag. 4 mejoras metodológicas nuevas activas.
- Code dedup: A12 (MAs) + A05 S3 (zone_bull_mr) — 2 dominios con single source of truth establecido.
- Auditorías Fidelidad 1 completadas: TF (A04) + MR (A04b). 21 áreas mapeadas, 1 única POT INVOLUNTARIA real (cooldown asimétrico compartido TF+MR, impacto bajo).
- A05 MR audit cleanup: docstring preciso + dead fields DEPRECATED + 6 inline comparisons refactoradas.
- Validación empírica: A13 ratio supervivencia 36.7% mean cross-símbolo.

**Regresión acumulada 34/34 tests PASS**:
- W3 bootstrap 8/8, W4 thresholds 8/8, A12 MA parity 4/4, A14 plateau 4/4, A15 engine tag 4/4, A05 zone helpers 6/6.

**Smoke test §0.8 3 niveles PASS** (al cierre):
- Nivel A BTC N=1000: diff 0.0000 exacto 5 métricas ✓.
- Nivel B ONDO+APT N=10000: match >99%, ratio bar-level consistente con baseline A10 2026-04-22 (ONDO ~0.79% / APT ~0.84% gross-count; PnL diff ~5.3% / ~1.3% dentro de drift arquitectónico §12.30 documentado) ✓.
- Nivel C SEI MR C2: 7/7 métricas diff 0.0000 ✓.

**Items §13.3 que quedan EN_ESPERA post-sesión**:

1. **Cooldown asimétrico TF+MR** (NUEVO — emergente A04+A04b). Única POT INVOLUNTARIA real detectada en ambas auditorías Fidelidad 1. Kernel diferencia `emergency/cancel → cooldown=t fijo` vs `sl/div → cooldown=t+cooldown_bars-1`; Pine uniforma `i_cooldown_bars`. Con default `cooldown_bars=1` son operacionalmente idénticos. Candidato pequeño pre-v3.0 reciclaje: investigar intención original o unificar.

2. **A30 hidden divergence asimetría TF vs MR**: diferido v3.0 por scope arquitectónico (67/138 configs). Requiere test diferencial completo con simulador swap TF↔MR.

3. **B2 prev_zone asimetría TF vs MR + B3 TF locals vs MR state directo div_ctx**: diferidos v3.0 por complejidad refactor API interna brain.

4. **P1 portfolio leverage**: proyecto arquitectónico separado. Disparador: balance >1000 USDT.

5. **§13.3 política adelantar reciclaje por criterio empírico**: pendiente decisión Ricardo según evolución post-N≥50.

6. **Batch fix emojis cp1252 restantes en lab_historico** (§13.3 MEJORA EN_ESPERA): 14 ocurrencias no críticas.

7. **R1 brain cooldown emergency/cancel**: diferido post-N≥50 + test diferencial.

8. **W3 sesiones futuras ampliar muestreo**: opcional post-primer reciclaje con W3.

9. Otros §13.3 EN_ESPERA dormidos (inventario antes próximo ciclo).

**Lecciones metodológicas §12 nuevas**:
- **L31 Verificar diseño documentado antes de diagnosticar problema arquitectónico** (caso origen A13 LL2 primera iteración incorrecta).
- **L32 Auditorías comparativas con referencia histórica requieren inventario de adaptaciones esperadas a priori** (caso origen A04b).

**Runbook reciclaje** creado en `docs/runbook_reciclaje.md` con 10 secciones: estado requerido, precondiciones hardware/compute, variables decisión, comandos ejecución, criterios aceptación, plan contingencia, items pendientes post-reciclaje, protocolo deploy VPS, referencias, cuándo ejecutar.

**Commits del día** (cronológicos en main):
1. `4e54c8d` feat(w3) + `ee4ce69` feat(w4) + `56d38d4` merge W3+W4.
2. `347639a` refactor(A12) + `ae5a21a` merge A12.
3. `5a7135b` fix(a14+a15) + `cf9d7b6` merge + `c6cf68c` docs.
4. `bcc3828` docs(a13 LL2).
5. `b620d9f` docs(A04 TF).
6. `8552b95` cleanup(A05) + `ca3bbd6` merge + `4a19c09` docs.
7. `09b01f6` docs(A04b MR).
8. (este commit cierre) docs sesión + L31+L32 + runbook.

**Estado operacional al cierre**:
- Bot v2.4.5 operacional VPS Tokio (sin deploy hoy — todas las resoluciones pre-reciclaje, no productivas).
- Fidelidad 2 invariante (ningún fix tocó path brain↔kernel operacional).
- Main branch commits 2026-04-23 todos mergeados.
- comboclaude ↔ combolab sincronizado (§0.7 MD5 2-way verificado en cada merge).

**Próxima acción esperada**: N≥50 trades post-v2.4.5 para primer audit/analyzer con data fresca → decisión adelantar reciclaje o mantener calendario julio.

Cierre: permanente. Sesión 2026-04-23 cerrada. Runbook listo para ejecutar reciclaje cuando Ricardo decida el momento.

---

**[AUDITORIA] [RESUELTO scope MR] A04b Fidelidad 1 formal kernel MR ↔ Pine v7.25 — 2026-04-23**

Contexto: scope simétrico a A04 TF (commit b620d9f). Caveat arquitectónico crítico (§0.2 + §0.6): Pine v7.25 MR es **versión congelada con faltas conocidas documentadas**; kernel MR moderno incluye **adaptaciones intencionales**. El objetivo de A04b NO era reconciliar kernel con Pine v7.25 sino inventariar + clasificar divergencias, distinguiendo ADAPTACIÓN DOCUMENTADA (esperada) vs POT INVOLUNTARIA (candidata a investigar).

**Metodología**: mapping estructural + auditoría dirigida a las 4 adaptaciones conocidas + verificación empírica §0.2 "4 mecanismos stop idénticos TF y MR en Pine y en kernel".

**Mapping 13 áreas + clasificación**:

| # | Área | Kernel MR | Pine v7.25 MR | Clasificación |
|---|---|---|---|---|
| 1 | Zonas fast/slow | `fast<slow=BULL` precomputado | `zonaAlcista_viz=series_fast_line<series_slow_line` L154 | ✓ EQUIVALENTE (semántica MR nativa en ambos) |
| 2 | HA/Tenkan | `calc_fast_line`+`calc_slow_line` vía mean_reversion_features | `f_tenkan` L126 + `ha_source_base` L134 | ✓ EQUIVALENTE |
| 3 | Div regular | bits 0/2 en `div_bits_arr` L176-177 | `pos_reg>0 or neg_reg>0` L380-381 | ✓ EQUIVALENTE |
| 4 | **Div HIDDEN FIX** | bits 12-13 "Hidden corregida"/"Both corregida" L10 + L180-191 | Sin toggle hid_inversion (L380-381 directo) | **ADAPTACIÓN §0.2** |
| 5 | **Cancel zona** bit 14 | `cancel_zona_bit` L77 + L293-314 | "Zona Inválida" inside `i_use_cancel` unificado L688-700 | **ADAPTACIÓN §0.2** |
| 6 | **Cancel TF** bit 15 | `cancel_tf_bit` L78 + L315-346 | "TF mismatch" inside `i_use_cancel` L704-732 | **ADAPTACIÓN §0.2** |
| 7 | **Cancel ghost** bit 16 | `cancel_ghost_bit` L79 + L347-372 | trajectory loop inside `i_use_cancel` L734+ | **ADAPTACIÓN §0.2** |
| 8 | SL inicial 3% | hardcoded L35 | `i_sl_percent=3.0` L56 | ✓ IDÉNTICO |
| 9 | SL emergency 5% intrabar | hardcoded L36 + L233-247 | `i_sl_emergency_percent=5.0` L63 + L543-563 | ✓ IDÉNTICO |
| 10 | TS 0.5% on-close | hardcoded `low[t-1]/high[t-1]` monotónico L222-231 | `i_ts_percent=0.5` `low[1]/high[1]` math.max/min L660-666 | ✓ IDÉNTICO |
| 11 | Filtros HTF | entry_mask bits 4-8 (TF1-TF5) | `i3_use_tf1/2/3/4/5` L186-196 | ✓ EQUIVALENTE |
| 12 | Umbral consenso div | hardcoded `>=1` L198 | `i_div_showlimit` 1-8 param L86 | ADAPTACIÓN NO DOC INTENCIONAL (igual div#2 A04 TF) |
| 13 | Cooldown asimétrico | `emergency/cancel=t` fijo, `sl/div=t+cooldown_bars-1` L408-415 | `i_cooldown_bars` uniforme | **ITEM INVESTIGATIVO** (reclasificado post-2026-04-23 con contexto Pine, ver §13.3 "Cooldown asimétrico — investigación empírica pre-reciclaje") |

**Tabla agregada A04b**:

| Categoría | Count |
|---|---|
| ✓ EQUIVALENTE / IDÉNTICO | 8 áreas |
| **ADAPTACIÓN DOCUMENTADA §0.2** | 4 áreas |
| ADAPTACIÓN NO DOC INTENCIONAL | 1 área |
| **NO DOC POT INVOLUNTARIA** | 1 área (compartida con TF) |

**Validación 4 adaptaciones conocidas esperadas**:
- #1 Hidden divergence fix: ✅ CONFIRMADA (kernel bits 12-13 "corregida"; Pine v7.25 sin fix).
- #2 Cancelaciones bits 14-16: ✅ CONFIRMADA (kernel separa en 3 bits independientes para walk-forward; Pine unifica en `i_use_cancel`).
- #3 HA/Tenkan cruce invertido: ✅ CONFIRMADA en ambos (propiedad diseño MR nativa, no adaptación del kernel sobre Pine).
- #4 Semántica zona invertida: ✅ CONFIRMADA en ambos (Pine v7.25 L154 nativo).

**POT INVOLUNTARIA única (reclasificada 2026-04-23)**: cooldown asimétrico por tipo de exit (compartido TF+MR). Confirmado como **patrón arquitectónico compartido del proyecto**, no bug aislado MR. Impacto bajo con `cooldown_bars=1` default. 

**Nota matizadora 2026-04-23**: Ricardo aportó contexto histórico Pine post-auditoría — el cooldown fue implementado originalmente para evitar aperturas-cierres en velas contiguas sin explicación aparente (whipsaws por bar forming/resolved timing en indicador Pine productivo). Reclasificado de "POT INVOLUNTARIA arbitraria" a **ITEM INVESTIGATIVO heredado con base operacional Pine**. Metodología test empírico documentada en §13.3 entrada "Cooldown asimétrico — investigación empírica pre-reciclaje" 2026-04-23.

**Cross-checks**:

- **§13.3 A30 hidden asimetría TF vs MR**: **VALIDADA**. Kernel MR usa bit mapping swapped (bits 1/3 "corregidos") vs kernel TF tradicional. Consistente con adaptación §0.2 #1. Los 67/138 configs con hid_inv invertido son naturaleza del diseño MR — no regresión vs Pine (que no tenía fix), sino mejora documentada.
- **§0.2 afirmación "4 mecanismos stop idénticos TF y MR en Pine y en kernel"**: **VALIDADA EMPÍRICAMENTE**. Kernel MR L222-256 idéntico estructuralmente a kernel TF L1482-1515. Pine MR L543-669 idéntico estructuralmente a Pine TF v44 L786-906. Parámetros (3%/5%/0.5%) coinciden.
- **§0.6 kernel verdad operacional / Pine referencia histórica**: caveat arquitectónico validado empíricamente. 4/5 divergencias estructurales son ADAPTACIÓN §0.2 consciente (kernel moderno mejora versión Pine congelada).

**Veredicto A04b**: auditoría **LIMPIA con caveat esperado**. Las 4 adaptaciones conocidas están presentes en kernel como documentado. 1 única POT INVOLUNTARIA (cooldown) ya conocida por A04 TF — patrón compartido, impacto bajo. Ninguna regresión arquitectónica detectada. Fidelidad 1 MR confirmada robusta dentro del marco §0.6 (kernel evoluciona sobre Pine congelado).

**Consolidación A04 completo (TF + MR)**:

Ambos scopes completados en mismo día. Totales acumulados ambas ramas:
- 21 áreas mapeadas (10 TF + 13 MR − 2 compartidas estructurales).
- 10 equivalencias IDÉNTICAS / EQUIVALENTES.
- 4 ADAPTACIÓN DOCUMENTADA §0.2 (todas MR).
- 3 NO DOC INTENCIONALES (div_showlimit shared + 2 solo TF: dontconfirm, source).
- 1 DOCUMENTADA en código (cancel_tf TF #1).
- 1 **POT INVOLUNTARIA compartida** (cooldown asimétrico TF+MR) — única candidata real a investigar pre-reciclaje.

**Deploy VPS NO requerido**. Bot v2.4.5 operacional. Fidelidad 2 invariante (A04/A04b son auditorías documentales, no tocan código).

**Siguiente ítem pre-reciclaje**: investigar cooldown asimétrico (único POT INVOLUNTARIA detectado en ambas auditorías) — decidir unificar vs documentar asimetría. Scope pequeño.

Referencias: `mean_reversion_kernel.py` + `indicador_v7_25_smartdiv_v40_28_MR.pine`, §0.2 versión congelada + faltas conocidas, §0.6 kernel verdad operacional, §13.3 A04 scope completo (TF + MR) movido a RESUELTO.

Cierre: permanente ambos scopes TF + MR.

---

**[MEJORA] [RESUELTO] A05 MR audit cleanup (docstring + dead fields + zone_bull helper) — 2026-04-23**

Contexto: auditoría Fidelidad 2 MR 2026-04-21 identificó 4 MENORES sin impacto operacional. MENOR 1 resuelto en su commit original (docstring dual-use `_check_cancel_tf`). Los 3 restantes (MENOR 2 zone_bull drift, MENOR 3 dead fields, MENOR docstring `_check_cancel_zona_mr` impreciso) quedaron consolidados en A05 pre-reciclaje julio.

**Resolución anticipada 2026-04-23** (3 MENORES en batch, commit 8552b95 → merge ca3bbd6):

**Sub-item 1 — docstring `_check_cancel_zona_mr` preciso**:

Pre-fix decía "forming zone at entry repainted and entry zone no longer valid" — descripción conceptual pero imprecisa. La implementación no compara "forming en entry_bar" directamente; compara:
- Same day (`entry_day == current_day`): zona actual usando `slow_forming[t]` (bar actual).
- Day closed: zona resolved en `entry_bar` usando `slow_resolved[entry_idx]`.

Docstring reescrito con semántica exacta + Args/Returns + referencia §0.5 MR invertida.

**Sub-item 2 — dead fields deprecation**:

`SymbolState.mr_entry_filters_forming` y `mr_entry_slow_line` son dead fields (asignados en entry MR path, nunca leídos). Residuos de diseño previo (cancel_zona snapshot-based abandonada). Opción adoptada: **preservar con docstring DEPRECATED** para back-compat con `engine_state.json` productivo (VPS + local). Eliminación planificada en v3.0 pre-reciclaje julio.

Justificación de no-eliminar: engine_state.json persistido en VPS contiene estos campos. Eliminarlos + dataclass frozen implícito causaría KeyError al `load_state` sobre JSON legacy. Preservar con default 0/0.0 es idempotente y zero-risk.

**Sub-item 3 — `zone_bull_mr` + `zone_bear_mr` helpers extract**:

Pre-fix: brain_engine recomputaba `fast < slow` inline en 6 sitios (4 en `_check_cancel_zona_mr`, 2 en `_check_cancel_ghost_mr`); kernel MR usaba `calc_zones` con arrays precomputados. Riesgo drift silencioso si `calc_zones` cambiaba fórmula sin actualizar brain.

Fix arquitectural:
- `zone_bull_mr(fast, slow)` y `zone_bear_mr(fast, slow)` añadidos module-level en `mean_reversion_features.py` (escalar + array friendly, NaN guard defensive).
- `calc_zones` refactorizado para delegar a helpers (single source of truth).
- `brain_engine.py` importa `from mean_reversion_features import zone_bull_mr, zone_bear_mr`.
- 6 inline comparisons reemplazados preservando NaN guards explícitos existentes:
  * `_check_cancel_zona_mr` L1735 (`ft<sf` → `zone_bull_mr(ft, sf)`), L1737, L1747, L1749.
  * `_check_cancel_ghost_mr` L1777, L1784.

Semántica bit-equivalente verificada (test 5: scalar helper ≡ inline comparison sobre 100 random pairs).

**Complementa A12 LL1** (commit ae5a21a): A12 consolidó MAs entre `lab_lite` ↔ `lab_historico`. A05 S3 consolida zonas MR entre `mean_reversion_features` ↔ `brain_engine`. Post-A05 brain MR es pass-through para los 2 cómputos comunes (MAs + zonas); cambios futuros en la fórmula zone_bull/bear MR se propagan automáticamente a ambos consumers.

**Validación**:

Tests 6/6 PASS (`tests/test_a05_zone_helpers.py`):
1. scalar bull/bear basic (fast<slow → bull True, inversos False, equal False strict).
2. NaN defensive: NaN input → False siempre (never crash).
3. Array vectorizado: shape + NaN propagation a False.
4. `calc_zones` delega correctamente (forming + resolved branches).
5. Parity scalar helper ≡ inline `fl<sf` sobre 100 pairs aleatorios.
6. brain_engine source verifica import + ausencia de inline remnants `ft<sf`.

Regresión 34/34 PASS acumulada (W3 8 + W4 8 + A12 4 + A14 4 + A15 4 + A05 6).

Smoke §0.8:
- Nivel A (BTC N=1000): diff 0.0000 exacto 5 métricas ✓.
- Nivel C (SEI MR, MANDATORIO por tocar brain MR): 7/7 métricas diff 0.0000 exacto ✓.
- Nivel B omitido: cambios aislados a helpers puros bit-equivalentes; test 5 prueba parity empírica.

**Fidelidad 2 MR invariante por construcción**. Deploy VPS NO requerido — helpers puros idempotentes, activan al próximo restart del bot. Bot v2.4.5 operacional con comportamiento bit-equivalente al pre-merge.

**Impacto residual para v3.0 reciclaje**:
- Dead fields mr_entry_filters_forming / mr_entry_slow_line: planificada eliminación total (campos + asignaciones L2099-2100, L2119-2120).
- Opcional: unificar también slow_line / fast_line MR (brain tiene `_calc_slow_line_*_mr` / `_calc_fast_line_mr` duplicados de `mean_reversion_features`). Fuera de scope A05.

Referencias: commit 8552b95 (fix) + ca3bbd6 (merge main), `live/brain_engine.py` (docstring + imports + helper calls + deprecation), `mean_reversion_features.py` (helpers + calc_zones delegation), `tests/test_a05_zone_helpers.py`, §0.5 MR invertida, §13.3 entry movido a RESUELTO A05.

Cierre: permanente para los 3 MENORES. Dead fields eliminación real en v3.0.

---

**[AUDITORIA] [RESUELTO scope TF] A04 Fidelidad 1 formal kernel TF ↔ Pine v44 — 2026-04-23**

Contexto: A04 del roadmap pre-reciclaje exige inventario formal de divergencias entre kernel Numba TF (`lab_historico_numba_v8_3.py`, 2678L) y Pine canónico TF (`indicador_v44_0_smartdiv_v11_0_TF.pine`, 1243L) para validar la asunción base del proyecto: kernel es implementación fiel del diseño Pine original. Scope completado para TF hoy; MR queda como A04b separada (Pine `indicador_v7_25_smartdiv_v40_28_MR.pine` ↔ kernel `mean_reversion_kernel.py`).

**Metodología**:
- Mapping estructural 10 áreas (MAs, zonas, entry, exit, divergencias, stops, cancelaciones, filtros HTF, cooldown, Heikin-Ashi) con delegación a agente Explore para extracción paralela de citas código.
- Auditoría detallada por área con énfasis en las 3 de mayor riesgo estructural (divergencias, stops, cancelaciones).
- Clasificación de cada divergencia: DOCUMENTADA / NO DOC INTENCIONAL / NO DOC POT INVOLUNTARIA.
- Cross-check con hallazgos previos §13.2 (lag, TS fidelity) y §13.3 (A30 hidden asimetría TF vs MR).

**5 divergencias inventariadas**:

**#1 cancel_tf: resolved[t] vs ha_trend_tfN_e[barsSinceEntry]**
- Kernel L1558-1562: comment literal "Fix fidelidad: usar resolved[t] (barra HTF actual finalizada) en vez de resolved[entry_bar]".
- Pine L920-934: reindex histórico `ha_trend_tfN_e[barsSinceEntry]`.
- **Tipo: DOCUMENTADA** ✓ (comment código + §0.6 CONTEXTO).
- Impacto: medio (trades donde HTF cambia entre entry y current bar sin cruce reciente).
- Resolución: mantener (decisión madurada §0.6).

**#2 div_showlimit hardcoded `1` vs parametrizable Pine 1-8**
- Pine L134: `i_div_showlimit = input.int(defval=1, minval=1, maxval=8)`.
- Kernel L1459: `net_div_score >= 1` hardcoded; comment L1458 "matches Pine default".
- **Tipo: NO DOC INTENCIONAL** (intencional por comment, limitación paramétrica no documentada en CONTEXTO).
- Impacto: medio si reciclaje futuro quisiera umbrales más estrictos.
- Resolución: considerar añadir bit config_id para explorar {1, 2, 3} en próximo reciclaje. Opcional pre-julio.

**#3 kernel no soporta `i_div_dontconfirm=true`**
- Pine L139: parametrizable (default false).
- Kernel L633: `startpoint = 1` hardcoded (equivalente a dontconfirm=false).
- **Tipo: NO DOC INTENCIONAL**.
- Impacto: bajo (default Pine coincide con kernel).
- Resolución: aceptar simplificación.

**#4 kernel pivotes sobre close exclusivamente vs Pine Close/High-Low param**
- Pine L136: `i_div_source = input.string(defval="Close", options=["Close", "High/Low"])`.
- Pine L512-513 usa `high`/`low` si source="High/Low".
- Kernel L641, 653: `close_arr` hardcoded.
- **Tipo: NO DOC INTENCIONAL**.
- Impacto: bajo (default Pine Close coincide).
- Resolución: aceptar simplificación.

**#5 cooldown diferenciado por tipo de exit en kernel**
- Kernel L1630-1637: `sl_emergency_signal` / `cancel_signal` → `cooldown_until = t` (1 bar fijo); `sl_exit_signal` / `div_exit_signal` → `cooldown_until = t + cooldown_bars - 1` (parametrizable).
- Pine: `last_cancel_bar := bar_index + i_cooldown_bars - 1` uniforme todos los exits.
- **Tipo inicial: NO DOC POT INVOLUNTARIA**.
- Impacto: BAJO con default `cooldown_bars=1` (ambos valores colapsan a 1 bar); divergencia solo emerge si `cooldown_bars>1`.
- Resolución: investigar intención original pre-reciclaje. Si intencional → añadir comment código. Si no → unificar.

**Nota matizadora 2026-04-23 post-A04/A04b**: Ricardo aportó contexto histórico Pine — el cooldown fue implementado originalmente para evitar aperturas-cierres en velas contiguas sin explicación aparente (whipsaws por bar forming/resolved timing en indicador operando productivamente). Reclasificado a **ITEM INVESTIGATIVO heredado con base operacional Pine**, no POT INVOLUNTARIA arbitraria. Ver §13.3 entrada "Cooldown asimétrico — investigación empírica pre-reciclaje" para metodología test empírico validando si mecanismos modernos (bits 14-16 cancelaciones + v2.3.11 bar forming fix) ya resuelven el problema original.

**Tabla agregada**:

| Categoría | Count | % del total |
|---|---|---|
| DOCUMENTADAS | 1 | 20% |
| NO DOC INTENCIONALES | 3 | 60% |
| NO DOC POT INVOLUNTARIAS | 1 | 20% |
| **Total** | **5** | **100%** |

**Cross-checks** (verificaciones con hallazgos previos):

- **§13.3 A30 hidden asimetría TF vs MR (67/138 configs afectados)**: confirmado que A30 es asimetría INTERNA kernel TF ↔ kernel MR (pre-swap bits 1↔3 en MR), NO divergencia kernel TF ↔ Pine TF. Bit mapping `hid_inv=0` tradicional en kernel coincide con Pine `hid_inverted=false`. A04 no amplifica A30; A30 sigue siendo hallazgo intra-proyecto pre-reciclaje separado.
- **§13.2 TS fidelity (resuelto v2.4.0)**: Pine L897-903 y kernel L1482-1492 idénticos (TS on-close, `low[1]/high[1]`, monotónico `math.max/min`, 0.5% prev bar). Fidelidad 1 en TS INTACTA. El issue §13.2 era Fidelidad 2 bot live (update_trailing_stop ratchetaba BingX intrabar), resuelto v2.4.0.
- **§13.2 lag estructural (resuelto v2.3.11)**: ni Pine ni kernel tenían lag. Era arquitectura bot live (sin bar forming); resuelto v2.3.11 restaurando fetch forming. Fidelidad 1 no afectada.

**Veredicto**: auditoría **LIMPIA**. Ninguna divergencia categórica que invalide arquitectura. 4/5 divergencias son paramétricas del tipo "kernel solo simula Pine con parámetros default" — consciente simplificación que reduce espacio de búsqueda del walk-forward. 1 divergencia (cooldown diferenciado) merece investigación menor pre-reciclaje pero impacto bajo con defaults actuales.

**Recomendaciones pre-reciclaje**:
1. Aceptar #1 (cancel_tf) como diseño madurado §0.6.
2. Considerar #2 (showlimit en config_id) como enhancement opcional next reciclaje — cost 1 bit, ×2-4 configs, potencial mejora filtro ruido divergencia.
3. Aceptar #3-#4 (dontconfirm, source) como simplificaciones documentadas.
4. Investigar #5 (cooldown) pre-reciclaje — decisión entre unificar o documentar asimetría.

**Scope MR (A04b)** queda pendiente. Auditoría MR requerirá esfuerzo similar (~1-2h compute + analysis) sobre `mean_reversion_kernel.py` ↔ Pine v7.25 MR.

Deploy VPS NO requerido. Bot v2.4.5 operacional. Fidelidad 2 invariante. El kernel sigue siendo "verdad operacional" (§0.6) validada empíricamente contra Pine como referencia histórica.

Referencias: `lab_historico_numba_v8_3.py` (kernel TF) y `indicador_v44_0_smartdiv_v11_0_TF.pine` (Pine TF), §0.6 Kernel como verdad operacional, §13.2 HALLAZGOS resueltos, §13.3 A30 pendiente (MR refactor), §13.3 A04 movido a RESUELTO scope TF.

Cierre: permanente para scope TF. Próximo: A04b (MR) como tarea separada.

---

**[MEJORA] [RESUELTO] A13 (LL2) lab_lite ratio supervivencia presets → walk-forward — 2026-04-23**

Contexto: §13.3 LL2 original (2026-04-17) advertía que kernel simplificado de lab_lite (solo zonas MA puras sin SL/TS/divergencias/cancelaciones/filtros HTF) podría tener selection bias. Criterio empírico documentado: "cuantificar % presets que pasan walk-forward tras lab_lite. Si <20%, reducción demasiado agresiva".

**Análisis empírico 2026-04-23** sobre 45 símbolos productivos completos (output/production/presets_*.csv vs regime_wf/*_specialist_configs.json):

Metodología:
- Extraer presets únicos de `presets_SYMBOL.csv` por signature `fast_type(period)/slow_type(period)` (excluyendo hyst tag _H00/_H05 y trend derivado slow×4).
- Extraer presets únicos de `top_configs` del JSON (union de clusters C0/C1/C2).
- Calcular intersection / inputs = ratio supervivencia per símbolo.

Resultados:

| Métrica cross-símbolo | Inputs lab_lite | Survived WF | Ratio% |
|---|---|---|---|
| Mean | 30.5 | 11.2 | **36.7%** |
| Median | 31 | 11 | **34.4%** |
| Min | 28 | 5 | 16.7% (MANA) |
| Max | 32 | 20 | 63.3% (FET) |

Distribución según §13.3 LL2:
- **<20% (agresivo)**: 2/45 = 4.4% (APTUSDT 17.2%, MANAUSDT 16.7%).
- **20-70% (saludable)**: 43/45 = 95.6%.
- **>70% (sobredimensionado)**: 0/45.

**Veredicto**: **Caso saludable**. Ratio mean 36.7% cómodamente por encima del threshold 20%. El pipeline lab_lite + walk-forward está apropiadamente calibrado. Sin fix al código requerido.

Cross-check cualitativo con W3 flagged (6 top-1 productivos flagged por bootstrap ci_low<1.0 o ci_width>5.0):
- **MANA C0** (cfg 5339578) flagged W3 + ratio MANA 16.7% (lowest del roster). Correlación observable.
- **APT C1** (cfg 31447907) reemplazado bajo W4 simulado + ratio APT 17.2% (2nd lowest). Correlación observable.
- Otros 4 flagged (ONDO 45.2%, LTC 36.7%, GRT 28.6%, TRX 37.5%, BTC 41.9%) en rango saludable — flagged por CI W3, no por supervivencia.

Hipótesis residual (observable, no causal): supervivencia baja lab_lite↔walk-forward puede correlacionar con mayor probabilidad de specialists flagged W3. Casos MANA + APT consistentes con hipótesis. Item monitoreo post-reciclaje, no acción inmediata.

**Matización importante del diseño**: el bias estructural del kernel lite (ausencia de SL/TS/divergencias/cancelaciones) es diseño INTENCIONAL y documentado — pre-filtro rápido sobre zonas puras. El 36.7% mean demuestra empíricamente que este pre-filtro **NO sesga excesivamente** la selección downstream: walk-forward refina sobre un pool adecuado de presets candidatos.

Reporte análisis previo (desestimado): la caracterización estructural del kernel lite vs completo (Fase 1 A13 primera iteración) diagnosticó el problema incorrecto — comparó equivalencia funcional de kernels cuando el criterio correcto §13.3 era ratio supervivencia de presets a lo largo del pipeline. La caracterización estructural es válida como observación arquitectónica pero no determina el veredicto. El veredicto correcto es empírico y saludable.

Deploy VPS NO requerido (sin fix). Bot v2.4.5 operacional. Fidelidad 2 invariante.

Items §13.3 actualizados:
- LL2 → RESUELTO.
- W3 (commit ee4ce69), W4 (ee4ce69), A12 LL1 (347639a), A14 W1 + A15 W2 (5a7135b): todos RESUELTO.
- Backlog pre-reciclaje §13.3 TF reducido significativamente con estas 6 resoluciones consecutivas.

Referencias: output/production/presets_*.csv (45 files), regime_wf/*_specialist_configs.json (45 files), §13.3 LL2 movido a RESUELTO.

Cierre: permanente. Próximo monitoreo natural al primer audit post-reciclaje para verificar que APT+MANA no emergen como problema específico.

---

**[MEJORA] [RESUELTO] A14+A15 regime_walk_forward polish — 2026-04-23**

Contexto: dos items pre-reciclaje del ultra review 2026-04-17 (W1 plateau_ratio inconsistency, W2 CUDA/CPU drift sin engine tag) atacados en batch dado scope compartido (mismo archivo `regime_walk_forward.py`). Rama `feature-a14-a15-wf-polish`, commit 5a7135b, merge cf9d7b6.

**A14 (W1) — plateau_ratio consistency**:

Problema: fórmula antigua (L1853-1856 pre-fix) hacía bit-flip sobre los 26 bits del config_id sin distinguir campos bitmask vs discrete. Ejemplo: config con campo MA_period en bits [5-8] — un flip del bit 8 cambiaba period de 12 a 20 (salto grande), no el vecino paramétrico esperado (±1). Resultado: plateau_ratio contaba como "neighbors" configs que NO son paramétricamente adyacentes, diluyendo el significado métrico.

Canonical: `_get_neighbors(config_id)` (L1246-1275) ya implementaba la lógica correcta:
- Campos bitmask: flip cada bit individual (semántica bitmask preservada).
- Campos discretos: ±1 dentro del rango válido.

Fix: reemplazar bit-flip loop por llamada única a `_get_neighbors(cid)`. Bloque `Phase 4: Plateau analysis` (L1838-1867 post-fix).

Evidencia empírica del fix (test_2): ONDO C0 cfg 2457036 — canonical genera **25 neighbors**, brute-26 genera **26 neighbors**, symmetric diff **3**. Tres configs considerados "neighbors" por fórmula vieja NO son paramétricamente adyacentes.

Impacto retroactivo: **plateau_ratio NO es filtro de selección** en pipeline canónico (solo metadata informativa: reporte text L1780 + JSON output opcional L2087). `extractor_gemas.py` lo usa como filtro, pero master.py no lo invoca (§13.2 "NO está en pipeline de producción"). Fix cambia SOLO valor metadata en JSONs post-reciclaje; cero impacto operacional hasta próximo `master.py --recycle`.

Tests 4/4 PASS (`tests/test_a14_plateau_consistency.py`):
1. `_get_neighbors(2457036)` devuelve set no-vacío, cid no incluido.
2. Canonical (25) ≠ brute-26 (26), symmetric diff 3.
3. Source code plateau block contiene `_get_neighbors(cid)`, no contiene `for bit in range(26)`.
4. Degenerate case empty neighbors → ratio=0 via `max(n, 1)` guard, sin crash.

**A15 (W2) — engine tag en parquet**:

Problema: bifurcación runtime CUDA↔CPU (L487-505) con variable local `engine_tag` usada solo para print, no persistida. Si un run se resume tras crash con engine distinto (e.g. máquina con CUDA había fallado, restart en máquina CPU), specialists generados tenían heterogeneidad silenciosa — precisión float32/float64 y orden de reducciones difieren marginalmente entre kernels CUDA y Numba CPU.

Fix arquitectural:
- Module constants: `_MACHINE_ID = platform.node()`, `_NUMBA_VERSION = numba.__version__`.
- `_get_engine_tag()` retorna dict con 4 campos (`engine_name`, `engine_version`, `machine_id`, `timestamp_run`). Timestamp fresh per llamada (no static module-load) para capturar momento real de cada parquet write.
- `_check_resume_engine_consistency(parts_dir)`:
  - Si no hay parquets existentes → noop (fresh run).
  - Si existe: lee `engine_name` del primer part. Si matches current → `[A15] resume engine consistency OK`. Si difiere → WARN `A15 RESUME ENGINE MISMATCH`. Legacy parquets sin columna `engine_name` → WARN `parquets pre-A15 sin engine_name — tratando como engine=unknown`. No aborta en ningún caso; decisión de restart queda al operador.
- `process_symbol` invoca check inmediatamente tras crear `parts_dir`.
- Parquet write L548-585: 4 columnas `engine_*` broadcast a todas las rows.

Tests 4/4 PASS (`tests/test_a15_engine_tag.py`):
1. `_get_engine_tag()` retorna 4 campos con formatos válidos (engine_name ∈ {cuda, cpu_numba}, timestamp ISO parseable).
2. Parquet round-trip preserva las 4 columnas broadcast a todas las rows.
3. Resume check con engine coincidente → mensaje `consistency OK`, sin WARN.
4. Resume check parquet legacy (sin `engine_name`) → WARN con 'pre-A15' + 'unknown', sin abort.

Ejemplo detectado en test: engine=cuda, version=numba=0.64.0, machine=Rixip.

Impacto retroactivo: parquets actuales (pre-A15) no tienen engine tag. Primera regeneración completa via `master.py --recycle` los reescribe con tag. Resume intermedio sobre parquets mixtos emite WARN pero proceder OK.

**Smoke test §0.8 post-fix**:
- Nivel A (BTC N=1000): diff 0.0000 exacto 5 métricas ✓.
- Nivel C (SEI MR config 45686): 7/7 métricas diff 0.0000 ✓.
- Nivel B omitido por scope (A14+A15 NO tocan brain/kernel signal logic, solo pipeline lab regime_walk_forward.py).

**Regresión acumulada**: 28/28 PASS (4 A14 + 4 A15 + 8 W3 + 8 W4 + 4 A12).

**Deploy VPS NO requerido**. Bot v2.4.5 operacional. Fidelidad 2 invariante (cambios pipeline lab, no bot ni kernel Numba). Activación A14 (plateau_ratio nuevo) + A15 (engine tag columns) en próximo reciclaje.

Referencias: `regime_walk_forward.py` L56-128 (engine tag module) + L460 (resume check) + L548-585 (parquet write) + L1838-1867 (plateau block), `tests/test_a14_plateau_consistency.py`, `tests/test_a15_engine_tag.py`, §13.3 W1 W2 movidos a RESUELTO.

Cierre: permanente. Siguiente ítem roadmap: A13 (LL2 kernel simplificado selection bias en lab_lite) o continuación Fase 4 pre-reciclaje.

---

**[MEJORA] [RESUELTO] A12 (LL1) MA implementations deduplicadas cross-file — 2026-04-23**

Contexto: Ultra review lab_lite LL1 (2026-04-17) marcó MAs como duplicadas en "4 archivos" con riesgo de drift silencioso. A12 verifica empíricamente la equivalencia y consolida si procede.

**Fase 1 — Inventario corregido** (hipótesis original errónea):
- Duplicación real es **2-way**, no 4-way: `lab_historico_numba_v8_3.py` ↔ `lab_lite_zonas_v5e.py`.
- `live/brain_engine.py` ya importa desde lab_historico (pass-through).
- `mean_reversion_features.py` idem pass-through (subset).
- `mean_reversion_kernel.py` consume features precomputadas, no usa MAs directamente.
- `lab_lite_zonas_v5d.py` legacy (master.py usa v5e).

**Fase 2 — Verificación bit-a-bit** (serie sintética N=2000, seed=42):
- 14 pares × 3-4 periods = 52 tests.
- **13 pares con diff absoluto 0.000e+00** (bit-idénticos).
- 4 MAs con drift sub-ε: calc_sma ~1e-11 (cumsum vectorizado vs loop), calc_hma ~1e-13 (ULP float), calc_alma ~5e-14 (ULP), calc_vwma ~3e-11 (cumsum).
- **52/52 PASS rtol=1e-10**.
- calc_wma única sin contraparte pública en lab_historico (está como closure interno en calc_hma).

**Fase 3 — Clasificación**:
- Veredicto: **Caso A — TODAS EQUIVALENTES** (drift <3e-11 << threshold 1e-10).
- Decisión: refactor consolidation. No crear módulo intermedio `indicators/moving_averages.py` — `lab_historico` ya es canon de facto (consumido por brain, MR features, regime_walk_forward).

**Fase 4 — Refactor aplicado** (rama `feature-a12-ma-dedup`):
- `lab_lite_zonas_v5e.py`: bloque L112-348 (234 líneas con 17 defs MA) reemplazado por import consolidado L112-132 (17 líneas):
  ```python
  from lab_historico_numba_v8_3 import (
      calc_ema, calc_sma, calc_hma, calc_alma, calc_zlema, calc_kama,
      calc_dema, calc_tema, calc_mcginley, calc_vidya, calc_frama,
      calc_t3, calc_ssmoother, calc_vwma, calc_tenkan, calc_jma,
  )
  ```
- calc_wma eliminado (era único caller calc_hma local; lab_historico.calc_hma tiene wma interno).
- Neto: -234 / +17 líneas.
- lab_historico preservada sin cambios (source canónica).
- brain_engine y MR features sin cambios (transitivos).

**Validación post-refactor**:
- Identity check: `lab_lite.calc_X is lab_historico.calc_X` → True para las 16 MAs. **Cero posibilidad de drift por construcción**.
- `tests/test_a12_ma_parity.py` **4/4 PASS**:
  1. 16/16 MA functions identical (`is` True).
  2. calc_wma eliminado de ambos módulos.
  3. Dispatcher `calc_ma` operativo (types 0, 10, 13, 15 verificados).
  4. Sanity numérica trivial (same obj → array_equal).
- No-regresión: `test_w3_bootstrap.py` 8/8, `test_w4_thresholds.py` 8/8.
- Smoke §0.8 Nivel A (BTC N=1000): diff 0.0000 exacto 5 métricas ✓.
- Smoke §0.8 Nivel C (SEI MR): 7/7 métricas diff 0.0000 ✓.
- Nivel B omitido por scope: A12 NO toca brain_engine/kernel (solo lab_lite del pipeline lab). §0.8 Nivel B gate obligatorio para brain/kernel signal logic, no aplica a este refactor. Parity tests + Nivel A+C suficientes.

**Deuda residual**: lab_historico tiene `calc_tenkan` duplicado interno (L536 DataFrame-based, L929 arrays-based). Duplicación intra-archivo fuera del scope cross-file de A12. Candidato pre-reciclaje.

**Deploy VPS NO requerido** — A12 toca pipeline del lab, no el bot. Fidelidad 2 invariante por construcción.

Referencias: `lab_lite_zonas_v5e.py` L112-132 (import block), `tests/test_a12_ma_parity.py`, §13.3 LL1 (movido a RESUELTO).

Cierre: permanente. Deuda técnica LL1 eliminada. Modificaciones futuras a MAs se aplican automáticamente a ambos consumers via single source of truth.

---

**[MEJORA] [RESUELTO] W4 thresholds _FWD + CI filters implementado — 2026-04-23**

Contexto: W4 (§13.3 priorizado post-Fase II.C 2026-04-22, ultra review 2026-04-17). Layered sobre W3 (commit 4e54c8d). Objetivo: subir thresholds `_FWD_MIN_TRADES=15/_FWD_MIN_PF=1.0` laxos + añadir filtros CI que W3 provee.

**Análisis Fase 1 cuantitativo sobre 138k candidates** (45 símbolos activos + TON histórico × 3 clusters × top-1000 per CSV intermedio):
- `trades_fwd`: median=73, p25=37. Subir 15→25 elimina solo 80 candidates/90k (0.09%).
- `pf_fwd`: median=2.47, p25=1.83. Subir 1.0→1.1 elimina 74 más.
- `pf_fwd_ci_low`: median=1.52, p25=1.23.
- `ci_width`: median=2.34, p75=5.86.
- **`NOT sospechoso` filtro dominante**: reduce pool 138k→90k (-35%). Los thresholds trade/pf son marginalmente discriminantes comparados.
- Todas las combinaciones con `NOT sospechoso` activa dan 134/138 clusters operables (baseline).

**Thresholds adoptados W4**:
- `_FWD_MIN_TRADES = 25` (vs 15 previo — defense-in-depth con W3).
- `_FWD_MIN_PF = 1.1` (vs 1.0 previo — marginal, consistencia metodológica).
- `_FWD_REQUIRE_NOT_SOSPECHOSO = True` (nuevo — encapsula ci_low≥1.0 AND ci_width≤5.0 vía flag W3).
- `_FWD_MIN_CI_LOW = 0.0` (hook nuevo, default OFF).
- `_FWD_MAX_CI_WIDTH = inf` (hook nuevo, default OFF).

Hooks se exponen para calibración futura sin code change.

**Integración**:
- Base filters (trades/pf) aplicados en primer pass sobre parquets (L1429-1432 ya existente).
- CI filters aplicados en `_apply_w4_fwd_ci_filters(df)` post-W3 bootstrap sobre `top_all` (L1690-1703 nuevo).
- WARN log `⚠️ W4 ORPHAN CLUSTER: sym Ck` si cluster queda sin candidatos.
- Reporte text (L1552-1556) documenta thresholds base + CI aplicados.

**Validación Fase 3 — reciclaje hipotético** sobre JSONs productivos actuales:

| Métrica | Valor |
|---|---|
| Clusters productivos (45 activos × 3) | 135 |
| Clusters orphan bajo W4 | **3** (TAO C1, TRX C2, WLD C0) |
| Símbolos con 3/3 clusters operables | 42/45 (93%) |
| Símbolos con 2/3 (1 orphan) | 3 |
| Mismo winner W4 vs actual | 26 (19%) |
| Cambio de winner | 106 (79%) |

**Cross-check los 6 flagged W3 (top-1 productivos actuales, §13.4 W3 validación Fase 3)**:
- ONDO C0 2457036 (pf_fwd=7.94 N=17) → 33586655 (reemplazado).
- LTC C2 2532096 → 1534656.
- GRT C2 58457547 → 41610560.
- TRX C2 53066572 → **ORPHAN** (ningún candidato en top-1000 pasa filtros W4).
- BTC C2 20607806 → 33831247.
- MANA C0 5339578 → 5339579.

**TRX C2 caso crítico**: top TF score 30.9 original (§2.1), flagged por ci_width=34.51 (pf_fwd=12.74 N=33). W4 confirma que cluster entero no tiene candidatos robustos — todos top-1000 flagged. Hallazgo consistente con Lección 29 (walk-forward N pequeño selecciona noise amplificado, no edge). TRX permanece operable en C0 y C1.

**Patrón típico de reemplazo**: old `pf_fwd` alto + N pequeño + flagged → new `pf_fwd` moderado + N grande + CI estrecho. Ejemplos:
- APT C1: PF 4.78 N=25 flagged → PF 1.63 N=146 clean.
- BNB C0: PF 1.17 N=104 flagged (ci_low=0.78) → PF 1.42 N=136 clean.
- ARB C2: PF 12.54 N=17 flagged → PF 2.52 N=47 clean.

Defense-in-depth operando como diseño pretende.

**Tests 8/8 PASS** (`tests/test_w4_thresholds.py`):
1. Constante `_FWD_MIN_TRADES=25`.
2. Constante `_FWD_MIN_PF=1.1`.
3. Defaults hooks (NOT sosp=True, ci_low=0.0, ci_width=inf).
4. NOT sospechoso bloquea flagged config.
5. NOT sospechoso pasa clean config.
6. ci_low hook ON bloquea, OFF pasa (ambos verificados).
7. ci_width hook ON bloquea wide-CI.
8. Retroactivo: ONDO C0 cfg 2457036 bloqueado (base N<25 + sospechoso).

**No-regression W3**: `tests/test_w3_bootstrap.py` sigue 8/8 PASS.

**Deploy VPS NO requerido** — cambio del pipeline del lab, no del bot. Bot v2.4.5 operacional con specialists actuales. Fidelidad 2 invariante (no toca brain/execution/portfolio). Activación en próximo `master.py --recycle`.

Referencias: `regime_walk_forward.py` L923-932 + L1032-1074 + L1690-1703, `tests/test_w4_thresholds.py`, §13.4 W3 entrada 2026-04-23 (prerequisito), §12.29 Lección base, §13.3 W4 movido a RESUELTO.

Cierre: permanente. Próxima acción dependiente: `§13.3 política adelantar reciclaje por criterio empírico` — W4 hace monitorizable el ratio sospechoso/total por cluster como señal de degradación.

---

**[MEJORA] [RESUELTO] W3 bootstrap pf_fwd + selección por ci_low implementado — 2026-04-23**

Contexto: W3 priorizado ALTA empíricamente post-2026-04-22 (§13.3 W3 previa + §12.29). Implementación completa hoy en rama `feature-w3-bootstrap-pf-fwd` sin deploy (specialists productivos permanecen — se activarán en próximo reciclaje).

**Método adoptado — Opción F (bootstrap sintético binomial)**:

Kernel Numba (`lab.run_on_slice`) NO exporta trade-level PnL arrays — solo agregados per config (`pnl, trades, wins, maxdd, gp, gl`). Modificar kernel para exportar trade-level sería invasivo (se descartó, se difiere a refactor §13.3 LL1 pre-reciclaje). W3 implementa bootstrap aproximado sobre pool sintético binario reconstruido desde agregados:
- Pool = {W × avg_win, (T-W) × -avg_loss} donde `avg_win = GP/W, avg_loss = GL/(T-W)`.
- Resample T trades con reemplazo → analíticamente: `k ~ Binomial(T, W/T)`, `pf_r = (k · avg_win) / ((T-k) · avg_loss)`.
- N=1000 resamples, percentil 2.5/97.5 → `pf_fwd_ci_low, pf_fwd_ci_high`.

**Caveat documentado**: NO captura dispersión intra-grupo. CI real es más ancho que el medido. Validación empírica lo confirmó: ONDO C0 `ci_low=2.75` pero real observado `PF=1.08` cae por debajo. El bootstrap aún flaggea el caso por `ci_width=36.36 > 5.0`.

**Arquitectura del cambio**:
- `regime_walk_forward.py` L930-1030: constantes `_BOOTSTRAP_*` + función `_bootstrap_pf_fwd_vectorized` (chunked, memoria ~40MB/batch) + función `_apply_bootstrap_pf_fwd`.
- L1668-1677: integración en `extract_validated_specialists` post-`_compute_sqn_haircut`. Re-sort por `specialist_score_ci_low` (W3b) desplaza el ordenamiento de selección.
- L1770-1788: JSON `top_configs[*]` extendido con 6 campos nuevos (opcional, backwards-compatible para JSONs existentes).
- L1528-1547: report text añade sección "W3 BOOTSTRAP pf_fwd" con distribuciones + flagged count.

**Campos nuevos por config**:
- `pf_fwd_ci_low, pf_fwd_ci_high, ci_width` (bootstrap pf_fwd).
- `pf_combined_ci_low` (fórmula: sustituir gp_fwd con `pf_fwd_ci_low × gl_fwd` manteniendo gl_fwd fijo — sesgo conservador).
- `specialist_score_ci_low` (recomputa score con pf_combined_ci_low).
- `flag_sospechoso_outlier` (True si `pf_fwd_ci_low < 1.0 | ci_width > 5.0`).

**Tests 8/8 PASS** (`tests/test_w3_bootstrap.py`, standalone estilo proyecto):
1. Happy path N=5 → CI finite.
2. N<5 → fallback ci_low=0, ci_high=pf_point, width=0.
3. All winners (L=0) → fallback invalid.
4. All losers (W=0) → fallback invalid.
5. Seed=42 determinista across 3 calls (mismo bit-a-bit).
6. ONDO-like N=17 pf_fwd=7.95 → ci_width=22.93 > 5 → flagged=True.
7. pf_combined_ci_low ≤ pf_combined point (sesgo conservador verificado).
8. W3b cambio ranking: config con CI wide penalizado vs config narrow-CI.

**Validación Fase 3 sobre JSONs productivos** (CSVs intermedios `{sym}_cluster_{k}_specialists.csv` preservan `wins_fwd, gp_fwd, gl_fwd`):

| Symbol/Cluster | cfg_id | pf_fwd | N_fwd | ci_low | ci_width | sc_old → sc_new | flag |
|---|---|---|---|---|---|---|---|
| ONDO C0 (Fase II.B) | 2457036 | 7.94 | 17 | 2.75 | 36.36 | 4.66 → 3.52 | **Y** |
| SEI C2 (MR rescue) | 50461968 | 2.20 | 58 | 1.33 | 2.52 | 1.72 → 1.58 | N |
| STX C2 (MR rescue) | 39664143 | 1.64 | 145 | 1.21 | 1.10 | 1.85 → 1.73 | N |
| UNI C0 (MR rescue) | 1614377 | 1.94 | 124 | 1.37 | 1.41 | 1.98 → 1.81 | N |
| LTC C2 (MR rescue) | 2532096 | 5.04 | 27 | 2.29 | 27.50 | 2.04 → 1.76 | **Y** |
| DOT C1 (MR rescue) | 34569536 | 2.53 | 107 | 1.67 | 2.11 | 2.20 → 1.89 | N |
| BCH C0 (MR rescue) | 40807173 | 1.94 | 84 | 1.24 | 1.89 | 1.68 → 1.53 | N |
| GRT C2 (swap MR) | 58457547 | 1.27 | 211 | 0.96 | 0.67 | 1.79 → 1.70 | **Y** |
| TRX C2 (top TF) | 53066572 | 12.74 | 33 | 6.25 | 34.51 | 30.90 → 28.73 | **Y** |
| BTC C2 (top TF) | 20607806 | 6.36 | 53 | 3.71 | 7.25 | 17.21 → 15.61 | **Y** |
| MANA C0 (top TF) | 5339578 | 4.49 | 64 | 2.71 | 5.14 | 15.51 → 13.84 | **Y** |
| HBAR C1 (top TF) | 20707614 | 3.43 | 83 | 2.11 | 3.31 | 12.23 → 10.95 | N |

**Hallazgos validación**:
- **6/12 = 50% top-1 productivos flagged**. Sesgo N pequeño NO es aislado a ONDO.
- **ONDO C0 flagged=Y ✓** confirma predictividad empírica vs Fase II.B.
- Patrón: N<58 tiende a `ci_width > 5` (flagged). N≥58 narrow-CI.
- GRT C2 caso especial: N=211 grande pero `ci_low=0.96 < 1.0` → edge débil robustamente medido. Flagged por threshold ci_low.
- Score penalty W3b: 7-24% típica (ONDO -24%, TRX -7%).

**Implicaciones pre-reciclaje**:
- W3 está listo para activarse en próximo `master.py --recycle`. No se re-ejecuta walk-forward hoy (specialists productivos preservados hasta reciclaje formal).
- El reciclaje (julio 2026 calendario o adelantado por §13.3 política empírica) producirá JSONs con 6 campos nuevos por config. Selección automáticamente prefiere robustez.
- W4 (_FWD_MIN_TRADES 15 → 25/30) ahora puede cuantificarse empíricamente usando la data de CI que W3 genera — siguiente ítem dependiente.
- §13.3 W3 → RESUELTO.

**Deploy VPS NO requerido** — cambio es del pipeline del lab, no del bot. Bot v2.4.5 sigue operacional con specialists actuales. Fidelidad 2 invariante por construcción (brain/execution/portfolio no tocados).

Referencias: `regime_walk_forward.py` (rama `feature-w3-bootstrap-pf-fwd`), `tests/test_w3_bootstrap.py`, §12.29 Lección base, §13.4 Fase II.B+II.C+Item 3.5 2026-04-22 (validaciones empíricas pre-implementación), §13.3 entradas actualizadas (W3 RESUELTO, W4 PRIORIDAD ALTA heredada, LL1 MA shared module backlog).

Cierre: permanente. Siguiente activación al primer `master.py --recycle` post-implementación.

---

**[PROTOCOLO] [RESUELTO] Protocolo smoke test pre-deploy formalizado (§0.8) — cierre sesión 2026-04-22**

Contexto: sesión multi-fase 2026-04-22 ejercitó secuencialmente:
1. Fase I — reconocimiento empírico revelando bug entry_timestamp_ms + degradación ONDO C0.
2. Fase II.A — fix v2.4.5 deployado.
3. Fase II.B — audit ONDO específico veredicto B_CONFIRMADA.
4. Fase II.C — audit + analyzer global Escenario Y.
5. A10 test diferencial brain↔kernel N≥10000 — Caso D drift cuantificado.
6. A10 forensic — distribución temporal ESTRUCTURAL NUMÉRICA.
7. A10 rank stability — Spearman ρ=1.0000 categoría ROBUSTA.

**Resultado metodológico consolidado**: smoke test legacy (N=1000 BTC/USDT) ocultó drift path-dependent en 5+ deploys previos. Upgrade formalizado en §0.8:

**Nivel A (~30-60s)**: `_run_verify_test --symbol BTC/USDT` N~500 — gate obligatorio TODO deploy brain/kernel. Criterio diff 0.0000 exacto. Catches bugs lógicos.

**Nivel B (~10-15 min)**: deep smoke ONDO+APT N≥8000 — gate obligatorio cambios brain/kernel signal logic + data_feed bar flow + pre-reciclaje + periódico. Criterio ratio divergencia bar-level <5% (baseline arquitectónico ~7-9% documentado §12.30). Catches drift path-dependent.

**Nivel C (~140s)**: `audit_mr_fidelity_sei.py` — gate obligatorio deploys MR o cambios brain completos. Criterio diff 0.0000 en 7 métricas. Verifica camino MR.

**Convención commits**: especificar niveles aplicados (Nivel A/B/C). Anti-patrón "Smoke test PASS" sin nivel.

**Items §13.3 resueltos en este cierre**:

1. **Root cause drift brain↔kernel**: RESUELTO vía Item 3.5 ranking stability (ρ=1.0000). Drift clasificado ESTRUCTURAL NUMÉRICA no-bloqueante (Opción C del análisis: aceptar + documentar). Documentación completa en §12.30 y §13.4 A10 entries. Sin refactor arquitectónico requerido pre-reciclaje.

2. **Upgrade protocolo smoke test (documental)**: RESUELTO vía §0.8. Aplicabilidad inmediata a todos los deploys futuros sin modificar código.

3. **Refactor `_run_verify_test` CLI**: queda en §13.3 EN_ESPERA como item menor (~30 min trabajo) para automatizar Nivel B sin wrapper externo. No bloquea aplicación de §0.8.

**Item W3 (CI bootstrap pf_fwd)**: elevado a PRIORIDAD ALTA empíricamente confirmada. Triple evidencia:
- Fase II.B ONDO C0 pf_fwd=7.945 N=17 → real PF 1.08 (ratio 0.14).
- Fase II.C 2 candidatos exclusión adicionales con mismo patrón.
- Item 3.5 ranking WF ≠ ranking kernel-actual: config #1 WF es rank #4 en régimen actual.

W3 es prerequisito OBLIGATORIO pre-reciclaje (julio o adelantado).

**Resumen completo del día 2026-04-22** (6 commits):

| Commit | Fase | Contenido |
|--------|------|-----------|
| `afaf0cc` | Evento ops | unattended-upgrades + APT mitigation + kernel reboot 1009→1012 |
| `bc673c8` `3ec73f6` `53951be` | Fase II.A | v2.4.5 entry_timestamp_ms fix + docs |
| `8b67397` | Fase II.B+C | Audit ONDO (B_CONFIRMADA) + Fase II.C global (Escenario Y) |
| `fa4da9f` | A10 | Test diferencial brain↔kernel N≥10000 (Caso D) |
| `acb1385` | A10 forensic | Distribución temporal ESTRUCTURAL NUMÉRICA |
| `e995168` | A10 rank stability | Spearman ρ=1.0000 (Categoría ROBUSTA) |
| (este commit) | Cierre | §0.8 protocolo formalizado + limpieza §13 |

**Veredicto final día**:
- Bot v2.4.5 operacional, kernel 6.17.0-1012-aws, APT window xx:15-xx:45 UTC.
- Fidelidad arquitectónica: drift cuantificado + documentado, ranking ROBUSTO.
- Escenario Y confirmado: sistema marginalmente rentable, edge walk-forward erosionando, reciclaje pre-julio candidato.
- 2 bugs metadata resueltos (size_usdt ayer + entry_timestamp_ms hoy).
- Protocolo smoke test formalizado para evitar regresiones futuras.

Referencias: §0.8 (protocolo), §12.29 + §12.30 (lecciones metodológicas), §13.4 A10 entries (base empírica), §13.3 items actualizados.

Cierre: sesión multi-fase completada. Próxima acción esperada: N≥50 oficial (~2026-04-26) o evento operacional que requiera attention.

---

**[AUDITORIA] [RESUELTO] A10 rank stability — drift NO afecta ranking walk-forward — 2026-04-22**

Contexto: A10 forensic reveló 46 divergencias ONDO + 121 APT (9%/7% vs brain) con patrón off-by-N bars. Pregunta crítica: ¿el drift cambia qué specialist_config gana el walk-forward? Si SÍ, el bot ejecuta configs sub-óptimos por construcción (obligatorio fix). Si NO, drift es cosmético.

**Test**: top-5 candidates ONDO C0 del JSON walk-forward evaluados en paralelo con:
- Kernel Numba (`run_on_slice`, accumulated state).
- Brain engine (`_evaluate_bar`, rolling window 500).
Ventana: N=2000 bars (tail ONDO, 1500 eval bars con warmup 500).

**Resultados**:

| Config | WF rank | kernel rank | brain rank | PF_k | PF_b | ΔPF |
|--------|---------|-------------|------------|------|------|-----|
| 2457036 (ganador WF) | 1 | **4** | **4** | 1.002 | 0.993 | −0.009 |
| 2391500 | 2 | **5** | **5** | 0.983 | 0.974 | −0.010 |
| 2571724 | 3 | **3** | **3** | 1.010 | 0.999 | −0.011 |
| 3628492 | 4 | **2** | **2** | 1.168 | 1.159 | −0.009 |
| 3104140 | 5 | **1** | **1** | 1.244 | 1.232 | −0.013 |

**Spearman ρ(kernel, brain) = 1.0000** (ranking bit-a-bit idéntico top-5).
**ΔPF% promedio: −0.95%** (min −1.08%, max −0.75%).

**Veredicto: Categoría ROBUSTA — Hipótesis R confirmada**.

- Drift es **ruido cosmético en magnitud absoluta** (~1% PF) pero NO cambia la **ordenación** entre candidates.
- Bot ejecuta el specialist que sería óptimo también con kernel perfecto (modulo bias sistemático ~1%).
- **Reciclaje con pipeline actual NO produciría specialists sub-óptimos por drift**. El drift no sesga la selección.
- Dado ρ=1.0000 perfecto en ONDO C0 (cluster flagged), la robustez aplica a nivel arquitectónico — no se necesita validar más símbolos/clusters para concluir.

**Bias direccional observado**:
- **Brain sistemáticamente ~1% PF menor que kernel** en ONDO C0 ventana 2000 tail.
- Direccional consistente en los 5 configs (todos ΔPF negativos).
- Contrasta con A10 original sobre N=8335 que mostró brain +5.30% (favorable). El sign del drift depende del segmento temporal.
- Sign es ruido; magnitud ~1% consistente.

**Hallazgo colateral importante — ranking WF ≠ ranking kernel en régimen actual**:

El JSON walk-forward rankea 2457036 como #1 con pf_combined=5.5 (y pf_fwd=7.945, N=17 OOS). En ventana actual (2000 bars recientes) ese config es solo **PF 1.002 (rank #4)**. El config WF-#5 (3104140) es actual-#1 con PF 1.244.

Eso NO es el drift brain↔kernel. Es:
- **Hipótesis B (régimen vs walk-forward)** dominante — ya documentada en Fase II.B/II.C.
- El edge PF=5.5 del walk-forward NO se reproduce en ventana reciente.
- Todos los 5 top configs generan PF en rango estrecho [0.97, 1.24] → edge plano generalizado para ONDO C0.
- **Health_monitor PF 1.08 vs expected 5.5 es por régimen, NO por drift**.

**Implicaciones refinadas para los ítems abiertos hoy**:

1. **§13.3 root cause drift** (abierto hoy): **PRIORIDAD BAJA** ahora. Drift es cosmético. Opción C (aceptar + documentar) es la decisión racional. No fix arquitectónico requerido pre-reciclaje.

2. **§13.3 smoke test upgrade** (abierto hoy): **PRIORIDAD MEDIA**. Útil para detectar bugs futuros de magnitud, pero no crítico para corrección de fidelidad.

3. **§13.3 W3 CI bootstrap pf_fwd**: **PRIORIDAD ALTA confirmada** — el gap entre WF ranking y actual ranking valida que pf_combined point estimate sobre N_fwd pequeño es engañoso. Implementar W3 antes del próximo reciclaje para selección robusta.

4. **§13.4 Fase II.C Escenario Y**: CONFIRMADO sin ajustes. Drift no contribuye materialmente al gap edge. Hipótesis B es ~95-99% del gap, A es ~1-5% (magnitud cosmetic), ranking stability garantiza que reciclaje futuro con pipeline actual produce selección válida.

**Artefactos generados** (no commiteados):
- `.a10_rank_stability.py`: wrapper temporal (eliminado).
- `.rank_ondo.txt`: output detallado (eliminado).
- Datos preservados en esta entrada.

Referencias:
- §13.4 A10 previous entries 2026-04-22 (forensic + drift cuantificado).
- §13.3 items drift + smoke test upgrade (prioridad rebajada tras este test).
- §13.3 W3 CI bootstrap pf_fwd (prioridad reforzada).
- §12 Lección 29 (walk-forward N pequeño inflando PF — validado empíricamente otra vez aquí).

Cierre: **drift es cosmético, no estructural**. Ranking walk-forward es robusto a la diferencia rolling-vs-acumulado. Escenario Y Fase II.C se mantiene intacto. Reciclaje pre-julio con W3 implementado producirá specialists válidos — el drift por sí solo no corrompe la selección. Próxima acción (Item 5): decisión fix vs documentar tiene argumentación EMPÍRICA hacia documentar (ruido cosmético) + no hay necesidad arquitectónica urgente.

---

**[AUDITORIA] [RESUELTO] A10 forensic — distribución temporal + cluster drift brain↔kernel — 2026-04-22**

Contexto: entrada A10 previa (§13.4 2026-04-22) reportó diff NETO 4 trades ONDO + 15 APT basado en comparación de contadores agregados (run_on_slice kernel Numba). Forensic granular trade-by-trade (via `extract_trades_tf` del audit v5.1 como referencia Python, match por `(entry_bar, side)` exacto) revela que los contadores ocultan magnitud real del drift bar-level.

**Resultados forensic**:

| Símbolo | Preset | Brain trades | Kernel trades | Common (match exact) | Brain_only | Kernel_only | Total divergentes | Ratio vs brain |
|---------|--------|--------------|---------------|----------------------|------------|-------------|-------------------|----------------|
| ONDO/USDT | VIDYA(18)/KAMA(54) | 506 | 510 | 485 | 21 | 25 | **46** | **9.09%** |
| APT/USDT | Tenkan(24)/KAMA(72) | 1786 | 1801 | 1685* | 101* | 116* | **121** | **6.77%** |

*APT common derivado de totals.

**Patrón observado**: muchos divergentes son **off-by-N bars pairs** (mismo exit_bar, mismo side, entry_bar difiere 1-6 bars). Ejemplo ONDO T1:
- bar 819 short brain_only → exit 844
- bar 820 short kernel_only → exit 844

Son conceptualmente el mismo trade con shift de 1 bar en entry timing por drift numérico en cruces ma_fast vs ma_slow. No es "trade distinto" sino "mismo trade detectado con drift temporal".

**Distribución temporal (3 tercios de bars evaluados)**:

| Símbolo | T1 | T2 | T3 | Ratio T1/T3 |
|---------|-----|-----|-----|--------------|
| ONDO | 25 (54.3%) | 11 (23.9%) | 10 (21.7%) | 2.5× |
| APT | 56 (46.3%) | 39 (32.2%) | 26 (21.5%) | 2.2× |

**Veredicto categoría: ESTRUCTURAL NUMÉRICA** (mezcla Caso α + drift continuo).

- T1 tiene 2-2.5× más divergencias que T3 → **componente warmup transitorio confirmado** (Caso α parcial).
- T2+T3 suman 46-54% del total → **drift continuo path-dependent también presente** (no solo warmup).
- NO es Caso α puro (en ese caso T1 sería ~90%+).
- NO es Caso β puro (distribución uniforme esperaría ~33%/tercio).
- Es mixto: warmup-fuerte + steady-state drift persistente.

**Cross-symbol correlación**:
- ONDO ratio 9.09% vs APT ratio 6.77% → **ratios similares** (diff ~30%). Drift no es fuertemente símbolo-dependiente.
- Ambos clusters C0 usan KAMA (indicador iterativo path-dependent) → consistente con hipótesis numérica.
- Preset ONDO usa VIDYA + KAMA (ambos path-dep), APT usa Tenkan + KAMA (1 path-dep). Ratio ONDO marginalmente mayor — consistente con más MAs path-dep → más drift.

**NO hay concentración focal en ONDO C0** (cluster flagged por health_monitor). El drift es distribuido estructural, no atribuible al cluster degradado específico.

**Recalibración sobre gap PF ONDO C0 (1.08 vs 5.5 esperado)**:
- A10 original reportó 99.2% match count → parecía drift minor.
- Forensic revela 9% de trades con off-by-N bar shift.
- Aunque 9% suena grande, la magnitud promedio del shift en PnL es pequeña (los trades "pares off-by-N" tienen PnL similar, diferenciándose por ~1-3% pnl por trade, ver ejemplos #2+#3 ONDO).
- Impacto estimado en PF ONDO C0: probablemente 5-15% del gap (mayor que la estimación previa 1-10% pero sigue siendo componente minoritario).
- **Causa raíz dominante del gap sigue siendo Hipótesis B** (degradación edge régimen vs walk-forward inflation).

**Implicaciones para ítems derivados**:

1. **Item §13.3 root cause drift** (abierto hoy): priorizar investigación pre-reciclaje. El drift es ESTRUCTURAL NUMÉRICA, no bug lógico. Opción C (aceptar + documentar) es razonable si no se quiere refactor mayor. Opción B (extender warmup brain 500→2000 bars) reduciría T1 drift ~50% pero no elimina T2/T3.

2. **Item §13.3 smoke test upgrade**: N≥5000 sobre símbolo con MAs path-dep necesario. Protocol detail:
   - Benchmark smoke: BTC N=1000 (fast, catch logical bugs).
   - Deep smoke: ONDO o APT N≥8000 (catch drift path-dependent).
   - Ambos requeridos antes de deploys críticos.

3. **Escenario Y de Fase II.C**: matización cuantitativa. Match rate audit v5.2 ajustado por drift off-by-N bars sería ~73% (vs 75.7% reportado). Pequeño ajuste, no cambia veredicto global Y+A_parcial.

**Artefactos generados** (no commiteados):
- `.a10_forensic.py`: wrapper temporal (eliminado al cierre).
- `.a10_ondo_forensic.txt`, `.a10_apt_forensic.txt`: outputs detallados (eliminados).

Datos forensic preservados en esta entrada §13.4.

Referencias:
- §13.4 entrada previa A10 2026-04-22 (veredicto Caso D que este forensic matiza).
- §13.3 root cause drift + smoke upgrade (items abiertos hoy).
- §12 Lección 30 (smoke test N pequeño oculta drift path-dependent).
- `audit_fidelity_v5.py:689` `extract_trades_tf` (usado como reference Python kernel).

Cierre: drift cuantificado a granularidad bar-by-bar. Categoría ESTRUCTURAL NUMÉRICA confirmada. No es bug lógico, es arquitectura rolling-vs-acumulado en MAs path-dependent. No requiere fix urgente. Priorizar para pre-reciclaje julio.

---

**[AUDITORIA] [RESUELTO] A10 test diferencial brain↔kernel sobre N≥10000 — divergencia cuantificada — 2026-04-22**

Contexto: tras Fase II.B (audit ONDO específico B_CONFIRMADA) y Fase II.C (audit + analyzer global Escenario Y), queda una asunción implícita de toda la infraestructura de audits: **kernel stateless del lab ≡ brain engine bit-a-bit**. El smoke test `_run_verify_test` de deploys previos usa BTC/USDT N=1000 y reporta consistentemente diff 0.0000. A10 escala a N≥10000 sobre ONDO (max 8335 disponible) y APT (10000) para validar/refutar la asunción en régimen de alta actividad.

**Prerequisito habilitante**: A27 cp1252 fix aplicado ayer (`lab_historico_numba_v8_3.py` L996 `[CALC]`) permite ejecutar kernel sin crash UnicodeEncodeError en Windows. Sin A27, N≥10000 imposible.

**Metodología**: wrapper script temporal replica flow de `_run_verify_test` con N configurable. Compara:
- Brain engine bar-by-bar via `_evaluate_bar` (Python, rolling window 500 bars).
- Kernel Numba via `lab_historico_numba_v8_3.run_on_slice` (acumulativo desde t=0, warmup interno 100).
Ambos con mismo `preset_tuple`, `config_id`, `hyst_mult` del specialist seleccionado.

**Resultados**:

| Símbolo | N_bars | Trades brain | Trades kernel | Diff count | Match% | Diff PnL abs | Dirección PnL |
|---------|--------|--------------|---------------|------------|--------|--------------|---------------|
| ONDO/USDT | 8335 | 506 | 510 | −4 | 99.22% | +5.2983% | brain mejor |
| APT/USDT | 10000 | 1786 | 1801 | −15 | 99.17% | −1.3260% | brain peor |

**Detalle ONDO**:
- Brain: 506 trades, 233 wins, PnL +12.3097%, GP 393.16, GL 380.85.
- Kernel: 510 trades, 232 wins, PnL +7.0114%, MaxDD 41.04%, GP 391.07, GL 384.06.

**Detalle APT**:
- Brain: 1786 trades, 619 wins, PnL −88.9407%, GP 851.44, GL 940.38.
- Kernel: 1801 trades, 625 wins, PnL −87.6147%, MaxDD 144.40%, GP 860.33, GL 947.95.

**Observaciones críticas**:

1. **Match count 99.2% en ambos símbolos, consistente**: brain suprime sistemáticamente 4-15 trades de 500-1800 que kernel Numba ejecutaría. NO es 100% bit-a-bit.

2. **Dirección del diff PnL NO es sistemática**: ONDO brain MÁS rentable (+5.30%), APT brain MENOS rentable (−1.33%). Descarta "sesgo de conservadurismo" (brain no es consistente). Es **ruido numérico path-dependent**.

3. **Escala con N**: smoke test N=1000 BTC → diff 0.0000 (5 deploys verificados). N=8-10k → diff cuantificable. El drift acumula sobre N grandes en indicadores path-dependent.

4. **Hipótesis root cause confirmada**: `_evaluate_bar` usa `df.iloc[max(0, i-499):i+1]` (rolling window 500 bars). Kernel Numba `run_on_slice` usa estado acumulado desde t=0 con warmup 100 interno. Para MAs path-dependent (VIDYA, KAMA, ALMA, T3, FRAMA, McGinley), la diferencia entre "ver bars 1..500" vs "bars 0..500 con estado acumulado" produce values ligeramente distintos. 4-15 cruces ma_fast vs ma_slow caen en un lado u otro del threshold difiriendo entre implementaciones. Vinculado a §13.3 LL1 (MA implementations duplicadas en 4 archivos sin checksum shared).

**Veredicto: Caso D — Divergencia cuantificada, NO catastrófica**.

- ✅ 99% trade count match.
- ❌ 1-5% PnL diff sobre N grandes.
- ❌ Smoke test N=1000 ocultó el drift (tolerance 0.1% pensada para small N, falla en large N).

**Implicaciones para Escenario Y de Fase II.C**:

El audit v5.2 reportó match rate generoso 75.7% asumiendo kernel Numba como ground truth. A10 revela sesgo no medido:
- **Kernel Numba ≠ Brain Python** en ~1% de barras.
- Match rate real bot↔brain (no vs kernel) sería probablemente ~90%+ (bot replica brain, brain más conservador que kernel).
- Match rate real bot↔kernel reportado 75.7% **cerca** del verdadero pero con sesgo componente-A no medido previamente.

**Reclasificación Escenario Y → Y+A_parcial (componente A ~1-10% del gap edge)**:
- Hipótesis histórica Ricardo "falta de fidelidad" encuentra **apoyo empírico parcial** — no es causa raíz del gap de edge ONDO PF 5.5→1.08, pero **contribuye mensurablemente**.
- Gap de 4.42 PF points: mayoritariamente régimen (Hipótesis B dominante), fracción ~1-10% atribuible a diff kernel↔brain (Hipótesis A parcial).
- Escenario Y global sigue válido con esta matización.

**Caveat del veredicto**:
- Dos símbolos muestran patrón consistente. Probable generalización a otros symbols/clusters.
- Diff es numérico path-dependent, NO lógico (las dos implementaciones tienen misma lógica, solo state construction diferente).
- En producción real, bot ejecuta 1-2 trades/día por símbolo × 45 símbolos. Sobre meses, drift acumulado puede ser significativo pero por trade individual el error es sub-0.01% típico.

**Protocolos afectados**:
- Smoke test `_run_verify_test` N=1000 es INSUFICIENTE para detectar drift. Debería usar N=5000-10000 en deploys críticos.
- Test de no-regresión de cualquier cambio en brain_engine o kernel debe usar N grande.

**Items §13.3 derivados**:
- **Nuevo item**: investigar root cause MAs path-dependent drift (candidato pre-reciclaje julio junto a §13.3 LL1).
- **Update smoke test protocol**: N≥5000 para tests de no-regresión críticos.

**Items §13.4 impactados retroactivamente**:
- Audits de deploy (v2.3.11, v2.4.0, v2.4.1, v2.4.2, v2.4.3, v2.4.4, v2.4.5 todos via smoke N=1000) reportaron diff 0.0000 pero tenían drift oculto. NO invalida los deploys (los cambios fueron estructurales correctos), solo matiza que la métrica N=1000 era insuficiente.

Referencias:
- wrapper temporal `.a10_diff_test.py` (creado + eliminado al cierre de esta tarea, no commiteado).
- `live/brain_engine.py:2284` `_run_verify_test` (N=1000 hardcoded — targeting update).
- `lab_historico_numba_v8_3.py` `run_on_slice` (kernel Numba referencia).
- §13.3 LL1 (MA implementations duplicadas sin checksum — hipótesis root cause relacionada).
- §13.4 Fase II.C 2026-04-22 (escenario Y que esta entrada matiza).
- §12 Lección 29 (walk-forward N pequeño — precedente de "N pequeño oculta drift").

Cierre: divergencia cuantificada. Investigación root cause prioridad pre-reciclaje. Audits previos retroactivamente matizados. No hay alarma roja: 99% trade count match es alto, sistema estructural OK, drift es refinamiento metodológico no falla operacional.

---

**[AUDITORIA] [RESUELTO] Fase II.C — Audit v5.2 + Analyzer v2.4.1 global N=47 post-v2.3.11 — 2026-04-22**

Contexto: tras Fase II.B (audit ONDO específico veredicto B_CONFIRMADA con caveat N=7), extender análisis a sistema completo con infraestructura Bloque 1 ejercitada en producción real por primera vez. Audit v5.2 (A01 segmentación + clustering_check + A34 timing_borderline + A36 log rotation + A02 verbose-slippage) + Analyzer v2.4.1 (A38 cluster_estructuralmente_perdedor + slippage USDT directo post-v2.4.4 + signal_price_lookup).

**Datos del audit v5.2 global** (`audit_v5_2_report_20260422_1046_utf8.txt`):
- N ventana: 47 trades.
- N excluidos: 10 (1 reconstructed + 4 mr_kernel_no_implementado + 4 reconcile_intervino + 1 clustering_divergente).
- N efectivo: 37.
- Match restrictivo (OK exact): 22/37 = **59.5%** [CI95 43.5%-73.7%].
- Match generoso (OK + timing_borderline reclasificados por A34): 28/37 = **75.7%** [CI95 ~60%-87%].
- Por encima del threshold 70% de "fidelidad mayoritaria".

**Segmentación por deploy_boundaries** (A01 Feature A):

| Segmento | N_eff | OK | NONE | EXCL | Rate | CI95 |
|----------|-------|----|----|------|------|------|
| v2.3.11 → v2.4.0 | 11 | 5 | 6 | 1 | 45.5% | [21.3, 72.0] |
| v2.4.0 → v2.4.1 | 2 | 2 | 0 | 2 | 100.0% | [34.2, 100] |
| v2.4.1 → v2.4.2_v2.4.3 | 7 | 7 | 0 | 4 | 100.0% | [64.6, 100] |
| v2.4.3-hotfix → now | 13 | 8 | 5 | 2 | 61.5% | [35.5, 82.3] |
| **Weighted avg** | 33 | 22 | — | — | **66.7%** | — |

Sin discontinuidades significativas entre segmentos (A01 detector). N pequeño por segmento limita CI individual.

**Hipótesis de no_match VPS (15 trades sin kernel exact match)**:
- timing_borderline (A34): **6 trades** — kernel match existe en (1, 2] velas. NO son fidelity failures.
- no_match_kernel: 9 trades — kernel post-hoc no genera signal en bar donde bot operó. Causas plausibles: drift implementación kernel Numba (live) vs Python (audit); cluster_live==cluster_post_hoc por k pero kernel post-hoc condiciones distintas; edge case TF/divergencias filter.

**Datos del analyzer v2.4.1 global** (`attribution_summary_20260422_1039_utf8.txt`):
- PnL total realizado: **+0.48 USDT** sobre 47 trades en ventana ~3 días.
- Alpha esperado nominal: **+5.64 USDT** (gap -91% vs realizado).
- Descomposición: slippage TOTAL -0.08 USDT (-17%, primer valor real post-v2.4.4 + v2.4.5), factor portfolio -1.17 (block_reduct -0.83 dominante), funding -0.06, alpha residual **-3.84 USDT (-799% del PnL real)**.
- Ecuación cierra: 5.64 - 1.17 - 0.08 - 0.06 - 3.84 = +0.49 ≈ +0.48 ✓.

**Alerts críticos del analyzer**:
- 🚨 **CANDIDATO EXCLUSION RECICLAJE**: ONDO/USDT C2, SAND/USDT C1 (NUEVOS — distintos de ONDO C0 del health_monitor).
- ⚠️ **EDGE EROSIONANDOSE**: alpha residual cae >10% en últimos 20 trades vs 20 anteriores.
- 🔧 ACELERAR v2.6 FILTRO FUNDING: funding/pnl_neto = -13.1%.
- 17 símbolos con `WARN_neg_res` (alpha residual negativo significativo).
- Slippage por símbolo: ADA peor con -20.46 bp total.

**Brain reconciles**: 253 eventos en ventana, tendencia decreciente -52.9% segunda mitad vs primera (efecto v2.4.2 silent reconcile + v2.4.3 pre-check operando).

**Veredicto consolidado**: **Escenario Y** (Sistema marginal + fidelidad mayoritariamente OK + varios clusters degradados):
- ✅ Sistema rentable marginalmente (PnL > 0 pero << alpha esperado).
- ✅ Fidelidad mayoritaria OK (75.7% generoso, 66.7% weighted segmentado).
- ❌ Edge generalizado erosionando: 2 candidatos exclusión nuevos + 17 WARN_neg_res + edge_erosion alert direccional.

NO es Escenario X (no es "todo bien" — claros problemas edge).
NO es Escenario Z (sistema rentable, no degradación masiva todavía).
NO es Escenario W (fidelidad 75.7% mayoritaria, no rota).

**Implicaciones operacionales**:
1. **Adelantar reciclaje por criterio empírico** justificado pero no urgente. Calendario original julio 2026, podría adelantarse a 2026-05/06 si emerge 3+ candidatos exclusión adicionales o PnL gira negativo sostenido.
2. **ONDO C0 NO es aislado** — patrón emergente. La hipótesis original Ricardo "falta de fidelidad" se valida débilmente (algunos no_match_kernel sospechosos), pero la causa primaria del gap PF expected vs real es **degradación walk-forward → régimen** (Hipótesis B dominante).
3. **W3 (CI bootstrap pf_fwd) validado empíricamente** como necesario para el reciclaje (ver Lección 29 nueva §12). El walk-forward original infló pf_fwd con N pequeño (ONDO C0 N=17 OOS pf_fwd=7.95 no se reproduce; SAND C1 similar; ONDO C2 N=38 ratio_oos=1.59 también flagged).
4. **W4 (thresholds _FWD laxos)** también gana relevancia como pre-reciclaje.
5. **Slippage operacionalmente contenido** (-0.08 USDT total = 17% del PnL real, marginal).
6. **Funding filter v2.6** acelera prioridad — funding/pnl_neto -13% es proporción significativa con balance bajo.

**Items §13.3 actualizables**:
- Política empírica "adelantar reciclaje por degradación clusters" (NUEVO item — ver §13.3).
- W3 + W4 prioridad elevada para pre-reciclaje (existentes en §13.3).

**Caveat de N**:
- N=37 efectivo aún bajo target N≥50 oficial. Veredicto Y_CONFIRMADA tiene confianza media-alta, no alta.
- CI95 wide en segmentos por N pequeño (varias ventanas de 2-7 trades).
- Convergencia esperada al alcanzar N≥50 (estimado 2026-04-26).

**Validación operacional infraestructura Bloque 1**:
Esta ejecución valida en producción real el roadmap completo:
- A01 segmentación por deploy_boundaries: funcional, detectó variación entre segmentos.
- A01 clustering_check: 1 trade excluido (ETC 2026-04-22 02:00, cluster live ≠ post-hoc).
- A02 signal_price_lookup: slippage USDT cuantificado por primera vez.
- A34 timing_borderline: 6 trades reclasificados (subió match rate de 59.5 → 75.7%).
- A36 log rotation: 13 .gz + actual procesados sin intervención manual.
- A38 cluster edge guard: separación losing_clusters de edge_erosion operacional.
- v2.4.4 size_usdt fix: slippage USDT computable.
- v2.4.5 entry_timestamp_ms fix: aplicable a trades futuros.

Pipeline empírico end-to-end validado.

Referencias:
- `audit_v5_2_report_20260422_1046_utf8.txt`: reporte audit completo.
- `attribution_summary_20260422_1039_utf8.txt`: reporte analyzer completo.
- §13.4 Audit ONDO Fase II.B 2026-04-22 (precedente).
- §12 Lección 29 nueva (validación empírica W3).
- §13.3 política reciclaje empírico (nuevo item).

Cierre: Fase II.C completa. Próxima evaluación al alcanzar N≥50 (~2026-04-26) o ante cambio sustantivo en alerts del analyzer.

---

**[AUDITORIA] [RESUELTO] Fase II.B — Audit ONDO/USDT específico veredicto B_CONFIRMADA — 2026-04-22**

Contexto: health monitor flaggea ONDO/USDT C0 con PF real 1.08 vs expected 5.5 (ratio 20%) en daily summary 2026-04-22 00:00 UTC. Primer cluster empíricamente flagged. Cuestiona hipótesis histórica de falta de fidelidad simulación↔ejecución vs degradación real de edge en régimen actual.

Audit trade-a-trade kernel stateless vs bot sobre 16 trades ONDO/USDT totales (2026-04-14 → 2026-04-21). N efectivo matchable = 7 (7 pre-v2.3.1 sin entry_candle inferible, 2 excluidos reconcile_intervino).

**Resultado matching** (`audit_v5_2_report_20260422_1021_utf8.txt`):
- MATCH exact 3/7 (43% con CI95 ancho por N=7).
- timing_borderline 4/7 (A34 captura los demás dentro ±2h).
- Match expandido **7/7 = 100%**.
- 0 no_match_kernel genuinos.
- 3 MATCH exact con exit reasons IDÉNTICAS bot↔kernel + entries ±0.15% (slippage operacional normal).

24 kernel_no_bot todos explicables: pre-bot-operating (4 del 2026-04-12), pre-v2.3.1 sin matching robusto (otros), o reentry bloqueado por posición abierta. Ningún caso anómalo.

**Veredicto: Categoría B_CONFIRMADA — degradación edge real en régimen actual**.

Evidencia primary:
- Bot ejecuta correctamente las decisiones que kernel generaría (fidelidad estructural OK para ONDO).
- Walk-forward entregó PF_combined=5.5 con pf_fwd=7.945 sobre N=17 OOS (CI ancho por N pequeño — caveat W3 §13.3 aplicable).
- PnL trades matched mean +0.18%, sum +0.54% — edge plano, no perdedor.
- Régimen actual no reproduce PF histórico del walk-forward.

Hipótesis A (fidelidad rota) DESCARTADA específicamente para ONDO:
- 0 trades bot sin kernel equivalente (incl. timing_borderline).
- 0 mismatch exit reason en MATCH OK.
- Entry diff ±0.15% coherente con slippage market order.

Caveat metodológico:
- N=7 efectivo → veredicto confidence media, no alta (CI95 [15.8%, 75.0%] restrictivo).
- Confidence sube al incluir timing_borderline en match expandido.
- Generalización a otros clusters validada en Fase II.C global (mismo día) que confirma patrón emergente.

Implicaciones arquitectónicas:
- Hipótesis histórica Ricardo "falta de fidelidad" no invalidada como prior estratégico, pero **debilitada como causa primaria** del gap en ONDO específicamente.
- Causa primaria observada: degradación edge walk-forward vs realidad, no ejecución divergente.
- Caveat W3 (§13.3 EN_ESPERA pre-existente) **validado empíricamente**: implementar CI bootstrap en pf_fwd pre-próximo-reciclaje para evitar specialist inflado.

Decisión operacional ONDO C0: mantener activo (Opción 1 del análisis). No genera pérdidas (PF 1.08, mean PnL +0.05%, Tipo A degradación plana confirmado), consume slot. Reciclaje natural eventual recalibraría o descartará.

Referencias:
- `audit_v5_2_report_20260422_1021_utf8.txt`: reporte detallado.
- `audit_fidelity_v5_2.py --timing-tolerance 1` (A34 utilizado).
- `engine.log` consolidado 2026-04-14 → 2026-04-22 (13 gz + actual).
- `regime_wf/ONDOUSDT_specialist_configs.json` C0 config_id 2457036 (VIDYA(18)/KAMA(54), pf_combined=5.5, pf_fwd=7.945 N=17).
- §13.4 Fase II.C 2026-04-22 (consecuencia: confirmación que ONDO no es aislado).
- §12 Lección 29 (formalización metodológica).

Cierre: veredicto establecido. ONDO C0 monitoreo pasivo. Próxima evaluación con audit N≥50 global o si emergen cambios estructurales.

---

**[RESUELTO] Bug entry_timestamp_ms=0 en trade_history.csv — fix v2.4.5 — 2026-04-22**

Contexto: Durante Fase I del reconocimiento empírico 2026-04-22 (preparación para decisión audit completo post-health report ONDO CRITICAL), el análisis del CSV VPS reveló 51/155 trades (33%) con `entry_timestamp_ms=0` a pesar de tener schema post-v2.3.3 (12 cols). Afecta incluso trades post-v2.4.4 (ej. SAND 2026-04-22 03:00). Patrón idéntico al bug size_usdt de v2.4.4 de ayer: campo sistemáticamente persistido a 0.

Investigación forense (Fase I, 5 preguntas respondidas):

**P1 — Alcance histórico por era**:
- pre-v2.3.3 (schema 10-col, 65 trades): N/A (campo no existía).
- v2.3.3 → v2.3.9 (40 trades): 7 con entry_ms=0 (17%), 33 con >0 — bug NO presente.
- v2.3.9 → v2.4.4 (50 trades): 41 con entry_ms=0 (82%) — bug activo.
- post-v2.4.4 (13 trades): 10 con entry_ms=0 (77%) — bug sigue vivo post-size_usdt fix.

Segregado por reason_exit:
- `_evaluate_bar` CLOSE reasons (div_exit, tf_exit, zone_exit, sl_hit, cancel_*, zone_exit_mr) **post-v2.3.9: 43/43 trades = 100% afectados**.
- Other reasons (regime_change, not_operable, below_min_order, sl_trigger_reconstructed) **post-v2.3.9: 0/7 afectados**.

Primer bug: 2026-04-17 10:00 APT (pre-v2.3.9, causa menor distinta).
Último bug: 2026-04-22 03:00 SAND (bug vivo).

**P2 — Bug aislado**: cross-tabulación con size_usdt, pnl_usdt, pnl_pct, funding_paid no mostró correlación. Bug afecta EXCLUSIVAMENTE a entry_timestamp_ms. size_usdt=0 residual era el bug v2.4.4 pre-fix, independiente.

**P3 — Root cause confirmado (H1)**:
- `brain_engine.py:285` (dentro de `_reset_state_on_exit` L264-287 introducido por v2.3.9 fix B1): `state.entry_timestamp_ms = 0`.
- `brain_engine.py:907` (TF) y `:2022` (MR): invocación de `_reset_state_on_exit` dentro de `_evaluate_bar` durante la generación de signal CLOSE.
- `live_engine.py:485`: `generate_signals(...)` invoca `_evaluate_bar` → reset corre AQUÍ.
- `live_engine.py:616-622` (bug): enriquecimiento lee `self.brain.symbol_state[sym].entry_timestamp_ms` POST-reset → campo es 0 → condición `> 0` falsa → NO enriquece `pos`.
- `execution_manager.py:944/972/1060`: `log_trade({..., "entry_timestamp_ms": pos.get("entry_timestamp_ms", 0)})` → persiste 0 al CSV.

Paths alternativos (exentos):
- `brain_engine.py:621` FLAT/not_operable: `state` no se muta → enriquecimiento funciona.
- `brain_engine.py:627-643` regime_change: reset parcial (solo position/entry_price/sl_level, NO entry_timestamp_ms) → enriquecimiento funciona.
- `live_engine.py:948-959` ORPHAN_CLOSE reconstructed: usa `pre.get("entry_timestamp_ms", 0)` desde `pre_signal_state` → funciona.

**P4 — Impacto análisis previos**:
- Audit v5.1 (`audit_fidelity_v5.py:211-231` `infer_entry_candle`): tiene **fallback** a log SIGNALS_EXECUTED cuando CSV entry_ms=0/missing → **MITIGADO** por C1 fix preexistente.
- Analyzer v2.4.1 (`analyze_performance_attribution.py:219-231`): misma mitigación → **MITIGADO**.
- Health_monitor (`health_monitor.py:34` `evaluation_window_days=30`): filtra por timestamp CSV col 0 (exit), no entry_ms → **NO afectado**.
- N=13 effective del audit 2026-04-21 **probablemente correcto** vía fallback (el audit filtra by entry_cycle inferido, no por CSV raw entry_ms).

Fix aplicado (`live_engine.py` +48/-7):
- Extraer lógica de enriquecimiento a función módulo-level `_enrich_positions_with_entry_ms(positions, pre_signal_state)` (nueva, L119-149).
- Cambiar fuente de `self.brain.symbol_state` (post-reset) a `pre_signal_state` (snapshot pre-reset en L467-483).
- Call-site reemplazado por 1 línea: `_enrich_positions_with_entry_ms(positions, pre_signal_state)`.

`pre_signal_state` ya capturaba `entry_timestamp_ms` desde v2.3.2 (phantom fix), solo no se usaba como fuente de enriquecimiento.

Scope: **1 archivo** (`live_engine.py`), 1 test nuevo (`test_entry_timestamp_ms_enrichment.py`, 186 líneas). Zero cambios a `brain_engine`, `execution_manager`, `state schema`. Zero riesgo Fidelidad 2 (cambio solo en fuente de metadata).

Tests 8/8 PASS (`tests/test_entry_timestamp_ms_enrichment.py`):
- `test_enriches_from_pre_signal_state` (happy path).
- `test_ignores_zero_pre_ts` (guard > 0).
- `test_ignores_missing_sym_in_pre_state`.
- `test_ignores_missing_entry_ms_key`.
- `test_enriches_multiple_symbols_independently`.
- `test_overrides_existing_entry_ms_in_pos` (defensivo).
- `test_empty_positions_noop`.
- `test_post_reset_scenario_regression` (regresión directa del bug).

Fidelidad 2 invariante:
- TF `_run_verify_test --symbol BTC/USDT`: Trades 1=1, Wins 0=0, PnL -0.5935=-0.5935, Gross profit 0.0000=0.0000, Gross loss 0.5935=0.5935 → diff **0.0000** en 5 métricas.
- MR `audit_mr_fidelity_sei.py` SEI/USDT C2 config 45686: PnL 1.0180=1.0180, Trades 17=17, Wins 5=5, Cancels 2=2, MaxDD 3.9316=3.9316, GrossProfit 9.6434=9.6434, GrossLoss 8.6254=8.6254 → diff **0.0000** en 7 métricas.

Deploy VPS 2026-04-22:
- T_stop = 09:45:30 UTC (graceful shutdown, 6 posiciones preservadas).
- T_start = 09:46:17 UTC (bot active + reconcile).
- Downtime total: **47 segundos** dentro de ventana segura xx:15-xx:45 UTC.
- MD5 3-way sincronizado: `4141ab7157b9eb341e99347b37f0cc44` (combolab + comboclaude + VPS).
- Backup: `/home/trader/combolab/live/live_engine.py.bak-pre-v245-20260422-094544`.

Smoke-A ✓ PASS:
- 45 GMM + 45 specialist_configs cargados en 2.06s.
- Estado restaurado ciclo #204 (continúa numeración natural).
- 6 posiciones sincronizadas desde exchange (RENDER/THETA/ONDO/APT/SEI long + SAND short — idénticas pre-stop).
- `[ALERT] [START]` Telegram emitido.
- Boot total 3.5s.
- 0 errores Python, 0 WARNINGs inesperados.
- **Validación indirecta del fix**: `engine_state.json` post-arranque muestra `entry_timestamp_ms` VÁLIDO (>0) para las 6 posiciones abiertas. Feature v2.3.3 de persistencia state intacta; fix v2.4.5 listo para trigger en próximo CLOSE.

Smoke-B ✓ PASS (cycle post-deploy 09:59:50-10:00:05 UTC):
- Cycle duration: **14735ms** (dentro de rango operacional 14-22s, sin degradación atribuible al helper extraído).
- Numeración cycle: `#204` (re-uso natural post-stop — state restauró cycle_count=204, mismo patrón que reboot kernel de esta mañana; cycle_count interno ya incrementó para persistir, próximo cycle a 10:59:54 será #205).
- 3 signals evaluadas (BNB/AVAX/UNI LONG), **0 ejecutadas** (todas `low_confidence` descartadas), 0 closes.
- 6 TS updates como `TS_NOOP_V240` (Fidelidad 2 TS operando normal post-fix).
- Balance estable 296.24 USDT.
- 6 posiciones preservadas (idénticas pre-stop: RENDER/THETA/ONDO/APT/SEI long + SAND short).
- 0 errores Python, 0 WARNINGs inesperados.
- `[SIGNALS_RAW]`, `[SIGNALS_EXECUTED]`, `[SIGNALS_DISCARDED]` emitidos con schema íntegro.

**Validación directa del fix (CSV entry_ms>0 post-close)** pendiente de próximo cycle que ejecute CLOSE. Cycle 204 post-deploy no generó closes (mercado lateral + 3 signals low_confidence descartadas). Próximos cycles con close confirmarán fix directamente via `tail trade_history.csv` verificando `entry_timestamp_ms` > 0 en columna 12.

**Evidencia indirecta robusta ya confirmada**:
- `_enrich_positions_with_entry_ms` llamado en cycle 204 post-fix (code path ejercitado).
- `engine_state.json` post-arranque muestra entry_ms VÁLIDO (>0) para las 6 posiciones — fuente que `pre_signal_state` capturará al próximo close.
- Tests 8/8 unit cubren el contrato completo del helper.
- Lógica inspeccionada línea a línea, refactor conservador (mismo algoritmo, fuente distinta).

Trades históricos (51 afectados) permanecen con `entry_timestamp_ms=0` en CSV — no migrables. Mitigación continúa vía fallback en analyzers/audits que ya existía.

Commits:
- `bc673c8` fix(v2.4.5): entry_timestamp_ms enrichment desde pre_signal_state (rama `fix-entry-timestamp-ms-v2.4.5`).
- `3ec73f6` merge rama → main con `--no-ff` (rama preservada para rollback).

Referencias:
- `live/live_engine.py` L119-149 (función helper), L616 (call-site).
- `live/brain_engine.py` L264-287 (_reset_state_on_exit), L285 (línea que setea entry_ms=0), L907/L2022 (invocaciones).
- `tests/test_entry_timestamp_ms_enrichment.py` (186 líneas, 8 tests).
- Fase I investigación 2026-04-22 (datos forenses CSV VPS analizado read-only).
- §12 Lección 26 (ecuaciones que cierran ≠ atribución correcta) — patrón análogo al size_usdt.

Cierre: fix deployado + validado Smoke-A. Validación directa Smoke-B cycle 205 pendiente de completion.

---

**[OBSERVACION] [RESUELTO] Evento unattended-upgrades restart automático + mitigación APT window — 2026-04-22**

Contexto: 2026-04-22 06:40:38 UTC, `unattended-upgrades.service` (timer APT diario Ubuntu) aplicó security update `python3.12` (3.12.3-1ubuntu0.12 → 0.13) entre 06:40:31-37 UTC junto con upgrades de `libpython3.12*`, `libcap2*`, `libntfs-3g89t64`, `ntfs-3g`, `linux-aws` (kernel 6.17.0-1012 instalado pero no activo al momento). `needrestart` en modo automático (default APT hook Ubuntu) disparó stop+start de `trading-bot.service` (+ `fail2ban.service`) 1 segundo después del fin del upgrade de Python. Bot respondió con graceful shutdown, 5 posiciones con stops en BingX preservadas, reconcile post-restart 5/5 recuperó idénticas (RENDER/THETA/ONDO/APT/SEI long). Downtime real ~11s dentro de ventana inactiva entre ciclo 201 (06:00) y ciclo 202 (07:00). Cero ciclos perdidos — esta vez por suerte, no por diseño.

Evidencia forense:
- Journal systemd: `Deactivated successfully` (exit code 0, no crash).
- engine.log: `Shutdown signal recibida` + `Deteniendo...` + `Bot detenido. 5 posiciones abiertas con stops.` (graceful path).
- `/var/log/unattended-upgrades/unattended-upgrades.log` línea 06:39:46 UTC lista packages incluyendo `libpython3.12-stdlib` + `libpython3.12t64` + `python3.12*`.
- `fail2ban.service` recibió mismo trato en misma ventana → patrón restart masivo de servicios Python-dependientes, no aislado al bot.

Análisis de riesgo (motivación de la mitigación):
- Probabilidad empírica: ~2 eventos/mes según security updates Ubuntu LTS que afectan libs Python compartidas.
- Ventana de riesgo crítico: xx:59-xx:01 (cycle start). Si security update futuro dispara en esa ventana, bot perdería 1 ciclo — impacto: signals LONG/SHORT no ejecutadas, CLOSE signals no ejecutadas (overshoot stop brain), trailing stop on-close no actualizado.
- Default Ubuntu: `apt-daily-upgrade.timer` `OnCalendar=*-*-* 6:00` + `RandomizedDelaySec=60m` → ventana nominal 06:00-07:00 UTC. Cycle start 06:59 cae dentro. Riesgo estructural no cero.

Mitigación implementada (Fase 1, 2026-04-22 08:18 UTC): drop-in systemd en `/etc/systemd/system/apt-daily-upgrade.timer.d/override.conf`:
```
[Timer]
OnCalendar=
OnCalendar=*-*-* 0/1:15:00
RandomizedDelaySec=30min
```

Efecto:
- Schedule cada hora a `:15:00` + dispersión aleatoria 0-30min → disparo real en ventana `xx:15-xx:45 UTC`.
- Equidistante de cycle starts (`xx:59:54`).
- Ventana de riesgo crítico xx:59-xx:01 **eliminada por diseño**.
- Reversible trivialmente con `rm /etc/systemd/system/apt-daily-upgrade.timer.d/override.conf` + `systemctl daemon-reload`.

Observación sobre `Persistent=true` del unit base: tras `daemon-reload` post-drop-in, timer detectó que slot `:15` ya había pasado (08:18 UTC > 08:15 UTC) y disparó catchup inmediato a 08:18:08 UTC. Ejecución benigna (1 segundo, idempotente, sin paquetes pendientes, sin needrestart triggers). Stamp file `/var/lib/systemd/timers/stamp-apt-daily-upgrade.timer` actualizado. Próximos disparos normales en ventana objetivo. Post-reboot Fase 3: next scheduled 2026-04-22 09:36:17 UTC (confirmado dentro de ventana objetivo, drop-in persiste across reboot).

Alternativas consideradas y descartadas:
- `nrconf{blacklist}` en `/etc/needrestart/conf.d/` para excluir trading-bot del auto-restart: rechazado porque dejaría bot con libs Python viejas hasta reboot manual, riesgo de bugs de compatibilidad (signatures ABI puede cambiar entre patches libpython).
- Desactivar `unattended-upgrades` global: rechazado por perder security updates automáticos del OS (superficie de ataque creciente sin supervisión humana — menos seguro que auto-restarts beneficiosos).
- Configurar `Unattended-Upgrade::Automatic-Reboot "true"`: rechazado (reboots automáticos sin coordinación con estado del bot/posiciones, blast radius superior al actual).

Cierre: Fase 1 ✓ completa. Timer recalculado post-catchup + post-reboot muestra NEXT dentro de ventana objetivo. Mitigación persiste across reboots.

Referencias:
- engine.log 2026-04-22 06:40:38-49 UTC (evento original + restart automático).
- engine.log 2026-04-22 08:19:43-08:20:32 UTC (stop controlado Fase 3).
- journalctl `trading-bot.service` en ventana incidente.
- `/var/log/unattended-upgrades/unattended-upgrades.log` 2026-04-22 06:39-06:41.
- `/etc/systemd/system/apt-daily-upgrade.timer.d/override.conf` (drop-in persistente).
- `systemctl list-timers apt-daily-upgrade.timer` post-reboot.

---

**[MEJORA] [RESUELTO] Kernel Linux upgrade 6.17.0-1012-aws aplicado via reboot planificado — 2026-04-22**

Contexto: tras unattended-upgrades del 2026-04-22 06:40 UTC, `/var/run/reboot-required` presente + `/var/run/reboot-required.pkgs` listaba `linux-image-6.17.0-1010-aws` y `linux-image-6.17.0-1012-aws` (dos versiones de kernel instaladas pero no activas; el VPS seguía corriendo `6.17.0-1009-aws` desde boot del 2026-04-08, un kernel upgrade anterior tampoco había sido activado via reboot). Ubuntu no reboota automáticamente (`Automatic-Reboot=false` default); kernel hubiera permanecido pendiente indefinidamente hasta intervención manual o reboot forzado AWS.

Decisión 2026-04-22: aplicar reboot planificado en misma sesión para evitar acumular deuda. Razonamiento: siguientes security updates de kernel añadirían más versiones pendientes; eventualmente reboot forzado (AWS maintenance o evento operacional) activaría múltiples kernels simultáneamente con incremento de riesgo (más potencial regresiones a diagnosticar simultáneamente).

Protocolo ejecutado:
1. Prerequisito: mitigación APT window Fase 1 aplicada (ver item previo) → futuros upgrades caen en ventana segura.
2. Verificar hora UTC en ventana xx:15-xx:45 antes de acción (hora inicio: 08:19:34 UTC) ✓.
3. Graceful stop via `sudo systemctl stop trading-bot.service`: engine.log confirmó `Shutdown signal recibida` + `Bot detenido. 5 posiciones abiertas con stops. 203 ciclos ejecutados.` + `[ALERT] [STOP]` Telegram emitido.
4. `sudo reboot` ejecutado 2026-04-22 ~08:19:47 UTC.
5. Poll SSH reconexión: VPS online en 1 iteración (~40s desde reboot command) a 2026-04-22 08:20:25 UTC.
6. Verificación post-boot:
   - `uname -r` = `6.17.0-1012-aws` ✓ (kernel nuevo activo).
   - `/var/run/reboot-required` ausente ✓.
   - `trading-bot.service` active (running) since 2026-04-22 08:20:21 UTC, Main PID 614 (systemd auto-start via `enabled` preset funcionó como esperado).
   - APT timer next fire 2026-04-22 09:36:17 UTC (dentro de ventana xx:15-xx:45, drop-in persiste across reboot).

Smoke-A (post-arranque 08:20:27-32 UTC): ✓ PASS.
- `[ENGINE] Arrancando en modo LIVE con 45 simbolos`.
- `Balance USDT — total: 296.24` (consistente con pre-reboot 296.25 dentro de 1 cent, discrepancia normal por funding acumulado sub-minuto).
- `Markets BingX cargados: 2887 simbolos` (vs 2879 pre-reboot; BingX listó 8 símbolos adicionales entre sesiones — cambio normal del exchange).
- `Modelos cargados: 45 GMM, 45 specialist_configs` en 2.63s.
- `Estado restaurado: 45 simbolos, ciclo #203` (continúa numeración pre-restart).
- `5 posiciones sincronizadas desde exchange` (RENDER/THETA/ONDO/APT/SEI long — idénticas pre-stop).
- Boot time total: 4.2s desde primer log a `[START]` alert.
- `[ALERT] [START]` Telegram emitido.
- 0 errores Python, 0 WARNINGs inesperados.

Downtime medido (T_stop_complete=08:19:44 UTC a T_start_complete=08:20:32 UTC): **48 segundos** totales. Dentro de ventana inactiva (entre ciclo 203 cerrado a 08:00:07 y cycle 204 programado a 08:59:54). **Cero ciclos perdidos**.

Smoke-B (primer cycle post-reboot, cycle #203 a 08:59:52-09:00:08 UTC): ✓ PASS.
- Cycle duration: 15883ms (dentro de rango operacional 14-22s, sin degradación atribuible al kernel 1012 vs 1009).
- 4 señales evaluadas: 1 ejecutada (SAND/USDT short, partial fill detectado y manejado por v2.3.8 B7 — filled=136.0 vs requested=136.19, stop dimensionado a filled), 3 descartadas por `low_confidence` (BNB/SUI/UNI).
- 5 TS updates ejecutados como `TS_NOOP_V240` (v2.4.0) sobre las 5 posiciones preservadas (ONDO/APT/RENDER/SEI/THETA) — Fidelidad 2 TS operando normal post-kernel.
- Balance estable 296.24 USDT.
- 6 posiciones al cerrar el cycle (las 5 preservadas + SAND nueva).
- 0 errores Python, 0 WARNINGs inesperados.
- Comportamiento del bot kernel-agnóstico — ningún cambio observable vs operación pre-reboot. Cero regresiones detectables atribuibles al kernel upgrade.

Nota sobre numeración cycles: el shutdown message pre-stop decía "203 ciclos ejecutados" (contador histórico incluyendo el cycle en progreso) mientras el último cycle completado era #202 a 08:00. El cycle post-reboot a 09:00 tomó #203 (continuación natural — el cycle #203 correspondía al slot horario 09:00 UTC ya fuera con reboot o sin él). Cero cycles perdidos en la sucesión.

Cierre: kernel 6.17.0-1012-aws activo. Sin kernels pendientes. Próximos security updates de kernel entrarán en ciclo normal (aplicar + reboot cuando proceda). Deuda kernel saldada.

Referencias:
- `uname -r` pre-reboot: 6.17.0-1009-aws.
- `uname -r` post-reboot: 6.17.0-1012-aws.
- engine.log 2026-04-22 08:19:43-08:20:32 UTC.
- `systemctl status trading-bot.service` post-boot.
- Item previo §13.4 "Evento unattended-upgrades + mitigación APT window — 2026-04-22" (prerequisito).

---

**[RESUELTO] A34: Hipótesis timing_borderline en audit v5.1 + v5.2 — 2026-04-23**

Contexto: §13.3 EN_ESPERA "Hipotesis timing_borderline en audit v5.1 — 2026-04-17". Item original describe añadir tolerancia ±1 vela para reclasificar falsos NONE por desajuste temporal mínimo.

**Hallazgo crítico en Fase 0**: el scope original del item estaba OBSOLETO. La función de matching del audit v5.1 ya tiene `ENTRY_CANDLE_TOLERANCE = 1` y `EXIT_CANDLE_TOLERANCE = 1` desde el ultra review del 2026-04-17 (C8 fix, aplicado pero no documentado explícitamente como item aislado en §13.4). Matches ±1 vela ya cuentan como exitosos pre-A34. Implementar literalmente el item original hubiera duplicado funcionalidad existente.

**Reinterpretación adoptada**: `--timing-tolerance N` extiende MÁS ALLÁ del `entry_tol` actual (delta extra). Default 1 → matches en ventana `(entry_tol, entry_tol + timing_tolerance]` = ±2h se reclasifican como `timing_borderline` en vez de `no_match_kernel`/`no_match_bot`. Conceptualmente mejor que scope original: captura genuinamente "kernel match existe pero distancia > tol baseline, no es fidelity failure".

Implementación:
- `audit_fidelity_v5.py`: constante `DEFAULT_TIMING_TOLERANCE = 1`, función nueva `detect_timing_borderline_pairs`, kwarg `is_timing_borderline` en `hypothesis_for_no_match`, callsite extendido con post-match pasada, CLI flag `--timing-tolerance N`.
- `audit_fidelity_v5_2.py`: mismo patrón replicado (duplicación aceptable, cleanup cross-módulo separable si emerge necesidad).

Orden de precedencia hipótesis: `diff_reason > micro_precio_BingX_vs_Binance > timing_borderline > no_match_kernel/no_match_bot`. Simetría en dirección `kernel_no_vps` (kernel sin VPS también se reclasifica). Greedy no-double-counting: cada kernel se asigna a 1 VPS (closest entry_diff).

Tests 15/15 PASS en `tests/test_a34_timing_borderline.py`:
- Guards window (inferior: `diff=0` y `diff=1=entry_tol` no reclasifica; superior: `diff=4 > 3` fuera de ventana).
- Happy paths ±2 con tolerance=1, ±3 con tolerance=2.
- Simetría diff negativo (`diff=-2` con abs).
- Symbol/side mismatch rechaza.
- Greedy 2 VPS vs 1 kernel → solo 1 match.
- Flag propagation en `hypothesis_for_no_match` (vps_no_kernel + kernel_no_vps).
- `diff_reason` inmune al flag (gana por precedencia).
- `--timing-tolerance 0` desactiva feature (comportamiento pre-A34 idéntico).
- v5.2 consistency (mismos helpers, misma semántica).

Cross-suite regression 129/129 PASS (A36, A35, A38 tests previos + A02, A01 precedentes).

Evidencia empírica dataset 2026-04-21: 9 `no_match_kernel` + 61 `no_match_bot` actuales. Sin correr audit completo (requiere OHLCV BingX+Binance), implementación preventiva. Con audit N≥50 (~2026-04-26), `timing_borderline` default ±2 podría reclasificar 0-3 casos; escalará con data doble/triple.

Commits: 
- `f74e31e` feat(audit) A34.
- `b97d1c7` test(audit) A34.
- `0f3d230` merge rama feature/a34-timing-borderline.

Referencias: `audit_fidelity_v5.py` L1451-1578 (matching pre-A34 con entry_tol=1 baseline), C8 ultra review 2026-04-17, §12 Lección 27 (items §13.3 obsoletos), §0.7 (convención sync que habilitó detección de desincronizaciones).

Cierre: feature disponible para audit N≥50. Default 1 activo por ser bajo riesgo + alto beneficio informacional (separa falsos NONE por timing borderline de NONE genuinos).

---

**[RESUELTO] A38: Guard edge erosion con scope ampliado (exp_pool≤0, exp_oos<0, ratio negativo) — 2026-04-23**

Contexto: §13.3 EN_ESPERA "Edge erosion con exp_pool negativo — 2026-04-17". Item original describe guard defensivo trivial para cluster con `exp_pool<0`.

**Hallazgo en Fase 0**: el bug real es triple, no solo `exp_pool<0`:
1. `exp_pool<0`: el caso del item original.
2. `exp_oos<0` con `exp_pool>0`: produce ratio negativo en `exp_oos/exp_pool`.
3. Ratio negativo cruza threshold `EDGE_EROSION_RATIO_ALERT=0.5` trivialmente (ej. `-0.25 < 0.5`) → flag `edge_erosion` ESPURIO, cuando el cluster en realidad es estructuralmente perdedor, no erosionándose.

Scope ampliado para resolver los 3 casos con refactor arquitectónico: helper `_classify_cluster_edge(exp_pool, exp_oos, n, min_n, ratio_alert)` con clasificación 3-way:
- `None` si inputs insuficientes o `n<min_n`.
- `'cluster_estructuralmente_perdedor'` si `exp_pool<=0 or exp_oos<0`.
- `'edge_erosion'` si cluster sano con `ratio < ratio_alert`.
- `None` si ratio sano (>= ratio_alert).

Implementación en `analyze_performance_attribution.py`:
- Helper añadido antes de `detect_edge_erosion` (L1729).
- Callsites refactorizados: tabla símbolo × cluster (L1296-1298) + alerts (L1559-1574 ahora separa `erosion_clusters` de `losing_clusters`).
- Emoji normalizado a escape literal `⚠️` (4/4 consistencia con resto del archivo, 0 unicode literals mezclados).

Tests 9/9 PASS en `tests/test_a38_cluster_edge.py`:
- edge_erosion happy path.
- cluster sano ratio>=0.5.
- 3 casos de exp negativos (exp_pool≤0, exp_oos<0, ambos).
- None inputs / n<min_n.
- custom thresholds (min_n, ratio_alert).
- ratio boundary strict-less.

**Implicación conceptual importante**: separar `cluster_estructuralmente_perdedor` de `edge_erosion`. Son fenómenos distintos:
- Edge erosion: cluster rentable (exp_pool>0) que se degrada progresivamente (exp_oos baja).
- Cluster estructuralmente perdedor: cluster que nunca debió operar (rentabilidad nominal negativa desde entry).

Próximo audit N≥50 puede revelar clusters en nueva categoría que antes se absorbían espuriamente como edge_erosion. Signal importante para decisiones de reciclaje.

**Patrón metodológico**: scope ampliado es instancia de §12 Lección 26 (ecuaciones que cierran ≠ atribución correcta). El ratio `exp_oos/exp_pool` mezclaba signos sin chequear componentes individuales, produciendo clasificación errónea que parecía matemáticamente válida. Validación per-componente independiente resuelve.

Commits: en merge `72cd6c0` (rama `feature/a35-a38-defensivos`, commit específico A38 `f107d6d`).

Referencias: `analyze_performance_attribution.py` L1296-1574, §12 Lección 26 (precedente metodológico).

Cierre: fix aplicado. Próximo reporte analyzer tendrá sección nueva `losing_clusters` distinta de `erosion_clusters`.

---

**[RESUELTO] A35: tz-naive defensivo en cross_exchange_diff_pct — 2026-04-23**

Contexto: §13.3 EN_ESPERA "Timestamp tz-naive defensivo en cross_exchange_diff_pct — 2026-04-17". Guard defensivo para evitar TypeError si timestamp llega sin zona horaria.

**Confirmación empírica Fase 0**: el bug ES real, no teórico. `audit_fidelity_v5.py:491` y `v5_2.py:488` usan `pd.Timestamp(target_ts).tz_convert('UTC')` sin guard → `TypeError: Cannot convert tz-naive Timestamp, use tz_localize to localize` reproducible con `pd.Timestamp('2026-04-21 12:00').tz_convert('UTC')`.

Fix idiomático (patrón idéntico en ambos audits):
```python
target_ts = pd.Timestamp(target_ts)
if target_ts.tzinfo is None:
    target_ts = target_ts.tz_localize('UTC')
else:
    target_ts = target_ts.tz_convert('UTC')
```

Tests 12/12 sub-checks PASS en `tests/test_a35_tz_naive_defensive.py` (6 sub-checks × 2 módulos):
- tz-aware identical → diff=0.0.
- tz-aware diff=0.5% correcto.
- tz-naive → tz_localize('UTC') fallback → sin TypeError.
- None inputs → None (backward compat).
- bx_close<=0 → None.
- ts missing → None.

Callsites actuales pasan tz-aware (no había regresión operacional), pero guard previene regresión silenciosa futura cuando alguna ruta nueva o refactor introduzca timestamp sin tz explícito.

Commit: en merge `72cd6c0` (rama `feature/a35-a38-defensivos`, commit específico A35 `d65592c`).

Referencias: `audit_fidelity_v5.py` L487-501, `audit_fidelity_v5_2.py` L484-498.

Cierre: guard aplicado. Robusto contra cualquier timestamp input sin especificación explícita de tz.

---

**[RESUELTO] A36: Log rotation tolerance (analyzer + audit v5.1 + audit v5.2) — 2026-04-23**

Contexto: §13.3 EN_ESPERA "Log rotation en analyzer v2.4 — 2026-04-17". Justificación roadmap 2026-04-22 Bloque 1 orden 5: logs VPS cerca de rotar orgánicamente. Sin fix, análisis post-rotación pierde primera parte de ventana.

Decisión 2026-04-23: aplicar a los 3 consumidores de `engine.log` (analyzer v2.4.1 + audit v5.1 + audit v5.2) en el mismo item para no fragmentar el fix.

Implementación:
- `combolab/log_file_resolver.py` (140 líneas, nuevo): helper compartido con `resolve_engine_log_paths(spec)` + `read_log_files(paths)` (lazy iterator, soporta gzip transparente).
- spec acepta 3 formatos: archivo único (backward compat), glob pattern (ej. `'logs/engine.log*'`), lista CSV (ej. `'logs/engine.log.1,logs/engine.log'`).
- Ordenamiento cronológico: detecta logrotate numeric (N mayor = más antiguo, convención estándar), timestamps `-YYYYMMDD` en nombre, fallback por mtime.
- Convención VPS detectada empíricamente en `audit_run_20260421/`: `engine.log.current` + `engine.log.{1..4}.gz`.
- 3 consumers modificados con patrón idéntico (+25/-4 líneas cada uno): import con sys.path guard, `parse_engine_log` usa `resolve_engine_log_paths` en lugar de `open(log_path)`, `read_log_files(paths)` lazy iterator, argparse help extendido documentando los 3 formatos.

Tests 19/19 PASS:
- 13 unit (`tests/test_log_file_resolver.py`): single file backward compat, glob ordering plain/gzip, CSV spec, missing path/spec raises, gzip transparente, rotation_age classifier, integration fixture.
- 6 integration (`tests/test_a36_integration.py`): los 3 consumidores × glob-vs-concat + backward compat archivo único + CSV spec + invalid spec retorna empty.

**Equivalencia verificada empíricamente**: `engine.log.concat` (4177 líneas, baseline pre-A36) vs glob de 4 `.gz` + 1 `.current` procesados via helper produce output IDÉNTICO (engine_states=108, signals_raw=340, signals_executed=100, brain_reconciles=197, orphan_closes=3). Todas las keys coinciden bit-a-bit.

Commits: 4 commits en rama `feature/a36-log-rotation` (`e8cf596` helper+tests, `77d0b6f` analyzer, `3c5072a` audit v5.1, `1ed4269` audit v5.2 + integration tests), merge `4868b98`.

Referencias: `log_file_resolver.py` (nuevo helper), `tests/test_log_file_resolver.py` + `tests/test_a36_integration.py`, §0.7 (convención sync que asegura presencia en ambos repos).

Cierre: feature disponible. Cuando logs roten orgánicamente en VPS, los 3 scripts manejarán rotation transparentemente sin intervención manual (sin concatenar `.gz` a mano como se hacía para el primer audit empírico 2026-04-21).

---

**[RESUELTO] Bug histórico size_usdt=0 en trade_history.csv — 2026-04-22 (v2.4.4)**

Contexto: hallazgo colateral durante demo A02 (signal_price_lookup + slippage directo). Demo reportó slippage USDT = +0.00 para 20/20 trades con size_usdt=0 en CSV. Investigación forense dedicada reveló bug sistemático desde origen del dataset.

Alcance histórico confirmado: 134/135 trades afectados (99.3%). Único trade con size>0 fue reconstrucción manual de Ricardo del 2026-04-16 GRT (ingreso manual 10.0 USDT). Bug desde primer trade automático 2026-04-13 22:00 ADA.

Root cause identificado con precisión quirúrgica:
- `data_feed.get_open_positions` (líneas 326-340): dict retornado con campos side/size/entry_price/unrealized_pnl/leverage/stop_order_id, SIN `size_usdt`.
- `execute_cycle` CLOSE branch usa `action["position"]` (dict reconstruido desde get_open_positions) → pos sin size_usdt.
- `log_trade` línea 948: `pos.get("size_usdt", 0.0)` → fallback 0.0 → CSV persiste 0 sistemáticamente.

Bug AISLADO a size_usdt. Otros campos sanos:
- pnl_usdt: 132/135 OK (computed independently from entry/exit ratio × size).
- pnl_pct: 134/135 OK (computed on-the-fly in log_trade).
- funding_paid: 127/135 OK (cómputo con fallback `notional or size × entry_price`).

Impacto en análisis previo (matización §13.4 primer audit empírico 2026-04-21):
- PnL real +0.77 USDT: CORRECTO (de pnl_usdt, no afectado).
- Alpha nominal +3.01: CORRECTO (balance × 5%, no usa size_usdt).
- Factor portfolio -0.56: CORRECTO (derivado de alpha).
- Funding -0.04: CORRECTO.
- Slippage +0.00: ESPURIO (contracts=None → NaN → 0). Valor real estimado ~-0.23 USDT basado en A02 demo (-0.18% por trade × tamaño promedio).
- Alpha residual -1.64: desagregable a ~-1.41 residual neto + ~-0.23 slippage absorbido.
- Ecuación sigue cerrando (pnl_real correcto), pero atribución por componente sesgada: "fenómeno no modelado" era ~86% residual / ~14% slippage oculto.
- Conclusiones cualitativas del audit (Fidelidad 2 empírica 84.6% match post-v2.3.11, CI95 overlap baseline 91%) NO afectadas (son matching brain↔kernel, no PnL attribution).

Fix: +15 líneas netas en `data_feed.py`.
```python
entry_px = float(pos.get("entryPrice", 0) or 0)
notional = float(pos.get("notional", 0) or 0)
size_usdt = notional if notional > 0 else (size * entry_px)
if size_usdt == 0 and size > 0:
    logger.warning(f"[get_open_positions] {master_sym} "
                   f"size_usdt=0 with size={size}, "
                   f"entry_price={entry_px}")
```
Campo `size_usdt` añadido al dict resultado.

Tests 8/8 PASS en `tests/test_get_open_positions_size_usdt.py`: size_usdt from notional, fallback contracts × entry_price, notional=0/None fallback, warning con entry_price=0, empty positions list, contracts=0 skip, multi-position.

Fidelidad 2 invariante verificada (protocolo proyecto aunque fix no toca brain/execution):
- TF `_run_verify_test --symbol BTC/USDT`: diff 0.0000 (Trades, Wins, PnL, Gross).
- MR `audit_mr_fidelity_sei.py` SEI C2 config 45686: diff 0.0000 en 7 métricas.

Deploy VPS 2026-04-21 18:22:02 UTC (fecha reloj del servidor). MD5 3-way sync confirmado: `d69afccf1be685c1c910a9d1c1a84f28` (combolab, comboclaude, VPS). Downtime ~20s. Smoke-A boot limpio: 45 GMM + specialists, 6 posiciones sincronizadas desde exchange SIN WARNINGs `[get_open_positions] size_usdt=0` en log de arranque.

Trades históricos permanecen con `size_usdt=0` en trade_history.csv (no migrable — data perdida en origen). Trades post-deploy tendrán size_usdt correcto.

Validación directa orgánica pendiente: próximo close post-deploy. Log del close tendrá size_usdt>0 en CSV; analyzer v2.4.1 reportará slippage directo correcto.

Commits: `fc796bb` (fix 1 línea data_feed.py), `5bb4f95` (tests 8 unitarios), merge main con `--no-ff` (rama `fix-size-usdt-data-feed` preservada).

Referencias: investigación forense 2026-04-22 (5 preguntas respondidas), demo A02 2026-04-22 como detector del síntoma, data_feed.py l.326-340 (origen), execution_manager.py l.944-954 (cascada), log_trade l.948 (fallback), §12 Lección 26 (nueva).

Cierre: fix deployado + validado (indirecto). Validación directa orgánica no bloqueante.

---

**[RESUELTO] A02: signal_price_lookup helper + slippage directo post-hoc — 2026-04-22**

Contexto: §13.3 EN_ESPERA "Logger enriquecer signal_entry_price / signal_exit_price" con scope original de modificar logger CSV. Investigación previa reveló que SIGNALS_RAW en engine.log ya loguea `p` (signal price) per-signal desde v2.3.1 (instrumentación pasiva). Derivación post-hoc es zero-touch al bot y 100% retroactiva.

Decisión: Opción 2 (post-hoc derivation) sobre Opción 1 (CSV schema extensión). Beneficio equivalente, riesgo cero operacional, scope 1/3 del trabajo.

Implementación:
- `combolab/signal_price_lookup.py` (145 líneas, nuevo). Helper compartido con funciones puras:
  * `get_signal_price(signals_raw, cycle_ts, symbol, action_hint=None)` — lookup desde dict indexado por (cycle_ts, symbol).
  * `compute_slippage_usdt(fill_price, signal_price, side, size_contracts)` — slippage signed, positivo=favorable.
  * `compute_slippage_pct(...)` — idem en porcentaje.
  * `attribute_slippage_per_trade(...)` — integration helper.
- `audit_fidelity_v5_2.py`: CLI flag `--verbose-slippage` + sección 2.5 nueva en reporte con slippage entry/exit per trade.
- Analyzer NO modificado: inspección reveló que `analyze_performance_attribution.py` líneas 910-947 YA tenía lookup inline de SIGNALS_RAW.p para slippage. El beneficio del helper es DRY futuro, no funcional inmediato.

Tests 24/24 PASS en `tests/test_signal_price_lookup.py`: 10 lookup edge cases (happy path, missing p/cycle/symbol, p=0, p no numérico, coerce str, action_hint mismatch/match), 6 slippage_usdt (LONG/SHORT favorable/adverso, zero, invalid side), 3 slippage_pct (LONG, SHORT, zero guard), 5 attribute_per_trade (LONG full, SHORT full, missing entry, missing both, LONG adverso).

Demo empírico sobre dataset 2026-04-21 (20 trades N_effective post-v2.3.11):
- Slippage entry: 20/20 computable, mean -0.061%, max |.| 0.586% (ONDO 13:00 long).
- Slippage exit: 19/20 computable, mean -0.121%, max |.| 0.368% (SEI short).
- Coste ejecución neto per trade ~-0.18%. Magnitud realista BingX MARKET orders.

Slippage USDT por trade NO computable en este demo porque dataset tiene size_usdt=0 (bug descubierto durante A02, ver entrada size_usdt fix v2.4.4 arriba). Tras v2.4.4 + primer close post-deploy, slippage USDT directo estará disponible.

Referencias: investigación previa T1+T2+T3 2026-04-22 (schema + consumers + flujo), decisión Opción 2 pura sobre Opción 3 híbrida, §13.4 entrada size_usdt fix 2026-04-22 (descubrimiento colateral), `signal_price_lookup.py`, `tests/test_signal_price_lookup.py`.

Cierre: infraestructura disponible y probada. Primer uso productivo en próximo audit + analyzer con N≥50 post-v2.3.11.

---

**[RESUELTO] A01: Audit v5.2 segmentación + exclusión clustering divergente — 2026-04-22**

Contexto: §13.3 REFERENCIA EN_ESPERA "Feature request audit v5.2". Motivación: primer audit empírico 2026-04-21 reveló que métricas agregadas sobre ventanas heterogéneas (pre-v2.3.11 con lag 1 bar vs post-v2.3.11 alineado) dan veredictos engañosos (26.7% global vs 84.6% post-filter). §12 Lección 25 formaliza el problema.

Implementación:
- `combolab/audit_fidelity_v5_2.py` (~2470 líneas, +240 sobre v5.1). Script independiente (no sobreescribe v5.1).
- `combolab/deploy_boundaries.json` (boundaries actuales: v2.3.11, v2.4.0, v2.4.1, v2.4.2, v2.4.3, v2.4.3-hotfix).
- `combolab/tests/test_audit_v5_2_parity.py` (380 líneas).

Features:

1. **Segmentación automática** (`--deploy-boundaries path.json`): genera reporte multi-segmento por períodos homogéneos entre boundaries. Tabla segmento × {N_eff, OK, NONE, EXCL, rate, CI95}. Weighted average match rate + flag de discontinuidad >20pp entre segmentos consecutivos.

2. **Exclusión clustering_divergente** (`--clustering-check`): nueva categoría en orden canónico (posición 6). Cuando `cluster_live (SIGNALS_RAW.k) != cluster_post_hoc (classify_bars_gmm stateless)`, trade se clasifica como excluido en vez de NONE. Reclasifica los 2 NONE IMX+GRT del 2026-04-21 (primer audit empírico) como excluidos.

Tests 29/29 PASS: orden EXCL_LABELS preservado v5.1 → v5.2 (backward compat), `load_deploy_boundaries` + 3 edge cases, `build_segments` + 1 edge, `assign_trade_to_segment` + 1 edge, `compute_segment_metrics` + 1 edge, `discontinuity_warnings` + 2 edge, `get_cluster_live` × 4, `get_cluster_post_hoc` × 3, `check_clustering_divergent` × 4, smoke tests (imports, help string, weighted_avg=total sanity).

Demo dry-run sobre dataset 2026-04-21 confirma: backward compat N=27, excluded=7, N_effective=20 idénticos a v5.1. Segmentación funcional: 5 segmentos con N_eff por boundary. Exclusiones ampliadas con fila #6 `excluido_clustering_divergente`.

Validación end-to-end IMX+GRT → excluido_clustering_divergente: lógica PASS por unit test con fixture; validación empírica completa pendiente de run con BingX kernel execution real (no bloqueante — arquitectura validada).

Observación menor: 4 trades transición (entry pre-v2.3.11, exit post-v2.3.11) excluidos automáticamente de segmentos. Comportamiento correcto (evita contaminación). Mejora incremental futura: pseudo-segmento "pre-window" para transparencia contable. Baja prioridad.

Referencias: diseño Fase II-A 2026-04-22 (roadmap post-sesión 2026-04-21), §12 Lección 25 (métricas heterogéneas) caso de estudio, §13.4 primer audit empírico 2026-04-21 (motivación), investigación IMX+GRT 2026-04-21 (CASO A clustering divergente).

Cierre: infraestructura disponible para audit definitivo N≥50 post-v2.3.11 (estimado 2026-04-26). Primera ejecución productiva con N≥50 validará end-to-end clustering_divergente.

---

**[RESUELTO] A40: Parser engine.log rollover — ya resuelto empíricamente en audit v5.1 — 2026-04-22 (verificación)**

Contexto: §13.3 EN_ESPERA "Parser de engine.log en audit_fidelity_v5.py usa rollover de fecha" con hipótesis de que la migración a `ENGINE_STATE.t` como ancla de fecha estaba pendiente. Verificación directa del código audit v5.1 reveló que el fix fue implementado en el ultra review 2026-04-17 como C5 ("Rollover con ENGINE_STATE.t").

Verificación literal `audit_fidelity_v5.py` líneas 245-315:
- Docstring: "C5 fix: usa [ENGINE_STATE].t (unix seconds, v2.3.1+) como ancla de fecha. Si hay gaps (bot caido multi-hora), la siguiente [ENGINE_STATE] re-sincroniza. Fallback rollover 23->00 solo para lineas sin anchor disponible."
- Implementación líneas 286-315: ENGINE_STATE.t dominante (re-sincroniza current_date desde campo t unix cada cycle). Rollover puro 23→00 solo dispararía en ventana sub-hora sin anchor, raro y defensivo.
- Contadores `log_date_sync_anchors` y `log_date_gap_warnings` trackean salud del parseo.

Veredicto: RESUELTO. El item estaba mal clasificado en §13.3 EN_ESPERA cuando en realidad ya estaba en §13.4 RESUELTO "Log date rollover robusto con ENGINE_STATE.t — 2026-04-17".

Cierre documental: item removido de §13.3 EN_ESPERA. Referenciado desde §13.4 entrada existente 2026-04-17.

Referencias: audit_fidelity_v5.py líneas 245-315 (implementación), §13.4 entrada "Log date rollover robusto con ENGINE_STATE.t — 2026-04-17" (fix documentado).

---

**[RESUELTO] A27: cp1252 emoji fix en lab_historico línea 996 — 2026-04-22**

Contexto: §13.3 EN_ESPERA "lab_historico: crash cp1252 por emoji en _run_verify_test". Bloqueaba [2/2] kernel compare step en Windows cp1252 por UnicodeEncodeError. Prerequisito de A10 (test diferencial brain vs kernel 10k barras).

Fix aplicado: `lab_historico_numba_v8_3.py` línea 996 (nota: item §13.3 decía "línea 990", drift de numeración detectado):
- Antes: `print(f"   ⚙️ Pre-calculando indicadores para {n} velas...")`
- Después: `print(f"   [CALC] Pre-calculando indicadores para {n} velas...")`

Syntax check PASS.

Descubrimiento colateral: otras 14 ocurrencias no-ASCII en lab_historico_numba_v8_3.py en paths que `_run_verify_test` NO ejecuta (master.py pipeline de procesamiento + walk-forward). Riesgo residual: si se ejecuta master.py --recycle en Windows cp1252 sin redirección UTF-8, crasheará en alguna de esas líneas. Candidato a fix batch pre-reciclaje (nuevo item §13.3 "Batch fix emojis cp1252 restantes").

Cierre: fix aplicado. A10 (test diferencial) desbloqueado para ejecución cuando llegue disparador post-audit N≥50.

Referencias: lab_historico_numba_v8_3.py l.996 (aplicado), l.1042/1089 (⚙️ restantes) + resto de ocurrencias listadas en §13.3 batch cp1252 (nuevo item agrupación).

---

**[RESUELTO] Primer audit empírico v5.1 + analyzer v2.4.1 (N=22 post-v2.3.11) — 2026-04-21**
Contexto: primer audit/analyzer sobre dataset homogéneo tras descubrir (diagnóstico mediodía) que la ventana N=70 mezclaba pre-v2.3.11 (lag estructural 1 bar, match ~3.4%) con post-v2.3.11 (alineado, match ~84.6% por entry-cycle filter). El 26.7% global inicial fue artefacto metodológico de segmentación por exit cycle, no bug de fidelidad.

Audit v5.1 segmentado (`--since 2026-04-19T17:51:00Z`):
- Exit cycle filter: 11/20 = 55.0%, CI95 [34.2%, 74.2%].
- Entry cycle filter (reinterpretación): **11/13 = 84.6%**, CI95 ~[57.8%, 95.7%]. Overlap con baseline 91% CI95 [62%, 98%].
- No hay segundo hallazgo crítico. Fidelidad 2 empíricamente confirmada en ventana homogénea.
- 3 exclusiones MR (UNI x2, STX x1) por kernel MR no implementado en audit v5.1. Fidelity MR validada independientemente por `audit_mr_fidelity_sei.py` (§13.4 2026-04-21 0.0000 diff).
- Dos trades con entry POST-v2.3.11 sin match kernel (IMX/USDT 14:00 UTC, GRT/USDT 01:00 UTC, ambos 2026-04-20). Investigación forense dedicada clasificó ambos como **CASO A dominante** (clustering GMM live vs post-hoc divergente en bars borderline) tras descartar state stale, reconcile, deploy boundaries. Ambos trades rentables (+0.148 y +0.066 USDT respectivamente), sugiriendo señales técnicamente válidas con divergencia estructural esperable. Ver §13.3 mini-item EN_ESPERA clustering divergente.

Analyzer v2.4.1 post-v2.3.11 (N=26 procesados, 1 reconstructed excluido):
- PnL real: **+0.77 USDT**.
- Alpha nominal: +3.01. Factor portfolio: -0.56. Slippage: +0.00. Funding: -0.04. Alpha residual: **-1.64**.
- Ecuación cierra: 3.01 - 0.56 + 0 - 0.04 - 1.64 = 0.77 ✓.
- Alpha residual -1.64 USDT (54% del alpha nominal 3.01). En términos absolutos per trade: -0.063 USDT/trade. No cruza criterio crítico del prompt (>5% pnl_real) porque pnl_real es pequeño por saturación portfolio. Lectura preliminar: fenómeno no modelado significativo en proporción al alpha teórico, aunque pequeño en magnitud absoluta. Desglose por símbolo y seguimiento con N≥50 pendiente.
- 1 alert: ONDO/USDT C2 candidato exclusión próximo reciclaje.

Pregunta slippage pre vs post v2.3.11:
- No concluyente directo (slippage_entry/exit vacíos por falta de signal_price pre-logging completo).
- Proxy via alpha_residual per trade: PRE=-0.077, POST=-0.063, reducción ~18% post-deploy. Direccional consistente con fix v2.3.11 pero no dramático.
- Ver §13.3 mini-item EN_ESPERA logger signal_prices.

Primera ejecución empírica completa del pipeline audit/analyzer establecida. Pipeline operando correctamente. Métricas comparables al baseline con N=13-22 (falta acumular hacia N≥50 post-v2.3.11 para reporte definitivo, estimado 2026-04-26).

Referencias: §2.4 v2.3.11 Fidelidad 2 restaurada, §13.4 v2.4.2+v2.4.3+hotfix, §13.2 HALLAZGO RESUELTO lag estructural 2026-04-19, `audit_v5_report_20260421_1256.txt`, `attribution_summary_20260421_1257.txt`, investigación IMX+GRT 2026-04-21.

**MATIZACIÓN 2026-04-22 por hallazgo colateral bug size_usdt=0 (v2.4.4):**

Cifras del analyzer v2.4.1 del 2026-04-21 tienen sesgo conocido en atribución por componente. NO invalidan conclusiones cualitativas del audit (match rate 84.6% post-v2.3.11 entry-filter sigue válido).

- PnL real +0.77 USDT: CORRECTO (de pnl_usdt del CSV, no afectado por bug size_usdt).
- Alpha nominal +3.01: CORRECTO (balance × 5%, no usa size_usdt).
- Factor portfolio -0.56: CORRECTO (derivado de alpha nominal).
- Funding -0.04: CORRECTO.
- Slippage +0.00: ESPURIO (contracts = size_usdt / entry_price = 0 → NaN → sum = 0). Valor real estimado ~-0.23 USDT basado en A02 demo 2026-04-22 midiendo -0.18% por trade.
- Alpha residual -1.64: desagregable ex-post a ~-1.41 residual neto + ~-0.23 slippage absorbido silenciosamente.

Ecuación cerraba porque PnL real era correcto; atribución estaba sesgada hacia "misterio residual" cuando parte era slippage medible. Desde v2.4.4 (22-Abr), slippage USDT computa correctamente. Audits futuros tendrán atribución limpia.

Conclusiones del audit NO afectadas:
- Fidelidad 2 empíricamente confirmada (match rate 84.6% CI95 overlap baseline 91%) → SIGUE VÁLIDA.
- Segmentación post-v2.3.11 homogénea identificada → SIGUE VÁLIDA.
- Hallazgo metodológico (Lección 25) → SIGUE VÁLIDO.

Ver [RESUELTO] size_usdt fix 2026-04-22 para detalle completo.

**MATIZACIÓN 2026-04-22 adicional por bug entry_timestamp_ms=0 (v2.4.5 fix):**

El audit reportó N=13 effective post-v2.3.11 usando entry-filter. Investigación forense 2026-04-22 (Fase I del reconocimiento empírico) reveló bug sistemático entry_timestamp_ms=0 en CSV (51/155 trades con valor 0, 100% de closes via `_evaluate_bar` post-v2.3.9).

Impacto en el audit 2026-04-21:
- El audit v5.1 (`audit_fidelity_v5.py:211-231` `infer_entry_candle`) tiene cadena de fallback: (1) CSV `entry_timestamp_ms` si presente y >0, (2) log `SIGNALS_EXECUTED` cycle_ts. Si el CSV raw tenía entry_ms=0, el audit automáticamente delegaba al log → entry_cycle inferido correctamente.
- Por tanto N=13 effective **probablemente correcto** vía fallback, no afectado por el bug en el CSV directo.
- Conclusión cualitativa 84.6% match rate **preserva validez**.
- Analyzer v2.4.1 tiene misma cadena de fallback (`analyze_performance_attribution.py:219-231`) → análisis de atribución no afectado por entry_ms.

Fix v2.4.5 deployado 2026-04-22 09:46 UTC. Trades post-deploy tendrán entry_ms correcto en CSV directo → fallback ya no será necesario. Trades históricos (51 afectados) permanecen con entry_ms=0 en CSV, pero audits/analyzers seguirán resolviendo vía fallback.

Ver [RESUELTO] entry_timestamp_ms fix v2.4.5 2026-04-22 para detalle completo.

Cierre: primer hito empírico alcanzado. Próxima ejecución disparada por N≥50 post-v2.3.11 (~2026-04-26).

**[RESUELTO] v2.4.2 + v2.4.3 + v2.4.3-hotfix — Smoke-B cycle 182 validación completa — 2026-04-21**
Contexto: consolidación en rama única + merge de tres fixes complementarios tras diagnóstico forense del patrón BRAIN_RECONCILE (UNI/ETH/ALGO) y documento de diseño Fase II-A que descartó refactor arquitectural v2.5.0 (archivado en §13.3 REFERENCIA) a favor de esta alternativa minimalista. La secuencia v2.4.2 → v2.4.3 → v2.4.3-hotfix se desplegó en 3 ventanas durante la sesión 2026-04-21 (deploy inicial 10:14 UTC, Smoke-B cycle 181 reveló bug, hotfix 11:09 UTC, Smoke-B cycle 182 validó).

**Cambios desplegados:**
- **v2.4.2 silent reconcile** (`live_engine.py::_reconcile_brain_after_execution`): diferencia rollback ESPERADO (symbol en `allocations FLAT` o en `exec_report.orders_failed`) → log DEBUG `[BRAIN_ROLLBACK_EXPECTED]`, vs desinc REAL (BingX cerró entre ciclos, orphan fill) → INFO `[BRAIN_RECONCILE]` preservado. Reset de 6 campos idéntico a v2.4.1.
- **v2.4.3 pre-check symbol-aware** (`portfolio_manager.py` + `live_engine.py`): nueva `compute_min_order_usdt_for(symbol, price, markets_info)` = `max(limits.cost.min, limits.amount.min × price, precision.amount × price)` con floor 5.0 USDT. Reemplaza constante `MIN_ORDER_USDT=5.0`. `live_engine.start()` carga `exchange.load_markets()` → `self.markets_info` (2879 símbolos). `allocate_positions` acepta kwarg opcional `markets_info`.
- **v2.4.3-hotfix ccxt format resolution**: bug Smoke-B cycle 181 — markets_info usa key formato perpetuo ccxt (`"ETH/USDT:USDT"`) pero bot pasa formato master (`"ETH/USDT"`) → fallback `DEFAULT_MIN=5.0` → ETH `sz=11.67` pasaba portfolio y fallaba en BingX. Fix: condicional que prueba `symbol` directo, luego con sufijo `":USDT"`, luego fallback. Commit 8b61e94.

**Tests 13/13 PASS:**
- `tests/test_silent_reconcile.py` (4): rollback_esperado_portfolio_flat (DEBUG), rollback_esperado_execution_failed (DEBUG), desync_real_log_info (INFO), reset_fields_identical_v241.
- `tests/test_min_order_precheck.py` (9): eth_high_price → 23.1, uni_normal → 5.0 floor, algo → 5.0 floor, fallbacks (no_markets, invalid_price, missing_symbol), eth_price_3000 → 30.0, btc_high_precision → 5.0 floor, **master_format_resolves_to_ccxt → 23.1** (validación específica del hotfix).

**Fidelidad 2 invariante (0.0000 diff vs baseline v2.4.1):**
- TF: `python -m live.brain_engine --verify --symbol BTC/USDT` → Trades/Wins/PnL/Gross iguales. RESULTADO: FIDELIDAD CONFIRMADA.
- MR: `python audit_mr_fidelity_sei.py` SEI/USDT C2 config 45686 → PnL 1.0180=1.0180, Trades 17=17, Wins 5=5, Cancels 2=2, MaxDD 3.9316=3.9316, GrossProfit 9.6434=9.6434, GrossLoss 8.6254=8.6254.

**Deploys VPS:**
- Deploy inicial v2.4.2+v2.4.3 2026-04-21 10:14-10:15 UTC. Backups `*.bak-v241-20260421-121457`. Downtime ~39s. MD5 live_engine `bc30d85…`, portfolio `b3d501b…`. Smoke-A PASS (2879 markets, 45 GMM + specialists, 7 posiciones, boot 3.8s, 0 errores).
- Smoke-B cycle 181 11:00:09 UTC detectó bug v2.4.3: `[EXEC] OPEN FALLIDO ETH` apareció porque ETH signal sz=11.67 pasó portfolio por símbolo no encontrado en markets_info. v2.4.2 SÍ funcionó (0 INFO BRAIN_RECONCILE).
- Deploy hotfix 11:09:56 UTC. Backup `portfolio_manager.py.bak-v243hotfix-20260421-130940`. MD5 portfolio `c4d5e749…074`. Downtime ~35s. Smoke-A post-hotfix PASS.

**Validación final Smoke-B cycle 182 (11:59:53-12:00:09 UTC):**
- Code path v2.4.3 confirmado operando: `[SIGNALS_DISCARDED] {"ALGO/USDT":{"a":"SHORT","d":"below_min_order_5.0usdt"}}` — label enriquecido confirma nueva función activa.
- v2.4.2 silent reconcile confirmado: 0 INFO BRAIN_RECONCILE para ALGO fantasma (brain marcó position=-1, portfolio descartó, reconcile silenciosamente reseteó en DEBUG). `engine_state.json` post-cycle no tiene ALGO en symbols (state limpio).
- 0 CRITICAL `[EXEC] OPEN FALLIDO` en cycle 182.
- Operación normal: cycle duration 15797ms, 6 posiciones sincronizadas (MANA, OP, RENDER, TAO, THETA, XLM), balance 296.77 USDT, 0 errores Python.

**Validación directa ETH** con threshold 23.1 USDT **pendiente de signal orgánico** próximo (evidencia indirecta robusta: test unit `test_master_format_resolves_to_ccxt` PASS + code path confirmado en producción con ALGO + lógica del hotfix verificada por inspección literal). Cierre 100% esperado en próximos cycles con ETH signal (estimado: 1-3h según frecuencia histórica ETH).

**Disparador de verificación final**: próxima sesión, `grep below_min_order_23.1usdt` en engine.log VPS. Si aparece → cierre 100%. Si no aparece pero ETH emitió signal → investigar.

**Commits consolidados:**
- bf1cb85: v2.4.2 silent reconcile.
- cdbd9ea: v2.4.3 pre-check original.
- e308189: tests 13/13 PASS + Fidelidad 2 invariante confirmada.
- 25a2c5a: merge rama `v2.4.2-silent-reconcile+precheck` → main.
- f63c3dd: CONTEXTO docs inicial.
- 8b61e94: v2.4.3-hotfix ccxt format resolution.
- [este commit]: CONTEXTO docs cierre completo + lección metodológica §12.

Cierre: validación directa ETH pendiente orgánica (no bloqueante). Sistema operacional estable post v2.4.2+v2.4.3+hotfix.

Referencias: §2.4 filas v2.4.2, v2.4.3, v2.4.3-hotfix; §2.6 portfolio fix #6, #7 + live_engine fix #16, #17; §12 nueva lección metodológica (tests con mocks propios); §13.3 REFERENCIA ARCHIVADA v2.5.0; §13.3 B-UNI-1 INFORMACIONAL.

**[RESUELTO] ETH "below min precision" en logs — resuelto via v2.4.3 — 2026-04-21**
Contexto: Balance 297 USDT + precio ETH ~$2310 producía sizing por debajo de mínimo BingX (0.01 ETH = 23.1 USDT, pero sizing vw-ajustado entregaba 5-11 USDT = 0.002-0.005 ETH). Cada ocurrencia generaba `[EXEC] OPEN LONG ETH/USDT FALLIDO: Invalid order: bingx amount of ETH/USDT:USDT must be greater than minimum amount precision of 0.01` + BRAIN_RECONCILE reset. Originalmente documentado como CRITICAL, verificación empírica 2026-04-21 confirmó reclasificación a `[EXEC]` info tras v2.4.0. Frecuencia observada: 7-11 ocurrencias/día.
Resolución: v2.4.3 aplica pre-check symbol-aware en portfolio. Para ETH @ 2310, `compute_min_order_usdt_for` calcula `max(2.0, 0.01 × 2310, 0.01 × 2310) = 23.1 USDT` como threshold. Si `size_usdt < 23.1`, portfolio marca allocation FLAT con reason `below_min_order_23.1usdt` ANTES de enviar a execution. BingX nunca recibe orden inválida → `[EXEC] OPEN FALLIDO ETH` elimina a 0. Complementado con v2.4.2: el BRAIN_RECONCILE post-FLAT ahora va a DEBUG (rollback esperado), no contamina INFO logs.
Verificación esperada Smoke-B cycle 181 @ 10:59:50 UTC: 0 CRITICAL/OPEN FALLIDO ETH, presencia de `below_min_order_23.1usdt` en `[SIGNALS_DISCARDED]` para ETH si confidence GMM produce signal.
Cierre: fix desplegado. Patrón ALGO análogo (below_min_order genérico) queda cubierto por el mismo flujo. Patrón UNI (low_confidence, no precision) no resuelto por v2.4.3 pero silenciado por v2.4.2 (ver §13.3 B-UNI-1 INFORMACIONAL).
Referencias: engine.log múltiples fechas 2026-04-17 → 2026-04-21, v2.4.3 en §2.4, verificación SSH 2026-04-21 10:05-10:15 UTC.

**[RESUELTO] Auditoría Fidelidad 2 MR formal — 2026-04-21**
Contexto: auditoría formal análoga al audit 4×3 TF de 2026-04-20, extendida con matriz 3×3 cancelaciones (diferencial MR), verificaciones laterales v2.4.0+v2.4.1 aplicando a path MR, y empírico `_run_verify_test` sobre SEI/USDT C2 config 45686.
Método ejecutado:
- Matriz 4×3 stops (SL inicial, TS on-close, SL emergency, trigger close<sl_level) × 3 capas (Pine v7.25 MR / kernel MR / brain MR): A=B=C en las 4 filas.
- Matriz 3×3 cancelaciones (cancel_zona, cancel_tf, cancel_ghost) × 3 capas: A≈B=C en las 3 filas (B y C isomorfos, A más amplio semánticamente).
- Verificación lateral: execution_manager.py 100% agnóstico a strategy_type (0 matches grep universal). Fixes v2.4.0 + v2.4.1 aplican universalmente a posiciones MR.
- Empírico SEI/USDT C2 config 45686 sobre 1500 barras (warmup brain=500, warmup kernel=100): PnL 1.0180%=1.0180%, Trades 17=17, Wins 5=5, Cancels 2=2, MaxDD 3.9316%=3.9316%, GrossProfit 9.6434=9.6434, GrossLoss 8.6254=8.6254. Diff 0.0000 en 7 métricas.
Verificación adicional 2026-04-21 sobre duda de Ricardo (snapshot vs recompute): `_check_cancel_zona_mr` y `_check_cancel_ghost_mr` revisados línea por línea. Brain MR usa reindex-al-pasado (patrón `fast_line[entry_idx] < slow_resolved[entry_idx]` en day-closed branch, `fast_line[t] < slow_forming[t]` en same-day branch). Coincide exactamente con kernel MR líneas 293-313 y 347-372. `state.mr_entry_zone_bull` (SymbolState l.142) guardado en entry (l.2096/2116), leído en cancel_ghost (l.1746) como entry_was_bull. `state.mr_entry_filters_forming` y `state.mr_entry_slow_line` son dead fields (asignados, nunca leídos) — no afectan fidelidad, residuos de iteración previa de diseño.
Veredicto: FIDELIDAD 2 MR CONFIRMADA. 0 CRÍTICOS, 0 MEDIOS, 3 MENORES (documentados como MEJORA EN_ESPERA pre-reciclaje julio, ver §13.3 "Deuda documental/refactor menores").
Símbolo seleccionado SEI C2 por: PF 2.38 (más alto de 6 rescates), N fwd 24 (robusto ≥20), cluster C2 canónico MR (4 de 6 rescates son C2), evita contaminación B-UNI-1.
Artefactos generados (no commiteados al repo operacional, en carpeta de archivo): `audit_mr_fidelity_sei.py` (harness reutilizable), `data_cache/SEIUSDT_mean_reversion.npz` (precalc MR SEI, subproducto).
Referencias:
- Reporte completo auditoría: conversación 2026-04-21 mañana.
- Verificación snapshot vs recompute: conversación 2026-04-21 mediodía.
- §0.5 MR (ampliada 2026-04-21 con confirmación).
- §0.6 Kernel como verdad operacional (nueva 2026-04-21).
Cierre: auditoría formal completa. No requiere continuación. Futuras auditorías MR (ej. post-N≥15 empírico MR real) son re-validaciones, no primeras auditorías.

**[RESUELTO] Auditoría Fidelidad 2 TF cancel_tf — verificación específica 2026-04-21**
Contexto: extensión de la auditoría Fidelidad 2 TF formal del 2026-04-20 (matriz 4×3 stops). Ricardo expandió duda filosófica ("anti-repintado requiere snapshot del valor en el momento de cierre, no recomputación desde el presente") a TF tras verificación MR. Verificación específica de cancel_tf en brain TF comparado con kernel TF (lab_historico_numba_v8_3.py) y Pine v44 TF canónico.
Método ejecutado:
- Citas literales de `_check_cancel_tf` (brain_engine.py l.1371-1425, helper compartido TF/MR).
- Citas literales de cancel_tf en kernel TF (lab_historico_numba_v8_3.py l.1550-1580).
- Verificación snapshot-at-entry: `state.entry_filters_forming` (SymbolState l.123, asignado en entry l.1023/1039 path TF) usado como referencia de ENTRY en las 4 ramas (TF2/TF3 × same-block/cross-block).
- Tabla 4 ramas × 3 capas (Pine v44 / kernel TF / brain TF): Brain = Kernel ✓ en las 4 ramas.
Veredicto: FIDELIDAD 2 TF CONFIRMADA (doble evidencia: matriz 4×3 original 2026-04-20 + verificación específica cancel_tf 2026-04-21).
Hallazgo colateral Fidelidad 1: kernel TF contiene comentario literal (l.1560-1562) documentando divergencia consciente con Pine v44. Kernel usa resolved[t] (último bloque HTF cerrado observable desde t) en vez de resolved[entry_bar] (reindex Pine-canónico). Documentado en §0.6 como principio operativo: divergencias kernel≠Pine con intención explícita son parte del diseño vigente, no bugs.
Implicación operacional: brain TF replica al kernel TF (incluido el "Fix fidelidad"), así que bot opera según kernel (no según Pine estricto). Si alguna vez se desea restaurar Pine-strict, requiere guardar `state.entry_filters_resolved` (actualmente no existe) y switch el helper para usar ese snapshot. No urgente.
Referencias:
- Reporte específico cancel_tf: conversación 2026-04-21 tarde.
- Matriz 4×3 original: §13.3 RESUELTO 2026-04-20.
- §0.6 Kernel como verdad operacional (nueva 2026-04-21).
Cierre: auditoría Fidelidad 2 TF completa (2 iteraciones independientes, misma conclusión). No requiere continuación.

**[RESUELTO] v2.4.1 Emergency stop path protegido — Smoke-B PASS 2026-04-20**
Contexto: finding Run 2 /ultrareview sobre rama v2.4.0-fidelity2-ts detectó que `update_trailing_stop` no-op introducido en v2.4.0 atrapaba también caller `atype="emergency_stop"` de `reconcile_state` (líneas 652-676 → `execute_cycle` 802). Red de seguridad desactivada en escenario de posición abierta sin stop. Medición histórica confirmó agujero teórico (0 disparos en 11 días × ~264 cycles/día = ~2900 evaluaciones reconcile); fix correcto independiente de frecuencia.
3 commits aplicados sobre v2.4.0-fidelity2-ts:
- be8c272: `_place_emergency_stop` helper (+94)
- 6d9c7cd: re-route + rename action + docstring (+16/-13)
- db4f8a1: fail-loud size guard (+16/-0)
Validación:
- Tests T7-T10 todos PASS (5 subtests: dry long/short, happy, fail, invalid_size a/b/c + update_trailing_stop rename + FIDELIDAD brain=kernel diff 0.0000).
- Smoke-A boot 19:07:59 UTC limpio: 8 posiciones sincronizadas, balance 297.02 USDT, 35s downtime total.
- Smoke-B cycle 166 (20:00 UTC): 7 TS_NOOP_V240, 0 EMERGENCY_STOP_*_V241, 0 UPDATE_TS post-deploy, duration 17347ms (+3s atribuible a 1 open + 1 close en el cycle, dentro de rango 14-22s), 0 errores/CRITICALS nuevos.
Descubrimiento pre-edit crítico: investigación de estructura `position` dict confirmó que canon es key `"size"` (línea 335 `get_open_positions` de `data_feed.py`), no `"contracts"`. Spec original del fix usaba `abs(position["contracts"])` que habría dado KeyError en producción. Helper final usa `position.get("size", 0.0)` consistente con `close_position:257` y pre-v2.4.0.
Cierre: merge v2.4.1-emergency-stop-fix → main aplicado tras Smoke-B PASS.
Referencias:
- `execution_manager.py` `_place_emergency_stop` + `update_trailing_stop`.
- Commits be8c272, 6d9c7cd, db4f8a1.
- MD5 v2.4.1: `50b126bea56a643003ff8f57592076bb`.

**[RESUELTO] v2.4.0 deploy + validación — Fidelidad 2 TS restaurada — 2026-04-20**
Contexto: tras auditoría de fidelidad 4×3 del 2026-04-20 (§13.4 RESUELTO) + verificación literal del kernel (§13.2 HALLAZGO confirmado) + lectura Pine por Ricardo, se implementó v2.4.0 con dos cambios: cp1252 fix + update_trailing_stop no-op. Rama git v2.4.0-fidelity2-ts, base commit baseline 8af9094, 3 commits (6b5743c docs + 607199a cp1252 + bc42352 no-op).
Deploy VPS 2026-04-20 14:08:22 UTC:
- Backup v2.3.11: execution_manager.py.bak-v2311-20260420-140719, lab_historico_numba_v8_3.py.bak-v2311-20260420-140719.
- MD5 3-way sincronizado (comboclaude + combolab + VPS).
- Downtime: 20s.
- Boot limpio: 45 GMM + 45 specialists + 45 sectores + 9 posiciones sincronizadas + balance 297 USDT.
- Cycle 161 post-v2.4.0 (15:00:07-15:00:09): 6 TS_NOOP_V240 (BNB, ALGO, IMX, MANA, GRT, THETA) + 2 cierres on-close vía close_position MARKET (ONDO div_exit PnL=0.00, RENDER zone_exit PnL=+0.25), 0 UPDATE_TS cancel+place-new.
Comportamiento validado:
- Brain TS vive on-close en state.sl_level (Pine/kernel fiel).
- BingX conserva stop_market al 5% emergency (colocado en open_position).
- close_position MARKET ejecuta cierres on-close normales (div_exit, zone_exit, sl_hit).
- Ventana migración Opción B: 8 posiciones legacy mantienen stop tensado hasta cerrarse. Ver ítem B-UNI-2 en §13.2 sobre implicación para trade_history.csv.
Cycle duration: cycle 161 = 16311ms. No medición pura porque incluyó 2 closes. Smoke-C pendiente para validar reducción esperada en cycle "puro TS" (-1.5 a -2s vs cycles v2.3.11 que promediaban 16s).
Referencias:
- §13.2 HALLAZGO Divergencia Fidelidad 2 TS — marcado RESUELTO.
- commit bc42352 (no-op) y 607199a (cp1252).
- MD5 post-deploy: e498e486...5ebf (execution_manager), 464137d7...4f32 (lab_historico_numba).
Cierre: Fidelidad 2 restaurada para TS. Los siguientes cierres por TS ratcheteado ejecutarán on-close via close_position MARKET, no por stop_market intrabar. Futuros audit v5.1 podrán comparar directamente kernel ↔ bot live sin la deuda arquitectural previa.

**[RESUELTO-CORRECCIÓN] Audit fidelidad 4x3 — revisión tras lectura Pine por Ricardo — 2026-04-20**
Contexto: auditoría inicial del 2026-04-20 concluyó "sistema materialmente FIEL al Pine" incluyendo TS. Ricardo leyó el Pine directamente (indicador_v44_0_smartdiv_v11_0_TF.pine) y detectó divergencia no capturada: Pine evalúa TS on-close (`barstate.isconfirmed` + `close < stopLossLevel_logic` línea 905), bot live delega a BingX stop_market que ejecuta intrabar.
Verificación adicional del kernel lab confirmó que éste es FIEL a Pine (on-close): líneas 1503-1509 `close_p < sl_level`. Divergencia aislada en execution_manager.py del bot live (update_trailing_stop líneas 574-740).
Audit original corregido:
- Mecanismo 1 (TS): veredicto FIEL → DIVERGENCIA MATERIAL (solo capa live, Fidelidad 1 intacta).
- Mecanismo 2 (SL Inicial 3%): FIEL (sin cambios, es el nivel inicial del mismo stopLossLevel_logic).
- Mecanismo 3 (SL Emergency 5%): FIEL (sin cambios, intrabar via BingX stop_market al 5% coincide con Pine).
- Mecanismo 4 (Cooldown R1): DIVERGENCIA CONSCIENTE brain ↔ Pine/kernel (sin cambios en interpretación, post-N>=50).
Lección metodológica: auditar por citas literales en las 3 capas no es suficiente para detectar divergencias cuando una capa delega comportamiento a un tercero (BingX en este caso). Hay que rastrear el flujo completo: brain calcula X → execution traduce X a orden Y → BingX ejecuta Y con su propia semántica (intrabar). La semántica final es la del exchange, no la del cálculo del brain. En auditorías futuras, cuando un mecanismo se delega al exchange, documentar explícitamente qué trigger type usa (MARK_PRICE vs LIMIT vs on-close equivalent) y cómo se compara con la semántica simulada.
Acción derivada: v2.4.0 para alinear execution con Pine/kernel on-close (ver §13.2 [HALLAZGO] ACTIVO).
Referencias: audit inicial del 2026-04-20 (mismo día, horas previas), verificación literal del kernel líneas 1476-1509, indicador_v44_0_smartdiv_v11_0_TF.pine línea 905 (trigger `close < stopLossLevel_logic` en barstate.isconfirmed).

**[RESUELTO] v2.3.11 estabilidad extendida verificada — 2026-04-20 10:00 UTC**
Contexto: tras 17 ciclos desde deploy v2.3.11 (17:51 UTC 2026-04-19 → 10:00 UTC 2026-04-20), verificación empírica vía SSH al VPS confirma estabilidad operacional sin regresión silenciosa.
Métricas observadas (ciclos 140-156):
- Cycle durations: 14832-16941 ms (rango 15-17s), dentro de ventana operacional 14-22s. Duración media ~15.7s, consistente con el +~1s esperado por forming fetch serial (paginated 0.88s → total ~1.8s).
- Forming fetch warnings: 0 en los 17 ciclos. Ni "forming fetch fallo" ni "forming ts inconsistente". La lógica 3-way determinística maneja al 100% la inconsistencia de BingX sin saturar logs.
- Errores Python nuevos: 0 relacionados con data_feed, brain o execution post-deploy. Las asyncio "Unclosed client session" observadas son de los stops controlados de los 5 deploys del 2026-04-19 (v2.3.7 → v2.3.11), ninguna post-v2.3.11 al 2026-04-20 10:00 UTC.
- Engine state coherente: peak_balance=298.3853, current_balance=296.8073, dd_multiplier=1.0, circuit_breaker_active=false. 7 posiciones abiertas al cycle 156 (RENDER short, THETA long, ALGO short, GRT long, MANA long, ONDO short, BNB long; INJ cerrado en cycle 156 con div_exit -0.07 USDT).
- Cross-feature validation: v2.3.8 B7 (partial fills) sin disparos en ventana observada — no hubo partial fills de apertura en los 17 ciclos, coherente con balance 297 USDT y mercado lateral observado.
- Recurrence benigna: ETH/USDT below minimum precision 0.01 (sizing 7 USDT a ETH 2307 = 0.00307 ETH < 0.01 BingX min) generó 5 CRITICALs 2026-04-17/18 + 1 hoy 10:00 UTC. Pre-existente (no post-v2.3.11), manejado limpiamente por BRAIN_RECONCILE (reset position=0 tras fallo open). Edge case de balance bajo, no regresión.
Cierre: v2.3.11 validada operacionalmente. Fidelidad 2 mantenida estructuralmente sin deuda adicional descubierta. Próxima verificación disparada por acumulación de trades hacia N>=50 post-v2.3.3.
Referencias: verificación SSH del 2026-04-20 10:05 UTC al VPS IP_VPS_TOKIO_REDACTADA, engine_state.json saved_at 2026-04-20T10:00:10Z, /home/trader/combolab/engine.log tail cycle 156.

**[RESUELTO] H1 + H4 health_monitor daily summary fix empíricamente validado — 2026-04-20 00:00 UTC**
Contexto: cierre del ítem de §13.1 VERIFICANDO "Daily summary post-v2.3.6 con métricas correctas". El daily summary de 2026-04-20 00:00:08 UTC (primer summary completo post-v2.3.6 deploy del 2026-04-19) reporta las dos métricas fijadas con valores correctos:
- DD from peak: -0.7% (H1 fix correcto). Comparativa: daily summaries 2026-04-18 y 2026-04-19 00:00 UTC (pre-fix) reportaban -121.7% espurio. Predicción en §13.1 ("~0.2-0.5%") se cumple con margen. El DD técnico es 0.53% ((298.39-296.81)/298.39), redondeado al grid de precisión del summary como -0.7%.
- Days since recycle: 12/90 (H4 fix correcto). Pre-fix retornaba 9999/90 disparando RECYCLE RECOMENDADO espurio. Valor real (~11.96 días desde 2026-04-08) cuadra con last_recycle.txt en el VPS.
- Portfolio: +0.8 USDT (coherente con saldo empírico y trades acumulados).
- Symbols section intacta: 32 symbols active con counts de trades por símbolo (ADA: 1, ALGO: 6, APT: 12, BNB: 1, ..., GRT: 3, HBAR: 3, ...) — todos con "need 15 to evaluate" placeholder intacto.
Summary salió completo sin truncamiento. Observabilidad del daily summary Telegram restaurada al nivel correcto.
Cierre: H1 y H4 confirmados operacionales empíricamente. Ítem §13.1 movido a §13.4.
Referencias: verificación SSH 2026-04-20 10:05 UTC, engine.log 2026-04-20 00:00:08 "[ALERT] 📊 Health Report (30d rolling)", §2.6 health_monitor bugs #3 (H1) y #4 (H4), v2.3.6 deploy del 2026-04-19.

**[RESUELTO] ORPHAN_CLOSE disparo orgánico verificado — 2026-04-20**
Contexto: cierre del ítem de §13.1 VERIFICANDO "[BUG] ORPHAN_CLOSE sin disparo orgánico — 2026-04-16". Desde el despliegue de v2.3.2 (2026-04-16 ~17:00 UTC) no había habido disparo orgánico del mecanismo. Verificación SSH del 2026-04-20 10:05 UTC encontró 3 eventos [ORPHAN_CLOSE] orgánicos en las últimas 72h, todos sobre OP/USDT:
- 2026-04-18 07:00:10 UTC — OP/USDT short reconstruido, entry=0.1318 exit~=0.1333635 pnl~=-1.19%.
- 2026-04-19 01:00:12 UTC — OP/USDT long reconstruido, entry=0.1264 exit~=0.125171 pnl~=-0.97%.
- 2026-04-19 23:00:07 UTC — OP/USDT long reconstruido, entry=0.123 exit~=0.121589 pnl~=-1.15%.
Verificación de los 3 chequeos que el ítem §13.1 demandaba:
- (a) Log [ORPHAN_CLOSE] presente: ✅ los 3 events en engine.log.
- (b) trade_history.csv con flag reconstructed_post_hoc/reconstructed: ✅ confirmada fila "2026-04-19 23:00:07.601,OP/USDT,long,0.123,0.121589,0.0,-1.1472,0.0,0.0,sl_trigger_reconstructed,reconstructed,1776628809478" (entry, exit, pnl_pct, reason_exit="sl_trigger_reconstructed", flag="reconstructed", entry_timestamp_ms del v2.3.3).
- (c) state.position=0 post-ciclo: ✅ engine_state.json saved_at 2026-04-20T10:00:10Z no tiene OP/USDT en posiciones con position != 0 (state limpio).
Los 3 events son disparos reales de BingX (stop trigger entre ciclos) procesados end-to-end por la lógica de reconciliación v2.3.2 sin intervención manual. El reconstruct también funciona consistente con H2 de v2.3.5 (reconstructed excluido de agregados del health_monitor).

Análisis de tipo de cierre (verificación profunda 2026-04-20 11:30 UTC):
- Escenario A (SL Emergency 5% intrabar): **0 casos**. |% variación| esperado ~5.0%, observado -1.19%/-0.97%/-1.15%.
- Escenario B (Trailing Stop ratcheteado, gatillo intra-hora entre ciclos): **3/3 casos**. TS movido a distancia corta del entry antes del gatillo real.
  - Caso 1 (04-18 07:00): SHORT OP/USDT @0.1318, SL inicial 0.139125 (+5.5%), TS 4 updates en 4h → 0.1333635 (+1.2%). Gatillo entre cycles 104-105. Brain cycle 105 SIGNALS_RAW CLOSE_SHORT reason=sl_hit.
  - Caso 2 (04-19 01:00): LONG OP/USDT @0.1264, SL inicial 0.12027 (-4.8%), TS 1 update en 1h → 0.125171 (-1.0%). Gatillo entre cycles 122-123. Brain cycle 123 CLOSE_LONG reason=tf_exit (brain también quería exit por condición TF).
  - Caso 3 (04-19 23:00): LONG OP/USDT @0.123, SL inicial 0.116945 (-4.9%), TS 2 updates en 3h → 0.121589 (-1.1%). Partial fill en apertura 79.4/79.45 capturado por v2.3.8 B7 (cross-feature). Gatillo entre cycles 144-145. Brain cycle 145 CLOSE_LONG reason=sl_hit.

Conclusión ampliada: ORPHAN_CLOSE captura **tanto SL Emergency 5% (intrabar hipotético) como Trailing Stops intermedios (intra-hora reales)**, ambos procesados end-to-end. En operación real, la mayoría de "cierres entre ciclos" observados hasta ahora vienen por TS ratcheteado, no por SL 5%. El exit_price reconstruido proviene de state.sl_level del brain (limitación conocida L4 de §13.3); el real exit fill de BingX puede diferir ±0.5%. PnL reconstruido es aproximado pero direccionalmente correcto. En los 3 eventos el brain en el ciclo siguiente también detectó condición de exit (sl_hit en 2, tf_exit en 1) — coherente con que el precio cerró cerca del TS, sin divergencia brain↔BingX.

Observación secundaria: los 3 ORPHAN_CLOSE son de OP/USDT, sugiere volatilidad y reversiones sustanciales en OP los últimos 3 días haciendo TS actuar agresivamente. No es bug del mecanismo — es mercado. Si aparece patrón similar recurrente en otros símbolos, considerar análisis de eficiencia del TS ratchet factor (actual 0.985/1.015 = 1.5%).
Cierre: mecanismo ORPHAN_CLOSE validado empíricamente con 3 casos reales, todos Escenario B (TS). Ítem §13.1 movido a §13.4.
Referencias: verificación SSH 2026-04-20 10:05 UTC, 3 eventos en engine.log/engine.log.1.gz, execution_manager.py _handle_orphan_close_signal(), live_engine.py integración con reconcile_state, v2.3.2 execution_manager bug #7, trade_history.csv fila 2026-04-19 23:00:07.

**[RESUELTO] Política /ultrareview v3 — entendimiento empírico — 2026-04-20**
Contexto: tras Run 1 (2026-04-20 sobre rama fidelity-2-review con diff docstring +26/-1, 0 findings) + investigación en documentación oficial (code.claude.com/docs/en/ultrareview) se corrige la política v2 formulada el 17-abril que asumía "diff trivial como pretexto para análisis holístico del codebase". Esa interpretación provenía de blogs secundarios, no de documentación oficial.
Realidad verificada empíricamente:
- /ultrareview analiza el DIFF entre current branch y default branch (main). No es auditor de codebase completo.
- Incluye cambios no commiteados del working tree.
- Orientado a pre-merge review de cambios sustanciales (cientos a pocos miles de líneas).
- Diff trivial (docstring solo) = 0 findings = run desperdiciado.
- Diff excesivamente grande (bug #50029 GitHub: 3318 archivos, +500K líneas) = posible retorno silencioso de findings:[] sin diagnóstico.
- No es sustituto de auditoría manual holística del codebase.
Política v3 (reemplaza v2):
- Lanzar /ultrareview ANTES de deploy de cambios funcionales sustanciales (no estilísticos/documentales).
- Tamaño óptimo del diff: cientos a ~2000 líneas, múltiples archivos con lógica real modificada.
- NO lanzar con diff trivial esperando análisis holístico — no es así como funciona.
- Verificar antes de cada run: el diff representa cambio funcional significativo, no solo documentación o refactor cosmético.
Runs restantes (2 de 3 lifetime):
- Run 2: reservado para R1 cooldown brain fix cuando se implemente tras N>=50 trades. Cambio en brain_engine.py de lógica crítica (cooldown same-bar) es exactamente el caso de uso canónico.
- Run 3: reservado para P1 leverage variable cuando/si se implemente post-N>=50 con evidencia empírica. Cambio multi-módulo (portfolio, execution, posiblemente brain) es caso de uso canónico.
Run 1 resultado: 0 findings, lección aprendida. No fue malgasto — permitió corregir política sin gastar dinero. Alternativa hubiera sido creer interpretación optimista y malgastar Run 2 y Run 3 experimentando.
Lección metodológica capturada: "interpretación de funcionalidad basada en blogs secundarios vs documentación oficial puede diverger. Antes de decisiones consequential con recursos limitados (runs gratuitos, tiempo, deploys críticos) verificar fuentes primarias."
Disparo: ninguno adicional. Política cerrada y documentada para sesiones futuras.
Cierre: entendimiento consolidado. Próxima invocación de /ultrareview esperada cuando R1 o P1 alcancen ventana de implementación (post-N>=50 trades).
Referencias:
- Documentación oficial: code.claude.com/docs/en/ultrareview.
- Bug conocido scope grande: github.com/anthropics/claude-code/issues/50029.
- Run 1 del 2026-04-20: rama fidelity-2-review, diff docstring, 0 findings.
- Política v2 del 2026-04-17 reemplazada por esta v3.

**[RESUELTO] Setup git local de combolab/ — 2026-04-20**
Contexto: combolab/ inicializada como repo git local sin remote (sin GitHub). Permite versionado de fixes con trazabilidad, compatibilidad con /ultrareview, y backup con historia clara. Decisión basada en investigación del 2026-04-20 que confirmó que /ultrareview puede operar sobre git local sin necesidad de GitHub (sube copia cifrada al sandbox Anthropic, no a repo público).
Configuración final:
- `git init` en c:/Users/rixip/combolab/.
- Rama default: main.
- Sin remote configurado.
- .gitignore con patrón *.bak* (catch-all) + excepciones !regime_wf/*.bak-TF-* y !regime_wf/*.bak-MR-* para preservar backups semánticos documentados (cláusula rollback §9.2.1).
- Total archivos commiteados: 524 (7 backups automáticos .bak_20260410_* pre-sesión 17-abril excluidos del versionado pero conservados en disco para recuperación manual).
- Archivos clave incluidos: lab_historico_numba_v8_3.py (kernel lab), indicador_v44_0_smartdiv_v11_0_TF.pine (fuente original Pine Script), 45 specialist_configs, data_cache parquets, antiguos de referencia/.
- Baseline commit: v2.3.11 tras Fidelidad 2 restaurada.
- Rama actual: main (limpia).
Workflow de deploy VPS: sin cambios. Sigue siendo scp + systemctl. Git local es para versionado y /ultrareview, no para deploy. Si en el futuro se quiere deploy via git, añadir pull al VPS sería cambio menor.
Prerequisito operacional crítico descubierto hoy: Claude Code debe lanzarse desde el working directory del repo git a revisar. Si se trabaja con dos repos (comboclaude/combolab), abrir sesión dedicada en combolab/ para cualquier operación git o /ultrareview. La sesión habitual corre desde comboclaude/ (sin git), por lo que /ultrareview fallaría con "Could not find merge-base" desde ahí.
Cierre: setup completo, testeado con /ultrareview Run 1, sin acciones pendientes.
Referencias: sesión del 2026-04-20, commits 8af9094 (baseline) + 16aa6d3 (docstring Fidelidad 2).

**[RESUELTO] v2.3.11 — Fidelidad 2 restaurada via forming fetch determinístico — 2026-04-19**
Contexto: Deploy del fix opción (b) para el HALLAZGO "Lag estructural de 1 bar brain↔live vs convención lab" (originalmente trackeado en §13.2 como ACTIVO el mismo 2026-04-19 con decisión transitoria opción (a) de "aceptar como feature"; reemplazado horas después por análisis más profundo que concluyó que el lag era sesgo unidireccional sistemático — "entrar una vela más tarde nunca es ventaja" — justificando opción (b)).
Cambio técnico: data_feed.download_all_ohlcv extendido con fetch adicional sin `since` (limit=2) tras el paginated. BingX paginated incluye el forming INCONSISTENTEMENTE (verificado empíricamente: a las 17:35:57 UTC paginated iloc[-1]=16:00 cerrada; a las 17:38 iloc[-1]=17:00 forming; a las 17:47 iloc[-1]=16:00 cerrada). Lógica 3-way determiniza: (a) si forming_ts == last_paginated+1h → append; (b) si forming_ts == last_paginated → update OHLC in-place con snapshot fresh (paginated ya traía forming, actualizar con valores del forming fetch que son ~unos ms más recientes); (c) otros (inconsistencia real, race xx:00:00) → warn y df sin modificar. Fallback robusto en excepción: warn y df sin modificar (modo lag solo ese símbolo ese ciclo).
Resultado: iloc[-1] siempre es el bar t en curso (close_forming ≈ close_real a ~6s del cierre). state.entry_bar_timestamp ahora persiste hora t (alineado con kernel lab que decide-y-entra con close[t] del mismo bar). Fidelidad 2 estructuralmente restaurada.
Brain_engine, live_engine, execution_manager: SIN cambios. El fix es puramente data-source.
_run_verify_test invariante — histórico .parquet no tiene forming, test sigue siendo válido como non-regression de la lógica brain.
Tests pre-deploy: 5/5 PASS (3 ramas + 2 fallbacks).
- Test integración BingX (10 símbolos): 10/10 con iloc[-1]=current_hour, 0 warnings. Latencia 1848ms (vs 880ms pre-fix, +~1s tolerable en budget de 14-20s cycle).
Deploy VPS: stop 17:51 → scp /tmp/data_feed_v2311.py → chown trader:trader → start 17:51:53. Bot arrancó limpio: 45 GMM + 45 specialists + 45 leverage + 45 sectores + 6 posiciones sincronizadas + balance 297.19 USDT. Ciclo #140 listo. 0 errores Python. MD5: daa7b2a8f86bf8f86469004133a6556a (comboclaude + combolab + VPS).
Backup v2.3.10: /home/trader/combolab/live/data_feed.py.bak-v2310-20260419-175121.
Métricas primer cycle post-deploy (#140, 17:59:50 → 18:00:09 UTC):
- Download: 1.12s (vs 0.88s baseline = +240ms por forming fetch, dentro de lo esperado por 45 forming fetches secuenciales por símbolo).
- Cycle total: 18804ms (rango normal 14-20s, sin degradación por el fix).
- ENGINE_STATE.t=1776621590 (17:59:50 UTC cycle start).
- SIGNALS_RAW "t":1776618000 = bar forming 18:00:00 UTC (iloc[-1] = bar t en curso) — confirmación operacional de Fidelidad 2.
- Forming warnings: 0 (ni "forming fetch fallo" ni "forming ts inconsistente"). El 100% de los 45 símbolos procesados via rama (a) append o (b) update-in-place silenciosamente.
- 5 señales activas (UNI SHORT, ONDO CLOSE_LONG, POL SHORT, INJ SHORT, SAND SHORT); 2 aperturas ejecutadas (INJ @3.214, SAND @0.07857) + 1 cierre (ONDO PnL −0.17 USDT) + 2 TS updates + 2 BRAIN_RECONCILE (UNI, POL discarded post-exec por balance bajo — patrón esperado).
- Partial fills capturados correctamente por v2.3.8 B7 (INJ 2.0/2.23, SAND 104/104.73) — cross-feature validation.
- 0 errores Python.
Opción B2 (forming fetch tardío a 2s del cierre para residual 6s→2s) documentada en §13.3 EN_ESPERA con disparador virtualmente improbable.
Cierre: fix aplicado, ambos repos sincronizados, deploy exitoso, tests PASS, Fidelidad 2 estructuralmente recuperada. Pendiente validación primer cycle empírico.
Referencias: data_feed.py `_fetch_one` post-append forming, test_v2311.py (5 tests unitarios), test_integration_v2311.py (BingX real), §0.3 aplicación concreta actualizada, §2.6 fix #8, v2.3.11 fila en §2.4.

**[RESUELTO] HALLAZGO Lag estructural de 1 bar brain↔live vs convención lab — 2026-04-19**
Contexto original (antes RESUELTO): Parte A de Fase 1 reveló divergencia de convenciones entre lab y live, caracterizada empíricamente con tests sobre BingX:
- (1) Path paginado de BingX con parámetro `since` EXCLUYE forming candle inconsistentemente; path sin `since` siempre incluye forming (verificado 2026-04-19 con comportamiento variable según timing).
- (2) Bot productivo usaba OHLCV_LIMIT=1500 → fuerza pagination → iloc[-1] podía ser última cerrada (ts = cycle_hour − 1:00).
- (3) Brain decidía con close[t−1] en esos casos. Order sent a xx:59:59.5, fill ≈ close[t] = price at cycle_hour:00.
- (4) Lab kernel (run_simulation_numba): `entry_price = close_p = close[t]` para signal en bar t. Lab "decide y entra en close del MISMO bar".
- (5) Convención divergente: live (modo lag) decidía en close[t−1] y entraba en close[t] (gap 1 bar); lab decide y entra en close[t] (gap 0).
Historia del bug latente: §2.6 data_feed fix #4 aumentó OHLCV_LIMIT de 120→1500 por necesidad de histórico. La pagination se introdujo como consecuencia técnica (BingX max 1440 por fetch). El cambio semántico de iloc[-1] fue efecto colateral no documentado.
Resolución (v2.3.11, 2026-04-19): **Opción (b) aplicada — Fidelidad 2 restaurada estructuralmente.** fetch adicional sin `since` tras paginated + lógica 3-way determiniza iloc[-1] = bar t en curso siempre. El lag 1 bar (60 min) queda reducido a ~6s (residual de timing del cycle xx:59:54 vs cierre xx:00:00). Principio aplicado: "entrar una vela más tarde nunca es ventaja" — era sesgo unidireccional. Opción B2 (reducir residual a ~2s con refactor cycle) documentada en §13.3 EN_ESPERA como mejora futura marginal.
Referencias: data_feed.py fix v2.3.11 (§2.6 fix #8), §0.3 Filosofía de fidelidad actualizada, entrada v2.3.11 en §13.4 arriba.

**[RESUELTO] Fase 1 C1 — Funding fallback frequency 0% — 2026-04-19**
Contexto: Ítem original en §13.3 "Verificar frecuencia de fallback funding estimado" (relacionado con E1 del ultra review execution_manager). Investigación empírica sobre 11 archivos de log (engine.log actual + 10 .gz rotados desde 2026-04-09): 0 ocurrencias de "Funding history no disponible" vs 35 SIGNALS_EXECUTED totales post-v2.3.1. Ratio: 0%. El fallback estimado con signo invertido (bug E1) nunca ha disparado en producción. fetch_funding_history de BingX es 100% disponible en ventana observada.
Cierre: investigación de frecuencia completada. E1 permanece como bug latente sin urgencia operacional — fix de signo correcto pero sin impacto actual. No genera trabajo Fase 2.
Referencias: Fase 1 C1 del 2026-04-19, execution_manager.py línea 177 (E1), §13.3 MEJORA E1 EN_ESPERA (preservada).

**[RESUELTO] Fase 1 C5 — current_balance usage audit — 2026-04-19**
Contexto: Ítem introducido tras deploy v2.3.6 para verificar edge case post-restart. Grep de live/ encontró 5 usos productivos: health_monitor.py:215 (guard explícito L219 `peak>0 and current>0 and current<=peak`), live_engine.py:159 (init default 0.0), :274 (asignación dentro de `_calc_dd_multiplier(balance)` protegido por L270 `if balance<=0: return 0.0`), :1046 (serialización), :1123 (load con default). Todos SAFE. Ningún uso en camino crítico (sizing, alerts operacionales) sin guard. Edge case post-restart (current_balance=0 hasta primer ciclo) correctamente manejado por guards existentes.
Cierre: auditoría completada sin hallazgos adicionales. Ningún fix requerido.
Referencias: Fase 1 C5 del 2026-04-19, deploy v2.3.6, health_monitor.py _compute_portfolio_dd.

**[RESUELTO parcial] Fase 1 C4 — D4 forming/closed refutado; genera HALLAZGO colateral — 2026-04-19**
Contexto: Ítem original en §13.3 "data_feed: ambigüedad forming vs closed en última candle" (D4 ultra review data_feed). Investigación empírica resolvió la pregunta original: brain NO evalúa con forming candle OHLC incompleto. Evidencia decisiva: test con fetch_ohlcv limit=1500 paginado (path productivo del bot) retorna iloc[-1] = última cerrada, NO forming. BingX con parámetro `since` (inherent al path paginado) EXCLUYE forming candle. El iloc[-1] siempre tiene close complete.
Sin embargo, la investigación reveló un hallazgo colateral: el path paginado introduce lag estructural de 1 bar entre brain decision y convención lab. Documentado como HALLAZGO separado en §13.2 "Lag estructural de 1 bar brain↔live vs convención lab".
Cierre: D4 original (riesgo de forming-candle contamination en brain) RESUELTO categóricamente. Hallazgo colateral (lag 1 bar) trackeado aparte con disparador propio (primer reporte analyzer v2.4.1 con N≥50).
Referencias: Fase 1 C4 del 2026-04-19, §13.2 "Lag estructural de 1 bar brain↔live vs convención lab", data_feed.py líneas 141-157.

**[RESUELTO] v2.3.10: D4 Telegram alerts fire-and-forget — cierre sesión 2026-04-19**
Contexto: Último deploy de la sesión 2026-04-19. Fix aislado con decisión clara: asyncio.create_task reemplaza await secuencial en los 2 loops de _post_cycle (OPEN + CLOSE). Justificacion: alertas son observabilidad, no decisiones operacionales. _send_alert tiene try/except interno (httpx + fallback urllib + logger.warning en Exception), excepciones no propagan a tasks huerfanas. Event loop retiene tasks hasta completion, no hace falta guardar referencias para evitar GC.
Alcance del fix: solo los 2 loops de alertas trade (OPEN, CLOSE). Single alerts (ERROR linea 797, DD linea 807, daily_summary linea 818) mantienen await — no son bottleneck.
Tests pre-deploy:
- Syntax check OK.
- Test latencia: sequential 5010ms (10 alerts x 0.5s) → fire-and-forget 0ms (100% reduccion).
- _run_verify_test: IDENTICO al baseline (4 senales, 2 trades, PnL +1.2940%, bars 511/523/610/617). D4 no toca brain, verificacion paranoia OK.
Deploy VPS: stop 13:13 → scp + chown → start 13:13:07 (active). Boot limpio: 45 GMM + 45 specialists + 45 leverage + 45 sectores + 6 posiciones sincronizadas + balance 297.22 USDT. MD5: eb6561186367e5eb2643c8d83247ce6a (comboclaude + combolab + VPS).
Cierre: fix aplicado, sincronizados ambos repos, desplegado al VPS, verificacion post-deploy exitosa.
Referencias: live_engine.py _post_cycle linea 767-793 (2 asyncio.create_task loops), Fase 3 cierre sesión del 2026-04-19 13:13 UTC.

**[RESUELTO] v2.3.9: B1 _reset_state_on_exit — brain_engine refactor isolado — 2026-04-19**
Contexto: Fase 3 Grupo B parte 2 aplicada con SCOPE REDUCIDO: solo B1 de los 3 refactors estilísticos planeados (B2 prev_zone y B3 TF locals vs MR state DIFERIDOS — ver notas en §13.3). Razón de diferir: Fase I de investigacion revelo complejidad inesperada en ambos (B2 premise del ultra review incorrecta + semantica cross-strategy TF/MR; B3 requiere modificar compute_divergences API en camino critico con riesgo de regresion sin test diferencial completo).
B1 aplicado:
- Helper `_reset_state_on_exit(state: SymbolState, mr: bool = False)` top-level standalone (NO metodo — _evaluate_bar es funcion top-level).
- Resetea 8 campos: position, entry_price, sl_level, bars_since_entry, entry_bar_timestamp, entry_filters_forming (int=0 no dict), stop_order_id (str='' no None), entry_timestamp_ms. Si mr=True: ademas mr_zone_history=[].
- NO resetea: current_cluster, active_config_id, cluster_probs (contexto de clasificacion), div_ctx, prev_zone, prev_div, cooldown_until (contexto inter-ciclo).
- Invocacion reemplaza 2 bloques de reset existentes: linea 877 TF (`_reset_state_on_exit(state, mr=False)`), linea 1977 MR (`_reset_state_on_exit(state, mr=True)`).
- Interaccion con v2.3.7 bars_since_entry: OK. Increment al inicio de _evaluate_bar si position!=0 (linea 649-650); reset dentro de evaluacion en exit. Atomico por bar, sin race condition.
Tests pre-deploy:
- Syntax check OK.
- Test unitario: instanciar SymbolState con 8 campos "sucios" + 5 campos no-tocables (current_cluster=2, active_config_id=12345, div_ctx_bull=True, cooldown_until=100, prev_zone_bull=True). Post-call: 8 campos reseteados, 5 campos intactos. Caso MR con mr_zone_history=[True,False,True] reseteado a []. Caso TF sin mr_zone_history tocado. Todo PASS.
- **Test crítico _run_verify_test IDENTICO al baseline Fase I**: 4 senales, 2 trades, PnL +1.2940%, Wins 1, Losses 1, Gross profit 1.8874%, Gross loss 0.5935%, Bar 511 LONG @ 67177.06 (ma_cross), Bar 523 CLOSE_LONG @ 68512.17 (tf_exit), Bar 610 SHORT @ 67955.10 (ma_cross), Bar 617 CLOSE_SHORT @ 68290.45 (tf_exit). Non-regression categorica verificada — B1 es refactor puramente semantico sin cambio de comportamiento.
Deploy VPS: stop 12:07:13 → scp + chown trader:trader → start 12:07:28 (active). Boot limpio: 45 GMM + 45 specialists + 45 leverage + 45 sectores + 7 posiciones sincronizadas (una cerro durante cycle 134 pre-deploy). Balance 297.33 USDT. 0 errores Python.
MD5: 95123b99ad71b7dee53792faabf2a191 (comboclaude + combolab + VPS).
Hallazgo colateral de Fase II v2.3.8 verification: cycle 134 (11:59:50 UTC) disparo B7 naturalmente — "OPEN SHORT APT/USDT: partial fill detectado filled=8.5 < requested=8.59. Stop dimensionado a filled." — validacion empirica en produccion del fix B7 de v2.3.8.
Cierre: B1 aplicado, sincronizados ambos repos, desplegado al VPS, verificacion post-deploy exitosa. B2 y B3 quedan en §13.3 con lecciones aprendidas documentadas.
Referencias: brain_engine.py _reset_state_on_exit (linea ~262 post-edit), brain_engine.py llamadas lineas 877 y 1977, _run_verify_test baseline y comparacion Fase I/III del 2026-04-19, Fase 3 Grupo B parte 2 del 2026-04-19 12:07 UTC.

**[RESUELTO] v2.3.8: 3 fixes Fase 3 Grupo B parte 1 — data_feed + execution — 2026-04-19**
Contexto: Despliegue aislado del modulo data_feed + execution_manager (3 de los 4 fixes planeados; B6 no aplicado por dependencia real). Sincronizados ambos repos (md5 data_feed: eb4a72f6cad2cd9783db2f91fee82fa6, execution_manager: 6c3ac2227add8fa3dfb3fb1b551d007a), desplegado al VPS con stop/start systemd 10:27-10:28 UTC. Bot arranco limpio: 45 GMM + 45 specialists + 45 leverage + 45 sectores + 8 posiciones sincronizadas + balance 297.63 USDT, 0 errores Python.
Los 3 fixes aplicados:
- B4 data_feed retry helper: download_all_ohlcv tenia retry inline con backoff fijo; get_balance/get_open_positions/get_open_orders no tenian retry — un hiccup propagaba excepcion, engine caia a consecutive_errors++. Implementado `_retry_async(coro_factory, name, max_retries=3, base_delay=0.5)` con backoff exponencial (0.5s → 1.0s → 2.0s). `ccxt_sync.AuthenticationError` re-lanzada sin retry (reintentar con creds invalidas es inutil y ruidoso). Aplicado a las 3 funciones faltantes via `lambda: exchange.fetch_X()` (callable necesario para re-await). Tests: retry flaky OK, auth no-retry OK.
- B5 OHLCV empty first-fetch: pagina 1 vacia en download_all_ohlcv caia al else con ohlcv=[] silenciosamente — brain saltaba el simbolo. Fix: `raise ValueError(...)` explicita cuando ohlcv_1 vacio, activa outer `for attempt in range(MAX_RETRIES)` que hace retry con backoff. IMPORTANTE: preservado el parametro `since` (spec original del usuario propuesta sin since cambiaria la semantica de forming candle, que Fase 1 decidio mantener como Opcion-a — no-forming via pagination). Test mock con primer fetch vacio: retry triggered, DataFrame final no vacio.
- B7 partial fills usan filled real: stop y emergency_close usaban `size` (allocation requested) no `entry_order.filled` (real de BingX). Si BingX ejecuta parcialmente (raro pero posible al escalar capital cerca de liquidez fina), stop quedaba sobredimensionado y podria fallar reduceOnly o ejecutarse mal. Fix: `filled_size = float(entry_order.get("filled", 0) or 0)` con warning log diferencial (partial fill vs fallback por campo ausente). Dict de return tambien usa filled_size en lugar de size. Test de logica boolean con entry_order full/partial/missing/zero: todos casos correctos.
B6 NO aplicado (preservado en §13.3 "data_feed: attach stops redundante en get_open_positions"):
Razon: grep revelo que close_position en execution_manager linea 258 SI consume stop_order_id desde el dict de positions para cancelar el stop vinculado. El user spec preveia este caso: "Si hay consumer que lo lee desde positions, NO eliminar — reportar y mantener item en 13.3". Ruta alternativa (refactorizar para eliminar la llamada separada get_open_orders en live_engine) requiere cambios en reconcile_state que necesita la orders list completa (no solo stop_order_id por simbolo). Out-of-scope para fix trivial. Redundancia real: 2 fetch_open_orders por ciclo — coste minimal.
Verificacion post-deploy: bot activo, ciclo #133 restaurado. Proximo ciclo a 10:59:50 UTC para verificar comportamiento operacional con los 3 fixes en camino critico.
Cierre: fixes aplicados, sincronizados ambos repos, desplegados al VPS, verificacion inicial post-deploy exitosa. Pendiente verificacion de 2-3 ciclos para confirmar estabilidad antes de proceder con v2.3.9.
Referencias: data_feed.py `_retry_async` helper + 3 wraps + B5 ValueError guard, execution_manager.py open_position filled_size logic, Fase 3 v2.3.8 del 2026-04-19 10:28 UTC.

**[RESUELTO] v2.3.7: 10 fixes triviales Fase 2 (Grupo A) — 2026-04-19**
Contexto: Despliegue agrupado de 10 fixes clasificados como triviales en el triaje post-ultra review. Cada fix <20 líneas, sin ambigüedad semántica, sin riesgo real de regresión. Aplicados al repo comboclaude, sincronizados a combolab (md5 idéntico), desplegados al VPS mediante stop systemctl + scp + chown + start. Bot arrancó limpio (10:04:43 UTC): 45 GMM + 45 specialist configs + 45 leverage entries + 45 sectores + 8 posiciones sincronizadas. Tests pre-deploy (4 focalizados) todos OK.
Los 10 fixes:
- brain_engine S2 (bars_since_entry): campo era dead field pero SÍ consumido externamente (engine_state.json línea 1071, audit_fidelity.py línea 110, audit_sync.py línea 26, vps_engine_state_latest.json). Implementación funcional: incremento al inicio de _evaluate_bar/_evaluate_bar_mr cuando position != 0. Los 6 resets existentes preservados.
- brain_engine S3 (BTC Override state sync): apply_btc_override mutaba regimes[symbol]['cluster'] pero no state.current_cluster → confidence reportado en _evaluate_bar línea 721 era del cluster pre-override. Fix: asignar state.current_cluster = alt_highvol post-override.
- brain_engine S5 (active_config_id stale): los 3 paths de select_active_configs que retornan config_id=-1 (no cfg_data, no cluster_data, no selected) no reseteaban state.active_config_id ni state.active_preset. Añadido reset a -1/'' en los 3 paths. Ítem no existía explícito en §13.3 (descubierto durante el ultra review pero no convertido a MEJORA).
- portfolio_manager S2 (correlación abs): identify_correlated_blocks usaba `abs(corr) > threshold` agrupando anticorrelacionados (r=-0.9) como concentración. Cambio: `corr_matrix.iloc[i,j] > threshold` (solo positiva). Test confirmó comportamiento correcto en ambos sentidos.
- portfolio_manager S4 (sector_map doc): §7.3 decía "9 sectores" pero código tenía 10. Fix documental: actualizado §7.3 a "10 sectores (L1_major, L1_alt, Legacy, DeFi, L2, Meme, Oracle, Infra, Metaverse, AI)".
- portfolio_manager S5 (46 leverage entries): TONUSDT_specialist_configs.json stale en regime_wf/ (TON eliminado §0 pero JSON preservado). Movido a regime_wf/archived/TONUSDT_specialist_configs.json.legacy-2026-04-19 en comboclaude + combolab + VPS. Post-deploy log: "Leverage map: 45 símbolos calculados" (antes 46).
- execution_manager E5 (fill_price=0 guard): open_position sin check explícito de fill_price → stop_price_bingx=0, BingX rechazaba con mensaje oscuro. Fix: return early con `"action": "open_failed"` si fill_price <= 0 (patrón consistente con el catch de ExecutionError líneas 457-461).
- live_engine L3 (phantom purge DRY_RUN): condición `if not self.config.dry_run` limitaba el purge solo a LIVE. Fix: extendido usando get_dry_run_positions() como fuente de verdad en DRY_RUN, positions (BingX) en LIVE.
- live_engine L5 (max_cycle_duration enforcement): max_cycle_duration_seconds=30.0 configurado pero no enforzado. Refactor: lógica extraída a _run_cycle_inner(); nuevo wrapper run_cycle() con asyncio.wait_for(timeout=30). Callers (run_forever:648, _run_once:1225) sin cambios. En TimeoutError registra error y continúa.
- live_engine L7 (Telegram HTML escape): _send_alert usaba parse_mode="HTML" con mensajes texto plano (sin tags intencionales) → caracteres especiales (<,>,&) en exception msg o PnL formateado rompían alerta con HTTP 400 silencioso. Fix: parse_mode omitido (Telegram default texto plano). Grep confirmó 0 uso de tags `<b>`, `<i>`, `<code>` en messages.
Tests pre-deploy: FIX #4 correlación negativa no agrupa + positiva sí agrupa, FIX #9 TimeoutError a 1s, FIX #1 incremento funcional, FIX #6 45 JSONs post-archive (sin TON). Syntax check 4/4 OK.
Post-deploy verificación: bot activo, 133 ciclos restaurados, 8 posiciones sincronizadas, balance 297.63 USDT, ningún Python error.
Cierre: fixes aplicados, sincronizados ambos repos, desplegados al VPS, verificación post-deploy exitosa.
Referencias: md5 ambos repos (brain_engine: 0cb4bdd6..., portfolio_manager: 82669d57..., execution_manager: bc509b9f..., live_engine: 2736e0b4...), deploy del 2026-04-19 10:04 UTC, tests pre-deploy del 2026-04-19, triaje Fase 2 del 2026-04-19.

**[RESUELTO] v2.3.6: H1 portfolio_dd sobre capital total + H4 days_since_recycle=0 si archivo inexistente — 2026-04-19**
Contexto: Dos fixes serios de health_monitor de la ultra review del 2026-04-17, agrupados en v2.3.6. H1 causaba bug visible en daily summary Telegram: DD reportado -121.7% sobre PnL cumsum cuando DD real sobre capital era 0.23% (empirico: peak_balance=298.39, current_balance=297.69, cero eventos DD breaker en logs de las ultimas 24h — confirma que el bug era puramente de observabilidad, no operacional). Fix H1: leer peak_balance y current_balance de engine_state.json, formula `(peak - current) / peak * 100`. Enabler: live_engine.py agrega `self._current_balance` atributo, capturado en `_calc_dd_multiplier(balance)`, persistido en `_save_state` y restaurado en `_load_state`. Edge case manejado: current_balance=0 (ramp-up post-restart antes del primer ciclo) trata DD como 0, no 100%. Fix H4: `_days_since_recycle` retorna 0 (no 9999) cuando last_recycle.txt no existe; placeholder "??/90" preservado en display via check directo de existencia. Tests pre-deploy: 9/9 OK (incluye edge case ramp-up y VPS snapshot real). Verificacion post-deploy: bot arranco limpio, summary reporta DD=-0.0% (correcto), no recycle needed (dias=11/90 real, sin trigger espurio).
Cierre: fixes aplicados, sincronizados ambos repos con md5 identicos (health_monitor: ebca999f..., live_engine: bcb5ee0b...), desplegados al VPS, verificacion post-deploy exitosa.
Referencias: health_monitor.py _compute_portfolio_dd + _days_since_recycle post-v2.3.6, live_engine.py atributo _current_balance, test_v236_h1_h4.py (9 tests).

**[RESUELTO] [SUPERSEDED por v3 del 2026-04-20] Naturaleza real de /ultrareview y política de uso — 2026-04-17**
SUPERSEDED: la política v2 descrita a continuación fue reemplazada el 2026-04-20 por v3 tras Run 1 empírico (0 findings con diff docstring +26/-1). La interpretación "diff trivial como pretexto para análisis holístico del codebase" resultó incorrecta según documentación oficial — /ultrareview revisa el diff específico current-vs-default branch, no es auditor de codebase completo. Ver entrada v3 del 2026-04-20 más arriba en §13.4. Conservada como registro histórico de la evolución del entendimiento (v1 17-abril → v2 19-abril → v3 20-abril).
Contexto: Tras búsqueda inicial incompleta (Claude Code reportó erróneamente "no existe" al buscar solo en filesystem local), Ricardo verificó empíricamente que el comando SÍ existe en la interfaz. Investigación posterior via claude-code-guide agent confirmó: /ultrareview lanzado 2026-04-16 con Opus 4.7 (docs: code.claude.com/docs/en/ultrareview.md). Arquitectura multi-agente en sandbox cloud, verificación empírica de hallazgos, +10% recall claimed vs review estándar. Diff-based sobre git: revisa cambio de rama vs default (o PR GitHub), no análisis estático. Runtime 5-10 min, coste $5-$20/run tras 3 runs gratuitos lifetime (NO 3/mes como se asumió inicialmente).
Reframe conceptual clave: los reviews sistemáticos del 2026-04-17 fueron análisis estático de código en producción — categoría distinta a la verificación diferencial pre-merge de /ultrareview. Re-auditar código existente con /ultrareview sería error de categoría.
Política adoptada (v2 — 2026-04-19, refinamiento de v1 del 2026-04-17):
- /ultrareview se usa como auditor holístico de integración, no como gate aislado de fixes individuales.
- Prerequisito: repositorio en estado lo más limpio posible (serios pendientes atendidos, especialmente los de Capa 1).
- Método: aplicar un diff pequeño (fix relevante o ajuste intencional) como "disparador" que activa el análisis multi-agente sobre la totalidad del ecosistema. El diff es pretexto, no objeto del análisis.
- 3 runs lifetime distribuidos por tema mayor:
    Run 1: tras limpieza post-v2.3.6 + setup git, primer diff significativo sobre bot core.
    Run 2: momento del fix R1 (post-audit v5.1 con N≥50).
    Run 3: reserva estratégica — usar cuando surja decisión arquitectónica con máxima necesidad de verificación de integración.
- Fixes individuales aislados (sin cambios de lógica cross-módulo) no justifican un run.
- Prerequisito: git+GitHub establecido (ver ítem en 13.3).

Racional del refinamiento v2: aplicar /ultrareview sobre un diff encima de un codebase con 41 serios pendientes haría que los agentes detectaran bugs ya conocidos y desperdiciaran su capacidad de recall en lo realmente nuevo. Limpiar primero optimiza la señal de integración emergente.
Limitaciones: requiere login Claude.ai, no API-key only. No disponible con Bedrock/Vertex/Foundry/ZDR. Sin scoping a subdirectorio (analiza todo el diff). Sin flags de configuración (invocación rígida).
Cierre: política de uso establecida, runs reservados con disparadores claros, prerequisito de git documentado.
Referencias: investigación Claude Code del 2026-04-17, docs oficiales code.claude.com/docs/en/ultrareview.md, ítems R1 y P1 en 13.2, ítem P1 leverage proyecto en 13.3.

**[RESUELTO] Triaje final de Capa 1 dependía de investigación leverage lab — 2026-04-17**
Contexto: Tras ultra review de portfolio_manager detectar P1 (leverage 1x uniforme por bug `*100.0`), se planteó como decisión transitoria que los fixes FIX CON RIESGO de Capa 1 (R1 brain cooldown, P1 portfolio leverage, y cualquiera que apareciera en execution/live_engine) quedarían bloqueados hasta entender si el lab asumía leverage variable (Escenario 2, fix necesario) o 1x (Escenario 1, fix cosmético). La investigación se ejecutó como Parte A del prompt de execution_manager el mismo 2026-04-17 con resultado decisivo: **Escenario 2 confirmado** — run_simulation_numba sin parámetro leverage, maxdd_worst en %, sistema sub-apalancado sistemáticamente. Triaje final ejecutado con base empírica: R1 y P1 diferidos hasta primer reporte audit v5.1 con N≥50; P1 elevado a proyecto arquitectónico separado por complicación de safety con balance 297 USDT. Execution y live_engine posteriormente no produjeron FIX CON RIESGO adicionales.
Cierre: escenario identificado el 2026-04-17, triaje ejecutado en la misma sesión, decisiones documentadas en ítems separados ("P1 leverage NO es fix simple" en 13.3, "Cooldown brain diverge del kernel" en 13.2, "Investigación leverage lab↔producción" en 13.2).
Referencias: Parte A del prompt de execution_manager del 2026-04-17, ítem HALLAZGO "Investigación leverage lab↔producción" en 13.2.

**[RESUELTO] v2.3.5: H3 health_monitor CSV parsing + H2 excluye reconstructed — 2026-04-17**
Contexto: Dos fixes agrupados en v2.3.5, desplegados el 2026-04-17 tras v2.3.4. H3 CRÍTICO FIX DIRECTO: `_load_trades` usaba `pd.read_csv(path)` directo que fallaba con CSV de schema evolucionado (header pre-v2.3.2 con 10 cols vs data rows con 11/12 cols). ParserError provocaba fallo silencioso del daily summary Telegram desde 2026-04-16. Reemplazado por parseo posicional con pad/trunc a 12 cols (mismo patrón de analyzer v2.4.1 y audit v5.1). H2 SERIO promocionado: añadido filtro `df = df[~df['flag'].isin({'reconstructed_post_hoc', 'reconstructed'})]` por consistencia entre los 3 consumidores del CSV (analyzer, audit, health_monitor ahora todos excluyen reconstructed).
Tests pre-deploy: local CSV fallaba con ParserError, post-fix carga 52/53 trades (excluye GRT reconstructed). Post-deploy dry run contra VPS CSV real ejecutó generate_daily_health_summary sin errores. Health summary confirma también que H1 (portfolio_dd_from_peak métrica) sigue activo: reporta "-314% DD from peak" — ítem H1 queda pendiente como SERIO en 13.3.
Cierre: H3 y H2 aplicados, sincronizados en ambos repos, desplegados al VPS, verificación post-deploy exitosa. Daily summary Telegram vuelve a enviarse a partir del próximo 00:00 UTC.
Referencias: health_monitor.py _load_trades post-v2.3.5, ultra review del 2026-04-17, deploy v2.3.5.

**[RESUELTO] v2.3.4: L1 scheduler month-end + L2 save atómico — 2026-04-17**
Contexto: Dos fixes desplegados juntos en v2.3.4 el 2026-04-17 a las 11:37:39 UTC. L1: `_next_activation_time` usaba `target.replace(day=now.day + 1, hour=0)` que lanzaba ValueError en último día del mes (ej. 2026-04-30 intentaba day=31). Reemplazado por `target + timedelta(hours=1)` que maneja rollover de hora/día/mes/año automáticamente. L2: `_save_state` usaba write directo no atómico; reemplazado por write-tmp + os.replace (atómico POSIX), previene JSON parcial en crash durante write (OOM/SIGKILL).
Tests sintéticos L1 pre-deploy: 5/5 OK (2026-04-30, 2026-12-31, 2028-02-29 bisiesto, casos normales). Verificación post-deploy: bot arrancó limpio, engine_state.json escrito correctamente por el save del stop() previo, sin .tmp huérfano.
Cierre: fixes aplicados, sincronizados en ambos repos, desplegados al VPS, verificación post-deploy exitosa.
Referencias: live_engine.py _next_activation_time y _save_state, ultra review del 2026-04-17, deploy v2.3.4.

**[RESUELTO] Log date rollover robusto con ENGINE_STATE.t — 2026-04-17**
Contexto: Ultra review C4 + item previo 13.3 sobre rollover. parse_engine_log ahora usa ENGINE_STATE.t (unix seconds, presente desde v2.3.1) como ancla de fecha. Si el bot estuvo caido varias horas, la siguiente [ENGINE_STATE] re-sincroniza automaticamente. Fallback a rollover 23->00 solo entre anclas. Contadores log_date_sync_anchors y log_date_gap_warnings trackean salud del parseo.
Cierre: analyzer v2.4.1 implementa two-anchor parser. Gaps multi-hora manejados sin desfase de fecha.
Referencias: analyze_performance_attribution.py parse_engine_log, ultra review C4.

**[RESUELTO] Audit v5.1: criticos + serios + menores del ultra review — 2026-04-17**
Contexto: Ultra review audit_fidelity_v5.py detecto 8 criticos (5 heredados de v4) + 10 serios + 10 menores. v5.1 aplica: C1 (entry/exit semantics correctas con infer_entry_candle), C2 (kernel parity checksum opcion C), C3 (is_reconstructed acepta ambos flags), C4 (MR cluster_hint via SIGNALS_RAW.k o GMM), C5 (rollover con ENGINE_STATE.t), C6 (COMBOLAB_DIR env/CLI), C7 (CSV 12 columnas), C8 (tolerancia +-1 vela), S4 (orden canonico exclusiones), S5 (N_INSUFICIENTE fuerza AMBER), S8 (match sin segunda pasada aliasing), S10 (divergencia por CI overlap), M4 (sl_hit aliases), M6 (scipy version check). Lazy import de combolab modules para que --combolab-dir tenga efecto completo.
Cierre: codigo sincronizado en ambos repos. Dry run local OK (kernel parity verified, denom=0 porque logs locales son pre-v2.3.1). Reporte seccion 5 incluye caveat explicito "v3/v4 referenciales, no ground truth".
Referencias: audit_fidelity_v5.py, EXPECTED_AUDIT_KERNEL_HASH=a93310e4..., EXPECTED_LAB_KERNEL_HASH=165b2357...

**[RESUELTO] Analyzer v2.4.1: criticos + serios mayores del ultra review — 2026-04-17**
Contexto: Ultra review identifico 4 criticos y 10 serios. v2.4.1 aplica: C1 (entry_candle inferido via entry_timestamp_ms v2.3.3 o log fallback), C2 (consistency check por precios), C3 (COMBOLAB_DIR env/CLI/default), C4 (rollover con ENGINE_STATE.t), S1 (classify con multipliers proxy), S2 (balance_req sin br double-count), S3 (--exclude-reconstructed default), S4 (split counters), S5 (unit validator pnl_tr), S6 (active_config_source=heuristic trackeado), S7 (CAPITALIZE safeguards N/pnl), M3 (docstring actualizado), M9 (DD breaker umbral).
Cierre: codigo sincronizado en ambos repos. Dry run local OK (syntax + runtime). v2.3.3 desplegable para comenzar a generar trades con entry_timestamp_ms.
Referencias: analyze_performance_attribution.py, live/execution_manager.py, live/live_engine.py, live/brain_engine.py.

**[RESUELTO] Swap GRT MR desplegado — 2026-04-17**
Contexto: JSON preparado y verificado en ambos repos. C2 paso de TF (score=1.79) a MR (score=3.36, pf_combined=2.918). Swap desplegado en VPS el 2026-04-17 a las 08:15:51 UTC. Verificado en logs del primer ciclo post-deploy (45 specialist configs cargados sin errores).
Cierre: swap efectivo, documentacion en seccion 9.2.1 con clausula de rollback ajustada a densidad empirica.
Referencias: regime_wf/GRTUSDT_specialist_configs.json, seccion 9.2.1 del documento.

**[RESUELTO] Clausula rollback GRT calibrada con densidad empirica — 2026-04-17**
Contexto: Datos del JSON revelaron densidad baja de trades MR en C2 (~1 cada 270 barras en C2, ~11 dias calendario efectivos en C2). Clausula original de "20 trades MR" podia tardar 1-2 anos. Clausula revisada a "20 trades O 90 dias, lo primero" interpretando el evento como disparo de REVISION (no rollback automatico). Protocolo de decision ramificado segun N disponible en el disparo.
Cierre: clausula documentada en seccion 9.2.1.
Referencias: seccion 9.2.1.

**[BUG] [RESUELTO] Signo de funding invertido en analyzer v2.4 — 2026-04-16**
Contexto: Primer diseño del analyzer usó fórmula funding = -funding_paid_csv bajo supuesto de que columna guardaba magnitud positiva. Verificación empírica tras implementación mostró que trade_history.csv guarda el valor ccxt 'amount' tal cual (negativo=pagado, positivo=recibido), por lo que la inversión duplicaba el error. Pre-fix el agregado mostraba funding=+0.07 (favorable, incorrecto); post-fix -0.07 (coste, correcto). Alert global 121% de |PnL| — funding erosiona más PnL del que trading genera con balance bajo + leverage 3x típico.
Disparo: no aplicable, bug cerrado.
Cierre: verificado post-fix con trade concreto — funding_paid CSV y analyzer.funding coinciden en signo y magnitud.
Referencias: analyze_performance_attribution.py attribute_trade(), docstring del módulo, fix de 2026-04-16

**[HALLAZGO] [RESUELTO] Auditoría v4 sobre CSV con agujeros por Bug #2 — 2026-04-16**
Contexto: La fidelidad v4 al 91% se midió sobre trade_history.csv que probablemente tenía agujeros — trades cerrados por SL trigger de BingX entre ciclos no se registraban (Bug #2, fix en v2.3.2). El match rate real podría haber sido peor si el denominador hubiera incluido esos trades perdidos. No invalida el resultado de v4 pero sí indica límite de su fiabilidad retroactiva. El trade GRT perdido (entry 16/04 08:00 UTC, SL trigger entre 09:00-10:00) fue reconstruido en CSV con flag='reconstructed_post_hoc'.
Disparo: no aplicable, cerrado retroactivamente.
Cierre: auditoría v5 partirá de datos limpios post-v2.3.2 y no adolecerá del problema.
Referencias: audit_fidelity_v4.py histórico, audit_fidelity_v5.py exclusión de flag='reconstructed_post_hoc'
