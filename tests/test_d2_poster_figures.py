"""D2 poster figures F5-F7: pilot guard, watermark, manifest traceability,
frozen edges — exercised on the archived gen2 pilot bundle's real schema."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "generalization" / "figures"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))

import d2_poster_figures as figs  # noqa: E402

PILOT = ROOT / "generalization" / "results" / "2026-08-30_d2_pilot_gen2"


def test_pilot_bundle_is_refused_without_the_flag(tmp_path):
    with pytest.raises(SystemExit, match="pilot numbers are never figures"):
        figs.render(PILOT, tmp_path / "out")
    assert not (tmp_path / "out" / "figures.manifest.json").exists()


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    out = tmp_path_factory.mktemp("d2figs")
    manifest = figs.render(PILOT, out, allow_pilot=True)
    return out, manifest


def test_schema_test_render_is_watermarked(rendered):
    out, manifest = rendered
    for name in ("f5_recovery_surface", "f6_sensitivity", "f7_nulls_controls"):
        assert (out / f"{name}.png").exists() and (out / f"{name}.pdf").exists()
    assert manifest["pilot"] is True and manifest["watermark"] == figs.WATERMARK
    assert figs.WATERMARK in (out / "captions.md").read_text()
    assert json.loads((out / "figures.manifest.json").read_text())["watermark"] == figs.WATERMARK


def test_frozen_edges(rendered):
    from d2_truth_model import WG_SURFACE_EDGES
    from metrics_generalization import AMP_EDGES

    _, manifest = rendered
    assert manifest["frozen_edges"]["wg"] == list(WG_SURFACE_EDGES) == [15, 41, 84, 217]
    assert manifest["frozen_edges"]["amp_ppt"] == list(AMP_EDGES["d2"]) == [0.5, 2, 5, 10, 30]
    assert len(figs.WG_LABELS) == len(WG_SURFACE_EDGES) + 1
    assert len(figs.AMP_LABELS) == len(AMP_EDGES["d2"]) + 1


def test_manifest_numbers_equal_the_bundle_files(rendered):
    _, manifest = rendered
    m = PILOT / "metrics"
    # F5 surface cells
    surface = pd.read_csv(m / "surfaces/recovery_wg_amplitude.csv")
    cells = manifest["figures"]["F5"]["numbers"]["cells"]
    assert len(cells) == len(surface)
    for _, row in surface.iterrows():
        cell = cells[f"wg{int(row['wg_bin'])}_amp{int(row['amp_bin'])}"]
        assert (cell["n_windows"], cell["k_windows"], cell["n_targets"]) == \
            (int(row["n_windows"]), int(row["k_windows"]), int(row["n_targets"]))
        assert "p" not in cell or cell["n_targets"] >= 5
    # F5 P4 rows
    cluster = pd.read_csv(m / "d2_cluster_completeness.csv")
    for denom in ("eligible", "usable"):
        row = cluster[(cluster["arm"] == "B") & (cluster["scenario"] == "nominal")
                      & (cluster["endpoint"] == "recovery") & (cluster["denominator"] == denom)].iloc[0]
        p4 = manifest["figures"]["F5"]["numbers"]["p4"][denom]
        assert p4["p"] == pytest.approx(row["p"]) and p4["lo"] == pytest.approx(row["lo"]) \
            and p4["hi"] == pytest.approx(row["hi"]) and p4["n_targets"] == int(row["n_targets"])
    # F5 strata are target means over nominal-B windows of per_star
    per_star = pd.read_csv(m / "per_star.csv", dtype={"sid": str, "cluster": str})
    b = per_star[(per_star["arm"] == "B") & (per_star["scenario"] == "nominal")]
    for k in (0, 1, 2):
        rows = b[b["template_k"] == k]
        rec = ((rows["best_status"] == "confirmed") & (rows["best_candidate_matches_dominant"] == "direct"))
        expected = rec.astype(float).groupby(rows["cluster"]).mean().mean()
        assert manifest["figures"]["F5"]["numbers"]["strata"][f"K{k}"]["p"] == pytest.approx(expected)
    # F6 contrasts
    contrasts = pd.read_csv(m / "d2_scenario_contrasts.csv")
    sel = contrasts[(contrasts["endpoint"] == "recovery") & (contrasts["denominator"] == "eligible")]
    f6 = manifest["figures"]["F6"]["numbers"]
    for _, row in sel.iterrows():
        entry = f6[row["scenario"]]
        assert entry["diff"] == pytest.approx(row["diff"]) and entry["diff_lo"] == pytest.approx(row["diff_lo"])
        assert entry["diff_hi"] == pytest.approx(row["diff_hi"]) and entry["interval"] == row["interval"]
        assert entry["n_targets_matched"] == int(row["n_targets_matched"])
    assert set(f6) - {"_range"} == set(sel["scenario"])
    # F7 nulls, paired controls, native rate, reuse
    trig = pd.read_csv(m / "trigger_rates.csv")
    fpr = trig[trig["quantity"] == "fpr_gaussian"].iloc[0]
    f7 = manifest["figures"]["F7"]["numbers"]
    assert f7["fpr_gaussian"]["k"] == int(fpr["k"]) and f7["fpr_gaussian"]["n_completed"] == int(fpr["n_completed"])
    assert f7["fpr_gaussian"]["cp_one_sided_95_upper"] == pytest.approx(fpr["cp_one_sided_95_upper"])
    assert f7["fpr_gaussian"]["n_completed_is_1000"] is False
    paired = pd.read_csv(m / "d2_paired_controls_summary.csv")
    for endpoint in ("D", "R"):
        row = paired[paired["endpoint"] == endpoint].iloc[0]
        got = f7[f"paired_{endpoint}"]
        for key in ("both", "b_only", "c_only", "neither", "union", "n_pairs_scored", "n_targets"):
            assert got[key] == int(row[key])
        assert got["p_b_and_not_c"] == pytest.approx(row["p_b_and_not_c"])
    native = trig[trig["quantity"] == "native_trigger_rate"].iloc[0]
    assert f7["native_trigger_rate"]["p"] == pytest.approx(native["p"]) and f7["native_trigger_rate"]["n"] == int(native["n"])
    reuse = pd.read_csv(m / "d2_control_reuse.csv")
    assert f7["reuse"]["n_control_windows"] == len(reuse)
    assert f7["reuse"]["n_b_assignments_total"] == int(reuse["n_b_assignments"].sum())
    assert not any(math.isnan(v) for v in (f7["fpr_gaussian"]["p"], f7["native_trigger_rate"]["p"]))


def test_input_shas_bind_the_bundle(rendered):
    _, manifest = rendered
    for rel, sha in manifest["inputs_sha256"].items():
        assert sha == figs.sha256_file(PILOT / rel)
    assert "metrics/manifest.json" in manifest["inputs_sha256"]
