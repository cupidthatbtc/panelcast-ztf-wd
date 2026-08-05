#!/usr/bin/env python3
"""Plot per-star periodograms and phase-folded light curves."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from lomb_scargle_common import load_exposures, prepare_series

ROOT = Path(__file__).resolve().parents[1]
SERIES_STYLE = {
    "zg": ("#2a78d6", "ZTF g", "-"),
    "zr": ("#eb6834", "ZTF r", "--"),
    "multiband": ("#1baf7a", "multiband", "-"),
}


def plot_periodogram(source_id: str, star_dir: Path, out_dir: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.6))
    for axis, pass_name in zip(axes, ("low", "high"), strict=True):
        data = pd.read_csv(star_dir / f"periodogram_{pass_name}.csv")
        peaks = pd.read_csv(star_dir / f"peaks_{pass_name}.csv", dtype={"source_id": str})
        for series, (colour, label, linestyle) in SERIES_STYLE.items():
            subset = data[data["series"] == series].sort_values("frequency_per_day")
            axis.plot(
                subset["frequency_per_day"],
                subset["power"],
                color=colour,
                linewidth=0.8,
                linestyle=linestyle,
                alpha=0.78,
                label=label,
            )
            top = peaks[peaks["series"] == series]
            axis.scatter(
                top["frequency_per_day"],
                top["power"],
                color=colour,
                s=24,
                edgecolor="white",
                linewidth=0.6,
                zorder=3,
            )
        aliases = peaks[peaks["alias_flag"].fillna(False).astype(bool)]
        for index, frequency in enumerate(aliases["frequency_per_day"]):
            axis.axvline(
                frequency,
                color="#d03b3b",
                linewidth=0.8,
                linestyle=":",
                alpha=0.65,
                label="vetted alias" if index == 0 else None,
            )
        axis.set_xlim((0, 48) if pass_name == "low" else (24, 1440))
        axis.set_ylabel("Lomb–Scargle power")
        axis.set_title(
            "low-frequency pass — global mean removed"
            if pass_name == "low"
            else "high-frequency pass — per-night median removed"
        )
        axis.grid(color="#e1e0d9", linewidth=0.6)
    axes[-1].set_xlabel("frequency (cycles day⁻¹)")
    handles, labels = axes[0].get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    fig.legend(
        unique.values(), unique.keys(), loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=4, frameon=False
    )
    fig.suptitle(f"Gaia DR3 {source_id} — blind periodograms", fontsize=13, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"periodogram_{source_id}.png", dpi=160, facecolor="white")
    plt.close(fig)


def phase_bin(phase: np.ndarray, value: np.ndarray, bins: int = 30) -> tuple[np.ndarray, np.ndarray]:
    edges = np.linspace(0, 1, bins + 1)
    index = np.digitize(phase, edges) - 1
    centers, means = [], []
    for bin_index in range(bins):
        selected = value[index == bin_index]
        if selected.size:
            centers.append((edges[bin_index] + edges[bin_index + 1]) / 2)
            ordered = np.sort(selected)
            trim = int(0.05 * len(ordered)) if len(ordered) >= 20 else 0
            trimmed = ordered[trim:-trim] if trim else ordered
            means.append(float(np.mean(trimmed)))
    return np.asarray(centers), np.asarray(means)


def plot_phase_fold(
    source_id: str,
    candidate: pd.Series,
    exposures: pd.DataFrame,
    out_dir: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(9.2, 5.4))
    high = candidate["pass"] == "high"
    frequency = float(candidate["frequency_per_day"])
    origin = float(exposures[exposures["source_id"] == source_id]["bjd_tdb"].min())
    plotted_values = []
    for band, (colour, label, _) in list(SERIES_STYLE.items())[:2]:
        frame = exposures[
            (exposures["source_id"] == source_id) & (exposures["band"] == band)
        ].sort_values("bjd_tdb")
        _, value, _ = prepare_series(frame, high_frequency=high)
        plotted_values.append(value)
        phase_time = frame["bjd_tdb"].to_numpy(dtype=float) - origin
        phase = np.mod(phase_time * frequency, 1.0)
        axis.scatter(
            np.concatenate([phase, phase + 1]),
            np.concatenate([value, value]),
            s=9,
            color=colour,
            alpha=0.28,
            linewidth=0,
            label=label,
        )
        center, phase_mean = phase_bin(phase, value)
        axis.plot(
            np.concatenate([center, center + 1]),
            np.concatenate([phase_mean, phase_mean]),
            color=colour,
            linewidth=2.0,
        )
    lower, upper = np.quantile(np.concatenate(plotted_values), [0.005, 0.995])
    padding = max(0.002, 0.08 * (upper - lower))
    axis.set(
        xlim=(0, 2),
        ylim=(upper + padding, lower - padding),
        xlabel="phase (two cycles)",
        ylabel="Δ magnitude",
        title=(
            f"Gaia DR3 {source_id} — P = {candidate['period_days']:.8g} d "
            f"({candidate['basis']})"
        ),
    )
    axis.grid(color="#e1e0d9", linewidth=0.6)
    axis.legend(frameon=False)
    axis.text(
        0.01,
        0.02,
        "solid line: 5% trimmed phase-bin mean",
        transform=axis.transAxes,
        fontsize=8,
        color="#52514e",
    )
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"phase_fold_{source_id}.png", dpi=170, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    args = parser.parse_args()

    exposures = load_exposures(args.exposures)
    source_ids = sorted(exposures["source_id"].unique())
    periodogram_dir = args.run_dir / "figures/periodograms"
    for source_id in source_ids:
        plot_periodogram(source_id, args.run_dir / "stars" / source_id, periodogram_dir)

    candidates = pd.read_csv(args.run_dir / "candidates.csv", dtype={"source_id": str})
    confirmed = candidates[candidates["status"] == "confirmed"].copy()
    confirmed = (
        confirmed.sort_values(["source_id", "best_band_fap"])
        .groupby("source_id", as_index=False)
        .first()
    )
    phase_dir = args.run_dir / "figures/phase_folds"
    for _, candidate in confirmed.iterrows():
        plot_phase_fold(candidate["source_id"], candidate, exposures, phase_dir)
    print(f"wrote {len(source_ids)} periodograms and {len(confirmed)} phase folds")


if __name__ == "__main__":
    main()
