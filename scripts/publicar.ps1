<#
    Publica el repositorio en GitHub.

    Uso:
      .\scripts\publicar.ps1 -UrlGitHub "https://github.com/TU-USUARIO/capstone-dropout.git"

    El script:
      1. Comprueba que el working tree esta limpio.
      2. Anade (o actualiza) el remoto `origin`.
      3. Sube la rama `main`.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$UrlGitHub
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$estado = git status --porcelain
if ($estado) {
    Write-Host "Hay cambios sin commitear:" -ForegroundColor Yellow
    $estado | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    $respuesta = Read-Host "Commitearlos antes de publicar? (s/n)"
    if ($respuesta -eq "s") {
        git add -A
        git commit -m "Actualizacion previa al despliegue"
    }
}

if (-not (git remote | Where-Object { $_ -eq "origin" })) {
    git remote add origin $UrlGitHub
    Write-Host "Remoto 'origin' anadido: $UrlGitHub" -ForegroundColor Green
} else {
    git remote set-url origin $UrlGitHub
    Write-Host "Remoto 'origin' actualizado: $UrlGitHub" -ForegroundColor Green
}

git push -u origin main

Write-Host ""
Write-Host "Repositorio publicado." -ForegroundColor Green
Write-Host "  1. API      -> Render (usa render.yaml)  : https://render.com" -ForegroundColor Cyan
Write-Host "  2. Frontend -> Vercel (root: frontend)  : https://vercel.com" -ForegroundColor Cyan
Write-Host "  3. En Vercel define la variable API_URL con la URL de la API." -ForegroundColor Cyan
Write-Host "  4. En Render define CORS_ORIGINS con la URL de Vercel y redespliega." -ForegroundColor Cyan
