Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

docker compose -f docker-compose.dev.yml down

Write-Host "Entorno de desarrollo detenido." -ForegroundColor Green

