@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ============================================================
:: START_Roland.bat — Roland Command Center
::
::   Dublu-click                = Pornire sistem
::   START_Roland.bat stop      = Oprire sistem
::   START_Roland.bat build     = Rebuild frontend + pornire
:: ============================================================

:: Log file pentru debug
set LOGFILE=%~dp0roland_start.log
echo [%date% %time%] START_Roland.bat executat > "%LOGFILE%"

:: --- MOD STOP ---
if /i "%~1"=="stop" goto :stop_servers
if /i "%~1"=="/stop" goto :stop_servers

:: --- Detectare mod BUILD ---
set DO_BUILD=0
if /i "%~1"=="build" set DO_BUILD=1
if /i "%~1"=="/build" set DO_BUILD=1

title Roland - Command Center
color 1F
cls

echo.
echo  +======================================================+
echo  :       ROLAND - COMMAND CENTER                        :
echo  +======================================================+
echo.

:: [1] Oprire procese existente
echo  [1/5] Oprire procese vechi...
echo [%time%] Pas 1: Oprire procese >> "%LOGFILE%"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000.*LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173.*LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
:: Oprire agresiva — orice python orphan (single-user machine)
taskkill /f /im python.exe >nul 2>&1
echo        OK

:: [2] Verificare Python
echo  [2/5] Verificare Python...
echo [%time%] Pas 2: Verificare Python >> "%LOGFILE%"
python --version >nul 2>&1
if errorlevel 1 (
    echo  [EROARE] Python nu este instalat!
    echo [%time%] EROARE: Python nu e in PATH >> "%LOGFILE%"
    pause
    exit /b 1
)
echo        OK

:: [3] Build frontend
echo [%time%] Pas 3: Build frontend >> "%LOGFILE%"
if "%DO_BUILD%"=="1" goto :build_frontend
if not exist "%~dp0frontend\dist\index.html" goto :build_frontend
echo  [3/5] Frontend OK — skip build
goto :after_build

:build_frontend
echo  [3/5] Build frontend...
pushd "%~dp0frontend"
call npx vite build >nul 2>&1
if errorlevel 1 (
    echo  [EROARE] Build esuat!
    echo [%time%] EROARE: vite build esuat >> "%LOGFILE%"
    popd
    pause
    exit /b 1
)
popd
echo        OK

:after_build

:: [4] Backup DB
echo  [4/5] Backup DB...
echo [%time%] Pas 4: Backup >> "%LOGFILE%"
if not exist "%~dp0backend\data\backups" mkdir "%~dp0backend\data\backups" 2>nul
if exist "%~dp0backend\data\calculator.db" (
    copy /y "%~dp0backend\data\calculator.db" "%~dp0backend\data\backups\calculator_backup.db" >nul 2>&1
)
echo        OK

:: [5] Pornire backend
echo  [5/5] Pornire server...
echo [%time%] Pas 5: Pornire backend >> "%LOGFILE%"

:: Detectare TLS (fara if imbricat — evita delayed expansion)
set HAS_TLS=0
if exist "%~dp0backend\certs\desktop-cjuecmn.tail7bc485.ts.net.crt" set HAS_TLS=1

:: Curata log backend vechi
set BACKEND_LOG=%~dp0roland_backend.log
del "!BACKEND_LOG!" >nul 2>&1

:: Scrie launcher (cu redirect output in log)
set LAUNCHER=%~dp0backend\_roland_start.cmd
echo @echo off > "!LAUNCHER!"
echo cd /d "%~dp0backend" >> "!LAUNCHER!"
echo set PYTHONIOENCODING=utf-8 >> "!LAUNCHER!"
if "!HAS_TLS!"=="1" (
    echo python -m uvicorn app.main:app --port 8000 --host 0.0.0.0 --ssl-certfile certs\desktop-cjuecmn.tail7bc485.ts.net.crt --ssl-keyfile certs\desktop-cjuecmn.tail7bc485.ts.net.key ^> "!BACKEND_LOG!" 2^>^&1 >> "!LAUNCHER!"
) else (
    echo python -m uvicorn app.main:app --port 8000 --host 0.0.0.0 ^> "!BACKEND_LOG!" 2^>^&1 >> "!LAUNCHER!"
)
echo [%time%] Launcher creat: !LAUNCHER! >> "%LOGFILE%"
echo [%time%] HAS_TLS=!HAS_TLS! >> "%LOGFILE%"

:: Scrie VBS pentru lansare complet ascunsa (fara PowerShell!)
set VBSFILE=%~dp0backend\_roland_hidden.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "!VBSFILE!"
echo WshShell.Run "cmd /c ""!LAUNCHER!""", 0, False >> "!VBSFILE!"

:: Lanseaza backend ASCUNS prin VBS
echo [%time%] Lansare backend cu wscript >> "%LOGFILE%"
wscript "!VBSFILE!"

:: Health check
echo.
echo  Asteptare backend...
set HEALTH_URL=http://127.0.0.1:8000/api/health
if "!HAS_TLS!"=="1" set HEALTH_URL=https://127.0.0.1:8000/api/health
echo [%time%] Health URL: !HEALTH_URL! >> "%LOGFILE%"

set /a ATTEMPTS=0
:healthcheck
set /a ATTEMPTS+=1
if !ATTEMPTS! gtr 60 (
    echo.
    echo  [EROARE] Backend nu a pornit in 60 secunde.
    echo.
    echo  === Ultimele erori din backend ===
    if exist "!BACKEND_LOG!" (
        type "!BACKEND_LOG!"
    ) else (
        echo  [Nu exista log backend]
    )
    echo  ================================
    echo.
    echo  Log startup: %LOGFILE%
    echo  Log backend: !BACKEND_LOG!
    echo [%time%] EROARE: Health check timeout dupa 60s >> "%LOGFILE%"
    pause
    exit /b 1
)
ping -n 2 127.0.0.1 >nul
curl -sk "!HEALTH_URL!" >nul 2>&1
if errorlevel 1 goto healthcheck
echo  Backend OK! (pornit in ~!ATTEMPTS!s)
echo [%time%] Backend pornit OK in ~!ATTEMPTS!s >> "%LOGFILE%"

:: URL browser
set APP_URL=http://localhost:8000
set MODE=HTTP
if "!HAS_TLS!"=="1" (
    set APP_URL=https://desktop-cjuecmn.tail7bc485.ts.net:8000
    set MODE=HTTPS
)

echo.
echo  ========================================================
echo   ROLAND COMMAND CENTER — !MODE!
echo.
echo   Acces:     !APP_URL!
echo   API Docs:  !APP_URL!/docs
echo.
echo   Oprire:    START_Roland.bat stop
echo   Rebuild:   START_Roland.bat build
echo  ========================================================

:: Deschide browser
start "" "!APP_URL!"
echo [%time%] Browser deschis: !APP_URL! >> "%LOGFILE%"

echo.
echo  [OK] Sistem pornit! Fereastra se inchide in 5 secunde.
ping -n 6 127.0.0.1 >nul

:: Curatare fisiere temporare
del "!VBSFILE!" >nul 2>&1
echo [%time%] DONE >> "%LOGFILE%"
endlocal
exit /b 0


:: ============================================================
:: STOP
:: ============================================================
:stop_servers
echo.
echo  Oprire Roland Command Center...
echo.

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000.*LISTENING"') do (
    echo  Oprire PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173.*LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
:: Oprire agresiva — orice python orphan
taskkill /f /im python.exe >nul 2>&1

del "%~dp0backend\_roland_start.cmd" >nul 2>&1
del "%~dp0backend\_roland_hidden.vbs" >nul 2>&1

echo.
echo  [OK] Serverele au fost oprite.
ping -n 4 127.0.0.1 >nul
exit /b 0
