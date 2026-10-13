# CHANGELOG

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

### Versión

- `CITATION.cff`: `version` 1.0.1, `date-released` 2026-10-13; en el abstract, «Binance top-45 perpetuals» pasa al reparto de §8(a). El título y el DOI no cambian.
- `README.md`: «working paper v1.0.0» → v1.0.1, con enlace a este CHANGELOG.
- Este `CHANGELOG.md`.

## v1.0.0 — 2026-07-07

Publicación inicial. Tag `v1.0.0` (commit `ae65eb4`); depósito en Zenodo, DOI 10.5281/zenodo.21229492; sello OpenTimestamps en el bloque 956.927 de Bitcoin.
