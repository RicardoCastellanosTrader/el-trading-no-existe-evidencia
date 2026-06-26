# -*- coding: utf-8 -*-
"""Exp#2 v3 — AGREGACIÓN / TABLA T3.2-Exp2. Veredicto = BRECHA real-vs-placebo."""
import os
import numpy as np, pandas as pd
D = os.path.dirname(os.path.abspath(__file__))
real = pd.read_csv(os.path.join(D, "results_obv3_real.csv"))
plac = pd.read_csv(os.path.join(D, "results_obv3_placebo.csv"))
out = []
def P(s=""):
    out.append(s); print(s)

N0, F0, P0 = 0.05, 0.75, 10
rp = real[(real.near == N0) & (real.frac == F0) & (real.P == P0)].copy()
pp = plac[(plac.near == N0) & (plac.frac == F0) & (plac.P == P0)].copy()

P("# EXP#2 v3 ORDER BLOCK (criterio real Ricardo) — TABLA T3.2-Exp2\n")
P("VEREDICTO por la BRECHA real-vs-placebo (no PF absoluto).\n")

floor = pp.pf_all.median()
P("## 1) EL JUEZ — BRECHA real vs placebo (pf_all full-series, misma base)")
P(f"   placebo floor (median 6 series) = {floor:.3f} | por serie: " + " ".join(f"{r.series}:{r.pf_all:.2f}" for r in pp.itertuples()))
P(f"   real median pf_all (45 sym)     = {rp.pf_all.median():.3f}")
P(f"   >>> BRECHA GEOMÉTRICA (real - placebo) = {rp.pf_all.median()-floor:+.3f}")
P(f"   real sym con pf_all > placebo floor: {int((rp.pf_all>floor).sum())}/{len(rp)}")

P("\n## 2) EDGE AS-OF FORWARD (pf_fwd holdout) — primario")
P(f"   real median pf_fwd = {rp.pf_fwd.median():.3f} | mean = {rp.pf_fwd.mean():.3f} | %pf<1 = {100*(rp.pf_fwd<1).mean():.0f}%")
P(f"   n con CI_low>1.0          = {int((rp.ci_low>1.0).sum())}/{len(rp)}")
P(f"   n con CI_low>placebo_floor({floor:.2f}) = {int((rp.ci_low>floor).sum())}/{len(rp)}  <-- bate geometría")
P(f"   brecha fwd (median pf_fwd - floor) = {rp.pf_fwd.median()-floor:+.3f}")

P("\n## 3) ROBUSTEZ (median pf_all real - median placebo por config)")
P(f"{'near':>6}{'frac':>6}{'P':>4}{'real':>8}{'placebo':>9}{'brecha':>8}")
for (nn, ff, pp_) in sorted(set(zip(real.near, real.frac, real.P))):
    rm = real[(real.near==nn)&(real.frac==ff)&(real.P==pp_)].pf_all.median()
    pm = plac[(plac.near==nn)&(plac.frac==ff)&(plac.P==pp_)].pf_all.median()
    fl = " <-PRIM" if (nn,ff,pp_)==(N0,F0,P0) else ""
    P(f"{nn:>6}{ff:>6}{pp_:>4}{rm:>8.3f}{pm:>9.3f}{rm-pm:>+8.3f}{fl}")

P("\n## 4) PER-CLUSTER (diagnóstico, primario, median pf_fwd real)")
for cc in range(3):
    col = f'pf_fwd_c{cc}'
    if col in rp: P(f"   cluster {cc}: median pf_fwd = {rp[col].median():.3f}")

P("\n## 5) DISTRIBUCIÓN real pf_fwd primario")
rr = rp[['symbol','pf_fwd','ci_low','ci_high','trades_fwd','pf_all']].sort_values('pf_fwd', ascending=False)
P("   top5:    " + " | ".join(f"{r.symbol}:{r.pf_fwd:.2f}[{r.ci_low:.2f}-{r.ci_high:.2f}]" for r in rr.head(5).itertuples()))
P("   bottom5: " + " | ".join(f"{r.symbol}:{r.pf_fwd:.2f}" for r in rr.tail(5).itertuples()))

P("\n## 6) VEREDICTO (sobre la BRECHA)")
gap_all = rp.pf_all.median()-floor; gap_fwd = rp.pf_fwd.median()-floor
n_beat = int((rp.ci_low>floor).sum())
P(f"   brecha pf_all={gap_all:+.3f} | brecha fwd={gap_fwd:+.3f} | sym CI>floor={n_beat}/45")
if abs(gap_all) < 0.08 and n_beat <= 4:
    P("   => placebo ~= real -> GEOMETRÍA, NO liquidez. NEGATIVO. Bifurcación (a)/(b).")
elif gap_fwd > 0.10 and n_beat >= 12:
    P("   => real SUPERA placebo robustamente -> SEÑAL: el barrido de liquidez carga edge.")
else:
    P("   => intermedio: leer robustez + per-cluster + consistencia.")

with open(os.path.join(D, "ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n[SAVED] ATRIBUCION_T3_2_EXP2V3_RESULTADOS.md")
