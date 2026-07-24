"""Variability census of the panel: scatter-to-error ratio at both binnings.

For each star this computes sd(mag) / median(mag_err) on the nightly g-band
slice and again on the monthly rebin (the descriptor of record), and plots one
against the other. It needs no fit artifacts -- it reads the committed panel
CSVs directly, so it documents what the panel itself can carry before any model
touches it.

The point it makes: nightly and monthly binning average over the periods of the
compact pulsators (ZZ Ceti, GW Vir, V777 Her -- minutes to about an hour), so at
monthly cadence those stars are indistinguishable from the constant population,
while the hours-to-days variables (binaries, the CV, the transit) survive.

Usage:
    python scripts/plot_variance_census.py [-o figures/variance_census.png]
"""

import argparse
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE = "#0173b2"
RED = "#d62728"
GREY = "#888888"

# Compact pulsators: periods of minutes to ~an hour, i.e. far below the bin width.
PULSATOR_CLASSES = {"ZZ Ceti", "GW Vir", "V777 Her", "Old DAVs"}

# Illustrative light curves for the right-hand panel: one of each regime.
EXAMPLES = (
    ("4318508939464901760", BLUE, "double-band binary"),
    ("3446909137068558464", RED, "ZZ Ceti pulsator"),
    ("114808397128552576", GREY, "unclassified, paper-constant"),
)


def by_star(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open() as fh:
        for row in csv.DictReader(fh):
            grouped[row["source_id"].removeprefix("GaiaDR3_")].append(row)
    return grouped


def scatter_over_error(rows: list[dict[str, str]]) -> float:
    mags = [float(r["mag_binned"]) for r in rows]
    errs = [float(r["mag_err"]) for r in rows]
    return st.pstdev(mags) / st.median(errs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", type=Path, default=Path("data/roster/jestin2026_roster.csv"))
    ap.add_argument("--nightly", type=Path, default=Path("data/raw/ztf_wd_zg.csv"))
    ap.add_argument("--monthly", type=Path, default=Path("data/raw/ztf_wd_zg_monthly.csv"))
    ap.add_argument("-o", "--out", type=Path, default=Path("figures/variance_census.png"))
    args = ap.parse_args()

    with args.roster.open() as fh:
        roster = {r["source_id"]: r for r in csv.DictReader(fh)}
    nightly, monthly = by_star(args.nightly), by_star(args.monthly)

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(14, 6.2))

    for source_id, rows in nightly.items():
        meta = roster[source_id]
        wd_class, is_var = meta["wd_class"], meta["paper_variable"]
        x, y = scatter_over_error(rows), scatter_over_error(monthly[source_id])
        if wd_class in PULSATOR_CLASSES:
            colour, marker, size = RED, "*", 190
            label = "compact pulsator (paper: variable)"
            ax.annotate(
                wd_class, (x, y), xytext=(6, -10), textcoords="offset points", fontsize=8.5, color=RED
            )
        elif is_var == "True":
            colour, marker, size = BLUE, "o", 70
            label = "binary / transit / CV (paper: variable)"
        else:
            colour, marker, size = GREY, "s", 70
            label = "paper: constant or unclassified"
        ax.scatter(
            x, y, c=colour, marker=marker, s=size, label=label, zorder=3, edgecolor="k", linewidth=0.4
        )

    ax.axhline(1, ls=":", c="k", lw=1)
    ax.axhspan(0.3, 1.6, color="k", alpha=0.06, zorder=0)
    ax.text(1.05, 1.62, "indistinguishable from constant\nat monthly cadence", fontsize=8.5, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("scatter / median error — nightly bins")
    ax.set_ylabel("scatter / median error — monthly bins (descriptor of record)")
    ax.set_title("Binning averages over the pulsators, keeps the binaries", fontsize=11)
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8.5, loc="upper left")
    ax.grid(alpha=0.25, zorder=0)

    for source_id, colour, label in EXAMPLES:
        rows = sorted(nightly[source_id], key=lambda r: float(r["night_mjd"]))
        mjd = [float(r["night_mjd"]) for r in rows]
        mags = [float(r["mag_binned"]) for r in rows]
        median = st.median(mags)
        ratio = scatter_over_error(rows)
        bx.plot(
            mjd, [m - median for m in mags], ".", ms=2.6, c=colour, alpha=0.8,
            label=f"{label}  sd/err {ratio:.1f}",
        )

    bx.invert_yaxis()
    bx.set_ylim(1.1, -1.1)
    bx.set_xlabel("MJD")
    bx.set_ylabel("Δ mag (median-subtracted, g)")
    bx.set_title("Same three stars, nightly-binned ZTF g", fontsize=11)
    bx.legend(fontsize=8.5, markerscale=4, loc="upper right")
    bx.grid(alpha=0.25)

    fig.suptitle(
        "ZTF white-dwarf panel (19 stars) — what the variance census can and cannot see", fontsize=12.5
    )
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=155)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
