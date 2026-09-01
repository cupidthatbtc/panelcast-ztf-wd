"""Tests for the post-launch descriptive D3 negative-trigger strata and the
covariate-by-class table (reviews/G5prep/sol_round2.md item 6,
ADMIT-DESCRIPTIVE). Bin edges, unknown cells, sum identities and abort paths
run on synthetic frames; the frozen roster / crossmatch frame are exercised
directly where present."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))

from d3_strata_covariates import (  # noqa: E402
    COVARIATE_COLUMNS,
    COVARIATES,
    EXPECTED_NEGATIVES,
    MAGNITUDE_CELLS,
    OID_CELLS,
    SKY_CELLS,
    STRATA_COLUMNS,
    TEFF_CELLS,
    check_metrics_manifest,
    covariates_by_class,
    describe,
    magnitude_bin,
    merged_oid_bin,
    negative_frame,
    negative_trigger_strata,
    sky_cell,
    teff_bin,
)

ROSTER_PATH = REPO_ROOT / "generalization/data/d3/roster_d3.csv"
CROSSMATCH_PATH = (
    REPO_ROOT / "generalization/data/d3/crossmatch_freeze/crossmatch_adjudication.csv"
)
REAL_FILES = ROSTER_PATH.exists() and CROSSMATCH_PATH.exists()


# ---------------------------------------------------------------- fixtures

def make_roster(n_negatives=EXPECTED_NEGATIVES, n_positives=3, n_candidates=2):
    rows = []
    rng = np.random.default_rng(20260901)
    for i in range(n_negatives):
        rows.append({"source_id": f"90{i:017d}", "class_label": "dsct_flag0",
                     "gmag": 15.0, "Teff": 6800.0, "ra": 292.0, "dec": 42.0})
    for i in range(n_positives):
        rows.append({"source_id": f"91{i:017d}", "class_label": "dsct_flag1",
                     "gmag": 13.5, "Teff": 7200.0, "ra": 295.0, "dec": 45.0})
    for i in range(n_candidates):
        rows.append({"source_id": f"92{i:017d}", "class_label": "dsct_flag2",
                     "gmag": 14.5, "Teff": 6600.0, "ra": 291.0, "dec": 40.0})
    roster = pd.DataFrame(rows)
    roster["gmag"] = roster["gmag"] + rng.normal(0, 0.01, len(roster))
    return roster


def make_crossmatch(roster, selected=4):
    return pd.DataFrame({
        "source_id": roster["source_id"],
        "nearest_separation_arcsec": 0.1,
        "ztf_objects_in_cone": 10,
        "selected_ztf_objects": float(selected),
        "zg_clean_rows": 700,
        "zr_clean_rows": 1100,
    })


def make_per_star(roster, statuses=None):
    """Every roster member not_detected in both passes unless overridden by
    statuses: sid -> (best, low, high)."""
    statuses = statuses or {}
    rows = []
    for r in roster.itertuples(index=False):
        best, low, high = statuses.get(r.source_id, ("not_detected",) * 3)
        rows.append({"sid": r.source_id, "class_label": r.class_label,
                     "best_status": best, "low_status": low, "high_status": high})
    return pd.DataFrame(rows)


def strata_lookup(table, stratifier, stratum):
    row = table[(table["stratifier"] == stratifier) & (table["stratum"] == stratum)]
    assert len(row) == 1, (stratifier, stratum)
    return row.iloc[0]


# ---------------------------------------------------------------- bin rules

def test_magnitude_boundary_is_le_14_and_unknown_cell():
    assert magnitude_bin(14.0) == "g_le_14"          # boundary in the bright stratum
    assert magnitude_bin(13.2) == "g_le_14"
    assert magnitude_bin(14.0000001) == "g_gt_14"
    assert magnitude_bin(16.7) == "g_gt_14"
    assert magnitude_bin(float("nan")) == "g_unknown"
    assert magnitude_bin(None) == "g_unknown"
    assert magnitude_bin(float("inf")) == "g_unknown"
    assert magnitude_bin("x") == "g_unknown"


def test_teff_bins_half_open_at_frozen_cuts():
    assert teff_bin(6596.999) == "<6597"
    assert teff_bin(6597.0) == "[6597,6737)"
    assert teff_bin(6736.999) == "[6597,6737)"
    assert teff_bin(6737.0) == "[6737,7092.5)"
    assert teff_bin(7092.499) == "[6737,7092.5)"
    assert teff_bin(7092.5) == ">=7092.5"
    assert teff_bin(9998) == ">=7092.5"
    assert teff_bin(float("nan")) == "teff_unknown"
    assert TEFF_CELLS == ("<6597", "[6597,6737)", "[6737,7092.5)", ">=7092.5", "teff_unknown")


def test_merged_oid_bins():
    assert merged_oid_bin(0) == "oid_le_1" and merged_oid_bin(1) == "oid_le_1"
    assert merged_oid_bin(2) == "oid_2"
    assert merged_oid_bin(3) == "oid_3_4" and merged_oid_bin(4) == "oid_3_4"
    assert merged_oid_bin(5) == "oid_ge_5" and merged_oid_bin(8) == "oid_ge_5"
    assert merged_oid_bin(float("nan")) == "oid_unknown"
    assert merged_oid_bin(None) == "oid_unknown"
    assert OID_CELLS == ("oid_le_1", "oid_2", "oid_3_4", "oid_ge_5", "oid_unknown")


def test_sky_cells_half_open_grid_and_unknown():
    assert sky_cell(290.0945525, 41.048665) == "RAq2_DECq2"       # cut belongs to the upper cell
    assert sky_cell(290.0945524, 41.048664) == "RAq1_DECq1"
    assert sky_cell(293.54213, 43.879275) == "RAq3_DECq3"
    assert sky_cell(296.340635, 46.70182) == "RAq4_DECq4"
    assert sky_cell(296.340634, 46.70181) == "RAq3_DECq3"
    assert sky_cell(280.0, 52.3) == "RAq1_DECq4"
    assert sky_cell(float("nan"), 42.0) == "sky_unknown"
    assert sky_cell(292.0, float("nan")) == "sky_unknown"
    assert len(SKY_CELLS) == 17
    assert SKY_CELLS[0] == "RAq1_DECq1" and SKY_CELLS[15] == "RAq4_DECq4"
    assert SKY_CELLS[-1] == "sky_unknown"


# ---------------------------------------------------------------- strata

def test_strata_counts_identities_and_pass_rows_not_additive():
    roster = make_roster()
    crossmatch = make_crossmatch(roster)
    sids = roster.loc[roster["class_label"] == "dsct_flag0", "source_id"].tolist()
    a, b, c, d, e = sids[:5]
    # a: confirmed in both passes; b: low only; c: high only (best = high);
    # d: candidate (rule 2 only, never rule 1); e: missing (no light curve)
    statuses = {
        a: ("confirmed", "confirmed", "confirmed"),
        b: ("confirmed", "confirmed", "not_detected"),
        c: ("confirmed", "not_detected", "confirmed"),
        d: ("candidate", "candidate", "not_detected"),
        e: ("missing", "missing", "missing"),
    }
    roster.loc[roster["source_id"] == a, ["gmag", "Teff", "ra", "dec"]] = [14.0, 6597.0, 296.340635, 46.70182]
    roster.loc[roster["source_id"] == b, ["gmag", "Teff"]] = [14.0001, 7092.5]
    roster.loc[roster["source_id"] == e, ["gmag", "Teff", "ra"]] = [13.0, float("nan"), float("nan")]
    crossmatch.loc[crossmatch["source_id"] == a, "selected_ztf_objects"] = 2
    crossmatch.loc[crossmatch["source_id"] == b, "selected_ztf_objects"] = 5
    crossmatch.loc[crossmatch["source_id"] == c, "selected_ztf_objects"] = float("nan")
    per_star = make_per_star(roster, statuses)

    frame = negative_frame(per_star, roster, crossmatch)
    assert len(frame) == EXPECTED_NEGATIVES
    table = negative_trigger_strata(frame)
    assert list(table.columns) == STRATA_COLUMNS
    assert (table["rule"] == "confirmed").all()
    assert (table["analysis_status"] == "postlaunch_descriptive").all()
    assert (~table["prespecified"].astype(bool)).all()
    assert (table["interval"] == "none").all()

    # every cell of every stratifier is emitted, in the ruled order
    for stratifier, cells in (("magnitude", MAGNITUDE_CELLS), ("teff", TEFF_CELLS),
                              ("merged_oid", OID_CELLS), ("sky", SKY_CELLS)):
        sub = table[table["stratifier"] == stratifier]
        assert sub["stratum"].tolist() == list(cells)
        assert (sub["pass_basis"] == "best").all()
        assert int(sub["n_negative"].sum()) == EXPECTED_NEGATIVES
        assert int(sub["k_confirmed"].sum()) == 3           # a, b, c under rule 1 best pass
    assert table["stratifier"].drop_duplicates().tolist() == \
        ["magnitude", "teff", "merged_oid", "pass", "sky"]

    # magnitude: a (14.0) is g_le_14 with e (missing, 13.0) in the denominator only
    mag_le = strata_lookup(table, "magnitude", "g_le_14")
    assert int(mag_le["n_negative"]) == 2 and int(mag_le["k_confirmed"]) == 1
    assert math.isclose(mag_le["rate"], 0.5)
    mag_gt = strata_lookup(table, "magnitude", "g_gt_14")
    assert int(mag_gt["n_negative"]) == EXPECTED_NEGATIVES - 2 and int(mag_gt["k_confirmed"]) == 2
    assert int(strata_lookup(table, "magnitude", "g_unknown")["n_negative"]) == 0
    assert math.isnan(strata_lookup(table, "magnitude", "g_unknown")["rate"])  # blank at zero denominator

    # teff: a sits on the 6597 cut (upper cell), b on 7092.5 (top cell), e unknown
    assert int(strata_lookup(table, "teff", "<6597")["n_negative"]) == 0
    assert int(strata_lookup(table, "teff", "[6597,6737)")["k_confirmed"]) == 1
    assert int(strata_lookup(table, "teff", ">=7092.5")["k_confirmed"]) == 1
    unknown_teff = strata_lookup(table, "teff", "teff_unknown")
    assert int(unknown_teff["n_negative"]) == 1 and int(unknown_teff["k_confirmed"]) == 0
    assert math.isclose(unknown_teff["rate"], 0.0)

    # merged oids: a -> oid_2, b -> oid_ge_5, c -> unknown, rest oid_3_4
    assert int(strata_lookup(table, "merged_oid", "oid_2")["k_confirmed"]) == 1
    assert int(strata_lookup(table, "merged_oid", "oid_ge_5")["k_confirmed"]) == 1
    unknown_oid = strata_lookup(table, "merged_oid", "oid_unknown")
    assert int(unknown_oid["n_negative"]) == 1 and int(unknown_oid["k_confirmed"]) == 1
    assert int(strata_lookup(table, "merged_oid", "oid_le_1")["n_negative"]) == 0

    # sky: a at the top corner -> RAq4_DECq4; e has NaN RA -> sky_unknown
    assert int(strata_lookup(table, "sky", "RAq4_DECq4")["k_confirmed"]) == 1
    assert int(strata_lookup(table, "sky", "sky_unknown")["n_negative"]) == 1
    assert int(strata_lookup(table, "sky", "RAq2_DECq2")["n_negative"]) == EXPECTED_NEGATIVES - 2

    # pass rows: each over ALL negatives; low = a,b (2); high = a,c (2); 2+2 != 3
    low = strata_lookup(table, "pass", "low")
    high = strata_lookup(table, "pass", "high")
    assert low["pass_basis"] == "low" and high["pass_basis"] == "high"
    assert int(low["n_negative"]) == EXPECTED_NEGATIVES == int(high["n_negative"])
    assert int(low["k_confirmed"]) == 2 and int(high["k_confirmed"]) == 2
    assert int(low["k_confirmed"]) + int(high["k_confirmed"]) != 3
    assert math.isclose(high["rate"], 2 / EXPECTED_NEGATIVES)


def test_missing_and_candidate_negatives_are_non_triggers_in_every_denominator():
    roster = make_roster()
    crossmatch = make_crossmatch(roster)
    sids = roster.loc[roster["class_label"] == "dsct_flag0", "source_id"].tolist()
    statuses = {s: ("missing", "missing", "missing") for s in sids[:100]}
    statuses.update({s: ("candidate", "candidate", "candidate") for s in sids[100:150]})
    table = negative_trigger_strata(
        negative_frame(make_per_star(roster, statuses), roster, crossmatch))
    assert (table["k_confirmed"] == 0).all()
    assert int(table[table["stratifier"] == "magnitude"]["n_negative"].sum()) == EXPECTED_NEGATIVES
    assert (table[table["stratifier"] == "pass"]["n_negative"] == EXPECTED_NEGATIVES).all()
    assert (table[table["n_negative"] > 0]["rate"] == 0.0).all()
    assert table[table["n_negative"] == 0]["rate"].isna().all()


def test_other_classes_never_enter_the_negative_frame():
    roster = make_roster()
    crossmatch = make_crossmatch(roster)
    pos = roster.loc[roster["class_label"] == "dsct_flag1", "source_id"].iloc[0]
    cand = roster.loc[roster["class_label"] == "dsct_flag2", "source_id"].iloc[0]
    per_star = make_per_star(roster, {pos: ("confirmed",) * 3, cand: ("confirmed",) * 3})
    frame = negative_frame(per_star, roster, crossmatch)
    assert pos not in set(frame["sid"]) and cand not in set(frame["sid"])
    assert negative_trigger_strata(frame)["k_confirmed"].sum() == 0


def test_abort_paths():
    roster = make_roster()
    crossmatch = make_crossmatch(roster)
    per_star = make_per_star(roster)

    with pytest.raises(SystemExit, match="refusing to stratify"):
        negative_frame(per_star.iloc[1:], roster, crossmatch)   # 2,313 negatives
    dup = per_star.copy()
    neg_idx = dup.index[dup["class_label"] == "dsct_flag0"]
    dup.loc[neg_idx[-1], "sid"] = dup.loc[neg_idx[0], "sid"]   # count intact, one sid twice
    with pytest.raises(SystemExit, match="duplicate sids"):
        negative_frame(dup, roster, crossmatch)
    swapped = per_star.copy()
    swapped.loc[swapped.index[0], "sid"] = "9099999999999999999"
    with pytest.raises(SystemExit, match="sid sets differ"):
        negative_frame(swapped, roster, crossmatch)
    with pytest.raises(SystemExit, match="roster holds"):
        negative_frame(per_star, roster.iloc[1:], crossmatch)
    with pytest.raises(SystemExit, match="does not cover"):
        negative_frame(per_star, roster, crossmatch.iloc[10:])
    with pytest.raises(SystemExit, match="duplicate source_id in the crossmatch"):
        negative_frame(per_star, roster, pd.concat([crossmatch, crossmatch.iloc[[0]]]))
    odd = per_star.copy()
    odd.loc[odd.index[0], "low_status"] = "detected"
    with pytest.raises(SystemExit, match="unexpected low_status"):
        negative_frame(odd, roster, crossmatch)
    with pytest.raises(SystemExit, match="rows !="):
        negative_trigger_strata(negative_frame(per_star, roster, crossmatch).iloc[:10])


def test_check_metrics_manifest_refuses_pilot_and_other_datasets():
    check_metrics_manifest({"dataset": "d3", "pilot": False})
    with pytest.raises(SystemExit, match="pilot"):
        check_metrics_manifest({"dataset": "d3", "pilot": True})
    with pytest.raises(SystemExit, match="not dataset d3"):
        check_metrics_manifest({"dataset": "d2", "pilot": False})


# ---------------------------------------------------------------- covariates

def test_describe_population_sd_and_linear_quantiles():
    d = describe(np.array([1.0, 2.0, 3.0, 4.0, float("nan"), float("inf")]))
    assert math.isclose(d["mean"], 2.5)
    assert math.isclose(d["sd"], math.sqrt(1.25))          # ddof=0
    assert math.isclose(d["p25"], 1.75) and math.isclose(d["p50"], 2.5)
    assert math.isclose(d["p10"], 1.3) and math.isclose(d["p90"], 3.7)
    assert d["min"] == 1.0 and d["max"] == 4.0
    empty = describe(np.array([float("nan")]))
    assert all(math.isnan(v) for v in empty.values())


def test_covariates_by_class_long_format():
    roster = pd.DataFrame([
        {"source_id": "9000000000000000001", "class_label": "dsct_flag0", "gmag": 14.0, "Teff": 6600, "ra": 290.0, "dec": 40.0},
        {"source_id": "9000000000000000002", "class_label": "dsct_flag0", "gmag": 15.0, "Teff": 6800, "ra": 291.0, "dec": 41.0},
        {"source_id": "9000000000000000003", "class_label": "dsct_flag0", "gmag": 16.0, "Teff": 7000, "ra": 292.0, "dec": 42.0},
        {"source_id": "9000000000000000004", "class_label": "dsct_flag0", "gmag": 17.0, "Teff": 7200, "ra": 293.0, "dec": 43.0},
        {"source_id": "9000000000000000005", "class_label": "dsct_flag1", "gmag": 13.5, "Teff": 7100, "ra": 294.0, "dec": 44.0},
        {"source_id": "9000000000000000006", "class_label": "dsct_flag2", "gmag": float("nan"), "Teff": 6900, "ra": 295.0, "dec": 45.0},
    ])
    crossmatch = make_crossmatch(roster)
    crossmatch["nearest_separation_arcsec"] = [0.1, 0.2, float("nan"), 0.4, 0.5, float("nan")]
    table = covariates_by_class(roster, crossmatch, expected_roster=6)
    assert list(table.columns) == COVARIATE_COLUMNS
    assert len(table) == 3 * len(COVARIATES)
    assert table["class_label"].drop_duplicates().tolist() == ["dsct_flag0", "dsct_flag1", "dsct_flag2"]
    assert table[table["class_label"] == "dsct_flag0"]["covariate"].tolist() == list(COVARIATES)
    g0 = table[(table["class_label"] == "dsct_flag0") & (table["covariate"] == "gmag")].iloc[0]
    assert int(g0["n_class"]) == 4 and int(g0["n_nonmissing"]) == 4 and int(g0["n_missing"]) == 0
    assert math.isclose(g0["mean"], 15.5) and math.isclose(g0["sd"], math.sqrt(1.25))
    assert math.isclose(g0["p25"], 14.75) and math.isclose(g0["p75"], 16.25)
    assert g0["min"] == 14.0 and g0["max"] == 17.0
    sep0 = table[(table["class_label"] == "dsct_flag0")
                 & (table["covariate"] == "nearest_separation_arcsec")].iloc[0]
    assert int(sep0["n_nonmissing"]) == 3 and int(sep0["n_missing"]) == 1
    g2 = table[(table["class_label"] == "dsct_flag2") & (table["covariate"] == "gmag")].iloc[0]
    assert int(g2["n_class"]) == 1 and int(g2["n_nonmissing"]) == 0 and int(g2["n_missing"]) == 1
    assert all(math.isnan(g2[k]) for k in ("mean", "sd", "p10", "p50", "p90", "min", "max"))
    assert (table["analysis_status"] == "postlaunch_descriptive").all()
    assert (~table["prespecified"].astype(bool)).all()
    assert (table["interval"] == "none").all()

    with pytest.raises(SystemExit, match="rows !="):
        covariates_by_class(roster, crossmatch, expected_roster=7)
    with pytest.raises(SystemExit, match="class levels"):
        covariates_by_class(roster[roster["class_label"] != "dsct_flag2"], crossmatch,
                            expected_roster=5)
    with pytest.raises(SystemExit, match="does not cover"):
        covariates_by_class(roster, crossmatch.iloc[1:], expected_roster=6)
    with pytest.raises(SystemExit, match="columns missing"):
        covariates_by_class(roster, crossmatch.drop(columns=["zg_clean_rows"]), expected_roster=6)


# ---------------------------------------------------------------- real frames

@pytest.mark.skipif(not REAL_FILES, reason="frozen D3 roster/crossmatch frame not present")
def test_real_roster_covariate_table():
    roster = pd.read_csv(ROSTER_PATH, dtype={"source_id": str})
    crossmatch = pd.read_csv(CROSSMATCH_PATH, dtype={"source_id": str})
    table = covariates_by_class(roster, crossmatch)
    assert len(table) == 27
    n_class = table.drop_duplicates("class_label").set_index("class_label")["n_class"]
    assert n_class.to_dict() == {"dsct_flag0": 2314, "dsct_flag1": 610, "dsct_flag2": 76}
    by = table.set_index(["class_label", "covariate"])
    assert (by.xs("gmag", level="covariate")["n_missing"] == 0).all()
    assert (by.xs("Teff", level="covariate")["n_missing"] == 0).all()
    assert int(by.xs("nearest_separation_arcsec", level="covariate")["n_missing"].sum()) == 45
    assert (by.xs("nearest_separation_arcsec", level="covariate")["n_nonmissing"]
            + by.xs("nearest_separation_arcsec", level="covariate")["n_missing"]
            == n_class.reindex(by.xs("nearest_separation_arcsec", level="covariate").index)).all()
    assert by.loc[("dsct_flag0", "gmag"), "min"] >= 13.2
    assert by.loc[("dsct_flag0", "selected_ztf_objects"), "max"] == 8


@pytest.mark.skipif(not REAL_FILES, reason="frozen D3 roster/crossmatch frame not present")
def test_real_roster_strata_membership():
    """Stratum membership over the real 2,314 negatives with an all-not_detected
    synthetic result frame: every frozen cut is exercised, every stratifier
    sums to 2,314, and the three gmag == 14.000 negatives land in g_le_14."""
    roster = pd.read_csv(ROSTER_PATH, dtype={"source_id": str})
    crossmatch = pd.read_csv(CROSSMATCH_PATH, dtype={"source_id": str})
    per_star = make_per_star(roster)
    table = negative_trigger_strata(negative_frame(per_star, roster, crossmatch))
    for stratifier in ("magnitude", "teff", "merged_oid", "sky"):
        assert int(table[table["stratifier"] == stratifier]["n_negative"].sum()) == 2314
    assert (table["k_confirmed"] == 0).all()

    neg = roster[roster["class_label"] == "dsct_flag0"]
    n_le = int(strata_lookup(table, "magnitude", "g_le_14")["n_negative"])
    assert n_le == int((neg["gmag"] <= 14.0).sum())
    assert n_le == int((neg["gmag"] < 14.0).sum()) + 3
    assert int(strata_lookup(table, "magnitude", "g_unknown")["n_negative"]) == 0

    teff_counts = {c: int(strata_lookup(table, "teff", c)["n_negative"]) for c in TEFF_CELLS}
    assert all(teff_counts[c] > 0 for c in TEFF_CELLS[:-1])
    assert teff_counts["teff_unknown"] == 0
    assert teff_counts == {"<6597": 716, "[6597,6737)": 698, "[6737,7092.5)": 615,
                           ">=7092.5": 285, "teff_unknown": 0}

    oid_counts = {c: int(strata_lookup(table, "merged_oid", c)["n_negative"]) for c in OID_CELLS}
    assert oid_counts == {"oid_le_1": 46, "oid_2": 438, "oid_3_4": 1439,
                          "oid_ge_5": 391, "oid_unknown": 0}

    sky = table[table["stratifier"] == "sky"].set_index("stratum")["n_negative"]
    assert int(sky["sky_unknown"]) == 0
    assert int((sky.drop("sky_unknown") > 0).sum()) >= 12
    assert int(strata_lookup(table, "pass", "high")["n_negative"]) == 2314
