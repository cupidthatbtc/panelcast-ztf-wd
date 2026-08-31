#!/usr/bin/env python3
"""Post-launch, pilot-informed DESCRIPTIVE partition of the D3 negative-class
trigger rate (P3) into solar-diurnal-band vs outside-band components.

Admitted by generalization/reviews/G5prep/sol_diurnal.md (ADMIT-AS-DESCRIPTIVE,
2026-08-31), adjudicated BEFORE any full-campaign D3 metric was computed. The
binding terms (also in reviews/G2_FREEZE.md, entry 2026-08-31):

- P3 itself is UNCHANGED: rule 1 (confirmed), best pass, all 2,314 dsct_flag0
  roster members (missing/unusable = non-trigger), frozen Wilson interval.
- This file computes an arithmetic partition of P3's observed NUMERATOR only:
    within_solar_diurnal_band  iff  f < 4/d  and
        min_{k in 1..3} |f - k * 1.000000/d| <= 0.020000/d   (closed endpoints)
  i.e. bands [0.980,1.020], [1.980,2.020], [2.980,3.020] cycles/day.
- Abort rather than classify silently if any confirmed negative lacks a finite
  best-pass frequency. No low-frequency-floor term.
- No confidence intervals, tests, acceptance thresholds, or weighting. The
  outside-band component is NEVER a "corrected" or "de-aliased" P3. Never
  applied to the census rate. Not used to veto/exclude/reclassify anything.
- FULL-run only (refuses pilot metrics bundles).

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive), so committing/pulling it is SHA-neutral for live runners.

Inputs: a completed D3 metrics out-dir (per_star.csv, trigger_rates.csv,
manifest.json). Outputs (out-dir): d3_trigger_decomposition.csv, README.md
(the verbatim disclosure sentence), manifest.json (input/output SHAs).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)

BAND_HARMONICS = (1, 2, 3)
BAND_CENTER_PER_DAY = 1.000000
BAND_HALF_WIDTH_PER_DAY = 0.020000
F_MAX_PER_DAY = 4.0
# IEEE-754 guard so the DECIMAL closed endpoints [0.980, 1.020] etc. hold as
# ruled: |1.020 - 1.0| in doubles is 0.020000000000000018. 1e-9 is five orders
# below the frozen grid step (~3.7e-5/d), so it can only ever absorb decimal-
# representation noise, never move a real grid frequency across the boundary.
FLOAT_GUARD_PER_DAY = 1e-9
EXPECTED_NEGATIVES = 2314
NEGATIVE_CLASS = "dsct_flag0"
RULE = "confirmed"
PASS_BASIS = "best"
ANALYSIS_STATUS = "postlaunch_pilot_informed_descriptive"
BAND_DEFINITION = (
    "f < 4/d and min_{k in 1..3} |f - k*1.000000/d| <= 0.020000/d "
    "(closed endpoints): [0.980,1.020] U [1.980,2.020] U [2.980,3.020] c/d"
)
VERDICT_FILE = "generalization/reviews/G5prep/sol_diurnal.md"
DISCLOSURE = (
    "Post-launch, pilot-informed descriptive analysis: after inspection of "
    "raw, unweighted per-pass statuses from the non-representative 150-star "
    "D3 timing pilot, and after the full D3 L-S run had launched but before "
    "any full-campaign metric was computed, we fixed the solar-diurnal "
    "frequency bands at union_{k=1..3} [k-0.020, k+0.020] / d; "
    "d3_trigger_decomposition.csv is an unweighted arithmetic partition of "
    "the frozen rule-1, best-pass D3 negative-class P3 numerator over its "
    "unchanged 2,314-star denominator, was not prespecified, carries no "
    "interval or confirmatory interpretation, is not used to veto, exclude, "
    "or reclassify any trigger, and does not establish that an individual "
    "band member is instrumental rather than astrophysical."
)

COLUMNS = [
    "component", "rule", "pass_basis", "n_negative", "n_confirmed_total",
    "n_component", "rate_of_all_negatives", "share_of_confirmed",
    "band_definition", "analysis_status", "prespecified", "interval",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within_band(freq: float) -> bool:
    """The frozen band rule, exactly as ruled: closed endpoints."""
    if not (freq < F_MAX_PER_DAY):
        return False
    return min(
        abs(freq - k * BAND_CENTER_PER_DAY) for k in BAND_HARMONICS
    ) <= BAND_HALF_WIDTH_PER_DAY + FLOAT_GUARD_PER_DAY


def decompose(per_star: pd.DataFrame,
              expected_negatives: int = EXPECTED_NEGATIVES) -> pd.DataFrame:
    """Pure arithmetic partition of the P3 numerator. No discretion anywhere."""
    negatives = per_star[per_star["class_label"] == NEGATIVE_CLASS]
    if len(negatives) != expected_negatives:
        raise SystemExit(
            f"{len(negatives)} {NEGATIVE_CLASS} rows != the frozen P3 "
            f"denominator {expected_negatives}; refusing to partition"
        )
    if negatives["sid"].duplicated().any():
        raise SystemExit("duplicate sids among the negatives")
    confirmed = negatives[negatives["best_status"] == RULE].copy()
    freq = pd.to_numeric(confirmed["best_frequency_per_day"], errors="coerce")
    finite = freq.notna() & freq.apply(
        lambda x: math.isfinite(float(x)) if pd.notna(x) else False
    )
    if not finite.all():
        bad = confirmed.loc[~finite, "sid"].tolist()
        raise SystemExit(
            "confirmed negatives without a finite best-pass frequency "
            f"(abort rather than classify silently): {bad[:10]}"
        )
    inside = freq.astype(float).apply(within_band)
    n_confirmed = int(len(confirmed))
    n_within = int(inside.sum())
    n_outside = n_confirmed - n_within
    if n_within + n_outside != n_confirmed:  # pragma: no cover - arithmetic identity
        raise SystemExit("partition identity violated")

    def row(component: str, n_component: int) -> dict:
        return {
            "component": component,
            "rule": RULE,
            "pass_basis": PASS_BASIS,
            "n_negative": expected_negatives,
            "n_confirmed_total": n_confirmed,
            "n_component": n_component,
            "rate_of_all_negatives": n_component / expected_negatives,
            "share_of_confirmed": (
                n_component / n_confirmed if n_confirmed else math.nan
            ),
            "band_definition": BAND_DEFINITION,
            "analysis_status": ANALYSIS_STATUS,
            "prespecified": False,
            "interval": "none",
        }

    table = pd.DataFrame(
        [row("within_solar_diurnal_band", n_within),
         row("outside_solar_diurnal_band", n_outside)],
        columns=COLUMNS,
    )
    total = table["rate_of_all_negatives"].sum()
    if not math.isclose(total, n_confirmed / expected_negatives, rel_tol=0, abs_tol=1e-15):
        raise SystemExit("rate identity violated")  # pragma: no cover
    return table


def verify_against_trigger_rates(table: pd.DataFrame,
                                 trigger_rates: pd.DataFrame) -> None:
    """The partition must reproduce the frozen P3 point estimate exactly
    (uniform dsct_flag0 weights make weighted p == k/n up to float roundoff)."""
    p3 = trigger_rates[
        (trigger_rates["quantity"] == "negative_class_trigger_rate")
        & (trigger_rates["rule"] == RULE)
    ]
    if len(p3) != 1:
        raise SystemExit("trigger_rates.csv has no unique rule-1 P3 row")
    n_conf = int(table["n_confirmed_total"].iloc[0])
    n_neg = int(table["n_negative"].iloc[0])
    if int(p3["n"].iloc[0]) != n_neg:
        raise SystemExit(
            f"P3 n ({int(p3['n'].iloc[0])}) != partition denominator ({n_neg})"
        )
    if not math.isclose(float(p3["p"].iloc[0]), n_conf / n_neg, rel_tol=1e-9):
        raise SystemExit(
            f"partition numerator {n_conf}/{n_neg} does not reproduce the "
            f"frozen P3 point estimate {float(p3['p'].iloc[0])}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args()

    assert_frozen()
    metrics_manifest = json.loads(
        (args.metrics_dir / "manifest.json").read_text(encoding="utf-8"))
    if metrics_manifest.get("dataset") != "d3":
        raise SystemExit("metrics bundle is not dataset d3")
    if metrics_manifest.get("pilot"):
        raise SystemExit("pilot metrics bundle: the decomposition is FULL-run only")
    per_star_path = args.metrics_dir / "per_star.csv"
    rates_path = args.metrics_dir / "trigger_rates.csv"
    per_star = pd.read_csv(per_star_path, dtype={"sid": str})
    trigger_rates = pd.read_csv(rates_path)

    table = decompose(per_star)
    verify_against_trigger_rates(table, trigger_rates)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / "d3_trigger_decomposition.csv"
    table.to_csv(out_csv, index=False, lineterminator="\n")
    readme = args.out_dir / "README.md"
    readme.write_text(
        "# D3 negative-class trigger decomposition (descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n"
        f"Band rule: {BAND_DEFINITION}\n\n"
        f"Admission verdict: {VERDICT_FILE} (ADMIT-AS-DESCRIPTIVE); binding\n"
        "terms recorded in generalization/reviews/G2_FREEZE.md (2026-08-31\n"
        "entry). P3 and fp_frequency_distribution.csv (the prespecified\n"
        "frequency audit) are unchanged; this table is not applied to the\n"
        "census rate and carries no interval.\n",
        encoding="utf-8",
    )
    verdict_path = REPO_ROOT / VERDICT_FILE
    manifest = {
        "analysis_status": ANALYSIS_STATUS,
        "band": {"harmonics": list(BAND_HARMONICS),
                 "center_per_day": BAND_CENTER_PER_DAY,
                 "half_width_per_day": BAND_HALF_WIDTH_PER_DAY,
                 "f_max_per_day": F_MAX_PER_DAY,
                 "float_guard_per_day": FLOAT_GUARD_PER_DAY,
                 "definition": BAND_DEFINITION},
        "inputs_sha256": {
            "per_star.csv": sha256_file(per_star_path),
            "trigger_rates.csv": sha256_file(rates_path),
            "metrics_manifest.json": sha256_file(args.metrics_dir / "manifest.json"),
            **({VERDICT_FILE: sha256_file(verdict_path)} if verdict_path.exists() else {}),
        },
        "outputs_sha256": {"d3_trigger_decomposition.csv": sha256_file(out_csv)},
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
        "counts": {r.component: int(r.n_component) for r in table.itertuples()},
        "n_confirmed_total": int(table["n_confirmed_total"].iloc[0]),
        "n_negative": int(table["n_negative"].iloc[0]),
    }
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(table.to_string(index=False))
    print(f"[decomposition] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
