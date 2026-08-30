#!/usr/bin/env python3
"""D3 crossmatch freeze: the realized ZTF crossmatch mapping + a ZERO-DISCRETION
ambiguity adjudication, committed as DATA before any campaign L-S run
(GENERALIZATION_PLAN.md, D3 roster; RUNBOOK D3 step 3).

Inputs: the panel builder's crossmatch_qc.csv (nearest-cluster crossmatch,
frozen QC chain), its shard_index.txt, and roster_d3.csv (class labels).

Dispositions are deterministic functions of the QC columns — no analyst
choice exists anywhere in this file, so the freeze cannot be conditioned on
a later detection outcome:

  headline      : the frozen chain's decision is final — every crossmatched
                  star is in the headline estimands (its `crossmatched` flag
                  is the eligibility; nothing here overrides it)
  crowding_clean: sep < 1.0" AND <= 3 ZTF objects in the 10" cone (plan's
                  prespecified crowding subset)
  ambiguous     : crossmatched AND (sep >= 1.5" OR > 1 ZTF object in cone)
                  — reported as its own attrition/sensitivity row, never
                  removed from the headline

Outputs (out-dir): crossmatch_adjudication.csv (one row per roster star),
attrition_by_class.csv, freeze_manifest.json (SHAs of inputs and outputs,
counts, the rule constants).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from frozen_api import REPO_ROOT, assert_frozen, campaign_file_shas

SEP_AMBIGUOUS_ARCSEC = 1.5
SEP_CLEAN_ARCSEC = 1.0
MAX_OBJECTS_CLEAN = 3
RULE_VERSION = "d3-crossmatch-freeze-v1 (2026-08-30)"
DISPOSITIONS = ("crossmatched_clean", "crossmatched_ambiguous", "crossmatched_crowded",
                "not_crossmatched", "cache_missing", "read_error")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adjudicate(qc: pd.DataFrame) -> pd.DataFrame:
    """Pure function of the QC columns; vectorized, no branches on labels."""
    out = qc.copy()
    for column in ("nearest_separation_arcsec", "ztf_objects_in_cone", "selected_ztf_objects"):
        if column not in out:
            out[column] = float("nan")
    crossmatched = out.get("crossmatched", pd.Series(False, index=out.index)).fillna(False).astype(bool)
    sep = pd.to_numeric(out["nearest_separation_arcsec"], errors="coerce")
    n_obj = pd.to_numeric(out["ztf_objects_in_cone"], errors="coerce")
    out["crossmatched"] = crossmatched
    out["sep_ge_ambiguous"] = crossmatched & (sep >= SEP_AMBIGUOUS_ARCSEC)
    out["multi_object_cone"] = crossmatched & (n_obj > 1)
    out["ambiguous"] = out["sep_ge_ambiguous"] | out["multi_object_cone"]
    out["crowding_clean"] = crossmatched & (sep < SEP_CLEAN_ARCSEC) & (n_obj <= MAX_OBJECTS_CLEAN)
    status = out.get("read_status", pd.Series("ok", index=out.index)).fillna("ok")
    disposition = pd.Series("not_crossmatched", index=out.index, dtype=object)
    disposition[status == "missing"] = "cache_missing"
    disposition[status == "error"] = "read_error"
    disposition[crossmatched & ~out["ambiguous"] & out["crowding_clean"]] = "crossmatched_clean"
    disposition[crossmatched & ~out["ambiguous"] & ~out["crowding_clean"]] = "crossmatched_crowded"
    disposition[crossmatched & out["ambiguous"]] = "crossmatched_ambiguous"
    out["disposition"] = disposition
    out["headline_eligible"] = crossmatched          # the frozen chain decides; never overridden
    out["rule_version"] = RULE_VERSION
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panels-dir", type=Path, required=True,
                        help="build_panels_generic out-dir (crossmatch_qc.csv, shard_index.txt)")
    parser.add_argument("--roster", type=Path,
                        default=REPO_ROOT / "generalization/data/d3/roster_d3.csv")
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "generalization/data/d3/crossmatch_freeze")
    args = parser.parse_args()

    assert_frozen()
    campaign_start = campaign_file_shas()
    qc_path = args.panels_dir / "crossmatch_qc.csv"
    index_path = args.panels_dir / "shard_index.txt"
    qc = pd.read_csv(qc_path, dtype={"source_id": str})
    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    if qc["source_id"].duplicated().any():
        raise SystemExit("crossmatch_qc.csv has duplicate source ids")
    if set(qc["source_id"]) != set(roster["source_id"]):
        raise SystemExit("crossmatch_qc.csv does not cover exactly the roster")
    index_ids = {line.strip() for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    adjudicated = adjudicate(qc)
    if set(adjudicated.loc[adjudicated["crossmatched"], "source_id"]) != index_ids:
        raise SystemExit("shard_index.txt != the crossmatched set in crossmatch_qc.csv")
    label_cols = [c for c in ("dsct", "class_label", "stratum", "gmag", "sampling_weight") if c in roster.columns]
    adjudicated = adjudicated.merge(roster[["source_id", *label_cols]], on="source_id",
                                    how="left", suffixes=("", "_roster"))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    adjudicated.to_csv(args.out_dir / "crossmatch_adjudication.csv", index=False, lineterminator="\n")

    group_col = "class_label_roster" if "class_label_roster" in adjudicated else (
        "class_label" if "class_label" in adjudicated else None)
    attrition_rows = []
    groups = adjudicated.groupby(group_col) if group_col else [("all", adjudicated)]
    for label, g in groups:
        attrition_rows.append({
            "class": label, "roster": len(g),
            "cache_present": int(g.get("cache_present", pd.Series(False, index=g.index)).fillna(False).astype(bool).sum()),
            "read_ok": int((g.get("read_status", pd.Series("ok", index=g.index)) == "ok").sum()),
            "crossmatched": int(g["crossmatched"].sum()),
            "ambiguous": int(g["ambiguous"].sum()),
            "crowding_clean": int(g["crowding_clean"].sum()),
        })
    attrition = pd.DataFrame(attrition_rows)
    attrition.to_csv(args.out_dir / "attrition_by_class.csv", index=False, lineterminator="\n")

    manifest = {
        "rule_version": RULE_VERSION,
        "constants": {"SEP_AMBIGUOUS_ARCSEC": SEP_AMBIGUOUS_ARCSEC, "SEP_CLEAN_ARCSEC": SEP_CLEAN_ARCSEC,
                      "MAX_OBJECTS_CLEAN": MAX_OBJECTS_CLEAN},
        "inputs_sha256": {"crossmatch_qc.csv": sha256_file(qc_path), "shard_index.txt": sha256_file(index_path),
                          "roster_d3.csv": sha256_file(args.roster)},
        "outputs_sha256": {name: sha256_file(args.out_dir / name)
                           for name in ("crossmatch_adjudication.csv", "attrition_by_class.csv")},
        "counts": {k: int(v) for k, v in adjudicated["disposition"].value_counts().items()},
        "n_roster": int(len(adjudicated)), "n_crossmatched": int(adjudicated["crossmatched"].sum()),
        "campaign_sha256": campaign_start,
    }
    if campaign_file_shas() != campaign_start:
        raise SystemExit("campaign code changed while adjudicating")
    (args.out_dir / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("counts", "n_roster", "n_crossmatched")}, indent=2))
    print(attrition.to_string(index=False))


if __name__ == "__main__":
    main()
