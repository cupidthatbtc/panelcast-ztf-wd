Result: the core production/provenance work is substantially improved, but four material contract defects remain. The current implementation files are byte-identical to commit `049f09e`; later commits only add review prompts.

## Verification

- `pytest --collect-only` found all 38 tests.
- The read-only sandbox cannot provide pytest a temporary directory, so the 14 fixture-based builder tests could not execute here.
- The 23 truth-model/frozen tests passed, and `test_production_requires_the_full_arm_matrix` passed separately.
- Direct D1 scoring reproduced `11/13` L-S, `9/13` census, `13/13` union.
- Canonical Amendment-3 data probe: 103 report targets, 33 mixed-cadence targets, all 33 schedulable at 120 s, exactly periods 126.84/127.03/153.26 s rejected for TIC 55650407, no dominant-mode changes, and only final campaign-ID digit 18 changes.

## Round-2 residuals

### (2) Sensitivity grouping/common subset — PARTIALLY RESOLVED

Grouping now includes `scenario`, ratios, phase, scale, `dominant_dropped`, and `cadence_code` at [metrics_generalization.py:922](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:922). Non-nominal scenarios request a nominal K=1 comparison at [metrics_generalization.py:934](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:934).

The exact-common-subset requirement still fails under asymmetric missingness because missing rows are removed before matching. A probe with two usable dropout targets but one missing nominal result emitted dropout `n=2` versus matched nominal `n=1`. This violates the common-subset rule at [METRICS_SPEC.md:166](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:166).

Exact fix: intersect usable cluster IDs on both sides, then restrict both scenario and nominal frames to that intersection. For eligible-denominator comparisons, retain missing rows on both sides as failures. Emit paired bootstrap contrasts using the existing common draw matrix.

### (4) Production status/run matrix — RESOLVED

- Mandatory arms, including `cadence_alt`: [d2_truth_model.py:129](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:129)
- Pure argument-based production decision: [d2_truth_model.py:347](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:347)
- Production flag re-derived: [metrics_generalization.py:316](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:316)
- Unconditional `assert_counts`: [metrics_generalization.py:323](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:323)
- 103 input-target requirement: [metrics_generalization.py:326](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:326)
- Foreign rejected IDs refused: [metrics_generalization.py:352](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:352)
- Focused production test: [test_d2_shards_contract.py:288](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:288)

The Amendment-3 cardinality problem below is separate from these core checks.

### (5) Generation provenance — RESOLVED

Every truth/index output SHA is checked before reading at [metrics_generalization.py:295](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:295); the generation basis/ID is reproduced at [metrics_generalization.py:304](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:304); frozen and shard-determining code identity are checked at [metrics_generalization.py:309](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:309).

The `D2_GENERATION_CODE` scope at [d2_truth_model.py:138](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:138) is acceptable: those three files contain the shard construction/truth logic and frozen import surface, while underlying frozen files are separately hashed. Excluding metrics and runner correctly permits later analysis/driver fixes without orphaning shard bytes. The complete contemporary campaign snapshot remains recorded at [build_d2_shards.py:634](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:634).

### (6) Completion and sidecar binding — PARTIALLY RESOLVED

The D2 path now performs the requested checks:

- Mandatory `completion.csv`, source count, failures, duplicates: [metrics_generalization.py:1035](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1035)
- IDs constrained to the generation and pilot re-derived: [metrics_generalization.py:1047](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1047)
- Pilot truth restricted to selected IDs: [metrics_generalization.py:1059](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1059)
- Result, attestation, generation, pass, environment, binding, shard and completion checks: [metrics_generalization.py:1102](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1102)

However, the shared D3 path remains fail-open: the runner records `shard_dir` at [run_generalization_ls.py:354](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:354), but metrics never verifies that path. Shard SHA validation is conditional on an optional `--shards-dir` and file existence at [metrics_generalization.py:1121](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1121). With no D2 generation, completion IDs are also never checked against D3 truth or an attested panel/shard index.

### (8) `--limit`/pilot semantics — RESOLVED

The help now calls `--limit` a nonrepresentative debug subset while noting that it marks the run `pilot=true`: [run_generalization_ls.py:198](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:198). Pilot status is independently reconstructed by metrics as noted above.

## Previous new findings

### NEW-1 Production arm matrix — PARTIALLY RESOLVED

Mandatory arms and general matrix counts are enforced. Production does not, however, guarantee that 33 cadence-alt rows were realized; see Amendment 3 below.

### NEW-2 Primary D2 aggregates — PARTIALLY RESOLVED

Completeness, contingency, surfaces, and chance-match now receive nominal arm B only at [metrics_generalization.py:1179](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1179).

The FP-frequency output is broken: the caller passes nominal arm B at [metrics_generalization.py:1203](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1203), while `fp_frequency_distribution` immediately filters D2 input to null/control arms at [metrics_generalization.py:897](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:897). A probe returned zero rows from a triggered nominal-B frame and one row when the full frame was supplied.

Exact fix: consistent with the Gaussian-null FP audit specified at [METRICS_SPEC.md:63](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:63), pass full `per_star` and retain `arm`/`scenario` columns so null and control observations remain distinguishable.

### NEW-3 `confirmatory` semantics — RESOLVED

P4 membership is limited to non-pilot nominal-B detection rows, both denominators, at [metrics_generalization.py:637](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:637). P5 membership depends on non-pilot plus 1,000 completions, independently of the acceptance outcome, at [metrics_generalization.py:826](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:826).

### NEW-4 Manifest semantic validation — PARTIALLY RESOLVED

Arm/scenario enumerations, scenario recomputation and campaign-ID recomputation are present at [d2_truth_model.py:366](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:366), and the validator is shared by builder and metrics.

But scenario-specific defaults are incomplete. A runtime probe constructed a valid-ID row combining ladder ratios, `phase_draw=1`, and `amp_scale=0.7`; it was accepted as `ladder_g3r1`. Priority-based `scenario_code` hides crossed axes rather than rejecting them.

Exact fix: enforce a mutually exclusive field tuple for each scenario—ladder only, phase only, amplitude-scale only, dropout only, redilution only, or cadence-alt only. Also validate `0 < crowdsap <= 1` for redilution and the enumerated match/template-status values.

## Amendment 3 — PARTIALLY RESOLVED

Implemented correctly:

- Manifest cadence fields: [d2_truth_model.py:117](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:117)
- Final cadence ID digit: [d2_truth_model.py:327](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:327)
- Pure-120-s rebuilding and K=1 scheduling: [build_d2_shards.py:471](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:471)
- SPOC v3 report in generation inputs: [build_d2_shards.py:605](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:605)
- Nominal aggregate non-pooling: [metrics_generalization.py:1181](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1181)

Remaining defect: production only asserts that the report names 33 mixed targets at [build_d2_shards.py:579](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:579). Scheduling may omit a target with no retained 120-s mode at [build_d2_shards.py:474](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:474), and expected counts simply adopt the shortened list at [d2_truth_model.py:490](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:490). A probe showed a nominally production argument set accepts an expected cadence-alt count of 32.

Exact fix: in production require `cadence_alt_tics == mixed_cadence`, length 33, and require the manifest cadence-alt TIC set to equal both lists with exactly one K=1 row each. Recheck this independently in `truth_d2`.

## New findings

- **BLOCKING — D3 run universe/shard provenance is not bound.** Require the runner to record the shard-index path and SHA; metrics must verify index = on-disk shards = completion IDs, require D3 selected IDs to be contained in D3 truth, and verify every sidecar shard SHA unconditionally using the recorded directory.

- **MAJOR — Sensitivity “matched” rows can have unequal denominators.** Intersect availability or retain missingness symmetrically as described under item 2.

- **MAJOR — D2 FP-frequency output is necessarily empty.** Pass the full D2 frame for the specified null/control audit.

- **MAJOR — Production does not enforce the realized 33-target cadence-alt set.** Assert set identity and cardinality in both builder and metrics.

- **MAJOR — Manifest validation accepts crossed sensitivity axes.** Replace scenario precedence as validation with scenario-specific exclusive invariants.

- **MINOR — ID-layout documentation is stale.** `AA … C0`/“trailing 0 reserved” remains at [d2_truth_model.py:73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:73) and [GENERALIZATION_PLAN.md:57](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:57). Change it to `AA … CD`; the executable ID implementation is already correct.

## Verdict: REJECT
