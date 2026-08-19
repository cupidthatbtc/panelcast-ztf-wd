#!/usr/bin/env python3
"""Add static Gaia covariates to the full-catalog monthly panel."""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    args = parser.parse_args()

    panel = pd.read_csv(args.run_dir / "panelcast_zg_monthly.csv", dtype={"source_id": str})
    roster = pd.read_csv(
        ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
        dtype={"source_id": str},
    )
    roster["source_id"] = "GaiaDR3_" + roster["source_id"]
    augmented = panel.merge(
        roster[["source_id", "gaia_g_mag", "bp_rp"]],
        on="source_id",
        how="left",
        validate="many_to_one",
    )
    if augmented[["gaia_g_mag", "bp_rp"]].isna().any().any():
        raise ValueError("Gaia covariates are missing for at least one panel entity")

    output_dir = args.run_dir / "hardening"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "panelcast_zg_monthly_gaia.csv"
    augmented.to_csv(output, index=False)
    print(
        f"wrote {output} ({len(augmented):,} events; "
        f"{augmented['source_id'].nunique():,} entities)"
    )


if __name__ == "__main__":
    main()
