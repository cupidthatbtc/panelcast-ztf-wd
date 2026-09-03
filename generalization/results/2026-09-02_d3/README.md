# D3 — ZTF × Kepler δ Scuti (Murphy+2019 labels; Mo+2026 frequencies), full run 2026-09-02

Frozen pipeline (tag frozen-2026-08-01), attested laptop run, 2,901/2,901 crossmatched
stars scored, 0 failures. Metrics: Mac re-run of the compliance-patched program,
certified against the laptop's frozen run (GUARD PASS: 13 science outputs
identical after newline normalisation). `metrics/` is authoritative;
`metrics_laptop_prefix/` is the laptop's pre-fix bundle, archived uninterpreted.

## Prespecified endpoints (rule 1 = confirmed, best pass, Wilson 95 %)

| endpoint | frame | n | k | p | 95 % CI |
|---|---|---|---|---|---|
| P1 detection completeness | dSct=1 eligible roster | 610 | 327 | 0.536 | 0.496–0.575 |
| P1 (usable light curve) | dSct=1 usable | 585 | 327 | 0.559 | 0.518–0.599 |
| P2 frequency recovery (dominant direct) | Mo-joined, S_best=1, usable | 441 | 72 | 0.163 | 0.132–0.201 |
| correct-frequency fraction among detected | detected ∩ P2 frame | 238 | 72 | 0.303 | 0.248–0.364 |
| P3 negative-class trigger rate | dSct=0 (uniform weight) | 2,314 | 963 | 0.416 | 0.396–0.436 |
| P3, census rule | dSct=0 | 2,314 | 65 | 0.028 | 0.022–0.036 |
| P3, either rule | dSct=0 | 2,314 | 993 | 0.429 | 0.409–0.449 |
| census completeness | dSct=1 eligible | 610 | 25 | 0.041 | 0.028–0.060 |
| union (either) completeness | dSct=1 usable | 585 | 334 | 0.571 | 0.530–0.610 |
| frame-specific label PPV | triggered roster members | 1,290 | — | 0.097 | 0.094–0.101 (survey bootstrap) |

Contingency (585 usable positives): census∧LS 18, census-only 7, LS-only 309,
neither 251; incremental census 0.012 [0.006, 0.024]; incremental LS 0.528
[0.488, 0.568]; McNemar exact p = 9e-82 (secondary).
Chance direct-match (prespecified, any-mode, 100 permutations): mean 0.0037, p95 0.0091.

## Descriptive, post-launch (ruled 2026-08-31 / 2026-09-01; no intervals; `descriptive_postlaunch/`)

| table | key numbers |
|---|---|
| solar-diurnal partition of P3 numerator | within ∪[k±0.020] c/d: 121/963 (0.052 of negatives); outside: 842/963 (0.364) |
| P3 by pass | low 920/2,314 = 0.398; high 85/2,314 = 0.037 |
| P3 by merged-oid count | ≤1: 0/46; 2: 107/438 = 0.244; 3–4: 670/1,439 = 0.466; ≥5: 186/391 = 0.476 |
| P3 by magnitude / Teff | g≤14 0.443, g>14 0.392; Teff quartiles 0.405 / 0.394 / 0.431 / 0.467 |
| P3 by sky cell (4×4) | 0.211–0.611 (RAq1 highest) |
| confirmed-positive match partition (327) | direct 72, unmatched 164 (38 with truth in top-15), unscored/unjoined 89, harmonic 1, window_alias 1 |
| P2 by dominant-frequency regime | <4 c/d 10/115 = 0.087; 4–24 62/318 = 0.195; ≥24 0/8 |
| fR rescoring, 40 aliased-dominant targets | 20 confirmed → 3 direct on fR; 0 Nyquist-reflection matches |
| dominant-only confirmed-conditioned chance (10,000 derangements) | mean 0.0003, q95 0.0042 |
| a95 medians (mmag) | high zg/zr 1.03/1.09 (neg), 1.15/1.15 (pos); low 2.62/2.87 (neg), 2.98/3.15 (pos) |
| coverage D3 vs 928 pool (medians) | zg epochs 754 vs 437.5; nights 640 vs 371.5; W_g 119 vs 58 |

Compliance outputs (METRICS_SPEC-mandated, implemented post-launch): `metrics/attrition.csv`
(555 cells; roster 3,000 → fetched 3,000 → crossmatched 2,955 → QC 2,901 →
both passes 2,901), `metrics/d3_mo_join_covariates.csv` (456 joined / 154 unjoined),
`metrics/attrition_summary.csv` (former scalar audit).

Reading discipline: every row above is either prespecified (interval shown) or
descriptive (no interval). The frozen veto covers the sidereal family only; the
ruled solar-diurnal bands hold 12.6 % of the P3 numerator — the remainder sits in
broad 1−δ / 2−δ alias wings and a cluster near 0.034 c/d (see
`metrics/fp_frequency_distribution.csv` and `descriptive_postlaunch/d1_d3_confirmed_frequency_histogram.csv`).
No band member is reclassified; no "corrected" P3 exists.

## Errata

- 2026-09-03 (G5 independent re-derivation, `generalization/reviews/G5/verifier_d3.md`): the
  development-pool medians in the coverage line were transcribed as integers (437, 372); the
  frozen `descriptive_postlaunch/d3_vs_pool_coverage.csv` gives 437.5 and 371.5 (linear medians
  of 928 windows). The line above now quotes the file values. Every other headline and
  descriptive number reproduced exactly. This README's entry in `SHA256SUMS` was recomputed for
  this edit; no other file changed.
