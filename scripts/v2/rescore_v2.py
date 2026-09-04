#!/usr/bin/env python3
"""EXACT offline re-application of the v2 decision rule for the three
decision constants (n_window_peaks, phase_tolerance_cycles, amp_ratio) from
the diagnostics recorded in v2 per-star JSONs — no periodogram is recomputed
(V2_PLAN.md §5).

Exactness (G-review 2026-09-02 finding 3): the candidate SET is ordered by
power only (independent of the veto constants); every veto component is
recorded per candidate and re-derived here from first principles —
  window veto  = within tol of a fixed locus (recomputed from window.fixed_loci)
                 OR recorded local window power >= 0.1
                 OR within tol of one of the first N recorded data-driven
                 window peaks (24 recorded per series);
  same-series alias-of-stronger = recorded (independent of N);
  cross-pass alias = any recorded low-pass partner that is UNALIASED under
                 the new N (the low pass is re-scored first);
  joint top-5 after veto = first 5 unaliased of the recorded joint top-15;
  coherence    = recorded delta_phase / amp ratio against the new gates.
Only the trend window needs a rerun (it changes the periodogram).

Output: one CSV row per (constants combination, star): best-pass status /
frequency and per-pass status / frequency — the columns
metrics_generalization.score_star derives — plus baseline_days.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import replace
from pathlib import Path

import pandas as pd

import hashlib  # noqa: E402

from rule import STATUS_ORDER, decide
from v2_common import (
    BANDS, DEFAULT, DEV_RUNS_V2_DIGEST, TUNABLE, WINDOW_POWER_THRESHOLD, V2Constants, overall_result, v2_digest,
)
from window import fixed_loci, fixed_locus_label


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_run_manifest(path: Path, stars_dir: Path) -> dict:
    """The source of an offline re-score must be a completed DEV run at the
    admitted pre-amendment digest (V2_PLAN.md §10, 2026-09-04) whose own
    stars directory is being re-scored: fail closed on anything else."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    binding = manifest.get("binding", {})
    problems = []
    if manifest.get("engine") != "v2":
        problems.append("engine is not v2")
    if binding.get("v2_digest") != DEV_RUNS_V2_DIGEST:
        problems.append(f"v2_digest {str(binding.get('v2_digest'))[:12]} is not the dev-run digest "
                        f"{DEV_RUNS_V2_DIGEST[:12]}")
    if manifest.get("split", {}).get("half") != "dev":
        problems.append("split half is not dev")
    if manifest.get("failures"):
        problems.append("the run has failures")
    if stars_dir.resolve() != (path.parent / "stars").resolve():
        problems.append("--stars-dir is not the manifest's own stars directory")
    if problems:
        raise SystemExit(f"{path}: not an admissible re-score source: {problems}")
    return manifest

SERIES_NAME = {"zg": "zg", "zr": "zr", "joint": "multiband"}
FIXED = [float(locus["frequency_per_day"]) for locus in fixed_loci()]   # listed loci (exposure audit)


def combination_id(constants: V2Constants) -> str:
    """Label of one point of the 2 x 3 x 3 x 3 = 54 candidate grid (V2_PLAN.md
    §3), trend window included."""
    return (f"W{constants.trend_window_days:g}_N{constants.n_window_peaks}"
            f"_phi{constants.phase_tolerance_cycles}"
            f"_r{constants.amp_ratio_min}-{constants.amp_ratio_max}")


def combinations(trend_window_days: float | None = None) -> list[tuple[str, V2Constants]]:
    """The candidate grid in §3 order (window, N, phase, ratio); restricted to
    one trend window when given (the window of the run being re-scored)."""
    windows = TUNABLE["trend_window_days"] if trend_window_days is None else (trend_window_days,)
    combos = []
    for window, n, phase, ratio in itertools.product(windows, TUNABLE["n_window_peaks"],
                                                     TUNABLE["phase_tolerance_cycles"],
                                                     TUNABLE["amp_ratio"]):
        constants = replace(DEFAULT, trend_window_days=float(window), n_window_peaks=n,
                            phase_tolerance_cycles=phase, amp_ratio_min=ratio[0], amp_ratio_max=ratio[1])
        combos.append((combination_id(constants), constants))
    return combos


def window_alias_under(frequency: float, window_power: float, peaks: list[dict],
                       tolerance: float, n_window_peaks: int) -> bool:
    if fixed_locus_label(frequency, tolerance):   # listed loci + comb rule + diurnal band (window.py)
        return True
    if window_power >= WINDOW_POWER_THRESHOLD:
        return True
    return any(abs(frequency - float(peak["frequency_per_day"])) <= tolerance
               for peak in peaks[:n_window_peaks])


def rescore_pass(pass_result: dict, constants: V2Constants,
                 low_alias: dict[tuple[str, float], bool] | None) -> tuple[dict, dict[tuple[str, float], bool]]:
    """Returns (best-candidate summary, {(band, frequency): aliased} for this
    pass's significant candidates — the partner map for later passes)."""
    v2 = pass_result.get("v2")
    alias_map: dict[tuple[str, float], bool] = {}
    if not pass_result.get("available", True) or not v2:
        return ({"status": pass_result["status"], "frequency_per_day": pass_result.get("frequency_per_day"),
                 "best_band_fap": pass_result.get("best_band_fap", 1.0), "basis": pass_result.get("basis", "")},
                alias_map)
    tolerance = float(v2["tolerance_per_day"])
    peaks = v2["window_peaks"]
    joint_top: list[float] = []
    for row in v2["series_peaks"]["multiband"]:
        f = float(row["frequency_per_day"])
        aliased = window_alias_under(f, float(row["window_power"]), peaks["multiband"], tolerance,
                                     constants.n_window_peaks) or bool(row["stronger_peak_alias"])
        if not aliased:
            joint_top.append(f)
        if len(joint_top) == constants.joint_top:
            break
    rescored = []
    for cand in v2["candidates"]:
        row = dict(cand)
        frequency = float(row["frequency_per_day"])
        for band in BANDS:
            window_alias = window_alias_under(frequency, float(row[f"{band}_window_power"]),
                                              peaks[SERIES_NAME[band]], tolerance, constants.n_window_peaks)
            cross = False
            if low_alias is not None:
                cross = any(low_alias.get((band, float(p))) is False
                            for p in row.get(f"{band}_cross_pass_partners", []))
            row[f"{band}_alias"] = bool(window_alias or row[f"{band}_same_series_alias"] or cross)
            if float(row[f"{band}_fap"]) < constants.fap_threshold:
                alias_map[(band, frequency)] = row[f"{band}_alias"]
        ratio = row.get("amp_ratio_r_over_g")
        row["coherent"] = bool(
            float(row["delta_phase_cycles"]) <= constants.phase_tolerance_cycles
            and ratio is not None and math.isfinite(float(ratio))
            and constants.amp_ratio_min <= float(ratio) <= constants.amp_ratio_max
        )
        row["joint_top5"] = any(abs(frequency - value) <= tolerance for value in joint_top)
        status, basis, reason = decide(row, constants)
        row.update({"status": status, "basis": basis, "candidate_reason": reason})
        rescored.append(row)
    rescored.sort(key=lambda r: (STATUS_ORDER[r["status"]], float(r["best_band_fap"]), float(r["frequency_per_day"])))
    best = rescored[0]
    return ({"status": best["status"], "frequency_per_day": best["frequency_per_day"],
             "best_band_fap": best["best_band_fap"], "basis": best["basis"]}, alias_map)


def rescore_star(result: dict, constants: V2Constants) -> dict:
    passes: dict[str, dict] = {}
    low_alias: dict[tuple[str, float], bool] | None = None
    for name in ("low", "high"):
        if name not in result["passes"]:
            continue
        summary, alias_map = rescore_pass(result["passes"][name], constants, low_alias if name == "high" else None)
        passes[name] = {**result["passes"][name], **summary}
        if name == "low":
            low_alias = alias_map
    overall = overall_result({**result, "passes": passes})
    row = {"sid": result["source_id"], "best_status": overall["blind_status"], "best_pass": overall["best_pass"],
           "best_frequency_per_day": overall["best_frequency_per_day"], "basis": overall["basis"],
           "baseline_days": float(result["baseline_days"]),
           "n_exp_zg": result["n_exp_zg"], "n_exp_zr": result["n_exp_zr"]}
    for name in ("low", "high"):
        row[f"{name}_status"] = passes[name]["status"] if name in passes else "missing"
        row[f"{name}_frequency_per_day"] = passes[name]["frequency_per_day"] if name in passes else None
        row[f"{name}_available"] = passes[name].get("available", True) if name in passes else False
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stars-dir", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True,
                        help="the source run's manifest.json (must be a completed dev run at the "
                             "admitted pre-amendment digest); its SHA and digest go into <out>.provenance.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = verify_run_manifest(args.run_manifest, args.stars_dir)
    window_expected = float(manifest["constants"]["trend_window_days"])
    if window_expected not in TUNABLE["trend_window_days"]:
        raise SystemExit(f"run trend window {window_expected} is not a declared candidate")
    rows = []
    combos = combinations(window_expected)
    for path in sorted(args.stars_dir.glob("*.json")):
        if path.name.endswith((".prov.json", ".error.json")):
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        if not result.get("complete") or result.get("engine") != "v2":
            continue
        window = float(result["v2"]["constants"]["trend_window_days"])
        if window != window_expected:
            raise SystemExit(f"{path.name}: trend window {window} != the run's {window_expected}")
        for combo_id, constants in combos:
            rows.append({"combination": combo_id, "trend_window_days": window,
                         **rescore_star(result, constants)})
    frame = pd.DataFrame(rows)
    frame.to_csv(args.out, index=False, lineterminator="\n")
    provenance = {
        "run_manifest": str(args.run_manifest), "run_manifest_sha256": sha256_file(args.run_manifest),
        "source_v2_digest": DEV_RUNS_V2_DIGEST, "rescore_v2_digest": v2_digest(),
        "dataset": manifest.get("dataset"), "trend_window_days": window_expected,
        "stars_file_sha256": manifest.get("binding", {}).get("stars_file_sha256"),
        "n_stars": int(frame["sid"].nunique()) if len(frame) else 0, "n_combinations": len(combos),
        "rescore_csv_sha256": sha256_file(args.out),
    }
    args.out.with_suffix(args.out.suffix + ".provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"[rescore] {provenance['n_stars']} stars x {len(combos)} combinations -> {args.out} "
          f"(source digest {DEV_RUNS_V2_DIGEST[:12]}, re-score digest {provenance['rescore_v2_digest'][:12]})")


if __name__ == "__main__":
    main()
