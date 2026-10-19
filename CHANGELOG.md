# CHANGELOG

## v1.0.3 — preparada, sin publicar

Alinea el archivo con las correcciones verificadas en la preparación del paquete del caso para Digital Finance (DF-1 y DF-2, 2026-10-19/20). **Ninguna cifra, intervalo ni veredicto cambia.** Cambia cómo se describen algunos hechos: qué placebos se usaron, qué mide cada cifra, qué puede probar cada pre-registro. **Por primera vez cambia la REDACCIÓN OFICIAL de `afirmaciones_respaldo.md` (§1, §5 y §6)**: contenía tres de las afirmaciones corregidas, y su texto anterior se conserva literal en la sección «Correcciones v1.0.3» de la propia tabla. Solo cambian archivos `.md` (ningún `.py`, `.json`, `.csv` ni parquet). Lo sellado no se edita: las notas y erratas van en archivos aparte.

| Bloque | Cambio | Archivos | Commit |
|---|---|---|---|
| 1 | README y guías alineados con las correcciones A1–A9 de la meta-auditoría y con las fuentes primarias:<br>• el noise floor 2,35 de E01 es la mediana de 1 GBM (2,14) y 2 block-shuffles de 168 h, no «GBM puro» (`e1_noise_floor/RESULTADO_E1.md` L7-13);<br>• los suelos de E04 (0,928; GBM solo 0,909) y E05 (0,9891) son paneles de GBM y block-shuffles;<br>• E03 se describe por la lectura neta de C2 (Δ +0,086, p 0,47; 0,983 < 1) y no por la partición de 3 regímenes que retiró A6;<br>• E02 queda acotado (A2);<br>• A1 lleva sus tres motivos;<br>• el 15/45 es de la v1 del detector de order blocks;<br>• el 0,8002 es el `pf_all` de la serie completa (forward 0,739);<br>• «~6,5×10⁸ evaluaciones por símbolo-pasada» pasa a «28–32 presets por símbolo»;<br>• la transferencia lleva el intervalo completo de C1 (incluye 0 y +0,30);<br>• E07 y la Lista de Cierre llevan su nivel de pre-registro (B y C) y E07 la discrepancia del límite de drawdown (−15/−20 % en el documento y en un comentario, −25 % en el test);<br>• la regla «placebo GBM» de la Lista de Cierre declara que C3 usó el suelo mixto de E05. | `README.md`; `HOW_TO_AUDIT.md`; `COMO_AUDITAR_ESTO.md`; `experimentos/README.md`; `experimentos/E01…E05, E07/README.md`; `harness/README.md`; `lista_cierre/README.md` | `2a2f7eb` |
| 2 | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md` vuelve a sus bytes sellados (sha256 `e4407617…`, commit `3b57151`). La nota que le añadió la v1.0.1 pasa a `cs_mom_sandbox/NOTA_v1.0.1_CS_MOM.md`. La comprobación de sellos de `prerregistros/README.md` §4 vuelve a dar **23/23** (daba 22/23 desde la v1.0.1). | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md`; `cs_mom_sandbox/NOTA_v1.0.1_CS_MOM.md`; `experimentos/E07_cs_momentum/README.md` | `721b79e` |
| 3 | `paper/ERRATA_working_paper_v1.0.0.md`: 16 erratas de los dos working papers v1.0.0 (el mismo texto del preprint SSRN 7085378), cada una con su fuente. Los working papers no se tocan. | `paper/ERRATA_working_paper_v1.0.0.md` | `2142a43` |
| 4 | `afirmaciones_respaldo.md`: 14 correcciones (REDACCIÓN OFICIAL §1, §5 y §6; filas L2, L4 y L5; afirmación 2, con el log de ONDO declarado ausente; 3(b); 4; 7; ROJO 1), cada una con su texto anterior literal y su fuente en la nueva sección «Correcciones v1.0.3». | `afirmaciones_respaldo.md` | el commit del bloque 4 |

| 5 | Canon línea a línea (DF-3, `CANON_v1.0.3.md` del paquete del caso):<br>• los datos W3 (`binance_w3_data`) dejan de llamarse «independientes»: son velas de futuros de Binance de la **misma ventana**, cuyo tercio forward la selección ya había visto como velas al contado; el pre-registro del Estudio los marca como solo «Parcial» intocados (L30). Cambia en la tabla (REDACCIÓN OFICIAL §6, C1, 3(a), afirmación 7, DISCREPANCIAS 4), en README, guías, `datos/REGENERAR.md` y las guías de E02, E16 y el índice;<br>• el intervalo de ETH de B8 es [11,5; 15,2] pp, no [11,5; 15,3] (redondeo de 0,15248);<br>• «listón honesto» pasa a «listón fijado para ella» (REDACCIÓN OFICIAL §3, afirmación 4, DISCREPANCIAS 2, README), alineado con el título del caso;<br>• fuera el superlativo «el de mayor respaldo académico» (L7, guía de E07): sin fuente bibliográfica en el archivo;<br>• «2 pasadas independientes» → «2 pasadas»; fuentes que faltaban en el barrido de contraejemplos.<br>Cada cambio de la tabla, con su texto anterior literal, en «Correcciones v1.0.3». Los documentos sellados o de registro que dicen lo mismo no se editan: `prerregistros/ERRATA_DOCUMENTOS_SELLADOS_v1.0.3.md` (10 erratas). `paper/ERRATA_working_paper_v1.0.0.md` gana las erratas 17 y 18. | `afirmaciones_respaldo.md`; `README.md`; `HOW_TO_AUDIT.md`; `COMO_AUDITAR_ESTO.md`; `datos/REGENERAR.md`; `experimentos/README.md`; `experimentos/E02, E07, E15, E16/README.md`; `prerregistros/ERRATA_DOCUMENTOS_SELLADOS_v1.0.3.md`; `paper/ERRATA_working_paper_v1.0.0.md` | el commit del bloque 5 |

Pendiente al publicar: la descripción del registro de Zenodo («across 31 presets, ~6.5×10^8 evaluations per pass») se corrige igual que el README; `CITATION.cff` (versión y fecha) y el DOI de versión se fijan en la publicación.

## v1.0.2 — 2026-10-14

Alinea el archivo con el manuscrito del caso enviado a PLOS ONE el 2026-10-13 (PONE-D-26-51403). **Ninguna cifra, intervalo ni veredicto cambia.** La REDACCIÓN OFICIAL de `afirmaciones_respaldo.md` es idéntica, carácter a carácter, a la de la v1.0.0. Solo cambian archivos `.md`, `CITATION.cff` y este `CHANGELOG.md` (ningún `.py`, `.json`, `.csv` ni parquet). Cada cambio se hizo con su artefacto primario delante.

| Bloque | Cambio | Archivos | Commit |
|---|---|---|---|
| 1a | «El único retorno neto positivo tras costes del proyecto es CS-MOM Curva C» pasa a «la única estrategia market-neutral neta positiva tras costes del proyecto»: el momentum solo largo (curva A, Sharpe 1,163), la pata larga del carry (+1,141) y el TSMOM diario (0,749) son positivos pero quedan por debajo de comprar y mantener (EW 1,443; 0,779 el TSMOM diario). Mismo cambio en la guía de auditoría (es/en) §2.6. Cifras: las que ya estaban en la tabla (L7, B1, B3 y afirmación 4). | `afirmaciones_respaldo.md` (afirmación 4); `HOW_TO_AUDIT.md`; `COMO_AUDITAR_ESTO.md` | `447bfdf` |
| 1b | La guía de auditoría (es/en) §2.6 seguía aplicando el 1,94 a la curva C. Ahora dice que la curva C falla sus criterios congelados (`cs_mom.py` L332-335: Sharpe ≥ 1,00, maxDD mejor que −25 %) y que el 1,94 (≈ EW + 0,5) es el listón de la curva A, como la tabla y la guía de E07 desde la v1.0.1. Barrido de «1.94»/«1,94» en todo el archivo: 34 apariciones en `.md`; fuera de las guías, solo los dos working papers v1.0.0 (`paper/working_paper_EN.md` y `_ES.md`, §5.3 y Tabla 1) lo aplican a la curva C, y se conservan sin tocar como documento fechado (como en la v1.0.1); el resto son la curva A (`cs_mom_sandbox/CS_MOM_PREREGISTRO.md`, `experimentos/E07_cs_momentum/README.md`, CONTEXTO), ratios corto/largo o factores de beneficio sin relación. | `HOW_TO_AUDIT.md`; `COMO_AUDITAR_ESTO.md` | `7f8517d` |
| 1c | La línea «Estado» de la afirmación 4 («tiene UN contraejemplo (CS-MOM Curva C)») pasa a nombrar los contraejemplos netos positivos tras costes: la curva C, única market-neutral, y las tres exposiciones largas por debajo de comprar y mantener (momentum solo largo, pata larga del carry, TSMOM diario). Los dos working papers v1.0.0 (`paper/`, es/en) reciben una nota de una línea bajo su sello de versión que remite a `afirmaciones_respaldo.md` y a este CHANGELOG para las correcciones posteriores; su texto y su sello («v1.0.0, 2026-07-07») no cambian. | `afirmaciones_respaldo.md` (afirmación 4); `paper/working_paper_ES.md`; `paper/working_paper_EN.md` | el commit 1c de la v1.0.2 (único commit posterior a `6f902d4`) |
| 2 | `CITATION.cff`: DOI de concepto 10.5281/zenodo.21229491 (resuelve a la última versión), versión 1.0.2, fecha 2026-10-14. README (es/en): v1.0.2 y DOI de concepto con la regla de cita (concepto + versión usada). Las menciones a 21229492 en `prerregistros/README.md` y en los dos working papers se conservan: son la cita de la v1.0.0 de entonces. | `CITATION.cff`; `README.md` | `3200128` |

## v1.0.1 — 2026-10-13

Corrección de erratas, rutas y descripciones de la v1.0.0, más hechos que faltaban en la tabla de respaldo. **Ninguna cifra, intervalo ni veredicto cambia.** La REDACCIÓN OFICIAL de `afirmaciones_respaldo.md` es idéntica, carácter a carácter, a la de la v1.0.0. Solo cambian archivos `.md`, `CITATION.cff` y este `CHANGELOG.md` (ningún `.py`, `.json`, `.csv` ni parquet). Cada cambio se hizo con su artefacto primario delante; el detalle, por nota, está en la sección «Correcciones v1.0.1» de `afirmaciones_respaldo.md`.

### Ya publicado en GitHub entre v1.0.0 y v1.0.1 (commit `5aa7aca`, 2026-07-07)

- `.gitattributes` nuevo (`* -text`): desactiva la conversión de fin de línea en el checkout. Sin él, un clon en Windows con `core.autocrlf=true` reescribe LF→CRLF y `ots verify` da un falso «File does not match original!» sobre los archivos anclados.
- `prerregistros/README.md` §4: los recibos publicados ya contienen la atestación definitiva en Bitcoin (bloque 956.927, 2026-07-06 14:29:58 UTC), con instrucciones de verificación sin nodo local y la nota sobre CRLF.
- **El zip de Zenodo v1.0.0 se generó desde el tag `v1.0.0` (commit `ae65eb4`), no desde ese commit:** no contiene `.gitattributes` y su `prerregistros/README.md` es el de 8.682 bytes, sin el §4. La v1.0.1 de Zenodo será, por tanto, la primera versión depositada que lleve esos dos cambios.

### Notas 1–10 (erratas del archivo detectadas al reparar el libro)

| # | Cambio | Archivos | Commit |
|---|---|---|---|
| 1 | La fila del 91 % citaba un informe que no existe en el archivo (`audit_v5_2_report_20260427_1844_utf8.txt`); la cifra está en `audit_v5_2_report_20260426_1106_utf8.txt` L30. Se declara que el script de la auditoría v4 (`audit_fidelity_v4.py`) no está en el archivo público. | `afirmaciones_respaldo.md` 5(a) | `07f32d9` |
| 2 | La tabla declara qué filtro usa para la suma de `funding_paid` (+0,118 USDT sobre las 591 filas con tamaño, el filtro de A9; −0,0188 USDT sobre las 736) y por qué. | `afirmaciones_respaldo.md` 5(c) | `5bb9558` |
| 3 | No aplica: la tabla no cita la alarma del 26-IV; se deja constancia de dónde están sus dos cifras en el informe del archivo (L31 y L49). | sección «Correcciones v1.0.1» | `ac9520a`, `1d53aa3` |
| 4 | TRX: el 97,06 % es de la certificación de la Capa 1 (30-V, documental, CONTEXTO) y el 98,24 % de `cert_fidelity_gate_W1500.json` (recalculado); la tabla dice cuál sostiene la afirmación. | `afirmaciones_respaldo.md` 5(a) | `92c1bb1` |
| 5 | No aplica: ninguna fila cita el 7–9 % del forense A10. | sección «Correcciones v1.0.1» | `ac9520a` |
| 6 | `CS_MOM_PREREGISTRO.md` conserva su cabecera de borrador; una nota bajo el título y otra en la guía de E07 dicen que lo congelado es `cs_mom.py` («CONGELADO 2026-06-29»), Nivel B. | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md`, `experimentos/E07_cs_momentum/README.md` | `d65d89d` |
| 7 | No es del archivo (es del libro): nada. | — | `ac9520a` |
| 8 | 145 de las 736 filas no registran `size_usdt` (la comisión estimada no las cobra) y 7 de ellas registran su pérdida solo en `pnl_pct`; el neto estimado de −1,7 USDT se presenta como la cota más generosa, junto al balance documental (~296–298 → 288,71 USDT). La cifra no se recalcula. | `afirmaciones_respaldo.md` 5(c); `auditoria_adversarial/README.md` (A9) | `de7170f` |
| 9 | La guía de E17 dice, como el propio veredicto C2, que su pre-registro es el del Nivel 3 original (`NIVEL3_CONFIRMACION_D3_DISENO_PREREGISTRO.md` L61–L62). | `experimentos/E17_nivel3_patas/README.md` | `a0efe8a` |
| 10 | El README enlaza el repositorio de GitHub (es/en) y dice que el historial `git` solo está allí. La relación en el registro de Zenodo se añade al publicar. | `README.md` | `2210fac` |

### §8 del encuadre del paper del caso

| Ítem | Cambio | Archivos | Commit |
|---|---|---|---|
| (a) | Datos y exchanges. La v1.0.0 decía «perps Binance top-45» para todo. Comprobado en cada runner: la búsqueda principal y 11 familias (E01–E05, E10, E12, E13, E16, E17, E18) usaron velas 1h de Binance **al contado** (`download_full_history.py` / `data_cache.py` con el mercado por defecto de ccxt; caché desde 2017); 7 (E06, E07, E08, E09, E11, E14, E15) usaron **perpetuos USDT-M** de data.binance.vision; la ejecución real fue en **perpetuos USDT-M de BingX**. La guía de E10 decía «datos diarios de data.binance.vision»; su runner lee `data_cache` 1h: corregida. | `afirmaciones_respaldo.md` (A8); `README.md` (formulación congelada y limitación 3, es/en); `datos/REGENERAR.md` §1 y §3; `experimentos/E10_tsmom_diario/README.md`; `CITATION.cff` (abstract) | `79521aa` (CITATION en el commit de versión) |
| (b) | El 1,94 (≈ EW + 0,5) es el listón de la curva A del CS-MOM (`cs_mom.py` L329), no el de la curva C. La curva C se juzga con sus criterios congelados (L332–335: \|β\| ≤ 0,15, Sharpe ≥ 1,00, maxDD > −25 %, Sharpe 2024 > 0) y falló Sharpe y drawdown; el veredicto no cambia. «Protocolo declarado en el propio doc» pasa a referirse al código. | `afirmaciones_respaldo.md` (afirmación 4); `experimentos/E07_cs_momentum/README.md` | `a39989e` |
| (c) | Entran en la tabla, con artefacto: los 39 auditores (dos pasadas); la diferencia de precios entre exchanges (≈ 0,113 %, CONTEXTO §0.6.1); el funding realizado (≈ 0,0023 %/operación, FASE_A §A9); y la Sharpe deflactada implementada y probada en seco pero no aplicada a los veredictos (`regime_walk_forward.py`, `_R1_DSR_METHOD = 'none'`; ROADMAP). | `afirmaciones_respaldo.md`, «Hechos añadidos a la tabla» | `4a2117e` |

### Dos líneas antes de publicar (ARCHIVO-1c, commit `8aa7f05`)

- `README.md` (es/en): bajo el bloque «formulación congelada», la nota «Congelada el 2026-07-06; la v1.0.1 corrige en ella solo la descripción de los datos y el exchange (ver CHANGELOG), ninguna cifra.»
- `auditoria_adversarial/README.md` (celda A8) y `cierre_definitivo_20260702/FASE_A_correcciones_documentales.md` (§A8): línea de remisión «(v1.0.1: el venue exacto por familia está en afirmaciones_respaldo.md, matiz A8; esta entrada se conserva como registro de la meta-auditoría.)». Nada más de esos archivos cambia.

### Versión

- `CITATION.cff`: `version` 1.0.1, `date-released` 2026-10-13; en el abstract, «Binance top-45 perpetuals» pasa al reparto de §8(a). El título y el DOI no cambian.
- `README.md`: «working paper v1.0.0» → v1.0.1, con enlace a este CHANGELOG.
- Este `CHANGELOG.md`.

## v1.0.0 — 2026-07-07

Publicación inicial. Tag `v1.0.0` (commit `ae65eb4`); depósito en Zenodo, DOI 10.5281/zenodo.21229492; sello OpenTimestamps en el bloque 956.927 de Bitcoin.
