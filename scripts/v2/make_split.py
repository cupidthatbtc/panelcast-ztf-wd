#!/usr/bin/env python3
"""Pre-registered dev/holdout split for the v2 arm (V2_PLAN.md §4; its SHA-256
is quoted in the plan). Revised 2026-09-02 after the sol pre-registration
review (generalization/reviews/V2G1/): the four development smoke stars form a
`dev_smoke` class excluded from BOTH halves; D2 controls referenced by any
odd-TIC nominal-B shard are sequestered to the holdout; the dev D2 run is the
500 dev nulls only (even-TIC B / control outputs are deferred until after the
holdout); the trend-window subsets were dropped (full dev reruns instead).

  D3: even KIC -> dev, odd KIC -> holdout, dev_smoke for the four smoke stars.
  D2: arm A/B shards by TIC parity (even -> dev); Gaussian nulls by serial
      (0-499 dev, 500-999 holdout); a control referenced by any odd-TIC
      nominal-B shard -> holdout, else (even-referenced) -> dev.

Outputs (generalization/v2/): split.csv; d3_dev.txt, d3_holdout.txt (halves
intersected with the frozen shard index), d3_dev_smoke.txt; d2_dev.txt (dev
nulls), d2_holdout.txt (holdout B-nominal + controls + nulls),
d2_dev_deferred.txt (dev B-nominal + dev controls); overlap30.txt (every 48th
D3 dev id); split_manifest.json (source SHAs, counts, window-crossing
disclosure, output SHAs).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "generalization" / "v2"
ROSTER_D3 = REPO_ROOT / "generalization" / "data" / "d3" / "roster_d3.csv"
SHARD_INDEX_D3 = REPO_ROOT / "generalization" / "data" / "d3" / "crossmatch_freeze" / "panels_shard_index.txt"
MANIFEST_D2 = REPO_ROOT / "generalization" / "results" / "2026-08-30_d2_pilot_gen2" / "run" / "shard_manifest_gen2.csv"
COLUMNS = ["dataset", "sid", "key", "group", "scenario", "split"]
# development smoke stars (V2_PLAN.md §10): inspected while the code was written
SMOKE_SIDS = ("9000000000000892667", "9000000000004752731",
              "9000000000009596355", "9000000000005475187")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def d3_split(roster: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in roster.itertuples(index=False):
        kic = int(r.KIC)
        sid = str(r.source_id)
        split = "dev_smoke" if sid in SMOKE_SIDS else ("dev" if kic % 2 == 0 else "holdout")
        rows.append({"dataset": "d3", "sid": sid, "key": f"KIC {kic}",
                     "group": str(r.class_label), "scenario": "", "split": split})
    return pd.DataFrame(rows, columns=COLUMNS)


def d2_split(manifest: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    control_parity: dict[str, set[str]] = {}
    for r in manifest.itertuples(index=False):
        arm, scenario = str(r.arm), str(r.scenario)
        if arm in ("A", "B"):
            tic = int(r.tic)
            half = "dev" if tic % 2 == 0 else "holdout"
            key = f"TIC {tic}"
            if arm == "B" and scenario == "nominal" and str(r.control_campaign_id):
                control_parity.setdefault(str(r.control_campaign_id), set()).add(half)
        elif arm == "gauss_null":
            serial = int(r.null_serial)
            half = "dev" if serial < 500 else "holdout"
            key = f"null {serial}"
        elif arm == "ctrl":
            continue
        else:
            raise SystemExit(f"unknown arm {arm}")
        rows.append({"dataset": "d2", "sid": str(r.campaign_id), "key": key,
                     "group": arm, "scenario": scenario, "split": half})
    both, unreferenced = 0, 0
    for r in manifest[manifest["arm"] == "ctrl"].itertuples(index=False):
        sid = str(r.campaign_id)
        halves = control_parity.get(sid, set())
        if not halves:
            half, unreferenced = "unreferenced", unreferenced + 1
        elif "holdout" in halves:
            half = "holdout"
            both += int(len(halves) == 2)
        else:
            half = "dev"
        rows.append({"dataset": "d2", "sid": sid, "key": f"pool {int(r.pool_index)}",
                     "group": "ctrl", "scenario": "control", "split": half})
    frame = pd.DataFrame(rows, columns=COLUMNS)
    # window-crossing disclosure: template windows shared by both halves
    nominal = manifest[(manifest["arm"] == "B") & (manifest["scenario"] == "nominal")]
    b_half = nominal["tic"].astype(int).mod(2).map({0: "dev", 1: "holdout"})
    b_windows = nominal.assign(half=b_half.values).groupby("template_source_id")["half"].nunique()
    nulls = manifest[manifest["arm"] == "gauss_null"]
    n_half = nulls["null_serial"].astype(int).lt(500).map({True: "dev", False: "holdout"})
    null_windows = nulls.assign(half=n_half.values).groupby("template_source_id")["half"].nunique()
    notes = {
        "controls_referenced_by_both_parities_assigned_holdout": both,
        "controls_unreferenced": unreferenced,
        "nominal_b_template_windows_in_both_halves": int((b_windows == 2).sum()),
        "nominal_b_template_windows_total": int(b_windows.size),
        "null_template_windows_in_both_halves": int((null_windows == 2).sum()),
        "null_template_windows_total": int(null_windows.size),
    }
    return frame, notes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    roster = pd.read_csv(ROSTER_D3, dtype={"source_id": str})
    manifest = pd.read_csv(MANIFEST_D2, dtype=str)
    d3 = d3_split(roster)
    d2, notes = d2_split(manifest)
    split = pd.concat([d3, d2], ignore_index=True)
    if split["sid"].duplicated().any():
        raise SystemExit("duplicate sid in the split table")
    split_path = args.out_dir / "split.csv"
    split.to_csv(split_path, index=False, lineterminator="\n")

    shard_ids = {line.strip() for line in SHARD_INDEX_D3.read_text().splitlines() if line.strip()}
    lists: dict[str, list[str]] = {}
    for half in ("dev", "holdout"):
        lists[f"d3_{half}.txt"] = sorted(sid for sid in d3.loc[d3["split"] == half, "sid"] if sid in shard_ids)
    lists["d3_dev_smoke.txt"] = sorted(sid for sid in d3.loc[d3["split"] == "dev_smoke", "sid"] if sid in shard_ids)
    b_nominal = (d2["group"] == "B") & (d2["scenario"] == "nominal")
    lists["d2_dev.txt"] = sorted(d2[(d2["split"] == "dev") & (d2["group"] == "gauss_null")]["sid"])
    lists["d2_holdout.txt"] = sorted(d2[(d2["split"] == "holdout") & (
        b_nominal | (d2["group"] == "ctrl") | (d2["group"] == "gauss_null"))]["sid"])
    lists["d2_dev_deferred.txt"] = sorted(d2[(d2["split"] == "dev") & (b_nominal | (d2["group"] == "ctrl"))]["sid"])
    lists["overlap30.txt"] = lists["d3_dev.txt"][::48][:30]
    for name, ids in lists.items():
        (args.out_dir / name).write_text("\n".join(ids) + "\n", encoding="utf-8")
    for stale in ("d3_dev_window_subset.txt", "d2_dev_window_subset.txt"):
        (args.out_dir / stale).unlink(missing_ok=True)

    balance = (d3.groupby(["split", "group"]).size().unstack(fill_value=0)).to_dict(orient="index")
    d2_counts = (d2.groupby(["split", "group", "scenario"]).size()
                 .reset_index(name="n").to_dict(orient="records"))
    record = {
        "rule": {"d3": "even KIC -> dev, odd KIC -> holdout; the four development smoke stars -> dev_smoke "
                       "(excluded from both halves)",
                 "d2": "A/B by TIC parity (even -> dev); nulls serial < 500 -> dev; a control referenced by "
                       "any odd-TIC nominal-B shard -> holdout, else -> dev; dev D2 run = dev nulls only, "
                       "dev B/controls deferred until after the holdout"},
        "smoke_sids": list(SMOKE_SIDS),
        "sources": {str(ROSTER_D3.relative_to(REPO_ROOT)): sha256_file(ROSTER_D3),
                    str(SHARD_INDEX_D3.relative_to(REPO_ROOT)): sha256_file(SHARD_INDEX_D3),
                    str(MANIFEST_D2.relative_to(REPO_ROOT)): sha256_file(MANIFEST_D2)},
        "d3_class_balance": balance,
        "d3_runner_lists": {name: len(ids) for name, ids in lists.items() if name.startswith("d3")},
        "d2_counts": d2_counts,
        "d2_runner_lists": {name: len(ids) for name, ids in lists.items() if name.startswith("d2")},
        "overlap30": len(lists["overlap30.txt"]),
        **notes,
        "outputs": {name: sha256_file(args.out_dir / name) for name in ["split.csv", *lists]},
    }
    (args.out_dir / "split_manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "d2_counts"}, indent=2))


if __name__ == "__main__":
    main()
