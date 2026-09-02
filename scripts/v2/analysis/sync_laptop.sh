#!/usr/bin/env bash
# Re-stage scripts/v2/*.py + generalization/v2/{split,lists,plan,artifacts} on the laptop and
# verify v2 digest parity. Retries until the laptop is reachable (it drops off Tailscale when
# Jack's VPN is on). Usage: nohup bash scripts/v2/analysis/sync_laptop.sh > outputs/v2/sync_laptop.log 2>&1 &
set -uo pipefail
cd /Users/jackneo/Documents/vonhippel-base9/astro-wd
MAC=$(.venv-gen/bin/python -c "import sys; sys.path.insert(0,'scripts/v2'); import v2_common; print(v2_common.v2_digest())" 2>/dev/null | tail -1)
for attempt in $(seq 1 400); do
  if ssh -o ConnectTimeout=15 -o BatchMode=yes win "'ok'" > /dev/null 2>&1; then
    scp -o ConnectTimeout=20 -q scripts/v2/*.py win:C:/Users/jcwen/Projects/astro-wd/scripts/v2/ \
      && scp -o ConnectTimeout=20 -q generalization/v2/split.csv generalization/v2/*.txt generalization/v2/split_manifest.json generalization/v2/constants_w10.json generalization/v2/V2_PLAN.md win:C:/Users/jcwen/Projects/astro-wd/generalization/v2/ \
      && scp -o ConnectTimeout=20 -q scripts/v2/v2_holdout_laptop.ps1 win:C:/Users/jcwen/Projects/astro-wd/v2_holdout_laptop.ps1
    LAP=$(ssh -o ConnectTimeout=20 win "Set-Location C:\Users\jcwen\Projects\astro-wd; .venv\Scripts\python.exe -c \"import sys; sys.path.insert(0,'scripts/v2'); import v2_common; print(v2_common.v2_digest())\"" 2>/dev/null | tr -d '\r' | tail -1)
    echo "$(date '+%FT%T') attempt $attempt: mac=$MAC laptop=$LAP"
    if [ "$LAP" = "$MAC" ]; then
      echo "$(date '+%FT%T') PARITY OK"
      # ship the admitted digest + the digest-gated chain, restart the parked chain
      printf '%s\n' "$MAC" > outputs/v2/expected_v2_digest.txt
      scp -o ConnectTimeout=20 -q outputs/v2/expected_v2_digest.txt win:C:/Users/jcwen/Projects/astro-wd/generalization/v2/EXPECTED_V2_DIGEST.txt
      scp -o ConnectTimeout=20 -q scripts/v2/v2_laptop_chain.ps1 win:C:/Users/jcwen/Projects/astro-wd/v2_laptop_chain.ps1
      scp -o ConnectTimeout=20 -q scripts/v2/v2_chain_restart.ps1 win:C:/Users/jcwen/Projects/astro-wd/v2_chain_restart.ps1
      ssh -o ConnectTimeout=30 win "powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\jcwen\Projects\astro-wd\v2_chain_restart.ps1" 2>/dev/null | tr -d '\r'
      sleep 8
      ssh -o ConnectTimeout=20 win "Get-Content C:\Users\jcwen\Projects\astro-wd\v2_chain.log -Tail 2" 2>/dev/null | tr -d '\r'
      curl -s -m 10 -H "Title: v2 laptop sync" -d "scripts/v2 re-staged on the laptop, digest parity OK ($MAC)" https://ntfy.sh/jack-pings-f594ecfd9ef1a9c2 > /dev/null || true
      exit 0
    fi
  else
    echo "$(date '+%FT%T') attempt $attempt: laptop unreachable"
  fi
  sleep 600
done
echo "$(date '+%FT%T') GAVE UP"
exit 1
