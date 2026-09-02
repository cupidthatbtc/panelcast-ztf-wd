#!/usr/bin/env bash
# Post-D2 sequence on the MAC (RUNBOOK D2 step 5 + round-2 item 5).
# Usage: bash scripts/generalization/descriptive/d2_mac_sequence.sh [YYYY-MM-DD]
set -euo pipefail
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
DATE="${1:-$(date +%Y-%m-%d)}"
PY=.venv-gen/bin/python
LAP='C:\Users\jcwen\Projects\astro-wd\outputs\generalization'
SYNC=outputs/generalization/d2_sync
MAC_METRICS=outputs/generalization/d2_metrics_mac
RES="generalization/results/${DATE}_d2"
DESC=scripts/generalization/descriptive

echo "== 0. preconditions"
[ -L 'outputs\generalization\replay_gate_full\replay_report.json' ] || { echo "attestation symlink missing"; exit 1; }
ssh win "Get-Content C:\Users\jcwen\Projects\astro-wd\chain2.log -Tail 3" | grep -q "d2 metrics rc=0" || { echo "chain2 has not finished D2 metrics yet"; exit 1; }

echo "== 1. zip on the laptop, pull, unzip (d2_run + d2_shards_gen2 + pre-fix metrics)"
ssh win "Compress-Archive -Force -Path '$LAP\d2_run','$LAP\d2_shards_gen2','$LAP\d2_metrics' -DestinationPath 'C:\Users\jcwen\d2_bundle.zip'; (Get-Item 'C:\Users\jcwen\d2_bundle.zip').Length"
command rm -rf "$SYNC"; mkdir -p "$SYNC"
scp -q win:C:/Users/jcwen/d2_bundle.zip "$SYNC/d2_bundle.zip"
unzip -q "$SYNC/d2_bundle.zip" -d "$SYNC" && command rm "$SYNC/d2_bundle.zip"
echo "results: $(ls "$SYNC/d2_run/stars" | grep -c -v prov)  shards: $(ls "$SYNC/d2_shards_gen2" | grep -c csv.gz)"

echo "== 2. patched metrics on the Mac"
command rm -rf "$MAC_METRICS"
$PY scripts/generalization/metrics_generalization.py --dataset d2 \
  --shards-dir "$SYNC/d2_shards_gen2" --stars-dir "$SYNC/d2_run/stars" \
  --run-manifest "$SYNC/d2_run/manifest.json" --out-dir "$MAC_METRICS"

echo "== 3. ruled guard (laptop pre-fix vs Mac post-fix)"
$PY $DESC/compare_metrics_runs.py --reference "$SYNC/d2_metrics" --candidate "$MAC_METRICS"

echo "== 4. admitted descriptive outputs (item 5)"
OUT="$RES/descriptive_postlaunch"; mkdir -p "$OUT"
$PY $DESC/d2_descriptives.py --metrics-dir "$MAC_METRICS" --shards-dir "$SYNC/d2_shards_gen2" --out-dir "$OUT"

echo "== 5. results bundle skeleton"
mkdir -p "$RES/metrics" "$RES/metrics_laptop_prefix" "$RES/run"
cp -R "$MAC_METRICS"/. "$RES/metrics/"; cp -R "$SYNC/d2_metrics"/. "$RES/metrics_laptop_prefix/"
cp "$SYNC/d2_run/manifest.json" "$SYNC/d2_run/completion.csv" "$SYNC/d2_run/progress.json" "$RES/run/"
cp "$SYNC/d2_shards_gen2/generation_manifest.json" "$SYNC/d2_shards_gen2/shard_manifest.csv" "$SYNC/d2_shards_gen2/injected_modes.csv" "$SYNC/d2_shards_gen2/rejected_modes.csv" "$RES/run/" 2>/dev/null || true
$PY -m pytest tests -q > "$RES/pytest_mac.log" 2>&1 || { echo "tests failed"; exit 1; }
( cd "$RES" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS )
echo "DONE: $RES  (write README.md + DATA_PROVENANCE.md + acceptance.json by hand)"
