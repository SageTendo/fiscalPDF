from pathlib import Path
import sys

from dotenv import load_dotenv
from platformdirs import user_documents_dir

load_dotenv()

APP_DIR = Path(user_documents_dir()) / "FiscalPDF"
INPUT_DIR = APP_DIR / "uploads"
OUTPUT_DIR = APP_DIR / "processed"

APP_DIR.mkdir(exist_ok=True)
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
