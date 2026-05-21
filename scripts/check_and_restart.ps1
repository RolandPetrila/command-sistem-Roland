# Rulat orar de Task Scheduler — verifica daca Roland CC e activ, reporneste daca nu
$pythonw = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\pythonw.exe"
$proj    = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"
$logFile = Join-Path $proj "logs\healthcheck.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    $line | Out-File -FilePath $logFile -Append -Encoding utf8
}

# Verifica daca backend-ul e up
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Log "OK -- backend activ"
        exit 0
    }
} catch {
    Log "WARN -- backend nu raspunde: $_"
}

# Backend nu e up -- reporneste
Log "RESTART -- pornesc Roland CC..."
& $pythonw "$proj\start.py" tunnel
Log "RESTART -- comanda trimisa"
