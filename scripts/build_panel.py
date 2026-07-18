#!/usr/bin/env python3
"""Tidy cached ZTF light curves into the nightly-binned panel.

Reads data/raw/lc_cache/<source_id>.csv (raw IRSA responses), keeps clean
epochs (catflags == 0), bins per (star, band, night=floor(mjd)), and writes
data/raw/ztf_wd_panel.csv with one row per (white dwarf, band, night).

mag_err uses a scatter-aware standard error:
    max(std(mag)/sqrt(n_exp), median(magerr)/sqrt(n_exp))
so nights whose intra-night scatter exceeds the reported photometric error are
not given a spuriously tight error bar.

Series with < 5 nights are dropped; stars with no surviving series are dropped.
"""
import csv
import glob
import math
import os
import statistics
from collections import defaultdict
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE_DIR = os.path.join(ROOT, "data", "raw", "lc_cache")
ROSTER = os.path.join(ROOT, "data", "roster", "jestin2026_roster.csv")
OUT = os.path.join(ROOT, "data", "raw", "ztf_wd_panel.csv")
MIN_NIGHTS = 5
MJD_EPOCH = date(1858, 11, 17)  # MJD 0

BAND_MAP = {"zg": "zg", "zr": "zr"}  # keep native ZTF band codes


def mjd_to_iso(night_mjd):
    return (MJD_EPOCH + timedelta(days=int(night_mjd))).isoformat()


def load_roster():
    meta = {}
    with open(ROSTER, newline="") as f:
        for row in csv.DictReader(f):
            meta[row["source_id"]] = row
    return meta


def parse_lc(path):
    """Yield (mjd, mag, magerr, band) for clean rows of one cached response."""
    with open(path, newline="") as f:
        # Skip IPAC-VOTable-style comment/pipe lines if present; header is CSV.
        reader = csv.DictReader(
            ln for ln in f if ln.strip() and not ln.startswith("\\") and not ln.startswith("|")
        )
        for r in reader:
            try:
                if int(float(r["catflags"])) != 0:
                    continue
                band = r["filtercode"].strip()
                if band not in BAND_MAP:
                    continue
                yield (float(r["mjd"]), float(r["mag"]), float(r["magerr"]), band)
            except (KeyError, ValueError, TypeError):
                continue


def build():
    meta = load_roster()
    rows = []
    star_summ = {}
    for path in sorted(glob.glob(os.path.join(CACHE_DIR, "*.csv"))):
        sid = os.path.splitext(os.path.basename(path))[0]
        m = meta.get(sid, {})
        # group epochs by (band, night)
        bins = defaultdict(lambda: {"mag": [], "magerr": []})
        for mjd, mag, magerr, band in parse_lc(path):
            night = math.floor(mjd)
            b = bins[(band, night)]
            b["mag"].append(mag)
            b["magerr"].append(magerr)

        # count nights per band before the <5 cut
        nights_per_band = defaultdict(int)
        for (band, night) in bins:
            nights_per_band[band] += 1
        keep_bands = {b for b, n in nights_per_band.items() if n >= MIN_NIGHTS}

        star_rows = []
        for (band, night), b in bins.items():
            if band not in keep_bands:
                continue
            mags = b["mag"]
            errs = b["magerr"]
            n = len(mags)
            med_mag = statistics.median(mags)
            med_err = statistics.median(errs)
            if n >= 2:
                sd = statistics.pstdev(mags) if n < 3 else statistics.stdev(mags)
                scatter_se = sd / math.sqrt(n)
            else:
                scatter_se = 0.0
            report_se = med_err / math.sqrt(n)
            mag_err = max(scatter_se, report_se)
            star_rows.append({
                "source_id": sid,
                "band": band,
                "night_mjd": night,
                "night_date": mjd_to_iso(night),
                "mag_binned": round(med_mag, 6),
                "mag_err": round(mag_err, 6),
                "n_exp": n,
                "wd_class": m.get("wd_class", ""),
                "ra": m.get("ra", ""),
                "dec": m.get("dec", ""),
            })
        if star_rows:
            rows.extend(star_rows)
            star_summ[sid] = {b: nights_per_band[b] for b in keep_bands}

    rows.sort(key=lambda r: (r["source_id"], r["band"], r["night_mjd"]))
    cols = ["source_id", "band", "night_mjd", "night_date", "mag_binned",
            "mag_err", "n_exp", "wd_class", "ra", "dec"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    return rows, star_summ, meta


def report(rows, star_summ, meta):
    n_cached = len(glob.glob(os.path.join(CACHE_DIR, "*.csv")))
    stars = sorted(star_summ)
    print(f"cached responses         : {n_cached}")
    print(f"stars with >=1 series    : {len(stars)}")
    print(f"panel rows               : {len(rows)}")

    # nights per star (summed across bands)
    nps = [sum(v.values()) for v in star_summ.values()]
    if nps:
        nps_sorted = sorted(nps)
        print(f"nights-per-star min/med/max: {min(nps)} / "
              f"{nps_sorted[len(nps_sorted)//2]} / {max(nps)}")
    # per-band mag range + series count
    for band in ("zg", "zr"):
        bmags = [r["mag_binned"] for r in rows if r["band"] == band]
        bseries = len({r["source_id"] for r in rows if r["band"] == band})
        if bmags:
            print(f"band {band}: series={bseries} rows={len(bmags)} "
                  f"mag range {min(bmags):.3f}..{max(bmags):.3f}")
        else:
            print(f"band {band}: no surviving series")

    # class counts among stars that survived
    from collections import Counter
    cc = Counter(meta[s].get("wd_class", "") for s in stars)
    print("class counts (surviving stars):")
    for k, v in sorted(cc.items(), key=lambda x: -x[1]):
        print(f"    {v:3d}  {k}")

    # empties / dropouts
    dropped = []
    for path in glob.glob(os.path.join(CACHE_DIR, "*.csv")):
        sid = os.path.splitext(os.path.basename(path))[0]
        if sid not in star_summ:
            n = sum(1 for _ in parse_lc(path))
            dropped.append((sid, n))
    if dropped:
        print(f"stars dropped (no series >= {MIN_NIGHTS} nights): {len(dropped)}")
        for sid, n in sorted(dropped):
            reason = "empty (0 clean epochs)" if n == 0 else f"{n} clean epochs, all series <{MIN_NIGHTS} nights"
            print(f"    {sid}: {reason}")


if __name__ == "__main__":
    rows, star_summ, meta = build()
    print(f"wrote {OUT}\n")
    report(rows, star_summ, meta)
