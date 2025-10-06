import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

print(os.environ.get("DEBUG"))

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "in"
OUTPUT_DIR = BASE_DIR / "out"

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
