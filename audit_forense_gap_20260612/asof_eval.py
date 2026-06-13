# -*- coding: utf-8 -*-
"""
E2-full evaluador de HOLDOUT: replica los picks as-of (GMM+specialist del sandbox) sobre
el periodo post-ancla INTOCADO usando el stack VPS (lo que el bot ES) + datos binance_deep.
Contabilidad idéntica (pnl_pct − 0.10pp fee RT). Leakage gate H1 sobre los trades del holdout.

Uso: python asof_eval.py --symbol BTC --anchor 2026-02-01
Holdout: A1(2025-10-01)→[2025-10-01,2026-02-01); A2(2026-02-01)→[2026-02-01,2026-05-17) (excluye mes audit).
"""
import sys, argparse, json
from pathlib import Path
import pandas as pd, numpy as np

ROOT = Path(r"c:\Users\rixip\combolab")
AUDIT = ROOT / "audit_forense_gap_20260612"
SNAP = AUDIT / "vps_snapshot" / "combolab"
sys.path.insert(0, str(SNAP)); sys.path.insert(0, str(AUDIT))
from live.brain_engine import (load_models, classify_regimes, apply_btc_override,
                               select_active_configs, generate_signals)
from leakage_gate import assert_holdout

MIN_CONF = 0.60; FEE = 0.10
HOLDOUT_END = {"2025-10-01": "2026-02-01", "2026-02-01": "2026-05-17"}  # A2 corta mes audit (ajuste #3)

def pf(p):
    gp=sum(x for x in p if x>0); gl=-sum(x for x in p if x<0)
    return gp/gl if gl>0 else (float('inf') if gp>0 else 0.0)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--symbol",required=True); ap.add_argument("--anchor",required=True)
    a=ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8",errors="replace")
    except AttributeError: pass
    sb=AUDIT/"asof_sandbox"/f"{a.symbol}_{a.anchor}"
    A=pd.Timestamp(a.anchor,tz="UTC"); END=pd.Timestamp(HOLDOUT_END[a.anchor],tz="UTC")
    symf=f"{a.symbol}/USDT"
    brain=load_models(str(sb/"regime_models"),str(sb/"regime_wf"),symbols=[symf])
    if symf not in brain.specialist_configs:
        print(f"[{a.symbol}@{a.anchor}] SIN specialist as-of (pipeline no produjo configs) — celda vacía"); return
    df=pd.read_parquet(AUDIT/"binance_deep"/f"{a.symbol}USDT_1h_binance.parquet")
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); bars=df.reset_index(drop=True)

    def window_for(T):
        idx=bars["timestamp"].searchsorted(T)
        if idx>=len(bars) or bars["timestamp"].iloc[idx]!=T: return None
        closed=bars.iloc[max(0,idx-1499):idx]; o=float(bars["open"].iloc[idx])
        forming=pd.DataFrame([{"timestamp":T,"open":o,"high":o,"low":o,"close":o,"volume":0.0}])
        return pd.concat([closed,forming],ignore_index=True)

    hours=pd.date_range(A,END-pd.Timedelta(hours=1),freq="1h")
    trades=[]; opent=None
    def close(exitT,xp,reason):
        ep=opent["ep"]
        pnl=(xp/ep-1)*100 if opent["side"]=="long" else (1-xp/ep)*100
        trades.append({"sym":a.symbol,"anchor":a.anchor,"entry_T":str(opent["eT"]),"exit_T":str(exitT),
                       "side":opent["side"],"pnl_pct":round(pnl,4),"reason":reason,"k":opent["k"]})
    for T in hours:
        w=window_for(T)
        if w is None: continue
        md={symf:w}
        reg=apply_btc_override(brain,classify_regimes(brain,md))
        act=select_active_configs(brain,reg); sig=generate_signals(brain,md,act)
        r=reg.get(symf); s=sig.get(symf)
        if r is None or s is None: continue
        st=brain.get_state(symf); action=s.get("action"); reason=s.get("reason"); conf=r["confidence"]
        price=s.get("entry_price")
        if action in ("LONG","SHORT"):
            if conf<MIN_CONF: st.position=0
            elif opent is None: opent={"eT":T,"side":"long" if action=="LONG" else "short","ep":price,"k":r["cluster"],"sl":s.get("sl_price")}
        elif action in ("CLOSE_LONG","CLOSE_SHORT") and opent:
            close(T, s.get("sl_price") if reason in("sl_hit","sl_emergency") and (s.get("sl_price") or 0)>0 else price, reason); opent=None
        elif action not in ("LONG","SHORT","HOLD") and opent:
            if not r["operable"] or act.get(symf,{}).get("config_id",-1)<0:
                close(T, price or float(bars["open"].iloc[bars["timestamp"].searchsorted(T)]), "not_operable"); opent=None
            elif conf<MIN_CONF:
                close(T, float(bars["open"].iloc[bars["timestamp"].searchsorted(T)]), "low_confidence"); opent=None; st.position=0
    if opent: close("OPEN_END",None,"open_at_end")

    out=pd.DataFrame(trades)
    closed=out[out.reason!="open_at_end"] if len(out) else out
    # leakage gate H1
    ts=[pd.Timestamp(x["entry_T"]) for _,x in closed.iterrows()] if len(closed) else []
    ok,errs=assert_holdout(A,END,ts,exclude_audit_month=(a.anchor=="2026-02-01"),label=f"{a.symbol}@{a.anchor}")
    p=[x-FEE for x in closed["pnl_pct"].tolist()] if len(closed) else []
    res={"symbol":a.symbol,"anchor":a.anchor,"holdout_end":HOLDOUT_END[a.anchor],
         "n_trades":len(p),"pf_net":round(pf(p),4) if p else None,"sum_pp":round(sum(p),2) if p else 0,
         "leakage_ok":ok,"leakage_errs":errs,
         "pre_anchor_bars":json.load(open(sb/"asof_meta.json"))["pre_anchor_bars"]}
    out.to_csv(AUDIT/f"asof_trades_{a.symbol}_{a.anchor}.csv",index=False)
    json.dump(res,open(AUDIT/f"asof_result_{a.symbol}_{a.anchor}.json","w"),indent=1)
    print(f"[{a.symbol}@{a.anchor}] holdout [{A.date()},{END.date()}) N={len(p)} PF_net={res['pf_net']} "
          f"sum={res['sum_pp']}pp prehist={res['pre_anchor_bars']} leakage={'OK' if ok else 'FAIL'}")
    if not ok:
        for e in errs: print("   →",e)

if __name__=="__main__": main()
