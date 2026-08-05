"""Build and plot the exposure/night/month variability census in ZTF g and r.

Usage:
    python scripts/plot_variance_census.py
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
PULSATOR_CLASSES = {"ZZ Ceti", "GW Vir", "V777 Her", "Old DAVs"}


def scatter_over_error(magnitude: pd.Series, error: pd.Series) -> float:
    return float(np.std(magnitude.to_numpy(dtype=float), ddof=0) / np.median(error))


def monthly_panel(nightly: pd.DataFrame) -> pd.DataFrame:
    frame = nightly.copy()
    frame["month_id"] = (
        pd.to_datetime(frame["night_mjd"], unit="D", origin="1858-11-17")
        .dt.to_period("M")
        .astype(str)
    )
    return (
        frame.groupby(["source_id", "band", "month_id"], as_index=False)
        .agg(mag_binned=("mag_binned", "median"), mag_err=("mag_err", "median"))
    )


def build_census(roster: pd.DataFrame, exposures: pd.DataFrame, nightly: pd.DataFrame) -> pd.DataFrame:
    exposures = exposures.copy()
    exposures["high_frequency_residual"] = exposures["mag"] - exposures.groupby(
        ["source_id", "band", "night_mjd"]
    )["mag"].transform("median")
    monthly = monthly_panel(nightly)

    rows = []
    for meta in roster.itertuples(index=False):
        if meta.source_id not in set(exposures["source_id"]):
            continue
        row = {
            "source_id": meta.source_id,
            "wdj_name": meta.wdj_name,
            "wd_class": meta.wd_class,
            "paper_variable": meta.paper_variable,
            "paper_periodic": meta.paper_periodic,
        }
        for band in ("zg", "zr"):
            exp = exposures[
                (exposures["source_id"] == meta.source_id) & (exposures["band"] == band)
            ]
            night = nightly[
                (nightly["source_id"] == meta.source_id) & (nightly["band"] == band)
            ]
            month = monthly[
                (monthly["source_id"] == meta.source_id) & (monthly["band"] == band)
            ]
            row[f"{band}_exposure_ratio"] = scatter_over_error(
                exp["high_frequency_residual"], exp["magerr"]
            )
            row[f"{band}_nightly_ratio"] = scatter_over_error(
                night["mag_binned"], night["mag_err"]
            )
            row[f"{band}_monthly_ratio"] = scatter_over_error(
                month["mag_binned"], month["mag_err"]
            )
        rows.append(row)
    return pd.DataFrame(rows)


def style_for(row: pd.Series) -> tuple[str, str, float, str]:
    if row["wd_class"] in PULSATOR_CLASSES:
        return ORANGE, "*", 180.0, "compact pulsator (paper: variable)"
    if row["paper_variable"] is True or str(row["paper_variable"]) == "True":
        return BLUE, "o", 65.0, "binary / transit / CV (paper: variable)"
    return AQUA, "s", 65.0, "paper: constant or unclassified"


def plot_transition(
    axis: plt.Axes,
    census: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    xlabel: str,
    ylabel: str,
    annotate_pulsators: bool,
) -> None:
    for _, row in census.iterrows():
        colour, marker, size, label = style_for(row)
        axis.scatter(
            row[x_column],
            row[y_column],
            c=colour,
            marker=marker,
            s=size,
            label=label,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        if annotate_pulsators and row["wd_class"] in PULSATOR_CLASSES:
            offsets = {
                "zg": {
                    "ZZ Ceti": (-52, 3),
                    "GW Vir": (7, -15),
                    "Old DAVs": (7, 8),
                    "V777 Her": (7, -14),
                },
                "zr": {
                    "ZZ Ceti": (7, -18),
                    "GW Vir": (-46, -16),
                    "Old DAVs": (-51, 9),
                    "V777 Her": (7, 7),
                },
            }
            band = x_column[:2]
            axis.annotate(
                row["wd_class"],
                (row[x_column], row[y_column]),
                xytext=offsets[band][row["wd_class"]],
                textcoords="offset points",
                fontsize=8,
                arrowprops={"arrowstyle": "-", "color": "#898781", "lw": 0.6},
            )
    limits = np.array([0.1, 40.0])
    axis.plot(limits, limits, color="#898781", linewidth=1.2, linestyle="--", zorder=0)
    axis.axvline(2.5, color="#c3c2b7", linewidth=0.9, linestyle=":", zorder=0)
    axis.axhline(2.5, color="#c3c2b7", linewidth=0.9, linestyle=":", zorder=0)
    axis.set(xscale="log", yscale="log", xlim=limits, ylim=limits, title=title, xlabel=xlabel, ylabel=ylabel)
    axis.grid(color="#e1e0d9", linewidth=0.7, alpha=0.8, zorder=0)


def plot_census(census: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 11.0), sharex=False, sharey=False)
    plot_transition(
        axes[0, 0], census, "zg_exposure_ratio", "zg_nightly_ratio",
        "g band — exposure residuals to nightly bins",
        "exposure-level high-frequency sd / median error",
        "nightly sd / median error", True,
    )
    plot_transition(
        axes[0, 1], census, "zg_nightly_ratio", "zg_monthly_ratio",
        "g band — nightly to monthly bins",
        "nightly sd / median error", "monthly sd / median error", False,
    )
    plot_transition(
        axes[1, 0], census, "zr_exposure_ratio", "zr_nightly_ratio",
        "r band — exposure residuals to nightly bins",
        "exposure-level high-frequency sd / median error",
        "nightly sd / median error", True,
    )
    plot_transition(
        axes[1, 1], census, "zr_nightly_ratio", "zr_monthly_ratio",
        "r band — nightly to monthly bins",
        "nightly sd / median error", "monthly sd / median error", False,
    )
    handles, labels = axes[0, 0].get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    fig.legend(unique.values(), unique.keys(), loc="upper center", ncol=3, frameon=False)
    fig.suptitle(
        "ZTF white-dwarf variability census — three cadences × two bands",
        fontsize=14,
        y=0.975,
    )
    fig.text(0.5, 0.012, "Dotted lines: census threshold 2.5. Dashed diagonal: unchanged ratio after binning.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=170, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster", type=Path, default=ROOT / "data/roster/jestin2026_roster.csv")
    parser.add_argument("--exposures", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--nightly", type=Path, default=ROOT / "data/raw/ztf_wd_panel.csv")
    parser.add_argument("--table", type=Path, default=ROOT / "data/raw/variance_census.csv")
    parser.add_argument("-o", "--out", type=Path, default=ROOT / "figures/variance_census.png")
    args = parser.parse_args()

    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    exposures = pd.read_csv(
        args.exposures,
        usecols=["source_id", "band", "night_mjd", "mag", "magerr"],
        dtype={"source_id": str},
        low_memory=False,
    )
    nightly = pd.read_csv(args.nightly, dtype={"source_id": str})
    census = build_census(roster, exposures, nightly)
    args.table.parent.mkdir(parents=True, exist_ok=True)
    census.to_csv(args.table, index=False)
    plot_census(census, args.out)
    print(f"wrote {args.table} ({len(census)} stars)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
