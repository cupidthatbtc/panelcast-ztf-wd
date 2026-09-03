from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/generalization/descriptive/synthesis_table.py"
SPEC = importlib.util.spec_from_file_location("synthesis_table", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
synthesis_table = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = synthesis_table
SPEC.loader.exec_module(synthesis_table)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def completeness_rows(dataset: str) -> list[dict]:
    if dataset == "d1":
        return [
            {"pass": "best", "rule": "confirmed", "scope": "detection_eligible_roster", "n": 13, "ess": 13, "p": 11 / 13, "lo": 0.58, "hi": 0.96},
            {"pass": "best", "rule": "confirmed", "scope": "freq_recovery_scorable", "n": 4, "ess": 4, "p": 0.25, "lo": 0.05, "hi": 0.70},
            {"pass": "best", "rule": "census", "scope": "detection_eligible_roster", "n": 13, "ess": 13, "p": 9 / 13, "lo": 0.42, "hi": 0.87},
            {"pass": "best", "rule": "either", "scope": "detection_eligible_roster", "n": 13, "ess": 13, "p": 1.0, "lo": 0.77, "hi": 1.0},
        ]
    return [
        {"pass": "best", "rule": "confirmed", "scope": "detection_eligible_roster", "n": 20, "ess": 20, "p": 0.5, "lo": 0.30, "hi": 0.70},
        {"pass": "best", "rule": "confirmed", "scope": "freq_recovery_scorable", "n": 12, "ess": 12, "p": 0.25, "lo": 0.09, "hi": 0.53},
        {"pass": "best", "rule": "census", "scope": "detection_eligible_roster", "n": 20, "ess": 20, "p": 0.1, "lo": 0.03, "hi": 0.30},
        {"pass": "best", "rule": "either", "scope": "detection_eligible_roster", "n": 20, "ess": 20, "p": 0.55, "lo": 0.34, "hi": 0.74},
    ]


def make_d1(root: Path, *, pilot: bool = False) -> Path:
    metrics = root / "d1_metrics"
    write_json(metrics / "manifest.json", {"dataset": "d1", "pilot": pilot})
    fields = ["pass", "rule", "scope", "n", "ess", "p", "lo", "hi"]
    write_csv(metrics / "completeness_by_class_pass_rule.csv", fields, completeness_rows("d1"))
    write_json(
        metrics / "contingency_complementarity.json",
        {
            "n_positives_scored": 13,
            "table": {"census_and_ls": 7, "census_only": 2, "ls_only": 4, "neither": 0},
            "union_completeness": {"p": 1.0, "lo": 0.77, "hi": 1.0},
            "incremental_census_only": {"p": 2 / 13, "lo": 0.04, "hi": 0.42},
            "mcnemar_exact_p_secondary": 0.6875,
        },
    )
    write_json(
        metrics / "chance_match.json",
        {
            "permutations": 100,
            "accidental_direct_match_rate_mean": 0.01,
            "accidental_direct_match_rate_p95": 0.03,
        },
    )
    write_csv(
        metrics / "per_star.csv",
        ["sid", "label_positive", "best_status"],
        [
            {"sid": "c1", "label_positive": "False", "best_status": "candidate"},
            {"sid": "c2", "label_positive": "False", "best_status": "not_detected"},
            {"sid": "c3", "label_positive": "False", "best_status": "not_detected"},
            {"sid": "c4", "label_positive": "False", "best_status": "not_detected"},
            {"sid": "c5", "label_positive": "False", "best_status": "not_detected"},
        ],
    )
    return metrics


def make_d3(root: Path, *, pilot: bool = False) -> Path:
    bundle = root / "d3_bundle"
    metrics = bundle / "metrics"
    write_json(metrics / "manifest.json", {"dataset": "d3", "pilot": pilot})
    fields = ["pass", "rule", "scope", "n", "ess", "p", "lo", "hi"]
    write_csv(metrics / "completeness_by_class_pass_rule.csv", fields, completeness_rows("d3"))
    write_csv(
        metrics / "trigger_rates.csv",
        ["quantity", "rule", "n", "ess", "p", "lo", "hi"],
        [{"quantity": "negative_class_trigger_rate", "rule": "confirmed", "n": 40, "ess": 40, "p": 0.4, "lo": 0.26, "hi": 0.55}],
    )
    write_json(
        metrics / "contingency_complementarity.json",
        {
            "n_positives_scored": 18,
            "table": {"census_and_ls": 1, "census_only": 1, "ls_only": 8, "neither": 8},
            "union_completeness": {"p": 10 / 18, "lo": 0.34, "hi": 0.75},
            "incremental_census_only": {"p": 1 / 18, "lo": 0.01, "hi": 0.26},
            "mcnemar_exact_p_secondary": 0.04,
        },
    )
    write_csv(
        metrics / "ppv.csv",
        ["estimand", "p", "lo", "hi", "interval", "n_triggered"],
        [{"estimand": "frame_specific_label_ppv", "p": 0.2, "lo": 0.15, "hi": 0.25, "interval": "survey_bootstrap_fpc_rescaled", "n_triggered": 25}],
    )
    write_json(
        metrics / "chance_match.json",
        {
            "permutations": 100,
            "accidental_direct_match_rate_mean": 0.02,
            "accidental_direct_match_rate_p95": 0.05,
        },
    )
    return bundle


def make_d2(root: Path) -> Path:
    bundle = root / "d2_bundle"
    metrics = bundle / "metrics"
    write_json(metrics / "manifest.json", {"dataset": "d2", "pilot": False})
    cluster_fields = [
        "arm", "scenario", "endpoint", "denominator", "n_targets", "p", "lo", "hi", "interval"
    ]
    write_csv(
        metrics / "d2_cluster_completeness.csv",
        cluster_fields,
        [
            {"arm": "B", "scenario": "nominal", "endpoint": "recovery", "denominator": "eligible", "n_targets": 103, "p": 0.3, "lo": 0.2, "hi": 0.4, "interval": "cluster_bootstrap"},
            {"arm": "B", "scenario": "nominal", "endpoint": "recovery", "denominator": "usable", "n_targets": 100, "p": 0.31, "lo": 0.21, "hi": 0.41, "interval": "cluster_bootstrap"},
            {"arm": "B", "scenario": "nominal", "endpoint": "trigger", "denominator": "eligible", "n_targets": 103, "p": 0.6, "lo": 0.5, "hi": 0.7, "interval": "cluster_bootstrap"},
        ],
    )
    write_csv(metrics / "d2_scenario_contrasts.csv", ["scenario", "diff"], [])
    write_csv(
        metrics / "trigger_rates.csv",
        ["quantity", "rule", "n_completed", "k", "p", "cp_one_sided_95_upper"],
        [{"quantity": "fpr_gaussian", "rule": "confirmed", "n_completed": 1000, "k": 1, "p": 0.001, "cp_one_sided_95_upper": 0.0047}],
    )
    control_fields = [
        "endpoint", "n_pairs_scored", "n_targets", "n_unique_windows",
        "paired_diff_b_minus_c", "paired_diff_b_minus_c_lo", "paired_diff_b_minus_c_hi",
    ]
    write_csv(
        metrics / "d2_paired_controls_summary.csv",
        control_fields,
        [
            {"endpoint": "D", "n_pairs_scored": 309, "n_targets": 103, "n_unique_windows": 106, "paired_diff_b_minus_c": 0.2, "paired_diff_b_minus_c_lo": 0.1, "paired_diff_b_minus_c_hi": 0.3},
            {"endpoint": "R", "n_pairs_scored": 309, "n_targets": 103, "n_unique_windows": 106, "paired_diff_b_minus_c": 0.25, "paired_diff_b_minus_c_lo": 0.15, "paired_diff_b_minus_c_hi": 0.35},
        ],
    )
    write_json(
        metrics / "chance_match.json",
        {"derangements": 10000, "accidental_recovery_rate_mean": 0.01, "accidental_recovery_rate_p95": 0.02},
    )
    return bundle


def make_v2_comparison(root: Path, dataset: str) -> Path:
    directory = root / f"{dataset}_comparison"
    chance = (
        {
            "chance_match": {
                "v2": {
                    "permutations": 100,
                    "accidental_direct_match_rate_mean": 0.02,
                    "accidental_direct_match_rate_p95": 0.04,
                }
            }
        }
        if dataset == "d3"
        else {}
    )
    write_json(
        directory / "manifest.json",
        {"dataset": dataset, "half": "holdout", "registration": {"split_sha256": "abc"}, **chance},
    )
    endpoints = (
        ["P1_detection", "P2_recovery", "P3_negative_trigger"]
        if dataset == "d3"
        else [
            "P4_recovery_eligible",
            "P4_recovery_usable",
            "P4_trigger_eligible",
            "P5_gaussian_false_alarm",
            "control_contrast_trigger",
            "control_contrast_strict_recovery",
        ]
    )
    fields = [
        "endpoint", "frame", "n", "interval", "frozen_p", "frozen_lo", "frozen_hi",
        "v2_p", "v2_lo", "v2_hi", "diff", "diff_lo", "diff_hi", "mcnemar_exact_p",
        "note", "v2_chance_direct_mean", "v2_chance_direct_p95",
    ]
    rows = []
    for endpoint in endpoints:
        p5 = endpoint == "P5_gaussian_false_alarm"
        rows.append(
            {
                "endpoint": endpoint,
                "frame": f"{dataset} holdout",
                "n": 50,
                "interval": "cp_upper" if p5 else "wilson",
                "frozen_p": 0.2,
                "frozen_lo": "" if p5 else 0.1,
                "frozen_hi": 0.3,
                "v2_p": 0.25,
                "v2_lo": "" if p5 else 0.15,
                "v2_hi": 0.35,
                "diff": 0.05,
                "diff_lo": -0.01,
                "diff_hi": 0.11,
                "mcnemar_exact_p": 0.2,
                "note": "paired holdout",
                "v2_chance_direct_mean": 0.02 if endpoint == "P2_recovery" else "",
                "v2_chance_direct_p95": 0.04 if endpoint == "P2_recovery" else "",
            }
        )
    write_csv(directory / "endpoints.csv", fields, rows)
    return directory


def build_synthetic(tmp_path: Path):
    d1 = make_d1(tmp_path)
    d3 = make_d3(tmp_path)
    out = tmp_path / "out"
    result = synthesis_table.build_synthesis(out_dir=out, d1_metrics=d1, d3_bundle=d3)
    return d1, d3, out, result


def test_builds_d1_d3_and_blanks_absent_slots(tmp_path: Path) -> None:
    _, _, out, result = build_synthetic(tmp_path)
    with (out / "synthesis_table.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    d1_p1 = next(row for row in rows if row["dataset"] == "D1" and row["endpoint"] == "P1_detection")
    d3_p3 = next(row for row in rows if row["dataset"] == "D3" and row["arm"] == "frozen" and row["endpoint"] == "P3_negative_trigger")
    assert float(d1_p1["estimate"]) == pytest.approx(11 / 13)
    assert float(d3_p3["estimate"]) == pytest.approx(0.4)

    unavailable = [row for row in rows if row["dataset"] == "D2" or row["arm"] == "v2"]
    assert unavailable
    assert all(row["estimate"] == "" and row["notes"] == "bundle not available" for row in unavailable)
    assert result.manifest["datasets"]["present"] == ["D1/frozen", "D3/frozen"]
    assert result.cross_check == "not run (D3 README absent)"


def test_refuses_pilot_bundle_for_dataset_slot(tmp_path: Path) -> None:
    bundle = tmp_path / "d2_pilot"
    write_json(bundle / "metrics" / "manifest.json", {"dataset": "d2", "pilot": True})
    with pytest.raises(SystemExit, match=r"D2 frozen bundle is marked pilot=true"):
        synthesis_table.build_synthesis(out_dir=tmp_path / "out", d2_bundle=bundle)


def test_evidence_map_covers_every_filled_cell_and_hashes_sources(tmp_path: Path) -> None:
    _, _, out, _ = build_synthetic(tmp_path)
    evidence = json.loads((out / "evidence_map.json").read_text(encoding="utf-8"))
    cells = evidence["cells"]
    with (out / "synthesis_table.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        prefix = f"{row['dataset']}|{row['arm']}|{row['endpoint']}"
        for column, value in row.items():
            if not value:
                continue
            item = cells[f"{prefix}|{column}"]
            source = Path(item["file"])
            if not source.is_absolute():
                source = REPO_ROOT / source
            assert item["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()

    assert set(evidence["bundle_manifests"]) == {"D1/frozen", "D3/frozen"}
    assert all(not item["pilot"] and item["engine"] == "frozen" for item in evidence["bundle_manifests"].values())


def test_markdown_has_one_column_per_present_dataset_arm(tmp_path: Path) -> None:
    _, _, out, _ = build_synthetic(tmp_path)
    markdown = (out / "synthesis_table.md").read_text(encoding="utf-8")
    header = next(line for line in markdown.splitlines() if line.startswith("| Endpoint"))
    assert header == "| Endpoint | D1/frozen | D3/frozen |"
    assert "D2/frozen" not in markdown
    assert "D3/v2" not in markdown


def test_injected_d3_expected_mismatch_exits_one(tmp_path: Path) -> None:
    d3 = make_d3(tmp_path)
    with pytest.raises(SystemExit, match=r"P1_detection\.estimate") as exc:
        synthesis_table.build_synthesis(
            out_dir=tmp_path / "out",
            d3_bundle=d3,
            d3_expected={"P1_detection.estimate": 0.999},
        )
    assert isinstance(exc.value.code, str)  # a message-valued SystemExit maps to process status 1


def test_accepts_future_d2_and_v2_output_schemas(tmp_path: Path) -> None:
    d2 = make_d2(tmp_path)
    d2_v2 = make_v2_comparison(tmp_path, "d2")
    d3_v2 = make_v2_comparison(tmp_path, "d3")
    result = synthesis_table.build_synthesis(
        out_dir=tmp_path / "out",
        d2_bundle=d2,
        d2_v2_comparison=d2_v2,
        d3_v2_comparison=d3_v2,
    )
    lookup = {
        (row.values["dataset"], row.values["arm"], row.values["endpoint"]): row.values
        for row in result.rows
    }
    assert lookup[("D2", "frozen", "P4_recovery_eligible")]["estimate"] == pytest.approx(0.3)
    assert lookup[("D2", "frozen", "P5_fpr_upper")]["estimate"] == pytest.approx(0.0047)
    assert lookup[("D2", "v2", "P5_fpr_upper")]["estimate"] == pytest.approx(0.35)
    assert lookup[("D3", "v2", "P1_detection")]["diff"] == pytest.approx(0.05)
    assert lookup[("D3", "v2", "chance_match_mean")]["estimate"] == pytest.approx(0.02)
