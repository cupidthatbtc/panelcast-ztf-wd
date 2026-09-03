#!/usr/bin/env python3
"""D2 frozen-arm poster figures F5-F7 (AAS 249; generalization/writing/outline/OUTLINE.md §2.3).

Reads ONLY a committed D2 results bundle `generalization/results/<date>_d2/`
(metrics/ in the layout metrics_generalization.py writes). No frozen or
campaign code is imported; no statistic is computed here except (a) the
target-level per-stratum (K0/K1/K2) point estimates for the F5 side panel,
which the bundle does not tabulate — drawn as descriptive counts WITHOUT an
interval — and (b) nothing else: every interval is read verbatim from the
bundle. Every number drawn is written to `figures.manifest.json` beside its
source file and locator (G5).

PILOT GUARD: a bundle whose metrics/manifest.json carries pilot=true is
refused — pilot numbers are never figures (OUTLINE Part D). The only way past
the guard is --allow-pilot-for-schema-test, which watermarks every panel
"PILOT — SCHEMA TEST ONLY, NOT A RESULT" and exists for exercising the code
against the archived gen2 pilot's real file schema.

Palette: identical to d3_poster_figures.py (dataviz skill default, light
mode, validated; the same categorical slots in the same fixed order so rule
identity is coloured identically across the poster). This module lives
outside the campaign SHA surface (scripts/generalization/*.py is globbed
non-recursively by campaign_file_shas).

Usage: python d2_poster_figures.py --bundle <results/<date>_d2> --out-dir <dir>
       [--allow-pilot-for-schema-test]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize

# ---------------------------------------------------------------- palette (dataviz skill default, light mode)
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"
CAT = {"confirmed": "#2a78d6", "confirmed_or_candidate": "#eb6834", "census": "#1baf7a", "either": "#eda100"}
PRIMARY_BLUE = CAT["confirmed"]          # slot 1: the rule-1 / arm-B identity, as in F1-F4
CONTROL_ORANGE = CAT["confirmed_or_candidate"]   # slot 2: paired uninjected control
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#0d366b"]
WATERMARK_RED = "#c62828"

WG_EDGES = (15, 41, 84, 217)                       # d2_truth_model.WG_SURFACE_EDGES (frozen)
WG_LABELS = ("<15", "15-41", "41-84", "84-217", ">=217")
AMP_EDGES_PPT = (0.5, 2.0, 5.0, 10.0, 30.0)         # metrics AMP_EDGES["d2"] (frozen)
AMP_LABELS = ("<0.5", "0.5-2", "2-5", "5-10", "10-30", ">=30")
SCENARIO_ORDER = ("ladder_g1r1", "ladder_g1r2", "ladder_g1r3", "ladder_g2r1", "ladder_g2r3",
                  "ladder_g3r1", "ladder_g3r2", "ladder_g3r3", "phase_1", "phase_2",
                  "ampscale_0.7", "ampscale_1.3", "dropout", "cadence_alt", "redilution")
P5_ACCEPTANCE = 0.005
WATERMARK = "PILOT — SCHEMA TEST ONLY, NOT A RESULT"

BUNDLE_FILES = [
    "metrics/manifest.json",
    "metrics/surfaces/recovery_wg_amplitude.csv",
    "metrics/d2_cluster_completeness.csv",
    "metrics/d2_scenario_contrasts.csv",
    "metrics/trigger_rates.csv",
    "metrics/d2_paired_controls_summary.csv",
    "metrics/d2_control_reuse.csv",
    "metrics/per_star.csv",
]


class PilotBundleError(SystemExit):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def style(axis) -> None:
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        axis.spines[spine].set_color(AXIS)
    axis.tick_params(labelsize=8, colors=INK_SECONDARY)
    axis.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
    axis.set_axisbelow(True)


def watermark(fig, enabled: bool) -> None:
    if enabled:
        fig.text(0.5, 0.5, WATERMARK, color=WATERMARK_RED, alpha=0.32, fontsize=22, fontweight="bold",
                 ha="center", va="center", rotation=18, zorder=100)


def load_bundle(bundle: Path, allow_pilot: bool) -> tuple[dict, dict, bool]:
    manifest = json.loads((bundle / "metrics/manifest.json").read_text(encoding="utf-8"))
    pilot = bool(manifest.get("pilot", False))
    if manifest.get("dataset") != "d2":
        raise SystemExit(f"{bundle}: metrics manifest dataset is {manifest.get('dataset')!r}, not d2")
    if pilot and not allow_pilot:
        raise PilotBundleError(
            f"{bundle}: metrics/manifest.json has pilot=true — pilot numbers are never figures "
            "(OUTLINE Part D). Use --allow-pilot-for-schema-test only to exercise the code; every "
            "panel is then watermarked."
        )
    data = {
        "manifest": manifest,
        "surface": pd.read_csv(bundle / "metrics/surfaces/recovery_wg_amplitude.csv"),
        "cluster": pd.read_csv(bundle / "metrics/d2_cluster_completeness.csv"),
        "contrasts": pd.read_csv(bundle / "metrics/d2_scenario_contrasts.csv"),
        "trigger_rates": pd.read_csv(bundle / "metrics/trigger_rates.csv"),
        "paired": pd.read_csv(bundle / "metrics/d2_paired_controls_summary.csv"),
        "reuse": pd.read_csv(bundle / "metrics/d2_control_reuse.csv", dtype={"control_campaign_id": str,
                                                                              "template_source_id": str}),
        "per_star": pd.read_csv(bundle / "metrics/per_star.csv", dtype={"sid": str, "cluster": str}),
    }
    shas = {rel: sha256_file(bundle / rel) for rel in BUNDLE_FILES}
    return data, shas, pilot


def _f(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


# ---------------------------------------------------------------------------------- F5 recovery surface
def stratum_marginals(per_star: pd.DataFrame) -> dict:
    """Target-level recovery per W_g stratum K0/K1/K2 on nominal arm B: for
    every target the stratum's window outcome (0/1), averaged over targets
    (one window per target per stratum by construction). DESCRIPTIVE counts,
    no interval — the bundle does not tabulate per-stratum rates."""
    b = per_star[(per_star["arm"] == "B") & (per_star["scenario"] == "nominal")]
    out = {}
    recovered = (b["best_status"].astype(str) == "confirmed") & \
        (b["best_candidate_matches_dominant"].astype(str) == "direct")
    for k in (0, 1, 2):
        rows = b[pd.to_numeric(b["template_k"]) == k]
        per_target = recovered[rows.index].astype(float).groupby(rows["cluster"]).mean()
        out[f"K{k}"] = {"n_targets": int(len(per_target)), "k_targets_equivalent": float(per_target.sum()),
                        "p": float(per_target.mean()) if len(per_target) else math.nan}
    return out


def fig_f5_surface(data: dict, out_dir: Path, pilot: bool) -> dict:
    surface = data["surface"]
    cluster = data["cluster"]
    numbers: dict = {"cells": {}, "p4": {}, "strata": {}}
    has_interval = "p" in surface.columns

    fig, (left, right) = plt.subplots(1, 2, figsize=(10.4, 4.2), gridspec_kw={"width_ratios": [2.1, 1]})
    grid = np.full((len(WG_LABELS), len(AMP_LABELS)), np.nan)
    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
    for _, row in surface.iterrows():
        wg, amp = int(row["wg_bin"]), int(row["amp_bin"])
        if not (0 <= wg < len(WG_LABELS)) or not (0 <= amp < len(AMP_LABELS)):
            continue    # amp_bin -1 (no published amplitude) is not on the surface
        cell = {"n_windows": int(row["n_windows"]), "k_windows": int(row["k_windows"]),
                "n_targets": int(row["n_targets"])}
        if has_interval and pd.notna(row.get("p", np.nan)) and cell["n_targets"] >= 5:
            cell.update({"p": _f(row["p"]), "lo": _f(row["lo"]), "hi": _f(row["hi"]),
                         "interval": str(row.get("interval", ""))})
            grid[wg, amp] = cell["p"]
        numbers["cells"][f"wg{wg}_amp{amp}"] = cell
    left.imshow(np.ma.masked_invalid(grid), cmap=cmap, norm=Normalize(0, 1), origin="lower", aspect="auto")
    left.set_facecolor("#f3f2ee")
    for wg in range(len(WG_LABELS)):
        for amp in range(len(AMP_LABELS)):
            cell = numbers["cells"].get(f"wg{wg}_amp{amp}")
            if cell is None:
                continue
            if "p" in cell:
                text = f"{cell['p']:.2f}\n[{cell['lo']:.2f}, {cell['hi']:.2f}]\n{cell['n_targets']} targets"
                color = "#ffffff" if cell["p"] > 0.55 else INK
            else:
                text = f"{cell['k_windows']}/{cell['n_windows']} win.\n{cell['n_targets']} targets"
                color = INK_SECONDARY
            left.text(amp, wg, text, ha="center", va="center", fontsize=6.4, color=color, zorder=5)
    left.set_xticks(range(len(AMP_LABELS))); left.set_xticklabels(AMP_LABELS, fontsize=7.5)
    left.set_yticks(range(len(WG_LABELS))); left.set_yticklabels(WG_LABELS, fontsize=7.5)
    left.set_xlabel("published TESS dominant amplitude (ppt), frozen edges", fontsize=8)
    left.set_ylabel("W_g stratum (zg exposures beyond one per night), frozen edges", fontsize=8)
    left.set_title("(a) target-level recovery on (W_g, amplitude), nominal arm B\n"
                   "fill + interval only where >= 5 targets (target-cluster bootstrap); counts otherwise",
                   fontsize=8.3, color=INK)
    left.tick_params(length=0, colors=INK_SECONDARY)

    # side panel: P4 eligible & usable (bundle rows) + K0/K1/K2 marginals (descriptive)
    nominal = cluster[(cluster["arm"] == "B") & (cluster["scenario"] == "nominal") & (cluster["endpoint"] == "recovery")]
    xs, labels = [], []
    for i, denom in enumerate(("eligible", "usable")):
        row = nominal[nominal["denominator"] == denom]
        if row.empty:
            continue
        row = row.iloc[0]
        p, lo, hi = _f(row["p"]), _f(row["lo"]), _f(row["hi"])
        right.bar(i, p, width=0.6, color=PRIMARY_BLUE, edgecolor=INK, linewidth=2.2 if denom == "eligible" else 0, zorder=3)
        right.errorbar([i], [p], yerr=[[max(0.0, p - lo)], [max(0.0, hi - p)]], fmt="none",
                       ecolor=INK_SECONDARY, capsize=3, zorder=4)
        right.annotate(f"{p:.2f}\n{int(row['n_targets'])} targets", (i, hi + 0.02), ha="center", va="bottom",
                       fontsize=7, color=INK_SECONDARY)
        xs.append(i); labels.append(f"P4 {denom}")
        numbers["p4"][denom] = {"p": p, "lo": lo, "hi": hi, "n_targets": int(row["n_targets"]),
                                "n_targets_zero_usable_strata": int(row["n_targets_zero_usable_strata"]),
                                "interval": str(row["interval"])}
    strata = stratum_marginals(data["per_star"])
    numbers["strata"] = strata
    for j, k in enumerate(("K0", "K1", "K2")):
        x = 2.4 + j * 0.7
        s = strata[k]
        if not math.isnan(s["p"]):
            right.plot([x], [s["p"]], marker="o", markersize=7, color=MUTED, markeredgecolor=INK_SECONDARY,
                       linestyle="none", zorder=4)
            right.annotate(f"{s['p']:.2f}\n({s['n_targets']})", (x, s["p"] + 0.03), ha="center", va="bottom",
                           fontsize=6.5, color=MUTED)
        xs.append(x); labels.append(k)
    right.axvline(2.0, color=GRID, linewidth=1.0, linestyle=":")
    right.set_xticks(xs); right.set_xticklabels(labels, fontsize=7.5)
    right.set_ylim(0, 1.12)
    right.set_ylabel("nominal arm-B dominant-mode recovery", fontsize=8)
    right.set_title("(b) P4 (cluster 95%) and K0/K1/K2\ntarget means (descriptive, no interval)",
                    fontsize=8.3, color=INK)
    style(right)
    fig.suptitle("F5 — D2 recovery surface (PRIMARY-P4 side panel; surface DESCRIPTIVE-PRESPEC)",
                 fontsize=10, color=INK)
    watermark(fig, pilot)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_dir / "f5_recovery_surface.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f5_recovery_surface.pdf", facecolor=SURFACE)
    plt.close(fig)
    return numbers


# ---------------------------------------------------------------------------------- F6 sensitivity
def fig_f6_sensitivity(data: dict, out_dir: Path, pilot: bool) -> dict:
    contrasts = data["contrasts"]
    rows = contrasts[(contrasts["endpoint"] == "recovery") & (contrasts["denominator"] == "eligible")]
    present = [s for s in SCENARIO_ORDER if s in set(rows["scenario"])]
    extra = sorted(set(rows["scenario"]) - set(present))
    order = present + extra
    numbers: dict = {}

    fig, axis = plt.subplots(figsize=(7.2, 5.2))
    for i, scenario in enumerate(order):
        row = rows[rows["scenario"] == scenario].iloc[0]
        diff, lo, hi = _f(row["diff"]), _f(row["diff_lo"]), _f(row["diff_hi"])
        degenerate = str(row["interval"]) == "cp_discordance_bound"
        y = len(order) - 1 - i
        axis.errorbar([diff], [y], xerr=[[max(0.0, diff - lo)], [max(0.0, hi - diff)]],
                      fmt="o" if not degenerate else "D", color=PRIMARY_BLUE if not degenerate else SURFACE,
                      markeredgecolor=PRIMARY_BLUE, markeredgewidth=1.4, markersize=6.5,
                      ecolor=INK_SECONDARY if not degenerate else MUTED,
                      elinewidth=1.6 if not degenerate else 1.0, capsize=3, zorder=4,
                      linestyle="none")
        if degenerate:
            axis.annotate("CP discordance bound", (hi, y), xytext=(4, 0), textcoords="offset points",
                          ha="left", va="center", fontsize=6.2, color=MUTED)
        axis.annotate(f"n={int(row['n_targets_matched'])}", (-1.02, y), ha="left", va="center", fontsize=6.5,
                      color=INK_SECONDARY)
        numbers[scenario] = {"diff": diff, "diff_lo": lo, "diff_hi": hi,
                             "discordance_u95": _f(row.get("discordance_u95", np.nan)),
                             "interval": str(row["interval"]), "n_targets_matched": int(row["n_targets_matched"]),
                             "p_scenario": _f(row["p_scenario"]), "p_nominal_k1": _f(row["p_nominal_k1"])}
    axis.axvline(0.0, color=INK, linewidth=0.9, zorder=2)
    axis.set_yticks(range(len(order)))
    axis.set_yticklabels(list(reversed(order)), fontsize=7.5)
    axis.set_xlim(-1.05, 1.05)
    axis.set_xlabel("recovery(scenario) − recovery(nominal, K1 window), eligible denominator\n"
                    "(paired common-draw target bootstrap 95%; open diamonds = zero discordances: CP bound)",
                    fontsize=8)
    axis.xaxis.grid(True, color=GRID, linewidth=0.7)
    axis.yaxis.grid(False)
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    axis.tick_params(labelsize=8, colors=INK_SECONDARY)
    finite = {s: v for s, v in numbers.items() if not math.isnan(v["diff"])}
    if finite:
        lo_s = min(finite, key=lambda s: finite[s]["diff"])
        hi_s = max(finite, key=lambda s: finite[s]["diff"])
        axis.set_title("F6 — D2 sensitivity (DESCRIPTIVE-PRESPEC)\n"
                       f"min {lo_s} ({finite[lo_s]['diff']:+.2f}), max {hi_s} ({finite[hi_s]['diff']:+.2f}); "
                       "no band, no interval on the range", fontsize=8.6, color=INK)
        numbers["_range"] = {"min_scenario": lo_s, "min_diff": finite[lo_s]["diff"],
                             "max_scenario": hi_s, "max_diff": finite[hi_s]["diff"]}
    handles = [plt.Line2D([], [], marker="o", color=PRIMARY_BLUE, linestyle="none", label="common-draw bootstrap"),
               plt.Line2D([], [], marker="D", markerfacecolor=SURFACE, markeredgecolor=PRIMARY_BLUE,
                          color=MUTED, linestyle="none", label="CP discordance bound (degenerate)")]
    axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=7,
                frameon=False)
    watermark(fig, pilot)
    fig.tight_layout()
    fig.savefig(out_dir / "f6_sensitivity.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f6_sensitivity.pdf", facecolor=SURFACE)
    plt.close(fig)
    return numbers


# ---------------------------------------------------------------------------------- F7 nulls & controls
def _two_by_two(axis, row: pd.Series, title: str) -> dict:
    cells = np.array([[int(row["both"]), int(row["b_only"])],
                      [int(row["c_only"]), int(row["neither"])]], dtype=float)
    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
    axis.imshow(cells, cmap=cmap, norm=Normalize(0, max(1.0, cells.max())))
    for i in range(2):
        for j in range(2):
            v = int(cells[i, j])
            axis.text(j, i, str(v), ha="center", va="center", fontsize=13, fontweight="bold",
                      color="#ffffff" if cells[i, j] / max(1.0, cells.max()) > 0.55 else INK)
    axis.set_xticks([0, 1]); axis.set_xticklabels(["control yes", "control no"], fontsize=7)
    axis.set_yticks([0, 1]); axis.set_yticklabels(["injected yes", "injected no"], fontsize=7)
    axis.tick_params(length=0)
    p, lo, hi = _f(row["p_b_and_not_c"]), _f(row["p_b_and_not_c_lo"]), _f(row["p_b_and_not_c_hi"])
    axis.set_title(f"{title}\nunion {int(row['union'])}/{int(row['n_pairs_scored'])} pairs, "
                   f"{int(row['n_targets'])} targets\nP(B=1, C=0) = {p:.2f} [{lo:.2f}, {hi:.2f}]",
                   fontsize=7.6, color=INK)
    return {"both": int(row["both"]), "b_only": int(row["b_only"]), "c_only": int(row["c_only"]),
            "neither": int(row["neither"]), "union": int(row["union"]), "n_pairs_scored": int(row["n_pairs_scored"]),
            "n_targets": int(row["n_targets"]), "n_unique_windows": int(row["n_unique_windows"]),
            "p_b": _f(row["p_b"]), "p_b_lo": _f(row["p_b_lo"]), "p_b_hi": _f(row["p_b_hi"]),
            "p_c": _f(row["p_c"]), "p_c_lo": _f(row["p_c_lo"]), "p_c_hi": _f(row["p_c_hi"]),
            "paired_diff_b_minus_c": _f(row["paired_diff_b_minus_c"]),
            "paired_diff_b_minus_c_lo": _f(row["paired_diff_b_minus_c_lo"]),
            "paired_diff_b_minus_c_hi": _f(row["paired_diff_b_minus_c_hi"]),
            "p_b_and_not_c": p, "p_b_and_not_c_lo": lo, "p_b_and_not_c_hi": hi}


def fig_f7_nulls_controls(data: dict, out_dir: Path, pilot: bool) -> dict:
    trig = data["trigger_rates"]
    paired = data["paired"]
    reuse = data["reuse"]
    numbers: dict = {}
    fig, axes = plt.subplots(1, 4, figsize=(12.6, 3.9), gridspec_kw={"width_ratios": [1.0, 1.0, 1.0, 1.25]})

    # (a) FPR_Gaussian with the exact one-sided CP upper and the 0.5 % acceptance line
    fpr = trig[trig["quantity"] == "fpr_gaussian"].iloc[0]
    x, n = int(_f(fpr["k"])), int(_f(fpr["n_completed"]))
    upper = _f(fpr["cp_one_sided_95_upper"])
    p = _f(fpr["p"])
    a = axes[0]
    a.bar([0], [p], width=0.5, color=PRIMARY_BLUE, zorder=3)
    a.errorbar([0], [p], yerr=[[0.0], [max(0.0, upper - p)]], fmt="none", ecolor=INK_SECONDARY, capsize=6,
               linewidth=1.6, zorder=4)
    a.axhline(P5_ACCEPTANCE, color=CAT["either"], linewidth=1.4, linestyle="--", zorder=2)
    a.set_xlim(-0.6, 0.6)
    a.annotate("0.5 % acceptance line", (-0.55, P5_ACCEPTANCE), xytext=(0, 3), textcoords="offset points",
               fontsize=6.6, color=INK_SECONDARY, ha="left", va="bottom")
    a.annotate(f"{x}/{n}\nU95 = {upper:.4f}", (0, upper), xytext=(0, 6), textcoords="offset points",
               ha="center", va="bottom", fontsize=7, color=INK)
    a.set_xticks([0]); a.set_xticklabels(["Gaussian nulls"], fontsize=7.5)
    a.set_ylim(0, max(0.02, upper * 1.6))
    a.set_ylabel("rule-1 false-alarm rate (exact one-sided CP upper)", fontsize=7.5)
    title = "(a) FPR_Gaussian (PRIMARY-P5)"
    if n != 1000:
        title += f"\nn_completed = {n} ≠ 1000: not the P5 decision"
    a.set_title(title, fontsize=8, color=INK)
    style(a)
    numbers["fpr_gaussian"] = {"k": x, "n_completed": n, "n_scheduled": int(_f(fpr["n_scheduled"])), "p": p,
                               "cp_one_sided_95_upper": upper,
                               "acceptance_u95_leq_0.005": bool(fpr["acceptance_u95_leq_0.005"]),
                               "n_completed_is_1000": bool(fpr["n_completed_is_1000"])}

    # (b) paired controls: 2x2 for D and for R (SECONDARY)
    for axis, endpoint, label in ((axes[1], "D", "(b) detection D, injected vs paired control"),
                                  (axes[2], "R", "(b) strict recovery R, injected vs paired control")):
        row = paired[paired["endpoint"] == endpoint]
        if row.empty:
            axis.axis("off"); continue
        numbers[f"paired_{endpoint}"] = _two_by_two(axis, row.iloc[0], label)

    # (c) native trigger rate of the control windows + reuse counts
    native = trig[trig["quantity"] == "native_trigger_rate"]
    c = axes[3]
    counts = reuse["n_b_assignments"].astype(int).value_counts().sort_index()
    c.bar(counts.index, counts.values, width=0.8, color=CONTROL_ORANGE, zorder=3)
    for k, v in counts.items():
        c.annotate(str(int(v)), (k, v), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom",
                   fontsize=6.5, color=INK_SECONDARY)
    c.set_xlabel("arm-B shards per control window (reuse count)", fontsize=7.5)
    c.set_ylabel("control windows", fontsize=7.5)
    if not native.empty:
        nr = native.iloc[0]
        c.set_title(f"(c) native trigger {_f(nr['p']):.2f} [{_f(nr['lo']):.2f}, {_f(nr['hi']):.2f}], "
                    f"n={int(_f(nr['n']))} windows\nreuse counts over {int(reuse['n_b_assignments'].sum())} "
                    "arm-B assignments", fontsize=7.6, color=INK)
        numbers["native_trigger_rate"] = {"p": _f(nr["p"]), "lo": _f(nr["lo"]), "hi": _f(nr["hi"]),
                                          "n": int(_f(nr["n"])), "ess": _f(nr["ess"])}
    numbers["reuse"] = {"n_control_windows": int(len(reuse)), "n_b_assignments_total": int(reuse["n_b_assignments"].sum()),
                        "reuse_histogram": {int(k): int(v) for k, v in counts.items()}}
    style(c)
    fig.suptitle("F7 — D2 nulls & controls (PRIMARY-P5; SECONDARY paired D/R; DESCRIPTIVE-PRESPEC native)",
                 fontsize=10, color=INK)
    watermark(fig, pilot)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out_dir / "f7_nulls_controls.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f7_nulls_controls.pdf", facecolor=SURFACE)
    plt.close(fig)
    return numbers


# ---------------------------------------------------------------------------------- captions + manifest
CAPTIONS = {
    "F5": ("D2 recovery surface. (a) Target-level dominant-mode recovery (rule 1, best pass, direct match "
           "to the largest-amplitude retained injected mode) on nominal arm-B windows, on the frozen "
           "(W_g stratum, published TESS amplitude) grid with edges W_g {15,41,84,217} and A {0.5,2,5,10,30,∞} "
           "ppt; a cell is filled and carries its target-cluster bootstrap 95% interval only where ≥ 5 "
           "targets, otherwise the raw window counts and target count are printed. Published amplitudes, "
           "never ladder-scaled; no window-level Wilson; no scenario pooling. (b) P4 in its eligible and "
           "usable variants with the cluster interval, and the K0/K1/K2 target means as descriptive counts "
           "without an interval. [PRIMARY-P4 (side panel); DESCRIPTIVE-PRESPEC (surface, strata)]"),
    "F6": ("D2 sensitivity. Paired scenario-minus-nominal-K1 recovery differences (eligible denominator) with "
           "common-draw target-bootstrap 95% intervals for the ladder points, phase draws, amplitude scales, "
           "dominant-mode dropout, cadence_alt and redilution; rows with zero observed discordances are drawn "
           "as the exact Clopper–Pearson discordance bound and marked. The min and max are named; no band and "
           "no interval on the range. [DESCRIPTIVE-PRESPEC]"),
    "F7": ("D2 nulls and controls. (a) FPR_Gaussian: rule-1 confirmations among the Gaussian nulls with the "
           "exact one-sided 95% Clopper–Pearson upper bound and the 0.5% acceptance line (the sole "
           "confirmatory decision; only at n = 1,000 completed trials). (b) Paired uninjected controls: 2×2 "
           "injected-vs-control for detection D and for strict recovery R with union and P(B=1, C=0) with its "
           "cluster interval. (c) Native trigger rate of the control windows with their reuse counts. Not a "
           "real-sky FPR; the native rate is never subtracted from P4. [PRIMARY-P5; SECONDARY (paired D/R); "
           "DESCRIPTIVE-PRESPEC (native, reuse)]"),
}


def write_captions(out_dir: Path, pilot: bool) -> None:
    lines = ["# D2 poster figure captions (F5-F7)\n"]
    if pilot:
        lines.append(f"> {WATERMARK}: rendered from a PILOT bundle to exercise the schema; nothing here is a result.\n")
    for key in ("F5", "F6", "F7"):
        lines.append(f"## {key}\n\n{CAPTIONS[key]}\n")
    (out_dir / "captions.md").write_text("\n".join(lines), encoding="utf-8")


def render(bundle: Path, out_dir: Path, allow_pilot: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    data, shas, pilot = load_bundle(bundle, allow_pilot)
    numbers = {
        "F5": fig_f5_surface(data, out_dir, pilot),
        "F6": fig_f6_sensitivity(data, out_dir, pilot),
        "F7": fig_f7_nulls_controls(data, out_dir, pilot),
    }
    write_captions(out_dir, pilot)
    manifest = {
        "bundle": str(bundle),
        "pilot": pilot,
        "watermark": WATERMARK if pilot else "",
        "inputs_sha256": shas,
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "frozen_edges": {"wg": list(WG_EDGES), "amp_ppt": list(AMP_EDGES_PPT)},
        "figures": {
            "F5": {"png": "f5_recovery_surface.png", "pdf": "f5_recovery_surface.pdf", "numbers": numbers["F5"]},
            "F6": {"png": "f6_sensitivity.png", "pdf": "f6_sensitivity.pdf", "numbers": numbers["F6"]},
            "F7": {"png": "f7_nulls_controls.png", "pdf": "f7_nulls_controls.pdf", "numbers": numbers["F7"]},
        },
        "captions": CAPTIONS,
    }
    (out_dir / "figures.manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n",
                                                   encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="generalization/results/<date>_d2")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--allow-pilot-for-schema-test", action="store_true",
                        help="render a PILOT bundle with every panel watermarked (schema exercise only)")
    args = parser.parse_args()
    render(args.bundle, args.out_dir, args.allow_pilot_for_schema_test)
    print(f"[d2_poster_figures] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
