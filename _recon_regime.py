"""Read-only recon: GMM struct, specialist JSON fields, GATE bitex, part_b dump."""
import json
from pathlib import Path
import numpy as np
import joblib
from regime_features import FEATURE_NAMES, N_FEATURES

D = Path("audit_etapa2_20260522_213747")
print("FEATURE_NAMES =", FEATURE_NAMES, "| N_FEATURES =", N_FEATURES)

# 1. GMM joblib struct
md = joblib.load(Path("regime_models") / "BTC_regime.joblib")
print("\n=== BTC_regime.joblib keys ===")
print(list(md.keys()))
print("n_clusters =", md.get("n_clusters"), "| lookback =", md.get("lookback"))
gmm = md["gmm"]; scaler = md["scaler"]
print("gmm.means_ shape =", gmm.means_.shape)
centroids_feat = scaler.inverse_transform(gmm.means_)
for k in range(centroids_feat.shape[0]):
    print(f"  C{k} centroid (feat space):",
          {FEATURE_NAMES[j]: round(float(centroids_feat[k, j]), 4) for j in range(N_FEATURES)})

# 2. Specialist JSON structure
def jstruct(p, label):
    with open(p) as f:
        d = json.load(f)
    print(f"\n=== {label} top-level keys ===", list(d.keys()))
    cl = d.get("clusters", {})
    print("clusters keys:", list(cl.keys()))
    for k, v in cl.items():
        tc = v.get("top_configs") or []
        if tc:
            print(f"  C{k} top_configs[0] keys:", list(tc[0].keys()))
            t0 = tc[0]
            print(f"     cfg={t0.get('config_id')} preset={t0.get('preset')} "
                  f"pf_combined={t0.get('pf_combined')} pf_fwd={t0.get('pf_fwd')} "
                  f"pf_tr={t0.get('pf_tr')} trades_fwd={t0.get('trades_fwd')} "
                  f"n_validated={t0.get('n_validated')} sqn={t0.get('sqn')}")
        else:
            print(f"  C{k}: NO top_configs (valid={v.get('valid')}, decision={v.get('decision')})")
        break  # just first cluster for key listing
    return d

dA = jstruct(D / "baseline_A_deployed" / "BTCUSDT_specialist_configs.json", "A_deployed BTC")

# 3. GATE BIT-EXACT: gate_bitex BTC vs baseline_A_deployed BTC, per-cluster top-1
print("\n=== GATE BIT-EXACT BTC (wrapper-master vs deployed) ===")
gate = D / "gate_bitex_BTC_20260526_143045" / "BTCUSDT_specialist_configs.json"
with open(gate) as f:
    dG = json.load(f)
with open(D / "baseline_A_deployed" / "BTCUSDT_specialist_configs.json") as f:
    dB = json.load(f)
fields = ["config_id", "pf_combined", "pf_fwd", "pf_tr", "trades_fwd", "n_validated", "sqn"]
all_match = True
for k in sorted(set(dG.get("clusters", {})) | set(dB.get("clusters", {}))):
    g = (dG["clusters"].get(k, {}).get("top_configs") or [None])[0]
    b = (dB["clusters"].get(k, {}).get("top_configs") or [None])[0]
    if g is None or b is None:
        print(f"  C{k}: gate={g is not None} deployed={b is not None} (one missing)")
        all_match = all_match and (g is None and b is None)
        continue
    diffs = {f: (g.get(f), b.get(f)) for f in fields if g.get(f) != b.get(f)}
    status = "MATCH" if not diffs else f"DIFF {diffs}"
    if diffs: all_match = False
    print(f"  C{k}: {status}")
print("GATE BIT-EXACT verdict:", "PASS" if all_match else "FAIL")

# 4. contamination_part_b.json dump
print("\n=== contamination_part_b.json per-cell ===")
with open(D / "contamination_part_b.json") as f:
    cells = json.load(f)
print(f"total cells: {len(cells)}")
hdr = f"{'sym':10} {'mode':4} {'k':2} {'cfg':>10} {'pf_fwd':>7} {'repro':>7} {'diff%':>6} {'ntot':>5} {'nin':>4} {'nout':>4} {'pf_in':>7} {'pf_out':>7}"
print(hdr)
for c in cells:
    if "error" in c:
        print(f"{c.get('sym'):10} {c.get('mode'):4} {c.get('k')} ERROR {c['error']}")
        continue
    def fnum(x):
        return "None" if x is None else (f"{float(x):.3f}" if x != float('inf') else "inf")
    print(f"{c['sym']:10} {c['mode']:4} {c['k']:<2} {c['config_id']:>10} "
          f"{c['expected_pf_fwd']:>7.3f} {c['repro_pf_fwd']:>7.3f} {c['repro_diff_pf_pct']:>6.2f} "
          f"{c['n_trades_total']:>5} {c['n_inside']:>4} {c['n_outside']:>4} "
          f"{fnum(c['pf_inside']):>7} {fnum(c['pf_outside']):>7}")
