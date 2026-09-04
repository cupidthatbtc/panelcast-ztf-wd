# Provenance — D2 full run and metrics

- Targets: 103 TESS DAVs / 341 published modes (Romero 2022 arXiv:2201.04158, Romero 2025
  arXiv:2407.07260; `generalization/data/d2/d2_targets.csv`, `d2_modes.csv`, roster report SHAs
  in `run/generation_manifest.json`); SPOC v3 verification (58/63 published modes at SNR ≥ 4 on
  their sectors; 33 mixed-cadence targets → cadence_alt) in `generalization/data/d2/spoc_verification/`.
- Windows: the attested 928-star 2026-08-01 catalog shards (magnitude-matched pool, W_g strata
  10/50/90 = 6/58/452, Amendment 4); generation gen2 (`129740d1809c…`, built 2026-08-30 on the
  laptop by `build_d2_shards.py` at commit b854e97; production = true; 3,089 shards; every
  template matched at |Δg| ≤ 0.25; truth tables `run/injected_modes.csv`, `run/rejected_modes.csv`,
  `run/shard_manifest.csv`, all SHA-bound in `run/generation_manifest.json`).
- Run: laptop Jacks_7i_5090, `run_generalization_ls.py`, 12 workers, strict attestation (full-928
  replay PASS 2026-08-29, SHA 64e1937a…), launched by `campaign_chain2.ps1` 2026-09-02 01:31 EDT
  after the D3 run, finished 2026-09-03 21:00 EDT (rc 0; 3,089 completed, 0 failed, ~70 shards/h);
  frozen checkout commit 5b5f826; `run/manifest.json`, `run/completion.csv` (result and sidecar
  SHA per shard).
- Metrics: laptop (pre-fix code, commit 5b5f826) → `metrics_laptop_prefix/`; Mac (post-fix code,
  HEAD f382175) → `metrics/`; guard `compare_metrics_runs.py` PASS: 17 outputs identical
  (newline tier), `per_star.csv` identical in every decision/match/count column with the two
  CSV-parsed truth columns (`primary_freq`, `truth_period_days`) differing by one ulp on 76 rows
  (max relative 2.06e-16; the laptop pandas float-parse artifact recorded in
  `generalization/env/CROSS_PLATFORM_REPLAY.md`), admitted through the named-column
  `--allow-known-platform-ulp` exception (tests `tests/test_guard_known_ulp.py`); env: python
  3.12.12 (laptop) / 3.12.13 (Mac), numpy 2.3.5, scipy 1.16.3, astropy 8.0.1, pandas 2.3.3.
- Descriptive outputs: `scripts/generalization/descriptive/d2_descriptives.py` per
  reviews/G5prep/sol_round2.md item 5; manifest with input/output SHA-256 beside them.
- Figures: `scripts/generalization/figures/d2_poster_figures.py` (F5–F7; `figures/figures.manifest.json`
  records every drawn number and input SHA).
- Raw per-star JSONs + sidecars (6,178 files) and the 3,089 shards are kept outside the repo at
  `outputs/generalization/d2_sync/` (Mac) and `outputs\generalization\d2_run`, `d2_shards_gen2`
  (laptop); their SHAs are bound in `run/completion.csv`, `run/generation_manifest.json` and
  `metrics/inputs_sha256.json`.
- Tests: 238 passed on the Mac (`pytest_mac.log`).
- Ledger: reviews/G2_FREEZE.md entry 2026-09-04 (P5 acceptance not met; guard exception).
