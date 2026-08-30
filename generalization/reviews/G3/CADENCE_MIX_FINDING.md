# G3 finding (post round-1): mixed 20-s/120-s sector solutions vs the frozen cadence rule

Source: SPOC verification v3 (all 103 targets, `v3_all103_verification_report.json`).
The frozen plan rule sets `cadence_s = 20 iff any 'f' sector` (an effective
integration time for the sinc de-integration). v3 chose, per target, the SPOC
product cadence covering the most PUBLISHED sectors; it switched 33 targets
from roster 20 s to 120 s products — every switch in that direction — because
those solutions combine 20-s ('f') AND 120-s sectors (a stitched multi-sector
fit; the published amplitude is therefore a sector-mixed integration).

Roster composition (sector kind x roster cadence): {('mixed', 20): 31, ('pure_120s', 20): 2, ('pure_120s', 120): 54, ('pure_20s', 20): 16}

Mixed-sector targets: 31 (128 modes). Modes with P < 300 s,
where sinc(120 s)/sinc(20 s) < 0.76 and the assumed cadence changes the
de-integrated amplitude by > 30%: 22 modes on 11 targets
(3 of them would be REJECTED under the 120-s rule).

| tic | roster cad | published sectors | coverage by cadence {20:n,120:n} | P [s] | A [ppt] | sinc120/sinc20 |
|---|---|---|---|---|---|---|
| 7675859 | 20 | 25,26,f40,f52-f54 | {'20': 4, '120': 6} | 254.49 | 4.14 | 0.679 |
| 33717565 | 20 | 27-29,32,35-36,39,f61-f63,f65-f68 | {'20': 7, '120': 14} | 243.02 | 2.04 | 0.652 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 126.84 | 1.80 | 0.059 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 127.03 | 0.48 | 0.061 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 153.26 | 0.41 | 0.264 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 199.52 | 0.59 | 0.511 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 200.08 | 4.42 | 0.513 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 200.66 | 0.88 | 0.516 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 206.70 | 0.39 | 0.539 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 261.61 | 0.47 | 0.695 |
| 55650407 | 20 | 11-13,f27-f39,f61-f64 | {'20': 17, '120': 20} | 262.46 | 7.19 | 0.697 |
| 63281499 | 20 | 01,f28,f68 | {'20': 2, '120': 3} | 269.13 | 2.31 | 0.710 |
| 141179495 | 20 | 22,f49 | {'20': 1, '120': 2} | 253.86 | 4.46 | 0.678 |
| 141976247 | 20 | 1-8,10-13,27-34,f35-f37 | {'20': 3, '120': 23} | 261.72 | 0.86 | 0.695 |
| 192937035 | 20 | 20,47,f60 | {'20': 1, '120': 3} | 298.27 | 5.25 | 0.760 |
| 238815671 | 20 | 01,f27-28 | {'20': 2, '120': 3} | 257.59 | 9.22 | 0.686 |
| 238815671 | 20 | 01,f27-28 | {'20': 2, '120': 3} | 287.29 | 6.86 | 0.743 |
| 343296348 | 20 | 12-13,f39,f66 | {'20': 2, '120': 4} | 287.26 | 7.11 | 0.743 |
| 343296348 | 20 | 12-13,f39,f66 | {'20': 2, '120': 4} | 288.27 | 10.81 | 0.744 |
| 453210132 | 20 | 34,f44-f46 | {'20': 3, '120': 4} | 200.31 | 6.93 | 0.514 |
| 900762564 | 20 | f40-41,47,f53,f60 | {'20': 4, '120': 5} | 260.78 | 4.61 | 0.693 |
| 900762564 | 20 | f40-41,47,f53,f60 | {'20': 4, '120': 5} | 268.39 | 5.12 | 0.709 |

## Options for the reviewers (no frozen rule is changed unilaterally)

A. Keep the frozen rule (20 s) as NOMINAL and add a prespecified SENSITIVITY
   scenario `cadence_alt` (120 s) for mixed-sector targets only (their short-
   period modes get the 120-s de-integration or rejection). Cost: <= 30 shards.
B. Exposure-time-weighted effective cadence per target (sum over published
   sectors of N_cadences x T_int / total) — a new derived input; needs the
   per-sector cadence counts from the SPOC products (available in the v3 report
   metadata) and its own prespecified formula.
C. Exclude P < 300 s modes of mixed-sector targets from the amplitude-axis
   surfaces (keep them in detection completeness) and state the caveat.

Recommendation: A (cheap, orthogonal to the ladder, keeps the frozen nominal
intact, and the contrast measures exactly the systematic in question).
