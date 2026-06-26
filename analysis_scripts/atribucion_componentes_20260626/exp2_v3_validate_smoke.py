# -*- coding: utf-8 -*-
"""
Exp#2 v3 — RE-VALIDACIÓN (XRP: ¿detecta bloque 17-nov + opera LARGO?) + SMOKE (no-look-ahead + 1 celda).
Dirección = gatillo MR (fast<slow=bull=largo). NO barrido 45.
"""
import sys, os, time
import numpy as np, pandas as pd
ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT); os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626"))
import regime_walk_forward as rwf
import mean_reversion_features as mrf
import ob_detector_v3 as ob

def zones(df, sym):
    cp = 'data_cache/' + sym.replace('/', '') + '_mean_reversion.npz'
    if os.path.exists(cp): os.remove(cp)
    d = mrf.precalculate_mean_reversion(sym, df)
    if os.path.exists(cp): os.remove(cp)
    return d['zone_bull_forming'], d['zone_bear_forming']

def arrs(df):
    return [df[x].values.astype(float) for x in ['open', 'high', 'low', 'close']]

# ===== RE-VALIDACIÓN XRP (ejemplo de Ricardo) =====
print("===== RE-VALIDACIÓN XRP (gatillo ~2026-06-25 -> ¿bloque 2024-11-17 + LARGO?) =====")
dfx = pd.read_parquet('data_cache/XRPUSDT_1h_ext.parquet').reset_index(drop=True)
dfx['timestamp'] = pd.to_datetime(dfx['timestamp_ms'], unit='ms'); dfx['ts'] = dfx['timestamp']
ox, hx, lx, cx = arrs(dfx)
zbx, zrx = zones(dfx, 'XRP/USDT')
t0 = time.time(); trx = ob.detect_ob_v3(ox, hx, lx, cx, zbx, zrx); dt = time.time() - t0
print(f"[XRP] {len(trx)} trades en {dt:.1f}s")
ts = dfx['ts'].values
recent = [x for x in trx if dfx['ts'].iloc[x['gat_bar']] >= pd.Timestamp('2026-06-01')]
print(f"trades con gatillo desde 2026-06-01: {len(recent)}")
for x in recent[:10]:
    bdate = str(dfx['ts'].iloc[x['block_bar']])[:13]
    flag = ' <== BLOQUE 2024-11-17 RICARDO' if pd.Timestamp('2024-11-16') <= dfx['ts'].iloc[x['block_bar']] <= pd.Timestamp('2024-11-18') else ''
    print(f"   gat {str(dfx['ts'].iloc[x['gat_bar']])[:13]} {'LARGO' if x['side']>0 else 'CORTO'} block@{bdate}[{x['block_low']:.4f}-{x['block_high']:.4f}] entry={x['entry_price']:.4f} {['tp','stop','time'][x['reason']]} pnl={x['pnl']:.2f}%{flag}")

# ===== SMOKE BTC: no-look-ahead + 1 celda =====
print("\n===== SMOKE BTC =====")
df = rwf.load_full_history("BTC/USDT")
o, h, l, c = arrs(df); zb, zr = zones(df, "BTC/USDT"); n = len(c)
t0 = time.time(); trades = ob.detect_ob_v3(o, h, l, c, zb, zr); dt = time.time() - t0
pnls = np.array([x['pnl'] for x in trades])
pf, gp, gl = ob.pf_from_pnls(pnls)
nb = sum(1 for x in trades if x['side'] > 0)
print(f"[DET] {len(trades)} trades ({nb}L/{len(trades)-nb}S) en {dt:.1f}s | win={100*(pnls>0).mean():.1f}% | PF(all)={pf:.3f}")

print("\n[B] NO-LOOK-AHEAD (prefix-invariance)")
T = n - 4000
dft = df.iloc[:T].copy()
ot, ht, lt, ct = arrs(dft); zbt, zrt = zones(dft, "BTC/USDT")
trt = ob.detect_ob_v3(ot, ht, lt, ct, zbt, zrt)
def key(x): return (x['gat_bar'], x['block_bar'], x['side'], x['entry_bar'], x['exit_bar'], round(x['entry_price'], 6), round(x['exit_price'], 6), x['reason'])
A = {key(x) for x in trades if x['exit_bar'] < T - 1}; B = {key(x) for x in trt if x['exit_bar'] < T - 1}
print(f"[NLA] full={len(A)} trunc={len(B)} IDENTICOS={A==B} | GATE {'PASS' if A==B else 'FAIL'}")
if A != B: print(f"  solo_full={list(A-B)[:2]} solo_trunc={list(B-A)[:2]}")

print("\n[C] 1 CELDA as-of BTC")
model = rwf.load_regime_model("BTC/USDT")
cl, ncl = rwf.compute_cluster_labels(df, model)
eps = rwf.identify_episodes(cl, ncl, min_bars=rwf.MIN_EPISODE_BARS)
reg, ndob, split = rwf.build_regime_labels(cl, eps, ncl, train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
valid = [k for k in range(ncl) if split[k]['valid']]
fwd = [x['pnl'] for x in trades if 0 <= x['entry_bar'] < len(reg) and reg[x['entry_bar']] >= ncl and (reg[x['entry_bar']]-ncl) in valid]
pf_f, gpf, glf = ob.pf_from_pnls(fwd); wf = int((np.array(fwd) > 0).sum()) if fwd else 0
b = rwf._bootstrap_pf_fwd_vectorized(np.array([len(fwd)]), np.array([wf]), np.array([gpf]), np.array([glf]))
print(f"[CELL] pf_fwd={pf_f:.3f} CI=[{b['pf_fwd_ci_low'][0]:.3f},{b['pf_fwd_ci_high'][0]:.3f}] (n_fwd={len(fwd)})")
print("\n[v3 VALIDATE+SMOKE DONE]")
