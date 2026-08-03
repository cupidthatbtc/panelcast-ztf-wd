#!/usr/bin/env python3
"""Run the two-attempt, 12-hour full-catalog panelcast policy from Windows."""

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TIMEBOX_SECONDS = 12 * 60 * 60


def current_runs() -> set[Path]:
    runs = set()
    roots = (ROOT / "outputs", ROOT / "outputs/failed")
    for base in roots:
        if not base.exists():
            continue
        for path in base.iterdir():
            if path.name in {"catalog", "failed"}:
                continue
            try:
                if path.is_dir():
                    runs.add(path.resolve())
            except OSError:
                continue
    return runs


def locate_new_run(before: set[Path]) -> Path | None:
    candidates = [
        path
        for path in current_runs() - before
        if (path / "manifest.json").exists() or (path / "pipeline.log.json").exists()
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def diagnostics_pass(path: Path) -> bool:
    diagnostics_path = path / "evaluation/diagnostics.json"
    if not diagnostics_path.exists():
        return False
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    return (
        float(diagnostics["rhat_max"]) <= 1.01
        and float(diagnostics["ess_bulk_min"]) >= 400
        and int(diagnostics["divergences"]) == 0
    )


def retry_settings(attempt_one: Path) -> tuple[float, str, str]:
    diagnostics_path = attempt_one / "evaluation/diagnostics.json"
    if not diagnostics_path.exists():
        return 0.90, "median", "median initialization after an incomplete first attempt"
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    if int(diagnostics["divergences"]) > 0:
        return 0.95, "uniform", "target_accept 0.95 for divergent transitions"
    return 0.90, "median", "median initialization for R-hat/ESS failure without divergences"


def fit_command(
    target_accept: float,
    init_strategy: str,
    tag: str,
    timeout_seconds: int,
    run_dir: Path,
) -> str:
    linux_repo = "/mnt/c/Users/jcwen/Projects/astro-wd"
    panel_path = f"{linux_repo}/outputs/catalog/{run_dir.name}/panelcast_zg_monthly.csv"
    retry_config = ""
    if init_strategy != "uniform":
        retry_path = (
            f"{linux_repo}/outputs/catalog/{run_dir.name}/"
            "panelcast_full_fit/retry_init.yaml"
        )
        retry_config = f"--config {shlex.quote(retry_path)} "
    command = (
        f"cd {shlex.quote(linux_repo)} && "
        f"export ZTF_WD_CATALOG_MONTHLY_PATH={shlex.quote(panel_path)} && "
        "export COLUMNS=180 TERM=dumb NO_COLOR=1 && "
        f"timeout --signal=TERM --kill-after=60s {timeout_seconds}s "
        "~/aoty-gpu/bin/panelcast run "
        "--dataset configs/datasets/ztf_wd_catalog_monthly.yaml "
        "--config configs/wd_fit.yaml "
        f"{retry_config}"
        "--no-artist --min-ratings 1 --max-albums 100 "
        "--num-chains 4 --num-samples 3000 --num-warmup 3000 "
        f"--target-accept {target_accept:.2f} "
        f"--seed 42 --tag {shlex.quote(tag)} --allow-unlocked-env"
    )
    return command


def evaluation_oom(path: Path) -> bool:
    failure_path = path / "failure.json"
    if not failure_path.exists():
        return False
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    return failure.get("stage") == "evaluate" and "RESOURCE_EXHAUSTED" in failure.get(
        "message", ""
    )


def evaluation_resume_command(run_id: str, timeout_seconds: int) -> str:
    linux_repo = "/mnt/c/Users/jcwen/Projects/astro-wd"
    panel_path = f"{linux_repo}/outputs/catalog/2026-08-01_full/panelcast_zg_monthly.csv"
    return (
        f"cd {shlex.quote(linux_repo)} && "
        f"export ZTF_WD_CATALOG_MONTHLY_PATH={shlex.quote(panel_path)} && "
        "export COLUMNS=180 TERM=dumb NO_COLOR=1 TF_GPU_ALLOCATOR=cuda_malloc_async && "
        f"timeout --signal=TERM --kill-after=60s {timeout_seconds}s "
        f"~/aoty-gpu/bin/panelcast run --resume {shlex.quote(run_id)} "
        "--allow-unlocked-env"
    )


def write_timebox_summary(fit_dir: Path, attempts: int, narrative: str) -> None:
    payload = {
        "status": "timebox_exceeded",
        "attempts": attempts,
        "max_rhat": None,
        "min_bulk_ess": None,
        "divergences": None,
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
    (fit_dir / "fit_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    parser.add_argument("--timebox-hours", type=float, default=12.0)
    args = parser.parse_args()

    fit_dir = args.run_dir / "panelcast_full_fit"
    fit_dir.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + min(TIMEBOX_SECONDS, int(args.timebox_hours * 3600))
    attempts_completed = 0

    for attempt in (1, 2):
        if attempt == 1:
            target_accept, init_strategy, remedy = 0.90, "uniform", "pilot configuration"
        else:
            target_accept, init_strategy, remedy = retry_settings(fit_dir / "attempt_1")
        destination = fit_dir / f"attempt_{attempt}"
        if destination.exists() and (destination / "evaluation/diagnostics.json").exists():
            attempts_completed += 1
            if diagnostics_pass(destination):
                break
            continue

        remaining = int(deadline - time.monotonic())
        if remaining < 300:
            write_timebox_summary(
                fit_dir,
                attempts_completed,
                "The 12-hour wall-clock budget expired before another complete attempt could start.",
            )
            print("panelcast timebox expired", flush=True)
            return

        if init_strategy != "uniform":
            (fit_dir / "retry_init.yaml").write_text(
                f"init_strategy: {init_strategy}\n",
                encoding="utf-8",
            )
        before = current_runs()
        command = fit_command(
            target_accept,
            init_strategy,
            f"catalog-rebuild-attempt-{attempt}",
            remaining,
            args.run_dir,
        )
        log_path = fit_dir / f"attempt_{attempt}.log"
        print(
            f"[panelcast] attempt {attempt}; target_accept={target_accept:.2f}; "
            f"init={init_strategy}; remedy={remedy}; remaining={remaining / 3600:.2f} h",
            flush=True,
        )
        with log_path.open("w", encoding="utf-8") as log:
            completed = subprocess.run(
                ["wsl", "bash", "-lc", command],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=remaining + 90,
                check=False,
                text=True,
            )
        new_run = locate_new_run(before)
        recovery_returncode = None
        if new_run is not None and evaluation_oom(new_run):
            recovery_remaining = int(deadline - time.monotonic())
            recovery_command = evaluation_resume_command(new_run.name, recovery_remaining)
            print(
                f"[panelcast] resuming attempt {attempt} evaluation with cuda_malloc_async",
                flush=True,
            )
            with log_path.open("a", encoding="utf-8") as log:
                log.write("\n[runner] resuming evaluation after allocator OOM\n")
                recovered = subprocess.run(
                    ["wsl", "bash", "-lc", recovery_command],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=recovery_remaining + 90,
                    check=False,
                    text=True,
                )
            recovery_returncode = recovered.returncode
            root_run = ROOT / "outputs" / new_run.name
            failed_run = ROOT / "outputs/failed" / new_run.name
            new_run = root_run if root_run.exists() else failed_run
        if new_run is not None and new_run.exists():
            shutil.move(str(new_run), str(destination))
        attempts_completed += 1
        failure = {
            "attempt": attempt,
            "target_accept": target_accept,
            "init_strategy": init_strategy,
            "remedy": remedy,
            "returncode": completed.returncode,
            "evaluation_recovery_returncode": recovery_returncode,
            "run_captured": new_run is not None and destination.exists(),
            "diagnostics_present": (destination / "evaluation/diagnostics.json").exists(),
        }
        (fit_dir / f"attempt_{attempt}_execution.json").write_text(
            json.dumps(failure, indent=2) + "\n",
            encoding="utf-8",
        )
        if diagnostics_pass(destination):
            break
        if new_run is None:
            raise RuntimeError(f"panelcast attempt {attempt} produced no run directory; see {log_path}")

    completed_attempts = [
        path
        for path in sorted(fit_dir.glob("attempt_*"))
        if path.is_dir() and (path / "evaluation/diagnostics.json").exists()
    ]
    if completed_attempts:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/summarize_catalog_panelcast.py"),
                "--fit-dir",
                str(fit_dir),
            ],
            check=True,
        )
    else:
        write_timebox_summary(
            fit_dir,
            attempts_completed,
            "No attempt reached diagnostics within the 12-hour wall-clock budget; logs and any partial run are retained.",
        )


if __name__ == "__main__":
    main()
