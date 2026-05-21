$token = [System.Environment]::GetEnvironmentVariable('CLOUDFLARE_TUNNEL_TOKEN','User')
if (-not $token) { Write-Host 'TOKEN NOT SET' -ForegroundColor Red; exit 1 }
Write-Host "Token found (len=$($token.Length))" -ForegroundColor Cyan

$cf = 'C:\Tools\cloudflared\cloudflared.exe'

# Ruleaza cu output capturat
$result = & $cf tunnel run --token $token 2>&1
Write-Host "--- OUTPUT ---"
$result | ForEach-Object { Write-Host $_ }
Write-Host "--- END ---"
