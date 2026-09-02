# Review request: pre-registration of the v2 detector arm (ADMIT / REVISE)

You are reviewing, as a methods + statistics referee, the pre-registration document
`generalization/v2/V2_PLAN.md` in the repository at
/Users/jackneo/Documents/vonhippel-base9/astro-wd (read it first, in full). You may read any
file in the repository to check claims; do NOT modify anything. Context you need:

- The frozen campaign (GENERALIZATION_PLAN.md, METRICS_SPEC.md — both frozen, SHA-pinned)
  scores a frozen Lomb–Scargle detector on D3 (2,901 ZTF light curves of Kepler-labeled stars:
  610 δ Sct, 2,314 non-δ Sct, 76 excluded) and D2 (TESS-DAV modes injected into real ZTF
  windows + Gaussian nulls + paired controls). Frozen D3 results (results/2026-09-02_d3/README.md):
  detection completeness 54 %, negative-class trigger 42 %, dominant-frequency recovery 16 %.
- v2 is a NEW detector arm designed from the frozen arm's descriptive failure analysis. Its
  code is scripts/v2/ (read v2_common.py, align.py, detrend.py, window.py, multiband.py,
  rule.py, analyze_star_v2.py, run_v2_ls.py, make_split.py, rescore_v2.py,
  compare_engines.py). The split files are in generalization/v2/ (split.csv, *_dev.txt,
  *_holdout.txt, split_manifest.json).
- The deliverable is an AAS 249 abstract (deadline 2026-09-30) + a January poster. The frozen
  arm is the control; v2 is judged on a pre-registered holdout against the frozen arm on the
  same stars.

Questions to answer, each with a verdict and the exact wording/code change you require if any:

1. Pre-registration soundness: is the dev/holdout split, the tunable-constant protocol (§3, §5:
   four constants, ≤ 3 declared values each, a fixed selection rule) and the "holdout scored
   once" discipline sufficient to make holdout numbers credible? Identify any leakage path,
   including the disclosed one in §10 (four smoke stars in the holdout) — is "report with and
   without them" adequate, or must they be excluded/handled differently?
2. Endpoints (§6): are the paired statistics right (McNemar exact for paired binary outcomes,
   star-bootstrap difference CI, target-cluster bootstrap for D2 P4, CP upper for 500 nulls)?
   Is the pre-declared STRONG/other reading acceptable? Anything that should be added or
   removed (e.g., the P2 frame "usable in both arms", the control-window endpoint)?
3. Algorithm risks (§2): (a) alignment absorbing real slow variability when oids are
   time-disjoint; (b) the 30-day running median leaving 0.03–24 c/d power in the high-pass
   series so it leaks into the 24–1440 c/d band through the spectral window (the frozen nightly
   median removed it); (c) the extended veto's exposure (fixed loci, data-driven top-12 window
   peaks, mirror family, cross-pass partners) killing real signals — is the "≈0.4 % of the high
   band per cross-pass partner" estimate right, and should the veto exposure of the truth
   frequencies be computed and reported (it is not yet in the plan)?; (d) the coherence gate
   (fixed 0.15-cycle phase tolerance and 0.3–1.5 amplitude ratio, ignoring the phase
   uncertainty) — is it defensible as pre-registered, or must a phase-uncertainty-aware
   statistic be used?
4. Provenance (§8): v2 is not byte-attested; results are bound to code/constants/env/shard
   digests and the machine label; the campaign digest is deliberately NOT bound (rationale in
   the plan). Acceptable for a poster/abstract claim? What must the abstract disclose?
5. Anything in the plan that is internally inconsistent with the code as written (spot-check
   the constants table against scripts/v2/v2_common.py, the veto loci against window.py, the
   decision rule against rule.py, the split rule against make_split.py).

Format: a numbered list of findings, each tagged BLOCKING / MAJOR / MINOR, then a one-line
overall verdict `VERDICT: ADMIT` or `VERDICT: REVISE` with the list of required changes.
Be concrete and terse; cite file:line where relevant.
