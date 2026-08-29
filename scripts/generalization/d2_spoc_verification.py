#!/usr/bin/env python3
"""D2 verification arm — runs on Google Colab (standalone, NOT the frozen
pipeline; no frozen_api import by design).

For the 20 highest-amplitude D2 targets: download TESS SPOC light curves
(MAST is fast from Google's network), then
  (a) DIRECTED check: linear least-squares sinusoid amplitude at every
      published Romero frequency, with an SNR from the local residual noise
      — confirms the published (period, amplitude) solutions;
  (b) BLIND check: iterative prewhitening (10 modes, coarse grid) — the
      dominant recovered frequency must match the published dominant;
  (c) harvest CROWDSAP per sector — the dilution factors that enable the
      prespecified de-dilution variant (GENERALIZATION_PLAN, D2).

Inputs (uploaded next to this script): d2_targets.csv, d2_modes.csv.
Outputs: spoc_verification_report.json, spoc_recovered_modes.csv.
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

N_TARGETS = 20
BLIND_MODES = 10
MATCH_REL_TOL = 1e-3
FREQ_MIN_PER_DAY = 4.0
FREQ_MAX_PER_DAY = 1250.0


def fit_amplitude(time_d: np.ndarray, flux: np.ndarray, freq_per_day: float):
    phase = 2.0 * np.pi * freq_per_day * time_d
    design = np.column_stack((np.ones_like(time_d), np.sin(phase), np.cos(phase)))
    beta, *_ = np.linalg.lstsq(design, flux, rcond=None)
    amp = float(np.hypot(beta[1], beta[2]))
    model = design @ beta
    return amp, model


def prewhiten(time_d: np.ndarray, flux: np.ndarray, n_modes: int):
    from astropy.timeseries import LombScargle
    residual = flux - np.mean(flux)
    found = []
    for _ in range(n_modes):
        ls = LombScargle(time_d, residual)
        freq, power = ls.autopower(
            minimum_frequency=FREQ_MIN_PER_DAY,
            maximum_frequency=FREQ_MAX_PER_DAY,
            samples_per_peak=4,
        )
        best = float(freq[np.argmax(power)])
        amp, model = fit_amplitude(time_d, residual, best)
        residual = residual - model
        noise = float(np.sqrt(2.0 / len(time_d)) * np.std(residual))
        found.append({"frequency_per_day": best, "period_s": 86400.0 / best,
                      "amp_ppt": amp * 1000.0, "snr": amp / noise if noise else 0.0})
        if amp / max(noise, 1e-12) < 4.0:
            break
    return found


def main() -> None:
    import lightkurve as lk

    targets = pd.read_csv("d2_targets.csv")
    modes = pd.read_csv("d2_modes.csv")
    dominant_amp = modes.groupby("tic")["amp_ppt"].max()
    chosen = dominant_amp.sort_values(ascending=False).head(N_TARGETS).index

    report = []
    recovered_rows = []
    for tic in chosen:
        entry = {"tic": int(tic)}
        try:
            search = lk.search_lightcurve(f"TIC {tic}", author="SPOC", exptime=120)
            if len(search) == 0:
                search = lk.search_lightcurve(f"TIC {tic}", author="SPOC", exptime=20)
                entry["cadence_s"] = 20
            else:
                entry["cadence_s"] = 120
            collection = search.download_all(quality_bitmask="default")
            crowdsap = [
                float(lc.meta.get("CROWDSAP")) for lc in collection
                if lc.meta.get("CROWDSAP") is not None
            ]
            stitched = collection.stitch().remove_nans()
            time_d = np.asarray(stitched.time.value, dtype=float)
            flux = np.asarray(stitched.flux.value, dtype=float)
            flux = flux / np.median(flux) - 1.0
            entry.update({
                "n_sectors": len(collection),
                "n_points": int(len(time_d)),
                "crowdsap_median": float(np.median(crowdsap)) if crowdsap else None,
                "crowdsap_all": crowdsap,
            })

            published = modes[modes["tic"] == tic]
            noise = float(np.sqrt(2.0 / len(time_d)) * np.std(flux))
            directed = []
            for row in published.itertuples(index=False):
                freq = 86400.0 / row.period_s
                amp, _ = fit_amplitude(time_d, flux, freq)
                directed.append({
                    "period_s": row.period_s,
                    "published_amp_ppt": row.amp_ppt,
                    "recovered_amp_ppt": amp * 1000.0,
                    "amp_ratio": amp * 1000.0 / row.amp_ppt if row.amp_ppt else None,
                    "snr": amp / noise if noise else 0.0,
                })
            entry["directed"] = directed
            entry["directed_confirmed_snr4"] = int(
                sum(1 for d in directed if d["snr"] >= 4.0))
            entry["n_published_modes"] = len(directed)

            blind = prewhiten(time_d, flux, BLIND_MODES)
            entry["blind_top"] = blind[:5]
            pub_dom_period = float(
                published.loc[published["amp_ppt"].idxmax(), "period_s"])
            dom_match = any(
                abs(86400.0 / b["frequency_per_day"] - pub_dom_period)
                / pub_dom_period < MATCH_REL_TOL
                for b in blind[:3]
            )
            entry["blind_dominant_matches_published"] = bool(dom_match)
            for b in blind:
                recovered_rows.append({"tic": int(tic), **b})
        except Exception as exc:
            entry["error"] = repr(exc)
        report.append(entry)
        print(f"[spoc-verify] TIC {tic}: "
              f"{entry.get('directed_confirmed_snr4', 'ERR')}/"
              f"{entry.get('n_published_modes', '?')} directed modes at SNR>=4, "
              f"dominant match={entry.get('blind_dominant_matches_published')}",
              flush=True)

    ok = [e for e in report if "error" not in e]
    summary = {
        "targets_attempted": len(report),
        "targets_ok": len(ok),
        "dominant_matches": sum(
            1 for e in ok if e.get("blind_dominant_matches_published")),
        "directed_modes_total": sum(e.get("n_published_modes", 0) for e in ok),
        "directed_confirmed_snr4": sum(
            e.get("directed_confirmed_snr4", 0) for e in ok),
        "crowdsap_available": sum(
            1 for e in ok if e.get("crowdsap_median") is not None),
    }
    with open("spoc_verification_report.json", "w") as handle:
        json.dump({"summary": summary, "targets": report}, handle, indent=2)
    pd.DataFrame(recovered_rows).to_csv("spoc_recovered_modes.csv", index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
