#!/usr/bin/env python3
"""Campaign metrics per METRICS_SPEC.md — the spec's names are binding.

Reads per-star JSONs directly (never only a summary CSV), scores the match
taxonomy against dataset truth, and emits the spec's output files. Datasets:

  d1  published 2026-08-01 bundle (19 labeled WDs inside the 928 catalog);
      truth = Jestin roster + literature periods; census = published CSV.
  d3  campaign Kepler dSct run; truth = roster_d3.csv + Mo+2026 frequencies;
      census = build_panels_generic output.
  d2  campaign injection run; truth = shard_manifest.csv + injected_modes.csv
      (the actually-injected post-sinc-rejection mode set, never d2_modes);
      census computed from the shards with frozen functions; the TESS target
      is the cluster (bootstrap over targets).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from frozen_api import (
    REPO_ROOT,
    SIDEREAL_FREQUENCY,
    assert_frozen,
    campaign_file_shas,
    census_row,
    env_versions,
    frozen_file_shas,
    monthly_panel,
    nightly_panel,
    overall_result,
)

RULES = ("confirmed", "confirmed_or_candidate", "census", "either")
PASSES = ("low", "high", "best")
CHANCE_MATCH_PERMUTATIONS = 100
CHANCE_MATCH_SEED = 20260829
BOOTSTRAP_B = 2000
BOOTSTRAP_SEED = 20260830
MIN_CELL = 5
# added to the pipeline 1.5/baseline tolerance: truth-table quantization
# (D1 literature frequencies are tabulated to 2 decimals; Mo/injected truth
# is effectively exact)
TRUTH_QUANTUM_PER_DAY = {"d1": 0.0025, "d2": 0.0, "d3": 0.0}
PERIOD_EDGES_DAYS = [100 / 86400, 200 / 86400, 500 / 86400, 1000 / 86400,
                     2000 / 86400, 0.05, 0.2, 1.0, 10.0, 100.0]
AMP_EDGES = {"d3": [0.5, 1, 2, 5, 10, 20, 50],
             "d2": [0.5, 2, 5, 10, 30]}
EXP_PER_NIGHT_EDGES = [1.0, 1.5, 2.0, 3.0, 5.0]


def wilson(k: float, n: float) -> tuple[float, float, float]:
    if n <= 0:
        return math.nan, math.nan, math.nan
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def weighted_wilson(successes: np.ndarray, weights: np.ndarray) -> dict:
    total = float(weights.sum())
    if total <= 0:
        return {"n": 0, "ess": 0.0, "p": math.nan, "lo": math.nan, "hi": math.nan}
    p = float((weights * successes).sum() / total)
    ess = total * total / float((weights * weights).sum())
    _, lo, hi = wilson(p * ess, ess)
    return {"n": int(len(successes)), "ess": round(ess, 1), "p": p, "lo": lo, "hi": hi}


def classify_match(freq: float, truth: list[float], tol: float) -> str:
    """Evaluate EVERY (truth mode, relation) predicate — no short-circuit
    (spec: hits in more than one relation class -> ambiguous)."""
    classes: set[str] = set()
    for f_t in truth:
        if abs(freq - f_t) <= tol:
            classes.add("direct")
        if abs(freq - 2.0 * f_t) <= tol or abs(freq - 0.5 * f_t) <= tol:
            classes.add("harmonic")
        for k in (1, 2):
            for sign in (1.0, -1.0):
                if abs(freq - abs(f_t + sign * k * SIDEREAL_FREQUENCY)) <= tol:
                    classes.add("window_alias")
    if not classes:
        return "unmatched"
    if len(classes) > 1:
        return "ambiguous"
    return classes.pop()


def pass_eligible(truth: list[float], pass_name: str, baseline: float) -> bool:
    if not truth:
        return False
    low, high = (2.0 / baseline, 48.0) if pass_name == "low" else (24.0, 1440.0)
    return any(low <= f <= high for f in truth)


def rule_fired(rule: str, status: str, census_flag) -> bool | None:
    if status == "missing":
        # no usable light curve: unconditionally a non-detection under every
        # rule in the eligible-roster estimand
        return False
    if rule == "confirmed":
        return status == "confirmed"
    if rule == "confirmed_or_candidate":
        return status in ("confirmed", "candidate")
    if rule == "census":
        return None if census_flag is None else bool(census_flag)
    if rule == "either":
        if census_flag is None:
            return status == "confirmed"
        return status == "confirmed" or bool(census_flag)
    raise ValueError(rule)


def score_star(json_path: Path, truth_freqs: list[float], primary_freq: float | None,
               truth_quantum: float = 0.0) -> dict:
    result = json.loads(json_path.read_text(encoding="utf-8"))
    if not result.get("complete"):
        raise SystemExit(f"{json_path} is not complete")
    passes = result["passes"]
    if set(passes) != {"low", "high"}:
        raise SystemExit(f"{json_path} passes {set(passes)} != low/high")
    baseline = float(result["baseline_days"])
    tol = 1.5 / baseline + truth_quantum
    overall = overall_result(result)

    row: dict = {
        "baseline_days": baseline,
        "n_exp_zg": result["n_exp_zg"],
        "n_exp_zr": result["n_exp_zr"],
        "best_pass": overall["best_pass"],
        "best_status": overall["blind_status"],
        "best_frequency_per_day": overall["best_frequency_per_day"],
        "low_available": passes["low"].get("available", True),
        "high_available": passes["high"].get("available", True),
    }
    any_direct_top = False
    for name in ("low", "high"):
        p = passes[name]
        freq = p.get("frequency_per_day")
        row[f"{name}_status"] = p["status"]
        row[f"{name}_frequency_per_day"] = freq
        row[f"{name}_match"] = (
            classify_match(float(freq), truth_freqs, tol)
            if freq is not None and truth_freqs else "unscored"
        )
        row[f"{name}_match_primary"] = (
            classify_match(float(freq), [primary_freq], tol)
            if freq is not None and primary_freq is not None else "unscored"
        )
        row[f"{name}_eligible"] = pass_eligible(truth_freqs, name, baseline)
        for peak in p.get("top_peaks", []):
            f_peak = peak.get("frequency_per_day")
            if f_peak is not None and truth_freqs and \
               classify_match(float(f_peak), truth_freqs, tol) == "direct":
                any_direct_top = True
    best_freq = row["best_frequency_per_day"]
    row["best_candidate_matches_any_mode"] = (
        classify_match(float(best_freq), truth_freqs, tol)
        if best_freq is not None and truth_freqs else "unscored"
    )
    row["best_candidate_matches_dominant"] = (
        classify_match(float(best_freq), [primary_freq], tol)
        if best_freq is not None and primary_freq is not None else "unscored"
    )
    row["any_top_peak_matches_any_mode"] = any_direct_top
    row["eligible_any_pass"] = row["low_eligible"] or row["high_eligible"]
    return row


# ---------------------------------------------------------------- truth loaders

def truth_d1() -> pd.DataFrame:
    """Labels from the PUBLISHED master table (19 usable stars; 13
    paper-variable) — the 20-row acquisition roster additionally contains
    sanity controls whose paper_variable flag does not enter the published
    counts. D1 truth frequencies are non-contemporaneous literature
    tabulations (multi-mode DAVs wander between epochs); frequency-recovery
    scoring for D1 is therefore DIAGNOSTIC ONLY (METRICS_SPEC) and D1's
    estimand is detection completeness."""
    master = pd.read_csv(
        REPO_ROOT / "lomb-scargle/results/2026-08-01_full/master_table.csv",
        dtype={"source_id": str},
    )
    lit = pd.read_csv(REPO_ROOT / "data/roster/literature_periods.csv",
                      dtype={"source_id": str})
    freqs = lit.groupby("source_id")["frequency_per_day"].apply(list).to_dict()
    rows = []
    for r in master.itertuples(index=False):
        truth = freqs.get(r.source_id, [])
        # 2833849800205759360 is the frozen pipeline's eclipsing-system sanity
        # control (expected confirmed at 6.1464 / d): a known variable, so it
        # can be neither a paper-constant negative nor a roster positive.
        is_control = r.source_id == "2833849800205759360"
        rows.append({
            "sid": r.source_id, "external_id": r.wdj_name,
            "class_label": "transit_control" if is_control else r.wd_class,
            "label_positive": None if is_control
            else str(r.paper_variable).lower() == "true",
            "weight": 1.0, "cluster": r.source_id,
            "truth_freqs": truth,
            "primary_freq": truth[0] if truth else None,
            "amp": math.nan, "truth_period_days": 1.0 / truth[0] if truth else math.nan,
            "freq_scorable": bool(truth),
        })
    return pd.DataFrame(rows)


def truth_d3() -> pd.DataFrame:
    roster = pd.read_csv(REPO_ROOT / "generalization/data/d3/roster_d3.csv",
                         dtype={"source_id": str})
    mo = pd.read_csv(REPO_ROOT / "generalization/data/d3/raw/mo2026_table2.csv")
    mo["freq_per_day"] = mo["Freq"] * 86400.0 / 1e6
    freq_lists = mo.groupby("KIC")["freq_per_day"].apply(list).to_dict()
    rows = []
    for r in roster.itertuples(index=False):
        kic = int(r.KIC)
        truth = freq_lists.get(kic, [])
        label = None if r.dSct == 2 else bool(r.dSct == 1)
        rows.append({
            "sid": r.source_id, "external_id": r.external_id,
            "class_label": r.class_label, "label_positive": label,
            "weight": float(r.sampling_weight), "cluster": r.source_id,
            "truth_freqs": truth,
            "primary_freq": float(r.dom_freq_per_day)
            if np.isfinite(r.dom_freq_per_day) else None,
            "amp": float(r.amp_mmag),
            "truth_period_days": 1.0 / float(r.dom_freq_per_day)
            if np.isfinite(r.dom_freq_per_day) and r.dom_freq_per_day > 0 else math.nan,
            "freq_scorable": bool(truth) and bool(label),
            "stratum": r.stratum, "near_saturation": bool(r.near_saturation),
            "subhour": bool(r.subhour),
        })
    return pd.DataFrame(rows)


D2_DTYPES = {"str": str, "int": "int64", "float": float, "bool": bool}


def load_d2_manifest(shards_dir: Path) -> pd.DataFrame:
    """Fixed typed manifest schema (d2_truth_model.MANIFEST_COLUMNS); any
    deviation, NaN in an int/bool column, or duplicate id is fatal."""
    from d2_truth_model import MANIFEST_COLUMN_NAMES, MANIFEST_COLUMNS
    path = shards_dir / "shard_manifest.csv"
    header = pd.read_csv(path, nrows=0).columns.tolist()
    if header != list(MANIFEST_COLUMN_NAMES):
        raise SystemExit(f"{path}: columns deviate from the frozen manifest schema")
    dtype = {name: D2_DTYPES[kind] for name, kind in MANIFEST_COLUMNS}
    try:
        manifest = pd.read_csv(path, dtype=dtype)
    except (ValueError, TypeError) as exc:
        raise SystemExit(f"{path}: manifest violates its typed schema: {exc}")
    for name, kind in MANIFEST_COLUMNS:
        if kind == "str":
            manifest[name] = manifest[name].fillna("")
        elif kind in ("int", "bool") and manifest[name].isna().any():
            raise SystemExit(f"{path}: NaN in typed column {name}")
    from d2_truth_model import validate_manifest_frame
    validate_manifest_frame(manifest)   # uniqueness + per-row semantic invariants
    return manifest


def truth_d2(shards_dir: Path, pilot: bool = False) -> tuple[pd.DataFrame, dict]:
    """Truth from injected_modes.csv — the ACTUALLY injected (post-sinc-
    rejection) mode set per shard, never the original mode table (G2 methods
    finding 4). Fail-closed contract checks (G3 methods findings 1, 4):
    published generation only, fixed typed schema, index == manifest == disk,
    per-shard SHA identity against the generation record, A/B <-> injected-row
    bijection, exactly one nominal-B replicate per (scheduled target, K in
    {0,1,2}), exact null serials 0..n-1 (n = 1000 in production)."""
    from d2_truth_model import SCENARIO_NOMINAL
    if (shards_dir / "IN_PROGRESS").exists():
        raise SystemExit(f"{shards_dir} is an unpublished (in-progress) generation")
    generation_path = shards_dir / "generation_manifest.json"
    if not generation_path.exists():
        raise SystemExit(f"{shards_dir} lacks generation_manifest.json (not a published generation)")
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    from d2_truth_model import (D2_GENERATION_CODE, TARGETS_PRODUCTION, assert_counts,
                                production_reasons)
    if not generation.get("production") and not pilot:
        raise SystemExit(f"non-production generation {generation.get('non_production_reasons')} "
                         f"can only feed a pilot (run manifest pilot=true)")
    # 1. every recorded output file must be byte-identical BEFORE it is read
    expected_outputs = ("shard_manifest.csv", "injected_modes.csv", "rejected_modes.csv",
                        "excluded_targets.csv", "shard_index.txt", "pilot_shard_index.txt")
    recorded_outputs = generation.get("outputs_sha256", {})
    if set(recorded_outputs) != set(expected_outputs):
        raise SystemExit("generation manifest outputs_sha256 lacks the complete truth-file set")
    for name, digest in recorded_outputs.items():
        if sha256_file(shards_dir / name) != digest:
            raise SystemExit(f"{name} differs from the generation record (tampered or mixed)")
    # 2. the generation id must be reproducible from its recorded basis
    basis_keys = ("inputs_sha256", "template_shas", "frozen_sha256", "generation_code_sha256", "args")
    basis = {k: generation.get(k) for k in basis_keys}
    if hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest() != generation.get("generation_id"):
        raise SystemExit("generation id does not reproduce from its recorded basis")
    # 3. frozen code and the shard-determining campaign code must be THIS checkout
    if generation.get("frozen_sha256") != frozen_file_shas():
        raise SystemExit("generation was built against different frozen files")
    current_code = {name: campaign_file_shas()[name] for name in D2_GENERATION_CODE}
    if generation.get("generation_code_sha256") != current_code:
        raise SystemExit("generation was built by different shard-determining code "
                         "(build_d2_shards/d2_truth_model/frozen_api); rebuild the generation")
    # 4. production claims are re-derived from the recorded arguments, never trusted
    args_rec = generation.get("args", {})
    reasons = production_reasons(set(args_rec.get("arms", [])), args_rec.get("limit"),
                                 int(args_rec.get("n_nulls", -1)), int(args_rec.get("expected_pool", -1)),
                                 int(generation.get("n_targets_input", -1)))
    if bool(generation.get("production")) != (not reasons):
        raise SystemExit(f"generation production flag inconsistent with its arguments: {reasons}")
    manifest = load_d2_manifest(shards_dir)
    # 5. the realized run matrix must equal the scheduled matrix, unconditionally
    assert_counts(manifest, generation.get("expected_counts", {}))
    if generation.get("production") and int(generation.get("n_targets_input", -1)) != TARGETS_PRODUCTION:
        raise SystemExit("production generation must schedule the canonical 103-target roster")
    index_ids = {line.strip() for line in
                 (shards_dir / "shard_index.txt").read_text(encoding="utf-8").splitlines() if line.strip()}
    disk_ids = {p.name.split(".csv")[0] for p in shards_dir.glob("*.csv.gz")}
    manifest_ids = set(manifest["campaign_id"])
    if not (index_ids == disk_ids == manifest_ids):
        raise SystemExit(f"{shards_dir}: index/disk/manifest id sets differ "
                         f"({len(index_ids)}/{len(disk_ids)}/{len(manifest_ids)})")
    recorded = generation.get("shard_sha256", {})
    if generation.get("n_shards") != len(manifest) or set(recorded) != manifest_ids:
        raise SystemExit("generation manifest does not describe this shard set")
    for row in manifest.itertuples(index=False):
        actual = sha256_file(shards_dir / f"{row.campaign_id}.csv.gz")
        if actual != row.shard_sha256 or actual != recorded[row.campaign_id]:
            raise SystemExit(f"{row.campaign_id}: shard bytes differ from the generation record")
    injected = pd.read_csv(shards_dir / "injected_modes.csv", dtype={"campaign_id": str})
    rejected = pd.read_csv(shards_dir / "rejected_modes.csv", dtype={"campaign_id": str})
    ab = manifest[manifest["arm"].isin(["A", "B"])]
    n_inj = injected.groupby("campaign_id").size()
    n_rej = rejected.groupby("campaign_id").size()
    for row in ab.itertuples(index=False):
        if int(n_inj.get(row.campaign_id, 0)) != row.n_modes_injected or row.n_modes_injected < 1:
            raise SystemExit(f"{row.campaign_id}: injected_modes rows != n_modes_injected (or zero)")
        if int(n_rej.get(row.campaign_id, 0)) != row.n_modes_rejected:
            raise SystemExit(f"{row.campaign_id}: rejected_modes rows != n_modes_rejected")
    if set(injected["campaign_id"]) - set(ab["campaign_id"]):
        raise SystemExit("injected_modes.csv carries control/null ids")
    if set(rejected["campaign_id"]) - set(ab["campaign_id"]):
        raise SystemExit("rejected_modes.csv carries foreign ids")
    scheduled = [int(t) for t in generation.get("scheduled_tics", [])]
    nominal_b = manifest[(manifest["arm"] == "B") & (manifest["scenario"] == SCENARIO_NOMINAL)]
    if not nominal_b.empty:
        per_target = nominal_b.groupby("tic")["template_k"].apply(lambda s: sorted(s.tolist()))
        if (sorted(per_target.index.tolist()) != sorted(scheduled)
                or any(ks != [0, 1, 2] for ks in per_target)):
            raise SystemExit("nominal arm-B rows are not exactly K={0,1,2} for every scheduled target")
        if len(scheduled) != int(generation.get("n_targets_scheduled", -1)):
            raise SystemExit("scheduled target list disagrees with the generation manifest")
    from d2_truth_model import check_cadence_alt_schedule
    if "cadence_alt" in set(args_rec.get("arms", [])):
        alt_sched = [int(t) for t in generation.get("cadence_alt_tics", [])]
        check_cadence_alt_schedule([int(t) for t in generation.get("mixed_cadence_tics_from_v3", [])],
                                   alt_sched, bool(generation.get("production")))
        alt_rows = manifest[manifest["scenario"] == "cadence_alt"]
        if (sorted(alt_rows["tic"].tolist()) != sorted(alt_sched)
                or (alt_rows["template_k"] != 1).any() or (alt_rows["arm"] != "B").any()):
            raise SystemExit("cadence_alt rows != the generation's scheduled cadence_alt targets")
    nulls = manifest[manifest["arm"] == "gauss_null"]
    if not nulls.empty:
        if sorted(nulls["null_serial"].tolist()) != list(range(int(generation.get("n_nulls", -1)))):
            raise SystemExit("null serials are not exactly 0..n_nulls-1")
        if generation.get("production") and int(generation["n_nulls"]) != 1000:
            raise SystemExit("production generation must schedule exactly 1000 nulls")
    freq_lists = injected.groupby("campaign_id")["frequency_per_day"].apply(
        lambda g: sorted(g.tolist())).to_dict()
    dominant, amp_dom = {}, {}
    for sid, group in injected.groupby("campaign_id"):
        best = group.loc[group["amp_tess_ppt"].idxmax()]
        dominant[sid] = float(best["frequency_per_day"])
        amp_dom[sid] = float(best["amp_tess_ppt"])
    rows = []
    for r in manifest.itertuples(index=False):
        arm, tic, sid = r.arm, int(r.tic), r.campaign_id
        positive = arm in ("A", "B")
        truth = freq_lists.get(sid, []) if positive else []
        rows.append({
            "sid": sid, "external_id": f"TIC {tic}" if tic else r.template_source_id,
            "class_label": f"arm_{arm}", "label_positive": positive,
            "weight": 1.0, "cluster": str(tic) if tic else sid,
            "truth_freqs": truth,
            "primary_freq": dominant.get(sid) if positive else None,
            "amp": float(amp_dom.get(sid, math.nan)),
            "truth_period_days": (1.0 / dominant[sid]) if sid in dominant and positive else math.nan,
            "freq_scorable": positive and bool(truth),
            "arm": arm, "scenario": r.scenario, "template_k": int(r.template_k),
            "pool_index": int(r.pool_index),
            "ratio_g": float(r.ratio_g), "ratio_rg": float(r.ratio_rg),
            "phase_draw": int(r.phase_draw), "amp_scale": float(r.amp_scale),
            "dominant_dropped": bool(r.dominant_dropped),
            "dropped_period_s": float(r.dropped_period_s),
            "crowdsap": float(r.crowdsap),
            "cadence_code": int(r.cadence_code), "cadence_s": float(r.cadence_s),
            "n_strata_scheduled": int(r.n_strata_scheduled),
            "null_serial": int(r.null_serial),
            "control_campaign_id": r.control_campaign_id,
            "shard_sha256": r.shard_sha256,
            "median_exp_per_night": float(r.template_exp_per_night),
            "template_status": r.template_status,
        })
    return pd.DataFrame(rows), generation


# ---------------------------------------------------------- census providers

def census_lookup_csv(path: Path) -> dict[str, dict]:
    frame = pd.read_csv(path, dtype={"source_id": str})
    ratio_cols = [c for c in frame.columns if c.endswith("_ratio")]
    for col in ratio_cols:
        exact = frame[col] == 2.5
        if exact.any():
            raise SystemExit(f"census ratio exactly 2.5 in {path}:{col} — spec guard")
    return {
        r["source_id"]: {
            "census_variable": bool(r["census_variable"]),
            "census_g_nightly": bool(r["census_g_nightly"]),
            "median_exp_per_night": float(r["zg_median_exp_per_night"])
            if "zg_median_exp_per_night" in frame.columns else math.nan,
        }
        for _, r in frame.iterrows()
    }


def census_from_shard(shard_path: Path) -> dict:
    frame = pd.read_csv(gzip.open(shard_path, "rt"), dtype={"source_id": str, "band": str})
    meta = SimpleNamespace(source_id=frame["source_id"].iloc[0], wdj_name="",
                           gaia_g_mag=math.nan, bp_rp=math.nan, in_core=True,
                           n_variants=0, known_roster=False, wd_class="",
                           paper_variable=None, paper_periodic=None)
    nightly = nightly_panel(frame)
    monthly = monthly_panel(nightly)
    row = census_row(meta, frame, nightly, monthly)
    for key in (f"{b}_{c}_ratio" for b in ("zg", "zr")
                for c in ("exposure", "nightly", "monthly")):
        if row.get(key) == 2.5:
            raise SystemExit(f"census ratio exactly 2.5 for {shard_path} — spec guard")
    return {"census_variable": bool(row["census_variable"]),
            "census_g_nightly": bool(row["census_g_nightly"])}


# ------------------------------------------------------------------ aggregates

def completeness_tables(per_star: pd.DataFrame, dataset: str) -> pd.DataFrame:
    # primary frequency-match column: D3 scores the DOMINANT Mo mode (any-mode
    # is secondary/diagnostic); D2 scores the exact injected list; D1 is
    # diagnostic-only either way (spec).
    use_dominant = True  # headline = best_candidate_matches_dominant (spec)
    rows = []
    positives = per_star[per_star["label_positive"] == True]  # noqa: E712
    usable = positives[(positives["best_status"] != "missing")
                       & positives["low_available"].fillna(False)
                       & positives["high_available"].fillna(False)]
    for pass_name in PASSES:
        status_col = "best_status" if pass_name == "best" else f"{pass_name}_status"
        match_col = ("best_candidate_matches_dominant" if pass_name == "best"
                     else f"{pass_name}_match_primary")
        for rule in RULES:
            for scope, frame in (
                ("detection_eligible_roster", positives),
                ("detection_usable_lightcurve", usable),
                ("freq_recovery_scorable", usable[
                    usable["freq_scorable"]
                    & (usable["eligible_any_pass"] if pass_name == "best"
                       else usable[f"{pass_name}_eligible"])
                ]),
            ):
                if scope == "freq_recovery_scorable" and rule in ("census", "either"):
                    continue  # frequency outcomes exist only for L-S rules
                if frame.empty:
                    rows.append({"pass": pass_name, "rule": rule, "scope": scope,
                                 "n": 0, "ess": 0.0, "p": math.nan,
                                 "lo": math.nan, "hi": math.nan})
                    continue
                fired = frame.apply(
                    lambda r: rule_fired(rule, r[status_col], r.get("census_variable")),
                    axis=1,
                )
                ok = fired.notna()
                success = fired[ok].astype(bool)
                if scope == "freq_recovery_scorable":
                    success = success & (frame.loc[ok, match_col] == "direct")
                stats = weighted_wilson(
                    success.to_numpy(dtype=float),
                    frame.loc[ok, "weight"].to_numpy(dtype=float),
                )
                rows.append({"pass": pass_name, "rule": rule, "scope": scope, **stats})
        # correct-frequency fraction among detected positives (spec):
        # P(match dominant | rule-1 fired, Y=1, F=1, S_p=1)
        scorable = usable[usable["freq_scorable"]
                          & (usable["eligible_any_pass"] if pass_name == "best"
                             else usable[f"{pass_name}_eligible"])]
        status_col = "best_status" if pass_name == "best" else f"{pass_name}_status"
        detected = scorable[scorable[status_col] == "confirmed"]
        if len(detected):
            correct = (detected[match_col] == "direct")
            stats = weighted_wilson(correct.to_numpy(dtype=float),
                                    detected["weight"].to_numpy(dtype=float))
        else:
            stats = {"n": 0, "ess": 0.0, "p": math.nan, "lo": math.nan, "hi": math.nan}
        rows.append({"pass": pass_name, "rule": "confirmed",
                     "scope": "correct_frequency_fraction_detected", **stats})
    return pd.DataFrame(rows)


def contingency(per_star: pd.DataFrame, dataset: str = "d1") -> dict:
    from scipy.stats import binomtest
    frame = per_star[(per_star["label_positive"] == True)  # noqa: E712
                     & per_star["census_variable"].notna()
                     & (per_star["best_status"] != "missing")]
    C = frame["census_variable"].astype(bool)
    L = frame["best_status"] == "confirmed"
    a, b = int((C & L).sum()), int((C & ~L).sum())
    c, d = int((~C & L).sum()), int((~C & ~L).sum())
    n = len(frame)
    union_p, union_lo, union_hi = wilson(a + b + c, n) if n else (math.nan,) * 3
    out = {
        "n_positives_scored": n,
        "table": {"census_and_ls": a, "census_only": b, "ls_only": c, "neither": d},
        "union_completeness": {"p": union_p, "lo": union_lo, "hi": union_hi},
        "incremental_census_only": dict(zip(("p", "lo", "hi"), wilson(b, n))) if n else {},
        "incremental_ls_only": dict(zip(("p", "lo", "hi"), wilson(c, n))) if n else {},
    }
    if b + c and dataset != "d2":
        out["mcnemar_exact_p_secondary"] = float(
            binomtest(min(b, c), b + c, 0.5).pvalue * 1.0
        )
    if dataset == "d2":
        out["mcnemar"] = "prohibited for d2 (cluster structure); use the target-cluster paired-difference bootstrap"
    return out


def chance_match_rate(per_star: pd.DataFrame) -> dict:
    scorable = per_star[per_star["freq_scorable"]
                        & per_star["best_frequency_per_day"].notna()].reset_index()
    if len(scorable) < 3:
        return {"permutations": 0, "note": "fewer than 3 scorable stars"}
    rng = np.random.Generator(np.random.PCG64(CHANCE_MATCH_SEED))
    rates = []
    truth_lists = scorable["truth_freqs"].tolist()
    for _ in range(CHANCE_MATCH_PERMUTATIONS):
        perm = rng.permutation(len(truth_lists))
        hits = 0
        for i, row in scorable.iterrows():
            if perm[i] == i:
                continue
            tol = 1.5 / row["baseline_days"]
            if classify_match(float(row["best_frequency_per_day"]),
                              truth_lists[perm[i]], tol) == "direct":
                hits += 1
        denom = int((np.arange(len(truth_lists)) != perm).sum())
        if denom:
            rates.append(hits / denom)
    return {"permutations": CHANCE_MATCH_PERMUTATIONS,
            "accidental_direct_match_rate_mean": float(np.mean(rates)),
            "accidental_direct_match_rate_p95": float(np.quantile(rates, 0.95))}


def cp_one_sided_bounds(k: int, n: int) -> tuple[float, float]:
    from scipy.stats import beta
    lower = float(beta.ppf(0.05, k, n - k + 1)) if k > 0 else 0.0
    upper = float(beta.ppf(0.95, k + 1, n - k)) if k < n else 1.0
    return lower, upper


def d2_cluster_bootstrap(per_star: pd.DataFrame, scheduled_tics: list[int] | None = None,
                         pilot: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """P4 machinery: per (scenario, endpoint), per-stratum rates and the
    scenario-standardized mean over targets; COMMON RANDOM NUMBERS — one
    resample-index matrix shared by every scenario; degenerate statistics
    fall back to target-level exact CP. Scenario identity is the explicit
    manifest `scenario` code plus every grouping key (G3 methods finding 2);
    the eligible denominator is the scenario's SCHEDULED strata count
    (3 nominal, 1 single-window sensitivities), never a fixed 3; the nominal
    arm-B scenario is the ONLY confirmatory P4 row, and only outside pilots."""
    if "arm" not in per_star or "scenario" not in per_star:
        return pd.DataFrame(), pd.DataFrame()
    frame = per_star[per_star["arm"].isin(["A", "B"])]
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame()
    if scheduled_tics:
        clusters = np.array(sorted(str(int(t)) for t in scheduled_tics))
    else:
        clusters = np.array(sorted(frame["cluster"].unique()))
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    draws = rng.integers(0, len(clusters), size=(BOOTSTRAP_B, len(clusters)))
    rows = []
    endpoints = {
        "detection": lambda f: f["best_status"] == "confirmed",
        "freq_recovery": lambda f: (f["best_status"] == "confirmed")
        & (f["best_candidate_matches_dominant"] == "direct"),
    }
    scenario_cols = ["arm", "scenario", "ratio_g", "ratio_rg", "phase_draw",
                     "amp_scale", "dominant_dropped", "cadence_code"]

    def bootstrap_stats(aligned: pd.Series) -> tuple[float, float, float, str, int]:
        observed = aligned.dropna()
        point = float(observed.mean())
        values = aligned.to_numpy(dtype=float)
        boots = []
        for b in range(BOOTSTRAP_B):
            sample = values[draws[b]]
            sample = sample[~np.isnan(sample)]
            if sample.size:
                boots.append(float(sample.mean()))
        target_hits = observed.round(6)
        degenerate = (target_hits == 0).all() or (target_hits == 1).all()
        if degenerate:
            k_deg = int((target_hits == 1).sum())
            lo, hi = cp_one_sided_bounds(k_deg, len(observed))
            return point, lo, hi, "cp_one_sided", len(observed)
        return (point, float(np.quantile(boots, 0.025)),
                float(np.quantile(boots, 0.975)), "cluster_bootstrap", len(observed))

    for keys, scenario in frame.groupby(scenario_cols):
        key = dict(zip(scenario_cols, keys))
        key["dominant_dropped"] = bool(key["dominant_dropped"])
        strata = scenario["n_strata_scheduled"].unique()
        if len(strata) != 1 or int(strata[0]) < 1:
            raise SystemExit(f"scenario {key} has inconsistent n_strata_scheduled {strata}")
        n_strata = int(strata[0])
        present = set(scenario["cluster"])
        is_nominal = key["scenario"] == "nominal"
        if is_nominal:
            counts = scenario.groupby(["cluster", "template_k"]).size()
            if (counts != 1).any() or set(scenario["template_k"]) != set(range(n_strata)):
                raise SystemExit("nominal scenario must hold exactly one replicate per (target, K)")
            if scheduled_tics and present != set(clusters):
                raise SystemExit("nominal scenario targets != scheduled targets")
        usable_rows = scenario[scenario["best_status"] != "missing"]
        zero_usable = sorted(present - set(usable_rows["cluster"]))
        # `confirmatory` = the row BELONGS to the prespecified production
        # analysis (P4 = detection, nominal arm B, non-pilot); it never encodes
        # whether the row passes anything (G3 methods round-2 new MAJOR)
        for endpoint, predicate in endpoints.items():
            confirmatory = (key["arm"] == "B" and is_nominal and not pilot
                            and endpoint == "detection")
            for denom in ("usable", "eligible"):
                subset = usable_rows if denom == "usable" else scenario
                if subset.empty:
                    continue
                if denom == "eligible":
                    # missing replicate = failure; fixed |K_t| = scheduled strata (spec P4)
                    success = predicate(subset) & (subset["best_status"] != "missing")
                    per_ts = success.groupby(
                        [subset["cluster"], subset["template_k"]]).mean()
                    per_target = per_ts.groupby(level=0).sum() / float(n_strata)
                else:
                    # renormalize over usable strata; a target with ZERO usable
                    # strata drops from the usable estimand (counted once, below)
                    success = predicate(subset)
                    per_ts = success.groupby(
                        [subset["cluster"], subset["template_k"]]).mean()
                    per_target = per_ts.groupby(level=0).mean()
                aligned = per_target.reindex(clusters)
                if aligned.dropna().empty:
                    continue
                point, lo, hi, interval, n_targets = bootstrap_stats(aligned)
                rows.append({
                    **key, "endpoint": endpoint, "denominator": denom,
                    "n_strata_scheduled": n_strata,
                    "n_targets_in_scenario": len(present),
                    "n_targets": n_targets,
                    "n_targets_zero_usable_strata": len(zero_usable),
                    "p": point, "lo": lo, "hi": hi, "interval": interval,
                    "confirmatory": confirmatory,
                })
        # paired census-vs-LS difference, target-clustered (nominal arm B only)
        if (key["arm"] == "B" and is_nominal
                and "census_variable" in usable_rows
                and usable_rows["census_variable"].notna().any()):
            paired = usable_rows[usable_rows["census_variable"].notna()]
            c_only = paired["census_variable"].astype(bool) & (
                paired["best_status"] != "confirmed")
            l_only = (~paired["census_variable"].astype(bool)) & (
                paired["best_status"] == "confirmed")
            diff = (c_only.astype(float) - l_only.astype(float)).groupby(
                paired["cluster"]).mean()
            aligned = diff.reindex(clusters)
            if not aligned.dropna().empty:
                point, lo, hi, interval, n_targets = bootstrap_stats(aligned)
                rows.append({
                    **key, "endpoint": "paired_census_minus_ls_discordance",
                    "denominator": "usable", "n_strata_scheduled": n_strata,
                    "n_targets_in_scenario": len(present), "n_targets": n_targets,
                    "n_targets_zero_usable_strata": len(zero_usable),
                    "p": point, "lo": lo, "hi": hi, "interval": interval,
                    "confirmatory": False,
                })

    # PAIRED contrasts (G3 round-3, both reviewers): every non-nominal arm-B
    # scenario vs nominal K=1 on the IDENTICAL target set, one row per target
    # on each side, ONE common draw matrix for both vectors and their
    # difference; usable denominator = targets usable on BOTH sides;
    # eligible denominator keeps missing rows as failures on both sides
    def boot_mean(vec: pd.Series) -> tuple[float, float, float]:
        values = vec.to_numpy(dtype=float)
        observed = values[~np.isnan(values)]
        if observed.size == 0:
            return math.nan, math.nan, math.nan
        boots = []
        for b in range(BOOTSTRAP_B):
            sample = values[draws[b]]
            sample = sample[~np.isnan(sample)]
            if sample.size:
                boots.append(float(sample.mean()))
        return (float(observed.mean()), float(np.quantile(boots, 0.025)),
                float(np.quantile(boots, 0.975)))

    contrasts = []
    b_rows = frame[frame["arm"] == "B"]
    nominal_k1 = b_rows[(b_rows["scenario"] == "nominal") & (b_rows["template_k"] == 1)]
    for keys, scenario in b_rows[b_rows["scenario"] != "nominal"].groupby(scenario_cols):
        key = dict(zip(scenario_cols, keys))
        key["dominant_dropped"] = bool(key["dominant_dropped"])
        if scenario["cluster"].duplicated().any():
            raise SystemExit(f"scenario {key['scenario']} holds more than one row per target")
        targets = set(scenario["cluster"])
        nom = nominal_k1[nominal_k1["cluster"].isin(targets)]
        if set(nom["cluster"]) != targets or nom["cluster"].duplicated().any():
            raise SystemExit(f"nominal K=1 rows do not match the {key['scenario']} target set")
        for endpoint, predicate in endpoints.items():
            for denom in ("usable", "eligible"):
                if denom == "usable":
                    both = (set(scenario.loc[scenario["best_status"] != "missing", "cluster"])
                            & set(nom.loc[nom["best_status"] != "missing", "cluster"]))
                    s_, n_ = scenario[scenario["cluster"].isin(both)], nom[nom["cluster"].isin(both)]
                else:
                    s_, n_ = scenario, nom
                if s_.empty:
                    continue
                ys = (predicate(s_) & (s_["best_status"] != "missing")).astype(float) \
                    .groupby(s_["cluster"]).mean().reindex(clusters)
                yn = (predicate(n_) & (n_["best_status"] != "missing")).astype(float) \
                    .groupby(n_["cluster"]).mean().reindex(clusters)
                ps, lo_s, hi_s = boot_mean(ys)
                pn, lo_n, hi_n = boot_mean(yn)
                pd_, lo_d, hi_d = boot_mean(ys - yn)
                contrasts.append({
                    **key, "endpoint": endpoint, "denominator": denom,
                    "contrast": "scenario_minus_nominal_k1",
                    "n_targets_matched": int(ys.notna().sum()),
                    "p_scenario": ps, "lo_scenario": lo_s, "hi_scenario": hi_s,
                    "p_nominal_k1": pn, "lo_nominal_k1": lo_n, "hi_nominal_k1": hi_n,
                    "diff": pd_, "diff_lo": lo_d, "diff_hi": hi_d,
                    "interval": "paired_cluster_bootstrap_common_draws",
                    "confirmatory": False,
                })
    return pd.DataFrame(rows), pd.DataFrame(contrasts)


def surface_cells(frame: pd.DataFrame, success: pd.Series,
                  x_values: pd.Series, edges: list[float],
                  x_name: str) -> list[dict]:
    """Half-open [lo, hi) bins; bin 0 = underflow, bin len(edges) = overflow;
    NaN x -> bin -1 ("unknown"). Cells below MIN_CELL: counts only."""
    bins = np.where(np.isfinite(x_values), np.digitize(x_values, edges), -1)
    rows = []
    for b, idx in frame.groupby(bins).groups.items():
        k = int(success.loc[idx].sum())
        n = len(idx)
        entry = {x_name: int(b), "n": n, "k": k}
        if n >= MIN_CELL:
            entry.update(dict(zip(("p", "lo", "hi"), wilson(k, n))))
        rows.append(entry)
    return rows


def surfaces(per_star: pd.DataFrame, dataset: str) -> dict[str, pd.DataFrame]:
    if dataset == "d1":
        return {}  # no amplitude axis for D1 (spec)
    out: dict[str, pd.DataFrame] = {}
    amp_edges = AMP_EDGES[dataset]
    positives = per_star[per_star["label_positive"] == True]  # noqa: E712
    # detection endpoint: ALL positives; unknown-amplitude stars form their
    # own bin (-1) so the 154 unjoined D3 positives stay in the denominator
    detection = positives["best_status"] == "confirmed"
    out["detection_amplitude"] = pd.DataFrame(
        surface_cells(positives, detection, positives["amp"], amp_edges, "amp_bin"))
    # detection endpoint on (period, amplitude): unknowns fall in bin -1
    p_bins_all = np.where(np.isfinite(positives["truth_period_days"]),
                          np.digitize(positives["truth_period_days"],
                                      PERIOD_EDGES_DAYS), -1)
    a_bins_all = np.where(np.isfinite(positives["amp"]),
                          np.digitize(positives["amp"], amp_edges), -1)
    det_rows = []
    for (pb, ab), idx in positives.groupby([p_bins_all, a_bins_all]).groups.items():
        k = int(detection.loc[idx].sum())
        n = len(idx)
        entry = {"period_bin": int(pb), "amp_bin": int(ab), "n": n, "k": k}
        if n >= MIN_CELL:
            entry.update(dict(zip(("p", "lo", "hi"), wilson(k, n))))
        det_rows.append(entry)
    out["detection_period_amplitude"] = pd.DataFrame(det_rows)
    # frequency-recovery endpoint: scorable AND S_best subset only
    scorable = positives[positives["freq_scorable"]
                         & positives["eligible_any_pass"]]
    if not scorable.empty:
        match_col = "best_candidate_matches_dominant"
        recovery = (scorable["best_status"] == "confirmed") & (
            scorable[match_col] == "direct")
        rows = []
        p_bins = np.digitize(scorable["truth_period_days"], PERIOD_EDGES_DAYS)
        a_bins = np.where(np.isfinite(scorable["amp"]),
                          np.digitize(scorable["amp"], amp_edges), -1)
        for (pb, ab), idx in scorable.groupby([p_bins, a_bins]).groups.items():
            k = int(recovery.loc[idx].sum())
            n = len(idx)
            entry = {"period_bin": int(pb), "amp_bin": int(ab), "n": n, "k": k}
            if n >= MIN_CELL:
                entry.update(dict(zip(("p", "lo", "hi"), wilson(k, n))))
            rows.append(entry)
        out["freq_recovery_period_amplitude"] = pd.DataFrame(rows)
        if "median_exp_per_night" in scorable and \
                scorable["median_exp_per_night"].notna().any():
            def epn_amp_cells(frame, success):
                e_bins = np.where(
                    np.isfinite(frame["median_exp_per_night"]),
                    np.digitize(frame["median_exp_per_night"], EXP_PER_NIGHT_EDGES),
                    -1)
                ab = np.where(np.isfinite(frame["amp"]),
                              np.digitize(frame["amp"], amp_edges), -1)
                cells = []
                for (eb, abin), idx in frame.groupby([e_bins, ab]).groups.items():
                    k = int(success.loc[idx].sum())
                    n = len(idx)
                    entry = {"exp_per_night_bin": int(eb), "amp_bin": int(abin),
                             "n": n, "k": k}
                    if n >= MIN_CELL:
                        entry.update(dict(zip(("p", "lo", "hi"), wilson(k, n))))
                    cells.append(entry)
                return pd.DataFrame(cells)

            out["freq_recovery_exposure_amplitude"] = epn_amp_cells(
                scorable, recovery)
        if "median_exp_per_night" in positives and \
                positives["median_exp_per_night"].notna().any():
            e_bins_all = np.where(
                np.isfinite(positives["median_exp_per_night"]),
                np.digitize(positives["median_exp_per_night"],
                            EXP_PER_NIGHT_EDGES), -1)
            det_e_rows = []
            for (eb, abin), idx in positives.groupby(
                    [e_bins_all, a_bins_all]).groups.items():
                k = int(detection.loc[idx].sum())
                n = len(idx)
                entry = {"exp_per_night_bin": int(eb), "amp_bin": int(abin),
                         "n": n, "k": k}
                if n >= MIN_CELL:
                    entry.update(dict(zip(("p", "lo", "hi"), wilson(k, n))))
                det_e_rows.append(entry)
            out["detection_exposure_amplitude"] = pd.DataFrame(det_e_rows)
    return out


def trigger_rates(per_star: pd.DataFrame, dataset: str, pilot: bool = False) -> pd.DataFrame:
    rows = []
    if dataset == "d3":
        negatives = per_star[per_star["class_label"] == "dsct_flag0"]
        for rule in RULES:
            fired = negatives.apply(
                lambda r: rule_fired(rule, r["best_status"], r.get("census_variable")),
                axis=1,
            )
            ok = fired.notna()
            stats = weighted_wilson(fired[ok].astype(bool).to_numpy(dtype=float),
                                    negatives.loc[ok, "weight"].to_numpy(dtype=float))
            rows.append({"quantity": "negative_class_trigger_rate", "rule": rule, **stats})
    if dataset == "d2" and "arm" in per_star:
        nulls = per_star[per_star["arm"] == "gauss_null"]
        if not nulls.empty:
            valid = (nulls["prov_valid"].astype(bool) if "prov_valid" in nulls
                     else pd.Series(True, index=nulls.index))
            completed = nulls[(nulls["best_status"] != "missing") & valid]
            if "null_serial" in completed and completed["null_serial"].duplicated().any():
                raise SystemExit("duplicate null serials among completed nulls")
            x = int((completed["best_status"] == "confirmed").sum())
            n = len(completed)
            _, upper = cp_one_sided_bounds(x, n) if n else (math.nan, math.nan)
            rows.append({
                "quantity": "fpr_gaussian", "rule": "confirmed",
                "n_scheduled": len(nulls), "n_completed": n, "k": x,
                "p": x / n if n else math.nan,
                "cp_one_sided_95_upper": upper,
                # the confirmatory decision requires ALL 1000 trials completed
                "acceptance_u95_leq_0.005": bool(n == 1000 and upper <= 0.005),
                "n_completed_is_1000": bool(n == 1000),
                # membership in the prespecified P5 analysis (non-pilot, all 1000
                # trials completed) — the OUTCOME is acceptance_u95_leq_0.005
                "confirmatory": bool((not pilot) and n == 1000),
            })
        controls = per_star[per_star["arm"] == "ctrl"]
        if not controls.empty:
            fired = controls["best_status"] == "confirmed"
            stats = weighted_wilson(fired.to_numpy(dtype=float),
                                    np.ones(len(controls)))
            rows.append({"quantity": "native_trigger_rate", "rule": "confirmed",
                         **stats})
    return pd.DataFrame(rows)


def ppv_d3(per_star: pd.DataFrame) -> dict:
    """Frame-specific label PPV: weighted fraction of triggered (rule-1, best
    pass) roster members labeled dSct=1; dSct=2 excluded, reported separately.
    Survey bootstrap: negatives resampled with replacement, positives fixed."""
    # the frame keeps every sampled member — a missing light curve cannot
    # trigger but remains part of the SRS (stats4: preserve all 2,314)
    frame = per_star[per_star["class_label"].isin(["dsct_flag0", "dsct_flag1"])]
    triggered = frame[frame["best_status"] == "confirmed"]
    if triggered.empty:
        return {"note": "no triggered stars in the PPV frame"}
    weights = triggered["weight"].to_numpy(dtype=float)
    is_pos = (triggered["class_label"] == "dsct_flag1").to_numpy()
    point = float((weights * is_pos).sum() / weights.sum())
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED + 1))
    positives = frame[frame["class_label"] == "dsct_flag1"]
    negatives = frame[frame["class_label"] == "dsct_flag0"].reset_index(drop=True)
    boots = []
    for _ in range(BOOTSTRAP_B):
        resampled = negatives.iloc[
            rng.integers(0, len(negatives), size=len(negatives))
        ]
        combined = pd.concat([positives, resampled])
        hit = combined[combined["best_status"] == "confirmed"]
        if hit.empty:
            continue
        w = hit["weight"].to_numpy(dtype=float)
        boots.append(float(
            (w * (hit["class_label"] == "dsct_flag1").to_numpy()).sum() / w.sum()
        ))
    triggered_ambiguous = int(
        (per_star[per_star["class_label"] == "dsct_flag2"]["best_status"]
         == "confirmed").sum()
    )
    # SRSWOR finite-population correction: sampling fraction f = 2314/7292;
    # bootstrap deviations rescaled by sqrt(1 - f) about the point estimate
    fpc = math.sqrt(1.0 - 2314.0 / 7292.0)
    rescaled = [point + fpc * (b - point) for b in boots]
    return {
        "estimand": "frame_specific_label_ppv",
        "p": point,
        "lo": float(np.quantile(rescaled, 0.025)) if rescaled else math.nan,
        "hi": float(np.quantile(rescaled, 0.975)) if rescaled else math.nan,
        "interval": "survey_bootstrap_fpc_rescaled",
        "n_triggered": int(len(triggered)),
        "bootstrap_B_effective": len(boots),
        "dsct2_triggered_reported_separately": triggered_ambiguous,
    }


def fp_frequency_distribution(per_star: pd.DataFrame, dataset: str) -> pd.DataFrame:
    if dataset == "d3":
        pool = per_star[per_star["class_label"] == "dsct_flag0"]
    elif dataset == "d2" and "arm" in per_star:
        pool = per_star[per_star["arm"].isin(["gauss_null", "ctrl"])]
    else:
        pool = per_star.iloc[0:0]
    triggered = pool[pool["best_status"].isin(["confirmed", "candidate"])]
    columns = ["sid", "class_label", "arm", "scenario", "best_status", "best_pass",
               "best_frequency_per_day", "baseline_days"]
    return triggered[[c for c in columns if c in triggered.columns]]


def sensitivity_table(per_star: pd.DataFrame, dataset: str,
                      crossmatch_qc: pd.DataFrame | None) -> pd.DataFrame:
    rows = []

    def rate(frame: pd.DataFrame, label: str, variant: str) -> None:
        if frame.empty:
            return
        success = (frame["best_status"] == "confirmed")
        rows.append({"variant": variant, "subset": label,
                     "n": len(frame), "k": int(success.sum()),
                     **dict(zip(("p", "lo", "hi"), wilson(int(success.sum()), len(frame))))})

    if dataset == "d2" and "arm" in per_star and "scenario" in per_star:
        # common-subset rule: every non-nominal scenario is contrasted with the
        # nominal median-window (K=1) rate recomputed on that scenario's EXACT
        # matched target set (G3 methods round-2 finding 2)
        median_b = per_star[(per_star["arm"] == "B") & (per_star["template_k"] == 1)]
        nominal = median_b[median_b["scenario"] == "nominal"]
        group_cols = ["scenario", "ratio_g", "ratio_rg", "phase_draw", "amp_scale",
                      "dominant_dropped", "cadence_code"]
        for keys, scenario in median_b.groupby(group_cols):
            label = "_".join(f"{c}={v}" for c, v in zip(group_cols, keys))
            if keys[0] == "nominal":
                rate(scenario[scenario["best_status"] != "missing"], "arm_b_median_window", label)
                continue
            # exact common subset: targets USABLE on both sides (symmetric missingness)
            usable_s = set(scenario.loc[scenario["best_status"] != "missing", "cluster"])
            usable_n = set(nominal.loc[nominal["best_status"] != "missing", "cluster"])
            both = usable_s & usable_n
            rate(scenario[scenario["cluster"].isin(both)], "arm_b_median_window_common", label)
            rate(nominal[nominal["cluster"].isin(both)], f"nominal_on_{keys[0]}_targets_common", label)
    if dataset == "d3":
        positives = per_star[(per_star["label_positive"] == True)  # noqa: E712
                             & (per_star["best_status"] != "missing")]
        if "near_saturation" in positives:
            rate(positives[positives["near_saturation"] == True], "positives", "near_saturation")  # noqa: E712
            rate(positives[positives["near_saturation"] == False], "positives", "safe_magnitude")  # noqa: E712
        if crossmatch_qc is not None:
            qc = crossmatch_qc.set_index("source_id")
            joined = positives.join(
                qc[["nearest_separation_arcsec", "ztf_objects_in_cone"]], on="sid")
            clean = joined[(joined["nearest_separation_arcsec"] < 1.0)
                           & (joined["ztf_objects_in_cone"] <= 3)]
            rate(clean, "positives", "crowding_clean")
    return pd.DataFrame(rows)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("d1", "d2", "d3"), required=True)
    parser.add_argument("--stars-dir", type=Path, required=True)
    parser.add_argument("--census-csv", type=Path, default=None)
    parser.add_argument("--shards-dir", type=Path, default=None,
                        help="the shard directory the run consumed (REQUIRED for d2/d3): "
                             "d2 = the published generation; d3 = <panels>/exposure_stars")
    parser.add_argument("--shard-index", type=Path, default=None,
                        help="shard_index.txt the run was launched with (default: "
                             "<shards-dir>/shard_index.txt); its SHA must equal the run "
                             "manifest's shard_index_sha256")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--crossmatch-qc", type=Path, default=None,
                        help="d3: crossmatch_qc.csv from build_panels_generic "
                             "(enables the crowding sensitivity subset)")
    parser.add_argument("--run-manifest", type=Path, default=None,
                        help="manifest.json written by run_generalization_ls for "
                             "the stars-dir; REQUIRED for d2/d3 — binds the scored "
                             "JSONs to their replay attestation and tier")
    args = parser.parse_args()

    assert_frozen()
    campaign_shas_start = campaign_file_shas()
    attestation_record: dict = {"tier": "published_bundle"}
    boundary_margin = 1e-9
    run_manifest: dict = {}
    generation: dict | None = None
    pilot = False
    if args.dataset in ("d2", "d3"):
        if args.run_manifest is None:
            raise SystemExit("d2/d3 metrics require --run-manifest (attestation binding)")
        run_manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
        if not str(run_manifest.get("dataset", "")).startswith(args.dataset):
            raise SystemExit(f"run manifest dataset {run_manifest.get('dataset')!r} is not {args.dataset}")
        pilot = bool(run_manifest.get("pilot", False))
        att_path = Path(run_manifest.get("replay_attestation", {}).get("path", ""))
        if not att_path.exists():
            raise SystemExit(f"run manifest's replay attestation not found: {att_path}")
        attestation = json.loads(att_path.read_text(encoding="utf-8"))
        if attestation.get("gate") != "replay_gate" or attestation.get("passed") is not True:
            # decision-equivalent tier: allowed ONLY if every star's diagnostic is clean
            diag = [s_.get("decision_equivalence") for s_ in attestation.get("stars", [])]
            if not diag or any(d is None or not d.get("decisions_identical") for d in diag):
                raise SystemExit("attestation is neither a strict PASS nor fully decision-equivalent")
            tier = "decision_identical"
            f64_max = max(d["f64_max_relative_difference"] for d in diag)
            boundary_margin = max(100.0 * f64_max, 1e-9)
        else:
            tier = "strict"
            f64_max = 0.0
        if run_manifest.get("frozen_sha256") != frozen_file_shas():
            raise SystemExit("run manifest frozen SHAs differ from this checkout")
        attestation_record = {
            "tier": tier, "path": str(att_path),
            "sha256": sha256_file(att_path),
            "roster_size": attestation.get("roster_size", len(attestation.get("stars", []))),
            "f64_max_relative_difference": f64_max,
            "boundary_margin_relative": boundary_margin,
            "run_manifest_sha256": sha256_file(args.run_manifest),
        }
    if args.dataset in ("d2", "d3") and args.shards_dir is None:
        raise SystemExit("d2/d3 metrics require --shards-dir (the run's shard universe)")
    if args.dataset == "d1":
        truth = truth_d1()
    elif args.dataset == "d3":
        truth = truth_d3()
    else:
        if args.shards_dir is None:
            raise SystemExit("d2 needs --shards-dir")
        truth, generation = truth_d2(args.shards_dir, pilot=pilot)
        if run_manifest.get("generation_id") != generation["generation_id"]:
            raise SystemExit("run manifest generation_id != shards-dir generation (stale or mixed results)")

    census = census_lookup_csv(args.census_csv) if args.census_csv else {}
    inputs: dict[str, str] = {}
    if args.census_csv:
        inputs[str(args.census_csv)] = sha256_file(args.census_csv)
    completion: pd.DataFrame | None = None
    selected_ids: set[str] | None = None
    run_binding: dict = {}
    run_env_digest = ""
    if args.run_manifest is not None:
        inputs[str(args.run_manifest)] = sha256_file(args.run_manifest)
        completion_path = args.run_manifest.parent / "completion.csv"
        if not completion_path.exists():
            raise SystemExit(f"run manifest has no completion.csv beside it: {completion_path}")
        inputs[str(completion_path)] = sha256_file(completion_path)
        completion = pd.read_csv(completion_path, dtype=str).fillna("")
        if int(run_manifest.get("source_count", -1)) != len(completion):
            raise SystemExit("run manifest source_count != completion table rows")
        failed_ids = set(run_manifest.get("failures", {}))
        if set(completion.loc[completion["status"] == "failed", "source_id"]) != failed_ids:
            raise SystemExit("run manifest failures != completion table failures")
        if completion["source_id"].duplicated().any():
            raise SystemExit("completion table has duplicate ids")
        selected_ids = set(completion["source_id"])
        subset_run = run_manifest.get("limit") is not None or bool(run_manifest.get("stars_file"))
        # run universe (G3 methods round-3 BLOCKING): the index the run was
        # launched with is SHA-bound to the run manifest, equals the on-disk
        # shard set, and bounds the completion table; d3 ids must be truth ids
        index_path = args.shard_index or (args.shards_dir / "shard_index.txt")
        if not index_path.exists():
            raise SystemExit(f"shard index not found: {index_path}")
        index_sha = sha256_file(index_path)
        if run_manifest.get("shard_index_sha256") != index_sha:
            raise SystemExit("shard index SHA differs from the run manifest's shard_index_sha256")
        inputs[str(index_path)] = index_sha
        universe = {line.strip() for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()}
        disk_universe = {p.name.split(".csv")[0] for p in args.shards_dir.glob("*.csv.gz")}
        if universe != disk_universe:
            raise SystemExit(f"shard index ({len(universe)}) != shards on disk ({len(disk_universe)})")
        if not selected_ids <= universe:
            raise SystemExit("completion table lists ids outside the shard index")
        if generation is not None and universe != set(generation.get("shard_sha256", {})):
            raise SystemExit("shard index != the generation's shard set")
        if args.dataset == "d3" and not selected_ids <= set(truth["sid"]):
            raise SystemExit("completion table lists ids that are not D3 truth ids")
        subset_run = subset_run or selected_ids != universe
        if bool(run_manifest.get("pilot")) != subset_run:
            raise SystemExit("run manifest pilot flag inconsistent with limit/stars_file/completion")
        run_binding = dict(run_manifest.get("binding", {}))
        run_env_digest = hashlib.sha256(
            json.dumps(run_manifest.get("env", {}), sort_keys=True).encode()).hexdigest()
        if pilot:
            # a pilot scores exactly what it ran; nothing else is eligible
            truth = truth[truth["sid"].isin(selected_ids)].reset_index(drop=True)
    if generation is not None:
        # the full D2 provenance chain (G3 methods finding 5): truth tables,
        # index, generation record and every shard's recorded SHA (verified
        # against disk in truth_d2)
        for name in ("shard_manifest.csv", "injected_modes.csv", "rejected_modes.csv",
                     "excluded_targets.csv", "shard_index.txt", "pilot_shard_index.txt",
                     "generation_manifest.json"):
            if (args.shards_dir / name).exists():
                inputs[str(args.shards_dir / name)] = sha256_file(args.shards_dir / name)
        for sid, sha in generation.get("shard_sha256", {}).items():
            inputs[str(args.shards_dir / f"{sid}.csv.gz")] = sha
        for label, sha in generation.get("inputs_sha256", {}).items():
            inputs[f"generation_input:{label}"] = sha

    rows = []
    missing = []
    for r in truth.itertuples(index=False):
        json_path = args.stars_dir / f"{r.sid}.json"
        if not json_path.exists():
            # eligible roster target with no usable light curve: counts as a
            # non-detection in the eligible-roster estimand, excluded from the
            # usable-light-curve estimand (G2 stats finding 2)
            missing.append(r.sid)
            if completion is not None:
                row_ = completion[completion["source_id"] == r.sid]
                if len(row_) == 1 and row_["status"].iloc[0] == "complete":
                    raise SystemExit(f"{r.sid}: completion table says complete but no result file")
            record = {**r._asdict(),
                      "best_status": "missing", "low_status": "missing",
                      "high_status": "missing", "best_candidate_matches_any_mode": "unscored",
                      "best_candidate_matches_dominant": "unscored", "low_match": "unscored",
                      "high_match": "unscored", "low_eligible": False,
                      "high_eligible": False, "eligible_any_pass": False,
                      "best_frequency_per_day": None, "baseline_days": math.nan,
                      "any_top_peak_matches_any_mode": False,
                      "prov_valid": False,
                      "census_variable": census.get(r.sid, {}).get("census_variable")}
            rows.append(record)
            continue
        inputs[str(json_path)] = sha256_file(json_path)
        if args.dataset in ("d2", "d3"):
            # provenance sidecar binding (G3 methods finding 6): a result counts
            # only if its sidecar ties it to THIS shard, attestation, generation
            prov_path = args.stars_dir / f"{r.sid}.prov.json"
            if not prov_path.exists():
                raise SystemExit(f"{r.sid}: result has no provenance sidecar")
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
            result_obj = json.loads(json_path.read_text(encoding="utf-8"))
            problems = []
            if result_obj.get("source_id") != r.sid:
                problems.append("result source_id")
            if prov.get("source_id") != r.sid:
                problems.append("sidecar source_id")
            if prov.get("result_sha256") != inputs[str(json_path)]:
                problems.append("result sha256")
            if prov.get("attestation_sha256") != attestation_record.get("sha256"):
                problems.append("attestation sha256")
            if generation is not None and prov.get("generation_id") != generation["generation_id"]:
                problems.append("generation id")
            shard_file = args.shards_dir / f"{r.sid}.csv.gz"
            if not shard_file.exists():
                problems.append("shard file missing from --shards-dir")
            elif prov.get("shard_sha256") != sha256_file(shard_file):
                problems.append("shard sha256")
            if set(prov.get("passes", [])) != set(run_manifest.get("passes", [])):
                problems.append("pass set")
            if prov.get("env_digest") != run_env_digest:
                problems.append("env digest")
            for key in ("frozen_digest", "campaign_digest", "generation_id"):
                if prov.get(key) != run_binding.get(key):
                    problems.append(f"binding {key}")
            if completion is not None:
                row_ = completion[completion["source_id"] == r.sid]
                if len(row_) != 1 or row_["status"].iloc[0] != "complete" \
                        or row_["result_sha256"].iloc[0] != inputs[str(json_path)]:
                    problems.append("completion table")
            if problems:
                raise SystemExit(f"{r.sid}: provenance sidecar mismatch: {problems}")
        scored = score_star(json_path, list(r.truth_freqs), r.primary_freq,
                            TRUTH_QUANTUM_PER_DAY[args.dataset])
        record = {**r._asdict(), **scored}
        if r.sid in census:
            record.update(census[r.sid])
        elif args.dataset == "d2" and args.shards_dir is not None:
            record.update(census_from_shard(args.shards_dir / f"{r.sid}.csv.gz"))
        else:
            record["census_variable"] = None
        record["prov_valid"] = True
        rows.append(record)
    per_star = pd.DataFrame(rows)
    if per_star.empty:
        raise SystemExit("no stars scored")
    # platform-boundary audit (amendment-1): decisions whose FAP sits within
    # the attested drift margin of the 1e-3 threshold, best-pass near-ties,
    # and frequency matches within the margin of the match tolerance — all
    # REPORTED; under the decision_identical tier they require strict-env
    # recomputation before the estimates are authoritative
    def fap_near(x):
        return x is not None and isinstance(x, (int, float)) and x > 0 \
            and abs(x - 1e-3) / 1e-3 <= boundary_margin
    flags = []
    for r in rows:
        near = []
        for pn in ("low", "high"):
            js = json.loads((args.stars_dir / f"{r['sid']}.json").read_text()) \
                if (args.stars_dir / f"{r['sid']}.json").exists() else None
            if not js:
                continue
            p_ = js["passes"].get(pn, {})
            for band in ("zg", "zr"):
                if fap_near(p_.get(f"{band}_fap")):
                    near.append(f"{pn}.{band}_fap")
        flags.append(near)
    per_star["platform_boundary_sensitive"] = [bool(f) for f in flags]
    per_star["platform_boundary_fields"] = [";".join(f) for f in flags]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    per_star.drop(columns=["truth_freqs"]).to_csv(
        args.out_dir / "per_star.csv", index=False)
    # D2 primary aggregates never pool arms/scenarios: nominal arm B only
    # (G3 methods round-2 new MAJOR); scenario contrasts live in sensitivity.csv
    if args.dataset == "d2":
        primary = per_star[(per_star["arm"] == "B") & (per_star["scenario"] == "nominal")]
    else:
        primary = per_star
    completeness_tables(primary, args.dataset).to_csv(
        args.out_dir / "completeness_by_class_pass_rule.csv", index=False)
    (args.out_dir / "contingency_complementarity.json").write_text(
        json.dumps(contingency(primary, args.dataset), indent=2) + "\n",
        encoding="utf-8")
    trigger_rates(per_star, args.dataset, pilot).to_csv(
        args.out_dir / "trigger_rates.csv", index=False)
    (args.out_dir / "chance_match.json").write_text(
        json.dumps(chance_match_rate(primary), indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "surfaces").mkdir(exist_ok=True)
    for name, surface in surfaces(primary, args.dataset).items():
        surface.to_csv(args.out_dir / "surfaces" / f"{name}.csv", index=False)
    if args.dataset == "d2":
        # a pilot scores the targets it ran; only a full run is bound to the
        # generation's scheduled target list (the bootstrap asserts identity)
        scheduled = None if pilot else (generation or {}).get("scheduled_tics")
        table, contrasts = d2_cluster_bootstrap(per_star, scheduled, pilot)
        table.to_csv(args.out_dir / "d2_cluster_completeness.csv", index=False)
        contrasts.to_csv(args.out_dir / "d2_scenario_contrasts.csv", index=False)
    if args.dataset == "d3":
        (args.out_dir / "ppv.csv").write_text(
            pd.DataFrame([ppv_d3(per_star)]).to_csv(index=False), encoding="utf-8")
    # the Gaussian-null / control FP audit needs the FULL frame (arms retained)
    fp_frequency_distribution(per_star, args.dataset).to_csv(
        args.out_dir / "fp_frequency_distribution.csv", index=False)
    qc_frame = (pd.read_csv(args.crossmatch_qc, dtype={"source_id": str})
                if args.crossmatch_qc else None)
    if qc_frame is not None:
        inputs[str(args.crossmatch_qc)] = sha256_file(args.crossmatch_qc)
    sensitivity_table(per_star, args.dataset, qc_frame).to_csv(
        args.out_dir / "sensitivity.csv", index=False)

    attrition = {
        "roster": len(truth),
        "scored": len(per_star),
        "missing_star_json": len(missing),
        "missing_ids_first5": missing[:5],
        "census_available": int(per_star["census_variable"].notna().sum()),
        "platform_boundary_sensitive": int(per_star["platform_boundary_sensitive"].sum()),
        "provenance_verified": int(per_star["prov_valid"].astype(bool).sum()),
    }
    manifest = {
        "dataset": args.dataset,
        "pilot": pilot,
        "confirmatory_allowed": not pilot,
        "generation_id": (generation or {}).get("generation_id", ""),
        "replay_attestation": attestation_record,
        "spec_sha256": sha256_file(REPO_ROOT / "generalization/METRICS_SPEC.md"),
        "attrition": attrition,
        "inputs_sha256_count": len(inputs),
        "inputs_sha256_digest": hashlib.sha256(
            json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
        "env": env_versions(),
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
    }
    if campaign_file_shas() != campaign_shas_start:
        raise SystemExit("campaign code changed while metrics were running")
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "inputs_sha256.json").write_text(
        json.dumps(inputs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.out_dir / "attrition.csv").write_text(
        pd.DataFrame([attrition]).to_csv(index=False), encoding="utf-8")
    print(json.dumps(attrition, indent=2))
    print(f"[metrics] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
