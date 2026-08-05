# Publication Readiness

- **Status:** FAIL
- **Critical failures:** 2
- **Recommended failures:** 0

## Checks

| Check | Severity | Passed | Detail |
|---|---|---|---|
| mcmc_min_2_chains | critical | yes | num_chains=4 (required >=2 for R-hat) |
| mcmc_recommended_4_chains | recommended | yes | num_chains=4 (recommended >=4 for publication-grade diagnostics) |
| convergence_passed | critical | yes | diagnostics.passed=True |
| rhat_available | critical | yes | rhat_max=1.0 |
| rhat_within_threshold | critical | yes | rhat_max=1.0000, threshold=1.0100 |
| ess_available | critical | yes | ess_bulk_min=3459.0 |
| ess_within_threshold | critical | yes | ess_bulk_min=3459, threshold=400 |
| prior_predictive_artifact_present | recommended | yes | evaluation/prior_predictive.json present |
| primary_calibration_within_tolerance | critical | yes | within_tolerance=True |
| secondary_split_evaluated | critical | yes | secondary_split_present=True |
| secondary_calibration_within_tolerance | critical | no | within_tolerance=False |
| publication_artifact_errors | critical | no | n_errors=1 |
