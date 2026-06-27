@echo off
setlocal

if "%~1"=="" (
  echo Usage: %~nx0 https://example.com [--markdown]
  echo Example JSON: %~nx0 https://example.com
  echo Example Markdown: %~nx0 https://example.com --markdown
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
node "%SCRIPT_DIR%audit_ai_visibility.mjs" %*
exit /b %ERRORLEVEL%
