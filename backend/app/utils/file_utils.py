from pathlib import Path
from fastapi import UploadFile

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TMP_DIR = PROJECT_ROOT / "data" / "tmp_uploads"
TMP_DIR.mkdir(parents=True, exist_ok=True)

def save_upload(file: UploadFile) -> Path:
    path = TMP_DIR / file.filename
    path.write_bytes(file.file.read())
    return path
