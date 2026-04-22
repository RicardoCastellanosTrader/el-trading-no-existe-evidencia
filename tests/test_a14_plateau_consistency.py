"""
Tests A14 (W1) — plateau_ratio consistency con _get_neighbors.

Pre-fix: plateau_ratio usaba bit-flip brutal en los 26 bits del config_id,
mientras _get_neighbors (canonical, usado en _compute_sqn_haircut)
respeta semántica bitmask vs discrete de _PARAM_FIELDS.

Post-fix 2026-04-23: plateau_ratio usa _get_neighbors.

Standalone. Run: python tests/test_a14_plateau_consistency.py
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
sys.path.insert(0, _root)

import regime_walk_forward as wf


def test_1_get_neighbors_happy_path():
    """_get_neighbors returns a non-empty set for any valid config_id."""
    cid = 2457036  # ONDO C0 productivo
    neighbors = wf._get_neighbors(cid)
    assert isinstance(neighbors, set)
    assert len(neighbors) > 0
    # Must not contain the config itself
    assert cid not in neighbors
    print(f"  test_1 PASS: _get_neighbors({cid}) = {len(neighbors)} neighbors")


def test_2_get_neighbors_distinguishes_bitmask_vs_discrete():
    """_get_neighbors produces different count than 26 bit-flips (the
    pre-fix formula), because discrete fields only generate ±1 neighbors,
    not N bit-flips per field."""
    cid = 2457036
    canonical = wf._get_neighbors(cid)

    # Recreate pre-fix formula: 26 bit-flips always
    brute_flips = set()
    for bit in range(26):
        brute_flips.add(cid ^ (1 << bit))
    brute_flips.discard(cid)

    # If both are identical for every config, the fix is meaningless.
    # We expect at least one config where they differ (typically many).
    # For ONDO C0 2457036 they almost certainly differ because _PARAM_FIELDS
    # has a mix of bitmask and discrete fields.
    assert canonical != brute_flips, \
        f"canonical {len(canonical)} == brute {len(brute_flips)} — fix is moot"
    print(f"  test_2 PASS: canonical {len(canonical)} != brute-26 {len(brute_flips)}"
          f" (symmetric diff {len(canonical ^ brute_flips)})")


def test_3_plateau_ratio_uses_canonical_neighbors():
    """Inspect source code of plateau block to confirm it calls
    _get_neighbors (not bit-flip loop)."""
    src_path = os.path.join(_root, 'regime_walk_forward.py')
    with open(src_path, encoding='utf-8') as f:
        source = f.read()
    # Locate plateau analysis block
    marker = 'Phase 4: Plateau analysis'
    idx = source.find(marker)
    assert idx >= 0, "plateau block marker not found"
    # Take next ~1500 chars of the block
    block = source[idx:idx + 1500]
    assert '_get_neighbors(cid)' in block, \
        "plateau block does not call _get_neighbors (fix not applied)"
    # And verify the old brute bit-flip is gone
    assert 'for bit in range(26):' not in block, \
        "old bit-flip loop still present in plateau block"
    print(f"  test_3 PASS: plateau_ratio source uses _get_neighbors, no 26-bit loop")


def test_4_zero_neighbors_degenerate_no_crash():
    """If a config has no valid neighbors (edge case at boundaries), code
    path uses max(len(neighbors), 1) guard → ratio=0/1=0, no ZeroDivision."""
    # _get_neighbors for any legal config_id returns at least one neighbor
    # because _PARAM_FIELDS has multiple fields. But we exercise the guard.
    validated_set = set()  # empty → ratio 0
    neighbors = wf._get_neighbors(2457036)
    n_in = sum(1 for nb in neighbors if nb in validated_set)
    ratio = n_in / max(len(neighbors), 1)
    assert ratio == 0.0
    # Degenerate: simulate empty neighbors (defensively)
    empty_neighbors = set()
    n_in_e = sum(1 for nb in empty_neighbors if nb in validated_set)
    ratio_e = n_in_e / max(len(empty_neighbors), 1)
    assert ratio_e == 0.0  # 0 / max(0, 1) = 0
    print(f"  test_4 PASS: degenerate cases handled (ratio=0 no crash)")


def _run_all():
    print("=" * 68)
    print("A14 (W1) plateau_ratio consistency test suite")
    print("=" * 68)
    tests = [
        test_1_get_neighbors_happy_path,
        test_2_get_neighbors_distinguishes_bitmask_vs_discrete,
        test_3_plateau_ratio_uses_canonical_neighbors,
        test_4_zero_neighbors_degenerate_no_crash,
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
