# Lomb–Scargle × panelcast census — execution plan

Goal: determine, per star, what a periodogram finds in the exposure-level ZTF data that the
panelcast variance census could not (and vice versa), compare both against the Jestin+2026
flags, and produce the tables/figures that support those comparisons. Results only — no
presentation material. Every number must trace to a committed script.

## Context

- Repo: `C:\Users\jcwen\Projects\astro-wd` (publishes as `github.com/cupidthatbtc/panelcast-ztf-wd`).
  `git pull` first — the Mac pushed commit d6cd3f3 (census figure + README section) on 7/24.
- Raw per-exposure data: `data/raw/lc_cache/<gaia_source_id>.csv` — one file per star, both bands
  mixed (`filtercode` = zg/zr). Columns include `hjd`, `mjd`, `mag`, `magerr`, `catflags`, `chi`,
  `sharp`, `limitmag`, `exptime` (30 s), `ra`, `dec`, `programid`.
- Roster: `data/roster/jestin2026_roster.csv` — 20 stars, `wd_class`, `paper_variable`,
  `paper_periodic` flags. 19 have usable light curves.
- Census reference numbers (nightly and monthly sd/err per star): committed census script
  `scripts/plot_variance_census.py` regenerates them from the committed CSVs.
- Converged panelcast run (monthly, g): `outputs/2026-07-18_151420_993941_17ac`
  (R-hat 1.00, ESS 1,711, 0 divergences). Do not touch it.
- Census verdicts to beat/complement: 9 of 13 paper-variables separated at nightly cadence
  (double-band periodic 23.6×, WD-MS binaries 15.9/6.0/5.2, CV 4.3, transit 4.2, RRL contaminant
  3.9, double-band 2.9/2.7). All four pulsator classes missed (ZZ Ceti 1.5×/0.8×, GW Vir 1.5/1.1,
  V777 Her 2.0/1.3, Old DAVs 2.1/1.5). One oddball: `1410345596469085184` (WDJ163914.29+474835.84,
  paper-constant, census 2.2×/1.5×).

## Phase 0 — environment + smoke test

1. Python env: repo's existing venv + `astropy>=5.1` (has `LombScargle`, `LombScargleMultiband`,
   `BoxLeastSquares`, false-alarm methods). No gatspy — unmaintained; astropy covers multiband.
2. Smoke test before anything real: take one quiet star's g-band exposures, inject a sinusoid
   (P = 8 min, A = 30 mmag), confirm the pipeline below recovers P to within grid resolution with
   FAP < 1e-6. If this fails, fix the pipeline, not the threshold.

## Phase 1 — exposure-level rebuild + QC

New script `scripts/build_exposure_panel.py` → `data/raw/ztf_wd_exposures.csv`:

1. Quality cuts, applied per row and counted per star in a QC table: `catflags == 0`,
   `magerr > 0`, finite mag, `chi < 4`. Report rows kept/dropped per star per band — no silent drops.
2. Timestamps: compute **BJD_TDB** from `mjd` + roster RA/Dec via astropy
   (`Time(..., scale='utc', location=Palomar)` + `SkyCoord.light_travel_time(kind='barycentric')`).
   The provided `hjd` is heliocentric-UTC; for coherent searches at P ≈ 100–300 s over a 7.5-yr
   baseline, second-level timing errors smear phase — use BJD_TDB everywhere. Keep both columns.
3. Keep bands separate (zg, zr). Ignore zi if present (too sparse).
4. Per star per band, record: N_exp, baseline, median magerr, median exposures/night — these feed
   the sensitivity numbers later.

## Phase 2 — blind periodogram search

New script `scripts/run_lomb_scargle.py` → `outputs/ls/<timestamp>/` (respect the existing
outputs/ conventions; everything regenerable from the CSVs).

Two passes per star per band, error-weighted (`dy=magerr`), `method='fast'`,
`samples_per_peak=10`:

- **Low-frequency pass** (binaries/CV/eclipses/RRL): f from 2/baseline to 48 d⁻¹
  (P: 30 min → ~3.7 yr). Input: exposures with only the global mean removed.
- **High-frequency pass** (pulsators): f from 24 to 1440 d⁻¹ (P: 60 s → 1 hr). Input: exposures
  with **per-night median subtracted** — removes binary/eclipse/long-term power that otherwise
  leaks into the pulsation band. Note the grid is ~4×10⁷ frequencies at this baseline; the fast
  method handles it, chunk the frequency array if memory complains.
- **Multiband**: run `LombScargleMultiband` on g+r jointly for both passes; single-band runs are
  the cross-check.
- **BLS**: for the transit/eclipse star (`103999471976858496`) additionally run
  `BoxLeastSquares` over P = 1 hr – 30 d; L-S is the wrong matched filter for box shapes.

For each pass record the top 5 peaks: frequency, period, power, Baluev FAP
(`false_alarm_probability`, accounting for the searched grid), and L-S model amplitude at the
peak. For the single best candidate per star, refine FAP with `method='bootstrap'`
(≥100 resamples).

**Alias vetting** (required before any peak is called a detection):
- Compute the spectral window function; flag peaks within 1.5/T of f_window peaks or of
  n ± 1.0027 d⁻¹ (sidereal day) aliases of a stronger peak.
- Confirmed = same frequency in g and r (or multiband + one band) within 1.5/baseline, FAP < 1e-3.
- Candidate = one band only, FAP < 1e-3, survives alias check.
- Below that: not detected; goes in the upper-limit table instead.

**Positive controls — run these first and stop if they fail:**
1. RR Lyrae contaminant (`3345661467822106624`): must recover P ≈ 0.2–1 d at extreme
   significance with the classic RRL asymmetric fold.
2. Double-band periodic star (`4318508939464901760`, census 23.6×): must recover a clean period
   in both bands.
If either control fails, the pipeline is broken — do not proceed to the pulsators.

## Phase 3 — directed search at literature periods

Blind FAP pays a ~4×10⁷-trial penalty; a directed test at a known frequency is single-trial and
far more sensitive. For the named pulsators — ZZ Ceti `3446909137068558464`
(WDJ052038.32+304823.92), GW Vir `1893101535448502400` (WDJ220247.69+275010.67), V777 Her
`1510467090935595008` (WDJ135309.97+484021.17), Old DAV `3984115430179696128`
(WDJ111026.19+191229.75):

1. Find published pulsation periods: SIMBAD/VizieR by WDJ name and Gaia ID, plus the Jestin+2026
   paper itself (check `docs/` in the repo for a PDF; otherwise fetch). Record the source for
   every period used. If no literature period exists for a star, say so and skip it — do not
   guess.
2. Evaluate L-S power at each literature frequency (and its 1-day aliases) on the high-frequency
   residuals; report single-trial FAP and the measured amplitude with an uncertainty.
3. Verdict per star: detected at literature period / not detected with amplitude upper limit.

## Phase 4 — sensitivity: upper limits + injection–recovery

1. **Upper limits for every non-detection**: A_95 = the 95th-percentile L-S amplitude of the
   noise peaks in the relevant search band. Table: star, band, N_exp, A_95 in mmag. A
   non-detection with "A < 4 mmag (95%)" is a measurement, not a shrug.
2. **Injection–recovery** on two real light curves (one quiet paper-constant, e.g.
   `114808397128552576`, and one with median sampling): inject sinusoids at
   P ∈ {2, 5, 10, 20, 60 min}, A ∈ {2, 5, 10, 20, 50 mmag}, 20 random phases each. For every
   injection compute all three detectors:
   - exposure-level L-S (FAP < 1e-3),
   - nightly census ratio (threshold 2.5, matching the observed constant band ceiling),
   - monthly census ratio (same threshold).
   Output: recovery-fraction grid per detector. This is the quantitative version of "the census
   is structurally blind to pulsators and the periodogram is not" — and it also shows where
   *both* fail (lowest amplitudes), which keeps it honest.
3. **Close the attenuation loop**: for every confirmed periodic detection, predict the surviving
   nightly-binned variance from the measured A, the per-night n_exp, and random-phase averaging
   (var_night ≈ A²/2 · 1/n_exp for P ≪ night span); compare predicted sd/err against the census's
   observed nightly ratio, one row per detected star. If the arithmetic matches the census, the
   two methods corroborate each other instead of merely disagreeing.

## Phase 5 — the comparison tables (the actual product)

`RESULTS.md` in the run output dir, containing — for **all 19 stars, no cherry-picking**:

1. **Master table**: star, WDJ name, class, paper_variable, paper_periodic | census nightly ratio,
   census monthly ratio | L-S best period, FAP, amplitude (or A_95 upper limit) | BLS where run |
   directed-search verdict | final concordance code.
2. **Concordance summary**: of the 13 paper-variables — how many recovered by census, by L-S, by
   the union; of the paper-constants — false-alarm count for each method. Expected story shape:
   census 9/13 + 0 false alarms, L-S adds some or all of the 4 pulsators, union ≥ census, and the
   oddball is whatever it turns out to be. Report what the data says even if it breaks this shape.
3. **Period accuracy**: for every star where Jestin+2026 or the literature states a period, yours
   vs theirs, in seconds/days as appropriate.
4. **The oddball** (`1410345596469085184`): L-S verdict at both passes + g-vs-r census
   concordance (compute the census ratios on r-band nightly bins — the committed census is
   g-only). Three outcomes, all reportable: periodic (new candidate with a period), aperiodic
   excess in both bands (census-only detection — L-S can't see it, which is *the census's* win),
   or g-only artifact (retract it, which is also a result).
5. **Figures** (matplotlib, committed script, no seaborn): periodogram per star (both passes,
   alias lines marked); phase-folded light curve for every confirmed detection — this is the
   proof artifact; the injection–recovery grid (3 panels, one per detector); predicted-vs-observed
   attenuation scatter.

## Panelcast: what to change (and what not to)

- **No model changes.** Do not add a periodic latent, do not refit at exposure level. The RW over
  binned means is the forecasting product and it converged; the census is a descriptor-side
  statistic; the periodogram is deliberately a *different* instrument. The comparison is the
  point.
- **Census script extension** (data-side, cheap): add the exposure-level high-frequency excess
  variance (per-night-median-subtracted) as a third column to `plot_variance_census.py`, and add
  r-band ratios. Three-cadence census (exposure/night/month) × two bands.
- **Optional, only if time permits after everything above**: an r-band monthly panelcast fit
  (config change only — new descriptor from the zr rows, same model). Per-star posterior
  concordance g vs r is a nice robustness result but is strictly lower priority than the L-S work.

## Guardrails

- Do not modify or re-run anything under `outputs/2026-07-18_151420_993941_17ac`.
- Every table number regenerable by a script in `scripts/`; no hand-edited values.
- Report FAPs with the trials context stated (blind grid vs single-trial directed).
- Detections require the alias vet + two-band (or multiband) agreement. One-band peaks are
  candidates, labeled as such everywhere.
- All 19 stars appear in every table. Non-detections carry upper limits, not blanks.
- Don't push to GitHub until Jack reviews RESULTS.md.

## Acceptance checklist

- [ ] Smoke-test injection recovered before real runs
- [ ] Both positive controls recovered (RRL, double-band star) with periods stated
- [ ] QC table: rows kept/dropped per star
- [ ] BJD_TDB used for the high-frequency pass
- [ ] Master table covers 19/19 stars
- [ ] Every pulsator has: blind result, directed result (or "no literature period found",
      sourced), and an amplitude upper limit if undetected
- [ ] Injection–recovery grid computed for all three detectors
- [ ] Attenuation-loop table for every confirmed detection
- [ ] Oddball star has a three-way verdict (periodic / both-band aperiodic / g-only artifact)
- [ ] RESULTS.md written, nothing pushed
