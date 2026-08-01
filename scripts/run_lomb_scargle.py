#!/usr/bin/env python3
"""Run blind low- and high-frequency Lomb–Scargle searches for the ZTF roster."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.timeseries import BoxLeastSquares
from scipy.signal import find_peaks

from lomb_scargle_common import (
    FrequencyGrid,
    approximate_peak_amplitude,
    baluev_fap,
    decimate_periodogram,
    exact_power_and_amplitude,
    extract_peaks,
    is_alias_of_stronger,
    is_window_alias,
    load_exposures,
    periodogram_to_memmap,
    prepare_series,
)

ROOT = Path(__file__).resolve().parents[1]
CONTROL_IDS = ("3345661467822106624", "4318508939464901760")
TRANSIT_ID = "103999471976858496"
PASS_BOUNDS = {"low": (None, 48.0), "high": (24.0, 1440.0)}


def parse_flag(value):
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def json_ready(value):
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def grid_for(pass_name: str, baseline: float) -> FrequencyGrid:
    minimum, maximum = PASS_BOUNDS[pass_name]
    return FrequencyGrid.create(2.0 / baseline if minimum is None else minimum, maximum, baseline)


def peak_rows_for_band(
    source_id: str,
    pass_name: str,
    band: str,
    power: np.ndarray,
    grid: FrequencyGrid,
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
) -> tuple[list[dict[str, object]], np.ndarray, float]:
    peaks, noise_indices = extract_peaks(power, grid, count=20)
    tolerance = 1.5 / np.ptp(time)
    rows: list[dict[str, object]] = []
    stronger: list[float] = []
    for rank, (_, index) in enumerate(peaks[:5], start=1):
        frequency = grid.minimum + grid.step * index
        exact_power, amplitude, amplitude_error = exact_power_and_amplitude(
            time, values, errors, frequency
        )
        fap = baluev_fap(time, values, errors, exact_power, grid)
        window_alias, window_power = is_window_alias(time, frequency, tolerance)
        stronger_alias = is_alias_of_stronger(frequency, stronger, tolerance)
        rows.append(
            {
                "source_id": source_id,
                "pass": pass_name,
                "series": band,
                "rank": rank,
                "frequency_per_day": frequency,
                "period_days": 1.0 / frequency,
                "period_seconds": 86400.0 / frequency,
                "power": exact_power,
                "baluev_fap_blind_grid": fap,
                "amplitude_mmag": amplitude * 1000.0,
                "amplitude_error_mmag": amplitude_error * 1000.0,
                "window_power": window_power,
                "window_alias": window_alias,
                "stronger_peak_sidereal_alias": stronger_alias,
                "alias_flag": window_alias or stronger_alias,
            }
        )
        stronger.append(frequency)

    if noise_indices.size:
        noise_power = np.asarray(power[noise_indices], dtype=float)
        p95 = float(np.quantile(noise_power, 0.95))
        a95 = approximate_peak_amplitude(time, values, errors, p95) * 1000.0
    else:
        a95 = math.nan
    return rows, noise_indices, a95


def multiband_power(
    zg: np.memmap,
    zr: np.memmap,
    out_path: Path,
    chunk_size: int = 500_000,
) -> tuple[np.memmap, tuple[float, float]]:
    sums = []
    for power in (zg, zr):
        total = 0.0
        for start in range(0, power.size, chunk_size):
            chunk = np.asarray(power[start : start + chunk_size], dtype=float)
            total += float(np.dot(chunk, chunk))
        sums.append(total)
    total = sums[0] + sums[1]
    weights = (sums[0] / total, sums[1] / total)

    combined = np.memmap(out_path, dtype="float32", mode="w+", shape=zg.shape)
    for start in range(0, zg.size, chunk_size):
        stop = min(start + chunk_size, zg.size)
        combined[start:stop] = weights[0] * zg[start:stop] + weights[1] * zr[start:stop]
    combined.flush()
    return combined, weights


def peak_rows_multiband(
    source_id: str,
    pass_name: str,
    power: np.ndarray,
    grid: FrequencyGrid,
    combined_time: np.ndarray,
) -> list[dict[str, object]]:
    peaks, _ = extract_peaks(power, grid, count=20)
    tolerance = 1.5 / np.ptp(combined_time)
    rows: list[dict[str, object]] = []
    stronger: list[float] = []
    for rank, (peak_power, index) in enumerate(peaks[:5], start=1):
        frequency = grid.minimum + grid.step * index
        window_alias, window_power = is_window_alias(combined_time, frequency, tolerance)
        stronger_alias = is_alias_of_stronger(frequency, stronger, tolerance)
        rows.append(
            {
                "source_id": source_id,
                "pass": pass_name,
                "series": "multiband",
                "rank": rank,
                "frequency_per_day": frequency,
                "period_days": 1.0 / frequency,
                "period_seconds": 86400.0 / frequency,
                "power": float(peak_power),
                "baluev_fap_blind_grid": math.nan,
                "amplitude_mmag": math.nan,
                "amplitude_error_mmag": math.nan,
                "window_power": window_power,
                "window_alias": window_alias,
                "stronger_peak_sidereal_alias": stronger_alias,
                "alias_flag": window_alias or stronger_alias,
            }
        )
        stronger.append(frequency)
    return rows


def cluster_candidate_frequencies(peak_rows: list[dict[str, object]], tolerance: float) -> list[float]:
    ordered = sorted(peak_rows, key=lambda row: (bool(row["alias_flag"]), -float(row["power"])))
    frequencies: list[float] = []
    for row in ordered:
        frequency = float(row["frequency_per_day"])
        if all(abs(frequency - existing) > tolerance for existing in frequencies):
            frequencies.append(frequency)
    return frequencies


def evaluate_candidates(
    source_id: str,
    pass_name: str,
    peak_rows: list[dict[str, object]],
    grid: FrequencyGrid,
    series: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]],
) -> list[dict[str, object]]:
    combined_time = np.concatenate([series["zg"][0], series["zr"][0]])
    tolerance = 1.5 / np.ptp(combined_time)
    frequencies = cluster_candidate_frequencies(peak_rows, tolerance)
    multiband_frequencies = [
        float(row["frequency_per_day"])
        for row in peak_rows
        if row["series"] == "multiband" and not row["alias_flag"]
    ]

    candidates: list[dict[str, object]] = []
    for frequency in frequencies:
        row: dict[str, object] = {
            "source_id": source_id,
            "pass": pass_name,
            "frequency_per_day": frequency,
            "period_days": 1.0 / frequency,
            "period_seconds": 86400.0 / frequency,
        }
        unaliased_significant: list[str] = []
        for band in ("zg", "zr"):
            time, values, errors = series[band]
            power, amplitude, amplitude_error = exact_power_and_amplitude(
                time, values, errors, frequency
            )
            fap = baluev_fap(time, values, errors, power, grid)
            tolerance_band = 1.5 / np.ptp(time)
            window_alias, window_power = is_window_alias(time, frequency, tolerance_band)
            stronger_frequencies = [
                float(peak["frequency_per_day"])
                for peak in peak_rows
                if peak["series"] == band and float(peak["power"]) > power
            ]
            stronger_alias = is_alias_of_stronger(
                frequency, stronger_frequencies, tolerance_band
            )
            alias = window_alias or stronger_alias
            row[f"{band}_power"] = power
            row[f"{band}_fap"] = fap
            row[f"{band}_amplitude_mmag"] = amplitude * 1000.0
            row[f"{band}_amplitude_error_mmag"] = amplitude_error * 1000.0
            row[f"{band}_window_power"] = window_power
            row[f"{band}_alias"] = alias
            if fap < 1e-3 and not alias:
                unaliased_significant.append(band)

        in_multiband = any(abs(frequency - value) <= tolerance for value in multiband_frequencies)
        if len(unaliased_significant) == 2:
            status = "confirmed"
            basis = "zg+zr"
        elif len(unaliased_significant) >= 1 and in_multiband:
            status = "confirmed"
            basis = f"multiband+{unaliased_significant[0]}"
        elif len(unaliased_significant) == 1:
            status = "candidate"
            basis = unaliased_significant[0]
        else:
            status = "not_detected"
            basis = ""
        row["multiband_top5"] = in_multiband
        row["status"] = status
        row["basis"] = basis
        row["best_band_fap"] = min(float(row["zg_fap"]), float(row["zr_fap"]))
        candidates.append(row)

    order = {"confirmed": 0, "candidate": 1, "not_detected": 2}
    candidates.sort(key=lambda row: (order[str(row["status"])], float(row["best_band_fap"])))
    return candidates


def write_periodogram_plot_data(
    path: Path,
    grid: FrequencyGrid,
    powers: dict[str, np.ndarray],
    peak_rows: list[dict[str, object]],
) -> None:
    frames = []
    for series_name, power in powers.items():
        frequency, sampled_power = decimate_periodogram(power, grid)
        frame = pd.DataFrame(
            {"frequency_per_day": frequency, "power": sampled_power, "series": series_name}
        )
        exact = pd.DataFrame(
            [
                {
                    "frequency_per_day": row["frequency_per_day"],
                    "power": row["power"],
                    "series": series_name,
                }
                for row in peak_rows
                if row["series"] == series_name
            ]
        )
        frames.extend([frame, exact])
    pd.concat(frames, ignore_index=True).sort_values(["series", "frequency_per_day"]).to_csv(
        path, index=False
    )


def run_bls(star: pd.DataFrame, out_path: Path) -> dict[str, object]:
    pieces = []
    for band, frame in star.groupby("band"):
        median_mag = float(frame["mag"].median())
        flux = np.power(10.0, -0.4 * (frame["mag"].to_numpy(dtype=float) - median_mag))
        flux_error = 0.4 * np.log(10.0) * flux * frame["magerr"].to_numpy(dtype=float)
        pieces.append(
            pd.DataFrame(
                {"time": frame["bjd_tdb"].to_numpy(dtype=float), "flux": flux, "error": flux_error}
            )
        )
    combined = pd.concat(pieces).sort_values("time")
    time = combined["time"].to_numpy(dtype=float)
    time -= time.min()
    model = BoxLeastSquares(time, combined["flux"].to_numpy(), dy=combined["error"].to_numpy())
    durations = np.array([2, 5, 10, 20], dtype=float) / 1440.0
    coarse_periods = np.geomspace(1.0 / 24.0, 30.0, 200_000)
    coarse = model.power(coarse_periods, durations, method="fast", oversample=5)
    coarse_peaks, _ = find_peaks(coarse.power, distance=5)
    if coarse_peaks.size:
        keep = min(20, len(coarse_peaks))
        top = coarse_peaks[np.argpartition(coarse.power[coarse_peaks], -keep)[-keep:]]
    else:
        top = np.array([int(np.argmax(coarse.power))])
    log_step = math.log(30.0 * 24.0) / (len(coarse_periods) - 1)

    refinements = []
    for index in top:
        center = float(coarse.period[index])
        periods = np.geomspace(center * math.exp(-5 * log_step), center * math.exp(5 * log_step), 2001)
        refinements.append(model.power(periods, durations, method="fast", oversample=5))
    result = max(refinements, key=lambda item: float(np.max(item.power)))
    index = int(np.argmax(result.power))
    summary = {
        "source_id": TRANSIT_ID,
        "period_days": float(result.period[index]),
        "duration_minutes": float(result.duration[index] * 1440.0),
        "transit_time_bjd_offset": float(result.transit_time[index]),
        "depth": float(result.depth[index]),
        "depth_snr": float(result.depth_snr[index]),
        "power": float(result.power[index]),
        "coarse_grid_size": len(coarse.period),
        "refined_candidates": len(refinements),
        "refined_grid_size_each": len(result.period),
    }
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def analyze_star(
    source_id: str,
    exposures_path: str,
    output_dir: str,
    passes: tuple[str, ...],
    keep_power: bool = False,
) -> dict[str, object]:
    exposures = load_exposures(Path(exposures_path))
    star = exposures[exposures["source_id"] == source_id].copy()
    if set(star["band"]) != {"zg", "zr"}:
        raise ValueError(f"{source_id} does not have both zg and zr exposures")

    star_dir = Path(output_dir) / "stars" / source_id
    star_dir.mkdir(parents=True, exist_ok=True)
    combined_baseline = float(star["bjd_tdb"].max() - star["bjd_tdb"].min())
    all_peaks: list[dict[str, object]] = []
    all_candidates: list[dict[str, object]] = []
    upper_limits: list[dict[str, object]] = []
    pass_summaries: dict[str, dict[str, object]] = {}

    for pass_name in passes:
        high = pass_name == "high"
        grid = grid_for(pass_name, combined_baseline)
        series = {
            band: prepare_series(star[star["band"] == band], high_frequency=high)
            for band in ("zg", "zr")
        }
        power_paths = {
            band: star_dir / f".{pass_name}_{band}.power.dat" for band in ("zg", "zr")
        }
        powers = {
            band: periodogram_to_memmap(*series[band], grid, power_paths[band])
            for band in ("zg", "zr")
        }
        multiband_path = star_dir / f".{pass_name}_multiband.power.dat"
        powers["multiband"], mb_weights = multiband_power(
            powers["zg"], powers["zr"], multiband_path
        )

        peak_rows: list[dict[str, object]] = []
        for band in ("zg", "zr"):
            rows, _, a95 = peak_rows_for_band(
                source_id, pass_name, band, powers[band], grid, *series[band]
            )
            peak_rows.extend(rows)
            upper_limits.append(
                {
                    "source_id": source_id,
                    "pass": pass_name,
                    "band": band,
                    "n_exp": len(series[band][0]),
                    "a95_mmag": a95,
                }
            )
        combined_time = star["bjd_tdb"].to_numpy(dtype=float)
        combined_time -= combined_time.min()
        peak_rows.extend(
            peak_rows_multiband(
                source_id, pass_name, powers["multiband"], grid, combined_time
            )
        )
        candidates = evaluate_candidates(source_id, pass_name, peak_rows, grid, series)
        write_periodogram_plot_data(
            star_dir / f"periodogram_{pass_name}.csv", grid, powers, peak_rows
        )
        pd.DataFrame(peak_rows).to_csv(star_dir / f"peaks_{pass_name}.csv", index=False)
        pd.DataFrame(candidates).to_csv(star_dir / f"candidates_{pass_name}.csv", index=False)

        best = candidates[0]
        pass_summaries[pass_name] = {
            "status": best["status"],
            "basis": best["basis"],
            "frequency_per_day": best["frequency_per_day"],
            "period_days": best["period_days"],
            "period_seconds": best["period_seconds"],
            "best_band_fap": best["best_band_fap"],
            "zg_amplitude_mmag": best["zg_amplitude_mmag"],
            "zr_amplitude_mmag": best["zr_amplitude_mmag"],
            "grid_size": grid.size,
            "grid_step_per_day": grid.step,
            "multiband_zg_weight": mb_weights[0],
            "multiband_zr_weight": mb_weights[1],
        }
        all_peaks.extend(peak_rows)
        all_candidates.extend(candidates)

        for power in powers.values():
            power.flush()
            power._mmap.close()
        powers.clear()
        if not keep_power:
            for path in (*power_paths.values(), multiband_path):
                path.unlink(missing_ok=True)

    bls = run_bls(star, star_dir / "bls.json") if source_id == TRANSIT_ID else None
    summary = {
        "source_id": source_id,
        "wdj_name": str(star["wdj_name"].iloc[0]) if pd.notna(star["wdj_name"].iloc[0]) else "",
        "wd_class": str(star["wd_class"].iloc[0]),
        "paper_variable": parse_flag(star["paper_variable"].iloc[0]),
        "paper_periodic": parse_flag(star["paper_periodic"].iloc[0]),
        "passes": pass_summaries,
        "bls": bls,
    }
    (star_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=json_ready) + "\n", encoding="utf-8"
    )
    pd.DataFrame(upper_limits).to_csv(star_dir / "upper_limits.csv", index=False)
    return summary


def verify_controls(summaries: list[dict[str, object]]) -> None:
    by_id = {str(summary["source_id"]): summary for summary in summaries}
    rr = by_id[CONTROL_IDS[0]]["passes"]["low"]
    double = by_id[CONTROL_IDS[1]]["passes"]["low"]
    rr_period = float(rr["period_days"])
    failures = []
    if rr["status"] != "confirmed" or not 0.2 <= rr_period <= 1.0:
        failures.append(f"RR Lyrae control: {rr}")
    if double["status"] != "confirmed" or double["basis"] != "zg+zr":
        failures.append(f"double-band control: {double}")
    if failures:
        raise RuntimeError("positive controls failed; stopping before full search\n" + "\n".join(failures))


def collect_outputs(run_dir: Path, source_ids: list[str]) -> None:
    tables = {"peaks": [], "candidates": [], "upper_limits": []}
    summaries = []
    for source_id in source_ids:
        star_dir = run_dir / "stars" / source_id
        summaries.append(json.loads((star_dir / "summary.json").read_text(encoding="utf-8")))
        for pass_name in PASS_BOUNDS:
            peak_path = star_dir / f"peaks_{pass_name}.csv"
            candidate_path = star_dir / f"candidates_{pass_name}.csv"
            if peak_path.exists():
                tables["peaks"].append(pd.read_csv(peak_path, dtype={"source_id": str}))
            if candidate_path.exists():
                tables["candidates"].append(pd.read_csv(candidate_path, dtype={"source_id": str}))
        tables["upper_limits"].append(pd.read_csv(star_dir / "upper_limits.csv", dtype={"source_id": str}))

    for name, frames in tables.items():
        pd.concat(frames, ignore_index=True).to_csv(run_dir / f"{name}.csv", index=False)
    (run_dir / "summaries.json").write_text(
        json.dumps(summaries, indent=2, default=json_ready) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--stars", nargs="*")
    parser.add_argument("--passes", nargs="+", choices=tuple(PASS_BOUNDS), default=tuple(PASS_BOUNDS))
    parser.add_argument("--skip-controls", action="store_true")
    parser.add_argument("--keep-power", action="store_true")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = args.out_dir or ROOT / "outputs/ls" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    exposures = load_exposures(args.exposures)
    source_ids = sorted(exposures["source_id"].unique())
    if args.stars:
        requested = set(args.stars)
        source_ids = [source_id for source_id in source_ids if source_id in requested]
        missing = requested - set(source_ids)
        if missing:
            raise ValueError(f"requested stars absent from exposures: {sorted(missing)}")

    if not args.skip_controls and not args.stars:
        control_dir = run_dir / "positive_controls"
        control_summaries = [
            analyze_star(source_id, str(args.exposures), str(control_dir), ("low",), args.keep_power)
            for source_id in CONTROL_IDS
        ]
        verify_controls(control_summaries)
        (run_dir / "positive_controls.json").write_text(
            json.dumps(control_summaries, indent=2, default=json_ready) + "\n", encoding="utf-8"
        )
        shutil.rmtree(control_dir)
        print("positive controls passed")

    summaries: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                analyze_star,
                source_id,
                str(args.exposures),
                str(run_dir),
                tuple(args.passes),
                args.keep_power,
            ): source_id
            for source_id in source_ids
        }
        for future in as_completed(futures):
            summary = future.result()
            summaries.append(summary)
            print(f"finished {summary['source_id']}", flush=True)

    collect_outputs(run_dir, source_ids)
    manifest = {
        "created": timestamp,
        "exposures": str(args.exposures.resolve()),
        "source_count": len(source_ids),
        "passes": args.passes,
        "workers": args.workers,
        "samples_per_peak": 10,
        "high_frequency_time_standard": "BJD_TDB",
        "high_frequency_detrending": "per-night median subtracted",
        "low_frequency_detrending": "per-band weighted global mean subtracted",
        "fast_method_tolerance": 1e-6,
        "spectral_window_power_threshold": 0.1,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {run_dir}")


if __name__ == "__main__":
    main()
