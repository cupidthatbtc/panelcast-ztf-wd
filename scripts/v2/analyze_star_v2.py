#!/usr/bin/env python3
"""v2 per-star analysis — same signature as the frozen analyze_star
(source_id, exposures_path, output_json, work_root, passes) and the SAME
per-star JSON schema (every frozen key present; schema_version "v2-1";
v2-only diagnostics under passes[p]["v2"] and the top-level "v2" block).

Pipeline per star: load shard -> per-oid zero-point alignment (align.py) ->
per pass: support-aware series (detrend.py) -> frozen per-band fast
periodograms on the frozen grid + the joint (chi^2-weighted) periodogram ->
spectral-window peaks per time set (window.py) -> top-15 peaks per series
with the v2 veto -> clustered candidate union -> exact per-band power / FAP,
joint fit, coherence, decision (rule.py). Search bounds and grids are the
frozen ones, so the comparison is about the rule, not the grid.
"""

from __future__ import annotations

import json
import math
import shutil
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from align import align_zero_points
from detrend import prepare_series_v2
from multiband import cluster_candidates
from rule import evaluate_candidates_v2
from v2_common import (
    BANDS,
    DEFAULT,
    ENGINE,
    SCHEMA_VERSION,
    FrequencyGrid,
    V2Constants,
    approximate_peak_amplitude,
    baluev_fap,
    exact_power_and_amplitude,
    extract_peaks,
    grid_for,
    json_ready,
    multiband_power,
    periodogram_to_memmap,
    unavailable_pass_result,
)
from window import is_alias_of_stronger_v2, is_window_alias_v2, veto_loci, window_peaks

SERIES = ("zg", "zr", "joint")
FROZEN_SERIES_NAME = {"zg": "zg", "zr": "zr", "joint": "multiband"}
BASE_COLUMNS = ["source_id", "band", "mjd", "bjd_tdb", "night_mjd", "mag", "magerr"]


def load_star_v2(path: Path) -> pd.DataFrame:
    """Frozen load_star plus the oid column (needed for alignment); a shard
    without oid is treated as a single oid per band."""
    header = pd.read_csv(path, nrows=0).columns.tolist()
    has_oid = "oid" in header
    columns = BASE_COLUMNS + (["oid"] if has_oid else [])
    dtype = {"source_id": str, "band": str}
    if has_oid:
        dtype["oid"] = str
    frame = pd.read_csv(path, usecols=columns, dtype=dtype)
    numeric = ["mjd", "bjd_tdb", "night_mjd", "mag", "magerr"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    if not has_oid:
        frame["oid"] = "0"
    if set(frame["band"]) != {"zg", "zr"}:
        raise ValueError("both zg and zr are required")
    return frame


def close_memmaps(powers: dict[str, np.ndarray]) -> None:
    for power in powers.values():
        if isinstance(power, np.memmap):
            power.flush()
            power._mmap.close()
    powers.clear()


def a95_from_noise(
    power: np.ndarray, noise_indices: np.ndarray,
    time: np.ndarray, values: np.ndarray, errors: np.ndarray,
) -> float:
    """Frozen 95th-percentile noise-peak amplitude limit (mmag)."""
    if noise_indices.size:
        noise_power = np.asarray(power[noise_indices], dtype=float)
        p95 = float(np.quantile(noise_power, 0.95))
        return approximate_peak_amplitude(time, values, errors, p95) * 1000.0
    return math.nan


def series_peak_rows(
    source_id: str,
    pass_name: str,
    series_name: str,
    power: np.ndarray,
    grid: FrequencyGrid,
    time: np.ndarray,
    values: np.ndarray | None,
    errors: np.ndarray | None,
    loci: list[dict[str, object]],
    tolerance: float,
    constants: V2Constants,
    cross_pass_stronger: list[float] | None = None,
) -> tuple[list[dict[str, object]], float]:
    """Top-`peaks_per_series` peaks of one series with the v2 veto; per-band
    series carry the exact power / amplitude / Baluev FAP (frozen helpers),
    the joint series carries the grid power only (as the frozen multiband
    rows do). `cross_pass_stronger` = the other pass's significant candidate
    frequencies (see rule.evaluate_candidates_v2). Returns (rows, a95_mmag)."""
    peaks, noise_indices = extract_peaks(power, grid, count=20)
    a95 = math.nan
    if values is not None:
        a95 = a95_from_noise(power, noise_indices, time, values, errors)
    rows: list[dict[str, object]] = []
    stronger: list[float] = list(cross_pass_stronger or [])
    for rank, (peak_power, index) in enumerate(peaks[: constants.peaks_per_series], start=1):
        frequency = grid.minimum + grid.step * index
        if values is not None:
            exact_power, amplitude, amplitude_error = exact_power_and_amplitude(
                time, values, errors, frequency
            )
            fap = baluev_fap(time, values, errors, exact_power, grid)
            amplitude_mmag, amplitude_error_mmag = amplitude * 1000.0, amplitude_error * 1000.0
        else:
            exact_power, fap = float(peak_power), math.nan
            amplitude_mmag, amplitude_error_mmag = math.nan, math.nan
        window_alias, window_power, locus = is_window_alias_v2(
            time, frequency, tolerance, loci, constants
        )
        stronger_alias = is_alias_of_stronger_v2(frequency, stronger, tolerance)
        rows.append({
            "source_id": source_id,
            "pass": pass_name,
            "series": FROZEN_SERIES_NAME[series_name],
            "rank": rank,
            "frequency_per_day": float(frequency),
            "period_days": 1.0 / frequency,
            "period_seconds": 86400.0 / frequency,
            "power": float(exact_power),
            "grid_power": float(peak_power),
            "baluev_fap_blind_grid": float(fap),
            "amplitude_mmag": float(amplitude_mmag),
            "amplitude_error_mmag": float(amplitude_error_mmag),
            "window_power": float(window_power),
            "window_alias": bool(window_alias),
            "window_locus": locus,
            "stronger_peak_sidereal_alias": bool(stronger_alias),   # frozen key; v2 = solar+sidereal spacings
            "stronger_peak_alias": bool(stronger_alias),
            "alias_flag": bool(window_alias or stronger_alias),
        })
        stronger.append(float(frequency))
    return rows, a95


def analyze_star_v2(
    source_id: str,
    shard_path: str,
    result_path: str,
    work_root: str,
    passes: tuple[str, ...],
    constants: V2Constants = DEFAULT,
) -> dict[str, object]:
    result_file = Path(result_path)
    if result_file.exists():
        existing = json.loads(result_file.read_text(encoding="utf-8"))
        if (
            existing.get("complete")
            and existing.get("schema_version") == SCHEMA_VERSION
            and set(existing.get("passes", {})) >= set(passes)
        ):
            return existing

    star = load_star_v2(Path(shard_path))
    aligned, alignment_table = align_zero_points(star, constants)
    origin = float(aligned["bjd_tdb"].min())
    baseline = float(aligned["bjd_tdb"].max() - origin)
    tolerance = constants.tolerance_over_baseline / baseline
    work_dir = Path(work_root) / source_id
    work_dir.mkdir(parents=True, exist_ok=True)
    pass_results: dict[str, dict[str, object]] = {}
    # significant candidate frequencies per band from passes already
    # evaluated (the low pass runs first): alias partners for later passes —
    # `cross_pass` holds the UNALIASED ones (used by the veto), `cross_pass_all`
    # every significant one (recorded so the veto is re-derivable offline)
    cross_pass: dict[str, list[float]] = {band: [] for band in BANDS}
    cross_pass_all: dict[str, list[float]] = {band: [] for band in BANDS}

    try:
        for pass_name in passes:
            high = pass_name == "high"
            grid = grid_for(pass_name, baseline)
            series = {
                band: prepare_series_v2(aligned[aligned["band"] == band], high, origin, constants)
                for band in BANDS
            }
            if high and all(np.ptp(series[band][1]) == 0 for band in BANDS):
                pass_results[pass_name] = unavailable_pass_result(
                    grid, "no variation after high-pass detrending"
                )
                continue
            combined_time = np.sort(np.concatenate([series[band][0] for band in BANDS]), kind="stable")
            times = {"zg": series["zg"][0], "zr": series["zr"][0], "joint": combined_time}
            paths = {name: work_dir / f".{pass_name}_{name}.power.dat" for name in SERIES}
            powers: dict[str, np.ndarray] = {}
            try:
                for band in BANDS:
                    powers[band] = periodogram_to_memmap(*series[band], grid, paths[band])
                powers["joint"], weights = multiband_power(powers["zg"], powers["zr"], paths["joint"])

                data_peaks = {name: window_peaks(times[name], grid, constants, tolerance) for name in SERIES}
                loci = {name: veto_loci(data_peaks[name], constants) for name in SERIES}

                peak_rows: list[dict[str, object]] = []
                rows_by_series: dict[str, list[dict[str, object]]] = {}
                upper_limits: dict[str, float] = {}
                for name in SERIES:
                    values = series[name][1] if name in BANDS else None
                    errors = series[name][2] if name in BANDS else None
                    rows, a95 = series_peak_rows(
                        source_id, pass_name, name, powers[name], grid, times[name],
                        values, errors, loci[name], tolerance, constants,
                        cross_pass.get(name) if name in BANDS else None,
                    )
                    rows_by_series[name] = rows
                    peak_rows.extend(rows)
                    if name in BANDS:
                        upper_limits[name] = a95

                frequencies = cluster_candidates(peak_rows, tolerance, constants.max_candidates)
                # joint top-5 AFTER the veto: the first `joint_top` unaliased
                # peaks of the joint top-15 (window aliases must not crowd
                # a real signal out of the list)
                joint_top = [
                    float(row["frequency_per_day"])
                    for row in rows_by_series["joint"]
                    if not row["alias_flag"]
                ][: constants.joint_top]
                candidates = evaluate_candidates_v2(
                    source_id, pass_name, frequencies, grid, series, peak_rows, joint_top,
                    {band: loci[band] for band in BANDS}, tolerance, constants,
                    cross_pass_stronger=cross_pass, cross_pass_all=cross_pass_all,
                )
                if not candidates:
                    pass_results[pass_name] = unavailable_pass_result(
                        grid, "no finite periodogram peaks", peak_rows
                    )
                    continue
                best = candidates[0]
                cross_pass_used = {band: list(cross_pass[band]) for band in BANDS}
                # only UNALIASED significant frequencies feed later passes'
                # veto (aliases of a window alias carry no new partner
                # information, and every entry excludes ~0.4 % of the high
                # band); every significant one is recorded as a possible partner
                for row in candidates:
                    for band in BANDS:
                        if float(row[f"{band}_fap"]) < constants.fap_threshold:
                            cross_pass_all[band].append(float(row["frequency_per_day"]))
                            if not bool(row[f"{band}_alias"]):
                                cross_pass[band].append(float(row["frequency_per_day"]))
                top_peaks = [
                    row for name in SERIES for row in rows_by_series[name][: 5]
                ]
                pass_results[pass_name] = {
                    "status": best["status"],
                    "basis": best["basis"],
                    "frequency_per_day": best["frequency_per_day"],
                    "period_days": best["period_days"],
                    "period_seconds": best["period_seconds"],
                    "best_band_fap": best["best_band_fap"],
                    "zg_power": best["zg_power"],
                    "zr_power": best["zr_power"],
                    "zg_fap": best["zg_fap"],
                    "zr_fap": best["zr_fap"],
                    "zg_amplitude_mmag": best["zg_amplitude_mmag"],
                    "zr_amplitude_mmag": best["zr_amplitude_mmag"],
                    "zg_alias": best["zg_alias"],
                    "zr_alias": best["zr_alias"],
                    "multiband_top5": best["multiband_top5"],
                    "zg_a95_mmag": upper_limits["zg"],
                    "zr_a95_mmag": upper_limits["zr"],
                    "grid_size": grid.size,
                    "grid_step_per_day": grid.step,
                    "multiband_zg_weight": weights[0],
                    "multiband_zr_weight": weights[1],
                    "top_peaks": top_peaks,
                    "available": True,
                    "unavailable_reason": "",
                    "v2": {
                        "coherent": best["coherent"],
                        "joint_top5": best["joint_top5"],
                        "delta_phase_cycles": best["delta_phase_cycles"],
                        "amp_ratio_r_over_g": best["amp_ratio_r_over_g"],
                        "candidate_reason": best["candidate_reason"],
                        "zg_window_locus": best["zg_window_locus"],
                        "zr_window_locus": best["zr_window_locus"],
                        "n_candidates": len(candidates),
                        "candidates": candidates,
                        "series_peaks": {
                            FROZEN_SERIES_NAME[name]: rows_by_series[name] for name in SERIES
                        },
                        "window_peaks": {
                            FROZEN_SERIES_NAME[name]: data_peaks[name] for name in SERIES
                        },
                        "tolerance_per_day": tolerance,
                        "n_points": {band: int(series[band][0].size) for band in BANDS},
                        "joint_top_frequencies": joint_top,
                        "cross_pass_stronger": cross_pass_used,
                    },
                }
            finally:
                close_memmaps(powers)
                for path in paths.values():
                    path.unlink(missing_ok=True)

        result = {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE,
            "source_id": source_id,
            "n_exp_zg": int((star["band"] == "zg").sum()),
            "n_exp_zr": int((star["band"] == "zr").sum()),
            "baseline_days": baseline,
            "passes": pass_results,
            "complete": set(pass_results) >= set(passes),
            "v2": {
                "constants": constants.as_dict(),
                "time_origin_bjd_tdb": origin,
                "alignment": alignment_table,
                "n_oids": {band: int(aligned.loc[aligned["band"] == band, "oid_label"].nunique())
                           for band in BANDS},
            },
        }
        temporary = result_file.with_suffix(".json.part")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(result, indent=2, default=json_ready) + "\n", encoding="utf-8"
        )
        temporary.replace(result_file)
        result_file.with_suffix(".error.json").unlink(missing_ok=True)
        shutil.rmtree(work_dir, ignore_errors=True)
        return result
    except Exception:
        error_path = result_file.with_suffix(".error.json")
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(
            json.dumps({"source_id": source_id, "error": traceback.format_exc()}, indent=2) + "\n",
            encoding="utf-8",
        )
        raise


__all__ = ["analyze_star_v2", "load_star_v2", "series_peak_rows"]
