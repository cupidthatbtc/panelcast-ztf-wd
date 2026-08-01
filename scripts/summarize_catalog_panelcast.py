#!/usr/bin/env python3
"""Summarize the time-boxed full-catalog panelcast attempts."""

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "outputs/2026-07-18_151420_993941_17ac"


def load_attempt(path: Path) -> dict[str, object]:
    diagnostics = json.loads(
        (path / "evaluation/diagnostics.json").read_text(encoding="utf-8")
    )
    metrics_path = path / "evaluation/metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        split = metrics["splits"]["within_entity_temporal"]
        coverages = split["calibration"]["coverages"]
        mae = split["point_metrics"]["mae"]
        rmse = split["point_metrics"]["rmse"]
        coverage_80 = coverages["0.80"]["empirical"]
        coverage_95 = coverages["0.95"]["empirical"]
    else:
        mae = rmse = coverage_80 = coverage_95 = None
    return {
        "path": path,
        "rhat": diagnostics["rhat_max"],
        "ess": diagnostics["ess_bulk_min"],
        "divergences": diagnostics["divergences"],
        "mae": mae,
        "rmse": rmse,
        "coverage_80": coverage_80,
        "coverage_95": coverage_95,
    }


def scalar_table(full_path: Path, output: Path) -> None:
    pilot = pd.read_csv(PILOT / "reports/tables/coefficients.csv", index_col=0)
    full = pd.read_csv(full_path / "reports/tables/coefficients.csv", index_col=0)
    pilot = pilot[~pilot.index.str.contains("beta", regex=False)].copy()
    full = full[~full.index.str.contains("beta", regex=False)].copy()
    pilot["parameter_key"] = pilot.index.str.replace(r"^[^_]+_", "", regex=True)
    full["parameter_key"] = full.index.str.replace(r"^[^_]+_", "", regex=True)
    compared = full.reset_index(names="full_parameter").merge(
        pilot.reset_index(names="pilot_parameter"),
        on="parameter_key",
        suffixes=("_full", "_pilot"),
        how="outer",
    )
    compared.to_csv(output, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fit-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full/panelcast_full_fit",
    )
    args = parser.parse_args()

    attempts = []
    for path in sorted(args.fit_dir.glob("attempt_*")):
        if (path / "evaluation/diagnostics.json").exists():
            attempts.append(load_attempt(path))
    if not attempts:
        raise ValueError("no completed panelcast attempt found")

    final = attempts[-1]
    converged = (
        float(final["rhat"]) <= 1.01
        and float(final["ess"]) >= 400
        and int(final["divergences"]) == 0
    )
    coefficients = Path(final["path"]) / "reports/tables/coefficients.csv"
    if coefficients.exists():
        scalar_table(Path(final["path"]), args.fit_dir / "posterior_scalars_vs_pilot.csv")
    if converged:
        narrative = (
            "The final attempt met all prespecified diagnostics. Held-out metrics use the "
            "within-entity-temporal split; posterior scalar estimates are compared with the "
            "19-star pilot in `posterior_scalars_vs_pilot.csv`."
        )
    else:
        narrative = (
            "The final permitted attempt did not meet the prespecified R-hat/ESS/divergence "
            "gate. No convergence ladder was started; the completed diagnostics are retained "
            "as the Stage C result."
        )
    summary = {
        "status": "converged" if converged else "failed_diagnostics",
        "attempts": len(attempts),
        "final_attempt": Path(final["path"]).name,
        "max_rhat": final["rhat"],
        "min_bulk_ess": final["ess"],
        "divergences": final["divergences"],
        "mae": final["mae"],
        "rmse": final["rmse"],
        "coverage_80": final["coverage_80"],
        "coverage_95": final["coverage_95"],
        "narrative": narrative,
        "selection_provenance": {
            "stage_a_eq3_count": 22264,
            "stage_b_count": 1423,
            "cross_variant_core": 1359,
            "sigma_g_convention": "phot_g_n_obs / 9",
            "stage_b_multiplier": 1.1896,
            "paper_multiplier": 1.25,
        },
        "acceptance": {
            "max_rhat": 1.01,
            "min_bulk_ess": 400,
            "divergences": 0,
        },
    }
    (args.fit_dir / "fit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
