# PRE-REGISTRO CONGELADO — Atribución por Componentes, Experimento #2: "Order Block / barrido de liquidez"

**Fecha congelación:** 2026-06-26 · **Estado:** FROZEN (diseño a-priori; T3.1-Exp2 pendiente OK Ricardo ANTES del barrido 45) · **Rama:** `atribucion-componentes`.

> **Congelado ANTES de mirar resultados.** Aquí el sobreajuste NO entra por optimizar parámetros (no hay versión optimizada — el componente no existía en el código) sino por **tunear el DISEÑO**. Por eso cada decisión de formalización (qué es bloque / escapada / barrido) + cada parámetro (k, W, R, L, H) se fija POR LÓGICA y A PRIORI en este documento. Cambiar la definición tras ver resultados = Ruta 1 = invalida el pre-registro.

---

## 0. Por qué CONSTRUIR (no medir)

Hallazgo cardinal Exp#1: el order block **NO EXISTE en el código** (0 hits `order_block/FVG/liquidity/displacement/stop-hunt/mecha/imbalance`, verificado Python + Pine). El sistema automatizado fue siempre **zonas multi-MA + Heikin-Ashi + SmartDiv**. El order block era de la estrategia MANUAL de Ricardo; nunca se implementó → el cruce de medias (Tenkan/HA) era el GATILLO (Exp#1: gatillo sin edge), no la fuente. La hipótesis causal del **barrido de liquidez** (liquidez forzada acumulada en niveles, barrida antes de revertir) es la **única Ruta 2 no probada**. Las 4 líneas negativas (re-selección + capacidad ρ≈0.047 + D3 + medias/gatillo) son todas Ruta 1 → no la cubren. Exp#2 = **kernel NUEVO**, separado, no muta nada productivo.

**Expectativa calibrada (honestidad):** base = 5º "no" probable. Construir NO es apostar a que funciona; es probar honestamente la única causa no probada, dispuestos al "no" (que sería el MÁS informativo: cierra la pregunta del proyecto). Build caro, backtest barato.

---

## 1. El componente (B.1) — definición causal

**Order Block alcista** = la última vela **bajista** inmediatamente antes de una **escapada alcista decisiva**. Su rango `[low_b, high_b]` = la zona (liquidez de órdenes dejada ahí). Tras la escapada, el precio RETORNA al bloque → entrada límite pasiva en el borde → reversión esperada. Simétrico bajista. Sin medias-como-señal, sin TF, sin divergencias.

**Variante "barrido" (secundaria, diagnóstica):** OB cuyo bloque además **barrió liquidez** justo antes (su low/high = extremo de las últimas P barras = stop-hunt) y cerró de vuelta. Prueba si la precondición de barrido refina el edge.

---

## 2. Parámetros de DISEÑO — LÓGICOS, FIJOS, CONGELADOS A PRIORI (la línea roja)

| Símbolo | Significado | Valor PRIMARIO (lógico) | Robustez (control 3) |
|---|---|---|---|
| **k** | escapada decisiva: `rango_ruptura > k·ATR(14)[t-1]` | **2.0** | {1.5, 2.0, 2.5} |
| **W** | ventana de retorno para llenar el límite | **50 barras** | {30, 50, 80} |
| **R_mult** | objetivo = entry + R·riesgo | **2.0** | {1.5, 2.0, 3.0} |
| **L_block** | lookback máx. para hallar la vela-bloque opuesta | **10 barras** | fijo |
| **H_max** | time-stop: salida forzada si no toca TP/SL | **200 barras** | fijo |
| **ATR** | `lab.calc_atr(high,low,close,14)` — REUSADO del sistema (no nuevo DOF) | 14 | fijo |
| **comisión** | round-trip | **0.10%** | fijo |
| **P_sweep** | (variante barrido) extremo de las últimas P barras | **20** | fijo |

**Decisiones de formalización congeladas (no se re-eligen tras ver datos):**
- **Bloque** = vela opuesta más reciente en `[t-L_block, t-1]` (alcista OB → última bajista; bajista OB → última alcista). Definición canónica, sin parámetro libre.
- **Escapada decisiva (alcista)** en vela t: `close[t]>open[t]` **Y** `(high[t]-low[t]) > k·ATR[t-1]` **Y** `close[t] > high_b` (cierra más allá del bloque). Simétrico bajista (`close[t]<low_b`).
- **Zona** = `[low_b, high_b]` (rango completo). **Borde proximal (entrada)** = `high_b` (alcista, el precio vuelve DESDE arriba) / `low_b` (bajista). El más conservador (basta tocar el borde).
- **Riesgo** R = rango del bloque = `high_b - low_b`. **TP** = `entry + R_mult·R` (alcista) / `entry - R_mult·R` (bajista).
- **Stop = basado en CIERRE** (no mecha): alcista sale si `close[u] < low_b`; bajista si `close[u] > high_b`. (Coherente con la hipótesis: el bloque se invalida si el precio CIERRA fuera.)
- **Llenado (fill)**: límite pasivo en el borde proximal, válido en `[t+1, t+W]`. Alcista llena en barra s cuando `low[s] ≤ high_b` (precio retorna al borde), a precio `high_b`. Primer toque llena.
- **Gestión (tras fill, barra u desde s)**, prioridad congelada: (1) TP intrabar si `high[u]≥TP` → sale a TP; (2) si no, stop si `close[u]` fuera del bloque → sale a `close[u]`; (3) si ni uno ni otro en H_max barras → time-stop a `close[s+H_max]`.
- **Unidad de medida = POR-SETUP INDEPENDIENTE**: cada OB activado → un trade candidato independiente (llena o expira); se permiten solapados. PF = sobre TODOS los OB llenados. Esto mide el EDGE DEL SETUP directamente, sin confundir con gestión de cartera/posición secuencial. (Difiere de Exp#1, que usó el kernel secuencial single-position; para un setup discreto la unidad natural es el setup.)
- **Lado**: bullish + bearish (both).

**NO hay versión "optimizada" existente** → el contraste lógico-vs-optimizado de Exp#1 NO aplica. El único overfit posible es de DISEÑO → controlado por (i) congelar todo arriba a priori y (ii) la robustez del control 3.

---

## 3. LOOK-AHEAD — control cardinal, garantizado por construcción + test explícito

- El bloque se identifica en la barra de ruptura t usando **solo datos ≤ t** (vela-bloque anterior; ATR[t-1]; ruptura confirmada al cierre de t). Entrada/stop/TP ocurren **estrictamente en barras > t**.
- **PROHIBIDO** condicionar la validez del bloque a su resultado posterior. El detector marca el bloque en su FORMACIÓN; lo que pase después es el TEST, no la definición.
- **Test explícito de no-look-ahead (prefix-invariance):** correr el detector sobre `serie[0:T]` y sobre la serie completa; **todo trade con `exit_bar < T-1` debe ser BIT-IDÉNTICO** entre ambos (truncar el futuro no altera detecciones pasadas). Si difiere → look-ahead → PARAR (T3.2-Exp2). Es el gate de fidelidad de Exp#2.

---

## 4. Los 4 controles (congelados)

1. **Edge OOS**: `pf_fwd` GLOBAL (agregado cross-cluster, forward holdout) neto 0.10%, **CI bootstrap por-símbolo que excluya 1.0**. Benchmark = breakeven 1.0 + noise floor del control 2.
2. **Random walk — especialmente potente aquí**: el OB corre sobre las 6 series placebo (GBM + block-shuffle). Un ruido **no tiene liquidez real acumulada que barrer** → si el OB "funciona" sobre ruido = ilusión geométrica → **DEBE caer a breakeven**. Control más discriminante que en Exp#1.
3. **Robustez al parámetro**: k∈{1.5,2,2.5} × W∈{30,50,80} × R∈{1.5,2,3}. Señal real = estable en el vecindario.
4. **As-of E2**: split GMM reutilizado (`regime_walk_forward`); cada trade se asigna a train/forward por `regime_labels[entry_bar]`; params fijados a priori ⇒ sin leakage.

**+ Diagnóstico per-cluster (NO criterio, descripción):** la **prueba causal específica** = un OB de reversión debería vivir en régimen de **reversión/lateral**, no tendencial. Si hay edge y se concentra coherentemente con la causa → señal; si aparece donde la causa no lo predice → sospecha de artefacto.

---

## 5. Criterio de éxito (pre-registrado)

El order block tiene edge si, sobre el panel LÓGICO primario (k=2/W=50/R=2):
- `pf_fwd` GLOBAL con **CI bootstrap por-símbolo que excluye 1.0**, **Y**
- **cae sobre random walk** (placebo PF≈breakeven), **Y**
- **robusto** en {k,W,R}, **Y**
- coherencia causal en el desglose per-cluster (vive donde la causa lo predice).

Edge → candidato real (la aguja). Sin edge → 5º "no", el más informativo (ni la hipótesis causal con respaldo de experiencia funciona) → cierra la pregunta del proyecto.

---

## 6. Universo, métricas, coste

- **Universo**: 45 símbolos. **Métricas**: PF + CI bootstrap por-símbolo, PnL neto, nº trades, win-rate, neto 0.10%.
- **Harness**: **kernel NUEVO de order-block** (`ob_detector.py`, lógica discreta por-setup; NO reusa el kernel de MA-cross). Reusa `lab.calc_atr` (ATR), `regime_walk_forward` (split as-of), `placebo_gen` (E1), bootstrap de Exp#1.
- **Coste**: detección = bucle barra-a-barra (numpy, ~segundos/símbolo); barrido 45 × {k,W,R} = minutos. BUILD caro (escribir+validar detector+test), backtest barato. **Smoke obligatorio** (detección sensata + 0 look-ahead) antes del barrido.

---

## 7. Tier-3 PAUSE Ricardo MANDATORY

- **T3.1-Exp2**: detector construido + smoke (detección sensata + test no-look-ahead PASS) + este .md congelado → Ricardo aprueba ANTES del barrido 45.
- **T3.2-Exp2**: el smoke revela look-ahead irreducible o detección incoherente → diagnóstico antes de seguir.
- **T3.3-Exp2**: durante el diseño, una decisión de formalización con grado de libertad grande sin elección lógica clara → Tier 3 (NO elegir tuneando).

## 8. Invariantes
ULTRATHINK + §12 L38. Línea roja trasladada al DISEÑO (k/W/R lógicos congelados a priori, NO tunear). Look-ahead fuera por construcción + test. Random walk especialmente potente. brain/portfolio/kernel productivos INTACTOS (kernel OB nuevo, separado). Migración Kraken en pausa. Bot Tokio stopped. NO martingala. Frame 3 cerrado.

## 9. Plan
Congelar .md (DONE) → construir `ob_detector.py` + test no-look-ahead → smoke 1 símbolo (BTC: detección sensata + prefix-invariance PASS + pf_fwd as-of de 1 celda) → **T3.1-Exp2** (OK Ricardo) → barrido 45 + placebo + robustez → T3.2 tabla.
