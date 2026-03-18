@echo off
title Calculator - Backend (port 8000)
color 1F
echo.
echo  === Backend Calculator Pret Traduceri ===
echo  Server: http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo  ========================================
echo.
cd /d "%~dp0backend"
set PYTHONIOENCODING=utf-8
python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
pause
