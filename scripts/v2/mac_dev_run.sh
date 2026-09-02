#!/usr/bin/env bash
# Mac dev-half v2 runs (V2_PLAN.md §9): D3 dev (1,458) then D2 dev (762), 8 workers.
# Waits for mains power (RUNBOOK rule: multi-hour Mac compute only on AC), keeps the
# machine awake with caffeinate, pings ntfy at every stage, and is resume-safe
# (rerun the same command after an interruption). Usage:
#   nohup bash scripts/v2/mac_dev_run.sh [constants-json-or-''] [suffix] > outputs/v2/mac_dev_run.log 2>&1 &
set -uo pipefail
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
PY=.venv-gen/bin/python
CONSTANTS="${1:-}"
SUFFIX="${2:-}"
NTFY=https://ntfy.sh/jack-pings-f594ecfd9ef1a9c2
D3_SHARDS=outputs/generalization/d3_sync/d3_panels/exposure_stars
D3_INDEX=outputs/generalization/d3_sync/d3_panels/shard_index.txt
D2_SHARDS=outputs/generalization/d2_shards_gen2_sync
D2_INDEX=$D2_SHARDS/shard_index.txt
OUT_D3=outputs/v2/d3_dev${SUFFIX}
OUT_D2=outputs/v2/d2_dev${SUFFIX}
WORK=outputs/v2/work${SUFFIX}
mkdir -p outputs/v2 "$WORK"

ping() { curl -s -m 10 -H "Title: v2 dev run" -d "$1" "$NTFY" > /dev/null || true; }
stamp() { date "+%Y-%m-%dT%H:%M:%S"; }

echo "$(stamp) waiting for AC power"
while ! pmset -g batt | grep -q "AC Power"; do sleep 120; done
echo "$(stamp) on AC power — starting"
ping "v2 dev run starting on the Mac (D3 dev 1,458 then D2 dev 762)${SUFFIX:+ [$SUFFIX]}"

EXTRA=()
if [ -n "$CONSTANTS" ]; then EXTRA=(--constants "$CONSTANTS"); fi

run_stage() {  # name out shards index stars dataset
  local name=$1 out=$2 shards=$3 index=$4 stars=$5 dataset=$6
  echo "$(stamp) $name start"
  caffeinate -i $PY scripts/v2/run_v2_ls.py --shard-dir "$shards" --shard-index "$index" \
    --out-dir "$out" --work-root "$WORK" --dataset "$dataset" --machine mac-m5 --workers 8 \
    --stars-file "$stars" --split-file generalization/v2/split.csv "${EXTRA[@]}" \
    > "$out.log" 2>&1
  local rc=$?
  echo "$(stamp) $name rc=$rc ($(tail -1 "$out.log"))"
  ping "v2 $name rc=$rc: $(tail -1 "$out.log")"
  return $rc
}

run_stage "D3 dev" "$OUT_D3" "$D3_SHARDS" "$D3_INDEX" generalization/v2/d3_dev.txt d3-kepler-dsct || exit 1
run_stage "D2 dev" "$OUT_D2" "$D2_SHARDS" "$D2_INDEX" generalization/v2/d2_dev.txt d2-tess-dav || exit 1
echo "$(stamp) MAC DEV DONE"
ping "v2 MAC DEV DONE — both dev halves complete"
