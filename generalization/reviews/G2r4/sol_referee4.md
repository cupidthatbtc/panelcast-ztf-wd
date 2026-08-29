The cited `G2r3/RESPONSE.md` is absent; I verified against the round-3 verdict and current documents.

### Five minimal blockers

1. **UNRESOLVED — Phase/amplitude protocol:** phase assignment is now deterministic, but amplitude stationarity remains a “stretch” in the plan while included in the binding sensitivity protocol ([Plan:161](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:161), [Plan:202](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:202), [Spec:155](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:155)).
2. **UNRESOLVED — P4 algebra:** partial missing strata and eligible-roster zeros are defined, but \(K_t=\varnothing\) leaves \(1/|K_t|\) undefined while the outer denominator remains 103 ([Spec:122](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:122)).
3. **RESOLVED — Template selection:** fallback, magnitude ties, total ordering, and round-half-even percentile indices are deterministic ([Plan:172](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:172)).
4. **RESOLVED — D3 PPV interval:** the bootstrap now fixes census positives and applies the SRSWOR finite-population correction to negative-sample bootstrap deviations ([Spec:49](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:49)).
5. **RESOLVED — D3 Mo-join scope:** MNAR is explicit, frequency recovery is Mo-conditioned, joined/unjoined comparison is mandatory, and detection retains all 610 via `amp_unknown` ([Spec:36](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:36), [Spec:174](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:174)).

### Six new contradictions

1. **RESOLVED — Phase sharing:** draw 0 shares phases across non-phase variants; draws 1–2 change only the phase vector using distinct deterministic seeds ([Plan:161](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:161)).
2. **UNRESOLVED — Amplitude stationarity:** it is simultaneously a stretch addition and part of the binding sensitivity protocol ([Plan:202](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:202), [Spec:155](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:155)).
3. **UNRESOLVED — P4 completeness:** the tuple now handles partially missing strata but still lacks a zero-usable-strata rule and corresponding usable denominator ([Spec:122](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:122)).
4. **RESOLVED — D3 surface denominator:** detection uses all 610 with `amp_unknown`; frequency-recovery surfaces use only the scorable subset ([Spec:174](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:174)).
5. **RESOLVED — Arm A role:** positive arm-A injections are diagnostic; zero-amplitude arm-A nulls alone are confirmatory ([Plan:189](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:189), [Spec:130](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:130)).
6. **RESOLVED — D1 surface scope:** surfaces are explicitly D2/D3-only and amplitude bins are correctly labeled D3 and D2 ([Spec:172](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:172)).

**FREEZABLE FOR EXECUTION? No.**

Execution-blocking items only:

- Decide whether amplitude-stationarity runs are mandatory or nonbinding, and make the plan/spec agree.
- Define P4 when a target has zero usable strata, including the usable-estimator denominator and bootstrap inclusion rule.
