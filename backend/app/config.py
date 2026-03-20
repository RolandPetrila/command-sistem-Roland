"""
Configurare aplicație Calculator Preț Traduceri.
Folosește pydantic-settings pentru management centralizat al setărilor.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


# Directorul rădăcină al proiectului backend
_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Setări globale ale aplicației."""

    # --- Căi fișiere ---
    reference_dir: Path = (
        _BACKEND_DIR.parent
        / "Fisiere_Reper_Tarif"
        / "Pret_Intreg_100la100"
    )
    uploads_dir: Path = _BACKEND_DIR / "uploads"
    data_dir: Path = _BACKEND_DIR / "data"
    calibration_file: Path = _BACKEND_DIR / "data" / "calibration.json"
    market_rates_file: Path = _BACKEND_DIR / "data" / "market_rates.json"
    db_path: Path = _BACKEND_DIR / "data" / "calculator.db"

    # --- Facturare ---
    default_invoice_percent: float = 75.0  # clientul plătește 75% din prețul pieței

    # --- Analiză ---
    ocr_words_threshold: int = 10  # sub acest nr de cuvinte/pagină → document scanat
    max_upload_size_mb: int = 50

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # --- Calibrare ---
    knn_neighbors: int = 3
    default_weights: dict = {
        "base_rate": 0.3,
        "word_rate": 0.4,
        "similarity": 0.3,
    }

    class Config:
        env_prefix = "CALC_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def ensure_dirs(self) -> None:
        """Creează directoarele necesare dacă nu există."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
