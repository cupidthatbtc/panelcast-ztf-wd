#!/usr/bin/env python3
"""Synthesize D2 exposure shards: DAV truth signals in real ZTF windows.

Template pool: ALL 928 stars of the published 2026-08-01 catalog — NOT the
510 not-detected subset (G1 referee finding 1: conditioning templates on the
pipeline's own non-detection is a circularity path). Native variability is
handled by frequency-matched scoring plus paired controls. Every shard
preserves the template's real epochs (bjd_tdb), real cadence structure and
real magerr; arms differ in what carries the noise:

  arm B (92…)  signal added to the REAL ZTF magnitudes — the headline arm
               ("TESS-truth signals injected into real ZTF photometry").
  ctrl (95…)   paired uninjected copy of every unique arm-B template window —
               identifies windows that trigger natively (real variables in
               the pool), so injected-recovery is scored against its own
               window's baseline behavior.
  arm A (93…)  signal added to a synthetic Gaussian floor (median mag +
               N(0, magerr_i)) — diagnostic; separates window effects from
               real-noise effects.
  nulls (94…)  arm-A construction with amplitude_scale = 0 — 1,000 shards
               cycling the 928 windows with distinct noise seeds (windows
               repeat, noise does not). This measures the GAUSSIAN-NULL
               false-alarm rate, not a real-sky FPR (G1 stats finding 11).

Template matching per target: |median zg mag − target G| <= 0.25 (widened to
0.5, then nearest-K, when the pool is thin — flagged in the manifest);
K=3 at the 10/50/90th percentiles of median-exposures-per-night, because 75%
of zg nights are single-exposure and per-night median subtraction is the
pre-registered dominant penalty (plan risk 3).

Run matrix (plan): nominal (1.7, 0.80) on K=3 for arms A+B; the other 8
ladder points on the median template only; 1,000 nulls.

Campaign id layout (19 digits): AA TTTTTTTTTT K GR 0000
  AA arm prefix (92/93), T zero-padded TIC, K template index (0/1/2),
  G/R ladder indices (1-3) into {1.4,1.7,2.1} x {0.70,0.80,0.90}, 22=nominal.
  Nulls: 94 + 17-digit serial. Controls: 95 + 17-digit index of the template
  in the SORTED FIXED 928-window pool — stable across invocations and roster
  subsets (G2 methods finding 3). Full mapping in shard_manifest.csv.

Truth preservation (G2 methods finding 4): every shard's actually-injected
modes (post sinc rejection, with signed factors and phases) go to
injected_modes.csv and the rejected ones to rejected_modes.csv; the metrics
scorer consumes injected_modes.csv, never the original mode table.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from d2_truth_model import (
    BANDPASS_LADDER_G,
    BANDPASS_LADDER_RG,
    NOMINAL_G,
    NOMINAL_RG,
    build_truth_model,
)
from frozen_api import EXPOSURE_COLUMNS, REPO_ROOT, assert_frozen, campaign_id_ok

PUBLISHED = REPO_ROOT / "catalog-rebuild/results/2026-08-01_full"
MATCH_TOL_MAG = 0.25
MATCH_TOL_WIDE = 0.5
N_NULLS = 1000


def load_templates(exposures_path: Path, catalog_path: Path) -> tuple[pd.DataFrame, dict]:
    catalog = pd.read_csv(catalog_path, dtype={"source_id": str})
    if len(catalog) != 928:
        raise SystemExit(f"published catalog has {len(catalog)} rows, expected 928")
    pool_ids = set(catalog["source_id"])
    status = catalog.set_index("source_id")["blind_status"].to_dict()
    exposures = pd.read_csv(
        exposures_path,
        dtype={"source_id": str, "band": str},
        usecols=EXPOSURE_COLUMNS,
    )
    exposures = exposures[exposures["source_id"].isin(pool_ids)]
    zg = exposures[exposures["band"] == "zg"]
    stats = zg.groupby("source_id").agg(
        median_zg=("mag", "median"),
        n_zg=("mag", "size"),
    )
    epn = (
        zg.groupby(["source_id", "night_mjd"]).size().groupby("source_id").median()
        .rename("exp_per_night")
    )
    stats = stats.join(epn)
    stats["blind_status"] = [status[sid] for sid in stats.index]
    frames = {sid: frame for sid, frame in exposures.groupby("source_id")}
    return stats.reset_index(), frames


def match_templates(stats: pd.DataFrame, gmag: float) -> tuple[list[str], str]:
    for tol, label in ((MATCH_TOL_MAG, "tol_0.25"), (MATCH_TOL_WIDE, "tol_0.5")):
        pool = stats[(stats["median_zg"] - gmag).abs() <= tol]
        if len(pool) >= 3:
            break
    else:
        label = "nearest"
    if len(pool) < 3:
        pool = stats.iloc[(stats["median_zg"] - gmag).abs().argsort()[:9]]
    ordered = pool.sort_values(["exp_per_night", "source_id"]).reset_index(drop=True)
    picks = [
        ordered.iloc[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]["source_id"]
        for q in (0.10, 0.50, 0.90)
    ]
    return picks, label


def campaign_id(arm_prefix: str, tic: int, k: int, g_idx: int, r_idx: int) -> str:
    return f"{arm_prefix}{tic:010d}{k}{g_idx}{r_idx}0000"


def write_shard(path: Path, frame: pd.DataFrame) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        frame[EXPOSURE_COLUMNS].to_csv(handle, index=False, lineterminator="\n")


def synthesize(
    template: pd.DataFrame,
    model,
    source_id: str,
    gaussian_floor: bool,
    seed: int,
) -> pd.DataFrame:
    frame = template.copy()
    frame["source_id"] = source_id
    t_ref = float(frame["bjd_tdb"].min())
    if gaussian_floor:
        rng = np.random.Generator(np.random.PCG64(seed))
        for band in ("zg", "zr"):
            mask = frame["band"] == band
            median = float(frame.loc[mask, "mag"].median())
            noise = rng.normal(0.0, frame.loc[mask, "magerr"].to_numpy(dtype=float))
            frame.loc[mask, "mag"] = median + noise
    for band in ("zg", "zr"):
        mask = frame["band"] == band
        frame.loc[mask, "mag"] = frame.loc[mask, "mag"] + model.evaluate(
            frame.loc[mask, "bjd_tdb"].to_numpy(dtype=float), band, t_ref
        )
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d2-dir", type=Path, default=REPO_ROOT / "generalization/data/d2")
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "generalization/data/d2/shards")
    parser.add_argument("--exposures", type=Path, default=PUBLISHED / "data/exposures.csv.gz")
    parser.add_argument("--catalog", type=Path,
                        default=PUBLISHED / "catalog/ls_full_catalog.csv")
    parser.add_argument("--arms", default="b,ctrl,a,ladder,nulls")
    parser.add_argument("--limit", type=int, default=None, help="pilot: first N targets")
    args = parser.parse_args()

    assert_frozen()
    arms = set(args.arms.split(","))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    targets = pd.read_csv(args.d2_dir / "d2_targets.csv")
    modes = pd.read_csv(args.d2_dir / "d2_modes.csv")
    if args.limit:
        targets = targets.head(args.limit)
    stats, frames = load_templates(args.exposures, args.catalog)

    pool_index = {sid: i for i, sid in enumerate(sorted(stats["source_id"]))}

    def control_id(template_id: str) -> str:
        return "95" + str(pool_index[template_id]).zfill(17)

    injected_rows: list[dict] = []
    rejected_rows: list[dict] = []
    ladder = [
        (gi + 1, ri + 1, g, r)
        for gi, g in enumerate(BANDPASS_LADDER_G)
        for ri, r in enumerate(BANDPASS_LADDER_RG)
    ]
    nominal = next(
        (gi, ri, g, r) for gi, ri, g, r in ladder if g == NOMINAL_G and r == NOMINAL_RG
    )
    manifest: list[dict] = []

    for target in targets.itertuples(index=False):
        star_modes = modes[modes["tic"] == target.tic]
        periods = star_modes["period_s"].tolist()
        amps = star_modes["amp_ppt"].tolist()
        picks, match_label = match_templates(stats, float(target.gmag))
        variants = []
        if "b" in arms or "a" in arms:
            variants.append((*nominal, (0, 1, 2)))
        if "ladder" in arms:
            variants.extend((gi, ri, g, r, (1,)) for gi, ri, g, r in ladder
                            if not (g == NOMINAL_G and r == NOMINAL_RG))
        for gi, ri, g, r, template_ks in variants:
            model = build_truth_model(
                int(target.tic), periods, amps, float(target.cadence_s),
                ratio_g=g, ratio_rg=r,
            )
            for k in template_ks:
                template_id = picks[k]
                template = frames[template_id]
                arm_list = []
                if g == NOMINAL_G and r == NOMINAL_RG:
                    if "b" in arms:
                        arm_list.append(("92", False))
                    if "a" in arms:
                        arm_list.append(("93", True))
                else:
                    arm_list.append(("92", False))
                for prefix, gaussian in arm_list:
                    sid = campaign_id(prefix, int(target.tic), k, gi, ri)
                    if not campaign_id_ok(sid):
                        raise SystemExit(f"bad campaign id {sid}")
                    shard = synthesize(template, model, sid, gaussian, seed=int(sid[2:]))
                    write_shard(args.out_dir / f"{sid}.csv.gz", shard)
                    for mode in model.modes:
                        injected_rows.append({
                            "campaign_id": sid, "period_s": mode.period_s,
                            "frequency_per_day": mode.frequency_per_day,
                            "amp_tess_ppt": mode.amp_tess_ppt,
                            "tess_sinc": mode.tess_sinc,
                            "ztf_sinc": mode.ztf_sinc,
                            "amp_g_mag": mode.amp_g_mag,
                            "amp_r_mag": mode.amp_r_mag,
                            "phase_rad": mode.phase_rad,
                        })
                    for rejected in model.rejected:
                        rejected_rows.append({"campaign_id": sid, **rejected})
                    manifest.append({
                        "campaign_id": sid, "arm": "A" if gaussian else "B",
                        "tic": int(target.tic), "template_source_id": template_id,
                        "template_status": stats.set_index("source_id")["blind_status"].get(template_id, ""),
                        "template_k": k, "ratio_g": g, "ratio_rg": r,
                        "match": match_label,
                        "control_campaign_id": control_id(template_id) if not gaussian else "",
                        "n_modes_injected": len(model.modes),
                        "n_modes_rejected": len(model.rejected),
                    })
        print(f"[d2-shards] TIC {target.tic}: {len(manifest)} shards so far", flush=True)

    if "ctrl" in arms:
        used = sorted({
            row["template_source_id"] for row in manifest if row["arm"] == "B"
        })
        null_model = build_truth_model(0, [], [], 120.0)
        for template_id in used:
            sid = control_id(template_id)
            shard = frames[template_id].copy()
            shard["source_id"] = sid
            write_shard(args.out_dir / f"{sid}.csv.gz", shard)
            manifest.append({
                "campaign_id": sid, "arm": "ctrl", "tic": 0,
                "template_source_id": template_id,
                "template_status": stats.set_index("source_id")["blind_status"].get(template_id, ""),
                "template_k": -1, "ratio_g": 0.0, "ratio_rg": 0.0, "match": "",
                "n_modes_injected": 0, "n_modes_rejected": 0,
            })
        print(f"[d2-shards] {len(used)} paired controls", flush=True)

    if "nulls" in arms:
        pool = stats.sort_values("source_id")["source_id"].tolist()
        null_model = build_truth_model(0, [], [], 120.0)
        for serial in range(N_NULLS):
            template_id = pool[serial % len(pool)]
            sid = "94" + str(serial).zfill(17)
            shard = synthesize(frames[template_id], null_model, sid, True, seed=serial)
            write_shard(args.out_dir / f"{sid}.csv.gz", shard)
            manifest.append({
                "campaign_id": sid, "arm": "null", "tic": 0,
                "template_source_id": template_id,
                "template_status": stats.set_index("source_id")["blind_status"].get(template_id, ""),
                "template_k": serial % len(pool),
                "ratio_g": 0.0, "ratio_rg": 0.0, "match": "",
                "n_modes_injected": 0, "n_modes_rejected": 0,
            })
            if (serial + 1) % 200 == 0:
                print(f"[d2-shards] nulls {serial + 1}/{N_NULLS}", flush=True)

    frame = pd.DataFrame(manifest)
    frame.to_csv(args.out_dir / "shard_manifest.csv", index=False)
    pd.DataFrame(injected_rows).to_csv(args.out_dir / "injected_modes.csv", index=False)
    pd.DataFrame(rejected_rows).to_csv(args.out_dir / "rejected_modes.csv", index=False)
    unique_rejected = {
        (row["campaign_id"].split("0000")[0][2:12], row["period_s"])
        for row in rejected_rows
    }
    import hashlib as _hashlib
    outputs_sha = {
        name: _hashlib.sha256((args.out_dir / name).read_bytes()).hexdigest()
        for name in ("shard_manifest.csv", "injected_modes.csv", "rejected_modes.csv")
    }
    ab = frame[frame["arm"].isin(["A", "B"])]
    summary = {
        "shards": len(frame),
        "by_arm": frame["arm"].value_counts().to_dict(),
        "match_labels": frame["match"].value_counts().to_dict(),
        "targets": int(ab["tic"].nunique()),
        "unique_windows_arm_b": int(
            frame.loc[frame["arm"] == "B", "template_source_id"].nunique()),
        "total_rejected_mode_rows": int(frame["n_modes_rejected"].sum()),
        "unique_target_modes_rejected": len(unique_rejected),
        "outputs_sha256": outputs_sha,
    }
    (args.out_dir / "shard_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
