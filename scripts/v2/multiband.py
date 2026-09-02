#!/usr/bin/env python3
"""Mechanism 3 — joint two-band finder + phase-coherence test.

Frozen two-band rule: two independent Baluev votes, or one vote plus a
heuristic power-sum "multiband" top-5; no joint model, no phase test — so
detection >> recovery on both datasets. v2:

  finder    : astropy's LombScargleMultiband(method="fast") is, by
              construction, the chi^2-weighted sum of the per-band fast
              periodograms — numerically the frozen multiband power-sum
              (weights = sum of squared power per band). The joint
              periodogram is therefore computed with the frozen helper on the
              frozen grid (a test pins the identity with astropy).
  candidates: union of the top-15 per-band peaks and the top-15 joint peaks,
              clustered at 1.5/T in order of decreasing power ONLY (the
              frozen unaliased-first order would make the candidate set
              depend on the tunable veto constants), capped at 45 = every
              peak row; the alias flags enter the decision, not the set.
  joint fit : at each candidate one weighted least-squares fit of
              mean + A sin(2 pi f t + phi) per band (block-diagonal design,
              both bands on ONE time origin) -> A_g, A_r, phi_g, phi_r.
  coherence : |phi_g - phi_r| <= 0.15 cycle (wrapped)  AND  0.3 <= A_r/A_g <= 1.5.
"""

from __future__ import annotations

import math

import numpy as np

from v2_common import BANDS, DEFAULT, V2Constants


def wrapped_phase_difference_cycles(phase_a: float, phase_b: float) -> float:
    delta = abs(float(phase_a) - float(phase_b)) % 1.0
    return float(min(delta, 1.0 - delta))


def sinusoid_fit(
    time: np.ndarray, values: np.ndarray, errors: np.ndarray, frequency: float
) -> dict[str, float]:
    """Weighted least squares of y = c + b1 sin(2 pi f t) + b2 cos(2 pi f t):
    amplitude A = hypot(b1, b2), phase phi = atan2(b2, b1) so that the model is
    c + A sin(2 pi f t + phi); phases in cycles in (-0.5, 0.5]."""
    time = np.asarray(time, dtype=float)
    values = np.asarray(values, dtype=float)
    errors = np.asarray(errors, dtype=float)
    theta = 2.0 * np.pi * float(frequency) * time
    design = np.column_stack((np.ones_like(time), np.sin(theta), np.cos(theta)))
    inv_var = 1.0 / np.square(errors)
    normal = design.T @ (inv_var[:, None] * design)
    covariance = np.linalg.inv(normal)
    beta = np.linalg.solve(normal, design.T @ (inv_var * values))
    b1, b2 = float(beta[1]), float(beta[2])
    amplitude = float(math.hypot(b1, b2))
    if amplitude == 0.0:
        amplitude_error = float(np.sqrt(covariance[1, 1] + covariance[2, 2]))
        phase_error = 0.5
    else:
        gradient = np.array([b1, b2]) / amplitude
        amplitude_error = float(np.sqrt(gradient @ covariance[1:, 1:] @ gradient))
        phase_gradient = np.array([-b2, b1]) / (amplitude * amplitude)
        phase_error = float(np.sqrt(phase_gradient @ covariance[1:, 1:] @ phase_gradient)) / (2.0 * np.pi)
    return {
        "mean": float(beta[0]),
        "amplitude": amplitude,
        "amplitude_error": amplitude_error,
        "phase_cycles": float(math.atan2(b2, b1) / (2.0 * np.pi)),
        "phase_error_cycles": phase_error,
    }


def joint_fit(
    series: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], frequency: float
) -> dict[str, object]:
    """Per-band sinusoid fits at ONE frequency on the shared time origin. The
    joint design is block-diagonal (per-band mean and sinusoid), so the joint
    solution equals the per-band solutions; solving per band keeps the
    normal equations well conditioned."""
    fits = {band: sinusoid_fit(*series[band], frequency) for band in BANDS}
    amp_g, amp_r = fits["zg"]["amplitude"], fits["zr"]["amplitude"]
    ratio = (amp_r / amp_g) if amp_g > 0.0 else math.inf
    return {
        "frequency_per_day": float(frequency),
        "zg": fits["zg"],
        "zr": fits["zr"],
        "delta_phase_cycles": wrapped_phase_difference_cycles(
            fits["zg"]["phase_cycles"], fits["zr"]["phase_cycles"]
        ),
        "amp_ratio_r_over_g": float(ratio),
    }


def is_coherent(fit: dict[str, object], constants: V2Constants = DEFAULT) -> bool:
    ratio = float(fit["amp_ratio_r_over_g"])
    return bool(
        float(fit["delta_phase_cycles"]) <= constants.phase_tolerance_cycles
        and math.isfinite(ratio)
        and constants.amp_ratio_min <= ratio <= constants.amp_ratio_max
    )


def cluster_candidates(
    peak_rows: list[dict[str, object]], tolerance: float, max_candidates: int
) -> list[float]:
    """Frozen cluster_candidate_frequencies logic with ONE change: the order
    is by (-power, frequency) only — the frozen (alias flag, -power) order
    would make the candidate SET depend on the tunable veto constants. Keep a
    frequency only if no kept frequency lies within `tolerance`; capped at
    `max_candidates` (45 = every peak row by default)."""
    ordered = sorted(
        peak_rows,
        key=lambda row: (-float(row["power"]), float(row["frequency_per_day"])),
    )
    frequencies: list[float] = []
    for row in ordered:
        frequency = float(row["frequency_per_day"])
        if all(abs(frequency - kept) > tolerance for kept in frequencies):
            frequencies.append(frequency)
            if len(frequencies) == max_candidates:
                break
    return frequencies


__all__ = [
    "cluster_candidates", "is_coherent", "joint_fit", "sinusoid_fit",
    "wrapped_phase_difference_cycles",
]
