# Model Card: Ztf Wd Catalog Monthly Gaia source_id Score Prediction Model

## Model Details

- **Model type:** Bayesian Hierarchical Regression with Time-Varying Effects
- **Version:** 0.23.0
- **Authors:** Ztf Wd Catalog Monthly Gaia Prediction Pipeline
- **Created:** 2026-08-03
- **Last updated:** 2026-08-03

## Intended Use

This model is intended for:

- Research on source id score trajectories
- Exploration of month id-to-month id score patterns
- Educational demonstration of Bayesian hierarchical modeling

### Out-of-Scope Use

This model should NOT be used for:

- High-stakes or operational decisions without human review
- Real-time prediction systems in production environments

## Training Data

- **Dataset:** ztf_wd_catalog_monthly_gaia
- **Size:** 49,422 albums
- **Description:** Sequential month id-level records grouped by source id from the 'ztf_wd_catalog_monthly_gaia' dataset, with the target score (mag_binned) bounded to [10, 20].
- **Preprocessing:** Leak-safe within-source id temporal splitting with source id-disjoint secondary checks, minimum observation-count filtering, features standardized to zero mean and unit variance.

## Model Architecture

Grouping entity: source_id; sequential event: month_id. Internal parameter names use 'artist' for the grouping entity.

Bayesian hierarchical regression with four key components:

1. **Hierarchical artist effects**: Partial pooling across artists for robust estimation of artist quality. Non-centered parameterization via LocScaleReparam avoids funnel geometry.

2. **Time-varying slopes**: Artist quality modeled as a random walk, allowing career trajectories to evolve over time.

3. **AR(1) structure**: Album-to-album dependencies captured via autoregressive term, modeling momentum effects where consecutive albums tend to have correlated scores.

4. **Heteroscedastic observation noise** (sigma_ref parameterization): Albums with more reviews have lower observation noise. The model samples sigma_ref (noise at the median review count n_ref) and derives per-observation noise as: sigma_obs = sigma_ref * n_ref^n_exponent, then sigma_i = sigma_obs / n_reviews_i^n_exponent. This reparameterization breaks the multiplicative funnel between sigma_obs and n_exponent that causes divergent transitions in MCMC sampling.

Mathematical form:
- y_ij ~ StudentT(df=4, mu_ij, sigma_i) (likelihood family configurable via --likelihood-family)
- mu_ij = artist_effect_jt + X_ij @ beta + rho * (prev_score_ij - ar_center)
- artist_effect_jt evolves via random walk from initial effect
- sigma_i = sigma_obs / n_reviews_i^n_exponent (heteroscedastic mode)

Since 0.5.0 the likelihood operates on the offset-logit transformed target by default (--target-transform offset_logit), and since 0.6.0 the default feature block includes a stacked-GBM offset (gbm_offset) with genre-level pooling where the dataset provides a group column. The per-run values are recorded in the hyperparameters table.

### Prior Distributions

Prior distributions are weakly informative, chosen to regularize inference while allowing the data to dominate:

- **mu_artist** ~ Normal(0.7227843999862671, 1.0): Centered at 0.7227843999862671 because artist effects represent deviations from feature-based predictions. Scale of 1.0 permits the population center to shift by ~1.0 SD on the standardized score scale.
- **sigma_artist** ~ HalfNormal(0.5): Scale of 0.5 encourages moderate partial pooling. Implies most artist effects within +/-1.0, consistent with observed between-artist spread.
- **sigma_rw** ~ HalfNormal(0.1): Scale of 0.1 produces smooth career trajectories where album-to-album quality changes are small relative to overall artist variation.
- **rho** ~ TruncatedNormal(0.0, 0.3, -0.99, 0.99): Centered at 0.0 with scale 0.3, allowing moderate autoregressive momentum without strong prior commitment to direction.
- **beta** ~ Normal(0.0, 1.0): Scale of 1.0 is weakly informative for standardized features, allowing data to determine effect sizes.
- **sigma_obs** ~ HalfNormal(0.5): Scale of 0.5 allows data to determine observation-level noise.


**Prior Predictive Check**: Prior predictive simulation (n_samples=500) shows 74.2% of prior-implied predictions fall within [10.0, 20.0]. Summary: mean=15.9, sd=3.8, range=[9.5, 20.5].

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| mu_artist_loc | 0.0 |
| mu_artist_scale | 1.0 |
| sigma_artist_scale | 0.5 |
| sigma_rw_scale | 0.1 |
| rho_loc | 0.0 |
| rho_scale | 0.3 |
| beta_loc | 0.0 |
| beta_scale | 1.0 |
| sigma_obs_scale | 1.0 |
| sigma_ref_scale | 1.0 |
| n_exponent_default | 0.0 |
| n_features | 8 |
| n_artists | 928 |
| max_albums | 100 |
| num_chains | 4 |
| num_warmup | 3000 |
| num_samples | 3000 |
| chain_method | sequential |
| target_accept_prob | 0.9 |
| max_tree_depth | 10 |
| target_transform | offset_logit |
| likelihood_family | studentt |
| entity_group_pooling | False |
| gbm_offset | False |

## Evaluation Results

### Convergence Diagnostics

Convergence status: PASSED

- R-hat (max): 1.0000 (threshold: < 1.01)
- ESS bulk (min): 5,133
- ESS tail (min): 6,191
- Divergent transitions: 0

### Calibration

Credible interval coverage:
- 80% CI: 78.6% empirical coverage, mean width=0.07
- 95% CI: 92.8% empirical coverage, mean width=0.13

**Posterior Predictive Checks:**
- mean: T(y_obs)=16.91, p=0.796 (MC SE: 0.004)
- sd: T(y_obs)=0.89, p=0.250 (MC SE: 0.004)
- skewness: T(y_obs)=-1.27, p=0.748 (MC SE: 0.004)
- min: T(y_obs)=12.81, p=0.426 (MC SE: 0.005)
- max: T(y_obs)=18.94, p=0.001 (MC SE: 0.000)
- q10: T(y_obs)=15.64, p=0.836 (MC SE: 0.003)
- q50: T(y_obs)=17.12, p=0.841 (MC SE: 0.003)
- q90: T(y_obs)=17.82, p=0.933 (MC SE: 0.002)

#### Flagged calibration slices

Slices whose nominal level falls outside the Wilson 95% CI. Under perfect calibration ~1.3 flags are expected by chance — read clusters, not lone flags.

| Dimension | Slice | n | Level | Empirical | Wilson 95% CI |
|-----------|-------|---|-------|-----------|----------------|
| n_reviews_decile | (0.999, 2.0] | 329 | 0.80 | 0.678 | [0.626, 0.726] |
| n_reviews_decile | (0.999, 2.0] | 329 | 0.95 | 0.854 | [0.812, 0.888] |
| n_reviews_decile | (5.0, 6.0] | 94 | 0.80 | 0.883 | [0.802, 0.933] |
| n_reviews_decile | (7.0, 8.0] | 125 | 0.80 | 0.880 | [0.811, 0.926] |
| n_reviews_decile | (8.0, 9.0] | 48 | 0.80 | 0.917 | [0.804, 0.967] |
| n_reviews_decile | (9.0, 26.0] | 57 | 0.80 | 0.965 | [0.881, 0.990] |
| train_history | 11+ | 903 | 0.95 | 0.930 | [0.912, 0.945] |
| target_tercile | (12.809000000000001, 16.69] | 310 | 0.80 | 0.910 | [0.873, 0.937] |
| target_tercile | (17.436, 18.94] | 309 | 0.80 | 0.667 | [0.612, 0.717] |
| target_tercile | (17.436, 18.94] | 309 | 0.95 | 0.871 | [0.829, 0.903] |

### Predictive Performance

Point prediction metrics:

- MAE: 0.02
- RMSE: 0.04
- R-squared: 0.998
- Held-out ELPD (test lppd): 1849.5 (SE: 35.2)

**Ranking:** Spearman 0.998, Kendall 0.967, precision@5 1.00, precision@10 0.90, precision@25 0.88 (single-slate, descriptive).

- **Held-out ELPD (test lppd):** 1849.5

## Limitations

- Dynamic source id trajectories are learned only when an source id has at least 2 training month ids.
- Score predictions are probabilistic and should not be treated as ground truth.
- Review the AOTY model card limitations for the statistical caveats of the shared model architecture (bounded target vs. symmetric likelihood, convergence budget).

## Ethical Considerations

- Predictions are for research and exploration, not operational decisions.
- Historical biases in the recorded mag_binned values will be reflected in predictions.

## How to Use

### Loading the Model

```python
from pathlib import Path

from panelcast.models.bayes.io import load_manifest, load_model

# Load the current ztfgcg-score model referenced by models/manifest.json
manifest = load_manifest(Path("models"))
model_name = manifest.current["ztfgcg_score"]
idata = load_model(Path("models") / model_name)
```

### Making Predictions

```python
from panelcast.models.bayes.predict import (
    extract_posterior_samples,
    predict_new_entity,
)
import jax.numpy as jnp

posterior_samples = extract_posterior_samples(idata)
n_features = int(posterior_samples["ztfgcg_beta"].shape[-1])
X_new = jnp.zeros((1, n_features), dtype=jnp.float32)
pred = predict_new_entity(
    posterior_samples=posterior_samples,
    X_new=X_new,
    prev_score=jnp.array([15], dtype=jnp.float32),
    n_reviews_new=jnp.array([100.0], dtype=jnp.float32),
    prefix="ztfgcg_",
    target_bounds=(10, 20),
)
```

### Interpreting Results

```python
import numpy as np

# Extract prediction statistics from posterior predictive draws
y_samples = np.asarray(pred['y']).ravel()
pred_mean = float(np.mean(y_samples))
pred_std = float(np.std(y_samples))
ci_95 = np.percentile(y_samples, [2.5, 97.5])

print(f"Predicted score: {pred_mean:.1f} +/- {pred_std:.1f}")
print(f"95% CI: [{ci_95[0]:.1f}, {ci_95[1]:.1f}]")
```
