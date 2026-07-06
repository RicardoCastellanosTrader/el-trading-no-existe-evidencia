# Declaración de asistencia de IA

*English version: [`AI_ASSISTANCE.md`](AI_ASSISTANCE.md)*

Este proyecto se realizó con asistencia extensiva de inteligencia artificial — **Claude y Claude Code (Anthropic)**, operando como agentes dirigidos. Esta declaración existe porque la asistencia de IA **forma parte del método del proyecto, no es una nota al margen**: lo que aquí se documenta es, entre otras cosas, un caso de investigación empírica dirigida por un no-programador mediante agentes de IA, con los controles de honestidad (pre-registros, gates anti-look-ahead, placebos, auditoría adversarial) construidos precisamente para que esa delegación técnica no comprometiera la validez de los resultados.

## Qué hizo la IA (como agente dirigido)

- La **implementación y ejecución técnica** de todo el código del proyecto: kernels GPU, pipeline de walk-forward, bot de producción, harness de validación, experimentos E01–E18 y su infraestructura.
- La **auditoría adversarial** de los propios veredictos (protocolo multiagente de 39 agentes ×2 pasadas; ver [`auditoria_adversarial/`](auditoria_adversarial/README.md)).
- La **curación de este repositorio**: sanitización del historial, estructura, guías de auditoría y verificación de cada número contra su artefacto primario.
- **Asistencia en la redacción del manuscrito** ([`paper/`](paper/)), generado a partir de la tabla de afirmaciones verificadas ([`afirmaciones_respaldo.md`](afirmaciones_respaldo.md)) — nunca desde memoria ni desde resúmenes.

Todo ello **bajo dirección, revisión y aprobación del autor**, tarea a tarea.

## Qué es del autor

- Las **preguntas de investigación** y las hipótesis (incluida la objetivación de su propio criterio de trading, E05).
- Las **decisiones de diseño** metodológico y de infraestructura.
- La **aprobación de cada pre-registro** antes de su ejecución.
- La **firma de cada veredicto**.
- La **responsabilidad plena de todas las afirmaciones publicadas** en este repositorio y en el manuscrito.

## Nota normativa

Conforme a los criterios estándar de autoría académica (**ICMJE, COPE**), las herramientas de IA no cumplen los criterios de autoría: no pueden asumir responsabilidad sobre el trabajo ni aprobar su versión final. El autor único de este trabajo es **Ricardo Castellanos**, que asume dicha responsabilidad en su totalidad.
