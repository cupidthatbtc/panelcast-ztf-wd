The round-4 implementation substantially resolves the round-3 defects, but one validator loophole and an unusable production/pilot runbook remain. Current HEAD is `1dc35ae`; its tracked changes after `2ad86a5` are only the two round-4 prompt files, so the reviewed implementation matches the claimed commit.

## Per-item verification

1. **D3 run-universe binding — RESOLVED**

- The runner requires a production shard index and checks index IDs against disk at [run_generalization_ls.py:205](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:205) and [run_generalization_ls.py:254](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:254).
- The run manifest records the index path and SHA at [run_generalization_ls.py:354](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:354).
- Metrics requires `--shards-dir` for D2/D3 at [metrics_generalization.py:1090](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1090).
- Index defaulting, manifest-SHA binding, index/disk equality, completion containment, D2 generation equality, D3 truth containment, and subset-to-pilot reconstruction are enforced at [metrics_generalization.py:1130](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1130).
- Every scored sidecar now requires the shard file and verifies its SHA unconditionally at [metrics_generalization.py:1215](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1215).
- The metrics commands supply the necessary D3 index and D2 generation directory at [RUNBOOK.md:42](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:42) and [RUNBOOK.md:61](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:61).

The recorded index path itself is not compared, but content identity is bound by SHA; that is sufficient.

2. **Symmetric missingness and paired contrasts — RESOLVED**

- `sensitivity_table` intersects scenario-usable and nominal-usable targets, then restricts both frames to that set at [metrics_generalization.py:1003](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1003).
- Paired contrasts use the same cluster draw matrix; usable requires both results, while eligible retains missing rows as failures at [metrics_generalization.py:705](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:705) and [metrics_generalization.py:736](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:736).
- The output is written to `d2_scenario_contrasts.csv` at [metrics_generalization.py:1294](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1294).

Probe result: asymmetric nominal missingness produced usable `n=1` on both sides; eligible retained both targets and scored the missing nominal result as failure.

3. **D2 FP-frequency frame — RESOLVED**

- The function filters the full D2 frame to Gaussian-null/control arms and retains `arm` and `scenario` at [metrics_generalization.py:965](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:965).
- Main passes full `per_star`, not nominal-B primary, at [metrics_generalization.py:1300](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1300).
- The focused test begins at [test_d2_shards_contract.py:315](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:315).

Probe output retained both a triggered `gauss_null` and a triggered `ctrl` row with their scenario labels.

4. **Cadence-alt cardinality and identity — RESOLVED**

- `check_cadence_alt_schedule` rejects duplicates, non-mixed targets, a production mixed set other than 33, and any production set inequality at [d2_truth_model.py:525](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:525).
- The builder invokes it and verifies one K=1 arm-B row per scheduled target at [build_d2_shards.py:579](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:579).
- `truth_d2` independently repeats both checks at [metrics_generalization.py:365](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:365).
- The focused cardinality test is at [test_d2_shards_contract.py:303](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:303).

Canonical-data probe: 103 targets, 33 unique mixed-cadence targets, and all 33 retain at least one mode under the 120-second endpoint.

5. **Mutually exclusive sensitivity axes and vocabularies — PARTIALLY RESOLVED**

- The exclusive-axis count is enforced at [d2_truth_model.py:393](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:393).
- `match` and `template_status` vocabularies are checked at [d2_truth_model.py:389](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:389).
- A self-consistent crossed ladder/phase/amplitude row was rejected in both the test at [test_d2_shards_contract.py:289](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:289) and my direct probe.

The `crowdsap` range check is incomplete; see NEW MAJOR below.

6. **`CD` layout wording — RESOLVED**

The executable comment and plan now consistently describe `AA TTTTTTTTTT K GR PS CD` at [d2_truth_model.py:73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:73) and [GENERALIZATION_PLAN.md:57](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:57).

## Shared validator and generation scope

These remain coherent.

- Builder and metrics both call `validate_manifest_frame` at [build_d2_shards.py:283](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:283) and [metrics_generalization.py:270](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:270).
- Generation scope is explicitly builder, truth model, and frozen import surface at [d2_truth_model.py:142](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:142).
- The generation ID covers source inputs, all template SHAs, frozen SHAs, scoped code, and arguments at [build_d2_shards.py:614](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:614).
- Metrics reproduces the basis and verifies current scoped code before consuming truth at [metrics_generalization.py:295](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:295).

Excluding runner/metrics from the generation ID appropriately permits analysis and driver corrections without changing shard identity.

## New findings

### MAJOR — Non-finite sentinel values bypass manifest semantics

At [d2_truth_model.py:386](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:386), `math.isfinite` is used both to infer whether `crowdsap` is present and to range-check it. Consequently, `crowdsap=inf` is treated as absent. A self-consistent nominal row with `crowdsap=inf` returned no validation error in a runtime probe. The same pattern permits non-finite, non-NaN “absent” `dropped_period_s` values and affects control/null emptiness checks at [d2_truth_model.py:440](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:440).

Exact fix: distinguish absence using `math.isnan`. Any non-NaN `crowdsap` must be finite and satisfy `0 < crowdsap <= 1`; absent `crowdsap`/`dropped_period_s` fields must be NaN exactly. Add tests for `inf`, `-inf`, and NaN in positive and control/null rows.

The current SPOC input is unaffected: all 20 available CROWDSAP values are finite and range from `0.0145` to `0.4158`.

### BLOCKING — The no-discretion runbook cannot launch the production D2 build or stratified pilot

The runbook declares itself “exact commands, no discretion” at [RUNBOOK.md:1](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:1), but:

- Its D2 build command at [RUNBOOK.md:53](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:53) omits required `--exposure-stars`, declared at [build_d2_shards.py:332](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:332).
- Its D2 run command at [RUNBOOK.md:59](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:59) omits required `--out-dir` and production-required `--shard-index`.
- It gives no D2 stratified-pilot command using `--stars-file <generation>/pilot_shard_index.txt`.
- D3 pilot/full commands likewise omit the now-required `--shard-index` at [RUNBOOK.md:37](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:37).

Exact D2 pilot shape:

```text
build_d2_shards.py --out-dir <fresh-generation> \
  --exposure-stars <attested-928-exposure-stars>

run_generalization_ls.py --shard-dir <fresh-generation> \
  --shard-index <fresh-generation>/shard_index.txt \
  --stars-file <fresh-generation>/pilot_shard_index.txt \
  --out-dir <pilot-run> --dataset d2-tess-dav \
  --replay-report <full-928-attestation> --work-root <scratch>
```

Add `--shard-index <d3_panels/shard_index.txt>` to both D3 runner invocations as well. The D2 arm/count description at [RUNBOOK.md:54](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:54) should also be updated from the obsolete five-arm/~2,957 statement to the current mandatory matrix/≤3,299.

There is no underlying data/code cardinality blocker once those arguments are supplied: production reasons were empty, the canonical cadence set passed 33/33, and the archived laptop attestation is a passing 928-star report for `Jacks_7i_5090`.

### MINOR — Output/test documentation is stale

- `METRICS_SPEC.md` does not list the new `d2_scenario_contrasts.csv` output at [METRICS_SPEC.md:252](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:252).
- The runbook still says 18 tests at [RUNBOOK.md:18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:18); current collection is 40.

Exact fix: add the contrast CSV to the output contract and update the test count.

## Runtime verification

- 40 tests collected.
- The read-only sandbox has no writable temporary directory, so the complete fixture-based suite could not run here.
- 25 non-temporary tests passed: all 13 truth-model tests, all 10 frozen-constant tests, cadence identity, and production-arm-matrix checks.
- Direct D1 audit reproduced 11/13 L-S, 9/13 census, and 13/13 union.
- No files were edited.

## Verdict: REJECT
