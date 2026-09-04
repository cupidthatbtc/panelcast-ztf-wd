#!/usr/bin/env bash
# HOLDOUT STAGING ONLY (V2_PLAN.md §10, round-7 revision of 2026-09-04): stage the amended
# scripts/v2 code, the final plan, the registered lists, dev_tuning.csv and
# V2_CONSTANTS_FROZEN.json on the laptop, verify digest parity, write the expected digest for
# v2_holdout_laptop.ps1 — and NEVER restart the dev chain. Refuses until the laptop chain has
# logged "V2 DEV RUNS DONE" (a chain restart at the amended digest would delete the
# old-digest dev results for recomputation) and until the constants artifact exists (run
# scripts/v2/analysis/dev_mac_sequence.sh first: it pulls and re-scores the dev runs).
# Retries while the laptop is unreachable (it drops off Tailscale when Jack's VPN is on).
# Usage: nohup bash scripts/v2/analysis/sync_laptop.sh > outputs/v2/sync_laptop.log 2>&1 &
set -uo pipefail
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
ROOT='C:\Users\jcwen\Projects\astro-wd'
for f in generalization/v2/V2_CONSTANTS_FROZEN.json generalization/v2/dev_tuning.csv; do
  [ -f "$f" ] || { echo "$f missing: run dev_mac_sequence.sh (pull + re-score + tuning) first"; exit 1; }
done
MAC=$(.venv-gen/bin/python scripts/v2/analysis/print_digest.py 2>/dev/null | tail -1)
ART=$(.venv-gen/bin/python -c "import json; print(json.load(open('generalization/v2/V2_CONSTANTS_FROZEN.json'))['v2_digest'])")
[ "$ART" = "$MAC" ] || { echo "constants artifact digest $ART != this checkout $MAC: regenerate the artifact"; exit 1; }
for attempt in $(seq 1 400); do
  if ssh -o ConnectTimeout=15 -o BatchMode=yes win "'ok'" > /dev/null 2>&1; then
    if ! ssh -o ConnectTimeout=20 win "Get-Content $ROOT\v2_chain.log -Tail 3" 2>/dev/null | tr -d '\r' | grep -q "V2 DEV RUNS DONE"; then
      echo "$(date '+%FT%T') attempt $attempt: the laptop chain has not logged 'V2 DEV RUNS DONE' — refusing to stage"
      sleep 600; continue
    fi
    scp -o ConnectTimeout=20 -q scripts/v2/*.py win:C:/Users/jcwen/Projects/astro-wd/scripts/v2/ \
      && scp -o ConnectTimeout=20 -q scripts/generalization/frozen_api.py win:C:/Users/jcwen/Projects/astro-wd/scripts/generalization/frozen_api.py \
      && scp -o ConnectTimeout=20 -q scripts/v2/analysis/print_digest.py win:C:/Users/jcwen/Projects/astro-wd/scripts/v2/analysis/print_digest.py \
      && scp -o ConnectTimeout=20 -q generalization/v2/split.csv generalization/v2/*.txt generalization/v2/split_manifest.json \
           generalization/v2/constants_w10.json generalization/v2/V2_PLAN.md generalization/v2/dev_tuning.csv \
           generalization/v2/V2_CONSTANTS_FROZEN.json win:C:/Users/jcwen/Projects/astro-wd/generalization/v2/ \
      && scp -o ConnectTimeout=20 -q scripts/v2/v2_holdout_laptop.ps1 win:C:/Users/jcwen/Projects/astro-wd/v2_holdout_laptop.ps1
    LAP=$(ssh -o ConnectTimeout=20 win "Set-Location $ROOT; .venv\Scripts\python.exe scripts\v2\analysis\print_digest.py" 2>/dev/null | tr -d '\r' | tail -1)
    echo "$(date '+%FT%T') attempt $attempt: mac=$MAC laptop=$LAP"
    if [ "$LAP" = "$MAC" ]; then
      printf '%s\n' "$MAC" > outputs/v2/expected_v2_digest.txt
      scp -o ConnectTimeout=20 -q outputs/v2/expected_v2_digest.txt win:C:/Users/jcwen/Projects/astro-wd/generalization/v2/EXPECTED_V2_DIGEST.txt
      echo "$(date '+%FT%T') PARITY OK — holdout staging complete (no chain restart). Next: git pull on the laptop (dev runs are over), then v2_holdout_laptop.ps1"
      curl -s -m 10 -H "Title: v2 holdout staging" -d "amended code + constants staged on the laptop, digest parity OK ($MAC)" https://ntfy.sh/jack-pings-f594ecfd9ef1a9c2 > /dev/null || true
      exit 0
    fi
  else
    echo "$(date '+%FT%T') attempt $attempt: laptop unreachable"
  fi
  sleep 600
done
echo "$(date '+%FT%T') GAVE UP"
exit 1
