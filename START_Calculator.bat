@echo off
chcp 65001 >nul 2>&1

title Calculator Pret Traduceri
color 1F
cls

echo.
echo  +======================================================+
echo  :       CALCULATOR PRET TRADUCERI                      :
echo  :       Sistem automat de estimare preturi             :
echo  :       pentru traduceri tehnice EN / RO               :
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

:: Verificare Node.js
echo  [2/4] Verificare Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo  [EROARE] Node.js nu este instalat sau nu e in PATH.
    pause
    exit /b 1
)
echo        OK

:: Verificare dependente
echo  [3/4] Verificare dependente...
python -c "import fastapi; import uvicorn; import fitz; import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo        Instalare pachete Python...
    python -m pip install fastapi uvicorn python-multipart aiosqlite PyMuPDF pdfplumber python-docx scikit-learn scipy numpy websockets pydantic pydantic-settings --quiet
)
if not exist "%~dp0frontend\node_modules\.package-lock.json" (
    echo        Instalare pachete npm...
    pushd "%~dp0frontend"
    call npm install --silent 2>nul
    popd
)
echo        OK

:: Pornire servere
echo  [4/4] Pornire servere...
echo.

:: Backend
start "Backend" /min cmd /c "title Calculator - Backend (8000) & cd /d %~dp0backend & set PYTHONIOENCODING=utf-8 & python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1"

timeout /t 3 /nobreak >nul

:: Frontend
start "Frontend" /min cmd /c "title Calculator - Frontend (5173) & cd /d %~dp0frontend & npx vite --host 127.0.0.1 --port 5173"

echo.
echo  ========================================================
echo   Serverele pornesc...
echo   Aplicatie:   http://localhost:5173
echo   API Docs:    http://localhost:8000/docs
echo   Se deschide browser-ul in 8 secunde...
echo  ========================================================

timeout /t 8 /nobreak >nul

start http://localhost:5173

echo.
echo  [OK] Sistem pornit!
echo  Backend si Frontend ruleaza in ferestre minimizate.
echo  Pentru oprire: inchide ferestrele "Calculator - Backend/Frontend".
echo.
pause
