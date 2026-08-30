1. The transfer-function physics is right, but the “up to ~2×” claim is too strong as written. For a coherent mode,
   \[
   S_T(P)=\operatorname{sinc}(\pi T/P),\qquad
   A_{\rm pub}\simeq A_{\rm intrinsic}S_{\rm mix}(P),
   \]
   where a joint mixed-cadence fit has \(S_{\rm mix}\) determined by the fit’s cadence counts, weights, and phase coverage. With positive contributions from both cadences, \(S_{120}<S_{\rm mix}<S_{20}\), so the frozen 20-s correction does under-correct, but by
   \[
   U(P)=S_{20}(P)/S_{\rm mix}(P),
   \]
   not generally by \(S_{20}/S_{120}\). At \(P=200\) s, the implemented sinc gives \(S_{20}=0.9836\), \(S_{120}=0.5046\), and the pure-endpoint ratio is 1.9495; thus “~2×” is the maximum 120-s-versus-20-s endpoint contrast, not the demonstrated bias of the stitched amplitude. The papers do concatenate mixed-cadence sectors for relevant solutions, but the exact fit weighting is not preserved in the roster or report. [Romero et al. 2025](https://arxiv.org/abs/2407.07260)

   The report’s cadence-coverage counts overlap: for TIC 55650407, `{20:17,120:20}` means 17 fast sectors and three additional 120-s-only sectors, not 37 independent sectors. Equal-sector weighting would give only a 1.079 correction at 200.08 s; approximate unweighted-point weighting, with about six times as many 20-s samples per equal-duration sector, gives 1.014. Across the 22 listed modes, equal-sector weighting peaks at about 1.36 and approximate point weighting at about 1.19. These are illustrative because the publication’s exact weights and mode stationarity are unknown.

   The bookkeeping also needs correction: v3 reports **33** switches, not 31, and joining those TICs to `d2_modes.csv` gives **141** modes. The finding’s “128” is the report-wide nonmarginal-mode count, not the mixed-target mode count. The 22-mode/11-target affected subset is reproducible. See the [v3 summary](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/data/d2/spoc_verification/v3_all103_verification_report.json:2) and the contradictory [finding count](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/reviews/G3/CADENCE_MIX_FINDING.md:11).

2. Adopt **A**, explicitly labeled a conservative **pure-120-s endpoint sensitivity**, not an estimate of the true effective cadence. It preserves the frozen nominal rule, brackets the integration-time systematic under the coherent-mode approximation, and costs exactly 33 K=1 shards. It is distinct from the 1.5× bandpass ladder: the ladder multiplies amplitudes coherently, whereas cadence attenuation is period-dependent and can change the retained mode set. Because the surface coordinate is the published amplitude, `cadence_alt` must retain the same amplitude bins and be reported separately from nominal, never pooled. The invariant-axis requirement is already explicit in [METRICS_SPEC.md](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:186).

   B cannot presently be made exact from the committed report. The formula apparently intended by “\(\sum N_{\rm cadence}T_{\rm int}/\) total cadences” is
   \[
   T_{\rm eff}^{(N)}
   =\frac{\sum_{s\in S_t}N_{ts}T_{ts}}{\sum_{s\in S_t}N_{ts}},
   \]
   using the published sector set \(S_t\), the number \(N_{ts}\) of quality-retained cadences actually entering the published fit, and the integration duration \(T_{ts}\in\{20,120\}\) for the product actually used. If “exposure-time-weighted” is literal, with \(E_{ts}=N_{ts}T_{ts}\), the formula instead becomes
   \[
   T_{\rm eff}^{(E)}
   =\frac{\sum N_{ts}T_{ts}^{2}}{\sum N_{ts}T_{ts}}.
   \]
   Neither is the correct mixed transfer in general because sinc is nonlinear. The more physical mode-specific expression is
   \[
   S_{\rm eff,t}(P)=
   \frac{\sum_s W_{ts}S_{T_{ts}}(P)}{\sum_s W_{ts}},
   \]
   with \(W_{ts}\) matching the NLLS weights. The JSON supplies overlapping sector coverage and aggregate point counts for the selected product, not the required per-sector fit counts and weights. C is unnecessarily destructive: it removes valid amplitude-surface observations while leaving the detection estimand’s cadence ambiguity unresolved.

3. Recompute retention independently inside `cadence_alt`. At 120 s, the modes at 126.84, 127.03, and 153.26 s—all on TIC 55650407—fail \(|\mathrm{sinc}|\ge0.3\) and must appear in `rejected_modes.csv`; every mixed target still has at least one retained mode, so all 33 alt shards remain schedulable. Their v3 directed SNRs are 1.03, 1.86, and 0.48, qualitatively consistent with little useful 120-s response, although SNR must not replace the numerical rejection rule. The implemented rejection and amplitude division are in [retained_modes/build_truth_model](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:160).

   Dominance must be scenario-local: `cadence_alt` uses the largest published amplitude among its 120-s-retained modes. Here the three rejected modes are not dominant; TIC 55650407 remains dominated by 262.46 s at 7.19 ppt, so neither the dominant frequency nor amplitude-surface coordinate changes. Dominant-mode dropout remains a separate nominal-cadence scenario—do not cross `dropout × cadence_alt`. Its eligibility and dropped mode continue to use the nominal retained set. Phase assignments remain stable because phases are generated before rejection and dropout.

### Recommended Amendment 3 text

Amendment 3 (mixed-cadence endpoint sensitivity): the frozen nominal cadence precedence remains `cadence_s = 20` whenever the chosen published solution contains any `f` sector; because the completed SPOC v3 verification identifies 33 such mixed 20-s/120-s targets, schedule for each exactly one additional arm-B, median-window (`K=1`) `cadence_alt` sensitivity shard at the nominal bandpass ratios (1.7/0.80), base phase draw, amplitude scale 1.0, PDCSAP crowding, and no dominant-mode dropout, evaluating the complete truth model with `cadence_s = 120` and reapplying the signed-sinc \(|\mathrm{sinc}|\ge0.3\) rule (three modes on TIC 55650407 are thereby rejected); `cadence_alt` is a conservative pure-120-s endpoint, not an estimate of the stitched solution’s effective cadence, is compared with nominal on the same 33-target K=1 subset using common bootstrap draws, never enters nominal P4 or is pooled with nominal surfaces, and retains the scenario-invariant published-amplitude coordinate; it has its own immutable scenario code and final campaign-ID digit and adds exactly 33 shards.

### Exact code change

- [d2_truth_model.py:scenario_code](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/d2_truth_model.py:122): add `SCENARIO_CADENCE_ALT`, cadence codes `0=nominal`, `1=alt`, and a `cadence_code` argument returning `"cadence_alt"` for code 1. Add typed manifest fields `cadence_code` and `cadence_s`. No algebra change is needed in `integration_sinc`, `retained_modes`, or `build_truth_model`.

- [build_d2_shards.py:campaign_id](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:204): change layout from `...PSC0` to `...PSCD`, using final digit `D=1` for `cadence_alt`.

- [build_d2_shards.py:main](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/build_d2_shards.py:338): load/pin the v3 report; define mixed TICs by `cadence_switched_from_roster`; assert 33; add `cadence_alt` to default scheduling; emit one nominal-ratio K=1 arm-B variant per mixed TIC with `build_truth_model(..., cadence_s=120)`, `cadence_code=1`, and no dropout/crowding/phase/amplitude-scale combination.

- [metrics_generalization.py:truth_d2/d2_cluster_bootstrap](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:275): propagate and group by `scenario`, `cadence_code`, and `cadence_s`; enforce the same-33-target K=1 common subset. Update `sensitivity_table` likewise.

- [metrics_generalization.py:surfaces](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:674): the current implementation pools all D2 scenarios. Filter headline surfaces to nominal arm B and, if alt surfaces are emitted, write them separately while retaining the published-amplitude coordinate.

- Extend `tests/test_d2_truth_model.py` and `tests/test_d2_shards_contract.py` to assert scenario disjointness, final-digit identity, 33/K=1 scheduling, the three 120-s rejections, unchanged dominant mode, phase stability, and no nominal-surface pooling.

## Verdict: ADOPT-A
