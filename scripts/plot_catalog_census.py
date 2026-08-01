#!/usr/bin/env python3
"""Plot the full-catalog g-band nightly-to-monthly variance census."""

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
GRAY = "#9b9a94"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--census",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full/census_full_catalog.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full/figures/census_full_catalog.png",
    )
    args = parser.parse_args()

    census = pd.read_csv(args.census, dtype={"source_id": str})
    valid = census[
        np.isfinite(census["zg_nightly_ratio"])
        & np.isfinite(census["zg_monthly_ratio"])
        & census["zg_nightly_ratio"].gt(0)
        & census["zg_monthly_ratio"].gt(0)
    ].copy()
    known = valid[valid["known_roster"].astype(bool)]
    ordinary = valid[~valid["known_roster"].astype(bool)]
    variable = ordinary[ordinary["census_variable"].astype(bool)]
    quiet = ordinary[~ordinary["census_variable"].astype(bool)]

    fig, axis = plt.subplots(figsize=(10.5, 8.2))
    axis.scatter(
        quiet["zg_nightly_ratio"],
        quiet["zg_monthly_ratio"],
        s=18,
        c=GRAY,
        alpha=0.55,
        linewidth=0,
        rasterized=True,
        label=f"not variable at any census cadence ({len(quiet):,})",
    )
    axis.scatter(
        variable["zg_nightly_ratio"],
        variable["zg_monthly_ratio"],
        s=25,
        c=BLUE,
        alpha=0.72,
        linewidth=0,
        rasterized=True,
        label=f"variable at ≥1 cadence/band ({len(variable):,})",
    )
    axis.scatter(
        known["zg_nightly_ratio"],
        known["zg_monthly_ratio"],
        s=125,
        c=ORANGE,
        marker="*",
        edgecolor="black",
        linewidth=0.55,
        zorder=5,
        label=f"pilot roster ({len(known)}/20 crossmatched)",
    )

    values = np.concatenate(
        [valid["zg_nightly_ratio"].to_numpy(), valid["zg_monthly_ratio"].to_numpy()]
    )
    lower = max(0.08, float(np.nanpercentile(values, 0.2)) * 0.75)
    upper = max(10.0, float(np.nanpercentile(values, 99.8)) * 1.5)
    bounds = np.array([lower, upper])
    axis.plot(bounds, bounds, color="#52514d", linestyle="--", linewidth=1.0)
    axis.axvline(2.5, color="#52514d", linestyle=":", linewidth=1.0)
    axis.axhline(2.5, color="#52514d", linestyle=":", linewidth=1.0)
    axis.set(
        xscale="log",
        yscale="log",
        xlim=bounds,
        ylim=bounds,
        xlabel="nightly g-band scatter / median reported error",
        ylabel="monthly g-band scatter / median nightly error",
        title="Rebuilt ZTF white-dwarf catalog: variability across binning scales",
    )
    axis.grid(color="#deddd7", linewidth=0.7, alpha=0.7)
    axis.legend(loc="upper left", frameon=False)
    fig.text(
        0.5,
        0.015,
        "Dotted: 2.5 census threshold · dashed: unchanged ratio after monthly binning",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180, facecolor="white")
    plt.close(fig)
    print(f"wrote {args.out} ({len(valid):,} plotted stars)")


if __name__ == "__main__":
    main()
