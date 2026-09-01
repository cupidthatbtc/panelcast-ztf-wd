"""METRICS_SPEC compliance tables (G5prep round 2, item 1): the == 456
frequency-scorable guard, ruled bin edges (left-closed/right-open, g <= 14.0),
cumulative attrition stages, and the Mo-joined vs unjoined covariate table."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization"))

import metrics_generalization as mg  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def test_real_roster_guard_456_and_identity():
    truth = mg.truth_d3()
    roster, mo = mg._d3_sources()
    joined = mg.d3_mo_joined(roster, mo)
    assert int(joined.sum()) == 456
    mg.d3_freq_scorable_guard(truth, joined)          # must not raise
    bad = joined.copy(); bad.iloc[0] = not bad.iloc[0]
    with pytest.raises(SystemExit):
        mg.d3_freq_scorable_guard(truth, bad)


def test_bin_edges_are_left_closed_right_open():
    b = mg._left_closed_bin
    assert b(float("nan"), mg.D3_AMP_EDGES_MMAG, mg.D3_AMP_LABELS, "amp_unknown") == "amp_unknown"
    assert b(0.4999, mg.D3_AMP_EDGES_MMAG, mg.D3_AMP_LABELS, "u") == "<0.5"
    assert b(0.5, mg.D3_AMP_EDGES_MMAG, mg.D3_AMP_LABELS, "u") == "[0.5,1)"
    assert b(49.999, mg.D3_AMP_EDGES_MMAG, mg.D3_AMP_LABELS, "u") == "[20,50)"
    assert b(50.0, mg.D3_AMP_EDGES_MMAG, mg.D3_AMP_LABELS, "u") == ">=50"
    assert b(2000.0, mg.D3_PERIOD_EDGES_S, mg.D3_PERIOD_LABELS, "u") == "[2000 s,0.05 d)"
    assert b(0.05 * 86400 - 1e-9, mg.D3_PERIOD_EDGES_S, mg.D3_PERIOD_LABELS, "u") == "[2000 s,0.05 d)"
    assert b(0.05 * 86400, mg.D3_PERIOD_EDGES_S, mg.D3_PERIOD_LABELS, "u") == "[0.05,0.2) d"
    assert b(100 * 86400, mg.D3_PERIOD_EDGES_S, mg.D3_PERIOD_LABELS, "u") == ">=100 d"
    assert b(6597.0, mg.D3_TEFF_CUTS_K, mg.D3_TEFF_LABELS, "u") == "[6597,6737)"
    assert b(6596.999, mg.D3_TEFF_CUTS_K, mg.D3_TEFF_LABELS, "u") == "<6597"
    assert b(7092.5, mg.D3_TEFF_CUTS_K, mg.D3_TEFF_LABELS, "u") == ">=7092.5"
    assert b(1.0, mg.D3_SEP_CUTS_ARCSEC, mg.D3_SEP_LABELS, "u") == ">=1.0"
    assert b(0.99999, mg.D3_SEP_CUTS_ARCSEC, mg.D3_SEP_LABELS, "u") == "[0.1538,1.0)"
    assert b(3, mg.D3_CONE_EDGES, mg.D3_CONE_LABELS, "u") == "0-3"
    assert b(4, mg.D3_CONE_EDGES, mg.D3_CONE_LABELS, "u") == "4-6"
    assert b(10, mg.D3_CONE_EDGES, mg.D3_CONE_LABELS, "u") == ">=10"


def _mini_inputs(both_passes_ok=True, break_monotone=False):
    roster = pd.DataFrame({
        "source_id": ["9000000000000000001", "9000000000000000002", "9000000000000000003"],
        "class_label": ["dsct_flag1", "dsct_flag0", "dsct_flag1"],
        "KIC": [1, 2, 3], "gmag": [14.0, 15.2, float("nan")], "Teff": [6600.0, 7100.0, float("nan")],
        "logg": [4.0, 4.1, 4.2], "ra": [290.0, 291.0, 292.0], "dec": [40.0, 41.0, 42.0],
        "dom_freq_per_day": [10.0, float("nan"), float("nan")], "amp_mmag": [3.0, float("nan"), float("nan")],
        "subhour": [True, False, False],
    })
    qc = pd.DataFrame({
        "source_id": roster["source_id"], "cache_present": [True, True, False],
        "read_status": ["ok", "ok", "missing"], "nearest_separation_arcsec": [0.05, 0.2, float("nan")],
        "ztf_objects_in_cone": [2, 5, float("nan")], "selected_ztf_objects": [2, 4, 0],
        "crossmatched": [True, False if not break_monotone else True, False],
        "zg_clean_rows": [500, 400, 0], "zr_clean_rows": [450, 380, 0],
    })
    if break_monotone:
        qc.loc[1, "read_status"] = "error"   # qc_passed without the crossmatched stage
    per_star = pd.DataFrame({
        "sid": roster["source_id"], "best_status": ["not_detected", "missing", "missing"],
        "low_available": [True, False, False], "high_available": [both_passes_ok, False, False],
    })
    mo_joined = pd.Series([True, False, False], index=roster["source_id"].to_numpy())
    return roster, qc, per_star, mo_joined


def test_stage_frame_bins_and_stages():
    roster, qc, per_star, joined = _mini_inputs()
    stage = mg._d3_stage_frame(roster, qc, per_star, joined)
    s0 = stage.iloc[0]
    assert s0["magnitude_bin"] == "g_le_14"            # boundary star enters g_le_14 (spec: <=)
    assert s0["amp_bin"] == "[2,5)" and s0["period_bin"] == "[0.05,0.2) d"  # 10 c/d = 8640 s = 0.1 d
    assert s0["teff_bin"] == "[6597,6737)" and s0["cone_count_bin"] == "0-3"
    assert s0["separation_bin"] == "<0.0542" and s0["mo_join_status"] == "mo_joined"
    assert bool(s0["fetched"]) and bool(s0["crossmatched"]) and bool(s0["qc_passed"]) and bool(s0["both_passes"])
    s2 = stage.iloc[2]
    assert s2["magnitude_bin"] == "g_unknown" and s2["amp_bin"] == "amp_unknown"
    assert s2["period_bin"] == "period_unknown" and s2["separation_bin"] == "sep_unknown"
    assert not s2["fetched"] and not s2["both_passes"]
    att = mg.d3_attrition_table(stage)
    assert att.columns.tolist() == mg.D3_ATTRITION_COLUMNS
    assert int(att["n_roster"].sum()) == 3 and int(att["n_both_passes"].sum()) == 1
    assert (att["analysis_status"] == "prespecified_compliance").all() and att["prespecified"].all()


def test_both_passes_requires_both_available():
    roster, qc, per_star, joined = _mini_inputs(both_passes_ok=False)
    stage = mg._d3_stage_frame(roster, qc, per_star, joined)
    assert not bool(stage.iloc[0]["both_passes"])


def test_non_monotone_stages_abort():
    roster, qc, per_star, joined = _mini_inputs(break_monotone=True)
    with pytest.raises(SystemExit, match="not monotone"):
        mg._d3_stage_frame(roster, qc, per_star, joined)


def test_covariate_table_shape_and_population_sd():
    roster, qc, per_star, joined = _mini_inputs()
    # 610-row requirement: replicate the two positives to 610 rows
    reps = 305
    big = pd.concat([roster.iloc[[0, 2]]] * reps, ignore_index=True)
    big["source_id"] = [f"90{i:017d}" for i in range(len(big))]
    qc_big = pd.concat([qc.iloc[[0, 2]]] * reps, ignore_index=True); qc_big["source_id"] = big["source_id"]
    ps_big = pd.concat([per_star.iloc[[0, 2]]] * reps, ignore_index=True); ps_big["sid"] = big["source_id"]
    joined_big = pd.Series([True, False] * reps, index=big["source_id"].to_numpy())
    stage = mg._d3_stage_frame(big, qc_big, ps_big, joined_big)
    cov = mg.d3_mo_join_covariates(stage)
    assert cov.columns.tolist() == mg.D3_COVARIATE_COLUMNS
    assert len(cov) == 2 * len(mg.D3_MO_JOIN_COVARIATES)
    row = cov[(cov.mo_join_status == "mo_joined") & (cov.covariate == "gmag")].iloc[0]
    assert row["n_group"] == 305 and row["n_nonmissing"] == 305 and row["sd"] == 0.0
    unj = cov[(cov.mo_join_status == "mo_unjoined") & (cov.covariate == "gmag")].iloc[0]
    assert unj["n_missing"] == 305 and math.isnan(unj["mean"])
    with pytest.raises(SystemExit, match="!= 610"):
        mg.d3_mo_join_covariates(stage.iloc[:10])
