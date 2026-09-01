#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE truth-provenance audit of the D3 frequency
comparison (ruling: generalization/reviews/G5prep/sol_round2.md, item 2,
F02-F04, ADMIT-DESCRIPTIVE, fixed 2026-09-01 before any full-campaign D3
metric existed). Two files:

  descriptive_postlaunch/d3_truth_provenance_rescoring.csv
      one row per ALIASED-DOMINANT dsct_flag1 target (ruled: exactly 40):
      a positive is aliased_dominant=true when at least one Mo table-1 row
      with C==0 satisfies |table1.Freq - roster.dom_freq_uhz| <= 0.1 µHz
      (several rows: minimum absolute difference, then minimum fR). For
      each, fR is converted with 86400/1e6 and the ENTIRE frozen taxonomy
      (classify_match, imported — never re-implemented) is applied to the
      best candidate against that single physical frequency with
      tolerance_per_day = 1.5 / baseline_days. The independent boolean
      matches_nyquist_reflection = |f_candidate - (2*24.46848 - fR_per_day)|
      <= tolerance_per_day (positive reflected frequencies only) never
      alters the frozen taxonomy. Any-mode-plus-fR scoring uses the exact
      union of all finite table-2 frequencies for the KIC and all finite
      table-1 fR values with C==0.
  descriptive_postlaunch/d3_p2_by_dominant_frequency_regime.csv
      the exact frozen P2 frame (dsct_flag1, Mo-joined/freq-scorable, both
      passes available, S_best=1, rule 1, best pass) split by the dominant
      frequency: [-inf,4), [4,24), [24,inf) d^-1; success remains
      best_status=="confirmed" and frozen dominant match class `direct`;
      the >=24 row is counts-only.

"Dominant" is the largest-amplitude Mo table-2 mode, which need not be a p
mode. Frozen P2 is unchanged; nothing here enters a headline, endpoint,
exclusion, reclassification, or replacement denominator. FULL-run only.

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402,F401
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)
from metrics_generalization import classify_match  # noqa: E402
import d3_descriptive_common as common  # noqa: E402
from d3_descriptive_common import (  # noqa: E402
    F_NYQ_PER_DAY,
    MISSING_STATUS,
    POSITIVE_CLASS,
    RULE,
    STATUS_COLUMNS,
    UNSCORED,
    finite_float,
    sha256_file,
    tolerance_per_day,
    truthy,
    uhz_to_per_day,
)

TABLE1_MATCH_TOL_UHZ = 0.1
EXPECTED_ALIASED = 40
REGIMES = (
    ("dominant_lt_4", -math.inf, 4.0),
    ("dominant_4_to_24", 4.0, 24.0),
    ("dominant_ge_24", 24.0, math.inf),
)
COUNTS_ONLY_REGIMES = ("dominant_ge_24",)

RESCORING_FILE = "d3_truth_provenance_rescoring.csv"
REGIME_FILE = "d3_p2_by_dominant_frequency_regime.csv"
README_FILE = "d3_truth_provenance.README.md"
MANIFEST_FILE = "d3_truth_provenance.manifest.json"

RESCORING_COLUMNS = [
    "sid", "KIC", "best_status", "best_frequency_per_day", "baseline_days",
    "tolerance_per_day", "aliased_dominant", "table1_alias_uhz", "fR_uhz",
    "fR_per_day", "nyquist_reflection_per_day", "best_candidate_match_fR",
    "matches_nyquist_reflection", "best_candidate_matches_any_mode_plus_fR",
    "any_top_peak_matches_any_mode_plus_fR", *STATUS_COLUMNS,
]
REGIME_COLUMNS = [
    "dominant_frequency_regime", "lo_inclusive_per_day", "hi_exclusive_per_day",
    "n_p2", "k_confirmed", "k_direct_recovery", "rate_direct_recovery",
    *STATUS_COLUMNS,
]

DISCLOSURE = (
    "Post-launch descriptive truth-provenance audit: frozen P2 remains an "
    "unchanged best-pass comparison against the largest-amplitude Mo table-2 "
    "frequency, while the added files report physical-\\(f_R\\), "
    "Kepler-Nyquist-reflection, augmented-any-mode, and "
    "dominant-frequency-regime counts without replacing P2; “dominant” "
    "means largest amplitude rather than necessarily a p mode, and the former "
    "“sub-hour stratum” is described as stars with a confirmed "
    "super-Nyquist mode."
)


# ---------------------------------------------------------------- aliased targets

def select_aliased_dominant(roster: pd.DataFrame, table1: pd.DataFrame) -> pd.DataFrame:
    """One row per aliased-dominant dsct_flag1 positive: the table-1 C==0 row
    with |Freq - dom_freq_uhz| <= 0.1 µHz, tie-break minimum absolute
    difference then minimum fR (deterministic, as ruled)."""
    c0 = common.table1_c0(table1)
    by_kic = {int(k): g for k, g in c0.groupby("KIC")}
    positives = roster[roster["class_label"] == POSITIVE_CLASS]
    rows = []
    for r in positives.itertuples(index=False):
        dom = finite_float(r.dom_freq_uhz)
        if math.isnan(dom):
            continue
        group = by_kic.get(int(r.KIC))
        if group is None:
            continue
        diff = (group["Freq"] - dom).abs()
        within = diff <= TABLE1_MATCH_TOL_UHZ
        if not within.any():
            continue
        cands = group.loc[within].assign(abs_diff_uhz=diff[within])
        best = cands.sort_values(["abs_diff_uhz", "fR"], kind="mergesort").iloc[0]
        rows.append({
            "sid": r.source_id, "KIC": int(r.KIC), "dom_freq_uhz": dom,
            "table1_alias_uhz": float(best["Freq"]), "fR_uhz": float(best["fR"]),
            "abs_diff_uhz": float(best["abs_diff_uhz"]),
            "n_qualifying_rows": int(within.sum()),
        })
    return pd.DataFrame(rows, columns=[
        "sid", "KIC", "dom_freq_uhz", "table1_alias_uhz", "fR_uhz",
        "abs_diff_uhz", "n_qualifying_rows"])


def json_sha_map(inputs_sha256: dict) -> dict[str, str]:
    """basename -> SHA-256 of every scored result JSON in the metrics bundle's
    inputs_sha256.json (keys are machine paths; sidecars excluded)."""
    out: dict[str, str] = {}
    for key, sha in inputs_sha256.items():
        name = str(key).replace("\\", "/").rsplit("/", 1)[-1]
        if not name.endswith(".json") or name.endswith(".prov.json"):
            continue
        if name in out and out[name] != sha:
            raise SystemExit(f"inputs_sha256.json lists {name} with two different SHAs")
        out[name] = sha
    return out


def load_top_peaks(stars_dir: Path, sids: list[str], statuses: dict[str, str],
                   sha_by_name: dict[str, str]) -> tuple[dict[str, list[float]], dict[str, str]]:
    """Stored top-15 peaks (both passes) for each target, read from the very
    JSONs the frozen metrics scored (SHA-bound to the bundle). A target with
    best_status=="missing" has no result and yields no peaks."""
    peaks: dict[str, list[float]] = {}
    used: dict[str, str] = {}
    for sid in sids:
        if statuses[sid] == MISSING_STATUS:
            peaks[sid] = []
            continue
        path = Path(stars_dir) / f"{sid}.json"
        if not path.exists():
            raise SystemExit(f"{sid}: per_star has a result but {path} does not exist")
        sha = sha256_file(path)
        recorded = sha_by_name.get(path.name)
        if recorded is None:
            raise SystemExit(f"{sid}: {path.name} is not among the metrics bundle's scored inputs")
        if recorded != sha:
            raise SystemExit(f"{sid}: {path.name} differs from the JSON the frozen metrics scored")
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("source_id") != sid or not result.get("complete"):
            raise SystemExit(f"{sid}: result JSON is not a complete result for this sid")
        freqs: list[float] = []
        for name in ("low", "high"):
            for peak in result["passes"][name].get("top_peaks", []):
                f_peak = peak.get("frequency_per_day")
                if f_peak is not None:
                    freqs.append(float(f_peak))
        peaks[sid] = freqs
        used[str(path)] = sha
    return peaks, used


# ---------------------------------------------------------------- rescoring table

def rescoring_table(targets: pd.DataFrame, per_star: pd.DataFrame,
                    table2_lists: dict[int, list[float]], table1_c0: pd.DataFrame,
                    peaks_by_sid: dict[str, list[float]],
                    expected_aliased: int = EXPECTED_ALIASED) -> pd.DataFrame:
    if len(targets) != expected_aliased:
        raise SystemExit(
            f"{len(targets)} aliased-dominant {POSITIVE_CLASS} targets != the "
            f"ruled {expected_aliased}; refusing"
        )
    if targets["sid"].duplicated().any():
        raise SystemExit("duplicate aliased-dominant targets")
    per_sid = per_star.set_index("sid")
    fr_by_kic = table1_c0.groupby("KIC")["fR"].apply(list).to_dict()
    rows = []
    for t in targets.itertuples(index=False):
        if t.sid not in per_sid.index:
            raise SystemExit(f"{t.sid}: aliased-dominant target absent from per_star.csv")
        r = per_sid.loc[t.sid]
        if r["class_label"] != POSITIVE_CLASS:
            raise SystemExit(f"{t.sid}: aliased-dominant target is not {POSITIVE_CLASS} in per_star.csv")
        best = finite_float(r["best_frequency_per_day"])
        baseline = finite_float(r["baseline_days"])
        tol = tolerance_per_day(baseline)
        if not math.isnan(best) and math.isnan(tol):
            raise SystemExit(f"{t.sid}: candidate frequency without a finite baseline")
        fr_per_day = uhz_to_per_day(t.fR_uhz)
        reflection = 2.0 * F_NYQ_PER_DAY - fr_per_day
        union = sorted(
            set(table2_lists.get(int(t.KIC), []))
            | {uhz_to_per_day(x) for x in fr_by_kic.get(int(t.KIC), [])}
        )
        if not union:  # pragma: no cover - the selected C==0 row is itself in the union
            raise SystemExit(f"{t.sid}: empty any-mode-plus-fR truth union")
        scored = not math.isnan(best)
        if scored:
            match_fr = classify_match(best, [fr_per_day], tol)
            matches_reflection = bool(reflection > 0 and abs(best - reflection) <= tol)
            match_any_plus = classify_match(best, union, tol)
        else:
            match_fr = UNSCORED
            matches_reflection = pd.NA
            match_any_plus = UNSCORED
        peaks = peaks_by_sid.get(t.sid, [])
        any_top = bool(
            not math.isnan(tol)
            and any(classify_match(float(f), union, tol) == "direct" for f in peaks)
        )
        rows.append({
            "sid": t.sid, "KIC": int(t.KIC), "best_status": r["best_status"],
            "best_frequency_per_day": best if scored else math.nan,
            "baseline_days": baseline, "tolerance_per_day": tol,
            "aliased_dominant": True,
            "table1_alias_uhz": float(t.table1_alias_uhz), "fR_uhz": float(t.fR_uhz),
            "fR_per_day": fr_per_day, "nyquist_reflection_per_day": reflection,
            "best_candidate_match_fR": match_fr,
            "matches_nyquist_reflection": matches_reflection,
            "best_candidate_matches_any_mode_plus_fR": match_any_plus,
            "any_top_peak_matches_any_mode_plus_fR": any_top,
        })
    table = pd.DataFrame(rows)
    table["matches_nyquist_reflection"] = table["matches_nyquist_reflection"].astype("boolean")
    return common.with_status(table)[RESCORING_COLUMNS]


# ---------------------------------------------------------------- regime split

def p2_regime_table(per_star: pd.DataFrame,
                    expected_positives: int = common.EXPECTED_POSITIVES,
                    expected_scorable: int = common.EXPECTED_MO_JOINED) -> pd.DataFrame:
    frame = common.p2_frame(per_star, expected_positives, expected_scorable)
    dom = frame["primary_freq"].to_numpy(dtype=float)
    confirmed = (frame["best_status"] == RULE).to_numpy()
    direct = confirmed & (frame["best_candidate_matches_dominant"] == "direct").to_numpy()
    rows = []
    for name, lo, hi in REGIMES:
        mask = (dom >= lo) & (dom < hi)
        n = int(mask.sum())
        k_c = int((confirmed & mask).sum())
        k_d = int((direct & mask).sum())
        rate = k_d / n if (n and name not in COUNTS_ONLY_REGIMES) else math.nan
        rows.append({
            "dominant_frequency_regime": name, "lo_inclusive_per_day": lo,
            "hi_exclusive_per_day": hi, "n_p2": n, "k_confirmed": k_c,
            "k_direct_recovery": k_d, "rate_direct_recovery": rate,
        })
    table = common.with_status(pd.DataFrame(rows))[REGIME_COLUMNS]
    if int(table["n_p2"].sum()) != len(frame):  # pragma: no cover - partition identity
        raise SystemExit("regime partition does not cover the P2 frame")
    return table


def verify_against_completeness(regime: pd.DataFrame, completeness: pd.DataFrame) -> None:
    """The regime rows must reproduce the frozen P2 point estimate exactly
    (unit positive weights make weighted p == k/n up to float roundoff)."""
    p2 = completeness[(completeness["pass"] == "best") & (completeness["rule"] == RULE)
                      & (completeness["scope"] == "freq_recovery_scorable")]
    if len(p2) != 1:
        raise SystemExit("completeness_by_class_pass_rule.csv has no unique P2 row")
    n = int(regime["n_p2"].sum())
    k = int(regime["k_direct_recovery"].sum())
    if int(p2["n"].iloc[0]) != n:
        raise SystemExit(f"P2 n ({int(p2['n'].iloc[0])}) != regime frame size ({n})")
    p_frozen = float(p2["p"].iloc[0])
    if n == 0:
        if not math.isnan(p_frozen):
            raise SystemExit("empty P2 frame but a finite frozen P2 estimate")
        return
    if not math.isclose(p_frozen, k / n, rel_tol=1e-9, abs_tol=1e-12):
        raise SystemExit(
            f"regime numerator {k}/{n} does not reproduce the frozen P2 estimate {p_frozen}"
        )


def assert_scorable_identity(per_star: pd.DataFrame, roster: pd.DataFrame,
                             table2: pd.DataFrame,
                             expected: int = common.EXPECTED_MO_JOINED) -> set[int]:
    """The per_star freq_scorable dsct_flag1 set must be exactly the ruled
    mo_joined set (item 1's 456-star guard), re-derived from the roster and
    Mo table 2."""
    joined = common.mo_joined_kics(roster, table2)
    if len(joined) != expected:
        raise SystemExit(f"{len(joined)} Mo-joined {POSITIVE_CLASS} KICs != the ruled {expected}")
    pos = per_star[per_star["class_label"] == POSITIVE_CLASS]
    kic = common.sid_to_kic(pos, roster)
    scorable = set(kic[pos["freq_scorable"].map(truthy).to_numpy()].astype(int))
    if scorable != joined:
        raise SystemExit(
            "per_star freq_scorable positives are not the ruled mo_joined set "
            f"({len(scorable ^ joined)} symmetric-difference KICs)"
        )
    return joined


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--stars-dir", type=Path, default=None,
                        help="per-star result JSONs the metrics scored "
                             "(default: <metrics-dir>/../run/stars)")
    parser.add_argument("--roster", type=Path, default=common.DEFAULT_ROSTER)
    parser.add_argument("--mo-table1", type=Path, default=common.DEFAULT_MO_TABLE1)
    parser.add_argument("--mo-table2", type=Path, default=common.DEFAULT_MO_TABLE2)
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args(argv)

    assert_frozen()
    metrics_manifest, per_star = common.load_metrics_bundle(args.metrics_dir)
    stars_dir = args.stars_dir or (args.metrics_dir.resolve().parent / "run" / "stars")
    inputs_sha_path = args.metrics_dir / "inputs_sha256.json"
    if not inputs_sha_path.exists():
        raise SystemExit(f"metrics bundle has no inputs_sha256.json: {inputs_sha_path}")
    sha_by_name = json_sha_map(json.loads(inputs_sha_path.read_text(encoding="utf-8")))
    completeness_path = args.metrics_dir / "completeness_by_class_pass_rule.csv"
    if not completeness_path.exists():
        raise SystemExit(f"metrics bundle has no completeness table: {completeness_path}")
    completeness = pd.read_csv(completeness_path)

    roster = common.load_roster(args.roster)
    table1 = common.load_mo_table1(args.mo_table1)
    table2 = common.load_mo_table2(args.mo_table2)
    common.positives_frame(per_star)
    assert_scorable_identity(per_star, roster, table2)

    targets = select_aliased_dominant(roster, table1)
    if len(targets) != EXPECTED_ALIASED:
        raise SystemExit(
            f"{len(targets)} aliased-dominant {POSITIVE_CLASS} targets != the ruled "
            f"{EXPECTED_ALIASED}; refusing"
        )
    statuses = per_star.set_index("sid")["best_status"].to_dict()
    for sid in targets["sid"]:
        if sid not in statuses:
            raise SystemExit(f"{sid}: aliased-dominant target absent from per_star.csv")
    peaks, json_shas = load_top_peaks(stars_dir, targets["sid"].tolist(), statuses, sha_by_name)
    rescoring = rescoring_table(targets, per_star, common.table2_per_day_lists(table2),
                                common.table1_c0(table1), peaks)
    regime = p2_regime_table(per_star)
    verify_against_completeness(regime, completeness)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_rescoring = args.out_dir / RESCORING_FILE
    out_regime = args.out_dir / REGIME_FILE
    common.write_csv(rescoring, out_rescoring, RESCORING_COLUMNS)
    common.write_csv(regime, out_regime, REGIME_COLUMNS)
    (args.out_dir / README_FILE).write_text(
        "# D3 truth-provenance audit (descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n"
        f"Ruling: {common.VERDICT_FILE}, item 2 (F02-F04, ADMIT-DESCRIPTIVE).\n"
        f"Fields on every row: analysis_status={common.ANALYSIS_STATUS}, "
        f"prespecified={str(common.PRESPECIFIED).lower()}, interval={common.INTERVAL}.\n\n"
        f"- {RESCORING_FILE}: one row per aliased-dominant dsct_flag1 target "
        f"(table-1 C==0 row with |Freq - dom_freq_uhz| <= {TABLE1_MATCH_TOL_UHZ} µHz; "
        "tie-break minimum absolute difference, then minimum fR; exactly "
        f"{EXPECTED_ALIASED}). fR_per_day = fR_uhz * 86400/1e6; the frozen taxonomy "
        "(classify_match, imported) is applied to the best candidate against that "
        "single physical frequency with tolerance_per_day = 1.5/baseline_days. "
        f"matches_nyquist_reflection = |f_candidate - (2*{F_NYQ_PER_DAY} - fR_per_day)| "
        "<= tolerance_per_day, positive reflected frequencies only; an independent "
        "boolean that never alters the frozen taxonomy. Any-mode-plus-fR uses the "
        "exact union of all finite table-2 frequencies for the KIC and all finite "
        "table-1 fR values with C==0; any_top_peak_* is direct agreement by any "
        "stored top-15 peak. Targets without a result carry best_status=missing, "
        "taxonomy cells `unscored`, and a blank matches_nyquist_reflection.\n"
        f"- {REGIME_FILE}: the exact frozen P2 frame split at 4 and 24 d^-1 "
        "(left-closed/right-open); success = best_status==confirmed and frozen "
        "dominant match `direct`; the >=24 row is counts-only (rate blank). The "
        "fixed roster contains 10 of 456 dominant frequencies in [24, 24.46848); "
        "the empty statement applies at >=24.47, not at >=24. \"Dominant\" is the "
        "largest-amplitude Mo table-2 mode, which need not be a p mode; the former "
        "\"sub-hour stratum\" is described as stars with a confirmed super-Nyquist "
        "mode.\n",
        encoding="utf-8",
    )
    manifest = {
        **common.provenance_block(Path(__file__)),
        "item": "sol_round2 item 2 (F02-F04)",
        "constants": {
            "table1_match_tolerance_uhz": TABLE1_MATCH_TOL_UHZ,
            "f_nyq_uhz": common.F_NYQ_UHZ, "f_nyq_per_day": F_NYQ_PER_DAY,
            "uhz_to_per_day": "x * 86400.0 / 1e6 (the frozen truth loader's expression)",
            "tolerance": "1.5 / baseline_days",
            "regimes": [{"name": n, "lo_inclusive": lo, "hi_exclusive": hi} for n, lo, hi in REGIMES],
            "counts_only_regimes": list(COUNTS_ONLY_REGIMES),
        },
        "inputs_sha256": {
            "per_star.csv": sha256_file(args.metrics_dir / "per_star.csv"),
            "metrics_manifest.json": sha256_file(args.metrics_dir / "manifest.json"),
            "inputs_sha256.json": sha256_file(inputs_sha_path),
            "completeness_by_class_pass_rule.csv": sha256_file(completeness_path),
            str(args.roster): sha256_file(args.roster),
            str(args.mo_table1): sha256_file(args.mo_table1),
            str(args.mo_table2): sha256_file(args.mo_table2),
            **json_shas,
        },
        "outputs_sha256": {
            RESCORING_FILE: sha256_file(out_rescoring),
            REGIME_FILE: sha256_file(out_regime),
        },
        "metrics_bundle": {"dataset": metrics_manifest.get("dataset"),
                           "pilot": bool(metrics_manifest.get("pilot", False)),
                           "stars_dir": str(stars_dir)},
        "counts": {
            "n_aliased_dominant": int(len(rescoring)),
            "n_aliased_with_result": int((rescoring["best_status"] != MISSING_STATUS).sum()),
            "best_candidate_match_fR": rescoring["best_candidate_match_fR"].value_counts().to_dict(),
            "matches_nyquist_reflection_true": int(rescoring["matches_nyquist_reflection"].fillna(False).sum()),
            "best_candidate_matches_any_mode_plus_fR":
                rescoring["best_candidate_matches_any_mode_plus_fR"].value_counts().to_dict(),
            "any_top_peak_matches_any_mode_plus_fR_true":
                int(rescoring["any_top_peak_matches_any_mode_plus_fR"].sum()),
            "regime": {r.dominant_frequency_regime: {"n_p2": int(r.n_p2), "k_confirmed": int(r.k_confirmed),
                                                     "k_direct_recovery": int(r.k_direct_recovery)}
                       for r in regime.itertuples()},
        },
    }
    common.write_json(args.out_dir / MANIFEST_FILE, manifest)
    print(rescoring.to_string(index=False))
    print(regime.to_string(index=False))
    print(f"[truth_provenance] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
