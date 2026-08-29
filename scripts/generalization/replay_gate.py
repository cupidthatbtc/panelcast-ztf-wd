#!/usr/bin/env python3
"""Replay gate: reproduce published 2026-08-01 per-star results byte-for-byte.

Re-runs the frozen `analyze_star` (imported through frozen_api, exactly as the
campaign driver will) on a deterministic sample of published stars and compares
the fresh output against the committed bundle files.

Comparison tiers, strongest first:
  identical                  raw bytes equal
  identical_newline          equal after CRLF->LF normalization (git stored the
                             bundle newline-normalized; Windows writes CRLF)
  identical_v1_schema        equal after the documented v1->v2 schema transform:
                             the run that produced 921/928 published files
                             predates commit fa16d7f, which added sparse-input
                             early-exit branches plus the `available`/
                             `unavailable_reason` keys and bumped schema_version
                             1->2; for any star that yields candidates the
                             numeric path is unchanged (the new branches fire
                             only on sparse inputs that previously crashed).
                             The replayed output is re-serialized with
                             schema_version=1 and those two keys dropped, then
                             byte-compared against the published file.
  MISMATCH                   anything else; the first differing JSON path is
                             reported. The gate FAILS.

The gate passes only if every sampled star lands in one of the identical tiers
AND at least one schema-v2 star reproduces with no transform (proving full-byte
reproduction of the final script's output). Campaign L-S runs are valid only on
machine+env combinations where this gate has passed.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import math

from frozen_api import (
    REPO_ROOT,
    analyze_star,
    assert_frozen,
    campaign_file_shas,
    env_versions,
    grid_for,
    json_ready,
    overall_result,
    physical_workers,
)

PUBLISHED_STARS = (
    REPO_ROOT / "catalog-rebuild/results/2026-08-01_full/lomb-scargle/stars"
)


def normalize(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def project_v1(replayed: dict) -> dict:
    """The documented v1->v2 projection (commit fa16d7f added two keys)."""
    downgraded = dict(replayed)
    downgraded["schema_version"] = 1
    downgraded["passes"] = {
        name: {k: v for k, v in pass_result.items()
               if k not in ("available", "unavailable_reason")}
        for name, pass_result in replayed["passes"].items()
    }
    return downgraded


def schema_v1_bytes(replayed: dict) -> bytes:
    downgraded = dict(replayed)
    downgraded["schema_version"] = 1
    downgraded["passes"] = {
        name: {
            key: value
            for key, value in pass_result.items()
            if key not in ("available", "unavailable_reason")
        }
        for name, pass_result in replayed["passes"].items()
    }
    text = json.dumps(downgraded, indent=2, default=json_ready) + "\n"
    return text.encode("utf-8")


def first_difference(published: object, replayed: object, path: str = "$") -> str:
    if type(published) is not type(replayed):
        return f"{path}: type {type(published).__name__} != {type(replayed).__name__}"
    if isinstance(published, dict):
        for key in sorted(set(published) | set(replayed)):
            if key not in published:
                return f"{path}.{key}: only in replay"
            if key not in replayed:
                return f"{path}.{key}: only in published"
            diff = first_difference(published[key], replayed[key], f"{path}.{key}")
            if diff:
                return diff
        return ""
    if isinstance(published, list):
        if len(published) != len(replayed):
            return f"{path}: length {len(published)} != {len(replayed)}"
        for index, (left, right) in enumerate(zip(published, replayed)):
            diff = first_difference(left, right, f"{path}[{index}]")
            if diff:
                return diff
        return ""
    if published != replayed:
        return f"{path}: {published!r} != {replayed!r}"
    return ""


DECISION_FIELDS = ("status", "basis", "zg_alias", "zr_alias", "multiband_top5",
                   "available", "unavailable_reason")
PEAK_FLAG_FIELDS = ("series", "rank", "alias_flag", "window_alias",
                    "stronger_peak_sidereal_alias")
F32_READBACK_KEYS = {"power"}  # only when series == "multiband" (raw memmap readback)


def grid_index(frequency: float, pass_name: str, baseline: float) -> int:
    grid = grid_for(pass_name, baseline)
    return int(round((frequency - grid.minimum) / grid.step))


def decision_equivalence(published: dict, replayed: dict) -> dict:
    """Report-only diagnostic (does NOT affect the strict pass criterion).
    FAIL-CLOSED: any structural difference (missing key, list length,
    nonfinite value, pass presence) is a recorded problem; decisions are
    identical only when the problem list is empty."""
    problems: list[str] = []
    f64_worst = f32_worst = a95_worst = 0.0
    n_numeric = 0
    baseline = float(published.get("baseline_days", 0.0) or 0.0)
    if replayed.get("baseline_days") != published.get("baseline_days"):
        problems.append("baseline_days differs")

    def rel(a: float, b: float) -> float:
        return abs(a - b) / max(abs(a), abs(b), 1e-300)

    def walk(a, b, path, key="", series=None):
        nonlocal f64_worst, f32_worst, n_numeric
        if isinstance(a, dict) != isinstance(b, dict) or isinstance(a, list) != isinstance(b, list):
            problems.append(f"{path}: type differs"); return
        if isinstance(a, dict):
            if set(a) != set(b):
                problems.append(f"{path}: keys differ {sorted(set(a) ^ set(b))[:4]}")
            for k in a:
                if k in b and not k.endswith("_a95_mmag"):
                    walk(a[k], b[k], f"{path}.{k}", k, a.get("series", series))
            return
        if isinstance(a, list):
            if len(a) != len(b):
                problems.append(f"{path}: length {len(a)} != {len(b)}"); return
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", key, series)
            return
        if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
            if a != b:
                problems.append(f"{path}: {a!r} != {b!r}")
            return
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            n_numeric += 1
            fa, fb = float(a), float(b)
            if not (math.isfinite(fa) and math.isfinite(fb)):
                if not (math.isnan(fa) and math.isnan(fb)) and fa != fb:
                    problems.append(f"{path}: nonfinite {a!r} vs {b!r}")
                return
            if fa != fb:
                if key in F32_READBACK_KEYS and series == "multiband":
                    f32_worst = max(f32_worst, rel(fa, fb))
                else:
                    f64_worst = max(f64_worst, rel(fa, fb))
            return
        if a != b:
            problems.append(f"{path}: {a!r} != {b!r}")

    for pass_name in ("low", "high"):
        pa = published["passes"].get(pass_name)
        pb = replayed["passes"].get(pass_name)
        if (pa is None) != (pb is None):
            problems.append(f"{pass_name}: pass presence differs"); continue
        if pa is None:
            continue
        for key in DECISION_FIELDS:
            if pa.get(key) != pb.get(key):
                problems.append(f"{pass_name}.{key}: {pa.get(key)!r} != {pb.get(key)!r}")
        fa, fb = pa.get("frequency_per_day"), pb.get("frequency_per_day")
        if (fa is None) != (fb is None):
            problems.append(f"{pass_name}.frequency: presence differs")
        elif fa is not None:
            if rel(fa, fb) > 1e-12:
                problems.append(f"{pass_name}.frequency: {fa} != {fb}")
            elif baseline and grid_index(fa, pass_name, baseline) != grid_index(fb, pass_name, baseline):
                problems.append(f"{pass_name}.frequency: grid index differs")
        ta, tb = pa.get("top_peaks", []), pb.get("top_peaks", [])
        if len(ta) != len(tb):
            problems.append(f"{pass_name}.top_peaks: length {len(ta)} != {len(tb)}")
        for i, (x, y) in enumerate(zip(ta, tb)):
            for key in PEAK_FLAG_FIELDS:
                if x.get(key) != y.get(key):
                    problems.append(f"{pass_name}.top_peaks[{i}].{key}: {x.get(key)!r} != {y.get(key)!r}")
            fx, fy = x.get("frequency_per_day"), y.get("frequency_per_day")
            if fx is None or fy is None or rel(fx, fy) > 1e-12 or (
                    baseline and grid_index(fx, pass_name, baseline) != grid_index(fy, pass_name, baseline)):
                problems.append(f"{pass_name}.top_peaks[{i}]: grid position differs")
        for band in ("zg", "zr"):
            x, y = pa.get(f"{band}_a95_mmag"), pb.get(f"{band}_a95_mmag")
            if (x is None) != (y is None):
                problems.append(f"{pass_name}.{band}_a95: presence differs")
            elif x is not None and y is not None:
                if not (math.isfinite(x) and math.isfinite(y)):
                    if not (math.isnan(x) and math.isnan(y)):
                        problems.append(f"{pass_name}.{band}_a95: nonfinite")
                elif x == 0 or y == 0:
                    if x != y:
                        problems.append(f"{pass_name}.{band}_a95: zero vs nonzero")
                else:
                    a95_worst = max(a95_worst, rel(x, y))
    walk(published["passes"], replayed["passes"], "passes")
    # derived OVERALL identity (best pass chosen by status then best_band_fap)
    try:
        oa, ob = overall_result(published), overall_result(replayed)
        for key in ("best_pass", "blind_status", "basis"):
            if oa.get(key) != ob.get(key):
                problems.append(f"overall.{key}: {oa.get(key)!r} != {ob.get(key)!r}")
        fa, fb = oa.get("best_frequency_per_day"), ob.get("best_frequency_per_day")
        if (fa is None) != (fb is None) or (fa is not None and rel(fa, fb) > 1e-12):
            problems.append("overall.best_frequency differs")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"overall_result failed: {exc!r}")
    return {"decisions_identical": not problems,
            "top_peaks_identical": not any("top_peaks" in q for q in problems),
            "problems": problems[:12],
            "numeric_fields": n_numeric,
            "f64_max_relative_difference": f64_worst,
            "f32_power_max_relative_difference": f32_worst,
            "a95_max_relative_difference": a95_worst}


def published_schema_version(path: Path) -> int:
    return int(json.loads(path.read_text(encoding="utf-8"))["schema_version"])


def select_stars(published_dir: Path, shard_dir: Path, count: int) -> list[str]:
    available = {
        path.name.split(".csv")[0] for path in shard_dir.glob("*.csv.gz")
    }
    stars = sorted(
        path.stem
        for path in published_dir.glob("*.json")
        if not path.name.endswith(".error.json") and path.stem in available
    )
    if not stars:
        raise SystemExit(f"no published stars have shards in {shard_dir}")
    v2 = [star for star in stars if published_schema_version(published_dir / f"{star}.json") == 2]
    v1 = [star for star in stars if star not in set(v2)]
    selected = list(v2)[:count]
    remaining = count - len(selected)
    if remaining > 0 and v1:
        stride = max(1, len(v1) // remaining)
        selected.extend(v1[::stride][:remaining])
    return sorted(selected)


def compare_star(star: str, published_dir: Path, replay_dir: Path) -> dict[str, object]:
    published_path = published_dir / f"{star}.json"
    replay_path = replay_dir / f"{star}.json"
    published_raw = published_path.read_bytes()
    replay_raw = replay_path.read_bytes()
    record: dict[str, object] = {
        "source_id": star,
        "published_schema_version": published_schema_version(published_path),
    }
    if published_raw == replay_raw:
        record["verdict"] = "identical"
        return record
    published_norm = normalize(published_raw)
    replay_norm = normalize(replay_raw)
    if published_norm == replay_norm:
        record["verdict"] = "identical_newline"
        return record
    replayed = json.loads(replay_norm.decode("utf-8"))
    if normalize(schema_v1_bytes(replayed)) == published_norm:
        record["verdict"] = "identical_v1_schema"
        return record
    record["verdict"] = "MISMATCH"
    published_obj = json.loads(published_norm.decode("utf-8"))
    compared = project_v1(replayed) if record["published_schema_version"] == 1 else replayed
    record["first_difference"] = first_difference(published_obj, compared)
    record["decision_equivalence"] = decision_equivalence(published_obj, compared)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-dir", type=Path, required=True,
                        help="directory of <source_id>.csv.gz exposure shards")
    parser.add_argument("--published-stars", type=Path, default=PUBLISHED_STARS)
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "outputs/generalization/replay_gate")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--stars", nargs="*", help="explicit star list (overrides --count)")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--resume", action="store_true",
                        help="keep complete per-star outputs already produced by a "
                             "previous run of THIS gate in the same out-dir (same code "
                             "+ env, verified by the drift/attestation checks) instead "
                             "of recomputing them; crash recovery for the full-928 run")
    args = parser.parse_args()

    assert_frozen()
    campaign_start = campaign_file_shas()
    workers = args.workers or physical_workers()
    replay_dir = args.out_dir / "stars"
    work_dir = args.out_dir / "work"
    replay_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    stars = args.stars or select_stars(args.published_stars, args.shard_dir, args.count)
    missing = [s for s in stars if not (args.shard_dir / f"{s}.csv.gz").exists()]
    if missing:
        raise SystemExit(f"missing shards for: {missing}")
    reused = 0
    for star in stars:
        existing = replay_dir / f"{star}.json"
        if args.resume and existing.exists():
            try:
                if json.loads(existing.read_text(encoding="utf-8")).get("complete"):
                    reused += 1
                    continue
            except json.JSONDecodeError:
                pass
        existing.unlink(missing_ok=True)
    if reused:
        print(f"[replay] resume: reusing {reused} complete outputs", flush=True)

    print(f"[replay] {len(stars)} stars, workers={workers}", flush=True)
    started = time.time()
    durations: dict[str, float] = {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                analyze_star,
                star,
                str(args.shard_dir / f"{star}.csv.gz"),
                str(replay_dir / f"{star}.json"),
                str(work_dir),
                ("low", "high"),
            ): (star, time.time())
            for star in stars
        }
        for future in as_completed(futures):
            star, _ = futures[future]
            future.result()
            durations[star] = round(time.time() - started, 1)
            print(f"[replay] finished {star} (+{durations[star]}s)", flush=True)

    records = [compare_star(star, args.published_stars, replay_dir) for star in stars]
    verdicts = {record["source_id"]: record["verdict"] for record in records}
    counts: dict[str, int] = {}
    for verdict in verdicts.values():
        counts[verdict] = counts.get(verdict, 0) + 1
    if not records:
        raise SystemExit("empty replay roster — the gate cannot pass vacuously")
    strict_v2 = any(
        record["verdict"] in ("identical", "identical_newline")
        and record["published_schema_version"] == 2
        for record in records
    )
    # strict_v2 is unconditional (G1 methods finding 2): a schema-v2 star that
    # reproduces with no transform is the proof of full-byte reproduction, and
    # the published bundle contains 7 of them — a roster without one is invalid.
    passed = all(record["verdict"] != "MISMATCH" for record in records) and strict_v2

    report = {
        "gate": "replay_gate",
        "passed": passed,
        "verdict_counts": counts,
        "stars": records,
        "wall_seconds": round(time.time() - started, 1),
        "completion_offsets_seconds": durations,
        "workers": workers,
        "resumed_outputs": reused,
        "env": env_versions(),
        "frozen_sha256": assert_frozen(),
        "campaign_sha256": campaign_start,
        "roster_digest": __import__("hashlib").sha256(
            ",".join(stars).encode()).hexdigest(),
        "roster_size": len(stars),
    }
    if campaign_file_shas() != campaign_start:
        raise SystemExit("campaign code changed while the gate ran — report void")
    report_path = args.out_dir / "replay_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[replay] {'PASS' if passed else 'FAIL'} {counts} -> {report_path}", flush=True)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
