# Anatomy of a Null Result: A Pre-Registered, Adversarially Audited Case Study of Retail Systematic Trading in Crypto Perpetuals (2018–2026)

**Ricardo Castellanos Macias**
Independent researcher

*Working paper — v1.0.0, 2026-07-07.*
*Code, pre-registrations, results, and regeneration scripts: https://github.com/RicardoCastellanosTrader/el-trading-no-existe-evidencia · Archived snapshot: DOI [10.5281/zenodo.21229492](https://doi.org/10.5281/zenodo.21229492).*

---

## Abstract

This is a pre-registered, adversarially audited case study of what a technically competent retail trader can actually extract from crypto perpetual futures. Over 18 experiment families I evaluated a strategy space of 20,891,648 configurations × 31 presets (~6.5×10⁸ evaluations per symbol-pass on GPU), on Binance USDT-margined perpetuals (top-45 by liquidity), 2018–2026, at taker costs, including ten weeks of real-money execution with certified simulation-to-live fidelity. Two results. **(1) Out-of-sample transfer of past-performance selection is approximately null:** the correlation between past and forward performance is +0.598 [0.451, 0.713] when measured on the same data that produced the selection, and −0.054 [−0.305, +0.389] on independent data. The apparent edge of the optimized system (profit factor 3.317 in-sample) collapses to 0.917 — below breakeven — when parameters are fixed a priori. **(2) The genuine signals detected never cleared an honest bar:** their magnitude is below retail costs (liquidation-cascade survival gap ≈ +1 bp gross per trade; hourly seasonality < 10 bps) or below a trivial benchmark (market-neutral momentum Sharpe 0.541 vs. 1.443 for an equal-weighted buy-and-hold; funding-carry long leg ≈ market beta). These findings replicate the established literature on backtest overfitting and retail trading losses; the contribution is the mechanistic anatomy from inside one operation, with open artifacts. Limitations — survivorship as an explicit ceiling, ~3 effective evidence clusters rather than 18 independent ones, a bounded domain, cryptographically verifiable pre-registration for only 3 of 18 families — are stated up front.

---

## 1. Introduction

The finding that most retail traders lose money is not new. Regulators publish it as a standardized disclosure (74–89% of retail CFD accounts lose money in ESMA-mandated warnings), and the academic record is consistent across markets and decades (Barber & Odean, 2000; Barber et al., 2014; Chague et al., 2020). The finding that backtests systematically overstate future performance is also not new: it has a formal theory (Bailey, Borwein, López de Prado & Zhu, 2014; Bailey & López de Prado, 2014) and a multiple-testing literature (White, 2000; Hansen, 2005; Harvey, Liu & Zhu, 2016).

This paper does not claim to demonstrate either result for the first time. It is a **replication and an anatomy**: a documented account, from inside a single retail operation, of *how exactly* both results manifest when the operator is competent enough to build the full industrial apparatus — a GPU backtesting kernel, a per-regime walk-forward pipeline, a production bot with certified execution fidelity — and honest enough to instrument his own search with pre-registrations, placebo controls, untouched holdouts, and an adversarial audit of his own verdicts.

Three things distinguish this study from the existing record:

1. **The inside view with real money.** The subject of the study is the author's own trading system, deployed live on a VPS with real capital. The gap between simulation and reality is not assumed; it was measured (signal-level fidelity 98.24–100% in the final certification) and the real-money outcome (736 fills over ten weeks) is reported to the cent.
2. **Open artifacts.** Every experiment ships with its pre-registration, code, results, and verdict. Raw market data are not redistributed but are exactly regenerable from a public source (data.binance.vision) with checksum manifests. A reader with the repository can recompute every number in this paper.
3. **The mechanistic anatomy of overfitting.** Beyond confirming *that* selection fails to transfer, the experiments isolate *where the illusion is minted*: the search machinery certifies "notable" configurations on pure geometric-Brownian noise at the same rate as on real data (noise floor profit factor 2.35 vs. 2.32 on production picks); the same ranking that correlates +0.598 with forward results on its own bars correlates −0.054 on independent bars; and a component stripped of optimization (logical parameters fixed a priori) performs indistinguishably from a random-walk placebo.

The paper is organized around a simple discipline: the conclusion was frozen before writing, every public number traces to a primary artifact through a claims-backing table published with the repository, and the limitations section is written to be the strongest section of the paper.

## 2. Related work

**Backtest overfitting.** Bailey, Borwein, López de Prado & Zhu (2014) formalized the probability of backtest overfitting and showed that unreported trials make in-sample performance nearly meaningless; Bailey & López de Prado (2014) proposed the deflated Sharpe ratio as a correction. Harvey, Liu & Zhu (2016) documented the multiple-testing problem at the scale of the factor literature itself. White (2000) and Hansen (2005) provided the classical reality-check machinery for data snooping. This study is, in effect, a single-operator field experiment of exactly the phenomenon that literature models: a search over ~2×10⁷ configurations with the trials counted, not hidden.

**Retail trading outcomes.** Barber & Odean (2000) established that trading is hazardous to retail wealth; Barber, Lee, Liu & Odean (2014) showed that persistent day-trading skill is rare in a complete market record; Chague, De-Losso & Giovannetti (2020) found that essentially no Brazilian day traders sustain a living over time. ESMA's product-intervention disclosures institutionalized the base rate. The present study adds the mechanism from the inside: not merely that the operator lost, but the audited decomposition of *why the system was expected to win and did not*.

**The anomalies tested.** Where the experiments touch documented anomalies, the anchors are standard: cross-sectional momentum (Jegadeesh & Titman, 1993), time-series momentum (Moskowitz, Ooi & Pedersen, 2012), betting-against-beta (Frazzini & Pedersen, 2014), and carry (Koijen et al., 2018). The question asked here is narrower than theirs: not whether the anomaly exists in academic data, but whether a retail operator at taker costs on this venue can eat it.

## 3. The system under test

The object of study is a complete retail systematic operation, built over roughly two years:

- **Strategy family ("SmartDiv").** Trend-following and mean-reversion variants over 1h bars, defined by a 26-bit configuration space (20,891,648 valid configurations) crossed with 31 parameter presets.
- **Search machinery.** A GPU backtesting kernel (~10⁶ configurations/second) driving a per-regime walk-forward pipeline: unsupervised market-regime clustering (Gaussian mixtures over volatility/efficiency features), per-regime specialist selection, and out-of-sample evaluation windows. One full recycling pass of the 45-symbol portfolio evaluates ≈ 6.5×10⁸ configuration×preset combinations per symbol. The final production state retained 138,000 configurations with complete walk-forward metrics.
- **Production.** A live engine (v2.8.1) executing on Binance USDT-margined perpetuals via a VPS, with circuit breakers, EWMA correlation control, and volatility targeting. Real capital (~296 USDT — deliberately small; the point was measurement, not income).
- **Fidelity instrumentation.** The claim "the backtest is what actually traded" was not assumed. An early audit matched 10 of 11 real trades against a stateless kernel replay (91%, CI [62%, 98%] — small N, reported as such). The stronger, later evidence is a signal-by-signal certification between the production brain and the laboratory kernel over 1,500-bar windows: **98.24–100% match per symbol** (e.g., 100% over 250 signals on BTC; 100% over 498 on ONDO). A shadow-equivalence run of two full stack versions over the same candles agreed on 99.46% of 6,470 cycles (documented in the lab journal).

This fidelity work is what makes the null result *interpretable*: when the live account fails to earn, the explanation cannot hide in an implementation gap.

## 4. Methods: the honesty harness

The core methodological problem of a self-study is self-deception. The harness built against it has seven components:

1. **Pre-registration, with an honest taxonomy.** Each experiment froze its hypothesis, falsifier, and cardinal metric in a written pre-registration before results were read. Three levels of external verifiability are declared, and the level of each experiment is published: **Level A** (pre-registration commit verifiably precedes the results commit in git history): 3 of 18 families (the live-edge campaign, the regime-conditional test, and the order-block experiment). **Level B** (pre-registration document written before results but committed together with them): the information-capacity study, the moving-average component study, and the two microstructure/momentum sandboxes. **Level C** (closure-list experiments and re-tests committed in a single batch commit). Git timestamps are self-asserted; external anchoring is provided by an OpenTimestamps attestation of the repository state (2026-07-06) and the archived DOI snapshot. One asymmetry deserves emphasis: **every verdict in this study is negative.** A fabricated pre-registration would be a strange instrument for a self-interested author, whose incentive points in the opposite direction — toward finding edge.
2. **Anti-look-ahead gates.** Every signal generator passes a prefix-invariance test: signals computed on a data prefix must be bit-identical to the same timestamps computed on the full series.
3. **Pure placebos.** Detector-level experiments are benchmarked against geometric Brownian motion placebos — not shuffled real data, which preserves exploitable structure. The placebo *floor* (what the metric yields on structureless noise) replaces the naive breakeven of 1.0. This single discipline reverses conclusions: 15/45 symbols "beat breakeven" on the order-block test; 0/45 beat the noise floor with confidence intervals.
4. **Symmetric, stratified controls.** Event studies (liquidation cascades) use volatility-matched control samples, after an adversarial audit showed the unmatched gap was inflated ~3–4×.
5. **Cluster bootstrap.** Confidence intervals on the deciding number, clustered by symbol (and by 8-hour blocks where funding applies), never pooled naively across correlated series.
6. **Benchmark-first.** Where a strategy competes with passive exposure, the benchmark (equal-weighted buy-and-hold, Sharpe 1.443) was computed and reported *before* the strategy's bar was set.
7. **Untouched as-of holdouts.** Selection replays are performed "as of" a historical date with bidirectional anti-leakage checks (the E2 harness); holdout windows consumed by one experiment are ledgered and never reused as fresh.

Finally, the verdicts themselves were adversarially audited: a multi-agent review (39 independent AI auditor instances, run twice) recomputed the headline numbers from primary artifacts and attempted to overturn each verdict. All seven principal verdicts survived as "correct with nuances"; the nine resulting corrections (e.g., the cascade survival gap deflated from +23 pp to ~+6–8 pp after volatility matching; a NaN-handling bug in one correlation) are incorporated throughout this paper and documented in the repository. The audit's working transcripts were not retained — only the corrections document; this is listed as a limitation.

**AI assistance as part of the method.** All technical implementation and execution — GPU kernels, walk-forward pipeline, production bot, validation harness, the experiments themselves and the 39-agent adversarial audit — was performed by AI agents (Claude and Claude Code, Anthropic) under the author's direction, review and approval, task by task. The author is a non-programmer; the honesty harness described in this section was built precisely so that this technical delegation could not compromise the validity of the results. The research questions, design decisions, approval of every pre-registration, sign-off of every verdict, and full responsibility for every published claim are the author's. Under ICMJE/COPE criteria, AI tools do not qualify for authorship. Full statement: `AI_ASSISTANCE.md` in the repository.

## 5. Results

The 18 experiment families are summarized in Table 1. Following the adversarial audit (correction A7), they are presented as **approximately three effective evidence clusters plus orthogonal single-axis probes** — not 18 independent confirmations. Numbers in this section are point estimates with 95% bootstrap intervals where computed; every number traces to a primary artifact via the claims table in the repository.

### 5.1 Cluster I: the optimized system and its selection machinery

**The optimized system has no demonstrated net edge.** Replayed as-of on untouched holdouts, the full production system's profit factor is **0.702 [0.439, 1.066]** (N = 163 trades); the most recent holdout excludes 1.0 from above (CI upper bound 0.96).

**The illusion is minted by the search, not the market.** The same selection machinery, run on pure GBM noise, certifies "notable" configurations with an expected profit factor floor of **2.35** — statistically indistinguishable from the **2.32** floor it certified on the real production picks. The production month realized **0.640 [0.26, 1.31]**. The machine manufactures the same promise on structureless noise as on real data; reality then pays neither.

**Past performance does not select future performance.** Ranking configurations by any past-performance dimension and correlating with forward results: within the same data slice, ρ = **+0.598 [0.451, 0.713]** (27 symbols, 243 configurations). On independent data: ρ = **−0.054 [−0.305, +0.389]** (9 symbols, 60 configurations). The interval includes zero and excludes nothing dramatic — the honest statement is *approximately null transfer*, not "proven collapse"; but the within/independent gap of ~0.65 in correlation is the signature of selection fitting its own bars. Three of four candidate "predictive dimensions" in the pipeline's scoring turned out to be mechanical auto-correlations of the target itself; the one clean candidate (regime context, ε² = 0.574 in-selection) failed confirmation on untouched holdouts: in the only cells that genuinely exercise the regime-conditional hypothesis (three-regime cells), the specialist performed *worse* in its own regime (Δ = −0.535 and −0.094), and the conditional portfolio nets 0.983 — below 1 — versus 0.931 agnostic, with a wrong-match placebo at p = 0.47 (no specificity).

**Optimization is the whole difference.** The same signal family with parameters fixed a priori by logic ("what a textbook would choose") yields a median forward profit factor of **0.917** — below breakeven. Optimized per asset: **3.317**. The 2.4-unit gap *is* the overfitting, measured directly.

### 5.2 Cluster II: the operator's own beliefs, objectified

**Moving-average crossovers carry no edge.** The crossover component in isolation, across 14 moving-average types with logical parameters, medians 0.917 (trend) and 0.742 (mean-reversion) versus GBM placebo floors of 0.928 and 0.853. Zero of 14 types exceed a median of 1. The result is "indistinguishable from noise *and* sub-breakeven" — the component the industry sells most is inert.

**The author's own discretionary system — the one that had made him money — also fails.** His order-block/liquidity criterion was formalized faithfully (verified against his own canonical trade example before any sweep), gated for look-ahead, and swept across 45 symbols: median profit factor **0.8002** versus a GBM placebo floor of **0.9891**. The real signal sits *below* structureless noise (gap −0.189, negative in 7/7 configuration variants); **0/45 symbols beat the floor with confidence intervals** (6/45 on point estimates — the distinction matters and is preserved). The audited nuance: the sign is robust (P(gap ≥ 0) ≤ 3.2%), the magnitude is not statistically earned. An ablation killed the causal core: entering at the *deepest* liquidity block (0.8002) is indistinguishable from the shallowest (0.8109) or a random block (0.8099). The rule that carried the intuition does nothing.

### 5.3 Cluster III: the documented anomalies, at retail costs

**Liquidation cascades: a real microstructural signal that costs eat.** Post-cascade survival differs genuinely from volatility-matched controls: **+13.2 pp** [11.1, 15.5] (BTC) and **+13.3 pp** [11.5, 15.3] (ETH). Net of a hard falsifier (worst price within 3 s, −2% stop, taker fees), the per-trade expectation is *negative* with the interval excluding zero (BTC 3-month: −0.00039 [−0.00062, −0.00017]). The adversarially corrected gross magnitude is on the order of **+1 basis point per trade** — two orders of magnitude below the cost stack.

**Cross-sectional momentum: the least-null result, still below the bar.** With the benchmark frozen first (equal-weighted buy-and-hold Sharpe **1.443**), a 12h Jegadeesh-Titman long/short quintile portfolio achieved genuine market neutrality (β = −0.043 vs. the index, −0.041 vs. BTC) and was **the only net-positive strategy in the entire study**: Sharpe **0.541**, +29.6% over two years net of rotation costs, max drawdown −27.4% (versus −59% for the benchmark). It still fails the pre-registered bar (1.94), fails absolute adequacy (0.541 < 1), and printed 0.028 in 2023. Long-only momentum (1.163) does not even beat buy-and-hold; short-only is toxic (−0.83; funding plus squeezes). Reported honestly: crypto cross-sectional momentum exists and hedges, but does not pay a retail operator for the time.

**The remaining axes, each with its own instrument, all negative.** Funding-carry: market-neutral Sharpe **−0.053** [−1.282, +1.261]; the long leg alone is genuinely positive (+1.141, orthogonal to momentum, ρ = 0.022) but below buy-and-hold (1.443) — carry's long leg is bull beta in disguise, and the short leg (−1.026) destroys the neutral combination. Short-horizon reversal: −0.121 at turnover 2.9. Daily time-series momentum over eight years including the 2022 bear: 0.749 versus 0.779 for buy-and-hold, with −85% max drawdown. Low-volatility/BAB: −0.633, unmasked by a corrected beta gate as covert short-beta (β = −0.494). BTC→altcoin lead-lag: the only FDR-surviving lag (1–2 h) is *negative* (−0.016) and far below the cost threshold. Clock seasonality: four hour/day buckets survive FDR (UTC hours 21–22, Friday, Saturday; 2017–2026) — a real effect of at most **5.97 bps** [2.82, 9.28], below the ~10 bps round-trip cost; useful for execution timing, untradeable as a strategy. Open-interest positioning: −0.42, not surviving 2024.

### 5.4 Summary table

| # | Family (popular name) | Cardinal result | Verdict |
|---|---|---|---|
| E01 | The optimized system ("my backtest wins") | PF 0.702 [0.439, 1.066]; noise floor 2.35 ≈ production floor 2.32; replay 0.640 | No net edge |
| E02 | Past-performance selection ("pick the best performers") | score→forward ρ +0.054, crosses 0 | Dead/mechanical |
| E03 | Regime conditioning ("trade the regime") | 3-regime cells Δ −0.535 / −0.094; net < 1 | Not confirmed |
| E04 | MA crossovers ("golden cross") | 0.917 vs. noise 0.928; 0/14 types > 1 | Negative |
| E05 | Order blocks / SMC ("smart money") | 0.8002 vs. floor 0.9891; 0/45 with CI | Negative, sign-robust |
| E06 | Liquidation cascades ("stop hunts") | survival gap real; net −0.2%/trade; ≈ +1 bp gross | Negative under falsifier |
| E07 | Cross-sectional momentum | L/S Sharpe 0.541 net-positive < bar 1.94; EW 1.443 | Below the bar |
| E08 | Funding carry | −0.053; long leg +1.141 < EW 1.443 | Not worthy |
| E09 | Short-term reversal | −0.121, turnover 2.9 | Not worthy |
| E10 | Daily TSMOM | 0.749 < EW 0.779; maxDD −85% | Not worthy |
| E11 | Low-vol / BAB | −0.633; β −0.494 (covert short-beta) | Not worthy |
| E12 | Lead-lag BTC→alts | only sig. lag negative (−0.016) | Closed |
| E13 | Clock seasonality | max 5.97 bps < 10 bps cost | Real, untradeable |
| E14 | Open interest | −0.42; dies in 2024 | Not worthy |
| E15 | Cascade squeeze (retest, vol-matched) | net diff CI excludes 0, negative | Dies |
| E16 | Selection transfer (retest) | ρ +0.598 within vs. −0.054 independent | Overfit signature |
| E17 | Regime placebo (retest) | wrong-match p = 0.47; conditional 0.983 < 1 | Reinforces E03 |
| E18 | Order-block ablation (retest) | deepest ≈ shallowest ≈ random | Causal rule inert |

### 5.5 Real-money coda

Over ten weeks of live production (2026-04-13 to 2026-06-21), the system executed **736 fills** across 43 symbols with certified fidelity. Gross price PnL: **+3.28 USDT**. Estimated commissions at 0.10% round-trip on 4,962 USDT of notional: **−4.96 USDT**. Net: **≈ −1.7 USDT** on ~296 USDT of capital. I did not lose dramatically; I did not win at all. *The costs consumed the PnL* — which is precisely what the measurement program predicts for a system whose true edge is indistinguishable from zero.

## 6. Limitations

This section is load-bearing; the study's claim to credibility rests on the precision of its own boundaries.

1. **Survivorship as a ceiling, by construction.** The 45-symbol universe is the top of the surviving 2026 liquidity distribution. Every positive number in this study (including momentum's 0.541 and carry's long leg) is therefore an *optimistic ceiling*; the nulls are, if anything, understated. This direction of bias is asymmetric in the study's favor only because its conclusions are negative.
2. **~3 effective evidence clusters, not 18.** The first five families share the kernel, data, and placebo machinery; the re-tests (E15–E18) deliberately re-attack earlier verdicts. Counting "18 families" describes experimental coverage, not independence. The adversarial audit's estimate of ~3 effective clusters is adopted as canonical.
3. **A bounded domain.** One venue (Binance USDT-margined perpetuals), one universe (top-45), one period (2018–2026, with sub-periods per experiment), one cost model (taker, 0.10–0.20% round trip). Nothing here speaks to maker rebates, institutional fee tiers, other venues, options, or spot. The conclusion is bounded to: *a retail taker on this venue in this period*.
4. **Pre-registration verifiability is honest but partial.** Only 3 of 18 families have cryptographic (git-precedence) proof that the pre-registration preceded results; the rest rest on documentary evidence, the lab journal, and the negative-verdict asymmetry. External time anchoring begins 2026-07-06 (OpenTimestamps) — after the work, sealing its state, not its chronology.
5. **The adversarial audit is documented but not replayable.** The 39-agent audit's corrections document is published; the raw transcripts were not retained. A skeptic must treat the audit as a documented internal procedure, not reproducible evidence — its *corrections*, however, are all recomputable from primary artifacts, and all of them made the study's claims weaker, not stronger.
6. **Small samples where reality is expensive.** The early fidelity audit is N = 11 (hence the certified W1500 signal-level evidence is what carries the fidelity claim); the real-money period is ten weeks and ~296 USDT. The live coda is consistent with the measurements; it is not independent proof.
7. **The access-gated strategies remain untested — and that is the thesis.** Five families were closed by access rather than by verdict: delta-neutral cash-and-carry (edge almost certainly real; irrelevant at 289 USDT), options variance-risk-premium (requires margin and jurisdiction access), market-making (requires L2 data and latency), cross-exchange arbitrage (capital fragmentation), and on-chain flow data (subscription costs and vendor look-ahead risk). The two doors where edge most plausibly exists were closed by capital and access, not by evidence of absence. The study's conclusion is therefore not "no edge exists" but: **within everything a retail operator can actually reach, nothing cleared an honest bar. The only thing I did not try is to stop being retail.**

## 7. Conclusion

A technically competent retail operator built the full industrial apparatus — a 20.9-million-configuration search, per-regime walk-forward selection, a production bot with certified 98–100% signal fidelity — pointed it at the most liquid crypto perpetuals for eight years of data, instrumented himself against self-deception, invited an adversarial audit of his own conclusions, and put real money behind the result. The outcome is a map of nulls with an anatomy: the selection machinery manufactures its promises on noise exactly as on data; past performance transfers approximately nothing; the operator's own most-trusted setup sits below structureless noise; and the signals that are real (cascades, seasonality, momentum, carry's long leg) are sized below costs or below a benchmark any passive holder gets for free.

None of this is a claim about hedge funds, market makers, or anyone with fee tiers, colocation, or balance sheets — the access-gated doors are exactly where the remaining edge plausibly lives. That asymmetry is the finding. The engineering survived every audit thrown at it; the alpha did not survive the engineering.

## 8. Data and code availability

The complete repository — pre-registrations, experiment code, results, the claims-backing table (every public number → primary artifact), the validation harness (anti-look-ahead gates, GBM placebos, cluster bootstrap, as-of replay), the 736-fill real-money log, and the full development history of the main branch (218 commits, PII-filtered) — is available at https://github.com/RicardoCastellanosTrader/el-trading-no-existe-evidencia, archived with DOI 10.5281/zenodo.21229492. Raw market data are regenerable from data.binance.vision via the included scripts and SHA-256 manifests. A reader's guide, *How to audit this work*, maps each headline number to its recomputation path.

## Acknowledgments

This project was carried out with extensive AI assistance — Claude and Claude Code (Anthropic), operating as directed agents: the technical implementation and execution of all code, experiments and infrastructure; the 39-agent adversarial audit protocol; the curation of the public repository; and assistance in drafting this manuscript from the table of verified claims (`afirmaciones_respaldo.md`). All of it under the author's direction, review and approval. The research questions, the design decisions, the approval of every pre-registration, the sign-off of every verdict, and full responsibility for every published claim — including all errors — are the author's. Under standard academic authorship criteria (ICMJE, COPE), AI tools do not qualify for authorship; the sole author is Ricardo Castellanos Macias. This statement is part of the method, not a footnote: the project documents, among other things, a case of empirical research directed by a non-programmer through AI agents. Full statement: `AI_ASSISTANCE.md`.

## References

- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2014). Pseudo-mathematics and financial charlatanism: The effects of backtest overfitting on out-of-sample performance. *Notices of the American Mathematical Society*, 61(5), 458–471.
- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management*, 40(5), 94–107.
- Barber, B. M., & Odean, T. (2000). Trading is hazardous to your wealth: The common stock investment performance of individual investors. *Journal of Finance*, 55(2), 773–806.
- Barber, B. M., Lee, Y.-T., Liu, Y.-J., & Odean, T. (2014). The cross-section of speculator skill: Evidence from day trading. *Journal of Financial Markets*, 18, 1–24.
- Chague, F., De-Losso, R., & Giovannetti, B. (2020). Day trading for a living? *SSRN Working Paper No. 3423101*. https://doi.org/10.2139/ssrn.3423101
- European Securities and Markets Authority (ESMA). (2018). Decisions (EU) 2018/795 and 2018/796 of 22 May 2018 to temporarily prohibit binary options and restrict contracts for differences in the Union, pursuant to Article 40 of Regulation (EU) No 600/2014. *Official Journal of the European Union*, L 136.
- Frazzini, A., & Pedersen, L. H. (2014). Betting against beta. *Journal of Financial Economics*, 111(1), 1–25.
- Hansen, P. R. (2005). A test for superior predictive ability. *Journal of Business & Economic Statistics*, 23(4), 365–380.
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). …and the cross-section of expected returns. *Review of Financial Studies*, 29(1), 5–68.
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *Journal of Finance*, 48(1), 65–91.
- Koijen, R. S. J., Moskowitz, T. J., Pedersen, L. H., & Vrugt, E. B. (2018). Carry. *Journal of Financial Economics*, 127(2), 197–225.
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics*, 104(2), 228–250.
- White, H. (2000). A reality check for data snooping. *Econometrica*, 68(5), 1097–1126.
