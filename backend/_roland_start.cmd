@echo off 
cd /d "C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend" 
set PYTHONIOENCODING=utf-8 
python -m uvicorn app.main:app --port 8000 --host 0.0.0.0 --ssl-certfile certs\desktop-cjuecmn.tail7bc485.ts.net.crt --ssl-keyfile certs\desktop-cjuecmn.tail7bc485.ts.net.key > "C:\Proiecte\NOU_Calculator_Pret_Traduceri\roland_backend.log" 2>&1 
