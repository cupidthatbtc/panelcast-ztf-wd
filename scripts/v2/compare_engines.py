#!/usr/bin/env python3
"""Frozen-vs-v2 paired comparison on one half of the split (V2_PLAN.md §6).

Frames are built from the split ROSTER (every roster id of the half, the
`dev_smoke` class excluded), never from the intersection of the two tables
(G-review 2026-09-02 finding 5): an id without a result is a failure in both
arms; an id of the runner list without a v2 row is an unexplained loss and
aborts. Inputs: the frozen arm's per_star.csv (full run), the v2 arm's
per_star.csv (metrics --engine v2 on the half's registered run), the split,
the half, the runner list.

Endpoints (D3): P1 detection (flag1 roster), P2 dominant-frequency recovery
on the FROZEN P2 frame (Mo-joined, freq-scorable, eligible, frozen-usable; a
v2 unavailable result counts as non-recovery) with the both-arms-usable frame
as sensitivity, P3 negative trigger (flag0 roster), P3 by pass. (D2): P5-style
Gaussian false-alarm on the nulls (exact one-sided Clopper–Pearson upper; the
half has 500 nulls, so even 0/500 has U95 = 0.6 % — a descriptive screen, not
the frozen P5 decision), P4 nominal arm-B recovery and trigger in the eligible
and usable variants (target means over scheduled strata; common-draw target
bootstrap), and the target-clustered injected-vs-paired-control contrasts.
Statistics: per-arm Wilson 95 %, paired difference v2 − frozen with a seeded
star (or target) bootstrap (B = 2000, seed 20260902; no discordant pairs ->
the exact discordance bound [-U95, +U95], U95 the one-sided Clopper-Pearson
upper bound of the discordance proportion at 0 of n, flagged), exact
two-sided McNemar on discordant pairs. The pre-declared STRONG reading is a
descriptive operational screen, not a hypothesis test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))
from metrics_generalization import classify_match, cp_one_sided_bounds, wilson  # noqa: E402

CANONICAL_REGISTRATION = (REPO_ROOT / "generalization" / "v2").resolve()

BOOTSTRAP_B = 2000
BOOTSTRAP_SEED = 20260902
MISSING_ROW = {"best_status": "missing", "low_status": "missing", "high_status": "missing",
               "low_available": False, "high_available": False,
               "best_candidate_matches_dominant": "unscored"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bool(series: pd.Series) -> np.ndarray:
    return series.astype(str).str.lower().eq("true").to_numpy()


def confirmed(frame: pd.DataFrame) -> np.ndarray:
    return frame["best_status"].astype(str).eq("confirmed").to_numpy()


def recovered(frame: pd.DataFrame) -> np.ndarray:
    return confirmed(frame) & frame["best_candidate_matches_dominant"].astype(str).eq("direct").to_numpy()


def usable(frame: pd.DataFrame) -> np.ndarray:
    present = ~frame["best_status"].astype(str).eq("missing").to_numpy()
    return present & _bool(frame["low_available"]) & _bool(frame["high_available"])


def mcnemar_exact(a: np.ndarray, b: np.ndarray) -> tuple[int, int, float]:
    frozen_only = int(np.sum(a & ~b))
    v2_only = int(np.sum(~a & b))
    n = frozen_only + v2_only
    if n == 0:
        return frozen_only, v2_only, 1.0
    p = float(stats.binomtest(min(frozen_only, v2_only), n, 0.5, alternative="two-sided").pvalue)
    return frozen_only, v2_only, min(1.0, p)


def paired_rate_row(endpoint: str, frame_label: str, frozen: np.ndarray, v2: np.ndarray,
                    rng: np.random.Generator, interval: str = "wilson") -> dict:
    n = int(frozen.size)
    row = {"endpoint": endpoint, "frame": frame_label, "n": n, "interval": interval}
    for label, x in (("frozen", frozen), ("v2", v2)):
        k = int(x.sum())
        if n == 0:
            p, lo, hi = math.nan, math.nan, math.nan
        elif interval == "cp_upper":
            p, lo, hi = k / n, math.nan, cp_one_sided_bounds(k, n)[1]
        else:
            p, lo, hi = wilson(k, n)
        row.update({f"{label}_k": k, f"{label}_p": p, f"{label}_lo": lo, f"{label}_hi": hi})
    if n:
        b, c, p_mc = mcnemar_exact(frozen, v2)
        diff = float(v2.mean() - frozen.mean())
        if b + c == 0:
            # exact discordance bound: with 0 discordant pairs among n the
            # discordance proportion is <= its one-sided 95 % Clopper-Pearson
            # upper bound U, so |difference| <= U
            upper = cp_one_sided_bounds(0, n)[1]
            lo, hi, note = -upper, upper, "no discordant pairs: exact discordance bound [-U95, +U95]"
        else:
            idx = rng.integers(0, n, size=(BOOTSTRAP_B, n))
            boots = v2[idx].mean(axis=1) - frozen[idx].mean(axis=1)
            lo, hi = np.quantile(boots, [0.025, 0.975])
            note = ""
        row.update({"diff": diff, "diff_lo": float(lo), "diff_hi": float(hi),
                    "frozen_only": b, "v2_only": c, "mcnemar_exact_p": p_mc, "note": note})
    else:
        row.update({"diff": math.nan, "diff_lo": math.nan, "diff_hi": math.nan,
                    "frozen_only": 0, "v2_only": 0, "mcnemar_exact_p": math.nan, "note": "empty frame"})
    return row


def target_means(frame: pd.DataFrame, outcome: np.ndarray, variant: str) -> tuple[np.ndarray, np.ndarray]:
    """Per-target mean over strata of `outcome` on nominal arm-B windows.
    eligible: denominator = n_strata_scheduled (missing/unusable windows count
    0); usable: mean over usable windows, targets with none excluded."""
    targets = np.unique(frame["cluster"].astype(str).to_numpy())
    values, keep = [], []
    use = usable(frame)
    for t in targets:
        mask = frame["cluster"].astype(str).to_numpy() == t
        if variant == "eligible":
            scheduled = int(pd.to_numeric(frame.loc[mask, "n_strata_scheduled"]).max())
            values.append(float(outcome[mask].sum()) / max(scheduled, 1))
            keep.append(True)
        else:
            m = mask & use
            values.append(float(outcome[m].mean()) if m.any() else math.nan)
            keep.append(bool(m.any()))
    return np.array(values), np.array(keep)


def d2_target_rows(frozen: pd.DataFrame, v2: pd.DataFrame, rng: np.random.Generator, suffix: str) -> list[dict]:
    rows = []
    fb_mask = (frozen["arm"] == "B") & (frozen["scenario"] == "nominal")
    fb, vb = frozen[fb_mask].reset_index(drop=True), v2[fb_mask.to_numpy()].reset_index(drop=True)
    for endpoint, fn in (("P4_recovery", recovered), ("P4_trigger", confirmed)):
        for variant in ("eligible", "usable"):
            f_t, f_keep = target_means(fb, fn(fb), variant)
            v_t, v_keep = target_means(vb, fn(vb), variant)
            keep = f_keep & v_keep if variant == "usable" else np.ones(f_t.size, dtype=bool)
            f_t, v_t = f_t[keep], v_t[keep]
            n = int(f_t.size)
            idx = rng.integers(0, n, size=(BOOTSTRAP_B, n)) if n else np.zeros((BOOTSTRAP_B, 0), dtype=int)
            fboot = f_t[idx].mean(axis=1) if n else np.full(BOOTSTRAP_B, math.nan)
            vboot = v_t[idx].mean(axis=1) if n else np.full(BOOTSTRAP_B, math.nan)
            rows.append({
                "endpoint": f"{endpoint}_{variant}", "frame": f"d2 nominal B targets, {variant}{suffix}", "n": n,
                "interval": "target_bootstrap",
                "frozen_k": float(np.nansum(f_t)), "frozen_p": float(np.nanmean(f_t)) if n else math.nan,
                "frozen_lo": float(np.nanquantile(fboot, 0.025)), "frozen_hi": float(np.nanquantile(fboot, 0.975)),
                "v2_k": float(np.nansum(v_t)), "v2_p": float(np.nanmean(v_t)) if n else math.nan,
                "v2_lo": float(np.nanquantile(vboot, 0.025)), "v2_hi": float(np.nanquantile(vboot, 0.975)),
                "diff": float(np.nanmean(v_t - f_t)) if n else math.nan,
                "diff_lo": float(np.nanquantile(vboot - fboot, 0.025)),
                "diff_hi": float(np.nanquantile(vboot - fboot, 0.975)),
                "frozen_only": int(np.sum(f_t > v_t)), "v2_only": int(np.sum(v_t > f_t)),
                "mcnemar_exact_p": math.nan,
                "note": "n_targets_zero_usable_strata excluded" if variant == "usable" else "",
            })
    return rows


def _strict_recovery(table: pd.DataFrame, sid: str, primary: float, baseline: float) -> float:
    """confirmed AND the candidate frequency directly matches the partner's
    injected dominant frequency (frozen classify_match, tol 1.5 / T)."""
    if str(table.loc[sid, "best_status"]) != "confirmed":
        return 0.0
    freq = table.loc[sid, "best_frequency_per_day"]
    if pd.isna(freq) or pd.isna(primary):
        return 0.0
    return float(classify_match(float(freq), [float(primary)], 1.5 / baseline) == "direct")


def d2_control_contrast_rows(frozen: pd.DataFrame, v2: pd.DataFrame, rng: np.random.Generator,
                             suffix: str) -> list[dict]:
    """Target-clustered injected-vs-paired-control contrasts per arm
    (D_b − D_c for the trigger; R_b − R_c for strict recovery, the control
    scored against its partner's injected dominant frequency), averaged per
    target, and the arm difference."""
    rows = []
    by_sid = {"frozen": frozen.set_index("sid"), "v2": v2.set_index("sid")}
    b = frozen[(frozen["arm"] == "B") & (frozen["scenario"] == "nominal")]
    b = b[b["control_campaign_id"].astype(str).str.len() > 0]
    contrasts = {kind: {"frozen": {}, "v2": {}} for kind in ("trigger", "strict_recovery")}
    n_pairs = 0
    for r in b.itertuples(index=False):
        control = str(r.control_campaign_id)
        if control not in by_sid["frozen"].index or control not in by_sid["v2"].index:
            continue
        n_pairs += 1
        primary = float(r.primary_freq) if not pd.isna(r.primary_freq) else math.nan
        for arm in ("frozen", "v2"):
            table = by_sid[arm]
            d_b = float(str(table.loc[r.sid, "best_status"]) == "confirmed")
            d_c = float(str(table.loc[control, "best_status"]) == "confirmed")
            contrasts["trigger"][arm].setdefault(str(r.cluster), []).append(d_b - d_c)
            baseline_b = float(table.loc[r.sid, "baseline_days"]) if not pd.isna(table.loc[r.sid, "baseline_days"]) else math.nan
            baseline_c = float(table.loc[control, "baseline_days"]) if not pd.isna(table.loc[control, "baseline_days"]) else math.nan
            r_b = _strict_recovery(table, r.sid, primary, baseline_b) if baseline_b > 0 else 0.0
            r_c = _strict_recovery(table, control, primary, baseline_c) if baseline_c > 0 else 0.0
            contrasts["strict_recovery"][arm].setdefault(str(r.cluster), []).append(r_b - r_c)
    for kind, per_arm in contrasts.items():
        targets = sorted(per_arm["frozen"])
        f_t = np.array([np.mean(per_arm["frozen"][t]) for t in targets])
        v_t = np.array([np.mean(per_arm["v2"][t]) for t in targets])
        n = len(targets)
        if n:
            idx = rng.integers(0, n, size=(BOOTSTRAP_B, n))
            fboot, vboot = f_t[idx].mean(axis=1), v_t[idx].mean(axis=1)
        else:
            fboot = vboot = np.full(BOOTSTRAP_B, math.nan)
        rows.append({
            "endpoint": f"control_contrast_{kind}",
            "frame": f"d2 injected-minus-paired-control ({kind}), {n} targets, {n_pairs} pairs{suffix}",
            "n": n, "interval": "target_bootstrap",
            "frozen_k": math.nan, "frozen_p": float(f_t.mean()) if n else math.nan,
            "frozen_lo": float(np.quantile(fboot, 0.025)), "frozen_hi": float(np.quantile(fboot, 0.975)),
            "v2_k": math.nan, "v2_p": float(v_t.mean()) if n else math.nan,
            "v2_lo": float(np.quantile(vboot, 0.025)), "v2_hi": float(np.quantile(vboot, 0.975)),
            "diff": float((v_t - f_t).mean()) if n else math.nan,
            "diff_lo": float(np.quantile(vboot - fboot, 0.025)), "diff_hi": float(np.quantile(vboot - fboot, 0.975)),
            "frozen_only": int(np.sum(f_t > v_t)), "v2_only": int(np.sum(v_t > f_t)), "mcnemar_exact_p": math.nan,
            "note": "pairs whose control lacks a result in either arm are dropped (count in frame)",
        })
    return rows


def endpoints(dataset: str, frozen: pd.DataFrame, v2: pd.DataFrame, suffix: str = "") -> list[dict]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows: list[dict] = []
    if dataset == "d3":
        pos = frozen["class_label"].eq("dsct_flag1").to_numpy()
        neg = frozen["class_label"].eq("dsct_flag0").to_numpy()
        rows.append(paired_rate_row("P1_detection", f"d3 flag1 roster{suffix}",
                                    confirmed(frozen)[pos], confirmed(v2)[pos], rng))
        frozen_p2 = pos & _bool(frozen["freq_scorable"]) & _bool(frozen["eligible_any_pass"]) & usable(frozen)
        rows.append(paired_rate_row("P2_recovery", f"d3 frozen P2 frame (Mo-joined, eligible, frozen-usable){suffix}",
                                    recovered(frozen)[frozen_p2], recovered(v2)[frozen_p2], rng))
        both = frozen_p2 & usable(v2)
        rows.append(paired_rate_row("P2_recovery_both_usable", f"d3 P2 frame usable in both arms (sensitivity){suffix}",
                                    recovered(frozen)[both], recovered(v2)[both], rng))
        rows.append(paired_rate_row("P3_negative_trigger", f"d3 flag0 roster{suffix}",
                                    confirmed(frozen)[neg], confirmed(v2)[neg], rng))
        for pass_name in ("low", "high"):
            f_pass = frozen[f"{pass_name}_status"].astype(str).eq("confirmed").to_numpy()
            v_pass = v2[f"{pass_name}_status"].astype(str).eq("confirmed").to_numpy()
            rows.append(paired_rate_row(f"P3_negative_trigger_{pass_name}", f"d3 flag0, {pass_name} pass{suffix}",
                                        f_pass[neg], v_pass[neg], rng))
    else:
        nulls = frozen["arm"].eq("gauss_null").to_numpy()
        rows.append(paired_rate_row("P5_gaussian_false_alarm", f"d2 Gaussian nulls (half; descriptive screen){suffix}",
                                    confirmed(frozen)[nulls], confirmed(v2)[nulls], rng, interval="cp_upper"))
        rows.extend(d2_target_rows(frozen, v2, rng, suffix))
        rows.extend(d2_control_contrast_rows(frozen, v2, rng, suffix))
    return rows


def transitions(frozen: pd.DataFrame, v2: pd.DataFrame, group: str, column: str) -> pd.DataFrame:
    table = pd.crosstab([frozen[group].astype(str).to_numpy(), frozen[column].astype(str).to_numpy()],
                        v2[column].astype(str).to_numpy())
    table.index.names = [group, f"frozen_{column}"]
    table.columns.name = f"v2_{column}"
    return table.reset_index()


def build_frames(dataset: str, half: str, split: pd.DataFrame, frozen: pd.DataFrame, v2: pd.DataFrame,
                 runner_ids: set[str]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    roster = split[(split["dataset"] == dataset) & (split["split"] == half)]
    if dataset == "d2":
        roster = roster[roster["sid"].isin(runner_ids)]   # the half's registered D2 subset
    ids = sorted(roster["sid"])
    frozen = frozen.set_index("sid")
    v2 = v2.set_index("sid")
    missing_frozen = [sid for sid in ids if sid not in frozen.index]
    if missing_frozen:
        raise SystemExit(f"{len(missing_frozen)} roster ids absent from the frozen table (e.g. {missing_frozen[:3]})")
    unexplained = [sid for sid in ids if sid in runner_ids and sid not in v2.index]
    if unexplained:
        raise SystemExit(f"{len(unexplained)} runner ids have no v2 row (e.g. {unexplained[:3]})")
    frozen_frame = frozen.loc[ids].reset_index()
    v2_rows = []
    for sid in ids:
        if sid in v2.index:
            v2_rows.append(v2.loc[sid].to_dict() | {"sid": sid})
        else:
            v2_rows.append({**frozen.loc[sid].to_dict(), **MISSING_ROW, "sid": sid})
    v2_frame = pd.DataFrame(v2_rows)
    for column in ("class_label", "arm", "scenario", "cluster", "freq_scorable", "eligible_any_pass",
                   "n_strata_scheduled", "control_campaign_id"):
        if column in frozen_frame.columns:
            v2_frame[column] = frozen_frame[column].to_numpy()
    counts = {"roster_ids": len(ids), "v2_missing_no_shard": int(sum(sid not in v2.index for sid in ids)),
              "v2_missing_status": int((v2_frame["best_status"].astype(str) == "missing").sum()),
              "frozen_missing_status": int((frozen_frame["best_status"].astype(str) == "missing").sum())}
    return frozen_frame, v2_frame, counts


def verify_registration(args, registration: Path, runner_ids: set[str]) -> dict:
    """Bind the comparison to the registration (round-2 findings 8 and 12):
    the canonical split and runner list (SHAs from split_manifest.json), the
    v2 run manifest (engine, half, list and split SHAs, canonical
    registration), both metrics manifests (the v2 one bound to the run
    manifest), and — for the holdout — the lock file and the constants
    artifact. Returns the record written to the output manifest."""
    manifest = json.loads((registration / "split_manifest.json").read_text(encoding="utf-8"))
    dataset, half = args.dataset, args.half
    split_sha, runner_sha = sha256_file(args.split), sha256_file(args.runner_list)
    if args.split.resolve() != (registration / "split.csv").resolve() or manifest["outputs"]["split.csv"] != split_sha:
        raise SystemExit("--split must be the registered generalization/v2/split.csv")
    if manifest["outputs"].get(f"{dataset}_{half}.txt") != runner_sha:
        raise SystemExit(f"--runner-list is not the registered {dataset}_{half}.txt")
    listed = {line.strip() for line in args.runner_list.read_text().splitlines() if line.strip()}
    if listed != runner_ids:
        raise SystemExit("runner list mismatch")
    run_manifest = json.loads(args.v2_run_manifest.read_text(encoding="utf-8"))
    binding = run_manifest.get("binding", {})
    problems = []
    if run_manifest.get("engine") != "v2":
        problems.append("run manifest engine")
    if not str(run_manifest.get("dataset", "")).startswith(dataset):
        problems.append("run manifest dataset")
    if binding.get("split_half") != half:
        problems.append("run manifest half")
    if binding.get("stars_file_sha256") != runner_sha:
        problems.append("run manifest stars_file_sha256")
    if binding.get("split_sha256") != split_sha:
        problems.append("run manifest split_sha256")
    if run_manifest.get("canonical_registration") is not True:
        problems.append("run manifest canonical_registration")
    if list(run_manifest.get("passes", [])) != ["low", "high"]:
        problems.append("run manifest passes are not exactly ['low', 'high']")
    if run_manifest.get("limit") is not None:
        problems.append("run manifest used --limit")
    v2_metrics = json.loads((args.v2_metrics_dir / "manifest.json").read_text(encoding="utf-8"))
    frozen_metrics = json.loads((args.frozen_metrics_dir / "manifest.json").read_text(encoding="utf-8"))
    if v2_metrics.get("engine") != "v2" or v2_metrics.get("dataset") != dataset:
        problems.append("v2 metrics manifest engine/dataset")
    if v2_metrics.get("replay_attestation", {}).get("run_manifest_sha256") != sha256_file(args.v2_run_manifest):
        problems.append("v2 metrics manifest is not bound to this run manifest")
    if frozen_metrics.get("engine", "frozen") != "frozen" or frozen_metrics.get("dataset") != dataset:
        problems.append("frozen metrics manifest engine/dataset")
    if frozen_metrics.get("pilot"):
        problems.append("frozen metrics bundle is a pilot")
    for directory in (args.frozen_metrics_dir, args.v2_metrics_dir):
        if not (directory / "per_star.csv").exists():
            problems.append(f"{directory} lacks per_star.csv")
    if args.frozen_per_star.resolve() != (args.frozen_metrics_dir / "per_star.csv").resolve() or \
            args.v2_per_star.resolve() != (args.v2_metrics_dir / "per_star.csv").resolve():
        problems.append("per-star tables must be the metrics bundles' own per_star.csv")
    record = {"split_sha256": split_sha, "runner_list_sha256": runner_sha,
              "v2_run_manifest_sha256": sha256_file(args.v2_run_manifest),
              "v2_metrics_manifest_sha256": sha256_file(args.v2_metrics_dir / "manifest.json"),
              "frozen_metrics_manifest_sha256": sha256_file(args.frozen_metrics_dir / "manifest.json"),
              "v2_digest": binding.get("v2_digest"), "constants_sha256": binding.get("constants_sha256")}
    if half == "holdout":
        lock_path = registration / f"HOLDOUT_LAUNCH_{dataset}.json"
        if not lock_path.exists():
            problems.append("holdout lock file missing")
        else:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            for key in ("stars_file_sha256", "constants_sha256", "v2_digest", "split_sha256", "plan_sha256",
                        "preregistration_commit", "constants_artifact_sha256"):
                if lock.get(key) != binding.get(key):
                    problems.append(f"lock vs run manifest: {key}")
            if lock.get("canonical_registration") is not True:
                problems.append("holdout lock is not from the canonical registration")
            if list(lock.get("passes", [])) != list(run_manifest.get("passes", [])) or \
                    list(lock.get("passes", [])) != ["low", "high"]:
                problems.append("lock vs run manifest: passes")
            if lock.get("frozen_digest") != binding.get("frozen_digest"):
                problems.append("lock vs run manifest: frozen_digest")
            env_digest = hashlib.sha256(json.dumps(run_manifest.get("env", {}), sort_keys=True).encode()).hexdigest()
            if lock.get("env_digest") != env_digest:
                problems.append("lock vs run manifest: env_digest")
            if lock.get("shard_index_sha256") != run_manifest.get("shard_index_sha256"):
                problems.append("lock vs run manifest: shard_index_sha256")
            if not run_manifest.get("holdout_registration") or \
                    run_manifest["holdout_registration"].get("lock_file", "").split("/")[-1] != lock_path.name:
                problems.append("run manifest holdout registration record")
            if args.constants_artifact is None or sha256_file(args.constants_artifact) != lock.get("constants_artifact_sha256"):
                problems.append("constants artifact missing or not the locked one")
            else:
                # V2_PLAN.md §10, 2026-09-04: the lock and the artifact bind the veto amendment commit
                # and the pre-amendment digest of the (re-scored, never rerun) dev runs
                from v2_common import DEV_RUNS_V2_DIGEST, VETO_AMENDMENT_COMMIT
                artifact = json.loads(args.constants_artifact.read_text(encoding="utf-8"))
                if lock.get("veto_amendment_commit") != VETO_AMENDMENT_COMMIT or \
                        artifact.get("veto_amendment_commit") != VETO_AMENDMENT_COMMIT:
                    problems.append("lock / constants artifact: veto_amendment_commit")
                if lock.get("dev_runs_v2_digest") != DEV_RUNS_V2_DIGEST or \
                        artifact.get("dev_runs_v2_digest") != DEV_RUNS_V2_DIGEST or len(artifact.get("dev_runs", [])) != 4:
                    problems.append("lock / constants artifact: dev-run digest and manifests")
                record["veto_amendment_commit"] = lock.get("veto_amendment_commit")
                record["dev_runs_v2_digest"] = lock.get("dev_runs_v2_digest")
            record["holdout_lock_sha256"] = sha256_file(lock_path)
            record["constants_artifact_sha256"] = lock.get("constants_artifact_sha256")
    if problems:
        raise SystemExit(f"registration binding failed: {problems}")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("d2", "d3"), required=True)
    parser.add_argument("--frozen-per-star", type=Path, required=True)
    parser.add_argument("--v2-per-star", type=Path, required=True)
    parser.add_argument("--split", type=Path, default=REPO_ROOT / "generalization/v2/split.csv")
    parser.add_argument("--half", choices=("dev", "holdout"), required=True)
    parser.add_argument("--runner-list", type=Path, required=True,
                        help="the registered id list the v2 run used (e.g. generalization/v2/d3_holdout.txt)")
    parser.add_argument("--v2-run-manifest", type=Path, required=True, help="the v2 run's manifest.json")
    parser.add_argument("--frozen-metrics-dir", type=Path, required=True, help="frozen metrics bundle (manifest + chance_match)")
    parser.add_argument("--v2-metrics-dir", type=Path, required=True, help="v2 metrics bundle (manifest + chance_match)")
    parser.add_argument("--constants-artifact", type=Path, default=None, help="required for the holdout")
    parser.add_argument("--registration-root", type=Path, default=CANONICAL_REGISTRATION,
                        help="tests only; a non-canonical root is recorded and the run manifest must still be canonical")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    split = pd.read_csv(args.split, dtype=str)
    frozen_all = pd.read_csv(args.frozen_per_star, dtype={"sid": str, "cluster": str, "control_campaign_id": str})
    v2_all = pd.read_csv(args.v2_per_star, dtype={"sid": str, "cluster": str, "control_campaign_id": str})
    runner_ids = {line.strip() for line in args.runner_list.read_text().splitlines() if line.strip()}
    registration = verify_registration(args, args.registration_root.resolve(), runner_ids)
    frozen, v2, counts = build_frames(args.dataset, args.half, split, frozen_all, v2_all, runner_ids)

    rows = endpoints(args.dataset, frozen, v2)
    chance, chance_files = {}, {}
    for label, directory in (("frozen", args.frozen_metrics_dir), ("v2", args.v2_metrics_dir)):
        path = directory / "chance_match.json"
        if args.dataset == "d3":
            if not path.exists():
                raise SystemExit(f"{path} is required (chance-match rate beside P2)")
            payload = json.loads(path.read_text(encoding="utf-8"))
            for key in ("accidental_direct_match_rate_mean", "accidental_direct_match_rate_p95", "permutations"):
                value = payload.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                    raise SystemExit(f"{path}: required chance-match field {key} is missing or not finite")
            if int(payload["permutations"]) < 1:
                raise SystemExit(f"{path}: chance-match has no permutations")
            chance[label] = payload
            chance_files[str(path)] = sha256_file(path)
        elif path.exists():
            chance[label] = json.loads(path.read_text(encoding="utf-8"))
            chance_files[str(path)] = sha256_file(path)
    for row in rows:
        if row["endpoint"].startswith("P2"):
            for label in ("frozen", "v2"):
                row[f"{label}_chance_direct_mean"] = chance[label]["accidental_direct_match_rate_mean"]
                row[f"{label}_chance_direct_p95"] = chance[label]["accidental_direct_match_rate_p95"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(args.out_dir / "endpoints.csv", index=False, lineterminator="\n")
    group = "class_label" if args.dataset == "d3" else "arm"
    transitions(frozen, v2, group, "best_status").to_csv(
        args.out_dir / "status_transitions.csv", index=False, lineterminator="\n")
    avail = pd.DataFrame({"frozen_usable": usable(frozen), "v2_usable": usable(v2), group: frozen[group]})
    avail.groupby([group, "frozen_usable", "v2_usable"]).size().reset_index(name="n").to_csv(
        args.out_dir / "availability_transitions.csv", index=False, lineterminator="\n")
    smoke = split[(split["dataset"] == args.dataset) & (split["split"] == "dev_smoke")]["sid"].tolist()
    inputs = {str(p): sha256_file(p) for p in (args.frozen_per_star, args.v2_per_star, args.split,
                                                args.runner_list, args.v2_run_manifest, Path(__file__).resolve(),
                                                args.frozen_metrics_dir / "manifest.json",
                                                args.v2_metrics_dir / "manifest.json")}
    if args.constants_artifact is not None:
        inputs[str(args.constants_artifact)] = sha256_file(args.constants_artifact)
    inputs.update(chance_files)
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "dataset": args.dataset, "half": args.half, "frames": counts,
        "registration": registration,
        "smoke_sids_excluded": smoke,
        "statistics": {"per_arm_interval": "Wilson 95 % (CP upper for nulls)",
                       "paired_difference": f"star/target bootstrap B={BOOTSTRAP_B} seed={BOOTSTRAP_SEED}",
                       "mcnemar": "exact two-sided on discordant pairs",
                       "reading": "STRONG/other = descriptive operational screen, not a hypothesis test"},
        "chance_match": chance,
        "inputs_sha256": inputs,
    }, indent=2) + "\n", encoding="utf-8")
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(table[["endpoint", "n", "frozen_k", "frozen_p", "v2_k", "v2_p", "diff", "diff_lo",
                     "diff_hi", "mcnemar_exact_p"]].to_string(index=False))
    print(f"[compare_engines] wrote {args.out_dir} frames={counts}")


if __name__ == "__main__":
    main()
