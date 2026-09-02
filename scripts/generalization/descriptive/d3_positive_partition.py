#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE partition of the D3 confirmed-positive numerator
(ruling: generalization/reviews/G5prep/sol_round2.md, item 3, F01,
ADMIT-DESCRIPTIVE; the positive-class solar-diurnal extension was REFUSED
and is NOT implemented here).

Writes descriptive_postlaunch/d3_confirmed_positive_match_partition.csv.

Frame: all eligible dsct_flag1 positives (n_positive = 610) with
best_status=="confirmed" under rule 1 and best pass. Crossed:

    best_candidate_matches_dominant in
        {direct, harmonic, window_alias, ambiguous, unmatched, unscored}
    any_top_peak_matches_any_mode in {false, true}

All 12 cells are emitted; unjoined confirmed positives remain `unscored`,
never dropped. The frozen columns are read as emitted by
metrics_generalization.py — nothing is rescored. No interval, no endpoint
status; the table does not identify or remove wrong-reason triggers.
FULL-run only.

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402,F401
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)
import d3_descriptive_common as common  # noqa: E402
from d3_descriptive_common import (  # noqa: E402
    EXPECTED_POSITIVES,
    MATCH_CLASSES_WITH_UNSCORED,
    RULE,
    STATUS_COLUMNS,
    UNSCORED,
    is_boolean_cell,
    sha256_file,
    truthy,
)

OUTPUT_FILE = "d3_confirmed_positive_match_partition.csv"
README_FILE = "d3_positive_partition.README.md"
MANIFEST_FILE = "d3_positive_partition.manifest.json"
PASS_BASIS = "best"

COLUMNS = [
    "match_class", "any_top_peak_matches_any_mode", "n_positive",
    "n_confirmed_positive", "n_cell", "rate_of_all_positives",
    "share_of_confirmed_positives", *STATUS_COLUMNS,
]

DISCLOSURE = (
    "Post-launch descriptive analysis: `d3_confirmed_positive_match_partition.csv` "
    "partitions the frozen rule-1 best-pass confirmed-positive numerator by its "
    "already-emitted dominant-match class and top-15 any-mode indicator over the "
    "unchanged 610-star P1 denominator, carries no interval or endpoint status, "
    "and does not identify or remove wrong-reason triggers."
)
REFUSAL = (
    "The admitted solar-diurnal rule is explicitly a partition of the "
    "negative-class P3 numerator only. Applying it to confirmed positives exceeds "
    "the 2026-08-31 admission. No positive-class `within_solar_diurnal_band` "
    "column is authorized here."
)


def partition(per_star: pd.DataFrame,
              expected_positives: int = EXPECTED_POSITIVES) -> pd.DataFrame:
    """Pure arithmetic 6 x 2 partition of the confirmed-positive numerator."""
    positives = common.positives_frame(per_star, expected_positives)
    confirmed = positives[positives["best_status"] == RULE].copy()
    classes = confirmed["best_candidate_matches_dominant"].astype(object)
    bad = ~classes.isin(MATCH_CLASSES_WITH_UNSCORED)
    if bad.any():
        raise SystemExit(
            "confirmed positives with a dominant-match class outside the frozen "
            f"taxonomy (abort rather than classify silently): "
            f"{confirmed.loc[bad, 'sid'].tolist()[:10]} -> {classes[bad].unique().tolist()}"
        )
    flags = confirmed["any_top_peak_matches_any_mode"]
    not_bool = ~flags.map(is_boolean_cell)
    if not_bool.any():
        raise SystemExit(
            "confirmed positives without an explicit any_top_peak_matches_any_mode "
            f"boolean: {confirmed.loc[not_bool, 'sid'].tolist()[:10]}"
        )
    flag_bool = flags.map(truthy)
    unjoined = ~confirmed["freq_scorable"].map(truthy)
    # Ruling: "unjoined confirmed positives remain `unscored`, never dropped".
    # The frozen metrics label them `unmatched` because the roster dominant
    # frequency is NaN (float, not None) when classify_match runs; no estimand
    # reads that cell (P2 excludes unjoined stars). Enforce the ruled label
    # here; the count is recorded in the manifest and disclosed.
    n_relabelled = int((unjoined & (classes != UNSCORED)).sum())
    classes = classes.where(~unjoined, UNSCORED)
    if (unjoined & (classes != UNSCORED)).any():  # pragma: no cover - relabelled above
        raise SystemExit(
            "an unjoined (not freq_scorable) confirmed positive carries a scored "
            "dominant-match class; per_star.csv is inconsistent"
        )
    n_confirmed = int(len(confirmed))
    rows = []
    for cls in MATCH_CLASSES_WITH_UNSCORED:
        for flag in (False, True):
            n_cell = int(((classes == cls) & (flag_bool == flag)).sum())
            rows.append({
                "match_class": cls,
                "any_top_peak_matches_any_mode": flag,
                "n_positive": expected_positives,
                "n_confirmed_positive": n_confirmed,
                "n_cell": n_cell,
                "rate_of_all_positives": n_cell / expected_positives,
                "share_of_confirmed_positives": (
                    n_cell / n_confirmed if n_confirmed else math.nan),
            })
    table = common.with_status(pd.DataFrame(rows))[COLUMNS]
    table.attrs["n_unjoined_relabelled_unscored"] = n_relabelled
    if len(table) != 12:  # pragma: no cover - fixed cross
        raise SystemExit("partition does not have 12 cells")
    if int(table["n_cell"].sum()) != n_confirmed:  # pragma: no cover - identity
        raise SystemExit("partition identity violated")
    if not math.isclose(float(table["rate_of_all_positives"].sum()),
                        n_confirmed / expected_positives, rel_tol=0, abs_tol=1e-12):
        raise SystemExit("rate identity violated")  # pragma: no cover
    return table


def verify_against_completeness(table: pd.DataFrame, completeness: pd.DataFrame) -> None:
    """The partition must reproduce the frozen P1 point estimate exactly
    (unit positive weights make weighted p == k/n up to float roundoff)."""
    p1 = completeness[(completeness["pass"] == PASS_BASIS) & (completeness["rule"] == RULE)
                      & (completeness["scope"] == "detection_eligible_roster")]
    if len(p1) != 1:
        raise SystemExit("completeness_by_class_pass_rule.csv has no unique P1 row")
    n_pos = int(table["n_positive"].iloc[0])
    n_conf = int(table["n_confirmed_positive"].iloc[0])
    if int(p1["n"].iloc[0]) != n_pos:
        raise SystemExit(f"P1 n ({int(p1['n'].iloc[0])}) != partition denominator ({n_pos})")
    if not math.isclose(float(p1["p"].iloc[0]), n_conf / n_pos, rel_tol=1e-9, abs_tol=1e-12):
        raise SystemExit(
            f"partition numerator {n_conf}/{n_pos} does not reproduce the frozen "
            f"P1 point estimate {float(p1['p'].iloc[0])}"
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args(argv)

    assert_frozen()
    metrics_manifest, per_star = common.load_metrics_bundle(args.metrics_dir)
    completeness_path = args.metrics_dir / "completeness_by_class_pass_rule.csv"
    if not completeness_path.exists():
        raise SystemExit(f"metrics bundle has no completeness table: {completeness_path}")
    completeness = pd.read_csv(completeness_path)

    table = partition(per_star)
    verify_against_completeness(table, completeness)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / OUTPUT_FILE
    common.write_csv(table, out_csv, COLUMNS)
    (args.out_dir / README_FILE).write_text(
        "# D3 confirmed-positive match partition (descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n" + REFUSAL + "\n\n"
        f"Ruling: {common.VERDICT_FILE}, item 3 (F01, ADMIT-DESCRIPTIVE; "
        "positive-class diurnal extension REFUSED).\n"
        f"Fields on every row: analysis_status={common.ANALYSIS_STATUS}, "
        f"prespecified={str(common.PRESPECIFIED).lower()}, interval={common.INTERVAL}.\n\n"
        "Frame: all eligible dsct_flag1 positives with best_status==confirmed under "
        "rule 1 and best pass, crossed by the frozen best_candidate_matches_dominant "
        "class (direct, harmonic, window_alias, ambiguous, unmatched, unscored) and "
        "the frozen any_top_peak_matches_any_mode indicator; all 12 cells emitted; "
        f"n_positive={EXPECTED_POSITIVES}; unjoined confirmed positives remain "
        "`unscored`, never dropped. share_of_confirmed_positives is blank when no "
        "positive is confirmed.\n",
        encoding="utf-8",
    )
    manifest = {
        **common.provenance_block(Path(__file__)),
        "item": "sol_round2 item 3 (F01)",
        "refused": "positive-class within_solar_diurnal_band column (not emitted)",
        "inputs_sha256": {
            "per_star.csv": sha256_file(args.metrics_dir / "per_star.csv"),
            "metrics_manifest.json": sha256_file(args.metrics_dir / "manifest.json"),
            "completeness_by_class_pass_rule.csv": sha256_file(completeness_path),
        },
        "outputs_sha256": {OUTPUT_FILE: sha256_file(out_csv)},
        "metrics_bundle": {"dataset": metrics_manifest.get("dataset"),
                           "pilot": bool(metrics_manifest.get("pilot", False))},
        "n_positive": int(table["n_positive"].iloc[0]),
        "n_confirmed_positive": int(table["n_confirmed_positive"].iloc[0]),
        "cells": {f"{r.match_class}|any_top_peak={str(r.any_top_peak_matches_any_mode).lower()}":
                  int(r.n_cell) for r in table.itertuples()},
    }
    manifest["n_unjoined_relabelled_unscored"] = int(
        table.attrs.get("n_unjoined_relabelled_unscored", 0))
    common.write_json(args.out_dir / MANIFEST_FILE, manifest)
    print(table.to_string(index=False))
    print(f"[positive_partition] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
