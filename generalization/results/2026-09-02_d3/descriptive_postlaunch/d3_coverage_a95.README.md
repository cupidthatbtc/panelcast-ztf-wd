# D3 vs pool coverage and per-pass a95 by class (descriptive, post-launch)

Post-launch descriptive coverage tables compare the crossmatched Kepler-field frame with the fixed 928-window development pool and summarize per-pass, per-band a95 values by D3 class; the quantiles describe the realized frames without intervals or ZTF-wide transfer claims.

Admission: generalization/reviews/G5prep/sol_round2.md, item 7 (F16/F18, ADMIT-DESCRIPTIVE).
Coverage frames: D3_crossmatched = all 2,901 D3 census-panel rows;
development_pool = all 928 census_full_catalog.csv rows;
wg_contrasts = zg_n_exp - zg_n_nights (asserted nonnegative); linear
quantiles; the frames are never pooled. a95 values are read directly
from passes[pass][band + "_a95_mmag"] of the per-star JSONs, crossed
class x pass x band with no pooling across bands; n_missing =
n_roster - n_finite. No interval, endpoint, exclusion,
reclassification, or ZTF-wide transfer claim.
