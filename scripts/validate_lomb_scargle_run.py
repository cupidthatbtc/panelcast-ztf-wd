#!/usr/bin/env python3
"""Validate the Lomb–Scargle run against the plan's acceptance checklist."""

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    args = parser.parse_args()

    smoke = json.loads((ROOT / "outputs/ls/smoke_test.json").read_text(encoding="utf-8"))
    controls = json.loads((args.run_dir / "positive_controls.json").read_text(encoding="utf-8"))
    qc = pd.read_csv(ROOT / "data/raw/ztf_wd_exposure_qc.csv", dtype={"source_id": str})
    manifest = json.loads((args.run_dir / "manifest.json").read_text(encoding="utf-8"))
    master = pd.read_csv(args.run_dir / "master_table.csv", dtype={"source_id": str})
    directed = pd.read_csv(args.run_dir / "directed_search.csv", dtype={"source_id": str})
    injections = pd.read_csv(args.run_dir / "injection_recovery.csv")
    attenuation = pd.read_csv(args.run_dir / "attenuation.csv", dtype={"source_id": str})
    candidates = pd.read_csv(args.run_dir / "candidates.csv", dtype={"source_id": str})
    bootstrap_path = args.run_dir / "bootstrap_fap.csv"
    bootstrap = (
        pd.read_csv(bootstrap_path, dtype={"source_id": str})
        if bootstrap_path.exists()
        else pd.DataFrame()
    )
    confirmed_count = candidates[candidates["status"] == "confirmed"]["source_id"].nunique()
    surviving_count = candidates[candidates["status"].isin(["confirmed", "candidate"])][
        "source_id"
    ].nunique()

    checks = {
        "smoke_test_passed": bool(smoke["passed"]),
        "rr_lyrae_control_confirmed": controls[0]["passes"]["low"]["status"] == "confirmed",
        "double_band_control_confirmed": controls[1]["passes"]["low"]["status"] == "confirmed",
        "qc_has_20_stars_x_2_bands": len(qc) == 40 and qc["source_id"].nunique() == 20,
        "bjd_tdb_high_pass": manifest["high_frequency_time_standard"] == "BJD_TDB",
        "master_has_19_unique_stars": len(master) == 19 and master["source_id"].nunique() == 19,
        "four_pulsators_directed": len(directed) == 4 and directed["source_id"].nunique() == 4,
        "injection_three_detectors_full_grid": (
            set(injections["detector"]) == {"lomb_scargle", "nightly_census", "monthly_census"}
            and len(injections) == 75
            and set(injections["n_injections"]) == {40}
        ),
        "attenuation_all_confirmed": len(attenuation) == confirmed_count,
        "bootstrap_all_surviving_candidates": (
            not bootstrap.empty
            and len(bootstrap) == surviving_count
            and bootstrap["bootstrap_resamples"].ge(100).all()
        ),
        "oddball_verdict_present": (args.run_dir / "oddball.csv").exists(),
        "nineteen_periodogram_figures": len(list((args.run_dir / "figures/periodograms").glob("*.png"))) == 19,
        "phase_fold_for_each_confirmed": len(list((args.run_dir / "figures/phase_folds").glob("*.png"))) == confirmed_count,
        "results_written": (args.run_dir / "RESULTS.md").exists(),
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    failed = [name for name, passed in checks.items() if not passed]
    payload = {"checks": checks, "all_passed": not failed, "failed": failed}
    (args.run_dir / "acceptance.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
