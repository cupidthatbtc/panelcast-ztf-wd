#!/usr/bin/env python3
"""Regenerate the incremental full-catalog results report."""

import argparse
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAPER_LADDER = {
    "Eq. 3 selection": 22264,
    "variability candidates": 1423,
    "ZTF crossmatches": 894,
    "clean light curves": 864,
    "periodic": 141,
    "undetermined": 7,
}


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().eq("true")


def fmt(value: object, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{number:.{digits}f}" if math.isfinite(number) else "—"


def roster_table(census: pd.DataFrame, qc: pd.DataFrame) -> list[str]:
    merged = qc.merge(census, on="source_id", how="left", suffixes=("_qc", ""))
    known_column = "known_roster_qc" if "known_roster_qc" in merged else "known_roster"
    known = merged[as_bool(merged[known_column].fillna(False))].copy()
    known = known.sort_values("source_id")
    lines = [
        "| Gaia DR3 | class | crossmatched | g exp | g night | g month | census |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in known.itertuples(index=False):
        crossmatched = str(getattr(row, "crossmatched", False)).lower() == "true"
        wd_class = getattr(row, "wd_class", None)
        if pd.isna(wd_class):
            wd_class = getattr(row, "wd_class_qc", "unclassified")
        verdict = getattr(row, "census_verdict", "—") if crossmatched else "unavailable"
        lines.append(
            f"| {row.source_id} | {wd_class} | {'yes' if crossmatched else 'no'} | "
            f"{fmt(getattr(row, 'zg_exposure_ratio', math.nan))} | "
            f"{fmt(getattr(row, 'zg_nightly_ratio', math.nan))} | "
            f"{fmt(getattr(row, 'zg_monthly_ratio', math.nan))} | "
            f"{verdict} |"
        )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    args = parser.parse_args()

    manifest = json.loads((args.run_dir / "census_manifest.json").read_text(encoding="utf-8"))
    census = pd.read_csv(args.run_dir / "census_full_catalog.csv", dtype={"source_id": str})
    qc = pd.read_csv(args.run_dir / "crossmatch_qc.csv", dtype={"source_id": str})
    cache_present = int(as_bool(qc["cache_present"]).sum())
    read_failures = int(qc["read_status"].ne("ok").sum())
    census_any = int(as_bool(census["census_variable"]).sum())
    census_night = int(as_bool(census["census_g_nightly"]).sum())
    census_month = int(as_bool(census["census_g_monthly"]).sum())

    lines = [
        "# Full-catalog rebuild — results",
        "",
        f"Run directory: `{args.run_dir.name}`. This report is generated from machine-readable outputs; it is intentionally updated after the census, Lomb–Scargle, and panelcast stages.",
        "",
        "## Selection provenance",
        "",
        "- The Gentile Fusillo main catalog reproduces the paper's Eq. 3 selection exactly: **22,264** sources.",
        "- The reconstructed variability cut contains **1,423** candidates and all **20/20** known roster members.",
        "- Gaia σ(G) uses the inferred per-CCD convention `phot_g_n_obs / 9`. The printed Eq. 4 constants require multiplier **1.1896** to reproduce 1,423, versus **1.25** quoted by the paper.",
        "- Four plausible calibrated recipes agree on **1,359/1,423 (95.5%)** sources; `in_core` and `n_variants` retain that boundary uncertainty per star.",
        "",
        "## Census stage",
        "",
        f"- Cached ZTF responses: **{cache_present:,}/1,423**; cache/read failures: **{read_failures:,}**.",
        f"- Crossmatched under the nearest-coordinate-cluster and ≥20 clean exposures in each of g and r rule: **{manifest['crossmatched_count']:,}/1,423**. This is 64 above the paper's 864 cleaned light curves; the simplified prespecified rule has no magnitude-consistency cut.",
        f"- Known roster retained: **{manifest['known_roster_crossmatched']}/20**. Gaia DR3 `6555925496084361344` is in Stage B but IRSA returned zero g/r rows within both 10 and 30 arcsec; this is an unavailable southern control, not a silent dropout.",
        f"- Any of six exposure/night/month × g/r ratios ≥2.5: **{census_any:,}** stars.",
        f"- Nightly g ratio ≥2.5: **{census_night:,}**; monthly g ratio ≥2.5: **{census_month:,}**.",
        "- The census is a variance screen, not a periodicity classifier; its count is not expected to equal the paper's 141 periodic stars.",
        "",
        "![Full-catalog census](figures/census_full_catalog.png)",
        "",
        "### Known roster",
        "",
        *roster_table(census, qc),
        "",
        "## Ladder against Jestin et al.",
        "",
        "| stage | paper | this rebuild |",
        "|---|---:|---:|",
        f"| Eq. 3 selection | {PAPER_LADDER['Eq. 3 selection']:,} | 22,264 |",
        f"| variability candidates | {PAPER_LADDER['variability candidates']:,} | 1,423 |",
        f"| fetched responses | — | {cache_present:,} |",
        f"| ZTF crossmatched / clean | {PAPER_LADDER['ZTF crossmatches']:,} → {PAPER_LADDER['clean light curves']:,} | {manifest['crossmatched_count']:,} |",
        f"| census-variable | not comparable | {census_any:,} |",
    ]

    ls_path = args.run_dir / "ls_full_catalog.csv"
    if ls_path.exists():
        ls = pd.read_csv(ls_path, dtype={"source_id": str})
        confirmed = ls[ls["blind_status"].eq("confirmed")]
        candidates = ls[ls["blind_status"].eq("candidate")]
        completed = int(as_bool(ls["ls_complete"]).sum()) if "ls_complete" in ls else len(ls)
        lines[-1] += ""
        lines.extend(
            [
                f"| L-S periodic | {PAPER_LADDER['periodic']:,} (+ {PAPER_LADDER['undetermined']} undetermined) | {len(confirmed):,} confirmed; {len(candidates):,} one-band candidates |",
                "",
                "## Full-catalog Lomb–Scargle",
                "",
                f"Completed both blind passes for **{completed:,}/{len(ls):,}** crossmatched stars: **{len(confirmed):,} confirmed**, **{len(candidates):,} one-band candidates**.",
            ]
        )
        sanity_path = args.run_dir / "ls/sanity_gates.json"
        if sanity_path.exists():
            sanity = json.loads(sanity_path.read_text(encoding="utf-8"))
            passed = sum(check["passed"] is True for check in sanity["checks"].values())
            unavailable = sum(not check["available"] for check in sanity["checks"].values())
            lines.append(
                f"Known-period sanity gates: **{passed}/{sanity['available_checks']} available controls passed** before the batch; {unavailable} southern RR Lyrae control had zero IRSA rows within both 10 and 30 arcsec and is explicitly unavailable rather than counted as a failure."
            )
        if "high_pass_available" in ls:
            unavailable_high = int((~as_bool(ls["high_pass_available"])).sum())
            lines.append(
                f"The high-frequency residual pass is structurally unavailable for **{unavailable_high}** sparse stars with one exposure per night in both bands; their low-frequency result remains valid, and the missing high-pass A95 is labeled rather than reported as a zero limit."
            )
        if "bootstrap_fap" in ls:
            bootstrapped = int(ls["bootstrap_fap"].notna().sum())
            floor = 1.0 / 101.0
            lines.append(
                f"The strongest **{bootstrapped}** surviving candidates received 100-resample pass-wide bootstrap tests; values at {floor:.5f} are a finite resolution floor, not zero."
            )
            bootstrap_path = args.run_dir / "bootstrap_top_candidates.csv"
            if bootstrap_path.exists():
                bootstrap = pd.read_csv(bootstrap_path, dtype={"source_id": str})
                pass_counts = bootstrap["pass"].value_counts().to_dict()
                lines.append(
                    f"All selected bootstrap targets came from the **{next(iter(pass_counts), 'unknown')}** pass because many analytic FAPs underflowed to zero; this validates the strongest low-frequency tail, not the high-frequency or marginal-candidate populations."
                )
        merged = ls.merge(
            census[["source_id", "census_variable"]],
            on="source_id",
            how="left",
        )
        merged["census_variable"] = as_bool(merged["census_variable"])
        ls_only = merged[
            merged["blind_status"].eq("confirmed") & ~merged["census_variable"]
        ]
        census_only = merged[
            ~merged["blind_status"].eq("confirmed") & merged["census_variable"]
        ]
        lines.extend(
            [
                f"The blind-spot symmetry is substantial: **{len(ls_only):,}** L-S-confirmed stars are census-quiet, while **{len(census_only):,}** census-variable stars lack an L-S confirmation.",
                "",
                "| direction | Gaia DR3 | period / note |",
                "|---|---|---|",
            ]
        )
        for row in ls_only.sort_values("best_band_fap").head(40).itertuples(index=False):
            lines.append(f"| L-S only | {row.source_id} | {fmt(row.best_period_days, 6)} d |")
        for row in census_only.sort_values("source_id").head(40).itertuples(index=False):
            lines.append(f"| census only | {row.source_id} | no confirmed blind period |")
        if len(ls_only) > 40 or len(census_only) > 40:
            lines.append("| … | full lists | `ls_census_disagreement.csv` |")
        lines.extend(
            [
                "",
                "![Period versus amplitude](figures/ls_period_amplitude.png)",
            ]
        )
    else:
        lines.extend(
            [
                "| L-S periodic | 141 (+ 7 undetermined) | pending |",
                "",
                "## Full-catalog Lomb–Scargle",
                "",
                "Pending. The census deliverable above is complete and does not depend on this stage.",
            ]
        )

    fit_summary_path = args.run_dir / "panelcast_full_fit/fit_summary.json"
    lines.extend(["", "## Full-catalog panelcast fit", ""])
    magnitude_audit_path = args.run_dir / "panelcast_crossmatch_magnitude_audit.csv"
    if magnitude_audit_path.exists():
        magnitude_audit = pd.read_csv(magnitude_audit_path, dtype={"source_id": str})
        mismatch_count = int(as_bool(magnitude_audit["magnitude_mismatch_flag"]).sum())
        lines.append(
            f"The nearest-coordinate crossmatch leaves **{mismatch_count}/928** sources whose median ZTF g differs from Gaia G by more than 1 mag. They are retained because the prespecified simplified hygiene rule contains no magnitude cut; `panelcast_crossmatch_magnitude_audit.csv` makes the sensitivity concern explicit."
        )
        lines.append("")
    if fit_summary_path.exists():
        summary = json.loads(fit_summary_path.read_text(encoding="utf-8"))
        lines.append(f"Status: **{summary['status']}** after {summary['attempts']} attempt(s).")
        lines.append("")
        lines.append(summary.get("narrative", "Diagnostics are recorded in `panelcast_full_fit/`."))
        lines.extend(
            [
                "",
                "| diagnostic | full catalog | acceptance |",
                "|---|---:|---:|",
                f"| max R-hat | {fmt(summary.get('max_rhat'), 4)} | ≤1.01 |",
                f"| min bulk ESS | {fmt(summary.get('min_bulk_ess'), 0)} | ≥400 |",
                f"| divergences | {fmt(summary.get('divergences'), 0)} | 0 |",
                f"| primary MAE | {fmt(summary.get('mae'), 5)} | — |",
                f"| primary RMSE | {fmt(summary.get('rmse'), 5)} | — |",
                f"| primary R² | {fmt(summary.get('r2'), 4)} | — |",
                f"| primary 80% coverage | {fmt(summary.get('coverage_80'), 3)} | 0.80 |",
                f"| primary 95% coverage | {fmt(summary.get('coverage_95'), 3)} | 0.95 |",
                f"| entity-disjoint MAE | {fmt(summary.get('secondary_mae'), 5)} | — |",
                f"| entity-disjoint RMSE | {fmt(summary.get('secondary_rmse'), 5)} | — |",
                f"| entity-disjoint R² | {fmt(summary.get('secondary_r2'), 4)} | — |",
                f"| entity-disjoint 80% coverage | {fmt(summary.get('secondary_coverage_80'), 3)} | 0.80 |",
                f"| entity-disjoint 95% coverage | {fmt(summary.get('secondary_coverage_95'), 3)} | 0.95 |",
                f"| prior-predictive fraction in bounds | {fmt(summary.get('prior_predictive_fraction_in_bounds'), 3)} | informational |",
            ]
        )
        scalar_path = args.run_dir / "panelcast_full_fit/posterior_scalars_vs_pilot.csv"
        if scalar_path.exists():
            scalars = pd.read_csv(scalar_path)
            lines.extend(
                [
                    "",
                    "Raw offset-logit scalars are not directly comparable because the full and pilot descriptors use different target bounds. The magnitude-equivalent columns invert the location or apply a local delta-method scale.",
                    "",
                    "| posterior scalar | latent full | latent pilot | mag-equivalent full | mag-equivalent pilot |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for row in scalars.itertuples(index=False):
                lines.append(
                    f"| {row.parameter_key} | {fmt(getattr(row, 'Estimate_full'), 5)} | "
                    f"{fmt(getattr(row, 'Estimate_pilot'), 5)} | "
                    f"{fmt(row.magnitude_equivalent_full, 5)} | "
                    f"{fmt(row.magnitude_equivalent_pilot, 5)} |"
                )
    else:
        lines.append("Pending by priority order; the census and Lomb–Scargle outputs are written first.")

    hardening_path = args.run_dir / "hardening/hardening_acceptance.json"
    if hardening_path.exists():
        hardening = json.loads(hardening_path.read_text(encoding="utf-8"))
        bootstrap_summary = pd.read_csv(
            args.run_dir / "hardening/stratified_bootstrap/summary.csv"
        )
        baselines = pd.read_csv(args.run_dir / "hardening/forecast_baselines.csv")
        median_baseline = baselines[
            baselines["model"].eq("entity_train_median")
        ].iloc[0]
        gaia_ols = baselines[
            baselines["model"].eq("gaia_g_bp_rp_train_ols")
            & baselines["subset"].eq("all")
        ].iloc[0]
        lines.extend(
            [
                "",
                "## Post-hoc hardening audit",
                "",
                f"Hardening acceptance: **{'passed' if hardening['all_passed'] else 'pending'}**. The prespecified 342-confirmation result is unchanged; **{hardening['magnitude_clean_confirmed']}** survive the >1 mag crossmatch sensitivity cut and **{hardening['conservative_confirmed_floor']}** survive that cut together with the wider daily-systematics screen.",
                "",
                "The correlation-aware bootstrap validates all five strong and four of five marginal low-frequency confirmations. High-frequency survival is weaker: three of five strong and one of five marginal confirmations pass at FAP ≤0.05, so the 65 high-pass confirmations remain exploratory.",
                "",
                f"The original panelcast fit does not beat the exact-split entity-median baseline (MAE **{median_baseline.mae:.5f}**). A converged Gaia-feature panelcast sensitivity also failed to improve cold start and was rejected; the train-only Gaia G + BP−RP benchmark reaches MAE **{gaia_ols.mae:.5f}**, R² **{gaia_ols.r2:.3f}**.",
                "",
                f"Eight bootstrap strata are recorded in `hardening/stratified_bootstrap/summary.csv` ({int(bootstrap_summary['sources'].sum())} sources). Full interpretation is in `hardening/HARDENING_RESULTS.md`.",
            ]
        )

    lines.extend(
        [
            "",
            "## Traceability and guardrails",
            "",
            "- `census_full_catalog.csv`: one row per crossmatched star, all six ratios and census verdict.",
            "- `crossmatch_qc.csv`: every Stage B candidate, including missing/failed responses and row-rejection counts.",
            "- `ls_full_catalog.csv`: one row per crossmatched star when the L-S stage is complete.",
            "- `panelcast_crossmatch_magnitude_audit.csv`: Gaia-versus-ZTF median-magnitude audit for every retained crossmatch.",
            "- The converged pilot directory `outputs/2026-07-18_151420_993941_17ac` and pilot L-S directory `outputs/ls/2026-08-01_full` were not modified or rerun.",
            "- Nothing has been pushed; review is required before any push.",
        ]
    )
    (args.run_dir / "CATALOG_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.run_dir / 'CATALOG_RESULTS.md'}")


if __name__ == "__main__":
    main()
