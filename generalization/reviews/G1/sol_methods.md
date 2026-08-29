Verdict: **request changes before campaign execution.** The five frozen files currently match their hardcoded hashes and the tag diff is empty, but the architecture does not yet enforce the claimed replay/environment/data freeze.

1. **BLOCKER — The replay gate does not actually block campaign runs.**  
   [run_generalization_ls.py:94](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:94) calls only `assert_frozen()`; it never requires or validates a replay report. Any machine/environment can launch the campaign.  
   Minimal fix: require a replay attestation whose `passed`, environment fingerprint, frozen hashes, worker/thread configuration, and reference-data hashes match the current run—or invoke the gate automatically.

2. **BLOCKER — The replay gate can pass vacuously.**  
   [replay_gate.py:207](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/replay_gate.py:207) permits `strict_v2 or not has_v2`. Thus `--count 0` passes with zero stars, and an explicit all-v1 list can pass without the mandatory v2 control. Missing v2 shards are also silently tolerated.  
   Minimal fix: require a nonempty canonical roster, `strict_v2` unconditionally, and exact expected schema counts—currently 7 v2 plus 18 fixed v1 controls.

3. **BLOCKER — The stated v1→v2 history is materially inaccurate.**  
   [GENERALIZATION_PLAN.md:51](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:51) says `fa16d7f` changed no numeric path. Its actual diff added sparse-high-pass and no-candidate control branches, visible at [run_catalog_lomb_scargle.py:126](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_catalog_lomb_scargle.py:126) and [run_catalog_lomb_scargle.py:175](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_catalog_lomb_scargle.py:175). All seven v2 records exercise the new unavailable-high-pass behavior.  
   The downgrade function itself is conservative—it removes only the new fields and byte-compares everything retained—but the historical argument is not airtight.  
   Minimal fix: correct the plan, pin both pre- and post-commit hashes, and replay/differential-test all 921 v1 stars.

4. **MAJOR — Twenty-five stars are not enough for an environment acceptance proof.**  
   [replay_gate.py:100](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/replay_gate.py:100) takes lexicographic v2 files and stride-samples v1 files; it is not stratified by baseline/grid size, status, near-threshold FAP, peak ties, aliases, or numerical branch. Backend drift can affect only boundary cases and evade 18 v1 controls.  
   Minimal fix: replay all 928 once per accepted machine/environment. If that is infeasible, freeze a branch- and boundary-coverage roster, including all seven v2 stars, and separately establish a full 928-star baseline on the production environment.

5. **BLOCKER — The numerical environment has contradictory and incomplete pins.**  
   The plan says the imported NumPy was 2.3.5, while [requirements-frozen.txt:2](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/requirements-frozen.txt:2) and [FROZEN_ENV.md:8](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/FROZEN_ENV.md:8) say 2.3.3. Python is documentary rather than enforced; transitive dependencies, wheel hashes, BLAS/LAPACK vendor, CPU features, Windows CRT/libm, and `OMP_NUM_THREADS`/OpenBLAS/MKL settings are unpinned. `env_versions()` merely records a small subset after execution.  
   Minimal fix: resolve the NumPy authority, hash-lock exact wheels and Python installer/container, assert versions before work, and capture backend/configuration, CPU, OS build, and numerical thread variables.

6. **BLOCKER — IERS/BJD generation is outside the replay gate.**  
   [build_catalog_panels.py:182](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/build_catalog_panels.py:182) computes BJD using Astropy `Time` and observatory position. Results can depend on the active IERS table/cache, auto-download state, leap-second data, ephemeris setting, ERFA build, and platform numerics. The L-S replay consumes already-generated `bjd_tdb`, so it cannot detect this drift.  
   Minimal fix: vendor and SHA-pin the exact IERS table, disable auto-download, set the ephemeris explicitly, and add a panel-stage golden replay that byte-compares fixed exposure shards including `bjd_tdb`.

7. **BLOCKER — Scientific inputs and replay references are not bound to content.**  
   The L-S manifest records only a shard path at [run_generalization_ls.py:182](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:182). The panel manifest records a roster path but no roster/cache/shard hashes. The frozen fetcher skips any nonempty cache file at [fetch_catalog_lightcurves.py:102](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/fetch_catalog_lightcurves.py:102), while its full-history query has no observation cutoff. D3 raw data is git-ignored. Although the published bundle has `SHA256SUMS`, the replay gate never validates it and accepts arbitrary `--published-stars` and shard directories.  
   Minimal fix: create and assert a content-addressed input manifest covering raw responses, roster, coordinates/query, cutoff/acquisition time, every shard, and published golden JSONs.

8. **BLOCKER — Resume can silently attribute old results to new inputs or environments.**  
   [run_generalization_ls.py:58](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:58) skips a JSON solely because `complete` is true and requested pass names exist. It does not bind the result to the shard hash, environment, replay attestation, driver, or frozen hashes. The final manifest then records the current environment, potentially misrepresenting reused outputs. Only pending IDs are validated.  
   Minimal fix: write a provenance sidecar per result and reuse only when source ID, shard SHA, passes, frozen/campaign SHAs, environment, and gate certificate all match.

9. **MAJOR — Campaign/adaptor code is neither frozen nor recorded.**  
   [frozen_api.py:34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/frozen_api.py:34) hashes only the five core files. `frozen_api` itself, the runner, panel adapter, truth/shard builders, and metrics implementation can change while manifests continue reporting identical frozen-core hashes.  
   Minimal fix: freeze a campaign release commit before the first run and record SHA-256 for every campaign script and specification in every stage manifest.

10. **MAJOR — Module resolution can bypass the files that were hashed.**  
    [frozen_api.py:112](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/frozen_api.py:112) inserts `SCRIPTS_DIR` only if it is absent. An earlier path entry—or a module preloaded in `sys.modules` by `sitecustomize`—can supply `run_catalog_lomb_scargle` while `assert_frozen()` hashes a different file.  
    Minimal fix: reject preloaded frozen module names, force the verified directory to index 0, and after import assert every module’s resolved `__file__` and content hash.

11. **MAJOR — `verify_cli_identity.py` does not run the frozen CLI.**  
    Its “CLI” arm directly imports and calls the same function in a fresh interpreter at [verify_cli_identity.py:26](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/verify_cli_identity.py:26). This is a useful import-side-effect/determinism check, but it does not verify `main()` plumbing, fixed pass selection, sanity gates, discovery, or resume behavior. The campaign also permits arbitrary pass lists at [run_generalization_ls.py:85](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:85), whereas the frozen CLI always uses both passes.  
    Minimal fix: narrow the claim to “same per-star callable,” enforce exactly `("low", "high")` in production, and add a real subprocess integration test of the frozen CLI on an isolated published-star run directory.

12. **MAJOR — Worker/scratch preflight does not implement the documented bound.**  
    [run_generalization_ls.py:38](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:38) caps against requested/physical workers, not the documented 22. A large explicit request can exceed physical cores; zero is treated as default; negative values survive until executor failure. `max(1, …)` starts one worker even when the formula says scratch cannot support one. The published maximum baseline requires about **0.470994 GB** for the three high-pass memmaps, already slightly above the stated 0.47 GB; D3’s later full-history baseline can be longer. The 50% reserve masks the present rounding error but does not make 0.47 a proven bound. Replay has no disk preflight at all.  
    Minimal fix: derive scratch bytes from each shard’s actual baseline/grid, validate positive worker requests, use `min(22, physical, requested, disk ceiling)`, fail if the ceiling is zero, and give replay a separate `--work-root` with the same check.

13. **MAJOR — Reused directories and overlapping shard jobs can introduce stale or corrupted inputs.**  
    [build_panels_generic.py:92](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_panels_generic.py:92) reuses an existing output directory without removing or indexing obsolete shards. The runner then globs every `*.csv.gz` at [run_generalization_ls.py:47](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:47). Concurrent overlapping jobs also share `work_root/source_id` memmaps and the same `.json.part`, with no lock.  
    Minimal fix: require fresh immutable stage directories, consume an exact roster-derived shard index, reject extras, and use per-source locks plus run-unique scratch paths.

14. **MINOR — The constants tests do not pin several claims they advertise.**  
    `test_frozen_shas_match_tag` at [test_frozen_constants.py:20](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_frozen_constants.py:20) never resolves the tag or its commit. The duplicate-bound test only proves that three literals occur somewhere, not that relevant conditions use them. The campaign-ID test manually slices a literal but never checks that bootstrap scripts still use `int(source_id[-9:])`.  
    Minimal fix: hardcode the frozen commit ID, compare Git blobs to the SHA map, hash any campaign-used bootstrap scripts, and test the actual seed/pass-bound AST expressions.

15. **MINOR — Final integrity is recorded but not enforced.**  
    The runner uses `frozen_file_shas()` rather than `assert_frozen()` in its final manifest at [run_generalization_ls.py:184](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:184). A mid-run filesystem change can therefore leave a successful run with mismatching hashes.  
    Minimal fix: call `assert_frozen()` again before successful completion and fail if the campaign-code or input hashes changed.

The strongest existing pieces are the strict retained-field byte comparison, atomic JSON replacement, and current five-file hash match. They are good foundations, but the blockers above mean “frozen pipeline” presently describes intent rather than an enforced end-to-end invariant. I made no file changes; the current shell lacked the campaign’s SciPy/Astropy/pytest environment, so this was a static/history-backed review rather than an execution replay.
