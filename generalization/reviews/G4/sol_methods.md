1. The “K=3 at 10/50/90th percentile” description is indefensible as written. The algorithm selects three distinct windows, but it does not produce three exposure-per-night strata: K0 and K1 have identical values for 103/103 targets, and K2 is only 1–2. A referee would treat K as an arbitrary rank in a tie-broken list and reject any exposure-stratified interpretation or exposure-axis trend. This is already acknowledged in the [pilot README](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/README.md:36>), while the [plan](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:190>) and [builder](</Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:194>) still call the picks exposure strata.

   Re-stratify now. Relabeling them “matched replicate windows” would be honest, but it abandons the prespecified risk-3 explanatory axis. Keeping the current labels with a caveat is insufficient. Given a ~90 s rebuild, ~2 h pilot, and no confirmatory run, this is exactly when a pilot-informed repair should occur.

   Recommended covariate: the zg within-night contrast count

   \[
   W_g(w)=\sum_n \max(m_{wgn}-1,0)=N_{zg}(w)-N_{\mathrm{zg\,nights}}(w),
   \]

   where \(m_{wgn}\) is the number of attested zg exposures in night \(n\). This directly measures support remaining after the frozen high-pass stage subtracts each night’s median ([implementation](</Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/lomb_scargle_common.py:58>)).

   Exact selection rule: retain the current magnitude-matched candidate pool and fallback; sort it lexicographically by `(W_g, source_id)`; select indices `int(np.round(q*(N-1)))` for \(q=\{0.10,0.50,0.90\}\), preserving NumPy round-half-even. Record `template_wg_contrasts` and require \(W_{g,0}<W_{g,1}<W_{g,2}\) in production.

   Recalculation on the frozen 928-window pool gives \(W_g\) min/10th/50th/90th/max = 0/6/58/449/2670, with 333 distinct values. Applying the exact proposed rule to all 103 target-specific magnitude pools gives three strictly distinct values for 103/103 targets: K0 ranges 0–23, K1 8–127, and K2 100–786.

2. Current reporting is insufficient for a primary injection-recovery claim. It is sufficient only for a secondary “post-injection trigger probability.”

   The evidence is strong:

   - Detection-only is 16/30 = 0.533, while confirmed plus dominant-mode direct recovery is 7/30 = 0.233 ([cluster results](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/d2_cluster_completeness.csv:54>)).
   - On 13 published-confirmed windows, 11 triggered and only 2 directly recovered the injection; on 15 not-detected windows, 4 triggered and all 4 recovered. Candidate windows contribute another 1/2 direct recovery ([README](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/README.md:43>)).
   - Only 7/16 detected shards recovered the dominant injected mode ([generic metrics](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/completeness_by_class_pass_rule.csv:24>)).
   - The ten pilot controls have an 8/10 native trigger rate ([trigger rates](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/trigger_rates.csv:3>)).

   Aggregate controls and census/L-S discordance describe the contamination; they do not remove it from \(P(D_{\text{post-injection}}=1)\). Promote the already-prespecified frequency endpoint to P4:

   \[
   Y^{\mathrm{rec}}_{tk}
   =I\{\text{rule 1 confirmed}\ \land\
   \text{best candidate directly matches the largest-amplitude retained injected mode}\}.
   \]

   Eligible estimand:

   \[
   \widehat p_{\mathrm{P4,E}}
   =\frac1{103}\sum_{t=1}^{103}\frac13\sum_{k=0}^{2}Y^{\mathrm{rec}}_{tk},
   \]

   with missing results counted as zero. The usable version retains the current per-target averaging over usable windows and excludes targets with zero usable windows. Use the existing target-cluster bootstrap. Detection-only remains secondary and must be named “post-injection rule-1 trigger rate,” never injection recovery or completeness.

   Also report the prespecified paired-control diagnostic explicitly rather than only as an aggregate rate. Let

   \[
   Q_t=\{k:\text{injected/control pair usable and control status is not\_detected}\}.
   \]

   Then report

   \[
   \widehat p_Q=
   \frac1{|T_Q|}\sum_{t\in T_Q}\frac1{|Q_t|}
   \sum_{k\in Q_t}I\{\text{injected shard confirmed}\},
   \]

   together with \(|T_Q|\), pair count, unique-window count, and direct-recovery rate within the same subset. This is a quiet-control-conditioned secondary estimand; it does not generalize to native-active windows.

   Required `METRICS_SPEC.md` changes:

   - Header [lines 4–7](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:4>): identify v4 as a disclosed post-pilot, pre-confirmatory amendment.
   - Estimand vocabulary [lines 13–30](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13>): make joint confirmed-plus-dominant-direct recovery primary; move detection-only to secondary.
   - P4 definition [lines 124–144](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:124>): replace \(y=I(\text{confirmed})\) with \(Y^{rec}\) above and prohibit further hierarchy changes after Amendment 4.
   - Complementarity [lines 177–184](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:177>): label D2 census/L-S tables as descriptive post-injection response, without recovery attribution.
   - Surfaces [lines 186–204](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:186>): make direct recovery the primary D2 surface and replace the degenerate exposure axis with K as the relative \(W_g\) stratum, while reporting actual \(W_g\).
   - Guards [lines 228–250](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:228>): enforce the new matching rule, strict K separation, and resolution of every nominal-B `control_campaign_id`.

3. The 10/10 control-status agreement certifies a narrow but useful fact: for those ten selected windows, the uninjected shard construction preserved enough of the real photometry and frozen execution behavior to reproduce the published `blind_status`, despite changing the source ID and therefore the frozen bootstrap seed. It supports the interpretation that the 8/10 triggers are native baseline responses rather than injection artifacts.

   It does not certify candidate frequency/pass identity, census reproduction, all 119 generated controls, the full 928-window pool, representativeness of the ten pilot controls, injected-signal fidelity, frequency recovery, or false-alarm calibration. Only 10 of the 30 nominal-B pilot pairs had their controls run, so it also cannot support a pilot-wide paired adjustment. The observed 8/10 is descriptive, not an estimate of the pool’s native-trigger prevalence.

4. The provenance chain is strong but still attackable.

   Strengths include 144/144 completion, zero failures, strict 928-star replay, generation/spec SHA binding, 144 provenance checks, zero platform-boundary-sensitive rows, and explicit `pilot=true`/`confirmatory_allowed=false` ([run manifest](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/run/manifest.json:2>), [metrics manifest](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/results/2026-08-30_d2_pilot/metrics/manifest.json:2>)).

   Remaining attacks:

   - The committed pilot directory omits the 144 raw result JSONs and `.prov.json` sidecars. `inputs_sha256.json` contains 144 result hashes but zero sidecar hashes. Verification occurred during scoring, but an external reader cannot reconstruct or independently audit it.
   - The run manifest SHA-binds the full `shard_index.txt`; `stars_file` is only an unhashed path string. The completion IDs are checked as a subset of the generation, not as exactly equal to `pilot_shard_index.txt`. Add `stars_file_sha256` and an exact set-equality guard.
   - The mandatory unique-window reuse table from the [unit-of-analysis specification](</Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:152>) is absent.
   - Generic D2 outputs use row-level Wilson intervals and count 30 shards, while the binding D2 unit is the TIC cluster. The amplitude surfaces likewise treat three windows per target as independent “stars,” and the complementarity JSON reports Wilson intervals despite requiring a cluster bootstrap. Suppress those D2 intervals or compute all D2 inference through the cluster machinery.
   - Chance matching currently permutes shard rows, so a pilot row can receive another replicate’s truth list from the same TIC. The specification says truth lists are permuted across stars; permutation must occur at TIC level.
   - The implementation marks production P4 detection rows `confirmatory=true`, while the plan/spec call P5 the sole confirmatory decision. Replace that ambiguous field with separate `prespecified_primary` and `confirmatory_decision` flags.
   - Record the exact command/argv, start/end timestamps, git commit and dirty state, sidecar hashes, and test-log hash. Per-file SHA snapshots mitigate these omissions, but the README’s “41/41” assertion is not independently attested.

### Recommended Amendment 4 text

> **Amendment 4 — post-pilot D2 window stratification and recovery estimand (2026-08-30).** The gen1 timing pilot was explicitly non-confirmatory and exposed two design defects before any confirmatory-era run: median exposures per zg night does not separate the planned K strata, and detection-only P4 conflates native template triggers with injected-signal recovery. Gen1 results remain archived as exploratory evidence and enter no estimate.
>
> For every attested template window \(w\), define the zg within-night contrast count \(W_g(w)=\sum_n\max(m_{wgn}-1,0)\). The magnitude-match pool and fallback rules remain unchanged. Sort each target’s pool lexicographically by `(W_g, source_id)` and select the round-half-even 10th-, 50th-, and 90th-percentile indices exactly as before. Label K=0/1/2 as low/median/high \(W_g\) matched-window strata, record \(W_g\) in the manifest, and fail production generation unless the three selected windows and their \(W_g\) values are distinct.
>
> Primary P4 becomes nominal-arm-B dominant-mode direct injection recovery: rule 1 is confirmed and the best candidate directly matches the largest-amplitude retained injected mode from `injected_modes.csv`. Eligible and usable target-equal estimators and the target-cluster bootstrap remain unchanged. Detection-only is retained as the secondary “post-injection rule-1 trigger rate” and carries no recovery or completeness interpretation.
>
> Paired controls remain contextual. Report their native-trigger rate, P4 recovery stratified by paired-control status, and quiet-control-conditioned detection using pairs whose control is usable and `not_detected`; report target, pair, and unique-window denominators. D2 census/L-S complementarity remains descriptive.
>
> Freeze the amended plan, specification, builder, and scorer before gen2. Regenerate gen2, rerun the stratified pilot, archive raw results and sidecars, bind the pilot-index SHA, and permit the full run only after all amended guards pass. Amendment 4 is disclosed as pilot-informed and is not represented as part of the original v3 preregistration.

## Verdict: PROCEED-WITH-AMENDMENT-4
