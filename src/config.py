from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "files.db"

FILES_PATH = Path(__file__).resolve().parent.parent / "data" / "uploads"

MAX_FILE_SIZE = 10 * 1024 * 1024