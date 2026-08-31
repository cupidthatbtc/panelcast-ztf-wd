ADMIT-AS-DESCRIPTIVE

The addition is admissible only as a post-launch arithmetic partition of P3’s observed numerator. P3 itself remains unchanged: rule 1, best pass, all 2,314 `dsct_flag0` stars, and its frozen Wilson interval ([METRICS_SPEC.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:121)). The outside-band component must not be called a “corrected,” “de-aliased,” or alternative P3.

### Exact rule text

> Among all 2,314 D3 `dsct_flag0` roster members, including missing/unusable stars as non-triggers, select stars with `best_status == "confirmed"` under rule 1. Use the finite `best_frequency_per_day` from the frozen best-pass selection. Define `within_solar_diurnal_band` iff
> \[
> f < 4\ {\rm d}^{-1}
> \quad\text{and}\quad
> \min_{k\in\{1,2,3\}}\left|f-k(1.000000\ {\rm d}^{-1})\right|
> \le 0.020000\ {\rm d}^{-1}.
> \]
> Thus the bands are \([0.980,1.020]\), \([1.980,2.020]\), and \([2.980,3.020]\ {\rm d}^{-1}\), with closed endpoints. Every other confirmed negative is `outside_solar_diurnal_band`. Abort rather than classify silently if any confirmed negative lacks a finite best-pass frequency.

No low-frequency-floor term should be added. The low-pass search already starts at the star-specific \(2/T\) ([run_lomb_scargle.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_lomb_scargle.py:58)); floor-adjacent signals are not the same physical family as integer solar-day harmonics.

For \(T\approx2700\) d, the frozen grid step is \(1/(10T)\approx3.70\times10^{-5}\ {\rm d}^{-1}\), and the pipeline alias tolerance is \(1.5/T\approx5.56\times10^{-4}\ {\rm d}^{-1}\) ([lomb_scargle_common.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/lomb_scargle_common.py:14)). The proposed 0.020 tolerance is therefore about 540 grid steps and 36 pipeline tolerances: it is not numerical uncertainty. It is an intentionally broad, pilot-informed descriptive band covering the observed displacement through 2.015/d, rounded outward before full metrics. That data-informed origin is why no inferential claim is admissible.

Report two rows satisfying:

\[
n_{\rm within}+n_{\rm outside}=n_{\rm confirmed},\qquad
\frac{n_{\rm within}}{2314}+\frac{n_{\rm outside}}{2314}=\widehat P3.
\]

Include counts, `rate_of_all_negatives`, and `share_of_confirmed`; include no confidence intervals, tests, acceptance thresholds, or weighting.

### File placement

Do not add rows to `trigger_rates.csv`. Its rule rows are frozen and implemented as such ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1119)).

Use a segregated file generated after the frozen metrics:

`generalization/results/<date>_d3/descriptive_postlaunch/d3_trigger_decomposition.csv`

Suggested columns:

```text
component,rule,pass_basis,n_negative,n_confirmed_total,n_component,
rate_of_all_negatives,share_of_confirmed,band_definition,
analysis_status,prespecified,interval
```

Set `analysis_status=postlaunch_pilot_informed_descriptive`, `prespecified=false`, and `interval=none`. The existing `fp_frequency_distribution.csv` remains the prespecified frequency audit ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1215)).

### Exact disclosure sentence

> Post-launch, pilot-informed descriptive analysis: after inspection of raw, unweighted per-pass statuses from the non-representative 150-star D3 timing pilot, and after the full D3 L-S run had launched but before any full-campaign metric was computed, we fixed the solar-diurnal frequency bands at \(\bigcup_{k=1}^{3}[k-0.020,k+0.020]\ {\rm d}^{-1}\); `d3_trigger_decomposition.csv` is an unweighted arithmetic partition of the frozen rule-1, best-pass D3 negative-class P3 numerator over its unchanged 2,314-star denominator, was not prespecified, carries no interval or confirmatory interpretation, is not used to veto, exclude, or reclassify any trigger, and does not establish that an individual band member is instrumental rather than astrophysical.

This preserves Amendment 4’s prohibition on further hierarchy changes ([G2_FREEZE.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:219)).

Do not apply the decomposition to the census negative trigger rate. Census has no frequency; attaching an L-S frequency to census triggers would create a different cross-method analysis rather than decompose the census numerator.

## Verdict: ADMIT
