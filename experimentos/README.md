# Experimentos E01–E18 — índice maestro

18 experimentos con pre-registro y veredicto propios: 7 líneas del arco de búsqueda de edge (E01–E07), 8 ejes de la Lista de Cierre Definitivo (E08–E15) y 3 retests de blindaje (E16–E18). **No son 18 evidencias independientes**: como evidencia efectiva son ~3 clusters (corrección A7 de la meta-auditoría) — E16/E17/E18 son retests de E02/E03/E05, y E15 es retest de E06 con control mejorado.

Cada experimento tiene su README con: hipótesis, pre-registro (y su nivel de verificabilidad temporal A/B/C — ver [`../prerregistros/README.md`](../prerregistros/README.md)), código, datos, resultados y veredicto con los números exactos. Los artefactos viven en sus rutas históricas dentro de este mismo repo; estos READMEs son la capa de navegación.

| ID | Experimento | "Lo que la industria vende" | Veredicto (número cardinal) |
|----|-------------|------------------------------|------------------------------|
| [E01](E01_edge_real/README.md) | Campaña Edge Real (as-of holdout) | "Mi sistema optimizado gana" | Sin edge neto demostrado: PF real 0.702 [0.439, 1.066] |
| [E02](E02_estudio_capacidad/README.md) | Estudio de Capacidad de Información | "Elige la config con mejor histórico" | Re-selección muerta/mecánica: ρ score→fwd +0.054 (cruza 0) |
| [E03](E03_regimen_d3/README.md) | Nivel 3 — D3 régimen (MATCH/MISMATCH) | "Opera según el régimen de mercado" | NO CONFIRMADO: celdas 3-régimen Δ −0.535 / −0.094 |
| [E04](E04_cruces_medias/README.md) | Exp#1 — cruce de medias aislado | "Cruces de medias móviles" | TF 0.917 vs ruido 0.928; 0/14 tipos de MA > 1 |
| [E05](E05_order_blocks/README.md) | Exp#2 — order block (criterio real) | "Order blocks / SMC / acción del precio" | Real 0.800 vs floor placebo 0.989; 0/45 (CI) |
| [E06](E06_cascadas_liquidacion/README.md) | MFE — exhaustión post-cascada | "Liquidation hunting" | Neto ≈ −0.2%/trade; señal real ≈ +1 bp bruto |
| [E07](E07_cs_momentum/README.md) | CS-MOM market-neutral | "Momentum: compra fuertes, vende débiles" | NO DIGNO: L/S neutral Sharpe 0.541 < listón (EW 1.443) |
| [E08](E08_funding_carry/README.md) | B1 funding-carry | "Cobrar el funding" | Sharpe −0.053; pata larga +1.141 anulada por corta −1.026 |
| [E09](E09_reversal_corto/README.md) | B2 reversal corto | "Compra el dip" | Sharpe −0.121, turnover 2.9 |
| [E10](E10_tsmom_diario/README.md) | B3 TSMOM diario | "Sigue la tendencia" | Sharpe 0.749 < EW 0.779 (8 años) |
| [E11](E11_low_vol_bab/README.md) | B4 low-vol / BAB | "Betting against beta" | Sharpe −0.633; β −0.494 (short-beta encubierto) |
| [E12](E12_lead_lag/README.md) | B5 lead-lag BTC→alts | "BTC manda, las alts siguen" | Único lag significativo (1-2h) NEGATIVO: −0.016 |
| [E13](E13_estacionalidad_reloj/README.md) | B6 estacionalidad horaria | "Las mejores horas para operar" | Efecto real no tradeable: máx +5.97 bps < 10 bps coste |
| [E14](E14_open_interest/README.md) | B7 open interest | "Sigue el posicionamiento" | Sharpe −0.42; no sobrevive 2024 |
| [E15](E15_mfe_squeeze/README.md) | B8 MFE squeeze (retest E06) | "Cazar el squeeze" | Neto peor que control: diff CI excluye 0 en negativo |
| [E16](E16_potencia_n2/README.md) | C1 — potencia real de N2 (retest E02) | — | ρ within +0.598 vs independiente −0.054 |
| [E17](E17_nivel3_patas/README.md) | C2 — patas omitidas Nivel 3 (retest E03) | — | Placebo p=0.47 (sin especificidad); condicional 0.983 < 1 |
| [E18](E18_ablacion_orderblock/README.md) | C3 — ablación order block (retest E05) | — | Regla causal INERTE: deepest ≈ shallowest ≈ random |

**Alcance (corrección A8):** perps Binance top-45 por liquidez, timeframes 1s/1h/12h/diario, 2018–2026, costes taker 0.10–0.20% round-trip. Los veredictos NO son atemporales ni se extienden a otros venues, ejecución maker o escala institucional. El sesgo de supervivencia del universo se asume y se declara como techo optimista.
