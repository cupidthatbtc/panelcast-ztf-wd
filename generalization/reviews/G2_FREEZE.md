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
