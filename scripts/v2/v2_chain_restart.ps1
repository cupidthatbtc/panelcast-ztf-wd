# Stop any running v2_laptop_chain.ps1 (matched from INSIDE this script, excluding this
# process — never kill-by-CommandLine over a bare ssh shell), parse-check the chain under
# the SAME engine WMI launches (Windows PowerShell 5.1), and relaunch it detached.
$root = "C:\Users\jcwen\Projects\astro-wd"
$me = $PID
try {
  [scriptblock]::Create((Get-Content "$root\v2_laptop_chain.ps1" -Raw)) | Out-Null
  "parse ok ($($PSVersionTable.PSVersion))"
} catch {
  "PARSE ERROR: " + $_.Exception.Message
  exit 3
}
# only genuine chain instances: launched by powershell -File …v2_laptop_chain.ps1; never this
# script, never an ssh/pwsh shell whose command line merely mentions the file name
$self = Get-CimInstance Win32_Process -Filter "ProcessId = $me"
$ancestors = @($me, $self.ParentProcessId)
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($ancestors -notcontains $_.ProcessId) -and
  $_.CommandLine -like 'powershell*-File*v2_laptop_chain.ps1*' -and
  $_.CommandLine -notlike '*v2_chain_restart*' -and $_.CommandLine -notlike '*pwsh*'
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "stopped $($_.ProcessId)" }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = "powershell -NoProfile -ExecutionPolicy Bypass -File $root\v2_laptop_chain.ps1" }
"relaunched pid $($r.ProcessId) rc $($r.ReturnValue)"
Start-Sleep 6
Get-Content "$root\v2_chain.log" -Tail 1
