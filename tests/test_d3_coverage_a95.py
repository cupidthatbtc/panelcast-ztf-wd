"""Tests for the post-launch descriptive D3-vs-pool coverage table and the
per-pass, per-band a95 table (reviews/G5prep/sol_round2.md item 7,
ADMIT-DESCRIPTIVE). Synthetic census frames and JSON fixtures exercise the
definitions and abort paths; the frozen D3 census panel and the published
928-star pool are exercised directly where present."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))

from d3_coverage_a95 import (  # noqa: E402
    A95_COLUMNS,
    BANDS,
    CLASS_LEVELS,
    COVERAGE_COLUMNS,
    COVERAGE_METRICS,
    PASSES,
    a95_table,
    check_metrics_manifest,
    coverage_table,
    read_a95_records,
    verify_records_against_per_star,
)

D3_CENSUS_PATH = (
    REPO_ROOT / "generalization/data/d3/crossmatch_freeze/panels_census_generic.csv"
)
POOL_CENSUS_PATH = (
    REPO_ROOT / "catalog-rebuild/results/2026-08-01_full/catalog/census_full_catalog.csv"
)
D1_STARS_DIR = REPO_ROOT / "catalog-rebuild/results/2026-08-01_full/lomb-scargle/stars"


# ---------------------------------------------------------------- coverage

def make_census(n, seed=1):
    rng = np.random.default_rng(seed)
    nights = rng.integers(20, 300, n)
    return pd.DataFrame({
        "source_id": [f"90{i:017d}" for i in range(n)],
        "zg_n_exp": nights + rng.integers(0, 200, n),
        "zg_n_nights": nights,
        "zr_n_exp": nights + rng.integers(0, 300, n),
        "zr_n_nights": nights + rng.integers(0, 5, n),
    })


def test_coverage_table_definitions_and_linear_quantiles():
    d3 = pd.DataFrame({
        "source_id": ["a", "b", "c", "d"],
        "zg_n_exp": [10, 20, 30, 40], "zg_n_nights": [10, 15, 20, 25],
        "zr_n_exp": [1, 2, 3, 4], "zr_n_nights": [1, 1, 1, 1],
    })
    pool = make_census(7, seed=2)
    table = coverage_table(d3, pool, expected_d3=4, expected_pool=7)
    assert list(table.columns) == COVERAGE_COLUMNS
    assert len(table) == 10
    assert table["frame"].tolist() == ["D3_crossmatched"] * 5 + ["development_pool"] * 5
    assert table[table["frame"] == "D3_crossmatched"]["covariate"].tolist() == list(COVERAGE_METRICS)
    by = table.set_index(["frame", "covariate"])
    wg = by.loc[("D3_crossmatched", "wg_contrasts")]
    assert int(wg["n_frame"]) == 4 and int(wg["n_nonmissing"]) == 4
    assert wg["min"] == 0 and wg["max"] == 15                     # 10-10, 20-15, 30-20, 40-25
    assert math.isclose(wg["p50"], 7.5) and math.isclose(wg["p25"], 3.75)  # linear
    assert math.isclose(wg["p10"], 1.5) and math.isclose(wg["p90"], 13.5)
    zg = by.loc[("D3_crossmatched", "zg_n_exp")]
    assert zg["min"] == 10 and zg["max"] == 40 and math.isclose(zg["p75"], 32.5)
    assert int(by.loc[("development_pool", "zr_n_nights"), "n_frame"]) == 7
    assert (table["analysis_status"] == "postlaunch_descriptive").all()
    assert (~table["prespecified"].astype(bool)).all()
    assert (table["interval"] == "none").all()


def test_coverage_aborts_on_frame_size_negative_wg_and_missing_columns():
    d3 = make_census(5)
    pool = make_census(3, seed=3)
    with pytest.raises(SystemExit, match="ruled frame size"):
        coverage_table(d3, pool, expected_d3=6, expected_pool=3)
    with pytest.raises(SystemExit, match="ruled frame size"):
        coverage_table(d3, pool, expected_d3=5, expected_pool=2)
    bad = d3.copy()
    bad.loc[0, "zg_n_nights"] = bad.loc[0, "zg_n_exp"] + 1
    with pytest.raises(SystemExit, match="wg_contrasts .* is negative"):
        coverage_table(bad, pool, expected_d3=5, expected_pool=3)
    with pytest.raises(SystemExit, match="columns missing"):
        coverage_table(d3.drop(columns=["zr_n_nights"]), pool, expected_d3=5, expected_pool=3)
    with pytest.raises(SystemExit, match="duplicate source_id"):
        coverage_table(pd.concat([d3, d3.iloc[[0]]]), pool, expected_d3=6, expected_pool=3)


def test_coverage_missing_values_are_excluded_not_imputed():
    d3 = make_census(4).astype({"zg_n_exp": float})
    d3.loc[0, "zg_n_exp"] = float("nan")
    pool = make_census(3, seed=5)
    table = coverage_table(d3, pool, expected_d3=4, expected_pool=3).set_index(["frame", "covariate"])
    assert int(table.loc[("D3_crossmatched", "zg_n_exp"), "n_nonmissing"]) == 3
    assert int(table.loc[("D3_crossmatched", "wg_contrasts"), "n_nonmissing"]) == 3
    assert int(table.loc[("D3_crossmatched", "zg_n_nights"), "n_nonmissing"]) == 4


@pytest.mark.skipif(not (D3_CENSUS_PATH.exists() and POOL_CENSUS_PATH.exists()),
                    reason="frozen D3 census panel / published pool census not present")
def test_real_coverage_frames():
    d3 = pd.read_csv(D3_CENSUS_PATH, dtype={"source_id": str})
    pool = pd.read_csv(POOL_CENSUS_PATH, dtype={"source_id": str})
    table = coverage_table(d3, pool).set_index(["frame", "covariate"])
    assert int(table.loc[("D3_crossmatched", "zg_n_exp"), "n_frame"]) == 2901
    assert int(table.loc[("development_pool", "zg_n_exp"), "n_frame"]) == 928
    assert (table["n_nonmissing"] == table["n_frame"]).all()
    assert table.loc[("D3_crossmatched", "wg_contrasts"), "min"] >= 0
    assert table.loc[("development_pool", "wg_contrasts"), "min"] >= 0
    assert np.isfinite(table["p50"]).all()
    assert table.loc[("D3_crossmatched", "wg_contrasts"), "p50"] == (
        float(np.quantile(d3["zg_n_exp"] - d3["zg_n_nights"], 0.5)))


# ---------------------------------------------------------------- a95 fixtures

def make_roster():
    rows = []
    for i in range(4):
        rows.append({"source_id": f"90{i:017d}", "class_label": "dsct_flag0"})
    for i in range(2):
        rows.append({"source_id": f"91{i:017d}", "class_label": "dsct_flag1"})
    rows.append({"source_id": "9200000000000000000", "class_label": "dsct_flag2"})
    return pd.DataFrame(rows)


def write_json(stars_dir: Path, sid: str, a95: dict, unavailable=(), complete=True,
               drop_key=None, passes=("low", "high"), source_id=None):
    """a95: {(pass, band): value}. unavailable passes get available=False and
    None a95 values exactly like the frozen unavailable_pass_result."""
    result = {"schema_version": 1, "source_id": source_id or sid, "n_exp_zg": 100,
              "n_exp_zr": 100, "baseline_days": 2000.0, "passes": {}, "complete": complete}
    for p in passes:
        block = {"status": "not_detected", "basis": "", "frequency_per_day": None,
                 "best_band_fap": 1.0, "top_peaks": []}
        for band in BANDS:
            block[f"{band}_a95_mmag"] = None if p in unavailable else a95.get((p, band))
        if p in unavailable:
            block["available"] = False
            block["unavailable_reason"] = "baseline too short"
        if drop_key and drop_key[0] == p:
            block.pop(drop_key[1])
        result["passes"][p] = block
    (stars_dir / f"{sid}.json").write_text(json.dumps(result), encoding="utf-8")


def build_stars(tmp_path: Path):
    """4 negatives: one without a JSON, one with the high pass unavailable;
    2 positives with values; the candidate has a JSON with None a95 in zr."""
    stars = tmp_path / "stars"
    stars.mkdir()
    v = lambda lo_g, lo_r, hi_g, hi_r: {  # noqa: E731
        ("low", "zg"): lo_g, ("low", "zr"): lo_r, ("high", "zg"): hi_g, ("high", "zr"): hi_r}
    write_json(stars, "9000000000000000000", v(1.0, 2.0, 3.0, 4.0))
    write_json(stars, "9000000000000000001", v(5.0, 6.0, 7.0, 8.0), unavailable=("high",))
    write_json(stars, "9000000000000000002", v(9.0, 10.0, 11.0, 12.0))
    # 9000000000000000003 has no JSON (missing light curve)
    write_json(stars, "9100000000000000000", v(20.0, 30.0, 40.0, 50.0))
    write_json(stars, "9100000000000000001", v(22.0, 32.0, 42.0, 52.0))
    write_json(stars, "9200000000000000000", v(70.0, None, 80.0, None))
    return stars


def make_per_star(roster, records):
    rows = []
    for r in roster.itertuples(index=False):
        rec = records.get(r.source_id)
        rows.append({
            "sid": r.source_id, "class_label": r.class_label,
            "best_status": "not_detected" if rec else "missing",
            "low_available": rec["available"]["low"] if rec else float("nan"),
            "high_available": rec["available"]["high"] if rec else float("nan"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- a95 table

def test_a95_table_cells_counts_and_quantiles(tmp_path):
    roster = make_roster()
    stars = build_stars(tmp_path)
    records = read_a95_records(stars, roster["source_id"].tolist())
    assert set(records) == set(roster["source_id"]) - {"9000000000000000003"}
    table = a95_table(roster, records, expected_roster=7)
    assert list(table.columns) == A95_COLUMNS
    assert len(table) == 12
    expected_order = [(c, p, b) for c in CLASS_LEVELS for p in PASSES for b in BANDS]
    assert list(zip(table["class_label"], table["pass"], table["band"])) == expected_order
    by = table.set_index(["class_label", "pass", "band"])

    # negatives: 4 roster, 3 JSON, high pass available for 2, finite values
    low_zg = by.loc[("dsct_flag0", "low", "zg")]
    assert int(low_zg["n_roster"]) == 4 and int(low_zg["n_json"]) == 3
    assert int(low_zg["n_pass_available"]) == 3 and int(low_zg["n_finite"]) == 3
    assert int(low_zg["n_missing"]) == 1
    assert low_zg["min"] == 1.0 and low_zg["max"] == 9.0 and low_zg["p50"] == 5.0
    assert math.isclose(low_zg["p25"], 3.0) and math.isclose(low_zg["p05"], 1.4)  # linear
    high_zr = by.loc[("dsct_flag0", "high", "zr")]
    assert int(high_zr["n_pass_available"]) == 2 and int(high_zr["n_finite"]) == 2
    assert int(high_zr["n_missing"]) == 2                         # unavailable + no JSON
    assert high_zr["min"] == 4.0 and high_zr["max"] == 12.0 and high_zr["p50"] == 8.0
    # bands are never pooled: zg and zr differ
    assert by.loc[("dsct_flag0", "high", "zg"), "p50"] == 7.0

    pos = by.loc[("dsct_flag1", "low", "zr")]
    assert int(pos["n_roster"]) == 2 == int(pos["n_json"]) == int(pos["n_finite"])
    assert int(pos["n_missing"]) == 0 and pos["p50"] == 31.0 and pos["p95"] == 31.9

    cand_zr = by.loc[("dsct_flag2", "low", "zr")]
    assert int(cand_zr["n_json"]) == 1 and int(cand_zr["n_pass_available"]) == 1
    assert int(cand_zr["n_finite"]) == 0 and int(cand_zr["n_missing"]) == 1
    assert all(math.isnan(cand_zr[k]) for k in ("min", "p05", "p50", "p95", "max"))  # blank
    cand_zg = by.loc[("dsct_flag2", "high", "zg")]
    assert int(cand_zg["n_finite"]) == 1 and cand_zg["min"] == 80.0 == cand_zg["max"]

    assert (table["n_finite"] + table["n_missing"] == table["n_roster"]).all()
    assert (table["analysis_status"] == "postlaunch_descriptive").all()
    assert (~table["prespecified"].astype(bool)).all()
    assert (table["interval"] == "none").all()


def test_a95_reader_fails_closed_on_schema_deviations(tmp_path):
    roster = make_roster()
    stars = tmp_path / "s"
    stars.mkdir()
    v = {(p, b): 1.0 for p in PASSES for b in BANDS}
    write_json(stars, "9000000000000000000", v, drop_key=("high", "zr_a95_mmag"))
    with pytest.raises(SystemExit, match="no 'zr_a95_mmag' key"):
        read_a95_records(stars, roster["source_id"].tolist())
    write_json(stars, "9000000000000000000", v, complete=False)
    with pytest.raises(SystemExit, match="not complete"):
        read_a95_records(stars, roster["source_id"].tolist())
    write_json(stars, "9000000000000000000", v, passes=("low",))
    with pytest.raises(SystemExit, match="passes != low/high"):
        read_a95_records(stars, roster["source_id"].tolist())
    write_json(stars, "9000000000000000000", v, source_id="9000000000000000009")
    with pytest.raises(SystemExit, match="source_id"):
        read_a95_records(stars, roster["source_id"].tolist())
    # ids that are not requested are ignored; a non-roster record is refused
    write_json(stars, "9000000000000000000", v)
    write_json(stars, "9099999999999999999", v)
    records = read_a95_records(stars, roster["source_id"].tolist())
    assert set(records) == {"9000000000000000000"}
    with pytest.raises(SystemExit, match="non-roster"):
        a95_table(roster, {**records, "9099999999999999999": records["9000000000000000000"]},
                  expected_roster=7)
    with pytest.raises(SystemExit, match="rows !="):
        a95_table(roster, records, expected_roster=8)
    with pytest.raises(SystemExit, match="class levels"):
        a95_table(roster[roster["class_label"] != "dsct_flag2"], records, expected_roster=6)


def test_verify_records_against_per_star(tmp_path):
    roster = make_roster()
    stars = build_stars(tmp_path)
    records = read_a95_records(stars, roster["source_id"].tolist())
    per_star = make_per_star(roster, records)
    verify_records_against_per_star(roster, records, per_star)

    scored = per_star.copy()   # per_star says scored but there is no JSON
    scored.loc[scored["sid"] == "9000000000000000003", "best_status"] = "not_detected"
    with pytest.raises(SystemExit, match="JSON absent"):
        verify_records_against_per_star(roster, records, scored)
    unscored = per_star.copy()  # JSON present but per_star says missing
    unscored.loc[unscored["sid"] == "9000000000000000000", "best_status"] = "missing"
    with pytest.raises(SystemExit, match="JSON present"):
        verify_records_against_per_star(roster, records, unscored)
    flipped = per_star.copy()
    flipped.loc[flipped["sid"] == "9000000000000000001", "high_available"] = True
    with pytest.raises(SystemExit, match="high_available disagrees"):
        verify_records_against_per_star(roster, records, flipped)
    relabelled = per_star.copy()
    relabelled.loc[relabelled["sid"] == "9000000000000000000", "class_label"] = "dsct_flag1"
    with pytest.raises(SystemExit, match="class_label"):
        verify_records_against_per_star(roster, records, relabelled)
    with pytest.raises(SystemExit, match="sid set"):
        verify_records_against_per_star(roster, records, per_star.iloc[1:])
    # the CSV round-trip form of the availability flags ("True"/"False") is accepted
    text = per_star.copy()
    text["low_available"] = text["low_available"].map(
        lambda x: "" if isinstance(x, float) and math.isnan(x) else str(bool(x)))
    verify_records_against_per_star(roster, records, text)


def test_check_metrics_manifest_refuses_pilot_and_other_datasets():
    check_metrics_manifest({"dataset": "d3", "pilot": False})
    with pytest.raises(SystemExit, match="pilot"):
        check_metrics_manifest({"dataset": "d3", "pilot": True})
    with pytest.raises(SystemExit, match="not dataset d3"):
        check_metrics_manifest({"dataset": "d1"})


@pytest.mark.skipif(not D1_STARS_DIR.exists(), reason="published D1 per-star JSONs not present")
def test_published_json_schema_carries_the_ruled_a95_key_path():
    """The campaign per-star JSONs share the published schema: the reader must
    accept a real published result and find passes[pass][band+'_a95_mmag']."""
    sid = "1004340654352214656"
    records = read_a95_records(D1_STARS_DIR, [sid])
    assert set(records) == {sid}
    rec = records[sid]
    assert rec["available"] == {"low": True, "high": True}
    assert set(rec["a95"]) == {(p, b) for p in PASSES for b in BANDS}
    assert all(math.isfinite(float(v)) for v in rec["a95"].values())
