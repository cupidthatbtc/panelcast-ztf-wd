"""The pre-registered dev/holdout split (generalization/v2/split.csv)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "generalization" / "v2"
SMOKE = {"9000000000000892667", "9000000000004752731", "9000000000009596355", "9000000000005475187"}


def _ids(name: str) -> list[str]:
    return [line.strip() for line in (V2 / name).read_text().splitlines() if line.strip()]


def test_split_sha_matches_plan_and_manifest():
    sha = hashlib.sha256((V2 / "split.csv").read_bytes()).hexdigest()
    plan = (V2 / "V2_PLAN.md").read_text()
    quoted = re.search(r"split\.csv`, SHA-256 `([0-9a-f]{64})`", plan)
    assert quoted and quoted.group(1) == sha
    manifest = json.loads((V2 / "split_manifest.json").read_text())
    assert manifest["outputs"]["split.csv"] == sha
    for name in ("d3_holdout.txt", "d2_holdout.txt", "d3_dev.txt", "d2_dev.txt"):
        assert manifest["outputs"][name] == hashlib.sha256((V2 / name).read_bytes()).hexdigest()


def test_halves_are_disjoint_and_parity_rule_holds():
    split = pd.read_csv(V2 / "split.csv", dtype=str)
    assert not split["sid"].duplicated().any()
    d3 = split[split["dataset"] == "d3"]
    assert set(d3.loc[d3["split"] == "dev_smoke", "sid"]) == SMOKE
    rest = d3[d3["split"] != "dev_smoke"]
    kic = rest["key"].str.replace("KIC ", "").astype(int)
    assert ((kic % 2 == 0) == (rest["split"] == "dev")).all()
    balance = d3.groupby(["split", "group"]).size().unstack(fill_value=0)
    assert balance.loc["dev", "dsct_flag1"] == 308 and balance.loc["holdout", "dsct_flag1"] == 299
    assert balance.loc["dev", "dsct_flag0"] == 1164 and balance.loc["holdout", "dsct_flag0"] == 1149
    assert balance.loc["dev_smoke", "dsct_flag1"] == 3 and balance.loc["dev_smoke", "dsct_flag0"] == 1


def test_runner_lists_are_subsets_of_their_half_and_of_the_shard_index():
    split = pd.read_csv(V2 / "split.csv", dtype=str).set_index("sid")
    shard_ids = set(_ids("../data/d3/crossmatch_freeze/panels_shard_index.txt"))
    for half in ("dev", "holdout"):
        ids = _ids(f"d3_{half}.txt")
        assert ids == sorted(ids) and set(ids) <= shard_ids and not (set(ids) & SMOKE)
        assert (split.loc[ids, "split"] == half).all() and (split.loc[ids, "dataset"] == "d3").all()
    dev, hold = set(_ids("d3_dev.txt")), set(_ids("d3_holdout.txt"))
    assert not (dev & hold)
    assert set(_ids("d3_dev_smoke.txt")) == SMOKE


def test_d2_lists_follow_the_revised_rule():
    split = pd.read_csv(V2 / "split.csv", dtype=str).set_index("sid")
    dev = split.loc[_ids("d2_dev.txt")]
    assert (dev["group"] == "gauss_null").all() and (dev["split"] == "dev").all() and len(dev) == 500
    hold = split.loc[_ids("d2_holdout.txt")]
    assert (hold["split"] == "holdout").all()
    assert hold["group"].value_counts().to_dict() == {"gauss_null": 500, "B": 129, "ctrl": 67}
    assert (hold.loc[hold["group"] == "B", "scenario"] == "nominal").all()
    deferred = split.loc[_ids("d2_dev_deferred.txt")]
    assert (deferred["split"] == "dev").all() and set(deferred["group"]) == {"B", "ctrl"}
    assert not (set(_ids("d2_dev.txt")) & set(_ids("d2_holdout.txt")))
    # every control referenced by an odd-TIC nominal-B shard is in the holdout
    manifest = json.loads((V2 / "split_manifest.json").read_text())
    assert manifest["controls_unreferenced"] == 0
    assert manifest["controls_referenced_by_both_parities_assigned_holdout"] == 43


def test_nulls_split_by_serial():
    split = pd.read_csv(V2 / "split.csv", dtype=str)
    nulls = split[(split["dataset"] == "d2") & (split["group"] == "gauss_null")]
    serial = nulls["key"].str.replace("null ", "").astype(int)
    assert ((serial < 500) == (nulls["split"] == "dev")).all()
    assert nulls["split"].value_counts().to_dict() == {"dev": 500, "holdout": 500}


def test_overlap_is_dev_only_and_no_window_subsets_remain():
    dev = set(_ids("d3_dev.txt"))
    assert set(_ids("overlap30.txt")) <= dev and len(_ids("overlap30.txt")) == 30
    assert not (V2 / "d3_dev_window_subset.txt").exists() and not (V2 / "d2_dev_window_subset.txt").exists()
