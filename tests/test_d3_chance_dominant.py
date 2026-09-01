"""Tests for the post-launch descriptive dominant-only confirmed-conditioned
chance-match calibration (reviews/G5prep/sol_round2.md item 8, F21): the
frame, the frozen-classifier hit matrix (`ambiguous` is not a hit; the
tolerance edge), fixed-point-free derangements from PCG64(20260829) with
exact determinism, the constant per-derangement denominator, the ruled
column set, and the CLI on a synthetic bundle."""

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
from d3_chance_dominant import (  # noqa: E402
    COLUMNS,
    DERANGEMENTS,
    SEED,
    confirmed_frame,
    derangement_rates,
    direct_hit_matrix,
    main,
    summary_table,
)
from metrics_generalization import classify_match  # noqa: E402


def test_ruled_constants():
    assert DERANGEMENTS == 10000 and SEED == 20260829


def test_confirmed_frame_is_p2_confirmed_finite(d3_world, per_star_roundtrip):
    for per_star in (d3_world.per_star, per_star_roundtrip):
        frame = confirmed_frame(per_star)
        p2 = common.p2_frame(per_star)
        expected = p2[p2["best_status"] == "confirmed"]
        assert list(frame.columns) == ["sid", "f", "tol", "dominant"]
        assert set(frame["sid"]) == set(expected["sid"])
        assert np.isfinite(frame[["f", "tol", "dominant"]].to_numpy()).all()
        assert np.allclose(frame["tol"], 1.5 / d3_world.baseline, rtol=0, atol=0)
        assert frame.attrs["n_confirmed_nonfinite_excluded"] == 0
        # excluded by construction: unusable (high pass unavailable) stars, unjoined stars
        pos = per_star[per_star["class_label"] == "dsct_flag1"]
        unusable = pos[~pos["high_available"].map(common.truthy) & (pos["best_status"] == "confirmed")]
        assert len(unusable) > 0 and not set(unusable["sid"]) & set(frame["sid"])


def test_confirmed_frame_filters_nonfinite_and_aborts_on_missing_tolerance(d3_world):
    per_star = d3_world.per_star.copy()
    frame0 = confirmed_frame(per_star)
    sid = frame0["sid"].iloc[0]
    per_star.loc[per_star["sid"] == sid, "best_frequency_per_day"] = math.inf
    frame = confirmed_frame(per_star)
    assert len(frame) == len(frame0) - 1 and frame.attrs["n_confirmed_nonfinite_excluded"] == 1
    per_star2 = d3_world.per_star.copy()
    per_star2.loc[per_star2["sid"] == sid, "baseline_days"] = math.nan
    with pytest.raises(SystemExit, match="finite tolerance"):
        confirmed_frame(per_star2)


def test_direct_hit_matrix_uses_frozen_classifier():
    f = np.array([1.0, 2.0, 3.0])
    tol = np.array([0.001, 0.001, 0.001])
    dominant = np.array([1.0, 2.0005, 3.002])
    matrix = direct_hit_matrix(f, tol, dominant)
    assert matrix.tolist() == [[True, False, False], [False, True, False], [False, False, False]]
    # the tolerance edge is the frozen `<=`
    assert direct_hit_matrix(np.array([1.0]), np.array([0.001]), np.array([1.001]))[0, 0] == (
        classify_match(1.0, [1.001], 0.001) == "direct")
    # a harmonic-only relation is not a hit
    assert not direct_hit_matrix(np.array([2.0]), np.array([0.001]), np.array([1.0]))[0, 0]
    # `ambiguous` (direct AND window alias inside a huge tolerance) is not a hit
    assert classify_match(1.0, [1.0], 0.6) == "ambiguous"
    assert not direct_hit_matrix(np.array([1.0]), np.array([0.6]), np.array([1.0]))[0, 0]
    with pytest.raises(SystemExit, match="mismatched"):
        direct_hit_matrix(f, tol[:2], dominant)


def test_derangements_fixed_point_free_deterministic_and_denominator():
    n = 12
    rng = np.random.default_rng(1)
    matrix = rng.random((n, n)) < 0.3
    rates1, rejected1 = derangement_rates(matrix, n_derangements=500, seed=SEED)
    rates2, rejected2 = derangement_rates(matrix, n_derangements=500, seed=SEED)
    assert np.array_equal(rates1, rates2) and rejected1 == rejected2       # exact determinism
    rates3, _ = derangement_rates(matrix, n_derangements=500, seed=SEED + 1)
    assert not np.array_equal(rates1, rates3)
    assert len(rates1) == 500 and rejected1 > 0                             # rejection sampling happened
    # every rate is hits / n with the denominator fixed at n for every derangement
    assert np.all((rates1 * n) - np.round(rates1 * n) == 0)
    # identity matrix: any fixed point would contribute 1/n; derangements give exactly 0
    zero, _ = derangement_rates(np.eye(n, dtype=bool), n_derangements=2000, seed=SEED)
    assert np.all(zero == 0.0)
    ones, _ = derangement_rates(np.ones((n, n), dtype=bool), n_derangements=50, seed=SEED)
    assert np.all(ones == 1.0)
    # n = 2 has exactly one derangement (the swap)
    two = np.array([[True, True], [False, True]])
    r2, _ = derangement_rates(two, n_derangements=20, seed=SEED)
    assert np.all(r2 == 0.5)


def test_fewer_than_two_members_aborts():
    with pytest.raises(SystemExit, match="no derangement exists"):
        derangement_rates(np.ones((1, 1), dtype=bool), n_derangements=10, seed=SEED)


def test_summary_table_columns_and_quantiles():
    rates = np.linspace(0.0, 0.2, DERANGEMENTS)
    table = summary_table(rates, n_confirmed=123)
    assert list(table.columns) == COLUMNS and len(table) == 1
    row = table.iloc[0]
    assert row["derangements"] == DERANGEMENTS and row["seed"] == SEED and row["n_confirmed"] == 123
    assert row["accidental_direct_rate_mean"] == float(np.mean(rates))
    assert row["accidental_direct_rate_median"] == float(np.median(rates))
    assert row["accidental_direct_rate_q95"] == float(np.quantile(rates, 0.95))
    assert row["analysis_status"] == "postlaunch_descriptive"
    assert row["prespecified"] is False or row["prespecified"] == False  # noqa: E712
    assert row["interval"] == "none"
    with pytest.raises(SystemExit, match="derangement count"):
        summary_table(rates[:-1], n_confirmed=123)


def test_full_synthetic_run_ten_thousand(d3_world):
    frame = confirmed_frame(d3_world.per_star)
    matrix = direct_hit_matrix(frame["f"].to_numpy(), frame["tol"].to_numpy(), frame["dominant"].to_numpy())
    rates, rejected = derangement_rates(matrix)
    assert len(rates) == DERANGEMENTS and rejected > 0
    assert np.all((rates >= 0) & (rates <= 1))
    table = summary_table(rates, len(frame))
    assert table["n_confirmed"].iloc[0] == len(frame)
    assert 0 <= table["accidental_direct_rate_mean"].iloc[0] <= 1
    assert 0 <= table["accidental_direct_rate_median"].iloc[0] <= table["accidental_direct_rate_q95"].iloc[0] <= 1
    assert table["accidental_direct_rate_mean"].iloc[0] == float(np.mean(rates))
    # the unpermuted diagonal is the observed direct rate, not part of the CSV
    assert np.trace(matrix) > 0


def test_cli_end_to_end_and_timing_guard(d3_bundle):
    out = d3_bundle["out"]
    main(["--metrics-dir", str(d3_bundle["metrics"]), "--out-dir", str(out)])
    table = pd.read_csv(out / "d3_dominant_confirmed_chance_match.csv")
    assert list(table.columns) == COLUMNS and len(table) == 1
    assert table["derangements"].iloc[0] == 10000 and table["seed"].iloc[0] == 20260829
    manifest = json.loads((out / "d3_chance_dominant.manifest.json").read_text())
    assert manifest["n_confirmed"] == table["n_confirmed"].iloc[0]
    assert manifest["inputs_sha256"].keys() == {"per_star.csv", "metrics_manifest.json", "chance_match.json"}
    assert "10,000 star-level derangements" in (out / "d3_chance_dominant.README.md").read_text()
    # rerun is byte-identical (seeded)
    first = (out / "d3_dominant_confirmed_chance_match.csv").read_bytes()
    main(["--metrics-dir", str(d3_bundle["metrics"]), "--out-dir", str(out)])
    assert (out / "d3_dominant_confirmed_chance_match.csv").read_bytes() == first
    # timing: refuses to run before the frozen chance file exists
    (d3_bundle["metrics"] / "chance_match.json").unlink()
    with pytest.raises(SystemExit, match="chance_match.json"):
        main(["--metrics-dir", str(d3_bundle["metrics"]), "--out-dir", str(out)])


def test_cli_refuses_pilot_bundle(d3_world, tmp_path):
    from conftest import write_bundle
    paths = write_bundle(d3_world, tmp_path, pilot=True)
    with pytest.raises(SystemExit, match="pilot"):
        main(["--metrics-dir", str(paths["metrics"]), "--out-dir", str(paths["out"])])
