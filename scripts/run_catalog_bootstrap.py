#!/usr/bin/env python3
"""Bootstrap the strongest full-catalog Lomb–Scargle candidates."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path

import numpy as np
import pandas as pd

from lomb_scargle_common import exact_power_and_amplitude, prepare_series
from run_bootstrap_fap import bootstrap_maximum
from run_catalog_lomb_scargle import load_star

ROOT = Path(__file__).resolve().parents[1]
RESAMPLES = 100
TOP_CANDIDATES = 30


def bootstrap_one(
    source_id: str,
    pass_name: str,
    frequency: float,
    band: str,
    shard_path: str,
    output_path: str,
    resamples: int,
) -> dict[str, object]:
    output = Path(output_path)
    if output.exists():
        return json.loads(output.read_text(encoding="utf-8"))

    star = load_star(Path(shard_path))
    frame = star[star["band"] == band]
    time, values, errors = prepare_series(frame, high_frequency=pass_name == "high")
    power, _, _ = exact_power_and_amplitude(time, values, errors, frequency)
    minimum = 2.0 / np.ptp(time) if pass_name == "low" else 24.0
    maximum = 48.0 if pass_name == "low" else 1440.0
    seed = (int(source_id[-9:]) + (1 if pass_name == "high" else 0)) % (2**32)
    maxima = bootstrap_maximum(
        time,
        values,
        errors,
        minimum,
        maximum,
        resamples,
        seed,
    )
    exceedances = int(np.sum(maxima >= power))
    result = {
        "source_id": source_id,
        "pass": pass_name,
        "band": band,
        "frequency_per_day": frequency,
        "power": power,
        "bootstrap_fap": (exceedances + 1.0) / (resamples + 1.0),
        "bootstrap_exceedances": exceedances,
        "bootstrap_resamples": resamples,
        "bootstrap_resolution": 1.0 / (resamples + 1.0),
        "bootstrap_grid_samples_per_peak": 2,
        "trials_context": f"bootstrap maximum over {minimum:.8g}..{maximum:g} d^-1",
    }
    temporary = output.with_suffix(".json.part")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    parser.add_argument("--resamples", type=int, default=RESAMPLES)
    parser.add_argument("--top", type=int, default=TOP_CANDIDATES)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    table_path = args.run_dir / "ls_full_catalog.csv"
    table = pd.read_csv(table_path, dtype={"source_id": str})
    surviving = table[table["blind_status"].isin(["confirmed", "candidate"])].copy()
    jobs = surviving.sort_values("best_band_fap").head(args.top)
    if jobs.empty:
        raise ValueError("no surviving candidates to bootstrap")

    output_dir = args.run_dir / "ls/bootstrap/stars"
    exposure_dir = args.run_dir / "exposure_stars"
    results: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for row in jobs.itertuples(index=False):
            band = "zg" if row.zg_fap <= row.zr_fap else "zr"
            future = executor.submit(
                bootstrap_one,
                row.source_id,
                row.best_pass,
                row.best_frequency_per_day,
                band,
                str(exposure_dir / f"{row.source_id}.csv.gz"),
                str(output_dir / f"{row.source_id}.json"),
                args.resamples,
            )
            futures[future] = row.source_id
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                f"[bootstrap] {len(results):02d}/{len(jobs):02d} "
                f"{result['source_id']} ({result['pass']})",
                flush=True,
            )

    bootstrap = pd.DataFrame(results).sort_values("bootstrap_fap")
    output = args.run_dir / "bootstrap_top_candidates.csv"
    bootstrap.to_csv(output, index=False)
    merge_columns = bootstrap[
        [
            "source_id",
            "bootstrap_fap",
            "bootstrap_exceedances",
            "bootstrap_resamples",
            "bootstrap_resolution",
        ]
    ]
    existing_bootstrap = [
        column for column in merge_columns.columns if column != "source_id" and column in table.columns
    ]
    table = table.drop(columns=existing_bootstrap).merge(
        merge_columns,
        on="source_id",
        how="left",
        validate="one_to_one",
    )
    table.to_csv(table_path, index=False)
    print(f"wrote {output} ({len(bootstrap)} candidates)")
    print(f"updated {table_path} with bootstrap columns")


if __name__ == "__main__":
    main()
