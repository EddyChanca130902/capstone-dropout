<#
    Levanta el stack completo en desarrollo:
      - API (FastAPI) en http://localhost:8000
      - Frontend (Angular) en http://localhost:4200
      - Dashboard legacy en Streamlit en http://localhost:8501 (opcional)

    Uso:
      .\scripts\dev.ps1              # API + frontend
      .\scripts\dev.ps1 -Streamlit   # ademas, el dashboard legacy
      .\scripts\dev.ps1 -Tests       # ejecuta pytest y las pruebas del frontend
#>
param(
    [switch]$Streamlit,
    [switch]$Tests
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$python = Join-Path $raiz "dropout-env\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "No se encuentra el entorno virtual: $python" -ForegroundColor Red
    Write-Host "Crealo con: python -m venv dropout-env" -ForegroundColor Yellow
    exit 1
}

if ($Tests) {
    Write-Host "`n=== pytest ===" -ForegroundColor Cyan
    & $python -m pytest -q
    Write-Host "`n=== Angular (vitest) ===" -ForegroundColor Cyan
    Push-Location frontend
    npm test -- --watch=false
    Pop-Location
    exit $LASTEXITCODE
}

Write-Host "`nIniciando la API en http://localhost:8000 (docs en /docs)" -ForegroundColor Green
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "api.main:app", "--reload", "--port", "8000" `
    -WorkingDirectory $raiz -NoNewWindow

Start-Sleep -Seconds 3

Write-Host "Iniciando el frontend en http://localhost:4200" -ForegroundColor Green
Start-Process -FilePath "npm" -ArgumentList "start", "--prefix", "frontend" `
    -WorkingDirectory $raiz -NoNewWindow

if ($Streamlit) {
    Write-Host "Iniciando el dashboard legacy en http://localhost:8501" -ForegroundColor Green
    Start-Process -FilePath $python `
        -ArgumentList "-m", "streamlit", "run", "dashboard/app.py" `
        -WorkingDirectory $raiz -NoNewWindow
}

Write-Host "`nStack en marcha. Ctrl+C para detener este script.`n" -ForegroundColor Cyan
while ($true) { Start-Sleep -Seconds 30 }
