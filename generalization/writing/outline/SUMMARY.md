# SUMMARY — writing outline for AAS 249 abstract, poster, and short paper (2026-09-01; updated 2026-09-02 for the v2 arm)

**Produced** (generalization/writing/outline/): OUTLINE.md (abstract slots, poster
sections + figure list, RNAAS and ApJL outlines, the not-allowed list),
EVIDENCE_MAP.md (81 claim rows → file → row selector → columns → prereg status,
15 of them v2), CONTINGENCIES.md (strong / ugly / mixed branches, P5-fail,
S14-fail, schedule, v2 branches §6), this file. Mode: `academic-paper`
outline-only. D3 frozen numbers now exist (quoted with bindings in
OUTLINE.md §0.4 and README.md); every other number, and every v2 number, is
still a `⟨placeholder⟩` bound to a named artifact.

**2026-09-02 update — v2 detector arm.** A second, pre-registered detector
(`generalization/v2/V2_PLAN.md`) fixing the four mechanisms the D3
descriptive tables diagnosed was ADMITTED at V2G1 round 6
(`reviews/V2G1/VERDICT.md`) after one REVISE round and four REVISE
confirmation rounds, all closed with regression tests. It is judged ONCE on
a pre-registered odd-KIC/odd-TIC holdout against the frozen arm on the same
stars (`scripts/v2/compare_engines.py`), and is conditional throughout this
outline: abstract slots S15/S16 (Tier C), poster §6 + figures F9–F12, RNAAS
Table 1 rows 17–23 + claims C20–C24, EVIDENCE_MAP §5 (V2-1…V2-15),
CONTINGENCIES §6 (STRONG/partial/negative/tuning-constraint-failure
branches). None of it changes the frozen arm's estimands, table rows, or
labels (Part D N29–N35 make this explicit). The v2 arm is not on the
abstract/paper critical path (CONTINGENCIES §4): if the dev runs or the
holdout slip past the Sep 22 decision point, the submission ships
frozen-only and the January poster carries v2 whenever it lands.

**Structure.** Abstract = 14 sentence slots with character budgets (AAS cap is
2,250 characters incl. spaces, not 250 words; Tier A ≈ 1,780 chars, Tier B
S8/S10/S12 drop in that order). Poster reuses `poster/poster.html` classes and
layout; 8 figures (F1 D3 turn-on, F2 rules × scopes, F3 negatives + FP audit
with the disclosed diurnal partition, F4 D3 2×2, F5 D2 W_g × amplitude recovery
+ P4, F6 scenario contrasts, F7 nulls + paired controls, F8 D1 anchor reused).
Short paper = RNAAS: 1,500 words all-in (150-word abstract; references count),
ONE table (contents exempt from the count) carrying all 16 endpoint rows with a
Status column; ApJL fallback 5–6 pages with 4 figures + the table.

**Labels are mandatory on every claim:** PRIMARY-P1…P5 (P5 sole confirmatory) ·
SECONDARY · DESCRIPTIVE-PRESPEC · DESCRIPTIVE-POST-LAUNCH (only
`d3_trigger_decomposition.csv`, with the verbatim disclosure sentence) ·
DIAGNOSTIC · PROVENANCE · ANCHOR · PILOT (never a number) · V2-HOLDOUT (frozen-
vs-v2 paired comparison on the holdout; descriptive operational screen, never
confirmatory). Amendment 4 is respected: no estimand is created, renamed,
swapped, or re-denominated anywhere; the v2 arm adds a parallel estimand
family (V2_PLAN.md §6) without touching the frozen one.

**Not-allowed list** (35 items, OUTLINE Part D): no "selection-function
measurement" as the measured object, no pooling, no real-sky completeness from
D2, no "D3 FPR", no unqualified purity, no ZTF-g threshold from Kepler
amplitudes, no causal cadence claims, no "band"/CI on the 3×3 grid, no D2
row-level Wilson, no native-rate subtraction, no "corrected" P3, no pilot
numbers, no 928-catalog counts as completeness, Amendment 4 disclosed as
pilot-informed; N29–N35 (new): no v2 number from the dev half, no v2 claim of
external/confirmatory validation, no "corrected" frozen P3 from v2, no pooling
frozen+v2, no dev-tuned v2 constant presented as pre-fixed, no v2 number
before its holdout lock file exists, no v2 window veto presented as fully
pre-registered (its fixed loci were extended once after partial dev-half
inspection, V2_PLAN.md §10 2026-09-04; the §7 disclosure clause is mandatory).

**Contingencies.** Ugly = pre-registered explanatory headline: bounded zeros
are measurements (one-sided 95 % CP: 0/610 → 0.49 %, 0/103 → 2.87 %, 0/48 →
6.05 %), strata make them explanatory (W_g pool 10/50/90 = 6/58/452; D3 median
dominant amplitude 1.77 mmag vs D1 median A95 5.2 mmag). Branch triggers,
replacement sentences, and figure changes are in CONTINGENCIES.md; table rows
and labels never change.

**Open items before G5/G6.**
1. `results/2026-08-30_d2_pilot_gen2/` has no README.md (the gen1 record does); write one before the pilot is cited as A4 motivation.
2. `ABSTRACT_SKELETON.md` (2026-08-28) predates Amendment 4 (its claims 8–9 make detection-only P4 the headline; claim 5 uses ESS-Wilson for P3; claim 11's 0.30 % is 0.299 %). OUTLINE §1.2 supersedes it.
3. New figure code (F3, F5, F6, F7) must not touch `scripts/generalization/*.py` while the D2 runner is live (campaign_file_shas drift guard); use a subdirectory. New v2 figure code (F9–F12) must not touch `scripts/v2/*.py` or `scripts/generalization/frozen_api.py` — the ADMITTED digest is locked into every dev/holdout run and the holdout lock; use `scripts/v2/analysis/` exclusively.
4. Verify at G6: AAS 249 character cap (https://aas.org/meetings/aas247/abstracts), RNAAS 1,500-word / one-table rule (https://journals.aas.org/research-note-preparation-guidelines/), ApJL page limit (http://w.astro.berkeley.edu/~rdawson/countwords.html).
5. Re-verify every column name in EVIDENCE_MAP against the real D3/D2 metrics headers at G5 (D3 columns confirmed against the real 2026-09-02 bundle already; D2 and every v2 column still to verify against a real `compare_engines.py` output once the holdout lands).
6. F12 (mechanism panel) and the coherence-failure stratification (V2-12, V2-13) have no aggregate script yet — write `scripts/v2/analysis/mechanism_summary.py` from the per-star v2 JSON fields named in EVIDENCE_MAP before figure freeze.
7. v2 is single-execution on the holdout (V2_PLAN.md §8): do not attempt a second holdout run for any reason (a different constants set, a code fix, a curiosity check) — the registered mode and the metrics/comparison checks refuse it by construction; if the holdout result looks wrong, the fix is a NEW pre-registration (a "v3"), never a rerun of this one.
8. Schedule (revised 2026-09-02): D3 numbers landed 2026-09-02. D2 frozen run in progress on the laptop, ETA ~2026-09-03 evening. v2: pre-registration ADMITTED 2026-09-02 (V2G1 round 6); dev runs (both trend windows) gated on the D2 chain finishing, ETA through ~2026-09-05/06; holdout ~2026-09-06/07; metrics (D2 frozen + v2 both datasets) by 2026-09-10; G5 (fresh verifier re-derivation, frozen AND v2) 2026-09-11–14; abstract draft + G6 (sol ×3) 2026-09-15–26; submit by 2026-09-30 (deadline). The 2026-09-22 decision point (CONTINGENCIES §4) governs whether v2 makes the submission; it is never on the critical path for D3/D2/D1.
