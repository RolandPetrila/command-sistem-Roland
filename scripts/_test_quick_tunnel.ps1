$cf = 'C:\Tools\cloudflared\cloudflared.exe'
Write-Host "cloudflared versiune:" -ForegroundColor Cyan
& $cf --version

Write-Host "`nTest quick tunnel (10 sec)..." -ForegroundColor Cyan
$p = Start-Process -FilePath $cf -ArgumentList "tunnel", "--url", "http://localhost:5173", "--no-autoupdate" -PassThru -WindowStyle Normal -RedirectStandardOutput "$env:TEMP\cf_out.txt" -RedirectStandardError "$env:TEMP\cf_err.txt"

Start-Sleep 10

$out = Get-Content "$env:TEMP\cf_out.txt" -ErrorAction SilentlyContinue
$err = Get-Content "$env:TEMP\cf_err.txt" -ErrorAction SilentlyContinue

$all = @($out) + @($err) | Where-Object { $_ }
$urlLine = $all | Where-Object { $_ -match 'trycloudflare\.com' } | Select-Object -First 1

if ($urlLine) {
    Write-Host "Quick tunnel URL detectat: $urlLine" -ForegroundColor Green
} elseif ($p.HasExited) {
    Write-Host "Cloudflared s-a oprit (ExitCode=$($p.ExitCode))" -ForegroundColor Red
    $all | Select-Object -Last 10 | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "Cloudflared ruleaza dar URL inca nu a aparut in output." -ForegroundColor Yellow
    Write-Host "Output capturat:" -ForegroundColor Yellow
    $all | Select-Object -Last 5 | ForEach-Object { Write-Host $_ }
}

if (-not $p.HasExited) {
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Proces oprit (test complet)." -ForegroundColor Yellow
}
