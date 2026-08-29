## Verdict: not freezable

The frozen numerical core replay is encouraging, but the campaign shell and D2 artifacts still permit silent provenance or truth misassociation.

1. **BLOCKER — Replay attestation does not bind the environment or replay scope claimed in the response.**  
   [run_generalization_ls.py:34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:34) excludes `numpy_blas`, `omp_num_threads`, `openblas_num_threads`, and `platform` from comparison, despite those fields being recorded by [frozen_api.py:96](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/frozen_api.py:96). It also accepts any truthy `passed` report without validating `gate`, unique star roster, or count. Consequently, completing the 928 replay will not make the driver require that stronger report.  
   Minimal fix: compare the complete canonical environment fingerprint, require `gate == "replay_gate"` and `passed is True`, and bind the accepted unique-star roster/count or digest—928 after the full replay passes.

2. **MAJOR — “`campaign_file_shas()` in every manifest” is not faithfully implemented.**  
   The runner records it, but the explicit panel manifest at [build_panels_generic.py:170](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_panels_generic.py:170), replay report, D2 shard summary, and both roster reports omit campaign SHAs.  
   Minimal fix: record initial and final campaign hashes in every stage artifact and fail if they change during the stage.

3. **MAJOR — Control IDs are subset-dependent and can silently change meaning.**  
   Controls are assigned serial IDs by sorting only templates used in the current invocation at [build_d2_shards.py:218](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:218). Comparing a 10-target pilot with the full roster, all 27 shared controls changed IDs. Combined with reusable output directories and result skipping at [run_generalization_ls.py:90](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:90), an existing `95…` result can be attributed to a different window.  
   Minimal fix: derive control IDs from a stable index over the fixed 928-window pool or a collision-checked hash; add `control_campaign_id` to every arm-B row; require a clean shard directory or reject extras.

4. **MAJOR — Exact post-sinc injection truth is not preserved.**  
   [d2_truth_model.py:127](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:127) correctly rejects modes, but [build_d2_shards.py:207](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:207) records only counts—not retained/rejected frequencies and amplitudes. Current data contain one genuinely rejected mode: TIC 220555122, 137.54 s. A scorer joining the original mode table can therefore match a frequency that was never injected. The summary also reports 14 rejected modes because it sums that one rejection across variants.  
   Minimal fix: emit a per-shard retained/rejected truth table and require scoring from it; report unique target-mode rejections separately.

5. **MAJOR — Builder input provenance is not content-faithful.**  
   [build_d2_roster.py:174](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_roster.py:174) hashes the tarballs but parses separately extracted `.tex` files at line 178. Those consumed files can change without changing the reported hashes. Neither roster report hashes its generated roster/mode outputs.  
   Minimal fix: hash every consumed extracted file and every generated roster/mode file, or parse directly from the verified archives.

6. **MINOR — D2 summary accounting is wrong with controls enabled.**  
   [build_d2_shards.py:262](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:262) includes control TIC `0`, so the default run reports 104 targets rather than 103.  
   Minimal fix: count distinct nonzero TICs from arms A/B only.

7. **MINOR — Several supposedly corrected claims remain contradicted in source documentation.**  
   [replay_gate.py:12](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/replay_gate.py:12) still says the v1→v2 commit changed no numeric path; [build_d3_roster.py:23](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d3_roster.py:23) still calls the D3 result an FPR upper bound; and [GENERALIZATION_PLAN.md:163](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:163) still describes nulls over 510 non-detected windows.  
   Minimal fix: reconcile all source docstrings and plan passages with the dispositions and current 928-window implementation.

The sinc, phase, 928-window current-data load, D3 SRS, IERS setting, module-resolution checks, worker preflight, strict-v2/nonempty gate, exact production pass set, and final `assert_frozen()` are implemented as claimed. All “FIXED in spec” statements are present textually in `METRICS_SPEC.md`, but the reviewed tests do not establish their runtime enforcement.

Validation: all 18 existing test functions passed in the local read-only environment; targeted checks found 928/928 templates and 1,442 unique injection IDs. There are no tests for shard arms, control identity stability, stale outputs, or attestation fingerprint enforcement. I made no file changes.
