from fastapi import APIRouter, Depends, Request, File, Form, UploadFile
from fastapi.templating import Jinja2Templates
import sqlite3
from collections.abc import Iterator
from typing import Annotated
import sqlite3
import db
from pathlib import Path

Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

def get_conn() -> Iterator[sqlite3.Connection]:
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()

@router.get("/hello")
def hello():
    return {"message": "hi"}