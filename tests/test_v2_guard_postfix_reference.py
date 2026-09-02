"""compare_metrics_runs: a POST-fix reference (attrition_summary.csv present)
is compared file-for-file on attrition.csv and attrition_summary.csv."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization" / "descriptive"))

from compare_metrics_runs import compare  # noqa: E402


def _bundle(root: Path, attrition: str, summary: str, manifest: dict) -> None:
    root.mkdir(parents=True)
    (root / "per_star.csv").write_text("sid,best_status\n1,confirmed\n")
    (root / "attrition.csv").write_text(attrition)
    (root / "attrition_summary.csv").write_text(summary)
    (root / "d3_mo_join_covariates.csv").write_text("mo_join_status\n")
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "inputs_sha256.json").write_text(json.dumps({"a": "s1"}))


def test_postfix_reference_passes_when_identical(tmp_path):
    table = "class_label,n_roster\ndsct_flag0,3\n"
    scalars = "roster,scored\n3,3\n"
    ref = {"dataset": "d3", "frozen_sha256": {"f": "1"}, "campaign_sha256": {"a": "1"}}
    cand = dict(ref, campaign_sha256={"a": "2"}, engine="frozen")
    _bundle(tmp_path / "ref", table, scalars, ref)
    _bundle(tmp_path / "cand", table, scalars, cand)
    assert compare(tmp_path / "ref", tmp_path / "cand") == []


def test_postfix_reference_fails_on_attrition_diff(tmp_path):
    scalars = "roster,scored\n3,3\n"
    m = {"dataset": "d3", "frozen_sha256": {"f": "1"}}
    _bundle(tmp_path / "ref", "class_label,n_roster\ndsct_flag0,3\n", scalars, m)
    _bundle(tmp_path / "cand", "class_label,n_roster\ndsct_flag0,4\n", scalars, m)
    problems = compare(tmp_path / "ref", tmp_path / "cand")
    assert any("attrition.csv" in p for p in problems)
