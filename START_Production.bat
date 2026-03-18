@echo off
chcp 65001 >nul 2>&1

title Roland - Command Center (Production)
color 1F
cls

echo.
echo  +======================================================+
echo  :       ROLAND - COMMAND CENTER (PRODUCTION)           :
echo  :       Un singur server, frontend pre-built           :
echo  +======================================================+
echo.

:: Verificare Python
echo  [1/4] Verificare Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [EROARE] Python nu este instalat sau nu e in PATH.
    pause
    exit /b 1
)
echo        OK

:: Build frontend (daca nu exista dist/)
echo  [2/4] Verificare frontend build...
if not exist "%~dp0frontend\dist\index.html" (
    echo        Building frontend...
    pushd "%~dp0frontend"
    call npx vite build
    popd
    if errorlevel 1 (
        echo  [EROARE] Frontend build a esuat.
        pause
        exit /b 1
    )
)
echo        OK

:: Backup DB
echo  [3/4] Backup baza de date...
pushd "%~dp0backend"
python backup.py 2>nul
popd
echo        OK

:: Pornire server (un singur proces)
echo  [4/4] Pornire server...
echo.

cd /d "%~dp0backend"
set PYTHONIOENCODING=utf-8
set TAILSCALE_ORIGIN=https://desktop-cjuecmn.tail7bc485.ts.net:8000

:: Detectare certificate TLS
set CERT_FILE=%~dp0backend\certs\desktop-cjuecmn.tail7bc485.ts.net.crt
set KEY_FILE=%~dp0backend\certs\desktop-cjuecmn.tail7bc485.ts.net.key
set SSL_ARGS=

if exist "%CERT_FILE%" (
    set SSL_ARGS=--ssl-certfile certs\desktop-cjuecmn.tail7bc485.ts.net.crt --ssl-keyfile certs\desktop-cjuecmn.tail7bc485.ts.net.key
    echo  ========================================================
    echo   Server pornit in mod PRODUCTIE (HTTPS)
    echo   Local:       https://localhost:8000
    echo   Tailscale:   https://desktop-cjuecmn.tail7bc485.ts.net:8000
    echo   API Docs:    https://localhost:8000/docs
    echo  ========================================================
    timeout /t 2 /nobreak >nul
    start https://localhost:8000
) else (
    echo  ========================================================
    echo   Server pornit in mod PRODUCTIE (HTTP)
    echo   Aplicatie:   http://localhost:8000
    echo   API Docs:    http://localhost:8000/docs
    echo   [WARN] Certificate TLS nu exista - fara HTTPS
    echo  ========================================================
    timeout /t 2 /nobreak >nul
    start http://localhost:8000
)

python -m uvicorn app.main:app --port 8000 --host 0.0.0.0 --reload --reload-dir app --reload-dir modules %SSL_ARGS%

pause
