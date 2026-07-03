#!/usr/bin/env python3
"""B7 — OI/positioning cross-sectional (fragilidad ΔOI). Descarga metrics + run_xs. CONGELADO."""
import io, json, zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd, requests
import xs_harness as xh, cs_mom as cm

HERE = Path(__file__).resolve().parent
OIDIR = HERE / "oi_data"; OIDIR.mkdir(exist_ok=True)
np.seterr(all="ignore")
URL = "https://data.binance.vision/data/futures/um/daily/metrics/{t}/{t}-metrics-{d}.zip"
DATES = list(pd.date_range("2023-01-01", "2024-12-31", freq="D").strftime("%Y-%m-%d"))

sess = requests.Session()
def dl(t, d):
    zp = OIDIR / f"{t}-metrics-{d}.zip"
    if zp.exists(): return zp if zp.stat().st_size > 0 else None
    try:
        r = sess.get(URL.format(t=t, d=d), timeout=60)
        if r.status_code != 200:
            zp.write_bytes(b""); return None
        zp.write_bytes(r.content); return zp
    except Exception:
        return None

def load_oi(sym):
    """Serie 12h de sum_open_interest (ultimo del bar) para el ticker logico."""
    tickers = cm.candidates(sym)
    rows = []
    for t in tickers:
        tasks = [(t, d) for d in DATES]
        with ThreadPoolExecutor(max_workers=24) as ex:
            zps = list(ex.map(lambda a: dl(*a), tasks))
        got = [z for z in zps if z]
        if not got: continue
        for zp in got:
            try:
                with zipfile.ZipFile(zp) as z:
                    raw = z.read([n for n in z.namelist() if n.endswith(".csv")][0])
                df = pd.read_csv(io.BytesIO(raw))
                if "sum_open_interest" not in df.columns: continue
                tcol = "create_time" if "create_time" in df.columns else df.columns[0]
                df["ts"] = pd.to_datetime(df[tcol], errors="coerce")
                rows.append(df[["ts", "sum_open_interest"]])
            except Exception:
                continue
        if rows: break   # usa el primer ticker con datos
    if not rows: return None
    d = pd.concat(rows).dropna().drop_duplicates("ts").set_index("ts").sort_index()
    return d["sum_open_interest"].astype(float)

print("descargando/leyendo OI metrics 44 sym 2023-24 ...")
grid = pd.date_range("2023-01-01", "2024-12-31 12:00", freq="12h", tz="UTC")
ois = {}
for s in cm.SYMS:
    oi = load_oi(s)
    if oi is not None and len(oi) > 100:
        if oi.index.tz is None: oi.index = oi.index.tz_localize("UTC")
        ois[s] = oi.reindex(oi.index.union(grid)).sort_index().ffill().reindex(grid)
print(f"OI disponible en {len(ois)}/{len(cm.SYMS)} sym")
OI = pd.DataFrame(ois).reindex(grid)

print("build_panels precios ...")
C, H, L, Q, F, cov = cm.build_panels(log=lambda *a: None)
OI = OI.reindex(columns=C.columns)
dOI = (OI - OI.shift(6)) / OI.shift(6)
fac = -dOI                                  # fragilidad: largo OI-cayendo, corto OI-subiendo
d7, (A7, B7s, C7) = xh.run_xs(C, H, L, Q, F, fac, rebal_bars=10, warmup=56)

def verdict(diag, Cser):
    be, bb = diag["beta_C_vs_EW"], diag["beta_C_vs_BTC"]
    cf = diag["C"]["full"]; sh = cf.get("sharpe"); dd = cf.get("maxdd_pct")
    lo, hi, _ = xh.block_bootstrap_sharpe_ci(Cser)
    s23 = diag["C"]["2023"].get("sharpe"); s24 = diag["C"]["2024"].get("sharpe")
    neutral = be is not None and bb is not None and abs(be) <= 0.15 and abs(bb) <= 0.15
    digna = neutral and sh is not None and sh >= 1.0 and lo is not None and lo > 0 and dd is not None and dd > -25 and s23 and s24 and s23 > 0 and s24 > 0
    return {"sharpe_full": sh, "CI": [round(lo, 3) if lo else None, round(hi, 3) if hi else None],
            "beta_EW": be, "beta_BTC": bb, "neutral": neutral, "maxdd_pct": dd,
            "sharpe_2023": s23, "sharpe_2024": s24, "A_long": diag["A"]["full"].get("sharpe"),
            "B_short": diag["B"]["full"].get("sharpe"), "turnover": diag["turnover_medio_por_rebal"],
            "n_sym_OI": int(OI.notna().any().sum()), "VEREDICTO": "DIGNA" if digna else "NO DIGNA"}

res = {"params": {"lookback_OI": 6, "ventana": "2023-2024", "direccion": "fragilidad(-dOI)"},
       "B7b_cross_sectional": verdict(d7, C7)}
(HERE / "results_B7.json").write_text(json.dumps(res, indent=2, default=str))
print(json.dumps(res, indent=2, default=str))
