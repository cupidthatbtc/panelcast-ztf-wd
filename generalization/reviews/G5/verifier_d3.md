# G5 — independent D3 headline-number verification

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Branch | `generalization/campaign-1` | `generalization/campaign-1` | MATCH | `git branch --show-current`. |
| Frozen run completion | 2,901/2,901; 0 failures | 2,901 JSONs; 2,901 completion rows; 0 non-`complete` | MATCH | Count result JSONs and `run/completion.csv` statuses. |
| Laptop/Mac science-output guard | 13 identical after newline normalization; 0 differ | 13/13 equal after `CR+LF -> LF`; 0 differ | MATCH | Compare the 13 common science outputs, excluding the three documented special files. |
| Definitions used | rule 1; `classify_match`; `pass_eligible`; Wilson; frozen `overall_result` | read source; first three reimplemented; only `overall_result` imported | MATCH | Read `METRICS_SPEC.md`, `metrics_generalization.py`, and `run_catalog_lomb_scargle.py:254-288`; no campaign aggregation function called. |

## 1. P1 detection completeness

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| P1, eligible roster | 327/610 = 0.536; 95% CI 0.496–0.575 | 327/610 = 0.536065574; Wilson [0.496388298, 0.575291448] | MATCH | Count `per_star.csv` `dsct_flag1`/`confirmed`; retain `missing` as non-detections. |
| P1, usable frame | 327/585 = 0.559; 95% CI 0.518–0.599 | 327/585 = 0.558974359; Wilson [0.518484788, 0.598694461] | MATCH | `per_star.csv` positives with nonmissing status and both passes available. |
| Raw-JSON P1 cross-check | 327/610 and 327/585 | 327/610 and 327/585 | MATCH | Rebuilt all 2,901 best statuses with frozen `overall_result`; 25/610 positives have no JSON. |

## 2. P2 dominant-frequency recovery

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Mo join | 456 joined / 154 unjoined | 456 / 154 | MATCH | Join positive-roster KICs to finite table-2 frequencies and largest-amplitude modes. |
| Dominant-frequency truth identity | roster/Mo dominant | max absolute difference 3.55e-15 d⁻¹ over 456 | MATCH | Compare roster `dom_freq_per_day` with table-2 maximum-`Amp` frequency × 86400/1e6. |
| P2 frame | n = 441 | n = 441 | MATCH | Mo-joined ∩ usable ∩ own `S_low or S_high` pass-eligibility calculation. |
| P2 direct recovery | 72/441 = 0.163; 95% CI 0.132–0.201 | 72/441 = 0.163265306; Wilson [0.131703524, 0.200642879] | MATCH | `confirmed` and own full-taxonomy dominant classification equals exactly `direct`. |
| Correct frequency among detected | 72/238 = 0.303; 95% CI 0.248–0.364 | 72/238 = 0.302521008; Wilson [0.247679888, 0.363635722] | MATCH | Restrict the same P2 frame to 238 best-pass confirmations. |
| Any-mode chance match | mean 0.0037; p95 0.0091; 100 permutations | mean 0.003727354675; p95 0.009071325500; 100 permutations | MATCH | PCG64(20260829), permuted raw table-2 mode lists, fixed points omitted from each draw's denominator. |

## 3. P3 negative-class trigger rates

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Rule 1 / LS | 963/2,314 = 0.416; 95% CI 0.396–0.436 | 963/2,314 = 0.416162489; Wilson [0.396233898, 0.436368975] | MATCH | Count `per_star.csv` `dsct_flag0`/`confirmed`; 70 `missing` rows remain non-triggers. |
| Census | 65/2,314 = 0.028; 95% CI 0.022–0.036 | 65/2,314 = 0.028089888; Wilson [0.022100108, 0.035643901] | MATCH | Left-join frozen census flags to all negatives; missing flags are non-triggers. |
| Either | 993/2,314 = 0.429; 95% CI 0.409–0.449 | 993/2,314 = 0.429127053; Wilson [0.409094456, 0.449394571] | MATCH | Boolean union of LS-confirmed and census-variable. |
| Raw-JSON P3 cross-check | 963/2,314 | 963/2,314 | MATCH | Rebuilt all available best statuses with frozen `overall_result`. |
| Positive census completeness | 25/610 = 0.041; 95% CI 0.028–0.060 | 25/610 = 0.040983607; Wilson [0.027911939, 0.059800381] | MATCH | Count positive census flags on the eligible roster. |

## 4. Contingency and complementarity

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Usable positive frame | 585 | 585 | MATCH | Positive rows with both passes and a census row. |
| Census ∧ LS | 18 | 18 | MATCH | Cross-tabulate census-variable and best-status-confirmed. |
| Census only | 7 | 7 | MATCH | Census true, LS false. |
| LS only | 309 | 309 | MATCH | Census false, LS true. |
| Neither | 251 | 251 | MATCH | Both false. |
| Union | 334/585 = 0.571; 95% CI 0.530–0.610 | 334/585 = 0.570940171; Wilson [0.530498347, 0.610456402] | MATCH | `(18 + 7 + 309) / 585`. |
| Incremental census | 0.012 [0.006, 0.024] | 7/585 = 0.011965812 [0.005808073, 0.024491185] | MATCH | Wilson interval for census-only. |
| Incremental LS | 0.528 [0.488, 0.568] | 309/585 = 0.528205128 [0.487700121, 0.568342129] | MATCH | Wilson interval for LS-only. |
| McNemar exact | 9e-82 | 8.948591379e-82 | MATCH | Exact two-sided binomial test on 7 vs 309 discordant pairs. |

## 5. PPV

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Triggered PPV frame | n = 1,290 | 327 positives + 963 negatives = 1,290 | MATCH | Best-pass rule-1 triggers; `dsct_flag2` excluded. |
| Frame-specific label PPV | 0.097; bootstrap 95% 0.094–0.101 | 0.097273461; [0.093743901, 0.100977665] | MATCH | Weight negatives by 7292/2314, then independently repeat B=2,000 PCG64(20260831) negative-resampling bootstrap and FPC rescaling. |
| Separately reported `dsct_flag2` triggers | 38 | 38 | MATCH | Count best-pass confirmations in the excluded class. |

## 6. Descriptive and compliance numbers

### 6a. File-wide independent checks

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| `d3_trigger_decomposition.csv` | 2 rows | 2/2 rows; max numeric Δ 9.02e-17 | MATCH | Reapply the fixed closed solar-diurnal bands to confirmed negatives. |
| `d3_negative_trigger_strata.csv` | 32 rows | 32/32 rows; max numeric Δ 8.33e-17 | MATCH | Re-bin raw roster/crossmatch values at the README cuts and count raw-overall statuses. |
| `d3_covariates_by_class.csv` | 27 rows | 27/27 rows; max numeric Δ 2.27e-13 | MATCH | Recompute classwise finite-value moments and linear quantiles from roster/crossmatch columns. |
| `d3_confirmed_positive_match_partition.csv` | 12 cells | 12/12 cells; max numeric Δ 8.33e-17 | MATCH | Reclassify dominant matches and scan raw JSON top-15 peaks against raw table-2 modes. |
| `d3_p2_by_dominant_frequency_regime.csv` | 3 rows | 3/3 rows; max numeric Δ 2.78e-17 | MATCH | Split the independently rebuilt P2 frame at 4 and 24 d⁻¹. |
| `d3_truth_provenance_rescoring.csv` | 40 rows | 40/40 rows; max numeric Δ 4.55e-13 | MATCH | Select table-1 C=0 aliases and independently rescore fR, reflection, union, and top peaks. |
| `d3_dominant_confirmed_chance_match.csv` | 1 row | all fields exact | MATCH | Rebuild direct-hit matrix and accept 10,000 fixed-point-free PCG64(20260829) permutations. |
| `d3_a95_by_class_pass_band.csv` | 12 rows | 12/12 rows; max numeric Δ 2.84e-14 | MATCH | Read each a95 directly from raw JSON and apply linear quantiles. |
| `d3_vs_pool_coverage.csv` | 10 rows | 10/10 rows; max numeric Δ 5.68e-14 | MATCH | Recompute five covariates in each unpooled census frame. |
| Frequency histogram | 66 rows; D1 n=342, D3 n=963; overflow 0/0 | 66/66 rows; n=342/963; overflow=0/0; max numeric Δ 2.22e-16 | MATCH | Re-bin confirmed D1/D3 frequencies with the 33 fixed half-open bins. |
| Extra-frequency relations | 3,000 rows | 3,000/3,000 rows exact | MATCH | Re-evaluate yearly aliases and Kepler-Nyquist reflections from raw Mo truth. |

### 6b. P3 decomposition and strata

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Solar-diurnal, within | 121/963; 0.052 of negatives; 12.6% of numerator | 121; 121/2,314=0.052290406; 121/963=0.125649014 | MATCH | `f<4` and min\|f−k\|≤0.020 for k=1,2,3. |
| Solar-diurnal, outside | 842/963; 0.364 of negatives | 842; 842/2,314=0.363872083; 842/963=0.874350987 | MATCH | Complement of the fixed band within the unchanged P3 numerator. |
| Low-pass P3 | 920/2,314 = 0.398 | 920/2,314 = 0.397579948 | MATCH | Count low-pass `confirmed` statuses. |
| High-pass P3 | 85/2,314 = 0.037 | 85/2,314 = 0.036732930 | MATCH | Count high-pass `confirmed` statuses. |
| Merged OID ≤1 | 0/46 | 0/46 = 0 | MATCH | Bin `selected_ztf_objects`. |
| Merged OID 2 | 107/438 = 0.244 | 107/438 = 0.244292237 | MATCH | Same. |
| Merged OID 3–4 | 670/1,439 = 0.466 | 670/1,439 = 0.465601112 | MATCH | Same. |
| Merged OID ≥5 | 186/391 = 0.476 | 186/391 = 0.475703325 | MATCH | Same. |
| Magnitude g≤14 | 0.443 | 484/1,092 = 0.443223443 | MATCH | Roster `gmag≤14.0`. |
| Magnitude g>14 | 0.392 | 479/1,222 = 0.391980360 | MATCH | Roster `gmag>14.0`. |
| Teff quartile 1 | 0.405 | 290/716 = 0.405027933 | MATCH | Teff <6597 K. |
| Teff quartile 2 | 0.394 | 275/698 = 0.393982808 | MATCH | 6597≤Teff<6737 K. |
| Teff quartile 3 | 0.431 | 265/615 = 0.430894309 | MATCH | 6737≤Teff<7092.5 K. |
| Teff quartile 4 | 0.467 | 133/285 = 0.466666667 | MATCH | Teff≥7092.5 K. |
| Sky-cell range (4×4) | 0.211–0.611; RAq1 highest | 0.210526316–0.611111111; max `RAq1_DECq1` | MATCH | Apply the fixed RA/Dec quartile cuts. |

| sky cell | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| RAq1_DECq1 | 44/72 = 0.611111 | 44/72 = 0.611111 | MATCH | Fixed sky bin. |
| RAq1_DECq2 | 118/195 = 0.605128 | 118/195 = 0.605128 | MATCH | Fixed sky bin. |
| RAq1_DECq3 | 77/184 = 0.418478 | 77/184 = 0.418478 | MATCH | Fixed sky bin. |
| RAq1_DECq4 | 107/200 = 0.535000 | 107/200 = 0.535000 | MATCH | Fixed sky bin. |
| RAq2_DECq1 | 52/192 = 0.270833 | 52/192 = 0.270833 | MATCH | Fixed sky bin. |
| RAq2_DECq2 | 73/179 = 0.407821 | 73/179 = 0.407821 | MATCH | Fixed sky bin. |
| RAq2_DECq3 | 30/106 = 0.283019 | 30/106 = 0.283019 | MATCH | Fixed sky bin. |
| RAq2_DECq4 | 70/138 = 0.507246 | 70/138 = 0.507246 | MATCH | Fixed sky bin. |
| RAq3_DECq1 | 36/171 = 0.210526 | 36/171 = 0.210526 | MATCH | Fixed sky bin. |
| RAq3_DECq2 | 48/122 = 0.393443 | 48/122 = 0.393443 | MATCH | Fixed sky bin. |
| RAq3_DECq3 | 41/131 = 0.312977 | 41/131 = 0.312977 | MATCH | Fixed sky bin. |
| RAq3_DECq4 | 75/156 = 0.480769 | 75/156 = 0.480769 | MATCH | Fixed sky bin. |
| RAq4_DECq1 | 35/82 = 0.426829 | 35/82 = 0.426829 | MATCH | Fixed sky bin. |
| RAq4_DECq2 | 37/91 = 0.406593 | 37/91 = 0.406593 | MATCH | Fixed sky bin. |
| RAq4_DECq3 | 50/136 = 0.367647 | 50/136 = 0.367647 | MATCH | Fixed sky bin. |
| RAq4_DECq4 | 70/159 = 0.440252 | 70/159 = 0.440252 | MATCH | Fixed sky bin. |

### 6c. Positive partition, P2 regimes, fR, chance

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Confirmed-positive total | 327 over P1 n=610 | 327/610 | MATCH | Best-pass rule-1 confirmations. |
| Direct | 72 | 29 top-15-false + 43 top-15-true = 72 | MATCH | Own dominant taxonomy. |
| Unmatched | 164, including 38 with truth in top 15 | 126 + 38 = 164; top-15 true=38 | MATCH | Own dominant taxonomy plus raw-JSON peak scan. |
| Unscored/unjoined | 89 | 89 | MATCH | Confirmed positives without finite dominant truth. |
| Harmonic | 1 | 1 | MATCH | Own full taxonomy. |
| Window alias | 1 | 1 | MATCH | Own full taxonomy. |
| Ambiguous | 0 | 0 | MATCH | Own full taxonomy. |
| P2 dominant <4 d⁻¹ | 10/115 = 0.087 | n=115; confirmed=53; direct=10; rate=0.086956522 | MATCH | Split rebuilt P2 frame. |
| P2 dominant 4–24 d⁻¹ | 62/318 = 0.195 | n=318; confirmed=183; direct=62; rate=0.194968553 | MATCH | Split rebuilt P2 frame. |
| P2 dominant ≥24 d⁻¹ | 0/8 | n=8; confirmed=2; direct=0 | MATCH | Split rebuilt P2 frame; counts-only cell. |
| Joined dominants [24,24.46848) | 10/456 | 10/456 | MATCH | Count raw table-2 maximum-amplitude frequencies. |
| Joined dominants ≥24.46848 | 0/456 | 0/456 | MATCH | Count raw table-2 maximum-amplitude frequencies. |
| Aliased-dominant fR frame | exactly 40; 20 confirmed | 40; 39 JSONs; 20 confirmed | MATCH | Table-1 C=0 and \|Freq−dominant\|≤0.1 μHz with stated tie-break. |
| fR direct rescoring | 3 | 3 | MATCH | Own frozen-taxonomy reclassification against one physical fR. |
| Nyquist-reflection matches | 0 | 0 | MATCH | Test positive `2×24.46848−fR` reflections at 1.5/baseline tolerance. |
| fR full class counts | file: 35 unmatched, 3 direct, 1 window alias, 1 unscored | 35, 3, 1, 1 | MATCH | Recompute all 40 rows. |
| Any-mode-plus-fR top-15 hits | file: 8 | 8 | MATCH | Scan both passes' stored peaks against table-2∪physical-fR truth. |
| Dominant-only chance | mean 0.0003; q95 0.0042; 10,000 derangements | mean 0.000301260504; median 0; q95 0.004201680672; 10,000 accepted, 17,098 rejected | MATCH | Direct-hit matrix; fixed-point-free PCG64(20260829) permutations over n=238. |

### 6d. a95 and coverage

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| High-pass a95, negatives, zg/zr | 1.03 / 1.09 mmag | 1.030541956 / 1.089875962 | MATCH | Linear medians of 2,244 finite raw-JSON values per band. |
| High-pass a95, positives, zg/zr | 1.15 / 1.15 mmag | 1.154151275 / 1.152399707 | MATCH | Linear medians of 585 finite raw-JSON values per band. |
| Low-pass a95, negatives, zg/zr | 2.62 / 2.87 mmag | 2.616459383 / 2.867371677 | MATCH | Linear medians of 2,244 finite raw-JSON values per band. |
| Low-pass a95, positives, zg/zr | 2.98 / 3.15 mmag | 2.981329008 / 3.145537615 | MATCH | Linear medians of 585 finite raw-JSON values per band. |
| Coverage frames | D3 2,901; pool 928 | 2,901; 928 | MATCH | Count the two census tables without pooling. |
| Median zg epochs | 754 vs 437 | D3 754.0; pool 437.5 (file 437.5; nearest integer 438) | **MISMATCH** | Linear median of `zg_n_exp` in each frame. |
| Median zg nights | 640 vs 372 | D3 640.0; pool 371.5 (rounds to 372) | MATCH | Linear median of `zg_n_nights` in each frame. |
| Median W_g contrasts | 119 vs 58 | 119.0 vs 58.0 | MATCH | Median of `zg_n_exp − zg_n_nights`; all values nonnegative. |

### 6e. Compliance and sidecar-only numeric statements

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Attrition cells | 555 | 555 | MATCH | Recreate all eight left-closed categorical keys and group the 3,000-row roster. |
| Attrition totals | 3,000→3,000→2,955→2,901→2,901 | 3,000→3,000→2,955→2,901→2,901 | MATCH | Sum roster/fetched/finite-crossmatch/QC/both-pass stage flags. |
| Histogram source frames | D1 928; D3 negative confirmations 963 | 928 rows; 963 confirmations | MATCH | Read published D1 catalog and rebuilt D3 statuses. |
| Histogram overflow ≥1440 d⁻¹ | file 0/0 | 0/0 | MATCH | Fixed final overflow bin. |
| Extra-relation rows/evaluable | 3,000 rows; file 444 per predicate | 3,000; 444 per predicate | MATCH | One row per `per_star`; require finite candidate, baseline, and relevant truth. |
| Extra yearly aliases, dominant/any | file 0 / 6 | 0 / 6 | MATCH | Apply Δyear=1/365.25 d⁻¹. |
| Extra Nyquist reflections, dominant/any | file 0 / 1 | 0 / 1 | MATCH | Apply fNyq=24.46848 d⁻¹. |

## 7. Raw-JSON and provenance spot-checks

| quantity | README/file value | re-derived value | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| Random raw-result sample | per-star frozen values | 50/50 status, 50/50 best pass, 50/50 frequency within 1e-12; max Δ=2.27e-13 d⁻¹ | MATCH | PCG64 seed 505003, without replacement from sorted 2,901 JSON SIDs; frozen `overall_result`. |
| Full raw-result audit | per-star frozen values | 2,901/2,901 for status/pass/frequency within 1e-12 | MATCH | Same comparison over the full raw-result population. |
| Random provenance sample | sidecar, shard, result, completion agree | 20/20 pass all five checks | MATCH | PCG64 seed 205003; hash shard/result/sidecar bytes and compare completion status/result/provenance fields. |

Raw-result sample (seed 505003): `9000000000002163636, 9000000000002581626, 9000000000003560366, 9000000000003748474, 9000000000003858926, 9000000000004285040, 9000000000004366310, 9000000000004737731, 9000000000004764008, 9000000000004919980, 9000000000005990706, 9000000000006192580, 9000000000006306941, 9000000000006356251, 9000000000006784170, 9000000000007336185, 9000000000007467076, 9000000000007514484, 9000000000007612505, 9000000000007916156, 9000000000007973052, 9000000000008086885, 9000000000008105657, 9000000000008128675, 9000000000008391086, 9000000000008420644, 9000000000008474295, 9000000000008525457, 9000000000008525674, 9000000000008545516, 9000000000008646235, 9000000000008783270, 9000000000008939379, 9000000000008955871, 9000000000009076726, 9000000000009712093, 9000000000009812716, 9000000000009873847, 9000000000009944208, 9000000000009965642, 9000000000010005961, 9000000000010095496, 9000000000010514349, 9000000000010593438, 9000000000010816401, 9000000000010989811, 9000000000011662543, 9000000000011819079, 9000000000012165609, 9000000000012646712`.

Provenance sample (seed 205003): `9000000000003658426, 9000000000004677282, 9000000000006421651, 9000000000006520395, 9000000000006522144, 9000000000006605809, 9000000000006879787, 9000000000006951698, 9000000000006964677, 9000000000007687468, 9000000000008018404, 9000000000008817926, 9000000000009364179, 9000000000009540796, 9000000000009602210, 9000000000009710659, 9000000000010471601, 9000000000011073754, 9000000000011767325, 9000000000011852985`.

## MISMATCHES

1. `README.md`, coverage line: development-pool median `zg_n_exp` is stated as **437**; `d3_vs_pool_coverage.csv` and the independent linear median both give **437.5**, which rounds to **438**, not 437. Likely cause: manual truncation/transcription in the top-level README; the descriptive CSV is correct.

## Exact commands/code run

```bash
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
git branch --show-current
git status --short
sed -n '1,220p' generalization/METRICS_SPEC.md
rg -n -A 90 -B 10 '^def overall_result' scripts/run_catalog_lomb_scargle.py
rg -n -A 80 '^def wilson|^def classify_match|^def pass_eligible' scripts/generalization/metrics_generalization.py
find generalization/results/2026-09-02_d3/descriptive_postlaunch -type f \( -iname 'README.md' -o -iname '*.README.md' -o -iname '*manifest*' \) -print | sort
```

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-gen/bin/python - <<'PY'
from pathlib import Path
from bisect import bisect_right
import hashlib, json, math, re, sys
import numpy as np
import pandas as pd
from scipy.stats import binomtest

R=Path('/Users/jackneo/Documents/vonhippel-base9/astro-wd'); B=R/'generalization/results/2026-09-02_d3'; M=B/'metrics'; D=B/'descriptive_postlaunch'
S=R/'outputs/generalization/d3_sync/d3_run/stars'; H=R/'outputs/generalization/d3_sync/d3_panels/exposure_stars'
sys.path.insert(0,str(R/'scripts/generalization'))
from frozen_api import overall_result
SID=1.00273790935
def finite(x):
    try:return math.isfinite(float(x))
    except (TypeError,ValueError):return False
def classify(fc,truth,tol):
    hit=set()
    for ft in truth:
        if abs(fc-ft)<=tol:hit.add('direct')
        if abs(fc-2*ft)<=tol or abs(fc-ft/2)<=tol:hit.add('harmonic')
        for k in (1,2):
            for sign in (1.,-1.):
                if abs(fc-abs(ft+sign*k*SID))<=tol:hit.add('window_alias')
    return 'unmatched' if not hit else (next(iter(hit)) if len(hit)==1 else 'ambiguous')
def eligible(truth,p,b):
    if not truth or not finite(b):return False
    lo,hi=(2/b,48.) if p=='low' else (24.,1440.)
    return any(lo<=x<=hi for x in truth)
def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return p,c-h,c+h
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

per=pd.read_csv(M/'per_star.csv',dtype={'sid':str}); ros=pd.read_csv(R/'generalization/data/d3/roster_d3.csv',dtype={'source_id':str})
mo2=pd.read_csv(R/'generalization/data/d3/raw/mo2026_table2.csv'); mo1=pd.read_csv(R/'generalization/data/d3/raw/mo2026_table1.csv')
xc=pd.read_csv(R/'generalization/data/d3/crossmatch_freeze/crossmatch_adjudication.csv',dtype={'source_id':str})
cen=pd.read_csv(R/'generalization/data/d3/crossmatch_freeze/panels_census_generic.csv',dtype={'source_id':str})
comp=pd.read_csv(B/'run/completion.csv',dtype={'source_id':str})
js={}; ov={}
for p in sorted(S.glob('*.json')):
    if p.name.endswith('.prov.json'):continue
    j=json.loads(p.read_text());js[j['source_id']]=j;ov[j['source_id']]=overall_result(j)
f=ros.assign(sid=ros.source_id);f['best_status']=f.sid.map(lambda s:ov[s]['blind_status'] if s in ov else 'missing')
f['best_pass']=f.sid.map(lambda s:ov[s]['best_pass'] if s in ov else None);f['best_frequency']=f.sid.map(lambda s:ov[s]['best_frequency_per_day'] if s in ov else np.nan)
f['baseline']=f.sid.map(lambda s:ov[s]['baseline_days'] if s in ov else np.nan);f['usable']=f.sid.isin(ov)
f=f.merge(cen[['source_id','census_variable']],on='source_id',how='left')
mo2['fd']=mo2.Freq*86400/1e6;truth={int(k):g.fd.tolist() for k,g in mo2.groupby('KIC')};mx=mo2.loc[mo2.groupby('KIC').Amp.idxmax()];primary=dict(zip(mx.KIC.astype(int),mx.fd))
f['truth']=f.KIC.astype(int).map(lambda k:truth.get(k,[]));f['primary']=f.KIC.astype(int).map(primary)
f['joined']=(f.class_label=='dsct_flag1')&f.truth.map(bool)&np.isfinite(f.primary)&np.isfinite(f.dom_freq_per_day)&np.isfinite(f.amp_mmag)
f['Sbest']=f.apply(lambda r:eligible(r.truth,'low',r.baseline) or eligible(r.truth,'high',r.baseline),axis=1)
f['match']=f.apply(lambda r:classify(r.best_frequency,[r.primary],1.5/r.baseline) if finite(r.best_frequency) and finite(r.primary) else 'unscored',axis=1)
pos=f[f.class_label=='dsct_flag1'];neg=f[f.class_label=='dsct_flag0'];p2=pos[pos.joined&pos.usable&pos.Sbest]
for name,k,n in [('P1',sum(pos.best_status=='confirmed'),len(pos)),('P1_usable',sum(pos[pos.usable].best_status=='confirmed'),sum(pos.usable)),('P2',sum((p2.best_status=='confirmed')&(p2.match=='direct')),len(p2)),('P2_given_detected',sum((p2.best_status=='confirmed')&(p2.match=='direct')),sum(p2.best_status=='confirmed')),('P3',sum(neg.best_status=='confirmed'),len(neg))]:print(name,k,n,wilson(k,n))
ck=int(neg.census_variable.fillna(False).sum());ek=int(((neg.best_status=='confirmed')|neg.census_variable.fillna(False)).sum());print('P3_census',ck,wilson(ck,len(neg)),'P3_either',ek,wilson(ek,len(neg)))
u=pos[pos.usable];C=u.census_variable.astype(bool);L=u.best_status=='confirmed';tab=[sum(C&L),sum(C&~L),sum(~C&L),sum(~C&~L)];print('contingency',tab,'union',wilson(sum(tab[:3]),len(u)),'mcnemar',binomtest(min(tab[1],tab[2]),tab[1]+tab[2],.5).pvalue)

# Prespecified chance and PPV.
cf=f[f.joined&f.best_frequency.map(finite)].reset_index(drop=True);rng=np.random.Generator(np.random.PCG64(20260829));rates=[]
for _ in range(100):
    pm=rng.permutation(len(cf));den=sum(pm!=np.arange(len(pm)));rates.append(sum(pm[i]!=i and classify(r.best_frequency,cf.iloc[pm[i]].truth,1.5/r.baseline)=='direct' for i,r in cf.iterrows())/den)
print('chance',np.mean(rates),np.quantile(rates,.95))
tr=f[f.class_label.isin(['dsct_flag0','dsct_flag1'])&(f.best_status=='confirmed')];point=sum(tr.sampling_weight*(tr.class_label=='dsct_flag1'))/sum(tr.sampling_weight)
rng=np.random.Generator(np.random.PCG64(20260831));p0=per[per.class_label=='dsct_flag1'];n0=per[per.class_label=='dsct_flag0'].reset_index(drop=True);boots=[]
for _ in range(2000):
    z=pd.concat([p0,n0.iloc[rng.integers(0,len(n0),len(n0))]]);z=z[z.best_status=='confirmed'];boots.append(sum(z.weight*(z.class_label=='dsct_flag1'))/sum(z.weight))
q=np.quantile([point+math.sqrt(1-2314/7292)*(x-point) for x in boots],[.025,.975]);print('ppv',len(tr),point,*q)

# Descriptive counts, a95, coverage.
inside=neg[neg.best_status=='confirmed'].best_frequency.map(lambda x:x<4 and min(abs(x-k) for k in (1,2,3))<=.020000001);print('solar',sum(inside),sum(~inside))
nx=neg.merge(xc[['source_id','selected_ztf_objects']],on='source_id');print('pass',sum(per[(per.class_label=='dsct_flag0')].low_status=='confirmed'),sum(per[(per.class_label=='dsct_flag0')].high_status=='confirmed'))
print('oid',[(q,sum((nx.selected_ztf_objects.map(lambda x:0 if x<=1 else 1 if x<3 else 2 if x<5 else 3)==q)&(nx.best_status=='confirmed')),sum(nx.selected_ztf_objects.map(lambda x:0 if x<=1 else 1 if x<3 else 2 if x<5 else 3)==q)) for q in range(4)])
for name,cuts,col in [('teff',(6597,6737,7092.5),'Teff'),('sky_ra',(290.0945525,293.54213,296.340635),'ra'),('sky_dec',(41.048665,43.879275,46.70182),'dec')]:print(name,pd.Series([bisect_right(cuts,float(x)) for x in neg[col]]).value_counts().sort_index().to_dict())
for cl in ('dsct_flag0','dsct_flag1'):
    ids=f.loc[f.class_label==cl,'sid']
    for pn in ('low','high'):
        print('a95',cl,pn,*[np.median([js[s]['passes'][pn][b+'_a95_mmag'] for s in ids if s in js]) for b in ('zg','zr')])
for name,path in [('D3',R/'generalization/data/d3/crossmatch_freeze/panels_census_generic.csv'),('pool',R/'catalog-rebuild/results/2026-08-01_full/catalog/census_full_catalog.csv')]:
    z=pd.read_csv(path);print('coverage',name,len(z),np.median(z.zg_n_exp),np.median(z.zg_n_nights),np.median(z.zg_n_exp-z.zg_n_nights))

# Random raw-result and provenance samples.
pi=per.set_index('sid');univ=np.array(sorted(ov));rng=np.random.default_rng(505003);s50=sorted(rng.choice(univ,50,False));ok=[]
for s in s50:
    o=ov[s];x=pi.loc[s];ok.append((o['blind_status']==x.best_status,o['best_pass']==x.best_pass,math.isclose(o['best_frequency_per_day'],x.best_frequency_per_day,rel_tol=0,abs_tol=1e-12)))
print('sample50',np.sum(ok,axis=0),max(abs(ov[s]['best_frequency_per_day']-pi.loc[s].best_frequency_per_day) for s in s50),','.join(s50))
ci=comp.set_index('source_id');rng=np.random.default_rng(205003);s20=sorted(rng.choice(univ,20,False));checks=[]
for s in s20:
    jp=S/f'{s}.json';pp=S/f'{s}.prov.json';sp=H/f'{s}.csv.gz';pr=json.loads(pp.read_text());c=ci.loc[s]
    checks.append(pr['shard_sha256']==sha(sp) and pr['result_sha256']==sha(jp) and c.status=='complete' and c.result_sha256==sha(jp) and c.provenance_sha256==sha(pp))
print('provenance20',sum(checks),','.join(s20))

# Newline-normalized 13-file guard.
ref=B/'metrics_laptop_prefix';special={'attrition.csv','manifest.json','inputs_sha256.json'};files=sorted(set(p.relative_to(ref).as_posix() for p in ref.rglob('*') if p.is_file())&set(p.relative_to(M).as_posix() for p in M.rglob('*') if p.is_file())-special)
norm=lambda p:re.sub(rb'\r+\n',b'\n',p.read_bytes());print('science_guard',len(files),sum(norm(ref/x)==norm(M/x) for x in files))
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-gen/bin/python - <<'PY'
from pathlib import Path
from bisect import bisect_right
import json, math, sys
import numpy as np
import pandas as pd
R=Path('/Users/jackneo/Documents/vonhippel-base9/astro-wd');B=R/'generalization/results/2026-09-02_d3';M=B/'metrics';D=B/'descriptive_postlaunch';S=R/'outputs/generalization/d3_sync/d3_run/stars'
sys.path.insert(0,str(R/'scripts/generalization'));from frozen_api import overall_result
SID=1.00273790935
def finite(x):
    try:return math.isfinite(float(x))
    except:return False
def cm(fc,truth,tol):
    h=set()
    for ft in truth:
        if abs(fc-ft)<=tol:h.add('direct')
        if abs(fc-2*ft)<=tol or abs(fc-ft/2)<=tol:h.add('harmonic')
        for k in (1,2):
            for s in (1.,-1.):
                if abs(fc-abs(ft+s*k*SID))<=tol:h.add('window_alias')
    return 'unmatched' if not h else (next(iter(h)) if len(h)==1 else 'ambiguous')
per=pd.read_csv(M/'per_star.csv',dtype={'sid':str});ros=pd.read_csv(R/'generalization/data/d3/roster_d3.csv',dtype={'source_id':str});mo2=pd.read_csv(R/'generalization/data/d3/raw/mo2026_table2.csv');mo1=pd.read_csv(R/'generalization/data/d3/raw/mo2026_table1.csv');xc=pd.read_csv(R/'generalization/data/d3/crossmatch_freeze/crossmatch_adjudication.csv',dtype={'source_id':str})
js={};ov={}
for p in S.glob('*.json'):
    if p.name.endswith('.prov.json'):continue
    j=json.loads(p.read_text());js[j['source_id']]=j;ov[j['source_id']]=overall_result(j)
mo2['fd']=mo2.Freq*86400/1e6;truth={int(k):g.fd.tolist() for k,g in mo2.groupby('KIC')};mx=mo2.loc[mo2.groupby('KIC').Amp.idxmax()];primary=dict(zip(mx.KIC.astype(int),mx.fd));f=ros.rename(columns={'source_id':'sid'}).copy();f['truth']=f.KIC.astype(int).map(lambda k:truth.get(k,[]));f['primary']=f.KIC.astype(int).map(primary);f['status']=f.sid.map(lambda s:ov[s]['blind_status'] if s in ov else 'missing');f['freq']=f.sid.map(lambda s:ov[s]['best_frequency_per_day'] if s in ov else np.nan);f['base']=f.sid.map(lambda s:ov[s]['baseline_days'] if s in ov else np.nan);f['match']=f.apply(lambda r:cm(r.freq,[r.primary],1.5/r.base) if finite(r.freq) and finite(r.primary) else 'unscored',axis=1)
def top(s,ts):
    if s not in js or not ts:return False
    t=1.5/js[s]['baseline_days']
    return any(cm(p['frequency_per_day'],ts,t)=='direct' for q in ('low','high') for p in js[s]['passes'][q].get('top_peaks',[]))
pc=f[(f.class_label=='dsct_flag1')&(f.status=='confirmed')].copy();pc['top']=pc.apply(lambda r:top(r.sid,r.truth),axis=1)
print('positive_partition',pc.groupby(['match','top']).size().to_dict())
p2=per[(per.class_label=='dsct_flag1')&per.freq_scorable&per.eligible_any_pass&(per.best_status!='missing')].copy()
for name,lo,hi in [('lt4',-np.inf,4),('4to24',4,24),('ge24',24,np.inf)]:
    z=p2[(p2.primary_freq>=lo)&(p2.primary_freq<hi)];print('regime',name,len(z),sum(z.best_status=='confirmed'),sum((z.best_status=='confirmed')&(z.best_candidate_matches_dominant=='direct')))
cf=p2[p2.best_status=='confirmed'].reset_index(drop=True);mat=np.array([[cm(a.best_frequency_per_day,[b.primary_freq],1.5/a.baseline_days)=='direct' for b in cf.itertuples()] for a in cf.itertuples()]);rng=np.random.Generator(np.random.PCG64(20260829));rates=[];rej=0
while len(rates)<10000:
    q=rng.permutation(len(cf))
    if any(q==np.arange(len(cf))):rej+=1;continue
    rates.append(mat[np.arange(len(cf)),q].mean())
print('dominant_chance',len(cf),np.mean(rates),np.median(rates),np.quantile(rates,.95),rej)
c0=mo1[mo1.C==0];fr=[]
for r in f[f.class_label=='dsct_flag1'].itertuples():
    if not finite(r.dom_freq_uhz):continue
    g=c0[c0.KIC==r.KIC].copy();g['d']=(g.Freq-r.dom_freq_uhz).abs();g=g[g.d<=.1]
    if g.empty:continue
    x=g.sort_values(['d','fR']).iloc[0];phys=x.fR*86400/1e6;ref=2*24.46848-phys;m=cm(r.freq,[phys],1.5/r.base) if finite(r.freq) else 'unscored';fr.append((r.sid,r.status,m,finite(r.freq) and ref>0 and abs(r.freq-ref)<=1.5/r.base,top(r.sid,r.truth+[v*86400/1e6 for v in c0.loc[c0.KIC==r.KIC,'fR']])))
fr=pd.DataFrame(fr,columns=['sid','status','match','reflection','top']);print('fR',len(fr),sum(fr.status=='confirmed'),fr.match.value_counts().to_dict(),sum(fr.reflection),sum(fr.top))

# Complete histogram/relation sidecar counts.
cat=pd.read_csv(R/'catalog-rebuild/results/2026-08-01_full/catalog/ls_full_catalog.csv');edges=np.array([0,.25,.5,.75,.98,1.02,1.25,1.5,1.75,1.98,2.02,2.25,2.5,2.75,2.98,3.02,3.25,3.5,3.75,4,6,8,12,16,20,24,32,48,96,192,384,768,1440,np.inf])
for name,a in [('D1',cat.loc[cat.blind_status=='confirmed','best_frequency_per_day'].to_numpy()),('D3',per.loc[(per.class_label=='dsct_flag0')&(per.best_status=='confirmed'),'best_frequency_per_day'].to_numpy())]:
    h=np.bincount(np.searchsorted(edges,a,side='right')-1,minlength=33);print('hist',name,len(a),len(h),h[-1])
dy=1/365.25;ny=24.46848;rr=[]
for r in per.itertuples():
    fc=float(r.best_frequency_per_day) if finite(r.best_frequency_per_day) else np.nan;t=1.5/r.baseline_days if finite(r.baseline_days) else np.nan;dom=float(r.primary_freq) if finite(r.primary_freq) else np.nan;ts=truth.get(int(ros.loc[ros.source_id==r.sid,'KIC'].iloc[0]),[]);ds=str(r.best_candidate_matches_dominant)!='unscored' and finite(dom);ass=str(r.best_candidate_matches_any_mode)!='unscored'
    y=lambda x:abs(fc-abs(x+dy))<=t or abs(fc-abs(x-dy))<=t;n=lambda x:2*ny-x>0 and abs(fc-(2*ny-x))<=t
    rr.append((y(dom) if ds else None,any(y(x) for x in ts) if ass else None,n(dom) if ds else None,any(n(x) for x in ts) if ass else None))
print('relations',len(rr),[(sum(x[i] is not None for x in rr),sum(x[i] is True for x in rr)) for i in range(4)])

# Attrition stage totals and ruled eight-key cell count.
def tf(x):return bool(x) if isinstance(x,(bool,np.bool_)) else isinstance(x,str) and x=='True'
def lb(x,e,l,u):
    if not finite(x):return u
    return l[bisect_right(e,float(x))]
rows=[];px=per.set_index('sid');joined=set(f.loc[(f.class_label=='dsct_flag1')&f.primary.notna(),'sid'])
for r in ros.itertuples():
    q=xc[xc.source_id==r.source_id].iloc[0];sep=q.nearest_separation_arcsec;sel=q.selected_ztf_objects;dom=r.dom_freq_per_day;period=86400/dom if finite(dom) and dom>0 else np.nan;both=r.source_id in px.index and px.loc[r.source_id,'best_status']!='missing'
    rows.append((r.class_label,lb(r.amp_mmag,(.5,1,2,5,10,20,50),tuple(range(8)),-1),'j' if r.source_id in joined else 'u','g0' if r.gmag<=14 else 'g1',lb(period,(100,200,500,1000,2000,.05*86400,.2*86400,86400,10*86400,100*86400),tuple(range(11)),-1),lb(r.Teff,(6597,6737,7092.5),tuple(range(4)),-1),lb(q.ztf_objects_in_cone,(4,7,10),tuple(range(4)),-1),lb(sep,(.054159657268769895,.0972924425684607,.15375607598589985,1),tuple(range(5)),-1),tf(q.cache_present),q.read_status=='ok' and finite(sep) and finite(sel) and sel>=1,tf(q.crossmatched),both))
a=pd.DataFrame(rows);print('attrition',len(a),a.iloc[:,8:].sum().astype(int).tolist(),a.groupby(list(range(8))).ngroups)
PY
```

```bash
git diff -- generalization/reviews/G5/verifier_d3.md
git status --short
```

VERDICT: DISCREPANCIES — top-level `README.md` reports the development-pool median `zg_n_exp` as 437; the frozen descriptive file and independent calculation give 437.5 (nearest integer 438). All other checked headline and descriptive numbers reproduce.
