#!/usr/bin/env python3
"""Mechanism 2 — spectral window + extended alias veto.

Frozen veto: the sidereal family only (k * 1.00274 +/- 1.5/T) plus the local
window test (max window strength within +/- 1.5/T >= 0.1). D3 false triggers
pile into the 1 - delta / 2 - delta wings, a lunar-synodic cluster (0.034 c/d)
and the 1 and 2 c/d cores. v2 vetoes a candidate when it lies within 1.5/T of
ANY listed spectral-window locus:

  fixed loci : k * 1.0 c/d (k = 1..3) with m / 365.25 yearly sidebands
               (m = -2..2; m = +1 IS the sidereal frequency), k * 1.00274
               (k = 1, 2), k / 29.530589 (k = 1, 2) with m = -1..1 yearly
               sidebands, and m / 365.25 (m = 1, 2);
  data-driven: the top-N (N = 12) peaks of the band's own spectral window on
               the pass grid subsampled x10;
  local test : the frozen rule, kept verbatim.

`is_alias_of_stronger` is generalised to the solar AND sidereal spacings and
to the mirror family k * spacing - f0 (the 1 - delta / 2 - delta wings: the
strongest D3 false-trigger locus, e.g. sidereal - lunar = 0.9688 c/d).
delta Sct (4-24 c/d) and DAV (40-1200 c/d) science frequencies are untouched
by construction; true ~1 c/d rotators are sacrificed and disclosed.
"""

from __future__ import annotations

import math

import numpy as np
from astropy.timeseries.periodograms.lombscargle.implementations.utils import trig_sum
from scipy.signal import find_peaks

from v2_common import (
    DEFAULT,
    LUNAR_SYNODIC_DAYS,
    SIDEREAL_FREQUENCY,
    SOLAR_FREQUENCY,
    WINDOW_POWER_THRESHOLD,
    YEAR_DAYS,
    FrequencyGrid,
    V2Constants,
    window_strength,
)

ALIAS_SPACINGS = (SOLAR_FREQUENCY, SIDEREAL_FREQUENCY)


def fixed_loci() -> list[dict[str, object]]:
    loci: list[dict[str, object]] = []
    for k in (1, 2, 3):
        for m in (-2, -1, 0, 1, 2):
            loci.append({"label": f"solar_k{k}_m{m:+d}",
                         "frequency_per_day": k * SOLAR_FREQUENCY + m / YEAR_DAYS})
    for k in (1, 2):
        loci.append({"label": f"sidereal_k{k}", "frequency_per_day": k * SIDEREAL_FREQUENCY})
    for k in (1, 2):
        for m in (-1, 0, 1):
            loci.append({"label": f"lunar_k{k}_m{m:+d}",
                         "frequency_per_day": k / LUNAR_SYNODIC_DAYS + m / YEAR_DAYS})
    for k in (1, 2):
        for spacing_label, spacing in (("solar", SOLAR_FREQUENCY), ("sidereal", SIDEREAL_FREQUENCY)):
            for sign in (-1, 1):
                loci.append({"label": f"{spacing_label}_k{k}_lunar{sign:+d}",
                             "frequency_per_day": k * spacing + sign / LUNAR_SYNODIC_DAYS})
    for m in (1, 2):
        loci.append({"label": f"yearly_m{m}", "frequency_per_day": m / YEAR_DAYS})
    for locus in loci:
        locus["source"] = "fixed"
        locus["strength"] = None
    return loci


def window_strength_grid(
    time: np.ndarray, grid: FrequencyGrid, subsample: int
) -> tuple[np.ndarray, np.ndarray]:
    """Spectral-window strength |mean exp(-2 pi i f t)|^2 on the pass grid
    subsampled by `subsample`, via the same O(N log N) trigonometric-sum
    approximation the frozen fast periodogram uses (exactness checked
    against the frozen window_strength in tests)."""
    time = np.asarray(time, dtype=float)
    count = int(math.ceil(grid.size / subsample))
    step = grid.step * subsample
    centered = time - np.mean(time)
    weights = np.full(time.shape, 1.0 / time.size)
    sines, cosines = trig_sum(centered, weights, step, count, f0=grid.minimum, use_fft=True)
    frequency = grid.minimum + step * np.arange(count, dtype=np.float64)
    return frequency, np.square(sines) + np.square(cosines)


def window_peaks(
    time: np.ndarray, grid: FrequencyGrid, constants: V2Constants = DEFAULT,
    tolerance: float | None = None,
) -> list[dict[str, object]]:
    """The strongest `window_peak_pool` spectral-window peaks of `time` on the
    pass grid (recorded; the veto uses the first `n_window_peaks`). Peaks are
    separated by `tolerance` (1.5 / combined baseline T; the per-series
    baseline is used only when no tolerance is given)."""
    frequency, strength = window_strength_grid(time, grid, constants.window_subsample)
    if strength.size < 3:
        return []
    if tolerance is None:
        tolerance = constants.tolerance_over_baseline / float(np.ptp(time))
    distance = max(2, int(math.ceil(tolerance / (grid.step * constants.window_subsample))))
    indices, _ = find_peaks(strength, distance=distance)
    if indices.size == 0:
        return []
    order = np.argsort(-strength[indices], kind="stable")[: constants.window_peak_pool]
    return [
        {
            "label": f"window_rank{rank}",
            "frequency_per_day": float(frequency[indices[i]]),
            "strength": float(strength[indices[i]]),
            "source": "data",
        }
        for rank, i in enumerate(order, start=1)
    ]


def veto_loci(
    data_peaks: list[dict[str, object]], constants: V2Constants = DEFAULT
) -> list[dict[str, object]]:
    """Fixed loci + the first n_window_peaks data-driven peaks."""
    return fixed_loci() + list(data_peaks[: constants.n_window_peaks])


def is_window_alias_v2(
    time: np.ndarray,
    frequency: float,
    tolerance: float,
    loci: list[dict[str, object]],
    constants: V2Constants = DEFAULT,
) -> tuple[bool, float, str]:
    """(alias, local window power, locus label). Alias if the frozen local test
    fires (max window strength within +/- tolerance >= 0.1) OR the candidate is
    within `tolerance` of any listed locus."""
    offsets = np.linspace(-tolerance, tolerance, constants.window_local_samples)
    local = float(np.max(window_strength(time, frequency + offsets)))
    label = ""
    best = math.inf
    for locus in loci:
        distance = abs(frequency - float(locus["frequency_per_day"]))
        if distance <= tolerance and distance < best:
            best, label = distance, str(locus["label"])
    if not label and local >= WINDOW_POWER_THRESHOLD:
        label = "local_window_power"
    return bool(label), local, label


def is_alias_of_stronger_v2(
    frequency: float,
    stronger_frequencies: list[float],
    tolerance: float,
    spacings: tuple[float, ...] = ALIAS_SPACINGS,
) -> bool:
    """Alias of a stronger same-series peak f0 under the solar or sidereal
    comb: the difference family f = f0 +/- k * spacing (the frozen test, one
    spacing) AND the mirror family f = k * spacing - f0 (the 1 - delta /
    2 - delta wings, absent from the frozen test): a real-valued series has a
    symmetric spectral window, so power at f0 also appears at k * spacing - f0."""
    for stronger in stronger_frequencies:
        for combination in (abs(frequency - stronger), frequency + stronger):
            for spacing in spacings:
                nearest = round(combination / spacing) * spacing
                if nearest > 0 and abs(combination - nearest) <= tolerance:
                    return True
    return False


__all__ = [
    "ALIAS_SPACINGS", "fixed_loci", "is_alias_of_stronger_v2", "is_window_alias_v2",
    "veto_loci", "window_peaks", "window_strength_grid",
]
