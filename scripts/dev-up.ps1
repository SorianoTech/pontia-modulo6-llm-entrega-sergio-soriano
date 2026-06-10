param(
    [switch]$WithObservability
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$services = @("db")
if ($WithObservability) {
    $services += @("prometheus", "grafana")
}

docker compose -f docker-compose.dev.yml up -d $services

Write-Host ""
Write-Host "Base de datos de desarrollo levantada." -ForegroundColor Green
Write-Host "Ahora puedes arrancar la app localmente con:" -ForegroundColor Yellow
Write-Host "uvicorn app.main:app --reload" -ForegroundColor Cyan

if ($WithObservability) {
    Write-Host "Prometheus disponible en: http://localhost:9090" -ForegroundColor Yellow
    Write-Host "Grafana disponible en: http://localhost:3000 (admin/admin)" -ForegroundColor Yellow
}
