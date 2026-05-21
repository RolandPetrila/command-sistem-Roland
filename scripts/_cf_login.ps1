$cfDir = "C:\Users\ALIENWARE\.cloudflared"
$cfExe = "C:\Tools\cloudflared\cloudflared.exe"

# Creaza folderul daca lipseste
if (-not (Test-Path $cfDir)) {
    New-Item -ItemType Directory -Force -Path $cfDir | Out-Null
    Write-Host "Folder .cloudflared creat." -ForegroundColor Green
}

Write-Host "Deschid browserul pentru login Cloudflare..." -ForegroundColor Cyan
Write-Host "Autorizeaza in browser, apoi astept..." -ForegroundColor Yellow
Write-Host ""

& $cfExe tunnel login

if (Test-Path "$cfDir\cert.pem") {
    Write-Host ""
    Write-Host "OK -- Login complet! cert.pem salvat." -ForegroundColor Green
    Write-Host "Rulam acum setup_named_tunnel.py..." -ForegroundColor Cyan
    & "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\python.exe" `
        "C:\Proiecte\NOU_Calculator_Pret_Traduceri\scripts\setup_named_tunnel.py"
} else {
    Write-Host ""
    Write-Host "[WARN] cert.pem inca lipseste dupa login." -ForegroundColor Yellow
    Write-Host "Cauta fisierul cert.pem in Downloads si copiaza-l la:" -ForegroundColor Yellow
    Write-Host "  $cfDir\cert.pem" -ForegroundColor White
}
Write-Host "Apasa Enter..." -NoNewline
Read-Host
