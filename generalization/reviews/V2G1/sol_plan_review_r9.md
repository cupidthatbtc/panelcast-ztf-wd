One blocking provenance gap remains.

1. Completion/schema is corrected: runner fields are used fail-closed, and callers share the checks ([v2_common.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/v2_common.py:186), [rescore_v2.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/rescore_v2.py:53), [dev_tuning.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/dev_tuning.py:69)).

2. Sidecar matching is correct ([dev_tuning.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/dev_tuning.py:85)), but downstream `dev_runs` validation does **not** require four distinct manifest identities. It deduplicates only `(dataset, window)` and merely checks each SHA’s format ([v2_common.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/v2_common.py:250)). Four records carrying the same `manifest` and `sha256`, with altered schedule metadata, are accepted. The authentic-runner test itself constructs and accepts exactly this case ([test_v2_amendment_provenance.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_v2_amendment_provenance.py:238)). No downstream check repairs it: the runner copies the accepted records into the lock ([run_v2_ls.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/run_v2_ls.py:239)), and comparison checks only artifact validation plus lock equality ([compare_engines.py](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/compare_engines.py:402)). Require four unique manifest SHAs, preferably four well-typed, unique manifest paths too.

3. The laptop restart path is closed as described ([v2_laptop_chain.ps1](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/v2_laptop_chain.ps1:16), [v2_chain_restart.ps1](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/v2_chain_restart.ps1:8), [v2_holdout_laptop.ps1](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/v2_holdout_laptop.ps1:18), [sync_laptop.sh](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/v2/analysis/sync_laptop.sh:26)).

4. SUMMARY and RUNBOOK are corrected ([SUMMARY.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/writing/outline/SUMMARY.md:47), [RUNBOOK.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:163)).

The focused 29 provenance/runner tests pass; the duplicate-manifest reproducer is also accepted.

VERDICT: REVISE
