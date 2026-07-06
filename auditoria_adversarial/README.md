# Auditoría adversarial de los veredictos (meta-auditoría, 2026-07-01/02)

Antes de cerrar el proyecto, los 7 veredictos del arco principal se sometieron a una **meta-auditoría adversarial multiagente**: 39 agentes de IA (Claude, Anthropic) en 2 pasadas independientes, con el mandato explícito de refutar cada veredicto, recomputar los números desde los artefactos primarios y buscar señales positivas suprimidas.

**Resultado global: 7/7 veredictos "correcto con matices" — ninguno se voltea, ningún auditor halló una señal real suprimida.** Pero la auditoría encontró sub-afirmaciones sobre-vendidas y 2 bugs numéricos, y TODAS las correcciones se aplicaron al registro. El documento primario es [`../cierre_definitivo_20260702/FASE_A_correcciones_documentales.md`](../cierre_definitivo_20260702/FASE_A_correcciones_documentales.md).

## Las 9 correcciones (A1–A9), en una línea cada una

| # | Qué se corrigió |
|---|-----------------|
| A1 | Edge Real, ancla A2: "EDGE AUSENTE" → "no-concluyente lean-negativo" (CI frágil a 0.04 de la frontera; la conclusión titular no depende de A2) |
| A2 | Estudio de Capacidad: D6 "muerta" → "muerta para re-rankear dentro de la shortlist" (restricción de rango); D4 → "UNTESTED"; el eslabón "+0.30→−0.05" era no-concluyente infra-potenciado (→ motivó el retest C1) |
| A3 | Exp#1: "≤ ruido" → "indistinguible del ruido y sub-breakeven" (el floor estaba inflado por una serie placebo inválida, PLBSH3) |
| A4 | Exp#2: "la línea MÁS FUERTE" → "negativa con signo robusto, magnitud no ganada"; certificación no-look-ahead del smoke irreproducible (inspección independiente sin fuga hallada) |
| A5 | MFE: el gap de supervivencia 23-vs-3pp estaba **inflado ~3-4× por un confound de volatilidad** → ~+6-8pp ≈ +1pb bruto; "peor que aleatorio" era slippage no-matched; funding "REFUTADO" → "NO CONFIRMADO"; **pivote de métrica post-hoc anotado como desviación procesal** |
| A6 | Nivel 3: "ε²=0.574 era artefacto" → "no contradice la convergencia" (partición selectiva post-hoc detectada; "no construir Frame 3" se sostiene por deployabilidad neta <1) |
| A7 | Convergencia: "7 líneas independientes" → "**~3 clusters efectivos**" (L1-L5 comparten kernel/datos/placebos; L6, L7 ortogonales) |
| A8 | Alcance: el cierre vale para perps Binance top-45, 1s/1h/12h/diario, 2023-2026, costes taker — **no es un negativo atemporal** |
| A9 | **Bug numérico corregido**: ρ de D5 publicado +0.2345 estaba corrupto por NaN silenciosos → valor verdadero +0.7465 (refuerza "mecánica"). + Contraste empírico del fee 0.10% RT contra los 736 fills reales: PnL registrado = bruto exacto, funding realizado negligible (~0.0023%/trade) → el supuesto de coste es fiel-a-conservador |

Léase el patrón: las correcciones van **en ambas direcciones** (algunas debilitan sub-claims, A9 y A3 refuerzan otras), y el proyecto las publicó todas en lugar de citarse a sí mismo sin corregir. Los números que este repositorio usa públicamente son los POST-corrección (ver `../afirmaciones_respaldo.md`).

## Nota honesta sobre reproducibilidad de esta auditoría

**Los transcripts crudos de los 39 agentes no se conservaron** (eran sesiones de trabajo, fuera del árbol git). Lo que queda — y lo único que se afirma — es el documento de correcciones con cada hallazgo aplicado al registro. Esta auditoría se declara por tanto como **auditoría interna documentada**, no como artefacto reproducible: su valor es que las correcciones existen, están aplicadas, y cualquiera puede repetir el ejercicio (los artefactos primarios y la guía `../COMO_AUDITAR_ESTO.md` están precisamente para eso).
