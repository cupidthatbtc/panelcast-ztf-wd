#!/usr/bin/env python3
"""v2 decision rule (frozen wording kept for comparability).

  confirmed    : not window-aliased, not an alias of a stronger peak, the
                 candidate sits in the joint top-5, at least one band has
                 Baluev FAP < 1e-3 (unaliased in that band), AND the two-band
                 fit is coherent;
  candidate    : at least one band FAP < 1e-3 and unaliased, but incoherent
                 or not in the joint top-5;
  not_detected : otherwise.

Best pass = the frozen overall_result (imported), so the "best" semantics
match the baseline exactly. Per-band significance uses the frozen exact
power / Baluev FAP helpers; the alias tests are the v2 versions (window.py).
"""

from __future__ import annotations

import math

import numpy as np

from multiband import is_coherent, joint_fit
from v2_common import (
    BANDS,
    DEFAULT,
    FrequencyGrid,
    V2Constants,
    baluev_fap,
    exact_power_and_amplitude,
)
from window import is_alias_of_stronger_v2, is_window_alias_v2

STATUS_ORDER = {"confirmed": 0, "candidate": 1, "not_detected": 2}


def decide(row: dict[str, object], constants: V2Constants = DEFAULT) -> tuple[str, str, str]:
    """(status, basis, reason) from a candidate row carrying per-band fap /
    alias flags, joint_top5 and coherent."""
    significant = [
        band for band in BANDS
        if float(row[f"{band}_fap"]) < constants.fap_threshold and not bool(row[f"{band}_alias"])
    ]
    if not significant:
        return "not_detected", "", "no_unaliased_significant_band"
    if bool(row["joint_top5"]) and bool(row["coherent"]):
        return "confirmed", "coherent+" + "+".join(significant), ""
    reasons = []
    if not bool(row["joint_top5"]):
        reasons.append("not_joint_top5")
    if not bool(row["coherent"]):
        reasons.append("incoherent")
    return "candidate", "+".join(significant), "+".join(reasons)


def evaluate_candidates_v2(
    source_id: str,
    pass_name: str,
    frequencies: list[float],
    grid: FrequencyGrid,
    series: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]],
    peak_rows: list[dict[str, object]],
    joint_top_frequencies: list[float],
    loci: dict[str, list[dict[str, object]]],
    tolerance: float,
    constants: V2Constants = DEFAULT,
    cross_pass_stronger: dict[str, list[float]] | None = None,
    cross_pass_all: dict[str, list[float]] | None = None,
) -> list[dict[str, object]]:
    """`cross_pass_stronger[band]`: UNALIASED significant candidate
    frequencies of the OTHER pass (the low pass, evaluated first) — a
    high-pass candidate that is a solar/sidereal difference or mirror alias of
    a strong low-frequency signal (e.g. 48 - f0) is vetoed although f0 is not
    on the high grid. `cross_pass_all[band]`: ALL significant low-pass
    candidate frequencies; the partners among them are recorded per candidate
    so the veto can be re-derived exactly for other n_window_peaks values."""
    cross_pass_stronger = cross_pass_stronger or {}
    cross_pass_all = cross_pass_all or {}
    candidates: list[dict[str, object]] = []
    for frequency in frequencies:
        row: dict[str, object] = {
            "source_id": source_id,
            "pass": pass_name,
            "frequency_per_day": float(frequency),
            "period_days": 1.0 / frequency,
            "period_seconds": 86400.0 / frequency,
        }
        for band in BANDS:
            time, values, errors = series[band]
            power, amplitude, amplitude_error = exact_power_and_amplitude(time, values, errors, frequency)
            fap = baluev_fap(time, values, errors, power, grid)
            window_alias, window_power, locus = is_window_alias_v2(
                time, frequency, tolerance, loci[band], constants
            )
            stronger = [
                float(peak["frequency_per_day"])
                for peak in peak_rows
                if peak["series"] == band and float(peak["power"]) > power
            ]
            same_series_alias = is_alias_of_stronger_v2(frequency, stronger, tolerance)
            cross_alias = is_alias_of_stronger_v2(
                frequency, list(cross_pass_stronger.get(band, [])), tolerance
            )
            stronger_alias = same_series_alias or cross_alias
            row[f"{band}_same_series_alias"] = bool(same_series_alias)
            row[f"{band}_cross_pass_alias"] = bool(cross_alias)
            row[f"{band}_cross_pass_partners"] = [
                partner for partner in cross_pass_all.get(band, [])
                if is_alias_of_stronger_v2(frequency, [partner], tolerance)
            ]
            row[f"{band}_power"] = float(power)
            row[f"{band}_fap"] = float(fap)
            row[f"{band}_amplitude_mmag"] = float(amplitude * 1000.0)
            row[f"{band}_amplitude_error_mmag"] = float(amplitude_error * 1000.0)
            row[f"{band}_window_power"] = float(window_power)
            row[f"{band}_window_locus"] = locus
            row[f"{band}_stronger_alias"] = bool(stronger_alias)
            row[f"{band}_alias"] = bool(window_alias or stronger_alias)
        fit = joint_fit(series, frequency)
        row["zg_phase_cycles"] = fit["zg"]["phase_cycles"]
        row["zr_phase_cycles"] = fit["zr"]["phase_cycles"]
        row["zg_phase_error_cycles"] = fit["zg"]["phase_error_cycles"]
        row["zr_phase_error_cycles"] = fit["zr"]["phase_error_cycles"]
        row["delta_phase_cycles"] = fit["delta_phase_cycles"]
        row["amp_ratio_r_over_g"] = (
            fit["amp_ratio_r_over_g"] if math.isfinite(fit["amp_ratio_r_over_g"]) else None
        )
        row["coherent"] = is_coherent(fit, constants)
        row["joint_top5"] = any(abs(frequency - value) <= tolerance for value in joint_top_frequencies)
        row["multiband_top5"] = row["joint_top5"]   # frozen key, v2 meaning
        status, basis, reason = decide(row, constants)
        row["status"] = status
        row["basis"] = basis
        row["candidate_reason"] = reason
        row["best_band_fap"] = min(float(row["zg_fap"]), float(row["zr_fap"]))
        candidates.append(row)
    candidates.sort(
        key=lambda row: (STATUS_ORDER[str(row["status"])], float(row["best_band_fap"]),
                         float(row["frequency_per_day"]))
    )
    return candidates


__all__ = ["STATUS_ORDER", "decide", "evaluate_candidates_v2"]
