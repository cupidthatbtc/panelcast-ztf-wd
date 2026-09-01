"""Tests for the post-launch descriptive frequency audits
(reviews/G5prep/sol_round2.md item 9, F32/F33): the fixed histogram edges
and half-open bins (0.98/1.02 edges, 1440 overflow), per-dataset
normalisation and density = share / bin_width, the abort on non-finite
selections, the yearly-alias and Kepler-Nyquist-reflection predicates,
the per-star relations table beside the unchanged frozen taxonomy, the
truth-list identity with the frozen loader on the real tables, and the CLI
(CSV + PNG + meta.json) on a synthetic bundle."""

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
from d3_frequency_audits import (  # noqa: E402
    HIST_COLUMNS,
    HIST_EDGES,
    RELATION_COLUMNS,
    assert_dominant_matches_roster,
    d1_confirmed_frequencies,
    d3_negative_confirmed_frequencies,
    extra_relations,
    histogram_table,
    kepler_nyquist_reflection,
    main,
    truth_lists_by_sid,
    yearly_alias,
)
from conftest import F_NYQ_PER_DAY, sid_for  # noqa: E402

RULED_EDGES = [0, 0.25, 0.50, 0.75, 0.98, 1.02, 1.25, 1.50, 1.75,
               1.98, 2.02, 2.25, 2.50, 2.75, 2.98, 3.02, 3.25, 3.50,
               3.75, 4, 6, 8, 12, 16, 20, 24, 32, 48, 96, 192, 384,
               768, 1440, math.inf]
DELTA_YEAR = 1 / 365.25


def test_edges_exactly_as_ruled():
    assert HIST_EDGES == RULED_EDGES
    assert len(HIST_EDGES) == 34 and HIST_EDGES[-1] == math.inf
    assert common.DELTA_YEAR_PER_DAY == 0.0027378507871321013
    assert common.F_NYQ_PER_DAY == 24.46848


def test_half_open_bins_and_overflow():
    idx = common.bin_index_half_open(
        np.array([0.0, 0.2499, 0.25, 0.9799, 0.98, 1.0, 1.0199, 1.02, 1.25, 24.0, 1439.999, 1440.0, 5000.0]),
        HIST_EDGES)
    assert idx.tolist() == [0, 0, 1, 3, 4, 4, 4, 5, 6, 25, 31, 32, 32]
    assert HIST_EDGES[4] == 0.98 and HIST_EDGES[5] == 1.02
    assert HIST_EDGES[32] == 1440 and math.isinf(HIST_EDGES[33])
    with pytest.raises(SystemExit, match="outside the fixed bin range"):
        common.bin_index_half_open(np.array([-0.1]), HIST_EDGES)
    with pytest.raises(SystemExit, match="outside the fixed bin range"):
        common.bin_index_half_open(np.array([math.nan]), HIST_EDGES)


def test_histogram_table_shares_and_density():
    d1 = np.array([0.1, 0.98, 1.0, 1.0199, 1.02, 2.0, 24.0, 1440.0, 3000.0, 0.5])
    d3 = np.array([1.0, 1.0, 3.0])
    table = histogram_table({"D1": ("sel1", d1), "D3": ("sel3", d3), "EMPTY": ("none", np.array([]))})
    assert list(table.columns) == HIST_COLUMNS
    assert len(table) == 3 * 33
    for dataset, freqs in (("D1", d1), ("D3", d3)):
        sub = table[table["dataset"] == dataset]
        assert (sub["n_confirmed_total"] == len(freqs)).all()
        assert sub["n_bin"].sum() == len(freqs)
        assert math.isclose(sub["share_of_confirmed"].sum(), 1.0)
        finite = sub[np.isfinite(sub["freq_hi_per_day"])]
        width = finite["freq_hi_per_day"] - finite["freq_lo_per_day"]
        assert np.allclose(finite["density_per_day"], finite["share_of_confirmed"] / width, rtol=0, atol=0)
        overflow = sub[~np.isfinite(sub["freq_hi_per_day"])]
        assert len(overflow) == 1 and overflow["density_per_day"].isna().all()
    d1_tab = table[table["dataset"] == "D1"].set_index("bin_index")
    assert d1_tab.loc[4, "n_bin"] == 3            # [0.98, 1.02): 0.98, 1.0, 1.0199
    assert d1_tab.loc[5, "n_bin"] == 1            # [1.02, 1.25): 1.02
    assert d1_tab.loc[32, "n_bin"] == 2           # [1440, inf): 1440 (final finite edge -> overflow), 3000
    assert d1_tab.loc[25, "n_bin"] == 1           # [24, 32)
    assert d1_tab.loc[4, "share_of_confirmed"] == 0.3
    assert math.isclose(d1_tab.loc[4, "density_per_day"], 0.3 / 0.04)
    empty = table[table["dataset"] == "EMPTY"]
    assert (empty["n_bin"] == 0).all() and empty["share_of_confirmed"].isna().all()
    assert (empty["n_confirmed_total"] == 0).all()
    assert (table["analysis_status"] == "postlaunch_descriptive").all()
    assert (table["interval"] == "none").all()


def test_selections_and_aborts(d3_world, per_star_roundtrip):
    freqs = d1_confirmed_frequencies(d3_world.d1_catalog)
    assert len(freqs) == int((d3_world.d1_catalog["blind_status"] == "confirmed").sum())
    assert np.all(freqs > 0)
    bad = d3_world.d1_catalog.copy()
    bad.loc[bad.index[bad["blind_status"] == "confirmed"][0], "best_frequency_per_day"] = math.nan
    with pytest.raises(SystemExit, match="finite positive best frequency"):
        d1_confirmed_frequencies(bad)
    with pytest.raises(SystemExit, match="not the published 928"):
        d1_confirmed_frequencies(d3_world.d1_catalog.iloc[:-1])
    for per_star in (d3_world.per_star, per_star_roundtrip):
        neg = d3_negative_confirmed_frequencies(per_star)
        expect = per_star[(per_star["class_label"] == "dsct_flag0") & (per_star["best_status"] == "confirmed")]
        assert len(neg) == len(expect) > 0
    zero = d3_world.per_star.copy()
    idx = zero.index[(zero["class_label"] == "dsct_flag0") & (zero["best_status"] == "confirmed")][0]
    zero.loc[idx, "best_frequency_per_day"] = 0.0
    with pytest.raises(SystemExit, match="finite positive best frequency"):
        d3_negative_confirmed_frequencies(zero)
    one_negative_short = d3_world.per_star.drop(index=idx)
    with pytest.raises(SystemExit, match="frozen P3 denominator"):
        d3_negative_confirmed_frequencies(one_negative_short)


def test_relation_predicates():
    tol = 1e-6
    assert yearly_alias(1.0 + DELTA_YEAR, 1.0, tol)
    assert yearly_alias(1.0 - DELTA_YEAR, 1.0, tol)
    assert not yearly_alias(1.0, 1.0, tol)                       # direct is not a yearly alias
    assert yearly_alias(abs(0.001 - DELTA_YEAR), 0.001, tol)     # the |.| of a negative difference
    assert yearly_alias(1.0 + DELTA_YEAR + 0.9 * tol, 1.0, tol)
    assert not yearly_alias(1.0 + DELTA_YEAR + 1.1 * tol, 1.0, tol)
    f_ref = 2 * F_NYQ_PER_DAY - 10.0
    assert kepler_nyquist_reflection(f_ref, 10.0, tol)
    assert kepler_nyquist_reflection(f_ref + 0.9 * tol, 10.0, tol)
    assert not kepler_nyquist_reflection(f_ref + 1.1 * tol, 10.0, tol)
    assert not kepler_nyquist_reflection(10.0, 10.0, tol)
    # negative reflected frequency: never eligible, even if |f_ref| matches
    assert 2 * F_NYQ_PER_DAY - 60.0 < 0
    assert not kepler_nyquist_reflection(abs(2 * F_NYQ_PER_DAY - 60.0), 60.0, tol)


def test_extra_relations_table(d3_world, per_star_roundtrip):
    lists = common.table2_per_day_lists(d3_world.table2)
    for per_star in (d3_world.per_star, per_star_roundtrip):
        truth = truth_lists_by_sid(per_star, d3_world.roster, lists)
        assert truth == {sid: d3_world.truth[sid] for sid in per_star["sid"]}
        table = extra_relations(per_star, truth)
        assert list(table.columns) == RELATION_COLUMNS
        assert len(table) == len(per_star) and table["sid"].tolist() == per_star["sid"].tolist()
        by_sid = table.set_index("sid")
        # frozen columns copied unchanged
        ps = per_star.set_index("sid")
        assert (by_sid["frozen_best_candidate_matches_dominant"]
                == ps["best_candidate_matches_dominant"].astype(str)).all()
        assert (by_sid["frozen_best_candidate_matches_any_mode"]
                == ps["best_candidate_matches_any_mode"].astype(str)).all()
        # blank exactly where the frozen column is unscored
        dom_unscored = by_sid["frozen_best_candidate_matches_dominant"] == "unscored"
        assert by_sid.loc[dom_unscored, "matches_yearly_alias_dominant"].isna().all()
        assert by_sid.loc[dom_unscored, "matches_kepler_nyquist_reflection_dominant"].isna().all()
        assert by_sid.loc[~dom_unscored, "matches_kepler_nyquist_reflection_dominant"].notna().all()
        any_unscored = by_sid["frozen_best_candidate_matches_any_mode"] == "unscored"
        assert by_sid.loc[any_unscored, "matches_yearly_alias_any_mode"].isna().all()
        assert by_sid.loc[~any_unscored, "matches_yearly_alias_any_mode"].notna().all()
        # the reflection star (k == 9) is flagged; a direct star is not
        r9 = by_sid.loc[sid_for(90, 9)]
        assert bool(r9["matches_kepler_nyquist_reflection_dominant"])
        assert bool(r9["matches_kepler_nyquist_reflection_any_mode"])
        assert not bool(r9["matches_yearly_alias_dominant"])
        assert r9["frozen_best_candidate_matches_dominant"] == "unmatched"     # taxonomy untouched
        r11 = by_sid.loc[sid_for(90, 11)]
        assert not bool(r11["matches_kepler_nyquist_reflection_dominant"])
        assert not bool(r11["matches_yearly_alias_dominant"])
        assert r11["frozen_best_candidate_matches_dominant"] == "direct"
        # negatives: no truth, no dominant -> all blank, but rows present
        neg = by_sid.loc[sid_for(90, 100_025)]
        assert neg["best_status"] == "confirmed" and pd.isna(neg["matches_yearly_alias_any_mode"])


def test_extra_relations_yearly_alias_positive_case_and_guards(d3_world):
    per_star = d3_world.per_star.copy()
    truth = {sid: d3_world.truth[sid] for sid in per_star["sid"]}
    sid = sid_for(90, 11)
    i = per_star.index[per_star["sid"] == sid][0]
    dom = per_star.loc[i, "primary_freq"]
    per_star.loc[i, "best_frequency_per_day"] = dom + DELTA_YEAR
    per_star.loc[i, "best_candidate_matches_dominant"] = "unmatched"
    per_star.loc[i, "best_candidate_matches_any_mode"] = "unmatched"
    row = extra_relations(per_star, truth).set_index("sid").loc[sid]
    assert bool(row["matches_yearly_alias_dominant"]) and bool(row["matches_yearly_alias_any_mode"])
    # inconsistency between the frozen columns and the inputs aborts
    broken = d3_world.per_star.copy()
    broken.loc[i, "best_candidate_matches_dominant"] = "unscored"
    with pytest.raises(SystemExit, match="frozen dominant match is unscored"):
        extra_relations(broken, truth)
    broken2 = d3_world.per_star.copy()
    broken2.loc[i, "baseline_days"] = math.nan
    with pytest.raises(SystemExit, match="tolerance missing"):
        extra_relations(broken2, truth)
    broken3 = d3_world.per_star.copy()
    broken3.loc[i, "best_candidate_matches_dominant"] = "nearly"
    with pytest.raises(SystemExit, match="outside the taxonomy"):
        extra_relations(broken3, truth)
    with pytest.raises(SystemExit, match="no truth list"):
        extra_relations(d3_world.per_star, {k: v for k, v in truth.items() if k != sid})


def test_assert_dominant_matches_roster(d3_world):
    assert_dominant_matches_roster(d3_world.per_star, d3_world.roster)
    broken = d3_world.per_star.copy()
    i = broken.index[broken["sid"] == sid_for(90, 11)][0]
    broken.loc[i, "primary_freq"] = broken.loc[i, "primary_freq"] * 1.001
    with pytest.raises(SystemExit, match="!= roster dom_freq_per_day"):
        assert_dominant_matches_roster(broken, d3_world.roster)


@pytest.mark.skipif(not (common.DEFAULT_ROSTER.exists() and common.DEFAULT_MO_TABLE2.exists()),
                    reason="real roster / Mo table 2 not present")
def test_real_truth_lists_identical_to_frozen_loader():
    from metrics_generalization import truth_d3
    frozen = truth_d3()
    roster = common.load_roster(common.DEFAULT_ROSTER)
    lists = common.table2_per_day_lists(common.load_mo_table2(common.DEFAULT_MO_TABLE2))
    rebuilt = truth_lists_by_sid(frozen[["sid"]], roster, lists)
    for sid, truth in zip(frozen["sid"], frozen["truth_freqs"]):
        assert rebuilt[sid] == list(truth)
    n_joined = sum(1 for t in frozen["truth_freqs"] if t)
    assert n_joined == 456 + 3            # 456 positives + 3 flag-2 KICs present in Mo table 2
    assert int((frozen["freq_scorable"]).sum()) == 456


def test_cli_end_to_end(d3_bundle):
    out = d3_bundle["out"]
    main(["--metrics-dir", str(d3_bundle["metrics"]), "--d1-catalog", str(d3_bundle["d1_catalog"]),
          "--roster", str(d3_bundle["roster"]), "--mo-table2", str(d3_bundle["table2"]),
          "--out-dir", str(out)])
    hist = pd.read_csv(out / "d1_d3_confirmed_frequency_histogram.csv")
    assert list(hist.columns) == HIST_COLUMNS and len(hist) == 66
    assert set(hist["dataset"]) == {"D1", "D3"}
    assert hist.loc[hist["dataset"] == "D1", "n_confirmed_total"].iloc[0] == int(
        (d3_bundle["world"].d1_catalog["blind_status"] == "confirmed").sum())
    png = out / "d1_d3_confirmed_frequency_histogram.png"
    assert png.exists() and png.stat().st_size > 1000 and png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    meta = json.loads((out / "d1_d3_confirmed_frequency_histogram.meta.json").read_text())
    assert meta["analysis_status"] == "postlaunch_descriptive" and meta["prespecified"] is False
    assert meta["interval"] == "none" and meta["source_csv"] == "d1_d3_confirmed_frequency_histogram.csv"
    assert meta["edges_per_day"][-1] == "inf" and meta["edges_per_day"][-2] == 1440
    rel = pd.read_csv(out / "d3_extra_frequency_relations.csv", dtype={"sid": str})
    assert list(rel.columns) == RELATION_COLUMNS and len(rel) == 3000
    manifest = json.loads((out / "d3_frequency_audits.manifest.json").read_text())
    assert set(manifest["outputs_sha256"]) == {
        "d1_d3_confirmed_frequency_histogram.csv", "d1_d3_confirmed_frequency_histogram.png",
        "d1_d3_confirmed_frequency_histogram.meta.json", "d3_extra_frequency_relations.csv"}
    assert "never reclassify a frozen match" in (out / "d3_frequency_audits.README.md").read_text()
    # the frozen per_star.csv is untouched
    assert "matches_yearly_alias_dominant" not in pd.read_csv(d3_bundle["metrics"] / "per_star.csv", nrows=1).columns


def test_cli_refuses_pilot_bundle(d3_world, tmp_path):
    from conftest import write_bundle
    paths = write_bundle(d3_world, tmp_path, pilot=True)
    with pytest.raises(SystemExit, match="pilot"):
        main(["--metrics-dir", str(paths["metrics"]), "--d1-catalog", str(paths["d1_catalog"]),
              "--roster", str(paths["roster"]), "--mo-table2", str(paths["table2"]),
              "--out-dir", str(paths["out"])])
