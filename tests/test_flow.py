import io
import time

import pytest

import db
import security
import storage
from models import File, FileTooLargeError, NoMatchingFileError


def test_full_file_lifecycle(tmp_path):
    conn = db.connect(tmp_path / "test.db")
    uploads = tmp_path / "uploads"
    now = int(time.time())

    share_token = security.generate_share_code()
    manager_token = security.generate_manager_token()
    stored_name = security.generate_stored_name()

    size = storage.save_file(io.BytesIO(b"hello world"), stored_name, uploads)

    record = File(
        stored_name=stored_name,
        original_name="hello.txt",
        share_token=share_token,
        manager_token_hash=security.hash_token(manager_token),
        password_hash=security.hash_password("sunflower42"),
        created_at=now,
        expire_at=now + 24 * 60 * 60,
        size_bytes=size,
        max_downloads=3,
    )
    db.save_file_record(conn, record)

    found = db.get_by_share_token(conn, share_token)
    assert found.original_name == "hello.txt"
    assert found.size_bytes == 11
    assert found.password_hash is not None
    assert not security.verify_password(found.password_hash, "wrong")
    assert security.verify_password(found.password_hash, "sunflower42")

    db.increment_downloads(conn, share_token)
    assert storage.get_path(found.stored_name, uploads).read_bytes() == b"hello world"

    managed = db.get_by_manager_token(conn, manager_token)
    assert managed.num_downloads == 1

    next_week = now + 7 * 24 * 60 * 60
    for name in db.delete_expired_records(conn, next_week):
        storage.delete_file(name, uploads)

    with pytest.raises(NoMatchingFileError):
        db.get_by_share_token(conn, share_token)
    assert not storage.get_path(stored_name, uploads).exists()

    conn.close()


def test_too_large_file_leaves_nothing_behind(tmp_path):
    uploads = tmp_path / "uploads"
    with pytest.raises(FileTooLargeError):
        storage.save_file(io.BytesIO(b"x" * 100), "big", uploads, max_size=10)
    assert not storage.get_path("big", uploads).exists()