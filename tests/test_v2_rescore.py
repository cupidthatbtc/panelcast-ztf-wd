"""rescore_v2: the offline re-score at the run's own constants reproduces the
run's decisions exactly, and the tunable gates change decisions as declared."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v2"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_star_v2 import analyze_star_v2  # noqa: E402
from rescore_v2 import combination_id, combinations, rescore_star  # noqa: E402
from v2_common import DEFAULT, TUNABLE, overall_result  # noqa: E402
from v2_helpers import synthetic_star, write_shard  # noqa: E402


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    root = tmp_path_factory.mktemp("rescore")
    out = {}
    for sid, kwargs in (("9000000000000000011", {}),                                  # coherent
                        ("9000000000000000012", {"phase_r_cycles": 0.12}),            # marginal phase
                        ("9000000000000000013", {"amp_r_mmag": 3.0, "amp_g_mmag": 30.0})):  # ratio 0.1
        shard = write_shard(synthetic_star(sid, **kwargs), root / "shards" / f"{sid}.csv.gz")
        path = root / "stars" / f"{sid}.json"
        analyze_star_v2(sid, str(shard), str(path), str(root / "work"), ("low", "high"))
        out[sid] = json.loads(path.read_text())
    return out


def test_combinations_cover_the_declared_sets():
    ids = [c for c, _ in combinations()]
    assert len(ids) == len(set(ids)) == 27
    assert combination_id(DEFAULT) in ids
    assert all(f"N{n}_" in "".join(ids) for n in TUNABLE["n_window_peaks"])


def test_default_rescore_reproduces_the_run(results):
    for result in results.values():
        row = rescore_star(result, DEFAULT)
        overall = overall_result(result)
        assert row["best_status"] == overall["blind_status"]
        assert row["best_pass"] == overall["best_pass"]
        assert row["best_frequency_per_day"] == overall["best_frequency_per_day"]
        for name in ("low", "high"):
            assert row[f"{name}_status"] == result["passes"][name]["status"]
            assert row[f"{name}_frequency_per_day"] == result["passes"][name]["frequency_per_day"]


def test_gates_change_decisions_as_declared(results):
    from dataclasses import replace

    coherent = results["9000000000000000011"]
    assert overall_result(coherent)["blind_status"] == "confirmed"
    marginal = results["9000000000000000012"]     # delta phase ~0.12 cycle
    low = marginal["passes"]["low"]["v2"]
    assert 0.10 < low["delta_phase_cycles"] < 0.15
    assert marginal["passes"]["low"]["status"] == "confirmed"
    strict = rescore_star(marginal, replace(DEFAULT, phase_tolerance_cycles=0.10))
    assert strict["low_status"] == "candidate"
    loose = rescore_star(marginal, replace(DEFAULT, phase_tolerance_cycles=0.25))
    assert loose["low_status"] == "confirmed"
    ratio = results["9000000000000000013"]         # A_r / A_g = 0.1
    assert ratio["passes"]["low"]["status"] == "candidate"
    wide = rescore_star(ratio, replace(DEFAULT, amp_ratio_min=0.2, amp_ratio_max=2.0))
    assert wide["low_status"] == "candidate"        # 0.1 is below every declared minimum
