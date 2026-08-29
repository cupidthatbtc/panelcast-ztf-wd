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
                             predates commit fa16d7f, which added the
                             `available`/`unavailable_reason` keys and bumped
                             schema_version 1->2 while changing no numeric path.
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

from frozen_api import (
    REPO_ROOT,
    analyze_star,
    assert_frozen,
    env_versions,
    json_ready,
    physical_workers,
)

PUBLISHED_STARS = (
    REPO_ROOT / "catalog-rebuild/results/2026-08-01_full/lomb-scargle/stars"
)


def normalize(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


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
    record["first_difference"] = first_difference(
        json.loads(published_norm.decode("utf-8")), replayed
    )
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
    args = parser.parse_args()

    assert_frozen()
    workers = args.workers or physical_workers()
    replay_dir = args.out_dir / "stars"
    work_dir = args.out_dir / "work"
    replay_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    stars = args.stars or select_stars(args.published_stars, args.shard_dir, args.count)
    missing = [s for s in stars if not (args.shard_dir / f"{s}.csv.gz").exists()]
    if missing:
        raise SystemExit(f"missing shards for: {missing}")
    for star in stars:
        (replay_dir / f"{star}.json").unlink(missing_ok=True)

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
        "env": env_versions(),
        "frozen_sha256": assert_frozen(),
    }
    report_path = args.out_dir / "replay_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[replay] {'PASS' if passed else 'FAIL'} {counts} -> {report_path}", flush=True)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
