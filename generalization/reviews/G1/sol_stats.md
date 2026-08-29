Verdict: not ready to freeze. The largest problems are the misuse of “purity,” undefined D2 sampling units, invalid pooled Wilson/McNemar inference, and an FPR experiment that measures only an idealized Gaussian null.

1. **BLOCKER — “Purity” is not defined as purity.**  
   [METRICS_SPEC.md:46](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:46) defines \(P(\text{matched primary}\mid\text{detected})\) among positives. That is frequency fidelity among detected positives, not positive predictive value. It excludes labeled negatives and therefore cannot measure contamination. “All stars with truth frequencies” does not fix this because truth-frequency availability is itself selected. Census-only detections also have no meaningful frequency-match purity.

   Minimal fix: rename the existing quantity “correct-frequency fraction among detected positives.” Define class purity as \(P(Y=1\mid D=1)\), and frequency-correct purity as \(P(Y=1,M=1\mid D=1)\). For D3, use inclusion weights because positives are taken exhaustively while negatives are sampled. For D2, where prevalence is artificial, report PPV as a function of assumed prevalence rather than mixing an arbitrary number of injections and nulls.

2. **BLOCKER — The frequency-completeness denominator is contradictory.**  
   The formula conditions only on “labeled positive,” while unscorable D3 positives are excluded from frequency scoring ([METRICS_SPEC.md:27](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:27), [METRICS_SPEC.md:40](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:40)). Detection-only completeness over all positives therefore cannot be subtracted from frequency completeness to decompose “missed” versus “wrong frequency”: the denominators differ.

   Minimal fix: define \(S_{ip}\) as having at least one eligible truth mode inside pass \(p\), after all mode rejection and search-bound rules. Report:

   \[
   P(DM\mid Y=1,S_p=1),\quad P(D\mid Y=1,S_p=1),\quad P(D\mid Y=1).
   \]

   Only the first two form the proposed decomposition. Also resolve “Mo frequencies … else the dominant” versus “no Mo row means unscorable.”

3. **MAJOR — Direct, harmonic, and window-alias matches are not mutually exclusive.**  
   A candidate can be within tolerance of truth mode \(f_k\) while also lying near \(2f_j\), \(f_j/2\), or a sampling-window alias of another injected mode. The specification says harmonics are logged separately but gives no precedence for such overlaps and does not define window-alias matching at all ([METRICS_SPEC.md:18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:18)). With many Mo/Romero modes, “match any truth frequency” also has a star-dependent chance-match opportunity.

   Minimal fix: create disjoint labels—strict direct, harmonic, window alias, and ambiguous—and exclude ambiguous cases from strict headline recovery. Estimate accidental matching by assigning the real truth lists to null/permuted stars. Report the number of eligible modes and the fraction of the searched frequency range covered by match windows. Keep `matched_any_mode` diagnostic rather than inferential.

4. **BLOCKER — The D2 unit of analysis is unspecified.**  
   Each truth target supplies three deliberately chosen window conditions ([GENERALIZATION_PLAN.md:123](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:123)). These are not three independent DAVs and are not a random sample of windows. Pooling them implicitly estimates an equal-weight target×window-stratum quantity, but that estimand is never stated.

   Minimal fix: make the truth target the cluster. Report the 10th-, 50th-, and 90th-percentile window strata separately, then define any aggregate explicitly as their equal-weight standardized mean. State missing-template handling and whether template windows can be reused across targets.

5. **BLOCKER — Pooled Wilson intervals create pseudoreplication.**  
   Wilson intervals assume independent Bernoulli observations. The three D2 outcomes share frequencies, amplitudes, and other target-level difficulty. Treating \(3N\) injections as independent understates uncertainty; with intracluster correlation \(\rho\), the design effect is \(1+2\rho\). Reused template windows would add cross-target dependence. The same issue applies across ladder variants.

   Minimal fix: use a target-cluster bootstrap that preserves all three templates and all sensitivity scenarios in each resample. Alternatively, use one observation per target within each window stratum. Wilson may remain for genuinely independent one-row-per-star proportions, but not for pooled D2, fractional target averages, or weighted estimates.

6. **BLOCKER — The McNemar table is not specified.**  
   “Census vs L-S on positives” leaves open the L-S margin: confirmed or confirmed|candidate; detection-only or frequency-correct; low pass, high pass, or their OR; nominal or ladder scenario; and which D2 template/arm ([METRICS_SPEC.md:53](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:53)).

   Minimal fix: preregister one primary \(2\times2\) table. For example, on positives with both methods available:

   - \(C=1\): census flagged.
   - \(L=1\): confirmed L-S detection-only under an explicitly defined pass rule.

   State \(n_{10}=C\text{-only}\) and \(n_{01}=L\text{-only}\). Use exact McNemar for small independent-star datasets. For D2, analyze each template stratum separately or use a target-cluster paired-difference test/bootstrap; pooled exact McNemar is invalid.

7. **MAJOR — McNemar does not test “complementarity.”**  
   McNemar tests equality of paired marginal detection probabilities, \(P(C=1,L=0)=P(C=0,L=1)\). Strong two-way complementarity can produce \(p=1\), while a significant result can reflect one method simply dominating the other.

   Minimal fix: report both discordant fractions, union completeness, and incremental yields \(P(C=1,L=0)\) and \(P(C=0,L=1)\), each with appropriate intervals. Use McNemar only if marginal equality is a substantive secondary hypothesis.

8. **MAJOR — Four rules plus passes, classes, surfaces, and scenarios form an undeclared multiplicity family.**  
   Reporting all four rules reduces selective omission, but separate 95% Wilson intervals remain pointwise, not simultaneous. Rule 4 is a deterministic union rather than an independent detector. The larger multiplicity comes from rules × passes × classes × datasets × surfaces × 18 D2 scenarios.

   Minimal fix: designate one primary rule, pass construction, class, arm, and scenario per main claim. Label all other estimates as pointwise descriptive sensitivity analyses. If significance or acceptance is based on multiple contrasts, preregister the family and use Holm or joint bootstrap intervals.

9. **MAJOR — The D2 “band” is not statistically coherent as currently worded.**  
   The min–max over a finite grid is a sensitivity range, not a confidence band and not a single population estimand. It is also unclear whether “across the ladder” means nine bandpass combinations or all 18 combinations including de-dilution ([METRICS_SPEC.md:58](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:58)). Selected extrema have additional sampling variability.

   Minimal fix: retain the nominal 1.7/0.80, de-dilution-off estimate as primary. Call the remainder a “prespecified finite-grid sensitivity range,” identify the scenarios attaining each endpoint, and keep de-dilution as a separate axis. If the envelope itself is inferential, bootstrap all scenarios jointly by target and derive uncertainty for the extrema.

10. **MAJOR — Ladder-specific amplitude surfaces can compare different stars.**  
    \(A_g\) changes with \(A_g/A_{\rm TESS}\) and de-dilution, so stars move between amplitude bins across scenarios. A per-bin “band” would therefore envelope estimates for different underlying compositions, not sensitivity of one fixed stratum.

    Minimal fix: bin on an invariant quantity such as published TESS amplitude or nominal \(A_g\), or show a separate surface for each scenario without taking cellwise ranges.

11. **BLOCKER — The 1,000-null design does not estimate operational D2 FPR.**  
    Arm-A nulls estimate false alarms under synthetic Gaussian noise on the chosen window distribution—not under real ZTF heteroskedasticity, correlations, outliers, or systematics ([GENERALIZATION_PLAN.md:128](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:128)). Calling arm-B nulls tautological correctly recognizes that selecting templates because they were previously “not detected” conditions on the outcome. The sampling frame for “1,000 distinct windows” is also unexplained relative to the 510-star template frame.

    Minimal fix: label the result \(FPR_{\text{Gaussian}}\). Add an independently selected real-noise null set chosen without reference to frozen-pipeline detection, or a prespecified block/per-night randomization that preserves real noise structure. Define the window sampling frame, reuse, stratification, and weights. D3’s dSct=0 result should remain explicitly an upper bound, not be pooled with this quantity.

12. **MAJOR — \(n=1000\) is not tied to an acceptance threshold and cannot support the alias audit.**  
    With zero events, the stated two-sided 95% Wilson upper bound is about 0.38%; that is correct, but only useful if approximately 0.4% is the preregistered acceptable limit. It cannot establish FPR below 0.1%. At an expected alias-blanking rate of 0.03–0.15%, 1,000 nulls yield only 0.3–1.5 expected events, far too few to estimate that rate or an FP frequency distribution.

    Minimal fix: specify the maximum acceptable FPR and size the null experiment to its one-sided upper-bound criterion, including any multiplicity adjustment across primary rules/passes. Treat the alias-frequency audit as unavailable below a minimum event count or run a much larger dedicated null calibration.

The cleanest repair is to freeze explicit target-level indicator formulas first, then replace “Wilson everywhere” with design-aware inference and sharply separate nominal estimates, finite-grid sensitivity ranges, and operational versus Gaussian-null FPR.
