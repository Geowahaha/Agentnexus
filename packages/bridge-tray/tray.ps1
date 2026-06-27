# AgentNexus Bridge system tray (Windows) — runs connect in background.
param(
    [string]$ApiBase = "https://agentnexus.mrgeo888.workers.dev"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$bridgeDir = Join-Path (Split-Path $PSScriptRoot -Parent) "bridge"
$bridgeScript = Join-Path $bridgeDir "index.mjs"
$node = (Get-Command node -ErrorAction Stop).Source

$proc = Start-Process -FilePath $node -ArgumentList "`"$bridgeScript`" connect --api `"$ApiBase`"" `
    -WorkingDirectory $bridgeDir -WindowStyle Hidden -PassThru

$icon = New-Object System.Windows.Forms.NotifyIcon
$icon.Icon = [System.Drawing.SystemIcons]::Shield
$icon.Text = "AgentNexus Bridge"
$icon.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip
$statusItem = $menu.Items.Add("Status: connecting...")
$openItem = $menu.Items.Add("Open AgentNexus")
$quitItem = $menu.Items.Add("Quit")

$openItem.Add_Click({
    Start-Process "$ApiBase/bridge"
})

$quitItem.Add_Click({
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    $icon.Visible = $false
    $icon.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

$icon.ContextMenuStrip = $menu
$icon.Add_DoubleClick({ Start-Process "$ApiBase/bridge" })

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 5000
$timer.Add_Tick({
    if ($proc.HasExited) {
        $statusItem.Text = "Status: disconnected (restarting...)"
        $script:proc = Start-Process -FilePath $node -ArgumentList "`"$bridgeScript`" connect --api `"$ApiBase`"" `
            -WorkingDirectory $bridgeDir -WindowStyle Hidden -PassThru
    } else {
        $statusItem.Text = "Status: online (PID $($proc.Id))"
    }
})
$timer.Start()

[System.Windows.Forms.Application]::Run()
$timer.Stop()
$icon.Dispose()