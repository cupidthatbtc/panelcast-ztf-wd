3. RESOLVED — 54 ordered labels and deterministic selector/artifact: `rescore_v2.py:45-64`; `dev_tuning.py:66-149,169-208`.

4. NOT RESOLVED — `V2_REGISTRATION_ROOT` selects an arbitrary registration directory (`run_v2_ls.py:165-171`). A copied root without its lock can launch the canonical holdout under altered allowed overrides: validation is relative to that root (`221-268`), and a successful `registered_holdout` skips the canonical-ID guard (`361-387`). The test itself demonstrates non-canonical holdout execution (`test_v2_runner.py:122-160`). Metrics accepts and scores that run (`metrics_generalization.py:1490-1500,1726-1730`); only comparison rejects its unchanged manifest (`compare_engines.py:336-337,369-370`). Scoring twice already compromises the holdout.

7. PARTIAL — discordance bound and strict-recovery contrast are resolved (`compare_engines.py:85-113,171-233`). Remaining:

- The module docstring still claims `[0,0]` for zero discordances (`compare_engines.py:21-24`).
- Empty/malformed `chance_match.json` files pass and produce NaNs (`408-417`); their SHAs are omitted from `inputs_sha256` (`428-433`).

8. RESOLVED — runner-list SHA authentication occurs before frame construction (`compare_engines.py:313-322,398-403`).

10. RESOLVED — both audit implementations are committed; contradictory detector documentation is removed (`analysis/*.py`; `detrend.py:18-22`; `window.py:21-25`).

12. RESOLVED — sidecar keys and comparison bindings are present (`metrics_generalization.py:1503-1512,1728-1730`; `compare_engines.py:306-377,428-444`).

13. RESOLVED — stale selector/clustering descriptions are corrected (`dev_tuning.py:5-28`; `multiband.py:14-18`).

(a) RESOLVED.

(b) NOT RESOLVED — copied-root runner/metrics attack above succeeds; comparison rejects the untouched non-canonical manifest.

(c) RESOLVED — D3 299/1,149; D2 129 B shards, 43 targets, 67 controls, 500 nulls. Missing runner rows abort.

Required changes:

- Canonical holdout IDs must require the canonical registration root in the runner itself; reject non-canonical holdout runs in metrics as defense in depth. Add a copied-root regression test.
- Validate finite required chance-match fields, SHA-bind both files, and correct the stale discordance docstring.

Full 215/215 was not rerun because the read-only sandbox cannot create pytest temporary files; four relevant no-write tests passed.

VERDICT: REVISE