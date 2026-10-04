from fastapi import APIRouter, Depends
import sqlite3
from collections.abc import Iterator
from typing import Annotated
import sqlite3
import db

Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

router = APIRouter()

def get_conn() -> Iterator[sqlite3.Connection]:
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()

@router.get("/hello")
def hello():
    return {"message": "hi"}