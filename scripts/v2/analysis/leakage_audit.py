#!/usr/bin/env python3
"""High-pass LEAKAGE AUDIT (V2_PLAN.md §6, descriptive; G-review finding 10).

The v2 high pass subtracts a slow running median, so 0.03–24 c/d variability
stays in the series and can alias into the 24–1440 c/d band through the
spectral window. This audit measures it on real dev windows: a pure
LOW-frequency sinusoid (default 0.7 c/d, 20 mmag, same phase in both bands)
is injected into each listed dev D3 shard; v2 is run on the injected shard
and the high-pass outcome is compared with the star's un-injected v2 result
(the dev run's JSON): high-pass status transitions, whether the high-pass
best frequency is a solar/sidereal partner of the injected frequency, and
the low-pass detection of the injection itself.

Compute: one v2 run per listed star. Output: leakage_audit_per_star.csv,
leakage_audit_summary.json (+ input SHAs). Purely descriptive.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

V2_DIR = Path(__file__).resolve().parents[1]   # scripts/v2 (this file lives in scripts/v2/analysis,
sys.path.insert(0, str(V2_DIR))                # outside the v2 code digest: analysis only)
from analyze_star_v2 import analyze_star_v2  # noqa: E402
from v2_common import DEFAULT, overall_result, with_overrides  # noqa: E402
from window import is_alias_of_stronger_v2  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inject(shard: Path, out: Path, frequency: float, amplitude_mmag: float, phase_cycles: float) -> None:
    frame = pd.read_csv(shard, dtype={"source_id": str, "band": str, "oid": str})
    t = frame["bjd_tdb"].to_numpy(dtype=float)
    frame["mag"] = frame["mag"].to_numpy(dtype=float) + (amplitude_mmag / 1000.0) * np.sin(
        2.0 * np.pi * (frequency * t + phase_cycles))
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as handle:
        frame.to_csv(handle, index=False, lineterminator="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stars-file", type=Path, required=True, help="dev D3 ids to audit (subset of d3_dev.txt)")
    parser.add_argument("--shards-dir", type=Path, required=True)
    parser.add_argument("--reference-stars-dir", type=Path, required=True, help="the dev run's v2 JSONs")
    parser.add_argument("--constants", default=None)
    parser.add_argument("--frequency", type=float, default=0.7)
    parser.add_argument("--amplitude-mmag", type=float, default=20.0)
    parser.add_argument("--phase-cycles", type=float, default=0.13)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    constants = DEFAULT
    if args.constants:
        payload = json.loads(Path(args.constants).read_text()) if Path(args.constants).exists() else json.loads(args.constants)
        constants = with_overrides(DEFAULT, **payload.get("overrides", payload))
    dev_ids = {l.strip() for l in (V2_DIR.parents[1] / "generalization/v2/d3_dev.txt").read_text().splitlines() if l.strip()}
    ids = [l.strip() for l in args.stars_file.read_text().splitlines() if l.strip()]
    if not set(ids) <= dev_ids:
        raise SystemExit("the leakage audit runs on dev ids only")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows, inputs = [], {}
    for sid in ids:
        reference_path = args.reference_stars_dir / f"{sid}.json"
        if not reference_path.exists():
            continue
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        inputs[str(reference_path)] = sha256_file(reference_path)
        shard = args.shards_dir / f"{sid}.csv.gz"
        injected = args.out_dir / "shards" / f"{sid}.csv.gz"
        inject(shard, injected, args.frequency, args.amplitude_mmag, args.phase_cycles)
        result_path = args.out_dir / "stars" / f"{sid}.json"
        result = analyze_star_v2(sid, str(injected), str(result_path), str(args.work_root), ("low", "high"), constants)
        tolerance = constants.tolerance_over_baseline / float(result["baseline_days"])
        high_ref, high_new = reference["passes"]["high"], result["passes"]["high"]
        low_new = result["passes"]["low"]
        f_high = high_new.get("frequency_per_day")
        rows.append({
            "sid": sid,
            "high_status_reference": high_ref["status"], "high_status_injected": high_new["status"],
            "high_frequency_injected": f_high,
            "high_best_is_partner_of_injection": bool(f_high) and is_alias_of_stronger_v2(
                float(f_high), [args.frequency], tolerance),
            "high_cross_pass_partners_recorded": int(sum(len(v) for v in high_new["v2"].get("cross_pass_stronger", {}).values())),
            "low_status_injected": low_new["status"],
            "low_detects_injection": bool(low_new.get("frequency_per_day")) and abs(
                float(low_new["frequency_per_day"]) - args.frequency) <= tolerance,
            "best_status_reference": overall_result(reference)["blind_status"],
            "best_status_injected": overall_result(result)["blind_status"],
        })
    table = pd.DataFrame(rows)
    table.to_csv(args.out_dir / "leakage_audit_per_star.csv", index=False, lineterminator="\n")
    summary = {
        "n": len(table),
        "injection": {"frequency_per_day": args.frequency, "amplitude_mmag": args.amplitude_mmag,
                      "phase_cycles": args.phase_cycles},
        "high_confirmed_reference": int((table["high_status_reference"] == "confirmed").sum()) if len(table) else 0,
        "high_confirmed_injected": int((table["high_status_injected"] == "confirmed").sum()) if len(table) else 0,
        "high_new_confirmations_that_are_partners": int(((table["high_status_reference"] != "confirmed")
                                                         & (table["high_status_injected"] == "confirmed")
                                                         & table["high_best_is_partner_of_injection"]).sum()) if len(table) else 0,
        "low_detects_injection": int(table["low_detects_injection"].sum()) if len(table) else 0,
        "constants": constants.as_dict(),
        "inputs_sha256_digest": hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
        "script_sha256": sha256_file(Path(__file__).resolve()),
    }
    (args.out_dir / "leakage_audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
