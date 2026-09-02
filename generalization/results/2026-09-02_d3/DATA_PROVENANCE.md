# Provenance — D3 full run and metrics

- Roster: generalization/data/d3/roster_d3.csv (3,000 = 610 dSct=1, 76 dSct=2, 2,314 dSct=0 SRS from 7,292; seed frozen).
- Labels: Murphy+2019 (VizieR J/MNRAS/485/2380); frequencies/amplitudes: Mo+2026 table1/table2 (raw SHAs in generalization/data/d3/roster_report.json and the metrics `inputs_sha256.json`).
- Light curves: IRSA ZTF DR, fetched by the frozen fetcher (laptop cache); crossmatch/QC by the frozen chain (build_panels_generic; panel golden gate PASS 2026-08-30); adjudication frozen as data (crossmatch_freeze/, 2,901 crossmatched).
- Run: laptop Jacks_7i_5090, run_generalization_ls.py, 12 workers, strict attestation (full-928 replay PASS 2026-08-29, SHA 64e1937a…); launched 2026-08-30 19:37, paused 2026-08-31 12:04, resumed 2026-09-01 00:41 (sidecar-bound resume; 1,184 valid results retained), finished 2026-09-02 01:28; `run/manifest.json`, `run/completion.csv` (provenance_sha256 per star).
- Metrics: laptop (pre-fix code, commit 5b5f826) → `metrics_laptop_prefix/`; Mac (post-fix code, commits 048a814…70bc860) → `metrics/`; guard `compare_metrics_runs.py` PASS (identical_newline tier); env: python 3.12.12/3.12.13, numpy 2.3.5, scipy 1.16.3, astropy 8.0.1, pandas 2.3.3.
- Descriptive outputs: scripts/generalization/descriptive/*.py per reviews/G5prep/sol_diurnal.md and sol_round2.md; each carries its own manifest with input/output SHA-256.
- Amendments/admissions: reviews/G2_FREEZE.md (A2–A4 ratified; 2026-08-31 and 2026-09-01 descriptive admissions; NaN-dominant labelling disclosure).
- Raw per-star JSONs + sidecars (5,802 files) are kept outside the repo at outputs/generalization/d3_sync/d3_run/stars (Mac) and outputs\generalization\d3_run\stars (laptop); their SHAs are bound in `run/completion.csv` and `metrics/inputs_sha256.json`.
- Tests: 143 passed on the Mac (`pytest_mac.log`).
