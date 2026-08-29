# G2 disposition — sol ×5 round 2, 2026-08-28

Verdicts received: referee2 NOT FREEZABLE (8 resolved / 12 partial + 8 new),
stats2 NOT FREEZABLE (5 blockers + 3 major), methods2 NOT FREEZABLE
(1 blocker + 5 major/minor), abstract CONDITIONAL GO (18 contradictions +
defects table + claims inventory + skeleton), astro re-running (first
attempt died on a 300k-token compaction failure).

All same-day fixes below are in METRICS_SPEC v3 and the revised plan;
code fixes are committed. Round-3 re-review targets the three
not-freezable lenses.

## Same-day FIXED (doc)

- 928-vs-510 null/arm contradictions removed; nulls = deterministic cycling
  of the sorted 928 pool, seed = serial; "templates ARE the not-detected
  set" deleted (referee2 1/7, abstract 7/8).
- Risk-register "FPR upper bound" and "band" wording corrected
  (referee2 9, abstract 9/10/18).
- Nyquist-vs-integration-null physics text corrected; cadence precedence
  algorithmic (referee2 4, abstract defects).
- Per-mode independent phases stated; amplitude-stationarity sensitivity
  axis added (×{0.7, 1.3}, median window, +206 runs) (referee2 5).
- Bandpass nominal re-attributed: blackbody gives (1.43, 0.80) ≈ low rung;
  1.7 is the adopted grid midpoint (referee2 25, abstract).
- Template matching fully algorithmic in the plan text — matches the
  implemented code exactly (referee2 24).
- Ladder median-window conditioning stated; run totals recomputed
  (≤ 2,957 core ≈ 1.5 d; stretches listed separately) (referee2 26,
  abstract 14/17).
- Self-windows demoted to a separate diagnostic arm (abstract 13).
- Near-saturation boundary closed (g ≤ 14 flagged) (abstract).
- Exact sampling fractions (2314/7292, 7292/2314) binding (abstract 3).
- Crossmatch mapping + adjudication file committed as DATA before any
  campaign L-S run (referee2 2).
- Deadline weekday, replay/panel gate status, numpy verdict updated.

## Same-day FIXED (spec v3)

- Estimand formulas explicit; `best_candidate_matches_dominant` /
  `_any_mode` naming; D3 primary = dominant mode (stats2 1, abstract).
- S_p defined for D3 and D2; missing light curves count as non-detections
  in eligible-roster estimands; dual denominators named scopes
  (stats2 2).
- Taxonomy: evaluate all (mode, relation) hits, ambiguous iff >1 relation
  class, multiple directs stay direct, f_sid frozen (referee2 22, stats2 3).
- D2 cluster bootstrap fully specified: resample 103 TICs, carry all
  replicates + paired outcomes jointly, common random numbers across
  scenarios, conditional-on-frozen-windows statement, unique-window
  reporting, degenerate-cell CP fallback, pooled McNemar prohibited
  (stats2 4, referee2 8/23).
- Primary family as 5 complete tuples; FPR_Gaussian acceptance is the sole
  confirmatory decision (stats2 5).
- PPV: frame defined (dSct=2 excluded), survey bootstrap (negatives
  resampled, positives fixed), ppv.csv output (referee2 17/27, stats2 6,
  abstract 4).
- Gaussian-null: exact one-sided Clopper-Pearson at observed x; window
  allocation frozen (stats2 7, referee2 28).
- Surfaces: star-level coordinates frozen (dominant/largest retained mode),
  half-open bins + underflow/overflow, D3 top bin [50, inf), exposure
  edges, no smoothing (referee2 21, stats2 8, abstract).
- Attrition dimensions extended (join status, period, Teff, crowding,
  amp_unknown) (referee2 14).
- Common-subset sensitivity rule (referee2 26).
- D1 denominators + 928-catalog non-denominator statement (abstract 2).

## Same-day FIXED (code)

- Stable control ids over the sorted 928 pool + control_campaign_id in
  arm-B manifest rows (methods2 3).
- injected_modes.csv / rejected_modes.csv per shard; metrics truth reads
  ONLY injected modes; unique-target-mode rejection counting; targets
  count excludes controls (methods2 4/6).
- Attestation: full env fingerprint, gate identity, nonempty roster
  (methods2 1).
- Metrics: per-dataset primary match column; missing JSONs scored as
  non-detections in the eligible scope; usable scope added (stats2
  conformance note).
- Docstring contradictions in replay_gate / build_d3_roster (methods2 7).

## ADOPTED-W2 (unchanged from G1 response where noted)

- campaign_file_shas in every stage artifact incl. builders' reports
  (methods2 2).
- Hash extracted .tex + generated roster outputs (methods2 5).
- Full-928 replay baseline (running); result-sidecar provenance.
- MNAR sensitivity bounds for the Mo join remain a stated limitation
  (referee2 11 — uniform re-extraction remains DECLINED, out of frozen
  scope).
- Negative-sample balance diagnostics table (referee2 15).

## DECLINED (with reason)

- Crossed target/window bootstrap (stats2 4 alt): inference declared
  conditional on frozen windows instead; window-reuse table reported.
- Holm/joint simultaneous inference over the descriptive family (stats2 5
  alt): a single confirmatory decision is designated instead; everything
  else labeled descriptive.
