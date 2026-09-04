# REGISTERED holdout runs on the laptop (V2_PLAN.md §8) — launch ONLY after: the dev tuning is
# frozen (generalization\v2\dev_tuning.csv + V2_CONSTANTS_FROZEN.json committed and copied here
# byte-identical), the laptop checkout contains the pre-registration commit (git pull after
# CHAIN2 DONE), and scripts\v2\*.py carries the frozen v2 digest. D3 holdout (1,439) then D2
# holdout (696), 12 workers; each creates generalization\v2\HOLDOUT_LAUNCH_<dataset>.json (copy
# both locks back to the Mac checkout and commit them). Resume-safe (exact resume only).
$ErrorActionPreference = "Continue"
$root = "C:\Users\jcwen\Projects\astro-wd"
Set-Location $root
$log = "$root\v2_holdout.log"
$ntfy = "https://ntfy.sh/jack-pings-f594ecfd9ef1a9c2"
function Log($m) { Add-Content $log ("{0} {1}" -f (Get-Date -Format s), $m) }
function Push($t, $m) { try { Invoke-RestMethod -Uri $ntfy -Method Post -Body $m -Headers @{ Title = $t } | Out-Null } catch {} }
if (-not (Test-Path "$root\generalization\v2\V2_CONSTANTS_FROZEN.json")) { Log "no frozen constants artifact"; exit 1 }
$py = "$root\.venv\Scripts\python.exe"
# V2_PLAN.md section 10 (2026-09-04): the holdout runs only after the dev runs are done, at the
# amended digest the Mac holdout staging wrote (the runner re-verifies it against the artifact)
if (-not ((Test-Path "$root\v2_chain.log") -and (Select-String -Path "$root\v2_chain.log" -Pattern "V2 DEV RUNS DONE" -Quiet))) { Log "the dev runs are not done - refusing"; exit 1 }
$expectedFile = "$root\generalization\v2\EXPECTED_V2_DIGEST.txt"
if (-not (Test-Path $expectedFile)) { Log "no EXPECTED_V2_DIGEST.txt (run the Mac holdout staging first)"; exit 1 }
$expected = (Get-Content $expectedFile -Raw).Trim()
$actual = ((& $py "$root\scripts\v2\analysis\print_digest.py" 2>&1) | ForEach-Object { "$_" } | Select-Object -Last 1).Trim()
if ($actual -ne $expected) { Log "digest $actual != expected holdout digest $expected - refusing"; exit 2 }
if ($actual -eq "ecc5df75d8f225cbd364d3c498894ab6dce6bf1aeead89ad1de285d4ee57d33c") { Log "staged code is still the pre-amendment dev-run digest - refusing"; exit 2 }
New-Item -ItemType Directory -Force -Path "$root\outputs\v2", "C:\ls_scratch\v2" | Out-Null
Log "V2 HOLDOUT START (pid $PID) digest $actual"
$split = "$root\generalization\v2\split.csv"
$constants = "$root\generalization\v2\V2_CONSTANTS_FROZEN.json"

function Stage($name, $out, $shards, $index, $stars, $dataset) {
  Log "$name start"
  & $py "$root\scripts\v2\run_v2_ls.py" --shard-dir $shards --shard-index $index --out-dir $out `
    --work-root "C:\ls_scratch\v2" --dataset $dataset --machine "laptop-7i-5090" --workers 12 `
    --stars-file $stars --split-file $split --allow-holdout --constants $constants *> "$out.log"
  $rc = $LASTEXITCODE
  $last = (Get-Content "$out.log" -Tail 1)
  Log "$name rc=$rc :: $last"
  Push "v2 $name rc=$rc" "$last"
  return $rc
}

$failures = 0
if ((Stage "D3 HOLDOUT" "$root\outputs\v2\d3_holdout" "$root\outputs\generalization\d3_panels\exposure_stars" "$root\outputs\generalization\d3_panels\shard_index.txt" "$root\generalization\v2\d3_holdout.txt" "d3-kepler-dsct") -ne 0) { $failures++ }
if ((Stage "D2 HOLDOUT" "$root\outputs\v2\d2_holdout" "$root\outputs\generalization\d2_shards_gen2" "$root\outputs\generalization\d2_shards_gen2\shard_index.txt" "$root\generalization\v2\d2_holdout.txt" "d2-tess-dav") -ne 0) { $failures++ }
Log "V2 HOLDOUT DONE (stages with failures: $failures)"
Push "v2 HOLDOUT DONE" "stages with failures: $failures - pull to the Mac: metrics --engine v2, compare_engines, bundles"
