# SUMMARY — literature review for the astro-wd selection-function study (AAS 249 / short paper)

Files: `annotated_bibliography.md` (83 entries, paper format), `references.bib` (83 Crossref-verified DOIs; 54 arXiv IDs title-checked; bibcodes flagged ADS-verified vs derived). Searched 2026-09-01.

## The 10 papers a referee will expect us to cite

| # | Paper | Why it is unavoidable |
|---|---|---|
| 1 | **Sokolovsky+2017** MNRAS 464, 274 | The index-comparison benchmark (18 indices, 7 labeled ground-based sets, C/P/F1 vs threshold and vs N); explicitly *excludes* period search — the seam we measure. |
| 2 | **Guidry+2021** ApJ 912, 125 | Gaia+ZTF scatter census on ~12,100 WDs; top-1% purity demonstrated (33/33 variable, 19 new ZZ Cetis), completeness never measured. Closest ZTF-WD analogue of our census. |
| 3 | **Coughlin+2021** MNRAS 505, 2954 (with **van Roestel+2021** AJ 161, 267) | ZTF DR2 periodicity metrics (CE/LS/AOV), 20-feature table, and the empirical diurnal (0.5, 1 d), sidereal and lunar alias pile-ups in ZTF; SCoPe's IQR pre-screen is a census-then-periodogram pipeline. |
| 4 | **Bellm+2019a,b** PASP 131, 018002 / 068003 and **Masci+2019** PASP 131, 018003 | Survey, 3-night public cadence (mostly one exposure per band per night), data products and QC flags — the origin of W_g and of every frozen QC cut. |
| 5 | **VanderPlas 2018** ApJS 236, 16 (+ **Baluev 2008** MNRAS 385, 1279) | LS theory, window function, aliasing, FAP; the Baluev bound is biased under strong aliasing (Süveges+2015) — supports reporting the alias decomposition next to FAP-based trigger rates. |
| 6 | **Dawson & Fabrycky 2010** ApJ 722, 937 | Solar-day vs sidereal-day alias families as distinct generators — the basis for vetoing the sidereal comb and describing the 1/2/3 c/d solar-diurnal comb. |
| 7 | **Murphy+2019** MNRAS 485, 2380 | D3 labels: 15,229 Kepler A/F stars, manual/SNR-based δ Sct classification, `dSct` = 0/1/2 (2 = other variability), **no Kepler-magnitude cut** (our g ≥ 13.2 is our own domain restriction), 18% dominant super-Nyquist. |
| 8 | **Mo+2026** A&A 710, A245 (+ **Bowman+2016** MNRAS 460, 1970) | D3 frequency/amplitude axis (1,838 stars = Bowman 983 ∪ Murphy 1,988; 259,883 SNR > 8 frequencies; 15,265 confirmed SNFs). Bowman's table has no amplitudes; 61% of δ Sct show amplitude modulation (non-contemporaneity caveat). |
| 9 | **Romero+2022** MNRAS 511, 1574 and **Romero+2025** ApJ 984, 112 | D2 truth: FAP = 1/1000 by reshuffling, per-star detection limits, 20-s flags, PDCSAP with CROWDSAP dilution correction stated explicitly (2025), three NOV retractions. |
| 10 | **Hermes+2017** ApJS 232, 23 | DAV mode line-width dichotomy and amplitude/phase non-stationarity — justifies D2's phase, amplitude and dropout sensitivity axes and the "conditional recovery of a stationary model" framing. |

Also expected: **Christiansen+2013/2020** (injection-recovery of a frozen pipeline), **Burke+2015** (window function vs detection efficiency), **VanderPlas & Ivezić 2015** (periodic injections into sparse multi-band cadence), **Chen+2020** / **Healy+2024** (what "ZTF completeness" currently means), **Oelkers+2018** (explicit sidereal/lunar/annual alias policy, 0.97–1.04 d exclusion), **Gentile Fusillo+2021**, and the interval citations (Wilson 1927; Clopper & Pearson 1934; Brown, Cai & DasGupta 2001; McNemar 1947; Efron 1979).

## Closest prior comparison

**Sokolovsky+2017** is the nearest single comparator: same object (a scatter census as first-stage detector), same reporting idiom, same "no rule dominates — combine" conclusion; but it never included a periodogram rule, its truth lists came from the same data, and its light-curve sets are not a public benchmark (use "test light curves not distributed", not "data not public"). In ZTF specifically, **Guidry+2021** (census purity on WDs, no completeness) and **van Roestel+2021 / Coughlin+2021** (IQR pre-screen + CE/LS/AOV, aliases documented, stage-wise completeness never reported) bracket our design. Methodologically, **Christiansen+2013, 2020** and **VanderPlas & Ivezić 2015** are the injection-recovery precedents; none injects published multi-mode DAV models into real ZTF windows.

## The gap this study fills

No published work measures, on one externally labeled sample and with intervals, the *stage-wise* response of a frozen ZTF variance census and a frozen two-band Lomb–Scargle rule — census-only, LS-only and union completeness — nor reports class-specific ZTF completeness against Kepler δ Sct labels with a frozen, weighted negative class, nor the conditional injection-recovery of TESS-derived DAV mode models in real ZTF windows stratified by surviving support (W_g), nor a frozen-band decomposition of a negative-class trigger rate into solar-diurnal and non-diurnal components. The literature predicts complementarity (Sokolovsky; Graham+2013a; Süveges+2015), cadence-conditional response (Burke; Süveges), and diurnal pile-ups (Coughlin; Oelkers); it has not measured them together with prespecified estimands.

## [UNVERIFIED] items (content, not bibliography)

1. Mo+2026: whether table2 amplitudes are corrected for Kepler LC integration (sinc) attenuation — not found in extracted text; W3 check.
2. 66 derived bibcodes (from verified journal/vol/page) — spot-check on ADS; PASP/JATIS article-number letters are the only non-trivial cases.
3. Sokolovsky+2017 "data not public" wording — soften as above.
4. Vincent+2020 new-ZZ-Ceti count — not extracted; annotation avoids a number.
5. Chen+2020 one-day-alias policy — not extracted; do not cite it for alias handling.
