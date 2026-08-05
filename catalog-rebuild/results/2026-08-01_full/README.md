# Full-catalog reproducibility bundle

This directory commits the canonical data, result tables, diagnostics, posterior artifacts, figures, and provenance for the `2026-08-01_full` rebuild. It is the reviewable companion to `catalog-rebuild/CATALOG_PLAN.md`, `catalog-rebuild/HARDENING_PLAN.md`, and the scripts under `scripts/`.

## Headline results

- 22,264 sources reproduce the paper's Gaia Eq. 3 cut.
- 1,423 reconstructed variability candidates; 1,359 are common to all four calibrated recipe variants.
- 928 sources pass the nearest-object and clean g+r coverage requirements.
- 342 prespecified Lomb–Scargle confirmations and 76 one-band candidates.
- 333 confirmations survive the Gaia–ZTF magnitude sensitivity cut; 311 survive that cut plus the wider daily-systematics screen.
- Native Gaia warm start improves unseen-entity panelcast MAE from 0.63439 to 0.15626 and R² from -0.005 to 0.799.
- Train-only Gaia correction plus validation conformalization reaches MAE 0.11729, R² 0.835, and 80%/95% coverage 0.829/0.966.

## Contents

- `CATALOG_RESULTS.md`: complete scientific report.
- `HARDENING_RESULTS.md`: robustness, baseline, bootstrap, and warm-start interpretation.
- `DATA_PROVENANCE.md`: source endpoints, query rules, throttling, cleaning, transformations, and regeneration map.
- `catalog/`: census, crossmatch QC, Lomb–Scargle catalog, disagreement table, and magnitude audit.
- `data/`: complete raw IRSA response cache archive plus aggregate exposure/night/month and panelcast datasets.
- `lomb-scargle/`: all per-source period-search results, sanity gates, and scratch-free completion evidence.
- `hardening/`: crossmatch/systematics sensitivity, all 40 stratified bootstrap results, calibrated predictions, and machine-readable acceptance.
- `panelcast/`: primary, additive-Gaia, and native-warm posterior, evaluation, prediction, and report artifacts.
- `figures/`: final census and period-amplitude figures.
- `SHA256SUMS`: hash and byte count for every committed artifact.

The raw paper manuscript is not redistributed. Obtain it from arXiv using the citation in `DATA_PROVENANCE.md`.
