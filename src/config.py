from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_data_dir

load_dotenv()

APP_DIR = Path(user_data_dir("FiscalPDF", "sagetendo", ensure_exists=True))
INPUT_DIR = APP_DIR / "uploads"
OUTPUT_DIR = APP_DIR / "processed"

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
