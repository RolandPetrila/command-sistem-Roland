# Start curat Roland CC si verifica porturile
$pythonw = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\pythonw.exe"
$python  = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\python.exe"
$proj    = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"

# Kill orice ramas pe porturile noastre
"8000","5173" | ForEach-Object {
    $port = $_
    $pids = (netstat -aon | Select-String ":$port .*LISTENING") -replace '.*\s+(\d+)$','$1'
    foreach ($p in $pids) {
        if ($p -match '^\d+$') { taskkill /F /PID $p 2>$null }
    }
}

Start-Sleep -Seconds 2

# Pornire
Start-Process $pythonw -ArgumentList "$proj\start.py tunnel" -WorkingDirectory $proj
Write-Host "Pornit. Astept 20s..." -ForegroundColor Cyan
Start-Sleep -Seconds 20

# Verificare
Write-Host ""
Write-Host "=== Porturi active ===" -ForegroundColor Cyan
netstat -aon | Select-String ":8000 |:5173 " | Select-String "LISTENING"

Write-Host ""
Write-Host "=== Health backend ===" -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "HTTP  :8000 -> $($r.StatusCode)" -ForegroundColor Green
} catch { Write-Host "HTTP  :8000 -> EROARE" -ForegroundColor Red }

try {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    $r2 = Invoke-WebRequest -Uri "https://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "HTTPS :8000 -> $($r2.StatusCode)" -ForegroundColor Green
} catch { Write-Host "HTTPS :8000 -> nu raspunde (poate e HTTP)" -ForegroundColor Yellow }
