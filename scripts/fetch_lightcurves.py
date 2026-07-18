#!/usr/bin/env python3
"""Resumable ZTF light-curve fetcher for the Jestin+2026 variable-WD roster.

For each roster star, queries IRSA's login-free ZTF light-curve API over a 3"
cone and caches the raw CSV response under data/raw/lc_cache/<source_id>.csv.
Reruns skip already-cached stars, so the job is fully resumable.

Built to scale to the full 864-source catalog once it publishes on VizieR; the
roster CSV path is the only thing that changes.

Usage:
    python scripts/fetch_lightcurves.py [--roster PATH] [--sleep 0.5]
"""
import argparse
import csv
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_ROSTER = os.path.join(ROOT, "data", "roster", "jestin2026_roster.csv")
CACHE_DIR = os.path.join(ROOT, "data", "raw", "lc_cache")
BASE = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
CONE_RADIUS_DEG = 0.000833  # 3 arcsec


def build_url(ra, dec):
    # POS=CIRCLE <ra> <dec> <r> ; space-delimited, URL-encoded.
    pos = f"CIRCLE {ra} {dec} {CONE_RADIUS_DEG}"
    params = {
        "POS": pos,
        "BANDNAME": "g,r",
        "FORMAT": "CSV",
        "BAD_CATFLAGS_MASK": "32768",
    }
    return BASE + "?" + urllib.parse.urlencode(params)


def fetch(url, tries=3):
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "astro-wd-panel/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:  # transient network / 5xx
            last = e
            if attempt < tries:
                time.sleep(2 * attempt)
    raise last


def n_data_rows(text):
    # First non-empty non-comment line is the header; count the rest.
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("\\") and not ln.startswith("|")]
    return max(0, len(lines) - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", default=DEFAULT_ROSTER)
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(args.roster, newline="") as f:
        stars = list(csv.DictReader(f))
    total = len(stars)
    print(f"[fetch] roster: {args.roster}  stars: {total}", flush=True)

    fetched = skipped = empty = failed = 0
    for i, s in enumerate(stars, 1):
        sid = s["source_id"]
        out = os.path.join(CACHE_DIR, f"{sid}.csv")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            skipped += 1
        else:
            try:
                text = fetch(build_url(s["ra"], s["dec"]))
                with open(out, "w", newline="") as fo:
                    fo.write(text)
                rows = n_data_rows(text)
                fetched += 1
                if rows == 0:
                    empty += 1
            except Exception as e:
                failed += 1
                print(f"[fetch] FAILED {sid}: {e}", file=sys.stderr, flush=True)
            time.sleep(args.sleep)
        if i % 25 == 0 or i == total:
            print(f"[fetch] {i}/{total}  fetched={fetched} skipped={skipped} "
                  f"empty={empty} failed={failed}", flush=True)

    print(f"[fetch] DONE  fetched={fetched} skipped={skipped} empty={empty} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
