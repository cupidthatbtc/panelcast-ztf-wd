#!/usr/bin/env python3
"""Recover a known 8-minute sinusoid from a quiet ZTF sampling pattern."""

import argparse
import json
from pathlib import Path

import numpy as np

from lomb_scargle_common import (
    FrequencyGrid,
    baluev_fap,
    exact_power_and_amplitude,
    extract_peaks,
    load_exposures,
    periodogram_to_memmap,
    prepare_series,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "114808397128552576"
PERIOD_DAYS = 8.0 / (24.0 * 60.0)
AMPLITUDE_MAG = 0.030


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/ls/smoke_test.json")
    args = parser.parse_args()

    exposures = load_exposures(args.exposures)
    sample = exposures[
        (exposures["source_id"] == SOURCE_ID) & (exposures["band"] == "zg")
    ].copy()
    phase_time = sample["bjd_tdb"].to_numpy(dtype=float)
    phase_time -= phase_time.min()
    sample["mag"] += AMPLITUDE_MAG * np.sin(2 * np.pi * phase_time / PERIOD_DAYS + 0.37)
    time, injected_residual, error = prepare_series(sample, high_frequency=True)
    grid = FrequencyGrid.create(24.0, 1440.0, np.ptp(time))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.out.with_suffix(".power.dat")
    periodogram = periodogram_to_memmap(time, injected_residual, error, grid, scratch)
    peaks, _ = extract_peaks(periodogram, grid, count=5)
    best_frequency = grid.minimum + grid.step * peaks[0][1]
    power, amplitude, amplitude_error = exact_power_and_amplitude(
        time, injected_residual, error, best_frequency
    )
    fap = baluev_fap(time, injected_residual, error, power, grid)
    recovered_period = 1.0 / best_frequency
    period_error = abs(recovered_period - PERIOD_DAYS)

    result = {
        "source_id": SOURCE_ID,
        "band": "zg",
        "n_exp": len(time),
        "injected_period_minutes": 8.0,
        "injected_amplitude_mmag": 30.0,
        "grid_size": grid.size,
        "grid_step_cycles_per_day": grid.step,
        "recovered_frequency_cycles_per_day": best_frequency,
        "recovered_period_minutes": recovered_period * 24.0 * 60.0,
        "period_error_seconds": period_error * 86400.0,
        "power": power,
        "baluev_fap_blind_grid": fap,
        "measured_amplitude_mmag": amplitude * 1000.0,
        "amplitude_error_mmag": amplitude_error * 1000.0,
        "passed": period_error <= grid.step / best_frequency**2 and fap < 1e-6,
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    del periodogram
    scratch.unlink(missing_ok=True)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit("smoke test failed")


if __name__ == "__main__":
    main()
