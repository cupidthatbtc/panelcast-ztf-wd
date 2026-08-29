## Verdict

Conditional **GO**. If D3 lands, this can support a referee-safe AAS abstract; D3 must carry the external-validation claim, with D2 presented as a conditional injection experiment and D1 as a finite-sample anchor. As written, however, the documents should not pass G2: several discrepancies can change denominators or run counts, and a few phrases directly violate the binding estimand vocabulary.

The drafting pass was deliberately claim-first and kept the three assessments separate.

## 1. Internal-consistency audit

### PLAN–SPEC contradictions, differences, and omissions

| # | Issue | Conflict | Required resolution |
|---:|---|---|---|
| 1 | G2 freeze status | [PLAN 210](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:210) says the SPEC freezes only after future G2; [SPEC 6](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:6) says it was “frozen at G2.” | Before G2, write “to be frozen at G2”; afterward mark G2 done with date and blob SHA. |
| 2 | D1 denominator | The PLAN distinguishes a 19-star truth roster from the 928-star catalog ([PLAN 18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:18)); the SPEC defines D2/D3 denominators but no D1 class denominators ([SPEC 13](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13)). | Define the labeled classes within the 19 stars explicitly and state that the 928-star catalog is not a labeled-positive completeness denominator. |
| 3 | Negative sampling probability | PLAN gives rounded inclusion probability `0.317` ([PLAN 113](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:113)); SPEC binds weight `7292/2314` ([SPEC 28](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:28)). | Store exact probability `2314/7292 = 0.3173340647` and weight `7292/2314 = 3.1512532411`; never derive the weight from `0.317`. |
| 4 | D3 PPV frame | PLAN excludes 76 `dSct=2` objects from headlines ([PLAN 112](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:112)); SPEC does not say whether they enter PPV ([SPEC 27](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:27)). | Specify headline PPV as weighted `dSct=1` versus `dSct=0`, with `dSct=2` excluded and reported separately. |
| 5 | The 456-star set | PLAN calls these stars “with dominant amplitude” ([PLAN 116](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:116)); SPEC calls them stars “with Mo rows” ([SPEC 20](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:20)). | Define and assert one set: “Mo-joined, at least one frequency, and a defined dominant-mode amplitude,” with count exactly 456. |
| 6 | Binding names | PLAN uses “frequency recovery” and “completeness turn-on curve” ([PLAN 23](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:23), [PLAN 118](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:118)); SPEC binds “frequency-recovery completeness” and “detection completeness” ([SPEC 13](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13)). | Use the binding names everywhere. |
| 7 | Gaussian-null window frame | PLAN first adopts all 928 windows ([PLAN 150](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:150), then assigns nulls to the obsolete 510-window set ([PLAN 163](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:163)); SPEC says 928 ([SPEC 35](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:35)). | Replace 510 with “1,000 zero-amplitude simulations scheduled over the 928-window frame; windows may repeat, noise seeds do not.” |
| 8 | Arm-B controls | PLAN says templates “ARE the not-detected set” and calls controls “Arm-B nulls” ([PLAN 165](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:165)); that contradicts both the all-928 design and the SPEC’s native-template trigger-rate estimand ([SPEC 39](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:39)). | Delete the sentence; call them paired uninjected controls, one per unique used arm-B window. |
| 9 | Gaussian metric name | PLAN says unqualified “FPR” ([PLAN 163](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:163)); SPEC binds `FPR_Gaussian` ([SPEC 34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:34)). | Use “Gaussian-null false-alarm rate (`FPR_Gaussian`).” |
| 10 | D3 result called FPR | PLAN risk 5 calls the negative result “FPR” ([PLAN 243](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:243)); both PLAN 127 and SPEC 30 prohibit this. | Replace with “negative-class trigger rate, with adjudicated plausible-variable and unexplained components.” |
| 11 | D2 detection versus recovery | PLAN says native variability is handled by strict frequency scoring ([PLAN 156](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:156)); SPEC makes detection-only rule firing primary and direct-frequency recovery separate ([SPEC 56](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:56)). | State that primary D2 detection is post-injection rule firing; strict matching measures frequency-recovery completeness, and controls contextualize native triggers. |
| 12 | Sinc threshold and positive eligibility | PLAN fixes rejection at `|sinc| < 0.3` ([PLAN 143](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:143)); SPEC only says “after sinc rejection” and does not define a target left with zero modes ([SPEC 21](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:21)). | Put the exact threshold in SPEC; define injection-positive eligibility as at least one retained nonzero mode while retaining all 103 targets in attrition. |
| 13 | Romero self-windows | PLAN says successful self-windows become “preferred” ([PLAN 159](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:159)); SPEC fixes the nominal `K=3` percentile design ([SPEC 78](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:78)). | Make self-windows a separate diagnostic that neither replaces nor enters the nominal K=3 aggregate. |
| 14 | Ladder scope and count | PLAN runs eight nonnominal points on only the median window, `8×103=824` ([PLAN 171](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:171)); SPEC does not limit its 3×3 range to that stratum ([SPEC 83](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:83)). | Say explicitly that the ladder is median-window-conditioned; otherwise the nonnominal count is 2,472, not 824. |
| 15 | Phase sensitivity | PLAN fixes two extra draws on the median template ([PLAN 175](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:175)); SPEC mentions phase variants without number, scope, or seed rule ([SPEC 78](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:78)). | Freeze all three dimensions in SPEC before G2 and call the result a descriptive finite-draw sensitivity range. |
| 16 | Arm-A and de-dilution diagnostics | PLAN includes 309 nonnull arm-A runs and a CROWDSAP subset ([PLAN 162](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:162), [PLAN 173](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:173)); SPEC defines neither diagnostic estimand. | Add both as pointwise descriptive analyses with their exact denominators. |
| 17 | D2 total | PLAN’s `≈2,960` comprises at most `309+309+1000+824+309+206=2,957` ([PLAN 169](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:169)), but excludes self-window and de-dilution work. | Call `≤2,957` the core scheduled total and list both stretch additions separately. |
| 18 | Sensitivity “band” | PLAN says the ladder headline is a “band” ([PLAN 242](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:242)); SPEC explicitly says it is never a confidence band ([SPEC 83](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:83)). | Say “nominal estimate plus prespecified finite-grid sensitivity range.” |

### Additional internal defects

These are not merely PLAN–SPEC wording differences:

- The deadline is labeled Tuesday, but 2026-09-30 is Wednesday ([PLAN 4](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:4)).

- The replay gate is recorded as PASS at [PLAN 73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:73) and simultaneously “running” at [PLAN 218](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:218).

- The nominal `A_g/A_TESS=1.7` is attributed to the blackbody derivative at [PLAN 145](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:145), while [PLAN 183](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:183) says the derivative gives 1.43, the low rung; describe 1.7 as the adopted midpoint, not the blackbody value.

- “P < 240 s is … past the first sinc null” is physically wrong for 120-s integration ([PLAN 138](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:138)); 240 s is the Nyquist period, while the first integration-response zero is at 120 s.

- At 84 runs/hour, the core D2 matrix takes about 35.2 hours, consistent with 1.5 days, not the “≈1 day” and “+1 day” fallback elsewhere ([PLAN 169](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:169), [PLAN 193](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:193), [PLAN 198](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:198)).

- The near-saturation strata omit exactly `g=14` because they are defined as `<14` and `>14` ([PLAN 124](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:124)).

- The supposedly disjoint frequency taxonomy makes `ambiguous` unreachable when strict precedence assigns `direct`, `harmonic`, or `window_alias` first ([SPEC 43](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:43)); test all match classes first, assign `ambiguous` if multiple classes match, then apply precedence only to single-class cases.

- `matched_primary` is described as matching the BEST candidate while “primary” also means the dominant truth mode ([SPEC 56](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:56)); use names encoding both axes, such as `best_candidate_matches_dominant_mode`.

- D2 frequency scorability requires a retained mode inside pass bounds, whereas D3 automatically treats all 456 Mo joins as scorable ([SPEC 18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:18)); either apply the same bounds rule or explicitly define D3 as end-to-end recovery including out-of-band failures.

- The surface specification does not define which mode supplies period and amplitude for multimode D2 targets ([SPEC 97](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:97)); freeze a star-level rule, probably the largest-amplitude retained published mode.

- No interval estimator or dependence treatment is specified for the 1,000 Gaussian nulls, despite repeated windows ([SPEC 34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:34)); bind the one-sided estimator and unit before running.

- Required weighted PPV has no unambiguous named output in the output inventory ([SPEC 27](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:27), [SPEC 126](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:126)); add a PPV file or explicit schema columns.

The major counts otherwise reconcile: `610+76+2314=3000`, `74+32−3=103`, `103×3=309`, and `8×103=824`.

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

## 4. Five most likely schedule failures

| Rank | Failure mode and warning | Mitigation and decision date |
|---:|---|---|
| 1 | **Metrics → G5 → abstract does not converge.** Warning: by Sep 14 the pilot cannot produce every required table, guard, bootstrap, permutation, manifest, and plot, or independent counts disagree by Sep 20. | Exercise the complete output pipeline on pilot data, including empty cells and independent headline recomputation; remove D2 and secondary surfaces from the abstract on Sep 18 if they are not green, and no-go the results abstract after Sep 24 if D3 headlines have not passed G5. |
| 2 | **Review gates become serial blockers.** Warning: unresolved G2 issues on Sep 2, no frozen SPEC SHA on Sep 3, or G3 findings open on Sep 9. | Maintain one deduplicated issue ledger and separate D3-blocking from D2-only findings; freeze a D3-only scope on Sep 4 if D2 is delaying G2. |
| 3 | **D3 fetch, crossmatch, or QC attrition destroys the critical sample.** Warning: under 90% fetched by Sep 1, no class-stratified attrition report by Sep 5, or disproportionate loss among positives or Mo-joined stars. | Fetch and panelize incrementally, prioritize all 610 positives, retry failures continuously, and monitor attrition by class/amplitude daily; suspend D2 stretch work on Sep 6 if D3 is behind. |
| 4 | **D2 consumes resources without becoming publishable.** Warning: desktop not awake, replay-attested, and scratch-tested by Sep 7; parser/G3 still failing Sep 9; no trustworthy pilot Sep 10. | Reserve the laptop for D3, drop self-window and de-dilution stretches first, and remove D2 from the deadline scope on Sep 10 unless hardware, parser, G3, and timing pilot are all green. |
| 5 | **Batch throughput or disk pressure compresses W4.** Warning: D3 pilot projects over 72 hours, failed shards exceed 2%, free scratch falls below roughly 26 GB for 22 workers, or detached jobs die. | Preflight capacity, use checkpointed local NVMe scratch and WMI launch, and allocate both machines to D3 if its projected completion exceeds Sep 17; invoke the minimum D3-only abstract if D3 is under 70% complete on Sep 15. |

The replay environment is not presently top-five because the recorded 25/25 replay passed; the full 928-star and panel-stage replays remain required hardening.
