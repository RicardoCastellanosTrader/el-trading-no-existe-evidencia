"""Tests funding_context.py — cache + enrich + classifications."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from funding_context import (
    FundingCache, lookup_rate_at, classify_crowd, classify_position_vs_crowd,
    compute_bar_level_evolution, compute_pattern, enrich_trade,
    NEUTRAL_THRESHOLD, EnrichedTrade,
)


def mk_rates(entries: list[tuple[str, float]]) -> pd.DataFrame:
    """entries: [(iso_utc, rate), ...]"""
    if not entries:
        return pd.DataFrame(columns=["timestamp", "rate", "datetime"]).astype(
            {"timestamp": "int64", "rate": "float64", "datetime": "object"})
    rows = []
    for iso, r in entries:
        ts = pd.Timestamp(iso).tz_localize("UTC") if pd.Timestamp(iso).tz is None else pd.Timestamp(iso)
        rows.append({"timestamp": int(ts.timestamp() * 1000), "rate": r, "datetime": iso})
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


def mk_trade(side: str, entry_iso: str, exit_iso: str, symbol="BTC/USDT") -> EnrichedTrade:
    entry_ts = pd.Timestamp(entry_iso).tz_localize("UTC") if pd.Timestamp(entry_iso).tz is None else pd.Timestamp(entry_iso)
    exit_ts = pd.Timestamp(exit_iso).tz_localize("UTC") if pd.Timestamp(exit_iso).tz is None else pd.Timestamp(exit_iso)
    return EnrichedTrade(
        timestamp=exit_ts, symbol=symbol, side=side,
        entry_price=100.0, exit_price=101.0, size_usdt=10.0,
        pnl_pct=1.0, pnl_usdt=0.1, funding_paid=0.0, reason_exit="tf_exit",
        flag="", entry_timestamp_ms=int(entry_ts.timestamp() * 1000),
        entry_ts_ms=int(entry_ts.timestamp() * 1000),
        exit_ts_ms=int(exit_ts.timestamp() * 1000),
    )


class TestCache(unittest.TestCase):
    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            cache = FundingCache(d)
            df = mk_rates([
                ("2026-04-01 08:00:00", 0.0001),
                ("2026-04-01 16:00:00", -0.0002),
            ])
            cache.save("BTC/USDT", df)
            loaded = cache.load("BTC/USDT")
            self.assertEqual(len(loaded), 2)
            self.assertAlmostEqual(float(loaded["rate"].iloc[0]), 0.0001)
            self.assertAlmostEqual(float(loaded["rate"].iloc[1]), -0.0002)

    def test_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            cache = FundingCache(d)
            df = mk_rates([
                ("2026-04-01 08:00:00", 0.0001),
                ("2026-04-02 08:00:00", 0.00005),
            ])
            cache.save("ETH/USDT", df)
            lo, hi = cache.coverage("ETH/USDT")
            self.assertEqual(lo, int(pd.Timestamp("2026-04-01 08:00:00", tz="UTC").timestamp() * 1000))
            self.assertEqual(hi, int(pd.Timestamp("2026-04-02 08:00:00", tz="UTC").timestamp() * 1000))
            lo2, hi2 = cache.coverage("NOTINCACHE/USDT")
            self.assertIsNone(lo2)
            self.assertIsNone(hi2)


class TestLookup(unittest.TestCase):
    def test_lookup_before_first(self):
        rates = mk_rates([("2026-04-01 08:00:00", 0.0001)])
        ts = int(pd.Timestamp("2026-04-01 07:00:00", tz="UTC").timestamp() * 1000)
        self.assertIsNone(lookup_rate_at(rates, ts))

    def test_lookup_exact(self):
        rates = mk_rates([
            ("2026-04-01 08:00:00", 0.0001),
            ("2026-04-01 16:00:00", -0.0002),
        ])
        ts = int(pd.Timestamp("2026-04-01 08:00:00", tz="UTC").timestamp() * 1000)
        self.assertAlmostEqual(lookup_rate_at(rates, ts), 0.0001)

    def test_lookup_between(self):
        rates = mk_rates([
            ("2026-04-01 08:00:00", 0.0001),
            ("2026-04-01 16:00:00", -0.0002),
        ])
        ts = int(pd.Timestamp("2026-04-01 12:00:00", tz="UTC").timestamp() * 1000)
        self.assertAlmostEqual(lookup_rate_at(rates, ts), 0.0001)

    def test_lookup_empty(self):
        rates = mk_rates([])
        ts = int(pd.Timestamp("2026-04-01 08:00:00", tz="UTC").timestamp() * 1000)
        self.assertIsNone(lookup_rate_at(rates, ts))


class TestClassify(unittest.TestCase):
    def test_neutral(self):
        self.assertEqual(classify_crowd(0.0), "neutral")
        self.assertEqual(classify_crowd(NEUTRAL_THRESHOLD * 0.5), "neutral")
        self.assertEqual(classify_crowd(-NEUTRAL_THRESHOLD * 0.5), "neutral")

    def test_long_crowd(self):
        self.assertEqual(classify_crowd(NEUTRAL_THRESHOLD * 2), "long_crowd")

    def test_short_crowd(self):
        self.assertEqual(classify_crowd(-NEUTRAL_THRESHOLD * 2), "short_crowd")

    def test_unknown(self):
        self.assertEqual(classify_crowd(None), "unknown")
        self.assertEqual(classify_crowd(float("nan")), "unknown")

    def test_aligned_contrarian(self):
        self.assertEqual(classify_position_vs_crowd("long", "long_crowd"), "aligned")
        self.assertEqual(classify_position_vs_crowd("short", "short_crowd"), "aligned")
        self.assertEqual(classify_position_vs_crowd("long", "short_crowd"), "contrarian")
        self.assertEqual(classify_position_vs_crowd("short", "long_crowd"), "contrarian")
        self.assertEqual(classify_position_vs_crowd("long", "neutral"), "neutral")


class TestBarLevelEvolution(unittest.TestCase):
    def test_short_trade_constant_rate(self):
        """Trade <8h con funding constante → min=max=mean, no flip."""
        rates = mk_rates([
            ("2026-04-01 08:00:00", 0.0002),
            ("2026-04-01 16:00:00", 0.0003),
        ])
        entry = int(pd.Timestamp("2026-04-01 10:00:00", tz="UTC").timestamp() * 1000)
        exit = int(pd.Timestamp("2026-04-01 13:00:00", tz="UTC").timestamp() * 1000)
        evo = compute_bar_level_evolution(rates, entry, exit, "long")
        self.assertAlmostEqual(evo["funding_rate_min_during"], 0.0002)
        self.assertAlmostEqual(evo["funding_rate_max_during"], 0.0002)
        self.assertAlmostEqual(evo["funding_rate_mean_during"], 0.0002)
        self.assertFalse(evo["funding_crowd_flipped"])
        self.assertEqual(evo["n_bars_contrarian"], 0)  # long_crowd + long → aligned.

    def test_long_trade_crosses_boundary_no_flip(self):
        """Trade cruzando 16:00 boundary, ambos rates positivos → no flip."""
        rates = mk_rates([
            ("2026-04-01 08:00:00", 0.0002),
            ("2026-04-01 16:00:00", 0.0003),
        ])
        entry = int(pd.Timestamp("2026-04-01 14:00:00", tz="UTC").timestamp() * 1000)
        exit = int(pd.Timestamp("2026-04-01 18:00:00", tz="UTC").timestamp() * 1000)
        evo = compute_bar_level_evolution(rates, entry, exit, "long")
        self.assertAlmostEqual(evo["funding_rate_min_during"], 0.0002)
        self.assertAlmostEqual(evo["funding_rate_max_during"], 0.0003)
        self.assertFalse(evo["funding_crowd_flipped"])  # both positive.

    def test_crowd_flip(self):
        """Trade cruza boundary donde rate cambia de signo → flip=True."""
        rates = mk_rates([
            ("2026-04-01 08:00:00", 0.0002),
            ("2026-04-01 16:00:00", -0.0002),
        ])
        entry = int(pd.Timestamp("2026-04-01 14:00:00", tz="UTC").timestamp() * 1000)
        exit = int(pd.Timestamp("2026-04-01 18:00:00", tz="UTC").timestamp() * 1000)
        evo = compute_bar_level_evolution(rates, entry, exit, "long")
        self.assertTrue(evo["funding_crowd_flipped"])
        # Long position: aligned durante 14-16 (long_crowd), contrarian 16-18 (short_crowd).
        self.assertGreater(evo["n_bars_contrarian"], 0)

    def test_contrarian_throughout(self):
        """Position contrarian todo el trade → n_bars = hold_bars."""
        rates = mk_rates([("2026-04-01 08:00:00", 0.0002)])
        entry = int(pd.Timestamp("2026-04-01 10:00:00", tz="UTC").timestamp() * 1000)
        exit = int(pd.Timestamp("2026-04-01 13:00:00", tz="UTC").timestamp() * 1000)
        evo = compute_bar_level_evolution(rates, entry, exit, "short")  # short vs long_crowd = contrarian.
        self.assertGreater(evo["n_bars_contrarian"], 0)
        self.assertEqual(evo["n_bars_contrarian"], evo["max_consecutive_bars_contrarian"])


class TestEnrichTradePattern(unittest.TestCase):
    def test_aligned_aligned(self):
        rates = mk_rates([("2026-04-01 08:00:00", 0.0002)])
        tr = mk_trade("long", "2026-04-01 10:00:00", "2026-04-01 12:00:00")
        enrich_trade(tr, rates)
        self.assertEqual(tr.signal_vs_entry_crowd, "aligned")
        self.assertEqual(tr.position_vs_exit_crowd, "aligned")
        self.assertEqual(tr.entry_exit_pattern, "aligned->aligned")

    def test_pattern_flip(self):
        rates = mk_rates([
            ("2026-04-01 08:00:00", 0.0002),
            ("2026-04-01 16:00:00", -0.0002),
        ])
        tr = mk_trade("long", "2026-04-01 14:00:00", "2026-04-01 18:00:00")
        enrich_trade(tr, rates)
        # Long + entry rate +0.0002 → aligned. Long + exit rate -0.0002 → contrarian.
        self.assertEqual(tr.signal_vs_entry_crowd, "aligned")
        self.assertEqual(tr.position_vs_exit_crowd, "contrarian")
        self.assertEqual(tr.entry_exit_pattern, "aligned->contrarian")
        self.assertTrue(tr.funding_crowd_flipped)

    def test_nan_fallback(self):
        rates = mk_rates([])
        tr = mk_trade("long", "2026-04-01 10:00:00", "2026-04-01 12:00:00")
        enrich_trade(tr, rates)
        self.assertIsNone(tr.funding_rate_at_entry)
        self.assertEqual(tr.funding_crowd_direction_entry, "unknown")
        self.assertEqual(tr.entry_exit_pattern, "unknown")
        self.assertFalse(tr.funding_crowd_flipped)


class TestComputePattern(unittest.TestCase):
    def test_9_combos(self):
        for a in ("aligned", "contrarian", "neutral"):
            for b in ("aligned", "contrarian", "neutral"):
                self.assertEqual(compute_pattern(a, b), f"{a}->{b}")
        self.assertEqual(compute_pattern("unknown", "aligned"), "unknown")
        self.assertEqual(compute_pattern("aligned", "unknown"), "unknown")


if __name__ == "__main__":
    unittest.main()
