$accountId = [System.Environment]::GetEnvironmentVariable('CLOUDFLARE_ACCOUNT_ID','User')
$apiToken  = [System.Environment]::GetEnvironmentVariable('CLOUDFLARE_API_TOKEN','User')

if ($accountId) { Write-Host "CLOUDFLARE_ACCOUNT_ID: SET (len=$($accountId.Length))" -ForegroundColor Green }
else            { Write-Host "CLOUDFLARE_ACCOUNT_ID: NOT SET" -ForegroundColor Red }

if ($apiToken)  { Write-Host "CLOUDFLARE_API_TOKEN:  SET (len=$($apiToken.Length))" -ForegroundColor Green }
else            { Write-Host "CLOUDFLARE_API_TOKEN:  NOT SET" -ForegroundColor Red }
