# G5prep round 2 — pre-metrics adjudication of the methods-panel findings

You are GPT-5.6-sol acting as the statistics + methods adjudicator for the
astro-wd generalization campaign (repo: this directory). Read first:
generalization/METRICS_SPEC.md, generalization/GENERALIZATION_PLAN.md,
generalization/reviews/G2_FREEZE.md (Amendments 2–4 RATIFIED; the
2026-08-31 descriptive diurnal admission and its terms),
generalization/reviews/G5prep/sol_diurnal.md (your prior ruling — the
template for what "descriptive post-launch" means here), and the fresh
five-persona methods panel: generalization/writing/methods_review/FINDINGS.md
(+ REVIEW_PANEL.md for detail).

## Situation (facts I verified myself, not the panel's numbers)

- D3 FULL run (2,901 Kepler-field ZTF light curves; 610 dSct=1, 76 dSct=2,
  2,314 dSct=0) finishes ~2026-09-02 05:40 UTC; a laptop-side chain then
  computes the FROZEN metrics automatically. NO full-campaign D3 or D2 metric
  exists yet. D2 FULL follows (~2026-09-04).
- Amendment 4 stands: no estimand-hierarchy change is permitted. The frozen
  scripts are untouchable. metrics_generalization.py is campaign code (in the
  SHA surface) but is post-hoc and re-runnable; descriptive add-ons live in
  scripts/generalization/descriptive/ (outside the SHA glob) per your prior
  ruling.
- Verified: (a) METRICS_SPEC lines 34–36 and 248–262 MANDATE a 7-dimension
  attrition table (class × amplitude stratum incl. amp_unknown × Mo-join
  status × magnitude × dominant period × Teff × crowding), a joined-vs-
  unjoined covariate table, and `assert count == 456` for freq-scorable
  positives — metrics_generalization.py emits NONE of them (attrition.csv =
  7 scalars). (b) truth_d3() builds truth lists from Mo+2026 table2 only
  (median 132 modes/star); every table2 frequency is sub-Kepler-Nyquist
  (max 282.92 µHz vs f_Nyq = 283.2 µHz); table1's physical `fR` is never
  used. Of the 290 flag-1 positives with ≥1 confirmed super-Nyquist mode
  (table1 C=0), exactly 40 have their largest-amplitude ("dominant") mode BE
  that super-Nyquist mode, and for all 40 the scored dominant frequency
  equals the reflection 2·f_Nyq − fR (|diff| < 0.1 µHz). Dominant-frequency
  quantiles 10/50/90 = 1.38/12.64/21.2 c/d; 0 of 459 ≥ 24.47 c/d; 120 < 4
  c/d (90 < 2.5); 50 of the 291 "sub-hour" members have dominant < 4 c/d.
  (c) build_d3_roster flags `gmag < 14.0` as near-saturation; the spec says
  "g <= 14.0 flagged"; 3 roster stars sit at g = 14.000 exactly and are
  flagged safe. (d) Class covariate imbalance: fraction g < 14 = 0.47
  (flag0) vs 0.66 (flag1). (e) plot_generalization.plot_turn_on reads a
  surface file name/schema the metrics never write (figure silently
  skipped) — figure code, not an estimand; noted, not adjudicated.
- Spec header: "Any change after the first campaign L-S run voids the
  prespecification and must be reported as such"; ledger: the first
  CONFIRMATORY run is the D2/D3 full run; spec v4 note calls Amendment 4 a
  disclosed post-pilot, pre-confirmatory amendment.

## What I need from you — one ruling per item, fixed BEFORE any D3 number exists

For each item give: VERDICT ∈ {COMPLIANCE (spec-mandated; must be
implemented in metrics_generalization.py), ADMIT-DESCRIPTIVE (segregated
descriptive output, prespecified=false, no interval, disclosed), REFUSE},
the EXACT frozen definition (bin edges, cells, tolerances, denominators,
column names) chosen now without any D3 result in view, file placement, the
disclosure sentence, and whether it must be computed before/after the frozen
metrics run (the frozen outputs are unaffected either way; I will require a
byte-identity diff of every pre-existing metrics file between the laptop's
pre-fix run and the Mac's post-fix run as the guard — say if that guard is
sufficient).

1. F07 — the mandated attrition table, joined-vs-unjoined covariate table,
   and the == 456 assertion. Fix the discretionary bins: magnitude (the spec
   gives only the g ≤ 14.0 split), Teff (quartiles of which frame?), dominant
   period, crowding (cone-object count; nearest separation), amplitude strata
   incl. amp_unknown. Also rule on (c): implement `<= 14.0` as the spec says
   (moving 3 stars) or keep the code's `< 14.0` with disclosure? Note any
   code change to build_d3_roster.py would alter the roster file SHA bound
   into the run — so the roster is fixed; the question is how the metrics
   STRATIFY.
2. F02–F04 — descriptive rescoring of the 40 aliased-dominant targets
   against fR (same match taxonomy/tolerance), a `matches_nyquist_reflection`
   relation, adding table1 fR modes to a descriptive any-mode match, and a
   P2 split by dominant-frequency regime (< 4 / 4–24 / ≥ 24 c/d; the last is
   empty → counts). P2 itself untouched. Wording: "stars with a confirmed
   super-Nyquist mode" instead of "sub-hour stratum"; "dominant = largest
   amplitude, not necessarily a p mode".
3. F01 — descriptive partition of rule-1 confirmed POSITIVES by
   `best_candidate_matches_dominant` class × `any_top_peak_matches_any_mode`
   (from per_star.csv). Separately: is applying the ADMITTED solar-diurnal
   band rule to confirmed POSITIVES admissible as a descriptive column, or
   does that exceed the 2026-08-31 admission (negatives only)?
4. F09 — printing the already-emitted per-pass recovery rows beside P4 and
   stating P4 is a best-pass estimand: presentation only? Confirm no new
   computation is implied.
5. F08 / F11 / F38 (D2) — recovery and trigger by W_g stratum K × template
   published status (from the generation manifest's template columns);
   a control-reuse figure from d2_control_reuse.csv; a paired arm-A vs arm-B
   table per (target, K). All descriptive.
6. F15 / F17 / F27 / F37 (D3 negatives) — P3 (rule 1, best pass, plain
   counts) by magnitude stratum, Teff quartile, merged-oid count
   (2 / 3–4 / ≥ 5 — from crossmatch_qc `selected_ztf_objects`), by PASS
   (low / high), and by sky cell (define the cells now); plus a covariate-by-
   class table. All descriptive, no intervals. Rule on whether "P3 by pass"
   may be labelled a sub-hour false-trigger proxy (F37) — my inclination: no.
7. F16 / F18 — a coverage comparison table (D3 vs the 928-star pool: zg/zr
   epochs, nights, W_g quantiles) from the census panels; per-pass a95
   distributions by class from the per-star JSONs. Descriptive.
8. F21 — beside the prespecified any-mode 100-permutation chance rate, a
   dominant-only, confirmed-conditioned 10,000-derangement descriptive rate.
9. F32 / F33 — a D1 confirmed-frequency histogram vs D3 negative triggers
   (figure); descriptive extra-relation columns (yearly alias ±1/365.25 c/d;
   Kepler-Nyquist reflection) beside the frozen taxonomy.
10. F05 — the dated exposure table (amendment, trigger, data seen, change)
    and ONE sentence reconciling the spec header with the ledger's
    confirmatory-run reading. Give the sentence.
11. Disclosure register only (no ruling needed unless you object): F06, F12,
    F13, F19, F20, F22, F23–F31, F35, F36, F39.

Constraints you must respect: nothing may veto, exclude, reclassify, or
re-denominate any prespecified endpoint; no confidence intervals on
descriptive rows; every descriptive output carries
analysis_status=postlaunch_descriptive (or `prespecified_compliance` for
item 1), prespecified=false/true accordingly, interval=none; the outside-band
component is never a corrected P3; and no wording may promote a descriptive
row to a headline. If an item cannot be defined without seeing D3 results,
REFUSE it.

End with a one-line VERDICT SUMMARY listing each item's verdict.
