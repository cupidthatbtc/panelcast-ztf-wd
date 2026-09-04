# V2G1 round 9 — confirmation of the round-8 revision

You are the methods reviewer of a pre-registered comparison (repository root is the
working directory; read-only). Your round-8 review is
`generalization/reviews/V2G1/sol_plan_review_r8.md` (VERDICT: REVISE: completion check read
a nonexistent key, shallow sidecar/record validation, a documented restart path that could
destroy the old-digest dev results, stale SUMMARY count, RUNBOOK example). The author
revised; see the last §10 entry of `generalization/v2/V2_PLAN.md` ("round-8 revision") and
`git diff 5c1d860 -- scripts/v2 tests generalization/v2 generalization/RUNBOOK.md
generalization/writing/outline`. No holdout star has been scored; no lock exists; the
laptop dev chain is still on its dev stages (the pinned chain and restart scripts were
already staged on the laptop; the running chain process is unaffected).

Verify adversarially (cite file:line):

1. Completion and schema. `v2_common.run_completion` reads the runner's own fields
   (`source_count`, `pending_at_start`, `completed_now`; missing → SystemExit).
   `v2_common.dev_run_record` is the single check used by `rescore_v2.verify_run_manifest`,
   by `dev_tuning.verify_dev_run_manifests` and (through `validate_dev_run_records`) by the
   registered runner and the comparison: engine, dev-run digest, dev half, no failures, no
   `--limit`, §5 schedule, registered list SHA (top-level AND binding), completion == list
   length. `tests/test_v2_amendment_provenance.py::test_authentic_runner_manifest_is_verified_by_the_same_record_check`
   runs the real runner in registered dev mode and checks the record on its manifest.
   Anything still accepted that should not be?
2. Sidecars and records. `dev_tuning.verify_rescore_provenance` matches each sidecar to
   its run by manifest SHA and checks dataset / window / list SHA against THAT record,
   the source and re-score digests, the table bytes, and one-to-one coverage of the four
   runs. `validate_dev_run_records` requires exactly four well-formed records mapping
   one-to-one onto the schedule, each with a SHA-256, the dev-run digest, the registered
   list SHA and its completion; the runner refuses an artifact whose `dev_runs` fails it
   ("junk", duplicates, wrong list SHA, wrong digest are tested in
   `tests/test_v2_runner.py`), the lock records `dev_runs`, and the comparison requires
   lock `dev_runs` == artifact `dev_runs` and validates them.
3. Restart path. `scripts/v2/v2_laptop_chain.ps1` is pinned to the dev-run digest in the
   script itself (the mutable expected-digest file is no longer read by the dev chain) and
   refuses to start once `v2_chain.log` carries "V2 DEV RUNS DONE"; `v2_chain_restart.ps1`
   refuses likewise; `v2_holdout_laptop.ps1` refuses before "V2 DEV RUNS DONE", requires
   the expected digest, refuses the dev-run digest; `sync_laptop.sh` stages the pinned
   chain + restart scripts BEFORE writing the amended expected digest. Is any documented
   path left that recomputes or deletes the old-digest dev outputs?
4. `SUMMARY.md` (35 items, N35 named), `RUNBOOK.md` step 3 (`--run-manifest`). Anything
   misleading left?

Tests: 277 passed. End with `VERDICT: ADMIT` or `VERDICT: REVISE` (minimal list).
