# Campaign runbook — exact commands, no discretion

Every stage runs on a machine that has PASSED the replay gate; every L-S run
requires the attestation flag. Envs: Mac `.venv-gen/bin/python`, laptop
`C:\Users\jcwen\Projects\astro-wd\.venv\Scripts\python.exe`.
Windows detached launches ONLY via WMI:
`Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments
@{CommandLine='cmd.exe /c "cd /d C:\...\astro-wd && <cmd> > log 2> err"'}`
(Start-Process children die with the sshd session).

## Gates (rerun after any env change; artifacts under outputs/generalization)

1. `python scripts/generalization/replay_gate.py --shard-dir <exposure_stars>`
   (25-star; PASS on jacks-7i-5090 2026-08-28; full-928 baseline:
   `--out-dir outputs/generalization/replay_gate_full --count 928`).
2. `python scripts/generalization/panel_golden_gate.py`
   (PASS both machines 2026-08-28).
3. `python -m pytest tests/ -q` (18 tests).
4. `python scripts/generalization/verify_cli_identity.py --shard
   <one published shard> --out-dir outputs/generalization/cli_identity`
   — PENDING; run on the laptop after the full replay frees the cores.

## D3 sequence

1. Fetch (Mac, running): frozen fetcher on `roster_d3.csv` →
   `generalization/data/d3/raw/irsa_cache` (resumable; rerun the same
   command to retry failures until fetch_events shows every target terminal).
2. Panels (LAPTOP — panel gate machine): 
   `python scripts/generalization/build_panels_generic.py
    --roster generalization/data/d3/roster_d3.csv
    --cache-dir <synced irsa_cache> --out-dir outputs/generalization/d3_panels`
3. COMMIT the crossmatch data freeze: crossmatch_qc.csv + an
   adjudication file (any positive with nearest_separation ≥ 1.5″ or
   multiple clusters gets a per-star disposition) BEFORE step 4.
4. Timing pilot: `run_generalization_ls.py --shard-dir <exposure_stars>
    --out-dir outputs/generalization/d3_run --dataset d3-kepler-dsct
    --limit 150 --work-root <local NVMe scratch>
    --replay-report outputs/generalization/replay_gate_full/replay_report.json`
5. Full run: same command without `--limit` (resume-safe: sidecar-bound).
6. Metrics (Mac): `metrics_generalization.py --dataset d3
    --stars-dir <stars> --census-csv <census_generic.csv>
    --crossmatch-qc <crossmatch_qc.csv> --out-dir <metrics>` then
   `plot_generalization.py`.

## D2 sequence (laptop, after D3 per slip rule — desktop unreachable)

1. Shards (LAPTOP): `build_d2_shards.py --out-dir <local shards dir>`
   (arms b,ctrl,a,ladder,nulls; ~2,957 shards; manifest + injected_modes +
   rejected_modes are the truth files).
2. Self-window diagnostic (running): frozen fetcher on
   `selfwindow_roster.csv` (96-prefix); usable crossmatches form a separate
   diagnostic arm only.
3. Run: `run_generalization_ls.py --shard-dir <shards> --dataset d2-tess-dav
    --replay-report <attestation> --work-root <scratch>`.
4. Metrics: `metrics_generalization.py --dataset d2 --shards-dir <shards>
    --stars-dir <stars> --out-dir <metrics>`.

## Results bundles

`generalization/results/<date>_<dataset>/` mirroring the published
convention: README, DATA_PROVENANCE, SHA256SUMS, acceptance.json, metrics/,
figures/. G5 re-derives every headline number from per_star.csv + JSONs.
