#!/usr/bin/env python3
"""Run resumable blind Lomb–Scargle searches over the rebuilt catalog."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import traceback

import numpy as np
import pandas as pd

from lomb_scargle_common import periodogram_to_memmap, prepare_series
from run_lomb_scargle import (
    PASS_BOUNDS,
    evaluate_candidates,
    grid_for,
    json_ready,
    multiband_power,
    peak_rows_for_band,
    peak_rows_multiband,
)

ROOT = Path(__file__).resolve().parents[1]
SANITY_IDS = (
    "3345661467822106624",
    "6555925496084361344",
    "103999471976858496",
    "2833849800205759360",
)


def physical_workers() -> int:
    try:
        import psutil

        physical = psutil.cpu_count(logical=False)
    except ImportError:
        physical = None
    cores = physical or os.cpu_count() or 1
    return max(1, cores - 2)


def load_star(path: Path) -> pd.DataFrame:
    columns = ["source_id", "band", "mjd", "bjd_tdb", "night_mjd", "mag", "magerr"]
    frame = pd.read_csv(path, usecols=columns, dtype={"source_id": str, "band": str})
    numeric = ["mjd", "bjd_tdb", "night_mjd", "mag", "magerr"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    if set(frame["band"]) != {"zg", "zr"}:
        raise ValueError("both zg and zr are required")
    return frame


def close_memmaps(powers: dict[str, np.ndarray]) -> None:
    for power in powers.values():
        if isinstance(power, np.memmap):
            power.flush()
            power._mmap.close()
    powers.clear()


def analyze_star(
    source_id: str,
    shard_path: str,
    result_path: str,
    work_root: str,
    passes: tuple[str, ...],
) -> dict[str, object]:
    result_file = Path(result_path)
    if result_file.exists():
        existing = json.loads(result_file.read_text(encoding="utf-8"))
        if existing.get("complete") and set(existing.get("passes", {})) >= set(passes):
            return existing

    star = load_star(Path(shard_path))
    work_dir = Path(work_root) / source_id
    work_dir.mkdir(parents=True, exist_ok=True)
    baseline = float(star["bjd_tdb"].max() - star["bjd_tdb"].min())
    pass_results: dict[str, dict[str, object]] = {}

    try:
        for pass_name in passes:
            high = pass_name == "high"
            grid = grid_for(pass_name, baseline)
            series = {
                band: prepare_series(star[star["band"] == band], high_frequency=high)
                for band in ("zg", "zr")
            }
            paths = {
                band: work_dir / f".{pass_name}_{band}.power.dat" for band in ("zg", "zr")
            }
            multiband_path = work_dir / f".{pass_name}_multiband.power.dat"
            powers: dict[str, np.ndarray] = {}
            try:
                for band in ("zg", "zr"):
                    powers[band] = periodogram_to_memmap(*series[band], grid, paths[band])
                powers["multiband"], weights = multiband_power(
                    powers["zg"], powers["zr"], multiband_path
                )

                peak_rows: list[dict[str, object]] = []
                upper_limits: dict[str, float] = {}
                for band in ("zg", "zr"):
                    rows, _, a95 = peak_rows_for_band(
                        source_id,
                        pass_name,
                        band,
                        powers[band],
                        grid,
                        *series[band],
                    )
                    peak_rows.extend(rows)
                    upper_limits[band] = a95
                combined_time = star["bjd_tdb"].to_numpy(dtype=float)
                combined_time -= combined_time.min()
                peak_rows.extend(
                    peak_rows_multiband(
                        source_id,
                        pass_name,
                        powers["multiband"],
                        grid,
                        combined_time,
                    )
                )
                candidates = evaluate_candidates(
                    source_id,
                    pass_name,
                    peak_rows,
                    grid,
                    series,
                )
                best = candidates[0]
                pass_results[pass_name] = {
                    "status": best["status"],
                    "basis": best["basis"],
                    "frequency_per_day": best["frequency_per_day"],
                    "period_days": best["period_days"],
                    "period_seconds": best["period_seconds"],
                    "best_band_fap": best["best_band_fap"],
                    "zg_power": best["zg_power"],
                    "zr_power": best["zr_power"],
                    "zg_fap": best["zg_fap"],
                    "zr_fap": best["zr_fap"],
                    "zg_amplitude_mmag": best["zg_amplitude_mmag"],
                    "zr_amplitude_mmag": best["zr_amplitude_mmag"],
                    "zg_alias": best["zg_alias"],
                    "zr_alias": best["zr_alias"],
                    "multiband_top5": best["multiband_top5"],
                    "zg_a95_mmag": upper_limits["zg"],
                    "zr_a95_mmag": upper_limits["zr"],
                    "grid_size": grid.size,
                    "grid_step_per_day": grid.step,
                    "multiband_zg_weight": weights[0],
                    "multiband_zr_weight": weights[1],
                    "top_peaks": peak_rows,
                }
            finally:
                close_memmaps(powers)
                for path in (*paths.values(), multiband_path):
                    path.unlink(missing_ok=True)

        result = {
            "schema_version": 1,
            "source_id": source_id,
            "n_exp_zg": int((star["band"] == "zg").sum()),
            "n_exp_zr": int((star["band"] == "zr").sum()),
            "baseline_days": baseline,
            "passes": pass_results,
            "complete": set(pass_results) >= set(passes),
        }
        temporary = result_file.with_suffix(".json.part")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(result, indent=2, default=json_ready) + "\n",
            encoding="utf-8",
        )
        temporary.replace(result_file)
        shutil.rmtree(work_dir, ignore_errors=True)
        return result
    except Exception:
        error_path = result_file.with_suffix(".error.json")
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(
            json.dumps(
                {
                    "source_id": source_id,
                    "error": traceback.format_exc(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


def overall_result(result: dict[str, object]) -> dict[str, object]:
    passes = result["passes"]
    order = {"confirmed": 0, "candidate": 1, "not_detected": 2}
    best_pass, best = min(
        passes.items(),
        key=lambda item: (order[item[1]["status"]], float(item[1]["best_band_fap"])),
    )
    return {
        "source_id": result["source_id"],
        "ls_complete": bool(result["complete"]),
        "blind_status": best["status"],
        "best_pass": best_pass,
        "best_frequency_per_day": best["frequency_per_day"],
        "best_period_days": best["period_days"],
        "best_period_seconds": best["period_seconds"],
        "basis": best["basis"],
        "best_band_fap": best["best_band_fap"],
        "zg_fap": best["zg_fap"],
        "zr_fap": best["zr_fap"],
        "zg_amplitude_mmag": best["zg_amplitude_mmag"],
        "zr_amplitude_mmag": best["zr_amplitude_mmag"],
        "zg_alias": best["zg_alias"],
        "zr_alias": best["zr_alias"],
        "low_zg_a95_mmag": passes.get("low", {}).get("zg_a95_mmag"),
        "low_zr_a95_mmag": passes.get("low", {}).get("zr_a95_mmag"),
        "high_zg_a95_mmag": passes.get("high", {}).get("zg_a95_mmag"),
        "high_zr_a95_mmag": passes.get("high", {}).get("zr_a95_mmag"),
        "n_exp_zg": result["n_exp_zg"],
        "n_exp_zr": result["n_exp_zr"],
        "baseline_days": result["baseline_days"],
    }


def rebuild_table(star_dir: Path, output: Path, roster: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for path in sorted(star_dir.glob("*.json")):
        if path.name.endswith(".error.json"):
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("complete"):
            rows.append(overall_result(result))
    table = pd.DataFrame(rows)
    if not table.empty:
        metadata = roster[
            [
                "source_id",
                "wdj_name",
                "wd_class",
                "known_roster",
                "in_core",
                "n_variants",
            ]
        ]
        table = metadata.merge(table, on="source_id", how="inner", validate="one_to_one")
        table.sort_values("source_id").to_csv(output, index=False)
    return table


def verify_sanity(results: dict[str, dict[str, object]]) -> dict[str, object]:
    failures: list[str] = []
    checks: dict[str, dict[str, object]] = {}
    for source_id in SANITY_IDS:
        low = results[source_id]["passes"]["low"]
        period = float(low["period_days"])
        frequency = float(low["frequency_per_day"])
        if source_id in SANITY_IDS[:2]:
            passed = low["status"] == "confirmed" and 0.2 <= period <= 1.0
            expected = "confirmed RR Lyrae, 0.2–1.0 d"
        elif source_id == "103999471976858496":
            passed = low["status"] == "confirmed" and abs(period - 0.44977) <= 0.005
            expected = "0.44977 ± 0.005 d"
        else:
            passed = low["status"] == "confirmed" and abs(frequency - 6.1464) <= 0.01
            expected = "6.1464 ± 0.01 d^-1"
        checks[source_id] = {
            "passed": passed,
            "expected": expected,
            "status": low["status"],
            "period_days": period,
            "frequency_per_day": frequency,
        }
        if not passed:
            failures.append(f"{source_id}: {checks[source_id]}")
    if failures:
        raise RuntimeError("catalog sanity gates failed:\n" + "\n".join(failures))
    return {"all_passed": True, "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    parser.add_argument("--workers", type=int, default=physical_workers())
    parser.add_argument("--stars", nargs="*")
    parser.add_argument("--skip-sanity", action="store_true")
    args = parser.parse_args()

    exposure_star_dir = args.run_dir / "exposure_stars"
    ls_dir = args.run_dir / "ls"
    star_dir = ls_dir / "stars"
    sanity_dir = ls_dir / "sanity"
    work_dir = ls_dir / "work"
    for path in (star_dir, sanity_dir, work_dir):
        path.mkdir(parents=True, exist_ok=True)

    roster = pd.read_csv(
        ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
        dtype={"source_id": str},
    )
    source_ids = sorted(path.stem.split(".csv")[0] for path in exposure_star_dir.glob("*.csv.gz"))
    if args.stars:
        requested = set(args.stars)
        source_ids = [source_id for source_id in source_ids if source_id in requested]
        missing = requested - set(source_ids)
        if missing:
            raise ValueError(f"requested stars absent from exposure shards: {sorted(missing)}")

    if not args.skip_sanity and not args.stars:
        sanity_results = {}
        for source_id in SANITY_IDS:
            shard = exposure_star_dir / f"{source_id}.csv.gz"
            if not shard.exists():
                raise ValueError(f"sanity source is not crossmatched: {source_id}")
            sanity_results[source_id] = analyze_star(
                source_id,
                str(shard),
                str(sanity_dir / f"{source_id}.json"),
                str(work_dir / "sanity"),
                ("low",),
            )
            print(f"[sanity] finished {source_id}", flush=True)
        sanity = verify_sanity(sanity_results)
        (ls_dir / "sanity_gates.json").write_text(
            json.dumps(sanity, indent=2, default=json_ready) + "\n",
            encoding="utf-8",
        )
        print("[sanity] all four known-period gates passed", flush=True)

    pending = []
    for source_id in source_ids:
        result_path = star_dir / f"{source_id}.json"
        if result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                if result.get("complete") and set(result.get("passes", {})) >= set(PASS_BOUNDS):
                    continue
            except json.JSONDecodeError:
                pass
        pending.append(source_id)

    print(
        f"[catalog-ls] sources={len(source_ids):,} pending={len(pending):,} workers={args.workers}",
        flush=True,
    )
    failures: dict[str, str] = {}
    completed_now = 0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                analyze_star,
                source_id,
                str(exposure_star_dir / f"{source_id}.csv.gz"),
                str(star_dir / f"{source_id}.json"),
                str(work_dir),
                tuple(PASS_BOUNDS),
            ): source_id
            for source_id in pending
        }
        for future in as_completed(futures):
            source_id = futures[future]
            try:
                future.result()
                completed_now += 1
                if completed_now % 10 == 0 or completed_now == len(pending):
                    table = rebuild_table(
                        star_dir,
                        args.run_dir / "ls_full_catalog.csv",
                        roster,
                    )
                    print(
                        f"[catalog-ls] completed {completed_now:,}/{len(pending):,}; "
                        f"table rows={len(table):,}",
                        flush=True,
                    )
            except Exception as exc:
                failures[source_id] = repr(exc)
                print(f"[catalog-ls] FAILED {source_id}: {exc}", flush=True)

    table = rebuild_table(star_dir, args.run_dir / "ls_full_catalog.csv", roster)
    manifest = {
        "source_count": len(source_ids),
        "completed": len(table),
        "pending_at_start": len(pending),
        "workers": args.workers,
        "passes": list(PASS_BOUNDS),
        "samples_per_peak": 10,
        "high_frequency_time_standard": "BJD_TDB",
        "high_frequency_detrending": "per-night median subtracted",
        "low_frequency_detrending": "per-band weighted global mean subtracted",
        "spectral_window_power_threshold": 0.1,
        "failures": failures,
    }
    (ls_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[catalog-ls] wrote {args.run_dir / 'ls_full_catalog.csv'} ({len(table):,} rows)")
    if failures or len(table) != len(source_ids):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
