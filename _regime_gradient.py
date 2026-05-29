"""PART B.5 — continuous gradient test of the §0.0 hypothesis (read-only).

§0.0 predicts: lower pct_recent (A blinder) -> larger B2 advantage -> Delta(B2-A)
should be NEGATIVELY correlated with pct_recent_5k.  Spearman (rank) = outlier-robust
(handles the ETH C1 pf_fwd=628 degenerate cell).
"""
import json
import numpy as np

rows = [r for r in json.load(open("audit_regime_type_results.json"))["part_a"] if "_meta" not in r]

def rank(x):
    x = np.asarray(x, float); order = x.argsort(); r = np.empty_like(order, float)
    r[order] = np.arange(len(x))
    # average ties
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    sums = np.zeros(len(cnt)); np.add.at(sums, inv, r); avg = sums / cnt
    return avg[inv]

def spearman(a, b):
    ra, rb = rank(a), rank(b)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra*rb).sum()/d) if d else float("nan")

pct = np.array([r["pct_recent_5k"] for r in rows])
dff = np.array([r["B2_pf_fwd"] - r["A_pf_fwd"] for r in rows])
dfc = np.array([r["B2_pf_combined"] - r["A_pf_combined"] for r in rows])
powered = np.array([min(r["A_trades_fwd"], r["B2_trades_fwd"]) >= 15 for r in rows])

print("n cells:", len(rows), "| powered>=15tr:", int(powered.sum()))
print("\nSpearman rho(pct_recent, Delta) — §0.0 predicts NEGATIVE & strong:")
print(f"  Delta pf_fwd      : rho = {spearman(pct, dff):+.3f}   (all 18)")
print(f"  Delta pf_combined : rho = {spearman(pct, dfc):+.3f}   (all 18)")
print(f"  Delta pf_fwd      : rho = {spearman(pct[powered], dff[powered]):+.3f}   (powered {int(powered.sum())})")
print(f"  Delta pf_combined : rho = {spearman(pct[powered], dfc[powered]):+.3f}   (powered {int(powered.sum())})")

print("\nCells sorted by pct_recent ASC (A blindest at top — §0.0 expects B2 winning/Delta>0 at top):")
print(f"  {'sym':10} {'k':2} {'pct5K':>6} {'dPF_fwd':>8} {'dPF_comb':>9} {'B2win_fwd':>9} {'B2win_comb':>10} {'minTr':>6}")
for r in sorted(rows, key=lambda r: r["pct_recent_5k"]):
    df_, dc_ = r["B2_pf_fwd"]-r["A_pf_fwd"], r["B2_pf_combined"]-r["A_pf_combined"]
    mt = min(r["A_trades_fwd"], r["B2_trades_fwd"])
    print(f"  {r['sym']:10} {r['k']:<2} {r['pct_recent_5k']*100:>5.1f}% {df_:>+8.3f} {dc_:>+9.3f} "
          f"{'B2' if df_>0 else 'A':>9} {'B2' if dc_>0 else 'A':>10} {mt:>6}")

# Overall B2 vs A regardless of regime class (context for PART D)
print("\nOverall (all 18, productive metric pf_combined):")
print(f"  B2 win rate = {(dfc>0).mean():.0%} | Delta median = {np.median(dfc):+.3f} | Delta mean = {dfc.mean():+.3f}")
print(f"  pf_fwd:  B2 win rate = {(dff>0).mean():.0%} | Delta median = {np.median(dff):+.3f}")
