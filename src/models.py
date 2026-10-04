from dataclasses import dataclass, field

@dataclass (kw_only=True)
class File:
    stored_name: str
    original_name: str
    share_token: str
    manager_token_hash: str
    password_hash: str | None
    created_at: int
    expire_at: int
    size_bytes: int
    max_downloads: int | None
    num_downloads: int = 0

class NoMatchingFileError(Exception):
    pass

class FileTooLargeError(Exception):
    pass