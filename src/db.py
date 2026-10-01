import sqlite3
from pathlib import Path
from models import File
from dataclasses import asdict
import security

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "files.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id                  INTEGER PRIMARY KEY,
    stored_name         TEXT NOT NULL UNIQUE,
    original_name       TEXT NOT NULL,
    share_token         TEXT NOT NULL UNIQUE,
    manager_token_hash  TEXT NOT NULL UNIQUE,
    password_hash       TEXT,
    created_at          INTEGER NOT NULL,
    expire_at           INTEGER NOT NULL,
    num_downloads       INT NOT NULL DEFAULT 0,
    size_bytes          INTEGER NOT NULL,
    max_downloads       INTEGER
) STRICT; 
"""

UPSERT = """
INSERT INTO files (
    id,
    stored_name,
    original_name,
    share_token,
    manager_token_hash, 
    password_hash,
    created_at,
    expire_at,
    num_downloads,
    size_bytes,
    max_downloads  
)
"""

def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    return conn

def save_file_record(conn: sqlite3.Connection, record: File) -> int:
    row = asdict(record)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO files (
                stored_name, original_name, share_token, manager_token_hash,
                password_hash, created_at, expire_at, num_downloads, size_bytes, max_downloads
            ) VALUES (
                :stored_name, :original_name, :share_token, :manager_token_hash,
                :password_hash, :created_at, :expire_at, :num_downloads, :size_bytes, :max_downloads
            )
            """,
            row,
        )
    assert cursor.lastrowid is not None
    return cursor.lastrowid

def fetch_num_downloads(token: str) -> int:
    hashed = security.hash_token(token)
    pass