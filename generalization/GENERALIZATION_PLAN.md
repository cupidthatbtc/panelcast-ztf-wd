# Generalization campaign: three-dataset selection-function measurement

Branch `generalization/campaign-1` · frozen baseline tag `frozen-2026-08-01` ·
deadline AAS 249 regular abstract Tue 2026-09-30.

## Claim under test

The 2026-08-01 ZTF white-dwarf run showed the variance census and the blind
Lomb-Scargle search have complementary selection functions — but on 19
truth-labeled stars, with a known mechanism, and injections conditioned on two
light curves. Red-team verdict: NO-GO as a discovery claim. The flip condition:
run the *frozen* pipeline on independently labeled samples large enough to
measure class-specific completeness and false-positive rate with uncertainty.
This campaign does exactly that and nothing else.

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
`94…` D2 statistical nulls. No collision with Gaia DR3 ids; always valid for
the frozen seed convention.

### Replay gate (blocks everything)

`replay_gate.py` re-runs the frozen `analyze_star` through `frozen_api` on 25
published stars (all 7 schema-v2 + 18 stride-sampled schema-v1) and
byte-compares against the committed bundle. Comparison tiers: raw-identical;
identical after CRLF→LF normalization (git stored the bundle normalized);
identical after the documented v1→v2 schema transform — 921/928 published
files were written before commit `fa16d7f`, which added the
`available`/`unavailable_reason` keys and bumped `schema_version` 1→2 while
changing no numeric code path (diff on record). Gate passes only with zero
mismatches AND at least one schema-v2 star reproducing with no transform.
Campaign L-S runs are valid only on machine+env pairs that passed the gate.

### Environment

The published run's venv (laptop `jacks-7i-5090`) is recorded in
`generalization/env/FROZEN_ENV.md`; the numerics-bearing subset is pinned in
`requirements-frozen.txt` (Python 3.12.12, numpy 2.3.x, scipy 1.16.3, astropy
8.0.1, iers-data 0.2026.7.27, pyerfa 2.0.1.5, pandas 2.3.3). Discrepancy on
record: pip metadata said numpy 2.3.3 but the venv imports 2.3.5; the replay
gate verdict on that venv is the authority on whether the published numbers
reproduce under what is actually installed. requirements-frozen.txt is updated
to whatever passes the gate, and the manifest of every campaign run records
`env_versions()` at runtime.

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
- Roster (`build_d3_roster.py`, built 2026-08-28, deterministic, no RNG):
  gmag ≥ 13.2 (ZTF saturation), ALL 610 dSct=1 survivors + ALL 76 dSct=2
  (own class, excluded from headline numbers) + 2,314 dSct=0 negatives
  stride-sampled in KIC order = 3,000. Amplitude coverage of positives:
  456/610 with dominant amplitude; 48 > 10 mmag; 254 in 1–10; 154 < 1;
  290 sub-hour; median 1.77 mmag. The 1–10 mmag log ladder and the
  sub-threshold majority make the completeness turn-on curve the headline
  D3 deliverable, not a defect (pre-registered: risk 2).
- Acquisition: frozen `fetch_catalog_lightcurves.py --roster roster_d3.csv`
  verbatim (10″ cone, 1.25 s cadence, resumable); frozen QC chain via
  `build_panels_generic.py` (nearest-cluster crossmatch, catflags/chi cuts,
  ≥20 exp/band, BJD_TDB at Palomar — all frozen functions).
- Prespecified subsets: crowding (sep < 1.0″, ≤3 objects in cone),
  near-saturation (g < 14 flagged; g > 14 safe subset).
- Caveat on record: dSct=0 means "not a delta Scuti", not "constant" —
  D3 FPR is an upper bound.

## D2 — TESS-truth transplant (DAV signals in real ZTF windows)

- Truth: Romero+2022 (MNRAS 511, 1574; arXiv:2201.04158; 74 new DAVs,
  TESS Cy1–3) + Romero+2025 (ApJ 984, 112; arXiv:2407.07260; 32 new DAVs,
  Cy4–5). Published per-mode tables: period [s] + amplitude [ppt] + per-star
  FAP(1/1000) limit + 20-s-cadence flags. 2025 revisions apply: NOV
  retractions (TIC 261400271, 804835539, 317620456) and updated mode lists
  for re-observed 2022 objects — latest published solution wins.
- Truth model, not interpolation (`d2_truth_model.py`): DAV P < 240 s is
  super-Nyquist AND past the first sinc null of TESS 120-s data; the mode
  table is evaluated analytically at the template's real `bjd_tdb`.
  Chain: ppt → mag (×1.0857e-3) → de-dilution OFF by default (SPOC PDCSAP is
  crowding-corrected; ON = prespecified variant) → de-integrate TESS sinc
  (reject modes with |sinc| < 0.3, i.e. P < 197 s from 120-s data; prefer
  20-s cadence solutions) → bandpass ladder A_g/A_TESS ∈ {1.4, 1.7, 2.1} ×
  A_r/A_g ∈ {0.70, 0.80, 0.90} (nominal 1.7/0.80 from an in-code blackbody
  derivative; the ladder is non-optional — zr carries most published
  confirmations) → re-integrate ZTF 30-s sinc analytically → compose
  phase-coherently in zg and zr (shared t_ref) so the frozen two-band rule
  keeps its meaning.
- Windows: templates from the 510 not-detected stars of the published run,
  matched by median zg mag (|Δg| ≤ 0.25), K=3 templates per target at
  10/50/90th percentile of exposures-per-night (75% of zg nights are
  single-exposure; per-night median subtraction annihilates 53% of zg data —
  D2 largely measures that penalty; pre-registered, stratified: risk 3).
- Arms: B primary (signal + real ZTF mags, real magerr), A diagnostic
  (synthetic Gaussian floor). FPR: 1,000 arm-A zero-amplitude nulls over
  1,000 distinct real windows (Wilson upper ~0.4% at zero confirmed);
  arm-B nulls are tautological (templates ARE the not-detected set).
  Verification arm: ~20 SPOC light curves prewhitened to confirm published
  solutions; everything else needs metadata only.

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
  D3@3,000 ≈ 1.2–1.9 d; D2 ≈ 1 d; hard stop via 150-star timing pilot.
  Disk binds, not time: `workers = min(22, floor(free_GB × 0.5 / 0.47))`,
  scratch on local NVMe/RAM disk, never a synced folder.
- Results bundles: `generalization/results/<date>_<dataset>/` mirroring the
  existing convention (README, DATA_PROVENANCE, SHA256SUMS, acceptance.json).

## Review gates (sol@xhigh + ChatGPT Pro standing directive)

| Gate | When | Reviewer | Scope |
|---|---|---|---|
| G1 | now | sol ×3 | dataset choices, architecture, label independence, referee objections |
| G2 | end W1 | sol ×5 | this file + METRICS_SPEC.md; frozen only after unanimous/addressed |
| G3 | W2 pre-batch | Pro (inline code) | d2_truth_model + build_d2_shards: sinc algebra, bandpass, phase coherence, schema |
| G4 | W3 mid-run | sol ×2 | pilot metrics sanity, run anomalies |
| G5 | W4 | Pro + fresh-context verifier | results audit; every headline number re-derived from JSONs/CSVs |
| G6 | Sep 26–29 | sol ×3 + ars-abstract | final abstract |

## Timeline

- W1 (Aug 28–Sep 3): tag+branch ✓, replay gate ✓(running), env pinning ✓,
  frozen_api+tests ✓, D3 roster ✓, D3 IRSA fetch (overnight, running),
  D2 sources downloaded ✓, PLAN+SPEC (this commit), G1, G2, D2 roster parser.
- W2 (Sep 4–10): build_panels_generic on D3 → census; d2_truth_model + tests
  + G3; build_d2_shards; verify_cli_identity; 150-star pilot; wake desktop.
- W3 (Sep 11–17): D3 full run (laptop) ∥ D2 (desktop); metrics+plots against
  pilot output; G4.
- W4 (Sep 18–25): metrics, ladders, figures, bundles, acceptance; G5;
  cross-dataset synthesis table.
- Sep 26–30: abstract + G6; submit.
- Slip rule: if only one new dataset lands by Sep 25, D2 alone + D1 flips the
  red-team condition; the abstract states D3 as in progress.

## Top risks

1. Env fails replay → pin/iterate until byte-identical; blocks all work.
2. D3 completeness ≈ 0 below the a95 floor → stratification IS the
   deliverable (turn-on curve).
3. D2 high-pass ≈ 0 from the single-exposure-night penalty → pre-registered
   expected headline, stratified to be explanatory.
4. A_r/A_g lever → mandatory ladder; headline reported as a band.
5. D3 negatives not constants → FPR an upper bound, stated.
6. Desktop unreachable → D2 on laptop after D3 (+1 day).
7. Romero mode tables are LaTeX prose with typos (comma decimals, stray
   units) → parser with hard row-count and range asserts; G3 reviews the
   parsed output against the PDFs.

## Mandatory citations

Sokolovsky+2017 (variability-index benchmark; data not public — comparison
baseline only), Guidry+2021, Hermes+2017, Murphy+2019, Bowman+2016 (context),
Mo+2026, Romero+2022, Romero+2025, Gentile Fusillo+2021, Masci+2019.
