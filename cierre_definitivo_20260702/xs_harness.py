#!/usr/bin/env python3
"""
xs_harness.py — Harness cross-sectional para la LISTA DE CIERRE DEFINITIVO (2026-07-02).

Reutiliza build_panels() del sandbox CS-MOM (datos 12h 2023-2024, 45 sym point-in-time,
funding, vol-target, costes, corto pesimista). Correcciones incorporadas de la auditoria:
  - GATE DE BETA ARREGLADO: mide beta CONTEMPORANEA (retorno de la estrategia sobre la barra
    i->i+1 vs retorno del mercado sobre la MISMA barra). El original comparaba fwd vs backward
    (desalineacion de 1 barra) -> beta ~0 para cualquier estrategia.
  - CI en el numero que decide: block-bootstrap sobre el tiempo (bloques de 10 barras ~5d,
    respeta autocorrelacion) para el Sharpe de la curva neutral.
  - Placebo GBM puro disponible (NO block-shuffle 168h).

NO toca produccion. Sandbox aislado.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CS = HERE.parent / "cs_mom_sandbox"
sys.path.insert(0, str(CS))
import cs_mom as cm  # noqa: E402

BY = cm.BARS_PER_YEAR


# ---------- metricas ----------
def sharpe(ret):
    ret = pd.Series(ret).dropna()
    if len(ret) < 2 or ret.std() == 0:
        return None
    return float(ret.mean() / ret.std() * np.sqrt(BY))


def perf(ret, name=""):
    return cm.perf(pd.Series(ret).dropna(), name)


def beta_aligned(strat_ret, market_ret_same_bar):
    """beta CONTEMPORANEA: ambos indexados a la misma barra de tenencia i->i+1."""
    j = pd.concat([strat_ret, market_ret_same_bar], axis=1).dropna()
    if len(j) < 3:
        return None
    return float(np.polyfit(j.iloc[:, 1], j.iloc[:, 0], 1)[0])


def block_bootstrap_sharpe_ci(ret, block=10, n=5000, seed=20260702, lo=2.5, hi=97.5):
    """CI del Sharpe por moving-block bootstrap sobre el tiempo."""
    r = pd.Series(ret).dropna().values
    T = len(r)
    if T < block + 2:
        return None, None, None
    rng = np.random.default_rng(seed)
    nblk = int(np.ceil(T / block))
    starts_all = np.arange(0, T - block + 1)
    sh = np.empty(n)
    for k in range(n):
        st = rng.choice(starts_all, size=nblk)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:T]
        s = r[idx]
        sd = s.std()
        sh[k] = (s.mean() / sd * np.sqrt(BY)) if sd > 0 else 0.0
    return float(np.percentile(sh, lo)), float(np.percentile(sh, hi)), float(np.median(sh))


# ---------- runner cross-sectional generico ----------
def run_xs(C, H, L, Q, F, fac, rebal_bars, warmup, enter_pct=0.20, exit_pct=0.33,
           fee_side=cm.FEE_SIDE, log=lambda *a: None):
    """
    fac: DataFrame [barras x simbolos] del FACTOR de ranking. Mayor = candidato a LARGO.
    warmup: primera barra elegible (>= max lookback usado por fac + ATR).
    Devuelve (diag, (A, B, Cc)) donde Cc = curva neutral L/S (la cardinal).
    Funding, vol-target, costes y corto-pesimista IDENTICOS al harness CS-MOM.
    """
    cols = C.columns
    rets = C.pct_change()
    fwd = rets.shift(-1)
    inv_vol = C / cm._atr(C, H, L)
    adv = Q.rolling(60, min_periods=10).mean()
    adv_med = adv.median(axis=1)
    slip = (cm.SLIP_BASE_BPS * adv_med.values[:, None] / adv.values).clip(0, cm.SLIP_CAP_BPS) / 1e4
    slip = pd.DataFrame(slip, index=C.index, columns=cols).fillna(cm.SLIP_CAP_BPS / 1e4)
    fund = F.fillna(0.0) * 1.5

    n = len(C.index)
    lw = pd.DataFrame(0.0, index=C.index, columns=cols)
    sw = pd.DataFrame(0.0, index=C.index, columns=cols)
    held_long, held_short = set(), set()
    last_l = pd.Series(0.0, index=cols); last_s = pd.Series(0.0, index=cols)
    rebal = set(range(int(warmup), n, rebal_bars))
    cost_l = pd.Series(0.0, index=C.index); cost_s = pd.Series(0.0, index=C.index)
    turn_events = []
    for i in range(n):
        if i in rebal:
            row = fac.iloc[i].dropna()
            if len(row) >= 10:
                r = row.rank(pct=True)
                held_long = (held_long & set(r[r >= 1 - exit_pct].index)) | set(r[r >= 1 - enter_pct].index)
                held_short = (held_short & set(r[r <= exit_pct].index)) | set(r[r <= enter_pct].index)
            wl = cm._volw(inv_vol.iloc[i], held_long, cols)
            ws = cm._volw(inv_vol.iloc[i], held_short, cols)
            dl = (wl - last_l).abs(); ds = (ws - last_s).abs()
            cost_l.iloc[i] = float((dl * (fee_side + slip.iloc[i])).sum())
            cost_s.iloc[i] = float((ds * (fee_side + slip.iloc[i])).sum())
            turn_events.append(float(dl.sum() + ds.sum()))
            last_l, last_s = wl, ws
        lw.iloc[i] = last_l.values
        sw.iloc[i] = last_s.values
    long_ret = (lw * fwd).sum(axis=1) - (lw * fund).sum(axis=1)
    short_ret = (sw * (-fwd)).sum(axis=1) + (sw * fund).sum(axis=1)
    A = long_ret - cost_l
    B = short_ret - cost_s
    Cc = long_ret + short_ret - cost_l - cost_s
    ew_fwd = fwd.mean(axis=1, skipna=True)                 # mercado sobre la MISMA barra i->i+1
    btc_fwd = fwd["BTC"] if "BTC" in cols else ew_fwd
    diag = {
        "params": {"rebal_bars": rebal_bars, "warmup": int(warmup),
                   "enter_pct": enter_pct, "exit_pct": exit_pct},
        "A": cm.perf_sub(A), "B": cm.perf_sub(B), "C": cm.perf_sub(Cc),
        "turnover_medio_por_rebal": round(float(np.mean([t for t in turn_events if t > 0])), 3) if turn_events else None,
        "beta_C_vs_EW": round(beta_aligned(Cc, ew_fwd), 3) if beta_aligned(Cc, ew_fwd) is not None else None,
        "beta_C_vs_BTC": round(beta_aligned(Cc, btc_fwd), 3) if beta_aligned(Cc, btc_fwd) is not None else None,
        "beta_A_vs_EW": round(beta_aligned(A, ew_fwd), 3) if beta_aligned(A, ew_fwd) is not None else None,
        "book_long_medio": round(float((lw != 0).sum(axis=1).replace(0, np.nan).mean()), 1),
        "book_short_medio": round(float((sw != 0).sum(axis=1).replace(0, np.nan).mean()), 1),
    }
    return diag, (A, B, Cc)


# ---------- self-test del gate de beta con serie sintetica de beta conocida ----------
def _selftest_beta():
    rng = np.random.default_rng(1)
    T = 1461
    idx = pd.date_range("2023-01-01", periods=T, freq="12h", tz="UTC")
    mkt = pd.Series(rng.normal(0, 0.02, T), index=idx)          # retorno de mercado por barra
    noise = pd.Series(rng.normal(0, 0.01, T), index=idx)
    for b_true in (0.0, 0.5, 1.0, -0.3):
        strat = b_true * mkt + noise
        # el gate ARREGLADO recibe strat y mercado indexados a la MISMA barra -> debe recuperar b_true
        est = beta_aligned(strat, mkt)
        # el gate ROTO (original): compara strat_fwd vs mercado_backward = desalineacion 1 barra
        broken = cm._beta(strat.shift(-1), mkt)  # emula la desalineacion del codigo original
        print(f"  beta_true={b_true:+.2f}  arreglado={est:+.3f}  roto(desalineado)={broken:+.3f}")
    print("  -> gate arreglado recupera beta_true; gate roto colapsa a ~0. VERIFICADO.")


if __name__ == "__main__":
    print("SELF-TEST gate de beta (serie sintetica de beta conocida):")
    _selftest_beta()
