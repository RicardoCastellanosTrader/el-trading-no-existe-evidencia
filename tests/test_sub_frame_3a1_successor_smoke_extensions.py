"""
Tests greenfield mínimos Sub-Frame 3.A.1 successor smoke extensions Sub-fase B.0.

Validates 3 spec violations resolved §12 L38 21ª aplicación recursiva pre-launch:
  1. GAMMA_1_N_VALUES extended to include N=8 (gamma1_only_N8 cell label).
  2. gamma1_only_N6 cell label preserved (no regression).
  3. load_top_k_presets returns top-K presets ranked baseline pf_fwd_ci_low.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)


def test_gamma1_only_n6_cell_label_preserved():
    """gamma1_only_N6 cell label MUST exist in ablation matrix (no regression)."""
    from analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid import (
        build_ablation_matrix,
    )
    matrix = build_ablation_matrix()
    labels = [c[2] for c in matrix]
    assert 'gamma1_only_N6' in labels, (
        f"gamma1_only_N6 missing — regression. Available: {labels[:10]}"
    )
    # Verify (N, P, label) tuple
    cell_n6 = next(c for c in matrix if c[2] == 'gamma1_only_N6')
    assert cell_n6 == (6, 0.75, 'gamma1_only_N6'), f"unexpected: {cell_n6}"
    print("   ✅ gamma1_only_N6 (N=6, P=0.75) preserved")


def test_gamma1_only_n8_cell_label_added():
    """gamma1_only_N8 cell label MUST exist post-extension Edit 1."""
    from analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid import (
        build_ablation_matrix, GAMMA_1_N_VALUES,
    )
    assert 8 in GAMMA_1_N_VALUES, (
        f"GAMMA_1_N_VALUES MUST include 8 post-Sub-fase B.0 Edit 1. "
        f"Got: {GAMMA_1_N_VALUES}"
    )
    matrix = build_ablation_matrix()
    labels = [c[2] for c in matrix]
    assert 'gamma1_only_N8' in labels, (
        f"gamma1_only_N8 missing post-extension. "
        f"Available γ.1 labels: {[l for l in labels if 'gamma1_only' in l]}"
    )
    cell_n8 = next(c for c in matrix if c[2] == 'gamma1_only_N8')
    assert cell_n8 == (8, 0.75, 'gamma1_only_N8'), f"unexpected: {cell_n8}"
    # joint_N8_P* cells also auto-generated
    joint_n8 = [l for l in labels if l.startswith('joint_N8_')]
    assert len(joint_n8) == 6, (
        f"Expected 6 joint_N8_P* cells (P grid 7 - P=0.75 dup), got {len(joint_n8)}"
    )
    print(f"   ✅ gamma1_only_N8 + {len(joint_n8)} joint_N8_P* cells generated")


def test_load_presets_csv_path_corrected():
    """presets_dir output/production/ resolves to ~30 ONDOUSDT CSV presets (NOT 5 SYMBOL_ZONE_PRESETS fallback)."""
    import regime_walk_forward as rwf
    presets_dir = os.path.join(_ROOT, 'output', 'production')
    presets = rwf.load_presets('ONDO/USDT', presets_dir)
    assert presets is not None, f"load_presets returned None for {presets_dir}"
    assert len(presets) >= 25, (
        f"Expected ~30 CSV presets, got {len(presets)} — "
        f"likely fallback to SYMBOL_ZONE_PRESETS (5 hardcoded). "
        f"Spec violation #4 §12 L38 22ª NOT resolved."
    )
    print(f"   ✅ presets_dir output/production/ → {len(presets)} ONDOUSDT CSV presets")


def test_load_top_k_presets_ondo_csv():
    """load_top_k_presets returns top-K presets for ONDO with corrected CSV path."""
    from analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid import (
        load_top_k_presets,
    )
    presets_dir = os.path.join(_ROOT, 'output', 'production')
    baseline_dir = os.path.join(_ROOT, 'regime_wf')
    top_10 = load_top_k_presets(
        'ONDO/USDT', presets_dir, baseline_dir, k=10
    )
    assert top_10 is not None, "load_top_k_presets returned None"
    assert isinstance(top_10, list), f"expected list, got {type(top_10)}"
    assert 5 <= len(top_10) <= 10, (
        f"top_10 length {len(top_10)} out of [5, 10] range — "
        f"expected near 10 with valid CSV pool"
    )
    # Verify each preset is 12-tuple structure
    for p in top_10:
        assert len(p) == 12, f"preset tuple length {len(p)} != 12: {p}"
        assert isinstance(p[0], str), f"fast_type not str: {p[0]}"
        assert isinstance(p[1], int), f"fast_period not int: {p[1]}"
    print(f"   ✅ load_top_k_presets ONDO/USDT k=10 → {len(top_10)} CSV presets matched")


def test_load_top_k_presets_fallback_missing_baseline():
    """load_top_k_presets falls back to ALL presets if baseline JSON missing."""
    from analysis_scripts.sub_frame_3a1_gmm_n_pthreshold_grid import (
        load_top_k_presets,
    )
    presets_dir = os.path.join(_ROOT, 'output', 'production')
    # Use non-existent baseline dir
    top_k = load_top_k_presets(
        'ONDO/USDT', presets_dir, '/non/existent/dir', k=10
    )
    # Should return ALL presets (fallback graceful)
    assert top_k is not None, "should fallback to ALL presets, not None"
    assert len(top_k) >= 25, (
        f"fallback should return ALL ~30 CSV presets, got {len(top_k)}"
    )
    print(f"   ✅ Fallback graceful: returned {len(top_k)} CSV presets (full set)")


def main():
    print("=" * 70)
    print("Sub-Frame 3.A.1 successor smoke extensions tests Sub-fase B.0")
    print("=" * 70)

    tests = [
        ('test_gamma1_only_n6_cell_label_preserved',
         test_gamma1_only_n6_cell_label_preserved),
        ('test_gamma1_only_n8_cell_label_added',
         test_gamma1_only_n8_cell_label_added),
        ('test_load_presets_csv_path_corrected',
         test_load_presets_csv_path_corrected),
        ('test_load_top_k_presets_ondo_csv',
         test_load_top_k_presets_ondo_csv),
        ('test_load_top_k_presets_fallback_missing_baseline',
         test_load_top_k_presets_fallback_missing_baseline),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n{name}:")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed}/{len(tests)} PASS, {failed} FAIL")
    print('=' * 70)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
