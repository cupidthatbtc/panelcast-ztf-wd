# Task: update the AAS 249 writing outline set for the v2 detector arm (ARS `academic-paper`, mode `outline-only`)

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1). You may
read anything; modify ONLY the four files in `generalization/writing/outline/` (OUTLINE.md,
EVIDENCE_MAP.md, CONTINGENCIES.md, SUMMARY.md) in place. Do not commit.

Conventions to follow (read first): the ARS skill definition
`/Users/jackneo/.claude/plugins/marketplaces/academic-research-skills/academic-paper/SKILL.md` (mode
`outline-only`: detailed outline + evidence map, no draft; balanced spectrum; high oversight = every
claim bound to an artifact and labelled) and its mode registry
`/Users/jackneo/.claude/plugins/marketplaces/academic-research-skills/MODE_REGISTRY.md` (§ outline-only).
The existing outline set already applies these conventions (label vocabulary in OUTLINE §0.2, the
placeholder rule §0.1, the not-allowed list Part D, the evidence-map row format, the contingency
branch format): keep them exactly; extend, never rewrite.

Sources to read in full before editing: generalization/writing/outline/*.md; generalization/v2/V2_PLAN.md
(the pre-registered v2 arm; §6 endpoints, §7 disclosure wording, §10 amendments and disclosures);
generalization/reviews/V2G1/VERDICT.md (ADMIT); generalization/results/2026-09-02_d3/README.md (the
frozen D3 numbers now exist — these may be quoted with their file bindings);
scripts/v2/compare_engines.py (output schema: endpoints.csv columns endpoint, frame, n, interval,
frozen_k/p/lo/hi, v2_k/p/lo/hi, diff, diff_lo, diff_hi, frozen_only, v2_only, mcnemar_exact_p, note,
frozen/v2_chance_direct_mean/p95 on P2 rows; status_transitions.csv; availability_transitions.csv;
manifest.json with the registration binding); scripts/v2/analysis/veto_exposure.py and
leakage_audit.py (declared descriptive audits and their output files); scripts/v2/rescore_v2.py and
dev_tuning.py (dev_tuning.csv, V2_CONSTANTS_FROZEN.json).

Required changes:
1. OUTLINE.md — Part A abstract slots: add the v2 sentence(s) using the V2_PLAN §7 disclosure wording
   VERBATIM and the pre-declared STRONG/other reading as a descriptive operational screen (never a
   hypothesis test or confirmatory decision); character budgets updated within the 2,250-character cap
   (Tier A/B rules). Part B poster: add synthesis figures F9 (frozen vs v2 paired endpoints on the holdout:
   P1/P2/P3 with paired differences and McNemar, D2 P4 eligible/usable, P5-style nulls, paired-control
   contrasts), F10 (status transitions frozen→v2 by class + availability transitions), F11 (truth-frequency
   veto exposure by component + the leakage audit), and a mechanism panel (alignment offsets / shared-night
   counts / unshifted oids; coherence failures stratified by phase error and S/N), each with artifact,
   forbidden readings, label. Part C: the single RNAAS table gains v2 rows with Status = "holdout,
   post-selection internal validation"; ApJL figure mapping updated.
2. EVIDENCE_MAP.md — one row per v2 claim → compare_engines outputs (file, row selector = endpoint name,
   columns), the v2 metrics bundle per_star.csv, dev_tuning.csv / V2_CONSTANTS_FROZEN.json, the holdout
   locks generalization/v2/HOLDOUT_LAUNCH_<dataset>.json, the audit outputs; prereg status column value
   "V2_PLAN §6" (or §5/§8 as applicable).
3. CONTINGENCIES.md — v2 branches: STRONG (P3 falls ≥ 15 points AND P1 not more than 5 points lower AND
   ≤ 2/500 holdout nulls), partial, negative, and the tuning_constraint_failure case (defaults retained);
   the four dev_smoke stars are never in a primary number; the null screen's U95 floor (0/500 → 0.60 %).
4. Part D not-allowed list additions: no v2 number from the dev half; no v2 claim of external or
   confirmatory validation; no "corrected" frozen P3; no pooling of frozen and v2; no dev-tuned constant
   presented as pre-fixed; no v2 number before the holdout lock exists.
5. SUMMARY.md — refresh: the D3 numbers exist (cite README), D2 frozen bundle ~Sep 4, v2 dev runs Sep 4–6,
   holdout ~Sep 6–7, metrics Sep 8–10, G5 Sep 11–14, abstract/G6 Sep 15–26, submit ≤ Sep 30; open items
   re-listed.
Rules: never invent a number — every v2 cell stays ⟨placeholder⟩ bound to the named file/row; frozen D3
numbers may be quoted only from README.md/metrics files with their binding. Terse, table-driven, same
style as the existing files. Finish by listing, in SUMMARY.md, what you changed in each file.
