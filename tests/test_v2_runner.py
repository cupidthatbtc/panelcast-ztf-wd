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
from v2_common import (  # noqa: E402
    DEV_RUNS_V2_DIGEST, DEV_RUN_SCHEDULE, VETO_AMENDMENT_COMMIT, registered_list, v2_digest,
)
from v2_helpers import synthetic_star, write_shard  # noqa: E402

PY = ROOT / ".venv-gen" / "bin" / "python"
RUNNER = ROOT / "scripts" / "v2" / "run_v2_ls.py"
SIDS = ["9000000000000000001", "9000000000000000002", "9000000000000000003"]


def _amendment_binding(reg: Path) -> dict:
    """V2_PLAN.md §10 (2026-09-04): every registered artifact binds the amendment
    commit and four well-formed dev-run records (one per §5 schedule entry, at
    the pre-amendment digest, with the registration root's dev-list SHAs)."""
    records = []
    for i, ((dataset, window), name) in enumerate(DEV_RUN_SCHEDULE.items()):
        sha, n = registered_list(reg, name)
        records.append({"manifest": f"{dataset}_w{window:g}/manifest.json", "sha256": str(i) * 64,
                        "dataset": dataset, "trend_window_days": window, "v2_digest": DEV_RUNS_V2_DIGEST,
                        "stars_file_sha256": sha, "completed": n})
    return {"dev_runs_v2_digest": DEV_RUNS_V2_DIGEST, "veto_amendment_commit": VETO_AMENDMENT_COMMIT,
            "dev_runs": records}


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
    (reg / "d3_dev.txt").write_text(SIDS[2] + "\n")
    (reg / "d2_dev.txt").write_text("9000000000000000009\n")
    (reg / "V2_PLAN.md").write_text("# plan\n")
    (reg / "dev_tuning.csv").write_text("combination,J\nW30_N6_phi0.15_r0.3-1.5,0.1\n")
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
    (reg / "split_manifest.json").write_text(json.dumps({"outputs": {"d3_holdout.txt": sha(holdout),
                                                                     "split.csv": sha(split)}}))
    (reg / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps({
        "overrides": {"n_window_peaks": 6}, "v2_digest": digest(), "split_sha256": sha(split),
        "plan_sha256": sha(reg / "V2_PLAN.md"), "preregistration_commit": head,
        "tuning_evidence_sha256": sha(reg / "dev_tuning.csv"), **_amendment_binding(reg)}))
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
    # V2_PLAN.md §10 (2026-09-04): an artifact without the amendment commit, the dev-run digest or the
    # four dev-run manifests is refused before any lock handling
    good_runs = artifact["dev_runs"]
    for broken in ({"veto_amendment_commit": "f" * 40}, {"dev_runs_v2_digest": v2_digest()}, {"dev_runs": []},
                   {"dev_runs": "junk"}, {"dev_runs": good_runs[:1] * 4},
                   {"dev_runs": [{**r, "sha256": good_runs[0]["sha256"]} for r in good_runs]},   # one manifest, 4 records
                   {"dev_runs": [{**r, "manifest": "same/manifest.json"} for r in good_runs]},
                   {"dev_runs": [{**good_runs[0], "stars_file_sha256": "0" * 64}, *good_runs[1:]]},
                   {"dev_runs": [{**good_runs[0], "v2_digest": v2_digest()}, *good_runs[1:]]}):
        (reg / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps({**artifact, "overrides": {"n_window_peaks": 6},
                                                                  **broken}))
        res = _run_reg(base + ["--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
        assert res.returncode != 0 and "does not match this checkout" in (res.stdout + res.stderr), broken


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


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_copied_registration_root_cannot_score_canonical_holdout_ids(tmp_path):
    """Round-3 bypass: a COPY of the canonical registration (without its lock,
    with altered allowed overrides) must not launch canonical holdout ids."""
    import hashlib
    import shutil

    from v2_common import v2_digest as digest

    canonical = ROOT / "generalization" / "v2"
    reg = tmp_path / "copied_reg"
    shutil.copytree(canonical, reg, ignore=shutil.ignore_patterns("HOLDOUT_LAUNCH_*", "codex", "__pycache__"))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
    (reg / "dev_tuning.csv").write_text("combination,J\nW30_N24_phi0.25_r0.2-2.0,0.2\n")
    (reg / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps({
        "overrides": {"n_window_peaks": 24}, "v2_digest": digest(), "split_sha256": sha(reg / "split.csv"),
        "plan_sha256": sha(reg / "V2_PLAN.md"), "preregistration_commit": head,
        "tuning_evidence_sha256": sha(reg / "dev_tuning.csv"), **_amendment_binding(reg)}))
    holdout_ids = [l.strip() for l in (canonical / "d3_holdout.txt").read_text().splitlines() if l.strip()]
    sid = holdout_ids[0]
    shards = tmp_path / "shards"
    write_shard(synthetic_star(sid, seed=3), shards / f"{sid}.csv.gz")
    (shards / "shard_index.txt").write_text(sid + "\n")
    res = _run_reg(["--shard-dir", str(shards), "--shard-index", str(shards / "shard_index.txt"),
                    "--out-dir", str(tmp_path / "out"), "--work-root", str(tmp_path / "work"),
                    "--dataset", "d3-kepler-dsct", "--machine", "test", "--workers", "1",
                    "--stars-file", str(reg / "d3_holdout.txt"), "--split-file", str(reg / "split.csv"),
                    "--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")], reg)
    assert res.returncode != 0 and "canonical registration" in (res.stdout + res.stderr)
    # refused BEFORE any lock handling: no lock under the copied root, no output
    assert not (reg / "HOLDOUT_LAUNCH_d3.json").exists()
    assert not (tmp_path / "out" / "stars").exists() or not list((tmp_path / "out" / "stars").glob("*.json"))
    assert not (tmp_path / "out" / "manifest.json").exists()


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_registered_holdout_refuses_debug_options_and_binds_passes(tmp_path):
    """Round-4 residual: the registered mode takes no debug options, requires
    the ordered frozen pass set and binds passes / code / environment in the lock."""
    shards = tmp_path / "shards"
    for i, sid in enumerate(SIDS):
        write_shard(synthetic_star(sid, seed=300 + i), shards / f"{sid}.csv.gz")
    index = shards / "shard_index.txt"
    index.write_text("\n".join(SIDS) + "\n")
    holder: dict = {}
    reg, holdout = _fake_registration(tmp_path, holder)
    out = tmp_path / "hold"
    base = ["--shard-dir", str(shards), "--shard-index", str(index), "--out-dir", str(out),
            "--work-root", str(tmp_path / "work"), "--dataset", "d3-test", "--machine", "test",
            "--workers", "2", "--stars-file", str(holdout), "--split-file", str(reg / "split.csv"),
            "--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")]
    for extra, needle in ((["--passes", "high,low"], "low,high"), (["--passes", "low"], "low,high"),
                          (["--allow-nonstandard-ids"], "--allow-nonstandard-ids"), (["--limit", "2"], "--limit")):
        res = _run_reg(base + extra, reg)
        assert res.returncode != 0 and needle in (res.stdout + res.stderr), extra
        assert not (reg / "HOLDOUT_LAUNCH_d3.json").exists()
    ok = _run_reg(base, reg)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    lock = json.loads((reg / "HOLDOUT_LAUNCH_d3.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    assert lock["passes"] == ["low", "high"] == manifest["passes"]
    assert lock["frozen_digest"] == manifest["binding"]["frozen_digest"]
    assert lock["shard_index_sha256"] == manifest["shard_index_sha256"]
    assert lock["constants_overrides"] == {"n_window_peaks": 6}
    import hashlib as _h
    assert lock["env_digest"] == _h.sha256(json.dumps(manifest["env"], sort_keys=True).encode()).hexdigest()
    # a relaunch with a different pass order is refused by the guard, not silently recomputed
    reorder = _run_reg(base + ["--passes", "high,low"], reg)
    assert reorder.returncode != 0
    assert json.loads((out / "manifest.json").read_text())["passes"] == ["low", "high"]


def test_v2_digest_covers_frozen_api():
    from v2_common import FROZEN_API_PATH, v2_file_shas

    shas = v2_file_shas()
    assert "scripts/generalization/frozen_api.py" in shas
    assert FROZEN_API_PATH.exists() and set(k for k in shas if k.startswith("scripts/v2/")) >= {
        "scripts/v2/analyze_star_v2.py", "scripts/v2/run_v2_ls.py", "scripts/v2/rule.py"}


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_relaunch_after_frozen_api_drift_is_refused(tmp_path):
    """Round-5 residual: editing frozen_api.py between launches changes the
    v2 runtime digest, so a registered relaunch is refused by the lock and an
    unregistered resume recomputes nothing silently (the binding differs)."""
    api = ROOT / "scripts" / "generalization" / "frozen_api.py"
    dirty = subprocess.run(["git", "status", "--porcelain", str(api)], cwd=ROOT, capture_output=True, text=True).stdout
    if dirty.strip():
        pytest.skip("frozen_api.py has local modifications; not touching it")
    shards = tmp_path / "shards"
    for i, sid in enumerate(SIDS):
        write_shard(synthetic_star(sid, seed=400 + i), shards / f"{sid}.csv.gz")
    index = shards / "shard_index.txt"
    index.write_text("\n".join(SIDS) + "\n")
    holder: dict = {}
    reg, holdout = _fake_registration(tmp_path, holder)
    out = tmp_path / "hold"
    base = ["--shard-dir", str(shards), "--shard-index", str(index), "--out-dir", str(out),
            "--work-root", str(tmp_path / "work"), "--dataset", "d3-test", "--machine", "test",
            "--workers", "2", "--stars-file", str(holdout), "--split-file", str(reg / "split.csv"),
            "--allow-holdout", "--constants", str(reg / "V2_CONSTANTS_FROZEN.json")]
    ok = _run_reg(base, reg)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    original = api.read_bytes()
    try:
        api.write_bytes(original + b"\n# drift (test)\n")
        drifted = _run_reg(base, reg)
    finally:
        api.write_bytes(original)
    assert drifted.returncode != 0 and ("frozen-constants artifact does not match" in (drifted.stdout + drifted.stderr)
                                        or "exact resume" in (drifted.stdout + drifted.stderr))
    # restored: the exact resume works again and reuses every result
    again = _run_reg(base, reg)
    assert again.returncode == 0 and "pending=0" in again.stdout
