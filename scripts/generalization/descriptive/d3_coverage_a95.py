#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE coverage comparison (D3 crossmatched frame vs the
928-window development pool) and per-pass, per-band a95 distributions by D3
class.

Admitted by generalization/reviews/G5prep/sol_round2.md item 7
(F16/F18, ADMIT-DESCRIPTIVE, ruling fixed 2026-09-01). The binding
definitions, implemented here without discretion:

- Coverage frames: `D3_crossmatched` = all 2,901 rows of the D3 census
  panel; `development_pool` = all 928 rows of census_full_catalog.csv.
  Metrics zg_n_exp, zr_n_exp, zg_n_nights, zr_n_nights and
  wg_contrasts = zg_n_exp - zg_n_nights (asserted nonnegative). Linear
  quantiles; no pooling of the two frames.
- a95: read the per-star JSONs directly; cross class_label in
  {dsct_flag0, dsct_flag1, dsct_flag2} x pass in {low, high} x band in
  {zg, zr}; value = passes[pass][band + "_a95_mmag"]; no pooling across
  bands. n_roster is the class's roster count, n_json the class members
  with a result JSON, n_pass_available those whose JSON marks the pass
  available, n_finite the finite a95 values, n_missing = n_roster -
  n_finite (every class member lacking a finite a95, whatever the reason).
  Quantiles are blank when n_finite is zero.
- analysis_status=postlaunch_descriptive, prespecified=false, interval=none.
  Nothing here enters a headline, endpoint, exclusion, reclassification, or
  replacement denominator. FULL-run only (refuses pilot metrics bundles).

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive), so committing/pulling it is SHA-neutral for live runners.

Inputs: a completed FULL D3 metrics out-dir (per_star.csv, manifest.json —
used only to bind the stars-dir to the frozen bundle), the stars-dir of
per-star JSONs, the frozen roster, the D3 census panel and the published
pool census. Outputs (out-dir): d3_vs_pool_coverage.csv,
d3_a95_by_class_pass_band.csv, d3_coverage_a95.README.md (verbatim
disclosure) and d3_coverage_a95.manifest.json (input/output SHAs). The
sidecars are module-prefixed so several descriptive modules can share one
descriptive_postlaunch/ directory without clobbering each other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)

EXPECTED_D3_CENSUS_ROWS = 2901
EXPECTED_POOL_ROWS = 928
EXPECTED_ROSTER = 3000
CLASS_LEVELS = ("dsct_flag0", "dsct_flag1", "dsct_flag2")
PASSES = ("low", "high")
BANDS = ("zg", "zr")

ANALYSIS_STATUS = "postlaunch_descriptive"
PRESPECIFIED = False
INTERVAL = "none"
VERDICT_FILE = "generalization/reviews/G5prep/sol_round2.md"
DISCLOSURE = (
    "Post-launch descriptive coverage tables compare the crossmatched "
    "Kepler-field frame with the fixed 928-window development pool and "
    "summarize per-pass, per-band a95 values by D3 class; the quantiles "
    "describe the realized frames without intervals or ZTF-wide transfer "
    "claims."
)

COVERAGE_FRAMES = (("D3_crossmatched", EXPECTED_D3_CENSUS_ROWS),
                   ("development_pool", EXPECTED_POOL_ROWS))
COVERAGE_SOURCE_COLUMNS = ("zg_n_exp", "zr_n_exp", "zg_n_nights", "zr_n_nights")
COVERAGE_METRICS = COVERAGE_SOURCE_COLUMNS + ("wg_contrasts",)
COVERAGE_QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
COVERAGE_COLUMNS = [
    "frame", "covariate", "n_frame", "n_nonmissing",
    "min", "p10", "p25", "p50", "p75", "p90", "max",
    "analysis_status", "prespecified", "interval",
]

A95_QUANTILES = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
A95_COLUMNS = [
    "class_label", "pass", "band", "n_roster", "n_json", "n_pass_available",
    "n_finite", "n_missing", "min", "p05", "p10", "p25", "p50", "p75", "p90", "p95", "max",
    "analysis_status", "prespecified", "interval",
]

DEFAULT_ROSTER = REPO_ROOT / "generalization/data/d3/roster_d3.csv"
DEFAULT_D3_CENSUS = (
    REPO_ROOT / "generalization/data/d3/crossmatch_freeze/panels_census_generic.csv"
)
DEFAULT_POOL_CENSUS = (
    REPO_ROOT / "catalog-rebuild/results/2026-08-01_full/catalog/census_full_catalog.csv"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_label(path: Path) -> str:
    """Repo-relative manifest key when the file lives under REPO_ROOT (so the
    manifest compares across machines); absolute otherwise."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(resolved)


def _finite(value) -> bool:
    try:
        return value is not None and not isinstance(value, bool) \
            and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _as_bool(value) -> bool | None:
    """CSV/JSON booleans; None when missing (NaN/None/empty)."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    text = str(value).strip().lower()
    if text in ("true", "1"):
        return True
    if text in ("false", "0"):
        return False
    if text == "":
        return None
    raise SystemExit(f"unreadable boolean {value!r}")


# ---------------------------------------------------------------- coverage

def coverage_rows(frame_name: str, census: pd.DataFrame, expected_rows: int) -> list[dict]:
    if len(census) != expected_rows:
        raise SystemExit(
            f"{frame_name}: {len(census)} rows != the ruled frame size {expected_rows}"
        )
    if "source_id" in census.columns and census["source_id"].duplicated().any():
        raise SystemExit(f"{frame_name}: duplicate source_id")
    missing = [c for c in COVERAGE_SOURCE_COLUMNS if c not in census.columns]
    if missing:
        raise SystemExit(f"{frame_name}: columns missing {missing}")
    values = {
        c: pd.to_numeric(census[c], errors="coerce").to_numpy(dtype=float)
        for c in COVERAGE_SOURCE_COLUMNS
    }
    wg = values["zg_n_exp"] - values["zg_n_nights"]
    finite_wg = wg[np.isfinite(wg)]
    if (finite_wg < 0).any():
        raise SystemExit(
            f"{frame_name}: wg_contrasts = zg_n_exp - zg_n_nights is negative for "
            f"{int((finite_wg < 0).sum())} rows"
        )
    values["wg_contrasts"] = wg
    rows = []
    for metric in COVERAGE_METRICS:
        x = values[metric]
        x = x[np.isfinite(x)]
        if x.size:
            q = np.quantile(x, COVERAGE_QUANTILES, method="linear")
            stats = {"min": float(np.min(x)), "p10": float(q[0]), "p25": float(q[1]),
                     "p50": float(q[2]), "p75": float(q[3]), "p90": float(q[4]),
                     "max": float(np.max(x))}
        else:
            stats = {k: math.nan for k in ("min", "p10", "p25", "p50", "p75", "p90", "max")}
        rows.append({
            "frame": frame_name, "covariate": metric,
            "n_frame": int(len(census)), "n_nonmissing": int(x.size),
            **stats,
            "analysis_status": ANALYSIS_STATUS,
            "prespecified": PRESPECIFIED, "interval": INTERVAL,
        })
    return rows


def coverage_table(d3_census: pd.DataFrame, pool_census: pd.DataFrame,
                   expected_d3: int = EXPECTED_D3_CENSUS_ROWS,
                   expected_pool: int = EXPECTED_POOL_ROWS) -> pd.DataFrame:
    rows = coverage_rows("D3_crossmatched", d3_census, expected_d3)
    rows += coverage_rows("development_pool", pool_census, expected_pool)
    return pd.DataFrame(rows, columns=COVERAGE_COLUMNS)


# ---------------------------------------------------------------- a95

def read_a95_records(stars_dir: Path, sids: list[str]) -> dict[str, dict]:
    """sid -> {"available": {pass: bool}, "a95": {(pass, band): raw value},
    "sha256": ...} for every sid with a JSON in stars_dir. Fail-closed on any
    schema deviation: incomplete result, pass set != {low, high}, or a
    missing `<band>_a95_mmag` key (never guessed as missing data)."""
    records: dict[str, dict] = {}
    for sid in sids:
        path = stars_dir / f"{sid}.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("source_id") != sid:
            raise SystemExit(f"{path}: source_id {result.get('source_id')!r} != {sid}")
        if not result.get("complete"):
            raise SystemExit(f"{path} is not complete")
        passes = result.get("passes")
        if not isinstance(passes, dict) or set(passes) != set(PASSES):
            raise SystemExit(f"{path} passes != low/high")
        available = {}
        a95 = {}
        for pass_name in PASSES:
            p = passes[pass_name]
            available[pass_name] = bool(p.get("available", True))
            for band in BANDS:
                key = f"{band}_a95_mmag"
                if key not in p:
                    raise SystemExit(
                        f"{path}: passes[{pass_name!r}] has no {key!r} key; "
                        "refusing to treat a schema deviation as missing data"
                    )
                a95[(pass_name, band)] = p[key]
        records[sid] = {"available": available, "a95": a95,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return records


def verify_records_against_per_star(roster: pd.DataFrame, records: dict[str, dict],
                                    per_star: pd.DataFrame) -> None:
    """The stars-dir must be the one the frozen metrics bundle scored: a JSON
    exists iff per_star best_status != 'missing', class labels agree, and the
    per-pass availability flags agree."""
    if per_star["sid"].duplicated().any():
        raise SystemExit("duplicate sids in per_star")
    if set(per_star["sid"]) != set(roster["source_id"]):
        raise SystemExit("per_star sid set != roster sid set (not a FULL D3 bundle?)")
    ps = per_star.set_index("sid")
    roster_labels = roster.set_index("source_id")["class_label"]
    for sid, label in roster_labels.items():
        if ps.at[sid, "class_label"] != label:
            raise SystemExit(f"{sid}: per_star class_label != roster class_label")
        has_json = sid in records
        scored = ps.at[sid, "best_status"] != "missing"
        if has_json != scored:
            raise SystemExit(
                f"{sid}: JSON {'present' if has_json else 'absent'} but per_star "
                f"best_status is {ps.at[sid, 'best_status']!r}; stars-dir does not "
                "match the metrics bundle"
            )
        if has_json:
            for pass_name in PASSES:
                flag = _as_bool(ps.at[sid, f"{pass_name}_available"])
                if flag is None or flag != records[sid]["available"][pass_name]:
                    raise SystemExit(
                        f"{sid}: {pass_name}_available disagrees between the JSON "
                        "and per_star"
                    )


def a95_table(roster: pd.DataFrame, records: dict[str, dict],
              expected_roster: int = EXPECTED_ROSTER) -> pd.DataFrame:
    if len(roster) != expected_roster:
        raise SystemExit(f"roster has {len(roster)} rows != {expected_roster}")
    if roster["source_id"].duplicated().any():
        raise SystemExit("duplicate source_id in the roster")
    levels = set(roster["class_label"])
    if levels != set(CLASS_LEVELS):
        raise SystemExit(f"roster class levels {sorted(levels)} != {list(CLASS_LEVELS)}")
    extra = set(records) - set(roster["source_id"])
    if extra:
        raise SystemExit(f"a95 records for {len(extra)} non-roster ids")
    rows = []
    for label in CLASS_LEVELS:
        sids = roster.loc[roster["class_label"] == label, "source_id"].tolist()
        n_roster = len(sids)
        recs = [records[s] for s in sids if s in records]
        n_json = len(recs)
        for pass_name in PASSES:
            n_available = sum(1 for r in recs if r["available"][pass_name])
            for band in BANDS:
                raw = [r["a95"][(pass_name, band)] for r in recs]
                x = np.asarray([float(v) for v in raw if _finite(v)], dtype=float)
                n_finite = int(x.size)
                if n_finite:
                    q = np.quantile(x, A95_QUANTILES, method="linear")
                    stats = {"min": float(np.min(x)), "p05": float(q[0]), "p10": float(q[1]),
                             "p25": float(q[2]), "p50": float(q[3]), "p75": float(q[4]),
                             "p90": float(q[5]), "p95": float(q[6]), "max": float(np.max(x))}
                else:
                    stats = {k: math.nan for k in
                             ("min", "p05", "p10", "p25", "p50", "p75", "p90", "p95", "max")}
                rows.append({
                    "class_label": label, "pass": pass_name, "band": band,
                    "n_roster": n_roster, "n_json": n_json,
                    "n_pass_available": n_available,
                    "n_finite": n_finite, "n_missing": n_roster - n_finite,
                    **stats,
                    "analysis_status": ANALYSIS_STATUS,
                    "prespecified": PRESPECIFIED, "interval": INTERVAL,
                })
    table = pd.DataFrame(rows, columns=A95_COLUMNS)
    if len(table) != len(CLASS_LEVELS) * len(PASSES) * len(BANDS):  # pragma: no cover
        raise SystemExit("a95 table does not hold every class x pass x band cell")
    return table


# ---------------------------------------------------------------- CLI

def check_metrics_manifest(manifest: dict) -> None:
    if manifest.get("dataset") != "d3":
        raise SystemExit("metrics bundle is not dataset d3")
    if manifest.get("pilot"):
        raise SystemExit("pilot metrics bundle: the descriptive coverage/a95 tables are FULL-run only")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--stars-dir", type=Path, required=True,
                        help="per-star result JSONs the metrics bundle scored")
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER,
                        help="frozen 3,000-row D3 roster")
    parser.add_argument("--d3-census", type=Path, default=DEFAULT_D3_CENSUS,
                        help="frozen 2,901-row D3 census panel")
    parser.add_argument("--pool-census", type=Path, default=DEFAULT_POOL_CENSUS,
                        help="published 928-row development-pool census catalog")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args()

    assert_frozen()
    metrics_manifest_path = args.metrics_dir / "manifest.json"
    check_metrics_manifest(json.loads(metrics_manifest_path.read_text(encoding="utf-8")))
    per_star_path = args.metrics_dir / "per_star.csv"
    per_star = pd.read_csv(per_star_path, dtype={"sid": str})
    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    d3_census = pd.read_csv(args.d3_census, dtype={"source_id": str})
    pool_census = pd.read_csv(args.pool_census, dtype={"source_id": str})
    if not set(d3_census["source_id"]) <= set(roster["source_id"]):
        raise SystemExit("D3 census panel lists ids outside the roster")

    coverage = coverage_table(d3_census, pool_census)
    records = read_a95_records(args.stars_dir, roster["source_id"].tolist())
    verify_records_against_per_star(roster, records, per_star)
    a95 = a95_table(roster, records)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    coverage_csv = args.out_dir / "d3_vs_pool_coverage.csv"
    a95_csv = args.out_dir / "d3_a95_by_class_pass_band.csv"
    coverage.to_csv(coverage_csv, index=False, lineterminator="\n")
    a95.to_csv(a95_csv, index=False, lineterminator="\n")
    readme = args.out_dir / "d3_coverage_a95.README.md"
    readme.write_text(
        "# D3 vs pool coverage and per-pass a95 by class (descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n"
        f"Admission: {VERDICT_FILE}, item 7 (F16/F18, ADMIT-DESCRIPTIVE).\n"
        "Coverage frames: D3_crossmatched = all 2,901 D3 census-panel rows;\n"
        "development_pool = all 928 census_full_catalog.csv rows;\n"
        "wg_contrasts = zg_n_exp - zg_n_nights (asserted nonnegative); linear\n"
        "quantiles; the frames are never pooled. a95 values are read directly\n"
        "from passes[pass][band + \"_a95_mmag\"] of the per-star JSONs, crossed\n"
        "class x pass x band with no pooling across bands; n_missing =\n"
        "n_roster - n_finite. No interval, endpoint, exclusion,\n"
        "reclassification, or ZTF-wide transfer claim.\n",
        encoding="utf-8",
    )
    verdict_path = REPO_ROOT / VERDICT_FILE
    json_digest = hashlib.sha256(
        "".join(f"{sid}:{records[sid]['sha256']}\n" for sid in sorted(records)).encode()
    ).hexdigest()
    manifest = {
        "analysis_status": ANALYSIS_STATUS,
        "prespecified": PRESPECIFIED,
        "interval": INTERVAL,
        "verdict_file": VERDICT_FILE,
        "constants": {
            "coverage_frames": {name: n for name, n in COVERAGE_FRAMES},
            "coverage_metrics": list(COVERAGE_METRICS),
            "wg_contrasts": "zg_n_exp - zg_n_nights",
            "a95_key_path": 'passes[pass][band + "_a95_mmag"]',
            "quantile_method": "linear",
        },
        "inputs_sha256": {
            "per_star.csv": sha256_file(per_star_path),
            "metrics_manifest.json": sha256_file(metrics_manifest_path),
            input_label(args.roster): sha256_file(args.roster),
            input_label(args.d3_census): sha256_file(args.d3_census),
            input_label(args.pool_census): sha256_file(args.pool_census),
            **({VERDICT_FILE: sha256_file(verdict_path)} if verdict_path.exists() else {}),
        },
        "stars_dir": {
            "path": str(args.stars_dir),
            "n_json_read": len(records),
            "sha256_digest_of_sorted_sid_sha_lines": json_digest,
        },
        "outputs_sha256": {
            "d3_vs_pool_coverage.csv": sha256_file(coverage_csv),
            "d3_a95_by_class_pass_band.csv": sha256_file(a95_csv),
        },
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "frozen_sha256": frozen_file_shas(),
        "campaign_sha256": campaign_file_shas(),
        "counts": {
            "n_roster": int(len(roster)),
            "n_by_class": {
                label: int((roster["class_label"] == label).sum()) for label in CLASS_LEVELS
            },
            "n_json_by_class": {
                label: int(a95.loc[a95["class_label"] == label, "n_json"].iloc[0])
                for label in CLASS_LEVELS
            },
        },
    }
    (args.out_dir / "d3_coverage_a95.manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(coverage.to_string(index=False))
    print(a95.to_string(index=False))
    print(f"[coverage_a95] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
