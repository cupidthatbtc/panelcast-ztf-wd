# Pre-metrics ruling — fixed 2026-09-01

This ruling uses frozen rosters, manifests, panel files, and code schemas only. No full-campaign D3 or D2 metric enters any definition.

For every admitted descriptive CSV:

```text
analysis_status=postlaunch_descriptive
prespecified=false
interval=none
```

Compliance outputs in item 1 instead carry:

```text
analysis_status=prespecified_compliance
prespecified=true
interval=none
```

Descriptive files go under `<result>/descriptive_postlaunch/`; figures receive a source CSV and metadata sidecar carrying those fields. Unless stated otherwise, bins are left-closed/right-open, missing values receive explicit `*_unknown` cells, zero cells are emitted, and rates are blank when their denominator is zero. None may enter a headline, endpoint decision, exclusion, reclassification, or replacement denominator.

## 1. F07 — COMPLIANCE

This is a delayed implementation of requirements already mandated by METRICS_SPEC, rather than a new analysis. It must be implemented in `metrics_generalization.py`.

### Frequency-scorable guard

For D3, define `mo_joined` iff a `dsct_flag1` KIC has:

- at least one finite Mo table-2 `Freq`;
- a finite table-2 maximum-amplitude row;
- finite positive dominant frequency and finite dominant amplitude in the roster.

Set `freq_scorable` from that conjunction and assert:

```text
sum(class_label == "dsct_flag1" and mo_joined) == 456
```

Also assert identity with the 456 `freq_scorable` rows used by P2. Abort before writing any output on failure.

### Mandatory attrition table

`metrics/attrition.csv` becomes the mandated table. Its exact columns are:

```text
class_label,amp_bin,mo_join_status,magnitude_bin,period_bin,teff_bin,
cone_count_bin,separation_bin,
n_roster,n_fetched,n_crossmatched,n_qc_passed,n_both_passes,
analysis_status,prespecified,interval
```

“Crowding” is one conceptual dimension represented by the two required components `cone_count_bin` and `separation_bin`. Emit every observed roster-level Cartesian cell.

Stages are cumulative:

- `n_roster`: fixed 3,000-row roster.
- `n_fetched`: nonempty cache file, `cache_present=true`.
- `n_crossmatched`: `read_status=="ok"`, finite nearest separation, and `selected_ztf_objects >= 1`.
- `n_qc_passed`: frozen `crossmatched=true`, equivalently at least 20 QC-passing observations in both zg and zr.
- `n_both_passes`: result exists and both `low_available` and `high_available` are true.

Assert monotonicity within every cell and globally.

Bins:

- `class_label`: `dsct_flag0`, `dsct_flag1`, `dsct_flag2`.
- `mo_join_status`: `mo_joined`, `mo_unjoined`.
- Magnitude: `g_le_14` for finite `gmag <= 14.0`; `g_gt_14`; `g_unknown`.
- Amplitude, mmag: `amp_unknown`, `<0.5`, `[0.5,1)`, `[1,2)`, `[2,5)`, `[5,10)`, `[10,20)`, `[20,50)`, `>=50`. Negative finite amplitudes abort.
- Dominant period: `period_unknown`, `<100 s`, `[100,200) s`, `[200,500) s`, `[500,1000) s`, `[1000,2000) s`, `[2000 s,0.05 d)`, `[0.05,0.2) d`, `[0.2,1) d`, `[1,10) d`, `[10,100) d`, `>=100 d`. These are the frozen surface edges.
- Teff: pooled finite Teff values from the fixed 3,000-star eligible roster, using linear quantiles fixed now at `6597.0`, `6737.0`, and `7092.5 K`: `<6597`, `[6597,6737)`, `[6737,7092.5)`, `>=7092.5`, plus unknown.
- Cone count: unknown, `0–3`, `4–6`, `7–9`, `>=10`.
- Nearest separation, arcsec: unknown, `<0.054159657268769895`, `[0.054159657268769895,0.0972924425684607)`, `[0.0972924425684607,0.15375607598589985)`, `[0.15375607598589985,1.0)`, `>=1.0`. The first three cuts are linear quartiles of the fixed 2,901-row finite crossmatch frame; 1.0″ is the frozen crowding-clean boundary.

Preserve the current seven-scalar audit as new `metrics/attrition_summary.csv`; it is no longer the mandatory attrition table.

### Joined-vs-unjoined table

Write `metrics/d3_mo_join_covariates.csv`, restricted to all 610 eligible `dsct_flag1` positives. Columns:

```text
mo_join_status,covariate,n_group,n_nonmissing,n_missing,
mean,sd,p10,p25,p50,p75,p90,min,max,
analysis_status,prespecified,interval
```

Use population SD (`ddof=0`) and linear quantiles. Covariates are fixed as:

```text
gmag,Teff,logg,ra,dec,subhour,cache_present,qc_passed,both_passes,
nearest_separation_arcsec,ztf_objects_in_cone,selected_ztf_objects,
zg_clean_rows,zr_clean_rows
```

Binary means are fractions. No tests or standardized-difference thresholds are permitted.

### Boundary ruling

Metric stratification must implement `gmag <= 14.0`, as the spec says. Do not edit `build_d3_roster.py` or the roster. Ignore its legacy `near_saturation` field for these compliance and new descriptive strata. Thus the three `gmag == 14.000` negatives enter `g_le_14`.

### Timing and guard

Allow the automatic pre-fix laptop metrics to finish and archive them without interpreting the results. Then patch and rerun metrics on the Mac. Within the patched invocation, the 456 guard must run before any output is committed.

The proposed byte-identity guard over *every* pre-existing file is impossible: `attrition.csv` must change, and `manifest.json` must record the new `metrics_generalization.py` SHA and Mac environment; path-keyed `inputs_sha256.json` can also differ across machines.

The sufficient guard is:

1. Byte identity for every pre-existing science output except `attrition.csv`: `per_star.csv`, completeness, contingency, trigger rates, PPV, frequency audit, chance calibration, surfaces, and sensitivity.
2. Expected-only diffs in `attrition.csv`, `manifest.json`, and path-keyed provenance.
3. Identical input-content SHAs after canonicalizing paths.
4. Additivity/monotonicity checks for the new table, exact `456/154` joined/unjoined positive counts, and a source diff confined to compliance-output construction and guards.

Disclosure:

> Prespecified-compliance repair: METRICS_SPEC v4 required the multidimensional D3 attrition table, the Mo-joined versus unjoined covariate table, and an exact 456-star frequency-scorable guard before any D3 result was known; these requirements were implemented post-launch without changing any endpoint, denominator, matching rule, or interval, and their magnitude strata re-derive the specified \(g\le14.0\) boundary from the fixed roster despite its legacy \(g<14.0\) flag.

## 2. F02–F04 — ADMIT-DESCRIPTIVE

Write:

```text
descriptive_postlaunch/d3_truth_provenance_rescoring.csv
descriptive_postlaunch/d3_p2_by_dominant_frequency_regime.csv
```

### Aliased-dominant targets and fR rescoring

Use table-1 rows with `C==0`. A positive is `aliased_dominant=true` when at least one such row satisfies:

```text
abs(table1.Freq - roster.dom_freq_uhz) <= 0.1 µHz
```

If several rows qualify, select minimum absolute difference, then minimum `fR` as the deterministic tie-break. Assert exactly 40 `dsct_flag1` targets.

For each, convert `fR` with `86400/1e6`. Apply the entire frozen taxonomy to the best candidate against that single physical frequency:

```text
tolerance_per_day = 1.5 / baseline_days
direct, harmonic, window_alias, ambiguous, unmatched
```

The Nyquist constant is exactly:

```text
f_Nyq = 283.2 µHz = 24.46848 d^-1
```

Define the additional relation:

```text
matches_nyquist_reflection =
abs(f_candidate - (2*24.46848 - fR_per_day)) <= tolerance_per_day
```

Only positive reflected frequencies are eligible. This relation is an independent boolean and never alters the frozen taxonomy.

For descriptive any-mode scoring, use the exact union of:

- all finite table-2 frequencies for that KIC; and
- all finite table-1 `fR` values with `C==0`.

Evaluate `best_candidate_matches_any_mode_plus_fR` with the frozen taxonomy and `any_top_peak_matches_any_mode_plus_fR` as direct agreement by any stored top-15 peak.

Per-target columns:

```text
sid,KIC,best_status,best_frequency_per_day,baseline_days,tolerance_per_day,
aliased_dominant,table1_alias_uhz,fR_uhz,fR_per_day,
nyquist_reflection_per_day,best_candidate_match_fR,
matches_nyquist_reflection,
best_candidate_matches_any_mode_plus_fR,
any_top_peak_matches_any_mode_plus_fR,
analysis_status,prespecified,interval
```

### P2 regime split

Use the exact frozen P2 frame: `dsct_flag1`, Mo-joined/frequency-scorable, both passes available, `S_best=1`, rule 1, best pass. Success remains `best_status=="confirmed"` and frozen dominant match class `direct`.

Rows:

```text
dominant_lt_4       [-inf,4)
dominant_4_to_24    [4,24)
dominant_ge_24      [24,inf)
```

Columns:

```text
dominant_frequency_regime,lo_inclusive_per_day,hi_exclusive_per_day,
n_p2,k_confirmed,k_direct_recovery,rate_direct_recovery,
analysis_status,prespecified,interval
```

The `>=24` row is counts-only. A factual correction is necessary: the fixed roster currently contains 10 of 456 dominant frequencies in `[24,24.46848)`; the empty statement applies at `>=24.47`, not at `>=24`.

Use the wording “stars with a confirmed super-Nyquist mode.” Define “dominant” as the largest-amplitude Mo table-2 mode, which need not be a p mode.

Timing: after frozen D3 metrics.

Disclosure:

> Post-launch descriptive truth-provenance audit: frozen P2 remains an unchanged best-pass comparison against the largest-amplitude Mo table-2 frequency, while the added files report physical-\(f_R\), Kepler-Nyquist-reflection, augmented-any-mode, and dominant-frequency-regime counts without replacing P2; “dominant” means largest amplitude rather than necessarily a p mode, and the former “sub-hour stratum” is described as stars with a confirmed super-Nyquist mode.

## 3. F01 — ADMIT-DESCRIPTIVE; positive diurnal extension REFUSED

Write `descriptive_postlaunch/d3_confirmed_positive_match_partition.csv`.

Frame: all eligible `dsct_flag1` positives with `best_status=="confirmed"` under rule 1 and best pass. Cross:

```text
best_candidate_matches_dominant ∈
{direct,harmonic,window_alias,ambiguous,unmatched,unscored}

any_top_peak_matches_any_mode ∈ {false,true}
```

Emit all 12 cells. Columns:

```text
match_class,any_top_peak_matches_any_mode,
n_positive,n_confirmed_positive,n_cell,
rate_of_all_positives,share_of_confirmed_positives,
analysis_status,prespecified,interval
```

Use `n_positive=610`; unjoined confirmed positives remain `unscored`, never dropped.

The admitted solar-diurnal rule is explicitly a partition of the negative-class P3 numerator only. Applying it to confirmed positives exceeds the 2026-08-31 admission. No positive-class `within_solar_diurnal_band` column is authorized here.

Timing: after frozen D3 metrics.

Disclosure:

> Post-launch descriptive analysis: `d3_confirmed_positive_match_partition.csv` partitions the frozen rule-1 best-pass confirmed-positive numerator by its already-emitted dominant-match class and top-15 any-mode indicator over the unchanged 610-star P1 denominator, carries no interval or endpoint status, and does not identify or remove wrong-reason triggers.

## 4. F09 — ADMIT-DESCRIPTIVE, presentation only

No new scientific computation or metric file is implied.

Present the two existing rows from `completeness_by_class_pass_rule.csv` with:

```text
pass ∈ {low,high}
rule=confirmed
scope=freq_recovery_scorable
```

beside the existing arm-B, nominal, `endpoint=recovery` P4 rows in `d2_cluster_completeness.csv`. Copy values verbatim. Label the pass rows “descriptive window-row recovery”; they are not target-cluster P4 variants.

P4 must be described as a best-pass estimand. Its eligible and usable target-cluster rows and intervals remain exactly as emitted.

File placement: manuscript/poster table assembly only; no new results CSV.

Timing: after frozen D2 metrics.

Disclosure:

> P4 is the prespecified target-equal best-pass recovery estimand; the adjacent low- and high-pass rows are already-emitted descriptive window-row diagnostics and do not replace or modify P4.

## 5. F08/F11/F38 — ADMIT-DESCRIPTIVE

### K × template status

Write `descriptive_postlaunch/d2_k_template_status.csv`.

Restrict to `arm=="B"` and `scenario=="nominal"`. Cross all `template_k={0,1,2}` with manifest `template_status={not_detected,candidate,confirmed}` and endpoints `{recovery,trigger}`.

- `trigger`: best status confirmed.
- `recovery`: trigger and frozen dominant match direct.
- Scheduled denominator includes missing rows as failures.
- `n_usable` requires both passes available and is context only; no usable-rate column.

Columns:

```text
template_k,wg_stratum,template_status,endpoint,
n_scheduled,n_usable,k_success,rate_scheduled,
wg_min,wg_median,wg_max,
analysis_status,prespecified,interval
```

### Control reuse figure

Generate from the existing `d2_control_reuse.csv`, with one bar per unique control, sorted by descending `n_b_assignments` then `control_campaign_id`. Plot assignment count, with `n_targets` available in the source table.

Files:

```text
descriptive_postlaunch/d2_control_reuse.png
descriptive_postlaunch/d2_control_reuse_source.csv
descriptive_postlaunch/d2_control_reuse.meta.json
```

### Paired A/B table

Write `descriptive_postlaunch/d2_arm_a_b_pairs.csv`. Require exactly one nominal A and one nominal B row per `(tic,template_k)` and assert matching template source, W_g, and status metadata.

Columns:

```text
tic,template_k,template_source_id,template_status,wg_contrasts,
a_sid,b_sid,a_status,b_status,a_usable,b_usable,pair_usable,
D_A,D_B,R_A,R_B,trigger_pair_class,recovery_pair_class,
analysis_status,prespecified,interval
```

`D` is confirmed; `R` is confirmed plus dominant direct. Pair classes are `both`, `A_only`, `B_only`, `neither`, or blank when `pair_usable=false`. No aggregate contrast, test, or interval is authorized.

Timing: after frozen D2 metrics.

Disclosure:

> Post-launch descriptive D2 diagnostics report nominal arm-B recovery and triggering by \(K\) and the template’s published status, the fixed control-window reuse pattern, and paired nominal arm-A/arm-B outcomes per target and \(K\); the rows expose native-variability and reuse confounding, carry no interval, and cannot support an unqualified recovery-versus-\(W_g\) trend.

## 6. F15/F17/F27/F37 — ADMIT-DESCRIPTIVE

Write:

```text
descriptive_postlaunch/d3_negative_trigger_strata.csv
descriptive_postlaunch/d3_covariates_by_class.csv
```

### Negative trigger strata

Frame: all 2,314 `dsct_flag0` roster members; missing/unusable results are non-triggers.

For magnitude, Teff, merged-oid count, and sky cell, use rule 1 and best pass. For pass rows, use the corresponding `low_status` or `high_status`.

Columns:

```text
stratifier,stratum,pass_basis,rule,
n_negative,k_confirmed,rate,
analysis_status,prespecified,interval
```

Definitions:

- Magnitude: `g_le_14`, `g_gt_14`, `g_unknown`.
- Teff: the pooled-roster cuts fixed in item 1: `<6597`, `[6597,6737)`, `[6737,7092.5)`, `>=7092.5`, unknown.
- Merged oids: `oid_le_1`, `oid_2`, `oid_3_4`, `oid_ge_5`, `oid_unknown`. The requested substantive cells are 2, 3–4, and ≥5; the additional cells prevent silent denominator loss.
- Pass: `low` and `high`, each over all 2,314 negatives. These rows are not additive because one star may confirm in both.
- Sky: a fixed 4×4 axis-aligned RA/Dec grid from pooled finite values in the 3,000-star roster. RA cuts are `290.0945525`, `293.54213`, `296.340635` degrees; Dec cuts are `41.048665`, `43.879275`, `46.70182` degrees. Cell IDs are `RAq1_DECq1` through `RAq4_DECq4`, with half-open boundaries and an explicit `sky_unknown`.

Do not label the high-pass row a “sub-hour false-trigger proxy.” The authorized label is “high-pass negative-class rule-1 trigger rate.” Murphy `dSct=0` is neither a constant-star label nor a complete exclusion of blends and other high-frequency variables.

### Covariate-by-class table

Use all 3,000 eligible roster rows and class levels 0/1/2. Long-format columns:

```text
class_label,covariate,n_class,n_nonmissing,n_missing,
mean,sd,p10,p25,p50,p75,p90,min,max,
analysis_status,prespecified,interval
```

Covariates:

```text
gmag,Teff,ra,dec,nearest_separation_arcsec,
ztf_objects_in_cone,selected_ztf_objects,zg_clean_rows,zr_clean_rows
```

Use unweighted sample descriptions, population SD, linear quantiles, and no tests.

Timing: after frozen D3 metrics.

Disclosure:

> Post-launch descriptive analysis stratifies the unchanged 2,314-star rule-1 negative-class trigger numerator by fixed magnitude, Teff, merged-oid, pass, and sky cells and separately describes covariates by class; these are plain counts and rates without intervals, and the high-pass row is a negative-class trigger diagnostic rather than an FPR or sub-hour false-trigger estimate.

## 7. F16/F18 — ADMIT-DESCRIPTIVE

### Coverage comparison

Write `descriptive_postlaunch/d3_vs_pool_coverage.csv`.

Frames:

- `D3_crossmatched`: all 2,901 rows in the D3 census panel.
- `development_pool`: all 928 rows in `census_full_catalog.csv`.

Metrics:

```text
zg_n_exp,zr_n_exp,zg_n_nights,zr_n_nights,wg_contrasts
```

Define `wg_contrasts = zg_n_exp - zg_n_nights` and assert it is nonnegative.

Columns:

```text
frame,covariate,n_frame,n_nonmissing,
min,p10,p25,p50,p75,p90,max,
analysis_status,prespecified,interval
```

Use linear quantiles.

### Per-pass a95 distributions

Read the per-star JSONs directly. Cross:

```text
class_label ∈ {dsct_flag0,dsct_flag1,dsct_flag2}
pass ∈ {low,high}
band ∈ {zg,zr}
```

Use `passes[pass][band+"_a95_mmag"]`; no pooling across bands.

Write `descriptive_postlaunch/d3_a95_by_class_pass_band.csv` with:

```text
class_label,pass,band,n_roster,n_json,n_pass_available,
n_finite,n_missing,min,p05,p10,p25,p50,p75,p90,p95,max,
analysis_status,prespecified,interval
```

Timing: after frozen D3 metrics. The coverage component is outcome-independent but should ship in the same post-metrics descriptive bundle.

Disclosure:

> Post-launch descriptive coverage tables compare the crossmatched Kepler-field frame with the fixed 928-window development pool and summarize per-pass, per-band a95 values by D3 class; the quantiles describe the realized frames without intervals or ZTF-wide transfer claims.

## 8. F21 — ADMIT-DESCRIPTIVE

Write `descriptive_postlaunch/d3_dominant_confirmed_chance_match.csv`.

Frame: exact P2 scorable/usable/`S_best=1` positives with `best_status=="confirmed"` and finite best and dominant frequencies.

Algorithm:

- Keep candidate frequencies and per-star tolerances fixed.
- Permute dominant frequencies at the star level.
- Accept only derangements with no fixed points.
- Generate exactly 10,000 accepted derangements using `PCG64(20260829)`.
- A hit requires the frozen classifier against the permuted single dominant frequency to return exactly `direct`; `ambiguous` is not a hit.
- Denominator is every confirmed-conditioned frame member in every derangement.

Columns:

```text
conditioning,truth_basis,derangements,seed,n_confirmed,
accidental_direct_rate_mean,accidental_direct_rate_median,
accidental_direct_rate_q95,
analysis_status,prespecified,interval
```

The q95 field is a quantile of the randomization distribution, not an interval.

Timing: after the frozen 100-permutation chance file is written.

Disclosure:

> Post-launch descriptive chance calibration conditions on the frozen P2 confirmed/scorable frame and uses 10,000 star-level derangements of the single dominant frequency; it accompanies, without replacing, the prespecified 100-permutation any-mode accidental-match audit and carries no inferential interval.

## 9. F32/F33 — ADMIT-DESCRIPTIVE

### D1 versus D3 frequency histogram

Select:

- D1: `blind_status=="confirmed"` from the 928-star published catalog.
- D3: `dsct_flag0` and `best_status=="confirmed"`.

Abort if any selected row lacks a finite positive best frequency.

Fixed edges, d\(^{-1}\):

```text
0, 0.25, 0.50, 0.75, 0.98, 1.02, 1.25, 1.50, 1.75,
1.98, 2.02, 2.25, 2.50, 2.75, 2.98, 3.02, 3.25, 3.50,
3.75, 4, 6, 8, 12, 16, 20, 24, 32, 48, 96, 192, 384,
768, 1440, infinity
```

Use left-closed/right-open bins, with the final finite edge included in the overflow rule. Normalize each dataset separately by its confirmed count. For finite-width bins, plot `share/bin_width` so unequal bins do not distort area.

Files:

```text
descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.csv
descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.png
descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.meta.json
```

Source columns:

```text
dataset,selection,bin_index,freq_lo_per_day,freq_hi_per_day,
n_confirmed_total,n_bin,share_of_confirmed,density_per_day,
analysis_status,prespecified,interval
```

### Extra relation columns

Write `descriptive_postlaunch/d3_extra_frequency_relations.csv`; never add these columns to frozen `per_star.csv`.

Let:

```text
delta_year = 1/365.25 = 0.0027378507871321013 d^-1
f_Nyq = 24.46848 d^-1
tol = 1.5/baseline_days
```

For the dominant frequency and, separately, every table-2 mode:

```text
yearly_alias:
abs(f_candidate - abs(f_truth ± delta_year)) <= tol

kepler_nyquist_reflection:
f_ref = 2*f_Nyq - f_truth
f_ref > 0 and abs(f_candidate - f_ref) <= tol
```

These are independent booleans. Harmonics and sidereal aliases are not folded into them.

Columns:

```text
sid,best_status,best_frequency_per_day,baseline_days,tolerance_per_day,
frozen_best_candidate_matches_dominant,
frozen_best_candidate_matches_any_mode,
matches_yearly_alias_dominant,matches_yearly_alias_any_mode,
matches_kepler_nyquist_reflection_dominant,
matches_kepler_nyquist_reflection_any_mode,
analysis_status,prespecified,interval
```

Timing: after frozen D3 metrics.

Disclosure:

> Post-launch descriptive frequency audits compare the normalized best-frequency distributions of published D1 confirmations and D3 negative-class confirmations and report yearly-alias and Kepler-Nyquist-reflection predicates beside the unchanged frozen taxonomy; the added relations never reclassify a frozen match or alter P2 or P3.

## 10. F05 — ADMIT-DESCRIPTIVE

Create `generalization/writing/methods_review/PRESPECIFICATION_EXPOSURE.csv` before inspecting full D3 metrics. Columns:

```text
date,event,trigger,data_seen_before_change,change,status_at_time,
analysis_status,prespecified,interval
```

Required rows:

| Date | Event | Trigger | Data seen before change | Change/status |
|---|---|---|---|---|
| 2026-08-29 | Amendment 1 | Cross-platform replay mismatch | Published-bundle replay diagnostics on Windows, Colab, and Mac; no campaign outcome | Decision-equivalent tier proposed and partially implemented; never ratified; all campaign L-S runs used the strict attested laptop tier |
| 2026-08-30 | Amendment 2 | G3 numerical/methods review | Source tables, SPOC metadata, code probes; no campaign L-S output | D2 truth/manifest/generation/crowding/dropout/pilot corrections; ratified before campaign L-S |
| 2026-08-30 | Amendment 3 | Mixed-cadence SPOC verification | Verification metadata for all 103 targets; no campaign L-S outcome | Added the separate 33-target `cadence_alt` sensitivity; nominal rule unchanged |
| 2026-08-30 | Amendment 4 | Gen1 D2 timing pilot | 144 non-confirmatory pilot shards and pilot metrics; no full-run estimate | Replaced degenerate window strata with W_g, made recovery primary P4, and added paired controls and associated metric corrections; ratified pre-confirmatory |
| 2026-08-31 | Diurnal descriptive admission | D3 150-star timing pilot | Raw pilot statuses/frequencies; full D3 launched; no full-campaign metric | Fixed negative-only solar-diurnal numerator partition; no spec, endpoint, or pipeline change |

Exact reconciliation sentence:

> Read literally, the METRICS_SPEC header places the freeze at the first campaign L-S pilot, whereas the ratified ledger places it at the first confirmatory D2/D3 full run; accordingly, Amendment 4 is reported as post-pilot and “prespecified” only under the ledger’s confirmatory-run convention rather than as part of original v3, and the 2026-08-31 diurnal partition is post-launch descriptive under both records.

Timing: before full D3 metrics are opened or summarized.

Disclosure:

> This dated exposure table records every post-freeze proposal or admission, the information available before it, and its effect on the campaign, and is a disclosure record rather than a scientific endpoint.

## 11. Disclosure register

No objection to disclosure-only treatment of F06, F12, F13, F19, F20, F22, F23–F31, F35, F36, and F39. Item 1 controls the actual `g==14.0` metric stratification despite F22’s legacy-roster disclosure; item 6 supplies F27’s sky-cell diagnostic. None of the register entries authorizes an endpoint or hierarchy change.

**VERDICT SUMMARY — 1 COMPLIANCE; 2 ADMIT-DESCRIPTIVE; 3 ADMIT-DESCRIPTIVE (positive-class diurnal extension REFUSE); 4 ADMIT-DESCRIPTIVE; 5 ADMIT-DESCRIPTIVE; 6 ADMIT-DESCRIPTIVE; 7 ADMIT-DESCRIPTIVE; 8 ADMIT-DESCRIPTIVE; 9 ADMIT-DESCRIPTIVE; 10 ADMIT-DESCRIPTIVE.**
