"""Tests for the post-launch descriptive D3 confirmed-positive match
partition (reviews/G5prep/sol_round2.md item 3, F01): the fixed 6 x 2 cross,
partition identities over the 610-star denominator, unjoined confirmed
positives kept as `unscored`, fail-closed guards, the refused diurnal
column, and the CLI on a synthetic bundle."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))

from d3_positive_partition import (  # noqa: E402
    COLUMNS,
    main,
    partition,
    verify_against_completeness,
)

CLASSES = ["direct", "harmonic", "window_alias", "ambiguous", "unmatched", "unscored"]


def _row(sid, status, cls, flag, scorable=True):
    return {"sid": sid, "class_label": "dsct_flag1", "label_positive": True, "primary_freq": 5.0,
            "freq_scorable": scorable, "baseline_days": 2000.0, "best_status": status,
            "best_frequency_per_day": 5.0, "low_available": True, "high_available": True,
            "eligible_any_pass": True, "best_candidate_matches_any_mode": cls,
            "best_candidate_matches_dominant": cls, "any_top_peak_matches_any_mode": flag}


def test_twelve_cells_and_identities(d3_world, per_star_roundtrip):
    for per_star in (d3_world.per_star, per_star_roundtrip):
        table = partition(per_star)
        assert list(table.columns) == COLUMNS
        assert len(table) == 12
        assert table["match_class"].tolist() == [c for c in CLASSES for _ in (0, 1)]
        assert table["any_top_peak_matches_any_mode"].tolist() == [False, True] * 6
        assert (table["n_positive"] == 610).all()
        pos = per_star[per_star["class_label"] == "dsct_flag1"]
        confirmed = pos[pos["best_status"] == "confirmed"]
        n_conf = len(confirmed)
        assert (table["n_confirmed_positive"] == n_conf).all()
        assert int(table["n_cell"].sum()) == n_conf
        assert math.isclose(table["rate_of_all_positives"].sum(), n_conf / 610, abs_tol=1e-12)
        assert math.isclose(table["share_of_confirmed_positives"].sum(), 1.0, abs_tol=1e-12)
        # unjoined confirmed positives are the `unscored` cells, never dropped
        unjoined_conf = int((~confirmed["freq_scorable"].astype(bool)).sum())
        unscored = table[table["match_class"] == "unscored"]
        assert int(unscored["n_cell"].sum()) == unjoined_conf > 0
        assert int(unscored.loc[unscored["any_top_peak_matches_any_mode"], "n_cell"].sum()) == 0
        assert (table["analysis_status"] == "postlaunch_descriptive").all()
        assert (~table["prespecified"].astype(bool)).all()
        assert (table["interval"] == "none").all()
        assert "within_solar_diurnal_band" not in table.columns     # REFUSED extension


def test_small_frame_manual_counts():
    per_star = pd.DataFrame([
        _row("a", "confirmed", "direct", True),
        _row("b", "confirmed", "direct", False),
        _row("c", "confirmed", "unscored", False, scorable=False),
        _row("d", "confirmed", "harmonic", True),
        _row("e", "not_detected", "direct", True),          # not confirmed: not in the numerator
        _row("f", "candidate", "unmatched", False),
        _row("g", "missing", "unscored", False, scorable=False),
    ])
    table = partition(per_star, expected_positives=7).set_index(
        ["match_class", "any_top_peak_matches_any_mode"])
    assert table.loc[("direct", True), "n_cell"] == 1
    assert table.loc[("direct", False), "n_cell"] == 1
    assert table.loc[("unscored", False), "n_cell"] == 1
    assert table.loc[("harmonic", True), "n_cell"] == 1
    assert table["n_cell"].sum() == 4
    assert (table["n_confirmed_positive"] == 4).all()
    assert table.loc[("direct", True), "rate_of_all_positives"] == 1 / 7
    assert table.loc[("direct", True), "share_of_confirmed_positives"] == 0.25
    zero = table.loc[("ambiguous", True)]
    assert zero["n_cell"] == 0 and zero["rate_of_all_positives"] == 0.0        # zero cells emitted


def test_zero_confirmed_gives_blank_share():
    per_star = pd.DataFrame([_row("a", "not_detected", "direct", True),
                             _row("b", "missing", "unscored", False, scorable=False)])
    table = partition(per_star, expected_positives=2)
    assert (table["n_cell"] == 0).all()
    assert (table["rate_of_all_positives"] == 0.0).all()
    assert table["share_of_confirmed_positives"].isna().all()


def test_guards_abort():
    base = [_row("a", "confirmed", "direct", True), _row("b", "not_detected", "direct", True)]
    with pytest.raises(SystemExit, match="!= the frozen positive"):
        partition(pd.DataFrame(base), expected_positives=3)
    bad_class = pd.DataFrame(base + [_row("c", "confirmed", "close_enough", True)])
    with pytest.raises(SystemExit, match="outside the frozen"):
        partition(bad_class, expected_positives=3)
    bad_flag = pd.DataFrame(base + [_row("c", "confirmed", "direct", math.nan)])
    with pytest.raises(SystemExit, match="explicit any_top_peak"):
        partition(bad_flag, expected_positives=3)
    unjoined_scored = pd.DataFrame(base + [_row("c", "confirmed", "direct", True, scorable=False)])
    with pytest.raises(SystemExit, match="unjoined"):
        partition(unjoined_scored, expected_positives=3)
    not_positive = pd.DataFrame(base + [{**_row("c", "confirmed", "direct", True), "label_positive": False}])
    with pytest.raises(SystemExit, match="not label_positive"):
        partition(not_positive, expected_positives=3)


def test_verify_against_completeness(d3_bundle):
    table = partition(d3_bundle["world"].per_star)
    completeness = pd.read_csv(d3_bundle["metrics"] / "completeness_by_class_pass_rule.csv")
    verify_against_completeness(table, completeness)
    bad = completeness.copy()
    bad.loc[(bad["pass"] == "best") & (bad["scope"] == "detection_eligible_roster"), "p"] += 1 / 610
    with pytest.raises(SystemExit, match="does not reproduce"):
        verify_against_completeness(table, bad)
    with pytest.raises(SystemExit, match="no unique P1 row"):
        verify_against_completeness(table, completeness[completeness["pass"] != "best"])
    wrong_n = completeness.copy()
    wrong_n.loc[(wrong_n["pass"] == "best") & (wrong_n["scope"] == "detection_eligible_roster"), "n"] = 609
    with pytest.raises(SystemExit, match="partition denominator"):
        verify_against_completeness(table, wrong_n)


def test_cli_end_to_end(d3_bundle):
    out = d3_bundle["out"]
    main(["--metrics-dir", str(d3_bundle["metrics"]), "--out-dir", str(out)])
    table = pd.read_csv(out / "d3_confirmed_positive_match_partition.csv")
    assert list(table.columns) == COLUMNS and len(table) == 12
    assert int(table["n_cell"].sum()) == d3_bundle["n_confirmed_positive"]
    manifest = json.loads((out / "d3_positive_partition.manifest.json").read_text())
    assert manifest["n_positive"] == 610
    assert manifest["outputs_sha256"].keys() == {"d3_confirmed_positive_match_partition.csv"}
    assert manifest["refused"].startswith("positive-class within_solar_diurnal_band")
    readme = (out / "d3_positive_partition.README.md").read_text()
    assert "does not identify or remove wrong-reason triggers" in readme
    assert "No positive-class `within_solar_diurnal_band` column is authorized" in readme


def test_cli_refuses_pilot_bundle(d3_world, tmp_path):
    from conftest import write_bundle
    paths = write_bundle(d3_world, tmp_path, pilot=True)
    with pytest.raises(SystemExit, match="pilot"):
        main(["--metrics-dir", str(paths["metrics"]), "--out-dir", str(paths["out"])])
