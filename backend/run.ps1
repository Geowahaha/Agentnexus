Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\python.exe" run.py