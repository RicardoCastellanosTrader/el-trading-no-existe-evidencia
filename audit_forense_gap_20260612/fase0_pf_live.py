# -*- coding: utf-8 -*-
"""
FASE 0 — PF live REAL con contabilidad explícita (auditoría forense gap sim↔live).
READ-ONLY sobre snapshot preservado vps_snapshot/combolab (MD5-verified 2026-06-12).

Contabilidad (primary-source verified):
  - pnl_pct  = SOLO PRECIO (exit/entry-1), GROSS de fees y funding (log_trade L1073-1084).
  - pnl_usdt = precio*size, sin fees (close_position L280s; orphan path resta fee del fill exit).
  - funding_paid = columna aparte (USDT).
  - Fees reales NO registrados per-trade -> estimación round-trip taker BingX 0.05%/side = 0.10% notional
    (idéntico al COMMISSION_RATE=0.001 round-trip del kernel sim — accounting comparable por diseño).
"""
import csv, json, random
from datetime import datetime
from collections import defaultdict

SNAP = r"c:\Users\rixip\combolab\audit_forense_gap_20260612\vps_snapshot\combolab"

DEPLOY = {  # entry_timestamp >= deploy => trade del specialist DESPLEGADO actual
    **{s: "2026-05-17 11:49:30" for s in ["BTC", "ETH", "BNB", "XRP", "TRX"]},
    **{s: "2026-05-22 18:16:18" for s in ["ONDO", "RENDER", "POL", "SEI", "TAO"]},
    **{s: "2026-06-05 09:31:49" for s in ["SOL", "DOGE", "ADA", "BCH", "LINK"]},
    **{s: "2026-06-12 11:41:40" for s in ["LTC", "XLM", "ETC", "VET", "FET"]},
}
FEE_RT_PCT = 0.10  # round-trip % notional (estimado, igual a sim COMMISSION_RATE)

def ts2dt(s):
    return datetime.strptime(s.split(".")[0], "%Y-%m-%d %H:%M:%S")

def pf(pnls):
    gp = sum(p for p in pnls if p > 0); gl = -sum(p for p in pnls if p < 0)
    if gl == 0: return float("inf") if gp > 0 else 0.0
    return gp / gl

def boot_ci(pnls, n=10000, seed=42):
    rng = random.Random(seed); out = []
    for _ in range(n):
        s = [rng.choice(pnls) for _ in pnls]
        out.append(pf(s))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n)]

rows = list(csv.DictReader(open(f"{SNAP}/trade_history.csv", encoding="utf-8")))
print(f"Total trades en historia: {len(rows)}")

# --- filtros ---
excl_flags = {"reconstructed", "reconstructed_post_hoc"}
clean = []
for r in rows:
    if r["flag"] in excl_flags: continue
    sym = r["symbol"].split("/")[0]
    if sym not in DEPLOY: continue
    ets = int(r["entry_timestamp_ms"] or 0)
    if ets <= 0:
        continue
    edt = datetime.utcfromtimestamp(ets / 1000)
    if edt < ts2dt(DEPLOY[sym]): continue
    r["_sym"] = sym; r["_edt"] = edt
    r["_pnl"] = float(r["pnl_pct"])
    r["_size"] = float(r["size_usdt"] or 0)
    r["_fund"] = float(r["funding_paid"] or 0)
    r["_pnl_usdt"] = float(r["pnl_usdt"] or 0)
    clean.append(r)

print(f"Trades VENTANA LIMPIA (entry >= deploy del símbolo, sin reconstructed): {len(clean)}")
print(f"  rango entries: {min(r['_edt'] for r in clean)} -> {max(r['_edt'] for r in clean)}")

pnls_g = [r["_pnl"] for r in clean]
# neto de fees estimadas (0.10pp por trade sobre notional => en pnl_pct restar 0.10)
pnls_fee = [p - FEE_RT_PCT for p in pnls_g]
# funding como pp del notional
def fund_pp(r):
    return (r["_fund"] / r["_size"] * 100) if r["_size"] > 0 else 0.0
pnls_net = [p - FEE_RT_PCT - fund_pp(r) for p, r in zip(pnls_g, clean)]

print("\n=== PORTFOLIO (ventana limpia, pnl_pct size-neutral) ===")
for label, ps in [("BRUTO (precio)", pnls_g), ("NETO fees est. 0.10pp", pnls_fee), ("NETO fees+funding", pnls_net)]:
    lo, hi = boot_ci(ps)
    wins = sum(1 for p in ps if p > 0)
    print(f"  {label:26s} PF={pf(ps):.3f}  CI95=[{lo:.3f},{hi:.3f}]  N={len(ps)} wins={wins} "
          f"({100*wins/len(ps):.1f}%)  sum={sum(ps):+.2f}pp  mean={sum(ps)/len(ps):+.4f}pp")

tot_fund = sum(r["_fund"] for r in clean)
tot_size = sum(r["_size"] for r in clean)
tot_pnl_usdt = sum(r["_pnl_usdt"] for r in clean)
fee_usdt_est = tot_size * FEE_RT_PCT / 100
print(f"\n  Notional total={tot_size:.1f} USDT  PnL_usdt bruto={tot_pnl_usdt:+.2f}  "
      f"fees est={fee_usdt_est:.2f}  funding={tot_fund:+.2f}  "
      f"=> neto est={tot_pnl_usdt - fee_usdt_est - tot_fund:+.2f} USDT")

print("\n=== PER-SÍMBOLO (bruto | neto fees+funding) ===")
bysym = defaultdict(list)
for r in clean: bysym[r["_sym"]].append(r)
for s in sorted(bysym, key=lambda s: -len(bysym[s])):
    rs = bysym[s]; ps = [r["_pnl"] for r in rs]
    pn = [r["_pnl"] - FEE_RT_PCT - fund_pp(r) for r in rs]
    print(f"  {s:7s} N={len(rs):3d}  PF_bruto={pf(ps):6.3f}  PF_neto={pf(pn):6.3f}  sum_bruto={sum(ps):+8.2f}pp")

print("\n=== PER-(SÍMBOLO,CLUSTER) — solo trades con etiqueta (backfill 30d) ===")
bysc = defaultdict(list)
for r in clean:
    if r["cluster"] != "": bysc[(r["_sym"], r["cluster"])].append(r)
n_lab = sum(len(v) for v in bysc.values())
print(f"  trades etiquetados en ventana limpia: {n_lab}")

# floors esperados de los JSONs DESPLEGADOS
exp = {}
for sym in set(s for s, _ in bysc) | set(bysym):
    fn = f"{SNAP}/regime_wf/{sym}USDT_specialist_configs.json"
    try:
        d = json.load(open(fn))
        for k, cl in d["clusters"].items():
            if cl.get("top_configs"):
                tc = cl["top_configs"][0]
                exp[(sym, k)] = (tc.get("pf_fwd"), tc.get("pf_fwd_ci_low"), tc.get("config_id"), tc.get("preset"))
    except FileNotFoundError:
        pass

print(f"  {'par':12s} {'N':>3s} {'PF_real_bruto':>13s} {'PF_real_neto':>12s} {'pf_fwd_sim':>10s} {'ci_low_sim':>10s}")
for (s, k) in sorted(bysc, key=lambda x: -len(bysc[x])):
    rs = bysc[(s, k)]; ps = [r["_pnl"] for r in rs]
    pn = [r["_pnl"] - FEE_RT_PCT - fund_pp(r) for r in rs]
    e = exp.get((s, k), (None, None, None, None))
    print(f"  {s+'-C'+k:12s} {len(rs):3d} {pf(ps):13.3f} {pf(pn):12.3f} "
          f"{e[0] if e[0] is not None else '?':>10} {e[1] if e[1] is not None else '?':>10}")

# blended floor esperado ponderado por N real por par etiquetado
num = den = 0.0
for (s, k), rs in bysc.items():
    e = exp.get((s, k))
    if e and e[1]:
        num += e[1] * len(rs); den += len(rs)
if den:
    print(f"\n  Floor blended esperado (pf_fwd_ci_low ponderado por N live etiquetado): {num/den:.3f}")
num2 = den2 = 0.0
for (s, k), rs in bysc.items():
    e = exp.get((s, k))
    if e and e[0]:
        num2 += e[0] * len(rs); den2 += len(rs)
if den2:
    print(f"  pf_fwd blended esperado (mismo peso): {num2/den2:.3f}")

print("\n=== EXIT REASONS ventana limpia (kernel-modelados vs orquestador) ===")
KERNEL_EXITS = {"sl_hit", "sl_emergency", "div_exit", "tf_exit", "zone_exit", "cancel_tf",
                "zone_exit_mr", "cancel_zona", "cancel_ghost", "cancel_mr"}
byreason = defaultdict(list)
for r in clean: byreason[r["reason_exit"]].append(r["_pnl"])
for reason in sorted(byreason, key=lambda x: -len(byreason[x])):
    ps = byreason[reason]
    tag = "KERNEL" if reason in KERNEL_EXITS else "ORQUESTADOR/OTRO"
    print(f"  {reason:28s} N={len(ps):3d}  sum={sum(ps):+8.2f}pp  PF={pf(ps):6.3f}  [{tag}]")
