#!/usr/bin/env python3
"""Post-launch DESCRIPTIVE dominant-only, confirmed-conditioned chance-match
calibration for D3 (ruling: generalization/reviews/G5prep/sol_round2.md,
item 8, F21, ADMIT-DESCRIPTIVE).

Writes descriptive_postlaunch/d3_dominant_confirmed_chance_match.csv.

Frame: the exact frozen P2 scorable/usable/S_best=1 positives with
best_status=="confirmed" and finite best and dominant frequencies.

Algorithm (as ruled):
- candidate frequencies and per-star tolerances (1.5/baseline_days) stay fixed;
- dominant frequencies are permuted at the star level;
- only derangements with no fixed points are accepted;
- exactly 10,000 accepted derangements are generated with PCG64(20260829);
- a hit requires the frozen classifier (classify_match, imported — never
  re-implemented) against the permuted single dominant frequency to return
  exactly `direct`; `ambiguous` is not a hit;
- the denominator is every confirmed-conditioned frame member in every
  derangement (each derangement's rate is hits / n_confirmed).

The q95 field is a quantile of the randomization distribution, not an
interval. This accompanies, without replacing, the prespecified
100-permutation any-mode audit (chance_match.json). FULL-run only.

This module lives in scripts/generalization/descriptive/ — deliberately
OUTSIDE the campaign_file_shas() surface (scripts/generalization/*.py,
non-recursive).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frozen_api import (  # noqa: E402,F401
    REPO_ROOT,
    assert_frozen,
    campaign_file_shas,
    frozen_file_shas,
)
from metrics_generalization import classify_match  # noqa: E402
import d3_descriptive_common as common  # noqa: E402
from d3_descriptive_common import (  # noqa: E402
    RULE,
    STATUS_COLUMNS,
    finite_series,
    sha256_file,
    tolerance_per_day,
)

DERANGEMENTS = 10000
SEED = 20260829
CONDITIONING = "p2_frame_confirmed_finite_best_and_dominant"
TRUTH_BASIS = "dominant_only_star_level_derangement"
OUTPUT_FILE = "d3_dominant_confirmed_chance_match.csv"
README_FILE = "d3_chance_dominant.README.md"
MANIFEST_FILE = "d3_chance_dominant.manifest.json"

COLUMNS = [
    "conditioning", "truth_basis", "derangements", "seed", "n_confirmed",
    "accidental_direct_rate_mean", "accidental_direct_rate_median",
    "accidental_direct_rate_q95", *STATUS_COLUMNS,
]

DISCLOSURE = (
    "Post-launch descriptive chance calibration conditions on the frozen P2 "
    "confirmed/scorable frame and uses 10,000 star-level derangements of the "
    "single dominant frequency; it accompanies, without replacing, the "
    "prespecified 100-permutation any-mode accidental-match audit and carries no "
    "inferential interval."
)


def confirmed_frame(per_star: pd.DataFrame,
                    expected_positives: int = common.EXPECTED_POSITIVES,
                    expected_scorable: int = common.EXPECTED_MO_JOINED) -> pd.DataFrame:
    """The ruled frame: P2 frame, best_status=="confirmed", finite best and
    dominant frequencies. Columns: sid, f, tol, dominant."""
    frame = common.p2_frame(per_star, expected_positives, expected_scorable)
    confirmed = frame[frame["best_status"] == RULE].copy()
    f = finite_series(confirmed["best_frequency_per_day"])
    dominant = finite_series(confirmed["primary_freq"])
    keep = f.notna() & dominant.notna()
    kept = confirmed.loc[keep]
    tol = kept["baseline_days"].map(tolerance_per_day)
    if tol.isna().any():
        raise SystemExit(
            "confirmed P2 stars without a finite tolerance (baseline_days): "
            f"{kept.loc[tol.isna(), 'sid'].tolist()[:10]}"
        )
    out = pd.DataFrame({
        "sid": kept["sid"].to_numpy(),
        "f": f[keep].to_numpy(dtype=float),
        "tol": tol.to_numpy(dtype=float),
        "dominant": dominant[keep].to_numpy(dtype=float),
    })
    out.attrs["n_confirmed_nonfinite_excluded"] = int((~keep).sum())
    return out


def direct_hit_matrix(f: np.ndarray, tol: np.ndarray, dominant: np.ndarray) -> np.ndarray:
    """M[i, j] = (frozen classify_match(f_i, [dominant_j], tol_i) == "direct").
    Every entry goes through the frozen classifier, so `ambiguous` (direct
    plus another relation) is never a hit."""
    n = len(f)
    if not (len(tol) == n and len(dominant) == n):
        raise SystemExit("frame arrays have mismatched lengths")
    matrix = np.zeros((n, n), dtype=bool)
    for i in range(n):
        for j in range(n):
            matrix[i, j] = classify_match(float(f[i]), [float(dominant[j])], float(tol[i])) == "direct"
    return matrix


def derangement_rates(matrix: np.ndarray, n_derangements: int = DERANGEMENTS,
                      seed: int = SEED) -> tuple[np.ndarray, int]:
    """Accidental direct-match rate of each accepted derangement (rejection
    sampling of uniform permutations; fixed points reject the draw)."""
    n = matrix.shape[0]
    if n < 2:
        raise SystemExit(f"{n} confirmed frame members: no derangement exists; refusing")
    rng = np.random.Generator(np.random.PCG64(seed))
    identity = np.arange(n)
    rates = np.empty(n_derangements, dtype=float)
    made = 0
    rejected = 0
    while made < n_derangements:
        perm = rng.permutation(n)
        if (perm == identity).any():
            rejected += 1
            continue
        rates[made] = matrix[identity, perm].sum() / n
        made += 1
    return rates, rejected


def summary_table(rates: np.ndarray, n_confirmed: int,
                  n_derangements: int = DERANGEMENTS, seed: int = SEED) -> pd.DataFrame:
    if len(rates) != n_derangements:
        raise SystemExit("rate vector length != the ruled derangement count")
    row = {
        "conditioning": CONDITIONING,
        "truth_basis": TRUTH_BASIS,
        "derangements": int(n_derangements),
        "seed": int(seed),
        "n_confirmed": int(n_confirmed),
        "accidental_direct_rate_mean": float(np.mean(rates)),
        "accidental_direct_rate_median": float(np.median(rates)),
        "accidental_direct_rate_q95": float(np.quantile(rates, 0.95)),
    }
    return common.with_status(pd.DataFrame([row]))[COLUMNS]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics-dir", type=Path, required=True,
                        help="completed FULL-run D3 metrics out-dir")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="<results>/descriptive_postlaunch")
    args = parser.parse_args(argv)

    assert_frozen()
    metrics_manifest, per_star = common.load_metrics_bundle(args.metrics_dir)
    frozen_chance = args.metrics_dir / "chance_match.json"
    if not frozen_chance.exists():
        raise SystemExit(
            "the frozen 100-permutation chance file (chance_match.json) is not "
            "written yet; this descriptive calibration runs only after it"
        )

    frame = confirmed_frame(per_star)
    matrix = direct_hit_matrix(frame["f"].to_numpy(), frame["tol"].to_numpy(),
                               frame["dominant"].to_numpy())
    rates, rejected = derangement_rates(matrix)
    table = summary_table(rates, len(frame))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / OUTPUT_FILE
    common.write_csv(table, out_csv, COLUMNS)
    (args.out_dir / README_FILE).write_text(
        "# D3 dominant-only confirmed-conditioned chance match (descriptive, post-launch)\n\n"
        + DISCLOSURE + "\n\n"
        f"Ruling: {common.VERDICT_FILE}, item 8 (F21, ADMIT-DESCRIPTIVE).\n"
        f"Fields on every row: analysis_status={common.ANALYSIS_STATUS}, "
        f"prespecified={str(common.PRESPECIFIED).lower()}, interval={common.INTERVAL}.\n\n"
        f"conditioning={CONDITIONING}: the exact frozen P2 scorable/usable/S_best=1 "
        "positives with best_status==confirmed and finite best and dominant "
        f"frequencies. truth_basis={TRUTH_BASIS}: candidate frequencies and per-star "
        "tolerances (1.5/baseline_days) fixed; the single dominant frequency permuted "
        "at the star level; only fixed-point-free derangements accepted; exactly "
        f"{DERANGEMENTS} accepted derangements from PCG64({SEED}); a hit is the frozen "
        "classifier returning exactly `direct` (`ambiguous` is not a hit); the "
        "denominator is every confirmed-conditioned frame member in every "
        "derangement. The q95 field is a quantile of the randomization distribution, "
        "not an interval.\n",
        encoding="utf-8",
    )
    manifest = {
        **common.provenance_block(Path(__file__)),
        "item": "sol_round2 item 8 (F21)",
        "algorithm": {"derangements": DERANGEMENTS, "seed": SEED, "bit_generator": "PCG64",
                      "acceptance": "no fixed points", "hit": "classify_match == direct",
                      "denominator": "n_confirmed per derangement", "quantile_method": "linear"},
        "inputs_sha256": {
            "per_star.csv": sha256_file(args.metrics_dir / "per_star.csv"),
            "metrics_manifest.json": sha256_file(args.metrics_dir / "manifest.json"),
            "chance_match.json": sha256_file(frozen_chance),
        },
        "outputs_sha256": {OUTPUT_FILE: sha256_file(out_csv)},
        "metrics_bundle": {"dataset": metrics_manifest.get("dataset"),
                           "pilot": bool(metrics_manifest.get("pilot", False))},
        "n_confirmed": int(len(frame)),
        "n_confirmed_nonfinite_excluded": int(frame.attrs.get("n_confirmed_nonfinite_excluded", 0)),
        "rejected_draws_with_fixed_points": int(rejected),
        "observed_direct_rate_unpermuted_context_only": (
            float(np.trace(matrix) / len(frame)) if len(frame) else math.nan),
    }
    common.write_json(args.out_dir / MANIFEST_FILE, manifest)
    print(table.to_string(index=False))
    print(f"[chance_dominant] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
