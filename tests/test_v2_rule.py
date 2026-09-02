"""v2 decision rule truth table (rule.decide)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "v2"))

from rule import decide  # noqa: E402
from v2_common import DEFAULT  # noqa: E402


def _row(zg_fap=1.0, zr_fap=1.0, zg_alias=False, zr_alias=False, joint_top5=True, coherent=True):
    return {"zg_fap": zg_fap, "zr_fap": zr_fap, "zg_alias": zg_alias, "zr_alias": zr_alias,
            "joint_top5": joint_top5, "coherent": coherent}


def test_no_significant_band_is_not_detected():
    assert decide(_row(), DEFAULT) == ("not_detected", "", "no_unaliased_significant_band")


def test_one_band_joint_and_coherent_is_confirmed():
    status, basis, reason = decide(_row(zg_fap=1e-5), DEFAULT)
    assert (status, basis, reason) == ("confirmed", "coherent+zg", "")
    assert decide(_row(zr_fap=1e-5), DEFAULT)[:2] == ("confirmed", "coherent+zr")


def test_two_bands_incoherent_is_candidate():
    assert decide(_row(zg_fap=1e-5, zr_fap=1e-6, coherent=False), DEFAULT) == ("candidate", "zg+zr", "incoherent")


def test_not_joint_top5_is_candidate():
    assert decide(_row(zg_fap=1e-5, joint_top5=False), DEFAULT) == ("candidate", "zg", "not_joint_top5")
    assert decide(_row(zg_fap=1e-5, joint_top5=False, coherent=False), DEFAULT)[2] == "not_joint_top5+incoherent"


def test_aliased_band_never_counts():
    assert decide(_row(zg_fap=1e-9, zg_alias=True), DEFAULT)[0] == "not_detected"
    assert decide(_row(zg_fap=1e-9, zg_alias=True, zr_fap=1e-4), DEFAULT)[:2] == ("confirmed", "coherent+zr")


def test_threshold_is_strict():
    assert decide(_row(zg_fap=1e-3), DEFAULT)[0] == "not_detected"
    assert decide(_row(zg_fap=0.999e-3), DEFAULT)[0] == "confirmed"
