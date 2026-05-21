$ts = "C:\Program Files\Tailscale\tailscale.exe"

Write-Host "Help serve:" -ForegroundColor Cyan
& $ts serve --help 2>&1 | Select-Object -First 30

Write-Host ""
Write-Host "Incerc serve --bg 5173..." -ForegroundColor Cyan
& $ts serve --bg 5173 2>&1

Write-Host ""
Write-Host "Incerc funnel (daca e activat)..." -ForegroundColor Cyan
& $ts funnel --bg 5173 2>&1

Write-Host ""
Write-Host "Status:" -ForegroundColor Cyan
& $ts serve status 2>&1
& $ts funnel status 2>&1
