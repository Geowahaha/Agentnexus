import template from '../bridge-install.template.ps1'

export function handleBridgeInstallRequest(request: Request): Response | null {
  const url = new URL(request.url)

  const reconnect = url.searchParams.has('reconnect')
  const forcePair = url.searchParams.has('force')
  const rawCode = url.searchParams.get('code') ?? ''
  const code = reconnect ? '' : rawCode.replace(/\D/g, '').slice(0, 6)
  const apiBase = `${url.protocol}//${url.host}`
  const download = url.searchParams.has('download')

  if (url.pathname === '/bridge/install.cmd') {
    const cmd = buildInstallCmd({ apiBase, code })
    const headers: Record<string, string> = {
      'Content-Type': 'application/octet-stream',
      'Cache-Control': 'no-store',
      'Content-Disposition': 'attachment; filename="Install-AgentNexus-Bridge.cmd"',
    }
    return new Response(cmd, { headers })
  }

  if (url.pathname !== '/bridge/install.ps1') {
    return null
  }

  const solutionContext = url.searchParams.get('solution') || ''
  const script = buildInstallScript({ apiBase, code, forcePair, solutionContext })

  const headers: Record<string, string> = {
    'Content-Type': 'text/plain; charset=utf-8',
    'Cache-Control': 'no-store',
  }
  if (download) {
    headers['Content-Disposition'] = 'attachment; filename="Install-AgentNexus-Bridge.ps1"'
  }

  return new Response(script, { headers })
}

function buildInstallCmd({ apiBase, code }: { apiBase: string; code: string }): string {
  const installUrl = `${apiBase}/bridge/install.ps1?code=${code}`
  const ps1Local = '%TEMP%\\agentnexus-install.ps1'
  return [
    '@echo off',
    'title AgentNexus Bridge Install',
    'echo AgentNexus Bridge - remote support install',
    'echo Do NOT close this window.',
    'echo.',
    'if not exist "%LOCALAPPDATA%\\AgentNexus" mkdir "%LOCALAPPDATA%\\AgentNexus"',
    'if not exist "%LOCALAPPDATA%\\AgentNexus\\bridge" mkdir "%LOCALAPPDATA%\\AgentNexus\\bridge"',
    `powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '${installUrl}' -OutFile '${ps1Local}' -UseBasicParsing } catch { Write-Host 'Download failed:' $_.Exception.Message -ForegroundColor Red; pause; exit 1 }"`,
    `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${ps1Local}"`,
    'if errorlevel 1 echo Install returned an error. Check %LOCALAPPDATA%\\AgentNexus\\bridge-install.log',
    'pause',
  ].join('\r\n')
}

function buildInstallScript({
  apiBase,
  code,
  forcePair,
  solutionContext = '',
}: {
  apiBase: string
  code: string
  forcePair: boolean
  solutionContext?: string
}): string {
  const escapedApi = apiBase.replace(/'/g, "''")
  const escapedCode = code.replace(/'/g, "''")
  const escapedSol = solutionContext.replace(/'/g, "''")
  let script = template
    .replaceAll('__API_BASE__', escapedApi)
    .replaceAll('__PAIRING_CODE__', escapedCode)
    .replaceAll('__FORCE_PAIR__', forcePair ? 'true' : 'false')
  if (escapedSol) {
    script = script.replace('__SOLUTION_CONTEXT__', escapedSol)
  } else {
    script = script.replace('__SOLUTION_CONTEXT__', '')
  }
  return script
}