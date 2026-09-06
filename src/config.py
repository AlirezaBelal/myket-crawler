import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("MYKET_DATA_DIR", str(BASE_DIR / "data")))
RESULT_FILE = Path(os.getenv("MYKET_DB_PATH", str(DATA_DIR / "myket_results.db")))

PAGE_DELAY_MS = int(os.getenv("MYKET_PAGE_DELAY_MS", "1200"))
APP_DELAY_MS = int(os.getenv("MYKET_APP_DELAY_MS", "250"))
PAGE_LOAD_TIMEOUT = int(os.getenv("MYKET_PAGE_LOAD_TIMEOUT", "30"))


def ensure_data_dir() -> None:
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
