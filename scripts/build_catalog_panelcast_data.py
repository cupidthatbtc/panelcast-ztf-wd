#!/usr/bin/env python3
"""Build the full-catalog monthly g-band panelcast input and descriptor."""

import argparse
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR_TEMPLATE = """# Rebuilt Jestin+2026 candidate catalog — monthly ZTF g photometry.
# Stage A reproduces 22,264 exactly. Stage B has 1,423 candidates using the
# inferred phot_g_n_obs / 9 convention and m=1.1896 (paper: 1.25); 1,359 are
# shared by all four calibrated recipe variants. See catalog-rebuild/CATALOG_PLAN.md.
name: ztf_wd_catalog_monthly

raw_path_env: ZTF_WD_CATALOG_MONTHLY_PATH
raw_path_default: outputs/catalog/2026-08-01_full/panelcast_zg_monthly.csv
encoding: utf-8
raw_column_map: {{}}
required_raw_columns:
  - source_id
  - month_id
  - month_date
  - mag_binned
  - n_exp
  - wd_class
  - year
optional_raw_columns:
  - mag_err

entity_col: source_id
event_col: month_id
entity_group_col: wd_class
date_col: month_date
parsed_date_col: month_date_parsed
year_col: year
date_format: "%Y-%m-%d"

target_col: mag_binned
target_bounds: [{lower:.1f}, {upper:.1f}]
model_prefix: ztfgc
n_obs_col: n_exp
n_obs_is_aggregation_count: true
secondary_target_col: null
secondary_prefix: null
secondary_n_obs_col: null

multi_entity_col: null
unknown_entity_sentinel: null
min_year: 2018
min_obs_thresholds: [1]
primary_min_obs: 1
processed_name_template: "ztfgcm_minobs_{{min_ratings}}"

feature_packs: []
feature_blocks:
  - name: temporal
  - name: entity_history
ablation_groups:
  temporal: [temporal]
  artist: [entity_history]
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    parser.add_argument(
        "--descriptor",
        type=Path,
        default=ROOT / "configs/datasets/ztf_wd_catalog_monthly.yaml",
    )
    args = parser.parse_args()

    monthly = pd.read_csv(
        args.run_dir / "monthly_panel.csv.gz",
        dtype={"source_id": str},
    )
    roster = pd.read_csv(
        ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
        dtype={"source_id": str},
    )
    qc = pd.read_csv(
        args.run_dir / "crossmatch_qc.csv",
        dtype={"source_id": str},
    )
    panel = monthly[monthly["band"].eq("zg")].merge(
        roster[["source_id", "wd_class", "gaia_g_mag"]],
        on="source_id",
        how="left",
        validate="many_to_one",
    )
    event_counts = panel.groupby("source_id")["month_id"].nunique()
    keep = set(event_counts[event_counts >= 2].index)
    panel = panel[panel["source_id"].isin(keep)].copy()
    audit = (
        panel.groupby("source_id", as_index=False)
        .agg(
            gaia_g_mag=("gaia_g_mag", "first"),
            ztf_g_median=("mag_binned", "median"),
            ztf_g_min=("mag_binned", "min"),
            ztf_g_max=("mag_binned", "max"),
            monthly_events=("month_id", "size"),
        )
        .merge(
            qc[["source_id", "nearest_separation_arcsec"]],
            on="source_id",
            how="left",
            validate="one_to_one",
        )
    )
    audit["ztf_minus_gaia_g"] = audit["ztf_g_median"] - audit["gaia_g_mag"]
    audit["magnitude_mismatch_flag"] = audit["ztf_minus_gaia_g"].abs().gt(1.0)
    audit.to_csv(args.run_dir / "panelcast_crossmatch_magnitude_audit.csv", index=False)

    panel["source_id"] = "GaiaDR3_" + panel["source_id"]
    panel["month_date"] = pd.to_datetime(panel["month_date"]).dt.strftime("%Y-%m-%d")
    columns = [
        "source_id",
        "mag_binned",
        "mag_err",
        "n_exp",
        "n_nights",
        "wd_class",
        "month_date",
        "month_id",
        "year",
    ]
    output = args.run_dir / "panelcast_zg_monthly.csv"
    panel[columns].sort_values(["source_id", "month_id"]).to_csv(output, index=False)

    lower = math.floor(float(panel["mag_binned"].min()) - 0.5)
    upper = math.ceil(float(panel["mag_binned"].max()) + 0.5)
    args.descriptor.parent.mkdir(parents=True, exist_ok=True)
    args.descriptor.write_text(
        DESCRIPTOR_TEMPLATE.format(lower=lower, upper=upper),
        encoding="utf-8",
    )
    print(
        f"wrote {output} ({len(panel):,} events; {panel['source_id'].nunique():,} entities)"
    )
    print(
        f"wrote {args.run_dir / 'panelcast_crossmatch_magnitude_audit.csv'} "
        f"({int(audit['magnitude_mismatch_flag'].sum())} sources differ from Gaia G by >1 mag)"
    )
    print(f"wrote {args.descriptor} (target bounds {lower:.1f}..{upper:.1f})")


if __name__ == "__main__":
    main()
