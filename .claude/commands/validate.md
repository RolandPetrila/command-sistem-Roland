# /validate — Validare sistem completa (Rule 08)

Executa validarea completa din `.claude/rules/08-post-change-validation.md`:

1. Kill procese test daca portul 8000 e ocupat:
   ```bash
   netstat -aon | findstr ":8000"
   taskkill /f /im python.exe  # doar daca portul e ocupat
   ```
2. Import check rapid:
   ```bash
   cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend
   set PYTHONIOENCODING=utf-8
   python -c "from app.main import app; print('Import OK')"
   ```
3. Start backend + health check:
   ```bash
   python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
   # Asteapta "Uvicorn running on"
   curl http://127.0.0.1:8000/api/health
   ```
4. Frontend build (daca frontend modificat in aceasta sesiune):
   ```bash
   cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\frontend
   npx vite build
   ```
5. Kill procesul de test, verifica port liber
6. Raporteaza:
   ```
   VALIDARE SISTEM:
   - Import check: OK/FAIL
   - Backend start: OK/FAIL
   - Health check: OK/FAIL
   - Frontend build: OK/FAIL/N/A
   - Port cleanup: OK/FAIL
   ```

Daca ORICE pas esueaza → fixeaza INAINTE de a declara gata.
Nu declara "gata" fara acest raport.
