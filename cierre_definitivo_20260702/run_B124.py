#!/usr/bin/env python3
"""Corre B1 (funding-carry), B2 (reversal corto), B4 (low-vol/BAB) con params CONGELADOS.
Un solo build de paneles. CI block-bootstrap en el Sharpe de C. Gate de beta ARREGLADO."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xs_harness as xh
import cs_mom as cm

HERE = Path(__file__).resolve().parent
np.seterr(all="ignore")

print("build_panels...")
C, H, L, Q, F, cov = cm.build_panels(log=lambda *a: None)
rets = C.pct_change()
print(f"panel {C.shape[1]}x{C.shape[0]}")

def verdict(diag, Cser, name):
    be, bb = diag["beta_C_vs_EW"], diag["beta_C_vs_BTC"]
    cfull = diag["C"]["full"]; c23 = diag["C"]["2023"]; c24 = diag["C"]["2024"]
    sh = cfull.get("sharpe"); dd = cfull.get("maxdd_pct")
    lo, hi, med = xh.block_bootstrap_sharpe_ci(Cser)
    neutral = be is not None and bb is not None and abs(be) <= 0.15 and abs(bb) <= 0.15
    c_ret = sh is not None and sh >= 1.00
    ci_excl0 = lo is not None and lo > 0
    prot = dd is not None and dd > -25
    s23 = c23.get("sharpe"); s24 = c24.get("sharpe")
    surv = s23 is not None and s24 is not None and s23 > 0 and s24 > 0
    digna = neutral and c_ret and ci_excl0 and prot and surv
    return {"name": name, "sharpe_full": sh, "sharpe_CI": [round(lo,3) if lo else None, round(hi,3) if hi else None],
            "ci_excluye_0": ci_excl0, "ci_excluye_1": (lo is not None and lo > 1.0),
            "beta_EW": be, "beta_BTC": bb, "neutral": neutral, "maxdd_pct": dd, "prot": prot,
            "sharpe_2023": s23, "sharpe_2024": s24, "sobrevive_ambos": surv,
            "sharpe>=1": c_ret, "turnover": diag["turnover_medio_por_rebal"],
            "book_LS": [diag["book_long_medio"], diag["book_short_medio"]],
            "A_full_sharpe": diag["A"]["full"].get("sharpe"), "B_full_sharpe": diag["B"]["full"].get("sharpe"),
            "VEREDICTO": "DIGNA" if digna else "NO DIGNA"}

out = {}

# ---- B1 funding-carry ----
Ftr = F.rolling(6, min_periods=3).mean()
fac_b1 = -Ftr                                  # mayor = funding mas negativo = LARGO
d1, (A1, B1s, C1) = xh.run_xs(C, H, L, Q, F, fac_b1, rebal_bars=10, warmup=56)
v1 = verdict(d1, C1, "B1_funding_carry")
# colapso en momentum: spearman medio ranking funding vs momentum en rebal bars
mom = cm.factor(C, H, L, 28)
rebal_idx = list(range(56, len(C.index), 10))
sp = []
for i in rebal_idx:
    a = fac_b1.iloc[i]; b = mom.iloc[i]
    j = pd.concat([a, b], axis=1).dropna()
    if len(j) >= 10:
        sp.append(j.iloc[:, 0].rank().corr(j.iloc[:, 1].rank()))
v1["spearman_medio_rank_funding_vs_momentum"] = round(float(np.nanmean(sp)), 3) if sp else None
v1["corr_serie_C_carry_vs_C_momentum"] = round(float(pd.concat([C1, xh.run_xs(C,H,L,Q,F,mom,10,56)[1][2]], axis=1).dropna().corr().iloc[0,1]), 3)
out["B1"] = v1

# ---- B2 reversal corto ----
fac_b2 = -(C / C.shift(6) - 1.0)               # mayor = mayor perdedor reciente = LARGO
d2, (A2, B2s, C2) = xh.run_xs(C, H, L, Q, F, fac_b2, rebal_bars=10, warmup=56)
out["B2"] = verdict(d2, C2, "B2_reversal_corto")

# ---- B4 low-vol / BAB ----
vol28 = rets.rolling(28, min_periods=14).std()
fac_b4 = -vol28                                # mayor = menor vol = LARGO
d4, (A4, B4s, C4) = xh.run_xs(C, H, L, Q, F, fac_b4, rebal_bars=10, warmup=56)
out["B4"] = verdict(d4, C4, "B4_low_vol_bab")

(HERE / "results_B124.json").write_text(json.dumps(out, indent=2, default=str))
print("\n" + "=" * 78)
for k in ("B1", "B2", "B4"):
    v = out[k]
    print(f"\n{v['name']}: {v['VEREDICTO']}")
    print(f"  Sharpe_full={v['sharpe_full']} CI{v['sharpe_CI']} (excl0={v['ci_excluye_0']} excl1={v['ci_excluye_1']})")
    print(f"  beta_EW={v['beta_EW']} beta_BTC={v['beta_BTC']} neutral={v['neutral']} | maxDD={v['maxdd_pct']}% prot={v['prot']}")
    print(f"  Sharpe 2023={v['sharpe_2023']} 2024={v['sharpe_2024']} sobrevive={v['sobrevive_ambos']}")
    print(f"  A_long={v['A_full_sharpe']} B_short={v['B_full_sharpe']} turnover={v['turnover']} book={v['book_LS']}")
print(f"\nB1 colapso-momentum: spearman_medio={out['B1']['spearman_medio_rank_funding_vs_momentum']} "
      f"corr_serie={out['B1']['corr_serie_C_carry_vs_C_momentum']}")
print("=" * 78)
