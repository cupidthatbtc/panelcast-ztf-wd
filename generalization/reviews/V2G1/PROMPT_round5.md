# Confirmation review (round 5) of the v2 pre-registration — ADMIT / REVISE

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1,
HEAD = the round-4 closure commit). Read-only. Same referee persona. Your single round-4 residual is
in `generalization/reviews/V2G1/sol_plan_review_r4.md`; the lead's dispositions are the fourth table
of `generalization/reviews/V2G1/RESPONSE.md`. Verify ONLY that residual:
`scripts/v2/run_v2_ls.py` (the guard block at the top of the split/holdout section of `main()`,
`registered_holdout`, the lock record), `scripts/generalization/metrics_generalization.py`
(`attestation_record_for` v2 branch; the sidecar loop's v2 pass-order check),
`scripts/v2/compare_engines.py::verify_registration`, and the tests
`tests/test_v2_runner.py::test_registered_holdout_refuses_debug_options_and_binds_passes`,
`test_copied_registration_root_cannot_score_canonical_holdout_ids`,
`tests/test_v2_metrics_engine.py::test_v2_holdout_manifest_requires_ordered_passes_and_registration`.
Try once more: score a canonical holdout id twice (different constants, code, pass order or
environment) or present a non-holdout run as the holdout, through any of the three programs.
Suite: 219/219 on the lead's machine. RESOLVED or the exact gap (file:line); then
`VERDICT: ADMIT` or `VERDICT: REVISE` with required changes. Terse.
