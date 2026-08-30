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
import pandas as pd

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
# Campaign id layout (19 digits): AA TTTTTTTTTT K GR PS CD
#   AA arm prefix (92 = arm B, 93 = arm A), T zero-padded TIC, K template index
#   (0/1/2), G/R ladder indices (1-3; 22 = nominal), P phase-draw (0-2),
#   S amplitude-scale code (below), C crowding-variant code (0 = PDCSAP as
#   published, 1 = SAP-equivalent re-dilution), D cadence code (0 = frozen
#   rule, 1 = cadence_alt pure-120-s endpoint; Amendment 3).
#   Nulls: 94 + 17-digit serial. Controls: 95 + 17-digit index of the template
#   in the sorted fixed 928-window pool. Self-window diagnostic: 96 prefix.
AMP_SCALE_CODES = {1.0: 0, 0.7: 1, 1.3: 2}
AMP_SCALE_CODE_DROPOUT = 3          # amp_scale 1.0 with the dominant mode dropped
CROWD_CODE_NONE = 0
CROWD_CODE_REDILUTION = 1
# Amendment 3 (G3 round-3 ADOPT-A): trailing id digit D = cadence code;
# cadence_alt = the conservative pure-120-s endpoint for targets whose
# published solution mixes 20-s and 120-s sectors (never pooled with nominal)
CADENCE_CODE_NOMINAL = 0
CADENCE_CODE_ALT = 1
CADENCE_ALT_S = 120.0
CADENCES_S = (20.0, 120.0)

SCENARIO_NOMINAL = "nominal"
SCENARIO_CADENCE_ALT = "cadence_alt"
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
    ("template_wg_contrasts", "int"),   # W_g = sum_nights max(n_zg,night - 1, 0): zg support surviving the frozen nightly-median subtraction (Amendment 4)
    ("ratio_g", "float"),           # 0.0 for ctrl/null
    ("ratio_rg", "float"),
    ("phase_draw", "int"),          # 0 for ctrl/null
    ("amp_scale", "float"),         # 1.0 for A/B unless ampscale scenario; 0.0 for null; 1.0 ctrl
    ("dominant_dropped", "bool"),
    ("dropped_period_s", "float"),  # nan unless dominant_dropped
    ("crowdsap", "float"),          # nan unless redilution scenario
    ("cadence_code", "int"),        # 0 nominal rule (20 iff any f sector) | 1 cadence_alt (120 s)
    ("cadence_s", "float"),         # integration time used by the truth model; 0.0 ctrl/null
    ("n_strata_scheduled", "int"),  # 3 nominal A/B, 1 sensitivity scenarios, 0 ctrl/null
    ("match", "str"),               # tol_0.25 | tol_0.5 | nearest | ""
    ("control_campaign_id", "str"), # paired control for arm B; "" otherwise
    ("null_serial", "int"),         # 0..N-1 for nulls; -1 otherwise
    ("n_modes_injected", "int"),
    ("n_modes_rejected", "int"),
    ("shard_sha256", "str"),
)
MANIFEST_COLUMN_NAMES = tuple(name for name, _ in MANIFEST_COLUMNS)
ARMS = ("A", "B", "ctrl", "gauss_null")
# the production run matrix (plan, D2 "Run matrix"): every arm below must be
# scheduled for a generation to be marked production (G3 methods round-2 new
# BLOCKING finding); 'redilution' is the prespecified stretch variant
MANDATORY_PRODUCTION_ARMS = ("b", "ctrl", "a", "ladder", "phase", "ampscale", "dropout",
                             "cadence_alt", "nulls")
MIXED_CADENCE_TARGETS_PRODUCTION = 33   # SPOC v3: targets whose solution mixes 20-s and 120-s sectors
TARGETS_PRODUCTION = 103
POOL_SIZE_PRODUCTION = 928
N_NULLS_PRODUCTION = 1000
# the code that determines shard BYTES; the generation id is derived from
# these files' SHAs (not the whole campaign snapshot) so later metrics/runner
# fixes do not orphan an already-run generation
D2_GENERATION_CODE = ("scripts/generalization/build_d2_shards.py",
                      "scripts/generalization/d2_truth_model.py",
                      "scripts/generalization/frozen_api.py")
AMP_SCALES = (1.0, 0.7, 1.3)
# Amendment 4 (G4): the K=0/1/2 matched windows are the round-half-even
# 10/50/90th-percentile positions of the magnitude-matched pool sorted by
# (W_g, source_id); the D2 surface's window axis is W_g with these frozen
# half-open edges = the 20/40/60/80th percentiles of the outcome-independent
# 928-window pool (computed 2026-08-30 with the frozen loader; the builder
# recomputes them from the attested pool and refuses production on mismatch)
WG_SURFACE_EDGES = (15, 41, 84, 217)
MATCH_LABELS = ("tol_0.25", "tol_0.5", "nearest")
BLIND_STATUSES = ("confirmed", "candidate", "not_detected")   # published catalog vocabulary
INJECTED_MODE_COLUMNS = ("campaign_id", "period_s", "frequency_per_day", "amp_tess_ppt",
                         "tess_sinc", "ztf_sinc", "amp_g_mag", "amp_r_mag", "phase_rad")
REJECTED_MODE_COLUMNS = ("campaign_id", "period_s", "amp_ppt", "tess_sinc")


def scenario_code(ratio_g: float, ratio_rg: float, phase_draw: int, amp_scale: float,
                  dominant_dropped: bool, crowd_code: int = CROWD_CODE_NONE,
                  cadence_code: int = CADENCE_CODE_NOMINAL) -> str:
    """Immutable scenario identity (G3 methods finding 2)."""
    nominal_ratios = ratio_g == NOMINAL_G and ratio_rg == NOMINAL_RG
    if cadence_code == CADENCE_CODE_ALT:
        return SCENARIO_CADENCE_ALT
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


# ------------------------------------------------------- ids + row semantics

def all_scenarios() -> set[str]:
    ladder = {f"ladder_g{gi}r{ri}" for gi in (1, 2, 3) for ri in (1, 2, 3)} - {"ladder_g2r2"}
    return ({SCENARIO_NOMINAL, SCENARIO_DROPOUT, "redilution", SCENARIO_CADENCE_ALT,
             "phase_1", "phase_2", "ampscale_0.7", "ampscale_1.3",
             SCENARIO_CONTROL, SCENARIO_NULL} | ladder)


def campaign_id(arm_prefix: str, tic: int, k: int, g_idx: int, r_idx: int,
                phase_draw: int = 0, amp_code: int = 0,
                crowd_code: int = CROWD_CODE_NONE,
                cadence_code: int = CADENCE_CODE_NOMINAL) -> str:
    """Layout AA TTTTTTTTTT K G R P S C D (D = cadence code, Amendment 3)."""
    sid = (f"{arm_prefix}{tic:010d}{k}{g_idx}{r_idx}"
           f"{phase_draw}{amp_code}{crowd_code}{cadence_code}")
    if len(sid) != 19 or not sid.isdigit():
        raise ValueError(f"malformed campaign id {sid}")
    return sid


def control_id(pool_index: int) -> str:
    return "95" + str(int(pool_index)).zfill(17)


def null_id(serial: int) -> str:
    return "94" + str(int(serial)).zfill(17)


def production_reasons(arms: set[str], limit, n_nulls: int, expected_pool: int,
                       n_targets_input: int) -> list[str]:
    """Empty list == production generation. Every reason is a hard fact about
    the arguments, never about the outcome."""
    reasons = []
    missing = sorted(set(MANDATORY_PRODUCTION_ARMS) - set(arms))
    if missing:
        reasons.append(f"arms missing {missing}")
    if limit is not None:
        reasons.append("limit")
    if n_nulls != N_NULLS_PRODUCTION:
        reasons.append("n_nulls")
    if expected_pool != POOL_SIZE_PRODUCTION:
        reasons.append("pool")
    if n_targets_input != TARGETS_PRODUCTION:
        reasons.append(f"targets {n_targets_input} != {TARGETS_PRODUCTION}")
    return reasons


def _row_problem(r) -> str:
    """Semantic invariants of ONE manifest row (G3 methods round-2 new MAJOR):
    enumerations, per-arm defaults, scenario recomputed from its fields, and
    the campaign id recomputed from its fields."""
    if r.arm not in ARMS:
        return f"arm {r.arm!r}"
    if r.scenario not in all_scenarios():
        return f"scenario {r.scenario!r}"
    if not (isinstance(r.shard_sha256, str) and len(r.shard_sha256) == 64):
        return "shard_sha256"
    if r.arm in ("A", "B"):
        if r.tic <= 0 or r.template_k not in (0, 1, 2) or r.pool_index < 0:
            return "tic/template_k/pool_index"
        if r.ratio_g not in BANDPASS_LADDER_G or r.ratio_rg not in BANDPASS_LADDER_RG:
            return "ratios"
        if r.phase_draw not in (0, 1, 2) or r.amp_scale not in AMP_SCALES:
            return "phase_draw/amp_scale"
        # absence is NaN EXACTLY; any present value must be finite and in range
        # (G3 methods round-4: inf must not read as "absent")
        crowd_present = not math.isnan(r.crowdsap)
        if crowd_present and not (math.isfinite(r.crowdsap) and 0.0 < r.crowdsap <= 1.0):
            return "crowdsap must be NaN (absent) or finite in (0, 1]"
        crowd = CROWD_CODE_REDILUTION if crowd_present else CROWD_CODE_NONE
        if r.match not in MATCH_LABELS or r.template_status not in BLIND_STATUSES:
            return "match/template_status vocabulary"
        if r.cadence_code not in (CADENCE_CODE_NOMINAL, CADENCE_CODE_ALT) or r.cadence_s not in CADENCES_S:
            return "cadence_code/cadence_s"
        # sensitivity axes are MUTUALLY EXCLUSIVE: nominal = no axis, every other
        # scenario = exactly one axis (G3 methods round-3: precedence must not
        # hide crossed axes)
        axes = [not (r.ratio_g == NOMINAL_G and r.ratio_rg == NOMINAL_RG),
                r.phase_draw != 0, r.amp_scale != 1.0, bool(r.dominant_dropped),
                crowd == CROWD_CODE_REDILUTION, r.cadence_code == CADENCE_CODE_ALT]
        if sum(axes) != (0 if r.scenario == SCENARIO_NOMINAL else 1):
            return "crossed or missing sensitivity axes for this scenario"
        if r.cadence_code == CADENCE_CODE_ALT and (
                r.cadence_s != CADENCE_ALT_S or r.arm != "B" or crowd != CROWD_CODE_NONE
                or bool(r.dominant_dropped) or r.phase_draw != 0 or r.amp_scale != 1.0
                or r.ratio_g != NOMINAL_G or r.ratio_rg != NOMINAL_RG):
            return "cadence_alt must be arm B, nominal ratios/phase/scale, no dropout/crowding, 120 s"
        if scenario_code(r.ratio_g, r.ratio_rg, r.phase_draw, r.amp_scale,
                         bool(r.dominant_dropped), crowd, r.cadence_code) != r.scenario:
            return "scenario inconsistent with its fields"
        dropped_present = not math.isnan(r.dropped_period_s)
        if dropped_present and not (math.isfinite(r.dropped_period_s) and r.dropped_period_s > 0.0):
            return "dropped_period_s must be NaN (absent) or a finite positive period"
        if bool(r.dominant_dropped) != dropped_present:
            return "dropped_period_s"
        if r.n_strata_scheduled != (3 if r.scenario == SCENARIO_NOMINAL else 1):
            return "n_strata_scheduled"
        if r.template_wg_contrasts < 0:
            return "template_wg_contrasts"
        if r.scenario != SCENARIO_NOMINAL and r.template_k != 1:
            return "sensitivity scenarios run on the median window only"
        if r.arm == "A" and r.scenario != SCENARIO_NOMINAL:
            return "arm A is nominal-only"
        if (r.arm == "B") != bool(r.control_campaign_id):
            return "control_campaign_id"
        if r.arm == "B" and r.control_campaign_id != control_id(r.pool_index):
            return "control_campaign_id value"
        if r.null_serial != -1 or r.n_modes_injected < 1:
            return "null_serial/n_modes_injected"
        amp_code = AMP_SCALE_CODE_DROPOUT if r.dominant_dropped else AMP_SCALE_CODES[r.amp_scale]
        expected = campaign_id("92" if r.arm == "B" else "93", int(r.tic), int(r.template_k),
                               BANDPASS_LADDER_G.index(r.ratio_g) + 1,
                               BANDPASS_LADDER_RG.index(r.ratio_rg) + 1,
                               int(r.phase_draw), amp_code, crowd, int(r.cadence_code))
        if r.campaign_id != expected:
            return f"campaign_id {r.campaign_id} != {expected}"
        return ""
    # controls and Gaussian nulls
    if r.tic != 0 or r.template_k != -1 or r.pool_index < 0:
        return "ctrl/null tic/template_k/pool_index"
    if r.template_wg_contrasts < 0:
        return "ctrl/null template_wg_contrasts"
    if r.match != "" or r.template_status not in BLIND_STATUSES:
        return "ctrl/null match/template_status"
    if r.ratio_g != 0.0 or r.ratio_rg != 0.0 or r.phase_draw != 0 or bool(r.dominant_dropped):
        return "ctrl/null defaults"
    if r.n_strata_scheduled != 0 or r.n_modes_injected != 0 or r.n_modes_rejected != 0:
        return "ctrl/null counts"
    if r.control_campaign_id != "" or not math.isnan(r.crowdsap) or not math.isnan(r.dropped_period_s):
        return "ctrl/null empties (absent floats must be NaN exactly)"
    if r.cadence_code != 0 or r.cadence_s != 0.0:
        return "ctrl/null cadence fields"
    if r.arm == "ctrl":
        if r.scenario != SCENARIO_CONTROL or r.amp_scale != 1.0 or r.null_serial != -1:
            return "control fields"
        if r.campaign_id != control_id(r.pool_index):
            return "control id"
    else:
        if r.scenario != SCENARIO_NULL or r.amp_scale != 0.0 or r.null_serial < 0:
            return "null fields"
        if r.campaign_id != null_id(r.null_serial):
            return "null id"
    return ""


def validate_manifest_frame(frame: pd.DataFrame) -> None:
    """Shared by the builder (before publishing) and the metrics reader
    (before consuming): schema, uniqueness, typed columns, and every row's
    semantic invariants. Raises SystemExit with the first offending row."""
    if list(frame.columns) != list(MANIFEST_COLUMN_NAMES):
        raise SystemExit("manifest columns deviate from MANIFEST_COLUMNS")
    if frame.empty:
        raise SystemExit("empty manifest")
    if frame["campaign_id"].duplicated().any():
        dup = frame.loc[frame["campaign_id"].duplicated(), "campaign_id"].head(3).tolist()
        raise SystemExit(f"duplicate campaign ids {dup}")
    for name, kind in MANIFEST_COLUMNS:
        if kind in ("int", "bool") and frame[name].isna().any():
            raise SystemExit(f"manifest column {name} has NaN")
    for r in frame.itertuples(index=False):
        problem = _row_problem(r)
        if problem:
            raise SystemExit(f"manifest row {r.campaign_id}: {problem}")
    nulls = frame[frame["arm"] == SCENARIO_NULL]
    if not nulls.empty and sorted(nulls["null_serial"].tolist()) != list(range(len(nulls))):
        raise SystemExit("null serials are not exactly 0..N-1")


def expected_counts(frame: pd.DataFrame, scheduled_tics: list[int],
                    dropout_eligible: list[int], redilution_tics: list[int],
                    n_nulls: int, arms: set[str],
                    cadence_alt_tics: list[int] | None = None) -> dict[str, int]:
    """The run-matrix counts a generation MUST realize, from the schedule
    alone (never from the outcome); asserted by builder and metrics."""
    n = len(scheduled_tics)
    counts: dict[str, int] = {}
    if "b" in arms:
        counts["B:nominal"] = 3 * n
    if "a" in arms:
        counts["A:nominal"] = 3 * n
    if "ladder" in arms:
        for gi in (1, 2, 3):
            for ri in (1, 2, 3):
                if (gi, ri) != (2, 2):
                    counts[f"B:ladder_g{gi}r{ri}"] = n
    if "phase" in arms:
        counts["B:phase_1"] = n
        counts["B:phase_2"] = n
    if "ampscale" in arms:
        counts["B:ampscale_0.7"] = n
        counts["B:ampscale_1.3"] = n
    if "dropout" in arms:
        counts["B:dropout"] = len(dropout_eligible)
    if "redilution" in arms:
        counts["B:redilution"] = len(redilution_tics)
    if "cadence_alt" in arms:
        counts["B:cadence_alt"] = len(cadence_alt_tics or [])
    if "ctrl" in arms:
        counts["ctrl:control"] = int(frame.loc[frame["arm"] == "B", "template_source_id"].nunique())
    if "nulls" in arms:
        counts["gauss_null:gauss_null"] = n_nulls
    return counts


def assert_counts(frame: pd.DataFrame, counts: dict[str, int]) -> None:
    realized = frame.groupby(["arm", "scenario"]).size()
    realized = {f"{a}:{sc}": int(v) for (a, sc), v in realized.items()}
    if realized != counts:
        missing = {k: v for k, v in counts.items() if realized.get(k) != v}
        extra = {k: v for k, v in realized.items() if k not in counts}
        raise SystemExit(f"run matrix mismatch: expected-but-different {missing}; unexpected {extra}")


def check_cadence_alt_schedule(mixed_from_v3: list[int], scheduled_alt: list[int],
                               production: bool) -> None:
    """Amendment 3 cardinality/identity (G3 round-3, both reviewers): in
    production the realized cadence_alt target set must equal the SPOC v3
    mixed-cadence set and count exactly MIXED_CADENCE_TARGETS_PRODUCTION;
    outside production it must still be a subset."""
    mixed, alt = set(int(t) for t in mixed_from_v3), set(int(t) for t in scheduled_alt)
    if len(alt) != len(list(scheduled_alt)):
        raise SystemExit("duplicate cadence_alt targets")
    if not alt <= mixed:
        raise SystemExit(f"cadence_alt scheduled for non-mixed targets {sorted(alt - mixed)[:3]}")
    if production:
        if len(mixed) != MIXED_CADENCE_TARGETS_PRODUCTION or len(list(mixed_from_v3)) != len(mixed):
            raise SystemExit(f"SPOC v3 lists {len(mixed)} unique mixed-cadence targets, "
                             f"expected {MIXED_CADENCE_TARGETS_PRODUCTION}")
        if alt != mixed:
            raise SystemExit(f"production requires every mixed-cadence target scheduled in "
                             f"cadence_alt: missing {sorted(mixed - alt)[:3]}")


def check_wg_strata(frame: pd.DataFrame, production: bool) -> list[str]:
    """Amendment 4: the three nominal windows of every target must carry
    strictly increasing W_g (K0 < K1 < K2). Production refuses violations;
    otherwise the violating targets are returned for the record."""
    nominal = frame[(frame["arm"].isin(["A", "B"])) & (frame["scenario"] == SCENARIO_NOMINAL)]
    violations = []
    for tic, g in nominal.drop_duplicates(["tic", "template_k"]).groupby("tic"):
        w = g.sort_values("template_k")["template_wg_contrasts"].tolist()
        if len(w) != 3 or not (w[0] < w[1] < w[2]):
            violations.append(f"TIC {tic}: W_g by K = {w}")
    if production and violations:
        raise SystemExit(f"W_g strata not strictly increasing for {len(violations)} targets: {violations[:3]}")
    return violations
