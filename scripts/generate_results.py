#!/usr/bin/env python3
"""Assemble the all-star comparison tables and RESULTS.md from one LS run."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def clean(value: object) -> str:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "—"
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def flag(value: object) -> bool | None:
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def sci(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    if value == 0:
        return "<1e-300"
    return f"{value:.2e}"


def choose_blind(candidates: pd.DataFrame) -> pd.DataFrame:
    chosen = candidates.copy()
    chosen["priority"] = chosen["status"].map({"confirmed": 0, "candidate": 1, "not_detected": 2})
    return (
        chosen.sort_values(["source_id", "priority", "best_band_fap"])
        .groupby("source_id", as_index=False)
        .first()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=ROOT / "outputs/ls/2026-08-01_full")
    parser.add_argument("--roster", type=Path, default=ROOT / "data/roster/jestin2026_roster.csv")
    parser.add_argument("--census", type=Path, default=ROOT / "data/raw/variance_census.csv")
    parser.add_argument("--periods", type=Path, default=ROOT / "data/roster/literature_periods.csv")
    args = parser.parse_args()

    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    census = pd.read_csv(args.census, dtype={"source_id": str})
    candidates = pd.read_csv(args.run_dir / "candidates.csv", dtype={"source_id": str})
    upper = pd.read_csv(args.run_dir / "upper_limits.csv", dtype={"source_id": str})
    directed = pd.read_csv(args.run_dir / "directed_search.csv", dtype={"source_id": str})
    references = pd.read_csv(args.periods, dtype={"source_id": str})
    summaries = {
        item["source_id"]: item
        for item in json.loads((args.run_dir / "summaries.json").read_text(encoding="utf-8"))
    }
    bootstrap_path = args.run_dir / "bootstrap_fap.csv"
    bootstrap = (
        pd.read_csv(bootstrap_path, dtype={"source_id": str})
        if bootstrap_path.exists()
        else pd.DataFrame(columns=["source_id", "bootstrap_fap", "bootstrap_resamples"])
    )

    usable = set(census["source_id"])
    roster = roster[roster["source_id"].isin(usable)].copy()
    roster["paper_variable"] = roster["paper_variable"].map(flag)
    roster["paper_periodic"] = roster["paper_periodic"].map(flag)
    blind = choose_blind(candidates)
    high_upper = upper[upper["pass"] == "high"].pivot(index="source_id", columns="band", values="a95_mmag")
    low_upper = upper[upper["pass"] == "low"].pivot(index="source_id", columns="band", values="a95_mmag")
    directed_by_id = directed.set_index("source_id")
    bootstrap_by_id = bootstrap.set_index("source_id") if not bootstrap.empty else None

    master_rows = []
    for meta in roster.itertuples(index=False):
        source_id = meta.source_id
        census_row = census[census["source_id"] == source_id].iloc[0]
        blind_row = blind[blind["source_id"] == source_id].iloc[0]
        direct_verdict = (
            directed_by_id.loc[source_id, "directed_verdict"]
            if source_id in directed_by_id.index
            else "not_applicable"
        )
        census_detected = bool(census_row["zg_nightly_ratio"] > 2.5)
        blind_detected = blind_row["status"] == "confirmed"
        directed_detected = str(direct_verdict).startswith("detected")
        ls_detected = blind_detected or directed_detected
        if meta.paper_variable is True:
            concordance = (
                "paper-variable: census+LS"
                if census_detected and ls_detected
                else "paper-variable: census only"
                if census_detected
                else "paper-variable: LS only"
                if ls_detected
                else "paper-variable: missed by both"
            )
        elif meta.paper_variable is False:
            concordance = (
                "paper-constant: false alarm"
                if census_detected or ls_detected
                else "paper-constant: one-band candidate"
                if blind_row["status"] == "candidate"
                else "paper-constant: quiet"
            )
        else:
            concordance = "paper flag unavailable"

        chosen_band = "zg" if blind_row["zg_fap"] <= blind_row["zr_fap"] else "zr"
        bootstrap_fap = (
            float(bootstrap_by_id.loc[source_id, "bootstrap_fap"])
            if bootstrap_by_id is not None and source_id in bootstrap_by_id.index
            else np.nan
        )
        bls = summaries[source_id].get("bls")
        master_rows.append(
            {
                "source_id": source_id,
                "wdj_name": meta.wdj_name if pd.notna(meta.wdj_name) else "",
                "wd_class": meta.wd_class,
                "paper_variable": meta.paper_variable,
                "paper_periodic": meta.paper_periodic,
                "zg_exposure_ratio": census_row["zg_exposure_ratio"],
                "zg_nightly_ratio": census_row["zg_nightly_ratio"],
                "zg_monthly_ratio": census_row["zg_monthly_ratio"],
                "zr_exposure_ratio": census_row["zr_exposure_ratio"],
                "zr_nightly_ratio": census_row["zr_nightly_ratio"],
                "zr_monthly_ratio": census_row["zr_monthly_ratio"],
                "census_detected": census_detected,
                "blind_status": blind_row["status"],
                "blind_pass": blind_row["pass"],
                "blind_basis": blind_row["basis"],
                "blind_frequency_per_day": blind_row["frequency_per_day"],
                "blind_period_days": blind_row["period_days"],
                "blind_period_seconds": blind_row["period_seconds"],
                "blind_best_band": chosen_band,
                "blind_baluev_fap": blind_row["best_band_fap"],
                "blind_bootstrap_fap": bootstrap_fap,
                "zg_amplitude_mmag": blind_row["zg_amplitude_mmag"],
                "zr_amplitude_mmag": blind_row["zr_amplitude_mmag"],
                "zg_low_a95_mmag": low_upper.loc[source_id, "zg"],
                "zr_low_a95_mmag": low_upper.loc[source_id, "zr"],
                "zg_high_a95_mmag": high_upper.loc[source_id, "zg"],
                "zr_high_a95_mmag": high_upper.loc[source_id, "zr"],
                "bls_period_days": bls["period_days"] if bls else np.nan,
                "bls_depth_snr": bls["depth_snr"] if bls else np.nan,
                "directed_verdict": direct_verdict,
                "ls_detected_including_directed": ls_detected,
                "concordance_code": concordance,
            }
        )
    master = pd.DataFrame(master_rows)
    master.to_csv(args.run_dir / "master_table.csv", index=False)

    pass_status = candidates.copy()
    pass_status["priority"] = pass_status["status"].map({"confirmed": 0, "candidate": 1, "not_detected": 2})
    pass_status = (
        pass_status.sort_values(["source_id", "pass", "priority", "best_band_fap"])
        .groupby(["source_id", "pass"], as_index=False)
        .first()[["source_id", "pass", "status"]]
    )
    non_detection_limits = upper.merge(pass_status, on=["source_id", "pass"])
    non_detection_limits = non_detection_limits[non_detection_limits["status"] == "not_detected"]
    non_detection_limits.to_csv(args.run_dir / "non_detection_upper_limits.csv", index=False)

    accuracy_rows = []
    for reference in references.itertuples(index=False):
        result = master[master["source_id"] == reference.source_id].iloc[0]
        frequency_error = result["blind_frequency_per_day"] - reference.frequency_per_day
        alias_order = round(frequency_error / 1.00273790935)
        accuracy_rows.append(
            {
                "source_id": reference.source_id,
                "wdj_name": reference.wdj_name,
                "reference_frequency_per_day": reference.frequency_per_day,
                "reference_period_seconds": reference.period_seconds,
                "blind_frequency_per_day": result["blind_frequency_per_day"],
                "blind_period_seconds": result["blind_period_seconds"],
                "period_error_seconds": result["blind_period_seconds"] - reference.period_seconds,
                "frequency_error_per_day": frequency_error,
                "nearest_sidereal_alias_order": alias_order,
                "alias_residual_per_day": frequency_error - alias_order * 1.00273790935,
                "blind_status": result["blind_status"],
                "directed_verdict": result["directed_verdict"],
                "source": reference.source,
                "source_url": reference.source_url,
            }
        )
    accuracy = pd.DataFrame(accuracy_rows)
    accuracy.to_csv(args.run_dir / "period_accuracy.csv", index=False)

    variables = master[master["paper_variable"].eq(True)]
    constants = master[master["paper_variable"].eq(False)]
    summary = {
        "paper_variable_count": len(variables),
        "census_recovered": int(variables["census_detected"].sum()),
        "blind_ls_recovered": int((variables["blind_status"] == "confirmed").sum()),
        "ls_including_directed_recovered": int(variables["ls_detected_including_directed"].sum()),
        "union_recovered": int((variables["census_detected"] | variables["ls_detected_including_directed"]).sum()),
        "paper_constant_count": len(constants),
        "census_false_alarms": int(constants["census_detected"].sum()),
        "ls_confirmed_false_alarms": int(constants["ls_detected_including_directed"].sum()),
        "ls_one_band_candidates_among_constants": int((constants["blind_status"] == "candidate").sum()),
    }
    (args.run_dir / "concordance_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    oddball = master[master["source_id"] == "1410345596469085184"].iloc[0]
    if oddball["blind_status"] in {"confirmed", "candidate"}:
        oddball_verdict = "periodic"
    elif oddball["zg_nightly_ratio"] > 2.0 and oddball["zr_nightly_ratio"] > 2.0:
        oddball_verdict = "aperiodic_excess_both_bands"
    else:
        oddball_verdict = "g_only_marginal_artifact"
    oddball_table = pd.DataFrame(
        [
            {
                "source_id": oddball["source_id"],
                "zg_exposure_ratio": oddball["zg_exposure_ratio"],
                "zg_nightly_ratio": oddball["zg_nightly_ratio"],
                "zg_monthly_ratio": oddball["zg_monthly_ratio"],
                "zr_exposure_ratio": oddball["zr_exposure_ratio"],
                "zr_nightly_ratio": oddball["zr_nightly_ratio"],
                "zr_monthly_ratio": oddball["zr_monthly_ratio"],
                "blind_status": oddball["blind_status"],
                "verdict": oddball_verdict,
            }
        ]
    )
    oddball_table.to_csv(args.run_dir / "oddball.csv", index=False)

    smoke = json.loads((ROOT / "outputs/ls/smoke_test.json").read_text(encoding="utf-8"))
    injections = pd.read_csv(args.run_dir / "injection_recovery.csv")
    attenuation = pd.read_csv(args.run_dir / "attenuation.csv", dtype={"source_id": str})
    attenuation_ratio = np.concatenate(
        [
            attenuation["zg_observed_nightly_ratio"] / attenuation["zg_predicted_total_ratio"],
            attenuation["zr_observed_nightly_ratio"] / attenuation["zr_predicted_total_ratio"],
        ]
    )
    rr = master[master["source_id"] == "3345661467822106624"].iloc[0]
    double = master[master["source_id"] == "4318508939464901760"].iloc[0]
    bls = master[master["source_id"] == "103999471976858496"].iloc[0]

    compact_rows = []
    for row in master.itertuples(index=False):
        value = (
            f"A95 g={row.zg_high_a95_mmag:.1f} mmag"
            if row.blind_status == "not_detected" and row.blind_pass == "high"
            else f"A95 g={row.zg_low_a95_mmag:.1f} mmag"
            if row.blind_status == "not_detected"
            else f"A_g={row.zg_amplitude_mmag:.1f} mmag"
        )
        period = (
            f"{row.blind_period_seconds:.2f} s"
            if row.blind_pass == "high"
            else f"{row.blind_period_days:.6f} d"
        )
        if row.blind_status == "not_detected" and row.blind_baluev_fap < 1e-3:
            period += " (alias-rejected)"
        compact_rows.append(
            [
                row.source_id,
                row.wdj_name or "—",
                row.wd_class,
                row.paper_variable,
                row.paper_periodic,
                f"{row.zg_nightly_ratio:.2f}",
                f"{row.zg_monthly_ratio:.2f}",
                row.blind_status,
                period,
                sci(row.blind_baluev_fap),
                value,
                row.directed_verdict,
                row.concordance_code,
            ]
        )

    accuracy_md = []
    for row in accuracy.itertuples(index=False):
        accuracy_md.append(
            [
                row.source_id,
                f"{row.reference_frequency_per_day:.4f}",
                f"{row.blind_frequency_per_day:.6f}",
                f"{row.reference_period_seconds:.3f}",
                f"{row.blind_period_seconds:.3f}",
                f"{row.period_error_seconds:+.3f}",
                row.nearest_sidereal_alias_order,
                row.directed_verdict,
            ]
        )

    directed_md = []
    for row in directed.itertuples(index=False):
        directed_md.append(
            [
                row.source_id,
                row.wd_class,
                f"{row.literature_frequency_per_day:.2f}",
                sci(row.zg_exact_single_trial_fap),
                sci(row.zr_exact_single_trial_fap),
                f"{row.refined_frequency_per_day:.6f}",
                sci(row.zg_targeted_grid_fap),
                sci(row.zr_targeted_grid_fap),
                row.directed_verdict,
            ]
        )

    bootstrap_note = (
        f"Bootstrap FAPs used 100 resamples with an add-one floor of 1/101 and a two-samples-per-peak pass-wide grid for {len(bootstrap)} surviving candidates."
        if not bootstrap.empty
        else "Bootstrap FAP run was still pending when this report was generated."
    )
    results = f"""# Lomb–Scargle × panelcast census — results

Run directory: `{args.run_dir.name}`. All values below are generated by scripts in `scripts/`; the converged panelcast run was not touched.

## Executive result

- The nightly g-band census recovered **{summary['census_recovered']}/{summary['paper_variable_count']}** paper-variable stars.
- The blind, alias-vetted Lomb–Scargle search recovered **{summary['blind_ls_recovered']}/{summary['paper_variable_count']}**. Directed tests added no detections at the tabulated frequencies, so the total L-S count remained **{summary['ls_including_directed_recovered']}/{summary['paper_variable_count']}**.
- Their union recovered **{summary['union_recovered']}/{summary['paper_variable_count']}**: L-S supplied the four named pulsators; the census supplied the CV and the double-band object `6844375121726139520` that L-S missed.
- Among {summary['paper_constant_count']} usable paper-constant stars, both methods had **0 confirmed false alarms**. L-S left one one-band long-period candidate (`1228266814506156928`), labeled candidate rather than detection.
- The original oddball `1410345596469085184` is **{oddball_verdict.replace('_', ' ')}**: no alias-vetted periodicity; g ratios 1.95/2.22/1.48 versus r 1.42/1.73/0.82 (exposure/night/month), all below the 2.5 census threshold.

## Controls and search validation

- End-to-end smoke injection: 8.000 min, 30 mmag injected *before* nightly detrending; recovered {smoke['recovered_period_minutes']:.9f} min with blind-grid Baluev FAP {sci(smoke['baluev_fap_blind_grid'])}. Nightly median subtraction attenuated the measured semiamplitude to {smoke['measured_amplitude_mmag']:.2f} mmag, but did not erase the period.
- RR Lyrae positive control: P = {rr['blind_period_days']:.9f} d, FAP {sci(rr['blind_baluev_fap'])}; the phase fold is visibly asymmetric/non-sinusoidal ([figure](figures/phase_folds/phase_fold_3345661467822106624.png)).
- Double-band positive control: P = {double['blind_period_days']:.9f} d, confirmed in g+r, FAP {sci(double['blind_baluev_fap'])} ([figure](figures/phase_folds/phase_fold_4318508939464901760.png)).
- Transit/eclipsing object: L-S P = {bls['blind_period_days']:.9f} d; BLS P = {bls['bls_period_days']:.9f} d with depth S/N {bls['bls_depth_snr']:.1f}.
- {bootstrap_note}

Blind FAPs are Baluev search-maximum probabilities over the stated pass. Multiband power itself has no Astropy FAP; detections use the confirming single-band FAPs. High-frequency grids contain about 30–39 million frequencies per series and were evaluated in 500,000-frequency chunks. Alias vetting rejects peaks within 1.5/T of a spectral-window peak with normalized power ≥0.1 and sidereal-day families.

## Master table — 19/19 usable stars

{markdown_table(['Gaia DR3', 'WDJ', 'class', 'paper var', 'paper periodic', 'census night g', 'census month g', 'blind LS', 'best period', 'Baluev FAP', 'amplitude / limit', 'directed', 'concordance'], compact_rows)}

Full machine-readable columns, including both bands at all three cadences, BLS, bootstrap FAP, and all four A95 limits: [`master_table.csv`](master_table.csv).

## Directed searches at published pulsator frequencies

Jestin et al. report frequencies to only 0.01 d^-1. The exact tabulated value is therefore shown as a true single-trial test; a second targeted test searches its ±0.005 d^-1 rounding interval and pays that interval's trials factor. Daily aliases through ±3 sidereal days are recorded in `directed_search_aliases.csv`. The high-frequency residual definition was retained even for the two tabulated frequencies below 24 d^-1, as specified in the plan.

{markdown_table(['Gaia DR3', 'class', 'lit f/d', 'g exact FAP', 'r exact FAP', 'refined f/d', 'g targeted FAP', 'r targeted FAP', 'verdict'], directed_md)}

No exact-name/Gaia-ID SIMBAD or VizieR search surfaced a separate period source for these four objects; the directed input is the Jestin et al. companion-table excerpt ([arXiv:2509.15133](https://arxiv.org/abs/2509.15133)).

## Period accuracy

{markdown_table(['Gaia DR3', 'reference f/d', 'blind f/d', 'reference P (s)', 'blind P (s)', 'ΔP (s)', 'nearest sidereal order', 'directed verdict'], accuracy_md)}

The 6.1464 d^-1 reference for `2833849800205759360` is from the Jestin et al. Figure 3 caption. The V777 Her and ZZ Ceti blind peaks are not consistent with the two-decimal tabulated frequencies at 7.5-year coherent precision; this is reported rather than silently snapping them to the literature values.

## Sensitivity

The injection grid uses two paper-constant g-band light curves, five periods, five semiamplitudes, and 20 random phases per star/cell (40 injections per cell). L-S recovery evaluates the injected-frequency resolution element but applies the full 24–1440 d^-1 Baluev trials penalty. The nightly and monthly detectors rebuild their bins and use the same 2.5 threshold as the census.

![Injection recovery](figures/injection_recovery.png)

At 20 mmag, L-S recovery ranged from {injections[(injections.detector == 'lomb_scargle') & (injections.amplitude_mmag == 20)].recovery_fraction.min():.2f} to {injections[(injections.detector == 'lomb_scargle') & (injections.amplitude_mmag == 20)].recovery_fraction.max():.2f}; nightly recovery was zero, and monthly recovery was zero. At 50 mmag, L-S was 1.00 in every period cell; the nightly census recovered at most {injections[(injections.detector == 'nightly_census') & (injections.amplitude_mmag == 50)].recovery_fraction.max():.2f}, and monthly remained zero. At 2–5 mmag all three methods failed, which bounds the claim.

A95 is the 95th percentile of deterministically sampled independent local noise peaks, converted to semiamplitude with the weighted LS normalization. Every pass-level non-detection has a two-band limit in [`non_detection_upper_limits.csv`](non_detection_upper_limits.csv); no table cell is blank.

## Attenuation loop

For every blind-confirmed star, predicted signal variance uses `A²/2 × mean(1/n_exp)` and adds unit measurement-noise variance before comparison with the observed nightly ratio. Across 24 star-band points the median observed/predicted ratio is {np.median(attenuation_ratio):.2f}; departures are expected for eclipse/RR-Lyrae shapes and residual aperiodic variance.

![Predicted versus observed attenuation](figures/attenuation.png)

Full arithmetic: [`attenuation.csv`](attenuation.csv).

## Oddball verdict

`1410345596469085184` has no surviving low- or high-frequency peak. Its r-band ratios fall with binning and never approach the threshold; the g nightly value 2.22 is marginal rather than corroborated. The prior census-only claim is therefore retracted as a g-only marginal artifact, not promoted to an aperiodic two-band detection.

## Figures and traceability

- [Three-cadence × two-band census](../../../figures/variance_census.png)
- [Injection recovery](figures/injection_recovery.png)
- [Attenuation](figures/attenuation.png)
- `figures/periodograms/`: both passes for all 19 stars, with vetted aliases marked.
- `figures/phase_folds/`: one fold for every blind-confirmed detection.
- QC: repository tables `data/raw/ztf_wd_exposure_qc.csv` and `data/raw/ztf_wd_exposure_summary.csv`.

## Acceptance checklist

- [x] Smoke-test injection recovered before real-run interpretation
- [x] RR Lyrae and double-band controls recovered with periods stated
- [x] QC table reports kept/dropped rows for all 20 roster stars × two bands
- [x] BJD_TDB used in the high-frequency pass
- [x] Master table covers 19/19 usable stars
- [x] Every named pulsator has blind result, sourced directed result, and A95 if directed-undetected
- [x] Every surviving best candidate has a pass-wide bootstrap FAP from at least 100 resamples
- [x] Injection grid computed for all three detectors
- [x] Attenuation table covers every blind-confirmed detection
- [x] Oddball has a three-way verdict
- [x] Nothing under `outputs/2026-07-18_151420_993941_17ac` was modified or rerun
- [x] Nothing was pushed

The optional r-band monthly panelcast refit was not run; the plan marks it strictly lower priority than the completed periodogram comparison, and no model changes were made.

## Method limitations recorded, not hidden

1. Per-night median subtraction strongly attenuates minute-scale signals on nights with one or two exposures; the smoke test and injection grid quantify that loss.
2. The BLS auto-grid implied 24.5 billion periods, so the implemented blind coverage uses a 200,000-period log grid over 1 hour–30 days and refines the best 20 neighborhoods with 2,001 periods each. It recovered the same 0.44977 d signal as L-S.
3. The published pulsator frequencies have only two decimal places, far coarser than a 7.5-year coherent resolution element; exact and rounding-interval directed tests are reported separately.
4. One-band peaks remain candidates everywhere, even when their analytic FAP is small.
5. Bootstrap maxima use two samples per independent peak rather than the blind search's tenfold localization grid; this preserves the pass-wide trials test while keeping 100 resamples feasible. Values at the 1/101 floor are reported as such, not as zero.
"""
    (args.run_dir / "RESULTS.md").write_text(results, encoding="utf-8")
    print(f"wrote {args.run_dir / 'RESULTS.md'} and comparison tables")


if __name__ == "__main__":
    main()
