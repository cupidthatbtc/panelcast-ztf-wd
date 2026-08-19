#!/usr/bin/env python3
"""Build crossmatched exposure, nightly, monthly, and census products."""

import argparse
import gzip
import json
import math
from pathlib import Path

import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PALOMAR = EarthLocation.from_geodetic(
    lon=-116.8630 * u.deg,
    lat=33.3563 * u.deg,
    height=1706 * u.m,
)
BANDS = ("zg", "zr")
MIN_EXPOSURES_PER_BAND = 20
OID_CLUSTER_ARCSEC = 1.5

EXPOSURE_COLUMNS = [
    "source_id",
    "band",
    "oid",
    "mjd",
    "bjd_tdb",
    "night_mjd",
    "mag",
    "magerr",
    "chi",
    "ra",
    "dec",
]
NIGHTLY_COLUMNS = [
    "source_id",
    "band",
    "night_mjd",
    "night_date",
    "mag_binned",
    "mag_err",
    "n_exp",
]
MONTHLY_COLUMNS = [
    "source_id",
    "band",
    "month_id",
    "month_date",
    "year",
    "mag_binned",
    "mag_err",
    "n_exp",
    "n_nights",
]


def angular_separation_arcsec(
    ra1: np.ndarray | float,
    dec1: np.ndarray | float,
    ra2: np.ndarray | float,
    dec2: np.ndarray | float,
) -> np.ndarray:
    ra1_rad = np.deg2rad(ra1)
    dec1_rad = np.deg2rad(dec1)
    ra2_rad = np.deg2rad(ra2)
    dec2_rad = np.deg2rad(dec2)
    delta_ra = ra1_rad - ra2_rad
    cos_angle = (
        np.sin(dec1_rad) * np.sin(dec2_rad)
        + np.cos(dec1_rad) * np.cos(dec2_rad) * np.cos(delta_ra)
    )
    return np.rad2deg(np.arccos(np.clip(cos_angle, -1.0, 1.0))) * 3600.0


def read_cache(path: Path) -> pd.DataFrame:
    required = {
        "oid",
        "mjd",
        "mag",
        "magerr",
        "catflags",
        "filtercode",
        "ra",
        "dec",
        "chi",
    }
    try:
        frame = pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=sorted(required))
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing cache columns: {sorted(missing)}")
    return frame


def select_nearest_source(
    frame: pd.DataFrame,
    target_ra: float,
    target_dec: float,
) -> tuple[pd.DataFrame, float, int, int]:
    coordinates = frame.dropna(subset=["oid", "ra", "dec"]).copy()
    if coordinates.empty:
        return frame.iloc[0:0].copy(), math.nan, 0, 0
    coordinates["oid"] = coordinates["oid"].astype(str)
    objects = coordinates.groupby("oid", as_index=False).agg(
        object_ra=("ra", "median"),
        object_dec=("dec", "median"),
    )
    objects["target_separation_arcsec"] = angular_separation_arcsec(
        objects["object_ra"].to_numpy(),
        objects["object_dec"].to_numpy(),
        target_ra,
        target_dec,
    )
    nearest = objects.loc[objects["target_separation_arcsec"].idxmin()]
    objects["nearest_object_separation_arcsec"] = angular_separation_arcsec(
        objects["object_ra"].to_numpy(),
        objects["object_dec"].to_numpy(),
        float(nearest["object_ra"]),
        float(nearest["object_dec"]),
    )
    selected_oids = set(
        objects.loc[
            objects["nearest_object_separation_arcsec"] <= OID_CLUSTER_ARCSEC,
            "oid",
        ]
    )
    selected = frame[frame["oid"].astype(str).isin(selected_oids)].copy()
    return selected, float(nearest["target_separation_arcsec"]), len(objects), len(selected_oids)


def clean_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    band_ok = frame["filtercode"].isin(BANDS)
    catflags = pd.to_numeric(frame["catflags"], errors="coerce")
    mag = pd.to_numeric(frame["mag"], errors="coerce")
    magerr = pd.to_numeric(frame["magerr"], errors="coerce")
    chi = pd.to_numeric(frame["chi"], errors="coerce")
    mjd = pd.to_numeric(frame["mjd"], errors="coerce")

    valid_catflags = catflags.eq(0)
    valid_mag = np.isfinite(mag)
    valid_magerr = np.isfinite(magerr) & magerr.gt(0)
    valid_chi = np.isfinite(chi) & chi.lt(4)
    valid_mjd = np.isfinite(mjd)
    keep = band_ok & valid_catflags & valid_mag & valid_magerr & valid_chi & valid_mjd
    counts = {
        "selected_rows": len(frame),
        "drop_unsupported_band": int((~band_ok).sum()),
        "drop_catflags": int((band_ok & ~valid_catflags).sum()),
        "drop_invalid_mag": int((band_ok & valid_catflags & ~valid_mag).sum()),
        "drop_invalid_magerr": int(
            (band_ok & valid_catflags & valid_mag & ~valid_magerr).sum()
        ),
        "drop_chi": int(
            (band_ok & valid_catflags & valid_mag & valid_magerr & ~valid_chi).sum()
        ),
        "drop_invalid_mjd": int(
            (
                band_ok
                & valid_catflags
                & valid_mag
                & valid_magerr
                & valid_chi
                & ~valid_mjd
            ).sum()
        ),
    }
    cleaned = frame.loc[keep].copy()
    cleaned["band"] = cleaned["filtercode"]
    for column, values in (("mag", mag), ("magerr", magerr), ("chi", chi), ("mjd", mjd)):
        cleaned[column] = values.loc[cleaned.index].astype(float)
    cleaned["oid"] = cleaned["oid"].astype(str)
    cleaned["night_mjd"] = np.floor(cleaned["mjd"]).astype(int)
    return cleaned, counts


def add_bjd(frame: pd.DataFrame, ra: float, dec: float) -> pd.DataFrame:
    times = Time(
        frame["mjd"].to_numpy(),
        format="mjd",
        scale="utc",
        location=PALOMAR,
    )
    coordinate = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs")
    frame = frame.copy()
    frame["bjd_tdb"] = (
        times.tdb + times.light_travel_time(coordinate, kind="barycentric")
    ).jd
    return frame


def nightly_panel(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (source_id, band, night), group in frame.groupby(
        ["source_id", "band", "night_mjd"], sort=True
    ):
        magnitudes = group["mag"].to_numpy(dtype=float)
        errors = group["magerr"].to_numpy(dtype=float)
        n_exp = len(group)
        if n_exp >= 3:
            scatter = float(np.std(magnitudes, ddof=1))
        elif n_exp == 2:
            scatter = float(np.std(magnitudes, ddof=0))
        else:
            scatter = 0.0
        mag_err = max(
            scatter / math.sqrt(n_exp),
            float(np.median(errors)) / math.sqrt(n_exp),
        )
        rows.append(
            {
                "source_id": source_id,
                "band": band,
                "night_mjd": int(night),
                "night_date": pd.Timestamp("1858-11-17")
                + pd.to_timedelta(int(night), unit="D"),
                "mag_binned": float(np.median(magnitudes)),
                "mag_err": mag_err,
                "n_exp": n_exp,
            }
        )
    return pd.DataFrame(rows, columns=NIGHTLY_COLUMNS)


def monthly_panel(nightly: pd.DataFrame) -> pd.DataFrame:
    frame = nightly.copy()
    frame["month_id"] = pd.to_datetime(frame["night_date"]).dt.to_period("M").astype(str)
    monthly = (
        frame.groupby(["source_id", "band", "month_id"], as_index=False)
        .agg(
            mag_binned=("mag_binned", "median"),
            mag_err=("mag_err", "median"),
            n_exp=("n_exp", "sum"),
            n_nights=("night_mjd", "size"),
        )
        .sort_values(["source_id", "band", "month_id"])
    )
    monthly["month_date"] = pd.to_datetime(monthly["month_id"] + "-01")
    monthly["year"] = monthly["month_date"].dt.year
    return monthly[MONTHLY_COLUMNS]


def scatter_over_error(values: pd.Series, errors: pd.Series) -> float:
    if len(values) < 2:
        return math.nan
    denominator = float(np.median(errors.to_numpy(dtype=float)))
    if not math.isfinite(denominator) or denominator <= 0:
        return math.nan
    return float(np.std(values.to_numpy(dtype=float), ddof=0) / denominator)


def census_row(
    meta: object,
    exposures: pd.DataFrame,
    nightly: pd.DataFrame,
    monthly: pd.DataFrame,
) -> dict[str, object]:
    row = {
        "source_id": meta.source_id,
        "wdj_name": meta.wdj_name,
        "gaia_g_mag": meta.gaia_g_mag,
        "bp_rp": meta.bp_rp,
        "in_core": meta.in_core,
        "n_variants": meta.n_variants,
        "known_roster": meta.known_roster,
        "wd_class": meta.wd_class,
        "paper_variable": meta.paper_variable,
        "paper_periodic": meta.paper_periodic,
    }
    for band in BANDS:
        exp = exposures[exposures["band"] == band].copy()
        exp["residual"] = exp["mag"] - exp.groupby("night_mjd")["mag"].transform("median")
        night = nightly[nightly["band"] == band]
        month = monthly[monthly["band"] == band]
        row[f"{band}_n_exp"] = len(exp)
        row[f"{band}_n_nights"] = len(night)
        row[f"{band}_n_months"] = len(month)
        row[f"{band}_exposure_ratio"] = scatter_over_error(exp["residual"], exp["magerr"])
        row[f"{band}_nightly_ratio"] = scatter_over_error(night["mag_binned"], night["mag_err"])
        row[f"{band}_monthly_ratio"] = scatter_over_error(month["mag_binned"], month["mag_err"])

    ratio_columns = [f"{band}_{cadence}_ratio" for band in BANDS for cadence in ("exposure", "nightly", "monthly")]
    row["census_variable"] = any(
        math.isfinite(float(row[column])) and float(row[column]) >= 2.5
        for column in ratio_columns
    )
    row["census_g_nightly"] = bool(row["zg_nightly_ratio"] >= 2.5)
    row["census_g_monthly"] = bool(row["zg_monthly_ratio"] >= 2.5)
    row["census_verdict"] = "variable" if row["census_variable"] else "not_variable"
    return row


def write_frame(handle: object, frame: pd.DataFrame, columns: list[str], header: bool) -> None:
    frame.to_csv(handle, columns=columns, index=False, header=header, lineterminator="\n")


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
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full",
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    exposure_star_dir = args.out_dir / "exposure_stars"
    exposure_star_dir.mkdir(parents=True, exist_ok=True)

    roster = pd.read_csv(args.roster, dtype={"source_id": str})
    if len(roster) != 1423:
        raise ValueError("rebuilt roster must contain 1,423 rows")

    exposure_path = args.out_dir / "exposures.csv.gz"
    nightly_path = args.out_dir / "nightly_panel.csv.gz"
    monthly_path = args.out_dir / "monthly_panel.csv.gz"
    qc_rows: list[dict[str, object]] = []
    census_rows: list[dict[str, object]] = []
    crossmatched = 0

    with (
        gzip.open(exposure_path, "wt", encoding="utf-8", newline="") as exposure_handle,
        gzip.open(nightly_path, "wt", encoding="utf-8", newline="") as nightly_handle,
        gzip.open(monthly_path, "wt", encoding="utf-8", newline="") as monthly_handle,
    ):
        for index, meta in enumerate(roster.itertuples(index=False), 1):
            cache_path = args.cache_dir / f"{meta.source_id}.csv"
            qc: dict[str, object] = {
                "source_id": meta.source_id,
                "wdj_name": meta.wdj_name,
                "wd_class": meta.wd_class,
                "known_roster": meta.known_roster,
                "in_core": meta.in_core,
                "cache_present": cache_path.exists() and cache_path.stat().st_size > 0,
                "cache_bytes": cache_path.stat().st_size if cache_path.exists() else 0,
                "read_status": "ok",
            }
            if not qc["cache_present"]:
                qc["read_status"] = "missing"
                qc_rows.append(qc)
                continue
            try:
                raw = read_cache(cache_path)
                qc["raw_rows"] = len(raw)
                selected, separation, n_objects, n_selected_objects = select_nearest_source(
                    raw,
                    float(meta.ra),
                    float(meta.dec),
                )
                clean, drop_counts = clean_rows(selected)
                qc.update(drop_counts)
                qc["nearest_separation_arcsec"] = separation
                qc["ztf_objects_in_cone"] = n_objects
                qc["selected_ztf_objects"] = n_selected_objects
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
            clean = add_bjd(clean, float(meta.ra), float(meta.dec))
            clean = clean.sort_values(["band", "bjd_tdb"])
            clean[EXPOSURE_COLUMNS].to_csv(
                exposure_star_dir / f"{meta.source_id}.csv.gz",
                index=False,
            )
            nightly = nightly_panel(clean)
            monthly = monthly_panel(nightly)
            write_frame(exposure_handle, clean, EXPOSURE_COLUMNS, crossmatched == 1)
            write_frame(nightly_handle, nightly, NIGHTLY_COLUMNS, crossmatched == 1)
            write_frame(monthly_handle, monthly, MONTHLY_COLUMNS, crossmatched == 1)
            census_rows.append(census_row(meta, clean, nightly, monthly))

            if index % 50 == 0 or index == len(roster):
                print(f"[panels] {index:,}/{len(roster):,}; crossmatched={crossmatched:,}", flush=True)

    qc_frame = pd.DataFrame(qc_rows)
    census = pd.DataFrame(census_rows)
    qc_frame.to_csv(args.out_dir / "crossmatch_qc.csv", index=False)
    census.to_csv(args.out_dir / "census_full_catalog.csv", index=False)

    known = census[census["known_roster"].astype(bool)] if not census.empty else census
    manifest = {
        "stage_a_eq3_count": 22264,
        "stage_b_candidate_count": 1423,
        "stage_b_cross_variant_core": 1359,
        "stage_b_core_fraction": 1359 / 1423,
        "known_roster_in_stage_b": 20,
        "crossmatch_rule": "nearest ZTF coordinate cluster; >=20 QC-passing exposures in zg and zr",
        "nearest_cluster_radius_arcsec": OID_CLUSTER_ARCSEC,
        "row_qc": "catflags == 0; finite mag; finite magerr > 0; chi < 4; finite MJD",
        "crossmatched_count": crossmatched,
        "known_roster_crossmatched": len(known),
        "exposure_time_standard": "BJD_TDB",
        "census_threshold": 2.5,
        "selection_provenance": {
            "sigma_g_convention": "Gaia phot_g_n_obs / 9 per-CCD inference",
            "stage_b_multiplier": 1.1896,
            "paper_multiplier": 1.25,
            "membership_variants": 4,
        },
    }
    (args.out_dir / "census_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'census_full_catalog.csv'} ({len(census):,} stars)")
    print(f"crossmatched {crossmatched:,}/{len(roster):,}; known roster {len(known)}/20")


if __name__ == "__main__":
    main()
