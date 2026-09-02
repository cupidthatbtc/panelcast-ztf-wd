# Confirmation review (round 2) of the v2 pre-registration — ADMIT / REVISE

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1,
commit 5ceb019 = the pre-registration commit). Read-only. You are the same methods + statistics
referee persona as round 1: your round-1 findings are in
`generalization/reviews/V2G1/sol_plan_review.md`; the lead's dispositions are in
`generalization/reviews/V2G1/RESPONSE.md`. Verify each disposition against the REVISED
`generalization/v2/V2_PLAN.md` and the code (`scripts/v2/*.py`, in particular
`make_split.py`, `align.py`, `window.py`, `multiband.py::cluster_candidates`, `rule.py`,
`analyze_star_v2.py`, `rescore_v2.py`, `dev_tuning.py`, `run_v2_ls.py::registered_holdout`,
`compare_engines.py`), the split artifacts (`generalization/v2/split.csv`, `split_manifest.json`,
`*_holdout.txt`, `*_dev.txt`) and the tests (`tests/test_v2_*.py`; the suite passes 207/207).

For each of your 13 round-1 findings state RESOLVED / PARTIAL / NOT RESOLVED with the exact
gap if any. Then check three specific points:

(a) Exactness of the offline re-score (finding 3): confirm from the code that, for a fixed
    trend window, the decision for every (n_window_peaks, phase, ratio) combination is a pure
    function of the recorded per-candidate diagnostics — or name the remaining dependence.
(b) The registered-holdout mode (finding 4): try to construct a way to score the holdout
    twice with different constants or code without tripping the lock/binding, and report it.
(c) The comparison frames (findings 5–8): confirm the denominators the code will produce on the
    holdout (D3: 299 flag1, 1,149 flag0; D2: 43 targets, 67 controls, 500 nulls) and that a
    missing v2 light curve is a failure, not an exclusion.

Do not re-litigate design choices you accepted in round 1 unless the revision broke them.
End with `VERDICT: ADMIT` or `VERDICT: REVISE` plus the list of required changes (if any).
Terse, cite file:line.
