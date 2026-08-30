"""Contract tests for the D2 shard generation (G3 round-1 findings).

A miniature pool (4 real-shaped ZTF windows) and 3 synthetic Romero-like
targets run through the REAL builder, then through the REAL metrics readers:
  * fixed typed manifest schema, every arm fully populated (M1/N1)
  * explicit scenario codes; dropout never pooled with nominal (M2/N2)
  * dropout scheduled only for >= 2 retained modes; zero-retained targets excluded
  * campaign-id layout (S=3 dropout code, crowding digit), no collisions (N6)
  * staging + atomic publish, sentinel, generation manifest, SHA identity (M3/M5)
  * bitwise epoch round-trip through the frozen loader (M7)
  * truth_d2 consumes the full default manifest and refuses tampering (M1/M4)
  * cluster bootstrap keeps scenarios apart and uses scheduled strata (M2)
  * stratified pilot index spans every arm (M8)
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization"))

import build_d2_shards as builder  # noqa: E402
from d2_truth_model import (  # noqa: E402
    AMP_SCALE_CODE_DROPOUT,
    MANIFEST_COLUMN_NAMES,
    SCENARIO_NOMINAL,
)
from frozen_api import EXPOSURE_COLUMNS, campaign_id_ok, load_star  # noqa: E402
import metrics_generalization as metrics  # noqa: E402

POOL_IDS = ["1000000000000000001", "1000000000000000002",
            "1000000000000000003", "1000000000000000004"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fake_window(sid: str, seed: int, gmag: float, exp_per_night: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for band, offset in (("zg", 0.0), ("zr", 0.31)):
        for night in range(24):
            for k in range(exp_per_night if night % 2 else 1):
                mjd = 58200.0 + night * 3.3 + k * 0.0123456789 + rng.uniform(0, 0.01)
                rows.append({
                    "source_id": sid, "band": band, "oid": 500000000000000 + seed,
                    "mjd": mjd, "bjd_tdb": mjd + 2400000.5 + 0.0049876543 + offset * 1e-5,
                    "night_mjd": int(mjd), "mag": gmag + offset + rng.normal(0, 0.02),
                    "magerr": 0.015 + rng.uniform(0, 0.01), "chi": 0.93,
                    "ra": 50.2877149, "dec": 14.1822509,
                })
    frame = pd.DataFrame(rows).sort_values(["band", "bjd_tdb"]).reset_index(drop=True)
    return frame[list(EXPOSURE_COLUMNS)]


@pytest.fixture(scope="module")
def generation(tmp_path_factory) -> dict:
    root = tmp_path_factory.mktemp("d2contract")
    stars = root / "exposure_stars"
    stars.mkdir()
    for i, (sid, gmag, epn) in enumerate(zip(POOL_IDS, (16.9, 17.1, 17.4, 18.2), (1, 2, 3, 5))):
        fake_window(sid, i + 1, gmag, epn).to_csv(stars / f"{sid}.csv.gz", index=False)
    catalog = root / "catalog.csv"
    pd.DataFrame({"source_id": POOL_IDS,
                  "blind_status": ["not_detected", "confirmed", "not_detected", "candidate"]}
                 ).to_csv(catalog, index=False)
    d2 = root / "d2"
    d2.mkdir()
    targets = pd.DataFrame([
        {"tic": 11, "paper": "romero2025", "sectors": "f48", "fap_ppt": 5.0, "cadence_s": 20,
         "nov": False, "n_modes": 3, "ra": 1.0, "dec": 2.0, "gmag": 17.0},
        {"tic": 22, "paper": "romero2022", "sectors": "19", "fap_ppt": 5.0, "cadence_s": 120,
         "nov": False, "n_modes": 1, "ra": 1.0, "dec": 2.0, "gmag": 17.3},
        {"tic": 33, "paper": "romero2022", "sectors": "20", "fap_ppt": 5.0, "cadence_s": 120,
         "nov": False, "n_modes": 2, "ra": 1.0, "dec": 2.0, "gmag": 18.0},
    ])
    modes = pd.DataFrame([
        {"tic": 11, "paper": "romero2025", "period_s": 300.0, "amp_ppt": 5.0},
        {"tic": 11, "paper": "romero2025", "period_s": 500.0, "amp_ppt": 9.0},
        {"tic": 11, "paper": "romero2025", "period_s": 700.0, "amp_ppt": 2.0},
        {"tic": 22, "paper": "romero2022", "period_s": 400.0, "amp_ppt": 12.0},
        {"tic": 33, "paper": "romero2022", "period_s": 120.5, "amp_ppt": 8.0},   # rejected at 120 s
        {"tic": 33, "paper": "romero2022", "period_s": 140.0, "amp_ppt": 6.0},   # rejected at 120 s
    ])
    targets.to_csv(d2 / "d2_targets.csv", index=False)
    modes.to_csv(d2 / "d2_modes.csv", index=False)
    (d2 / "d2_roster_report.json").write_text(json.dumps({
        "outputs_sha256": {"d2_targets.csv": sha(d2 / "d2_targets.csv"),
                           "d2_modes.csv": sha(d2 / "d2_modes.csv")}}))
    out = root / "shards"
    builder.main(["--d2-dir", str(d2), "--out-dir", str(out), "--exposure-stars", str(stars),
                  "--catalog", str(catalog), "--n-nulls", "5"], expected_pool=4)
    return {"root": root, "out": out, "stars": stars, "d2": d2}


def test_publish_is_atomic_and_described(generation):
    out = generation["out"]
    assert out.exists() and not (out / "IN_PROGRESS").exists()
    assert not (out.parent / (out.name + ".staging")).exists()
    gen = json.loads((out / "generation_manifest.json").read_text())
    assert gen["production"] is False and set(gen["non_production_reasons"]) == {"n_nulls", "pool"}
    assert gen["n_targets_scheduled"] == 2 and gen["scheduled_tics"] == [11, 22]
    assert [e["tic"] for e in gen["excluded_targets"]] == [33]
    disk = {p.name.split(".csv")[0] for p in out.glob("*.csv.gz")}
    assert set(gen["shard_sha256"]) == disk
    for sid, digest in gen["shard_sha256"].items():
        assert sha(out / f"{sid}.csv.gz") == digest
    index = set((out / "shard_index.txt").read_text().split())
    assert index == disk


def test_manifest_schema_fully_typed_for_every_arm(generation):
    manifest = pd.read_csv(generation["out"] / "shard_manifest.csv",
                           dtype={"campaign_id": str, "control_campaign_id": str})
    assert list(manifest.columns) == list(MANIFEST_COLUMN_NAMES)
    for column in ("phase_draw", "amp_scale", "template_k", "pool_index", "n_strata_scheduled",
                   "null_serial", "dominant_dropped", "template_exp_per_night"):
        assert not manifest[column].isna().any(), column
    assert set(manifest["arm"]) == {"A", "B", "ctrl", "gauss_null"}
    assert manifest["campaign_id"].is_unique
    assert all(campaign_id_ok(s) for s in manifest["campaign_id"])
    nulls = manifest[manifest["arm"] == "gauss_null"]
    assert sorted(nulls["null_serial"]) == [0, 1, 2, 3, 4] and (nulls["amp_scale"] == 0.0).all()
    ctrl = manifest[manifest["arm"] == "ctrl"]
    b_windows = set(manifest.loc[manifest["arm"] == "B", "template_source_id"])
    assert set(ctrl["template_source_id"]) == b_windows and (ctrl["n_strata_scheduled"] == 0).all()


def test_scenarios_are_explicit_and_dropout_is_separate(generation):
    manifest = pd.read_csv(generation["out"] / "shard_manifest.csv", dtype={"campaign_id": str})
    nominal_b = manifest[(manifest["arm"] == "B") & (manifest["scenario"] == SCENARIO_NOMINAL)]
    assert sorted(nominal_b.groupby("tic")["template_k"].apply(sorted).tolist()) == [[0, 1, 2], [0, 1, 2]]
    assert (nominal_b["n_strata_scheduled"] == 3).all() and not nominal_b["dominant_dropped"].any()
    dropout = manifest[manifest["scenario"] == "dropout"]
    assert dropout["tic"].tolist() == [11]            # TIC 22 has one retained mode
    assert dropout["dominant_dropped"].all() and (dropout["amp_scale"] == 1.0).all()
    assert dropout["dropped_period_s"].tolist() == [500.0]
    assert (dropout["n_strata_scheduled"] == 1).all() and (dropout["template_k"] == 1).all()
    sid = dropout["campaign_id"].iloc[0]
    # layout AA TTTTTTTTTT K G R P S C 0 -> P=15, S=16, C=17, reserved=18
    assert sid[15] == "0" and sid[16] == str(AMP_SCALE_CODE_DROPOUT) and sid[17] == "0" and sid[18] == "0"
    expected = {SCENARIO_NOMINAL, "dropout", "phase_1", "phase_2", "ampscale_0.7", "ampscale_1.3",
                "control", "gauss_null"} | {f"ladder_g{g}r{r}" for g in (1, 2, 3) for r in (1, 2, 3)
                                      if (g, r) != (2, 2)}
    assert set(manifest["scenario"]) == expected
    injected = pd.read_csv(generation["out"] / "injected_modes.csv", dtype={"campaign_id": str})
    assert set(injected.loc[injected["campaign_id"] == sid, "period_s"]) == {300.0, 700.0}


def test_epochs_round_trip_bitwise_through_frozen_loader(generation):
    manifest = pd.read_csv(generation["out"] / "shard_manifest.csv", dtype={"campaign_id": str})
    row = manifest[(manifest["arm"] == "B") & (manifest["scenario"] == SCENARIO_NOMINAL)].iloc[0]
    template = load_star(generation["stars"] / f"{row.template_source_id}.csv.gz")
    shard = load_star(generation["out"] / f"{row.campaign_id}.csv.gz")
    for column in ("mjd", "bjd_tdb", "night_mjd", "magerr"):
        assert np.array_equal(template[column].to_numpy(), shard[column].to_numpy()), column
    assert not np.array_equal(template["mag"].to_numpy(), shard["mag"].to_numpy())
    with gzip.open(generation["out"] / f"{row.campaign_id}.csv.gz", "rt") as handle:
        header = handle.readline().strip().split(",")
    assert header == list(EXPOSURE_COLUMNS)


def test_truth_d2_consumes_default_manifest_and_refuses_tampering(generation, tmp_path):
    out = generation["out"]
    with pytest.raises(SystemExit):
        metrics.truth_d2(out, pilot=False)           # non-production needs a pilot
    truth, gen = metrics.truth_d2(out, pilot=True)
    assert len(truth) == gen["n_shards"]
    for column in ("scenario", "dominant_dropped", "n_strata_scheduled", "null_serial",
                   "phase_draw", "amp_scale", "shard_sha256"):
        assert column in truth
    ab = truth[truth["label_positive"]]
    assert ab["freq_scorable"].all() and ab["primary_freq"].notna().all()
    assert (truth.loc[truth["arm"] == "gauss_null", "null_serial"] >= 0).all()
    # tamper: copy the generation and flip one byte of one shard
    import shutil
    copy = tmp_path / "tampered"
    shutil.copytree(out, copy)
    victim = next(copy.glob("92*.csv.gz"))
    data = bytearray(victim.read_bytes())
    data[-1] ^= 0x01
    victim.write_bytes(bytes(data))
    with pytest.raises(SystemExit):
        metrics.truth_d2(copy, pilot=True)
    # sentinel refusal
    sentinel = tmp_path / "inprogress"
    shutil.copytree(out, sentinel)
    (sentinel / "IN_PROGRESS").write_text("x")
    with pytest.raises(SystemExit):
        metrics.truth_d2(sentinel, pilot=True)


def test_cluster_bootstrap_keeps_scenarios_apart_and_uses_scheduled_strata(generation):
    truth, gen = metrics.truth_d2(generation["out"], pilot=True)
    per_star = truth.copy()
    # synthetic outcomes: nominal B detects K=0,1 for TIC 11 and nothing for TIC 22;
    # dropout (TIC 11, K=1) does NOT detect — pooling it into nominal would change p
    def status(r):
        if r["arm"] == "B" and r["scenario"] == SCENARIO_NOMINAL:
            return "confirmed" if (r["cluster"] == "11" and r["template_k"] in (0, 1)) else "not_detected"
        if r["scenario"] == "dropout":
            return "not_detected"
        return "candidate"
    per_star["best_status"] = per_star.apply(status, axis=1)
    per_star["best_candidate_matches_dominant"] = "direct"
    table = metrics.d2_cluster_bootstrap(per_star, gen["scheduled_tics"], pilot=True)
    nominal = table[(table["arm"] == "B") & (table["scenario"] == SCENARIO_NOMINAL)
                    & (table["endpoint"] == "detection") & (table["denominator"] == "eligible")]
    assert len(nominal) == 1
    assert nominal["n_strata_scheduled"].iloc[0] == 3
    assert abs(nominal["p"].iloc[0] - (2 / 3 + 0) / 2) < 1e-12      # (1/3)*2 for TIC 11, 0 for TIC 22
    assert not nominal["confirmatory"].iloc[0]                        # pilot
    dropout = table[(table["scenario"] == "dropout") & (table["endpoint"] == "detection")
                    & (table["denominator"] == "eligible")]
    assert len(dropout) == 1 and dropout["n_strata_scheduled"].iloc[0] == 1
    assert dropout["p"].iloc[0] == 0.0 and dropout["n_targets_in_scenario"].iloc[0] == 1
    assert {"arm", "scenario", "ratio_g", "ratio_rg", "phase_draw", "amp_scale",
            "dominant_dropped"} <= set(table.columns)


def test_pilot_index_spans_every_arm(generation):
    manifest = pd.read_csv(generation["out"] / "shard_manifest.csv", dtype={"campaign_id": str})
    pilot = set((generation["out"] / "pilot_shard_index.txt").read_text().split())
    assert pilot <= set(manifest["campaign_id"])
    picked = manifest[manifest["campaign_id"].isin(pilot)]
    assert {"A", "B", "ctrl", "gauss_null"} <= set(picked["arm"])
    assert "dropout" in set(picked["scenario"]) and "ladder_g1r1" in set(picked["scenario"])


def test_refuses_existing_out_dir_and_bad_roster_sha(generation, tmp_path):
    with pytest.raises(SystemExit):
        builder.main(["--d2-dir", str(generation["d2"]), "--out-dir", str(generation["out"]),
                      "--exposure-stars", str(generation["stars"]),
                      "--catalog", str(generation["root"] / "catalog.csv"), "--n-nulls", "5"],
                     expected_pool=4)
    bad = tmp_path / "d2bad"
    import shutil
    shutil.copytree(generation["d2"], bad)
    (bad / "d2_modes.csv").write_text((bad / "d2_modes.csv").read_text() + "\n")
    with pytest.raises(SystemExit):
        builder.main(["--d2-dir", str(bad), "--out-dir", str(tmp_path / "x"),
                      "--exposure-stars", str(generation["stars"]),
                      "--catalog", str(generation["root"] / "catalog.csv"), "--n-nulls", "5"],
                     expected_pool=4)
