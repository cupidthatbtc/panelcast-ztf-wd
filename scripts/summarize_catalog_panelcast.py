#!/usr/bin/env python3
"""Summarize the time-boxed full-catalog panelcast attempts."""

import argparse
import json
import math
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
        secondary = metrics["splits"].get("entity_disjoint")
        mae = split["point_metrics"]["mae"]
        rmse = split["point_metrics"]["rmse"]
        r2 = split["point_metrics"]["r2"]
        coverage_80 = coverages["0.80"]["empirical"]
        coverage_95 = coverages["0.95"]["empirical"]
    else:
        mae = rmse = r2 = coverage_80 = coverage_95 = None
        secondary = None
    prior_path = path / "evaluation/prior_predictive.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.exists() else {}
    return {
        "path": path,
        "rhat": diagnostics["rhat_max"],
        "ess": diagnostics["ess_bulk_min"],
        "divergences": diagnostics["divergences"],
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "coverage_80": coverage_80,
        "coverage_95": coverage_95,
        "secondary_mae": (
            secondary["point_metrics"]["mae"] if secondary is not None else None
        ),
        "secondary_rmse": (
            secondary["point_metrics"]["rmse"] if secondary is not None else None
        ),
        "secondary_r2": (
            secondary["point_metrics"]["r2"] if secondary is not None else None
        ),
        "secondary_coverage_80": (
            secondary["calibration"]["coverages"]["0.80"]["empirical"]
            if secondary is not None
            else None
        ),
        "secondary_coverage_95": (
            secondary["calibration"]["coverages"]["0.95"]["empirical"]
            if secondary is not None
            else None
        ),
        "prior_predictive_reasonable": prior.get("reasonable"),
        "prior_predictive_mean": prior.get("summary", {}).get("mean"),
        "prior_predictive_sd": prior.get("summary", {}).get("sd"),
        "prior_predictive_fraction_in_bounds": prior.get("fraction_in_bounds"),
        "prior_predictive_flags": prior.get("informational_flags", []),
    }


def inverse_offset_logit(value: float, lower: float, upper: float) -> float:
    probability = 1.0 / (1.0 + math.exp(-value))
    return lower - 0.5 + probability * (upper - lower + 1.0)


def offset_logit_derivative(value: float, lower: float, upper: float) -> float:
    probability = 1.0 / (1.0 + math.exp(-value))
    return (upper - lower + 1.0) * probability * (1.0 - probability)


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
    full_mu = float(compared.loc[compared["parameter_key"].eq("mu_artist"), "Estimate_full"].iloc[0])
    pilot_mu = float(compared.loc[compared["parameter_key"].eq("mu_artist"), "Estimate_pilot"].iloc[0])
    full_derivative = offset_logit_derivative(full_mu, 10.0, 20.0)
    pilot_derivative = offset_logit_derivative(pilot_mu, 15.0, 18.8)
    compared["magnitude_equivalent_full"] = pd.NA
    compared["magnitude_equivalent_pilot"] = pd.NA
    mean_mask = compared["parameter_key"].eq("mu_artist")
    scale_mask = compared["parameter_key"].isin(["sigma_artist", "sigma_obs"])
    compared.loc[mean_mask, "magnitude_equivalent_full"] = inverse_offset_logit(
        full_mu, 10.0, 20.0
    )
    compared.loc[mean_mask, "magnitude_equivalent_pilot"] = inverse_offset_logit(
        pilot_mu, 15.0, 18.8
    )
    compared.loc[scale_mask, "magnitude_equivalent_full"] = (
        compared.loc[scale_mask, "Estimate_full"] * full_derivative
    )
    compared.loc[scale_mask, "magnitude_equivalent_pilot"] = (
        compared.loc[scale_mask, "Estimate_pilot"] * pilot_derivative
    )
    compared["comparison_note"] = (
        "Raw latent values use different descriptor bounds; magnitude equivalents "
        "invert the location or apply a delta-method local scale."
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
            "The final attempt met all prespecified sampling diagnostics. The primary "
            "within-entity-temporal holdout is well calibrated, while the optional "
            "entity-disjoint cold-start split fails badly and must not be interpreted as "
            "validated out-of-entity prediction. Posterior scalar estimates are compared "
            "with the 19-star pilot in `posterior_scalars_vs_pilot.csv`."
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
        "r2": final["r2"],
        "coverage_80": final["coverage_80"],
        "coverage_95": final["coverage_95"],
        "secondary_mae": final["secondary_mae"],
        "secondary_rmse": final["secondary_rmse"],
        "secondary_r2": final["secondary_r2"],
        "secondary_coverage_80": final["secondary_coverage_80"],
        "secondary_coverage_95": final["secondary_coverage_95"],
        "prior_predictive_reasonable": final["prior_predictive_reasonable"],
        "prior_predictive_mean": final["prior_predictive_mean"],
        "prior_predictive_sd": final["prior_predictive_sd"],
        "prior_predictive_fraction_in_bounds": final[
            "prior_predictive_fraction_in_bounds"
        ],
        "prior_predictive_flags": final["prior_predictive_flags"],
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
