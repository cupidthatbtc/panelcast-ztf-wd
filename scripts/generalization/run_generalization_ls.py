#!/usr/bin/env python3
"""Resumable, shardable campaign driver over the frozen analyze_star.

This is the ONLY way campaign Lomb-Scargle searches run. It imports
analyze_star through frozen_api (SHA-gated) and never invokes the frozen CLI,
whose main() would merge against the WD roster and rewrite the published
catalog table. Per-star JSONs are the product; no roster merge, no CSV — the
campaign metrics read the JSONs directly (METRICS_SPEC.md).

Resumability is inherited from analyze_star: a complete result file is
returned untouched, so re-running after a crash or shard split is safe.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from frozen_api import (
    analyze_star,
    assert_frozen,
    campaign_file_shas,
    campaign_id_ok,
    env_versions,
    frozen_file_shas,
    physical_workers,
)

# environment keys that must match between the replay attestation and this run
ATTESTATION_KEYS = ("python", "numpy", "scipy", "astropy", "astropy_iers_data",
                    "pyerfa", "pandas", "machine")


def validate_attestation(report_path: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report.get("passed"):
        raise SystemExit(f"replay attestation {report_path} is not a PASS")
    current = env_versions()
    mismatched = [
        key for key in ATTESTATION_KEYS
        if report["env"].get(key) != current.get(key)
    ]
    if mismatched:
        raise SystemExit(
            f"replay attestation env differs from this run: {mismatched} "
            f"(attested {[report['env'].get(k) for k in mismatched]} vs "
            f"current {[current.get(k) for k in mismatched]})"
        )
    if report.get("frozen_sha256") != frozen_file_shas():
        raise SystemExit("replay attestation frozen SHAs differ from this checkout")
    return report

# One in-flight star holds two full-resolution float32 periodogram memmaps plus
# the multiband combination on scratch; the worst published-catalog baseline
# needs 0.471 GB for the three high-pass memmaps, so 0.52 adds ~10% headroom
# for longer campaign baselines. Disk, not wall time, binds worker count.
SCRATCH_GB_PER_WORKER = 0.52


def preflight_workers(requested: int | None, work_root: Path) -> tuple[int, float]:
    if requested is not None and requested < 1:
        raise SystemExit(f"invalid --workers {requested}")
    free_gb = shutil.disk_usage(work_root).free / 1e9
    ceiling = int(free_gb * 0.5 / SCRATCH_GB_PER_WORKER)
    if ceiling < 1:
        raise SystemExit(
            f"scratch {work_root} has {free_gb:.1f} GB free — below one worker's "
            f"{SCRATCH_GB_PER_WORKER} GB requirement"
        )
    workers = min(requested or physical_workers(), physical_workers(), ceiling)
    return workers, free_gb


def scan_pending(shard_dir: Path, star_dir: Path, passes: tuple[str, ...],
                 only: set[str] | None, limit: int | None) -> tuple[list[str], int]:
    source_ids = sorted(path.name.split(".csv")[0] for path in shard_dir.glob("*.csv.gz"))
    if only is not None:
        missing = only - set(source_ids)
        if missing:
            raise SystemExit(f"requested stars absent from shards: {sorted(missing)[:5]}...")
        source_ids = [sid for sid in source_ids if sid in only]
    if limit is not None:
        source_ids = source_ids[:limit]
    pending = []
    for source_id in source_ids:
        result_path = star_dir / f"{source_id}.json"
        if result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                if result.get("complete") and set(result.get("passes", {})) >= set(passes):
                    continue
            except json.JSONDecodeError:
                pass
        pending.append(source_id)
    return pending, len(source_ids)


def write_progress(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".json.part")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=None,
                        help="scratch for periodogram memmaps; put on local NVMe "
                             "or a RAM disk, NEVER inside a synced folder")
    parser.add_argument("--dataset", required=True,
                        help="manifest label, e.g. d3-kepler-dsct or d2-tess-dav")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--passes", default="low,high")
    parser.add_argument("--stars-file", type=Path, default=None,
                        help="optional newline-separated campaign_id subset (a shard)")
    parser.add_argument("--limit", type=int, default=None,
                        help="pilot mode: first N stars only")
    parser.add_argument("--allow-nonstandard-ids", action="store_true",
                        help="permit non-campaign source_ids (replay/debug only)")
    parser.add_argument("--replay-report", type=Path, required=True,
                        help="replay_report.json from a PASSING replay_gate run "
                             "on THIS machine+env; campaign runs refuse to start "
                             "without one (G1 methods finding 1)")
    args = parser.parse_args()

    assert_frozen()
    attestation = validate_attestation(args.replay_report)
    passes = tuple(args.passes.split(","))
    if passes != ("low", "high") and not args.allow_nonstandard_ids:
        raise SystemExit("production runs use exactly low,high (the frozen CLI's "
                         "pass set); pass --allow-nonstandard-ids for debug runs")
    star_dir = args.out_dir / "stars"
    work_root = args.work_root or (args.out_dir / "work")
    star_dir.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)

    only = None
    if args.stars_file:
        only = {line.strip() for line in args.stars_file.read_text().splitlines() if line.strip()}
    pending, total = scan_pending(args.shard_dir, star_dir, passes, only, args.limit)

    if not args.allow_nonstandard_ids:
        bad = [sid for sid in pending if not campaign_id_ok(sid)]
        if bad:
            raise SystemExit(
                f"{len(bad)} shard ids violate the campaign 19-digit prefix "
                f"convention (first: {bad[:3]}); refusing to run"
            )

    workers, free_gb = preflight_workers(args.workers, work_root)
    print(
        f"[{args.dataset}] sources={total:,} pending={len(pending):,} "
        f"workers={workers} (free {free_gb:.0f} GB on scratch)",
        flush=True,
    )

    progress_path = args.out_dir / "progress.json"
    started = time.time()
    failures: dict[str, str] = {}
    completed_now = 0

    def progress_payload() -> dict:
        elapsed = time.time() - started
        rate = completed_now / elapsed if elapsed > 0 else 0.0
        return {
            "dataset": args.dataset,
            "total": total,
            "pending_at_start": len(pending),
            "completed_now": completed_now,
            "failed": len(failures),
            "elapsed_seconds": round(elapsed, 1),
            "stars_per_hour": round(rate * 3600.0, 2),
            "eta_hours": round((len(pending) - completed_now - len(failures)) / (rate * 3600.0), 2)
            if rate > 0
            else None,
            "workers": workers,
        }

    write_progress(progress_path, progress_payload())
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                analyze_star,
                source_id,
                str(args.shard_dir / f"{source_id}.csv.gz"),
                str(star_dir / f"{source_id}.json"),
                str(work_root),
                passes,
            ): source_id
            for source_id in pending
        }
        for future in as_completed(futures):
            source_id = futures[future]
            try:
                future.result()
                completed_now += 1
            except Exception as exc:
                failures[source_id] = repr(exc)
                print(f"[{args.dataset}] FAILED {source_id}: {exc}", flush=True)
            if completed_now % 10 == 0 or completed_now + len(failures) == len(pending):
                write_progress(progress_path, progress_payload())
                print(
                    f"[{args.dataset}] {completed_now:,}/{len(pending):,} "
                    f"({progress_payload()['stars_per_hour']}/h)",
                    flush=True,
                )

    manifest = {
        "dataset": args.dataset,
        "driver": "run_generalization_ls.py",
        "source_count": total,
        "pending_at_start": len(pending),
        "completed_now": completed_now,
        "failures": failures,
        "passes": list(passes),
        "workers": workers,
        "wall_seconds": round(time.time() - started, 1),
        "shard_dir": str(args.shard_dir),
        "env": env_versions(),
        "frozen_sha256": assert_frozen(),
        "campaign_sha256": campaign_file_shas(),
        "replay_attestation": {
            "path": str(args.replay_report),
            "wall_seconds": attestation.get("wall_seconds"),
            "verdict_counts": attestation.get("verdict_counts"),
        },
    }
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    write_progress(progress_path, progress_payload())
    print(f"[{args.dataset}] done: {completed_now:,} completed, {len(failures)} failed", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
