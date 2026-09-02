#!/usr/bin/env python3
"""Resumable, shardable v2 campaign driver (copy of run_generalization_ls.py's
discipline over analyze_star_v2).

Differences from the frozen driver, all deliberate:
  * no replay attestation — v2 is NOT byte-frozen; the manifest records
    `attestation_sha256 = "v2-unattested"` and the machine label;
  * binding = {engine, v2_digest, frozen_digest, constants_sha256,
    generation_id}: a result is reused on resume only if the v2 code, the
    frozen helpers, the constants, the environment and the shard bytes are
    unchanged. The campaign digest (scripts/generalization/*.py) is recorded
    for audit but is NOT part of the binding: v2 numerics never depend on it,
    and binding it would void a live run whenever the metrics module is
    edited;
  * --machine label, --constants (declared candidate values only) and
    --split-file / --allow-holdout: with a split file, the requested ids must
    all belong to ONE half; holdout ids refuse to run without --allow-holdout
    (the holdout is scored once, after the dev constants are fixed).
Same sidecars, completion.csv, IN_PROGRESS refusal, resume-safe scan.
"""

from __future__ import annotations

import argparse
import datetime
import functools
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

V2_DIR = Path(__file__).resolve().parent
if str(V2_DIR) not in sys.path:
    sys.path.insert(0, str(V2_DIR))

from analyze_star_v2 import analyze_star_v2  # noqa: E402
from v2_common import (  # noqa: E402
    DEFAULT,
    ENGINE,
    REPO_ROOT,
    SCHEMA_VERSION,
    V2Constants,
    campaign_digest,
    campaign_file_shas,
    env_digest,
    env_versions,
    frozen_api,
    frozen_digest,
    frozen_file_shas,
    v2_digest,
    v2_file_shas,
    with_overrides,
)

DRIVER = "run_v2_ls.py"
UNATTESTED = "v2-unattested"
# three float32 memmaps per pass (zg, zr, joint) as the frozen driver; the
# spectral window is computed in RAM on the x10-subsampled grid
SCRATCH_GB_PER_WORKER = 0.52


def physical_workers() -> int:
    return frozen_api.physical_workers()


def preflight_workers(requested: int | None, work_root: Path) -> tuple[int, float]:
    if requested is not None and requested < 1:
        raise SystemExit(f"invalid --workers {requested}")
    free_gb = shutil.disk_usage(work_root).free / 1e9
    ceiling = int(free_gb * 0.5 / SCRATCH_GB_PER_WORKER)
    if ceiling < 1:
        raise SystemExit(f"scratch {work_root} has {free_gb:.1f} GB free")
    workers = min(requested or physical_workers(), physical_workers(), ceiling)
    return workers, free_gb


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def constants_sha256(constants: V2Constants) -> str:
    return hashlib.sha256(json.dumps(constants.as_dict(), sort_keys=True).encode()).hexdigest()


def provenance_path(star_dir: Path, source_id: str) -> Path:
    return star_dir / f"{source_id}.prov.json"


def write_provenance(star_dir: Path, source_id: str, shard: Path,
                     passes: tuple[str, ...], binding: dict, machine: str) -> None:
    result_path = star_dir / f"{source_id}.json"
    provenance_path(star_dir, source_id).write_text(
        json.dumps({
            "source_id": source_id,
            "passes": list(passes),
            "shard_sha256": sha256_file(shard),
            "result_sha256": sha256_file(result_path),
            "env_digest": env_digest(),
            "driver": DRIVER,
            "machine": machine,
            **binding,
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def scan_pending(shard_dir: Path, star_dir: Path, passes: tuple[str, ...],
                 only: set[str] | None, limit: int | None,
                 binding: dict) -> tuple[list[str], list[str]]:
    source_ids = sorted(path.name.split(".csv")[0] for path in shard_dir.glob("*.csv.gz"))
    if only is not None:
        missing = only - set(source_ids)
        if missing:
            raise SystemExit(f"requested stars absent from shards: {sorted(missing)[:5]}...")
        source_ids = [sid for sid in source_ids if sid in only]
    if limit is not None:
        source_ids = source_ids[:limit]
    current_env = env_digest()
    pending = []
    for source_id in source_ids:
        result_path = star_dir / f"{source_id}.json"
        prov_file = provenance_path(star_dir, source_id)
        if result_path.exists() and prov_file.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                prov = json.loads(prov_file.read_text(encoding="utf-8"))
                if (
                    result.get("complete")
                    and result.get("schema_version") == SCHEMA_VERSION
                    and result.get("source_id") == source_id
                    and set(result.get("passes", {})) >= set(passes)
                    and prov.get("source_id") == source_id
                    and set(prov.get("passes", [])) == set(passes)
                    and prov.get("shard_sha256") == sha256_file(shard_dir / f"{source_id}.csv.gz")
                    and prov.get("result_sha256") == sha256_file(result_path)
                    and prov.get("env_digest") == current_env
                    and all(prov.get(key) == value for key, value in binding.items())
                ):
                    continue
            except json.JSONDecodeError:
                pass
        result_path.unlink(missing_ok=True)
        prov_file.unlink(missing_ok=True)
        pending.append(source_id)
    return pending, source_ids


def write_progress(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".json.part")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


FROZEN_CONSTANTS_NAME = "V2_CONSTANTS_FROZEN.json"
CANONICAL_REGISTRATION = (REPO_ROOT / "generalization" / "v2").resolve()


def registration_root() -> Path:
    """The registration directory (split, lists, plan, constants artifact,
    locks). Canonical = generalization/v2; the V2_REGISTRATION_ROOT
    environment variable exists for the test suite only — a run under a
    non-canonical root is marked canonical_registration = false in its
    manifest and is refused by the comparison."""
    return Path(os.environ.get("V2_REGISTRATION_ROOT", str(CANONICAL_REGISTRATION))).resolve()


def canonical_holdout_ids() -> set[str]:
    """Every registered holdout id of both datasets (from the CANONICAL
    registration, whatever the root in use): a debug or unregistered run may
    never touch them."""
    ids: set[str] = set()
    for name in ("d3_holdout.txt", "d2_holdout.txt"):
        path = CANONICAL_REGISTRATION / name
        if path.exists():
            ids |= {line.strip() for line in path.read_text().splitlines() if line.strip()}
    return ids


def verify_preregistration_commit(commit: str) -> None:
    if not commit:
        raise SystemExit("frozen-constants artifact lacks preregistration_commit")
    full = subprocess.run(["git", "rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=REPO_ROOT,
                          capture_output=True, text=True)
    if full.returncode != 0:
        raise SystemExit(f"pre-registration commit {commit} is not in this repository")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", full.stdout.strip(), "HEAD"], cwd=REPO_ROOT)
    if ancestor.returncode != 0:
        raise SystemExit(f"pre-registration commit {commit} is not an ancestor of HEAD")


def load_constants(spec: str | None) -> V2Constants:
    """--constants '{"trend_window_days": 10.0, "amp_ratio": [0.5, 1.2]}' or a
    JSON file; a frozen-constants artifact carries the overrides under
    "overrides". Only declared candidate values are accepted (TUNABLE)."""
    if not spec:
        return DEFAULT
    payload = json.loads(Path(spec).read_text(encoding="utf-8")) if Path(spec).exists() else json.loads(spec)
    overrides = payload.get("overrides", payload) if isinstance(payload, dict) else payload
    return with_overrides(DEFAULT, **overrides)


def registered_holdout(args, constants: V2Constants, split_record: dict, stars_sha: str,
                       root: Path) -> dict:
    """Single-execution holdout discipline (G-review 2026-09-02 finding 4,
    round 2 (b)): the exact registered holdout list, no --limit, the
    frozen-constants artifact at the registration root whose v2-code / split /
    plan digests match this checkout, whose pre-registration commit is an
    ancestor of HEAD and whose evidence table is intact, and one lock file per
    dataset created ATOMICALLY (O_EXCL) before computation; a relaunch must be
    an exact resume of the locked run."""
    dataset = args.dataset.split("-")[0]
    if args.limit is not None:
        raise SystemExit("holdout runs forbid --limit")
    manifest = json.loads((root / "split_manifest.json").read_text(encoding="utf-8"))
    expected = manifest["outputs"].get(f"{dataset}_holdout.txt")
    if stars_sha != expected:
        raise SystemExit("holdout runs must use the registered holdout list exactly "
                         f"({dataset}_holdout.txt, SHA {str(expected)[:12]}…)")
    if manifest["outputs"].get("split.csv") != split_record["sha256"]:
        raise SystemExit("split.csv does not match the registered split manifest")
    artifact_path = (root / FROZEN_CONSTANTS_NAME).resolve()
    if not args.constants or Path(args.constants).resolve() != artifact_path or not artifact_path.exists():
        raise SystemExit(f"holdout runs require --constants {artifact_path} (the registered artifact)")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    checks = {
        "v2_digest": (artifact.get("v2_digest"), v2_digest()),
        "split_sha256": (artifact.get("split_sha256"), split_record["sha256"]),
        "plan_sha256": (artifact.get("plan_sha256"), sha256_file(root / "V2_PLAN.md")),
        "tuning_evidence_sha256": (artifact.get("tuning_evidence_sha256"),
                                   sha256_file(root / "dev_tuning.csv") if (root / "dev_tuning.csv").exists() else None),
    }
    bad = {k: v for k, v in checks.items() if v[0] != v[1]}
    if bad:
        raise SystemExit(f"frozen-constants artifact does not match this checkout: {bad}")
    verify_preregistration_commit(str(artifact.get("preregistration_commit", "")))
    lock_path = root / f"HOLDOUT_LAUNCH_{dataset}.json"
    record = {
        "dataset": dataset, "machine": args.machine, "out_dir": str(args.out_dir.resolve()),
        "stars_file_sha256": stars_sha, "constants_sha256": constants_sha256(constants),
        "v2_digest": v2_digest(), "split_sha256": split_record["sha256"],
        "plan_sha256": checks["plan_sha256"][1],
        "preregistration_commit": artifact["preregistration_commit"],
        "constants_artifact_sha256": sha256_file(artifact_path),
        "tuning_evidence_sha256": checks["tuning_evidence_sha256"][1],
        "registration_root": str(root),
        "canonical_registration": root == CANONICAL_REGISTRATION,
    }
    try:
        fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
        drift = {k: (existing.get(k), v) for k, v in record.items() if existing.get(k) != v}
        if drift:
            raise SystemExit(f"holdout for {dataset} was already launched with a different "
                             f"configuration; only an exact resume is permitted: {drift}")
        record = existing
    else:
        record["launched_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(record, indent=2) + "\n")
    return {"lock_file": str(lock_path), **record}


def split_half(split_file: Path, dataset: str, ids: set[str]) -> str:
    split = pd.read_csv(split_file, dtype=str)
    split = split[split["dataset"] == dataset]
    halves = split.set_index("sid")["split"]
    unknown = ids - set(halves.index)
    if unknown:
        raise SystemExit(f"{len(unknown)} requested ids are not in the split table (e.g. {sorted(unknown)[:3]})")
    found = set(halves.loc[sorted(ids)])
    if len(found) != 1:
        raise SystemExit(f"requested ids span both halves of the split: {sorted(found)}")
    return found.pop()


def git_state() -> dict:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, timeout=30).stdout.strip()
        tracked = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO_ROOT,
                                 capture_output=True, text=True, timeout=30).stdout.strip()
        untracked = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=REPO_ROOT,
                                   capture_output=True, text=True, timeout=60).stdout.splitlines()
        return {"git_commit": head, "git_tracked_dirty": bool(tracked),
                "git_untracked_count": sum(1 for line in untracked if line.startswith("??"))}
    except Exception as exc:  # noqa: BLE001
        return {"git_commit": "", "git_tracked_dirty": None, "git_untracked_count": None,
                "git_error": repr(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=None)
    parser.add_argument("--dataset", required=True, help="d3-kepler-dsct | d2-tess-dav")
    parser.add_argument("--machine", required=True, help="machine label recorded in the manifest and sidecars")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--passes", default="low,high")
    parser.add_argument("--stars-file", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--expect-count", type=int, default=None)
    parser.add_argument("--shard-index", type=Path, default=None)
    parser.add_argument("--allow-nonstandard-ids", action="store_true")
    parser.add_argument("--constants", default=None,
                        help="JSON (inline or file) of tunable overrides; declared candidates only")
    parser.add_argument("--split-file", type=Path, default=None,
                        help="generalization/v2/split.csv; the requested ids must lie in ONE half")
    parser.add_argument("--allow-holdout", action="store_true",
                        help="permit running holdout ids (only after the dev constants are fixed)")
    args = parser.parse_args()

    frozen_api.assert_frozen()
    constants = load_constants(args.constants)
    v2_shas_start = v2_file_shas()
    campaign_shas_start = campaign_file_shas()
    passes = tuple(args.passes.split(","))
    if passes != ("low", "high") and not args.allow_nonstandard_ids:
        raise SystemExit("v2 runs use exactly low,high; pass --allow-nonstandard-ids for debug runs")
    if (args.shard_dir / "IN_PROGRESS").exists():
        raise SystemExit(f"{args.shard_dir} is an unpublished shard generation (IN_PROGRESS sentinel)")
    generation_path = args.shard_dir / "generation_manifest.json"
    generation = (json.loads(generation_path.read_text(encoding="utf-8"))
                  if generation_path.exists() else {})
    if args.dataset.startswith("d2") and not generation and not args.allow_nonstandard_ids:
        raise SystemExit("d2 runs require a published shard generation (generation_manifest.json)")
    pilot = args.limit is not None or args.stars_file is not None
    stars_sha = sha256_file(args.stars_file) if args.stars_file else ""
    star_dir = args.out_dir / "stars"
    work_root = args.work_root or (args.out_dir / "work")
    star_dir.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)

    if args.expect_count is not None:
        found = len(list(args.shard_dir.glob("*.csv.gz")))
        if found != args.expect_count:
            raise SystemExit(f"shard dir holds {found} shards, expected {args.expect_count}")
    if args.shard_index is None and not args.allow_nonstandard_ids:
        raise SystemExit("production runs require --shard-index; --allow-nonstandard-ids for debug")
    if args.shard_index is not None:
        index_ids = {line.strip() for line in args.shard_index.read_text().splitlines() if line.strip()}
        disk_ids = {path.name.split(".csv")[0] for path in args.shard_dir.glob("*.csv.gz")}
        if disk_ids != index_ids:
            raise SystemExit(
                f"shard dir does not match the index: {len(disk_ids - index_ids)} extra, "
                f"{len(index_ids - disk_ids)} missing"
            )
    only = None
    if args.stars_file:
        only = {line.strip() for line in args.stars_file.read_text().splitlines() if line.strip()}
    split_record = {"file": "", "sha256": "", "half": ""}
    holdout_record: dict = {}
    root = registration_root()
    if args.split_file is not None:
        if only is None:
            raise SystemExit("--split-file requires --stars-file (one half of the split)")
        if args.split_file.resolve() != (root / "split.csv").resolve():
            raise SystemExit(f"--split-file must be the registered split {root / 'split.csv'}")
        half = split_half(args.split_file, args.dataset.split("-")[0], only)
        if half == "dev_smoke":
            raise SystemExit("dev_smoke stars are excluded from every registered run")
        split_record = {"file": str(args.split_file), "sha256": sha256_file(args.split_file), "half": half}
        if half == "holdout":
            if not args.allow_holdout:
                raise SystemExit("these are HOLDOUT ids: refusing without --allow-holdout "
                                 "(pre-registration: the holdout is scored once, after dev)")
            holdout_record = registered_holdout(args, constants, split_record, stars_sha, root)
    elif only is not None and not args.allow_nonstandard_ids:
        raise SystemExit("--stars-file without --split-file: pass --split-file generalization/v2/split.csv "
                         "(or --allow-nonstandard-ids for debug subsets)")
    # holdout-id protection (round-2 (b), round-3): a CANONICAL holdout id can
    # only ever be scored by a registered holdout run under the CANONICAL
    # registration root — never by a debug, dev or unregistered run, and never
    # under a copied registration root (whatever it contains)
    requested = only if only is not None else {
        path.name.split(".csv")[0] for path in args.shard_dir.glob("*.csv.gz")}
    touched = requested & canonical_holdout_ids()
    if touched and not holdout_record:
        raise SystemExit(f"{len(touched)} requested ids are registered HOLDOUT ids; they can only be "
                         "scored in the registered holdout mode (--split-file + --allow-holdout)")
    if touched and root != CANONICAL_REGISTRATION:
        raise SystemExit(f"{len(touched)} requested ids are CANONICAL holdout ids: a registered holdout run "
                         f"must use the canonical registration {CANONICAL_REGISTRATION}, not {root}")
    binding = {
        "engine": ENGINE,
        "v2_digest": v2_digest(),
        "frozen_digest": frozen_digest(),
        "constants_sha256": constants_sha256(constants),
        "generation_id": generation.get("generation_id", ""),
        "attestation_sha256": UNATTESTED,
        "machine": args.machine,
        "split_sha256": split_record["sha256"],
        "split_half": split_record["half"],
        "stars_file_sha256": stars_sha,
    }
    if holdout_record:
        binding["plan_sha256"] = holdout_record["plan_sha256"]
        binding["preregistration_commit"] = holdout_record["preregistration_commit"]
        binding["constants_artifact_sha256"] = holdout_record["constants_artifact_sha256"]
    pending, source_ids = scan_pending(args.shard_dir, star_dir, passes, only, args.limit, binding)
    total = len(source_ids)
    if not args.allow_nonstandard_ids:
        bad = [sid for sid in pending if not frozen_api.campaign_id_ok(sid)]
        if bad:
            raise SystemExit(f"{len(bad)} shard ids violate the campaign id convention (first: {bad[:3]})")

    workers, free_gb = preflight_workers(args.workers, work_root)
    print(f"[{args.dataset}/v2] sources={total:,} pending={len(pending):,} workers={workers} "
          f"(free {free_gb:.0f} GB on scratch) machine={args.machine}", flush=True)

    progress_path = args.out_dir / "progress.json"
    started = time.time()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    failures: dict[str, str] = {}
    completed_now = 0

    def progress_payload() -> dict:
        elapsed = time.time() - started
        rate = completed_now / elapsed if elapsed > 0 else 0.0
        return {
            "dataset": args.dataset, "engine": ENGINE, "machine": args.machine,
            "total": total, "pending_at_start": len(pending), "completed_now": completed_now,
            "failed": len(failures), "elapsed_seconds": round(elapsed, 1),
            "stars_per_hour": round(rate * 3600.0, 2),
            "eta_hours": round((len(pending) - completed_now - len(failures)) / (rate * 3600.0), 2)
            if rate > 0 else None,
            "workers": workers,
        }

    analyze = functools.partial(analyze_star_v2, constants=constants)
    write_progress(progress_path, progress_payload())
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                analyze, source_id, str(args.shard_dir / f"{source_id}.csv.gz"),
                str(star_dir / f"{source_id}.json"), str(work_root), passes,
            ): source_id
            for source_id in pending
        }
        for future in as_completed(futures):
            source_id = futures[future]
            try:
                future.result()
                write_provenance(star_dir, source_id, args.shard_dir / f"{source_id}.csv.gz",
                                 passes, binding, args.machine)
                completed_now += 1
            except Exception as exc:  # noqa: BLE001
                failures[source_id] = repr(exc)
                print(f"[{args.dataset}/v2] FAILED {source_id}: {exc}", flush=True)
            if completed_now % 10 == 0 or completed_now + len(failures) == len(pending):
                write_progress(progress_path, progress_payload())
                print(f"[{args.dataset}/v2] {completed_now:,}/{len(pending):,} "
                      f"({progress_payload()['stars_per_hour']}/h)", flush=True)

    manifest = {
        "dataset": args.dataset,
        "engine": ENGINE,
        "driver": DRIVER,
        "machine": args.machine,
        "source_count": total,
        "pending_at_start": len(pending),
        "completed_now": completed_now,
        "failures": failures,
        "passes": list(passes),
        "workers": workers,
        "wall_seconds": round(time.time() - started, 1),
        "shard_dir": str(args.shard_dir),
        "shard_index": str(args.shard_index) if args.shard_index else "",
        "shard_index_sha256": sha256_file(args.shard_index) if args.shard_index else "",
        "stars_file_sha256": stars_sha,
        "argv": sys.argv,
        "started_utc": started_utc,
        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **git_state(),
        "generation_id": binding["generation_id"],
        "pilot": pilot,
        "limit": args.limit,
        "stars_file": str(args.stars_file) if args.stars_file else "",
        "split": split_record,
        "allow_holdout": bool(args.allow_holdout),
        "holdout_registration": holdout_record,
        "registration_root": str(root),
        "canonical_registration": root == CANONICAL_REGISTRATION,
        "constants": constants.as_dict(),
        "constants_sha256": binding["constants_sha256"],
        "env": env_versions(),
        "frozen_sha256": frozen_api.assert_frozen(),
        "v2_sha256": v2_shas_start,
        "campaign_sha256_at_start": campaign_shas_start,
        "campaign_digest_at_start": hashlib.sha256(
            json.dumps(campaign_shas_start, sort_keys=True).encode()).hexdigest(),
        "binding": binding,
        "replay_attestation": {"path": "", "sha256": UNATTESTED, "tier": "v2_unattested"},
    }
    completion_rows = []
    for source_id in source_ids:
        result_path = star_dir / f"{source_id}.json"
        prov_file = provenance_path(star_dir, source_id)
        if source_id in failures:
            status = "failed"
        elif result_path.exists() and prov_file.exists():
            status = "complete"
        else:
            status = "pending"
        completion_rows.append({
            "source_id": source_id, "status": status,
            "result_sha256": sha256_file(result_path) if result_path.exists() else "",
            "provenance_sha256": sha256_file(prov_file) if prov_file.exists() else "",
        })
    pd.DataFrame(completion_rows, columns=["source_id", "status", "result_sha256", "provenance_sha256"]).to_csv(
        args.out_dir / "completion.csv", index=False, lineterminator="\n")
    if v2_file_shas() != v2_shas_start or frozen_file_shas() != manifest["frozen_sha256"]:
        raise SystemExit("v2 or frozen code changed mid-run — results void")
    if campaign_file_shas() != campaign_shas_start:
        manifest["campaign_changed_during_run"] = True   # informational: not part of the binding
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_progress(progress_path, progress_payload())
    print(f"[{args.dataset}/v2] done: {completed_now:,} completed, {len(failures)} failed", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
