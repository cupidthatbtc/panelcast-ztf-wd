"""Tests for the post-launch descriptive D3 truth-provenance audit
(reviews/G5prep/sol_round2.md item 2, F02-F04): aliased-dominant selection
and tie-breaks, the 0.1 µHz boundary, fR / Nyquist-reflection / any-mode-
plus-fR rescoring through the frozen classifier, the P2 regime split with
its half-open edges, the fail-closed guards, the ruled roster-level facts on
the real roster/Mo tables, and the CLI end to end on a synthetic bundle."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))

import d3_descriptive_common as common  # noqa: E402
from d3_truth_provenance import (  # noqa: E402
    EXPECTED_ALIASED,
    REGIME_COLUMNS,
    RESCORING_COLUMNS,
    TABLE1_MATCH_TOL_UHZ,
    assert_scorable_identity,
    json_sha_map,
    load_top_peaks,
    main,
    p2_regime_table,
    rescoring_table,
    select_aliased_dominant,
    verify_against_completeness,
)
from conftest import F_NYQ_PER_DAY, F_NYQ_UHZ, UHZ_TO_PER_DAY, sid_for  # noqa: E402

REAL_ROSTER = common.DEFAULT_ROSTER
REAL_T1 = common.DEFAULT_MO_TABLE1
REAL_T2 = common.DEFAULT_MO_TABLE2
real_data = pytest.mark.skipif(
    not (REAL_ROSTER.exists() and REAL_T1.exists() and REAL_T2.exists()),
    reason="real roster / Mo tables not present")


def _status_ok(table: pd.DataFrame) -> None:
    assert (table["analysis_status"] == "postlaunch_descriptive").all()
    assert (~table["prespecified"].astype(bool)).all()
    assert (table["interval"] == "none").all()


# ---------------------------------------------------------------- selection

def test_select_aliased_dominant_count_and_tie_breaks(d3_world):
    targets = select_aliased_dominant(d3_world.roster, d3_world.table1)
    assert len(targets) == EXPECTED_ALIASED
    assert set(targets["sid"]) == {sid_for(90, i) for i in range(EXPECTED_ALIASED)}
    by_sid = targets.set_index("sid")
    # star 0: exact row beats the +0.05 µHz row (minimum |diff| first)
    row0 = by_sid.loc[sid_for(90, 0)]
    assert row0["abs_diff_uhz"] == 0.0 and row0["n_qualifying_rows"] == 2
    assert row0["fR_uhz"] != 111.0
    # star 1: three zero-difference rows -> minimum fR wins
    row1 = by_sid.loc[sid_for(90, 1)]
    assert row1["n_qualifying_rows"] == 3 and row1["fR_uhz"] == 250.0
    # C==1 rows (star 45) and a 5 µHz-off C==0 row (star 50) never qualify
    assert sid_for(90, 45) not in by_sid.index and sid_for(90, 50) not in by_sid.index
    assert (targets["KIC"] == targets["KIC"].astype(int)).all()


def test_boundary_0p1_uhz_inclusive():
    roster = pd.DataFrame([
        {"source_id": "a", "KIC": 1, "class_label": "dsct_flag1", "dom_freq_uhz": 100.0,
         "dom_freq_per_day": 8.64, "amp_mmag": 1.0},
        {"source_id": "b", "KIC": 2, "class_label": "dsct_flag1", "dom_freq_uhz": 100.0,
         "dom_freq_per_day": 8.64, "amp_mmag": 1.0},
        {"source_id": "c", "KIC": 3, "class_label": "dsct_flag1", "dom_freq_uhz": 100.0,
         "dom_freq_per_day": 8.64, "amp_mmag": 1.0},
        {"source_id": "d", "KIC": 4, "class_label": "dsct_flag2", "dom_freq_uhz": 100.0,
         "dom_freq_per_day": 8.64, "amp_mmag": 1.0},
        {"source_id": "e", "KIC": 5, "class_label": "dsct_flag1", "dom_freq_uhz": math.nan,
         "dom_freq_per_day": math.nan, "amp_mmag": math.nan},
    ])
    table1 = pd.DataFrame([
        {"KIC": 1, "Freq": 100.1, "Amp": 1, "fR": 466.3, "C": 0, "SC": -9},        # diff <= 0.1: in
        {"KIC": 2, "Freq": 100.10001, "Amp": 1, "fR": 466.3, "C": 0, "SC": -9},    # just above: out
        {"KIC": 3, "Freq": 99.9, "Amp": 1, "fR": 466.5, "C": 0, "SC": -9},         # -0.1: in
        {"KIC": 4, "Freq": 100.0, "Amp": 1, "fR": 466.4, "C": 0, "SC": -9},        # flag2: never
        {"KIC": 5, "Freq": 100.0, "Amp": 1, "fR": 466.4, "C": 0, "SC": -9},        # no dominant
        {"KIC": 1, "Freq": 100.0, "Amp": 1, "fR": math.nan, "C": 0, "SC": -9},     # non-finite fR: ignored
    ])
    targets = select_aliased_dominant(roster, table1)
    assert set(targets["sid"]) == {"a", "c"}
    assert TABLE1_MATCH_TOL_UHZ == 0.1
    assert abs(100.1 - 100.0) <= 0.1 and abs(100.10001 - 100.0) > 0.1


# ---------------------------------------------------------------- rescoring

def _rescoring(d3_world, per_star=None):
    targets = select_aliased_dominant(d3_world.roster, d3_world.table1)
    return rescoring_table(
        targets, d3_world.per_star if per_star is None else per_star,
        common.table2_per_day_lists(d3_world.table2), common.table1_c0(d3_world.table1),
        d3_world.peaks)


def test_rescoring_table_columns_and_frozen_classes(d3_world):
    table = _rescoring(d3_world)
    assert list(table.columns) == RESCORING_COLUMNS
    assert len(table) == EXPECTED_ALIASED
    assert table["aliased_dominant"].all()
    _status_ok(table)
    assert "within_solar_diurnal_band" not in table.columns
    by_sid = table.set_index("sid")
    tol = 1.5 / d3_world.baseline
    # unit conversions exactly as ruled
    assert np.allclose(by_sid["fR_per_day"], by_sid["fR_uhz"] * 86400 / 1e6, rtol=0, atol=0)
    assert np.allclose(by_sid["nyquist_reflection_per_day"],
                       2 * 24.46848 - by_sid["fR_per_day"], rtol=0, atol=0)
    assert np.allclose(by_sid["tolerance_per_day"].dropna(), tol, rtol=0, atol=0)
    # a direct-to-dominant candidate (star 11): the reflected fR IS the dominant
    r11 = by_sid.loc[sid_for(90, 11)]
    assert r11["best_status"] == "confirmed"
    assert r11["best_candidate_match_fR"] == "unmatched"
    assert r11["matches_nyquist_reflection"] is True or bool(r11["matches_nyquist_reflection"])
    assert r11["best_candidate_matches_any_mode_plus_fR"] == "direct"
    assert bool(r11["any_top_peak_matches_any_mode_plus_fR"])
    # a candidate AT the physical fR (star 9): direct to fR, not a reflection
    r9 = by_sid.loc[sid_for(90, 9)]
    assert r9["best_candidate_match_fR"] == "direct"
    assert not bool(r9["matches_nyquist_reflection"])
    assert r9["best_candidate_matches_any_mode_plus_fR"] == "direct"
    assert bool(r9["any_top_peak_matches_any_mode_plus_fR"])
    # a harmonic-of-dominant candidate (star 2): union scoring keeps the frozen taxonomy
    r2 = by_sid.loc[sid_for(90, 2)]
    assert r2["best_candidate_matches_any_mode_plus_fR"] == "harmonic"
    # a non-dominant table-2 mode (star 5): direct in the augmented union, unmatched vs fR
    r5 = by_sid.loc[sid_for(90, 5)]
    assert r5["best_candidate_match_fR"] == "unmatched"
    assert r5["best_candidate_matches_any_mode_plus_fR"] == "direct"
    # targets without a result stay unscored / blank, never dropped
    for i in (0, 10, 20, 30):
        r = by_sid.loc[sid_for(90, i)]
        assert r["best_status"] == "missing"
        assert r["best_candidate_match_fR"] == "unscored"
        assert r["best_candidate_matches_any_mode_plus_fR"] == "unscored"
        assert pd.isna(r["matches_nyquist_reflection"])
        assert not bool(r["any_top_peak_matches_any_mode_plus_fR"])
        assert math.isnan(r["tolerance_per_day"])


def test_rescoring_tolerance_boundary_and_reflection_positivity():
    baseline = 1000.0
    tol = 1.5 / baseline
    fr_uhz = 200.0
    fr_per_day = fr_uhz * 86400 / 1e6
    reflection = 2 * F_NYQ_PER_DAY - fr_per_day
    rows = []
    for j, best in enumerate((fr_per_day + tol * 0.999, fr_per_day + tol * 1.001,
                              reflection + tol * 0.999, reflection + tol * 1.001)):
        rows.append({"sid": f"s{j}", "class_label": "dsct_flag1", "best_status": "confirmed",
                     "best_frequency_per_day": best, "baseline_days": baseline})
    # a target whose reflection is negative (fR > 2 f_Nyq): never eligible
    rows.append({"sid": "neg", "class_label": "dsct_flag1", "best_status": "confirmed",
                 "best_frequency_per_day": abs(2 * F_NYQ_PER_DAY - 700.0 * UHZ_TO_PER_DAY),
                 "baseline_days": baseline})
    per_star = pd.DataFrame(rows)
    targets = pd.DataFrame([
        {"sid": f"s{j}", "KIC": 10 + j, "dom_freq_uhz": 1.0, "table1_alias_uhz": 1.0,
         "fR_uhz": fr_uhz, "abs_diff_uhz": 0.0, "n_qualifying_rows": 1} for j in range(4)
    ] + [{"sid": "neg", "KIC": 99, "dom_freq_uhz": 1.0, "table1_alias_uhz": 1.0,
          "fR_uhz": 700.0, "abs_diff_uhz": 0.0, "n_qualifying_rows": 1}])
    c0 = pd.DataFrame({"KIC": [10, 11, 12, 13, 99], "Freq": 1.0,
                       "fR": [fr_uhz] * 4 + [700.0], "C": 0})
    table = rescoring_table(targets, per_star, {}, c0, {}, expected_aliased=5).set_index("sid")
    assert table.loc["s0", "best_candidate_match_fR"] == "direct"
    assert table.loc["s1", "best_candidate_match_fR"] == "unmatched"
    assert bool(table.loc["s2", "matches_nyquist_reflection"])
    assert not bool(table.loc["s3", "matches_nyquist_reflection"])
    assert table.loc["neg", "nyquist_reflection_per_day"] < 0
    assert not bool(table.loc["neg", "matches_nyquist_reflection"])


def test_rescoring_guards(d3_world):
    targets = select_aliased_dominant(d3_world.roster, d3_world.table1)
    lists = common.table2_per_day_lists(d3_world.table2)
    c0 = common.table1_c0(d3_world.table1)
    with pytest.raises(SystemExit, match="!= the ruled"):
        rescoring_table(targets.iloc[:-1], d3_world.per_star, lists, c0, d3_world.peaks)
    with pytest.raises(SystemExit, match="absent from per_star"):
        rescoring_table(targets, d3_world.per_star[d3_world.per_star["sid"] != sid_for(90, 3)],
                        lists, c0, d3_world.peaks)
    broken = d3_world.per_star.copy()
    broken.loc[broken["sid"] == sid_for(90, 11), "baseline_days"] = math.nan
    with pytest.raises(SystemExit, match="without a finite baseline"):
        rescoring_table(targets, broken, lists, c0, d3_world.peaks)


# ---------------------------------------------------------------- P2 regime split

def _expected_p2(per_star):
    pos = per_star[per_star["class_label"] == "dsct_flag1"]
    return pos[pos["freq_scorable"].map(common.truthy) & (pos["best_status"] != "missing")
               & pos["low_available"].map(common.truthy) & pos["high_available"].map(common.truthy)
               & pos["eligible_any_pass"].map(common.truthy)]


def test_p2_regime_table_partition_and_counts_only_row(d3_world, per_star_roundtrip):
    for per_star in (d3_world.per_star, per_star_roundtrip):
        table = p2_regime_table(per_star)
        assert list(table.columns) == REGIME_COLUMNS
        assert table["dominant_frequency_regime"].tolist() == [
            "dominant_lt_4", "dominant_4_to_24", "dominant_ge_24"]
        assert table["lo_inclusive_per_day"].tolist() == [-math.inf, 4.0, 24.0]
        assert table["hi_exclusive_per_day"].tolist() == [4.0, 24.0, math.inf]
        _status_ok(table)
        frame = _expected_p2(per_star)
        dom = frame["primary_freq"].astype(float)
        assert int(table["n_p2"].sum()) == len(frame)
        conf = frame["best_status"] == "confirmed"
        direct = conf & (frame["best_candidate_matches_dominant"] == "direct")
        for name, lo, hi in (("dominant_lt_4", -math.inf, 4), ("dominant_4_to_24", 4, 24),
                             ("dominant_ge_24", 24, math.inf)):
            m = (dom >= lo) & (dom < hi)
            row = table.set_index("dominant_frequency_regime").loc[name]
            assert int(row["n_p2"]) == int(m.sum())
            assert int(row["k_confirmed"]) == int((conf & m).sum())
            assert int(row["k_direct_recovery"]) == int((direct & m).sum())
        ge = table.set_index("dominant_frequency_regime").loc["dominant_ge_24"]
        assert ge["n_p2"] > 0 and math.isnan(ge["rate_direct_recovery"])   # counts-only, as ruled
        lt = table.set_index("dominant_frequency_regime").loc["dominant_lt_4"]
        assert math.isclose(lt["rate_direct_recovery"], lt["k_direct_recovery"] / lt["n_p2"])


def test_p2_regime_half_open_edges():
    rows = []
    for j, (dom, cls) in enumerate(((3.999, "direct"), (4.0, "direct"), (23.999, "harmonic"),
                                    (24.0, "direct"), (24.4, "unmatched"), (0.5, "direct"))):
        rows.append({"sid": f"s{j}", "class_label": "dsct_flag1", "label_positive": True,
                     "primary_freq": dom, "freq_scorable": True, "baseline_days": 2000.0,
                     "best_status": "confirmed", "best_frequency_per_day": dom,
                     "low_available": True, "high_available": True, "eligible_any_pass": True,
                     "best_candidate_matches_any_mode": cls, "best_candidate_matches_dominant": cls,
                     "any_top_peak_matches_any_mode": True})
    per_star = pd.DataFrame(rows)
    table = p2_regime_table(per_star, expected_positives=6, expected_scorable=6)
    t = table.set_index("dominant_frequency_regime")
    assert t.loc["dominant_lt_4", "n_p2"] == 2 and t.loc["dominant_lt_4", "k_direct_recovery"] == 2
    assert t.loc["dominant_4_to_24", "n_p2"] == 2 and t.loc["dominant_4_to_24", "k_direct_recovery"] == 1
    assert t.loc["dominant_ge_24", "n_p2"] == 2 and t.loc["dominant_ge_24", "k_direct_recovery"] == 1
    assert math.isnan(t.loc["dominant_ge_24", "rate_direct_recovery"])
    assert t.loc["dominant_4_to_24", "rate_direct_recovery"] == 0.5
    with pytest.raises(SystemExit, match="freq_scorable positives"):
        p2_regime_table(per_star, expected_positives=6, expected_scorable=5)
    with pytest.raises(SystemExit, match="!= the frozen positive"):
        p2_regime_table(per_star, expected_positives=7, expected_scorable=6)


def test_verify_against_completeness(d3_bundle):
    table = p2_regime_table(d3_bundle["world"].per_star)
    completeness = pd.read_csv(d3_bundle["metrics"] / "completeness_by_class_pass_rule.csv")
    verify_against_completeness(table, completeness)
    bad = completeness.copy()
    bad.loc[bad["scope"] == "freq_recovery_scorable", "p"] += 1e-3
    with pytest.raises(SystemExit, match="does not reproduce"):
        verify_against_completeness(table, bad)
    with pytest.raises(SystemExit, match="no unique P2 row"):
        verify_against_completeness(table, completeness[completeness["scope"] != "freq_recovery_scorable"])


def test_assert_scorable_identity(d3_world):
    joined = assert_scorable_identity(d3_world.per_star, d3_world.roster, d3_world.table2)
    assert len(joined) == 456
    flipped = d3_world.per_star.copy()
    idx = flipped.index[(flipped["class_label"] == "dsct_flag1") & ~flipped["freq_scorable"]][0]
    flipped.loc[idx, "freq_scorable"] = True
    with pytest.raises(SystemExit, match="not the ruled mo_joined set"):
        assert_scorable_identity(flipped, d3_world.roster, d3_world.table2)


# ---------------------------------------------------------------- JSON binding

def test_json_sha_map_and_top_peaks(d3_bundle):
    inputs = json.loads((d3_bundle["metrics"] / "inputs_sha256.json").read_text())
    sha_map = json_sha_map(inputs)
    assert all(not k.endswith(".prov.json") for k in sha_map)
    assert f"{sid_for(90, 11)}.json" in sha_map
    with pytest.raises(SystemExit, match="two different SHAs"):
        json_sha_map({"a/x.json": "1", "b\\x.json": "2"})
    world = d3_bundle["world"]
    statuses = world.per_star.set_index("sid")["best_status"].to_dict()
    sids = [sid_for(90, 0), sid_for(90, 11), sid_for(90, 9)]
    peaks, used = load_top_peaks(d3_bundle["stars"], sids, statuses, sha_map)
    assert peaks[sid_for(90, 0)] == []                      # missing result -> no peaks
    assert peaks[sid_for(90, 11)] == world.peaks[sid_for(90, 11)]
    assert len(used) == 2
    # a JSON that is not the one the metrics scored is refused
    path = d3_bundle["stars"] / f"{sid_for(90, 11)}.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(SystemExit, match="differs from the JSON"):
        load_top_peaks(d3_bundle["stars"], sids, statuses, sha_map)
    with pytest.raises(SystemExit, match="not among the metrics bundle"):
        load_top_peaks(d3_bundle["stars"], [sid_for(90, 9)], statuses, {})


# ---------------------------------------------------------------- real roster facts

@real_data
def test_real_roster_facts_as_ruled():
    roster = common.load_roster(REAL_ROSTER)
    table1 = common.load_mo_table1(REAL_T1)
    table2 = common.load_mo_table2(REAL_T2)
    assert len(roster) == 3000
    targets = select_aliased_dominant(roster, table1)
    assert len(targets) == 40                                  # ruled: exactly 40
    assert (targets["n_qualifying_rows"] == 1).all()           # no tie-break needed in the fixed tables
    reflected = 2 * F_NYQ_UHZ - targets["fR_uhz"]
    assert (np.abs(reflected - targets["dom_freq_uhz"]) <= 0.1).all()
    joined = common.mo_joined_kics(roster, table2)
    assert len(joined) == 456                                  # ruled: 456 Mo-joined positives
    pos = roster[roster["class_label"] == "dsct_flag1"]
    assert len(pos) == 610
    dom = pos.loc[pos["KIC"].isin(joined), "dom_freq_per_day"]
    assert int(((dom >= 24.0) & (dom < 24.46848)).sum()) == 10  # ruled factual correction
    assert int((dom >= 24.46848).sum()) == 0
    assert 283.2 * 86400 / 1e6 == 24.46848                     # f_Nyq exactly as ruled
    lists = common.table2_per_day_lists(table2)
    assert all(len(lists[k]) >= 1 for k in joined)


# ---------------------------------------------------------------- CLI

def test_cli_end_to_end(d3_bundle):
    out = d3_bundle["out"]
    main(["--metrics-dir", str(d3_bundle["metrics"]), "--stars-dir", str(d3_bundle["stars"]),
          "--roster", str(d3_bundle["roster"]), "--mo-table1", str(d3_bundle["table1"]),
          "--mo-table2", str(d3_bundle["table2"]), "--out-dir", str(out)])
    rescoring = pd.read_csv(out / "d3_truth_provenance_rescoring.csv", dtype={"sid": str})
    regime = pd.read_csv(out / "d3_p2_by_dominant_frequency_regime.csv")
    assert list(rescoring.columns) == RESCORING_COLUMNS and len(rescoring) == 40
    assert list(regime.columns) == REGIME_COLUMNS and len(regime) == 3
    assert regime["n_p2"].sum() == d3_bundle["n_p2"]
    assert regime["k_direct_recovery"].sum() == d3_bundle["k_direct"]
    manifest = json.loads((out / "d3_truth_provenance.manifest.json").read_text())
    assert manifest["analysis_status"] == "postlaunch_descriptive"
    assert manifest["prespecified"] is False and manifest["interval"] == "none"
    assert "per_star.csv" in manifest["inputs_sha256"] and len(manifest["script_sha256"]) == 64
    assert set(manifest["outputs_sha256"]) == {"d3_truth_provenance_rescoring.csv",
                                               "d3_p2_by_dominant_frequency_regime.csv"}
    assert manifest["counts"]["n_aliased_dominant"] == 40
    readme = (out / "d3_truth_provenance.README.md").read_text()
    assert "Post-launch descriptive truth-provenance audit" in readme
    assert "stars with a confirmed super-Nyquist mode" in readme


def test_cli_refuses_pilot_bundle(d3_world, tmp_path):
    from conftest import write_bundle
    paths = write_bundle(d3_world, tmp_path, pilot=True)
    with pytest.raises(SystemExit, match="pilot"):
        main(["--metrics-dir", str(paths["metrics"]), "--stars-dir", str(paths["stars"]),
              "--roster", str(paths["roster"]), "--mo-table1", str(paths["table1"]),
              "--mo-table2", str(paths["table2"]), "--out-dir", str(paths["out"])])
