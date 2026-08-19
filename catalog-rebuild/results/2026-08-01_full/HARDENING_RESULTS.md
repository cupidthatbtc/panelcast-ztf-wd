# Catalog hardening — final results

## Crossmatch sensitivity

The prespecified result has **928** sources and **342** L-S confirmations. Applying |median ZTF g − Gaia G| ≤1 leaves **908** sources and **333** confirmations.

| scenario | sources | known_roster | census_variable | ls_confirmed | ls_candidates | ls_not_detected | ls_confirmed_fraction | census_or_ls_confirmed |
|---|---|---|---|---|---|---|---|---|
| primary_all | 928 | 19 | 203 | 342 | 76 | 510 | 0.36853 | 436 |
| magnitude_delta_le_2 | 914 | 19 | 203 | 336 | 75 | 503 | 0.36761 | 430 |
| magnitude_delta_le_1 | 908 | 19 | 201 | 333 | 74 | 501 | 0.36674 | 427 |
| magnitude_delta_le_0.5 | 898 | 19 | 196 | 330 | 73 | 495 | 0.36748 | 421 |
| separation_le_2_arcsec | 907 | 19 | 199 | 334 | 74 | 499 | 0.36825 | 426 |
| separation_le_2_and_delta_le_1 | 902 | 19 | 197 | 331 | 73 | 498 | 0.36696 | 423 |

## Wider daily-systematics audit

A ±0.01 d⁻¹ neighborhood around the nearest solar/sidereal harmonic across the full low and high grids flags **31** of 418 confirmed/candidate results. This is a sensitivity flag, not a post-hoc replacement classification.

## Forecast baselines

### Within-entity temporal

| split | model | subset | mae | rmse | r2 | n |
|---|---|---|---|---|---|---|
| within_entity_temporal | panelcast_primary | all | 0.02422 | 0.03604 | 0.99837 | 928 |
| within_entity_temporal | last_value | all | 0.02401 | 0.03580 | 0.99840 | 928 |
| within_entity_temporal | entity_train_median | all | 0.01962 | 0.03127 | 0.99878 | 928 |
| within_entity_temporal | global_train_mean | all | 0.69778 | 0.89382 | -0.00000 | 928 |
| within_entity_temporal | panelcast_gaia_features | all | 0.02411 | 0.03582 | 0.99839 | 928 |
| within_entity_temporal | panelcast_gaia_warm | all | 0.02410 | 0.03588 | 0.99839 | 928 |

### Entity-disjoint

| split | model | subset | mae | rmse | r2 | n |
|---|---|---|---|---|---|---|
| entity_disjoint | panelcast_primary | all | 0.63439 | 0.82955 | -0.00528 | 7639 |
| entity_disjoint | global_train_mean | all | 0.63390 | 0.83258 | -0.01263 | 7639 |
| entity_disjoint | class_train_mean | all | 0.63392 | 0.83290 | -0.01341 | 7639 |
| entity_disjoint | gaia_g_direct | all | 0.15774 | 0.37177 | 0.79810 | 7639 |
| entity_disjoint | gaia_g_bp_rp_train_ols | all | 0.11664 | 0.33603 | 0.83504 | 7639 |
| entity_disjoint | panelcast_gaia_features | all | 0.62888 | 0.82270 | 0.01125 | 7639 |
| entity_disjoint | panelcast_gaia_warm | all | 0.15626 | 0.37100 | 0.79893 | 7639 |
| entity_disjoint | panelcast_gaia_warm_calibrated | all | 0.11729 | 0.33592 | 0.83516 | 7639 |

The original panelcast fit does not beat the entity-median baseline for known stars and is effectively a global-mean model for unseen stars. A converged sensitivity fit added Gaia G and BP−RP through `core_numeric` and removed the GBM offset, but the AR previous-score term still dominated training and the static coefficients did not materially improve cold start. The change is therefore rejected rather than promoted. The train-only Gaia regression remains the honest unseen-entity benchmark.

## Conservative catalog floor

Combining |median ZTF g − Gaia G| ≤1 with the wider ±0.01 d⁻¹ daily-systematics screen leaves **311** prespecified confirmations. This is a sensitivity floor, not a rewritten primary catalog.

## Minimal Gaia-feature panelcast sensitivity

The fit converged with max R-hat **1.000**, minimum bulk ESS **5133**, and **0** divergences.

| split | model | subset | mae | rmse | r2 | n |
|---|---|---|---|---|---|---|
| within_entity_temporal | panelcast_gaia_features | all | 0.02411 | 0.03582 | 0.99839 | 928 |
| entity_disjoint | panelcast_gaia_features | all | 0.62888 | 0.82270 | 0.01125 | 7639 |
| entity_disjoint | panelcast_gaia_features | magnitude_delta_le_1 | 0.61166 | 0.79619 | 0.01595 | 7503 |

The existing additive feature seam cannot solve cold start here because the AR previous-score term explains nearly every non-debut training observation, leaving static Gaia coefficients weakly identified for unseen entities. The sensitivity fit is retained as a clean negative result and is not adopted over the prespecified primary fit.

## Native Gaia warm-start panelcast

The default-off `cold_start_target_col` seam converged with max R-hat **1.000**, minimum bulk ESS **5100**, and **0** divergences. Gaia G initialized all 928 training debuts and all 7,639 unseen-entity test rows with zero fallback.

| split | model | subset | mae | rmse | r2 | n |
|---|---|---|---|---|---|---|
| within_entity_temporal | panelcast_gaia_warm | all | 0.02410 | 0.03588 | 0.99839 | 928 |
| entity_disjoint | panelcast_gaia_warm | all | 0.15626 | 0.37100 | 0.79893 | 7639 |
| entity_disjoint | panelcast_gaia_warm | magnitude_delta_le_1 | 0.11819 | 0.17434 | 0.95282 | 7503 |
| entity_disjoint | panelcast_gaia_warm_calibrated | all | 0.11729 | 0.33592 | 0.83516 | 7639 |
| entity_disjoint | panelcast_gaia_warm_calibrated | magnitude_delta_le_1 | 0.08122 | 0.13066 | 0.97350 | 7503 |

A leakage-safe hybrid fits the Gaia G + BP−RP proxy correction on the 648 entity-disjoint training entities, then derives split-conformal radii on the 7,400 validation rows. Test MAE is **0.11729**, R² **0.835**, with 80%/95% coverage **0.829/0.966** and interval widths **0.245/1.056** mag.

The native warm start is adopted for unseen-entity point prediction. Its uncalibrated Bayesian intervals remain too narrow because the fitted model does not contain Gaia-to-ZTF proxy error; the validation-conformal wrapper, not the raw posterior interval, is the accepted uncertainty product.

## Stratified correlation-aware bootstrap

| selection_stratum | sources | median_bootstrap_fap | fap_le_0p01 | fap_le_0p05 |
|---|---|---|---|---|
| candidate_high_marginal | 5 | 0.47525 | 0 | 1 |
| candidate_high_strong | 5 | 0.11881 | 0 | 2 |
| candidate_low_marginal | 5 | 0.03960 | 2 | 3 |
| candidate_low_strong | 5 | 0.00990 | 5 | 5 |
| confirmed_high_marginal | 5 | 0.24752 | 0 | 1 |
| confirmed_high_strong | 5 | 0.00990 | 3 | 3 |
| confirmed_low_marginal | 5 | 0.00990 | 4 | 4 |
| confirmed_low_strong | 5 | 0.00990 | 5 | 5 |

The audit covers **40** detections across all eight strong/marginal × low/high × confirmed/candidate strata. Low-frequency signals are substantially more robust than high-frequency signals under correlation-preserving nulls; the bootstrap table is a validation audit rather than a post-hoc relabeling of the primary catalog.

## Final hardening verdict

The reconstruction and low-frequency population are publication-grade robustness results: all five strong and four of five marginal low-frequency confirmations survive the correlation-aware audit, and 311 confirmations remain after simultaneous crossmatch and daily-systematics sensitivity screens. The 65 high-frequency primary confirmations remain valid prespecified outputs but must be presented as exploratory: only three of five strong and one of five marginal examples survive at FAP ≤0.05. Panelcast still does not beat the entity-median baseline for known stable stars, but native Gaia initialization repairs unseen-entity point prediction; train-only proxy correction plus validation conformalization supplies calibrated cold-start intervals without touching the prespecified primary fit.
