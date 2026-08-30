Amendment 4 is substantially implemented, but two metric defects remain. Six items are resolved and two are partial. No BLOCKING finding; two MAJOR and one MINOR finding require correction.

### 1. Stratification — RESOLVED

- `load_pool` computes \(W_g=\sum_n\max(n_{zg,n}-1,0)\) at [build_d2_shards.py:184](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:184).
- Matching sorts by `(wg_contrasts, source_id)` and retains NumPy round-half-even 10/50/90 picks at [build_d2_shards.py:199](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:199).
- `template_wg_contrasts` is in the fixed schema at [d2_truth_model.py:101](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:101) and is populated for injected, control, and null rows at [build_d2_shards.py:511](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:511).
- Strict \(K0<K1<K2\) checking and production refusal are at [d2_truth_model.py:563](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:563).
- Frozen edges and production equality are at [d2_truth_model.py:147](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:147) and [build_d2_shards.py:590](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:590); generation-manifest quantiles, edges, and violations are written at [build_d2_shards.py:650](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:650).

Independent recomputation over the current 928-window pool gave:

- \(W_g\) quantiles: 10/50/90 = 6/58/452.3.
- 20/40/60/80 = 15/41/84/216.8, rounding to `(15, 41, 84, 217)`.
- Strict separation for 103/103 targets.
- \(W_g=n_{\rm eff}-N_{\rm multi-night}\) exactly, with Spearman correlation 0.99865 against the proposed \(n_{\rm eff}\).

Assessment: \(W_g\) is an acceptable, arguably more mechanism-aligned realization. It counts the within-night contrast degrees remaining after estimating and removing one nightly location. It should continue to be described as contrast/support count, not as an independent-observation ESS.

### 2. Primary P4 and flags — RESOLVED

Recovery is exactly `confirmed AND best_candidate_matches_dominant == direct`; detection-only is the `trigger` endpoint at [metrics_generalization.py:604](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:604). Non-pilot nominal-B recovery rows receive `prespecified_primary=True`, while every P4 row has `confirmatory_decision=False`, at [metrics_generalization.py:652](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:652).

P5 remains in `trigger_rates`, with the exact one-sided CP rule and sole confirmatory decision at [metrics_generalization.py:1080](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1080). Runtime probe for 0/1000 produced \(U_{95}=0.00299125\), `prespecified_primary=True`, `confirmatory_decision=True`.

### 3. Paired controls — RESOLVED

`d2_paired_controls` scores each control frequency against its partner B target’s dominant injected mode and emits D/R pair outcomes at [metrics_generalization.py:980](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:980). The summary includes 2×2 counts, B-only/C-only/union, target-standardized paired differences, and \(P(B=1,C=0)\) using one common target-draw matrix at [metrics_generalization.py:1010](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1010). The quiet-control secondary is at line 1043.

The reuse table is derived from the full manifest, not the pilot subset, at [metrics_generalization.py:1513](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1513). A runtime probe confirmed that one reused control can recover one partner’s frequency but not another’s.

### 4. Surfaces — RESOLVED

`_target_equal_cells` reports `n_windows`, `k_windows`, and `n_targets`, computes target-equal points, and bootstraps targets only for cells with at least five targets at [metrics_generalization.py:889](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:889). `d2_surfaces` emits recovery and trigger surfaces for \(W_g\times\)amplitude, period×amplitude, and amplitude at [metrics_generalization.py:914](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:914).

A deliberately unbalanced cell produced the correct target-equal estimate 0.20 rather than the pooled-window value 0.4286.

### 5. Chance-match — PARTIALLY RESOLVED

The function does use frozen-seed target derangements, moves all K rows through a target mapping, vectorizes dominant/any-mode direct comparisons, and computes target means at [metrics_generalization.py:937](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:937).

However, the initial filter at line 942 removes rows with no best frequency before defining targets and denominators. Consequently, non-detections and missing-frequency failures do not contribute zero, and targets with no candidate disappear entirely. A three-target probe with one confirmed match plus two non-detections per target returned 1.0; the endpoint-aligned all-K rate is 1/3.

### 6. Degenerate paired contrasts — RESOLVED

Zero observed target-level discordances switch to `cp_discordance_bound`, set `discordance_u95`, and report `diff ± U95` at [metrics_generalization.py:761](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:761). With five concordant targets, the runtime result was \(0\pm0.45072\), never `[0,0]`.

### 7. Descriptive rows and interval suppression — PARTIALLY RESOLVED

- The sensitivity rows are labelled descriptive at [metrics_generalization.py:1176](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1176).
- D2 completeness `lo`/`hi` are suppressed at [metrics_generalization.py:1490](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1490).

Two defects remain:

- `contingency()` still generates row-level Wilson `lo`/`hi` at [metrics_generalization.py:532](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:532); the D2 main path merely adds a label saying they are absent.
- The sensitivity endpoint clamp is ineffective for floating residue: runtime 0/3 still yielded `lo=5.551115123125783e-17`, not exact zero.

### 8. Specification, plan, and ledger — RESOLVED

The v4 disclosure and vocabulary are present at [METRICS_SPEC.md:7](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:7); P4, flags, and paired controls at [METRICS_SPEC.md:133](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:133); units/strata at [METRICS_SPEC.md:168](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:168); complementarity and surfaces at [METRICS_SPEC.md:207](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:207); and guards/outputs at [METRICS_SPEC.md:262](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:262).

The plan’s Amendment 4 paragraph is at [GENERALIZATION_PLAN.md:268](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:268). The ledger entry and hashes are at [G2_FREEZE.md:172](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:172). Current-byte hashes match exactly:

- `METRICS_SPEC.md`: `66013732a585c4a612376704e3c1e9af2ba81919e30eb9c1967e0ec4bfc02eca`
- `GENERALIZATION_PLAN.md`: `e2cd36af2cbb4bc11537b3f7e90c1b722bb8b0c611d3e887879c7105b10ddc65`

### New findings and exact fixes

- **MAJOR — chance-match denominator mismatch.** Preserve every nominal-B K row and every target. Treat absent/non-confirmed candidate frequencies as failures through a finite-frequency mask; construct the target list before any candidate-frequency filtering. Add a regression test with one candidate and two `NaN` frequencies per target that requires 1/3, not 1.0.

- **MAJOR — D2 contingency intervals remain.** For `dataset=="d2"`, remove or null `lo`/`hi` from `union_completeness`, `incremental_census_only`, and `incremental_ls_only`; retain counts and descriptive point estimates. Add a test asserting no D2 contingency interval keys.

- **MINOR — sensitivity endpoint clamp.** Set `lo=0.0` explicitly when `k==0` and `hi=1.0` when `k==n`; `max(lo,0)` cannot eliminate a small positive floating residue. Add exact endpoint assertions.

Tests: all 46 tests collect successfully; 26 read-only-compatible tests passed. The full suite could not run in this sandbox because pytest’s temporary-directory creation is prohibited. The requested contract tests are present at [test_d2_shards_contract.py:359](/Users/jackneo/Documents/vonhippel-base9/astro-wd/tests/test_d2_shards_contract.py:359), but the chance test only checks range/order and does not exercise missing-frequency denominators. The D1 regression independently reproduced 11/13, 9/13, and 13/13.

No files were edited.

## Verdict: APPROVE-WITH-CHANGES
