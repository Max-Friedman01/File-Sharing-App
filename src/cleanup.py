from storage import delete_file
from db import connect, delete_expired_records
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

def cleanup(now: int) -> None:
    conn = connect()
    to_delete = delete_expired_records(conn, now)
    try:
        for stored_name in to_delete:
            exists = delete_file(stored_name)
            if not exists:
                logger.warning(f"No such file as {stored_name}")
    except OSError as e:
        logger.warning("Could not process %s: %s", stored_name, e)
    finally:
        conn.close()