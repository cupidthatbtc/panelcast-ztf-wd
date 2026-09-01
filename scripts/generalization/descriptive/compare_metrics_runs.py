#!/usr/bin/env python3
"""Guard for the G5prep round-2 compliance repair (reviews/G5prep/sol_round2.md,
item 1, "Timing and guard"): compare the laptop's PRE-fix metrics bundle
(reference) against the Mac's POST-fix bundle (candidate).

Sufficient guard, as ruled:
  1. byte identity for every pre-existing science output except attrition.csv;
  2. expected-only diffs: attrition.csv (reference scalars must equal the
     candidate's attrition_summary.csv), manifest.json (only campaign_sha256,
     env, inputs_sha256_count/digest may differ), path-keyed inputs_sha256.json
     (identical content SHAs after canonicalising paths to basenames);
  3. the candidate's new files are exactly the compliance outputs.
Exit 1 on any unexpected difference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_NEW = {"attrition_summary.csv", "d3_mo_join_covariates.csv"}
MANIFEST_MAY_DIFFER = {"campaign_sha256", "env", "inputs_sha256_count", "inputs_sha256_digest"}
SPECIAL = {"attrition.csv", "manifest.json", "inputs_sha256.json"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(reference: Path, candidate: Path) -> list[str]:
    problems: list[str] = []
    ref_files = {p.relative_to(reference).as_posix() for p in reference.rglob("*") if p.is_file()}
    cand_files = {p.relative_to(candidate).as_posix() for p in candidate.rglob("*") if p.is_file()}
    missing = ref_files - cand_files
    if missing:
        problems.append(f"candidate lacks reference files: {sorted(missing)[:5]}")
    extra = cand_files - ref_files
    if extra - EXPECTED_NEW:
        problems.append(f"unexpected new files: {sorted(extra - EXPECTED_NEW)[:5]}")
    for rel in sorted(ref_files & cand_files):
        if rel in SPECIAL:
            continue
        if sha(reference / rel) != sha(candidate / rel):
            problems.append(f"science output differs: {rel}")
    # attrition: reference scalars == candidate attrition_summary
    if "attrition.csv" in ref_files:
        summary = candidate / "attrition_summary.csv"
        if not summary.exists():
            problems.append("candidate has no attrition_summary.csv")
        elif sha(reference / "attrition.csv") != sha(summary):
            problems.append("reference attrition.csv != candidate attrition_summary.csv")
    # manifest: only the allowed keys may differ
    if "manifest.json" in ref_files and "manifest.json" in cand_files:
        ref_m = json.loads((reference / "manifest.json").read_text())
        cand_m = json.loads((candidate / "manifest.json").read_text())
        for key in sorted(set(ref_m) | set(cand_m)):
            if key in MANIFEST_MAY_DIFFER:
                continue
            if ref_m.get(key) != cand_m.get(key):
                problems.append(f"manifest key differs: {key}")
    # inputs: identical content SHAs after canonicalising paths
    if "inputs_sha256.json" in ref_files and "inputs_sha256.json" in cand_files:
        def canon(path: Path) -> Counter:
            data = json.loads(path.read_text())
            # laptop keys are Windows paths (backslashes are ONE component on macOS)
            return Counter((k if k.startswith("generation_input:")
                            else k.replace("\\", "/").rsplit("/", 1)[-1], v)
                           for k, v in data.items())
        if canon(reference / "inputs_sha256.json") != canon(candidate / "inputs_sha256.json"):
            problems.append("inputs_sha256.json content SHAs differ after path canonicalisation")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="pre-fix laptop metrics dir")
    parser.add_argument("--candidate", type=Path, required=True, help="post-fix Mac metrics dir")
    args = parser.parse_args()
    problems = compare(args.reference, args.candidate)
    if problems:
        print("GUARD FAIL")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("GUARD PASS: pre-existing science outputs byte-identical; only expected diffs")


if __name__ == "__main__":
    main()
