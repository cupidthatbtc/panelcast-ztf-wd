# Data acquisition and provenance

## Scientific source

The reconstruction follows Jestin et al. 2026, arXiv:2509.15133. The unpublished 864-source companion table was unavailable from VizieR, so the candidate population was rebuilt from public catalogs rather than inferred from the manuscript's result table.

## Gaia parent sample

The parent catalog is the Gentile Fusillo et al. white-dwarf catalog, VizieR table `J/MNRAS/508/3877/maincat`, queried through VizieR TAP. The paper's Eq. 3 conditions were applied to the catalog columns:

```text
Pwd >= 0.75
Gmag < 18
BPmag - RPmag <= 2
sepsi <= 15
```

The resulting 22,264 rows are committed as `catalog-rebuild/stageA_eq3_cut.csv`. The exact source columns retained are WDJname, Gaia EDR3 identifier, ICRS coordinates, Pwd, G/BP/RP magnitudes, sepsi, G-band observation count, and G-band flux-over-error.

The variability boundary uses the printed Eq. 4 constants `(0.748, -18.597, 0.0038)`, Gaia G uncertainty inferred with the per-CCD `phot_g_n_obs / 9` convention, and multiplier 1.1896 calibrated to the paper's published 1,423-candidate count. Four plausible calibrated conventions were evaluated; 1,359/1,423 sources occur in all four. `in_core` and `n_variants` preserve this boundary sensitivity per source. The complete selection is committed as `catalog-rebuild/stageB_variable_candidates.csv` and `data/roster/jestin2026_rebuilt_candidates.csv`.

The control roster was transcribed from the paper excerpt and individually named objects. Full-precision coordinates were resolved with Gaia DR3 TAP. The paper PDF is not included.

## ZTF acquisition

`scripts/fetch_catalog_lightcurves.py` queried the public IRSA endpoint:

```text
https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves
```

Each candidate used a 10-arcsec cone at its Gaia coordinates with `BANDNAME=g,r`, `FORMAT=CSV`, and `BAD_CATFLAGS_MASK=32768`. Requests were serial, separated by at least 1.25 seconds, with exponential backoff plus jitter for HTTP 429/5xx and network timeouts, at most six retries, and atomic `.part` replacement. Existing nonempty responses were skipped, making the fetch resumable. Failures and response counts were logged; all 1,423 targets reached a terminal cached response with no silent failures.

`data/irsa_raw_cache.tar.gz` contains the complete 1,423-source response cache, fetch event log, and fetch manifest. `crossmatch_qc.csv` records every candidate, including empty responses and all row-rejection counts.

## Crossmatch and photometric cleaning

Rows were grouped by ZTF object coordinate and the nearest coordinate cluster to the Gaia target was selected within the 10-arcsec response. Retention required at least 20 clean zg and 20 clean zr observations. Per-row QC required:

```text
catflags == 0
finite magnitude
finite positive magerr
chi < 4
finite MJD
```

This leaves 928 sources. Times were converted from MJD UTC to BJD TDB at Palomar with Astropy. `exposures.csv.gz` contains the complete retained exposure panel; `nightly_panel.csv.gz` and `monthly_panel.csv.gz` contain deterministic bins derived from it.

## Variability census and period search

The census computes scatter-to-error ratios at exposure-residual, nightly, and monthly cadence in zg and zr. Any of six ratios at least 2.5 is the prespecified variance flag.

The blind Lomb–Scargle search has two passes:

- low: `2 / baseline` through 48 d^-1;
- high: 24 through 1440 d^-1 after per-night median subtraction.

It evaluates multiband, zg, and zr evidence; uses Baluev false-alarm probabilities; vets aliases; reports amplitudes or A95 limits; and writes one atomic result per source. The correlation-aware hardening bootstrap uses moving observation blocks for low-frequency series and night-wise wild sign flips for high-frequency residuals. All detailed outputs are under `lomb-scargle/` and `hardening/stratified_bootstrap/`.

## Panelcast

The monthly zg panel contains 50,350 events from 928 entities. The primary, additive-Gaia, and native-warm fits used JAX 0.8.2, NumPyro 0.19.0, four chains, 3,000 warmup, 3,000 samples per chain, seed 42, Student-t likelihood, offset-logit target transform, and hierarchical random walk. Evaluation GPU allocation failures occurred only after converged sampling and were recovered by resuming the identical posterior in a fresh process with `TF_GPU_ALLOCATOR=cuda_malloc_async`; no second sampling attempt was made.

Native warm start uses panelcast PR #453's default-off `cold_start_target_col: gaia_g_mag`. The accepted uncertainty layer fits Gaia G + BP-RP correction only on the 648 entity-disjoint training entities, computes finite-sample conformal radii only on 7,400 validation rows, and evaluates once on 7,639 test rows. Raw native posterior cold-start intervals are retained but not treated as calibrated because they omit Gaia-to-ZTF proxy error.

## Regeneration and integrity

- `scripts/run_catalog_pipeline.py` orchestrates the primary rebuild.
- `scripts/audit_catalog_robustness.py` regenerates hardening tables, calibrated predictions, and acceptance.
- `scripts/generate_catalog_results.py` regenerates the report.
- `scripts/validate_catalog_rebuild.py` enforces the 27 primary checks.
- `SHA256SUMS` records every bundled file's SHA-256 and byte count.

Transient process logs, duplicate extracted per-source exposure shards, temporary scratch files, and the deliberately short smoke fit are excluded because they duplicate canonical data or are not scientific products. Failed-evaluation provenance is retained in each canonical fit's `failure.json`, manifest, and the warm execution record.
