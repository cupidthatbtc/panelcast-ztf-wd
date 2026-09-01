#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE frequency audits (ruling:
generalization/reviews/G5prep/sol_round2.md, item 9, F32/F33,
ADMIT-DESCRIPTIVE).

D1 versus D3 confirmed-frequency histogram
  D1: blind_status=="confirmed" from the 928-star published catalog;
  D3: dsct_flag0 and best_status=="confirmed". Abort if any selected row
  lacks a finite positive best frequency. Fixed edges (d^-1):
    0, 0.25, 0.50, 0.75, 0.98, 1.02, 1.25, 1.50, 1.75, 1.98, 2.02, 2.25,
    2.50, 2.75, 2.98, 3.02, 3.25, 3.50, 3.75, 4, 6, 8, 12, 16, 20, 24, 32,
    48, 96, 192, 384, 768, 1440, infinity
  left-closed/right-open, the final finite edge (1440) included in the
  overflow bin. Each dataset is normalised separately by its confirmed
  count; density_per_day = share_of_confirmed / bin_width for finite bins
  (blank for the overflow bin). Files:
    descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.csv
    descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.png
    descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.meta.json

Extra relation columns
  descriptive_postlaunch/d3_extra_frequency_relations.csv — NEVER added to
  the frozen per_star.csv. With delta_year = 1/365.25, f_Nyq = 24.46848
  d^-1 and tol = 1.5/baseline_days, for the dominant frequency and,
  separately, every table-2 mode:
    yearly_alias:  |f_candidate - |f_truth ± delta_year|| <= tol
    kepler_nyquist_reflection: f_ref = 2 f_Nyq - f_truth, f_ref > 0 and
                               |f_candidate - f_ref| <= tol
  Independent booleans; harmonics and sidereal aliases are not folded in;
  the frozen taxonomy columns are copied beside them unchanged. Rows
  mirror per_star.csv (one per star); a relation is blank wherever the
  corresponding frozen match column is `unscored` (no candidate or no
  truth). FULL-run only.

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402,F401
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)
import d3_descriptive_common as common  # noqa: E402
from d3_descriptive_common import (  # noqa: E402
    DELTA_YEAR_PER_DAY,
    F_NYQ_PER_DAY,
    RULE,
    STATUS_COLUMNS,
    UNSCORED,
    bin_index_half_open,
    finite_float,
    finite_series,
    sha256_file,
    tolerance_per_day,
)

HIST_EDGES = [
    0, 0.25, 0.50, 0.75, 0.98, 1.02, 1.25, 1.50, 1.75,
    1.98, 2.02, 2.25, 2.50, 2.75, 2.98, 3.02, 3.25, 3.50,
    3.75, 4, 6, 8, 12, 16, 20, 24, 32, 48, 96, 192, 384,
    768, 1440, math.inf,
]
EXPECTED_D1_CATALOG_ROWS = 928
D1_DATASET = "D1"
D3_DATASET = "D3"
D1_SELECTION = 'blind_status=="confirmed" (928-star published catalog)'
D3_SELECTION = 'dsct_flag0 and best_status=="confirmed"'

HIST_CSV = "d1_d3_confirmed_frequency_histogram.csv"
HIST_PNG = "d1_d3_confirmed_frequency_histogram.png"
HIST_META = "d1_d3_confirmed_frequency_histogram.meta.json"
RELATIONS_CSV = "d3_extra_frequency_relations.csv"
README_FILE = "d3_frequency_audits.README.md"
MANIFEST_FILE = "d3_frequency_audits.manifest.json"

HIST_COLUMNS = [
    "dataset", "selection", "bin_index", "freq_lo_per_day", "freq_hi_per_day",
    "n_confirmed_total", "n_bin", "share_of_confirmed", "density_per_day",
    *STATUS_COLUMNS,
]
RELATION_COLUMNS = [
    "sid", "best_status", "best_frequency_per_day", "baseline_days", "tolerance_per_day",
    "frozen_best_candidate_matches_dominant", "frozen_best_candidate_matches_any_mode",
    "matches_yearly_alias_dominant", "matches_yearly_alias_any_mode",
    "matches_kepler_nyquist_reflection_dominant",
    "matches_kepler_nyquist_reflection_any_mode", *STATUS_COLUMNS,
]

DISCLOSURE = (
    "Post-launch descriptive frequency audits compare the normalized "
    "best-frequency distributions of published D1 confirmations and D3 "
    "negative-class confirmations and report yearly-alias and "
    "Kepler-Nyquist-reflection predicates beside the unchanged frozen taxonomy; "
    "the added relations never reclassify a frozen match or alter P2 or P3."
)


# ---------------------------------------------------------------- histogram

def _require_finite_positive(freqs: pd.Series, label: str, ids: pd.Series) -> np.ndarray:
    x = finite_series(freqs)
    bad = ~(x > 0)
    if bad.any():
        raise SystemExit(
            f"{label}: selected rows without a finite positive best frequency "
            f"(abort rather than bin silently): {ids[bad].tolist()[:10]}"
        )
    return x.to_numpy(dtype=float)


def d1_confirmed_frequencies(catalog: pd.DataFrame,
                             expected_rows: int = EXPECTED_D1_CATALOG_ROWS) -> np.ndarray:
    for col in ("source_id", "blind_status", "best_frequency_per_day"):
        if col not in catalog.columns:
            raise SystemExit(f"D1 catalog lacks column {col}")
    if len(catalog) != expected_rows:
        raise SystemExit(f"D1 catalog has {len(catalog)} rows, not the published {expected_rows}")
    if catalog["source_id"].astype(str).duplicated().any():
        raise SystemExit("D1 catalog has duplicate source_ids")
    sel = catalog[catalog["blind_status"] == RULE]
    return _require_finite_positive(sel["best_frequency_per_day"], D1_DATASET,
                                    sel["source_id"].astype(str))


def d3_negative_confirmed_frequencies(per_star: pd.DataFrame,
                                      expected_negatives: int = common.EXPECTED_NEGATIVES
                                      ) -> np.ndarray:
    neg = common.negatives_frame(per_star, expected_negatives)
    sel = neg[neg["best_status"] == RULE]
    return _require_finite_positive(sel["best_frequency_per_day"], D3_DATASET, sel["sid"])


def histogram_table(selections: dict[str, tuple[str, np.ndarray]],
                    edges: list[float] = HIST_EDGES) -> pd.DataFrame:
    """selections: dataset -> (selection label, frequencies). One row per
    dataset x bin; zero bins emitted; shares blank when the dataset has no
    confirmed row; density blank for the infinite-width overflow bin."""
    n_bins = len(edges) - 1
    rows = []
    for dataset, (selection, freqs) in selections.items():
        freqs = np.asarray(freqs, dtype=float)
        n_total = int(len(freqs))
        idx = bin_index_half_open(freqs, edges)
        counts = np.bincount(idx, minlength=n_bins) if n_total else np.zeros(n_bins, dtype=int)
        if int(counts.sum()) != n_total:  # pragma: no cover - identity
            raise SystemExit("histogram counts do not sum to the selection size")
        for b in range(n_bins):
            lo, hi = float(edges[b]), float(edges[b + 1])
            n_bin = int(counts[b])
            share = n_bin / n_total if n_total else math.nan
            width = hi - lo
            density = share / width if (n_total and math.isfinite(width)) else math.nan
            rows.append({
                "dataset": dataset, "selection": selection, "bin_index": b,
                "freq_lo_per_day": lo, "freq_hi_per_day": hi,
                "n_confirmed_total": n_total, "n_bin": n_bin,
                "share_of_confirmed": share, "density_per_day": density,
            })
    return common.with_status(pd.DataFrame(rows))[HIST_COLUMNS]


def plot_histogram(table: pd.DataFrame, png_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 4.8))
    styles = {D1_DATASET: ("#1f77b4", "-"), D3_DATASET: ("#d62728", "--")}
    for dataset in table["dataset"].unique():
        sub = table[table["dataset"] == dataset].sort_values("bin_index")
        n_total = int(sub["n_confirmed_total"].iloc[0])
        finite = sub[np.isfinite(sub["freq_hi_per_day"])]
        overflow = sub[~np.isfinite(sub["freq_hi_per_day"])]
        n_over = int(overflow["n_bin"].sum())
        label = f"{dataset}: n_confirmed={n_total}, n>={finite['freq_hi_per_day'].iloc[-1]:g}/d={n_over}"
        if n_total == 0:
            ax.plot([], [], label=label + " (no rows)")
            continue
        edges = finite["freq_lo_per_day"].tolist() + [float(finite["freq_hi_per_day"].iloc[-1])]
        colour, ls = styles.get(dataset, ("black", "-"))
        ax.stairs(finite["density_per_day"].to_numpy(dtype=float), edges,
                  label=label, color=colour, linestyle=ls, linewidth=1.6)
    ax.set_xscale("symlog", linthresh=0.25, linscale=0.4)
    ax.set_xlim(0, float(table["freq_lo_per_day"].max()))
    ax.set_xlabel("best-pass frequency (d$^{-1}$); fixed left-closed/right-open edges; "
                  "symlog x (linear below 0.25)")
    ax.set_ylabel("share of confirmed per d$^{-1}$ (share / bin width)")
    ax.set_title("D1 published vs D3 negative-class confirmations: descriptive, no interval")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- extra relations

def yearly_alias(f_candidate: float, f_truth: float, tol: float) -> bool:
    return bool(
        abs(f_candidate - abs(f_truth + DELTA_YEAR_PER_DAY)) <= tol
        or abs(f_candidate - abs(f_truth - DELTA_YEAR_PER_DAY)) <= tol
    )


def kepler_nyquist_reflection(f_candidate: float, f_truth: float, tol: float) -> bool:
    f_ref = 2.0 * F_NYQ_PER_DAY - f_truth
    return bool(f_ref > 0 and abs(f_candidate - f_ref) <= tol)


def truth_lists_by_sid(per_star: pd.DataFrame, roster: pd.DataFrame,
                       table2_lists: dict[int, list[float]]) -> dict[str, list[float]]:
    kic = common.sid_to_kic(per_star, roster)
    return {sid: list(table2_lists.get(int(k), [])) for sid, k in zip(per_star["sid"], kic)}


def extra_relations(per_star: pd.DataFrame,
                    truth_by_sid: dict[str, list[float]]) -> pd.DataFrame:
    """One row per per_star row. Evaluability follows the frozen columns:
    a dominant relation is evaluated iff frozen_best_candidate_matches_dominant
    is scored (candidate and dominant both present); an any-mode relation iff
    frozen_best_candidate_matches_any_mode is scored. Inconsistency between
    the frozen columns and the inputs aborts."""
    common.check_per_star_columns(per_star)
    rows = []
    for r in per_star.itertuples(index=False):
        best = finite_float(r.best_frequency_per_day)
        baseline = finite_float(r.baseline_days)
        tol = tolerance_per_day(baseline)
        dominant = finite_float(r.primary_freq)
        truth = truth_by_sid.get(r.sid)
        if truth is None:
            raise SystemExit(f"{r.sid}: no truth list (roster/Mo join)")
        frozen_dom = str(r.best_candidate_matches_dominant)
        frozen_any = str(r.best_candidate_matches_any_mode)
        if frozen_dom not in common.MATCH_CLASSES_WITH_UNSCORED \
                or frozen_any not in common.MATCH_CLASSES_WITH_UNSCORED:
            raise SystemExit(f"{r.sid}: frozen match class outside the taxonomy")
        dom_scored = frozen_dom != UNSCORED
        any_scored = frozen_any != UNSCORED
        if dom_scored and (math.isnan(best) or math.isnan(dominant) or math.isnan(tol)):
            raise SystemExit(f"{r.sid}: frozen dominant match is scored but candidate/dominant/tolerance missing")
        if any_scored and (math.isnan(best) or not truth or math.isnan(tol)):
            raise SystemExit(f"{r.sid}: frozen any-mode match is scored but candidate/truth/tolerance missing")
        if not dom_scored and not math.isnan(best) and not math.isnan(dominant):
            raise SystemExit(f"{r.sid}: candidate and dominant present but frozen dominant match is unscored")
        if not any_scored and not math.isnan(best) and truth:
            raise SystemExit(f"{r.sid}: candidate and table-2 modes present but frozen any-mode match is unscored")
        rows.append({
            "sid": r.sid, "best_status": r.best_status,
            "best_frequency_per_day": best, "baseline_days": baseline,
            "tolerance_per_day": tol,
            "frozen_best_candidate_matches_dominant": frozen_dom,
            "frozen_best_candidate_matches_any_mode": frozen_any,
            "matches_yearly_alias_dominant": (
                yearly_alias(best, dominant, tol) if dom_scored else pd.NA),
            "matches_yearly_alias_any_mode": (
                any(yearly_alias(best, f_t, tol) for f_t in truth) if any_scored else pd.NA),
            "matches_kepler_nyquist_reflection_dominant": (
                kepler_nyquist_reflection(best, dominant, tol) if dom_scored else pd.NA),
            "matches_kepler_nyquist_reflection_any_mode": (
                any(kepler_nyquist_reflection(best, f_t, tol) for f_t in truth)
                if any_scored else pd.NA),
        })
    table = pd.DataFrame(rows)
    for col in ("matches_yearly_alias_dominant", "matches_yearly_alias_any_mode",
                "matches_kepler_nyquist_reflection_dominant",
                "matches_kepler_nyquist_reflection_any_mode"):
        table[col] = table[col].astype("boolean")
    return common.with_status(table)[RELATION_COLUMNS]


def assert_dominant_matches_roster(per_star: pd.DataFrame, roster: pd.DataFrame) -> None:
    """The metrics' primary_freq must be the roster's dom_freq_per_day for
    every star (guards against a roster/per_star mismatch)."""
    lookup = roster.set_index("source_id")["dom_freq_per_day"]
    for sid, primary in zip(per_star["sid"], per_star["primary_freq"]):
        a = finite_float(primary)
        b = finite_float(lookup.get(sid, math.nan))
        if math.isnan(a) and math.isnan(b):
            continue
        if math.isnan(a) != math.isnan(b) or not math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0):
            raise SystemExit(f"{sid}: per_star primary_freq {primary} != roster dom_freq_per_day {b}")


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--d1-catalog", type=Path, default=common.DEFAULT_D1_CATALOG,
                        help="published 928-star D1 catalog (ls_full_catalog.csv)")
    parser.add_argument("--roster", type=Path, default=common.DEFAULT_ROSTER)
    parser.add_argument("--mo-table2", type=Path, default=common.DEFAULT_MO_TABLE2)
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args(argv)

    assert_frozen()
    metrics_manifest, per_star = common.load_metrics_bundle(args.metrics_dir)
    catalog = pd.read_csv(args.d1_catalog, dtype={"source_id": str})
    roster = common.load_roster(args.roster)
    table2 = common.load_mo_table2(args.mo_table2)
    assert_dominant_matches_roster(per_star, roster)

    hist = histogram_table({
        D1_DATASET: (D1_SELECTION, d1_confirmed_frequencies(catalog)),
        D3_DATASET: (D3_SELECTION, d3_negative_confirmed_frequencies(per_star)),
    })
    relations = extra_relations(
        per_star, truth_lists_by_sid(per_star, roster, common.table2_per_day_lists(table2)))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_hist = args.out_dir / HIST_CSV
    out_png = args.out_dir / HIST_PNG
    out_meta = args.out_dir / HIST_META
    out_rel = args.out_dir / RELATIONS_CSV
    common.write_csv(hist, out_hist, HIST_COLUMNS)
    plot_histogram(hist, out_png)
    common.write_csv(relations, out_rel, RELATION_COLUMNS)
    totals = {d: int(hist.loc[hist["dataset"] == d, "n_confirmed_total"].iloc[0])
              for d in (D1_DATASET, D3_DATASET)}
    overflow = {d: int(hist.loc[(hist["dataset"] == d) & ~np.isfinite(hist["freq_hi_per_day"]), "n_bin"].sum())
                for d in (D1_DATASET, D3_DATASET)}
    meta = {
        **common.STATUS_FIELDS,
        "figure": HIST_PNG, "source_csv": HIST_CSV,
        "source_csv_sha256": sha256_file(out_hist), "png_sha256": sha256_file(out_png),
        "edges_per_day": [e if math.isfinite(e) else "inf" for e in HIST_EDGES],
        "bins": "left-closed/right-open; final finite edge 1440 included in the overflow bin [1440, inf)",
        "normalisation": "each dataset separately by its confirmed count (share_of_confirmed)",
        "density_per_day": "share_of_confirmed / (freq_hi - freq_lo) for finite bins; blank for the overflow bin",
        "selections": {D1_DATASET: D1_SELECTION, D3_DATASET: D3_SELECTION},
        "n_confirmed_total": totals, "n_overflow_ge_1440": overflow,
        "plot": "density (share per d^-1) as step outlines over the finite bins; symlog x axis "
                "(linear below 0.25 d^-1) so the [0, 0.25) bin is drawn; overflow counts in the legend",
        "verdict_file": common.VERDICT_FILE,
    }
    common.write_json(out_meta, meta)
    (args.out_dir / README_FILE).write_text(
        "# D3 frequency audits (descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n"
        f"Ruling: {common.VERDICT_FILE}, item 9 (F32/F33, ADMIT-DESCRIPTIVE).\n"
        f"Fields on every row: analysis_status={common.ANALYSIS_STATUS}, "
        f"prespecified={str(common.PRESPECIFIED).lower()}, interval={common.INTERVAL}.\n\n"
        f"- {HIST_CSV} / {HIST_PNG} / {HIST_META}: D1 = {D1_SELECTION}; D3 = {D3_SELECTION}; "
        "fixed edges, left-closed/right-open, 1440 included in the overflow bin; each "
        "dataset normalised separately by its confirmed count; density_per_day = "
        "share/bin_width for finite bins.\n"
        f"- {RELATIONS_CSV}: one row per per_star.csv row; delta_year = 1/365.25 = "
        f"{DELTA_YEAR_PER_DAY!r} d^-1, f_Nyq = {F_NYQ_PER_DAY} d^-1, tol = 1.5/baseline_days; "
        "yearly_alias: |f_candidate - |f_truth +/- delta_year|| <= tol; "
        "kepler_nyquist_reflection: f_ref = 2 f_Nyq - f_truth, f_ref > 0 and "
        "|f_candidate - f_ref| <= tol; evaluated for the dominant frequency and, "
        "separately, every table-2 mode; independent booleans (harmonics and sidereal "
        "aliases not folded in); blank wherever the corresponding frozen match column is "
        "`unscored`. These columns are never added to the frozen per_star.csv.\n",
        encoding="utf-8",
    )
    manifest = {
        **common.provenance_block(Path(__file__)),
        "item": "sol_round2 item 9 (F32/F33)",
        "constants": {"delta_year_per_day": DELTA_YEAR_PER_DAY, "f_nyq_per_day": F_NYQ_PER_DAY,
                      "tolerance": "1.5 / baseline_days",
                      "edges_per_day": [e if math.isfinite(e) else "inf" for e in HIST_EDGES]},
        "inputs_sha256": {
            "per_star.csv": sha256_file(args.metrics_dir / "per_star.csv"),
            "metrics_manifest.json": sha256_file(args.metrics_dir / "manifest.json"),
            str(args.d1_catalog): sha256_file(args.d1_catalog),
            str(args.roster): sha256_file(args.roster),
            str(args.mo_table2): sha256_file(args.mo_table2),
        },
        "outputs_sha256": {
            HIST_CSV: sha256_file(out_hist), HIST_PNG: sha256_file(out_png),
            HIST_META: sha256_file(out_meta), RELATIONS_CSV: sha256_file(out_rel),
        },
        "metrics_bundle": {"dataset": metrics_manifest.get("dataset"),
                           "pilot": bool(metrics_manifest.get("pilot", False))},
        "counts": {
            "n_confirmed_total": totals, "n_overflow_ge_1440": overflow,
            "relations_rows": int(len(relations)),
            "relations_true": {
                col: int(relations[col].fillna(False).sum())
                for col in ("matches_yearly_alias_dominant", "matches_yearly_alias_any_mode",
                            "matches_kepler_nyquist_reflection_dominant",
                            "matches_kepler_nyquist_reflection_any_mode")},
            "relations_evaluated": {
                col: int(relations[col].notna().sum())
                for col in ("matches_yearly_alias_dominant", "matches_yearly_alias_any_mode",
                            "matches_kepler_nyquist_reflection_dominant",
                            "matches_kepler_nyquist_reflection_any_mode")},
        },
    }
    common.write_json(args.out_dir / MANIFEST_FILE, manifest)
    print(hist.to_string(index=False))
    print(f"[frequency_audits] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
