#!/usr/bin/env python3
"""D2 truth model: analytic DAV signals for injection into real ZTF windows.

Why a truth model and not interpolation: DAV periods reach below twice the
TESS 120-s cadence (super-Nyquist) and below the first sinc null; interpolated
TESS photometry is undefined there. The published mode solution (period,
amplitude) IS the measurement — we evaluate it analytically at the template's
real BJD_TDB epochs.

Amplitude chain (GENERALIZATION_PLAN.md, D2):
  A_ppt (published, TESS-integrated)
    -> fractional flux (x 1e-3)
    -> de-dilution OFF by default (SPOC PDCSAP is crowding-corrected;
       ON = prespecified variant, divides by the published dilution if given)
    -> de-integrate the TESS exposure: divide by sinc(pi f T_cad);
       REJECT modes with |sinc| < 0.3 (do not amplify model error > 3.3x).
       Note: at T=120 s this cutoff is P < ~160.1 s (the plan text said
       "197 s", which is the |sinc| = 0.5 point — arithmetic slip, criterion
       |sinc| >= 0.3 is what was prespecified and is what runs).
    -> magnitudes (x 1.0857)
    -> bandpass ladder: A_g = R_g * A_TESS_intrinsic, A_r = R_rg * A_g with
       R_g in {1.4, 1.7, 2.1}, R_rg in {0.70, 0.80, 0.90}; blackbody T-derivative
       ratios at Teff ~ 11,500 K give (1.43, 0.80) — the ladder's low rung;
       empirical DAV multi-band ratios (limb darkening + nonadiabatic boost in
       the blue) motivate the upper rungs. Nominal (1.7, 0.80). Headline
       numbers are quoted as the band across the ladder.
    -> re-integrate the ZTF 30-s exposure: multiply by sinc(pi f 30s).

Phase protocol (frozen): each mode gets ONE independent phase; the base
assignment (phase_draw=0) seeds PCG64(TIC) and is shared across bands and
across every bandpass/de-dilution/amplitude-scale variant (variant-stable).
The two phase-draw sensitivity variants d in {1, 2} seed PCG64(TIC*10 + d)
— the ONLY thing that changes between phase draws is the phase vector.
A shared t_ref keeps the two-band evidence rule meaningful.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

PPT_TO_FRAC = 1.0e-3
FRAC_TO_MAG = 1.0857
ZTF_EXPOSURE_S = 30.0
SINC_REJECT_BELOW = 0.3
BANDPASS_LADDER_G = (1.4, 1.7, 2.1)
BANDPASS_LADDER_RG = (0.70, 0.80, 0.90)
NOMINAL_G = 1.7
NOMINAL_RG = 0.80

# band-effective wavelengths [nm] for the blackbody-derivative check
LAMBDA_NM = {"zg": 472.0, "zr": 642.0, "tess": 786.0}
HC_OVER_K_NM_K = 1.43877688e7  # h c / k_B in nm*K


def integration_sinc(period_s: float, t_int_s: float) -> float:
    """Signed attenuation of a sinusoid amplitude under boxcar integration."""
    x = math.pi * t_int_s / period_s
    return 1.0 if x == 0.0 else math.sin(x) / x


def blackbody_dlnB_dlnT(wavelength_nm: float, teff_k: float) -> float:
    x = HC_OVER_K_NM_K / (wavelength_nm * teff_k)
    return x / (1.0 - math.exp(-x))


def blackbody_amplitude_ratios(teff_k: float = 11500.0) -> tuple[float, float]:
    """(A_g/A_TESS, A_r/A_g) for pure temperature perturbations."""
    g = blackbody_dlnB_dlnT(LAMBDA_NM["zg"], teff_k)
    r = blackbody_dlnB_dlnT(LAMBDA_NM["zr"], teff_k)
    tess = blackbody_dlnB_dlnT(LAMBDA_NM["tess"], teff_k)
    return g / tess, r / g


@dataclass(frozen=True)
class TruthMode:
    period_s: float
    frequency_per_day: float
    amp_tess_ppt: float
    tess_sinc: float
    amp_g_mag: float          # intrinsic zg amplitude after ladder, before ZTF sinc
    amp_r_mag: float
    ztf_sinc: float
    phase_rad: float


@dataclass(frozen=True)
class TruthModel:
    tic: int
    cadence_s: float
    ratio_g: float
    ratio_rg: float
    dedilution: float | None
    modes: tuple[TruthMode, ...]
    rejected: tuple[dict, ...] = field(default=())

    def evaluate(self, bjd_tdb: np.ndarray, band: str, t_ref: float) -> np.ndarray:
        """Delta-mag time series at the template's real epochs (days)."""
        if band not in ("zg", "zr"):
            raise ValueError(band)
        delta = np.zeros_like(np.asarray(bjd_tdb, dtype=float))
        for mode in self.modes:
            amp = mode.amp_g_mag if band == "zg" else mode.amp_r_mag
            amp *= mode.ztf_sinc
            phase = 2.0 * np.pi * mode.frequency_per_day * (bjd_tdb - t_ref)
            delta += amp * np.cos(phase + mode.phase_rad)
        return delta


def build_truth_model(
    tic: int,
    periods_s: list[float],
    amps_ppt: list[float],
    cadence_s: float,
    ratio_g: float = NOMINAL_G,
    ratio_rg: float = NOMINAL_RG,
    dedilution: float | None = None,
    amplitude_scale: float = 1.0,
    phase_draw: int = 0,
    drop_dominant: bool = False,
) -> TruthModel:
    """amplitude_scale=0.0 builds a zero-amplitude null with the same modes;
    phase_draw in {0, 1, 2} selects the frozen phase assignment (0 = base);
    drop_dominant removes the largest-amplitude mode (nonstationarity
    sensitivity beyond a common multiplier: DAV modes can vanish outright)."""
    if len(periods_s) != len(amps_ppt):
        raise ValueError("periods and amplitudes must align")
    if drop_dominant and amps_ppt:
        dominant_index = int(np.argmax(amps_ppt))
        periods_s = [x for i, x in enumerate(periods_s) if i != dominant_index]
        amps_ppt = [x for i, x in enumerate(amps_ppt) if i != dominant_index]
    if phase_draw not in (0, 1, 2):
        raise ValueError("phase_draw must be 0, 1, or 2")
    seed = int(tic) if phase_draw == 0 else int(tic) * 10 + phase_draw
    rng = np.random.Generator(np.random.PCG64(seed))
    phases = rng.uniform(0.0, 2.0 * np.pi, size=len(periods_s))
    modes: list[TruthMode] = []
    rejected: list[dict] = []
    for period, amp_ppt, phase in zip(periods_s, amps_ppt, phases):
        tess_sinc = integration_sinc(period, cadence_s)
        if abs(tess_sinc) < SINC_REJECT_BELOW:
            rejected.append(
                {"period_s": period, "amp_ppt": amp_ppt, "tess_sinc": tess_sinc}
            )
            continue
        frac = amp_ppt * PPT_TO_FRAC * amplitude_scale
        if dedilution is not None:
            frac /= dedilution
        intrinsic_frac = frac / tess_sinc  # signed: negative sinc = pi phase flip
        amp_tess_mag = intrinsic_frac * FRAC_TO_MAG
        modes.append(
            TruthMode(
                period_s=period,
                frequency_per_day=86400.0 / period,
                amp_tess_ppt=amp_ppt,
                tess_sinc=tess_sinc,
                amp_g_mag=amp_tess_mag * ratio_g,
                amp_r_mag=amp_tess_mag * ratio_g * ratio_rg,
                ztf_sinc=integration_sinc(period, ZTF_EXPOSURE_S),
                phase_rad=float(phase),
            )
        )
    return TruthModel(
        tic=tic,
        cadence_s=cadence_s,
        ratio_g=ratio_g,
        ratio_rg=ratio_rg,
        dedilution=dedilution,
        modes=tuple(modes),
        rejected=tuple(rejected),
    )
