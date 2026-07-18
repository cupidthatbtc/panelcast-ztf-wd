"""Readable per-star light-curve panels from a panelcast run.

panelcast's stock per-entity fan charts hardcode the AOTY 0-100 score axis
(panelcast issue #254), which flattens magnitude-scale data into an unreadable
strip. This re-plots each star from the saved run artifacts instead: the full
monthly light curve, the held-out test month with its predictive interval, and
the next-month forecast quantiles. Magnitude axis is inverted per convention.

Usage:
    python scripts/plot_star_panels.py outputs/<run_dir> [--panel data/raw/ztf_wd_zg_monthly.csv]

Writes PNGs to <run_dir>/reports/figures_readable/.
"""

import argparse
import json
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BLUE = "#0173b2"
ORANGE = "#de8f05"
GREEN = "#029e73"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--panel", type=Path, default=Path("data/raw/ztf_wd_zg_monthly.csv"))
    args = ap.parse_args()

    panel = pd.read_csv(args.panel, parse_dates=["month_date"])
    evals = json.loads((args.run_dir / "evaluation" / "predictions.json").read_text())
    eval_df = pd.DataFrame(
        {k: evals[k] for k in ("entity", "event", "y_true", "y_pred_mean", "y_pred_lower", "y_pred_upper")}
    )
    interval = evals.get("interval_level", 0.95)
    fc = pd.read_csv(args.run_dir / "predictions" / "next_event_known_entities.csv")
    fc = fc[fc["scenario"] == "same"].set_index("entity")

    out_dir = args.run_dir / "reports" / "figures_readable"
    out_dir.mkdir(parents=True, exist_ok=True)

    for sid, lc in panel.groupby("source_id"):
        lc = lc.sort_values("month_date")
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.errorbar(
            lc["month_date"], lc["mag_binned"], yerr=lc["mag_err"],
            fmt="o-", ms=3, lw=0.8, color=BLUE, ecolor=BLUE, elinewidth=0.6,
            capsize=0, alpha=0.85, label="monthly binned g",
        )

        row = eval_df[eval_df["entity"] == sid]
        if not row.empty:
            r = row.iloc[0]
            test_date = pd.to_datetime(str(r["event"]) + "-01")
            ax.errorbar(
                [test_date], [r["y_pred_mean"]],
                yerr=[[r["y_pred_mean"] - r["y_pred_lower"]], [r["y_pred_upper"] - r["y_pred_mean"]]],
                fmt="s", ms=6, color=ORANGE, elinewidth=1.6, capsize=4,
                label=f"held-out prediction ({interval:.0%} CI)",
            )
            ax.plot([test_date], [r["y_true"]], "*", ms=12, color="black", zorder=5, label="held-out actual")

        if sid in fc.index:
            f = fc.loc[sid]
            fdate = lc["month_date"].max() + timedelta(days=30)
            ax.errorbar(
                [fdate], [f["pred_q50"]],
                yerr=[[f["pred_q50"] - f["pred_q05"]], [f["pred_q95"] - f["pred_q50"]]],
                fmt="D", ms=5, color=GREEN, elinewidth=1.2, capsize=4,
                label="next-month forecast (q05-q95)",
            )

        wd_class = lc["wd_class"].iloc[0]
        ax.set_title(f"{sid}  ({wd_class}, {len(lc)} months)", fontsize=11)
        ax.set_ylabel("g (mag)")
        ax.invert_yaxis()
        ax.legend(fontsize=8, loc="best")
        ax.grid(alpha=0.25, lw=0.5)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(out_dir / f"star_{sid}.png", dpi=150)
        plt.close(fig)

    print(f"wrote {len(panel['source_id'].unique())} panels to {out_dir}")


if __name__ == "__main__":
    main()
