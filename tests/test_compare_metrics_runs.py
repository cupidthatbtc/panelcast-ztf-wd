"""compare_metrics_runs: the ruled guard for the compliance re-run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization" / "descriptive"))

from compare_metrics_runs import compare  # noqa: E402


def _bundle(root: Path, attrition: str, manifest: dict, inputs: dict, extra: dict | None = None):
    root.mkdir(parents=True)
    (root / "per_star.csv").write_text("sid,best_status\n1,confirmed\n")
    (root / "trigger_rates.csv").write_text("quantity,p\nx,0.1\n")
    (root / "attrition.csv").write_text(attrition)
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "inputs_sha256.json").write_text(json.dumps(inputs))
    for name, content in (extra or {}).items():
        (root / name).write_text(content)


def test_guard_passes_on_expected_diffs_only(tmp_path):
    scalars = "roster,scored\n3,3\n"
    ref_m = {"dataset": "d3", "pilot": False, "campaign_sha256": {"a": "1"}, "env": {"machine": "laptop"},
             "inputs_sha256_count": 2, "inputs_sha256_digest": "x", "frozen_sha256": {"f": "1"}}
    cand_m = dict(ref_m, campaign_sha256={"a": "2"}, env={"machine": "mac"}, inputs_sha256_digest="y")
    _bundle(tmp_path / "ref", scalars, ref_m, {r"C:\Users\lap\roster.csv": "s1", r"C:\Users\lap\stars\1.json": "s2"})
    _bundle(tmp_path / "cand", "class_label,n_roster\ndsct_flag0,3\n", cand_m,
            {"/mac/roster.csv": "s1", "/mac/stars/1.json": "s2"},
            extra={"attrition_summary.csv": scalars, "d3_mo_join_covariates.csv": "mo_join_status\n"})
    assert compare(tmp_path / "ref", tmp_path / "cand") == []


def test_guard_fails_on_science_diff_and_bad_manifest(tmp_path):
    scalars = "roster,scored\n3,3\n"
    m = {"dataset": "d3", "pilot": False, "frozen_sha256": {"f": "1"}}
    _bundle(tmp_path / "ref", scalars, m, {"a": "s1"})
    _bundle(tmp_path / "cand", "x\n", dict(m, frozen_sha256={"f": "2"}), {"a": "s1"},
            extra={"attrition_summary.csv": scalars, "d3_mo_join_covariates.csv": "", "rogue.csv": ""})
    (tmp_path / "cand" / "per_star.csv").write_text("sid,best_status\n1,candidate\n")
    problems = compare(tmp_path / "ref", tmp_path / "cand")
    joined = "\n".join(problems)
    assert "science output differs: per_star.csv" in joined
    assert "manifest key differs: frozen_sha256" in joined
    assert "unexpected new files" in joined
