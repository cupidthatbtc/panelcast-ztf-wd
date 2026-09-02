"""Shared-night per-oid zero-point alignment (align.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "v2"))

from align import align_zero_points, shared_night_offset, weighted_median  # noqa: E402
from v2_common import DEFAULT  # noqa: E402


def _band(rng, band: str, oids: dict[str, tuple[float, list[int]]], base: float = 16.0,
          n_exp: int = 2, noise: float = 0.004) -> pd.DataFrame:
    """oids: label -> (offset_mag, nights); every night gets `n_exp` rows."""
    rows = []
    for label, (offset, nights) in oids.items():
        for night in nights:
            for k in range(n_exp):
                t = 58000.0 + night + 0.2 + 0.01 * k
                rows.append({"source_id": "s", "band": band, "oid": label, "mjd": t, "bjd_tdb": t + 2400000.5,
                             "night_mjd": float(night), "mag": base + offset + rng.normal(0.0, noise),
                             "magerr": noise, "chi": 1.0, "ra": 0.0, "dec": 0.0})
    return pd.DataFrame(rows)


def test_weighted_median_matches_brute_force():
    rng = np.random.default_rng(3)
    for _ in range(50):
        values = rng.integers(0, 6, size=15).astype(float)   # many ties
        weights = rng.uniform(0.1, 3.0, size=15)
        order = np.argsort(values, kind="stable")
        cumulative = np.cumsum(weights[order])
        expected = values[order][np.searchsorted(cumulative, 0.5 * cumulative[-1], side="left")]
        assert weighted_median(values, weights) == expected


def test_shared_night_offsets_recovered_and_small_oids_left_unshifted():
    rng = np.random.default_rng(11)
    nights = list(range(0, 60, 2))
    frame = pd.concat([
        _band(rng, "zg", {"a": (0.0, nights), "b": (+0.012, nights[::2]), "c": (-0.020, nights[1::2]),
                          "tiny": (+0.050, nights[:2])}, n_exp=1),
        _band(rng, "zr", {"a": (0.0, nights)}),
    ], ignore_index=True)
    aligned, table = align_zero_points(frame, DEFAULT)
    rows = {(r["band"], r["oid"]): r for r in table}
    assert rows[("zg", "a")]["role"] == "anchor" and rows[("zg", "a")]["offset_mmag"] == 0.0
    for label, offset in (("b", 12.0), ("c", -20.0)):
        r = rows[("zg", label)]
        assert r["applied"] and r["role"] == "aligned" and r["n_shared_nights"] >= 5
        assert abs(r["offset_mmag"] - offset) < 0.5 * 4 + 1.0   # noise-limited (mmag)
        sub = aligned[(aligned["band"] == "zg") & (aligned["oid_label"] == label)]
        anchor = aligned[(aligned["band"] == "zg") & (aligned["oid_label"] == "a")]
        assert abs(sub["mag"].median() - anchor["mag"].median()) < 4.0e-3   # ~1 sigma of a 15-row median
    tiny = rows[("zg", "tiny")]
    assert not tiny["applied"] and tiny["role"] == "unshifted_too_few_rows"
    sub = aligned[(aligned["band"] == "zg") & (aligned["oid_label"] == "tiny")]
    assert (sub["mag"] == sub["mag_raw"]).all()
    assert rows[("zr", "a")]["role"] == "anchor" and len([r for r in table if r["band"] == "zr"]) == 1


def test_disjoint_nights_are_not_aligned():
    rng = np.random.default_rng(5)
    frame = pd.concat([
        _band(rng, "zg", {"a": (0.0, list(range(0, 40))), "b": (+0.030, list(range(50, 90)))}),
        _band(rng, "zr", {"a": (0.0, list(range(0, 40)))}),
    ], ignore_index=True)
    aligned, table = align_zero_points(frame, DEFAULT)
    b = next(r for r in table if r["band"] == "zg" and r["oid"] == "b")
    assert not b["applied"] and b["role"] == "unshifted_insufficient_overlap" and b["n_shared_nights"] == 0
    assert abs(b["offset_mmag"] - 30.0) < 3.0    # whole-row estimate is reported, not applied
    assert (aligned["mag"] == aligned["mag_raw"]).all()


def test_slow_variability_does_not_enter_a_shared_night_offset():
    rng = np.random.default_rng(9)
    nights = list(range(0, 100))
    frame = pd.concat([_band(rng, "zg", {"a": (0.0, nights), "b": (+0.010, nights[::3])}),
                       _band(rng, "zr", {"a": (0.0, nights)})], ignore_index=True)
    # a 300-day ramp of 80 mmag affects both oids identically on shared nights
    frame["mag"] += 0.080 * (frame["night_mjd"] / 300.0)
    _, table = align_zero_points(frame, DEFAULT)
    b = next(r for r in table if r["band"] == "zg" and r["oid"] == "b")
    assert b["applied"] and abs(b["offset_mmag"] - 10.0) < 1.5


def test_anchor_is_the_oid_with_most_rows_and_no_oid_column_is_one_oid():
    rng = np.random.default_rng(1)
    frame = pd.concat([_band(rng, "zg", {"x": (0.0, list(range(10))), "y": (0.005, list(range(30)))}),
                       _band(rng, "zr", {"x": (0.0, list(range(10)))})], ignore_index=True)
    _, table = align_zero_points(frame, DEFAULT)
    assert next(r for r in table if r["band"] == "zg" and r["role"] == "anchor")["oid"] == "y"
    single = frame.drop(columns=["oid"])
    aligned, table = align_zero_points(single, DEFAULT)
    assert [r["role"] for r in table] == ["anchor", "anchor"]
    assert (aligned["mag"] == aligned["mag_raw"]).all()


def test_shared_night_offset_direct():
    mags = np.array([1.0, 1.0, 1.1, 1.1, 2.0, 1.0, 1.1])
    weights = np.ones(7)
    nights = np.array([0, 0, 0, 0, 1, 2, 2], dtype=float)
    oid = np.array([False, False, True, True, True, False, True])
    anchor = ~oid
    offset, shared = shared_night_offset(mags, weights, nights, oid, anchor)
    assert shared == 2 and offset == pytest.approx(0.1)
