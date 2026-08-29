#!/usr/bin/env python3
"""Print (and optionally loop over) a campaign run's progress.json."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def render(path: Path) -> str:
    progress = json.loads(path.read_text(encoding="utf-8"))
    eta = progress.get("eta_hours")
    return (
        f"{progress['dataset']}: {progress['completed_now']:,}/{progress['pending_at_start']:,} "
        f"(+{progress['failed']} failed) {progress['stars_per_hour']}/h "
        f"eta={eta if eta is not None else '?'}h elapsed={progress['elapsed_seconds'] / 3600.0:.1f}h"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("progress_file", type=Path)
    parser.add_argument("--loop", type=int, default=None, help="refresh every N seconds")
    args = parser.parse_args()
    while True:
        print(render(args.progress_file), flush=True)
        if args.loop is None:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
