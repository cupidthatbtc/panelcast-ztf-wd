# D2 stratified pilot — generation gen1, 2026-08-30 (PILOT: never confirmatory)

Purpose: the plan's timing pilot + first end-to-end exercise of the whole D2
chain (generation → attested laptop run → sidecar/completion binding →
fail-closed metrics) on real inputs. Every P4/P5 row carries
`confirmatory=false`; nothing here enters an estimate.

## Run

- Generation gen1: `ca793ad7ec0a…` (production=true; 3,102 shards; 103 targets;
  76 dropout, 33 cadence_alt, 20 redilution, 119 controls, 1,000 nulls; every
  template matched at |Δg| ≤ 0.25). `run/generation_manifest_gen1.json`.
- Pilot index: 144 shards spanning every arm/scenario (30 nominal B, 30 nominal
  A, 3 per sensitivity scenario, 2 redilution, 10 controls, 30 nulls).
- Runner: laptop `Jacks_7i_5090`, strict attestation (full-928 replay PASS),
  144/144 complete, 0 failed, 2.12 h wall, **67.9 shards/h** (22 workers, same
  rate as 69.2/h at 12 workers ⇒ the laptop saturates at ~12 workers).
  Wall model: full D2 (3,102) ≈ 46 h; D3 (~3,000) ≈ 44 h, at 12 workers.
- Metrics (laptop, 12 s): all provenance checks passed (generation SHAs, index
  SHA, 144 sidecars, completion table); outputs in `metrics/`.

## First numbers (10 targets; small-sample, descriptive only)

| quantity | value |
|---|---|
| nominal arm B, detection (confirmed), eligible = usable | 16/30 = 0.53 [0.43, 0.63] (target-cluster bootstrap) |
| nominal arm B, confirmed AND dominant mode recovered (direct) | 7/30 = 0.23 |
| nominal arm A (Gaussian floor), detection / direct recovery | 15/30 / 10/30 |
| Gaussian nulls | 0/30 confirmed (CP U95 = 0.095 at n = 30) |
| paired uninjected controls | 8/10 confirmed = exactly their PUBLISHED statuses (10/10 agreement) |
| recovery vs published dominant amplitude | direct recoveries only for A ≥ 6.1 ppt; 0.86 and 3.33 ppt targets: 0/6 |
| scenario contrasts (3 targets each) | all within [−1, +1] noise; no scenario separable at n = 3 |

## Observations for G4 (decisions belong to the reviewers)

1. **Exposures-per-night strata are degenerate.** The 928-window pool has
   median exposures-per-night quantiles (10/50/90) = (1.0, 1.0, 2.0); K=0 and
   K=1 windows have identical exposures-per-night for 103/103 targets; K=2 is
   1–2. The three windows are valid magnitude-matched replicates, but the
   plan's "10/50/90th percentile of exposures-per-night" stratification does
   not stratify; the completeness surface's exposure axis (bins 1/1.5/2/3/5)
   is populated almost entirely at 1–2.
2. **Native variability dominates detection-only P4.** 342/928 pool windows
   are published `confirmed` (+76 candidate); 53/119 gen1 nominal-B windows
   are confirmed. In the pilot, on confirmed windows nominal B is "confirmed"
   11/13 times but recovers the injected dominant mode 2/13; on not_detected
   windows 4/15 confirmed, all 4 direct recoveries. The uninjected controls
   reproduce the published status 10/10. Detection-only P4 therefore mostly
   measures the pool's native variability at these magnitudes; the
   frequency-recovery endpoint behaves as designed.
3. Arm-A confirmations that are not the dominant mode (5/15): one is another
   injected mode (`best_candidate_matches_any_mode = direct`), one sits
   ~1.6× the match tolerance from the sidereal alias of the dominant mode,
   three are unmatched peaks with the injected frequency present in the top-15
   (`any_top_peak_matches_any_mode = true`).

## Provenance

`metrics/manifest.json` (attestation tier strict, generation id, pilot=true,
confirmatory_allowed=false), `metrics/inputs_sha256.json` (full chain),
`run/manifest.json`, `run/completion.csv`, `run/shard_manifest_gen1.csv`.
Code: commit 5134fbd (tests 41/41 on both machines).
