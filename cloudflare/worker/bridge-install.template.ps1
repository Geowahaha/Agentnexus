param(
  [string]$PairingCode = '__PAIRING_CODE__',
  [string]$ApiBase = '__API_BASE__',
  [string]$ForcePair = '__FORCE_PAIR__',
  [string]$SolutionContext = '__SOLUTION_CONTEXT__'
)

$logDir = Join-Path $env:LOCALAPPDATA 'AgentNexus'
$logFile = Join-Path $logDir 'bridge-install.log'
$Root = Join-Path $logDir 'bridge'

try {
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null

  function Log([string]$msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue
    Write-Host $msg
  }

  function Refresh-PathEnv {
    $machine = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
  }

  function Find-NodeExe {
    Refresh-PathEnv
    $cmd = Get-Command node -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
      (Join-Path $env:ProgramFiles 'nodejs\node.exe')
    )
    if (${env:ProgramFiles(x86)}) {
      $candidates += (Join-Path ${env:ProgramFiles(x86)} 'nodejs\node.exe')
    }
    foreach ($candidate in $candidates) {
      if (Test-Path $candidate) { return $candidate }
    }
    return $null
  }

  function Stop-AllBridgeProcesses {
    Set-Location $env:TEMP
    $taskName = 'AgentNexusBridge'
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    $startupVbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'AgentNexusBridge.vbs'
    if (Test-Path $startupVbs) {
      Remove-Item $startupVbs -Force -ErrorAction SilentlyContinue
    }

    $patterns = 'index\.mjs', 'AgentNexus[\\/]bridge', 'AgentNexusBridge'
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
      $cmd = $_.CommandLine
      if (-not $cmd) { return }
      foreach ($pattern in $patterns) {
        if ($cmd -match $pattern) {
          Log "Stopping PID $($_.ProcessId) ($($_.Name))..."
          Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
          break
        }
      }
    }

    Get-Process -Name node -ErrorAction SilentlyContinue | ForEach-Object {
      Log "Stopping node PID $($_.Id)..."
      Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Seconds 2
  }

  function Install-BridgeBundleFromZip([string]$zipPath) {
    Stop-AllBridgeProcesses
    Set-Location $env:TEMP

    $stage = Join-Path $env:TEMP "agentnexus-bridge-stage-$([Guid]::NewGuid().ToString('N'))"
    New-Item -ItemType Directory -Force -Path $stage | Out-Null

    Log 'Extracting bridge bundle to staging folder...'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $stage)

    if (-not (Test-Path (Join-Path $stage 'index.mjs'))) {
      throw 'Bridge bundle incomplete after extract.'
    }
    if (-not (Test-Path (Join-Path $stage 'node_modules\ws\package.json'))) {
      throw 'Bridge bundle missing ws module.'
    }

    $retired = Join-Path $logDir "bridge.retired.$(Get-Date -Format 'yyyyMMddHHmmss')"
    $moved = $false
    for ($attempt = 1; $attempt -le 6; $attempt++) {
      try {
        Stop-AllBridgeProcesses
        if (Test-Path $Root) {
          Log "Retiring previous bridge folder (attempt $attempt)..."
          Move-Item -LiteralPath $Root -Destination $retired -Force -ErrorAction Stop
        }
        Move-Item -LiteralPath $stage -Destination $Root -Force -ErrorAction Stop
        $moved = $true
        break
      } catch {
        Log "Folder swap attempt $attempt failed: $($_.Exception.Message)"
        if ($attempt -eq 6) { throw "Could not replace bridge folder. Close other programs using $Root and run installer again." }
        Start-Sleep -Seconds 2
      }
    }

    if (-not $moved) {
      throw 'Bridge folder swap failed.'
    }

    if (Test-Path $retired) {
      Start-Job -ScriptBlock {
        param($Path)
        Start-Sleep -Seconds 5
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
      } -ArgumentList $retired | Out-Null
    }

    Set-Location $Root
  }

  function Pair-BridgeDevice {
    param(
      [string]$Code,
      [string]$Name,
      [string]$ApiBase,
      [string[]]$Roots
    )
    $pairUrl = "$($ApiBase.TrimEnd('/'))/api/v1/bridge/pair"
    $bodyObj = @{
      code = $Code
      device_name = $Name
      allowed_roots = @($Roots)
      enable_write_execute = $true
      solution_context = if ($SolutionContext) { $SolutionContext } else { $null }
    }
    $bodyJson = $bodyObj | ConvertTo-Json -Compress
    Log "Pair POST $pairUrl (code=$Code, device=$Name)"
    try {
      $response = Invoke-RestMethod -Uri $pairUrl -Method POST `
        -ContentType 'application/json; charset=utf-8' -Body $bodyJson -ErrorAction Stop
    } catch {
      $detail = $_.ErrorDetails.Message
      if (-not $detail) { $detail = $_.Exception.Message }
      throw "Pair failed: $detail"
    }
    $configDir = Join-Path $env:USERPROFILE '.agentnexus'
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null
    $config = [ordered]@{
      api_base = $ApiBase.TrimEnd('/')
      device_id = [string]$response.device_id
      device_name = [string]$response.device_name
      device_token = [string]$response.device_token
      allowed_roots = @($Roots)
      solution_context = if ($SolutionContext) { $SolutionContext } else { $null }
      paired_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    $cfgOut = Join-Path $configDir 'bridge.json'
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($cfgOut, ($config | ConvertTo-Json -Depth 6), $utf8NoBom)
    Log "Paired as $($response.device_name) ($($response.device_id))"
  }

  function Ensure-NodeExe {
    $existing = Find-NodeExe
    if ($existing) { return $existing }
    Log 'Node.js not found - installing via winget (1-2 min)...'
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent | Out-Null
      Start-Sleep -Seconds 8
      Refresh-PathEnv
    }
    $node = Find-NodeExe
    if (-not $node) {
      throw 'Node.js required. Install from https://nodejs.org then run installer again.'
    }
    return $node
  }

  Log '=== AgentNexus bridge install started ==='
  Log "Log file: $logFile"
  Log "Install dir: $Root"

  $configPath = Join-Path $env:USERPROFILE '.agentnexus\bridge.json'
  $skipPair = $false
  $hasFreshCode = ($PairingCode -and $PairingCode.Length -eq 6)

  if ($hasFreshCode -or $ForcePair -eq 'true') {
    if (Test-Path $configPath) {
      $bakPath = "$configPath.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
      Move-Item $configPath $bakPath -Force
      if ($hasFreshCode) {
        Log "Fresh code provided — removed old pairing ($bakPath)."
      } else {
        Log "Force re-pair: moved old config to $bakPath"
      }
    }
  } elseif (Test-Path $configPath) {
    try {
      $existingConfig = Get-Content $configPath -Raw | ConvertFrom-Json
      $existingApi = [string]$existingConfig.api_base
      if ($existingConfig.device_token -and $existingApi -and ($existingApi.TrimEnd('/') -eq $ApiBase.TrimEnd('/'))) {
        $skipPair = $true
        Log 'Existing pairing found — will validate with server before reconnecting.'
      }
    } catch {
      Log 'Could not read existing bridge config — will pair with code if provided.'
    }
  }

  if (-not $skipPair -and (-not $PairingCode -or $PairingCode.Length -ne 6)) {
    throw 'Missing pairing code. Ask your agent for a fresh code (Generate code on /bridge) and run install immediately.'
  }

  Stop-AllBridgeProcesses

  $zipUrl = "$ApiBase/bridge/bridge-bundle.zip"
  $zipFile = Join-Path $env:TEMP 'agentnexus-bridge-bundle.zip'
  Log "Downloading $zipUrl"
  Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing

  if (-not (Test-Path $zipFile)) {
    throw 'Download failed - no zip file.'
  }

  Install-BridgeBundleFromZip $zipFile
  Remove-Item $zipFile -Force -ErrorAction SilentlyContinue

  $node = Ensure-NodeExe
  $deviceName = $env:COMPUTERNAME
  $allowedRoots = $env:USERPROFILE

  if ($skipPair) {
    Log 'Validating existing pairing with server...'
    $probeStdout = Join-Path $logDir 'probe-stdout.log'
    $probeStderr = Join-Path $logDir 'probe-stderr.log'
    $probeProc = Start-Process -FilePath $node `
      -ArgumentList @('index.mjs','probe','--api',$ApiBase) `
      -WorkingDirectory $Root -Wait -PassThru -NoNewWindow `
      -RedirectStandardOutput $probeStdout -RedirectStandardError $probeStderr
    if (Test-Path $probeStdout) { Get-Content $probeStdout | ForEach-Object { Log $_ } }
    if (Test-Path $probeStderr) { Get-Content $probeStderr | ForEach-Object { Log "ERR: $_" } }
    if ($probeProc.ExitCode -ne 0) {
      $skipPair = $false
      if (Test-Path $configPath) {
        $bakPath = "$configPath.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
        Move-Item $configPath $bakPath -Force
        Log "Stale pairing removed ($bakPath). A fresh agent code is required."
      }
      if (-not $PairingCode -or $PairingCode.Length -ne 6) {
        throw 'This PC was paired to an old session. Generate a NEW code on the agent /bridge page and run install with that code.'
      }
    }
  }

  if ($skipPair) {
    $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
    $cfg.allowed_roots = @($allowedRoots)
    $cfg.api_base = $ApiBase
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($configPath, ($cfg | ConvertTo-Json -Depth 6), $utf8NoBom)
    Log "Reconnecting existing device ($($cfg.device_name))..."
  } else {
    Log "Pairing $deviceName with code $PairingCode (codes expire in 30 min — run install right after agent generates code)..."
    Pair-BridgeDevice -Code $PairingCode -Name $deviceName -ApiBase $ApiBase -Roots @($allowedRoots)
  }

  function Register-StartupFallback {
    $startup = [Environment]::GetFolderPath('Startup')
    $vbsPath = Join-Path $startup 'AgentNexusBridge.vbs'
    $connectScript = "Set-Location -LiteralPath '$Root'; & '$node' index.mjs connect --api '$ApiBase'"
    $escaped = $connectScript -replace '"', '""'
    @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command ""$escaped""", 0, False
"@ | Set-Content -Path $vbsPath -Encoding ASCII
    Log "Auto-start fallback: Startup shortcut ($vbsPath)"
  }

  $taskName = 'AgentNexusBridge'
  $startupVbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'AgentNexusBridge.vbs'
  try {
    $connectScript = "Set-Location -LiteralPath '$Root'; & '$node' index.mjs connect --api '$ApiBase'"
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command $connectScript"
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force -ErrorAction Stop | Out-Null
    if (Test-Path $startupVbs) { Remove-Item $startupVbs -Force -ErrorAction SilentlyContinue }
    Log 'Auto-start task registered.'
  } catch {
    Log "Auto-start task skipped: $($_.Exception.Message)"
    Register-StartupFallback
  }

  Start-Process -FilePath $node -ArgumentList @('index.mjs','connect','--api',$ApiBase) -WorkingDirectory $Root -WindowStyle Hidden
  Log 'Bridge connect started — verifying connection...'
  Start-Sleep -Seconds 4
  $verifyStdout = Join-Path $logDir 'verify-stdout.log'
  $verifyStderr = Join-Path $logDir 'verify-stderr.log'
  $verifyProc = Start-Process -FilePath $node `
    -ArgumentList @('index.mjs','probe','--api',$ApiBase) `
    -WorkingDirectory $Root -Wait -PassThru -NoNewWindow `
    -RedirectStandardOutput $verifyStdout -RedirectStandardError $verifyStderr
  if (Test-Path $verifyStdout) { Get-Content $verifyStdout | ForEach-Object { Log $_ } }
  if (Test-Path $verifyStderr) { Get-Content $verifyStderr | ForEach-Object { Log "ERR: $_" } }
  if ($verifyProc.ExitCode -ne 0) {
    throw 'Bridge could not connect to the agent server. Generate a NEW code on /bridge and run install again within 30 minutes.'
  }

  Write-Host ''
  Write-Host 'SUCCESS - this PC is connected!' -ForegroundColor Green
  Write-Host 'Tell your support agent to refresh their dashboard.' -ForegroundColor Green
  Start-Process "$ApiBase/bridge/connected"
} catch {
  $err = $_.Exception.Message
  try {
    Add-Content -Path $logFile -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] FAILED: $err" -ErrorAction SilentlyContinue
  } catch {}
  Write-Host ''
  Write-Host "FAILED: $err" -ForegroundColor Red
  Write-Host "Log: $logFile" -ForegroundColor Yellow
} finally {
  Write-Host ''
  Read-Host 'Press Enter to close this window'
}