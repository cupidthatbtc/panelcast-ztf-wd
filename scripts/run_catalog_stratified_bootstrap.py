#!/usr/bin/env python3
"""Run stratified, correlation-aware bootstrap checks across catalog detections."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.timeseries import LombScargle

from lomb_scargle_common import FAST_KWDS, exact_power_and_amplitude, prepare_series
from run_catalog_lomb_scargle import load_star

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PER_PEAK = 2


def select_strata(table: pd.DataFrame, per_stratum: int) -> pd.DataFrame:
    selected = []
    for status in ("confirmed", "candidate"):
        for pass_name in ("low", "high"):
            group = table[
                table["blind_status"].eq(status) & table["best_pass"].eq(pass_name)
            ].sort_values("best_band_fap")
            strong = group.head(per_stratum).copy()
            strong["selection_stratum"] = f"{status}_{pass_name}_strong"
            remaining = group[~group["source_id"].isin(strong["source_id"])]
            marginal = remaining.tail(per_stratum).copy()
            marginal["selection_stratum"] = f"{status}_{pass_name}_marginal"
            selected.extend([strong, marginal])
    result = pd.concat(selected, ignore_index=True)
    if result["source_id"].duplicated().any():
        raise ValueError("stratified bootstrap selection contains duplicate sources")
    return result


def bootstrap_indices(rng: np.random.Generator, size: int, block_length: int) -> np.ndarray:
    indices = []
    while len(indices) < size:
        start = int(rng.integers(0, size))
        indices.extend((start + np.arange(block_length)) % size)
    return np.asarray(indices[:size], dtype=int)


def bootstrap_maxima(
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    nights: np.ndarray,
    minimum: float,
    maximum: float,
    resamples: int,
    seed: int,
    high_frequency: bool,
    chunk_size: int = 500_000,
) -> tuple[np.ndarray, int]:
    baseline = float(np.ptp(time))
    step = 1.0 / (SAMPLES_PER_PEAK * baseline)
    size = int(math.floor((maximum - minimum) / step)) + 1
    rng = np.random.default_rng(seed)
    maxima = np.empty(resamples)
    block_length = max(2, int(round(math.sqrt(len(values)))))
    unique_nights = np.unique(nights)

    for replicate in range(resamples):
        if high_frequency:
            signs = dict(zip(unique_nights, rng.choice((-1.0, 1.0), len(unique_nights))))
            sample_values = values * np.asarray([signs[night] for night in nights])
            sample_errors = errors
        else:
            indices = bootstrap_indices(rng, len(values), block_length)
            sample_values = values[indices]
            sample_errors = errors[indices]
        model = LombScargle(
            time,
            sample_values,
            sample_errors,
            fit_mean=True,
            center_data=True,
        )
        peak = -np.inf
        for start in range(0, size, chunk_size):
            stop = min(start + chunk_size, size)
            frequency = minimum + step * np.arange(start, stop, dtype=float)
            power = model.power(
                frequency,
                method="fast",
                assume_regular_frequency=True,
                method_kwds=FAST_KWDS,
            )
            peak = max(peak, float(np.nanmax(power)))
        maxima[replicate] = peak
    return maxima, block_length


def bootstrap_one(
    job: dict[str, object],
    exposure_dir: str,
    output_dir: str,
    resamples: int,
) -> dict[str, object]:
    source_id = str(job["source_id"])
    output = Path(output_dir) / f"{source_id}.json"
    if output.exists():
        return json.loads(output.read_text(encoding="utf-8"))

    star = load_star(Path(exposure_dir) / f"{source_id}.csv.gz")
    band = "zg" if float(job["zg_fap"]) <= float(job["zr_fap"]) else "zr"
    frame = star[star["band"].eq(band)].sort_values("bjd_tdb")
    high = job["best_pass"] == "high"
    time, values, errors = prepare_series(frame, high_frequency=high)
    nights = frame["night_mjd"].to_numpy()
    frequency = float(job["best_frequency_per_day"])
    observed_power, _, _ = exact_power_and_amplitude(time, values, errors, frequency)
    minimum = 24.0 if high else 2.0 / np.ptp(time)
    maximum = 1440.0 if high else 48.0
    seed = (int(source_id[-9:]) + (991 if high else 313)) % (2**32)
    maxima, block_length = bootstrap_maxima(
        time,
        values,
        errors,
        nights,
        minimum,
        maximum,
        resamples,
        seed,
        high,
    )
    exceedances = int(np.sum(maxima >= observed_power))
    result = {
        "source_id": source_id,
        "selection_stratum": job["selection_stratum"],
        "blind_status": job["blind_status"],
        "pass": job["best_pass"],
        "band": band,
        "frequency_per_day": frequency,
        "observed_power": observed_power,
        "bootstrap_fap": (exceedances + 1.0) / (resamples + 1.0),
        "bootstrap_exceedances": exceedances,
        "bootstrap_resamples": resamples,
        "bootstrap_resolution": 1.0 / (resamples + 1.0),
        "resampling_scheme": "night_wild_sign" if high else "moving_observation_block",
        "block_length": None if high else block_length,
        "grid_samples_per_peak": SAMPLES_PER_PEAK,
        "trials_context": f"maximum over {minimum:.8g}..{maximum:g} d^-1",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.part")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    parser.add_argument("--per-stratum", type=int, default=5)
    parser.add_argument("--resamples", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    table = pd.read_csv(args.run_dir / "ls_full_catalog.csv", dtype={"source_id": str})
    jobs = select_strata(table, args.per_stratum)
    output_dir = args.run_dir / "hardening/stratified_bootstrap"
    output_dir.mkdir(parents=True, exist_ok=True)
    jobs.to_csv(output_dir / "selection.csv", index=False)

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                bootstrap_one,
                row._asdict(),
                str(args.run_dir / "exposure_stars"),
                str(output_dir / "stars"),
                args.resamples,
            ): row.source_id
            for row in jobs.itertuples(index=False)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                f"[stratified-bootstrap] {len(results):02d}/{len(jobs):02d} "
                f"{result['source_id']} {result['selection_stratum']} "
                f"fap={result['bootstrap_fap']:.4f}",
                flush=True,
            )

    results_frame = pd.DataFrame(results).sort_values(
        ["selection_stratum", "bootstrap_fap", "source_id"]
    )
    results_frame.to_csv(output_dir / "results.csv", index=False)
    summary = (
        results_frame.groupby("selection_stratum", as_index=False)
        .agg(
            sources=("source_id", "size"),
            median_bootstrap_fap=("bootstrap_fap", "median"),
            fap_le_0p01=("bootstrap_fap", lambda values: int((values <= 0.01).sum())),
            fap_le_0p05=("bootstrap_fap", lambda values: int((values <= 0.05).sum())),
        )
        .sort_values("selection_stratum")
    )
    summary.to_csv(output_dir / "summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
