Verdict: **not freezable.** The rewrite resolves several round-1 problems—especially terminology, invariant amplitude axes, and sensitivity-range wording—but leaves five blockers and three major issues.

1. **BLOCKER — Frequency estimands remain non-unique.** [Estimands and rules](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:18)

   `correct-frequency fraction` lacks an explicit formula, while `census` and census-only `either` detections have no frequency estimate. D3 headline recovery also alternates between the dominant mode and the full Mo list.

   **Minimal fix:** define
   \(P(DM\mid Y=1,F=1,S_p=1)\) and
   \(P(M\mid D=1,Y=1,F=1,S_p=1)\);
   restrict frequency outcomes to frequency-bearing L-S rules; define separate `direct_dominant` and `direct_any_mode`, with only the former primary for D3.

2. **BLOCKER — Denominators are still selectable.** [Frequency denominator](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:19), [attrition denominator](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:109)

   D3’s 456 Mo joins are called scorable without pass-specific eligibility. This matters: only 10/456 dominant frequencies are ≥24 d⁻¹, so 446 are outside the high-pass range. The eligible-roster analysis also does not say whether unavailable targets are failures or missing.

   **Minimal fix:** define \(S_{ip}\) for D3 and D2; use \(S_{i,\mathrm{best}}=S_{i,\mathrm{low}}\lor S_{i,\mathrm{high}}\); count unavailable eligible targets as \(D=0\), excluding them only from the explicitly usable-light-curve estimand.

3. **BLOCKER — The taxonomy is neither disjoint nor precedence-safe.** [Taxonomy](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:43)

   “Strict first” makes `direct` win before `ambiguous`, but line 53 appears to require ambiguity when a candidate directly matches one mode and harmonically or alias-matches another. Either interpretation is implementable.

   **Minimal fix:** enumerate all `(truth mode, relation)` hits first; assign `ambiguous` if multiple qualifying modes or relations exist; otherwise assign the unique relation. Freeze the numerical \(f_{\rm sid}\), and state whether multiple direct modes are ambiguous.

4. **BLOCKER — The cluster bootstrap is only conditionally defensible and is underspecified.** [Bootstrap](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:78)

   The design has 309 target–window rows but only 119 unique windows; 264 rows reuse a window, some for eight targets. A target-only bootstrap is acceptable only for inference conditional on those frozen windows. It does not represent uncertainty over the 928-window frame. The statistic, missing-replicate rule, interval type, and handling of all-zero/all-one outcomes are also absent.

   **Minimal fix:** state the target-level estimator explicitly; resample the 103 TICs with replacement, carrying every selected window, phase, ladder result, and paired C/L outcome jointly; hold assignments and outputs fixed; use identical draws across scenarios. Declare inference conditional on frozen windows, or use crossed target/window resampling. Prohibit pooled exact McNemar for D2 and use the target-cluster paired-difference bootstrap. Add a boundary-safe interval fallback.

5. **BLOCKER — The “primary family” does not prevent outcome selection.** [Primary family](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:64)

   Rule, pass, and D2 variant are fixed, but endpoint, population, eligible-versus-usable denominator, class, contrast, surface, and claim direction remain selectable.

   **Minimal fix:** enumerate each primary endpoint as a complete tuple: dataset, population, endpoint, denominator, rule, pass, arm/scenario, statistic, direction, and decision criterion. Either make the Gaussian-null criterion the sole confirmatory decision and label everything else descriptive, or control the enumerated family with Holm/joint bootstrap inference.

6. **MAJOR — Effective-sample-size Wilson is unsuitable for weighted D3 PPV.** [Intervals](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:73)

   Positives are exhaustive while negatives are an SRS without replacement. Kish-ESS Wilson does not represent that stratified finite-population design.

   **Minimal fix:** exclude/report `dSct=2` separately; hold exhaustive positives fixed and infer the total triggered negatives using hypergeometric inversion or a finite-population survey bootstrap, then transform to PPV. For the negative-class trigger rate, weights are constant and cancel, so ordinary Wilson on the 2,314 sampled negatives is acceptable, conservatively without an FPC.

7. **MAJOR — The Gaussian-null decision remains exploitable.** [Null criterion](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:34)

   The one-sided interval method and allocation of 1,000 runs across 928 windows are unspecified. “At zero events” also leaves the decision for \(x>0\) undefined.

   **Minimal fix:** freeze uniform-with-replacement window sampling and independent seeds, name the exact one-sided interval, and define acceptance as \(U_{0.95}(x,1000)\le0.005\) for the observed \(x\).

8. **MAJOR — Surface definitions and edge semantics are incomplete.** [Surfaces](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:97)

   The central D3 amplitude edges are sensible: counts are 84, 70, 97, 106, and 51 through the bins below 10 mmag. Above 10 mmag they are 23, 18, 6, and 1, so the 200-mmag split creates a one-star overflow. “Completeness” is also unspecified, exposure-per-night edges are absent, and interval closure/underflow/overflow are undefined.

   **Minimal fix:** name the surface endpoint and D2 target coordinate; freeze exposure edges; define half-open bins with explicit tails. Collapse D3 to a final \([50,\infty)\) bin or declare the existing extreme tail counts-only.

One additional conformance warning: the current implementation does not yet implement the prose. It uses any-mode matching for the headline and pooled weighted-Wilson aggregation, and silently drops missing JSONs: [truth/matching](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:220), [aggregation](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:291), [missing handling](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:475).

**Bottom line:** fix findings 1–5 before freezing. Findings 6–8 are also small enough to close now and would otherwise remain genuine researcher degrees of freedom.
