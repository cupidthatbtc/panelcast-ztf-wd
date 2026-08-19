#!/usr/bin/env python3
"""Bootstrap the blind-grid FAP for each star's strongest surviving candidate."""

import argparse
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.timeseries import LombScargle

from lomb_scargle_common import FAST_KWDS, exact_power_and_amplitude, load_exposures, prepare_series

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SAMPLES_PER_PEAK = 2


def bootstrap_maximum(
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    minimum_frequency: float,
    maximum_frequency: float,
    resamples: int,
    seed: int,
    chunk_size: int = 500_000,
) -> np.ndarray:
    baseline = float(np.ptp(time))
    step = 1.0 / (BOOTSTRAP_SAMPLES_PER_PEAK * baseline)
    size = int(math.floor((maximum_frequency - minimum_frequency) / step)) + 1
    rng = np.random.default_rng(seed)
    maxima = np.empty(resamples)
    for replicate in range(resamples):
        sample = rng.integers(0, len(values), len(values))
        model = LombScargle(
            time,
            values[sample],
            errors[sample],
            fit_mean=True,
            center_data=True,
        )
        peak = -np.inf
        for start in range(0, size, chunk_size):
            stop = min(start + chunk_size, size)
            frequency = minimum_frequency + step * np.arange(start, stop, dtype=float)
            power = model.power(
                frequency,
                method="fast",
                assume_regular_frequency=True,
                method_kwds=FAST_KWDS,
            )
            peak = max(peak, float(np.nanmax(power)))
        maxima[replicate] = peak
    return maxima


def bootstrap_one(
    source_id: str,
    pass_name: str,
    frequency: float,
    band: str,
    exposures_path: str,
    resamples: int,
) -> dict[str, object]:
    exposures = load_exposures(Path(exposures_path))
    frame = exposures[
        (exposures["source_id"] == source_id) & (exposures["band"] == band)
    ]
    time, values, errors = prepare_series(frame, high_frequency=pass_name == "high")
    power, _, _ = exact_power_and_amplitude(time, values, errors, frequency)
    minimum_frequency = 2.0 / np.ptp(time) if pass_name == "low" else 24.0
    maximum_frequency = 48.0 if pass_name == "low" else 1440.0
    seed = (int(source_id[-9:]) + (1 if pass_name == "high" else 0)) % (2**32)
    maxima = bootstrap_maximum(
        time,
        values,
        errors,
        minimum_frequency,
        maximum_frequency,
        resamples,
        seed,
    )
    exceedances = int(np.sum(maxima >= power))
    fap = (exceedances + 1.0) / (resamples + 1.0)
    return {
        "source_id": source_id,
        "pass": pass_name,
        "band": band,
        "frequency_per_day": frequency,
        "power": power,
        "bootstrap_fap": fap,
        "bootstrap_exceedances": exceedances,
        "bootstrap_resamples": resamples,
        "bootstrap_resolution": 1.0 / (resamples + 1.0),
        "bootstrap_grid_samples_per_peak": BOOTSTRAP_SAMPLES_PER_PEAK,
        "trials_context": f"bootstrap maximum over {minimum_frequency:.8g}..{maximum_frequency:g} d^-1",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--resamples", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    candidates = pd.read_csv(args.run_dir / "candidates.csv", dtype={"source_id": str})
    surviving = candidates[candidates["status"].isin(["confirmed", "candidate"])].copy()
    if surviving.empty:
        raise ValueError("no surviving candidates to bootstrap")
    surviving["priority"] = surviving["status"].map({"confirmed": 0, "candidate": 1})
    best = (
        surviving.sort_values(["source_id", "priority", "best_band_fap"])
        .groupby("source_id", as_index=False)
        .first()
    )
    jobs = []
    for _, row in best.iterrows():
        band = "zg" if row["zg_fap"] <= row["zr_fap"] else "zr"
        jobs.append((row["source_id"], row["pass"], row["frequency_per_day"], band))

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                bootstrap_one,
                *job,
                str(args.exposures),
                args.resamples,
            ): job[0]
            for job in jobs
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"bootstrapped {result['source_id']} ({result['pass']})", flush=True)

    pd.DataFrame(results).sort_values("source_id").to_csv(
        args.run_dir / "bootstrap_fap.csv", index=False
    )
    print(f"wrote bootstrap FAPs for {len(results)} surviving candidates")


if __name__ == "__main__":
    main()
