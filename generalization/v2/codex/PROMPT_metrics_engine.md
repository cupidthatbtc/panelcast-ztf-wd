# Task: add `--engine v2` to scripts/generalization/metrics_generalization.py (guarded)

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1).
Python: `.venv-gen/bin/python`. Tests: `.venv-gen/bin/python -m pytest tests -q` (143 pass now).
Do NOT commit. Do NOT touch scripts/*.py at the repo's scripts/ top level (frozen, SHA-pinned),
scripts/v2/*, or any file under generalization/ except the report named below.

## Background

The frozen campaign metrics (`metrics_generalization.py`, ~1,860 lines) score per-star JSONs
produced by the frozen driver `scripts/generalization/run_generalization_ls.py`. For d2/d3 they
REQUIRE a run manifest whose `replay_attestation.path` points at a passing replay-gate report,
check `frozen_sha256`, and verify every star's `.prov.json` sidecar against the run manifest
(read `main()` from the line `attestation_record: dict = {"tier": "published_bundle"}` through the
sidecar loop `for key in ("frozen_digest", "campaign_digest", "generation_id"): ...`).

A new detector arm ("v2", `scripts/v2/run_v2_ls.py`, read it) writes the SAME per-star JSON
schema (schema_version "v2-1") and the same sidecars/completion.csv/manifest.json, except:
- `manifest["engine"] == "v2"`, `manifest["replay_attestation"] == {"path": "", "sha256":
  "v2-unattested", "tier": "v2_unattested"}` (there is no replay report to load);
- `manifest["binding"]` = {engine, v2_digest, frozen_digest, constants_sha256, generation_id,
  attestation_sha256 = "v2-unattested"} — NO campaign_digest (deliberate: see the runner's
  docstring); the manifest carries `campaign_sha256_at_start` / `campaign_digest_at_start`
  for audit only;
- each sidecar carries those binding keys plus `engine`, `machine`, `driver = "run_v2_ls.py"`.

## Required change (inside main() only; keep the frozen path byte-for-byte equivalent)

1. `parser.add_argument("--engine", choices=("frozen", "v2"), default="frozen")`.
2. For d2/d3 with `--engine v2`: require `run_manifest.get("engine") == "v2"` (else SystemExit);
   skip loading/validating the replay attestation; set
   `attestation_record = {"tier": "v2_unattested", "path": "", "sha256": "v2-unattested",
   "engine": "v2", "v2_digest": run_manifest["binding"]["v2_digest"],
   "constants_sha256": run_manifest["binding"]["constants_sha256"],
   "machine": run_manifest.get("machine", ""), "roster_size": None,
   "f64_max_relative_difference": None, "boundary_margin_relative": 1e-9,
   "run_manifest_sha256": sha256_file(args.run_manifest)}`; keep the
   `run_manifest.get("frozen_sha256") != frozen_file_shas()` check. With `--engine frozen`
   (default) a manifest whose engine is "v2" must be refused (SystemExit) so the two arms can
   never be mixed; with `--engine v2` a manifest without `engine == "v2"` is refused.
3. Sidecar loop: the attestation check `prov.get("attestation_sha256") !=
   attestation_record.get("sha256")` already works for v2 ("v2-unattested" both sides). Make
   the binding-key tuple engine-dependent: frozen → ("frozen_digest", "campaign_digest",
   "generation_id") exactly as today; v2 → ("engine", "frozen_digest", "v2_digest",
   "constants_sha256", "generation_id"). Also for v2 require `prov.get("driver") ==
   "run_v2_ls.py"`; for frozen keep behaviour unchanged (no new check).
4. Add `"engine": args.engine` to the output `manifest` dict written to manifest.json (frozen
   runs will now carry `"engine": "frozen"` — this is the ONLY allowed change to frozen
   outputs; see the guard below, which permits manifest.json diffs in a whitelist — add
   "engine" to `MANIFEST_MAY_DIFFER` in
   `scripts/generalization/descriptive/compare_metrics_runs.py` as well, and update its
   docstring accordingly; that guard script is also campaign code, so keep the change minimal).
5. Refactor as little as possible; prefer small inline branches. Do not change any computation.

## Guard (mandatory; record the output in the report)

Run the FROZEN metrics with the patched module on the real D3 bundle and compare against the
committed authoritative bundle; it must PASS:

```
.venv-gen/bin/python scripts/generalization/metrics_generalization.py --dataset d3 \
  --stars-dir outputs/generalization/d3_sync/d3_run/stars \
  --run-manifest outputs/generalization/d3_sync/d3_run/manifest.json \
  --shards-dir outputs/generalization/d3_sync/d3_panels/exposure_stars \
  --shard-index outputs/generalization/d3_sync/d3_panels/shard_index.txt \
  --census-csv outputs/generalization/d3_sync/d3_panels/census_generic.csv \
  --crossmatch-qc outputs/generalization/d3_sync/d3_panels/crossmatch_qc.csv \
  --out-dir outputs/generalization/d3_metrics_engine_guard
.venv-gen/bin/python scripts/generalization/descriptive/compare_metrics_runs.py \
  --reference generalization/results/2026-09-02_d3/metrics \
  --candidate outputs/generalization/d3_metrics_engine_guard
```
(The metrics run takes a few minutes. The reference is the committed Mac run; the only expected
manifest differences are campaign_sha256, env, inputs_sha256_count/digest and the new "engine"
key. If the guard fails for any other reason, fix your change, not the guard.)

## Tests to add: `tests/test_v2_metrics_engine.py`

- A synthetic v2 mini-bundle test for the sidecar/manifest binding logic. Because a full d3 CLI
  run needs the real roster + Mo tables, factor the engine-dependent binding into two small
  pure helpers inside metrics_generalization.py, e.g. `attestation_record_for(engine,
  run_manifest, run_manifest_path)` and `sidecar_binding_keys(engine)`, and unit-test them:
  v2 manifest under engine frozen → SystemExit; frozen-style manifest under engine v2 →
  SystemExit; v2 manifest under engine v2 → tier "v2_unattested", sha "v2-unattested", keys
  tuple as specified; frozen keys tuple unchanged.
- A test that `compare_metrics_runs.compare` still PASSES when manifest.json differs only in
  the new "engine" key (mirror the existing tests in tests/test_compare_metrics_runs.py).
- Keep tests/test_compare_metrics_runs.py and all 143 existing tests green.

## Report

Write `generalization/v2/codex/METRICS_ENGINE_REPORT.md`: the unified diff of your changes,
the guard's full output (must include the PASS line), and the final pytest summary line.
