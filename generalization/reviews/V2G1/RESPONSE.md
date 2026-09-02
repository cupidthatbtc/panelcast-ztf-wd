# V2G1 — response to the sol pre-registration review (round 1, 2026-09-02)

Review: `sol_plan_review.md` (prompt `PROMPT_round1.md`; codex GPT-5.6-sol, xhigh). Verdict
REVISE. Every finding is accepted; dispositions below reference the revised
`generalization/v2/V2_PLAN.md` (§) and code.

| # | severity | disposition |
|---|---|---|
| 1 | BLOCKING | ACCEPTED. The four smoke stars are the class `dev_smoke` in `split.csv`, excluded from both halves and from every registered run (`make_split.py::SMOKE_SIDS`; runner refuses `dev_smoke`); holdout counts flag1 299 / flag0 1,149 (§4); primary numbers never include them; a table including them is labelled "contaminated sensitivity analysis" (§6). |
| 2 | MAJOR | ACCEPTED. §1 "What the holdout validates" states the internal post-selection nature verbatim and that no alternative partition was evaluated; §7 adopts the required abstract wording. |
| 3 | BLOCKING | ACCEPTED (exactness achieved without the 9 full reruns): the candidate set is now ordered by power only (cap 45 = every peak row), and every veto component is recorded per candidate (locus label, local window power, same-series alias, cross-pass alias and the full partner list; 24 window peaks per series; joint top-15), so `rescore_v2.py` re-derives the veto, the joint top-5 and the coherence gates EXACTLY for the 27 decision-constant combinations; only the trend window is rerun, and its set is reduced to {30, 10} d with FULL dev reruns (the subsets are removed). `dev_tuning.py` asserts the 54 combinations, applies the fixed selection rule with the declared tie-break and records `tuning_constraint_failure` (§5). |
| 4 | BLOCKING | ACCEPTED. `run_v2_ls.py::registered_holdout`: exact registered list SHA (from `split_manifest.json`), no `--limit`, `V2_CONSTANTS_FROZEN.json` required with v2-digest / split-SHA / plan-SHA equality, `HOLDOUT_LAUNCH_<dataset>.json` lock created before computation, relaunch only as an exact resume; tested (`tests/test_v2_runner.py`). |
| 5 | BLOCKING | ACCEPTED. `compare_engines.py::build_frames` left-joins the v2 table onto the split roster of the half (`dev_smoke` excluded); ids without a v2 shard are failures; runner-list ids without a v2 row abort. Denominators: 299 / 1,149. |
| 6 | MAJOR | ACCEPTED. Primary P2 = frozen P2 frame (Mo-joined, freq-scorable, eligible, frozen-usable), v2 unavailable = non-recovery; both-arms-usable reported as sensitivity with availability transitions (§6). |
| 7 | MAJOR | ACCEPTED. B = 2000, seed 20260902, two-sided McNemar and the degenerate-bootstrap fallback declared (§6, `compare_engines.py`); P4 eligible AND usable variants; chance-match rates of both bundles beside P2; the 24-control rate replaced by the target-clustered injected-vs-paired-control contrast; STRONG called a descriptive operational screen; the null screen's U95 floor stated. |
| 8 | MAJOR | ACCEPTED. Controls referenced by any odd-TIC nominal-B shard → holdout (67); dev D2 before the freeze = 500 dev nulls only; even-TIC B / control outputs deferred (`d2_dev_deferred.txt`, 219); window crossing disclosed (43/106 B windows, 72/928 null windows) as fixed-window, independent-noise validation (§4). |
| 9 | MAJOR | ACCEPTED. `align.py`: shared-night per-oid weighted medians, `min_shared_nights = 5`, insufficient overlap → unshifted and flagged (`unshifted_insufficient_overlap`), whole-row estimate recorded not applied; overlap counts in every JSON; endpoint sensitivity to alignment-affected stars declared (§6). |
| 10 | MAJOR | ACCEPTED. "Untouched by construction" removed; leakage stated in §2 and the low-frequency-only injection audit on dev D3 windows plus the paired-control contrast declared (§6); truth-frequency veto exposure by dataset / pass / band / component and union declared as mandatory descriptive output; the 12/T ≈ 0.43 % per-partner estimate and its baseline dependence stated. |
| 11 | MINOR | ACCEPTED. §2.4 states the gate is operational, phase errors do not enter the decision; stratified failure reporting declared (§6). No rule-code change. |
| 12 | MAJOR | ACCEPTED. Binding keys extended (machine, split_sha256, split_half, stars_file_sha256; plan_sha256 + preregistration_commit for the holdout) in sidecars and in `metrics_generalization.sidecar_binding_keys("v2")`; the comparison manifest binds both per-star tables, the split, the script, the constants artifact and the smoke exclusions. The revision is committed before any registered run (this commit). |
| 13 | MINOR | ACCEPTED. `window_peaks` separates peaks on the combined T; the window subsets and their `make_split.py` lines are removed. |

Pending for the confirmation round: none of the findings is deferred; the audits of
findings 10–11 are descriptive outputs produced after the dev runs (declared, not yet
computed).

# Round 2 (confirmation) — `sol_plan_review_r2.md`, verdict REVISE; dispositions

| # | round-2 status | disposition (all ACCEPTED) |
|---|---|---|
| 3 | PARTIAL | `rescore_v2.combination_id` includes the trend window (54 labels, §3 order); `dev_tuning.py` ingests both trend-window tables for D3 and the nulls, asserts 54 combinations and the denominators (D3 rows = registered dev list; D2 rows = 500 dev nulls; roster 308 / 1,164), uses the frozen P2 frame, applies the §3 tie order, records `tuning_constraint_failure`, verifies the pre-registration commit is an ancestor of HEAD and emits `V2_CONSTANTS_FROZEN.json` bound to code / split / plan / commit / evidence / inputs. |
| 4 | NOT RESOLVED | (b) closed: `--split-file` must be the registered split at the registration root; every unregistered path (debug, dev, no split file) refuses any registered holdout id (`canonical_holdout_ids`), tested; the lock is created with O_EXCL; the artifact's `preregistration_commit` must be an ancestor of HEAD and its `tuning_evidence_sha256` must match `dev_tuning.csv`; the lock records `registration_root` / `canonical_registration`; the comparison refuses non-canonical registrations. The test uses HEAD as the commit and refuses "deadbeef". |
| 7 | PARTIAL | exact discordance bound [−U95, +U95] at zero discordant pairs; chance-match mandatory beside P2 (both bundles); strict-recovery paired-control contrast added (control scored against the partner's injected dominant frequency). |
| 8 | PARTIAL | the runner list is authenticated against `split_manifest.json` (`<dataset>_<half>.txt` SHA) before any frame is built. |
| 10 | PARTIAL | audit implementations committed (`scripts/v2/analysis/veto_exposure.py`, `leakage_audit.py`, f10e57e); the contradictory sentences in `detrend.py` and `window.py` replaced by the leakage / exposure statements. |
| 12 | PARTIAL | metrics sidecar keys include `plan_sha256`, `preregistration_commit`, `constants_artifact_sha256`; the comparison binds both metrics manifests, the run manifest, the registered list, the split, the constants artifact and the lock. |
| 13 | PARTIAL | stale docstrings (`dev_tuning.py`, `multiband.py`) rewritten. |
| 1, 2, 5, 6, 9, 11 | RESOLVED | — |
