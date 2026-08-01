"""Shared numerical helpers for the exposure-level period searches."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.timeseries import LombScargle
from scipy.signal import find_peaks

SIDEREAL_FREQUENCY = 1.00273790935
SAMPLES_PER_PEAK = 10
WINDOW_POWER_THRESHOLD = 0.1
FAST_KWDS = {"trig_sum_kwds": {"eps": 1e-6}}


@dataclass(frozen=True)
class FrequencyGrid:
    minimum: float
    maximum: float
    step: float
    size: int

    @classmethod
    def create(cls, minimum: float, maximum: float, baseline: float) -> "FrequencyGrid":
        step = 1.0 / (SAMPLES_PER_PEAK * baseline)
        size = int(math.floor((maximum - minimum) / step)) + 1
        return cls(minimum, maximum, step, size)

    def values(self, start: int = 0, stop: int | None = None) -> np.ndarray:
        stop = self.size if stop is None else min(stop, self.size)
        return self.minimum + self.step * np.arange(start, stop, dtype=np.float64)


def load_exposures(path: Path) -> pd.DataFrame:
    columns = [
        "source_id",
        "band",
        "mjd",
        "bjd_tdb",
        "night_mjd",
        "mag",
        "magerr",
        "wdj_name",
        "wd_class",
        "paper_variable",
        "paper_periodic",
    ]
    frame = pd.read_csv(path, usecols=columns, dtype={"source_id": str, "band": str}, low_memory=False)
    numeric = ["mjd", "bjd_tdb", "night_mjd", "mag", "magerr"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    return frame


def prepare_series(frame: pd.DataFrame, high_frequency: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ordered = frame.sort_values("bjd_tdb")
    time = ordered["bjd_tdb"].to_numpy(dtype=float)
    time -= time.min()
    mag = ordered["mag"].to_numpy(dtype=float)
    if high_frequency:
        nightly = ordered.groupby("night_mjd")["mag"].transform("median").to_numpy(dtype=float)
        mag = mag - nightly
    else:
        weights = 1.0 / np.square(ordered["magerr"].to_numpy(dtype=float))
        mag = mag - np.average(mag, weights=weights)
    error = ordered["magerr"].to_numpy(dtype=float)
    return time, mag, error


def periodogram_to_memmap(
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    grid: FrequencyGrid,
    path: Path,
    chunk_size: int = 500_000,
) -> np.memmap:
    periodogram = np.memmap(path, dtype="float32", mode="w+", shape=(grid.size,))
    model = LombScargle(time, values, errors, fit_mean=True, center_data=True)
    for start in range(0, grid.size, chunk_size):
        stop = min(start + chunk_size, grid.size)
        frequency = grid.values(start, stop)
        power = model.power(
            frequency,
            method="fast",
            assume_regular_frequency=True,
            method_kwds=FAST_KWDS,
        )
        periodogram[start:stop] = np.asarray(power, dtype="float32")
    periodogram.flush()
    return periodogram


def extract_peaks(
    power: np.ndarray,
    grid: FrequencyGrid,
    count: int = 20,
    chunk_size: int = 500_000,
) -> tuple[list[tuple[float, int]], np.ndarray]:
    candidates: list[tuple[float, int]] = []
    noise_indices: list[np.ndarray] = []
    separation = max(2, int(math.ceil(1.5 * SAMPLES_PER_PEAK)))

    for start in range(0, grid.size, chunk_size):
        stop = min(start + chunk_size, grid.size)
        read_start = max(0, start - separation)
        read_stop = min(grid.size, stop + separation)
        chunk = np.asarray(power[read_start:read_stop])
        peaks, _ = find_peaks(chunk, distance=separation)
        global_peaks = read_start + peaks
        global_peaks = global_peaks[(global_peaks >= start) & (global_peaks < stop)]
        if not global_peaks.size:
            continue
        local_power = np.asarray(power[global_peaks])
        keep = min(max(count * 5, 100), global_peaks.size)
        chosen = np.argpartition(local_power, -keep)[-keep:]
        candidates.extend(
            (float(local_power[index]), int(global_peaks[index])) for index in chosen
        )
        noise_indices.append(global_peaks[::20])

    candidates.sort(reverse=True)
    selected: list[tuple[float, int]] = []
    for peak_power, index in candidates:
        if all(abs(index - prior_index) >= separation for _, prior_index in selected):
            selected.append((peak_power, index))
            if len(selected) == count:
                break
    noise = np.concatenate(noise_indices) if noise_indices else np.array([], dtype=np.int64)
    return selected, noise


def decimate_periodogram(power: np.ndarray, grid: FrequencyGrid, points: int = 12_000) -> tuple[np.ndarray, np.ndarray]:
    stride = max(1, grid.size // points)
    indices = np.arange(0, grid.size, stride, dtype=np.int64)
    return grid.minimum + grid.step * indices, np.asarray(power[indices], dtype=float)


def exact_power_and_amplitude(
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    frequency: float,
) -> tuple[float, float, float]:
    model = LombScargle(time, values, errors, fit_mean=True, center_data=True)
    power = float(model.power(frequency, method="chi2"))

    phase = 2.0 * np.pi * frequency * time
    design = np.column_stack((np.ones_like(time), np.sin(phase), np.cos(phase)))
    inv_var = 1.0 / np.square(errors)
    normal = design.T @ (inv_var[:, None] * design)
    covariance = np.linalg.inv(normal)
    beta = np.linalg.solve(normal, design.T @ (inv_var * values))
    amplitude = float(np.hypot(beta[1], beta[2]))
    if amplitude == 0:
        amplitude_error = float(np.sqrt(covariance[1, 1] + covariance[2, 2]))
    else:
        gradient = np.array([beta[1], beta[2]]) / amplitude
        amplitude_error = float(np.sqrt(gradient @ covariance[1:, 1:] @ gradient))
    return power, amplitude, amplitude_error


def baluev_fap(
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    power: float,
    grid: FrequencyGrid,
) -> float:
    model = LombScargle(time, values, errors, fit_mean=True, center_data=True)
    return float(
        model.false_alarm_probability(
            power,
            method="baluev",
            samples_per_peak=SAMPLES_PER_PEAK,
            minimum_frequency=grid.minimum,
            maximum_frequency=grid.maximum,
        )
    )


def window_strength(time: np.ndarray, frequency: np.ndarray | float) -> np.ndarray:
    frequency_array = np.atleast_1d(frequency).astype(float)
    centered = time - np.mean(time)
    phase = -2j * np.pi * frequency_array[:, None] * centered[None, :]
    return np.square(np.abs(np.mean(np.exp(phase), axis=1)))


def is_window_alias(time: np.ndarray, frequency: float, tolerance: float) -> tuple[bool, float]:
    offsets = np.linspace(-tolerance, tolerance, 21)
    strengths = window_strength(time, frequency + offsets)
    near_sidereal = abs(frequency / SIDEREAL_FREQUENCY - round(frequency / SIDEREAL_FREQUENCY)) * SIDEREAL_FREQUENCY
    nearby_window_peak = np.max(strengths) >= WINDOW_POWER_THRESHOLD
    return bool(nearby_window_peak or near_sidereal <= tolerance), float(np.max(strengths))


def is_alias_of_stronger(
    frequency: float,
    stronger_frequencies: list[float],
    tolerance: float,
) -> bool:
    for stronger in stronger_frequencies:
        delta = abs(frequency - stronger)
        nearest_alias = round(delta / SIDEREAL_FREQUENCY) * SIDEREAL_FREQUENCY
        if nearest_alias > 0 and abs(delta - nearest_alias) <= tolerance:
            return True
    return False


def approximate_peak_amplitude(
    time: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    power: float,
) -> float:
    weights = 1.0 / np.square(errors)
    centered = values - np.average(values, weights=weights)
    chi2_ref = float(np.sum(weights * centered**2))
    return math.sqrt(max(0.0, 4.0 * power * chi2_ref / np.sum(weights)))
