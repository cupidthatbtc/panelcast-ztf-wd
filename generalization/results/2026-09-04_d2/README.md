# D2 — TESS DAV modes (Romero 2022/2025) injected into real ZTF windows, full run 2026-09-03

Frozen pipeline (tag frozen-2026-08-01), attested laptop run on generation gen2
(`129740d1809c…`, Amendment 4 W_g strata), 3,089/3,089 shards scored, 0 failures
(309 nominal arm B, 309 nominal arm A, 824 ladder, 206 phase, 206 ampscale, 76
dropout, 33 cadence_alt, 20 redilution, 106 paired controls, 1,000 Gaussian nulls).
Metrics: Mac re-run of the compliance-patched program, certified against the
laptop's frozen run (GUARD PASS: 17 science outputs identical after newline
normalisation; `per_star.csv` identical in every decision, match and count
column, with two CSV-parsed TRUTH columns — `primary_freq`, `truth_period_days` —
differing by one ulp on 76 rows, the documented laptop float-parse artifact of
`generalization/env/CROSS_PLATFORM_REPLAY.md`; max relative difference
2.1 × 10⁻¹⁶, disclosed exception `--allow-known-platform-ulp`). `metrics/` is
authoritative; `metrics_laptop_prefix/` is the laptop's pre-fix bundle, archived
uninterpreted.

## Prespecified endpoints (rule 1 = confirmed, best pass)

| endpoint | frame | n | estimate | 95 % interval | status |
|---|---|---|---|---|---|
| **P5 FPR_Gaussian** (sole confirmatory decision) | 1,000 Gaussian nulls, arm-A floor | 1,000 | 19 confirmed = **0.019** | one-sided CP upper **0.0278** | acceptance (U95 ≤ 0.005) **FAILS** |
| P4 conditional recovery, eligible | nominal arm B, 103 targets, 3 strata each | 103 | 0.217 | 0.172–0.262 (target-cluster bootstrap) | PRIMARY |
| P4 conditional recovery, usable | same (0 targets with zero usable strata) | 103 | 0.217 | 0.172–0.262 | PRIMARY |
| P4 trigger (detection only) | nominal arm B | 103 | 0.557 | 0.518–0.602 | secondary |
| arm A recovery / trigger (Gaussian floor) | nominal arm A | 103 | 0.346 / 0.440 | 0.298–0.395 / 0.392–0.492 | descriptive |
| paired controls, detection D | 309 pairs, 103 targets, 106 windows | 309 | B 0.557 vs C 0.417; B−C 0.139 | 0.091–0.191 | secondary |
| paired controls, strict recovery R | same | 309 | B 0.217 vs C 0.000; P(B=1, C=0) 0.217 | 0.172–0.262 | secondary |
| native trigger rate of control windows | 106 uninjected windows | 106 | 0.443 | 0.352–0.538 (Wilson) | descriptive |
| chance match (10,000 derangements) | nominal arm B, target-equal | — | recovery 0.000; any-mode 0.000 | p95 0.000 | descriptive |

Paired-control 2 × 2 (D): both 118, B-only 54, C-only 11, neither 126 (union 183/309).
(R): both 0, B-only 67, C-only 0, neither 242.

**Reading the P5 outcome.** The frozen rule "confirms" 1.9 % of pure-Gaussian
windows (19/1,000; CP upper 2.8 %), so the pre-registered acceptance criterion
for the Gaussian false-alarm rate (upper bound ≤ 0.5 %) is not met. No endpoint
is swapped or re-denominated; the D2 recovery estimates stand as pre-registered
with this failure beside them, and the contingency branch of the writing outline
(`generalization/writing/outline/CONTINGENCIES.md`, P5-fail) applies.

## Scenario contrasts (recovery, eligible denominator; paired common-draw target bootstrap)

| scenario | n targets | p scenario | p nominal K1 | diff | 95 % |
|---|---|---|---|---|---|
| ladder g1r1 / g1r2 / g1r3 | 103 | 0.068 / 0.087 / 0.097 | 0.107 | −0.039 / −0.019 / −0.010 | [−0.078, −0.010] / [−0.049, 0] / [−0.029, 0] |
| ladder g2r1 / g2r3 | 103 | 0.097 / 0.126 | 0.107 | −0.010 / +0.019 | [−0.029, 0] / [0, 0.049] |
| ladder g3r1 / g3r2 / g3r3 | 103 | 0.146 each | 0.107 | +0.039 | [0.010, 0.078] |
| ampscale 0.7 / 1.3 | 103 | 0.049 / 0.146 | 0.107 | −0.058 / +0.039 | [−0.107, −0.019] / [0.010, 0.078] |
| phase 1 / 2 | 103 | 0.117 / 0.165 | 0.107 | +0.010 / +0.058 | [−0.019, 0.039] / [0.019, 0.107] |
| dropout | 76 | 0.039 | 0.092 | −0.053 | [−0.105, −0.012] |
| cadence_alt | 33 | 0.152 | 0.091 | +0.061 | [0, 0.152] |
| redilution | 20 | 0.000 | 0.350 | −0.350 | [−0.571, −0.143] |

Recovery surface (`metrics/surfaces/recovery_wg_amplitude.csv`, target-level,
frozen edges W_g {15, 41, 84, 217}, A {0.5, 2, 5, 10, 30} ppt): recovery rises
with W_g and amplitude — W_g ≥ 217: 0.23 / 0.38 / 0.59 / 0.89 for A 2–5 / 5–10 /
10–30 / ≥ 30 ppt (13 / 32 / 44 / 9 targets); W_g < 15: 0.00 / 0.00 / 0.11 / 0.22
(11 / 31 / 45 / 9); K0 / K1 / K2 target means 0.07 / 0.11 / 0.48 (figure F5).

## Descriptive, post-launch (ruled item 5; no intervals; `descriptive_postlaunch/`)

| table | key numbers |
|---|---|
| nominal B by K × template status | K2 confirmed-template windows trigger 62/62 but recover 22/62 (0.35); K2 not-detected-template windows recover 10/17 (0.59); K1 confirmed windows recover 3/41 (0.07) |
| control reuse | 106 unique windows over 309 assignments (36 used once, max 12) |
| arm A/B pairs | 309 usable (tic, K) pairs; no aggregate contrast |

Figures (`figures/`, code `scripts/generalization/figures/d2_poster_figures.py`,
every drawn number in `figures.manifest.json`): F5 recovery surface + P4 side
panel, F6 scenario contrasts, F7 nulls & paired controls.

Reading discipline: every row is either prespecified (interval shown) or
descriptive (no interval); D2 row-level intervals are suppressed everywhere
(Amendment 4); no real-sky completeness is read from D2; the ladder/phase/
ampscale/dropout/cadence/redilution rows are sensitivity, never pooled with the
nominal estimate.
