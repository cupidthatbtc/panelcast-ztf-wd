## Verdict: REJECT

A separate non-production replay tier can coexist with the strict byte-reproducibility claim in principle. The current amendment does not establish that separation safely enough for canonical campaign estimands or publishable campaign outputs. Retain the cross-platform runs as diagnostic evidence and resubmit after the blockers below are closed.

The reviewed text changed from the requested \(10^{-9}\) f64 limit to \(10^{-4}\). Neither version supports approval as written.

### Threshold assessment

| Criterion | Observed Mac maximum | Assessment |
|---|---:|---|
| f64: original \(10^{-9}\) | \(6.944\times10^{-6}\) | Empirically fails by ~6,944×. |
| f64: current \(10^{-4}\) | \(6.944\times10^{-6}\) | Encloses the sample with ~14× headroom, but is only an engineering ceiling—not a guarantee on unseen stars. |
| f32: \(10^{-3}\) | \(5.155\times10^{-5}\) | ~19× headroom. Unsafe to call non-decision-bearing: f32 periodograms select and rank peaks upstream of decisions. |
| A95: \(10^{-2}\) | \(1.971\times10^{-3}\) | Acceptable only as explicitly platform-specific descriptive output; it must never affect inclusion, thresholds, endpoints, or model choice. |
| Frequency: \(10^{-12}\) | \(2.929\times10^{-13}\) | Adequate for observed same-grid rounding, but require exact grid-index identity and unchanged downstream match classification. |

The Mac report contains the relevant maxima ([replay_report.json:37](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/xplat_mac/replay_report.json:37), [replay_report.json:121](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/xplat_mac/replay_report.json:121), [replay_report.json:205](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/xplat_mac/replay_report.json:205)). The corrected prose still understates its field-level breakdown: independent recomputation finds Baluev-FAP drift up to \(5.67\times10^{-6}\) and window-power drift up to \(6.94\times10^{-6}\), not \(1.3\times10^{-6}\) and \(6.4\times10^{-7}\) as stated at [CROSS_PLATFORM_REPLAY.md:34](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/CROSS_PLATFORM_REPLAY.md:34).

### Blocking findings

1. **The comparator is report-only and fail-open.** It ignores missing keys, truncates list comparisons with `zip`, lacks finite-mask checks, skips zero A95 values, and does not compare exact grid indices or derived overall best pass ([replay_gate.py:103](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/replay_gate.py:103)). It also classifies every field named `power` as f32, although single-band peak powers are exact f64 and only multiband peak powers are f32 readbacks ([run_lomb_scargle.py:77](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_lomb_scargle.py:77), [run_lomb_scargle.py:150](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_lomb_scargle.py:150)).

2. **The Mac evidence is not generation-bound.** The current report reused all 25 outputs, while resume verifies only `complete`, not their producing environment, code, or inputs ([replay_gate.py:229](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/replay_gate.py:229), [replay_report.json:388](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/xplat_mac/replay_report.json:388)). It proves re-comparison of those files, not fresh generation under the recorded environment. Acceptance evidence needs a no-resume run or cryptographically bound per-output provenance.

3. **Evidence scope is insufficient.** Colab’s nine stars do not meet the proposed 25-star requirement, and its report predates the current diagnostic. Mac’s 25 schema/stride-selected stars establish agreement only for that exact machine/environment and roster. They do not bound behavior near numerical discontinuities on new campaign stars. This also relaxes the 928-star exact-set condition whose resolution closed G2 ([sol_methods6.md:1](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2r6/sol_methods6.md:1)). For primary or confirmatory campaign work, require a fresh full-928 replay on each candidate environment, or return with a separately reviewed, boundary-enriched stress roster. A 25-star tier is suitable only for pilot/exploratory work.

4. **The campaign boundary flag does not protect estimands.** Flagging `platform_boundary_sensitive` while retaining the platform-produced status or frequency still lets it enter detection and frequency-recovery estimands ([CROSS_PLATFORM_REPLAY.md:76](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/CROSS_PLATFORM_REPLAY.md:76), [METRICS_SPEC.md:13](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:13)). Excluding it would change the frozen denominator. Every flagged case therefore needs strict-environment recomputation before metrics, with that result authoritative. If unavailable, metrics must stop or report both assignments; P5 must use the worst-case assignment because one confirmation flip can reverse its conclusion.

5. **FAP is not the only boundary.** The audit must also cover:

   - candidate and low/high-pass FAP ordering;
   - the window-power threshold and alias boundaries;
   - f32 peak/top-k ordering and candidate clustering;
   - multiband membership;
   - exact overall `best_pass`, status, basis, and grid index;
   - direct, harmonic, and window-alias truth-match boundaries.

   Float32 powers are causally upstream of peak extraction and `multiband_top5` ([lomb_scargle_common.py:97](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/lomb_scargle_common.py:97), [run_lomb_scargle.py:177](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/run_lomb_scargle.py:177)); the memo’s statement that they enter neither decisions nor estimands is therefore false.

6. **Metrics can bypass replay provenance.** The runner enforces an attestation, but metrics accepts an arbitrary stars directory and does not validate the run manifest, attestation, tier, or per-star provenance ([metrics_generalization.py:801](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:801)). Its manifest omits the replay-attestation reference required by the frozen spec ([metrics_generalization.py:903](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:903), [METRICS_SPEC.md:218](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:218)). This permits copied, stale, or mixed-tier JSONs to enter estimates.

7. **The freeze authority is inconsistent.** `G2_FREEZE.md` records plan SHA `8487…`, but both the tagged and current plan hash to `8bb8…`, matching the Mac report ([G2_FREEZE.md:15](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G2_FREEZE.md:15), [replay_report.json:425](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/env/xplat_mac/replay_report.json:425)). Add a formal erratum and Amendment 1 entry before any campaign L-S execution.

### Required record and claim separation

A resubmitted gate must record:

- `strict_pass`, `decision_equivalent_on_roster_pass`, `accepted_for_campaign_generation`, and `byte_claim_eligible` separately;
- exact roster IDs/digest, schema composition, reference-bundle and input-shard hashes;
- environment, hardware, BLAS/thread configuration, frozen/code/spec/plan/amendment SHAs;
- versioned field typing and comparison policy, including absolute-plus-relative tolerances and nonfinite/signed-zero rules;
- counts and absolute/relative maxima with source ID, pass, JSONPath, and both values;
- every decision/ranking/matching margin and any strict adjudication;
- the immutable attestation hash in per-run provenance, metrics manifests, README, `DATA_PROVENANCE`, acceptance record, and `SHA256SUMS`.

The byte claim must be limited to named 2026-08-01 anchor artifacts and their documented raw, newline-canonicalized, or schema-projected strict tier. Any campaign bundle containing soft-tier bytes must explicitly state that it is not a byte-for-byte reproduction of the anchor.

No files were edited.
