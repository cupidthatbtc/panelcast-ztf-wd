#!/usr/bin/env python3
"""Write the directed-search and accuracy frequencies from Jestin et al. (2026)."""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://arxiv.org/abs/2509.15133"

PERIODS = (
    ("1510467090935595008", "WDJ135309.97+484021.17", "V777 Her", 176.58, True, "draft Table 2 continuation, line 613"),
    ("3446909137068558464", "WDJ052038.32+304823.92", "ZZ Ceti", 320.01, True, "draft Table 2 continuation, line 614"),
    ("3984115430179696128", "WDJ111026.19+191229.75", "Old DAVs", 5.38, True, "draft Table 2 continuation, line 615"),
    ("1893101535448502400", "WDJ220247.69+275010.67", "GW Vir", 1.23, True, "draft Table 2 continuation, line 617"),
    ("2833849800205759360", "", "unclassified", 6.1464, False, "draft Figure 3 caption, lines 390-394"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "data/roster/literature_periods.csv")
    args = parser.parse_args()

    rows = []
    for source_id, wdj_name, wd_class, frequency, directed_search, source_location in PERIODS:
        rows.append(
            {
                "source_id": source_id,
                "wdj_name": wdj_name,
                "wd_class": wd_class,
                "frequency_per_day": frequency,
                "period_days": 1.0 / frequency,
                "period_seconds": 86400.0 / frequency,
                "directed_search": directed_search,
                "source": "Jestin et al. 2026",
                "source_url": SOURCE_URL,
                "source_location": source_location,
                "independent_period_source": (
                    "none found in exact-name/Gaia-ID SIMBAD-VizieR searches"
                    if directed_search
                    else "not queried; paper reference only"
                ),
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
