"""D3 poster figures F1-F4 (scripts/generalization/figures/d3_poster_figures.py).

Runs the module on the COMMITTED frozen D3 bundle (real numbers, not a
synthetic fixture — the bundle is small and static) and checks: all four
figure files (PNG + PDF) exist, the manifest's numbers equal the bundle's own
files, and the amp_unknown bin (154 stars) is present in F1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generalization" / "figures" / "d3_poster_figures.py"
BUNDLE = ROOT / "generalization" / "results" / "2026-09-02_d3"
PY = ROOT / ".venv-gen" / "bin" / "python"


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    out = tmp_path_factory.mktemp("d3_figures")
    python = str(PY) if PY.exists() else sys.executable
    result = subprocess.run([python, str(SCRIPT), "--bundle", str(BUNDLE), "--out-dir", str(out)],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((out / "figures.manifest.json").read_text())
    return out, manifest


@pytest.mark.skipif(not BUNDLE.exists(), reason="frozen D3 bundle not present on this machine")
@pytest.mark.skipif(not (PY.exists() or True), reason="no python available")
def test_all_four_figures_render(rendered):
    out, _ = rendered
    for stem in ("f1_turn_on", "f2_rules_scopes", "f3_negatives", "f4_complementarity"):
        for ext in ("png", "pdf"):
            path = out / f"{stem}.{ext}"
            assert path.exists() and path.stat().st_size > 1000, path
    assert (out / "captions.md").exists()
    assert (out / "figures.manifest.json").exists()


@pytest.mark.skipif(not BUNDLE.exists(), reason="frozen D3 bundle not present on this machine")
def test_f1_amp_unknown_bin_present(rendered):
    _, manifest = rendered
    detection = pd.read_csv(BUNDLE / "metrics/surfaces/detection_amplitude.csv").set_index("amp_bin")
    unknown_row = detection.loc[-1]
    numbers = manifest["figures"]["F1"]["numbers"]["detection"]["unknown"]
    assert numbers["n"] == int(unknown_row["n"]) == 154
    assert numbers["k"] == int(unknown_row["k"])
    assert numbers["p"] == pytest.approx(unknown_row["p"])


@pytest.mark.skipif(not BUNDLE.exists(), reason="frozen D3 bundle not present on this machine")
def test_manifest_numbers_match_bundle_files(rendered):
    _, manifest = rendered
    completeness = pd.read_csv(BUNDLE / "metrics/completeness_by_class_pass_rule.csv")
    best = completeness[completeness["pass"] == "best"]

    p1 = best[(best["rule"] == "confirmed") & (best["scope"] == "detection_eligible_roster")].iloc[0]
    f2 = manifest["figures"]["F2"]["numbers"]["confirmed__detection_eligible_roster"]
    assert f2["n"] == int(p1["n"]) and f2["p"] == pytest.approx(p1["p"])
    assert f2["primary"] == "P1"

    p2 = best[(best["rule"] == "confirmed") & (best["scope"] == "freq_recovery_scorable")].iloc[0]
    f2b = manifest["figures"]["F2"]["numbers"]["confirmed__freq_recovery_scorable"]
    assert f2b["n"] == int(p2["n"]) and f2b["p"] == pytest.approx(p2["p"])
    assert f2b["primary"] == "P2"

    trigger = pd.read_csv(BUNDLE / "metrics/trigger_rates.csv")
    p3 = trigger[(trigger["quantity"] == "negative_class_trigger_rate")
                & (trigger["rule"] == "confirmed")].iloc[0]
    f3 = manifest["figures"]["F3"]["numbers"]["trigger_rate"]["confirmed"]
    assert f3["n"] == int(p3["n"]) and f3["p"] == pytest.approx(p3["p"])

    contingency = json.loads((BUNDLE / "metrics/contingency_complementarity.json").read_text())
    f4 = manifest["figures"]["F4"]["numbers"]
    assert f4["table"] == contingency["table"]
    assert f4["mcnemar_exact_p_secondary"] == pytest.approx(contingency["mcnemar_exact_p_secondary"])

    decomposition = pd.read_csv(BUNDLE / "descriptive_postlaunch/d3_trigger_decomposition.csv")
    within = decomposition[decomposition["component"] == "within_solar_diurnal_band"].iloc[0]
    f3d = manifest["figures"]["F3"]["numbers"]["decomposition"]["within_solar_diurnal_band"]
    assert f3d["n"] == int(within["n_component"])
    assert f3d["rate_of_all_negatives"] == pytest.approx(within["rate_of_all_negatives"])


@pytest.mark.skipif(not BUNDLE.exists(), reason="frozen D3 bundle not present on this machine")
def test_manifest_binds_input_shas_and_disclosure(rendered):
    _, manifest = rendered
    assert set(manifest["inputs_sha256"]) >= {
        "metrics/surfaces/detection_amplitude.csv",
        "metrics/completeness_by_class_pass_rule.csv",
        "metrics/trigger_rates.csv",
        "descriptive_postlaunch/d3_trigger_decomposition.csv",
        "descriptive_postlaunch/README.md",
    }
    assert "does not establish that an individual band member is instrumental" in \
        manifest["disclosure_sentence_f3"]
    assert manifest["disclosure_sentence_f3"] in manifest["captions"]["F3"]
