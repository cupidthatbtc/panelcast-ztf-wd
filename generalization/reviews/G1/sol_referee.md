## Referee verdict

I would reject an abstract claiming a “quantified selection-function measurement.” The present design supports a domain-restricted external validation in D3 and a conditional injection–recovery experiment in D2. It does not measure an end-to-end real-sky selection function, and it does not currently measure a defensible false-positive rate.

The decisive problems occur in the [D3 design](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:75), [D2 design](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:103), and [headline estimands](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/METRICS_SPEC.md:38).

## Numbered objections

1. **REJECT-LEVEL — D2 templates are selected using the pipeline outcome being evaluated.**  
   The templates are the 510 stars previously classified as “not detected” by the frozen pipeline. That is a direct circularity path: the evaluation conditions the real-noise/window population on the algorithm having failed to trigger. This suppresses trigger-prone artifacts and selects favorable noise realizations. The admission that arm-B nulls are tautological does not cure the bias in positive injection recovery.  
   **Fix:** draw templates without reference to frozen-pipeline status—ideally the actual ZTF windows of the Romero targets, otherwise a prespecified random or weighted sample of the full parent population. Run paired zero-signal and injected versions. If unchanged, every D2 result must explicitly be conditional on “previously non-triggering templates.”

2. **MAJOR — D3 has no obvious ZTF label leakage, but “independently labeled” needs qualification.**  
   Murphy labels and Mo frequencies are external to the ZTF pipeline, so I see no direct D3 label-to-ZTF-output circularity. However, Mo is described as a Murphy×Bowman-derived sample; these are not independent label sources.  
   **Fix:** say “labels obtained independently of the frozen ZTF pipeline,” not “independent catalogs” or “independent validation datasets.” Freeze crossmatches and all ambiguity resolution before opening ZTF outcomes.

3. **REJECT-LEVEL — D2 is not an independently labeled positive sample.**  
   The TESS catalog supplies an external signal prescription, but the evaluated ZTF positives are synthetic. Matching a recovered frequency to the injected frequency is legitimate injection scoring, not independent real-source validation.  
   **Fix:** classify D2 exclusively as an injection–recovery experiment. Do not count D2 as satisfying the plan’s requirement for “independently labeled samples.”

4. **REJECT-LEVEL — The stated TESS sinc algebra is wrong.**  
   For a 120-s boxcar,  
   \[
   A_{\rm obs}/A_{\rm true}=\left|\mathrm{sinc}(\pi\,120/P)\right|.
   \]
   The first null occurs at \(P=120\) s, not 240 s. At \(P=197\) s the attenuation is approximately 0.492, not 0.3; \(|\mathrm{sinc}|=0.3\) occurs near \(P=160\) s. The text conflates sampling Nyquist with exposure-integration attenuation. This can materially corrupt injected amplitudes.  
   **Fix:** derive the formula using the actual integration time, distinguish Nyquist aliasing from boxcar attenuation, and test it numerically at the null, Nyquist period, and threshold.

5. **REJECT-LEVEL — The D2 phases are unspecified and potentially artificial.**  
   The Romero tables provide periods and amplitudes, not the phases needed to reconstruct a unique waveform. “Shared \(t_{\rm ref}\)” secures cross-band coherence but may align all modes at one arbitrary phase. Sparse ZTF recovery can depend strongly on phase and multimode interference. DAV amplitudes also vary between the TESS and ZTF epochs.  
   **Fix:** assign independent prespecified random phases per mode, share each mode’s phase across bands, use multiple phase draws, and include temporal-amplitude scaling as a sensitivity axis. Inference must cluster repeated realizations by source.

6. **REJECT-LEVEL — Real timestamps and residuals do not imply real-sky completeness.**  
   D2 preserves selected timestamps, errors, and residual artifacts. It does not preserve the joint distribution of target position, detector, color, blending, crowding, crossmatch failures, source extraction, quality cuts, native variability, or survey availability. Because injection occurs after at least some upstream operations, it cannot validate those operations.  
   **Fix:** call the result “conditional injection–recovery efficiency of the search stage.” An end-to-end claim requires injection upstream of extraction/QC or real labeled ZTF targets followed through every pipeline stage.

7. **MAJOR — Arm-A nulls measure a model false-alarm probability, not real-sky FPR.**  
   Gaussian draws on real timestamps test calibration under Gaussian noise and the chosen error model. They omit non-Gaussian artifacts, blending, calibration failures, and intrinsic variability.  
   **Fix:** label this “Gaussian-null false-alarm rate.” A real-sky FPR requires independently identified quiet sources processed end to end.

8. **MAJOR — D2’s repeated injections invalidate ordinary Wilson intervals.**  
   Three windows per Romero target, multiple phases, and 18 transformation variants are correlated replicates. Treating them as independent Bernoulli trials produces overconfident intervals.  
   **Fix:** specify the target-level estimand and use a two-stage or cross-classified bootstrap over Romero sources and template windows. Report the number of unique sources and windows separately.

9. **REJECT-LEVEL — `dSct=0` does not support the claimed FPR, including as an “upper bound.”**  
   These objects may be other real variables or missed δ-Scuti stars. A legitimate detection of another variable is not a false positive for a generic variability pipeline. Moreover,
   \[
   P(D\mid dSct=0)=\pi_C P(D\mid C)+\pi_VP(D\mid V)
   \]
   is not necessarily an upper bound on \(P(D\mid C)\) without an unjustified ordering assumption.  
   **Fix:** rename it “trigger rate among Murphy non-dSct stars.” For FPR, construct an independently selected Kepler-quiet control set and audit detected controls for contamination and crossmatch failures.

10. **MAJOR — Matching any Mo frequency creates a multiple-opportunity match.**  
    The Mo table contains roughly 141 frequencies per cataloged star on average. A candidate matched to any listed frequency has many chances to succeed by accident, especially around window aliases. Calling this `matched_primary` is misleading.  
    **Fix:** make dominant-mode recovery the primary frequency metric; retain any-published-mode recovery as secondary. Estimate accidental-match probability by permuting frequency lists between stars or shifting them while preserving mode count and frequency support.

11. **REJECT-LEVEL — The 456/610 amplitude join can bias the headline turn-on curve.**  
    The amplitude estimand is
    \[
    P(D\mid A,J=1),
    \]
    where \(J\) denotes inclusion in Mo, not \(P(D\mid A)\) for all 610 positives. Because Mo frequencies require SNR \(>8\) and catalog inclusion is plausibly related to amplitude, frequency complexity, magnitude, and crowding, missingness is almost certainly informative. The curve may be preferentially populated by easier detections.  
    **Fix:** extract amplitudes uniformly for all 610 positives. Otherwise call the curve “Mo-join-conditioned,” compare joined and unjoined recovery and covariates, and provide sensitivity bounds. Propensity weighting alone cannot repair unmeasured amplitude-dependent missingness.

12. **MAJOR — The frequency-completeness denominator is internally inconsistent.**  
    The metrics specification says stars without Mo rows receive no frequency scoring, but defines headline completeness conditional on all labeled positives. Dropping 154 unscorable positives silently changes the denominator from 610 to 456. Counting them as misses would also be wrong.  
    **Fix:** define separate estimands explicitly: detection completeness on \(N=610\), and frequency-recovery completeness on the Mo-covered \(N=456\). Never present the latter as completeness for all Murphy positives.

13. **MAJOR — Mo’s amplitude is not \(A_g\).**  
    The plan converts ppt to mmag but does not establish a Kepler-to-ZTF-\(g\) amplitude transformation. The metrics specification nevertheless calls the surface axis \(\log A_g\). In addition, the Kepler amplitude is non-contemporaneous with ZTF.  
    **Fix:** label the axis “historical Kepler-band dominant amplitude.” Either model the bandpass and temporal-amplitude uncertainty or refrain from interpreting the curve as a ZTF-\(g\) detection threshold.

14. **MAJOR — The \(g\ge13.2\) cut defines a truncated population, not a correction for saturation.**  
    The cut removes bright stars and can change the amplitude, subtype, color, and crowding distribution. Its provenance is unclear: catalog \(g\), ZTF median \(g\), and transformed Gaia \(g\) imply different selection mechanisms.  
    **Fix:** define the magnitude source and apply the cut before viewing outcomes. Publish an attrition table by label, amplitude-join status, period, color, and crowding. Restrict every claim to \(g\ge13.2\); do not extrapolate across the cut.

15. **MAJOR — Stride-sampling negatives in KIC order is not representative sampling.**  
    Determinism is not a statistical virtue. Catalog order can correlate with sky position and consequently ZTF coverage, crowding, and observing history. The case-control roster also destroys natural class prevalence.  
    **Fix:** use a frozen random or stratified sample with known inclusion probabilities, balancing at least magnitude, color, position, crowding, and coverage. Carry sampling weights into population-rate and purity calculations.

16. **REJECT-LEVEL — “Tabulated separately” does not resolve unavailable cases.**  
    For an end-to-end selection function, fetch, crossmatch, QC, and unavailable-pass failures are misses. For search-stage completeness, they may be excluded—but then the estimand is conditional on analyzability. The specification never makes this choice.  
    **Fix:** report both:
    \[
    P(D\mid\text{eligible target})
    \quad\text{and}\quad
    P(D\mid\text{usable light curve}).
    \]
    Provide a full eligibility-to-output attrition diagram.

17. **MAJOR — The proposed “purity” is not purity.**  
    \(P(\text{frequency match}\mid\text{detected, labeled positive})\) is frequency agreement among known positives. It is not positive predictive value. The roster’s altered prevalence and contaminated negative class make population purity unidentified.  
    **Fix:** rename it “frequency-match fraction among detected positives.” Claim purity only after representative prevalence weighting and adjudication of detections in a valid negative population.

18. **MAJOR — The turn-on analysis is insufficiently prespecified.**  
    Exact bin edges, minimum cell sizes, treatment of empty/sparse cells, and any smoothing or monotonic fitting are absent. A min–max band across transformation ladders is a sensitivity envelope, not statistical uncertainty.  
    **Fix:** freeze bin edges and minimum counts now; distinguish sampling intervals from model-sensitivity envelopes; use cluster-aware intervals for D2.

19. **MAJOR — McNemar does not by itself establish “complementarity.”**  
    The L-S side requires frequency truth while the census side does not, so the paired outcomes are not symmetric. McNemar tests marginal discordance, not scientific complementarity or incremental recovery.  
    **Fix:** headline the full overlap table and incremental completeness with paired confidence intervals. Treat McNemar as a secondary comparison using genuinely parallel detection definitions.

20. **REJECT-LEVEL — The three datasets cannot be collapsed into one selection-function measurement.**  
    D1 is 19 labeled white dwarfs, D2 is a conditional synthetic DAV experiment, and D3 is a magnitude-truncated Kepler-field δ-Scuti sample. They have different populations, labels, amplitudes, windows, and endpoints. The [slip rule](/Users/jackneo/Documents/vonhippel-base9/astro-wd/generalization/GENERALIZATION_PLAN.md:176) claiming D2+D1 alone “flips” the independent-label condition is untenable.  
    **Fix:** report three separate response assessments. Any synthesis must be qualitative or list domain-specific estimands side by side—never pool them into “the pipeline selection function.”

## Wording that could survive review

If the D2 design remains unchanged:

> Using published TESS mode solutions as external signal prescriptions, we measured the frozen search’s conditional injection–recovery efficiency after adding synthetic DAV signals to previously non-triggering ZTF light curves. This semi-empirical test preserves the timestamps and residuals of the selected templates but remains conditional on template selection, phase and stationarity assumptions, the TESS-to-ZTF amplitude transformation, and successful upstream data processing. It is not an empirical estimate of DAV completeness on the ZTF sky.

For D3:

> We measured detection completeness in Murphy et al. dSct=1 stars satisfying \(g\ge13.2\). Amplitude-dependent results are conditional on the 456/610 objects joined to Mo et al. and use historical Kepler-band amplitudes. The trigger rate among dSct=0 stars is reported as a negative-class trigger rate, not as a constant-source false-positive rate.

A defensible abstract-level claim would be:

> We map the conditional recovery behavior of a frozen variability pipeline using an externally labeled, magnitude-restricted Kepler δ-Scuti sample and TESS-derived DAV injections into selected ZTF light curves.

I would strike “quantified selection-function measurement,” “real-sky completeness,” “independently labeled D2 sample,” “D3 FPR,” and “purity” unless the corresponding fixes above are implemented.
