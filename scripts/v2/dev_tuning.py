#!/usr/bin/env python3
"""Dev-half tuning table and the pre-registered selection rule (V2_PLAN.md §5).

Inputs: the rescore table (`rescore_v2.py` on the D3 dev run and on the D2 dev
run), optional window-ladder runs (per-star CSVs from rescore on the subset
runs at 10 d / 3 d and the default run restricted to the same ids), the frozen
truth (metrics_generalization.truth_d3 / D2 shard manifest + injected modes)
and the split. For every constants combination it computes on the DEV ids:

  P1_dev  = confirmed fraction, D3 flag1 (eligible roster: missing = 0)
  P2_dev  = confirmed AND dominant direct, D3 Mo-joined freq-scorable usable
  P3_dev  = confirmed fraction, D3 flag0
  nulls   = confirmed count among the dev Gaussian nulls (500)
  J       = P2_dev - P3_dev

Selection: maximize J subject to nulls <= 2 and P1_dev >= P1_dev(default) - 0.05;
ties -> the default combination. Output: dev_tuning.csv (all combinations,
constraint flags, chosen), and the chosen constants as JSON overrides.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "v2"))
from metrics_generalization import classify_match, pass_eligible, truth_d3  # noqa: E402
from v2_common import DEFAULT, TUNABLE  # noqa: E402

DEFAULT_ID = f"N{DEFAULT.n_window_peaks}_phi{DEFAULT.phase_tolerance_cycles}_r{DEFAULT.amp_ratio_min}-{DEFAULT.amp_ratio_max}"
MAX_DEV_NULLS = 2
P1_SLACK = 0.05


def d3_scores(rescored: pd.DataFrame, truth: pd.DataFrame, dev_ids: set[str]) -> pd.DataFrame:
    """Per (combination, sid) outcome columns on the dev D3 ids: confirmed,
    recovered (confirmed & dominant direct), class, frames."""
    truth = truth[truth["sid"].isin(dev_ids)].set_index("sid")
    rows = []
    for combo, group in rescored.groupby("combination"):
        got = group.set_index("sid")
        for sid, t in truth.iterrows():
            present = sid in got.index
            status = str(got.loc[sid, "best_status"]) if present else "missing"
            freq = got.loc[sid, "best_frequency_per_day"] if present else None
            baseline = None
            confirmed = status == "confirmed"
            direct = False
            if confirmed and t.primary_freq is not None and freq is not None and not pd.isna(freq):
                # tolerance 1.5 / baseline: the rescore table has no baseline; use the
                # frozen per-star baseline when available, else the pass grid step x 15
                baseline = float(got.loc[sid, "baseline_days"]) if "baseline_days" in got.columns else math.nan
                tol = 1.5 / baseline if baseline and not math.isnan(baseline) else 1.5 / 2700.0
                direct = classify_match(float(freq), [float(t.primary_freq)], tol) == "direct"
            usable = present and bool(got.loc[sid, "low_available"]) and bool(got.loc[sid, "high_available"])
            eligible = bool(t.truth_freqs) and any(
                pass_eligible(list(t.truth_freqs), p, baseline if baseline else 2700.0) for p in ("low", "high"))
            rows.append({"combination": combo, "sid": sid, "class_label": t.class_label,
                         "confirmed": confirmed, "recovered": confirmed and direct,
                         "p2_frame": bool(t.freq_scorable) and usable and eligible})
    return pd.DataFrame(rows)


def summarize(d3: pd.DataFrame, nulls: pd.DataFrame | None) -> pd.DataFrame:
    out = []
    for combo, g in d3.groupby("combination"):
        pos = g[g["class_label"] == "dsct_flag1"]
        neg = g[g["class_label"] == "dsct_flag0"]
        p2 = pos[pos["p2_frame"]]
        row = {"combination": combo,
               "P1_dev": pos["confirmed"].mean(), "n_P1": len(pos),
               "P2_dev": p2["recovered"].mean() if len(p2) else math.nan, "n_P2": len(p2),
               "P3_dev": neg["confirmed"].mean(), "n_P3": len(neg)}
        if nulls is not None:
            n = nulls[nulls["combination"] == combo]
            row["dev_nulls_confirmed"] = int(n["best_status"].astype(str).eq("confirmed").sum())
            row["n_nulls"] = len(n)
        else:
            row["dev_nulls_confirmed"], row["n_nulls"] = math.nan, 0
        row["J"] = row["P2_dev"] - row["P3_dev"]
        out.append(row)
    table = pd.DataFrame(out)
    default_p1 = float(table.loc[table["combination"] == DEFAULT_ID, "P1_dev"].iloc[0])
    table["null_ok"] = table["dev_nulls_confirmed"].fillna(0) <= MAX_DEV_NULLS
    table["p1_ok"] = table["P1_dev"] >= default_p1 - P1_SLACK
    table["feasible"] = table["null_ok"] & table["p1_ok"]
    feasible = table[table["feasible"]]
    best_j = feasible["J"].max()
    winners = feasible[np.isclose(feasible["J"], best_j)]
    chosen = DEFAULT_ID if DEFAULT_ID in set(winners["combination"]) or winners.empty else str(winners.iloc[0]["combination"])
    table["chosen"] = table["combination"] == chosen
    return table.sort_values("J", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d3-rescore", type=Path, required=True, help="rescore_v2.py output on the D3 dev run")
    parser.add_argument("--d2-rescore", type=Path, default=None, help="rescore_v2.py output on the D2 dev run (nulls)")
    parser.add_argument("--split", type=Path, default=REPO_ROOT / "generalization/v2/split.csv")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    split = pd.read_csv(args.split, dtype=str)
    d3_dev = set(split[(split["dataset"] == "d3") & (split["split"] == "dev")]["sid"])
    rescored = pd.read_csv(args.d3_rescore, dtype={"sid": str})
    d3 = d3_scores(rescored, truth_d3(), d3_dev)
    nulls = None
    if args.d2_rescore is not None:
        d2 = pd.read_csv(args.d2_rescore, dtype={"sid": str})
        null_ids = set(split[(split["dataset"] == "d2") & (split["split"] == "dev") & (split["group"] == "gauss_null")]["sid"])
        nulls = d2[d2["sid"].isin(null_ids)]
    table = summarize(d3, nulls)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out_dir / "dev_tuning.csv", index=False, lineterminator="\n")
    chosen = str(table.loc[table["chosen"], "combination"].iloc[0])
    n, phi, ratio = chosen.split("_")
    overrides = {"n_window_peaks": int(n[1:]), "phase_tolerance_cycles": float(phi[3:]),
                 "amp_ratio": [float(x) for x in ratio[1:].split("-")]}
    (args.out_dir / "chosen_overrides.json").write_text(json.dumps(overrides, indent=2) + "\n", encoding="utf-8")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(table.to_string(index=False))
    print(f"[dev_tuning] chosen {chosen} -> {args.out_dir / 'chosen_overrides.json'}")


if __name__ == "__main__":
    main()
