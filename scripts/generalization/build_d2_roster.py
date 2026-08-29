#!/usr/bin/env python3
"""Build the D2 truth roster from the Romero TESS DAV papers.

Parses the published per-mode tables (period [s], amplitude [ppt]) from the
arXiv LaTeX sources cached in generalization/data/d2/raw:
  Romero+2022  arXiv:2201.04158 (MNRAS 511, 1574)  74 new DAVs, Cycles 1-3
  Romero+2025  arXiv:2407.07260 (ApJ 984, 112)     32 new DAVs, Cycles 4-5
               + Table "old": revised mode lists for re-observed 2022 DAVs,
               including NOV retractions.

Supersede policy (prespecified): the latest published solution per TIC wins —
2025 "old" table over 2022; NOV objects are dropped from the roster entirely.

The LaTeX tables contain human typos (comma decimals `356,09`, stray unit
`503.99s`, one missing close-paren, missing list commas). The parser
normalizes these mechanically and then enforces hard range/count asserts;
G3 reviews the parsed output against the paper PDFs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from frozen_api import REPO_ROOT, assert_frozen

RAW = REPO_ROOT / "generalization/data/d2/raw"
NOV_TICS = {261400271, 804835539, 317620456}
# TIC 683837451 is in the 2022 mode table but its Table-1 row is commented out
# in the arXiv source (NewTess.tex line ~260: "%0683837451 & 045827.11 &
# $-$654003.4 & 17.40 & ..."); values transcribed from that commented row.
CURATED_META = {
    683837451: {
        "ra": 15.0 * (4.0 + 58.0 / 60.0 + 27.11 / 3600.0),
        "dec": -(65.0 + 40.0 / 60.0 + 3.4 / 3600.0),
        "gmag": 17.40,
    }
}
MODE_PAIR = re.compile(r"(\d+\.\d+)\s*s?\s*\(\s*(\d+\.?\d*)\s*[)}]?")


def strip_row(line: str) -> str:
    # drop unescaped % comments, row terminator, italics markup, math mode
    out = []
    for index, char in enumerate(line):
        if char == "%" and (index == 0 or line[index - 1] != "\\"):
            break
        out.append(char)
    text = "".join(out)
    text = text.replace("\\\\", "").replace("{\\it", " ").replace("\\textit{", " ")
    text = text.replace("{", " ").replace("}", " ").replace("$", "")
    return text.strip()


def table_rows(source: str, header_pattern: str, count: int = 1) -> list[list[str]]:
    """All `&`-separated rows from tables whose header matches header_pattern."""
    rows: list[list[str]] = []
    seen = 0
    for block in re.split(r"\\begin\{table\*?\}", source)[1:]:
        body = block.split("\\end{table")[0]
        if not re.search(header_pattern, body):
            continue
        seen += 1
        for line in body.splitlines():
            if "&" not in line or "\\hline" in line:
                continue
            cleaned = strip_row(line)
            if not cleaned or re.search(header_pattern, line):
                continue
            rows.append([cell.strip() for cell in cleaned.split("&")])
    if seen < count:
        raise SystemExit(f"found {seen} tables matching {header_pattern!r}, expected >= {count}")
    return rows


def merge_continuations(rows: list[list[str]]) -> dict[int, list[list[str]]]:
    """Group rows by TIC; a leading-cdots row continues the previous TIC."""
    grouped: dict[int, list[list[str]]] = {}
    current: int | None = None
    for row in rows:
        first = row[0].replace("\\cdots", "").strip()
        if first.isdigit():
            current = int(first)
            grouped.setdefault(current, []).append(row)
        elif current is not None:
            grouped[current].append(row)
    return grouped


def parse_modes(cells: list[str]) -> list[tuple[float, float]]:
    text = " , ".join(cells)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)  # comma decimals -> dots
    return [(float(p), float(a)) for p, a in MODE_PAIR.findall(text)]


def parse_mode_table(source: str, paper: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = table_rows(source, r"FAP\(1/1000\)\s*\[ppt\]")
    modes: list[dict] = []
    stars: list[dict] = []
    for tic, group in merge_continuations(rows).items():
        sectors = group[0][1]
        fap_text = group[0][2].strip()
        mode_cells = [row[3] for row in group if len(row) > 3]
        extra_sectors = [
            row[1] for row in group[1:]
            if len(row) > 1 and re.search(r"\d", row[1].replace("\\cdots", ""))
        ]
        if extra_sectors:
            sectors = sectors.rstrip(", ") + "," + ",".join(extra_sectors)
        is_nov = any("NOV" in cell for cell in mode_cells)
        pairs = [] if is_nov else parse_modes(mode_cells)
        if not is_nov and not pairs:
            raise SystemExit(f"{paper} TIC {tic}: no modes parsed from {mode_cells!r}")
        stars.append(
            {
                "tic": tic,
                "paper": paper,
                "sectors": re.sub(r"\s+", "", sectors),
                "fap_ppt": float(fap_text),
                "cadence_s": 20 if "f" in sectors else 120,
                "nov": is_nov,
                "n_modes": len(pairs),
            }
        )
        for period, amp in pairs:
            modes.append({"tic": tic, "paper": paper, "period_s": period, "amp_ppt": amp})
    return pd.DataFrame(stars), pd.DataFrame(modes)


def sexagesimal_to_deg(ra_text: str, dec_text: str) -> tuple[float, float]:
    ra_text = ra_text.replace("\\", "").strip()
    dec_text = dec_text.replace("\\", "").replace("−", "-").strip()
    def split3(text: str) -> list[float]:
        parts = text.split(":")
        if len(parts) == 4:  # paper typo: colon used as the decimal point
            parts = parts[:2] + [parts[2] + "." + parts[3]]
        return [float(x) for x in parts]

    if ":" in ra_text:
        h, m, s = split3(ra_text)
        dd, dm, ds = split3(dec_text.replace("+", ""))
        sign = -1.0 if dec_text.lstrip().startswith("-") else 1.0
    else:
        h, m, s = float(ra_text[0:2]), float(ra_text[2:4]), float(ra_text[4:])
        stripped = dec_text.lstrip("+-")
        dd, dm, ds = float(stripped[0:2]), float(stripped[2:4]), float(stripped[4:])
        sign = -1.0 if dec_text.startswith("-") else 1.0
    return 15.0 * (h + m / 60.0 + s / 3600.0), sign * (abs(dd) + dm / 60.0 + ds / 3600.0)


def parse_star_table(source: str, paper: str) -> pd.DataFrame:
    rows = table_rows(source, r"RA\s*&\s*DEC")
    records = []
    for tic, group in merge_continuations(rows).items():
        row = group[0]
        ra, dec = sexagesimal_to_deg(row[1], row[2])
        records.append(
            {"tic": tic, "paper": paper, "ra": ra, "dec": dec, "gmag": float(row[3])}
        )
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "generalization/data/d2")
    args = parser.parse_args()
    assert_frozen()

    provenance = {
        name: hashlib.sha256((RAW / name).read_bytes()).hexdigest()
        for name in ("romero2022_src.tar.gz", "romero2025_src.tar.gz")
    }
    src2022 = (RAW / "romero2022_src/NewTess.tex").read_text(encoding="utf-8", errors="replace")
    src2025 = (RAW / "romero2025_src/NewTESS.tex").read_text(encoding="utf-8", errors="replace")

    # the 2025 file holds two mode tables: "new" (32) then "old" (revised
    # R22); slice at the old table's begin marker (its caption sits inside
    # the block, so slicing at the caption text would orphan the rows)
    old_caption = src2025.find("showing a change in the period list")
    if old_caption < 0:
        raise SystemExit("2025 old-table caption not found")
    old_start = src2025.rfind("\\begin{table", 0, old_caption)
    stars22, modes22 = parse_mode_table(src2022, "romero2022")
    stars25, modes25 = parse_mode_table(src2025[:old_start], "romero2025")
    stars25old, modes25old = parse_mode_table(src2025[old_start:], "romero2025old")

    if len(stars22) != 74:
        raise SystemExit(f"2022 mode table: {len(stars22)} stars, expected 74")
    if len(stars25) != 32:
        raise SystemExit(f"2025 new mode table: {len(stars25)} stars, expected 32")
    nov_found = set(stars25old.loc[stars25old["nov"], "tic"])
    if nov_found != NOV_TICS:
        raise SystemExit(f"NOV set {nov_found} != expected {NOV_TICS}")

    meta22 = parse_star_table(src2022, "romero2022")
    meta25 = parse_star_table(src2025, "romero2025")
    meta = pd.concat([meta25, meta22], ignore_index=True).drop_duplicates("tic", keep="first")

    # supersede: 2025old > 2022; drop NOV
    solutions = {}
    for frame in (stars22, stars25, stars25old):
        for record in frame.to_dict("records"):
            if record["paper"] == "romero2025old" or record["tic"] not in solutions:
                solutions[record["tic"]] = record
    targets = pd.DataFrame(
        record for record in solutions.values() if not record["nov"]
    ).sort_values("tic")
    modes = pd.concat([modes22, modes25, modes25old], ignore_index=True)
    chosen = modes.merge(
        targets[["tic", "paper"]], on=["tic", "paper"], how="inner"
    ).sort_values(["tic", "period_s"])

    if not ((chosen["period_s"] >= 70.0) & (chosen["period_s"] <= 2200.0)).all():
        bad = chosen[(chosen["period_s"] < 70.0) | (chosen["period_s"] > 2200.0)]
        raise SystemExit(f"periods out of DAV range:\n{bad}")
    if not ((chosen["amp_ppt"] > 0.0) & (chosen["amp_ppt"] <= 400.0)).all():
        raise SystemExit("amplitudes out of range")
    missing_meta = set(targets["tic"]) - set(meta["tic"])
    curated = [
        {"tic": tic, "paper": "curated", **CURATED_META[tic]}
        for tic in missing_meta
        if tic in CURATED_META
    ]
    if curated:
        meta = pd.concat([meta, pd.DataFrame(curated)], ignore_index=True)
        missing_meta -= set(CURATED_META)
    if missing_meta:
        raise SystemExit(f"targets missing star metadata: {sorted(missing_meta)[:5]}")

    targets = targets.merge(meta[["tic", "ra", "dec", "gmag"]], on="tic", how="left")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    targets.to_csv(args.out_dir / "d2_targets.csv", index=False)
    chosen.to_csv(args.out_dir / "d2_modes.csv", index=False)
    modes.to_csv(args.out_dir / "d2_modes_all_solutions.csv", index=False)

    report = {
        "targets": len(targets),
        "from_2022_only": int((targets["paper"] == "romero2022").sum()),
        "from_2025_new": int((targets["paper"] == "romero2025").sum()),
        "superseded_by_2025old": int((targets["paper"] == "romero2025old").sum()),
        "nov_dropped": sorted(NOV_TICS),
        "modes_total": len(chosen),
        "modes_per_star_median": float(targets["n_modes"].median()),
        "period_s_range": [float(chosen["period_s"].min()), float(chosen["period_s"].max())],
        "amp_ppt_range": [float(chosen["amp_ppt"].min()), float(chosen["amp_ppt"].max())],
        "stars_with_20s_cadence": int((targets["cadence_s"] == 20).sum()),
        "gmag_range": [float(targets["gmag"].min()), float(targets["gmag"].max())],
        "provenance_sha256": provenance,
    }
    (args.out_dir / "d2_roster_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
