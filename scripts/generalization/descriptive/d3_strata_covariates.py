#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE stratification of the D3 negative-class rule-1
trigger numerator (P3) and a covariate-by-class table.

Admitted by generalization/reviews/G5prep/sol_round2.md item 6
(F15/F17/F27/F37, ADMIT-DESCRIPTIVE, ruling fixed 2026-09-01). The binding
definitions, implemented here without discretion:

- Frame: all 2,314 `dsct_flag0` roster members; missing/unusable results are
  non-triggers. Rule 1 (`confirmed`), best pass, for magnitude / Teff /
  merged-oid / sky strata; the two pass rows use `low_status` and
  `high_status` and are each over all 2,314 negatives (NOT additive: a star
  may confirm in both passes).
- Magnitude: `g_le_14` for finite gmag <= 14.0 (the ruled boundary; the
  roster's legacy `near_saturation` flag is ignored), `g_gt_14`, `g_unknown`.
- Teff: pooled-roster linear-quantile cuts fixed at 6597.0 / 6737.0 /
  7092.5 K -> `<6597`, `[6597,6737)`, `[6737,7092.5)`, `>=7092.5`, unknown.
- Merged oids (`selected_ztf_objects` of the frozen crossmatch frame):
  `oid_le_1`, `oid_2`, `oid_3_4`, `oid_ge_5`, `oid_unknown`.
- Sky: fixed 4x4 axis-aligned RA/Dec grid, RA cuts 290.0945525 / 293.54213 /
  296.340635 deg, Dec cuts 41.048665 / 43.879275 / 46.70182 deg, half-open
  cells `RAq1_DECq1` .. `RAq4_DECq4` plus `sky_unknown`.
- Every stratifier emits every cell (zero cells included); rates are blank
  when the denominator is zero; each stratifier's n_negative sums to 2,314.
- The high-pass row is the "high-pass negative-class rule-1 trigger rate";
  it is never a "sub-hour false-trigger proxy".
- Covariates by class: all 3,000 eligible roster rows, class levels 0/1/2,
  unweighted, population SD (ddof=0), linear quantiles, no tests.
- analysis_status=postlaunch_descriptive, prespecified=false, interval=none.
  Nothing here enters a headline, endpoint, exclusion, reclassification, or
  replacement denominator. FULL-run only (refuses pilot metrics bundles).

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive), so committing/pulling it is SHA-neutral for live runners.

Inputs: a completed FULL D3 metrics out-dir (per_star.csv, manifest.json),
the frozen roster and the frozen crossmatch adjudication frame. Outputs
(out-dir): d3_negative_trigger_strata.csv, d3_covariates_by_class.csv,
d3_strata_covariates.README.md (verbatim disclosure) and
d3_strata_covariates.manifest.json (input/output SHAs). The sidecars are
module-prefixed so several descriptive modules can share one
descriptive_postlaunch/ directory without clobbering each other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)

# ---------------------------------------------------------------- frozen constants
# (sol_round2.md items 1 and 6; never derived at run time)
GMAG_BOUNDARY = 14.0
TEFF_CUTS_K = (6597.0, 6737.0, 7092.5)
RA_CUTS_DEG = (290.0945525, 293.54213, 296.340635)
DEC_CUTS_DEG = (41.048665, 43.879275, 46.70182)

EXPECTED_NEGATIVES = 2314
EXPECTED_ROSTER = 3000
NEGATIVE_CLASS = "dsct_flag0"
CLASS_LEVELS = ("dsct_flag0", "dsct_flag1", "dsct_flag2")
RULE = "confirmed"
BEST_PASS_BASIS = "best"
STATUS_VOCABULARY = frozenset({"confirmed", "candidate", "not_detected", "missing"})

ANALYSIS_STATUS = "postlaunch_descriptive"
PRESPECIFIED = False
INTERVAL = "none"
VERDICT_FILE = "generalization/reviews/G5prep/sol_round2.md"
HIGH_PASS_LABEL = "high-pass negative-class rule-1 trigger rate"
DISCLOSURE = (
    "Post-launch descriptive analysis stratifies the unchanged 2,314-star "
    "rule-1 negative-class trigger numerator by fixed magnitude, Teff, "
    "merged-oid, pass, and sky cells and separately describes covariates by "
    "class; these are plain counts and rates without intervals, and the "
    "high-pass row is a negative-class trigger diagnostic rather than an FPR "
    "or sub-hour false-trigger estimate."
)

MAGNITUDE_CELLS = ("g_le_14", "g_gt_14", "g_unknown")
TEFF_CELLS = ("<6597", "[6597,6737)", "[6737,7092.5)", ">=7092.5", "teff_unknown")
OID_CELLS = ("oid_le_1", "oid_2", "oid_3_4", "oid_ge_5", "oid_unknown")
PASS_CELLS = ("low", "high")
SKY_CELLS = tuple(
    f"RAq{i}_DECq{j}" for i in range(1, 5) for j in range(1, 5)
) + ("sky_unknown",)

STRATA_COLUMNS = [
    "stratifier", "stratum", "pass_basis", "rule",
    "n_negative", "k_confirmed", "rate",
    "analysis_status", "prespecified", "interval",
]
COVARIATE_COLUMNS = [
    "class_label", "covariate", "n_class", "n_nonmissing", "n_missing",
    "mean", "sd", "p10", "p25", "p50", "p75", "p90", "min", "max",
    "analysis_status", "prespecified", "interval",
]
ROSTER_COVARIATES = ("gmag", "Teff", "ra", "dec")
CROSSMATCH_COVARIATES = (
    "nearest_separation_arcsec", "ztf_objects_in_cone", "selected_ztf_objects",
    "zg_clean_rows", "zr_clean_rows",
)
COVARIATES = ROSTER_COVARIATES + CROSSMATCH_COVARIATES
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)

DEFAULT_ROSTER = REPO_ROOT / "generalization/data/d3/roster_d3.csv"
DEFAULT_CROSSMATCH = (
    REPO_ROOT / "generalization/data/d3/crossmatch_freeze/crossmatch_adjudication.csv"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_label(path: Path) -> str:
    """Repo-relative manifest key when the file lives under REPO_ROOT (so the
    manifest compares across machines); absolute otherwise."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(resolved)


def _finite(value) -> bool:
    try:
        return value is not None and not isinstance(value, bool) \
            and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------- bin rules

def magnitude_bin(gmag) -> str:
    """`g_le_14` for finite gmag <= 14.0 (boundary IN the bright stratum)."""
    if not _finite(gmag):
        return "g_unknown"
    return "g_le_14" if float(gmag) <= GMAG_BOUNDARY else "g_gt_14"


def teff_bin(teff) -> str:
    """Left-closed/right-open cells at the frozen cuts."""
    if not _finite(teff):
        return "teff_unknown"
    return TEFF_CELLS[bisect_right(TEFF_CUTS_K, float(teff))]


def merged_oid_bin(n_selected) -> str:
    if not _finite(n_selected):
        return "oid_unknown"
    n = float(n_selected)
    if n <= 1:
        return "oid_le_1"
    if n < 3:
        return "oid_2"
    if n < 5:
        return "oid_3_4"
    return "oid_ge_5"


def quartile_index(value: float, cuts: tuple[float, ...]) -> int:
    """1-based half-open index: 1 for value < cuts[0], 2 for [cuts[0], cuts[1]), ..."""
    return bisect_right(cuts, float(value)) + 1


def sky_cell(ra, dec) -> str:
    if not (_finite(ra) and _finite(dec)):
        return "sky_unknown"
    return f"RAq{quartile_index(ra, RA_CUTS_DEG)}_DECq{quartile_index(dec, DEC_CUTS_DEG)}"


# ---------------------------------------------------------------- frames

def negative_frame(per_star: pd.DataFrame, roster: pd.DataFrame,
                   crossmatch: pd.DataFrame,
                   expected_negatives: int = EXPECTED_NEGATIVES) -> pd.DataFrame:
    """The 2,314 negatives with their statuses and stratifier inputs.
    Fail-closed on every identity that could silently move the denominator."""
    negatives = per_star[per_star["class_label"] == NEGATIVE_CLASS]
    if len(negatives) != expected_negatives:
        raise SystemExit(
            f"{len(negatives)} {NEGATIVE_CLASS} rows in per_star != the frozen "
            f"P3 denominator {expected_negatives}; refusing to stratify"
        )
    if negatives["sid"].duplicated().any():
        raise SystemExit("duplicate sids among the per_star negatives")
    if roster["source_id"].duplicated().any():
        raise SystemExit("duplicate source_id in the roster")
    roster_neg = roster[roster["class_label"] == NEGATIVE_CLASS]
    if len(roster_neg) != expected_negatives:
        raise SystemExit(
            f"roster holds {len(roster_neg)} {NEGATIVE_CLASS} rows != {expected_negatives}"
        )
    if set(negatives["sid"]) != set(roster_neg["source_id"]):
        raise SystemExit("per_star negatives are not the roster negatives (sid sets differ)")
    if crossmatch["source_id"].duplicated().any():
        raise SystemExit("duplicate source_id in the crossmatch frame")
    if not set(roster_neg["source_id"]) <= set(crossmatch["source_id"]):
        raise SystemExit("crossmatch frame does not cover every roster negative")
    for column in ("best_status", "low_status", "high_status"):
        bad = set(negatives[column].astype(str)) - STATUS_VOCABULARY
        if bad:
            raise SystemExit(f"unexpected {column} values among negatives: {sorted(bad)}")

    frame = (
        negatives[["sid", "best_status", "low_status", "high_status"]]
        .merge(roster_neg[["source_id", "gmag", "Teff", "ra", "dec"]],
               left_on="sid", right_on="source_id", how="left", validate="one_to_one")
        .merge(crossmatch[["source_id", "selected_ztf_objects"]],
               on="source_id", how="left", validate="one_to_one")
        .drop(columns=["source_id"])
        .reset_index(drop=True)
    )
    if len(frame) != expected_negatives:  # pragma: no cover - merge identity
        raise SystemExit("negative frame lost rows in the join")
    return frame


def negative_trigger_strata(frame: pd.DataFrame,
                            expected_negatives: int = EXPECTED_NEGATIVES) -> pd.DataFrame:
    """Plain counts and rates per cell; every cell of every stratifier emitted."""
    n_total = len(frame)
    if n_total != expected_negatives:
        raise SystemExit(f"negative frame has {n_total} rows != {expected_negatives}")
    best_conf = (frame["best_status"] == RULE).to_numpy()
    low_conf = (frame["low_status"] == RULE).to_numpy()
    high_conf = (frame["high_status"] == RULE).to_numpy()
    k_total = int(best_conf.sum())

    def row(stratifier: str, stratum: str, pass_basis: str, n: int, k: int) -> dict:
        return {
            "stratifier": stratifier, "stratum": stratum,
            "pass_basis": pass_basis, "rule": RULE,
            "n_negative": n, "k_confirmed": k,
            "rate": (k / n) if n else math.nan,
            "analysis_status": ANALYSIS_STATUS,
            "prespecified": PRESPECIFIED, "interval": INTERVAL,
        }

    rows: list[dict] = []
    labelled = (
        ("magnitude", MAGNITUDE_CELLS, frame["gmag"].map(magnitude_bin)),
        ("teff", TEFF_CELLS, frame["Teff"].map(teff_bin)),
        ("merged_oid", OID_CELLS, frame["selected_ztf_objects"].map(merged_oid_bin)),
    )
    sky_labels = pd.Series(
        [sky_cell(ra, dec) for ra, dec in zip(frame["ra"], frame["dec"])],
        index=frame.index,
    )

    def emit(stratifier: str, cells: tuple[str, ...], labels: pd.Series) -> None:
        unknown_labels = set(labels) - set(cells)
        if unknown_labels:  # pragma: no cover - bin functions are closed over cells
            raise SystemExit(f"{stratifier}: labels outside the cell set {unknown_labels}")
        n_sum = 0
        k_sum = 0
        for cell in cells:
            mask = (labels == cell).to_numpy()
            n = int(mask.sum())
            k = int((mask & best_conf).sum())
            n_sum += n
            k_sum += k
            rows.append(row(stratifier, cell, BEST_PASS_BASIS, n, k))
        if n_sum != n_total or k_sum != k_total:
            raise SystemExit(
                f"{stratifier}: cells sum to n={n_sum}, k={k_sum}; expected "
                f"n={n_total}, k={k_total}"
            )

    for stratifier, cells, labels in labelled:
        emit(stratifier, cells, labels)
    # pass rows: each over ALL negatives; non-additive by construction
    rows.append(row("pass", "low", "low", n_total, int(low_conf.sum())))
    rows.append(row("pass", "high", "high", n_total, int(high_conf.sum())))
    emit("sky", SKY_CELLS, sky_labels)

    table = pd.DataFrame(rows, columns=STRATA_COLUMNS)
    return table


# ---------------------------------------------------------------- covariates

def describe(values: np.ndarray) -> dict:
    """Unweighted description: mean, population SD (ddof=0), linear quantiles,
    min, max. All blank (NaN) when nothing finite is present."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {k: math.nan for k in ("mean", "sd", "p10", "p25", "p50", "p75", "p90", "min", "max")}
    q = np.quantile(x, QUANTILES, method="linear")
    return {
        "mean": float(np.mean(x)),
        "sd": float(np.std(x, ddof=0)),
        "p10": float(q[0]), "p25": float(q[1]), "p50": float(q[2]),
        "p75": float(q[3]), "p90": float(q[4]),
        "min": float(np.min(x)), "max": float(np.max(x)),
    }


def covariates_by_class(roster: pd.DataFrame, crossmatch: pd.DataFrame,
                        expected_roster: int = EXPECTED_ROSTER) -> pd.DataFrame:
    if len(roster) != expected_roster:
        raise SystemExit(f"roster has {len(roster)} rows != {expected_roster}")
    if roster["source_id"].duplicated().any():
        raise SystemExit("duplicate source_id in the roster")
    levels = set(roster["class_label"])
    if levels != set(CLASS_LEVELS):
        raise SystemExit(f"roster class levels {sorted(levels)} != {list(CLASS_LEVELS)}")
    if crossmatch["source_id"].duplicated().any():
        raise SystemExit("duplicate source_id in the crossmatch frame")
    if not set(roster["source_id"]) <= set(crossmatch["source_id"]):
        raise SystemExit("crossmatch frame does not cover every roster row")
    missing_cols = [c for c in ROSTER_COVARIATES if c not in roster.columns] + \
        [c for c in CROSSMATCH_COVARIATES if c not in crossmatch.columns]
    if missing_cols:
        raise SystemExit(f"covariate columns missing from inputs: {missing_cols}")

    merged = roster[["source_id", "class_label", *ROSTER_COVARIATES]].merge(
        crossmatch[["source_id", *CROSSMATCH_COVARIATES]],
        on="source_id", how="left", validate="one_to_one",
    )
    rows: list[dict] = []
    for label in CLASS_LEVELS:
        sub = merged[merged["class_label"] == label]
        n_class = int(len(sub))
        for covariate in COVARIATES:
            values = pd.to_numeric(sub[covariate], errors="coerce").to_numpy(dtype=float)
            n_nonmissing = int(np.isfinite(values).sum())
            rows.append({
                "class_label": label, "covariate": covariate,
                "n_class": n_class, "n_nonmissing": n_nonmissing,
                "n_missing": n_class - n_nonmissing,
                **describe(values),
                "analysis_status": ANALYSIS_STATUS,
                "prespecified": PRESPECIFIED, "interval": INTERVAL,
            })
    table = pd.DataFrame(rows, columns=COVARIATE_COLUMNS)
    if int(table.drop_duplicates(["class_label"])["n_class"].sum()) != expected_roster:
        raise SystemExit("class sizes do not sum to the roster")  # pragma: no cover
    return table


# ---------------------------------------------------------------- CLI

def check_metrics_manifest(manifest: dict) -> None:
    if manifest.get("dataset") != "d3":
        raise SystemExit("metrics bundle is not dataset d3")
    if manifest.get("pilot"):
        raise SystemExit("pilot metrics bundle: the descriptive strata are FULL-run only")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER,
                        help="frozen 3,000-row D3 roster")
    parser.add_argument("--crossmatch-csv", type=Path, default=DEFAULT_CROSSMATCH,
                        help="frozen per-star crossmatch adjudication frame")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args()

    assert_frozen()
    metrics_manifest_path = args.metrics_dir / "manifest.json"
    check_metrics_manifest(json.loads(metrics_manifest_path.read_text(encoding="utf-8")))
    per_star_path = args.metrics_dir / "per_star.csv"
    per_star = pd.read_csv(per_star_path, dtype={"sid": str})
    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    crossmatch = pd.read_csv(args.crossmatch_csv, dtype={"source_id": str})

    frame = negative_frame(per_star, roster, crossmatch)
    strata = negative_trigger_strata(frame)
    covariates = covariates_by_class(roster, crossmatch)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    strata_csv = args.out_dir / "d3_negative_trigger_strata.csv"
    covariates_csv = args.out_dir / "d3_covariates_by_class.csv"
    strata.to_csv(strata_csv, index=False, lineterminator="\n")
    covariates.to_csv(covariates_csv, index=False, lineterminator="\n")
    readme = args.out_dir / "d3_strata_covariates.README.md"
    readme.write_text(
        "# D3 negative-class trigger strata and covariates by class "
        "(descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n"
        f"Admission: {VERDICT_FILE}, item 6 (F15/F17/F27/F37, ADMIT-DESCRIPTIVE).\n"
        f"Frozen cuts: gmag <= {GMAG_BOUNDARY}; Teff {TEFF_CUTS_K} K; "
        f"RA {RA_CUTS_DEG} deg; Dec {DEC_CUTS_DEG} deg; merged oids "
        "<=1 / 2 / 3-4 / >=5 from the frozen crossmatch frame's "
        "selected_ztf_objects. Bins are left-closed/right-open; unknown cells\n"
        "are explicit; zero cells are emitted; rates are blank at zero\n"
        "denominators. The pass rows are each over all 2,314 negatives and are\n"
        f"not additive; the high-pass row is the \"{HIGH_PASS_LABEL}\".\n"
        "P3 itself is unchanged and none of these rows enters a headline,\n"
        "endpoint, exclusion, reclassification, or replacement denominator.\n",
        encoding="utf-8",
    )
    verdict_path = REPO_ROOT / VERDICT_FILE
    n_low = int(strata.loc[(strata["stratifier"] == "pass") & (strata["stratum"] == "low"),
                           "k_confirmed"].iloc[0])
    n_high = int(strata.loc[(strata["stratifier"] == "pass") & (strata["stratum"] == "high"),
                            "k_confirmed"].iloc[0])
    manifest = {
        "analysis_status": ANALYSIS_STATUS,
        "prespecified": PRESPECIFIED,
        "interval": INTERVAL,
        "verdict_file": VERDICT_FILE,
        "constants": {
            "gmag_boundary": GMAG_BOUNDARY,
            "teff_cuts_k": list(TEFF_CUTS_K),
            "ra_cuts_deg": list(RA_CUTS_DEG),
            "dec_cuts_deg": list(DEC_CUTS_DEG),
            "merged_oid_source": "selected_ztf_objects",
            "quantile_method": "linear",
            "sd_ddof": 0,
            "high_pass_label": HIGH_PASS_LABEL,
        },
        "inputs_sha256": {
            "per_star.csv": sha256_file(per_star_path),
            "metrics_manifest.json": sha256_file(metrics_manifest_path),
            input_label(args.roster): sha256_file(args.roster),
            input_label(args.crossmatch_csv): sha256_file(args.crossmatch_csv),
            **({VERDICT_FILE: sha256_file(verdict_path)} if verdict_path.exists() else {}),
        },
        "outputs_sha256": {
            "d3_negative_trigger_strata.csv": sha256_file(strata_csv),
            "d3_covariates_by_class.csv": sha256_file(covariates_csv),
        },
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
        "counts": {
            "n_negative": int(len(frame)),
            "k_confirmed_best_pass": int((frame["best_status"] == RULE).sum()),
            "k_confirmed_low_pass": n_low,
            "k_confirmed_high_pass": n_high,
            "n_roster": int(len(roster)),
            "n_by_class": {
                label: int((roster["class_label"] == label).sum()) for label in CLASS_LEVELS
            },
        },
    }
    (args.out_dir / "d3_strata_covariates.manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(strata.to_string(index=False))
    print(f"[strata_covariates] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
