# Pre-registros: qué prueban los timestamps, qué no, y cómo verificarlo

Este directorio documenta la disciplina de pre-registro de los 18 experimentos (E01–E18) y su verificabilidad temporal. Los documentos de pre-registro viven en sus rutas originales del árbol (no se movieron: mover los archivos rompería la trazabilidad de `git log --follow`); aquí está la taxonomía, la tabla completa y los sellos externos.

**Este README está escrito para el lector hostil.** La afirmación pública es exactamente esta: *18 experimentos con pre-registro documental; precedencia temporal criptográficamente verificable en git para 3 de ellos; reproducibilidad completa (código + datos regenerables + resultados) para los 18*. Ni más, ni menos.

---

## 1. Qué prueba un timestamp de git — y qué no

Los timestamps de git son **auto-declarados**: los fija la máquina del autor y pueden falsificarse. Lo que un commit SÍ garantiza es la **integridad de contenido** (el hash sella el árbol completo) y la **consistencia interna** de la cadena (cada commit ancla a sus padres). Por eso este proyecto no descansa solo en git:

1. **Sello OpenTimestamps (2026-07-06)** — ancla criptográfica externa en la blockchain de Bitcoin. Ver §4.
2. **DOI de Zenodo** — snapshot con timestamp de tercero en el momento de la publicación.
3. **La asimetría del incentivo** — ver §3.

## 2. Taxonomía de verificabilidad (Niveles A/B/C)

### Nivel A — precedencia temporal verificable en git (3 de 18)

El commit que introduce el pre-registro es estrictamente anterior al commit que introduce los resultados.

| Exp | Pre-registro | Commit prereg | Commit resultados | Intervalo |
|-----|--------------|---------------|-------------------|-----------|
| E01 Campaña Edge Real | `audit_forense_gap_20260612/CAMPAÑA_EDGE_REAL_FASE0_PREREGISTRO.md` | `d94123d` 2026-06-13 | `6b396ac` 2026-06-16 (`VEREDICTO_FASE1.md`) | 3 días |
| E03 Nivel 3 — D3 régimen | `audit_forense_gap_20260612/NIVEL3_CONFIRMACION_D3_DISENO_PREREGISTRO.md` | `fac92c01` 2026-06-16 | `68ecff2f` 2026-06-21 (`VEREDICTO_NIVEL3_D3.md`) | 5 días |
| E05 Exp#2 order block | `analysis_scripts/atribucion_componentes_20260626/PREREGISTRO_EXP2_ORDERBLOCK.md` (v1) / `PREREGISTRO_EXP2_V3_FINAL.md` (v3) | v1 `76a09db4` 12:01 / v3 `25b50930` 17:19 (2026-06-26) | v1 `8c72516a` 12:08 / v3 `8b9bf2a0` 17:37 | **7–18 minutos** |

**Honestidad sobre E05:** con intervalos de minutos, el ORDEN es demostrable pero la "congelación previa" descansa en el intervalo — un lector escéptico puede descontar E05 y quedarse con E01/E03. La versión intermedia v2 (`PREREGISTRO_EXP2_V2_GATILLO.md`, `2b0f96b1`) documenta además una retractación en tiempo real: la v1 (detector ICT estrecho) se declaró no representativa del criterio real y se re-formalizó ANTES del barrido v3.

Verificación (cualquier fila):
```bash
git log --format='%h %ad %s' --date=iso --  "<ruta prereg>" "<ruta veredicto>"
```

### Nivel B — pre-registro documental, commit conjunto (4 de 18)

El documento de pre-registro existe con criterios congelados por escrito (hipótesis, métrica cardinal, listones, zonas de veredicto) pero entró en el MISMO commit que los resultados. Git no puede demostrar la precedencia; la estructura interna de los documentos (secciones de pre-registro redactadas en futuro, veredicto añadido en secciones finales) y el diario de laboratorio la documentan.

| Exp | Pre-registro | Commit |
|-----|--------------|--------|
| E02 Estudio de Capacidad | `audit_forense_gap_20260612/ESTUDIO_CAPACIDAD_INFORMACION_FASE0_PREREGISTRO.md` | `06091df3` 2026-06-16 |
| E04 Exp#1 cruces de medias | `analysis_scripts/atribucion_componentes_20260626/PREREGISTRO_EXP1_MEDIAS.md` | `d5ae6c81` 2026-06-26 |
| E06 MFE cascadas | `mfe_sandbox/MFE_FASE_EDGE_PREREGISTRO.md` (veredicto embebido §13) | `3b57151f` 2026-06-29 |
| E07 CS-MOM | `cs_mom_sandbox/CS_MOM_PREREGISTRO.md` (veredicto embebido §10) | `3b57151f` 2026-06-29 |

### Nivel C — cierre/retests en commit único (11 de 18)

Toda la Lista de Cierre Definitivo (pre-registros B1–B8, retests C1–C3, runners y resultados) entró en **un único commit** al completarse: `65b99c81` 2026-07-03.

| Exp | Pre-registro / doc |
|-----|--------------------|
| E08 B1 funding-carry | `cierre_definitivo_20260702/B1_funding_carry_PREREGISTRO.md` |
| E09 B2 reversal corto | `cierre_definitivo_20260702/B2_reversal_corto_PREREGISTRO.md` |
| E10 B3 TSMOM diario | `cierre_definitivo_20260702/B3_tsmom_diario_PREREGISTRO.md` |
| E11 B4 low-vol / BAB | `cierre_definitivo_20260702/B4_low_vol_bab_PREREGISTRO.md` |
| E12 B5 lead-lag BTC→alts | `cierre_definitivo_20260702/B5_lead_lag_PREREGISTRO.md` |
| E13 B6 estacionalidad reloj | `cierre_definitivo_20260702/B6_estacionalidad_PREREGISTRO.md` |
| E14 B7 open interest | `cierre_definitivo_20260702/B7_open_interest_PREREGISTRO.md` |
| E15 B8 MFE squeeze | `cierre_definitivo_20260702/B8_mfe_squeeze_PREREGISTRO.md` |
| E16 C1 potencia de N2 | `cierre_definitivo_20260702/C1_N2_potencia_VEREDICTO.md` (prereg embebido) |
| E17 C2 Nivel3 patas omitidas | `cierre_definitivo_20260702/C2_nivel3_patas_omitidas_VEREDICTO.md` |
| E18 C3 ablación Exp#2 | `cierre_definitivo_20260702/B_C3_note.md` |

En los Nivel C la disciplina fue la regla operativa de la lista de cierre ("mini-pre-registro congelado ANTES de resultados, métrica cardinal a priori sin pivote" — ver `lista_cierre/`) y así lo registra el diario; git solo puede demostrar que todo existía el 2026-07-03.

## 3. La asimetría del incentivo (léase antes de descontar los Niveles B/C)

**Los 18 veredictos son negativos o no-dignos.** El fraude de pre-registro que la taxonomía no puede excluir sería: el autor corrió el experimento, vio el resultado, y escribió después un "pre-registro" a medida. Ese fraude sirve para fabricar POSITIVOS (elegir la métrica que salió bien). Aquí los resultados son adversos al sistema del propio autor, a su tesis previa y a su cuenta de trading real: quien quiera sostener que los timestamps están falsificados debe explicar **qué gana el autor fabricando evidencia de que su propio sistema no funciona**. Además, la meta-auditoría adversarial (39 agentes ×2; `auditoria_adversarial/`) buscó específicamente señales positivas suprimidas y no halló ninguna; el mejor candidato (CS-MOM Curva C, neta-positiva sub-listón) está declarado en portada.

## 4. Anclaje externo: OpenTimestamps + Zenodo

El 2026-07-06 — antes de construir este repositorio público — se sellaron con **OpenTimestamps** (agregadores → blockchain de Bitcoin) dos archivos, publicados en [`ots/`](ots/):

1. **`head_state_20260706.txt`** — el hash del HEAD del repo original privado y las puntas de sus 34 ramas. Como un hash de commit sella merkle-style todo el historial, este sello ancla la EXISTENCIA de todo el árbol y su historia a fecha 2026-07-06.
2. **`prerregistros_manifest_20260706.txt`** — sha256 del contenido exacto commiteado de los 23 documentos de pre-registro/veredicto.

**Cadena de verificación en este repo público:** este repositorio es un clon del original con PII filtrada (`git filter-repo`), lo que reescribe los hashes de commit — PERO el filtrado no tocó ninguno de los 23 documentos, así que sus sha256 de contenido son idénticos. Verifícalo:

```bash
# 1. Recomputa los sha256 de los 23 documentos en ESTE repo y compáralos con el manifiesto sellado:
git -c core.quotepath=off ls-files | grep -iE 'PREREG|VEREDICTO|B_C3_note' | sort | while IFS= read -r f; do
  echo "$(git show "HEAD:$f" | sha256sum | cut -d' ' -f1)  $f"
done
# → deben coincidir 23/23 con las líneas de ots/prerregistros_manifest_20260706.txt

# 2. Verifica el sello del manifiesto contra Bitcoin (requiere cliente ots):
ots verify ots/prerregistros_manifest_20260706.txt.ots -f ots/prerregistros_manifest_20260706.txt
```

**Estado de la atestación:** ambos recibos publicados ya contienen la atestación definitiva en Bitcoin — **bloque 956927** (minado 2026-07-06 14:29:58 UTC), merkle root `86ba8b514a698069a7e0b05bc8ead67dc2aadb010185111049f4185ef1f8fe72`. `ots verify` completo requiere un nodo Bitcoin local; sin nodo, `ots info <archivo>.ots` muestra la `BitcoinBlockHeaderAttestation(956927)` y el merkle root puede cotejarse contra cualquier explorador público (p. ej. `https://blockstream.info/api/block-height/956927` → hash del bloque → `merkle_root`).

**Nota Windows (CRLF):** los sellos y los sha256 comprometen los **bytes exactos commiteados**. Este repo desactiva la conversión de fin de línea vía `.gitattributes` (`* -text`); si tu clon es anterior a ese archivo o fuerza `core.autocrlf=true`, el checkout reescribe LF→CRLF y `ots verify` dará un falso "File does not match original!". En ese caso extrae los bytes exactos antes de verificar:

```bash
git show HEAD:prerregistros/ots/prerregistros_manifest_20260706.txt > /tmp/manifest.txt
ots verify ots/prerregistros_manifest_20260706.txt.ots -f /tmp/manifest.txt
```

El snapshot de Zenodo añade el **DOI** con timestamp de tercero sobre el conjunto completo: [10.5281/zenodo.21229492](https://doi.org/10.5281/zenodo.21229492).

## 5. `commit_map_filtrado.txt`

El diario de laboratorio (`CONTEXTO_PROYECTO_TRADING.md`) y varios documentos citan hashes del repo original (pre-filtrado). [`commit_map_filtrado.txt`](commit_map_filtrado.txt) traduce cada hash original → hash de este repo público (224 líneas, formato `original público`). Ejemplo: el commit de cierre `fa72edcf…` del diario es `65b99c81…` aquí.

```bash
grep '^fa72edcf' commit_map_filtrado.txt
```
