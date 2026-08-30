## Verdict: APPROVE-WITH-CHANGES

The frozen estimands are not independent of cross-platform numerics. They consume categorical decisions and selected frequencies; FAPs, multiband weights, and periodogram peaks can affect those quantities upstream. The observed 25-star Mac replay is decision-identical, but that does not eliminate boundary cases on new campaign stars.

### Estimand input trace

| Frozen quantity | Direct inputs | Platform-sensitive path |
|---|---|---|
| Detection completeness, including P1 and P4 | Positive label, eligible/usable denominator, rule firing; D2 additionally uses target/stratum clustering | Rules 1, 2, and 4 consume `status`. Rule 3 is census-only and independent of L-S replay. |
| Frequency-recovery completeness, including P2 | Rule firing, selected low/high/best frequency, truth frequencies, baseline-derived tolerance, \(S_p\) | Depends directly on status and selected frequency. A last-bit frequency difference can theoretically cross the match boundary in [METRICS_SPEC.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:92). |
| Correct-frequency fraction among detected | Confirmed subset plus the same selected-frequency match | Both numerator and denominator can change with status; numerator can also change at a frequency-match boundary. |
| D3 frame-specific PPV | Confirmed statuses, class labels, sampling weights, bootstrap | Depends on status, but not frequency, A95, or stored powers. |
| D3 negative-class trigger rate | Status and/or census flag, depending on rule | Rules 1, 2, and 4 depend on L-S status; census-only rule 3 does not. |
| D2 Gaussian-null FPR/P5 | Number of completed nulls and count with `status == confirmed`, followed by CP calculation | A single confirmation flip changes \(x\), potentially changing the sole confirmatory conclusion. |
| D2 native trigger rate | Confirmed status among controls | Status-dependent only. |

The complementarity tables, detection surfaces, and detection sensitivity analyses likewise depend on status. Frequency-recovery surfaces additionally depend on selected-frequency matching. Their amplitude and period coordinates come from external truth data, not the drifting fitted amplitudes.

Quantity-by-quantity:

- **Decisions:** direct inputs to nearly every L-S estimand. They were identical in the observed replay, but that identity is a required condition, not evidence that future stars cannot lie on a numerical boundary.
- **Best frequencies:** direct inputs to frequency recovery, correct-frequency fraction, chance-match calibration, and descriptive false-positive frequency tables. The current scorer constructs these matches at [metrics_generalization.py:127](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:127).
- **`top_peaks`:** directly enters only `any_top_peak_matches_any_mode`, which is explicitly diagnostic. Upstream, however, peak membership and ranking generate candidates and determine `multiband_top5`.
- **A95:** enters no frozen estimand and is not used in confirmation. It may drift within its descriptive tables without changing estimates.
- **Multiband weights:** not read by the metrics program, but they form the multiband periodogram and can therefore affect top-five membership, `multiband_top5`, status, and selected frequency.
- **FAPs:** do not enter the final proportion formulas as continuous values, but they determine significance and candidate status at [run_lomb_scargle.py:236](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_lomb_scargle.py:236). They also rank candidates and select the overall best pass. In particular, `overall_result` breaks same-status pass ties with `best_band_fap` at [run_catalog_lomb_scargle.py:254](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_catalog_lomb_scargle.py:254).

### FAP boundary

Yes. At \(T=10^{-3}\), a relative drift of \(10^{-13}\) is about \(10^{-16}\) absolute. Values on opposite sides of \(T\) but separated by less than that can produce different results under the frozen strict comparison `fap < 1e-3`. Depending on the other band and `multiband_top5`, this can change confirmed to candidate or not-detected.

For P5 this is material: at \(n=1000\),

- \(U_{95}(1,1000)\approx0.00474\), which passes;
- \(U_{95}(2,1000)\approx0.00628\), which fails.

Thus one null-star flip can reverse P5 when \(x\) changes between 1 and 2.

### Required changes

1. Add a prespecified boundary audit. Because the proposed tier permits \(10^{-9}\) relative float64 drift, not merely the observed \(10^{-13}\), flag every decision-bearing FAP satisfying  
   \[
   |FAP-10^{-3}| \le 10^{-12}.
   \]
   Also flag FAP near-ties used to select candidates or the best pass.

2. Recompute every flagged campaign star in the strict production environment. Its full-precision result under the unchanged `< 1e-3` rule is authoritative. Exact equality is not significant; displayed rounding must never decide the case.

3. Report each boundary star’s ID, pass, band, both full-precision FAPs, relative difference, statuses/bases, authoritative environment, and effect on every affected estimate. If strict adjudication is unavailable, report both assignments; P5 may be declared accepted only if both assignments pass.

4. Extend `decision_identical` to require identity of the **derived overall** `best_pass`, status, basis, and selected grid index—not only per-pass fields. Otherwise a FAP-order reversal could change the best frequency while every per-pass category remains identical.

5. Add an analogous audit for selected frequencies lying within the allowed frequency drift of a truth-match boundary. Require identical downstream match classifications or strict-environment adjudication.

With these safeguards, this remains a process amendment rather than an estimand change. Without them, the tier does not protect the frozen estimands at discontinuous decision and matching boundaries.
