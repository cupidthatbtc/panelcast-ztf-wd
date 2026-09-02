# D3 confirmed-positive match partition (descriptive, post-launch)

Post-launch descriptive analysis: `d3_confirmed_positive_match_partition.csv` partitions the frozen rule-1 best-pass confirmed-positive numerator by its already-emitted dominant-match class and top-15 any-mode indicator over the unchanged 610-star P1 denominator, carries no interval or endpoint status, and does not identify or remove wrong-reason triggers.

The admitted solar-diurnal rule is explicitly a partition of the negative-class P3 numerator only. Applying it to confirmed positives exceeds the 2026-08-31 admission. No positive-class `within_solar_diurnal_band` column is authorized here.

Ruling: generalization/reviews/G5prep/sol_round2.md, item 3 (F01, ADMIT-DESCRIPTIVE; positive-class diurnal extension REFUSED).
Fields on every row: analysis_status=postlaunch_descriptive, prespecified=false, interval=none.

Frame: all eligible dsct_flag1 positives with best_status==confirmed under rule 1 and best pass, crossed by the frozen best_candidate_matches_dominant class (direct, harmonic, window_alias, ambiguous, unmatched, unscored) and the frozen any_top_peak_matches_any_mode indicator; all 12 cells emitted; n_positive=610; unjoined confirmed positives remain `unscored`, never dropped. share_of_confirmed_positives is blank when no positive is confirmed.
