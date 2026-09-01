"""Tests for the post-launch descriptive D2 diagnostics
(reviews/G5prep/sol_round2.md item 5, F08/F11/F38, ADMIT-DESCRIPTIVE).
The three pure constructors are exercised on synthetic manifest + per_star
frames; the CLI's fail-closed guards and the real-archive path are covered by
a smoke test on the archived gen2 pilot (development mode, --allow-pilot)."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(REPO / "scripts" / "generalization"))

from d2_descriptives import (  # noqa: E402
    ANALYSIS_STATUS,
    DISCLOSURE,
    ENDPOINTS,
    K_TABLE_COLUMNS,
    PAIR_COLUMNS,
    PILOT_DEV_STATUS,
    REUSE_SOURCE_COLUMNS,
    TEMPLATE_STATUSES,
    VERDICT_FILE,
    WG_STRATUM_LABELS,
    arm_a_b_pairs,
    attach_outcomes,
    control_reuse_source,
    k_template_status_table,
    pair_class,
)

SCRIPT = REPO / "scripts" / "generalization" / "descriptive" / "d2_descriptives.py"
PILOT = REPO / "generalization" / "results" / "2026-08-30_d2_pilot_gen2"

# (tic, K, template_source_id, template_status, W_g)
WINDOWS = [
    (1, 0, "src10", "not_detected", 5),
    (1, 1, "src11", "confirmed", 50),
    (1, 2, "src12", "candidate", 400),
    (2, 0, "src20", "not_detected", 8),
    (2, 1, "src21", "not_detected", 60),
    (2, 2, "src22", "confirmed", 450),
]


def sid(arm: str, tic: int, k: int) -> str:
    return f"{arm}{tic}K{k}"


def make_manifest(windows=WINDOWS, extra_rows=()) -> pd.DataFrame:
    rows = []
    for tic, k, src, status, wg in windows:
        for arm in ("A", "B"):
            rows.append({
                "campaign_id": sid(arm, tic, k), "arm": arm, "scenario": "nominal",
                "tic": tic, "template_source_id": src, "template_status": status,
                "template_k": k, "template_wg_contrasts": wg,
                "control_campaign_id": f"C{src}" if arm == "B" else "",
                "shard_sha256": f"sha_{arm}{tic}{k}",
            })
    # rows the descriptives must ignore: a control and a sensitivity replicate
    rows.append({"campaign_id": "Csrc10", "arm": "ctrl", "scenario": "control", "tic": 0,
                 "template_source_id": "src10", "template_status": "not_detected",
                 "template_k": -1, "template_wg_contrasts": 5, "control_campaign_id": "",
                 "shard_sha256": "sha_c"})
    rows.append({"campaign_id": "B1K1ladder", "arm": "B", "scenario": "ladder_g1r1", "tic": 1,
                 "template_source_id": "src11", "template_status": "confirmed",
                 "template_k": 1, "template_wg_contrasts": 50, "control_campaign_id": "",
                 "shard_sha256": "sha_l"})
    rows.extend(extra_rows)
    return pd.DataFrame(rows)


# sid -> (best_status, best_candidate_matches_dominant, low_available, high_available)
OUTCOMES = {
    sid("B", 1, 0): ("confirmed", "direct", True, True),
    # B 2 K0 deliberately absent: scheduled but never scored -> failure
    sid("B", 1, 1): ("confirmed", "unmatched", True, False),   # success, not usable
    sid("B", 2, 1): ("not_detected", "unmatched", True, True),
    sid("B", 1, 2): ("candidate", "direct", True, True),       # rule 1 does not fire
    sid("B", 2, 2): ("confirmed", "direct", True, True),
    sid("A", 1, 0): ("not_detected", "unmatched", True, True),
    sid("A", 2, 0): ("confirmed", "direct", True, True),
    sid("A", 1, 1): ("confirmed", "direct", True, True),
    sid("A", 2, 1): ("confirmed", "unmatched", True, True),
    # A 1 K2 deliberately absent
    sid("A", 2, 2): ("confirmed", "direct", True, True),
}


def make_per_star(manifest: pd.DataFrame, outcomes=OUTCOMES, mutate=None) -> pd.DataFrame:
    rows = []
    by_id = manifest.set_index("campaign_id")
    for s, (status, match, low, high) in outcomes.items():
        m = by_id.loc[s]
        rows.append({
            "sid": s, "arm": m["arm"], "scenario": m["scenario"], "cluster": str(int(m["tic"])),
            "template_k": int(m["template_k"]), "template_status": m["template_status"],
            "wg_contrasts": int(m["template_wg_contrasts"]), "shard_sha256": m["shard_sha256"],
            "best_status": status, "best_candidate_matches_dominant": match,
            "low_available": low, "high_available": high,
        })
    frame = pd.DataFrame(rows)
    if mutate:
        mutate(frame)
    return frame


def outcomes_frame(**kwargs) -> pd.DataFrame:
    manifest = make_manifest()
    return attach_outcomes(manifest, make_per_star(manifest, **kwargs))


def cell(table: pd.DataFrame, k: int, status: str, endpoint: str) -> pd.Series:
    sel = table[(table["template_k"] == k) & (table["template_status"] == status)
                & (table["endpoint"] == endpoint)]
    assert len(sel) == 1
    return sel.iloc[0]


def test_disclosure_is_verbatim_from_the_ruling():
    text = (REPO / VERDICT_FILE).read_text(encoding="utf-8")
    assert ("> " + DISCLOSURE) in text.splitlines()
    assert ANALYSIS_STATUS == "postlaunch_descriptive"
    assert PILOT_DEV_STATUS != ANALYSIS_STATUS


def test_k_table_grid_is_complete_ordered_and_stamped():
    table = k_template_status_table(outcomes_frame())
    assert list(table.columns) == K_TABLE_COLUMNS
    assert len(table) == 3 * 3 * 2
    expected_order = [(k, s, e) for k in (0, 1, 2) for s in TEMPLATE_STATUSES for e in ENDPOINTS]
    assert list(zip(table["template_k"], table["template_status"], table["endpoint"])) == expected_order
    assert TEMPLATE_STATUSES == ("not_detected", "candidate", "confirmed")
    assert (table["wg_stratum"] == table["template_k"].map(WG_STRATUM_LABELS)).all()
    assert (table["analysis_status"] == ANALYSIS_STATUS).all()
    assert (~table["prespecified"].astype(bool)).all()
    assert (table["interval"] == "none").all()
    # zero cells are emitted with blank rate and blank W_g summaries
    empty = cell(table, 0, "candidate", "recovery")
    assert int(empty["n_scheduled"]) == 0 and int(empty["k_success"]) == 0
    assert math.isnan(empty["rate_scheduled"]) and math.isnan(empty["wg_median"])
    assert pd.isna(empty["wg_min"]) and pd.isna(empty["wg_max"])
    # the scheduled cells partition the six nominal arm-B rows, per endpoint
    for endpoint in ENDPOINTS:
        assert int(table[table["endpoint"] == endpoint]["n_scheduled"].sum()) == 6


def test_k_table_missing_row_is_failure_and_usable_is_context_only():
    table = k_template_status_table(outcomes_frame())
    nd0_t = cell(table, 0, "not_detected", "trigger")
    nd0_r = cell(table, 0, "not_detected", "recovery")
    # B 1 K0 confirmed+direct; B 2 K0 never scored -> counted, failed, unusable
    assert int(nd0_t["n_scheduled"]) == 2 and int(nd0_t["n_usable"]) == 1
    assert int(nd0_t["k_success"]) == 1 and int(nd0_r["k_success"]) == 1
    assert nd0_t["rate_scheduled"] == 0.5
    assert int(nd0_t["wg_min"]) == 5 and nd0_t["wg_median"] == 6.5 and int(nd0_t["wg_max"]) == 8
    # a confirmed row with one pass unavailable is a trigger success but NOT usable
    c1_t = cell(table, 1, "confirmed", "trigger")
    c1_r = cell(table, 1, "confirmed", "recovery")
    assert int(c1_t["n_scheduled"]) == 1 and int(c1_t["n_usable"]) == 0
    assert int(c1_t["k_success"]) == 1 and int(c1_r["k_success"]) == 0   # unmatched -> no recovery
    # candidate never fires rule 1
    assert int(cell(table, 2, "candidate", "trigger")["k_success"]) == 0
    # recovery requires confirmed AND direct
    assert int(cell(table, 2, "confirmed", "recovery")["k_success"]) == 1
    assert "rate_usable" not in table.columns


def test_k_table_vocabulary_and_duplicate_guards():
    frame = outcomes_frame()
    first_b = frame.index[frame["arm"] == "B"][0]
    first_a = frame.index[frame["arm"] == "A"][0]
    bad_k = frame.copy()
    bad_k.loc[first_b, "template_k"] = 3
    with pytest.raises(SystemExit, match="template_k outside"):
        k_template_status_table(bad_k)
    bad_status = frame.copy()
    bad_status.loc[first_b, "template_status"] = "detected"
    with pytest.raises(SystemExit, match="published vocabulary"):
        k_template_status_table(bad_status)
    # the table is arm B only: an arm-A defect never enters it
    a_only = frame.copy()
    a_only.loc[first_a, "template_status"] = "detected"
    assert len(k_template_status_table(a_only)) == 18
    dup = pd.concat([frame, frame[frame["arm"] == "B"].head(1)], ignore_index=True)
    with pytest.raises(SystemExit, match="more than one nominal arm-B row"):
        k_template_status_table(dup)


def test_attach_outcomes_binds_per_star_to_the_manifest():
    manifest = make_manifest()

    def wrong_status(frame):
        frame.loc[0, "template_status"] = "confirmed" if frame.loc[0, "template_status"] != "confirmed" else "candidate"
    with pytest.raises(SystemExit, match="disagrees with the manifest"):
        attach_outcomes(manifest, make_per_star(manifest, mutate=wrong_status))

    def wrong_sha(frame):
        frame.loc[0, "shard_sha256"] = "tampered"
    with pytest.raises(SystemExit, match="shard_sha256"):
        attach_outcomes(manifest, make_per_star(manifest, mutate=wrong_sha))

    def foreign(frame):
        frame.loc[0, "sid"] = "B9K9"
    with pytest.raises(SystemExit, match="absent from the manifest"):
        attach_outcomes(manifest, make_per_star(manifest, mutate=foreign))

    def duplicate(frame):
        frame.loc[len(frame)] = frame.loc[0]
    with pytest.raises(SystemExit, match="duplicate sids"):
        attach_outcomes(manifest, make_per_star(manifest, mutate=duplicate))
    # non-nominal / control manifest rows never enter the scheduled frame
    outcomes = attach_outcomes(manifest, make_per_star(manifest))
    assert set(outcomes["arm"]) == {"A", "B"} and len(outcomes) == 12
    assert not outcomes["campaign_id"].str.endswith("ladder").any()


def test_pair_class_values():
    assert pair_class(True, True) == "both"
    assert pair_class(True, False) == "A_only"
    assert pair_class(False, True) == "B_only"
    assert pair_class(False, False) == "neither"


def test_pairs_classes_metadata_and_blank_when_not_usable():
    table = arm_a_b_pairs(outcomes_frame())
    assert list(table.columns) == PAIR_COLUMNS
    assert len(table) == 6
    assert list(zip(table["tic"], table["template_k"])) == [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    by = table.set_index(["tic", "template_k"])
    r = by.loc[(1, 0)]
    assert r["a_sid"] == "A1K0" and r["b_sid"] == "B1K0"
    assert r["template_source_id"] == "src10" and r["template_status"] == "not_detected" and r["wg_contrasts"] == 5
    assert bool(r["pair_usable"]) and r["trigger_pair_class"] == "B_only" and r["recovery_pair_class"] == "B_only"
    r = by.loc[(2, 0)]           # B never scored
    assert r["b_status"] == "missing" and not r["b_usable"] and not r["pair_usable"]
    assert bool(r["D_A"]) and not r["D_B"]
    assert r["trigger_pair_class"] == "" and r["recovery_pair_class"] == ""
    r = by.loc[(1, 1)]           # B confirmed but one pass unavailable
    assert bool(r["D_B"]) and not r["R_B"] and not r["b_usable"]
    assert r["trigger_pair_class"] == "" and r["recovery_pair_class"] == ""
    r = by.loc[(2, 1)]           # A confirmed off-frequency, B not detected
    assert r["trigger_pair_class"] == "A_only" and r["recovery_pair_class"] == "neither"
    r = by.loc[(1, 2)]           # A never scored
    assert r["a_status"] == "missing" and r["trigger_pair_class"] == ""
    r = by.loc[(2, 2)]
    assert r["trigger_pair_class"] == "both" and r["recovery_pair_class"] == "both"
    assert (table["analysis_status"] == ANALYSIS_STATUS).all()
    assert (~table["prespecified"].astype(bool)).all() and (table["interval"] == "none").all()
    # no aggregate row, contrast, or interval column anywhere
    assert not any(c.startswith(("diff", "delta", "lo", "hi", "p_")) for c in table.columns)


def test_pairs_abort_without_twin_or_on_metadata_mismatch():
    manifest = make_manifest()
    frame = attach_outcomes(manifest, make_per_star(manifest))
    no_b = frame[frame["campaign_id"] != "B2K2"]
    with pytest.raises(SystemExit, match=r"\(tic 2, K 2\): 1 nominal arm-A and 0 nominal arm-B"):
        arm_a_b_pairs(no_b)
    no_a = frame[frame["campaign_id"] != "A1K1"]
    with pytest.raises(SystemExit, match="0 nominal arm-A and 1 nominal arm-B"):
        arm_a_b_pairs(no_a)
    dup_a = pd.concat([frame, frame[frame["campaign_id"] == "A1K0"]], ignore_index=True)
    with pytest.raises(SystemExit, match="2 nominal arm-A and 1 nominal arm-B"):
        arm_a_b_pairs(dup_a)
    for column, value in (("wg_contrasts", 999), ("template_status", "candidate"),
                          ("template_source_id", "other")):
        bad = frame.copy()
        bad.loc[bad["campaign_id"] == "A2K2", column] = value
        with pytest.raises(SystemExit, match=f"metadata differ on \\['{column}'\\]"):
            arm_a_b_pairs(bad)
    # a target missing one of its three strata is not a valid nominal schedule
    partial = frame[~frame["campaign_id"].isin(["A2K2", "B2K2"])]
    with pytest.raises(SystemExit, match=r"exactly K=\{0,1,2\}"):
        arm_a_b_pairs(partial)


def test_control_reuse_sorting_rule_and_guards():
    reuse = pd.DataFrame([
        {"control_campaign_id": "C3", "template_source_id": "s3", "n_b_assignments": 2, "n_targets": 2},
        {"control_campaign_id": "C1", "template_source_id": "s1", "n_b_assignments": 5, "n_targets": 4},
        {"control_campaign_id": "C4", "template_source_id": "s4", "n_b_assignments": 1, "n_targets": 1},
        {"control_campaign_id": "C2", "template_source_id": "s2", "n_b_assignments": 5, "n_targets": 5},
        {"control_campaign_id": "C0", "template_source_id": "s0", "n_b_assignments": 2, "n_targets": 1},
    ])
    source = control_reuse_source(reuse)
    assert list(source.columns) == REUSE_SOURCE_COLUMNS
    # descending n_b_assignments, ties broken by ascending control_campaign_id
    assert source["control_campaign_id"].tolist() == ["C1", "C2", "C0", "C3", "C4"]
    assert source["bar_index"].tolist() == [0, 1, 2, 3, 4]
    assert source["n_targets"].tolist() == [4, 5, 1, 2, 1]          # carried, not plotted
    assert (source["analysis_status"] == ANALYSIS_STATUS).all()
    assert (source["interval"] == "none").all() and (~source["prespecified"].astype(bool)).all()
    dup = pd.concat([reuse, reuse.head(1)], ignore_index=True)
    with pytest.raises(SystemExit, match="one row per unique control"):
        control_reuse_source(dup)
    bad_counts = reuse.copy()
    bad_counts.loc[0, "n_targets"] = 3            # n_targets > n_b_assignments
    with pytest.raises(SystemExit, match="n_b_assignments >= n_targets"):
        control_reuse_source(bad_counts)
    with pytest.raises(SystemExit, match="columns"):
        control_reuse_source(reuse.drop(columns=["n_targets"]))


def test_control_reuse_must_match_the_manifest_recount():
    manifest = make_manifest()
    recount = pd.DataFrame([
        {"control_campaign_id": f"Csrc{t}{k}", "template_source_id": f"src{t}{k}",
         "n_b_assignments": 1, "n_targets": 1} for t, k, *_ in WINDOWS
    ])
    source = control_reuse_source(recount, manifest)
    assert len(source) == 6 and source["control_campaign_id"].is_monotonic_increasing
    inflated = recount.copy()
    inflated.loc[0, "n_b_assignments"] = 2
    with pytest.raises(SystemExit, match="does not equal the manifest"):
        control_reuse_source(inflated, manifest)


@pytest.mark.skipif(not (PILOT / "metrics" / "per_star.csv").exists(),
                    reason="archived gen2 pilot not present on this machine")
def test_cli_smoke_on_archived_pilot(tmp_path):
    base = [sys.executable, str(SCRIPT),
            "--metrics-dir", str(PILOT / "metrics"),
            "--shard-manifest", str(PILOT / "run" / "shard_manifest_gen2.csv"),
            "--out-dir", str(tmp_path)]
    refused = subprocess.run(base, capture_output=True, text=True, cwd=REPO)
    assert refused.returncode != 0 and "pilot" in refused.stderr
    assert not list(tmp_path.iterdir())
    done = subprocess.run(base + ["--allow-pilot"], capture_output=True, text=True, cwd=REPO)
    assert done.returncode == 0, done.stderr
    names = {"d2_k_template_status.csv", "d2_control_reuse.png", "d2_control_reuse_source.csv",
             "d2_control_reuse.meta.json", "d2_arm_a_b_pairs.csv",
             "d2_descriptives.README.md", "d2_descriptives.manifest.json"}
    assert names <= {p.name for p in tmp_path.iterdir()}

    k_table = pd.read_csv(tmp_path / "d2_k_template_status.csv")
    assert list(k_table.columns) == K_TABLE_COLUMNS and len(k_table) == 18
    assert (k_table["analysis_status"] == PILOT_DEV_STATUS).all()
    assert (k_table["analysis_status"] != ANALYSIS_STATUS).all()
    for endpoint in ENDPOINTS:
        assert int(k_table[k_table["endpoint"] == endpoint]["n_scheduled"].sum()) == 309
    assert int(k_table[k_table["endpoint"] == "trigger"]["n_usable"].sum()) == 30
    rec = k_table[k_table["endpoint"] == "recovery"]["k_success"].to_numpy()
    trig = k_table[k_table["endpoint"] == "trigger"]["k_success"].to_numpy()
    assert (rec <= trig).all()

    pairs = pd.read_csv(tmp_path / "d2_arm_a_b_pairs.csv", dtype={"a_sid": str, "b_sid": str},
                        keep_default_na=False)
    assert list(pairs.columns) == PAIR_COLUMNS and len(pairs) == 309
    assert pairs.groupby("tic").size().eq(3).all() and pairs["tic"].nunique() == 103
    usable = pairs["pair_usable"].astype(str).str.lower() == "true"
    assert int(usable.sum()) == 30
    assert (pairs.loc[~usable, ["trigger_pair_class", "recovery_pair_class"]] == "").all().all()
    assert set(pairs.loc[usable, "trigger_pair_class"]) <= {"both", "A_only", "B_only", "neither"}
    assert (pairs["a_sid"].str.startswith("93") & pairs["b_sid"].str.startswith("92")).all()

    source = pd.read_csv(tmp_path / "d2_control_reuse_source.csv", dtype={"control_campaign_id": str})
    assert list(source.columns) == REUSE_SOURCE_COLUMNS and len(source) == 106
    assert int(source["n_b_assignments"].sum()) == 309
    key = list(zip(-source["n_b_assignments"], source["control_campaign_id"]))
    assert key == sorted(key)
    meta = json.loads((tmp_path / "d2_control_reuse.meta.json").read_text(encoding="utf-8"))
    assert meta["analysis_status"] == PILOT_DEV_STATUS and meta["prespecified"] is False
    assert meta["interval"] == "none" and meta["n_controls"] == 106
    assert meta["disclosure"] == DISCLOSURE
    for name, digest in meta["outputs_sha256"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest

    manifest = json.loads((tmp_path / "d2_descriptives.manifest.json").read_text(encoding="utf-8"))
    assert manifest["pilot_bundle"] is True and manifest["analysis_status"] == PILOT_DEV_STATUS
    assert manifest["counts"]["pairs"] == 309 and manifest["counts"]["unique_controls"] == 106
    for name, digest in manifest["outputs_sha256"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    assert "scripts/generalization/descriptive/d2_descriptives.py" not in manifest["campaign_sha256"]
    assert DISCLOSURE in (tmp_path / "d2_descriptives.README.md").read_text(encoding="utf-8")
