"""
Tests M2 fix: re-orden selección specialists por pf_fwd_ci_low directo
(rama feature-m2-fix-pffwd-cilow-ranking, 2026-04-24).

Contexto: §13.2 bloque REFINAMIENTO canónico 2026-04-24 identifica
Mecanismo 2 (pf_combined como media ponderada train/fwd diluye fwd).
Fix: sort post-bootstrap por pf_fwd_ci_low primero, tie-breaker
specialist_score_ci_low (preserva W3b secundario).

Tests:
  1. Inversión ranking: config A (pf_tr alto, pf_fwd_ci_low bajo) vs
     config B (pf_tr moderado, pf_fwd_ci_low alto). Pre-M2-fix sort
     por specialist_score_ci_low → A gana (embebe pf_tr via
     pf_combined). Post-M2-fix sort por pf_fwd_ci_low → B gana.
  2. Tie-breaker funcional: dos configs con mismo pf_fwd_ci_low →
     specialist_score_ci_low desempata.
  3. Estabilidad N preservada: sort no pierde configs.

Standalone, no pytest. Run: python tests/test_m2_fix_pffwd_ranking.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import numpy as np
import pandas as pd
from regime_walk_forward import _apply_bootstrap_pf_fwd


def test_1_inversion_ranking_train_vs_fwd():
    """
    Config A (train-dominant): pf_tr alto con N_tr grande, pf_fwd apenas
    supera threshold 1.1 con N_fwd moderado → pf_combined alto por
    peso train → specialist_score_ci_low alto.
    Config B (fwd-robusto): pf_tr moderado con N_tr grande, pf_fwd
    claramente alto con N_fwd grande → pf_combined intermedio (peso
    train lo baja) → specialist_score_ci_low más bajo que A aunque
    pf_fwd_ci_low de B sea mayor.

    M2 fix debe rankear B sobre A (el test no visto es lo que importa).
    """
    df = pd.DataFrame({
        # Config A: pf_tr=3.0 (N_tr grande), pf_fwd apenas 1.2 (borderline)
        # Config B: pf_tr=1.3 (moderado), pf_fwd=2.8 (robusto)
        'trades_fwd': [80, 100],
        'wins_fwd':   [42, 60],
        'gp_fwd':     [30.0, 50.0],
        'gl_fwd':     [25.0, 17.857],  # A: GP/GL=1.2, B: GP/GL=2.8
        'gp_tr':      [180.0, 90.0],
        'gl_tr':      [60.0, 69.231],  # A: GP/GL=3.0, B: GP/GL=1.3
        'pf_combined': [(180 + 30) / (60 + 25),       # A ≈ 2.47
                        (90 + 50) / (69.231 + 17.857)], # B ≈ 1.61
        'pf_robustness': [1.5, 1.5],
        'trades_total': [240, 280],
        'sqn_p5': [2.0, 2.0],
    })
    _apply_bootstrap_pf_fwd(df)

    # Invariante setup: A tiene pf_combined mayor (peso train)
    pf_comb_A = float(df['pf_combined'].iloc[0])
    pf_comb_B = float(df['pf_combined'].iloc[1])
    assert pf_comb_A > pf_comb_B, \
        f"Setup invariant: A pf_combined ({pf_comb_A:.3f}) debe > B ({pf_comb_B:.3f})"

    # Invariante setup: B tiene pf_fwd_ci_low mayor (test no visto mejor)
    ci_low_A = float(df['pf_fwd_ci_low'].iloc[0])
    ci_low_B = float(df['pf_fwd_ci_low'].iloc[1])
    assert ci_low_B > ci_low_A, \
        f"Setup invariant: B pf_fwd_ci_low ({ci_low_B:.3f}) debe > A ({ci_low_A:.3f})"

    # W3b (pre-M2-fix): sort por specialist_score_ci_low
    df_w3b = df.sort_values('specialist_score_ci_low', ascending=False).reset_index(drop=True)
    winner_w3b = int(df_w3b['trades_fwd'].iloc[0])  # A=80, B=100

    # M2 fix: sort por pf_fwd_ci_low primero, tie-breaker score_ci_low
    df_m2 = df.sort_values(
        ['pf_fwd_ci_low', 'specialist_score_ci_low'],
        ascending=[False, False]).reset_index(drop=True)
    winner_m2 = int(df_m2['trades_fwd'].iloc[0])

    # Assertion crítica: M2 fix invierte ranking hacia B
    assert winner_m2 == 100, \
        f"M2 fix debería rankear B (trades_fwd=100) primero, got trades_fwd={winner_m2}"

    # Log diagnostic
    print(f"  Config A: pf_tr=3.00 pf_fwd=1.20 pf_comb={pf_comb_A:.3f}"
          f" ci_low={ci_low_A:.3f} score_ci_low={float(df['specialist_score_ci_low'].iloc[0]):.3f}")
    print(f"  Config B: pf_tr=1.30 pf_fwd=2.80 pf_comb={pf_comb_B:.3f}"
          f" ci_low={ci_low_B:.3f} score_ci_low={float(df['specialist_score_ci_low'].iloc[1]):.3f}")
    print(f"  W3b winner (pre-fix): trades_fwd={winner_w3b}")
    print(f"  M2 fix winner:        trades_fwd={winner_m2} (B, fwd-robusto)")
    print(f"  test_1 PASS: M2 fix invierte ranking hacia config B (pf_fwd_ci_low mayor)")


def test_2_tiebreaker_functional():
    """
    Dos configs con pf_fwd_ci_low idénticos → specialist_score_ci_low
    desempata. Verifica que tie-breaker funciona.
    """
    # Construyo dos configs con bootstrap determinista mismo seed →
    # mismo pf_fwd_ci_low aprox; difieren en pf_tr que afecta
    # specialist_score_ci_low via pf_combined_ci_low.
    df = pd.DataFrame({
        'trades_fwd': [100, 100],
        'wins_fwd':   [55, 55],
        'gp_fwd':     [40.0, 40.0],
        'gl_fwd':     [20.0, 20.0],  # Ambos: pf_fwd=2.0, ci_low similar
        'gp_tr':      [150.0, 50.0],  # A alto train, B bajo train
        'gl_tr':      [50.0, 40.0],   # A: pf_tr=3.0, B: pf_tr=1.25
        'pf_combined': [(150 + 40) / (50 + 20),   # A=2.71
                        (50 + 40) / (40 + 20)],    # B=1.5
        'pf_robustness': [1.5, 1.5],
        'trades_total': [300, 200],
        'sqn_p5': [2.0, 2.0],
    })
    _apply_bootstrap_pf_fwd(df)

    ci_low_A = float(df['pf_fwd_ci_low'].iloc[0])
    ci_low_B = float(df['pf_fwd_ci_low'].iloc[1])
    # Deben ser idénticos porque gp_fwd/gl_fwd/wins_fwd/trades_fwd idénticos + seed 42
    assert abs(ci_low_A - ci_low_B) < 1e-6, \
        f"Setup requiere pf_fwd_ci_low idénticos para tiebreaker test: A={ci_low_A:.6f}, B={ci_low_B:.6f}"

    score_cilow_A = float(df['specialist_score_ci_low'].iloc[0])
    score_cilow_B = float(df['specialist_score_ci_low'].iloc[1])
    # A tiene pf_combined_ci_low mayor (por pf_tr alto) → score_ci_low mayor
    assert score_cilow_A > score_cilow_B, \
        f"Setup: A score_ci_low ({score_cilow_A:.3f}) > B ({score_cilow_B:.3f})"

    # M2 fix con tie-breaker: A gana por score_ci_low desempate
    df_m2 = df.sort_values(
        ['pf_fwd_ci_low', 'specialist_score_ci_low'],
        ascending=[False, False]).reset_index(drop=True)
    winner_gp_tr = float(df_m2['gp_tr'].iloc[0])

    assert abs(winner_gp_tr - 150.0) < 1e-3, \
        f"Tie-breaker debería favorecer A (gp_tr=150), got {winner_gp_tr}"

    print(f"  Config A: ci_low={ci_low_A:.3f} score_ci_low={score_cilow_A:.3f}")
    print(f"  Config B: ci_low={ci_low_B:.3f} score_ci_low={score_cilow_B:.3f}")
    print(f"  test_2 PASS: tie-breaker desempata por specialist_score_ci_low (A gana)")


def test_3_n_preservado():
    """Sort no pierde filas. N in == N out."""
    df = pd.DataFrame({
        'trades_fwd': [50, 60, 70, 80, 90],
        'wins_fwd':   [30, 32, 40, 44, 50],
        'gp_fwd':     [30.0, 25.0, 40.0, 35.0, 50.0],
        'gl_fwd':     [15.0, 12.0, 20.0, 17.0, 25.0],
        'gp_tr':      [90.0, 80.0, 110.0, 100.0, 140.0],
        'gl_tr':      [40.0, 35.0, 50.0, 45.0, 65.0],
        'pf_combined': [(90+30)/(40+15), (80+25)/(35+12),
                        (110+40)/(50+20), (100+35)/(45+17),
                        (140+50)/(65+25)],
        'pf_robustness': [1.5] * 5,
        'trades_total': [140, 150, 180, 190, 240],
        'sqn_p5': [2.0] * 5,
    })
    n_before = len(df)
    _apply_bootstrap_pf_fwd(df)
    df_sorted = df.sort_values(
        ['pf_fwd_ci_low', 'specialist_score_ci_low'],
        ascending=[False, False]).reset_index(drop=True)
    n_after = len(df_sorted)
    assert n_before == n_after, f"Sort perdió filas: {n_before} -> {n_after}"
    # Verifica orden descendente pf_fwd_ci_low
    ci_lows = df_sorted['pf_fwd_ci_low'].values
    for i in range(1, len(ci_lows)):
        assert ci_lows[i] <= ci_lows[i-1] + 1e-6, \
            f"Orden roto en idx {i}: {ci_lows[i-1]:.3f} < {ci_lows[i]:.3f}"
    print(f"  test_3 PASS: N preservado ({n_after}), orden descendente OK")


def _run_all():
    print("=" * 68)
    print("M2 fix ranking pf_fwd_ci_low directo — test suite")
    print("=" * 68)
    tests = [
        test_1_inversion_ranking_train_vs_fwd,
        test_2_tiebreaker_functional,
        test_3_n_preservado,
    ]
    n_pass = 0
    n_fail = 0
    for t in tests:
        try:
            t()
            n_pass += 1
        except AssertionError as e:
            print(f"  {t.__name__} FAIL: {e}")
            n_fail += 1
        except Exception as e:
            print(f"  {t.__name__} ERROR: {type(e).__name__}: {e}")
            n_fail += 1
    print("=" * 68)
    print(f"Result: {n_pass}/{len(tests)} PASS, {n_fail} FAIL")
    print("=" * 68)
    return n_fail == 0


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)
