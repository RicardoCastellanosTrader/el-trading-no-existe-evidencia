# Cómo auditar este trabajo

Guía para el crítico técnico. Cada hallazgo clave del proyecto, con el comando exacto para recomputarlo desde el artefacto primario de este repositorio y el número que debe salir. Si algún comando no reproduce el número declarado, eso es un hallazgo tuyo — repórtalo.

Requisitos: `git`, `python` ≥3.10 con `pandas`. Todos los comandos se ejecutan desde la raíz del repo.

---

## 0. Qué es este repositorio (y la sanitización)

- Es el **repo de trabajo original completo** (225 commits, 34 ramas, 2026-04 → 2026-07), clonado y filtrado con `git filter-repo --replace-text` / `--replace-message` para eliminar identificadores personales. Los placeholders `IP_DOMESTICA_REDACTADA`, `IP_VPS_TOKIO_REDACTADA`, `IP_VPS_IRLANDA_REDACTADA`, `AWS_ACCOUNT_REDACTADO`, `INSTANCE_ID_TOKIO_REDACTADO`, `INSTANCE_ID_IRLANDA_REDACTADO` son deliberados y sustituyen literales 1:1 — ningún dato de mercado, resultado ni código fue alterado.
- El filtrado reescribe los hashes de commit. El diario (`CONTEXTO_PROYECTO_TRADING.md`) cita hashes del repo original: la traducción original→público está en **`prerregistros/commit_map_filtrado.txt`**.
- El repo original privado quedó sellado con **OpenTimestamps el 2026-07-06** (HEAD + manifiesto sha256 de los 23 documentos de pre-registro/veredicto). Los sha256 de esos documentos son idénticos en este repo — verificación en `prerregistros/README.md`.

## 1. Timestamps de los pre-registros

Ver **`prerregistros/README.md`** (taxonomía A/B/C, comandos de verificación, sellos OTS). Resumen honesto: 3 de 18 experimentos tienen precedencia git verificable; el resto es pre-registro documental. Los veredictos son todos negativos — un timestamp falsificado tendría que explicar qué gana el autor fabricando resultados adversos a su propio sistema.

## 2. Hallazgos clave, uno a uno

### 2.1 La firma del sobreajuste: ρ +0,60 in-sample vs −0,05 independiente (C1 / E16)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_C1.json')); print(d['spearman_pf_tr_vs_pf_fwd'], d['CI95_symbol_clustered'], d['caveat'])"
```
**Debe salir:** `0.5984 [0.451, 0.713]` — correlación pasado→futuro sobre LOS MISMOS bars (27 símbolos, 243 configs, split cronológico).

```bash
python -c "import json; print(round(json.load(open('audit_forense_gap_20260612/estudio_capacidad_fase1_results.json'))['rho_pf_tr_fwd_b2'],4))"
```
**Debe salir:** `-0.0545` — la misma selección contra datos independientes (binance_w3_data, 9 símbolos). CI [−0.305, +0.389] (bootstrap symbol-clustered; ver `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md`).

**Lectura correcta (y la que usa el proyecto):** transferencia ≈ nula / indistinguible de cero — NO "colapso demostrado" (el CI independiente incluye 0 y +0.297; 9 símbolos = infra-potenciado). El gap +0.60↔−0.05 es la firma del sobreajuste-a-los-bars. Recomputar desde crudo: `cierre_definitivo_20260702/run_C1_extend.py` + `results_C1_extend.csv`.

### 2.2 La brecha optimizado vs lógico (Exp#1 / E04)

```bash
python -c "import pandas as pd; print(pd.read_csv('analysis_scripts/atribucion_componentes_20260626/results_optimized.csv')['opt_pf_fwd_global'].median())"
```
**Debe salir:** `3.3167` — PF forward mediano del cruce de medias OPTIMIZADO por activo (N=45).

```bash
python -c "import pandas as pd; t=pd.read_csv('analysis_scripts/atribucion_componentes_20260626/results_tf_logical.csv'); print(round(t[(t.fast==10)&(t.slow==55)&(t.hyst==0.0)]['pf_fwd'].median(),4))"
```
**Debe salir:** `0.9167` — el mismo componente con parámetros LÓGICOS fijados a priori (config primaria 10/55). Bajo breakeven.

**Lectura correcta:** el 3,32 no es edge — está contaminado por selección; la diferencia 3,32 → 0,92 ES la medida del sobreajuste. Placebo de referencia: `results_placebo.csv` (mediana ~0.928 con ruido).

### 2.3 Order block / "mi propio sistema" (Exp#2 v3 / E05 + ablación C3 / E18)

```bash
python -c "import pandas as pd; r=pd.read_csv('analysis_scripts/atribucion_componentes_20260626/results_obv3_real.csv'); print(round(r[(r.near==0.05)&(r.frac==0.75)&(r.P==10)]['pf_all'].median(),4))"
```
**Debe salir:** `0.8002` — el criterio real del autor (verificado en su ejemplo XRP antes del barrido), sobre 45 símbolos. El floor placebo (mediana de 6 series de ruido, misma geometría) = **0.9891** → el real queda DEBAJO del ruido. Derivación del floor y las 7 configs: `ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md` + `results_obv3_placebo.csv`. **0/45 símbolos con CI_low > floor** (en punto-estimado 6/45 — no intercambiar las dos cifras).

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_C3.json')); print(d)"
```
**Debe salir:** deepest ≈ 0.8002, shallowest ≈ 0.8109, random ≈ 0.8099 — la regla causal ("el bloque más profundo = pool de liquidez mayor") es INERTE.

**Matiz A4 (obligatorio):** brecha de signo robusto (P(brecha≥0) ≤ 3,2%) pero magnitud no ganada estadísticamente; la certificación no-look-ahead del smoke commiteado es irreproducible (la inspección independiente del código congelado no halló fuga; una fuga sería simétrica real/placebo). Ver `auditoria_adversarial/README.md`.

### 2.4 Estacionalidad horaria: real pero < costes (B6 / E13)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_B6.json')); print(d['fdr_significativos']); print(d['VEREDICTO'])"
```
**Debe salir:** 4 buckets supervivientes a FDR-BH (hour_22 +5.97 bps [2.82, 9.28], hour_21 +5.37, vie, sáb) — máximo **5,97 pb < 10 pb** de coste RT. Efecto real, no tradeable.

### 2.5 Carry: la pata larga es beta (B1 / E08)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_B124.json'))['B1']; print(d['sharpe_full'], d['sharpe_CI'])"
```
**Debe salir:** Sharpe **−0.053** [−1.282, +1.261] para el factor market-neutral. La pata larga sola: Sharpe **+1.141** — pero el benchmark trivial comprar-y-mantener EW da **1.443**:

```bash
python -c "import json; d=json.load(open('cs_mom_sandbox/results/benchmark.json')); print(d['2023-2024']['sharpe'])"
```
**Debe salir:** `1.443`. La pata larga del carry ≈ beta de bull, no edge.

### 2.6 CS-MOM: lo "menos muerto", y aun así no digno (E07)

```bash
python -c "import json; d=json.load(open('cs_mom_sandbox/results/curves.json')); print(d['bench_sharpe'], d['base']['C'])"
```
**Debe salir:** bench 1.443; Curva C (L/S market-neutral real, β vs EW −0.043) Sharpe **0.541**, +29,6% en 2 años NETO de costes de rotación, maxDD −27%, 2023 ≈ 0.028. **Este es el único retorno neto-positivo del proyecto** — y queda bajo el listón pre-registrado (1.94) y bajo el índice pasivo. Se declara como contraejemplo explícito de cualquier "todas las señales < comisiones": ver `afirmaciones_respaldo.md` §4.

### 2.7 Cascadas de liquidación: la señal existe, el edge no (MFE / E06 + B8 / E15)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_B8.json')); print(d['BTCUSDT']['net_3m']); print(d['VEREDICTO'])"
```
**Debe salir:** neto 3m de cascada ≈ −0.0025 vs control vol-matched −0.0021, **diferencia con CI que excluye 0 en negativo** (BTC −0.00039 [−0.00062, −0.00017]). El gap de supervivencia (+13pp sobre el control) es señal microestructural real; tras corregir el confound de volatilidad ≈ +6-8pp sobre coin-flip ≈ **+1 pb bruto/trade** — un orden de magnitud bajo cualquier coste. Original: `mfe_sandbox/results/edge_summary.json` + corrección A5 en `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md`.

### 2.8 Fidelidad sim↔live del bot (producción, dinero real)

```bash
python -c "import json; d=json.load(open('cert_fidelity_gate_W1500.json')); print(min(x['match_rate'] for x in d), max(x['match_rate'] for x in d), sum(x['n_brain'] for x in d))"
```
**Debe salir:** `98.24 100.0` sobre 9 símbolos (N por símbolo 125–498) — certificación señal-a-señal brain↔kernel W1500. La auditoría temprana kernel↔exchange dio 91% con **N=11** (CI 62–98%): se cita siempre con su N (`audit_v5_2_report_20260427_1844_utf8.txt`).

### 2.9 Los 736 fills reales y el "no gané"

```bash
python -c "import pandas as pd; df=pd.read_csv('logs_historicos_vps/trade_history/trade_history.csv'); print(len(df), df.timestamp.min(), df.timestamp.max(), round(df.pnl_usdt.sum(),2))"
```
**Debe salir:** `736` fills, 2026-04-13 → 2026-06-21, PnL bruto de precio **+3.28 USDT**. La comisión no está registrada en los fills (es mark-based; ver análisis A9): estimada a taker nominal 0,10% RT sobre el notional (≈ 4.962 USDT) ≈ **−4.96 USDT** → neto ≈ **−1.7 USDT**. La formulación exacta del proyecto: *"no gané: los costes se llevaron el PnL"*. El contraste empírico del supuesto de costes contra estos mismos fills (funding realizado ≈ negligible, +0.118 USDT total): `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A9.

## 3. Cómo intentar romper esto

Invitación explícita — por orden de rentabilidad esperada para el crítico:

1. **Busca look-ahead.** Los gates de prefix-invariance están en `analysis_scripts/atribucion_componentes_20260626/exp2*smoke*.py`, el generador de placebos en `audit_forense_gap_20260612/placebo_gen.py`, y el harness as-of anti-leakage bidireccional en `audit_forense_gap_20260612/asof_run.py` / `asof_eval.py`. Si encuentras una fuga que sea asimétrica real/placebo, tienes un flip potencial.
2. **Recomputa los CI.** Todo el bootstrap cluster-por-símbolo de FASE B/C está en `cierre_definitivo_20260702/xs_harness.py` + `run_B*.py` / `run_C*.py`. Los CI son los números que deciden; los puntos-estimados no.
3. **Audita los umbrales.** Cada listón (breakeven, 10 pb, EW+0.5, zonas de veredicto) está congelado en su pre-registro. Comprueba que ningún veredicto pivotó de métrica post-hoc — el único pivote detectado (MFE, métrica cardinal supervivencia → media neta) está declarado y anotado como desviación procesal en A5.
4. **Busca la señal positiva suprimida.** La meta-auditoría (39 agentes ×2) lo intentó: ninguna encontrada. El mejor candidato es CS-MOM Curva C y está declarado en portada, no enterrado.
5. **Reproduce desde crudo.** Los datos se regeneran de fuentes públicas (data.binance.vision): `datos/REGENERAR.md` + manifiestos sha256.

## 4. Qué NO puede verificarse desde este repo (declarado)

- Los **transcripts crudos** de la meta-auditoría de 39 agentes (no se conservaron; queda el doc de correcciones A1–A9).
- La **comisión efectiva** de los fills reales (BingX registra PnL mark-based sin fee; el 0,10% RT es el taker nominal publicado — fiel a conservador, ver A9).
- El **capital inicial exacto** de la cuenta (~296 USDT, documental).
- Los números marcados **ROJO** en `afirmaciones_respaldo.md` no se usan públicamente — esa lista existe precisamente para que compruebes que no aparecen en el paper.
