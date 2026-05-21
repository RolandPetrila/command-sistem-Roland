$cfExe = "C:\Tools\cloudflared\cloudflared.exe"
$cfDir = "C:\Users\ALIENWARE\.cloudflared"

# Creaza folderul daca lipseste
if (-not (Test-Path $cfDir)) {
    New-Item -ItemType Directory -Force -Path $cfDir | Out-Null
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  CLOUDFLARE TUNNEL LOGIN" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "ATENTIE: Vei vedea un URL mai jos." -ForegroundColor Cyan
Write-Host "Copiaza URL-ul si deschide-l IN BROWSER." -ForegroundColor Cyan
Write-Host "Pe pagina Cloudflare care se deschide, da click pe butonul MARE albastru." -ForegroundColor Cyan
Write-Host "NU naviga altundeva pe Cloudflare!" -ForegroundColor Red
Write-Host ""

# Ruleaza si captureaza output-ul pentru URL
$job = Start-Job -ScriptBlock {
    & "C:\Tools\cloudflared\cloudflared.exe" tunnel login 2>&1
}

# Asteapta URL in output (max 15s)
$url = $null
$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline -and -not $url) {
    Start-Sleep -Milliseconds 500
    $output = Receive-Job $job -Keep
    foreach ($line in $output) {
        if ($line -match 'https://dash\.cloudflare\.com/argotunnel\S+') {
            $url = $matches[0]
            break
        }
    }
}

if ($url) {
    Write-Host ""
    Write-Host "URL DE AUTORIZARE:" -ForegroundColor Green
    Write-Host "$url" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host ""
    Write-Host "Deschide URL-ul de mai sus in browser." -ForegroundColor Yellow
    Write-Host "Vei vedea o pagina cu un buton mare albastru 'Authorize'." -ForegroundColor Yellow
    Write-Host "Da click pe el si revino aici." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "Nu am gasit URL in timp. Veri output-ul complet:" -ForegroundColor Yellow
    Receive-Job $job -Keep | ForEach-Object { Write-Host "  $_" }
}

# Asteapta completare
Write-Host "Astept autorizarea..." -ForegroundColor Cyan
$job | Wait-Job | Out-Null
$finalOutput = Receive-Job $job
$finalOutput | ForEach-Object { Write-Host $_ }
Remove-Job $job

Write-Host ""
if (Test-Path "$cfDir\cert.pem") {
    Write-Host "SUCCES! cert.pem salvat. Inchide aceasta fereastra." -ForegroundColor Green
    Write-Host "Ruleaza acum: python scripts/setup_named_tunnel.py" -ForegroundColor Cyan
} else {
    Write-Host "cert.pem inca lipseste." -ForegroundColor Red
    Write-Host "Incearca sa deschizi manual URL-ul de mai sus in browser." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Apasa Enter pentru a inchide..."
Read-Host
