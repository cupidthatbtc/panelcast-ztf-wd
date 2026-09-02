# Stop any running v2_laptop_chain.ps1 (matched from INSIDE this script, excluding this
# process — never kill-by-CommandLine over a bare ssh shell) and relaunch it detached.
$root = "C:\Users\jcwen\Projects\astro-wd"
$me = $PID
Get-CimInstance Win32_Process | Where-Object {
  $_.ProcessId -ne $me -and $_.CommandLine -and $_.CommandLine -like '*v2_laptop_chain.ps1*'
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "stopped $($_.ProcessId)" }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = "powershell -NoProfile -ExecutionPolicy Bypass -File $root\v2_laptop_chain.ps1" }
"relaunched pid $($r.ProcessId) rc $($r.ReturnValue)"
