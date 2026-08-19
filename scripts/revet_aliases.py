#!/usr/bin/env python3
"""Reapply the spectral-window and sidereal-alias vet to saved periodograms."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from lomb_scargle_common import (
    WINDOW_POWER_THRESHOLD,
    is_alias_of_stronger,
    is_window_alias,
    load_exposures,
    prepare_series,
)
from run_lomb_scargle import collect_outputs, evaluate_candidates, grid_for, json_ready

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    args = parser.parse_args()

    exposures = load_exposures(args.exposures)
    source_ids = sorted(exposures["source_id"].unique())
    for source_id in source_ids:
        star = exposures[exposures["source_id"] == source_id]
        star_dir = args.run_dir / "stars" / source_id
        summary_path = star_dir / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        baseline = float(star["bjd_tdb"].max() - star["bjd_tdb"].min())
        origin = float(star["bjd_tdb"].min())
        combined_time = star["bjd_tdb"].to_numpy(dtype=float) - origin

        for pass_name in ("low", "high"):
            high = pass_name == "high"
            grid = grid_for(pass_name, baseline)
            series = {
                band: prepare_series(star[star["band"] == band], high_frequency=high)
                for band in ("zg", "zr")
            }
            peaks = pd.read_csv(star_dir / f"peaks_{pass_name}.csv", dtype={"source_id": str})
            updated = []
            for series_name, group in peaks.groupby("series", sort=False):
                time = combined_time if series_name == "multiband" else series[series_name][0]
                tolerance = 1.5 / np.ptp(time)
                stronger = []
                for _, row in group.sort_values("rank").iterrows():
                    frequency = float(row["frequency_per_day"])
                    window_alias, window_power = is_window_alias(time, frequency, tolerance)
                    stronger_alias = is_alias_of_stronger(frequency, stronger, tolerance)
                    row["window_power"] = window_power
                    row["window_alias"] = window_alias
                    row["stronger_peak_sidereal_alias"] = stronger_alias
                    row["alias_flag"] = window_alias or stronger_alias
                    updated.append(row)
                    stronger.append(frequency)
            peaks = pd.DataFrame(updated).sort_values(["series", "rank"])
            candidates = evaluate_candidates(
                source_id, pass_name, peaks.to_dict("records"), grid, series
            )
            peaks.to_csv(star_dir / f"peaks_{pass_name}.csv", index=False)
            pd.DataFrame(candidates).to_csv(star_dir / f"candidates_{pass_name}.csv", index=False)

            best = candidates[0]
            summary["passes"][pass_name].update(
                {
                    "status": best["status"],
                    "basis": best["basis"],
                    "frequency_per_day": best["frequency_per_day"],
                    "period_days": best["period_days"],
                    "period_seconds": best["period_seconds"],
                    "best_band_fap": best["best_band_fap"],
                    "zg_amplitude_mmag": best["zg_amplitude_mmag"],
                    "zr_amplitude_mmag": best["zr_amplitude_mmag"],
                }
            )
        summary_path.write_text(
            json.dumps(summary, indent=2, default=json_ready) + "\n", encoding="utf-8"
        )

    collect_outputs(args.run_dir, source_ids)
    manifest_path = args.run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["spectral_window_power_threshold"] = WINDOW_POWER_THRESHOLD
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"re-vetted aliases for {len(source_ids)} stars")


if __name__ == "__main__":
    main()
