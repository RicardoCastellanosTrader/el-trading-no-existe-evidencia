"""Tests A34 — timing_borderline reclasificacion post-matching.

Verifica:
  - Match exacto / ±1 (dentro de ENTRY_CANDLE_TOLERANCE) preserva
    comportamiento pre-A34: esos pares matchean en match_vps_to_kernel
    directamente, no llegan a detect_timing_borderline_pairs.
  - Timing borderline ±2 (entry_tol < diff <= entry_tol + timing_tolerance):
    reclasifica VPS + kernel pair.
  - NONE real (fuera de ventana extendida): no reclasifica.
  - Precedencia hipotesis: micro_precio_BingX > timing_borderline > no_match_kernel.
  - --timing-tolerance 0: feature desactivada (sets vacios).
  - --timing-tolerance 2: extiende a ±3 horas totales (entry_tol=1 + 2).
  - Simetria kernel_no_vps tambien reclasifica.

Run: python tests/test_a34_timing_borderline.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audit_fidelity_v5 import (
    detect_timing_borderline_pairs,
    hypothesis_for_no_match,
    ENTRY_CANDLE_TOLERANCE,
    DEFAULT_TIMING_TOLERANCE,
)


BASE_TS = pd.Timestamp('2026-04-21 12:00', tz='UTC')


def _vps_nm(idx, sym, side, hour_offset):
    """Helper: construye fila no_match_vps con entry_candle = BASE_TS + h."""
    return {
        'idx': idx,
        'symbol': sym,
        'side': side,
        'entry_candle': BASE_TS + pd.Timedelta(hours=hour_offset),
        'exit_cycle': BASE_TS + pd.Timedelta(hours=hour_offset + 5),
        'reason': 'tf_exit',
        'entry_price': 100.0,
    }


def _kt(sym, side, hour_offset):
    """Helper: construye kernel trade con entry_ts = BASE_TS + h."""
    return {
        'symbol': sym,
        'side': side,
        'entry_ts': BASE_TS + pd.Timedelta(hours=hour_offset),
        'exit_ts': BASE_TS + pd.Timedelta(hours=hour_offset + 5),
        'entry_price': 100.0,
        'reason': 'tf_exit',
    }


def test_exact_match_not_in_borderline():
    """Match exacto (diff=0) no pasa por borderline (se maneja en matching).
    El detector solo ve trades NO matcheados."""
    # Simulamos que matching ya hizo su trabajo: no_match_vps y no_match_kernel
    # no contienen pares que matchearon. Aqui comprobamos que cuando diff=0,
    # NO se reclasifica como borderline (porque detector requiere diff > entry_tol).
    # Pasar el caso explicitamente para validar el guard inferior del intervalo.
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 0)]  # diff=0h, deberia haber matcheado upstream
    vps_b, ker_b, pairs = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    # diff=0 < entry_tol=1 → NO borderline (guard: entry_tol < diff_h)
    assert vps_b == set(), f"diff=0 no deberia ser borderline: {vps_b}"
    assert ker_b == set()
    print("OK exact match (diff=0) no reclasifica a borderline (guard inferior)")


def test_within_entry_tol_not_borderline():
    """Match ±1 (dentro de entry_tol=1) no borderline — pertenece a match normal."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 1)]  # diff=1h == entry_tol, NO borderline
    vps_b, ker_b, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == set(), f"diff=1 == entry_tol no deberia ser borderline: {vps_b}"
    print("OK diff=1 (igual a entry_tol) no reclasifica a borderline")


def test_timing_borderline_plus_two():
    """Diff=+2h con tolerance=1 -> entry_tol < 2 <= entry_tol+timing_tol=2 -> BORDERLINE."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 2)]
    vps_b, ker_b, pairs = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == {1}, f"diff=2 deberia ser borderline: {vps_b}"
    assert ker_b == {0}
    assert pairs[1] == (0, 2), f"pair details: {pairs}"
    print("OK diff=+2h con tolerance=1 -> borderline")


def test_timing_borderline_minus_two():
    """Diff=-2h (kernel anterior al VPS) tambien reclasifica."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', -2)]  # 2h antes
    vps_b, ker_b, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == {1}, f"diff=-2 deberia ser borderline (abs): {vps_b}"
    assert ker_b == {0}
    print("OK diff=-2h (negativo) -> borderline (abs)")


def test_true_none_outside_window():
    """Diff=+5h con tolerance=1 -> fuera de ventana -> NO borderline."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 5)]
    vps_b, ker_b, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == set(), f"diff=5 fuera ventana no deberia ser borderline: {vps_b}"
    assert ker_b == set()
    print("OK diff=+5h fuera de ventana -> NONE definitivo")


def test_tolerance_zero_disables():
    """--timing-tolerance 0 desactiva feature: retorna sets vacios incluso con pares cercanos."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 2)]  # Caso que con tolerance=1 seria borderline
    vps_b, ker_b, pairs = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=0)
    assert vps_b == set() and ker_b == set() and pairs == {}
    print("OK --timing-tolerance 0 desactiva feature")


def test_tolerance_custom_two():
    """--timing-tolerance 2 extiende a diff <= 3h total."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 3)]  # diff=3, entry_tol+timing=3 -> incluido
    vps_b, ker_b, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=2)
    assert vps_b == {1}, f"diff=3 con timing_tol=2 deberia ser borderline: {vps_b}"

    # diff=4 > 3 -> fuera
    vps2 = [_vps_nm(2, 'BTC/USDT', 'long', 0)]
    kernel2 = [_kt('BTC/USDT', 'long', 4)]
    vps_b2, _, _ = detect_timing_borderline_pairs(vps2, kernel2, entry_tol=1, timing_tolerance=2)
    assert vps_b2 == set(), f"diff=4 > 3 no deberia ser borderline: {vps_b2}"
    print("OK --timing-tolerance 2 matchea ±3h total, excluye ±4h")


def test_side_mismatch_not_borderline():
    """Diff=+2h pero side diferente (long vs short) -> NO borderline."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'short', 2)]
    vps_b, _, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == set(), f"side mismatch no deberia ser borderline: {vps_b}"
    print("OK side mismatch no reclasifica")


def test_symbol_mismatch_not_borderline():
    """Diff=+2h pero symbol diferente -> NO borderline."""
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('ETH/USDT', 'long', 2)]
    vps_b, _, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == set()
    print("OK symbol mismatch no reclasifica")


def test_greedy_no_double_counting():
    """Un kernel trade solo se asigna a UN VPS borderline (greedy closest)."""
    # 2 VPS, 1 kernel. Ambos VPS quieren el mismo kernel.
    # VPS#1 en T+0, VPS#2 en T+4. Kernel en T+2.
    # diff(VPS1, K) = 2. diff(VPS2, K) = 2. Con greedy, el primero gana.
    vps = [
        _vps_nm(1, 'BTC/USDT', 'long', 0),
        _vps_nm(2, 'BTC/USDT', 'long', 4),
    ]
    kernel = [_kt('BTC/USDT', 'long', 2)]
    vps_b, ker_b, _ = detect_timing_borderline_pairs(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert len(vps_b) == 1, f"Un kernel solo matches a 1 VPS: {vps_b}"
    assert ker_b == {0}
    print("OK no double-counting (greedy)")


def test_hypothesis_vps_no_kernel_borderline():
    """hypothesis_for_no_match con is_timing_borderline=True retorna 'timing_borderline'."""
    entry = {'symbol': 'BTC/USDT', 'exit_ts': BASE_TS + pd.Timedelta(hours=5)}
    # Sin is_timing_borderline -> no_match_kernel
    hyp_pre = hypothesis_for_no_match(entry, 'vps_no_kernel', {}, {})
    assert hyp_pre == 'no_match_kernel', f"pre-A34 deberia ser no_match_kernel: {hyp_pre}"
    # Con is_timing_borderline=True -> timing_borderline
    hyp_post = hypothesis_for_no_match(entry, 'vps_no_kernel', {}, {}, is_timing_borderline=True)
    assert hyp_post == 'timing_borderline', f"con flag deberia ser timing_borderline: {hyp_post}"
    print("OK hypothesis flag VPS no_kernel -> timing_borderline")


def test_hypothesis_kernel_no_vps_borderline():
    """Simetria: kernel_no_vps + is_timing_borderline -> timing_borderline."""
    entry = {'symbol': 'BTC/USDT', 'exit_ts': BASE_TS + pd.Timedelta(hours=5)}
    hyp_pre = hypothesis_for_no_match(entry, 'kernel_no_vps', {}, {})
    assert hyp_pre == 'no_match_bot'
    hyp_post = hypothesis_for_no_match(entry, 'kernel_no_vps', {}, {}, is_timing_borderline=True)
    assert hyp_post == 'timing_borderline'
    print("OK hypothesis flag kernel_no_vps -> timing_borderline")


def test_diff_reason_not_affected():
    """is_timing_borderline no afecta kind='diff_reason' (reason distinta)."""
    entry = {'symbol': 'BTC/USDT'}
    hyp = hypothesis_for_no_match(entry, 'diff_reason', {}, {}, is_timing_borderline=True)
    assert hyp == 'razon_salida_distinta', f"diff_reason debe ganar: {hyp}"
    print("OK diff_reason no afectado por timing_borderline flag")


def test_default_timing_tolerance_value():
    """DEFAULT_TIMING_TOLERANCE = 1 (spec del usuario)."""
    assert DEFAULT_TIMING_TOLERANCE == 1
    assert ENTRY_CANDLE_TOLERANCE == 1
    print(f"OK DEFAULT_TIMING_TOLERANCE={DEFAULT_TIMING_TOLERANCE}, "
          f"ENTRY_CANDLE_TOLERANCE={ENTRY_CANDLE_TOLERANCE}")


def test_v52_consistency():
    """Audit v5.2 expone mismas constantes + helpers que v5.1."""
    from audit_fidelity_v5_2 import (
        detect_timing_borderline_pairs as detect_v52,
        hypothesis_for_no_match as hyp_v52,
        DEFAULT_TIMING_TOLERANCE as DEF_TOL_V52,
        ENTRY_CANDLE_TOLERANCE as ENTRY_TOL_V52,
    )
    assert DEF_TOL_V52 == DEFAULT_TIMING_TOLERANCE
    assert ENTRY_TOL_V52 == ENTRY_CANDLE_TOLERANCE

    # Mismo caso que test_timing_borderline_plus_two pero con v5.2
    vps = [_vps_nm(1, 'BTC/USDT', 'long', 0)]
    kernel = [_kt('BTC/USDT', 'long', 2)]
    vps_b, ker_b, pairs = detect_v52(vps, kernel, entry_tol=1, timing_tolerance=1)
    assert vps_b == {1} and ker_b == {0}

    hyp = hyp_v52({'symbol': 'BTC/USDT'}, 'vps_no_kernel', {}, {}, is_timing_borderline=True)
    assert hyp == 'timing_borderline'
    print("OK v5.2 expone mismos helpers (consistencia cross-modulo)")


if __name__ == "__main__":
    tests = [
        test_exact_match_not_in_borderline,
        test_within_entry_tol_not_borderline,
        test_timing_borderline_plus_two,
        test_timing_borderline_minus_two,
        test_true_none_outside_window,
        test_tolerance_zero_disables,
        test_tolerance_custom_two,
        test_side_mismatch_not_borderline,
        test_symbol_mismatch_not_borderline,
        test_greedy_no_double_counting,
        test_hypothesis_vps_no_kernel_borderline,
        test_hypothesis_kernel_no_vps_borderline,
        test_diff_reason_not_affected,
        test_default_timing_tolerance_value,
        test_v52_consistency,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    total = len(tests)
    print(f"\n{total - failed}/{total} tests PASS")
    sys.exit(0 if failed == 0 else 1)
