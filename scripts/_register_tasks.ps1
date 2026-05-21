# Inregistreaza toate Task Scheduler tasks pentru Roland CC
# Ruleaza o singura data dupa setup initial.
$ErrorActionPreference = "Continue"

$pythonw = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\pythonw.exe"
$python  = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\python.exe"
$proj    = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"

Write-Host "Inregistrez tasks Roland CC..." -ForegroundColor Cyan

# ── Task 1: Auto-start la login ────────────────────────────────────────────────
schtasks /Create /TN "RolandCommandCenter" `
    /TR "$pythonw $proj\start.py tunnel" `
    /SC ONLOGON /DELAY 0:30 `
    /RU ALIENWARE /IT /F `
    /RL HIGHEST 2>&1
Write-Host "Task 1 (auto-start): $LASTEXITCODE" -ForegroundColor $(if ($LASTEXITCODE -eq 0) {"Green"} else {"Yellow"})

# ── Task 2: Reinnoire cert Tailscale la fiecare 25 zile ───────────────────────
schtasks /Create /TN "RolandCertRenewal" `
    /TR "$python $proj\scripts\renew_cert.py" `
    /SC DAILY /MO 25 /ST 03:00 `
    /RU ALIENWARE /IT /F 2>&1
Write-Host "Task 2 (cert renewal): $LASTEXITCODE" -ForegroundColor $(if ($LASTEXITCODE -eq 0) {"Green"} else {"Yellow"})

# ── Task 3: Restart watchdog la fiecare ora (failsafe) ────────────────────────
# Verifica daca aplicatia ruleaza, o reporneste daca nu
$checkScript = "$proj\scripts\check_and_restart.ps1"
if (Test-Path $checkScript) {
    schtasks /Create /TN "RolandHealthCheck" `
        /TR "powershell -NoProfile -ExecutionPolicy Bypass -File $checkScript" `
        /SC HOURLY /MO 1 `
        /RU ALIENWARE /IT /F 2>&1
    Write-Host "Task 3 (health check): $LASTEXITCODE" -ForegroundColor $(if ($LASTEXITCODE -eq 0) {"Green"} else {"Yellow"})
}

Write-Host ""
Write-Host "Tasks inregistrate. Verificare:" -ForegroundColor Green
schtasks /Query /TN "RolandCommandCenter" /FO LIST 2>&1 | Select-String "TaskName|Status|Next"
schtasks /Query /TN "RolandCertRenewal" /FO LIST 2>&1 | Select-String "TaskName|Status|Next"
