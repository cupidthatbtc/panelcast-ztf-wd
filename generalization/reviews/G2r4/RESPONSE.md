# G2 round-4 disposition — 2026-08-28 (late)

Verdicts: referee4 NOT-FREEZABLE (2 residual doc blockers), stats4
NOT-FREEZABLE (5 code-conformance residuals), methods4 NOT-FREEZABLE
(4 fail-closed residuals), astro NO BLOCKERS (1 minor + 5 major
astrophysical framing/design items).

Everything below shipped same-session (commit "G2 round-4 response" + this
follow-up). Note for round-5: the missing G2r3/RESPONSE.md the panel
flagged was real — its write had been aborted by a failed command chain;
recreated and committed.

## referee4
1. Amplitude-stationarity stretch-vs-core — FIXED: CORE and binding in the
   plan run matrix (total ≤ 3,266 ≈ 1.6 d), matching the spec.
2. P4 zero-usable-strata — FIXED in spec (K_t = ∅ excluded from usable,
   y = 0 over |K_t| = 3 in eligible; denominator stays 103) and in code
   (both denominators emitted with n_targets_zero_usable_strata).

## stats4
1. P5 completed-trials — FIXED: acceptance requires n_completed == 1000;
   missing nulls break acceptance and are reported (n_scheduled vs
   n_completed).
2. Dominant headline + binding columns — FIXED: every dataset's headline
   uses the dominant-match column; correct_frequency_fraction_detected
   emitted per pass.
3. P4 denominators + paired contrasts — FIXED: eligible + usable variants
   in d2_cluster_completeness.csv; target-clustered paired
   census-minus-LS discordance bootstrap row.
4. PPV frame — FIXED: all sampled negatives retained (missing = cannot
   trigger, stays in the SRS).
5. Surfaces — FIXED: dominant match + S_best filter; detection
   period×amplitude with unknown bins; exposure axis now real
   median-exposures-per-night (zg_median_exp_per_night column added to
   build_panels_generic census; template_exp_per_night in the D2 manifest).

## methods4
1. Panel gate — FIXED: finite-value checks on science columns; roster hash
   in inputs; drift snapshot; report bound. build_panels_generic REQUIRES a
   passing panel attestation with matching env.
2. Attestation — FIXED: 928 UNIQUE ids required.
3. Stale shards — FIXED: builders emit shard_index.txt; the runner REQUIRES
   --shard-index in production and enforces exact bidirectional set match.
4. Drift snapshots — FIXED: replay gate, panel gate, shard builder, panels
   builder, metrics, runner all capture start SHAs and fail on drift.

## astro
1 (minor, algebra OK) — effective-integration-time + midpoint wording in
plan. 2 — ladder relabeled a phenomenological sensitivity grid; DA-
atmosphere endpoint validation recorded as a limitation (DECLINED in-scope).
3 — dominant-mode-dropout variant added as CORE (code: drop_dominant in
build_truth_model; matrix ≤ +103); ±30% labeled a local sensitivity.
4 — dSct=0 renamed the non-dSct comparison class (spec); attributed
detection = the existing frequency-recovery primary (P2). 5 — sub-hour
aperture-level caveat binding in plan + W4 adjudication + W3 check of Mo
amplitude sinc-correction status. 6 — near-saturation subset promoted to
the principal robustness lens; per-epoch saturation via frozen catflags QC
noted.
