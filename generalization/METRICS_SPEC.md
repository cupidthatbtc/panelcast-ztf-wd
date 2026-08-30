# METRICS_SPEC — to be frozen at G2 (freeze = git blob SHA recorded in
# GENERALIZATION_PLAN.md when the G2 panel reaches no-blocker verdicts)

Implemented by `scripts/generalization/metrics_generalization.py`. Any change
after the first campaign L-S run voids the prespecification and must be
reported as such. v3, 2026-08-28: absorbs G2 round-2 findings (referee2,
stats2, methods2, abstract lenses). v4, 2026-08-30 (Amendment 4): a DISCLOSED
post-pilot, pre-confirmatory amendment — the gen1 timing pilot (non-
confirmatory, archived, entering no estimate) exposed a degenerate D2 window
stratification and a construct-validity defect in detection-only P4; both
are repaired here BEFORE any confirmatory-era run, and no further hierarchy
change is permitted after Amendment 4.

## Estimand vocabulary (names are binding)

Three separate response assessments; never pooled.

- **detection completeness** — P(rule fires | labeled positive), reported for
  BOTH denominators: `eligible_roster` (missing/unusable light curves count
  as non-detections) and `usable_lightcurve` (frozen QC passed, both passes
  complete). D1 denominators: the 13 paper-variable stars of the published
  19-star master table (the 928-star catalog is NOT a labeled-positive
  completeness denominator). D3: the 610 dSct=1 survivors. D2: injection
  targets — always labeled *conditional injection-recovery efficiency of the
  search stage*. Amendment 4: the D2 PRIMARY endpoint is injected-signal
  RECOVERY (rule 1 fires AND the best candidate directly matches the
  largest-amplitude retained injected mode, `endpoint = recovery`);
  post-injection rule firing (detection-only) is the SECONDARY
  "post-injection rule-1 trigger rate" (`endpoint = trigger`) and carries no
  recovery or completeness interpretation; paired uninjected controls
  contextualize native triggers and never enter the primary denominator.
- **frequency-recovery completeness** — P(rule fires AND
  best_candidate_matches_dominant | labeled positive AND freq-scorable AND
  S_p = 1). Freq-scorable: D3 = Mo-joined with >=1 frequency and a defined
  dominant amplitude (assert count == 456; "Mo-join-conditioned" label
  mandatory; joined-vs-unjoined covariate table mandatory); D2 = >=1
  RETAINED injected mode (from injected_modes.csv, post |sinc|>=0.3
  rejection — never the original mode table); D1 = diagnostic only
  (non-contemporaneous literature frequencies; see below).
  S_p (per pass p): >=1 truth frequency inside pass p's search bounds
  (low: [2/baseline, 48] / d; high: [24, 1440] / d); S_best = S_low OR
  S_high. Known consequence stated up front: only ~10/456 D3 dominant
  frequencies lie >= 24 / d, so D3 high-pass frequency recovery is a
  near-empty cell and is reported as counts.
  Mo-join MNAR limitation (binding statement): Mo inclusion required
  SNR > 8 in Kepler photometry and is plausibly related to amplitude,
  magnitude, and mode complexity; missingness for the 154 unjoined
  positives is treated as informative — the frequency-recovery curve is
  therefore a Mo-join-conditioned estimand, the joined-vs-unjoined
  covariate table is mandatory, and DETECTION surfaces retain all 610
  positives with the unjoined stars in an explicit `amp_unknown` bin so
  their detection behavior is visible beside the joined sample.
  The missed-vs-wrong-frequency decomposition uses matching denominators
  only: P(D AND M | Y=1, F=1, S_p=1) vs P(D | Y=1, F=1, S_p=1).
- **correct-frequency fraction among detected positives** —
  P(best_candidate_matches_dominant | rule-1 fired, Y=1, F=1, S_p=1).
  Never called purity.
- **frame-specific label PPV (D3 only)** — among triggered roster members of
  the weighted frame {dSct=1 census positives, dSct=0 SRS negatives; dSct=2
  EXCLUDED, reported separately}: weighted fraction labeled dSct=1.
  Interval: FPC-rescaled survey bootstrap (B=2000, frozen seed): the 2,314
  negatives are resampled with replacement, positives held fixed (census),
  and bootstrap deviations are rescaled by sqrt(1 − f) with sampling
  fraction f = 2314/7292 (SRSWOR finite-population correction).
  No transfer to other prevalences. Output: ppv.csv.
- **negative-class trigger rate (D3)** — P(rule fires | dSct=0, the
  NON-dSct COMPARISON CLASS — it contains genuine gamma Dor, rotational,
  binary and other variables, which is why this is a trigger rate). Weights are
  constant within the class and cancel: plain Wilson on the 2,314 sampled
  negatives (no FPC — conservative). Triggered negatives adjudicated in W4
  (plausible real variable vs unexplained), reported descriptively.
- **Gaussian-null false-alarm rate (FPR_Gaussian, D2)** — P(confirmed |
  arm-A zero-amplitude null), n = 1000; window allocation frozen as
  deterministic cycling of the sorted 928-window pool (serial i -> window
  i mod 928), noise seed = serial. Interval: EXACT one-sided
  Clopper-Pearson upper bound at the OBSERVED event count x
  (U = Beta_{0.95}(x+1, n-x)); acceptance criterion (confirmatory):
  U_95(x, 1000) <= 0.005. Windows repeat; inference is conditional on the
  frozen window set. FP frequency-distribution/alias audit descriptive only
  below 10 events.
- **native trigger rate of the template pool (D2)** — P(confirmed | paired
  uninjected control window, 95-prefix). Context, not an FPR.

Exact D3 sampling constants (binding): negatives inclusion probability
2314/7292 (= 0.31733406...), sampling weight 7292/2314 (= 3.15125324...);
never derived from rounded values.

## D1 specifics

Labels from the published master table (19 usable stars: 13 paper-variable,
5 paper-constant, 1 transit control excluded from both classes — it is the
frozen pipeline's eclipsing sanity object). D1 truth frequencies are
non-contemporaneous single-epoch literature tabulations of multi-mode
pulsators (observed lit-vs-ZTF offsets reach 0.6%): frequency-recovery for
D1 is DIAGNOSTIC only; the D1 estimand is detection completeness.
Match tolerance adds a truth-quantum term: D1 +0.0025 / d (2-decimal
tables); D2/D3 +0. Validation on record (2026-08-28): the engine reproduces
all five published D1 numbers (11/13 L-S, 9/13 census, 13/13 union,
0 confirmed + 1 candidate among the 5 constants).

## Frequency-match taxonomy (evaluate everything, then classify)

Tolerance: 1.5 / baseline_days + truth-quantum. f_sid = 1.00273790935 / d
(frozen, the pipeline's constant). For each detected candidate, evaluate ALL
(truth mode, relation) hits across the star's full truth list:
  direct       |f_cand - f_t| <= tol
  harmonic     |f_cand - 2 f_t| <= tol or |f_cand - f_t/2| <= tol
  window_alias |f_cand - |f_t +/- k f_sid|| <= tol, k = 1, 2
Classification: no hits -> `unmatched`; hits in exactly one relation class ->
that class (several DIRECT hits on different modes remain `direct`); hits in
more than one relation class -> `ambiguous` (excluded from strict recovery).
Named estimator columns encode both axes:
`best_candidate_matches_dominant` (headline; D3 dominant Mo mode / D2
largest-amplitude retained injected mode; D1 diagnostic) and
`best_candidate_matches_any_mode` (secondary), plus
`any_top_peak_matches_any_mode` (diagnostic over the 15 stored peaks).
Chance-match calibration: truth lists permuted across stars (frozen seed
20260829, 100 permutations) -> accidental direct-match rate beside every
frequency-recovery table.

## Detection rules and the preregistered primary family

Rules (all four always reported): 1 `confirmed`, 2 `confirmed|candidate`,
3 `census` (any of six frozen ratios >= 2.5), 4 `either` (1 OR 3).
PRIMARY endpoints — complete tuples; everything else is pointwise
descriptive sensitivity:
  P1 D3 detection completeness: {D3, dSct=1 (610), eligible_roster, rule 1,
     best pass, unweighted, Wilson 95%}.
  P2 D3 frequency recovery: {D3, Mo-joined S_best=1 subset, usable, rule 1 +
     best_candidate_matches_dominant, Wilson 95%, beside chance-match rate}.
  P3 D3 negative-class trigger rate: {D3, dSct=0 (2314), rule 1, best pass,
     plain Wilson}.
  P4 D2 conditional injection-recovery, algebraically (Amendment 4):
     p-hat = (1/103) Σ_t (1/|K_t|) Σ_{k in K_t} y_{t,k}, where y_{t,k} = 1
     iff rule 1 fires AND best_candidate_matches_dominant == direct (the
     largest-amplitude RETAINED injected mode from injected_modes.csv) on
     target t's stratum-k nominal (1.7/0.80, PDCSAP as published,
     phase_draw 0, cadence rule) arm-B shard, and K_t ⊆
     {0, 1, 2} is the set of strata with a usable result. ELIGIBLE variant:
     denominator all 103 targets; missing stratum counts y = 0 with
     |K_t| = n_strata_scheduled (3 for the nominal scenario; 1 for the
     single-window sensitivity scenarios — Amendment 2); a K_t = ∅ target
     contributes 0. USABLE variant:
     p-hat_u = (1/(103 − n_∅)) Σ_{t: K_t ≠ ∅} (1/|K_t|) Σ_k y_{t,k} —
     K_t = ∅ targets are excluded from numerator AND denominator, with
     n_∅ reported as n_targets_zero_usable_strata. The bootstrap resamples
     all 103 target labels with the common draw matrix for both variants;
     a resampled-in K_t = ∅ target contributes 0 to the eligible statistic
     and is dropped from that replicate's usable statistic (matching the
     estimators). Both variants reported. Interval: target-cluster
     bootstrap 95%.
  P5 FPR_Gaussian acceptance: {D2 arm A nulls, rule 1, exact one-sided CP
     upper at observed x <= 0.5%} — the sole confirmatory decision.
No claim direction reversal, endpoint swap, or denominator swap after the
first campaign L-S run. Flags: `prespecified_primary` marks the P4 recovery
rows (nominal arm B, non-pilot) and the P5 row; `confirmatory_decision` is
True only on the P5 row when its acceptance rule passes (P5 is the SOLE
confirmatory decision). Paired controls (Amendment 4): every nominal arm-B
shard is scored against its paired uninjected control for detection D and
strict recovery R (the control's candidate frequency matched against the
B target's dominant injected mode); report the 2×2 counts, B-only/C-only/
union yields, target-standardized paired differences and P(R_B=1, R_C=0)
with the common target-cluster draws, the quiet-control-conditioned
secondary estimand (pairs whose control is usable and not_detected; report
|T_Q|, pairs, unique windows), and the control reuse table. No aggregate
native-rate subtraction; no conditioning of the primary denominator.

## Units of analysis and intervals

- D1/D3: the star is the unit. Wilson 95% on unweighted proportions; plain
  Wilson on the negatives class (weights cancel); survey bootstrap for PPV;
  ESS-Wilson only for other descriptive weighted proportions, labeled
  approximate.
- D2: the TESS target (TIC) is the CLUSTER; inference is CONDITIONAL on the
  frozen window assignment (report unique window count and reuse table —
  windows repeat across targets, and a target-only bootstrap does not
  represent the 928-window frame; stated as a limitation).
  Estimator: per-target mean over its replicates within a scenario/stratum;
  aggregate = equal-weight mean over the 103 targets (a scenario mix, NOT
  the 928-window frame). Window strata (Amendment 4): K = 0/1/2 are the
  round-half-even 10/50/90th-percentile positions of the magnitude-matched
  pool sorted by (W_g, source_id), W_g = Σ_nights max(n_zg,night − 1, 0) =
  the zg support surviving the frozen nightly-median subtraction; the three
  W_g values are strictly increasing for every target (production refuses
  otherwise) and are recorded per shard. Paired scenario contrasts with
  zero observed target-level discordances report the exact one-sided CP
  upper bound on the discordance probability as the effect bound, never a
  bootstrap [0, 0]. Bootstrap: resample the 103 TICs with replacement
  (B = 2000, frozen seed 20260830), carrying ALL of a resampled target's
  replicates, paired census/L-S outcomes, phases, and scenario results
  jointly; identical resample draws across scenarios (common random
  numbers). Percentile 95% intervals; if a statistic is degenerate
  (all-0/all-1), report the exact one-sided CP bound at the target level
  instead. Pooled exact McNemar is PROHIBITED for D2; use the target-cluster
  paired-difference bootstrap.
- Sensitivity contrasts (D2 ladder, phase draws, amplitude-stationarity,
  dominant-mode dropout — ALL core and binding; the ±30% multiplier is a
  local sensitivity, never presented as an astrophysical uncertainty
  envelope):
  COMMON-SUBSET RULE — every contrast against nominal is computed with
  nominal re-evaluated on the same median-window (K=1) subset and the same
  bootstrap draws. Min-max across the 3x3 grid is a "prespecified
  finite-grid sensitivity range", never a confidence band; endpoint
  scenarios identified. De-dilution and amplitude-stationarity are separate
  axes.

## Complementarity (census vs L-S)

Per dataset, on labeled positives with both methods available and usable:
C = census flag; L = rule-1 detection (detection-only, symmetric margins).
Report the full 2x2, both discordant fractions, union completeness, and
incremental yields with intervals (Wilson for D1/D3; cluster bootstrap for
D2). Exact McNemar secondary (D1/D3 only; marginal homogeneity, not
complementarity). D2 (Amendment 4): the census/L-S tables describe the
post-injection RESPONSE of nominal arm-B windows; they are descriptive
(no row-level intervals) and carry no recovery attribution.

## Surfaces

Surfaces exist for D2 and D3 only (D1 has no amplitude axis). Two
endpoints, separate files: (a) rule-1 DETECTION completeness over ALL
labeled positives — stars without a defined amplitude (the 154 unjoined
D3 positives) fall in an explicit `amp_unknown` bin (bin index −1), so
the full 610-star denominator is preserved; (b) frequency recovery over
the scorable subset only. Coordinates per star (frozen): D3 = dominant Mo
mode (period from dominant frequency; historical Kepler-band dominant
amplitude, mmag — explicitly non-contemporaneous, not a ZTF-g threshold);
D2 = largest-amplitude RETAINED injected mode (period; published TESS
amplitude, ppt). Bins half-open [lo, hi); explicit underflow and overflow
bins; no smoothing, no monotonic fitting, no interpolation. Edges frozen:
period {100 s, 200 s, 500 s, 1000 s, 2000 s, 0.05 d, 0.2 d, 1 d, 10 d,
100 d}; amplitude D3 {0.5, 1, 2, 5, 10, 20, 50} mmag with top bin
[50, inf); D2 {0.5, 2, 5, 10, 30} ppt with top bin [30, inf);
D3 median-exposures-per-night {1, 1.5, 2, 3, 5} with top bin [5, inf).
D2 window axis (Amendment 4): W_g with frozen half-open edges
{15, 41, 84, 217} = the 20/40/60/80th percentiles of the outcome-
independent 928-window pool (the builder recomputes them from the attested
pool and refuses production on mismatch); D2 surfaces are nominal arm B,
endpoints recovery (primary) and trigger, cells at TARGET level (report
n_windows, n_targets, target-equal point estimate, target-cluster bootstrap
interval when the cell holds >= 5 targets; counts only otherwise). D3
cells below 5 stars: counts only. Amplitude axes are invariant across
scenarios (never the ladder-scaled injected amplitude). Chance-match
calibration for D2: 10,000 frozen-seed TARGET-level derangements (all K
replicates of a target move together), numerators aligned with the
endpoints (dominant-mode recovery; any-mode).

## Eligibility and attrition

Both denominators always reported (see detection completeness). Attrition
table (roster -> fetched -> crossmatched -> QC-passed -> both-passes) by
class, amplitude stratum (including `amp_unknown`), Mo-join status,
magnitude, dominant period, Teff (declared the color surrogate — Murphy
carries no color column and Teff is its physical equivalent), and crowding
(cone object count, nearest-separation). The negative-sample balance
diagnostic (sampled vs full-frame quantiles of gmag/Teff/RA/Dec) is part
of the roster report (`roster_report.json`) and is a required output. D3 near-saturation strata: g <= 14.0 flagged,
g > 14.0 safe (boundary in the flagged stratum). Unavailable passes never
silently dropped; missing light curves enter eligible-roster estimands as
non-detections.

## Guards

- Assert no campaign census ratio equals 2.5 exactly.
- Assert every scored JSON has complete == true, both passes present.
- D2 truth ONLY from injected_modes.csv; assert every scored D2 shard id
  appears there (or is a null/control).
- Manifest: SHA-256 of every input file, env versions, frozen + campaign
  file SHAs, replay attestation reference, spec file SHA-256.
- D2 contract (Amendment 2): shard_manifest.csv has the fixed typed schema
  d2_truth_model.MANIFEST_COLUMNS with every field populated for every arm
  (no NaN in int/bool columns; empty strings for absent ids); scenario
  identity is the manifest `scenario` code AND every grouping key (arm,
  ratio_g, ratio_rg, phase_draw, amp_scale, dominant_dropped, cadence_code
  — Amendment 3) — the
  dominant-mode-dropout variant is its own scenario and never enters the
  nominal P4 estimator; the P4 eligible denominator is the scenario's
  `n_strata_scheduled` (3 nominal; 1 for single-window sensitivities), and
  the nominal arm-B scenario must hold exactly one replicate per
  (scheduled target, K ∈ {0,1,2}); truth_d2 refuses an unpublished
  (IN_PROGRESS) or undescribed (no generation_manifest.json) generation,
  requires index == manifest == disk id sets, per-shard SHA identity with
  the generation record, A/B ↔ injected_modes bijection with n_modes
  counts, exact null serials 0..999 (production), and a non-production
  generation only under a pilot run manifest; every scored result needs a
  provenance sidecar whose source_id, result SHA, shard SHA, attestation
  SHA and generation id match, else metrics stop; inputs_sha256 carries
  the full chain (truth tables, index, generation manifest, per-shard
  SHAs, generation inputs, run manifest, completion table).
- Pilot rule: run manifests with `pilot: true` (any --limit/--stars-file
  run) yield `prespecified_primary: false` on every P4/P5 row,
  `confirmatory_decision: false`, and `confirmatory_allowed: false` in the
  metrics manifest; a subset run's selection file is SHA-bound
  (`stars_file_sha256`) and must equal the completion-table id set exactly.
- W_g strata guard (Amendment 4): every nominal target's three windows carry
  strictly increasing W_g; the generation records the pool W_g quantiles and
  surface edges; every nominal-B `control_campaign_id` resolves to a control
  shard in the generation.

## Outputs

`generalization/results/<date>_<dataset>/metrics/`: per_star.csv,
completeness_by_class_pass_rule.csv, contingency_complementarity.json,
trigger_rates.csv, ppv.csv (D3), fp_frequency_distribution.csv,
chance_match.json, surfaces/*.csv, sensitivity.csv, attrition.csv,
d2_cluster_completeness.csv + d2_scenario_contrasts.csv (D2: P4 table and
the paired common-draw scenario-vs-nominal-K=1 contrasts),
d2_paired_controls.csv + d2_paired_controls_summary.csv +
d2_control_reuse.csv (Amendment 4), manifest.json,
inputs_sha256.json.
Figures via plot_generalization.py from these CSVs only.
