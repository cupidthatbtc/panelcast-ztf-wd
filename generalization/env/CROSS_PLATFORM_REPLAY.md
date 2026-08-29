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

## Mac (macOS arm64 M5, Accelerate BLAS, Python 3.12, numpy 2.3.5, scipy
## 1.16.3, astropy 8.0.1) — the full 25-star gate roster

- Strict verdict: FAIL (byte mismatch on every star). Per-star outputs in
  `generalization/env/xplat_mac/`.
- **Every decision identical on all 25** (status, basis, best frequency,
  alias flags, multiband_top5).
- **Every stored top-peak grid position identical on all 25** once compared
  at 1e-12 relative: the frequency value `minimum + step × index` differs
  in the last bit because ARM computes it with a fused multiply-add
  (grid index shifts are 0 everywhere).
- Decision-bearing float64 numerics (exact chi2 powers, Baluev FAPs,
  amplitudes): last-bit drift, as on Colab. Raw float32 fast-method
  periodogram readbacks (multiband top-peak `power`): up to 5.2e-5 relative
  (FFT/extirpolation path differs between Accelerate and OpenBLAS/pocketfft).
  A95 upper limits (95th-percentile quantile of float32 noise peaks):
  median 1.4e-8, one star at 2.0e-3 relative — a reported limit, not a
  decision.

## Three-platform summary

| platform | strict bytes | decisions | peak grids | f64 decision numerics | f32 readbacks | A95 |
|---|---|---|---|---|---|---|
| Windows x86 (production) | PASS 25/25 | = | = | = | = | = |
| Linux x86 (Colab, scipy-openblas) | FAIL 9/9 | = | = | ≤ 3.6e-13 | ≤ 3.6e-13 | ≤ 3.6e-13 |
| macOS arm64 (Accelerate) | FAIL 25/25 | = | = (FMA last bit) | ~1e-13 | ≤ 5.2e-5 | ≤ 2.0e-3 |

## Implication and proposed amendment (G2-AMENDMENT-1, not yet reviewed)

The frozen plan binds campaign L-S runs to machines that pass the STRICT
gate. That is the right standard for the referee claim "the published
bundle is byte-reproducible". For running NEW campaign data on a second
machine, byte identity with the published bundle is not the relevant
property — decision equivalence and bounded numeric drift are. Proposed
additional acceptance tier, applicable ONLY to non-production-machine
campaign runs and reported as such in every manifest:

`decision_identical`: for EVERY replayed star (full 25-star roster),
(a) all decision fields identical (status, basis, alias flags,
multiband_top5; best frequency within 1e-12 relative), (b) all stored
top-peak grid positions and alias flags identical (frequencies within
1e-12 relative — absorbs FMA last-bit differences), (c) decision-bearing
float64 numerics (exact powers, Baluev FAPs, amplitudes, multiband weights)
within 1e-9 relative, (d) raw float32 periodogram readbacks (top-peak
`power`) within 1e-3 relative and A95 limits within 1e-2 relative — both
reported quantities, neither a decision, (e) the tier recorded in the
attestation and propagated into run manifests and the results bundle
README with the measured maxima. Strict tiers remain required for the
production machine and for any claim of byte reproducibility of the
published bundle. Campaign estimands (METRICS_SPEC) depend only on
decisions and best-candidate frequencies, never on raw f32 readbacks; A95
enters only descriptive tables.

This is a process amendment to the frozen plan's replay section, not an
estimand change; it requires its own sol review round and, if approved, an
entry in reviews/G2_FREEZE.md as amendment 1.
