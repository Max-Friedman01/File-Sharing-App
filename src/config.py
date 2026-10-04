from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "files.db"

FILES_PATH = Path(__file__).resolve().parent.parent / "data" / "uploads"

MAX_FILE_SIZE = 10 * 1024 * 1024

EXPIRY_OPTIONS = {
    60 * 60: "1 hour",
    60 * 60 * 12: "12 hours",
    60 * 60 * 24: "1 day",
    60 * 60 * 24 * 3: "3 days",
    60 * 60 * 24 * 7: "7 days"
}