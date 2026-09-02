"""compare_engines: roster-based frames, exact discordance bound, strict-
recovery control contrast, registration binding."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))

import compare_engines as ce  # noqa: E402
from metrics_generalization import cp_one_sided_bounds  # noqa: E402

PY = ROOT / ".venv-gen" / "bin" / "python"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(sids, statuses, cls="dsct_flag1", **extra):
    return pd.DataFrame({"sid": sids, "class_label": cls, "best_status": statuses,
                         "low_status": statuses, "high_status": statuses,
                         "low_available": True, "high_available": True,
                         "best_candidate_matches_dominant": ["direct" if s == "confirmed" else "unmatched" for s in statuses],
                         "freq_scorable": True, "eligible_any_pass": True, "best_frequency_per_day": 5.0,
                         "baseline_days": 1000.0, "primary_freq": 5.0, **extra})


def test_build_frames_missing_is_failure_and_runner_loss_aborts():
    split = pd.DataFrame({"dataset": ["d3"] * 5, "sid": list("abcde"), "key": [""] * 5, "group": ["dsct_flag1"] * 5,
                          "scenario": [""] * 5, "split": ["holdout", "holdout", "holdout", "holdout", "dev_smoke"]})
    frozen = _rows(list("abcde"), ["confirmed", "not_detected", "confirmed", "missing", "confirmed"])
    v2 = _rows(list("ab"), ["confirmed", "confirmed"])
    runner = {"a", "b"}          # c has no shard (not crossmatched); d is missing in both
    f, v, counts = ce.build_frames("d3", "holdout", split, frozen, v2, runner)
    assert list(f["sid"]) == ["a", "b", "c", "d"] and list(v["sid"]) == ["a", "b", "c", "d"]
    assert v.loc[v["sid"] == "c", "best_status"].iloc[0] == "missing"
    assert counts["roster_ids"] == 4 and counts["v2_missing_no_shard"] == 2
    with pytest.raises(SystemExit):
        ce.build_frames("d3", "holdout", split, frozen, v2, {"a", "b", "c"})


def test_exact_discordance_bound_when_no_discordant_pairs():
    rng = np.random.default_rng(0)
    x = np.array([True, False, True, False, False])
    row = ce.paired_rate_row("P", "f", x, x.copy(), rng)
    upper = cp_one_sided_bounds(0, 5)[1]
    assert row["diff"] == 0.0 and row["diff_lo"] == pytest.approx(-upper) and row["diff_hi"] == pytest.approx(upper)
    assert "discordance bound" in row["note"] and row["mcnemar_exact_p"] == 1.0


def test_strict_recovery_control_contrast():
    rng = np.random.default_rng(1)
    b = pd.DataFrame({"sid": ["b1", "b2"], "arm": "B", "scenario": "nominal", "cluster": ["t1", "t2"],
                      "control_campaign_id": ["c1", "c2"], "primary_freq": [5.0, 7.0], "baseline_days": 1000.0,
                      "best_status": ["confirmed", "confirmed"], "best_frequency_per_day": [5.0, 7.0004]})
    c = pd.DataFrame({"sid": ["c1", "c2"], "arm": "ctrl", "scenario": "control", "cluster": ["c1", "c2"],
                      "control_campaign_id": "", "primary_freq": math.nan, "baseline_days": 1000.0,
                      "best_status": ["confirmed", "not_detected"], "best_frequency_per_day": [5.0, math.nan]})
    frozen = pd.concat([b, c], ignore_index=True)
    v2 = frozen.copy()
    v2.loc[v2["sid"] == "c1", "best_status"] = "not_detected"    # v2 removes the control's false trigger
    rows = {r["endpoint"]: r for r in ce.d2_control_contrast_rows(frozen, v2, rng, "")}
    # frozen: t1 D_b - D_c = 0, t2 = 1 -> 0.5; v2: 1 and 1 -> 1.0
    assert rows["control_contrast_trigger"]["frozen_p"] == pytest.approx(0.5)
    assert rows["control_contrast_trigger"]["v2_p"] == pytest.approx(1.0)
    # strict recovery: frozen t1 R_b - R_c = 1 - 1 = 0 (the control matched the partner's frequency),
    # t2 = 1 - 0; v2 t1 = 1 - 0
    assert rows["control_contrast_strict_recovery"]["frozen_p"] == pytest.approx(0.5)
    assert rows["control_contrast_strict_recovery"]["v2_p"] == pytest.approx(1.0)


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_cli_refuses_unbound_inputs(tmp_path):
    """The comparison must be bound to the registration: an unregistered
    runner list is refused before any endpoint is computed."""
    reg = tmp_path / "reg"
    reg.mkdir()
    split = reg / "split.csv"
    pd.DataFrame({"dataset": ["d3"], "sid": ["a"], "key": [""], "group": ["dsct_flag1"], "scenario": [""],
                  "split": ["holdout"]}).to_csv(split, index=False)
    (reg / "split_manifest.json").write_text(json.dumps({"outputs": {"split.csv": _sha(split), "d3_holdout.txt": "0" * 64}}))
    runner = reg / "d3_holdout.txt"
    runner.write_text("a\n")
    for d in ("frozen", "v2"):
        (tmp_path / d).mkdir()
        _rows(["a"], ["confirmed"]).to_csv(tmp_path / d / "per_star.csv", index=False)
        (tmp_path / d / "manifest.json").write_text(json.dumps({"dataset": "d3", "engine": d, "pilot": False,
                                                                 "replay_attestation": {}}))
    run_manifest = tmp_path / "run_manifest.json"
    run_manifest.write_text(json.dumps({"engine": "v2", "dataset": "d3-kepler-dsct", "binding": {}}))
    res = subprocess.run([str(PY), str(ROOT / "scripts/v2/compare_engines.py"), "--dataset", "d3", "--half", "holdout",
                          "--frozen-per-star", str(tmp_path / "frozen/per_star.csv"),
                          "--v2-per-star", str(tmp_path / "v2/per_star.csv"), "--split", str(split),
                          "--runner-list", str(runner), "--v2-run-manifest", str(run_manifest),
                          "--frozen-metrics-dir", str(tmp_path / "frozen"), "--v2-metrics-dir", str(tmp_path / "v2"),
                          "--registration-root", str(reg), "--out-dir", str(tmp_path / "out")],
                         capture_output=True, text=True, cwd=ROOT)
    assert res.returncode != 0 and "registered" in (res.stdout + res.stderr)
    assert not (tmp_path / "out" / "endpoints.csv").exists()
