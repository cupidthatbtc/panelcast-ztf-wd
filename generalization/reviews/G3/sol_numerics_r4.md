All round-3 findings are resolved. I found no new numerics or physics issue.

1. Cadence-alt production identity — RESOLVED

- `check_cadence_alt_schedule` rejects duplicate scheduled targets, non-mixed targets, a production mixed set other than exactly 33 unique TICs, and any production set inequality ([d2_truth_model.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:525)).
- The builder invokes it and then requires exactly one K=1 arm-B manifest row per scheduled target ([build_d2_shards.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:579)).
- `truth_d2` independently repeats both schedule and manifest-row checks ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:365)).
- `test_cadence_alt_schedule_identity` covers the valid 33-set, 32 realized, 32 reported, non-mixed target, and non-production subset cases ([test_d2_shards_contract.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:303)).
- Current data contain 33 unique mixed TICs, all present in the 103-target roster and all retaining at least one mode at 120 s.

2. Paired common-bootstrap contrasts — RESOLVED

- `d2_cluster_bootstrap` returns `(table, contrasts)` and creates one frozen draw matrix shared throughout ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:580)).
- Every non-nominal arm-B scenario is processed; duplicate scenario rows are rejected, and nominal K=1 must have exactly the same target membership ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:724)).
- Usable contrasts take the intersection usable on both sides; eligible contrasts retain all paired targets and encode missing results as failures ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:736)).
- The same draws are applied to scenario, nominal-K1, and paired-difference vectors, producing `p_scenario`, `p_nominal_k1`, `diff`, and their intervals ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:750)).
- Output is written to `d2_scenario_contrasts.csv` ([metrics_generalization.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1293)).
- The contract test verifies scenario membership, paired point estimates, common-draw labeling, and symmetric missingness behavior ([test_d2_shards_contract.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:372)).

3. Wording and frozen counts — RESOLVED

- The plan uses `AA TTTTTTTTTT K GR PS CD` ([GENERALIZATION_PLAN.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:57)).
- The source header and test comment use the same layout ([d2_truth_model.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:73), [test_d2_shards_contract.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:168)).
- The core maximum is 3,299 ([GENERALIZATION_PLAN.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:221)).
- The freeze records 40 tests as 10 frozen-constant + 13 truth-model + 17 contract ([G2_FREEZE.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:130)); source inspection confirms that collected-case count.

Production-readiness assessment — RESOLVED

Independent calculation from the current truth tables reproduced:

- 103 scheduled targets
- 76 dropout targets
- 33/33 realizable cadence-alt targets
- Three 120-s mode rejections, all on TIC 55650407
- 20 redilution targets

The reported 3,102 shards reconcile as 3,082 core shards plus 20 redilution shards, implying 119 unique controls and leaving 217 shards of headroom below the conservative 3,299 core maximum. The reported all-`tol_0.25` assignments add no numerical concern.

The laptop generation itself is not present for row-level inspection, but production will be revalidated by both the builder and `truth_d2`; this is an operational provenance check, not an unresolved numerics issue.

Runtime note: workspace HEAD is `1dc35ae`; `2ad86a5` is its immediate ancestor, and the intervening commit adds only the two round-4 prompt files. Full pytest could not start because the sandbox has no writable temporary directory. I inspected all test cases and directly ran 25 read-only tests successfully.

New findings: none.

## Verdict: APPROVE
