# D3 frequency audits (descriptive, post-launch)

Post-launch descriptive frequency audits compare the normalized best-frequency distributions of published D1 confirmations and D3 negative-class confirmations and report yearly-alias and Kepler-Nyquist-reflection predicates beside the unchanged frozen taxonomy; the added relations never reclassify a frozen match or alter P2 or P3.

Ruling: generalization/reviews/G5prep/sol_round2.md, item 9 (F32/F33, ADMIT-DESCRIPTIVE).
Fields on every row: analysis_status=postlaunch_descriptive, prespecified=false, interval=none.

- d1_d3_confirmed_frequency_histogram.csv / d1_d3_confirmed_frequency_histogram.png / d1_d3_confirmed_frequency_histogram.meta.json: D1 = blind_status=="confirmed" (928-star published catalog); D3 = dsct_flag0 and best_status=="confirmed"; fixed edges, left-closed/right-open, 1440 included in the overflow bin; each dataset normalised separately by its confirmed count; density_per_day = share/bin_width for finite bins.
- d3_extra_frequency_relations.csv: one row per per_star.csv row; delta_year = 1/365.25 = 0.0027378507871321013 d^-1, f_Nyq = 24.46848 d^-1, tol = 1.5/baseline_days; yearly_alias: |f_candidate - |f_truth +/- delta_year|| <= tol; kepler_nyquist_reflection: f_ref = 2 f_Nyq - f_truth, f_ref > 0 and |f_candidate - f_ref| <= tol; evaluated for the dominant frequency and, separately, every table-2 mode; independent booleans (harmonics and sidereal aliases not folded in); blank wherever the corresponding frozen match column is `unscored`. These columns are never added to the frozen per_star.csv.
