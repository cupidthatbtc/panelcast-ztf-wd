#!/usr/bin/env python3
"""Single import surface for the frozen 2026-08-01 pipeline.

The generalization campaign (branch generalization/campaign-1) never edits the
scripts that produced the published 2026-08-01_full bundle. Campaign code
imports frozen callables ONLY through this module, which verifies the SHA-256
of every frozen file against the values recorded at tag `frozen-2026-08-01`
before any import happens. `assert_frozen()` is also called explicitly at the
top of every campaign script.

Referee defense: `git diff frozen-2026-08-01 -- <frozen files>` is empty, and
scripts/generalization/replay_gate.py reproduces published per-star results
under these imports.
"""

from __future__ import annotations

import hashlib
import os
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(
    os.environ.get("GENERALIZATION_REPO_ROOT", Path(__file__).resolve().parents[2])
)
SCRIPTS_DIR = REPO_ROOT / "scripts"

FROZEN_TAG = "frozen-2026-08-01"

# SHA-256 of every frozen file at tag frozen-2026-08-01 (== branch point of
# generalization/campaign-1). Recorded 2026-08-28; never update these values —
# a mismatch means the frozen pipeline was edited and all campaign results are void.
FROZEN_SHA256 = {
    "scripts/run_catalog_lomb_scargle.py": "34a4de5d234cab07dc3231e5671f4220f5c4ab1bdd4b3d92183bb7e443da6c46",
    "scripts/run_lomb_scargle.py": "ce9211254949969b5d2e7a93f350eb387014aaf0a15f939753c599c1261a4e78",
    "scripts/lomb_scargle_common.py": "5ed3983e6a9b91f86b4ba2afc37025ba97fee4ef8a0086259140618927bfef7d",
    "scripts/build_catalog_panels.py": "1fb659cfdf6997751bc7589b70bdd26fa0d210f49e0e9da5da82bcbb1a5d9794",
    "scripts/fetch_catalog_lightcurves.py": "e28f4ade76fedf78e056b26b62549a4c5dfc1e0c76d5d127876cce7b3cb3ed82",
}

# Campaign source_id convention: 19-digit numeric strings, dataset-prefixed.
# All prefixes chosen so ids cannot collide with real Gaia DR3 source_ids used
# in the 2026-08-01 run and so int(source_id[-9:]) (the frozen bootstrap's seed
# convention) is always a valid int.
CAMPAIGN_ID_PREFIXES = {
    "90": "D3 ZTF x Kepler delta Scuti (real ZTF light curves)",
    "92": "D2 arm B (TESS-truth signal + real ZTF photometry)",
    "93": "D2 arm A (TESS-truth signal + synthetic Gaussian floor)",
    "94": "D2 Gaussian nulls (zero amplitude, arm-A floor)",
    "95": "D2 paired real-window controls (uninjected template windows)",
    "96": "D2 self-window templates (real ZTF at Romero positions; diagnostic)",
}


class FrozenIntegrityError(RuntimeError):
    """A frozen file's content no longer matches tag frozen-2026-08-01."""


def frozen_file_shas() -> dict[str, str]:
    shas: dict[str, str] = {}
    for rel in FROZEN_SHA256:
        path = REPO_ROOT / rel
        shas[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "MISSING"
    return shas


def assert_frozen() -> dict[str, str]:
    actual = frozen_file_shas()
    mismatches = [
        f"{rel}: expected {expected[:12]}..., found {actual[rel][:12]}..."
        for rel, expected in FROZEN_SHA256.items()
        if actual[rel] != expected
    ]
    if mismatches:
        raise FrozenIntegrityError(
            "frozen pipeline files modified since tag "
            f"{FROZEN_TAG}:\n" + "\n".join(mismatches)
        )
    return actual


def env_versions() -> dict[str, str]:
    import astropy
    import astropy_iers_data
    import erfa
    import numpy
    import pandas
    import scipy

    blas = ""
    try:
        config = numpy.__config__.CONFIG["Build Dependencies"]["blas"]
        blas = f"{config.get('name', '')} {config.get('version', '')}".strip()
    except Exception:
        pass
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.node(),
        "numpy": numpy.__version__,
        "numpy_blas": blas,
        "scipy": scipy.__version__,
        "astropy": astropy.__version__,
        "astropy_iers_data": astropy_iers_data.__version__,
        "pyerfa": erfa.__version__,
        "pandas": pandas.__version__,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", ""),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS", ""),
    }


def campaign_file_shas() -> dict[str, str]:
    """SHA-256 of every campaign script + spec, recorded in every manifest so
    adapter-shell drift is visible (G1 methods finding 9)."""
    shas: dict[str, str] = {}
    for path in sorted((REPO_ROOT / "scripts/generalization").glob("*.py")):
        shas[f"scripts/generalization/{path.name}"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    for rel in ("generalization/GENERALIZATION_PLAN.md", "generalization/METRICS_SPEC.md"):
        path = REPO_ROOT / rel
        if path.exists():
            shas[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return shas


def campaign_id_ok(source_id: str) -> bool:
    return (
        isinstance(source_id, str)
        and len(source_id) == 19
        and source_id.isdigit()
        and source_id[:2] in CAMPAIGN_ID_PREFIXES
    )


assert_frozen()
_FROZEN_MODULES = (
    "run_catalog_lomb_scargle",
    "run_lomb_scargle",
    "lomb_scargle_common",
    "build_catalog_panels",
)
for _name in _FROZEN_MODULES:
    if _name in sys.modules:
        raise FrozenIntegrityError(
            f"{_name} was imported before frozen_api verified it"
        )
sys.path.insert(0, str(SCRIPTS_DIR))

from build_catalog_panels import (  # noqa: E402
    BANDS,
    EXPOSURE_COLUMNS,
    MIN_EXPOSURES_PER_BAND,
    MONTHLY_COLUMNS,
    NIGHTLY_COLUMNS,
    OID_CLUSTER_ARCSEC,
    PALOMAR,
    add_bjd,
    angular_separation_arcsec,
    census_row,
    clean_rows,
    monthly_panel,
    nightly_panel,
    read_cache,
    scatter_over_error,
    select_nearest_source,
)
from lomb_scargle_common import (  # noqa: E402
    FrequencyGrid,
    SAMPLES_PER_PEAK,
    SIDEREAL_FREQUENCY,
    WINDOW_POWER_THRESHOLD,
    prepare_series,
)
from run_catalog_lomb_scargle import (  # noqa: E402
    analyze_star,
    load_star,
    overall_result,
    physical_workers,
    unavailable_pass_result,
)
from run_lomb_scargle import (  # noqa: E402
    PASS_BOUNDS,
    grid_for,
    json_ready,
)

for _name in _FROZEN_MODULES:
    _file = Path(sys.modules[_name].__file__).resolve()
    if _file != (SCRIPTS_DIR / f"{_name}.py").resolve():
        raise FrozenIntegrityError(
            f"{_name} resolved to {_file}, not the SHA-verified copy"
        )

__all__ = [
    "REPO_ROOT",
    "SCRIPTS_DIR",
    "FROZEN_TAG",
    "FROZEN_SHA256",
    "CAMPAIGN_ID_PREFIXES",
    "FrozenIntegrityError",
    "frozen_file_shas",
    "assert_frozen",
    "env_versions",
    "campaign_file_shas",
    "campaign_id_ok",
    "BANDS",
    "EXPOSURE_COLUMNS",
    "MIN_EXPOSURES_PER_BAND",
    "MONTHLY_COLUMNS",
    "NIGHTLY_COLUMNS",
    "OID_CLUSTER_ARCSEC",
    "PALOMAR",
    "add_bjd",
    "angular_separation_arcsec",
    "census_row",
    "clean_rows",
    "monthly_panel",
    "nightly_panel",
    "read_cache",
    "scatter_over_error",
    "select_nearest_source",
    "FrequencyGrid",
    "SAMPLES_PER_PEAK",
    "SIDEREAL_FREQUENCY",
    "WINDOW_POWER_THRESHOLD",
    "prepare_series",
    "analyze_star",
    "load_star",
    "overall_result",
    "physical_workers",
    "unavailable_pass_result",
    "PASS_BOUNDS",
    "grid_for",
    "json_ready",
]
