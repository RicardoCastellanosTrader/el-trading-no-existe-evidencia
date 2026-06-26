# -*- coding: utf-8 -*-
"""
Atribucion por Componentes — Experimento #2 — DETECTOR DE ORDER BLOCK (look-ahead-free).
Construido segun PREREGISTRO_EXP2_ORDERBLOCK.md (params LOGICOS CONGELADOS).
Kernel NUEVO, separado — NO reusa el kernel de MA-cross, NO muta nada productivo.

Unidad = POR-SETUP INDEPENDIENTE: cada OB activado -> un trade candidato (llena o expira).
Look-ahead: el bloque se marca en la barra de ruptura t con datos <= t; entrada/stop/TP en barras > t.
"""
import numpy as np

# Params LOGICOS PRIMARIOS congelados (ver .md)
K_PRIMARY = 2.0
W_PRIMARY = 50
R_PRIMARY = 2.0
L_BLOCK = 10
H_MAX = 200
P_SWEEP = 20
COMMISSION = 0.10  # round-trip %


def detect_order_block_trades(open_, high, low, close, atr,
                              k=K_PRIMARY, W=W_PRIMARY, R_mult=R_PRIMARY,
                              L_block=L_BLOCK, H_max=H_MAX, commission=COMMISSION,
                              sweep=False, P_sweep=P_SWEEP):
    """Devuelve lista de trades (dict) detectados causalmente. Cada OB = trade independiente.
    trade = {act_bar, block_bar, side(+1/-1), entry_bar, exit_bar, entry_price, exit_price,
             pnl, reason(0=tp,1=stop,2=time)}.
    """
    n = len(close)
    trades = []
    for t in range(L_block + 1, n):
        atr_prev = atr[t - 1]
        if not np.isfinite(atr_prev) or atr_prev <= 0:
            continue
        rng = high[t] - low[t]
        if rng <= k * atr_prev:
            continue  # no es escapada decisiva

        # ---------- OB ALCISTA: vela t alcista, cierra sobre el high del ultimo bloque bajista ----------
        if close[t] > open_[t]:
            b = -1
            for j in range(t - 1, max(t - 1 - L_block, -1), -1):
                if close[j] < open_[j]:  # bajista
                    b = j
                    break
            if b >= 0 and close[t] > high[b]:
                ok = True
                if sweep:  # variante barrido: el bloque barrio el minimo de las ultimas P barras
                    lo0 = max(b - P_sweep, 0)
                    ok = (low[b] <= np.min(low[lo0:b + 1]))
                if ok:
                    tr = _simulate(t, b, +1, open_, high, low, close, W, H_max, R_mult, commission, n)
                    if tr is not None:
                        trades.append(tr)

        # ---------- OB BAJISTA: vela t bajista, cierra bajo el low del ultimo bloque alcista ----------
        if close[t] < open_[t]:
            b = -1
            for j in range(t - 1, max(t - 1 - L_block, -1), -1):
                if close[j] > open_[j]:  # alcista
                    b = j
                    break
            if b >= 0 and close[t] < low[b]:
                ok = True
                if sweep:
                    hi0 = max(b - P_sweep, 0)
                    ok = (high[b] >= np.max(high[hi0:b + 1]))
                if ok:
                    tr = _simulate(t, b, -1, open_, high, low, close, W, H_max, R_mult, commission, n)
                    if tr is not None:
                        trades.append(tr)
    return trades


def _simulate(t, b, side, open_, high, low, close, W, H_max, R_mult, commission, n):
    """Fill (limite pasivo en borde proximal en [t+1,t+W]) + gestion (TP intrabar / stop close / time)."""
    if side == +1:
        entry_price = high[b]          # borde proximal (top del bloque); precio vuelve desde arriba
        stop_ref = low[b]              # invalidacion = cierre por debajo
        risk = entry_price - stop_ref
        if risk <= 0:
            return None
        tp = entry_price + R_mult * risk
        # fill: primer s con low[s] <= entry_price
        entry_bar = -1
        for s in range(t + 1, min(t + W + 1, n)):
            if low[s] <= entry_price:
                entry_bar = s
                break
        if entry_bar < 0:
            return None
        for u in range(entry_bar, min(entry_bar + H_max + 1, n)):
            if high[u] >= tp:
                return _mk(t, b, side, entry_bar, u, entry_price, tp, commission, 0)
            if close[u] < stop_ref:
                return _mk(t, b, side, entry_bar, u, entry_price, close[u], commission, 1)
        u = min(entry_bar + H_max, n - 1)
        return _mk(t, b, side, entry_bar, u, entry_price, close[u], commission, 2)
    else:
        entry_price = low[b]           # borde proximal (bottom); precio vuelve desde abajo
        stop_ref = high[b]
        risk = stop_ref - entry_price
        if risk <= 0:
            return None
        tp = entry_price - R_mult * risk
        entry_bar = -1
        for s in range(t + 1, min(t + W + 1, n)):
            if high[s] >= entry_price:
                entry_bar = s
                break
        if entry_bar < 0:
            return None
        for u in range(entry_bar, min(entry_bar + H_max + 1, n)):
            if low[u] <= tp:
                return _mk(t, b, side, entry_bar, u, entry_price, tp, commission, 0)
            if close[u] > stop_ref:
                return _mk(t, b, side, entry_bar, u, entry_price, close[u], commission, 1)
        u = min(entry_bar + H_max, n - 1)
        return _mk(t, b, side, entry_bar, u, entry_price, close[u], commission, 2)


def _mk(act_bar, block_bar, side, entry_bar, exit_bar, entry_price, exit_price, commission, reason):
    if side == +1:
        pnl = (exit_price - entry_price) / entry_price * 100.0 - commission
    else:
        pnl = (entry_price - exit_price) / entry_price * 100.0 - commission
    return dict(act_bar=int(act_bar), block_bar=int(block_bar), side=int(side),
                entry_bar=int(entry_bar), exit_bar=int(exit_bar),
                entry_price=float(entry_price), exit_price=float(exit_price),
                pnl=float(pnl), reason=int(reason))


def pf_from_pnls(pnls):
    pnls = np.asarray(pnls, dtype=float)
    gp = pnls[pnls > 0].sum()
    gl = -pnls[pnls < 0].sum()
    if gl > 0:
        return gp / gl, gp, gl
    return (5.0 if gp > 0 else 0.0), gp, gl
