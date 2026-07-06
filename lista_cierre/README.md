# Lista de Cierre Definitivo y criterio de parada

El proyecto no se abandonó: se **cerró por criterio de parada pre-acordado y cumplido**. Este directorio apunta a los documentos primarios del cierre.

## El documento primario

[`../cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md`](../cierre_definitivo_20260702/FASE_D_CIERRE_DEFINITIVO.md) — el cierre formal, con las fases:

- **FASE A** — correcciones documentales de la meta-auditoría (ver [`../auditoria_adversarial/`](../auditoria_adversarial/README.md)).
- **FASE B** — los 8 ejes restantes que la meta-auditoría señaló como no explorados, todos con mini-pre-registro y todos negativos: B1 funding-carry, B2 reversal corto, B3 TSMOM diario, B4 low-vol/BAB, B5 lead-lag BTC→alts, B6 estacionalidad de reloj, B7 open interest, B8 MFE squeeze (E08–E15 en [`../experimentos/`](../experimentos/)).
- **FASE C** — 3 retests de blindaje de los eslabones débiles detectados: C1 (potencia real del test de transferencia), C2 (patas omitidas de Nivel 3), C3 (ablación del order block) — E16–E18.
- **FASE D** — el cierre.

## Las reglas de la lista (congeladas antes de ejecutarla)

1. Lista **congelada y finita** — se acordó ANTES de correr FASE B/C que ningún resultado generaría nuevos experimentos: un positivo modesto = hallazgo limitado-por-capital; un negativo = suma al mapa.
2. Mini-pre-registro congelado ANTES de resultados; **métrica cardinal a priori, sin pivote** (la lección procesal de A5).
3. El CI decide, no el punto-estimado; cluster-bootstrap cross-símbolo; placebo GBM puro.
4. Coste local $0, VPS parados, sandboxes aislados, producción intacta.

**Al vaciarse la lista, el criterio de parada quedó cumplido y el proyecto CERRADO (2026-07-03).** Eso es lo que este repositorio documenta.

## Las 5 puertas cerradas POR ACCESO (no por veredicto)

La distinción importa: estas 5 no se probaron y el cierre lo declara — con la razón exacta registrada en FASE_D §D2. Es la evidencia de la tesis "lo único que no probé es dejar de ser retail":

| Puerta | Razón exacta registrada |
|--------|------------------------|
| Carry delta-neutral spot-perp | "edge casi seguro real (cash-and-carry, base de Ethena) pero irrelevante a 289 USDT (5-15%/año sobre 289 = 15-45 USDT/año menos fees de 2 patas). Test barato pero negocio inviable a esta escala." |
| VRP opciones (Deribit) | "el respaldo académico más fuerte, pero exige margen ≫ 289 USDT + acceso EU/MiCA dudoso + riesgo de cola de vender vol sin colchón = ruina. Edge probablemente real, INVIABLE para este operador." |
| Market-making / provisión de liquidez | "no falsable en backtest sin L2 completo (Tardis ~500 USD/mes o grabar meses); latencia doméstica = adverse selection; 289 USDT no alcanza tier maker. INVIABLE, cerrada por argumento." |
| Arbitraje cross-exchange | "spread comprimido a bps; con 289 USDT fragmentados = céntimos/evento vs fees de retirada; killer = capital fragmentado + latencia. INVIABLE." |
| On-chain flows | "literatura marginal post-2021 + riesgo de look-ahead del vendor (métricas revisadas retroactivamente) + suscripción 100-1200 USD. No digno." |

Nótese la honestidad del registro: en dos de ellas (carry delta-neutral, VRP) el propio documento declara que **el edge probablemente existe** — lo que falta es capital y acceso. El cierre no dice "no hay edge en ningún sitio"; dice "no hay edge alcanzable desde esta silla".
