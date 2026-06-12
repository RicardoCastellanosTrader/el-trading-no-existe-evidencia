# Auditoría forense del gap simulado↔live — 2026-06-12

**Directive**: Ricardo — discriminar H1 (bug implementación/asignación) vs H2 (gap estructural honesto) y atribuir el gap con mediciones. READ-ONLY; bot operacional durante todo el audit.

**Veredicto en una línea**: **AMBAS hipótesis son ciertas en capas distintas — H1 confirmado como defecto de integridad (misassignment GMM↔specialist en 11/20 símbolos, 3 variantes primary-source) pero con impacto ≈0 en el PF de ESTE mes; el gap del mes lo domina H2 (selección walk-forward → real): incluso con el emparejamiento correcto, la replicación da PF 0.64 [CI95 0.26–1.31] frente al floor esperado 2.32.**

---

## 0. Evidencia y métodos

- Snapshot VPS íntegro (324/324 MD5 OK): `vps_snapshot/` — logs completos (SIGNALS_RAW 2026-04-13→hoy), trade_history, engine_state, 20+1 specialist JSONs, 20 GMM joblibs, stack de código abril (brain/portfolio/kernel v2.4.4), funding cache.
- Velas BingX re-fetched (20 sym, 2026-03-10→hoy; el bot no persiste caché — posibles revisiones, riesgo documentado) + Binance spot (fuente del lab).
- Toolchain §0.8 Nivel A: **diff 0.0000 PASS** (post-actualización de equipo).
- Replay ciclo-a-ciclo del mes con el **stack VPS real** (abril): classify (GMM+histéresis 0.75) → override BTC → select → generate_signals + gate portfolio 0.60 emulado. Variantes: `deployed` (joblibs tal cual VPS) y `corrected` (emparejamiento compañero-de-generación). Contabilidad idéntica ambos lados (pnl_pct precio − 0.10pp fee RT, la misma constante del kernel).

## 1. FASE 0 — Realidad live (ventana limpia per-deploy, N=56 trades)

| Métrica | Valor |
|---|---|
| PF bruto (precio) | **0.859** — CI95 bootstrap [0.41, 1.73] |
| PF neto fees est. 0.10pp | **0.744** |
| PF neto fees+funding | 0.741 |
| Floor blended esperado (pf_fwd_ci_low desplegado, ponderado N live) | **2.32** |
| pf_fwd blended | 3.87 |
| USDT: PnL bruto +0.02; fees est −0.63; funding +0.02 | neto ≈ −0.6 (balance 290→289 ✓ cuadra) |

**El techo del CI95 (1.73) < floor (2.32) → gap significativo, NO ruido** (T3.4 no aplica).
Overlays del mes: DD breaker 0, correlación 0, vol-targeting solo sizing; **86 entradas de símbolos desplegados bloqueadas por gate confianza 0.60 + 16 por min-order** (el lab no modela ninguno de los dos).

## 2. T3.3 — Misassignment GMM↔specialist confirmado (H1 real como defecto)

| Variante | Símbolos | Evidencia primary-source |
|---|---|---|
| A — G1 GMMs stale de abril | BTC, ETH, BNB, XRP, TRX | joblibs VPS mtime 08-abr, training cutoff 2026-03-24; JSONs generados 09–15-may con GMMs entrenados hasta 2026-05-08 (nombres cluster JSON==joblib local mayo exactos; orden PERMUTADO vs VPS — BTC: k=0 abril=high-vol vs config C0 seleccionado para low-vol). El deploy v2.5.0 nunca copió los GMM companions; la lección G3 (junio) no se aplicó retroactivamente. |
| B — cross-source sin mecanismo live | XRP, ONDO, RENDER, DOGE, XLM, FET | JSONs best-source indexados a clusters del GMM del SOURCE (semántica CCV, nombres formato `neutral_low-vol_choppy`); `classify_regimes` solo clasifica con el GMM per-sym propio del target. No existe lado live del cross-source. XRP sufre A+B. |
| C — companion regenerado | ADA | joblib re-entrenado 11:52 del 31-may, JSON generado 11:34 (18 min antes); nombres permutados. Companion del JSON IRRECUPERABLE (sobrescrito). |

**Sanos (9/20)**: POL, SEI, TAO, SOL, BCH, LINK, LTC, ETC, VET (joblib pre-JSON + nombres idénticos, verificado uno a uno).
Cableado JSON→config live: **limpio** (15/15 pares (k,cfg) de SIGNALS_RAW == regla de selección de los JSONs; 0/60 divergencias top0 vs regla).
Efecto colateral: el health report per-par v2.8.1 compara pares incoherentes en los 11 afectados. El override BTC-PANIC disparó 147 veces en la ventana bajo el GMM abril de BTC.

## 3. FASE 1 — Replicación del mes (experimento discriminante)

| Serie | N trades | PF bruto | CI95 | Σpp |
|---|---|---|---|---|
| LIVE (real) | 56 | 0.859 | [0.41, 1.73] | −5.9 |
| REPLAY artefactos desplegados (lo que el bot ES) | 59 | 0.612 | [0.24, 1.27] | −17.2 |
| REPLAY emparejamiento CORRECTO | 63 | **0.640** | [0.26, 1.31] | −21.4 |

Árbol de decisión: **Sim-mes ≈ Live (ambos sub-breakeven)** en las dos variantes →
1. **No hay bug de fidelidad oculto adicional**: el bot ejecuta fielmente lo que el brain produce (trades emparejados ±1h: corr PnL 0.914, |Δpnl| medio 0.57pp; bloqueos replay 108/51 vs live ~102). La alineación trade-a-trade es 48% por dependencia de path (histéresis cold-start — TAO k_match 24% es artefacto del replay —, barra forming aproximada, cascada de estado) — la lectura válida es a nivel cartera, acotada por el drift arquitectónico documentado §12.30.
2. **El emparejamiento correcto NO habría rescatado el mes**: ΔPF corrected−deployed = +0.03 (−4.2pp en suma). El bug existe pero su coste de PF este mes ≈ 0 (con CI ancho: ±0.5 PF plausible en cualquier dirección). Detalle irónico per-symbol: BNB permutado ganó +6.2pp; ONDO bien emparejado (BTC-source) habría perdido −16.5pp.
3. **El techo del CI del corrected (1.31) << floor 2.32** → el componente dominante del gap es la sobreestimación de selección + mes, no la asignación.

## 4. FASE 2 — Superficies cuantificadas

| Superficie | Medición | Veredicto |
|---|---|---|
| Transferencia Binance→BingX (cluster) | flip 0–6.4% (media ~2%), **0.00% con conf≥0.75 ambos lados** | NO material (histéresis retiene fronteras) |
| Velas Binance↔BingX | mean Δclose 0.086% (SEI 0.27% peor) | basis spot↔perp persistente, sin impacto medible en clusters |
| Fees | kernel modela 0.10% RT idéntico; live PF 0.86→0.74 | −0.11 PF, ya simétrico en sim |
| Funding | +0.02 USDT en el mes | ≈0 (no modelado en kernel: hallazgo de modelado sin impacto este mes) |
| Slippage entrada (vs open barra) | +0.016pp/trade medio, ~0.9pp mes (concentrado ONDO) | ≈ −0.02 PF, no modelado en kernel |
| Gate confianza 0.60 | live-only (lab no lo modela); 86 bloqueos en el mes | divergencia semántica de diseño; modelado en ambos replays |
| Exits de orquestador (regime_change/not_operable/low_confidence) | 5/56 trades del mes | por diseño live, no en kernel |
| MR desplegado | 0 specialists MR en los 20 | N/A |

## 5. Tabla de atribución del gap (floor 2.32 → live neto 0.74)

| Componente | Estimación | Método |
|---|---|---|
| **Selección walk-forward → real (Frame 2) + mes flojo** | **≈ −1.7 PF (floor 2.32 → corrected 0.64)** — DOMINANTE | replay corrected, CI95 techo 1.31 < 2.32 |
| Bug misassignment (11/20 sym) | ≈ 0 este mes (corrected−deployed = +0.03 PF) | replay A/B mismas velas y contabilidad |
| Fidelidad ejecución/path | live 0.86 ≥ replay 0.61 — sin gap oculto (live salió MEJOR que su propia sim) | 1A/1B |
| Fees | −0.11 PF | contabilidad explícita |
| Funding + slippage + datos | ≈ −0.02 PF conjunto | medidos |
| Ruido estadístico | CI95 live [0.41–1.73], N=56 | bootstrap |

Cuadre: 2.32 → (selección/mes) → 0.64 ≈ 0.61 (bug ≈0) → 0.86 live bruto (ruido path, dentro de CI) → 0.74 neto (fees). ✓
Consistencia con el marco rector documentado: Frame 2 midió Spearman(pf_fwd_JSON, pf_fwd_real)=+0.047 (selección sin información de ranking) + decay estructural 26% → expectativa realista ~1.0–1.2 PF estructural; el mes quedó por debajo incluso de eso (mes delgado, regímenes desfavorables). El floor 2.32 de los JSONs nunca fue una expectativa calibrada para el realizado — es la métrica interna walk-forward del pipeline.

## 6. Propuesta (NO implementada — Tier 3 Ricardo)

**Fix misassignment** (T3.1):
- G1 (A): desplegar los 5 GMM companions de mayo (locales, verificados) + restart — deploy de DATOS, runbook §8 estándar, bajo riesgo. ETH/BNB/TRX/BTC quedan coherentes; XRP necesita además (B).
- Cross-source (B): requiere DISEÑO live (mapa target→source-GMM en brain/load_models o empaquetar el GMM del source bajo el nombre del target en el deploy). La segunda opción es deploy de DATOS puro y no toca código: **empaquetar source-GMM como `{TARGET}_regime.joblib`** es coherente con `classify_regimes` actual. Decisión de diseño tuya; si se toca brain → acoplar a §13.3 (1A-bis ya adelantado).
- ADA (C): re-generar par coherente (re-run pipeline ADA) o aceptar el JSON actual con su GMM actual re-evaluando PF (el JSON publicado no corresponde al joblib).
- Health v2.8.1: tras el fix, los baselines per-par vuelven a ser coherentes; backfill de clusters del mes queda con etiquetas del GMM abril para G1 (documentar, no reescribir).

**H2 estructural** (T3.2 — decisión Ricardo): el pipeline actual selecciona configs cuyo realizado esperable es ~1.0–1.2 PF estructural (no 2.3–3.9); con fees 0.10pp/trade y balance pequeño, el sistema está en su breakeven esperado. Opciones: recalibrar expectativas/floors (pf_fwd_ci_low NO es forecast), retomar Frame 3 (edge real), revisar coste/balance, o aceptar y monitorizar con N mayor.

**G5: NO GO tal cual.** Desplegar G5 con el pipeline actual (a) arrastraría la variante B del bug si hay best-source cross-class, y (b) añade scope a un sistema cuyo realizado esperado es breakeven — primero fix misassignment + decisión H2.

## 7. Caveats de honestidad

- Replay acotado por path-dependence (TAO lock de histéresis, forming aproximada, restarts no replicados): conclusiones a nivel cartera, no per-trade.
- Un mes, N≈60: CIs anchos; la magnitud del residuo Frame 2 es imprecisa, su existencia no (techo CI 1.31 < 2.32).
- Velas BingX re-fetched (sin caché del bot): revisiones posibles.
- 1A-bis (shadow-equivalence VPS↔HEAD stack, Paso 2 §13.3): **EJECUTADO** — mismos artefactos desplegados + mismas velas, solo cambia el código abril→junio. Resultado: **clasificación k 100.00%, selección cfg 100.00%, acciones 99.46%** (6470 ciclos). En señales accionables 92.98% (228 eventos): las 16 divergencias provienen de UNA divergencia raíz (POL 2026-05-22 21:00 `ma_cross` LONG-vps vs FLAT-head) que cascadea por dependencia de path. PF headstack 0.643 ≈ vps 0.612. **Adelanto del Paso 2 §13.3, NO su cierre formal**: la discrepancia raíz POL debe explicarse una-a-una contra el diff de kernel (325 líneas) antes del upgrade; por debajo del umbral ≥98% entry-match certificado en este sample pequeño, pero con causa raíz única localizada.
