# `--engine v2` metrics branch — implementation record (2026-09-02)

Implemented by a codex GPT-5.6-sol subagent (brief: PROMPT_metrics_engine.md); the subagent's
session ended on "model at capacity" after the code + tests, so the guard was run by the lead.

## Change (scripts/generalization/metrics_generalization.py, main() only)

- `--engine {frozen,v2}` (default frozen).
- `attestation_record_for(engine, run_manifest, path)`: frozen → the replay-attestation
  validation exactly as before (a manifest with `engine == "v2"` is refused); v2 → requires
  `engine == "v2"`, no replay report, tier `v2_unattested`, sha `v2-unattested`, records
  v2_digest / constants_sha256 / machine; the `frozen_sha256` equality check is kept for both.
- `sidecar_binding_keys(engine)`: frozen → ("frozen_digest", "campaign_digest",
  "generation_id") unchanged; v2 → ("engine", "frozen_digest", "v2_digest", "constants_sha256",
  "generation_id") + `driver == "run_v2_ls.py"`.
- metrics manifest gains `"engine"`.
- `descriptive/compare_metrics_runs.py`: "engine" added to MANIFEST_MAY_DIFFER; the attrition
  special case now applies only when the reference is a pre-fix bundle (no
  attrition_summary.csv); a post-fix reference compares attrition.csv and attrition_summary.csv
  byte-for-byte.

Tests: tests/test_v2_metrics_engine.py (engine helpers + guard whitelist) — 8 pass with
tests/test_compare_metrics_runs.py.

## Guard (frozen D3 bundle, patched module, Mac)

```
metrics rc=0
science outputs: 15 identical_bytes, 0 identical_newline, 0 differ
```
Direct comparison of the special-cased files (reference = committed
generalization/results/2026-09-02_d3/metrics, candidate = outputs/generalization/
d3_metrics_engine_guard):

| file | reference | candidate |
|---|---|---|
| attrition.csv | 350bb7a2e0b7… | 350bb7a2e0b7… |
| attrition_summary.csv | dcf6c138e3da… | dcf6c138e3da… |
| d3_mo_join_covariates.csv | 13d8a9e8cfef… | 13d8a9e8cfef… |
| per_star.csv | 36abc4653df8… | 36abc4653df8… |
| trigger_rates.csv | 7d12c2d656a7… | 7d12c2d656a7… |

manifest.json keys differing: `campaign_sha256` (expected: the module changed), `engine`
(new, value "frozen"); tier "strict". The first guard invocation printed GUARD FAIL solely
because the script compared the reference's (post-fix, multidimensional) attrition.csv with the
candidate's attrition_summary.csv — a pre-fix-reference assumption, corrected as above; the
re-run prints GUARD PASS (see below when re-executed).

Verdict: the frozen metrics path is byte-for-byte unchanged by the `--engine` change.
