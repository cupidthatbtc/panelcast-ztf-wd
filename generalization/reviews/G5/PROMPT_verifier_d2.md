# G5 — independent re-derivation of every frozen D2 headline number (read-only)

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1).
Python: `.venv-gen/bin/python` (numpy, pandas, scipy). Read anything, run read-only Python; do NOT
modify tracked files. Write your report ONLY to `generalization/reviews/G5/verifier_d2.md`.

You are a fresh verifier with no attachment to the campaign. The authoritative frozen D2 bundle is
`generalization/results/2026-09-04_d2/` (README.md — if present — states the headline numbers;
metrics/ holds per_star.csv, d2_cluster_completeness.csv, d2_scenario_contrasts.csv,
d2_paired_controls.csv, d2_paired_controls_summary.csv, d2_control_reuse.csv, trigger_rates.csv,
chance_match.json, surfaces/, completeness_by_class_pass_rule.csv (descriptive for D2),
sensitivity.csv, fp_frequency_distribution.csv, attrition.csv, manifest.json, inputs_sha256.json;
metrics_laptop_prefix/ is the laptop's pre-fix run; run/ holds the run manifest, completion.csv,
generation_manifest.json, shard_manifest.csv, injected_modes.csv, rejected_modes.csv;
descriptive_postlaunch/ holds the admitted D2 descriptives with README/manifest sidecars). The raw
per-star JSONs + sidecars are at `outputs/generalization/d2_sync/d2_run/stars/` and the shards at
`outputs/generalization/d2_sync/d2_shards_gen2/`. Definitions: `generalization/METRICS_SPEC.md`
(P4 eligible/usable algebra, P5 acceptance, paired controls, scenario contrasts, the rules) and
`scripts/generalization/metrics_generalization.py` (truth_d2, d2_cluster_bootstrap, d2_paired_controls,
d2_chance_match, d2_surfaces, trigger_rates, classify_match) plus `scripts/generalization/d2_truth_model.py`
(MANIFEST_COLUMNS, scenario_code, WG_SURFACE_EDGES).

Task — re-derive INDEPENDENTLY (your own code; you may import classify_match / pass_eligible /
wilson / cp_one_sided_bounds and the frozen overall_result only after reading them and saying so):

1. Run universe: 3,089 shards = the generation's run matrix (309 nominal B, 309 A, ladder 8×103,
   phase 2×103, ampscale 2×103, dropout 76, cadence_alt 33, redilution 20, 106 controls, 1,000 nulls);
   completion table and sidecars consistent; 0 failures.
2. P4 nominal arm-B recovery, ELIGIBLE and USABLE variants, exactly per the spec algebra (per target
   mean over scheduled strata; missing = 0 for eligible), point estimates and the target-cluster
   bootstrap 95 % intervals (state seed/B you used vs the metrics'), plus the detection-only trigger
   variant; the K0/K1/K2 target means.
3. P5: nulls confirmed x/1000, exact one-sided CP upper, acceptance ≤ 0.5 % (the sole confirmatory
   decision) — re-derive x from the raw JSONs via overall_result too.
4. Paired controls: the 2×2 for D and for R (control scored against its partner's injected dominant
   frequency), P(B=1, C=0) with its interval, the native trigger rate of the controls and the reuse
   distribution.
5. Scenario contrasts: every scenario-minus-nominal-K1 difference (eligible denominator), the
   discordance-bound rows, min/max named.
6. Surfaces: recovery on (W_g, amplitude) — n_targets, k/n per cell — and the chance-match
   (derangements) numbers.
7. Every number quoted in README.md (if present) and in the descriptive_postlaunch READMEs:
   MATCH / MISMATCH with your value.
8. Provenance spot-check: 20 random stars — sidecar shard SHA equals the shard on disk, result SHA
   equals the JSON, completion.csv agrees, generation id matches; truth files' SHAs equal the
   generation manifest's.

Report format: tables (quantity | file value | re-derived | MATCH/MISMATCH | one-line derivation),
then every MISMATCH with likely cause, then the exact code you ran, then
`VERDICT: NUMBERS REPRODUCE` or `VERDICT: DISCREPANCIES`. Terse and precise.
