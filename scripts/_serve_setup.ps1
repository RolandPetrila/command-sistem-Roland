$ts = "C:\Program Files\Tailscale\tailscale.exe"

# Reset config vechi
Write-Host "Reset serve config..." -ForegroundColor Yellow
& $ts serve reset 2>&1

Start-Sleep 2

# Pornire --bg (persistent, nu blocheaza)
Write-Host "Activate serve --bg 5173..." -ForegroundColor Cyan
& $ts serve --bg 5173 2>&1

Start-Sleep 2

# Status
Write-Host ""
Write-Host "=== Serve status ===" -ForegroundColor Cyan
& $ts serve status 2>&1

# Incearca funnel --bg (necesita Funnel activat in cont)
Write-Host ""
Write-Host "=== Incerc funnel --bg ===" -ForegroundColor Cyan
& $ts funnel --bg 5173 2>&1

Write-Host ""
Write-Host "=== Funnel status ===" -ForegroundColor Cyan
& $ts funnel status 2>&1
