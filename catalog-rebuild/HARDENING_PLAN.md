# Catalog rebuild hardening plan

Goal: turn the completed Stage C run into a publication-grade robustness package without changing panelcast internals or replacing the prespecified primary analysis.

## 1. Crossmatch and count sensitivity

- Keep the 928-source nearest-coordinate result as the prespecified primary analysis.
- Recompute census and L-S headline counts under transparent Gaia–ZTF magnitude-consistency and separation thresholds.
- Report whether the 342 confirmations and census/L-S blind-spot result survive exclusion of the 20 >1 mag mismatches.
- Never silently replace the primary population.

## 2. Period-search robustness

- Audit wider solar/sidereal/harmonic neighborhoods beyond the original narrow spectral-window veto.
- Select a stratified validation sample spanning strong/marginal, low/high, and confirmed/one-band results rather than letting underflowed analytic FAP ties select only low-frequency detections.
- Run temporal-block/residual resampling appropriate to each pass and report survival by stratum.
- Preserve the original `ls_full_catalog.csv`; write hardening products separately.

## 3. Forecast baselines

- Benchmark the converged panelcast fit against last-value, per-entity median, global-mean, class-mean, direct Gaia G, and train-only Gaia G + BP−RP regression baselines on the exact saved splits.
- Treat panelcast as adding value only where it beats the relevant simple baseline.

## 4. Minimal panelcast extension

- Add Gaia G and BP−RP through panelcast's existing `core_numeric` feature block; no panelcast source changes.
- Disable the previous-score GBM offset in a domain overlay so entity level is learned from the hierarchical model and static Gaia covariates can transfer to unseen stars.
- Fit one 4×3000 sensitivity model under the same Student-t, offset-logit, RW, seed-42, and identifiability pins.
- Compare primary and entity-disjoint metrics against both the original fit and the simple baselines. Do not replace the primary fit unless both sampling diagnostics and predictive comparisons improve.

## 5. Acceptance

Hardening is complete when:

- every sensitivity count is script-generated;
- baseline and Gaia-feature metrics are computed on the exact stored splits;
- the stratified period audit spans low/high and strong/marginal populations;
- model diagnostics retain max R-hat ≤1.01, bulk ESS ≥400, and zero divergences;
- conclusions distinguish prespecified primary results from post-hoc sensitivity analyses;
- all code checks pass and the branch remains unpushed.
