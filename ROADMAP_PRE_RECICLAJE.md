# Roadmap pre-reciclaje — consolidado 2026-04-24

**Criterio institucional Ricardo 2026-04-24**: todas las mejoras (A+B+C) implementadas antes de lanzar reciclaje completo 45 sym. Categorías D+E esperan datos operacionales temporales. Reciclaje se lanza cuando A+B+C done + D+E validados/archivados.

## Categorías

### Categoría A — Z_BTC como feature GMM altcoins (mejora estructural)
Scope: ~8-12h sesión dedicada.
Modifica `regime_features.py` para añadir Z_ATR BTC como feature cross-símbolo del GMM de altcoins. BTC sin cambio. Re-entrena GMMs altcoins afectados. Smoke mini validation post-modificación.
Referencias: §9.4 v3.0, §13.3 Z_ATR BTC 2026-04-23.

### Categoría B — Metodología walk-forward Mecanismo 2 fix (refinamiento ranking)
Scope: ~4-6h sesión dedicada. **Fase actual**.
Re-ordena selección specialists por `pf_fwd_ci_low` directo en lugar de `specialist_score_ci_low` (que embebe pf_combined con dilución train/fwd). Elimina sesgo Mecanismo 2 identificado por Ricardo 2026-04-24.
Referencias: §13.2 bloque REFINAMIENTO canónico 2026-04-24, §13.3 W3 implementation 2026-04-23.

### Categoría C — Operacionales menores (micro-fixes + audit)
Scope: ~4-6h total distribuido.
- Opción D pnl_recon causa raíz (~1-2h data-independent).
- Audit Fidelidad 2 N≥50 post-v2.3.11 (~2h, disparador temporal ~2026-04-26, probablemente datos disponibles).
- L1892 active_config_id en SIGNALS_RAW (~30min).
- L1904 multiplicadores en SIGNALS_DISCARDED (~30min).
- Triaje micro-items adicionales (L1843, L1849, L1855, L1861) — muchos son de ultra-review 2026-04-17, pueden ser obsoletos tras v2.4.x. Decidir individualmente pre-implementación.

## Orden de ejecución

**Secuencial estricto** (Ricardo 2026-04-24): un hilo Claude Code activo por vez. Sin paralelización.

1. **Fase B primero**: Mecanismo 2 fix.
   Razón: marco mecánico recién consolidado (memoria fresca), baseline comparativo limpio para validar fix, scope acotado.
2. **Fase A segundo**: Z_BTC implementación + re-entrenamiento GMMs altcoins.
   Razón: Z_BTC es cambio estructural mayor; con B ya consolidado, smoke Z_BTC valida pipeline completo W3+W4+A14+A15+M2fix+Z_BTC. Si A entrara antes de B, no sabríamos atribución mejoras en smoke.
3. **Fase C en paralelo** (entre A y B o después de A, según oportunidad): micro-fixes sin bloquear cadena principal. Audit Fidelidad 2 cuando disparador temporal ~2026-04-26 madure.

## Dependencias y post-reciclaje

### Categoría D — Espera datos operacionales N≥100 (~2026-05-01)
- v2.6-inv entry filter candidato — validación Welch p<0.05 S4 homogéneo obligatorio (§13.3 actualizado Fase 3 stress-test).
- Cache funding extender a origen dataset (prerequisito VPS ~30 min).

### Categoría E — Espera datos operacionales N≥150 (~2026-05-10)
- v2.6-exit filter candidato (cerrar contrarian losing trades).

### Post-reciclaje
- Tier 0 I1 kernel reason_exit + Bloque 2c H1+H_funding+H_strategy (proyecto dedicado ~20-30h).
- Multi-testing correction formal (Bonferroni/BH/Deflated SR) — refinamiento menor no bloqueante.
- k-fold CV vs train/fwd split único — refinamiento menor.
- `_FWD_MIN_PF` óptimo calibrado — refinamiento menor.

## Reciclaje completo 45 símbolos

Trigger: A+B+C done + D+E validados o archivados.
Scope compute: ~180-225h VPS (8-10 días).
Estimación fecha: ~2026-05-12 a 05-22.

## Invariantes durante A+B+C

- Fidelidad 2 invariante (bot v2.4.5 operacional continuo).
- Sin deploy nuevos durante A+B+C salvo micro-fixes operacionales C que lo requieran explícitamente.
- Smokes pre-deploy §0.8 mandatory para cualquier cambio lab-side que genere JSONs nuevos.

## Referencias cruzadas

- §13.2 HALLAZGO ESTRUCTURAL + bloque REFINAMIENTO canónico 2026-04-24.
- §13.3 Categorías A (Z_BTC 2026-04-23), D+E (v2.6-inv/exit, cache funding), operacionales varios.
- §13.4 W3 IMPLEMENTADO 2026-04-23, W4 IMPLEMENTADO 2026-04-23, A14+A15 2026-04-23, Smoke reciclaje Bloque 5 PASS 2026-04-24, Smoke C 2026-04-24.
- §9.4 v3.0 roadmap técnico (Z_BTC contexto conceptual).
- Conversación Ricardo 2026-04-24 post-smoke (marco mecánico consolidado + criterio institucional orden).

## Actualización de este roadmap

Documento vivo. Se actualiza con:
- Mejoras adicionales identificadas durante ejecución A+B+C.
- Cambios de orden justificados.
- Cierre individual categorías (marcar DONE o ARCHIVADO con fecha).
- Re-trigger post-ejecución (reciclaje → roadmap post-reciclaje separado).

## Historia

- **2026-04-22** (`roadmap_2026-04-22.md.archived-20260424`): roadmap original categorización §13.3 N/R/C (29 items). Sustituido por criterio institucional 2026-04-24 "todas mejoras A+B+C pre-reciclaje".
- **2026-04-24**: roadmap consolidado A+B+C+D+E post-smoke reciclaje Bloque 5 + refinamiento §13.2 marco mecánico canónico.
