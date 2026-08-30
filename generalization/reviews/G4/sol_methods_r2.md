The scientific core of Amendment 4 is implemented correctly, but I would not start the full D2 run yet. There are no new BLOCKING design defects, but three MAJOR mechanical/provenance gaps should be closed first.

Current reviewed files are byte-identical to `b854e97`; current HEAD `10ce29f` only adds the round-2 prompts. The frozen hashes match current bytes exactly:

- `METRICS_SPEC.md`: `66013732…02eca`
- `GENERALIZATION_PLAN.md`: `e2cd36af…ddc65`

Those are the values recorded in [G2_FREEZE.md:195](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:195).

## Per-item verification

- **RESOLVED — `build_d2_shards.py`.** \(W_g=\sum(\text{exposures/night}-1)_+\) is computed in `load_pool` at [build_d2_shards.py:184](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:184). Matching sorts by `(wg_contrasts, source_id)` and applies the exact NumPy round-half-even indices at [build_d2_shards.py:199](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:199). `template_wg_contrasts` is typed and emitted for A/B, controls, and nulls at [build_d2_shards.py:267](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:267), [build_d2_shards.py:509](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:509), [build_d2_shards.py:525](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:525), and [build_d2_shards.py:539](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:539). Production enforces strict strata and exact frozen surface edges at [build_d2_shards.py:576](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:576). Quantiles, edges, and violations enter the generation manifest at [build_d2_shards.py:650](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:650). Independent recomputation on the local 928-window pool gave quantiles `0/6/58/452.3/2670` and edges `15/41/84/217`.

- **RESOLVED — `d2_truth_model.py`.** The fixed column is in the manifest schema at [d2_truth_model.py:99](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:99), frozen edges at [d2_truth_model.py:147](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:147), row-level nonnegative invariants for A/B and controls/nulls at [d2_truth_model.py:377](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:377), and the strict cross-row \(K_0<K_1<K_2\) checker at [d2_truth_model.py:563](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:563).

- **RESOLVED — primary P4 and flags.** Recovery and trigger are separate endpoints at [metrics_generalization.py:604](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:604). Only non-pilot nominal-B recovery rows get `prespecified_primary`; all P4 `confirmatory_decision` values are false at [metrics_generalization.py:652](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:652). P5 alone can set the decision flag at [metrics_generalization.py:1091](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1091).

- **PARTIALLY RESOLVED — paired controls.** The pair table, D/R 2×2 counts, target-cluster bootstrap, \(P(B=1,C=0)\), quiet-control row, and reuse table exist at [metrics_generalization.py:980](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:980) and [metrics_generalization.py:1513](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1513). Two exact-estimand/guard gaps remain below.

- **RESOLVED — target-level surfaces.** Target means and target bootstrap intervals are implemented at [metrics_generalization.py:889](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:889), with recovery/trigger surfaces on \(W_g\), amplitude, and period at [metrics_generalization.py:914](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:914).

- **RESOLVED — TIC-level chance matching.** All nominal replicates share a target-level derangement; 10,000 fixed-seed derangements are used at [metrics_generalization.py:937](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:937).

- **RESOLVED — degenerate paired contrasts.** Zero observed target-level discordance produces a one-sided CP discordance/effect bound instead of `[0,0]` at [metrics_generalization.py:761](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:761).

- **PARTIALLY RESOLVED — descriptive D2 row outputs.** Generic completeness intervals are suppressed at [metrics_generalization.py:1490](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1490), but suppression is incomplete; see MAJOR 1.

- **RESOLVED — stars-file provenance.** `--stars-file` is exposed at [metrics_generalization.py:1237](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1237), and SHA plus exact ID-set equality are enforced at [metrics_generalization.py:1055](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1055) and invoked at [metrics_generalization.py:1350](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1350).

- **RESOLVED for named fields; PARTIAL for full provenance — runner.** `stars_file_sha256`, argv, timestamps, commit, and dirty state are written at [run_generalization_ls.py:358](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:358). Sidecars bind result/shard/environment/attestation/generation at [run_generalization_ls.py:116](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:116).

- **RESOLVED — `METRICS_SPEC.md`.** v4 disclosure is at [METRICS_SPEC.md:4](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:4); vocabulary and recovery-primary hierarchy at [METRICS_SPEC.md:14](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:14); P4, flags, and paired controls at [METRICS_SPEC.md:121](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:121); units/strata at [METRICS_SPEC.md:168](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:168); descriptive complementarity at [METRICS_SPEC.md:207](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:207); surfaces at [METRICS_SPEC.md:218](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:218); guards and outputs at [METRICS_SPEC.md:262](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:262).

- **RESOLVED — plan.** The exact window rule is at [GENERALIZATION_PLAN.md:190](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:190); the Amendment 4 disclosure and hierarchy are at [GENERALIZATION_PLAN.md:268](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:268).

- **PARTIALLY RESOLVED — runbook.** Gen2 generation, pilot, full-run, and metrics commands are present at [RUNBOOK.md:64](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:64). Raw JSON and `.prov.json` archival is explicitly required at [RUNBOOK.md:81](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:81). Execution remains pending because the pilot is still running; its completed archive cannot yet be verified.

- **RESOLVED — freeze record.** Amendment 4’s disclosure, implementation summary, tests, D1 statement, and current document SHAs are recorded at [G2_FREEZE.md:172](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:172). Its `PENDING G4 round-2` status is still accurate at [G2_FREEZE.md:202](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:202).

## Findings requiring changes

1. **NEW — MAJOR: D2 row-level interval suppression is incomplete.** `contingency()` still constructs Wilson intervals at [metrics_generalization.py:531](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:531), and they are serialized unchanged even while the JSON is labeled “no row-level intervals” at [metrics_generalization.py:1497](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1497). D2 `sensitivity.csv` also retains row-level Wilson intervals at [metrics_generalization.py:1180](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1180).

   **Exact fix:** for D2, remove/null all nested complementarity and sensitivity `lo`/`hi` values, retaining descriptive counts/points and directing inference to the cluster/paired tables. Add serialization-level tests asserting no finite D2 row-level intervals.

2. **NEW — MAJOR: paired-control usability and relational guards are incomplete.** The quiet-control estimand filters only `control_usable`; a missing injected B result is retained as a failure, contrary to Round 1’s “injected/control pair usable” definition at [metrics_generalization.py:1028](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1028). Missing controls are silently skipped at [metrics_generalization.py:989](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:989). The scorer also does not re-run `check_wg_strata` or enforce the spec’s cross-row control-resolution guard, despite [METRICS_SPEC.md:295](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:295).

   **Exact fix:** add `b_usable` and `pair_usable`; define the quiet subset as `pair_usable & control_status=="not_detected"`. In `truth_d2`, validate strict \(W_g\), equality with recorded violations, and that every nominal-B control ID resolves to exactly one control with matching template ID, pool index, and \(W_g\). Fail instead of `continue`. These can be implemented in the scorer without rebuilding gen2.

3. **ROUND-1 UNRESOLVED — MAJOR: sidecar and test-log hashes are not yet bound.** Metrics verifies sidecar contents at [metrics_generalization.py:1403](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:1403), but never adds the sidecar SHA to `inputs_sha256`; the completion table records only the result SHA at [run_generalization_ls.py:393](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:393). No test-log hash is specified or archived.

   **Exact fix:** add each `.prov.json` SHA to `inputs_sha256` and either `provenance_sha256` to `completion.csv` or an archive-level `SHA256SUMS` covering every result and sidecar. Archive both-machine 46-test logs and bind their hashes in the pilot provenance record before full launch.

4. **NEW — MINOR: stale text remains.** The builder docstring still describes exposure-per-night stratification at [build_d2_shards.py:33](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:33); the cluster function still says “confirmatory P4 row” at [metrics_generalization.py:582](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:582); and the runbook says 40 rather than 46 tests at [RUNBOOK.md:18](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/RUNBOOK.md:18). Correct those phrases. Changing the builder—even its docstring—changes generation-code SHA and would force a gen2 rebuild, so that cosmetic builder edit is non-gating unless gen2 is rebuilt deliberately.

5. **NEW — MINOR: `git_dirty` ignores untracked files.** The runner uses `--untracked-files=no` at [run_generalization_ls.py:298](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/run_generalization_ls.py:298). Either include untracked state or rename the field `git_tracked_dirty` and record untracked state separately.

## Before the full D2 run may start

- Apply and test the three MAJOR fixes.
- Let the gen2 pilot finish; require zero unexplained failures, run amended metrics, and verify all \(W_g\), selection-SHA, control-resolution, provenance, and platform-boundary guards.
- Archive the pilot’s raw JSONs, sidecars, completion/manifest files, metrics, test logs, and complete hashes.
- Obtain the G4 round-2 stats clearance and update the freeze ledger from `PENDING`.
- Launch from the reviewed, attested laptop checkout with the full command lacking `--stars-file`.

Current source contains 46 test cases—42 test functions plus the five-way truth-file parameterization—and a current-code D1 probe reproduces `11/13`, `9/13`, and `13/13`. I could not re-execute pytest in this read-only review sandbox because no writable temporary directory is available.

## Verdict: APPROVE-WITH-CHANGES
