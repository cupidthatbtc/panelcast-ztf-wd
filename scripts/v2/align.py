#!/usr/bin/env python3
"""Mechanism 1 — per-oid, per-band zero-point alignment on SHARED nights.

The frozen pipeline merges every ZTF oid within 1.5 arcsec with no zero-point
alignment; its low pass subtracts a single weighted mean, so inter-oid
calibration steps become slow power plus alias combs (D3: false triggers rise
from 0 % at one oid to 48 % at five or more). v2 aligns first, per band:

  anchor = the oid with the most rows (ties: smallest oid label);
  for every other oid with n >= min_oid_rows rows and >= min_shared_nights
  nights in common with the anchor: on each shared night take the weighted
  median of the oid's rows and of the anchor's rows (weights 1/magerr^2);
  the offset is the weighted median over shared nights of their difference
  (weight = 1 / (var_oid,night + var_anchor,night)); the offset is
  subtracted from the oid's rows. Oids with too few rows or too few shared
  nights are left UNSHIFTED and flagged (their whole-row offset estimate is
  reported for the record). Same-night pairing means astrophysical
  variability on longer timescales cannot enter the offset (G-review 2026-09-02
  finding 9). Deterministic; no iteration.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from v2_common import BANDS, DEFAULT, V2Constants


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Smallest value whose cumulative weight reaches half the total weight
    (stable ordering, so ties are deterministic)."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if values.size == 0:
        raise ValueError("weighted_median of an empty array")
    order = np.argsort(values, kind="stable")
    ordered = values[order]
    cumulative = np.cumsum(weights[order])
    index = int(np.searchsorted(cumulative, 0.5 * cumulative[-1], side="left"))
    return float(ordered[min(index, ordered.size - 1)])


def _oid_labels(frame: pd.DataFrame) -> pd.Series:
    if "oid" not in frame.columns:
        return pd.Series(["0"] * len(frame), index=frame.index, dtype=object)
    return frame["oid"].astype(object).where(frame["oid"].notna(), "nan").astype(str)


def shared_night_offset(
    mags: np.ndarray, weights: np.ndarray, nights: np.ndarray,
    oid_mask: np.ndarray, anchor_mask: np.ndarray,
) -> tuple[float, int]:
    """(offset, n_shared_nights): weighted median over shared nights of the
    per-night weighted-median difference oid − anchor."""
    shared = np.intersect1d(np.unique(nights[oid_mask]), np.unique(nights[anchor_mask]))
    diffs, night_weights = [], []
    for night in shared:
        o = oid_mask & (nights == night)
        a = anchor_mask & (nights == night)
        diffs.append(weighted_median(mags[o], weights[o]) - weighted_median(mags[a], weights[a]))
        night_weights.append(1.0 / (1.0 / weights[o].sum() + 1.0 / weights[a].sum()))
    if not diffs:
        return float("nan"), 0
    return weighted_median(np.array(diffs), np.array(night_weights)), int(len(diffs))


def align_zero_points(
    frame: pd.DataFrame, constants: V2Constants = DEFAULT
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Return (aligned copy, per-oid table). The copy keeps the raw magnitude
    in `mag_raw` and replaces `mag` with the aligned magnitude; the table holds
    one row per (band, oid): band, oid, n, n_shared_nights, offset_mmag
    (the applied shared-night offset, or the unapplied whole-row estimate),
    applied, role."""
    aligned = frame.copy()
    aligned["oid_label"] = _oid_labels(aligned)
    aligned["mag_raw"] = aligned["mag"].astype(float)
    table: list[dict[str, object]] = []
    for band in BANDS:
        in_band = aligned["band"] == band
        sub = aligned.loc[in_band]
        if sub.empty:
            continue
        mags = sub["mag_raw"].to_numpy(dtype=float)
        weights = 1.0 / np.square(sub["magerr"].to_numpy(dtype=float))
        nights = sub["night_mjd"].to_numpy(dtype=float)
        labels = sub["oid_label"].to_numpy()
        counts = pd.Series(labels).value_counts()
        anchor = sorted(counts.index, key=lambda label: (-int(counts[label]), str(label)))[0]
        anchor_mask = labels == anchor
        anchor_level = weighted_median(mags[anchor_mask], weights[anchor_mask])
        for label in sorted(counts.index, key=str):
            mask = labels == label
            n = int(mask.sum())
            whole_row_offset = weighted_median(mags[mask], weights[mask]) - anchor_level
            if label == anchor:
                role, applied, offset, shared = "anchor", False, 0.0, int(np.unique(nights[mask]).size)
            elif n < constants.min_oid_rows:
                role, applied, offset, shared = "unshifted_too_few_rows", False, whole_row_offset, 0
            else:
                offset_shared, shared = shared_night_offset(mags, weights, nights, mask, anchor_mask)
                if shared >= constants.min_shared_nights:
                    role, applied, offset = "aligned", True, offset_shared
                    rows = sub.index[mask]
                    aligned.loc[rows, "mag"] = aligned.loc[rows, "mag_raw"] - offset
                else:
                    role, applied, offset = "unshifted_insufficient_overlap", False, whole_row_offset
            table.append({
                "band": band,
                "oid": str(label),
                "n": n,
                "n_shared_nights": int(shared),
                "offset_mmag": float(offset * 1000.0),
                "applied": bool(applied),
                "role": role,
            })
    return aligned, table


__all__ = ["align_zero_points", "shared_night_offset", "weighted_median"]
