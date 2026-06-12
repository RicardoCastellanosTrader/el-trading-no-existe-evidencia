# -*- coding: utf-8 -*-
"""2A — Transferencia Binance→BingX: tasa de divergencia de cluster (argmax crudo,
features causales computadas una vez por serie). GMMs desplegados (snapshot VPS)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

AUDIT = Path(r"c:\Users\rixip\combolab\audit_forense_gap_20260612")
SNAP = AUDIT / "vps_snapshot" / "combolab"
sys.path.insert(0, str(SNAP))
from regime_features import compute_regime_features

W0 = pd.Timestamp("2026-05-17 12:00", tz="UTC"); W1 = pd.Timestamp("2026-06-12 11:00", tz="UTC")
SYMS = ["BTC", "ETH", "BNB", "XRP", "TRX", "ONDO", "RENDER", "POL", "SEI", "TAO",
        "SOL", "DOGE", "ADA", "BCH", "LINK"]

def classify_series(df, model):
    feats, valid = compute_regime_features(df, lookback=model["lookback"])
    X = model["scaler"].transform(feats[valid])
    probs = model["gmm"].predict_proba(X)
    k = np.argmax(probs, axis=1)
    conf = probs[np.arange(len(k)), k]
    ts = df["timestamp"].reset_index(drop=True)[pd.Series(valid)]
    return pd.DataFrame({"ts": ts.values, "k": k, "conf": conf}).assign(ts=lambda d: pd.to_datetime(d.ts, utc=True))

print(f'{"sym":7s} {"n":>4s} {"flip%":>7s} {"flip_conf>=.75%":>15s} {"conf_mean_bx":>12s}')
rows = []
for s in SYMS:
    model = joblib.load(SNAP / "regime_models" / f"{s}_regime.joblib")
    out = {}
    for feed, path in [("bx", AUDIT / "bingx_data" / f"{s}USDT_1h_bingx.parquet"),
                       ("bn", AUDIT / "binance_data" / f"{s}USDT_1h_binance.parquet")]:
        df = pd.read_parquet(path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        out[feed] = classify_series(df, model)
    m = out["bx"].merge(out["bn"], on="ts", suffixes=("_bx", "_bn"))
    m = m[(m.ts >= W0) & (m.ts <= W1)]
    flip = (m.k_bx != m.k_bn)
    both_hi = (m.conf_bx >= 0.75) & (m.conf_bn >= 0.75)
    flip_hi = (m.k_bx != m.k_bn) & both_hi
    print(f"{s:7s} {len(m):4d} {100*flip.mean():7.2f} {100*flip_hi.sum()/max(both_hi.sum(),1):15.2f} {m.conf_bx.mean():12.3f}")
    rows.append({"sym": s, "n": len(m), "flip_pct": round(100 * flip.mean(), 2),
                 "flip_hi_pct": round(100 * flip_hi.sum() / max(both_hi.sum(), 1), 2)})
pd.DataFrame(rows).to_csv(AUDIT / "fase2a_transfer_binance_bingx.csv", index=False)
print("DONE")
