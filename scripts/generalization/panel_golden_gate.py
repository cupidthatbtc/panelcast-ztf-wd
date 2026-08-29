#!/usr/bin/env python3
"""Panel-stage golden gate: the frozen crossmatch/QC/BJD chain reproduces the
published exposure panel on THIS machine and environment.

The L-S replay gate consumes already-generated bjd_tdb, so it cannot detect
drift in the panel stage (astropy Time/light_travel_time, IERS tables, ERFA
build — G1 methods finding 6). This gate closes that hole: it re-derives the
exposure rows for sampled stars from the PUBLISHED raw IRSA cache using the
frozen functions exactly as build_catalog_panels.main() does (IERS
auto-download disabled; the pinned astropy-iers-data package supplies the
table) and compares against the published exposures.csv.gz:

  SCIENCE columns except bjd_tdb (source_id, band, mjd, night_mjd, mag,
  magerr) must be BYTE-identical; bjd_tdb is compared at <= 1 ulp (~40 us):
  the barycentric chain sits at double rounding boundaries, so any ns-level
  IERS-state difference since build time flips the last bit — measured on
  the production machine itself (2026-08-28). 1 ulp is 7e-7 cycles at the
  shortest searched period; the campaign pins IERS via astropy-iers-data
  with auto_download disabled and records the max ulp deviation. Carried
  metadata (oid, ra, dec, chi) is compared at <= 1 ulp, because the archived
  cache tarball is a re-serialization of the fetch-time responses (17-digit
  float strings) whose parse can differ from the original short strings by
  one ulp. chi additionally must not sit within 1e-9 of the QC boundary 4.0.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import tarfile
from pathlib import Path

import pandas as pd
from astropy.utils import iers

iers.conf.auto_download = False

from frozen_api import (  # noqa: E402
    EXPOSURE_COLUMNS,
    REPO_ROOT,
    add_bjd,
    assert_frozen,
    campaign_file_shas,
    clean_rows,
    env_versions,
    frozen_file_shas,
    read_cache,
    select_nearest_source,
)

PUBLISHED = REPO_ROOT / "catalog-rebuild/results/2026-08-01_full"


SCIENCE_COLUMNS = ["source_id", "band", "mjd", "night_mjd", "mag", "magerr"]
META_COLUMNS = ["ra", "dec", "chi"]


def rebuild_star(cache_bytes: bytes, ra: float, dec: float, source_id: str) -> pd.DataFrame:
    raw = read_cache(io.BytesIO(cache_bytes))
    selected, _, _, _ = select_nearest_source(raw, ra, dec)
    clean, _ = clean_rows(selected)
    clean["source_id"] = source_id
    clean = add_bjd(clean, ra, dec)
    clean = clean.sort_values(["band", "bjd_tdb"])
    return clean[EXPOSURE_COLUMNS].reset_index(drop=True)


def compare_star(rebuilt: pd.DataFrame, reference: pd.DataFrame) -> dict:
    import numpy as _np
    if len(rebuilt) != len(reference):
        return {"verdict": "MISMATCH", "reason": f"row count {len(rebuilt)} != {len(reference)}"}
    for col in ("mjd", "night_mjd", "mag", "magerr"):
        for side, frame in (("rebuilt", rebuilt), ("published", reference)):
            if not _np.isfinite(frame[col].to_numpy(dtype=float)).all():
                return {"verdict": "MISMATCH", "reason": f"nonfinite {col} ({side})"}
    sci_a = rebuilt[SCIENCE_COLUMNS].to_csv(index=False, lineterminator="\n")
    sci_b = reference[SCIENCE_COLUMNS].to_csv(index=False, lineterminator="\n")
    if sci_a != sci_b:
        for line_no, (a, b) in enumerate(zip(sci_a.splitlines(), sci_b.splitlines())):
            if a != b:
                return {"verdict": "MISMATCH", "reason": "science columns differ",
                        "first_diff_line": line_no, "rebuilt": a[:160], "published": b[:160]}
    import numpy as np
    bjd_a = rebuilt["bjd_tdb"].to_numpy(dtype=float)
    bjd_b = reference["bjd_tdb"].to_numpy(dtype=float)
    if not (np.isfinite(bjd_a).all() and np.isfinite(bjd_b).all()):
        return {"verdict": "MISMATCH", "reason": "nonfinite bjd_tdb"}
    bjd_ulp = np.abs(bjd_a - bjd_b) / np.spacing(np.abs(bjd_b))
    if (bjd_ulp > 1.0).any():
        worst = int(np.argmax(bjd_ulp))
        return {"verdict": "MISMATCH", "reason": "bjd_tdb beyond 1 ulp",
                "row": worst, "max_ulp": float(bjd_ulp.max())}
    if not (rebuilt["oid"].astype(str) == reference["oid"].astype(str)).all():
        return {"verdict": "MISMATCH", "reason": "oid differs"}
    chi = reference["chi"].to_numpy(dtype=float)
    if (abs(chi - 4.0) < 1e-9).any():
        return {"verdict": "MISMATCH", "reason": "chi within 1e-9 of QC boundary 4.0"}
    for col in META_COLUMNS:
        a = rebuilt[col].to_numpy(dtype=float)
        b = reference[col].to_numpy(dtype=float)
        if not (np.isfinite(a).all() and np.isfinite(b).all()):
            return {"verdict": "MISMATCH", "reason": f"nonfinite {col}"}
        ulp = np.spacing(np.abs(b))
        if (np.abs(a - b) > ulp).any():
            worst = int(np.argmax(np.abs(a - b) / np.maximum(ulp, 1e-300)))
            return {"verdict": "MISMATCH", "reason": f"{col} beyond 1 ulp",
                    "row": worst, "rebuilt": float(a[worst]), "published": float(b[worst])}
    all_exact = (bjd_ulp == 0.0).all() and all(
        (rebuilt[c].to_numpy(dtype=float) == reference[c].to_numpy(dtype=float)).all()
        for c in ("ra", "dec", "chi")
    )
    return {"verdict": "identical" if all_exact else "identical_1ulp",
            "bjd_max_ulp": float(bjd_ulp.max()),
            "bjd_rows_off_by_1ulp": int((bjd_ulp > 0).sum())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5,
                        help="stars to replay (>= 1 enforced)")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "outputs/generalization/panel_golden_report.json")
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("--count must be >= 1 (a vacuous gate cannot pass)")
    assert_frozen()
    campaign_start = campaign_file_shas()

    roster = pd.read_csv(REPO_ROOT / "data/roster/jestin2026_rebuilt_candidates.csv",
                         dtype={"source_id": str})
    coords = roster.set_index("source_id")[["ra", "dec"]]

    published = pd.read_csv(PUBLISHED / "data/exposures.csv.gz",
                            dtype={"source_id": str, "band": str})
    star_ids = sorted(published["source_id"].unique())
    stride = max(1, len(star_ids) // args.count)
    sample = star_ids[::stride][: args.count]

    records = []
    with tarfile.open(PUBLISHED / "data/irsa_raw_cache.tar.gz") as archive:
        for source_id in sample:
            member = archive.extractfile(f"catalog_lc_cache/{source_id}.csv")
            if member is None:
                records.append({"source_id": source_id, "verdict": "MISSING_CACHE"})
                continue
            rebuilt = rebuild_star(
                member.read(),
                float(coords.loc[source_id, "ra"]),
                float(coords.loc[source_id, "dec"]),
                source_id,
            )
            reference = published[published["source_id"] == source_id][
                EXPOSURE_COLUMNS
            ].reset_index(drop=True)
            record = {"source_id": source_id, "rows": len(reference),
                      **compare_star(rebuilt, reference)}
            records.append(record)
            print(f"[panel-golden] {source_id}: {record['verdict']}", flush=True)

    ids = [r["source_id"] for r in records]
    if not records or len(set(ids)) != len(ids):
        raise SystemExit("empty or duplicated star sample — gate invalid")
    passed = all(
        r["verdict"] in ("identical", "identical_1ulp") for r in records
    ) and len(records) >= args.count
    import hashlib
    if campaign_file_shas() != campaign_start:
        raise SystemExit("campaign code changed while the gate ran — report void")
    report = {"gate": "panel_golden_gate", "passed": passed, "stars": records,
              "env": env_versions(),
              "frozen_sha256": frozen_file_shas(),
              "campaign_sha256": campaign_start,
              "inputs": {
                  "exposures_sha256": hashlib.sha256(
                      (PUBLISHED / "data/exposures.csv.gz").read_bytes()).hexdigest(),
                  "raw_cache_sha256": hashlib.sha256(
                      (PUBLISHED / "data/irsa_raw_cache.tar.gz").read_bytes()).hexdigest(),
                  "roster_sha256": hashlib.sha256(
                      (REPO_ROOT / "data/roster/jestin2026_rebuilt_candidates.csv"
                       ).read_bytes()).hexdigest(),
              }}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[panel-golden] {'PASS' if passed else 'FAIL'} -> {args.out}")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
