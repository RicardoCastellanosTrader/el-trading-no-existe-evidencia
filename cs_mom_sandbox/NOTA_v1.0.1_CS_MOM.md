# Nota sobre `CS_MOM_PREREGISTRO.md` (v1.0.1, trasladada aquí en la v1.0.3)

`CS_MOM_PREREGISTRO.md` es uno de los 23 documentos sellados con OpenTimestamps el 2026-07-06 (`prerregistros/ots/prerregistros_manifest_20260706.txt`). En la v1.0.1 se le añadió una nota bajo el título; eso cambió sus bytes y la comprobación del sello (`prerregistros/README.md` §4) dejó de dar 23/23. En la v1.0.3 el documento vuelve a sus bytes sellados (sha256 `e44076175a1ba8b3be660e667497101b3bc01425c25a6da560bacfeb08ca62f3`, commit `3b57151`) y la nota vive en este archivo aparte. Regla: lo sellado no se edita; notas, aclaraciones y erratas van en archivos aparte.

Texto de la nota de la v1.0.1, sin cambios:

> **Nota v1.0.1 (2026-10-13).** Este documento conserva su cabecera de borrador («BORRADOR v0, PENDIENTE FREEZE») y no debe leerse como un pre-registro congelado. Lo congelado es el código: `cs_mom.py` («CONGELADO 2026-06-29», bloque `--- CONGELADO ---`, con el protocolo benchmark-primero y los criterios de veredicto de las curvas A y C). Es un pre-registro de **Nivel B** (documental, commit conjunto `3b57151f`, 2026-06-29): ver `../prerregistros/README.md`.


Añadido en la v1.0.3: el límite de drawdown no es coherente en el registro. La sección de veredicto de este documento (L118 y L122) y un comentario del código (`cs_mom.py` L334) dan un objetivo de −15 a −20 %; el test del código (`cs_mom.py` L334) aplicó −25 %, el más permisivo. El resultado de la curva C (−27,4 %; `results/curves.json`, `maxdd_pct` −27.39) falla los dos.
