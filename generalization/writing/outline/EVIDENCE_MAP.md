# Evidence map — claim → artifact → pre-registration status

Produced 2026-09-01, before any full-run number exists. Every row names the
exact file, the row selector, and the columns that fill the placeholder. Paths
are relative to `generalization/results/<date>_d3/metrics/` or
`generalization/results/<date>_d2/metrics/` unless stated. Column names were
verified against the gen2 pilot outputs (same code path) and
`metrics_generalization.py`; re-verify against the real headers at G5.

Status vocabulary (binding; see OUTLINE.md §0.2): PRIMARY-P1…P5 · SECONDARY ·
DESCRIPTIVE-PRESPEC · DESCRIPTIVE-POST-LAUNCH · DIAGNOSTIC · PROVENANCE · ANCHOR ·
PILOT (never a result).

Use columns: A = abstract slot, F = poster figure, C = paper claim (OUTLINE.md).

## 1. D3 — externally labeled, magnitude-restricted validation on real ZTF photometry

| ID | Claim (template) | Artifact → row selector → columns | Estimator / interval | Status | Used in |
|---|---|---|---|---|---|
| D3-1 | Eligible-roster confirmed detection completeness ⟨x/610; p; lo–hi⟩ | completeness_by_class_pass_rule.csv → pass=best, rule=confirmed, scope=detection_eligible_roster → n (assert 610), p, lo, hi | unweighted Wilson 95 % | PRIMARY-P1 | S6, F2, C9, T1 row 1 |
| D3-2 | Usable-light-curve confirmed detection completeness ⟨x_u/n_u⟩ | same → scope=detection_usable_lightcurve | Wilson | SECONDARY | S6, F2, C9, T1 row 2 |
| D3-3 | Frequency-recovery completeness ⟨x/n_S⟩ among Mo-joined, freq-scorable, S_best=1 positives | same → scope=freq_recovery_scorable, rule=confirmed, pass=best → n (= n_S ≤ 456), p, lo, hi | Wilson; beside chance rate | PRIMARY-P2 | S7, F1(b), C10, T1 row 3 |
| D3-4 | Accidental direct-match rate ⟨p_acc⟩ | chance_match.json (D3) → mean / p95 over 100 frozen-seed (20260829) permutations of truth lists across stars | permutation calibration | DESCRIPTIVE-PRESPEC (calibration of P2) | S7, C10, T1 row 3 |
| D3-5 | Correct-frequency fraction among detected positives ⟨x/n_det⟩ | same file → scope=correct_frequency_fraction_detected, rule=confirmed, pass=best | Wilson | DESCRIPTIVE-PRESPEC | T1 row 4 |
| D3-6 | Missed-vs-wrong-frequency decomposition on matching denominators | per_star.csv → class_label=dsct_flag1 & freq_scorable & S_p → best_status, best_candidate_matches_dominant (direct/harmonic/window_alias/ambiguous/unmatched) | counts | DESCRIPTIVE-PRESPEC | paper §3 text if room |
| D3-7 | Detection completeness by historical Kepler amplitude bin incl. amp_unknown | surfaces/detection_amplitude.csv → amp_bin ∈ {−1 (unknown), 0…7}, n, k; edges {0.5,1,2,5,10,20,50} mmag, top bin [50,∞) | Wilson where n ≥ 5, counts otherwise; no smoothing | DESCRIPTIVE-PRESPEC | S8, F1(a), C11 |
| D3-8 | Detection / recovery by (period, amplitude) | surfaces/detection_period_amplitude.csv, surfaces/freq_recovery_period_amplitude.csv → period_bin, amp_bin, n, k; period edges {100 s…100 d} | same | DESCRIPTIVE-PRESPEC | ApJL Fig 1 |
| D3-9 | Detection / recovery by (median exposures per night, amplitude) | surfaces/detection_exposure_amplitude.csv, surfaces/freq_recovery_exposure_amplitude.csv → exp_per_night_bin (edges 1,1.5,2,3,5), amp_bin, n, k | same; expect near-degenerate occupancy at 1–2 (75 % of zg nights are single-exposure) — report as observed, no gradient claim | DESCRIPTIVE-PRESPEC | appendix only |
| D3-10 | Negative-class confirmed trigger rate ⟨k/2314; p; lo–hi⟩ | trigger_rates.csv → quantity=negative_class_trigger_rate, rule=confirmed → n, ess, p, lo, hi (weights constant within class → plain Wilson) | plain Wilson (no FPC) | PRIMARY-P3 | S9, F3(a), C12, T1 row 5 |
| D3-11 | Negative-class trigger rate under the other three rules | same → rule ∈ {confirmed_or_candidate, census, either} | Wilson | DESCRIPTIVE-PRESPEC | F3(a) |
| D3-12 | Frame-specific label PPV ⟨p; lo–hi⟩, dSct=2 excluded | ppv.csv → estimand=frame_specific_label_ppv, p, lo, hi, interval=survey_bootstrap_fpc_rescaled, n_triggered, dsct2_triggered_reported_separately | FPC-rescaled survey bootstrap (B=2000) | DESCRIPTIVE-PRESPEC | T1 row 6 |
| D3-13 | Census-only / L-S-only / union on positives with both methods | contingency_complementarity.json (D3) → table{census_and_ls, census_only, ls_only, neither}, incremental_census_only, incremental_ls_only, union_completeness (p, lo, hi), mcnemar | Wilson; exact McNemar secondary | DESCRIPTIVE-PRESPEC; McNemar SECONDARY | S10, F4, C16, T1 row 7 |
| D3-14 | Attrition 3,000 → fetched → crossmatched → QC → both passes, by class / amplitude stratum / join status / magnitude / period / Teff / crowding | attrition.csv (metrics); data/d3/crossmatch_freeze/attrition_by_class.csv (roster 610/76/2314; crossmatched 585/72/2244; crowding_clean 44/3/228) | counts | DESCRIPTIVE-PRESPEC (design data) | poster §3 tally; C5 |
| D3-15 | Near-saturation (g ≤ 14 flagged) vs safe (g > 14) and crowding-clean subset rates | sensitivity.csv → variant/subset ∈ {near_saturation, safe_magnitude, crowding_clean} (D3 rows) → n, k, p, lo, hi | Wilson, pointwise | DESCRIPTIVE-PRESPEC | ApJL §5; poster if space |
| D3-16 | Joined-vs-unjoined covariate comparison (Mo MNAR statement) | attrition.csv strata + data/d3/roster_report.json → positives_amplitude_mmag (456/154) | descriptive | DESCRIPTIVE-PRESPEC (mandatory table) | C17 |
| D3-17 | Frequencies of confirmed negatives (alias-veto audit) | fp_frequency_distribution.csv → sid, class_label=dsct_flag0, best_status=confirmed, best_pass, best_frequency_per_day, baseline_days | histogram; descriptive below 10 events | DESCRIPTIVE-PRESPEC | F3(b) |
| D3-18 | Within / outside solar-diurnal band partition of the P3 numerator | results/<date>_d3/descriptive_postlaunch/d3_trigger_decomposition.csv → component ∈ {within_solar_diurnal_band, outside_solar_diurnal_band}, n_negative (2314), n_confirmed_total, n_component, rate_of_all_negatives, share_of_confirmed, analysis_status=postlaunch_pilot_informed_descriptive, prespecified=false, interval=none; README.md carries the disclosure sentence | arithmetic partition; NO interval | DESCRIPTIVE-POST-LAUNCH | F3(b) shading, C18 |
| D3-19 | Sub-hour stratum detections (290 stars) with the Kepler-aperture blend caveat; W4 adjudication of triggered negatives | per_star.csv → subhour=True; adjudication file (to be produced in W4 as data, not an estimand) | counts | DESCRIPTIVE-PRESPEC | ApJL §5 |
| D3-20 | High-pass frequency recovery is a near-empty cell (~10/456 dominant frequencies ≥ 24 d⁻¹) | completeness_by_class_pass_rule.csv → pass=high, scope=freq_recovery_scorable | counts only | DESCRIPTIVE-PRESPEC | paper §4 one clause |

## 2. D2 — conditional injection-recovery efficiency of the search stage

| ID | Claim (template) | Artifact → row selector → columns | Estimator / interval | Status | Used in |
|---|---|---|---|---|---|
| D2-1 | Nominal arm-B dominant-mode recovery, eligible ⟨p; lo–hi⟩ | d2_cluster_completeness.csv → arm=B, scenario=nominal, endpoint=recovery, denominator=eligible → n_targets (103), n_strata_scheduled (3), p, lo, hi, interval=cluster_bootstrap, prespecified_primary=True | target-cluster bootstrap B=2000 seed 20260830 | PRIMARY-P4 | S11, F5 side panel, C13, T1 row 8 |
| D2-2 | Same, usable | same → denominator=usable → n_targets_zero_usable_strata | same | PRIMARY-P4 (usable variant) | S11, T1 row 9 |
| D2-3 | Recovery by W_g stratum K0/K1/K2 | surfaces/recovery_wg_amplitude.csv → wg_bin, amp_bin, n_windows, k_windows, n_targets (marginalize over amp_bin at target level); OR per_star.csv → arm=B, scenario=nominal, template_k ∈ {0,1,2}, wg_contrasts → recompute target-equal mean | cluster interval where ≥ 5 targets | DESCRIPTIVE-PRESPEC | S11, F5, T1 row 10 |
| D2-4 | Recovery surface on (W_g, published amplitude) | surfaces/recovery_wg_amplitude.csv (edges W_g {15,41,84,217}; A {0.5,2,5,10,30}) | target-equal cells | DESCRIPTIVE-PRESPEC | F5 |
| D2-5 | Recovery by (period, amplitude) and by amplitude alone | surfaces/recovery_period_amplitude.csv, surfaces/recovery_amplitude.csv | same | DESCRIPTIVE-PRESPEC | ApJL Fig 3 |
| D2-6 | Post-injection rule-1 trigger rate ⟨p; lo–hi⟩ | d2_cluster_completeness.csv → arm=B, scenario=nominal, endpoint=trigger | cluster bootstrap | SECONDARY | T1 row 12; F5 caption |
| D2-7 | Trigger surfaces | surfaces/trigger_wg_amplitude.csv, trigger_period_amplitude.csv, trigger_amplitude.csv | target-equal | DESCRIPTIVE-PRESPEC | appendix |
| D2-8 | Bandpass-grid sensitivity range ⟨p_min–p_max⟩, endpoint scenarios named | d2_scenario_contrasts.csv → arm=B, scenario ∈ {ladder_g1r1 … ladder_g3r3} (8 non-nominal), endpoint=recovery, denominator=eligible → p_scenario, p_nominal_k1, diff, diff_lo, diff_hi, discordance_u95, interval | common-subset, common-draw paired difference; CP discordance bound when degenerate | DESCRIPTIVE-PRESPEC | S12, F6, C13, T1 row 11 |
| D2-9 | Phase-draw sensitivity | same → scenario ∈ {phase_1, phase_2} | same | DESCRIPTIVE-PRESPEC | F6 |
| D2-10 | Amplitude-stationarity ±30 % (local sensitivity) | same → scenario ∈ {ampscale_0.7, ampscale_1.3} | same | DESCRIPTIVE-PRESPEC | F6 |
| D2-11 | Dominant-mode dropout (76 targets) | same → scenario=dropout (n_targets_matched=76) | same | DESCRIPTIVE-PRESPEC | F6 |
| D2-12 | Mixed-cadence pure-120-s endpoint (33 targets) | same → scenario=cadence_alt (n_targets_matched=33) | same; "conservative endpoint, not the stitched effective cadence" | DESCRIPTIVE-PRESPEC (Amendment 3) | F6 |
| D2-13 | SAP-equivalent re-dilution (20 SPOC-verified targets) | same → scenario=redilution | same | DIAGNOSTIC (stretch arm) | ApJL appendix |
| D2-14 | Per-scenario descriptive counts | sensitivity.csv → variant, subset ∈ {arm_b_median_window_common, nominal_on_<scenario>_targets_common}, n, k, p (no intervals) | counts | DESCRIPTIVE-PRESPEC | appendix |
| D2-15 | FPR_Gaussian ⟨x/1000; U95⟩ and acceptance | trigger_rates.csv → quantity=fpr_gaussian, rule=confirmed → n_scheduled, n_completed (assert 1000), k, p, cp_one_sided_95_upper, acceptance_u95_leq_0.005, n_completed_is_1000, prespecified_primary, confirmatory_decision | exact one-sided CP at observed x; accept iff U ≤ 0.005 (x ≤ 1) | PRIMARY-P5 (sole confirmatory decision) | S13, F7(a), C15, T1 row 15 |
| D2-16 | Native trigger rate of the template pool ⟨x/106⟩ | trigger_rates.csv → quantity=native_trigger_rate → n, p, lo, hi | descriptive (Wilson shown, labeled descriptive) | DESCRIPTIVE-PRESPEC | F7(c), T1 row 14 |
| D2-17 | Paired controls, detection D: 2 × 2, yields, paired difference | d2_paired_controls_summary.csv → endpoint=D → n_pairs_scored, n_targets, n_unique_windows, both, b_only, c_only, neither, union, p_b, p_c, paired_diff_b_minus_c (+lo/hi), p_b_and_not_c (+lo/hi), n_pairs_not_run | cluster bootstrap | SECONDARY | F7(b) |
| D2-18 | Paired controls, strict recovery R; P(R_B=1, R_C=0) | same → endpoint=R | cluster bootstrap | SECONDARY (attribution diagnostic) | S12, F7(b), T1 row 13 |
| D2-19 | Quiet-control-conditioned recovery (|T_Q|, pairs, unique windows) | d2_paired_controls.csv → pair_usable & control status not_detected → aggregate per spec | cluster bootstrap | SECONDARY | ApJL §4 |
| D2-20 | Control reuse table | d2_control_reuse.csv → control_campaign_id, template_source_id, n_b_assignments, n_targets | counts | DESCRIPTIVE-PRESPEC (mandatory) | F7(c) inset |
| D2-21 | Chance-match calibration (target-level derangements) | chance_match.json (D2) → derangements=10000, accidental_recovery_rate_mean/p95, accidental_any_mode_rate_mean/p95 | derangement | DESCRIPTIVE-PRESPEC | F5 caption |
| D2-22 | Census / L-S post-injection response table | contingency_complementarity.json (D2) → table, union, incremental (no intervals; mcnemar prohibited); d2_cluster_completeness.csv → endpoint=paired_census_minus_ls_discordance | descriptive; cluster paired difference | DESCRIPTIVE-PRESPEC (no recovery attribution) | C16 (D2 clause) |
| D2-23 | Row-level completeness by pass × rule × scope (30 → 309 windows) | completeness_by_class_pass_rule.csv (D2) → inference="descriptive (window rows)…" | NO intervals | DESCRIPTIVE-PRESPEC | never headline |
| D2-24 | Arm-A (Gaussian-floor) positive injections | d2_cluster_completeness.csv → arm=A, scenario=nominal | cluster bootstrap | DIAGNOSTIC | ApJL appendix |
| D2-25 | Retained-vs-rejected modes (|sinc| ≥ 0.3), excluded targets (0), cadence assignment | generation_manifest_gen2.json → total_rejected_mode_rows (22), excluded_targets ([]), cadence_alt_tics (33); shards/injected_modes.csv, rejected_modes.csv | counts | design fact | C6 |
| D2-26 | Romero self-window diagnostic | separate arm (96-prefix), only if run; never enters nominal | — | DIAGNOSTIC | ApJL appendix, conditional |

## 3. D1 — the finite-roster anchor

| ID | Claim | Artifact | Status | Used in |
|---|---|---|---|---|
| D1-1 | 11/13 L-S, 9/13 census, 13/13 union, 0 confirmed + 1 candidate among 5 constants; 1 transit control excluded | lomb-scargle/results/2026-08-01_full/master_table.csv; METRICS_SPEC "Validation on record (2026-08-28)" — the campaign engine reproduces all five | ANCHOR (DESCRIPTIVE-PRESPEC counts; Wilson finite-roster intervals) | S5, F8, C2, T1 row 16 |
| D1-2 | D1 frequency agreement | per_star.csv (D1 run of the metrics engine) → best_candidate_matches_dominant with truth-quantum +0.0025 d⁻¹ | DIAGNOSTIC only | ApJL appendix |
| D1-3 | 928-catalog 2 × 2 (109/233/94/492; 327 one-channel) | talk/data/ls_full_catalog.csv, census_full_catalog.csv | DESCRIPTIVE (rule disagreements; NOT a labeled denominator) | poster F8 caption at most |

## 4. Provenance and pre-registration facts

| ID | Claim | Artifact | Status |
|---|---|---|---|
| PV-1 | Frozen five scripts unchanged since tag `frozen-2026-08-01`; empty `git diff` | scripts/generalization/frozen_api.py SHA table; `git diff frozen-2026-08-01 -- scripts/<frozen five>` | PROVENANCE |
| PV-2 | 25/25 and 928/928 published stars replay byte-identically on the attested laptop (921 identical_v1_schema + 7 identical_newline; 13 h, 15 workers) | generalization/attestation/laptop_replay_full_2026-08-29/; RUNBOOK.md "Attested production machine" | PROVENANCE |
| PV-3 | Panel-stage golden gate PASS both machines; CLI-identity PASS | attestation/laptop_panel_gate_2026-08-30/, laptop_cli_identity_2026-08-30/ | PROVENANCE |
| PV-4 | Env pins (Python 3.12.12, numpy 2.3.5, scipy 1.16.3, astropy 8.0.1, pandas 2.3.3, iers-data 0.2026.7.27) | generalization/env/FROZEN_ENV.md, requirements-frozen.txt; run manifests env_versions() | PROVENANCE |
| PV-5 | Spec/plan frozen 2026-08-28 after 6 sol rounds; A2/A3 2026-08-30 pre-run; A4 2026-08-30 post-pilot pre-confirmatory (disclosed); diurnal admission 2026-08-31 post-launch descriptive; SHAs | reviews/G2_FREEZE.md; tag g2-frozen-2026-08-28; metrics manifest.json → spec_sha256 | PROVENANCE |
| PV-6 | D3 crossmatch frozen as DATA before any D3 metric | data/d3/crossmatch_freeze/ (freeze_manifest.json, SHA256SUMS; commit e2988f2) | PROVENANCE |
| PV-7 | Every scored result provenance-bound (sidecars, completion table, generation id, attestation SHA) | metrics manifest.json, inputs_sha256.json; attrition.csv → provenance_verified | PROVENANCE |
| PV-8 | Amendment 4 motivation (degenerate exposure strata; detection-only measured native triggers) | results/2026-08-30_d2_pilot/README.md; reviews/G4/ | PILOT — cite as motivation only, never as a number |

## 5. Synthesis claims (qualitative only)

| ID | Claim | Condition | Artifact | Status |
|---|---|---|---|---|
| SY-1 | Census and confirmed period-search responses are empirically non-redundant in each assessment | both discordant cells > 0 in each of D1, D2, D3 | three contingency_complementarity.json files | DESCRIPTIVE-PRESPEC, conditional |
| SY-2 | The three assessments separate finite-anchor behavior, model-conditioned recovery, and externally labeled performance | always | design | framing |
| SY-3 | Any cross-dataset comparison is a side-by-side table, never a pooled estimate | always | Table 1 | rule (N2) |

## 6. Slot → artifact cross-index (abstract)
S2→PV-2 · S3→D3-14 · S4→D2-25 · S5→D1-1 · S6→D3-1, D3-2 · S7→D3-3, D3-4 ·
S8→D3-7 · S9→D3-10 · S10→D3-13 · S11→D2-1, D2-2, D2-3 · S12→D2-8, D2-18 ·
S13→D2-15 · S14→SY-1.
