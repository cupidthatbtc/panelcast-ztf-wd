Round 2 remains a reject. The patch resolves three findings, but five are only partial; production completeness and provenance remain fail-open.

## Verification

- Current suite collects exactly 31 tests. The 23 tests not requiring temporary files pass in the repository environment: `23 passed in 0.87s`.
- The eight builder integration tests could not run because this review sandbox is read-only and pytest cannot create its temporary directory. The default `python3` also lacks pytest; `.venv-gen` is the correct environment.
- A direct run through the current D1 scoring functions reproduced `11/13` L-S, `9/13` census, `13/13` union.
- Current D2 data probe: 103 unique targets, all 103 schedulable, zero zero-retained exclusions, 76 dropout-eligible.
- The Amendment-2 document hashes match those recorded at [G2_FREEZE.md:63](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:63).

## Round-1 findings

1. BLOCKING — RESOLVED.

The shared fixed schema is defined at [d2_truth_model.py:89](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:89). `typed_row` populates and casts every column at [build_d2_shards.py:267](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:267); controls and nulls receive explicit typed values at [build_d2_shards.py:498](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:498). `load_d2_manifest` enforces the header and dtypes at [metrics_generalization.py:252](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:252), and `truth_d2` propagates all relevant fields at [metrics_generalization.py:343](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:343). The full A/B/control/null integration case is covered at [test_d2_shards_contract.py:121](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:121) and [test_d2_shards_contract.py:172](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:172).

2. BLOCKING — PARTIALLY RESOLVED.

Scenario codes are explicit and disjoint at [d2_truth_model.py:84](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:84) and [d2_truth_model.py:122](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:122). The builder schedules nominal, ladder, phase, scale and dropout separately at [build_d2_shards.py:451](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:451). The cluster estimator groups by scenario and all specified keys, uses `n_strata_scheduled`, and isolates nominal arm B at [metrics_generalization.py:561](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:561).

However, `sensitivity_table` groups only by ratios, phase and amplitude scale at [metrics_generalization.py:880](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:880). It omits `scenario` and `dominant_dropped`, contrary to the common-subset/scenario rule in [METRICS_SPEC.md:166](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:166). A runtime probe with one confirmed nominal row and one failed dropout row produced one pooled `n=2, k=1, p=0.5` row. It also does not emit nominal K=1 recomputed on each sensitivity scenario’s matched target subset.

3. BLOCKING — RESOLVED.

The builder refuses an existing output, uses a staging directory and sentinel at [build_d2_shards.py:361](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:361), derives the generation ID and records all shard hashes at [build_d2_shards.py:566](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:566), then removes the sentinel and publishes with `os.replace` at [build_d2_shards.py:613](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:613). There is no builder `--resume`. The runner refuses a sentinel-bearing or undescribed D2 generation at [run_generalization_ls.py:222](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:222).

4. BLOCKING — PARTIALLY RESOLVED.

`truth_d2` now checks manifest uniqueness, index/disk/manifest equality, shard hashes, injected/rejected counts, nominal K sets and null serials at [metrics_generalization.py:293](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:293). `n_targets_zero_usable_strata` is calculated once and reported for both denominators at [metrics_generalization.py:598](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:598). P5 uses provenance-valid completed nulls and requires `n=1000` for acceptance at [metrics_generalization.py:774](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:774).

The production design is nevertheless fail-open. `production` ignores `--arms` at [build_d2_shards.py:347](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:347), while `truth_d2` validates nominal B and nulls only when those subsets are nonempty at [metrics_generalization.py:321](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:321) and [metrics_generalization.py:329](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:329). Thus `--arms nulls` or `--arms b` can be marked production and skip a required endpoint entirely. There is also no unconditional production assertion of exactly 103 scheduled TICs, and extra foreign rows in `rejected_modes.csv` are not rejected.

5. BLOCKING — PARTIALLY RESOLVED.

The builder verifies the roster report’s target/mode hashes at [build_d2_shards.py:370](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:370) and records roster, SPOC, recovered modes, catalog, template shards, frozen files, campaign code, arguments, outputs and shard hashes at [build_d2_shards.py:566](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:566).

Metrics records the current truth-table hashes and declared generation inputs at [metrics_generalization.py:988](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:988), but it never compares the current truth-table hashes with `generation["outputs_sha256"]`. `truth_d2` verifies shard bytes and row counts only at [metrics_generalization.py:301](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:301). Changing injected frequencies without changing row counts is therefore accepted. Metrics also does not recompute the generation ID or compare the generation’s campaign/frozen hashes with the current checkout.

Exact remaining fix: recompute and verify every generation output SHA, the generation basis/ID, and current campaign/frozen hashes before reading truth; reject any extra injected or rejected ID.

6. MAJOR — PARTIALLY RESOLVED.

The runner sidecar contains the requested source, pass, shard/result, environment, frozen/campaign, attestation and generation fields at [run_generalization_ls.py:113](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:113). Reuse checks all those fields at [run_generalization_ls.py:133](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:133), and `completion.csv` is emitted at [run_generalization_ls.py:368](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:368).

Metrics merely hashes `completion.csv` if it happens to exist; it never requires or parses it at [metrics_generalization.py:983](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:983). Its sidecar checks omit `passes`, `env_digest`, `frozen_digest` and `campaign_digest` at [metrics_generalization.py:1024](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1024). It also does not verify the run manifest’s shard directory, stars directory, selected IDs, source count or failures. Consequently, the claim in [GENERALIZATION_PLAN.md:252](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:252) that metrics “verify all of it” is not yet true.

7. MAJOR — RESOLVED.

Templates are read as original text tokens while model epochs come from the frozen parser at [build_d2_shards.py:134](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:134). Synthesis preserves every token except source ID and magnitude at [build_d2_shards.py:227](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:227). Every written shard is reloaded and checked for bitwise epoch identity, finiteness, bands and source ID at [build_d2_shards.py:251](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:251), with integration coverage at [test_d2_shards_contract.py:159](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:159).

8. MAJOR — PARTIALLY RESOLVED.

The deterministic stratified pilot index is implemented at [build_d2_shards.py:308](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:308) and emitted at [build_d2_shards.py:563](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:563). Runner manifests mark any subset run as pilot at [run_generalization_ls.py:229](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:229), and pilot P4/P5 rows are nonconfirmatory at [metrics_generalization.py:600](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:600) and [metrics_generalization.py:793](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:793).

But the runner still advertises lexicographical `--limit` as “pilot mode” at [run_generalization_ls.py:198](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:198), preserving the unrepresentative path. More importantly, metrics trusts the run manifest’s raw `pilot` Boolean at [metrics_generalization.py:942](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:942) without checking it against `limit`, `stars_file` and `completion.csv`; a modified pilot manifest can therefore be promoted to confirmatory.

## New findings

- BLOCKING — Production status does not require the production arm matrix. Exact fix: define the mandatory core arm set and make `production=true` contingent on that exact matrix, canonical 103-target roster, 928-window pool and 1,000 nulls. In `truth_d2`, make all production count/bijection assertions unconditional; never guard them with `if not subset.empty`. Add refusal tests for `--arms nulls`, `--arms b`, missing controls and missing sensitivity scenarios.

- MAJOR — Other D2 outputs still pool arms and scenarios. `completeness_tables` selects all positive A/B rows at [metrics_generalization.py:418](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:418), and `surfaces` does the same at [metrics_generalization.py:679](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:679). Exact fix: restrict primary D2 aggregates/surfaces to nominal arm B, or emit explicitly keyed arm/scenario-specific tables; construct each sensitivity contrast against nominal K=1 on the exact matched TIC subset.

- MAJOR — `confirmatory` has inconsistent semantics. A production nominal-B probe marked all four detection/frequency × usable/eligible rows confirmatory, although P4 is detection-only. Conversely, a complete production P5 with `x=2` correctly failed acceptance but was labeled `confirmatory=false`. Exact fix: make `confirmatory` describe whether the row belongs to the prespecified production analysis, independent of whether it passes; retain `acceptance_u95_leq_0.005` as the outcome. Frequency-recovery and paired-discordance rows must remain nonconfirmatory.

- MAJOR — The typed schema does not enforce semantic row invariants. A runtime probe showed `validate_manifest` accepts `arm=B, scenario=garbage, dominant_dropped=True, n_strata_scheduled=99`. Exact fix: validate arm/scenario enumerations and recompute the expected scenario from ratio, phase, scale, dropout and crowding fields; enforce per-arm defaults and allowed stratum counts in both builder and metrics. Add manifest-semantic and truth-table tamper tests.

## Verdict: REJECT
