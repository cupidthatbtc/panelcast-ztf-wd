#!/usr/bin/env python3
"""CLI-identity gate: the campaign import path is the frozen code path.

Runs the same shard twice:
  A. analyze_star imported through frozen_api (exactly what the campaign
     driver does), in this process;
  B. analyze_star imported directly from scripts/ in a FRESH interpreter with
     frozen_api never imported (exactly what the frozen CLI does internally).
Byte-compares the two result files, then repeats arm A to prove determinism.

This is the honest substitute for "run the frozen CLI on campaign shards":
the CLI's main() cannot run on campaign data because it merges against the WD
roster and rewrites the published catalog table.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from frozen_api import SCRIPTS_DIR, analyze_star, assert_frozen, env_versions

DIRECT_RUNNER = """
import sys
sys.path.insert(0, {scripts_dir!r})
from run_catalog_lomb_scargle import analyze_star
analyze_star({source_id!r}, {shard!r}, {result!r}, {work!r}, ("low", "high"))
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=Path, required=True,
                        help="one <source_id>.csv.gz exposure shard")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    assert_frozen()
    source_id = args.shard.name.split(".csv")[0]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        arm: args.out_dir / f"{source_id}.{arm}.json" for arm in ("api", "cli", "api2")
    }
    for path in paths.values():
        path.unlink(missing_ok=True)

    analyze_star(source_id, str(args.shard), str(paths["api"]),
                 str(args.out_dir / "work_api"), ("low", "high"))
    script = DIRECT_RUNNER.format(
        scripts_dir=str(SCRIPTS_DIR),
        source_id=source_id,
        shard=str(args.shard),
        result=str(paths["cli"]),
        work=str(args.out_dir / "work_cli"),
    )
    subprocess.run([sys.executable, "-c", script], check=True)
    analyze_star(source_id, str(args.shard), str(paths["api2"]),
                 str(args.out_dir / "work_api2"), ("low", "high"))

    api, cli, api2 = (paths[arm].read_bytes() for arm in ("api", "cli", "api2"))
    report = {
        "gate": "verify_cli_identity",
        "source_id": source_id,
        "api_equals_cli": api == cli,
        "deterministic": api == api2,
        "passed": api == cli == api2,
        "env": env_versions(),
    }
    report_path = args.out_dir / f"{source_id}.identity_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
