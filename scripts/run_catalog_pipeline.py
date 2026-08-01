#!/usr/bin/env python3
"""Execute Stage C in census, Lomb–Scargle, then panelcast priority order."""

import json
from pathlib import Path
import subprocess
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "outputs/catalog/2026-08-01_full"
FETCH_MANIFEST = ROOT / "data/raw/catalog_lc_cache/fetch_manifest.json"
STATE_PATH = RUN_DIR / "pipeline_state.json"


def write_state(stage: str, status: str, detail: str = "") -> None:
    payload = {"stage": stage, "status": status, "detail": detail}
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[pipeline] {stage}: {status} {detail}", flush=True)


def run_stage(name: str, *arguments: str) -> None:
    write_state(name, "running")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / arguments[0]), *arguments[1:]],
        cwd=ROOT,
        check=True,
    )
    write_state(name, "complete")


def wait_for_fetch() -> None:
    write_state("fetch", "waiting", "for 1,423 terminal responses")
    deadline = time.monotonic() + 36 * 60 * 60
    last_count = -1
    while time.monotonic() < deadline:
        count = len(list((ROOT / "data/raw/catalog_lc_cache").glob("*.csv")))
        if count != last_count and (count % 25 == 0 or count == 1423):
            print(f"[pipeline] fetch cache count={count:,}", flush=True)
            last_count = count
        if FETCH_MANIFEST.exists():
            manifest = json.loads(FETCH_MANIFEST.read_text(encoding="utf-8"))
            if manifest.get("targets") == 1423:
                if manifest.get("failed", 0):
                    write_state("fetch", "retrying", f"{manifest['failed']} terminal failures")
                    subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts/fetch_catalog_lightcurves.py"),
                            "--sleep",
                            "1.25",
                        ],
                        cwd=ROOT,
                        check=True,
                    )
                    manifest = json.loads(FETCH_MANIFEST.read_text(encoding="utf-8"))
                if manifest.get("failed", 0) == 0 and (
                    manifest.get("fetched", 0) + manifest.get("skipped", 0) == 1423
                ):
                    write_state("fetch", "complete")
                    return
        time.sleep(30)
    raise TimeoutError("catalog fetch did not complete within 36 hours")


def validate_census_gate() -> None:
    manifest = json.loads((RUN_DIR / "census_manifest.json").read_text(encoding="utf-8"))
    count = int(manifest["crossmatched_count"])
    known = int(manifest["known_roster_crossmatched"])
    if not 800 <= count <= 1000:
        raise RuntimeError(f"crossmatch count {count} lies outside the planned neighborhood")
    if known != 20:
        raise RuntimeError(f"only {known}/20 known roster stars crossmatched")
    census = pd.read_csv(RUN_DIR / "census_full_catalog.csv")
    if census.isna().any().loc[
        [
            f"{band}_{cadence}_ratio"
            for band in ("zg", "zr")
            for cadence in ("exposure", "nightly", "monthly")
        ]
    ].any():
        raise RuntimeError("at least one crossmatched star lacks a census ratio")
    write_state("census_gate", "complete", f"{count} crossmatches; 20/20 known")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    wait_for_fetch()
    run_stage(
        "census",
        "build_catalog_panels.py",
        "--out-dir",
        str(RUN_DIR),
    )
    run_stage(
        "census_figure",
        "plot_catalog_census.py",
        "--census",
        str(RUN_DIR / "census_full_catalog.csv"),
        "--out",
        str(RUN_DIR / "figures/census_full_catalog.png"),
    )
    run_stage(
        "census_report",
        "generate_catalog_results.py",
        "--run-dir",
        str(RUN_DIR),
    )
    validate_census_gate()

    run_stage(
        "lomb_scargle",
        "run_catalog_lomb_scargle.py",
        "--run-dir",
        str(RUN_DIR),
    )
    run_stage(
        "bootstrap",
        "run_catalog_bootstrap.py",
        "--run-dir",
        str(RUN_DIR),
    )
    run_stage(
        "ls_figure",
        "plot_catalog_lomb_scargle.py",
        "--run-dir",
        str(RUN_DIR),
    )
    run_stage(
        "ls_report",
        "generate_catalog_results.py",
        "--run-dir",
        str(RUN_DIR),
    )

    run_stage(
        "panelcast_data",
        "build_catalog_panelcast_data.py",
        "--run-dir",
        str(RUN_DIR),
    )
    run_stage(
        "panelcast",
        "run_catalog_panelcast.py",
        "--run-dir",
        str(RUN_DIR),
    )
    run_stage(
        "final_report",
        "generate_catalog_results.py",
        "--run-dir",
        str(RUN_DIR),
    )
    run_stage(
        "acceptance",
        "validate_catalog_rebuild.py",
        "--run-dir",
        str(RUN_DIR),
    )
    write_state("pipeline", "complete")


if __name__ == "__main__":
    main()
