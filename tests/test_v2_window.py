from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))

from v2_common import (  # noqa: E402
    LUNAR_SYNODIC_DAYS,
    SIDEREAL_FREQUENCY,
    SOLAR_FREQUENCY,
    YEAR_DAYS,
    grid_for,
)
from window import (  # noqa: E402
    fixed_loci,
    is_alias_of_stronger_v2,
    is_window_alias_v2,
    veto_loci,
    window_peaks,
    window_strength_grid,
)
from lomb_scargle_common import window_strength  # noqa: E402


def _ztf_like_times() -> np.ndarray:
    rng = np.random.default_rng(20260902)
    seasons = []
    for year_start in (0.0, 365.25, 730.5):
        nights = np.sort(rng.choice(np.arange(225), size=145, replace=False))
        times = year_start + nights + rng.uniform(0.04, 0.30, size=nights.size)
        seasons.append(times)
    return np.concatenate(seasons)


def test_window_strength_grid_matches_frozen_exact_strength():
    time = _ztf_like_times()
    grid = grid_for("low", float(np.ptp(time)))
    frequency, strength = window_strength_grid(time, grid, subsample=10)
    rng = np.random.default_rng(913)
    indices = rng.choice(frequency.size, size=200, replace=False)

    exact = window_strength(time, frequency[indices])

    np.testing.assert_allclose(strength[indices], exact, rtol=0.0, atol=1e-3)


def test_fixed_loci_include_preregistered_families_and_beats():
    loci = fixed_loci()
    by_label = {str(row["label"]): float(row["frequency_per_day"]) for row in loci}

    assert by_label["solar_k1_m+0"] == pytest.approx(SOLAR_FREQUENCY)
    assert by_label["sidereal_k1"] == pytest.approx(SIDEREAL_FREQUENCY)
    assert by_label["lunar_k1_m+0"] == pytest.approx(1.0 / LUNAR_SYNODIC_DAYS)
    assert by_label["yearly_m1"] == pytest.approx(1.0 / YEAR_DAYS)
    for k in (1, 2):
        for sign in (-1, 1):
            assert by_label[f"solar_k{k}_lunar{sign:+d}"] == pytest.approx(
                k * SOLAR_FREQUENCY + sign / LUNAR_SYNODIC_DAYS
            )


@pytest.mark.parametrize(
    ("frequency", "prefix"),
    [
        (1.00274, "sidereal_"),
        (2.0, "solar_"),
        (1.0 / LUNAR_SYNODIC_DAYS, "lunar_"),
        (1.0 + 2.0 / YEAR_DAYS, "solar_"),
    ],
)
def test_fixed_window_aliases_are_vetoed_with_family_label(frequency, prefix):
    time = _ztf_like_times()
    tolerance = 1.5 / np.ptp(time)

    aliased, _, label = is_window_alias_v2(time, frequency, tolerance, fixed_loci())

    assert aliased is True
    assert label.startswith(prefix)


def test_science_frequency_is_not_a_window_alias_on_synthetic_cadence():
    time = _ztf_like_times()
    tolerance = 1.5 / np.ptp(time)

    aliased, _, label = is_window_alias_v2(time, 12.3, tolerance, fixed_loci())

    assert aliased is False
    assert label == ""


@pytest.mark.parametrize(
    "candidate",
    [
        0.0339 + 1.0,
        0.0339 + SIDEREAL_FREQUENCY,
        0.0339 - 2.0,
        1.0 - 0.0339,
        SIDEREAL_FREQUENCY - 0.0339,
        2.0 - 0.0339,
    ],
)
def test_alias_of_stronger_catches_difference_and_mirror_families(candidate):
    assert is_alias_of_stronger_v2(candidate, [0.0339], tolerance=1e-5)


def test_unrelated_science_peaks_are_not_stronger_peak_aliases():
    assert not is_alias_of_stronger_v2(12.3, [7.1], tolerance=1e-4)


def test_real_d3_window_peaks_and_vetoes_when_shard_is_available():
    shard = (
        ROOT
        / "outputs/generalization/d3_sync/d3_panels/exposure_stars"
        / "9000000000000892667.csv.gz"
    )
    if not shard.exists():
        pytest.skip("real D3 shard 9000000000000892667 is not present")
    frame = pd.read_csv(shard, usecols=["band", "bjd_tdb"])
    baseline = float(frame["bjd_tdb"].max() - frame["bjd_tdb"].min())
    time = np.sort(frame.loc[frame["band"] == "zg", "bjd_tdb"].to_numpy(dtype=float))
    grid = grid_for("low", baseline)

    peaks = window_peaks(time, grid)
    frequencies = np.array([row["frequency_per_day"] for row in peaks])
    assert np.min(np.abs(frequencies - 1.00274)) < 2.0 / baseline
    assert np.min(np.abs(frequencies - 2.0055)) < 2.0 / baseline

    tolerance = 1.5 / baseline
    loci = veto_loci(peaks)
    assert is_window_alias_v2(time, 1.0027, tolerance, loci)[0]
    assert is_window_alias_v2(time, 0.0339, tolerance, loci)[0]
    assert not is_window_alias_v2(time, 12.3, tolerance, loci)[0]
