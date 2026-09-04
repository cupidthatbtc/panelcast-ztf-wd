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
SIDEREAL_MONTH_DAYS = 27.321661   # Amendment 2026-09-04 (V2_PLAN.md §10): moon-vs-field cycle
YEAR_DAYS = 365.25
# V2_PLAN.md §10, 2026-09-04: the dev runs were produced at the round-6 admitted digest and are
# re-scored (never rerun) under the amended veto; every downstream artifact binds both.
DEV_RUNS_V2_DIGEST = "ecc5df75d8f225cbd364d3c498894ab6dce6bf1aeead89ad1de285d4ee57d33c"
VETO_AMENDMENT_COMMIT = "017c925e161bb83a69a71ee2547dbd67accfdbcb"
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


FROZEN_API_PATH = REPO_ROOT / "scripts" / "generalization" / "frozen_api.py"


def v2_file_shas() -> dict[str, str]:
    """SHA-256 of every scripts/v2/*.py file PLUS scripts/generalization/
    frozen_api.py — the complete v2 runtime code identity: v2 imports the
    frozen helpers through frozen_api, which is in neither the frozen nor
    the v2-only surface (V2G1 round 5)."""
    shas = {
        f"scripts/v2/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(V2_DIR.glob("*.py"))
    }
    shas["scripts/generalization/frozen_api.py"] = hashlib.sha256(FROZEN_API_PATH.read_bytes()).hexdigest()
    return shas


def v2_digest() -> str:
    return hashlib.sha256(json.dumps(v2_file_shas(), sort_keys=True).encode()).hexdigest()


def frozen_digest() -> str:
    return hashlib.sha256(json.dumps(frozen_file_shas(), sort_keys=True).encode()).hexdigest()


def campaign_digest() -> str:
    return hashlib.sha256(json.dumps(campaign_file_shas(), sort_keys=True).encode()).hexdigest()


def env_digest() -> str:
    return hashlib.sha256(json.dumps(env_versions(), sort_keys=True).encode()).hexdigest()


# ---- V2_PLAN.md §5 / §10: the four dev runs and their fail-closed binding records -------------
# (dataset, trend window) -> registered dev list; verified by dev_tuning (from the manifests),
# by the registered holdout runner and by the comparison (from the bound artifact / lock).
DEV_RUN_SCHEDULE = {("d3-kepler-dsct", 30.0): "d3_dev.txt", ("d3-kepler-dsct", 10.0): "d3_dev.txt",
                    ("d2-tess-dav", 30.0): "d2_dev.txt", ("d2-tess-dav", 10.0): "d2_dev.txt"}
DEV_RUN_RECORD_KEYS = ("manifest", "sha256", "dataset", "trend_window_days", "v2_digest",
                       "stars_file_sha256", "completed")


def registered_list(registration: Path, name: str) -> tuple[str, int]:
    """(SHA-256, number of ids) of a registered id list."""
    path = Path(registration) / name
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest(), len([line for line in text.splitlines() if line.strip()])


def run_completion(manifest: dict) -> tuple[int, int]:
    """(completed, total) of a run_v2_ls.py manifest — its own schema:
    source_count, pending_at_start, completed_now (resume-aware). A manifest
    without them is refused, never treated as complete."""
    try:
        total = int(manifest["source_count"])
        done = total - int(manifest["pending_at_start"]) + int(manifest["completed_now"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit("run manifest lacks the completion fields "
                         f"(source_count, pending_at_start, completed_now): {exc!r}")
    return done, total


def dev_run_record(manifest_path: Path, registration: Path) -> dict:
    """Verify ONE dev-run manifest fail-closed and return its binding record:
    engine v2, the admitted pre-amendment digest, the dev half, no failures,
    no --limit, a (dataset, trend window) of the §5 schedule, the registered
    dev list (top-level AND binding SHA) and completion equal to its length."""
    manifest_path = Path(manifest_path)
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    binding = m.get("binding") or {}
    problems: list[str] = []
    if m.get("engine") != "v2":
        problems.append("engine is not v2")
    if binding.get("v2_digest") != DEV_RUNS_V2_DIGEST:
        problems.append(f"v2_digest {str(binding.get('v2_digest'))[:12]} is not the dev-run digest "
                        f"{DEV_RUNS_V2_DIGEST[:12]}")
    if (m.get("split") or {}).get("half") != "dev":
        problems.append("split half is not dev")
    if m.get("failures"):
        problems.append("the run has failures")
    if m.get("limit") is not None:
        problems.append("a --limit run")
    try:
        window = float((m.get("constants") or {}).get("trend_window_days"))
    except (TypeError, ValueError):
        window = float("nan")
    key = (m.get("dataset"), window)
    completed = -1
    if key not in DEV_RUN_SCHEDULE:
        problems.append(f"(dataset, window) {key} is not in the §5 schedule")
    else:
        list_sha, n_list = registered_list(registration, DEV_RUN_SCHEDULE[key])
        if m.get("stars_file_sha256") != list_sha or binding.get("stars_file_sha256") != list_sha:
            problems.append(f"stars_file_sha256 is not the registered {DEV_RUN_SCHEDULE[key]}")
        done, total = run_completion(m)
        if total != n_list or done != n_list:
            problems.append(f"completion {done}/{total} != registered list {n_list}")
        completed = n_list
    if problems:
        raise SystemExit(f"{manifest_path}: dev-run manifest rejected: {problems}")
    return {"manifest": str(manifest_path), "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "dataset": key[0], "trend_window_days": key[1], "v2_digest": binding["v2_digest"],
            "stars_file_sha256": binding["stars_file_sha256"], "completed": completed}


def validate_dev_run_records(records, registration: Path) -> list[dict]:
    """The bound `dev_runs` of a constants artifact or lock: exactly four
    well-formed records mapping one-to-one onto the §5 schedule, each at the
    dev-run digest, with the registered list SHA and its full completion."""
    import re

    if not isinstance(records, list) or len(records) != 4:
        raise SystemExit("dev_runs must be a list of exactly 4 records")
    seen: set[tuple] = set()
    for record in records:
        if not isinstance(record, dict) or set(DEV_RUN_RECORD_KEYS) - set(record):
            raise SystemExit(f"dev_runs record must carry {DEV_RUN_RECORD_KEYS}")
        try:
            key = (record["dataset"], float(record["trend_window_days"]))
        except (TypeError, ValueError):
            raise SystemExit("dev_runs record has a non-numeric trend window")
        if key not in DEV_RUN_SCHEDULE or key in seen:
            raise SystemExit(f"dev_runs record {key} is not a unique §5 schedule entry")
        seen.add(key)
        if not re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"])):
            raise SystemExit("dev_runs record sha256 is not a SHA-256")
        if record["v2_digest"] != DEV_RUNS_V2_DIGEST:
            raise SystemExit("dev_runs record digest is not the dev-run digest")
        list_sha, n_list = registered_list(registration, DEV_RUN_SCHEDULE[key])
        if record["stars_file_sha256"] != list_sha or int(record["completed"]) != n_list:
            raise SystemExit(f"dev_runs record {key}: registered list / completion mismatch")
    if seen != set(DEV_RUN_SCHEDULE):
        raise SystemExit("dev_runs do not cover the §5 schedule one-to-one")
    return records


__all__ = [
    "DEV_RUN_RECORD_KEYS", "DEV_RUN_SCHEDULE", "dev_run_record", "registered_list", "run_completion",
    "validate_dev_run_records",
    "BANDS", "DEFAULT", "DEV_RUNS_V2_DIGEST", "ENGINE", "LUNAR_SYNODIC_DAYS", "PASS_BOUNDS", "REPO_ROOT",
    "VETO_AMENDMENT_COMMIT",
    "SAMPLES_PER_PEAK", "SCHEMA_VERSION", "SIDEREAL_FREQUENCY", "SIDEREAL_MONTH_DAYS", "SOLAR_FREQUENCY",
    "TUNABLE", "V2Constants", "V2_DIR", "WINDOW_POWER_THRESHOLD", "YEAR_DAYS",
    "FrequencyGrid", "approximate_peak_amplitude", "baluev_fap", "campaign_digest",
    "campaign_file_shas", "env_digest", "env_versions", "exact_power_and_amplitude",
    "extract_peaks", "frozen_api", "frozen_digest", "frozen_file_shas", "grid_for",
    "json_ready", "multiband_power", "overall_result", "periodogram_to_memmap",
    "unavailable_pass_result", "v2_digest", "v2_file_shas", "window_strength",
    "with_overrides",
]
