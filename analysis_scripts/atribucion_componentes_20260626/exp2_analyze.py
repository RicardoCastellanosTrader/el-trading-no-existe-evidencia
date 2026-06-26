# -*- coding: utf-8 -*-
"""
Exp#2 ORDER BLOCK — AGREGACION / TABLA T3.2-Exp2.
VEREDICTO = BRECHA real-vs-placebo (no PF absoluto). El random walk es EL juez.
"""
import os
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
real = pd.read_csv(os.path.join(D, "results_ob_real.csv"))
plac = pd.read_csv(os.path.join(D, "results_ob_placebo.csv"))
out = []
def P(s=""):
    out.append(s); print(s)

K0, W0, R0 = 2.0, 50, 2.0
rp = real[(real.k == K0) & (real.W == W0) & (real.R == R0)].copy()
pp = plac[(plac.k == K0) & (plac.W == W0) & (plac.R == R0)].copy()

P("# EXPERIMENTO #2 — ORDER BLOCK — TABLA DE ATRIBUCION (T3.2-Exp2)\n")
P("VEREDICTO por la BRECHA real-vs-placebo, NO por el PF absoluto (caveat geometrico).\n")

# ---------- EL JUEZ: brecha geometrica (pf_all, misma base full-series) ----------
floor_all = pp.pf_all.median()
real_all_med = rp.pf_all.median()
P("## 1) EL JUEZ — BRECHA REAL vs PLACEBO (pf_all full-series, misma base)")
P(f"   placebo floor (median pf_all 6 series, geometria del setup) = {floor_all:.3f}")
P(f"   placebo por serie: " + " ".join(f"{r.series}:{r.pf_all:.2f}" for r in pp.itertuples()))
P(f"   real median pf_all (45 sym)                                  = {real_all_med:.3f}")
P(f"   >>> BRECHA GEOMETRICA (real - placebo) = {real_all_med - floor_all:+.3f}")
P(f"   real sym con pf_all > placebo floor: {int((rp.pf_all > floor_all).sum())}/45")

# ---------- As-of forward edge ----------
P("\n## 2) EDGE AS-OF FORWARD (pf_fwd, holdout) — primario k=2/W=50/R=2")
P(f"   real median pf_fwd = {rp.pf_fwd.median():.3f} | mean = {rp.pf_fwd.mean():.3f} | %pf_fwd<1 = {100*(rp.pf_fwd<1).mean():.0f}%")
P(f"   n con CI_low>1.0 (breakeven)        = {int((rp.ci_low>1.0).sum())}/45")
P(f"   n con CI_low>placebo_floor ({floor_all:.2f}) = {int((rp.ci_low>floor_all).sum())}/45   <-- beats geometria")
P(f"   real median pf_fwd ({rp.pf_fwd.median():.3f}) vs placebo floor ({floor_all:.3f}) -> brecha fwd = {rp.pf_fwd.median()-floor_all:+.3f}")

# ---------- Robustez del GAP a traves del grid ----------
P("\n## 3) ROBUSTEZ — brecha (real_median - placebo_median) pf_all por (k,W,R)")
P(f"{'k':>5}{'W':>5}{'R':>5}{'real':>8}{'placebo':>9}{'brecha':>8}")
for (k, w, r), g in real.groupby(['k', 'W', 'R']):
    pm = plac[(plac.k == k) & (plac.W == w) & (plac.R == r)].pf_all.median()
    rm = g.pf_all.median()
    flag = " <-PRIM" if (k, w, r) == (K0, W0, R0) else ""
    P(f"{k:>5}{w:>5}{r:>5}{rm:>8.3f}{pm:>9.3f}{rm-pm:>+8.3f}{flag}")

# ---------- Per-cluster diagnostico ----------
P("\n## 4) PER-CLUSTER (diagnostico) — median pf_fwd real, primario")
for c in range(3):
    col = f'pf_fwd_c{c}'
    if col in rp:
        P(f"   cluster {c}: median pf_fwd = {rp[col].median():.3f} (n_sym={rp[col].notna().sum()})")
P("   (prueba causal: el OB de reversion deberia vivir en regimen de reversion/lateral, no tendencial)")

# ---------- Distribucion real primario (top/bottom) ----------
P("\n## 5) DISTRIBUCION real pf_fwd primario (mejores/peores)")
rr = rp[['symbol', 'pf_fwd', 'ci_low', 'ci_high', 'trades_fwd', 'pf_all']].sort_values('pf_fwd', ascending=False)
P("   top5:    " + " | ".join(f"{r.symbol}:{r.pf_fwd:.2f}[{r.ci_low:.2f}-{r.ci_high:.2f}]" for r in rr.head(5).itertuples()))
P("   bottom5: " + " | ".join(f"{r.symbol}:{r.pf_fwd:.2f}" for r in rr.tail(5).itertuples()))

# ---------- VEREDICTO ----------
P("\n## 6) VEREDICTO (sobre la BRECHA, no el PF absoluto)")
gap_all = real_all_med - floor_all
gap_fwd = rp.pf_fwd.median() - floor_all
n_beat = int((rp.ci_low > floor_all).sum())
P(f"   brecha geometrica pf_all = {gap_all:+.3f} | brecha fwd = {gap_fwd:+.3f} | sym que baten geometria (CI>floor) = {n_beat}/45")
if abs(gap_all) < 0.08 and n_beat <= 4:
    P("   => placebo ~= real -> el PF es GEOMETRIA del setup, NO liquidez. VEREDICTO NEGATIVO (5a linea).")
elif gap_fwd > 0.10 and n_beat >= 15:
    P("   => real SUPERA placebo robustamente -> el OB captura algo que el ruido no tiene. SENAL POSITIVA.")
else:
    P("   => zona intermedia: brecha modesta. Leer robustez + per-cluster + consistencia antes de concluir.")

with open(os.path.join(D, "ATRIBUCION_T3_2_EXP2_RESULTADOS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n[SAVED] ATRIBUCION_T3_2_EXP2_RESULTADOS.md")
