#!/usr/bin/env python3
"""B8 — MFE squeeze (cascadas alcistas). Mirror del pipeline MFE, params CONGELADOS.
Reconstruye grid con BUY vol + entrada CORTO worst-3s (low3s) + control VOL-MATCHED
(leccion auditoria) + metrica cardinal CONJUNTA (media neta Y supervivencia)."""
import sys, io, json, time, zipfile
from pathlib import Path
import numpy as np, pandas as pd
MFE = Path(r"c:\Users\rixip\combolab\mfe_sandbox"); sys.path.insert(0, str(MFE))
import run_edge as re
HERE = Path(__file__).resolve().parent
DATA = MFE / "data"; np.seterr(all="ignore")
DROP, VZ, VEL, BW, BMIN, COOL, MAXW, SLIP, FEE, STOP = 0.003, 3.0, 15, 3600, 600, 300, 60, 3, 0.0020, 0.02
HOR = (60, 180, 300); NCTRL = 10; SEED = 20260629

def per_second_buy(zp):
    with zipfile.ZipFile(zp) as z:
        raw = z.read([n for n in z.namelist() if n.endswith(".csv")][0])
    first = raw[:200].split(b"\n", 1)[0].decode("utf-8", "replace").lower()
    hdr = "transact_time" in first or "agg_trade_id" in first
    df = pd.read_csv(io.BytesIO(raw), header=0 if hdr else None, names=None if hdr else re.COLS, usecols=range(7))
    df.columns = re.COLS
    bm = df["is_buyer_maker"]
    if bm.dtype == object:
        bm = bm.astype(str).str.strip().str.lower().map({"true": True, "false": False, "1": True, "0": False})
    bm = bm.astype(bool)
    tmax = int(df["transact_time"].max()); unit = "ns" if tmax > 1e17 else "us" if tmax > 1e14 else "ms"
    ts = pd.to_datetime(df["transact_time"], unit=unit, utc=True)
    s = pd.DataFrame({"price": df["price"].values,
                      "buy": np.where(~bm.values, df["quantity"].values, 0.0)}, index=ts).sort_index()
    return pd.DataFrame({"price": s["price"].resample("1s").last(), "hi": s["price"].resample("1s").max(),
                         "lo": s["price"].resample("1s").min(), "buy_vol": s["buy"].resample("1s").sum()})

def build_grid(sym, days, log=print):
    cache = DATA / f"grid_buy_{sym}_{days[0]}_{days[-1]}.parquet"
    if cache.exists(): return pd.read_parquet(cache)
    grids, gb, t0 = [], 0.0, time.time()
    for i, d in enumerate(days):
        try: zp = re.download_day(sym, d)
        except Exception as e: log(f"  {d} skip dl {e}"); continue
        gb += zp.stat().st_size / 1e9
        try: grids.append(per_second_buy(zp))
        except Exception as e: log(f"  {d} skip parse {e}")
        try: zp.unlink()
        except OSError: pass
        if (i + 1) % 90 == 0: log(f"  {sym} {i+1}/{len(days)} {gb:.1f}GB {(time.time()-t0)/60:.0f}min", flush=True)
    g = pd.concat(grids).sort_index()
    full = pd.date_range(g.index[0].floor("D"), g.index[-1].floor("D") + pd.Timedelta(days=1), freq="1s", tz="UTC", inclusive="left")
    g = g.reindex(full); g["price"] = g["price"].ffill()
    g["hi"] = g["hi"].fillna(g["price"]); g["lo"] = g["lo"].fillna(g["price"]); g["buy_vol"] = g["buy_vol"].fillna(0.0)
    g["low3s"] = g["lo"].rolling(SLIP).min().shift(-(SLIP - 1))   # peor precio corto = mas bajo en 3s
    try: g.to_parquet(cache)
    except Exception: pass
    return g

class S:
    def __init__(self, g):
        self.start = g.index[0]; self.price = g["price"].to_numpy(); self.hi = g["hi"].to_numpy()
        self.lo = g["lo"].to_numpy(); self.low3s = g["low3s"].to_numpy(); self.n = len(self.price)
        p = g["price"]; self.ret15 = (p / p.shift(VEL) - 1.0).to_numpy()
        bv = g["buy_vol"]; cur = bv.rolling(VEL).sum() / VEL; base = bv.shift(VEL + 1)
        self.bmean = base.rolling(BW, min_periods=BMIN).mean().to_numpy()
        bstd = base.rolling(BW, min_periods=BMIN).std()
        self.volz = ((cur - base.rolling(BW, min_periods=BMIN).mean()) / bstd).to_numpy(); self.bstd = bstd.to_numpy()
    def ts(self, pos): return self.start + pd.Timedelta(seconds=int(pos))

def triggers(s):
    mask = (s.ret15 >= DROP) & (s.volz >= VZ) & np.isfinite(s.bstd) & (s.bstd > 0)
    out, last = [], -10**9
    for p in np.flatnonzero(mask):
        if p - last >= COOL: out.append(p); last = p
    return np.array(out, dtype=np.int64)

def exhaustion(s, pt):
    hi = min(pt + MAXW, s.n - 1)
    for p in range(pt + 1, hi + 1):
        if np.isfinite(s.ret15[p]) and s.ret15[p] <= 0: return p
    return hi

def measure_short(s, pe):
    epx = s.low3s[pe]; r = {"entry_pos": pe}
    if not np.isfinite(epx) or epx <= 0:
        for H in HOR: r[f"net_{H//60}m"] = np.nan; r[f"surv_{H//60}m"] = np.nan
        return r
    stop = epx * (1 + STOP)   # corto: stop si el precio SUBE +2%
    for H in HOR:
        m = H // 60; end = pe + H
        if end >= s.n: r[f"net_{m}m"] = np.nan; r[f"surv_{m}m"] = np.nan; continue
        hi_win = s.hi[pe:end + 1]; stopped = np.any(hi_win >= stop)
        exit_px = stop if stopped else s.price[end]
        net = epx / exit_px - 1.0 - FEE     # PnL corto
        r[f"net_{m}m"] = float(net); r[f"surv_{m}m"] = bool(net > 0)
    return r

def entries(s, pos, kind):
    rows = []
    for pt in pos:
        pe = exhaustion(s, pt) if kind == "casc" else pt
        m = measure_short(s, pe); m["trigger_ts"] = s.ts(pt); m["bstd"] = float(s.bstd[pt]) if np.isfinite(s.bstd[pt]) else np.nan
        m["kind"] = kind; rows.append(m)
    return pd.DataFrame(rows)

def vol_matched_control(s, casc_bstd, n_per, seed):
    """control estratificado por decil de bstd de las cascadas (slippage regime matched)."""
    lo = BW; hi = s.n - max(HOR) - MAXW - SLIP - 2
    valid = np.flatnonzero(np.isfinite(s.bstd[lo:hi]) & (s.bstd[lo:hi] > 0)) + lo
    vb = s.bstd[valid]
    cb = casc_bstd[np.isfinite(casc_bstd)]
    if len(cb) < 10 or len(valid) < 100: return valid[:0]
    edges = np.quantile(cb, np.linspace(0, 1, 11))
    rng = np.random.default_rng(seed); picks = []
    want = np.histogram(cb, bins=edges)[0] * n_per
    for d in range(10):
        m = (vb >= edges[d]) & (vb <= edges[d + 1]); pool = valid[m]
        k = int(want[d])
        if len(pool) and k > 0:
            picks.append(rng.choice(pool, size=min(k, len(pool)), replace=False))
    return np.sort(np.concatenate(picks)) if picks else valid[:0]

def cluster_boot(casc, ctrl, col, seed=SEED, nb=10000):
    a = casc.dropna(subset=[col]).copy(); b = ctrl.dropna(subset=[col]).copy()
    if len(a) < 30 or len(b) < 30: return None
    a["w8"] = pd.to_datetime(a["trigger_ts"], utc=True).dt.floor("8h")
    b["w8"] = pd.to_datetime(b["trigger_ts"], utc=True).dt.floor("8h")
    wins = np.array(sorted(set(a["w8"]) | set(b["w8"]))); rng = np.random.default_rng(seed)
    ga = {w: g[col].values for w, g in a.groupby("w8")}; gb = {w: g[col].values for w, g in b.groupby("w8")}
    diffs = []
    for _ in range(nb):
        pick = rng.choice(len(wins), size=len(wins), replace=True)
        va = np.concatenate([ga[wins[i]] for i in pick if wins[i] in ga]) if any(wins[i] in ga for i in pick) else np.array([])
        vb = np.concatenate([gb[wins[i]] for i in pick if wins[i] in gb]) if any(wins[i] in gb for i in pick) else np.array([])
        if len(va) and len(vb): diffs.append(va.mean() - vb.mean())
    d = np.array(diffs)
    return {"casc_mean": float(a[col].mean()), "ctrl_mean": float(b[col].mean()),
            "diff_mean": float(a[col].mean() - b[col].mean()),
            "CI": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))], "n_casc": len(a), "n_ctrl": len(b)}

SMOKE = "--smoke" in sys.argv
if SMOKE:
    months = [("2024", "03")]
else:
    months = [(y, f"{m:02d}") for y in ("2023", "2024") for m in range(1, 13)]
def days_of(months):
    ds = []
    for y, m in months:
        ds += list(pd.date_range(f"{y}-{m}-01", periods=32, freq="D").strftime("%Y-%m-%d"))
        ds = [d for d in ds if d[:7] == f"{y}-{m}"] + [d for d in ds if d[:7] != f"{y}-{m}"]
    # simpler: full range
    return None
allres = {}
for sym in ("BTCUSDT", "ETHUSDT"):
    if SMOKE:
        days = list(pd.date_range("2024-03-01", "2024-03-31", freq="D").strftime("%Y-%m-%d"))
    else:
        days = list(pd.date_range("2023-01-01", "2024-12-31", freq="D").strftime("%Y-%m-%d"))
    print(f"=== {sym} ({'SMOKE' if SMOKE else 'FULL'}) {len(days)} dias ===", flush=True)
    g = build_grid(sym, days); s = S(g)
    trig = triggers(s); print(f"  {sym}: {len(trig)} cascadas alcistas", flush=True)
    casc = entries(s, trig, "casc")
    ctrl_pos = vol_matched_control(s, casc["bstd"].values, NCTRL, SEED)
    ctrl = entries(s, ctrl_pos, "ctrl")
    sym_res = {"n_casc": int(len(casc)), "n_ctrl": int(len(ctrl))}
    for H in HOR:
        m = H // 60
        net = cluster_boot(casc, ctrl, f"net_{m}m")
        sv = cluster_boot(casc, ctrl, f"surv_{m}m")
        sym_res[f"net_{m}m"] = net; sym_res[f"surv_{m}m"] = sv
    allres[sym] = sym_res
    print(f"  {sym} 3m net: {sym_res.get('net_3m')}", flush=True)

# veredicto conjunto (usa 3m como horizonte de referencia, pooled BTC+ETH via medias reportadas)
def digno(sym_res):
    n = sym_res.get("net_3m"); sv = sym_res.get("surv_3m")
    if not n or not sv: return False
    return n["casc_mean"] > 0 and n["CI"][0] > 0 and sv["diff_mean"] > 0 and sv["CI"][0] > 0
allres["VEREDICTO"] = {sym: ("DIGNO" if digno(allres[sym]) else "MUERE") for sym in ("BTCUSDT", "ETHUSDT")}
out = HERE / ("results_B8_smoke.json" if SMOKE else "results_B8.json")
out.write_text(json.dumps(allres, indent=2, default=str))
print(json.dumps(allres["VEREDICTO"], indent=2))
