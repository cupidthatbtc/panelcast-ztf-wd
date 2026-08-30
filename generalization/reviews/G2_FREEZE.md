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

Frozen document SHA-256 after Amendment 3:

- generalization/METRICS_SPEC.md
  6986e2fce033369d72efac9b08d257894446c2b71522a1f707587fe6cc6c9365
- generalization/GENERALIZATION_PLAN.md
  1f7153a7f473e6f1300221fafa4a5b40f97165a45202f4dedab4fb5d5640dc73

Tests: 38 passing (10 + 14 + 14). Status: PENDING G3 round-3 verdicts
(numerics + methods); Amendments 2 and 3 are ratified together when both
return APPROVE.
