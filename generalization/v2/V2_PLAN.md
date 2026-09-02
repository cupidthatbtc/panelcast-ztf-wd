# v2 detector arm — pre-registration (2026-09-02; revised the same day after the sol review, before any registered run)

Status: PRE-REGISTERED at the commit that adds this file, `split.csv`, the
runner id lists, `scripts/v2/` and the tests. The SHA-256 values below are
quoted from `split_manifest.json`. Any later change is an AMENDMENT (dated
entry in §10, with reason) and must precede the holdout run. The frozen
campaign (`GENERALIZATION_PLAN.md`, `METRICS_SPEC.md`, results/2026-09-02_d3,
the D2 full run) is not edited by anything here.

## 1. Purpose, relation to the frozen arm, and what this validation is

The frozen arm (rule 1, best pass) is the CONTROL: on D3 it fires on 54 % of
δ Sct and on 42 % of labeled non-pulsators, recovers the dominant frequency
for 16 % (≈ 40× chance); on D2 recovery is ~16 % and rides on within-night
support. The campaign's descriptive tables (results/2026-09-02_d3/
descriptive_postlaunch; the D2 mid-run peek is disclosed in the ledger and is
NOT used here) diagnosed four mechanisms:

| # | Mechanism (frozen) | Evidence | v2 fix |
|---|---|---|---|
| 1 | every ZTF oid within 1.5″ merged with no zero-point alignment; low pass subtracts one weighted mean → oid steps become slow power + alias combs | P3 0 % (1 oid) → 24 % → 47 % → 48 % (≥ 5 oids) | per-oid, per-band zero-point alignment on shared nights before anything else |
| 2 | alias veto = sidereal family only (k·1.00274 ± 1.5/T) + local window test | false triggers in 1−δ / 2−δ wings, lunar-synodic cluster (0.034 c/d), 1 / 2 c/d cores | veto on spectral-window loci (solar, sidereal, lunar, yearly sidebands, lunar–solar beats, data-driven top-N window peaks) + alias-of-stronger with solar AND sidereal spacing, difference AND mirror families, cross-pass partners |
| 3 | two-band rule = two Baluev votes or one vote + a power-sum "multiband" top-5; no joint model, no phase test | detection ≫ recovery on both datasets | joint (χ²-weighted) finder + phase-coherence gate between zg and zr at the candidate frequency |
| 4 | high pass subtracts the per-night MEDIAN → single-exposure nights become exactly 0 (85 % of D3 band-nights) | D2 recovery 6 % (low W_g) → 35 % (high W_g) | support-aware detrending: aligned zero points + a slow running weighted median; single-exposure nights kept |

**What the holdout validates.** Because the v2 architecture was selected
using summaries from the complete frozen D3 campaign (which includes the
stars that later form the holdout), the odd-ID split holds out v2 EXECUTION
and CONSTANT SELECTION, not architecture development: it is an internal
post-selection validation, not an independent or confirmatory validation.
A claim untouched by design-level information requires another dataset. No
alternative partition was evaluated against frozen outcomes; the parity rule
was fixed before the split was built.

v2 is a NEW arm: same shards in, same per-star JSON schema out
(`schema_version = "v2-1"`, every frozen key present, v2 diagnostics under
`passes[p]["v2"]` and a top-level `v2` block), so the unchanged
`metrics_generalization.score_star`, `overall_result` and every descriptive
module score it. Search bounds and grids are the frozen ones (low [2/T, 48],
high [24, 1440] c/d, 10 samples per peak): the comparison is about the RULE.
Code: `scripts/v2/` (outside every frozen and campaign SHA surface); frozen
helpers are imported read-only after `frozen_api` verifies the frozen SHAs.

## 2. Algorithm (exact)

One time origin per star (its first epoch across both bands); T = combined
baseline; tol = 1.5/T everywhere (veto, window-peak separation, clustering,
joint top-5 membership); the metrics' frequency-match tolerance is the
frozen 1.5/T unchanged.

1. **`align.py` — zero-point alignment on shared nights.** Per band: anchor
   = the oid with the most rows (ties: smallest oid label). For every other
   oid with n ≥ 5 rows and ≥ 5 nights in common with the anchor: on each
   shared night take the weighted median (weights 1/magerr²) of the oid's
   rows and of the anchor's rows; the offset is the weighted median over
   shared nights of their difference (night weight 1/(var_oid + var_anchor));
   the offset is subtracted from the oid's rows. Oids with too few rows or
   too few shared nights are left UNSHIFTED and flagged (their whole-row
   offset estimate is recorded, not applied). Same-night pairing keeps
   astrophysical variability on longer timescales out of the offset. Output:
   aligned `mag` + table (band, oid, n, n_shared_nights, offset_mmag,
   applied, role). A shard without an `oid` column is one oid per band.
2. **`detrend.py` — series preparation.** Low pass: aligned mag minus the
   band's 1/magerr²-weighted mean (frozen low pass after alignment). High
   pass: aligned mag minus a centred running weighted median over
   `trend_window_days`; a window holding fewer than 5 points is replaced by
   the 5 nearest-in-time points. Single-exposure nights are kept, valued
   relative to the local trend. The frozen "unavailable" rule (both bands
   have zero peak-to-peak after detrending) is kept. LEAKAGE: a running
   median this slow leaves 0.03–24 c/d variability in the high-pass series,
   which can alias into 24–1440 c/d through the spectral window (the frozen
   nightly median removed it); this is measured, not assumed away (§6
   audits).
3. **`window.py` — spectral window + extended veto.** For each time set
   (zg, zr, and the combined set used for the joint series) the window
   strength |mean exp(−2πift)|² is computed on the pass grid subsampled ×10
   (the frozen fast periodogram's trigonometric-sum approximation; tested
   against the frozen exact `window_strength`); the strongest 24 window
   peaks separated by tol are recorded (the veto uses the first
   `n_window_peaks`). Fixed loci: k·1.0 + m/365.25 (k = 1..3, m = −2..2;
   m = +1 is the sidereal frequency), k·1.00274 (k = 1, 2), k/29.530589 +
   m/365.25 (k = 1, 2; m = −1..1), m/365.25 (m = 1, 2), and the lunar–solar /
   lunar–sidereal beats k·{1.0, 1.00274} ± 1/29.530589 (k = 1, 2). A
   candidate is `window_alias` in a series if it lies within tol of any
   fixed or data-driven locus of that series, or if the frozen local test
   fires (max window strength within ± tol ≥ 0.1). `is_alias_of_stronger`
   (stronger = same-series peaks with higher power) uses spacings {1.0,
   1.00274} c/d and BOTH families: difference |f − f₀| ≈ k·spacing (frozen,
   sidereal only) and mirror f + f₀ ≈ k·spacing (the 1−δ / 2−δ wings; a
   real-valued series has a symmetric window). Cross-pass partners: the high
   pass (evaluated after the low pass) also tests each band's candidates
   against that band's UNALIASED significant low-pass candidate frequencies
   (FAP < 1e-3), so a mirror such as 48 − f₀ of a strong low-frequency
   signal is vetoed although f₀ is not on the high grid; every significant
   low-pass frequency that is a partner of a candidate is recorded
   (aliased or not) so the veto is re-derivable. VETO EXPOSURE: the fixed
   loci, the data-driven peaks, the local test, the mirror family and the
   cross-pass partners CAN veto real signals (each partner excludes ≈ 8·tol
   = 12/T ≈ 0.43 % of the high band at T ≈ 2,765 d before overlaps, more for
   shorter baselines); true ≈1, 2 c/d and ≈29.5 d variables are sacrificed;
   the exposure of the truth frequencies is a mandatory descriptive output
   (§6).
4. **`multiband.py` — joint finder + coherence.** Per band: frozen fast
   periodogram on the frozen grid. Joint series: astropy's
   `LombScargleMultiband(method="fast")` is by construction the χ²-weighted
   sum of the per-band fast periodograms (weights ∝ Σ power²), i.e. the frozen
   `multiband_power`; it is computed with that frozen helper (identity pinned
   by a test). Candidates = union of the top-15 peaks of zg, zr and joint
   (frozen `extract_peaks`, 20 → 15), clustered at tol in order of
   DECREASING POWER ONLY (the frozen unaliased-first order would make the
   candidate set depend on the veto constants), capped at 45 (= every peak
   row). At each candidate: exact per-band power / amplitude / Baluev FAP
   (frozen helpers), the joint fit (one weighted least-squares sinusoid per
   band at the shared frequency on the shared time origin → A_g, A_r, φ_g,
   φ_r with errors), and **coherence** = wrapped |φ_g − φ_r| ≤
   `phase_tolerance_cycles` AND `amp_ratio_min` ≤ A_r/A_g ≤ `amp_ratio_max`.
   Coherence is an operational gate, not a statistical test; the recorded
   phase errors do not enter the decision (failures are reported stratified
   by phase uncertainty and amplitude S/N, §6).
5. **`rule.py` — decision** (frozen wording kept). `confirmed` = at least one
   band with Baluev FAP < 1e-3 and not aliased in that band, AND the candidate
   lies within tol of one of the first five UNALIASED joint peaks (the joint
   top-15 after the veto — "joint top-5 after veto"), AND coherent;
   `candidate` = at least one unaliased band with FAP < 1e-3 but incoherent
   or not in the joint top-5 (reason recorded); else `not_detected`. Within a
   pass the best candidate is the first by (status order, best band FAP,
   frequency); best pass = frozen `overall_result`. Basis strings:
   `coherent+zg+zr`, `coherent+zg`, `coherent+zr` (confirmed); `zg`, `zr`,
   `zg+zr` (candidate).
6. **`analyze_star_v2.py`** — same signature as the frozen `analyze_star`;
   `top_peaks` keeps the frozen 15 rows (5 per series; series names zg, zr,
   multiband) with the frozen keys (v2 alias semantics; extra keys
   `window_locus`, `stronger_peak_alias`, `grid_power`). Every veto
   component is recorded per candidate: locus label, local window power,
   same-series alias flag, cross-pass alias flag and partner list, the 24
   window peaks per series, the joint top-15.

## 3. Constants

| constant | default | tunable? | candidate set |
|---|---|---|---|
| trend_window_days | 30 | yes (full dev rerun per value) | {30, 10} |
| n_window_peaks | 12 | yes (exact offline re-score) | {12, 6, 24} |
| phase_tolerance_cycles | 0.15 | yes (exact offline re-score) | {0.15, 0.10, 0.25} |
| amp_ratio (A_r/A_g) | [0.3, 1.5] | yes (exact offline re-score) | {[0.3,1.5], [0.5,1.2], [0.2,2.0]} |
| FAP threshold | 1e-3 | NO | frozen |
| tolerance | 1.5/T | NO | frozen |
| min rows per aligned oid / min shared nights | 5 / 5 | NO | |
| min points per trend window | 5 | NO | |
| peaks per series / joint top / candidate cap | 15 / 5 / 45 | NO | |
| window subsample / recorded window peaks | 10 / 24 | NO | |
| search bounds, grid, samples per peak, rule structure, fixed loci | frozen / fixed | NO | |

`scripts/v2/v2_common.py::TUNABLE` is the machine-readable copy; the runner
refuses any value outside the candidate sets. 2 × 3 × 3 × 3 = 54 combinations.

## 4. Split (`split.csv`, SHA-256 `a486056f1f8a2b5f87d579ee184720820caf661894e19092723003e5701d40f8`)

Built by `scripts/v2/make_split.py` from the frozen roster
(`roster_d3.csv` d04f6e4e…), the frozen D3 shard index
(`crossmatch_freeze/panels_shard_index.txt` ce792543…) and the archived D2
gen2 shard manifest (826016d7…, byte-identical to the laptop's production
manifest). Rules:

- D3: even KIC → dev, odd KIC → holdout; the four DEVELOPMENT SMOKE STARS
  (KIC 892667, 4752731, 9596355, 5475187 — inspected while the code was
  written, chosen from the frozen per-star table before the split existed,
  all odd-KIC) form the class `dev_smoke` and are EXCLUDED from both halves
  and from every registered run. Class balance dev / holdout / dev_smoke:
  flag0 1,164 / 1,149 / 1; flag1 308 / 299 / 3; flag2 36 / 40 / 0. Runner
  lists (∩ shard index): `d3_dev.txt` 1,458 (957c63a2…), `d3_holdout.txt`
  1,439 (eca7e01e…), `d3_dev_smoke.txt` 4.
- D2: arm A/B shards by TIC parity (even → dev): 60 dev vs 43 holdout
  targets (parity is imbalanced by chance; the rule is kept as
  pre-registered); Gaussian nulls by serial (0–499 dev, 500–999 holdout);
  every paired control referenced by ANY odd-TIC nominal arm-B shard is
  sequestered to the holdout (67 controls, 43 of them also referenced by
  even-TIC shards), the rest to dev. The D2 native windows are NOT
  window-disjoint across halves: 43 of the 106 nominal-B template windows and
  72 of the 928 null template windows occur in both halves. Consequently the
  dev D2 run before the constants freeze is the 500 dev NULLS ONLY (synthetic
  Gaussian noise on fixed windows: a fixed-window, independent-noise
  validation), and the even-TIC B / control outputs (`d2_dev_deferred.txt`,
  219 shards) are run only AFTER the holdout, as descriptive material. Runner
  lists: `d2_dev.txt` 500 nulls (71325ec0…), `d2_holdout.txt` 696 = 129
  nominal-B + 67 controls + 500 nulls (cd44f517…). Ladder / phase / ampscale /
  dropout / cadence_alt / redilution shards are split by parity but are NOT
  part of the v2 arm.
- No sid is in both halves (asserted by the builder and by a test).
- `overlap30.txt` (every 48th D3 dev id, 92713ce6…) is the cross-machine
  decision-agreement set.

The runner (`run_v2_ls.py --split-file --stars-file`) refuses id lists that
span both halves, refuses `dev_smoke` ids, and runs holdout ids only in the
registered mode of §8.

## 5. What may be tuned on dev, and how (exact, deterministic)

Only the four tunable constants, each within its declared set:

1. Run dev D3 (1,458) and dev D2 (500 nulls) at the defaults, and again at
   trend_window_days = 10 (full dev lists; the trend window changes the
   periodogram, so it is the only rerun dimension).
2. For each of the two runs, `scripts/v2/rescore_v2.py` re-applies the
   decision rule EXACTLY for the 27 (n_window_peaks, phase tolerance,
   amplitude ratio) combinations from the recorded diagnostics: the candidate
   set is power-ordered (independent of the veto constants); the window veto
   is re-derived from the fixed loci, the recorded local window power and the
   first N of the 24 recorded window peaks; same-series alias flags are
   recorded; the cross-pass alias is re-derived from the recorded partner
   list and the re-scored low pass; the joint top-5 after veto is re-derived
   from the recorded joint top-15; the coherence gates are re-applied to the
   recorded Δφ and A_r/A_g. No periodogram is recomputed.
3. `scripts/v2/dev_tuning.py` asserts all 54 combinations and the expected
   denominators, computes on the DEV ids P1_dev (flag1 roster, missing = 0),
   P2_dev (frozen P2 frame: Mo-joined, freq-scorable, eligible, frozen-usable;
   v2 unavailable = non-recovery), P3_dev (flag0 roster) and the dev-null
   confirmed count, and J = P2_dev − P3_dev.
4. Selection rule (fixed now): the combination maximizing J subject to
   (a) at most 2 of the 500 dev nulls `confirmed` and (b) P1_dev ≥ P1_dev of
   the default combination − 0.05. Ties: the first feasible maximizer in the
   candidate-set order of §3 (trend window, then N, then phase, then ratio).
   If no combination is feasible, the default is retained and
   `tuning_constraint_failure = true` is recorded. No other criterion, no
   manual override.
5. The result is written to `V2_CONSTANTS_FROZEN.json` (overrides, the v2
   code digest, split SHA, plan SHA, the pre-registration commit, the SHA of
   the evidence table `dev_tuning.csv`), an amendment entry is added to §10,
   the commit is made, and only then is the holdout scored — once (§8).

Not tunable, ever: bounds, grids, FAP threshold, tolerance, the rule's
structure, the veto's fixed loci, the alignment / detrend definitions.

## 6. Comparison endpoints (holdout only, frozen vs v2 on the same stars)

Frames are built from the split ROSTER of the half (`dev_smoke` excluded):
an id without a result is a failure in both arms; an id of the runner list
without a v2 row is an unexplained loss and aborts the comparison
(`scripts/v2/compare_engines.py`). The frozen arm's numbers come from its
full-run per-star table restricted to the same ids (no frozen re-run).
Statistics: per-arm Wilson 95 % (exact one-sided Clopper–Pearson upper for
the nulls); paired difference v2 − frozen with a seeded star (D3) or target
(D2) bootstrap, B = 2000, seed 20260902 — when there are no discordant pairs
the difference interval is the degenerate [0, 0] and is flagged; exact
two-sided McNemar on the discordant pairs (D3 binary endpoints).

| endpoint | frame (holdout) | statistic |
|---|---|---|
| P1 detection completeness | D3 flag1 roster (299) | Wilson; paired diff; McNemar |
| P2 dominant-frequency recovery | frozen P2 frame: Mo-joined, freq-scorable, eligible, FROZEN-usable; a v2 unavailable result = non-recovery | Wilson; paired diff; McNemar; chance-match rates of both bundles beside |
| P2 sensitivity | the P2 frame usable in both arms | same |
| P3 negative-class trigger rate | D3 flag0 roster (1,149); also per pass | Wilson; paired diff; McNemar |
| P4 D2 conditional recovery and trigger | nominal arm-B, 43 holdout targets; ELIGIBLE (scheduled-strata denominator, missing = 0) and USABLE variants | common-draw target bootstrap → paired difference CI |
| P5-style Gaussian false-alarm | 500 holdout nulls | CP upper each; McNemar — a DESCRIPTIVE SCREEN: even 0/500 has U95 = 0.60 %, so this half cannot pass the frozen P5 0.5 % criterion; it is not a confirmatory decision |
| paired-control contrast | injected-minus-paired-control trigger per target (67 holdout controls) | target bootstrap per arm and the arm difference |
| descriptive (no inference) | status transitions frozen → v2 and availability transitions; P3 by merged-oid count, by pass, by ruled frequency band; alignment offsets, shared-night counts, unshifted-oid counts and the endpoints without alignment-affected stars; coherence failures stratified by phase error and amplitude S/N; TRUTH-FREQUENCY VETO EXPOSURE by dataset / pass / band / component (fixed loci, data peaks, local test, mirror, cross-pass) and their union; the LEAKAGE AUDIT (a low-frequency-only sinusoid injected into dev D3 windows: high-pass trigger rate with and without the injection) | tables |

Pre-declared reading (a descriptive operational screen, not a hypothesis
test or a confirmatory decision): STRONG if P3 falls by ≥ 15 points AND P1
is not more than 5 points lower AND at most 2 of 500 holdout nulls are
confirmed; any other outcome is reported as it is. No endpoint swap, no
denominator swap, no second holdout. The four `dev_smoke` stars are never
part of a primary number; a sensitivity table including them is labelled
"contaminated sensitivity analysis".

## 7. Disclosure (verbatim, for the abstract and poster)

"After full-cohort frozen-arm failure analysis, we fixed a digest-locked
but not byte-replay-attested v2 detector, selected four prespecified
constants on development data, and evaluated it once on an internal odd-ID
holdout excluding four stars used during development; this is
post-selection internal validation, not confirmatory external validation."

## 8. Provenance, single holdout execution, metrics

`run_v2_ls.py`: binding = {engine, v2_digest (SHA over scripts/v2/*.py),
frozen_digest, constants_sha256, generation_id, attestation_sha256 =
"v2-unattested", machine, split_sha256, split_half, stars_file_sha256}; a
holdout run adds plan_sha256 and preregistration_commit. The campaign digest
is recorded at start for audit but is NOT bound (v2 numerics never depend on
scripts/generalization/*.py; the metrics bundle records the spec/campaign
SHAs separately). Sidecars, completion.csv, IN_PROGRESS refusal and the
resume scan follow the frozen driver.

Registered holdout mode (`--allow-holdout`): requires the registered
holdout list exactly (SHA equal to `split_manifest.json`), forbids
`--limit`, requires `--constants generalization/v2/V2_CONSTANTS_FROZEN.json`
whose v2-code digest, split SHA and plan SHA equal this checkout's, and
creates `generalization/v2/HOLDOUT_LAUNCH_<dataset>.json` before computation;
a relaunch is permitted only as an exact resume of the locked configuration
(same list, constants, code, split, plan, output directory).

`metrics_generalization.py --engine v2`: skips the replay-attestation
requirement (tier `v2_unattested`), binds sidecars to the run manifest's
binding keys (including machine, split, half and list SHAs), labels
`manifest.engine = "v2"`; the frozen path is untouched and guarded by
`compare_metrics_runs.py` on the D3 frozen bundle (PASS recorded in
codex/METRICS_ENGINE_REPORT.md). The comparison output is bound to both
metrics-manifest SHAs, the split SHA, the comparison-script SHA, the
constants artifact and the smoke exclusions (its manifest.json).

## 9. Machines and schedule

Laptop (12 workers, `.venv`, after its frozen D2 run finishes and the frozen
D2 bundle is pulled): dev runs (both trend windows), then the holdout halves —
v2 code is staged there as untracked files outside the campaign SHA surface
and its digest must equal the Mac's before every run. The Mac (M5,
`.venv-gen`) is used for development checks only unless its owner allows
sustained load; the overlap set is run on both machines and decision
agreement reported. Results: `generalization/results/<date>_d3_v2/`,
`<date>_d2_v2/`, `<date>_synthesis/` (frozen vs v2 side by side, evidence
map). Reviewer gate: one sol round on this document (REVISE, 2026-09-02;
dispositions in `generalization/reviews/V2G1/`), a confirmation round on
the revision, then the dev runs.

## 10. Amendments and disclosures

- 2026-09-02, before any registered run (revision after the sol review of
  the first draft, `generalization/reviews/V2G1/sol_plan_review.md`):
  (1) the four development smoke stars reclassified as `dev_smoke` and
  removed from both halves (they had informed: the mirror family and the
  lunar–solar beat loci — a 1−δ wing, sidereal − lunar = 0.9688 c/d, survived
  the difference-only test; cross-pass partners — a 52-mmag δ Sct at 1.742
  c/d produced a high-pass confirmation at 48 − 1.742 c/d; the joint top-5
  after veto — a frozen-missed 39-mmag star at 0.3335 c/d was crowded out by
  vetoed 1 c/d aliases; the unaliased-only cross-pass list); (2) the holdout
  qualified as internal post-selection validation; (3) exact offline
  re-scoring (power-ordered candidate set, cap 45, recorded veto components
  and partner lists) and the trend-window set reduced to {30, 10} with full
  dev reruns, the window subsets dropped; (4) registered single-execution
  holdout mode with a lock file and extended binding keys; (5) roster-based
  comparison frames, the frozen P2 frame, P4 eligible + usable, the
  paired-control contrast, the null screen labelled descriptive; (6) D2
  controls referenced by odd-TIC shards sequestered to the holdout, dev D2
  reduced to the nulls, window crossing disclosed; (7) shared-night
  alignment with min 5 shared nights; (8) leakage and veto-exposure audits
  declared, "untouched by construction" removed; (9) the coherence gate
  described as operational; (10) window-peak separation on the combined T.
  Development inspection after the split used `d3_dev.txt` ids only.
