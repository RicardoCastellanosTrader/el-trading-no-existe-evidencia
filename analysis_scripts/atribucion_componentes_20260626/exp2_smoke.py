# -*- coding: utf-8 -*-
"""
Exp#2 ORDER BLOCK — SMOKE: (A) deteccion sensata + (B) test NO-LOOK-AHEAD (prefix-invariance)
+ (C) 1 celda as-of (BTC) pf_fwd global + CI + per-cluster. NO barrido 45 (requiere T3.1-Exp2).
"""
import sys, os, time
import numpy as np

ROOT = r"c:\Users\rixip\combolab"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "analysis_scripts", "atribucion_componentes_20260626"))
import regime_walk_forward as rwf
import lab_historico_numba_v8_3 as lab
import ob_detector as ob

SYM = "BTC/USDT"
df = rwf.load_full_history(SYM)
o = df['open'].values.astype(float); h = df['high'].values.astype(float)
l = df['low'].values.astype(float); c = df['close'].values.astype(float)
atr = lab.calc_atr(h, l, c, lab.HYST_ATR_LEN)
n = len(c)
print(f"[DATA] {SYM} {n} barras")

# ================= (A) DETECCION SENSATA =================
print("\n===== (A) DETECCION (params primarios k=2.0 W=50 R=2.0) =====")
t0 = time.time()
trades = ob.detect_order_block_trades(o, h, l, c, atr)
dt = time.time() - t0
nb = sum(1 for x in trades if x['side'] == +1); ns = len(trades) - nb
pnls = np.array([x['pnl'] for x in trades])
wins = int((pnls > 0).sum())
reasons = {0: 'tp', 1: 'stop', 2: 'time'}
rc = {reasons[r]: sum(1 for x in trades if x['reason'] == r) for r in (0, 1, 2)}
pf, gp, gl = ob.pf_from_pnls(pnls)
print(f"[DET] {len(trades)} OB trades llenados ({nb} long / {ns} short) en {dt:.2f}s")
print(f"[DET] win-rate={100*wins/max(len(trades),1):.1f}% | salidas: {rc} | PF(all)={pf:.3f} | pnl_medio={pnls.mean():.3f}%")
print(f"[SANITY] esperado: TP a 2R menos frecuente que stop+time; win-rate < 50% plausible con R=2")

# muestra de 3 bloques
for x in trades[:3]:
    print(f"   OB {'L' if x['side']>0 else 'S'} block@{x['block_bar']} act@{x['act_bar']} entry@{x['entry_bar']}({x['entry_price']:.2f}) exit@{x['exit_bar']}({x['exit_price']:.2f}) {reasons[x['reason']]} pnl={x['pnl']:.2f}%")

# ================= (B) NO-LOOK-AHEAD (prefix-invariance) =================
print("\n===== (B) TEST NO-LOOK-AHEAD (prefix-invariance) =====")
T = n - 4000
trades_trunc = ob.detect_order_block_trades(o[:T], h[:T], l[:T], c[:T], atr[:T])
def key(x):
    return (x['act_bar'], x['block_bar'], x['side'], x['entry_bar'], x['exit_bar'],
            round(x['entry_price'], 8), round(x['exit_price'], 8), x['reason'])
full_resolved = {key(x) for x in trades if x['exit_bar'] < T - 1}
trunc_resolved = {key(x) for x in trades_trunc if x['exit_bar'] < T - 1}
identical = full_resolved == trunc_resolved
print(f"[NLA] trades resueltos antes de T={T}: full={len(full_resolved)} trunc={len(trunc_resolved)}")
print(f"[NLA] conjuntos IDENTICOS: {identical}")
if not identical:
    only_full = list(full_resolved - trunc_resolved)[:3]
    only_trunc = list(trunc_resolved - full_resolved)[:3]
    print(f"[NLA][FAIL] solo_full={only_full} | solo_trunc={only_trunc}")
print(f"[GATE B] NO-LOOK-AHEAD {'PASS' if identical else 'FAIL'} -> deteccion {'causal' if identical else 'CON LEAKAGE — PARAR (T3.2)'}")

# ================= (C) 1 CELDA AS-OF (BTC) =================
print("\n===== (C) 1 CELDA as-of (BTC) — pf_fwd GLOBAL + CI + per-cluster =====")
model = rwf.load_regime_model(SYM)
cl_labels, ncl = rwf.compute_cluster_labels(df, model)
episodes = rwf.identify_episodes(cl_labels, ncl, min_bars=rwf.MIN_EPISODE_BARS)
reg, ndob, split = rwf.build_regime_labels(cl_labels, episodes, ncl,
                                           train_ratio=rwf.TRAIN_RATIO, toxic_tail=rwf.TOXIC_TAIL)
valid = [k for k in range(ncl) if split[k]['valid']]
fwd_pnls = []; tr_pnls = []; per = {k: [] for k in valid}
for x in trades:
    eb = x['entry_bar']
    lab_e = reg[eb]
    if lab_e < 0:
        continue
    if lab_e >= ncl:
        kk = lab_e - ncl
        if kk in per:
            fwd_pnls.append(x['pnl']); per[kk].append(x['pnl'])
    else:
        tr_pnls.append(x['pnl'])
pf_f, gpf, glf = ob.pf_from_pnls(fwd_pnls)
pf_t, _, _ = ob.pf_from_pnls(tr_pnls)
trf = len(fwd_pnls); wf = int((np.array(fwd_pnls) > 0).sum()) if fwd_pnls else 0
b = rwf._bootstrap_pf_fwd_vectorized(np.array([trf]), np.array([wf]), np.array([gpf]), np.array([glf]))
cil, cih = float(b['pf_fwd_ci_low'][0]), float(b['pf_fwd_ci_high'][0])
print(f"[CELL] pf_tr={pf_t:.3f} (n={len(tr_pnls)}) | pf_fwd GLOBAL={pf_f:.3f} CI=[{cil:.3f},{cih:.3f}] (n_fwd={trf}, wins={wf})")
print(f"[CRIT] CI excluye 1.0? {'SI' if cil>1.0 else 'NO'} | benchmark breakeven=1.0")
print("[per-cluster fwd (diagnostico)]:")
for k in valid:
    pk, _, _ = ob.pf_from_pnls(per[k])
    print(f"   C{k}: pf_fwd={pk:.3f} (n={len(per[k])})")
print("\n[SMOKE EXP2 DONE]")
