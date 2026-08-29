## Round-3 outcome

**Not freezable.** Of the 20 items reviewed:

- **13 RESOLVED**
- **5 PARTIAL**
- **2 UNRESOLVED**

I credited only requirements in the revised plan/spec. `UNRESOLVED` means the specific residual identified in round 2 was not added, even if earlier improvements remain.

### Audit of the 12 round-2 PARTIALs

| Item | Verdict | Revised-document evidence |
|---|---|---|
| **1. D2 template circularity** | **RESOLVED** | Templates now come from all 928 stars, and Gaussian nulls cycle over the same sorted frame ([Plan:164](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:164), [Plan:183](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:183), [Metrics:51](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:51)). The 510-window reference is historical only. |
| **2. D3 independence qualification** | **RESOLVED** | The realized crossmatch and ambiguity-adjudication file must be committed before any campaign L-S run ([Plan:119](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:119)). |
| **4. TESS sinc algebra** | **RESOLVED** | Nyquist \(P=240\) s and first integration null \(P=120\) s are distinguished; the cutoff and 20-s/120-s cadence rule are executable ([Plan:144](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:144), [Plan:151](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:151), [Plan:153](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:153)). |
| **5. D2 phases and amplitude variability** | **PARTIAL** | Per-mode independent phases are stated ([Plan:160](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:160)), but later phases are “drawn once per star” ([Plan:205](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:205)). “Shared across all variants” also conflicts with two phase-draw variants ([Plan:194](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:194)). Amplitude stationarity is a plan “stretch” but a binding spec axis ([Plan:195](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:195), [Metrics:141](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:141)). |
| **7. Gaussian-null interpretation** | **RESOLVED** | `FPR_Gaussian` is tied to 1,000 Gaussian nulls over the 928-window allocation; real controls are separately labeled contextual native-trigger rates ([Metrics:51](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:51), [Metrics:60](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:60)). |
| **8. Correlated D2 replicates** | **RESOLVED by scope restriction** | Inference is explicitly conditional on frozen windows, must report window reuse, and does not represent the 928-window frame. Targets are resampled with all replicates jointly ([Metrics:127](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:127), [Metrics:131](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:131)). |
| **9. `dSct=0` is not FPR** | **RESOLVED** | Both the D3 section and risk register now use only negative-class trigger-rate language ([Plan:132](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:132), [Plan:269](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:269), [Metrics:47](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:47)). |
| **11. 456/610 amplitude-join bias** | **UNRESOLVED** | The spec retains only the Mo-conditioned label and joined/unjoined covariate table ([Metrics:25](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:25)); no MNAR limitation or sensitivity bounds appear, while the curve remains the headline D3 deliverable ([Plan:121](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:121)). The disposition’s claim at [Response:87](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2/RESPONSE.md:87) is not implemented. |
| **14. \(g\ge13.2\) truncation** | **PARTIAL** | The cut and `amp_unknown`, join, period, \(T_{\rm eff}\), and crowding attrition dimensions are present ([Plan:113](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:113), [Metrics:174](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:174)). The requested color dimension remains absent; \(T_{\rm eff}\) is not declared its substitute. |
| **15. Negative sampling** | **UNRESOLVED** | The documents retain valid frozen-seed SRS and weights ([Plan:113](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:113)), but the promised sampled-versus-full-frame balance diagnostic is absent from both the required analyses and outputs ([Metrics:176](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:176), [Metrics:194](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:194)). |
| **17. “Purity” misnomer** | **RESOLVED** | The quantity is now precisely a frame-specific weighted label PPV; `dSct=2` is excluded and transfer to other prevalences prohibited ([Metrics:41](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:41)). |
| **18. Turn-on prespecification** | **RESOLVED** | Scalar coordinates, half-open bins, under/overflow, minimum cell size, and prohibitions on smoothing, monotonic fitting, and interpolation are all specified ([Metrics:158](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:158), [Metrics:165](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:165)). |

### Audit of objections 21–28

| Item | Verdict | Revised-document evidence |
|---|---|---|
| **21. Multimode surface coordinates** | **RESOLVED** | Unit is the star; D3 uses the dominant Mo mode and D2 the largest-amplitude retained injected mode ([Metrics:160](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:160)). |
| **22. Match taxonomy** | **RESOLVED** | All truth-mode/relation predicates are evaluated before classification; multi-relation hits become ambiguous ([Metrics:80](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:80)). |
| **23. D2 window-population estimand** | **PARTIAL** | The scope is correctly restricted to a conditional 103-target scenario mix, not the 928-window frame ([Metrics:127](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:127)). But P4 does not explicitly assign \(1/3\) weight to each K stratum or define failed/missing-stratum behavior under eligible versus usable denominators ([Metrics:112](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:112), [Metrics:131](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:131)). |
| **24. Template matching** | **PARTIAL** | Thresholds, ordering, and percentile-index selection are added ([Plan:170](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:170)). However, “widened to 0.5 … else the 9 nearest” does not unambiguously state the post-0.5 fallback, ninth-nearest magnitude ties, or the half-tie convention for `round(q(n−1))`. |
| **25. Bandpass justification** | **RESOLVED** | The blackbody result \(1.43\) is consistently identified with the approximate 1.4 low rung; 1.7 is the adopted grid midpoint ([Plan:155](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:155), [Plan:207](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:207)). |
| **26. Common-subset sensitivity** | **RESOLVED** | All contrasts recompute nominal on the same median-window subset using common bootstrap draws ([Plan:193](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:193), [Metrics:141](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:141)). |
| **27. D3 PPV interval** | **PARTIAL** | Positives are correctly fixed and negatives resampled ([Metrics:41](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:41)). But resampling the 2,314 negatives with replacement is an ordinary empirical bootstrap, not an SRS-without-replacement design bootstrap; it omits the finite-population correction despite a 31.7% sampling fraction ([Metrics:44](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:44), [Metrics:63](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:63)). |
| **28. Gaussian-null acceptance** | **RESOLVED** | Exact one-sided Clopper–Pearson at observed \(x\) and the full acceptance rule are now specified ([Metrics:51](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:51), [Metrics:116](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:116)). |

## New contradictions introduced by v3

1. **Phase variants versus phase sharing.** Per-mode phases are shared across “all variants,” yet two phase-draw variants are scheduled; the later “once per star” wording adds a second conflict ([Plan:160](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:160), [Plan:194](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:194), [Plan:205](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:205)).

2. **Amplitude stationarity is optional and binding simultaneously.** It is outside the core as a stretch addition in the plan but part of the binding sensitivity protocol in the spec ([Plan:190](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:190), [Metrics:141](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:141)).

3. **P4 is called a “complete tuple” but is incomplete.** It omits an explicit K-stratum combination formula and denominator/failure behavior ([Metrics:104](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:104), [Metrics:112](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:112)).

4. **D3 surface denominator conflict.** Detection completeness is defined over all 610 positives, but the D3 surface coordinate requires a dominant Mo mode available for only 456; no surface rule is given for the other 154 ([Metrics:13](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13), [Metrics:25](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:25), [Metrics:160](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:160)).

5. **Arm A is both diagnostic and confirmatory.** The plan calls arm A diagnostic, while P5 makes its null endpoint the sole confirmatory decision ([Plan:183](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:183), [Metrics:116](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:116)). Presumably positive arm-A injections are diagnostic and arm-A nulls confirmatory, but that distinction is unstated.

6. **D1 surface scope appears accidentally restored.** Surface coordinates are defined only for D2/D3, while the amplitude bins say “D3/D1” ([Metrics:160](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:160), [Metrics:168](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:168)).

## Final verdict and minimal blockers

**Not freezable.** The minimal blocker list is:

1. Freeze the complete phase protocol—one phase per mode, draw-specific deterministic seeds, and exactly which variants share phases—and make amplitude stationarity either mandatory or explicitly nonbinding.
2. Define P4 algebraically, including \(1/3\) K-stratum weights, eligible/usable versions, and missing-stratum handling.
3. Make template selection a total deterministic algorithm, including fallback, magnitude ties, and rounding convention.
4. Replace the D3 PPV bootstrap with an SRSWOR/finite-population-valid variance procedure.
5. Resolve the D3 Mo-join scope: define the surface denominator for the 154 unjoined positives and add the promised explicit MNAR limitation/sensitivity treatment.

The missing color and negative-sample balance diagnostics remain substantive deficiencies, but they are not independently execution-blocking once the valid SRS design is retained.
