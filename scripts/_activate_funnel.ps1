$ts = "C:\Program Files\Tailscale\tailscale.exe"

Write-Host "=== tailscale serve (tailnet HTTPS) ===" -ForegroundColor Cyan
& $ts serve 5173 2>&1

Write-Host "=== tailscale funnel (public internet) ===" -ForegroundColor Cyan
& $ts funnel 5173 2>&1

Write-Host "=== Status final ===" -ForegroundColor Cyan
& $ts funnel status 2>&1
