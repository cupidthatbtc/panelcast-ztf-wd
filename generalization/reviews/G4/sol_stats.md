Recommendation: adopt Amendment 4, regenerate gen1, rerun the pilot validation, then start the full run. The pilot data and provenance are sound, but the present P4 label and several metric implementations need correction.

1. Observation 1 — degenerate exposure strata

Evidence: all 103 nominal targets have `K0 = K1 = 1.0` median exposures/night; K2 is 1.0 for 71 targets and 2.0 for 32. Thus the planned exposure stratification did not occur, as already noted in the [pilot README](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/README.md:36).

The frozen estimator remains mathematically well-defined:

\[
\hat p=\frac1{103}\sum_t\frac13\sum_k y_{tk}.
\]

With complete results it is the exact mean over the fixed 309-shard schedule. But “unbiased” needs qualification:

- It is exact for that finite, deterministic three-window design.
- It is not design-unbiased for the 928-window population because the windows were not randomly sampled.
- It is not an exposure-stratified estimate, and relabelling K as replicates cannot make the deterministically selected, source-ID-tie-broken windows exchangeable.
- The target bootstrap remains appropriate only for the prespecified target-superpopulation interpretation conditional on those windows, as stated in the [metrics specification](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:152).

I recommend re-stratification, not merely relabelling. A mechanism-aligned covariate is

\[
n_{\mathrm{eff},zg}=\sum_{\text{night}}n_{\text{night}}\mathbf1(n_{\text{night}}\ge2),
\]

the number of zg exposures on nights that are not annihilated by single-exposure nightly subtraction. Across the 928 windows its 10/50/90 percentiles are 12/104/724. Selecting target-specific 10/50/90 positions by this variable gives strict K0<K1<K2 separation for 103/103 targets, with selected medians 12/107/691. Baseline is non-degenerate but much more compressed and is less directly tied to the stated failure mechanism.

Recommendation: regenerate gen1 with low/median/high effective-zg-support strata. Report the surface against raw \(n_{\mathrm{eff},zg}\), not “exposures per night,” with both `n_targets` and `n_windows`, target-equal estimates, and target-cluster intervals. If regeneration were declined, K must be called `replicate_id`, and the existing exposure surface should be reported only as observed 1-versus-2 support with no exposure-gradient claim.

2. Observation 2 — P4 construct validity and controls

Evidence: nominal B produced 16/30 detections but only 7/30 strict dominant-frequency recoveries [in the P4 table](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/d2_cluster_completeness.csv:54). By template status:

- Published confirmed: detection 11/13, strict recovery 2/13.
- Published not-detected: detection 4/15, strict recovery 4/15.
- Published candidate: detection 1/2, strict recovery 1/2.

Moreover, 53/119 unique nominal windows are published confirmed, and the ten pilot controls reproduced published trigger status 10/10. These results support the [README’s construct-validity concern](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/README.md:43): detection-only mostly measures whether the combined light curve triggers, not whether the injected DAV signal was recovered.

Recommendation:

- Make `confirmed AND best_candidate_matches_dominant == direct` the primary/headline P4 estimand.
- Retain detection-only as a key secondary endpoint named “post-injection trigger rate,” not “injection-recovery completeness.”
- Do not condition the primary analysis on the control being non-triggering; that changes the denominator to a selected, status-dependent subset.
- Do not subtract the aggregate 119-control native-trigger rate from P4.
- The emitted census/L-S discordance is method complementarity within injected B and does not address uninjected controls.

Instead, score every paired control against the truth of each B shard to which it is paired. For both detection \(D\) and strict recovery \(R\), report the B/control 2×2, B-only yield, control-only yield, union, and paired mean difference. In particular,

\[
R^C_{tk}=1\{\text{control confirmed and its best frequency directly matches target }t\text{’s dominant injected mode}\}.
\]

Report \(P(R^B=1,R^C=0)\) and \(\overline{R^B-R^C}\) as secondary attribution diagnostics using the target-cluster bootstrap. Keep \(P(R^B=1)\) as primary completeness. This preserves the full intended window mixture while directly revealing native accidental matches. Because 119 controls are reused across 309 B assignments, report the reuse table and retain the explicitly conditional-on-assignment interpretation.

3. P5 Gaussian-null design

No change recommended. The pilot’s 0/30 gives the correctly reported \(U_{95}=0.0950\) [in `trigger_rates.csv`](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/trigger_rates.csv:2), so it is essentially uninformative about a 0.5% threshold.

At \(n=1000\), the frozen observed-x rule behaves as follows:

- x=0: U95=0.002991 — accept.
- x=1: U95=0.004735 — accept.
- x=2: U95=0.006282 — reject.

Thus confirmation means at most one false alarm. At the boundary \(p=0.005\), the probability of acceptance is about 4.0%, consistent with a stringent one-sided 5% demonstration. The design is appropriate if the objective is to establish an upper bound ≤0.5%; it is not a high-power design for rates close to 0.5%, but 0/30 provides no basis for altering it. Retain the exact CP-at-observed-x rule in the [frozen P5 specification](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:63).

4. Other statistical anomalies

The provenance/run layer is clean: 144/144 completed, no missing results, no boundary-sensitive cases, and all confirmatory flags are false.

Three metric-layer issues should be fixed before the full run:

- Surface pseudoreplication: surface cells use shard rows as independent “stars.” For example, the detection surface reports intervals for cells with 8 windows/3 targets and 12 windows/4 targets [here](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/surfaces/detection_exposure_amplitude.csv:4), contrary to “cells below five stars: counts only” in the [specification](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:186). One frequency-recovery cell is 1/8 pooled but 1/9 under the required target-equal calculation. Use targets, not windows, for thresholds and intervals.

- Degenerate paired-bootstrap intervals: 36/60 scenario-contrast rows report `[0,0]` because all three observed paired differences were zero. With n=3, zero discordances have a one-sided CP upper bound of 0.632; `[0,0]` is not evidence of equivalence. Add a degeneracy fallback based on the target-level discordance bound. Other n=3 intervals such as `[0,1]` are simply appropriately uninformative.

- Chance-match mismatch: the reported 1.90% mean and 6.90% p95 [chance rate](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/chance_match.json:2) permutes 30 replicated window rows, not ten target truth lists; assignments to another replicate of the same target are incorrectly treated as permutations. It also calibrates direct matching to any injected mode regardless of confirmed status, whereas headline recovery is confirmed plus direct dominant-mode matching. A target-level dominant-endpoint recalculation gave 0 accidental recoveries in all 100 pilot permutations—still too small to interpret. Permute targets, carry all K replicates together, align the numerator with each endpoint, and increase to 10,000 deterministic derangements.

The separate Wilson intervals in `sensitivity.csv` should be labelled descriptive; inference on scenario changes belongs in the paired contrast table. Its \(5.55\times10^{-17}\) lower limits for 0/n should also be clamped to zero as a cosmetic numerical correction.

## Recommended Amendment 4 text

> **Amendment 4 — pilot-informed D2 window support, primary endpoint, and metric corrections.** The 144-shard gen1 pilot remains non-confirmatory and is excluded from every final estimate and decision. This amendment is frozen before any full-campaign L-S run.
>
> For nominal K=3 template selection, replace median exposures per night with \(n_{\mathrm{eff},zg}=\sum_n n_{zg,n}\mathbf1(n_{zg,n}\ge2)\), computed from each attested template after frozen QC. Within the unchanged magnitude-matched candidate pool, sort by `(n_eff_zg, source_id)` and select the unchanged round-half-even 10th/50th/90th-percentile positions. Label K as low/median/high effective-zg-support strata. Record `n_eff_zg` in the shard and generation manifests and regenerate gen1 atomically.
>
> Replace the D2 exposure-surface coordinate with `n_eff_zg`; freeze half-open edges `{28, 74, 144, 371}`, the nearest empirical 20/40/60/80 percentiles of the outcome-independent 928-window pool. Report `n_targets`, `n_windows`, target-equal point estimates, and target-cluster intervals; cells with fewer than five targets report counts only.
>
> P4 primary becomes frequency-recovery completeness with \(y_{tk}=1\) iff nominal arm B is `confirmed` and `best_candidate_matches_dominant == direct`, subject to the existing frequency-scorable and \(S_{\rm best}=1\) conditions. The equal-target/equal-stratum estimator, eligible and usable denominator rules, seed, and target-cluster bootstrap remain unchanged. Detection-only remains a key secondary endpoint labelled “post-injection trigger rate.”
>
> For every B/control pairing, evaluate the control candidate against that B target’s dominant injected frequency. Report paired B/control 2×2 tables, B-only and control-only yields, union, and target-standardized paired differences separately for detection and strict recovery. Report `confirmed-and-direct in B but not control` as a secondary attribution endpoint. Do not condition the primary denominator on control status and do not apply aggregate native-rate subtraction. Census/L-S discordance remains a separate complementarity analysis.
>
> Chance-match calibration uses 10,000 frozen-seed target-level derangements; all K replicates move together. Report endpoint-aligned accidental rates separately for dominant-mode recovery and any-mode recovery.
>
> For paired scenario contrasts with zero observed target-level discordances, do not report bootstrap `[0,0]`; report the point difference plus the exact one-sided 95% CP upper bound on the discordance probability and its conservative effect bound. P5, including n=1000 and the observed-x one-sided CP acceptance rule, is unchanged.
>
> The regenerated generation, pilot outputs, manifests, and tests must pass the existing provenance and fail-closed gates before the full run begins.

## Verdict: PROCEED-WITH-AMENDMENT-4
