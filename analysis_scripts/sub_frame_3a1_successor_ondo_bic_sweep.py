"""
Sub-Frame 3.A.1 successor — Parte 0_v2 ONDO BIC sweep N=2..12.

Resuelve H_AUX_1 (ONDO N_optimo NOT validated transferred BTC asumed).
Análoga Parte 0 ayer BTC BIC sweep (memory file consolidated §13.4
2026-04-29 entry permanente).

§12 L38 20ª aplicación recursiva — API verified primary sources real:
  - compute_regime_features(df, lookback=100) returns (features, valid_mask) tuple.
  - fit_gmm_with_convergence_monitoring(features, n_clusters, max_iter=300)
    returns dict {gmm, scaler, converged, n_iter_actual, max_iter_used, bic}.

Compute: ~70s zero compute analytical (10 GMM fits × ~7s each).

Outcome interpretation:
  - IF ONDO N_optimo ≈ N=6 knee similar BTC: H_AUX_1 RESUELTO favorable.
  - IF ONDO N_optimo significantly different: H_AUX_1 reveals gap →
    escalación Ricardo decision strategic.
"""

import sys
import time
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

import numpy as np
import pandas as pd

from regime_features import compute_regime_features
from analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid import (
    fit_gmm_with_convergence_monitoring,
)

LOOKBACK = 100
N_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12]


def main():
    t_total = time.time()

    print("=" * 70)
    print("Parte 0_v2 ONDO BIC sweep N=2..12 (resuelve H_AUX_1)")
    print("=" * 70)

    print("\n[1/3] Loading ONDO parquet...")
    parquet_path = os.path.join(_ROOT, 'data_cache', 'ONDOUSDT_1h.parquet')
    ondo_df = pd.read_parquet(parquet_path)
    print(f"  rows: {len(ondo_df):,}")
    ts_col = 'timestamp_ms' if 'timestamp_ms' in ondo_df.columns else 'timestamp'
    print(f"  range ({ts_col}): {ondo_df[ts_col].iloc[0]} -> "
          f"{ondo_df[ts_col].iloc[-1]}")

    print("\n[2/3] Computing regime features (lookback=100)...")
    features, valid_mask = compute_regime_features(ondo_df, lookback=LOOKBACK)
    print(f"  features shape: {features.shape}")
    print(f"  valid_mask sum: {int(valid_mask.sum())}/{len(valid_mask)}")

    valid_features = features[valid_mask]
    print(f"  valid_features: {valid_features.shape}")

    print("\n[3/3] BIC sweep N=2..12 ONDO:")
    bic_results = {}
    for n in N_VALUES:
        t0 = time.time()
        result = fit_gmm_with_convergence_monitoring(
            valid_features, n_clusters=n, max_iter=300
        )
        fit_time = time.time() - t0
        bic_results[n] = {
            'bic': result['bic'],
            'converged': result['converged'],
            'n_iter': result['n_iter_actual'],
            'max_iter_used': result['max_iter_used'],
            'fit_time': fit_time,
        }
        flag = "" if result['converged'] else " [NOT CONVERGED]"
        print(
            f"  N={n:2d}: BIC={result['bic']:11.1f}  "
            f"n_iter={result['n_iter_actual']:3d}  "
            f"fit={fit_time:5.1f}s{flag}"
        )

    print("\n" + "=" * 70)
    print("ΔBIC sequence ONDO:")
    sorted_ns = sorted(bic_results.keys())
    prev_bic = None
    for n in sorted_ns:
        bic = bic_results[n]['bic']
        if prev_bic is not None:
            prev_n = sorted_ns[sorted_ns.index(n) - 1]
            delta = bic - prev_bic
            marker = ""
            if abs(delta) < 200:
                marker = " <- PLATEAU"
            elif delta > 0:
                marker = " <- BIC INCREASE (multi-modal evidence)"
            print(f"  N={prev_n}->{n}: ΔBIC={delta:+8.0f}{marker}")
        prev_bic = bic

    n_optimo = min(bic_results.keys(), key=lambda n: bic_results[n]['bic'])
    print(f"\nN_optimo BIC absolute ONDO: N={n_optimo} "
          f"(BIC={bic_results[n_optimo]['bic']:.1f})")

    # Knee detection: find first N where ΔBIC drops below 200 (plateau signature)
    print("\nKnee detection (plateau threshold |ΔBIC| < 200):")
    knee_n = None
    for i, n in enumerate(sorted_ns[1:], start=1):
        prev_n = sorted_ns[i - 1]
        delta = bic_results[n]['bic'] - bic_results[prev_n]['bic']
        if abs(delta) < 200 and knee_n is None:
            knee_n = prev_n
            print(f"  Knee detected at N={prev_n} "
                  f"(ΔBIC N={prev_n}->{n}={delta:+.0f} < 200 plateau)")

    # Comparison BTC vs ONDO
    print("\n" + "=" * 70)
    print("Comparison BTC (Parte 0 ayer) vs ONDO (Parte 0_v2 hoy):")
    btc_bic_ayer = {
        2: 615064.3, 3: 607169.2, 4: 603223.4, 5: 599303.3,
        6: 598086.3, 7: 597924.9, 8: 596732.9, 9: 596059.5,
        10: 596089.3, 12: 595003.3,
    }
    print(f"  BTC knee ayer: N=6 (BIC=598086, ΔBIC N=5->6=-1217 + "
          f"N=6->7 plateau=-161)")
    print(f"  BTC absolute optimum: N=12 boundary unresolved (multi-modal "
          f"oscillation)")
    print(f"  ONDO knee detected: N={knee_n}" if knee_n
          else "  ONDO knee NOT detected (no plateau in range)")
    print(f"  ONDO absolute optimum: N={n_optimo} (BIC="
          f"{bic_results[n_optimo]['bic']:.1f})")

    # Verdict H_AUX_1
    print("\n" + "=" * 70)
    print("H_AUX_1 verdict ONDO N_optimo vs BTC transferred priori:")
    if knee_n == 6:
        print("  FAVORABLE: ONDO knee N=6 matches BTC priori - H_AUX_1 RESUELTO.")
    elif knee_n in (5, 7):
        print(f"  MOSTLY FAVORABLE: ONDO knee N={knee_n} adjacent BTC N=6 - "
              f"H_AUX_1 mostly resolved within +-1 tolerance.")
    elif knee_n is None:
        print("  AMBIGUOUS: ONDO no plateau detected in N=2..12 range. "
              "H_AUX_1 partially resolved - N=6 priori still defensible "
              "if BIC monotonic decreasing similar BTC.")
    else:
        print(f"  UNFAVORABLE: ONDO knee N={knee_n} significantly different "
              f"from BTC N=6 - H_AUX_1 reveals methodological gap. "
              f"Escalation Ricardo strategic decision.")

    print(f"\nTotal compute: {time.time() - t_total:.1f}s")
    return bic_results


if __name__ == '__main__':
    results = main()
