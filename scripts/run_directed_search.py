#!/usr/bin/env python3
"""Evaluate the named pulsators at Jestin et al.'s published frequencies."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.timeseries import LombScargle, LombScargleMultiband

from lomb_scargle_common import (
    SIDEREAL_FREQUENCY,
    exact_power_and_amplitude,
    is_window_alias,
    load_exposures,
    prepare_series,
)

ROOT = Path(__file__).resolve().parents[1]
ROUNDING_HALF_WIDTH = 0.005


def single_trial_fap(model: LombScargle, power: float) -> float:
    return float(np.clip(1.0 - model.distribution(power, cumulative=True), 0.0, 1.0))


def targeted_fap(
    model: LombScargle,
    power: float,
    center_frequency: float,
) -> float:
    return float(
        model.false_alarm_probability(
            power,
            method="baluev",
            samples_per_peak=10,
            minimum_frequency=max(1e-9, center_frequency - ROUNDING_HALF_WIDTH),
            maximum_frequency=center_frequency + ROUNDING_HALF_WIDTH,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--periods", type=Path, default=ROOT / "data/roster/literature_periods.csv")
    parser.add_argument("--blind-run", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or args.blind_run / "directed_search.csv"

    exposures = load_exposures(args.exposures)
    periods = pd.read_csv(args.periods, dtype={"source_id": str})
    periods = periods[periods["directed_search"].eq(True)]
    upper = pd.read_csv(args.blind_run / "upper_limits.csv", dtype={"source_id": str})
    detail_rows = []
    summary_rows = []

    for period in periods.itertuples(index=False):
        star = exposures[exposures["source_id"] == period.source_id]
        series = {
            band: prepare_series(star[star["band"] == band], high_frequency=True)
            for band in ("zg", "zr")
        }
        models = {
            band: LombScargle(*series[band], fit_mean=True, center_data=True)
            for band in ("zg", "zr")
        }
        frequency_set = []
        for alias_order in range(-3, 4):
            frequency = period.frequency_per_day + alias_order * SIDEREAL_FREQUENCY
            if frequency > 0:
                frequency_set.append((alias_order, frequency))

        literature_rows = []
        for alias_order, frequency in frequency_set:
            for band in ("zg", "zr"):
                time, values, errors = series[band]
                power, amplitude, amplitude_error = exact_power_and_amplitude(
                    time, values, errors, frequency
                )
                fap = single_trial_fap(models[band], power)
                alias_flag, window_power = is_window_alias(time, frequency, 1.5 / np.ptp(time))
                row = {
                    "source_id": period.source_id,
                    "wdj_name": period.wdj_name,
                    "wd_class": period.wd_class,
                    "alias_order": alias_order,
                    "band": band,
                    "frequency_per_day": frequency,
                    "period_seconds": 86400.0 / frequency,
                    "power": power,
                    "single_trial_fap": fap,
                    "amplitude_mmag": amplitude * 1000.0,
                    "amplitude_error_mmag": amplitude_error * 1000.0,
                    "window_power": window_power,
                    "window_alias": alias_flag,
                    "source": period.source,
                    "source_url": period.source_url,
                }
                detail_rows.append(row)
                if alias_order == 0:
                    literature_rows.append(row)

        origin = float(star["bjd_tdb"].min())
        combined_time = np.concatenate(
            [
                star[star["band"] == band].sort_values("bjd_tdb")["bjd_tdb"].to_numpy(dtype=float)
                - origin
                for band in ("zg", "zr")
            ]
        )
        combined_values = np.concatenate([series["zg"][1], series["zr"][1]])
        combined_errors = np.concatenate([series["zg"][2], series["zr"][2]])
        combined_bands = np.concatenate(
            [np.repeat("zg", len(series["zg"][0])), np.repeat("zr", len(series["zr"][0]))]
        )
        baseline = float(np.ptp(combined_time))
        step = 1.0 / (10.0 * baseline)
        local_frequency = np.arange(
            period.frequency_per_day - ROUNDING_HALF_WIDTH,
            period.frequency_per_day + ROUNDING_HALF_WIDTH + step / 2,
            step,
        )
        multiband = LombScargleMultiband(
            combined_time,
            combined_values,
            combined_bands,
            combined_errors,
            nterms_base=1,
            nterms_band=0,
        )
        local_multiband_power = multiband.power(local_frequency, method="flexible")
        refined_frequency = float(local_frequency[int(np.argmax(local_multiband_power))])

        refined = {}
        for band in ("zg", "zr"):
            time, values, errors = series[band]
            power, amplitude, amplitude_error = exact_power_and_amplitude(
                time, values, errors, refined_frequency
            )
            refined[band] = {
                "power": power,
                "fap": targeted_fap(models[band], power, period.frequency_per_day),
                "amplitude": amplitude * 1000.0,
                "amplitude_error": amplitude_error * 1000.0,
            }

        by_band = {row["band"]: row for row in literature_rows}
        exact_detected = all(
            by_band[band]["single_trial_fap"] < 1e-3 and not by_band[band]["window_alias"]
            for band in ("zg", "zr")
        )
        rounded_detected = all(refined[band]["fap"] < 1e-3 for band in ("zg", "zr"))
        if exact_detected:
            verdict = "detected_at_tabulated_frequency"
        elif rounded_detected:
            verdict = "detected_within_reported_rounding"
        else:
            verdict = "not_detected"

        limit_rows = upper[
            (upper["source_id"] == period.source_id) & (upper["pass"] == "high")
        ]
        limits = {row.band: row.a95_mmag for row in limit_rows.itertuples(index=False)}
        summary_rows.append(
            {
                "source_id": period.source_id,
                "wdj_name": period.wdj_name,
                "wd_class": period.wd_class,
                "literature_frequency_per_day": period.frequency_per_day,
                "literature_period_seconds": period.period_seconds,
                "frequency_precision_per_day": 0.01,
                "zg_exact_single_trial_fap": by_band["zg"]["single_trial_fap"],
                "zr_exact_single_trial_fap": by_band["zr"]["single_trial_fap"],
                "refined_frequency_per_day": refined_frequency,
                "refined_period_seconds": 86400.0 / refined_frequency,
                "zg_targeted_grid_fap": refined["zg"]["fap"],
                "zr_targeted_grid_fap": refined["zr"]["fap"],
                "zg_amplitude_mmag": refined["zg"]["amplitude"],
                "zg_amplitude_error_mmag": refined["zg"]["amplitude_error"],
                "zr_amplitude_mmag": refined["zr"]["amplitude"],
                "zr_amplitude_error_mmag": refined["zr"]["amplitude_error"],
                "multiband_power": float(np.max(local_multiband_power)),
                "directed_verdict": verdict,
                "zg_a95_mmag_if_undetected": np.nan if verdict != "not_detected" else limits.get("zg", np.nan),
                "zr_a95_mmag_if_undetected": np.nan if verdict != "not_detected" else limits.get("zr", np.nan),
                "trials_context": "exact value is single-trial; refinement searches the reported 0.01 d^-1 rounding interval",
                "source": period.source,
                "source_url": period.source_url,
            }
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(out, index=False)
    pd.DataFrame(detail_rows).to_csv(out.with_name("directed_search_aliases.csv"), index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
