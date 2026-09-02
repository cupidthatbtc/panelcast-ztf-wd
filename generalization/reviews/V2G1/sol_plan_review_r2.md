Scope: preregistration tree `5ceb019`. Later tests/audit files were treated as supplementary, not part of that commit.

1. **RESOLVED.** Smoke stars are `dev_smoke`, excluded from both halves and rejected by registered runs; primary D3 counts are 299/1,149. `make_split.py:38-54`, `run_v2_ls.py:316-324`, `split_manifest.json:23-37`, `V2_PLAN.md:165-172,262-264`.

2. **RESOLVED.** The holdout is correctly described as internal post-selection validation, with no alternative partition evaluated. `V2_PLAN.md:26-33,268-272`.

3. **PARTIAL.** For a fixed trend window, offline re-scoring is exact; see (a). The selector is not:

   - `combination_id` omits trend window and produces only 27 IDs. `rescore_v2.py:45-58`.
   - `dev_tuning.py` accepts one D3 and one D2 table, not both trend-window runs; it neither asserts 54 combinations nor expected denominators. `dev_tuning.py:103-119`.
   - Missing D2 evidence is allowed and treated as satisfying the null constraint. `dev_tuning.py:82-93,105-118`.
   - P2 uses v2 usability, not the frozen P2 frame. `dev_tuning.py:63-68`.
   - Tie ordering is not §3 candidate order, and no `tuning_constraint_failure` is written. `dev_tuning.py:95-100`.
   - It writes `chosen_overrides.json`, not the required digest/evidence-bound `V2_CONSTANTS_FROZEN.json`. `dev_tuning.py:120-126`.

4. **NOT RESOLVED.** The normal registered path locks one configuration, but “holdout once” remains bypassable; see (b). The artifact also verifies only v2/split/plan hashes—not preregistration commit or tuning-evidence digest—and the lock creation is non-atomic. `run_v2_ls.py:183-220`. The test explicitly accepts arbitrary preregistration value `"deadbeef"`. `tests/test_v2_runner.py:109-111,133-136`.

5. **RESOLVED.** D3 is roster-based; non-runner missing rows become failures, while unexplained missing runner rows abort. `compare_engines.py:247-276`. Canonical holdout denominators are 299 flag1 and 1,149 flag0.

6. **RESOLVED.** Primary P2 uses the frozen-usable frame; v2 usability only defines the sensitivity frame. `compare_engines.py:217-222`. The actual holdout primary frame is n=211.

7. **PARTIAL.** B/seed, two-sided McNemar, CP upper, and both P4 variants are implemented. Remaining gaps:

   - No exact discordance-bound fallback: zero discordances produce the overconfident interval `[0,0]`. `compare_engines.py:96-107`.
   - Chance-match inputs are optional and merely copied into the manifest, not required beside P2. `compare_engines.py:288-314`.
   - Paired-control code implements trigger contrast only, not strict-recovery contrast. `compare_engines.py:165-205`.

8. **PARTIAL.** The split itself is correct: 500 dev nulls; holdout has 129 nominal-B shards across 43 targets, 67 controls, and 500 nulls; crossings are disclosed. `make_split.py:58-108,132-136`, `split_manifest.json:235-280`. However, D2 comparison filters on an arbitrary supplied runner list without checking its registered SHA, permitting denominator reduction. `compare_engines.py:247-252,286-298`.

9. **RESOLVED.** Shared-night weighted-median alignment, five-night threshold, unshifted flag, and recorded overlap counts are implemented. `align.py:50-65,93-117`; sensitivity is declared at `V2_PLAN.md:256`.

10. **PARTIAL.** Leakage and veto-exposure outputs are declared, but commit `5ceb019` contains no implementing audit scripts. Worse, contradictory claims remain: “cannot inject or remove power” in `detrend.py:18-21` and “science frequencies are untouched by construction” in `window.py:21-22`. Paired-control recovery is also absent.

11. **RESOLVED.** The plan correctly calls coherence operational, excludes phase errors from the decision, and prespecifies stratification. `V2_PLAN.md:115-119,256`; rule code remains deterministic at `multiband.py:92-98`.

12. **PARTIAL.** Machine/split/half/list keys were added, and the revision is committed. Remaining provenance gaps:

   - Metrics-sidecar verification omits holdout `plan_sha256` and `preregistration_commit`. `metrics_generalization.py:1503-1509`.
   - Registered holdout does not validate preregistration commit or evidence digest. `run_v2_ls.py:193-209`.
   - Comparison does not read or bind either metrics manifest; constants and chance artifacts are optional. `compare_engines.py:279-327`.
   - Split/runner-list hashes are recorded but not checked against `split_manifest.json`.

13. **PARTIAL.** Combined-T peak separation is correctly supplied by `analyze_star_v2.py:178-180,204-213`, and subset artifacts are gone. A stale subset/3-day-ladder description remains in `dev_tuning.py:4-7`; `multiband.py:14-16` also still describes the superseded alias-first/cap-30 clustering.

Specific checks:

- **(a) Exactness:** Confirmed for a fixed trend window. Candidate membership is veto-independent (`multiband.py:101-120`), while re-scoring derives window vetoes, cross-pass aliases, joint top-five, coherence, status, candidate ranking, and best pass solely from recorded candidate/series/window diagnostics. `rescore_v2.py:61-141`. The only external dependencies are fixed registered code/constants (`fixed_loci`, `decide`, `overall_result`); no light curve or periodogram is reread.

- **(b) Holdout attack:** Construction succeeds. After one registered run, run the same `d3_holdout.txt` into another output directory with `--allow-nonstandard-ids`, omit `--split-file`, and supply a different inline declared constant. The branch at `run_v2_ls.py:313-327` skips `registered_holdout`, so no lock is consulted. Different code likewise receives a self-consistent new v2 binding. Alternatively, copy the registration files to another directory: the lock location derives from `split_file.parent` (`run_v2_ls.py:183-201`), yielding another lock. `compare_engines.py` does not verify registration manifests, so either result can subsequently be presented as holdout.

- **(c) Frames:** With the canonical files, confirmed: D3 299 flag1/1,149 flag0; D2 129 B shards = 43 targets, 67 distinct controls, 500 nulls. Missing-status rows score as failures; absent listed v2 rows abort, never silently exclude. The qualification is that D2’s supplied runner list is not authenticated, so these denominators are not enforced.

Required changes:

- Repair `dev_tuning.py` to ingest both trend windows, label/assert all 54 combinations and denominators, use frozen P2 usability, implement the registered tie/failure rule, and emit the evidence-bound constants artifact.
- Close holdout bypasses: canonical registration paths/hashes, holdout-ID protection in debug mode, atomic exclusive lock creation, and preregistration/evidence verification.
- Require and bind both metrics manifests, the registered runner list, split, constants artifact, and holdout lock in comparison.
- Add the exact discordance bound, mandatory chance-match output, and strict-recovery paired-control contrast.
- Commit the declared audit implementations and remove stale contradictory documentation.

VERDICT: REVISE