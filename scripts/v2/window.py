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
               sidebands, m / 365.25 (m = 1, 2), and the month sidebands of
               the first two diurnal harmonics k * {1.0, 1.00274} +/- 1/month
               for the synodic (29.530589 d) and — Amendment 2026-09-04 — the
               sidereal (27.321661 d) month;
  comb rule  : (Amendment 2026-09-04) the month sidebands k * spacing +/-
               1/month for EVERY harmonic k >= 1 of both spacings and both
               months (the high pass sees the same comb at k = 24..1440),
               plus the bare sidereal lines k * 1.00274 for every k — the
               frozen pipeline's own family, which the pre-amendment list
               carried only for k = 1, 2 (bare solar lines beyond k = 3 are
               left to the data-driven peaks and the local test);
  diurnal    : (Amendment 2026-09-04) the closed band [k * 1.0 - 2/365.25,
               k * 1.00274 + 2/365.25] +/- tol for k = 1..3 (the yearly
               sideband comb is denser than 2 tol, so isolated loci leave
               unvetoed gaps inside it);
  data-driven: the top-N (N = 12) peaks of the band's own spectral window on
               the pass grid subsampled x10;
  local test : the frozen rule, kept verbatim.

The amendment was derived in closed form after inspecting the partial dev
run (V2_PLAN.md §10, 2026-09-04) and before any holdout star was scored: at
k = 1 the solar-minus-synodic and sidereal-minus-sidereal-month sidebands
coincide (0.96614 c/d), at k = 2 they split (1.96614 vs 1.96888 c/d) and the
pre-amendment list carried only the synodic one.

`is_alias_of_stronger` is generalised to the solar AND sidereal spacings and
to the mirror family k * spacing - f0 (the 1 - delta / 2 - delta wings: the
strongest D3 false-trigger locus, e.g. sidereal - lunar = 0.9688 c/d).
The fixed loci avoid the delta Sct (4-24 c/d) and DAV (40-1200 c/d) science
bands, but the data-driven loci, the local window test, the mirror family
and the cross-pass partners CAN veto real signals anywhere: the exposure of
the truth frequencies is measured (scripts/v2/analysis/veto_exposure.py) and
disclosed; true ~1 c/d rotators and ~29.5 d variables are sacrificed.
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
    SIDEREAL_MONTH_DAYS,
    SOLAR_FREQUENCY,
    WINDOW_POWER_THRESHOLD,
    YEAR_DAYS,
    FrequencyGrid,
    V2Constants,
    window_strength,
)

ALIAS_SPACINGS = (SOLAR_FREQUENCY, SIDEREAL_FREQUENCY)
COMB_SPACINGS = (("solar", SOLAR_FREQUENCY), ("sidereal", SIDEREAL_FREQUENCY))
MONTHS = (("lunar", LUNAR_SYNODIC_DAYS), ("sidmonth", SIDEREAL_MONTH_DAYS))
DIURNAL_BAND_HARMONICS = (1, 2, 3)


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
    for k in (1, 2):   # Amendment 2026-09-04: sidereal-month sidebands
        for spacing_label, spacing in COMB_SPACINGS:
            for sign in (-1, 1):
                loci.append({"label": f"{spacing_label}_k{k}_sidmonth{sign:+d}",
                             "frequency_per_day": k * spacing + sign / SIDEREAL_MONTH_DAYS})
    for m in (1, 2):
        loci.append({"label": f"yearly_m{m}", "frequency_per_day": m / YEAR_DAYS})
    for locus in loci:
        locus["source"] = "fixed"
        locus["strength"] = None
    return loci


def comb_sideband_label(frequency: float, tolerance: float) -> str:
    """Amendment 2026-09-04: the synodic-month and sidereal-month sidebands
    k * spacing +/- 1/month of every harmonic k >= 1 of the solar and the
    sidereal spacing, plus the bare sidereal lines k * 1.00274 (the frozen
    family, every k). Nearest match within `tolerance`, else ''."""
    best = math.inf
    label = ""
    for spacing_label, spacing in COMB_SPACINGS:
        centre = int(round(frequency / spacing))
        for k in (centre - 1, centre, centre + 1):
            if k < 1:
                continue
            offsets = [("m+0", 0.0)] if spacing_label == "sidereal" else []
            offsets += [
                (f"{month_label}{sign:+d}", sign / days) for month_label, days in MONTHS for sign in (-1, 1)
            ]
            for tag, offset in offsets:
                distance = abs(frequency - (k * spacing + offset))
                if distance <= tolerance and distance < best:
                    best, label = distance, f"comb_{spacing_label}_k{k}_{tag}"
    return label


def diurnal_band_label(frequency: float, tolerance: float) -> str:
    """Amendment 2026-09-04: the closed band between the outermost yearly
    sidebands of the solar and sidereal harmonics k = 1..3, widened by tol."""
    for k in DIURNAL_BAND_HARMONICS:
        low = k * SOLAR_FREQUENCY - 2.0 / YEAR_DAYS - tolerance
        high = k * SIDEREAL_FREQUENCY + 2.0 / YEAR_DAYS + tolerance
        if low <= frequency <= high:
            return f"diurnal_band_k{k}"
    return ""


def locus_label(frequency: float, tolerance: float, loci: list[dict[str, object]]) -> str:
    """The veto label of `frequency`: the nearest listed locus within
    `tolerance` (fixed and data-driven), else the comb-sideband rule, else the
    diurnal band; '' when none applies. Pure function of (frequency,
    tolerance, loci): the runner and the offline re-scorer share it."""
    label = ""
    best = math.inf
    for locus in loci:
        distance = abs(frequency - float(locus["frequency_per_day"]))
        if distance <= tolerance and distance < best:
            best, label = distance, str(locus["label"])
    if not label:
        label = comb_sideband_label(frequency, tolerance)
    if not label:
        label = diurnal_band_label(frequency, tolerance)
    return label


_FIXED_LOCI = fixed_loci()


def fixed_locus_label(frequency: float, tolerance: float) -> str:
    """`locus_label` against the fixed loci only (offline re-scoring and the
    veto-exposure audit; data-driven peaks are tested separately there)."""
    return locus_label(frequency, tolerance, _FIXED_LOCI)


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
    within `tolerance` of any listed locus, the comb-sideband rule or the
    diurnal band (`locus_label`)."""
    offsets = np.linspace(-tolerance, tolerance, constants.window_local_samples)
    local = float(np.max(window_strength(time, frequency + offsets)))
    label = locus_label(frequency, tolerance, loci)
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
    "ALIAS_SPACINGS", "COMB_SPACINGS", "DIURNAL_BAND_HARMONICS", "MONTHS", "comb_sideband_label",
    "diurnal_band_label", "fixed_loci", "fixed_locus_label", "is_alias_of_stronger_v2",
    "is_window_alias_v2", "locus_label", "veto_loci", "window_peaks", "window_strength_grid",
]
