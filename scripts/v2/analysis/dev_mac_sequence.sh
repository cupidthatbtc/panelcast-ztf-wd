#!/usr/bin/env bash
# Post-dev sequence on the MAC (V2_PLAN.md §5): pull the four laptop dev runs
# (D3 dev @30 d/@10 d, D2 dev nulls @30 d/@10 d), re-score each exactly for the
# 27 decision-constant combinations, run the selector, and emit the bound
# constants artifact. Light CPU (JSON parsing only). Usage:
#   bash scripts/v2/analysis/dev_mac_sequence.sh <preregistration-commit>
set -euo pipefail
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
COMMIT="${1:?pre-registration commit required (e.g. 5ceb019)}"
PY=.venv-gen/bin/python
LAP='C:\Users\jcwen\Projects\astro-wd\outputs\v2'
SYNC=outputs/v2/dev_sync
TUNE=outputs/v2/tuning

echo "== 0. preconditions"
ssh win "Get-Content C:\Users\jcwen\Projects\astro-wd\v2_chain.log -Tail 1" | tr -d '\r' | grep -q "V2 DEV RUNS DONE" \
  || { echo "the laptop v2 chain has not logged 'V2 DEV RUNS DONE'"; exit 1; }
for run in d3_dev_w30 d2_dev_w30 d3_dev_w10 d2_dev_w10; do
  ssh win "Get-Content $LAP\\$run.log -Tail 1" | tr -d '\r' | grep -q "done: " || { echo "$run did not finish cleanly"; exit 1; }
done

echo "== 1. zip on the laptop, pull, unzip"
ssh win "Compress-Archive -Force -Path '$LAP\d3_dev_w30','$LAP\d2_dev_w30','$LAP\d3_dev_w10','$LAP\d2_dev_w10' -DestinationPath 'C:\Users\jcwen\v2_dev.zip'; (Get-Item 'C:\Users\jcwen\v2_dev.zip').Length"
command rm -rf "$SYNC"; mkdir -p "$SYNC"
scp -q win:C:/Users/jcwen/v2_dev.zip "$SYNC/v2_dev.zip"
unzip -q "$SYNC/v2_dev.zip" -d "$SYNC" && command rm "$SYNC/v2_dev.zip"
for run in d3_dev_w30 d2_dev_w30 d3_dev_w10 d2_dev_w10; do
  echo "$run: $(ls "$SYNC/$run/stars" | grep -c -v prov) results, $(grep -c ',complete,' "$SYNC/$run/completion.csv") complete"
done

echo "== 2. digest parity: every dev run must carry the admitted pre-amendment digest (V2_PLAN §10, 2026-09-04)"
# The dev runs were produced at the round-6 digest; the veto amendment of 2026-09-04 changed the
# code digest and is applied to them by EXACT offline re-scoring (rescore reproduces 1,065/1,065
# run decisions with the pre-amendment code). The holdout runs use this checkout's digest.
DEV_RUN_DIGEST=ecc5df75d8f225cbd364d3c498894ab6dce6bf1aeead89ad1de285d4ee57d33c
DIGEST=$($PY scripts/v2/analysis/print_digest.py 2>/dev/null | tail -1)
echo "dev-run digest ${DEV_RUN_DIGEST:0:12}…  this checkout ${DIGEST:0:12}…"
for run in d3_dev_w30 d2_dev_w30 d3_dev_w10 d2_dev_w10; do
  $PY - "$SYNC/$run/manifest.json" "$DEV_RUN_DIGEST" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))
assert m["engine"] == "v2" and m["binding"]["v2_digest"] == sys.argv[2], (sys.argv[1], m["binding"]["v2_digest"][:12], sys.argv[2][:12])
assert m["split"]["half"] == "dev" and not m["failures"], (m["split"], m["failures"])
print(sys.argv[1], "ok", m["constants"]["trend_window_days"], "d", m["completed_now"], "completed")
EOF
done

echo "== 3. exact re-score (27 combinations per run; provenance sidecar beside each table)"
mkdir -p "$TUNE"
for run in d3_dev_w30 d2_dev_w30 d3_dev_w10 d2_dev_w10; do
  $PY scripts/v2/rescore_v2.py --stars-dir "$SYNC/$run/stars" --run-manifest "$SYNC/$run/manifest.json" --out "$TUNE/rescore_$run.csv"
done

echo "== 4. selector -> generalization/v2/dev_tuning.csv + V2_CONSTANTS_FROZEN.json (fail-closed on the four dev manifests)"
$PY scripts/v2/dev_tuning.py --d3-rescore "$TUNE/rescore_d3_dev_w30.csv" "$TUNE/rescore_d3_dev_w10.csv" \
  --d2-rescore "$TUNE/rescore_d2_dev_w30.csv" "$TUNE/rescore_d2_dev_w10.csv" \
  --dev-run-manifests "$SYNC/d3_dev_w30/manifest.json" "$SYNC/d3_dev_w10/manifest.json" "$SYNC/d2_dev_w30/manifest.json" "$SYNC/d2_dev_w10/manifest.json" \
  --frozen-per-star generalization/results/2026-09-02_d3/metrics/per_star.csv \
  --preregistration-commit "$COMMIT"
cat <<'MSG'
DONE. Next, in this order (plan_sha256 is bound into the artifact):
  1. read generalization/v2/dev_tuning.csv and the chosen combination;
  2. write the §10 tuning entry in V2_PLAN.md (chosen combination, constraint status);
  3. RE-RUN step 4 exactly as above so the artifact binds the final plan;
  4. commit dev_tuning.csv + V2_CONSTANTS_FROZEN.json + V2_PLAN.md;
  5. bash scripts/v2/analysis/sync_laptop.sh   (holdout staging; refuses before 'V2 DEV RUNS DONE'; no chain restart);
  6. on the laptop: git pull (dev runs are over), then v2_holdout_laptop.ps1 (registered, once).
Never run metrics_generalization on the old-digest dev outputs as amended-veto metrics; only the re-score tables carry the amended veto.
MSG
