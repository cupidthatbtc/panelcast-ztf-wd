#!/usr/bin/env python3
"""Build the Stage C roster from the reconstructed Jestin candidate table."""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates",
        type=Path,
        default=ROOT / "catalog-rebuild/stageB_variable_candidates.csv",
    )
    parser.add_argument(
        "--known-roster",
        type=Path,
        default=ROOT / "data/roster/jestin2026_roster.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
    )
    args = parser.parse_args()

    candidates = pd.read_csv(args.candidates, dtype={"GaiaEDR3": str})
    known = pd.read_csv(args.known_roster, dtype={"source_id": str})
    if len(candidates) != 1423 or candidates["GaiaEDR3"].nunique() != 1423:
        raise ValueError("Stage B must contain 1,423 unique Gaia sources")

    known_columns = [
        "source_id",
        "wd_class",
        "paper_variable",
        "paper_periodic",
        "provenance",
    ]
    roster = candidates.rename(
        columns={
            "GaiaEDR3": "source_id",
            "RA_ICRS": "ra",
            "DE_ICRS": "dec",
            "Gmag": "gaia_g_mag",
            "WDJname": "wdj_name",
        }
    ).merge(known[known_columns], on="source_id", how="left", validate="one_to_one")
    roster["bp_rp"] = roster["BPmag"] - roster["RPmag"]
    roster["known_roster"] = roster["wd_class"].notna()
    roster["wd_class"] = roster["wd_class"].fillna("unclassified")
    roster["provenance"] = roster["provenance"].fillna("stageB_rebuild")
    roster["wdj_name"] = roster["wdj_name"].astype(str).str.strip()

    missing_known = sorted(set(known["source_id"]) - set(roster["source_id"]))
    if missing_known:
        raise ValueError(f"known roster sources absent from Stage B: {missing_known}")
    if int(roster["in_core"].sum()) != 1359:
        raise ValueError("Stage B core membership must contain 1,359 sources")

    columns = [
        "source_id",
        "ra",
        "dec",
        "gaia_g_mag",
        "bp_rp",
        "wdj_name",
        "wd_class",
        "paper_variable",
        "paper_periodic",
        "known_roster",
        "in_core",
        "n_variants",
        "Pwd",
        "sepsi",
        "sigma_G_nobs",
        "provenance",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    roster[columns].sort_values("source_id").to_csv(args.out, index=False)
    print(
        f"wrote {args.out} ({len(roster):,} candidates; "
        f"{int(roster['in_core'].sum()):,} cross-variant core; "
        f"{int(roster['known_roster'].sum())} known roster stars)"
    )


if __name__ == "__main__":
    main()
