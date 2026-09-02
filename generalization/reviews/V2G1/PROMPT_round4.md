# Confirmation review (round 4) of the v2 pre-registration — ADMIT / REVISE

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1,
HEAD = the round-3 closure commit). Read-only. Same referee persona. Your round-3 residuals are in
`generalization/reviews/V2G1/sol_plan_review_r3.md`; the lead's dispositions are the third table of
`generalization/reviews/V2G1/RESPONSE.md`. Verify ONLY the two round-3 residuals:

1. Holdout bypass (your finding 4 / check (b)): `scripts/v2/run_v2_ls.py` (`canonical_holdout_ids`,
   `registration_root`, the guard block after the split/holdout branch in `main()`),
   `scripts/generalization/metrics_generalization.py::attestation_record_for` (v2 branch),
   `scripts/v2/compare_engines.py::verify_registration`, and the tests
   `tests/test_v2_runner.py::test_copied_registration_root_cannot_score_canonical_holdout_ids`,
   `test_debug_runs_cannot_touch_registered_holdout_ids`,
   `tests/test_v2_metrics_engine.py::test_v2_holdout_manifest_requires_canonical_registration`.
   Try once more to score a canonical holdout id twice (different constants or code) or to present
   a non-holdout run as the holdout, through the runner (any root), the metrics or the comparison.
2. Chance-match validation and binding, and the discordance docstring: `compare_engines.py` (module
   docstring; the chance block in `main()`; `inputs.update(chance_files)`).

Suite: 217/217 on the lead's machine. State each residual RESOLVED or give the exact gap (file:line).
End with `VERDICT: ADMIT` or `VERDICT: REVISE` plus required changes (if any). Terse.
