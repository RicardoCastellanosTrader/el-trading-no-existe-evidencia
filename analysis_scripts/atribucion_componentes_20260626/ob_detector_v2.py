# -*- coding: utf-8 -*-
"""
Exp#2 v2 — DETECTOR ORDER BLOCK con el criterio REAL de Ricardo (validado Q1-Q4).
Difiere de v1 (ICT estrecho + 2R fijo + sin gatillo): GATILLO-ancla + bloque por
CHOQUE HISTORICO + cercania 5% + stop cierre-fuera + TP = NUEVO CRUCE. Look-ahead-free
(simulacion estrictamente BARRA-A-BARRA: el cruce cancela/cierra cuando OCURRE, no se
pre-computa la ventana — fix tras FAIL prefix-invariance v2.0).

GATILLO (reusa MR): cruce Tenkan-9/HA-diaria-forming. bull->LONG soporte debajo; bear->SHORT resist arriba.
BLOQUE: nivel anterior mas reciente FRESCO (no mitigado) dentro del 5%, que el precio reencuentra.
TP = siguiente cruce tras la entrada. STOP = cierre fuera del bloque.
[DOF flagged Ricardo via XRP]: la objetivacion de "choque relevante" (vela fresca dentro del 5%).
"""
import numpy as np

NEAR_PCT = 0.05
COMMISSION = 0.10


def detect_ob_v2(o, h, l, c, zone_bull, zone_bear, near_pct=NEAR_PCT, commission=COMMISSION):
    n = len(c)
    state = zone_bull.astype(np.int8) - zone_bear.astype(np.int8)  # +1/-1/0; cruce = cambio
    trades = []
    for t in range(1, n):
        bull_gat = zone_bull[t] and not zone_bull[t - 1]
        bear_gat = zone_bear[t] and not zone_bear[t - 1]
        if not (bull_gat or bear_gat):
            continue
        side = +1 if bull_gat else -1
        ct = c[t]

        # ---- BLOQUE por choque historico (fresco, dentro del 5%, borde proximal) ----
        blk = -1
        if side == +1:                       # soporte debajo
            run_min = l[t]
            for j in range(t - 1, -1, -1):
                if l[j] < run_min:
                    run_min = l[j]
                    if h[j] < ct:
                        if (ct - h[j]) / ct <= near_pct:
                            blk = j
                        break               # primer soporte fresco bajo el precio decide
            if blk < 0:
                continue
            entry = h[blk]; stopref = l[blk]
        else:                                # resistencia arriba
            run_max = h[t]
            for j in range(t - 1, -1, -1):
                if h[j] > run_max:
                    run_max = h[j]
                    if l[j] > ct:
                        if (l[j] - ct) / ct <= near_pct:
                            blk = j
                        break
            if blk < 0:
                continue
            entry = l[blk]; stopref = h[blk]

        # ---- FILL bar-a-bar: limite vivo hasta que un CRUCE lo cancele ----
        entry_bar = -1
        s = t + 1
        while s < n:
            if state[s] != state[s - 1]:      # cruce -> zona terminada, cancela si no lleno
                break
            if (side == +1 and l[s] <= entry) or (side == -1 and h[s] >= entry):
                entry_bar = s; break
            s += 1
        if entry_bar < 0:
            continue

        # ---- GESTION bar-a-bar: stop (cierre fuera) o TP (siguiente cruce tras entrada) ----
        exit_bar = -1; exit_price = 0.0; reason = 2
        u = entry_bar
        while u < n:
            if (side == +1 and c[u] < stopref) or (side == -1 and c[u] > stopref):
                exit_bar = u; exit_price = c[u]; reason = 1; break
            if u > entry_bar and state[u] != state[u - 1]:
                exit_bar = u; exit_price = c[u]; reason = 0; break
            u += 1
        if exit_bar < 0:
            exit_bar = n - 1; exit_price = c[n - 1]; reason = 2  # time-stop fin de datos

        pnl = ((exit_price - entry) if side == +1 else (entry - exit_price)) / entry * 100.0 - commission
        trades.append(dict(gat_bar=int(t), block_bar=int(blk), side=int(side),
                           entry_bar=int(entry_bar), exit_bar=int(exit_bar),
                           entry_price=float(entry), exit_price=float(exit_price),
                           block_low=float(l[blk]), block_high=float(h[blk]),
                           pnl=float(pnl), reason=int(reason)))
    return trades


def pf_from_pnls(pnls):
    a = np.asarray(pnls, dtype=float)
    gp = a[a > 0].sum(); gl = -a[a < 0].sum()
    if gl > 0:
        return gp / gl, gp, gl
    return (5.0 if gp > 0 else 0.0), gp, gl
