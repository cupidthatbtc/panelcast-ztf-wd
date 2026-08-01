#!/usr/bin/env python3
"""Fetch full-history ZTF g/r light curves for the rebuilt catalog."""

import argparse
import csv
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
CONE_RADIUS_DEG = 10.0 / 3600.0
RETRYABLE_CODES = {429, 500, 502, 503, 504}


def build_url(ra: str, dec: str) -> str:
    params = {
        "POS": f"CIRCLE {ra} {dec} {CONE_RADIUS_DEG:.10f}",
        "BANDNAME": "g,r",
        "FORMAT": "CSV",
        "BAD_CATFLAGS_MASK": "32768",
    }
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def fetch(url: str, retries: int) -> tuple[str, int]:
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "panelcast-ztf-wd-catalog/1.0"},
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read().decode("utf-8", errors="replace"), attempt
        except urllib.error.HTTPError as exc:
            retryable = exc.code in RETRYABLE_CODES
            if not retryable or attempt == retries:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == retries:
                raise
        delay = min(60.0, 2.0 ** attempt) + random.uniform(0.0, 0.5)
        time.sleep(delay)
    raise RuntimeError("unreachable retry loop")


def row_count(text: str) -> int:
    lines = (
        line
        for line in text.splitlines()
        if line.strip() and not line.startswith("\\") and not line.startswith("|")
    )
    return max(0, sum(1 for _ in lines) - 1)


def log_event(path: Path, payload: dict[str, object]) -> None:
    payload = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--roster",
        type=Path,
        default=ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=ROOT / "data/raw/catalog_lc_cache",
    )
    parser.add_argument("--sleep", type=float, default=1.25)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    if args.sleep < 1.0:
        raise ValueError("the full-catalog fetch requires at least one second between requests")
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    event_log = args.cache_dir / "fetch_events.jsonl"

    with args.roster.open(newline="", encoding="utf-8") as handle:
        stars = list(csv.DictReader(handle))
    if args.limit is not None:
        stars = stars[: args.limit]

    totals = {"fetched": 0, "skipped": 0, "empty": 0, "failed": 0, "retried": 0}
    print(f"[fetch] {len(stars):,} targets; 10 arcsec cone; sleep={args.sleep:.2f}s", flush=True)
    for index, star in enumerate(stars, 1):
        source_id = star["source_id"]
        output = args.cache_dir / f"{source_id}.csv"
        if output.exists() and output.stat().st_size > 0:
            totals["skipped"] += 1
        else:
            try:
                text, attempts = fetch(build_url(star["ra"], star["dec"]), args.retries)
                temporary = output.with_suffix(".csv.part")
                temporary.write_text(text, encoding="utf-8", newline="")
                temporary.replace(output)
                rows = row_count(text)
                totals["fetched"] += 1
                totals["empty"] += int(rows == 0)
                totals["retried"] += int(attempts > 0)
                log_event(
                    event_log,
                    {
                        "source_id": source_id,
                        "status": "fetched",
                        "rows": rows,
                        "retries": attempts,
                        "bytes": output.stat().st_size,
                    },
                )
            except Exception as exc:
                totals["failed"] += 1
                log_event(
                    event_log,
                    {
                        "source_id": source_id,
                        "status": "failed",
                        "error": repr(exc),
                    },
                )
                print(f"[fetch] FAILED {source_id}: {exc}", flush=True)
            time.sleep(args.sleep)

        if index % 25 == 0 or index == len(stars):
            counts = " ".join(f"{key}={value}" for key, value in totals.items())
            print(f"[fetch] {index:,}/{len(stars):,} {counts}", flush=True)

    manifest = {
        "roster": str(args.roster),
        "targets": len(stars),
        "cone_radius_arcsec": 10.0,
        "bands": ["zg", "zr"],
        "sleep_seconds": args.sleep,
        "max_retries": args.retries,
        **totals,
    }
    (args.cache_dir / "fetch_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[fetch] DONE {json.dumps(manifest, sort_keys=True)}", flush=True)
    if totals["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
