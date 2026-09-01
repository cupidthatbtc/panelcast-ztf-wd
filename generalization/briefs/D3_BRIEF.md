# D3 — ZTF × Kepler δ Scuti: externally labeled, magnitude-restricted validation on real ZTF photometry

Written 2026-09-01 (methods-panel F39). Design facts only; no campaign result. Sources: GENERALIZATION_PLAN.md (SHA e2cd36af…), METRICS_SPEC.md (SHA 66013732…), data/d3/roster_report.json, data/d3/crossmatch_freeze/, scripts/generalization/build_d3_roster.py, writing/methods_review/{FINDINGS,REVIEW_PANEL}.md. `⟨TBD⟩` = not yet in the repo.

## 1. Source catalogs

| Role | Catalog | VizieR table | Bibcode | Content used | Raw file SHA-256 (8) |
|---|---|---|---|---|---|
| Labels, magnitude, Teff, positions | Murphy et al. 2019, MNRAS 485, 2380 | J/MNRAS/485/2380/table1 | 2019MNRAS.485.2380M | 14,330 Kepler A/F stars; `dSct` ∈ {0,1,2}; `gmag` (KIC g); Teff; logg; RA/Dec | 809be478 |
| Truth frequencies + amplitudes | Mo et al. 2026, A&A 710, A245 | J/A+A/710/A245/table2 | 2026A&A...710A.245M | 259,883 SNR > 8 frequencies (µHz) + amplitudes (ppt) for 1,838 δ Sct | f9b43552 |
| Super-Nyquist membership | Mo et al. 2026 | J/A+A/710/A245/table1 | 2026A&A...710A.245M | 15,265 confirmed super-Nyquist frequencies in 1,309 stars; columns Freq (alias), fR (physical, 99–1,410 µHz), C | ad3d7a61 |
| Photometry | ZTF public light curves via IRSA (frozen `fetch_catalog_lightcurves.py`, 10″ cone) | — | Masci et al. 2019, PASP 131, 018003 (doi 10.1088/1538-3873/aae8ac) | zg / zr epochs, magerr, catflags, chi | irsa_cache (1,474 entries) |

Roster: `data/d3/roster_d3.csv`, SHA d04f6e4e…; builder `build_d3_roster.py` SHA 3d7b2d23…; context: Bowman et al. 2016 (2016MNRAS.460.1970B; superseded as amplitude source by Mo+2026).

## 2. Selection chain

| Step | Rule | dSct=1 | dSct=2 | dSct=0 | Total |
|---|---|---|---|---|---|
| 0 | Murphy+2019 table1 | — | — | — | 14,330 |
| 1 | KIC g ≥ 13.2 (saturation proxy) | 610 | 76 | 7,292 (pool) | 7,978 (sum) |
| 2 | Take ALL dSct=1 and ALL dSct=2 (census) | 610 | 76 | — | 686 |
| 3 | SRS of dSct=0, seed 20260828, π = 2314/7292 = 0.31733406…, weight 7292/2314 = 3.15125324… | — | — | 2,314 | 2,314 |
| 4 | Roster (`roster_d3.csv`) | 610 | 76 | 2,314 | 3,000 |
| 5 | IRSA fetch: cache present / read OK | 610 / 610 | 76 / 76 | 2,314 / 2,314 | 3,000 |
| 6 | Frozen nearest-cluster crossmatch (`crossmatched`) — frozen as DATA 2026-08-31, commit e2988f2 | 585 | 72 | 2,244 | 2,901 |
| 6′ | Not crossmatched | 25 | 4 | 70 | 99 |
| 7 | Frozen QC passed (catflags, chi < 4, ≥ 20 exp/band) | ⟨TBD: metrics attrition.csv, full run⟩ | ⟨TBD⟩ | ⟨TBD⟩ | ⟨TBD⟩ |
| 8 | Both L-S passes complete (`usable_lightcurve`) | ⟨TBD⟩ | ⟨TBD⟩ | ⟨TBD⟩ | ⟨TBD⟩ |

Crossmatch realized data (`crossmatch_adjudication.csv`): nearest separation median 0.08–0.10″; objects in 10″ cone median 7–8; `selected_ztf_objects` over all 3,000: {0: 45, 1: 17, 2: 556, 3: 109, 4: 1,732, 5: 38, 6: 486, 7: 4, 8: 13}; oids merged per crossmatched star: 2 (544), 3 (105), 4 (1,715), 5 (38), 6 (482), 7–8 (17); epochs dropped 56,404 by catflags, 32,658 by chi < 4. `ambiguous` (multi-object cone) = 2,901/2,901. Crowding-clean (sep < 1.0″ AND ≤ 3 objects) = 275 = 228 / 44 / 3 (dSct 0/1/2).

Coverage (`panels_census_generic.csv`): zg ≈ 750 epochs / 640 nights / 82 months per star; `zg_median_exp_per_night` = 1.0 for 2,354 / 2,901; within-night support (n_exp − n_nights) median 112–126 vs 58 in the D2 928-star pool.

## 3. Labels

| Item | Value |
|---|---|
| Label | Murphy+2019 `dSct`: 1 = δ Scuti (positive, 610); 0 = not δ Scuti (comparison class, 2,314); 2 = ambiguous (own class, 76; excluded from every headline, reported separately) |
| Provenance | Obtained independently of the frozen pipeline; Murphy computed Fourier transforms only above 5 d⁻¹ and classified on 5–43.9 d⁻¹ (brief_diurnal/SUMMARY.md §4) |
| dSct=0 meaning | "not a δ Scuti", NOT "constant": contains γ Dor, rotational, binary and other variables → negative-class TRIGGER RATE, never FPR (plan risk 5; N5, N20) |
| Class covariates | g median 13.80 (pos) vs 14.05 (neg); fraction g < 14.0: 0.66 (pos) / 0.47 (neg) / 0.86 (dSct=2); Teff median 7,350 K (IQR 6,973–7,767) vs 6,675 K (IQR 6,581–6,845) |

## 4. Truth frequencies and amplitudes

| Item | Value |
|---|---|
| Truth list | ALL Mo+2026 table2 frequencies of the star (median 132 modes/star); table1 `fR` never enters the truth list |
| Dominant mode | Largest-amplitude table2 row: `dom_freq_uhz`, `dom_freq_per_day` (× 0.0864), `dom_amp_ppt` → `amp_mmag` (× 1.0857) |
| Join coverage | 456 / 610 positives Mo-joined (freq-scorable; spec asserts == 456); 154 unjoined → `amp_unknown` bin (index −1) on detection surfaces; join is MNAR (SNR > 8 in Kepler) |
| Amplitude (456) | > 10 mmag 48; 1–10 mmag 254; < 1 mmag 154; quantiles 5/25/50/75/95 = 0.173 / 0.712 / 1.769 / 4.429 / 24.238 mmag |
| Dominant frequency | 10/50/90 = 1.38 / 12.64 / 21.2 c/d (Mo-joined roster); 120 < 4 c/d; 0 ≥ 24.47 c/d (= Kepler LC Nyquist 283.2 µHz). dSct=1 only (456): 117 < 4 c/d (89 < 2.5), 10 in [24, 24.47) c/d, 0 ≥ 48 c/d, 2 inside the diurnal bands |
| Nyquist | Every table2 frequency is sub-Nyquist: roster max 282.92 µHz (full table2 max 283.257 µHz, E5) vs f_Nyq 283.2 µHz |
| Super-Nyquist flag (`subhour`) | ≥ 1 table1 row with C = 0 → 290 positives; their dominant frequencies 2.0 / 15.5 / 22.4 c/d (10/50/90) = LOW pass; 49 have dominant < 4 c/d |
| Reflection cases | For exactly 40 of the 290, the dominant table2 mode IS the super-Nyquist mode and is scored at its reflection 2·f_Nyq − fR (|diff| < 0.1 µHz) |
| Kepler LC boxcar | \|sinc\| at dominant period 0.68 / 0.80 / 0.89 (5th/25th/50th pct); Mo amplitude sinc-correction status ⟨TBD: W3 verification against Mo+2026⟩ |
| Match tolerance | 1.5 / baseline_days; truth quantum +0 (D3); f_sid = 1.00273790935 c/d; relations direct / harmonic / window_alias(k = 1, 2); yearly alias and Nyquist reflection are outside the taxonomy → `unmatched` |
| Pass bounds | low [2/baseline, 48] c/d; high [24, 1440] c/d; S_best = S_low OR S_high |

Known limits: non-contemporaneous historical Kepler-band amplitudes (never a ZTF-g threshold, N7); MNAR join (frequency-recovery is Mo-join-conditioned, N9); aliased dominant for 40 stars (F02); "dominant" = largest amplitude, not p-mode (F04); high-pass recovery cell near-empty (F03); sub-hour signal established in the Kepler aperture, not in the ZTF source — essentially every cone holds > 1 ZTF object (N28).

## 5. Sampling and weights

| Item | Value |
|---|---|
| Positives, dSct=2 | Census; `sampling_weight` = 1.0 |
| Negatives | SRSWOR, seed 20260828; `sampling_weight` = 7292/2314 exactly (never from rounded values) |
| Where weights act | Cancel within class → P3 plain Wilson on 2,314 (no FPC, conservative); PPV = FPC-rescaled survey bootstrap (B = 2000, negatives resampled, positives fixed, deviations × sqrt(1 − 2314/7292)); ESS-Wilson only for other weighted descriptives (labeled approximate) |
| Balance (pool vs sample, 25/50/75) | g 13.388/14.066/15.294 vs 13.385/14.049/15.214; Teff 6,536/6,671/7,193.8 vs 6,536/6,675/7,207.4 K; RA 286.372/292.95/297.682 vs 286.164/293.098/297.713; Dec 39.453/44.118/49.058 vs 39.473/44.099/49.043 |

## 6. Strata and prespecified subsets

| Stratum / subset | Definition | n |
|---|---|---|
| Roster `stratum` (precedence: class_0, class_2, subhour, amp_unknown, amplitude) | class_0 2,314; class_2 76; subhour 290; amp_unknown 154; amp_lt1 65; amp_ladder_1…6 17/14/13/22/11/8; amp_gt10 16 | 3,000 |
| Amplitude surface bins | half-open edges {0.5, 1, 2, 5, 10, 20, 50} mmag, top [50, ∞), bin −1 = amp_unknown; binned on `amp_mmag` directly (never on `stratum`, F25) | 610 |
| Period bins | {100 s, 200 s, 500 s, 1000 s, 2000 s, 0.05 d, 0.2 d, 1 d, 10 d, 100 d} | 456 |
| Median-exposures-per-night bins | {1, 1.5, 2, 3, 5}, top [5, ∞); expected near-degenerate at 1–2 | — |
| Near-saturation | spec text: g ≤ 14.0 flagged / g > 14.0 safe (PRINCIPAL robustness lens); code: `gmag < 14.0` flagged; 3 stars at g = 14.000 (all negatives) flagged safe | flagged 1,557 (1,089 / 403 / 65 by dSct 0/1/2); safe 1,443 |
| Crowding-clean | sep < 1.0″ AND ≤ 3 objects in cone | 275 (228 / 44 / 3) |
| Confirmed super-Nyquist mode ("sub-hour" — rename, F03) | ≥ 1 table1 row, C = 0 | 290 |
| Mo-joined / unjoined | table2 join | 456 / 154 |
| Pass regime (descriptive split, F03) | dominant < 4 / 4–24 / ≥ 24 c/d | 117 / 329 / 10 (dSct=1) |
| Cells below 5 stars | counts only, no interval | — |

## 7. Estimands this dataset feeds (names binding, METRICS_SPEC)

| Estimand | Denominator | Rule / pass | Interval | Status |
|---|---|---|---|---|
| Detection completeness | 610 eligible_roster (missing = non-detection); n_usable | rule 1 / best | Wilson 95 % | PRIMARY-P1; usable = SECONDARY |
| Frequency-recovery completeness | Mo-joined, S_best = 1 (≤ 456) | rule 1 + `best_candidate_matches_dominant` = direct | Wilson; beside any-mode chance rate (100 permutations, seed 20260829) | PRIMARY-P2 |
| Negative-class trigger rate | 2,314 dSct=0 | rule 1 / best | plain Wilson | PRIMARY-P3 |
| Correct-frequency fraction among detected positives | n_det | — | Wilson | DESCRIPTIVE-PRESPEC |
| Frame-specific label PPV | weighted frame, dSct=2 excluded | — | survey bootstrap FPC | DESCRIPTIVE-PRESPEC |
| Census vs L-S 2 × 2, union, incremental | positives with both usable | — | Wilson; McNemar secondary | DESCRIPTIVE-PRESPEC |
| Within / outside solar-diurnal band partition of the P3 numerator | 2,314 | bands ∪_{k=1..3} [k − 0.020, k + 0.020] c/d | none | DESCRIPTIVE-POST-LAUNCH (2026-08-31) |

## 8. Known limitations (panel A-class items)

| ID | Limitation |
|---|---|
| F01 | P1 counts confirmed triggers of any origin on positives, incl. solar-diurnal systematics (pilot: 30/33 negative passes in-band) → P1 reads with P3 as its floor and with P2 |
| F02 | Truth frequencies are Kepler sub-Nyquist table2 values; 40 / 290 super-Nyquist positives have an aliased dominant; `fR` never scored |
| F03 | "Sub-hour" set is scored on low-pass dominants (2.0/15.5/22.4 c/d); ZTF high-pass regime untested by P2 (10/456 in [24, 24.47) c/d) |
| F04 | 117/456 dominants < 4 c/d (89 < 2.5): g-mode / rotational, not p-mode; 49 of them super-Nyquist-flagged |
| F14 | Frozen veto is sidereal-only (k × 1.00274 c/d ± 1.5/T); solar-family modulation passes the two-band rule (future work) |
| F16 | One field with atypical ZTF coverage → responses are Kepler-field statements |
| F17 | 2,235 / 2,901 stars merge 4–6 ZTF oids with no inter-oid zero-point alignment → low-pass / census power |
| F18 | High pass keeps only multi-exposure-night contrasts (~16 % of epochs); sub-hour regime floor-limited by high-pass a95 |
| F19 | `ambiguous` crossmatch lens degenerate (100 %); crowding-clean = 275 (44 positives) |
| F20 | L-S-only cell of the 2 × 2 can hold systematic-only triggers → qualified by match class |
| F21 | Chance-match rate is any-mode (median 132 modes/star), not confirmed-conditioned; conservative vs dominant-only P2 |
| F22 | Near-saturation boundary: code `< 14.0` vs text `≤ 14.0`; 3 negatives at g = 14.000 classed safe |
| F23 | Kepler LC \|sinc\| 0.68–0.89 at dominant periods; Mo amplitude sinc-correction status ⟨TBD: W3⟩ |
| F24 | C = 0 meaning ⟨TBD: quote Mo+2026 column definition⟩ |
| F25 | `stratum` uses sub-hour precedence (amp_gt10 = 16 vs 48 stars > 10 mmag); never quote `stratum` as amplitude counts |
| F26 | "Usable" = both passes; low-pass-only-usable stars leave the usable denominator (count reported) |
| F27 | Wilson assumes star independence under a common-mode systematic; P3 by sky cell descriptive |
| F29 | Timing pilot = 150 lowest KICs (`--limit 150`), a sky corner; diurnal band half-width fixed after that peek |
| F35 | Turn-on = a95 floor; P3 floor = the systematic → frame as calibration, not discovery |
| plan | Sub-hour signal is in the Kepler aperture, not automatically in the ZTF source (blends); dSct=0 ≠ constant; amplitudes historical, non-contemporaneous |

## 9. What this dataset can and cannot support

| CAN | CANNOT |
|---|---|
| Detection completeness of the frozen rule on 610 externally labeled δ Scuti at KIC g ≥ 13.2 (eligible and usable denominators) | Any FPR, "purity", or upper bound on false positives (N5, N6) |
| Mo-join-conditioned frequency-recovery completeness on ≤ 456 stars, with an accidental-match rate beside it | Completeness "for all 610" from the 456-star curve; silent 610 ↔ 456 ↔ n_usable swaps (N9) |
| Negative-class trigger rate on 2,314 non-δ-Scuti stars, plus a descriptive within/outside diurnal-band partition | A "corrected" / "de-aliased" P3; instrumental-vs-astrophysical attribution of any band member (N14) |
| Frame-specific label PPV at the design prevalence | PPV at any other prevalence |
| Turn-on curve in historical Kepler-band dominant amplitude (incl. amp_unknown) | A ZTF-g amplitude threshold or detection limit (N7) |
| Census vs L-S 2 × 2 with both discordant cells and union yields | "Complementarity proven by McNemar" (N21) |
| Kepler-field, g ≥ 13.2 statements; descriptive strata by magnitude / Teff / merged-oid / crowding / sky cell | "δ Scuti completeness of ZTF"; extrapolation past the cut or the field (N19); causal cadence / crowding claims (N8) |
| Counts of confirmed super-Nyquist-mode stars detected (Kepler-aperture caveat) | Sub-hour detection claims in the ZTF source; high-pass frequency recovery beyond counts (F03) |
| Statements about ≥ 5 d⁻¹ pulsation labels | Statements about < 5 d⁻¹ variability of the negative class (Murphy classified 5–43.9 d⁻¹ only) |
