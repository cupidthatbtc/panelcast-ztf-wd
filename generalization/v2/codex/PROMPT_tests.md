# Task: write the pytest suite for the v2 detector arm (tests/test_v2_*.py)

You are working in the git repository at /Users/jackneo/Documents/vonhippel-base9/astro-wd
(branch generalization/campaign-1). Python: `.venv-gen/bin/python` (3.12, numpy 2.3.5, scipy
1.16.3, astropy 8.0.1, pandas 2.3.3, pytest). Run tests with
`.venv-gen/bin/python -m pytest tests -q`. The existing suite (143 tests) must stay green.

## Context

`scripts/v2/` is a new detector arm ("v2") that reads the same light-curve shards as the frozen
pipeline and writes the same per-star JSON schema. READ these files first, in this order:
`scripts/v2/v2_common.py`, `align.py`, `detrend.py`, `window.py`, `multiband.py`, `rule.py`,
`analyze_star_v2.py`, `run_v2_ls.py`, `make_split.py`, and the pre-registration
`generalization/v2/V2_PLAN.md` (the algorithm, constants and split rules the tests must pin).
Also read `tests/conftest.py` (sys.path pattern; it inserts scripts/generalization and
scripts/generalization/descriptive — your tests must ALSO insert `ROOT/scripts/v2`), and the
frozen helpers `scripts/lomb_scargle_common.py` (prepare_series, window_strength,
exact_power_and_amplitude, baluev_fap) and `scripts/run_catalog_lomb_scargle.py`
(analyze_star JSON schema, overall_result) — v2 must stay schema-compatible with them.
`scripts/generalization/metrics_generalization.py::score_star` is the consumer to satisfy.

Shard format (gzip CSV): columns source_id, band (zg|zr), oid, mjd, bjd_tdb, night_mjd, mag,
magerr, chi, ra, dec. Real D3 shards (if present on this machine; skip such tests otherwise):
`outputs/generalization/d3_sync/d3_panels/exposure_stars/<sid>.csv.gz`, e.g.
9000000000000892667 (T ≈ 2770 d, ~1,800 rows). A full two-pass v2 run on a real D3 star takes
~50 s single-threaded: mark any test that runs BOTH passes on a real shard with
`@pytest.mark.slow` and skip it unless the environment variable V2_SLOW_TESTS=1. Everything
else must be fast (synthetic shards with a 100–300 day baseline and a few hundred points; a
two-pass v2 run on such a shard takes ~1–3 s).

## Rules

- DO NOT modify anything under scripts/ (the v2 modules are owned by the lead; the frozen
  scripts are SHA-pinned and must never change) or under generalization/ except the report
  file below. Only create/modify `tests/test_v2_*.py`.
- If a test reveals a genuine defect in scripts/v2, write the test for the INTENDED behavior
  (per V2_PLAN.md and the module docstrings), mark it `xfail(strict=True, reason=...)`, and
  describe the defect precisely (file, function, reproduction, suggested fix) in
  `generalization/v2/codex/TESTS_REPORT.md`. Do not paper over it.
- Deterministic tests only (seeded RNGs). No network.
- Finish by running the whole suite and putting the final pytest summary line and the list of
  test files you created in TESTS_REPORT.md.

## Required tests (one file per bullet unless noted)

1. `test_v2_align.py`: a synthetic 3-oid band series (one band, or both) with injected offsets
   (e.g. +12 and −20 mmag, oid row counts ≥ 5) → after `align_zero_points` the residual
   per-oid weighted-median offsets relative to the anchor are < 0.5 mmag; an oid with n < 5
   rows is left unaligned (applied False, role "unaligned_too_few_rows") and its rows keep the
   raw mag; a single-oid star is unchanged (mag == mag_raw everywhere, table has one anchor row
   per band); the anchor is the oid with the most rows; `weighted_median` matches a brute-force
   definition on random inputs including ties; a shard with NO oid column is treated as one oid.
2. `test_v2_detrend.py`: `running_weighted_median` — single-exposure nights survive with
   non-zero values (compare against the frozen `prepare_series(high_frequency=True)` which
   zeroes them); a 30-day-period sinusoid (large amplitude) on a ZTF-like cadence is removed by
   the 30 d window to < 10 % of its amplitude... careful: a running MEDIAN over a window equal
   to the sinusoid period removes it only partially; instead test that a slow trend (a 300-day
   linear ramp plus a 60-day sinusoid) is reduced by more than 80 % in RMS, and that a 12 c/d
   sinusoid of amplitude 20 mmag sampled at 2–3 exposures per night is preserved to < 2 %
   amplitude loss (fit the amplitude with `multiband.sinusoid_fit` before/after); the
   fewer-than-5-points fallback uses the 5 nearest-in-time points; input must be time-sorted
   (unsorted raises).
3. `test_v2_window.py`: `window_strength_grid` agrees with the frozen `window_strength` to
   1e-3 absolute at 200 random grid frequencies (synthetic ZTF-like nightly cadence with
   yearly gaps, T ≈ 1000 d, low grid); `fixed_loci` contains the solar, sidereal, lunar
   (1/29.530589), yearly (1/365.25) loci and the k·1.0 ± 1/29.530589 beats;
   `is_window_alias_v2` flags a candidate exactly at 1.00274 c/d, at 2.0 c/d, at 1/29.530589
   and at 1 + 2/365.25 (locus labels start with sidereal_/solar_/lunar_), and does NOT flag
   12.3 c/d on that time set; `is_alias_of_stronger_v2` flags f = f0 + 1.0, f0 + 1.00274,
   f0 − 2.0 (difference family) AND 1.0 − f0, 1.00274 − f0, 2.0 − f0 (mirror family) for
   f0 = 0.0339, and does NOT flag 12.3 vs a stronger 7.1; with the REAL D3 shard
   9000000000000892667 (skip if absent) the low-pass `window_peaks` of the zg times include
   peaks within 2/T of 1.00274 and 2.0055 and the veto flags 1.0027 and 0.0339 but not 12.3.
4. `test_v2_multiband.py`: `sinusoid_fit` recovers amplitude and phase of a noiseless
   sinusoid (phase convention: model = c + A sin(2πft + φ), φ in cycles);
   `wrapped_phase_difference_cycles(0.45, −0.45) == 0.1`; `joint_fit` on a coherent two-band
   injected signal (A_r = 0.8 A_g, same phase, Gaussian noise) gives delta_phase < 0.05 and
   ratio ≈ 0.8, and `is_coherent` True; an incoherent signal (random phase per band, or
   quadrature) is rejected by `is_coherent`; a signal with A_r/A_g = 0.1 is rejected on the
   ratio; the joint (multiband_power) periodogram equals astropy's
   `LombScargleMultiband(t, y, bands, dy).power(freq, method="fast", sb_method="fast",
   assume_regular_frequency=True)` on a small regular grid to 1e-4 (the per-band memmaps are
   float32; build them with the frozen `periodogram_to_memmap` in tmp_path);
   `cluster_candidates` reproduces the frozen `run_lomb_scargle.cluster_candidate_frequencies`
   ordering on a synthetic peak list and honours the cap; a coherent two-band signal whose
   per-band Baluev FAP is ~1e-2 in EACH band (tune the SNR) is present in the joint top-5 (use
   `analyze_star_v2` on a synthetic shard and inspect passes["low"]["v2"]["series_peaks"]
   ["multiband"]) — assert the frequency appears within tol; document the SNR you used.
5. `test_v2_rule.py`: `decide` truth table — no significant band → not_detected; one
   significant band + joint_top5 + coherent → confirmed with basis "coherent+zg"; two
   significant bands but incoherent → candidate with basis "zg+zr" and reason "incoherent";
   significant but not joint top-5 → candidate with reason "not_joint_top5"; aliased band is
   never counted as significant.
6. `test_v2_schema.py`: run `analyze_star_v2` on a synthetic two-band shard (T ≈ 200 d, ~400
   rows, an injected 12.3 c/d coherent signal, two oids per band with an offset, some
   single-exposure nights) with passes ("low", "high") into tmp_path; assert: schema_version
   "v2-1", engine "v2", passes keys {"low","high"}, every frozen pass key present (list them
   from `unavailable_pass_result` plus status/basis/frequency_per_day/... — compare against the
   key set of the frozen `run_catalog_lomb_scargle.analyze_star` output structure documented in
   that file), `top_peaks` has 15 rows with series in {zg, zr, multiband} (5 each, ranks 1–5)
   carrying the frozen row keys; the frozen `overall_result(result)` works;
   `metrics_generalization.score_star(json_path, [12.3], 12.3)` returns
   best_candidate_matches_dominant == "direct" and best_status == "confirmed"; a second run on
   the same shard into a second path is byte-identical (determinism); a corrupt shard (missing
   zr) writes `<sid>.error.json` and raises.
7. `test_v2_split.py`: `generalization/v2/split.csv` — no sid in both halves; the D3 class
   balance per half matches split_manifest.json; the SHA-256 of split.csv equals the value
   quoted in V2_PLAN.md (parse the 64-hex string after "split.csv, SHA-256"); every id in
   d3_dev.txt / d3_holdout.txt is in the matching half and in
   generalization/data/d3/crossmatch_freeze/panels_shard_index.txt; d2_dev.txt/d2_holdout.txt
   contain only nominal-B, ctrl and gauss_null sids of their half; nulls split 500/500;
   D3 dev = even KIC (parse the key column "KIC <n>").
8. `test_v2_runner.py`: `run_v2_ls.load_constants` accepts declared candidates
   ('{"trend_window_days": 10.0, "amp_ratio": [0.5, 1.2]}') and rejects undeclared values;
   `split_half` raises on ids spanning both halves and returns "dev"/"holdout" otherwise;
   an end-to-end subprocess run of `scripts/v2/run_v2_ls.py` on 3 synthetic shards in
   tmp_path (`--allow-nonstandard-ids --shard-index <index> --machine test --workers 2
   --dataset d3-test`) produces stars/<sid>.json + .prov.json, completion.csv (3 complete),
   manifest.json with engine "v2", binding.attestation_sha256 == "v2-unattested",
   binding.v2_digest == v2_common.v2_digest(); a second invocation reuses all results
   (pending 0 in the printed line / progress.json completed_now 0); editing the constants
   (`--constants '{"n_window_peaks": 6}'`) makes the scan recompute all three.

Write clean, well-named tests; keep total added runtime under ~90 s (excluding slow-marked).
