from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from astropy.timeseries import LombScargleMultiband

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))

from analyze_star_v2 import analyze_star_v2  # noqa: E402
from detrend import prepare_series_v2  # noqa: E402
from lomb_scargle_common import (  # noqa: E402
    FrequencyGrid,
    baluev_fap,
    exact_power_and_amplitude,
    periodogram_to_memmap,
)
from multiband import (  # noqa: E402
    cluster_candidates,
    is_coherent,
    joint_fit,
    sinusoid_fit,
    wrapped_phase_difference_cycles,
)
from run_lomb_scargle import (  # noqa: E402
    cluster_candidate_frequencies,
    multiband_power,
)
from v2_common import grid_for  # noqa: E402


def test_sinusoid_fit_recovers_amplitude_and_phase():
    time = np.linspace(0.0, 40.0, 401)
    frequency = 3.71
    amplitude = 0.017
    phase_cycles = 0.23
    values = 15.2 + amplitude * np.sin(
        2.0 * np.pi * (frequency * time + phase_cycles)
    )

    fit = sinusoid_fit(time, values, np.full_like(time, 0.003), frequency)

    assert fit["mean"] == pytest.approx(15.2, abs=1e-12)
    assert fit["amplitude"] == pytest.approx(amplitude, abs=1e-12)
    assert fit["phase_cycles"] == pytest.approx(phase_cycles, abs=1e-12)


def test_wrapped_phase_difference_crosses_cycle_boundary():
    assert wrapped_phase_difference_cycles(0.45, -0.45) == pytest.approx(0.1)


def _two_band_series(
    phase_g: float = 0.11,
    phase_r: float = 0.11,
    ratio: float = 0.8,
    noise: float = 0.002,
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(441)
    frequency = 4.37
    time_g = np.sort(rng.uniform(0.0, 100.0, size=180))
    time_r = np.sort(rng.uniform(0.0, 100.0, size=170))
    error_level = noise if noise else 1e-4   # weights need finite, positive errors
    error_g = np.full_like(time_g, error_level)
    error_r = np.full_like(time_r, error_level)
    value_g = 0.030 * np.sin(2.0 * np.pi * (frequency * time_g + phase_g))
    value_r = 0.030 * ratio * np.sin(2.0 * np.pi * (frequency * time_r + phase_r))
    if noise:
        value_g += rng.normal(0.0, noise, size=time_g.size)
        value_r += rng.normal(0.0, noise, size=time_r.size)
    return {"zg": (time_g, value_g, error_g), "zr": (time_r, value_r, error_r)}


def test_joint_fit_accepts_coherent_two_band_signal():
    fit = joint_fit(_two_band_series(), 4.37)

    assert fit["delta_phase_cycles"] < 0.05
    assert fit["amp_ratio_r_over_g"] == pytest.approx(0.8, abs=0.05)
    assert is_coherent(fit) is True


def test_joint_fit_rejects_quadrature_signal():
    fit = joint_fit(_two_band_series(phase_g=0.0, phase_r=0.25, noise=0.0), 4.37)

    assert fit["delta_phase_cycles"] == pytest.approx(0.25, abs=1e-10)
    assert is_coherent(fit) is False


def test_joint_fit_rejects_extreme_amplitude_ratio():
    fit = joint_fit(_two_band_series(ratio=0.1, noise=0.0), 4.37)

    assert fit["amp_ratio_r_over_g"] == pytest.approx(0.1, abs=1e-10)
    assert is_coherent(fit) is False


def test_frozen_multiband_memmap_matches_astropy_fast_method(tmp_path):
    rng = np.random.default_rng(772)
    time_g = np.sort(rng.uniform(0.0, 30.0, 90))
    time_r = np.sort(rng.uniform(0.0, 30.0, 85))
    error_g = np.full_like(time_g, 0.01)
    error_r = np.full_like(time_r, 0.012)
    value_g = 0.02 * np.sin(2.0 * np.pi * 2.3 * time_g) + rng.normal(0.0, 0.01, time_g.size)
    value_r = 0.015 * np.sin(2.0 * np.pi * 2.3 * time_r + 0.2) + rng.normal(0.0, 0.012, time_r.size)
    grid = FrequencyGrid.create(0.1, 5.0, baseline=30.0)
    frequency = grid.values()

    power_g = periodogram_to_memmap(time_g, value_g, error_g, grid, tmp_path / "zg.dat")
    power_r = periodogram_to_memmap(time_r, value_r, error_r, grid, tmp_path / "zr.dat")
    joint, _ = multiband_power(power_g, power_r, tmp_path / "joint.dat")
    try:
        time = np.concatenate([time_g, time_r])
        values = np.concatenate([value_g, value_r])
        errors = np.concatenate([error_g, error_r])
        bands = np.array(["zg"] * time_g.size + ["zr"] * time_r.size)
        model = LombScargleMultiband(time, values, bands, errors)
        kwargs = {"method": "fast", "sb_method": "fast"}
        # Astropy 8 validates regular spacing internally but its public method
        # no longer exposes the older assume_regular_frequency keyword.
        if "assume_regular_frequency" in inspect.signature(model.power).parameters:
            kwargs["assume_regular_frequency"] = True
        expected = model.power(frequency, **kwargs)
        np.testing.assert_allclose(np.asarray(joint), expected, rtol=0.0, atol=1e-4)
    finally:
        for mmap in (joint, power_g, power_r):
            mmap.flush()
            mmap._mmap.close()


def test_cluster_candidates_orders_by_power_only_and_honours_cap():
    """v2 clusters by (-power, frequency) ONLY, so the candidate set does not
    depend on the tunable veto constants (the frozen order puts aliased peaks
    last; with no aliased rows the two orders agree)."""
    rows = [
        {"frequency_per_day": 5.0, "power": 0.20, "alias_flag": False},
        {"frequency_per_day": 1.0, "power": 0.80, "alias_flag": False},
        {"frequency_per_day": 1.01, "power": 0.70, "alias_flag": False},
        {"frequency_per_day": 3.0, "power": 0.99, "alias_flag": True},
        {"frequency_per_day": 2.0, "power": 0.10, "alias_flag": False},
    ]
    assert cluster_candidates(rows, tolerance=0.02, max_candidates=30) == [3.0, 1.0, 5.0, 2.0]
    assert cluster_candidates(rows, tolerance=0.02, max_candidates=2) == [3.0, 1.0]
    flipped = [dict(row, alias_flag=not row["alias_flag"]) for row in rows]
    assert cluster_candidates(flipped, tolerance=0.02, max_candidates=30) == [3.0, 1.0, 5.0, 2.0]
    unaliased = [dict(row, alias_flag=False) for row in rows]
    assert cluster_candidates(unaliased, tolerance=0.02, max_candidates=30) == \
        cluster_candidate_frequencies(unaliased, tolerance=0.02)


def _marginal_signal_shard(path: Path) -> tuple[pd.DataFrame, float]:
    rng = np.random.default_rng(1803)
    frequency = 8.37
    rows = []
    for band, phase in (("zg", 0.17), ("zr", 0.17)):
        nights = np.sort(rng.choice(np.arange(121), size=105, replace=False))
        time = nights + rng.uniform(0.04, 0.31, size=nights.size)
        noise = rng.normal(0.0, 0.010, size=time.size)
        mag = 15.0 + 0.0070 * np.sin(2.0 * np.pi * (frequency * time + phase)) + noise
        for i, epoch in enumerate(time):
            rows.append(
                {
                    "source_id": "marginal",
                    "band": band,
                    "oid": "1",
                    "mjd": 60_000.0 + epoch,
                    "bjd_tdb": 2_460_000.0 + epoch,
                    "night_mjd": int(np.floor(epoch)),
                    "mag": mag[i],
                    "magerr": 0.010,
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False, compression="gzip")
    return frame, frequency


def test_marginal_per_band_signal_is_promoted_into_joint_top_five(tmp_path):
    shard = tmp_path / "marginal.csv.gz"
    frame, frequency = _marginal_signal_shard(shard)
    origin = float(frame["bjd_tdb"].min())
    baseline = float(frame["bjd_tdb"].max() - origin)
    grid = grid_for("low", baseline)
    faps = []
    for band in ("zg", "zr"):
        series = prepare_series_v2(frame[frame["band"] == band], False, origin)
        power, _, _ = exact_power_and_amplitude(*series, frequency)
        faps.append(baluev_fap(*series, power, grid))
    # Fixed SNR A/sigma = 0.70: each band ALONE fails the 1e-3 threshold (FAPs ~1e-2),
    # so only the joint finder can list the frequency.
    assert all(1e-3 < fap <= 0.2 for fap in faps), faps

    result = analyze_star_v2(
        "marginal",
        str(shard),
        str(tmp_path / "marginal.json"),
        str(tmp_path / "work"),
        ("low",),
    )
    joint_top_five = result["passes"]["low"]["v2"]["series_peaks"]["multiband"][:5]

    tolerance = 1.5 / baseline
    assert any(
        abs(float(row["frequency_per_day"]) - frequency) <= tolerance
        for row in joint_top_five
    )
