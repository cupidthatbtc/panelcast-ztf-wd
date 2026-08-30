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

Templates are the ATTESTED per-star exposure shards the frozen pipeline
consumed (`--exposure-stars`), not a re-derivation: every non-modified column
is copied as its ORIGINAL TEXT TOKEN, the model is evaluated on the epochs as
the frozen loader parses them, and each written shard is re-loaded through the
frozen loader and checked bitwise (epochs) before it counts (G3 methods
finding 7 — a 17-significant-digit BJD can re-parse one ulp off on the
production machine, so tokens, not floats, are what is preserved).

Template matching per target: |median zg mag − target G| <= 0.25 (widened to
0.5, then nearest-9, when the pool is thin — flagged in the manifest);
K=3 at the 10/50/90th percentiles of median-exposures-per-night, because 75%
of zg nights are single-exposure and per-night median subtraction is the
pre-registered dominant penalty (plan risk 3). Ties: stable sort on
(|Δmag|, source_id), then (exp_per_night, source_id) — a total order.

Run matrix (plan): nominal (1.7, 0.80) on K=3 for arms A+B; every other
scenario on the median template (K=1) only; 1,000 nulls; one control per
unique arm-B window. Targets with ZERO retained modes at nominal cannot be
positives and are excluded from the matrix (recorded in
excluded_targets.csv); dropout is scheduled only for targets with >= 2
retained modes.

Scenario identity is an explicit immutable code (d2_truth_model.scenario_code)
carried on every manifest row; the manifest schema is fixed
(d2_truth_model.MANIFEST_COLUMNS) and every row of every arm is fully typed.

Generation discipline (G3 methods finding 3): shards are built into a staging
directory carrying an IN_PROGRESS sentinel, validated (index == manifest ==
disk, bijections, SHAs), described by generation_manifest.json (a generation
id derived from every input SHA + code SHAs + arguments), and only then
published atomically by renaming the staging directory into place. There is
no resume: a generation is all-or-nothing.

Truth preservation (G2 methods finding 4): every shard's actually-injected
modes (post sinc rejection, with signed factors and phases) go to
injected_modes.csv and the rejected ones to rejected_modes.csv; the metrics
scorer consumes injected_modes.csv, never the original mode table.

A stratified pilot_shard_index.txt (~150 shards spanning every arm and
scenario, window strata and target amplitudes) is always emitted for the
timing pilot (run it with --stars-file); pilot outputs are never
confirmatory (G3 methods finding 8).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from d2_truth_model import (
    AMP_SCALE_CODE_DROPOUT,
    AMP_SCALE_CODES,
    BANDPASS_LADDER_G,
    BANDPASS_LADDER_RG,
    CADENCE_ALT_S,
    CADENCE_CODE_ALT,
    CADENCE_CODE_NOMINAL,
    CROWD_CODE_NONE,
    CROWD_CODE_REDILUTION,
    D2_GENERATION_CODE,
        INJECTED_MODE_COLUMNS,
    MANIFEST_COLUMN_NAMES,
    MANIFEST_COLUMNS,
    N_NULLS_PRODUCTION,
    NOMINAL_G,
    NOMINAL_RG,
    POOL_SIZE_PRODUCTION,
    REJECTED_MODE_COLUMNS,
    SCENARIO_CONTROL,
    SCENARIO_NOMINAL,
    SCENARIO_NULL,
    assert_counts,
    build_truth_model,
    campaign_id,
    check_cadence_alt_schedule,
    control_id,
    expected_counts,
    null_id,
    production_reasons,
    retained_modes,
    scenario_code,
    validate_manifest_frame,
)
from frozen_api import (
    EXPOSURE_COLUMNS,
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    campaign_id_ok,
    frozen_file_shas,
    load_star,
)

PUBLISHED = REPO_ROOT / "catalog-rebuild/results/2026-08-01_full"
MATCH_TOL_MAG = 0.25
MATCH_TOL_WIDE = 0.5
PILOT_TARGETS = 10
PILOT_NULLS = 30
SENTINEL = "IN_PROGRESS"
PANDAS_NA_TOKENS = {"#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
                    "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None",
                    "n/a", "nan", "null"}
SPOC_REPORT = "spoc_verification/v2_publishedsectors_report.json"
SPOC_MODES = "spoc_verification/v2_publishedsectors_recovered_modes.csv"
SPOC_V3_REPORT = "spoc_verification/v3_all103_verification_report.json"   # cadence_alt targets


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------ templates

def read_template(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(tokens, values): the shard's original text tokens for every column and
    the numeric values exactly as the frozen loader parses them."""
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        tokens = pd.read_csv(handle, dtype=str, keep_default_na=False)
    values = load_star(path)
    if len(tokens) != len(values) or list(tokens["band"]) != list(values["band"]):
        raise SystemExit(f"{path}: token/value row mismatch")
    missing = [c for c in EXPOSURE_COLUMNS if c not in tokens.columns]
    if missing:
        raise SystemExit(f"{path}: template lacks columns {missing}")
    return tokens, values


def load_pool(exposure_stars: Path, catalog_path: Path, expected_pool: int
              ) -> tuple[pd.DataFrame, dict[str, tuple[pd.DataFrame, pd.DataFrame]], dict[str, str]]:
    catalog = pd.read_csv(catalog_path, dtype={"source_id": str})
    ids = sorted(catalog["source_id"])
    if len(ids) != expected_pool or len(set(ids)) != expected_pool:
        raise SystemExit(f"catalog has {len(ids)} rows ({len(set(ids))} unique), "
                         f"expected {expected_pool} unique")
    status = catalog.set_index("source_id")["blind_status"].to_dict()
    templates: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    shas: dict[str, str] = {}
    rows = []
    for sid in ids:
        path = exposure_stars / f"{sid}.csv.gz"
        if not path.exists():
            raise SystemExit(f"pool window missing for {sid}: {path}")
        tokens, values = read_template(path)
        zg = values[values["band"] == "zg"]
        if zg.empty:
            raise SystemExit(f"{sid}: no zg window (pool must be complete)")
        templates[sid] = (tokens, values)
        shas[sid] = sha256_file(path)
        rows.append({
            "source_id": sid,
            "median_zg": float(zg["mag"].median()),
            "n_zg": int(len(zg)),
            "exp_per_night": float(zg.groupby("night_mjd").size().median()),
            "blind_status": str(status[sid]),
        })
    stats = pd.DataFrame(rows).sort_values("source_id").reset_index(drop=True)
    stats["pool_index"] = np.arange(len(stats))
    return stats, templates, shas


def match_templates(stats: pd.DataFrame, gmag: float) -> tuple[list[str], str]:
    delta = (stats["median_zg"] - gmag).abs()
    label = "nearest"
    pool = stats.iloc[0:0]
    for tol, tol_label in ((MATCH_TOL_MAG, "tol_0.25"), (MATCH_TOL_WIDE, "tol_0.5")):
        candidate = stats[delta <= tol]
        if len(candidate) >= 3:
            pool, label = candidate, tol_label
            break
    if len(pool) < 3:
        ranked = stats.assign(abs_delta=delta).sort_values(
            ["abs_delta", "source_id"], kind="stable")
        pool = ranked.head(9)
    ordered = pool.sort_values(["exp_per_night", "source_id"], kind="stable").reset_index(drop=True)
    picks = [
        str(ordered.iloc[min(len(ordered) - 1, int(np.round(q * (len(ordered) - 1))))]["source_id"])
        for q in (0.10, 0.50, 0.90)
    ]
    return picks, label


# ----------------------------------------------------------------- ids/shards

def write_shard(path: Path, frame: pd.DataFrame) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        frame[list(EXPOSURE_COLUMNS)].to_csv(handle, index=False, lineterminator="\n")


def synthesize(tokens: pd.DataFrame, values: pd.DataFrame, model, source_id: str,
               gaussian_floor: bool, seed: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Returns (frame to write, computed mag array). Every column except
    source_id and mag is the template's original text token."""
    frame = tokens.copy()
    frame["source_id"] = source_id
    bjd = values["bjd_tdb"].to_numpy(dtype=float)
    band = values["band"].to_numpy()
    mag = values["mag"].to_numpy(dtype=float).copy()
    t_ref = float(bjd.min())
    if gaussian_floor:
        rng = np.random.Generator(np.random.PCG64(seed))
        for name in ("zg", "zr"):
            mask = band == name
            median = float(np.median(mag[mask]))
            noise = rng.normal(0.0, values.loc[mask, "magerr"].to_numpy(dtype=float))
            mag[mask] = median + noise
    for name in ("zg", "zr"):
        mask = band == name
        mag[mask] = mag[mask] + model.evaluate(bjd[mask], name, t_ref)
    frame["mag"] = mag
    return frame, mag


def verify_written(path: Path, values: pd.DataFrame, mag: np.ndarray, source_id: str) -> None:
    """Frozen-loader round trip: epochs bitwise identical to the injection
    epochs, mags within a few ulp, both bands, one id, all finite."""
    loaded = load_star(path)
    for column in ("mjd", "bjd_tdb", "night_mjd", "magerr"):
        if not np.array_equal(loaded[column].to_numpy(dtype=float),
                              values[column].to_numpy(dtype=float)):
            raise SystemExit(f"{path}: {column} does not round-trip bitwise through the frozen loader")
    got = loaded["mag"].to_numpy(dtype=float)
    scale = float(np.max(np.abs(mag))) or 1.0
    if not np.all(np.isfinite(got)) or float(np.max(np.abs(got - mag))) > 8.0 * np.finfo(float).eps * scale:
        raise SystemExit(f"{path}: mag does not round-trip within 8 ulp")
    if set(loaded["source_id"]) != {source_id} or set(loaded["band"]) != {"zg", "zr"}:
        raise SystemExit(f"{path}: source_id/band contract violated")


def typed_row(**fields) -> dict:
    """A manifest row with EVERY schema column present and typed."""
    defaults = {
        "campaign_id": "", "arm": "", "scenario": "", "tic": 0,
        "template_source_id": "", "template_status": "", "template_k": -1,
        "pool_index": -1, "template_exp_per_night": math.nan,
        "ratio_g": 0.0, "ratio_rg": 0.0, "phase_draw": 0, "amp_scale": 1.0,
        "dominant_dropped": False, "dropped_period_s": math.nan,
        "crowdsap": math.nan, "cadence_code": 0, "cadence_s": 0.0,
        "n_strata_scheduled": 0, "match": "",
        "control_campaign_id": "", "null_serial": -1,
        "n_modes_injected": 0, "n_modes_rejected": 0, "shard_sha256": "",
    }
    unknown = set(fields) - set(defaults)
    if unknown:
        raise ValueError(f"unknown manifest fields {unknown}")
    row = {**defaults, **fields}
    casts = {"str": str, "int": int, "float": float, "bool": bool}
    return {name: casts[kind](row[name]) for name, kind in MANIFEST_COLUMNS}


def validate_manifest(frame: pd.DataFrame) -> None:
    validate_manifest_frame(frame)   # schema, uniqueness, typed, per-row semantics
    bad = [sid for sid in frame["campaign_id"] if not campaign_id_ok(sid)]
    if bad:
        raise SystemExit(f"{len(bad)} ids violate the campaign convention: {bad[:3]}")
    # no string cell may be a token pandas' default reader turns into NaN
    for name, kind in MANIFEST_COLUMNS:
        if kind == "str":
            hits = frame[name].isin(PANDAS_NA_TOKENS)
            if hits.any():
                raise SystemExit(f"manifest column {name} holds a pandas NA token: "
                                 f"{frame.loc[hits, name].unique()[:3]}")


def pilot_index(frame: pd.DataFrame, dominant_amp: dict[int, float], n_nulls: int) -> list[str]:
    """Deterministic stratified pilot spanning every arm/scenario."""
    chosen: list[str] = []
    nominal_b = frame[(frame["arm"] == "B") & (frame["scenario"] == SCENARIO_NOMINAL)]
    tics = sorted(nominal_b["tic"].unique(), key=lambda t: (dominant_amp.get(int(t), 0.0), t))
    if tics:
        idx = np.unique(np.round(np.linspace(0, len(tics) - 1, min(PILOT_TARGETS, len(tics)))).astype(int))
        pilot_tics = [tics[i] for i in idx]
        for arm in ("B", "A"):
            sub = frame[(frame["arm"] == arm) & (frame["scenario"] == SCENARIO_NOMINAL)
                        & frame["tic"].isin(pilot_tics)]
            chosen.extend(sub["campaign_id"].tolist())
        for scenario, per in frame[frame["arm"] == "B"].groupby("scenario"):
            if scenario == SCENARIO_NOMINAL:
                continue
            take = per[per["tic"].isin(pilot_tics)].sort_values("campaign_id").head(3)
            if take.empty:
                take = per.sort_values("campaign_id").head(3)
            chosen.extend(take["campaign_id"].tolist())
        controls = nominal_b[nominal_b["tic"].isin(pilot_tics)]["control_campaign_id"]
        chosen.extend(sorted({c for c in controls if c})[:10])
    nulls = frame[frame["arm"] == SCENARIO_NULL].sort_values("null_serial")
    if not nulls.empty:
        idx = np.unique(np.round(np.linspace(0, len(nulls) - 1, min(PILOT_NULLS, len(nulls)))).astype(int))
        chosen.extend(nulls.iloc[idx]["campaign_id"].tolist())
    return sorted(set(chosen))


# ----------------------------------------------------------------------- main

def main(argv: list[str] | None = None, expected_pool: int = POOL_SIZE_PRODUCTION) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d2-dir", type=Path, default=REPO_ROOT / "generalization/data/d2")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="generation directory; must not exist (all-or-nothing build)")
    parser.add_argument("--exposure-stars", type=Path, required=True,
                        help="attested per-star exposure shards of the published 928 catalog")
    parser.add_argument("--catalog", type=Path,
                        default=PUBLISHED / "catalog/ls_full_catalog.csv")
    parser.add_argument("--arms", default="b,ctrl,a,ladder,phase,ampscale,dropout,cadence_alt,nulls",
                        help="add 'redilution' to schedule the SAP-equivalent re-dilution "
                             "variant for SPOC-verified targets (crowdsap from the SPOC report); "
                             "'cadence_alt' = Amendment-3 pure-120-s endpoint for the mixed-"
                             "cadence targets identified by the SPOC v3 report")
    parser.add_argument("--limit", type=int, default=None,
                        help="TEST ONLY: first N targets (non-production; NOT the stratified "
                             "pilot — that is pilot_shard_index.txt of a production generation)")
    parser.add_argument("--n-nulls", type=int, default=N_NULLS_PRODUCTION,
                        help="TEST ONLY: production requires 1000")
    args = parser.parse_args(argv)

    assert_frozen()
    campaign_start = campaign_file_shas()
    arms = set(args.arms.split(","))
    out_dir: Path = args.out_dir
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists — a generation is all-or-nothing; use a fresh directory")
    staging = out_dir.parent / (out_dir.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    (staging / SENTINEL).write_text("building\n", encoding="utf-8")

    targets_path = args.d2_dir / "d2_targets.csv"
    modes_path = args.d2_dir / "d2_modes.csv"
    roster_report_path = args.d2_dir / "d2_roster_report.json"
    roster_report = json.loads(roster_report_path.read_text(encoding="utf-8"))
    for name in ("d2_targets.csv", "d2_modes.csv"):
        recorded = roster_report.get("outputs_sha256", {}).get(name)
        actual = sha256_file(args.d2_dir / name)
        if recorded != actual:
            raise SystemExit(f"{name} SHA {actual[:12]} != roster report's {str(recorded)[:12]}")
    targets = pd.read_csv(targets_path)
    modes = pd.read_csv(modes_path)
    n_targets_input = int(len(targets))
    non_production = production_reasons(arms, args.limit, args.n_nulls, expected_pool, n_targets_input)
    production = not non_production
    if args.limit:
        targets = targets.head(args.limit)
    spoc_report_path = args.d2_dir / SPOC_REPORT
    spoc_modes_path = args.d2_dir / SPOC_MODES
    crowdsap: dict[int, float] = {}
    if spoc_report_path.exists():
        spoc = json.loads(spoc_report_path.read_text(encoding="utf-8"))
        for entry in spoc.get("targets", []):
            if entry.get("crowdsap_median") is not None and "error" not in entry:
                crowdsap[int(entry["tic"])] = float(entry["crowdsap_median"])
    elif "redilution" in arms:
        raise SystemExit("redilution arm needs the SPOC verification report")
    spoc_v3_path = args.d2_dir / SPOC_V3_REPORT
    mixed_cadence: list[int] = []
    if spoc_v3_path.exists():
        v3 = json.loads(spoc_v3_path.read_text(encoding="utf-8"))
        mixed_cadence = sorted(int(e["tic"]) for e in v3.get("targets", [])
                               if e.get("cadence_switched_from_roster") and "error" not in e)
    elif "cadence_alt" in arms:
        raise SystemExit("cadence_alt arm needs the SPOC v3 verification report")

    stats, templates, template_shas = load_pool(args.exposure_stars, args.catalog, expected_pool)
    status_of = stats.set_index("source_id")["blind_status"].to_dict()
    epn_of = stats.set_index("source_id")["exp_per_night"].to_dict()
    pool_index_of = stats.set_index("source_id")["pool_index"].to_dict()

    ladder = [(gi + 1, ri + 1, g, r)
              for gi, g in enumerate(BANDPASS_LADDER_G)
              for ri, r in enumerate(BANDPASS_LADDER_RG)]
    nominal = next((gi, ri, g, r) for gi, ri, g, r in ladder
                   if g == NOMINAL_G and r == NOMINAL_RG)

    manifest: list[dict] = []
    injected_rows: list[dict] = []
    rejected_rows: list[dict] = []
    excluded: list[dict] = []
    dominant_amp: dict[int, float] = {}
    scheduled_tics: list[int] = []
    dropout_eligible: list[int] = []
    redilution_tics: list[int] = []
    cadence_alt_tics: list[int] = []

    def emit(sid: str, tokens, values, model, gaussian: bool, seed: int, **fields) -> None:
        if not campaign_id_ok(sid):
            raise SystemExit(f"bad campaign id {sid}")
        path = staging / f"{sid}.csv.gz"
        if path.exists():
            raise SystemExit(f"duplicate shard {sid}")
        frame, mag = synthesize(tokens, values, model, sid, gaussian, seed)
        write_shard(path, frame)
        verify_written(path, values, mag, sid)
        for mode in model.modes:
            injected_rows.append({
                "campaign_id": sid, "period_s": mode.period_s,
                "frequency_per_day": mode.frequency_per_day,
                "amp_tess_ppt": mode.amp_tess_ppt, "tess_sinc": mode.tess_sinc,
                "ztf_sinc": mode.ztf_sinc, "amp_g_mag": mode.amp_g_mag,
                "amp_r_mag": mode.amp_r_mag, "phase_rad": mode.phase_rad,
            })
        for rejected in model.rejected:
            rejected_rows.append({"campaign_id": sid, **rejected})
        manifest.append(typed_row(
            campaign_id=sid, n_modes_injected=len(model.modes),
            n_modes_rejected=len(model.rejected), shard_sha256=sha256_file(path),
            **fields))

    for target in targets.itertuples(index=False):
        tic = int(target.tic)
        star_modes = modes[modes["tic"] == tic]
        periods = star_modes["period_s"].tolist()
        amps = star_modes["amp_ppt"].tolist()
        cadence = float(target.cadence_s)
        keep = retained_modes(periods, amps, cadence)
        if not keep:
            excluded.append({"tic": tic, "reason": "zero retained modes at this cadence",
                             "n_published_modes": len(periods)})
            continue
        scheduled_tics.append(tic)
        dominant_amp[tic] = float(max(amps[i] for i in keep))
        picks, match_label = match_templates(stats, float(target.gmag))
        N = CADENCE_CODE_NOMINAL
        variants: list[tuple] = []   # (gi, ri, g, r, ks, phase_draw, amp_scale, drop, crowd, cadence_code)
        if "b" in arms or "a" in arms:
            variants.append((*nominal, (0, 1, 2), 0, 1.0, False, CROWD_CODE_NONE, N))
        if "ladder" in arms:
            variants.extend((gi, ri, g, r, (1,), 0, 1.0, False, CROWD_CODE_NONE, N)
                            for gi, ri, g, r in ladder if not (g == NOMINAL_G and r == NOMINAL_RG))
        if "phase" in arms:
            variants.extend((*nominal, (1,), d, 1.0, False, CROWD_CODE_NONE, N) for d in (1, 2))
        if "ampscale" in arms:
            variants.extend((*nominal, (1,), 0, sc, False, CROWD_CODE_NONE, N) for sc in (0.7, 1.3))
        if "dropout" in arms and len(keep) >= 2:
            variants.append((*nominal, (1,), 0, 1.0, True, CROWD_CODE_NONE, N))
            dropout_eligible.append(tic)
        if "redilution" in arms and tic in crowdsap:
            variants.append((*nominal, (1,), 0, 1.0, False, CROWD_CODE_REDILUTION, N))
            redilution_tics.append(tic)
        if "cadence_alt" in arms and tic in mixed_cadence:
            # Amendment 3: pure-120-s endpoint; retention re-applied at 120 s inside
            # build_truth_model; every mixed target keeps >= 1 retained mode (v3 check)
            if retained_modes(periods, amps, CADENCE_ALT_S):
                variants.append((*nominal, (1,), 0, 1.0, False, CROWD_CODE_NONE, CADENCE_CODE_ALT))
                cadence_alt_tics.append(tic)
            else:
                excluded.append({"tic": tic, "reason": "cadence_alt: zero retained modes at 120 s",
                                 "n_published_modes": len(periods)})
        for gi, ri, g, r, ks, phase_draw, amp_scale, drop, crowd, cadence_code in variants:
            scenario = scenario_code(g, r, phase_draw, amp_scale, drop, crowd, cadence_code)
            model_cadence = CADENCE_ALT_S if cadence_code == CADENCE_CODE_ALT else cadence
            model = build_truth_model(
                tic, periods, amps, model_cadence, ratio_g=g, ratio_rg=r,
                crowdsap=crowdsap[tic] if crowd == CROWD_CODE_REDILUTION else None,
                amplitude_scale=amp_scale, phase_draw=phase_draw, drop_dominant=drop)
            amp_code = AMP_SCALE_CODE_DROPOUT if drop else AMP_SCALE_CODES[amp_scale]
            for k in ks:
                template_id = picks[k]
                tokens, values = templates[template_id]
                arm_list = []
                if scenario == SCENARIO_NOMINAL:
                    if "b" in arms:
                        arm_list.append(("92", False))
                    if "a" in arms:
                        arm_list.append(("93", True))
                else:
                    arm_list.append(("92", False))
                for prefix, gaussian in arm_list:
                    sid = campaign_id(prefix, tic, k, gi, ri, phase_draw, amp_code, crowd, cadence_code)
                    emit(sid, tokens, values, model, gaussian, int(sid[2:]),
                         arm="A" if gaussian else "B", scenario=scenario, tic=tic,
                         template_source_id=template_id,
                         template_status=status_of[template_id], template_k=k,
                         pool_index=pool_index_of[template_id],
                         template_exp_per_night=epn_of[template_id],
                         ratio_g=g, ratio_rg=r, phase_draw=phase_draw,
                         amp_scale=amp_scale, dominant_dropped=drop,
                         dropped_period_s=model.dropped_period_s if drop else math.nan,
                         crowdsap=crowdsap[tic] if crowd == CROWD_CODE_REDILUTION else math.nan,
                         cadence_code=cadence_code, cadence_s=model_cadence,
                         n_strata_scheduled=len(ks), match=match_label,
                         control_campaign_id=control_id(pool_index_of[template_id]) if not gaussian else "")
        print(f"[d2-shards] TIC {tic}: {len(manifest)} shards so far", flush=True)

    if "ctrl" in arms:
        used = sorted({row["template_source_id"] for row in manifest if row["arm"] == "B"})
        for template_id in used:
            sid = control_id(pool_index_of[template_id])
            tokens, values = templates[template_id]
            null_model = build_truth_model(0, [], [], 120.0)
            emit(sid, tokens, values, null_model, False, 0,
                 arm="ctrl", scenario=SCENARIO_CONTROL, template_source_id=template_id,
                 template_status=status_of[template_id],
                 pool_index=pool_index_of[template_id],
                 template_exp_per_night=epn_of[template_id])
        print(f"[d2-shards] {len(used)} paired controls", flush=True)

    if "nulls" in arms:
        pool = stats["source_id"].tolist()   # already sorted by source_id
        null_model = build_truth_model(0, [], [], 120.0)
        for serial in range(args.n_nulls):
            template_id = pool[serial % len(pool)]
            tokens, values = templates[template_id]
            emit(null_id(serial), tokens, values, null_model, True, serial,
                 arm=SCENARIO_NULL, scenario=SCENARIO_NULL, template_source_id=template_id,
                 template_status=status_of[template_id],
                 pool_index=pool_index_of[template_id],
                 template_exp_per_night=epn_of[template_id], amp_scale=0.0,
                 null_serial=serial)
            if (serial + 1) % 200 == 0:
                print(f"[d2-shards] nulls {serial + 1}/{args.n_nulls}", flush=True)

    frame = pd.DataFrame(manifest, columns=list(MANIFEST_COLUMN_NAMES))
    validate_manifest(frame)
    injected = pd.DataFrame(injected_rows, columns=list(INJECTED_MODE_COLUMNS))
    rejected = pd.DataFrame(rejected_rows, columns=list(REJECTED_MODE_COLUMNS))
    # bijections: A/B shards <-> injected rows; every shard on disk <-> manifest
    per_sid_injected = injected.groupby("campaign_id").size()
    ab = frame[frame["arm"].isin(["A", "B"])]
    for row in ab.itertuples(index=False):
        if int(per_sid_injected.get(row.campaign_id, 0)) != row.n_modes_injected or row.n_modes_injected < 1:
            raise SystemExit(f"{row.campaign_id}: injected rows != n_modes_injected or zero modes")
    if set(injected["campaign_id"]) - set(ab["campaign_id"]):
        raise SystemExit("injected_modes carries non-A/B ids")
    if set(rejected["campaign_id"]) - set(ab["campaign_id"]):
        raise SystemExit("rejected_modes carries non-A/B ids")
    per_sid_rejected = rejected.groupby("campaign_id").size()
    for row in ab.itertuples(index=False):
        if int(per_sid_rejected.get(row.campaign_id, 0)) != row.n_modes_rejected:
            raise SystemExit(f"{row.campaign_id}: rejected rows != n_modes_rejected")
    disk = {p.name.split(".csv")[0] for p in staging.glob("*.csv.gz")}
    if disk != set(frame["campaign_id"]):
        raise SystemExit("disk shards != manifest ids")
    nominal_b = frame[(frame["arm"] == "B") & (frame["scenario"] == SCENARIO_NOMINAL)]
    per_target_k = nominal_b.groupby("tic")["template_k"].apply(lambda s: sorted(s.tolist()))
    if "b" in arms:
        if sorted(per_target_k.index.tolist()) != sorted(scheduled_tics):
            raise SystemExit("nominal arm-B targets != scheduled targets")
        if any(ks != [0, 1, 2] for ks in per_target_k):
            raise SystemExit("nominal arm-B strata are not exactly K={0,1,2} per target")
    nulls = frame[frame["arm"] == SCENARIO_NULL]
    if "nulls" in arms and sorted(nulls["null_serial"].tolist()) != list(range(args.n_nulls)):
        raise SystemExit("null serials are not exactly 0..N-1")
    # the realized run matrix must equal the SCHEDULED matrix (never outcome-based)
    counts = expected_counts(frame, scheduled_tics, dropout_eligible, redilution_tics,
                             args.n_nulls if "nulls" in arms else 0, arms, cadence_alt_tics)
    assert_counts(frame, counts)
    if "cadence_alt" in arms:
        check_cadence_alt_schedule(mixed_cadence, cadence_alt_tics, production)
        alt_rows = frame[frame["scenario"] == "cadence_alt"]
        if (sorted(alt_rows["tic"].tolist()) != sorted(cadence_alt_tics)
                or (alt_rows["template_k"] != 1).any() or (alt_rows["arm"] != "B").any()):
            raise SystemExit("cadence_alt manifest rows != scheduled cadence_alt targets (one K=1 arm-B row each)")

    frame.to_csv(staging / "shard_manifest.csv", index=False, lineterminator="\n")
    injected.to_csv(staging / "injected_modes.csv", index=False, lineterminator="\n")
    rejected.to_csv(staging / "rejected_modes.csv", index=False, lineterminator="\n")
    pd.DataFrame(excluded, columns=["tic", "reason", "n_published_modes"]).to_csv(
        staging / "excluded_targets.csv", index=False, lineterminator="\n")
    (staging / "shard_index.txt").write_text(
        "\n".join(sorted(frame["campaign_id"])) + "\n", encoding="utf-8")
    (staging / "pilot_shard_index.txt").write_text(
        "\n".join(pilot_index(frame, dominant_amp, args.n_nulls)) + "\n", encoding="utf-8")

    inputs_sha = {
        "d2_targets.csv": sha256_file(targets_path),
        "d2_modes.csv": sha256_file(modes_path),
        "d2_roster_report.json": sha256_file(roster_report_path),
        "catalog": sha256_file(args.catalog),
        "GENERALIZATION_PLAN.md": sha256_file(REPO_ROOT / "generalization/GENERALIZATION_PLAN.md"),
        "METRICS_SPEC.md": sha256_file(REPO_ROOT / "generalization/METRICS_SPEC.md"),
    }
    if spoc_report_path.exists():
        inputs_sha["spoc_report"] = sha256_file(spoc_report_path)
    if spoc_modes_path.exists():
        inputs_sha["spoc_recovered_modes"] = sha256_file(spoc_modes_path)
    if spoc_v3_path.exists():
        inputs_sha["spoc_v3_report"] = sha256_file(spoc_v3_path)
    outputs_sha = {name: sha256_file(staging / name) for name in (
        "shard_manifest.csv", "injected_modes.csv", "rejected_modes.csv",
        "excluded_targets.csv", "shard_index.txt", "pilot_shard_index.txt")}
    shard_shas = dict(zip(frame["campaign_id"], frame["shard_sha256"]))
    generation_basis = {
        "inputs_sha256": inputs_sha, "template_shas": template_shas,
        "frozen_sha256": frozen_file_shas(),
        # only the shard-determining code enters the generation id
        "generation_code_sha256": {name: campaign_start[name] for name in D2_GENERATION_CODE},
        "args": {"arms": sorted(arms), "limit": args.limit, "n_nulls": args.n_nulls,
                 "expected_pool": expected_pool},
    }
    generation_id = hashlib.sha256(
        json.dumps(generation_basis, sort_keys=True).encode()).hexdigest()
    generation = {
        "generation_id": generation_id,
        "production": production,
        "non_production_reasons": non_production,
        "arms": sorted(arms),
        "n_targets_input": n_targets_input,
        "n_targets_scheduled": len(scheduled_tics),
        "scheduled_tics": scheduled_tics,
        "dropout_eligible_tics": dropout_eligible,
        "redilution_tics": redilution_tics,
        "cadence_alt_tics": cadence_alt_tics,
        "mixed_cadence_tics_from_v3": mixed_cadence,
        "expected_counts": counts,
        "campaign_sha256_snapshot": campaign_start,
        "excluded_targets": excluded,
        "n_nulls": args.n_nulls,
        "n_shards": int(len(frame)),
        "by_arm": {k: int(v) for k, v in frame["arm"].value_counts().items()},
        "by_scenario": {k: int(v) for k, v in frame["scenario"].value_counts().items()},
        "match_labels": {k: int(v) for k, v in frame["match"].value_counts().items()},
        "unique_windows_arm_b": int(frame.loc[frame["arm"] == "B", "template_source_id"].nunique()),
        "total_rejected_mode_rows": int(frame["n_modes_rejected"].sum()),
        "crowdsap_available": sorted(crowdsap),
        **generation_basis,
        "outputs_sha256": outputs_sha,
        "shard_sha256": shard_shas,
    }
    if campaign_file_shas() != campaign_start:
        raise SystemExit("campaign code changed while shards were building")
    (staging / "generation_manifest.json").write_text(
        json.dumps(generation, indent=2) + "\n", encoding="utf-8")
    (staging / SENTINEL).unlink()
    os.replace(staging, out_dir)
    summary = {k: generation[k] for k in ("generation_id", "production", "n_targets_scheduled",
                                          "n_shards", "by_arm", "by_scenario", "match_labels")}
    print(json.dumps(summary, indent=2))
    return out_dir


if __name__ == "__main__":
    main()
