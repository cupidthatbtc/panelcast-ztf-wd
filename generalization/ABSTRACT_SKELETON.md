# Abstract skeleton + supportable claims (G2 abstract lens, 2026-08-28)

Source: generalization/reviews/G2/sol_abstract.md (sol@xhigh). For G6:
fill placeholders ONLY from frozen metrics outputs; claim list is the
ceiling of what the design supports.

## 2. Claims the design can support

Each sentence below is safe if its placeholders are filled from frozen outputs.

1. Among the 610 Murphy `dSct=1` stars with KIC \(g\ge13.2\), the frozen confirmed rule has eligible-roster detection completeness `[x/610; p%; 95% Wilson CI L–U]` and usable-light-curve completeness `[x_u/n_u; p_u%; CI L_u–U_u]`.

2. Among the 456 Mo-joined D3 positives, `[x/456; p%; 95% CI L–U]` produce a confirmed BEST candidate directly matching the historical dominant frequency within \(1.5/T_{\rm baseline}\), beside an accidental-match rate of `[p_acc%]`.

3. Among `[n]` confirmed, frequency-scorable D3 positives, `[x/n; p%; 95% CI L–U]` have a direct dominant-frequency match, giving the correct-frequency fraction among detected positives.

4. D3 detection or frequency-recovery completeness varies from `[p_low]` to `[p_high]` across prespecified historical Kepler-amplitude, period, magnitude, and crowding strata, with pointwise intervals and no causal or contemporaneous ZTF-amplitude interpretation.

5. The weighted confirmed negative-class trigger rate in the 7,292-member magnitude-restricted `dSct=0` frame is `[p%; approximate ESS-Wilson CI L–U]`, with triggered sources divided descriptively into plausible variables and unexplained cases.

6. Within the weighted D3 frame containing `dSct=1` positives and `dSct=0` negatives, the frame-specific label PPV is `[p%; approximate CI L–U]`, with `dSct=2` excluded and no transfer to populations with different prevalence.

7. Among `[n]` D3 positives with both methods available, census-only, Lomb–Scargle-only, and union fractions are `[x_C/n]`, `[x_L/n]`, and `[x_U/n]`, demonstrating empirical non-redundancy if both discordant cells are populated.

8. Across 103 Romero DAV signal models, the nominal arm-B post-injection confirmed-rule probability is `[p%; target-cluster-bootstrap CI L–U]`, standardized equally over the selected 10th-, 50th-, and 90th-percentile window conditions.

9. Among D2 targets with at least one retained injected mode inside the search bounds, `[x/n; p%; target-cluster-bootstrap CI L–U]` produce a confirmed BEST candidate directly matching an injected mode.

10. Median-window D2 recovery ranges from `[p_min]` to `[p_max]` over the prespecified 3×3 bandpass grid and by `[Δ_phase]` over three deterministic phase assignments, which are finite sensitivity ranges rather than confidence bands.

11. The paired uninjected arm-B windows have native-template trigger rate `[x/m; p%]`, while, if zero Gaussian nulls trigger, `FPR_Gaussian=0/1000` has a one-sided 95% upper limit of approximately 0.30% once the interval method is frozen.

12. The D1 results describe responses within the 19-star labeled white-dwarf roster, with class-specific counts and intervals expressing finite-roster imprecision rather than population-wide completeness.

13. If both discordant cells occur separately in D1, D2, and D3, the campaign can conclude that the census and confirmed period-search rules exhibit empirical non-redundancy in each assessment, without pooling them into a universal response estimate.

The design cannot support a universal ZTF selection function, real-sky DAV completeness from D2, three external validations, a D3 false-positive rate, a contemporaneous ZTF-\(g\) threshold, causal cadence/crowding claims, or unqualified purity.

## 3. Referee-safe 250-word abstract skeleton

Whitespace-delimited count: exactly 250 words, with each compact placeholder counting as one word.

> Wide-field variability searches must quantify how frozen decision rules respond beyond their development sample. We evaluate a frozen ZTF variance-census and blind Lomb–Scargle pipeline through three deliberately separate assessments. D3, the only external-label validation on real ZTF photometry, applies the pipeline to a magnitude-restricted Kepler A/F-star frame: all 610 labeled δ Scuti stars, 76 dSct=2 objects excluded from headline estimates, and a weighted random sample of 2,314 labeled non-δ-Scuti stars. D2 measures conditional injection-recovery of the frozen search stage by transplanting published DAV mode models into three magnitude-matched real ZTF windows for 103 targets, with target-cluster bootstrap intervals and prespecified bandpass and phase sensitivity analyses. D1 serves only as the published 19-star white-dwarf anchor.
>
> For D3, primary confirmed detection completeness is [x/610;p%;95%CI:L–U] on the eligible roster and [x/n;p%;95%CI:L–U] among usable light curves. Strict best-candidate direct-frequency recovery among 456 frequency-scorable positives is [x/456;p%;95%CI:L–U], versus an accidental-match rate of [p%]. The weighted negative-class trigger rate is [x_w/7292;p%;approx95%CI:L–U], interpreted for a class that can contain other variables. Census-only and Lomb–Scargle-only fractions are [x_C/n;p%;95%CI:L–U] and [x_L/n;p%;95%CI:L–U], yielding union completeness [x_U/n;p%;95%CI:L–U]. Completeness is stratified by historical Kepler amplitude and magnitude, with pointwise Wilson intervals and sparse cells reported as counts.
>
> For D2, nominal confirmed conditional injection-recovery is [p%;cluster-95%CI:L–U], and strict direct-frequency recovery is [x/n_Sp;p%;cluster-95%CI:L–U]. Results span [p_min–p_max] across the prespecified bandpass grid and [p10,p50,p90] across window strata; paired uninjected controls trigger at [x/m;p%].
>
> Together, these measurements show that census and period-search responses remain empirically non-overlapping while separating finite-anchor behavior, model-conditioned recovery, and externally labeled performance.

