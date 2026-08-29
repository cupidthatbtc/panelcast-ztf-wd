# Generalization campaign: three-dataset response assessment of the frozen pipeline

Branch `generalization/campaign-1` · frozen baseline tag `frozen-2026-08-01` ·
deadline AAS 249 regular abstract Wed 2026-09-30.

## Claim under test

The 2026-08-01 ZTF white-dwarf run showed the variance census and the blind
Lomb-Scargle search have complementary selection functions — but on 19
truth-labeled stars, with a known mechanism, and injections conditioned on two
light curves. Red-team verdict: NO-GO as a discovery claim. The flip condition:
run the *frozen* pipeline on externally labeled samples large enough to
measure class-specific response rates with uncertainty.

G1 review (sol ×3, 2026-08-28) sharpened what this campaign can honestly
claim — THREE SEPARATE response assessments, never pooled into one
"selection function":
- D1: the anchor (19 labeled WDs + 928-star catalog, published);
- D2: conditional injection-recovery efficiency of the frozen search stage
  (TESS-truth signals in real ZTF windows) — labeled as such, NOT real-sky
  completeness and NOT an independently labeled sample;
- D3: externally labeled, magnitude-restricted validation on real ZTF
  photometry (detection completeness, frequency recovery, negative-class
  trigger rate).
Banned phrases (G1): "quantified selection-function measurement", "real-sky
completeness" (for D2), "D3 FPR", unqualified "purity". Estimand names in
METRICS_SPEC.md are binding.

## Frozen-core / adapter-shell architecture

- Tag `frozen-2026-08-01` = branch point. Zero edits to any script that
  produced the published bundle; the referee check is an empty
  `git diff frozen-2026-08-01 -- scripts/<frozen five>`.
- Frozen five: `run_catalog_lomb_scargle.py`, `run_lomb_scargle.py`,
  `lomb_scargle_common.py`, `build_catalog_panels.py`,
  `fetch_catalog_lightcurves.py`. SHA-256 pinned in
  `scripts/generalization/frozen_api.py`; `assert_frozen()` runs at import and
  at the top of every campaign script.
- Campaign code lives in `scripts/generalization/` and imports the frozen
  callables only through `frozen_api`. The frozen CLI never runs on campaign
  data (its `main()` merges the WD roster and rewrites the published table);
  `verify_cli_identity.py` proves the import path is byte-identical to the
  CLI's internal call path.
- Known frozen quirks are pinned by `tests/test_frozen_constants.py`, fixed by
  nothing: the `>= 2.5` vs `> 2.5` census inconsistency (provably
  non-affecting: 0 of 5,568 published ratios within 1e-4 of 2.5; campaign
  metrics use `>=` and assert no campaign ratio equals 2.5 exactly), the
  bootstrap's `int(source_id[-9:])` seed (harmless for 19-digit numeric
  campaign ids by construction), duplicated pass-bound literals (AST-scan
  test).

### Campaign source_id convention

19-digit numeric strings: `90…` D3 targets, `92…` D2 arm B, `93…` D2 arm A,
`94…` D2 Gaussian nulls, `95…` D2 paired real-window controls. No collision
with Gaia DR3 ids; always valid for the frozen seed convention.

### Replay gate (blocks everything)

`replay_gate.py` re-runs the frozen `analyze_star` through `frozen_api` on 25
published stars (all 7 schema-v2 + 18 stride-sampled schema-v1) and
byte-compares against the committed bundle. Comparison tiers: raw-identical;
identical after CRLF→LF normalization (git stored the bundle normalized);
identical after the documented v1→v2 schema transform — 921/928 published
files were written before commit `fa16d7f` (parent `e917bd1`), which added
sparse-input early-exit branches plus the `available`/`unavailable_reason`
keys and bumped `schema_version` 1→2. For any star that yields candidates,
the numeric path is unchanged (the new branches fire only on sparse inputs
that previously crashed; all 7 v2 records exercise exactly those branches).
The downgrade transform removes only the two added keys and byte-compares
everything retained. Gate passes only with a nonempty roster, zero
mismatches AND at least one schema-v2 star reproducing with no transform
(unconditional). VERDICT 2026-08-28 (jacks-7i-5090, production venv):
PASS — 7 identical_newline + 18 identical_v1_schema, 25/25.
Campaign L-S runs are valid only on machine+env pairs that passed the gate;
`run_generalization_ls.py` refuses to start without a matching PASS
attestation (full env fingerprint + frozen SHAs + gate identity). Full
928-star baseline replay running on the production machine (launched
2026-08-28). Panel-stage golden gate (`panel_golden_gate.py`): PASS on both
machines 2026-08-28 — science columns byte-identical vs the published
exposure panel; bjd_tdb ≤ 1 ulp (~40 µs) on ~2.5% of rows (the barycentric
chain sits at rounding boundaries; ns-level IERS-state drift since build
time flips the last bit — measured on the production machine itself);
campaign builds pin IERS via astropy-iers-data with auto_download off.

### Environment

The published run's venv (laptop `jacks-7i-5090`) is recorded in
`generalization/env/FROZEN_ENV.md`; the numerics-bearing subset is pinned in
`requirements-frozen.txt` (Python 3.12.12, numpy 2.3.x, scipy 1.16.3, astropy
8.0.1, iers-data 0.2026.7.27, pyerfa 2.0.1.5, pandas 2.3.3). Discrepancy on
record: pip metadata said numpy 2.3.3 but the venv imports 2.3.5; the replay
gate PASSED under 2.3.5 (2026-08-28), making 2.3.5 the pinned authority.
Every campaign-run manifest records `env_versions()` (incl. BLAS vendor and
thread env vars) at runtime.

## D1 — ZTF white dwarfs (anchor, done)

The published 2026-08-01 bundle: 19-star truth roster + 928-star catalog.
No re-run; campaign metrics re-read the published per-star JSONs.

## D3 — ZTF × Kepler delta Scuti (real ZTF light curves, external labels)

- Labels: Murphy+2019 (VizieR J/MNRAS/485/2380/table1, 14,330 Kepler A/F
  stars; `dSct` flag 0/1/2 — ships its own labeled negative class).
- Amplitude axis: Mo+2026 (J/A+A/710/A245): table2 = 259,883 extracted
  frequencies (SNR>8) for 1,838 delta Scutis → per-star dominant amplitude
  (ppt × 1.0857 → mmag); table1 = confirmed super-Nyquist modes → the
  sub-hour stratum (any confirmed SNF ⇒ real mode above Kepler LC Nyquist
  283.2 µHz ⇒ P < 59 min). This replaces the originally scouted Bowman+2016
  join: Bowman's VizieR table carries no amplitudes; Mo+2026 supersedes it
  (and is itself the published Murphy×Bowman merge, 1,838 stars).
- Roster (`build_d3_roster.py`, rebuilt 2026-08-28 post-G1): gmag ≥ 13.2
  (Murphy/KIC g magnitude — the named saturation proxy), ALL 610 dSct=1
  survivors + ALL 76 dSct=2 (own class, excluded from headline numbers) +
  2,314 dSct=0 negatives as a frozen-seed (20260828) simple random sample
  (inclusion probability exactly 2314/7292, weight exactly 7292/2314;
  sampling_weight column carried into every weighted estimate) = 3,000.
  Before any campaign L-S run, the realized crossmatch mapping and an
  ambiguity-adjudication file are committed (crossmatch frozen as DATA,
  not just procedure). Amplitude coverage of positives:
  456/610 with dominant amplitude; 48 > 10 mmag; 254 in 1–10; 154 < 1;
  290 sub-hour; median 1.77 mmag. The 1–10 mmag log ladder and the
  sub-threshold majority make the completeness turn-on curve the headline
  D3 deliverable, not a defect (pre-registered: risk 2).
  Sub-hour stratum caveat (binding): a confirmed Mo super-Nyquist frequency
  establishes a sub-hour signal in the KEPLER APERTURE, not automatically
  in the ZTF-matched source (blends), and the per-star dominant amplitude
  need not describe the super-Nyquist mode; sub-hour-stratum detections are
  adjudicated in W4 alongside triggered negatives, and Mo amplitude
  sinc-correction status gets verified against the paper in W3.
- Acquisition: frozen `fetch_catalog_lightcurves.py --roster roster_d3.csv`
  verbatim (10″ cone, 1.25 s cadence, resumable); frozen QC chain via
  `build_panels_generic.py` (nearest-cluster crossmatch, catflags/chi cuts,
  ≥20 exp/band, BJD_TDB at Palomar — all frozen functions).
- Prespecified subsets: crowding (sep < 1.0″, ≤3 objects in cone),
  near-saturation (g ≤ 14.0 flagged; g > 14.0 safe subset — the PRINCIPAL
  robustness lens: KIC g is only a saturation proxy and bright A/F stars
  can still saturate in r; per-epoch saturation is additionally handled by
  the frozen catflags QC).
- Caveat on record: dSct=0 means "not a delta Scuti", not "constant" — the
  D3 negative-class result is a TRIGGER RATE (never called FPR); triggered
  negatives get adjudicated in W4 (plausible real variable vs unexplained).

## D2 — TESS-truth transplant (DAV signals in real ZTF windows)

- Truth: Romero+2022 (MNRAS 511, 1574; arXiv:2201.04158; 74 new DAVs,
  TESS Cy1–3) + Romero+2025 (ApJ 984, 112; arXiv:2407.07260; 32 new DAVs,
  Cy4–5). Published per-mode tables: period [s] + amplitude [ppt] + per-star
  FAP(1/1000) limit + 20-s-cadence flags. 2025 revisions apply: NOV
  retractions (TIC 261400271, 804835539, 317620456) and updated mode lists
  for re-observed 2022 objects — latest published solution wins.
- Truth model, not interpolation (`d2_truth_model.py`): for 120-s sampling,
  DAV P < 240 s is super-Nyquist (Nyquist period 240 s) and the boxcar
  integration response has its first null at P = 120 s — two distinct
  boundaries, both making interpolated TESS photometry undefined in the DAV
  range; the mode table is evaluated analytically at the template's real
  `bjd_tdb`. Chain: ppt → mag (×1.0857e-3) → de-dilution OFF by default
  (SPOC PDCSAP is crowding-corrected; ON = prespecified variant) →
  de-integrate the TESS boxcar (signed sinc; REJECT modes with
  |sinc| < 0.3, i.e. P < ~160 s at 120-s cadence, P < ~27 s at 20-s);
  cadence precedence is algorithmic: cadence_s (an EFFECTIVE integration
  time; TESS timestamps are exposure midpoints, as the signed-sinc algebra
  assumes) = 20 iff the star's chosen published solution includes any "f"
  (20-s) sector, else 120 →
  bandpass ladder A_g/A_TESS ∈ {1.4, 1.7, 2.1} × A_r/A_g ∈
  {0.70, 0.80, 0.90} — a PHENOMENOLOGICAL SENSITIVITY GRID, not a derived
  physical range: the blackbody T-derivative at 11,500 K gives (1.43, 0.80)
  ≈ the low rung (not band-integrated, no limb darkening, l-independent);
  the ADOPTED nominal (1.7, 0.80) is the grid midpoint; DA-atmosphere
  band-integrated validation of the endpoints is a stated limitation (the
  ladder is non-optional — zr carries most published confirmations) →
  re-integrate the ZTF 30-s boxcar analytically → compose with the FROZEN
  phase protocol: one independent phase per mode; base assignment
  (phase_draw = 0) seeds PCG64(TIC) and is shared across bands and across
  every bandpass/de-dilution/amplitude-scale variant; the two phase-draw
  sensitivity variants d ∈ {1, 2} seed PCG64(TIC·10 + d) and change ONLY
  the phase vector; shared t_ref keeps the frozen two-band rule meaningful.
- Windows: templates from ALL 928 stars of the published catalog (G1 fix —
  the earlier 510-not-detected pool conditioned on the pipeline's own
  outcome), matched by median zg mag (|Δg| ≤ 0.25, widened when thin;
  flagged), K=3 per target at 10/50/90th percentile of exposures-per-night
  (75% of zg nights are single-exposure; per-night median subtraction
  annihilates 53% of zg data — pre-registered, stratified: risk 3).
  Template matching is a TOTAL deterministic algorithm (zero analyst
  discretion): candidate pool = stars with |median_zg − target_G| ≤ 0.25;
  if fewer than 3, the pool widens once to ≤ 0.5; if still fewer than 3,
  the pool is the 9 smallest |Δmag| stars, magnitude ties broken by
  ascending source_id (pandas argsort is stable over the source_id-sorted
  stats table); the pool is then sorted lexicographically by
  (median exposures-per-night, source_id) — a total order, so no residual
  ties — and picks are indices round-half-even(q·(n−1)) for
  q ∈ {0.10, 0.50, 0.90} (numpy round). Match label recorded per target.
  D2 primary detection is post-injection rule firing (detection-only);
  strict frequency matching is the separate frequency-recovery estimand;
  native variability in the pool is contextualized by PAIRED UNINJECTED
  CONTROLS (95-prefix; stable ids indexed over the sorted 928 pool): one
  control shard per unique arm-B template window. W2 stretch: fetch real
  ZTF light curves at the 103 Romero positions; usable self-windows form a
  SEPARATE DIAGNOSTIC arm — they do not replace or enter the nominal K=3
  aggregate.
- Arms: B primary (signal + real ZTF mags, real magerr), A diagnostic for
  positive injections; arm-A ZERO-AMPLITUDE NULLS are the campaign's sole
  confirmatory endpoint (P5, METRICS_SPEC). Gaussian-null false-alarm rate
  (`FPR_Gaussian`): 1,000 arm-A zero-amplitude simulations scheduled over
  the 928-window frame by deterministic cycling (serial i → sorted-pool
  window i mod 928, noise seed = serial); windows repeat, seeds do not.
  Verification arm: ~20 SPOC light curves prewhitened to confirm published
  solutions; everything else needs metadata only.
- Run matrix (22 workers ≈ 84 runs/h). CORE scheduled total ≤ 3,266 ≈
  1.6 d, all binding: arm B nominal (1.7/0.80) 103×3 = 309; arm A nominal
  309; Gaussian nulls 1,000; paired controls ≤ 309 (unique arm-B windows);
  ladder sensitivity MEDIAN-WINDOW-CONDITIONED: 8 non-nominal (R_g, R_rg)
  points × 103 × 1 = 824; phase-draw sensitivity 2 × 103 = 206;
  amplitude-stationarity axis (scale × {0.7, 1.3}) 2 × 103 = 206;
  dominant-mode-dropout variant ≤ 103 (targets with ≥ 2 modes) — the
  ±30% multiplier is a LOCAL sensitivity, not an astrophysical envelope;
  DAV modes can vanish outright between epochs, which dropout probes
  (all sensitivity axes: median window, arm B nominal ratios).
  Stretch additions listed separately: Romero self-window diagnostic
  (count set by crossmatch yield); de-dilution variant only for the SPOC
  verification-arm stars (CROWDSAP comes with the ~20 downloads).
  Every sensitivity contrast uses the common-subset rule (METRICS_SPEC).
- Truth-model corrections found at implementation (2026-08-28): |sinc| ≥ 0.3
  rejection corresponds to P < ~160 s at 120-s cadence (the earlier "197 s"
  was the |sinc| = 0.5 point); D2 min published period is 115.9 s and 49/103
  stars carry 20-s solutions, so few modes are affected. Phase protocol is
  frozen above (per-mode independent; PCG64(TIC) base; PCG64(TIC·10+d)
  for the two phase-draw variants). Blackbody derivative at 11,500 K gives
  (1.43, 0.80) ≈ the 1.4/0.80 low rung; upper rungs cover
  atmosphere-model/limb-darkening uncertainty; 1.7 is the adopted midpoint.

## Metrics — see METRICS_SPEC.md (frozen before any campaign L-S run)

## Execution topology

- Mac: rosters, fetches, shard building, metrics, figures, git (authoritative).
- Laptop `jacks-7i-5090` (22 workers): replay gate + D3 run. Desktop
  (needs wake; offline 64 d): D2 + D3 overflow; if unreachable, D2 runs on
  the laptop after D3 (+1 day; slip rule below).
- Windows job launches escape the sshd job object via WMI
  `Win32_Process.Create` (Start-Process children die with the ssh session —
  found the hard way on the first replay launch).
- Wall model (anchor 928 ≈ 11 h at 22 workers; cost scales with baseline):
  D3@3,000 ≈ 1.2–1.9 d; D2 core ≈ 1.5 d; hard stop via 150-star pilot.
  Disk binds, not time: `workers = min(22, floor(free_GB × 0.5 / 0.47))`,
  scratch on local NVMe/RAM disk, never a synced folder.
- Results bundles: `generalization/results/<date>_<dataset>/` mirroring the
  existing convention (README, DATA_PROVENANCE, SHA256SUMS, acceptance.json).

## Review gates (sol@xhigh + ChatGPT Pro standing directive)

| Gate | When | Reviewer | Scope |
|---|---|---|---|
| G1 | DONE 2026-08-28 | sol ×3 | 47 findings; dispositions in reviews/G1/RESPONSE.md; design fixes applied same day |
| G2 | **FROZEN 2026-08-28** | sol, 6 rounds (5+4+3+3 reviewer-passes) | unanimous FREEZABLE at round 6; ~90 findings addressed across rounds (ledgers in reviews/G2*/RESPONSE.md); frozen SHAs: METRICS_SPEC.md 5d8d589ae73a608a…, GENERALIZATION_PLAN.md 8487f14f9480612f… (full values in reviews/G2_FREEZE.md) |
| G3 | W2 pre-batch | Pro (inline code) | d2_truth_model + build_d2_shards: sinc algebra, bandpass, phase coherence, schema |
| G4 | W3 mid-run | sol ×2 | pilot metrics sanity, run anomalies |
| G5 | W4 | Pro + fresh-context verifier | results audit; every headline number re-derived from JSONs/CSVs |
| G6 | Sep 26–29 | sol ×3 + ars-abstract | final abstract |

## Timeline

- W1 (Aug 28–Sep 3): tag+branch ✓, replay gate PASS 25/25 ✓ (full-928
  baseline running), panel golden gate PASS both machines ✓, env pinning ✓,
  frozen_api+tests ✓, D3 roster ✓, D3 IRSA fetch (overnight, running),
  D2 sources downloaded ✓, PLAN+SPEC (this commit), G1, G2, D2 roster parser.
- W2 (Sep 4–10): build_panels_generic on D3 → census; d2_truth_model + tests
  + G3; build_d2_shards; verify_cli_identity; 150-star pilot; wake desktop.
- W3 (Sep 11–17): D3 full run (laptop) ∥ D2 (desktop); metrics+plots against
  pilot output; G4.
- W4 (Sep 18–25): metrics, ladders, figures, bundles, acceptance; G5;
  cross-dataset synthesis table.
- Sep 26–30: abstract + G6; submit.
- Slip rule (revised at G1 — the old "D2 alone flips the condition" claim is
  untenable since D2 is not an externally labeled sample): D3 is the dataset
  that satisfies the external-label condition; if only ONE new dataset can
  land by Sep 25 it must be D3, with D2 stated as in progress. If only D2
  lands, the abstract is scoped to injection-recovery + D1 and makes no
  external-validation claim.

## Top risks

1. Env fails replay → pin/iterate until byte-identical; blocks all work.
2. D3 completeness ≈ 0 below the a95 floor → stratification IS the
   deliverable (turn-on curve).
3. D2 high-pass ≈ 0 from the single-exposure-night penalty → pre-registered
   expected headline, stratified to be explanatory.
4. A_r/A_g lever → mandatory ladder; nominal estimate + prespecified
   finite-grid sensitivity range (never called a band/CI).
5. D3 negatives not constants → negative-class trigger rate with W4
   adjudication (never called FPR).
6. Desktop unreachable → D2 on laptop after D3 (+1 day).
7. Romero mode tables are LaTeX prose with typos (comma decimals, stray
   units) → parser with hard row-count and range asserts; G3 reviews the
   parsed output against the PDFs.

## Mandatory citations

Sokolovsky+2017 (variability-index benchmark; data not public — comparison
baseline only), Guidry+2021, Hermes+2017, Murphy+2019, Bowman+2016 (context),
Mo+2026, Romero+2022, Romero+2025, Gentile Fusillo+2021, Masci+2019.
