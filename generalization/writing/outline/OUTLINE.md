# Writing outline — AAS 249 abstract, poster, short paper

Campaign: astro-wd generalization (three separate response assessments of the
frozen 2026-08-01 pipeline). Produced 2026-09-01 with `academic-paper`
outline-only mode (structure_architect lens), before any full-run number exists.
Companion files: EVIDENCE_MAP.md (claim → artifact → prereg status),
CONTINGENCIES.md (strong / ugly branches), SUMMARY.md.

## 0. Conventions and constraints

### 0.1 Placeholders
Every number that does not yet exist is written `⟨P1 = xx% [lo, hi]⟩`. Fill
ONLY from the frozen metrics outputs named beside each slot; never from
`outputs/`, never from a pilot record, never from a notebook.

### 0.2 Pre-registration labels (mandatory on every claim, every figure caption, every table row)
| Label | Meaning | Authority |
|---|---|---|
| `PRIMARY-P1…P5` | prespecified primary tuple (METRICS_SPEC "Detection rules and the preregistered primary family"); P5 is the SOLE confirmatory decision | METRICS_SPEC.md (SHA after A4 `66013732…`), G2_FREEZE.md |
| `SECONDARY` | explicitly named secondary in the frozen spec (post-injection trigger rate; `best_candidate_matches_any_mode`; paired-control R/D diagnostics incl. P(R_B=1,R_C=0) and the quiet-control-conditioned estimand; exact McNemar D1/D3; P1 usable-denominator variant) | METRICS_SPEC.md |
| `DESCRIPTIVE-PRESPEC` | in the frozen spec, pointwise, no confirmatory weight (surfaces, sensitivity ranges, scenario contrasts, PPV, complementarity tables, attrition, FP-frequency audit, chance-match calibration, native trigger rate, D1 anchor counts) | METRICS_SPEC.md |
| `DESCRIPTIVE-POST-LAUNCH` | admitted after launch, pilot-informed; ships with the verbatim disclosure sentence; no interval, no veto, no reclassification. Currently exactly ONE artifact: `descriptive_postlaunch/d3_trigger_decomposition.csv` | G2_FREEZE.md 2026-08-31 entry; reviews/G5prep/sol_diurnal.md |
| `DIAGNOSTIC` | prespecified but explicitly non-inferential (D1 frequency recovery; arm-A positive injections; `any_top_peak_matches_any_mode`; Romero self-window arm; SAP re-dilution arm) | METRICS_SPEC.md, GENERALIZATION_PLAN.md |
| `PROVENANCE` | attested facts about the frozen pipeline (replay gates, tags, SHAs, env pins) | RUNBOOK.md, attestation/ |
| `PILOT` | never a result; may be cited only as the disclosed motivation for Amendment 4 | G2_FREEZE.md Amendment 4 |
| `V2-HOLDOUT` | a frozen-vs-v2 paired comparison endpoint on the pre-registered v2 holdout; a descriptive operational screen (STRONG/other), never a hypothesis test or a confirmatory decision; the v2 arm's own P5-analog (Gaussian nulls) is diagnostic screen only — it cannot meet the frozen P5 0.5 % criterion at n = 500 | `generalization/v2/V2_PLAN.md` §6–§7 (ADMIT: `reviews/V2G1/VERDICT.md`) |

Amendment 4 forbids any further estimand-hierarchy change. Nothing in this
outline creates, renames, swaps, or re-denominates an estimand. If a draft
sentence needs a quantity that has no row in the output inventory, the sentence
is cut, not the spec.

### 0.3 Venue rules (verify again at G6; sources in SUMMARY.md)
| Venue | Limit | Consequence for this outline |
|---|---|---|
| AAS 249 regular abstract (deadline Wed 2026-09-30; late 13–26 Oct) | ≤ 2,250 characters incl. spaces, single paragraph, plain text | The 250-word skeleton grows when placeholders expand to `x/610; 41%; 95% CI 37–45%`. Slots carry character budgets and drop tiers (§1.3). |
| RNAAS (primary short paper) | ≤ 1,500 words incl. title, headers, captions, references; 150 of them reserved for the required abstract; ONE figure OR ONE table (not both); table CONTENTS are exempt from the count, captions are not | One table, no figure. The table carries every endpoint; prose carries design + limits. |
| ApJL (fallback) | 5–6 typeset pages (AAS length calculator); redirect to ApJ/AJ if it cannot compress | ~3,500 words, ≤ 5 figures+tables. |
| Poster | AAS cap 45 × 45 in; existing D1 poster is 42 × 36 in, three columns | Reuse `poster/poster.html` layout classes verbatim (scoreline, defbox, tally, "does not establish" list). Chambliss = iPoster only. |

### 0.4 Data-availability status at outline time
D3 full run (2,901 crossmatched of 3,000 roster) completes the night of
2026-09-01; D2 full matrix (gen2: 3,089 shards = 309 B + 309 A + 824 ladder +
206 phase + 206 ampscale + 76 dropout + 33 cadence_alt + 20 redilution + 106
controls + 1,000 nulls) completes ≈ 2026-09-04. Metrics, G5 and figures follow.
Frozen inputs that MAY be quoted now (they are design facts, not results):
D3 roster 610/76/2,314 (KIC g ≥ 13.2; negatives SRS from 7,292, π = 2314/7292);
crossmatch freeze 2,901/3,000 (585/610 positives; 2,244/2,314 negatives;
72/76 flag2); crowding-clean subset 275; Mo-joined positives 456 (48 > 10 mmag,
254 in 1–10, 154 < 1; 154 unjoined; 290 sub-hour; median dominant amplitude
1.77 mmag); D2 103 targets, 341 modes, P = 115.9–1,879 s, A = 0.39–88.2 ppt,
g = 13.5–17.5, 49 with 20-s solutions, 33 mixed-cadence, 76 dropout-eligible,
106 unique arm-B windows; W_g pool 10/50/90th = 6/58/452, surface edges
{15, 41, 84, 217}; P5 arithmetic at n = 1000: x = 0 → U95 = 0.299 %,
x = 1 → 0.474 % (accept), x = 2 → 0.628 % (reject).

**D3 frozen headline numbers now exist** (`generalization/results/2026-09-02_d3/README.md`,
certified GUARD PASS) and may be quoted with their file bindings: P1 610→327
(0.536 [0.496, 0.575]); P1 usable 585→327 (0.559 [0.518, 0.599]); P2 441→72
(0.163 [0.132, 0.201]), correct-frequency fraction among detected 238→72
(0.303 [0.248, 0.364]); P3 2,314→963 (0.416 [0.396, 0.436]), census 65
(0.028 [0.022, 0.036]), either 993 (0.429 [0.409, 0.449]); census completeness
25/610 (0.041 [0.028, 0.060]); union 334/585 (0.571 [0.530, 0.610]); PPV
0.097 [0.094, 0.101]; contingency 18/7/309/251, incremental census 0.012,
incremental LS 0.528, McNemar p = 9e-82; chance direct-match mean 0.0037,
p95 0.0091. D2 full run still in progress on the laptop.

**v2 detector arm** (`generalization/v2/V2_PLAN.md`, ADMIT at V2G1 round 6,
`reviews/V2G1/VERDICT.md`, 2026-09-02): a second, pre-registered detector fixing
the four mechanisms the D3 descriptive tables diagnosed (oid zero-point
alignment, an extended alias veto, a joint two-band finder with a
phase-coherence gate, support-aware detrending), judged ONCE on an odd-KIC/
odd-TIC holdout against the frozen arm on the same stars
(`scripts/v2/compare_engines.py`). Status at outline time: code ADMITTED,
digest locked, dev runs not yet started (gated on the frozen D2 run finishing).
No v2 number exists yet; every v2 slot below is conditional on the holdout
landing before G6 — see CONTINGENCIES.md §6.

---

## Part A — AAS 249 abstract outline (sentence-level slots)

### 1.1 Title candidates (choose at G6; none may contain "selection function" as the measured object)
1. *How a frozen ZTF variability pipeline responds beyond its development sample: an externally labeled Kepler δ Scuti test and TESS-DAV injection recovery*
2. *Three separate response assessments of a frozen variance-census and Lomb–Scargle search on ZTF photometry*
3. *Class-specific completeness and trigger rates of a frozen ZTF variability search: Kepler δ Scuti validation, TESS-DAV injections, and a white-dwarf anchor*

"Selection function" is admissible only in the motivation sentence (what
surveys need), never as the thing measured (G1 referee objection 20;
GENERALIZATION_PLAN banned phrases).

### 1.2 Sentence slots
Budget column = characters incl. spaces AFTER placeholder expansion. Tier A =
must survive; Tier B = drop in the listed order if over 2,250. Column "Artifact"
gives file → row selector → columns; full detail in EVIDENCE_MAP.md.

| Slot | Tier | Budget | Sentence template (fill from artifact) | Artifact (row selector) | Label |
|---|---|---|---|---|---|
| S1 | A | 120 | Wide-field variability searches must quantify how frozen decision rules respond beyond their development sample. | — (framing) | — |
| S2 | A | 200 | We evaluate a frozen ZTF variance-census and blind Lomb–Scargle pipeline (tag `frozen-2026-08-01`; 928/928 published stars replayed byte-identically) through three deliberately separate assessments. | attestation/laptop_replay_full_2026-08-29/ (921 identical_v1_schema + 7 identical_newline) | PROVENANCE |
| S3 | A | 210 | D3, the only external-label test on real ZTF photometry, applies it to a magnitude-restricted (KIC g ≥ 13.2) Kepler A/F frame: all 610 Murphy et al. δ Scuti stars and a frozen-seed random sample of 2,314 non-δ-Scuti stars (76 dSct=2 objects excluded from headlines). | data/d3/roster_report.json → counts | design fact |
| S4 | A | 200 | D2 measures conditional injection-recovery of the search stage: 103 Romero et al. TESS DAV mode solutions transplanted into three magnitude-matched real ZTF windows each, stratified by the within-night support W_g that survives nightly-median subtraction. | results/…_d2/run/generation_manifest_gen2.json → n_targets_scheduled, wg_pool_quantiles | design fact |
| S5 | A | 60 | D1 is the published 19-star white-dwarf anchor. | lomb-scargle/results/2026-08-01_full/master_table.csv | ANCHOR |
| S6 | A | 190 | D3 confirmed-rule detection completeness is ⟨x/610; p %; 95 % Wilson lo–hi⟩ on the eligible roster and ⟨x_u/n_u; p_u %; lo–hi⟩ among usable light curves. | completeness_by_class_pass_rule.csv → pass=best, rule=confirmed, scope ∈ {detection_eligible_roster, detection_usable_lightcurve} → n, p, lo, hi | PRIMARY-P1 (eligible); SECONDARY (usable) |
| S7 | A | 190 | Among the ⟨n_S⟩ Mo-joined positives with a dominant frequency inside the search bounds, ⟨x/n_S; p %; lo–hi⟩ yield a confirmed best candidate directly matching the historical dominant frequency, against an accidental-match rate of ⟨p_acc %⟩. | same file → scope=freq_recovery_scorable, rule=confirmed, pass=best; chance_match.json (D3: 100 permutations, seed 20260829) | PRIMARY-P2 |
| S8 | B (drop 1st) | 150 | Detection completeness is ⟨p_lo⟩ below 1 mmag and ⟨p_hi⟩ above 10 mmag of historical Kepler-band dominant amplitude, with 154 unjoined positives kept in an explicit unknown-amplitude bin. | surfaces/detection_amplitude.csv → amp_bin (edges 0.5,1,2,5,10,20,50; bin −1 = amp_unknown) → n, k | DESCRIPTIVE-PRESPEC |
| S9 | A | 150 | The confirmed negative-class trigger rate is ⟨k/2314; p %; Wilson lo–hi⟩, for a class that can contain other genuine variables. | trigger_rates.csv → quantity=negative_class_trigger_rate, rule=confirmed → n, p, lo, hi | PRIMARY-P3 |
| S10 | B (drop 2nd) | 170 | Census-only and Lomb–Scargle-only detections are ⟨x_C/n⟩ and ⟨x_L/n⟩ of positives with both methods available (union ⟨x_U/n; p %; lo–hi⟩). | contingency_complementarity.json (D3) → table, incremental_*, union_completeness | DESCRIPTIVE-PRESPEC |
| S11 | A | 190 | D2 nominal confirmed dominant-mode recovery is ⟨p %; target-cluster 95 % lo–hi⟩ (eligible denominator; ⟨p_u %⟩ usable), ⟨p_K0 / p_K1 / p_K2⟩ across low/median/high-W_g strata. | d2_cluster_completeness.csv → arm=B, scenario=nominal, endpoint=recovery, denominator ∈ {eligible, usable}; surfaces/recovery_wg_amplitude.csv (marginal over amp_bin per wg_bin, target-level) | PRIMARY-P4; strata DESCRIPTIVE-PRESPEC |
| S12 | B (drop 3rd) | 170 | Median-window recovery spans ⟨p_min–p_max⟩ over the prespecified 3 × 3 bandpass grid; paired uninjected controls recover the injected dominant mode in ⟨x_c/m⟩ pairs. | d2_scenario_contrasts.csv → scenario ∈ ladder_*, endpoint=recovery → p_scenario (min/max, endpoints named); d2_paired_controls_summary.csv → endpoint=R → c_only, p_c | DESCRIPTIVE-PRESPEC; SECONDARY |
| S13 | A | 140 | Zero-amplitude Gaussian nulls give FPR_Gaussian = ⟨x/1000⟩ (one-sided 95 % Clopper–Pearson upper ⟨U %⟩), ⟨meeting / failing⟩ the preregistered ≤ 0.5 % acceptance. | trigger_rates.csv → quantity=fpr_gaussian → k, cp_one_sided_95_upper, acceptance_u95_leq_0.005, confirmatory_decision | PRIMARY-P5 (sole confirmatory) |
| S14 | A | 130 | In each assessment the census and period-search responses remain empirically non-overlapping; the three are reported side by side, not pooled. | contingency_complementarity.json for D1, D2 (descriptive counts), D3: BOTH discordant cells > 0 in each, else rewrite (see CONTINGENCIES §3) | DESCRIPTIVE-PRESPEC (conditional sentence) |
| S15 | C (conditional; cut if the v2 holdout has not landed by G6) | 220 | After inspecting the frozen arm's descriptive failure analysis, a pre-registered v2 detector (aligned zero points, phase-coherent two-band amplitude, an extended alias veto) was evaluated once on an odd-ID holdout excluding four development stars: negative-class trigger rate ⟨p3_v2⟩ vs ⟨p3_frozen⟩ (paired Δ ⟨lo, hi⟩), detection completeness ⟨p1_v2⟩ vs ⟨p1_frozen⟩, ⟨x/500⟩ Gaussian nulls triggering. | `scripts/v2/compare_engines.py` output `endpoints.csv` → endpoint ∈ {P1_detection, P3_negative_trigger, P5_gaussian_false_alarm} → frozen_p/lo/hi, v2_p/lo/hi, diff, diff_lo, diff_hi, mcnemar_exact_p | V2-HOLDOUT |
| S16 | C (conditional, ships only with S15) | 260 | V2_PLAN.md §7 disclosure sentence, VERBATIM: "After full-cohort frozen-arm failure analysis, we fixed a digest-locked but not byte-replay-attested v2 detector, extended its fixed window-veto loci once after inspecting development-half results, selected four prespecified constants on development data, and evaluated it once on an internal odd-ID holdout excluding four stars used during development; this is post-selection internal validation, not confirmatory external validation." | `generalization/v2/V2_PLAN.md` §7 | V2-HOLDOUT (mandatory disclosure, verbatim, not paraphrased) |

Tier A total ≈ 1,780 characters; Tier B adds ≈ 490 → 2,270. Expect to keep
two of S8/S10/S12. Character count is decided at G6 on the filled text. S15/S16
(≈ 480 chars together) are OUTSIDE this budget: they replace nothing and are
included only if they fit after every Tier-A/B slot is filled and only if the
v2 holdout numbers exist (V2_PLAN.md §6 STRONG/other reading, never a
hypothesis test); if they do not fit or do not exist, the abstract states the
frozen calibration alone and closes with "a redesigned rule (v2) is under
evaluation on a pre-registered holdout; results follow at the poster
(January)" in place of S15, dropping S16 — see CONTINGENCIES.md §6.4.

### 1.3 Abstract rules of construction
- Word/phrase substitutions are fixed by METRICS_SPEC vocabulary: "detection completeness", "frequency-recovery completeness", "correct-frequency fraction among detected positives", "negative-class trigger rate", "Gaussian-null false-alarm rate (FPR_Gaussian)", "conditional injection-recovery efficiency of the search stage", "native trigger rate of the template pool", "post-injection rule-1 trigger rate", "frame-specific label PPV", "prespecified finite-grid sensitivity range".
- Every D3 number states its denominator (610 / n_usable / 456-or-n_S / 2,314). Every D2 number states cluster = TIC and that inference is conditional on the frozen window assignment (one clause suffices in the abstract).
- The pilot numbers (16/30, 7/30, 8/10, 10/10) never appear.
- The 928-catalog counts (109/233/94/492; 327) never appear as completeness; they are D1 descriptives only and are out of the abstract.
- The descriptive diurnal partition is NOT in the abstract (post-launch; no interval).
- S15/S16 use the v2 vocabulary fixed by V2_PLAN.md: "pre-registered v2 detector", "odd-ID holdout", "internal post-selection validation" (never "external" or "confirmatory"); the disclosure sentence (S16) is quoted verbatim, never paraphrased; the STRONG/other reading is reported as a descriptive operational screen, never as a hypothesis test or a p-value claim.
- No v2 number is dev-half; no v2 number predates the holdout lock (`generalization/v2/HOLDOUT_LAUNCH_<dataset>.json`); the four `dev_smoke` stars never appear in a v2 abstract number.
- Keywords (AAS category picks): stellar pulsations; time-domain astronomy; sky surveys; astronomy data analysis; white dwarf stars; δ Scuti stars.

---

## Part B — Poster outline

Layout: reuse `poster/poster.html` (42 × 36 in, three columns, Times, the
`.scoreline`, `.defbox`, `.tally`, "What this does not establish" and "What was
frozen, and when" blocks). No new CSS. Figures regenerate from CSVs only
(METRICS_SPEC "Figures via plot_generalization.py from these CSVs only"; the
v2 synthesis figures regenerate from `compare_engines.py` outputs only).

Operational gotcha: `scripts/generalization/*.py` (non-recursive) is the
`campaign_file_shas()` drift-guard surface for the LIVE runners. Do not edit
`plot_generalization.py` until both runs have finished and metrics are
computed; until then, new figure functions go in a subdirectory (pattern already
used: `scripts/generalization/descriptive/`), e.g. `scripts/generalization/figures/`.
The v2 figures have the SAME constraint one level over: `scripts/v2/*.py` plus
`scripts/generalization/frozen_api.py` is the ADMITTED v2 code digest bound
into every dev/holdout run and lock — new v2 figure code goes in
`scripts/v2/analysis/` (already the home of `veto_exposure.py`/
`leakage_audit.py`) and NEVER touches `scripts/v2/*.py` while a dev or holdout
run is live, or the digest gate refuses every subsequent stage.

For the January poster (v2 confirmed as the deliverable regardless of the
abstract's fate — CONTINGENCIES.md §6.4), the layout below is the full,
eight-plus-four-figure version; if v2 has not reached the holdout by the
AAS 249 poster print date, §6/F9–F12 are omitted and the poster reverts to
the seven-section, eight-figure layout below.

### 2.1 Header
- Title: one of §1.1. Subtitle: "three separate response assessments of one frozen pipeline".
- Claim paragraph (`.claim`): the S14 sentence + "each estimate is reported with its own denominator and interval; nothing is pooled".
- Scoreline (six `.score` tiles): P1 ⟨x/610⟩ · P2 ⟨x/n_S⟩ · P3 ⟨k/2314⟩ · P4 ⟨p % [lo, hi]⟩ · P5 ⟨x/1000, U95⟩ · "3 assessments, 0 pooled".

### 2.2 Sections (column order)
| § | Heading | Content | Feeds |
|---|---|---|---|
| 1 | Why three separate assessments | The D1 red-team verdict (NO-GO as discovery; flip condition = frozen pipeline on externally labeled large-N samples); the G1 correction that D2 is not an external label; one line per dataset on what it can and cannot claim. | GENERALIZATION_PLAN.md "Claim under test" |
| 2 | The frozen pipeline | Two `.defbox` blocks copied from the D1 poster (variance census R ≥ 2.5 over six band × cadence ratios; two-pass alias-vetted L-S with the cross-band confirmed rule). Provenance strip: tag, 928/928 replay, panel golden gate, CLI identity, env pins, spec SHA, Amendments 2–4 disclosed as pre-confirmatory, Amendment 4 pilot-informed. | RUNBOOK.md, G2_FREEZE.md |
| 3 | D3 — external-label validation on real ZTF photometry | Figures F1–F4; `.tally` of the attrition chain 3,000 → 2,901 crossmatched → ⟨usable⟩ → ⟨both passes⟩ by class. | attrition.csv; data/d3/crossmatch_freeze/attrition_by_class.csv |
| 4 | D2 — conditional injection-recovery of the search stage | Figures F5–F7; one-paragraph design (truth model, sinc de/re-integration, bandpass grid, W_g strata, K = 3, paired controls, 1,000 Gaussian nulls). | GENERALIZATION_PLAN.md D2 design |
| 5 | D1 — the finite-roster anchor | Figure F8 (reuse `figures/headtohead.png`); tally 11/13 · 9/13 · 13/13 · 0/5 confirmed (+1 candidate). | master_table.csv; METRICS_SPEC D1 validation on record |
| 6 (conditional; drop if v2 has not reached the holdout) | v2 — a redesigned detector on a pre-registered holdout | The disclosure sentence (S16, verbatim) as the section lede; Figures F9–F12; a `.defbox` naming the four fixed mechanisms (align/veto/joint+coherence/detrend) beside the frozen `.defbox` of §2. | V2_PLAN.md §1–§2, §7; `scripts/v2/compare_engines.py` outputs |
| 7 | What this does not establish | Rendered from Part D (poster-length version: 6 bullets, + the v2 bullets N29–N34 if §6 is present). | Part D |
| 8 | What was frozen, and when | Pre-registration timeline: spec frozen 2026-08-28 (G2, 6 rounds), A2/A3 2026-08-30 (pre-run), A4 2026-08-30 (post-pilot, pre-confirmatory, disclosed), descriptive diurnal admission 2026-08-31 (post-launch, disclosed); v2 pre-registered 2026-09-02, V2G1 ADMIT at round 6 (5 REVISE rounds closed) same day. | G2_FREEZE.md; `reviews/V2G1/VERDICT.md` |
| Footer | Take-away, data & code, acknowledgements, references | Take-away = S14 + "variability flags should ship with class-specific response estimates and their denominators". Mandatory citations: Sokolovsky+2017, Guidry+2021, Hermes+2017, Murphy+2019, Bowman+2016, Mo+2026, Romero+2022, Romero+2025, Gentile Fusillo+2021, Masci+2019, Jestin arXiv:2509.15133. | GENERALIZATION_PLAN.md "Mandatory citations" |

### 2.3 Figure list
| Fig | Must show | Must NOT show | Feed (file → columns) | Label | Plot code |
|---|---|---|---|---|---|
| F1 D3 turn-on | Rule-1 best-pass detection completeness vs historical Kepler-band dominant amplitude, half-open bins {0.5,1,2,5,10,20,50,∞} mmag plus an explicit `amp_unknown` bar (154 stars); pointwise Wilson only where n ≥ 5, counts otherwise; second panel: frequency-recovery over the scorable subset. | Smoothed/fitted curve; any ZTF-g threshold reading; interpolation | surfaces/detection_amplitude.csv, surfaces/freq_recovery_period_amplitude.csv (marginalize) → amp_bin, n, k | DESCRIPTIVE-PRESPEC | exists: `plot_turn_on` → turn_on_amplitude.png (verify it renders bin −1) |
| F2 D3 rules × scopes | Four rules (confirmed, confirmed_or_candidate, census, either) × best pass × three scopes (eligible, usable, freq-scorable) with Wilson bars; P1 and P2 bars outlined as the primaries | "purity"; the 928 catalog | completeness_by_class_pass_rule.csv → pass=best → rule, scope, n, p, lo, hi | PRIMARY-P1/P2 highlighted; rest DESCRIPTIVE-PRESPEC | exists: `plot_completeness` → completeness_rules.png |
| F3 D3 negatives | (a) negative-class trigger rate per rule with plain Wilson (P3 = confirmed); (b) histogram of best-pass frequencies of confirmed negatives (the prespecified FP-frequency audit) with the solar-diurnal bands [k ± 0.020] d⁻¹ shaded and the within/outside counts annotated; caption carries the verbatim disclosure sentence. | Any "corrected" or "de-aliased" rate; any interval on the partition; use on census triggers | trigger_rates.csv → negative_class_trigger_rate; fp_frequency_distribution.csv → best_frequency_per_day, best_pass; descriptive_postlaunch/d3_trigger_decomposition.csv → component, n_component, rate_of_all_negatives, share_of_confirmed | PRIMARY-P3; DESCRIPTIVE-PRESPEC (audit); DESCRIPTIVE-POST-LAUNCH (bands) | NEW |
| F4 D3 complementarity | 2 × 2 census × L-S on positives with both methods usable; both discordant cells; union and incremental yields with Wilson; exact McNemar p in caption as secondary | Any "complementarity proven by McNemar" wording | contingency_complementarity.json (D3) | DESCRIPTIVE-PRESPEC; McNemar SECONDARY | exists: `plot_contingency` → contingency.png |
| F5 D2 recovery surface | Target-level recovery on (W_g stratum, published TESS amplitude ppt) with edges W_g {15,41,84,217}, A {0.5,2,5,10,30,∞}; n_targets per cell; cluster interval only where ≥ 5 targets; side panel: P4 eligible & usable with cluster CI and the K0/K1/K2 marginals | Ladder-scaled amplitudes; window-level Wilson; pooled scenarios | surfaces/recovery_wg_amplitude.csv → wg_bin, amp_bin, n_windows, k_windows, n_targets; d2_cluster_completeness.csv → arm=B, scenario=nominal, endpoint=recovery | PRIMARY-P4 (side panel); DESCRIPTIVE-PRESPEC (surface) | NEW |
| F6 D2 sensitivity | Paired scenario-minus-nominal-K1 differences with common-draw intervals for the 8 ladder points, phase_1/2, ampscale 0.7/1.3, dropout, cadence_alt; degenerate rows drawn as the CP discordance bound (marked); endpoint scenarios of the min–max named | A "band"; a CI on the min–max; crossing of axes | d2_scenario_contrasts.csv → scenario, endpoint=recovery, denominator=eligible → diff, diff_lo, diff_hi, discordance_u95, interval | DESCRIPTIVE-PRESPEC | NEW |
| F7 D2 nulls & controls | (a) FPR_Gaussian: x/1000 with the exact one-sided CP upper and the 0.5 % acceptance line; (b) paired controls: 2 × 2 for D and for R, b_only / c_only / union, P(R_B=1,R_C=0) with cluster CI; (c) native trigger rate of the 106 control windows with reuse counts | "real-sky FPR"; subtraction of the native rate from P4 | trigger_rates.csv → fpr_gaussian, native_trigger_rate; d2_paired_controls_summary.csv → endpoint ∈ {D,R}; d2_control_reuse.csv → n_b_assignments | PRIMARY-P5; SECONDARY (paired R/D); DESCRIPTIVE-PRESPEC (native) | NEW |
| F8 D1 anchor | Reuse `poster/figures/headtohead.png` (blind L-S period vs g amplitude, 19 stars, channel colour) with the finite-roster caption | Any population completeness reading | committed D1 tables (talk/data) | ANCHOR (DESCRIPTIVE-PRESPEC counts) | exists (MATLAB) |
| F9 frozen vs v2, paired endpoints (holdout) | Per-endpoint frozen/v2 point + Wilson (CP upper for the null screen) with the paired difference and its interval, for P1, P3, P3 by pass, P2 (with chance-match rates of both bundles), and D2 P4 recovery (eligible & usable), P4 trigger, the null screen, and the two paired-control contrasts; exact McNemar p annotated where computed | Any p<0.05 framing; any claim the difference is "significant"; any number from the dev half | `scripts/v2/compare_engines.py` → `endpoints.csv` → endpoint, n, frozen_p/lo/hi, v2_p/lo/hi, diff, diff_lo, diff_hi, mcnemar_exact_p, frozen/v2_chance_direct_mean/p95 (P2 rows) | V2-HOLDOUT | NEW |
| F10 status transitions + availability | Frozen→v2 best-status transition counts by class (D3) / arm (D2); a second panel of frozen-usable × v2-usable counts | Any "improvement rate" without the transition table beside it | `compare_engines.py` → `status_transitions.csv` (class_label\|arm, frozen_best_status, v2_best_status columns), `availability_transitions.csv` (class_label\|arm, frozen_usable, v2_usable, n) | V2-HOLDOUT (descriptive) | NEW |
| F11 veto exposure + leakage audit | (a) fraction of truth frequencies vetoed by component (fixed loci, data-driven peaks, local test, mirror family, cross-pass partners) and their union, by pass/band; (b) the low-frequency injection leakage audit on dev windows: high-pass confirmed-count with vs without the injection, and how many new confirmations are alias partners of the injection | Any claim the veto "does not affect" science frequencies; any leakage number from the holdout | `scripts/v2/analysis/veto_exposure.py` → `veto_exposure_summary.csv` (pass, band, veto_fixed/_data/_local/_stronger/_cross_pass/_union _mean/_sum, n); `leakage_audit.py` → `leakage_audit_summary.json` (n, injection, high_confirmed_reference/_injected, high_new_confirmations_that_are_partners, low_detects_injection) | V2-HOLDOUT (descriptive; dev-window audit) | NEW |
| F12 v2 mechanism panel | (a) per-oid alignment: offset (mmag) vs shared-night count, applied/unshifted marked; (b) coherence-gate failures stratified by phase-error and amplitude S/N, confirmed vs candidate outcome | Any causal reading of the strata; any claim alignment offsets are astrophysical | per-star v2 JSON `v2.alignment` (band, oid, n, n_shared_nights, offset_mmag, applied, role) and `passes[p]["v2"].candidates[]` (delta_phase_cycles, amp_ratio_r_over_g, coherent) aggregated by a not-yet-written script (`scripts/v2/analysis/mechanism_summary.py` — open item, SUMMARY.md) | V2-HOLDOUT (descriptive) | TBD script |

Poster figure priority if space binds: F1, F5, F7, F3, F2, F6, F4, F8, then
(if v2 landed) F9, F1[0-2] in that order — F9 (the headline comparison) never
drops before F6.

---

## Part C — Short paper outline

### 3.1 Primary: RNAAS (≤ 1,500 words all-in; one TABLE, no figure)
Rationale for table-not-figure: table contents are exempt from the word count,
so the whole endpoint inventory (with denominators, intervals, and prereg
labels) fits without consuming prose budget; a single figure could not carry
five primaries plus their denominators legibly.

Word budget (total 1,500 incl. references; 50-word reserve):
| Block | Words | Content |
|---|---|---|
| Title + authors + affiliations | 30 | Title from §1.1 (shorter variant 2). |
| Abstract | 150 | S1, S2 (short), S3+S4 compressed, S6, S9, S11, S13, S14. |
| §1 Motivation and design | 220 | C1–C3 |
| §2 Frozen pipeline, datasets, estimands | 300 | C4–C8 |
| §3 Results (Table 1) | 320 | C9–C15 |
| §4 What is and is not established | 240 | C16–C19 |
| Table 1 caption | 60 | counts against the limit |
| Acknowledgements + software | 30 | ZTF/IRSA, TESS/MAST, VizieR; astropy, numpy, scipy versions pinned |
| References | 100 | 8 entries max: Murphy+2019, Mo+2026, Romero+2022, Romero+2025, Sokolovsky+2017, Guidry+2021, Masci+2019, Jestin arXiv:2509.15133 (Hermes+2017, Bowman+2016, Gentile Fusillo+2021 move to the ApJL fallback) |

Table 1 — "Prespecified endpoints of three separate response assessments"
Columns: Assessment | Estimand (binding name) | Denominator | Rule / pass |
Estimate | 95 % interval (method) | Status. Rows (order fixed):
1. D3 detection completeness — eligible roster — 610 — rule 1 / best — ⟨⟩ — Wilson — PRIMARY-P1
2. D3 detection completeness — usable light curves — ⟨n_u⟩ — rule 1 / best — ⟨⟩ — Wilson — SECONDARY
3. D3 frequency-recovery completeness — Mo-joined, S_best = 1 — ⟨n_S⟩ — rule 1 + dominant direct — ⟨⟩ — Wilson; chance rate ⟨⟩ — PRIMARY-P2
4. D3 correct-frequency fraction among detected positives — ⟨n_det⟩ — ⟨⟩ — Wilson — DESCRIPTIVE-PRESPEC
5. D3 negative-class trigger rate — 2,314 dSct=0 — rule 1 / best — ⟨⟩ — plain Wilson — PRIMARY-P3
6. D3 frame-specific label PPV — weighted frame (dSct=2 excluded) — ⟨⟩ — FPC survey bootstrap — DESCRIPTIVE-PRESPEC
7. D3 census-only / L-S-only / union — positives with both methods — ⟨⟩ — Wilson — DESCRIPTIVE-PRESPEC
8. D2 conditional injection-recovery, nominal arm B — 103 targets (eligible) — ⟨⟩ — target-cluster bootstrap — PRIMARY-P4
9. D2 same, usable — 103 − n_∅ — ⟨⟩ — cluster bootstrap — PRIMARY-P4 (usable variant)
10. D2 recovery by W_g stratum K0 / K1 / K2 — 103 each — ⟨⟩ — cluster bootstrap — DESCRIPTIVE-PRESPEC
11. D2 prespecified finite-grid sensitivity range (median window, 3 × 3 bandpass) — ⟨p_min (scenario)–p_max (scenario)⟩ — none (range) — DESCRIPTIVE-PRESPEC
12. D2 post-injection rule-1 trigger rate — 103 — ⟨⟩ — cluster bootstrap — SECONDARY
13. D2 paired controls, P(R_B = 1, R_C = 0) — ⟨n_pairs⟩ — ⟨⟩ — cluster bootstrap — SECONDARY
14. D2 native trigger rate of the template pool — 106 control windows — ⟨⟩ — descriptive — DESCRIPTIVE-PRESPEC
15. D2 FPR_Gaussian — 1,000 nulls — ⟨x/1000⟩ — one-sided CP upper ⟨U⟩; acceptance ≤ 0.5 % ⟨PASS/FAIL⟩ — PRIMARY-P5 (confirmatory)
16. D1 anchor: L-S 11/13, census 9/13, union 13/13, constants 0/5 confirmed (+1 candidate) — 13 / 5 — Wilson — ANCHOR

Rows 17–23 (CONDITIONAL: appended only if the v2 holdout has landed by G6;
Status column reads "holdout, post-selection internal validation" on every
v2 row; source `compare_engines.py` → `endpoints.csv` unless noted):
17. v2 D3 detection completeness, paired vs frozen — 299 (flag1 roster) — ⟨⟩ — Wilson + paired diff + McNemar — holdout, post-selection internal validation
18. v2 D3 frequency-recovery, paired vs frozen (frozen P2 frame) — ⟨n⟩ — ⟨⟩ — Wilson + paired diff + McNemar; chance-match both bundles — holdout, post-selection internal validation
19. v2 D3 negative-class trigger rate, paired vs frozen — 1,149 (flag0 roster) — ⟨⟩ — Wilson + paired diff + McNemar — holdout, post-selection internal validation
20. v2 D2 conditional recovery, nominal arm B, eligible & usable, paired vs frozen — 43 targets — ⟨⟩ — target-cluster bootstrap paired diff — holdout, post-selection internal validation
21. v2 D2 paired-control contrasts (trigger; strict recovery), paired vs frozen — 67 controls — ⟨⟩ — target bootstrap — holdout, post-selection internal validation
22. v2 D2 null screen (descriptive; NOT the frozen P5 decision) — 500 holdout nulls — ⟨x/500⟩ — one-sided CP upper — descriptive operational screen, not confirmatory
23. v2 truth-frequency veto exposure, by component and union — ⟨⟩ — ⟨⟩ — descriptive — DESCRIPTIVE (mechanism)

### 3.2 Paragraph-level claims (RNAAS; each with artifact + status; full table in EVIDENCE_MAP.md)
| ID | Section | Claim (one sentence each) | Evidence artifact | Status |
|---|---|---|---|---|
| C1 | §1 | Variability flags in sparse surveys are rule outputs; their class-specific response must be measured on labels the rule never saw. | Sokolovsky+2017; Guidry+2021 (context) | framing |
| C2 | §1 | The published D1 result (19 labeled WDs) showed complementary census/L-S responses but could not support a discovery or completeness claim. | poster/drafts/ABSTRACT.md red-team verdict; master_table.csv | ANCHOR |
| C3 | §1 | We therefore ran the pipeline, frozen and attested, on two new samples designed as separate response assessments with pre-registered estimands. | G2_FREEZE.md; METRICS_SPEC.md SHA | PROVENANCE |
| C4 | §2 | The pipeline is byte-frozen (tag; empty `git diff` on the five scripts; 928/928 replay; env pins). | attestation/laptop_replay_full_2026-08-29 | PROVENANCE |
| C5 | §2 | D3: Murphy+2019 dSct flags as labels obtained independently of the pipeline; KIC g ≥ 13.2; 610 positives, 2,314 SRS negatives (π = 2314/7292), dSct=2 excluded; Mo+2026 dominant amplitudes for 456. | roster_report.json; crossmatch_freeze/ | design |
| C6 | §2 | D2: Romero+2022/2025 mode tables evaluated analytically (signed-sinc de/re-integration, bandpass grid with nominal 1.7/0.80) into K = 3 W_g-stratified real ZTF windows for 103 targets; paired uninjected controls; 1,000 Gaussian nulls. | generation_manifest_gen2.json; GENERALIZATION_PLAN.md | design |
| C7 | §2 | Estimand names and the five-member primary family were frozen before the first confirmatory run; Amendment 4 (recovery endpoint; W_g strata) is pilot-informed and disclosed; P5 is the sole confirmatory decision. | G2_FREEZE.md Amendment 4 | PROVENANCE |
| C8 | §2 | D2 inference clusters on the TESS target and is conditional on the frozen window assignment; D3 inference is star-level Wilson. | METRICS_SPEC "Units of analysis" | PROVENANCE |
| C9 | §3 | P1 sentence (S6). | completeness_by_class_pass_rule.csv | PRIMARY-P1 |
| C10 | §3 | P2 sentence (S7) with chance rate. | same + chance_match.json | PRIMARY-P2 |
| C11 | §3 | Turn-on sentence (S8) with the sub-1 mmag majority explicitly counted. | surfaces/detection_amplitude.csv | DESCRIPTIVE-PRESPEC |
| C12 | §3 | P3 sentence (S9); PPV and adjudicated components in Table 1 only. | trigger_rates.csv; ppv.csv | PRIMARY-P3; DESCRIPTIVE-PRESPEC |
| C13 | §3 | P4 sentence (S11) + strata + grid range (S12). | d2_cluster_completeness.csv; surfaces/recovery_wg_amplitude.csv; d2_scenario_contrasts.csv | PRIMARY-P4; DESCRIPTIVE-PRESPEC |
| C14 | §3 | Controls: paired R yields and native trigger rate (numbers in Table 1). | d2_paired_controls_summary.csv; trigger_rates.csv | SECONDARY; DESCRIPTIVE-PRESPEC |
| C15 | §3 | P5 sentence (S13). | trigger_rates.csv | PRIMARY-P5 |
| C16 | §4 | Per-dataset non-redundancy sentence (S14), conditional on both discordant cells. | contingency_complementarity.json ×3 | DESCRIPTIVE-PRESPEC |
| C17 | §4 | D2 is not real-sky completeness (template selection, phases, stationarity, bandpass, upstream processing); D3 is a g ≥ 13.2 Kepler-field statement; the negative class contains real variables; amplitudes are historical Kepler-band; Mo-join missingness is informative. | METRICS_SPEC limitations; G1 RESPONSE | limitation |
| C18 | §4 | Post-launch descriptive: the confirmed-negative frequencies concentrate in / outside the solar-diurnal bands in ⟨n_w / n_o⟩; disclosure sentence verbatim; no correction applied. | descriptive_postlaunch/d3_trigger_decomposition.csv | DESCRIPTIVE-POST-LAUNCH |
| C19 | §4 | Recommendation: survey variability flags should ship with class-specific response estimates and their denominators. | — | framing |
| C20 | §3 (conditional) | v2 sentence (S15) with the paired P1/P3/P5-screen differences and their intervals. | `compare_engines.py` → `endpoints.csv` | V2-HOLDOUT |
| C21 | §3 (conditional) | v2 D2 sentence: conditional recovery and the paired-control contrasts, eligible & usable. | same → `P4_recovery_eligible/_usable`, `control_contrast_*` | V2-HOLDOUT |
| C22 | §4 (conditional) | v2 disclosure sentence (S16), verbatim; the STRONG/other reading is a descriptive operational screen, never a hypothesis test; the four `dev_smoke` stars are excluded from every number. | `generalization/v2/V2_PLAN.md` §7 | V2-HOLDOUT (mandatory if §3 v2 claims appear) |
| C23 | §4 (conditional) | v2 is an internal post-selection validation (architecture chosen from the same D3 campaign the holdout is drawn from); it does not establish external validity beyond the frozen arm's own limits (C17). | V2_PLAN.md §1 "What the holdout validates" | limitation |
| C24 | §4 (conditional) | Truth-frequency veto exposure and the leakage audit are reported so the extended veto's cost is visible, not asserted away. | F11 artifacts | V2-HOLDOUT (descriptive) |

If §3/§4 v2 claims (C20–C24) are included, reallocate ≈ 70 words from §2 (300→270)
and ≈ 50 from the Abstract block (already absorbed by S15/S16 being outside its
budget); if v2 has not landed, C20–C24 and Table 1 rows 17–23 are cut entirely
and the RNAAS budget in §3.1 is unchanged.

Transitions: §1 ends on "what the three samples can and cannot claim" → §2
opens with the freeze; §2 ends on the estimand family → §3 opens with Table 1;
§3 ends on P5 → §4 opens with what P5 does and does not bound.

### 3.3 Fallback: ApJL-length (5–6 pages; ≤ 5 figures/tables; ~3,500 words)
| § | Title | Words | Figures/tables | Claims |
|---|---|---|---|---|
| 1 | Introduction | 450 | — | C1–C3 + literature (Sokolovsky, Guidry, Hermes, Oelkers) |
| 2 | The frozen pipeline and its attestation | 350 | — | C4, C7, C8 |
| 3 | Three response assessments | 700 | Table 1 (from §3.1) | C5, C6; attrition table in text |
| 4 | Results | 1,100 | Fig 1 = F1+F2 stacked; Fig 2 = F3+F4; Fig 3 = F5+F6; Fig 4 = F7 (if v2 landed: Fig 4 = F7+F9 stacked, dropping F9 to online appendix only if the 5-figure/table cap is exceeded) | C9–C16 (+ C20–C21 if v2 landed) |
| 5 | What is and is not established | 600 | — | C17, C18 + the Part D list in prose (+ C22–C23, N29–N34 if v2 landed) |
| 6 | Summary | 200 | — | S14, C19 |
| — | Appendix (online) | — | attrition.csv, sensitivity.csv, ppv.csv, d2_control_reuse.csv as machine-readable tables (+ endpoints.csv, veto_exposure_summary.csv, leakage_audit_summary.json if v2 landed and F9/F11 were dropped to the appendix) | DESCRIPTIVE-PRESPEC / V2-HOLDOUT |

---

## Part D — Claims we are NOT allowed to make
Sources: G1 referee/stats/methods (reviews/G1), GENERALIZATION_PLAN "Banned
phrases", METRICS_SPEC vocabulary, ABSTRACT_SKELETON "cannot support", Amendment
4, the 2026-08-31 diurnal admission, poster/drafts/ABSTRACT.md avoid-list.

| # | Forbidden claim / phrase | Why | Say instead |
|---|---|---|---|
| N1 | "quantified selection-function measurement"; "the pipeline's selection function"; a universal ZTF selection function | G1 ref. 20; plan banned list | "three separate response assessments"; "class-specific detection completeness / trigger rates" |
| N2 | Pooling D1, D2, D3 into one completeness or one FPR | G1 ref. 20; spec "never pooled" | side-by-side table; qualitative synthesis only |
| N3 | "real-sky DAV completeness" from D2; "D2 validates the pipeline on real DAVs" | G1 ref. 3, 6 | "conditional injection-recovery efficiency of the search stage" |
| N4 | D2 counted as an independently / externally labeled sample; "three external validations" | G1 ref. 3; slip rule | "D3 is the only external-label validation" |
| N5 | "D3 FPR"; "false-positive rate among dSct=0"; "upper bound on FPR" | G1 ref. 9; spec | "negative-class trigger rate (a class containing other genuine variables)" |
| N6 | Unqualified "purity" | G1 stats 1 | "correct-frequency fraction among detected positives"; "frame-specific label PPV (no transfer to other prevalences)" |
| N7 | A ZTF-g amplitude threshold / detection limit from the D3 turn-on; "A_g" axis | G1 ref. 13 | "historical Kepler-band dominant amplitude, non-contemporaneous" |
| N8 | Causal cadence / crowding / exposure-gradient claims | G1 ref.; G4 stats obs. 1 | observed strata differences, conditional on frozen windows |
| N9 | "Completeness for all 610" from the 456-star frequency curve; silently swapping 610 ↔ 456 ↔ n_usable | G1 ref. 12 | state the denominator every time; "Mo-join-conditioned" |
| N10 | Calling the 3 × 3 grid min–max a "band", "uncertainty envelope", or CI; the ±30 % amplitude scale an astrophysical envelope | G1 stats 9; spec | "prespecified finite-grid sensitivity range, endpoints named"; "local sensitivity" |
| N11 | Any D2 row-level Wilson interval; pooled McNemar for D2 | spec (A4) | target-cluster bootstrap; CP discordance bound when degenerate |
| N12 | "Injection-recovery completeness" for the detection-only D2 endpoint | A4 | "post-injection rule-1 trigger rate" (SECONDARY) |
| N13 | Subtracting the native trigger rate from P4; conditioning P4 on quiet controls | A4 (G4 stats obs. 2) | report paired 2 × 2, P(R_B=1,R_C=0), quiet-control-conditioned SECONDARY beside P4 |
| N14 | A "corrected", "de-aliased", or "instrumental-only" P3 from the diurnal partition; any interval on it; applying it to census; using it to veto or reclassify | 2026-08-31 admission | the two-row arithmetic partition with the verbatim disclosure sentence |
| N15 | Presenting Amendment 4 (recovery endpoint, W_g strata) as part of the original preregistration | A4 ratification | "pilot-informed, disclosed, frozen before the first confirmatory run" |
| N16 | Quoting any pilot number (gen1 16/30, 7/30, 8/10, 10/10; gen2 pilot; D3 150-star pilot) as a result | spec pilot rule | pilot cited only as the motivation for A4 |
| N17 | "Real-sky FPR" or "operational false-alarm rate" from the Gaussian nulls | G1 ref. 7, stats 11 | "Gaussian-null false-alarm rate (FPR_Gaussian), conditional on the frozen window set" |
| N18 | Claiming the alias audit / FP frequency distribution is informative below 10 events | spec | "descriptive only (n < 10 events)" |
| N19 | Extrapolating D3 across the g ≥ 13.2 cut or beyond the Kepler field; "δ Scuti completeness of ZTF" | G1 ref. 14 | "within the magnitude-restricted Kepler A/F frame" |
| N20 | Treating dSct=0 as "constant"; treating dSct=2 as positives or negatives | plan | "non-dSct comparison class"; dSct=2 excluded, reported separately |
| N21 | "Complementarity proven by McNemar" | G1 ref. 19 | both discordant cells + union + incremental yields; McNemar = marginal homogeneity, secondary |
| N22 | The 928-catalog counts as completeness or as a labeled denominator; "342 confirmed periodics"; "327 verified errors" | spec D1; ABSTRACT.md cut list | D1 completeness only on the 13 paper-variables; catalog = rule disagreements |
| N23 | "Zero false positives" (D1 0/5); "variance screens are blind to pulsators"; "all four pulsator classes"; "independent catalog reconstruction"; "validated two-channel detector" | ABSTRACT.md avoid-list; Guidry+2021 counterexample | D1 anchor counts with finite-roster intervals |
| N24 | The cadence_alt endpoint as an estimate of the stitched solution's effective cadence; pooling cadence_alt / dropout / redilution with nominal | A3, A2 | "conservative pure-120-s endpoint sensitivity, common-subset contrast" |
| N25 | Any estimand, rule, pass, denominator, or interval method not in METRICS_SPEC; any new one invented for a nicer sentence | A4 prohibition | cut the sentence |
| N26 | "Unbiased for the 928-window frame" (D2 aggregate) | G4 stats obs. 1 | "equal-weight target mean over a fixed three-window design, conditional on the frozen windows" |
| N27 | Frequency-recovery claims for D1 | spec D1 | D1 frequency recovery = DIAGNOSTIC only |
| N28 | Mo super-Nyquist sub-hour stratum described as sub-hour signals *in the ZTF source* without the blend caveat | plan sub-hour caveat | "sub-hour signal established in the Kepler aperture" |
| N29 | Any v2 number from the DEV half (D3 `d3_dev.txt`, D2 `d2_dev.txt`/`d2_dev_deferred.txt`) presented as a result | V2_PLAN.md §5, §8 ("the holdout is scored once") | "holdout only, once"; dev numbers stay in `generalization/v2/dev_tuning.csv` as tuning evidence, never quoted as a finding |
| N30 | v2 described as "external validation", "confirmatory", "independently confirms", or any p-value / significance language on the STRONG/other reading | V2_PLAN.md §1, §6 | "internal post-selection validation"; "descriptive operational screen" |
| N31 | A "corrected" frozen P3 (or any frozen number) derived from or adjusted by the v2 arm; v2 presented as fixing the frozen result rather than as a separate arm | V2_PLAN.md §1 ("v2 is a NEW arm") | "a second, separately reported detector arm evaluated on the same stars" |
| N32 | Pooling frozen and v2 estimates into one number; a combined interval across arms | N2 (pooling), V2_PLAN.md §6 | side-by-side table with the paired difference only |
| N33 | Any v2 constant (trend window, N window peaks, phase tolerance, amplitude ratio) presented as pre-fixed rather than dev-tuned within its declared V2_PLAN.md §3 candidate set; omitting `tuning_constraint_failure` when true | V2_PLAN.md §5 | cite `V2_CONSTANTS_FROZEN.json`; if `tuning_constraint_failure=true`, say so ("no dev combination met the constraint; the default constants were retained") |
| N34 | Any v2 number quoted before `generalization/v2/HOLDOUT_LAUNCH_<dataset>.json` exists for that dataset; any v2 number from a non-canonical or unregistered run | V2_PLAN.md §8 (registered single-execution holdout) | cite the lock file's timestamp; if it does not exist, the number does not exist |
| N35 | The v2 window veto presented as fully pre-registered: its fixed loci were extended once (sidereal-month sidebands, comb rule, diurnal bands) after inspecting partial development-half results, before any holdout star (V2_PLAN.md §10, 2026-09-04); any partial-dev number from that inspection quoted as a result | V2_PLAN.md §7 (amended disclosure clause), §10 | the §7 sentence carries the clause "extended its fixed window-veto loci once after inspecting development-half results"; the dev evidence stays in §10, never in a figure or table |

---

## Part E — Contingencies
See CONTINGENCIES.md: the outline above is branch-neutral; the STRONG and UGLY
branches change the headline sentence (S14), the poster claim paragraph, and
§4 of the paper, never the estimands, the table rows, or the labels. §6 of
CONTINGENCIES.md covers the v2 branches (STRONG / partial / negative /
tuning-constraint-failure) and never changes S1–S14, Table 1 rows 1–16, or
any frozen label either — only S15/S16, poster §6, and Table 1 rows 17–23
(all conditional, all v2) are affected.
