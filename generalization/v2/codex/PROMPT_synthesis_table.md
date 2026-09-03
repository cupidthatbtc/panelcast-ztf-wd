# Task: cross-dataset synthesis table + evidence map (campaign descriptive code)

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1).
Python: `.venv-gen/bin/python`; tests: `.venv-gen/bin/python -m pytest tests -q` (221 pass now).
Do NOT commit. Do NOT touch scripts/*.py at the top level (frozen, SHA-pinned),
scripts/generalization/*.py at the top level (campaign SHA surface — a live laptop run's drift
guard depends on it), or scripts/v2/*.py (admitted digest). Create ONLY:
`scripts/generalization/descriptive/synthesis_table.py`, `tests/test_synthesis_table.py`, and the
report `generalization/v2/codex/SYNTHESIS_TABLE_REPORT.md`.

## Goal

One script that assembles the AAS 249 synthesis table across the campaign's datasets from the
committed metrics bundles, with a machine-readable EVIDENCE MAP (every cell → file + row/key), so
that the G5 verifier and the abstract can trace each number to a file. It must work today with the
datasets that exist (D1 published baseline, D3 frozen) and accept the later bundles (D2 frozen;
v2 holdout comparison outputs) when they appear, leaving their cells blank (not NaN-crashing).

## Inputs (read them; do not assume)

- D1 (published 928-star baseline re-scored by the campaign metrics): `outputs/generalization/metrics_d1/`
  (per_star.csv, completeness_by_class_pass_rule.csv, contingency_complementarity.json,
  chance_match.json, fp_frequency_distribution.csv, sensitivity.csv, attrition.csv, manifest.json).
  Note: it is an OUTPUT directory (gitignored) — the script takes it as an argument; the tests use
  synthetic bundles.
- D3 frozen: `generalization/results/2026-09-02_d3/metrics/` (same files plus trigger_rates.csv,
  ppv.csv, attrition_summary.csv, d3_mo_join_covariates.csv, surfaces/) and README.md (the
  headline numbers, for cross-checking only). Descriptive outputs in
  `generalization/results/2026-09-02_d3/descriptive_postlaunch/` (P3 by merged-oid count is in
  `d3_strata_covariates*`/`d3_trigger_decomposition*` — read their README sidecars to find the
  exact columns).
- D2 frozen (NOT yet available; expected at `generalization/results/<date>_d2/metrics/` with
  d2_cluster_completeness.csv, d2_scenario_contrasts.csv, d2_paired_controls_summary.csv,
  trigger_rates.csv, chance_match.json) — read `scripts/generalization/metrics_generalization.py`
  to learn those files' columns (functions d2_cluster_bootstrap, d2_paired_controls,
  trigger_rates) and the archived pilot `generalization/results/2026-08-30_d2_pilot_gen2/metrics/`
  for real examples of the shapes (pilot numbers must never be used in the table; the pilot flag
  in manifest.json is true there — the script must refuse pilot bundles for the synthesis and
  say so).
- v2 holdout comparison (NOT yet available; produced by `scripts/v2/compare_engines.py` → read it
  for the output schema: endpoints.csv columns endpoint, frame, n, interval, frozen_k/p/lo/hi,
  v2_k/p/lo/hi, diff, diff_lo, diff_hi, frozen_only, v2_only, mcnemar_exact_p, note, and for P2
  rows frozen_chance_direct_mean etc.; manifest.json with registration binding).
- The estimand definitions: `generalization/METRICS_SPEC.md` (P1..P5, rules 1–4, the D1
  validation numbers 11/13, 9/13, 13/13, 0+1 which the D1 bundle reproduces).

## Output (`--out-dir`, default `generalization/results/<date>_synthesis/` given by the caller)

1. `synthesis_table.csv`: one row per (dataset, arm, endpoint), columns: dataset (D1|D2|D3),
   arm (frozen|v2), endpoint (P1_detection, P2_recovery, P3_negative_trigger, census_rate,
   either_rate, union_rate, incremental_census, mcnemar_p, ppv, chance_match_mean,
   chance_match_p95, P4_recovery_eligible, P4_recovery_usable, P4_trigger, P5_fpr_upper,
   control_contrast_trigger, control_contrast_strict_recovery, and for the v2 rows the paired
   diff/diff_lo/diff_hi/mcnemar vs frozen), n, estimate, lo, hi, interval_type, frame, source_file,
   source_locator (row index / JSON key path), notes. Blank estimate + notes="bundle not
   available" when the input is absent.
2. `evidence_map.json`: {cell_id: {file, sha256, locator, value}} for every filled cell; plus
   the bundle manifests' SHAs and each bundle's `pilot`/`engine` flags.
3. `synthesis_table.md`: a compact Markdown rendering (datasets as columns, endpoints as rows,
   "estimate [lo, hi] (n)") suitable for pasting into the outline.
4. `manifest.json`: script SHA, inputs (paths + SHAs), datasets present/absent, timestamp.

Cross-check (must be implemented, must pass on the real D3 bundle): the D3 cells for P1, P2, P3,
union, incremental census, PPV, chance-match must equal the values in the D3 README (parse the
README numbers with regexes or hard-code the expected values in a small dict with a comment
citing README line numbers) to 3 decimals; mismatch → exit 1 with the offending cell.

## Tests (`tests/test_synthesis_table.py`, synthetic bundles in tmp_path, fast)

- builds the table from a synthetic D1 + D3 bundle; absent D2/v2 → blank cells with the note;
- refuses a pilot bundle (manifest pilot=true) for a dataset slot with a clear SystemExit;
- evidence map covers every filled cell, SHAs equal the files;
- the Markdown rendering has one column per present dataset/arm;
- a mismatch against an injected expected value exits 1.

## Report

`generalization/v2/codex/SYNTHESIS_TABLE_REPORT.md`: the real D3+D1 table you produced (run the
script with `--d1-metrics outputs/generalization/metrics_d1 --d3-bundle
generalization/results/2026-09-02_d3 --out-dir outputs/generalization/synthesis_dry_run`; the
out dir is gitignored), the cross-check result, and the final pytest summary line (whole suite).
