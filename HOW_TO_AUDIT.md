# How to audit this work

A guide for the hostile technical reader. Every key finding of the project, with the exact command to recompute it from this repository's primary artifact, and the number that must come out. If a command does not reproduce the declared number, that is a finding of yours — report it.

Requirements: `git`, `python` ≥3.10 with `pandas`. All commands run from the repo root.

---

## 0. What this repository is (and the sanitization)

- It is the **complete original working repo** (225 commits, 34 branches, 2026-04 → 2026-07), cloned and filtered with `git filter-repo --replace-text` / `--replace-message` to remove personal identifiers. The placeholders `IP_DOMESTICA_REDACTADA`, `IP_VPS_TOKIO_REDACTADA`, `IP_VPS_IRLANDA_REDACTADA`, `AWS_ACCOUNT_REDACTADO`, `INSTANCE_ID_TOKIO_REDACTADO`, `INSTANCE_ID_IRLANDA_REDACTADO` are deliberate, 1:1 literal substitutions — no market data, result or code was altered.
- Filtering rewrites commit hashes. The lab diary (`CONTEXTO_PROYECTO_TRADING.md`) cites original-repo hashes: the original→public translation is in **`prerregistros/commit_map_filtrado.txt`**.
- The original private repo was sealed with **OpenTimestamps on 2026-07-06** (HEAD + sha256 manifest of the 23 pre-registration/verdict documents). The sha256 of those documents are identical in this repo — verification in `prerregistros/README.md`.

## 1. Pre-registration timestamps

See **`prerregistros/README.md`** (A/B/C taxonomy, verification commands, OTS seals). Honest summary: 3 of 18 experiments have git-verifiable precedence; the rest are documentary pre-registrations. All verdicts are negative — a forged timestamp would have to explain what the author gains by fabricating results adverse to his own system.

## 2. Key findings, one by one

### 2.1 The overfitting signature: ρ +0.60 in-sample vs −0.05 independent (C1 / E16)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_C1.json')); print(d['spearman_pf_tr_vs_pf_fwd'], d['CI95_symbol_clustered'], d['caveat'])"
```
**Expected:** `0.5984 [0.451, 0.713]` — past→future correlation on THE SAME bars (27 symbols, 243 configs, chronological split).

```bash
python -c "import json; print(round(json.load(open('audit_forense_gap_20260612/estudio_capacidad_fase1_results.json'))['rho_pf_tr_fwd_b2'],4))"
```
**Expected:** `-0.0545` — the same selection against independent data (binance_w3_data, 9 symbols). CI [−0.305, +0.389] (symbol-clustered bootstrap; see `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md`).

**Correct reading (and the one the project uses):** transfer ≈ nil / indistinguishable from zero — NOT "demonstrated collapse" (the independent CI includes 0 and +0.297; 9 symbols = underpowered). The +0.60↔−0.05 gap is the signature of overfitting-to-the-bars. Recompute from raw: `cierre_definitivo_20260702/run_C1_extend.py` + `results_C1_extend.csv`.

### 2.2 The optimized-vs-logical gap (Exp#1 / E04)

```bash
python -c "import pandas as pd; print(pd.read_csv('analysis_scripts/atribucion_componentes_20260626/results_optimized.csv')['opt_pf_fwd_global'].median())"
```
**Expected:** `3.3167` — median forward PF of the per-asset OPTIMIZED moving-average cross (N=45).

```bash
python -c "import pandas as pd; t=pd.read_csv('analysis_scripts/atribucion_componentes_20260626/results_tf_logical.csv'); print(round(t[(t.fast==10)&(t.slow==55)&(t.hyst==0.0)]['pf_fwd'].median(),4))"
```
**Expected:** `0.9167` — the same component with a-priori LOGICAL parameters (primary config 10/55). Below breakeven.

**Correct reading:** the 3.32 is not edge — it is contaminated by selection; the 3.32 → 0.92 difference IS the measurement of overfitting. Noise reference: `results_placebo.csv` (median ~0.928 on noise).

### 2.3 Order block / "my own system" (Exp#2 v3 / E05 + C3 ablation / E18)

```bash
python -c "import pandas as pd; r=pd.read_csv('analysis_scripts/atribucion_componentes_20260626/results_obv3_real.csv'); print(round(r[(r.near==0.05)&(r.frac==0.75)&(r.P==10)]['pf_all'].median(),4))"
```
**Expected:** `0.8002` — the author's real criterion (verified on his exact XRP example before the sweep), over 45 symbols. The placebo floor (median of 6 noise series, same geometry) = **0.9891** → the real signal sits BELOW noise. Floor derivation and the 7 configs: `ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md` + `results_obv3_placebo.csv`. **0/45 symbols with CI_low > floor** (6/45 on point estimates — do not swap the two figures).

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_C3.json')); print(d)"
```
**Expected:** deepest ≈ 0.8002, shallowest ≈ 0.8109, random ≈ 0.8099 — the causal rule ("deepest block = biggest liquidity pool") is INERT.

**Mandatory A4 nuance:** sign-robust gap (P(gap≥0) ≤ 3.2%) but magnitude not statistically earned; the committed no-look-ahead smoke certification is irreproducible (independent inspection of the frozen code found no leak; any leak would be symmetric real/placebo). See `auditoria_adversarial/README.md`.

### 2.4 Hourly seasonality: real but < costs (B6 / E13)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_B6.json')); print(d['fdr_significativos']); print(d['VEREDICTO'])"
```
**Expected:** 4 buckets surviving FDR-BH (hour_22 +5.97 bps [2.82, 9.28], hour_21 +5.37, Fri, Sat) — maximum **5.97 bps < 10 bps** RT cost. Real effect, not tradeable.

### 2.5 Carry: the long leg is beta (B1 / E08)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_B124.json'))['B1']; print(d['sharpe_full'], d['sharpe_CI'])"
```
**Expected:** Sharpe **−0.053** [−1.282, +1.261] for the market-neutral factor. The long leg alone: Sharpe **+1.141** — but the trivial buy-and-hold EW benchmark gives **1.443**:

```bash
python -c "import json; d=json.load(open('cs_mom_sandbox/results/benchmark.json')); print(d['2023-2024']['sharpe'])"
```
**Expected:** `1.443`. The carry long leg ≈ bull beta, not edge.

### 2.6 CS-MOM: the "least dead" line, still not worthy (E07)

```bash
python -c "import json; d=json.load(open('cs_mom_sandbox/results/curves.json')); print(d['bench_sharpe'], d['base']['C'])"
```
**Expected:** bench 1.443; Curve C (real L/S market-neutral, β vs EW −0.043) Sharpe **0.541**, +29.6% over 2 years NET of rotation costs, maxDD −27%, 2023 ≈ 0.028. **This is the project's only net-positive return** — and it sits below the pre-registered bar (1.94) and below the passive index. It is declared as the explicit counterexample to any "all signals < commissions" phrasing: see `afirmaciones_respaldo.md` §4.

### 2.7 Liquidation cascades: the signal exists, the edge does not (MFE / E06 + B8 / E15)

```bash
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_B8.json')); print(d['BTCUSDT']['net_3m']); print(d['VEREDICTO'])"
```
**Expected:** cascade 3-minute net ≈ −0.0025 vs vol-matched control −0.0021, **difference with CI excluding 0 on the negative side** (BTC −0.00039 [−0.00062, −0.00017]). The survival gap (+13pp over control) is a real microstructural signal; after correcting the volatility confound ≈ +6-8pp over coin-flip ≈ **+1 bp gross/trade** — an order of magnitude below any cost. Original: `mfe_sandbox/results/edge_summary.json` + correction A5 in `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md`.

### 2.8 Sim↔live fidelity of the bot (production, real money)

```bash
python -c "import json; d=json.load(open('cert_fidelity_gate_W1500.json')); print(min(x['match_rate'] for x in d), max(x['match_rate'] for x in d), sum(x['n_brain'] for x in d))"
```
**Expected:** `98.24 100.0` over 9 symbols (per-symbol N 125–498) — signal-by-signal brain↔kernel W1500 certification. The early kernel↔exchange audit gave 91% with **N=11** (CI 62–98%): always cited with its N (`audit_v5_2_report_20260427_1844_utf8.txt`).

### 2.9 The 736 real fills and the "I didn't win"

```bash
python -c "import pandas as pd; df=pd.read_csv('logs_historicos_vps/trade_history/trade_history.csv'); print(len(df), df.timestamp.min(), df.timestamp.max(), round(df.pnl_usdt.sum(),2))"
```
**Expected:** `736` fills, 2026-04-13 → 2026-06-21, gross price PnL **+3.28 USDT**. Commission is not recorded in the fills (they are mark-based; see the A9 analysis): estimated at nominal taker 0.10% RT on notional (≈ 4,962 USDT) ≈ **−4.96 USDT** → net ≈ **−1.7 USDT**. The project's exact phrasing: *"I didn't win: costs took the PnL."* The empirical check of the cost assumption against these same fills (realized funding ≈ negligible, +0.118 USDT total): `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A9.

## 3. How to try to break this

Explicit invitation — ordered by expected payoff for the critic:

1. **Hunt for look-ahead.** The prefix-invariance gates are in `analysis_scripts/atribucion_componentes_20260626/exp2*smoke*.py`, the placebo generator in `audit_forense_gap_20260612/placebo_gen.py`, and the bidirectional anti-leakage as-of harness in `audit_forense_gap_20260612/asof_run.py` / `asof_eval.py`. If you find a leak that is asymmetric real/placebo, you have a potential flip.
2. **Recompute the CIs.** All per-symbol cluster bootstrap for PHASE B/C is in `cierre_definitivo_20260702/xs_harness.py` + `run_B*.py` / `run_C*.py`. The CIs are the deciding numbers; point estimates are not.
3. **Audit the thresholds.** Every bar (breakeven, 10 bps, EW+0.5, verdict zones) is frozen in its pre-registration. Check that no verdict pivoted metrics post-hoc — the single detected pivot (MFE, cardinal metric survival → net mean) is declared and recorded as a procedural deviation in A5.
4. **Search for the suppressed positive signal.** The meta-audit (39 agents ×2) tried: none found. The best candidate is CS-MOM Curve C and it is declared on the front page, not buried.
5. **Reproduce from raw.** Data regenerates from public sources (data.binance.vision): `datos/REGENERAR.md` + sha256 manifests.

## 4. What cannot be verified from this repo (declared)

- The **raw transcripts** of the 39-agent meta-audit (not preserved; the A1–A9 corrections document remains).
- The **effective commission** of the real fills (BingX records mark-based PnL without fees; the 0.10% RT is the published nominal taker — faithful-to-conservative, see A9).
- The **exact initial capital** of the account (~296 USDT, documentary).
- Numbers marked **RED** in `afirmaciones_respaldo.md` are not used publicly — that list exists precisely so you can check they do not appear in the paper.
