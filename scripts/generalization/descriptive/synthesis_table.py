#!/usr/bin/env python3
"""Assemble the campaign synthesis table and cell-level evidence map.

The program only reads frozen metric bundles and v2 comparison outputs.  A
missing input slot is represented by blank rows, while a supplied malformed or
pilot bundle is rejected rather than silently entering the synthesis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = Path(__file__).resolve()

TABLE_COLUMNS = [
    "dataset",
    "arm",
    "endpoint",
    "n",
    "estimate",
    "lo",
    "hi",
    "diff",
    "diff_lo",
    "diff_hi",
    "mcnemar_vs_frozen",
    "interval_type",
    "frame",
    "source_file",
    "source_locator",
    "notes",
]

FROZEN_ENDPOINTS = {
    "D1": (
        "P1_detection",
        "P2_recovery",
        "P3_negative_trigger",
        "census_rate",
        "either_rate",
        "union_rate",
        "incremental_census",
        "mcnemar_p",
        "chance_match_mean",
        "chance_match_p95",
    ),
    "D2": (
        "chance_match_mean",
        "chance_match_p95",
        "P4_recovery_eligible",
        "P4_recovery_usable",
        "P4_trigger",
        "P5_fpr_upper",
        "control_contrast_trigger",
        "control_contrast_strict_recovery",
    ),
    "D3": (
        "P1_detection",
        "P2_recovery",
        "P3_negative_trigger",
        "census_rate",
        "either_rate",
        "union_rate",
        "incremental_census",
        "mcnemar_p",
        "ppv",
        "chance_match_mean",
        "chance_match_p95",
    ),
}

V2_ENDPOINTS = {
    "D2": (
        "P4_recovery_eligible",
        "P4_recovery_usable",
        "P4_trigger",
        "P5_fpr_upper",
        "control_contrast_trigger",
        "control_contrast_strict_recovery",
    ),
    "D3": (
        "P1_detection",
        "P2_recovery",
        "P3_negative_trigger",
        "chance_match_mean",
        "chance_match_p95",
    ),
}

# D3 README.md lines 13, 15, 17, 21-22, and 24-27.  Comparisons are made
# after formatting both the source cell and these displayed values to three
# decimal places, as required by the synthesis-table specification.
D3_README_EXPECTED = {
    "P1_detection.n": 610,
    "P1_detection.estimate": 0.536,
    "P1_detection.lo": 0.496,
    "P1_detection.hi": 0.575,
    "P2_recovery.n": 441,
    "P2_recovery.estimate": 0.163,
    "P2_recovery.lo": 0.132,
    "P2_recovery.hi": 0.201,
    "P3_negative_trigger.n": 2314,
    "P3_negative_trigger.estimate": 0.416,
    "P3_negative_trigger.lo": 0.396,
    "P3_negative_trigger.hi": 0.436,
    "union_rate.n": 585,
    "union_rate.estimate": 0.571,
    "union_rate.lo": 0.530,
    "union_rate.hi": 0.610,
    "incremental_census.estimate": 0.012,
    "incremental_census.lo": 0.006,
    "incremental_census.hi": 0.024,
    "ppv.n": 1290,
    "ppv.estimate": 0.097,
    "ppv.lo": 0.094,
    "ppv.hi": 0.101,
    "chance_match_mean.estimate": 0.0037,
    "chance_match_p95.estimate": 0.0091,
}


@dataclass(frozen=True)
class Origin:
    path: Path
    locator: str


@dataclass
class SynthesisRow:
    values: dict[str, Any]
    origins: dict[str, Origin] = field(default_factory=dict)


@dataclass
class BuildResult:
    rows: list[SynthesisRow]
    evidence_map: dict[str, Any]
    manifest: dict[str, Any]
    cross_check: str


class Context:
    def __init__(self) -> None:
        self.input_shas: dict[str, str] = {}
        self.bundle_manifests: dict[str, dict[str, Any]] = {}

    def sha(self, path: Path) -> str:
        path = path.resolve()
        key = display_path(path)
        if key not in self.input_shas:
            self.input_shas[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        return self.input_shas[key]

    def record(self, path: Path) -> None:
        self.sha(path)


def display_path(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def is_filled(value: Any) -> bool:
    if value is None or value == "":
        return False
    return not (isinstance(value, float) and math.isnan(value))


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def integer(value: Any) -> int | None:
    result = number(value)
    return int(result) if result is not None else None


def flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def json_file(path: Path, context: Context) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"required JSON file not found: {path}")
    context.record(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"could not read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"expected a JSON object in {path}")
    return payload


def csv_file(path: Path, context: Context) -> list[dict[str, str]]:
    if not path.is_file():
        raise SystemExit(f"required CSV file not found: {path}")
    context.record(path)
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise SystemExit(f"CSV has no header: {path}")
            rows = []
            for line_number, row in enumerate(reader, start=2):
                row["__line__"] = str(line_number)
                rows.append(row)
            return rows
    except OSError as exc:
        raise SystemExit(f"could not read {path}: {exc}") from exc


def select_one(path: Path, rows: Iterable[dict[str, str]], **criteria: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(str(row.get(key, "")) == str(expected) for key, expected in criteria.items())
    ]
    if len(matches) != 1:
        selector = ", ".join(f"{key}={value}" for key, value in criteria.items())
        raise SystemExit(f"{path}: expected exactly one row for {selector}; found {len(matches)}")
    return matches[0]


def csv_origin(path: Path, row: dict[str, str], column: str) -> Origin:
    return Origin(path.resolve(), f"CSV line {row['__line__']}, column {column}")


def json_origin(path: Path, key_path: str) -> Origin:
    return Origin(path.resolve(), f"JSON key {key_path}")


def script_origin(locator: str) -> Origin:
    return Origin(SCRIPT_PATH, locator)


def base_values(dataset: str, arm: str, endpoint: str) -> dict[str, Any]:
    return {column: None for column in TABLE_COLUMNS} | {
        "dataset": dataset,
        "arm": arm,
        "endpoint": endpoint,
    }


def missing_row(dataset: str, arm: str, endpoint: str) -> SynthesisRow:
    values = base_values(dataset, arm, endpoint)
    values["notes"] = "bundle not available"
    origin = script_origin(f"endpoint slot {dataset}/{arm}/{endpoint}")
    return SynthesisRow(
        values,
        {key: origin for key, value in values.items() if is_filled(value)},
    )


def sourced_row(
    dataset: str,
    arm: str,
    endpoint: str,
    primary: Origin,
    *,
    origins: dict[str, Origin] | None = None,
    **fields: Any,
) -> SynthesisRow:
    values = base_values(dataset, arm, endpoint)
    values.update(fields)
    values["source_file"] = display_path(primary.path)
    values["source_locator"] = primary.locator
    provenance = {
        key: primary for key, value in values.items() if is_filled(value)
    }
    if origins:
        provenance.update(origins)
    return SynthesisRow(values, provenance)


def bundle_locations(path: Path, label: str) -> tuple[Path, Path]:
    supplied = path.expanduser()
    if not supplied.exists():
        raise SystemExit(f"{label} path does not exist: {supplied}")
    supplied = supplied.resolve()
    if (supplied / "metrics").is_dir():
        return supplied, supplied / "metrics"
    if (supplied / "manifest.json").is_file():
        root = supplied.parent if supplied.name == "metrics" else supplied
        return root, supplied
    raise SystemExit(f"{label} is neither a bundle root nor a metrics directory: {supplied}")


def load_bundle_manifest(
    metrics_dir: Path,
    dataset: str,
    arm: str,
    context: Context,
) -> dict[str, Any]:
    path = metrics_dir / "manifest.json"
    manifest = json_file(path, context)
    found_dataset = str(manifest.get("dataset", "")).lower()
    if found_dataset and found_dataset != dataset.lower():
        raise SystemExit(
            f"{path}: dataset={found_dataset!r}, but this is the {dataset} slot"
        )
    pilot = flag(manifest.get("pilot", False))
    engine = str(manifest.get("engine", "frozen" if arm == "frozen" else "v2"))
    if pilot:
        raise SystemExit(
            f"{dataset} {arm} bundle is marked pilot=true and cannot enter synthesis: {path}"
        )
    if arm == "frozen" and engine != "frozen":
        raise SystemExit(f"{path}: frozen slot has engine={engine!r}")
    context.bundle_manifests[f"{dataset}/{arm}"] = {
        "file": display_path(path),
        "sha256": context.sha(path),
        "pilot": pilot,
        "engine": engine,
    }
    return manifest


def wilson(k: int, n: int) -> tuple[float | None, float | None, float | None]:
    if n == 0:
        return None, None, None
    z = 1.959963984540054
    p = k / n
    denominator = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denominator
    half = z / denominator * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return p, max(0.0, center - half), min(1.0, center + half)


def completeness_row(
    dataset: str,
    endpoint: str,
    path: Path,
    rows: list[dict[str, str]],
    *,
    rule: str,
    scope: str,
    frame: str,
    notes: str = "",
) -> SynthesisRow:
    source = select_one(path, rows, **{"pass": "best", "rule": rule, "scope": scope})
    primary = csv_origin(path, source, "p")
    origins = {
        "n": csv_origin(path, source, "n"),
        "estimate": csv_origin(path, source, "p"),
        "lo": csv_origin(path, source, "lo"),
        "hi": csv_origin(path, source, "hi"),
    }
    return sourced_row(
        dataset,
        "frozen",
        endpoint,
        primary,
        origins=origins,
        n=integer(source.get("n")),
        estimate=number(source.get("p")),
        lo=number(source.get("lo")),
        hi=number(source.get("hi")),
        interval_type="Wilson 95%",
        frame=frame,
        notes=notes,
    )


def contingency_rows(dataset: str, metrics_dir: Path, context: Context) -> list[SynthesisRow]:
    path = metrics_dir / "contingency_complementarity.json"
    payload = json_file(path, context)
    n = integer(payload.get("n_positives_scored"))
    output = []
    for endpoint, key in (
        ("union_rate", "union_completeness"),
        ("incremental_census", "incremental_census_only"),
    ):
        item = payload.get(key)
        if not isinstance(item, dict):
            raise SystemExit(f"{path}: missing object {key}")
        primary = json_origin(path, f"$.{key}.p")
        output.append(
            sourced_row(
                dataset,
                "frozen",
                endpoint,
                primary,
                origins={
                    "n": json_origin(path, "$.n_positives_scored"),
                    "estimate": primary,
                    "lo": json_origin(path, f"$.{key}.lo"),
                    "hi": json_origin(path, f"$.{key}.hi"),
                },
                n=n,
                estimate=number(item.get("p")),
                lo=number(item.get("lo")),
                hi=number(item.get("hi")),
                interval_type="Wilson 95%",
                frame="positives with both methods available and usable",
                notes="",
            )
        )
    key = "mcnemar_exact_p_secondary"
    output.append(
        sourced_row(
            dataset,
            "frozen",
            "mcnemar_p",
            json_origin(path, f"$.{key}"),
            origins={"n": json_origin(path, "$.n_positives_scored")},
            n=n,
            estimate=number(payload.get(key)),
            interval_type="exact two-sided McNemar",
            frame="positives with both methods available and usable",
            notes="secondary marginal-homogeneity test",
        )
    )
    return output


def chance_rows(dataset: str, metrics_dir: Path, context: Context) -> list[SynthesisRow]:
    path = metrics_dir / "chance_match.json"
    payload = json_file(path, context)
    if dataset == "D2":
        count_key = "derangements"
        mean_key = "accidental_recovery_rate_mean"
        p95_key = "accidental_recovery_rate_p95"
        interval = "target-level derangement calibration"
        frame = "nominal arm-B target-equal recovery"
    else:
        count_key = "permutations"
        mean_key = "accidental_direct_match_rate_mean"
        p95_key = "accidental_direct_match_rate_p95"
        interval = "truth-list permutation calibration"
        frame = "frequency-scorable stars"
    output = []
    for endpoint, key in (("chance_match_mean", mean_key), ("chance_match_p95", p95_key)):
        if number(payload.get(key)) is None:
            raise SystemExit(f"{path}: missing finite {key}")
        output.append(
            sourced_row(
                dataset,
                "frozen",
                endpoint,
                json_origin(path, f"$.{key}"),
                origins={"n": json_origin(path, f"$.{count_key}")},
                n=integer(payload.get(count_key)),
                estimate=number(payload.get(key)),
                interval_type=interval,
                frame=frame,
                notes="calibration; not an observed recovery estimate",
            )
        )
    return output


def d1_negative_row(metrics_dir: Path, context: Context) -> SynthesisRow:
    path = metrics_dir / "per_star.csv"
    rows = csv_file(path, context)
    negatives = [row for row in rows if str(row.get("label_positive", "")).lower() == "false"]
    if not negatives:
        raise SystemExit(f"{path}: no label_positive=false paper-constant rows")
    confirmed = sum(row.get("best_status") == "confirmed" for row in negatives)
    candidates = sum(row.get("best_status") == "candidate" for row in negatives)
    estimate, lo, hi = wilson(confirmed, len(negatives))
    lines = ",".join(row["__line__"] for row in negatives)
    origin = Origin(
        path.resolve(),
        f"CSV lines {lines}, filter label_positive=false; aggregate best_status",
    )
    return sourced_row(
        "D1",
        "frozen",
        "P3_negative_trigger",
        origin,
        n=len(negatives),
        estimate=estimate,
        lo=lo,
        hi=hi,
        interval_type="Wilson 95%",
        frame="five paper-constant stars; transit control excluded",
        notes=f"{confirmed} confirmed + {candidates} candidate",
    )


def frozen_d1(metrics_dir: Path, context: Context) -> list[SynthesisRow]:
    load_bundle_manifest(metrics_dir, "D1", "frozen", context)
    completeness_path = metrics_dir / "completeness_by_class_pass_rule.csv"
    completeness = csv_file(completeness_path, context)
    rows = [
        completeness_row(
            "D1",
            "P1_detection",
            completeness_path,
            completeness,
            rule="confirmed",
            scope="detection_eligible_roster",
            frame="13 paper-variable stars (eligible roster)",
        ),
        completeness_row(
            "D1",
            "P2_recovery",
            completeness_path,
            completeness,
            rule="confirmed",
            scope="freq_recovery_scorable",
            frame="frequency-scorable paper-variable stars",
            notes="diagnostic only; non-contemporaneous literature frequencies",
        ),
        d1_negative_row(metrics_dir, context),
        completeness_row(
            "D1",
            "census_rate",
            completeness_path,
            completeness,
            rule="census",
            scope="detection_eligible_roster",
            frame="13 paper-variable stars (eligible roster)",
        ),
        completeness_row(
            "D1",
            "either_rate",
            completeness_path,
            completeness,
            rule="either",
            scope="detection_eligible_roster",
            frame="13 paper-variable stars (eligible roster)",
        ),
    ]
    rows.extend(contingency_rows("D1", metrics_dir, context))
    rows.extend(chance_rows("D1", metrics_dir, context))
    return rows


def d3_trigger_row(root: Path, metrics_dir: Path, context: Context) -> SynthesisRow:
    path = metrics_dir / "trigger_rates.csv"
    table = csv_file(path, context)
    source = select_one(
        path,
        table,
        quantity="negative_class_trigger_rate",
        rule="confirmed",
    )
    primary = csv_origin(path, source, "p")
    notes = "non-dSct comparison class; not a Gaussian false-positive rate"
    origins: dict[str, Origin] = {
        "n": csv_origin(path, source, "n"),
        "estimate": primary,
        "lo": csv_origin(path, source, "lo"),
        "hi": csv_origin(path, source, "hi"),
    }

    strata_path = root / "descriptive_postlaunch" / "d3_negative_trigger_strata.csv"
    if strata_path.is_file():
        strata = csv_file(strata_path, context)
        labels = (
            ("oid_le_1", "<=1"),
            ("oid_2", "2"),
            ("oid_3_4", "3-4"),
            ("oid_ge_5", ">=5"),
        )
        parts = []
        selected_lines = []
        for code, display in labels:
            item = select_one(strata_path, strata, stratifier="merged_oid", stratum=code)
            selected_lines.append(item["__line__"])
            parts.append(
                f"{display}: {integer(item.get('k_confirmed'))}/{integer(item.get('n_negative'))}"
                f"={number(item.get('rate')):.3f}"
            )
        notes += "; merged-oid descriptive rates (no intervals): " + ", ".join(parts)
        origins["notes"] = Origin(
            strata_path.resolve(),
            f"CSV lines {','.join(selected_lines)}, stratifier=merged_oid",
        )
        sidecar = root / "descriptive_postlaunch" / "d3_strata_covariates.README.md"
        if sidecar.is_file():
            context.record(sidecar)

    return sourced_row(
        "D3",
        "frozen",
        "P3_negative_trigger",
        primary,
        origins=origins,
        n=integer(source.get("n")),
        estimate=number(source.get("p")),
        lo=number(source.get("lo")),
        hi=number(source.get("hi")),
        interval_type="Wilson 95%",
        frame="dSct=0 sampled negative class",
        notes=notes,
    )


def d3_ppv_row(metrics_dir: Path, context: Context) -> SynthesisRow:
    path = metrics_dir / "ppv.csv"
    table = csv_file(path, context)
    source = select_one(path, table, estimand="frame_specific_label_ppv")
    primary = csv_origin(path, source, "p")
    return sourced_row(
        "D3",
        "frozen",
        "ppv",
        primary,
        origins={
            "n": csv_origin(path, source, "n_triggered"),
            "estimate": primary,
            "lo": csv_origin(path, source, "lo"),
            "hi": csv_origin(path, source, "hi"),
            "interval_type": csv_origin(path, source, "interval"),
        },
        n=integer(source.get("n_triggered")),
        estimate=number(source.get("p")),
        lo=number(source.get("lo")),
        hi=number(source.get("hi")),
        interval_type=source.get("interval") or "survey bootstrap",
        frame="triggered weighted frame; dSct=2 excluded",
        notes="frame-specific label PPV; no transfer to other prevalences",
    )


def frozen_d3(root: Path, metrics_dir: Path, context: Context) -> list[SynthesisRow]:
    load_bundle_manifest(metrics_dir, "D3", "frozen", context)
    completeness_path = metrics_dir / "completeness_by_class_pass_rule.csv"
    completeness = csv_file(completeness_path, context)
    rows = [
        completeness_row(
            "D3",
            "P1_detection",
            completeness_path,
            completeness,
            rule="confirmed",
            scope="detection_eligible_roster",
            frame="dSct=1 eligible roster",
        ),
        completeness_row(
            "D3",
            "P2_recovery",
            completeness_path,
            completeness,
            rule="confirmed",
            scope="freq_recovery_scorable",
            frame="Mo-joined, S_best=1, usable",
            notes="Mo-join-conditioned dominant-direct recovery",
        ),
        d3_trigger_row(root, metrics_dir, context),
        completeness_row(
            "D3",
            "census_rate",
            completeness_path,
            completeness,
            rule="census",
            scope="detection_eligible_roster",
            frame="dSct=1 eligible roster",
        ),
        completeness_row(
            "D3",
            "either_rate",
            completeness_path,
            completeness,
            rule="either",
            scope="detection_eligible_roster",
            frame="dSct=1 eligible roster",
        ),
    ]
    rows.extend(contingency_rows("D3", metrics_dir, context))
    rows.append(d3_ppv_row(metrics_dir, context))
    rows.extend(chance_rows("D3", metrics_dir, context))
    return rows


def d2_cluster_row(
    path: Path,
    table: list[dict[str, str]],
    endpoint: str,
    source_endpoint: str,
    denominator: str,
) -> SynthesisRow:
    source = select_one(
        path,
        table,
        arm="B",
        scenario="nominal",
        endpoint=source_endpoint,
        denominator=denominator,
    )
    primary = csv_origin(path, source, "p")
    notes = "target-equal nominal arm-B estimate"
    if endpoint == "P4_trigger":
        notes += "; eligible denominator (usable trigger variant remains in source table)"
    return sourced_row(
        "D2",
        "frozen",
        endpoint,
        primary,
        origins={
            "n": csv_origin(path, source, "n_targets"),
            "estimate": primary,
            "lo": csv_origin(path, source, "lo"),
            "hi": csv_origin(path, source, "hi"),
            "interval_type": csv_origin(path, source, "interval"),
        },
        n=integer(source.get("n_targets")),
        estimate=number(source.get("p")),
        lo=number(source.get("lo")),
        hi=number(source.get("hi")),
        interval_type=source.get("interval") or "target-cluster bootstrap",
        frame=f"nominal arm-B targets, {denominator}; scheduled strata",
        notes=notes,
    )


def d2_p5_row(metrics_dir: Path, context: Context) -> SynthesisRow:
    path = metrics_dir / "trigger_rates.csv"
    table = csv_file(path, context)
    source = select_one(path, table, quantity="fpr_gaussian", rule="confirmed")
    primary = csv_origin(path, source, "cp_one_sided_95_upper")
    n = integer(source.get("n_completed"))
    k = integer(source.get("k"))
    return sourced_row(
        "D2",
        "frozen",
        "P5_fpr_upper",
        primary,
        origins={"n": csv_origin(path, source, "n_completed"), "estimate": primary},
        n=n,
        estimate=number(source.get("cp_one_sided_95_upper")),
        interval_type="exact one-sided Clopper-Pearson 95% upper",
        frame="completed arm-A Gaussian nulls",
        notes=f"upper bound is the endpoint; observed {k}/{n}",
    )


def d2_control_rows(metrics_dir: Path, context: Context) -> list[SynthesisRow]:
    path = metrics_dir / "d2_paired_controls_summary.csv"
    table = csv_file(path, context)
    output = []
    for endpoint, source_endpoint in (
        ("control_contrast_trigger", "D"),
        ("control_contrast_strict_recovery", "R"),
    ):
        source = select_one(path, table, endpoint=source_endpoint)
        primary = csv_origin(path, source, "paired_diff_b_minus_c")
        n_targets = integer(source.get("n_targets"))
        n_pairs = integer(source.get("n_pairs_scored"))
        windows = integer(source.get("n_unique_windows"))
        output.append(
            sourced_row(
                "D2",
                "frozen",
                endpoint,
                primary,
                origins={
                    "n": csv_origin(path, source, "n_targets"),
                    "estimate": primary,
                    "lo": csv_origin(path, source, "paired_diff_b_minus_c_lo"),
                    "hi": csv_origin(path, source, "paired_diff_b_minus_c_hi"),
                },
                n=n_targets,
                estimate=number(source.get("paired_diff_b_minus_c")),
                lo=number(source.get("paired_diff_b_minus_c_lo")),
                hi=number(source.get("paired_diff_b_minus_c_hi")),
                interval_type="target-cluster bootstrap",
                frame="nominal injected minus paired-control response",
                notes=f"{n_pairs} scored pairs; {windows} unique control windows",
            )
        )
    return output


def frozen_d2(metrics_dir: Path, context: Context) -> list[SynthesisRow]:
    load_bundle_manifest(metrics_dir, "D2", "frozen", context)
    cluster_path = metrics_dir / "d2_cluster_completeness.csv"
    cluster = csv_file(cluster_path, context)
    # This file is not a headline-table source, but binding it records the
    # available sensitivity output alongside the selected nominal rows.
    contrasts = metrics_dir / "d2_scenario_contrasts.csv"
    if contrasts.is_file():
        context.record(contrasts)
    rows = chance_rows("D2", metrics_dir, context)
    rows.extend(
        [
            d2_cluster_row(cluster_path, cluster, "P4_recovery_eligible", "recovery", "eligible"),
            d2_cluster_row(cluster_path, cluster, "P4_recovery_usable", "recovery", "usable"),
            d2_cluster_row(cluster_path, cluster, "P4_trigger", "trigger", "eligible"),
            d2_p5_row(metrics_dir, context),
        ]
    )
    rows.extend(d2_control_rows(metrics_dir, context))
    return rows


def load_comparison_manifest(
    directory: Path,
    dataset: str,
    context: Context,
) -> dict[str, Any]:
    manifest_path = directory / "manifest.json"
    manifest = json_file(manifest_path, context)
    found_dataset = str(manifest.get("dataset", "")).lower()
    if found_dataset != dataset.lower():
        raise SystemExit(
            f"{manifest_path}: dataset={found_dataset!r}, but this is the {dataset} v2 slot"
        )
    if flag(manifest.get("pilot", False)):
        raise SystemExit(
            f"{dataset} v2 comparison is marked pilot=true and cannot enter synthesis: {manifest_path}"
        )
    if manifest.get("half") != "holdout":
        raise SystemExit(f"{manifest_path}: v2 synthesis requires half='holdout'")
    if not isinstance(manifest.get("registration"), dict) or not manifest["registration"]:
        raise SystemExit(f"{manifest_path}: missing registration binding")
    engine = str(manifest.get("engine", "v2"))
    context.bundle_manifests[f"{dataset}/v2"] = {
        "file": display_path(manifest_path),
        "sha256": context.sha(manifest_path),
        "pilot": False,
        "engine": engine,
    }
    return manifest


def comparison_row(
    dataset: str,
    output_endpoint: str,
    path: Path,
    source: dict[str, str],
    *,
    upper_is_endpoint: bool = False,
) -> SynthesisRow:
    estimate_column = "v2_hi" if upper_is_endpoint else "v2_p"
    primary = csv_origin(path, source, estimate_column)
    note = source.get("note", "")
    if upper_is_endpoint:
        observed = number(source.get("v2_p"))
        note = (note + "; " if note else "") + f"upper bound is endpoint; point estimate={observed}"
    return sourced_row(
        dataset,
        "v2",
        output_endpoint,
        primary,
        origins={
            "n": csv_origin(path, source, "n"),
            "estimate": primary,
            "lo": csv_origin(path, source, "v2_lo"),
            "hi": csv_origin(path, source, "v2_hi"),
            "diff": csv_origin(path, source, "diff"),
            "diff_lo": csv_origin(path, source, "diff_lo"),
            "diff_hi": csv_origin(path, source, "diff_hi"),
            "mcnemar_vs_frozen": csv_origin(path, source, "mcnemar_exact_p"),
            "interval_type": csv_origin(path, source, "interval"),
            "frame": csv_origin(path, source, "frame"),
            "notes": csv_origin(path, source, "note"),
        },
        n=integer(source.get("n")),
        estimate=number(source.get(estimate_column)),
        lo=None if upper_is_endpoint else number(source.get("v2_lo")),
        hi=None if upper_is_endpoint else number(source.get("v2_hi")),
        diff=number(source.get("diff")),
        diff_lo=number(source.get("diff_lo")),
        diff_hi=number(source.get("diff_hi")),
        mcnemar_vs_frozen=number(source.get("mcnemar_exact_p")),
        interval_type=(
            "exact one-sided Clopper-Pearson 95% upper"
            if upper_is_endpoint
            else source.get("interval", "")
        ),
        frame=source.get("frame", ""),
        notes=note,
    )


def comparison_chance_rows(
    dataset: str,
    endpoints_path: Path,
    p2: dict[str, str],
    manifest_path: Path,
    manifest: dict[str, Any],
) -> list[SynthesisRow]:
    output = []
    chance = manifest.get("chance_match", {}).get("v2", {})
    n = integer(chance.get("permutations")) if isinstance(chance, dict) else None
    n_origin = json_origin(manifest_path, "$.chance_match.v2.permutations")
    for endpoint, column in (
        ("chance_match_mean", "v2_chance_direct_mean"),
        ("chance_match_p95", "v2_chance_direct_p95"),
    ):
        value = number(p2.get(column))
        if value is None:
            raise SystemExit(f"{endpoints_path}: P2 row lacks finite {column}")
        primary = csv_origin(endpoints_path, p2, column)
        output.append(
            sourced_row(
                dataset,
                "v2",
                endpoint,
                primary,
                origins={"n": n_origin, "estimate": primary},
                n=n,
                estimate=value,
                interval_type="truth-list permutation calibration",
                frame="v2 frequency-scorable holdout stars",
                notes="calibration reported beside the paired P2 comparison",
            )
        )
    return output


def v2_comparison(directory: Path, dataset: str, context: Context) -> list[SynthesisRow]:
    if not directory.exists() or not directory.is_dir():
        raise SystemExit(f"{dataset} v2 comparison directory does not exist: {directory}")
    directory = directory.resolve()
    manifest = load_comparison_manifest(directory, dataset, context)
    manifest_path = directory / "manifest.json"
    endpoints_path = directory / "endpoints.csv"
    table = csv_file(endpoints_path, context)
    mapping = (
        {
            "P4_recovery_eligible": "P4_recovery_eligible",
            "P4_recovery_usable": "P4_recovery_usable",
            "P4_trigger": "P4_trigger_eligible",
            "P5_fpr_upper": "P5_gaussian_false_alarm",
            "control_contrast_trigger": "control_contrast_trigger",
            "control_contrast_strict_recovery": "control_contrast_strict_recovery",
        }
        if dataset == "D2"
        else {
            "P1_detection": "P1_detection",
            "P2_recovery": "P2_recovery",
            "P3_negative_trigger": "P3_negative_trigger",
        }
    )
    output = []
    selected: dict[str, dict[str, str]] = {}
    for output_endpoint, source_endpoint in mapping.items():
        source = select_one(endpoints_path, table, endpoint=source_endpoint)
        selected[output_endpoint] = source
        output.append(
            comparison_row(
                dataset,
                output_endpoint,
                endpoints_path,
                source,
                upper_is_endpoint=output_endpoint == "P5_fpr_upper",
            )
        )
    if dataset == "D3":
        output.extend(
            comparison_chance_rows(
                dataset,
                endpoints_path,
                selected["P2_recovery"],
                manifest_path,
                manifest,
            )
        )
    return output


def order_rows(rows: list[SynthesisRow]) -> list[SynthesisRow]:
    expected = []
    for dataset in ("D1", "D2", "D3"):
        expected.extend((dataset, "frozen", endpoint) for endpoint in FROZEN_ENDPOINTS[dataset])
        if dataset in V2_ENDPOINTS:
            expected.extend((dataset, "v2", endpoint) for endpoint in V2_ENDPOINTS[dataset])
    by_key = {
        (row.values["dataset"], row.values["arm"], row.values["endpoint"]): row
        for row in rows
    }
    if len(by_key) != len(rows):
        raise SystemExit("internal error: duplicate (dataset, arm, endpoint) rows")
    return [by_key[key] for key in expected]


def cross_check_d3(
    rows: list[SynthesisRow],
    expected: dict[str, float] | None = None,
) -> int:
    expected = D3_README_EXPECTED if expected is None else expected
    indexed = {
        row.values["endpoint"]: row.values
        for row in rows
        if row.values["dataset"] == "D3" and row.values["arm"] == "frozen"
    }
    checked = 0
    for cell, wanted in expected.items():
        endpoint, field_name = cell.rsplit(".", 1)
        actual = indexed.get(endpoint, {}).get(field_name)
        if not is_filled(actual) or f"{float(actual):.3f}" != f"{float(wanted):.3f}":
            raise SystemExit(
                f"D3 README cross-check failed for {cell}: "
                f"table={actual!r}, expected={wanted!r} (three-decimal comparison)"
            )
        checked += 1
    return checked


def evidence_document(rows: list[SynthesisRow], context: Context) -> dict[str, Any]:
    cells: dict[str, dict[str, Any]] = {}
    for row in rows:
        prefix = f"{row.values['dataset']}|{row.values['arm']}|{row.values['endpoint']}"
        for column in TABLE_COLUMNS:
            value = row.values.get(column)
            if not is_filled(value):
                continue
            origin = row.origins.get(column)
            if origin is None:
                raise SystemExit(f"internal error: no evidence origin for {prefix}|{column}")
            cell_id = f"{prefix}|{column}"
            cells[cell_id] = {
                "file": display_path(origin.path),
                "sha256": context.sha(origin.path),
                "locator": origin.locator,
                "value": value,
            }
    return {
        "schema_version": 1,
        "cells": cells,
        "bundle_manifests": context.bundle_manifests,
    }


def write_csv(path: Path, rows: list[SynthesisRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(row.values for row in rows)


def compact_number(value: Any) -> str:
    numeric = number(value)
    if numeric is None:
        return ""
    absolute = abs(numeric)
    if absolute and absolute < 0.001:
        return f"{numeric:.2e}"
    if absolute and absolute < 0.01:
        return f"{numeric:.4f}"
    return f"{numeric:.3f}"


def markdown_cell(row: SynthesisRow | None) -> str:
    if row is None or not is_filled(row.values.get("estimate")):
        return "—"
    values = row.values
    rendered = compact_number(values["estimate"])
    if is_filled(values.get("lo")) and is_filled(values.get("hi")):
        rendered += f" [{compact_number(values['lo'])}, {compact_number(values['hi'])}]"
    if is_filled(values.get("n")):
        rendered += f" ({values['n']})"
    if values.get("arm") == "v2" and is_filled(values.get("diff")):
        rendered += f"; Δ={compact_number(values['diff'])}"
        if is_filled(values.get("diff_lo")) and is_filled(values.get("diff_hi")):
            rendered += f" [{compact_number(values['diff_lo'])}, {compact_number(values['diff_hi'])}]"
    return rendered


def markdown_table(rows: list[SynthesisRow], present_slots: list[str]) -> str:
    columns = [tuple(slot.split("/", 1)) for slot in present_slots]
    available_endpoints = []
    for dataset, arm in columns:
        profile = FROZEN_ENDPOINTS[dataset] if arm == "frozen" else V2_ENDPOINTS[dataset]
        for endpoint in profile:
            if endpoint not in available_endpoints:
                available_endpoints.append(endpoint)
    lookup = {
        (row.values["dataset"], row.values["arm"], row.values["endpoint"]): row
        for row in rows
    }
    header = ["Endpoint", *(f"{dataset}/{arm}" for dataset, arm in columns)]
    lines = [
        "# Campaign synthesis table",
        "",
        "Values are estimate [95% interval] (n). For v2 cells, Δ is v2 − frozen on the paired holdout frame.",
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---", *("---:" for _ in columns)]) + " |",
    ]
    for endpoint in available_endpoints:
        cells = [endpoint]
        for dataset, arm in columns:
            cells.append(markdown_cell(lookup.get((dataset, arm, endpoint))))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def build_synthesis(
    *,
    out_dir: Path,
    d1_metrics: Path | None = None,
    d2_bundle: Path | None = None,
    d3_bundle: Path | None = None,
    d2_v2_comparison: Path | None = None,
    d3_v2_comparison: Path | None = None,
    d3_expected: dict[str, float] | None = None,
) -> BuildResult:
    context = Context()
    context.record(SCRIPT_PATH)
    rows: list[SynthesisRow] = []
    slots: dict[str, bool] = {
        "D1/frozen": d1_metrics is not None,
        "D2/frozen": d2_bundle is not None,
        "D3/frozen": d3_bundle is not None,
        "D2/v2": d2_v2_comparison is not None,
        "D3/v2": d3_v2_comparison is not None,
    }

    if d1_metrics is None:
        rows.extend(missing_row("D1", "frozen", endpoint) for endpoint in FROZEN_ENDPOINTS["D1"])
    else:
        _, metrics = bundle_locations(d1_metrics, "D1 metrics")
        rows.extend(frozen_d1(metrics, context))

    if d2_bundle is None:
        rows.extend(missing_row("D2", "frozen", endpoint) for endpoint in FROZEN_ENDPOINTS["D2"])
    else:
        _, metrics = bundle_locations(d2_bundle, "D2 bundle")
        rows.extend(frozen_d2(metrics, context))

    d3_root: Path | None = None
    if d3_bundle is None:
        rows.extend(missing_row("D3", "frozen", endpoint) for endpoint in FROZEN_ENDPOINTS["D3"])
    else:
        d3_root, metrics = bundle_locations(d3_bundle, "D3 bundle")
        rows.extend(frozen_d3(d3_root, metrics, context))

    for dataset, comparison in (
        ("D2", d2_v2_comparison),
        ("D3", d3_v2_comparison),
    ):
        if comparison is None:
            rows.extend(missing_row(dataset, "v2", endpoint) for endpoint in V2_ENDPOINTS[dataset])
        else:
            rows.extend(v2_comparison(comparison, dataset, context))

    rows = order_rows(rows)
    cross_check = "not run (D3 bundle absent)"
    if d3_root is not None:
        readme = d3_root / "README.md"
        if d3_expected is not None:
            checked = cross_check_d3(rows, d3_expected)
            cross_check = f"pass ({checked} injected expected cells)"
        elif readme.is_file():
            context.record(readme)
            checked = cross_check_d3(rows)
            cross_check = f"pass ({checked} README cells at three decimals)"
        else:
            cross_check = "not run (D3 README absent)"

    evidence = evidence_document(rows, context)
    present = [slot for slot, available in slots.items() if available]
    absent = [slot for slot, available in slots.items() if not available]
    manifest = {
        "script": {"path": display_path(SCRIPT_PATH), "sha256": context.sha(SCRIPT_PATH)},
        "inputs": dict(sorted(context.input_shas.items())),
        "datasets": {"present": present, "absent": absent},
        "d3_readme_cross_check": cross_check,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "synthesis_table.csv", rows)
    (out_dir / "evidence_map.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "synthesis_table.md").write_text(
        markdown_table(rows, present), encoding="utf-8"
    )
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return BuildResult(rows, evidence, manifest, cross_check)


def parse_args() -> argparse.Namespace:
    default_out = REPO_ROOT / "generalization" / "results" / (
        datetime.now().date().isoformat() + "_synthesis"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d1-metrics", type=Path)
    parser.add_argument("--d2-bundle", type=Path)
    parser.add_argument("--d3-bundle", type=Path)
    parser.add_argument("--d2-v2-comparison", type=Path)
    parser.add_argument("--d3-v2-comparison", type=Path)
    parser.add_argument("--out-dir", type=Path, default=default_out)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_synthesis(
        out_dir=args.out_dir,
        d1_metrics=args.d1_metrics,
        d2_bundle=args.d2_bundle,
        d3_bundle=args.d3_bundle,
        d2_v2_comparison=args.d2_v2_comparison,
        d3_v2_comparison=args.d3_v2_comparison,
    )
    print(f"[synthesis_table] wrote {args.out_dir}")
    print(f"[synthesis_table] D3 README cross-check: {result.cross_check.upper()}")


if __name__ == "__main__":
    main()
