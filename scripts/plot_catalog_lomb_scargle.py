#!/usr/bin/env python3
"""Plot full-catalog confirmed periods and write census/L-S disagreements."""

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
GRAY = "#8d8b84"


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().eq("true")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    args = parser.parse_args()

    ls = pd.read_csv(args.run_dir / "ls_full_catalog.csv", dtype={"source_id": str})
    census = pd.read_csv(
        args.run_dir / "census_full_catalog.csv",
        dtype={"source_id": str},
    )
    merged = ls.merge(
        census[["source_id", "census_variable", "census_verdict"]],
        on="source_id",
        how="left",
        validate="one_to_one",
    )
    merged["census_variable"] = as_bool(merged["census_variable"])
    merged["known_roster"] = as_bool(merged["known_roster"])
    merged["disagreement"] = np.select(
        [
            merged["blind_status"].eq("confirmed") & ~merged["census_variable"],
            ~merged["blind_status"].eq("confirmed") & merged["census_variable"],
        ],
        ["ls_only", "census_only"],
        default="agreement",
    )
    merged[merged["disagreement"].ne("agreement")].sort_values(
        ["disagreement", "source_id"]
    ).to_csv(args.run_dir / "ls_census_disagreement.csv", index=False)

    confirmed = merged[merged["blind_status"].eq("confirmed")].copy()
    confirmed["amplitude_mmag"] = confirmed[
        ["zg_amplitude_mmag", "zr_amplitude_mmag"]
    ].max(axis=1)
    ordinary = confirmed[~confirmed["known_roster"]]
    known = confirmed[confirmed["known_roster"]]

    fig, axis = plt.subplots(figsize=(10.5, 7.8))
    for census_value, color, label in (
        (False, GRAY, "census quiet"),
        (True, BLUE, "census variable"),
    ):
        subset = ordinary[ordinary["census_variable"].eq(census_value)]
        axis.scatter(
            subset["best_period_days"],
            subset["amplitude_mmag"],
            c=color,
            s=30,
            alpha=0.7,
            linewidth=0,
            rasterized=True,
            label=f"{label} ({len(subset):,})",
        )
    axis.scatter(
        known["best_period_days"],
        known["amplitude_mmag"],
        c=ORANGE,
        marker="*",
        s=145,
        edgecolor="black",
        linewidth=0.55,
        zorder=5,
        label=f"pilot roster ({len(known):,})",
    )
    axis.set(
        xscale="log",
        yscale="log",
        xlabel="best alias-vetted period (days)",
        ylabel="largest confirming semiamplitude (mmag)",
        title="Full-catalog blind Lomb–Scargle confirmations",
    )
    axis.grid(color="#deddd7", linewidth=0.7, alpha=0.7)
    axis.legend(frameon=False)
    fig.tight_layout()
    output = args.run_dir / "figures/ls_period_amplitude.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, facecolor="white")
    plt.close(fig)
    print(f"wrote {output} ({len(confirmed):,} confirmed periods)")
    print(f"wrote {args.run_dir / 'ls_census_disagreement.csv'}")


if __name__ == "__main__":
    main()
