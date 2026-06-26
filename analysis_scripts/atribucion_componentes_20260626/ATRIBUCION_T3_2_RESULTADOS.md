# EXPERIMENTO #1 — TABLA DE ATRIBUCION (T3.2)

Benchmark sistema completo as-of GLOBAL = 0.702 [0.44, 1.07]. Breakeven=1.0.

## 1) TF PRIMARIO (10/55, hyst 0) — por tipo de media (45 simbolos)

tipo         n n_edge  med_pf_fwd    mean   %pf<1  med_pf_tr
Tenkan      45      3       0.955   0.979     56%      0.940
VWMA        45      3       0.949   0.977     67%      0.914
VIDYA       45      4       0.947   1.192     58%      1.676
SMA         45      2       0.922   0.969     64%      0.964
TEMA        45      0       0.922   0.924     73%      0.892
T3          45      2       0.917   0.964     69%      0.957
ZLEMA       45      0       0.916   0.927     80%      0.943
EMA         45      1       0.913   0.912     78%      0.914
KAMA        45      0       0.911   0.925     67%      0.860
FRAMA       45      1       0.911   0.904     84%      0.998
ALMA        45      0       0.909   0.909     84%      0.897
HMA         45      0       0.902   0.906     80%      0.899
DEMA        45      1       0.894   0.914     73%      0.910
McGinley    45      3       0.834   0.897     76%      0.898

[CONCEPTO TF] median pf_fwd (todos tipos,primario) = 0.917 | edge cells (CI_low>1) = 20/630 (3.2%) | %pf_fwd<1 = 72%

## 2) CONSISTENCIA ENTRE TIPOS (senal de causa)
   rango medianas pf_fwd entre tipos: [0.834, 0.955] | tipos con mediana>1: 0/14

## 3) ROBUSTEZ AL PARAMETRO (median pf_fwd por periodos x hyst, todos tipos)
 fast/slow    hyst0  hyst0.5
      8/40    0.912    0.934
     10/55    0.917    0.933
     12/60    0.917    0.952

## 4) DESGLOSE PER-CLUSTER (DIAGNOSTICO, primario, median pf_fwd)
   cluster 0: median pf_fwd = 0.928 (n=630)
   cluster 1: median pf_fwd = 0.908 (n=630)
   cluster 2: median pf_fwd = 0.914 (n=630)

## 5) RANDOM WALK (placebo) — debe caer a PF~1
   median pf (todo panel) = 0.928 | mean = 0.954 | %pf>1.05 = 15% | CI_low>1 = 43/504
   por tipo ruido: GBM=0.909 | SHUF=0.969
   tipos con mayor pf sobre ruido (geometria?): ALMA:0.97, DEMA:0.97, T3:0.95, KAMA:0.94

## 6) BRECHA LOGICO vs OPTIMIZADO (sobreajuste-al-activo, T3.3)
   CAVEAT: opt_pf_fwd CONTAMINADO por seleccion (no es edge). La brecha = sobreajuste.
   median opt_pf_fwd_global = 3.317 | median logico EMA = 0.913 | median logico BEST = 1.164
   median BRECHA (opt - log_best) = 1.798 | simbolos con opt>>log (gap>0.5) = 41/45

## 7) MR (Tenkan-9/HA-diario, fija-logica) — por-simbolo global
   median pf_fwd = 0.742 | mean = 0.754 | n_edge(CI_low>1) = 0/45 | %pf<1 = 100%
   cluster 0: median pf_fwd = 0.786
   cluster 1: median pf_fwd = 0.742
   cluster 2: median pf_fwd = 0.734
   [MR random walk] median pf = 0.853 | PLBGB1=0.7896 | PLBSH1=0.7882 | PLBGB2=0.8534 | PLBSH2=0.8534 | PLBGB3=0.8788 | PLBSH3=0.8829

## 8) VEREDICTO contra los 4 controles (criterio pre-registrado)
   (edge = CI por-simbolo excluye 1.0 EN PANEL LOGICO + cae en ruido + robusto + consistente entre tipos)
   - TF: 3.2% de celdas primarias con CI_low>1 (edge por-simbolo).
   - MR: 0.0% simbolos con CI_low>1.