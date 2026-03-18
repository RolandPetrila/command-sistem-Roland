@echo off
title Calculator - Frontend (port 5173)
color 1F
echo.
echo  === Frontend Calculator Pret Traduceri ===
echo  App: http://localhost:5173
echo  =========================================
echo.
cd /d "%~dp0frontend"
npx vite --force --host 127.0.0.1 --port 5173
pause
