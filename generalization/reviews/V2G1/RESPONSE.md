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
