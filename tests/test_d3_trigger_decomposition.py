"""Tests for the post-launch descriptive D3 trigger decomposition
(reviews/G5prep/sol_diurnal.md, ADMIT-AS-DESCRIPTIVE). The band rule and the
partition identities are exercised on synthetic frames; the CLI's frozen-run
guards are covered by the fail-closed checks in the module itself."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "scripts" / "generalization"))

from d3_trigger_decomposition import (  # noqa: E402
    EXPECTED_NEGATIVES,
    decompose,
    verify_against_trigger_rates,
    within_band,
)


def make_frame(confirmed_freqs, n_negatives=EXPECTED_NEGATIVES,
               n_missing=5, extra_rows=()):
    """n_negatives dsct_flag0 rows: the given confirmed frequencies, some
    missing (NaN frequency), the rest not_detected; plus extra rows."""
    rows = []
    for i, f in enumerate(confirmed_freqs):
        rows.append({"sid": f"90{i:017d}", "class_label": "dsct_flag0",
                     "best_status": "confirmed", "best_frequency_per_day": f})
    for i in range(n_missing):
        rows.append({"sid": f"91{i:017d}", "class_label": "dsct_flag0",
                     "best_status": "missing", "best_frequency_per_day": float("nan")})
    n_rest = n_negatives - len(rows)
    assert n_rest >= 0
    for i in range(n_rest):
        rows.append({"sid": f"92{i:017d}", "class_label": "dsct_flag0",
                     "best_status": "not_detected", "best_frequency_per_day": 5.4321})
    rows.extend(extra_rows)
    return pd.DataFrame(rows)


def test_band_rule_closed_endpoints_and_harmonics():
    assert within_band(1.000)
    assert within_band(0.980) and within_band(1.020)      # closed endpoints
    assert within_band(1.980) and within_band(2.020)
    assert within_band(2.980) and within_band(3.020)
    assert within_band(2.015)                              # the pilot's pile-up
    assert not within_band(0.9799) and not within_band(1.0201)
    assert not within_band(3.0201)
    assert not within_band(0.5)                            # f<4 but no band
    assert not within_band(4.0) and not within_band(8.0)   # outside f<4


def test_partition_counts_and_identities():
    frame = make_frame([1.000, 1.020, 2.015, 2.980, 1.0201, 3.5, 8.0])
    table = decompose(frame)
    within = table[table["component"] == "within_solar_diurnal_band"].iloc[0]
    outside = table[table["component"] == "outside_solar_diurnal_band"].iloc[0]
    assert int(within["n_component"]) == 4
    assert int(outside["n_component"]) == 3
    assert int(within["n_confirmed_total"]) == 7
    assert int(within["n_negative"]) == EXPECTED_NEGATIVES
    # arithmetic identities from the verdict
    assert int(within["n_component"]) + int(outside["n_component"]) \
        == int(within["n_confirmed_total"])
    assert math.isclose(
        within["rate_of_all_negatives"] + outside["rate_of_all_negatives"],
        7 / EXPECTED_NEGATIVES, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(
        within["share_of_confirmed"] + outside["share_of_confirmed"], 1.0)
    assert (table["analysis_status"] == "postlaunch_pilot_informed_descriptive").all()
    assert (~table["prespecified"]).all()
    assert (table["interval"] == "none").all()


def test_missing_stars_count_only_in_denominator():
    table = decompose(make_frame([1.001], n_missing=200))
    assert int(table["n_confirmed_total"].iloc[0]) == 1
    assert int(table["n_negative"].iloc[0]) == EXPECTED_NEGATIVES


def test_candidate_and_other_classes_ignored():
    extras = [
        {"sid": "8000000000000000001", "class_label": "dsct_flag1",
         "best_status": "confirmed", "best_frequency_per_day": 1.001},
        {"sid": "8000000000000000002", "class_label": "dsct_flag2",
         "best_status": "confirmed", "best_frequency_per_day": 2.001},
    ]
    frame = make_frame([1.5], extra_rows=extras)
    # a candidate (rule-2-only) negative never enters the rule-1 numerator
    idx = frame.index[frame["best_status"] == "not_detected"][0]
    frame.loc[idx, "best_status"] = "candidate"
    frame.loc[idx, "best_frequency_per_day"] = 1.002
    table = decompose(frame)
    assert int(table["n_confirmed_total"].iloc[0]) == 1


def test_confirmed_without_finite_frequency_aborts():
    frame = make_frame([1.001, float("nan")])
    with pytest.raises(SystemExit, match="finite best-pass frequency"):
        decompose(frame)
    frame_inf = make_frame([1.001, float("inf")])
    with pytest.raises(SystemExit, match="finite best-pass frequency"):
        decompose(frame_inf)


def test_wrong_denominator_aborts():
    frame = make_frame([1.001], n_negatives=150)
    with pytest.raises(SystemExit, match="refusing to partition"):
        decompose(frame, expected_negatives=EXPECTED_NEGATIVES)


def test_zero_confirmed_gives_nan_shares_zero_rates():
    table = decompose(make_frame([]))
    assert (table["n_component"] == 0).all()
    assert (table["rate_of_all_negatives"] == 0.0).all()
    assert table["share_of_confirmed"].isna().all()


def test_verify_against_trigger_rates_exact_and_mismatch():
    table = decompose(make_frame([1.0, 2.0, 3.6]))
    good = pd.DataFrame([{"quantity": "negative_class_trigger_rate",
                          "rule": "confirmed", "n": EXPECTED_NEGATIVES,
                          "p": 3 / EXPECTED_NEGATIVES}])
    verify_against_trigger_rates(table, good)
    bad = good.assign(p=4 / EXPECTED_NEGATIVES)
    with pytest.raises(SystemExit, match="does not reproduce"):
        verify_against_trigger_rates(table, bad)
    with pytest.raises(SystemExit, match="no unique rule-1 P3 row"):
        verify_against_trigger_rates(table, good.assign(rule="census"))
