#!/usr/bin/env python3
"""v2 detector arm — shared constants, the frozen-code gate and the v2 digest.

scripts/v2/ sits OUTSIDE every frozen and campaign SHA surface
(frozen_api.FROZEN_SHA256 covers scripts/*.py of the published pipeline;
campaign_file_shas() globs scripts/generalization/*.py non-recursively). The v2
arm touches the frozen world in exactly two places: it reads the same shards
and it writes the same per-star JSON schema, so the unchanged metrics and
descriptive stack score it.

Frozen code is used READ-ONLY and only after frozen_api has verified every
frozen file's SHA-256: grids, the exact single-frequency power/amplitude fit,
the Baluev FAP, the spectral-window strength, peak extraction, the memmapped
fast periodogram and the best-pass semantics (overall_result). Nothing else
from scripts/generalization/*.py is imported.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path

V2_DIR = Path(__file__).resolve().parent
REPO_ROOT = V2_DIR.parents[1]
if str(REPO_ROOT / "scripts" / "generalization") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))

import frozen_api  # noqa: E402  — SHA gate; places scripts/ on sys.path
from frozen_api import (  # noqa: E402
    PASS_BOUNDS,
    SAMPLES_PER_PEAK,
    SIDEREAL_FREQUENCY,
    WINDOW_POWER_THRESHOLD,
    FrequencyGrid,
    campaign_file_shas,
    env_versions,
    frozen_file_shas,
    grid_for,
    json_ready,
    overall_result,
    unavailable_pass_result,
)
from lomb_scargle_common import (  # noqa: E402  — frozen, SHA-verified above
    approximate_peak_amplitude,
    baluev_fap,
    exact_power_and_amplitude,
    extract_peaks,
    periodogram_to_memmap,
    window_strength,
)
from run_lomb_scargle import multiband_power  # noqa: E402  — frozen power-sum

SCHEMA_VERSION = "v2-1"
ENGINE = "v2"
SOLAR_FREQUENCY = 1.0
LUNAR_SYNODIC_DAYS = 29.530589
YEAR_DAYS = 365.25
BANDS = ("zg", "zr")


@dataclass(frozen=True)
class V2Constants:
    """Every number the v2 rule depends on. The first four are the ONLY
    tunable constants (dev half only; candidate sets in TUNABLE); the rest are
    fixed by pre-registration (generalization/v2/V2_PLAN.md)."""

    # --- tunable on the dev half (declared candidate sets in TUNABLE) ---
    trend_window_days: float = 30.0       # high-pass running weighted-median window
    n_window_peaks: int = 12              # data-driven spectral-window peaks vetoed
    phase_tolerance_cycles: float = 0.15  # |phi_g - phi_r| coherence gate
    amp_ratio_min: float = 0.3            # A_r / A_g coherence gate (inclusive)
    amp_ratio_max: float = 1.5
    # --- fixed ---
    fap_threshold: float = 1e-3           # frozen per-band Baluev threshold
    tolerance_over_baseline: float = 1.5  # frozen 1.5 / T match & veto tolerance
    min_oid_rows: int = 5                 # oids with fewer rows are left unshifted
    min_shared_nights: int = 5            # shared-night alignment needs >= 5 nights in common
    min_trend_points: int = 5             # running median needs >= 5 points
    peaks_per_series: int = 15            # union of top-15 per band + top-15 joint
    joint_top: int = 5                    # "joint peak in top-5 joint (after veto)"
    max_candidates: int = 45              # = every clustered peak (3 series x 15): the
                                          # candidate set is ordered by power only, so it
                                          # does not depend on the tunable veto constants
    window_subsample: int = 10            # window strength on the pass grid / 10
    window_local_samples: int = 21        # frozen local window test (21 offsets)
    window_peak_pool: int = 24            # window peaks RECORDED (>= n_window_peaks)

    def tunable(self) -> dict[str, object]:
        return {
            "trend_window_days": self.trend_window_days,
            "n_window_peaks": self.n_window_peaks,
            "phase_tolerance_cycles": self.phase_tolerance_cycles,
            "amp_ratio": [self.amp_ratio_min, self.amp_ratio_max],
        }

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT = V2Constants()

# Pre-registered candidate sets (the first value is the default). The trend
# window needs a full dev rerun per value (2 values); the other three are
# re-scored offline EXACTLY from the recorded diagnostics (rescore_v2.py).
TUNABLE: dict[str, tuple] = {
    "trend_window_days": (30.0, 10.0),
    "n_window_peaks": (12, 6, 24),
    "phase_tolerance_cycles": (0.15, 0.10, 0.25),
    "amp_ratio": ((0.3, 1.5), (0.5, 1.2), (0.2, 2.0)),
}


def with_overrides(base: V2Constants = DEFAULT, **overrides) -> V2Constants:
    """Build a constants set from the declared candidate values only."""
    kwargs: dict[str, object] = {}
    for key, value in overrides.items():
        if key == "amp_ratio":
            if tuple(value) not in TUNABLE["amp_ratio"]:
                raise ValueError(f"amp_ratio {value} is not a declared candidate")
            kwargs["amp_ratio_min"], kwargs["amp_ratio_max"] = float(value[0]), float(value[1])
        elif key in TUNABLE:
            if value not in TUNABLE[key]:
                raise ValueError(f"{key}={value} is not a declared candidate")
            kwargs[key] = value
        else:
            raise ValueError(f"{key} is not a tunable constant")
    return replace(base, **kwargs)


def v2_file_shas() -> dict[str, str]:
    """SHA-256 of every scripts/v2/*.py file (the v2 code identity)."""
    return {
        f"scripts/v2/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(V2_DIR.glob("*.py"))
    }


def v2_digest() -> str:
    return hashlib.sha256(json.dumps(v2_file_shas(), sort_keys=True).encode()).hexdigest()


def frozen_digest() -> str:
    return hashlib.sha256(json.dumps(frozen_file_shas(), sort_keys=True).encode()).hexdigest()


def campaign_digest() -> str:
    return hashlib.sha256(json.dumps(campaign_file_shas(), sort_keys=True).encode()).hexdigest()


def env_digest() -> str:
    return hashlib.sha256(json.dumps(env_versions(), sort_keys=True).encode()).hexdigest()


__all__ = [
    "BANDS", "DEFAULT", "ENGINE", "LUNAR_SYNODIC_DAYS", "PASS_BOUNDS", "REPO_ROOT",
    "SAMPLES_PER_PEAK", "SCHEMA_VERSION", "SIDEREAL_FREQUENCY", "SOLAR_FREQUENCY",
    "TUNABLE", "V2Constants", "V2_DIR", "WINDOW_POWER_THRESHOLD", "YEAR_DAYS",
    "FrequencyGrid", "approximate_peak_amplitude", "baluev_fap", "campaign_digest",
    "campaign_file_shas", "env_digest", "env_versions", "exact_power_and_amplitude",
    "extract_peaks", "frozen_api", "frozen_digest", "frozen_file_shas", "grid_for",
    "json_ready", "multiband_power", "overall_result", "periodogram_to_memmap",
    "unavailable_pass_result", "v2_digest", "v2_file_shas", "window_strength",
    "with_overrides",
]
