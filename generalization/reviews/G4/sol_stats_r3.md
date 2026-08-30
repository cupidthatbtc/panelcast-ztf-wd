All three closure items are resolved. No new BLOCKING, MAJOR, or MINOR findings.

### 1. Chance-match denominator — RESOLVED

- The main path supplies nominal arm-B rows at [metrics_generalization.py:1542](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1542).
- `d2_chance_match` retains all `freq_scorable` rows and defines targets before inspecting candidate frequencies at [metrics_generalization.py:961](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:961).
- Candidate frequencies and tolerances use an explicit finite mask; failures become `NaN` and cannot be confirmed at [metrics_generalization.py:974](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:974).
- Dominant- and any-mode distances are vectorized, with `NaN` distances converted to infinity before minimization at [metrics_generalization.py:990](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:990). Rates remain target-equal at line 996.
- The regression test is at [test_d2_shards_contract.py:530](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:530).

Runtime probe with one finite confirmed self-match plus `NaN` and `inf` non-detections per target produced:

- 200 derangements: recovery mean `0.0`, any-mode mean `0.0`
- Self-match rate: exactly `0.3333333333333333`

### 2. D2 row-level interval suppression — RESOLVED

- `strip_intervals` recursively nulls every nested `lo` and `hi` at [metrics_generalization.py:1097](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1097).
- The D2 contingency object is stripped before JSON serialization at [metrics_generalization.py:1547](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1547).
- D2 sensitivity `lo`/`hi` columns are set to `NaN` before CSV serialization at [metrics_generalization.py:1603](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1603).
- The recursive regression test is at [test_d2_shards_contract.py:554](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:554).

Runtime probes found all six contingency interval values serialized as `null`; sensitivity CSV round-trip parsed every `lo`/`hi` as `NaN`.

### 3. Exact sensitivity endpoints — RESOLVED

The explicit endpoint assignments are correct: `lo=0.0` when `k==0` and `hi=1.0` when `k==n` at [metrics_generalization.py:1232](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1232). Exact assertions are at [test_d2_shards_contract.py:562](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:562).

Runtime results were exactly `lo=[0.0]` for 0/n and `hi=[1.0]` for n/n.

### Round-2 resolved-item regression audit — RESOLVED

- W_g construction, deterministic matching, strict strata, frozen edges, and manifest recording remain intact at [build_d2_shards.py:184](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:184), [build_d2_shards.py:199](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:199), and [d2_truth_model.py:563](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:563). Current-pool recomputation gave 928 windows, quantiles 6/58/452.3, edges 15/41/84/217, and strict separation for 103/103 targets.
- P4 remains recovery-only primary; trigger is secondary and P5 remains the sole confirmatory decision at [metrics_generalization.py:623](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:623), [metrics_generalization.py:671](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:671), and [metrics_generalization.py:1140](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1140).
- Paired controls and reuse output remain intact at [metrics_generalization.py:1007](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1007) and [metrics_generalization.py:1576](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1576). A reused-control probe recovered one partner’s frequency and not the other’s.
- Target-equal surfaces remain intact at [metrics_generalization.py:908](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:908). The unbalanced probe returned `0.20`, not pooled-window `3/7`.
- Degenerate contrasts still use `cp_discordance_bound` with ±U95 at [metrics_generalization.py:780](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:780); runtime U95 was `0.4507197283`.
- Frozen plan/spec hashes still match the ledger at [G2_FREEZE.md:195](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:195).
- Current-code D1 regression reproduced `11/13`, `9/13`, and `13/13`.

All 51 tests collected; 27 read-only-compatible tests passed. Fixture-backed tests could not run because the sandbox has no writable temporary directory, but their closure assertions were independently reproduced in memory. Post-`cb90b71`, only the round-3 prompt files changed. No tracked files were modified during review.

New findings: none.

## Verdict: APPROVE
