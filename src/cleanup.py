from storage import delete_file
from db import connect, delete_expired_records
from datetime import datetime, UTC
import logging
from sqlite3 import Connection
from pathlib import Path
import config
import time

logger = logging.getLogger(__name__)

def cleanup_pass(conn: Connection, now: int, folder: Path = config.FILES_PATH) -> int:
    to_delete = delete_expired_records(conn, now)
    num_deleted = 0
    for stored_name in to_delete:
        try:
            exists = delete_file(stored_name, folder)
            num_deleted += 1
            if not exists:
                logger.warning("No such file as %s", stored_name)
        except OSError as e:
            logger.warning("Could not process %s: %s", stored_name, e)
    return num_deleted

def run_cleanup():
    conn = connect()
    try:
        deleted = cleanup_pass(conn, int(time.time()))
    finally:
        conn.close()
    if deleted:
        logger.info("Cleanup removed %d expired file(s)", deleted)