# EXP#2 v3 ORDER BLOCK (criterio real Ricardo) — TABLA T3.2-Exp2

VEREDICTO por la BRECHA real-vs-placebo (no PF absoluto).

## 1) EL JUEZ — BRECHA real vs placebo (pf_all full-series, misma base)
   placebo floor (median 6 series) = 0.989 | por serie: PLBGB1:0.90 PLBSH1:1.66 PLBGB2:1.04 PLBSH2:1.27 PLBGB3:0.94 PLBSH3:0.89
   real median pf_all (45 sym)     = 0.800
   >>> BRECHA GEOMÉTRICA (real - placebo) = -0.189
   real sym con pf_all > placebo floor: 6/45

## 2) EDGE AS-OF FORWARD (pf_fwd holdout) — primario
   real median pf_fwd = 0.739 | mean = 0.718 | %pf<1 = 84%
   n con CI_low>1.0          = 0/45
   n con CI_low>placebo_floor(0.99) = 0/45  <-- bate geometría
   brecha fwd (median pf_fwd - floor) = -0.250

## 3) ROBUSTEZ (median pf_all real - median placebo por config)
  near  frac   P    real  placebo  brecha
  0.03  0.75  10   0.775    1.118  -0.344
  0.05  0.75  10   0.800    0.989  -0.189 <-PRIM
  0.05  0.75  30   0.714    1.019  -0.305
  0.05  0.75  50   0.668    1.008  -0.340
  0.05   0.9  10   0.861    1.067  -0.207
  0.05   1.0  10   0.878    1.032  -0.154
  0.07  0.75  10   0.844    1.029  -0.185

## 4) PER-CLUSTER (diagnóstico, primario, median pf_fwd real)
   cluster 0: median pf_fwd = 0.754
   cluster 1: median pf_fwd = 0.800
   cluster 2: median pf_fwd = 0.584

## 5) DISTRIBUCIÓN real pf_fwd primario
   top5:    QNT:1.44[0.73-2.86] | BCH:1.38[0.78-2.32] | BTC:1.12[0.53-2.15] | SOL:1.09[0.67-1.72] | LINK:1.08[0.68-1.66]
   bottom5: ALGO:0.40 | XLM:0.34 | RENDER:0.26 | ENA:0.17 | POL:0.10

## 6) VEREDICTO (sobre la BRECHA)
   brecha pf_all=-0.189 | brecha fwd=-0.250 | sym CI>floor=0/45
   => intermedio: leer robustez + per-cluster + consistencia.