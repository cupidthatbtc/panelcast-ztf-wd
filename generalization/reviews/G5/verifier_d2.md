# G5 independent verification — frozen D2

Scope: `generalization/results/2026-09-04_d2/`, raw star JSON/provenance sidecars, and gen2 shards. I read `overall_result` before importing it; it is the only frozen/campaign computation imported. Match classification, Wilson and Clopper–Pearson intervals, P4 algebra, clustered bootstraps, scenario contrasts, surfaces, derangements, hashes, and all aggregations below are independent code.

The verifier used `B=2000`, `PCG64` seed `20260830`, matching the metrics program, so the percentile intervals are directly comparable. The 20-star provenance sample used seed `20260903`; chance matching used the frozen seed `20260829` and 10,000 target-level derangements.

## Run universe and integrity

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| nominal arm B | 309 | 309 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| nominal arm A | 309 | 309 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| ladder (8 × 103) | 824 | 824 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| phase (2 × 103) | 206 | 206 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| ampscale (2 × 103) | 206 | 206 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| dropout | 76 | 76 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| cadence_alt | 33 | 33 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| redilution | 20 | 20 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| paired controls | 106 | 106 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| Gaussian nulls | 1000 | 1000 | MATCH | Counted typed shard-manifest rows by arm/scenario. |
| total shards | 3,089 | 3089 | MATCH | Summed the generation run matrix and counted unique campaign IDs. |
| completion / failures | 3,089 / 0 | 3089 / 0 | MATCH | Read completion.csv and the run-manifest failure map. |
| all completion/result/provenance chains | 3,089 consistent | 3,089 consistent | MATCH | For every ID, hashed JSON and sidecar; checked completion hashes, source ID, passes, generation ID, and manifest shard SHA. |
| generation ID | 129740d1809c7a347e16474d2186aac30a8f4eac29f9b06b0fc047cc1c4ef7cb | 129740d1809c7a347e16474d2186aac30a8f4eac29f9b06b0fc047cc1c4ef7cb | MATCH | SHA-256 of canonical sorted generation basis; copies in run, metrics, and raw generation agree. |
| raw selector/match rows vs per_star.csv | 3,089 selectors; 1,983 A/B match rows | all equal | MATCH | Applied frozen overall_result to raw JSON and independent dominant-mode classification. |
| bundle SHA256SUMS | 69 entries | all hashes equal | MATCH | Hashed every listed frozen-bundle file. |

## P4 nominal arm B

For eligible, each target contributes `(y_K0 + y_K1 + y_K2)/3`, with an absent or unusable scheduled stratum set to zero. For usable, each target contributes the mean over usable strata and a target with no usable strata is omitted. Here all 309 strata are usable, so eligible and usable coincide. Recovery is `confirmed AND dominant match == direct`; trigger is `confirmed`.

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| P4 nominal B recovery, eligible | 0.216828478964 [0.171521035599, 0.26213592233] | 0.216828478964 [0.171521035599, 0.26213592233] | MATCH | Mean of target means over K; n_targets=103, zero-usable targets=0. |
| P4 nominal B recovery, usable | 0.216828478964 [0.171521035599, 0.26213592233] | 0.216828478964 [0.171521035599, 0.26213592233] | MATCH | Mean of target means over K; n_targets=103, zero-usable targets=0. |
| P4 nominal B trigger, eligible | 0.556634304207 [0.517799352751, 0.601941747573] | 0.556634304207 [0.517799352751, 0.601941747573] | MATCH | Mean of target means over K; n_targets=103, zero-usable targets=0. |
| P4 nominal B trigger, usable | 0.556634304207 [0.517799352751, 0.601941747573] | 0.556634304207 [0.517799352751, 0.601941747573] | MATCH | Mean of target means over K; n_targets=103, zero-usable targets=0. |

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| recovery K0 target mean | 7/103 = 0.0679611650485 | 7/103 = 0.0679611650485 | MATCH | Counted raw nominal-B endpoint successes in the scheduled K stratum. |
| recovery K1 target mean | 11/103 = 0.106796116505 | 11/103 = 0.106796116505 | MATCH | Counted raw nominal-B endpoint successes in the scheduled K stratum. |
| recovery K2 target mean | 49/103 = 0.47572815534 | 49/103 = 0.47572815534 | MATCH | Counted raw nominal-B endpoint successes in the scheduled K stratum. |
| trigger K0 target mean | 24/103 = 0.233009708738 | 24/103 = 0.233009708738 | MATCH | Counted raw nominal-B endpoint successes in the scheduled K stratum. |
| trigger K1 target mean | 54/103 = 0.52427184466 | 54/103 = 0.52427184466 | MATCH | Counted raw nominal-B endpoint successes in the scheduled K stratum. |
| trigger K2 target mean | 94/103 = 0.912621359223 | 94/103 = 0.912621359223 | MATCH | Counted raw nominal-B endpoint successes in the scheduled K stratum. |

## P5 Gaussian-null acceptance

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| confirmed Gaussian nulls | 19/1,000 = 0.019 | 19/1000 = 0.019 | MATCH | Applied overall_result to all 1,000 raw null JSONs and counted confirmed. |
| one-sided exact CP upper | 0.0277552860455 | 0.0277552860455 | MATCH | Computed Beta_0.95(x+1, n-x). |
| sole confirmatory decision | U95 ≤ 0.005: FAILS | 0.0277552860455 ≤ 0.005: False | MATCH | Compared the re-derived exact upper bound with 0.005. |

## Paired controls, native trigger rate, and reuse

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| D 2×2 | both=118, B-only=54, C-only=11, neither=126 | both=118, B-only=54, C-only=11, neither=126 | MATCH | Joined each nominal-B shard to its manifest control; R_C uses the partner B dominant frequency and control baseline tolerance. |
| D P(B=1) | 0.556634304207 [0.517799352751, 0.601941747573] | 0.556634304207 [0.517799352751, 0.601941747573] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| D P(C=1) | 0.417475728155 [0.36569579288, 0.46925566343] | 0.417475728155 [0.36569579288, 0.46925566343] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| D B−C | 0.139158576052 [0.0906148867314, 0.190938511327] | 0.139158576052 [0.0906148867314, 0.190938511327] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| D P(B=1,C=0) | 0.174757281553 [0.135922330097, 0.220064724919] | 0.174757281553 [0.135922330097, 0.220064724919] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| R 2×2 | both=0, B-only=67, C-only=0, neither=242 | both=0, B-only=67, C-only=0, neither=242 | MATCH | Joined each nominal-B shard to its manifest control; R_C uses the partner B dominant frequency and control baseline tolerance. |
| R P(B=1) | 0.216828478964 [0.171521035599, 0.26213592233] | 0.216828478964 [0.171521035599, 0.26213592233] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| R P(C=1) | 0 [0, 0] | 0 [0, 0] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| R B−C | 0.216828478964 [0.171521035599, 0.26213592233] | 0.216828478964 [0.171521035599, 0.26213592233] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| R P(B=1,C=0) | 0.216828478964 [0.171521035599, 0.26213592233] | 0.216828478964 [0.171521035599, 0.26213592233] | MATCH | Computed per-target means over three K pairs and resampled 103 target labels. |
| native control trigger rate | 47/106; 0.443396226415 [0.352450813698, 0.538300819348] | 47/106; 0.443396226415 [0.352450813698, 0.538300819348] | MATCH | Counted confirmed among 106 unique controls; two-sided Wilson 95% interval. |
| control reuse distribution (assignments→controls) | 1→36, 2→28, 3→11, 4→10, 5→6, 6→5, 7→4, 8→2, 9→2, 10→1, 12→1 | 1→36, 2→28, 3→11, 4→10, 5→6, 6→5, 7→4, 8→2, 9→2, 10→1, 12→1 | MATCH | Grouped the 309 nominal-B control IDs; counts sum to 106 controls and 309 assignments. |
| paired-control row table | 309 pairs | 309 pairs, all rows equal | MATCH | Compared independently reconstructed D/R booleans and IDs row by row. |

## Scenario-minus-nominal-K1 contrasts — eligible denominator

Each value is `p_scenario; p_nominal_K1; difference [95% bounds]`. The same 103-target draw matrix is used on both paired vectors; scenarios with fewer targets retain NaNs for unscheduled targets before each resample.

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| ampscale_0.7 — recovery | pS=0.0485436893204; pN=0.106796116505; Δ=-0.0582524271845 [-0.106796116505, -0.0194174757282] | pS=0.0485436893204; pN=0.106796116505; Δ=-0.0582524271845 [-0.106796116505, -0.0194174757282] | MATCH | Paired target means, n=103. |
| ampscale_0.7 — trigger | pS=0.466019417476; pN=0.52427184466; Δ=-0.0582524271845 [-0.116504854369, -0.00970873786408] | pS=0.466019417476; pN=0.52427184466; Δ=-0.0582524271845 [-0.116504854369, -0.00970873786408] | MATCH | Paired target means, n=103. |
| ampscale_1.3 — recovery | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| ampscale_1.3 — trigger | pS=0.553398058252; pN=0.52427184466; Δ=0.0291262135922 [-0.00970873786408, 0.0776699029126] | pS=0.553398058252; pN=0.52427184466; Δ=0.0291262135922 [-0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| cadence_alt — recovery | pS=0.151515151515; pN=0.0909090909091; Δ=0.0606060606061 [0, 0.151573426573] | pS=0.151515151515; pN=0.0909090909091; Δ=0.0606060606061 [0, 0.151573426573] | MATCH | Paired target means, n=33. |
| cadence_alt — trigger | pS=0.606060606061; pN=0.575757575758; Δ=0.030303030303 [-0.0666666666667, 0.135165847666] | pS=0.606060606061; pN=0.575757575758; Δ=0.030303030303 [-0.0666666666667, 0.135165847666] | MATCH | Paired target means, n=33. |
| dropout — recovery | pS=0.0394736842105; pN=0.0921052631579; Δ=-0.0526315789474 [-0.105263157895, -0.0121951219512] | pS=0.0394736842105; pN=0.0921052631579; Δ=-0.0526315789474 [-0.105263157895, -0.0121951219512] | MATCH | Paired target means, n=76. |
| dropout — trigger | pS=0.578947368421; pN=0.578947368421; Δ=0 [-0.0641233766234, 0.0641025641026] | pS=0.578947368421; pN=0.578947368421; Δ=0 [-0.0641233766234, 0.0641025641026] | MATCH | Paired target means, n=76. |
| ladder_g1r1 — recovery | pS=0.0679611650485; pN=0.106796116505; Δ=-0.0388349514563 [-0.0776699029126, -0.00970873786408] | pS=0.0679611650485; pN=0.106796116505; Δ=-0.0388349514563 [-0.0776699029126, -0.00970873786408] | MATCH | Paired target means, n=103. |
| ladder_g1r1 — trigger | pS=0.47572815534; pN=0.52427184466; Δ=-0.0485436893204 [-0.0970873786408, 0] | pS=0.47572815534; pN=0.52427184466; Δ=-0.0485436893204 [-0.0970873786408, 0] | MATCH | Paired target means, n=103. |
| ladder_g1r2 — recovery | pS=0.0873786407767; pN=0.106796116505; Δ=-0.0194174757282 [-0.0485436893204, 0] | pS=0.0873786407767; pN=0.106796116505; Δ=-0.0194174757282 [-0.0485436893204, 0] | MATCH | Paired target means, n=103. |
| ladder_g1r2 — trigger | pS=0.485436893204; pN=0.52427184466; Δ=-0.0388349514563 [-0.0873786407767, 0.000242718446601] | pS=0.485436893204; pN=0.52427184466; Δ=-0.0388349514563 [-0.0873786407767, 0.000242718446601] | MATCH | Paired target means, n=103. |
| ladder_g1r3 — recovery | pS=0.0970873786408; pN=0.106796116505; Δ=-0.00970873786408 [-0.0291262135922, 0] | pS=0.0970873786408; pN=0.106796116505; Δ=-0.00970873786408 [-0.0291262135922, 0] | MATCH | Paired target means, n=103. |
| ladder_g1r3 — trigger | pS=0.495145631068; pN=0.52427184466; Δ=-0.0291262135922 [-0.0776699029126, 0.00970873786408] | pS=0.495145631068; pN=0.52427184466; Δ=-0.0291262135922 [-0.0776699029126, 0.00970873786408] | MATCH | Paired target means, n=103. |
| ladder_g2r1 — recovery | pS=0.0970873786408; pN=0.106796116505; Δ=-0.00970873786408 [-0.0291262135922, 0] | pS=0.0970873786408; pN=0.106796116505; Δ=-0.00970873786408 [-0.0291262135922, 0] | MATCH | Paired target means, n=103. |
| ladder_g2r1 — trigger | pS=0.52427184466; pN=0.52427184466; Δ=0 [-0.0286658881036, 0.0286658881036] | pS=0.52427184466; pN=0.52427184466; Δ=0 [-0.0286658881036, 0.0286658881036] | MATCH | Paired target means, n=103. Zero discordances; exact one-sided discordance U95=0.0286658881036. |
| ladder_g2r3 — recovery | pS=0.126213592233; pN=0.106796116505; Δ=0.0194174757282 [0, 0.0485436893204] | pS=0.126213592233; pN=0.106796116505; Δ=0.0194174757282 [0, 0.0485436893204] | MATCH | Paired target means, n=103. |
| ladder_g2r3 — trigger | pS=0.543689320388; pN=0.52427184466; Δ=0.0194174757282 [0, 0.0485436893204] | pS=0.543689320388; pN=0.52427184466; Δ=0.0194174757282 [0, 0.0485436893204] | MATCH | Paired target means, n=103. |
| ladder_g3r1 — recovery | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| ladder_g3r1 — trigger | pS=0.553398058252; pN=0.52427184466; Δ=0.0291262135922 [-0.00970873786408, 0.0776699029126] | pS=0.553398058252; pN=0.52427184466; Δ=0.0291262135922 [-0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| ladder_g3r2 — recovery | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| ladder_g3r2 — trigger | pS=0.553398058252; pN=0.52427184466; Δ=0.0291262135922 [-0.00970873786408, 0.0776699029126] | pS=0.553398058252; pN=0.52427184466; Δ=0.0291262135922 [-0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| ladder_g3r3 — recovery | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | pS=0.145631067961; pN=0.106796116505; Δ=0.0388349514563 [0.00970873786408, 0.0776699029126] | MATCH | Paired target means, n=103. |
| ladder_g3r3 — trigger | pS=0.572815533981; pN=0.52427184466; Δ=0.0485436893204 [0.00970873786408, 0.0970873786408] | pS=0.572815533981; pN=0.52427184466; Δ=0.0485436893204 [0.00970873786408, 0.0970873786408] | MATCH | Paired target means, n=103. |
| phase_1 — recovery | pS=0.116504854369; pN=0.106796116505; Δ=0.00970873786408 [-0.0194174757282, 0.0388349514563] | pS=0.116504854369; pN=0.106796116505; Δ=0.00970873786408 [-0.0194174757282, 0.0388349514563] | MATCH | Paired target means, n=103. |
| phase_1 — trigger | pS=0.504854368932; pN=0.52427184466; Δ=-0.0194174757282 [-0.0776699029126, 0.0291262135922] | pS=0.504854368932; pN=0.52427184466; Δ=-0.0194174757282 [-0.0776699029126, 0.0291262135922] | MATCH | Paired target means, n=103. |
| phase_2 — recovery | pS=0.165048543689; pN=0.106796116505; Δ=0.0582524271845 [0.0194174757282, 0.106796116505] | pS=0.165048543689; pN=0.106796116505; Δ=0.0582524271845 [0.0194174757282, 0.106796116505] | MATCH | Paired target means, n=103. |
| phase_2 — trigger | pS=0.543689320388; pN=0.52427184466; Δ=0.0194174757282 [-0.0388349514563, 0.0776699029126] | pS=0.543689320388; pN=0.52427184466; Δ=0.0194174757282 [-0.0388349514563, 0.0776699029126] | MATCH | Paired target means, n=103. |
| redilution — recovery | pS=0; pN=0.35; Δ=-0.35 [-0.571428571429, -0.142857142857] | pS=0; pN=0.35; Δ=-0.35 [-0.571428571429, -0.142857142857] | MATCH | Paired target means, n=20. |
| redilution — trigger | pS=0.25; pN=0.7; Δ=-0.45 [-0.705882352941, -0.173913043478] | pS=0.25; pN=0.7; Δ=-0.45 [-0.705882352941, -0.173913043478] | MATCH | Paired target means, n=20. |
| recovery contrast min/max | min -0.35 (redilution); max 0.0606060606061 (cadence_alt) | min -0.35 (redilution); max 0.0606060606061 (cadence_alt) | MATCH | Selected extrema across all eligible scenario contrasts. |
| trigger contrast min/max | min -0.45 (redilution); max 0.0485436893204 (ladder_g3r3) | min -0.45 (redilution); max 0.0485436893204 (ladder_g3r3) | MATCH | Selected extrema across all eligible scenario contrasts. |

## Recovery surface: W_g × published amplitude

W_g bins are `<15`, `[15,41)`, `[41,84)`, `[84,217)`, `≥217`; amplitude bins are `[0.5,2)`, `[2,5)`, `[5,10)`, `[10,30)`, `≥30` ppt. `k/n` is the raw window count. `p` is the target-equal cell estimate, which can differ from `k/n` when one target contributes multiple windows to a cell.

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| W_g <15, A [0.5,2) | k/n=0/2; targets=2; p=— [—, —] | k/n=0/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g <15, A [2,5) | k/n=0/11; targets=11; p=0 [0, 0] | k/n=0/11; targets=11; p=0 [0, 0] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g <15, A [5,10) | k/n=0/31; targets=31; p=0 [0, 0] | k/n=0/31; targets=31; p=0 [0, 0] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g <15, A [10,30) | k/n=5/46; targets=45; p=0.111111111111 [0.0222222222222, 0.2] | k/n=5/46; targets=45; p=0.111111111111 [0.0222222222222, 0.2] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g <15, A ≥30 | k/n=2/9; targets=9; p=0.222222222222 [0, 0.555555555556] | k/n=2/9; targets=9; p=0.222222222222 [0, 0.555555555556] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [15,41), A [0.5,2) | k/n=0/2; targets=2; p=— [—, —] | k/n=0/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [15,41), A [2,5) | k/n=0/2; targets=2; p=— [—, —] | k/n=0/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [15,41), A [5,10) | k/n=0/1; targets=1; p=— [—, —] | k/n=0/1; targets=1; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [41,84), A [0.5,2) | k/n=0/2; targets=2; p=— [—, —] | k/n=0/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [41,84), A [2,5) | k/n=0/11; targets=11; p=0 [0, 0] | k/n=0/11; targets=11; p=0 [0, 0] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [41,84), A [5,10) | k/n=0/30; targets=30; p=0 [0, 0] | k/n=0/30; targets=30; p=0 [0, 0] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [41,84), A [10,30) | k/n=4/44; targets=44; p=0.0909090909091 [0.0227272727273, 0.181818181818] | k/n=4/44; targets=44; p=0.0909090909091 [0.0227272727273, 0.181818181818] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [41,84), A ≥30 | k/n=5/9; targets=9; p=0.555555555556 [0.222222222222, 0.888888888889] | k/n=5/9; targets=9; p=0.555555555556 [0.222222222222, 0.888888888889] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [84,217), A [0.5,2) | k/n=0/2; targets=2; p=— [—, —] | k/n=0/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [84,217), A [2,5) | k/n=1/2; targets=2; p=— [—, —] | k/n=1/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [84,217), A [5,10) | k/n=1/2; targets=2; p=— [—, —] | k/n=1/2; targets=2; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g [84,217), A [10,30) | k/n=0/1; targets=1; p=— [—, —] | k/n=0/1; targets=1; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g ≥217, A [0.5,2) | k/n=0/4; targets=4; p=— [—, —] | k/n=0/4; targets=4; p=— [—, —] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g ≥217, A [2,5) | k/n=3/13; targets=13; p=0.230769230769 [0, 0.461538461538] | k/n=3/13; targets=13; p=0.230769230769 [0, 0.461538461538] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g ≥217, A [5,10) | k/n=12/32; targets=32; p=0.375 [0.21875, 0.53125] | k/n=12/32; targets=32; p=0.375 [0.21875, 0.53125] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g ≥217, A [10,30) | k/n=26/44; targets=44; p=0.590909090909 [0.431818181818, 0.727272727273] | k/n=26/44; targets=44; p=0.590909090909 [0.431818181818, 0.727272727273] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |
| W_g ≥217, A ≥30 | k/n=8/9; targets=9; p=0.888888888889 [0.666666666667, 1] | k/n=8/9; targets=9; p=0.888888888889 [0.666666666667, 1] | MATCH | Binned nominal-B rows with half-open frozen edges; target-cluster cell bootstrap when ≥5 targets. |

## Chance match

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| chance match derangements | 10000 | 10000 | MATCH | Permuted 103 target truth lists with no fixed points; all three K rows move together. |
| chance match accidental_recovery_rate_mean | 0 | 0 | MATCH | Permuted 103 target truth lists with no fixed points; all three K rows move together. |
| chance match accidental_recovery_rate_p95 | 0 | 0 | MATCH | Permuted 103 target truth lists with no fixed points; all three K rows move together. |
| chance match accidental_any_mode_rate_mean | 0 | 0 | MATCH | Permuted 103 target truth lists with no fixed points; all three K rows move together. |
| chance match accidental_any_mode_rate_p95 | 0 | 0 | MATCH | Permuted 103 target truth lists with no fixed points; all three K rows move together. |

## README.md audit

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| README run-matrix sentence | 3,089/3,089; 0 failures; 309 B, 309 A, 824 ladder, 206 phase, 206 ampscale, 76 dropout, 33 cadence_alt, 20 redilution, 106 controls, 1,000 nulls | same | MATCH | The run-universe table above re-counts every component. |
| README cross-platform guard | 17 newline-identical outputs; 2 named columns; 76 rows; max relative 2.1×10⁻¹⁶ | 17; 2; 76; 2.06e-16 | MATCH | Compared the laptop and authoritative metric trees independently. |
| README P5/P4/trigger rows | P5 19/1,000, 0.019, U95 0.0278, FAIL; P4 0.217 [0.172,0.262]; trigger 0.557 [0.518,0.602] | P5 19/1000, 0.019, U95 0.0278, FAIL; P4 0.217 [0.172,0.262]; trigger 0.557 [0.518,0.602] | MATCH | Rounded the exact raw re-derivations to README precision. |
| README arm-A row | recovery 0.346 [0.298,0.395]; trigger 0.440 [0.392,0.492] | recovery 0.346 [0.298,0.395]; trigger 0.440 [0.392,0.492] | MATCH | Applied the same target algebra and bootstrap to nominal arm A. |
| README paired/native/chance rows and 2×2 prose | all displayed values | all exact values in paired/native/chance tables above | MATCH | Reconstructed from raw B/control JSONs and manifest pairings. |
| README recovery scenario table | 15 scenario rows rounded to 3 decimals | 15/15 exact rows match before rounding | MATCH | See the recovery rows in the exact contrast table above. |
| README W_g≥217 surface headline | p 0.23/0.38/0.59/0.89; targets 13/32/44/9 | p 0.23/0.38/0.59/0.89; targets 13/32/44/9 | MATCH | Selected amplitude bins 2–5 from the independent surface. |
| README W_g<15 surface headline | p 0.00/0.00/0.11/0.22; targets 11/31/45/9 | p 0.00/0.00/0.11/0.22; targets 11/31/45/9 | MATCH | Selected amplitude bins 2–5 from the independent surface. |
| README K0/K1/K2 recovery means | 0.07 / 0.11 / 0.48 | 0.07 / 0.11 / 0.48 | MATCH | Counted 7/103, 11/103, and 49/103. |
| README descriptive key numbers | K2 confirmed 62/62 trigger, 22/62 recovery; K2 not-detected 10/17 recovery; K1 confirmed 3/41 recovery; reuse 106/309, 36 once, max 12; 309 usable A/B pairs | same | MATCH | Rebuilt all three admitted descriptive tables; detailed cells follow. |
| README structural numerals | run date 2026-09-03; tag frozen-2026-08-01; gen2; rule 1; 95%; Amendment 4; F5–F7 | consistent with run manifest, frozen tag, generation ID/schema, metrics spec, and figure files | MATCH | These are provenance/method identifiers rather than estimates. |

## Descriptive post-launch README and sidecars

`d2_descriptives.README.md` quotes no empirical estimate or sample count; its numerals (`item 5`, `F08/F11/F38`, `95-prefix`, `P4/P5`) are ruling, field, ID-prefix, and endpoint identifiers. The quantitative outputs named by that README are independently checked below.

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| descriptive manifest nominal_b_scheduled | 309 | 309 | MATCH | Re-counted independently reconstructed descriptive rows. |
| descriptive manifest nominal_b_scored | 309 | 309 | MATCH | Re-counted independently reconstructed descriptive rows. |
| descriptive manifest nominal_b_usable | 309 | 309 | MATCH | Re-counted independently reconstructed descriptive rows. |
| descriptive manifest k_template_status_cells | 18 | 18 | MATCH | Re-counted independently reconstructed descriptive rows. |
| descriptive manifest unique_controls | 106 | 106 | MATCH | Re-counted independently reconstructed descriptive rows. |
| descriptive manifest pairs | 309 | 309 | MATCH | Re-counted independently reconstructed descriptive rows. |
| descriptive manifest pairs_usable | 309 | 309 | MATCH | Re-counted independently reconstructed descriptive rows. |
| d2_arm_a_b_pairs.csv | 309 rows | 309 rows, rowwise equal | MATCH | Rejoined nominal A/B by (TIC,K) and recomputed D/R. |
| d2_control_reuse_source.csv | 106 rows | 106 rows, rowwise equal | MATCH | Recounted and sorted controls independently. |
| descriptive README/manifest SHA bindings | 36 recorded hashes | all equal | MATCH | Hashed all declared inputs, outputs, script, frozen files, campaign files, and reuse-meta files. |

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| K0 not_detected recovery | n=76; usable=76; k=6; p=0.0789473684211; W_g=2/7/20 | n=76; usable=76; k=6; p=0.0789473684211; W_g=2/7/20 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K0 not_detected trigger | n=76; usable=76; k=6; p=0.0789473684211; W_g=2/7/20 | n=76; usable=76; k=6; p=0.0789473684211; W_g=2/7/20 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K0 candidate recovery | n=1; usable=1; k=0; p=0; W_g=0/0/0 | n=1; usable=1; k=0; p=0; W_g=0/0/0 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K0 candidate trigger | n=1; usable=1; k=0; p=0; W_g=0/0/0 | n=1; usable=1; k=0; p=0; W_g=0/0/0 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K0 confirmed recovery | n=26; usable=26; k=1; p=0.0384615384615; W_g=5/6/23 | n=26; usable=26; k=1; p=0.0384615384615; W_g=5/6/23 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K0 confirmed trigger | n=26; usable=26; k=18; p=0.692307692308; W_g=5/6/23 | n=26; usable=26; k=18; p=0.692307692308; W_g=5/6/23 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K1 not_detected recovery | n=55; usable=55; k=5; p=0.0909090909091; W_g=8/58/97 | n=55; usable=55; k=5; p=0.0909090909091; W_g=8/58/97 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K1 not_detected trigger | n=55; usable=55; k=12; p=0.218181818182; W_g=8/58/97 | n=55; usable=55; k=12; p=0.218181818182; W_g=8/58/97 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K1 candidate recovery | n=7; usable=7; k=3; p=0.428571428571; W_g=54/63/115 | n=7; usable=7; k=3; p=0.428571428571; W_g=54/63/115 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K1 candidate trigger | n=7; usable=7; k=4; p=0.571428571429; W_g=54/63/115 | n=7; usable=7; k=4; p=0.571428571429; W_g=54/63/115 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K1 confirmed recovery | n=41; usable=41; k=3; p=0.0731707317073; W_g=52/62/127 | n=41; usable=41; k=3; p=0.0731707317073; W_g=52/62/127 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K1 confirmed trigger | n=41; usable=41; k=38; p=0.926829268293; W_g=52/62/127 | n=41; usable=41; k=38; p=0.926829268293; W_g=52/62/127 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K2 not_detected recovery | n=17; usable=17; k=10; p=0.588235294118; W_g=100/436/461 | n=17; usable=17; k=10; p=0.588235294118; W_g=100/436/461 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K2 not_detected trigger | n=17; usable=17; k=13; p=0.764705882353; W_g=100/436/461 | n=17; usable=17; k=13; p=0.764705882353; W_g=100/436/461 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K2 candidate recovery | n=24; usable=24; k=17; p=0.708333333333; W_g=373/443/478 | n=24; usable=24; k=17; p=0.708333333333; W_g=373/443/478 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K2 candidate trigger | n=24; usable=24; k=19; p=0.791666666667; W_g=373/443/478 | n=24; usable=24; k=19; p=0.791666666667; W_g=373/443/478 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K2 confirmed recovery | n=62; usable=62; k=22; p=0.354838709677; W_g=359/421/786 | n=62; usable=62; k=22; p=0.354838709677; W_g=359/421/786 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |
| K2 confirmed trigger | n=62; usable=62; k=62; p=1; W_g=359/421/786 | n=62; usable=62; k=62; p=1; W_g=359/421/786 | MATCH | Scheduled-denominator cell; W_g shown as min/median/max. |

## Provenance spot-check

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| 9200211870721330000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9200556504071330000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9201674865431221000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9201929370351130000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9202388156711230000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9202388156712220000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9203131099451220200 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9203751997991120000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9204153372241220000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9207124068091220000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9208004208121220010 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9219440494271330000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9301599731522220000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9306311612220220000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9400000000000000000 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9400000000000000104 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9400000000000000236 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9400000000000000248 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9400000000000000345 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |
| 9400000000000000860 | shard/result/completion/generation all agree | shard=True, result=True, completion=True, generation=True | MATCH | Random without replacement, PCG64 seed 20260903. |

| quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation |
|---|---:|---:|---|---|
| truth file shard_manifest.csv | 826016d77a7228d2737f1f1306fb0024d5b98c33d8c5aa4154dfb02142852fc4 | 826016d77a7228d2737f1f1306fb0024d5b98c33d8c5aa4154dfb02142852fc4 | MATCH | SHA-256 over the raw generation truth file. |
| truth file injected_modes.csv | ea659c6ce712910d3ef3d014b4e29f7ce40aeb9785a910de9f55123b14cc87b4 | ea659c6ce712910d3ef3d014b4e29f7ce40aeb9785a910de9f55123b14cc87b4 | MATCH | SHA-256 over the raw generation truth file. |
| truth file rejected_modes.csv | b4f06c9c2515e9383734ad2fcae12c019f22b7111a0b51ef061e9c00212517a5 | b4f06c9c2515e9383734ad2fcae12c019f22b7111a0b51ef061e9c00212517a5 | MATCH | SHA-256 over the raw generation truth file. |
| truth file excluded_targets.csv | b6d86277900b8287b787359838cc4b97959405d229f6c2999dfdfeb69022cefd | b6d86277900b8287b787359838cc4b97959405d229f6c2999dfdfeb69022cefd | MATCH | SHA-256 over the raw generation truth file. |
| truth file shard_index.txt | fd934d755d4e54ca07c61ff62ac81e190e31828f1d8f81097d6e2614433684ef | fd934d755d4e54ca07c61ff62ac81e190e31828f1d8f81097d6e2614433684ef | MATCH | SHA-256 over the raw generation truth file. |
| truth file pilot_shard_index.txt | 48bb5e7157a8a69fcefea859b0d4eeac8cd6f78b6864a986f50ec621e339687b | 48bb5e7157a8a69fcefea859b0d4eeac8cd6f78b6864a986f50ec621e339687b | MATCH | SHA-256 over the raw generation truth file. |

## Every MISMATCH and likely cause

None.

## Exact code run

Verifier SHA-256: `d0653b36ee19f236512da12df1c2a646e3e086c0e71cf7a0e2eae8891ad9ca05`

Invocation: `.venv-gen/bin/python -m py_compile /tmp/g5_verify_d2.py && .venv-gen/bin/python /tmp/g5_verify_d2.py`

```python
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path("/Users/jackneo/Documents/vonhippel-base9/astro-wd")
BUNDLE = ROOT / "generalization/results/2026-09-04_d2"
METRICS = BUNDLE / "metrics"
DESC = BUNDLE / "descriptive_postlaunch"
SHARDS = ROOT / "outputs/generalization/d2_sync/d2_shards_gen2"
STARS = ROOT / "outputs/generalization/d2_sync/d2_run/stars"
BOOT_B = 2000
BOOT_SEED = 20260830
SPOT_SEED = 20260903
CHANCE_SEED = 20260829
SIDEREAL = 1.00273790935
AMP_EDGES = [0.5, 2.0, 5.0, 10.0, 30.0]
WG_EDGES = [15, 41, 84, 217]

# I read scripts/run_catalog_lomb_scargle.py:254-280 before this import.
# This is the only campaign/frozen computation imported by this verifier.
sys.path.insert(0, str(ROOT / "scripts/generalization"))
from frozen_api import overall_result  # noqa: E402


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def classify(freq: float, truth: list[float], tol: float) -> str:
    kinds: set[str] = set()
    for ft in truth:
        if abs(freq - ft) <= tol:
            kinds.add("direct")
        if abs(freq - 2.0 * ft) <= tol or abs(freq - 0.5 * ft) <= tol:
            kinds.add("harmonic")
        for k in (1, 2):
            for sign in (-1.0, 1.0):
                if abs(freq - abs(ft + sign * k * SIDEREAL)) <= tol:
                    kinds.add("window_alias")
    if not kinds:
        return "unmatched"
    return next(iter(kinds)) if len(kinds) == 1 else "ambiguous"


def wilson(k: int, n: int) -> tuple[float, float, float]:
    z = 1.959963984540054
    p = k / n
    den = 1.0 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, mid - half), min(1.0, mid + half)


def cp_upper(k: int, n: int) -> float:
    return float(beta.ppf(0.95, k + 1, n - k)) if k < n else 1.0


def same(a, b, tol=2e-12) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    if isinstance(a, (float, np.floating, int, np.integer)) and isinstance(
        b, (float, np.floating, int, np.integer)
    ):
        return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
    return str(a) == str(b)


mismatches: list[str] = []


def check(label: str, got, want, tol=2e-12) -> bool:
    ok = same(got, want, tol)
    if not ok:
        mismatches.append(f"{label}: file={want!r}, rederived={got!r}")
    return ok


def frame_check(label: str, got: pd.DataFrame, want: pd.DataFrame, keys: list[str], cols: list[str]) -> bool:
    g = got.sort_values(keys).reset_index(drop=True)
    w = want.sort_values(keys).reset_index(drop=True)
    if list(g.columns) != list(w.columns) or len(g) != len(w):
        mismatches.append(
            f"{label}: shape/columns differ: got {g.shape}/{list(g.columns)}, want {w.shape}/{list(w.columns)}"
        )
        return False
    for i in range(len(g)):
        for c in cols:
            if not same(g.at[i, c], w.at[i, c]):
                mismatches.append(f"{label} row {i} col {c}: file={w.at[i,c]!r}, rederived={g.at[i,c]!r}")
                return False
    return True


id_types = {
    "campaign_id": str,
    "template_source_id": str,
    "control_campaign_id": str,
    "shard_sha256": str,
}
manifest = pd.read_csv(SHARDS / "shard_manifest.csv", dtype=id_types)
manifest["control_campaign_id"] = manifest["control_campaign_id"].fillna("")
injected = pd.read_csv(SHARDS / "injected_modes.csv", dtype={"campaign_id": str})
completion = pd.read_csv(
    BUNDLE / "run/completion.csv", dtype={"source_id": str, "result_sha256": str, "provenance_sha256": str}
)
generation = json.loads((SHARDS / "generation_manifest.json").read_text())
frozen_generation = json.loads((BUNDLE / "run/generation_manifest.json").read_text())
run_manifest = json.loads((BUNDLE / "run/manifest.json").read_text())
metrics_manifest = json.loads((METRICS / "manifest.json").read_text())

freqs = injected.groupby("campaign_id")["frequency_per_day"].apply(list).to_dict()
dominant: dict[str, float] = {}
dominant_amp: dict[str, float] = {}
for sid, group in injected.groupby("campaign_id", sort=False):
    row = group.loc[group["amp_tess_ppt"].idxmax()]
    dominant[sid] = float(row["frequency_per_day"])
    dominant_amp[sid] = float(row["amp_tess_ppt"])

completion_by_id = completion.set_index("source_id")
raw_rows: list[dict] = []
all_sidecars_ok = True
for r in manifest.itertuples(index=False):
    sid = r.campaign_id
    result_path = STARS / f"{sid}.json"
    prov_path = STARS / f"{sid}.prov.json"
    result = json.loads(result_path.read_text())
    prov = json.loads(prov_path.read_text())
    result_digest, prov_digest = sha(result_path), sha(prov_path)
    c = completion_by_id.loc[sid]
    side_ok = (
        c["status"] == "complete"
        and result_digest == c["result_sha256"] == prov["result_sha256"]
        and prov_digest == c["provenance_sha256"]
        and prov["source_id"] == sid == str(result["source_id"])
        and prov["generation_id"] == generation["generation_id"]
        and prov["shard_sha256"] == r.shard_sha256
        and prov["passes"] == ["low", "high"]
    )
    all_sidecars_ok &= side_ok
    if not side_ok and len(mismatches) < 20:
        mismatches.append(f"completion/sidecar chain failed for {sid}")
    best = overall_result(result)
    f = best["best_frequency_per_day"]
    truth = freqs.get(sid, [])
    dom = dominant.get(sid)
    tol = 1.5 / float(result["baseline_days"])
    match_dom = (
        classify(float(f), [dom], tol)
        if f is not None and dom is not None and np.isfinite(float(f))
        else "unscored"
    )
    match_any = (
        classify(float(f), truth, tol)
        if f is not None and truth and np.isfinite(float(f))
        else "unscored"
    )
    low_avail = bool(result["passes"]["low"].get("available", True))
    high_avail = bool(result["passes"]["high"].get("available", True))
    usable = bool(result.get("complete") and low_avail and high_avail and best["blind_status"] != "missing")
    raw_rows.append(
        {
            "sid": sid,
            "arm": r.arm,
            "scenario": r.scenario,
            "tic": str(int(r.tic)),
            "template_k": int(r.template_k),
            "template_source_id": r.template_source_id,
            "template_status": r.template_status,
            "wg": int(r.template_wg_contrasts),
            "control_sid": r.control_campaign_id,
            "best_status": best["blind_status"],
            "best_pass": best["best_pass"],
            "best_freq": float(f) if f is not None else math.nan,
            "baseline": float(result["baseline_days"]),
            "match_dom": match_dom,
            "match_any": match_any,
            "usable": usable,
            "low_available": low_avail,
            "high_available": high_avail,
            "D": best["blind_status"] == "confirmed",
            "R": best["blind_status"] == "confirmed" and match_dom == "direct",
            "amp": dominant_amp.get(sid, math.nan),
            "truth_period": (1.0 / dom) if dom else math.nan,
            "result_sha": result_digest,
            "prov_sha": prov_digest,
        }
    )
raw = pd.DataFrame(raw_rows)

# Full-universe and provenance checks.
expected_matrix = {
    "B:nominal": 309,
    "A:nominal": 309,
    "B:ladder": 8 * 103,
    "B:phase": 2 * 103,
    "B:ampscale": 2 * 103,
    "B:dropout": 76,
    "B:cadence_alt": 33,
    "B:redilution": 20,
    "ctrl:control": 106,
    "gauss_null:gauss_null": 1000,
}
matrix = {
    "B:nominal": int(((manifest.arm == "B") & (manifest.scenario == "nominal")).sum()),
    "A:nominal": int(((manifest.arm == "A") & (manifest.scenario == "nominal")).sum()),
    "B:ladder": int(((manifest.arm == "B") & manifest.scenario.str.startswith("ladder_")).sum()),
    "B:phase": int(((manifest.arm == "B") & manifest.scenario.str.startswith("phase_")).sum()),
    "B:ampscale": int(((manifest.arm == "B") & manifest.scenario.str.startswith("ampscale_")).sum()),
    "B:dropout": int(((manifest.arm == "B") & (manifest.scenario == "dropout")).sum()),
    "B:cadence_alt": int(((manifest.arm == "B") & (manifest.scenario == "cadence_alt")).sum()),
    "B:redilution": int(((manifest.arm == "B") & (manifest.scenario == "redilution")).sum()),
    "ctrl:control": int((manifest.arm == "ctrl").sum()),
    "gauss_null:gauss_null": int((manifest.arm == "gauss_null").sum()),
}
for k, v in expected_matrix.items():
    check(f"run matrix {k}", matrix[k], v)
check("run matrix total", len(manifest), 3089)
check("completion rows", len(completion), 3089)
check("completion unique IDs", completion.source_id.nunique(), 3089)
check("completion complete statuses", int((completion.status == "complete").sum()), 3089)
check("run manifest source_count", run_manifest["source_count"], 3089)
check("run manifest completed_now", run_manifest["completed_now"], 3089)
check("run manifest failures", len(run_manifest["failures"]), 0)
id_sets_ok = set(manifest.campaign_id) == set(completion.source_id)
check("manifest ID set equals completion", id_sets_ok, True)
check("all completion/sidecar chains", all_sidecars_ok, True)
check("frozen generation manifest copy", frozen_generation == generation, True)
check(
    "frozen completion copy",
    sha(BUNDLE / "run/completion.csv"),
    sha(ROOT / "outputs/generalization/d2_sync/d2_run/completion.csv"),
)
check(
    "frozen run manifest copy",
    sha(BUNDLE / "run/manifest.json"),
    sha(ROOT / "outputs/generalization/d2_sync/d2_run/manifest.json"),
)
for copied_truth in ("shard_manifest.csv", "injected_modes.csv", "rejected_modes.csv"):
    check(
        f"frozen truth copy {copied_truth}",
        sha(BUNDLE / "run" / copied_truth),
        sha(SHARDS / copied_truth),
    )
gen_ids = {
    generation["generation_id"],
    frozen_generation["generation_id"],
    run_manifest["generation_id"],
    metrics_manifest["generation_id"],
}
check("generation IDs across manifests", len(gen_ids), 1)
basis_keys = ("inputs_sha256", "template_shas", "frozen_sha256", "generation_code_sha256", "args")
basis = {k: generation[k] for k in basis_keys}
gen_recalc = hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest()
check("generation id basis", gen_recalc, generation["generation_id"])

truth_sha_rows = []
for name, recorded in generation["outputs_sha256"].items():
    actual = sha(SHARDS / name)
    ok = check(f"truth SHA {name}", actual, recorded)
    truth_sha_rows.append({"file": name, "recorded": recorded, "actual": actual, "match": ok})

spot_ids = sorted(
    np.random.Generator(np.random.PCG64(SPOT_SEED)).choice(
        manifest.campaign_id.to_numpy(), size=20, replace=False
    ).tolist()
)
spot_rows = []
manifest_by_id = manifest.set_index("campaign_id")
for sid in spot_ids:
    r = manifest_by_id.loc[sid]
    prov = json.loads((STARS / f"{sid}.prov.json").read_text())
    c = completion_by_id.loc[sid]
    shard_actual = sha(SHARDS / f"{sid}.csv.gz")
    result_actual = sha(STARS / f"{sid}.json")
    prov_actual = sha(STARS / f"{sid}.prov.json")
    flags = {
        "shard": shard_actual == r.shard_sha256 == prov["shard_sha256"] == generation["shard_sha256"][sid],
        "result": result_actual == prov["result_sha256"] == c["result_sha256"],
        "completion": c["status"] == "complete" and prov_actual == c["provenance_sha256"],
        "generation": prov["generation_id"] == generation["generation_id"],
    }
    for name, ok in flags.items():
        check(f"spot {sid} {name}", ok, True)
    spot_rows.append({"sid": sid, **flags, "all": all(flags.values())})

# Frozen per_star is checked against the independently scored raw JSONs.
frozen_ps = pd.read_csv(METRICS / "per_star.csv", dtype={"sid": str, "cluster": str, "control_campaign_id": str})
frozen_ps["control_campaign_id"] = frozen_ps["control_campaign_id"].fillna("")
raw_score = raw[["sid", "best_status", "best_pass", "best_freq", "low_available", "high_available"]].copy()
raw_score.columns = ["sid", "best_status", "best_pass", "best_frequency_per_day", "low_available", "high_available"]
want_score = frozen_ps[raw_score.columns]
raw_score_match = frame_check("raw JSON selector vs per_star", raw_score, want_score, ["sid"], list(raw_score.columns))
raw_match = raw[raw.arm.isin(["A", "B"])][["sid", "match_dom"]].rename(columns={"match_dom": "best_candidate_matches_dominant"})
want_match = frozen_ps[frozen_ps.arm.isin(["A", "B"])][["sid", "best_candidate_matches_dominant"]]
raw_score_match &= frame_check("raw JSON dominant matching vs per_star", raw_match, want_match, ["sid"], list(raw_match.columns))

# README cross-platform guard claim, independently from the two CSV trees.
laptop_dir = BUNDLE / "metrics_laptop_prefix"
mac_dir = METRICS
laptop_files = {p.relative_to(laptop_dir).as_posix() for p in laptop_dir.rglob("*") if p.is_file()}
mac_files = {p.relative_to(mac_dir).as_posix() for p in mac_dir.rglob("*") if p.is_file()}
special = {"attrition.csv", "manifest.json", "inputs_sha256.json", "per_star.csv"}
newline_identical = 0
for rel in sorted((laptop_files & mac_files) - special):
    a = re.sub(rb"\r+\n", b"\n", (laptop_dir / rel).read_bytes())
    b = re.sub(rb"\r+\n", b"\n", (mac_dir / rel).read_bytes())
    if a == b:
        newline_identical += 1
check("README guard newline-identical outputs", newline_identical, 17)
laptop_ps = pd.read_csv(laptop_dir / "per_star.csv", dtype=str).fillna("").set_index("sid").sort_index()
mac_ps = pd.read_csv(mac_dir / "per_star.csv", dtype=str).fillna("").set_index("sid").sort_index()
diff_cols, diff_union, guard_worst = [], np.zeros(len(laptop_ps), dtype=bool), 0.0
for col in laptop_ps.columns:
    unequal = (laptop_ps[col] != mac_ps[col]).to_numpy()
    if unequal.any():
        diff_cols.append(col)
        diff_union |= unequal
        x = pd.to_numeric(laptop_ps.loc[unequal, col], errors="coerce")
        y = pd.to_numeric(mac_ps.loc[unequal, col], errors="coerce")
        rel = (abs(x - y) / abs(x).where(abs(x) > 0, 1.0)).max()
        guard_worst = max(guard_worst, float(rel))
check("README guard differing columns", diff_cols == ["primary_freq", "truth_period_days"], True)
check("README guard differing rows", int(diff_union.sum()), 76)
check("README guard max relative difference", guard_worst, 2.06e-16, tol=1e-18)

# P4 nominal arm-B endpoints and clustered intervals.
clusters = np.array(sorted(str(int(t)) for t in generation["scheduled_tics"]))
rng = np.random.Generator(np.random.PCG64(BOOT_SEED))
draws = rng.integers(0, len(clusters), size=(BOOT_B, len(clusters)))
nom_b = raw[(raw.arm == "B") & (raw.scenario == "nominal")].copy()
nom_b["cluster"] = nom_b.tic


def boot_stats(values: pd.Series) -> tuple[float, float, float]:
    a = values.reindex(clusters).to_numpy(float)
    obs = a[~np.isnan(a)]
    boots = []
    for draw in draws:
        s = a[draw]
        s = s[~np.isnan(s)]
        if len(s):
            boots.append(float(s.mean()))
    return float(obs.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


p4_rows = []
frozen_cluster = pd.read_csv(METRICS / "d2_cluster_completeness.csv")
for endpoint, col in (("recovery", "R"), ("trigger", "D")):
    for denom in ("eligible", "usable"):
        if denom == "eligible":
            per_target = nom_b.groupby("cluster")[col].sum().div(3.0).reindex(clusters, fill_value=0.0)
        else:
            use = nom_b[nom_b.usable]
            per_target = use.groupby("cluster")[col].mean().reindex(clusters)
        p, lo, hi = boot_stats(per_target)
        f = frozen_cluster[
            (frozen_cluster.arm == "B")
            & (frozen_cluster.scenario == "nominal")
            & (frozen_cluster.endpoint == endpoint)
            & (frozen_cluster.denominator == denom)
        ].iloc[0]
        ok = all(
            [
                check(f"P4 {endpoint}/{denom} {q}", v, f[q])
                for q, v in (("p", p), ("lo", lo), ("hi", hi))
            ]
        )
        p4_rows.append(
            {
                "endpoint": endpoint,
                "denominator": denom,
                "file": [float(f.p), float(f.lo), float(f.hi)],
                "derived": [p, lo, hi],
                "n_targets": int(per_target.notna().sum()),
                "zero_usable": int(103 - per_target.notna().sum()) if denom == "usable" else 0,
                "match": ok,
            }
        )

nom_a_for_readme = raw[(raw.arm == "A") & (raw.scenario == "nominal")].copy()
nom_a_for_readme["cluster"] = nom_a_for_readme.tic
arm_a_rows = []
for endpoint, col in (("recovery", "R"), ("trigger", "D")):
    per_target = nom_a_for_readme.groupby("cluster")[col].sum().div(3.0).reindex(clusters, fill_value=0.0)
    stats = boot_stats(per_target)
    f = frozen_cluster[
        (frozen_cluster.arm == "A")
        & (frozen_cluster.scenario == "nominal")
        & (frozen_cluster.endpoint == endpoint)
        & (frozen_cluster.denominator == "eligible")
    ].iloc[0]
    ok = all(check(f"README arm A {endpoint} {q}", v, f[q]) for q, v in zip(("p", "lo", "hi"), stats))
    arm_a_rows.append({"endpoint": endpoint, "file": [float(f.p), float(f.lo), float(f.hi)], "derived": list(stats), "match": ok})

k_rows = []
frozen_nom_b = frozen_ps[(frozen_ps.arm == "B") & (frozen_ps.scenario == "nominal")]
for endpoint, col, fcol in (
    ("recovery", "R", None),
    ("trigger", "D", None),
):
    for k in (0, 1, 2):
        part = nom_b[nom_b.template_k == k]
        got_k = int(part[col].sum())
        fp = frozen_nom_b[frozen_nom_b.template_k == k]
        want_k = int(
            ((fp.best_status == "confirmed") & (fp.best_candidate_matches_dominant == "direct")).sum()
            if endpoint == "recovery"
            else (fp.best_status == "confirmed").sum()
        )
        ok = check(f"K{k} {endpoint} successes", got_k, want_k)
        k_rows.append({"endpoint": endpoint, "K": k, "file_k_n": [want_k, len(fp)], "derived_k_n": [got_k, len(part)], "match": ok})

# P5 from raw null JSONs.
nulls = raw[raw.arm == "gauss_null"]
null_x = int(nulls.D.sum())
null_n = len(nulls)
null_upper = cp_upper(null_x, null_n)
trigger_file = pd.read_csv(METRICS / "trigger_rates.csv")
ffp = trigger_file[trigger_file.quantity == "fpr_gaussian"].iloc[0]
p5_ok = all(
    [
        check("P5 x", null_x, int(ffp.k)),
        check("P5 n", null_n, int(ffp.n_completed)),
        check("P5 p", null_x / null_n, ffp.p),
        check("P5 CP upper", null_upper, ffp.cp_one_sided_95_upper),
        check("P5 acceptance", null_upper <= 0.005, bool(ffp["acceptance_u95_leq_0.005"])),
    ]
)

# Paired controls, target-cluster intervals, native rate, and reuse.
controls = raw[raw.arm == "ctrl"].set_index("sid")
pair_rows = []
for b in nom_b.itertuples(index=False):
    c = controls.loc[b.control_sid]
    r_c = bool(
        c.best_status == "confirmed"
        and np.isfinite(c.best_freq)
        and classify(float(c.best_freq), [dominant[b.sid]], 1.5 / float(c.baseline)) == "direct"
    )
    pair_rows.append(
        {
            "b_sid": b.sid,
            "control_sid": b.control_sid,
            "cluster": b.tic,
            "template_k": b.template_k,
            "b_status": b.best_status,
            "control_status": c.best_status,
            "b_usable": b.usable,
            "control_usable": c.usable,
            "pair_usable": bool(b.usable and c.usable),
            "D_B": b.D,
            "D_C": bool(c.D),
            "R_B": b.R,
            "R_C": r_c,
        }
    )
pairs = pd.DataFrame(pair_rows)
frozen_pairs = pd.read_csv(
    METRICS / "d2_paired_controls.csv", dtype={"b_sid": str, "control_sid": str, "cluster": str}
)
pairs_match = frame_check(
    "paired controls row table", pairs, frozen_pairs, ["b_sid"], list(pairs.columns)
)


def pair_boot(series: pd.Series) -> tuple[float, float, float]:
    per_t = series.astype(float).groupby(pairs.loc[series.index, "cluster"]).mean().reindex(clusters)
    return boot_stats(per_t)


pair_summary_rows = []
usable_pairs = pairs[pairs.pair_usable]
frozen_pair_summary = pd.read_csv(METRICS / "d2_paired_controls_summary.csv")
for endpoint in ("D", "R"):
    b = usable_pairs[f"{endpoint}_B"]
    c = usable_pairs[f"{endpoint}_C"]
    counts = {
        "both": int((b & c).sum()),
        "b_only": int((b & ~c).sum()),
        "c_only": int((~b & c).sum()),
        "neither": int((~b & ~c).sum()),
    }
    pair_stats = {
        "p_b": pair_boot(b),
        "p_c": pair_boot(c),
        "paired_diff_b_minus_c": pair_boot(b.astype(float) - c.astype(float)),
        "p_b_and_not_c": pair_boot(b & ~c),
    }
    f = frozen_pair_summary[frozen_pair_summary.endpoint == endpoint].iloc[0]
    ok = True
    for q, v in counts.items():
        ok &= check(f"paired {endpoint} {q}", v, int(f[q]))
    for label, stats in pair_stats.items():
        for suffix, v in zip(("", "_lo", "_hi"), stats):
            ok &= check(f"paired {endpoint} {label}{suffix}", v, f[f"{label}{suffix}"])
    pair_summary_rows.append(
        {
            "endpoint": endpoint,
            "counts": counts,
            "file_stats": {label: [float(f[label]), float(f[f"{label}_lo"]), float(f[f"{label}_hi"])] for label in pair_stats},
            "derived_stats": {label: list(stats) for label, stats in pair_stats.items()},
            "match": bool(ok),
        }
    )

native_x = int((controls.best_status == "confirmed").sum())
native_n = len(controls)
native_stats = wilson(native_x, native_n)
fnative = trigger_file[trigger_file.quantity == "native_trigger_rate"].iloc[0]
native_ok = all(
    [
        check("native x", native_x, round(float(fnative.p) * int(fnative.n))),
        check("native n", native_n, int(fnative.n)),
        *[check(f"native {q}", v, fnative[q]) for q, v in zip(("p", "lo", "hi"), native_stats)],
    ]
)
reuse = (
    nom_b.groupby(["control_sid", "template_source_id"])
    .agg(n_b_assignments=("sid", "size"), n_targets=("tic", "nunique"))
    .reset_index()
    .rename(columns={"control_sid": "control_campaign_id"})
)
frozen_reuse = pd.read_csv(
    METRICS / "d2_control_reuse.csv", dtype={"control_campaign_id": str, "template_source_id": str}
)
reuse_match = frame_check(
    "control reuse", reuse, frozen_reuse, ["control_campaign_id"], list(reuse.columns)
)
reuse_dist = (
    reuse.groupby("n_b_assignments")
    .agg(n_controls=("control_campaign_id", "size"), n_assignments=("n_b_assignments", "sum"))
    .reset_index()
    .to_dict("records")
)

# Eligible scenario-minus-nominal-K1 contrasts.
nom_k1 = nom_b[nom_b.template_k == 1]


def boot_mean(series: pd.Series) -> tuple[float, float, float]:
    return boot_stats(series.reindex(clusters))


contrast_rows = []
frozen_contrasts = pd.read_csv(METRICS / "d2_scenario_contrasts.csv")
for scenario_name in sorted(set(raw.loc[(raw.arm == "B") & (raw.scenario != "nominal"), "scenario"])):
    s = raw[(raw.arm == "B") & (raw.scenario == scenario_name)].copy()
    target_set = set(s.tic)
    n = nom_k1[nom_k1.tic.isin(target_set)]
    for endpoint, col in (("recovery", "R"), ("trigger", "D")):
        ys = s.groupby("tic")[col].mean().reindex(clusters)
        yn = n.groupby("tic")[col].mean().reindex(clusters)
        ps = boot_mean(ys)
        pn = boot_mean(yn)
        diff_vec = ys - yn
        diff = list(boot_mean(diff_vec))
        observed = diff_vec.dropna()
        discordance = math.nan
        interval = "paired_cluster_bootstrap_common_draws"
        if len(observed) and (observed == 0).all():
            discordance = cp_upper(0, len(observed))
            diff[1], diff[2] = -discordance, discordance
            interval = "cp_discordance_bound"
        f = frozen_contrasts[
            (frozen_contrasts.scenario == scenario_name)
            & (frozen_contrasts.endpoint == endpoint)
            & (frozen_contrasts.denominator == "eligible")
        ].iloc[0]
        ok = True
        for q, v in zip(("p_scenario", "lo_scenario", "hi_scenario"), ps):
            ok &= check(f"contrast {scenario_name}/{endpoint} {q}", v, f[q])
        for q, v in zip(("p_nominal_k1", "lo_nominal_k1", "hi_nominal_k1"), pn):
            ok &= check(f"contrast {scenario_name}/{endpoint} {q}", v, f[q])
        for q, v in zip(("diff", "diff_lo", "diff_hi"), diff):
            ok &= check(f"contrast {scenario_name}/{endpoint} {q}", v, f[q])
        ok &= check(f"contrast {scenario_name}/{endpoint} discordance", discordance, f.discordance_u95)
        ok &= check(f"contrast {scenario_name}/{endpoint} interval", interval, f.interval)
        contrast_rows.append(
            {
                "scenario": scenario_name,
                "endpoint": endpoint,
                "n": int(ys.notna().sum()),
                "file": [float(f.p_scenario), float(f.p_nominal_k1), float(f["diff"]), float(f.diff_lo), float(f.diff_hi)],
                "derived": [ps[0], pn[0], diff[0], diff[1], diff[2]],
                "discordance_u95": discordance,
                "interval": interval,
                "match": bool(ok),
            }
        )

contrast_extrema = []
for endpoint in ("recovery", "trigger"):
    sub = [x for x in contrast_rows if x["endpoint"] == endpoint]
    vals = [x["derived"][2] for x in sub]
    lo, hi = min(vals), max(vals)
    contrast_extrema.append(
        {
            "endpoint": endpoint,
            "min": lo,
            "min_scenarios": [x["scenario"] for x in sub if same(x["derived"][2], lo)],
            "max": hi,
            "max_scenarios": [x["scenario"] for x in sub if same(x["derived"][2], hi)],
        }
    )

# Nominal arm-B W_g x amplitude recovery surface.
surface_base = nom_b.copy()
surface_base["wg_bin"] = np.digitize(surface_base.wg.to_numpy(float), WG_EDGES)
surface_base["amp_bin"] = np.digitize(surface_base.amp.to_numpy(float), AMP_EDGES)
surface_rows = []
frozen_surface = pd.read_csv(METRICS / "surfaces/recovery_wg_amplitude.csv")
for (wb, ab), sub in surface_base.groupby(["wg_bin", "amp_bin"], sort=True):
    per_t = sub.R.astype(float).groupby(sub.tic).mean()
    entry = {
        "wg_bin": int(wb),
        "amp_bin": int(ab),
        "n_windows": int(len(sub)),
        "k_windows": int(sub.R.sum()),
        "n_targets": int(len(per_t)),
        "p": math.nan,
        "lo": math.nan,
        "hi": math.nan,
    }
    if len(per_t) >= 5:
        a = per_t.to_numpy(float)
        cell_rng = np.random.Generator(np.random.PCG64([BOOT_SEED, int(wb) + 7, int(ab) + 7]))
        cell_draws = cell_rng.integers(0, len(a), size=(BOOT_B, len(a)))
        boots = a[cell_draws].mean(axis=1)
        entry.update(p=float(a.mean()), lo=float(np.quantile(boots, 0.025)), hi=float(np.quantile(boots, 0.975)))
    f = frozen_surface[(frozen_surface.wg_bin == wb) & (frozen_surface.amp_bin == ab)].iloc[0]
    ok = True
    for q in ("n_windows", "k_windows", "n_targets", "p", "lo", "hi"):
        ok &= check(f"surface W{wb}/A{ab} {q}", entry[q], f[q])
    entry["file"] = [int(f.n_windows), int(f.k_windows), int(f.n_targets), float(f.p), float(f.lo), float(f.hi)]
    entry["match"] = bool(ok)
    surface_rows.append(entry)
check("surface row count", len(surface_rows), len(frozen_surface))

# Target-level derangements, all K rows moving together.
chance_rows = nom_b.copy()
targets = sorted(chance_rows.tic.unique())
t_index = {t: i for i, t in enumerate(targets)}
dom_by_target = np.array([dominant[chance_rows[chance_rows.tic == t].iloc[0].sid] for t in targets])
mode_lists = [freqs[chance_rows[chance_rows.tic == t].iloc[0].sid] for t in targets]
width = max(map(len, mode_lists))
modes = np.full((len(targets), width), np.nan)
for i, vals in enumerate(mode_lists):
    modes[i, : len(vals)] = vals
f = chance_rows.best_freq.to_numpy(float)
tol = 1.5 / chance_rows.baseline.to_numpy(float)
confirmed = chance_rows.D.to_numpy(bool) & np.isfinite(f)
t_idx = np.array([t_index[t] for t in chance_rows.tic])
chance_rng = np.random.Generator(np.random.PCG64(CHANCE_SEED))
rec_rates, any_rates = [], []
made = 0
while made < 10000:
    perm = chance_rng.permutation(len(targets))
    if (perm == np.arange(len(targets))).any():
        continue
    made += 1
    sigma = perm[t_idx]
    rec = confirmed & (np.abs(f - dom_by_target[sigma]) <= tol)
    dist = np.abs(f[:, None] - modes[sigma])
    dist = np.where(np.isnan(dist), np.inf, dist)
    any_hit = confirmed & (dist.min(axis=1) <= tol)
    rec_per_t = np.bincount(t_idx, weights=rec.astype(float)) / np.bincount(t_idx)
    any_per_t = np.bincount(t_idx, weights=any_hit.astype(float)) / np.bincount(t_idx)
    rec_rates.append(float(rec_per_t.mean()))
    any_rates.append(float(any_per_t.mean()))
chance = {
    "derangements": 10000,
    "accidental_recovery_rate_mean": float(np.mean(rec_rates)),
    "accidental_recovery_rate_p95": float(np.quantile(rec_rates, 0.95)),
    "accidental_any_mode_rate_mean": float(np.mean(any_rates)),
    "accidental_any_mode_rate_p95": float(np.quantile(any_rates, 0.95)),
}
chance_file = json.loads((METRICS / "chance_match.json").read_text())
chance_ok = all(check(f"chance {q}", v, chance_file[q]) for q, v in chance.items())

# Independently recreate every descriptive table and sidecar count.
desc_k_rows = []
for k in (0, 1, 2):
    for status in ("not_detected", "candidate", "confirmed"):
        cell = nom_b[(nom_b.template_k == k) & (nom_b.template_status == status)]
        for endpoint, col in (("recovery", "R"), ("trigger", "D")):
            n_sched, n_use, k_success = len(cell), int(cell.usable.sum()), int(cell[col].sum())
            desc_k_rows.append(
                {
                    "template_k": k,
                    "wg_stratum": {0: "wg_p10", 1: "wg_p50", 2: "wg_p90"}[k],
                    "template_status": status,
                    "endpoint": endpoint,
                    "n_scheduled": n_sched,
                    "n_usable": n_use,
                    "k_success": k_success,
                    "rate_scheduled": k_success / n_sched if n_sched else math.nan,
                    "wg_min": int(cell.wg.min()) if n_sched else math.nan,
                    "wg_median": float(cell.wg.median()) if n_sched else math.nan,
                    "wg_max": int(cell.wg.max()) if n_sched else math.nan,
                    "analysis_status": "postlaunch_descriptive",
                    "prespecified": False,
                    "interval": "none",
                }
            )
desc_k = pd.DataFrame(desc_k_rows)
frozen_desc_k = pd.read_csv(DESC / "d2_k_template_status.csv")
desc_k_match = frame_check(
    "descriptive K/status", desc_k, frozen_desc_k,
    ["template_k", "template_status", "endpoint"], list(desc_k.columns),
)


def pair_class(a: bool, b: bool) -> str:
    return "both" if a and b else "A_only" if a else "B_only" if b else "neither"


nom_a = raw[(raw.arm == "A") & (raw.scenario == "nominal")]
ab_rows = []
for b in nom_b.sort_values(["tic", "template_k"]).itertuples(index=False):
    a = nom_a[(nom_a.tic == b.tic) & (nom_a.template_k == b.template_k)].iloc[0]
    ab_rows.append(
        {
            "tic": int(b.tic), "template_k": b.template_k,
            "template_source_id": b.template_source_id, "template_status": b.template_status,
            "wg_contrasts": b.wg, "a_sid": a.sid, "b_sid": b.sid,
            "a_status": a.best_status, "b_status": b.best_status,
            "a_usable": a.usable, "b_usable": b.usable, "pair_usable": bool(a.usable and b.usable),
            "D_A": a.D, "D_B": b.D, "R_A": a.R, "R_B": b.R,
            "trigger_pair_class": pair_class(a.D, b.D),
            "recovery_pair_class": pair_class(a.R, b.R),
            "analysis_status": "postlaunch_descriptive", "prespecified": False, "interval": "none",
        }
    )
ab_pairs = pd.DataFrame(ab_rows)
frozen_ab = pd.read_csv(
    DESC / "d2_arm_a_b_pairs.csv",
    dtype={"template_source_id": str, "a_sid": str, "b_sid": str},
)
ab_match = frame_check("descriptive A/B pairs", ab_pairs, frozen_ab, ["tic", "template_k"], list(ab_pairs.columns))

reuse_source = reuse.sort_values(
    ["n_b_assignments", "control_campaign_id"], ascending=[False, True], kind="mergesort"
).reset_index(drop=True)
reuse_source.insert(0, "bar_index", np.arange(len(reuse_source)))
reuse_source["analysis_status"] = "postlaunch_descriptive"
reuse_source["prespecified"] = False
reuse_source["interval"] = "none"
frozen_reuse_source = pd.read_csv(
    DESC / "d2_control_reuse_source.csv", dtype={"control_campaign_id": str, "template_source_id": str}
)
reuse_source_match = frame_check(
    "descriptive reuse source", reuse_source, frozen_reuse_source, ["bar_index"], list(reuse_source.columns)
)
desc_manifest = json.loads((DESC / "d2_descriptives.manifest.json").read_text())
desc_counts = {
    "nominal_b_scheduled": len(nom_b),
    "nominal_b_scored": len(nom_b),
    "nominal_b_usable": int(nom_b.usable.sum()),
    "k_template_status_cells": len(desc_k),
    "unique_controls": len(reuse),
    "pairs": len(ab_pairs),
    "pairs_usable": int(ab_pairs.pair_usable.sum()),
}
desc_count_rows = []
for q, v in desc_counts.items():
    ok = check(f"descriptive manifest {q}", v, desc_manifest["counts"][q])
    desc_count_rows.append({"quantity": q, "file": desc_manifest["counts"][q], "derived": v, "match": ok})

desc_input_paths = {
    "per_star.csv": METRICS / "per_star.csv",
    "d2_control_reuse.csv": METRICS / "d2_control_reuse.csv",
    "metrics_manifest.json": METRICS / "manifest.json",
    "outputs/generalization/d2_sync/d2_shards_gen2/shard_manifest.csv": SHARDS / "shard_manifest.csv",
    "generalization/reviews/G5prep/sol_round2.md": ROOT / "generalization/reviews/G5prep/sol_round2.md",
}
desc_sidecar_checks = []
for name, recorded in desc_manifest["inputs_sha256"].items():
    actual = sha(desc_input_paths[name])
    desc_sidecar_checks.append(check(f"descriptive sidecar input {name}", actual, recorded))
for name, recorded in desc_manifest["outputs_sha256"].items():
    actual = sha(DESC / name)
    desc_sidecar_checks.append(check(f"descriptive sidecar output {name}", actual, recorded))
desc_sidecar_checks.append(
    check(
        "descriptive sidecar script",
        sha(ROOT / "scripts/generalization/descriptive/d2_descriptives.py"),
        desc_manifest["script_sha256"],
    )
)
for rel, recorded in {**desc_manifest["frozen_sha256"], **desc_manifest["campaign_sha256"]}.items():
    desc_sidecar_checks.append(check(f"descriptive sidecar source {rel}", sha(ROOT / rel), recorded))
reuse_meta = json.loads((DESC / "d2_control_reuse.meta.json").read_text())
for name, recorded in reuse_meta["inputs_sha256"].items():
    desc_sidecar_checks.append(check(f"reuse meta input {name}", sha(METRICS / name), recorded))
for name, recorded in reuse_meta["outputs_sha256"].items():
    desc_sidecar_checks.append(check(f"reuse meta output {name}", sha(DESC / name), recorded))
readme = (DESC / "d2_descriptives.README.md").read_text()
readme_empirical_numbers = re.findall(r"(?<![A-Za-z])(?:\d+\.\d+|\d+)(?:\s*%)?", readme)

bundle_sha_entries = []
for line in (BUNDLE / "SHA256SUMS").read_text().splitlines():
    recorded, rel = line.split("  ", 1)
    path = BUNDLE / rel.removeprefix("./")
    actual = sha(path)
    ok = check(f"bundle SHA256SUMS {rel}", actual, recorded)
    bundle_sha_entries.append(ok)

result = {
    "mismatches": mismatches,
    "run": {
        "matrix": matrix,
        "expected_matrix": expected_matrix,
        "total": len(manifest),
        "completion": len(completion),
        "failures": len(run_manifest["failures"]),
        "all_sidecars_ok": all_sidecars_ok,
        "generation_id": generation["generation_id"],
        "generation_rederived": gen_recalc,
        "truth_shas": truth_sha_rows,
        "bundle_sha_entries": len(bundle_sha_entries),
        "bundle_sha_all_match": all(bundle_sha_entries),
    },
    "raw_score_match": raw_score_match,
    "guard": {
        "newline_identical": newline_identical,
        "diff_columns": diff_cols,
        "diff_rows": int(diff_union.sum()),
        "max_relative_difference": guard_worst,
    },
    "p4": p4_rows,
    "arm_a": arm_a_rows,
    "k": k_rows,
    "p5": {
        "x": null_x, "n": null_n, "p": null_x / null_n, "upper": null_upper,
        "accepted": null_upper <= 0.005, "match": p5_ok,
    },
    "paired": pair_summary_rows,
    "pairs_table_match": pairs_match,
    "native": {"x": native_x, "n": native_n, "stats": native_stats, "match": native_ok},
    "reuse": {"n_controls": len(reuse), "total": int(reuse.n_b_assignments.sum()), "distribution": reuse_dist, "match": reuse_match},
    "contrasts": contrast_rows,
    "contrast_extrema": contrast_extrema,
    "surfaces": surface_rows,
    "chance": {"derived": chance, "file": chance_file, "match": chance_ok},
    "descriptive": {
        "readme_empirical_numeric_tokens": readme_empirical_numbers,
        "k_rows": desc_k.to_dict("records"), "k_match": desc_k_match,
        "ab_rows": len(ab_pairs), "ab_match": ab_match,
        "reuse_rows": len(reuse_source), "reuse_match": reuse_source_match,
        "count_rows": desc_count_rows,
        "sidecar_sha_checks": len(desc_sidecar_checks),
        "sidecar_shas_match": all(desc_sidecar_checks),
    },
    "spot_seed": SPOT_SEED,
    "spot": spot_rows,
    "settings": {"bootstrap_B": BOOT_B, "bootstrap_seed": BOOT_SEED, "chance_seed": CHANCE_SEED},
}
Path("/tmp/g5_d2_results.json").write_text(json.dumps(result, indent=2, allow_nan=True) + "\n")
print(json.dumps({"mismatch_count": len(mismatches), "spot_ids": spot_ids, "p5": result["p5"]}, indent=2))
```

VERDICT: NUMBERS REPRODUCE
