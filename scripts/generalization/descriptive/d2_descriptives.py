#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE D2 diagnostics — ruling item 5 (F08/F11/F38).

Admitted by generalization/reviews/G5prep/sol_round2.md (ADMIT-DESCRIPTIVE,
fixed 2026-09-01), a pre-metrics ruling that uses frozen manifests, rosters,
and code schemas only. Three outputs, exactly as ruled:

1. `d2_k_template_status.csv` — nominal arm B only; every
   template_k {0,1,2} x manifest template_status {not_detected, candidate,
   confirmed} x endpoint {recovery, trigger} cell (18 rows, zero cells
   emitted). `trigger` = best status confirmed; `recovery` = trigger AND the
   frozen dominant match is `direct`. The SCHEDULED denominator is the
   manifest's nominal arm-B rows — a scheduled shard with no scored row is a
   failure. `n_usable` (both passes available) is context only: no usable
   rate column. Rates are blank when the denominator is zero.
2. `d2_control_reuse.png` + `_source.csv` + `.meta.json` — from the existing
   metrics `d2_control_reuse.csv`: one bar per unique control, sorted by
   descending n_b_assignments then control_campaign_id; assignment count is
   plotted, n_targets stays in the source table.
3. `d2_arm_a_b_pairs.csv` — exactly one nominal A and one nominal B row per
   (tic, template_k); template source, W_g, and status metadata must agree.
   D = confirmed; R = confirmed AND dominant direct. Pair classes both /
   A_only / B_only / neither, blank when pair_usable=false. NO aggregate
   contrast, test, or interval.

Every row carries analysis_status=postlaunch_descriptive, prespecified=false,
interval=none. None of these files may enter a headline, endpoint decision,
exclusion, reclassification, or replacement denominator.

FULL-run only: a pilot metrics bundle (manifest.json pilot=true) is refused
unless --allow-pilot is given, in which case every output is stamped
analysis_status=pilot_dev_only (never the ruled status) so the code can be
exercised on the archived gen2 pilot during development.

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive), so committing/pulling it is SHA-neutral for live runners.

Inputs: a completed D2 metrics out-dir (per_star.csv, d2_control_reuse.csv,
manifest.json) and the generation's typed shard manifest (--shards-dir, or
--shard-manifest for an archived copy under another name). Outputs go to
--out-dir (<result>/descriptive_postlaunch) together with
d2_descriptives.README.md (the verbatim disclosure) and
d2_descriptives.manifest.json (input/output SHA-256, script SHA).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)
from d2_truth_model import (  # noqa: E402
    MANIFEST_COLUMN_NAMES,
    MANIFEST_COLUMNS,
    SCENARIO_NOMINAL,
    validate_manifest_frame,
)

ANALYSIS_STATUS = "postlaunch_descriptive"
PILOT_DEV_STATUS = "pilot_dev_only"
PRESPECIFIED = False
INTERVAL = "none"
VERDICT_FILE = "generalization/reviews/G5prep/sol_round2.md"
# verbatim from the ruling (item 5 disclosure), including its \(K\) / \(W_g\)
# markup and the typographic apostrophe; a test checks byte identity
DISCLOSURE = (
    r"Post-launch descriptive D2 diagnostics report nominal arm-B recovery "
    r"and triggering by \(K\) and the template’s published status, the fixed "
    r"control-window reuse pattern, and paired nominal arm-A/arm-B outcomes "
    r"per target and \(K\); the rows expose native-variability and reuse "
    r"confounding, carry no interval, and cannot support an unqualified "
    r"recovery-versus-\(W_g\) trend."
)

K_VALUES = (0, 1, 2)
# K = 0/1/2 are the round-half-even 10/50/90th-percentile W_g positions of
# the magnitude-matched pool (Amendment 4); `wg_stratum` is that fixed label
# for K — the realized W_g values of a cell are in wg_min/wg_median/wg_max
WG_STRATUM_LABELS = {0: "wg_p10", 1: "wg_p50", 2: "wg_p90"}
TEMPLATE_STATUSES = ("not_detected", "candidate", "confirmed")
ENDPOINTS = ("recovery", "trigger")
RULE = "confirmed"
DIRECT = "direct"
MISSING = "missing"
UNSCORED = "unscored"
PAIR_ARMS = ("A", "B")

K_TABLE_COLUMNS = [
    "template_k", "wg_stratum", "template_status", "endpoint",
    "n_scheduled", "n_usable", "k_success", "rate_scheduled",
    "wg_min", "wg_median", "wg_max",
    "analysis_status", "prespecified", "interval",
]
REUSE_INPUT_COLUMNS = ["control_campaign_id", "template_source_id",
                       "n_b_assignments", "n_targets"]
REUSE_SOURCE_COLUMNS = [
    "bar_index", "control_campaign_id", "template_source_id",
    "n_b_assignments", "n_targets",
    "analysis_status", "prespecified", "interval",
]
PAIR_COLUMNS = [
    "tic", "template_k", "template_source_id", "template_status", "wg_contrasts",
    "a_sid", "b_sid", "a_status", "b_status", "a_usable", "b_usable", "pair_usable",
    "D_A", "D_B", "R_A", "R_B", "trigger_pair_class", "recovery_pair_class",
    "analysis_status", "prespecified", "interval",
]
PER_STAR_REQUIRED = (
    "sid", "arm", "scenario", "cluster", "template_k", "template_status",
    "wg_contrasts", "shard_sha256", "best_status",
    "best_candidate_matches_dominant", "low_available", "high_available",
)
OUTCOME_COLUMNS = [
    "campaign_id", "arm", "tic", "template_k", "template_source_id",
    "template_status", "wg_contrasts", "control_campaign_id", "scored",
    "best_status", "dominant_match", "low_available", "high_available",
    "usable", "D", "R",
]
D2_DTYPES = {"str": str, "int": "int64", "float": float, "bool": bool}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_bool(value) -> bool:
    """CSV-robust boolean: True/'True'/'true' -> True; NaN/''/False -> False."""
    return str(value).strip().lower() == "true"


def _status_fields(analysis_status: str) -> dict:
    return {"analysis_status": analysis_status, "prespecified": PRESPECIFIED,
            "interval": INTERVAL}


# ------------------------------------------------------------------- loaders

def load_manifest(path: Path) -> pd.DataFrame:
    """The generation's typed shard manifest (d2_truth_model.MANIFEST_COLUMNS),
    read exactly as the metrics reader does; any schema deviation, NaN in an
    int/bool column, duplicate id, or per-row invariant violation is fatal."""
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
    validate_manifest_frame(manifest)
    return manifest


def load_per_star(path: Path) -> pd.DataFrame:
    per_star = pd.read_csv(path, dtype={"sid": str, "control_campaign_id": str,
                                        "shard_sha256": str, "cluster": str})
    missing = [c for c in PER_STAR_REQUIRED if c not in per_star.columns]
    if missing:
        raise SystemExit(f"{path}: per_star.csv lacks columns {missing}")
    return per_star


# ------------------------------------------------------- scheduled outcomes

def attach_outcomes(manifest: pd.DataFrame, per_star: pd.DataFrame) -> pd.DataFrame:
    """Every SCHEDULED nominal arm-A/arm-B shard (the manifest) joined to its
    scored per_star row. A scheduled shard without a scored row is a failure
    (best_status=missing, unusable). Every scored nominal row must exist in
    the manifest with identical arm/scenario/tic/K/status/W_g/shard SHA —
    any disagreement aborts (fail closed: the outcomes must be THIS
    generation's)."""
    missing_cols = [c for c in PER_STAR_REQUIRED if c not in per_star.columns]
    if missing_cols:
        raise SystemExit(f"per_star lacks columns {missing_cols}")
    if per_star["sid"].duplicated().any():
        raise SystemExit("duplicate sids in per_star")
    nominal = manifest[manifest["arm"].isin(PAIR_ARMS)
                       & (manifest["scenario"] == SCENARIO_NOMINAL)]
    if nominal.empty:
        raise SystemExit("manifest holds no nominal arm-A/arm-B rows")
    scored = per_star.set_index("sid")
    ps_nominal = per_star[per_star["arm"].isin(PAIR_ARMS)
                          & (per_star["scenario"] == SCENARIO_NOMINAL)]
    foreign = sorted(set(ps_nominal["sid"]) - set(nominal["campaign_id"]))
    if foreign:
        raise SystemExit(f"per_star nominal rows absent from the manifest: {foreign[:5]}")
    rows = []
    for r in nominal.itertuples(index=False):
        sid = r.campaign_id
        if sid in scored.index:
            s = scored.loc[sid]
            expected = {
                "arm": (str(s["arm"]), r.arm),
                "scenario": (str(s["scenario"]), r.scenario),
                "tic": (int(s["cluster"]), int(r.tic)),
                "template_k": (int(s["template_k"]), int(r.template_k)),
                "template_status": (str(s["template_status"]), r.template_status),
                "wg_contrasts": (int(s["wg_contrasts"]), int(r.template_wg_contrasts)),
                "shard_sha256": (str(s["shard_sha256"]), r.shard_sha256),
            }
            bad = [name for name, (got, want) in expected.items() if got != want]
            if bad:
                raise SystemExit(f"{sid}: per_star disagrees with the manifest on {bad}")
            best_status = str(s["best_status"])
            dominant_match = str(s["best_candidate_matches_dominant"])
            low = _as_bool(s["low_available"])
            high = _as_bool(s["high_available"])
            was_scored = True
        else:
            best_status, dominant_match = MISSING, UNSCORED
            low = high = False
            was_scored = False
        usable = bool(was_scored and best_status != MISSING and low and high)
        detected = bool(best_status == RULE)
        rows.append({
            "campaign_id": sid, "arm": r.arm, "tic": int(r.tic),
            "template_k": int(r.template_k),
            "template_source_id": r.template_source_id,
            "template_status": r.template_status,
            "wg_contrasts": int(r.template_wg_contrasts),
            "control_campaign_id": r.control_campaign_id,
            "scored": was_scored, "best_status": best_status,
            "dominant_match": dominant_match,
            "low_available": low, "high_available": high, "usable": usable,
            "D": detected, "R": bool(detected and dominant_match == DIRECT),
        })
    return pd.DataFrame(rows, columns=OUTCOME_COLUMNS)


# ------------------------------------------------ 1. K x template status

def k_template_status_table(outcomes: pd.DataFrame,
                            analysis_status: str = ANALYSIS_STATUS) -> pd.DataFrame:
    """Nominal arm B: every K x template_status x endpoint cell over the
    SCHEDULED denominator (missing rows are failures). Pure arithmetic."""
    b = outcomes[outcomes["arm"] == "B"]
    if b.empty:
        raise SystemExit("no scheduled nominal arm-B rows")
    bad_k = sorted(set(b["template_k"]) - set(K_VALUES))
    if bad_k:
        raise SystemExit(f"nominal arm-B template_k outside {{0,1,2}}: {bad_k}")
    bad_status = sorted(set(b["template_status"]) - set(TEMPLATE_STATUSES))
    if bad_status:
        raise SystemExit(f"nominal arm-B template_status outside the published vocabulary: {bad_status}")
    if b.duplicated(["tic", "template_k"]).any():
        raise SystemExit("more than one nominal arm-B row per (tic, K)")
    rows = []
    for k in K_VALUES:
        for status in TEMPLATE_STATUSES:
            cell = b[(b["template_k"] == k) & (b["template_status"] == status)]
            n_scheduled = int(len(cell))
            n_usable = int(cell["usable"].sum())
            wg = cell["wg_contrasts"].to_numpy(dtype=float)
            for endpoint in ENDPOINTS:
                k_success = int((cell["R"] if endpoint == "recovery" else cell["D"]).sum())
                rows.append({
                    "template_k": k, "wg_stratum": WG_STRATUM_LABELS[k],
                    "template_status": status, "endpoint": endpoint,
                    "n_scheduled": n_scheduled, "n_usable": n_usable,
                    "k_success": k_success,
                    "rate_scheduled": k_success / n_scheduled if n_scheduled else math.nan,
                    "wg_min": float(wg.min()) if n_scheduled else math.nan,
                    "wg_median": float(np.median(wg)) if n_scheduled else math.nan,
                    "wg_max": float(wg.max()) if n_scheduled else math.nan,
                    **_status_fields(analysis_status),
                })
    table = pd.DataFrame(rows, columns=K_TABLE_COLUMNS)
    table["wg_min"] = table["wg_min"].astype("Int64")
    table["wg_max"] = table["wg_max"].astype("Int64")
    if len(table) != len(K_VALUES) * len(TEMPLATE_STATUSES) * len(ENDPOINTS):
        raise SystemExit("K x template_status x endpoint grid is incomplete")  # pragma: no cover
    for endpoint in ENDPOINTS:
        sub = table[table["endpoint"] == endpoint]
        if int(sub["n_scheduled"].sum()) != len(b):
            raise SystemExit("scheduled cells do not partition the nominal arm-B rows")  # pragma: no cover
    if ((table["k_success"] > table["n_scheduled"]) | (table["n_usable"] > table["n_scheduled"])).any():
        raise SystemExit("cell count exceeds its scheduled denominator")  # pragma: no cover
    rec = table[table["endpoint"] == "recovery"]["k_success"].to_numpy()
    trig = table[table["endpoint"] == "trigger"]["k_success"].to_numpy()
    if (rec > trig).any():
        raise SystemExit("recovery exceeds trigger in a cell")  # pragma: no cover
    return table


# ------------------------------------------------ 2. control reuse figure

def control_reuse_source(reuse: pd.DataFrame, manifest: pd.DataFrame | None = None,
                         analysis_status: str = ANALYSIS_STATUS) -> pd.DataFrame:
    """The existing d2_control_reuse.csv, one row per unique control, ordered
    as plotted: descending n_b_assignments, then control_campaign_id. When
    the manifest is given, the table must equal its nominal arm-B recount."""
    if list(reuse.columns) != REUSE_INPUT_COLUMNS:
        raise SystemExit(f"d2_control_reuse.csv columns {list(reuse.columns)} != {REUSE_INPUT_COLUMNS}")
    if reuse.empty:
        raise SystemExit("d2_control_reuse.csv is empty")
    if reuse["control_campaign_id"].duplicated().any():
        raise SystemExit("d2_control_reuse.csv is not one row per unique control")
    counts = reuse[["n_b_assignments", "n_targets"]]
    if counts.isna().any().any() or (counts["n_targets"] < 1).any() \
            or (counts["n_b_assignments"] < counts["n_targets"]).any():
        raise SystemExit("d2_control_reuse.csv counts violate n_b_assignments >= n_targets >= 1")
    if manifest is not None:
        nominal_b = manifest[(manifest["arm"] == "B") & (manifest["scenario"] == SCENARIO_NOMINAL)]
        recount = (nominal_b.groupby(["control_campaign_id", "template_source_id"])
                   .agg(n_b_assignments=("campaign_id", "size"), n_targets=("tic", "nunique"))
                   .reset_index())
        key = ["control_campaign_id", "template_source_id"]
        got = reuse.astype({"n_b_assignments": int, "n_targets": int}).sort_values(key).reset_index(drop=True)
        want = recount.astype({"n_b_assignments": int, "n_targets": int}).sort_values(key).reset_index(drop=True)
        if not got[REUSE_INPUT_COLUMNS].equals(want[REUSE_INPUT_COLUMNS]):
            raise SystemExit("d2_control_reuse.csv does not equal the manifest's nominal arm-B recount")
    ordered = reuse.sort_values(["n_b_assignments", "control_campaign_id"],
                                ascending=[False, True], kind="mergesort").reset_index(drop=True)
    ordered.insert(0, "bar_index", np.arange(len(ordered)))
    for name, value in _status_fields(analysis_status).items():
        ordered[name] = value
    return ordered[REUSE_SOURCE_COLUMNS]


def plot_control_reuse(source: pd.DataFrame, png_path: Path, analysis_status: str) -> None:
    n = len(source)
    heights = source["n_b_assignments"].to_numpy(dtype=int)
    fig, ax = plt.subplots(figsize=(max(6.0, min(18.0, 0.12 * n + 2.0)), 4.2))
    ax.bar(source["bar_index"].to_numpy(), heights, width=0.8, color="#4c72b0", linewidth=0)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(0, int(heights.max()) + 1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel("nominal arm-B assignments (n_b_assignments)")
    ax.set_xlabel("unique paired control window, sorted by descending "
                  "n_b_assignments then control_campaign_id")
    if n <= 120:
        ax.set_xticks(source["bar_index"].to_numpy())
        ax.set_xticklabels(source["control_campaign_id"].astype(str), rotation=90, fontsize=5)
    else:
        ax.set_xticks([])
    ax.set_title("D2 control-window reuse (descriptive, post-launch)")
    ax.text(0.99, 0.97,
            f"{n} unique controls; {int(heights.sum())} nominal arm-B assignments\n"
            f"analysis_status={analysis_status}; prespecified=false; interval=none",
            transform=ax.transAxes, ha="right", va="top", fontsize=8)
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------- 3. paired A/B table

def pair_class(a: bool, b: bool) -> str:
    if a and b:
        return "both"
    if a:
        return "A_only"
    if b:
        return "B_only"
    return "neither"


def arm_a_b_pairs(outcomes: pd.DataFrame,
                  analysis_status: str = ANALYSIS_STATUS) -> pd.DataFrame:
    """One row per (tic, K): exactly one nominal A and one nominal B shard,
    same template source / W_g / status. No aggregate anything."""
    ab = outcomes[outcomes["arm"].isin(PAIR_ARMS)]
    if ab.empty:
        raise SystemExit("no scheduled nominal arm-A/arm-B rows")
    rows = []
    for (tic, k), group in ab.groupby(["tic", "template_k"], sort=True):
        a = group[group["arm"] == "A"]
        b = group[group["arm"] == "B"]
        if len(a) != 1 or len(b) != 1:
            raise SystemExit(f"(tic {tic}, K {k}): {len(a)} nominal arm-A and {len(b)} "
                             "nominal arm-B rows; exactly one of each is required")
        a, b = a.iloc[0], b.iloc[0]
        mismatch = [name for name in ("template_source_id", "wg_contrasts", "template_status")
                    if a[name] != b[name]]
        if mismatch:
            raise SystemExit(f"(tic {tic}, K {k}): arm-A/arm-B template metadata differ on {mismatch}")
        pair_usable = bool(a["usable"] and b["usable"])
        rows.append({
            "tic": int(tic), "template_k": int(k),
            "template_source_id": a["template_source_id"],
            "template_status": a["template_status"],
            "wg_contrasts": int(a["wg_contrasts"]),
            "a_sid": a["campaign_id"], "b_sid": b["campaign_id"],
            "a_status": a["best_status"], "b_status": b["best_status"],
            "a_usable": bool(a["usable"]), "b_usable": bool(b["usable"]),
            "pair_usable": pair_usable,
            "D_A": bool(a["D"]), "D_B": bool(b["D"]),
            "R_A": bool(a["R"]), "R_B": bool(b["R"]),
            "trigger_pair_class": pair_class(bool(a["D"]), bool(b["D"])) if pair_usable else "",
            "recovery_pair_class": pair_class(bool(a["R"]), bool(b["R"])) if pair_usable else "",
            **_status_fields(analysis_status),
        })
    table = pd.DataFrame(rows, columns=PAIR_COLUMNS)
    per_tic = table.groupby("tic")["template_k"].apply(lambda s: sorted(s.tolist()))
    incomplete = [int(t) for t, ks in per_tic.items() if ks != list(K_VALUES)]
    if incomplete:
        raise SystemExit(f"targets without exactly K={{0,1,2}} nominal pairs: {incomplete[:5]}")
    return table


# --------------------------------------------------------------------- CLI

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed D2 metrics out-dir (per_star.csv, d2_control_reuse.csv, manifest.json)")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--shards-dir", type=Path,
                        help="published generation directory holding shard_manifest.csv")
    source.add_argument("--shard-manifest", type=Path,
                        help="explicit path to the generation's typed shard manifest CSV")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    parser.add_argument("--allow-pilot", action="store_true",
                        help="DEVELOPMENT ONLY: accept a pilot metrics bundle; every output is "
                             f"stamped analysis_status={PILOT_DEV_STATUS}, never the ruled status")
    args = parser.parse_args()

    assert_frozen()
    metrics_manifest_path = args.metrics_dir / "manifest.json"
    metrics_manifest = json.loads(metrics_manifest_path.read_text(encoding="utf-8"))
    if metrics_manifest.get("dataset") != "d2":
        raise SystemExit("metrics bundle is not dataset d2")
    pilot = bool(metrics_manifest.get("pilot"))
    if pilot and not args.allow_pilot:
        raise SystemExit("pilot metrics bundle: the D2 descriptives are FULL-run only "
                         "(--allow-pilot exercises the code with analysis_status=pilot_dev_only)")
    analysis_status = PILOT_DEV_STATUS if pilot else ANALYSIS_STATUS

    manifest_path = args.shard_manifest or (args.shards_dir / "shard_manifest.csv")
    if args.shards_dir is not None and (args.shards_dir / "generation_manifest.json").exists():
        generation = json.loads((args.shards_dir / "generation_manifest.json").read_text(encoding="utf-8"))
        if generation.get("generation_id") != metrics_manifest.get("generation_id"):
            raise SystemExit("metrics bundle and --shards-dir describe different generations")
        recorded = generation.get("outputs_sha256", {}).get("shard_manifest.csv")
        if recorded and recorded != sha256_file(manifest_path):
            raise SystemExit("shard_manifest.csv differs from the generation record")
    per_star_path = args.metrics_dir / "per_star.csv"
    reuse_path = args.metrics_dir / "d2_control_reuse.csv"
    manifest = load_manifest(manifest_path)
    per_star = load_per_star(per_star_path)
    reuse = pd.read_csv(reuse_path, dtype={"control_campaign_id": str, "template_source_id": str})

    outcomes = attach_outcomes(manifest, per_star)
    k_table = k_template_status_table(outcomes, analysis_status)
    reuse_source = control_reuse_source(reuse, manifest, analysis_status)
    pairs = arm_a_b_pairs(outcomes, analysis_status)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    k_csv = args.out_dir / "d2_k_template_status.csv"
    k_table.to_csv(k_csv, index=False, lineterminator="\n")
    reuse_csv = args.out_dir / "d2_control_reuse_source.csv"
    reuse_source.to_csv(reuse_csv, index=False, lineterminator="\n")
    reuse_png = args.out_dir / "d2_control_reuse.png"
    plot_control_reuse(reuse_source, reuse_png, analysis_status)
    pairs_csv = args.out_dir / "d2_arm_a_b_pairs.csv"
    pairs.to_csv(pairs_csv, index=False, lineterminator="\n")
    script_sha = sha256_file(Path(__file__).resolve())
    reuse_meta = args.out_dir / "d2_control_reuse.meta.json"
    reuse_meta.write_text(json.dumps({
        "figure": reuse_png.name,
        "source_csv": reuse_csv.name,
        **_status_fields(analysis_status),
        "plotted_quantity": "n_b_assignments",
        "bar_unit": "one bar per unique control_campaign_id",
        "sort": "descending n_b_assignments, then control_campaign_id ascending",
        "n_controls": int(len(reuse_source)),
        "n_b_assignments_total": int(reuse_source["n_b_assignments"].sum()),
        "inputs_sha256": {"d2_control_reuse.csv": sha256_file(reuse_path)},
        "outputs_sha256": {reuse_png.name: sha256_file(reuse_png),
                           reuse_csv.name: sha256_file(reuse_csv)},
        "script_sha256": script_sha,
        "disclosure": DISCLOSURE,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readme = args.out_dir / "d2_descriptives.README.md"
    readme.write_text(
        "# D2 descriptive diagnostics (post-launch; ruling item 5, F08/F11/F38)\n\n"
        + DISCLOSURE + "\n\n"
        f"Admission verdict: {VERDICT_FILE} (ADMIT-DESCRIPTIVE, item 5).\n"
        "Files: d2_k_template_status.csv (nominal arm B, K x template_status x\n"
        "endpoint over the scheduled denominator; missing rows are failures;\n"
        "n_usable is context only), d2_control_reuse.png/_source.csv/.meta.json\n"
        "(one bar per unique control from the frozen d2_control_reuse.csv), and\n"
        "d2_arm_a_b_pairs.csv (one nominal A and one nominal B per (tic, K); no\n"
        "aggregate contrast, test, or interval). P4/P5 and every frozen metrics\n"
        "file are unchanged; nothing here enters a headline, endpoint decision,\n"
        "exclusion, reclassification, or replacement denominator.\n"
        f"analysis_status={analysis_status}; prespecified=false; interval=none.\n",
        encoding="utf-8",
    )
    verdict_path = REPO_ROOT / VERDICT_FILE
    b_rows = outcomes[outcomes["arm"] == "B"]
    bundle_manifest = {
        **_status_fields(analysis_status),
        "pilot_bundle": pilot,
        "generation_id": metrics_manifest.get("generation_id"),
        "inputs_sha256": {
            "per_star.csv": sha256_file(per_star_path),
            "d2_control_reuse.csv": sha256_file(reuse_path),
            "metrics_manifest.json": sha256_file(metrics_manifest_path),
            str(manifest_path): sha256_file(manifest_path),
            **({VERDICT_FILE: sha256_file(verdict_path)} if verdict_path.exists() else {}),
        },
        "outputs_sha256": {
            k_csv.name: sha256_file(k_csv),
            reuse_csv.name: sha256_file(reuse_csv),
            reuse_png.name: sha256_file(reuse_png),
            reuse_meta.name: sha256_file(reuse_meta),
            pairs_csv.name: sha256_file(pairs_csv),
        },
        "script_sha256": script_sha,
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
        "counts": {
            "nominal_b_scheduled": int(len(b_rows)),
            "nominal_b_scored": int(b_rows["scored"].sum()),
            "nominal_b_usable": int(b_rows["usable"].sum()),
            "k_template_status_cells": int(len(k_table)),
            "unique_controls": int(len(reuse_source)),
            "pairs": int(len(pairs)),
            "pairs_usable": int(pairs["pair_usable"].sum()),
        },
        "disclosure": DISCLOSURE,
    }
    (args.out_dir / "d2_descriptives.manifest.json").write_text(
        json.dumps(bundle_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(k_table.to_string(index=False))
    print(f"[d2_descriptives] {len(reuse_source)} unique controls; {len(pairs)} A/B pairs "
          f"({int(pairs['pair_usable'].sum())} usable); status={analysis_status}")
    print(f"[d2_descriptives] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
