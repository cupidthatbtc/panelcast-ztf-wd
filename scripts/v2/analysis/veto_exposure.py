#!/usr/bin/env python3
"""Truth-frequency VETO EXPOSURE (V2_PLAN.md §6, descriptive; G-review finding 10).

For every star with truth frequencies (D3: the Mo dominant frequency per
roster star; D2: every retained injected mode of nominal arm-B shards) and
for each pass whose grid contains the frequency, decide — from the v2
per-star JSON and the shard — whether the truth frequency would be vetoed by
each component of the v2 veto in each band, and by their union:

  fixed      : within tol of a fixed locus (window.fixed_loci);
  data       : within tol of one of the first N recorded window peaks;
  local      : frozen local test on the shard's time stamps (max window
               strength within +/- tol >= 0.1);
  stronger   : difference/mirror alias (solar or sidereal spacing) of a
               recorded same-series peak whose power exceeds the exact
               power at the truth frequency (frozen helper on the v2 series);
  cross_pass : (high pass only) alias of a recorded unaliased significant
               low-pass candidate frequency.

Output: veto_exposure_per_truth.csv (one row per truth frequency x pass x
band) and veto_exposure_summary.csv (fraction exposed by component and
union, by dataset / pass / band), plus a manifest with input SHAs. Purely
descriptive: nothing here feeds a decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

V2_DIR = Path(__file__).resolve().parents[1]   # scripts/v2 (this file lives in scripts/v2/analysis,
sys.path.insert(0, str(V2_DIR))                # outside the v2 code digest: analysis only)
from align import align_zero_points  # noqa: E402
from analyze_star_v2 import load_star_v2  # noqa: E402
from detrend import prepare_series_v2  # noqa: E402
from rescore_v2 import FIXED  # noqa: E402
from v2_common import (  # noqa: E402
    BANDS, DEFAULT, PASS_BOUNDS, WINDOW_POWER_THRESHOLD, V2Constants, exact_power_and_amplitude,
    window_strength, with_overrides,
)
from window import is_alias_of_stronger_v2  # noqa: E402

REPO_ROOT = V2_DIR.parents[1]
SERIES = {"zg": "zg", "zr": "zr"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truth_frequencies(dataset: str, shards_dir: Path | None) -> dict[str, list[float]]:
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))
    if dataset == "d3":
        from metrics_generalization import truth_d3
        truth = truth_d3()
        return {r.sid: ([float(r.primary_freq)] if r.primary_freq is not None else [])
                for r in truth.itertuples(index=False)}
    injected = pd.read_csv(shards_dir / "injected_modes.csv", dtype={"campaign_id": str})
    return injected.groupby("campaign_id")["frequency_per_day"].apply(list).to_dict()


def pass_for(frequency: float, baseline: float) -> list[str]:
    passes = []
    for name, (lo, hi) in PASS_BOUNDS.items():
        lower = 2.0 / baseline if lo is None else lo
        if lower <= frequency <= hi:
            passes.append(name)
    return passes


def exposure_rows(sid: str, result: dict, shard_path: Path, truths: list[float],
                  constants: V2Constants) -> list[dict]:
    star = load_star_v2(shard_path)
    aligned, _ = align_zero_points(star, constants)
    origin = float(aligned["bjd_tdb"].min())
    baseline = float(result["baseline_days"])
    tolerance = constants.tolerance_over_baseline / baseline
    rows = []
    for name, pass_result in result["passes"].items():
        v2 = pass_result.get("v2")
        if not v2:
            continue
        series = {band: prepare_series_v2(aligned[aligned["band"] == band], name == "high", origin, constants)
                  for band in BANDS}
        cross = v2.get("cross_pass_stronger", {})
        for truth in truths:
            if name not in pass_for(truth, baseline):
                continue
            for band in BANDS:
                time, values, errors = series[band]
                power, _, _ = exact_power_and_amplitude(time, values, errors, truth)
                offsets = np.linspace(-tolerance, tolerance, constants.window_local_samples)
                local_power = float(np.max(window_strength(time, truth + offsets)))
                peaks = v2["window_peaks"][SERIES[band]][: constants.n_window_peaks]
                stronger = [float(p["frequency_per_day"]) for p in v2["series_peaks"][SERIES[band]]
                            if float(p["power"]) > power]
                components = {
                    "fixed": any(abs(truth - locus) <= tolerance for locus in FIXED),
                    "data": any(abs(truth - float(p["frequency_per_day"])) <= tolerance for p in peaks),
                    "local": local_power >= WINDOW_POWER_THRESHOLD,
                    "stronger": is_alias_of_stronger_v2(truth, stronger, tolerance),
                    "cross_pass": (name == "high") and is_alias_of_stronger_v2(
                        truth, [float(x) for x in cross.get(band, [])], tolerance),
                }
                rows.append({"sid": sid, "pass": name, "band": band, "truth_frequency_per_day": truth,
                             "exact_power": power, "local_window_power": local_power,
                             **{f"veto_{k}": bool(v) for k, v in components.items()},
                             "veto_union": any(components.values())})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("d2", "d3"), required=True)
    parser.add_argument("--stars-dir", type=Path, required=True)
    parser.add_argument("--shards-dir", type=Path, required=True)
    parser.add_argument("--constants", default=None, help="the run's constants overrides (JSON/file)")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    constants = DEFAULT
    if args.constants:
        payload = json.loads(Path(args.constants).read_text()) if Path(args.constants).exists() else json.loads(args.constants)
        constants = with_overrides(DEFAULT, **payload.get("overrides", payload))
    truths = truth_frequencies(args.dataset, args.shards_dir)
    rows, inputs = [], {}
    for path in sorted(args.stars_dir.glob("*.json")):
        if path.name.endswith((".prov.json", ".error.json")):
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        sid = result.get("source_id", "")
        if result.get("engine") != "v2" or not truths.get(sid):
            continue
        shard = args.shards_dir / f"{sid}.csv.gz"
        inputs[str(path)] = sha256_file(path)
        rows.extend(exposure_rows(sid, result, shard, truths[sid], constants))
    per_truth = pd.DataFrame(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    per_truth.to_csv(args.out_dir / "veto_exposure_per_truth.csv", index=False, lineterminator="\n")
    if not per_truth.empty:
        columns = [c for c in per_truth.columns if c.startswith("veto_")]
        summary = per_truth.groupby(["pass", "band"])[columns].agg(["mean", "sum"])
        summary.columns = [f"{a}_{b}" for a, b in summary.columns]
        summary["n"] = per_truth.groupby(["pass", "band"]).size()
        summary.reset_index().to_csv(args.out_dir / "veto_exposure_summary.csv", index=False, lineterminator="\n")
        print(summary.reset_index().to_string(index=False))
    (args.out_dir / "veto_exposure.manifest.json").write_text(json.dumps({
        "dataset": args.dataset, "constants": constants.as_dict(), "n_truth_rows": len(per_truth),
        "inputs_sha256_count": len(inputs),
        "inputs_sha256_digest": hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
        "script_sha256": sha256_file(Path(__file__).resolve()),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"[veto_exposure] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
