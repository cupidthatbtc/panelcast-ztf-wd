# METRICS_SPEC — frozen before any campaign Lomb-Scargle run

Implemented by `scripts/generalization/metrics_generalization.py`. Any change
to this file after the first campaign L-S run voids the prespecification and
must be reported as such.

## Inputs

Per-star JSONs from `run_generalization_ls.py` (never only a summary CSV:
`overall_result` collapses the two passes and can report a spuriously low
best pass). For each star and each pass (`low`, `high`) the JSON carries the
best candidate, the 15 stored `top_peaks` (5 zg + 5 zr + 5 multiband), FAPs,
amplitudes, A95 limits, alias flags, and availability. Census rows come from
`build_panels_generic.py` output (D3) or the frozen published census (D1).

## Frequency-match definitions

- Tolerance: `1.5 / baseline_days` per star — the pipeline's own alias/window
  tolerance, adopted verbatim. `baseline_days` from the star JSON.
- `matched_primary`: the pipeline's best candidate frequency within tolerance
  of any truth frequency (D3: Mo+2026 frequencies for that KIC, else the
  dominant; D2: the injected mode list).
- `matched_any_mode`: ANY of the 15 stored top_peaks within tolerance of any
  truth frequency.
- Harmonics: matches at 2f and f/2 are logged separately
  (`matched_harmonic`), never counted in the headline.
- Truth frequencies for D3 stars without Mo+2026 rows: no frequency scoring;
  the star contributes to detection-level completeness only
  (`freq_scorable = False` in the per-star table).

## Detection rules (all four always reported)

1. `confirmed` — headline: blind status == confirmed.
2. `confirmed|candidate` — permissive: status in {confirmed, candidate}.
3. `census` — frozen census flag (any of six ratios >= 2.5).
4. `either` — (1) OR (3): the complementarity number.

## Headline estimands

- **Completeness** (per class × pass × rule):
  P(detected AND matched_primary | labeled positive) for rules 1–2;
  P(census flag | labeled positive) for rule 3; rule 4 uses rule 1's
  frequency requirement on the L-S side.
  Also reported without the frequency requirement (detection-only), to
  decompose "missed" vs "found at wrong frequency".
- **Purity**: P(matched_primary | detected) among labeled positives, and
  among all stars with truth frequencies.
- **FPR** (per rule): P(detected | labeled negative). D3: dSct=0 class
  (upper bound; stated). D2: 1,000 arm-A zero-amplitude nulls (statistical).
  FP frequency distribution plotted for the alias-veto audit; alias-blanking
  rate reported as a diagnostic (expected 0.03–0.15% per star).
- **Intervals**: Wilson 95% on every proportion, inline in every table.
- **Contingency + McNemar** (census vs L-S on positives) per dataset — the
  complementarity claim in quantified form.
- **Completeness surfaces**: (log P, log A_g) and (exposures-per-night,
  log A_g) bins; per-cell Wilson intervals; D3 also vs the amplitude ladder
  strata from the roster.
- **Sensitivity**: every D2 ladder variant (3×3 bandpass × de-dilution
  on/off) and every prespecified D3 subset (crowding, near-saturation,
  safe) reported alongside the nominal; headline quoted as the band across
  the ladder, not a single number.

## Guards

- Assert no campaign census ratio equals 2.5 exactly (the frozen `>=`/`>`
  inconsistency is non-affecting on D1; this keeps it provably so on campaign
  data).
- Assert every input JSON has `complete == true` and both passes; stars with
  unavailable passes are tabulated separately, never dropped silently.
- Manifest: SHA-256 of every input file, env versions, frozen-file SHAs,
  spec version (git blob SHA of this file at run time).

## Outputs

`generalization/results/<date>_<dataset>/metrics/`:
per_star.csv, completeness_by_class_pass_rule.csv, contingency_mcnemar.json,
fpr.csv, fp_frequency_distribution.csv, surfaces/*.csv, sensitivity.csv,
manifest.json. Figures via `plot_generalization.py` from these CSVs only.
