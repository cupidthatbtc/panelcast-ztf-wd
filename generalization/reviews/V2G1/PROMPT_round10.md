# V2G1 round 10 — confirmation of the round-9 fix (distinct dev-run manifest identities)

You are the methods reviewer of a pre-registered comparison (repository root is the
working directory; read-only). Your round-9 review is
`generalization/reviews/V2G1/sol_plan_review_r9.md` (VERDICT: REVISE on one item: the bound
`dev_runs` records did not have to carry four distinct manifest identities). The author
fixed it: `v2_common.validate_dev_run_records` now requires each record's `manifest` to be a
non-empty string and its `sha256` a SHA-256, and refuses any repeated `sha256` or repeated
`manifest` across the four records ("four distinct manifests are required"); the runner,
the lock and the comparison use that function unchanged. Tests: the reproducer you named
(one manifest identity, four records) is now a negative case in
`tests/test_v2_amendment_provenance.py` (both in
`test_validate_dev_run_records_rejects_junk_and_shallow_records` and at the end of the
authentic-runner test) and in `tests/test_v2_runner.py` (the registered runner refuses such
an artifact). See `git diff d481fcf -- scripts/v2/v2_common.py tests` and the last §10 entry
of `generalization/v2/V2_PLAN.md`. No holdout star has been scored; no lock exists.

Confirm, adversarially (cite file:line): (1) four distinct, well-typed manifest identities
are now required everywhere `dev_runs` is accepted; (2) nothing else regressed. End with
`VERDICT: ADMIT` or `VERDICT: REVISE` (minimal list).
