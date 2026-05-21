$ts = "C:\Program Files\Tailscale\tailscale.exe"
Write-Host "Serve status:" -ForegroundColor Cyan
& $ts serve status 2>&1

Write-Host ""
Write-Host "Funnel status:" -ForegroundColor Cyan
& $ts funnel status 2>&1
