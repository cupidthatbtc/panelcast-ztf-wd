"""compare_metrics_runs: the disclosed last-ulp exception for named truth
columns of per_star.csv (platform CSV float parsing), and nothing else."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization" / "descriptive"))

from compare_metrics_runs import compare, within_known_ulp  # noqa: E402


def _bundle(root: Path, per_star: str) -> None:
    root.mkdir(parents=True)
    (root / "per_star.csv").write_text(per_star)
    (root / "attrition.csv").write_text("roster,scored\n3,3\n")
    (root / "attrition_summary.csv").write_text("roster,scored\n3,3\n")
    (root / "manifest.json").write_text(json.dumps({"dataset": "d2", "frozen_sha256": {"f": "1"}}))
    (root / "inputs_sha256.json").write_text(json.dumps({"a": "s1"}))


REF = "sid,primary_freq,truth_period_days,best_status\n1,431.8272690923631,0.016234375,confirmed\n2,5.0,0.2,not_detected\n"
ULP = "sid,primary_freq,truth_period_days,best_status\n1,431.82726909236305,0.016234375000000002,confirmed\n2,5.0,0.2,not_detected\n"
DECISION = "sid,primary_freq,truth_period_days,best_status\n1,431.8272690923631,0.016234375,candidate\n2,5.0,0.2,not_detected\n"
BIG = "sid,primary_freq,truth_period_days,best_status\n1,431.83,0.016234375,confirmed\n2,5.0,0.2,not_detected\n"


def test_last_ulp_truth_difference_passes_only_with_the_named_columns(tmp_path):
    _bundle(tmp_path / "ref", REF)
    _bundle(tmp_path / "cand", ULP)
    assert compare(tmp_path / "ref", tmp_path / "cand") != []          # strict: differs
    assert compare(tmp_path / "ref", tmp_path / "cand", ("primary_freq", "truth_period_days")) == []
    assert compare(tmp_path / "ref", tmp_path / "cand", ("primary_freq",)) != []   # second column unlisted


def test_decision_or_large_differences_never_pass(tmp_path):
    _bundle(tmp_path / "ref", REF)
    _bundle(tmp_path / "cand_decision", DECISION)
    _bundle(tmp_path / "cand_big", BIG)
    cols = ("primary_freq", "truth_period_days", "best_status")
    assert compare(tmp_path / "ref", tmp_path / "cand_decision", cols) != []   # non-numeric difference
    ok, detail = within_known_ulp(tmp_path / "ref" / "per_star.csv", tmp_path / "cand_big" / "per_star.csv",
                                  ("primary_freq",))
    assert not ok and "exceeds" in detail
