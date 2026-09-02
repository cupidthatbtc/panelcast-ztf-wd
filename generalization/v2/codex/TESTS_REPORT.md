# v2 test suite — record (2026-09-02)

Brief: PROMPT_tests.md (codex GPT-5.6-sol subagent, workspace-write). The subagent wrote
`tests/test_v2_align.py` (5), `test_v2_detrend.py` (5), `test_v2_multiband.py` (8) and
`test_v2_window.py` (7) before its process was killed at 14:04 by the lead's
`pkill -f analyze_star_v2` (the pattern matched the subagent's own command line, which
carried the brief). Lead fixes to the subagent's tests: a numpy-2 `ndarray.ptp()` call, a
zero-error series helper (weights need finite positive errors), and the marginal-signal
FAP window (the intent is "each band alone fails 1e-3", not a fixed 1e-2 band).

Lead-written: `tests/v2_helpers.py` (synthetic two-band shard), `test_v2_rule.py` (6),
`test_v2_schema.py` (8: frozen key sets, 15 top_peaks rows, frozen `overall_result` +
`metrics_generalization.score_star` on a v2 JSON → confirmed/direct, alignment offsets
recovered, byte-identical determinism, load-time rejection, error.json path),
`test_v2_split.py` (5: plan-quoted SHA, parity rule, class balance, runner lists ⊆ half ∩
shard index, nulls 500/500, dev-only subsets/overlap), `test_v2_runner.py` (3: constants
loading, split guard, end-to-end subprocess run → resume reuses all → constants change
recomputes), `test_v2_guard_postfix_reference.py` (2). The metrics subagent wrote
`test_v2_metrics_engine.py` (4).

Result on the Mac (`.venv-gen`): `205 passed in 43.36s` (143 frozen/campaign + 62 v2).
