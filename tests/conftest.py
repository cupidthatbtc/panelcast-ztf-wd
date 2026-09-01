"""Shared synthetic fixtures for the post-launch descriptive D3 analyses
(reviews/G5prep/sol_round2.md items 2, 3, 8, 9). The synthetic world mimics
the frozen per_star.csv schema written by metrics_generalization.py, a
roster, Mo tables 1/2, per-star result JSONs and a metrics bundle on disk;
its frozen match columns are filled with the frozen classify_match so the
fixtures can never disagree with the taxonomy."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "generalization" / "descriptive"))
sys.path.insert(0, str(ROOT / "scripts" / "generalization"))

from metrics_generalization import classify_match, pass_eligible  # noqa: E402
from d3_descriptive_common import uhz_to_per_day  # noqa: E402

F_NYQ_UHZ = 283.2
F_NYQ_PER_DAY = 24.46848
UHZ_TO_PER_DAY = 86400.0 / 1e6
SIDEREAL = 1.00273790935
N_POS, N_JOINED, N_ALIASED, N_NEG, N_FLAG2 = 610, 456, 40, 2314, 76


def sid_for(prefix: int, i: int) -> str:
    return f"{prefix:02d}{i:017d}"


@dataclass
class World:
    per_star: pd.DataFrame
    roster: pd.DataFrame
    table1: pd.DataFrame
    table2: pd.DataFrame
    peaks: dict[str, list[float]]
    truth: dict[str, list[float]]
    d1_catalog: pd.DataFrame
    baseline: float
    notes: dict = field(default_factory=dict)


def build_world(baseline: float = 2700.0, n_pos: int = N_POS, n_joined: int = N_JOINED,
                n_aliased: int = N_ALIASED, n_neg: int = N_NEG, n_flag2: int = N_FLAG2) -> World:
    tol = 1.5 / baseline
    roster_rows, t1_rows, t2_rows, ps_rows = [], [], [], []
    peaks: dict[str, list[float]] = {}
    truth: dict[str, list[float]] = {}

    def dominant_per_day(i: int) -> float:
        if i < 60:
            return 1.0 + i * 0.03                      # [1.0, 2.8) -> < 4
        if i < n_joined - 10:
            return 5.0 + (i - 60) * 0.04               # [5.0, ~20.5) -> [4, 24)
        return 24.0 + (i - (n_joined - 10)) * 0.04     # 10 in [24, 24.36] -> [24, 24.46848)

    def per_star_row(sid, kic, class_label, label_positive, dom, amp, truth_list, joined,
                     status, best_freq, usable_high=True, peak_list=()):
        present = status != "missing"
        row = {
            "sid": sid, "external_id": f"KIC {kic}", "class_label": class_label,
            "label_positive": label_positive, "weight": 1.0 if class_label == "dsct_flag1" else 7292 / 2314,
            "cluster": sid, "primary_freq": dom, "amp": amp,
            "truth_period_days": (1.0 / dom) if (dom is not None and not math.isnan(dom)) else math.nan,
            "freq_scorable": bool(joined) and bool(label_positive),
            "stratum": "x", "near_saturation": False, "subhour": False,
        }
        if not present:
            row.update({
                "baseline_days": math.nan, "n_exp_zg": math.nan, "n_exp_zr": math.nan,
                "best_pass": None, "best_status": "missing", "best_frequency_per_day": None,
                "low_available": None, "high_available": None,
                "low_status": "missing", "low_frequency_per_day": None, "low_match": "unscored",
                "low_match_primary": "unscored", "low_eligible": False,
                "high_status": "missing", "high_frequency_per_day": None, "high_match": "unscored",
                "high_match_primary": "unscored", "high_eligible": False,
                "best_candidate_matches_any_mode": "unscored",
                "best_candidate_matches_dominant": "unscored",
                "any_top_peak_matches_any_mode": False, "eligible_any_pass": False,
                "census_variable": None, "prov_valid": False,
                "platform_boundary_sensitive": False, "platform_boundary_fields": "",
            })
            return row
        primary = None if (dom is None or math.isnan(dom)) else dom
        any_mode = classify_match(best_freq, truth_list, tol) if truth_list else "unscored"
        dominant = classify_match(best_freq, [primary], tol) if primary is not None else "unscored"
        any_top = bool(truth_list) and any(
            classify_match(f, truth_list, tol) == "direct" for f in peak_list)
        low_el = pass_eligible(truth_list, "low", baseline)
        high_el = pass_eligible(truth_list, "high", baseline)
        row.update({
            "baseline_days": baseline, "n_exp_zg": 1000, "n_exp_zr": 1500,
            "best_pass": "low", "best_status": status, "best_frequency_per_day": best_freq,
            "low_available": True, "high_available": usable_high,
            "low_status": status, "low_frequency_per_day": best_freq, "low_match": any_mode,
            "low_match_primary": dominant, "low_eligible": low_el,
            "high_status": "not_detected", "high_frequency_per_day": best_freq * 3.1,
            "high_match": "unmatched" if truth_list else "unscored",
            "high_match_primary": "unmatched" if primary is not None else "unscored",
            "high_eligible": high_el,
            "best_candidate_matches_any_mode": any_mode,
            "best_candidate_matches_dominant": dominant,
            "any_top_peak_matches_any_mode": any_top,
            "eligible_any_pass": low_el or high_el,
            "census_variable": False, "prov_valid": True,
            "platform_boundary_sensitive": False, "platform_boundary_fields": "",
        })
        return row

    # ---- positives
    for i in range(n_pos):
        kic = 1_000_000 + i
        sid = sid_for(90, i)
        joined = i < n_joined
        if joined:
            # Mo table 2 is the primary record (µHz); every per-day value the
            # world uses is derived from it through the frozen loader's
            # conversion, exactly as the campaign truth is
            dom_uhz = dominant_per_day(i) / UHZ_TO_PER_DAY
            modes_uhz = [dom_uhz, dom_uhz * 1.37, dom_uhz + 0.5 / UHZ_TO_PER_DAY]
            modes = [uhz_to_per_day(x) for x in modes_uhz]
            dom = modes[0]
            for f_uhz, amp in zip(modes_uhz, (1.0, 0.3, 0.1)):
                t2_rows.append({"KIC": kic, "Freq": f_uhz, "Amp": amp})
            amp_mmag = 1.0857
            truth[sid] = modes
            if i < n_aliased:
                t1_rows.append({"KIC": kic, "Freq": dom_uhz, "Amp": 1.0,
                                "fR": 2 * F_NYQ_UHZ - dom_uhz, "C": 0, "SC": -9})
            if i == 0:   # a second qualifying row further away: tie-break by |diff|
                t1_rows.append({"KIC": kic, "Freq": dom_uhz + 0.05, "Amp": 0.5,
                                "fR": 111.0, "C": 0, "SC": -9})
            if i == 1:   # two rows at zero difference: tie-break by minimum fR
                t1_rows.append({"KIC": kic, "Freq": dom_uhz, "Amp": 0.5, "fR": 250.0, "C": 0, "SC": -9})
                t1_rows.append({"KIC": kic, "Freq": dom_uhz, "Amp": 0.5, "fR": 300.0, "C": 0, "SC": -9})
            if i == 45:  # C==1 rows never qualify
                t1_rows.append({"KIC": kic, "Freq": dom_uhz, "Amp": 1.0,
                                "fR": 2 * F_NYQ_UHZ - dom_uhz, "C": 1, "SC": 1})
            if i == 50:  # C==0 but 5 µHz away: not aliased-dominant
                t1_rows.append({"KIC": kic, "Freq": dom_uhz + 5.0, "Amp": 1.0,
                                "fR": 2 * F_NYQ_UHZ - dom_uhz - 5.0, "C": 0, "SC": -9})
        else:
            dom, dom_uhz, amp_mmag, modes = math.nan, math.nan, math.nan, []
            truth[sid] = []
        roster_rows.append({
            "source_id": sid, "external_id": f"KIC {kic}", "ra": 290.0 + i * 0.001, "dec": 40.0,
            "class_label": "dsct_flag1", "label_variable": True, "label_periodic": True,
            "gaia_g_mag": math.nan, "KIC": kic, "gmag": 13.0, "Teff": 7000, "logg": 4.0, "dSct": 1,
            "dom_freq_uhz": dom_uhz, "dom_freq_per_day": dom, "dom_amp_ppt": amp_mmag / 1.0857,
            "amp_mmag": amp_mmag, "subhour": i < n_aliased, "near_saturation": False,
            "stratum": "x", "sampling_weight": 1.0,
        })
        if joined:
            k = i % 10
            usable_high = True
            if k == 0:
                status, best = "missing", None
            elif k in (1, 8):
                status, best = "confirmed", dom
            elif k == 2:
                status, best = "confirmed", 2.0 * dom
            elif k == 3:
                status, best = "confirmed", abs(dom - SIDEREAL)
            elif k == 4:
                status, best = "not_detected", dom + 0.7
            elif k == 5:
                status, best = "candidate", dom * 1.37
            elif k == 6:
                status, best = "confirmed", dom + 0.7
            elif k == 7:
                status, best, usable_high = "confirmed", dom, False
            else:  # k == 9: the Kepler-Nyquist reflection of the dominant
                status, best = "confirmed", 2.0 * F_NYQ_PER_DAY - dom
            peak_list = [] if best is None else [best, best * 0.5 + 0.01]
            if k in (1, 2, 8):
                peak_list.append(dom)
        else:
            usable_high = True
            if i % 7 == 0:
                status, best = "missing", None
            elif i % 5 == 0:
                status, best = "confirmed", 3.3
            else:
                status, best = "not_detected", 4.4
            peak_list = [] if best is None else [best]
        peaks[sid] = peak_list
        ps_rows.append(per_star_row(sid, kic, "dsct_flag1", True, dom, amp_mmag, truth[sid], joined,
                                    status, best, usable_high, peak_list))

    # ---- negatives
    neg_freqs = [1.0, 2.01, 0.5, 10.0, 30.0, 1440.0, 0.1, 0.98, 1.02, 24.0, 3.0]
    for i in range(n_neg):
        kic = 2_000_000 + i
        sid = sid_for(90, 100_000 + i)
        roster_rows.append({
            "source_id": sid, "external_id": f"KIC {kic}", "ra": 291.0, "dec": 41.0 + i * 0.001,
            "class_label": "dsct_flag0", "label_variable": False, "label_periodic": False,
            "gaia_g_mag": math.nan, "KIC": kic, "gmag": 14.5, "Teff": 6800, "logg": 4.1, "dSct": 0,
            "dom_freq_uhz": math.nan, "dom_freq_per_day": math.nan, "dom_amp_ppt": math.nan,
            "amp_mmag": math.nan, "subhour": False, "near_saturation": False,
            "stratum": "negative", "sampling_weight": 7292 / 2314,
        })
        truth[sid] = []
        if i % 40 == 0:
            status, best = "missing", None
        elif i % 25 == 0:
            status, best = "confirmed", neg_freqs[(i // 25) % len(neg_freqs)]
        else:
            status, best = "not_detected", 5.5
        peaks[sid] = [] if best is None else [best]
        ps_rows.append(per_star_row(sid, kic, "dsct_flag0", False, math.nan, math.nan, [], False,
                                    status, best, True, peaks[sid]))

    # ---- flag 2 (excluded class)
    for i in range(n_flag2):
        kic = 3_000_000 + i
        sid = sid_for(90, 200_000 + i)
        roster_rows.append({
            "source_id": sid, "external_id": f"KIC {kic}", "ra": 292.0, "dec": 42.0,
            "class_label": "dsct_flag2", "label_variable": True, "label_periodic": True,
            "gaia_g_mag": math.nan, "KIC": kic, "gmag": 13.5, "Teff": 7100, "logg": 4.0, "dSct": 2,
            "dom_freq_uhz": math.nan, "dom_freq_per_day": math.nan, "dom_amp_ppt": math.nan,
            "amp_mmag": math.nan, "subhour": False, "near_saturation": False,
            "stratum": "flag2", "sampling_weight": 1.0,
        })
        truth[sid] = []
        peaks[sid] = [6.6]
        ps_rows.append(per_star_row(sid, kic, "dsct_flag2", None, math.nan, math.nan, [], False,
                                    "not_detected", 6.6, True, peaks[sid]))

    per_star = pd.DataFrame(ps_rows)
    roster = pd.DataFrame(roster_rows)
    table1 = pd.DataFrame(t1_rows, columns=["KIC", "Freq", "Amp", "fR", "C", "SC"])
    table2 = pd.DataFrame(t2_rows, columns=["KIC", "Freq", "Amp"])

    # ---- synthetic D1 catalog (928 rows)
    d1_rows = []
    d1_freqs = [0.3, 0.99, 1.0, 1.019, 1.02, 2.0, 3.01, 5.0, 12.5, 25.0, 100.0, 1440.0, 2000.0]
    for i in range(928):
        confirmed = i % 9 == 0
        d1_rows.append({
            "source_id": f"{1_000_000_000_000_000_000 + i}",
            "blind_status": "confirmed" if confirmed else ("candidate" if i % 9 == 1 else "not_detected"),
            "best_frequency_per_day": d1_freqs[(i // 9) % len(d1_freqs)] if confirmed else 7.7,
        })
    d1_catalog = pd.DataFrame(d1_rows)
    return World(per_star=per_star, roster=roster, table1=table1, table2=table2, peaks=peaks,
                 truth=truth, d1_catalog=d1_catalog, baseline=baseline)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bundle(world: World, root: Path, pilot: bool = False) -> dict:
    """Write a metrics bundle (per_star.csv, manifest.json, inputs_sha256.json,
    completeness_by_class_pass_rule.csv, chance_match.json), the run's star
    JSONs, the roster, Mo tables and a D1 catalog under root."""
    metrics = root / "metrics"
    stars = root / "run" / "stars"
    data = root / "data"
    for d in (metrics, stars, data):
        d.mkdir(parents=True, exist_ok=True)
    world.per_star.to_csv(metrics / "per_star.csv", index=False)
    inputs = {}
    for r in world.per_star.itertuples(index=False):
        if r.best_status == "missing":
            continue
        result = {
            "schema_version": 3, "source_id": r.sid, "n_exp_zg": 1000, "n_exp_zr": 1500,
            "baseline_days": world.baseline, "complete": True,
            "passes": {
                "low": {"status": r.best_status, "frequency_per_day": r.best_frequency_per_day,
                        "top_peaks": [{"frequency_per_day": f} for f in world.peaks[r.sid]]},
                "high": {"status": "not_detected", "frequency_per_day": None, "top_peaks": []},
            },
        }
        path = stars / f"{r.sid}.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        inputs[f"C:\\fake\\run\\stars\\{r.sid}.json"] = _sha(path)
        inputs[f"C:\\fake\\run\\stars\\{r.sid}.prov.json"] = "0" * 64
    (metrics / "inputs_sha256.json").write_text(json.dumps(inputs, indent=2), encoding="utf-8")
    (metrics / "manifest.json").write_text(
        json.dumps({"dataset": "d3", "pilot": pilot, "confirmatory_allowed": not pilot}),
        encoding="utf-8")
    (metrics / "chance_match.json").write_text(json.dumps({"permutations": 100}), encoding="utf-8")
    pos = world.per_star[world.per_star["class_label"] == "dsct_flag1"]
    n_conf = int((pos["best_status"] == "confirmed").sum())
    usable = pos[(pos["best_status"] != "missing") & (pos["low_available"] == True)  # noqa: E712
                 & (pos["high_available"] == True)]  # noqa: E712
    p2 = usable[usable["freq_scorable"] & usable["eligible_any_pass"]]
    k_direct = int(((p2["best_status"] == "confirmed")
                    & (p2["best_candidate_matches_dominant"] == "direct")).sum())
    completeness = pd.DataFrame([
        {"pass": "best", "rule": "confirmed", "scope": "detection_eligible_roster",
         "n": len(pos), "ess": float(len(pos)), "p": n_conf / len(pos), "lo": 0.0, "hi": 1.0},
        {"pass": "best", "rule": "confirmed", "scope": "freq_recovery_scorable",
         "n": len(p2), "ess": float(len(p2)), "p": (k_direct / len(p2)) if len(p2) else math.nan,
         "lo": 0.0, "hi": 1.0},
        {"pass": "low", "rule": "confirmed", "scope": "detection_eligible_roster",
         "n": len(pos), "ess": float(len(pos)), "p": n_conf / len(pos), "lo": 0.0, "hi": 1.0},
    ])
    completeness.to_csv(metrics / "completeness_by_class_pass_rule.csv", index=False)
    world.roster.to_csv(data / "roster_d3.csv", index=False)
    world.table1.to_csv(data / "mo2026_table1.csv", index=False)
    world.table2.to_csv(data / "mo2026_table2.csv", index=False)
    world.d1_catalog.to_csv(data / "ls_full_catalog.csv", index=False)
    return {
        "metrics": metrics, "stars": stars, "roster": data / "roster_d3.csv",
        "table1": data / "mo2026_table1.csv", "table2": data / "mo2026_table2.csv",
        "d1_catalog": data / "ls_full_catalog.csv", "out": root / "descriptive_postlaunch",
        "n_confirmed_positive": n_conf, "n_p2": int(len(p2)), "k_direct": k_direct,
    }


@pytest.fixture(scope="session")
def d3_world() -> World:
    return build_world()


@pytest.fixture()
def d3_bundle(d3_world, tmp_path) -> dict:
    paths = write_bundle(d3_world, tmp_path)
    paths["world"] = d3_world
    return paths


@pytest.fixture()
def per_star_roundtrip(d3_bundle) -> pd.DataFrame:
    """per_star as the CLIs read it (CSV round trip: NaN/None blanks, object
    boolean columns)."""
    return pd.read_csv(d3_bundle["metrics"] / "per_star.csv", dtype={"sid": str, "cluster": str})
