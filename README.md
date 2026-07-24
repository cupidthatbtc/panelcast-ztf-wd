# panelcast-ztf-wd

The first astronomy deployment of [panelcast](https://github.com/cupidthatbtc/panelcast).
It ports ZTF white-dwarf light curves into panelcast's **entity-event panel**
contract and fits them with the same hierarchical random-walk model panelcast
uses for album-rating trajectories — here each white dwarf is an entity and each
observing night is an event.

## What this is

A **19-star** panel of ZTF g/r photometry for the white dwarfs recoverable from
Jestin+2026 ([arXiv:2509.15133](https://arxiv.org/abs/2509.15133)), shaped for
panelcast's entity-event descriptor contract:

- **`data/raw/ztf_wd_panel.csv`** — 19,950 rows, nightly-binned g **and** r
  epochs (one row per white dwarf x band x night).
- **`data/raw/ztf_wd_zg.csv`** — 9,501 rows, the g-band nightly slice fed to the
  `ztf_wd` descriptor.
- **`data/raw/ztf_wd_zg_monthly.csv`** — 1,147 rows, the same g-band series
  re-binned monthly (the descriptor-of-record for the converged fit below).

The science framing is a **per-entity variance census** — the per-white-dwarf
random-walk variance posterior versus Jestin's variable-vs-constant split — not
pulsation-period recovery.

## What the panel can carry — and what the binning removes

Before any model runs, the panel itself decides which variability is
recoverable. Scatter-to-error ratio per star, nightly against monthly
(`python scripts/plot_variance_census.py`, reads the committed CSVs only):

![Variability census of the 19-star panel](figures/variance_census.png)

The compact pulsators pulse on **minutes-to-an-hour** periods — far below either
bin width — so nightly binning averages them out and monthly binning finishes
the job. At the monthly cadence that the converged fit actually uses, ZZ Ceti
lands at sd/err **0.8** (its month-to-month scatter is smaller than its own error
bar), and GW Vir, V777 Her and Old DAVs sit at 1.1–1.5, inside the range spanned
by stars Jestin calls constant. One paper-constant unclassified star
(`1410345596469085184`, sd/err 1.5) outranks three of the named pulsators.

| regime | example | sd/err nightly | sd/err monthly |
|---|---|---|---|
| double-band binary | `4318508939464901760` | 23.6 | 16.4 |
| WD-MS binary | `1191504471436192512` | 15.9 | 6.9 |
| CV | `3750072904055666176` | 4.3 | 4.8 |
| **pulsator** | ZZ Ceti | **1.5** | **0.8** |
| **pulsator** | GW Vir | **1.5** | **1.1** |
| paper-constant | `114808397128552576` | 1.0 | 0.4 |

So the census separates **hours-to-days** variability (binaries, the CV, the
transit) from constant cleanly, and is **structurally blind** to compact-pulsator
variability. That is a property of the event axis, not of the model: recovering
the pulsators means making the panel event the *exposure* rather than the night,
which changes the entity-event contract. Read the variance posteriors with that
scope in mind — "recovers the variable-vs-constant split" holds for the
long-period variables only.

Three per-star panels from the converged run, one per regime (all 19 are written
to `<run_dir>/reports/figures_readable/` by `scripts/plot_star_panels.py`):

| high-amplitude binary | pulsator, averaged flat | paper-constant |
|---|---|---|
| ![](figures/star_double_band_binary.png) | ![](figures/star_zz_ceti.png) | ![](figures/star_paper_constant.png) |

This is a validation sample. The full **864-source** companion table is pending
VizieR publication with the paper; the pipeline here scales to it by repointing
`data/roster/jestin2026_roster.csv` and re-running the two scripts
(`scripts/fetch_lightcurves.py`, then `scripts/build_panel.py`) — the dataset
descriptors are unchanged bar `target_bounds`.

## Reproduce

The panelcast invocation that converges (run against a panelcast checkout with
this repo's `configs/` and `data/` on the path):

```
panelcast run \
  --dataset configs/datasets/ztf_wd_monthly.yaml \
  --config configs/wd_fit.yaml \
  --no-artist --min-ratings 1 --max-albums 100 \
  --num-chains 4 --num-samples 3000 --num-warmup 3000 \
  --target-accept 0.90 --allow-unlocked-env
```

Diagnostics: **R-hat 1.00, bulk ESS 1,711, 0 divergences in 12,000 draws**.
The command above is canonical; `configs/wd_fit.yaml` carries both
identifiability pins (`heteroscedastic_entity_obs: false`,
`entity_group_pooling: false`).

### The convergence ladder

| Stage | Chains x samples | R-hat | ESS | What changed |
|---|---|---|---|---|
| Nightly | 2 x 500 | 2.44 | 2 | baseline nightly panel |
| Monthly | 4 x 1000 | 2.56 | 5 | monthly binning — multimodality is unidentifiability, not RW length |
| + entity-obs off, artist features off | 4 x 1000 | 1.008 | 395 | removed the unidentifiable components |
| + target-accept 0.90 | 4 x 3000 | 1.00 | 1,197 | mixes well; 2 divergences in the class-pooling funnel |
| + target-accept 0.93 | 4 x 3000 | 1.011 | 789 | 0 divergences via smaller steps — treats the symptom, costs mixing |
| + class pooling off, accept 0.90 | 4 x 3000 | 1.00 | 1,711 | removed the funnel itself — final config |

**Diagnosis.** These are near-constant series, so the model has interchangeable
explanations for the same data: the entity mean, AR persistence, and the random
walk all absorb the (tiny) variation, and global vs per-entity observation noise
trade off freely. Chains settle into different variance attributions — different
modes of one posterior, hence the high R-hat with zero divergences. Removing the
unidentifiable components (per-entity overdispersion and the entity-history
features) collapsed the modes into one. The last two divergences lived in the
class-pooling variance funnel — a between-`wd_class` scale the handful of groups
cannot inform; raising `target-accept` merely tiptoed around it, while dropping
the pooling term removed it and improved mixing at the same time.

## Per-domain verdicts

`heteroscedastic_entity_obs` (per-entity observation noise) is the AOTY default
as of panelcast **v0.13.0**, but is pinned **OFF** here in `configs/wd_fit.yaml`.
At N=19 near-constant series it is unidentifiable against the shared `sigma_obs`
/ `sigma_artist` terms — chains simply reallocate variance between them. This is
expected to **reverse at the 864-star roster**, where cross-entity pooling can
identify a per-entity noise scale. The pin follows the external-domain
run-config pattern from the panelcast v0.13.0 release notes.

`entity_group_pooling` (partial pooling across `wd_class`) is likewise pinned
**OFF**. With only a handful of classes over 19 stars, the between-class
variance is data-starved and its posterior develops the classic hierarchical
funnel — the source of the final 2 divergences on the ladder. Removing it
raised bulk ESS from 1,197 to 1,711 at the same `target-accept`. Also expected
to be revisited at 864 stars, where the class populations carry real weight.

## Porting gotchas

Found while adapting an album-ratings pipeline to photometry:

- **All-digit Gaia IDs must be carried as strings.** Gaia DR3 `source_id`s are
  19-digit integers; loaded as numerics they lose precision / collide, so the
  entity key is string-typed end to end.
- **AOTY min-obs defaults would delete single-exposure nights.** Most ZTF nights
  are a single exposure (median `n_exp` = 1); the music-domain minimum-ratings
  thresholds would discard the panel. The descriptors set
  `min_obs_thresholds: [1]` to keep everything.
- **The 50-event career cap vs 1000-night light curves.** AOTY entities top out
  at a few dozen releases; a white dwarf has hundreds to a thousand nights. The
  event axis had to be uncapped for the light-curve length.

## Layout

```
configs/
  datasets/ztf_wd.yaml          nightly g-band descriptor
  datasets/ztf_wd_monthly.yaml  monthly g-band descriptor (converged fit)
  wd_fit.yaml                   run-config pins (heteroscedastic_entity_obs: false,
                                entity_group_pooling: false)
scripts/
  fetch_lightcurves.py          resumable IRSA cone-search fetch -> data/raw/lc_cache/
  build_panel.py                bin cached epochs -> data/raw/ztf_wd_panel.csv
  plot_variance_census.py       panel-only variability census -> figures/
  plot_star_panels.py           readable per-star panels from a run dir
figures/
  variance_census.png           nightly-vs-monthly scatter/error, all 19 stars
  star_*.png                    three per-star panels, one per variability regime
data/
  roster/jestin2026_roster.csv  the 20-row roster (19 with usable ZTF light
                                curves) + _source_provenance/
  raw/ztf_wd_panel.csv          nightly g+r panel (19,950 rows)
  raw/ztf_wd_zg.csv             nightly g-band slice (9,501 rows)
  raw/ztf_wd_zg_monthly.csv     monthly g-band slice (1,147 rows)
  raw/lc_cache/                 cached raw IRSA responses (regenerable via fetch)
```

Pipeline byproducts (`data/processed/`, `data/splits/`, `data/features/`,
`data/audit/`, `outputs/`, `models/`, `*.log`) are gitignored; the two scripts
plus a panelcast run regenerate them.

## Data credits & citations

- **ZTF** — Zwicky Transient Facility public data releases; light curves fetched
  from IRSA's login-free `nph_light_curves` service.
- **Gaia DR3** — coordinates and G magnitudes via the Gaia TAP service.
- **Jestin+2026** — [arXiv:2509.15133](https://arxiv.org/abs/2509.15133), source
  of the white-dwarf roster excerpt.
- **panelcast** — https://github.com/cupidthatbtc/panelcast, the model and
  descriptor contract.

The roster in this repo is the paper's **published 11-row excerpt table plus its
individually-named stars only** — it is **not** the full 864-source catalog,
which publishes separately to VizieR.

## License

Code and configs are released under the **MIT License** (see `LICENSE`). The
photometry itself is public survey data credited above and carries the licenses
and acknowledgement requirements of ZTF, Gaia, and IRSA.
