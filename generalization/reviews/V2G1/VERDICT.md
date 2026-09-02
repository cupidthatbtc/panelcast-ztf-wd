# V2G1 — pre-registration gate verdict

**ADMIT** at round 6 (2026-09-02; codex GPT-5.6-sol, xhigh, read-only), after five REVISE rounds:
round 1 (13 findings, 5 blocking), round 2 (residuals on 3/4/7/8/10/12/13; exactness and frames
confirmed; holdout bypass found), round 3 (copied-root bypass; chance-match binding), round 4
(debug options / pass order / lock completeness), round 5 (`frozen_api.py` outside both digests).
Prompts, reviews and dispositions: `PROMPT_round{1..6}.md`, `sol_plan_review{,_r2..r6}.md`,
`RESPONSE.md`. Governing document at the verdict: `generalization/v2/V2_PLAN.md`
(revised 2026-09-02); v2 runtime digest at the verdict: ecc5df75d8f225cb…; suite 221 passed.

Round-6 statement (verbatim): "`frozen_api.py` is now covered by `v2_digest`, propagated through
artifact/lock, resume scan, end-run check, metrics sidecars, and comparison verification.
Import-graph audit found no uncovered project runtime source; no relaunch bypass found."

What the gate admits: the dev runs (both trend windows), the exact re-score and selector, the
constants freeze, and ONE registered holdout execution per dataset under the canonical
registration. Any change to `scripts/v2/*.py` or `scripts/generalization/frozen_api.py` after
the dev runs start voids resume and, after the freeze, the holdout.
