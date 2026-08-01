#!/usr/bin/env python3
"""Compare periodogram, nightly-census, and monthly-census injection recovery."""

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

from lomb_scargle_common import FrequencyGrid, baluev_fap, load_exposures, prepare_series
from astropy.timeseries import LombScargle

ROOT = Path(__file__).resolve().parents[1]
QUIET_SOURCE = "114808397128552576"
PERIODS_MIN = (2, 5, 10, 20, 60)
AMPLITUDES_MMAG = (2, 5, 10, 20, 50)
PHASES_PER_CELL = 20


def choose_sampling_sources(exposures: pd.DataFrame, roster: pd.DataFrame) -> list[str]:
    g_counts = exposures[exposures["band"] == "zg"].groupby("source_id").size()
    median_count = float(g_counts.median())
    constants = set(roster.loc[roster["paper_variable"].eq(False), "source_id"])
    alternatives = g_counts[
        g_counts.index.isin(constants - {QUIET_SOURCE})
    ]
    median_source = str((alternatives - median_count).abs().idxmin())
    return [QUIET_SOURCE, median_source]


def binned_ratio(frame: pd.DataFrame, monthly: bool) -> float:
    work = frame.copy()
    work["night_mjd"] = np.floor(work["mjd"]).astype(int)
    nights = []
    for night, rows in work.groupby("night_mjd"):
        magnitude = rows["injected_mag"].to_numpy(dtype=float)
        reported = rows["magerr"].to_numpy(dtype=float)
        n_exp = len(rows)
        scatter_se = np.std(magnitude, ddof=1) / math.sqrt(n_exp) if n_exp >= 2 else 0.0
        nights.append(
            {
                "night_mjd": night,
                "mag_binned": float(np.median(magnitude)),
                "mag_err": max(scatter_se, float(np.median(reported)) / math.sqrt(n_exp)),
            }
        )
    binned = pd.DataFrame(nights)
    if monthly:
        binned["month_id"] = (
            pd.to_datetime(binned["night_mjd"], unit="D", origin="1858-11-17")
            .dt.to_period("M")
            .astype(str)
        )
        binned = binned.groupby("month_id", as_index=False).agg(
            mag_binned=("mag_binned", "median"), mag_err=("mag_err", "median")
        )
    return float(np.std(binned["mag_binned"], ddof=0) / np.median(binned["mag_err"]))


def ls_recovery(frame: pd.DataFrame, injected_frequency: float) -> tuple[bool, float, float]:
    time, residual, error = prepare_series(frame, high_frequency=True)
    baseline = float(np.ptp(time))
    local_frequency = injected_frequency + np.linspace(-2.0 / baseline, 2.0 / baseline, 41)
    model = LombScargle(time, residual, error, fit_mean=True, center_data=True)
    power = model.power(local_frequency, method="chi2")
    index = int(np.argmax(power))
    best_frequency = float(local_frequency[index])
    grid = FrequencyGrid.create(24.0, 1440.0, baseline)
    fap = baluev_fap(time, residual, error, float(power[index]), grid)
    recovered = abs(best_frequency - injected_frequency) <= 1.5 / baseline and fap < 1e-3
    return recovered, best_frequency, fap


def plot_grid(summary: pd.DataFrame, out: Path) -> None:
    detectors = (
        ("lomb_scargle", "Exposure-level Lomb–Scargle"),
        ("nightly_census", "Nightly census ratio > 2.5"),
        ("monthly_census", "Monthly census ratio > 2.5"),
    )
    cmap = LinearSegmentedColormap.from_list("recovery_blue", ["#cde2fb", "#2a78d6", "#0d366b"])
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.8), sharex=True, sharey=True)
    for axis, (detector, title) in zip(axes, detectors, strict=True):
        table = (
            summary[summary["detector"] == detector]
            .pivot(index="amplitude_mmag", columns="period_minutes", values="recovery_fraction")
            .reindex(index=AMPLITUDES_MMAG, columns=PERIODS_MIN)
        )
        image = axis.imshow(table.to_numpy(), origin="lower", vmin=0, vmax=1, cmap=cmap, aspect="auto")
        for row in range(len(AMPLITUDES_MMAG)):
            for column in range(len(PERIODS_MIN)):
                value = float(table.iloc[row, column])
                axis.text(
                    column,
                    row,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color="white" if value >= 0.55 else "#0b0b0b",
                    fontsize=9,
                )
        axis.set_title(title, fontsize=10.5)
        axis.set_xticks(range(len(PERIODS_MIN)), PERIODS_MIN)
        axis.set_yticks(range(len(AMPLITUDES_MMAG)), AMPLITUDES_MMAG)
        axis.set_xlabel("injected period (min)")
    axes[0].set_ylabel("injected semiamplitude (mmag)")
    colorbar_axis = fig.add_axes([0.91, 0.16, 0.014, 0.68])
    colorbar = fig.colorbar(image, cax=colorbar_axis)
    colorbar.set_label("recovery fraction")
    fig.suptitle("Injection–recovery on two paper-constant ZTF g light curves", fontsize=13)
    fig.subplots_adjust(left=0.07, right=0.87, bottom=0.14, top=0.82, wspace=0.16)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=170, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--roster", type=Path, default=ROOT / "data/roster/jestin2026_roster.csv")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    args = parser.parse_args()

    exposures = load_exposures(args.exposures)
    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    source_ids = choose_sampling_sources(exposures, roster)
    rng = np.random.default_rng(20260801)
    rows = []

    for source_id in source_ids:
        base = exposures[
            (exposures["source_id"] == source_id) & (exposures["band"] == "zg")
        ].copy()
        time = base["bjd_tdb"].to_numpy(dtype=float)
        time -= time.min()
        for period_minutes in PERIODS_MIN:
            frequency = 1440.0 / period_minutes
            for amplitude_mmag in AMPLITUDES_MMAG:
                for replicate, phase in enumerate(rng.uniform(0, 2 * np.pi, PHASES_PER_CELL)):
                    injected = base.copy()
                    injected["injected_mag"] = injected["mag"] + amplitude_mmag / 1000.0 * np.sin(
                        2 * np.pi * frequency * time + phase
                    )
                    injected["mag"] = injected["injected_mag"]
                    ls_found, recovered_frequency, fap = ls_recovery(injected, frequency)
                    nightly_ratio = binned_ratio(injected, monthly=False)
                    monthly_ratio = binned_ratio(injected, monthly=True)
                    rows.append(
                        {
                            "source_id": source_id,
                            "period_minutes": period_minutes,
                            "amplitude_mmag": amplitude_mmag,
                            "replicate": replicate,
                            "phase_radians": phase,
                            "ls_recovered": ls_found,
                            "ls_recovered_frequency_per_day": recovered_frequency,
                            "ls_baluev_fap_blind_grid": fap,
                            "nightly_ratio": nightly_ratio,
                            "nightly_recovered": nightly_ratio > 2.5,
                            "monthly_ratio": monthly_ratio,
                            "monthly_recovered": monthly_ratio > 2.5,
                        }
                    )

    detail = pd.DataFrame(rows)
    summary_parts = []
    for detector, column in (
        ("lomb_scargle", "ls_recovered"),
        ("nightly_census", "nightly_recovered"),
        ("monthly_census", "monthly_recovered"),
    ):
        aggregate = detail.groupby(["period_minutes", "amplitude_mmag"], as_index=False)[column].mean()
        aggregate = aggregate.rename(columns={column: "recovery_fraction"})
        aggregate["detector"] = detector
        aggregate["n_injections"] = len(source_ids) * PHASES_PER_CELL
        summary_parts.append(aggregate)
    summary = pd.concat(summary_parts, ignore_index=True)

    args.run_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.run_dir / "injection_recovery_detail.csv", index=False)
    summary.to_csv(args.run_dir / "injection_recovery.csv", index=False)
    pd.DataFrame(
        {
            "source_id": source_ids,
            "selection_role": ["quiet paper-constant", "paper-constant nearest roster median g sampling"],
            "n_exp_zg": [
                int(((exposures["source_id"] == source_id) & (exposures["band"] == "zg")).sum())
                for source_id in source_ids
            ],
        }
    ).to_csv(args.run_dir / "injection_recovery_sources.csv", index=False)
    plot_grid(summary, args.run_dir / "figures/injection_recovery.png")
    print(f"wrote injection recovery for {len(detail)} injections across {source_ids}")


if __name__ == "__main__":
    main()
