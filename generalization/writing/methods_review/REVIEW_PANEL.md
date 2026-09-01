# Simulated Peer-Review Panel — METHODS of the generalization campaign

Mode: `academic-paper-reviewer` / `methodology-focus` (ARS 3.19.0, skill v1.10.0), panel expanded at the Phase 0 checkpoint to the five personas requested by the caller (the mode's default two-seat contract is superseded by explicit configuration; the sprint-contract machinery is not run — this is a Mode-B standalone panel).
Review date: 2026-09-01. Review round: 1 (methods-only; results pending).
Read-only: no manuscript file was modified; outputs live only in `generalization/writing/methods_review/`.

## Manuscript

"Three-dataset response assessment of a frozen ZTF variance-census + blind Lomb–Scargle pipeline" — methods-only pre-registration consisting of:

| Surface | Path (repo-relative) |
|---|---|
| Plan | `generalization/GENERALIZATION_PLAN.md` (SHA e2cd36af…, Amendment-4 state) |
| Metrics spec | `generalization/METRICS_SPEC.md` (SHA 66013732…) |
| Freeze ledger | `generalization/reviews/G2_FREEZE.md` (Amendments 2–4; 2026-08-31 descriptive diurnal admission) |
| Abstract skeleton | `generalization/ABSTRACT_SKELETON.md` (2026-08-28, pre-Amendment-4) |
| Dataset briefs | `generalization/briefs/` — **directory is empty** (no one-pagers exist; see F39) |
| D3 crossmatch freeze | `generalization/data/d3/crossmatch_freeze/README.md` + CSV/JSON |
| D2 gen2 pilot | `generalization/results/2026-08-30_d2_pilot_gen2/` — **no README** (only the gen1 pilot has one) |
| Design background | `/Users/jackneo/.claude/plans/recursive-wondering-church.md` |

Prior harvests read and NOT repeated (G1 referee/stats/methods 47 findings; G2 rounds 2–6; G2A1; G3 rounds 1–5; G4 rounds 1–3; G5prep diurnal): every finding below is either new, or a specific mechanism/number that survived those rounds.

## Constraint frame (binding on every remedy)

Amendment 4 forbids any further estimand-hierarchy change; the frozen five scripts cannot be edited; the D3 full run is executing. Every finding therefore carries exactly one class:

- **A** — must be DISCLOSED / argued in the text (abstract, poster, methods section).
- **B** — addressable by an additional DESCRIPTIVE table or figure computed from outputs that already exist or that the frozen metrics program will emit (`per_star.csv`, per-star JSONs, roster, crossmatch freeze, shard manifests, pilot records), with no estimand touched. Where a small new descriptive script is needed it must follow the `descriptive/` precedent (outside the campaign SHA surface, `prespecified=false`, no interval).
- **C** — genuine limitation to state as future work; anything requiring a pipeline re-run or a change to the frozen chain is C by definition.

## Evidence base established before the panel sat (verified from repository data, no campaign script executed)

| # | Fact | Source |
|---|---|---|
| E1 | D3 roster 3,000 = 610 / 76 / 2,314; crossmatched 2,901 (585 / 72 / 2,244); not crossmatched 25 / 4 / 70 | `crossmatch_freeze/attrition_by_class.csv` |
| E2 | Positives: g median 13.80, 66% with g < 14.0; negatives: g median 14.05, 47% < 14.0; dSct=2: 86% < 14.0 | `roster_d3.csv` |
| E3 | Teff: positives median 7,350 K (IQR 6,973–7,767); negatives median 6,675 K (IQR 6,581–6,845) | `roster_d3.csv` |
| E4 | Exactly 3 stars (all negatives) have g = 14.000; `near_saturation = gmag < 14.0` flags them SAFE; plan/spec say "g ≤ 14.0 flagged" | `build_d3_roster.py:164`, plan 144, spec 257 |
| E5 | Mo table2 `Freq` max = 283.257 µHz (= Kepler LC Nyquist 283.2); table1 carries `Freq` (alias) and `fR` (real, 99–1,410 µHz); the roster's `dom_freq` comes from table2 only | `raw/mo2026_table{1,2}.csv`, `build_d3_roster.py:133–139` |
| E6 | 40 of the 290 sub-hour positives have a table2 dominant frequency that equals a table1 super-Nyquist ALIAS row (the physical frequency is `fR`) | join of roster × table1 |
| E7 | Of 456 scorable positives, 117 have dominant frequency < 4 c/d (89 < 2.5 c/d); 49 of those are sub-hour-flagged; only 10 have ≥ 24 c/d; 0 ≥ 48 c/d; only 2 fall inside the diurnal bands | `roster_d3.csv` |
| E8 | Sub-hour positives' dominant frequency 10/50/90 pct = 22.7 / 179.7 / 259.8 µHz = 2.0 / 15.5 / 22.4 c/d — i.e. LOW pass | `roster_d3.csv` |
| E9 | Kepler LC boxcar |sinc| at the dominant period: 5th pct 0.68, 25th 0.80, median 0.89 (uncorrected amplitudes understated up to ~1.5×) | computed from `dom_freq` |
| E10 | Roster `stratum` uses sub-hour precedence: `amp_gt10` = 16 although 48 positives have A > 10 mmag | `build_d3_roster.py:96–106`, `roster_report.json` |
| E11 | Crossmatch: nearest separation median 0.08–0.10″; objects in 10″ cone median 7–8; oids merged per star: 2 (544), 3 (105), 4 (1,715), 5 (38), 6 (482), 7–8 (17); 56,404 epochs dropped by catflags, 32,658 by chi < 4 | `crossmatch_adjudication.csv` |
| E12 | D3 coverage: zg ≈ 750 epochs / 640 nights / 82 months per star; `zg_median_exp_per_night` = 1.0 for 2,354 / 2,901; W_g proxy (n_exp − n_nights) median 112–126 vs D2 pool median 58 (10/90 = 6/452) | `panels_census_generic.csv`, gen2 manifest |
| E13 | Metrics `attrition.csv` = 7 scalars; no attrition-by-covariate table, no joined-vs-unjoined table, no `assert == 456` | `metrics_generalization.py:1610–1618`, grep |
| E14 | D3 `chance_match_rate` permutes full Mo lists (any-mode, 100 permutations, not conditioned on `confirmed`) while P2 is dominant-only | `metrics_generalization.py:567–590` |
| E15 | D3 `sensitivity_table` emits near-saturation / safe / crowding-clean rows for POSITIVES' detection only; no negative-class breakdown | `metrics_generalization.py:1263–1275` |
| E16 | Published D1 catalog: 342 confirmed, 277 (81%) in the LOW pass; low-pass confirmed frequency median 2.56 c/d (10th pct 0.41); 174/342 below 4 c/d; 18/342 inside the diurnal bands; 19-star master: 12 confirmed, none in the bands | `catalog-rebuild/results/2026-08-01_full/catalog/ls_full_catalog.csv`, `master_table.csv` |
| E17 | D2: 103 targets, g 13.53–17.48 (median 16.46); 341 modes (median 3/star, max 19); dominant amplitude 10/50/90 = 3.2 / 10.2 / 28.3 ppt; 2.9% of modes P < 240 s | `d2_targets.csv`, `d2_modes.csv` |
| E18 | gen2: 3,089 shards; nominal-B 309 assignments on 106 unique windows (reuse: 36 windows ×1 … one window ×12; top two windows = 22 assignments); 52% of assignments (161/309) sit on published-variable windows | `shard_manifest_gen2.csv` |
| E19 | W_g by K: K0 mean 7.6 (0–23), K1 62.8 (8–127), K2 433 (100–786); template status by K — K0: 76 not_detected / 26 confirmed / 1 candidate; K1: 55 / 41 / 7; K2: 17 / 62 / 24 (K2 = 84% published variables) | `shard_manifest_gen2.csv` |
| E20 | Arm A = N(0, magerr_i) around the band median on real timestamps; nulls cycle all 928 windows (510 nd / 342 conf / 76 cand unique) | `build_d2_shards.py:227–246` |
| E21 | gen2 pilot (10 targets, 30 nominal-B windows): recovery 5/30, trigger 17/30; arm A recovery 8/30, trigger 10/30; HIGH-pass recovery 7/30 but BEST-pass recovery 5/30 (best-pass rule demotes two correct high-pass recoveries); correct-frequency fraction 7/8 (high) vs 5/17 (best); nulls 0/30; controls 6/10 confirmed | `results/2026-08-30_d2_pilot_gen2/metrics/*` |
| E22 | D3 timing pilot was `--limit 150` = lexicographic = the 150 lowest KIC numbers (a sky corner); the diurnal band half-width 0.020 c/d was fixed after seeing 0.994–1.006 and 2.000–2.015 c/d in it | `RUNBOOK.md:44–51`, `G5prep/PROMPT_diurnal.md` |

---

# Phase 0 — Field analysis and reviewer configuration

**Field**: time-domain optical astronomy (survey variability detection); paradigm: quantitative, pre-registered measurement study with injection–recovery and external-label validation; maturity: methods frozen, results pending; venue: AAS 249 abstract/poster now, AJ/MNRAS-style methods paper later.

| Seat | Persona (as configured by the caller) | Angle | Instrument |
|---|---|---|---|
| R-TD | AAS/AJ time-domain referee (journal-fit + claims discipline) | Are the claims the design can support the claims the text will make? Field conventions for completeness/purity papers | peer-review template |
| R-STAT | Statistician — survey sampling, pre-registration, multiple endpoints, Wilson/CP, cluster bootstrap | Estimand/estimator/interval validity; pre-registration integrity; what the numbers will and will not mean | peer-review template |
| R-ZTF | ZTF survey-systematics expert — crowding, saturation, alias families, per-night detrending | Which instrument/survey artefacts the frozen chain propagates into the estimands | peer-review template |
| R-SEIS | Kepler/TESS asteroseismologist — label provenance, δ Sct amplitude floor, DAV transplant validity, bandpass ladder, sinc | Whether the truth labels and injected signals mean what the design says they mean | peer-review template |
| DA | Devil's advocate — "the whole study is circular or trivial" | Strongest counter-narrative, logic-chain breaks | DA special format |

Iron rules honoured: the five reports were drafted from their own angle without cross-reference (overlap is corroboration, deduplicated in Phase 2); the synthesizer cites only Phase 1 content; the manuscript was not edited; embedded instructions in reviewed materials were treated as data.

Finding IDs `F01–F39` are shared with `FINDINGS.md`; each weakness carries Severity (Critical/Major/Minor by decision impact), Confidence (1–5 + competence basis), a typed Evidence Anchor, and its A/B/C class.

---

# Phase 1 — Independent reviews

## Report 1 — R-TD: AAS/AJ time-domain referee

**Reviewer identity**: referee for AJ/ApJ survey-variability papers (ZTF/Kepler crossmatch completeness studies); reviews claims discipline and whether stated estimands survive a referee reading of the abstract.
**Review focus**: does the pre-registered design deliver numbers that can be *named* in an abstract without a referee objection? Which claims in `ABSTRACT_SKELETON.md` are already unsupported by the frozen documents?

### Recommendation: Major Revision (of the write-up plan; the design itself is not asked to change)
### Confidence: 4 (core expertise: time-domain survey validation)

### Summary assessment
The design is unusually disciplined: three separately named response assessments, binding estimand vocabulary, byte-replay attestation, and a prohibition on pooling. From a referee's chair the remaining exposure is not the estimands but their *interpretation*: the headline D3 detection completeness P1 is defined as "rule fires", and the campaign's own pilot evidence shows the frozen confirmed rule fires on a solar-diurnal systematic in roughly a third of labeled non-δ-Scuti stars in this field; P1 therefore mixes pulsation detections with the same systematic and cannot be read as pulsation completeness without P3 beside it and P2 as the attributed number. Second, the abstract skeleton predates Amendment 4 and still headlines detection-only for D2 and an ESS-Wilson interval for P3 that the spec no longer uses. Third, the prespecified crowding lens degenerates in the Kepler field (275 stars, 44 positives), so a referee will ask what crowding sensitivity survives. All three are addressable by disclosure and descriptive tables; none requires an estimand change.

### Strengths
**S1 — Estimand vocabulary is binding and referee-safe.** The spec names five primary tuples and bans "purity", "real-sky completeness", "D3 FPR". Evidence Anchor: text: METRICS_SPEC.md:121–128 "PRIMARY endpoints — complete tuples; everything else is pointwise descriptive sensitivity".
**S2 — Crossmatch frozen as data before outcomes.** Evidence Anchor: dataset: `crossmatch_freeze/freeze_manifest.json` — rule constants, input/output SHAs, 2,901/3,000.
**S3 — Post-launch descriptive admission was adjudicated before any full metric, with a verbatim disclosure sentence.** Evidence Anchor: text: G2_FREEZE.md:239–241 "Adjudicated BEFORE any full-campaign D3 metric was computed".

### Weaknesses

**W1 = F01 — P1 headline counts wrong-reason triggers on positives.**
Problem: P1 = P(rule 1 fires | dSct=1) counts a confirmed 1.00 c/d best candidate on a δ Sct star exactly as it counts the pulsation. The negatives' pilot pile-up (30/33 confirmed passes at ~1.00/2.00 c/d) implies the same trigger family operates on positives; P1 ≈ attributed completeness + a systematic floor of order P3.
Evidence Anchor: text: METRICS_SPEC.md:127–128 "P1 D3 detection completeness: {D3, dSct=1 (610), eligible_roster, rule 1, best pass, unweighted, Wilson 95%}".
Why it matters: the abstract skeleton leads with P1 ("primary confirmed detection completeness is [x/610…]"); a referee will subtract P3 and ask what is left.
Suggestion: present P1, P3 and P2 as one triplet; state in the text that P1 includes triggers of the same family as P3; add a descriptive partition of confirmed positives by `best_candidate_matches_dominant` class (direct / harmonic / window_alias / ambiguous / unmatched) × `any_top_peak_matches_any_mode` from `per_star.csv` — "pulsation present in the top-15 but outranked" becomes visible without touching P1.
Severity: Major | Confidence: 5 — core expertise | Class: A + B.

**W2 = F10 — Abstract skeleton is stale relative to Amendment 4.**
Problem: claim 8 and the D2 paragraph headline the "post-injection confirmed-rule probability" as the D2 number and list strict recovery second; Amendment 4 made recovery primary and trigger secondary. Claim 5 quotes an "approximate ESS-Wilson CI" for P3 while the spec binds plain Wilson on 2,314 (weights cancel).
Evidence Anchor: text: ABSTRACT_SKELETON.md:25 "the nominal arm-B post-injection confirmed-rule probability is [p%; target-cluster-bootstrap CI L–U]".
Why it matters: G6 fills placeholders from this skeleton; an un-updated skeleton reproduces the pre-Amendment-4 hierarchy in the submitted abstract.
Suggestion: re-issue the skeleton with recovery first, trigger labelled "post-injection rule-1 trigger rate", P3 with plain Wilson, and the D2 census/L-S sentence without an interval.
Severity: Major | Confidence: 5 | Class: A.

**W3 = F19 — The prespecified crowding lens is degenerate in the Kepler field.**
Problem: `ambiguous` is true for 2,901/2,901 crossmatched stars; the crowding-clean subset is 275 (44 positives). The plan calls near-saturation "the PRINCIPAL robustness lens" but the crowding lens has no comparison group of its own.
Evidence Anchor: text: crossmatch_freeze/README.md:6–8 "makes `ambiguous` true for ~100% of crossmatched stars (2,244/2,244 flag0, 585/585 flag1, 72/72 flag2)".
Why it matters: a referee will ask for crowding sensitivity and find a 44-positive cell.
Suggestion: disclose the degeneracy; add descriptive rows by continuous covariates already in `crossmatch_qc.csv` (nearest separation quartiles; objects-in-cone quartiles; merged-oid count) for both classes.
Severity: Major | Confidence: 4 | Class: A + B.

**W4 = F20 — The closing sentence claims non-overlap the design cannot assert for D2.**
Problem: "census and period-search responses remain empirically non-overlapping" — D2 census/L-S tables are descriptive with no intervals (Amendment 4), and the D3 L-S-only cell will contain systematic-only triggers.
Evidence Anchor: text: ABSTRACT_SKELETON.md:49 "these measurements show that census and period-search responses remain empirically non-overlapping".
Suggestion: restrict the sentence to D1/D3 with intervals and qualify the D3 L-S-only cell by match class.
Severity: Major | Confidence: 4 | Class: A.

**W5 = F25 — Roster stratum labels use sub-hour precedence and will be misread.**
Problem: `stratum` assigns `subhour` before amplitude, so `amp_gt10` = 16 while 48 positives have A > 10 mmag; the "1–10 mmag log ladder" strata (8–22 stars each) are the non-sub-hour remainder.
Evidence Anchor: dataset: `roster_report.json` — `strata.amp_gt10 = 16` vs `positives_amplitude_mmag.gt10 = 48`.
Suggestion: state that surfaces bin on amplitude directly and that `stratum` is a precedence label; never quote `stratum` counts as amplitude-bin counts.
Severity: Minor | Confidence: 5 | Class: A.

**W6 = F31 — Magnitude systems in D2 template matching are not stated.**
Problem: DAV `gmag` (from the TIC/Gaia, 13.5–17.5) is matched to the WD pool's ZTF median zg; the offset between systems for blue WDs is small but unstated.
Evidence Anchor: text: GENERALIZATION_PLAN.md:192 "matched by median zg mag (|Δg| ≤ 0.25, widened when thin; flagged)".
Suggestion: name both magnitude systems and note all 309 matches were within 0.25.
Severity: Minor | Confidence: 3 — adjacent | Class: A.

**W7 = F32 — D1 context is under-described for the complementarity claim.**
Problem: in the published 928-star catalog 277/342 confirmations are low-pass with median 2.6 c/d — for white dwarfs these are not the pulsation regime; D1's "census vs L-S" complementarity is largely a low-frequency story, which the write-up does not say. Only 18/342 lie in the diurnal bands, so the D1 confirmations are not the D3 systematic.
Evidence Anchor: dataset: `catalog-rebuild/results/2026-08-01_full/catalog/ls_full_catalog.csv` — best_pass low = 277 of 342 confirmed.
Suggestion: one sentence in the D1 paragraph; a descriptive best-frequency histogram of D1 confirmations beside the D3 negative-class triggers (B).
Severity: Minor | Confidence: 4 | Class: A + B.

**W8 = F39 — The dataset briefs do not exist.**
Problem: `generalization/briefs/` is empty; the plan's dataset one-pagers were listed as review inputs and as the vH talking material.
Evidence Anchor: absence: generalization/briefs/ — expected D2 and D3 one-pagers; checked the directory listing, RUNBOOK.md, GENERALIZATION_PLAN.md.
Suggestion: write the two one-pagers from the plan's D2/D3 sections before the poster; they are the natural home for the A-class disclosures collected here.
Severity: Minor | Confidence: 5 | Class: A.

### Questions for authors
1. Will the abstract quote P1 alone, or the P1/P3/P2 triplet? (W1)
2. Which sentence will replace "empirically non-overlapping" for D2? (W4)
3. What is the sub-hour stratum's *estimand* once E8 is acknowledged (its dominant modes are low-pass)?

### Dimension scores (methods-only manuscript)
| Dimension | Score | Descriptor |
|---|---|---|
| Originality | 74 | Strong (pre-registered frozen-pipeline replay is rare in the subfield) |
| Methodological Rigor | 82 | Strong |
| Evidence Sufficiency | not assessed | results pending |
| Argument Coherence | 66 | Adequate (skeleton/spec drift) |
| Writing Quality | 58 | Adequate (ledger prose; no briefs) |

---

## Report 2 — R-STAT: Statistician

**Reviewer identity**: applied statistician (survey sampling, pre-registration audits, binomial/cluster inference).
**Review focus**: are the estimators what the estimands say; is the pre-registration record internally consistent; what does the sole confirmatory decision decide; which mandatory outputs are actually produced.

### Recommendation: Major Revision
### Confidence: 5 (core expertise)

### Summary assessment
The spec is precise where it matters (target-cluster bootstrap with common random numbers, exact CP at observed x, FPC-rescaled survey bootstrap, degenerate-contrast fallback). Four things a statistician will still raise. (1) The freeze rule and the ledger disagree on what "first campaign L-S run" means; two changes post-date L-S runs and one post-dates the full D3 launch — all disclosed, but the contradiction in the spec's own sentence is not. (2) The sole confirmatory decision P5 has a non-trivial a-priori failure probability under the confirmed rule's four-way multiplicity, and no pre-registered consequence of failure. (3) Two mandatory outputs (the seven-dimension attrition table and the joined-vs-unjoined covariate table) are not emitted by the metrics program; G5 will notice. (4) Several descriptive calibrations are misaligned with their endpoints (D3 chance-match is any-mode, not dominant; the D2 best-pass rule demotes correct high-pass recoveries, as the pilot already shows). All are A or B.

### Strengths
**S1 — P4 estimator fully written out with both denominators and a matching bootstrap.** Evidence Anchor: equation: METRICS_SPEC.md:133–151 — p-hat = (1/103) Σ_t (1/|K_t|) Σ_k y_{t,k}, eligible vs usable variants.
**S2 — Degenerate-contrast fallback is correct (CP discordance bound instead of [0,0]).** Evidence Anchor: table: `d2_scenario_contrasts.csv` — `interval = cp_discordance_bound`, ±0.6316 at n = 3.
**S3 — Row-level D2 intervals are suppressed everywhere; inference lives at the cluster.** Evidence Anchor: table: `completeness_by_class_pass_rule.csv` (gen2 pilot) — `lo`/`hi` empty, `inference = descriptive (window rows)`.

### Weaknesses

**W1 = F05 — The freeze sentence contradicts the ledger's operative definition.**
Problem: the spec voids the prespecification on "any change after the first campaign L-S run"; the gen1 pilot (an L-S run) preceded Amendment 4, and the diurnal admission post-dates the full D3 launch. The ledger re-defines the trigger as the first *confirmatory* run. Both are disclosed, but the spec sentence itself is not amended (it cannot be — SHA frozen), so the two texts will be read side by side.
Evidence Anchor: text: METRICS_SPEC.md:4–6 "Any change after the first campaign L-S run voids the prespecification and must be reported as such".
Why it matters: pre-registration credibility is the paper's methodological contribution; an unexplained contradiction invites "the goalposts moved".
Suggestion: a dated exposure table in the text: for each amendment (1–4 + diurnal), date, trigger, what data had been seen (none / gen1 pilot 144 shards / D3 150-star raw statuses), and what changed; state explicitly that the spec sentence is read with "confirmatory" per the ledger and why.
Severity: Major | Confidence: 5 | Class: A + B.

**W2 = F06 — P5 can fail for reasons that are not a pipeline defect, and failure has no pre-registered consequence.**
Problem: rule 1 gives a Gaussian null four independent chances (2 bands × 2 passes) for a top blind peak with Baluev FAP < 1e-3 to be joined by a multiband top-5 coincidence; if the Baluev bound were tight the expected count at n = 1,000 would be of order 2–4, and acceptance requires x ≤ 1 (U95(2) = 0.0063). Baluev is conservative for uneven sampling, so the true expectation is probably below 1 — but the pilot's 0/30 is uninformative and the design never states what x ≥ 2 means for the abstract. Separately, P5 is a calibration of a FAP bound; it "confirms" no scientific hypothesis of the study.
Evidence Anchor: text: METRICS_SPEC.md:152–153 "P5 FPR_Gaussian acceptance: {D2 arm A nulls, rule 1, exact one-sided CP upper at observed x <= 0.5%} — the sole confirmatory decision".
Why it matters: a failed P5 with no plan reads as an unplanned negative result; a passed P5 will be over-read as "the pipeline is confirmed".
Suggestion: state the a-priori expectation and its derivation; state that P5 pass/fail changes only the sentence about the Gaussian false-alarm rate and gates nothing else; report x, U95 and the per-pass/per-band route of every null trigger.
Severity: Major | Confidence: 4 | Class: A.

**W3 = F07 — Two mandatory spec outputs are not produced.**
Problem: the spec requires an attrition table by class × amplitude stratum × Mo-join × magnitude × period × Teff × crowding and a joined-vs-unjoined covariate table (MNAR statement); `attrition.csv` contains seven scalars and no join table exists; the spec's "assert count == 456" is not implemented.
Evidence Anchor: absence: metrics_generalization.py:1610–1618 — expected the spec §"Eligibility and attrition" multi-dimensional table and the joined-vs-unjoined table; checked `attrition`, `sensitivity_table`, `truth_d3`, the outputs list.
Why it matters: these are the paper's answer to the MNAR objection (G1 referee 11); G5 re-derives every headline and will find the table missing.
Suggestion: compute both descriptively from `per_star.csv` + `roster_d3.csv` + `crossmatch_adjudication.csv` (all frozen inputs); no estimand is involved.
Severity: Major | Confidence: 5 | Class: B.

**W4 = F09 — The best-pass rule demotes correct high-pass recoveries; P4 is strictly ≤ the high-pass recovery row.**
Problem: `overall_result` picks the pass with the best (status, FAP); a native low-frequency confirmation with a smaller FAP becomes the "best" candidate even when the high pass recovered the injected mode. The gen2 pilot shows it: high-pass recovery 7/30, best-pass recovery 5/30; correct-frequency fraction 7/8 in the high pass vs 5/17 at best pass.
Evidence Anchor: table: `completeness_by_class_pass_rule.csv` (gen2 pilot) — high/confirmed/freq_recovery_scorable p = 0.2333 vs best/confirmed/freq_recovery_scorable p = 0.1667.
Why it matters: P4 is frozen on best pass; readers will otherwise attribute the shortfall to the search stage rather than to the frozen pass-selection rule.
Suggestion: report the per-pass recovery rows beside P4 (they already exist) and say in words that P4 is a best-pass estimand.
Severity: Major | Confidence: 5 | Class: A + B.

**W5 = F21 — D3 chance-match calibration is misaligned with P2.**
Problem: `chance_match_rate` permutes the full Mo frequency lists (mean ~141 modes/star), scores any-mode direct matches, uses 100 permutations, and does not condition on `confirmed`; P2 is dominant-only. The reported accidental rate is therefore an any-mode upper bound placed beside a dominant-only headline.
Evidence Anchor: text: metrics_generalization.py:582–583 "classify_match(float(row[\"best_frequency_per_day\"]), truth_lists[perm[i]], tol) == \"direct\"".
Suggestion: label it "any-mode accidental rate (conservative)"; add a dominant-only, confirmed-conditioned rate with 10,000 derangements computed from `per_star.csv` as a descriptive companion.
Severity: Minor | Confidence: 5 | Class: A + B.

**W6 = F22 — The g = 14.0 boundary convention differs between code and documents.**
Problem: plan/spec put the boundary in the flagged stratum ("g ≤ 14.0 flagged"); the roster uses `gmag < 14.0`; three negatives at g = 14.000 are flagged safe. No emitted row changes (the sensitivity rows use positives only), but the attrition-by-magnitude table will.
Evidence Anchor: text: build_d3_roster.py:164 "roster[\"near_saturation\"] = roster[\"gmag\"] < 14.0".
Suggestion: disclose the implemented convention and the three affected negatives.
Severity: Minor | Confidence: 5 | Class: A.

**W7 = F26 — "Usable light curve" is operationalised as "both passes available".**
Problem: a star whose high pass is unavailable (no within-night variation) is dropped from the usable denominator even though its low pass — where every δ Sct dominant mode below 24 c/d lives — is fully usable.
Evidence Anchor: text: METRICS_SPEC.md:19–21 "`usable_lightcurve` (frozen QC passed, both passes complete)".
Suggestion: state the definition and report how many stars are usable-low-only.
Severity: Minor | Confidence: 4 | Class: A (+ B count).

**W8 = F27 — Wilson intervals assume star-level independence inside one field with a field-coherent systematic.**
Problem: P1 and P3 treat 610 / 2,314 stars as independent Bernoulli trials; a solar-diurnal systematic is common-mode across the field, so the effective replication for the systematic component is the number of field/season/CCD conditions, not stars.
Evidence Anchor: text: METRICS_SPEC.md:168–169 "D1/D3: the star is the unit. Wilson 95% on unweighted proportions".
Suggestion: state the assumption; add a descriptive P3 by sky cell (RA/Dec quartiles from the roster) to show whether triggers cluster spatially.
Severity: Minor | Confidence: 4 | Class: A + B.

**W9 = F28 — Amendment 1 (decision-equivalent replay tier) has no ratification entry.**
Problem: `CROSS_PLATFORM_REPLAY.md` proposes the tier and records a REJECT/A-w-C round; the ledger mentions only an erratum found by that review; the metrics code implements the tier. All campaign L-S runs are strict-tier on the laptop, so the tier is unused — but the record does not say so.
Evidence Anchor: text: CROSS_PLATFORM_REPLAY.md:58 "Implication and proposed amendment (G2-AMENDMENT-1, not yet reviewed)".
Suggestion: one ledger-style sentence in the text: Amendment 1 was not ratified and no campaign L-S output was produced under it.
Severity: Minor | Confidence: 4 | Class: A.

**W10 = F36 — Roughly twelve intervals will appear in a 250-word abstract with one confirmatory decision.**
Problem: pointwise intervals across P1–P4, strata, and 2×2 cells with no simultaneity; the spec designates one confirmatory decision but the abstract does not say the rest are pointwise.
Evidence Anchor: text: ABSTRACT_SKELETON.md:45 "Completeness is stratified by historical Kepler amplitude and magnitude, with pointwise Wilson intervals".
Suggestion: keep "pointwise" in the abstract and say once that P5 is the only decision rule.
Severity: Minor | Confidence: 5 | Class: A.

**W11 = F34 — The D2 turn-on figure is silently skipped.**
Problem: `plot_turn_on` reads `freq_recovery_period_amplitude.csv`; D2 writes `recovery_period_amplitude.csv`, so the function returns early for D2.
Evidence Anchor: text: plot_generalization.py:69–71 "path = metrics_dir / \"surfaces\" / \"freq_recovery_period_amplitude.csv\" … if not path.exists(): return".
Suggestion: draw the D2 recovery surface from the existing CSV (descriptive script outside the campaign SHA surface).
Severity: Minor | Confidence: 5 | Class: B.

### Questions for authors
1. What sentence will the abstract carry if x ≥ 2 nulls trigger? (W2)
2. Will the attrition and joined/unjoined tables be added before G5, and by which script? (W3)
3. Is "first campaign L-S run" in the spec to be read as "first confirmatory run" everywhere in the paper? (W1)

### Dimension scores
| Dimension | Score | Descriptor |
|---|---|---|
| Originality | 70 | Strong |
| Methodological Rigor | 78 | Strong (estimators) / Adequate (record consistency) |
| Evidence Sufficiency | not assessed | results pending |
| Argument Coherence | 64 | Adequate |
| Writing Quality | 60 | Adequate |

---

## Report 3 — R-ZTF: ZTF survey-systematics expert

**Reviewer identity**: ZTF DR photometry/systematics practitioner (calibration, crowding, saturation, cadence and alias structure).
**Review focus**: which survey artefacts the frozen QC/search chain passes into P1–P3, and whether the D3 field is representative of the ZTF sky.

### Recommendation: Major Revision
### Confidence: 4 (core expertise: ZTF systematics; adjacent: Kepler field specifics)

### Summary assessment
The frozen chain is faithful ZTF practice (catflags = 0, chi < 4, 1.5″ oid clustering, BJD_TDB at Palomar) and the D3 field is deep (≈750 zg epochs, 640 nights per star). Four systematics will shape the D3 numbers and none is yet described in the text: (1) the confirmed rule's two-band requirement does not protect against a common-mode solar-diurnal modulation, and the frozen veto covers only the sidereal family — the pilot pile-up at 1.000 c/d sits five match tolerances from 1.0027 c/d and survives; (2) 2,200 of 2,901 stars have 4–6 ZTF oids merged into one series with no inter-oid zero-point alignment, which injects step/seasonal power into the un-detrended low pass and into the census exposure ratio; (3) the two classes differ in magnitude and Teff, so class comparisons are also brightness comparisons; (4) the Kepler field is far better sampled than the D2/D1 pool, so D3 responses are field-specific. Each is a disclosure plus a descriptive table from data already frozen.

### Strengths
**S1 — Per-epoch saturation is handled by the frozen catflags QC and its effect is counted.** Evidence Anchor: dataset: `crossmatch_adjudication.csv` — `drop_catflags` = 56,404 epochs, `drop_chi` = 32,658.
**S2 — The diurnal admission is honest about what it is.** Evidence Anchor: text: G2_FREEZE.md:247–250 "the outside-band component is never called a \"corrected\" or \"de-aliased\" P3".

### Weaknesses

**W1 = F14 — A common-mode solar-diurnal systematic defeats the two-band rule; the frozen veto is sidereal-only.**
Problem: rule 1 needs two unaliased bands (or one band + multiband top-5); an airmass/extinction-driven modulation is shared by zg and zr and is coherent over 640 nights, so its FAP is tiny in both. `is_window_alias` vetoes only |f − k·1.00274| ≤ 1.5/T (5.6e-4 c/d) and window power ≥ 0.1; a candidate at 1.0000 c/d is 2.7e-3 c/d away — not vetoed — and the pile-up shows the spectral window at 1.000 c/d was below 0.1, i.e. the modulation is in the photometry, not the sampling.
Evidence Anchor: text: lomb_scargle_common.py:195–197 "near_sidereal = abs(frequency / SIDEREAL_FREQUENCY - round(frequency / SIDEREAL_FREQUENCY)) * SIDEREAL_FREQUENCY".
Why it matters: this is the mechanism behind the P3 floor and F01; without it the reader cannot judge whether P3 transfers to other fields (E16 says it does not: the D1 catalog has 18/342 in-band).
Suggestion: state the mechanism and the veto's family coverage in the text; state that a solar-family veto would require a pipeline change (future work); show P3 by Teff/colour quartile descriptively (an extinction-colour mechanism predicts a Teff gradient).
Severity: Major | Confidence: 4 | Class: A + C (+ B for the Teff table).

**W2 = F17 — Multi-oid merging without zero-point alignment.**
Problem: 1,715 stars merge 4 oids and 482 merge 6 (different fields/CCD-quadrants overlapping in the Kepler field); `select_nearest_source` concatenates them and `census_row` / the low pass see the inter-oid offsets as real variability.
Evidence Anchor: text: build_catalog_panels.py:127–133 "selected_oids = set(objects.loc[objects[\"nearest_object_separation_arcsec\"] <= OID_CLUSTER_ARCSEC, \"oid\"])".
Why it matters: predicts census and low-pass triggers rising with `selected_ztf_objects`, on both classes.
Suggestion: descriptive P1/P3 and census trigger rate by merged-oid count (2 / 3–4 / ≥5) from `per_star.csv` + `crossmatch_qc.csv`; state the mechanism.
Severity: Major | Confidence: 3 — mechanism inferred, not yet measured | Class: A + B.

**W3 = F15 — Class covariate imbalance.**
Problem: positives are brighter (66% vs 47% with g < 14) and hotter (7,350 vs 6,675 K) than negatives; P3, PPV and the complementarity 2×2 compare classes that also differ in saturation proximity and colour.
Evidence Anchor: dataset: `roster_d3.csv` — `near_saturation` mean 0.661 (dSct=1) vs 0.471 (dSct=0); Teff medians 7,350 vs 6,675 K.
Suggestion: covariate table by class; P3 and census trigger rate by magnitude stratum (g < 14 / ≥ 14) and Teff quartile, descriptive.
Severity: Major | Confidence: 5 | Class: B.

**W4 = F16 — The D3 field is atypically well sampled; responses are field-specific.**
Problem: zg ≈ 750 epochs / 640 nights / 82 months per star; within-night support (n_exp − n_nights) median 112–126 vs 58 for the D2/D1 pool. The turn-on curve and P3 are for a field observed twice as often as the pool median.
Evidence Anchor: dataset: `panels_census_generic.csv` — zg_n_exp median 745–759, zg_n_nights 635–644 by class.
Suggestion: a coverage comparison table (D3 vs the 928-window pool: epochs, nights, W_g quantiles); a sentence that no ZTF-wide transfer is claimed.
Severity: Major | Confidence: 5 | Class: A + B.

**W5 = F18 — The sub-hour regime is the high pass, where nightly-median detrending keeps ~16% of the epochs.**
Problem: 81% of stars have median 1 zg exposure per night; only multi-exposure nights survive `prepare_series(high_frequency=True)`; the high-pass a95 will be several times the low-pass a95, so the sub-hour stratum's turn-on will be mostly counts.
Evidence Anchor: text: lomb_scargle_common.py:63–65 "nightly = ordered.groupby(\"night_mjd\")[\"mag\"].transform(\"median\") … mag = mag - nightly".
Suggestion: report per-pass a95 distributions by class from the per-star JSONs (`zg_a95_mmag`, `zr_a95_mmag`); state that the high-pass floor, not the label set, limits the sub-hour result.
Severity: Major | Confidence: 5 | Class: A + B.

**W6 = F33 — The yearly alias is outside the match taxonomy.**
Problem: window_alias uses ±k·f_sid (k = 1, 2); a ±1/365.25 c/d alias (2.7e-3 c/d) is five tolerances away and lands in `unmatched`.
Evidence Anchor: text: METRICS_SPEC.md:108 "window_alias |f_cand - |f_t +/- k f_sid|| <= tol, k = 1, 2".
Suggestion: a descriptive extra relation (yearly, and 2f_Nyq,Kepler − f) evaluated from `per_star.csv` best frequency vs the roster's dominant frequency; P2 untouched.
Severity: Minor | Confidence: 4 | Class: B.

**W7 = F37 — The high-pass negative-class trigger rate is the interpretable sub-hour false-trigger proxy and is not separately shown.**
Problem: Murphy's dSct = 0 excludes p-mode pulsators above the Kepler threshold (tens of µmag), so a mmag-level confirmed high-pass signal on a negative is spurious or a blend; the low pass has no such guarantee. `trigger_rates.csv` reports P3 at best pass only.
Evidence Anchor: text: METRICS_SPEC.md:66–68 "negative-class trigger rate (D3) — P(rule fires | dSct=0, the NON-dSct COMPARISON CLASS".
Suggestion: descriptive P3 by pass (`low_status`, `high_status` of negatives) with the argument above; never called FPR.
Severity: Minor | Confidence: 4 | Class: B.

**W8 = F29 — The D3 timing pilot is a sky corner.**
Problem: `--limit 150` is lexicographic on campaign id = lowest KIC numbers, which are contiguous in declination; the diurnal band width was fixed from that peek.
Evidence Anchor: text: RUNBOOK.md:50–51 "(`--limit` = lexicographic debug subset, marked pilot; D3 has one arm so it is adequate for timing; never confirmatory)".
Suggestion: disclose the sky footprint of the 150 pilot stars beside the admission sentence.
Severity: Minor | Confidence: 4 | Class: A.

### Questions for authors
1. Does the P3 pile-up correlate with `selected_ztf_objects` or with Teff? (W2, W1)
2. What are the per-pass a95 distributions for g < 14 vs g ≥ 14? (W5)

### Dimension scores
| Dimension | Score | Descriptor |
|---|---|---|
| Originality | 68 | Adequate |
| Methodological Rigor | 74 | Strong (chain fidelity) / Adequate (systematics disclosure) |
| Evidence Sufficiency | not assessed | |
| Argument Coherence | 62 | Adequate |
| Writing Quality | 60 | Adequate |

---

## Report 4 — R-SEIS: Kepler/TESS asteroseismologist

**Reviewer identity**: δ Scuti / DAV asteroseismologist (Kepler super-Nyquist work, TESS DAV mode tables).
**Review focus**: do the labels and injected signals mean what the design says — δ Sct dominant modes, sub-hour stratum, DAV coherence, amplitude provenance, bandpass and integration corrections.

### Recommendation: Major Revision
### Confidence: 5 (core expertise)

### Summary assessment
The D2 transplant is carefully built (signed sinc, PDCSAP dilution handled correctly after G3, per-mode phases, retained-mode dominance) and the D3 truth chain is sourced cleanly. The label provenance nonetheless carries three defects the text does not yet acknowledge and that a seismologist will spot immediately: the roster's dominant frequencies come from Mo table2, whose values are Kepler sub-Nyquist (aliased) frequencies — 40 of the 290 sub-hour positives have a "dominant" frequency that is an alias of a real super-Nyquist mode, and the truth lists never contain the physical `fR`; a quarter of scorable positives have a dominant mode below 4 c/d (g-mode/rotation), so P2 partly scores γ Dor/rotational recovery; and the sub-hour stratum's dominant modes are themselves low-pass (2–22 c/d), so the ZTF high-pass regime that motivated the stratum is untested. On D2, a fixed-amplitude strictly coherent sinusoid over 2,000–2,700 d is an upper bound on any real DAV, and the TESS-discovered sample is amplitude-biased. All are A/B/C; none needs an estimand change.

### Strengths
**S1 — Sinc de-integration is correct and signed, with retention defined over post-sinc modes.** Evidence Anchor: text: d2_truth_model.py:300 "intrinsic_frac = frac / tess_sinc  # signed: negative sinc = pi phase flip".
**S2 — PDCSAP-already-corrected handled correctly after G3; re-dilution is multiplication.** Evidence Anchor: text: d2_truth_model.py:299 "frac *= crowdsap  # SAP-equivalent re-dilution (never division)".
**S3 — Phase protocol is variant-stable.** Evidence Anchor: text: d2_truth_model.py:274–276 "seed = int(tic) if phase_draw == 0 else int(tic) * 10 + phase_draw".

### Weaknesses

**W1 = F02 — Mo table2 frequencies are Kepler sub-Nyquist aliases; the truth lists never contain the physical super-Nyquist frequency.**
Problem: table2 `Freq` never exceeds 283.26 µHz (the LC Nyquist); table1 lists each confirmed super-Nyquist mode twice — `Freq` (alias) and `fR` (real, 99–1,410 µHz). The roster takes `dom_freq` and the any-mode truth list from table2 only. For 40 of the 290 sub-hour positives the dominant table2 row IS a table1 alias row; ZTF (30-s exposures, no LC Nyquist) will find `fR`, which is neither `direct` nor `window_alias` under the frozen taxonomy.
Evidence Anchor: dataset: `raw/mo2026_table1.csv` — columns `Freq, Amp, fR, C, SC`; e.g. KIC 3757814 Freq 249.04 µHz / fR 317.38 µHz, Amp 12.6 ppt; joined to roster `dom_freq_uhz` = 249.04.
Why it matters: P2 and the any-mode column are biased low for exactly the stratum whose physics is advertised (sub-hour), and the "sub-hour stratum" label set is scored against non-physical frequencies for 14% of its members.
Suggestion: disclose; add a descriptive rescoring column "best candidate matches `fR` (table1)" and "matches 2f_Nyq − f_dom" from `per_star.csv` + table1 — reported beside P2, never replacing it.
Severity: Major | Confidence: 5 | Class: A + B.

**W2 = F03 — The "sub-hour stratum" is not a high-pass stratum.**
Problem: membership = "any confirmed SNF"; the star's dominant (scored) mode has 10/50/90 pct 2.0 / 15.5 / 22.4 c/d — the low pass; only 10 of 456 positives have a dominant frequency ≥ 24 c/d.
Evidence Anchor: text: GENERALIZATION_PLAN.md:114–116 "any confirmed SNF ⇒ real mode above Kepler LC Nyquist 283.2 µHz ⇒ P < 59 min".
Why it matters: the plan's "sub-hour stratum" reads as a test of ZTF's sub-hour sensitivity; as scored it is a test of low-pass recovery on stars that also have a sub-hour mode.
Suggestion: rename in the text ("stars with a confirmed super-Nyquist mode"); split P2 descriptively by dominant-frequency regime (< 4, 4–24, ≥ 24 c/d).
Severity: Major | Confidence: 5 | Class: A + B.

**W3 = F04 — A quarter of scorable positives have a g-mode/rotational "dominant" frequency.**
Problem: 117/456 dominant frequencies are < 4 c/d (89 < 2.5 c/d): hybrids and rotational signals in Murphy's A/F sample; for them "δ Sct dominant-mode recovery" scores a γ Dor/rotation frequency in the same band as the diurnal systematic (only 2 fall inside the 0.02 c/d bands, so accidental in-band matches are few).
Evidence Anchor: dataset: `roster_d3.csv` — 117 positives with `dom_freq_per_day` < 4.
Suggestion: same regime split as W2; state that "dominant Mo mode" is amplitude-dominant, not p-mode-dominant.
Severity: Major | Confidence: 5 | Class: A + B.

**W4 = F12 — D2 assumes strict amplitude and phase coherence over 2,000–2,700 d.**
Problem: the truth model evaluates fixed-amplitude, fixed-phase sinusoids at every ZTF epoch across the whole baseline; real DAV modes wander in amplitude and phase on weeks–months, drop out, and carry unresolved rotational splitting. The ±30% scale and dominant-mode dropout axes test neither coherence loss nor phase wander.
Evidence Anchor: text: d2_truth_model.py:244–245 "phase = 2.0 * np.pi * mode.frequency_per_day * (bjd_tdb - t_ref); delta += amp * np.cos(phase + mode.phase_rad)".
Why it matters: D2 recovery is an upper bound for real DAVs at the same published amplitude; the text must say so or "conditional injection-recovery" will be read as "DAV recovery".
Suggestion: state the coherence assumption and the direction of the bias; future work: stochastic phase-wander injections (C).
Severity: Major | Confidence: 5 | Class: A + C.

**W5 = F13 — The D2 truth population is discovery-biased toward high amplitude.**
Problem: TESS-discovered DAVs at T ≈ 16–17 need ppt-level amplitudes to pass a FAP(1/1000) limit; dominant amplitudes 10/50/90 = 3.2 / 10.2 / 28.3 ppt (3.4 / 11 / 31 mmag), well above the K2/Kepler DAV population.
Evidence Anchor: dataset: `d2_modes.csv` — dominant `amp_ppt` quantiles 3.17 / 10.23 / 28.31.
Suggestion: state the selection and quote the amplitude quantiles; the amplitude surface, not the aggregate P4, is the transferable object.
Severity: Major | Confidence: 5 | Class: A.

**W6 = F23 — Kepler LC integration attenuation of the dominant amplitude is unresolved.**
Problem: if Mo's amplitudes are not sinc-corrected, dominant modes at 60–113 min carry |sinc| 0.68–0.89; the amplitude axis of the sub-hour-adjacent bins shifts by up to ~1.5× (less than one bin width, but systematic). The plan schedules a W3 check with no record of its outcome.
Evidence Anchor: text: GENERALIZATION_PLAN.md:136–137 "Mo amplitude sinc-correction status gets verified against the paper in W3".
Suggestion: record the verification result; if uncorrected, add a descriptive corrected-amplitude column (A / sinc(π·29.42 min / P)) beside the frozen axis.
Severity: Minor | Confidence: 3 — pending verification | Class: A + B.

**W7 = F24 — The Mo table1 flag used for the sub-hour stratum is undefined in the text.**
Problem: `subhour = KIC in table1 rows with C == 0` (13,463 of 15,265 rows); the plan calls this "any confirmed SNF" without stating what `C` encodes.
Evidence Anchor: text: build_d3_roster.py:135 "subhour_kics = set(snf.loc[snf[\"C\"] == 0, \"KIC\"].astype(int))".
Suggestion: quote the column definition from Mo+2026 in the methods.
Severity: Minor | Confidence: 3 | Class: A.

**W8 = F30 — CROWDSAP is small for the verified targets, so PDCSAP amplitudes inherit large dilution-correction uncertainty.**
Problem: CROWDSAP 0.0145–0.4158 (median 0.19) for the 20 SPOC-verified targets; the PDCSAP amplitude is the SAP amplitude ÷ CROWDSAP, so a 10% error in CROWDSAP is a 10% error in the injected amplitude; the ±30% scale axis covers this only loosely.
Evidence Anchor: text: GENERALIZATION_PLAN.md:167–169 "the pre-G3 text's \"divide by CROWDSAP\" would have inflated amplitudes ~5× at the median CROWDSAP 0.19".
Suggestion: state the CROWDSAP range and that the amplitude-scale axis is the proxy for it.
Severity: Minor | Confidence: 4 | Class: A.

**W9 = F38 — Arm A vs arm B on identical windows is the cleanest native-variability diagnostic and is not tabulated as a pair.**
Problem: pilot arm A recovers 8/30 with 10/30 triggers; arm B recovers 5/30 with 17/30 triggers — real windows raise triggers and lower recovery relative to the Gaussian floor. The spec calls arm A "diagnostic" and defines no A–B contrast.
Evidence Anchor: table: `d2_cluster_completeness.csv` (gen2 pilot) — A/nominal recovery p = 0.267 vs B/nominal recovery p = 0.167.
Suggestion: a descriptive paired A/B table per (target, K) from `per_star.csv`.
Severity: Minor | Confidence: 4 | Class: B.

### Questions for authors
1. Are Mo table2 frequencies documented as the extracted sub-Nyquist values? (W1)
2. How many of the 290 "sub-hour" members have their largest-amplitude mode above 283 µHz once `fR` is used? (W1/W2)
3. Was the Kepler LC sinc-correction status of Mo amplitudes verified? (W6)

### Dimension scores
| Dimension | Score | Descriptor |
|---|---|---|
| Originality | 72 | Strong |
| Methodological Rigor | 70 | Adequate (truth provenance gaps) |
| Evidence Sufficiency | not assessed | |
| Argument Coherence | 66 | Adequate |
| Writing Quality | 62 | Adequate |

---

## Report 5 — Devil's Advocate

*(Genuine strengths, stated once: the study is honest about what D2 is not, freezes labels and crossmatches before outcomes, and has already used its own pilots to catch two construct-validity defects. That is more than most survey-completeness papers do.)*

### Strongest counter-argument
The campaign promises a "response assessment beyond the development sample" but its two new datasets are each, in a different way, the development sample again. D2's "real ZTF windows" are the 928 white-dwarf light curves whose blind statuses the pipeline itself published: 45% of the pool and 52% of the nominal-B assignments are windows the pipeline already calls variable, and the new W_g stratification — chosen to repair the degenerate exposure strata — sorts windows by within-night support, which in this pool is almost the same thing as sorting by the pipeline's own confirmed flag (K2 windows are 84% published variables, K0 windows 74% non-detections). Any "recovery rises with W_g" trend will be entangled with native variables outcompeting the injected mode for the best candidate. The paired controls that "reproduce published status 10/10" do so by construction (same bytes, same code). D3 is external, but its answer is largely predetermined: a pipeline built for 5–20 mmag pulsations is asked about a population whose median historical amplitude is 1.8 mmag; the turn-on curve will be the a95 noise floor drawn through the Kepler amplitude axis, and the D3 negative-class result will be the field's solar-diurnal systematic, which the pipeline's sidereal-only veto cannot see. The only confirmatory decision (P5) tests whether a Baluev bound is a bound under Gaussian noise — it confirms no hypothesis of the paper and may fail on multiplicity alone. Finally, the "frozen pipeline" sits on top of an analysis plan amended four times, twice after data were seen. A hostile reader will summarise: "a bespoke pipeline is shown to find large coherent signals and to trigger on a systematic, in one field, with a pre-registration that moved." The defence is available but must be written: the deliverable is a calibration (turn-on location + systematic floor), not a discovery; the amendments are pilot-informed and dated; the D2 confounding is measurable from the manifest; and the D1 catalog shows the systematic is field-specific (18/342 in-band).

### Issue list

#### CRITICAL
| # | Dimension | Issue Description | Evidence Anchor | Confidence | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|---|---|---|---|---|---|
| C1 | Core thesis / Foundation | = F11 + F08. The D2 window frame is the pipeline's own published catalog and the W_g strata are confounded with the pipeline's own confirmed flag (K2: 62 confirmed + 24 candidate of 103), so the "conditional injection-recovery of the search stage" is conditional on windows selected by a variable strongly correlated with the pipeline's prior outcome — a residual of the G1 circularity that the all-928 fix did not remove. Alone this does not invalidate D3, but it invalidates any *window-stratified* D2 claim as stated. | dataset: `shard_manifest_gen2.csv` — template_status by template_k: K0 76/26/1, K1 55/41/7, K2 17/62/24 (nd/conf/cand) | 5 — core: injection-recovery design | Injection–recovery convention (e.g. Kepler/TESS completeness papers) requires the injection frame to be selected independently of the detector's output on that frame | Here the stratification covariate is correlated with the detector's prior output on the very windows used |

#### MAJOR
| # | Dimension | Issue Description | Evidence Anchor | Confidence | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|---|---|---|---|---|---|
| M1 | "So what?" | = F35. The D3 turn-on is the a95 floor drawn through the Kepler amplitude axis; the result is predetermined in shape and only its location is new. The text must frame the deliverable as a calibration (turn-on location, systematic floor), not as a discovery about δ Scuti. | text: GENERALIZATION_PLAN.md:376–377 "D3 completeness ≈ 0 below the a95 floor → stratification IS the deliverable (turn-on curve)" | 4 | — | — |
| M2 | Logic chain | = F06 restated from the DA angle: the sole confirmatory decision decides nothing about the paper's thesis; a pass will be over-read, a fail is unplanned. | text: METRICS_SPEC.md:153 "the sole confirmatory decision" | 4 | — | — |
| M3 | Confirmation-bias / pre-registration | = F05. "Frozen pipeline" is true; "frozen analysis" is not: Amendment 4 and the diurnal partition are pilot-informed, and the spec's own freeze sentence says such changes void the prespecification. | text: G2_FREEZE.md:292–294 "Amendment 4 is disclosed as pilot-informed and is not represented as part of the original v3 preregistration" | 5 | — | — |
| M4 | Overgeneralization | = F16 + F14 + F32. One field, one Galactic latitude, one cadence history, one systematic family; the D1 catalog's confirmations are 95% outside the diurnal bands, so the D3 floor is field-specific and nothing about "ZTF" follows. | dataset: `ls_full_catalog.csv` — 18/342 confirmed inside the diurnal bands vs ~30/33 pilot passes in D3 | 4 | — | — |
| M5 | Logic chain | = F01/F09. Both P1 (D3) and the D2 trigger endpoint credit "confirmed for the wrong reason"; the frozen best-pass rule even demotes correct high-pass recoveries (pilot 7/30 → 5/30). The text must lead with attributed endpoints (P2, P4-recovery). | table: gen2 pilot `completeness_by_class_pass_rule.csv` — best/confirmed/correct_frequency_fraction_detected = 5/17 | 5 | — | — |

#### MINOR
| # | Dimension | Issue Description | Evidence Anchor | Confidence |
|---|---|---|---|---|
| m1 | Cherry-picking risk | Thirteen claim templates and ~40 descriptive tables give wide latitude to headline the flattering row; the primary family mitigates it, but the poster should print the five primaries first, in the spec's order. | text: ABSTRACT_SKELETON.md:9 "claim list is the ceiling of what the design supports" | 4 |
| m2 | Alternative path | The D1 928-star catalog itself (all with published statuses and the same window set as D2) could have served as a labelled *negative-class* frame for the systematic audit (best-frequency distribution), which the paper does not use. | dataset: `ls_full_catalog.csv` — 342 confirmed, 277 low-pass, median 2.56 c/d | 3 |
| m3 | Stakeholder blind spot | The ZTF calibration/DR team's perspective on solar-diurnal residuals is absent (the mechanism is asserted from one pilot). | absence: GENERALIZATION_PLAN.md — expected a systematics-provenance paragraph; checked plan risks 373–387, G2_FREEZE diurnal entry, RUNBOOK | 3 |

### Ignored alternative explanations / paths
1. The P3 pile-up may be a near-saturation (nonlinearity × airmass) effect confined to g < 14 stars rather than a field-wide extinction-colour term; the two predict different magnitude gradients (testable descriptively — F15).
2. The K-stratum recovery gradient, if seen, may be entirely native-variable suppression rather than a support effect (testable — F08's K × status table).
3. A failed P5 may reflect Baluev's four-way multiplicity in the frozen rule, not a pipeline miscalibration (F06).

### Missing stakeholder perspectives
- ZTF calibration/DR team (systematics provenance).
- Murphy+2019 / Mo+2026 authors (flag semantics, Nyquist convention of table2 — F02, F24).

### Unexamined premise
That "response beyond the development sample" can be established with windows drawn from the development sample (D2) and with a single field (D3). The premise is defensible only if the paper explicitly downgrades D2 to "within-sample search-stage response" and D3 to "one-field external validation".

### Observations (non-defects)
- The pilot-driven repairs (Amendments 2–4) are evidence the pre-registration is functioning, not failing — if the exposure table (F05) is printed.
- The D1 catalog's 342 confirmations being 81% low-pass is itself an interesting descriptive fact for the WD paper and costs nothing to show.

---

# Phase 2 — Editorial synthesis

## Panel provenance
All five personas ran on one model family (the session model); persona diversity is not model diversity, so blind spots may be correlated across seats. No cross-model track was run (methodology-focus mode has no Reviewer-2 substrate swap).

## Decision: **Major Revision of the write-up plan** (design unchanged; results pending)

The design needs no estimand change and cannot have one. What must change is what the text says and which descriptive tables accompany the frozen outputs. Nothing found is class C except two future-work items (solar-family veto; stochastic DAV injections) and the coherence caveat.

## Top blocking issues (ranked)

| Rank | Blocking issue | Source | Evidence anchor | Resolving item |
|---|---|---|---|---|
| 1 | Headline D3 detection completeness P1 counts diurnal-systematic triggers; must be presented as P1/P3/P2 triplet with a match-class partition (F01, M5) | R-TD, DA | text: METRICS_SPEC.md:127–128 (P1 tuple) | R1 |
| 2 | Truth-label provenance: Mo table2 aliases (F02), sub-hour stratum not high-pass (F03), g-mode dominants (F04) | R-SEIS | dataset: `raw/mo2026_table1.csv` `fR` vs table2 `Freq` | R2 |
| 3 | D2 window frame = development catalog and W_g strata confounded with native variability (F08, F11, C1) | DA, R-ZTF, R-STAT | dataset: `shard_manifest_gen2.csv` status × K | R3 |

## Consensus analysis

**CONSENSUS-4+** (independent corroboration across seats):
1. The confirmed rule fires for reasons unrelated to the labelled signal, in both D3 (diurnal) and D2 (native variables); attributed endpoints must lead — R-TD W1, R-STAT W4, R-ZTF W1, R-SEIS (W9 A/B contrast), DA M5.
2. The D3 result is field-specific and the amplitude turn-on is floor-limited — R-ZTF W4/W5, R-SEIS W5 (D2 analogue), DA M1/M4, R-TD (crowding lens W3).
3. Pre-registration exposure must be printed as a dated table — R-STAT W1, DA M3 (R-TD silent, R-ZTF silent, R-SEIS silent → CONSENSUS-2 with no dissent).

**Disagreements**
- *Severity of the D2 confounding.* DA rates it CRITICAL (C1); R-STAT and R-ZTF treat it as Major with a descriptive remedy. **Editor's resolution**: Major-with-mandatory-disclosure. Rationale: the aggregate P4 (equal-weight over K) is a defined, honest estimand of a stated scenario mix; what is invalidated is any *window-support gradient* claim, and the K × template_status table (B) plus the paired A/B and control tables make the confounding visible without a re-run. DA's C1 is therefore **adjudicated and partially upheld**: it blocks any K-trend sentence in the abstract; it does not block the aggregate P4. Recorded per Iron Rule 4.
- *Whether P5 is a real risk.* R-STAT (Major) vs the pilot's 0/30 (uninformative). Resolution: keep Major; the remedy is a sentence, cheap and necessary.

## DA CRITICAL adjudication (Iron Rule 4)
C1 — validated in part (see above). Consequence: the abstract/poster may not state a recovery-vs-W_g trend without the K × native-status decomposition beside it; the aggregate P4 may be stated.

## Decision rationale
Every seat independently converged on the same two mechanisms (wrong-reason confirmations; field/frame specificity) and on the same remedy class (disclosure + descriptive tables from frozen outputs). No finding requires an estimand or pipeline change, so "Major Revision" here means a substantial rewrite of the claims layer and roughly ten descriptive tables/figures before G5/G6, not a re-run. A lesser decision would leave the abstract exposed on P1 and on the sub-hour truth labels; a stricter one would ignore that the design is the strongest part of the manuscript.

## Required revisions (Must Fix — all A or B)

| # | Revision item | Findings | Severity | Source | Class |
|---|---|---|---|---|---|
| R1 | Present P1 with P3 and P2; partition confirmed positives by match class × top-15 presence | F01 | Major | R-TD/DA | A + B |
| R2 | Disclose Mo table2 Nyquist-alias provenance; add `fR`/reflection rescoring column; rename sub-hour stratum; split P2 by dominant-frequency regime | F02, F03, F04 | Major | R-SEIS | A + B |
| R3 | Disclose D2 frame = development catalog + reuse (106/309, max 12); K × template_status recovery/trigger table; paired A/B table | F08, F11, F38 | Major | DA/R-ZTF/R-STAT/R-SEIS | A + B |
| R4 | Dated amendment/exposure table; explain the spec freeze sentence vs "confirmatory" | F05, F28 | Major | R-STAT | A + B |
| R5 | State P5's a-priori expectation and the consequence of x ≥ 2; state P5 gates nothing else | F06 | Major | R-STAT | A |
| R6 | Emit the seven-dimension attrition table and the joined-vs-unjoined covariate table | F07 | Major | R-STAT | B |
| R7 | Report per-pass recovery rows beside P4 and say P4 is best-pass | F09 | Major | R-STAT | A + B |
| R8 | Re-issue ABSTRACT_SKELETON.md under Amendment 4 (recovery primary; plain Wilson P3; no D2 "non-overlapping" interval claim) | F10, F20 | Major | R-TD | A |
| R9 | Systematics paragraph: solar vs sidereal veto coverage, two-band rule vs common-mode, multi-oid merging; tables by Teff, magnitude, merged-oid count; P3 by pass | F14, F15, F17, F37 | Major | R-ZTF | A + B (+ C for the veto) |
| R10 | Coverage comparison table D3 vs pool; per-pass a95 by class; "one-field" scoping sentence | F16, F18 | Major | R-ZTF | A + B |
| R11 | D2 coherence assumption and amplitude-selection statements; future-work item for phase-wander injections | F12, F13 | Major | R-SEIS | A + C |
| R12 | Disclose the degenerate crowding lens; continuous-covariate tables | F19 | Major | R-TD | A + B |
| R13 | Frame the deliverable as calibration (turn-on location + systematic floor), not discovery | F35 | Major | DA | A |

## Suggested revisions (Should Fix)
F21 (dominant-only chance rate, B), F22 (g = 14.0 convention, A), F23 (Kepler sinc status, A/B), F24 (flag C semantics, A), F25 (stratum labels, A), F26 (usable definition, A), F27 (sky-cell P3, A/B), F29 (pilot sky corner, A), F30 (CROWDSAP, A), F31 (magnitude systems, A), F32 (D1 low-pass context, A/B), F33 (yearly/Nyquist relations, B), F34 (D2 turn-on figure, B), F36 (pointwise wording, A), F39 (write the briefs, A).

## Revision roadmap
- **Priority 1 (before G5, ~3 days)**: R1, R2, R3, R6, R7 — the descriptive tables (all from `per_star.csv`, JSONs, roster, table1, manifests; follow the `descriptive/` precedent: outside the campaign SHA glob, `prespecified=false`, no intervals).
- **Priority 2 (before G6, ~2 days)**: R4, R5, R8, R9, R10, R11, R12, R13 — text: methods paragraphs, exposure table, re-issued skeleton, the two briefs.
- **Priority 3 (poster/abstract polish)**: the Should-Fix list.

## Closing
The panel would not reject this design; it would reject an abstract that quotes P1 alone, calls the sub-hour stratum a sub-hour test, or reports a recovery-vs-support gradient without the native-variability decomposition. Each of those is preventable in the text.
