#!/usr/bin/env python3
"""Build crossmatch, period-systematics, and forecast-baseline sensitivity products."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().eq("true")


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    residual = y_true - y_pred
    return {
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "r2": float(1.0 - np.sum(residual**2) / np.sum((y_true - y_true.mean()) ** 2)),
        "n": int(len(y_true)),
    }


def add_metric(
    rows: list[dict[str, object]],
    split: str,
    model: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    subset: str = "all",
) -> None:
    rows.append({"split": split, "model": model, "subset": subset, **metrics(y_true, y_pred)})


def prediction_arrays(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return (
        np.asarray(payload["y_true"], dtype=float),
        np.asarray(payload["y_pred_mean"], dtype=float),
        np.asarray(payload["entity"], dtype=str),
    )


def crossmatch_sensitivity(
    run_dir: Path,
    roster: pd.DataFrame,
    census: pd.DataFrame,
    ls: pd.DataFrame,
) -> pd.DataFrame:
    audit = pd.read_csv(
        run_dir / "panelcast_crossmatch_magnitude_audit.csv",
        dtype={"source_id": str},
    )
    merged = audit.merge(
        census[["source_id", "census_variable"]],
        on="source_id",
        validate="one_to_one",
    ).merge(
        ls[["source_id", "blind_status"]],
        on="source_id",
        validate="one_to_one",
    ).merge(
        roster[["source_id", "known_roster"]],
        on="source_id",
        validate="one_to_one",
    )
    delta = merged["ztf_minus_gaia_g"].abs()
    separation = merged["nearest_separation_arcsec"]
    scenarios = {
        "primary_all": pd.Series(True, index=merged.index),
        "magnitude_delta_le_2": delta.le(2.0),
        "magnitude_delta_le_1": delta.le(1.0),
        "magnitude_delta_le_0.5": delta.le(0.5),
        "separation_le_2_arcsec": separation.le(2.0),
        "separation_le_2_and_delta_le_1": separation.le(2.0) & delta.le(1.0),
    }
    rows = []
    for name, keep in scenarios.items():
        frame = merged[keep]
        confirmed = int(frame["blind_status"].eq("confirmed").sum())
        census_variable = int(as_bool(frame["census_variable"]).sum())
        rows.append(
            {
                "scenario": name,
                "sources": len(frame),
                "known_roster": int(as_bool(frame["known_roster"]).sum()),
                "census_variable": census_variable,
                "ls_confirmed": confirmed,
                "ls_candidates": int(frame["blind_status"].eq("candidate").sum()),
                "ls_not_detected": int(frame["blind_status"].eq("not_detected").sum()),
                "ls_confirmed_fraction": confirmed / len(frame),
                "census_or_ls_confirmed": int(
                    (as_bool(frame["census_variable"]) | frame["blind_status"].eq("confirmed")).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def period_systematics(ls: pd.DataFrame) -> pd.DataFrame:
    frame = ls[ls["blind_status"].isin(["confirmed", "candidate"])].copy()
    frequency = pd.to_numeric(frame["best_frequency_per_day"], errors="coerce").to_numpy()
    references = []
    for harmonic in range(1, 11):
        references.extend(
            [
                (f"solar_{harmonic}", float(harmonic)),
                (f"sidereal_{harmonic}", 1.00273790935 * harmonic),
            ]
        )
    distances = np.column_stack([np.abs(frequency - value) for _, value in references])
    nearest = np.argmin(distances, axis=1)
    frame["nearest_daily_systematic"] = [references[index][0] for index in nearest]
    frame["distance_to_daily_systematic_per_day"] = distances[np.arange(len(frame)), nearest]
    frame["wide_daily_alias_0p01"] = frame["distance_to_daily_systematic_per_day"].lt(0.01)
    return frame[
        [
            "source_id",
            "blind_status",
            "best_pass",
            "best_frequency_per_day",
            "best_period_days",
            "best_band_fap",
            "basis",
            "nearest_daily_systematic",
            "distance_to_daily_systematic_per_day",
            "wide_daily_alias_0p01",
        ]
    ].sort_values(["wide_daily_alias_0p01", "distance_to_daily_systematic_per_day"], ascending=[False, True])


def forecast_baselines(run_dir: Path, roster: pd.DataFrame) -> pd.DataFrame:
    split_root = ROOT / "data/splits"
    temporal_train = pd.read_parquet(split_root / "within_entity_temporal/train.parquet")
    temporal_test = pd.read_parquet(split_root / "within_entity_temporal/test.parquet")
    disjoint_train = pd.read_parquet(split_root / "entity_disjoint/train.parquet")
    disjoint_test = pd.read_parquet(split_root / "entity_disjoint/test.parquet")

    fit = run_dir / "panelcast_full_fit/attempt_1/evaluation"
    primary_y, primary_pred, primary_entities = prediction_arrays(
        fit / "within_entity_temporal/predictions.json"
    )
    disjoint_y, disjoint_pred, disjoint_entities = prediction_arrays(
        fit / "entity_disjoint/predictions.json"
    )
    rows: list[dict[str, object]] = []
    add_metric(rows, "within_entity_temporal", "panelcast_primary", primary_y, primary_pred)

    temporal_train = temporal_train.sort_values(["source_id", "month_date_parsed"])
    last_value = temporal_train.groupby("source_id").tail(1).set_index("source_id")["mag_binned"]
    entity_median = temporal_train.groupby("source_id")["mag_binned"].median()
    temporal_y = temporal_test["mag_binned"].to_numpy(dtype=float)
    add_metric(
        rows,
        "within_entity_temporal",
        "last_value",
        temporal_y,
        temporal_test["source_id"].map(last_value).to_numpy(dtype=float),
    )
    add_metric(
        rows,
        "within_entity_temporal",
        "entity_train_median",
        temporal_y,
        temporal_test["source_id"].map(entity_median).to_numpy(dtype=float),
    )
    add_metric(
        rows,
        "within_entity_temporal",
        "global_train_mean",
        temporal_y,
        np.full(len(temporal_y), temporal_train["mag_binned"].mean()),
    )

    add_metric(rows, "entity_disjoint", "panelcast_primary", disjoint_y, disjoint_pred)
    disjoint_y_split = disjoint_test["mag_binned"].to_numpy(dtype=float)
    add_metric(
        rows,
        "entity_disjoint",
        "global_train_mean",
        disjoint_y_split,
        np.full(len(disjoint_y_split), disjoint_train["mag_binned"].mean()),
    )
    class_mean = disjoint_train.groupby("wd_class")["mag_binned"].mean()
    add_metric(
        rows,
        "entity_disjoint",
        "class_train_mean",
        disjoint_y_split,
        disjoint_test["wd_class"]
        .map(class_mean)
        .fillna(disjoint_train["mag_binned"].mean())
        .to_numpy(dtype=float),
    )

    features = roster.copy()
    features["source_id"] = "GaiaDR3_" + features["source_id"]
    features = features.set_index("source_id")[["gaia_g_mag", "bp_rp"]]
    gaia_direct = disjoint_test["source_id"].map(features["gaia_g_mag"]).to_numpy(dtype=float)
    add_metric(rows, "entity_disjoint", "gaia_g_direct", disjoint_y_split, gaia_direct)

    train_entity = (
        disjoint_train.groupby("source_id")["mag_binned"].median().to_frame("target").join(features)
    )
    design = np.column_stack(
        [
            np.ones(len(train_entity)),
            train_entity["gaia_g_mag"],
            train_entity["bp_rp"],
        ]
    )
    coefficients = np.linalg.lstsq(design, train_entity["target"].to_numpy(), rcond=None)[0]
    test_design = np.column_stack(
        [
            np.ones(len(disjoint_test)),
            disjoint_test["source_id"].map(features["gaia_g_mag"]),
            disjoint_test["source_id"].map(features["bp_rp"]),
        ]
    )
    gaia_ols = test_design @ coefficients
    add_metric(rows, "entity_disjoint", "gaia_g_bp_rp_train_ols", disjoint_y_split, gaia_ols)

    audit = pd.read_csv(
        run_dir / "panelcast_crossmatch_magnitude_audit.csv",
        dtype={"source_id": str},
    )
    clean_entities = set(
        "GaiaDR3_" + audit.loc[~as_bool(audit["magnitude_mismatch_flag"]), "source_id"]
    )
    clean_prediction = np.isin(disjoint_entities, list(clean_entities))
    clean_split = disjoint_test["source_id"].isin(clean_entities).to_numpy()
    add_metric(
        rows,
        "entity_disjoint",
        "panelcast_primary",
        disjoint_y[clean_prediction],
        disjoint_pred[clean_prediction],
        "magnitude_delta_le_1",
    )
    add_metric(
        rows,
        "entity_disjoint",
        "gaia_g_bp_rp_train_ols",
        disjoint_y_split[clean_split],
        gaia_ols[clean_split],
        "magnitude_delta_le_1",
    )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "|" + "|".join("---" for _ in frame.columns) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:.5f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(
    output: Path,
    sensitivity: pd.DataFrame,
    systematics: pd.DataFrame,
    baselines: pd.DataFrame,
) -> None:
    primary = sensitivity[sensitivity["scenario"].eq("primary_all")].iloc[0]
    clean = sensitivity[sensitivity["scenario"].eq("magnitude_delta_le_1")].iloc[0]
    wide_aliases = systematics[systematics["wide_daily_alias_0p01"]]
    primary_rows = baselines[
        (baselines["split"].eq("within_entity_temporal")) & baselines["subset"].eq("all")
    ]
    disjoint_rows = baselines[
        (baselines["split"].eq("entity_disjoint")) & baselines["subset"].eq("all")
    ]
    lines = [
        "# Catalog hardening — interim results",
        "",
        "## Crossmatch sensitivity",
        "",
        f"The prespecified result has **{int(primary.sources)}** sources and **{int(primary.ls_confirmed)}** L-S confirmations. Applying |median ZTF g − Gaia G| ≤1 leaves **{int(clean.sources)}** sources and **{int(clean.ls_confirmed)}** confirmations.",
        "",
        markdown_table(sensitivity),
        "",
        "## Wider daily-systematics audit",
        "",
        f"A ±0.01 d⁻¹ neighborhood around the first ten solar/sidereal harmonics flags **{len(wide_aliases)}** of {len(systematics)} confirmed/candidate results. This is a sensitivity flag, not a post-hoc replacement classification.",
        "",
        "## Forecast baselines",
        "",
        "### Within-entity temporal",
        "",
        markdown_table(primary_rows),
        "",
        "### Entity-disjoint",
        "",
        markdown_table(disjoint_rows),
        "",
        "The original panelcast fit does not beat the entity-median baseline for known stars and is effectively a global-mean model for unseen stars. Gaia G and BP−RP provide a strong, train-only cold-start baseline, motivating the minimal `core_numeric` panelcast sensitivity fit.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    args = parser.parse_args()

    roster = pd.read_csv(
        ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
        dtype={"source_id": str},
    )
    census = pd.read_csv(args.run_dir / "census_full_catalog.csv", dtype={"source_id": str})
    ls = pd.read_csv(args.run_dir / "ls_full_catalog.csv", dtype={"source_id": str})
    output_dir = args.run_dir / "hardening"
    output_dir.mkdir(parents=True, exist_ok=True)

    sensitivity = crossmatch_sensitivity(args.run_dir, roster, census, ls)
    systematics = period_systematics(ls)
    baselines = forecast_baselines(args.run_dir, roster)
    sensitivity.to_csv(output_dir / "crossmatch_sensitivity.csv", index=False)
    systematics.to_csv(output_dir / "period_systematics_audit.csv", index=False)
    baselines.to_csv(output_dir / "forecast_baselines.csv", index=False)
    write_report(output_dir / "HARDENING_RESULTS.md", sensitivity, systematics, baselines)

    payload = {
        "primary_sources": int(sensitivity.iloc[0]["sources"]),
        "primary_confirmed": int(sensitivity.iloc[0]["ls_confirmed"]),
        "magnitude_clean_sources": int(sensitivity.iloc[2]["sources"]),
        "magnitude_clean_confirmed": int(sensitivity.iloc[2]["ls_confirmed"]),
        "wide_daily_alias_flags": int(as_bool(systematics["wide_daily_alias_0p01"]).sum()),
        "baseline_rows": len(baselines),
    }
    (output_dir / "robustness_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
