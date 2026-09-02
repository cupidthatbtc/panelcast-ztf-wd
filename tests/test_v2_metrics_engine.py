"""Engine binding guards for frozen and v2 campaign metrics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import metrics_generalization as metrics
from compare_metrics_runs import compare


def _manifest_path(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _v2_manifest() -> dict:
    return {
        "engine": "v2",
        "machine": "test-machine",
        "binding": {
            "engine": "v2",
            "v2_digest": "v2-digest",
            "frozen_digest": "frozen-digest",
            "constants_sha256": "constants-sha",
            "generation_id": "generation-1",
            "attestation_sha256": "v2-unattested",
        },
        "replay_attestation": {
            "path": "",
            "sha256": "v2-unattested",
            "tier": "v2_unattested",
        },
    }


def test_crossed_engine_manifests_are_refused(tmp_path):
    v2_manifest = _v2_manifest()
    v2_path = _manifest_path(tmp_path, v2_manifest)
    with pytest.raises(SystemExit, match="cannot be scored with --engine frozen"):
        metrics.attestation_record_for("frozen", v2_manifest, v2_path)

    frozen_manifest = {"binding": {}}
    frozen_path = _manifest_path(tmp_path, frozen_manifest)
    with pytest.raises(SystemExit, match="requires a run manifest with engine == 'v2'"):
        metrics.attestation_record_for("v2", frozen_manifest, frozen_path)


def test_v2_attestation_record_and_sidecar_binding(tmp_path):
    manifest = _v2_manifest()
    manifest_path = _manifest_path(tmp_path, manifest)
    record = metrics.attestation_record_for("v2", manifest, manifest_path)

    assert record == {
        "tier": "v2_unattested",
        "path": "",
        "sha256": "v2-unattested",
        "engine": "v2",
        "v2_digest": "v2-digest",
        "constants_sha256": "constants-sha",
        "machine": "test-machine",
        "roster_size": None,
        "f64_max_relative_difference": None,
        "boundary_margin_relative": 1e-9,
        "run_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    assert metrics.sidecar_binding_keys("v2") == (
        "engine", "frozen_digest", "v2_digest", "constants_sha256", "generation_id",
        "machine", "split_sha256", "split_half", "stars_file_sha256",
        "plan_sha256", "preregistration_commit", "constants_artifact_sha256",
    )


def test_frozen_sidecar_binding_keys_are_unchanged():
    assert metrics.sidecar_binding_keys("frozen") == (
        "frozen_digest", "campaign_digest", "generation_id",
    )


def test_compare_allows_only_new_engine_manifest_key(tmp_path):
    reference = tmp_path / "reference"
    candidate = tmp_path / "candidate"
    reference.mkdir()
    candidate.mkdir()
    (reference / "manifest.json").write_text(json.dumps({"dataset": "d3"}), encoding="utf-8")
    (candidate / "manifest.json").write_text(
        json.dumps({"dataset": "d3", "engine": "frozen"}), encoding="utf-8")

    assert compare(reference, candidate) == []


def test_v2_holdout_manifest_requires_canonical_registration(tmp_path):
    """Defense in depth (V2G1 round 3): a v2 holdout run produced under a
    non-canonical registration root is refused by the metrics."""
    import json

    path = tmp_path / "manifest.json"
    base = {"engine": "v2", "machine": "m", "passes": ["low", "high"], "limit": None,
            "holdout_registration": {"lock_file": "x"},
            "binding": {"v2_digest": "d", "constants_sha256": "c", "split_half": "holdout"}}
    path.write_text(json.dumps({**base, "canonical_registration": False}))
    with pytest.raises(SystemExit):
        metrics.attestation_record_for("v2", json.loads(path.read_text()), path)
    path.write_text(json.dumps({**base, "canonical_registration": True}))
    assert metrics.attestation_record_for("v2", json.loads(path.read_text()), path)["tier"] == "v2_unattested"
    dev = {**base, "binding": {**base["binding"], "split_half": "dev"}, "canonical_registration": False}
    path.write_text(json.dumps(dev))
    assert metrics.attestation_record_for("v2", json.loads(path.read_text()), path)["tier"] == "v2_unattested"


def test_v2_holdout_manifest_requires_ordered_passes_and_registration(tmp_path):
    import json

    path = tmp_path / "manifest.json"
    good = {"engine": "v2", "machine": "m", "canonical_registration": True, "passes": ["low", "high"],
            "limit": None, "holdout_registration": {"lock_file": "x"},
            "binding": {"v2_digest": "d", "constants_sha256": "c", "split_half": "holdout"}}
    path.write_text(json.dumps(good))
    assert metrics.attestation_record_for("v2", json.loads(path.read_text()), path)["tier"] == "v2_unattested"
    for bad in ({**good, "passes": ["high", "low"]}, {**good, "passes": ["low"]},
                {**good, "limit": 5}, {**good, "holdout_registration": {}}):
        path.write_text(json.dumps(bad))
        with pytest.raises(SystemExit):
            metrics.attestation_record_for("v2", json.loads(path.read_text()), path)
