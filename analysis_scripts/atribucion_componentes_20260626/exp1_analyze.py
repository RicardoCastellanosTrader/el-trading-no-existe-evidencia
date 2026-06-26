# -*- coding: utf-8 -*-
"""
Atribucion por Componentes — Experimento #1 — AGREGACION / TABLA T3.2.
Lee los result CSVs y produce la tabla de atribucion + veredicto contra los 4 controles.
Unidad registrada = POR-SIMBOLO (global = cross-cluster dentro del simbolo).
El edge se lee del panel LOGICO; optimizadas = contraste de sobreajuste.
"""
import os
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
def load(name):
    p = os.path.join(D, name)
    return pd.read_csv(p) if os.path.exists(p) else None

tf = load("results_tf_logical.csv")
pl = load("results_placebo.csv")
opt = load("results_optimized.csv")
mr = load("results_mr_logical.csv")
mrp = load("results_mr_placebo.csv")

out = []
def P(s=""):
    out.append(s); print(s)

P("# EXPERIMENTO #1 — TABLA DE ATRIBUCION (T3.2)\n")
P(f"Benchmark sistema completo as-of GLOBAL = 0.702 [0.44, 1.07]. Breakeven=1.0.\n")

# ---------- TF PRIMARIO (10/55, hyst 0) por tipo de media ----------
if tf is not None:
    prim = tf[(tf.fast == 10) & (tf.slow == 55) & (tf.hyst == 0.0)].copy()
    P("## 1) TF PRIMARIO (10/55, hyst 0) — por tipo de media (45 simbolos)\n")
    P(f"{'tipo':<10}{'n':>4}{'n_edge':>7}{'med_pf_fwd':>12}{'mean':>8}{'%pf<1':>8}{'med_pf_tr':>11}")
    rowsum = []
    for mt, g in prim.groupby('ma_type'):
        n = len(g); n_edge = int((g.ci_low > 1.0).sum())
        med = g.pf_fwd.median(); mean = g.pf_fwd.mean()
        sub = 100.0 * (g.pf_fwd < 1.0).mean(); medtr = g.pf_tr.median()
        rowsum.append((mt, n, n_edge, med, mean, sub, medtr))
    rowsum.sort(key=lambda r: -r[3])
    for mt, n, n_edge, med, mean, sub, medtr in rowsum:
        P(f"{mt:<10}{n:>4}{n_edge:>7}{med:>12.3f}{mean:>8.3f}{sub:>7.0f}%{medtr:>11.3f}")
    allp = prim
    P(f"\n[CONCEPTO TF] median pf_fwd (todos tipos,primario) = {allp.pf_fwd.median():.3f} | "
      f"edge cells (CI_low>1) = {int((allp.ci_low>1.0).sum())}/{len(allp)} "
      f"({100*(allp.ci_low>1.0).mean():.1f}%) | %pf_fwd<1 = {100*(allp.pf_fwd<1.0).mean():.0f}%")

    # ---------- Consistencia entre tipos ----------
    P("\n## 2) CONSISTENCIA ENTRE TIPOS (senal de causa)")
    meds = prim.groupby('ma_type').pf_fwd.median()
    P(f"   rango medianas pf_fwd entre tipos: [{meds.min():.3f}, {meds.max():.3f}] | "
      f"tipos con mediana>1: {int((meds>1.0).sum())}/{len(meds)}")

    # ---------- Robustez al parametro ----------
    P("\n## 3) ROBUSTEZ AL PARAMETRO (median pf_fwd por periodos x hyst, todos tipos)")
    P(f"{'fast/slow':>10}{'hyst0':>9}{'hyst0.5':>9}")
    for (fp, sp), g in tf.groupby(['fast', 'slow']):
        h0 = g[g.hyst == 0.0].pf_fwd.median(); h5 = g[g.hyst == 0.5].pf_fwd.median()
        P(f"{f'{fp}/{sp}':>10}{h0:>9.3f}{h5:>9.3f}")

    # ---------- Desglose per-cluster (diagnostico) ----------
    P("\n## 4) DESGLOSE PER-CLUSTER (DIAGNOSTICO, primario, median pf_fwd)")
    for c in range(3):
        col = f'pf_fwd_c{c}'
        if col in prim: P(f"   cluster {c}: median pf_fwd = {prim[col].median():.3f} (n={prim[col].notna().sum()})")

# ---------- Random walk ----------
if pl is not None:
    P("\n## 5) RANDOM WALK (placebo) — debe caer a PF~1")
    P(f"   median pf (todo panel) = {pl.pf.median():.3f} | mean = {pl.pf.mean():.3f} | "
      f"%pf>1.05 = {100*(pl.pf>1.05).mean():.0f}% | CI_low>1 = {int((pl.ci_low>1.0).sum())}/{len(pl)}")
    g = pl.groupby('kind').pf.median()
    P(f"   por tipo ruido: " + " | ".join(f"{k}={v:.3f}" for k, v in g.items()))
    # tipos de media que 'funcionan' sobre ruido (geometria)
    geo = pl.groupby('ma_type').pf.median().sort_values(ascending=False)
    P(f"   tipos con mayor pf sobre ruido (geometria?): " + ", ".join(f"{k}:{v:.2f}" for k, v in geo.head(4).items()))

# ---------- Contraste optimizado (brecha sobreajuste) ----------
if opt is not None and tf is not None:
    P("\n## 6) BRECHA LOGICO vs OPTIMIZADO (sobreajuste-al-activo, T3.3)")
    P("   CAVEAT: opt_pf_fwd CONTAMINADO por seleccion (no es edge). La brecha = sobreajuste.")
    base = prim[prim.ma_type == 'EMA'][['symbol', 'pf_fwd']].rename(columns={'pf_fwd': 'log_ema'})
    # mejor tipo logico por simbolo (primario)
    best = prim.groupby('symbol').pf_fwd.max().rename('log_best').reset_index()
    m = opt.merge(base, on='symbol', how='left').merge(best, on='symbol', how='left')
    m['gap_best'] = m['opt_pf_fwd_global'] - m['log_best']
    P(f"   median opt_pf_fwd_global = {m.opt_pf_fwd_global.median():.3f} | "
      f"median logico EMA = {m.log_ema.median():.3f} | median logico BEST = {m.log_best.median():.3f}")
    P(f"   median BRECHA (opt - log_best) = {m.gap_best.median():.3f} | "
      f"simbolos con opt>>log (gap>0.5) = {int((m.gap_best>0.5).sum())}/{len(m)}")

# ---------- MR ----------
if mr is not None:
    P("\n## 7) MR (Tenkan-9/HA-diario, fija-logica) — por-simbolo global")
    n_edge = int((mr.ci_low > 1.0).sum())
    P(f"   median pf_fwd = {mr.pf_fwd.median():.3f} | mean = {mr.pf_fwd.mean():.3f} | "
      f"n_edge(CI_low>1) = {n_edge}/{len(mr)} | %pf<1 = {100*(mr.pf_fwd<1.0).mean():.0f}%")
    for c in range(3):
        col = f'pf_fwd_c{c}'
        if col in mr: P(f"   cluster {c}: median pf_fwd = {mr[col].median():.3f}")
if mrp is not None:
    P(f"   [MR random walk] median pf = {mrp.pf.median():.3f} | " +
      " | ".join(f"{r.series}={r.pf}" for r in mrp.itertuples()))

# ---------- Veredicto ----------
P("\n## 8) VEREDICTO contra los 4 controles (criterio pre-registrado)")
P("   (edge = CI por-simbolo excluye 1.0 EN PANEL LOGICO + cae en ruido + robusto + consistente entre tipos)")
if tf is not None:
    edge_share = 100*(prim.ci_low>1.0).mean()
    P(f"   - TF: {edge_share:.1f}% de celdas primarias con CI_low>1 (edge por-simbolo).")
if mr is not None:
    P(f"   - MR: {100*(mr.ci_low>1.0).mean():.1f}% simbolos con CI_low>1.")

with open(os.path.join(D, "ATRIBUCION_T3_2_RESULTADOS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n[SAVED] ATRIBUCION_T3_2_RESULTADOS.md")
