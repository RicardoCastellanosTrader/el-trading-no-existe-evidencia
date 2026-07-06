# El Escudo — anatomía de una búsqueda exhaustiva de edge retail en cripto (2018–2026)

*El Escudo — the anatomy of an exhaustive retail edge search in crypto (2018–2026). English version below.*

---

## Español

### Qué es esto

Este repositorio documenta, con artefactos abiertos, la conclusión de un proyecto de trading algorítmico llevado durante meses hasta su cierre definitivo: un sistema completo (laboratorio GPU + bot en producción con dinero real), 18 familias de experimentos pre-registradas, y una auditoría adversarial de los propios veredictos. El resultado es negativo, y ese es el punto: esto es la anatomía mecanística, desde dentro, de por qué la selección por rendimiento pasado no se transfiere fuera de muestra, y de cómo las pocas señales genuinas que existen quedan por debajo de los costes de un operador retail.

### La conclusión (formulación congelada)

> Estudio de caso pre-registrado y auditado adversarialmente (18 familias de experimentos, un espacio de 20,9 millones de configuraciones (~10¹⁰ evaluaciones acumuladas), perps Binance top-45, 2018–2026, costes taker): (1) transferencia fuera de muestra ≈ nula de la selección por rendimiento pasado (ρ −0,05 independiente vs +0,60 in-sample); (2) ninguna señal genuina superó el listón honesto: magnitud inferior a costes (cascadas ≈ +1 pb; estacionalidad < 10 pb) o por debajo del benchmark trivial (Curva C 0,541 < EW 1,443; carry pata larga ≈ beta). Consistente con la literatura (Bailey–López de Prado, backtest overfitting; Barber–Odean/Chague, pérdidas retail; disclosures ESMA), a la que aporta la anatomía mecanística desde dentro con artefactos abiertos.

**Posicionamiento:** esto es una **réplica/anatomía independiente de resultados establecidos**, no una "primera demostración" de nada. La literatura ya sabía que los backtests sobreajustan y que el retail pierde; lo que este repositorio aporta es el mecanismo medido desde dentro, con el instrumental y los datos a la vista.

### Limitaciones (léelas antes que nada)

1. **Sesgo de supervivencia asumido como techo.** El universo (top-45 por capitalización, point-in-time parcial) favorece al backtest; los resultados positivos serían un techo optimista. Como todos los veredictos son negativos, el sesgo juega *contra* la conclusión, no a favor.
2. **~3 clusters efectivos, no 18 evidencias independientes.** Las 18 familias comparten parcialmente kernel, datos y placebos (corrección A7 de la meta-auditoría). "18" es un conteo de experimentos, no de líneas independientes.
3. **Dominio acotado.** Perps de Binance top-45, marcos 1s/1h/12h/diario, 2018–2026, costes taker 0,10–0,20% RT. No es un negativo atemporal ni cubre otros venues, maker, u operativa institucional.
4. **Un solo mercado y un solo operador.** N=1 como estudio de caso; la generalización viene de la consistencia con la literatura, no de este repositorio solo.
5. **Pre-registros: 3 de 18 con precedencia git verificable.** Solo E01, E03 y E05 tienen el commit del pre-registro estrictamente anterior al de resultados. El resto es pre-registro documental (criterios congelados por escrito, commit conjunto). La taxonomía completa y por qué esto no invierte la carga de la prueba: [`prerregistros/README.md`](prerregistros/README.md).

### Mapa del repositorio

```
README.md                        ← estás aquí
COMO_AUDITAR_ESTO.md             ← guía para el crítico técnico (EN: HOW_TO_AUDIT.md)
afirmaciones_respaldo.md         ← cada afirmación pública → su artefacto primario (incluye los números ROJOS descartados)
paper/                           ← working paper (EN y ES)
prerregistros/                   ← taxonomía A/B/C, guía de verificación de timestamps, sellos OpenTimestamps
experimentos/                    ← guías E01–E18: pre-registro + código + resultados + veredicto de cada familia
auditoria_adversarial/           ← la meta-auditoría de los 7 veredictos (correcciones A1–A9)
lista_cierre/                    ← el criterio de parada y las 5 puertas cerradas-por-acceso
harness/                         ← el instrumental anti-autoengaño (gates, placebos, bootstrap)
datos/                           ← cómo regenerar cada dataset desde fuentes públicas + checksums
trades_reales/                   ← los 736 fills con dinero real y qué prueban
--- árbol histórico de trabajo (se conserva íntegro) ---
CONTEXTO_PROYECTO_TRADING.md     ← el diario de laboratorio (10.600 líneas)
cierre_definitivo_20260702/      ← FASE A/B/C/D: pre-registros B1–B8, retests C1–C3, resultados, harness cross-sectional
audit_forense_gap_20260612/      ← campaña Edge Real, Estudio de Capacidad, Nivel 3, harness as-of
analysis_scripts/atribucion_componentes_20260626/  ← Exp#1 medias y Exp#2 order block
mfe_sandbox/  cs_mom_sandbox/    ← cascadas de liquidación y momentum cross-sectional
live/  tests/  master.py  ...    ← el sistema bajo test (bot v2.8.1, pipeline, kernels, 449 tests)
```

### Empezar a auditar en 3 comandos

```bash
# 1. Precedencia temporal de un pre-registro Nivel A (E01):
git log --format='%h %ad %s' --date=short -- \
  "audit_forense_gap_20260612/CAMPAÑA_EDGE_REAL_FASE0_PREREGISTRO.md" \
  "audit_forense_gap_20260612/VEREDICTO_FASE1.md"
# → el pre-registro (d94123d, 2026-06-13) precede al veredicto (6b396ac, 2026-06-16)

# 2. La firma del sobreajuste (ρ in-sample vs independiente):
python -c "import json; d=json.load(open('cierre_definitivo_20260702/results_C1.json')); print(d['spearman_pf_tr_vs_pf_fwd'], d['CI95_symbol_clustered'])"
# → 0.5984 [0.451, 0.713]  (mismos datos)
python -c "import json; print(round(json.load(open('audit_forense_gap_20260612/estudio_capacidad_fase1_results.json'))['rho_pf_tr_fwd_b2'],4))"
# → -0.0545  (datos independientes; CI [−0.305, +0.389])

# 3. Los 736 fills reales:
python -c "import pandas as pd; df=pd.read_csv('logs_historicos_vps/trade_history/trade_history.csv'); print(len(df), round(df.pnl_usdt.sum(),2))"
# → 736  3.28   (PnL bruto de precio; las comisiones no registradas ≈ −4.96 → neto ≈ −1.7 USDT)
```

La guía completa, hallazgo por hallazgo, está en [`COMO_AUDITAR_ESTO.md`](COMO_AUDITAR_ESTO.md).

### Autoría y asistencia de IA

**Ricardo Castellanos**, investigador independiente — autor único, conforme a los criterios ICMJE/COPE (las herramientas de IA no cumplen criterios de autoría). El proyecto se realizó con asistencia extensiva de **Claude y Claude Code (Anthropic)** como agentes dirigidos: la implementación y ejecución técnica de todo el código, experimentos e infraestructura; la meta-auditoría adversarial de los propios veredictos (39 agentes ×2 pasadas; ver [`auditoria_adversarial/`](auditoria_adversarial/README.md)); la curación de este repositorio; y la asistencia en la redacción del manuscrito a partir de la tabla de afirmaciones verificadas. Las preguntas de investigación, las decisiones de diseño, la aprobación de cada pre-registro, la firma de cada veredicto y la responsabilidad plena de todas las afirmaciones publicadas son del autor. Este proyecto documenta, entre otras cosas, un caso de investigación dirigida por un no-programador mediante agentes de IA: la declaración **forma parte del método**, no es una nota al margen. Declaración completa: [`DECLARACION_ASISTENCIA_IA.md`](DECLARACION_ASISTENCIA_IA.md).

### Estado y licencias

- **Estado: pre-release / working paper.** Sin DOI todavía; el snapshot con DOI (Zenodo) acompañará a la publicación.
- **Código:** licencia MIT ([`LICENSE`](LICENSE)). **Textos, figuras y paper:** CC BY 4.0 ([`LICENSE-docs`](LICENSE-docs)).
- Este repositorio es un clon del repo de trabajo original con el historial completo (223 commits) **filtrado de identificadores personales** con `git filter-repo`; los placeholders `IP_*_REDACTADA`, `AWS_ACCOUNT_REDACTADO`, `INSTANCE_ID_*` son deliberados. Detalles y mapeo de hashes: [`COMO_AUDITAR_ESTO.md`](COMO_AUDITAR_ESTO.md) §sanitización.

---

## English

### What this is

This repository documents, with open artifacts, the conclusion of an algorithmic-trading project carried through to its definitive close: a complete system (GPU lab + production bot trading real money), 18 pre-registered experiment families, and an adversarial audit of the verdicts themselves. The result is negative — and that is the point: this is the mechanistic anatomy, from the inside, of why past-performance selection does not transfer out of sample, and how the few genuine signals that do exist fall below realistic retail costs.

### The conclusion (frozen formulation)

> A pre-registered, adversarially audited case study (18 experiment families, a search space of 20.9 million configurations (~10¹⁰ accumulated evaluations), Binance top-45 perpetuals, 2018–2026, taker costs): (1) out-of-sample transfer of past-performance selection ≈ nil (ρ −0.05 on independent data vs +0.60 in-sample); (2) no genuine signal cleared the honest bar: magnitudes below costs (cascades ≈ +1 bp; hourly seasonality < 10 bps) or below the trivial benchmark (Curve C 0.541 < EW 1.443; carry long leg ≈ beta). Consistent with the literature (Bailey–López de Prado on backtest overfitting; Barber–Odean/Chague on retail losses; ESMA disclosures), to which it contributes the mechanistic anatomy from the inside, with open artifacts.

**Positioning:** this is an **independent replication/anatomy of established results** — never a "first demonstration". The literature already knew backtests overfit and retail loses; what this repository adds is the mechanism, measured from the inside, with the instruments and data in the open.

### Limitations (read these first)

1. **Survivorship bias assumed as a ceiling.** The universe (top-45 by capitalization, partially point-in-time) favours the backtest; positive results would be an optimistic ceiling. Since every verdict is negative, the bias works *against* the conclusion, not for it.
2. **~3 effective clusters, not 18 independent lines of evidence.** The 18 families partially share kernel, data and placebos (correction A7 of the meta-audit). "18" counts experiments, not independent evidence.
3. **Bounded domain.** Binance top-45 perpetuals, 1s/1h/12h/daily frames, 2018–2026, taker costs 0.10–0.20% RT. Not a timeless negative; other venues, maker execution and institutional operation are out of scope.
4. **One market, one operator.** N=1 as a case study; generalization comes from consistency with the literature, not from this repository alone.
5. **Pre-registrations: 3 of 18 with git-verifiable precedence.** Only E01, E03 and E05 have the pre-registration commit strictly before the results commit. The rest are documentary pre-registrations (criteria frozen in writing, committed jointly). Full taxonomy and why this does not flip the burden of proof: [`prerregistros/README.md`](prerregistros/README.md).

### Repository map

See the Spanish section above — directory names are shared. Curation layer: `COMO_AUDITAR_ESTO.md` / `HOW_TO_AUDIT.md` (auditor's guide), `afirmaciones_respaldo.md` (every public claim → its primary artifact, including the discarded RED numbers), `paper/`, `prerregistros/` (timestamp taxonomy + OpenTimestamps seals), `experimentos/` (E01–E18 guides), `auditoria_adversarial/`, `lista_cierre/`, `harness/`, `datos/`, `trades_reales/`. The full historical working tree (lab diary, sandboxes, production bot, 449 tests) is preserved intact.

### Start auditing in 3 commands

See the Spanish section above — the commands and expected outputs are identical. The full finding-by-finding guide is [`HOW_TO_AUDIT.md`](HOW_TO_AUDIT.md).

### Authorship and AI assistance

**Ricardo Castellanos**, independent researcher — sole author, under ICMJE/COPE criteria (AI tools do not qualify for authorship). The project was carried out with extensive assistance from **Claude and Claude Code (Anthropic)** as directed agents: the technical implementation and execution of all code, experiments and infrastructure; the adversarial meta-audit of the verdicts themselves (39 agents ×2 passes; see [`auditoria_adversarial/`](auditoria_adversarial/README.md)); the curation of this repository; and assistance in drafting the manuscript from the table of verified claims. The research questions, the design decisions, the approval of every pre-registration, the sign-off of every verdict and full responsibility for every published claim belong to the author. This project documents, among other things, a case of research directed by a non-programmer through AI agents: the statement **is part of the method**, not a footnote. Full statement: [`AI_ASSISTANCE.md`](AI_ASSISTANCE.md).

### Status and licenses

- **Status: pre-release / working paper.** No DOI yet; the DOI snapshot (Zenodo) will accompany publication.
- **Code:** MIT ([`LICENSE`](LICENSE)). **Texts, figures, paper:** CC BY 4.0 ([`LICENSE-docs`](LICENSE-docs)).
- This repository is a clone of the original working repo with the complete history (223 commits) **filtered of personal identifiers** using `git filter-repo`; the placeholders `IP_*_REDACTADA`, `AWS_ACCOUNT_REDACTADO`, `INSTANCE_ID_*` are deliberate. Details and hash mapping: [`HOW_TO_AUDIT.md`](HOW_TO_AUDIT.md) §sanitization.
