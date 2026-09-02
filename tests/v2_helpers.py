"""Synthetic two-band ZTF-like shards for the v2 tests (deterministic)."""

from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = ["source_id", "band", "oid", "mjd", "bjd_tdb", "night_mjd", "mag", "magerr", "chi", "ra", "dec"]


def synthetic_star(
    source_id: str = "9000000000000000001",
    baseline_days: float = 200.0,
    frequency: float = 12.3,
    amp_g_mmag: float = 30.0,
    amp_r_mmag: float = 24.0,
    phase_r_cycles: float = 0.0,
    noise_mmag: float = 8.0,
    oid_offset_mmag: float = 15.0,
    seed: int = 20260902,
    nights: int = 120,
) -> pd.DataFrame:
    """Nightly cadence with 1-3 exposures per night, two oids per band: oid 1
    on every night, oid 2 (offset by `oid_offset_mmag`) on every other night
    so the two oids share many nights (the shared-night alignment needs
    >= 5 nights in common); a coherent sinusoid in both bands (phase in r
    shifted by `phase_r_cycles`), Gaussian noise; times in BJD_TDB days."""
    rng = np.random.default_rng(seed)
    rows = []
    night_starts = np.sort(rng.choice(int(baseline_days), size=nights, replace=False)).astype(float)
    for band, amp, phase_shift, base_mag in (("zg", amp_g_mmag, 0.0, 16.0), ("zr", amp_r_mmag, phase_r_cycles, 15.6)):
        for k, night in enumerate(night_starts):
            oids = ["1", "2"] if k % 2 == 0 else ["1"]
            for oid in oids:
                n_exp = int(rng.integers(1, 4))
                times = 58000.0 + night + 0.15 + rng.uniform(0.0, 0.12, size=n_exp)
                offset = 0.0 if oid == "1" else oid_offset_mmag / 1000.0
                for t in np.sort(times):
                    signal = (amp / 1000.0) * np.sin(2.0 * np.pi * frequency * t + 2.0 * np.pi * phase_shift)
                    mag = base_mag + offset + signal + rng.normal(0.0, noise_mmag / 1000.0)
                    rows.append({
                        "source_id": source_id, "band": band, "oid": f"{band}{oid}",
                        "mjd": t, "bjd_tdb": t + 2400000.5 + 0.0031, "night_mjd": float(np.floor(t)),
                        "mag": mag, "magerr": noise_mmag / 1000.0, "chi": 1.0, "ra": 290.0, "dec": 40.0,
                    })
    return pd.DataFrame(rows, columns=COLUMNS)


def write_shard(frame: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        frame.to_csv(handle, index=False, lineterminator="\n")
    return path
