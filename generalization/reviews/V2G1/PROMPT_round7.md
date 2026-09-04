# V2G1 round 7 — pre-holdout amendment of the fixed window-veto loci (2026-09-04)

You are the methods reviewer of a pre-registered comparison (repository root is the
working directory; read-only). The plan is `generalization/v2/V2_PLAN.md`; your rounds 1–6
are in `generalization/reviews/V2G1/` (round 6 = ADMIT). Since round 6 the v2 dev runs
started on the laptop; NO holdout star has been scored and no holdout lock exists.

Today the author inspected the PARTIAL dev D3 run (1,065 of 1,458 dev-half stars, scored
at the admitted digest `ecc5df75…`) and amended the fixed veto loci in closed form. The
amendment is logged as the last entry of V2_PLAN.md §10 and changes §2 item 3, §5 (last
paragraph) and the §7 disclosure sentence. Code: `scripts/v2/window.py` (new
`comb_sideband_label`, `diurnal_band_label`, `locus_label`, `fixed_locus_label`; the
sidereal-month loci `*_sidmonth±1`), `scripts/v2/rescore_v2.py` (`window_alias_under` now
calls `fixed_locus_label`), `scripts/v2/v2_common.py` (`SIDEREAL_MONTH_DAYS`),
`scripts/v2/dev_tuning.py` (`--dev-run-digest`, recorded as `dev_runs_v2_digest`),
`scripts/v2/analysis/dev_mac_sequence.sh` (digest parity against the dev-run digest),
`scripts/v2/analysis/veto_exposure.py` (`fixed` component via `fixed_locus_label`),
`tests/test_v2_window.py`. Run `git diff HEAD~1 -- scripts/v2 tests generalization/v2
generalization/writing/outline/OUTLINE.md` to see the exact change if HEAD is the amendment
commit, else `git diff`.

Evidence the author saw (dev half only, partial, never a reportable number): of 94 dev
flag0 stars confirmed by v2, 45 sit at 1.9689–1.9690 c/d = 2·1.00274 − 1/27.321661
(sidereal-month sideband of the second sidereal-day harmonic), between the listed loci
1.96614 and 1.97161 at ≈ 5 tol; 5 at 1.0011–1.0041 c/d in the gaps of the yearly-sideband
comb; 4 in the high pass at 46.9634 = 47 − 1/27.321661 and 48.9662 = 49 − 1/29.530589.
Applied offline: 56 of 94 dev-negative confirmations and 9 dev-positive confirmations
removed, none added; 8 of the 9 positives sat at those loci without a truth match, 1 was a
correct recovery of a 1.03975 c/d dominant mode (within tol of 1.00274 + 1/27.321661).
`rescore_v2.rescore_star` reproduced the runner's status/pass/frequency on 1,065/1,065
partial dev stars with the PRE-amendment code (exactness of offline re-scoring on real
data). Exposure of the amended fixed rule: 7/456 Mo dominant frequencies (0 before),
38/6,558 D2 injected modes (0 before), 1.0 % of a uniform draw in 4–24 and 24–1440 c/d.
Tests: 257 passed. New digest `1a99db05…`.

Questions (answer each with a numbered finding; be adversarial; cite file:line):

1. Admissibility. §5 said the fixed loci were "not tunable, ever". The author extends them
   once, in closed form, after dev-half inspection, before any holdout star, with a §10
   entry, a §7 disclosure clause and the partial-dev evidence. Is this an admissible
   pre-registration amendment, or does it need something more (e.g. the amendment commit
   hash bound into `V2_CONSTANTS_FROZEN.json` / the holdout lock, an explicit "no further
   veto change after the lock" rule, the pre-amendment sentence kept verbatim somewhere)?
   Is the disclosure clause adequate and not misleading?
2. Correctness of the derivation: 1/solar − 1/synodic = 1/sidereal-day − 1/sidereal-month
   (both 0.96614 c/d at k = 1), splitting at k = 2 to 1.96614 vs 1.96888. Is the
   sidereal-month mechanism (moon position vs a fixed field) physically right for a
   nightly ground-based survey, and is the comb rule (sidebands ± 1/month of BOTH spacings
   for every k, bare sidereal lines for every k — the frozen family — and no bare solar
   line beyond k = 3) a principled closed-form family rather than a data-fitted patch?
3. Exactness: is `window.locus_label` used identically by the runner
   (`is_window_alias_v2`) and by `rescore_v2.window_alias_under` (fixed loci + comb + band,
   then the local test, then the data-driven peaks), so that the dev runs at the old digest
   can be re-scored under the amended veto without a rerun? Any path where the runner's
   recorded `*_window_locus` / `*_alias` fields would be read by the re-scorer or the
   metrics instead of being re-derived? Any effect on the cross-pass partner re-derivation
   or the joint top-5 after veto?
4. Provenance: the dev runs carry digest `ecc5df75…`, the re-scoring and the holdout carry
   `1a99db05…`. `dev_tuning.py` records `dev_runs_v2_digest`; `dev_mac_sequence.sh` asserts
   the dev-run digest. Does anything downstream (runner registered mode, metrics `--engine
   v2`, `compare_engines.py`) break or silently accept a wrong digest? Should the
   constants artifact or the lock bind the amendment commit?
5. Exposure and disclosure: 1 % of the axis, 7/456 and 38/6,558 truth frequencies. Is
   this acceptable, is it disclosed in the right places (§10, §6 audits, the outline's
   not-allowed list / contingencies), and should the STRONG screen or any endpoint change?
   (The author's position: no endpoint or screen changes.)
6. Anything else that must change before the holdout (README/RUNBOOK text, outline,
   tests), or any reason to REVISE.

End with `VERDICT: ADMIT` or `VERDICT: REVISE` and, if REVISE, the minimal list of
required changes.
