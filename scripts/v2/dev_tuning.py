#!/usr/bin/env python3
"""Dev-half tuning table, the pre-registered selection rule and the frozen
constants artifact (V2_PLAN.md §5).

Inputs: the `rescore_v2.py` tables of BOTH trend-window dev runs for D3
(d3_dev.txt at 30 d and 10 d) and for the D2 dev nulls (d2_dev.txt at 30 d
and 10 d), the frozen D3 per-star table (the frozen P2 frame), the split and
the pre-registration commit. For EVERY one of the 54 combinations
(2 windows x 3 x 3 x 3), on the DEV ids:

  P1_dev  = confirmed fraction, dev flag1 ROSTER (308; missing = 0)
  P2_dev  = confirmed AND dominant direct on the FROZEN P2 frame restricted to
            dev (Mo-joined, freq-scorable, eligible, frozen-usable); a v2
            unavailable / missing result counts as non-recovery
  P3_dev  = confirmed fraction, dev flag0 ROSTER (1,164)
  nulls   = confirmed count among the 500 dev Gaussian nulls
  J       = P2_dev - P3_dev

Assertions (fail-closed): all 54 combinations present; for each, the D3 rows
cover exactly the registered dev runner list and the D2 rows exactly the 500
dev nulls; the denominators equal the roster counts.

Selection: maximize J subject to nulls <= 2 and P1_dev >= P1_dev(default) -
0.05; ties -> the first feasible maximizer in the §3 candidate order (window,
N, phase, ratio); no feasible combination -> the default with
tuning_constraint_failure = true. Output: dev_tuning.csv (evidence) and
V2_CONSTANTS_FROZEN.json bound to the v2 code digest, the split, the plan,
the pre-registration commit and the evidence table.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "generalization"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "v2"))
from metrics_generalization import classify_match  # noqa: E402
from rescore_v2 import combination_id, combinations  # noqa: E402
from v2_common import (  # noqa: E402
    DEFAULT, DEV_RUNS_V2_DIGEST, DEV_RUN_SCHEDULE, TUNABLE, VETO_AMENDMENT_COMMIT, dev_run_record,
    v2_digest, validate_dev_run_records,
)

REGISTRATION = REPO_ROOT / "generalization" / "v2"
DEFAULT_ID = combination_id(DEFAULT)
MAX_DEV_NULLS = 2
P1_SLACK = 0.05
EXPECTED = {"flag1": 308, "flag0": 1164, "nulls": 500}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def verify_dev_run_manifests(paths: list[Path], registration: Path = REGISTRATION) -> list[dict]:
    """Fail-closed provenance of the four dev runs (V2_PLAN.md §10,
    2026-09-04): engine v2, the admitted pre-amendment digest, the dev half,
    no failures, the registered dev list, complete, and exactly the
    (dataset, trend window) schedule of §5. Returns the binding records."""
    records = [dev_run_record(path, registration) for path in paths]   # each verified fail-closed
    return validate_dev_run_records(records, registration)            # exactly the §5 schedule, once each


def verify_rescore_provenance(csv_paths: list[Path], dev_runs: list[dict]) -> None:
    """Every re-score table must carry the sidecar `rescore_v2.py --run-manifest`
    writes, naming one verified dev run as its source (by manifest SHA) with
    THAT run's dataset, trend window and registered-list SHA, the dev-run
    digest as the source digest, THIS checkout's digest as the re-score
    digest, and the table's own bytes; the four tables claim the four runs
    one-to-one."""
    by_sha = {r["sha256"]: r for r in dev_runs}
    claimed: dict[str, Path] = {}
    for path in csv_paths:
        sidecar = path.with_suffix(path.suffix + ".provenance.json")
        if not sidecar.exists():
            raise SystemExit(f"{path}: missing {sidecar.name} (run rescore_v2.py with --run-manifest)")
        prov = json.loads(sidecar.read_text(encoding="utf-8"))
        problems = []
        record = by_sha.get(str(prov.get("run_manifest_sha256")))
        if record is None:
            problems.append("source run manifest is not one of the verified dev runs")
        else:
            if prov.get("dataset") != record["dataset"] or \
                    float(prov.get("trend_window_days", float("nan"))) != float(record["trend_window_days"]):
                problems.append("dataset / trend window differ from the source run's record")
            if prov.get("stars_file_sha256") != record["stars_file_sha256"]:
                problems.append("registered-list SHA differs from the source run's record")
            if record["sha256"] in claimed:
                problems.append(f"source run already claimed by {claimed[record['sha256']].name}")
            claimed[record["sha256"]] = path
        if prov.get("source_v2_digest") != DEV_RUNS_V2_DIGEST:
            problems.append("source digest is not the dev-run digest")
        if prov.get("rescore_v2_digest") != v2_digest():
            problems.append("re-score digest is not this checkout's digest")
        if prov.get("rescore_csv_sha256") != sha256_file(path):
            problems.append("table bytes differ from the provenance record")
        if problems:
            raise SystemExit(f"{path}: re-score provenance rejected: {problems}")
    if set(claimed) != set(by_sha):
        raise SystemExit("the re-score tables do not claim the four verified dev runs one-to-one")


def load_rescores(paths: list[Path]) -> pd.DataFrame:
    frames = [pd.read_csv(p, dtype={"sid": str}) for p in paths]
    table = pd.concat(frames, ignore_index=True)
    if table.duplicated(["combination", "sid"]).any():
        raise SystemExit("duplicate (combination, sid) rows across the rescore tables")
    return table


def d3_table(rescored: pd.DataFrame, frozen: pd.DataFrame, split: pd.DataFrame) -> pd.DataFrame:
    dev = split[(split["dataset"] == "d3") & (split["split"] == "dev")]
    runner = {l.strip() for l in (REGISTRATION / "d3_dev.txt").read_text().splitlines() if l.strip()}
    roster = frozen[frozen["sid"].isin(set(dev["sid"]))].set_index("sid")
    if len(roster) != len(dev):
        raise SystemExit("frozen per-star table does not cover the dev roster")
    frozen_p2 = (roster["class_label"].eq("dsct_flag1") & _bool(roster["freq_scorable"])
                 & _bool(roster["eligible_any_pass"]) & ~roster["best_status"].astype(str).eq("missing")
                 & _bool(roster["low_available"]) & _bool(roster["high_available"]))
    rows = []
    for combo, group in rescored.groupby("combination"):
        got = group.set_index("sid")
        if set(got.index) != runner:
            raise SystemExit(f"{combo}: D3 rescore rows ({len(got)}) != the registered dev runner list ({len(runner)})")
        pos = roster[roster["class_label"] == "dsct_flag1"]
        neg = roster[roster["class_label"] == "dsct_flag0"]
        if len(pos) != EXPECTED["flag1"] or len(neg) != EXPECTED["flag0"]:
            raise SystemExit(f"dev roster counts {len(pos)}/{len(neg)} != expected {EXPECTED}")

        def confirmed(sid: str) -> bool:
            return sid in got.index and str(got.loc[sid, "best_status"]) == "confirmed"

        def recovered(sid: str) -> bool:
            if not confirmed(sid):
                return False
            freq, primary = got.loc[sid, "best_frequency_per_day"], roster.loc[sid, "primary_freq"]
            if pd.isna(freq) or pd.isna(primary):
                return False
            tol = 1.5 / float(got.loc[sid, "baseline_days"])
            return classify_match(float(freq), [float(primary)], tol) == "direct"

        p2_ids = list(roster.index[frozen_p2])
        rows.append({"combination": combo,
                     "P1_dev": sum(confirmed(s) for s in pos.index) / len(pos), "n_P1": len(pos),
                     "P2_dev": (sum(recovered(s) for s in p2_ids) / len(p2_ids)) if p2_ids else math.nan,
                     "n_P2": len(p2_ids),
                     "P3_dev": sum(confirmed(s) for s in neg.index) / len(neg), "n_P3": len(neg)})
    return pd.DataFrame(rows)


def nulls_table(rescored: pd.DataFrame, split: pd.DataFrame) -> pd.DataFrame:
    null_ids = set(split[(split["dataset"] == "d2") & (split["split"] == "dev")
                         & (split["group"] == "gauss_null")]["sid"])
    if len(null_ids) != EXPECTED["nulls"]:
        raise SystemExit("dev nulls != 500 in the split")
    rows = []
    for combo, group in rescored.groupby("combination"):
        if set(group["sid"]) != null_ids:
            raise SystemExit(f"{combo}: D2 rescore rows != the 500 dev nulls")
        rows.append({"combination": combo,
                     "dev_nulls_confirmed": int(group["best_status"].astype(str).eq("confirmed").sum()),
                     "n_nulls": len(group)})
    return pd.DataFrame(rows)


def select(table: pd.DataFrame) -> tuple[pd.DataFrame, str, bool]:
    order = {combo: i for i, (combo, _) in enumerate(combinations())}
    expected = set(order)
    if set(table["combination"]) != expected:
        raise SystemExit(f"combinations present {len(set(table['combination']))} != 54 expected")
    table = table.copy()
    table["order"] = table["combination"].map(order)
    table["J"] = table["P2_dev"] - table["P3_dev"]
    default_p1 = float(table.loc[table["combination"] == DEFAULT_ID, "P1_dev"].iloc[0])
    table["null_ok"] = table["dev_nulls_confirmed"] <= MAX_DEV_NULLS
    table["p1_ok"] = table["P1_dev"] >= default_p1 - P1_SLACK
    table["feasible"] = table["null_ok"] & table["p1_ok"]
    feasible = table[table["feasible"]].sort_values(["J", "order"], ascending=[False, True])
    if feasible.empty:
        chosen, failure = DEFAULT_ID, True
    else:
        best_j = float(feasible["J"].iloc[0])
        chosen = str(feasible[feasible["J"] >= best_j - 1e-12].sort_values("order").iloc[0]["combination"])
        failure = False
    table["chosen"] = table["combination"] == chosen
    return table.sort_values("order"), chosen, failure


def overrides_for(combo: str) -> dict:
    window, n, phi, ratio = combo.split("_")
    return {"trend_window_days": float(window[1:]), "n_window_peaks": int(n[1:]),
            "phase_tolerance_cycles": float(phi[3:]), "amp_ratio": [float(x) for x in ratio[1:].split("-")]}


def verify_commit(commit: str) -> str:
    full = subprocess.run(["git", "rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=REPO_ROOT,
                          capture_output=True, text=True)
    if full.returncode != 0:
        raise SystemExit(f"pre-registration commit {commit} is not in this repository")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", full.stdout.strip(), "HEAD"], cwd=REPO_ROOT)
    if ancestor.returncode != 0:
        raise SystemExit(f"pre-registration commit {commit} is not an ancestor of HEAD")
    return full.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d3-rescore", type=Path, nargs="+", required=True,
                        help="rescore tables of the D3 dev runs (30 d AND 10 d)")
    parser.add_argument("--d2-rescore", type=Path, nargs="+", required=True,
                        help="rescore tables of the D2 dev-null runs (30 d AND 10 d)")
    parser.add_argument("--frozen-per-star", type=Path, required=True, help="frozen D3 metrics per_star.csv")
    parser.add_argument("--split", type=Path, default=REGISTRATION / "split.csv")
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--dev-run-manifests", type=Path, nargs=4, required=True,
                        help="manifest.json of the four dev runs (D3 30 d, D3 10 d, D2 30 d, D2 10 d); "
                             "verified fail-closed against the admitted dev-run digest, the dev half, the "
                             "registered lists and completion; SHA-bound into the artifact (V2_PLAN.md §10)")
    parser.add_argument("--out-dir", type=Path, default=REGISTRATION)
    args = parser.parse_args()

    dev_runs = verify_dev_run_manifests(args.dev_run_manifests)
    verify_rescore_provenance([*args.d3_rescore, *args.d2_rescore], dev_runs)
    split = pd.read_csv(args.split, dtype=str)
    frozen = pd.read_csv(args.frozen_per_star, dtype={"sid": str, "cluster": str})
    d3 = d3_table(load_rescores(args.d3_rescore), frozen, split)
    nulls = nulls_table(load_rescores(args.d2_rescore), split)
    table = d3.merge(nulls, on="combination", how="outer")
    if table.isna().any().any():
        raise SystemExit("D3 and D2 rescore tables do not cover the same combinations")
    table, chosen, failure = select(table)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    evidence = args.out_dir / "dev_tuning.csv"
    table.to_csv(evidence, index=False, lineterminator="\n")
    commit = verify_commit(args.preregistration_commit)
    amendment = verify_commit(VETO_AMENDMENT_COMMIT)
    if subprocess.run(["git", "merge-base", "--is-ancestor", commit, amendment], cwd=REPO_ROOT).returncode != 0:
        raise SystemExit("the pre-registration commit is not an ancestor of the veto amendment commit")
    inputs = {str(p): sha256_file(p) for p in [*args.d3_rescore, *args.d2_rescore, args.frozen_per_star, args.split]}
    artifact = {
        "overrides": overrides_for(chosen),
        "chosen": chosen,
        "tuning_constraint_failure": failure,
        "selection_rule": f"max J = P2_dev - P3_dev s.t. dev nulls <= {MAX_DEV_NULLS} and P1_dev >= P1_dev(default) - {P1_SLACK}; "
                          "ties -> first feasible maximizer in V2_PLAN.md §3 order",
        "v2_digest": v2_digest(),
        "dev_runs_v2_digest": DEV_RUNS_V2_DIGEST,
        "dev_runs": dev_runs,
        "veto_amendment_commit": amendment,
        "split_sha256": sha256_file(args.split),
        "plan_sha256": sha256_file(REGISTRATION / "V2_PLAN.md"),
        "preregistration_commit": commit,
        "tuning_evidence_sha256": sha256_file(evidence),
        "inputs_sha256": inputs,
        "frozen_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (args.out_dir / "V2_CONSTANTS_FROZEN.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(table[["combination", "P1_dev", "P2_dev", "P3_dev", "dev_nulls_confirmed", "J", "feasible", "chosen"]]
              .to_string(index=False))
    print(f"[dev_tuning] chosen {chosen} (constraint failure: {failure}) -> {args.out_dir / 'V2_CONSTANTS_FROZEN.json'}")


if __name__ == "__main__":
    main()
