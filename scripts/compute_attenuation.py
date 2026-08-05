#!/usr/bin/env python3
"""Compare predicted random-phase binning attenuation with the census ratios."""

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--nightly", type=Path, default=ROOT / "data/raw/ztf_wd_panel.csv")
    parser.add_argument("--census", type=Path, default=ROOT / "data/raw/variance_census.csv")
    args = parser.parse_args()

    candidates = pd.read_csv(args.run_dir / "candidates.csv", dtype={"source_id": str})
    confirmed = candidates[candidates["status"] == "confirmed"].copy()
    confirmed = (
        confirmed.sort_values(["source_id", "best_band_fap"])
        .groupby("source_id", as_index=False)
        .first()
    )
    exposures = pd.read_csv(
        args.exposures,
        usecols=["source_id", "band", "night_mjd"],
        dtype={"source_id": str},
        low_memory=False,
    )
    nightly = pd.read_csv(args.nightly, dtype={"source_id": str})
    census = pd.read_csv(args.census, dtype={"source_id": str}).set_index("source_id")

    rows = []
    for _, candidate in confirmed.iterrows():
        source_id = candidate["source_id"]
        row = {
            "source_id": source_id,
            "pass": candidate["pass"],
            "period_days": candidate["period_days"],
            "frequency_per_day": candidate["frequency_per_day"],
        }
        for band in ("zg", "zr"):
            subset = exposures[
                (exposures["source_id"] == source_id) & (exposures["band"] == band)
            ]
            n_exp = subset.groupby("night_mjd").size().to_numpy(dtype=float)
            mean_inverse_n = float(np.mean(1.0 / n_exp))
            amplitude_mmag = float(candidate[f"{band}_amplitude_mmag"])
            signal_sd_mmag = amplitude_mmag / math.sqrt(2.0) * math.sqrt(mean_inverse_n)
            nightly_errors = nightly[
                (nightly["source_id"] == source_id) & (nightly["band"] == band)
            ]["mag_err"]
            median_error_mmag = float(np.median(nightly_errors) * 1000.0)
            signal_ratio = signal_sd_mmag / median_error_mmag
            row[f"{band}_amplitude_mmag"] = amplitude_mmag
            row[f"{band}_median_n_exp"] = float(np.median(n_exp))
            row[f"{band}_mean_inverse_n_exp"] = mean_inverse_n
            row[f"{band}_predicted_signal_sd_mmag"] = signal_sd_mmag
            row[f"{band}_median_nightly_error_mmag"] = median_error_mmag
            row[f"{band}_predicted_signal_ratio"] = signal_ratio
            row[f"{band}_predicted_total_ratio"] = math.sqrt(1.0 + signal_ratio**2)
            row[f"{band}_observed_nightly_ratio"] = float(
                census.loc[source_id, f"{band}_nightly_ratio"]
            )
        rows.append(row)

    attenuation = pd.DataFrame(rows)
    attenuation.to_csv(args.run_dir / "attenuation.csv", index=False)

    fig, axis = plt.subplots(figsize=(7.2, 6.4))
    for band, colour, marker, label in (
        ("zg", "#2a78d6", "o", "ZTF g"),
        ("zr", "#eb6834", "s", "ZTF r"),
    ):
        x = attenuation[f"{band}_predicted_total_ratio"]
        y = attenuation[f"{band}_observed_nightly_ratio"]
        axis.scatter(x, y, s=65, color=colour, marker=marker, edgecolor="white", linewidth=0.8, label=label)
    limit = max(
        3.0,
        float(
            np.nanmax(
                attenuation[
                    [
                        "zg_predicted_total_ratio",
                        "zr_predicted_total_ratio",
                        "zg_observed_nightly_ratio",
                        "zr_observed_nightly_ratio",
                    ]
                ].to_numpy()
            )
        )
        * 1.12,
    )
    axis.plot([0.8, limit], [0.8, limit], linestyle="--", linewidth=1.2, color="#898781")
    axis.set(
        xscale="log",
        yscale="log",
        xlim=(0.8, limit),
        ylim=(0.8, limit),
        xlabel="predicted nightly sd / error (signal + measurement noise)",
        ylabel="observed nightly sd / median error",
        title="Random-phase attenuation: predicted vs observed",
    )
    axis.grid(color="#e1e0d9", linewidth=0.7)
    axis.legend(frameon=False)
    fig.tight_layout()
    figure_path = args.run_dir / "figures/attenuation.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=170, facecolor="white")
    plt.close(fig)
    print(f"wrote attenuation comparison for {len(attenuation)} confirmed stars")


if __name__ == "__main__":
    main()
