#!/usr/bin/env python3
"""Shared, non-discretionary helpers for the ADMIT-DESCRIPTIVE D3 analyses
ruled in generalization/reviews/G5prep/sol_round2.md (fixed 2026-09-01,
before any full-campaign D3 metric existed).

Binding conventions (ruling preamble, applied to every descriptive CSV):

    analysis_status=postlaunch_descriptive
    prespecified=false
    interval=none

Bins are left-closed/right-open, missing values receive explicit unknown /
unscored cells, zero cells are emitted, rates are blank when their
denominator is zero. None of these outputs may enter a headline, endpoint
decision, exclusion, reclassification, or replacement denominator.

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive). It never edits frozen files and never re-implements the
frozen match taxonomy (classify_match is imported from
metrics_generalization by the analysis modules).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
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

# ---------------------------------------------------------------- ruled fields
ANALYSIS_STATUS = "postlaunch_descriptive"
PRESPECIFIED = False
INTERVAL = "none"
STATUS_COLUMNS = ["analysis_status", "prespecified", "interval"]
STATUS_FIELDS = {
    "analysis_status": ANALYSIS_STATUS,
    "prespecified": PRESPECIFIED,
    "interval": INTERVAL,
}
VERDICT_FILE = "generalization/reviews/G5prep/sol_round2.md"
OUT_SUBDIR = "descriptive_postlaunch"

# ---------------------------------------------------------------- ruled constants
# "The Nyquist constant is exactly: f_Nyq = 283.2 µHz = 24.46848 d^-1"
F_NYQ_UHZ = 283.2
F_NYQ_PER_DAY = 24.46848
# "convert fR with 86400/1e6": the identical expression the frozen truth
# loader applies to Mo table-2 frequencies (Freq * 86400.0 / 1e6); kept as a
# function so no pre-divided constant can change the last bit.
def uhz_to_per_day(x: float) -> float:
    return float(x) * 86400.0 / 1e6
# "delta_year = 1/365.25 = 0.0027378507871321013 d^-1"
DELTA_YEAR_PER_DAY = 1.0 / 365.25
# "tolerance_per_day = 1.5 / baseline_days" (D3 truth quantum is 0)
TOLERANCE_NUMERATOR_DAYS = 1.5

POSITIVE_CLASS = "dsct_flag1"
NEGATIVE_CLASS = "dsct_flag0"
CANDIDATE_CLASS = "dsct_flag2"
EXPECTED_POSITIVES = 610
EXPECTED_NEGATIVES = 2314
EXPECTED_ROSTER = 3000
EXPECTED_MO_JOINED = 456
RULE = "confirmed"
MISSING_STATUS = "missing"
UNSCORED = "unscored"
MATCH_CLASSES = ("direct", "harmonic", "window_alias", "ambiguous", "unmatched")
MATCH_CLASSES_WITH_UNSCORED = MATCH_CLASSES + (UNSCORED,)

DEFAULT_ROSTER = REPO_ROOT / "generalization/data/d3/roster_d3.csv"
DEFAULT_MO_TABLE1 = REPO_ROOT / "generalization/data/d3/raw/mo2026_table1.csv"
DEFAULT_MO_TABLE2 = REPO_ROOT / "generalization/data/d3/raw/mo2026_table2.csv"
DEFAULT_D1_CATALOG = (
    REPO_ROOT / "catalog-rebuild/results/2026-08-01_full/catalog/ls_full_catalog.csv"
)

PER_STAR_REQUIRED = (
    "sid", "class_label", "label_positive", "primary_freq", "freq_scorable",
    "baseline_days", "best_status", "best_frequency_per_day",
    "low_available", "high_available", "eligible_any_pass",
    "best_candidate_matches_any_mode", "best_candidate_matches_dominant",
    "any_top_peak_matches_any_mode",
)


# ---------------------------------------------------------------- small utilities

def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def truthy(value) -> bool:
    """Strict boolean reading of a per_star.csv cell: True only for a real
    True / "True" / "true"; NaN, None, False, blanks and anything else read
    as False. Used for availability / eligibility / scorable flags, whose
    frozen semantics are exactly 'True means yes'."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def is_boolean_cell(value) -> bool:
    """True iff the cell is an explicit boolean (True/False or their strings)."""
    if isinstance(value, (bool, np.bool_)):
        return True
    return isinstance(value, str) and value.strip().lower() in ("true", "false")


def finite_float(value) -> float:
    """float(value) if it is a finite number, else NaN (blanks, None, inf)."""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return math.nan
    return x if math.isfinite(x) else math.nan


def finite_series(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce").astype(float)
    return x.where(np.isfinite(x), np.nan)


def tolerance_per_day(baseline_days) -> float:
    """1.5 / baseline_days; NaN when the baseline is not a finite positive."""
    b = finite_float(baseline_days)
    if not (b > 0):
        return math.nan
    return TOLERANCE_NUMERATOR_DAYS / b


def bin_index_half_open(values: np.ndarray, edges: list[float]) -> np.ndarray:
    """Left-closed/right-open bin index for each value against sorted edges
    whose last element may be +inf: value in [edges[i], edges[i+1]) -> i.
    Values below edges[0] or >= edges[-1] are an error (caller guarantees
    the range); NaN is an error too (callers abort before binning)."""
    edges_arr = np.asarray(edges, dtype=float)
    if np.any(np.diff(edges_arr) <= 0):
        raise SystemExit("bin edges are not strictly increasing")
    vals = np.asarray(values, dtype=float)
    if vals.size and (not np.all(np.isfinite(vals)) or np.any(vals < edges_arr[0])
                      or np.any(vals >= edges_arr[-1])):
        raise SystemExit("values outside the fixed bin range (or non-finite)")
    return np.searchsorted(edges_arr, vals, side="right") - 1


# ---------------------------------------------------------------- inputs

def load_metrics_bundle(metrics_dir: Path) -> tuple[dict, pd.DataFrame]:
    """A completed FULL-run D3 metrics out-dir (manifest.json + per_star.csv).
    Pilot bundles are refused, as in the precedent module."""
    metrics_dir = Path(metrics_dir)
    manifest_path = metrics_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"metrics bundle has no manifest.json: {metrics_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset") != "d3":
        raise SystemExit("metrics bundle is not dataset d3")
    if manifest.get("pilot"):
        raise SystemExit("pilot metrics bundle: descriptive analyses are FULL-run only")
    per_star_path = metrics_dir / "per_star.csv"
    if not per_star_path.exists():
        raise SystemExit(f"metrics bundle has no per_star.csv: {metrics_dir}")
    per_star = pd.read_csv(per_star_path, dtype={"sid": str, "cluster": str})
    check_per_star_columns(per_star)
    return manifest, per_star


def check_per_star_columns(per_star: pd.DataFrame) -> None:
    missing = [c for c in PER_STAR_REQUIRED if c not in per_star.columns]
    if missing:
        raise SystemExit(f"per_star.csv lacks frozen columns {missing}")
    if per_star["sid"].duplicated().any():
        raise SystemExit("per_star.csv has duplicate sids")


def load_roster(path: Path = DEFAULT_ROSTER) -> pd.DataFrame:
    roster = pd.read_csv(path, dtype={"source_id": str})
    for col in ("source_id", "KIC", "class_label", "dom_freq_uhz",
                "dom_freq_per_day", "amp_mmag"):
        if col not in roster.columns:
            raise SystemExit(f"roster lacks column {col}: {path}")
    if roster["source_id"].duplicated().any():
        raise SystemExit("roster has duplicate source_ids")
    roster = roster.copy()
    roster["KIC"] = roster["KIC"].astype("int64")
    return roster


def load_mo_table1(path: Path = DEFAULT_MO_TABLE1) -> pd.DataFrame:
    t1 = pd.read_csv(path)
    for col in ("KIC", "Freq", "fR", "C"):
        if col not in t1.columns:
            raise SystemExit(f"Mo table 1 lacks column {col}: {path}")
    return t1


def load_mo_table2(path: Path = DEFAULT_MO_TABLE2) -> pd.DataFrame:
    t2 = pd.read_csv(path)
    for col in ("KIC", "Freq", "Amp"):
        if col not in t2.columns:
            raise SystemExit(f"Mo table 2 lacks column {col}: {path}")
    return t2


def table1_c0(table1: pd.DataFrame) -> pd.DataFrame:
    """Table-1 rows with C==0 and finite Freq and fR (the ruled row set)."""
    t1 = table1.copy()
    t1["Freq"] = finite_series(t1["Freq"])
    t1["fR"] = finite_series(t1["fR"])
    c = pd.to_numeric(t1["C"], errors="coerce")
    keep = (c == 0) & t1["Freq"].notna() & t1["fR"].notna()
    out = t1.loc[keep].copy()
    out["KIC"] = out["KIC"].astype("int64")
    return out


def table2_per_day_lists(table2: pd.DataFrame) -> dict[int, list[float]]:
    """KIC -> all finite table-2 frequencies in d^-1, table order, converted
    with the identical expression the frozen truth loader uses
    (Freq * 86400.0 / 1e6)."""
    t2 = table2.copy()
    freq = finite_series(t2["Freq"])
    t2 = t2.loc[freq.notna()].copy()
    t2["freq_per_day"] = t2["Freq"].astype(float).map(uhz_to_per_day)
    t2["KIC"] = t2["KIC"].astype("int64")
    return t2.groupby("KIC")["freq_per_day"].apply(list).to_dict()


def mo_joined_kics(roster: pd.DataFrame, table2: pd.DataFrame) -> set[int]:
    """The ruled (item 1) mo_joined conjunction over dsct_flag1 roster rows:
    at least one finite table-2 Freq; a finite table-2 maximum-amplitude row;
    finite positive dominant frequency and finite dominant amplitude in the
    roster."""
    t2 = table2.copy()
    t2["Freq"] = finite_series(t2["Freq"])
    t2["Amp"] = finite_series(t2["Amp"])
    t2["KIC"] = t2["KIC"].astype("int64")
    has_freq = set(t2.loc[t2["Freq"].notna(), "KIC"])
    with_amp = t2.loc[t2["Amp"].notna()]
    max_rows = with_amp.loc[with_amp.groupby("KIC")["Amp"].idxmax()]
    has_max = set(max_rows.loc[max_rows["Freq"].notna(), "KIC"])
    pos = roster[roster["class_label"] == POSITIVE_CLASS]
    dom = finite_series(pos["dom_freq_per_day"])
    amp = finite_series(pos["amp_mmag"])
    ok = pos["KIC"].isin(has_freq) & pos["KIC"].isin(has_max) & (dom > 0) & amp.notna()
    return set(pos.loc[ok, "KIC"].astype("int64"))


def sid_to_kic(per_star: pd.DataFrame, roster: pd.DataFrame) -> pd.Series:
    """KIC per per_star sid via the roster's source_id; every sid must be a
    roster row (the metrics guard already enforces this for D3)."""
    lookup = roster.set_index("source_id")["KIC"]
    missing = [s for s in per_star["sid"] if s not in lookup.index]
    if missing:
        raise SystemExit(f"per_star sids not in the roster: {missing[:5]}")
    return per_star["sid"].map(lookup).astype("int64")


# ---------------------------------------------------------------- frozen frames

def positives_frame(per_star: pd.DataFrame,
                    expected_positives: int = EXPECTED_POSITIVES) -> pd.DataFrame:
    """All eligible dsct_flag1 positives (the P1 denominator)."""
    check_per_star_columns(per_star)
    pos = per_star[per_star["class_label"] == POSITIVE_CLASS].copy()
    if len(pos) != expected_positives:
        raise SystemExit(
            f"{len(pos)} {POSITIVE_CLASS} rows != the frozen positive "
            f"denominator {expected_positives}; refusing"
        )
    if not pos["label_positive"].map(truthy).all():
        raise SystemExit("a dsct_flag1 row is not label_positive; per_star.csv inconsistent")
    return pos


def p2_frame(per_star: pd.DataFrame,
             expected_positives: int = EXPECTED_POSITIVES,
             expected_scorable: int = EXPECTED_MO_JOINED) -> pd.DataFrame:
    """The exact frozen P2 frame (metrics_generalization.completeness_tables
    / surfaces): dsct_flag1, freq_scorable (Mo-joined), usable (result
    present, both passes available), S_best=1 (eligible_any_pass)."""
    pos = positives_frame(per_star, expected_positives)
    scorable = pos["freq_scorable"].map(truthy)
    if int(scorable.sum()) != expected_scorable:
        raise SystemExit(
            f"{int(scorable.sum())} freq_scorable positives != the ruled "
            f"{expected_scorable}; refusing"
        )
    usable = (
        (pos["best_status"] != MISSING_STATUS)
        & pos["low_available"].map(truthy)
        & pos["high_available"].map(truthy)
    )
    s_best = pos["eligible_any_pass"].map(truthy)
    frame = pos[scorable & usable & s_best].copy()
    dom = finite_series(frame["primary_freq"])
    if not (dom > 0).all():
        raise SystemExit("a P2-frame star lacks a finite positive dominant frequency")
    frame["primary_freq"] = dom
    return frame


def negatives_frame(per_star: pd.DataFrame,
                    expected_negatives: int = EXPECTED_NEGATIVES) -> pd.DataFrame:
    check_per_star_columns(per_star)
    neg = per_star[per_star["class_label"] == NEGATIVE_CLASS].copy()
    if len(neg) != expected_negatives:
        raise SystemExit(
            f"{len(neg)} {NEGATIVE_CLASS} rows != the frozen P3 denominator "
            f"{expected_negatives}; refusing"
        )
    return neg


# ---------------------------------------------------------------- outputs

def with_status(table: pd.DataFrame) -> pd.DataFrame:
    out = table.copy()
    out["analysis_status"] = ANALYSIS_STATUS
    out["prespecified"] = PRESPECIFIED
    out["interval"] = INTERVAL
    return out


def write_csv(table: pd.DataFrame, path: Path, columns: list[str]) -> None:
    missing = [c for c in columns if c not in table.columns]
    if missing:
        raise SystemExit(f"output lacks ruled columns {missing}")
    table[columns].to_csv(path, index=False, lineterminator="\n")


def provenance_block(script_path: Path) -> dict:
    """Manifest block shared by every descriptive module: verdict, script,
    common-module, frozen and campaign SHAs, plus the ruled status fields."""
    verdict_path = REPO_ROOT / VERDICT_FILE
    block = {
        **STATUS_FIELDS,
        "verdict_file": VERDICT_FILE,
        "script_sha256": sha256_file(Path(script_path).resolve()),
        "common_module_sha256": sha256_file(Path(__file__).resolve()),
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
    }
    if verdict_path.exists():
        block["verdict_sha256"] = sha256_file(verdict_path)
    return block


def write_json(path: Path, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, default=_json_default) + "\n",
                          encoding="utf-8")


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"not JSON serialisable: {type(obj)}")


__all__ = [
    "REPO_ROOT", "assert_frozen", "campaign_file_shas", "frozen_file_shas",
    "ANALYSIS_STATUS", "PRESPECIFIED", "INTERVAL", "STATUS_COLUMNS", "STATUS_FIELDS",
    "VERDICT_FILE", "OUT_SUBDIR",
    "F_NYQ_UHZ", "F_NYQ_PER_DAY", "uhz_to_per_day", "DELTA_YEAR_PER_DAY",
    "TOLERANCE_NUMERATOR_DAYS",
    "POSITIVE_CLASS", "NEGATIVE_CLASS", "CANDIDATE_CLASS", "EXPECTED_POSITIVES",
    "EXPECTED_NEGATIVES", "EXPECTED_ROSTER", "EXPECTED_MO_JOINED", "RULE",
    "MISSING_STATUS", "UNSCORED", "MATCH_CLASSES", "MATCH_CLASSES_WITH_UNSCORED",
    "DEFAULT_ROSTER", "DEFAULT_MO_TABLE1", "DEFAULT_MO_TABLE2", "DEFAULT_D1_CATALOG",
    "sha256_file", "truthy", "is_boolean_cell", "finite_float", "finite_series",
    "tolerance_per_day", "bin_index_half_open",
    "load_metrics_bundle", "check_per_star_columns", "load_roster", "load_mo_table1",
    "load_mo_table2", "table1_c0", "table2_per_day_lists", "mo_joined_kics",
    "sid_to_kic", "positives_frame", "p2_frame", "negatives_frame",
    "with_status", "write_csv", "provenance_block", "write_json",
]
