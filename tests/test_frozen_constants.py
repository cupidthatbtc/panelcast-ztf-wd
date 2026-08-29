"""Pin the frozen pipeline's constants and its known, provably-benign quirks.

These tests do not fix anything (the pipeline is frozen); they make silent
drift impossible. If any test here fails, the frozen premise of the
generalization campaign is broken and every campaign result is void.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))

import frozen_api  # noqa: E402


def test_frozen_shas_match_tag():
    assert frozen_api.assert_frozen() == frozen_api.FROZEN_SHA256


def test_pass_bounds_canonical():
    assert frozen_api.PASS_BOUNDS == {"low": (None, 48.0), "high": (24.0, 1440.0)}


def test_pass_bounds_duplicates_agree():
    """The bootstrap scripts re-derive the pass bounds as bare literals instead
    of importing PASS_BOUNDS. Frozen policy: no refactor; this AST scan asserts
    every float literal 24.0/48.0/1440.0 in those files matches the canonical
    bounds, so the duplication cannot drift."""
    canonical = {24.0, 48.0, 1440.0}
    for name in (
        "run_bootstrap_fap.py",
        "run_catalog_bootstrap.py",
        "run_catalog_stratified_bootstrap.py",
    ):
        tree = ast.parse((REPO_ROOT / "scripts" / name).read_text(encoding="utf-8"))
        found = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, float)
            and node.value in canonical
        }
        assert found == canonical, f"{name}: pass-bound literals {found} != {canonical}"


def test_census_threshold_is_geq_2p5():
    """census_row uses >= 2.5 on all six ratios. The frozen code base also
    contains a > 2.5 comparison elsewhere; that inconsistency is provably
    non-affecting (0 of 5,568 published ratios are within 1e-4 of 2.5) and is
    NOT fixed. Campaign metrics use >= and assert no campaign ratio equals 2.5
    exactly (metrics_generalization.py)."""
    source = (REPO_ROOT / "scripts" / "build_catalog_panels.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    census = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "census_row"
    )
    comparisons = [
        type(node.ops[0]).__name__
        for node in ast.walk(census)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(comp, ast.Constant) and comp.value == 2.5
            for comp in node.comparators
        )
    ]
    assert comparisons and set(comparisons) == {"GtE"}, comparisons


def test_grid_and_vetting_constants():
    assert frozen_api.SAMPLES_PER_PEAK == 10
    assert frozen_api.WINDOW_POWER_THRESHOLD == 0.1
    assert abs(frozen_api.SIDEREAL_FREQUENCY - 1.00273790935) < 1e-12
    assert frozen_api.MIN_EXPOSURES_PER_BAND == 20
    assert frozen_api.OID_CLUSTER_ARCSEC == 1.5


def test_fap_detection_threshold_literal():
    source = (REPO_ROOT / "scripts" / "run_lomb_scargle.py").read_text(encoding="utf-8")
    assert "if fap < 1e-3 and not alias:" in source


def test_match_tolerance_convention():
    """The pipeline's own frequency-match tolerance is 1.5 / baseline; the
    campaign metrics spec adopts it verbatim."""
    source = (REPO_ROOT / "scripts" / "run_lomb_scargle.py").read_text(encoding="utf-8")
    assert source.count("1.5 / np.ptp(") >= 3


def test_grid_for_low_and_high():
    low = frozen_api.grid_for("low", 1000.0)
    high = frozen_api.grid_for("high", 1000.0)
    assert low.minimum == 2.0 / 1000.0 and low.maximum == 48.0
    assert high.minimum == 24.0 and high.maximum == 1440.0
    assert low.step == 1.0 / (10 * 1000.0)


def test_campaign_id_convention():
    assert frozen_api.campaign_id_ok("9000000000000757076")
    assert frozen_api.campaign_id_ok("9200000000000123456")
    assert frozen_api.campaign_id_ok("9300000000000123456")
    assert frozen_api.campaign_id_ok("9400000000000000001")
    assert frozen_api.campaign_id_ok("9500000000000000001")
    assert not frozen_api.campaign_id_ok("757076")  # not 19 digits
    assert not frozen_api.campaign_id_ok("9100000000000123456")  # unknown prefix
    assert not frozen_api.campaign_id_ok("1013776353903293056")  # real Gaia id
    # the frozen bootstrap seeds RNGs with int(source_id[-9:]); every campaign
    # id must survive that convention
    assert int("9000000000000757076"[-9:]) == 757076


def test_unavailable_pass_result_shape():
    grid = frozen_api.grid_for("high", 100.0)
    result = frozen_api.unavailable_pass_result(grid, "test")
    assert result["status"] == "not_detected"
    assert result["available"] is False
    assert result["grid_size"] == grid.size
