Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

docker compose -f docker-compose.dev.yml up -d db

Write-Host ""
Write-Host "Base de datos de desarrollo levantada." -ForegroundColor Green
Write-Host "Ahora puedes arrancar la app localmente con:" -ForegroundColor Yellow
Write-Host "uvicorn app.main:app --reload" -ForegroundColor Cyan

