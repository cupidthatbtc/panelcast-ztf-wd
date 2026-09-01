# SUMMARY — writing outline for AAS 249 abstract, poster, and short paper (2026-09-01)

**Produced** (generalization/writing/outline/): OUTLINE.md (abstract slots, poster
sections + figure list, RNAAS and ApJL outlines, the not-allowed list),
EVIDENCE_MAP.md (60 claim rows → file → row selector → columns → prereg status),
CONTINGENCIES.md (strong / ugly / mixed branches, P5-fail, S14-fail, schedule),
this file. Mode: `academic-paper` outline-only. No numbers exist yet; every
result is a `⟨placeholder⟩` bound to a frozen metrics artifact.

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
DIAGNOSTIC · PROVENANCE · ANCHOR · PILOT (never a number). Amendment 4 is
respected: no estimand is created, renamed, swapped, or re-denominated anywhere.

**Not-allowed list** (28 items, OUTLINE Part D): no "selection-function
measurement" as the measured object, no pooling, no real-sky completeness from
D2, no "D3 FPR", no unqualified purity, no ZTF-g threshold from Kepler
amplitudes, no causal cadence claims, no "band"/CI on the 3×3 grid, no D2
row-level Wilson, no native-rate subtraction, no "corrected" P3, no pilot
numbers, no 928-catalog counts as completeness, Amendment 4 disclosed as
pilot-informed.

**Contingencies.** Ugly = pre-registered explanatory headline: bounded zeros
are measurements (one-sided 95 % CP: 0/610 → 0.49 %, 0/103 → 2.87 %, 0/48 →
6.05 %), strata make them explanatory (W_g pool 10/50/90 = 6/58/452; D3 median
dominant amplitude 1.77 mmag vs D1 median A95 5.2 mmag). Branch triggers,
replacement sentences, and figure changes are in CONTINGENCIES.md; table rows
and labels never change.

**Open items before G5/G6.**
1. `results/2026-08-30_d2_pilot_gen2/` has no README.md (the gen1 record does); write one before the pilot is cited as A4 motivation.
2. `ABSTRACT_SKELETON.md` (2026-08-28) predates Amendment 4 (its claims 8–9 make detection-only P4 the headline; claim 5 uses ESS-Wilson for P3; claim 11's 0.30 % is 0.299 %). OUTLINE §1.2 supersedes it.
3. New figure code (F3, F5, F6, F7) must not touch `scripts/generalization/*.py` while the runners are live (campaign_file_shas drift guard); use a subdirectory or wait for both runs to finish.
4. Verify at G6: AAS 249 character cap (https://aas.org/meetings/aas247/abstracts), RNAAS 1,500-word / one-table rule (https://journals.aas.org/research-note-preparation-guidelines/), ApJL page limit (http://w.astro.berkeley.edu/~rdawson/countwords.html).
5. Re-verify every column name in EVIDENCE_MAP against the real D3/D2 metrics headers at G5 (names were taken from the gen2 pilot outputs and `metrics_generalization.py`).
6. Slack vs plan: runs finish ~Sep 1/4 instead of W3; propose metrics by Sep 6, G5 by Sep 12, figure freeze Sep 19, G6 Sep 22–26, submit Sep 30.
