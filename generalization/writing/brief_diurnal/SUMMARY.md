# SUMMARY — sentences for the AAS 249 abstract/poster (diurnal-family paragraph)

Source: `BRIEF.md` in this directory. Each sentence below is written so it can be lifted verbatim; citation keys are in `references.bib`.

## Five sentences we can defensibly write

1. Single-site, night-only sampling gives a ground-based survey a spectral window with a strong peak at 1 cycle/day and its harmonics, so any low-frequency power in a light curve is partially aliased to f ± n(1 c/d); the 1-day member is in fact a solar/sidereal doublet at 1.0000 and 1.0027 c/d whose members carry ±m/yr sidebands (VanderPlas 2018, §4.2.1, §7.2, Eq. 45; Dawson & Fabrycky 2010, §2.1–2.2).

2. Published ZTF, ATLAS, ASAS-SN and CRTS period catalogues treat narrow excesses of periods at 1, 1/2, 1/3, 2 d (and lunar multiples) as sampling artefacts and remove or down-weight them with bands 0.02–0.05 c/d wide centred on integer c/d, none of which distinguishes the solar-day from the sidereal-day member (Coughlin et al. 2021, §4: 0.95–1.05, 1.95–2.05, 2.95–3.05 c/d; Chen et al. 2020, §3: |P − 1| < 0.03 d; Drake et al. 2014, §4; Jayasinghe et al. 2020, §3.5; Christy et al. 2023; Heinze et al. 2018, Figs 24/26; McLennan et al. 2026, §3.2, preprint).

3. The frozen pipeline's frequency-locus veto targets only k·f_sid = k × 1.00274 c/d within ±1.5/T ≈ ±5.6 × 10⁻⁴ c/d, which for T ≈ 2700 d is about one-fifth of the solar–sidereal separation 1/365.25 d = 0.00274 c/d, so members of the solar-day family are outside that veto by construction and are caught only if the local spectral-window power within ±1.5/T exceeds 0.1 (scripts/lomb_scargle_common.py, `is_window_alias`, `is_alias_of_stronger`; scripts/run_lomb_scargle.py).

4. The pilot's pile-up of confirmed negative-class triggers at 0.994–1.006 and 2.000–2.015 c/d is the period-histogram signature that these catalogue papers attribute to the diurnal alias family (Coughlin et al. 2021, Fig. 11; Christy et al. 2023, "discrete spike near P ~ 1 day"; Heinze et al. 2018, Figs 24/26), and the Kepler δ Sct label cannot speak to it because Murphy et al. (2019, §3) computed Fourier transforms only above 5 d⁻¹ and classified on 5–43.9 d⁻¹.

5. A narrow excess at integer c/d is a population-level systematic signature, but individual members can be genuine variables — the same papers report "a few percent" of true variables inside their alias bands (Drake et al. 2014, §4; Coughlin et al. 2021, §4; Kramer et al. 2023: 1–2%), about 40% of Kepler A stars show rotational modulation whose periods span ~1 d (Balona 2013), and essentially every D3 star has a second ZTF object within 10″ (crossmatch_freeze/README.md; ZTF PSF ~2″, Bellm et al. 2019a) — which is why the decomposition is reported descriptively and no band member is reclassified (sol_diurnal.md disclosure sentence).

## Three sentences we must NOT write

1. "The triggers at 1, 2 and 3 c/d are instrumental false positives." — No per-star test in the pipeline or the literature separates an instrumental member from an aliased real slow variable (Chen et al. 2020 mechanism; Heinze et al. 2018 "aliased long-period variables") or from a genuine ~1-d rotator/blend; the admitted decomposition explicitly "does not establish that an individual band member is instrumental rather than astrophysical".

2. "After removing the diurnal family the negative-class trigger rate is X%." — The outside-band component is an unweighted arithmetic partition of the frozen rule-1 P3 numerator, not a corrected or de-aliased P3, carries no interval, and was not prespecified (sol_diurnal.md; METRICS_SPEC.md freeze rule; Amendment 4).

3. "Roughly N% of ZTF false periods are known to be 1-day aliases, consistent with our ~90%." — No published ZTF/ATLAS/ASAS-SN/CRTS study reports the fraction of detections on labelled non-variables that falls in the family; the available numbers (VanderPlas 2018: ~36% of simulated periodic objects mis-assigned to f0 ± n c/d; Drake et al. 2014: ~11% of periodic candidates removed as sidereal/lunar aliases; Kramer et al. 2023: 35% wrong ZTF asteroid periods, of which masks fix ~1 point) measure period misassignment or candidate attrition, not a negative-class trigger rate, and cannot be quoted as agreement.

## [UNVERIFIED] items

- Balona (2013) rotation-frequency range "0.1 < f < 5 d⁻¹": from a fetched summary, not seen in the abstract; only the "about 875 (40 per cent)" statement is verified.
- DOIs for Coughlin et al. (2021), Christy et al. (2023) and Kramer et al. (2023), and Kramer's article number: not present in the preprint texts; volume/page confirmed from publisher listings only.
- Christy et al. (2023) end page 5287: not confirmed.
- McLennan, Farihi & Parsons (2026): arXiv preprint, not peer-reviewed at time of writing.
- Bellm et al. (2019b) hour-angle coverage "~±75°": read from the Fig. 7 axis labels in the extracted text, not from a sentence.
- Inference, not literature: that the 1.0000 (solar) member dominates the ZTF Kepler-field window and that the pilot loci 0.994/1.006 c/d are the m = ±2 yearly sidebands (1 ∓ 2/365.25 = 0.9945/1.0055 c/d); testable on the D3 timestamps with the pipeline's own `window_strength` and on `fp_frequency_distribution.csv`, not computed here.
- PTF (Sesar et al.) and any ZTF-specific solar-day *instrumental* systematic: not verified; no source found in this search.
