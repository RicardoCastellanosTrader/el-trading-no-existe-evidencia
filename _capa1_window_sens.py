"""CAPA 1 PARTE A.2 — Discriminador de convergencia drift-vs-bug (READ-ONLY).

Mide la divergencia de la MA adaptativa de período largo (SLOW+TREND) entre:
  - full-series (kernel/backtest, seeded bar 0)
  - rolling-1500 (live OHLCV_LIMIT)
  - rolling-500 (verify_test harness)
vs el valor full en cada bar. Usa lab_historico.calc_ma (single-source-of-truth).

Predicción drift path-dependent (NO bug): div_500 > div_1500 -> ~0 a medida que la
ventana se acerca a full (el seeding se diluye). Si div NO decrece con la ventana, o
afecta MAs cuya ventana ya excede varios períodos -> sospechoso (bug).
"""
import numpy as np, pandas as pd, json
from pathlib import Path
import lab_historico_numba_v8_3 as lh

# Config top-1 desplegada de cada divergente (de audit_capa1_detail): (slow_type, slow_p), (trend_type, trend_p)
CONFIGS = {
    "ETH/USDT":    [("FRAMA", 60), ("FRAMA", 240)],
    "ONDO/USDT":   [("KAMA", 57),  ("KAMA", 228)],
    "TRX/USDT":    [("VIDYA", 69), ("VIDYA", 276)],
    "RENDER/USDT": [("McGinley", 45), ("McGinley", 180)],
}
N = 8000
K = 60          # bars finales sobre los que medir divergencia steady-state
WINDOWS = [500, 1500]

def load(sym):
    sc = sym.replace("/", "").replace("USDT", "")
    df = pd.read_parquet(Path("data_cache") / f"{sc}USDT_1h.parquet")
    if "timestamp" not in df.columns and "timestamp_ms" in df.columns:
        df = df.rename(columns={"timestamp_ms": "timestamp"})
    return df.tail(N).reset_index(drop=True)

def ma_full(ma_type, c, h, l, v, p):
    return lh.calc_ma(ma_type, c, h, l, v, p)

print(f"{'sym':12} {'MA(period)':16} {'div_roll500':>12} {'div_roll1500':>13} {'ratio 1500/500':>15}")
out = {}
for sym, mas in CONFIGS.items():
    df = load(sym)
    c = df["close"].values.astype(np.float64); h = df["high"].values.astype(np.float64)
    l = df["low"].values.astype(np.float64); v = df["volume"].values.astype(np.float64)
    n = len(c)
    out[sym] = {}
    for ma_type, p in mas:
        full = ma_full(ma_type, c, h, l, v, p)
        divs = {W: [] for W in WINDOWS}
        for i in range(n - K, n):
            ref = full[i]
            if not np.isfinite(ref) or ref == 0:
                continue
            for W in WINDOWS:
                s = max(0, i - W + 1)
                w = ma_full(ma_type, c[s:i+1], h[s:i+1], l[s:i+1], v[s:i+1], p)
                wv = w[-1]
                if np.isfinite(wv):
                    divs[W].append(abs(wv - ref) / abs(ref))
        d500 = float(np.mean(divs[500])) * 100 if divs[500] else float("nan")
        d1500 = float(np.mean(divs[1500])) * 100 if divs[1500] else float("nan")
        ratio = (d1500 / d500) if d500 else float("nan")
        out[sym][f"{ma_type}({p})"] = {"div_roll500_pct": round(d500, 4), "div_roll1500_pct": round(d1500, 4)}
        print(f"{sym:12} {ma_type+'('+str(p)+')':16} {d500:>11.4f}% {d1500:>12.4f}% {ratio:>15.3f}")

json.dump(out, open("audit_capa1_window_sens_results.json", "w"), indent=2)
print("\nInterpretación: div_roll500 = divergencia que ve verify_test; div_roll1500 = la que")
print("vería el bot LIVE (OHLCV_LIMIT=1500). ratio<<1 => la ventana live cierra el gap")
print("=> truncamiento de warmup adaptativo (drift path-dependent), NO bug lógico.")
print("Saved: audit_capa1_window_sens_results.json")
