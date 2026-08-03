#!/usr/bin/env python3
"""Validate the completed full-catalog rebuild against its execution plan."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RATIO_COLUMNS = [
    f"{band}_{cadence}_ratio"
    for band in ("zg", "zr")
    for cadence in ("exposure", "nightly", "monthly")
]
SANITY_IDS = {
    "3345661467822106624",
    "6555925496084361344",
    "103999471976858496",
    "2833849800205759360",
}


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

    roster = pd.read_csv(
        ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
        dtype={"source_id": str},
    )
    fetch = json.loads(
        (ROOT / "data/raw/catalog_lc_cache/fetch_manifest.json").read_text(encoding="utf-8")
    )
    census_manifest = json.loads(
        (args.run_dir / "census_manifest.json").read_text(encoding="utf-8")
    )
    qc = pd.read_csv(args.run_dir / "crossmatch_qc.csv", dtype={"source_id": str})
    census = pd.read_csv(
        args.run_dir / "census_full_catalog.csv",
        dtype={"source_id": str},
    )
    ls = pd.read_csv(args.run_dir / "ls_full_catalog.csv", dtype={"source_id": str})
    sanity = json.loads((args.run_dir / "ls/sanity_gates.json").read_text(encoding="utf-8"))
    control_coverage = json.loads(
        (args.run_dir / "control_coverage.json").read_text(encoding="utf-8")
    )
    bootstrap = pd.read_csv(
        args.run_dir / "bootstrap_top_candidates.csv",
        dtype={"source_id": str},
    )
    fit = json.loads(
        (args.run_dir / "panelcast_full_fit/fit_summary.json").read_text(encoding="utf-8")
    )
    magnitude_audit = pd.read_csv(
        args.run_dir / "panelcast_crossmatch_magnitude_audit.csv",
        dtype={"source_id": str},
    )

    crossmatched = as_bool(qc["crossmatched"].fillna(False))
    known = as_bool(qc["known_roster"])
    surviving = ls[ls["blind_status"].isin(["confirmed", "candidate"])]
    expected_bootstrap = min(30, len(surviving))
    scratch_power = list((args.run_dir / "ls/work").rglob("*.power.dat"))
    error_records = list((args.run_dir / "ls/stars").glob("*.error.json"))
    unavailable_rr = qc[qc["source_id"].eq("6555925496084361344")].iloc[0]
    checks = {
        "stage_b_has_1423_unique_sources": len(roster) == 1423
        and roster["source_id"].nunique() == 1423,
        "stage_b_core_is_1359": int(as_bool(roster["in_core"]).sum()) == 1359,
        "all_20_known_members_present": int(as_bool(roster["known_roster"]).sum()) == 20,
        "fetch_complete_without_silent_failures": fetch["targets"] == 1423
        and fetch["failed"] == 0
        and fetch["fetched"] + fetch["skipped"] == 1423,
        "qc_covers_every_candidate": len(qc) == 1423 and qc["source_id"].nunique() == 1423,
        "crossmatch_count_matches_manifest": int(crossmatched.sum())
        == census_manifest["crossmatched_count"],
        "crossmatch_neighborhood_is_plausible": 800 <= int(crossmatched.sum()) <= 1000,
        "known_roster_crossmatch_complete_or_documented": (
            int((known & crossmatched).sum()) == 19
            and int(unavailable_rr["raw_rows"]) == 0
            and str(unavailable_rr["crossmatched"]).lower() != "true"
            and control_coverage["verdict"] == "unavailable_no_ztf_rows"
            and [check["rows"] for check in control_coverage["checks"]] == [0, 0]
        ),
        "census_one_row_per_crossmatch": len(census) == int(crossmatched.sum())
        and census["source_id"].nunique() == len(census),
        "all_six_census_ratios_finite": np.isfinite(census[RATIO_COLUMNS].to_numpy()).all(),
        "bjd_exposure_shard_per_crossmatch": len(list((args.run_dir / "exposure_stars").glob("*.csv.gz")))
        == int(crossmatched.sum()),
        "ls_one_complete_row_per_crossmatch": len(ls) == int(crossmatched.sum())
        and as_bool(ls["ls_complete"]).all(),
        "ls_status_taxonomy_valid": set(ls["blind_status"]) <= {
            "confirmed",
            "candidate",
            "not_detected",
        },
        "available_sanity_gates_passed_and_missing_documented": (
            sanity["all_available_passed"]
            and sanity["available_checks"] == 3
            and sanity["unavailable_checks"] == 1
            and set(sanity["checks"]) == SANITY_IDS
            and sanity["checks"]["6555925496084361344"]["status"]
            == "unavailable_no_ztf_rows"
        ),
        "bootstrap_top_candidates_complete": len(bootstrap) == expected_bootstrap
        and bootstrap["bootstrap_resamples"].ge(100).all(),
        "no_periodogram_scratch_files": not scratch_power,
        "no_period_search_error_records": not error_records,
        "panelcast_magnitude_mismatch_audit_complete": (
            len(magnitude_audit) == int(crossmatched.sum())
            and magnitude_audit["source_id"].nunique() == len(magnitude_audit)
            and int(as_bool(magnitude_audit["magnitude_mismatch_flag"]).sum()) == 20
        ),
        "panelcast_attempt_policy_respected": 1 <= fit["attempts"] <= 2
        and fit["status"] in {"converged", "failed_diagnostics", "timebox_exceeded"},
        "panelcast_diagnostics_recorded": all(
            key in fit for key in ("max_rhat", "min_bulk_ess", "divergences")
        ),
        "required_figures_present": all(
            (args.run_dir / path).exists()
            for path in (
                "figures/census_full_catalog.png",
                "figures/ls_period_amplitude.png",
            )
        ),
        "incremental_results_present": (args.run_dir / "CATALOG_RESULTS.md").exists(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    failed = [name for name, passed in checks.items() if not passed]
    payload = {
        "checks": checks,
        "all_passed": not failed,
        "failed": failed,
        "counts": {
            "stage_b": len(roster),
            "crossmatched": int(crossmatched.sum()),
            "census_variable": int(as_bool(census["census_variable"]).sum()),
            "ls_confirmed": int(ls["blind_status"].eq("confirmed").sum()),
            "ls_candidates": int(ls["blind_status"].eq("candidate").sum()),
            "bootstrap": len(bootstrap),
        },
    }
    (args.run_dir / "acceptance.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
