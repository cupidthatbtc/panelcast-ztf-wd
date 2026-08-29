## Outcome

Not freezable. Of the 20 round-1 objections, I find **8 RESOLVED and 12 PARTIAL**. Several partial dispositions retain blocker-level contradictions. I credit only requirements actually present in the revised plan/spec, not assertions in `RESPONSE.md`.

For items 1–20, `BLOCKER` corresponds to the former `REJECT-LEVEL`.

## Round-1 disposition audit

1. **BLOCKER — PARTIAL: D2 template circularity.**  
   The primary window pool is now stated to include all 928 stars, with paired uninjected controls ([Plan:150](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:150)). But the arms section still says the Gaussian nulls use the 510 previously non-detected windows and, worse, that arm-B templates “ARE the not-detected set” ([Plan:163](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:163)). Those are mutually incompatible operative definitions. The positive-injection fix is present, but the design is not unambiguous enough to execute.

2. **MAJOR — PARTIAL: qualification of D3 independence.**  
   The revisions consistently call D3 “externally labeled” rather than treating Murphy and Mo as independent catalogs ([Plan:22](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:22), [Plan:99](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:99)). However, the claimed pre-outcome freeze of realized crossmatches and ambiguity resolutions is absent. The plan freezes the crossmatch procedure, not the resulting mapping or an ambiguity adjudication file ([Plan:120](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:120)).

3. **BLOCKER — RESOLVED: D2 is not independently labeled validation.**  
   D2 is explicitly classified as conditional injection–recovery, not real-sky completeness or an independently labeled sample ([Plan:19](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:19), [Metrics:13](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13)). The slip rule now assigns the external-validation condition solely to D3 ([Plan:228](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:228)).

4. **BLOCKER — PARTIAL: TESS sinc algebra.**  
   The threshold is correctly revised to approximately 160 s for \(|\mathrm{sinc}|=0.3\), and 197 s is correctly identified as the 0.5 point ([Plan:178](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:178)). But the truth-model section still says every \(P<240\) s mode is both super-Nyquist “AND past the first sinc null” ([Plan:138](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:138)). The first null is at \(P=T=120\) s; periods from 120–240 s are not past it. The text still conflates the Nyquist boundary with the integration null. The exact precedence between 20-s and 120-s solutions is also only “prefer,” not algorithmically specified ([Plan:141](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:141)).

5. **BLOCKER — PARTIAL: D2 phases and temporal amplitude variability.**  
   Multiple deterministic phase draws, cross-band sharing, and target-cluster inference are now present ([Plan:175](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:175), [Metrics:78](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:78)). But “drawn once per star” does not state that every mode receives an independent phase ([Plan:181](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:181)). More importantly, the requested temporal-amplitude scaling sensitivity axis is absent from the complete run matrix. Extra phase draws do not address nonstationary DAV amplitudes.

6. **BLOCKER — RESOLVED: real timestamps are not real-sky completeness.**  
   Both documents bind D2 to “conditional injection-recovery efficiency of the search stage” and expressly prohibit a real-sky completeness interpretation ([Plan:19](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:19), [Metrics:15](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:15)).

7. **MAJOR — PARTIAL: Gaussian-null interpretation.**  
   The metric is correctly renamed `FPR_Gaussian`, and real-window controls are described only as context ([Metrics:34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:34)). But the plan still calls it simply “FPR” and uses the 510 non-triggering windows, while the spec declares a 928-window frame ([Plan:163](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:163)). Until the frame is reconciled, even the conditional Gaussian-null estimand is undefined.

8. **MAJOR — PARTIAL: correlated D2 replicates.**  
   Ordinary pooled Wilson intervals have been removed; targets are clusters and a 2,000-replicate target bootstrap is specified ([Metrics:73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:73)). However, windows can repeat across targets ([Plan:163](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:163)), creating cross-target dependence that a target-only bootstrap does not preserve. There is no two-stage/cross-classified window bootstrap and no required reporting of unique target and window counts.

9. **BLOCKER — PARTIAL: `dSct=0` is not FPR.**  
   The substantive D3 section correctly calls it a negative-class trigger rate and requires adjudication ([Plan:126](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:126), [Metrics:30](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:30)). But the risk register still says “FPR an upper bound” ([Plan:243](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:243)). That is precisely the invalid upper-bound claim rejected in round 1.

10. **MAJOR — RESOLVED: any-mode multiple-opportunity matching.**  
    Dominant-mode recovery is now primary, any-mode recovery secondary, and a 100-permutation chance-match calibration is required ([Metrics:56](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:56)). A separate defect in the new taxonomy appears below as objection 22.

11. **BLOCKER — PARTIAL: 456/610 amplitude-join bias.**  
    The frequency and amplitude analyses are correctly labeled Mo-join-conditioned, with joined/unjoined covariate comparison ([Metrics:18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:18)). But there are no sensitivity bounds and no explicit missing-not-at-random limitation. Despite that, the joined-sample turn-on curve remains the “headline D3 deliverable” ([Plan:116](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:116)). Scope correction helps, but the central curve remains vulnerable to unquantified selection bias.

12. **MAJOR — RESOLVED: inconsistent frequency denominator.**  
    Detection completeness uses all 610 positives; frequency recovery uses only the 456 Mo-covered positives; decompositions use matching denominators ([Metrics:13](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13), [Metrics:18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:18)).

13. **MAJOR — RESOLVED: Kepler amplitude is not \(A_g\).**  
    D3’s axis is explicitly “historical Kepler-band dominant amplitude,” non-contemporaneous and not interpretable as a ZTF-\(g\) threshold ([Metrics:99](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:99)).

14. **MAJOR — PARTIAL: \(g\ge13.2\) truncation.**  
    The source is now Murphy/KIC \(g\), and D3 claims are described as magnitude-restricted ([Plan:110](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:110)). But the required attrition dimensions are incomplete: the spec requires class, amplitude stratum, and magnitude only—not join status, period, color, and crowding ([Metrics:109](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:109)). It also does not explicitly freeze the cut before viewing all ZTF outcomes. An amplitude-stratified attrition table is undefined for the 154 stars without amplitudes unless a missing-amplitude stratum is added.

15. **MAJOR — PARTIAL: negative sampling.**  
    KIC-order stride sampling has been replaced by frozen-seed simple random sampling with known weights ([Plan:110](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:110)). That removes the deterministic-order bias. But no balance criterion or diagnostic is specified for magnitude, color, position, crowding, or coverage, as round 1 requested. The resulting probability sample is defensible, but the full disposition is not implemented.

16. **BLOCKER — RESOLVED: unavailable cases.**  
    Eligible-roster and usable-light-curve denominators are both mandatory, with explicit acquisition-to-output attrition and no silent dropping ([Metrics:109](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:109)).

17. **MAJOR — PARTIAL: “purity” misnomer.**  
    Frequency agreement is correctly renamed “correct-frequency fraction among detected positives” ([Metrics:25](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:25)). But the revision introduces a D3 “class-level PPV” without defining what class the generic variability rule predicts or how `dSct=2` is treated. Weighting a contaminated/nonparallel negative class does not by itself establish pipeline PPV. The safe quantity is the weighted fraction of triggered roster members labeled `dSct=1`, not generic purity or PPV.

18. **MAJOR — PARTIAL: turn-on prespecification.**  
    Fixed edges, a five-star minimum, cluster-aware D2 intervals, and separation of sensitivity ranges from confidence intervals are now specified ([Metrics:97](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:97)). Missing pieces remain: treatment of underflow/overflow values, an explicit prohibition or definition of smoothing/monotonic fitting, and a scalar period/amplitude rule for multimode stars. The last issue is blocker-level and detailed below.

19. **MAJOR — RESOLVED: McNemar and complementarity.**  
    The full symmetric detection-only \(2\times2\), incremental yields, and intervals are primary; McNemar is explicitly secondary and limited to marginal homogeneity ([Metrics:87](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:87)).

20. **BLOCKER — RESOLVED: no pooled selection function.**  
    The plan and spec require three separate response assessments and prohibit pooling ([Plan:15](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:15), [Metrics:8](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:8)). The revised slip rule is consistent with that restriction.

## New objections

21. **BLOCKER — Multimode surfaces have no defined unit or scalar coordinates.**  
    The surface specification requires one \((P,A)\) location per observation but never says how a multimode D3 or D2 target is assigned a period and amplitude ([Metrics:97](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:97)). D3 could plausibly use the dominant mode, but this is unstated; D2 has multiple injected modes and only a target-level outcome. Expanding one target into multiple mode rows would change the unit of analysis and require clustered/multivariate scoring. The headline turn-on estimand cannot be implemented uniquely.

22. **MAJOR — The new disjoint match taxonomy is logically inconsistent.**  
    `ambiguous` is fourth in precedence but is defined as matching more than one earlier class ([Metrics:43](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:43)). A sequential implementation will already assign `direct`, `harmonic`, or `window_alias`, making `ambiguous` unreachable. All match predicates must be evaluated first; ambiguity must then take precedence whenever multiple truth modes/classes match.

23. **BLOCKER — D2 lacks a template-window population estimand.**  
    The design selects one window at each of three exposure-density quantiles per target ([Plan:150](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:150)), while the spec says only that aggregates are equal-weight means over targets ([Metrics:78](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:78)). It never defines weighting across the three window strata or the population to which the aggregate refers. Equal weighting would describe an artificial 1/3–1/3–1/3 scenario distribution, not the 928-window frame.

24. **MAJOR — Template matching remains underprespecified.**  
    “\(|\Delta g|\le0.25\), widened when thin” gives no definition of thinness, widening schedule, maximum width, fallback, percentile interpolation, or tie-breaking ([Plan:152](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:152)). That is substantial analyst discretion in a supposedly frozen design.

25. **MAJOR — The bandpass justification contradicts itself.**  
    The nominal \(A_g/A_{\rm TESS}=1.7\) is first attributed to the blackbody derivative ([Plan:144](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:144)); later the same derivative is said to produce 1.43, the low rung ([Plan:182](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:182)). The grid itself uses 1.4, not 1.43. The exact implemented constants and rationale must be reconciled before shard generation.

26. **MAJOR — Sensitivity contrasts are confounded by unequal window designs.**  
    Nominal D2 uses all three windows, whereas nonnominal bandpass and extra-phase runs use only the median window ([Plan:169](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:169)). The spec’s min–max sensitivity range does not require the nominal comparison to be recomputed on that same median-window subset ([Metrics:82](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:82)). Without a common-subset rule, differences can reflect window composition rather than bandpass or phase.

27. **MAJOR — Weighted Wilson intervals are not appropriate for the D3 sampling design.**  
    The negative sample is SRS without replacement at roughly 31.7%, positives are a census, and PPV is a weighted ratio. The proposed effective-sample-size Wilson approximation ([Metrics:73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:73)) does not encode the finite-population correction or the two-component census/sample variance. Use a design-based variance or bootstrap respecting the negative SRS and fixed positive census.

28. **MAJOR — The Gaussian-null acceptance rule is incomplete.**  
    The spec gives “one-sided 95% upper bound \(\le0.5\%\) at zero events” but does not name the interval construction or specify the decision for one or more events ([Metrics:34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:34)). Different one-sided procedures yield different limits. The rule must state the method and apply to the observed event count, not merely the zero-event scenario.

## Verdict

**No—the design is not freezable for execution.** The minimum freeze blockers are:

- reconcile the 928-window versus 510-nontriggering D2 definitions;
- remove the remaining false `dSct=0` FPR-upper-bound claim;
- correct the Nyquist/null language and fully specify 20-s/120-s truth precedence;
- define independent per-mode phases and the temporal-amplitude sensitivity;
- define scalar multimode surface coordinates;
- define the D2 target/window estimand and window-stratum weights;
- make match ambiguity executable;
- freeze common-subset sensitivity comparisons and valid interval procedures.

Running now would force implementers to make consequential choices not fixed by the documents.
