@echo off
:: Configurează Roland Command Center să pornească automat la logon
:: Rulează ca Administrator!

chcp 65001 >nul 2>&1
echo.
echo  Configurare auto-start Roland Command Center...
echo.

set SCRIPT_DIR=%~dp0
set TASK_NAME=RolandCommandCenter

:: Verifică drepturi administrator
net session >nul 2>&1
if errorlevel 1 (
    echo  [EROARE] Rulează acest script ca Administrator!
    echo  Click dreapta ^> Run as administrator
    pause
    exit /b 1
)

:: Crează task în Windows Task Scheduler
schtasks /create /tn "%TASK_NAME%" ^
    /tr "cmd /c cd /d \"%SCRIPT_DIR%backend\" && set PYTHONIOENCODING=utf-8 && python -m uvicorn app.main:app --port 8000 --host 0.0.0.0 --reload --reload-dir app --reload-dir modules" ^
    /sc onlogon ^
    /rl highest ^
    /f

if errorlevel 1 (
    echo  [EROARE] Nu s-a putut crea task-ul.
    pause
    exit /b 1
)

echo.
echo  [OK] Auto-start configurat!
echo  Task: %TASK_NAME%
echo  Trigger: la logon
echo  Comanda: uvicorn app.main:app (port 8000)
echo.
echo  Pentru dezactivare: schtasks /delete /tn "%TASK_NAME%" /f
echo.
pause
