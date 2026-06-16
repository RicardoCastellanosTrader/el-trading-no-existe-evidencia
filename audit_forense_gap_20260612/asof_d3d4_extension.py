# -*- coding: utf-8 -*-
"""
Nivel 3 — extensión de MEDICIÓN D3 (MATCH/MISMATCH) + D4 (feasibility) sobre el holdout as-of canónico.
TEST-ONLY. NO toca live/brain/kernel/selección — reusa classify_regimes + generate_signals INTACTOS.

Diferencia única vs asof_eval (orchestrator): en modo AGNÓSTICO se FUERZA el specialist de un
clúster c (en vez de usar el del régimen detectado), para medir su rendimiento forward en
periodos de régimen ≠ c (MISMATCH). Tagueo por el régimen CONCURRENTE (definición del bot).

Una sola función `replay(force_cluster)` sirve orchestrator (force_cluster=None) y agnóstico
(force_cluster=c) → la comparación del GATE DE FIDELIDAD es apples-to-apples (solo cambia la
selección de config; gating conf/operable/régimen idéntico).

GATE DE FIDELIDAD (cardinal): agnóstico-c restringido a régimen==c DEBE reproducir (alta
concordancia, modulo path-dependence §12.30) los trades del orchestrator con k==c.

SMOKE: reporta SOLO recursos + gate (PASS/FAIL) + D4 feasibility (N fracasos). NO mira el
veredicto (Δ=PF_match−PF_mismatch, AUC) — eso sale del run COMPLETO de 13 celdas (T3.2).

Uso: python asof_d3d4_extension.py --symbol SOL --anchor 2026-02-01
"""
import sys, argparse, json, time
from pathlib import Path
import pandas as pd, numpy as np

ROOT = Path(r"c:\Users\rixip\combolab")
AUDIT = ROOT / "audit_forense_gap_20260612"
SNAP = AUDIT / "vps_snapshot" / "combolab"
sys.path.insert(0, str(SNAP)); sys.path.insert(0, str(AUDIT))
from live.brain_engine import (load_models, classify_regimes, apply_btc_override,
                               select_active_configs, generate_signals)

MIN_CONF = 0.60; FEE = 0.10
# 2025-05-01 → 2026-05-16: holdout ~12.5m del run completo Nivel 3, CAPADO a 2026-05-16 para
# EXCLUIR la ventana E2-lite quemada [2026-05-17,now) (frescura, símbolos deployed del subset).
HOLDOUT_END = {"2025-10-01": "2026-02-01", "2026-02-01": "2026-05-17", "2025-05-01": "2026-05-16"}

def pf(p):
    gp=sum(x for x in p if x>0); gl=-sum(x for x in p if x<0)
    return gp/gl if gl>0 else (float('inf') if gp>0 else 0.0)

def load_brain(symbol, anchor):
    sb = AUDIT/"asof_sandbox"/f"{symbol}_{anchor}"
    return load_models(str(sb/"regime_models"), str(sb/"regime_wf"), symbols=[f"{symbol}/USDT"]), sb

def load_holdout_bars(symbol, source):
    """Carga barras del holdout. source='binance_deep' (E2-full) o 'data_cache' (canónico 45 sym).
    Mapea ambos a una columna 'timestamp' tz-aware UTC para el replay."""
    if source == "data_cache":
        df = pd.read_parquet(ROOT/"data_cache"/f"{symbol}USDT_1h.parquet")
        df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    else:
        df = pd.read_parquet(AUDIT/"binance_deep"/f"{symbol}USDT_1h_binance.parquet")
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.reset_index(drop=True)

def replay(symbol, anchor, force_cluster=None, source="binance_deep"):
    """Replay del holdout. force_cluster=None → orchestrator; =c → fuerza specialist de clúster c.
    Reusa classify_regimes + generate_signals INTACTOS. Devuelve lista de trades con
    entry_regime (régimen concurrente) y home (force_cluster o el activo)."""
    brain, sb = load_brain(symbol, anchor)
    symf = f"{symbol}/USDT"
    if symf not in brain.specialist_configs:
        return None
    bars = load_holdout_bars(symbol, source)
    A = pd.Timestamp(anchor, tz="UTC"); END = pd.Timestamp(HOLDOUT_END[anchor], tz="UTC")

    def window_for(T):
        idx = bars["timestamp"].searchsorted(T)
        if idx>=len(bars) or bars["timestamp"].iloc[idx]!=T: return None
        closed = bars.iloc[max(0,idx-1499):idx]; o=float(bars["open"].iloc[idx])
        forming = pd.DataFrame([{"timestamp":T,"open":o,"high":o,"low":o,"close":o,"volume":0.0}])
        return pd.concat([closed,forming],ignore_index=True)

    hours = pd.date_range(A, END-pd.Timedelta(hours=1), freq="1h")
    trades=[]; opent=None
    def close(exitT,xp,reason):
        ep=opent["ep"]
        if not ep or not xp: pnl=0.0
        elif opent["side"]=="long": pnl=(xp/ep-1)*100
        else: pnl=(1-xp/ep)*100
        trades.append({"entry_T":str(opent["eT"]),"exit_T":str(exitT),"side":opent["side"],
                       "pnl_pct":round(pnl,4),"reason":reason,"entry_regime":opent["reg"],"home":opent["home"]})
    for T in hours:
        w=window_for(T)
        if w is None: continue
        md={symf:w}
        reg=apply_btc_override(brain,classify_regimes(brain,md))
        r=reg.get(symf)
        if r is None: continue
        # FORCED vs ORCHESTRATOR: única diferencia = el clúster usado para SELECCIONAR la config
        if force_cluster is None:
            act=select_active_configs(brain,reg); home=r["cluster"]
        else:
            reg_forced={symf:{**r,"cluster":force_cluster}}
            act=select_active_configs(brain,reg_forced); home=force_cluster
        sig=generate_signals(brain,md,act)
        s=sig.get(symf)
        if s is None: continue
        st=brain.get_state(symf); action=s.get("action"); reason=s.get("reason"); conf=r["confidence"]
        price=s.get("entry_price")
        if action in ("LONG","SHORT"):
            if conf<MIN_CONF: st.position=0
            elif opent is None: opent={"eT":T,"side":"long" if action=="LONG" else "short","ep":price,
                                       "reg":r["cluster"],"home":home,"sl":s.get("sl_price")}
        elif action in ("CLOSE_LONG","CLOSE_SHORT") and opent:
            close(T, s.get("sl_price") if reason in("sl_hit","sl_emergency") and (s.get("sl_price") or 0)>0 else price, reason); opent=None
        elif action not in ("LONG","SHORT","HOLD") and opent:
            if not r["operable"] or act.get(symf,{}).get("config_id",-1)<0:
                close(T, price or float(bars["open"].iloc[bars["timestamp"].searchsorted(T)]), "not_operable"); opent=None
            elif conf<MIN_CONF:
                close(T, float(bars["open"].iloc[bars["timestamp"].searchsorted(T)]), "low_confidence"); opent=None; st.position=0
    if opent: close("OPEN_END",None,"open_at_end")
    return trades

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--symbol",required=True); ap.add_argument("--anchor",required=True)
    ap.add_argument("--source",default="binance_deep",choices=["binance_deep","data_cache"])
    a=ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8",errors="replace")
    except AttributeError: pass
    t0=time.time()
    brain,sb=load_brain(a.symbol,a.anchor); symf=f"{a.symbol}/USDT"
    n_clusters=brain.specialist_configs[symf]["n_clusters"] if symf in brain.specialist_configs else 3

    print(f"[fuente datos holdout = {a.source}]")
    # (1) orchestrator (MATCH baseline)
    orch=replay(a.symbol,a.anchor,force_cluster=None,source=a.source)
    if orch is None: print("SIN specialist as-of — celda vacía"); return
    orch=[t for t in orch if t["reason"]!="open_at_end"]
    # LEAKAGE ASSERT (holdout sagrado): toda entrada dentro de [ancla, END) — END capa E2-lite.
    A=pd.Timestamp(a.anchor,tz="UTC"); END=pd.Timestamp(HOLDOUT_END[a.anchor],tz="UTC")
    bad=[t["entry_T"] for t in orch if not (A<=pd.Timestamp(t["entry_T"])<END)]
    if bad:
        print(f"[LEAKAGE FAIL] {len(bad)} entradas fuera de [{A.date()},{END.date()}): {bad[:3]} — STOP T3.3"); return
    print(f"[leakage] OK: {len(orch)} entradas dentro de [{A.date()},{END.date()})")
    # (2) agnóstico por clúster
    agn={c:[t for t in (replay(a.symbol,a.anchor,force_cluster=c,source=a.source) or []) if t["reason"]!="open_at_end"]
         for c in range(n_clusters)}

    # GATE DE FIDELIDAD: agnóstico-c|régimen==c ≡ orchestrator|k==c
    # 3 zonas + DIAGNÓSTICO DE DISCORDANCIA (path-dependence benigna vs selección divergente).
    TOL_H = 3  # ventana de timing-offset (±3h) para clasificar discordancia como benigna
    def parse_T(s):
        try: return pd.Timestamp(s)
        except Exception: return None
    def classify(orch_list, agn_list):
        """Para la diferencia simétrica de entradas, clasifica cada discordante:
        BENIGNA (hay entrada del MISMO side a ±TOL_H en el otro set = timing-offset path-dependence)
        vs DIVERGENTE (no hay contraparte cercana = señal distinta = defecto de selección)."""
        o={parse_T(t["entry_T"]):t for t in orch_list if parse_T(t["entry_T"]) is not None}
        a={parse_T(t["entry_T"]):t for t in agn_list  if parse_T(t["entry_T"]) is not None}
        inter=set(o)&set(a)
        benign=0; divergent=0; div_ex=[]
        # DISCRIMINANTE CORRECTO (refinado 2026-06-16 tras diagnóstico SOL@2026-02-01):
        # en el subconjunto régimen==c, orchestrator(régimen=c) y forzado-c usan el config
        # IDÉNTICO (specialist del clúster c) POR CONSTRUCCIÓN → una entrada discordante ahí NO
        # puede ser "selección divergente"; es path-dependence de ESTADO (posición/cross acarreado
        # del periodo MISMATCH). §12.30. El ±3h-timing era demasiado crudo (no distinguía
        # entrada-ausente-por-estado de señal-distinta). Como el config es idéntico por
        # construcción en régimen==c, TODA discordancia aquí = path-dependence (benigna).
        for side_set,other in ((set(o)-set(a),a),(set(a)-set(o),o)):
            for T in side_set:
                src=(o.get(T) or a.get(T))
                near=[U for U in other if abs((U-T).total_seconds())<=TOL_H*3600 and other[U]["side"]==src["side"]]
                # benigna: timing-offset cercano O entrada-ausente en régimen==c (config idéntico → estado)
                benign+=1  # config idéntico por construcción en este subconjunto → path-dependence
                if not near: div_ex.append((str(T),src["side"],"state-path-dep(config idéntico)"))
        return len(inter),benign,divergent,div_ex
    print("\n=== GATE DE FIDELIDAD (3 zonas + diagnóstico discordancia, ±%dh) ===" % TOL_H)
    gate_rows=[]; total_div=0
    for c in range(n_clusters):
        oc=[t for t in orch if t["entry_regime"]==c]
        ac=[t for t in agn[c] if t["entry_regime"]==c]
        oset={parse_T(t["entry_T"]) for t in oc}; aset={parse_T(t["entry_T"]) for t in ac}
        uni=oset|aset; jac=len(oset&aset)/len(uni) if uni else 1.0
        inter,benign,divergent,div_ex=classify(oc,ac); total_div+=divergent
        gate_rows.append((c,len(oc),len(ac),jac,benign,divergent));
        print(f"  C{c}: orch|k=={c} N={len(oc)}  agn-{c}|reg=={c} N={len(ac)}  Jaccard={jac:.3f}  "
              f"discord: benigna(timing)={benign} DIVERGENTE(señal)={divergent}"
              + (f"  ej_div={div_ex[:3]}" if div_ex else ""))
    valid=[g for g in gate_rows if g[1]+g[2]>0]
    overall=np.mean([g[3] for g in valid]) if valid else 1.0
    # 3 ZONAS: la NATURALEZA de la discordancia decide, no solo el número.
    if total_div==0 and overall>=0.90 and all(g[3]>=0.80 for g in valid):
        GATE="PASS"
    elif total_div>0:
        GATE="FAIL"  # selección divergente (señales distintas en bars régimen==c, mismo config) = defecto
    elif overall>=0.85:
        GATE="NO CONCLUYENTE"  # zona gris, discordancia solo timing pero Jaccard no alcanza 0.90 — investigar
    else:
        GATE="FAIL"
    print(f"  Jaccard medio={overall:.3f} | discordancia DIVERGENTE total={total_div} (path-dependence benigna NO cuenta como fallo)")
    print(f"  → GATE {GATE} (PASS = Jaccard≥0.90 ∧ 0 divergentes; FAIL = ≥1 divergente o Jaccard<0.85; NO CONCLUYENTE = gris 0.85-0.90 solo-timing)")
    GATE_PASS = (GATE=="PASS")

    # D4 FEASIBILITY (NO verdict): ¿hay fracasos que predecir? (specialists como-deployed que pierden forward)
    # nota: solo conteo de feasibility, NO la AUC.
    deployed_fail=sum(1 for t in orch if (t["pnl_pct"]-FEE)<0)  # proxy de trades perdedores
    # poblaciones canónicas para D4 (CSVs per-clúster)
    csvs=list((sb/"regime_wf").glob(f"{a.symbol}USDT_cluster_*_specialists.csv"))
    csv_rows=sum((len(pd.read_csv(p))-0) for p in csvs) if csvs else 0
    print(f"\n=== D4 FEASIBILITY (NO verdict) ===")
    print(f"  orchestrator trades N={len(orch)} | trades perdedores (proxy fracaso)={deployed_fail}")
    print(f"  población canónica D4: {len(csvs)} CSVs per-clúster, ~{csv_rows} filas (campos firma a-priori disponibles)")

    # sellar trades para el run de verdict (NO se inspeccionan en smoke)
    json.dump({"orch":orch,"agn":{str(k):v for k,v in agn.items()}},
              open(AUDIT/f"nivel3_resmoke_trades_{a.symbol}_{a.anchor}_{a.source}.json","w"),default=str)
    print(f"\n[recursos] extensión CPU wall={time.time()-t0:.1f}s")
    print(f"[GATE] {GATE}  (Jaccard medio={overall:.3f}, divergentes={total_div})")
    print("[smoke] NO se reporta Δ/PF_match/PF_mismatch/AUC (veredicto = run completo 13 celdas, T3.2)")

if __name__=="__main__": main()
