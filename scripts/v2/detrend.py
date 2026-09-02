#!/usr/bin/env python3
"""Mechanism 4 — support-aware series preparation (replaces prepare_series).

Frozen high pass: magnitude minus the per-night MEDIAN, so every night with a
single exposure becomes exactly zero (85 % of D3 band-nights); D2 recovery
rides entirely on the surviving within-night support (6 % at low W_g -> 35 %
at high W_g). v2:

  low pass : aligned magnitude minus the band's 1/magerr^2-weighted mean
             (identical to the frozen low pass after alignment);
  high pass: aligned magnitude minus a running weighted median over a
             centred window of `trend_window_days` (default 30 d), each window
             holding at least `min_trend_points` (5) points — where the
             centred window holds fewer, the 5 nearest-in-time points are
             used. Single-exposure nights are KEPT, valued relative to the
             local trend.

The 30-day scale (0.033 c/d) sits far below the low-pass floor (2/T ~ 0.0007
c/d is NOT affected because the low pass never uses this trend) and far above
the high-pass lower bound (24 c/d); a trend that smooth cannot inject or
remove power in the high band. Both series use ONE time origin (the star's
first epoch across both bands) so per-band phases are comparable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from align import weighted_median
from v2_common import DEFAULT, V2Constants


def running_weighted_median(
    time: np.ndarray,
    values: np.ndarray,
    weights: np.ndarray,
    window_days: float,
    min_points: int,
) -> np.ndarray:
    """Centred running weighted median; `time` must be sorted ascending."""
    time = np.asarray(time, dtype=float)
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if time.size and np.any(np.diff(time) < 0):
        raise ValueError("running_weighted_median needs ascending time")
    half = 0.5 * float(window_days)
    lower = np.searchsorted(time, time - half, side="left")
    upper = np.searchsorted(time, time + half, side="right")
    trend = np.empty(time.size, dtype=float)
    k = min(int(min_points), time.size)
    for i in range(time.size):
        start, stop = int(lower[i]), int(upper[i])
        if stop - start >= k:
            trend[i] = weighted_median(values[start:stop], weights[start:stop])
        else:
            nearest = np.argsort(np.abs(time - time[i]), kind="stable")[:k]
            trend[i] = weighted_median(values[nearest], weights[nearest])
    return trend


def prepare_series_v2(
    frame: pd.DataFrame,
    high_frequency: bool,
    origin: float,
    constants: V2Constants = DEFAULT,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(time, detrended magnitude, magnitude error) for one band, time measured
    from `origin` (the star's global first epoch), rows in stable time order."""
    ordered = frame.sort_values("bjd_tdb", kind="stable")
    time = ordered["bjd_tdb"].to_numpy(dtype=float) - float(origin)
    mag = ordered["mag"].to_numpy(dtype=float)
    error = ordered["magerr"].to_numpy(dtype=float)
    weights = 1.0 / np.square(error)
    if high_frequency:
        trend = running_weighted_median(
            time, mag, weights, constants.trend_window_days, constants.min_trend_points
        )
        mag = mag - trend
    else:
        mag = mag - np.average(mag, weights=weights)
    return time, mag, error


__all__ = ["prepare_series_v2", "running_weighted_median"]
