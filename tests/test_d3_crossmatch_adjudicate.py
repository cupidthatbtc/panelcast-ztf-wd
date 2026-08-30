"""The D3 crossmatch freeze is a pure, deterministic function of the QC columns."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization"))

from d3_crossmatch_adjudicate import DISPOSITIONS, adjudicate  # noqa: E402


def test_dispositions_are_deterministic_and_never_override_the_frozen_chain():
    qc = pd.DataFrame([
        {"source_id": "9000000000000000001", "read_status": "ok", "crossmatched": True,
         "nearest_separation_arcsec": 0.3, "ztf_objects_in_cone": 1},
        {"source_id": "9000000000000000002", "read_status": "ok", "crossmatched": True,
         "nearest_separation_arcsec": 1.7, "ztf_objects_in_cone": 1},      # separation-ambiguous
        {"source_id": "9000000000000000003", "read_status": "ok", "crossmatched": True,
         "nearest_separation_arcsec": 0.4, "ztf_objects_in_cone": 2},      # multi-object-ambiguous
        {"source_id": "9000000000000000004", "read_status": "ok", "crossmatched": True,
         "nearest_separation_arcsec": 1.2, "ztf_objects_in_cone": 1},      # not clean, not ambiguous
        {"source_id": "9000000000000000005", "read_status": "ok", "crossmatched": False,
         "nearest_separation_arcsec": 0.2, "ztf_objects_in_cone": 1},
        {"source_id": "9000000000000000006", "read_status": "missing", "crossmatched": False},
        {"source_id": "9000000000000000007", "read_status": "error", "crossmatched": False},
    ])
    out = adjudicate(qc)
    assert out["disposition"].tolist() == ["crossmatched_clean", "crossmatched_ambiguous",
                                           "crossmatched_ambiguous", "crossmatched_crowded",
                                           "not_crossmatched", "cache_missing", "read_error"]
    assert set(out["disposition"]) <= set(DISPOSITIONS)
    assert out["headline_eligible"].tolist() == out["crossmatched"].tolist()
    # crowding-clean (plan lens: sep < 1", <= 3 objects) and ambiguous (> 1 object) are
    # independent flags: the 2-object cone at 0.4" is clean AND ambiguous
    assert out["crowding_clean"].tolist() == [True, False, True, False, False, False, False]
    assert out["ambiguous"].tolist() == [False, True, True, False, False, False, False]
    # idempotent + label-blind: shuffling rows or adding a class column changes nothing
    again = adjudicate(qc.assign(class_label="dsct_flag1").sample(frac=1, random_state=3)).sort_values("source_id")
    assert again["disposition"].tolist() == out.sort_values("source_id")["disposition"].tolist()
