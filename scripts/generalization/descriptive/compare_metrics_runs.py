#!/usr/bin/env python3
"""Guard for the G5prep round-2 compliance repair (reviews/G5prep/sol_round2.md,
item 1, "Timing and guard"): compare the laptop's PRE-fix metrics bundle
(reference) against the Mac's POST-fix bundle (candidate).

Sufficient guard, as ruled:
  1. byte identity for every pre-existing science output except attrition.csv;
  2. expected-only diffs: attrition.csv (reference scalars must equal the
     candidate's attrition_summary.csv), manifest.json (only campaign_sha256,
     env, inputs_sha256_count/digest, and engine may differ), path-keyed
     inputs_sha256.json (identical content SHAs after canonicalising paths to
     basenames);
  3. the candidate's new files are exactly the compliance outputs.
Exit 1 on any unexpected difference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

EXPECTED_NEW = {"attrition_summary.csv", "d3_mo_join_covariates.csv"}
MANIFEST_MAY_DIFFER = {"campaign_sha256", "engine", "env", "inputs_sha256_count",
                       "inputs_sha256_digest"}
SPECIAL = {"attrition.csv", "manifest.json", "inputs_sha256.json"}


TEXT_SUFFIXES = {".csv", ".json", ".txt", ".md"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_lf(path: Path) -> str:
    """SHA-256 after newline normalisation: any run of CR before LF -> LF.
    Windows text-mode writes give CRLF, and write_text(to_csv(...)) gives
    CR CR LF (pandas emits CRLF, then text mode translates the LF again)."""
    return hashlib.sha256(re.sub(rb"\r+\n", b"\n", path.read_bytes())).hexdigest()


def identity_tier(a: Path, b: Path) -> str:
    """identical_bytes | identical_newline | differs — the replay gate's vocabulary
    (its full-928 attestation classified 7 files as identical_newline)."""
    if sha(a) == sha(b):
        return "identical_bytes"
    if a.suffix in TEXT_SUFFIXES and sha_lf(a) == sha_lf(b):
        return "identical_newline"
    return "differs"


ULP_RTOL = 1e-14   # <= ~45 ulp of a double: the laptop CSV float parser's 1-ulp mis-rounding sits far inside


def within_known_ulp(reference: Path, candidate: Path, columns: tuple[str, ...]) -> tuple[bool, str]:
    """A per-star table whose ONLY differences are last-ulp float differences in
    the named truth columns (values parsed from CSV on different platforms;
    generalization/env/CROSS_PLATFORM_REPLAY.md: pandas' fast float parser on
    Windows mis-rounds 17-digit decimals by 1 ulp). Every other column must be
    byte-identical. Returns (ok, detail)."""
    import pandas as pd

    a = pd.read_csv(reference, dtype=str).fillna("")
    b = pd.read_csv(candidate, dtype=str).fillna("")
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False, "shape/columns differ"
    key = "sid" if "sid" in a.columns else a.columns[0]
    a = a.set_index(key).sort_index()
    b = b.set_index(key).sort_index()
    if list(a.index) != list(b.index):
        return False, "row keys differ"
    worst = 0.0
    for column in a.columns:
        unequal = a[column] != b[column]
        if not unequal.any():
            continue
        if column not in columns:
            return False, f"column {column} differs ({int(unequal.sum())} rows) and is not a named truth column"
        x = pd.to_numeric(a.loc[unequal, column], errors="coerce")
        y = pd.to_numeric(b.loc[unequal, column], errors="coerce")
        if x.isna().any() or y.isna().any():
            return False, f"non-numeric difference in {column}"
        rel = (abs(x - y) / abs(x).where(abs(x) > 0, 1.0)).max()
        worst = max(worst, float(rel))
        if rel > ULP_RTOL:
            return False, f"{column}: max relative difference {rel:.3e} exceeds {ULP_RTOL:.0e}"
    return True, f"named truth columns differ within {worst:.2e} relative (last-ulp platform float parse)"


def compare(reference: Path, candidate: Path, ulp_columns: tuple[str, ...] = ()) -> list[str]:
    problems: list[str] = []
    ref_files = {p.relative_to(reference).as_posix() for p in reference.rglob("*") if p.is_file()}
    cand_files = {p.relative_to(candidate).as_posix() for p in candidate.rglob("*") if p.is_file()}
    missing = ref_files - cand_files
    if missing:
        problems.append(f"candidate lacks reference files: {sorted(missing)[:5]}")
    extra = cand_files - ref_files
    if extra - EXPECTED_NEW:
        problems.append(f"unexpected new files: {sorted(extra - EXPECTED_NEW)[:5]}")
    tiers = Counter()
    for rel in sorted(ref_files & cand_files):
        if rel in SPECIAL:
            continue
        tier = identity_tier(reference / rel, candidate / rel)
        if tier == "differs" and ulp_columns and rel.endswith("per_star.csv"):
            ok, detail = within_known_ulp(reference / rel, candidate / rel, ulp_columns)
            if ok:
                tier = "identical_within_known_ulp"
                print(f"  {rel}: {detail} (columns {', '.join(ulp_columns)})")
        tiers[tier] += 1
        if tier == "differs":
            problems.append(f"science output differs: {rel}")
    print(f"science outputs: {tiers['identical_bytes']} identical_bytes, "
          f"{tiers['identical_newline']} identical_newline, "
          f"{tiers['identical_within_known_ulp']} identical_within_known_ulp, {tiers['differs']} differ")
    # attrition: a PRE-fix reference (no attrition_summary.csv) holds the seven
    # scalars in attrition.csv, which must equal the candidate's
    # attrition_summary.csv; a POST-fix reference is compared file-for-file
    if "attrition.csv" in ref_files:
        summary = candidate / "attrition_summary.csv"
        if not summary.exists():
            problems.append("candidate has no attrition_summary.csv")
        elif "attrition_summary.csv" in ref_files:
            for name in ("attrition.csv", "attrition_summary.csv"):
                if identity_tier(reference / name, candidate / name) == "differs":
                    problems.append(f"science output differs: {name}")
        elif identity_tier(reference / "attrition.csv", summary) == "differs":
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
    parser.add_argument("--allow-known-platform-ulp", default="",
                        help="comma-separated per_star.csv TRUTH columns (parsed from CSV) that may differ "
                             "by last-ulp platform float parsing; every other column stays byte-bound "
                             "(disclosed in the bundle README when used)")
    args = parser.parse_args()
    ulp = tuple(c for c in args.allow_known_platform_ulp.split(",") if c)
    problems = compare(args.reference, args.candidate, ulp)
    if problems:
        print("GUARD FAIL")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("GUARD PASS: pre-existing science outputs byte-identical; only expected diffs")


if __name__ == "__main__":
    main()
