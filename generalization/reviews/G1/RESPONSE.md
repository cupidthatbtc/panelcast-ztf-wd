# G1 disposition — sol ×3 (referee / methods / stats), 2026-08-28

47 findings. Legend: **FIXED** (same-day code/doc change), **ADOPTED-W2**
(scheduled, named owner task), **REFRAMED** (claim language changed as
demanded), **DECLINED** (with reason).

## Referee lens (sol_referee.md)

1. D2 template circularity (REJECT) — **FIXED**: pool = all 928 windows;
   paired uninjected controls (95-prefix); **ADOPTED-W2**: Romero
   self-window fetch, preferred templates where crossmatch succeeds.
2. "Independently labeled" wording — **REFRAMED**: "labels obtained
   independently of the frozen ZTF pipeline"; crossmatches frozen pre-outcome.
3. D2 not an independently labeled sample (REJECT) — **REFRAMED**: D2 is
   exclusively "conditional injection-recovery efficiency of the search
   stage"; slip rule rewritten (D3 is the external-label dataset).
4. Sinc algebra wrong (REJECT) — **FIXED** before the review landed:
   d2_truth_model implements signed sin(x)/x with x = πT/P, first null at
   P = T, |sinc|=0.3 at P≈160 s (120 s); unit-tested at null/2T/boundary.
   Plan text corrected (197 s was the 0.5 point).
5. Phases unspecified (REJECT) — **FIXED**: independent per-mode phases,
   PCG64(TIC), shared across bands and variants (already implemented; plan
   now states it); **ADOPTED-W2**: +2 phase draws sensitivity axis;
   amplitude-stationarity caveat added to the wording template.
6. Real timestamps ≠ real-sky completeness (REJECT) — **REFRAMED**:
   "conditional injection-recovery efficiency of the search stage";
   reviewer's suggested wording adopted for the abstract.
7. Arm-A nulls are Gaussian-null FAP (MAJOR) — **REFRAMED**: estimand
   renamed FPR_Gaussian; real-noise context from paired controls reported
   as "native trigger rate of the template pool".
8. Wilson invalid for repeated injections (MAJOR) — **FIXED in spec**:
   target-cluster bootstrap (B=2000); per-stratum reporting; no pooling.
9. dSct=0 ≠ FPR (REJECT) — **REFRAMED**: "negative-class trigger rate",
   weighted, with W4 adjudication; upper-bound language dropped.
10. Any-mode matching multiplicity (MAJOR) — **FIXED in spec**: dominant
    mode is primary; disjoint match taxonomy; 100-permutation chance-match
    calibration.
11. Amplitude-join bias (REJECT) — **REFRAMED + partial**: all frequency/
    amplitude analyses labeled "Mo-join-conditioned"; joined vs unjoined
    covariate comparison required; uniform amplitude re-extraction for the
    154 unjoined **DECLINED** (would require original Kepler photometry
    analysis — out of frozen-campaign scope; stated as a limitation).
12. Denominator inconsistency (MAJOR) — **FIXED in spec**: separate
    estimands, decomposition only on matching denominators (S_p = 1).
13. Kepler amplitude ≠ A_g (MAJOR) — **FIXED in spec**: axis renamed
    "historical Kepler-band dominant amplitude"; non-contemporaneity stated.
14. g≥13.2 truncation (MAJOR) — **FIXED**: magnitude source named
    (Murphy/KIC g); cut applied pre-outcome (roster frozen before any ZTF
    result exists); attrition table required in spec; claims restricted to
    g≥13.2.
15. Stride sampling (MAJOR) — **FIXED**: frozen-seed SRS, inclusion
    probability + sampling_weight column; roster rebuilt before any fetch
    of negatives completed.
16. Unavailable cases unresolved (REJECT) — **FIXED in spec**: dual
    denominators (eligible vs usable) + full attrition table.
17. "Purity" misnomer (MAJOR) — **FIXED in spec**: renamed; weighted PPV
    for D3 only, with caveats.
18. Turn-on prespecification (MAJOR) — **FIXED in spec**: bin edges and
    min-cell rules frozen; sensitivity envelope ≠ statistical uncertainty.
19. McNemar ≠ complementarity (MAJOR) — **FIXED in spec**: overlap table +
    incremental yields primary; McNemar secondary.
20. No pooling into one selection function (REJECT) — **REFRAMED**: title
    and claim section rewritten; three separate assessments.

## Methods lens (sol_methods.md)

1. Driver doesn't require replay attestation (BLOCKER) — **FIXED**:
   --replay-report mandatory; validates passed + env fingerprint + frozen
   SHAs.
2. Vacuous gate pass (BLOCKER) — **FIXED**: nonempty roster + strict_v2
   unconditional.
3. v1→v2 history wording (BLOCKER) — **FIXED**: plan corrected (branches
   added for sparse inputs; v2 records exercise them); both commits named.
   Full-921 differential replay → **ADOPTED-W2** (full-928 baseline).
4. 25 stars insufficient (MAJOR) — **ADOPTED-W2**: one full 928-star replay
   on the production machine as the per-env baseline.
5. Env pins contradictory (BLOCKER) — **FIXED**: replay verdict makes
   numpy 2.3.5 the authority; requirements-frozen + FROZEN_ENV updated;
   env_versions() now records BLAS + thread env. Wheel-hash/container
   pinning **DECLINED** (timeline; replay gate is the acceptance test).
6. IERS/BJD outside gate (BLOCKER) — **FIXED**: iers auto-download disabled
   in build_panels_generic; **ADOPTED-W2**: panel-stage golden replay
   byte-comparing a rebuilt shard incl. bjd_tdb.
7. Inputs not content-bound (BLOCKER) — **ADOPTED-W2**: content-addressed
   input manifest (roster/cache/shard SHAs) emitted by builders and checked
   by the driver. Roster/raw SHAs already recorded by both roster builders.
8. Resume provenance (BLOCKER) — **ADOPTED-W2**: per-result sidecar (shard
   SHA + env fingerprint); reuse only on full match.
9. Campaign code not recorded (MAJOR) — **FIXED**: campaign_file_shas() in
   every manifest.
10. Module resolution bypass (MAJOR) — **FIXED**: preload rejection,
    sys.path index 0, post-import __file__ verification.
11. CLI-identity claim too broad (MAJOR) — **FIXED**: claim narrowed in
    docstring; driver enforces exactly ("low","high") in production.
12. Preflight math (MAJOR) — **FIXED**: min(physical, requested, ceiling),
    reject nonpositive, fail on zero ceiling, 0.52 GB/worker headroom.
13. Stale dirs / overlapping jobs (MAJOR) — **PARTIAL**: runbooks use
    manifest-derived --stars-file; fresh out-dirs per stage documented.
    Per-source locks **DECLINED** (single-driver-per-dataset operation).
14. Test gaps (MINOR) — **ADOPTED-W2**.
15. Final assert_frozen (MINOR) — **FIXED**.

## Stats lens (sol_stats.md)

1. Purity (BLOCKER) — **FIXED in spec** (see referee 17).
2. Denominators (BLOCKER) — **FIXED in spec** (S_p eligibility).
3. Match taxonomy (MAJOR) — **FIXED in spec** (disjoint labels, precedence,
   permutation calibration).
4. D2 unit of analysis (BLOCKER) — **FIXED in spec** (target = cluster;
   strata separate; equal-weight standardized aggregate).
5. Pooled Wilson (BLOCKER) — **FIXED in spec** (cluster bootstrap).
6. McNemar table unspecified (BLOCKER) — **FIXED in spec** (preregistered
   2×2, detection-only, symmetric margins).
7. McNemar ≠ complementarity (MAJOR) — **FIXED in spec**.
8. Multiplicity (MAJOR) — **FIXED in spec** (primary family designated;
   everything else descriptive/pointwise).
9. Band coherence (MAJOR) — **FIXED in spec** ("prespecified finite-grid
   sensitivity range"; endpoints identified; de-dilution separate axis).
10. Ladder-dependent binning (MAJOR) — **FIXED in spec** (invariant axes:
    TESS ppt / historical Kepler mmag).
11. Null design ≠ operational FPR (BLOCKER) — **REFRAMED** (FPR_Gaussian) +
    **FIXED** (928-window frame defined; paired-control native trigger rate
    as the real-noise context quantity).
12. n=1000 not tied to acceptance (MAJOR) — **FIXED in spec** (one-sided
    95% upper ≤ 0.5% at zero events preregistered; alias audit descriptive
    below 10 events).
