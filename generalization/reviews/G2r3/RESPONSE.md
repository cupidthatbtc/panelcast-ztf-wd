# G2 round-3 disposition — 2026-08-28
(Recreated 2026-08-28 late: the original write was aborted by a failed
command chain — the round-4 reviewers correctly flagged it absent; the
content matches the fixes shipped in commits c0a92c3..55da006 range and the
round-3 conformance commit.)

Verdicts: referee3 NOT-FREEZABLE (13R/5P/2U + 6 new), stats3 NOT-FREEZABLE
(prose resolves all 8; code conformance gaps), methods3 NOT-FREEZABLE
(4R/3P). Note: stats3 reviewed code predating the W2-hardening commit
(ppv/fp-dist/sensitivity already existed there).

Fixed in the round-3 conformance commit: taxonomy full enumeration (no elif
short-circuit); surfaces rewritten (detection over ALL positives with
amp_unknown bin; freq endpoint scorable-only; spec edges; D1 excluded);
FPR_Gaussian exact one-sided CP at observed x + acceptance flag; D2 cluster
bootstrap scenario-grouped with common random numbers + CP fallback + D2
McNemar suppression; per-pass primary-match columns; freq scope limited to
L-S rules; usable = both passes; missing = non-detection everywhere; PPV
FPC rescaling; panel gate NaN fail-closed + bound report; 928-star
attestation; campaign-drift checks; stale-shard guards; frozen phase
protocol (phase_draw 0/1/2) + phase/amp-scale variant shards (smoke-tested).

Docs: phase protocol frozen; amplitude-stationarity core; P4 algebra;
template matching total-deterministic; PPV FPC; D3 surface denominator +
MNAR statement; arm-A dual role; D1 surface scope; Teff color surrogate;
balance diagnostics required output.
