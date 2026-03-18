r"""
Backup baza de date + migrari -> folder configurat.

Utilizare:
  python backup.py                    # backup in folderul implicit
  python backup.py --dest "D:/Backup" # backup in folder personalizat

Folderul implicit: G:\My Drive\Roly\4. Artificial Inteligence\1.0_Traduceri\Backup_DB\
(Google Drive sincronizat local)
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path

# Căi sursă
BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR / "data" / "calculator.db"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"

# Destinație implicită (Google Drive sincronizat)
DEFAULT_DEST = Path(
    r"G:\My Drive\Roly\4. Artificial Inteligence\1.0_Traduceri\Backup_DB"
)


def backup(dest: Path | None = None) -> str:
    """Execută backup și returnează calea directorului creat."""
    dest = dest or DEFAULT_DEST
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = dest / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    copied = []

    # Copiază baza de date
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_dir / "calculator.db")
        copied.append("calculator.db")
    else:
        print(f"[WARN] DB not found: {DB_PATH}")

    # Copiază migrările
    if MIGRATIONS_DIR.exists():
        migrations_dest = backup_dir / "migrations"
        shutil.copytree(MIGRATIONS_DIR, migrations_dest)
        n = len(list(migrations_dest.glob("*.sql")))
        copied.append(f"migrations/ ({n} files)")

    # Copiază calibration.json dacă există
    cal_file = BACKEND_DIR / "data" / "calibration.json"
    if cal_file.exists():
        shutil.copy2(cal_file, backup_dir / "calibration.json")
        copied.append("calibration.json")

    print(f"[OK] Backup creat: {backup_dir}")
    for item in copied:
        print(f"     - {item}")

    # Cleanup: keep only the last 10 backups
    existing = sorted(dest.glob("backup_*"), reverse=True)
    for old in existing[10:]:
        shutil.rmtree(old, ignore_errors=True)
        print(f"[CLEANUP] Removed old backup: {old.name}")

    return str(backup_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup bază de date Roland CC")
    parser.add_argument("--dest", type=Path, default=None, help="Folder destinație")
    args = parser.parse_args()
    backup(args.dest)
