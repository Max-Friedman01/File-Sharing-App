from fastapi import APIRouter, Depends, Request, File, Form, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
import sqlite3
from collections.abc import Iterator
from typing import Annotated, Any
import db
from pathlib import Path
import config
import storage
import security
from models import FileTooLargeError, FileRecord, NoMatchingFileError
from datetime import UTC, datetime
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

def get_conn() -> Iterator[sqlite3.Connection]:
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()

Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

@router.get("/")
def upload_page(request: Request):
    max_size = config.MAX_FILE_SIZE // (1024 * 1024)
    expiry_options = config.EXPIRY_OPTIONS
    return templates.TemplateResponse(request, "upload.html", {"max_size_mb": max_size, "expiry_options": expiry_options})

@router.post("/upload")
def upload_file(
        request: Request,
        conn: Conn,
        file: Annotated[UploadFile, File()],
        expiry: Annotated[int, Form()],
        max_downloads: Annotated[int | None, Form()] = None,
        password: Annotated[str | None, Form()] = None
    ):
    if expiry not in config.EXPIRY_OPTIONS:
        return render_upload_error(request, 400, "Choose an expiry time from the list.")
    if max_downloads is not None and max_downloads < 1:
        return render_upload_error(request, 400, "Invalid maximum downloads figure")
    original_name = file.filename
    if original_name is None:
        original_name = "File"
    stored_name = security.generate_stored_name()
    try:
        size = storage.save_file(file.file, stored_name)
    except FileTooLargeError as e:
        return render_upload_error(request, 413, "File too large")
    share_token = security.generate_share_code()
    manager_token = security.generate_manager_token()
    now = int(time.time())
    expire_at = now + expiry
    password_hash = (security.hash_password(password) if password else None)
    record = FileRecord(
        stored_name = stored_name,
        original_name = original_name,
        share_token = share_token,
        manager_token_hash = security.hash_token(manager_token),
        password_hash = password_hash,
        created_at = now,
        expire_at = expire_at,
        size_bytes = size,
        max_downloads = max_downloads,
        )
    db.save_file_record(conn, record)
    share_url = str(request.url_for("download_page", share_token=share_token))
    manage_url = str(request.url_for("manage_page", manager_token=manager_token))
    expire_text = time_readable(expire_at)
    return templates.TemplateResponse(request, "links.html", {
        "original_name": original_name,
        "share_url": share_url,
        "manage_url": manage_url,
        "expires_at": expire_text,
        "max_downloads": max_downloads,
        "has_password": password_hash is not None
    })

def render_upload_error(
        request: Request,
        status_code: int = 200,
        message: str = "error"
    ):
    return templates.TemplateResponse(
       request,
       "upload.html",
        {
            "max_size_mb": config.MAX_FILE_SIZE // (1024 * 1024),
            "expiry_options": config.EXPIRY_OPTIONS,
            "error": message,
        },
        status_code=status_code,
    )

def return_message_error(
        request: Request,
        status_code: int = 200,
        title: str = "title",
        message: str = "error"
    ):
    return templates.TemplateResponse(
        request,
        "message.html",
        {
            "title": title,
            "message": message,
        },
        status_code=status_code,
    )

def time_readable(unix_time: int) -> str:
    return datetime.fromtimestamp(unix_time, UTC).strftime("%d %b %Y, %H:%M UTC")

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"

@router.get("/d/{share_token}")
def download_page(request: Request, conn: Conn, share_token: str):
    record = db.get_by_share_token(conn, share_token)
    if record.max_downloads is not None:
        if record.max_downloads - record.num_downloads <= 0:
            return return_message_error(
                request,
                410,
                "This link has reached the maximum allowed downloads",
                "Ask the person who sent it to upload the file again."
            )
    if int(time.time()) >= record.expire_at:
        return return_message_error(
            request,
            410,
            "This link has expired",
            "Ask the person who sent it to upload the file again."
        )
    return templates.TemplateResponse(request, "download.html", download_context(record))

def download_context(record: FileRecord) -> dict[str, Any]:
    return {
        "original_name": record.original_name,
        "size": format_size(record.size_bytes),
        "expires_at": time_readable(record.expire_at),
        "downloads_left": (max_downloads - record.num_downloads if (max_downloads := record.max_downloads) is not None else None),
        "needs_password": record.password_hash is not None
    }

@router.post("/d/{share_token}")
def download_file(
    request: Request,
    conn: Conn,
    share_token: str,
    password: Annotated[str | None, Form()] = None
    ):
    record = db.get_by_share_token(conn, share_token)
    if record.max_downloads is not None:
        if record.max_downloads - record.num_downloads <= 0:
            return return_message_error(
                request,
                410,
                "This link has reached the maximum allowed downloads",
                "Ask the person who sent it to upload the file again."
            )
    if int(time.time()) >= record.expire_at:
        return return_message_error(
            request,
            410,
            "This link has expired",
            "Ask the person who sent it to upload the file again."
        )
    if record.password_hash is not None:
        if password is None or not security.verify_password(record.password_hash, password):
            return templates.TemplateResponse(
                request,
                "download.html",
                {
                    **download_context(record),
                    "error": "That password isn't right. Check with the person who sent you the link.",
                },
                status_code=403,
            )
    file_path = storage.get_path(record.stored_name)
    if not file_path.exists():
        logger.error("File missing on disk: %s", record.stored_name)
        return return_message_error(
            request,
            500,
            "File not available right now",
            "Try later, or ask the person who sent you this link to upload the file again"
        )
    db.increment_downloads(conn, share_token)
    return FileResponse(file_path, filename=record.original_name)

@router.get("/manage/{manager_token}")
def manage_page(request: Request, conn: Conn, manager_token: str):
    record = db.get_by_manager_token(conn, manager_token)
    return templates.TemplateResponse(
        request,
        "manage.html",
        {
            "original_name": record.original_name,
            "size": format_size(record.size_bytes),
            "created_at": time_readable(record.created_at),
            "expires_at": time_readable(record.expire_at),
            "num_downloads": record.num_downloads,
            "max_downloads": record.max_downloads,
            "has_password": record.password_hash is not None,
            "share_url": str(request.url_for("download_page", share_token=record.share_token)),
            "delete_url": str(request.url_for("delete_upload", manager_token=manager_token))
        }
    )

@router.post("/manage/{manager_token}/delete")
def delete_upload(request: Request, conn: Conn, manager_token: str):
    stored_name = db.delete_file_record(conn, manager_token)
    storage.delete_file(stored_name)
    return return_message_error(
        request,
        200,
        "File successfully deleted",
        "Your file's share link no longer works"
    )
