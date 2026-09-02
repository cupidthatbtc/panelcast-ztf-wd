"""analyze_star_v2: frozen-schema compatibility, frozen consumers, determinism,
error path — on a synthetic two-band shard with a coherent 12.3 c/d signal."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_star_v2 import analyze_star_v2  # noqa: E402
from metrics_generalization import score_star  # noqa: E402
from v2_common import SCHEMA_VERSION, grid_for, overall_result, unavailable_pass_result  # noqa: E402
from v2_helpers import synthetic_star, write_shard  # noqa: E402

FROZEN_PASS_KEYS = set(unavailable_pass_result(grid_for("low", 100.0), "x"))
FROZEN_PEAK_KEYS = {
    "source_id", "pass", "series", "rank", "frequency_per_day", "period_days", "period_seconds",
    "power", "baluev_fap_blind_grid", "amplitude_mmag", "amplitude_error_mmag", "window_power",
    "window_alias", "stronger_peak_sidereal_alias", "alias_flag",
}
SID = "9000000000000000001"


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    root = tmp_path_factory.mktemp("schema")
    shard = write_shard(synthetic_star(SID), root / "shards" / f"{SID}.csv.gz")
    out = root / "stars" / f"{SID}.json"
    analyze_star_v2(SID, str(shard), str(out), str(root / "work"), ("low", "high"))
    return json.loads(out.read_text()), out, shard, root


def test_top_level_schema(result):
    r, *_ = result
    assert r["schema_version"] == SCHEMA_VERSION and r["engine"] == "v2"
    assert r["complete"] is True and set(r["passes"]) == {"low", "high"}
    assert r["source_id"] == SID and r["n_exp_zg"] > 0 and r["n_exp_zr"] > 0
    assert r["baseline_days"] > 100
    assert {"constants", "alignment", "time_origin_bjd_tdb", "n_oids"} <= set(r["v2"])
    assert r["v2"]["n_oids"] == {"zg": 2, "zr": 2}


def test_pass_keys_superset_of_frozen(result):
    r, *_ = result
    for name in ("low", "high"):
        p = r["passes"][name]
        assert FROZEN_PASS_KEYS <= set(p), FROZEN_PASS_KEYS - set(p)
        assert p["available"] is True and p["grid_size"] > 0
        assert isinstance(p["v2"]["candidates"], list) and p["v2"]["n_candidates"] >= 1


def test_top_peaks_frozen_shape(result):
    r, *_ = result
    for name in ("low", "high"):
        rows = r["passes"][name]["top_peaks"]
        assert len(rows) == 15
        for series in ("zg", "zr", "multiband"):
            ranks = [row["rank"] for row in rows if row["series"] == series]
            assert ranks == [1, 2, 3, 4, 5]
        for row in rows:
            assert FROZEN_PEAK_KEYS <= set(row)


def test_frozen_consumers_accept_v2_json(result):
    r, out, *_ = result
    overall = overall_result(r)
    assert overall["blind_status"] == "confirmed" and overall["best_pass"] == "low"
    assert abs(overall["best_frequency_per_day"] - 12.3) < 1.5 / r["baseline_days"]
    assert overall["basis"].startswith("coherent+")
    scored = score_star(out, [12.3], 12.3)
    assert scored["best_status"] == "confirmed"
    assert scored["best_candidate_matches_dominant"] == "direct"
    assert scored["any_top_peak_matches_any_mode"] is True


def test_alignment_recovers_the_injected_offset(result):
    r, *_ = result
    aligned = [row for row in r["v2"]["alignment"] if row["applied"]]
    assert len(aligned) == 2
    for row in aligned:
        # the two oids sample the 30-mmag sinusoid at different times within a
        # night, so the per-night differences carry +/- 60 mmag of signal; the
        # weighted median over ~60 shared nights recovers the 15-mmag step to
        # a few mmag (precision is pinned in test_v2_align.py)
        assert abs(abs(row["offset_mmag"]) - 15.0) < 8.0
        assert row["role"] == "aligned" and row["n_shared_nights"] >= 5


def test_determinism_byte_identical(result):
    r, out, shard, root = result
    again = root / "stars2" / f"{SID}.json"
    analyze_star_v2(SID, str(shard), str(again), str(root / "work2"), ("low", "high"))
    assert again.read_bytes() == out.read_bytes()


def test_single_band_shard_is_rejected_before_analysis(tmp_path):
    """Frozen semantics: a shard without both bands raises at load time and
    writes nothing (the frozen load_star does the same)."""
    frame = synthetic_star(SID)
    shard = write_shard(frame[frame["band"] == "zg"], tmp_path / "bad.csv.gz")
    out = tmp_path / "stars" / f"{SID}.json"
    with pytest.raises(ValueError):
        analyze_star_v2(SID, str(shard), str(out), str(tmp_path / "work"), ("low",))
    assert not out.exists()


def test_analysis_failure_writes_error_json(tmp_path, monkeypatch):
    import analyze_star_v2 as module

    def boom(*args, **kwargs):
        raise RuntimeError("synthetic failure inside the pass loop")

    monkeypatch.setattr(module, "grid_for", boom)
    shard = write_shard(synthetic_star(SID), tmp_path / f"{SID}.csv.gz")
    out = tmp_path / "stars" / f"{SID}.json"
    with pytest.raises(RuntimeError):
        analyze_star_v2(SID, str(shard), str(out), str(tmp_path / "work"), ("low",))
    error = tmp_path / "stars" / f"{SID}.error.json"
    assert error.exists() and not out.exists()
    assert "synthetic failure" in json.loads(error.read_text())["error"]
