# C1 — N2 con potencia real — VEREDICTO (2026-07-02/03)

Pre-registro = retest de blindaje de la auditoría (§5): ¿el eslabón "pf_tr +0.30 en-slice → −0.05 independiente" es colapso real o no-concluyente infra-potenciado?

## Parte 1 — CI riguroso sobre los datos independientes existentes (binance_w3_data, 9 sym, 60 configs)
- ρ Spearman(pf_tr_bin, pf_fwd_bin) = **−0.0545**.
- CI95 symbol-clustered bootstrap (10k) = **[−0.305, +0.389]** → **incluye +0.297 (en-slice) Y 0**.
- **Resultado:** el "colapso a −0.05" NO está estadísticamente establecido sobre datos independientes — es un **no-concluyente infra-potenciado** (9 símbolos). **Confirma la corrección A2 de la auditoría.**

## Parte 2 — Extensión a 27 sym / 243 configs (data_cache, split cronológico 67/33)
- ρ = **+0.5984**, CI symbol-clustered **[0.451, 0.713]** → excluye 0, POR ENCIMA de +0.297.
- **CAVEAT CARDINAL (Tier-3, anticipado en el pre-registro):** data_cache = **mismos bars que la selección**, con split CRONOLÓGICO (≠ split por episodios de producción). Esto mide **robustez-al-split / persistencia WITHIN-DATA**, NO independencia. El +0.60 es el eje "en-slice"/mecánico (más fuerte aún que el +0.30 del JSON), no el test out-of-sample.

## INTERPRETACIÓN honesta (el contraste ES la firma)
- **Within-data (chronological, mismos bars):** ρ = +0.60 → persistencia FUERTE.
- **Independiente (ventana distinta, binance_w3_data):** ρ = −0.05 [−0.31,+0.39] → indistinguible de 0.
- El **gap +0.60 within vs −0.05 independiente = firma clásica de sobreajuste-a-los-bars**: la persistencia pf_tr→pf_fwd existe cuando train/fwd son el mismo histórico (incluso cortado cronológicamente) y **se desvanece al mover a datos independientes**. Refuerza (no voltea) la conclusión del Estudio de Capacidad ("re-selección por rendimiento pasado = mecánica/in-sample").

## VEREDICTO C1
- **Sub-claim corregido (A2) SE MANTIENE:** como afirmación de TRANSFERENCIA a datos independientes, el eslabón es infra-potenciado (CI 9-sym incluye +0.30 y 0). No es un "colapso demostrado".
- **La extensión NO tightened el CI independiente** (por diseño: data_cache no es independiente). Para tightenlo de verdad haría falta descargar la ventana bloque2c-independiente para ≥15 símbolos más (descarga dedicada) — **FLAG Tier-3: decisión de qué fuente independiente usar, no pre-especificada**. No se hizo porque el contraste within-vs-independiente ya es interpretativamente claro y consistente con el veredicto global.
- **Neto:** ni "colapso total demostrado" ni "transferencia parcial real" — el pf_tr pasado predice el forward SOLO cuando comparten los bars (mecánico); en datos independientes no se distingue de 0. La familia de re-selección sigue sin edge transferible.

`results_C1.json` + `results_C1_extend.csv` (243 filas).
