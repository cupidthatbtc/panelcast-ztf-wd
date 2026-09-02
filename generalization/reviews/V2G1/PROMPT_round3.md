# Confirmation review (round 3) of the v2 pre-registration — ADMIT / REVISE

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1,
HEAD = the round-2 revision commit). Read-only. Same referee persona. Your round-2 findings are in
`generalization/reviews/V2G1/sol_plan_review_r2.md`; the lead's round-2 dispositions are the
second table of `generalization/reviews/V2G1/RESPONSE.md`. Verify ONLY the round-2 residuals
(findings 3, 4, 7, 8, 10, 12, 13 and your specific checks (a)–(c)) against the revised
`generalization/v2/V2_PLAN.md` (§5, §6, §8, §10) and the code: `scripts/v2/rescore_v2.py`
(combination labels), `scripts/v2/dev_tuning.py`, `scripts/v2/run_v2_ls.py`
(registration_root, canonical_holdout_ids, registered_holdout, the unregistered-path guard),
`scripts/v2/compare_engines.py` (verify_registration, paired_rate_row discordance bound,
d2_control_contrast_rows), `scripts/generalization/metrics_generalization.py::sidecar_binding_keys`,
`scripts/v2/analysis/*.py`, and the tests `tests/test_v2_runner.py`, `tests/test_v2_compare.py`,
`tests/test_v2_rescore.py` (suite 215/215).

Repeat check (b): try again to score the holdout twice with different constants or code, or to
present an unregistered run as the holdout, without tripping a guard — through the runner
(including the V2_REGISTRATION_ROOT variable), the metrics (`--engine v2`) or the comparison.
State each residual precisely (file:line) or RESOLVED.

End with `VERDICT: ADMIT` or `VERDICT: REVISE` plus the list of required changes (if any). Terse.
