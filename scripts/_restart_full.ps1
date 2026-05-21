$pythonw = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\pythonw.exe"
$python  = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\python.exe"
$proj    = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"

# Stop complet
& $python "$proj\start.py" stop 2>&1 | Out-Null
Start-Sleep -Seconds 3

# Pornire tunnel (foloseste named tunnel daca config.yml exista, altfel quick tunnel)
Start-Process $pythonw -ArgumentList "$proj\start.py tunnel" -WorkingDirectory $proj
Write-Host "Pornit. Astept 25s pentru initializare..." -ForegroundColor Cyan
Start-Sleep -Seconds 25

# Verificare porturi
Write-Host "=== Porturi ===" -ForegroundColor Cyan
netstat -aon | findstr ":8000 " | findstr "LISTENING"
netstat -aon | findstr ":5173 " | findstr "LISTENING"

Write-Host "=== Backend HTTP ===" -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "HTTP  OK: $($r.StatusCode)" -ForegroundColor Green
} catch { Write-Host "HTTP  EROARE" -ForegroundColor Red }

Write-Host "=== Backend HTTPS ===" -ForegroundColor Cyan
try {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    $r2 = Invoke-WebRequest -Uri "https://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "HTTPS OK: $($r2.StatusCode)" -ForegroundColor Green
} catch { Write-Host "HTTPS nu raspunde (backend probabil HTTP-only)" -ForegroundColor Yellow }

Write-Host "=== Frontend ===" -ForegroundColor Cyan
try {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    $r3 = Invoke-WebRequest -Uri "https://localhost:5173/" -UseBasicParsing -TimeoutSec 5
    Write-Host "HTTPS :5173 OK: $($r3.StatusCode)" -ForegroundColor Green
} catch {
    try {
        $r4 = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 5
        Write-Host "HTTP  :5173 OK: $($r4.StatusCode) (cert nu e inca in Vite?)" -ForegroundColor Yellow
    } catch { Write-Host "Frontend nu raspunde" -ForegroundColor Red }
}
