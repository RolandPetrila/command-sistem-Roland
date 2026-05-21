$ts = "C:\Program Files\Tailscale\tailscale.exe"

# Reset orice config existent
& $ts serve reset 2>&1 | Out-Null
Start-Sleep 2

# Serve background — HTTPS in tailnet (persistent, fara foreground)
Write-Host "Serve --bg (tailnet HTTPS)..." -ForegroundColor Cyan
$r1 = & $ts serve --bg 5173 2>&1
Write-Host $r1

Start-Sleep 1

# Funnel background — HTTPS public internet (persistent)
Write-Host "Funnel --bg (public internet)..." -ForegroundColor Cyan
$r2 = & $ts funnel --bg 5173 2>&1
Write-Host $r2

Start-Sleep 1

# Status final
Write-Host ""
Write-Host "=== STATUS FINAL ===" -ForegroundColor Green
& $ts funnel status 2>&1
