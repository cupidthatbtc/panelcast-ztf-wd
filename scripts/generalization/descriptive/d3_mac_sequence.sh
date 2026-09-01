#!/usr/bin/env bash
# Post-D3 sequence on the MAC (RUNBOOK steps 6–7 + G5prep round-2 outputs).
# Usage: bash scripts/generalization/descriptive/d3_mac_sequence.sh [YYYY-MM-DD]
# Stages: (1) zip + pull the laptop's d3_run / d3_panels / pre-fix metrics;
# (2) run the PATCHED metrics here; (3) ruled guard vs the laptop pre-fix run;
# (4) the nine admitted descriptive CLIs; (5) results-bundle skeleton + sums.
# Fail-closed at every stage. Never pulls git on the laptop.
set -euo pipefail
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
DATE="${1:-$(date +%Y-%m-%d)}"
PY=.venv-gen/bin/python
LAP='C:\Users\jcwen\Projects\astro-wd\outputs\generalization'
SYNC=outputs/generalization/d3_sync
MAC_METRICS=outputs/generalization/d3_metrics_mac
RES="generalization/results/${DATE}_d3"
DESC=scripts/generalization/descriptive

echo "== 0. preconditions"
[ -L 'outputs\generalization\replay_gate_full\replay_report.json' ] || { echo "attestation symlink missing (RUNBOOK step 6)"; exit 1; }
ssh win "Get-Content $LAP\..\..\chain2.log -Tail 3" | grep -q "d3 metrics rc=0" || { echo "chain2 has not finished D3 metrics yet"; exit 1; }

echo "== 1. zip on the laptop, pull, unzip"
ssh win "Compress-Archive -Force -Path '$LAP\d3_run','$LAP\d3_panels','$LAP\d3_metrics','$LAP\d3_metrics_descriptive_postlaunch' -DestinationPath 'C:\Users\jcwen\d3_bundle.zip'; (Get-Item 'C:\Users\jcwen\d3_bundle.zip').Length"
command rm -rf "$SYNC"; mkdir -p "$SYNC"
scp -q win:C:/Users/jcwen/d3_bundle.zip "$SYNC/d3_bundle.zip"
unzip -q "$SYNC/d3_bundle.zip" -d "$SYNC" && command rm "$SYNC/d3_bundle.zip"
echo "stars: $(ls "$SYNC/d3_run/stars" | grep -c -v prov) results, $(ls "$SYNC/d3_run/stars" | grep -c prov) sidecars"

echo "== 2. patched metrics on the Mac"
command rm -rf "$MAC_METRICS"
$PY scripts/generalization/metrics_generalization.py --dataset d3 \
  --stars-dir "$SYNC/d3_run/stars" --run-manifest "$SYNC/d3_run/manifest.json" \
  --shards-dir "$SYNC/d3_panels/exposure_stars" --shard-index "$SYNC/d3_panels/shard_index.txt" \
  --census-csv "$SYNC/d3_panels/census_generic.csv" --crossmatch-qc "$SYNC/d3_panels/crossmatch_qc.csv" \
  --out-dir "$MAC_METRICS"

echo "== 3. ruled guard (laptop pre-fix vs Mac post-fix)"
$PY $DESC/compare_metrics_runs.py --reference "$SYNC/d3_metrics" --candidate "$MAC_METRICS"

echo "== 4. admitted descriptive outputs"
OUT="$RES/descriptive_postlaunch"; mkdir -p "$OUT"
$PY $DESC/d3_trigger_decomposition.py --metrics-dir "$MAC_METRICS" --out-dir "$OUT"
$PY $DESC/d3_truth_provenance.py     --metrics-dir "$MAC_METRICS" --stars-dir "$SYNC/d3_run/stars" --out-dir "$OUT"
$PY $DESC/d3_positive_partition.py   --metrics-dir "$MAC_METRICS" --out-dir "$OUT"
$PY $DESC/d3_chance_dominant.py      --metrics-dir "$MAC_METRICS" --out-dir "$OUT"
$PY $DESC/d3_frequency_audits.py     --metrics-dir "$MAC_METRICS" --out-dir "$OUT"
$PY $DESC/d3_strata_covariates.py    --metrics-dir "$MAC_METRICS" --out-dir "$OUT"
$PY $DESC/d3_coverage_a95.py         --metrics-dir "$MAC_METRICS" --stars-dir "$SYNC/d3_run/stars" --out-dir "$OUT"

echo "== 5. results bundle skeleton"
mkdir -p "$RES/metrics" "$RES/metrics_laptop_prefix" "$RES/run"
cp -R "$MAC_METRICS"/. "$RES/metrics/"
cp -R "$SYNC/d3_metrics"/. "$RES/metrics_laptop_prefix/"
cp "$SYNC/d3_run/manifest.json" "$SYNC/d3_run/completion.csv" "$SYNC/d3_run/progress.json" "$RES/run/"
$PY -m pytest tests -q > "$RES/pytest_mac.log" 2>&1 || { echo "tests failed — see $RES/pytest_mac.log"; exit 1; }
( cd "$RES" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS )
echo "DONE: $RES  (write README.md + DATA_PROVENANCE.md + acceptance.json by hand; raw stars stay in $SYNC)"
