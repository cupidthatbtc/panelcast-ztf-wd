# Full-catalog rebuild — Stage C execution plan (laptop agent)

Context: the Jestin+2026 (arXiv:2509.15133) 864-star catalog is not on VizieR yet, so we rebuilt
their candidate selection from public data on the Mac. This plan scales the ZTF fetch + variance
census to the full rebuilt candidate list. Same repo conventions as `LOMB_SCARGLE_PLAN.md`
(repo `C:\Users\jcwen\Projects\astro-wd`, branch off `lomb-scargle-census`).

## What is already done (Mac, verified against the paper)

`catalog-rebuild/` (copied next to this file):
- `stageA_eq3_cut.csv` — Gentile Fusillo J/MNRAS/508/3877 maincat with the paper's Eq. 3 cuts
  (Pwd ≥ 0.75, G < 18, BP−RP ≤ 2, sepsi ≤ 15) via VizieR TAP → **22,264 sources, exactly the
  paper's number**.
- `stageB_variable_candidates.csv` — **1,423 candidates, all 20 ground-truth stars present**
  (19 roster + the second RR Lyrae named in their Sect. 3.3, Gaia DR3 6555925496084361344).
  Recipe: σ(G) computed with **n_obs/9 (per-CCD)** — the paper's Eq. 1 as printed uses
  phot_g_n_obs directly, but its Eq. 4 constants only reproduce the selection under the /9
  convention — paired with the **printed** Eq. 4 constants (0.748, −18.597, 0.0038) and the
  threshold multiplier calibrated to their published count: m=1.1896 (paper quotes 1.25).
  Membership robustness: 4 plausible recipe variants each calibrated to 1,423 agree on
  **1,359/1,423 (95.5%)**; per-star columns `in_core` (in all 4 variants) and `n_variants`
  quantify boundary confidence. Fringe stars are near-threshold marginal variables either way —
  the census measures them regardless of label.

Document this provenance in every output: 22,264 exact; 1,423 exact with 20/20 known members;
per-CCD /9 convention inferred; m=1.19 vs paper's 1.25; 95.5% cross-variant membership core.

## Stage C — fetch + census at full scale

1. **Fetch ZTF light curves** for all 1,423 candidates (+ the one appended roster star) using
   the same IRSA endpoint/pattern as `scripts/fetch_lightcurves.py`: 10 arcsec cone by
   RA_ICRS/DE_ICRS, bands zg+zr, full history. Serial with polite throttling (~1–2 s between
   requests, exponential backoff on 429/5xx); expect a few hours. Cache per star as in
   `lc_cache/` (source_id.csv), resumable — skip stars already cached. Log failures, never
   silently drop.
2. **Crossmatch hygiene** (the paper's §4.1 in spirit, simplified and documented): keep the
   nearest match; require ≥20 measurements per band in both bands to count as "crossmatched"
   (the paper's criterion → their 894 → 864 after cleaning). Report how many of the 1,423 pass —
   the target neighborhood is ~860–900. Apply the same per-row QC as the L-S run (catflags == 0,
   magerr > 0, chi < 4).
3. **Panels**: exposure-level with BJD_TDB (reuse `build_exposure_panel.py`), nightly and
   monthly bins (reuse the existing binning code paths).
4. **Census at full scale**: three-cadence × two-band ratios for every crossmatched star
   (extend `plot_variance_census.py` machinery; output a CSV, not just a figure). Threshold 2.5
   as established.
5. **Full-catalog Lomb–Scargle** (CPU, start as soon as the fetch completes; run overnight):
   - Same two-pass blind search as `LOMB_SCARGLE_PLAN.md` (low-f + high-f, error-weighted,
     BJD_TDB, per-night-median-subtracted residuals for the high pass), same alias vetting,
     same confirmed/candidate rules. Multiband + both single bands.
   - Parallelize across stars with a process pool sized to physical cores minus 2; chunk the
     high-f grid as before. Resumable: write one result JSON per star, skip existing.
   - Skip at full scale: injection–recovery (already done on the pilot), bootstrap FAPs
     (Baluev only; bootstrap the top ~30 candidates at the end), directed searches (no
     literature frequencies for the full set).
   - Re-detection sanity gates before trusting the batch: the RR Lyrae pair, the transit star
     (0.44977 d), and the Fig 8 star (6.1464 d⁻¹) must come back at their known periods.
6. **Full-catalog panelcast refit** (GPU — run CONCURRENTLY with step 5; the L-S pool is CPU):
   - Monthly g-band descriptor for all crossmatched stars, built exactly like the pilot's
     `ztf_wd_zg_monthly.csv`. Same converged pilot config (`configs/wd_fit.yaml` lineage:
     studentt + offset_logit, rw latent, rho pinned, per-entity obs noise OFF, class pooling
     OFF), same seed policy. min-events filter as in the pilot (≥2 monthly events).
   - **Time-box: 12 h wall-clock, max 2 attempts.** Attempt 1 = pilot config as-is. If
     diagnostics fail (R-hat > 1.01, ESS < 400, or divergences), ONE retry with the obvious
     remedy for the observed failure (e.g. target_accept 0.95, or init_strategy median) — do
     NOT start a convergence ladder. If attempt 2 fails, stop and write up the diagnostics:
     at this scale a clean failure report is a result (the pilot's pinned components were
     predicted to become identifiable at N~864 — document what actually broke and where).
   - If it converges: held-out within-entity-temporal split as in the pilot; report MAE/RMSE,
     coverage at 80/95, and the posterior scalars next to the pilot's values.
7. **Deliverables** (`outputs/catalog/<timestamp>/`):
   - `census_full_catalog.csv` — one row per star: source_id, WDJname, G, BP−RP, N_exp per
     band, all six census ratios, census verdict.
   - `ls_full_catalog.csv` — one row per star: blind status, best period, band basis, Baluev
     FAP (bootstrap where run), amplitude or A95 limits, alias flags.
   - `panelcast_full_fit/` — diagnostics JSON, metrics, posterior scalar table vs pilot
     (or the failure write-up per step 6).
   - `CATALOG_RESULTS.md` — the ladder vs the paper's (1423 → 894 → 864 → 141 periodic +
     7 undetermined): our fetched / crossmatched / census-variable / L-S-periodic counts side
     by side. The census count is NOT expected to equal 141 (variance ≠ periodicity) — report
     both and say why. Table of L-S-periodic stars NOT flagged variable by the census and vice
     versa (the blind-spot symmetry at full scale). The 19 roster stars highlighted everywhere.
   - Figures: full-catalog census scatter (nightly vs monthly, g) with roster stars marked;
     L-S period vs amplitude for all confirmed periodics colored by census verdict.
   - Priority order if time runs short: census → L-S → panelcast. Never block an earlier
     deliverable on a later one; write results incrementally.

## Guardrails

- New scripts under `scripts/`, outputs under `outputs/catalog/` — do not touch
  `outputs/2026-07-18_151420_993941_17ac` or `outputs/ls/2026-08-01_full`.
- Resumable fetch; IRSA throttling is mandatory (do not hammer).
- Every count in CATALOG_RESULTS.md traceable to a script.
- Nothing pushed until Jack reviews.
