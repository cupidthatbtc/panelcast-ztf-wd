#!/usr/bin/env python3
"""Campaign metrics per METRICS_SPEC.md — the spec's names are binding.

Reads per-star JSONs directly (never only a summary CSV), scores the match
taxonomy against dataset truth, and emits the spec's output files. Datasets:

  d1  published 2026-08-01 bundle (19 labeled WDs inside the 928 catalog);
      truth = Jestin roster + literature periods; census = published CSV.
  d3  campaign Kepler dSct run; truth = roster_d3.csv + Mo+2026 frequencies;
      census = build_panels_generic output.
  d2  campaign injection run; truth = shard_manifest.csv + d2_modes.csv;
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
AMP_EDGES = {"d1": [0.5, 1, 2, 5, 10, 20, 50, 200],
             "d3": [0.5, 1, 2, 5, 10, 20, 50, 200],
             "d2": [0.5, 2, 5, 10, 30, 100]}


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
    classes: set[str] = set()
    for f_t in truth:
        if abs(freq - f_t) <= tol:
            classes.add("direct")
        elif abs(freq - 2.0 * f_t) <= tol or abs(freq - 0.5 * f_t) <= tol:
            classes.add("harmonic")
        else:
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
    # status "missing" (no usable light curve) fires no L-S rule
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
        row[f"{name}_eligible"] = pass_eligible(truth_freqs, name, baseline)
        for peak in p.get("top_peaks", []):
            f_peak = peak.get("frequency_per_day")
            if f_peak is not None and truth_freqs and \
               classify_match(float(f_peak), truth_freqs, tol) == "direct":
                any_direct_top = True
    best_freq = row["best_frequency_per_day"]
    row["best_match"] = (
        classify_match(float(best_freq), truth_freqs, tol)
        if best_freq is not None and truth_freqs else "unscored"
    )
    row["best_match_primary"] = (
        classify_match(float(best_freq), [primary_freq], tol)
        if best_freq is not None and primary_freq is not None else "unscored"
    )
    row["matched_any_mode_diagnostic"] = any_direct_top
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
        r["source_id"]: {"census_variable": bool(r["census_variable"]),
                         "census_g_nightly": bool(r["census_g_nightly"])}
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
    primary_match = {"d1": "best_match_primary", "d2": "best_match",
                     "d3": "best_match_primary"}[dataset]
    rows = []
    positives = per_star[per_star["label_positive"] == True]  # noqa: E712
    usable = positives[positives["best_status"] != "missing"]
    for pass_name in PASSES:
        status_col = "best_status" if pass_name == "best" else f"{pass_name}_status"
        match_col = primary_match if pass_name == "best" else f"{pass_name}_match"
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
                if scope == "freq_recovery_scorable" and rule in (
                        "confirmed", "confirmed_or_candidate", "either"):
                    success = success & (frame.loc[ok, match_col] == "direct")
                stats = weighted_wilson(
                    success.to_numpy(dtype=float),
                    frame.loc[ok, "weight"].to_numpy(dtype=float),
                )
                rows.append({"pass": pass_name, "rule": rule, "scope": scope, **stats})
    return pd.DataFrame(rows)


def contingency(per_star: pd.DataFrame) -> dict:
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
    if b + c:
        out["mcnemar_exact_p_secondary"] = float(
            binomtest(min(b, c), b + c, 0.5).pvalue * 1.0
        )
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


def d2_cluster_bootstrap(per_star: pd.DataFrame) -> pd.DataFrame:
    frame = per_star[per_star.get("arm").isin(["A", "B"])] if "arm" in per_star else per_star.iloc[0:0]
    if frame.empty:
        return pd.DataFrame()
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    rows = []
    for (arm, k), stratum in frame.groupby(["arm", "template_k"]):
        success = (stratum["best_status"] == "confirmed") & (stratum["best_match"] == "direct")
        per_target = success.groupby(stratum["cluster"]).mean()
        point = float(per_target.mean())
        clusters = per_target.index.to_numpy()
        boots = []
        for _ in range(BOOTSTRAP_B):
            sample = rng.choice(clusters, size=len(clusters), replace=True)
            boots.append(float(per_target.loc[sample].mean()))
        rows.append({"arm": arm, "template_k": int(k), "n_targets": len(clusters),
                     "p": point, "lo": float(np.quantile(boots, 0.025)),
                     "hi": float(np.quantile(boots, 0.975))})
    return pd.DataFrame(rows)


def surfaces(per_star: pd.DataFrame, dataset: str) -> pd.DataFrame:
    positives = per_star[(per_star["label_positive"] == True)  # noqa: E712
                         & per_star["freq_scorable"]]
    if positives.empty:
        return pd.DataFrame()
    amp_edges = AMP_EDGES[dataset]
    rows = []
    p_bins = np.digitize(positives["truth_period_days"], PERIOD_EDGES_DAYS)
    a_bins = np.digitize(positives["amp"], amp_edges)
    success = (positives["best_status"] == "confirmed") & (positives["best_match"] == "direct")
    for (pb, ab), idx in positives.groupby([p_bins, a_bins]).groups.items():
        cell = positives.loc[idx]
        k = int(success.loc[idx].sum())
        n = len(cell)
        entry = {"period_bin": int(pb), "amp_bin": int(ab), "n": n, "k": k}
        if n >= MIN_CELL:
            entry.update(dict(zip(("p", "lo", "hi"), wilson(k, n))))
        rows.append(entry)
    return pd.DataFrame(rows)


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
        for arm, name in (("null", "fpr_gaussian"), ("ctrl", "native_trigger_rate")):
            subset = per_star[per_star["arm"] == arm]
            if subset.empty:
                continue
            fired = subset["best_status"] == "confirmed"
            stats = weighted_wilson(fired.to_numpy(dtype=float),
                                    np.ones(len(subset)))
            rows.append({"quantity": name, "rule": "confirmed", **stats})
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
    args = parser.parse_args()

    assert_frozen()
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
                      "high_status": "missing", "best_match": "unscored",
                      "best_match_primary": "unscored", "low_match": "unscored",
                      "high_match": "unscored", "low_eligible": False,
                      "high_eligible": False, "eligible_any_pass": False,
                      "best_frequency_per_day": None, "baseline_days": math.nan,
                      "matched_any_mode_diagnostic": False,
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

    args.out_dir.mkdir(parents=True, exist_ok=True)
    per_star.drop(columns=["truth_freqs"]).to_csv(
        args.out_dir / "per_star.csv", index=False)
    completeness_tables(per_star, args.dataset).to_csv(
        args.out_dir / "completeness_by_class_pass_rule.csv", index=False)
    (args.out_dir / "contingency_complementarity.json").write_text(
        json.dumps(contingency(per_star), indent=2) + "\n", encoding="utf-8")
    trigger_rates(per_star, args.dataset).to_csv(
        args.out_dir / "trigger_rates.csv", index=False)
    (args.out_dir / "chance_match.json").write_text(
        json.dumps(chance_match_rate(per_star), indent=2) + "\n", encoding="utf-8")
    surface = surfaces(per_star, args.dataset)
    (args.out_dir / "surfaces").mkdir(exist_ok=True)
    surface.to_csv(args.out_dir / "surfaces" / "period_amplitude.csv", index=False)
    if args.dataset == "d2":
        d2_cluster_bootstrap(per_star).to_csv(
            args.out_dir / "d2_cluster_completeness.csv", index=False)

    attrition = {
        "roster": len(truth),
        "scored": len(per_star),
        "missing_star_json": len(missing),
        "missing_ids_first5": missing[:5],
        "census_available": int(per_star["census_variable"].notna().sum()),
    }
    manifest = {
        "dataset": args.dataset,
        "spec_sha256": sha256_file(REPO_ROOT / "generalization/METRICS_SPEC.md"),
        "attrition": attrition,
        "inputs_sha256_count": len(inputs),
        "inputs_sha256_digest": hashlib.sha256(
            json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
        "env": env_versions(),
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
    }
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
