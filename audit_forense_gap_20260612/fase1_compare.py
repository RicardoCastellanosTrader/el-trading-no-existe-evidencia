# -*- coding: utf-8 -*-
"""FASE 1 — Comparación replay vs realidad live.
1A: nivel señal/clasificación vs SIGNALS_RAW (k, cfg, acción).
1B: nivel trade vs trade_history (±1 barra).
1C: nivel PnL (contabilidad idéntica: pnl_pct precio − 0.10pp fee round-trip)."""
import pandas as pd, numpy as np, csv, sys
from datetime import datetime, timezone
from pathlib import Path

AUDIT = Path(r"c:\Users\rixip\combolab\audit_forense_gap_20260612")
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "deployed"
FEE = 0.10

def pf(p):
    gp = sum(x for x in p if x > 0); gl = -sum(x for x in p if x < 0)
    return gp / gl if gl > 0 else (float("inf") if gp > 0 else 0.0)

cyc = pd.read_csv(AUDIT / f"replay_cycles_{VARIANT}.csv")
cyc["T"] = pd.to_datetime(cyc["T"], utc=True)
raw = pd.read_csv(AUDIT / "signals_raw_window.csv")
raw["bar_T"] = pd.to_datetime(raw["bar_t"], unit="s", utc=True)
raw["sym"] = raw["symbol"].str.replace("/USDT", "", regex=False)

# ---------- 1A: clasificación + config en eventos SIGNALS_RAW ----------
print(f"=== 1A [{VARIANT}] match clasificación/config en {len(raw)} eventos SIGNALS_RAW ===")
m = raw.merge(cyc, left_on=["sym", "bar_T"], right_on=["symbol", "T"],
              suffixes=("_live", "_rep"), how="left")
have = m[m["k_rep"].notna()].copy() if "k_rep" in m else m[m["k"].notna()].copy()
kcol_l, kcol_r = ("k_live", "k_rep") if "k_rep" in m.columns else ("k_x", "k_y")
cfg_l, cfg_r = ("cfg_live", "cfg_rep") if "cfg_rep" in m.columns else ("cfg_x", "cfg_y")
have["k_match"] = have[kcol_l] == have[kcol_r]
have["cfg_match"] = have[cfg_l] == have[cfg_r]
act_l = "action_live" if "action_live" in have.columns else "action_x"
act_r = "action_rep" if "action_rep" in have.columns else "action_y"
have["act_match"] = have[act_l] == have[act_r]
print(f"eventos con ciclo replay: {len(have)}/{len(m)}")
for col in ["k_match", "cfg_match", "act_match"]:
    print(f"  {col}: {100*have[col].mean():.1f}%")
print("\nper-símbolo k_match / act_match:")
g = have.groupby("sym").agg(n=("k_match", "size"), k=("k_match", "mean"), a=("act_match", "mean"))
print((g.assign(k=lambda d: (100*d.k).round(1), a=lambda d: (100*d.a).round(1))).to_string())
mm = have[~have["k_match"]]
if len(mm):
    print("\nmismatches k (primeros 15):")
    print(mm[["bar_T", "sym", kcol_l, kcol_r, cfg_l, cfg_r, act_l, act_r]].head(15).to_string())

# ---------- 1B: trades ----------
rt = pd.read_csv(AUDIT / f"replay_trades_{VARIANT}.csv")
rt["entry_T"] = pd.to_datetime(rt["entry_T"], utc=True, errors="coerce")
rows = list(csv.DictReader(open(AUDIT / "vps_snapshot" / "combolab" / "trade_history.csv", encoding="utf-8")))
DEP = {**{s: "2026-05-17" for s in ["BTC", "ETH", "BNB", "XRP", "TRX"]},
       **{s: "2026-05-22" for s in ["ONDO", "RENDER", "POL", "SEI", "TAO"]},
       **{s: "2026-06-05" for s in ["SOL", "DOGE", "ADA", "BCH", "LINK"]}}
live = []
for r in rows:
    s = r["symbol"].split("/")[0]
    if s not in DEP or r["flag"].startswith("reconstructed"):
        continue
    ets = int(r["entry_timestamp_ms"] or 0)
    if ets <= 0:
        continue
    edt = pd.Timestamp(datetime.fromtimestamp(ets / 1000, tz=timezone.utc)).floor("h")
    if str(edt.date()) < DEP[s]:
        continue
    live.append({"sym": s, "side": r["side"], "entry_T": edt, "exit_ts": r["timestamp"],
                 "pnl": float(r["pnl_pct"]), "reason": r["reason_exit"], "k": r["cluster"]})
lv = pd.DataFrame(live)
print(f"\n=== 1B [{VARIANT}] alineación trades: replay={len(rt)} live={len(lv)} ===")
rt["matched"] = False
lv["matched"] = False
pairs = []
for i, lr in lv.iterrows():
    cand = rt[(rt.symbol == lr.sym) & (rt.side == lr.side) & (~rt.matched)
              & (abs(rt.entry_T - lr.entry_T) <= pd.Timedelta("1h"))]
    if len(cand):
        j = cand.index[0]
        rt.loc[j, "matched"] = True
        lv.loc[i, "matched"] = True
        pairs.append({"sym": lr.sym, "side": lr.side, "T_live": lr.entry_T, "T_rep": rt.loc[j, "entry_T"],
                      "pnl_live": lr.pnl, "pnl_rep": rt.loc[j, "pnl_pct"],
                      "reason_live": lr.reason, "reason_rep": rt.loc[j, "reason_exit"]})
pr = pd.DataFrame(pairs)
print(f"matched (±1h, mismo lado): {len(pr)}  | live-only: {(~lv.matched).sum()}  | replay-only: {(~rt.matched).sum()}")
if len(pr):
    print(f"  de los matched, mismo reason_exit: {100*(pr.reason_live==pr.reason_rep).mean():.0f}%")
    print(f"  corr pnl live vs rep: {pr.pnl_live.corr(pr.pnl_rep):.3f}  mean|dpnl|={abs(pr.pnl_live-pr.pnl_rep).mean():.3f}pp")
print("\nlive-only por símbolo:", dict(lv[~lv.matched].groupby("sym").size()))
print("replay-only por símbolo:", dict(rt[~rt.matched].groupby("symbol").size()))

# ---------- 1C: PF ----------
ok = rt[rt.reason_exit != "open_at_end"]
p_rep = ok.pnl_pct.tolist()
p_live = lv.pnl.tolist()
print(f"\n=== 1C [{VARIANT}] PF mes (contabilidad idéntica) ===")
print(f"  REPLAY : N={len(p_rep)}  PF_bruto={pf(p_rep):.3f}  PF_neto={pf([x-FEE for x in p_rep]):.3f}  sum={sum(p_rep):+.2f}pp")
print(f"  LIVE   : N={len(p_live)}  PF_bruto={pf(p_live):.3f}  PF_neto={pf([x-FEE for x in p_live]):.3f}  sum={sum(p_live):+.2f}pp")
bysym = ok.groupby("symbol").pnl_pct.agg(["count", "sum"]).round(2)
print("\nreplay per-símbolo:")
print(bysym.to_string())
pr_out = AUDIT / f"fase1_pairs_{VARIANT}.csv"
if len(pr):
    pr.to_csv(pr_out, index=False)
print("DONE")
