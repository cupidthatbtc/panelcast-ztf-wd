#!/usr/bin/env python3
"""Build the quality-filtered exposure-level ZTF panel with BJD_TDB times."""

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
import astropy.units as u

ROOT = Path(__file__).resolve().parents[1]
PALOMAR = EarthLocation.from_geodetic(lon=-116.8630 * u.deg, lat=33.3563 * u.deg, height=1706 * u.m)
BANDS = {"zg", "zr"}


def load_roster(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["source_id"]: row for row in csv.DictReader(fh)}


def parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def rejection_reason(row: dict[str, str]) -> str | None:
    try:
        catflags = int(float(row["catflags"]))
    except (KeyError, TypeError, ValueError):
        return "invalid_catflags"
    if catflags != 0:
        return "catflags"

    magerr = parse_float(row.get("magerr", ""))
    if not math.isfinite(magerr) or magerr <= 0:
        return "invalid_magerr"

    mag = parse_float(row.get("mag", ""))
    if not math.isfinite(mag):
        return "invalid_mag"

    chi = parse_float(row.get("chi", ""))
    if not math.isfinite(chi) or chi >= 4:
        return "chi"

    mjd = parse_float(row.get("mjd", ""))
    if not math.isfinite(mjd):
        return "invalid_mjd"
    return None


def add_bjd(rows: list[dict[str, object]], roster: dict[str, dict[str, str]]) -> None:
    by_star: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_star[str(row["source_id"])].append(index)

    for source_id, indices in by_star.items():
        meta = roster[source_id]
        coord = SkyCoord(float(meta["ra"]) * u.deg, float(meta["dec"]) * u.deg, frame="icrs")
        mjd = np.array([float(rows[index]["mjd"]) for index in indices])
        times = Time(mjd, format="mjd", scale="utc", location=PALOMAR)
        bjd = (times.tdb + times.light_travel_time(coord, kind="barycentric")).jd
        for index, value in zip(indices, bjd, strict=True):
            rows[index]["bjd_tdb"] = f"{value:.10f}"


def build(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    roster = load_roster(args.roster)
    output_rows: list[dict[str, object]] = []
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    for path in sorted(args.cache_dir.glob("*.csv")):
        source_id = path.stem
        if source_id not in roster:
            raise ValueError(f"cached source {source_id} is absent from roster")
        with path.open(newline="", encoding="utf-8") as fh:
            for raw in csv.DictReader(fh):
                band = raw.get("filtercode", "").strip() or "unknown"
                key = (source_id, band)
                counts[key]["rows_total"] += 1
                if band not in BANDS:
                    counts[key]["unsupported_band"] += 1
                    continue
                reason = rejection_reason(raw)
                if reason:
                    counts[key][reason] += 1
                    continue

                row: dict[str, object] = dict(raw)
                row.update(
                    source_id=source_id,
                    band=band,
                    night_mjd=math.floor(float(raw["mjd"])),
                    wdj_name=roster[source_id]["wdj_name"],
                    wd_class=roster[source_id]["wd_class"],
                    paper_variable=roster[source_id]["paper_variable"],
                    paper_periodic=roster[source_id]["paper_periodic"],
                )
                output_rows.append(row)
                counts[key]["rows_kept"] += 1

    for source_id in roster:
        for band in sorted(BANDS):
            counts[(source_id, band)]

    add_bjd(output_rows, roster)
    output_rows.sort(key=lambda row: (str(row["source_id"]), str(row["band"]), float(row["bjd_tdb"])))

    qc_rows: list[dict[str, object]] = []
    for (source_id, band), count in sorted(counts.items()):
        total = count["rows_total"]
        kept = count["rows_kept"]
        qc_rows.append(
            {
                "source_id": source_id,
                "band": band,
                "rows_total": total,
                "rows_kept": kept,
                "rows_dropped": total - kept,
                "drop_catflags": count["catflags"],
                "drop_invalid_catflags": count["invalid_catflags"],
                "drop_invalid_magerr": count["invalid_magerr"],
                "drop_invalid_mag": count["invalid_mag"],
                "drop_chi": count["chi"],
                "drop_invalid_mjd": count["invalid_mjd"],
                "drop_unsupported_band": count["unsupported_band"],
            }
        )

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in output_rows:
        grouped[(str(row["source_id"]), str(row["band"]))].append(row)

    summary_rows: list[dict[str, object]] = []
    for (source_id, band), rows in sorted(grouped.items()):
        times = np.array([float(row["bjd_tdb"]) for row in rows])
        errors = np.array([float(row["magerr"]) for row in rows])
        per_night = Counter(int(row["night_mjd"]) for row in rows)
        summary_rows.append(
            {
                "source_id": source_id,
                "band": band,
                "n_exp": len(rows),
                "baseline_days": f"{np.ptp(times):.8f}",
                "median_magerr": f"{np.median(errors):.8f}",
                "median_exposures_per_night": f"{np.median(list(per_night.values())):.3f}",
            }
        )
    return output_rows, qc_rows, summary_rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    fieldnames = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster", type=Path, default=ROOT / "data/roster/jestin2026_roster.csv")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data/raw/lc_cache")
    parser.add_argument("--out", type=Path, default=ROOT / "data/raw/ztf_wd_exposures.csv")
    parser.add_argument("--qc-out", type=Path, default=ROOT / "data/raw/ztf_wd_exposure_qc.csv")
    parser.add_argument("--summary-out", type=Path, default=ROOT / "data/raw/ztf_wd_exposure_summary.csv")
    args = parser.parse_args()

    rows, qc, summary = build(args)
    write_csv(args.out, rows)
    write_csv(args.qc_out, qc)
    write_csv(args.summary_out, summary)
    print(f"wrote {args.out} ({len(rows):,} clean exposures)")
    print(f"wrote {args.qc_out} ({len(qc)} star-band rows)")
    print(f"wrote {args.summary_out} ({len(summary)} usable star-band series)")


if __name__ == "__main__":
    main()
