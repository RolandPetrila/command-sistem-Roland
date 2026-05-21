$token = [System.Environment]::GetEnvironmentVariable('CLOUDFLARE_TUNNEL_TOKEN','User')
if (-not $token) { Write-Host 'TOKEN NOT SET' -ForegroundColor Red; exit 1 }
Write-Host "Token found (len=$($token.Length)), testez cloudflared..." -ForegroundColor Cyan

$cf = 'C:\Tools\cloudflared\cloudflared.exe'
if (-not (Test-Path $cf)) { Write-Host "cloudflared.exe NOT FOUND la $cf" -ForegroundColor Red; exit 1 }

# Porneste tunel in background pt 5 secunde
$p = Start-Process -FilePath $cf -ArgumentList "tunnel", "run", "--token", $token -PassThru -WindowStyle Hidden
Start-Sleep 5
if (-not $p.HasExited) {
    Write-Host "Tunnel PORNIT OK (PID=$($p.Id))" -ForegroundColor Green
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Tunel oprit (test complet)." -ForegroundColor Yellow
} else {
    Write-Host "Tunnel s-a oprit imediat (ExitCode=$($p.ExitCode))" -ForegroundColor Red
}
