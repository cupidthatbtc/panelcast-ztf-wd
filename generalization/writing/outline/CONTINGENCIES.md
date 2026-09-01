# Contingency outlines — results strong vs results ugly

Rule of the game: the branches change WORDING (headline sentence, poster claim
paragraph, paper §4), never estimands, denominators, table rows, or labels
(Amendment 4). The ugly case is pre-registered as an explanatory headline
(GENERALIZATION_PLAN risks 2 and 3), so both branches are positive results
about the pipeline's response; only the sentence that carries them differs.

Branch selection is read off the frozen outputs with these observable triggers
(they are reading rules for prose, not acceptance criteria):

| Axis | STRONG trigger | UGLY trigger | MIXED (most likely) |
|---|---|---|---|
| D3 detection (P1) | eligible P1 lower Wilson bound clearly > 0 AND the > 10 mmag bin (48 stars) is high (k/48 ≳ 0.5) with the 1–10 mmag ladder intermediate | P1 point ≈ 0 AND even the > 10 mmag bin is ≈ 0 (k ≤ 2 of 48) | P1 small overall (sub-1 mmag majority) but the > 10 mmag bin clearly detected → a visible turn-on |
| D3 frequency (P2) | P2 point far above the chance rate (D3-4) | P2 indistinguishable from chance | P2 above chance on few stars |
| D3 negatives (P3) | P3 low (k/2314 ≲ 1 %) with FP frequencies not concentrated in the diurnal bands | P3 high with most confirmed negatives inside the diurnal bands | P3 moderate; partition shows a diurnal share |
| D2 recovery (P4) | eligible P4 lower cluster bound > 0 AND K2 (high W_g) ≫ K0 | P4 point ≈ 0 in all strata (≤ 3 of 103 targets recover anywhere) | P4 ≈ 0 in K0, non-zero in K2 → the pre-registered single-exposure-night headline |
| D2 nulls (P5) | x ≤ 1 → confirmatory PASS | x ≥ 2 → FAIL (U95 > 0.5 %) | — |

## 1. STRONG branch

### 1.1 Abstract (differences from OUTLINE §1.2)
- S14 becomes: "Within its magnitude-restricted Kepler frame the frozen rule detects labeled δ Scuti with ⟨P1⟩ completeness and recovers ⟨P2⟩ of dominant frequencies, triggers on ⟨P3⟩ of non-δ-Scuti stars, recovers ⟨P4⟩ of injected DAV models with FPR_Gaussian ⟨U95⟩; census and period-search responses remain non-overlapping in each assessment." (all five primaries in one closing sentence; still no pooling)
- Keep S8 (turn-on) as the Tier-B survivor; drop S10 first.
- Title: OUTLINE §1.1 option 3 (class-specific completeness and trigger rates).

### 1.2 Poster
- Scoreline unchanged (six tiles). Claim paragraph leads with P1 and P4.
- F1 leads column 1 (turn-on with a clear step); F5 leads column 2; F7 leads column 3 with the P5 PASS line.
- "What this does not establish" keeps N1, N3, N5, N7, N19 (still true when strong).

### 1.3 Paper (RNAAS)
- §3 opens with Table 1 rows 1, 3, 5, 8, 15 in one paragraph; §4 spends its budget on N3/N7/N19 limits and on the strata (K0/K1/K2) reading: "recovery is a function of surviving within-night support, conditional on the frozen windows".
- If P5 PASSES: "the preregistered acceptance ⟨U95 ≤ 0.5 %⟩ holds" (the only sentence in the paper that may use the word "confirmatory").

## 2. UGLY branch (pre-registered explanatory headline)

### 2.1 Why it is still a positive result
- Selection functions are the deliverable. A bounded zero is a measurement: one-sided 95 % Clopper–Pearson upper bounds for 0 successes are 0/610 → 0.49 %, 0/456 → 0.66 %, 0/290 → 1.03 %, 0/103 targets → 2.87 %, 0/48 → 6.05 %. Each is a defensible completeness statement about a labeled class at ZTF cadence with the frozen rule; none existed before.
- The mechanism was pre-registered: 75 % of zg nights are single-exposure and nightly-median subtraction annihilates 53 % of zg data (median surviving support W_g = 58); D3 positives have median dominant amplitude 1.77 mmag, below the D1 median A95 limit of 5.2 mmag (published bundle). The ugly case is the prediction, and the strata make it explanatory.
- The census/L-S complementarity claim does not depend on high completeness; it depends on both discordant cells being populated.

### 2.2 D2 ugly (P4 ≈ 0 from the single-exposure-night penalty)
Headline sentence (replaces S11 + S14 content):
"With ⟨p_K0⟩, ⟨p_K1⟩, ⟨p_K2⟩ recovery in the low/median/high within-night-support strata, DAV signals injected into representative ZTF windows are ⟨not recovered above a one-sided 95 % bound of 2.9 %⟩ by the frozen high-pass search: the nightly-median residual stage discards most single-exposure nights, a pre-registered expectation now measured with cluster-level uncertainty."
Supporting slots and their artifacts (all already in EVIDENCE_MAP):
- D2-1/D2-2 with the CP bound reported when degenerate (spec: "if a statistic is degenerate, report the exact one-sided CP bound at the target level").
- D2-3 strata: the only place a gradient may be *described* (never causal — N8).
- D2-6 (post-injection trigger rate) beside it shows the pipeline still fires on native variability: the injected signal, not the pipeline, is what the windows cannot carry.
- D2-18 P(R_B=1,R_C=0) ≈ 0 confirms no accidental recoveries inflate the zero.
- D2-8/D2-9/D2-10: if every scenario also gives 0 with zero discordances, report discordance_u95 per row (CP bound, e.g. 0.632 at n=3 was the pilot's; at n=103 it is 0.029) — "no bandpass, phase, or amplitude-scale choice within the grid changes the conclusion, bounded at ⟨discordance_u95⟩".
- D2-15 P5 still stands alone; report PASS/FAIL regardless of P4.
- Arm A (D2-24, DIAGNOSTIC): if Gaussian-floor injections recover while arm B does not, one clause is allowed: "recovery under an idealized noise floor at the same timestamps is ⟨p_A⟩ (diagnostic)". Never a comparison test.
Poster: F5 becomes a mostly-empty surface with n_targets per cell — keep it; the emptiness IS the figure. Add the W_g histogram of the 928-window pool (from generation_manifest_gen2.json wg_pool_quantiles or per_star wg_contrasts) as an inset so the reader sees why K0 windows carry ~6 surviving contrasts.
Paper §4: two sentences on what would recover the signal (multi-exposure nights; this is a statement about cadence support, not a design recommendation for ZTF) — permitted because it describes the observed strata, not a causal estimate.

### 2.3 D3 ugly (P1 ≈ 0 below the amplitude floor)
Headline sentence (replaces S6/S8):
"The frozen confirmed rule detects ⟨x/610⟩ Kepler-labeled δ Scuti stars at KIC g ≥ 13.2 (one-sided 95 % upper bound ⟨U⟩ %); detections are confined to the ⟨≥ 10 mmag⟩ historical-amplitude bin (⟨k/48⟩) and absent below ⟨1 | 2 | 5⟩ mmag (⟨0/n⟩), where ⟨p_sub⟩ % of the labeled class lies — the turn-on curve is the result."
Supporting artifacts: D3-1 (with CP bound if 0), D3-7 (the turn-on; the amp_unknown bin must be shown so the 154 unjoined stars are not hidden), D3-16 (joined vs unjoined: the MNAR caveat matters more here), D3-15 (safe-magnitude subset to rule out saturation as the cause — descriptive only), D3-14 (attrition, to show usable-denominator P1 is not much higher), D3-20 (high pass near-empty).
If P2 is at chance: report it as "⟨x/n_S⟩ against an accidental rate of ⟨p_acc⟩; frequency recovery is not demonstrated" (P2 remains reported, never dropped).
If P3 is high and diurnal: F3(b) with the partition; sentence C18 verbatim disclosure; the rate is NOT corrected. Prose may say "the confirmed-negative frequencies lie within 0.02 d⁻¹ of integer solar-day harmonics in ⟨n_w/n_confirmed⟩ cases; the frozen veto covers only the sidereal family" — a description of where triggers sit, not a reclassification.
Poster: F1 leads, with the sub-1 mmag majority annotated; scoreline tile P1 shows "⟨0/610⟩ (< 0.5 %)" style bound; the D1 A95 = 5.2 mmag median limit may be quoted as D1 context in F1's caption (published number).
Paper §4: "what ZTF-cadence δ Scuti searches can and cannot see at these amplitudes" — restricted to g ≥ 13.2, Kepler field, historical amplitudes (N7, N19).

### 2.4 Both ugly
- Title: OUTLINE §1.1 option 1 or 2 (response-framed).
- Abstract closing (S14 replacement): "Both new assessments bound the frozen rule's completeness for low-amplitude, sparsely sampled signals near zero with quantified uncertainty while the census/period-search discordance persists; the surviving within-night support, not the search statistic, sets the limit."
- Table 1 unchanged; CP bounds appear in the interval column where the point estimate is 0.
- The paper stays RNAAS-length; nothing about the ugly case needs the ApJL fallback.

### 2.5 P5 FAILS (x ≥ 2 confirmed nulls)
- Sentence: "FPR_Gaussian = ⟨x/1000⟩ (U95 = ⟨U⟩ %) does not meet the preregistered ≤ 0.5 % acceptance." Reported in the same slot; the word "confirmatory" is then used only to say the decision failed.
- If x ≥ 10, the FP-frequency audit (D3-17 analogue for D2: fp_frequency_distribution.csv rows with arm=gauss_null) becomes informative per spec; describe the alias family (sidereal / diurnal) of the false alarms — descriptive.
- Nothing else in the abstract changes; P1–P4 are not gated on P5.

## 3. Complementarity sentence (S14) fails its condition
If any dataset has an empty discordant cell (e.g. D2 census-only = 0 or D3
L-S-only = 0), S14 must not say "non-overlapping in each assessment". Replace
with the per-dataset statement that holds ("in D1 and D3 both discordant cells
are populated; in D2 the census channel adds ⟨0⟩ recoveries beyond the period
search") and cite the three JSONs.

## 4. Schedule contingencies (from reviews/G2/sol_abstract.md §4, dated to the actual run finish)
| Failure | Warning sign | Decision |
|---|---|---|
| Metrics/G5 do not converge | D3 metrics not green with every guard by 2026-09-08; G5 re-derivation disagrees on any headline by 2026-09-19 | Remove D2 slots (S4, S11–S13) from the abstract on 2026-09-22 if D2 is not green; no-go the results abstract after 2026-09-24 if D3 headlines have not passed G5 — fall back to a design/preregistration abstract (D1 anchor + frozen design + "results in preparation"). |
| D2 full run fails or overruns | run not complete by 2026-09-06; failed shards > 2 % | Slip rule: D3 + D1 abstract; D2 "in progress"; the paper waits. |
| D3 metrics guard failure (crossmatch, sidecar, env) | any `SystemExit` in metrics | Fix the input chain, never the spec; if unfixable by 2026-09-15, D3 is out and there is no external-validation claim — abstract becomes D2 + D1 injection-recovery only (plan slip rule, second clause). |
| Diurnal partition finds a confirmed negative without a finite best-pass frequency | script aborts by design | Report the abort; the partition is omitted, P3 unaffected. |

## 5. What never changes across branches
Estimands, denominators, rules, passes, interval methods, the five primary
tuples, the P5 acceptance rule, the labels on every number, the disclosure
sentence, the mandatory citations, the "not allowed" list (OUTLINE Part D).
