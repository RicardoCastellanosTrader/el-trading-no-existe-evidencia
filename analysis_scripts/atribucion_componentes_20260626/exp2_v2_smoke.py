# -*- coding: utf-8 -*-
"""
Exp#2 v2 SMOKE: (A) deteccion sensata + (B) NO-LOOK-AHEAD (prefix-invariance, re-precalc MR
truncado) + (C) 1 celda as-of BTC + (D) validacion visual XRP (bloques cerca de ~1.04).
NO barrido 45 (requiere T3.1-Exp2). Gatillo = MR Tenkan/HA-diaria-forming reusado.
"""
import sys, os, time
import numpy as np
ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT); os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626"))
import regime_walk_forward as rwf
import mean_reversion_features as mrf
import ob_detector_v2 as ob


def zones(df, sym):
    d = mrf.precalculate_mean_reversion(sym, df)
    return d['zone_bull_forming'], d['zone_bear_forming']


def arrays(df):
    return (df['open'].values.astype(float), df['high'].values.astype(float),
            df['low'].values.astype(float), df['close'].values.astype(float))


# ================= BTC =================
SYM = "BTC/USDT"
df = rwf.load_full_history(SYM)
o, h, l, c = arrays(df)
zb, zr = zones(df, SYM)
n = len(c)
print(f"[DATA] {SYM} {n} barras | gatillos bull={int(((zb[1:])&(~zb[:-1])).sum())} bear={int(((zr[1:])&(~zr[:-1])).sum())}")

print("\n===== (A) DETECCION v2 (gatillo-ancla + bloque choque + TP cruce) =====")
t0 = time.time()
trades = ob.detect_ob_v2(o, h, l, c, zb, zr)
dt = time.time() - t0
pnls = np.array([x['pnl'] for x in trades])
nb = sum(1 for x in trades if x['side'] > 0)
rc = {0: 'tp_cruce', 1: 'stop', 2: 'time'}
rr = {rc[k]: sum(1 for x in trades if x['reason'] == k) for k in (0, 1, 2)}
pf, gp, gl = ob.pf_from_pnls(pnls)
print(f"[DET] {len(trades)} trades ({nb}L/{len(trades)-nb}S) en {dt:.2f}s | win={100*(pnls>0).mean():.1f}% | salidas {rr} | PF(all)={pf:.3f} | pnl_medio={pnls.mean():.3f}%")
for x in trades[:3]:
    print(f"   {'L' if x['side']>0 else 'S'} gat@{x['gat_bar']} block@{x['block_bar']}[{x['block_low']:.2f}-{x['block_high']:.2f}] entry@{x['entry_bar']}({x['entry_price']:.2f}) exit@{x['exit_bar']}({x['exit_price']:.2f}) {rc[x['reason']]} pnl={x['pnl']:.2f}%")

print("\n===== (B) NO-LOOK-AHEAD (prefix-invariance, re-precalc MR truncado) =====")
T = n - 4000
dft = df.iloc[:T].copy()
ot, ht, lt, ct = arrays(dft)
zbt, zrt = zones(dft, SYM)
trades_tr = ob.detect_ob_v2(ot, ht, lt, ct, zbt, zrt)
def key(x):
    return (x['gat_bar'], x['block_bar'], x['side'], x['entry_bar'], x['exit_bar'],
            round(x['entry_price'], 6), round(x['exit_price'], 6), x['reason'])
A = {key(x) for x in trades if x['exit_bar'] < T - 1}
B = {key(x) for x in trades_tr if x['exit_bar'] < T - 1}
ident = A == B
print(f"[NLA] resueltos<T: full={len(A)} trunc={len(B)} | IDENTICOS={ident}")
if not ident:
    print(f"[NLA][FAIL] solo_full={list(A-B)[:2]} solo_trunc={list(B-A)[:2]}")
print(f"[GATE B] {'PASS — causal' if ident else 'FAIL — leakage (T3.2)'}")

print("\n===== (C) 1 CELDA as-of (BTC) =====")
model = rwf.load_regime_model(SYM)
cl, ncl = rwf.compute_cluster_labels(df, model)
eps = rwf.identify_episodes(cl, ncl, min_bars=rwf.MIN_EPISODE_BARS)
reg, ndob, split = rwf.build_regime_labels(cl, eps, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
valid = [k for k in range(ncl) if split[k]['valid']]
fwd = [x['pnl'] for x in trades if 0 <= x['entry_bar'] < len(reg) and reg[x['entry_bar']] >= ncl and (reg[x['entry_bar']]-ncl) in valid]
trn = [x['pnl'] for x in trades if 0 <= x['entry_bar'] < len(reg) and 0 <= reg[x['entry_bar']] < ncl]
pf_f, gpf, glf = ob.pf_from_pnls(fwd); pf_t, _, _ = ob.pf_from_pnls(trn)
wf = int((np.array(fwd) > 0).sum()) if fwd else 0
b = rwf._bootstrap_pf_fwd_vectorized(np.array([len(fwd)]), np.array([wf]), np.array([gpf]), np.array([glf]))
print(f"[CELL] pf_tr={pf_t:.3f}(n={len(trn)}) | pf_fwd={pf_f:.3f} CI=[{b['pf_fwd_ci_low'][0]:.3f},{b['pf_fwd_ci_high'][0]:.3f}] (n_fwd={len(fwd)})")

print("\n===== (D) VALIDACION VISUAL XRP (bloques cerca de ~1.00-1.06) =====")
dfx = rwf.load_full_history("XRP/USDT")
ox, hx, lx, cx = arrays(dfx)
zbx, zrx = zones(dfx, "XRP/USDT")
trx = ob.detect_ob_v2(ox, hx, lx, cx, zbx, zrx)
near = [x for x in trx if 1.00 <= x['entry_price'] <= 1.06 or (0.98 <= x['block_low'] <= 1.06)]
ts = dfx['timestamp'].values
print(f"[XRP] {len(trx)} trades total; {len(near)} con bloque/entrada en ~1.00-1.06 (Ricardo marco ~1.0485/1.0038):")
for x in near[:8]:
    print(f"   {'L' if x['side']>0 else 'S'} {str(ts[x['gat_bar']])[:10]} block[{x['block_low']:.4f}-{x['block_high']:.4f}] entry={x['entry_price']:.4f} exit={x['exit_price']:.4f} {rc[x['reason']]} pnl={x['pnl']:.2f}%")
print("\n[SMOKE v2 DONE]")
