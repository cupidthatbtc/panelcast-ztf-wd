"""run_v2_ls.py: constants loading, split guard, end-to-end resume-safe run."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_v2_ls  # noqa: E402
from v2_common import v2_digest  # noqa: E402
from v2_helpers import synthetic_star, write_shard  # noqa: E402

PY = ROOT / ".venv-gen" / "bin" / "python"
RUNNER = ROOT / "scripts" / "v2" / "run_v2_ls.py"
SIDS = ["9000000000000000001", "9000000000000000002", "9000000000000000003"]


def test_load_constants_accepts_declared_and_rejects_undeclared(tmp_path):
    c = run_v2_ls.load_constants('{"trend_window_days": 10.0, "amp_ratio": [0.5, 1.2]}')
    assert c.trend_window_days == 10.0 and (c.amp_ratio_min, c.amp_ratio_max) == (0.5, 1.2)
    path = tmp_path / "c.json"
    path.write_text('{"n_window_peaks": 24}')
    assert run_v2_ls.load_constants(str(path)).n_window_peaks == 24
    for bad in ('{"trend_window_days": 12.0}', '{"amp_ratio": [0.1, 9.0]}', '{"fap_threshold": 0.01}'):
        with pytest.raises(ValueError):
            run_v2_ls.load_constants(bad)
    assert run_v2_ls.load_constants(None) is run_v2_ls.DEFAULT


def test_split_half_guard(tmp_path):
    split = tmp_path / "split.csv"
    pd.DataFrame({"dataset": ["d3"] * 3, "sid": ["a", "b", "c"], "key": ["", "", ""],
                  "group": ["", "", ""], "scenario": ["", "", ""],
                  "split": ["dev", "dev", "holdout"]}).to_csv(split, index=False)
    assert run_v2_ls.split_half(split, "d3", {"a", "b"}) == "dev"
    assert run_v2_ls.split_half(split, "d3", {"c"}) == "holdout"
    with pytest.raises(SystemExit):
        run_v2_ls.split_half(split, "d3", {"a", "c"})
    with pytest.raises(SystemExit):
        run_v2_ls.split_half(split, "d3", {"zzz"})


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([str(PY), str(RUNNER), *args], capture_output=True, text=True, cwd=ROOT)


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_end_to_end_run_resume_and_constants_change(tmp_path):
    shards = tmp_path / "shards"
    for i, sid in enumerate(SIDS):
        write_shard(synthetic_star(sid, seed=100 + i), shards / f"{sid}.csv.gz")
    index = shards / "shard_index.txt"
    index.write_text("\n".join(SIDS) + "\n")
    out = tmp_path / "run"
    base = ["--shard-dir", str(shards), "--shard-index", str(index), "--out-dir", str(out),
            "--work-root", str(tmp_path / "work"), "--dataset", "d3-test", "--machine", "test",
            "--workers", "2", "--allow-nonstandard-ids"]
    first = _run(base)
    assert first.returncode == 0, first.stdout + first.stderr
    for sid in SIDS:
        assert (out / "stars" / f"{sid}.json").exists() and (out / "stars" / f"{sid}.prov.json").exists()
    completion = pd.read_csv(out / "completion.csv", dtype=str)
    assert (completion["status"] == "complete").all() and len(completion) == 3
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["engine"] == "v2" and manifest["machine"] == "test"
    assert manifest["binding"]["attestation_sha256"] == "v2-unattested"
    assert manifest["binding"]["v2_digest"] == v2_digest()
    assert manifest["replay_attestation"]["tier"] == "v2_unattested"
    prov = json.loads((out / "stars" / f"{SIDS[0]}.prov.json").read_text())
    assert prov["driver"] == "run_v2_ls.py" and prov["engine"] == "v2"
    assert prov["constants_sha256"] == manifest["constants_sha256"]

    second = _run(base)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "pending=0" in second.stdout
    assert json.loads((out / "progress.json").read_text())["completed_now"] == 0

    third = _run(base + ["--constants", '{"n_window_peaks": 6}'])
    assert third.returncode == 0, third.stdout + third.stderr
    assert "pending=3" in third.stdout
    assert json.loads((out / "manifest.json").read_text())["constants"]["n_window_peaks"] == 6


def _fake_registration(root: Path, split_sha_holder: dict) -> tuple[Path, Path]:
    """A minimal registered-holdout environment (split.csv, split_manifest.json,
    V2_PLAN.md, dev_tuning.csv, V2_CONSTANTS_FROZEN.json) under a test
    registration root selected with the V2_REGISTRATION_ROOT variable; the
    pre-registration commit is the repository HEAD (a real ancestor)."""
    import hashlib

    from v2_common import v2_digest as digest

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    reg = root / "reg"
    reg.mkdir()
    split = reg / "split.csv"
    pd.DataFrame({"dataset": ["d3"] * 3, "sid": SIDS, "key": [""] * 3, "group": ["dsct_flag1"] * 3,
                  "scenario": [""] * 3, "split": ["holdout", "holdout", "dev"]}).to_csv(split, index=False)
    holdout = reg / "d3_holdout.txt"
    holdout.write_text("\n".join(SIDS[:2]) + "\n")
    (reg / "V2_PLAN.md").write_text("# plan\n")
    (reg / "dev_tuning.csv").write_text("combination,J\nW30_N6_phi0.15_r0.3-1.5,0.1\n")
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
    (reg / "split_manifest.json").write_text(json.dumps({"outputs": {"d3_holdout.txt": sha(holdout),
                                                                     "split.csv": sha(split)}}))
    (reg / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps({
        "overrides": {"n_window_peaks": 6}, "v2_digest": digest(), "split_sha256": sha(split),
        "plan_sha256": sha(reg / "V2_PLAN.md"), "preregistration_commit": head,
        "tuning_evidence_sha256": sha(reg / "dev_tuning.csv")}))
    split_sha_holder["split"], split_sha_holder["commit"] = sha(split), head
    return reg, holdout


def _run_reg(args: list[str], reg: Path) -> subprocess.CompletedProcess:
    import os

    env = dict(os.environ, V2_REGISTRATION_ROOT=str(reg))
    return subprocess.run([str(PY), str(RUNNER), *args], capture_output=True, text=True, cwd=ROOT, env=env)


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_registered_holdout_mode_locks_and_refuses_drift(tmp_path):
    shards = tmp_path / "shards"
    for i, sid in enumerate(SIDS):
        write_shard(synthetic_star(sid, seed=200 + i), shards / f"{sid}.csv.gz")
    index = shards / "shard_index.txt"
    index.write_text("\n".join(SIDS) + "\n")
    holder: dict = {}
    reg, holdout = _fake_registration(tmp_path, holder)
    out = tmp_path / "hold"
    base = ["--shard-dir", str(shards), "--shard-index", str(index), "--out-dir", str(out),
            "--work-root", str(tmp_path / "work"), "--dataset", "d3-test", "--machine", "test",
            "--workers", "2", "--stars-file", str(holdout), "--split-file", str(reg / "split.csv")]
    refused = _run_reg(base, reg)
    assert refused.returncode != 0 and "HOLDOUT" in (refused.stdout + refused.stderr)
    no_artifact = _run_reg(base + ["--allow-holdout"], reg)
    assert no_artifact.returncode != 0 and "V2_CONSTANTS_FROZEN" in (no_artifact.stdout + no_artifact.stderr)
    # the split file must be the registered one (a copy elsewhere is refused)
    copy = tmp_path / "elsewhere.csv"
    copy.write_bytes((reg / "split.csv").read_bytes())
    elsewhere = _run_reg(base[:-1] + [str(copy), "--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert elsewhere.returncode != 0 and "registered split" in (elsewhere.stdout + elsewhere.stderr)
    ok = _run_reg(base + ["--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    lock = json.loads((reg / "HOLDOUT_LAUNCH_d3.json").read_text())
    assert lock["split_sha256"] == holder["split"] and lock["preregistration_commit"] == holder["commit"]
    assert lock["canonical_registration"] is False      # test root, recorded as non-canonical
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["binding"]["split_half"] == "holdout" and manifest["binding"]["plan_sha256"] == lock["plan_sha256"]
    assert manifest["binding"]["constants_artifact_sha256"] == lock["constants_artifact_sha256"]
    assert manifest["constants"]["n_window_peaks"] == 6 and manifest["holdout_registration"]["lock_file"]
    assert manifest["canonical_registration"] is False
    resume = _run_reg(base + ["--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert resume.returncode == 0 and "pending=0" in resume.stdout
    # a different constants artifact (drift) is refused by the lock
    (reg / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps({
        **json.loads((reg / "V2_CONSTANTS_FROZEN.json").read_text()), "overrides": {"n_window_peaks": 24}}))
    drift = _run_reg(base + ["--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert drift.returncode != 0 and "exact resume" in (drift.stdout + drift.stderr)
    limited = _run_reg(base + ["--allow-holdout", "--limit", "1", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert limited.returncode != 0
    # a bogus pre-registration commit is refused
    artifact = json.loads((reg / "V2_CONSTANTS_FROZEN.json").read_text())
    (reg / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps({**artifact, "overrides": {"n_window_peaks": 6},
                                                              "preregistration_commit": "deadbeef"}))
    bogus = _run_reg(base + ["--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert bogus.returncode != 0 and "not in this repository" in (bogus.stdout + bogus.stderr)


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_debug_runs_cannot_touch_registered_holdout_ids(tmp_path):
    """Round-2 bypass: a debug run (--allow-nonstandard-ids, no split file) on
    a CANONICAL holdout id is refused."""
    holdout_ids = [l.strip() for l in (ROOT / "generalization/v2/d3_holdout.txt").read_text().splitlines() if l.strip()]
    sid = holdout_ids[0]
    shards = tmp_path / "shards"
    write_shard(synthetic_star(sid, seed=7), shards / f"{sid}.csv.gz")
    (shards / "shard_index.txt").write_text(sid + "\n")
    stars = tmp_path / "ids.txt"
    stars.write_text(sid + "\n")
    out = tmp_path / "dbg"
    for extra in ([], ["--stars-file", str(stars)]):
        res = _run(["--shard-dir", str(shards), "--shard-index", str(shards / "shard_index.txt"),
                    "--out-dir", str(out), "--work-root", str(tmp_path / "work"), "--dataset", "d3-test",
                    "--machine", "test", "--workers", "1", "--allow-nonstandard-ids", *extra])
        assert res.returncode != 0 and "registered HOLDOUT ids" in (res.stdout + res.stderr)
    assert not (out / "stars").exists() or not list((out / "stars").glob("*.json"))
