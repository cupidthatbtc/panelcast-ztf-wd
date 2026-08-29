#!/usr/bin/env python3
"""Campaign figures — drawn ONLY from metrics_generalization.py CSV outputs.

No statistic is computed here beyond what the metrics files carry; every
figure states its estimand name (METRICS_SPEC vocabulary) in the title.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from frozen_api import assert_frozen

INK = "#2b2a26"
ACCENT = "#8c2d19"
MUTED = "#c3c2b7"
RULE_ORDER = ["confirmed", "confirmed_or_candidate", "census", "either"]


def style(axis) -> None:
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    axis.tick_params(labelsize=8)


def plot_completeness(metrics_dir: Path, out_dir: Path, dataset: str) -> None:
    frame = pd.read_csv(metrics_dir / "completeness_by_class_pass_rule.csv")
    frame = frame[frame["pass"] == "best"]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True)
    scopes = ["detection_eligible_roster", "detection_usable_lightcurve",
              "freq_recovery_scorable"]
    for axis, scope in zip(axes, scopes):
        subset = frame[frame["scope"] == scope].set_index("rule").reindex(RULE_ORDER)
        x = range(len(subset))
        axis.errorbar(
            x, subset["p"],
            yerr=[subset["p"] - subset["lo"], subset["hi"] - subset["p"]],
            fmt="o", color=INK, ecolor=ACCENT, capsize=3, markersize=5,
        )
        for i, (_, row) in enumerate(subset.iterrows()):
            if row["n"] > 0:
                axis.annotate(f"n={int(row['n'])}", (i, 0.02), ha="center", fontsize=7,
                              color=INK)
        axis.set_xticks(list(x))
        labels = {"confirmed": "confirmed", "confirmed_or_candidate": "conf. |\ncand.",
                  "census": "census", "either": "either"}
        axis.set_xticklabels([labels.get(r, r) for r in subset.index], fontsize=7)
        axis.set_title(scope.replace("_", " "), fontsize=9)
        axis.set_ylim(0, 1.05)
        axis.axhline(1.0, color=MUTED, linewidth=0.8, linestyle=":")
        style(axis)
    axes[0].set_ylabel("completeness (best pass, Wilson 95%)", fontsize=8)
    fig.suptitle(f"{dataset.upper()} detection / frequency-recovery completeness",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(out_dir / "completeness_rules.png", dpi=200)
    plt.close(fig)


def plot_turn_on(metrics_dir: Path, out_dir: Path, dataset: str) -> None:
    path = metrics_dir / "surfaces" / "period_amplitude.csv"
    surface = pd.read_csv(path)
    if surface.empty or "p" not in surface.columns:
        return
    marginal = (
        surface.groupby("amp_bin")
        .agg(n=("n", "sum"), k=("k", "sum"))
        .reset_index()
    )
    fig, axis = plt.subplots(figsize=(5.0, 3.4))
    from math import sqrt
    z = 1.959963984540054
    for _, row in marginal.iterrows():
        n, k = row["n"], row["k"]
        if n >= 5:
            p = k / n
            denom = 1 + z * z / n
            center = (p + z * z / (2 * n)) / denom
            half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
            axis.errorbar(row["amp_bin"], p, yerr=[[max(0, p - (center - half))],
                                                   [max(0, (center + half) - p)]],
                          fmt="o", color=INK, ecolor=ACCENT, capsize=3)
            axis.annotate(f"{int(k)}/{int(n)}", (row["amp_bin"], p + 0.04),
                          ha="center", fontsize=7, color=INK)
        else:
            axis.annotate(f"{int(k)}/{int(n)}", (row["amp_bin"], 0.02),
                          ha="center", fontsize=7, color=ACCENT)
    axis.set_xlabel("amplitude bin index (frozen edges; see METRICS_SPEC)", fontsize=8)
    unit = "historical Kepler-band mmag" if dataset == "d3" else (
        "published TESS ppt" if dataset == "d2" else "mmag")
    axis.set_ylabel("rule-1 frequency-recovery completeness", fontsize=8)
    axis.set_title(f"{dataset.upper()} turn-on ({unit}); cells<5 shown as counts",
                   fontsize=9)
    axis.set_ylim(0, 1.1)
    style(axis)
    fig.tight_layout()
    fig.savefig(out_dir / "turn_on_amplitude.png", dpi=200)
    plt.close(fig)


def plot_contingency(metrics_dir: Path, out_dir: Path, dataset: str) -> None:
    data = json.loads((metrics_dir / "contingency_complementarity.json").read_text())
    table = data["table"]
    fig, axis = plt.subplots(figsize=(3.6, 3.2))
    cells = [[table["census_and_ls"], table["census_only"]],
             [table["ls_only"], table["neither"]]]
    axis.imshow(cells, cmap="Greys", vmin=0, vmax=max(2, max(max(r) for r in cells)))
    for i in range(2):
        for j in range(2):
            axis.text(j, i, str(cells[i][j]), ha="center", va="center",
                      fontsize=14, color=ACCENT)
    axis.set_xticks([0, 1]); axis.set_xticklabels(["L-S conf.", "no L-S"], fontsize=8)
    axis.set_yticks([0, 1]); axis.set_yticklabels(["census", "no census"], fontsize=8)
    union = data.get("union_completeness", {})
    axis.set_title(
        f"{dataset.upper()} positives, detection-only 2x2\n"
        f"union {union.get('p', float('nan')):.2f} "
        f"[{union.get('lo', 0):.2f}, {union.get('hi', 0):.2f}]",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(out_dir / "contingency.png", dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-dir", type=Path, required=True)
    parser.add_argument("--dataset", choices=("d1", "d2", "d3"), required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    assert_frozen()
    out_dir = args.out_dir or (args.metrics_dir / "figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_completeness(args.metrics_dir, out_dir, args.dataset)
    plot_turn_on(args.metrics_dir, out_dir, args.dataset)
    plot_contingency(args.metrics_dir, out_dir, args.dataset)
    print(f"[plots] wrote {out_dir}")


if __name__ == "__main__":
    main()
