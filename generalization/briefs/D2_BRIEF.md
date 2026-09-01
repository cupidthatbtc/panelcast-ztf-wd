# D2 — TESS-truth DAV signals in real ZTF windows: conditional injection-recovery efficiency of the search stage

Written 2026-09-01 (methods-panel F39). Design facts only; no campaign result. Sources: GENERALIZATION_PLAN.md (SHA e2cd36af…), METRICS_SPEC.md (SHA 66013732…), data/d2/d2_roster_report.json, results/2026-08-30_d2_pilot_gen2/README.md, scripts/generalization/{build_d2_roster,build_d2_shards}.py, writing/methods_review/{FINDINGS,REVIEW_PANEL}.md. `⟨TBD⟩` = not yet in the repo. NOT an externally labeled sample (G1; N3, N4).

## 1. Source catalogs

| Role | Source | Bibcode / id | Content used | Raw SHA-256 (8) |
|---|---|---|---|---|
| Truth (mode tables) | Romero et al. 2022, MNRAS 511, 1574 | 2022MNRAS.511.1574R; arXiv:2201.04158 | 74 new DAVs, TESS Cycles 1–3; per-mode period [s], amplitude [ppt]; per-star FAP(1/1000) limit; sector list with 20-s ('f') flags; RA/Dec; magnitude | 4432c09d (src tar); f1f35024 (NewTess.tex) |
| Truth (mode tables + revisions) | Romero et al. 2025, ApJ 984, 112 | 2025ApJ...984..112R; arXiv:2407.07260 | 32 new DAVs, Cycles 4–5; "old" table = revised solutions for re-observed 2022 objects incl. NOV retractions | 850aed26 (src tar); c92ee7e0 (NewTESS.tex) |
| Windows (templates) | Published 2026-08-01 ZTF white-dwarf catalog, `catalog-rebuild/results/2026-08-01_full` | tag `frozen-2026-08-01` | ALL 928 attested per-star exposure shards (real bjd_tdb, mags, magerr); status 510 not_detected / 342 confirmed / 76 candidate | — |
| Verification | TESS SPOC light curves (MAST) | — | v2: published sectors, ~20 targets, CROWDSAP on file; v3: all 103 targets (cadence composition) | spoc_verification/ |

Parsed outputs: `d2_targets.csv` (103; SHA 4faf2117…), `d2_modes.csv` (341; 0b82a937…), `d2_modes_all_solutions.csv` (415; 5f375e5a…). Parser normalizes LaTeX typos (comma decimals, stray units, missing parens) mechanically with hard row-count / range asserts; G3 reviewed against the PDFs.

## 2. Selection chain

| Step | Rule | Count |
|---|---|---|
| 0 | Romero+2022 (74) + Romero+2025 new (32) | 106 |
| 1 | Drop NOV retractions (TIC 261400271, 317620456, 804835539) | 103 |
| 1′ | Composition: 2022-only 53; 2025-new 32; 2022 objects superseded by the 2025 "old" table 18 (latest published solution wins) | 103 |
| 2 | Modes retained per star from the chosen solution | 341 (median 3 / star, max 19) |
| 3 | Cadence rule: `cadence_s` = 20 iff the chosen solution has any 'f' sector, else 120 | 49 targets at 20 s; 33 mixed 20-s/120-s (SPOC v3) |
| 4 | Signed-sinc rejection \|sinc\| < 0.3 (P < ~160 s at 120 s; < ~27 s at 20 s) | 22 rejected mode rows over gen2; targets with 0 retained modes: 0 → 103 scheduled |
| 5 | Template matching, K = 3 windows per target | 309 nominal arm-B assignments on 106 unique windows |
| 6 | Full production generation gen2 (id 129740d1…4ef7cb) | 3,089 shards |

Target properties: P 115.924–1,879.21 s (2.9 % of modes P < 240 s); A 0.39–88.17 ppt; dominant amplitude 10/50/90 = 3.2 / 10.2 / 28.3 ppt; g 13.53–17.48 (median 16.46); CROWDSAP 0.0145–0.4158 (median 0.19) on the SPOC-verified subset.

## 3. Label and truth provenance

| Item | Value |
|---|---|
| "Label" | Every target is a published DAV; the positive class is the injected signal, not an external label of the ZTF source |
| Truth used by the scorer | `injected_modes.csv` of the generation (post-sinc, signed factors, phases) — never the original mode table; rejected modes in `rejected_modes.csv` |
| Amplitude chain | ppt → mag (× 1.0857e-3) → PDCSAP as published (already dilution-corrected; no de-dilution) → de-integrate TESS boxcar (signed sinc at `cadence_s`, exposure-midpoint timestamps) → bandpass ladder A_g/A_TESS ∈ {1.4, 1.7, 2.1} × A_r/A_g ∈ {0.70, 0.80, 0.90}, nominal (1.7, 0.80) = grid midpoint (blackbody 11,500 K derivative gives (1.43, 0.80) ≈ low rung) → re-integrate ZTF 30-s boxcar |
| Phases | One independent phase per mode; base draw PCG64(TIC), shared across bands and all variants; sensitivity draws d ∈ {1, 2} seed PCG64(TIC·10 + d); shared t_ref |
| Signal model | Strictly coherent, fixed-amplitude sinusoids evaluated analytically at the template's real `bjd_tdb` (baseline 2,000–2,700 d) |
| Surface coordinate | Largest-amplitude RETAINED injected mode: period; published TESS amplitude (ppt), invariant across scenarios |
| Known limits | Coherent / stationary assumption (upper bound at fixed amplitude, F12); TESS-discovery amplitude bias (F13); phenomenological bandpass grid, no DA-atmosphere validation of endpoints; PDCSAP dilution uncertainty (F30); cadence_alt = pure-120-s endpoint, not the stitched effective cadence (~1.1–1.4 bias vs 1.95 endpoint contrast at 200 s) |

## 4. Windows, sampling, and strata

| Item | Value |
|---|---|
| Pool | 928 published-catalog stars (45 % published variables); NOT the 510 not-detected subset (G1 circularity fix) |
| Magnitude match | \|median zg − target G\| ≤ 0.25 (widen to 0.5, then nearest-9; flagged); all 309 nominal matches at ≤ 0.25 |
| W_g | Σ_nights max(n_zg,night − 1, 0) = zg support surviving nightly-median subtraction; pool 10/50/90 = 6 / 58 / 452; 75 % of zg nights single-exposure; median subtraction annihilates 53 % of zg data |
| K strata | K = 0/1/2 at round-half-even 10/50/90th positions of the matched pool sorted by (W_g, source_id); strictly increasing W_g for 103/103 (production refuses otherwise) |
| W_g by K (mean, range) | K0 7.6 (0–23); K1 62.8 (8–127); K2 433 (100–786) |
| Template status by K (nd / conf / cand) | K0 76 / 26 / 1; K1 55 / 41 / 7; K2 17 / 62 / 24 (K2 = 84 % published variables) |
| Reuse | 106 unique windows carry 309 assignments: 36 used once, one used ×12, top two = 22; 161/309 (52 %) on published-variable windows |
| Surface edges | W_g {15, 41, 84, 217} (20/40/60/80th pct of the 928 pool; builder recomputes and refuses on mismatch); amplitude {0.5, 2, 5, 10, 30} ppt, top [30, ∞); period {100 s … 100 d} |
| Unit of inference | TESS target (TIC) = cluster; equal-weight target mean; conditional on the frozen window assignment (never "unbiased for the 928 frame", N26); cluster bootstrap B = 2000, seed 20260830, common draws |

## 5. Run matrix (gen2, 3,089 shards; every arm binding)

| Arm / scenario | Prefix | Windows | Shards | Role |
|---|---|---|---|---|
| Arm B nominal (1.7 / 0.80, PDCSAP, phase 0, cadence rule) | 92 | K = 0, 1, 2 | 309 | PRIMARY-P4 (recovery); SECONDARY (trigger) |
| Arm A nominal (Gaussian floor N(0, magerr_i) on real timestamps) | 93 | K = 0, 1, 2 | 309 | DIAGNOSTIC |
| Gaussian nulls (arm A, amplitude 0; serial i → sorted-pool window i mod 928; noise seed = serial) | 94 | 928 cycled | 1,000 | PRIMARY-P5 (sole confirmatory) |
| Paired uninjected controls (one per unique arm-B window) | 95 | 106 | 106 | native trigger rate; paired D / R |
| Bandpass ladder, 8 non-nominal (R_g, R_rg) points | 92 | K = 1 | 824 | DESCRIPTIVE-PRESPEC (finite-grid range) |
| Phase draws d = 1, 2 | 92 | K = 1 | 206 | DESCRIPTIVE-PRESPEC |
| Amplitude scale 0.7, 1.3 (local sensitivity, N10) | 92 | K = 1 | 206 | DESCRIPTIVE-PRESPEC |
| Dominant-mode dropout (targets with ≥ 2 retained modes) | 92 (S = 3) | K = 1 | 76 | DESCRIPTIVE-PRESPEC (own scenario) |
| cadence_alt (mixed-cadence targets, 120 s; Amendment 3) | 92 (D = 1) | K = 1 | 33 | DESCRIPTIVE-PRESPEC (endpoint) |
| SAP-equivalent re-dilution A × CROWDSAP (SPOC-verified; Amendment 2) | 92 (C = 1) | K = 1 | 20 | DIAGNOSTIC (stretch) |
| Romero self-window diagnostic (real ZTF at the 103 positions) | 96 | own | ⟨TBD: count set by crossmatch yield; `selfwindow_roster.csv` lists 103; not in gen2⟩ | DIAGNOSTIC, never enters nominal |

Campaign id layout `AA TTTTTTTTTT K GR PS CD`; every contrast vs nominal uses the common-subset rule (same K = 1 targets, same draws); no crossing of sensitivity axes.

## 6. Estimands this dataset feeds (names binding, METRICS_SPEC)

| Estimand | Definition | Denominator | Interval | Status |
|---|---|---|---|---|
| Conditional injection-recovery efficiency (P4) | rule 1 fires AND best candidate = direct match to the largest-amplitude retained injected mode, per (target, K), target-equal mean | eligible 103 (missing stratum = 0, \|K_t\| = 3); usable 103 − n_∅ | target-cluster bootstrap 95 % | PRIMARY-P4 (Amendment 4) |
| Post-injection rule-1 trigger rate | rule 1 fires | same | same | SECONDARY (no recovery meaning, N12) |
| FPR_Gaussian (P5) | P(confirmed \| zero-amplitude null) | 1,000 | exact one-sided CP upper; accept iff U95 ≤ 0.005 ⇔ x ≤ 1 (x = 0 → 0.299 %, 1 → 0.474 %, 2 → 0.628 %) | PRIMARY-P5 (sole confirmatory decision) |
| Native trigger rate of the template pool | P(confirmed \| control window) | 106 | descriptive | DESCRIPTIVE-PRESPEC |
| Paired controls D / R | control scored against partner's injected truth; 2 × 2, B-only / C-only / union, P(R_B = 1, R_C = 0), quiet-control-conditioned secondary | pairs | cluster bootstrap; CP discordance bound when degenerate | SECONDARY |
| Scenario contrasts | scenario − nominal K = 1 on identical targets, common draws | per scenario (76 dropout, 33 cadence_alt, 20 redilution, 103 others) | paired difference | DESCRIPTIVE-PRESPEC |
| Chance-match calibration | 10,000 target-level derangements, endpoint-aligned numerators | — | — | DESCRIPTIVE-PRESPEC |
| Census vs L-S post-injection response | 2 × 2 on nominal arm B; no row-level intervals; McNemar prohibited | — | cluster paired difference | DESCRIPTIVE-PRESPEC (no recovery attribution) |

## 7. Known limitations (panel A-class items)

| ID | Limitation |
|---|---|
| F06 | P5 has a non-trivial a-priori failure chance (four band × pass routes to a Baluev FAP < 1e-3 top peak); x ≥ 2 changes only the FPR_Gaussian sentence; it confirms no scientific hypothesis |
| F08 | W_g strata confounded with native variability (K0 74 % not_detected; K2 84 % published variables) → no K-trend sentence without the K × template-status table |
| F09 | P4 is a best-pass estimand; the frozen best-pass rule can demote correct high-pass recoveries (P4 ≤ high-pass row by construction) |
| F11 | Frame = the pipeline's own development sample; 106 windows carry 309 assignments → "within-development-sample search-stage response" |
| F12 | Coherent fixed-amplitude sinusoids over 2,000–2,700 d → recovery is an upper bound at fixed amplitude; phase-wander / amplitude modulation = future work |
| F13 | TESS-discovery amplitude bias (3.2 / 10.2 / 28.3 ppt) → the amplitude surface, not the aggregate, is the transferable object |
| F20 | "Empirically non-overlapping" not assertable for D2 (descriptive 2 × 2, no intervals) |
| F30 | PDCSAP amplitudes inherit dilution-correction uncertainty (CROWDSAP 0.0145–0.4158); amplitude-scale axis is its proxy |
| F31 | Matching magnitudes: Romero star-table G ⟨TBD: confirm the Romero column header⟩ vs ZTF median zg |
| F35 | High-pass ≈ 0 from the single-exposure-night penalty is the pre-registered expected headline (risk 3) → calibration, not discovery |
| plan | Bandpass ladder is a phenomenological grid; ±30 % is a local sensitivity; inference conditional on the frozen window set; cadence_alt is an endpoint; pilot numbers (gen1 16/30, 7/30; gen2 5/30, 17/30) never appear as results (N16) |

## 8. What this dataset can and cannot support

| CAN | CANNOT |
|---|---|
| Conditional injection-recovery efficiency of the frozen search stage for published DAV mode solutions at published amplitude, in real ZTF windows of matched magnitude | Real-sky DAV completeness; "validates the pipeline on real DAVs" (N3) |
| Recovery vs W_g stratum and vs published amplitude / period, at target level, conditional on the frozen windows | Causal cadence / exposure claims; an unbiased estimate for the 928-window frame (N8, N26) |
| Prespecified finite-grid sensitivity ranges (bandpass, phase, amplitude scale, dropout, cadence endpoint), endpoints named | A "band", "envelope" or CI on the min–max; an astrophysical amplitude envelope (N10) |
| Gaussian-null false-alarm rate with an exact CP bound and one pre-registered acceptance decision | A real-sky or operational FPR (N17); a scientific hypothesis test |
| Native trigger rate of the 106 control windows and paired attribution diagnostics | Subtracting the native rate from P4; conditioning P4 on quiet controls (N13) |
| Post-injection census / L-S response tables (descriptive) | Complementarity claims with intervals for D2; pooled McNemar (N11) |
| Search-stage response within the development sample, labeled as such | An external-label validation; a third "independently labeled" sample (N4); anything beyond the bright-TESS-DAV amplitude regime (F13) |
