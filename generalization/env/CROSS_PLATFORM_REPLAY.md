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
- CORRECTION (2026-08-29 01:30; an earlier revision of this file wrongly
  carried Colab's ~1e-13 over to the Mac): decision-bearing float64
  numerics on ARM drift up to **~7e-6 relative** — Baluev FAPs of stored
  peaks up to 1.3e-6, window powers up to 6.4e-7, exact candidate powers
  and amplitudes up to ~7e-6 (Accelerate's float64 linear algebra and the
  float32 fast-method periodogram feeding the peak search differ from
  OpenBLAS/pocketfft). Raw float32 readbacks (multiband top-peak `power`):
  up to 5.2e-5. A95 upper limits: median 1.4e-8, one star 2.0e-3 — a
  reported limit, not a decision.
- Boundary analysis (all 25 stars, both passes, both bands): the decision
  FAP closest to the 1e-3 confirmation threshold is 1.069e-3 (6.9% above;
  star 2033382692116807296, low, zr) with platform drift 1.6e-11 — a
  safety factor of ~4e9. Every FAP with drift > 1e-7 sits more than 1.4
  decades from the threshold. No decision is within reach of the observed
  drift.

## Three-platform summary

| platform | strict bytes | decisions | peak grids | f64 decision numerics | f32 readbacks | A95 |
|---|---|---|---|---|---|---|
| Windows x86 (production) | PASS 25/25 | = | = | = | = | = |
| Linux x86 (Colab, scipy-openblas) | FAIL 9/9 | = | = | ≤ 3.6e-13 | ≤ 3.6e-13 | ≤ 3.6e-13 |
| macOS arm64 (Accelerate) | FAIL 25/25 | = | = (FMA last bit) | ≤ 7e-6 | ≤ 5.2e-5 | ≤ 2.0e-3 |

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
within 1e-4 relative, (d) raw float32 periodogram readbacks (top-peak
`power`) within 1e-3 relative and A95 limits within 1e-2 relative — both
reported quantities, neither a decision, (e) BOUNDARY RULE: for every
replayed star, every decision FAP's relative distance from the 1e-3
threshold exceeds 100 × that star's measured maximum FAP drift; and in
CAMPAIGN outputs produced under this tier, every star whose best-candidate
FAP lies within 1e-3 relative of the threshold is flagged
`platform_boundary_sensitive` in per_star.csv (reported, never silently
resolved), (f) the tier recorded in the attestation and propagated into
run manifests and the results bundle README with the measured maxima. Strict tiers remain required for the
production machine and for any claim of byte reproducibility of the
published bundle. Campaign estimands (METRICS_SPEC) depend only on
decisions and best-candidate frequencies, never on raw f32 readbacks; A95
enters only descriptive tables.

This is a process amendment to the frozen plan's replay section, not an
estimand change; it requires its own sol review round and, if approved, an
entry in reviews/G2_FREEZE.md as amendment 1.
