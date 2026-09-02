# G2 FREEZE RECORD — 2026-08-28

Unanimous FREEZABLE verdicts at review round 6 (referee6, stats6, methods6 —
each verifying its own residual list with line-level evidence and runtime
probes; see reviews/G2r6/). Review history: G2 round-2 (5 lenses incl.
abstract CONDITIONAL-GO and the twice-crashed astro lens completed at
round 4 with NO blockers), rounds 3–6 convergence; ~90 distinct findings
dispositioned (ledgers: G2/RESPONSE.md, G2r3/RESPONSE.md, G2r4/RESPONSE.md).

Frozen document SHA-256 (any change after the first campaign L-S run voids
the prespecification):

- generalization/METRICS_SPEC.md
  5d8d589ae73a608ada2f6f37c82e1be0ba63de9002b0a17c118410cccdf27824
- generalization/GENERALIZATION_PLAN.md
  8bb8cd8f6ed61722aee5c95ea2a207af0f7f9074dd0e40cbdbb23d907d6baaaf

Git tag: g2-frozen-2026-08-28. The spec SHA is re-verified at metrics run
time (manifest field spec_sha256).

## ERRATUM 2026-08-29 (found by the amendment-1 methods review)

The plan SHA originally recorded above (8487f14f9480612f…) was computed BEFORE
the freeze row was inserted into the plan's gate table, i.e. it hashed a
pre-freeze byte-state. The correct frozen plan SHA is the one at tag
g2-frozen-2026-08-28: 8bb8cd8f6ed61722aee5c95ea2a207af0f7f9074dd0e40cbdbb23d907d6baaaf. Verified: `git show
g2-frozen-2026-08-28:generalization/GENERALIZATION_PLAN.md | sha256`.
Current working-tree plan SHA: 8bb8cd8f6ed61722aee5c95ea2a207af0f7f9074dd0e40cbdbb23d907d6baaaf (identical to the tag).

## AMENDMENT 2 — 2026-08-30 (G3 round-1: D2 injection code, both reviewers REJECT)

Scope: D2 only; no campaign L-S run has been executed (the first campaign
run is the D3 pilot, still pending the IRSA fetch), so the freeze's own
rule ("any change after the first campaign L-S run voids the
prespecification") is respected. Trigger: generalization/reviews/G3/
sol_numerics.md and sol_methods.md (5 BLOCKING + 4 MAJOR + 2 MINOR distinct
findings). Changes to the prespecification, each reviewer-driven:

1. Crowding variant corrected: PDCSAP amplitudes are already
   dilution-corrected (Romero+2022 §2, Romero+2025 §2); the prespecified
   sensitivity is the SAP-equivalent RE-dilution A × CROWDSAP. The pre-G3
   text ("divide by CROWDSAP") was physically reversed and is withdrawn.
2. Dominant-mode dropout defined over RETAINED (post-sinc) modes; survivors
   keep their nominal phases; scheduled only for ≥ 2 retained modes.
   Phases are now a function of (TIC, phase_draw, table position) only.
3. Targets with zero retained modes at their cadence are excluded from the
   run matrix (recorded); the scheduled-target list in the generation
   manifest is the P4 denominator.
4. Fixed typed manifest schema + explicit scenario codes; P4 eligible
   denominator = scheduled strata per scenario (3 nominal, 1 sensitivity);
   dropout is its own scenario; nominal arm-B is the only confirmatory P4.
5. Generation discipline: staging + atomic publish, generation manifest
   (generation id over all input SHAs + code + args; per-shard SHAs;
   roster/SPOC provenance), no resume; runner and metrics verify the chain
   (sidecars bind result/shard/attestation/generation; completion table).
6. Pilot = stratified pilot_shard_index.txt via --stars-file; pilot outputs
   never confirmatory (P4/P5 rows carry confirmatory=false).
7. Campaign-id convention documents S=3 (dropout), the crowding digit and
   the 96 self-window prefix.
8. Token hygiene: the Gaussian-null arm is labelled gauss_null (the literal
   "null" is a pandas NA token — caught by the new contract tests).

Frozen document SHA-256 after Amendment 2:

- generalization/METRICS_SPEC.md
  a81f36d37d38be0a69a8c6dfd103f0c2da19ad1359e30e7cd27bcc21aed61e07
- generalization/GENERALIZATION_PLAN.md
  c1909fa231c790d5f01f42772d6afec6544d8a001ab1b5a1e2de3bf032c9ee95

Code: scripts/generalization/{d2_truth_model,build_d2_shards,
metrics_generalization,run_generalization_ls}.py; tests: 31 passing across
the suite at that commit (10 frozen-constant + 13 truth-model + 8 contract;
the contract tests run the real builder and the real metrics readers on a
miniature pool). D1 regression of the patched metrics program: 11/13, 9/13,
13/13 unchanged.
Round-2 verdicts: numerics APPROVE-WITH-CHANGES, methods REJECT (residuals:
production must require the full arm matrix; manifest row semantics; truth-
table SHA enforcement; completion-table + full sidecar binding; primary D2
aggregates must not pool scenarios; `confirmatory` = membership semantics;
sensitivity common-subset rows). All addressed in the round-3 commit
together with Amendment 3 (below): shared `validate_manifest_frame` (per-row
invariants incl. scenario and campaign-id recomputed from fields),
`production_reasons` + `expected_counts`/`assert_counts` (run matrix asserted
from the schedule in builder AND metrics), generation id over the shard-
determining code only, generation output SHAs + basis reproduction + frozen/
code identity enforced before any truth file is read, completion.csv
required and cross-checked (pilot flag re-derived), sidecars checked on pass
set/env/frozen/campaign/generation, D2 primary aggregates = nominal arm B,
`confirmatory` = prespecified-analysis membership (P4 detection rows, P5 with
1000 completed), sensitivity rows carry the nominal K=1 rate on each
scenario's exact target subset. Status: PENDING G3 round-3 verdicts.

## AMENDMENT 3 — 2026-08-30 (mixed-cadence endpoint sensitivity; G3 round-3 ADOPT-A)

Trigger: the completed SPOC verification arm (v3, all 103 targets) shows that
33 targets' published solutions combine 20-s ('f') and 120-s sectors, so the
frozen rule `cadence_s = 20 iff any f sector` under-corrects their short-
period modes (U = S_20/S_mix; endpoint contrast 1.95 at 200 s, stitched bias
~1.1–1.4). Adjudication: generalization/reviews/G3/sol_numerics_r3_cadence.md
(ADOPT-A). Change: the frozen nominal rule is UNCHANGED; a `cadence_alt`
sensitivity scenario (one K=1 arm-B shard per mixed target at 120 s, own
scenario code and final id digit, never pooled with nominal, common-subset
contrast) is added to the mandatory production matrix (33 shards). Full
text: GENERALIZATION_PLAN.md, D2 run matrix ("Amendment 3"). No campaign L-S
run has been executed.

Frozen document SHA-256 after Amendment 3 (round-4 state; the plan gained the
`CD` id-layout wording and the 3,299 core maximum):

- generalization/METRICS_SPEC.md
  6986e2fce033369d72efac9b08d257894446c2b71522a1f707587fe6cc6c9365
- generalization/GENERALIZATION_PLAN.md
  6b28b634f0abb96230c49eeb98463d6ba8c7c406b6dbddae54894d65f1f09ae6

Round-3 verdicts: numerics APPROVE-WITH-CHANGES (production must realize the
33 cadence_alt shards; paired common-draw contrast vs nominal K=1; layout/
count wording), methods REJECT (D3 run-universe binding BLOCKING; symmetric
missingness in matched sensitivity rows; D2 FP-frequency audit received the
wrong frame; crossed sensitivity axes accepted; cadence_alt cardinality).
Round-4 commit: `check_cadence_alt_schedule` (set identity + 33, builder AND
metrics), `d2_scenario_contrasts.csv` (every non-nominal arm-B scenario vs
nominal K=1 on the identical targets, one common draw matrix, paired
difference interval; usable = usable on both sides, eligible keeps missing as
failure on both), sensitivity rows on the symmetric common subset, FP audit on
the full frame with arm/scenario retained, mutually exclusive sensitivity
axes + crowdsap range + match/status vocabularies in the shared validator,
runner records shard_index path + SHA and metrics binds index SHA == run
manifest, index == on-disk shards, completion ⊆ index (== outside pilots),
D3 ids ⊆ truth, sidecar shard SHA unconditional (file required).
Tests: 40 passing (10 frozen-constant + 13 truth-model + 17 contract).
Round-4 verdicts: numerics APPROVE (no new findings; production-readiness
reconciled: 103 targets, 76 dropout, 33/33 cadence_alt, 20 redilution,
3,102 shards); methods REJECT on three mechanical items — non-finite
sentinels (`inf`) read as "absent" by the isfinite-based checks (now:
absence is NaN exactly, any present value must be finite and in range, with
inf/-inf/NaN tests on positive and control/null rows), the RUNBOOK's D2/D3
commands lacked the now-required arguments (rewritten verbatim: generation
with --exposure-stars and the mandatory arm list, stratified pilot via
--stars-file pilot_shard_index.txt, full run, metrics with --run-manifest/
--shards-dir/--shard-index; D3 runner commands carry --shard-index), and
stale doc lines (spec output list gains d2_scenario_contrasts.csv; runbook
test count 40). Frozen document SHA-256 after those doc edits:

- generalization/METRICS_SPEC.md
  b59ec7e44f310e8bb945d219c07b0c6fd5abf2ad4bbe9d067da38cd83b156cf2
- generalization/GENERALIZATION_PLAN.md
  6b28b634f0abb96230c49eeb98463d6ba8c7c406b6dbddae54894d65f1f09ae6

Round-5 methods verdict (generalization/reviews/G3/sol_methods_r5.md):
APPROVE-WITH-CHANGES — no BLOCKING or MAJOR issue remains; two documentation-
only MINORs (runbook CLI-identity status line; duplicate spec output entry),
both applied. Numerics: APPROVE (sol_numerics_r4.md). The reviewer states
that the production D2 generation may be built and the stratified pilot run
on the attested laptop.

## RATIFIED 2026-08-30: Amendments 2 and 3

Final frozen document SHA-256 (working tree == this ledger):

- generalization/METRICS_SPEC.md
  c827ed9e7dd4068babff12a5cf26f2ebe480d813e7cf115f015f96d7332b3a3e
- generalization/GENERALIZATION_PLAN.md
  6b28b634f0abb96230c49eeb98463d6ba8c7c406b6dbddae54894d65f1f09ae6

Any change to either document after the first campaign L-S run (the D2
stratified pilot on generation gen1 is a PILOT, never confirmatory; the first
confirmatory run is the D2 full matrix or the D3 full run) voids the
prespecification. Review history for G3: rounds 1–5 (numerics: REJECT,
A-w-C, A-w-C, APPROVE; methods: REJECT ×4, A-w-C), ~30 distinct findings
dispositioned; verdict files under generalization/reviews/G3/.

## AMENDMENT 4 — 2026-08-30 (post-pilot D2 window stratification, recovery estimand, metric corrections)

Trigger: the gen1 stratified pilot (generalization/results/2026-08-30_d2_pilot/,
non-confirmatory, enters no estimate). G4 verdicts: stats and methods both
PROCEED-WITH-AMENDMENT-4 (generalization/reviews/G4/sol_stats.md,
sol_methods.md). Changes, all prespecified BEFORE any confirmatory-era run:
(1) window strata K = 0/1/2 on W_g = Σ max(n_zg,night − 1, 0) (pool 10/50/90 =
6/58/452; strictly distinct for 103/103 targets; production refuses
violations; frozen surface edges (15, 41, 84, 217)); gen1 → gen2;
(2) PRIMARY P4 = injected-signal recovery (confirmed AND dominant-mode direct
match); detection-only = secondary trigger rate; (3) paired controls scored
against the partner's injected truth (2×2, yields, paired differences,
P(R_B=1,R_C=0), quiet-control-conditioned secondary, reuse table); (4) target-
level D2 surfaces, target-level chance-match derangements (10,000), CP
discordance bound for degenerate paired contrasts, descriptive row-level D2
tables, `prespecified_primary`/`confirmatory_decision` flags; (5) provenance:
raw results + sidecars archived with pilots, `stars_file_sha256` + exact
id-set equality, argv/timestamps/git state in run manifests.
Code: d2_truth_model.py (W_g column, WG_SURFACE_EDGES, check_wg_strata),
build_d2_shards.py, metrics_generalization.py (recovery endpoint,
d2_surfaces, d2_chance_match, d2_paired_controls, verify_stars_file),
run_generalization_ls.py; tests 46/46; D1 regression unchanged.

Frozen document SHA-256 after Amendment 4:

- generalization/METRICS_SPEC.md
  66013732a585c4a612376704e3c1e9af2ba81919e30eb9c1967e0ec4bfc02eca
- generalization/GENERALIZATION_PLAN.md
  e2cd36af2cbb4bc11537b3f7e90c1b722bb8b0c611d3e887879c7105b10ddc65

G4 round-2 verdicts: stats APPROVE-WITH-CHANGES (chance-match denominator
must keep non-detections; nested D2 contingency intervals; exact sensitivity
endpoints), methods APPROVE-WITH-CHANGES (same interval suppression incl.
sensitivity; pair usability on BOTH sides + quiet subset on pair_usable;
unresolved controls recorded not skipped; scorer re-runs the W_g strata guard
and the control-resolution guard; sidecar SHAs bound into inputs_sha256 and a
`provenance_sha256` column in completion.csv; both-machine test logs archived;
git_tracked_dirty + untracked count; wording). All applied in the round-3
commit (51 tests; D1 unchanged). The builder docstring's stale
"exposures-per-night" wording is deliberately left until the next deliberate
regeneration (editing build_d2_shards.py changes the generation-code SHA and
would orphan gen2). Plan/spec bytes are unchanged since the SHAs above.
G4 round-3 verdicts: stats APPROVE (no findings; runtime probes: chance-
match denominator 0 under derangement / exactly 1/3 self-match, nested
intervals null, exact endpoints), methods APPROVE (no findings; builder-
docstring deferral accepted as non-gating; remaining items operational).

## RATIFIED 2026-08-30: Amendment 4 (G4 closure)

Operational gates before the FULL D2 run (from sol_methods_r3.md): gen2 pilot
finishes with zero unexplained failures; laptop pulled only after the pilot;
amended metrics pass every guard (W_g, selection SHA, control resolution,
completion/sidecar, env/attestation, generation, platform boundary); pilot
record archived with raw JSONs, sidecars, run manifest, completion table,
metrics, both-machine 51-test logs and an archive-wide SHA256SUMS; the full
run launched from the reviewed attested laptop checkout without --stars-file
after inspecting git_tracked_dirty / git_untracked_count. The builder
docstring stays untouched until a deliberate regeneration. Amendment 4 is
disclosed as pilot-informed; no further estimand-hierarchy change is
permitted after it. Frozen document SHAs: unchanged from the Amendment-4
entry above.

## 2026-08-31: Post-launch descriptive admission — D3 diurnal-band partition

Trigger: the non-confirmatory 150-star D3 timing pilot showed the raw
negative-class (dsct_flag0) rule-1 triggers concentrated near 1.00/2.00 c/d
(solar-diurnal alias family; the frozen veto's ANALYTIC locus test covers
only k·f_sid within ±1.5/T — about one-fifth of the solar–sidereal
separation — while its family-agnostic local window-power test fires only
above threshold 0.1; see writing/brief_diurnal/BRIEF.md). Adjudicated BEFORE any full-campaign D3 metric was computed
(prompt: reviews/G5prep/PROMPT_diurnal.md; verdict:
reviews/G5prep/sol_diurnal.md). Verdict: ADMIT-AS-DESCRIPTIVE.

Terms (binding): P3 unchanged — rule 1, best pass, all 2,314 dsct_flag0
members, frozen Wilson interval. The addition is a post-launch arithmetic
partition of P3's observed numerator ONLY: within_solar_diurnal_band iff
f < 4 / d and min_{k in 1..3} |f - k * 1.000000 / d| <= 0.020000 / d
(closed endpoints; bands [0.980,1.020], [1.980,2.020], [2.980,3.020] / d);
abort rather than classify silently if any confirmed negative lacks a
finite best-pass frequency. No low-frequency-floor term. No confidence
intervals, tests, acceptance thresholds, or weighting; the outside-band
component is never called a "corrected" or "de-aliased" P3; the
decomposition is never applied to the census trigger rate and never used
to veto, exclude, or reclassify any trigger. Output segregated at
<results>/descriptive_postlaunch/d3_trigger_decomposition.csv with
analysis_status=postlaunch_pilot_informed_descriptive, prespecified=false,
interval=none; the verdict's verbatim disclosure sentence ships beside it.
fp_frequency_distribution.csv remains the prespecified frequency audit.

Amendment 4's prohibition on further estimand-hierarchy changes is
untouched: GENERALIZATION_PLAN.md / METRICS_SPEC.md bytes unchanged (SHAs
as in the Amendment-4 entry). Code lives at
scripts/generalization/descriptive/d3_trigger_decomposition.py —
deliberately OUTSIDE the campaign_file_shas() glob surface
(scripts/generalization/*.py, non-recursive), so pulling this commit on
the laptop is SHA-neutral for the live D3/D2 runners' drift guards.

## 2026-09-01: G5prep round 2 — pre-metrics ruling on the methods-panel findings

Trigger: a fresh five-persona methods panel (writing/methods_review/, 39
findings, 0 critical) on the frozen plan/spec; load-bearing facts verified
against the roster/Mo tables/metrics code before adjudication (prompt:
reviews/G5prep/PROMPT_round2.md; ruling: reviews/G5prep/sol_round2.md; fixed
2026-09-01 ~15:40 EDT, before any full-campaign D3/D2 metric existed).

Rulings (binding): item 1 F07 = COMPLIANCE — METRICS_SPEC-mandated D3
attrition table (class × amp × Mo-join × g≤14 × period × Teff × cone-count ×
separation; cumulative stages roster→fetched→crossmatched→QC→both-passes),
`d3_mo_join_covariates.csv`, and the `== 456` frequency-scorable guard are
implemented in metrics_generalization.py post-launch; magnitude strata use
`gmag <= 14.0` as the spec says (roster's legacy `< 14.0` flag ignored, roster
untouched); the automatic pre-fix laptop metrics are archived uninterpreted,
then metrics are re-run on the Mac with the guard: byte identity of every
pre-existing science output except attrition.csv; expected-only diffs in
attrition/manifest/path-keyed provenance; identical input-content SHAs; 456/154
counts. Items 2–10 = ADMIT-DESCRIPTIVE (segregated under
`<result>/descriptive_postlaunch/`, analysis_status=postlaunch_descriptive,
prespecified=false, interval=none): fR/Nyquist-reflection rescoring of the 40
aliased-dominant targets + P2 by dominant-frequency regime (<4/4–24/≥24 c/d);
confirmed-positive match-class × any-top-peak partition (610 denominator);
per-pass rows beside P4 (presentation only); D2 K × template-status, control
reuse figure, paired A/B table; negative trigger strata (g≤14, Teff cuts
6597/6737/7092.5 K, merged oids ≤1/2/3–4/≥5, pass, fixed 4×4 RA/Dec grid) +
covariates by class; D3-vs-pool coverage + a95 by class/pass/band;
dominant-only confirmed-conditioned 10,000-derangement chance rate
(PCG64(20260829)); D1-vs-D3 confirmed-frequency histogram (fixed edges) +
yearly-alias/Kepler-reflection predicates in a separate file; dated
prespecification-exposure table + the reconciliation sentence. REFUSED:
applying the solar-diurnal band rule to confirmed positives. Disclosure
register (F06, F12, F13, F19, F20, F22–F31, F35, F36, F39): disclosure-only.
No endpoint, denominator, matching rule, interval, or hierarchy changes.
GENERALIZATION_PLAN.md / METRICS_SPEC.md bytes unchanged.

Round-2 implementation verified 2026-09-01 (independent fresh-context
verifier, reviews/G5prep/VERIFIER_round2_code.md): CONDITIONAL PASS — every
ruled definition conforms and was re-derived on the real roster/Mo/crossmatch
files. Three defects fixed before any real D3 metric: (1) compare_metrics_runs
canonicalisation of Windows-backslash input keys (would have produced a false
GUARD FAIL); (2) separation-bin labels now the ruled strings verbatim
(boundaries were already exact); (3) the laptop run manifest's Windows-relative
attestation path is made to resolve on the Mac by a literal-name symlink
(RUNBOOK step 6), never by editing the metrics loader. Defensible choices
recorded: `freq_scorable` asserted identical to the Mo-joined set rather than
re-set (preserves per_star.csv byte identity); `wg_stratum` = fixed K labels
wg_p10/p50/p90; per-module README/manifest sidecars in the shared
descriptive_postlaunch/ directory; rescoring file = the 40 aliased-dominant
rows only; extra-relations file = one row per per_star row; a95 n_missing =
n_roster − n_finite. Provenance correction: the ruled separation cuts
(0.054159657268769895 / 0.0972924425684607 / 0.15375607598589985) reproduce
from the 2,955 finite-separation crossmatch rows, not the 2,901
crossmatched==True rows named in the ruling's parenthetical; the constants
themselves are used verbatim. Tests: 141.

D3 FULL run landed 2026-09-02 01:28 UTC-4 (2,901/2,901, 0 failures; laptop
frozen metrics rc=0, provenance_verified 2,901). Ruled guard executed on the
real pair (laptop pre-fix `d3_metrics` vs Mac post-fix `d3_metrics_mac`):
GUARD PASS — 13 science outputs identical after newline normalisation (the
laptop writes CRLF, and write_text(to_csv(...)) yields CR CR LF; the replay
gate's `identical_newline` tier), 0 differ; attrition.csv == candidate
attrition_summary.csv; manifest differs only in campaign_sha256/env/
input-count fields; input content SHAs identical after path canonicalisation.
Authoritative D3 metrics = generalization/results/2026-09-02_d3/metrics (Mac);
the laptop pre-fix bundle is archived beside it uninterpreted
(metrics_laptop_prefix/). Guard tool commits 8bc637e, 70bc860.

Disclosure (found on the real D3 bundle, 2026-09-02): for the 154 unjoined
dsct_flag1 positives the frozen metrics' `best_candidate_matches_dominant`
reads `unmatched` rather than `unscored` because the roster dominant frequency
reaches classify_match as a float NaN (not None); `best_candidate_matches_
any_mode` is `unscored` as intended. No estimand reads that cell (the P2
frame excludes unjoined stars; P1/P3 ignore match classes). The frozen
per_star.csv is left byte-identical; the ruled descriptive modules enforce the
ruled `unscored` label for unjoined rows (positive partition records
n_unjoined_relabelled_unscored; frequency audits leave relation cells blank
when the dominant is NaN). Disclosed here and in the disclosure register.
