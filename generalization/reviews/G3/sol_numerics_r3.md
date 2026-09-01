## Runtime verification

The sandbox cannot create pytest temporary files, so `pytest tests/ -q` stopped before collection. Read-only-compatible checks found:

- **38 tests collected**: 10 frozen-constant, 13 truth-model, 15 contract cases.
- **24 non-temporary tests passed**; the remaining tmp-backed contract cases were inspected directly.
- Independent calculation from the current v3 report and mode table reproduced **33 mixed targets, 141 modes, exactly three 120-s rejections, zero unschedulable targets, and no dominance changes**.

## 1. Truth-table SHA enforcement — RESOLVED

`truth_d2` now:

- Requires exactly all six output hashes and verifies each before parsing a sidecar at [metrics_generalization.py:295](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:295).
- Reproduces `generation_id` from the recorded basis at [metrics_generalization.py:304](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:304).
- Requires current frozen-file and shard-determining-code identity at [metrics_generalization.py:309](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:309).
- Does not parse the manifest or mode tables until [metrics_generalization.py:323](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:323) and [metrics_generalization.py:342](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:342).

The parameterized test tampers with manifest, injected, rejected, index, and excluded files at [test_d2_shards_contract.py:247](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:247), and requires rejection at [test_d2_shards_contract.py:260](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:260).

## 2. Redilution fixture coverage — RESOLVED

The fixture supplies CROWDSAP 0.19 and explicitly schedules `redilution` at [test_d2_shards_contract.py:103](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:103) and [test_d2_shards_contract.py:110](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:110).

It asserts:

- One scheduled redilution shard at [test_d2_shards_contract.py:125](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:125).
- Identity differs from nominal only at zero-based digit 17, with CROWDSAP 0.19, at [test_d2_shards_contract.py:193](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:193).
- Injected amplitudes equal nominal amplitudes × 0.19 at [test_d2_shards_contract.py:199](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:199).

## 3. Amendment 3 — PARTIALLY RESOLVED

The core physics and identity implementation are correct:

- Cadence constants/scenario and mandatory arm: [d2_truth_model.py:84](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:84), [d2_truth_model.py:132](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:132).
- Immutable scenario code and final ID digit: [d2_truth_model.py:150](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:150), [d2_truth_model.py:327](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:327).
- Alt-row invariants prohibit ladder/phase/scale/dropout/crowding crossings and require arm B at 120 s: [d2_truth_model.py:383](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:383).
- `expected_counts["B:cadence_alt"]`: [d2_truth_model.py:490](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:490).
- v3 mixed-target selection uses `cadence_switched_from_roster`: [build_d2_shards.py:386](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:386).
- One K=1 120-s variant is constructed with retention reapplied inside `build_truth_model`: [build_d2_shards.py:471](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:471).
- The v3 report SHA enters the generation basis: [build_d2_shards.py:605](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:605).
- Metrics propagate and group by `cadence_code`: [metrics_generalization.py:399](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:399), [metrics_generalization.py:598](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:598).
- Headline surfaces are nominal arm B only: [metrics_generalization.py:1179](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1179).
- Amendment text appears at [GENERALIZATION_PLAN.md:240](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:240) and [G2_FREEZE.md:93](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:93); both recorded document SHAs match current bytes.
- Contract assertions cover the 150-s rejection, final digit 18, shared phases, K=1/120 s, expected count, and scenario separation at [test_d2_shards_contract.py:174](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:174) and [test_d2_shards_contract.py:331](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:331).

The current report itself records 33 switches at [v3_all103_verification_report.json:14](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/data/d2/spoc_verification/v3_all103_verification_report.json:14). Independent evaluation rejects only the three modes at [d2_modes.csv:47](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/data/d2/d2_modes.csv:47), while the 262.46-s, 7.19-ppt dominant mode remains at [d2_modes.csv:55](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/data/d2/d2_modes.csv:55).

## New findings

1. **MAJOR — production does not fail closed on 33 realized cadence-alt shards.** The builder conditionally appends targets only when they exist in the roster and retain a 120-s mode at [build_d2_shards.py:471](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:471), then sets the expected count from that potentially shortened list. The production assertion checks only that the report contains 33 entries at [build_d2_shards.py:579](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:579). Thus 33 report flags but 32 realized shards can still be labeled production.

   **Exact fix:** for production, require 33 unique report TICs, `set(cadence_alt_tics) == set(mixed_cadence)`, and exactly 33 manifest rows with `arm=B`, `scenario=cadence_alt`, `K=1`. Recheck the same conditions in `truth_d2`; add tests for an absent, duplicate, or zero-retention mixed TIC.

2. **MAJOR — the required same-subset, common-bootstrap cadence contrast is not implemented.** The plan requires nominal and `cadence_alt` on the same 33 K=1 targets using common bootstrap draws at [GENERALIZATION_PLAN.md:252](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:252). `d2_cluster_bootstrap` instead reports nominal over all scheduled targets/K strata and alt separately at [metrics_generalization.py:586](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:586). `sensitivity_table` does select the matched nominal subset, but emits separate Wilson rates without a paired/common bootstrap at [metrics_generalization.py:914](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:914).

   **Exact fix:** construct paired nominal-K1 and cadence-alt outcomes on the identical 33 TICs, assert one row per target/scenario, apply one bootstrap index matrix to both vectors, and report both estimates plus the paired difference and interval. Add a contract test that verifies identical membership and reused draws.

3. **MINOR — Amendment bookkeeping contains stale wording.**

   - Change the ID layout from `...C0` to `...CD` at [GENERALIZATION_PLAN.md:57](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:57), [d2_truth_model.py:73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:73), and the test comment at [test_d2_shards_contract.py:166](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:166).
   - Update the core maximum from 3,266 to 3,299 at [GENERALIZATION_PLAN.md:221](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:221).
   - The total “38” is correct, but change `10 + 14 + 14` to `10 + 13 + 15` at [G2_FREEZE.md:114](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:114).

## Verdict: APPROVE-WITH-CHANGES
