# -*- coding: utf-8 -*-
"""
Exp#2 v3 FINAL — DETECTOR ORDER BLOCK, criterio real de Ricardo (alcance MÍNIMO FIEL).
- Gatillo EN-ZONA: mientras z_bull/z_bear (forming) estando flat; dirección por zona MR
  (fast<slow=bull=largo). Replica mean_reversion_kernel:542-583.
- BLOQUE = nivel de reacción/swing pivot (±P), FRESCO (extremo no mitigado) + REENCUENTRO
  (≥out_thresh fuera de la banda ±5%), con el NIVEL (low en alcista) dentro del 5% del precio
  (permite precio DENTRO del rango del bloque). Retroceso s/tope (cap).
- ENTRADA (corregido) = orden límite en el BORDE LEJANO (donde barre la mecha de liquidación):
  alcista -> hacia el LOW; ENTRY_FRAC=0.75 del camino hacia el extremo. NO el borde proximal.
  Fill cuando la mecha barre hasta el nivel (limit pasiva, espera el barrido).
- Salidas (prioridad kernel): STOP (cierre fuera del bloque = más allá del borde lejano) >
  TP/zone-exit (zona opuesta = nuevo cruce) > cancel_zona (anti-repintado forming/resolved).
- SIN cancel_tf/cancel_ghost/ángulo (refinamientos). Look-ahead-free bar-a-bar; gate prefix-invariance.
"""
import numpy as np
import pandas as pd

NEAR_PCT = 0.05
P_PIVOT = 10
OUT_THRESH = 0.90
SCAN_CAP = 25000
ENTRY_FRAC = 0.75      # fracción del camino hacia el borde LEJANO (donde barre la mecha)
COMMISSION = 0.10
COOLDOWN = 1


def _swings(arr, P, kind):
    s = pd.Series(arr)
    if kind == 'low':
        return arr == s.rolling(2 * P + 1, center=True, min_periods=2 * P + 1).min().values
    return arr == s.rolling(2 * P + 1, center=True, min_periods=2 * P + 1).max().values


def _find_block(t, side, l, h, c, is_low, is_high, near_pct, out_thresh, scan_cap):
    ct = c[t]
    # SELECCIÓN: entre los bloques válidos por el lado correcto dentro del 5%, elegir el MÁS PROFUNDO
    # (= el pool mayor de liquidez hacia donde barre la mecha; principista por la tesis del barrido,
    #  NO el más cercano). Reproduce el bloque significativo de Ricardo (el origen profundo).
    best = -1
    if side == +1:                                  # soporte: swing LOW con su nivel dentro del 5% bajo el precio
        best_low = np.inf
        run = l[t]
        for j in range(t - P_PIVOT - 1, max(P_PIVOT, t - scan_cap) - 1, -1):
            if l[j] < run:
                run = l[j]
                if not is_low[j]:
                    continue
                L = l[j]
                if L > ct:                          # nivel por encima del precio: no es soporte abajo
                    continue
                if (ct - L) / ct > near_pct:
                    break                           # más atrás solo más profundo (fuera de banda)
                cl = c[j + 1:t]
                if len(cl) and np.mean((cl < L * 0.95) | (cl > L * 1.05)) >= out_thresh:
                    if L < best_low:
                        best_low = L; best = j      # el más profundo
        return best
    else:                                           # resistencia: swing HIGH dentro del 5% sobre el precio
        best_high = -np.inf
        run = h[t]
        for j in range(t - P_PIVOT - 1, max(P_PIVOT, t - scan_cap) - 1, -1):
            if h[j] > run:
                run = h[j]
                if not is_high[j]:
                    continue
                L = h[j]
                if L < ct:
                    continue
                if (L - ct) / ct > near_pct:
                    break
                cl = c[j + 1:t]
                if len(cl) and np.mean((cl < L * 0.95) | (cl > L * 1.05)) >= out_thresh:
                    if L > best_high:
                        best_high = L; best = j     # la más alta (más profunda en resistencia)
        return best


def detect_ob_v3(o, h, l, c, zbf, zbr, zsf, zsr, ts_ms,
                 near_pct=NEAR_PCT, out_thresh=OUT_THRESH, scan_cap=SCAN_CAP,
                 entry_frac=ENTRY_FRAC, commission=COMMISSION):
    n = len(c)
    is_low = _swings(l, P_PIVOT, 'low'); is_high = _swings(h, P_PIVOT, 'high')
    day = ts_ms // 86400000
    trades = []
    st = 0  # 0=flat-buscando, 1=limite-pendiente, 2=en-posición
    side = 0; blk_lo = 0.0; blk_hi = 0.0; entry_lvl = 0.0; entry_bar = -1; entry = 0.0
    cooldown_until = -1
    for t in range(P_PIVOT + 1, n):
        if st == 0:
            if t <= cooldown_until:
                continue
            s = +1 if zbf[t] else (-1 if zsf[t] else 0)
            if s == 0:
                continue
            j = _find_block(t, s, l, h, c, is_low, is_high, near_pct, out_thresh, scan_cap)
            if j < 0:
                continue
            side = s; blk_lo = l[j]; blk_hi = h[j]; rng = blk_hi - blk_lo
            # orden límite en el borde LEJANO (alcista->hacia low; bajista->hacia high), al entry_frac
            entry_lvl = blk_hi - entry_frac * rng if s == +1 else blk_lo + entry_frac * rng
            st = 1
        elif st == 1:
            cur = +1 if zbf[t] else (-1 if zsf[t] else 0)
            if cur != side:                          # la zona del gatillo terminó -> cancelar pendiente
                st = 0; continue
            if (side == +1 and l[t] <= entry_lvl) or (side == -1 and h[t] >= entry_lvl):
                entry = entry_lvl; entry_bar = t; st = 2   # fill (la mecha barrió hasta el nivel)
        else:  # st == 2 en-posición
            ed, cd = day[entry_bar], day[t]
            ex = False; ep = 0.0; reason = -1
            if side == +1 and c[t] < blk_lo:
                ex, ep, reason = True, c[t], 1          # STOP cierre fuera (más allá del borde lejano)
            elif side == -1 and c[t] > blk_hi:
                ex, ep, reason = True, c[t], 1
            if not ex:
                if side == +1 and zsf[t]:
                    ex, ep, reason = True, c[t], 0      # TP zona opuesta (nuevo cruce)
                elif side == -1 and zbf[t]:
                    ex, ep, reason = True, c[t], 0
            if not ex:                                  # cancel_zona anti-repintado
                if side == +1:
                    if (ed == cd and not zbf[t]) or (ed != cd and not zbr[entry_bar]):
                        ex, ep, reason = True, c[t], 3
                else:
                    if (ed == cd and not zsf[t]) or (ed != cd and not zsr[entry_bar]):
                        ex, ep, reason = True, c[t], 3
            if ex:
                pnl = ((ep - entry) if side == +1 else (entry - ep)) / entry * 100.0 - commission
                trades.append(dict(entry_bar=int(entry_bar), exit_bar=int(t), side=int(side),
                                   block_low=float(blk_lo), block_high=float(blk_hi),
                                   entry_price=float(entry), exit_price=float(ep),
                                   pnl=float(pnl), reason=int(reason)))
                st = 0; cooldown_until = t + COOLDOWN
    return trades


def pf_from_pnls(pnls):
    a = np.asarray(pnls, dtype=float)
    gp = a[a > 0].sum(); gl = -a[a < 0].sum()
    if gl > 0:
        return gp / gl, gp, gl
    return (5.0 if gp > 0 else 0.0), gp, gl
