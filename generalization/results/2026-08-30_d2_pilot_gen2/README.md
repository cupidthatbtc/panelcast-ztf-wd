# D2 stratified pilot — generation gen2 (Amendment 4, W_g strata), 2026-08-30 (PILOT: never confirmatory)

Purpose: the operational gate before the FULL D2 run under Amendment 4 — an
end-to-end exercise of the RE-generated D2 chain (gen2 = W_g window strata,
recovery-primary P4, paired-control scoring, target-level surfaces/chance
match) on real inputs, archived with raw results. Every row carries
`prespecified_primary=false`, `confirmatory_decision=false`; nothing here
enters an estimate. This README is documentation only and is deliberately
NOT listed in `SHA256SUMS` (the archive-wide sums were frozen when the record
was committed; the README was added 2026-09-01 after the writing-outline
track flagged its absence).

## Generation gen2

- `run/generation_manifest_gen2.json`: id `129740d1…4ef7cb`, production=true,
  **3,089 shards**, 103 targets; expected_counts asserted per arm
  (B/A nominal 309 each, ladder 8×103, phase 2×103, ampscale 2×103, dropout,
  cadence_alt 33, redilution, controls = unique arm-B windows, 1,000 nulls).
- Window strata K = 0/1/2 on W_g = Σ_nights max(n_zg,night − 1, 0) (pool
  10/50/90 = 6/58/452; strictly distinct for 103/103 targets; the builder
  refuses violations; surface edges (15, 41, 84, 217)). This replaces the
  degenerate exposures-per-night strata of gen1 (see the gen1 README).
- The gen1 record (`../2026-08-30_d2_pilot/`) remains the pilot-informed
  motivation for Amendment 4; gen2 is the post-amendment operational gate.

## Run

- Pilot index `run/pilot_shard_index.txt`: 144 shards spanning every
  arm/scenario (nominal B/A 30 each, 3 per sensitivity scenario, controls,
  nulls). Runner: laptop `Jacks_7i_5090`, strict attestation (full-928 replay
  PASS), 12 workers. The pilot was PAUSED mid-run (GPU needed) and RESUMED
  sidecar-bound: the archived `run/manifest.json` is the resuming invocation
  (`pending_at_start` 46 of 144, 0 failures, 39 min wall for the remainder;
  started 2026-08-30T20:48:41Z, finished 21:27:43Z, commit b854e97). The
  runner's `git_tracked_dirty`/`git_untracked_count` fields are `null` in this
  manifest (git-state capture raised inside the detached job); the pre-launch
  gate inspected the checkout by hand instead.
- `run/stars/`: 144 result JSONs + 144 `.prov.json` sidecars (288 files);
  `run/completion.csv` with `provenance_sha256`.
- Metrics (laptop, after the post-pilot pull to 2626612): every fail-closed
  guard passed — 144/144 sidecars, generation/index/shard SHAs, completion
  table, W_g strata guard, control resolution, env/attestation.
  `metrics/attrition.csv`: roster 144, scored 144, missing 0,
  provenance_verified 144, platform_boundary_sensitive 0.
- Tests: 51/51 on BOTH machines (`tests/pytest_laptop_Jacks_7i_5090.log`,
  `tests/pytest_mac_M5.log`).

## First numbers (10 nominal targets × 3 strata; small-sample, descriptive only)

| quantity (nominal, target-equal cluster bootstrap) | value |
|---|---|
| arm B recovery (confirmed AND dominant mode direct) — the A4 PRIMARY form | 0.17 [0.07, 0.27] |
| arm B trigger (confirmed only) — secondary | 0.57 [0.40, 0.73] |
| arm A (Gaussian floor) recovery / trigger | 0.27 [0.13, 0.40] / 0.33 [0.17, 0.53] |
| Gaussian nulls | 0/30 confirmed (CP U95 = 0.095 at n = 30; P5 needs all 1,000) |
| paired uninjected controls, detection D (10 pairs, 6 targets) | both 6, B-only 2, C-only 0, neither 2; P(D_B=1, D_C=0) = 0.25 [0.0, 0.6] |
| paired controls, recovery R vs partner truth | both 0, B-only 3, C-only 0; P(R_B=1, R_C=0) = 0.33 [0.05, 0.67] |
| native (control) trigger rate | 6/10 = 0.60 [0.31, 0.83] |
| paired census − L-S discordance (arm B) | −0.13 [−0.33, 0.07] |
| chance match (10,000 target derangements) | accidental recovery 0.000 (p95 0.000) |
| scenario contrasts (3 targets each) | intervals span [−1, +1]; nothing separable at n = 3 |

Reading: the recovery/trigger gap (0.17 vs 0.57) is the gen1 observation
again — native variability of the real windows drives detection-only
triggering, while frequency recovery isolates the injected signal, which is
why Amendment 4 made recovery the primary. Controls reproduce their
published statuses; no control "recovers" the partner's injected truth.

## Provenance

`metrics/manifest.json` (dataset d2, pilot=true, confirmatory_allowed=false,
generation id above), `metrics/inputs_sha256.json` (full chain incl. sidecar
SHAs), `run/manifest.json`, `run/completion.csv`,
`run/shard_manifest_gen2.csv`, `run/generation_manifest_gen2.json`;
archive-wide `SHA256SUMS` (README excluded, see above).
