#!/usr/bin/env python3
"""D2 truth model: analytic DAV signals for injection into real ZTF windows.

Why a truth model and not interpolation: DAV periods reach below twice the
TESS 120-s cadence (super-Nyquist) and below the first sinc null; interpolated
TESS photometry is undefined there. The published mode solution (period,
amplitude) IS the measurement — we evaluate it analytically at the template's
real BJD_TDB epochs.

Amplitude chain (GENERALIZATION_PLAN.md, D2):
  A_ppt (published, TESS-integrated, PDCSAP = already crowding-corrected —
         Romero+2022 and Romero+2025 both state their amplitudes are
         dilution-corrected)
    -> fractional flux (x 1e-3)
    -> crowding sensitivity (G3 numerics finding 4): the prespecified variant
       is the SAP-EQUIVALENT RE-DILUTION, A_variant = A_PDCSAP x CROWDSAP
       (multiplication; dividing PDCSAP by CROWDSAP again would inflate the
       injected amplitude ~5x at the median CROWDSAP of 0.19). OFF by default
       (crowdsap=None); scheduled only for SPOC-verified stars.
    -> de-integrate the TESS exposure: divide by sinc(pi f T_cad);
       REJECT modes with |sinc| < 0.3 (do not amplify model error > 3.3x).
       At T=120 s this cutoff is P < ~160.0 s; at 20 s, P < ~26.7 s.
    -> magnitudes (x 1.0857)
    -> bandpass ladder: A_g = R_g * A_TESS_intrinsic, A_r = R_rg * A_g with
       R_g in {1.4, 1.7, 2.1}, R_rg in {0.70, 0.80, 0.90}; blackbody T-derivative
       ratios at Teff ~ 11,500 K give (1.43, 0.80) — the ladder's low rung;
       empirical DAV multi-band ratios (limb darkening + nonadiabatic boost in
       the blue) motivate the upper rungs. Nominal (1.7, 0.80). Headline
       numbers are quoted as the band across the ladder.
    -> re-integrate the ZTF 30-s exposure: multiply by sinc(pi f 30s).

Phase protocol (frozen): each mode of the COMPLETE published mode list gets
ONE independent phase, drawn in published-table order BEFORE sinc rejection
and before any dropout, so a mode's phase is a function of (TIC, phase_draw,
table position) only. The base assignment (phase_draw=0) seeds PCG64(TIC) and
is shared across bands and across every bandpass/crowding/amplitude-scale/
dropout variant (variant-stable). The two phase-draw sensitivity variants
d in {1, 2} seed PCG64(TIC*10 + d) — the ONLY thing that changes between phase
draws is the phase vector. A shared t_ref keeps the two-band evidence rule
meaningful.

Dominant-mode dropout (G3 numerics finding 3): the dropped mode is the
largest-amplitude RETAINED (post-sinc) mode; every surviving mode keeps the
phase it has in the nominal model; dropout is defined only when >= 2 modes are
retained (the builder checks `retained_modes` first).

This module also owns the D2 manifest CONTRACT (column schema + scenario
codes) so the shard builder and the metrics program cannot drift apart.
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

# ----------------------------------------------------------------- contract
# Campaign id layout (19 digits): AA TTTTTTTTTT K GR PS C0
#   AA arm prefix (92 = arm B, 93 = arm A), T zero-padded TIC, K template index
#   (0/1/2), G/R ladder indices (1-3; 22 = nominal), P phase-draw (0-2),
#   S amplitude-scale code (below), C crowding-variant code (0 = PDCSAP as
#   published, 1 = SAP-equivalent re-dilution), trailing 0 reserved.
#   Nulls: 94 + 17-digit serial. Controls: 95 + 17-digit index of the template
#   in the sorted fixed 928-window pool. Self-window diagnostic: 96 prefix.
AMP_SCALE_CODES = {1.0: 0, 0.7: 1, 1.3: 2}
AMP_SCALE_CODE_DROPOUT = 3          # amp_scale 1.0 with the dominant mode dropped
CROWD_CODE_NONE = 0
CROWD_CODE_REDILUTION = 1

SCENARIO_NOMINAL = "nominal"
SCENARIO_CONTROL = "control"
SCENARIO_NULL = "gauss_null"   # never the token "null": pandas parses it as NaN
SCENARIO_DROPOUT = "dropout"

# Fixed manifest schema: EVERY row of EVERY arm carries EVERY column with a
# typed value (G3 methods finding 1) — no NaN in int/bool columns, ever.
MANIFEST_COLUMNS: tuple[tuple[str, str], ...] = (
    ("campaign_id", "str"),
    ("arm", "str"),                 # A | B | ctrl | gauss_null (never "null": a pandas NA token)
    ("scenario", "str"),            # nominal | ladder_g{i}r{j} | phase_{d} | ampscale_{s} | dropout | redilution | control | gauss_null
    ("tic", "int"),                 # 0 for ctrl/null
    ("template_source_id", "str"),
    ("template_status", "str"),     # published blind_status of the window (metadata only)
    ("template_k", "int"),          # 0/1/2 for A/B; -1 for ctrl/null
    ("pool_index", "int"),          # index of the window in the sorted 928 pool
    ("template_exp_per_night", "float"),
    ("ratio_g", "float"),           # 0.0 for ctrl/null
    ("ratio_rg", "float"),
    ("phase_draw", "int"),          # 0 for ctrl/null
    ("amp_scale", "float"),         # 1.0 for A/B unless ampscale scenario; 0.0 for null; 1.0 ctrl
    ("dominant_dropped", "bool"),
    ("dropped_period_s", "float"),  # nan unless dominant_dropped
    ("crowdsap", "float"),          # nan unless redilution scenario
    ("n_strata_scheduled", "int"),  # 3 nominal A/B, 1 sensitivity scenarios, 0 ctrl/null
    ("match", "str"),               # tol_0.25 | tol_0.5 | nearest | ""
    ("control_campaign_id", "str"), # paired control for arm B; "" otherwise
    ("null_serial", "int"),         # 0..N-1 for nulls; -1 otherwise
    ("n_modes_injected", "int"),
    ("n_modes_rejected", "int"),
    ("shard_sha256", "str"),
)
MANIFEST_COLUMN_NAMES = tuple(name for name, _ in MANIFEST_COLUMNS)
INJECTED_MODE_COLUMNS = ("campaign_id", "period_s", "frequency_per_day", "amp_tess_ppt",
                         "tess_sinc", "ztf_sinc", "amp_g_mag", "amp_r_mag", "phase_rad")
REJECTED_MODE_COLUMNS = ("campaign_id", "period_s", "amp_ppt", "tess_sinc")


def scenario_code(ratio_g: float, ratio_rg: float, phase_draw: int, amp_scale: float,
                  dominant_dropped: bool, crowd_code: int = CROWD_CODE_NONE) -> str:
    """Immutable scenario identity (G3 methods finding 2)."""
    nominal_ratios = ratio_g == NOMINAL_G and ratio_rg == NOMINAL_RG
    if crowd_code == CROWD_CODE_REDILUTION:
        return "redilution"
    if dominant_dropped:
        return SCENARIO_DROPOUT
    if not nominal_ratios:
        gi = BANDPASS_LADDER_G.index(ratio_g) + 1
        ri = BANDPASS_LADDER_RG.index(ratio_rg) + 1
        return f"ladder_g{gi}r{ri}"
    if phase_draw != 0:
        return f"phase_{phase_draw}"
    if amp_scale != 1.0:
        return f"ampscale_{amp_scale}"
    return SCENARIO_NOMINAL


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


def retained_modes(periods_s: list[float], amps_ppt: list[float],
                   cadence_s: float) -> list[int]:
    """Indices (published-table order) of modes surviving the |sinc| >= 0.3
    rule — the set over which 'dominant' is defined."""
    return [i for i, p in enumerate(periods_s)
            if abs(integration_sinc(p, cadence_s)) >= SINC_REJECT_BELOW]


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
    crowdsap: float | None
    amplitude_scale: float
    phase_draw: int
    dominant_dropped: bool
    dropped_period_s: float | None
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
    crowdsap: float | None = None,
    amplitude_scale: float = 1.0,
    phase_draw: int = 0,
    drop_dominant: bool = False,
) -> TruthModel:
    """amplitude_scale=0.0 builds a zero-amplitude null with the same modes;
    phase_draw in {0, 1, 2} selects the frozen phase assignment (0 = base);
    crowdsap (0 < c <= 1) selects the SAP-equivalent re-dilution variant
    (amplitudes MULTIPLIED by CROWDSAP); drop_dominant removes the
    largest-amplitude RETAINED mode while every survivor keeps its phase."""
    if len(periods_s) != len(amps_ppt):
        raise ValueError("periods and amplitudes must align")
    if phase_draw not in (0, 1, 2):
        raise ValueError("phase_draw must be 0, 1, or 2")
    if crowdsap is not None and not (0.0 < crowdsap <= 1.0):
        raise ValueError(f"CROWDSAP must lie in (0, 1], got {crowdsap}")
    # phases for the COMPLETE published list, in table order, before any
    # rejection or dropout: a mode's phase never depends on other modes
    seed = int(tic) if phase_draw == 0 else int(tic) * 10 + phase_draw
    rng = np.random.Generator(np.random.PCG64(seed))
    phases = rng.uniform(0.0, 2.0 * np.pi, size=len(periods_s))
    keep = retained_modes(periods_s, amps_ppt, cadence_s)
    dropped_period: float | None = None
    if drop_dominant:
        if len(keep) < 2:
            raise ValueError("dominant-mode dropout needs >= 2 retained modes")
        dominant = max(keep, key=lambda i: (amps_ppt[i], -i))
        dropped_period = float(periods_s[dominant])
        keep = [i for i in keep if i != dominant]
    keep_set = set(keep)
    modes: list[TruthMode] = []
    rejected: list[dict] = []
    for index, (period, amp_ppt, phase) in enumerate(zip(periods_s, amps_ppt, phases)):
        tess_sinc = integration_sinc(period, cadence_s)
        if abs(tess_sinc) < SINC_REJECT_BELOW:
            rejected.append(
                {"period_s": period, "amp_ppt": amp_ppt, "tess_sinc": tess_sinc}
            )
            continue
        if index not in keep_set:
            continue  # the dropped dominant mode (recorded in dropped_period_s)
        frac = amp_ppt * PPT_TO_FRAC * amplitude_scale
        if crowdsap is not None:
            frac *= crowdsap  # SAP-equivalent re-dilution (never division)
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
        crowdsap=crowdsap,
        amplitude_scale=amplitude_scale,
        phase_draw=phase_draw,
        dominant_dropped=drop_dominant,
        dropped_period_s=dropped_period,
        modes=tuple(modes),
        rejected=tuple(rejected),
    )
