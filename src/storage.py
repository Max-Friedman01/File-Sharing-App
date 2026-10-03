from pathlib import Path
from typing import BinaryIO
import config
from models import FileTooLargeError

CHUNK_SIZE = 1024 * 1024

def save_file(source: BinaryIO,
              stored_name: str,
              destination: Path = config.FILES_PATH, 
              max_size: int = config.MAX_FILE_SIZE
              ) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    path = get_path(stored_name, destination)
    try:
        with open(destination / stored_name, "xb") as f:
            num_bytes = 0
            while chunk := source.read(CHUNK_SIZE):
                num_bytes += len(chunk)
                if num_bytes > max_size:
                    raise FileTooLargeError(f"File over max bytes of {max_size}")
                f.write(chunk)
    except FileTooLargeError:
        path.unlink(missing_ok=True)
        raise
    return num_bytes

def delete_file(stored_name: str, destination: Path = config.FILES_PATH) -> bool:
    path = get_path(stored_name, destination)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True

def get_path(stored_name: str, destination: Path = config.FILES_PATH) -> Path:
    return destination / stored_name