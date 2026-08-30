All three round-4 findings are functionally resolved. No BLOCKING or MAJOR issue remains. I found two documentation-only MINOR cleanups, so the closure verdict is APPROVE-WITH-CHANGES.

## Per-item verification

1. MAJOR non-finite manifest semantics — RESOLVED

- `crowdsap` presence is now defined by `not math.isnan`; present values must be finite and satisfy `0 < crowdsap <= 1` at [d2_truth_model.py:386](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:386).
- `dropped_period_s` uses the same NaN-exact presence rule and requires a finite positive value at [d2_truth_model.py:412](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:412).
- Control/null rows require both absent floats to be NaN exactly at [d2_truth_model.py:446](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:446).
- The focused contract test covers `±inf` across positive `crowdsap`, positive `dropped_period_s`, control, and Gaussian-null victims, plus NaN dropout/redilution failures at [test_d2_shards_contract.py:301](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:301).

Direct `_row_problem` probes confirmed:

- Nominal/control/null absence: NaN accepted; `±inf` rejected.
- Dropout `dropped_period_s`: NaN and `±inf` rejected.
- Redilution `crowdsap`: NaN and `±inf` rejected.
- `crowdsap`: smallest positive finite value and `1.0` accepted; `0`, negative, `>1`, and `±inf` rejected.
- `dropped_period_s`: positive finite values accepted; zero, negative, and `±inf` rejected.

2. BLOCKING production/pilot runbook — RESOLVED

- D2 generation includes `--exposure-stars` and the complete arm list at [RUNBOOK.md:59](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:59).
- The mandatory matrix states 3,102 current shards and core ≤3,299 at [RUNBOOK.md:64](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:64).
- The stratified pilot carries `--shard-index`, `--stars-file .../pilot_shard_index.txt`, `--out-dir`, `--work-root`, and `--replay-report` at [RUNBOOK.md:73](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:73).
- The full-run transformation is explicit at [RUNBOOK.md:82](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:82), and D2 metrics supplies `--shards-dir` and `--run-manifest` at [RUNBOOK.md:85](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:85).
- D3 pilot includes `--shard-index`; the full run inherits it from the same command at [RUNBOOK.md:37](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:37) and [RUNBOOK.md:45](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:45).
- Runtime parser probes of the documented D2 generation, pilot, full, and metrics commands and both D3 runner forms all exited successfully.

3. MINOR stale output/test documentation — RESOLVED

- The runbook reports 40 tests at [RUNBOOK.md:18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:18).
- The output contract lists both `d2_cluster_completeness.csv` and `d2_scenario_contrasts.csv` at [METRICS_SPEC.md:258](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:258).
- Current collection produced exactly 40 tests. The 25 tests not requiring temporary storage passed. The complete fixture-backed suite could not run in this read-only sandbox because pytest has no writable temporary directory.

4. Amendment 2/3 ledger and SHAs — RESOLVED

- The Amendment 2 hashes at [G2_FREEZE.md:63](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:63) reproduce the historical `b7c4092` blobs.
- The Amendment 3 round-4 hashes at [G2_FREEZE.md:107](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:107) reproduce the historical `2ad86a5` blobs.
- The final post-round-4-edit hashes at [G2_FREEZE.md:142](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:142) match the current bytes exactly:
  - `METRICS_SPEC.md`: `b59ec7e44f310e8bb945d219c07b0c6fd5abf2ad4bbe9d067da38cd83b156cf2`
  - `GENERALIZATION_PLAN.md`: `6b28b634f0abb96230c49eeb98463d6ba8c7c406b6dbddae54894d65f1f09ae6`

## New findings

MINOR — two redundant/stale documentation fragments:

- [RUNBOOK.md:19](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:19) still labels CLI identity “PENDING,” although the archived laptop report records `passed: true` at [identity_report.json:2](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/attestation/laptop_cli_identity_2026-08-30/5453725283205041024.identity_report.json:2). Exact fix: replace the pending note with the 2026-08-30 laptop PASS and archived-report path.
- [METRICS_SPEC.md:260](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:260) repeats `d2_cluster_completeness.csv` immediately after the combined listing. Exact fix: remove that second occurrence and update the ledger’s current spec SHA to `5dcf326bd18f669fa6703d1ae176e56e6020a62959107c267d38f3933d4f68ba`.

These are documentation-only and do not affect execution or provenance enforcement.

The archived laptop replay report is a passing 928-record, 928-unique attestation whose IDs exactly equal the published catalog set at [replay_report.json:2](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/attestation/laptop_replay_full_2026-08-29/replay_report.json:2). Therefore, with the current checkout and laptop-resident exposure shards/report, the production D2 generation may be built and the stratified pilot may run on `Jacks_7i_5090`.

No files were edited.

## Verdict: APPROVE-WITH-CHANGES
