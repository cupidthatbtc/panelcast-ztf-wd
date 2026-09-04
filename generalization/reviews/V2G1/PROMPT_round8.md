# V2G1 round 8 — confirmation of the round-7 revision (fail-closed dev-run provenance)

You are the methods reviewer of a pre-registered comparison (repository root is the
working directory; read-only). Your round-7 review of the 2026-09-04 veto amendment is
`generalization/reviews/V2G1/sol_plan_review_r7.md` (VERDICT: REVISE, three required
changes). The author revised; the revision is the last §10 entry of
`generalization/v2/V2_PLAN.md` ("2026-09-04, round-7 revision") and the commit after
`017c925`. Run `git log --oneline -4` and `git diff 017c925 -- scripts/v2 tests generalization/v2
generalization/RUNBOOK.md generalization/writing/outline` to see it. No holdout star has been
scored; no holdout lock exists; the laptop dev chain is still on its dev stages.

Verify each required change adversarially (cite file:line):

1. Provenance fail-closed. `scripts/v2/rescore_v2.py` now requires `--run-manifest`,
   refuses (`verify_run_manifest`) anything but a completed dev run at the compiled
   `DEV_RUNS_V2_DIGEST` re-scoring its own stars directory, and writes
   `<table>.provenance.json`. `scripts/v2/dev_tuning.py` requires `--dev-run-manifests`
   (exactly four), verifies them (`verify_dev_run_manifests`: engine, digest, half, no
   failures, registered list SHA, completion via total − pending_at_start + completed_now,
   the §5 (dataset, window) schedule), verifies every re-score sidecar
   (`verify_rescore_provenance`), verifies the pre-registration commit is an ancestor of the
   compiled `VETO_AMENDMENT_COMMIT`, and binds `dev_runs`, `dev_runs_v2_digest`,
   `veto_amendment_commit` into the artifact. `scripts/v2/run_v2_ls.py` (registered mode)
   and `scripts/v2/compare_engines.py` verify those fields against the compiled constants;
   the lock records them. Tests: `tests/test_v2_amendment_provenance.py`, the runner
   negative cases in `tests/test_v2_runner.py`. Is any path still open where a wrong
   source digest, a partial run, a holdout run or a foreign manifest is silently accepted?
   Is compiling the constants into `v2_common.py` (inside the digest) the right reference,
   or does it create a circularity you object to?
2. Laptop sequence. `scripts/v2/analysis/sync_laptop.sh` is now holdout staging only:
   refuses without the artifact, refuses until the laptop chain logged "V2 DEV RUNS DONE",
   copies code + plan + lists + `dev_tuning.csv` + artifact + the holdout script, verifies
   parity, writes the expected digest, never restarts the chain.
   `scripts/v2/analysis/dev_mac_sequence.sh` pulls and re-scores first (with
   `--run-manifest`), then the tuning step; its DONE message orders: §10 tuning entry →
   re-run the tuning step (plan_sha256 bound) → commit → staging → laptop pull → holdout.
   `generalization/RUNBOOK.md` step 3 says the same. Can the old-digest dev results still
   be destroyed or re-scored twice by any documented path?
3. Wording and freeze. §5 freezes the veto from `017c925` onward; §10 calls the change
   dev-derived; the exposure numbers are labelled a full-cohort truth audit; `window.py`'s
   docstring no longer claims the fixed loci avoid the science bands; the outline's
   limitation ranges read N29–N35. Anything misleading left?
4. Anything else that must change before the holdout.

Tests: 268 passed. End with `VERDICT: ADMIT` or `VERDICT: REVISE` (minimal list).
