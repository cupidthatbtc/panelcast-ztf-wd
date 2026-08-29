# METRICS_SPEC — frozen before any campaign Lomb-Scargle run

Implemented by `scripts/generalization/metrics_generalization.py`. Any change
after the first campaign L-S run voids the prespecification and must be
reported as such. Revised at G1 (2026-08-28) in response to the sol review
panel — see `generalization/reviews/G1/RESPONSE.md`; frozen at G2.

## Estimand vocabulary (names are binding)

The campaign does NOT produce a single pooled "selection function". It
produces three separate response assessments with these named estimands:

- **detection completeness** — P(rule fires | labeled positive), per dataset,
  class, pass rule. D3 denominator: all 610 dSct=1 (external labels).
  D2 denominator: injection targets (synthetic positives — reported as
  *conditional injection-recovery efficiency of the search stage*, never as
  real-sky completeness).
- **frequency-recovery completeness** — P(rule fires AND strict frequency
  match | labeled positive AND frequency-scorable). D3 frequency-scorable:
  the 456/610 with Mo+2026 rows (reported as "Mo-join-conditioned"; joined
  vs unjoined covariates compared). D2: targets with >=1 injected mode
  inside the pass's search bounds after sinc rejection (S_p = 1).
  The missed-vs-wrong-frequency decomposition uses ONLY matching
  denominators (both conditional on scorable/S_p = 1).
- **correct-frequency fraction among detected positives** — what an earlier
  draft called "purity"; it is not positive predictive value and is never
  labeled purity. Class-level PPV is reported for D3 only, with sampling
  weights (negatives carry weight pool/sample = 7292/2314), as a
  prevalence-weighted estimate with the contaminated-negative caveat.
- **negative-class trigger rate** — P(rule fires | Murphy dSct=0). NOT called
  FPR: the class contains non-dSct variables; reported with sampling weights
  and, after adjudication of triggered negatives (W4), split into
  "plausible real variable" vs "unexplained".
- **Gaussian-null false-alarm rate (FPR_Gaussian)** — P(confirmed | arm-A
  zero-amplitude null), n = 1000 over the 928-window frame (windows repeat,
  seeds do not). Acceptance criterion (preregistered): one-sided 95% upper
  bound <= 0.5% at zero events. The FP frequency-distribution/alias audit is
  descriptive only below 10 events.
- **native trigger rate of the template pool** — P(confirmed | paired
  uninjected control window), the 95-prefix arm. Context for D2 recovery,
  not an FPR.

## Frequency-match taxonomy (disjoint labels, strict first)

Tolerance: 1.5 / baseline_days per star (the pipeline's own convention).
For each detected candidate, in precedence order against the truth list
(D3: Mo frequencies for that KIC; D2: injected modes):

1. `direct` — within tolerance of a truth frequency;
2. `harmonic` — within tolerance of 2f or f/2 of a truth frequency;
3. `window_alias` — within tolerance of |f_truth ± k f_sid|, k = 1, 2
   (sidereal-day family, the pipeline's own alias model);
4. `ambiguous` — matches >1 truth frequency class above;
5. `unmatched`.

Headline frequency recovery counts `direct` only, scored against the
pipeline's BEST candidate (`matched_primary`). D3's primary truth frequency
is the DOMINANT Mo mode; any-mode direct matches are a secondary column.
`matched_any_mode` over the 15 stored top_peaks is diagnostic only.
Chance-match calibration: truth lists permuted across stars (frozen seed,
100 permutations) → accidental direct-match rate reported beside every
frequency-recovery table.

## Detection rules (all four always reported; PRIMARY = rule 1)

1. `confirmed` (headline), 2. `confirmed|candidate`, 3. `census`
(any of six frozen ratios >= 2.5), 4. `either` (1 OR 3).
Primary claim family (preregistered): rule 1, pass = best of {low, high}
(the frozen `overall_result` ordering), nominal D2 variant (1.7/0.80,
de-dilution off, arm B), per dataset. Everything else is labeled a
pointwise descriptive sensitivity analysis; no simultaneous-coverage claim.

## Units of analysis and intervals

- D1/D3: the star is the unit; Wilson 95% intervals on independent per-star
  proportions; weighted estimates use the effective-sample-size Wilson
  approximation.
- D2: the TESS target is the CLUSTER. K=3 template windows and ladder/phase
  variants are correlated replicates, never pooled as independent trials.
  Per-stratum (10/50/90th percentile window) proportions are reported
  separately; aggregates are equal-weight standardized means over targets
  with cluster bootstrap intervals (resample targets, keep all replicates;
  B = 2000, frozen seed). Ladder results: nominal is primary; the min-max
  across the 3x3 grid is a "prespecified finite-grid sensitivity range",
  never a confidence band; endpoint scenarios identified.

## Complementarity (census vs L-S)

Primary table (per dataset, on labeled positives with both methods
available): C = census flag; L = rule-1 detection (detection-only, no
frequency requirement — symmetric margins). Report the full 2x2, both
discordant fractions, union completeness, and incremental yields
P(C=1,L=0), P(C=0,L=1) with intervals (Wilson for D3/D1; cluster bootstrap
for D2). Exact McNemar is SECONDARY (marginal-homogeneity only; it does not
measure complementarity).

## Surfaces

Completeness on (log P, log A) and (median exposures-per-night, log A).
Amplitude axis is INVARIANT per dataset: D3 = historical Kepler-band
dominant amplitude (mmag; explicitly non-contemporaneous, not a ZTF-g
threshold); D2 = published TESS amplitude (ppt) for cross-variant surfaces,
nominal injected A_g for the nominal-only surface. Bin edges frozen here:
log P edges at P = {100 s, 200 s, 500 s, 1000 s, 2000 s, 0.05 d, 0.2 d,
1 d, 10 d, 100 d}; amplitude edges {0.5, 1, 2, 5, 10, 20, 50, 200} mmag
(D3) / {0.5, 2, 5, 10, 30, 100} ppt (D2); cells below 5 stars reported as
counts only, no proportion.

## Eligibility and attrition

Two denominators, both always reported: P(rule | eligible roster target) and
P(rule | usable light curve) (frozen QC crossmatch passed, both passes
available). A full attrition table (roster -> fetched -> crossmatched ->
QC-passed -> both-passes-complete) by class, amplitude stratum, and
magnitude accompanies every dataset. Unavailable passes are never silently
dropped.

## Guards

- Assert no campaign census ratio equals 2.5 exactly.
- Assert every scored JSON has complete == true; both passes present.
- Manifest: SHA-256 of every input file, env versions, frozen + campaign
  file SHAs (frozen_api.campaign_file_shas), replay attestation reference,
  spec git blob SHA.

## Outputs

`generalization/results/<date>_<dataset>/metrics/`: per_star.csv,
completeness_by_class_pass_rule.csv, contingency_complementarity.json,
trigger_rates.csv, fp_frequency_distribution.csv, chance_match.csv,
surfaces/*.csv, sensitivity.csv, attrition.csv, manifest.json.
Figures via plot_generalization.py from these CSVs only.
