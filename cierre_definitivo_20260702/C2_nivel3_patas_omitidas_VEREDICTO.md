# C2 — Nivel 3: patas pre-registradas OMITIDAS (retest de blindaje) — VEREDICTO

**2026-07-02.** Pre-registro = el original Nivel 3 (`NIVEL3_..._PREREGISTRO.md` L61 cartera condicional-vs-agnóstica + L62 placebo wrong-match), que nunca se reportaron. Computadas desde los 13 sealed JSONs (`nivel3_resmoke_trades_*_2025-05-01_data_cache.json`), SIN GPU. Métrica NETA (fee 0.10pp RT), como el freeze.

## Leg (a) — Placebo wrong-match (calibrador de especificidad)
- Δ pooled observado (PF_match − PF_mismatch, neto) = **+0.0863**.
- Permutación de la etiqueta 'home' (2000 reps, reasigna aleatoriamente qué cluster es el "hogar" de cada specialist): null media **+0.0037**, p95|Δ| 0.236, **p_permutación = 0.4735**.
- **Resultado:** el emparejamiento real régimen↔specialist **NO es más específico que uno aleatorio** (p=0.47). El +0.086 observado es ruido dentro de la distribución nula. **Confirma la reconstrucción del auditor (pseudo ≈ real): el instrumento D3 carece de especificidad.**

## Leg (b) — Cartera régimen-condicional vs agnóstica
- PF condicional (solo trades MATCH, régimen-gated) = **0.9828** (n=1674).
- PF agnóstica (todos los trades del specialist, sin gate) = **0.9308** (n=4219).
- Condicional > agnóstica (+0.052) PERO **ambas < 1.0 neto** → `gate_regimen_ayuda = FALSE`.
- **Resultado:** condicionar por régimen sube el PF marginalmente (0.93→0.98) pero se queda **sub-breakeven** → no añade valor desplegable.

## VEREDICTO C2
Las dos patas omitidas **CONFIRMAN y CALIBRAN** el "D3 NO CONFIRMADO / no construir Frame 3": (i) sin especificidad (p_perm 0.47 — real indistinguible de aleatorio), (ii) el gate régimen-condicional mejora ~0.05 de PF pero permanece <1.0 neto. Cierra el gap de calibración de potencia que el auditor señaló y convierte el "no contradice la convergencia" (A6) en una **no-confirmación positivamente calibrada** (ruido + sub-breakeven, ni adverso ni soportivo). Ningún re-run GPU necesario.

Detalle por celda en `results_C2.json` (THETA Δ=−0.48 y XRP Δ=+0.28 = las colas; el pooled +0.086 es ruido per la permutación).
