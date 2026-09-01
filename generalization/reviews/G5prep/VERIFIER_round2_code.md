# VERIFIER — G5prep round-2 implementation audit (code vs ruling)

Independent verification of the code implementing `reviews/G5prep/sol_round2.md`
(binding, fixed 2026-09-01) against that ruling, `METRICS_SPEC.md`,
`reviews/G2_FREEZE.md` (Amendment 4, 2026-08-31, 2026-09-01 entries) and
`reviews/G5prep/sol_diurnal.md`. Read-only audit; no code, test, data or output
was modified. Date: 2026-09-01. Test suite: `141 passed in 13.34s`
(`.venv-gen/bin/python -m pytest tests -q`).

Line references are to the working tree at HEAD `7d52890` (compliance commit
`048a814`, descriptive commits `fc2f17a`, `a93ee24`, `c46c5d2`).

## 0. Ruled facts re-derived on the real inputs

All executed with the repo's own loaders on the frozen files (not the tests).

| Fact (ruling) | Verified value | Source |
|---|---|---|
| Roster 3,000 = 2,314 / 610 / 76 | 3000 = 2314 / 610 / 76 | `roster_d3.csv` |
| Mo-joined `dsct_flag1` == 456 | 456 by `mg.d3_mo_joined`; 456 by `common.mo_joined_kics`; the two KIC sets are identical; `d3_freq_scorable_guard` passes on `truth_d3()` | item 1 / item 2 |
| Unjoined positives = 154 | 154 | attrition `mo_join x class` |
| 10 of 456 dominant frequencies in [24, 24.46848) | 10; 0 at >= 24.46848 | roster `dom_freq_per_day` |
| Teff cuts 6597.0 / 6737.0 / 7092.5 = linear quartiles of pooled finite roster Teff | exactly `[6597.0, 6737.0, 7092.5]` (n = 3000 finite) | roster `Teff` |
| RA cuts 290.0945525 / 293.54213 / 296.340635 | exact | roster `ra` |
| Dec cuts 41.048665 / 43.879275 / 46.70182 | `np.quantile` gives 46.701820000000005 for the third; the ruled constant 46.70182 is used; no star has dec in (46.70182, 46.701820000000005], so no classification differs | roster `dec` |
| All 16 sky cells observed | 16 over the roster and 16 over the 2,314 negatives (smallest negative cell = 72) | `sky_cell` |
| Three negatives at gmag == 14.000 enter `g_le_14` | 3 stars, all `dsct_flag0`, legacy `near_saturation == False`; `g_le_14` count over negatives = 1092 = (g < 14 count 1089) + 3 | roster |
| Separation cuts 0.054159657268769895 / 0.0972924425684607 / 0.15375607598589985 | reproduce EXACTLY as linear quartiles of the 2,955 finite `nearest_separation_arcsec` rows of `panels_crossmatch_qc.csv`; the 2,901 `crossmatched==True` rows give 0.05412 / 0.09710 / 0.15356 instead. The ruling's parenthetical "2,901-row finite crossmatch frame" is therefore mislabelled; the frozen CONSTANTS are what the code uses (see Defensible D1-7) | `panels_crossmatch_qc.csv` |
| 40 aliased-dominant targets (0.1 µHz, C==0) | 40; every target has exactly one qualifying row (tie-break never exercised); 0 NaN `fR`/`Freq` among the 13,463 C==0 rows | `mo2026_table1.csv` |
| Attrition stages monotone on the frozen QC frame | `cache_present` True for 3000/3000; stage-crossmatched 2,955; `crossmatched==True` 2,901; no `qc && !stage`, no `stage && !fetched` | `panels_crossmatch_qc.csv` |
| `n_fetched` = "nonempty cache file, cache_present=true" | `build_panels_generic.py:143` defines `cache_present = exists and st_size > 0`, so the single flag is exactly the ruled condition | builder |
| D1 catalog 928 rows; `blind_status=="confirmed"` all finite-positive | 928; 342 confirmed; 342 finite positive (min 9.8e-4, max 1230.9 d^-1) | `ls_full_catalog.csv` |
| D3 census panel 2,901; pool 928; `wg_contrasts >= 0` | 2901 / 928; 0 negative | `panels_census_generic.csv`, `census_full_catalog.csv` |
| `crossmatch_adjudication.csv` vs `panels_crossmatch_qc.csv` (item 6 uses the former, item 1 the latter) | `selected_ztf_objects`, `ztf_objects_in_cone`, `zg/zr_clean_rows`, `crossmatched`, `cache_present` identical; `nearest_separation_arcsec` differs on 1 row by 4.4e-16 (CSV round-trip; both 2.149036, bin `>=1.0` either way) | both files |
| Descriptive code outside the campaign SHA surface | `frozen_api.campaign_file_shas` globs `scripts/generalization/*.py` non-recursively (`frozen_api.py:117`); `descriptive/` is outside; `metrics_generalization.py` is inside (its SHA change is the expected manifest diff) | `frozen_api.py` |
| End-to-end compliance tables on the real roster (synthetic per_star: every `crossmatched` star `not_detected`, both passes available) | 555 observed cells; partition sums 3000; stages 3000 / 3000 / 2955 / 2901 / 2901; `n_group` 456 / 154; 28 covariate rows; all 16 columns in ruled order | items 1 functions |

## 1. Per-item verdict table

| Item | File(s) | Verdict | Evidence (line refs) |
|---|---|---|---|
| 1 — guard (`mo_joined`, == 456, identity with P2, before any output) | `metrics_generalization.py` | CONFORMS | `d3_mo_joined` 282-298 implements the ruled conjunction (finite table-2 `Freq`; finite `Amp` row; roster `dom_freq_per_day` finite and > 0; `amp_mmag` finite; `class_label == dsct_flag1`). `d3_freq_scorable_guard` 301-312 asserts count == 456 AND set identity with `truth["freq_scorable"]` (the column P2 consumes at 695/722/766/1046/1161). Called at 1549-1553 immediately after `truth_d3()`, before `inputs`, `per_star`, or any file write (first write is 1738-1740). `freq_scorable` is not overwritten — see Defensible D1-1. |
| 1 — `attrition.csv` columns / bins / stages | `metrics_generalization.py` | CONFORMS (one label deviation, Defect 2) | Columns 247-250 = ruled list, in order. Amplitude edges/labels 232-233 verbatim; period edges 234-235 (0.05 d = 4320 s etc.) and labels 236-238 verbatim; Teff cuts 230 and labels 239 verbatim; cone edges (4,7,10) 241 with labels `0-3/4-6/7-9/>=10` (ASCII hyphen; D1-3); separation cuts 231 verbatim but labels 240 ABBREVIATED (Defect 2). `_left_closed_bin` 271-279 is left-closed/right-open with NaN -> `*_unknown` (tests 33-51 pin every edge). Magnitude 356-357 `gmag <= 14.0` -> `g_le_14`, legacy flag ignored. Negative finite amplitude aborts 347-348. Stages 330-339: fetched = `cache_present`; crossmatched = `read_status=="ok" & finite sep & selected>=1`; qc = frozen `crossmatched`; both = result present & `low_available` & `high_available` via `_strict_true` (never `bool(NaN)`). Per-star monotonicity abort 340-344; per-cell monotonicity 385-388; partition identity 389-390. "Every observed Cartesian cell": `groupby(keys, sort=True)` 381. Status fields 227-228 `prespecified_compliance / True / none`. |
| 1 — `d3_mo_join_covariates.csv` | `metrics_generalization.py` | CONFORMS | Restricted to 610 positives with abort 397-399; columns 251-253 in ruled order; covariate list 243-246 = ruled 14 in order; `sd` = `std(ddof=0)` 412; `np.quantile` default linear 411; booleans cast to float so means are fractions 404; NaN cells when nothing finite 406-408; no test / standardized difference anywhere. |
| 1 — `attrition_summary.csv` | `metrics_generalization.py` | CONFORMS | 1844-1845 preserves the seven-scalar audit verbatim; for d3 `attrition.csv` becomes the mandated table 1846-1852; d1/d2 unchanged 1853-1855. |
| 1 — no pre-existing science output can change | `metrics_generalization.py` (diff of `048a814`) | CONFORMS | Diff is (a) constants + 8 new functions inserted between `truth_d1` and `truth_d3`; (b) `truth_d3` refactor moving its two `read_csv` calls into `_d3_sources()` with identical arguments/dtypes (mutation `mo["freq_per_day"]` acts on a fresh frame; `main()` calls `_d3_sources()` again for a separate frame); (c) three lines after `truth_d3()` that read `truth` (`.astype(bool)` copies) and can only raise; (d) the tail after `manifest.json`/`inputs_sha256.json` are written. Every producer of `per_star.csv`, completeness, contingency, trigger rates, PPV, surfaces, chance, FP audit, sensitivity (1739-1809) is untouched and receives no new input; `qc_frame` was already loaded pre-patch (1800) and is used read-only; `_d3_stage_frame` reads `per_star` via `set_index` (new frame). `inputs` dict unchanged. Hence byte identity of every pre-existing science output is structural, consistent with the D1 GUARD PASS in the commit message. Legacy `near_saturation` sensitivity rows 1464-1466 are deliberately left (byte identity; F22 disclosure). |
| 1 — guard tool | `descriptive/compare_metrics_runs.py` | DEVIATES (Defect 1) | Items 1-3 of the ruled guard are implemented (byte identity 44-48; `attrition.csv` == `attrition_summary.csv` 50-55; manifest keys 57-64; canonicalised inputs 66-72; expected-new set 25). BUT `canon()` 67-70 uses `Path(k).name`, which on macOS does not split Windows backslashes; the real laptop `inputs_sha256.json` (gen2 pilot: 3,386 of 3,395 keys contain `\`) therefore yields a false GUARD FAIL. Reproduced: `compare()` with keys `C:\lap\run\stars\1.json` vs `/mac/run/stars/1.json` returns `inputs_sha256.json content SHAs differ after path canonicalisation`. The unit test (`test_compare_metrics_runs.py:30`) uses forward-slash `C:/lap/...` keys and so masks it. Guard item 4 (456/154, additivity) is enforced in-program (301-312, 389-390, 397-399) rather than by the tool — acceptable, see R-3. |
| 2 — aliased-dominant + fR rescoring | `descriptive/d3_truth_provenance.py`, `d3_descriptive_common.py` | CONFORMS | C==0 rows via `table1_c0` (common 220-229); `abs(Freq - dom_freq_uhz) <= 0.1` 127-128 with `TABLE1_MATCH_TOL_UHZ = 0.1` (71); tie-break `sort_values(["abs_diff_uhz","fR"], mergesort)` 132; exactly-40 abort 198-202 and 363-367. `uhz_to_per_day = x*86400.0/1e6` (common 63-64) = the frozen loader's expression (`metrics_generalization.py:424`). Frozen taxonomy via imported `classify_match` 229 against the single fR frequency; `tol = 1.5/baseline` (common 138-143). `f_Nyq = 24.46848` (common 59; `283.2*86400/1e6 == 24.46848` asserted in tests); reflection `2*24.46848 - fR_per_day` 220, boolean requires `reflection > 0` 230, never alters the taxonomy. Union = finite table-2 freqs ∪ finite C==0 fR 221-224; `best_candidate_matches_any_mode_plus_fR` 231; `any_top_peak_...` = any stored top-15 peak (both passes, as the frozen scorer) `direct` 237-240. Columns 85-91 = ruled order. Top-peak JSONs are SHA-bound to the bundle's `inputs_sha256.json` 158-189 (handles backslash keys 149). |
| 2 — P2 regime split | `d3_truth_provenance.py` | CONFORMS | `p2_frame` (common 291-315) = dsct_flag1 & `freq_scorable` (asserted 456) & usable (`best_status != missing` & both `*_available`) & `eligible_any_pass` — the same predicate as `completeness_tables` 682-698. Regimes 73-77 `[-inf,4) [4,24) [24,inf)`, half-open 269; success = confirmed & dominant `direct` 265-266; `>=24` counts-only (rate NaN) 78, 273; columns 92-96 ruled order; runtime identity with the frozen P2 row 285-304 (n and k/n). Wording "stars with a confirmed super-Nyquist mode" and "largest-amplitude ... need not be a p mode" in README 402-409; disclosure 98-107 verbatim. |
| 3 — confirmed-positive partition; diurnal REFUSED | `descriptive/d3_positive_partition.py` | CONFORMS | Frame = 610 positives (asserted) with `best_status == confirmed` 85-86; 6 × 2 = 12 cells always emitted 111-123; columns 61-65 ruled order; `n_positive = 610` 117; unjoined confirmed stay `unscored` (consistency abort 103-108); rate/share identities 125-131; share blank at zero denominator 121-122; P1 reproduction guard 135-150. No `within_solar_diurnal_band` column exists (tests assert absence; README carries the refusal text 74-79). |
| 4 — pass rows beside P4 (presentation only) | none | CONFORMS (by absence) | `grep` finds no code computing or writing "descriptive window-row recovery"; no new results CSV, as ruled. |
| 5 — D2 K × template status | `descriptive/d2_descriptives.py` | CONFORMS | Nominal arm B only 258; grid K{0,1,2} × {not_detected,candidate,confirmed} × {recovery,trigger} = 18 rows always 270-289; trigger = confirmed 236; recovery = trigger & `direct` 247; scheduled denominator = manifest rows, unscored shard = failure 231-235; `n_usable` = result & both passes 235, context only, no usable-rate column; rate blank at zero 283; columns 106-111 ruled order; per-star rows bound to the manifest on arm/scenario/tic/K/status/W_g/shard SHA 214-225. |
| 5 — control reuse figure | `d2_descriptives.py` | CONFORMS | From the existing `d2_control_reuse.csv` 461-464; one bar per unique control 318-319; sort desc `n_b_assignments` then `control_campaign_id` 334-335; assignment count plotted 344-346, `n_targets` carried in the source table 114-118; files `d2_control_reuse.png/_source.csv/.meta.json` 474-496; meta carries status fields + source CSV 482-496; optional recount against the manifest 324-333. |
| 5 — paired A/B table | `d2_descriptives.py` | CONFORMS | Exactly one nominal A and one B per (tic,K) 387-392; template source / W_g / status equality asserted 394-397; columns 119-124 ruled order; `D` = confirmed, `R` = confirmed & direct 236, 247; pair classes `both/A_only/B_only/neither`, blank when `pair_usable=false` 410-411; no aggregate, contrast, test or interval (tests 260-261). |
| 6 — negative trigger strata | `descriptive/d3_strata_covariates.py` | CONFORMS | Frame = 2,314 negatives with sid-set identity to the roster 197-213; missing/candidate = non-trigger 243-246; magnitude `<= 14.0` 152-156; Teff `bisect_right` at (6597, 6737, 7092.5) 159-163 (left-closed); merged oids `oid_le_1/oid_2/oid_3_4/oid_ge_5/oid_unknown` 166-176 from `selected_ztf_objects` (D6-1); sky 4×4 with the ruled RA/Dec cuts 71-72, half-open via `bisect_right` 179-187, ids `RAq{i}_DECq{j}` + `sky_unknown` 100-102; pass rows `low_status`/`high_status` each over 2,314 291-292; every cell emitted incl. zeros 275-281 with per-stratifier sum identities 282-286; columns 104-108 ruled order; label "high-pass negative-class rule-1 trigger rate" 86, no "sub-hour false-trigger proxy" text; disclosure 87-94 verbatim. |
| 6 — covariates by class | `d3_strata_covariates.py` | CONFORMS | 3,000 rows asserted 320-321; class levels 0/1/2 asserted 324-326; long format, columns 109-113 ruled order; covariates 114-119 = ruled 9 in order; `ddof=0`, `method="linear"` 308-311; no tests. |
| 7 — coverage comparison | `descriptive/d3_coverage_a95.py` | CONFORMS | Frames `D3_crossmatched` (2,901 asserted) and `development_pool` (928 asserted) 61-62, 80-81, 148-151; metrics 82-83; `wg_contrasts = zg_n_exp - zg_n_nights` with nonnegativity abort 161-167; linear quantiles 174; columns 85-89 ruled order; frames never pooled. |
| 7 — a95 by class/pass/band | `d3_coverage_a95.py` | CONFORMS | Reads per-star JSONs directly 200-233; `passes[pass][band+"_a95_mmag"]` 224-230 with fail-closed schema checks; class × pass × band = 12 rows 281-309; no pooling across bands; columns 92-96 ruled order; stars-dir bound to the bundle by presence ⟺ `best_status != missing` and per-pass availability agreement 236-265. |
| 8 — dominant-only chance match | `descriptive/d3_chance_dominant.py` | CONFORMS | Frame = P2 frame & confirmed & finite best and dominant 82-106; candidate frequencies and per-star tolerances fixed (row index i keeps `f_i`, `tol_i`) 109-120, 140; hit = imported `classify_match(f_i, [dominant_j], tol_i) == "direct"` (so `ambiguous` is not a hit) 119; star-level permutation, fixed points rejected 135-139; exactly 10,000 accepted 59, 132-141; `np.random.Generator(np.random.PCG64(20260829))` 60, 130; denominator n per derangement 140; mean/median/q95 155-157; columns 67-71 ruled order; refuses to run before `chance_match.json` exists 173-178. |
| 9 — D1 vs D3 histogram | `descriptive/d3_frequency_audits.py` | CONFORMS | Edges 72-77 = ruled list (34 edges, `inf` last; test 49-50 byte-compares); D1 `blind_status=="confirmed"` from the 928-row catalog 126-137; D3 `dsct_flag0 & confirmed` 140-145; abort on non-finite/non-positive 115-123; left-closed/right-open with 1440 in the overflow bin (`searchsorted(side="right")-1`, common 146-158; test 56-62 pins 1440 -> bin 32); per-dataset normalisation 165; `density = share/width` finite bins only 166-167; columns 91-95 ruled order; files `.csv/.png/.meta.json` 84-86 with status fields in the meta 340-354. |
| 9 — extra relation columns | `d3_frequency_audits.py` | CONFORMS | Separate file 87, never written into `per_star.csv` (test 255); `delta_year = 1/365.25` (common 66, == 0.0027378507871321013 asserted), `f_Nyq = 24.46848`, `tol = 1.5/baseline`; `yearly_alias` 212-216 both signs with `abs()`; `kepler_nyquist_reflection` 219-221 requires `f_ref > 0`; evaluated for the dominant and separately for every table-2 mode 268-276; harmonics/sidereal not folded in; frozen classes copied unchanged 266-267 with consistency aborts 249-261; columns 96-102 ruled order. |
| 10 — exposure table | `writing/methods_review/PRESPECIFICATION_EXPOSURE.csv` | CONFORMS (documentation gap R-5) | Columns exactly as ruled; the five required rows present with the ruled content, plus a sixth 2026-09-01 row; status fields `postlaunch_descriptive,false,none`. The ruled reconciliation sentence ("Read literally, the METRICS_SPEC header ...") exists only in `sol_round2.md`; it is not yet placed in the disclosure register / methods-review text. |
| Preamble (all descriptive CSVs) | `d3_descriptive_common.py`, each module | CONFORMS | `analysis_status=postlaunch_descriptive, prespecified=false, interval=none` (common 44-52; d2 77-80; strata 82-84; coverage 68-70); outputs under `descriptive_postlaunch/`; pilot bundles refused (common 173-174; strata 366-367; coverage 320-321; d2 447-449 with the dev-only exception D5-2); `grep` finds no Wilson/bootstrap/scipy/test machinery in any descriptive module and no write into the metrics bundle. |

## 2. DEFECTS (must-fix before real data)

1. **`compare_metrics_runs.py` canonicalisation fails on real laptop paths (false GUARD FAIL).**
   `canon()` (lines 67-70) uses `Path(k).name`; on macOS a key such as
   `C:\Users\...\d3_run\stars\9000000000001570023.json` is one path component,
   so the reference Counter is keyed by full Windows paths while the candidate
   is keyed by basenames. The archived laptop bundle
   `results/2026-08-30_d2_pilot_gen2/metrics/inputs_sha256.json` has 3,386 of
   3,395 keys with backslashes; a D3 laptop bundle will too. Reproduced with
   `compare()` -> `['inputs_sha256.json content SHAs differ after path canonicalisation']`.
   The unit test masks this by using forward-slash `C:/lap/...` keys.
   **Remedy:** in `canon()` replace the key transform with
   `k if k.startswith("generation_input:") else k.replace("\\", "/").rsplit("/", 1)[-1]`
   (the same normalisation `d3_truth_provenance.json_sha_map` line 149 already
   uses), and change `tests/test_compare_metrics_runs.py:30` to use real
   backslash keys (e.g. `r"C:\lap\run\stars\1.json"`). Without this the ruled
   guard cannot print GUARD PASS on the real rerun and there will be pressure
   to "interpret" the failure.

2. **Separation bin labels deviate from the ruled strings.**
   `D3_SEP_LABELS` (line 240) emits `<0.0542`, `[0.0542,0.0973)`,
   `[0.0973,0.1538)`, `[0.1538,1.0)`, `>=1.0`; the ruling names the bins
   `<0.054159657268769895`, `[0.054159657268769895,0.0972924425684607)`,
   `[0.0972924425684607,0.15375607598589985)`, `[0.15375607598589985,1.0)`,
   `>=1.0` in the same code-font convention whose amplitude, period and Teff
   labels the code reproduces verbatim. The BOUNDARIES are exact (line 231);
   only the label text is rounded. Cosmetic, but this is a
   `prespecified_compliance` output and the rounding is undisclosed.
   **Remedy:** set `D3_SEP_LABELS` to the five ruled strings verbatim (and the
   unknown label stays `sep_unknown`); update `tests/test_d3_compliance_tables.py:47-48,87`
   accordingly. If the abbreviation is kept instead, record the exact mapping
   in the G2_FREEZE ledger entry for item 1.

3. **Operational blocker for the ruled Mac rerun (pre-existing code, not the patch): the laptop run manifest's `replay_attestation.path` does not resolve on the Mac.**
   `run_generalization_ls.py:391` stores `str(args.replay_report)`; on the
   laptop that is a Windows-style relative path (gen2 manifest:
   `outputs\generalization\replay_gate_full\replay_report.json`).
   `metrics_generalization.py:1520-1522` does `Path(path).exists()` and aborts
   ("run manifest's replay attestation not found") — verified `False` on this
   Mac. No d2/d3 metrics bundle has ever been produced on the Mac from a
   laptop run manifest (all archived bundles report `env.machine = Jacks_7i_5090`),
   so the ruled "patch and rerun metrics on the Mac" step has never been
   exercised end to end. **Remedy (do NOT edit `metrics_generalization.py`;
   that would widen the source diff beyond compliance-output construction and
   guards, guard item 4):** before the rerun, make the literal path resolve
   from the Mac invocation directory, e.g. from the repo root
   `ln -s "$PWD/generalization/attestation/laptop_replay_full_2026-08-29/replay_report.json" 'outputs\generalization\replay_gate_full\replay_report.json'`
   (a single filename containing backslashes), after confirming
   `shasum -a 256` of that file equals the D3 run manifest's recorded
   attestation SHA (the archived file's SHA `64e1937a8d45...` equals the gen2
   manifest's `replay_attestation.sha256`; every `.prov.json` sidecar is also
   checked against it at 1674-1675). Record the step in RUNBOOK step 6.

No defect was found that could alter a frozen science output, an endpoint, a
denominator, a matching rule, or an interval; no descriptive module computes an
interval or a test; no descriptive module writes into the metrics bundle;
`per_star.csv` is never modified; the positive-class diurnal column is absent.

## 3. Recommendations (should-fix; not blocking)

- R-1 `metrics_generalization.py:1847-1848`: the d3 `--crossmatch-qc` requirement is checked after `per_star.csv`, every science output, `manifest.json` and `inputs_sha256.json` are written; a missing flag leaves a bundle without `attrition.csv`/`d3_mo_join_covariates.csv` that could be mistaken for complete. Move the check next to the `--run-manifest`/`--shards-dir` argument validation (1513-1546). (Allowed by guard item 4: it is a guard.)
- R-2 `_d3_stage_frame` 330, 333 read `cache_present`/`crossmatched` with `bool(...)`, which would misread a string `"False"`; the frozen frames are bool-typed so it is inert today, but `_strict_true` (263-268) exists for exactly this and should be used for both.
- R-3 `compare_metrics_runs.py`: add guard item 4 to the tool (candidate `attrition.csv`: `n_roster` sums to 3000, per-cell monotonicity, `mo_joined`/`mo_unjoined` positive totals 456/154; candidate `d3_mo_join_covariates.csv`: `n_group` 456/154) so the ruled four-part guard is a single GUARD PASS line, and note in the docstring that item 4's source-diff review is manual.
- R-4 `d3_coverage_a95.py`: bind the per-star JSONs to the bundle's `inputs_sha256.json` SHAs (as `d3_truth_provenance.json_sha_map`/`load_top_peaks` do) instead of presence/availability agreement only.
- R-5 Item 10: place the ruled reconciliation sentence verbatim beside `PRESPECIFICATION_EXPOSURE.csv` (methods_review or `briefs/DISCLOSURE_REGISTER.md` F05 row); it currently exists only inside the ruling file.
- R-6 Item 1, pilot bundles: the compliance tables are also emitted for pilot metrics runs with `n_roster = 3000` while `per_star` holds only the pilot subset (so `n_both_passes` is tiny); the manifest's `pilot=true` disambiguates, but a one-line note in the RUNBOOK would prevent misreading an archived pilot `attrition.csv`.

## 4. DEFENSIBLE choices to record in the ledger

Item 1 (`metrics_generalization.py`)
- D1-1 `freq_scorable` is NOT re-set from the `mo_joined` conjunction; the conjunction is computed separately and set identity with the frozen `truth_d3()` column is asserted (301-312). This satisfies "set from that conjunction" in effect while preserving byte identity of `per_star.csv`; a silent re-set could have changed P2's frame without tripping the guard.
- D1-2 "a finite table-2 maximum-amplitude row" is implemented as "the KIC has at least one finite `Amp` row" (288-289, 295) in the metrics program and as "the argmax-`Amp` row has finite `Freq`" in `d3_descriptive_common.mo_joined_kics` (254-256). Both give 456 and the identical KIC set on the frozen tables.
- D1-3 Cone-count labels use ASCII hyphens (`0-3`, `4-6`, `7-9`) for the ruling's en-dash `0–3` etc. (CSV hygiene).
- D1-4 `mo_join_status` is `mo_unjoined` for every `dsct_flag0`/`dsct_flag2` row (the conjunction requires `dsct_flag1`).
- D1-5 `attrition_summary.csv` is written for d1/d2 too (where it duplicates the unchanged scalar `attrition.csv`).
- D1-6 `--crossmatch-qc` is now mandatory for d3 (was optional); RUNBOOK step 6 updated.
- D1-7 Separation cut provenance: the ruled constants reproduce from the 2,955 finite-separation rows of `panels_crossmatch_qc.csv`, not from the 2,901 `crossmatched==True` rows as the ruling's parenthetical says. The code correctly uses the frozen constants; the ledger should carry the corrected provenance sentence.
- D1-8 The legacy `near_saturation`/`safe_magnitude` rows of `sensitivity.csv` (1464-1466) are left as emitted (byte identity), with F22 as the disclosure; only the new compliance/descriptive strata use `gmag <= 14.0`.
- D1-9 Global monotonicity is implied by per-star (340-344) and per-cell (385-388) checks rather than asserted separately.
- D1-10 `compare_metrics_runs.MANIFEST_MAY_DIFFER` also tolerates `inputs_sha256_count`; harmless because the canonicalised Counter comparison is exact once Defect 1 is fixed.

Item 2 (`d3_truth_provenance.py`, `d3_descriptive_common.py`)
- D2-1 `table1_c0` keeps only C==0 rows with finite `Freq` AND finite `fR` (so a matching row with NaN `fR` would neither qualify nor enter the union); inert on the frozen table (0 NaN among 13,463 C==0 rows).
- D2-2 Targets without a result carry `best_status=missing`, taxonomy cells `unscored`, `tolerance_per_day`/`best_frequency_per_day` blank, `matches_nyquist_reflection` blank (pandas NA) and `any_top_peak_* = False` (the frozen convention).
- D2-3 Default `--stars-dir` is `<metrics-dir>/../run/stars`; every JSON read is SHA-bound to the bundle's `inputs_sha256.json`, and a JSON not among the scored inputs aborts.
- D2-4 Regime rate for the `>=24` row is emitted as a blank cell (counts-only) rather than omitted.
- D2-5 The 456-identity is re-checked from the roster + Mo table 2 inside the descriptive run (307-324), independently of item 1.

Item 3 (`d3_positive_partition.py`)
- D3-1 Consistency aborts beyond the ruling: a confirmed positive whose `any_top_peak_matches_any_mode` is not an explicit boolean, or an unjoined confirmed positive carrying a scored class, aborts rather than being binned.

Item 5 (`d2_descriptives.py`)
- D5-1 `wg_stratum` values are `wg_p10`/`wg_p50`/`wg_p90` for K = 0/1/2 (the ruling lists the column but not its vocabulary; Amendment 4 defines K as the 10/50/90th-percentile positions). Realised W_g per cell is in `wg_min/median/max`.
- D5-2 A pilot bundle is refused unless `--allow-pilot` is given, in which case every output (CSV rows, meta, README, manifest) is stamped `analysis_status=pilot_dev_only`, never the ruled status. Used only to exercise the code on the archived gen2 pilot; must not be used on the production run.
- D5-3 Stricter than ruled: every target must hold exactly K = {0,1,2} nominal pairs (the production schedule guarantees this); `d2_control_reuse.csv` must equal the manifest's nominal-B recount; `wg_min/wg_max` are integer-typed.
- D5-4 A scheduled shard with no `per_star` row is `best_status=missing`, unusable, failure for both endpoints (as ruled); a scored row that disagrees with the manifest on any binding field aborts.

Item 6 (`d3_strata_covariates.py`)
- D6-1 "Merged-oid count" is `selected_ztf_objects` of the frozen crossmatch adjudication frame (`crossmatch_freeze/crossmatch_adjudication.csv`); the same column in `panels_crossmatch_qc.csv` is identical row-for-row. Non-integer counts are binned by `<=1`, `<3`, `<5`.
- D6-2 Dec cut is the ruled decimal 46.70182 (the pooled quantile evaluates to 46.701820000000005); no roster star lies between the two.
- D6-3 Row order: magnitude, teff, merged_oid, pass, sky (the order of the ruling's definitions).

Item 7 (`d3_coverage_a95.py`)
- D7-1 `n_missing = n_roster - n_finite` (every class member lacking a finite a95, whatever the reason: no JSON, pass unavailable, null value); `n_json` and `n_pass_available` are reported beside it.
- D7-2 A JSON whose `passes[pass]` lacks the `<band>_a95_mmag` key aborts (schema deviation is never read as missing data).

Item 8 (`d3_chance_dominant.py`)
- D8-1 Confirmed frame members with a non-finite best or dominant frequency are excluded as ruled and their count is recorded in the manifest (`n_confirmed_nonfinite_excluded`); the unpermuted diagonal rate is recorded in the manifest only, never in the CSV.
- D8-2 Fewer than two frame members aborts (no derangement exists).

Item 9 (`d3_frequency_audits.py`)
- D9-1 `d3_extra_frequency_relations.csv` has one row per `per_star.csv` row (all 3,000, including negatives and `dsct_flag2`); a relation is blank wherever the corresponding frozen match column is `unscored`, and any inconsistency between the frozen columns and the inputs aborts.
- D9-2 The histogram PNG draws density as step outlines on a symlog x axis (linear below 0.25 d^-1) with overflow counts in the legend; the CSV is the source of record.
- D9-3 Any-mode truth lists are the finite table-2 frequencies converted with the frozen expression; verified identical to `truth_d3().truth_freqs` on the real tables (test `test_real_truth_lists_identical_to_frozen_loader`).

Item 10
- D10-1 The exposure CSV carries a sixth row (2026-09-01, G5prep round 2) beyond the five required.

Cross-cutting
- DX-1 All descriptive modules live under `scripts/generalization/descriptive/` (outside the non-recursive `campaign_file_shas()` glob), import `classify_match` from the frozen program rather than re-implementing it, and write module-prefixed README/manifest sidecars so several modules can share one `descriptive_postlaunch/` directory.
- DX-2 The compliance patch changes the campaign SHA surface (`metrics_generalization.py`); the laptop must not pull until its chain completes (commit message), and `manifest.campaign_sha256` differing is the expected diff the guard tolerates.

## 5. Final verdict

VERDICT: CONDITIONAL PASS — every ruled definition (columns, order, bin edges and closedness, frozen constants, denominators 2,314/610/456/P2, status fields, abort-rather-than-guess, pilot refusal, the refused positive-class diurnal column, no intervals/tests, frozen outputs untouched, compliance code structurally unable to alter a pre-existing science output) is implemented as ruled and re-verified on the real roster/Mo/crossmatch files; fix Defects 1-3 (guard-tool backslash canonicalisation, verbatim separation labels, attestation-path resolution for the Mac rerun) before the real D3 metrics rerun.
