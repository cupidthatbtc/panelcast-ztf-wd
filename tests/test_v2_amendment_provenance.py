"""V2_PLAN.md §10 (2026-09-04, round-7 revision): the re-scored dev runs are
bound fail-closed — rescore_v2 refuses a non-dev-digest source and writes a
provenance sidecar; dev_tuning verifies the four dev-run manifests and the
sidecars; the compiled amendment constants are the reference."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))

import dev_tuning  # noqa: E402
import rescore_v2  # noqa: E402
from v2_common import DEV_RUNS_V2_DIGEST, VETO_AMENDMENT_COMMIT, v2_digest  # noqa: E402

REG = ROOT / "generalization" / "v2"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _list_len(name: str) -> int:
    return len([line for line in (REG / name).read_text().splitlines() if line.strip()])


def _manifest(dataset: str, window: float, **override) -> dict:
    list_name = "d3_dev.txt" if dataset.startswith("d3") else "d2_dev.txt"
    n = _list_len(list_name)
    base = {"engine": "v2", "dataset": dataset, "constants": {"trend_window_days": window},
            "split": {"half": "dev"}, "failures": [], "total": n, "pending_at_start": n, "completed_now": n,
            "binding": {"v2_digest": DEV_RUNS_V2_DIGEST, "stars_file_sha256": _sha(REG / list_name)}}
    base.update(override)
    return base


def _write_runs(root: Path, **override) -> list[Path]:
    paths = []
    for dataset, window in (("d3-kepler-dsct", 30.0), ("d3-kepler-dsct", 10.0),
                            ("d2-tess-dav", 30.0), ("d2-tess-dav", 10.0)):
        run = root / f"{dataset[:2]}_w{window:g}"
        (run / "stars").mkdir(parents=True)
        (run / "manifest.json").write_text(json.dumps(_manifest(dataset, window, **override)))
        paths.append(run / "manifest.json")
    return paths


def test_constants_name_the_admitted_dev_digest_and_the_amendment_commit():
    assert DEV_RUNS_V2_DIGEST.startswith("ecc5df75d8f225cb") and len(DEV_RUNS_V2_DIGEST) == 64
    assert VETO_AMENDMENT_COMMIT.startswith("017c925e") and len(VETO_AMENDMENT_COMMIT) == 40
    assert v2_digest() != DEV_RUNS_V2_DIGEST   # the amendment moved the code digest


def test_rescore_refuses_a_source_that_is_not_a_dev_run_at_the_dev_digest(tmp_path):
    run = tmp_path / "run"
    (run / "stars").mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0,
                                                            binding={"v2_digest": v2_digest()})))
    with pytest.raises(SystemExit, match="dev-run digest"):
        rescore_v2.verify_run_manifest(run / "manifest.json", run / "stars")
    (run / "manifest.json").write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0, split={"half": "holdout"})))
    with pytest.raises(SystemExit, match="not dev"):
        rescore_v2.verify_run_manifest(run / "manifest.json", run / "stars")
    (run / "manifest.json").write_text(json.dumps(_manifest("d3-kepler-dsct", 30.0)))
    with pytest.raises(SystemExit, match="own stars directory"):
        rescore_v2.verify_run_manifest(run / "manifest.json", tmp_path / "elsewhere")
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
    assert prov["run_manifest_sha256"] == _sha(run / "manifest.json")
    assert prov["source_v2_digest"] == DEV_RUNS_V2_DIGEST and prov["rescore_v2_digest"] == v2_digest()
    assert prov["trend_window_days"] == 10.0 and prov["n_combinations"] == 27
    assert prov["rescore_csv_sha256"] == _sha(out)


def test_dev_tuning_accepts_exactly_the_registered_schedule(tmp_path):
    records = dev_tuning.verify_dev_run_manifests(_write_runs(tmp_path))
    assert len(records) == 4 and {r["dataset"] for r in records} == {"d3-kepler-dsct", "d2-tess-dav"}
    assert all(r["v2_digest"] == DEV_RUNS_V2_DIGEST for r in records)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"binding": {"v2_digest": "0" * 64, "stars_file_sha256": "x"}}, "dev-run digest"),
        ({"split": {"half": "holdout"}}, "not dev"),
        ({"failures": ["9000000000000000001"]}, "failures"),
        ({"completed_now": 3}, "completion"),
        ({"constants": {"trend_window_days": 20.0}}, "schedule"),
    ],
)
def test_dev_tuning_rejects_a_bad_dev_run_manifest(tmp_path, override, message):
    paths = _write_runs(tmp_path)
    bad = json.loads(paths[0].read_text())
    bad.update(override)
    paths[0].write_text(json.dumps(bad))
    with pytest.raises(SystemExit, match=message):
        dev_tuning.verify_dev_run_manifests(paths)


def test_dev_tuning_rejects_a_missing_schedule_entry_and_bad_sidecars(tmp_path):
    paths = _write_runs(tmp_path)
    with pytest.raises(SystemExit, match="schedule"):
        dev_tuning.verify_dev_run_manifests(paths[:3])
    records = dev_tuning.verify_dev_run_manifests(paths)
    table = tmp_path / "rescore_d3_dev_w30.csv"
    table.write_text("combination,sid\n")
    with pytest.raises(SystemExit, match="provenance"):
        dev_tuning.verify_rescore_provenance([table], records)
    sidecar = tmp_path / "rescore_d3_dev_w30.csv.provenance.json"
    good = {"run_manifest_sha256": records[0]["sha256"], "source_v2_digest": DEV_RUNS_V2_DIGEST,
            "rescore_v2_digest": v2_digest(), "rescore_csv_sha256": _sha(table)}
    sidecar.write_text(json.dumps(good))
    dev_tuning.verify_rescore_provenance([table], records)
    sidecar.write_text(json.dumps({**good, "rescore_v2_digest": DEV_RUNS_V2_DIGEST}))
    with pytest.raises(SystemExit, match="this checkout"):
        dev_tuning.verify_rescore_provenance([table], records)
    sidecar.write_text(json.dumps({**good, "run_manifest_sha256": "0" * 64}))
    with pytest.raises(SystemExit, match="verified dev runs"):
        dev_tuning.verify_rescore_provenance([table], records)


def test_amendment_commit_descends_from_the_preregistration_commit():
    if subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, capture_output=True).returncode != 0:
        pytest.skip("not a git checkout")
    amendment = dev_tuning.verify_commit(VETO_AMENDMENT_COMMIT)      # ancestor of HEAD
    prereg = dev_tuning.verify_commit("5ceb019")
    assert subprocess.run(["git", "merge-base", "--is-ancestor", prereg, amendment], cwd=ROOT).returncode == 0
