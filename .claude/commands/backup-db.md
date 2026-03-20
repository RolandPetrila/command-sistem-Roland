# /backup-db — Backup rapid SQLite

Backup manual rapid al bazei de date inainte de operatiuni riscante.

1. Copiaza `backend/calculator.db` in `backend/data/backups/calculator_YYYY-MM-DD_HHMMSS.db`
2. Verifica integritatea copiei: `sqlite3 [backup] "PRAGMA integrity_check"`
3. Afiseaza dimensiunea fisierului si numarul de backup-uri existente
4. Daca > 10 backup-uri, propune cleanup (dar NU sterge automat)
