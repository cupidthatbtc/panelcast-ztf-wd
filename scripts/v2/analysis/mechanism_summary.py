#!/usr/bin/env python3
"""v2 MECHANISM SUMMARY (descriptive; poster figure F12, EVIDENCE_MAP V2-12/13).

From a directory of v2 per-star JSONs (optionally restricted to a registered
id list), aggregate the two mechanism diagnostics the outline needs:

  (a) alignment — one row per (star, band, oid) from `v2.alignment`
      (n, n_shared_nights, offset_mmag, applied, role) and a per-band summary
      (oid counts by role, |offset| and shared-night quantiles among aligned
      oids); `alignment_affected_sids.txt` lists the stars with at least one
      oid left unshifted for insufficient overlap (the endpoint-sensitivity
      subset declared in V2_PLAN.md §6);
  (b) coherence — for every pass and every candidate with at least one
      unaliased band below the FAP threshold (status confirmed or candidate):
      delta phase, per-band phase errors, amplitude ratio, per-band amplitude
      S/N (amplitude / amplitude error), the gate outcome and the recorded
      reason; a stratified table of coherent vs incoherent counts by
      max-phase-error bin x min-amplitude-S/N bin.

Purely descriptive: nothing here feeds a decision. Outputs + a manifest with
input SHAs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

PHASE_ERROR_EDGES = [0.0, 0.02, 0.05, 0.10, math.inf]
SNR_EDGES = [0.0, 3.0, 5.0, 10.0, math.inf]
PHASE_LABELS = ["<0.02", "0.02-0.05", "0.05-0.10", ">=0.10"]
SNR_LABELS = ["<3", "3-5", "5-10", ">=10"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bin(value: float, edges: list[float], labels: list[str]) -> str:
    if value is None or not math.isfinite(value):
        return "undefined"
    for i in range(len(labels)):
        if edges[i] <= value < edges[i + 1]:
            return labels[i]
    return labels[-1]


def load_results(stars_dir: Path, ids: set[str] | None) -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(stars_dir.glob("*.json")):
        if path.name.endswith((".prov.json", ".error.json")):
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("engine") != "v2" or not result.get("complete"):
            continue
        if ids is not None and result.get("source_id") not in ids:
            continue
        out.append((path, result))
    return out


def alignment_tables(results: list[tuple[Path, dict]]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rows = []
    for _, result in results:
        for entry in result.get("v2", {}).get("alignment", []):
            rows.append({"sid": result["source_id"], **entry})
    table = pd.DataFrame(rows, columns=["sid", "band", "oid", "n", "n_shared_nights", "offset_mmag", "applied", "role"])
    summary_rows = []
    for band, group in table.groupby("band"):
        aligned = group[group["applied"] == True]  # noqa: E712
        abs_offsets = aligned["offset_mmag"].abs()
        summary_rows.append({
            "band": band,
            "n_stars": int(group["sid"].nunique()),
            "n_oids": int(len(group)),
            "n_anchor": int((group["role"] == "anchor").sum()),
            "n_aligned": int(len(aligned)),
            "n_unshifted_too_few_rows": int((group["role"] == "unshifted_too_few_rows").sum()),
            "n_unshifted_insufficient_overlap": int((group["role"] == "unshifted_insufficient_overlap").sum()),
            "abs_offset_mmag_q50": float(abs_offsets.median()) if len(aligned) else math.nan,
            "abs_offset_mmag_q90": float(abs_offsets.quantile(0.9)) if len(aligned) else math.nan,
            "abs_offset_mmag_max": float(abs_offsets.max()) if len(aligned) else math.nan,
            "shared_nights_q10": float(aligned["n_shared_nights"].quantile(0.1)) if len(aligned) else math.nan,
            "shared_nights_q50": float(aligned["n_shared_nights"].median()) if len(aligned) else math.nan,
        })
    affected = sorted(set(table.loc[table["role"] == "unshifted_insufficient_overlap", "sid"]))
    return table, pd.DataFrame(summary_rows), affected


def coherence_tables(results: list[tuple[Path, dict]], fap_threshold: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for _, result in results:
        for pass_name, pass_result in result["passes"].items():
            v2 = pass_result.get("v2")
            if not v2:
                continue
            for cand in v2["candidates"]:
                significant = [b for b in ("zg", "zr")
                               if float(cand[f"{b}_fap"]) < fap_threshold and not bool(cand[f"{b}_alias"])]
                if not significant:
                    continue
                snr = {b: (float(cand[f"{b}_amplitude_mmag"]) / float(cand[f"{b}_amplitude_error_mmag"])
                           if float(cand[f"{b}_amplitude_error_mmag"]) > 0 else math.inf) for b in ("zg", "zr")}
                phase_err = {b: float(cand[f"{b}_phase_error_cycles"]) for b in ("zg", "zr")}
                rows.append({
                    "sid": result["source_id"], "pass": pass_name,
                    "frequency_per_day": float(cand["frequency_per_day"]),
                    "is_best": cand is v2["candidates"][0],
                    "status": cand["status"], "candidate_reason": cand.get("candidate_reason", ""),
                    "significant_bands": "+".join(significant),
                    "delta_phase_cycles": float(cand["delta_phase_cycles"]),
                    "zg_phase_error_cycles": phase_err["zg"], "zr_phase_error_cycles": phase_err["zr"],
                    "max_phase_error_cycles": max(phase_err.values()),
                    "amp_ratio_r_over_g": cand.get("amp_ratio_r_over_g"),
                    "zg_amp_snr": snr["zg"], "zr_amp_snr": snr["zr"], "min_amp_snr": min(snr.values()),
                    "coherent": bool(cand["coherent"]), "joint_top5": bool(cand["joint_top5"]),
                })
    table = pd.DataFrame(rows)
    if table.empty:
        return table, pd.DataFrame()
    table["phase_error_bin"] = table["max_phase_error_cycles"].map(lambda v: _bin(v, PHASE_ERROR_EDGES, PHASE_LABELS))
    table["amp_snr_bin"] = table["min_amp_snr"].map(lambda v: _bin(v, SNR_EDGES, SNR_LABELS))
    strata = (table.groupby(["pass", "phase_error_bin", "amp_snr_bin"])
              .agg(n=("coherent", "size"), n_coherent=("coherent", "sum"),
                   n_confirmed=("status", lambda s: int((s == "confirmed").sum())))
              .reset_index())
    strata["n_incoherent"] = strata["n"] - strata["n_coherent"]
    return table, strata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stars-dir", type=Path, required=True)
    parser.add_argument("--ids-file", type=Path, default=None, help="registered id list to restrict to")
    parser.add_argument("--fap-threshold", type=float, default=1e-3)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    ids = None
    if args.ids_file is not None:
        ids = {line.strip() for line in args.ids_file.read_text().splitlines() if line.strip()}
    results = load_results(args.stars_dir, ids)
    if not results:
        raise SystemExit("no complete v2 results found")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    offsets, alignment_summary, affected = alignment_tables(results)
    offsets.to_csv(args.out_dir / "alignment_offsets.csv", index=False, lineterminator="\n")
    alignment_summary.to_csv(args.out_dir / "alignment_summary.csv", index=False, lineterminator="\n")
    (args.out_dir / "alignment_affected_sids.txt").write_text("\n".join(affected) + ("\n" if affected else ""), encoding="utf-8")
    candidates, strata = coherence_tables(results, args.fap_threshold)
    candidates.to_csv(args.out_dir / "coherence_candidates.csv", index=False, lineterminator="\n")
    strata.to_csv(args.out_dir / "coherence_strata.csv", index=False, lineterminator="\n")
    inputs = {str(path): sha256_file(path) for path, _ in results}
    (args.out_dir / "mechanism_summary.manifest.json").write_text(json.dumps({
        "n_stars": len(results), "ids_file": str(args.ids_file) if args.ids_file else "",
        "ids_file_sha256": sha256_file(args.ids_file) if args.ids_file else "",
        "fap_threshold": args.fap_threshold, "n_alignment_affected": len(affected),
        "phase_error_edges": PHASE_ERROR_EDGES[:-1], "amp_snr_edges": SNR_EDGES[:-1],
        "inputs_sha256_count": len(inputs),
        "inputs_sha256_digest": hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
        "script_sha256": sha256_file(Path(__file__).resolve()),
    }, indent=2) + "\n", encoding="utf-8")
    with pd.option_context("display.width", 200):
        print(alignment_summary.to_string(index=False))
        print(strata.to_string(index=False) if not strata.empty else "no coherence candidates")
    print(f"[mechanism_summary] {len(results)} stars -> {args.out_dir} (alignment-affected: {len(affected)})")


if __name__ == "__main__":
    main()
