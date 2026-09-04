"""V2_PLAN.md §10 (2026-09-04, round-7/8 revisions): the re-scored dev runs are
bound fail-closed. Every check reads the runner's OWN manifest schema
(source_count / pending_at_start / completed_now, top-level and binding
stars_file_sha256, split.half, constants.trend_window_days, limit); one test
produces an authentic manifest with the runner itself."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dev_tuning  # noqa: E402
import rescore_v2  # noqa: E402
import v2_common  # noqa: E402
from v2_common import (  # noqa: E402
    DEV_RUNS_V2_DIGEST, DEV_RUN_SCHEDULE, VETO_AMENDMENT_COMMIT, dev_run_record, registered_list,
    run_completion, v2_digest, validate_dev_run_records,
)
from v2_helpers import synthetic_star, write_shard  # noqa: E402

REG = ROOT / "generalization" / "v2"
PY = ROOT / ".venv-gen" / "bin" / "python"
RUNNER = ROOT / "scripts" / "v2" / "run_v2_ls.py"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(dataset: str, window: float, reg: Path = REG, **override) -> dict:
    """The runner's manifest schema (run_v2_ls.py main), dev half, complete."""
    sha, n = registered_list(reg, DEV_RUN_SCHEDULE[(dataset, window)])
    base = {"engine": "v2", "dataset": dataset, "driver": "run_v2_ls.py", "machine": "laptop-7i-5090",
            "source_count": n, "pending_at_start": n, "completed_now": n, "failures": {}, "limit": None,
            "passes": ["low", "high"], "stars_file_sha256": sha,
            "split": {"file": "split.csv", "sha256": "0" * 64, "half": "dev"},
            "constants": {"trend_window_days": window},
            "binding": {"engine": "v2", "v2_digest": DEV_RUNS_V2_DIGEST, "split_half": "dev",
                        "stars_file_sha256": sha}}
    base.update(override)
    return base


def _write_runs(root: Path, reg: Path = REG, **override) -> list[Path]:
    paths = []
    for (dataset, window) in DEV_RUN_SCHEDULE:
        run = root / f"{dataset[:2]}_w{window:g}"
        (run / "stars").mkdir(parents=True)
        (run / "manifest.json").write_text(json.dumps(_manifest(dataset, window, reg, **override)))
        paths.append(run / "manifest.json")
    return paths


def _sidecar(table: Path, record: dict, **override) -> None:
    prov = {"run_manifest_sha256": record["sha256"], "source_v2_digest": DEV_RUNS_V2_DIGEST,
            "rescore_v2_digest": v2_digest(), "rescore_csv_sha256": _sha(table), "dataset": record["dataset"],
            "trend_window_days": record["trend_window_days"], "stars_file_sha256": record["stars_file_sha256"]}
    prov.update(override)
    table.with_suffix(table.suffix + ".provenance.json").write_text(json.dumps(prov))


def test_constants_name_the_admitted_dev_digest_and_the_amendment_commit():
    assert DEV_RUNS_V2_DIGEST.startswith("ecc5df75d8f225cb") and len(DEV_RUNS_V2_DIGEST) == 64
    assert VETO_AMENDMENT_COMMIT.startswith("017c925e") and len(VETO_AMENDMENT_COMMIT) == 40
    assert v2_digest() != DEV_RUNS_V2_DIGEST   # the amendment moved the code digest


def test_run_completion_reads_the_runner_schema_and_fails_closed():
    assert run_completion({"source_count": 5, "pending_at_start": 2, "completed_now": 2}) == (5, 5)
    assert run_completion({"source_count": 5, "pending_at_start": 5, "completed_now": 3}) == (3, 5)
    with pytest.raises(SystemExit, match="completion fields"):
        run_completion({"total": 5, "pending_at_start": 5, "completed_now": 5})


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"binding": {"v2_digest": "0" * 64, "stars_file_sha256": "x"}}, "dev-run digest"),
        ({"split": {"half": "holdout"}}, "not dev"),
        ({"failures": {"9000000000000000001": "boom"}}, "failures"),
        ({"completed_now": 3}, "completion"),
        ({"pending_at_start": 0, "completed_now": 0, "source_count": 3}, "completion"),
        ({"constants": {"trend_window_days": 20.0}}, "schedule"),
        ({"limit": 10}, "limit"),
        ({"stars_file_sha256": "0" * 64}, "registered"),
        ({"engine": "frozen"}, "engine"),
    ],
)
def test_dev_run_record_rejects_a_bad_manifest(tmp_path, override, message):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0, **override)))
    with pytest.raises(SystemExit, match=message):
        dev_run_record(path, REG)


def test_dev_run_record_binds_a_good_manifest(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest("d2-tess-dav", 10.0)))
    record = dev_run_record(path, REG)
    sha, n = registered_list(REG, "d2_dev.txt")
    assert record == {"manifest": str(path), "sha256": _sha(path), "dataset": "d2-tess-dav",
                      "trend_window_days": 10.0, "v2_digest": DEV_RUNS_V2_DIGEST, "stars_file_sha256": sha,
                      "completed": n}


def test_rescore_refuses_a_foreign_stars_dir_and_an_incomplete_source(tmp_path):
    run = tmp_path / "run"
    (run / "stars").mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0)))
    with pytest.raises(SystemExit, match="own stars directory"):
        rescore_v2.verify_run_manifest(run / "manifest.json", tmp_path / "elsewhere")
    (run / "manifest.json").write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0, completed_now=1)))
    with pytest.raises(SystemExit, match="completion"):
        rescore_v2.verify_run_manifest(run / "manifest.json", run / "stars")
    (run / "manifest.json").write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0)))
    assert rescore_v2.verify_run_manifest(run / "manifest.json", run / "stars")["engine"] == "v2"


def test_rescore_cli_writes_a_provenance_sidecar_bound_to_the_source(tmp_path, monkeypatch):
    run = tmp_path / "run"
    (run / "stars").mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps(_manifest("d2-tess-dav", 10.0)))
    out = tmp_path / "rescore.csv"
    monkeypatch.setattr(sys, "argv", ["rescore_v2.py", "--stars-dir", str(run / "stars"),
                                      "--run-manifest", str(run / "manifest.json"), "--out", str(out)])
    rescore_v2.main()
    prov = json.loads((tmp_path / "rescore.csv.provenance.json").read_text())
    sha, _ = registered_list(REG, "d2_dev.txt")
    assert prov["run_manifest_sha256"] == _sha(run / "manifest.json")
    assert prov["source_v2_digest"] == DEV_RUNS_V2_DIGEST and prov["rescore_v2_digest"] == v2_digest()
    assert prov["dataset"] == "d2-tess-dav" and prov["trend_window_days"] == 10.0
    assert prov["stars_file_sha256"] == sha and prov["n_combinations"] == 27
    assert prov["rescore_csv_sha256"] == _sha(out)


def test_dev_tuning_accepts_exactly_the_registered_schedule(tmp_path):
    records = dev_tuning.verify_dev_run_manifests(_write_runs(tmp_path))
    assert {(r["dataset"], r["trend_window_days"]) for r in records} == set(DEV_RUN_SCHEDULE)
    assert all(r["v2_digest"] == DEV_RUNS_V2_DIGEST for r in records)


def test_dev_tuning_rejects_a_missing_or_duplicated_schedule_entry(tmp_path):
    paths = _write_runs(tmp_path)
    with pytest.raises(SystemExit, match="exactly 4"):
        dev_tuning.verify_dev_run_manifests(paths[:3])
    with pytest.raises(SystemExit, match="unique"):
        dev_tuning.verify_dev_run_manifests([paths[0], paths[0], paths[2], paths[3]])


def test_validate_dev_run_records_rejects_junk_and_shallow_records():
    good = [{"manifest": f"run{i}/manifest.json", "sha256": str(i) * 64, "dataset": d, "trend_window_days": w,
             "v2_digest": DEV_RUNS_V2_DIGEST, "stars_file_sha256": registered_list(REG, name)[0],
             "completed": registered_list(REG, name)[1]} for i, ((d, w), name) in enumerate(DEV_RUN_SCHEDULE.items())]
    assert validate_dev_run_records(good, REG) == good
    for bad, message in (("junk", "list of exactly 4"), (good[:3], "exactly 4"), (good[:1] * 4, "unique"),
                         ([{**good[0], "sha256": "zz"}, *good[1:]], "SHA-256"),
                         ([{**r, "sha256": good[0]["sha256"]} for r in good], "distinct"),
                         ([{**r, "manifest": good[0]["manifest"]} for r in good], "distinct"),
                         ([{**good[0], "manifest": ""}, *good[1:]], "not a path"),
                         ([{**good[0], "manifest": 7}, *good[1:]], "not a path"),
                         ([{**good[0], "v2_digest": v2_digest()}, *good[1:]], "dev-run digest"),
                         ([{**good[0], "completed": 1}, *good[1:]], "completion"),
                         ([{k: v for k, v in good[0].items() if k != "stars_file_sha256"}, *good[1:]], "carry")):
        with pytest.raises(SystemExit, match=message):
            validate_dev_run_records(bad, REG)


def test_rescore_provenance_is_matched_to_its_own_run_one_to_one(tmp_path):
    records = dev_tuning.verify_dev_run_manifests(_write_runs(tmp_path))
    tables = []
    for i, record in enumerate(records):
        table = tmp_path / f"rescore_{i}.csv"
        table.write_text(f"combination,sid\nW30_N12_phi0.15_r0.3-1.5,{i}\n")
        _sidecar(table, record)
        tables.append(table)
    dev_tuning.verify_rescore_provenance(tables, records)
    _sidecar(tables[0], records[0], dataset=records[1]["dataset"], trend_window_days=records[1]["trend_window_days"])
    with pytest.raises(SystemExit, match="dataset / trend window"):
        dev_tuning.verify_rescore_provenance(tables, records)
    _sidecar(tables[0], records[0], stars_file_sha256="0" * 64)
    with pytest.raises(SystemExit, match="registered-list"):
        dev_tuning.verify_rescore_provenance(tables, records)
    _sidecar(tables[0], records[1])                       # two tables claim the same run
    with pytest.raises(SystemExit, match="already claimed"):
        dev_tuning.verify_rescore_provenance(tables, records)
    _sidecar(tables[0], records[0], rescore_v2_digest=DEV_RUNS_V2_DIGEST)
    with pytest.raises(SystemExit, match="this checkout"):
        dev_tuning.verify_rescore_provenance(tables, records)
    _sidecar(tables[0], records[0], run_manifest_sha256="0" * 64)
    with pytest.raises(SystemExit, match="verified dev runs"):
        dev_tuning.verify_rescore_provenance(tables, records)
    _sidecar(tables[0], records[0])
    with pytest.raises(SystemExit, match="one-to-one"):
        dev_tuning.verify_rescore_provenance(tables[:3], records)


@pytest.mark.skipif(not PY.exists(), reason="repo venv not present")
def test_authentic_runner_manifest_is_verified_by_the_same_record_check(tmp_path, monkeypatch):
    """A real registered DEV run (the runner itself, one synthetic star) yields a
    manifest that dev_run_record rejects for its digest alone — and accepts,
    with completion 1/1 on the registered list, once the digest is the dev one."""
    sid, other = "9000000000000000003", "9000000000000000009"
    reg = tmp_path / "reg"
    reg.mkdir()
    pd.DataFrame({"dataset": ["d3", "d3"], "sid": [sid, other], "key": ["", ""], "group": ["dsct_flag1"] * 2,
                  "scenario": ["", ""], "split": ["dev", "dev"]}).to_csv(reg / "split.csv", index=False)
    (reg / "d3_dev.txt").write_text(sid + "\n")
    (reg / "d2_dev.txt").write_text(other + "\n")
    shards = tmp_path / "shards"
    write_shard(synthetic_star(sid, seed=11), shards / f"{sid}.csv.gz")
    (shards / "shard_index.txt").write_text(sid + "\n")
    out = tmp_path / "dev_run"
    env = dict(os.environ, V2_REGISTRATION_ROOT=str(reg))
    res = subprocess.run([str(PY), str(RUNNER), "--shard-dir", str(shards), "--shard-index",
                          str(shards / "shard_index.txt"), "--out-dir", str(out), "--work-root",
                          str(tmp_path / "work"), "--dataset", "d3-kepler-dsct", "--machine", "test",
                          "--workers", "1", "--stars-file", str(reg / "d3_dev.txt"),
                          "--split-file", str(reg / "split.csv")],
                         capture_output=True, text=True, cwd=ROOT, env=env)
    assert res.returncode == 0, res.stdout + res.stderr
    manifest = out / "manifest.json"
    m = json.loads(manifest.read_text())
    assert (m["source_count"], m["pending_at_start"], m["completed_now"]) == (1, 1, 1) and not m["failures"]
    with pytest.raises(SystemExit, match="dev-run digest"):
        dev_run_record(manifest, reg)
    monkeypatch.setattr(v2_common, "DEV_RUNS_V2_DIGEST", m["binding"]["v2_digest"])
    record = dev_run_record(manifest, reg)
    assert record["completed"] == 1 and record["stars_file_sha256"] == _sha(reg / "d3_dev.txt")
    assert record["dataset"] == "d3-kepler-dsct" and record["trend_window_days"] == 30.0
    others = [{**record, "dataset": d, "trend_window_days": w, "manifest": f"other{i}/manifest.json",
               "sha256": str(i) * 64, "stars_file_sha256": registered_list(reg, n)[0],
               "completed": registered_list(reg, n)[1]}
              for i, ((d, w), n) in enumerate(DEV_RUN_SCHEDULE.items()) if (d, w) != ("d3-kepler-dsct", 30.0)]
    validate_dev_run_records([record, *others], reg)
    with pytest.raises(SystemExit, match="distinct"):          # the same manifest identity four times
        validate_dev_run_records([record, *[{**o, "manifest": record["manifest"], "sha256": record["sha256"]}
                                            for o in others]], reg)


def test_amendment_commit_descends_from_the_preregistration_commit():
    if subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, capture_output=True).returncode != 0:
        pytest.skip("not a git checkout")
    amendment = dev_tuning.verify_commit(VETO_AMENDMENT_COMMIT)      # ancestor of HEAD
    prereg = dev_tuning.verify_commit("5ceb019")
    assert subprocess.run(["git", "merge-base", "--is-ancestor", prereg, amendment], cwd=ROOT).returncode == 0
