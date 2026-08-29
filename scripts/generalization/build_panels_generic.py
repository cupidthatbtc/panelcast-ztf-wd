#!/usr/bin/env python3
"""Generic panel/census builder: frozen QC chain over a campaign roster.

Re-implements ONLY the roster/paths plumbing of build_catalog_panels.main();
every scientific operation (nearest-cluster crossmatch, row QC, BJD_TDB
conversion, nightly/monthly binning, 2.5-ratio census) is the frozen function
imported through frozen_api, applied verbatim.

Roster CSV contract (build_d3_roster.py writes this):
  source_id     19-digit campaign id (prefix 90/92/93/94)
  external_id   upstream name (e.g. KIC 8462852)
  ra, dec       ICRS degrees for the ZTF cone
  class_label   truth class (e.g. dsct_flag1, notdsct_flag0)
  label_variable, label_periodic   truth booleans (may be empty)
  gaia_g_mag    optional; empty allowed
Census output maps the frozen column names onto campaign semantics:
wdj_name<-external_id, wd_class<-class_label, paper_variable<-label_variable,
paper_periodic<-label_periodic, known_roster<-False, in_core<-True,
n_variants<-0, bp_rp<-NaN unless provided.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from frozen_api import (
    BANDS,
    EXPOSURE_COLUMNS,
    MIN_EXPOSURES_PER_BAND,
    MONTHLY_COLUMNS,
    NIGHTLY_COLUMNS,
    add_bjd,
    assert_frozen,
    campaign_id_ok,
    census_row,
    clean_rows,
    env_versions,
    frozen_file_shas,
    monthly_panel,
    nightly_panel,
    read_cache,
    select_nearest_source,
)


def roster_meta(row: pd.Series) -> SimpleNamespace:
    def opt_float(name: str) -> float:
        value = row.get(name)
        try:
            return float(value)
        except (TypeError, ValueError):
            return math.nan

    def opt_bool(name: str):
        value = row.get(name)
        if pd.isna(value) or value == "":
            return None
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

    return SimpleNamespace(
        source_id=str(row["source_id"]),
        wdj_name=str(row.get("external_id", "")),
        gaia_g_mag=opt_float("gaia_g_mag"),
        bp_rp=opt_float("bp_rp"),
        in_core=True,
        n_variants=0,
        known_roster=False,
        wd_class=str(row.get("class_label", "")),
        paper_variable=opt_bool("label_variable"),
        paper_periodic=opt_bool("label_periodic"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True,
                        help="IRSA response cache: <source_id>.csv per target")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--allow-nonstandard-ids", action="store_true")
    args = parser.parse_args()

    assert_frozen()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    exposure_star_dir = args.out_dir / "exposure_stars"
    exposure_star_dir.mkdir(parents=True, exist_ok=True)

    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    if not args.allow_nonstandard_ids:
        bad = [sid for sid in roster["source_id"] if not campaign_id_ok(sid)]
        if bad:
            raise SystemExit(f"{len(bad)} roster ids violate the campaign convention: {bad[:3]}")

    qc_rows: list[dict[str, object]] = []
    census_rows: list[dict[str, object]] = []
    crossmatched = 0

    for index, (_, row) in enumerate(roster.iterrows(), 1):
        meta = roster_meta(row)
        cache_path = args.cache_dir / f"{meta.source_id}.csv"
        qc: dict[str, object] = {
            "source_id": meta.source_id,
            "external_id": meta.wdj_name,
            "class_label": meta.wd_class,
            "cache_present": cache_path.exists() and cache_path.stat().st_size > 0,
            "read_status": "ok",
        }
        if not qc["cache_present"]:
            qc["read_status"] = "missing"
            qc_rows.append(qc)
            continue
        try:
            raw = read_cache(cache_path)
            qc["raw_rows"] = len(raw)
            selected, separation, n_objects, n_selected = select_nearest_source(
                raw, float(row["ra"]), float(row["dec"])
            )
            clean, drop_counts = clean_rows(selected)
            qc.update(drop_counts)
            qc["nearest_separation_arcsec"] = separation
            qc["ztf_objects_in_cone"] = n_objects
            qc["selected_ztf_objects"] = n_selected
        except Exception as exc:
            qc["read_status"] = "error"
            qc["error"] = repr(exc)
            qc_rows.append(qc)
            continue

        for band in BANDS:
            qc[f"{band}_raw_rows"] = int((raw["filtercode"] == band).sum())
            qc[f"{band}_clean_rows"] = int((clean["band"] == band).sum())
        is_crossmatched = all(
            qc[f"{band}_clean_rows"] >= MIN_EXPOSURES_PER_BAND for band in BANDS
        )
        qc["crossmatched"] = is_crossmatched
        qc_rows.append(qc)
        if not is_crossmatched:
            continue

        crossmatched += 1
        clean["source_id"] = meta.source_id
        clean = add_bjd(clean, float(row["ra"]), float(row["dec"]))
        clean = clean.sort_values(["band", "bjd_tdb"])
        clean[EXPOSURE_COLUMNS].to_csv(
            exposure_star_dir / f"{meta.source_id}.csv.gz", index=False
        )
        nightly = nightly_panel(clean)
        monthly = monthly_panel(nightly)
        census_rows.append(census_row(meta, clean, nightly, monthly))
        if index % 50 == 0 or index == len(roster):
            print(f"[panels-generic] {index:,}/{len(roster):,}; crossmatched={crossmatched:,}",
                  flush=True)

    pd.DataFrame(qc_rows).to_csv(args.out_dir / "crossmatch_qc.csv", index=False)
    pd.DataFrame(census_rows).to_csv(args.out_dir / "census_generic.csv", index=False)
    manifest = {
        "builder": "build_panels_generic.py",
        "roster": str(args.roster),
        "roster_rows": len(roster),
        "crossmatched_count": crossmatched,
        "crossmatch_rule": "frozen: nearest ZTF coordinate cluster; "
                           f">={MIN_EXPOSURES_PER_BAND} QC-passing exposures in zg and zr",
        "row_qc": "frozen: catflags == 0; finite mag; finite magerr > 0; chi < 4; finite MJD",
        "census_threshold": 2.5,
        "env": env_versions(),
        "frozen_sha256": frozen_file_shas(),
    }
    (args.out_dir / "panels_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[panels-generic] crossmatched {crossmatched:,}/{len(roster):,}")


if __name__ == "__main__":
    main()
