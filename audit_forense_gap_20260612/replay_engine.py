# -*- coding: utf-8 -*-
"""
FASE 1 — Replay del mes live con el STACK DEL VPS (snapshot preservado, abril v2.4.4).
Replica ciclo-a-ciclo: classify_regimes (GMM+hysteresis 0.75) -> apply_btc_override ->
select_active_configs -> generate_signals, con emulación del gate de confianza 0.60
del portfolio (rollback de entradas + cierre low_confidence como reconcile live).

Variantes:
  deployed  = joblibs tal cual están en el VPS (G1 abril stale, cross-source GMM propio)
  corrected = emparejamiento compañero-de-generación (G1 mayo; cross-source GMM del source)

Aproximaciones documentadas:
  - Barra forming en hora T: OHLC = open(T), volume=0 (el bot ve ~segundos de la vela).
  - Restarts intra-ventana del bot (reset hysteresis) no replicados.
  - below_min_order / sizing no replicados (size-neutral pnl_pct).
"""
import sys, os, json, csv, time
from pathlib import Path
import numpy as np
import pandas as pd

AUDIT = Path(r"c:\Users\rixip\combolab\audit_forense_gap_20260612")
SNAP = AUDIT / "vps_snapshot" / "combolab"
sys.path.insert(0, str(SNAP))

from live.brain_engine import (load_models, classify_regimes, apply_btc_override,
                               select_active_configs, generate_signals)

VARIANT = sys.argv[1] if len(sys.argv) > 1 else "deployed"
MIN_CONF = 0.60
FEE_RT = 0.10  # pp round-trip

DEPLOY_HOUR = {
    **{s: "2026-05-17 12:00" for s in ["BTC", "ETH", "BNB", "XRP", "TRX"]},
    **{s: "2026-05-22 19:00" for s in ["ONDO", "RENDER", "POL", "SEI", "TAO"]},
    **{s: "2026-06-05 10:00" for s in ["SOL", "DOGE", "ADA", "BCH", "LINK"]},
}
SYMS = list(DEPLOY_HOUR.keys())
END = pd.Timestamp("2026-06-12 12:00", tz="UTC")

models_dir = str(SNAP / "regime_models") if VARIANT == "deployed" else str(AUDIT / "corrected_models")
configs_dir = str(SNAP / "regime_wf")

symbols_fmt = [f"{s}/USDT" for s in SYMS]
brain = load_models(models_dir, configs_dir, symbols=symbols_fmt)
print(f"[{VARIANT}] GMMs={len(brain.gmm_models)} configs={len(brain.specialist_configs)}", flush=True)

# datos BingX
bars = {}
for s in SYMS:
    df = pd.read_parquet(AUDIT / "bingx_data" / f"{s}USDT_1h_bingx.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    bars[s] = df.reset_index(drop=True)

def window_for(s, T):
    """1499 barras cerradas (< T) + forming stub en T (OHLC=open(T))."""
    df = bars[s]
    idx = df["timestamp"].searchsorted(T)  # primera barra >= T
    if idx >= len(df) or df["timestamp"].iloc[idx] != T:
        return None  # sin barra T en datos
    closed = df.iloc[max(0, idx - 1499):idx]
    o = float(df["open"].iloc[idx])
    forming = pd.DataFrame([{"timestamp": T, "open": o, "high": o, "low": o, "close": o, "volume": 0.0}])
    w = pd.concat([closed, forming], ignore_index=True)
    return w

hours = pd.date_range(pd.Timestamp("2026-05-17 12:00", tz="UTC"), END, freq="1h")
deploy_ts = {s: pd.Timestamp(v, tz="UTC") for s, v in DEPLOY_HOUR.items()}

cycles_out, trades_out, blocked_out = [], [], []
open_trades = {}  # sym -> dict

def st_sl_valid(sig, tr):
    return (sig.get("sl_price") or 0) > 0 or (tr.get("sl") or 0) > 0

def last_close(s, T):
    df = bars[s]
    idx = df["timestamp"].searchsorted(T)
    return float(df["open"].iloc[idx]) if idx < len(df) else float(df["close"].iloc[-1])

def close_trade(out, tr, exit_T, exit_price, reason, s):
    ep = tr["entry_price"]; xp = exit_price
    if not ep or not xp:
        pnl = 0.0
    elif tr["side"] == "long":
        pnl = (xp / ep - 1) * 100
    else:
        pnl = (1 - xp / ep) * 100
    out.append({"symbol": s, "side": tr["side"], "entry_T": tr["entry_T"], "exit_T": exit_T,
                "entry_price": ep, "exit_price": xp, "pnl_pct": round(pnl, 4),
                "reason_exit": reason, "k_entry": tr["k_entry"], "cfg": tr["cfg"]})

t0 = time.time()
for ci, T in enumerate(hours):
    active_syms = [s for s in SYMS if T >= deploy_ts[s]]
    md = {}
    for s in active_syms:
        w = window_for(s, T)
        if w is not None:
            md[f"{s}/USDT"] = w
    if "BTC/USDT" not in md:
        continue
    regimes = classify_regimes(brain, md)
    regimes = apply_btc_override(brain, regimes)
    active = select_active_configs(brain, regimes)
    signals = generate_signals(brain, md, active)

    for s in active_syms:
        symf = f"{s}/USDT"
        reg = regimes.get(symf); cfg = active.get(symf); sig = signals.get(symf)
        if reg is None or sig is None:
            continue
        st = brain.get_state(symf)
        act, reason = sig.get("action"), sig.get("reason")
        conf = reg["confidence"]
        cycles_out.append({"T": str(T), "symbol": s, "k": reg["cluster"], "conf": round(conf, 4),
                           "operable": reg["operable"], "cfg": cfg.get("config_id"),
                           "action": act, "reason": reason,
                           "price": sig.get("entry_price"), "sl": sig.get("sl_price")})

        # --- emulación ejecución + gate portfolio ---
        if act in ("LONG", "SHORT"):
            if conf < MIN_CONF:
                # rollback como _reconcile_brain_after_execution
                st.position = 0
                blocked_out.append({"T": str(T), "symbol": s, "action": act, "why": "low_confidence", "conf": conf})
            elif s in open_trades:
                pass  # ya en posición (no debería: brain controla)
            else:
                open_trades[s] = {"entry_T": str(T), "side": "long" if act == "LONG" else "short",
                                  "entry_price": sig.get("entry_price"), "k_entry": reg["cluster"],
                                  "cfg": cfg.get("config_id"), "sl": sig.get("sl_price")}
        elif act in ("CLOSE_LONG", "CLOSE_SHORT"):
            tr = open_trades.pop(s, None)
            if tr:
                if reason in ("sl_hit", "sl_emergency") and tr.get("sl") and st_sl_valid(sig, tr):
                    exit_price = sig.get("sl_price") or sig.get("entry_price")
                else:
                    exit_price = sig.get("entry_price")  # close de la barra (≈ fill live xx:00:10)
                close_trade(trades_out, tr, str(T), exit_price, reason, s)
        else:
            # FLAT: cierres forzados estilo reconcile live
            if s in open_trades:
                if not reg["operable"] or cfg.get("config_id", -1) < 0:
                    tr = open_trades.pop(s)
                    close_trade(trades_out, tr, str(T), sig.get("entry_price") or last_close(s, T), "not_operable", s)
                elif conf < MIN_CONF:
                    tr = open_trades.pop(s)
                    close_trade(trades_out, tr, str(T), last_close(s, T), "low_confidence", s)
                    st.position = 0

# trades aún abiertos al final
for s, tr in open_trades.items():
    close_trade(trades_out, tr, "OPEN_END", None, "open_at_end", s)

print(f"[{VARIANT}] ciclos={len(cycles_out)} trades={len(trades_out)} blocked={len(blocked_out)} "
      f"en {time.time()-t0:.0f}s", flush=True)

pd.DataFrame(cycles_out).to_csv(AUDIT / f"replay_cycles_{VARIANT}.csv", index=False)
pd.DataFrame(trades_out).to_csv(AUDIT / f"replay_trades_{VARIANT}.csv", index=False)
pd.DataFrame(blocked_out).to_csv(AUDIT / f"replay_blocked_{VARIANT}.csv", index=False)
print("WRITTEN", flush=True)
