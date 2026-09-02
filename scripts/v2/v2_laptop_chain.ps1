# v2 dev runs on the laptop (V2_PLAN.md §5 / §9). Waits for the frozen campaign chain
# (chain2.log "CHAIN2 DONE") so the frozen D2 run is never disturbed, then runs, at 12 workers:
#   D3 dev (defaults) -> D2 dev nulls (defaults) -> D3 dev @ trend window 10 d -> D2 dev nulls @ 10 d
# Holdout runs are launched separately in the registered mode (--allow-holdout) after the
# constants are frozen. Resume-safe: relaunch the same script after a reboot. Launch detached:
#   Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=
#     'powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\jcwen\Projects\astro-wd\v2_laptop_chain.ps1'}
$ErrorActionPreference = "Continue"
$root = "C:\Users\jcwen\Projects\astro-wd"
Set-Location $root
$log = "$root\v2_chain.log"
$ntfy = "https://ntfy.sh/jack-pings-f594ecfd9ef1a9c2"
function Log($m) { Add-Content $log ("{0} {1}" -f (Get-Date -Format s), $m) }
function Push($t, $m) { try { Invoke-RestMethod -Uri $ntfy -Method Post -Body $m -Headers @{ Title = $t } | Out-Null } catch {} }
New-Item -ItemType Directory -Force -Path "$root\outputs\v2", "C:\ls_scratch\v2" | Out-Null
$py = "$root\.venv\Scripts\python.exe"
function AssertDigest($stage) {
  # the admitted v2 runtime digest is shipped by the Mac (scripts/v2/analysis/sync_laptop.sh);
  # every stage refuses to start unless the staged code matches it
  $expectedFile = "$root\generalization\v2\EXPECTED_V2_DIGEST.txt"
  if (-not (Test-Path $expectedFile)) { Log "${stage}: no EXPECTED_V2_DIGEST.txt - refusing"; Push "v2 chain BLOCKED" "${stage}: no expected digest file"; exit 2 }
  $expected = (Get-Content $expectedFile -Raw).Trim()
  $digestOut = & $py "$root\scripts\v2\analysis\print_digest.py" 2>&1
  $actual = ($digestOut | ForEach-Object { "$_" } | Select-Object -Last 1).Trim()
  if ($actual -ne $expected) { Log "${stage}: digest $actual != expected $expected - refusing"; Push "v2 chain BLOCKED" "${stage}: staged code digest differs from the admitted digest"; exit 2 }
  Log "${stage}: digest OK $actual"
}
Log "V2 CHAIN START (pid $PID)"
while (-not (Select-String -Path "$root\chain2.log" -Pattern "CHAIN2 DONE" -Quiet)) { Start-Sleep -Seconds 600 }
Log "chain2 DONE observed"
AssertDigest "pre-flight"
Push "v2 laptop chain" "chain2 DONE - starting the v2 dev runs (D3 dev 1,458 + D2 dev nulls 500, at 30 d and 10 d)"

$d3shards = "$root\outputs\generalization\d3_panels\exposure_stars"
$d3index  = "$root\outputs\generalization\d3_panels\shard_index.txt"
$d2shards = "$root\outputs\generalization\d2_shards_gen2"
$d2index  = "$root\outputs\generalization\d2_shards_gen2\shard_index.txt"
$split    = "$root\generalization\v2\split.csv"

function Stage($name, $out, $shards, $index, $stars, $dataset, $constants) {
  AssertDigest $name
  Log "$name start"
  $a = @("$root\scripts\v2\run_v2_ls.py", "--shard-dir", $shards, "--shard-index", $index,
         "--out-dir", $out, "--work-root", "C:\ls_scratch\v2", "--dataset", $dataset,
         "--machine", "laptop-7i-5090", "--workers", "12", "--stars-file", $stars, "--split-file", $split)
  if ($constants) { $a += @("--constants", $constants) }
  & $py @a *> "$out.log"
  $rc = $LASTEXITCODE
  $last = (Get-Content "$out.log" -Tail 1)
  Log "$name rc=$rc :: $last"
  Push "v2 $name rc=$rc" "$last"
  return $rc
}

$failures = 0
if ((Stage "D3 dev w30" "$root\outputs\v2\d3_dev_w30" $d3shards $d3index "$root\generalization\v2\d3_dev.txt" "d3-kepler-dsct" $null) -ne 0) { $failures++ }
if ((Stage "D2 dev nulls w30" "$root\outputs\v2\d2_dev_w30" $d2shards $d2index "$root\generalization\v2\d2_dev.txt" "d2-tess-dav" $null) -ne 0) { $failures++ }
if ((Stage "D3 dev w10" "$root\outputs\v2\d3_dev_w10" $d3shards $d3index "$root\generalization\v2\d3_dev.txt" "d3-kepler-dsct" "$root\generalization\v2\constants_w10.json") -ne 0) { $failures++ }
if ((Stage "D2 dev nulls w10" "$root\outputs\v2\d2_dev_w10" $d2shards $d2index "$root\generalization\v2\d2_dev.txt" "d2-tess-dav" "$root\generalization\v2\constants_w10.json") -ne 0) { $failures++ }
Log "V2 DEV RUNS DONE (stages with failures: $failures)"
Push "v2 DEV RUNS DONE" "stages with failures: $failures - next: rescore + dev_tuning, freeze constants, registered holdout"
