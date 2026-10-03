import sqlite3
from pathlib import Path
from models import File, NoMatchingFileError
from dataclasses import asdict
import security
import config


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
    num_downloads       INTEGER NOT NULL DEFAULT 0,
    size_bytes          INTEGER NOT NULL,
    max_downloads       INTEGER
) STRICT; 
"""

FILE_COLUMNS = """
    stored_name, original_name, share_token, manager_token_hash, password_hash,
    created_at, expire_at, num_downloads, size_bytes, max_downloads
"""

def connect(path: Path = config.DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.row_factory = sqlite3.Row
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

def increment_downloads(conn: sqlite3.Connection, share_token: str) -> None:
    with conn:
        cursor = conn.execute(
            "UPDATE files SET num_downloads = num_downloads + 1 WHERE share_token = ?",
            (share_token,),
        )
    if cursor.rowcount == 0:
        raise NoMatchingFileError(f"No such file for {share_token}")

def delete_file_record(conn: sqlite3.Connection, manager_token: str) -> str:
    hashed = security.hash_token(manager_token)
    with conn:
        row = conn.execute(
            "DELETE FROM files WHERE manager_token_hash = ? RETURNING stored_name",
            (hashed,),
        ).fetchone()
    if row is None:
        raise NoMatchingFileError("No file for this manager token")
    return row["stored_name"]

def delete_expired_records(conn: sqlite3.Connection, now: int) -> list[str]:
    with conn:
        rows = conn.execute(
            "DELETE FROM files WHERE expire_at <= ? RETURNING stored_name",
            (now,),
        ).fetchall()
    return [row["stored_name"] for row in rows]

def get_by_share_token(conn: sqlite3.Connection, share_token: str) -> File:
    row = conn.execute(
        f"SELECT {FILE_COLUMNS} FROM files WHERE share_token = ?",
        (share_token,),
    ).fetchone()
    if row is None:
        raise NoMatchingFileError("No file for this share token")
    return File(**dict(row))


def get_by_manager_token(conn: sqlite3.Connection, manager_token: str) -> File:
    hashed = security.hash_token(manager_token)
    row = conn.execute(
        f"SELECT {FILE_COLUMNS} FROM files WHERE manager_token_hash = ?",
        (hashed,),
    ).fetchone()
    if row is None:
        raise NoMatchingFileError("No file for this manager token")
    return File(**dict(row))
