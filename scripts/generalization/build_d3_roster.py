#!/usr/bin/env python3
"""Build the D3 roster: ZTF x Kepler delta Scuti with external truth labels.

Sources (VizieR, cached under generalization/data/d3/raw with SHA-256 recorded):
  Murphy+2019  J/MNRAS/485/2380/table1  14,330 Kepler A/F stars; dSct flag
               0 = not delta Sct (labeled negative class), 1 = delta Sct,
               2 = ambiguous (kept as its own class, excluded from headline
               completeness/FPR); gmag; positions.
  Mo+2026      J/A+A/710/A245/table2    259,883 extracted frequencies (SNR>8)
               for 1,838 Kepler delta Sct stars; per-star dominant amplitude
               (ppt) and its frequency (uHz).
  Mo+2026      J/A+A/710/A245/table1    15,265 confirmed super-Nyquist
               frequencies in 1,309 stars; any confirmed SNF implies a real
               mode above the Kepler LC Nyquist (283.2 uHz), i.e. P < 59 min
               -> the sub-hour stratum.

Selection:
  gmag >= 13.2 (ZTF saturation; gmag is the Murphy/KIC g magnitude); ALL
  dSct=1 (610) and dSct=2 (76) survivors; dSct=0 negatives drawn as a
  frozen-seed simple random sample (seed 20260828) with the inclusion
  probability recorded and a sampling_weight column carried into metrics.

Labels are obtained independently of the frozen ZTF pipeline. Negatives are
"not a delta Sct", not "constant": the D3 negative-class result is a TRIGGER
RATE, never an FPR (GENERALIZATION_PLAN.md risk 5; estimand names in
METRICS_SPEC.md are binding).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from frozen_api import REPO_ROOT, assert_frozen, campaign_id_ok

TAP_SYNC = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
PPT_TO_MMAG = 1.0857  # dm = -2.5 log10(1 + dF/F) ~= 1.0857 (dF/F); 1 ppt -> 1.0857 mmag
UHZ_TO_PER_DAY = 86400.0 / 1e6
KEPLER_LC_NYQUIST_UHZ = 283.2
NEGATIVE_SAMPLE_SEED = 20260828

QUERIES = {
    "murphy2019_table1.csv": 'SELECT KIC, GaiaDR2, gmag, Teff, logg, dSct, _RA, _DE '
                             'FROM "J/MNRAS/485/2380/table1"',
    "mo2026_table2.csv": 'SELECT KIC, Freq, Amp FROM "J/A+A/710/A245/table2"',
    "mo2026_table1.csv": 'SELECT KIC, Freq, Amp, fR, C, SC FROM "J/A+A/710/A245/table1"',
}


def tap_fetch(query: str, retries: int = 4) -> str:
    payload = urllib.parse.urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    ).encode()
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(TAP_SYNC, data=payload)
            with urllib.request.urlopen(request, timeout=300) as response:
                text = response.read().decode("utf-8")
            if text.lstrip().startswith("<?xml"):
                raise RuntimeError(f"TAP error response: {text[:300]}")
            return text
        except Exception:
            if attempt == retries:
                raise
            time.sleep(5.0 * (attempt + 1))
    raise RuntimeError("unreachable")


def cached_pull(raw_dir: Path, name: str, provenance: dict) -> pd.DataFrame:
    path = raw_dir / name
    if not path.exists():
        text = tap_fetch(QUERIES[name])
        path.write_text(text, encoding="utf-8", newline="")
    raw = path.read_bytes()
    provenance[name] = {
        "query": QUERIES[name],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    return pd.read_csv(io.BytesIO(raw))


def campaign_id_for_kic(kic: int) -> str:
    return "90" + str(int(kic)).zfill(17)


def amp_ladder_stratum(amp_mmag: float, subhour: bool) -> str:
    if subhour:
        return "subhour"
    if not np.isfinite(amp_mmag):
        return "amp_unknown"
    if amp_mmag > 10.0:
        return "amp_gt10"
    if amp_mmag >= 1.0:
        edges = np.logspace(0.0, 1.0, 7)  # six log bins across 1-10 mmag
        return f"amp_ladder_{np.searchsorted(edges, amp_mmag, side='right')}"
    return "amp_lt1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "generalization/data/d3")
    parser.add_argument("--total", type=int, default=3000)
    parser.add_argument("--mag-cut", type=float, default=13.2)
    args = parser.parse_args()

    assert_frozen()
    raw_dir = args.out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    provenance: dict[str, dict] = {}

    murphy = cached_pull(raw_dir, "murphy2019_table1.csv", provenance)
    freqs = cached_pull(raw_dir, "mo2026_table2.csv", provenance)
    snf = cached_pull(raw_dir, "mo2026_table1.csv", provenance)

    if len(murphy) != 14330:
        raise SystemExit(f"Murphy table has {len(murphy)} rows, expected 14330")
    if len(freqs) != 259883:
        raise SystemExit(f"Mo table2 has {len(freqs)} rows, expected 259883")
    if len(snf) != 15265:
        raise SystemExit(f"Mo table1 has {len(snf)} rows, expected 15265")

    dominant = freqs.loc[freqs.groupby("KIC")["Amp"].idxmax()]
    dominant = dominant.rename(columns={"Freq": "dom_freq_uhz", "Amp": "dom_amp_ppt"})
    subhour_kics = set(snf.loc[snf["C"] == 0, "KIC"].astype(int))

    stars = murphy.merge(dominant[["KIC", "dom_freq_uhz", "dom_amp_ppt"]], on="KIC", how="left")
    stars["amp_mmag"] = stars["dom_amp_ppt"] * PPT_TO_MMAG
    stars["dom_freq_per_day"] = stars["dom_freq_uhz"] * UHZ_TO_PER_DAY
    stars["subhour"] = stars["KIC"].astype(int).isin(subhour_kics)
    stars = stars[stars["gmag"] >= args.mag_cut].copy()
    if (stars["_DE"] < -28.0).any():
        raise SystemExit("targets below the ZTF footprint; Kepler field expected")

    positives = stars[stars["dSct"] == 1].sort_values("KIC")
    ambiguous = stars[stars["dSct"] == 2].sort_values("KIC")
    negatives_pool = stars[stars["dSct"] == 0].sort_values("KIC").reset_index(drop=True)
    n_negatives = max(0, args.total - len(positives) - len(ambiguous))
    # frozen-seed simple random sample (G1 referee finding 15: KIC-order stride
    # correlates with sky position/coverage); inclusion probability recorded so
    # population rates can be reweighted
    rng = np.random.Generator(np.random.PCG64(NEGATIVE_SAMPLE_SEED))
    chosen = np.sort(rng.choice(len(negatives_pool), size=n_negatives, replace=False))
    negatives = negatives_pool.iloc[chosen]

    roster = pd.concat([positives, ambiguous, negatives], ignore_index=True)
    roster["source_id"] = [campaign_id_for_kic(k) for k in roster["KIC"]]
    roster["external_id"] = ["KIC " + str(int(k)) for k in roster["KIC"]]
    roster["ra"] = roster["_RA"]
    roster["dec"] = roster["_DE"]
    roster["class_label"] = ["dsct_flag" + str(int(f)) for f in roster["dSct"]]
    roster["label_variable"] = roster["dSct"].map({0: False, 1: True, 2: None})
    roster["label_periodic"] = roster["label_variable"]
    roster["near_saturation"] = roster["gmag"] < 14.0
    roster["sampling_weight"] = [
        (len(negatives_pool) / len(negatives)) if flag == 0 else 1.0
        for flag in roster["dSct"]
    ]
    roster["stratum"] = [
        amp_ladder_stratum(a, s) if flag == 1 else f"class_{flag}"
        for a, s, flag in zip(roster["amp_mmag"], roster["subhour"], roster["dSct"])
    ]
    bad = [sid for sid in roster["source_id"] if not campaign_id_ok(sid)]
    if bad:
        raise SystemExit(f"generated invalid campaign ids: {bad[:3]}")
    if roster["source_id"].duplicated().any():
        raise SystemExit("duplicate campaign ids")

    columns = [
        "source_id", "external_id", "ra", "dec", "class_label",
        "label_variable", "label_periodic", "gaia_g_mag",
        "KIC", "gmag", "Teff", "logg", "dSct", "dom_freq_uhz",
        "dom_freq_per_day", "dom_amp_ppt", "amp_mmag", "subhour",
        "near_saturation", "stratum", "sampling_weight",
    ]
    roster["gaia_g_mag"] = ""
    roster_path = args.out_dir / "roster_d3.csv"
    roster[columns].to_csv(roster_path, index=False)

    pos_amp = positives["amp_mmag"]
    report = {
        "roster": str(roster_path),
        "mag_cut": args.mag_cut,
        "counts": {
            "total": len(roster),
            "positives_dsct1": len(positives),
            "ambiguous_dsct2": len(ambiguous),
            "negatives_dsct0": len(negatives),
            "negatives_pool": len(negatives_pool),
            "negative_sample_seed": NEGATIVE_SAMPLE_SEED,
            "negative_inclusion_probability": n_negatives / len(negatives_pool),
        },
        "positives_amplitude_mmag": {
            "with_amplitude": int(np.isfinite(pos_amp).sum()),
            "without_amplitude": int((~np.isfinite(pos_amp)).sum()),
            "gt10": int((pos_amp > 10).sum()),
            "1to10": int(((pos_amp >= 1) & (pos_amp <= 10)).sum()),
            "lt1": int((pos_amp < 1).sum()),
            "subhour": int(positives["subhour"].sum()),
            "quantiles": {
                q: round(float(np.nanquantile(pos_amp, float(q))), 3)
                for q in ("0.05", "0.25", "0.5", "0.75", "0.95")
            },
        },
        "strata": roster["stratum"].value_counts().to_dict(),
        "provenance": provenance,
        "conversions": {"ppt_to_mmag": PPT_TO_MMAG, "uhz_to_per_day": UHZ_TO_PER_DAY,
                        "kepler_lc_nyquist_uhz": KEPLER_LC_NYQUIST_UHZ},
    }
    (args.out_dir / "roster_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in ("counts", "positives_amplitude_mmag")}, indent=2))


if __name__ == "__main__":
    main()
