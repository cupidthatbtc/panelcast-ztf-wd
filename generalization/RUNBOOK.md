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
3. `python -m pytest tests/ -q` (51 tests).
4. `python scripts/generalization/verify_cli_identity.py --shard
   <one published shard> --out-dir outputs/generalization/cli_identity`
   — PASS on the laptop 2026-08-30 (api_equals_cli + deterministic; archived at
   generalization/attestation/laptop_cli_identity_2026-08-30/).

## D3 sequence

1. Fetch (LAPTOP since 2026-08-30 02:20 EDT — moved off the Mac after a reboot
   killed the Mac run at 1,473/3,000; cache tar-piped over Tailscale, launcher
   `d3_fetch_laptop.ps1`, log `d3_fetch.log`): frozen fetcher on `roster_d3.csv` →
   `generalization/data/d3/raw/irsa_cache` (resumable; rerun the same
   command to retry failures until fetch_events shows every target terminal).
2. Panels (LAPTOP — panel gate machine): 
   `python scripts/generalization/build_panels_generic.py
    --roster generalization/data/d3/roster_d3.csv
    --cache-dir <synced irsa_cache> --out-dir outputs/generalization/d3_panels`
3. COMMIT the crossmatch data freeze BEFORE step 4 (zero discretion):
   `python scripts/generalization/d3_crossmatch_adjudicate.py
    --panels-dir outputs/generalization/d3_panels` → commit
   `generalization/data/d3/crossmatch_freeze/` (crossmatch_adjudication.csv:
   dispositions crossmatched_clean / crossmatched_ambiguous [sep ≥ 1.5″ or
   > 1 object in cone] / crossmatched_crowded / not_crossmatched /
   cache_missing / read_error; the frozen chain's `crossmatched` flag is
   never overridden; attrition_by_class.csv; freeze_manifest.json with SHAs)
   together with a copy of crossmatch_qc.csv and shard_index.txt.
4. Timing pilot: `python scripts/generalization/run_generalization_ls.py
    --shard-dir outputs/generalization/d3_panels/exposure_stars
    --shard-index outputs/generalization/d3_panels/shard_index.txt
    --out-dir outputs/generalization/d3_pilot --dataset d3-kepler-dsct
    --limit 150 --work-root C:/ls_scratch/d3_pilot --workers 12
    --replay-report outputs/generalization/replay_gate_full/replay_report.json`
   (`--limit` = lexicographic debug subset, marked pilot; D3 has one arm so
   it is adequate for timing; never confirmatory).
5. Full run: same command without `--limit`, `--out-dir
   outputs/generalization/d3_run --work-root C:/ls_scratch/d3_run`
   (resume-safe: sidecar-bound).
6. Metrics (Mac; `--crossmatch-qc` is REQUIRED for d3 since the G5prep round-2
   compliance repair — mandated attrition table + d3_mo_join_covariates.csv +
   the == 456 guard; the laptop chain's pre-fix metrics are archived
   uninterpreted and the AUTHORITATIVE bundle is the Mac post-fix run, guarded
   by `scripts/generalization/descriptive/compare_metrics_runs.py --reference
   <laptop pre-fix dir> --candidate <mac dir>` → must print GUARD PASS):
   `metrics_generalization.py --dataset d3
    --stars-dir <stars> --run-manifest <d3_run/manifest.json>
    --shards-dir <d3_panels/exposure_stars> --shard-index <d3_panels/shard_index.txt>
    --census-csv <census_generic.csv>
    --crossmatch-qc <crossmatch_qc.csv> --out-dir <metrics>` (completion.csv
    must sit beside the run manifest; sync stars/, manifest.json,
    completion.csv, the panels dir) then
   `plot_generalization.py`.

7. Post-launch descriptive decomposition (AFTER step 6; FULL run only, never
   the pilot; admitted by generalization/reviews/G5prep/sol_diurnal.md):
   `python scripts/generalization/descriptive/d3_trigger_decomposition.py
    --metrics-dir <metrics> --out-dir <results>/descriptive_postlaunch`
   Writes d3_trigger_decomposition.csv + README.md (verbatim disclosure
   sentence) + manifest.json. Arithmetic partition of the frozen rule-1
   best-pass P3 numerator over its unchanged 2,314-star denominator —
   no interval, no veto, no estimand change; never applied to census.

## D2 sequence (laptop, after D3 per slip rule — desktop unreachable)

1. Generation (LAPTOP; all-or-nothing, ~90 s; `<gen>` must not exist;
   gen1 is superseded by gen2 under Amendment 4 — W_g strata):
   `python scripts/generalization/build_d2_shards.py
    --out-dir outputs/generalization/d2_shards_gen2
    --exposure-stars outputs/catalog/2026-08-01_full/exposure_stars
    --arms b,ctrl,a,ladder,phase,ampscale,dropout,cadence_alt,nulls,redilution`
   Mandatory production matrix (Amendments 2+3): arm B nominal 309, arm A
   nominal 309, ladder 824, phase 206, ampscale 206, dropout ≤ 103 (76 on
   the current tables), cadence_alt 33, controls = unique arm-B windows,
   nulls 1,000; plus the stretch `redilution` arm (20 SPOC-verified targets)
   ⇒ 3,102 shards on the current inputs (core ≤ 3,299). The builder refuses
   to publish unless generation_manifest.json says production=true.
2. Self-window diagnostic (DONE on the laptop): frozen fetcher on
   `selfwindow_roster.csv` (96-prefix); usable crossmatches form a separate
   diagnostic arm only.
3. Stratified pilot (LAPTOP; ~150 shards spanning every arm/scenario; never
   confirmatory):
   `python scripts/generalization/run_generalization_ls.py
    --shard-dir outputs/generalization/d2_shards_gen2
    --shard-index outputs/generalization/d2_shards_gen2/shard_index.txt
    --stars-file outputs/generalization/d2_shards_gen2/pilot_shard_index.txt
    --out-dir outputs/generalization/d2_pilot_gen2 --dataset d2-tess-dav
    --work-root C:/ls_scratch/d2_pilot_gen2 --workers 12
    --replay-report outputs/generalization/replay_gate_full/replay_report.json`
   Archive with every pilot record: metrics/, run/manifest.json,
   run/completion.csv, run/stars/ (raw result JSONs AND .prov.json sidecars),
   tests/ (pytest logs from BOTH machines), and a SHA256SUMS covering every
   archived file (`shasum -a 256` over the record; committed).
4. Full run (LAPTOP): the same command WITHOUT `--stars-file` and with
   `--out-dir outputs/generalization/d2_run --work-root C:/ls_scratch/d2_run`
   (resume-safe: sidecar-bound; `--workers 12` — the laptop saturates there).
5. Metrics (laptop or Mac): `python scripts/generalization/metrics_generalization.py
    --dataset d2 --shards-dir <d2_shards_gen2>
    --stars-dir <d2_run/stars> --run-manifest <d2_run/manifest.json>
    --out-dir generalization/results/<date>_d2/metrics`
   (shard index defaults to `<generation>/shard_index.txt`; for a pilot add
   `--stars-file <generation>/pilot_shard_index.txt`; completion.csv must
   sit beside manifest.json).

## Results bundles

`generalization/results/<date>_<dataset>/` mirroring the published
convention: README, DATA_PROVENANCE, SHA256SUMS, acceptance.json, metrics/,
figures/. G5 re-derives every headline number from per_star.csv + JSONs.

## Attested production machine (2026-08-29)

Laptop `Jacks_7i_5090` full-928 replay gate **PASS** (15 workers, 13 h;
921 `identical_v1_schema` + 7 `identical_newline`; python 3.12.12, numpy 2.3.5,
scipy 1.16.3, astropy 8.0.1, pandas 2.3.3, Windows 11). Report on the laptop:
`outputs\generalization\replay_gate_full\replay_report.json` (= the
`--replay-report` argument for every production `run_generalization_ls.py`
invocation); archived copy in
`generalization/attestation/laptop_replay_full_2026-08-29/`.
Mac (M5, macOS arm64) is NOT an attested machine: strict tier fails on bytes
(BLAS/FMA/CSV-parse last-bit), the 928-star decision-equivalence evidence run was
stopped at 311/928 (battery) — partial record in
`outputs/generalization/replay_gate_mac_full/PARTIAL_RUN_ATTESTATION.json`.
Rule: multi-hour compute on the Mac only on mains power; default to the laptop.
