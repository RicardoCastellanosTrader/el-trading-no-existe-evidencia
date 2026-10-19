# Erratas de documentos sellados o de registro (v1.0.3)

**Regla:** lo sellado no se edita nunca; las notas, aclaraciones y erratas van en archivos aparte. Los documentos de esta lista están en el manifiesto sellado con OpenTimestamps el 2026-07-06 (`ots/prerregistros_manifest_20260706.txt`, marcados «sellado»). Los demás son registros históricos de la campaña («registro»): tampoco se reescriben. La comprobación de sellos de `README.md` §4 sigue dando 23/23.

Cada errata da el texto del documento, lo que dice la fuente primaria y la fuente. Ninguna cambia un veredicto.

| # | Documento (estado) | Línea | El documento dice | Lo que dice la fuente | Fuente |
|---|---|---|---|---|---|
| 1 | `audit_forense_gap_20260612/VEREDICTO_FASE1.md` (sellado) | 13 | «qué floors acuña la búsqueda sobre RUIDO puro \| NOISE FLOOR = 2.35» | El 2,35 es la mediana de tres placebos: 1 GBM (2,14) y 2 block-shuffles de 168 h de barras reales (3,03 y 2,35). El GBM solo ya supera el umbral pre-registrado de 1,7 | `audit_forense_gap_20260612/e1_noise_floor/RESULTADO_E1.md` L7-15; `placebo_gen.py` L1-17 |
| 2 | ídem (sellado) | 43 | «el noise floor (2.35) **iguala** el floor de producción (2.32)» | No hay contraste entre las dos cifras: el 2,35 es una mediana de medianas del `pf_fwd_ci_low` sobre placebos; el 2,32, una media ponderada por trades en vivo sobre datos reales. La comparación es descriptiva | `RESULTADO_E1.md` L7-13; `INFORME_AUDITORIA_FORENSE_GAP.md` L23; `fase0_pf_live.py` L127-134 |
| 3 | `audit_forense_gap_20260612/e1_noise_floor/RESULTADO_E1.md` (registro) | 19 | «Los floors … son **estadísticamente indistinguibles** de lo que la búsqueda acuña sobre ruido puro» | Igual que 2: no hay contraste, y los placebos no son todos ruido puro | ídem |
| 4 | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` (sellado) | 50 | «NIVEL 2 — ANCLA INDEPENDIENTE» | El mismo documento (L30) califica ese conjunto de «Parcial — re-cómputo en fuente de datos distinta …, pero misma ventana temporal 33%». Es otra fuente, no un periodo independiente | L30 del mismo documento; `analysis_scripts/bloque2c_w3_validation_20260423/bloque2c_smoke_c.py` L3-7, L35, L50 |
| 5 | `audit_forense_gap_20260612/VEREDICTO_ESTUDIO_CAPACIDAD.md` (sellado) | 34, 42, 52 | «datos independientes (N2)»; «datos Binance independientes» | Ídem 4: velas de futuros de Binance de la misma ventana; su tercio forward (para BTC, 2025-04-23 → 2026-04-23) cubre meses que la selección ya había visto como velas al contado (hasta 2026-03-24) | ídem 4; `output/production/ranking_lite_v5e_BTCUSDT.txt` L18 |
| 6 | `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md` (sellado) | 3, 5, 8, 16, 17, 20, 21 | «−0.05 independiente»; «datos independientes existentes (binance_w3_data…)»; «**Independiente (ventana distinta**, binance_w3_data)» | Ídem 4 y 5: otra fuente, **misma** ventana. El resto del veredicto (intervalo [−0,305, +0,389], que incluye 0 y +0,297; prueba infrapotenciada; «ni colapso … ni transferencia parcial») se mantiene | ídem 4 y 5 |
| 7 | `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` (registro) | 18 | «"pf_tr +0.30 en-slice → −0.05 independiente"» | Ídem 6 | ídem |
| 8 | `cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md` (registro) | 27 | «CI independiente riguroso (9 sym)» | Ídem 6 | ídem |
| 9 | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md` (sellado) | 89, 109, 136 | «la de mayor respaldo previo» / «la de mayor respaldo académico previo» | Superlativo sin fuente bibliográfica en el archivo; el anclaje citado es Jegadeesh y Titman (1993) | — |
| 10 | ídem (sellado) | 118, 122 | objetivo de drawdown «−15/−20» | El test del código aplicó −25 % (`cs_mom.py` L334); el resultado (−27,4 %) falla los dos. Ver `cs_mom_sandbox/NOTA_v1.0.1_CS_MOM.md` | `cs_mom_sandbox/cs_mom.py` L334; `results/curves.json` |

## Ampliación v1.0.4 (2026-10-20)

Barrido de todos los archivos del tag v1.0.3 (no solo los `.md`) contra las tablas de propagación y de canon del paquete del caso. Mismo criterio: lo sellado y los registros no se editan.

| # | Documento (estado) | Línea | El documento dice | Lo que dice la fuente | Fuente |
|---|---|---|---|---|---|
| 11 | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` (sellado) | 136 | «→ **−0.05 en datos independientes**» | Ídem 4 | ídem 4 |
| 12 | `audit_forense_gap_20260612/VEREDICTO_ESTUDIO_CAPACIDAD.md` (sellado) | 7, 44 | «el único contrapeso barato con datos independientes»; «la única dimensión pura-pasado que se puede cruzar contra datos independientes (`pf_tr`) **colapsa de +0.30 a −0.05**» | Ídem 5. Y «colapsa»: el intervalo [−0,305, +0,389] incluye 0 y +0,297; ni colapso ni transferencia demostrados (C1, posterior) | ídem 5; `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md` L7-8, L16-23 |
| 13 | `cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md` (registro) | 47 | «supera el listón honesto» | «el listón fijado para ella» | `afirmaciones_respaldo.md`, REDACCIÓN OFICIAL §3 |
| 14 | ídem (registro) | 49 | «no en datos independientes» | Ídem 6 | ídem 6 |
| 15 | ídem (registro) | 59 | «Que TODOS converjan negativo con instrumentos independientes» | A7: unos 3 clústeres efectivos; las líneas comparten en parte kernel, datos y placebos | `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` §A7 |
| 16 | ídem (registro) | 3, 61 | «placebo GBM puro» (regla de la lista) | C3 se comparó con el suelo mixto de E05 (3 GBM + 3 block-shuffles) | `cierre_definitivo_20260702/results_C3.json` L25; `lista_cierre/README.md`, regla 3 |
| 17 | `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` (registro) | 23 | «"TF indistinguible del ruido y sub-breakeven neto"» | Comparación descriptiva de medianas (real 0,917; panel 0,928; GBM solo 0,909), sin contraste formal | `analysis_scripts/atribucion_componentes_20260626/ATRIBUCION_T3_2_RESULTADOS.md` L40-41, L54 |
| 18 | ídem (registro) | 30 | «La inspección independiente del código congelado NO halló fuga» | «independiente» sin respaldo: la inspección la hizo la propia meta-auditoría (mismo criterio que H1 de la tabla de respaldo) | `afirmaciones_respaldo.md`, Correcciones v1.0.3, H1 |
| 19 | `audit_forense_gap_20260612/VEREDICTO_NIVEL3_D3.md` (sellado) | 29 | «**Decisivo:** las 2 celdas **3-régimen** … **leanean NEGATIVO**» | A6: partición post hoc, retirada. La lectura neta (C2) es Δ +0,086, indistinguible de un emparejamiento aleatorio (p = 0,47). El veredicto D3 NO CONFIRMADO se mantiene | `FASE_A_correcciones_documentales.md` L44-46; `cierre_definitivo_20260702/C2_nivel3_patas_omitidas_VEREDICTO.md` L6-7, L11-12 |
| 20 | ídem (sellado) | 36-38 | «Tres líneas **independientes** convergen»; «noise floor 2.35 ≈ floor producción»; «re-selección por PF/calidad/estabilidad MUERTA o mecánica» | A7 (comparten kernel, datos y placebos); 2,35 frente a 2,32 sin contraste (ver 2); A2 (muerta para re-rankear dentro de la shortlist, no concluyente en rango completo) | `FASE_A_correcciones_documentales.md` §A7, §A2 (L15); ver 2 |
| 21 | `audit_forense_gap_20260612/CAMPAÑA_EDGE_REAL_FASE0_PREREGISTRO.md` (sellado) | 73 | «la fábrica los produce sobre ruido puro» (hipótesis) | Los placebos usados fueron 1 GBM y 2 block-shuffles de 168 h (ver 1) | ídem 1 |
| 22 | `audit_forense_gap_20260612/NIVEL3_CONFIRMACION_D3_DISENO_PREREGISTRO.md` (sellado) | 5 | «E1 lo probó: sobre ruido puro SIEMPRE existe un "ganador"» | Ídem 21 | ídem 1 |
| 23 | `CONTEXTO_PROYECTO_TRADING.md` (registro: diario) | 1694, 1698, 1700, 1702 | «N2 ancla bloque2c N=60 (Binance independiente)»; «DECISIVO: las 2 celdas 3-régimen leanean NEGATIVO»; «7 líneas convergentes … supera el listón honesto»; «mini-pre-registro congelado ANTES de resultados … placebo GBM puro» | Ídem 4; ídem 19; ídem 13 y 15; nivel C (git no demuestra la precedencia) e ídem 16 | ídem |
| 24 | `audit_forense_gap_20260612/estudio_capacidad_fase1.py` (registro: código tal como corrió) | 256 | «# ---- D1: bloque2c N=60 (pooled, instrumento independiente) ----» | Ídem 4 | ídem 4 |
| 25 | Documentos y scripts de pre-registro de nivel B y C (lista abajo) (sellados o registro) | varias | «CONGELADO», «congelado», «params CONGELADOS» | La palabra registra lo que el autor fijó por escrito. En los niveles B y C git no puede demostrar que precediera a los resultados; la precedencia la documentan la estructura del documento y el diario. Ningún criterio cambió | `prerregistros/README.md` §2 (niveles B y C) |

Archivos de la errata 25:

- `analysis_scripts/atribucion_componentes_20260626/PREREGISTRO_EXP1_MEDIAS.md`: L1, 3, 102
- `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md`: L3, 5, 54, 62, 92
- `audit_forense_gap_20260612/estudio_capacidad_fase1.py`: L7, 326
- `cierre_definitivo_20260702/B1_funding_carry_PREREGISTRO.md … B8_mfe_squeeze_PREREGISTRO.md`: cabecera (L1, L3) y secciones de criterios
- `cierre_definitivo_20260702/B_C3_note.md`: L3
- `cierre_definitivo_20260702/run_B124.py, run_B3.py, run_B5.py, run_B7.py, run_B8.py`: L2
- `cierre_definitivo_20260702/run_C2.py, run_C3.py`: L5
- `cs_mom_sandbox/CS_MOM_PREREGISTRO.md`: L3, 8, 44, 60, 100
- `cs_mom_sandbox/cs_mom.py`: L3, 7, 15, 19, 34, 183, 337
- `mfe_sandbox/MFE_FASE_EDGE_PREREGISTRO.md`: L1, 3, 19, 24, 51, 68, 76, 92, 106, 122, 155, 165, 238
- `mfe_sandbox/run_edge.py; mfe_sandbox/smoke_calibration.py`: L5, 7, 43; 15-19, 172
