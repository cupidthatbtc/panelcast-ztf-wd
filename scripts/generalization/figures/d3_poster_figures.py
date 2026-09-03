#!/usr/bin/env python3
"""D3 frozen-arm poster figures F1-F4 (AAS 249; generalization/writing/outline/OUTLINE.md §2.3).

Reads ONLY the committed bundle `generalization/results/2026-09-02_d3/` — no
frozen or campaign code is imported, no statistic is computed here beyond a
Wilson interval on an already-tabulated (k, n) cell, applied exactly where the
outline's Feed column says "marginalize". Every number drawn is written to
`figures.manifest.json` beside its source file and locator so every annotation
is traceable (G5). This module lives outside the campaign SHA surface
(scripts/generalization/*.py is globbed non-recursively by campaign_file_shas)
and is never imported by, and never imports, the live campaign runners.

Palette: the dataviz skill's validated default (references/palette.md),
light mode (poster is printed on white). Categorical slots are assigned to
the frozen rule vocabulary in FIXED order (RULE_ORDER) and reused identically
across every figure that shows rule identity (F2, F3a), per the "color follows
the entity" rule. Wilson bars are pointwise only where n >= 5, else the raw
count is annotated instead (F1); no smoothing, no fit, no interpolation.

Usage: python d3_poster_figures.py --bundle <results/2026-09-02_d3> --out-dir <dir>
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
RULE_ORDER = ("confirmed", "confirmed_or_candidate", "census", "either")
RULE_LABEL = {"confirmed": "confirmed", "confirmed_or_candidate": "conf. |\ncandidate",
              "census": "census", "either": "either"}
RULE_COLOR = dict(zip(RULE_ORDER, ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")))  # categorical slots 1-4
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#0d366b"]  # sequential ramp, light->dark
Z95 = 1.959963984540054

D3_AMP_EDGES_MMAG = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0)
D3_AMP_LABELS = ("<0.5", "0.5-1", "1-2", "2-5", "5-10", "10-20", "20-50", ">=50")

BUNDLE_FILES = [
    "metrics/surfaces/detection_amplitude.csv",
    "metrics/surfaces/freq_recovery_period_amplitude.csv",
    "metrics/completeness_by_class_pass_rule.csv",
    "metrics/trigger_rates.csv",
    "metrics/fp_frequency_distribution.csv",
    "metrics/contingency_complementarity.json",
    "descriptive_postlaunch/d3_trigger_decomposition.csv",
    "descriptive_postlaunch/README.md",
]

DISCLOSURE_SENTENCE = (
    "Post-launch, pilot-informed descriptive analysis: after inspection of raw, "
    "unweighted per-pass statuses from the non-representative 150-star D3 timing "
    "pilot, and after the full D3 L-S run had launched but before any "
    "full-campaign metric was computed, we fixed the solar-diurnal frequency "
    "bands at union_{k=1..3} [k-0.020, k+0.020] / d; d3_trigger_decomposition.csv "
    "is an unweighted arithmetic partition of the frozen rule-1, best-pass D3 "
    "negative-class P3 numerator over its unchanged 2,314-star denominator, was "
    "not prespecified, carries no interval or confirmatory interpretation, is "
    "not used to veto, exclude, or reclassify any trigger, and does not "
    "establish that an individual band member is instrumental rather than "
    "astrophysical."
)


def style(axis) -> None:
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        axis.spines[spine].set_color(AXIS)
    axis.tick_params(labelsize=8, colors=INK_SECONDARY)
    axis.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
    axis.set_axisbelow(True)


def wilson(k: float, n: float) -> tuple[float, float, float]:
    """Wilson score interval, z = 1.959963984540054 (the frozen formula's
    constant; a standard closed form, re-derived here only for the ONE
    marginalized cut the outline calls for — every other interval in these
    figures is read verbatim from the committed bundle)."""
    if n <= 0:
        return math.nan, math.nan, math.nan
    p = k / n
    denom = 1.0 + Z95 * Z95 / n
    center = (p + Z95 * Z95 / (2 * n)) / denom
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_bundle(bundle: Path) -> dict:
    data = {
        "detection_amplitude": pd.read_csv(bundle / "metrics/surfaces/detection_amplitude.csv"),
        "freq_recovery_period_amplitude": pd.read_csv(
            bundle / "metrics/surfaces/freq_recovery_period_amplitude.csv"),
        "completeness": pd.read_csv(bundle / "metrics/completeness_by_class_pass_rule.csv"),
        "trigger_rates": pd.read_csv(bundle / "metrics/trigger_rates.csv"),
        "fp_frequency_distribution": pd.read_csv(bundle / "metrics/fp_frequency_distribution.csv",
                                                  dtype={"sid": str}),
        "contingency": json.loads((bundle / "metrics/contingency_complementarity.json").read_text()),
        "trigger_decomposition": pd.read_csv(
            bundle / "descriptive_postlaunch/d3_trigger_decomposition.csv"),
    }
    shas = {rel: sha256_file(bundle / rel) for rel in BUNDLE_FILES}
    return data, shas


def annotate_bar(axis, x: float, y: float, text: str, *, color: str = INK, fontsize: float = 7,
                 dy: float = 0.02) -> None:
    axis.annotate(text, (x, y + dy), ha="center", va="bottom", fontsize=fontsize, color=color)


def yerr_pair(p: float, lo: float, hi: float) -> list[list[float]]:
    """[[lower, upper]] with sub-ulp Wilson-boundary rounding clipped to 0."""
    return [[max(0.0, p - lo)], [max(0.0, hi - p)]]


# ---------------------------------------------------------------------------------- F1 turn-on
def fig_f1_turn_on(data: dict, out_dir: Path) -> dict:
    detection = data["detection_amplitude"].set_index("amp_bin")
    recovery_raw = data["freq_recovery_period_amplitude"]
    recovery = recovery_raw.groupby("amp_bin").agg(n=("n", "sum"), k=("k", "sum")).reset_index()

    fig, (left, right) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    numbers: dict = {"detection": {}, "recovery": {}}

    # panel 1: detection completeness, "unknown" (amp_bin -1) + the 8 frozen bins
    xticks, xlabels = [], []
    for i, amp_bin in enumerate([-1, *range(8)]):
        if amp_bin not in detection.index:
            continue
        row = detection.loc[amp_bin]
        n, k, p, lo, hi = int(row["n"]), int(row["k"]), row["p"], row["lo"], row["hi"]
        label = "unknown" if amp_bin == -1 else D3_AMP_LABELS[amp_bin]
        color = MUTED if amp_bin == -1 else RULE_COLOR["confirmed"]
        marker = "X" if amp_bin == -1 else "o"
        if n >= 5:
            left.errorbar([i], [p], yerr=yerr_pair(p, lo, hi), fmt=marker, color=color,
                          ecolor=INK_SECONDARY, capsize=3, markersize=7 if amp_bin == -1 else 6,
                          markeredgecolor=INK_SECONDARY if amp_bin == -1 else "none",
                          markeredgewidth=0.8, zorder=3)
            annotate_bar(left, i, hi, f"{k}/{n}", color=INK_SECONDARY)
        else:
            annotate_bar(left, i, 0.02, f"{k}/{n}", color=MUTED)
        xticks.append(i)
        xlabels.append(label)
        numbers["detection"][label] = {"n": n, "k": k, "p": p, "lo": lo, "hi": hi}
    left.axvline(0.5, color=GRID, linewidth=1.0, linestyle=":")
    left.set_xticks(xticks)
    left.set_xticklabels(xlabels, fontsize=7, rotation=0)
    left.set_ylim(0, 1.08)
    left.set_ylabel("rule-1 detection completeness\n(Wilson 95%, best pass)", fontsize=8)
    left.set_xlabel("historical Kepler-band dominant amplitude (mmag)", fontsize=8)
    left.set_title("D3 turn-on: detection", fontsize=9, color=INK)
    style(left)

    # panel 2: frequency recovery, marginalized over period_bin (no unknown bin: all
    # freq-scorable stars have a Mo-joined amplitude)
    for i in range(8):
        cell = recovery[recovery["amp_bin"] == i]
        if cell.empty:
            continue
        n, k = int(cell["n"].iloc[0]), int(cell["k"].iloc[0])
        p, lo, hi = wilson(k, n)
        label = D3_AMP_LABELS[i]
        if n >= 5:
            right.errorbar([i], [p], yerr=yerr_pair(p, lo, hi), fmt="o", color=RULE_COLOR["confirmed"],
                           ecolor=INK_SECONDARY, capsize=3, markersize=6, zorder=3)
            annotate_bar(right, i, hi, f"{k}/{n}", color=INK_SECONDARY)
        else:
            annotate_bar(right, i, 0.02, f"{k}/{n}", color=MUTED)
        numbers["recovery"][label] = {"n": n, "k": k, "p": p, "lo": lo, "hi": hi}
    right.set_xticks(range(8))
    right.set_xticklabels(D3_AMP_LABELS, fontsize=7)
    right.set_ylim(0, 1.08)
    right.set_ylabel("rule-1 frequency-recovery completeness\n(dominant direct; marginalized, Wilson 95%)",
                     fontsize=8)
    right.set_xlabel("historical Kepler-band dominant amplitude (mmag)", fontsize=8)
    right.set_title("D3 turn-on: frequency recovery", fontsize=9, color=INK)
    style(right)

    fig.suptitle("F1 — D3 turn-on (DESCRIPTIVE-PRESPEC)", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_dir / "f1_turn_on.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f1_turn_on.pdf", facecolor=SURFACE)
    plt.close(fig)
    return numbers


# ---------------------------------------------------------------------------------- F2 rules x scopes
def fig_f2_rules_scopes(data: dict, out_dir: Path) -> dict:
    frame = data["completeness"]
    frame = frame[frame["pass"] == "best"]
    scopes = [
        ("detection_eligible_roster", "detection\neligible roster"),
        ("detection_usable_lightcurve", "detection\nusable light curve"),
        ("freq_recovery_scorable", "freq. recovery\nscorable"),
    ]
    primary = {("confirmed", "detection_eligible_roster"): "P1",
              ("confirmed", "freq_recovery_scorable"): "P2"}

    fig, axis = plt.subplots(figsize=(8.8, 4.0))
    width = 0.19
    numbers: dict = {}
    for si, (scope, scope_label) in enumerate(scopes):
        for ri, rule in enumerate(RULE_ORDER):
            row = frame[(frame["scope"] == scope) & (frame["rule"] == rule)]
            if row.empty:
                continue
            row = row.iloc[0]
            x = si + (ri - 1.5) * width
            n, p, lo, hi = int(row["n"]), row["p"], row["lo"], row["hi"]
            is_primary = (rule, scope) in primary
            axis.bar(x, p, width=width * 0.92, color=RULE_COLOR[rule],
                    edgecolor=INK if is_primary else "none", linewidth=2.4 if is_primary else 0,
                    zorder=3)
            axis.errorbar([x], [p], yerr=yerr_pair(p, lo, hi), fmt="none", ecolor=INK_SECONDARY,
                          capsize=2.5, linewidth=1.0, zorder=4)
            if is_primary:
                annotate_bar(axis, x, hi, primary[(rule, scope)], color=INK, fontsize=8, dy=0.03)
            numbers[f"{rule}__{scope}"] = {"n": n, "p": p, "lo": lo, "hi": hi,
                                            "primary": primary.get((rule, scope), "")}
    axis.set_xticks(range(len(scopes)))
    axis.set_xticklabels([label for _, label in scopes], fontsize=8)
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("completeness (best pass, Wilson 95%)", fontsize=8)
    axis.set_title("F2 — D3 rules x scopes (PRIMARY-P1/P2 outlined)", fontsize=10, color=INK)
    handles = [mpatches.Patch(facecolor=RULE_COLOR[r], label=RULE_LABEL[r].replace("\n", " "))
              for r in RULE_ORDER]
    axis.legend(handles=handles, loc="upper right", fontsize=7, frameon=False, ncol=2)
    style(axis)
    fig.tight_layout()
    fig.savefig(out_dir / "f2_rules_scopes.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f2_rules_scopes.pdf", facecolor=SURFACE)
    plt.close(fig)
    return numbers


# ---------------------------------------------------------------------------------- F3 negatives
def fig_f3_negatives(data: dict, out_dir: Path) -> dict:
    trig = data["trigger_rates"]
    fp = data["fp_frequency_distribution"]
    decomposition = data["trigger_decomposition"]
    numbers: dict = {"trigger_rate": {}, "decomposition": {}}

    fig, (left, right) = plt.subplots(1, 2, figsize=(10.2, 3.8),
                                      gridspec_kw={"width_ratios": [1, 1.6]})

    # (a) P3 by rule, plain Wilson
    for i, rule in enumerate(RULE_ORDER):
        row = trig[(trig["quantity"] == "negative_class_trigger_rate") & (trig["rule"] == rule)]
        if row.empty:
            continue
        row = row.iloc[0]
        n, p, lo, hi = int(row["n"]), row["p"], row["lo"], row["hi"]
        left.bar(i, p, width=0.6, color=RULE_COLOR[rule],
                edgecolor=INK if rule == "confirmed" else "none",
                linewidth=2.4 if rule == "confirmed" else 0, zorder=3)
        left.errorbar([i], [p], yerr=yerr_pair(p, lo, hi), fmt="none", ecolor=INK_SECONDARY,
                     capsize=3, zorder=4)
        if rule == "confirmed":
            annotate_bar(left, i, hi, "P3", color=INK, fontsize=8, dy=0.03)
        numbers["trigger_rate"][rule] = {"n": n, "p": p, "lo": lo, "hi": hi}
    left.set_xticks(range(4))
    left.set_xticklabels([RULE_LABEL[r] for r in RULE_ORDER], fontsize=7)
    left.set_ylim(0, 1.0)
    left.set_ylabel("negative-class trigger rate\n(P3 = confirmed; plain Wilson)", fontsize=8)
    left.set_title("(a) by rule", fontsize=9, color=INK)
    style(left)

    # (b) confirmed-negative frequency histogram, low pass 0-4 c/d (where the ruled bands sit),
    # bands [k-0.020, k+0.020] c/d shaded, k=1..3
    confirmed_neg = fp[fp["best_status"] == "confirmed"]
    freqs = confirmed_neg["best_frequency_per_day"].to_numpy(dtype=float)
    low = freqs[freqs < 4.0]
    bins = np.arange(0.0, 4.0 + 0.05, 0.05)
    right.hist(low, bins=bins, color=INK, alpha=0.85, zorder=3, linewidth=0)
    for k in (1, 2, 3):
        right.axvspan(k - 0.020, k + 0.020, facecolor=MUTED, alpha=0.35, hatch="////",
                     edgecolor=INK_SECONDARY, linewidth=0, zorder=2)
    within = decomposition[decomposition["component"] == "within_solar_diurnal_band"].iloc[0]
    outside = decomposition[decomposition["component"] == "outside_solar_diurnal_band"].iloc[0]
    right.annotate(
        f"within bands: {int(within['n_component'])}/{int(within['n_confirmed_total'])} "
        f"({within['rate_of_all_negatives']:.3f} of all negatives)\n"
        f"outside bands (all passes, all f): {int(outside['n_component'])}/{int(outside['n_confirmed_total'])} "
        f"({outside['rate_of_all_negatives']:.3f})",
        xy=(0.02, 0.97), xycoords="axes fraction", ha="left", va="top", fontsize=6.6, color=INK_SECONDARY,
        zorder=6, bbox=dict(boxstyle="round,pad=0.35", facecolor=SURFACE, edgecolor=GRID,
                            linewidth=0.7, alpha=0.96))
    right.set_xlabel("best-pass frequency (c/d), confirmed negatives, low pass", fontsize=8)
    right.set_ylabel("count", fontsize=8)
    right.set_title("(b) confirmed-negative frequencies (DESCRIPTIVE-PRESPEC audit;\n"
                    "shaded bands DESCRIPTIVE-POST-LAUNCH, no interval)", fontsize=8.3, color=INK)
    style(right)
    numbers["decomposition"] = {
        "within_solar_diurnal_band": {"n": int(within["n_component"]),
                                       "n_confirmed_total": int(within["n_confirmed_total"]),
                                       "rate_of_all_negatives": within["rate_of_all_negatives"]},
        "outside_solar_diurnal_band": {"n": int(outside["n_component"]),
                                       "n_confirmed_total": int(outside["n_confirmed_total"]),
                                       "rate_of_all_negatives": outside["rate_of_all_negatives"]},
    }

    fig.suptitle("F3 — D3 negatives", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out_dir / "f3_negatives.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f3_negatives.pdf", facecolor=SURFACE)
    plt.close(fig)
    return numbers


# ---------------------------------------------------------------------------------- F4 complementarity
def fig_f4_complementarity(data: dict, out_dir: Path) -> dict:
    c = data["contingency"]
    table = c["table"]
    # rows = census yes / no, columns = L-S confirmed / not confirmed:
    # census-only stars are census YES and L-S NOT confirmed (row 0, col 1);
    # L-S-only stars are census NO and L-S confirmed (row 1, col 0)
    cells = np.array([[table["census_and_ls"], table["census_only"]],
                      [table["ls_only"], table["neither"]]], dtype=float)
    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
    norm = Normalize(vmin=0, vmax=cells.max())

    fig, axis = plt.subplots(figsize=(4.2, 3.8))
    axis.imshow(cells, cmap=cmap, norm=norm)
    for i in range(2):
        for j in range(2):
            value = int(cells[i, j])
            text_color = "#ffffff" if norm(value) > 0.55 else INK
            axis.text(j, i, str(value), ha="center", va="center", fontsize=15, color=text_color,
                     fontweight="bold")
    axis.set_xticks([0, 1]); axis.set_xticklabels(["L-S confirmed", "L-S not confirmed"], fontsize=8)
    axis.set_yticks([0, 1]); axis.set_yticklabels(["census yes", "census no"], fontsize=8)
    axis.tick_params(length=0)
    union = c["union_completeness"]
    axis.set_title(
        f"F4 - D3 complementarity, positives (n={c['n_positives_scored']})\n"
        f"union {union['p']:.3f} [{union['lo']:.3f}, {union['hi']:.3f}]\n"
        f"McNemar exact p = {c['mcnemar_exact_p_secondary']:.1e} (SECONDARY)",
        fontsize=8.5, color=INK)
    fig.tight_layout()
    fig.savefig(out_dir / "f4_complementarity.png", dpi=300, facecolor=SURFACE)
    fig.savefig(out_dir / "f4_complementarity.pdf", facecolor=SURFACE)
    plt.close(fig)
    return {"table": table, "union_completeness": union,
            "incremental_census_only": c["incremental_census_only"],
            "incremental_ls_only": c["incremental_ls_only"],
            "mcnemar_exact_p_secondary": c["mcnemar_exact_p_secondary"],
            "n_positives_scored": c["n_positives_scored"]}


# ---------------------------------------------------------------------------------- captions + manifest
CAPTIONS = {
    "F1": ("D3 turn-on. Rule-1 (confirmed), best-pass detection completeness (left) and "
          "frequency-recovery completeness (right, dominant-direct match, marginalized over "
          "period bin) against the historical Kepler-band dominant amplitude, half-open bins "
          "{0.5,1,2,5,10,20,50,∞} mmag; the left panel adds an explicit `amp_unknown` bar "
          "(154 roster stars with no Mo-joined amplitude). Pointwise Wilson 95% only where "
          "n ≥ 5, else the raw count. No smoothing, fit, or interpolation. "
          "[DESCRIPTIVE-PRESPEC]"),
    "F2": ("D3 rules x scopes. Four detection rules (confirmed, confirmed-or-candidate, census, "
          "either) at the best pass, across three scopes (detection-eligible roster, "
          "detection-usable light curve, frequency-recovery-scorable), Wilson 95% error bars. "
          "The confirmed-rule bars at the eligible-roster and freq-recovery-scorable scopes are "
          "outlined and marked P1/P2. [PRIMARY-P1/P2 outlined; rest DESCRIPTIVE-PRESPEC]"),
    "F3": ("D3 negatives. (a) Negative-class trigger rate per rule (P3 = confirmed), plain "
          "Wilson 95%. (b) Histogram of best-pass frequencies of confirmed negatives, low pass "
          "(<4 c/d, where the ruled bands sit); the solar-diurnal bands [k−0.020, k+0.020] "
          "c/d (k=1,2,3) are shaded. " + DISCLOSURE_SENTENCE + " [PRIMARY-P3; DESCRIPTIVE-PRESPEC "
          "(histogram, the prespecified FP-frequency audit); DESCRIPTIVE-POST-LAUNCH (shaded "
          "bands and their counts)]"),
    "F4": ("D3 complementarity. 2x2 census x L-S (rule 1, best pass) on positives with both "
          "methods usable; union and incremental yields with Wilson 95%; exact McNemar p in the "
          "panel title. [DESCRIPTIVE-PRESPEC; McNemar SECONDARY]"),
}


def write_captions(out_dir: Path) -> None:
    lines = ["# D3 poster figure captions (F1-F4)\n"]
    for key in ("F1", "F2", "F3", "F4"):
        lines.append(f"## {key}\n\n{CAPTIONS[key]}\n")
    (out_dir / "captions.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True,
                        help="generalization/results/2026-09-02_d3 (or a later dated bundle "
                             "of the same schema)")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    data, shas = load_bundle(args.bundle)
    numbers = {
        "F1": fig_f1_turn_on(data, args.out_dir),
        "F2": fig_f2_rules_scopes(data, args.out_dir),
        "F3": fig_f3_negatives(data, args.out_dir),
        "F4": fig_f4_complementarity(data, args.out_dir),
    }
    write_captions(args.out_dir)

    manifest = {
        "bundle": str(args.bundle),
        "inputs_sha256": shas,
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "figures": {
            "F1": {"png": "f1_turn_on.png", "pdf": "f1_turn_on.pdf", "numbers": numbers["F1"]},
            "F2": {"png": "f2_rules_scopes.png", "pdf": "f2_rules_scopes.pdf", "numbers": numbers["F2"]},
            "F3": {"png": "f3_negatives.png", "pdf": "f3_negatives.pdf", "numbers": numbers["F3"]},
            "F4": {"png": "f4_complementarity.png", "pdf": "f4_complementarity.pdf", "numbers": numbers["F4"]},
        },
        "disclosure_sentence_f3": DISCLOSURE_SENTENCE,
        "captions": CAPTIONS,
    }
    (args.out_dir / "figures.manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"[d3_poster_figures] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
