# Cross-platform replay evidence (2026-08-29)

The L-S replay gate's strict tiers (raw / newline / documented v1→v2
schema transform) require BYTE-identical per-star JSON. That holds on the
production machine (jacks-7i-5090: 25/25 PASS 2026-08-28; full-928 baseline
in progress) and does NOT hold across platforms — as the attestation design
assumed and as BLAS reduction-order differences predict.

## Colab (Linux x86-64, Python 3.13.15, numpy 2.3.5 + scipy-openblas 0.3.30,
## scipy 1.16.3, astropy 8.0.1) — 9 stars (all 7 schema-v2 + 2 v1)

- Strict verdict: FAIL (9/9 MISMATCH). Report + per-star outputs in
  `generalization/env/xplat_colab/`.
- Quantified drift: 1,634 numeric fields compared; **max relative
  difference 3.56e-13** (`4235280071072332672.low.top_peaks[6]
  .baluev_fap_blind_grid`); typical differences 1–2 ulp in accumulated
  quantities (multiband weights = sums of squares of float32 periodograms,
  Baluev FAPs, amplitude errors).
- **Every decision identical**: status, basis, best frequency/period
  (to < 1e-12 relative), alias flags, multiband_top5, and all 15 stored
  top-peak grid frequencies + alias flags per pass, for all 9 stars.

## Mac (macOS arm64, Accelerate BLAS) — 25 stars — PENDING (running)

## Implication and proposed amendment (G2-AMENDMENT-1, not yet reviewed)

The frozen plan binds campaign L-S runs to machines that pass the STRICT
gate. That is the right standard for the referee claim "the published
bundle is byte-reproducible". For running NEW campaign data on a second
machine, byte identity with the published bundle is not the relevant
property — decision equivalence and bounded numeric drift are. Proposed
additional acceptance tier, applicable ONLY to non-production-machine
campaign runs and reported as such in every manifest:

`decision_identical_ulp`: for every replayed star, (a) all decision fields
identical, (b) all stored top-peak grid frequencies and alias flags
identical, (c) max relative numeric difference ≤ 1e-11, (d) verdict tier
recorded in the attestation and propagated into run manifests + the
results bundle README. Strict tiers remain required for the production
machine and for any claim of byte reproducibility.

This is a process amendment to the frozen plan's replay section, not an
estimand change; it requires its own sol review round and, if approved, an
entry in reviews/G2_FREEZE.md as amendment 1.
