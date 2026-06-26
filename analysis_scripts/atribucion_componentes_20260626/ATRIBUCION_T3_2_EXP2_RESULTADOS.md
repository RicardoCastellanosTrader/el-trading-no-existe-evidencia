# EXPERIMENTO #2 — ORDER BLOCK — TABLA DE ATRIBUCION (T3.2-Exp2)

VEREDICTO por la BRECHA real-vs-placebo, NO por el PF absoluto (caveat geometrico).

## 1) EL JUEZ — BRECHA REAL vs PLACEBO (pf_all full-series, misma base)
   placebo floor (median pf_all 6 series, geometria del setup) = 1.230
   placebo por serie: PLBGB1:1.23 PLBSH1:1.15 PLBGB2:1.26 PLBSH2:1.23 PLBGB3:1.36 PLBSH3:1.21
   real median pf_all (45 sym)                                  = 1.259
   >>> BRECHA GEOMETRICA (real - placebo) = +0.029
   real sym con pf_all > placebo floor: 29/45

## 2) EDGE AS-OF FORWARD (pf_fwd, holdout) — primario k=2/W=50/R=2
   real median pf_fwd = 1.163 | mean = 1.187 | %pf_fwd<1 = 9%
   n con CI_low>1.0 (breakeven)        = 15/45
   n con CI_low>placebo_floor (1.23) = 1/45   <-- beats geometria
   real median pf_fwd (1.163) vs placebo floor (1.230) -> brecha fwd = -0.067

## 3) ROBUSTEZ — brecha (real_median - placebo_median) pf_all por (k,W,R)
    k    W    R    real  placebo  brecha
  1.5   30  1.5   1.332    1.316  +0.016
  1.5   30  2.0   1.167    1.155  +0.012
  1.5   30  3.0   1.067    1.005  +0.062
  1.5   50  1.5   1.375    1.318  +0.057
  1.5   50  2.0   1.199    1.160  +0.039
  1.5   50  3.0   1.085    1.011  +0.073
  1.5   80  1.5   1.395    1.331  +0.064
  1.5   80  2.0   1.213    1.165  +0.048
  1.5   80  3.0   1.090    1.008  +0.082
  2.0   30  1.5   1.405    1.426  -0.021
  2.0   30  2.0   1.221    1.229  -0.008
  2.0   30  3.0   1.084    1.065  +0.019
  2.0   50  1.5   1.456    1.442  +0.015
  2.0   50  2.0   1.259    1.230  +0.029 <-PRIM
  2.0   50  3.0   1.112    1.064  +0.048
  2.0   80  1.5   1.486    1.495  -0.009
  2.0   80  2.0   1.278    1.248  +0.030
  2.0   80  3.0   1.127    1.066  +0.061
  2.5   30  1.5   1.521    1.385  +0.136
  2.5   30  2.0   1.290    1.147  +0.143
  2.5   30  3.0   1.135    1.040  +0.096
  2.5   50  1.5   1.554    1.377  +0.177
  2.5   50  2.0   1.346    1.168  +0.179
  2.5   50  3.0   1.177    1.064  +0.112
  2.5   80  1.5   1.609    1.409  +0.200
  2.5   80  2.0   1.368    1.229  +0.139
  2.5   80  3.0   1.190    1.065  +0.125

## 4) PER-CLUSTER (diagnostico) — median pf_fwd real, primario
   cluster 0: median pf_fwd = 1.183 (n_sym=45)
   cluster 1: median pf_fwd = 1.202 (n_sym=45)
   cluster 2: median pf_fwd = 1.036 (n_sym=45)
   (prueba causal: el OB de reversion deberia vivir en regimen de reversion/lateral, no tendencial)

## 5) DISTRIBUCION real pf_fwd primario (mejores/peores)
   top5:    VET:1.66[1.37-2.03] | SHIB:1.49[1.15-1.95] | FIL:1.46[1.17-1.87] | HBAR:1.43[1.17-1.78] | DOGE:1.40[1.16-1.66]
   bottom5: APT:1.00 | LTC:1.00 | LINK:0.96 | SUI:0.78 | ENA:0.66

## 6) VEREDICTO (sobre la BRECHA, no el PF absoluto)
   brecha geometrica pf_all = +0.029 | brecha fwd = -0.067 | sym que baten geometria (CI>floor) = 1/45
   => placebo ~= real -> el PF es GEOMETRIA del setup, NO liquidez. VEREDICTO NEGATIVO (5a linea).