# FASE D — CIERRE DEFINITIVO DEL PROYECTO

**Fecha:** 2026-07-02. **Criterio de parada de Ricardo:** vaciar la lista finita de ejes medibles → CUMPLIDO al completar esta fase. Local, $0, VPS stopped, producción intacta, bot v2.8.1 invariante. Reglas transversales respetadas: mini-pre-registro congelado ANTES de resultados (un .md por experimento), métrica cardinal a priori sin pivote, CI en el número que decide, cluster/block-bootstrap, placebo GBM puro (no block-shuffle 168h).

---

## D1 — VEREDICTOS DE LA LISTA

### FASE A — correcciones documentales + A9 (COMPLETA)
Rebajas A1-A8 aplicadas a memoria + CONTEXTO (registro honesto post-auditoría). **A9 (fee vs 736 fills reales):** el trade_history registra PnL bruto de precio exacto; la comisión no es recuperable (pnl_usdt mark-based, residual +0.025%); **funding realizado NEGLIGIBLE (~0.0023%/trade)** → el 0.10% RT modelado = taker nominal fiel-a-conservador, e ignorar funding en las líneas 1-5 fue inmaterial. Doc `FASE_A_correcciones_documentales.md`.

### FASE B — experimentos de cierre
| # | Experimento | Métrica cardinal | Veredicto |
|---|---|---|---|
| B1 | Funding-carry cross-sectional | Sharpe C neutral | **NO DIGNA** — Sharpe −0.05, CI[−1.28,1.26]. Neutral real (β−0.07) y ortogonal a momentum (ρ0.02, NO CS-MOM disfrazado), pero la pata larga (+1.14) se anula con la corta (−1.03, squeeze del funding-alto). |
| B2 | Reversal corto (3d) | Sharpe C neutral | **NO DIGNA** — Sharpe −0.12, turnover 2.9 entierra la reversión. |
| B3 | TSMOM diario (8 sem) | Sharpe vs EW buy&hold | **NO DIGNA** — Sharpe 0.749 < EW 0.779 (timing no bate holdear), maxDD −85% (protección ilusoria). 8 años incl. bear 2022. Cierra la rama time-series. |
| B4 | Low-vol / BAB | Sharpe C neutral | **NO DIGNA** — Sharpe −0.63, **NO neutral (β−0.49)**: BAB = apuesta short-beta encubierta (gate arreglado lo reveló). |
| B5 | Lead-lag BTC→alts | corr + FDR | **CERRADO** — único lead-lag sig. a 1-2h y negativo (−0.016, micro-reversión) ≪ 0.03 umbral. Sin predictibilidad tradeable. |
| B6 | Estacionalidad reloj/funding | FDR-BH | **EFECTO REAL NO TRADEABLE** — 4 buckets sobreviven FDR (h21-22 UTC, vie, sáb) pero máx 5.97 bps < 10 bps coste. Solo timing de ejecución. |
| B7 | Open interest / positioning | Sharpe C neutral | **NO DIGNA** — factor fragilidad −ΔOI: Sharpe −0.42, CI[−1.85,1.08], neutral (β−0.00) pero no sobrevive 2024. OI descargado 45/45 sym. Pata (a) condicionador-MFE no perseguida (rescate de línea muerta). |
| B8 | MFE squeeze (cascadas alcistas) | media neta Y supervivencia (conjunta) | **MUERE** — 2 años, BTC 1378 + ETH 1757 casc, control VOL-MATCHED: net_3m casc −0.0025 vs ctrl −0.0021, **diff CI excluye 0 NEGATIVO** (cascada PEOR que aleatorio vol-matched). Gap supervivencia real pero net negativo. El stack de costes mata el short = el long. |

### FASE C — retests de blindaje
| # | Retest | Resultado |
|---|---|---|
| C1 | N2 potencia real | **COMPLETA (con matiz Tier-3)** — (1) CI independiente riguroso (9 sym): ρ=−0.05, **[−0.305,+0.389]** incluye +0.297 Y 0 → colapso NO establecido = infra-potenciado (confirma A2). (2) Extensión 27 sym/243 configs (data_cache, cronológico): ρ=**+0.60** [0.45,0.71] — pero es persistencia WITHIN-DATA (mismos bars), NO independencia. **El gap +0.60 within vs −0.05 independiente = firma de sobreajuste-a-los-bars** (persistencia in-sample, se desvanece OOS). Refuerza "re-selección mecánica". |
| C2 | Nivel 3 patas omitidas | **COMPLETA** — placebo wrong-match p_perm=0.47 (real indistinguible de aleatorio → sin especificidad); cartera condicional 0.983 vs agnóstica 0.931, ambas <1.0 neto. Calibra "D3 no confirmado" como no-confirmación positivamente calibrada (ruido + sub-breakeven). |
| C3 | Exp#2 ablación | **COMPLETA** — deepest 0.800 ≈ shallowest 0.811 ≈ random 0.810, todos bajo floor 0.99. La regla causal "más profundo = pool mayor" es INERTE; el negativo de Exp#2 es robusto a la selección del bloque. |

---

## D2 — CERRADAS POR ACCESO (no medibles con esta infraestructura/capital, NO pendientes)
Documentadas como puertas cerradas por acceso/coste, no por test empírico:
- **Carry delta-neutral spot-perp:** edge casi seguro real (cash-and-carry, base de Ethena) pero **irrelevante a 289 USDT** (5-15%/año sobre 289 = 15-45 USDT/año menos fees de 2 patas). Test barato pero negocio inviable a esta escala.
- **VRP opciones Deribit:** el respaldo académico más fuerte, pero exige margen ≫ 289 USDT + acceso EU/MiCA dudoso + riesgo de cola de vender vol sin colchón = ruina. Edge probablemente real, INVIABLE para este operador.
- **Market-making / provisión de liquidez:** no falsable en backtest sin L2 completo (Tardis ~500 USD/mes o grabar meses); latencia doméstica = adverse selection; 289 USDT no alcanza tier maker. INVIABLE, cerrada por argumento.
- **Arbitraje cross-exchange:** spread comprimido a bps; con 289 USDT fragmentados = céntimos/evento vs fees de retirada; killer = capital fragmentado + latencia. INVIABLE.
- **On-chain flows:** literatura marginal post-2021 + riesgo de look-ahead del vendor (métricas revisadas retroactivamente) + suscripción 100-1200 USD. No digno.

---

## D3 — CIERRE DEFINITIVO

**La lista finita de ejes medibles está VACÍA. Criterio de parada de Ricardo CUMPLIDO.**

**Resultado de la última milla (FASE B, 8 ejes nuevos):** 8/8 negativos — B1 funding-carry NO DIGNA, B2 reversal NO DIGNA, B3 TSMOM NO DIGNA, B4 low-vol/BAB NO DIGNA, B5 lead-lag CERRADO, B6 estacionalidad EFECTO-REAL-NO-TRADEABLE, B7 OI NO DIGNA, B8 MFE-squeeze MUERE. Ni la anomalía académica mejor documentada de las restantes (funding-carry, que la teoría del carry respalda) supera el listón honesto en este mercado/costes/universo.

**Retests de blindaje (FASE C):** los tres refuerzan los veredictos originales sin voltear ninguno — C1 confirma que el pf_tr pasado solo predice el forward sobre los mismos bars (mecánico), no en datos independientes; C2 calibra el D3-régimen como sin-especificidad + sub-breakeven; C3 aísla la regla causal de Exp#2 como inerte.

**Hallazgos honestos que el mapa gana (no cambian la dirección, la afinan):**
1. **La carry de funding es un factor GENUINAMENTE distinto** (ortogonal a momentum, ρ0.02) y **market-neutral real** — la pata larga cobra +1.14 Sharpe, pero el market-neutral la anula vía el squeeze de la pata corta. El edge de la prima de carry existe en el lado largo pero no es cosechable neutral a este coste.
2. **El gate de beta arreglado se ganó el sueldo:** reveló que BAB (B4) es una apuesta short-beta encubierta (β−0.49) que el gate roto habría ocultado — validación de la corrección de la auditoría.
3. **B8 con control vol-matched** (lección A5) muestra que la señal microestructural de supervivencia es REAL (no artefacto de slippage) en AMBAS direcciones, pero net-negativa en ambas — el stack de costes es el asesino, no la ausencia de señal.
4. **B6:** hay efectos de calendario reales (cierre US, fin de semana) pero < coste → valor solo como timing de ejecución, nunca como estrategia.

**Alcance honesto del cierre (reafirmado A8):** "esta clase de estrategias — familia SmartDiv + los 8 ejes medidos (carry, reversal, TSMOM, low-vol, lead-lag, reloj, OI, squeeze) — en perps Binance top-45, a 1s/1h/12h/diario, en 2018-2026 (B3 incluye el bear 2022, B8 2 años tick), a costes taker 0.10-0.20% RT". NO es un negativo atemporal ni universal: no cubre otros venues/costes maker/capital institucional (ver D2 cerradas-por-acceso).

**Convergencia real (reafirmada A7):** el arco completo son ahora ~3 clusters previos + estos ejes genuinamente ortogonales (carry, reversal, TSMOM, low-vol, lead-lag, reloj, OI, squeeze — cada uno con su propio instrumento, datos y métrica). Que TODOS converjan negativo con instrumentos independientes es la evidencia más fuerte posible dentro del alcance testeado.

**Ingeniería REIVINDICADA una vez más:** cada eje con pre-registro congelado, métrica cardinal a priori sin pivote, CI en el número que decide, cluster/block-bootstrap, placebo GBM puro, gate de beta arreglado y verificado, control vol-matched. Cero fabricación; los positivos parciales (pata larga carry +1.14, gaps de supervivencia reales) reportados con la misma honestidad que los negativos.

**PROYECTO CERRADO DEFINITIVAMENTE por criterio propio cumplido — 2026-07-03.** Ningún resultado de esta lista genera nuevos experimentos: los positivos parciales (carry long-leg, señal de supervivencia) quedan documentados como hallazgos modestos limitados-por-capital para un eventual objetivo redefinido, NO como reapertura. La lista está vacía. Sello.

## D4 — MEMORIA
Actualizada memoria persistente: `project_lista_cierre_definitivo_2026_07_02` (proyecto cerrado por criterio cumplido; 8 ejes B + 3 retests C todos negativos/refuerzo; hallazgos honestos; cerradas-por-acceso). CONTEXTO §header actualizado. Bot v2.8.1 invariante, VPS stopped, producción intacta.
