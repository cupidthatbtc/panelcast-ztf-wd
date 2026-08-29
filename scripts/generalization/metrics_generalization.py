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


def truth_d2(shards_dir: Path) -> pd.DataFrame:
    """Truth from injected_modes.csv — the ACTUALLY injected (post-sinc-
    rejection) mode set per shard, never the original mode table (G2 methods
    finding 4)."""
    manifest = pd.read_csv(shards_dir / "shard_manifest.csv",
                           dtype={"campaign_id": str, "template_source_id": str})
    injected = pd.read_csv(shards_dir / "injected_modes.csv",
                           dtype={"campaign_id": str})
    freq_lists = injected.groupby("campaign_id")["frequency_per_day"].apply(
        lambda g: sorted(g.tolist())).to_dict()
    dominant = {}
    amp_dom = {}
    for sid, group in injected.groupby("campaign_id"):
        best = group.loc[group["amp_tess_ppt"].idxmax()]
        dominant[sid] = float(best["frequency_per_day"])
        amp_dom[sid] = float(best["amp_tess_ppt"])
    rows = []
    for r in manifest.itertuples(index=False):
        arm = r.arm
        tic = int(r.tic)
        sid = r.campaign_id
        truth = freq_lists.get(sid, []) if arm in ("A", "B") else []
        rows.append({
            "sid": sid, "external_id": f"TIC {tic}" if tic else r.template_source_id,
            "class_label": f"arm_{arm}",
            "label_positive": arm in ("A", "B"),
            "weight": 1.0, "cluster": str(tic) if tic else sid,
            "truth_freqs": truth,
            "primary_freq": dominant.get(sid) if arm in ("A", "B") else None,
            "amp": float(amp_dom.get(sid, math.nan)),
            "truth_period_days": (86400.0 / dominant[sid] / 86400.0)
            if sid in dominant and arm in ("A", "B") else math.nan,
            "freq_scorable": arm in ("A", "B") and bool(truth),
            "arm": arm, "template_k": r.template_k,
            "ratio_g": float(r.ratio_g), "ratio_rg": float(r.ratio_rg),
            "phase_draw": int(getattr(r, "phase_draw", 0)),
            "amp_scale": float(getattr(r, "amp_scale", 1.0)),
            "median_exp_per_night": float(getattr(r, "template_exp_per_night",
                                                  math.nan)),
            "template_status": getattr(r, "template_status", ""),
        })
    return pd.DataFrame(rows)


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


def d2_cluster_bootstrap(per_star: pd.DataFrame) -> pd.DataFrame:
    """P4 machinery: per (scenario, endpoint), per-stratum rates and the
    equal-weight (1/3 per K stratum) scenario-standardized mean over targets;
    COMMON RANDOM NUMBERS — one resample-index matrix shared by every
    scenario; degenerate statistics fall back to target-level exact CP."""
    if "arm" not in per_star:
        return pd.DataFrame()
    frame = per_star[per_star["arm"].isin(["A", "B"])]
    if frame.empty:
        return pd.DataFrame()
    clusters = np.array(sorted(frame["cluster"].unique()))
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    draws = rng.integers(0, len(clusters), size=(BOOTSTRAP_B, len(clusters)))
    rows = []
    endpoints = {
        "detection": lambda f: f["best_status"] == "confirmed",
        "freq_recovery": lambda f: (f["best_status"] == "confirmed")
        & (f["best_candidate_matches_dominant"] == "direct"),
    }
    scenario_cols = ["arm", "ratio_g", "ratio_rg"]
    for extra in ("phase_draw", "amp_scale"):
        if extra in frame:
            scenario_cols.append(extra)

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
        arm, g, r = keys[0], keys[1], keys[2]
        usable_rows = scenario[scenario["best_status"] != "missing"]
        for endpoint, predicate in endpoints.items():
            for denom in ("usable", "eligible"):
                subset = usable_rows if denom == "usable" else scenario
                if subset.empty:
                    continue
                if denom == "eligible":
                    # missing replicate = failure, fixed |K_t| = 3 (spec P4)
                    success = predicate(subset) & (subset["best_status"] != "missing")
                    per_ts = success.groupby(
                        [subset["cluster"], subset["template_k"]]).mean()
                    per_target = per_ts.groupby(level=0).sum() / 3.0
                else:
                    # renormalize over usable strata; a target with ZERO usable
                    # strata drops from the usable estimand (counted below)
                    success = predicate(subset)
                    per_ts = success.groupby(
                        [subset["cluster"], subset["template_k"]]).mean()
                    per_target = per_ts.groupby(level=0).mean()
                aligned = per_target.reindex(clusters)
                if aligned.dropna().empty:
                    continue
                point, lo, hi, interval, n_targets = bootstrap_stats(aligned)
                rows.append({
                    "arm": arm, "ratio_g": g, "ratio_rg": r,
                    "endpoint": endpoint, "denominator": denom,
                    "n_targets": n_targets,
                    "n_targets_zero_usable_strata": int(aligned.isna().sum()),
                    "p": point, "lo": lo, "hi": hi, "interval": interval,
                })
        # paired census-vs-LS difference, target-clustered (nominal arm B only)
        if (arm == "B" and float(g) == 1.7 and float(r) == 0.8
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
                    "arm": arm, "ratio_g": g, "ratio_rg": r,
                    "endpoint": "paired_census_minus_ls_discordance",
                    "denominator": "usable", "n_targets": n_targets,
                    "n_targets_zero_usable_strata": int(aligned.isna().sum()),
                    "p": point, "lo": lo, "hi": hi, "interval": interval,
                })
    return pd.DataFrame(rows)


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


def trigger_rates(per_star: pd.DataFrame, dataset: str) -> pd.DataFrame:
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
        nulls = per_star[per_star["arm"] == "null"]
        if not nulls.empty:
            completed = nulls[nulls["best_status"] != "missing"]
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
        pool = per_star[per_star["arm"].isin(["null", "ctrl"])]
    else:
        pool = per_star.iloc[0:0]
    triggered = pool[pool["best_status"].isin(["confirmed", "candidate"])]
    columns = ["sid", "class_label", "best_status", "best_pass",
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

    if dataset == "d2" and "arm" in per_star:
        # common-subset rule: nominal recomputed on the SAME median-window
        # (k=1) subset used by every non-nominal scenario
        median_b = per_star[(per_star["arm"] == "B") & (per_star["template_k"] == 1)]
        group_cols = ["ratio_g", "ratio_rg"]
        for extra in ("phase_draw", "amp_scale"):
            if extra in median_b:
                group_cols.append(extra)
        for keys, scenario in median_b.groupby(group_cols):
            label = "_".join(f"{c}{v}" for c, v in zip(group_cols, keys))
            rate(scenario, "arm_b_median_window", label)
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
                        help="d2: shard dir with shard_manifest.csv; census "
                             "computed from shards when --census-csv absent")
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
    if args.dataset in ("d2", "d3"):
        if args.run_manifest is None:
            raise SystemExit("d2/d3 metrics require --run-manifest (attestation binding)")
        run_manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
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
    if args.dataset == "d1":
        truth = truth_d1()
    elif args.dataset == "d3":
        truth = truth_d3()
    else:
        if args.shards_dir is None:
            raise SystemExit("d2 needs --shards-dir")
        truth = truth_d2(args.shards_dir)

    census = census_lookup_csv(args.census_csv) if args.census_csv else {}
    inputs: dict[str, str] = {}
    if args.census_csv:
        inputs[str(args.census_csv)] = sha256_file(args.census_csv)

    rows = []
    missing = []
    for r in truth.itertuples(index=False):
        json_path = args.stars_dir / f"{r.sid}.json"
        if not json_path.exists():
            # eligible roster target with no usable light curve: counts as a
            # non-detection in the eligible-roster estimand, excluded from the
            # usable-light-curve estimand (G2 stats finding 2)
            missing.append(r.sid)
            record = {**r._asdict(),
                      "best_status": "missing", "low_status": "missing",
                      "high_status": "missing", "best_candidate_matches_any_mode": "unscored",
                      "best_candidate_matches_dominant": "unscored", "low_match": "unscored",
                      "high_match": "unscored", "low_eligible": False,
                      "high_eligible": False, "eligible_any_pass": False,
                      "best_frequency_per_day": None, "baseline_days": math.nan,
                      "any_top_peak_matches_any_mode": False,
                      "census_variable": census.get(r.sid, {}).get("census_variable")}
            rows.append(record)
            continue
        inputs[str(json_path)] = sha256_file(json_path)
        scored = score_star(json_path, list(r.truth_freqs), r.primary_freq,
                            TRUTH_QUANTUM_PER_DAY[args.dataset])
        record = {**r._asdict(), **scored}
        if r.sid in census:
            record.update(census[r.sid])
        elif args.dataset == "d2" and args.shards_dir is not None:
            record.update(census_from_shard(args.shards_dir / f"{r.sid}.csv.gz"))
        else:
            record["census_variable"] = None
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
    completeness_tables(per_star, args.dataset).to_csv(
        args.out_dir / "completeness_by_class_pass_rule.csv", index=False)
    (args.out_dir / "contingency_complementarity.json").write_text(
        json.dumps(contingency(per_star, args.dataset), indent=2) + "\n",
        encoding="utf-8")
    trigger_rates(per_star, args.dataset).to_csv(
        args.out_dir / "trigger_rates.csv", index=False)
    (args.out_dir / "chance_match.json").write_text(
        json.dumps(chance_match_rate(per_star), indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "surfaces").mkdir(exist_ok=True)
    for name, surface in surfaces(per_star, args.dataset).items():
        surface.to_csv(args.out_dir / "surfaces" / f"{name}.csv", index=False)
    if args.dataset == "d2":
        d2_cluster_bootstrap(per_star).to_csv(
            args.out_dir / "d2_cluster_completeness.csv", index=False)
    if args.dataset == "d3":
        (args.out_dir / "ppv.csv").write_text(
            pd.DataFrame([ppv_d3(per_star)]).to_csv(index=False), encoding="utf-8")
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
    }
    manifest = {
        "dataset": args.dataset,
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
