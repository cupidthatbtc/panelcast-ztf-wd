from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))

from detrend import prepare_series_v2, running_weighted_median  # noqa: E402
from lomb_scargle_common import prepare_series  # noqa: E402
from multiband import sinusoid_fit  # noqa: E402


def _frame(time: np.ndarray, mag: np.ndarray, error: float = 0.003) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "bjd_tdb": 2_460_000.0 + time,
            "night_mjd": np.floor(time).astype(int),
            "mag": mag,
            "magerr": error,
        }
    )


def test_single_exposure_nights_survive_v2_high_pass():
    time = np.arange(40.0)
    mag = 15.0 + 0.002 * time + 0.015 * np.sin(2.0 * np.pi * 0.173 * time + 0.4)
    frame = _frame(time, mag)

    _, frozen_values, _ = prepare_series(frame, high_frequency=True)
    _, v2_values, _ = prepare_series_v2(
        frame, high_frequency=True, origin=float(frame["bjd_tdb"].min())
    )

    np.testing.assert_array_equal(frozen_values, np.zeros_like(frozen_values))
    assert np.count_nonzero(v2_values) > 0
    assert np.ptp(v2_values) > 0.01


def test_running_median_removes_more_than_80_percent_of_slow_trend_rms():
    time = np.arange(0.0, 300.0, 0.5)
    slow = 0.30 * (time / np.ptp(time) - 0.5) + 0.010 * np.sin(2.0 * np.pi * time / 60.0)
    weights = np.ones_like(time)

    trend = running_weighted_median(time, slow, weights, window_days=30.0, min_points=5)
    residual = slow - trend

    original_rms = np.sqrt(np.mean(np.square(slow - np.mean(slow))))
    residual_rms = np.sqrt(np.mean(np.square(residual)))
    assert residual_rms < 0.20 * original_rms


def test_running_median_preserves_12_cycles_per_day_amplitude():
    nights = np.arange(120.0)
    offsets = np.array([0.013, 0.041, 0.076])
    time = np.sort((nights[:, None] + offsets[None, :]).ravel())
    amplitude = 0.020
    values = 15.0 + amplitude * np.sin(2.0 * np.pi * 12.0 * time + 0.73)
    errors = np.full_like(time, 0.003)
    before = sinusoid_fit(time, values, errors, 12.0)["amplitude"]

    trend = running_weighted_median(
        time, values, 1.0 / np.square(errors), window_days=30.0, min_points=5
    )
    after = sinusoid_fit(time, values - trend, errors, 12.0)["amplitude"]

    assert abs(after / before - 1.0) < 0.02


def test_sparse_window_falls_back_to_five_nearest_points():
    time = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
    values = np.array([9.0, 1.0, 8.0, 2.0, 7.0, 3.0, 6.0])
    weights = np.ones_like(time)

    trend = running_weighted_median(time, values, weights, window_days=1.0, min_points=5)

    for i, epoch in enumerate(time):
        nearest = np.argsort(np.abs(time - epoch), kind="stable")[:5]
        expected = np.sort(values[nearest])[2]
        assert trend[i] == expected


def test_running_weighted_median_rejects_unsorted_time():
    with pytest.raises(ValueError, match="ascending"):
        running_weighted_median(
            np.array([0.0, 2.0, 1.0]),
            np.array([1.0, 2.0, 3.0]),
            np.ones(3),
            window_days=30.0,
            min_points=5,
        )
